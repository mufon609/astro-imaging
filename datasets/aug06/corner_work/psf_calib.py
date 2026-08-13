#!/usr/bin/env python3
"""Is 0.4621 a physical constant or an estimator-dependent calibration?

THE CLAIM UNDER TEST. `sky_rate_gradient.json` attributes part of the corner
defect to the across-field gradient of the projected sky rate, and the
attribution turns on a conversion:

    major^2 - minor^2 = (2.3548^2 / 12) * L^2 = 0.4621 * L^2

That identity is EXACT — for SECOND MOMENTS. A uniform trail of length L has
variance L^2/12; convolution adds variances; converting variance to FWHM
multiplies by 2.3548^2. Nothing in it is arguable.

But Siril does not report second moments. `findstar` fits an elliptical GAUSSIAN
(profile=0 in the .lst header; `-moffat` is the only alternative and there is no
trail model). A trailed star is a top-hat convolved with the optical PSF, and on
this corpus L/sigma runs 1.65-2.19 — squarely the flat-topped regime, where a
Gaussian is the wrong shape and its fitted width is not the profile's second
moment. So 0.4621 is a CALIBRATION CONSTANT OF AN ESTIMATOR, not a parameter-free
physical one, and it is published as parameter-free.

WHY THIS IS DECISIVE RATHER THAN PEDANTIC. The bias is a function of L/sigma, and
L varies across the field as cos(dec) — which IS the regressor the attribution is
fitted against. The estimator's error is therefore CONFOUNDED WITH THE SIGNAL
UNDER TEST, and a slope measured through a biased estimator is not the slope of
the physical relation. The mechanism was already written down in this repo
(`docs/untracked-widefield-standards.md` F.2a) and was FILED, NOT ABSORBED — used
as grounds to prefer one conversion rather than as a reason both are uncalibrated.

WHAT THIS DOES. Renders synthetic trailed stars of KNOWN L, measures them with
the SAME Siril call the real measurement used, and regresses recovered
major^2 - minor^2 on L^2 to get the constant that Siril's estimator actually
delivers. No repo data is touched: the input is synthetic, so the true L is known
rather than inferred, which is the only way an estimator can be calibrated at all.

BRIGHT LINE. The synthetic frame is a FIXTURE, not a deliverable — the same
standing as the planted-orientation fixture in `pa_convention.py`. Every
measurement of it is Siril's `findstar`; in-house code renders the fixture and
fits the straight line. Nothing here reads, gates or tunes a product's pixels.

IT ALSO CLOSES AN UNCHECKED PREMISE for free. `pa_convention.py` assumes Siril's
reported `angle` is consistent with the X, Y it reports for the same star — read
from source and supported by a fixture that tests only in-house code, never by
pushing a source of KNOWN orientation through `findstar`. These fixtures have a
known trail direction, so the round trip is checkable here.

USAGE
    psf_calib.py --render     render the fixture frames only
    psf_calib.py --measure    run Siril findstar over them
    psf_calib.py              render, measure, fit, write the JSON record
"""

import json
import os
import subprocess
import sys

import numpy as np
from astropy.io import fits

HERE = os.path.dirname(os.path.abspath(__file__))
WORK = os.path.join(HERE, "psf_calib_work")
RAW = os.path.join(WORK, "raw")

# the corpus's own scale, from its tracked records: minor FWHM 2.01 px, so the
# optical sigma is 2.01/2.3548, and the sky-rate trail runs 1.407-1.867 px
SIGMA_PSF = 2.01 / 2.3548
L_VALUES = [round(v, 2) for v in np.arange(0.0, 2.81, 0.20)]
TRAIL_PA_DEG = 20.0          # a known, non-axis-aligned orientation
IMG_W, IMG_H = 1200, 1200
GRID = 56                    # star spacing, px
SUPERSAMPLE = 7
SKY = 300.0
GAIN = 1.0
CONSTANT_IDENTITY = 2.3548 ** 2 / 12.0


def render_frame(L, amp_lo=3000.0, amp_hi=30000.0, seed=0):
    """A frame of trailed stars: a top-hat of length L convolved with a Gaussian.

    The top-hat is integrated ANALYTICALLY along the trail (the convolution of a
    box with a Gaussian is a difference of error functions), so the only
    approximation is the pixel integration, done by 7x7 supersampling. Rendering
    the box by discrete convolution instead would add a second estimator between
    the truth and the measurement, which is exactly what this script exists to
    avoid.
    """
    from scipy.special import erf
    rng = np.random.default_rng(1000 + seed)
    img = np.full((IMG_H, IMG_W), SKY, dtype=np.float64)

    xs = np.arange(GRID, IMG_W - GRID, GRID, dtype=float)
    ys = np.arange(GRID, IMG_H - GRID, GRID, dtype=float)
    pa = np.radians(TRAIL_PA_DEG)
    ct, st = np.cos(pa), np.sin(pa)

    half = 9
    off = (np.arange(SUPERSAMPLE) + 0.5) / SUPERSAMPLE - 0.5
    truth = []
    for cy0 in ys:
        for cx0 in xs:
            # randomised sub-pixel phase — a fixed phase would let the pixel grid
            # alias with the trail length and fake a dependence on L
            cx = cx0 + rng.uniform(-0.5, 0.5)
            cy = cy0 + rng.uniform(-0.5, 0.5)
            amp = rng.uniform(amp_lo, amp_hi)

            i0, j0 = int(cy - half), int(cx - half)
            yy = np.arange(i0, i0 + 2 * half + 1)
            xx = np.arange(j0, j0 + 2 * half + 1)
            gx, gy = np.meshgrid(xx, yy)
            acc = np.zeros_like(gx, dtype=float)
            for dy in off:
                for dx in off:
                    u = (gx + dx - cx) * ct + (gy + dy - cy) * st   # along trail
                    v = -(gx + dx - cx) * st + (gy + dy - cy) * ct  # across
                    if L > 0:
                        prof = (erf((u + L / 2) / (SIGMA_PSF * np.sqrt(2)))
                                - erf((u - L / 2) / (SIGMA_PSF * np.sqrt(2)))) \
                               / (2.0 * L)
                    else:
                        prof = np.exp(-u ** 2 / (2 * SIGMA_PSF ** 2)) \
                               / (SIGMA_PSF * np.sqrt(2 * np.pi))
                    acc += prof * np.exp(-v ** 2 / (2 * SIGMA_PSF ** 2))
            acc /= SUPERSAMPLE ** 2
            acc *= amp / acc.max()
            img[i0:i0 + 2 * half + 1, j0:j0 + 2 * half + 1] += acc
            truth.append((cx, cy, amp))

    img = rng.poisson(np.clip(img, 0, None) * GAIN) / GAIN
    return np.clip(img, 0, 65535).astype(np.uint16), truth


def render_all():
    os.makedirs(RAW, exist_ok=True)
    meta = {}
    for k, L in enumerate(L_VALUES):
        img, truth = render_frame(L, seed=k)
        path = os.path.join(RAW, "t_%05d.fit" % (k + 1))
        fits.PrimaryHDU(img).writeto(path, overwrite=True)
        meta["t_%05d" % (k + 1)] = {"L_px": L, "n_planted": len(truth)}
        print("rendered L = %.2f px -> %s (%d stars)" % (L, os.path.basename(path),
                                                         len(truth)))
    json.dump(meta, open(os.path.join(WORK, "truth.json"), "w"), indent=1)
    return meta


def measure_all():
    """Siril does every measurement. Same call the real measurement used."""
    lines = ["requires 1.4.4", "set16bits", "setcompress 0", "setext fit",
             "cd %s" % RAW,
             "setfindstar reset -relax=on -sigma=0.5 -roundness=0.05 -maxR=1.0"]
    for k in range(len(L_VALUES)):
        lines.append("load t_%05d" % (k + 1))
        lines.append("findstar -out=%s/m_%05d.lst" % (WORK, k + 1))
    ssf = os.path.join(WORK, "measure.ssf")     # must live under $HOME: the
    open(ssf, "w").write("\n".join(lines) + "\n")   # flatpak has a private /tmp
    r = subprocess.run(["flatpak", "run", "--command=siril-cli", "org.siril.Siril",
                        "-d", RAW, "-s", ssf],
                       capture_output=True, text=True, timeout=3600)
    open(os.path.join(WORK, "siril.log"), "w").write(r.stdout + "\n" + r.stderr)
    if r.returncode != 0:
        print(r.stdout[-3000:], r.stderr[-3000:])
        raise SystemExit("siril exited %d — see psf_calib_work/siril.log"
                         % r.returncode)
    print("siril measured %d frames" % len(L_VALUES))


def fit_and_report():
    rows = []
    for k, L in enumerate(L_VALUES):
        p = os.path.join(WORK, "m_%05d.lst" % (k + 1))
        if not os.path.exists(p):
            continue
        d = np.loadtxt(p, comments="#", usecols=(3, 5, 6, 7, 8, 11))
        if d.ndim == 1 or len(d) < 20:
            continue
        A, x, y, maj, mnr, ang = d.T
        d2 = maj ** 2 - mnr ** 2
        rows.append({
            "L_px": L, "L_over_sigma": L / SIGMA_PSF, "n_measured": int(len(d)),
            "median_major_px": float(np.median(maj)),
            "median_minor_px": float(np.median(mnr)),
            "median_major2_minus_minor2": float(np.median(d2)),
            "predicted_by_identity": CONSTANT_IDENTITY * L ** 2,
            "median_angle_deg": float(np.median(ang)),
            "angle_error_vs_planted_deg": float(np.median(ang) - TRAIL_PA_DEG),
        })

    out = {
        "what_is_under_test": "whether major^2 - minor^2 = 0.4621 * L^2 holds for "
                              "Siril's elliptical-GAUSSIAN fit, or only for the "
                              "second moments the identity is derived from",
        "identity_constant": CONSTANT_IDENTITY,
        "optical_sigma_px": SIGMA_PSF,
        "sigma_source": "the corpus's own minor FWHM 2.01 px / 2.3548",
        "corpus_L_range_px": [1.407, 1.867],
        "corpus_L_over_sigma": [1.407 / SIGMA_PSF, 1.867 / SIGMA_PSF],
        "trail_pa_planted_deg": TRAIL_PA_DEG,
        "measurement": "Siril 1.4.4 findstar, setfindstar reset -relax=on "
                       "-sigma=0.5 -roundness=0.05 — the same call the real "
                       "measurement used",
        "rows": rows,
    }

    # the fitted constant: median(major^2-minor^2) regressed on L^2 through zero
    good = [r for r in rows if r["L_px"] > 0]
    L2 = np.array([r["L_px"] ** 2 for r in good])
    dv = np.array([r["median_major2_minus_minor2"] for r in good])
    out["fitted_constant_all_L"] = float((L2 @ dv) / (L2 @ L2))

    # and restricted to the range the corpus actually occupies, which is what
    # the attribution depends on
    band = [r for r in good if 1.35 <= r["L_px"] <= 1.95]
    if band:
        L2b = np.array([r["L_px"] ** 2 for r in band])
        dvb = np.array([r["median_major2_minus_minor2"] for r in band])
        out["fitted_constant_in_corpus_L_band"] = float((L2b @ dvb) / (L2b @ L2b))
        out["corpus_band_L_values"] = [r["L_px"] for r in band]

    # THE QUANTISATION FLOOR. The .lst writes FWHM to two decimals, so at ~2.12 px
    # the difference of squares is quantised in steps of about 2*2.12*0.01 =
    # 0.0424 px^2 — and the L = 0 frame, a perfectly ROUND star, reads exactly
    # 2.13^2 - 2.12^2 = 0.0425. That is a reporting floor, not an ellipticity, and
    # it inflates any constant fitted through the origin using small-L points.
    zero = [r for r in rows if r["L_px"] == 0.0]
    if zero:
        out["quantisation_floor_px2"] = zero[0]["median_major2_minus_minor2"]
        out["quantisation_floor_note"] = (
            "the L = 0 frame is a perfectly round star and still reads %.4f px^2, "
            "which is exactly %.2f^2 - %.2f^2. The .lst's two-decimal FWHM is the "
            "cause. Subtract it before fitting through the origin, or fit an "
            "intercept." % (zero[0]["median_major2_minus_minor2"],
                            zero[0]["median_major_px"], zero[0]["median_minor_px"]))

    # THE CONFOUND THE ORACLE NAMED: the bias is a function of L, and L varies
    # across the field as cos(dec), which IS the regressor. So what matters is not
    # the constant's offset but how much it MOVES across the corpus's own L range.
    local = [{"L_px": r["L_px"],
              "local_constant": r["median_major2_minus_minor2"] / r["L_px"] ** 2}
             for r in rows if r["L_px"] > 0]
    out["local_constant_per_L"] = local
    inband = [v["local_constant"] for v in local if 1.35 <= v["L_px"] <= 1.95]
    if inband:
        out["local_constant_across_corpus_L_range"] = {
            "min": float(min(inband)), "max": float(max(inband)),
            "fractional_variation": float((max(inband) - min(inband))
                                          / np.mean(inband)),
            "reads": "this is the size of the confound with cos(dec), because L "
                     "varies over the field exactly as the regressor does. "
                     "Compare it against the measurement's own fractional error, "
                     "0.416/2.548 = 16.3%.",
        }

    c = out.get("fitted_constant_in_corpus_L_band") or out["fitted_constant_all_L"]
    out["ratio_fitted_over_identity"] = float(c / CONSTANT_IDENTITY)
    out["what_it_does_to_the_attribution"] = (
        "sky_rate_gradient.json predicts a slope of 2.266 px^2 against cos^2(dec) "
        "from the identity constant and measures 2.548 +- 0.416 with the radial "
        "and one-sided terms held (0.68 sigma). Rescaling the PREDICTION by the "
        "ratio above gives %.3f px^2, which the same measurement sits %.2f sigma "
        "from." % (2.266 * out["ratio_fitted_over_identity"],
                   abs(2.548 - 2.266 * out["ratio_fitted_over_identity"]) / 0.416))
    out["angle_round_trip"] = {
        "planted_deg": TRAIL_PA_DEG,
        "max_abs_error_deg": float(max(abs(r["angle_error_vs_planted_deg"])
                                       for r in good)) if good else None,
        "closes": "the pa_convention.py premise that Siril's reported angle is "
                  "consistent with the X, Y it reports for the same star — "
                  "previously read from source and fixture-tested only against "
                  "in-house code, never through findstar itself",
    }
    out["reports_only"] = "MEASUREMENT. No threshold, no verdict. Exits 0."

    path = os.path.join(HERE, "psf_calib.json")
    json.dump(out, open(path, "w"), indent=1)
    print("wrote %s" % path)
    print()
    print("%-8s %-9s %8s %9s %9s %11s %9s"
          % ("L_px", "L/sigma", "n", "major", "minor", "maj2-min2", "identity"))
    for r in rows:
        print("%-8.2f %-9.2f %8d %9.3f %9.3f %11.4f %9.4f"
              % (r["L_px"], r["L_over_sigma"], r["n_measured"],
                 r["median_major_px"], r["median_minor_px"],
                 r["median_major2_minus_minor2"], r["predicted_by_identity"]))
    print()
    print("identity constant                 %.4f" % CONSTANT_IDENTITY)
    print("fitted constant, all L            %.4f" % out["fitted_constant_all_L"])
    if "fitted_constant_in_corpus_L_band" in out:
        print("fitted constant, corpus L band    %.4f"
              % out["fitted_constant_in_corpus_L_band"])
    print("ratio fitted / identity           %.4f" % out["ratio_fitted_over_identity"])
    print(out["what_it_does_to_the_attribution"])
    if out["angle_round_trip"]["max_abs_error_deg"] is not None:
        print("angle round trip: planted %.1f deg, max error %.2f deg"
              % (TRAIL_PA_DEG, out["angle_round_trip"]["max_abs_error_deg"]))
    return 0


def main():
    if "--render" in sys.argv:
        render_all()
        return 0
    if "--fit" in sys.argv:
        return fit_and_report()
    if "--measure" in sys.argv:
        measure_all()
        return fit_and_report()
    render_all()
    measure_all()
    return fit_and_report()


if __name__ == "__main__":
    sys.exit(main())
