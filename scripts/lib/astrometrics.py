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

# --- per-set geometry context ---------------------------------------------
# Corridor, foreground and report-box geometry are COMPOSITION facts, not
# algorithm constants. Product entry points call configure(session, set,
# stack) which resolves, in order:
#   <session>/config_<set>.json  (tracked; composition facts are process)
#   corridor mode "manual" (explicit p0/p1/halfw)  |  "wcs" (galactic-
#   latitude band from the plate solve: work/wcs_<set>.json or the stack
#   header)  |  "none" (no config + no WCS: corridor absent -> the gate's
#   sky scope degrades to whole-frame on the starless render = stricter,
#   with a warning; mw_boost is skipped).
# A bare, unconfigured CTX carries NO composition geometry (see
# SetContext.__init__): corridor 'none', foreground None. The real
# geometry is resolved per set by configure() from config_<set>.json or
# the plate-solve WCS; set-03's hand-measured values live in its config,
# NEVER as a module default — so importing this module and forgetting to
# configure() can never apply one dataset's masks to another's data.

# ICRS (J2000) equatorial -> galactic unit-vector rotation (IAU 1958
# pole/center as realized for J2000; standard 3x3, no astropy needed).
_EQ2GAL = np.array([
    [-0.0548755604, -0.8734370902, -0.4838350155],
    [+0.4941094279, -0.4448296300, +0.7469822445],
    [-0.8676661490, -0.1980763734, +0.4559837762]])


class SetContext:
    """Resolved per-set geometry (see configure()). A freshly constructed
    (unconfigured) context carries NO geometry — corridor 'none',
    foreground None, no report boxes — so any entry point that forgets to
    call configure() degrades to whole-frame / no-mask (stricter, and
    warned by configure()) instead of silently inheriting set-03's masks.
    configure() fills these from config_<set>.json or the plate solve."""

    def __init__(self):
        self.source = "unconfigured"
        self.corridor_mode = "none"          # manual | wcs | none
        self.band_p0 = None                  # manual mode: set by configure()
        self.band_p1 = None
        self.band_halfw = None
        self.b_halfwidth_deg = 9.0           # wcs mode default: |b| <= this
        # (calibrated against set-03's hand-measured corridor: IoU 0.776,
        # gate verdict unchanged)
        self.wcs = None                      # dict of WCS cards (floats)
        self.foreground = None               # (x0,y0,x1,y1) | "mask" | None
        self.fg_mask_path = None             # npz pixel mask (landscape
        #                                      compositions a rect can't
        #                                      model); wins over rect
        self.mw_box = None                   # report boxes | None = derive
        self.sky_box = None
        self.judgment_crops = None           # {name: [x0,y0,x1,y1] px} | None
        self.starsep = {}                    # optional per-set overrides
        self._cache = {}


CTX = SetContext()


def _wcs_floats(d):
    """Normalize a WCS dict ({KEY: value} or {KEY: [value, comment]} from
    solve_field --json / FITS header parse) to plain floats/strings."""
    out = {}
    for k, v in d.items():
        val = v[0] if isinstance(v, (list, tuple)) else v
        if isinstance(val, str):
            val = val.strip().strip("'").strip()
        try:
            out[k] = float(val)
        except (TypeError, ValueError):
            out[k] = val
    return out


def read_fits_header(path):
    """Header cards only (same parse as read_fits, no data)."""
    hdr = {}
    with open(path, "rb") as f:
        off = 0
        while True:
            block = f.read(2880).decode("ascii", "replace")
            if not block:
                sys.exit(f"astrometrics: no END card in {path}")
            off += 2880
            for i in range(0, 2880, 80):
                c = block[i:i + 80]
                key = c[:8].strip()
                if key == "END":
                    return hdr
                if "=" in c:
                    hdr[key] = c[10:].split("/")[0].strip()


def _find_wcs(session_dir, set_name, stack=None):
    """WCS source resolution: work/wcs_<set>.json, else the stack header
    (solve_field-injected or siril platesolve). Returns (dict, src) or
    (None, None)."""
    import json as _json
    if session_dir and set_name:
        p = os.path.join(session_dir, "work", f"wcs_{set_name}.json")
        if os.path.exists(p):
            return _wcs_floats(_json.load(open(p))), os.path.basename(p)
    if stack and os.path.exists(stack):
        hdr = _wcs_floats(read_fits_header(stack))
        if "CRVAL1" in hdr and "CD1_1" in hdr:
            return hdr, os.path.basename(stack) + " header"
    return None, None


def configure(session_dir, set_name, stack=None, quiet=False):
    """Resolve the per-set geometry context (module global CTX).

    Precedence: config_<set>.json fields; corridor 'wcs' mode (default
    when no config) pulls the plate-solve WCS; nothing found -> corridor
    'none' + foreground None, loudly. Returns the context."""
    global CTX
    ctx = SetContext()
    ctx.corridor_mode = "none"
    ctx.foreground = None
    ctx.mw_box = ctx.sky_box = None
    src = []
    cfg = {}
    cfgp = (os.path.join(session_dir, f"config_{set_name}.json")
            if session_dir and set_name else None)
    if cfgp and os.path.exists(cfgp):
        import json as _json
        cfg = _json.load(open(cfgp))
        src.append(os.path.basename(cfgp))
    cor = cfg.get("corridor", {"mode": "wcs"})
    mode = (cor or {}).get("mode", "wcs")
    if mode == "manual":
        ctx.corridor_mode = "manual"
        ctx.band_p0 = tuple(cor["p0"])
        ctx.band_p1 = tuple(cor["p1"])
        ctx.band_halfw = float(cor["halfw"])
    elif mode == "wcs":
        ctx.b_halfwidth_deg = float((cor or {}).get("b_halfwidth_deg",
                                                    ctx.b_halfwidth_deg))
        wcs, wsrc = _find_wcs(session_dir, set_name, stack)
        if wcs is not None:
            ctx.wcs = wcs
            ctx.corridor_mode = "wcs"
            src.append(f"wcs:{wsrc}")
        else:
            ctx.corridor_mode = "none"
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
                  "(regen: scripts/suggest_foreground.py) — foreground "
                  "treated as none", flush=True)
    elif fg and fg.get("rect"):
        ctx.foreground = tuple(float(v) for v in fg["rect"])
    if cfg.get("mw_box"):
        ctx.mw_box = tuple(cfg["mw_box"])
    if cfg.get("sky_box"):
        ctx.sky_box = tuple(cfg["sky_box"])
    if cfg.get("judgment_crops"):
        ctx.judgment_crops = {k: tuple(v)
                              for k, v in cfg["judgment_crops"].items()}
    ctx.starsep = cfg.get("starsep", {})
    ctx.source = "+".join(src) if src else "none"
    if not quiet:
        msg = (f"[setctx] {set_name or 'unconfigured'}: "
               f"corridor={ctx.corridor_mode}"
               + (f" (|b|<={ctx.b_halfwidth_deg}deg)"
                  if ctx.corridor_mode == "wcs" else "")
               + f", foreground={'rect' if ctx.foreground else 'none'}"
               + f", source={ctx.source}")
        print(msg, flush=True)
        if ctx.corridor_mode == "none":
            print("[setctx] WARNING: no corridor (no config, no WCS) — "
                  "sky-scope QA degrades to whole-frame on the starless "
                  "render; mw_boost will be skipped", flush=True)
    CTX = ctx
    return ctx


def _radec_grid(wcs, h, w, step=16):
    """Coarse display-oriented RA/Dec grids (radians) from a TAN-SIP WCS.
    Rows are display order (top-down); FITS y = h - display_row."""
    nr = max(2, h // step)
    nc = max(2, w // step)
    rs = np.linspace(0.0, h - 1.0, nr)
    cs = np.linspace(0.0, w - 1.0, nc)
    C, R = np.meshgrid(cs, rs)
    xf = C + 1.0            # FITS 1-based x
    yf = h - R              # FITS y (bottom-up) for display row R
    u = xf - float(wcs["CRPIX1"])
    v = yf - float(wcs["CRPIX2"])
    ao = int(wcs.get("A_ORDER", 0) or 0)
    bo = int(wcs.get("B_ORDER", 0) or 0)
    du = np.zeros_like(u)
    dv = np.zeros_like(v)
    for p in range(ao + 1):
        for q in range(ao + 1 - p):
            cpq = float(wcs.get(f"A_{p}_{q}", 0.0) or 0.0)
            if cpq:
                du += cpq * (u ** p) * (v ** q)
    for p in range(bo + 1):
        for q in range(bo + 1 - p):
            cpq = float(wcs.get(f"B_{p}_{q}", 0.0) or 0.0)
            if cpq:
                dv += cpq * (u ** p) * (v ** q)
    u2, v2 = u + du, v + dv
    xi = np.radians(float(wcs["CD1_1"]) * u2 + float(wcs["CD1_2"]) * v2)
    eta = np.radians(float(wcs["CD2_1"]) * u2 + float(wcs["CD2_2"]) * v2)
    ra0 = np.radians(float(wcs["CRVAL1"]))
    dec0 = np.radians(float(wcs["CRVAL2"]))
    rr = np.hypot(xi, eta)
    cang = np.arctan(rr)                      # inverse gnomonic
    cosc = np.cos(cang)
    sinc_r = np.where(rr > 1e-12, np.sin(cang) / np.maximum(rr, 1e-12), 1.0)
    dec = np.arcsin(np.clip(
        cosc * np.sin(dec0) + eta * sinc_r * np.cos(dec0), -1.0, 1.0))
    ra = ra0 + np.arctan2(
        xi * sinc_r, cosc * np.cos(dec0) - eta * sinc_r * np.sin(dec0))
    return ra, dec


def galactic_maps(h, w):
    """Full-res float32 (b_deg, l_deg) maps for CTX.wcs, display-oriented.
    Computed on a coarse grid (WCS is smooth), upsampled via the galactic
    unit VECTOR (wrap-safe for l), cached per (h, w)."""
    key = ("gal", h, w)
    if key in CTX._cache:
        return CTX._cache[key]
    from scipy.ndimage import zoom
    ra, dec = _radec_grid(CTX.wcs, h, w)
    cd = np.cos(dec)
    vec = np.stack([cd * np.cos(ra), cd * np.sin(ra), np.sin(dec)])
    g = np.tensordot(_EQ2GAL, vec, axes=1)
    full = []
    for i in range(3):
        z = zoom(g[i].astype(np.float32),
                 (h / g.shape[1], w / g.shape[2]), order=1)
        # zoom rounds the output shape; pad/crop the last px to (h, w)
        if z.shape[0] < h:
            z = np.pad(z, ((0, h - z.shape[0]), (0, 0)), mode="edge")
        if z.shape[1] < w:
            z = np.pad(z, ((0, 0), (0, w - z.shape[1])), mode="edge")
        full.append(z[:h, :w])
    gx, gy, gz = full
    b = np.degrees(np.arcsin(np.clip(gz, -1.0, 1.0))).astype(np.float32)
    l = (np.degrees(np.arctan2(gy, gx)) % 360.0).astype(np.float32)
    CTX._cache[key] = (b, l)
    return b, l


def frame_diag_deg(h, w):
    """Angular length of the frame diagonal (deg) from CTX.wcs — converts
    'fraction of the frame diagonal' feathers into degrees in wcs mode."""
    key = ("diag", h, w)
    if key in CTX._cache:
        return CTX._cache[key]
    ra, dec = _radec_grid(CTX.wcs, h, w, step=max(h, w))  # corners only
    v = np.stack([np.cos(dec) * np.cos(ra),
                  np.cos(dec) * np.sin(ra), np.sin(dec)], axis=-1)
    dot = float(np.clip((v[0, 0] * v[-1, -1]).sum(), -1.0, 1.0))
    d = float(np.degrees(np.arccos(dot)))
    CTX._cache[key] = d
    return d


def band_mask_frac(h, w, feather=0.0):
    """Soft [0..1] corridor mask of the MW band (1 inside). feather is an
    extra half-width over which the mask rolls off smoothly, as a fraction
    of the frame diagonal (converted to degrees in wcs mode).
    Modes (CTX): manual = legacy straight strip (byte-identical math);
    wcs = |galactic b| <= b_halfwidth_deg; none = zeros."""
    if CTX.corridor_mode == "none":
        return np.zeros((h, w), np.float32)
    if CTX.corridor_mode == "wcs":
        b, _ = galactic_maps(h, w)
        d = np.abs(b)
        hw = float(CTX.b_halfwidth_deg)
        if feather <= 0:
            return (d <= hw).astype(np.float32)
        fdeg = feather * frame_diag_deg(h, w)
        return np.clip((hw + fdeg - d) / fdeg, 0.0, 1.0).astype(np.float32)
    ys = (np.arange(h) + 0.5) / h
    xs = (np.arange(w) + 0.5) / w
    X, Y = np.meshgrid(xs, ys)
    x0, y0 = CTX.band_p0
    x1, y1 = CTX.band_p1
    dx, dy = x1 - x0, y1 - y0
    n2 = dx * dx + dy * dy
    t = ((X - x0) * dx + (Y - y0) * dy) / n2
    t = np.clip(t, 0.0, 1.0)
    px, py = x0 + t * dx, y0 + t * dy
    d = np.hypot(X - px, Y - py)  # distance in frame-fraction units
    if feather <= 0:
        return (d <= CTX.band_halfw).astype(np.float32)
    return np.clip((CTX.band_halfw + feather - d) / feather, 0.0, 1.0) \
        .astype(np.float32)


def band_along_coord(h, w, stride=1):
    """Per-pixel 'along the band' coordinate for profile binning
    (corridor_report): manual mode = projection onto the band axis (px
    units, legacy math); wcs mode = galactic longitude l (deg); none ->
    None."""
    if CTX.corridor_mode == "none":
        return None
    if CTX.corridor_mode == "wcs":
        _, l = galactic_maps(h, w)
        return l[::stride, ::stride]
    p0 = np.array([CTX.band_p0[0] * w, CTX.band_p0[1] * h])
    p1 = np.array([CTX.band_p1[0] * w, CTX.band_p1[1] * h])
    u = (p1 - p0) / np.linalg.norm(p1 - p0)
    yy, xx = np.mgrid[0:h:stride, 0:w:stride]
    return (xx - p0[0]) * u[0] + (yy - p0[1]) * u[1]


def box_median_g(img_chw, box):
    c, h, w = img_chw.shape
    x0, y0, x1, y1 = (int(box[0] * w), int(box[1] * h),
                      int(box[2] * w), int(box[3] * h))
    return float(np.median(img_chw[min(1, c - 1), y0:y1, x0:x1]))


def report_boxes(h, w):
    """(mw_box, sky_box) fractions for the MW-contrast report. Config'd
    boxes win; else derived from the corridor mask: densest-corridor
    0.30x0.25 window vs the least-corridor window (deterministic grid
    search, foreground excluded); no corridor -> None."""
    if CTX.mw_box and CTX.sky_box:
        return CTX.mw_box, CTX.sky_box
    key = ("boxes", h, w)
    if key in CTX._cache:
        return CTX._cache[key]
    if CTX.corridor_mode == "none":
        return None, None
    s = 8
    m = band_mask_frac(h, w)[::s, ::s]
    keep = branch_mask(h, w, stride=s).astype(np.float32)
    bw, bh = 0.30, 0.25
    hh, ww = m.shape
    bwp, bhp = int(ww * bw), int(hh * bh)
    best_mw, best_sky = None, None
    hi, lo = -1.0, 2.0
    for fy in np.linspace(0.0, 1.0 - bh, 13):
        for fx in np.linspace(0.0, 1.0 - bw, 13):
            y0, x0 = int(fy * hh), int(fx * ww)
            sl = np.s_[y0:y0 + bhp, x0:x0 + bwp]
            kfrac = keep[sl].mean()
            if kfrac < 0.98:          # stay clear of the foreground
                continue
            v = float(m[sl].mean())
            box = (round(fx, 3), round(fy, 3),
                   round(fx + bw, 3), round(fy + bh, 3))
            if v > hi:
                hi, best_mw = v, box
            if v < lo:
                lo, best_sky = v, box
    if hi < 0.02:   # corridor never actually crosses the frame (e.g. a
        best_mw = best_sky = None   # high-galactic-latitude field)
    CTX._cache[key] = (best_mw, best_sky)
    return best_mw, best_sky


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
    rectangle. For rendering operators (lum_core weight, mw_boost
    exclusion): corrections fade over ~feather*h px instead of stopping at
    a hard printed edge. CTX.foreground None -> zeros."""
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


def corridor_report(img8_hwc):
    """REPORTED corridor + seam metrics on an 8-bit HxWx3 render of the
    STARLESS layer. Not a gate — the gate scope masks the corridor, so
    these exist to make corridor-contained costs and mask seams
    measurable instead of invisible.

    Returns dict:
      floor_p50/floor_p5: corridor starless block-median G percentiles
        minus deep-sky block P50 (issue 3: how far the corridor floor sits
        above the sky; P5 ~ 'do the gaps reach sky black').
      band_rg/band_bg: P2V of the sigma-24-smoothed chroma profile binned
        along the band axis, hi-pass (issue 1's diffuse color bands).
      seam_y/seam_x: blotch-TEXTURE ratio across the foreground-rectangle
        edges (un-cored side MAD / cored side MAD of the sigma-48 mid-scale
        residual field). A level-step gauge fails here: the coring seam is
        a texture discontinuity whose strip-median is ~0; real sky
        gradients and 8-bit quantization dominate level steps. ~1.0 = no
        seam; a hard rendering mask measured 4.5 (y) / 1.35 (x)."""
    from scipy.ndimage import gaussian_filter, median_filter
    a = np.asarray(img8_hwc, dtype=np.float32)
    h, w, _ = a.shape
    G = a[..., 1]
    keep = branch_mask(h, w)
    res = {"floor_p50": None, "floor_p5": None,
           "band_rg": None, "band_bg": None,
           "seam_y": None, "seam_x": None}
    blk = 100

    def blocks(mask):
        gy, gx = h // blk, w // blk
        out = []
        for by in range(gy):
            for bx in range(gx):
                m = mask[by * blk:(by + 1) * blk, bx * blk:(bx + 1) * blk]
                if m.mean() > 0.8:
                    out.append(np.median(
                        G[by * blk:(by + 1) * blk, bx * blk:(bx + 1) * blk]))
        return np.asarray(out)

    if CTX.corridor_mode != "none":
        corr = band_mask_frac(h, w, feather=0.10)
        sky_b = blocks((corr < 0.01) & keep)
        cor_b = blocks((corr > 0.9) & keep)
        sky50 = float(np.percentile(sky_b, 50)) if len(sky_b) else float("nan")
        if len(cor_b):
            res["floor_p50"] = float(np.percentile(cor_b, 50) - sky50)
            res["floor_p5"] = float(np.percentile(cor_b, 5) - sky50)

        # band chroma along the corridor axis — only when the corridor
        # actually crosses the frame (len(cor_b)); a high-galactic-latitude
        # field has no band, so the whole-frame chroma spread it would
        # otherwise report is meaningless (the floor guard above skips it
        # for the same reason).
        if len(cor_b):
            t_along = band_along_coord(h, w, stride=4)
            t_along = np.asarray(t_along).ravel()
            msk = keep[::4, ::4].ravel()
            if CTX.corridor_mode == "wcs":
                # t_along is galactic longitude l in [0,360): a field
                # straddling l=0 (Sagittarius/Scutum) splits into two
                # clusters at the ends of a raw min->max axis and empties
                # the middle bins. Re-center on the circular mean of the
                # in-frame l so the bins span one contiguous arc.
                ang = np.radians(t_along[msk])
                lc = np.degrees(np.arctan2(np.sin(ang).mean(),
                                           np.cos(ang).mean()))
                t_along = (t_along - lc + 180.0) % 360.0 - 180.0
            for key, ch in (("band_rg", a[..., 0] - G), ("band_bg", a[..., 2] - G)):
                sm = gaussian_filter(ch, 24)[::4, ::4].ravel()
                bins = np.linspace(t_along[msk].min(), t_along[msk].max(), 160)
                idx = np.digitize(t_along, bins)
                prof = np.array([np.median(sm[(idx == i) & msk])
                                 for i in range(1, len(bins))
                                 if ((idx == i) & msk).sum() > 200])
                resid = prof - median_filter(prof, 31, mode="nearest")
                res[key] = float(np.percentile(resid, 99) - np.percentile(resid, 1))

    if CTX.foreground is not None and CTX.foreground != "mask":
        # seam gauges are rect-edge-specific; mask foregrounds have no
        # straight printed edge to gauge (and no rendering op multiplies
        # a hard mask)
        resid = G - gaussian_filter(G, 16)
        blotch = gaussian_filter(resid, 48)

        def tex(sl):
            v = blotch[sl]
            return 1.4826 * float(np.median(np.abs(v)))

        # seam gauges anchored to the foreground rect edges; the sampling
        # strips are rect-proportional with fractions chosen to reproduce
        # the original set-03 strips EXACTLY (rect (0,0.75,0.22,1.0):
        # x 5/22..20/22 of rect width = 0.05w..0.20w, y 3/25..22/25 of
        # rect height = 0.78h..0.97h — the calibrated gauge positions).
        fx0, fy0, fx1, fy1 = CTX.foreground
        rw, rh = fx1 - fx0, fy1 - fy0
        y_e, x_e = int(fy0 * h), int(fx1 * w)
        x0 = int((fx0 + rw * 5.0 / 22.0) * w)
        x1 = int((fx0 + rw * 20.0 / 22.0) * w)
        res["seam_y"] = tex(np.s_[y_e + 40:y_e + 320, x0:x1]) \
            / max(tex(np.s_[y_e - 320:y_e - 40, x0:x1]), 1e-6)
        y0 = int((fy0 + rh * 3.0 / 25.0) * h)
        y1 = int((fy0 + rh * 22.0 / 25.0) * h)
        res["seam_x"] = tex(np.s_[y0:y1, x_e - 320:x_e - 40]) \
            / max(tex(np.s_[y0:y1, x_e + 40:x_e + 320]), 1e-6)
    return res


def star_shell_report(img8_hwc, cat_npz):
    """REPORTED star-shell metrics — the ghost-aura defect class: the
    stars-layer MTF amplifies skirt noise into a colored shell between
    each star's core and its dilated mask edge, ending at a cliff.
    Invisible to the background gate (it lives ON stars), so it gets its
    own numbers in every render, like corridor_report for the corridor.

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
