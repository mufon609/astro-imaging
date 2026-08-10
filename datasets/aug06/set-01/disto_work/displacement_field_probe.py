#!/usr/bin/env python
"""DIAGNOSTIC probe v3 — adds the two checks that decide whether v2's
non-radial residual is real:

 1. RADIAL-BASIS CONVERGENCE. A radial displacement field has du = u*f(r),
    which is ODD in u. So a WRONG radial f (basis truncated too low) leaves an
    ODD-in-u residual, never an even one. Fitting f at degrees 4..8 shows
    whether model A is basis-limited.
 2. EVEN/ODD DECOMPOSITION of the residual across x. Even-in-x structure
    cannot be produced by any centred radial model at any degree.
 3. REPRODUCIBILITY across frames from different sets and different nights —
    a fixed lens property must repeat in SENSOR coordinates.

Tools: sep (SExtractor core) detection + centroids; astrometry.net solution
and catalogue list. Correspondence uses the tool's full TAN+SIP solution;
the displacement is measured against the LINEAR part of the same solution.
"""
import json
import sys

sys.path.insert(0, "/home/samsung/Desktop/astro-imaging/scripts/lib")
sys.path.insert(0, "/home/samsung/Desktop/astro-imaging/scripts/calibrate")

import numpy as np
from scipy.spatial import cKDTree
from scipy.optimize import minimize
from astropy.io import fits
from astropy.wcs import WCS

import solve_field as sf

HINT = (303.0, 43.0, 25.0)
MATCH_TOL = 8.0


def design(un, vn, kind, deg=4):
    r = np.hypot(un, vn)
    r2 = r ** 2
    one, zero = np.ones_like(un), np.zeros_like(un)
    if kind == "poly4":
        C = [un ** p * vn ** q for p in range(5) for q in range(5 - p)]
        k = len(C)
        return np.vstack([np.column_stack(C + [zero] * k),
                          np.column_stack([zero] * k + C)])
    rad_u = [un * r ** k for k in range(1, deg + 1)]
    rad_v = [vn * r ** k for k in range(1, deg + 1)]
    Cu = [one, un, vn, zero, zero, zero] + rad_u
    Cv = [zero, zero, zero, one, un, vn] + rad_v
    if kind == "brown":
        Cu += [2 * un * vn, r2 + 2 * un ** 2]
        Cv += [r2 + 2 * vn ** 2, 2 * un * vn]
    return np.vstack([np.column_stack(Cu), np.column_stack(Cv)])


def fit(un, vn, du, dv, kind, deg=4):
    A = design(un, vn, kind, deg)
    b = np.concatenate([du, dv])
    coef, *_ = np.linalg.lstsq(A, b, rcond=None)
    res = b - A @ coef
    n = len(du)
    return coef, res[:n], res[n:]


def rms(a, b):
    return float(np.sqrt((a ** 2 + b ** 2).mean()))


def analyse(frame, tag, warcmin=None):
    det_stars, H, W = sf.detect_stars_sep(frame, max_stars=8000)
    det = np.array(det_stars, float)
    solve_stars, _, _ = sf.detect_stars_sep(frame, max_stars=1500)
    m = sf.solve(solve_stars, hint=sf.scale_hint(frame, warcmin),
                 scales=sf.scale_set(frame, warcmin), pos=HINT)
    hdr = fits.Header()
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
    print(f"[{tag}] detections {len(det)} | catalogue in frame {len(fx)} -> matched {good.sum()}")
    xm, ym = det[i1[good], 0], det[i1[good], 1]
    xl, yl = lx[good], ly[good]
    du, dv = xm - xl, ym - yl
    R = 0.5 * float(np.hypot(W, H))
    u0, v0 = (W + 1) / 2.0, (H + 1) / 2.0
    un, vn = (xl - u0) / R, (yl - v0) / R
    _, ru, rv = fit(un, vn, du, dv, "radial")
    r = np.hypot(ru, rv)
    keep = r < np.median(r) + 4 * 1.4826 * np.median(np.abs(r - np.median(r)))
    un, vn, du, dv, xl = un[keep], vn[keep], du[keep], dv[keep], xl[keep]
    n = len(un)
    tot = np.hypot(du, dv)
    print(f"\n=== {tag}  RA {m.center_ra_deg:.2f} Dec {m.center_dec_deg:+.2f} "
          f"logodds {m.logodds:.0f} | {n} stars | displacement vs LINEAR WCS "
          f"median {np.median(tot):.1f} px max {tot.max():.1f} px")

    out = {"tag": tag, "n": int(n), "ra": m.center_ra_deg,
           "dec": m.center_dec_deg, "logodds": m.logodds,
           "displacement_median_px": round(float(np.median(tot)), 2),
           "displacement_max_px": round(float(tot.max()), 2)}

    print("  radial-basis convergence (model A = affine + centred radial):")
    conv = {}
    for deg in (4, 5, 6, 7, 8):
        _, a, b = fit(un, vn, du, dv, "radial", deg)
        conv[deg] = round(rms(a, b), 3)
        print(f"    radial degree {deg}: RMS {conv[deg]:6.3f} px")
    out["A_rms_by_radial_degree"] = conv

    cB, aB, bB = fit(un, vn, du, dv, "brown", 8)
    _, aD, bD = fit(un, vn, du, dv, "poly4")
    p1, p2 = cB[-2], cB[-1]
    # peak px the tangential pair contributes anywhere on the sensor
    gu = np.linspace(-W / 2, W / 2, 60) / R
    gv = np.linspace(-H / 2, H / 2, 40) / R
    GU, GV = np.meshgrid(gu, gv)
    RR = GU ** 2 + GV ** 2
    tu = 2 * p1 * GU * GV + p2 * (RR + 2 * GU ** 2)
    tv = p1 * (RR + 2 * GV ** 2) + 2 * p2 * GU * GV
    peak = float(np.hypot(tu, tv).max())
    out["B_brown"] = {"rms_px": round(rms(aB, bB), 3),
                      "p1": round(float(p1), 5), "p2": round(float(p2), 5),
                      "peak_tangential_px": round(peak, 2)}
    out["D_poly4_rms_px"] = round(rms(aD, bD), 3)
    print(f"  B (+Brown p1,p2 on degree-8 radial): RMS {out['B_brown']['rms_px']:.3f} px"
          f"   p1 {p1:+.4f} p2 {p2:+.4f}  -> peak tangential "
          f"{peak:.1f} px on the sensor")
    print(f"  D (general 2-D poly order 4, 30 params): "
          f"RMS {out['D_poly4_rms_px']:.3f} px")

    def cost(p):
        _, a, b = fit((xl - u0 - p[0]) / R, vn - p[1] / R, du, dv, "radial", 8)
        return rms(a, b)
    opt = minimize(cost, [0.0, 0.0], method="Nelder-Mead",
                   options={"initial_simplex": [[0, 0], [400, 0], [0, 400]],
                            "xatol": 5.0, "fatol": 1e-3})
    out["C_free_centre"] = {"rms_px": round(float(opt.fun), 3),
                            "shift_px": [round(float(opt.x[0])),
                                         round(float(opt.x[1]))]}
    print(f"  C (radial deg 8 about a FREE centre): RMS {opt.fun:.3f} px "
          f"(shift {opt.x[0]:+.0f}, {opt.x[1]:+.0f} px)")

    # even/odd decomposition of the degree-8 radial residual across x
    _, ru, rv = fit(un, vn, du, dv, "radial", 8)
    edges = np.linspace(0, W, 9)
    prof = []
    for i in range(8):
        s = (xl >= edges[i]) & (xl < edges[i + 1])
        prof.append(None if s.sum() < 8 else
                    (int(s.sum()), float(ru[s].mean()), float(rv[s].mean()),
                     int(round(100 * (edges[i] + edges[i + 1]) / 2 / W))))
    print("  residual of the degree-8 CENTRED RADIAL model, binned across x:")
    print("      x%     n   mean dx   mean dy       | even/odd pairs of dx")
    pairs = []
    for i in range(8):
        if prof[i]:
            nn, mdx, mdy, xp = prof[i]
            j = 7 - i
            extra = ""
            if i < 4 and prof[j]:
                ev = (mdx + prof[j][1]) / 2
                od = (mdx - prof[j][1]) / 2
                pairs.append({"x_pct": xp, "even_dx": round(ev, 2),
                              "odd_dx": round(od, 2)})
                extra = f"   even {ev:+6.2f}   odd {od:+6.2f}"
            print(f"     {xp:>3}  {nn:>4}   {mdx:+7.3f}  {mdy:+7.3f}{extra}")
    out["even_odd_dx"] = pairs
    ev = np.array([p["even_dx"] for p in pairs])
    od = np.array([p["odd_dx"] for p in pairs])
    out["even_rms_px"] = round(float(np.sqrt((ev ** 2).mean())), 2)
    out["odd_rms_px"] = round(float(np.sqrt((od ** 2).mean())), 2)
    print(f"  => EVEN-in-x component RMS {out['even_rms_px']} px "
          f"(unrepresentable by ANY centred radial model)")
    print(f"     ODD-in-x  component RMS {out['odd_rms_px']} px "
          f"(what a radial-basis error would produce)")
    return out


if __name__ == "__main__":
    import os
    frame, tag = sys.argv[1], sys.argv[2]
    warcmin = float(sys.argv[3]) if len(sys.argv) > 3 else None
    r = analyse(frame, tag, warcmin)
    out = os.path.join(os.path.dirname(frame), f"disp_{tag}.json")
    json.dump(r, open(out, "w"), indent=1)
    print("wrote", out)
