#!/usr/bin/env python3
"""Blind astrometric solve of a linear stack; optionally inject the WCS.

Usage: solve_field.py <stack.fit> [--inject=<out.fit>] [--json=<wcs.json>]
                     [--ra=<deg> --dec=<deg> [--radius-deg=<N>]] [--central=<frac>]
                     [--field-width-arcmin=<N>] [--scales=<lo>-<hi>]
                     [--max-stars=<N>]

--max-stars sets how many detected stars are handed to the solver (default
200). 200 is ample to MATCH a field — the matcher needs only a handful of
quads — but the same list also constrains the solver's SIP distortion fit,
and an order-3 SIP is 20 free parameters per axis. Brightest-first selection
on a Milky-Way field clusters those stars in the band and leaves the corners
carrying almost no constraint, so the polynomial extrapolates freely exactly
where distortion is largest. Raise this when the SOLUTION's distortion terms
are the product being consumed rather than just its position.

--scales overrides the field-derived index-scale set (the operator's
download/breadth control: a narrow field derives scales whose low end
means multi-GB index downloads; the cached mid scales usually carry the
solution — quads 10-50% of the field width are the prime matching range).

Why this exists: Siril's internal solver cannot match this rig's ultra-wide
trailed-star fields (its online cone caps at ~2.5 deg, and with the local
Gaia catalog + correct center it still fails star matching at 52 and 26 deg
FOV). The astrometry.net engine with field-size-derived index scales solves
the same field from 200 peak-detected stars in seconds. SPCC accepts the
injected TAN-SIP WCS.

Position hint: --ra/--dec [+--radius-deg] localizes the search; when absent,
a header RA/DEC (a driven mount's pointing, standard in astrocam FITS) is
used AUTOMATICALLY — it is unverified metadata, so a header-hinted attempt
that fails falls back to BLIND before giving up (a wrong position hint
cannot mis-solve; it just fails, which makes the fallback safe — a CLI hint
is explicit intent and never falls back). A very wide, distorted field can
defeat the blind match: a fast wide lens warps the outer star quads, and
the true field then never surfaces above the all-sky false-match noise. Two
overrides for that case (a wide-field Milky-Way frame at 50 mm/41 deg
needed both): the position hint above, and --central=<frac> restricts
detection to the low-distortion central fraction of the frame (|dx|,|dy| <
frac x size) so the quads it forms actually match a TAN projection.

Index scales load CACHED-FIRST: the field-derived set splits into scales
whose index series are fully cached vs those needing download, and the
cached tier is attempted first (a narrow field's derived set reaches the
multi-GB low scales, while the cached mid scales — quads ~10-50% of the
field — usually carry the solution). Only when every cached attempt fails
does the run extend to the download tier, saying so. --scales bypasses the
split (an explicit set, attempted as-is).

Star detection (--detect=sep, the default): SExtractor's own core via the
`sep` package — official extraction, shape-blind so trailed sources feed
the matcher (20 sigma over the SExtractor background model, flux-ranked,
25 px de-crowding, brightest 200). --detect=peaks is the in-house
peak-centroid fallback, pending removal (BACKLOG register). Solve runs in
FITS pixel convention (1-based, bottom-up rows) so the WCS can be written
straight into the file.

Runs inside a private venv (~/.local/share/astrometry-venv) holding the
`astrometry` + `sep` pip packages (bundled astrometry.net engine +
SExtractor core; index files auto-download to the venv dir on first use).
Bootstraps itself: run with plain python3, it creates the venv and
re-execs.
"""
import json
import os
import subprocess
import sys

# scripts/lib holds the shared lib (astrometrics); locate it by
# walking up from this file so one bootstrap works at any nesting depth.
_libdir = os.path.dirname(os.path.abspath(__file__))
while _libdir != os.path.dirname(_libdir):
    if os.path.isdir(os.path.join(_libdir, "lib")):
        sys.path.insert(0, os.path.join(_libdir, "lib"))
        break
    _libdir = os.path.dirname(_libdir)

VENV = os.path.expanduser("~/.local/share/astrometry-venv")
CACHE = os.path.join(VENV, "index-cache")


def bootstrap():
    py = os.path.join(VENV, "bin", "python")
    # compare sys.prefix, not executable realpaths: the venv python is a
    # symlink to the system python, so realpath() says "already inside"
    # while running OUTSIDE the venv and the astrometry import then fails
    if os.path.realpath(sys.prefix) != os.path.realpath(VENV):
        if not os.path.exists(py):
            print(f"[solve_field] creating venv {VENV} + installing "
                  "astrometry/sep/astropy/numpy/scipy (one-time)")
            subprocess.run([sys.executable, "-m", "venv", VENV], check=True)
            subprocess.run([py, "-m", "pip", "install", "--quiet",
                            "astrometry", "sep", "astropy", "numpy", "scipy"],
                           check=True)
        else:
            # bring an older venv up to date with the current defaults
            for pkg in ("sep", "astropy"):
                if subprocess.run([py, "-c", f"import {pkg}"],
                                  capture_output=True).returncode != 0:
                    subprocess.run([py, "-m", "pip", "install", "--quiet", pkg],
                                   check=True)
        os.execv(py, [py] + sys.argv)


def detect_stars_sep(path, central=None, max_stars=200):
    """Official extraction: SExtractor's core (`sep`) — detection,
    deblending and windowed centroids are the tool's own measurement; this
    function only ranks, de-crowds and converts to FITS convention (the
    same post-processing the peaks fallback applies to its candidates)."""
    import astrometrics as am
    import numpy as np
    import sep

    data, _ = am.read_fits(path)
    g = np.ascontiguousarray(
        data[min(1, data.shape[0] - 1)].astype(np.float32))
    h, w = g.shape
    sep.set_extract_pixstack(2_000_000)
    bkg = sep.Background(g)
    obj = sep.extract(g - bkg.back(), thresh=20.0, err=bkg.globalrms)
    obj = np.sort(obj, order="flux")[::-1]
    keep_mask = None
    if am.CTX.foreground is not None:
        from scipy.ndimage import binary_erosion
        keep_mask = binary_erosion(am.branch_mask(h, w), np.ones((49, 49)))
    taken = np.zeros((h // 25 + 2, w // 25 + 2), bool)
    stars = []
    for o in obj:
        x0, y0 = float(o["x"]), float(o["y"])
        if central is not None and (abs(x0 - w / 2) > central * w
                                    or abs(y0 - h / 2) > central * h):
            continue
        if keep_mask is not None and not keep_mask[
                min(h - 1, max(0, int(y0))), min(w - 1, max(0, int(x0)))]:
            continue
        cy, cx = int(y0) // 25, int(x0) // 25
        if taken[max(0, cy - 1):cy + 2, max(0, cx - 1):cx + 2].any():
            continue
        taken[cy, cx] = True
        # FITS convention: 1-based, bottom-up rows
        stars.append((x0 + 1.0, h - y0))
        if len(stars) >= max_stars:
            break
    return stars, h, w


def detect_stars(path, central=None, max_stars=200):
    import astrometrics as am
    import numpy as np
    from scipy.ndimage import maximum_filter

    data, _ = am.read_fits(path)
    g = data[min(1, data.shape[0] - 1)].astype(np.float32)
    h, w = g.shape
    bs = 128
    gy, gx = h // bs, w // bs
    bg = np.median(g[:gy * bs, :gx * bs].reshape(gy, bs, gx, bs), axis=(1, 3))
    d = g[:gy * bs, :gx * bs] - np.repeat(np.repeat(bg, bs, 0), bs, 1)
    sig = 1.4826 * np.median(np.abs(d - np.median(d)))
    mx = maximum_filter(d, size=9)
    cand = (d == mx) & (d > 20 * sig)
    # exclude the configured foreground (+ a margin for its glow/smear
    # halo): treeline tips and glow edges detect as bright "peaks" and
    # poison the matcher — a treed field solves only with them excluded
    if am.CTX.foreground is not None:
        keep = am.branch_mask(h, w)[:gy * bs, :gx * bs]
        from scipy.ndimage import binary_erosion
        keep = binary_erosion(keep, np.ones((49, 49)))
        cand &= keep
    ys0, xs0 = np.nonzero(cand)
    vals = d[ys0, xs0]
    # `central` shrinks the pool a lot (frac^2 of the area), so widen the
    # candidate cut so the quota still fills from the low-distortion centre
    order = np.argsort(vals)[::-1][:max(6000 if central else 1200,
                                        6 * max_stars)]
    taken = np.zeros((h // 25 + 2, w // 25 + 2), bool)
    stars = []
    for k in order:
        y0, x0 = ys0[k], xs0[k]
        if central is not None and (abs(x0 - w / 2) > central * w
                                    or abs(y0 - h / 2) > central * h):
            continue                          # low-distortion centre only
        cy, cx = y0 // 25, x0 // 25
        if taken[max(0, cy - 1):cy + 2, max(0, cx - 1):cx + 2].any():
            continue
        taken[cy, cx] = True
        # clamp the centroid window to the array on BOTH sides: a peak
        # within 4 px of an edge otherwise clips the data window while
        # mgrid keeps the full 9x9 — shape-mismatch crash
        dy0, dy1 = max(0, y0 - 4), min(d.shape[0], y0 + 5)
        dx0, dx1 = max(0, x0 - 4), min(d.shape[1], x0 + 5)
        win = d[dy0:dy1, dx0:dx1].clip(0)
        wy, wx = np.mgrid[dy0:dy1, dx0:dx1]
        s = win.sum()
        # FITS convention: 1-based, bottom-up rows
        stars.append((float((win * wx).sum() / s + 1.0),
                      float(h - (win * wy).sum() / s)))
        if len(stars) >= max_stars:
            break
    return stars, h, w


def scale_hint(path, width_arcmin=None):
    """Pixel-scale hint (arcsec/px) from the FITS header (siril propagates
    FOCALLEN + XPIXSZ from EXIF), or from an explicit --field-width-arcmin.
    A hard-coded scale range fits only one rig/focal — 26-40"/px missed a
    24mm field (~44-51"/px), which could never solve. Returns (lo, hi) or
    None (blind)."""
    from astropy.io import fits
    try:
        hdr = fits.getheader(path)
        if width_arcmin is not None:
            s = width_arcmin * 60.0 / float(hdr["NAXIS1"])
        else:
            # center scale, arcsec/px
            s = 206.265 * float(hdr["XPIXSZ"]) / float(hdr["FOCALLEN"])
        # wide envelope: wide-angle projection + integer-mm EXIF wobble
        return (0.6 * s, 1.5 * s)
    except (KeyError, ValueError, OSError):
        return None


# astrometry.net 42xx index scale -> (lo, hi) skymark/quad diameter, arcmin.
# Load index scales whose quad size spans ~7-100% of the field width. The
# low bound sits below the textbook 10% because a wide, star-rich blind
# field matches on quads well under 10% of the full frame (a wide field's
# solution can sit near ~6% of the width, and excluding it gives no
# solution). 0.07*W admits those low scales while still covering the higher
# scales a narrow telescope field needs. A fixed set
# fits only one focal length; loading dense low scales on a wide field just
# grinds — so the window is bounded on BOTH ends.
_SCALE_ARCMIN = {
    0: (2.0, 2.8), 1: (2.8, 4.0), 2: (4.0, 5.6), 3: (5.6, 8.0),
    4: (8.0, 11.0), 5: (11.0, 16.0), 6: (16.0, 22.0), 7: (22.0, 30.0),
    8: (30.0, 42.0), 9: (42.0, 60.0), 10: (60.0, 85.0), 11: (85.0, 120.0),
    12: (120.0, 170.0), 13: (170.0, 240.0), 14: (240.0, 340.0),
    15: (340.0, 480.0), 16: (480.0, 680.0), 17: (680.0, 1000.0),
    18: (1000.0, 1400.0), 19: (1400.0, 2000.0)}
_SCALE_FALLBACK = {13, 14, 15, 16, 17, 18, 19}

# 4200-series tile counts per scale (astrometry.net's healpix split):
# scales 0-4 ship 48 tiles (index-42XX-00..47), 5-7 ship 12, 8+ one file.
# A scale counts as CACHED only when its series is COMPLETE — the solver's
# index_files() silently completes a partial series, i.e. downloads.
_SCALE_TILES = {**{s: 48 for s in range(0, 5)},
                **{s: 12 for s in range(5, 8)},
                **{s: 1 for s in range(8, 20)}}


def scale_cached(s):
    import glob
    d = os.path.join(CACHE, "4200")
    if _SCALE_TILES[s] == 1:
        return os.path.exists(os.path.join(d, f"index-42{s:02d}.fits"))
    return len(glob.glob(os.path.join(d, f"index-42{s:02d}-*.fits"))) \
        >= _SCALE_TILES[s]


def scale_set(path, width_arcmin=None):
    """Index scales to load, derived from the field width (arcsec/px x
    NAXIS1, or an explicit --field-width-arcmin) so any focal length can
    solve. A ~55 deg wide-lens field -> {13..19}; a ~4 deg (500 mm scope)
    field -> {6..14}, which a fixed set could not. When the header
    lacks FOCALLEN/XPIXSZ and no width is given, the WIDE-FIELD scales
    are all that can be loaded (loading every scale grinds) — that
    fallback cannot solve a narrow field, so it warns loudly and names
    the override."""
    from astropy.io import fits
    w_arcmin = width_arcmin
    if w_arcmin is None:
        try:
            hdr = fits.getheader(path)
            w_arcmin = (206.265 * float(hdr["XPIXSZ"]) / float(hdr["FOCALLEN"])
                        * float(hdr["NAXIS1"]) / 60.0)
        except (KeyError, ValueError, OSError):
            print("[solve_field] WARNING: header has no FOCALLEN/XPIXSZ and "
                  "no --field-width-arcmin given — falling back to the "
                  f"WIDE-FIELD index scales {sorted(_SCALE_FALLBACK)} "
                  "(~3-33 deg quads). A narrow (telescope) field CANNOT "
                  "solve on these; pass --field-width-arcmin=<true field "
                  "width> to load the right scales.")
            return set(_SCALE_FALLBACK)
    lo, hi = 0.07 * w_arcmin, 1.0 * w_arcmin      # quads ~7-100% of the field
    sel = {s for s, (a, b) in _SCALE_ARCMIN.items() if b >= lo and a <= hi}
    return sel or set(_SCALE_FALLBACK)


def solve(stars, hint=None, scales=None, pos=None, required=True):
    import astrometry
    scales = set(scales) if scales else set(_SCALE_FALLBACK)
    solver = astrometry.Solver(
        astrometry.series_4200.index_files(
            cache_directory=CACHE, scales=scales))
    print(f"[solve_field] index scales {sorted(scales)} | scale hint: "
          + (f"{hint[0]:.1f}-{hint[1]:.1f} arcsec/px" if hint else "none (blind)")
          + (f" | position hint RA {pos[0]:.1f} Dec {pos[1]:+.1f} r{pos[2]:g} deg"
             if pos else ""))
    sol = solver.solve(
        stars=stars,
        size_hint=(astrometry.SizeHint(hint[0], hint[1]) if hint else None),
        position_hint=(astrometry.PositionHint(
            ra_deg=pos[0], dec_deg=pos[1], radius_deg=pos[2]) if pos else None),
        solution_parameters=astrometry.SolutionParameters(
            sip_order=3,
            # Stop at the first astronomically-confident match instead of
            # grinding every quad of every loaded scale. Field-derived
            # scale sets can be large (dense low scales for narrow fields),
            # and CONTINUE-to-exhaustion makes even a 55-deg field
            # minutes-slow with dense low scales in the set. logodds 100 = odds
            # ~1e43, far above both the ~20.7 default solve floor and the
            # 115-373 these blind solves reach — never stops on a spurious
            # match. The solver hands the callback the running list of match
            # log-odds, so test the best (max) against the threshold.
            logodds_callback=lambda los: (
                astrometry.Action.STOP if max(los) >= 100.0
                else astrometry.Action.CONTINUE)))
    if not sol.has_match():
        if required:
            sys.exit("solve_field: NO SOLUTION")
        return None
    return sol.best_match()


def inject(src, dst, wcs, logodds):
    """Write a WCS-injected copy via astropy: the solver's WCS cards replace any
    existing ones; every other header card and the exact pixel data are preserved
    (do_not_scale_image_data keeps BITPIX/BZERO/BSCALE untouched, so the linear
    stack round-trips unchanged for SPCC)."""
    from astropy.io import fits
    with fits.open(src, do_not_scale_image_data=True) as hdul:
        hdr = hdul[0].header
        for k in wcs:                        # drop any prior value we replace
            hdr.remove(k, ignore_missing=True, remove_all=True)
        hdr.add_comment("WCS injected by solve_field.py "
                        f"(astrometry.net, logodds {logodds:.0f})")
        for k, (v, com) in wcs.items():
            hdr[k] = (v.decode() if isinstance(v, bytes) else v, com)
        hdul.writeto(dst, overwrite=True)


def main():
    bootstrap()
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    opts = dict(a[2:].split("=", 1) for a in sys.argv[1:] if a.startswith("--"))
    if not args:
        sys.exit(__doc__)
    src = args[0]
    if "session" in opts and "set" in opts:
        import astrometrics as am
        am.configure(opts["session"], opts["set"], quiet=True)
    central = float(opts["central"]) if "central" in opts else None
    max_stars = int(opts.get("max-stars", 200))
    width_arcmin = (float(opts["field-width-arcmin"])
                    if "field-width-arcmin" in opts else None)
    pos, pos_src = None, "none"
    if "ra" in opts and "dec" in opts:
        pos = (float(opts["ra"]), float(opts["dec"]),
               float(opts.get("radius-deg", 15.0)))
        pos_src = "cli"
    else:
        # a driven mount's pointing rides in astrocam FITS headers — an
        # UNVERIFIED hint (it cannot mis-solve, only fail), so a
        # header-hinted failure falls back to blind in the attempt loop
        try:
            from astropy.io import fits as _f
            _h = _f.getheader(src)
            if "RA" in _h and "DEC" in _h:
                pos = (float(_h["RA"]), float(_h["DEC"]),
                       float(opts.get("radius-deg", 15.0)))
                pos_src = "header"
                print(f"[solve_field] position hint from header: RA "
                      f"{pos[0]:.2f} Dec {pos[1]:+.2f} r{pos[2]:g} deg "
                      "(unverified — falls back to blind on failure)")
        except (OSError, ValueError, TypeError):
            pass
    detector = opts.get("detect", "sep")
    if detector not in ("sep", "peaks"):
        sys.exit(f"solve_field: unknown --detect={detector} (sep|peaks)")
    fn = detect_stars_sep if detector == "sep" else detect_stars
    stars, h, w = fn(src, central=central, max_stars=max_stars)
    print(f"[solve_field] {len(stars)} stars via "
          + ("sep (SExtractor core)" if detector == "sep"
             else "in-house peak centroids (fallback)")
          + (f" (central {central:g} of frame)" if central else ""))
    hint = scale_hint(src, width_arcmin)
    if "scales" in opts:
        lo, hi = (int(v) for v in opts["scales"].split("-", 1))
        scales = set(range(lo, hi + 1))
        print(f"[solve_field] index scales OVERRIDDEN to {lo}-{hi} "
              "(--scales; field-derived set not used)")
    else:
        scales = scale_set(src, width_arcmin)
    if "scales" in opts:
        tiers = [("override", scales)]
    else:
        cached = {s for s in scales if scale_cached(s)}
        uncached = sorted(scales - cached)
        if cached and uncached:
            tiers = [("cached", cached), (f"download {uncached}", scales)]
        elif cached:
            tiers = [("cached", cached)]
        else:
            tiers = [(f"download {uncached} (nothing cached)", scales)]
    attempts = []
    for tlabel, tset in tiers:
        attempts.append((tlabel, tset, pos))
        if pos is not None and pos_src == "header":
            attempts.append((f"{tlabel} + blind", tset, None))
    m = winning = None
    for alabel, aset, apos in attempts:
        print(f"[solve_field] attempt [{alabel}]")
        m = solve(stars, hint=hint, scales=aset, pos=apos, required=False)
        if m is not None:
            winning = (alabel, sorted(aset), apos)
            break
    if m is None:
        sys.exit("solve_field: NO SOLUTION")
    print(f"[solve_field] SOLVED: RA {m.center_ra_deg:.3f} "
          f"Dec {m.center_dec_deg:+.3f} scale "
          f"{m.scale_arcsec_per_pixel:.2f} arcsec/px logodds {m.logodds:.0f}")
    # Parity: det(CD) < 0 = the stored image displays SKY-TRUE (east
    # counter-clockwise from north); det > 0 = mirrored vs the sky. The
    # classic cause is top-down camera FITS carrying no ROWORDER keyword
    # ingested under the bottom-up default — self-consistent all the way
    # through, so only the solve can see it. Reported every solve.
    cd = {k: v[0] for k, v in m.wcs_fields.items()
          if k in ("CD1_1", "CD1_2", "CD2_1", "CD2_2")}
    det = (cd.get("CD1_1", 0) * cd.get("CD2_2", 0)
           - cd.get("CD1_2", 0) * cd.get("CD2_1", 0))
    par = "sky-true" if det < 0 else "MIRRORED vs sky"
    print(f"[solve_field] parity: det(CD) {det:+.2e} -> displayed image "
          f"is {par}")
    wcs = {k: [v[0] if not isinstance(v[0], bytes) else v[0].decode(), v[1]]
           for k, v in m.wcs_fields.items()}
    if "json" in opts:
        json.dump(wcs, open(opts["json"], "w"), indent=1)
        print(f"[solve_field] wrote {opts['json']}")
    if "inject" in opts:
        inject(src, opts["inject"], wcs, m.logodds)
        print(f"[solve_field] wrote {opts['inject']} (WCS-injected copy)")
    # durable per-solve record next to the session's other capture files
    # (spcc_run writes work/spcc_<set>.json; a wrong solve needs the same
    # after-the-fact trail: what was detected, hinted, loaded, and found)
    stem = os.path.splitext(os.path.basename(src))[0]
    wdir = os.path.normpath(os.path.join(os.path.dirname(src), "..", "work"))
    if not os.path.isdir(wdir):
        wdir = os.path.dirname(src) or "."
    rec = {"input": src, "detector": detector,
           "n_stars_detected": len(stars),
           "central": central,
           "position_hint": winning[2], "position_hint_source": pos_src,
           "attempt": winning[0],
           "field_width_arcmin_arg": width_arcmin,
           "scale_hint_arcsec_px": list(hint) if hint else None,
           "index_scales": sorted(scales), "scales_solved": winning[1],
           "ra_deg": m.center_ra_deg, "dec_deg": m.center_dec_deg,
           "scale_arcsec_px": m.scale_arcsec_per_pixel,
           "logodds": m.logodds,
           "parity": par, "cd_det": det,
           "injected": opts.get("inject")}
    p_rec = os.path.join(wdir, f"solve_{stem}.json")
    json.dump(rec, open(p_rec, "w"), indent=1)
    print(f"[solve_field] record -> {p_rec}")
    # tracked home: when the caller names the dataset, the record also
    # lands in datasets/<session>/<set>/qa_work/ (the versioned measure);
    # the results-side copy stays the UI's product sidecar, regenerated
    # with every solve
    if "session" in opts and "set" in opts:
        repo = os.path.dirname(os.path.dirname(
            os.path.dirname(os.path.abspath(__file__))))
        qa = os.path.join(repo, "datasets", os.path.basename(
            os.path.normpath(opts["session"])), opts["set"], "qa_work")
        os.makedirs(qa, exist_ok=True)
        p_qa = os.path.join(qa, f"solve_{stem}.json")
        json.dump(rec, open(p_qa, "w"), indent=1)
        print(f"[solve_field] tracked record -> {p_qa}")


if __name__ == "__main__":
    main()
