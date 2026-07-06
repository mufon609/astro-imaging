#!/usr/bin/env python3
"""Shared measurement library for pipeline inspection and experiments.

Pure numpy/scipy/PIL. Everything that grades an image lives here so
inspect_stage.py (per-stage report) and experiment.py (single-variable
ladders) measure identically. bg_qa.py stays the final hard gate; this
module imports its constants/functions where they overlap.

Units convention: FITS data are normalized to [0,1] floats internally;
"display units" in reports are 16-bit counts (x65535) for linear stages —
matching siril's stat output — and 8-bit counts for stretched JPEGs.
"""
import os
import sys
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bg_qa  # noqa: E402  (constants + ring_amp shared with the gate)


# --- I/O ----------------------------------------------------------------------

def read_fits(path):
    """Minimal FITS reader (Siril-produced files): returns (data, hdr) with
    data float32 shaped (nchan, ny, nx) normalized to [0,1] for integer
    types; float data is taken as already 0..1 (Siril 32-bit convention)."""
    with open(path, "rb") as f:
        raw = f.read()
    hdr = {}
    off = 0
    while True:
        block = raw[off:off + 2880].decode("ascii", "replace")
        off += 2880
        done = False
        for i in range(0, 2880, 80):
            c = block[i:i + 80]
            key = c[:8].strip()
            if key == "END":
                done = True
                break
            if "=" in c:
                hdr[key] = c[10:].split("/")[0].strip()
        if done:
            break
        if off >= len(raw):
            sys.exit(f"astrometrics: no END card in {path}")
    bitpix = int(hdr["BITPIX"])
    naxis = int(hdr["NAXIS"])
    nx, ny = int(hdr["NAXIS1"]), int(hdr["NAXIS2"])
    nc = int(hdr.get("NAXIS3", "1")) if naxis == 3 else 1
    bzero = float(hdr.get("BZERO", "0"))
    bscale = float(hdr.get("BSCALE", "1"))
    dt = {-32: ">f4", -64: ">f8", 16: ">i2", 32: ">i4", 8: "u1"}[bitpix]
    data = np.frombuffer(raw, dtype=dt, count=nc * ny * nx, offset=off)
    data = data.astype(np.float32) * bscale + bzero
    if bitpix == 16:
        data /= 65535.0
    elif bitpix == 8:
        data /= 255.0
    elif bitpix == 32:
        data /= 4294967295.0
    # FITS rows are bottom-up; flip to display orientation (top-down) so
    # panels match the JPEG previews and the branch mask hits the right
    # corner regardless of input type.
    return data.reshape(nc, ny, nx)[:, ::-1, :].copy(), hdr


def fits_dims(path):
    """(width, height) from the header only — no data read."""
    import re
    raw = open(path, "rb").read(2880 * 4).decode("ascii", "replace")
    return (int(re.search(r"NAXIS1\s*=\s*(\d+)", raw).group(1)),
            int(re.search(r"NAXIS2\s*=\s*(\d+)", raw).group(1)))


def load_image(path):
    """FITS or JPEG/PNG -> (data float32 (C,H,W) in [0,1], kind str).
    kind is 'fits' or 'jpg' (jpg == 8-bit display referred)."""
    if path.lower().endswith((".fit", ".fits", ".fts")):
        data, _ = read_fits(path)
        return data, "fits"
    from PIL import Image
    a = np.asarray(Image.open(path), dtype=np.float32) / 255.0
    if a.ndim == 2:
        a = a[None]
    else:
        a = a.transpose(2, 0, 1)
    return a, "jpg"


# --- basic statistics ----------------------------------------------------------

# --- MW band corridor (shared geometry) ---------------------------------------
# The Milky Way band corridor in display fractions, measured on the L2
# starless layer (band-course measurement, see NOTES). Single source of
# truth: starcomb uses it to LOCALIZE the mw_boost (and to exclude
# background samples in mode 'banded'); bg_qa uses it to EXCLUDE the
# corridor from background statistics under the layer-appropriate QA scope
# (ratified 2026-07-06) — the corridor is known signal, exactly like the
# branch corner is known non-sky.

BAND_P0 = (0.30, 1.00)   # (x, y) fractions, bottom end
BAND_P1 = (0.80, 0.00)   # top-right exit (widened after the overlay check)
BAND_HALFW = 0.19        # fraction of the frame diagonal


def band_mask_frac(h, w, feather=0.0):
    """Soft [0..1] corridor mask of the MW band (1 inside). feather is an
    extra half-width over which the mask rolls off smoothly."""
    ys = (np.arange(h) + 0.5) / h
    xs = (np.arange(w) + 0.5) / w
    X, Y = np.meshgrid(xs, ys)
    x0, y0 = BAND_P0
    x1, y1 = BAND_P1
    dx, dy = x1 - x0, y1 - y0
    n2 = dx * dx + dy * dy
    t = ((X - x0) * dx + (Y - y0) * dy) / n2
    t = np.clip(t, 0.0, 1.0)
    px, py = x0 + t * dx, y0 + t * dy
    d = np.hypot(X - px, Y - py)  # distance in frame-fraction units
    if feather <= 0:
        return (d <= BAND_HALFW).astype(np.float32)
    return np.clip((BAND_HALFW + feather - d) / feather, 0.0, 1.0) \
        .astype(np.float32)


def bg_stats(ch, iters=5, stride=2):
    """(background median, robust pixel noise sigma).

    Median: iterative 3-sigma MAD clip (star-resistant level estimate).
    Sigma: MAD of ADJACENT-pixel differences / sqrt(2) — smooth gradients
    (moonglow, vignette, MW) cancel in the difference, so this tracks true
    pixel noise; a plain global MAD measured the gradient instead (10.5%
    "noise" on a stack siril grades at 1.46%)."""
    sub = ch[::stride, ::stride]
    x = sub.ravel()
    x = x[np.isfinite(x)]
    for _ in range(iters):
        med = np.median(x)
        s = 1.4826 * np.median(np.abs(x - med))
        if s == 0:
            break
        keep = np.abs(x - med) < 3.0 * s
        if keep.sum() < 1000 or keep.all():
            break
        x = x[keep]
    d = np.diff(sub, axis=1).ravel()
    d = d[np.isfinite(d)]
    sig = 1.4826 * np.median(np.abs(d - np.median(d))) / np.sqrt(2.0)
    return float(np.median(x)), float(sig)


def channel_levels(data):
    """Per-channel level summary in [0,1] units."""
    out = []
    for c in range(data.shape[0]):
        ch = data[c]
        sub = ch[::4, ::4]
        med, sig = bg_stats(ch)
        out.append({
            "median": med, "bgnoise": sig,
            "mean": float(sub.mean()),
            "p01": float(np.percentile(sub, 1)),
            "p99": float(np.percentile(sub, 99)),
            "max": float(ch.max()),
            "clip_frac": float((sub >= 0.999).mean()),
        })
    return out


# --- geometry helpers ----------------------------------------------------------

def radius_map(h, w, stride=1):
    yy = (np.arange(0, h, stride) - h / 2) / (h / 2)
    xx = (np.arange(0, w, stride) - w / 2) / (w / 2)
    return np.sqrt((yy[:, None] ** 2 + xx[None, :] ** 2) / 2.0)


def branch_mask(h, w, stride=1):
    """True where measurable (the bottom-left foreground branch excluded) —
    same geometry as bg_qa's block mask (rows >=75% height, cols <22% w)."""
    m = np.ones((len(range(0, h, stride)), len(range(0, w, stride))), bool)
    ys = np.arange(0, h, stride) / h
    xs = np.arange(0, w, stride) / w
    m[np.ix_(ys >= 0.75, xs < 0.22)] = False
    return m


def radial_profile(data, nbins=48, stride=4, mask_branch=False):
    """Median radial profile per channel on a subsampled grid.
    Returns (bin centers, prof (nbins, C) with NaN for empty bins)."""
    c, h, w = data.shape
    r = radius_map(h, w, stride)
    sub = data[:, ::stride, ::stride]
    keep = np.isfinite(sub[0])
    if mask_branch:
        keep &= branch_mask(h, w, stride)
    edges = np.linspace(0, 1, nbins + 1)
    centers = (edges[:-1] + edges[1:]) / 2
    prof = np.full((nbins, c), np.nan)
    idx = np.digitize(r.ravel(), edges) - 1
    kr = keep.ravel()
    for i in range(nbins):
        m = kr & (idx == i)
        if m.sum() > 200:
            for ci in range(c):
                prof[i, ci] = np.median(sub[ci].ravel()[m])
    return centers, prof


def radial_metrics(centers, prof):
    """Flatness numbers from a luminance (G) radial profile:
    - p2v_inner: peak-to-valley over r<=0.85 relative to its median
    - rim_dev: worst relative deviation in r>0.9 from the r~0.85 level
    - ring P2V (detrended, absolute in profile units) via bg_qa.ring_amp."""
    g = prof[:, min(1, prof.shape[1] - 1)]
    ok = ~np.isnan(g)
    inner = ok & (centers <= 0.85)
    rim = ok & (centers > 0.9)
    out = {}
    if inner.sum() >= 4:
        v = g[inner]
        ref = float(np.median(v))
        out["p2v_inner_rel"] = float((v.max() - v.min()) / max(abs(ref), 1e-9))
        anchor = float(v[-1])
        if rim.any():
            out["rim_dev_rel"] = float(
                np.max(np.abs(g[rim] - anchor)) / max(abs(ref), 1e-9))
    if ok.sum() >= 12:
        out["ring_p2v"] = bg_qa.ring_amp(g[ok])
        if prof.shape[1] == 3:
            out["ring_rg_p2v"] = bg_qa.ring_amp((prof[:, 0] - prof[:, 1])[ok])
            out["ring_bg_p2v"] = bg_qa.ring_amp((prof[:, 2] - prof[:, 1])[ok])
    return out


def plane_tilt(ch, block=101):
    """Fit a plane to block medians (branch corner masked); tilt as % of
    mean level per half-frame (same convention as selfflat.py's glow-tilt
    print). Without the mask the dark branch drags the fit and a glow-free
    frame still reads ~10%/half-frame."""
    ny, nx = ch.shape
    gy, gx = ny // block, nx // block
    t = ch[:gy * block, :gx * block]
    med = np.median(t.reshape(gy, block, gx, block).transpose(0, 2, 1, 3)
                    .reshape(gy, gx, -1), axis=2)
    cy = (np.arange(gy) * block + block / 2) / ny * 2 - 1
    cx = (np.arange(gx) * block + block / 2) / nx * 2 - 1
    keep2d = ~((cy[:, None] >= 0.5) & (cx[None, :] < -0.56))  # branch corner
    Y, X = np.meshgrid(cy, cx, indexing="ij")
    A = np.stack([np.ones(med.size), X.ravel(), Y.ravel()], axis=1)
    b = med.ravel()
    A, b = A[keep2d.ravel()], b[keep2d.ravel()]
    # one round of outlier rejection so stars/branch don't skew the plane
    cs, *_ = np.linalg.lstsq(A, b, rcond=None)
    r = b - A @ cs
    keep = np.abs(r - np.median(r)) < 3 * (1.4826 * np.median(np.abs(r - np.median(r))) + 1e-12)
    if keep.sum() >= 12:
        cs, *_ = np.linalg.lstsq(A[keep], b[keep], rcond=None)
    denom = abs(cs[0]) if abs(cs[0]) > 1e-9 else max(abs(np.median(b)), 1e-9)
    return float(100.0 * np.hypot(cs[1], cs[2]) / denom)


# --- star metrics ---------------------------------------------------------------

def star_metrics(ch, max_stars=500, k_sigma=8.0, cut=12, min_prom_frac=0.004):
    """Detect stars on one channel (local maxima above bg + k*sigma) and
    measure: count, equivalent-area FWHM, elongation, peak levels, halo
    ratio (flux 3-8px annulus / flux <=3px core). Works on linear FITS and
    stretched 8-bit alike (all values in [0,1]).

    A candidate counts as a star only if its prominence over the LOCAL ring
    background exceeds max(4*sigma, min_prom_frac*local_bg): on smooth
    surfaces (self-flat median) the noise sigma collapses and pure-sigma
    thresholds promote glow mottles to "stars" (measured: ratio 1.06 vs
    calibrated frames instead of ~0). n_stars counts ALL prominence-passing
    maxima; shape stats come from the brightest max_stars of them."""
    from scipy import ndimage
    h, w = ch.shape
    bg, sig = bg_stats(ch)
    if sig <= 0:
        return {"n_stars": 0}
    thr = bg + k_sigma * sig
    mx = ndimage.maximum_filter(ch, size=5, mode="nearest")
    cand = (ch >= mx) & (ch > thr)
    cand[:cut + 1, :] = cand[-cut - 1:, :] = False
    cand[:, :cut + 1] = cand[:, -cut - 1:] = False
    bm = branch_mask(h, w)
    cand &= bm
    ys, xs = np.nonzero(cand)
    if len(ys) == 0:
        return {"n_stars": 0, "bg": bg, "sigma": sig}
    peaks = ch[ys, xs]
    order = np.argsort(peaks)[::-1][:6000]  # brightest candidates only
    # de-duplicate plateau maxima (saturated cores): keep one per 9px box
    seen = np.zeros((h // 9 + 2, w // 9 + 2), bool)
    stars = []
    for i in order:
        gy, gx = ys[i] // 9, xs[i] // 9
        if seen[gy, gx]:
            continue
        seen[gy, gx] = True
        stars.append(i)
    yy0, xx0 = np.mgrid[-cut:cut + 1, -cut:cut + 1]
    rr = np.hypot(yy0, xx0)
    ring = rr >= cut - 1
    core = rr <= 3
    halo_a = (rr > 3) & (rr <= 8)
    half_zone = rr <= 10
    fwhms, elongs, halos, peak_list, contrasts = [], [], [], [], []
    n_pass = 0
    for i in stars:
        y, x = ys[i], xs[i]
        c = ch[y - cut:y + cut + 1, x - cut:x + cut + 1]
        if c.shape != (2 * cut + 1, 2 * cut + 1):
            continue
        loc_bg = float(np.median(c[ring]))
        pk = float(c[cut, cut])
        amp = pk - loc_bg
        if amp <= max(4 * sig, min_prom_frac * max(loc_bg, 1e-6)):
            continue
        n_pass += 1
        peak_list.append(pk)
        if n_pass > max_stars:
            continue  # count everything, shape-measure the brightest
        contrasts.append(amp)
        above = (c - loc_bg > amp / 2) & half_zone
        area = int(above.sum())
        fwhms.append(2.0 * np.sqrt(area / np.pi))
        if area >= 3:
            ay, ax = np.nonzero(above)
            wgt = (c - loc_bg)[above]
            cy = np.average(ay, weights=wgt)
            cx2 = np.average(ax, weights=wgt)
            vy = np.average((ay - cy) ** 2, weights=wgt)
            vx = np.average((ax - cx2) ** 2, weights=wgt)
            vxy = np.average((ay - cy) * (ax - cx2), weights=wgt)
            tr, det = vy + vx, vy * vx - vxy ** 2
            disc = max(tr * tr / 4 - det, 0.0)
            l1 = tr / 2 + np.sqrt(disc)
            l2 = max(tr / 2 - np.sqrt(disc), 1e-6)
            elongs.append(float(np.sqrt(l1 / l2)))
        cflux = float(np.clip(c - loc_bg, 0, None)[core].sum())
        hflux = float(np.clip(c - loc_bg, 0, None)[halo_a].sum())
        if cflux > 0:
            halos.append(hflux / cflux)
    if not peak_list:
        return {"n_stars": 0, "bg": bg, "sigma": sig}
    peak_arr = np.array(peak_list)
    top = peak_arr[:min(100, len(peak_arr))]  # already peak-sorted
    mid = peak_arr[100:500] if len(peak_arr) > 120 else peak_arr
    return {
        "n_stars": n_pass,  # prominence-passing maxima (uncapped)
        "n_maxima": int(len(stars)),  # raw dedup'd maxima among 6000 brightest
        "n_measured": min(n_pass, max_stars),
        "bg": bg, "sigma": sig,
        "fwhm_med": float(np.median(fwhms)),
        "elong_med": float(np.median(elongs)) if elongs else None,
        "halo_med": float(np.median(halos)) if halos else None,
        "top100_peak_med": float(np.median(top)),
        "mid_peak_med": float(np.median(mid)),  # ranks 100-500: the tier that
        # actually separates crisp from washed-out (top-100 saturate anyway)
        "contrast_med": float(np.median(contrasts)),
        "sat_star_frac": float((peak_arr >= 0.98).mean()),
    }


# --- consistent rendering -------------------------------------------------------

def mtf(x, m):
    """PixInsight/siril midtone transfer function, x in [0,1]."""
    return ((m - 1.0) * x) / (((2.0 * m - 1.0) * x) - m)


def autostretch_u8(data, sigma=-2.8, target=0.25):
    """The ONE consistent rendering used for every inspection JPEG:
    linked MTF autostretch — shadow clip at median + sigma*bgnoise (G
    channel stats), midtone solved so the background lands on `target`.
    Returns uint8 (H,W,3)."""
    g = data[min(1, data.shape[0] - 1)]
    med, sig = bg_stats(g)
    lo = max(0.0, med + sigma * sig)
    hi = 1.0
    x0 = (med - lo) / (hi - lo) if hi > lo else 0.5
    x0 = min(max(x0, 1e-6), 0.9999)
    m = x0 * (target - 1.0) / (2.0 * x0 * target - x0 - target)
    m = min(max(m, 1e-4), 1 - 1e-4)
    out = []
    for c in range(data.shape[0]):
        x = np.clip((data[c] - lo) / (hi - lo), 0.0, 1.0)
        out.append(mtf(x, m))
    a = np.stack(out, axis=-1)
    if a.shape[-1] == 1:
        a = np.repeat(a, 3, axis=-1)
    return (np.clip(a, 0, 1) * 255.0 + 0.5).astype(np.uint8)


def render_panel(data, out_path, thumb_stride=4, crop=700, quality=88):
    """Write the stage inspection JPEG: full-frame thumb (stride-subsampled)
    on the left; 1:1 center crop over 1:1 top-right corner crop on the
    right — all through the SAME autostretch (computed once, full image)."""
    from PIL import Image
    u8 = autostretch_u8(data)  # full res, one stretch for all panels
    h, w = u8.shape[:2]
    thumb = u8[::thumb_stride, ::thumb_stride]
    th, tw = thumb.shape[:2]
    gutter = 12
    ch = (th - gutter) // 2
    cw = min(crop, w)
    cy, cx = h // 2, w // 2
    center = u8[cy - ch // 2:cy + ch - ch // 2, cx - cw // 2:cx + cw - cw // 2]
    inset = 60
    corner = u8[inset:inset + ch, w - inset - cw:w - inset]
    canvas = np.full((th, tw + cw + gutter, 3), 24, np.uint8)
    canvas[:th, :tw] = thumb
    canvas[:center.shape[0], tw + gutter:tw + gutter + center.shape[1]] = center
    canvas[ch + gutter:ch + gutter + corner.shape[0],
           tw + gutter:tw + gutter + corner.shape[1]] = corner
    Image.fromarray(canvas).save(out_path, quality=quality)
    return {"panels": "left: full frame (1/%d); right: center 1:1 (top), "
                      "top-right corner 1:1 (bottom)" % thumb_stride}


def plot_radial(centers, prof, out_path, title="", display_scale=65535.0,
                ylabel="counts (16-bit)"):
    """Radial luminance + chroma profile PNG with the rim zone shaded."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(7, 5), sharex=True,
                                   height_ratios=[2, 1])
    ok = ~np.isnan(prof[:, 0])
    colors = ["#d62728", "#2ca02c", "#1f77b4"]
    names = ["R", "G", "B"]
    for c in range(prof.shape[1]):
        ax1.plot(centers[ok], prof[ok, c] * display_scale, color=colors[c % 3],
                 lw=1.2, label=names[c % 3])
    ax1.axvspan(0.9, 1.0, alpha=0.12, color="orange", label="rim zone")
    ax1.set_ylabel(ylabel)
    ax1.legend(fontsize=8, ncol=4)
    ax1.set_title(title, fontsize=10)
    if prof.shape[1] == 3:
        ax2.plot(centers[ok], (prof[ok, 0] - prof[ok, 1]) * display_scale,
                 color="#d62728", lw=1.0, label="R-G")
        ax2.plot(centers[ok], (prof[ok, 2] - prof[ok, 1]) * display_scale,
                 color="#1f77b4", lw=1.0, label="B-G")
        ax2.axhline(0, color="gray", lw=0.6)
        ax2.axvspan(0.9, 1.0, alpha=0.12, color="orange")
        ax2.legend(fontsize=8)
        ax2.set_ylabel("chroma")
    ax2.set_xlabel("normalized radius (1 = corner)")
    fig.tight_layout()
    fig.savefig(out_path, dpi=90)
    plt.close(fig)
