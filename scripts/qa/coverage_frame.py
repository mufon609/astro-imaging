#!/usr/bin/env python3
"""Propose the VERIFIED COVERAGE FRAME of a framing=max union — the largest
axis-aligned rectangle every part of which the tool measures as covered sky.

  coverage_frame.py <union.fit> <out.json> [--grid=80x50] [--channel=Green]
                    [--floor=<ADU>] [--framing-record=<json>]
  coverage_frame.py --selftest [--keep]

WHY IT EXISTS. `docs/dead-ends.md` pins the ORDER — on a union/max canvas, crop
to the verified coverage frame BEFORE any background step, because `subsky`'s
sample grid ingests the zero-coverage rims and its `-tolerance` excludes only
BRIGHT outliers, not empty sky. The repo had the VERIFY half of that
(`web/verify_framing.py` checks a rectangle with Siril `crop`+`stat`) and the
CONSUME half (`finish_render --crop-record`), but nothing that PROPOSES the
rectangle: it came from a hand-drawn box in `web/crop.html`. So on a union
nobody had drawn, the pinned order could not be followed at all. This is the
proposing half, and it hands `verify_framing.py` a record to pass or fail —
this script never marks its own work verified.

WHAT IS THE TOOL'S AND WHAT IS IN-HOUSE (the bright line, `CLAUDE.md`):
  Siril 1.4.4  one `load`, then `boxselect`+`stat` per box. Every pixel is read
               by Siril and every number here — Min, Median — is Siril's. Same
               probed-identical route `starlight_preservation.py` uses
               (`boxselect`+`stat` == `crop`+`stat` to every printed digit, in
               ONE load instead of N).
  in-house     the grid bookkeeping and the largest-all-covered-rectangle
               search over the tool's own numbers. No pixel is read here.
REPORTS ONLY: it writes a record and, with --framing-record, an UNVERIFIED
framing record. It crops nothing, gates nothing, and always exits 0.

REMOVAL CONDITION: an official tool reports, headless, the largest fully
covered axis-aligned rectangle of a registered union (or a coverage map ON the
union's own canvas that `verify_framing.py --map` can consume). Probed on this
rig: Siril `stat`/`bg` measure a selection or the whole frame and know nothing
about coverage; `seqapplyreg -framing=` chooses min/max/COG framings but
reports no covered region; the repo's own `coverage_probe.sh` builds a true
per-pixel member-count map, but through `register -2pass`, so on an
ASTROMETRICALLY registered union its canvas is not the product's and its
docstring already refuses that use. Register row in BACKLOG:`removal-conditions`.

THE COVERAGE TEST NAMES ONE REFERENCE CHANNEL, and it must not be the low one.
The registry rule is the SIBLING-CLASS SKY FLOOR, never mere non-zero (lanczos
edge-ringing residue passes a Min>0 guard at Min 7-26 on a ~90 ADU sky). But
applying that floor to the WORST channel is unusable on an OSC class whose low
channel clips: MEASURED on the three aug06 per-set stacks, which are
`-framing=min` products and so fully covered by construction, Siril reads Red
Min 0.0 on all three (Red medians 14.6/32.1/28.3) while Green reads Min
60.4/72.4/67.7 at medians 71.8/83.8/79.3. Hence --channel, defaulting to Green.
Run with no --floor first: the script prints the Min distribution so the floor
can be DERIVED from the siblings and checked against the data's own gap.

`boxselect` COUNTS y FROM THE TOP while FITS rows run from the bottom, so a box
held in FITS coordinates is emitted at `y_select = H - y - h`. The record
carries BOTH conventions for exactly that reason (the registered crop-y-flip
trap), and `--selftest` step 2 goes RED if the convention ever flips.
"""
import json
import math
import os
import re
import shutil
import sys

import numpy as np
from astropy.io import fits
from astropy.wcs import WCS

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "lib"))
from siril_run import run as siril_run   # serialized invoker (BACKLOG:removal-conditions)

# Sigma and bgnoise accept nan: Siril prints `Sigma: -nan` on a ZERO-VARIANCE
# selection (registered), and a numeric-only class there makes the whole line
# fail to match — so a uniform box reads as "no data" and is silently called
# UNCOVERED. That is not hypothetical here: a flat rim or a saturated patch is
# exactly the kind of region a coverage test lands on, and this fixture's own
# uniform ringing band reproduced it on the selftest's first run.
STAT_RE = re.compile(
    r"(Red|Green|Blue|B&W) layer: Mean: (?P<mean>[-+0-9.eE]+), "
    r"Median: (?P<median>[-+0-9.eE]+), Sigma: (?P<sigma>[-+0-9.eEanN]+), "
    r"Min: (?P<min>[-+0-9.eE]+), Max: (?P<max>[-+0-9.eE]+), "
    r"bgnoise: (?P<bgnoise>[-+0-9.eEanN]+)")
SEL_RE = re.compile(r"Current selection \[x, y, w, h\]: "
                    r"(-?\d+) (-?\d+) (-?\d+) (-?\d+)")


def largest_rect(ok, nx, ny):
    """Largest all-True axis-aligned rectangle in a boolean grid (the maximal
    rectangle in a histogram, row by row). Grid coordinates, j bottom-up,
    inclusive: (i0, j0, i1, j1), or None if nothing is covered."""
    best_area, best = 0, None
    heights = [0] * nx
    for j in range(ny):
        for i in range(nx):
            heights[i] = heights[i] + 1 if ok[j][i] else 0
        stack = []
        for i in range(nx + 1):
            h = heights[i] if i < nx else 0
            start = i
            while stack and stack[-1][1] >= h:
                s, sh = stack.pop()
                if sh * (i - s) > best_area:
                    best_area, best = sh * (i - s), (s, j - sh + 1, i - 1, j)
                start = s
            stack.append((start, h))
    return best


def measure_grid(src, nx, ny, workdir):
    """Siril's own per-box statistics over a fixed grid. Boxes are in FITS
    pixels (y from the bottom); the emitted selection is top-down."""
    hdr = fits.getheader(src)
    W, H = int(hdr["NAXIS1"]), int(hdr["NAXIS2"])
    bw, bh = W // nx, H // ny
    if bw < 8 or bh < 8:
        sys.exit(f"coverage_frame: {nx}x{ny} leaves {bw}x{bh} px per box")
    home = os.path.expanduser("~")
    if os.path.commonpath([os.path.abspath(workdir), home]) != home:
        sys.exit("coverage_frame: the work dir is outside $HOME — the Siril "
                 "flatpak has its OWN private /tmp, so an .ssf written there "
                 "is invisible to it and every stat comes back empty.")
    os.makedirs(workdir, exist_ok=True)
    ssf = os.path.join(workdir, "_coverage_grid.ssf")
    boxes = [(i, j, i * bw, j * bh) for j in range(ny) for i in range(nx)]
    with open(ssf, "w") as fh:
        fh.write(f"requires 1.2.0\nsetcompress 0\nsetext fit\nload {src}\n")
        for _, _, x, y in boxes:
            fh.write(f"boxselect {x} {H - y - bh} {bw} {bh}\nstat\n")
        fh.write("boxselect -clear\n")
    r = siril_run(["-d", workdir, "-s", ssf], capture_output=True, text=True)
    text = r.stdout + r.stderr
    os.remove(ssf)
    # Anchor the parse on the SELECTION echo, never on the layer lines: Siril
    # `stat` excludes zero pixels from every estimator, so an ENTIRELY
    # zero-coverage box echoes its selection and then prints nothing. Anchored
    # on layer lines instead, that silence shifts every later box's numbers one
    # box up — the whole grid mis-attributed, with no error anywhere.
    per, cur = [], None
    for line in text.splitlines():
        m = SEL_RE.search(line)
        if m:
            cur = {"box": [int(v) for v in m.groups()], "chans": {}}
            per.append(cur)
            continue
        m = STAT_RE.search(line)
        if m and cur is not None:
            cur["chans"][m.group(1)] = {k: float(v) for k, v
                                        in m.groupdict().items()}
    if len(per) != len(boxes):
        sys.exit(f"coverage_frame: siril echoed {len(per)} selections for "
                 f"{len(boxes)} boxes — siril said:\n{text[-1200:]}")
    cells = []
    for (i, j, x, y), sel in zip(boxes, per):
        want = [x, H - y - bh, bw, bh]
        if sel["box"] != want:
            sys.exit(f"coverage_frame: selection echo {sel['box']} does not "
                     f"match the requested {want} at grid ({i},{j})")
        cells.append({"ij": [i, j], "box": [x, y, bw, bh],
                      "no_stat": not sel["chans"],
                      "min": {c: v["min"] for c, v in sel["chans"].items()},
                      "median": {c: v["median"]
                                 for c, v in sel["chans"].items()}})
    return cells, {"image_wh": [W, H], "grid": [nx, ny], "box_px": [bw, bh]}


def run(src, out_json, nx, ny, chan, floor, framing_record=None):
    src, out_json = os.path.abspath(src), os.path.abspath(out_json)
    workdir = os.path.dirname(out_json) or "."
    cells, geom = measure_grid(src, nx, ny, workdir)
    W, H = geom["image_wh"]
    bw, bh = geom["box_px"]
    vals = sorted(c["min"].get(chan, 0.0) for c in cells)
    qs = {f"p{int(100 * q)}": vals[int(q * (len(vals) - 1))]
          for q in (0.0, 0.05, 0.1, 0.25, 0.5, 0.75, 1.0)}
    zero = sum(1 for v in vals if v <= 0.0)
    print(f"grid {nx}x{ny} = {len(cells)} boxes of {bw}x{bh} px on {W}x{H}")
    print(f"  {chan} Min: {zero} box(es) at zero ({sum(1 for c in cells if c['no_stat'])} "
          f"with no stat at all — entirely uncovered), quantiles "
          + " ".join(f"{k} {v:.1f}" for k, v in qs.items()))
    band = sorted(v for v in vals if 0.0 < v < (floor or 0.0))
    if floor is not None:
        print(f"  floor {floor}: {len(band)} box(es) fall in (0, {floor}) — the "
              f"edge band — against a clean population starting at "
              f"{min((v for v in vals if v >= floor), default=float('nan')):.1f}")
    rec = {"source": src, "canvas_wh": [W, H], "grid": [nx, ny],
           "box_px": [bw, bh], "channel": chan, "floor": floor,
           "instrument": "Siril load + boxselect + stat (every per-box number "
                         "is Siril's); in-house is the grid bookkeeping and the "
                         "largest-all-covered-rectangle search",
           "criterion": f"a box is COVERED when Siril Min on the {chan} layer "
                        "is >= floor — the sibling-class sky floor, never mere "
                        "non-zero, and never the worst channel (the low channel "
                        "clips to zero on fully covered sky in this class)",
           "min_quantiles": qs, "zero_boxes": zero,
           "no_stat_boxes": sum(1 for c in cells if c["no_stat"]),
           "edge_band_boxes": len(band), "cells": cells}
    if floor is None:
        with open(out_json, "w") as fh:
            json.dump(rec, fh, indent=1)
        print(f"  no --floor given: measured only. record: {out_json}")
        return rec
    byij = {tuple(c["ij"]): c for c in cells}
    ok = [[byij[(i, j)]["min"].get(chan, 0.0) >= floor for i in range(nx)]
          for j in range(ny)]
    r = largest_rect(ok, nx, ny)
    if r is None:
        # REPORTS ONLY, so "nothing clears the floor" is a recorded finding, not
        # an exit code. It is also a real answer: this surface has no coverage
        # frame at this floor on this channel, and verify_framing has nothing to
        # be handed. Exiting here would additionally make the selftest's own
        # falsification step unobservable — it has to be able to WATCH the
        # clipping channel fail.
        rec["covered_boxes"] = 0
        rec["rect_fits"] = None
        print(f"  NO COVERAGE FRAME: not one box clears floor {floor} on the "
              f"{chan} layer — nothing is proposed")
        with open(out_json, "w") as fh:
            json.dump(rec, fh, indent=1)
        print(f"  record: {out_json}")
        return rec
    i0, j0, i1, j1 = r
    x, y = i0 * bw, j0 * bh
    w, h = (i1 - i0 + 1) * bw, (j1 - j0 + 1) * bh
    rec["covered_boxes"] = sum(sum(1 for v in row if v) for row in ok)
    rec["rect_fits"] = [x, y, w, h]
    rec["rect_siril_crop_args"] = [x, H - y - h, w, h]
    rec["rect_frac_of_canvas"] = w * h / float(W * H)
    print(f"  {rec['covered_boxes']}/{len(cells)} boxes covered; largest "
          f"rectangle FITS x={x} y={y} w={w} h={h} "
          f"({100 * rec['rect_frac_of_canvas']:.1f}% of the canvas)")
    print(f"  siril crop args (y from the TOP): {rec['rect_siril_crop_args']}")
    print("  the rectangle is a PROPOSAL — web/verify_framing.py decides")
    if framing_record:
        hdr = fits.getheader(src)
        fr = {"product": os.path.basename(src)[:-4],
              "canvas_wh": [W, H], "rect_fits": [x, y, w, h],
              "rect_siril_crop_args": rec["rect_siril_crop_args"],
              "source": f"DERIVED by scripts/qa/coverage_frame.py from Siril "
                        f"stat over a {nx}x{ny} grid, floor {floor} on {chan}",
              "status": "unverified"}
        try:
            wcs = WCS(hdr, naxis=2)
            fr["radec_corners_deg"] = [
                [float(v) for v in wcs.all_pix2world([[px, py]], 0)[0]]
                for px, py in ((x, y + h), (x + w, y + h), (x + w, y), (x, y))]
            fr["scale_deg_per_px"] = float(math.sqrt(
                abs(np.linalg.det(wcs.pixel_scale_matrix))))
        except Exception as exc:                      # noqa: BLE001 — reported
            print(f"  (no WCS on this surface: {type(exc).__name__} — the "
                  f"framing record carries no RA/Dec corners, so a consumer "
                  f"cannot derive its field width)")
        with open(framing_record, "w") as fh:
            json.dump(fr, fh, indent=1)
            fh.write("\n")
        print(f"  framing record (UNVERIFIED): {framing_record}")
    with open(out_json, "w") as fh:
        json.dump(rec, fh, indent=1)
    print(f"  record: {out_json}")
    return rec


# --------------------------------------------------------------- selftest ---
def selftest(keep=False):
    """Plant a coverage frame this code did not choose, then make it find it —
    and make the known failure mode actually fail."""
    work = os.path.expanduser("~/.cache/astro-imaging/coverage_frame_selftest")
    if os.path.isdir(work):
        shutil.rmtree(work)
    os.makedirs(work)
    W, H, ok = 800, 500, True
    # PLANTED TRUTH: sky everywhere inside the box, hard zero outside it, and a
    # ring of half-level "edge ringing" just inside the zero — the residue the
    # sibling-class floor exists to reject and a Min>0 test would accept.
    # DELIBERATELY ASYMMETRIC IN y: with a vertically centred box the top-down
    # crop args equal the bottom-up FITS args and step 2 passes without testing
    # anything. Here y=100 h=250 gives crop y=150, so a flipped convention reads
    # a different band of rows and step 2 goes RED.
    # The ringing band is a WHOLE GRID BOX wide on every side, deliberately: a
    # band narrower than a box never forms a box that is purely ringing, every
    # such box straddles the true zero and reads Min 0, and step 3's non-zero
    # falsification then cannot grow the rectangle — it passes for the wrong
    # reason. (That is how this fixture failed on its first run.)
    X0, Y0, X1, Y1 = 160, 100, 640, 350      # the covered box, FITS pixels
    RX, RY = 80, 50                          # ringing band, one box each way
    sky = np.zeros((3, H, W), dtype="float32")
    rng = np.random.default_rng(20260812)
    sky[1, Y0 - RY:Y1 + RY, X0 - RX:X1 + RX] = 45.0     # ringing band, Green
    sky[1, Y0:Y1, X0:X1] = 90.0 + rng.normal(0, 0.5, (Y1 - Y0, X1 - X0))
    # the LOW channel clips to zero inside covered sky — the measured OSC case
    sky[0, Y0:Y1, X0:X1] = 0.0
    sky[2, Y0:Y1, X0:X1] = 60.0
    path = os.path.join(work, "synth.fit")
    fits.writeto(path, (sky / 65535.0).astype("float32"), overwrite=True)

    print("=== step 1: the planted frame is recovered on the reference channel")
    r = run(path, os.path.join(work, "cov.json"), 20, 10, "Green", 80.0)
    x, y, w, h = r["rect_fits"]
    bw, bh = r["box_px"]
    # the grid is conservative by a box: any box touching the ring or the zero
    # is excluded, so the found rect sits INSIDE the planted one by < 1 box
    inside = (x >= X0 - bw and y >= Y0 - bh
              and x + w <= X1 + bw and y + h <= Y1 + bh)
    covers = (x <= X0 + bw and y <= Y0 + bh
              and x + w >= X1 - bw and y + h >= Y1 - bh)
    step1 = inside and covers
    print(f"    found FITS [{x} {y} {w} {h}] against planted "
          f"[{X0} {Y0} {X1 - X0} {Y1 - Y0}], grid box {bw}x{bh} -> "
          f"{'GREEN' if step1 else 'RED'}")
    ok &= step1

    print("=== step 2: y CONVENTION — the crop args must address the SAME rows")
    # boxselect counts y from the top; the record carries both. Re-measuring the
    # proposed rectangle through Siril's own crop must reproduce a covered frame.
    ssf = os.path.join(work, "_c.ssf")
    cx, cy, cw, ch = r["rect_siril_crop_args"]
    with open(ssf, "w") as fh:
        fh.write(f"requires 1.2.0\nsetcompress 0\nsetext fit\nload {path}\n"
                 f"crop {cx} {cy} {cw} {ch}\nstat\n")
    res = siril_run(["-d", work, "-s", ssf], capture_output=True, text=True)
    gmin = None
    for m in STAT_RE.finditer(res.stdout + res.stderr):
        if m.group(1) == "Green":
            gmin = float(m.group("min"))
    step2 = gmin is not None and gmin >= 80.0
    print(f"    Siril crop{r['rect_siril_crop_args']} reads Green Min {gmin} "
          f"(bar 80.0) -> {'GREEN' if step2 else 'RED — the y origin flipped'}")
    ok &= step2

    print("=== step 3: FALSIFICATION — the known failure modes must FAIL")
    r_low = run(path, os.path.join(work, "cov_red.json"), 20, 10, "Red", 80.0)
    step3a = r_low.get("rect_fits") is None and r_low["covered_boxes"] == 0
    print(f"    floor on the CLIPPING channel: {r_low['covered_boxes']} boxes "
          f"covered -> {'RED as required' if step3a else 'NOT RED — the low '
                        'channel silently passed'}")
    r_nz = run(path, os.path.join(work, "cov_nz.json"), 20, 10, "Green", 0.001)
    x2, y2, w2, h2 = r_nz["rect_fits"]
    step3b = w2 * h2 > r["rect_fits"][2] * r["rect_fits"][3]
    print(f"    mere non-zero: rectangle grows to {w2}x{h2} from {w}x{h} — it "
          f"swallows the ringing band -> "
          f"{'RED as required' if step3b else 'NOT RED — the floor does nothing'}")
    ok &= step3a and step3b

    if not keep:
        shutil.rmtree(work)
    else:
        print(f"\nfixture kept at {work}")
    print(f"\nSELFTEST {'PASS' if ok else 'FAIL'}")
    return 0 if ok else 1


def main():
    argv = sys.argv[1:]
    if "--selftest" in argv:
        return selftest(keep="--keep" in argv)
    args = [a for a in argv if not a.startswith("--")]
    opts = dict(a[2:].split("=", 1) for a in argv
                if a.startswith("--") and "=" in a)
    if len(args) != 2:
        sys.exit(__doc__)
    nx, ny = (int(v) for v in opts.get("grid", "80x50").split("x"))
    run(args[0], args[1], nx, ny, opts.get("channel", "Green"),
        float(opts["floor"]) if "floor" in opts else None,
        opts.get("framing-record"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
