#!/usr/bin/env python3
"""Stack-vs-stack comparators for a with/without ladder (the stack-policy
adoption instrument: README's trigger doctrine wants a measured
with-vs-without before any weight/cull pins).

Both stacks must be registered to the SAME reference (true for
partitioned_stack.py variants and for rebuilt monolithic stacks with a
pinned reference): then A-B isolates exactly what the policy change did,
and structure in the difference is the contamination one variant admitted
(or the signal it lost).

Per stack (G channel, or the single channel on mono): statistical-sky
median + MAD (the stack noise number), 32-px block-median MAD over the sky
(blotch-class proxy), sky-block p2v, star count. For the pair: sky MAD of
the difference, the largest |block-median| of the difference (structure),
and a stretched difference JPEG for eyes.

All counts in 16-bit ADU of the loaded scale. WARN-only, prints numbers.

Usage: stack_ab.py <A.fit> <B.fit> [--label-a e0 --label-b e1]
       [--diff-jpg out.jpg] [--session <dir> --set <name>]
"""
import argparse
import os
import sys

import numpy as np

# scripts/lib holds the shared libs (astrometrics, bg_qa); locate it by
# walking up from this file so one bootstrap works at any nesting depth.
_libdir = os.path.dirname(os.path.abspath(__file__))
while _libdir != os.path.dirname(_libdir):
    if os.path.isdir(os.path.join(_libdir, "lib")):
        sys.path.insert(0, os.path.join(_libdir, "lib"))
        break
    _libdir = os.path.dirname(_libdir)
import astrometrics as am  # noqa: E402


def gchan(path):
    # read_fits returns planes-first (C,H,W)
    d, _ = am.read_fits(path)
    return d[1] if d.ndim == 3 else d


def block_medians(ch, mask, block=32):
    h, w = ch.shape
    bh, bw = h // block, w // block
    vals = []
    for by in range(bh):
        for bx in range(bw):
            m = mask[by * block:(by + 1) * block,
                     bx * block:(bx + 1) * block]
            if m.mean() > 0.7:
                vals.append(float(np.median(
                    ch[by * block:(by + 1) * block,
                       bx * block:(bx + 1) * block][m])))
    return np.asarray(vals)


def stack_numbers(path):
    ch = gchan(path)
    mask = am.sky_pixel_mask(ch)
    sky = ch[mask]
    med = float(np.median(sky))
    mad = float(np.median(np.abs(sky - med)))
    bm = block_medians(ch, mask)
    bmad = float(np.median(np.abs(bm - np.median(bm)))) if bm.size else 0.0
    p2v = float(bm.max() - bm.min()) if bm.size else 0.0
    stars = am.star_metrics(ch)
    n_stars = stars.get("n_stars", stars.get("count", -1)) \
        if isinstance(stars, dict) else -1
    return {"sky_med": med * 65535, "sky_mad": mad * 65535,
            "block_mad": bmad * 65535, "sky_p2v": p2v * 65535,
            "n_stars": n_stars, "ch": ch, "mask": mask}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("a")
    ap.add_argument("b")
    ap.add_argument("--label-a", default="A")
    ap.add_argument("--label-b", default="B")
    ap.add_argument("--diff-jpg", default=None)
    ap.add_argument("--session", default=None)
    ap.add_argument("--set", dest="set_name", default=None)
    args = ap.parse_args()
    if args.session and args.set_name:
        am.configure(args.session, args.set_name, quiet=True)

    A = stack_numbers(args.a)
    B = stack_numbers(args.b)
    print(f"{'':12s} {args.label_a:>12s} {args.label_b:>12s} "
          f"{'delta B-A':>12s}")
    for k in ("sky_med", "sky_mad", "block_mad", "sky_p2v"):
        print(f"{k:12s} {A[k]:12.3f} {B[k]:12.3f} {B[k] - A[k]:+12.3f}"
              + ("   ({:+.1f}%)".format(100 * (B[k] / A[k] - 1))
                 if A[k] else ""))
    print(f"{'n_stars':12s} {A['n_stars']:12} {B['n_stars']:12}")

    if A["ch"].shape != B["ch"].shape:
        print(f"shape mismatch {A['ch'].shape} vs {B['ch'].shape} — "
              f"no difference analysis")
        return
    diff = B["ch"] - A["ch"]
    mask = A["mask"] & B["mask"]
    dmad = float(np.median(np.abs(diff[mask] - np.median(diff[mask]))))
    bm = block_medians(diff - np.median(diff[mask]), mask)
    bmax = float(np.max(np.abs(bm))) if bm.size else 0.0
    print(f"\ndifference ({args.label_b} - {args.label_a}), sky scope:")
    print(f"  sky MAD        {dmad * 65535:9.3f} c16 (pixel-level noise "
          f"delta the exclusion causes)")
    print(f"  max |block med| {bmax * 65535:8.3f} c16 (STRUCTURE: cloud "
          f"residue one variant carries)")
    if args.diff_jpg:
        from PIL import Image
        d = diff - np.median(diff[mask])
        scale = max(5 * dmad, 1e-6)
        img = np.clip(d / (2 * scale) + 0.5, 0, 1)
        Image.fromarray((img * 255).astype(np.uint8)).resize(
            (img.shape[1] // 4, img.shape[0] // 4)).save(
            args.diff_jpg, quality=90)
        print(f"  stretched diff (±{2 * scale * 65535:.1f} c16 full range)"
              f" -> {args.diff_jpg}")


if __name__ == "__main__":
    main()
