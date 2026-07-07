#!/usr/bin/env python3
"""Blind astrometric solve of a linear stack; optionally inject the WCS.

Usage: solve_field.py <stack.fit> [--inject=<out.fit>] [--json=<wcs.json>]

Why this exists: Siril 1.4's internal solver cannot match this rig's
ultra-wide trailed-star fields (measured 2026-07-06: online cone capped at
2.5 deg; with the local Gaia astro catalog + correct center it still fails
star matching at 52 and 26 deg FOV). The astrometry.net engine with
Tycho-2 wide-field indexes (4213-4219) solves the same field from 200
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


def solve(stars, hint=None):
    import astrometry
    solver = astrometry.Solver(
        astrometry.series_4200.index_files(
            cache_directory=CACHE, scales={13, 14, 15, 16, 17, 18, 19}))
    print(f"[solve_field] scale hint: "
          + (f"{hint[0]:.1f}-{hint[1]:.1f} arcsec/px" if hint else
             "none (blind)"))
    sol = solver.solve(
        stars=stars,
        size_hint=(astrometry.SizeHint(hint[0], hint[1]) if hint else None),
        position_hint=None,
        solution_parameters=astrometry.SolutionParameters(
            sip_order=3,
            logodds_callback=lambda lo: astrometry.Action.CONTINUE))
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
    m = solve(stars, hint=scale_hint(src))
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
