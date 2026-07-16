#!/usr/bin/env python3
"""Radial profile of star shape across a frame, from a Siril findstar list.

Usage: star_shape_profile.py <stars.lst> [--center=<x>,<y>] [--bins=N]
                             [--json=<out.json>] [--label=<name>]

Why this exists: a registration model that cannot express the true
frame-to-frame mapping leaves a residual that GROWS WITH FIELD RADIUS —
sharp at the centre, smeared at the edges. A whole-frame median hides
exactly that: it averages the good centre into the bad edge and reports one
mediocre number. Binning star shape by distance from the optical axis is the
measurement that separates "the registration model is wrong" (shape degrades
with radius) from "the frames themselves are soft" (shape flat vs radius).

Siril does every pixel operation and every measurement: `findstar` fits the
PSF and writes FWHMx/FWHMy/X/Y per star. This script reads that text list and
only bins it — no pixel is read here, no threshold gates anything, and it
reports rather than decides. It computes the one derived quantity no Siril
command outputs headless: the radial profile.

Roundness is reported as minor/major = min(FWHMx,FWHMy)/max(FWHMx,FWHMy), so
1.0 is round and smaller is more elongated. Note this differs from Siril's own
"roundness" (FWHMy/FWHMx, which is orientation-dependent and can exceed 1) and
from eccentricity e=sqrt(1-(b/a)^2) — three related but distinct measures; the
minor/major form is used here because it is orientation-blind, which a smear
that changes direction across the field requires.

The centre defaults to the image centre inferred from the star bounding box.
Pass --center= when the frame has been cropped off-axis (a registration
`-framing=min` crop of a drifting sequence is NOT centred on the optical axis,
and radial structure read about the wrong centre looks like a one-sided
gradient).

Removal condition: retire this when a tool reports a headless radial star-shape
profile directly (Siril's aberration inspector is GUI-only as of 1.4.4).
"""
import json
import sys


def read_lst(path):
    """Parse a Siril findstar list -> list of (x, y, fwhmx, fwhmy, angle).

    Siril writes a '#'-commented header then tab-separated columns:
    star# layer B A beta X Y FWHMx FWHMy FWHMx" FWHMy" angle RMSE mag ...
    """
    out = []
    for line in open(path):
        if line.startswith("#") or not line.strip():
            continue
        f = line.split("\t")
        try:
            out.append((float(f[5]), float(f[6]), float(f[7]),
                        float(f[8]), float(f[11])))
        except (IndexError, ValueError):
            continue
    return out


def median(v):
    s = sorted(v)
    n = len(s)
    if not n:
        return float("nan")
    return s[n // 2] if n % 2 else 0.5 * (s[n // 2 - 1] + s[n // 2])


def profile(stars, cx, cy, nbins):
    rows = []
    for x, y, fx, fy, _ in stars:
        major, minor = max(fx, fy), min(fx, fy)
        r = ((x - cx) ** 2 + (y - cy) ** 2) ** 0.5
        rows.append((r, minor / major if major else float("nan"), major))
    if not rows:
        return []
    rmax = max(r for r, _, _ in rows)
    out = []
    for i in range(nbins):
        lo, hi = i * rmax / nbins, (i + 1) * rmax / nbins
        sel = [t for t in rows if lo <= t[0] < hi]
        if len(sel) < 20:
            continue
        out.append({"r_lo": round(lo, 1), "r_hi": round(hi, 1),
                    "n": len(sel),
                    "roundness": round(median([t[1] for t in sel]), 4),
                    "major_fwhm_px": round(median([t[2] for t in sel]), 3)})
    return out


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    opts = dict(a[2:].split("=", 1) for a in sys.argv[1:] if a.startswith("--"))
    if not args:
        sys.exit(__doc__)
    stars = read_lst(args[0])
    if not stars:
        sys.exit(f"star_shape_profile: no stars parsed from {args[0]}")
    xs = [s[0] for s in stars]
    ys = [s[1] for s in stars]
    if "center" in opts:
        cx, cy = (float(v) for v in opts["center"].split(","))
    else:
        cx, cy = 0.5 * (min(xs) + max(xs)), 0.5 * (min(ys) + max(ys))
    nbins = int(opts.get("bins", 6))
    prof = profile(stars, cx, cy, nbins)
    rec = {"input": args[0], "label": opts.get("label"),
           "n_stars": len(stars), "center": [round(cx, 1), round(cy, 1)],
           "whole_frame": {
               "roundness": round(median([min(s[2], s[3]) / max(s[2], s[3])
                                          for s in stars]), 4),
               "major_fwhm_px": round(median([max(s[2], s[3])
                                              for s in stars]), 3)},
           "radial_profile": prof,
           "measured_by": "Siril findstar PSF fits (this script only bins them)"}
    lab = f" [{rec['label']}]" if rec["label"] else ""
    print(f"{len(stars)} stars{lab}  centre=({cx:.0f},{cy:.0f})  "
          f"whole-frame roundness={rec['whole_frame']['roundness']:.3f} "
          f"majFWHM={rec['whole_frame']['major_fwhm_px']:.2f}px")
    print(f"{'r range (px)':>18}  {'n':>5}  {'roundness':>9}  {'majFWHM':>8}")
    for b in prof:
        print(f"{b['r_lo']:8.0f}-{b['r_hi']:<8.0f}  {b['n']:5d}  "
              f"{b['roundness']:9.3f}  {b['major_fwhm_px']:8.2f}")
    if "json" in opts:
        json.dump(rec, open(opts["json"], "w"), indent=1)
        print(f"wrote {opts['json']}")


if __name__ == "__main__":
    main()
