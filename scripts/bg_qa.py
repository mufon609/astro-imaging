#!/usr/bin/env python3
"""Whole-frame background QA for a stretched preview JPEG.

Two independent checks, PASS/FAIL per fixed thresholds so a recipe cannot
be graded by hand-picked patches:
- block map: star-robust block medians over the ENTIRE frame (branch corner
  excluded) — luminance uniformity (P95/P50) and color neutrality (worst
  |R-G|, |B-G|);
- radial rings: per-channel radial profiles detrended with a wide moving
  average — the residual peak-to-valley is the concentric-ring amplitude
  the eye picks up even when the block map passes.
"""
import sys
import numpy as np
from PIL import Image

BLOCK = 200
LUM_RATIO_MAX = 1.6     # brightest block / median block luminance
COLOR_DEV_MAX = 7.0     # worst |R-G| or |B-G| among blocks (8-bit counts)
RING_LUM_MAX = 4.0      # detrended radial peak-to-valley, luminance
RING_COLOR_MAX = 4.0    # detrended radial peak-to-valley, R-G / B-G
NB = 40                 # radial bins

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
if not ok:
    yy, xx = np.unravel_index(np.argmax(np.where(mask, lum, 0)), lum.shape)
    print(f"  brightest block at row {yy+1}/{gy}, col {xx+1}/{gx} "
          f"(y~{(yy+0.5)*BLOCK:.0f}px, x~{(xx+0.5)*BLOCK:.0f}px)")
    dev = np.maximum(np.abs(rg), np.abs(bg))
    yy, xx = np.unravel_index(np.argmax(np.where(mask, dev, 0)), dev.shape)
    print(f"  worst color block at row {yy+1}/{gy}, col {xx+1}/{gx}")

# --- radial ring check -------------------------------------------------------
yyc = (np.arange(h) - h / 2)[:, None] / (h / 2)
xxc = (np.arange(w) - w / 2)[None, :] / (w / 2)
r = np.sqrt((yyc**2 + xxc**2) / 2.0)
edges = np.linspace(0, 1, NB + 1)
prof = np.full((NB, 3), np.nan)
for i in range(NB):
    m = (r >= edges[i]) & (r < edges[i + 1])
    if m.sum() > 500:
        prof[i] = [np.median(a[..., c][m]) for c in range(3)]
valid = ~np.isnan(prof[:, 0])
prof = prof[valid]

def ring_amp(v, win=9):
    pad = np.pad(v, win // 2, mode="edge")
    smooth = np.convolve(pad, np.ones(win) / win, mode="valid")
    d = v - smooth
    return d.max() - d.min()

ring_l = ring_amp(prof[:, 1])
ring_rg = ring_amp(prof[:, 0] - prof[:, 1])
ring_bg = ring_amp(prof[:, 2] - prof[:, 1])
print(f"  radial rings: lum P2V {ring_l:.1f} (limit {RING_LUM_MAX}), "
      f"R-G {ring_rg:.1f} / B-G {ring_bg:.1f} (limit {RING_COLOR_MAX})")
ok_r = ring_l <= RING_LUM_MAX and ring_rg <= RING_COLOR_MAX and ring_bg <= RING_COLOR_MAX

print("  PASS" if (ok and ok_r) else "  FAIL")
sys.exit(0 if (ok and ok_r) else 1)
