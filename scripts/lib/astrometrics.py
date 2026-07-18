#!/usr/bin/env python3
"""Shared FITS-read + per-set geometry helpers for the orchestration layer.

Pure numpy/scipy, EXAMINE/orchestrate only: a minimal FITS reader (feeds the
plate-solve star extraction), header-derived pixel scale, and the per-set
foreground geometry the tools are pointed around. It does NOT grade or
transform the deliverable's pixels — every pixel measurement and every pixel
operation is sourced from an industry tool (Siril / darktable /
astrometry.net / …), never hand-rolled here. Finals I/O is a tool's job
(Siril `savepng`/`savetif`); the hand-rolled FITS parse itself retires to
astropy (installed on this rig — an arm-doable retirement, BACKLOG item 6).

Units convention: FITS data are normalized to [0,1] floats internally.
"""
import os
import sys
import numpy as np


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
    # the branch mask hits the right corner regardless of input type.
    return data.reshape(nc, ny, nx)[:, ::-1, :].copy(), hdr


def fits_pixel_scale(path):
    """Pixel scale (arcsec/px) derived from the FOCALLEN (mm) + XPIXSZ (µm)
    header cards: 206.265·XPIXSZ/FOCALLEN — the same derivation the
    plate-solve scale hint uses, so recorded FWHM numbers stay
    rig-interpretable without any configured constant. None when either
    card is absent or degenerate (callers report px-only and say so
    rather than inventing a scale)."""
    import re
    raw = open(path, "rb").read(2880 * 8).decode("ascii", "replace")
    fl = re.search(r"FOCALLEN\s*=\s*([0-9.Ee+-]+)", raw)
    px = re.search(r"XPIXSZ\s*=\s*([0-9.Ee+-]+)", raw)
    if not fl or not px:
        return None
    try:
        fl_v, px_v = float(fl.group(1)), float(px.group(1))
    except ValueError:
        return None
    if fl_v <= 0 or px_v <= 0:
        return None
    return 206.265 * px_v / fl_v


# --- per-set geometry context ---------------------------------------------
# The only per-set COMPOSITION fact is the terrestrial FOREGROUND (a treeline
# to exclude from sky statistics and protect in rendering operators) plus its
# report/crop boxes. Product entry points call configure(session, set) which
# reads datasets/<session>/<set>/geometry.json. A bare, unconfigured CTX
# carries NO geometry (foreground None), so a forgotten configure() degrades
# to whole-frame / no-mask instead of inheriting another dataset's foreground.
# Only the terrestrial FOREGROUND is a per-set geometry fact (a mask/rect the
# tools are pointed around); the sky itself is never geometrically scoped
# here — its statistics are a tool's job.


class SetContext:
    """Resolved per-set geometry (see configure()). A freshly constructed
    (unconfigured) context carries NO geometry — foreground None, no boxes —
    so any entry point that forgets to call configure() degrades to
    whole-frame / no-mask instead of silently inheriting another set's
    foreground. configure() fills these from geometry.json."""

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


def dataset_dir(session_dir, set_name):
    """Tracked per-dataset home: <repo>/datasets/<session-basename>/<set>/.
    Session data dirs are gitignored (third-party raws must never be
    committed), so everything the repo must version about a dataset —
    geometry, recipe, baseline — lives here instead."""
    repo = os.path.dirname(os.path.dirname(os.path.dirname(
        os.path.abspath(__file__))))
    return os.path.join(repo, "datasets",
                        os.path.basename(os.path.normpath(session_dir)),
                        set_name)


def configure(session_dir, set_name, stack=None, quiet=False):
    """Resolve the per-set geometry context (module global CTX) from
    datasets/<session>/<set>/geometry.json: the terrestrial foreground
    (rect or npz mask), its report/crop boxes, and optional starsep
    overrides. No geometry file -> foreground None (whole-frame, no mask).
    Relative mask paths resolve against the SESSION dir (derived masks are
    data, they live with the data). `stack` is accepted and ignored (kept
    for call-site compatibility). Returns the context."""
    global CTX
    ctx = SetContext()
    src = []
    cfg = {}
    cfgp = (os.path.join(dataset_dir(session_dir, set_name), "geometry.json")
            if session_dir and set_name else None)
    if cfgp and os.path.exists(cfgp):
        import json as _json
        cfg = _json.load(open(cfgp))
        src.append(os.path.relpath(cfgp,
                                   os.path.dirname(os.path.dirname(cfgp))))
    fg = cfg.get("foreground")
    if fg and fg.get("mask"):
        p = fg["mask"]
        if not os.path.isabs(p):
            p = os.path.join(session_dir, p)
        if os.path.exists(p):
            ctx.fg_mask_path = p
            ctx.foreground = "mask"
        else:
            print(f"[setctx] WARNING: foreground mask {p} missing — "
                  "foreground treated as none (supply the mask "
                  "datasets/<session>/<set>/geometry.json points at)",
                  flush=True)
    elif fg and fg.get("rect"):
        ctx.foreground = tuple(float(v) for v in fg["rect"])
        if not fg_rect_touches_border(ctx.foreground):
            raise ValueError(
                f"geometry: foreground rect {ctx.foreground} touches no "
                "frame border — a terrestrial obstruction enters from an "
                "edge, and the foreground is EXCLUDED from the sky-statistics "
                "scope, so an interior rect would carve sky out of that "
                f"scope. Fix {cfgp}.")
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


# --- geometry helpers ----------------------------------------------------------

def fg_rect_touches_border(rect, eps=0.002):
    """Border-anchor invariant for a foreground rect (frame fractions
    x0,y0,x1,y1): a terrestrial obstruction is border-anchored by
    construction, and the foreground is excluded from the sky-statistics
    scope — so a floating interior 'foreground' is a config error that
    would silently shrink that scope, never a real treeline."""
    x0, y0, x1, y1 = rect
    return x0 <= eps or y0 <= eps or x1 >= 1.0 - eps or y1 >= 1.0 - eps


def _fg_mask(h, w):
    """Full-res boolean foreground mask from CTX.fg_mask_path (cached).
    True = foreground."""
    key = ("fgmask", h, w)
    if key in CTX._cache:
        return CTX._cache[key]
    m = np.load(CTX.fg_mask_path)["mask"].astype(bool)
    # border-anchor invariant (same reasoning as fg_rect_touches_border;
    # terrestrial masks are border-anchored by construction, so a violating
    # mask is malformed). An empty mask excludes nothing and passes.
    b = max(2, int(round(0.002 * max(m.shape))))
    if m.any() and not (m[:b].any() or m[-b:].any()
                        or m[:, :b].any() or m[:, -b:].any()):
        raise ValueError(
            f"geometry: foreground mask {CTX.fg_mask_path} touches no frame "
            "border — terrestrial masks are border-anchored, and the "
            "foreground is EXCLUDED from the sky-statistics scope; an interior "
            "mask would carve sky out of that scope.")
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
    """True where measurable (the terrestrial foreground excluded — a rect,
    or a mask-file foreground for shapes a rect can't model).
    STATISTICS scope only: a hard edge is fine when selecting samples. A
    RENDERING operator must never multiply a hard mask into a correction —
    it prints a visible seam (measured +1.0/−1.5 counts); the render layer
    re-derives a feathered variant when it lands. CTX.foreground None ->
    all True."""
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
