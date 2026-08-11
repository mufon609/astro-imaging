#!/usr/bin/env python3
"""Record Siril `findstar` PSF fits in boxes placed at SKY positions by the
product's own solved WCS — the acceptance instrument for combined products.

Usage: shape_at_sky.py <solved.fit> --pos RA,DEC[,label] [--pos ...]
                       [--box=800] [--top=30] [--json=<out>] [--label=<name>]

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
convention ships a mirrored window, and this check makes that impossible to
miss). The y convention is resolved by that verification: if every box lands
mirrored, the other convention is tried ONCE and the one that verifies is
recorded in the output.

A position whose box would fall outside the canvas is an ERROR, not a smaller
box (equal-area discipline, star_stations.py).

Removal condition: retire when an official tool reports headless star-shape
statistics for a sky-addressed region of a solved image (a scriptable
`findstar` with a WCS-addressed subregion, or a PixInsight equivalent).
Registered in BACKLOG `removal-conditions`.
"""
import argparse
import json
import math
import os
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


def measure(image, positions, box, top, y_top_origin):
    """One siril pass: crop every position's box, findstar each. Returns rows."""
    from astropy.io import fits
    from astropy.wcs import WCS
    hdr = fits.getheader(image)
    W, H = int(hdr["NAXIS1"]), int(hdr["NAXIS2"])
    wcs = WCS(hdr, naxis=2)      # RGB stacks are 3-plane; SIP is 2-D only
    out = []
    with tempfile.TemporaryDirectory(dir=os.path.expanduser("~/.cache")) as work:
        ssf = os.path.join(work, "m.ssf")
        with open(ssf, "w") as f:
            f.write(f"requires 1.4.4\nsetcompress 0\nsetext fit\n{GATE}\n")
            for i, (ra, dec, label) in enumerate(positions):
                px = wcs.all_world2pix([[ra, dec]], 0)[0]
                x0, y0 = float(px[0]), float(px[1])
                x = int(round(x0 - box / 2))
                y_fits = int(round(y0 - box / 2))
                y = (H - y_fits - box) if y_top_origin else y_fits
                if x < 0 or y < 0 or x + box > W or y + box > H:
                    raise SystemExit(
                        f"ERROR: box for {label} (RA {ra} Dec {dec}) at pixel "
                        f"({x0:.0f},{y0:.0f}) does not fit the {W}x{H} canvas — "
                        "a shrunk box breaks the equal-area comparison")
                lst = os.path.join(work, f"p{i}.lst")
                f.write(f"load {image}\ncrop {x} {y} {box} {box}\n"
                        f"findstar -out={lst}\n")
                out.append({"label": label, "ra": ra, "dec": dec,
                            "pixel_xy": [round(x0, 1), round(y0, 1)],
                            "crop": [x, y, box, box], "lst": lst})
        r = siril_run.run(["-d", work, "-s", ssf], capture_output=True, text=True)
        for row in out:
            if not os.path.exists(row["lst"]):
                raise SystemExit(f"findstar wrote no list for {row['label']} — "
                                 f"siril said:\n{(r.stdout or '')[-800:]}")
            rows = read_lst(row.pop("lst"))
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


def main():
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("image")
    ap.add_argument("--pos", action="append", required=True,
                    help="RA,DEC[,label] in degrees; repeatable")
    ap.add_argument("--box", type=int, default=800)
    ap.add_argument("--top", type=int, default=30)
    ap.add_argument("--json")
    ap.add_argument("--label", default="")
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

    rows, convention = None, None
    for y_top in (False, True):
        got = measure(image, positions, a.box, a.top, y_top)
        offs = [r.get("box_center_offset_deg") for r in got]
        if any(o is None for o in offs):
            # no solved star positions to verify with — cannot resolve the flip
            raise SystemExit("ERROR: findstar emitted no per-star RA/Dec (image "
                             "unsolved?) — the box placement cannot be verified")
        if all(o <= tol for o in offs):
            rows, convention = got, ("top" if y_top else "bottom")
            break
        print(f"  [shape_at_sky] y-origin={'top' if y_top else 'bottom'} places "
              f"boxes {max(offs):.2f} deg off target (tol {tol:.2f}) — "
              "trying the other convention", file=sys.stderr)
    if rows is None:
        raise SystemExit("ERROR: neither crop y-convention lands the boxes on "
                         "target — placement broken, refusing to report shapes")

    rec = {"image": image, "label": a.label or os.path.basename(image),
           "instrument": (f"Siril findstar ({GATE}), {a.box} px boxes placed by "
                          f"the product's own WCS (y-origin {convention}, "
                          "verified by the tool's own per-star RA/Dec); FWHM = "
                          "median (FWHMx+FWHMy)/2, roundness = median min/max, "
                          f"over the {a.top} brightest fits"),
           "positions": rows}
    for r in rows:
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
