#!/usr/bin/env python3
"""Crop a drift-composited stack to its coverage-complete rectangle.

A long untracked sequence drifts and rotates, so the registered stack's
border band is covered by only a subset of frames: rejection zeroes the
uncovered contributions and the band reads as a large fake falloff (a
long drifting set can lose tens of percent at the rim while its interior
is flat, unlike a rigidly-registered set whose fully-covered borders
carry only a small level plane).
Downstream assumes uniform sky statistics (the gate's statistical block
selection would embrace the dark band), so the stack ships only the
region every kept frame covered.

Bounds come from a bounds JSON (computed once per SET from the union
variant so every stack variant crops IDENTICALLY and stays comparable):
  {"top": r0, "bottom": r1, "left": c0, "right": c1, "basis": "..."}
rows r0..r1 and cols c0..c1 inclusive, in FILE pixel order.

Usage: crop_coverage.py <in.fit> <out.fit> --bounds <bounds.json>
"""
import argparse
import json
import os
import sys

# scripts/lib holds the shared libs (astrometrics, bg_qa); locate it by
# walking up from this file so one bootstrap works at any nesting depth.
_libdir = os.path.dirname(os.path.abspath(__file__))
while _libdir != os.path.dirname(_libdir):
    if os.path.isdir(os.path.join(_libdir, "lib")):
        sys.path.insert(0, os.path.join(_libdir, "lib"))
        break
    _libdir = os.path.dirname(_libdir)
import astrometrics as am  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("src")
    ap.add_argument("dst")
    ap.add_argument("--bounds", required=True)
    args = ap.parse_args()
    b = json.load(open(args.bounds))
    cards, planes, _ = am.read_fits_planes(args.src)
    nc, ny, nx = planes.shape
    t, bo, l, r = b["top"], b["bottom"], b["left"], b["right"]
    if not (0 <= t < bo < ny and 0 <= l < r < nx):
        sys.exit(f"bounds {t}..{bo} x {l}..{r} out of range for "
                 f"{nx}x{ny}")
    out = planes[:, t:bo + 1, l:r + 1].copy()
    am.write_fits_planes(args.dst, cards, out)
    print(f"crop_coverage: {nx}x{ny} -> {out.shape[2]}x{out.shape[1]} "
          f"(rows {t}..{bo}, cols {l}..{r}; "
          f"{100 * out.shape[1] * out.shape[2] / (nx * ny):.1f}% kept) "
          f"-> {args.dst}")


if __name__ == "__main__":
    main()
