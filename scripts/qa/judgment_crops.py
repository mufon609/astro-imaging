#!/usr/bin/env python3
"""Assemble the user-judgment package for a set of candidate renders:
fixed 1:1 crops of the known defect zones per candidate, side by side
with the same crop of the reference render.

Usage: judgment_crops.py <outdir> <label=render.jpg> [...]
       [--session=<dir> --set=<name>]

Crop zones come from the per-set config (`judgment_crops`, px boxes —
chosen once per set and kept fixed so runs stay comparable):
  mw_mid    corridor middle w/ dark gaps + stipple
  lefttop   gray-patch zone
  seam      foreground-rectangle corner
  band      corridor edge w/ the strongest chroma bands
Without config crops they are DERIVED per image: corridor centroid
(mw_mid), corridor edge (band), left-top quadrant, foreground corner
(seam, only if a foreground rect exists). Each crop is exported at native
resolution with a fixed mild enhancement (bg-anchored gain 3) so faint
defects are visible identically everywhere.
"""
import os
import sys

import numpy as np
from PIL import Image, ImageDraw

# scripts/lib holds the shared libs (astrometrics, bg_qa); locate it by
# walking up from this file so one bootstrap works at any nesting depth.
_libdir = os.path.dirname(os.path.abspath(__file__))
while _libdir != os.path.dirname(_libdir):
    if os.path.isdir(os.path.join(_libdir, "lib")):
        sys.path.insert(0, os.path.join(_libdir, "lib"))
        break
    _libdir = os.path.dirname(_libdir)
import astrometrics as am  # noqa: E402

GAIN = 3.0


def resolve_crops(h, w):
    """Config crops win; else derive deterministic defect-zone boxes from
    the foreground geometry (an unconfigured context yields just the
    left-top quadrant — no set inherits another's crop boxes)."""
    if am.CTX.judgment_crops:
        return dict(am.CTX.judgment_crops)
    bw, bh = w // 3, h // 3          # crop size ~ a ninth of the frame

    def box_at(cx, cy):
        x0 = int(np.clip(cx - bw / 2, 0, w - bw))
        y0 = int(np.clip(cy - bh / 2, 0, h - bh))
        return (x0, y0, x0 + bw, y0 + bh)

    crops = {"lefttop": (0, int(0.05 * h), bw, int(0.05 * h) + bh)}
    if am.CTX.foreground == "mask":
        fg = am._fg_mask(h, w)
        ys, xs = np.nonzero(fg)
        if len(ys):   # sky-facing top of the foreground silhouette
            crops["seam"] = box_at(float(xs.mean()), float(ys.min()))
    elif am.CTX.foreground is not None:
        fx0, fy0, fx1, fy1 = am.CTX.foreground
        crops["seam"] = box_at(fx1 * w, fy0 * h)  # rect's sky-facing corner
    return crops


def enhance(c, bg):
    return np.clip((c.astype(np.float32) - bg) * GAIN + 24.0, 0, 255) \
        .astype(np.uint8)


def main():
    argv = [a for a in sys.argv[1:] if not a.startswith("--")]
    opts = dict(a[2:].split("=", 1) for a in sys.argv[1:]
                if a.startswith("--") and "=" in a)
    if len(argv) < 2:
        sys.exit(__doc__)
    if "session" in opts and "set" in opts:
        am.configure(opts["session"], opts["set"], quiet=True)
    outdir = argv[0]
    os.makedirs(outdir, exist_ok=True)
    pairs = [a.split("=", 1) for a in argv[1:]]
    imgs = {lab: np.asarray(Image.open(p)) for lab, p in pairs}
    # one shared bg level per crop zone (reference = first candidate) so
    # every candidate gets the identical rendering transform
    ref = next(iter(imgs.values()))
    crops = resolve_crops(ref.shape[0], ref.shape[1])
    for name, (x0, y0, x1, y1) in crops.items():
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
