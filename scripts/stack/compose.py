#!/usr/bin/env python3
"""Compose per-line stacks into ONE linear colour stack — the convergence
stage for multi-line targets (dual-band OSC lines today; per-filter mono
stacks when that ingest lands).

Usage: compose.py <session> <set>

Reads datasets/<session>/<set>/composition.json (the BUILD record: lines +
the channels palette mapping — see datasets/README.md) and the per-line
stacks <session>/results/stack_<set>_<line>.fit, and writes the composed
3-channel float FITS <session>/results/stack_<set>_comp.fit. The composed
stack then enters the ordinary flow (solve -> SPCC -> render) exactly like
any colour stack.

Pure numpy channel mapping — deterministic, no resampling, no scaling: the
lines were registered to the SAME reference frame at ingest, so the
channels must already overlay. That claim is MEASURED here, not assumed:
star centroids are detected on the first line and re-centroided on every
other line; the median offset prints, lands in the inspection report
(compose stage, bound 1.0 px), and is emitted as a machine line
(COMPOSE_RESID <median_px> <p95_px>) for the pipeline runner.

FITS I/O is a minimal local reader/writer in FILE order (no orientation
handling — all channels transform identically; the shared-helper dedup in
BACKLOG sweeps this into the lib later).
"""
import json
import os
import sys

import numpy as np


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
    channels = comp.get("channels")
    lines = comp.get("lines")
    if not channels or not lines or sorted(channels) != ["B", "G", "R"]:
        sys.exit(f"compose: {p_comp} needs 'lines' + a full R/G/B "
                 "'channels' mapping")

    line_data, cards0 = {}, None
    for ln in lines:
        p = os.path.join(sdir, "results", f"stack_{set_name}_{ln}.fit")
        if not os.path.exists(p):
            sys.exit(f"compose: line stack missing: {p}")
        cards, data, hdr = read_fits_raw(p)
        if data.shape[0] != 1:
            sys.exit(f"compose: line stack {p} has {data.shape[0]} "
                     "channels — a line is mono by construction")
        st = os.stat(p)
        print(f"[compose] line {ln}: {os.path.basename(p)} "
              f"{data.shape[2]}x{data.shape[1]} "
              f"(size {st.st_size}, mtime {int(st.st_mtime)})")
        line_data[ln] = data[0]
        if cards0 is None:
            cards0 = cards
    dims = {ln: d.shape for ln, d in line_data.items()}
    if len(set(dims.values())) != 1:
        sys.exit(f"compose: line stacks disagree on geometry: {dims}")

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

    provenance = [
        f"COMMENT compose.py: channels " +
        " ".join(f"{c}={channels[c]}" for c in order),
    ] + [
        f"COMMENT compose.py: line {ln} = stack_{set_name}_{ln}.fit"
        for ln in lines
    ]
    cards_out = cards0 + [c.ljust(80) for c in provenance]
    p_out = os.path.join(sdir, "results", f"stack_{set_name}_comp.fit")
    write_fits3(p_out, cards_out, planes)
    print(f"[compose] wrote {os.path.relpath(p_out, repo)}")


if __name__ == "__main__":
    main()
