#!/usr/bin/env python3
"""The COHERENT TRAIL ANISOTROPY estimator, and the spin-2 fit of it per rho bin.

  coherent_trail.py --selftest                      the fire test (planted trail)
  coherent_trail.py gates <out.json>                reproduce the recorded numbers
  coherent_trail.py bins <out.json>                 the per-rho-bin spin-2 fit

WHY THIS FILE EXISTS, and it is a records finding as much as a measurement. The
statistic below produced this thread's central number — the raws carry ~0.53x the
geometrically predicted coherent trail — and it existed only as inline code in a
session whose transcript is gone. Its COMPONENTS graduated into the tree and its
COMPOSITION did not: the inputs are tracked `.lst` files, the conversion constant
is a tracked record, the spin-2 fit and the per-star prediction machinery are
tracked and selftested, and nothing wired them together. This is the wiring, so
that the number re-executes instead of being re-derived from prose.

THE QUANTITY. Siril `findstar` reports a fitted elliptical Gaussian per star:
major and minor FWHM in px and a position angle. The anisotropy

    D = major^2 - minor^2        [px^2, and >= 0 by the major/minor sort]

is the part of the second moment that a blur ADDS along one axis, so a uniform
trail of length L contributes D = CONV * L^2 along the trail axis and nothing
across it. Because D is an AXIAL (mod-180) quantity it is carried as spin-2:

    D1 = D cos(2 theta),  D2 = D sin(2 theta)

and a term shared by every star survives averaging while random optical
anisotropy cancels. Two readings of that average, and they are NOT the same
number — state which one you are quoting:

  COHERENT MAGNITUDE, direction-free   |(<D1>, <D2>)| at axis 0.5*atan2(<D2>,<D1>)
  PROJECTION on a named axis           <D cos(2(theta - axis))>

They differ by cos(2 * offset) between the two axes, which is exactly how the
recorded pair 0.5869 at +9.16 deg and 0.5798 on the +4.70 deg trail axis relate
(0.5869 * cos(2*4.46 deg) = 0.5798). The direction-free form is the honest one
when the axis is what is under test; the projection is the one to quote against a
prediction that names a direction.

WHY PER RHO BIN, AND WHY THE AZIMUTHAL AVERAGE IS THE WRONG STATISTIC HERE. The
projection weights each star by cos(2 phi) relative to a fixed axis, so a RADIAL
term cancels out of it only under COMPLETE azimuthal sampling. A rectangular frame
does not sample azimuth completely outside its inscribed circle: on 6064x4040 the
circle holds only to rho = 0.554, and beyond rho = 0.832 only the corners remain.
The excluded azimuths are those near +-90 deg where cos(2 phi) = -1, so removing
them leaves <cos 2 phi> POSITIVE and a radial term leaks into the drift-axis
projection with a positive sign. `decompose()` is immune by construction because
it FITS the radial term jointly instead of assuming it averages away.

WHAT IS THE TOOL'S AND WHAT IS IN-HOUSE (the bright line, CLAUDE.md):
  Siril        every star: the elliptical-Gaussian fit, its major/minor FWHM and
               its position angle, via `findstar` -> the tracked `.lst` files.
  Siril        the CONVERSION constant: `psf_calib.json`'s
               `fitted_constant_in_corpus_L_band`, measured by pushing planted
               trails of known L through the same `findstar` call.
  in-house     the spin-2 bookkeeping, the averaging, the cut ladder and the
               least-squares fit — a derived result no tool reports.
It reads NO pixel: `.lst` text and JSON records only.

THE CONVERSION CONSTANT IS FITTED, NOT ANALYTIC, AND THE DIFFERENCE IS 6.4%.
The second-moment identity gives CONV = 2.3548^2/12 = 0.46209, but Siril fits an
elliptical GAUSSIAN to a top-hat-convolved star and the measured constant over
this corpus's L band is 0.49375 (`psf_calib.json`). Using the identity understates
the prediction by 6.41% and would return a clean-looking wrong ratio. This file
reads the fitted value from the record and refuses to hardcode it.

REMOVAL CONDITION. Delete this file if Siril (or any tool in TOOLS.md) grows a
command reporting a coherent spin-2 moment over a star list, or if the trail
question it serves is closed. It gates nothing and rewrites nothing.

REPORTS ONLY: no threshold, no verdict, exits 0. `--selftest` is the exception —
it exits 1 when the planted control is not recovered, because a fixture that
cannot fail is this repo's most persistent defect.
"""
import json
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
DATASETS = os.path.normpath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, HERE)

from pa_convention import read_lst, decompose, wrap180  # noqa: E402

INJECT = os.path.join(HERE, "inject_work")
PSF_WORK = os.path.join(DATASETS, "aug06", "set-01", "psf_work")
MEMRAW = os.path.join(HERE, "memraw_work")


# --------------------------------------------------------------------------
# the statistic
# --------------------------------------------------------------------------

def anisotropy(major, minor, theta_deg):
    """(major, minor, PA) -> (D, D1, D2) in px^2, spin-2."""
    D = major ** 2 - minor ** 2
    t2 = 2.0 * np.radians(theta_deg)
    return D, D * np.cos(t2), D * np.sin(t2)


def coherent(D1, D2):
    """Direction-free coherent term: (magnitude px^2, axis deg in (-90, +90])."""
    m1, m2 = float(np.mean(D1)), float(np.mean(D2))
    return float(np.hypot(m1, m2)), wrap180(0.5 * np.degrees(np.arctan2(m2, m1))), m1, m2


def projection(D, theta_deg, axis_deg):
    """Mean anisotropy projected on a NAMED axis, px^2."""
    return float(np.mean(D * np.cos(2.0 * np.radians(theta_deg - axis_deg))))


def conv_constant():
    """Siril's own fitted top-hat->Gaussian conversion. Never the identity."""
    rec = json.load(open(os.path.join(HERE, "psf_calib.json")))
    return float(rec["fitted_constant_in_corpus_L_band"])


def load_many(paths):
    """Stack several .lst files into one population."""
    out = []
    for p in paths:
        d, _ = read_lst(p)
        out.append(d)
    return np.vstack(out)


def measure(d, axis_deg=None, cut=None):
    """One population -> the full set of readings, optionally |D|-cut."""
    major, minor, theta = d[:, 3], d[:, 4], d[:, 5]
    D, D1, D2 = anisotropy(major, minor, theta)
    keep = np.ones(len(D), bool) if cut is None else (D <= cut)
    D, D1, D2, theta = D[keep], D1[keep], D2[keep], theta[keep]
    mag, ax, m1, m2 = coherent(D1, D2)
    r = {
        "n": int(keep.sum()),
        "coherent_magnitude_px2": mag,
        "coherent_axis_deg": ax,
        "mean_D1": m1,
        "mean_D2": m2,
        "median_absD": float(np.median(D)),
        "mean_absD": float(np.mean(D)),
        "mean_over_median_absD": float(np.mean(D) / np.median(D)),
    }
    if axis_deg is not None:
        r["projection_on_axis_px2"] = projection(D, theta, axis_deg)
        r["projection_axis_deg"] = axis_deg
        r["frac_negative_on_axis"] = float(
            np.mean(np.cos(2.0 * np.radians(theta - axis_deg)) * D < 0))
    return r


# --------------------------------------------------------------------------
# the selftest -- Gate 2, the planted control, and it CAN fail
# --------------------------------------------------------------------------

def sites_to_lst_frame(sites, H):
    """Planted-site array coordinates -> the frame Siril `findstar` reports in.

    MEASURED, not assumed, and it is a trap that cost this fixture its first run.
    The site array is in ARRAY order (y counted from the top); `findstar` reports
    FITS order (y from the bottom). Matching them as-is recovers 85 of 2765
    planted stars instead of ~2735, and the 85 are chance coincidences — the
    fixture then reads the REAL population as if it were the planted one and
    every downstream number is wrong in the direction that flatters the estimator.

    The exact relation, from the matched residuals under each candidate:
        x_lst = x_site + 0.5
        y_lst = (H - 1 - y_site) + 0.5 = H - 0.5 - y_site
    A half-pixel offset appears in BOTH axes with the same sign, which is the
    signature of a pixel-centre convention difference rather than a fit bias; a
    bias would not be symmetric in x and y. Under it the median residual is
    0.000 px in both axes.
    """
    return sites[:, 0] + 0.5, (H - 0.5) - sites[:, 1]


def _match_planted(lst_path, sites_path, H=4040, tol=1.5):
    """Label the planted population in a mixed list by nearest planted site.

    The injection put synthetic trails at KNOWN sites into a real frame and
    measured both populations with ONE findstar call, so the list is mixed and
    the site array is the only ground truth that separates them. Sites were
    rejected within 12 px of any real star, so a 1.5 px match radius cannot pull
    in a real star that happens to sit nearby.
    """
    d, _ = read_lst(lst_path)
    sites = np.load(sites_path)
    sx, sy = sites_to_lst_frame(sites, H)
    dx = d[:, 1][:, None] - sx[None, :]
    dy = d[:, 2][:, None] - sy[None, :]
    r = np.hypot(dx, dy)
    near = r.min(axis=1)
    return d[near <= tol], d[near > tol], near


def selftest():
    fails = []

    def check(name, got, want, tol, unit=""):
        ok = abs(got - want) <= tol
        print("  %-58s %10.4f vs %10.4f %-4s %s"
              % (name, got, want, unit, "OK" if ok else "*** FAIL ***"))
        if not ok:
            fails.append(name)

    print("CONVERSION CONSTANT — must be the FITTED one, not the identity")
    CONV = conv_constant()
    check("CONV read from psf_calib.json", CONV, 0.49374712819727373, 1e-12)
    check("CONV is NOT the analytic identity 0.46209",
          abs(CONV - 0.4620902533333333) > 0.03, True, 0.5)
    L = 1.657
    pred = CONV * L ** 2
    check("CONV * L^2 at L=1.657 reproduces the recorded prediction",
          pred, 1.3555, 0.002, "px2")

    print()
    print("ALGEBRA — the two readings must relate by cos(2*offset), exactly")
    # a planted spin-2 field with a known magnitude and axis
    rng = np.random.default_rng(20260813)
    n = 20000
    th = rng.uniform(-90, 90, n)
    D = np.full(n, 2.0)
    # inject a coherent axis at +9.16 deg by rotating a fraction of the sample
    th_coh = np.full(n, 9.16)
    _, C1, C2 = anisotropy(np.sqrt(D + 4.0), np.full(n, 2.0), th_coh)
    magc, axc, _, _ = coherent(C1, C2)
    check("planted coherent axis recovered", axc, 9.16, 0.01, "deg")
    off = 4.46
    proj = projection(np.full(n, magc), th_coh, 9.16 - off)
    check("projection = magnitude * cos(2*offset)",
          proj, magc * np.cos(np.radians(2 * off)), 1e-9, "px2")

    print()
    print("GATE 2 — the PLANTED TRAIL control, ground truth from sites2.npy")
    # WHICH FILE: injected2/sites2 is DSC_6339, the REPRESENTATIVE frame. The
    # lower-numbered injected/sites pair is DSC_6239 — the first-frame-of-night
    # anomaly the injection was REDONE to avoid, and nothing in the filenames
    # says so. Reaching for the "1" file is the natural mistake and it silently
    # substitutes a frame whose own real-star axis sits ~29 deg away. The check
    # below pins the identification instead of trusting the name.
    lst = os.path.join(INJECT, "injected2.lst")
    sites = os.path.join(INJECT, "sites2.npy")
    if not (os.path.exists(lst) and os.path.exists(sites)):
        print("  *** FAIL *** ground truth missing: %s / %s" % (lst, sites))
        fails.append("gate2 inputs")
    else:
        # the labelling must be PROVEN, not assumed: the flipped convention must
        # recover the planted population and the as-is one must NOT. Without this
        # the fixture passes on a chance-coincidence population.
        arr = np.load(sites)
        d_all, _ = read_lst(lst)
        naive = np.hypot(d_all[:, 1][:, None] - arr[None, :, 0],
                         d_all[:, 2][:, None] - arr[None, :, 1]).min(axis=1)
        check("as-is (unflipped) matching FAILS, as it must",
              float((naive <= 1.5).sum()), 0.0, 200.0, "stars")

        planted, real, near = _match_planted(lst, sites)
        sx, sy = sites_to_lst_frame(arr, 4040)
        jj = np.hypot(planted[:, 1][:, None] - sx[None, :],
                      planted[:, 2][:, None] - sy[None, :]).argmin(axis=1)
        check("matched residual median dx", float(np.median(planted[:, 1] - sx[jj])),
              0.0, 0.05, "px")
        check("matched residual median dy", float(np.median(planted[:, 2] - sy[jj])),
              0.0, 0.05, "px")

        rp = measure(planted, axis_deg=4.70)
        check("planted stars recovered (n)", rp["n"], 2735, 60)
        check("planted mean projection on the trail axis",
              rp["projection_on_axis_px2"], 1.3403, 0.05, "px2")
        check("planted ratio vs predicted 1.3555",
              rp["projection_on_axis_px2"] / 1.3555, 0.99, 0.04, "x")
        check("planted coherent axis recovered",
              rp["coherent_axis_deg"], 4.9, 0.6, "deg")
        # THE CONTRAST, at the recorded condition. The 0.43x figure is the real
        # stars at AMPLITUDE FLOOR 2400 (the record's amplitude ladder), not at
        # floor 0 — quoting it without the floor compares two different
        # populations and reads 1.59x.
        rr = measure(real[real[:, 0] >= 2400], axis_deg=4.70)
        check("REAL stars, same frame, A >= 2400 (the contrast)",
              rr["projection_on_axis_px2"] / 1.3555, 0.43, 0.05, "x")
        # the discriminating control: the planted population must NOT look like
        # the real one. If these ever agree, the labelling is broken.
        sep = rp["projection_on_axis_px2"] / max(rr["projection_on_axis_px2"], 1e-9)
        check("planted/real separation (labelling is real)", sep, 2.30, 0.5, "x")

        # WHICH-FRAME PIN: the discarded pair must still read as the anomaly.
        # This is what stops a future session silently using injected.lst.
        lst1 = os.path.join(INJECT, "injected.lst")
        sites1 = os.path.join(INJECT, "sites.npy")
        if os.path.exists(lst1) and os.path.exists(sites1):
            _, real1, _ = _match_planted(lst1, sites1)
            a1 = measure(real1, cut=6.0)["coherent_axis_deg"]
            check("the DISCARDED pair still carries the DSC_6239 anomaly",
                  a1, -29.3, 6.0, "deg")

    print()
    if fails:
        print("SELFTEST FAILED: %s" % ", ".join(fails))
        return 1
    print("SELFTEST PASSED")
    return 0


# --------------------------------------------------------------------------
# Gate 1 -- reproduce the recorded numbers on tracked inputs
# --------------------------------------------------------------------------

def gates(out_path):
    CONV = conv_constant()
    PRED = 1.3555  # px^2, the recorded constant-field prediction
    rec = {
        "what": "GATE 1: does this estimator reproduce the recorded coherent-trail "
                "numbers from TRACKED inputs?",
        "conversion_constant": {
            "value": CONV,
            "source": "psf_calib.json fitted_constant_in_corpus_L_band",
            "analytic_identity_NOT_used": 0.4620902533333333,
            "ratio_fitted_over_identity": CONV / 0.4620902533333333,
        },
        "prediction_px2": PRED,
        "samples": {},
    }

    # sample A -- the 3 tracked single RAWs, 8074 stars, recorded at
    # coherent 0.5869 px^2 at +9.16 deg and projection 0.5798 on the +4.70 axis
    paths = [os.path.join(PSF_WORK, "f%d.lst" % i) for i in (1, 2, 3)]
    if all(os.path.exists(p) for p in paths):
        d = load_many(paths)
        m = measure(d, axis_deg=4.70)
        m["recorded_coherent_magnitude_px2"] = 0.5869
        m["recorded_coherent_axis_deg"] = 9.16
        m["recorded_projection_px2"] = 0.5798
        m["recorded_n"] = 8074
        m["ratio_vs_prediction"] = m["projection_on_axis_px2"] / PRED
        m["recorded_ratio"] = 0.43
        rec["samples"]["A_psf_work_3_raws"] = m

    # sample B -- sub_01's 5 constituent raws, recorded cut ladder
    # 0.7264 / 0.7276 / 0.7251 / 0.7131 at cuts none / 20 / 10 / 6.
    #
    # TWO SPECIFICATIONS THE RECORD DOES NOT STATE, both recovered by requiring
    # all FIVE per-raw values to match at once (5 simultaneous matches is an
    # identification, not a fit):
    #   POPULATION  above-median amplitude, per frame. Uncut, the same frames
    #               read 1.3695/2.4322/1.8493/1.5412/1.7712 — nothing like it.
    #   STATISTIC   the direction-free COHERENT MAGNITUDE, not the projection on
    #               the +4.70 axis. Sample A's recorded 0.5798 IS a projection,
    #               so the two headline numbers of this thread are DIFFERENT
    #               QUANTITIES and the records do not say so.
    # The magnitude is the norm of a mean 2-vector and is therefore positively
    # biased by noise, where a projection on a named axis is unbiased. At these
    # n the bias is small, but the two are not interchangeable and B's ratio is
    # the slightly generous one.
    paths = [os.path.join(MEMRAW, "k_0000%d.lst" % i) for i in range(1, 6)]
    if all(os.path.exists(p) for p in paths):
        ladder, per_raw = {}, {}
        for cut, label in ((None, "none"), (20.0, "20"), (10.0, "10"), (6.0, "6")):
            vals = []
            for p in paths:
                d, _ = read_lst(p)
                d = d[d[:, 0] >= np.median(d[:, 0])]      # above-median amplitude
                vals.append(measure(d, axis_deg=4.70,
                                    cut=cut)["coherent_magnitude_px2"])
            ladder[label] = float(np.mean(vals))
            if cut is None:
                per_raw = {os.path.basename(p): v for p, v in zip(paths, vals)}
        rec["samples"]["B_memraw_5_constituent_raws"] = {
            "population": "above-median amplitude per frame",
            "statistic": "direction-free coherent MAGNITUDE (not the axis projection)",
            "cut_ladder_mean_coherent_magnitude_px2": ladder,
            "recorded_cut_ladder": {"none": 0.7264, "20": 0.7276,
                                    "10": 0.7251, "6": 0.7131},
            "per_raw_none_cut": per_raw,
            "recorded_per_raw": {"DSC_6239": 0.4615, "DSC_6264": 0.7573,
                                 "DSC_6289": 0.8026, "DSC_6314": 0.7951,
                                 "DSC_6338": 0.8154},
            "ratio_vs_prediction_no_cut": ladder["none"] / PRED,
            "recorded_ratio": 0.536,
        }

    json.dump(rec, open(out_path, "w"), indent=1)
    print(json.dumps(rec, indent=1))
    return 0


# --------------------------------------------------------------------------
# the per-rho-bin spin-2 fit -- the actual product
# --------------------------------------------------------------------------

def bins(out_path, nbin=5):
    CONV = conv_constant()
    PRED = 1.3555
    acq = json.load(open(os.path.join(DATASETS, "aug06", "set-01",
                                      "acquisition.json")))["exif"]
    W, H = acq["image_wh"]
    cx, cy = (W - 1) / 2.0, (H - 1) / 2.0
    rmax = np.hypot(cx, cy)

    # THE POPULATION IS THE ONE a2c7ba2's RULING WAS BUILT ON, recovered by its
    # own star count: above-median amplitude per frame, then |D| <= 6, pooled
    # over the 5 constituent raws -> 17 762 stars, which that commit states.
    paths = [os.path.join(MEMRAW, "k_0000%d.lst" % i) for i in range(1, 6)]
    paths = [p for p in paths if os.path.exists(p)]
    parts = []
    for p in paths:
        dd, _ = read_lst(p)
        parts.append(dd[dd[:, 0] >= np.median(dd[:, 0])])
    d = np.vstack(parts)
    major, minor, theta = d[:, 3], d[:, 4], d[:, 5]
    D, D1, D2 = anisotropy(major, minor, theta)
    keep = D <= 6.0                      # the validated tail cut
    x, y = d[:, 1][keep], d[:, 2][keep]
    D, D1, D2, theta = D[keep], D1[keep], D2[keep], theta[keep]
    phi = np.arctan2(y - cy, x - cx)
    rho = np.hypot(x - cx, y - cy) / rmax
    pooled_mag, pooled_axis, _, _ = coherent(D1, D2)

    edges = np.quantile(rho, np.linspace(0, 1, nbin + 1))
    rows = []
    for i in range(nbin):
        lo, hi = edges[i], edges[i + 1]
        m = (rho >= lo) & (rho <= hi if i == nbin - 1 else rho < hi)
        if m.sum() < 200:
            continue
        fit = decompose(phi[m], D1[m], D2[m])
        C1, C2 = fit["fixed_c0"], fit["fixed_s0"]
        proj_fixed = (C1 * np.cos(np.radians(2 * pooled_axis))
                      + C2 * np.sin(np.radians(2 * pooled_axis)))
        # the NAIVE statistic a2c7ba2's ruling used: the direction-free coherent
        # magnitude within the bin. Reported alongside so the artefact and the
        # immune estimator are visible in the same table.
        naive = coherent(D1[m], D2[m])[0]
        rows.append({
            "bin": i + 1,
            "rho_lo": float(lo), "rho_hi": float(hi),
            "n": int(m.sum()),
            "rho_median": float(np.median(rho[m])),
            "FIXED_C1": C1, "FIXED_C2": C2,
            "FIXED_magnitude_px2": fit["fixed_amplitude"],
            "FIXED_magnitude_SE_units": fit["fixed_amplitude_SE_units"],
            "FIXED_axis_deg": fit["fixed_direction_theta0_deg"],
            "FIXED_axis_se_deg": fit["fixed_direction_se_deg"],
            "FIXED_projection_on_trail_axis_px2": float(proj_fixed),
            "RADIAL_R_px2": fit["radial_R"],
            "RADIAL_SE_units": fit["radial_SE_units"],
            "design_condition": fit["design_condition"],
            "ratio_fixed_projection_vs_prediction": float(proj_fixed / PRED),
            "naive_coherent_magnitude_px2": naive,
            "naive_ratio": float(naive / PRED),
        })

    # THE PINNED PREDICTION. Only the INNER THREE bins are used: they lie inside
    # (or almost inside) the inscribed circle so their azimuth is complete, their
    # design condition is 1.09-1.10, and naive and spin-2 agree there. Bins 4-5
    # are excluded because that is exactly where the azimuth clips.
    inner = [r for r in rows if r["bin"] <= 3]
    pred_block = None
    if len(inner) == 3:
        rr = [r["ratio_fixed_projection_vs_prediction"] for r in inner]
        ss = [(r["FIXED_magnitude_px2"] / r["FIXED_magnitude_SE_units"]) / PRED
              for r in inner]
        ratio = float(np.mean(rr))
        se = float(np.sqrt(sum(s * s for s in ss)) / 3.0)
        t = float(np.sqrt(ratio))
        st = se / (2.0 * np.sqrt(ratio))
        dm = float(-2.5 * np.log10(t))
        sdm = float(2.5 / np.log(10) * st / t)
        pred_block = {
            "why_inner_three_only": "complete azimuth inside the inscribed "
                                    "circle (rho <= 0.554), design condition "
                                    "1.09-1.10, naive and spin-2 agree",
            "trail_ratio_px2": ratio,
            "trail_ratio_se": se,
            "per_bin_ratios": rr,
            "t_eff_over_t_nominal": t,
            "PREDICTED_ZP_DEFICIT_MAG": dm,
            "PREDICTED_ZP_DEFICIT_SE_MAG": sdm,
            "axis_systematic_mag": 0.013,
            "axis_systematic_note": "projecting on the trail axis +4.70 instead "
                                    "of the pooled +12.71 gives 0.583 mag; the "
                                    "difference is the systematic",
            "conversion": "anisotropy ~ L^2 ~ t_exp^2, so t_eff/t_nom = "
                          "sqrt(ratio) and dm = -2.5 log10(sqrt(ratio)). "
                          "Reading the px^2 ratio AS a time ratio doubles it.",
        }

    rec = {
        "what": "the coherent trail term per rho bin, estimated by the JOINT "
                "spin-2 fit (fixed + radial) rather than by azimuthal averaging",
        "PREDICTION_PINNED": pred_block,
        "why": "the azimuthal projection cancels a radial term only under "
               "COMPLETE azimuth, which a rectangular frame does not provide "
               "beyond its inscribed circle (rho = 0.554 here). decompose() "
               "fits the radial term instead of assuming it averages away.",
        "conversion_constant": CONV,
        "prediction_px2": PRED,
        "canvas": [W, H],
        "inscribed_circle_rho": float(min(cx, cy) / rmax),
        "corners_only_beyond_rho": float(max(cx, cy) / rmax),
        "tail_cut_absD_px2": 6.0,
        "n_stars": int(len(D)),
        "n_stars_recorded_by_a2c7ba2": 17762,
        "pooled_coherent_magnitude_px2": pooled_mag,
        "pooled_axis_deg": pooled_axis,
        "pooled_axis_recorded_by_a2c7ba2_deg": 12.71,
        "recorded_naive_quintile_ratios": [0.37, 0.35, 0.33, 0.46, 0.73],
        "bins": rows,
        "reports_only": "MEASUREMENT. No threshold, no verdict. Exits 0.",
    }
    json.dump(rec, open(out_path, "w"), indent=1)
    print(json.dumps(rec, indent=1))
    return 0


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return 2
    cmd = sys.argv[1]
    if cmd == "--selftest":
        return selftest()
    if cmd == "gates":
        return gates(sys.argv[2])
    if cmd == "bins":
        return bins(sys.argv[2])
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main())
