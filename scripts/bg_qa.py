#!/usr/bin/env python3
"""Whole-frame background QA for a stretched preview JPEG.

Blocks the full frame (star-robust medians), excludes only the known branch
corner, and reports: luminance uniformity (P5/P50/P95, worst blocks) and
color neutrality (worst |R-G|, |B-G|). PASS/FAIL per fixed thresholds so a
recipe can't be graded by hand-picked patches.
"""
import sys
import numpy as np
from PIL import Image

BLOCK = 200
LUM_RATIO_MAX = 1.6     # brightest block / median block luminance
COLOR_DEV_MAX = 7.0     # worst |R-G| or |B-G| among blocks (8-bit counts)

a = np.asarray(Image.open(sys.argv[1]), dtype=np.float64)
h, w, _ = a.shape
gy, gx = h // BLOCK, w // BLOCK
blocks = a[:gy*BLOCK, :gx*BLOCK].reshape(gy, BLOCK, gx, BLOCK, 3)
med = np.median(blocks.transpose(0, 2, 1, 3, 4).reshape(gy, gx, -1, 3), axis=2)

mask = np.ones((gy, gx), bool)
mask[int(gy*0.75):, :int(gx*0.22)] = False   # branch, bottom-left

lum = med[..., 1]  # G as luminance proxy
lv = lum[mask]
p5, p50, p95 = np.percentile(lv, [5, 50, 95])
rg = med[..., 0] - med[..., 1]
bg = med[..., 2] - med[..., 1]
worst_rg = np.abs(rg[mask]).max()
worst_bg = np.abs(bg[mask]).max()
ratio = p95 / max(p50, 1)

print(f"{sys.argv[1].split('/')[-1]}")
print(f"  luminance blocks: P5 {p5:.0f}  P50 {p50:.0f}  P95 {p95:.0f}  "
      f"(P95/P50 {ratio:.2f}, limit {LUM_RATIO_MAX})")
print(f"  color: worst |R-G| {worst_rg:.1f}, worst |B-G| {worst_bg:.1f} "
      f"(limit {COLOR_DEV_MAX})")
ok = ratio <= LUM_RATIO_MAX and worst_rg <= COLOR_DEV_MAX and worst_bg <= COLOR_DEV_MAX
# where are the worst offenders?
if not ok:
    yy, xx = np.unravel_index(np.argmax(np.where(mask, lum, 0)), lum.shape)
    print(f"  brightest block at row {yy+1}/{gy}, col {xx+1}/{gx} "
          f"(y~{(yy+0.5)*BLOCK:.0f}px, x~{(xx+0.5)*BLOCK:.0f}px)")
    dev = np.maximum(np.abs(rg), np.abs(bg))
    yy, xx = np.unravel_index(np.argmax(np.where(mask, dev, 0)), dev.shape)
    print(f"  worst color block at row {yy+1}/{gy}, col {xx+1}/{gx}")
print("  PASS" if ok else "  FAIL")
sys.exit(0 if ok else 1)
