#!/usr/bin/env python3
"""Shared measurement library for pipeline inspection and rendering.

Pure numpy/scipy/PIL. Everything that grades an image lives here so
inspect_stage.py (per-stage report) and starcomb's ladder (single-variable
sweeps) measure identically. bg_qa.py stays the final hard gate; this
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

# --- per-set geometry context ---------------------------------------------
# The only per-set COMPOSITION fact is the terrestrial FOREGROUND (a treeline
# to exclude from sky statistics and protect in rendering operators) plus its
# report/crop boxes. Product entry points call configure(session, set) which
# reads <session>/config_<set>.json. A bare, unconfigured CTX carries NO
# geometry (foreground None), so a forgotten configure() degrades to
# whole-frame / no-mask instead of inheriting another dataset's foreground.
# The background is NOT a per-set composition fact: the gate (bg_qa) selects
# its sky STATISTICALLY, because a geometric band cannot scope an
# object-dominated field.


class SetContext:
    """Resolved per-set geometry (see configure()). A freshly constructed
    (unconfigured) context carries NO geometry — foreground None, no boxes —
    so any entry point that forgets to call configure() degrades to
    whole-frame / no-mask instead of silently inheriting another set's
    foreground. configure() fills these from config_<set>.json."""

    def __init__(self):
        self.source = "unconfigured"
        self.foreground = None               # (x0,y0,x1,y1) | "mask" | None
        self.fg_mask_path = None             # npz pixel mask (landscape
        #                                      compositions a rect can't
        #                                      model); wins over rect
        self.judgment_crops = None           # {name: [x0,y0,x1,y1] px} | None
        self.starsep = {}                    # optional per-set overrides
        self._cache = {}


CTX = SetContext()


def configure(session_dir, set_name, stack=None, quiet=False):
    """Resolve the per-set geometry context (module global CTX) from
    <session>/config_<set>.json: the terrestrial foreground (rect or npz
    mask), its report/crop boxes, and optional starsep overrides. No config
    -> foreground None (whole-frame, no mask). `stack` is accepted and
    ignored (kept for call-site compatibility). Returns the context."""
    global CTX
    ctx = SetContext()
    src = []
    cfg = {}
    cfgp = (os.path.join(session_dir, f"config_{set_name}.json")
            if session_dir and set_name else None)
    if cfgp and os.path.exists(cfgp):
        import json as _json
        cfg = _json.load(open(cfgp))
        src.append(os.path.basename(cfgp))
    fg = cfg.get("foreground")
    if fg and fg.get("mask"):
        p = fg["mask"]
        if not os.path.isabs(p):
            p = os.path.join(session_dir, p)
        if os.path.exists(p):
            ctx.fg_mask_path = p
            ctx.foreground = "mask"
        else:
            print(f"[setctx] WARNING: foreground mask {p} missing "
                  "(regen: scripts/geometry/suggest_foreground.py) — foreground "
                  "treated as none", flush=True)
    elif fg and fg.get("rect"):
        ctx.foreground = tuple(float(v) for v in fg["rect"])
    if cfg.get("judgment_crops"):
        ctx.judgment_crops = {k: tuple(v)
                              for k, v in cfg["judgment_crops"].items()}
    ctx.starsep = cfg.get("starsep", {})
    ctx.source = "+".join(src) if src else "none"
    if not quiet:
        print(f"[setctx] {set_name or 'unconfigured'}: "
              f"foreground={'mask' if ctx.foreground == 'mask' else 'rect' if ctx.foreground else 'none'}"
              f", source={ctx.source}", flush=True)
    CTX = ctx
    return ctx


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


def _fg_mask(h, w):
    """Full-res boolean foreground mask from CTX.fg_mask_path (cached).
    True = foreground."""
    key = ("fgmask", h, w)
    if key in CTX._cache:
        return CTX._cache[key]
    m = np.load(CTX.fg_mask_path)["mask"].astype(bool)
    if m.shape != (h, w):
        from scipy.ndimage import zoom
        m = zoom(m.astype(np.uint8),
                 (h / m.shape[0], w / m.shape[1]), order=0).astype(bool)
        if m.shape[0] < h:
            m = np.pad(m, ((0, h - m.shape[0]), (0, 0)), mode="edge")
        if m.shape[1] < w:
            m = np.pad(m, ((0, 0), (0, w - m.shape[1])), mode="edge")
        m = m[:h, :w]
    CTX._cache[key] = m
    return m


def branch_mask(h, w, stride=1):
    """True where measurable (the foreground excluded; set-03: the
    bottom-left branch rect, rows >=75% height, cols <22% w; mask-file
    foregrounds for compositions a rect can't model).
    STATISTICS scope only: a hard edge is fine when selecting samples. Any
    RENDERING operator must use branch_mask_frac instead — a hard mask
    multiplied into a correction prints a visible seam (measured +1.0/−1.5
    counts). CTX.foreground None -> all True."""
    if CTX.foreground == "mask":
        return ~_fg_mask(h, w)[::stride, ::stride]
    m = np.ones((len(range(0, h, stride)), len(range(0, w, stride))), bool)
    if CTX.foreground is None:
        return m
    x0, y0, x1, y1 = CTX.foreground
    ys = np.arange(0, h, stride) / h
    xs = np.arange(0, w, stride) / w
    m[np.ix_((ys >= y0) & (ys < y1), (xs >= x0) & (xs < x1))] = False
    return m


def branch_mask_frac(h, w, feather=0.05):
    """Soft [0..1] foreground mask (1 = foreground rect, 0 = sky) with a
    smooth rolloff over `feather` (fraction of frame height) OUTSIDE the
    rectangle. For a rendering operator that needs a feathered foreground:
    corrections fade over ~feather*h px instead of stopping at a hard
    printed edge. CTX.foreground None -> zeros."""
    if CTX.foreground is None:
        return np.zeros((h, w), np.float32)
    if CTX.foreground == "mask":
        key = ("fgfrac", h, w, round(float(feather), 4))
        if key in CTX._cache:
            return CTX._cache[key]
        m = _fg_mask(h, w)
        if feather <= 0:
            out = m.astype(np.float32)
        else:
            from scipy.ndimage import distance_transform_edt
            d = distance_transform_edt(~m)  # px to the mask
            out = np.clip(1.0 - d / (feather * h), 0.0, 1.0) \
                .astype(np.float32)
        CTX._cache[key] = out
        return out
    x0, y0, x1, y1 = CTX.foreground
    ys = (np.arange(h) + 0.5) / h
    xs = (np.arange(w) + 0.5) / w
    # signed distance outside the rectangle along each axis (0 inside)
    dy = np.maximum(np.maximum(y0 - ys, ys - y1), 0.0)[:, None]
    dx = np.maximum(np.maximum(x0 - xs, xs - x1), 0.0)[None, :]
    d = np.hypot(dy, dx)  # frame-fraction distance to the rectangle
    if feather <= 0:
        return (d <= 0).astype(np.float32)
    return np.clip(1.0 - d / feather, 0.0, 1.0).astype(np.float32)


def sky_pixel_mask(ch, k=3.0):
    """Boolean background-sky mask: pixels at or below bg + k*sigma (the dark
    sky), foreground excluded. The composition-agnostic scope for noise
    estimation in the rendering corings — real signal (galaxy / Milky Way /
    nebula) is brighter than the sky and drops out, so the estimate tracks
    the true sky noise on ANY framing."""
    bg, sig = bg_stats(ch)
    h, w = ch.shape
    return (ch <= bg + k * sig) & branch_mask(h, w)


def star_shell_report(img8_hwc, cat_npz):
    """REPORTED star-shell metrics — the ghost-aura defect class: the
    stars-layer MTF amplifies skirt noise into a colored shell between
    each star's core and its dilated mask edge, ending at a cliff.
    Invisible to the background gate (it lives ON stars), so it gets its
    own reported numbers in every render.

    Sample: catalog peak ranks 10..80 (bright tier, worst shells),
    frame-interior. Median annulus profiles around their centroids:
      aura_lum:    max over r in [8,16) of median G minus the r in
                   [32,40) baseline (counts). THE defect discriminant: the
                   ghost-aura shell reads high here while a clean render
                   reads low, so the WARN bound 4.0 sits with clean margin
                   on both sides.
      shell_chroma: max over r in [4,12) of mean(MAD(R-G), MAD(B-G)).
                   REPORT-ONLY, no bound: it mixes noise speckle with the
                   HONEST PSF fringe (dispersion/CA on trailed stars) and
                   is sample/chain dependent, so a fixed threshold would
                   cry wolf. Track the trend; it drops when acquisition
                   fixes the fringe.
    WARN only, never a gate."""
    from scipy import ndimage
    a = np.asarray(img8_hwc, dtype=np.float32)
    h, w = a.shape[:2]
    cat = np.load(cat_npz) if isinstance(cat_npz, str) else cat_npz
    peak, ids, labels = cat["peak"], cat["ids"], cat["labels"]
    order = np.argsort(peak)[::-1][10:80]
    coms = ndimage.center_of_mass(np.ones_like(labels, np.uint8),
                                  labels, ids[order])
    R = 40
    yy, xx = np.mgrid[-R:R + 1, -R:R + 1]
    rr = np.hypot(yy, xx)
    rings = [(rr >= i) & (rr < i + 1) for i in range(R)]
    lum = [[] for _ in range(R)]
    ch = [[] for _ in range(R)]
    for (cy, cx) in coms:
        cy, cx = int(round(cy)), int(round(cx))
        if not (R < cy < h - R and R < cx < w - R):
            continue
        t = a[cy - R:cy + R + 1, cx - R:cx + R + 1]
        G = t[..., 1]
        RG = t[..., 0] - G
        BG = t[..., 2] - G
        for i in range(R):
            m = rings[i]
            lum[i].append(np.median(G[m]))
            ch[i].append((1.4826 * np.median(np.abs(RG[m] - np.median(RG[m])))
                          + 1.4826 * np.median(np.abs(BG[m] - np.median(BG[m])))) / 2)
    if not lum[0]:
        return {"aura_lum": None, "shell_chroma": None, "n_sample": 0}
    pl = np.array([np.median(v) for v in lum])
    pc = np.array([np.median(v) for v in ch])
    base = float(np.median(pl[32:40]))
    return {"aura_lum": float(np.max(pl[8:16]) - base),
            "shell_chroma": float(np.max(pc[4:12])),
            "n_sample": len(lum[0])}


STAR_SHELL_WARN = {"aura_lum": 4.0}


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
    if CTX.foreground == "mask":     # block-level foreground fraction
        fg = _fg_mask(ny, nx)[:gy * block, :gx * block]
        bf = fg.reshape(gy, block, gx, block).mean(axis=(1, 3))
        keep2d = bf < 0.5
    elif CTX.foreground is not None:  # foreground rect in ±1 block coords
        fx0, fy0, fx1, fy1 = CTX.foreground
        keep2d = ~(((cy[:, None] >= 2 * fy0 - 1) & (cy[:, None] <= 2 * fy1 - 1))
                   & ((cx[None, :] >= 2 * fx0 - 1) & (cx[None, :] < 2 * fx1 - 1)))
    else:
        keep2d = np.ones((gy, gx), bool)
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


def write_png16(path, arr16):
    """Write a 16-bit RGB PNG (color type 2, bit depth 16) from a uint16
    (H, W, 3) array. Pure zlib/struct — Pillow cannot write 48-bit RGB
    PNGs, and the render is computed in float: an 8-bit final quantizes
    to 256 levels, this keeps 65536 (visually indistinguishable from the
    float render)."""
    import struct
    import zlib
    h, w, c = arr16.shape
    assert c == 3 and arr16.dtype == np.uint16

    def chunk(tag, payload):
        return (struct.pack(">I", len(payload)) + tag + payload
                + struct.pack(">I", zlib.crc32(tag + payload) & 0xffffffff))

    # scanlines: filter byte 0 + big-endian samples per row
    body = np.empty((h, 1 + w * 6), np.uint8)
    body[:, 0] = 0
    body[:, 1:] = arr16.astype(">u2").reshape(h, -1).view(np.uint8)
    ihdr = struct.pack(">IIBBBBB", w, h, 16, 2, 0, 0, 0)
    with open(path, "wb") as f:
        f.write(b"\x89PNG\r\n\x1a\n")
        f.write(chunk(b"IHDR", ihdr))
        f.write(chunk(b"IDAT", zlib.compress(body.tobytes(), 6)))
        f.write(chunk(b"IEND", b""))


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
