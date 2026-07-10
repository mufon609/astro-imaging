#!/usr/bin/env python3
"""Compose per-line/per-filter stacks into ONE linear colour stack — the
convergence stage for multi-channel targets.

Usage: compose.py <session> <set-or-target>

Reads datasets/<session>/<name>/composition.json (the BUILD record — see
datasets/README.md) and writes the composed 3-channel float FITS
<session>/results/stack_<name>_comp.fit. The composed stack then enters
the ordinary flow (solve -> SPCC -> render) exactly like any colour stack.

Two kinds:
- `dualband-osc`: inputs are the ingest's per-line stacks
  (stack_<set>_<line>.fit). The lines came from the SAME frames
  registered to the SAME reference, so they already overlay — no
  resampling here.
- `mono-filters`: `members` maps channel names to SIBLING sets (a filter
  wheel: one set per filter), each already stacked by the ordinary mono
  path. Different frames per channel means nothing overlays by
  construction, so compose ALIGNS the member stacks first: a siril
  sequence of the stacks, registered to the member named `reference`
  (one interpolation pass — the reference channel itself gets only the
  identity transform).

Either way the overlay is MEASURED, never assumed: star centroids are
detected on the first channel and re-centroided on every other distinct
channel; the median offset prints, lands in the inspection report
(compose stage, bound 1.0 px), and is emitted as a machine line
(COMPOSE_RESID <median_px> <p95_px>) for the pipeline runner.

A composition with a `luminance` member is REFUSED for now: LRGB joins L
after both parts are stretched (a nonlinear-space operation), which this
compose-then-render flow cannot express yet — that design lands with the
LRGB corpus work (BACKLOG).

FITS I/O is a minimal local reader/writer in FILE order (no orientation
handling — all channels transform identically; the shared-helper dedup in
BACKLOG sweeps this into the lib later).
"""
import json
import os
import shutil
import subprocess
import sys

import numpy as np

SIRIL = ["flatpak", "run", "--command=siril-cli", "org.siril.Siril"]


def read_fits_raw(path):
    """(header_cards, data float32 (C,H,W) in FILE order, hdr dict)."""
    raw = open(path, "rb").read()
    cards, off, end = [], 0, False
    while not end:
        block = raw[off:off + 2880]
        for i in range(0, 2880, 80):
            c = block[i:i + 80].decode("ascii")
            if c.startswith("END"):
                end = True
                break
            cards.append(c)
        off += 2880
        if off > len(raw):
            sys.exit(f"compose: no END card in {path}")
    hdr = {c[:8].strip(): c[10:].split("/")[0].strip()
           for c in cards if "=" in c}
    bitpix = int(hdr["BITPIX"])
    if bitpix != -32:
        sys.exit(f"compose: expected float32 line stack, got BITPIX "
                 f"{bitpix} in {path}")
    nx, ny = int(hdr["NAXIS1"]), int(hdr["NAXIS2"])
    nc = int(hdr.get("NAXIS3", "1")) if int(hdr["NAXIS"]) == 3 else 1
    data = np.frombuffer(raw, dtype=">f4", count=nc * ny * nx,
                         offset=off).reshape(nc, ny, nx)
    return cards, data.astype(np.float32), hdr


def write_fits3(path, cards_src, planes):
    """Write (3,H,W) float32 in FILE order, header = source cards with the
    NAXIS geometry patched to the cube and provenance comments appended."""
    ny, nx = planes.shape[1], planes.shape[2]
    out = []
    seen_naxis3 = False
    for c in cards_src:
        key = c[:8].strip()
        if key == "NAXIS":
            out.append(f"{'NAXIS':<8s}= {3:>20d}".ljust(80))
        elif key == "NAXIS1":
            out.append(f"{'NAXIS1':<8s}= {nx:>20d}".ljust(80))
        elif key == "NAXIS2":
            out.append(f"{'NAXIS2':<8s}= {ny:>20d}".ljust(80))
        elif key == "NAXIS3":
            out.append(f"{'NAXIS3':<8s}= {3:>20d}".ljust(80))
            seen_naxis3 = True
        else:
            out.append(c)
    if not seen_naxis3:
        # insert NAXIS3 right after NAXIS2 (FITS requires axis order)
        for i, c in enumerate(out):
            if c[:8].strip() == "NAXIS2":
                out.insert(i + 1, f"{'NAXIS3':<8s}= {3:>20d}".ljust(80))
                break
    hdr = "".join(out) + "END".ljust(80)
    hdr += " " * ((-len(hdr)) % 2880)
    body = planes.astype(">f4").tobytes()
    with open(path, "wb") as f:
        f.write(hdr.encode("ascii"))
        f.write(body)
        f.write(b"\x00" * ((-len(body)) % 2880))


def bg_subtract(ch, bs=128):
    """Coarse block-median background removal (crops to block multiples —
    identical crop for every channel of one composed stack)."""
    h, w = ch.shape
    gy, gx = h // bs, w // bs
    bg = np.median(ch[:gy * bs, :gx * bs].reshape(gy, bs, gx, bs),
                   axis=(1, 3))
    return ch[:gy * bs, :gx * bs] - np.repeat(np.repeat(bg, bs, 0), bs, 1)


def detect_peaks(d, n_max=150, k_sig=20.0, minsep=25, border=32):
    """Bright local maxima on a background-subtracted channel (the same
    trail-robust peak approach the solver uses)."""
    from scipy.ndimage import maximum_filter
    h, w = d.shape
    sig = 1.4826 * np.median(np.abs(d - np.median(d)))
    mx = maximum_filter(d, size=9)
    cand = (d == mx) & (d > k_sig * max(sig, 1e-9))
    cand[:border] = cand[-border:] = False
    cand[:, :border] = cand[:, -border:] = False
    ys, xs = np.nonzero(cand)
    order = np.argsort(d[ys, xs])[::-1]
    taken = np.zeros((h // minsep + 2, w // minsep + 2), bool)
    picks = []
    for k in order:
        cy, cx = ys[k] // minsep, xs[k] // minsep
        if taken[max(0, cy - 1):cy + 2, max(0, cx - 1):cx + 2].any():
            continue
        taken[cy, cx] = True
        picks.append((ys[k], xs[k]))
        if len(picks) >= n_max:
            break
    return picks


def centroid(d, y, x, r=4):
    """Flux-weighted centroid in a (2r+1)^2 window, clipped at 0."""
    y0, y1 = max(0, y - r), min(d.shape[0], y + r + 1)
    x0, x1 = max(0, x - r), min(d.shape[1], x + r + 1)
    win = np.clip(d[y0:y1, x0:x1], 0, None)
    s = win.sum()
    if s <= 0:
        return None
    wy, wx = np.mgrid[y0:y1, x0:x1]
    return float((win * wy).sum() / s), float((win * wx).sum() / s)


def channel_residual(planes, line_of_channel):
    """Median + p95 star-centroid offset (px) between the first line and
    every OTHER distinct line, measured on the composed planes."""
    lines = list(dict.fromkeys(line_of_channel))      # unique, ordered
    if len(lines) < 2:
        return 0.0, 0.0, 0
    dref = bg_subtract(planes[line_of_channel.index(lines[0])])
    peaks = detect_peaks(dref)
    offs = []
    for other in lines[1:]:
        doth = bg_subtract(planes[line_of_channel.index(other)])
        for (y, x) in peaks:
            a = centroid(dref, y, x)
            b = centroid(doth, y, x)
            if a and b:
                offs.append(np.hypot(a[0] - b[0], a[1] - b[1]))
    if not offs:
        return None, None, 0
    offs = np.asarray(offs)
    return float(np.median(offs)), float(np.percentile(offs, 95)), len(offs)


def load_plane(path, name):
    """One mono stack -> (cards, 2-D plane). Loud on wrong shape."""
    if not os.path.exists(path):
        sys.exit(f"compose: input stack missing: {path}")
    cards, data, _hdr = read_fits_raw(path)
    if data.shape[0] != 1:
        sys.exit(f"compose: {path} has {data.shape[0]} channels — a "
                 "compose input is mono by construction")
    st = os.stat(path)
    print(f"[compose] {name}: {os.path.basename(path)} "
          f"{data.shape[2]}x{data.shape[1]} "
          f"(size {st.st_size}, mtime {int(st.st_mtime)})")
    return cards, data[0]


def align_members(repo, sdir, set_name, members, reference):
    """mono-filters: register the member stacks to the `reference` member
    (siril sequence of the stacks, explicit reference, one pass) and
    return {member_name: aligned_path}. Different frames per channel mean
    nothing overlays by construction — this is the one interpolation pass
    the composed product carries (the reference channel gets only the
    identity transform)."""
    names = sorted(members)                      # deterministic 00001.. order
    if reference not in members:
        sys.exit(f"compose: reference '{reference}' is not a member "
                 f"({names})")
    work = os.path.join(sdir, "work", f"compose_{set_name}")
    if os.path.isdir(work):
        shutil.rmtree(work)
    os.makedirs(work)
    for i, n in enumerate(names, 1):
        src = os.path.join(sdir, "results", f"stack_{members[n]}.fit")
        if not os.path.exists(src):
            sys.exit(f"compose: member stack missing: {src} (stack the "
                     f"member set '{members[n]}' first)")
        os.link(src, os.path.join(work, f"ch_{i:05d}.fit"))
    ref_idx = names.index(reference) + 1
    rel = os.path.relpath(work, sdir)
    ssf = os.path.join(sdir, "work", f"compose_{set_name}.gen.ssf")
    with open(ssf, "w") as f:
        f.write("requires 1.4.0\n"
                f"cd {rel}\n"
                "convert ch\n"
                f"setref ch {ref_idx}\n"
                "register ch\n"
                "close\n")
    print(f"[compose] aligning {len(names)} member stacks to "
          f"'{reference}' (ref index {ref_idx})")
    r = subprocess.run(SIRIL + ["-d", sdir, "-s", ssf],
                       capture_output=True, text=True)
    log = r.stdout + r.stderr
    aligned = {n: os.path.join(work, f"r_ch_{i:05d}.fit")
               for i, n in enumerate(names, 1)}
    if r.returncode != 0 or not all(os.path.exists(p)
                                    for p in aligned.values()):
        sys.exit("compose: member alignment failed:\n" + log[-2000:])
    m = [ln for ln in log.splitlines() if "registered" in ln]
    if m:
        print(f"[compose] {m[-1].strip().replace('log: ', '')}")
    return aligned


def main():
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    session, set_name = sys.argv[1], sys.argv[2]
    repo = os.path.dirname(os.path.dirname(
        os.path.dirname(os.path.abspath(__file__))))
    sdir = os.path.join(repo, session)
    p_comp = os.path.join(repo, "datasets", os.path.basename(
        os.path.normpath(session)), set_name, "composition.json")
    if not os.path.exists(p_comp):
        sys.exit(f"compose: no composition record {p_comp} — an ordinary "
                 "single-stack set has nothing to compose")
    comp = json.load(open(p_comp))
    kind = comp.get("kind")
    channels = comp.get("channels")
    if not channels or sorted(channels) != ["B", "G", "R"]:
        sys.exit(f"compose: {p_comp} needs a full R/G/B 'channels' mapping")
    if comp.get("luminance"):
        sys.exit("compose: this composition names a `luminance` member — "
                 "LRGB joins L after both parts are stretched, which this "
                 "flow cannot express yet (BACKLOG); compose the RGB "
                 "without it or wait for that design")

    line_data, cards0 = {}, None
    if kind == "dualband-osc":
        lines = comp.get("lines")
        if not lines:
            sys.exit(f"compose: {p_comp} (dualband-osc) needs 'lines'")
        for ln in lines:
            p = os.path.join(sdir, "results", f"stack_{set_name}_{ln}.fit")
            cards, plane = load_plane(p, f"line {ln}")
            line_data[ln] = plane
            if cards0 is None:
                cards0 = cards
    elif kind == "mono-filters":
        members = comp.get("members")
        if not members:
            sys.exit(f"compose: {p_comp} (mono-filters) needs 'members' "
                     "(channel name -> sibling set)")
        reference = comp.get("reference", sorted(members)[0])
        aligned = align_members(repo, sdir, set_name, members, reference)
        # header source = the REFERENCE member's aligned stack (its
        # geometry is the composed product's geometry)
        for n in sorted(members):
            cards, plane = load_plane(aligned[n], f"member {n}")
            line_data[n] = plane
            if n == reference:
                cards0 = cards
    else:
        sys.exit(f"compose: unknown composition kind '{kind}'")

    dims = {ln: d.shape for ln, d in line_data.items()}
    if len(set(dims.values())) != 1:
        sys.exit(f"compose: input stacks disagree on geometry: {dims}")
    missing = [c for c in "RGB" if channels[c] not in line_data]
    if missing:
        sys.exit(f"compose: channels map to unknown inputs: "
                 f"{ {c: channels[c] for c in missing} }")

    order = ["R", "G", "B"]
    line_of_channel = [channels[c] for c in order]
    planes = np.stack([line_data[channels[c]] for c in order])
    print(f"[compose] channels: " +
          " ".join(f"{c}={channels[c]}" for c in order))

    # per-channel always-on stats (the stage reports itself)
    for i, c in enumerate(order):
        p = planes[i]
        bg = float(np.median(p))
        sig = float(1.4826 * np.median(np.abs(p - bg)))
        print(f"[compose] {c} ({channels[c]}): bg {bg:.5f} sigma "
              f"{sig:.6f} p99 {float(np.percentile(p[::4, ::4], 99)):.5f}")

    med, p95, n = channel_residual(planes, line_of_channel)
    if med is None:
        print("[compose] WARNING: no common stars centroided — channel "
              "alignment UNMEASURED")
    else:
        print(f"[compose] channel alignment: median {med:.3f} px, "
              f"p95 {p95:.3f} px over {n} star pairs")
        print(f"COMPOSE_RESID {med:.3f} {p95:.3f}")

    if kind == "dualband-osc":
        inputs = [f"{ln} = stack_{set_name}_{ln}.fit"
                  for ln in comp["lines"]]
    else:
        inputs = [f"{n} = stack_{comp['members'][n]}.fit (aligned to "
                  f"'{comp.get('reference', sorted(comp['members'])[0])}')"
                  for n in sorted(comp["members"])]
    provenance = [
        f"COMMENT compose.py [{kind}]: channels " +
        " ".join(f"{c}={channels[c]}" for c in order),
    ] + [f"COMMENT compose.py: {s}" for s in inputs]
    cards_out = cards0 + [c.ljust(80) for c in provenance]
    p_out = os.path.join(sdir, "results", f"stack_{set_name}_comp.fit")
    write_fits3(p_out, cards_out, planes)
    print(f"[compose] wrote {os.path.relpath(p_out, repo)}")
    # the aligned intermediates are consumed; the composed stack + the
    # printed provenance are the record
    walign = os.path.join(sdir, "work", f"compose_{set_name}")
    if os.path.isdir(walign):
        shutil.rmtree(walign)


if __name__ == "__main__":
    main()
