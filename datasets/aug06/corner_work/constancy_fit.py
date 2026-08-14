#!/usr/bin/env python3
"""Is the fixed spin-2 term, after trail subtraction, a CONSTANT 2-VECTOR in rho?

  constancy_fit.py <out.json>
  constancy_fit.py --selftest

WHY THIS IS THE QUESTION. `corner-fix-landscape` classifies single-PSF
deconvolution (`rl -loadpsf=`) as the one FIX-classified route on the board, and
gates it on a genuinely FIELD-CONSTANT component: a uniform PSF component is what
an ordinary single-PSF deconvolution can remove. Constancy is testable WITHOUT
pinning the trail magnitude. If the residual after trail subtraction still
rotates, no single global PSF removes it and the route dies; if a good subtraction
exists, its scale IS the trail magnitude, obtained as a by-product of the question
that actually decides something.

THE MODEL, and it is asserted in the quantity the result is expressed in. A spin-2
residual has TWO components, so constancy in magnitude alone is not constancy:

    C_i  =  f * T_i  +  K  +  noise            i = 1..nbin

  C_i  the bin's FIXED term from the joint fixed+radial spin-2 fit (px^2, 2-vec)
  T_i  the bin's PREDICTED trail 2-vector, from the frame's own WCS (px^2)
  f    ONE free scale on the trail, the nuisance parameter
  K    the field-constant 2-vector under test, free, 2 parameters

Linear in (f, K1, K2): 3 parameters against 2*nbin observations.

THE LEVER IS WEAK AND THAT GOVERNS WHAT CAN BE CONCLUDED — measured, not assumed.
Across rho-equal bins the PREDICTED trail vector varies only 5.0% in magnitude and
1.6 deg in axis. T_i is therefore nearly a constant vector, so f*T_i is nearly
absorbed by K: the f column of the design is nearly collinear with the K columns.

  Consequence 1, and it makes the test WORK: because subtracting f*T can barely
  change the SHAPE of C(rho), "is C - f*T constant?" is very nearly "is C
  constant?" — a question the data answers. If C rotates, NO f rescues it.
  Consequence 2, and it makes f UNQUOTABLE: if the residual IS constant, f is
  poorly determined by construction, and the design's condition number says so.
  f is also degenerate with any overall scale error in the WCS used for T.

So this file can KILL the fix route decisively and can only ever BOUND f. It
reports the conditioning so that asymmetry is visible rather than implied.

WHAT IS THE TOOL'S AND WHAT IS IN-HOUSE (the bright line, CLAUDE.md):
  Siril            every star: the elliptical-Gaussian fit, major/minor FWHM and
                   position angle, via `findstar` -> the tracked .lst files.
  astrometry.net   the WCS the trail prediction is computed from.
  Siril            the conversion constant (psf_calib.json's FITTED 0.49375).
  in-house         the spin-2 bookkeeping, the binning, the least squares.
Reads no pixel: .lst text, a WCS header and JSON records only.

REMOVAL CONDITION. Retire when a tool reports a field-constant PSF component over
a star list, or when the fix route it gates is closed either way.

REPORTS ONLY: no threshold, no verdict, exits 0. --selftest exits 1 on failure.
"""
import json
import math
import os
import sys

import numpy as np
from astropy.io import fits
from astropy.wcs import WCS

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from pa_convention import read_lst, decompose, wrap180          # noqa: E402
from coherent_trail import anisotropy, coherent, conv_constant  # noqa: E402

MEMRAW = os.path.join(HERE, "memraw_work")
WCSF = os.path.join(HERE, "phot_work", "k3.wcs")
TAILCUT = 6.0
SIDEREAL = 15.041          # arcsec/s of RA motion at dec 0
EXPTIME = 2.5

# the recorded equal-count numbers this must bracket against
REC_EQCOUNT_RATIO = [0.369, 0.357, 0.324, 0.392, 0.603]
REC_EQCOUNT_AXIS = [0.04, 13.86, 21.94, 15.74, 10.49]


def population():
    """The same population coherent_trail.bins uses: above-median amplitude per
    frame, then |D| <= 6, pooled over sub_01's five constituent raws."""
    acq = json.load(open(os.path.join(os.path.dirname(HERE), "set-01",
                                      "acquisition.json")))["exif"]
    W, H = acq["image_wh"]
    parts = []
    for i in range(1, 6):
        p = os.path.join(MEMRAW, "k_0000%d.lst" % i)
        d, _ = read_lst(p)
        parts.append(d[d[:, 0] >= np.median(d[:, 0])])
    d = np.vstack(parts)
    D, D1, D2 = anisotropy(d[:, 3], d[:, 4], d[:, 5])
    k = D <= TAILCUT
    x, y = d[k, 1], d[k, 2]
    cx, cy = (W - 1) / 2.0, (H - 1) / 2.0
    rmax = math.hypot(cx, cy)
    return {"x": x, "y": y, "D": D[k], "D1": D1[k], "D2": D2[k],
            "theta": d[k, 5], "phi": np.arctan2(y - cy, x - cx),
            "rho": np.hypot(x - cx, y - cy) / rmax, "W": W, "H": H}


def trail_vectors(x, y):
    """Per-star PREDICTED trail 2-vector, px^2, from the frame's own WCS.

    L_sky = 15.041 * cos(dec) * t_exp arcsec of +RA motion; the WCS Jacobian turns
    that into a pixel displacement, whose length and direction give the trail. The
    conversion to anisotropy is Siril's own fitted kappa, not the identity.

    ONE WCS FOR FIVE FRAMES. The raws carry no WCS; this uses the solve of
    k_00003's own star list. The five sampled raws span 100 frames of a ~1.9 px
    per frame drift, i.e. ~190 px on a 6064 px frame, so the pointing differs by
    ~3% of the field — negligible for dec (which sets cos dec) and for the local
    plate scale. Any OVERALL scale error in this WCS is absorbed by f and is one
    more reason f is a nuisance parameter here.
    """
    w = WCS(fits.getheader(WCSF))
    K = conv_constant()
    dd = 1.0
    a0, d0 = w.all_pix2world(x, y, 0)
    ax, dx_ = w.all_pix2world(x + dd, y, 0)
    ay, dy_ = w.all_pix2world(x, y + dd, 0)
    cd = np.cos(np.radians(d0))
    j11, j21 = (ax - a0) * cd * 3600 / dd, (dx_ - d0) * 3600 / dd
    j12, j22 = (ay - a0) * cd * 3600 / dd, (dy_ - d0) * 3600 / dd
    det = j11 * j22 - j21 * j12
    px_dx, px_dy = j22 / det, -j21 / det          # px per arcsec of +RA
    L = SIDEREAL * np.cos(np.radians(d0)) * EXPTIME
    tx, ty = L * px_dx, L * px_dy
    Lpx = np.hypot(tx, ty)
    th2 = 2.0 * np.arctan2(ty, tx)
    return K * Lpx ** 2 * np.cos(th2), K * Lpx ** 2 * np.sin(th2), Lpx


def population_per_frame():
    """Each raw separately — the 5 frames are INDEPENDENT realisations."""
    acq = json.load(open(os.path.join(os.path.dirname(HERE), "set-01",
                                      "acquisition.json")))["exif"]
    W, H = acq["image_wh"]
    cx, cy = (W - 1) / 2.0, (H - 1) / 2.0
    rmax = math.hypot(cx, cy)
    out = []
    for i in range(1, 6):
        d, _ = read_lst(os.path.join(MEMRAW, "k_0000%d.lst" % i))
        d = d[d[:, 0] >= np.median(d[:, 0])]
        D, D1, D2 = anisotropy(d[:, 3], d[:, 4], d[:, 5])
        k = D <= TAILCUT
        x, y = d[k, 1], d[k, 2]
        out.append({"frame": "k_0000%d" % i, "x": x, "y": y,
                    "D1": D1[k], "D2": D2[k], "theta": d[k, 5],
                    "phi": np.arctan2(y - cy, x - cx),
                    "rho": np.hypot(x - cx, y - cy) / rmax})
    return out


def run_bins_perframe(frames, T1f, T2f, mode, n=5, drop=()):
    """Per-bin fixed term as the MEAN over frames, with a FRAME-BASED SE.

    THE ERROR MODEL IS THE FINDING HERE. A star-level bootstrap inside one pooled
    population captures shot noise only, and MEASURED on these five raws it
    understates the true uncertainty on the per-bin fixed term by a median factor
    of 5.76 — the frame-to-frame scatter is 4-9x the bootstrap SE. Using the
    bootstrap makes chi2/dof 35.6 where the frame-based error makes it ~1.1, i.e.
    it turns "cannot reject" into a spurious rejection. Independent realisations
    are the only honest error bar for a per-bin property.
    """
    allrho = np.concatenate([f["rho"] for f in frames])
    e = bin_edges(allrho, n, mode)
    rows = []
    for b in range(n):
        per = []
        for j, f in enumerate(frames):
            if f["frame"] in drop:
                continue
            m = (f["rho"] >= e[b]) & (f["rho"] <= e[b + 1] if b == n - 1
                                      else f["rho"] < e[b + 1])
            if m.sum() < 150:
                continue
            fit = decompose(f["phi"][m], f["D1"][m], f["D2"][m], nboot=120)
            per.append((fit["fixed_c0"], fit["fixed_s0"],
                        fit["fixed_direction_theta0_deg"],
                        float(np.mean(T1f[j][m])), float(np.mean(T2f[j][m]))))
        if len(per) < 3:
            continue
        a = np.array(per)
        nn = len(a)
        rows.append({
            "bin": b + 1, "rho_lo": float(e[b]), "rho_hi": float(e[b + 1]),
            "n_frames": nn,
            "error_model": "frame_based",
            "C1": float(a[:, 0].mean()), "C2": float(a[:, 1].mean()),
            "se_C1_frame_based": float(a[:, 0].std(ddof=1) / math.sqrt(nn)),
            "se_C2_frame_based": float(a[:, 1].std(ddof=1) / math.sqrt(nn)),
            "fixed_magnitude": float(math.hypot(a[:, 0].mean(), a[:, 1].mean())),
            "fixed_axis_deg": float(a[:, 2].mean()),
            "fixed_axis_se_deg_frame_based": float(a[:, 2].std(ddof=1) / math.sqrt(nn)),
            "per_frame_axis_deg": [float(v) for v in a[:, 2]],
            "T1": float(a[:, 3].mean()), "T2": float(a[:, 4].mean()),
            "T_magnitude": float(math.hypot(a[:, 3].mean(), a[:, 4].mean())),
            "T_axis_deg": float(wrap180(0.5 * math.degrees(
                math.atan2(a[:, 4].mean(), a[:, 3].mean())))),
        })
    return rows


def row_error_model(rows):
    """The ONE error model these rows carry, or a refusal.

    WHY THIS EXISTS — the defect it removes was measured in this file. `se_C1`
    was written from a frame-based scatter by run_bins_perframe and from a
    star-level bootstrap by run_bins, and `constancy()` consumed it without being
    able to tell which. Both arms are DELIBERATE (the bootstrap arm is what makes
    chi2/dof 35.6 where the frame-based one makes it ~1.1 — that contrast is the
    finding), so the fix is not to force one model but to make every row DECLARE
    its own and refuse a mixed or unlabelled set.
    """
    models = {r.get("error_model") for r in rows}
    if models == {None}:
        raise SystemExit("constancy_fit: rows carry no `error_model` — refusing "
                         "to weight by an SE whose error model is unstated")
    if len(models) != 1:
        raise SystemExit("constancy_fit: rows MIX error models %s — a weighted "
                         "fit across both is meaningless" % sorted(map(str, models)))
    return models.pop()


def axis_constancy(rows):
    """Is the fixed-term AXIS constant across bins?

    Uses whichever error model the rows declare, and RECORDS it. This docstring
    used to say "Frame-based errors" while the function accepted bootstrap rows
    just as happily — the claim was in the prose and not in the code.
    """
    em = row_error_model(rows)
    m = np.array([r["fixed_axis_deg"] for r in rows])
    s = np.array([r["fixed_axis_se_deg_" + em] for r in rows])
    w = 1.0 / s ** 2
    wm = float((m * w).sum() / w.sum())
    chi2 = float((((m - wm) / s) ** 2).sum())
    return {"error_model": em,
            "axes_deg": [float(v) for v in m], "ses_deg": [float(v) for v in s],
            "span_deg": float(m.max() - m.min()), "weighted_mean_deg": wm,
            "chi2": chi2, "dof": len(m) - 1,
            "rejects_constant_axis_95pct": bool(chi2 > 9.49)}


def bin_edges(rho, n, mode):
    if mode == "equal_count":
        return np.quantile(rho, np.linspace(0, 1, n + 1))
    return np.linspace(rho.min(), rho.max(), n + 1)


def run_bins(pop, T1, T2, mode, n=5):
    rho = pop["rho"]
    e = bin_edges(rho, n, mode)
    rows = []
    for i in range(n):
        m = (rho >= e[i]) & (rho <= e[i + 1] if i == n - 1 else rho < e[i + 1])
        if m.sum() < 200:
            continue
        fit = decompose(pop["phi"][m], pop["D1"][m], pop["D2"][m])
        rows.append({
            "bin": i + 1, "rho_lo": float(e[i]), "rho_hi": float(e[i + 1]),
            "rho_median": float(np.median(rho[m])), "n": int(m.sum()),
            "error_model": "star_bootstrap",
            "C1": fit["fixed_c0"], "C2": fit["fixed_s0"],
            "se_C1_star_bootstrap": fit["se_bootstrap"][0],
            "se_C2_star_bootstrap": fit["se_bootstrap"][1],
            "fixed_magnitude": fit["fixed_amplitude"],
            "fixed_axis_deg": fit["fixed_direction_theta0_deg"],
            "fixed_axis_se_deg_star_bootstrap":
                fit["fixed_direction_se_deg_star_bootstrap"],
            "radial_R": fit["radial_R"],
            "radial_SE_units_star_bootstrap": fit["radial_SE_units_star_bootstrap"],
            "design_condition": fit["design_condition"],
            "T1": float(np.mean(T1[m])), "T2": float(np.mean(T2[m])),
            "T_magnitude": float(math.hypot(np.mean(T1[m]), np.mean(T2[m]))),
            "T_axis_deg": float(wrap180(0.5 * math.degrees(
                math.atan2(np.mean(T2[m]), np.mean(T1[m]))))),
            "ratio_C_over_prediction": float(
                (fit["fixed_c0"] * np.mean(T1[m]) + fit["fixed_s0"] * np.mean(T2[m]))
                / (np.mean(T1[m]) ** 2 + np.mean(T2[m]) ** 2)),
        })
    return rows


def constancy(rows):
    """Least squares for C_i = f*T_i + K, weighted by each component's own SE.

    The SE's error model comes from the rows themselves (`row_error_model`) and
    is RETURNED, because chi2/dof from this fit is quoted as evidence and is
    ~30x different between the two models on the same data.
    """
    em = row_error_model(rows)
    nb = len(rows)
    y = np.array([r["C1"] for r in rows] + [r["C2"] for r in rows])
    s = np.array([r["se_C1_" + em] for r in rows]
                 + [r["se_C2_" + em] for r in rows])
    X = np.zeros((2 * nb, 3))
    X[:nb, 0] = 1.0                       # K1
    X[nb:, 1] = 1.0                       # K2
    X[:nb, 2] = [r["T1"] for r in rows]   # f
    X[nb:, 2] = [r["T2"] for r in rows]
    Xw, yw = X / s[:, None], y / s
    beta, *_ = np.linalg.lstsq(Xw, yw, rcond=None)
    cov = np.linalg.inv(Xw.T @ Xw)
    resid = yw - Xw @ beta
    chi2 = float(resid @ resid)
    dof = 2 * nb - 3
    sv = np.linalg.svd(Xw, compute_uv=False)

    # the two reference models, so the fit is read against something
    def chi2_fixed_f(fval):
        Xk = X[:, :2] / s[:, None]
        yk = (y - fval * X[:, 2]) / s
        b, *_ = np.linalg.lstsq(Xk, yk, rcond=None)
        r = yk - Xk @ b
        return float(r @ r), [float(v) for v in b]

    c0, k0 = chi2_fixed_f(0.0)
    c1, k1 = chi2_fixed_f(1.0)
    return {
        "error_model": em,
        "f": float(beta[2]), "f_se": float(math.sqrt(cov[2, 2])),
        "K1": float(beta[0]), "K2": float(beta[1]),
        "K_magnitude": float(math.hypot(beta[0], beta[1])),
        "K_axis_deg": float(wrap180(0.5 * math.degrees(
            math.atan2(beta[1], beta[0])))),
        "chi2": chi2, "dof": dof, "chi2_per_dof": chi2 / dof,
        "design_condition": float(sv[0] / sv[-1]),
        "no_trail_f0": {"chi2": c0, "dof": 2 * len(rows) - 2, "K": k0},
        "full_trail_f1": {"chi2": c1, "dof": 2 * len(rows) - 2, "K": k1},
    }


def selftest():
    fails = []

    def ck(name, got, want, tol):
        ok = abs(got - want) <= tol
        print("  %-56s %10.4f vs %10.4f  %s"
              % (name, got, want, "OK" if ok else "*** FAIL ***"))
        if not ok:
            fails.append(name)

    # THE FIT MUST RECOVER A PLANTED (f, K) — and must FAIL to make a rotating
    # residual constant. A fixture that cannot fail is this repo's worst defect.
    rng = np.random.default_rng(11)
    T = [(1.20 + 0.02 * i, 0.12 + 0.002 * i) for i in range(5)]
    for f_true, k_true in ((0.55, (0.30, -0.10)), (1.00, (0.0, 0.0))):
        rows = [{"C1": f_true * t[0] + k_true[0] + rng.normal(0, 1e-4),
                 "C2": f_true * t[1] + k_true[1] + rng.normal(0, 1e-4),
                 "error_model": "frame_based",
                 "se_C1_frame_based": 1e-4, "se_C2_frame_based": 1e-4,
                 "T1": t[0], "T2": t[1]}
                for t in T]
        r = constancy(rows)
        ck("planted f=%.2f recovered" % f_true, r["f"], f_true, 0.05)
        ck("planted K1=%.2f recovered" % k_true[0], r["K1"], k_true[0], 0.02)

    # a residual that ROTATES with rho cannot be made constant by any f
    rows = []
    for i, t in enumerate(T):
        ang = np.radians(2 * (i * 12.0))
        rows.append({"C1": 0.55 * t[0] + 0.4 * math.cos(ang),
                     "C2": 0.55 * t[1] + 0.4 * math.sin(ang),
                     "error_model": "frame_based",
                     "se_C1_frame_based": 1e-3, "se_C2_frame_based": 1e-3,
                     "T1": t[0], "T2": t[1]})
    r = constancy(rows)
    print("  %-56s chi2/dof = %.1f  %s"
          % ("a ROTATING residual must NOT fit a constant", r["chi2_per_dof"],
             "OK" if r["chi2_per_dof"] > 100 else "*** FAIL ***"))
    if not r["chi2_per_dof"] > 100:
        fails.append("rotating residual")

    print()
    if fails:
        print("SELFTEST FAILED: %s" % ", ".join(fails))
        return 1
    print("SELFTEST PASSED")
    return 0


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return 2
    if sys.argv[1] == "--selftest":
        return selftest()
    pop = population()
    T1, T2, Lpx = trail_vectors(pop["x"], pop["y"])

    out = {"what": "is the fixed spin-2 term, after trail subtraction, a CONSTANT "
                   "2-VECTOR in rho? The gate on corner-fix-landscape's only "
                   "FIX-classified route.",
           "population": "sub_01's five constituent raws, above-median amplitude "
                         "per frame, |D| <= %.0f px^2, pooled" % TAILCUT,
           "n_stars": int(len(pop["D"])),
           "trail_prediction": {
               "source": "astrometry.net WCS of k_00003's own star list "
                         "(phot_work/k3.wcs); conversion is Siril's fitted kappa",
               "kappa": conv_constant(),
               "L_px_range": [float(Lpx.min()), float(Lpx.max())],
               "L_px_median": float(np.median(Lpx))},
           "binnings": {}}

    frames = population_per_frame()
    Tf = [trail_vectors(f["x"], f["y"]) for f in frames]
    T1f, T2f = [t[0] for t in Tf], [t[1] for t in Tf]

    for mode in ("equal_count", "rho_equal"):
        rows = run_bins(pop, T1, T2, mode)
        fit = constancy(rows)
        lev_m = [r["T_magnitude"] for r in rows]
        lev_a = [r["T_axis_deg"] for r in rows]
        out["binnings"][mode] = {
            "bins": rows, "constancy_fit_BOOTSTRAP_ERRORS_DO_NOT_USE": fit,
            "LEVER": {
                "trail_magnitude_spread_percent": 100 * (max(lev_m) / min(lev_m) - 1),
                "trail_axis_spread_deg": max(lev_a) - min(lev_a),
                "reads": "f is determined only by how much T VARIES across bins. "
                         "A nearly constant T is absorbed by K, so a weak lever "
                         "makes f unquotable while leaving the constancy question "
                         "intact — subtracting a near-constant vector cannot "
                         "change the SHAPE of C(rho)."},
        }
        for lab, drop in (("all_5_frames", ()), ("drop_DSC_6239", ("k_00001",))):
            pr = run_bins_perframe(frames, T1f, T2f, mode, drop=drop)
            out["binnings"][mode][lab] = {
                "bins": pr, "constancy_fit": constancy(pr),
                "axis_constancy": axis_constancy(pr)}

    ec = out["binnings"]["equal_count"]["bins"]
    out["BRACKET_against_recorded_equal_count"] = {
        "why": "if the equal-count arm does not reproduce, the harness moved and "
               "nothing else here is readable",
        "recorded_axis_deg": REC_EQCOUNT_AXIS,
        "measured_axis_deg": [r["fixed_axis_deg"] for r in ec],
        "recorded_ratio": REC_EQCOUNT_RATIO,
    }
    json.dump(out, open(sys.argv[1], "w"), indent=1)

    for mode in ("equal_count", "rho_equal"):
        b = out["binnings"][mode]
        print("\n=== %s ===" % mode)
        print("%3s %-13s %6s %9s %9s %8s %9s %8s"
              % ("bin", "rho", "n", "|C|", "axis", "axSE", "R", "cond"))
        for r in b["bins"]:
            print("%3d %.3f-%.3f %6d %9.4f %+9.2f %8.2f %+9.4f %8.2f"
                  % (r["bin"], r["rho_lo"], r["rho_hi"], r["n"],
                     r["fixed_magnitude"], r["fixed_axis_deg"],
                     r["fixed_axis_se_deg_star_bootstrap"], r["radial_R"],
                     r["design_condition"]))
        f = b["constancy_fit"]
        print("  lever: |T| spread %.1f%%, axis spread %.2f deg"
              % (b["LEVER"]["trail_magnitude_spread_percent"],
                 b["LEVER"]["trail_axis_spread_deg"]))
        print("  f = %.3f +- %.3f | K = (%.4f, %.4f) |K| %.4f at %+.2f deg"
              % (f["f"], f["f_se"], f["K1"], f["K2"], f["K_magnitude"],
                 f["K_axis_deg"]))
        print("  chi2/dof = %.1f (%d dof) | f=0: %.1f | f=1: %.1f | cond %.1f"
              % (f["chi2_per_dof"], f["dof"], f["no_trail_f0"]["chi2"],
                 f["full_trail_f1"]["chi2"], f["design_condition"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
