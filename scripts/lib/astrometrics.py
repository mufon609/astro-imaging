#!/usr/bin/env python3
"""Shared I/O + per-set geometry helpers for the orchestration layer.

Pure numpy/scipy/PIL, EXAMINE/orchestrate only: FITS and display-image readers,
the FITS/PNG writers finals are packaged with (incl. the sRGB colorimetry
tags), and the per-set foreground geometry the tools are pointed around. It
does NOT grade or transform the deliverable's pixels — every pixel
measurement and every pixel operation is sourced from an industry tool
(Siril / GraXpert / astrometry.net / …), never hand-rolled here.

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
    # panels match the JPEG previews and the branch mask hits the right
    # corner regardless of input type.
    return data.reshape(nc, ny, nx)[:, ::-1, :].copy(), hdr


def fits_dims(path):
    """(width, height) from the header only — no data read."""
    import re
    raw = open(path, "rb").read(2880 * 4).decode("ascii", "replace")
    return (int(re.search(r"NAXIS1\s*=\s*(\d+)", raw).group(1)),
            int(re.search(r"NAXIS2\s*=\s*(\d+)", raw).group(1)))


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


def load_linear(path):
    """Processing-input loader: FITS ONLY. Display-referred / lossy files
    (jpg, png) exist solely as QA, gate and judgment surfaces — a
    processing stage fed one would silently work on quantized or
    chroma-subsampled data, so this guard refuses instead."""
    data, kind = load_image(path)
    if kind != "fits":
        sys.exit(f"astrometrics: {path} is not FITS — processing stages "
                 "take linear FITS only (jpg/png are QA/judgment "
                 "surfaces, never inputs)")
    return data


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


SRGB_ICC = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                        "srgb.icc")
# PNG colorimetry signal chunks (sRGB perceptual + the spec's companion
# gAMA/cHRM fallbacks for non-sRGB-aware decoders): the render's colour
# math (LCh operators, Luv luminance) treats display RGB as
# sRGB-companded, so finals DECLARE that instead of leaving viewers to
# assume it. Fixed bytes — deterministic by construction.
PNG_SRGB_CHUNKS = (
    (b"sRGB", b"\x00"),
    (b"gAMA", (45455).to_bytes(4, "big")),
    (b"cHRM", b"".join(v.to_bytes(4, "big") for v in
                       (31270, 32900, 64000, 33000,
                        30000, 60000, 15000, 6000))),
)


def srgb_icc():
    """The vendored sRGB profile finals embed (lcms matrix profile with
    the creation timestamp and profile ID zeroed, so embedding stays
    byte-deterministic across machines and runs)."""
    with open(SRGB_ICC, "rb") as f:
        return f.read()


def png_srgb_info():
    """PngInfo carrying PNG_SRGB_CHUNKS for PIL PNG saves (written before
    IDAT, per spec)."""
    from PIL.PngImagePlugin import PngInfo
    pi = PngInfo()
    for tag, payload in PNG_SRGB_CHUNKS:
        pi.add(tag, payload)
    return pi


def write_png16(path, arr16):
    """Write a 16-bit RGB PNG (color type 2, bit depth 16) from a uint16
    (H, W, 3) array. Pure zlib/struct — Pillow cannot write 48-bit RGB
    PNGs, and the render is computed in float: an 8-bit final quantizes
    to 256 levels, this keeps 65536 (visually indistinguishable from the
    float render). Carries the same sRGB colorimetry chunks as the PIL
    finals."""
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
        for tag, payload in PNG_SRGB_CHUNKS:
            f.write(chunk(tag, payload))
        f.write(chunk(b"IDAT", zlib.compress(body.tobytes(), 6)))
        f.write(chunk(b"IEND", b""))


def read_fits_planes(path):
    """Raw float32 FITS read, FILE order (no orientation flip): returns
    (header cards, planes (C,H,W) float32, hdr dict). For processing
    stages that write their result back out — pair with
    write_fits_planes so the header cards and the pixel order round-trip
    untouched (read_fits flips to display orientation and is for
    measurement)."""
    raw = open(path, "rb").read()
    cards, off, end = [], 0, False
    while not end:
        block = raw[off:off + 2880]
        for i in range(0, 2880, 80):
            c = block[i:i + 80].decode("ascii")
            if c.startswith("END"):
                end = True
                break
            cards.append(c)
        off += 2880
        if off > len(raw):
            sys.exit(f"astrometrics: no END card in {path}")
    hdr = {c[:8].strip(): c[10:].split("/")[0].strip()
           for c in cards if "=" in c}
    bitpix = int(hdr["BITPIX"])
    if bitpix != -32:
        sys.exit(f"astrometrics: read_fits_planes expects a float32 FITS, "
                 f"got BITPIX {bitpix} in {path}")
    nx, ny = int(hdr["NAXIS1"]), int(hdr["NAXIS2"])
    nc = int(hdr.get("NAXIS3", "1")) if int(hdr["NAXIS"]) == 3 else 1
    planes = np.frombuffer(raw, dtype=">f4", count=nc * ny * nx,
                           offset=off).reshape(nc, ny, nx)
    return cards, planes.astype(np.float32), hdr


def write_fits_planes(path, cards_src, planes):
    """Write float32 planes (C,H,W) in FILE order under the source header
    cards, geometry patched to the array. The card grid is 80-byte cells:
    one oversized card would shift END off its boundary and every reader
    rejects the file, so refuse those loudly."""
    over = [c for c in cards_src if len(c) > 80]
    if over:
        sys.exit(f"astrometrics: header card exceeds 80 bytes "
                 f"({len(over[0])}): {over[0][:60]!r}...")
    nc, ny, nx = planes.shape
    out, seen3 = [], False
    for c in cards_src:
        key = c[:8].strip()
        if key == "NAXIS":
            out.append(f"{'NAXIS':<8s}= {(3 if nc == 3 else 2):>20d}".ljust(80))
        elif key == "NAXIS1":
            out.append(f"{'NAXIS1':<8s}= {nx:>20d}".ljust(80))
        elif key == "NAXIS2":
            out.append(f"{'NAXIS2':<8s}= {ny:>20d}".ljust(80))
        elif key == "NAXIS3":
            if nc > 1:
                out.append(f"{'NAXIS3':<8s}= {nc:>20d}".ljust(80))
                seen3 = True
        else:
            out.append(c)
    if nc > 1 and not seen3:
        for i, c in enumerate(out):
            if c[:8].strip() == "NAXIS2":
                out.insert(i + 1, f"{'NAXIS3':<8s}= {nc:>20d}".ljust(80))
                break
    hdr = "".join(out) + "END".ljust(80)
    hdr += " " * ((-len(hdr)) % 2880)
    body = planes.astype(">f4").tobytes()
    with open(path, "wb") as f:
        f.write(hdr.encode("ascii"))
        f.write(body)
        f.write(b"\x00" * ((-len(body)) % 2880))
