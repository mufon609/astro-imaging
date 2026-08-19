#!/usr/bin/env python3
"""JOINT refit of ptlens (a,b,c) AND the distortion centre, against an absolute
catalogue — the one route lensfun's `<center>` element can serve.

    fit_ptlens_joint.py extract <session>/<set>/<FRAME>.NEF ...   (per frame)
    fit_ptlens_joint.py fit <pairs.json> ...                      (all frames)

WHY IT IS JOINT. ptlens is r_d = r_u·(a·r_u³ + b·r_u² + c·r_u + 1−a−b−c), a
function of radius FROM THE DISTORTION CENTRE alone — which is why it cannot
express a left-right asymmetry, and why the centre is the only door asymmetry
comes through. Moving the centre changes what "radius" means for every pixel,
so the radial curve that best describes the same field changes shape: a,b,c and
(cx,cy) are ONE fit. Fitting them in sequence is measured to LOSE
(docs/dead-ends.md, the <center> entry: 2.589 → 4.235–7.610 px).

WHY AGAINST A CATALOGUE, not between frames. Hugin's d,e stage fits the centre
jointly with per-image yaw/pitch on BETWEEN-FRAME correspondences, where the two
are nearly degenerate — measured to diverge on 4 of 5 sets (d=6.3e6 on
aug06/set-02). Against a fixed catalogue there is ONE global affine per frame
instead, and the centre is identifiable. The catalogue also reaches the frame
CORNER (ρ ≈ 1.8) where cpfind's control points stop at ρ ≈ 1.0–1.5 — the
extrapolation the registry blames for 6–8 px model divergence.

TOOLS. Every pixel and every position is a tool's: `sep` (SExtractor's core)
detects and centroids, astrometry.net solves and supplies the catalogue, and
its own TAN+SIP solution establishes correspondence. This script fits a model to
those numbers and computes no image statistic of its own.

UNITS + CONVENTION, both verified. Radius and centre are normalised by
size/2 = HALF THE IMAGE HEIGHT (2020 px on this body) — from modifier.cpp
(the distortion origin is Width/2 + CenterX·size/2) and independently from the
repo's radius-normalisation probe (a free normalisation landed at 2000 vs 2020).
The fit runs in darktable's IMAGE convention (x right, y DOWN), so cx,cy drop
straight into `install_lens_model.sh --center cx,cy`; sep reports FITS
bottom-up, so y is flipped on the way in.

A FIT IS A CANDIDATE. This one is judged like every other: the residual
displacement field through the production warp first, then star_stations +
seqtilt at the COMBINE and the owner's eyes. Never on its own residual.

REMOVAL CONDITION: retire the joint least squares when hugin/lensfun fit
ptlens + distortion centre jointly against an absolute (catalogue) reference,
or when no OPEN item in BACKLOG `one-sided-band` / `corner-fix-landscape`
still consumes a fitted distortion-centre quantity. Registered in BACKLOG
`removal-conditions` (condition authored by audit — this divergence shipped
with none; RATIFIED by the owner 2026-08-19).
"""
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                "..", "lib"))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                "..", "calibrate"))

R_NORM = 2020.0          # lensfun size/2 for this body; asserted below
MATCH_TOL = 8.0          # px against the tool's own full TAN+SIP solution
HINT = (303.0, 43.0, 25.0)


def extract(fits_path, tag):
    """One frame -> matched (linear-WCS predicted, measured) pairs, image
    convention. Nothing here is an in-house measurement: sep centroids,
    astrometry.net solves and supplies the catalogue."""
    import numpy as np
    from scipy.spatial import cKDTree
    from astropy.io import fits as pyfits
    from astropy.wcs import WCS
    import solve_field as sf

    det_stars, H, W = sf.detect_stars_sep(fits_path, max_stars=8000)
    det = np.array(det_stars, float)
    solve_stars, _, _ = sf.detect_stars_sep(fits_path, max_stars=1500)
    m = sf.solve(solve_stars, hint=sf.scale_hint(fits_path),
                 scales=sf.scale_set(fits_path), pos=HINT)

    hdr = pyfits.Header()
    for k, v in m.wcs_fields.items():
        hdr[k] = v[0] if not isinstance(v[0], bytes) else v[0].decode()
    wcs_full = WCS(hdr, relax=True)
    lin = hdr.copy()
    for k in [k for k in lin if k.startswith(("A_", "B_", "AP_", "BP_"))]:
        del lin[k]
    for k in ("CTYPE1", "CTYPE2"):
        lin[k] = str(lin[k]).replace("-SIP", "")
    wcs_lin = WCS(lin)

    cat = np.array([[s.ra_deg, s.dec_deg] for s in m.stars], float)
    fx, fy = wcs_full.all_world2pix(cat[:, 0], cat[:, 1], 1)
    lx, ly = wcs_lin.all_world2pix(cat[:, 0], cat[:, 1], 1)
    ok = np.isfinite(fx) & np.isfinite(fy) & (fx > 0) & (fx <= W) \
        & (fy > 0) & (fy <= H)
    fx, fy, lx, ly = fx[ok], fy[ok], lx[ok], ly[ok]
    t_det, t_cat = cKDTree(det), cKDTree(np.column_stack([fx, fy]))
    d1, i1 = t_det.query(np.column_stack([fx, fy]), k=1)
    _, i2 = t_cat.query(det, k=1)
    good = (d1 < MATCH_TOL) & (i2[i1] == np.arange(len(fx)))

    # FITS bottom-up -> darktable image convention (y DOWN), so the fitted
    # centre needs no sign guessing at install time.
    return {"tag": tag, "frame": fits_path, "w": W, "h": H,
            "ra": m.center_ra_deg, "dec": m.center_dec_deg,
            "scale_arcsec_px": m.scale_arcsec_per_pixel, "logodds": m.logodds,
            "n": int(good.sum()),
            "lin_x": lx[good].tolist(),
            "lin_y": (H + 1 - ly[good]).tolist(),
            "meas_x": det[i1[good], 0].tolist(),
            "meas_y": (H + 1 - det[i1[good], 1]).tolist()}


def ptlens(p_xy, pa, pb, pc, cx, cy):
    """lensfun's ptlens, applied about (cx,cy). Direction matches
    ModifyCoord_Dist_PTLens: undistorted -> distorted (source), which is the
    direction image correction consumes."""
    import numpy as np
    u = (p_xy[0] - cx) / R_NORM
    v = (p_xy[1] - cy) / R_NORM
    r = np.hypot(u, v)
    f = pa * r ** 3 + pb * r ** 2 + pc * r + (1.0 - pa - pb - pc)
    return cx + R_NORM * u * f, cy + R_NORM * v * f


def fit(frames, free_centre=True, brown=False, clip=None,
        seed=(0.00350093, 0.01453356, 0.00043983)):
    """brown=True adds Brown's tangential pair p1,p2 on top of ptlens — the
    CONTROL that says whether any decentring survives once the per-frame
    nuisance is projective. clip=<px> re-fits after dropping pairs whose first
    -pass residual exceeds it (mismatched stars, not optics)."""
    import numpy as np
    from scipy.optimize import least_squares

    nf = len(frames)
    # PER-FRAME NUISANCE = A HOMOGRAPHY, not an affine. The linear WCS is a
    # gnomonic (TAN) projection about ITS tangent point and rotation; the ideal
    # camera frame the ptlens model lives in is a gnomonic projection about the
    # optical axis. Two gnomonic projections of the same sky differ by a plane
    # projective transform EXACTLY (the same result that makes a homography the
    # right registration class here). Over +-14 deg the projective part reaches
    # ~180 px, so an affine cannot absorb it and the lens terms deform to
    # compensate: measured, an affine nuisance inflated this fit to 14.2/9.2 px
    # RMS against the 3.9/2.4 px it reaches with a homography.
    # Normalised so the parameters are O(1); h33 == 1 by construction.
    h0 = [1., 0., 0., 0., 1., 0., 0., 0.]
    lens0 = list(seed) + ([0.0, 0.0] if free_centre else []) \
        + ([0.0, 0.0] if brown else [])
    x0 = np.concatenate([np.array(lens0), np.tile(h0, nf)])
    nlens = len(lens0)
    S = 3000.0                      # coordinate scale for the projective terms

    def resid(x):
        pa, pb, pc = x[:3]
        cx, cy = (x[3], x[4]) if free_centre else (0.0, 0.0)
        out = []
        for i, fr in enumerate(frames):
            H = x[nlens + 8 * i: nlens + 8 * i + 8]
            lx = np.asarray(fr["lin_x"]) - fr["w"] / 2.0
            ly = np.asarray(fr["lin_y"]) - fr["h"] / 2.0
            cxp = fr["w"] / 2.0 + cx * R_NORM
            cyp = fr["h"] / 2.0 + cy * R_NORM
            den = 1.0 + (H[6] * lx + H[7] * ly) / S
            ix = (H[0] * lx + H[1] * ly + H[2]) / den + fr["w"] / 2.0
            iy = (H[3] * lx + H[4] * ly + H[5]) / den + fr["h"] / 2.0
            px, py = ptlens((ix, iy), pa, pb, pc, cxp, cyp)
            if brown:
                p1, p2 = x[nlens - 2], x[nlens - 1]
                un, vn = (ix - cxp) / R_NORM, (iy - cyp) / R_NORM
                r2 = un ** 2 + vn ** 2
                px = px + R_NORM * (2 * p1 * un * vn + p2 * (r2 + 2 * un ** 2))
                py = py + R_NORM * (p1 * (r2 + 2 * vn ** 2) + 2 * p2 * un * vn)
            out.append(px - np.asarray(fr["meas_x"]))
            out.append(py - np.asarray(fr["meas_y"]))
        return np.concatenate(out)

    sol = least_squares(resid, x0, loss="soft_l1", f_scale=3.0,
                        x_scale="jac", max_nfev=600)
    if clip:
        r = sol.fun
        n = len(r) // 2
        d = np.hypot(r[:n], r[n:])
        k, kept = 0, []
        for fr in frames:
            m = fr["n"]
            keep = d[k:k + m] < clip
            kept.append({**fr, "n": int(keep.sum()),
                         "lin_x": list(np.asarray(fr["lin_x"])[keep]),
                         "lin_y": list(np.asarray(fr["lin_y"])[keep]),
                         "meas_x": list(np.asarray(fr["meas_x"])[keep]),
                         "meas_y": list(np.asarray(fr["meas_y"])[keep])})
            k += m
        frames = kept
        sol = least_squares(resid, sol.x, loss="soft_l1", f_scale=3.0,
                            x_scale="jac", max_nfev=600)
    r = sol.fun
    n = len(r) // 2
    per = []
    k = 0
    for fr in frames:
        m = fr["n"]
        d = np.hypot(r[k:k + m], r[n + k:n + k + m])
        per.append({"tag": fr["tag"], "n": m,
                    "rms_px": round(float(np.sqrt((d ** 2).mean())), 3),
                    "median_px": round(float(np.median(d)), 3)})
        k += m
    d_all = np.hypot(r[:n], r[n:])
    return {"free_centre": free_centre, "brown": brown,
            "p1p2": ([float(sol.x[nlens - 2]), float(sol.x[nlens - 1])]
                     if brown else None),
            "n_dropped_by_clip": int(sum(f["n"] for f in frames)) if clip else 0,
            "ptlens": {"a": float(sol.x[0]), "b": float(sol.x[1]),
                       "c": float(sol.x[2])},
            "center": ({"x": float(sol.x[3]), "y": float(sol.x[4])}
                       if free_centre else {"x": 0.0, "y": 0.0}),
            "center_px": ({"x": round(float(sol.x[3]) * R_NORM, 1),
                           "y": round(float(sol.x[4]) * R_NORM, 1)}
                          if free_centre else {"x": 0.0, "y": 0.0}),
            "rms_px": round(float(np.sqrt((d_all ** 2).mean())), 3),
            "median_px": round(float(np.median(d_all)), 3),
            "n_pairs": int(n), "n_frames": len(frames),
            "per_frame": per, "success": bool(sol.success)}


if __name__ == "__main__":
    mode = sys.argv[1]
    if mode == "extract":
        rec = extract(sys.argv[2], sys.argv[3])
        json.dump(rec, open(sys.argv[4], "w"))
        print(f"{rec['tag']}: {rec['n']} pairs, RA {rec['ra']:.2f} "
              f"Dec {rec['dec']:+.2f} logodds {rec['logodds']:.0f}")
    elif mode == "fit":
        frames = [json.load(open(p)) for p in sys.argv[2:]]
        assert all(f["h"] / 2.0 == R_NORM for f in frames), \
            "R_NORM must be half the image height for this body"
        print(f"{len(frames)} frames, {sum(f['n'] for f in frames)} pairs\n")
        out = {}
        arms = (("centred_control", False, False), ("joint_free_centre", True, False),
                ("centred_plus_brown", False, True))
        for tag, fc, br in arms:
            res = fit(frames, free_centre=fc, brown=br, clip=6.0)
            out[tag] = res
            p, c = res["ptlens"], res["center_px"]
            print(f"{tag:20s} RMS {res['rms_px']:6.3f} px  median "
                  f"{res['median_px']:6.3f}  a={p['a']:+.6f} b={p['b']:+.6f} "
                  f"c={p['c']:+.6f}  centre ({c['x']:+.0f},{c['y']:+.0f}) px")
        print("\nper frame (RMS px):")
        for a, b in zip(out["centred_control"]["per_frame"],
                        out["joint_free_centre"]["per_frame"]):
            print(f"  {a['tag']:26s} n={a['n']:>4}  centred {a['rms_px']:6.3f}"
                  f"  ->  joint {b['rms_px']:6.3f}")
        json.dump(out, open("ptlens_joint_fit.json", "w"), indent=1)
        print("\nwrote ptlens_joint_fit.json")
