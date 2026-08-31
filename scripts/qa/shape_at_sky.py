#!/usr/bin/env python3
"""Record Siril `findstar` PSF fits in boxes placed at SKY positions by the
product's own solved WCS — the acceptance instrument for combined products.

Usage: shape_at_sky.py <solved.fit> --pos RA,DEC[,label] [--pos ...]
                       [--box=800] [--top=30] [--json=<out>] [--label=<name>]
                       [--lst-dir=<dir>]
       shape_at_sky.py --selftest      (data-free: the placement rule's controls)

Why this exists: the compose-registration defect class is invisible to every
per-member measure and to whole-frame statistics — it lives at specific SKY
positions of a combined canvas (measured: roundness 0.458 at RA 294.86 on a
28-member union whose members each read 0.92+ there). Comparing products of
different canvases/depths at the SAME SKY therefore needs boxes placed by each
product's OWN plate solution, and a shape median is only comparable
rank-matched (a deeper image admits fainter, worse-fitted stars — the
detection-depth trap) and WITH its n (survivorship trap). This records, per
position: n, the median FWHM=(FWHMx+FWHMy)/2 and roundness=min/max over the
`--top` brightest fits (by the tool's own amplitude A), and the faintest
admitted amplitude.

Every fit is Siril's (`findstar`, open gate: reset -roundness=0.10 -relax=on
-maxR=1.0 — the default 0.50 roundness floor truncates exactly the elongated
tail under study); placement is header-only astropy WCS; this script computes
only medians/ratios of the tool's own per-star numbers, like star_stations.py.

THE BOX PLACEMENT IS VERIFIED BY THE TOOL, NEVER TRUSTED: Siril `crop` keeps
the solved WCS, and `findstar` on a solved image emits each star's RA/Dec, so
after measuring, the median star sky-position must sit inside the box of the
target (the numpy-vs-Siril crop y-flip is a registered trap — a wrong
convention ships a mirrored window). BOTH crop y-conventions are run, and the
one whose boxes land closer (the smaller median offset) is accepted — ONLY if
the two passes differ by more than the tolerance at some box; otherwise the
box set cannot tell the conventions apart and this refuses.
THE MECHANISM THE OLD RULE MISSED (first pass under tolerance wins): the wrong
convention mirrors a box about the centre row, displacing it by 2·|y0 − H/2|;
a set whose boxes all lie within ~300 px of the centre row keeps every
mirrored box inside the 2.83° tolerance (box/2 × scale × 1.5 ≈ 600 px), so the
wrong convention VERIFIED and shipped displaced boxes — GO #6's record: the
corpus boxes +136..+270 px, 96 of 190 member boxes 8–602 px (median 349).
Registry: docs/dead-ends/verification-traps.md, the entry headlined
"shape_at_sky's crop-flip check passed the wrong convention on mid-row box sets".

A position whose box would fall outside the canvas is an ERROR, not a smaller
box (equal-area discipline, star_stations.py).

Removal condition: retire when an official tool reports headless star-shape
statistics for a sky-addressed region of a solved image (a scriptable
`findstar` with a WCS-addressed subregion, or a PixInsight equivalent).
"""
import argparse
import json
import math
import os
import shutil
import statistics
import sys
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "lib"))
import siril_run

GATE = "setfindstar reset -roundness=0.10 -relax=on -maxR=1.0"
RADEC_SENTINEL = 1e6          # findstar prints 9.99e9 when the image is unsolved


def read_lst(path):
    """findstar list rows: (A, FWHMx, FWHMy, RA, Dec) — tool columns 3/7/8/16/17."""
    rows = []
    with open(path) as f:
        for line in f:
            if line.startswith("#"):
                continue
            p = line.split()
            if len(p) < 18:
                continue
            rows.append((float(p[3]), float(p[7]), float(p[8]),
                         float(p[16]), float(p[17])))
    return rows


def ang_sep_deg(ra1, dec1, ra2, dec2):
    a, b = math.radians(dec1), math.radians(dec2)
    dra = math.radians(ra1 - ra2)
    x = (math.sin(a) * math.sin(b) + math.cos(a) * math.cos(b) * math.cos(dra))
    return math.degrees(math.acos(max(-1.0, min(1.0, x))))


def measure(image, positions, box, top, y_top_origin, work, tag):
    """One siril pass: crop every position's box, findstar each. Returns rows.

    The tool's own per-position star lists stay in `work` (named by `tag`, so
    the two convention passes never overwrite each other) and each row keeps
    its `lst` path; the caller copies the ACCEPTED pass's lists out, so a later
    re-summary of the SAME fits under a different depth-matching rule (a common
    amplitude floor rather than top-N) needs no second Siril pass.
    """
    from astropy.io import fits
    from astropy.wcs import WCS
    hdr = fits.getheader(image)
    W, H = int(hdr["NAXIS1"]), int(hdr["NAXIS2"])
    wcs = WCS(hdr, naxis=2)      # RGB stacks are 3-plane; SIP is 2-D only
    out = []
    ssf = os.path.join(work, f"{tag}.ssf")
    with open(ssf, "w") as f:
        f.write(f"requires 1.4.4\nsetcompress 0\nsetext fit\n{GATE}\n")
        for i, (ra, dec, label) in enumerate(positions):
            px = wcs.all_world2pix([[ra, dec]], 0)[0]
            x0, y0 = float(px[0]), float(px[1])
            x = int(round(x0 - box / 2))
            y_fits = int(round(y0 - box / 2))
            y = (H - y_fits - box) if y_top_origin else y_fits
            if x < 0 or y < 0 or x + box > W or y + box > H:
                # never a smaller box (equal-area discipline) — the position
                # is reported OUT-OF-CANVAS and excluded from statistics, so
                # a product that does not cover a target says so plainly
                # (the fit test is the same under both conventions)
                out.append({"label": label, "ra": ra, "dec": dec,
                            "pixel_xy": [round(x0, 1), round(y0, 1)],
                            "out_of_canvas": True})
                continue
            lst = os.path.join(work, f"{tag}_p{i}.lst")
            f.write(f"load {image}\ncrop {x} {y} {box} {box}\n"
                    f"findstar -out={lst}\n")
            out.append({"label": label, "ra": ra, "dec": dec,
                        "pixel_xy": [round(x0, 1), round(y0, 1)],
                        "crop": [x, y, box, box], "lst": lst})
    r = siril_run.run(["-d", work, "-s", ssf], capture_output=True, text=True)
    for row in out:
        if row.get("out_of_canvas"):
            continue
        if not os.path.exists(row["lst"]):
            raise SystemExit(f"findstar wrote no list for {row['label']} — "
                             f"siril said:\n{(r.stdout or '')[-800:]}")
        rows = read_lst(row["lst"])
        row["n"] = len(rows)
        if not rows:
            continue
        solved = [t for t in rows if abs(t[3]) < RADEC_SENTINEL]
        if solved:
            mra = statistics.median(t[3] for t in solved)
            mdec = statistics.median(t[4] for t in solved)
            row["box_center_offset_deg"] = round(
                ang_sep_deg(mra, mdec, row["ra"], row["dec"]), 3)
        bright = sorted(rows, key=lambda t: -t[0])[:top]
        row["top_n"] = len(bright)
        row["fwhm_px"] = round(statistics.median(
            (t[1] + t[2]) / 2 for t in bright), 3)
        row["roundness"] = round(statistics.median(
            min(t[1], t[2]) / max(t[1], t[2]) for t in bright), 3)
        row["faintest_admitted_A"] = round(min(t[0] for t in rows), 6)
    return out


def old_rule(off_bottom, off_top, tol):
    """THE RETIRED RULE, kept only for the selftest's control: the first
    convention whose boxes all verify within tolerance wins (bottom tried first)."""
    if all(o <= tol for o in off_bottom):
        return "bottom"
    if all(o <= tol for o in off_top):
        return "top"
    return None


def resolve_convention(off_bottom, off_top, tol, box):
    """Choose the crop y-convention from the two passes' per-box offsets (deg).

    Accepts the convention with the SMALLER median offset, and only when the
    passes differ by more than the tolerance at some box — the wrong convention
    displaces a box by 2·|y0 − H/2| px, so a set lying within box·0.375 px of
    the centre row cannot distinguish them and is REFUSED. The accepted pass
    must still land every box within tolerance. Returns (convention, info)."""
    pairs = list(zip(off_bottom, off_top))
    if not pairs:
        return None, {"note": "every position out of canvas"}
    if any(b is None or t is None for b, t in pairs):
        raise SystemExit("ERROR: findstar emitted no per-star RA/Dec (image "
                         "unsolved?) — the box placement cannot be verified")
    margin = max(abs(b - t) for b, t in pairs)
    mb, mt = statistics.median(off_bottom), statistics.median(off_top)
    if margin <= tol or mb == mt:
        raise SystemExit(
            f"REFUSED: the two crop y-conventions cannot be told apart by this "
            f"box set — they differ by at most {margin:.2f} deg against a "
            f"tolerance of {tol:.2f} (median offsets bottom {mb:.2f} / top "
            f"{mt:.2f}). The wrong convention mirrors a box about the centre "
            f"row by 2*|y0 - H/2| px, and every box here lies within "
            f"~{box * 0.375:.0f} px of it, so either convention would 'verify'. "
            f"Add one position more than {box * 0.375:.0f} px from the centre "
            f"row (a sentinel box is fine; its reading is yours to discard).")
    conv = "top" if mt < mb else "bottom"
    accepted = [t if conv == "top" else b for b, t in pairs]
    if max(accepted) > tol:
        raise SystemExit(
            f"ERROR: the better crop y-convention ({conv}) still places a box "
            f"{max(accepted):.2f} deg off target (tol {tol:.2f}) — placement "
            "broken, refusing to report shapes")
    return conv, {"median_offset_bottom_deg": round(mb, 3),
                  "median_offset_top_deg": round(mt, 3),
                  "max_pass_difference_deg": round(margin, 3),
                  "tolerance_deg": round(tol, 3)}


def selftest():
    """Data-free controls for the placement rule. Plants a canvas geometry and
    per-box offsets: the RIGHT convention reads a small offset, the WRONG one
    the mirror displacement 2·|y0 − H/2| in degrees. Evaluates the retired rule
    and the current rule on the SAME plants."""
    H, scale, box = 5677, 0.004722, 800          # the corpus canvas, 17"/px
    tol = box / 2 * scale * 1.5
    right = 0.10

    def plant(ys, truth):
        wrong = [abs(H - 2 * y0) * scale for y0 in ys]
        ok = [right] * len(ys)
        # returns (bottom-pass offsets, top-pass offsets): the TRUE convention
        # reads the small offset, the other the mirror displacement
        return (wrong, ok) if truth == "top" else (ok, wrong)

    def new(b, t):
        try:
            return resolve_convention(b, t, tol, box)[0]
        except SystemExit as e:
            return f"REFUSED({str(e)[:8]})"

    fails = 0
    def check(name, cond, detail):
        nonlocal fails
        print(f"  {'PASS' if cond else 'FAIL'}  {name}: {detail}")
        if not cond:
            fails += 1

    # (i) GO #6's own corpus rows: every box within 136-270 px of the centre row
    b, t = plant([2906.6, 2940.2, 2973.7], "top")
    o, n = old_rule(b, t, tol), new(b, t)
    check("mid-row set, OLD rule accepts the WRONG convention (the control)",
          o == "bottom", f"truth top, old rule -> {o}; wrong-pass offsets "
          f"{[round(x, 2) for x in b]} deg all <= tol {tol:.2f}")
    check("mid-row set, NEW rule refuses", n.startswith("REFUSED"),
          f"new rule -> {n} (max pass difference {max(abs(x - y) for x, y in zip(b, t)):.2f} <= tol)")
    # (ii) one far-from-centre box: both rules resolve to the truth
    for truth in ("top", "bottom"):
        b, t = plant([2940.2, 1476.0], truth)
        o, n = old_rule(b, t, tol), new(b, t)
        check(f"far box (1476 of 5677), truth {truth}: old -> truth", o == truth, f"old rule -> {o}")
        check(f"far box (1476 of 5677), truth {truth}: new -> truth", n == truth,
              f"new rule -> {n} (wrong-pass offset at the far box {abs(H - 2 * 1476.0) * scale:.2f} deg)")
    # (iii) boxes on the centre row: the passes are identical -> refused
    b, t = plant([H / 2], "top")
    n = new(b, t)
    check("centre-row set (passes equal), NEW rule refuses", n.startswith("REFUSED"),
          f"offsets bottom {b} top {t} -> {n}")
    # (iv) decisive set but the better pass still misses tolerance -> refused
    b, t = plant([2940.2, 1476.0], "top")
    t = [3.5, 3.5]
    n = new(b, t)
    check("better pass beyond tolerance -> refused", n.startswith("REFUSED") or n is None,
          f"top offsets {t} vs tol {tol:.2f} -> {n}")
    print(f"shape_at_sky --selftest: {'PASS' if fails == 0 else f'{fails} FAILED'}")
    return 0 if fails == 0 else 1


def main():
    if "--selftest" in sys.argv[1:]:
        sys.exit(selftest())
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("image")
    ap.add_argument("--pos", action="append", required=True,
                    help="RA,DEC[,label] in degrees; repeatable")
    ap.add_argument("--box", type=int, default=800)
    ap.add_argument("--top", type=int, default=30)
    ap.add_argument("--json")
    ap.add_argument("--label", default="")
    ap.add_argument("--lst-dir", dest="lst_dir",
                    help="keep the tool's own per-position star lists here")
    a = ap.parse_args()
    image = os.path.abspath(a.image)
    positions = []
    for p in a.pos:
        parts = p.split(",")
        positions.append((float(parts[0]), float(parts[1]),
                          parts[2] if len(parts) > 2 else f"RA{parts[0]}"))

    # box-half in degrees, from the WCS scale — the verification tolerance
    from astropy.io import fits
    from astropy.wcs import WCS
    hdr = fits.getheader(image)
    if hdr.get("A_ORDER") is None and "CD1_1" not in hdr and "CDELT1" not in hdr:
        raise SystemExit("ERROR: image carries no plate solution — this "
                         "instrument places boxes by the product's OWN WCS")
    scale_deg = abs(WCS(hdr, naxis=2).proj_plane_pixel_scales()[0].value)
    tol = a.box / 2 * scale_deg * 1.5

    with tempfile.TemporaryDirectory(dir=os.path.expanduser("~/.cache")) as work:
        passes = {c: measure(image, positions, a.box, a.top, c == "top", work, c)
                  for c in ("bottom", "top")}
        offs = {c: [r.get("box_center_offset_deg") for r in passes[c]
                    if not r.get("out_of_canvas")] for c in passes}
        convention, info = resolve_convention(offs["bottom"], offs["top"], tol, a.box)
        rows = passes[convention or "top"]
        rejected = passes["bottom" if convention == "top" else "top"]
        for r in rows:
            lst = r.pop("lst", None)
            if lst and a.lst_dir:
                os.makedirs(a.lst_dir, exist_ok=True)
                shutil.copy(lst, os.path.join(a.lst_dir, f"{r['label']}.lst"))
        info["rejected_pass_offsets_deg"] = {
            r["label"]: r.get("box_center_offset_deg") for r in rejected
            if not r.get("out_of_canvas")}
    conv_txt = convention or "n/a (every position out of canvas)"
    print(f"  [shape_at_sky] y-origin {conv_txt}: median offset bottom "
          f"{info.get('median_offset_bottom_deg', float('nan')):.2f} / top "
          f"{info.get('median_offset_top_deg', float('nan')):.2f} deg, passes differ by "
          f"{info.get('max_pass_difference_deg', float('nan')):.2f} (tol {tol:.2f})",
          file=sys.stderr)

    rec = {"image": image, "label": a.label or os.path.basename(image),
           "instrument": (f"Siril findstar ({GATE}), {a.box} px boxes placed by "
                          f"the product's own WCS (y-origin {conv_txt}, "
                          "verified by the tool's own per-star RA/Dec against "
                          "BOTH crop conventions — the smaller median offset, "
                          "accepted only where the passes differ by more than "
                          "the tolerance); FWHM = "
                          "median (FWHMx+FWHMy)/2, roundness = median min/max, "
                          f"over the {a.top} brightest fits"),
           "placement": {"y_origin": conv_txt, **info},
           "positions": rows}
    for r in rows:
        if r.get("out_of_canvas"):
            print(f"  {r['label']:<14} OUT OF CANVAS (pixel {r['pixel_xy']})")
            continue
        print(f"  {r['label']:<14} n={r['n']:5d}  "
              f"FWHM={r.get('fwhm_px', float('nan')):6.3f} px  "
              f"roundness={r.get('roundness', float('nan')):5.3f}  "
              f"(top {r.get('top_n', 0)}, box offset "
              f"{r.get('box_center_offset_deg', -1):.3f} deg)")
    if a.json:
        json.dump(rec, open(a.json, "w"), indent=1)
        print(f"  record -> {a.json}")


if __name__ == "__main__":
    main()
