#!/usr/bin/env python3
"""Two corrections to the corner-quality result, both from measurement.

  mechanism_and_specs.py <corner_quality.json> <out.json>

(1) SPECIFICATION ROBUSTNESS. The first pass published "roundness is one-sided
in sensor x, not radial" on a fit of x_frac + |x_frac| + rho, quoting 7.1 SE on
x against 1.6 SE on rho. `corr(|x_frac|, rho) = +0.93` on these stations, so
|x_frac| IS a symmetric term and it absorbed the radial signal — rho's 1.6 SE
was collinearity, not absence, and the published sentence overstated. Six
specifications are run here instead of one, and the honest reading is that
BOTH terms carry real signal.

The weighting matters and the data says which weight to use: between-station
scatter tau is measured against the mean per-station measurement variance, and
when tau dominates, weighting by 1/se^2 over-weights a handful of low-SE
stations. The random-effects weight 1/(se^2 + tau^2) is the principled one and
it lands on the unweighted answer.

(2) WHERE THE ONE-SIDED TERM LIVES, from single RAW exposures. The first pass
established member-level and sensor-fixed, then wrote "candidate 3 (optics)
owns the radial term" — which its discriminating test does not support, since
optics, a distortion-model residual, within-member registration and
differential refraction are ALL member-level and sensor-fixed. Siril `findstar`
on three single raws — debayered, uncalibrated, unwarped, unregistered,
unstacked — settles part of it: whatever is in THOSE frames cannot have been
made by registration, by the compose, or as the residual of a correction that
has not been applied yet.

Every number is Siril's (`convert -debayer`, `findstar` at the open gate);
in-house is the binning and the fits. Reads no deliverable pixel. REPORTS ONLY,
exits 0.
"""
import json
import os
import sys

import numpy as np
from astropy.io import fits

HERE = os.path.dirname(os.path.abspath(__file__))
PSF = os.path.join(HERE, "..", "set-01", "psf_work")


def read_lst(path, cols=(3, 5, 6, 7, 8, 11)):
    out = []
    for line in open(path):
        if line.startswith("#"):
            continue
        q = line.split()
        if len(q) < 16:
            continue
        out.append([float(q[c]) for c in cols])
    return np.array(out)


def member_stations(rec):
    """Rebuild the pooled station table from the committed per-series records."""
    out = []
    blocks = list(rec["member_rays"].items()) + list(rec["member_azimuth"].items())
    blocks += [(f"member_{t}", v) for t, v in rec["member_radial_profile"].items()]
    for name, rows in blocks:
        j = os.path.join(HERE, f"shape_{name}.json")
        if not os.path.exists(j):
            continue
        rc = json.load(open(j))
        h = fits.getheader(rc["image"])
        W, H = int(h["NAXIS1"]), int(h["NAXIS2"])
        by = {r["label"]: r for r in rows}
        for r in rc["positions"]:
            if r.get("out_of_canvas") or r["label"] not in by:
                continue
            x, y, w, hh = r["crop"]
            xc, yc = x + w / 2, (H - y - hh) + hh / 2
            s = by[r["label"]]
            out.append({"xf": (xc - (W - 1) / 2) / (W / 2),
                        "rho": float(np.hypot(xc - (W - 1) / 2, yc - (H - 1) / 2)
                                     / np.hypot((W - 1) / 2, (H - 1) / 2)),
                        "roundness": s["roundness"], "roundness_se": s["roundness_se"],
                        "major": s["major_px"], "n": s["n"]})
    return out


def wls(cols, y, w):
    X = np.column_stack(cols)
    A = X * np.sqrt(w)[:, None]
    c, *_ = np.linalg.lstsq(A, y * np.sqrt(w), rcond=None)
    r = y - X @ c
    cov = np.linalg.inv(A.T @ A) * max(1e-12, (r ** 2 * w).sum() / (len(y) - X.shape[1]))
    return c, np.sqrt(np.diag(cov)), float((r ** 2).sum())


def sided_bands(xf, y, edges):
    rows = []
    for lo, hi in zip(edges[:-1], edges[1:]):
        m = (np.abs(xf) >= lo) & (np.abs(xf) < hi)
        a, b = m & (xf < 0), m & (xf > 0)
        if a.sum() < 3 or b.sum() < 3:
            continue
        rows.append({"abs_x_band": [lo, hi], "n_minus": int(a.sum()),
                     "n_plus": int(b.sum()),
                     "minus_x": float(np.median(y[a])), "plus_x": float(np.median(y[b])),
                     "difference": float(np.median(y[b]) - np.median(y[a]))})
    return rows


def main():
    rec = json.load(open(sys.argv[1]))
    out_json = os.path.abspath(sys.argv[2])
    st = member_stations(rec)
    xf = np.array([s["xf"] for s in st])
    rho = np.array([s["rho"] for s in st])
    rnd = np.array([s["roundness"] for s in st])
    maj = np.array([s["major"] for s in st])
    se = np.array([s["roundness_se"] for s in st])
    n = np.array([s["n"] for s in st], float)
    one = np.ones(len(xf))

    _, _, ss = wls((one, xf, rho), rnd, one)
    resid_var = ss / (len(rnd) - 3)
    tau2 = max(0.0, resid_var - float(np.mean(se ** 2)))

    specs = {}
    for nm, w in (("unweighted", one), ("weight_n_stars", n),
                  ("weight_inverse_se2", 1 / se ** 2),
                  ("random_effects_inverse_se2_plus_tau2", 1 / (se ** 2 + tau2))):
        c, s, _ = wls((one, xf, rho), rnd, w)
        specs[nm] = {"x_coef": c[1], "x_SE_units": abs(c[1]) / s[1],
                     "rho_coef": c[2], "rho_SE_units": abs(c[2]) / s[2]}
    c, s, _ = wls((one, xf, np.abs(xf), rho), rnd, one)
    specs["published_form_x_absx_rho"] = {
        "x_coef": c[1], "x_SE_units": abs(c[1]) / s[1],
        "absx_coef": c[2], "absx_SE_units": abs(c[2]) / s[2],
        "rho_coef": c[3], "rho_SE_units": abs(c[3]) / s[3],
        "why_it_misleads": "corr(|x_frac|, rho) = %+.3f, so |x_frac| carries the "
                           "symmetric term and rho is left with a collinear "
                           "remainder of the wrong sign" % np.corrcoef(np.abs(xf), rho)[0, 1]}

    nested = {}
    for key, y in (("roundness", rnd), ("major_px", maj)):
        _, _, ssr = wls((one, rho), y, one)
        _, _, ssx = wls((one, xf), y, one)
        cb, sb, ssb = wls((one, rho, xf), y, one)
        tot = float(((y - y.mean()) ** 2).sum())
        nested[key] = {
            "rho_only_R2": 1 - ssr / tot, "x_only_R2": 1 - ssx / tot,
            "both_R2": 1 - ssb / tot,
            "F_adding_x_to_radial": (ssr - ssb) / (ssb / (len(y) - 3)),
            "F_adding_rho_to_one_sided": (ssx - ssb) / (ssb / (len(y) - 3)),
            "both_rho_SE_units": abs(cb[1]) / sb[1], "both_x_SE_units": abs(cb[2]) / sb[2]}

    out = {
        "correction_1_specification_robustness": {
            "stations": len(st),
            "tau_between_station": float(np.sqrt(tau2)),
            "median_measurement_se": float(np.median(se)),
            "tau_over_median_se": float(np.sqrt(tau2) / np.median(se)),
            "which_weight_is_principled": "the random-effects one. Real "
                "between-station variation exceeds measurement error by the "
                "ratio above, so 1/se^2 over-weights a few low-SE stations; "
                "1/(se^2+tau^2) is the correct precision weight and it lands on "
                "the unweighted answer.",
            "specifications": specs,
            "nested_model_tests_unweighted": nested,
            "verdict": "BOTH terms carry real signal in roundness — neither "
                       "model is adequate alone. Star SIZE is a different "
                       "story and is purely radial.",
            "model_free_sided_bands_member_stations":
                sided_bands(xf, rnd, [0.0, 0.2, 0.4, 0.6, 0.8, 1.01])},
    }

    # ---- correction 2: single RAW exposures ---------------------------------
    lsts = [os.path.join(PSF, f) for f in ("f1.lst", "f2.lst", "f3.lst")]
    if all(os.path.exists(p) for p in lsts):
        hdr = fits.getheader(os.path.join(PSF, "r_00001.fit")) \
            if os.path.exists(os.path.join(PSF, "r_00001.fit")) else None
        W, H = (6064, 4040) if hdr is None else (int(hdr["NAXIS1"]), int(hdr["NAXIS2"]))
        d = np.vstack([read_lst(p) for p in lsts])
        A, Xp, Yp, FX, FY, PA = d.T
        cx, cy = (W - 1) / 2, (H - 1) / 2
        rxf = (Xp - cx) / (W / 2)
        rrho = np.hypot(Xp - cx, Yp - cy) / np.hypot(cx, cy)
        rr = FY / FX
        onr = np.ones(len(rxf))
        raw = {"frames": 3, "stars": int(len(A)), "canvas": [W, H],
               "exptime_s": None if hdr is None else hdr.get("EXPTIME"),
               "state": "debayered, UNcalibrated, UNwarped, UNregistered, "
                        "UNstacked — one exposure",
               "whole_frame": {"major": float(np.median(FX)),
                               "minor": float(np.median(FY)),
                               "roundness": float(np.median(rr))},
               "model_free_sided_bands_roundness":
                   sided_bands(rxf, rr, [0.0, 0.2, 0.4, 0.6, 0.8, 1.01]),
               "model_free_sided_bands_major":
                   sided_bands(rxf, FX, [0.0, 0.2, 0.4, 0.6, 0.8, 1.01])}
        q = A >= np.percentile(A, 75)
        raw["brightest_quartile_control_roundness"] = sided_bands(
            rxf[q], rr[q], [0.6, 0.8, 1.01])
        for key, y in (("roundness", rr), ("major_px", FX)):
            _, _, ssr = wls((onr, rrho), y, onr)
            cb, sb, ssb = wls((onr, rrho, rxf), y, onr)
            raw.setdefault("fits", {})[key] = {
                "rho_SE_units": abs(cb[1]) / sb[1], "x_SE_units": abs(cb[2]) / sb[2],
                "F_adding_x_to_radial": (ssr - ssb) / (ssb / (len(y) - 3))}
        sect = []
        az = np.degrees(np.arctan2(Yp - cy, Xp - cx))
        for lo in range(-180, 180, 45):
            m = (az >= lo) & (az < lo + 45)
            if m.sum() < 50:
                continue
            sect.append({"azimuth_centre_deg": lo + 22.5, "n": int(m.sum()),
                         "median_PA_deg": float(np.median(PA[m])),
                         "roundness": float(np.median(rr[m]))})
        raw["elongation_direction_by_field_azimuth"] = {
            "sectors": sect,
            "PA_spread_deg": float(np.std([s["median_PA_deg"] for s in sect])),
            "reading": "a fixed sensor direction predicts ~0 spread; a radial "
                       "optical term predicts the PA sweeping with azimuth"}
        raw["what_this_rules_OUT"] = [
            "within-member registration — the frame has not been registered",
            "the compose — the frame has not been composed",
            "a residual of the lensfun distortion model — the frame carries no "
            "correction, so there is no residual of one in it"]
        raw["what_remains_UNSEPARATED"] = (
            "the in-exposure family: an optical asymmetry, differential "
            "refraction, and the across-field gradient of the projected sky "
            "rate. All three are in the photons of a single exposure and none "
            "is removed by a better distortion model. The named discriminator "
            "(BACKLOG:one-sided-band) is hour-angle dependence, and the headers "
            "carry DATE-OBS but no site coordinates, so it needs designing.")
        raw["tension_with_an_inherited_claim"] = (
            "BACKLOG:compose-homography-smear records, from 136k stars over 3 "
            "frames x 6 sets x 2 nights, that 'the major-axis angle tracks the "
            "field azimuth in 7 of 8 zones in every set'. On these 3 frames of "
            "aug06/set-01 the median PA is near-CONSTANT across 8 azimuth "
            "sectors (spread in the record above), which is the trailing "
            "signature, not a rotating radial one. One of the two is measuring "
            "something the other is not — sample, channel (the raws solve on "
            "the half-res green plane) or convention. NOT resolved here; "
            "flagged so neither is quoted as settled.")
        out["correction_2_where_the_one_sided_term_lives"] = raw

    out["reports_only"] = "MEASUREMENT. No threshold, no verdict. Exits 0."
    json.dump(out, open(out_json, "w"), indent=1)
    print(f"  record -> {out_json}")
    c1 = out["correction_1_specification_robustness"]
    print(f"  tau {c1['tau_between_station']:.4f} vs median SE "
          f"{c1['median_measurement_se']:.4f} ({c1['tau_over_median_se']:.1f}x)")
    for k, v in c1["specifications"].items():
        if "rho_SE_units" in v:
            print(f"    {k:<38} x {v['x_SE_units']:4.2f} SE   rho {v['rho_SE_units']:4.2f} SE")
    for k, v in c1["nested_model_tests_unweighted"].items():
        print(f"    {k:<12} R2 rho-only {v['rho_only_R2']:.3f}  x-only {v['x_only_R2']:.3f}  "
              f"both {v['both_R2']:.3f}   F(+x)={v['F_adding_x_to_radial']:.1f}  "
              f"F(+rho)={v['F_adding_rho_to_one_sided']:.1f}")
    if "correction_2_where_the_one_sided_term_lives" in out:
        r = out["correction_2_where_the_one_sided_term_lives"]
        print(f"  RAWS: {r['stars']} stars, {r['frames']} single exposures")
        for b in r["model_free_sided_bands_roundness"]:
            print(f"    |x| {b['abs_x_band'][0]:.1f}-{b['abs_x_band'][1]:.1f}  "
                  f"-x {b['minus_x']:.3f}  +x {b['plus_x']:.3f}  {b['difference']:+.3f}")


if __name__ == "__main__":
    main()
