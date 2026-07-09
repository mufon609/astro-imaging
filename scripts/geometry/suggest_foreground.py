#!/usr/bin/env python3
"""Derive a foreground (non-sky) mask from a linear stack — trees,
horizon objects — for the per-set config (the alternative is a hand-set
rect like set-03's branch).

Usage: suggest_foreground.py <stack.fit> <out.npz>
           [--k=0.4] [--dilate=48] [--overlay=<path.jpg>]

Detection: foreground pixels block the sky, so on the LINEAR stack they
sit far below the sky level (set-03 sky noise is ~40 sigma above 0.4x
median — sky cannot reach the threshold). Candidates = G < k * sky
median, kept only if their connected component touches the bottom/left/
right border (trees grow from edges; a dark nebula or lane never touches
the border at these focal lengths). Morphological close bridges branch
gaps; a generous dilation absorbs the drift-smear halo that star-aligned
stacking paints around foreground silhouettes.

Output npz: mask (bool, display orientation), k, dilate, source stack
name. The mask is a per-session work/ artifact (gitignored, regenerable
by this command — record the command in the dataset's geometry.json).
Point datasets/<session>/<set>/geometry.json at it:
  "foreground": {"mask": "work/fgmask_<set>.npz"}.
Always eyeball the --overlay before trusting it.
"""
import os
import sys

import numpy as np
from scipy import ndimage

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
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    opts = dict(a[2:].split("=", 1) for a in sys.argv[1:]
                if a.startswith("--") and "=" in a)
    if len(args) != 2:
        sys.exit(__doc__)
    stack, out = args
    k = float(opts.get("k", 0.4))
    dil = int(opts.get("dilate", 48))
    data, _ = am.read_fits(stack)
    g = data[min(1, data.shape[0] - 1)]
    h, w = g.shape
    med, sig = am.bg_stats(g)
    thr = k * med
    cand = g < thr
    print(f"[fg] sky median {med * 65535:.0f} (16-bit), sigma "
          f"{sig * 65535:.1f}, threshold {thr * 65535:.0f} "
          f"({(thr - med) / max(sig, 1e-9):.0f} sigma below median), "
          f"raw candidates {cand.mean() * 100:.1f}%")
    # close small gaps so a treeline reads as one component
    cand = ndimage.binary_closing(cand, structure=np.ones((9, 9)))
    labels, n = ndimage.label(cand)
    if n == 0:
        print("[fg] no foreground candidates — writing empty mask")
        mask = np.zeros((h, w), bool)
    else:
        border = np.zeros((h, w), bool)
        # a BAND, not the exact edge rows: binary_closing's erosion step
        # (border_value=0) eats the outermost pixels, so components never
        # touch row h-1 exactly
        border[-16:, :] = True                     # bottom
        border[:, :16] = border[:, -16:] = True    # sides
        border_labels = np.unique(labels[border & cand])
        border_labels = border_labels[border_labels > 0]
        area = ndimage.sum_labels(cand, labels, border_labels)
        keep = border_labels[area > 0.0005 * h * w]  # >0.05% of frame
        mask = np.isin(labels, keep)
        print(f"[fg] components {n}, border-touching kept {len(keep)}")
        if mask.any():
            mask = ndimage.binary_closing(
                mask, structure=np.ones((25, 25)))
            mask = ndimage.binary_dilation(mask, iterations=dil)
    frac = mask.mean()
    ys, xs = np.nonzero(mask) if mask.any() else (np.array([0]), np.array([0]))
    print(f"[fg] final mask: {frac * 100:.1f}% of frame, bbox "
          f"x {xs.min()}-{xs.max()}, y {ys.min()}-{ys.max()}")
    np.savez_compressed(out, mask=mask, k=k, dilate=dil,
                        source=os.path.basename(stack))
    print(f"[fg] wrote {out}")
    if "overlay" in opts:
        from PIL import Image
        u8 = am.autostretch_u8(data)
        edge = ndimage.binary_dilation(mask, iterations=6) & ~mask
        u8[mask] = (0.55 * u8[mask] + np.array([80, 0, 0])).clip(0, 255) \
            .astype(np.uint8)
        u8[edge] = [255, 80, 80]
        Image.fromarray(u8[::4, ::4]).save(opts["overlay"], quality=90)
        print(f"[fg] overlay {opts['overlay']} (red = foreground mask)")


if __name__ == "__main__":
    main()
