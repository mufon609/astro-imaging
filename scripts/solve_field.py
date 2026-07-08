#!/usr/bin/env python3
"""Blind astrometric solve of a linear stack; optionally inject the WCS.

Usage: solve_field.py <stack.fit> [--inject=<out.fit>] [--json=<wcs.json>]

Why this exists: Siril 1.4's internal solver cannot match this rig's
ultra-wide trailed-star fields (measured 2026-07-06: online cone capped at
2.5 deg; with the local Gaia astro catalog + correct center it still fails
star matching at 52 and 26 deg FOV). The astrometry.net engine with
field-size-derived index scales solves the same field from 200
peak-detected stars in seconds (set-03: RA 312.774 Dec +48.156, 32.78
arcsec/px, logodds 361 — Cygnus, not the "Big Dipper" the session notes
originally claimed). SPCC accepts the injected TAN-SIP WCS.

Star detection: coarse background-subtracted local maxima (trail-robust
peak centroids — component/blob centroids and Siril's PSF-fit detection
both fail to feed the matcher on this data; 20 sigma, 25 px min
separation, brightest 200). Solve runs in FITS pixel convention (1-based,
bottom-up rows) so the WCS can be written straight into the file.

Runs inside a private venv (~/.local/share/astrometry-venv) holding the
`astrometry` pip package (bundled astrometry.net engine; index files
auto-download to the venv dir on first use). Bootstraps itself: run with
plain python3, it creates the venv and re-execs.
"""
import json
import os
import subprocess
import sys

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
                  "astrometry/numpy/scipy (one-time)")
            subprocess.run([sys.executable, "-m", "venv", VENV], check=True)
            subprocess.run([py, "-m", "pip", "install", "--quiet",
                            "astrometry", "numpy", "scipy"], check=True)
        os.execv(py, [py] + sys.argv)


def detect_stars(path):
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
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
    order = np.argsort(vals)[::-1][:1200]
    taken = np.zeros((h // 25 + 2, w // 25 + 2), bool)
    stars = []
    for k in order:
        cy, cx = ys0[k] // 25, xs0[k] // 25
        if taken[max(0, cy - 1):cy + 2, max(0, cx - 1):cx + 2].any():
            continue
        taken[cy, cx] = True
        y0, x0 = ys0[k], xs0[k]
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
        if len(stars) >= 200:
            break
    return stars, h, w


def scale_hint(path):
    """Pixel-scale hint (arcsec/px) from the FITS header (siril propagates
    FOCALLEN + XPIXSZ from EXIF). A hard-coded scale range fits only one
    rig/focal — 26-40"/px missed a 24mm field (~44-51"/px), which could
    never solve. Returns (lo, hi) or None (blind)."""
    import re
    try:
        raw = open(path, "rb").read(2880 * 8).decode("ascii", "replace")
        fl = float(re.search(r"FOCALLEN\s*=\s*([0-9.Ee+-]+)", raw).group(1))
        px = float(re.search(r"XPIXSZ\s*=\s*([0-9.Ee+-]+)", raw).group(1))
        s = 206.265 * px / fl   # center scale, arcsec/px
        # wide envelope: wide-angle projection + integer-mm EXIF wobble
        return (0.6 * s, 1.5 * s)
    except (AttributeError, ValueError, OSError):
        return None


# astrometry.net 42xx index scale -> (lo, hi) skymark/quad diameter, arcmin.
# Load index scales whose quad size spans ~7-100% of the field width. The
# low bound sits below the textbook 10% because a wide, star-rich blind
# field matches on quads well under 10% of the full frame — set-03's
# solution is at scale 13 (~6%), and dropping it gives NO SOLUTION
# (measured). 0.07*W reproduces the proven {13..19} for set-03 while still
# admitting the lower scales a narrow telescope field needs. A fixed set
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


def scale_set(path):
    """Index scales to load, derived from the field width (arcsec/px x
    NAXIS1) so any focal length can solve. Falls back to the wide-field
    set when the header lacks FOCALLEN/XPIXSZ. set-03 (55 deg) -> {13..19}
    (the proven set); a 500 mm field (~4 deg) -> {6..14}, which the fixed
    set could not."""
    import re
    try:
        raw = open(path, "rb").read(2880 * 8).decode("ascii", "replace")
        fl = float(re.search(r"FOCALLEN\s*=\s*([0-9.Ee+-]+)", raw).group(1))
        px = float(re.search(r"XPIXSZ\s*=\s*([0-9.Ee+-]+)", raw).group(1))
        nx = float(re.search(r"NAXIS1\s*=\s*([0-9]+)", raw).group(1))
    except (AttributeError, ValueError, OSError):
        return set(_SCALE_FALLBACK)
    w_arcmin = 206.265 * px / fl * nx / 60.0      # field width, arcmin
    lo, hi = 0.07 * w_arcmin, 1.0 * w_arcmin      # quads ~7-100% of the field
    sel = {s for s, (a, b) in _SCALE_ARCMIN.items() if b >= lo and a <= hi}
    return sel or set(_SCALE_FALLBACK)


def solve(stars, hint=None, scales=None):
    import astrometry
    scales = set(scales) if scales else set(_SCALE_FALLBACK)
    solver = astrometry.Solver(
        astrometry.series_4200.index_files(
            cache_directory=CACHE, scales=scales))
    print(f"[solve_field] index scales {sorted(scales)} | scale hint: "
          + (f"{hint[0]:.1f}-{hint[1]:.1f} arcsec/px" if hint else
             "none (blind)"))
    sol = solver.solve(
        stars=stars,
        size_hint=(astrometry.SizeHint(hint[0], hint[1]) if hint else None),
        position_hint=None,
        solution_parameters=astrometry.SolutionParameters(
            sip_order=3,
            # Stop at the first astronomically-confident match instead of
            # grinding every quad of every loaded scale. Field-derived
            # scale sets can be large (dense low scales for narrow fields),
            # and CONTINUE-to-exhaustion made even set-03 minutes-slow once
            # scale 12 was added. logodds 100 = odds ~1e43, far above both
            # the ~20.7 default solve floor and the 115-373 these blind
            # solves actually reach — so it never stops on a spurious match.
            logodds_callback=lambda lo: (
                astrometry.Action.STOP if lo >= 100.0
                else astrometry.Action.CONTINUE)))
    if not sol.has_match():
        sys.exit("solve_field: NO SOLUTION")
    return sol.best_match()


def fmt_card(key, val, comment):
    if isinstance(val, str):
        body = f"{key:<8s}= '{val:<8s}'"
    elif isinstance(val, bool):
        body = f"{key:<8s}= {'T' if val else 'F':>20s}"
    elif isinstance(val, int):
        body = f"{key:<8s}= {val:>20d}"
    else:
        body = f"{key:<8s}= {val:>20.14G}"
    if comment:
        body += f" / {comment}"
    return body[:80].ljust(80)


def inject(src, dst, wcs, logodds):
    raw = open(src, "rb").read()
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
    wkeys = set(wcs.keys())
    kept = [c for c in cards if c[:8].strip() not in wkeys]
    new = kept + [f"COMMENT WCS injected by solve_field.py "
                  f"(astrometry.net, logodds {logodds:.0f})".ljust(80)]
    for k, (v, com) in wcs.items():
        new.append(fmt_card(k, v, com))
    new.append("END".ljust(80))
    hdr = "".join(new)
    hdr += " " * ((-len(hdr)) % 2880)
    with open(dst, "wb") as f:
        f.write(hdr.encode("ascii"))
        f.write(raw[off:])


def main():
    bootstrap()
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    opts = dict(a[2:].split("=", 1) for a in sys.argv[1:] if a.startswith("--"))
    if not args:
        sys.exit(__doc__)
    src = args[0]
    if "session" in opts and "set" in opts:
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        import astrometrics as am
        am.configure(opts["session"], opts["set"], quiet=True)
    stars, h, w = detect_stars(src)
    print(f"[solve_field] {len(stars)} peak-detected stars")
    m = solve(stars, hint=scale_hint(src), scales=scale_set(src))
    print(f"[solve_field] SOLVED: RA {m.center_ra_deg:.3f} "
          f"Dec {m.center_dec_deg:+.3f} scale "
          f"{m.scale_arcsec_per_pixel:.2f} arcsec/px logodds {m.logodds:.0f}")
    wcs = {k: [v[0] if not isinstance(v[0], bytes) else v[0].decode(), v[1]]
           for k, v in m.wcs_fields.items()}
    if "json" in opts:
        json.dump(wcs, open(opts["json"], "w"), indent=1)
        print(f"[solve_field] wrote {opts['json']}")
    if "inject" in opts:
        inject(src, opts["inject"], wcs, m.logodds)
        print(f"[solve_field] wrote {opts['inject']} (WCS-injected copy)")


if __name__ == "__main__":
    main()
