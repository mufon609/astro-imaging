#!/usr/bin/env python3
"""Compose per-line/per-filter stacks into ONE linear colour stack — the
convergence stage for multi-channel targets.

Usage: compose.py <session> <set-or-target>

Reads datasets/<session>/<name>/composition.json (the BUILD record — see
datasets/README.md) and writes the composed 3-channel float32 RGB FITS
<repo>/web/results/<session>/stack_<name>_comp.fit. The composed stack then
enters the ordinary flow (solve -> SPCC -> render) exactly like any colour
stack.

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

Siril owns EVERY pixel operation AND the output write: the align is
`register`/`seqapplyreg`, the combine is `rgbcomp` under `set32bits`
(3-plane float32; verified pixel-identical to the in-house combine it
replaced before the swap — the A/B record lives in the per-dataset
qa_work). This module only resolves the record, drives the tool, and
guards the inputs — and the guards are FITS-HEADER-ONLY (astropy): float32
contract (BITPIX -32), mono inputs, geometry agreement. No pixel is read
in-house. rgbcomp sums exposure metadata (LIVETIME/STACKCNT) across the
channels — the composed product's integration is the members' sum, which
is the composed product's honest depth.

Provenance: the composition record IS the build's record; the channel
mapping and per-input identities are printed to the run log, and rgbcomp
writes its own FITS header.

A composition with a `luminance` member is REFUSED for now: LRGB joins L
after both parts are stretched (a nonlinear-space operation), which this
compose-then-render flow cannot express yet. `rgbcomp -lum=` is the
headless mechanism for it when an L corpus arrives (BACKLOG; its CLI
blend colour space is undocumented — resolve before first use).
"""
import json
import os
import shutil
import subprocess
import sys

from astropy.io import fits

SIRIL = ["flatpak", "run", "--command=siril-cli", "org.siril.Siril"]


def results_dir(sdir):
    """Durable output root for a session: <repo>/web/results/<session-basename>
    (the web-servable output tree; the session dir itself is transient
    staging). Member stacks are read from and the composed stack written to
    this one place."""
    repo = os.path.dirname(os.path.dirname(
        os.path.dirname(os.path.abspath(__file__))))
    return os.path.join(repo, "web", "results",
                        os.path.basename(os.path.normpath(sdir)))


def check_input(path, name):
    """Header-only input guard: the file exists, is float32 (BITPIX -32 —
    the linear-chain contract), and is MONO (a compose input is a single
    plane by construction). Returns (nx, ny). Loud on any violation."""
    if not os.path.exists(path):
        sys.exit(f"compose: input stack missing: {path}")
    h = fits.getheader(path)
    if int(h["BITPIX"]) != -32:
        sys.exit(f"compose: expected float32 line stack, got BITPIX "
                 f"{h['BITPIX']} in {path}")
    if int(h.get("NAXIS", 2)) == 3 and int(h.get("NAXIS3", 1)) != 1:
        sys.exit(f"compose: {path} has {h['NAXIS3']} channels — a "
                 "compose input is mono by construction")
    nx, ny = int(h["NAXIS1"]), int(h["NAXIS2"])
    st = os.stat(path)
    print(f"[compose] {name}: {os.path.basename(path)} {nx}x{ny} "
          f"(size {st.st_size}, mtime {int(st.st_mtime)})")
    return nx, ny


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
        src = os.path.join(results_dir(sdir), f"stack_{members[n]}.fit")
        if not os.path.exists(src):
            sys.exit(f"compose: member stack missing: {src} (stack the "
                     f"member set '{members[n]}' first)")
        # staged inputs must NOT share the sequence prefix: siril
        # `convert ch` symlinks its sequence entries over same-named
        # files — a ch_*.fit input becomes a self-referential link
        os.link(src, os.path.join(work, f"in_{i:05d}.fit"))
    ref_idx = names.index(reference) + 1
    rel = os.path.relpath(work, sdir)
    ssf = os.path.join(sdir, "work", f"compose_{set_name}.gen.ssf")
    # -framing=min crops every output to the INTERSECTION of member
    # coverage: a pixel the composed product ships must exist in EVERY
    # channel — compositing an uncovered margin fabricates colour there
    # (measured: a single uncovered corner block read R-G +8 and failed
    # the colour gate on an otherwise neutral sky). The crop is integer-
    # aligned, so the reference channel is still never interpolated.
    with open(ssf, "w") as f:
        f.write("requires 1.4.0\n"
                "setcompress 0\n"
                f"cd {rel}\n"
                "convert ch\n"
                f"setref ch {ref_idx}\n"
                "register ch -2pass\n"
                f"setref ch {ref_idx}\n"
                "seqapplyreg ch -framing=min\n"
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
                 "flow cannot express yet (`rgbcomp -lum=` is the headless "
                 "mechanism; its blend colour space is undocumented — "
                 "BACKLOG); compose the RGB without it or wait for that "
                 "design")

    inputs = {}
    if kind == "dualband-osc":
        lines = comp.get("lines")
        if not lines:
            sys.exit(f"compose: {p_comp} (dualband-osc) needs 'lines'")
        for ln in lines:
            inputs[ln] = os.path.join(results_dir(sdir),
                                      f"stack_{set_name}_{ln}.fit")
    elif kind == "mono-filters":
        members = comp.get("members")
        if not members:
            sys.exit(f"compose: {p_comp} (mono-filters) needs 'members' "
                     "(channel name -> sibling set)")
        reference = comp.get("reference", sorted(members)[0])
        inputs = align_members(repo, sdir, set_name, members, reference)
    else:
        sys.exit(f"compose: unknown composition kind '{kind}'")

    dims = {n: check_input(p, f"input {n}") for n, p in sorted(inputs.items())}
    if len(set(dims.values())) != 1:
        sys.exit(f"compose: input stacks disagree on geometry: {dims}")
    missing = [c for c in "RGB" if channels[c] not in inputs]
    if missing:
        sys.exit(f"compose: channels map to unknown inputs: "
                 f"{ {c: channels[c] for c in missing} }")

    order = ["R", "G", "B"]
    print("[compose] channels: " +
          " ".join(f"{c}={channels[c]}" for c in order))

    # the combine + the write are Siril's: rgbcomp under set32bits
    p_out = os.path.join(results_dir(sdir), f"stack_{set_name}_comp.fit")
    if os.path.exists(p_out):
        os.remove(p_out)
    r_, g_, b_ = (inputs[channels[c]] for c in order)
    ssf = os.path.join(sdir, "work", f"compose_{set_name}.rgb.ssf")
    with open(ssf, "w") as f:
        f.write("requires 1.4.0\n"
                "setcompress 0\n"
                "set32bits\n"
                f"rgbcomp {r_} {g_} {b_} -out={p_out}\n")
    r = subprocess.run(SIRIL + ["-d", sdir, "-s", ssf],
                       capture_output=True, text=True)
    log = r.stdout + r.stderr
    if r.returncode != 0 or not os.path.exists(p_out):
        sys.exit("compose: rgbcomp failed:\n" + log[-2000:])
    h = fits.getheader(p_out)
    if int(h["BITPIX"]) != -32 or int(h.get("NAXIS3", 1)) != 3:
        sys.exit(f"compose: rgbcomp output is not a float32 3-plane cube "
                 f"(BITPIX {h['BITPIX']}, NAXIS3 {h.get('NAXIS3')})")
    print(f"[compose] wrote {os.path.relpath(p_out, repo)} "
          f"(rgbcomp, float32 {h['NAXIS1']}x{h['NAXIS2']}x3)")
    # the aligned intermediates are consumed; the composed stack + the
    # composition record + the printed provenance are the record
    walign = os.path.join(sdir, "work", f"compose_{set_name}")
    if os.path.isdir(walign):
        shutil.rmtree(walign)


if __name__ == "__main__":
    main()
