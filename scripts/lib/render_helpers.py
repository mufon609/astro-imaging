"""Shared helpers for starcomb's comparison-ladder (--param mode): the GraXpert
runner and rendered-JPEG measurement. Imported, not run standalone
(astrometrics/bg_qa resolve as lib siblings)."""
import os
import subprocess
import sys

import numpy as np

import astrometrics as am
import bg_qa

GRAXPERT = os.path.expanduser("~/.local/bin/graxpert")


def run_graxpert(stack_fit, work, log):
    """GraXpert AI background extraction on the pinned stack, cached by
    input identity (mtime+size) so ladders reuse it."""
    st = os.stat(stack_fit)
    key = f"gx_{st.st_size}_{int(st.st_mtime)}"
    out = os.path.join(work, f"{key}.fits")
    if os.path.exists(out):
        log(f"graxpert: cache hit {os.path.basename(out)}")
        return out
    log("graxpert: running background-extraction (first run downloads the "
        "AI model; takes minutes on this box)")
    r = subprocess.run([GRAXPERT, "-cmd", "background-extraction",
                        stack_fit, "-output", out[:-5], "-gpu", "false"],
                       capture_output=True, text=True)
    if not os.path.exists(out):
        sys.exit("graxpert: produced no output:\n"
                 + r.stdout[-3000:] + "\n" + r.stderr[-2000:])
    return out


def run_rbf_constrained(stack_fit, work, log, protect="significance"):
    """Constrained background extraction (bgelin_mode `rbf`), in-house:
    the mode for fields carrying BOTH a real (coloured / higher-order)
    gradient AND faint object signal a full extraction would absorb.

    CHROMA-RIGID by construction: ONE gray thin-plate RBF surface fitted
    through off-structure sample luminances, plus a first-degree PLANE
    per channel for the coloured part of the background (the coloured
    part of light pollution is smooth; independently-fit per-channel
    surfaces ripple chroma at block scale — measured gate colour 31
    with neutral global sky medians, the "per-channel V must be GRAY"
    self-flat lesson recurring at the extraction stage).

    Samples may sit only where a SIGNIFICANCE mask at the smoothing
    scale sees no structure: star-suppressed (median-15) G smoothed at
    sigma 32 px, thresholded at 3x the smoothed noise floor (the pixel
    noise attenuated analytically by the kernel — a spatial-MAD
    threshold is gradient-inflated and measured blind to a 3-10 sigma
    envelope). The protection REFERENCE is per-dataset state (knob
    `rbf_protect`), because single-image statistics cannot tell
    frame-filling faint nebulosity from instrumental envelope:

    - `significance` — above the global statistical sky. Protects
      everything significant INCLUDING a frame-filling faint envelope
      (that envelope is the target on its motivating class); the
      surface rests on true dark-sky cells only.
    - `band` — bandpass significance (present at the smoothing scale,
      absent at the 202 px protection ceiling — a class constant ~1.35x
      the 150 px top of the protected structure class, deliberately NOT
      derived from the sample spacing: resolution and protection are
      different quantities). Protects compact/mid-scale faint structure
      while frame-scale elevation is absorbed as background — ONLY
      for fields whose frame-scale envelope is measured CALIBRATION
      DEBT (unusable flats: vignette residual, glow), never celestial
      signal.

    One sample per eligible grid cell at the darkest smoothed point,
    valued by a 25 px per-channel local median; per-channel scalar
    re-pedestal after subtraction (a scalar cannot create spatial
    chroma). Deterministic (fixed grid, closed-form fits). Refuses
    loudly when fewer than 20 cells offer sky samples."""
    from scipy.interpolate import RBFInterpolator
    from scipy.ndimage import gaussian_filter, maximum_filter, \
        median_filter, minimum_filter, zoom

    st = os.stat(stack_fit)
    key = f"rbf2_{protect}_{st.st_size}_{int(st.st_mtime)}"
    out = os.path.join(work, f"{key}.fits")
    if os.path.exists(out):
        log(f"rbf-constrained: cache hit {os.path.basename(out)}")
        return out

    SIG_S = 32.0        # smoothing scale: below the ~50 px floor of the
    K_SIG = 3.0         # protected structure class, so the class
    DILATE = 64         # survives the smoothing; threshold + margin
    NY, NX = 20, 30     # sample grid: ~160 px spacing resolves the sky
    #                     structure between the protection ceiling and
    #                     the grid Nyquist (a 15x10 grid left a 200-600
    #                     px aliasing zone that rendered as rings 11.4)
    SAMPLE_R = 12       # 25 px value window
    MIN_CELLS = 20
    SIG_BASE = 202.0    # band-protect ceiling: a CLASS constant (~1.35x
    #                     the 150 px top of the protected structure
    #                     class), deliberately NOT derived from the
    #                     sample spacing — resolution and protection
    #                     are different quantities
    SMOOTHING = 1e-3    # noise-matched regularizer: sample-residual RMS
    #                     0.086 c16 ~ the 25 px median-window noise on
    #                     the calibration dataset; guards degenerate
    #                     sample geometry, does not shape the surface

    cards, planes, _ = am.read_fits_planes(stack_fit)
    nc, h, w = planes.shape
    G = planes[min(1, nc - 1)]
    # star suppression BEFORE smoothing: the mask must see 50+ px faint
    # structure, not the star field (15 px median kills <=10 px stars)
    Gm = median_filter(G, size=15)
    sm = gaussian_filter(Gm, SIG_S)
    _, sig_px = am.bg_stats(G)
    # noise floor of the smoothed map: white pixel noise through a
    # normalized gaussian kernel (2-D: variance falls by 1/(4*pi*s^2))
    sig_sm = sig_px / (2.0 * np.sqrt(np.pi) * SIG_S)
    if protect == "band":
        base_sm = gaussian_filter(Gm, SIG_BASE)
        var = (1.0 / SIG_S ** 2 + 1.0 / SIG_BASE ** 2) / (4.0 * np.pi) \
            - 1.0 / (np.pi * (SIG_S ** 2 + SIG_BASE ** 2))
        sig_band = sig_px * float(np.sqrt(max(var, 1e-30)))
        mask = (sm - base_sm) > K_SIG * sig_band
        del base_sm
        ref_note = (f"band s{SIG_S:g}->s{SIG_BASE:g}, "
                    f"sig_band {sig_band * 65535:.3f} c16")
    elif protect == "significance":
        # global statistical sky of the smoothed map, settled with the
        # detected structure excluded (the structure inflates the very
        # median used to find it)
        elig = am.branch_mask(h, w)
        obj = np.zeros((h, w), bool)
        for _ in range(4):
            sky = float(np.median(sm[elig & ~obj]))
            new = sm > sky + K_SIG * sig_sm
            if new.sum() == obj.sum():
                break
            obj = new
        mask = obj
        ref_note = (f"significance sky {sky * 65535:.1f} c16, "
                    f"sig_sm {sig_sm * 65535:.3f} c16")
    else:
        sys.exit(f"rbf-constrained: unknown protect reference "
                 f"{protect!r} (significance|band)")
    mask |= ~am.branch_mask(h, w)        # terrestrial foreground: never
    mask = maximum_filter(mask, size=2 * DILATE + 1)   # sampled; margin
    frac = float(mask.mean())
    # cell eligibility is CLEAN-CORE, not masked-fraction: on a
    # texture-dense field most cells are majority-masked yet still hold
    # real sky patches the mask itself located (a >50%-masked skip rule
    # measured 37/150 cells with whole frame bands empty -> the
    # under-constrained surface left a 10.7 plane-fit gradient). A cell
    # samples wherever a fully-unmasked value window survives erosion —
    # masked pixels are still never sampled, and the sample window is
    # now guaranteed clean by construction.
    clean_core = minimum_filter(~mask, size=2 * SAMPLE_R + 1)

    pts, vals = [], []
    for iy in range(NY):
        for ix in range(NX):
            y0, y1 = h * iy // NY, h * (iy + 1) // NY
            x0, x1 = w * ix // NX, w * (ix + 1) // NX
            cc = clean_core[y0:y1, x0:x1]
            if not cc.any():             # no clean window in this cell
                continue
            cell = np.where(cc, sm[y0:y1, x0:x1], np.inf)
            ry, rx = divmod(int(np.argmin(cell)), cell.shape[1])
            py, px = y0 + ry, x0 + rx
            wy0, wy1 = max(0, py - SAMPLE_R), min(h, py + SAMPLE_R + 1)
            wx0, wx1 = max(0, px - SAMPLE_R), min(w, px + SAMPLE_R + 1)
            pts.append((py, px))
            vals.append([float(np.median(planes[c, wy0:wy1, wx0:wx1]))
                         for c in range(nc)])
    if len(pts) < MIN_CELLS:
        sys.exit(f"rbf-constrained: only {len(pts)} off-structure sample "
                 f"cells on {stack_fit} — the field is too object-filled "
                 "to constrain a background fit; use bgelin_mode plane "
                 "or gx deliberately instead")
    log(f"rbf-constrained: {ref_note}; mask {100 * frac:.1f}% of frame, "
        f"{len(pts)}/{NX * NY} sample cells (sig_px "
        f"{sig_px * 65535:.2f} c16)")

    P = np.array([[(px + 0.5) / w, (py + 0.5) / h] for py, px in pts])
    V = np.array(vals, np.float64)
    gray = V.mean(axis=1)
    rbf = RBFInterpolator(P, gray, kernel="thin_plate_spline",
                          smoothing=SMOOTHING)
    # evaluate on a stride-8 grid, bilinear to full res: the surface
    # carries no structure below the ~300 px sample spacing, so the
    # 8 px resample is exact at background scales and 64x cheaper
    gh, gw = (h + 7) // 8, (w + 7) // 8
    yy = ((np.arange(gh) * 8 + 3.5) / h)
    xx = ((np.arange(gw) * 8 + 3.5) / w)
    YY, XX = np.meshgrid(yy, xx, indexing="ij")
    surf = rbf(np.stack([XX.ravel(), YY.ravel()], 1)).reshape(gh, gw)
    gray_bg = zoom(surf, 8, order=1, grid_mode=True,
                   mode="nearest")[:h, :w].astype(np.float32)

    Xn = ((np.arange(w) + 0.5) / w).astype(np.float32)[None, :]
    Yn = ((np.arange(h) + 0.5) / h).astype(np.float32)[:, None]
    # chroma correction is QUADRATIC per channel: low-order by design —
    # six coefficients over the frame cannot ripple at block scale (the
    # per-channel-surface failure) — but able to follow a real coloured
    # gradient beyond first degree (first-degree measured colour 9 vs
    # the gate's 7 on a field whose coloured LP curves; quadratic cut
    # the linear chroma residual 2.5x)
    A = np.column_stack([P[:, 0], P[:, 1], np.ones(len(P)),
                         P[:, 0] ** 2, P[:, 1] ** 2, P[:, 0] * P[:, 1]])
    outp = np.empty_like(planes)
    for c in range(nc):
        if nc > 1:
            coef, *_ = np.linalg.lstsq(A, V[:, c] - gray, rcond=None)
            bg = gray_bg + (coef[0] * Xn + coef[1] * Yn + coef[2]
                            + coef[3] * Xn * Xn + coef[4] * Yn * Yn
                            + coef[5] * Xn * Yn)
            log(f"rbf-constrained: ch{c} chroma quad "
                f"[{coef[0] * 65535:+.2f}, {coef[1] * 65535:+.2f}, "
                f"{coef[2] * 65535:+.2f}, {coef[3] * 65535:+.2f}, "
                f"{coef[4] * 65535:+.2f}, {coef[5] * 65535:+.2f}] c16 "
                f"(x, y, 1, x2, y2, xy)")
        else:
            bg = gray_bg
        outp[c] = planes[c] - bg + float(np.median(bg))
    am.write_fits_planes(out, cards, outp)
    return out


def sanitize(v):
    return str(v).replace(" ", "").replace("/", "_").replace("=", "") \
        .replace("-", "m").replace(".", "p")[:40]


def measure_jpg(path):
    from PIL import Image
    a8 = np.asarray(Image.open(path), dtype=np.float64)
    qa = bg_qa.qa_metrics(a8)
    data = (a8.transpose(2, 0, 1) / 255.0).astype(np.float32)
    stars = am.star_metrics(data[1])
    lev = am.channel_levels(data)
    return qa, stars, lev


def fmt(v, spec="{:.2f}"):
    return "" if v is None else spec.format(v)
