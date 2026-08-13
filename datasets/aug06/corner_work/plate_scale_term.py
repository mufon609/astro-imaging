#!/usr/bin/env python3
"""Does the LOCAL plate scale absorb part of the unattributed radial term?

    plate_scale_term.py <corner_quality.json> <out.json>

THE DEFECT BEING CORRECTED. `sky_rate_gradient.py` converts the sky trail from
arcsec to pixels with ONE plate scale — 16.979 "/px from `acquisition.json` —
for all 148 stations. But a rectilinear lens maps r = f*tan(theta), so the local
scale is not constant across a 28.6-degree field: radially it goes as sec^2(theta)
and tangentially as sec(theta). Two consequences, neither represented:
  (a) the predicted trail IN PIXELS is under-predicted toward the edges, and
  (b) the trail's pixel length becomes DIRECTION-dependent.
Both are radial functions of position, so both are confounded with exactly the
radial term the corner work has been unable to attribute.

WHY THIS IS NOT A THEORY CORRECTION. The sec^2 figure is what the IDEAL gnomonic
model predicts. What is used here instead is each member's OWN SOLVED WCS — the
full solution including its SIP terms — differentiated numerically at each
station. That is the empirical local scale of the actual optic as the plate solve
measured it, and it needs no assumption about how well the lens obeys r = f tan.
MEASURED on sub_01: 17.079 "/px at the frame centre against 16.08-16.13 at the
corners, so the pixel trail is ~6% LONGER at the corner than the global constant
implies, and ~12% in L^2.

THE TRAIL DIRECTION IS THE ONE THAT MATTERS. A star drifts along constant
declination, so the relevant scale is the one along the local +RA direction, not
the mean scale and not the radial one. The Jacobian gives that directly: invert
d(world)/d(pixel) and push a unit RA displacement through it. That also picks up
(b) for free — the direction dependence is in the Jacobian, not bolted on.

THREE OUTCOMES, STATED BEFORE RUNNING:
  ATTRIBUTION   the correction absorbs a meaningful fraction of the radial
                coefficient, and part of the unattributed term is this.
  CLEANER NULL  it absorbs a negligible fraction; the radial term survives and
                is better established for having survived a real subtraction.
  ILL-DETERMINED the correction is itself too uncertain to subtract, in which
                case say so rather than reporting whichever way it moved.

PLAYBOOK SHAPE C — our own result not applied one stage over.
`docs/untracked-widefield-standards.md` F.2b already computed these exact factors
and they were FILED, NOT ABSORBED.

Every major/minor is Siril `findstar`'s via `shape_at_sky.py`; every declination
and every local scale is the member's own solved WCS. In-house code holds the
trail arithmetic and the fits. Reads no pixel. Reports only; exits 0.
"""

import json
import os
import sys
import warnings

import numpy as np
from astropy.io import fits
from astropy.wcs import WCS

HERE = os.path.dirname(os.path.abspath(__file__))
SIDEREAL_ARCSEC_PER_S = 15.041
FWHM_PER_SIGMA = 2.3548
UNIFORM_TRAIL_VARIANCE = 1 / 12.0
CONV = FWHM_PER_SIGMA ** 2 * UNIFORM_TRAIL_VARIANCE      # 0.46209


def jacobian(wcs, x, y, d=1.0):
    """d(RA*cos dec, dec)/d(x, y) in arcsec/px, by finite difference.

    Numerical rather than analytic so it uses the FULL solution — SIP and all —
    instead of just the CD matrix, which is the linear part and therefore has
    exactly none of the field-dependent behaviour under test.
    """
    c0 = wcs.pixel_to_world(x, y)
    cx = wcs.pixel_to_world(x + d, y)
    cy = wcs.pixel_to_world(x, y + d)
    cosd = np.cos(np.radians(c0.dec.deg))

    def dra(a, b):
        return ((a.ra.deg - b.ra.deg + 180) % 360 - 180) * cosd * 3600.0
    return np.array([[dra(cx, c0) / d, dra(cy, c0) / d],
                     [(cx.dec.deg - c0.dec.deg) * 3600.0 / d,
                      (cy.dec.deg - c0.dec.deg) * 3600.0 / d]])


def trail_px_local(wcs, x, y, arcsec):
    """Pixels spanned by a sky displacement of `arcsec` along +RA at (x, y)."""
    j = jacobian(wcs, x, y)
    if abs(np.linalg.det(j)) < 1e-12:
        return None
    return float(np.hypot(*(np.linalg.inv(j) @ np.array([arcsec, 0.0]))))


def scale_along_ra(wcs, x, y):
    """arcsec per pixel along the local +RA direction."""
    t = trail_px_local(wcs, x, y, 1.0)
    return None if not t else 1.0 / t


def stations(rec):
    """Same station table as sky_rate_gradient, plus the WCS each one sits in."""
    out = []
    blocks = list(rec["member_rays"].items()) + list(rec["member_azimuth"].items())
    blocks += [("member_%s" % t, v)
               for t, v in rec["member_radial_profile"].items()]
    cache = {}
    for name, rows in blocks:
        j = os.path.join(HERE, "shape_%s.json" % name)
        if not os.path.exists(j):
            continue
        rc = json.load(open(j))
        img = rc["image"]
        if img not in cache:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                h = fits.getheader(img)
                cache[img] = (WCS(h, naxis=2), int(h["NAXIS1"]), int(h["NAXIS2"]))
        wcs, W, H = cache[img]
        by = {r["label"]: r for r in rows}
        for r in rc["positions"]:
            if r.get("out_of_canvas") or r["label"] not in by:
                continue
            x, y, w, hh = r["crop"]
            xc, yc = x + w / 2, (H - y - hh) + hh / 2
            s = by[r["label"]]
            out.append({"series": name, "label": r["label"], "dec": r["dec"],
                        "xc": xc, "yc": yc, "image": img, "wcs": wcs,
                        "xf": (xc - (W - 1) / 2) / (W / 2),
                        "rho": float(np.hypot(xc - (W - 1) / 2, yc - (H - 1) / 2)
                                     / np.hypot((W - 1) / 2, (H - 1) / 2)),
                        "major": s["major_px"], "minor": s["minor_px"]})
    return out


def ols(cols, y):
    X = np.column_stack(cols)
    c, *_ = np.linalg.lstsq(X, y, rcond=None)
    r = y - X @ c
    se = np.sqrt(np.diag(np.linalg.inv(X.T @ X)) * r.var(ddof=X.shape[1]))
    return c, se, 1 - (r ** 2).sum() / float(((y - y.mean()) ** 2).sum())


def selftest():
    """The Jacobian must recover a KNOWN scale from a KNOWN WCS."""
    fails, notes = [], []

    def check(n, c, d=""):
        notes.append(("PASS" if c else "FAIL") + "  " + n + ("   " + d if d else ""))
        if not c:
            fails.append(n)

    # a clean TAN WCS with a known scale and no rotation
    scale_deg = 16.979 / 3600.0
    h = fits.Header()
    h["NAXIS"] = 2
    h["NAXIS1"], h["NAXIS2"] = 6000, 4000
    h["CTYPE1"], h["CTYPE2"] = "RA---TAN", "DEC--TAN"
    h["CRPIX1"], h["CRPIX2"] = 3000.0, 2000.0
    h["CRVAL1"], h["CRVAL2"] = 300.0, 42.0
    h["CD1_1"], h["CD1_2"] = -scale_deg, 0.0
    h["CD2_1"], h["CD2_2"] = 0.0, scale_deg
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        w = WCS(h, naxis=2)

    s0 = scale_along_ra(w, 3000.0, 2000.0)
    check("Jacobian recovers the planted scale at the tangent point",
          abs(s0 - 16.979) < 0.01, "planted 16.979, got %.4f arcsec/px" % s0)

    # A TAN projection is r = f*tan(theta), so the scale MUST fall toward the
    # edge in the tangent plane. This is the gnomonic term the correction is for,
    # and the fixture confirms the code sees it rather than assuming it.
    off = 2800.0
    theta = np.degrees(np.arctan(off * scale_deg * np.pi / 180.0 / (np.pi / 180.0)
                                 * np.pi / 180.0))
    s1 = scale_along_ra(w, 3000.0 + off, 2000.0)
    check("scale VARIES across a pure TAN field (the gnomonic term exists)",
          abs(s1 - s0) / s0 > 0.005,
          "centre %.4f -> +%.0f px %.4f arcsec/px (%.2f%%)"
          % (s0, off, s1, 100 * (s1 - s0) / s0))
    check("and it FALLS outward, as r = f tan(theta) requires",
          s1 < s0, "%.4f < %.4f" % (s1, s0))

    # a trail of known angular length must convert to the right pixel count
    L = 15.041 * np.cos(np.radians(42.0)) * 2.5
    tp = trail_px_local(w, 3000.0, 2000.0, L)
    check("trail arcsec -> px at the tangent point matches the global arithmetic",
          abs(tp - L / 16.979) < 0.01,
          "%.4f px against %.4f px" % (tp, L / 16.979))

    # a DEGENERATE wcs must return None rather than a number
    h2 = h.copy()
    h2["CD1_1"] = h2["CD2_2"] = h2["CD1_2"] = h2["CD2_1"] = 0.0
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        try:
            bad = trail_px_local(WCS(h2, naxis=2), 3000.0, 2000.0, L)
        except Exception:
            bad = None
    check("a degenerate WCS returns None rather than a plausible number",
          bad is None, "got %s" % bad)

    for n in notes:
        print("  " + n)
    print()
    if fails:
        print("SELFTEST FAILED: %d of %d" % (len(fails), len(notes)))
        return 1
    print("SELFTEST PASSED: %d of %d" % (len(notes), len(notes)))
    return 0


def main():
    if "--selftest" in sys.argv:
        return selftest()

    rec = json.load(open(sys.argv[1]))
    out_json = os.path.abspath(sys.argv[2])
    acq = json.load(open(os.path.join(HERE, "..", "set-01",
                                      "acquisition.json")))["exif"]
    texp, gscale = acq["exposure_s"], acq["pixel_scale_arcsec"]

    st = stations(rec)
    keep = []
    for s in st:
        sc = scale_along_ra(s["wcs"], s["xc"], s["yc"])
        if sc:
            s["scale_local"] = sc
            keep.append(s)
    st = keep

    dec = np.array([s["dec"] for s in st])
    maj = np.array([s["major"] for s in st])
    mnr = np.array([s["minor"] for s in st])
    rho = np.array([s["rho"] for s in st])
    xf = np.array([s["xf"] for s in st])
    loc = np.array([s["scale_local"] for s in st])
    one = np.ones(len(dec))
    aniso = maj ** 2 - mnr ** 2

    L_arcsec = SIDEREAL_ARCSEC_PER_S * np.cos(np.radians(dec)) * texp
    trail_global = L_arcsec / gscale
    trail_local = L_arcsec / loc
    pred_global = CONV * trail_global ** 2
    pred_local = CONV * trail_local ** 2

    # how much of the RADIAL coefficient does the correction take?
    fits_ = {}
    for nm, pred in (("global_scale", pred_global), ("local_scale", pred_local)):
        c, se, R2 = ols((one, pred, rho, xf), aniso)
        fits_[nm] = {
            "pred_coef": c[1], "pred_SE_units": abs(c[1]) / se[1],
            "rho_coef": c[2], "rho_SE_units": abs(c[2]) / se[2],
            "x_coef": c[3], "x_SE_units": abs(c[3]) / se[3], "R2": R2}
    dr = fits_["local_scale"]["rho_coef"] - fits_["global_scale"]["rho_coef"]

    # and the direct per-station test: measured against predicted, slope 1
    direct = {}
    for nm, pred in (("global_scale", pred_global), ("local_scale", pred_local)):
        c, se, R2 = ols((one, pred), aniso)
        direct[nm] = {"slope": c[1], "se": se[1],
                      "sigma_from_unity": abs(c[1] - 1.0) / se[1], "R2": R2}

    out = {
        "what": "does the position-dependent plate scale absorb part of the "
                "unattributed radial term?",
        "the_defect": "sky_rate_gradient.py converts the sky trail to pixels "
                      "with ONE scale, %.3f arcsec/px, for all stations. A "
                      "rectilinear lens has a field-dependent local scale, and "
                      "the variation is radial — confounded with the radial "
                      "term." % gscale,
        "the_correction": "each station's LOCAL scale along the +RA (trail) "
                          "direction, from its own member's solved WCS "
                          "differentiated numerically — the full solution "
                          "including SIP, not the CD matrix and not an ideal "
                          "sec^2 model",
        "stations": len(st),
        "scale_arcsec_per_px": {
            "global_constant_used_before": gscale,
            "local_min": float(loc.min()), "local_max": float(loc.max()),
            "local_median": float(np.median(loc)),
            "spread_percent": float(100 * (loc.max() - loc.min())
                                    / np.median(loc)),
            "corr_with_rho": float(np.corrcoef(loc, rho)[0, 1]),
        },
        "predicted_trail_px": {
            "global_min_max": [float(trail_global.min()),
                               float(trail_global.max())],
            "local_min_max": [float(trail_local.min()), float(trail_local.max())],
            "median_ratio_local_over_global": float(
                np.median(trail_local / trail_global)),
            "max_ratio": float((trail_local / trail_global).max()),
        },
        "predicted_anisotropy_px2": {
            "global_median": float(np.median(pred_global)),
            "local_median": float(np.median(pred_local)),
            "median_ratio": float(np.median(pred_local / pred_global)),
        },
        "joint_fit_aniso_on_pred_rho_x": fits_,
        "HOW_MUCH_OF_THE_RADIAL_TERM_IT_ABSORBS": {
            "rho_coef_with_global_scale": fits_["global_scale"]["rho_coef"],
            "rho_coef_with_local_scale": fits_["local_scale"]["rho_coef"],
            "absolute_change_px2": dr,
            "fraction_of_the_radial_coefficient": float(
                dr / fits_["global_scale"]["rho_coef"])
            if fits_["global_scale"]["rho_coef"] else None,
        },
        "direct_test_measured_vs_predicted_slope_should_be_1": direct,
        "reports_only": "MEASUREMENT. No threshold, no verdict. Exits 0.",
    }
    json.dump(out, open(out_json, "w"), indent=1)
    print("wrote %s" % out_json)
    print()
    print("local scale %.4f..%.4f arcsec/px (median %.4f) against the global "
          "%.3f — spread %.2f%%, corr with rho %+.3f"
          % (loc.min(), loc.max(), np.median(loc), gscale,
             out["scale_arcsec_per_px"]["spread_percent"],
             out["scale_arcsec_per_px"]["corr_with_rho"]))
    print("predicted trail px: global %.3f..%.3f, local %.3f..%.3f "
          "(median ratio %.4f)"
          % (trail_global.min(), trail_global.max(), trail_local.min(),
             trail_local.max(),
             out["predicted_trail_px"]["median_ratio_local_over_global"]))
    print()
    print("%-14s %14s %16s %14s %8s"
          % ("scale used", "pred coef", "RADIAL rho coef", "x coef", "R2"))
    for nm in ("global_scale", "local_scale"):
        f = fits_[nm]
        print("%-14s %14s %16s %14s %8.4f"
              % (nm, "%.3f (%.1f SE)" % (f["pred_coef"], f["pred_SE_units"]),
                 "%.4f (%.1f SE)" % (f["rho_coef"], f["rho_SE_units"]),
                 "%.4f (%.1f SE)" % (f["x_coef"], f["x_SE_units"]), f["R2"]))
    print()
    print("radial coefficient moves %+.4f px^2 (%.1f%% of it)"
          % (dr, 100 * dr / fits_["global_scale"]["rho_coef"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
