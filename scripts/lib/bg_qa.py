#!/usr/bin/env python3
"""Background QA for a stretched render — THE GATE.

Two independent checks, PASS/FAIL per fixed thresholds so a recipe cannot
be graded by hand-picked patches:
- block map: star-robust block medians (branch corner excluded) —
  luminance uniformity (P95/P50) and color neutrality (worst |R-G|,
  |B-G|);
- radial rings: per-channel radial profiles detrended with a wide moving
  average — the residual peak-to-valley is the concentric-ring amplitude
  the eye picks up even when the block map passes.

Two SCOPES, same thresholds (thresholds never loosen):
- whole-frame (default): on the separated chain it reads intentional MW
  signal as artifact, so it is REPORTED as reference on recombined images,
  never gated.
- --sky-scope: the gate for the separated chain — run on the STARLESS
  render with the measured MW corridor (+ feather) masked as known signal.
  Corridor-contained costs are covered separately by
  astrometrics.corridor_report (reported, not gated).

Importable (functions below) for the inspection/experiment tooling.
"""
import sys
import numpy as np

BLOCK = 200
LUM_RATIO_MAX = 1.6     # brightest block / median block luminance
COLOR_DEV_MAX = 7.0     # worst |R-G| or |B-G| among blocks (8-bit counts)
RING_LUM_MAX = 4.0      # detrended radial peak-to-valley, luminance
RING_COLOR_MAX = 4.0    # detrended radial peak-to-valley, R-G / B-G
NB = 40                 # radial bins


def block_metrics(a, signal_mask=None):
    """Star-robust block medians over the whole frame, branch corner masked.
    signal_mask (HxW bool, True = known-signal pixels, e.g. the measured MW
    corridor under the layer-appropriate sky scope): blocks that are mostly
    signal leave the statistics exactly like the branch blocks do — scope
    change only, the thresholds are untouched.
    Returns dict with percentiles, worst color deviations and offender
    locations (block row/col, 1-based, and approx pixel coords)."""
    h, w, _ = a.shape
    gy, gx = h // BLOCK, w // BLOCK
    blocks = a[:gy*BLOCK, :gx*BLOCK].reshape(gy, BLOCK, gx, BLOCK, 3)
    med = np.median(blocks.transpose(0, 2, 1, 3, 4).reshape(gy, gx, -1, 3),
                    axis=2)

    mask = np.ones((gy, gx), bool)
    import astrometrics as am  # lazy: astrometrics imports bg_qa at top
    if am.CTX.foreground == "mask":     # block-level foreground fraction
        fg = am._fg_mask(h, w)[:gy*BLOCK, :gx*BLOCK] \
            .reshape(gy, BLOCK, gx, BLOCK).mean(axis=(1, 3))
        mask &= fg <= 0.5
    elif am.CTX.foreground is not None:  # foreground rect (set-03: branch)
        fx0, fy0, fx1, fy1 = am.CTX.foreground
        mask[int(gy * fy0):int(gy * fy1), int(gx * fx0):int(gx * fx1)] = False
    if signal_mask is not None:
        sm = signal_mask[:gy*BLOCK, :gx*BLOCK] \
            .reshape(gy, BLOCK, gx, BLOCK).mean(axis=(1, 3))
        mask &= sm <= 0.5

    lum = med[..., 1]  # G as luminance proxy
    lv = lum[mask]
    p5, p50, p95 = np.percentile(lv, [5, 50, 95])
    rg = med[..., 0] - med[..., 1]
    bg = med[..., 2] - med[..., 1]
    worst_rg = float(np.abs(rg[mask]).max())
    worst_bg = float(np.abs(bg[mask]).max())
    ratio = p95 / max(p50, 1)

    yy, xx = np.unravel_index(np.argmax(np.where(mask, lum, 0)), lum.shape)
    bright = (int(yy), int(xx), gy, gx)
    dev = np.maximum(np.abs(rg), np.abs(bg))
    yy, xx = np.unravel_index(np.argmax(np.where(mask, dev, 0)), dev.shape)
    return {"p5": float(p5), "p50": float(p50), "p95": float(p95),
            "ratio": float(ratio), "worst_rg": worst_rg, "worst_bg": worst_bg,
            "bright_block": bright, "color_block": (int(yy), int(xx))}


def radial_profile_rgb(a, nb=NB, signal_mask=None):
    """Per-channel median radial profile (r=1 at the corners). Returns the
    profile rows that had enough pixels. signal_mask pixels (known signal)
    are excluded from the bin medians."""
    h, w = a.shape[:2]
    yyc = (np.arange(h) - h / 2)[:, None] / (h / 2)
    xxc = (np.arange(w) - w / 2)[None, :] / (w / 2)
    r = np.sqrt((yyc**2 + xxc**2) / 2.0)
    edges = np.linspace(0, 1, nb + 1)
    prof = np.full((nb, 3), np.nan)
    sky = None if signal_mask is None else ~signal_mask
    for i in range(nb):
        m = (r >= edges[i]) & (r < edges[i + 1])
        if sky is not None:
            m &= sky
        if m.sum() > 500:
            prof[i] = [np.median(a[..., c][m]) for c in range(3)]
    return prof[~np.isnan(prof[:, 0])]


def ring_amp(v, win=9):
    pad = np.pad(v, win // 2, mode="edge")
    smooth = np.convolve(pad, np.ones(win) / win, mode="valid")
    d = v - smooth
    return float(d.max() - d.min())


def ring_metrics(a, signal_mask=None):
    prof = radial_profile_rgb(a, signal_mask=signal_mask)
    return {"ring_l": ring_amp(prof[:, 1]),
            "ring_rg": ring_amp(prof[:, 0] - prof[:, 1]),
            "ring_bg": ring_amp(prof[:, 2] - prof[:, 1])}


def sky_signal_mask(h, w):
    """The layer-appropriate sky scope's signal mask: the measured MW band
    corridor incl. the mw_boost feather zone — every pixel an intentional MW
    lift can touch. True = signal, excluded from background statistics. The
    branch corner is excluded separately by block_metrics."""
    import astrometrics as am
    return am.band_mask_frac(h, w, feather=0.10) > 0.01


def qa_metrics(a, signal_mask=None):
    """All QA numbers + the verdict, without printing.
    signal_mask=None: the historical whole-frame scope (byte-identical).
    signal_mask=<HxW bool>: layer-appropriate sky scope — known-signal
    pixels leave the background statistics; thresholds identical."""
    bm = block_metrics(a, signal_mask)
    rm = ring_metrics(a, signal_mask)
    ok_b = (bm["ratio"] <= LUM_RATIO_MAX and bm["worst_rg"] <= COLOR_DEV_MAX
            and bm["worst_bg"] <= COLOR_DEV_MAX)
    ok_r = (rm["ring_l"] <= RING_LUM_MAX and rm["ring_rg"] <= RING_COLOR_MAX
            and rm["ring_bg"] <= RING_COLOR_MAX)
    return {**bm, **rm, "ok_blocks": ok_b, "ok_rings": ok_r,
            "pass": ok_b and ok_r,
            "scope": "whole-frame" if signal_mask is None else "sky"}


def main():
    from PIL import Image
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    sky = "--sky-scope" in sys.argv[1:]
    opts = dict(a[2:].split("=", 1) for a in sys.argv[1:]
                if a.startswith("--") and "=" in a)
    # per-set geometry (corridor + foreground): config_<set>.json, else
    # WCS-derived, else none (whole-frame QA, warned). Without
    # --session/--set the context stays unconfigured = none, never set-03.
    import astrometrics as am
    am.configure(opts.get("session"), opts.get("set"), stack=opts.get("stack"))
    a = np.asarray(Image.open(args[0]), dtype=np.float64)
    sm = sky_signal_mask(a.shape[0], a.shape[1]) if sky else None
    m = qa_metrics(a, sm)

    print(f"{args[0].split('/')[-1]}"
          + ("  [sky scope: MW corridor + branch masked]" if sky else ""))
    print(f"  luminance blocks: P5 {m['p5']:.0f}  P50 {m['p50']:.0f}  "
          f"P95 {m['p95']:.0f}  (P95/P50 {m['ratio']:.2f}, limit {LUM_RATIO_MAX})")
    print(f"  color: worst |R-G| {m['worst_rg']:.1f}, worst |B-G| {m['worst_bg']:.1f} "
          f"(limit {COLOR_DEV_MAX})")
    if not m["ok_blocks"]:
        yy, xx, gy, gx = m["bright_block"]
        print(f"  brightest block at row {yy+1}/{gy}, col {xx+1}/{gx} "
              f"(y~{(yy+0.5)*BLOCK:.0f}px, x~{(xx+0.5)*BLOCK:.0f}px)")
        yy, xx = m["color_block"]
        print(f"  worst color block at row {yy+1}/{gy}, col {xx+1}/{gx}")
    print(f"  radial rings: lum P2V {m['ring_l']:.1f} (limit {RING_LUM_MAX}), "
          f"R-G {m['ring_rg']:.1f} / B-G {m['ring_bg']:.1f} (limit {RING_COLOR_MAX})")
    print("  PASS" if m["pass"] else "  FAIL")
    sys.exit(0 if m["pass"] else 1)


if __name__ == "__main__":
    main()
