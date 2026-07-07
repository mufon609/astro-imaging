#!/usr/bin/env python3
"""Assemble the user-judgment package for a set of candidate renders:
fixed 1:1 crops of the known defect zones (the four session-5 issues) per
candidate, side by side with the same crop of the reference render.

Usage: judgment_crops.py <outdir> <label=render.jpg> [label2=render2.jpg ...]

Crops are chosen once (session 5) and stay fixed so runs stay comparable:
  mw_mid    corridor middle w/ dark gaps + stipple (issues 3+4)
  lefttop   gray-patch zone (issue 2)
  seam      branch-rectangle corner (M0 seam)
  band      corridor edge w/ the strongest chroma bands (issue 1)
Each crop is exported at native resolution with a fixed mild enhancement
(bg-anchored gain 3) so faint defects are visible identically everywhere.
"""
import os
import sys

import numpy as np
from PIL import Image, ImageDraw

CROPS = {
    "mw_mid": (2500, 1300, 4500, 2700),
    "lefttop": (0, 200, 2000, 1600),
    "seam": (600, 2500, 2600, 3900),
    "band": (3600, 300, 5600, 1700),
}
GAIN = 3.0


def enhance(c, bg):
    return np.clip((c.astype(np.float32) - bg) * GAIN + 24.0, 0, 255) \
        .astype(np.uint8)


def main():
    if len(sys.argv) < 3:
        sys.exit(__doc__)
    outdir = sys.argv[1]
    os.makedirs(outdir, exist_ok=True)
    pairs = [a.split("=", 1) for a in sys.argv[2:]]
    imgs = {lab: np.asarray(Image.open(p)) for lab, p in pairs}
    # one shared bg level per crop zone (reference = first candidate) so
    # every candidate gets the identical rendering transform
    ref = next(iter(imgs.values()))
    for name, (x0, y0, x1, y1) in CROPS.items():
        bg = float(np.median(ref[y0:y1, x0:x1, 1]))
        tiles, labels = [], []
        for lab, im in imgs.items():
            tiles.append(enhance(im[y0:y1, x0:x1], bg))
            labels.append(lab)
        hgt = max(t.shape[0] for t in tiles) + 28
        wid = sum(t.shape[1] for t in tiles) + 8 * (len(tiles) - 1)
        canvas = np.zeros((hgt, wid, 3), np.uint8)
        x = 0
        for t in tiles:
            canvas[28:28 + t.shape[0], x:x + t.shape[1]] = t
            x += t.shape[1] + 8
        img = Image.fromarray(canvas)
        d = ImageDraw.Draw(img)
        x = 0
        for t, lab in zip(tiles, labels):
            d.text((x + 6, 6), lab, fill=(255, 255, 0))
            x += t.shape[1] + 8
        img.save(os.path.join(outdir, f"judge_{name}.jpg"), quality=90)
        print(f"judge_{name}.jpg  ({', '.join(labels)}, gain {GAIN}, bg {bg:.0f})")


if __name__ == "__main__":
    main()
