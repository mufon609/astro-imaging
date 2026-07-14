#!/usr/bin/env python3
"""Object-integrity audit — grades the OBJECT region the gate is blind to.

The gate (bg_qa) grades the SKY by design; nothing grades the object, so a
crushed nebula / hollow shell / mottled dust / neutralized colour passes
every standing check (the measured escapes: a vst chroma-crush, coring
mottle, a linked-stretch drowned line, and a hollow sphere all shipped
gate-PASSing). This is the standing WARN-level object audit (BACKLOG C18).

It compares the render's OBJECT region to the CALIBRATED LINEAR STACK the
render was made from — a plain matched autostretch = what the object should
look like with NO corings / denoise / crush — in BOTH directions:

- RETENTION (chain-REMOVED signal, one-sided): object STRUCTURE contrast and
  above-sky CHROMA energy, render vs the linear reference, each normalized so
  the comparison survives the two different stretches. render << linear WARNs
  (the chain crushed structure / neutralized colour).
- INTRODUCTION (chain-ADDED texture): mid-scale (coring-pyramid-scale)
  patchiness in the render's object that the linear reference does NOT carry
  WARNs (coring mottle, seams).

SCOPE (important): grade a render against its OWN calibrated linear input —
the SAME colour balance, co-registered (a starcomb render vs its SPCC stack).
The chroma measure is fair only at the same balance; the render is registered
to the reference first (a small offset is corrected, a large one means the
wrong reference was passed).

HONEST reliability (measured against synthetic + real defects; WARN-only):
- TEXTURE (mottle) — RELIABLE: the old coring chain reads 5.4x vs ~1.1x clean.
- CHROMA (absolute object colour vs the same-balance input) — RELIABLE:
  catches neutralization (old chain 0.40; a 90%-desaturated object 0.05).
- STRUCTURE (grain-robust worst-region correlation) — catches GROSS object
  flattening (a hard wide blur 0.65) without false-flagging a good render
  (0.90), but does NOT reliably resolve a SMALL LOCAL hollow (a hollowed
  shell ~2% of the object reads ~0.87) — it is washed out by the surrounding
  object. A small local structure defect (e.g. the Bubble's hollow sphere)
  is better caught upstream: that specific case was a channel MISALIGNMENT,
  flagged by nightlight_sho's alignment check, not by this render audit.

Usage:
  object_integrity.py <render.png|jpg> <linear_stack.fit>
      [--session <dir> --set <name>]   # foreground excluded if configured

Object region = extended_object_mask on the linear luminance (the smoothed
above-sky nebula; point stars fall out), terrestrial foreground excluded.
"""
import argparse
import os
import sys

import numpy as np
from scipy.ndimage import gaussian_filter

_libdir = os.path.dirname(os.path.abspath(__file__))
while _libdir != os.path.dirname(_libdir):
    if os.path.isdir(os.path.join(_libdir, "lib")):
        sys.path.insert(0, os.path.join(_libdir, "lib"))
        break
    _libdir = os.path.dirname(_libdir)
import astrometrics as am  # noqa: E402

# WARN bounds (calibrate as a class history accrues; WARN-only, never gates):
STRUCT_WARN = 0.70     # worst-region structure correlation below (gross
#                        flattening; a SMALL local hollow is not resolved —
#                        see the honest limitation in the module docstring)
CHROMA_WARN = 0.60     # object chroma retained below this fraction of linear
TEXTURE_WARN = 1.60    # render object mid-scale texture > 1.6x the linear ref
WORK = 1600            # downsample longest side to this for the measures
REG_MAX = 12           # cap the render->reference registration search (px)


def _lum(rgb):
    return rgb[min(1, rgb.shape[0] - 1)]


def _norm01(a):
    return np.clip(a, 0.0, 1.0)


def _band(a, lo=3.0, hi=24.0):
    """Object-scale band-pass (px at the audit's downsampled working scale):
    keeps coherent structure (filaments, the shell edge), drops fine grain and
    the smooth background."""
    return gaussian_filter(a, lo) - gaussian_filter(a, hi)


def _corr(a, b):
    """Normalized cross-correlation of two flat arrays — amplitude-invariant
    (a scale on either side cancels), so it measures WHETHER the pattern is
    shared, not how bright/saturated it is."""
    a, b = a - a.mean(), b - b.mean()
    denom = float(np.sqrt(float((a * a).sum()) * float((b * b).sum())))
    return float((a * b).sum() / max(denom, 1e-12))


def _register(a_band, b_band, mask):
    """Integer (dy,dx) that best aligns a to b over the object (FFT cross-
    correlation of the masked band-passed luminance). A render and its linear
    reference can sit on different alignment frames (a different reference
    member), and a global offset must NOT read as lost structure, so register
    first then correlate. The object is interior, so the wrap is harmless."""
    from numpy.fft import fft2, ifft2
    a = np.where(mask, a_band, 0.0)
    b = np.where(mask, b_band, 0.0)
    cc = np.abs(ifft2(fft2(a) * np.conj(fft2(b))))
    hh, ww = mask.shape
    # search only SMALL shifts: a render vs its own input is near-registered,
    # so a large 'best' shift means the wrong reference was passed (a different
    # alignment frame), not sub-object drift — do not chase it
    r = REG_MAX
    win = np.full_like(cc, -1.0)
    for sy in (slice(0, r + 1), slice(hh - r, hh)):
        for sx in (slice(0, r + 1), slice(ww - r, ww)):
            win[sy, sx] = cc[sy, sx]
    dy, dx = np.unravel_index(int(np.argmax(win)), win.shape)
    return (int(dy - hh) if dy > hh // 2 else int(dy),
            int(dx - ww) if dx > ww // 2 else int(dx))


def _struct_local(r_band, l_band, mask, block=96):
    """LOCALIZED structure retention: per-block band-correlation, reported as
    the low percentile (WORST region). A hollow shell / crushed knot is a
    small sub-region — a whole-object average washes it out (measured: a hard
    blur barely moved it), but its own block decorrelates. Blocks that are
    mostly object are scored; the 10th-percentile block is the retention."""
    hh, ww = mask.shape
    vals = []
    for y in range(0, hh, block):
        for x in range(0, ww, block):
            m = mask[y:y + block, x:x + block]
            if m.sum() < 0.3 * m.size:
                continue
            vals.append(_corr(r_band[y:y + block, x:x + block][m],
                              l_band[y:y + block, x:x + block][m]))
    return float(np.percentile(vals, 10)) if vals else 1.0


def _texture(lum, mask):
    """Mid-scale patchiness (the coring pyramid band at the working scale),
    normalized — the mottle/seam signature the corings introduce."""
    band = gaussian_filter(lum, 6.0) - gaussian_filter(lum, 24.0)
    m = float(lum[mask].mean())
    return float(band[mask].std() / max(m, 1e-6))


def audit(render_rgb, linear_rgb, obj_mask):
    """render_rgb, linear_rgb: (3,H,W) display-referred [0,1] at the audit
    working scale. Returns the refined measures + one-sided flags."""
    rl, ll = _lum(render_rgb), _lum(linear_rgb)
    ll_band = _band(ll)
    # register the render to the linear over the object, then correlate, so a
    # global alignment-frame difference between them is not read as lost
    # structure (only a change in WHERE structure/colour is counts)
    dy, dx = _register(_band(rl), ll_band, obj_mask)
    rshift = np.stack([np.roll(render_rgb[c], (dy, dx), axis=(0, 1))
                       for c in range(3)])
    struct_ret = _struct_local(_band(_lum(rshift)), ll_band, obj_mask)
    # chroma: ABSOLUTE object chroma vs the co-registered, SAME-BALANCE linear
    # input (a starcomb render vs its own SPCC stack). Absolute — not a
    # pattern correlation — because a uniform DESATURATION toward gray (the
    # neutralization escape) leaves the pattern intact but drops the amount;
    # fair against false balance flags only because it is the render's OWN
    # input balance (see the scope note in main()).
    Lr, Cr, _ = am.rgb_to_lch(_norm01(rshift))
    Ll, Cl, _ = am.rgb_to_lch(_norm01(linear_rgb))
    chroma_r = float(Cr[obj_mask].mean() / max(Lr[obj_mask].mean(), 1e-6))
    chroma_l = float(Cl[obj_mask].mean() / max(Ll[obj_mask].mean(), 1e-6))
    chroma_ret = chroma_r / max(chroma_l, 1e-9)
    texture_exc = _texture(rl, obj_mask) / max(_texture(ll, obj_mask), 1e-9)
    flags = []
    if struct_ret < STRUCT_WARN:
        flags.append(f"structure NOT retained (corr {struct_ret:.2f} < "
                     f"{STRUCT_WARN}) — object crushed/flattened/HOLLOW or "
                     "replaced by uncorrelated mottle")
    if chroma_ret < CHROMA_WARN:
        flags.append(f"chroma neutralized (retained {chroma_ret:.2f} < "
                     f"{CHROMA_WARN}) — object colour pushed toward gray")
    if texture_exc > TEXTURE_WARN:
        flags.append(f"texture added ({texture_exc:.2f}x > {TEXTURE_WARN}) — "
                     "mid-scale mottle/seams the linear ref does not carry")
    return {"struct_retained": struct_ret, "chroma_retained": chroma_ret,
            "texture_excess": texture_exc, "obj_frac": float(obj_mask.mean()),
            "reg_shift": (dy, dx), "flags": flags}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("render")
    ap.add_argument("stack")
    ap.add_argument("--session", default=None)
    ap.add_argument("--set", default=None)
    args = ap.parse_args()
    if args.session and args.set:
        am.configure(args.session, args.set, quiet=True)

    from PIL import Image
    Image.MAX_IMAGE_PIXELS = None

    def _rs(rgb, nw, nh):
        return np.stack([
            np.asarray(Image.fromarray((np.clip(rgb[c], 0, 1) * 255)
                       .astype(np.uint8)).resize((nw, nh))) / 255.0
            for c in range(3)]).astype(np.float32)

    render_full = (np.asarray(Image.open(args.render).convert("RGB"))
                   .transpose(2, 0, 1) / 255.0).astype(np.float32)
    # the linear reference: the calibrated stack under the SAME consistent
    # inspection autostretch (plain, no corings/denoise) — what the object
    # SHOULD look like
    lin = am.load_linear(args.stack)
    if lin.shape[0] == 1:
        lin = np.repeat(lin, 3, axis=0)
    linref_full = (am.autostretch_u8(lin).transpose(2, 0, 1) / 255.0
                   ).astype(np.float32)
    # downsample BOTH to a common working grid — the object structure lives
    # well above the pixel scale, so the band-scale measures are unchanged and
    # the full-frame gaussians run 10-30x faster
    h, w = render_full.shape[1:]
    s = min(1.0, WORK / float(max(h, w)))
    nw, nh = int(round(w * s)), int(round(h * s))
    render, linref = _rs(render_full, nw, nh), _rs(linref_full, nw, nh)

    lum = _lum(linref)
    fg = am.branch_mask(lum.shape[0], lum.shape[1])  # foreground excluded
    obj = am.extended_object_mask(lum) & fg          # the bright nebula
    if obj.sum() < 300:
        print("[object-integrity] object region too small to grade "
              f"({int(obj.sum())} px at work scale) — no bright extended "
              "object here; SKIP (grades a resolved object, not a star field)")
        return

    r = audit(render, linref, obj)
    print(f"[object-integrity] {os.path.basename(args.render)} vs "
          f"{os.path.basename(args.stack)} (object {r['obj_frac']*100:.1f}% "
          f"of frame; render registered to ref by {r['reg_shift']} px)")
    print(f"  STRUCTURE retained corr {r['struct_retained']:.2f} "
          "(1.0=real structure kept in place; grain-robust)")
    print(f"  CHROMA    retained {r['chroma_retained']:.2f} "
          "(1.0=object colour kept vs its own-balance input)")
    print(f"  TEXTURE   excess   {r['texture_excess']:.2f}x (mid-scale mottle)")
    if r["flags"]:
        for f in r["flags"]:
            print(f"  WARN: {f}")
    else:
        print("  OK — object structure, chroma and texture within bounds")
    return r


if __name__ == "__main__":
    main()
