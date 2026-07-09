#!/usr/bin/env python3
"""Background QA for a stretched render — THE GATE.

A background DEFECT is a property of the SKY — the dark, empty regions; real
signal (stars, galaxy, Milky Way, nebula) is BRIGHT and must NEVER count as a
defect. So the gate selects the sky STATISTICALLY (no composition mask) and
grades the defects that generalize across any framing:

- color:    worst |R-G| / |B-G| among sky blocks       (color cast / blotch)
- gradient: peak-to-valley of a least-squares PLANE fit to the sky-block
            luminance                                   (vignette / glow gradient)
- resid:    sky-block scatter about that plane          (mid-scale blotches)
- rings:    detrended radial P2V on sky pixels          (concentric vignette rings)

The plane fit is robust to a localized bright object (the object blocks are not
in the sky selection and cannot tilt the plane), so an object-dominated frame
(a galaxy filling the center) is graded on its true sky exactly like an empty
field or a Milky-Way band. Selecting the sky statistically is what makes that
generalize: a bright object has no fixed band and no maskable boundary, so no
geometric per-composition mask could scope it.

The terrestrial FOREGROUND (a treeline: real, but DARK, so the statistical sky
selector would wrongly include it) is excluded via astrometrics.branch_mask,
applied to BOTH the block and the ring scope.

Thresholds never loosen; they are calibrated so the deep/clean references pass
with margin and a real gradient/cast fails. Importable for the inspection and
experiment tooling.
"""
import sys
import numpy as np

BLOCK = 200
SKY_K = 2.5             # sky = blocks with luminance <= P50 + SKY_K*MAD
COLOR_DEV_MAX = 7.0     # worst |R-G| or |B-G| among sky blocks (8-bit counts)
GRAD_MAX = 8.0          # plane-fit P2V over the sky blocks (8-bit counts)
RESID_MAX = 5.0         # sky-block MAD about the plane (8-bit counts)
RING_MAX = 8.0          # detrended radial P2V on sky pixels (8-bit counts)
NB = 40                 # radial bins


def ring_amp(v, win=9):
    """Detrended peak-to-valley of a 1-D profile (moving-average residual)."""
    pad = np.pad(v, win // 2, mode="edge")
    smooth = np.convolve(pad, np.ones(win) / win, mode="valid")
    d = v - smooth
    return float(d.max() - d.min())


def _fg_block_frac(h, w):
    """Per-block foreground fraction (gy, gx) from the resolved CTX, or None
    when no foreground is configured. astrometrics imports bg_qa at module
    load, so import it lazily here."""
    import astrometrics as am
    gy, gx = h // BLOCK, w // BLOCK
    if am.CTX.foreground == "mask":
        fg = am._fg_mask(h, w)[:gy * BLOCK, :gx * BLOCK]
        return fg.reshape(gy, BLOCK, gx, BLOCK).mean(axis=(1, 3))
    if am.CTX.foreground is not None:
        fx0, fy0, fx1, fy1 = am.CTX.foreground
        m = np.zeros((gy, gx), np.float32)
        m[int(gy * fy0):int(gy * fy1), int(gx * fx0):int(gx * fx1)] = 1.0
        return m
    return None


def sky_mask_blocks(a):
    """Block medians + the statistical SKY block mask (not-bright, foreground
    excluded). Returns (med (gy,gx,3), lum (gy,gx), sky bool (gy,gx))."""
    h, w, _ = a.shape
    gy, gx = h // BLOCK, w // BLOCK
    if gy < 1 or gx < 1:
        raise ValueError(
            f"bg_qa: render {w}x{h} is smaller than one {BLOCK}px block — too "
            "small to grade a sky (the gate is calibrated on full-frame renders)")
    blocks = a[:gy * BLOCK, :gx * BLOCK].reshape(gy, BLOCK, gx, BLOCK, 3)
    med = np.median(blocks.transpose(0, 2, 1, 3, 4).reshape(gy, gx, -1, 3),
                    axis=2)
    lum = med[..., 1]                       # G as luminance proxy
    valid = np.ones((gy, gx), bool)
    fg = _fg_block_frac(h, w)
    if fg is not None:
        valid &= fg <= 0.5
    lv = lum[valid]
    p50 = np.median(lv)
    mad = 1.4826 * np.median(np.abs(lv - p50))
    sky = valid & (lum <= p50 + SKY_K * max(mad, 1e-6))
    return med, lum, sky


def _plane_p2v(lum, sky):
    """(gradient P2V, residual MAD) of a least-squares plane fit L ~ ax+by+c
    to the sky blocks, one round of outlier rejection so a faint object wing
    or a stray bright block does not tilt it. P2V is evaluated over the whole
    grid (the worst-corner extent of the fitted background trend)."""
    gy, gx = lum.shape
    ys, xs = np.nonzero(sky)
    if len(ys) < 12:
        return 0.0, 0.0
    A = np.c_[xs, ys, np.ones(len(xs))]
    coef, *_ = np.linalg.lstsq(A, lum[sky], rcond=None)
    resid = lum[sky] - A @ coef
    sig = 1.4826 * np.median(np.abs(resid - np.median(resid)))
    keep = np.abs(resid - np.median(resid)) < 3.0 * (sig + 1e-9)
    if keep.sum() >= 12:
        A2, b2 = A[keep], lum[sky][keep]
        coef, *_ = np.linalg.lstsq(A2, b2, rcond=None)
        resid = b2 - A2 @ coef
        sig = 1.4826 * np.median(np.abs(resid - np.median(resid)))
    YY, XX = np.mgrid[0:gy, 0:gx]
    plane = coef[0] * XX + coef[1] * YY + coef[2]
    return float(plane.max() - plane.min()), float(sig)


def _sky_rings(a, sky_blocks):
    """Detrended radial G-P2V over the SKY pixels only (sky block mask
    upsampled to full res). Object / foreground pixels are excluded so the
    profile measures concentric background rings, not the object."""
    h, w = a.shape[:2]
    sky_pix = np.repeat(np.repeat(sky_blocks, BLOCK, 0), BLOCK, 1)
    if sky_pix.shape[0] < h or sky_pix.shape[1] < w:
        sky_pix = np.pad(sky_pix, ((0, h - sky_pix.shape[0]),
                                   (0, w - sky_pix.shape[1])), mode="edge")
    sky_pix = sky_pix[:h, :w]
    yyc = (np.arange(h) - h / 2)[:, None] / (h / 2)
    xxc = (np.arange(w) - w / 2)[None, :] / (w / 2)
    r = np.sqrt((yyc ** 2 + xxc ** 2) / 2.0)
    edges = np.linspace(0, 1, NB + 1)
    prof = []
    G = a[..., 1]
    for i in range(NB):
        m = (r >= edges[i]) & (r < edges[i + 1]) & sky_pix
        if m.sum() > 500:
            prof.append(np.median(G[m]))
    prof = np.asarray(prof)
    return ring_amp(prof) if len(prof) > 3 else 0.0


def qa_metrics(a):
    """All gate numbers + the verdict for an 8-bit HxWx3 render, without
    printing. Composition-agnostic: sky is selected statistically and the
    terrestrial foreground (CTX) is excluded."""
    a = np.asarray(a, dtype=np.float64)
    med, lum, sky = sky_mask_blocks(a)
    rg = med[..., 0] - med[..., 1]
    bg = med[..., 2] - med[..., 1]
    color = float(max(np.abs(rg[sky]).max(), np.abs(bg[sky]).max())) \
        if sky.any() else 0.0
    grad, resid = _plane_p2v(lum, sky)
    ring_l = _sky_rings(a, sky)
    floor = float(np.median(lum[sky])) if sky.any() else float(np.median(lum))
    ok_color = color <= COLOR_DEV_MAX
    ok_grad = grad <= GRAD_MAX
    ok_resid = resid <= RESID_MAX
    ok_rings = ring_l <= RING_MAX
    # offender block for reporting (brightest sky block)
    yy, xx = np.unravel_index(np.argmax(np.where(sky, lum, -1)), lum.shape)
    return {"color": color, "grad": grad, "resid": resid, "ring_l": ring_l,
            "floor": floor, "skyfrac": float(sky.mean()),
            "ok_color": ok_color, "ok_grad": ok_grad, "ok_resid": ok_resid,
            "ok_rings": ok_rings,
            "pass": bool(ok_color and ok_grad and ok_resid and ok_rings),
            "bright_sky_block": (int(yy), int(xx))}


def main():
    from PIL import Image
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    opts = dict(a[2:].split("=", 1) for a in sys.argv[1:]
                if a.startswith("--") and "=" in a)
    # Foreground geometry (a treeline to exclude from the sky) comes from
    # the dataset's geometry.json via configure(); without --session/--set
    # the context stays foreground-None and the whole frame is eligible sky.
    import astrometrics as am
    am.configure(opts.get("session"), opts.get("set"))
    a = np.asarray(Image.open(args[0]), dtype=np.float64)
    m = qa_metrics(a)
    print(f"{args[0].split('/')[-1]}  [sky scope: {m['skyfrac']*100:.0f}% of "
          "blocks, foreground excluded]")
    print(f"  sky floor G {m['floor']:.0f}  "
          f"| color worst |R-G|/|B-G| {m['color']:.1f} (limit {COLOR_DEV_MAX})"
          f"  {'OK' if m['ok_color'] else 'FAIL'}")
    print(f"  gradient (plane P2V) {m['grad']:.1f} (limit {GRAD_MAX})  "
          f"{'OK' if m['ok_grad'] else 'FAIL'}"
          f"  | blotch resid {m['resid']:.1f} (limit {RESID_MAX})  "
          f"{'OK' if m['ok_resid'] else 'FAIL'}")
    print(f"  radial rings {m['ring_l']:.1f} (limit {RING_MAX})  "
          f"{'OK' if m['ok_rings'] else 'FAIL'}")
    print("  PASS" if m["pass"] else "  FAIL")
    sys.exit(0 if m["pass"] else 1)


if __name__ == "__main__":
    main()
