#!/usr/bin/env python3
"""HEAD-TO-HEAD: PSFEx's field model against this repo's in-house spin-2 fit.

WHY. Four things this session corrected were all the same kind of error, and none
was a measurement mistake:
  - the PA "contradiction" was a statistic-and-population artefact;
  - "not coma" was a wrong reference exponent;
  - "theta0 rises, consistent with trailing" was a wrong flow model;
  - "star size is purely radial" was a linear fit averaging a sign flip to zero.
Every one is a BASIS or MODEL-SPECIFICATION artefact. We keep projecting a spin-2
field onto a basis we chose and then arguing about the projection. PSFEx returns
the field itself — eigen-PSFs varying polynomially across the frame — which is the
survey standard precisely because it does not require the basis to be picked
first.

THIS IS A MEASUREMENT, NOT AN ADOPTION. Nothing here touches a deliverable, no
homogenisation is run, and the bright line puts the burden on us: the question is
whether the in-house instrument is WORSE, and the answer has to be measured. The
PSF model is PSFEx's; source-extractor does the detection and the VIGNET
extraction; Siril did the debayer and the green-plane split. In-house code
reconstructs PSFEx's own model from its own coefficients, takes second moments,
and runs the SAME fits already applied to Siril's measurements.

THE BASIS ORDERING IS TRANSCRIBED FROM SOURCE, NOT GUESSED. psfex-3.21.1
src/wcs/poly.c poly_powers() is an exponent odometer; transcribing it gives, for
PSFVAR_DEGREES 2, the term order [1, X, X^2, Y, XY, Y^2] — X-major within each
power of Y, which is NOT the (1, X, Y, X^2, XY, Y^2) ordering a reader would
assume. Guessing it wrong transposes the whole field model.

THE FRAME. source-extractor reports Y_IMAGE in standard FITS bottom-up
coordinates; Siril's findstar reports the MIRROR of that (MEASURED: 300 of 300
brightest match under y -> H - y, 2 of 300 as reported). So PSFEx's field lives in
the opposite frame to every number in `pa_convention.json`, and comparing them
requires the mirror: phi -> -phi and e2 -> -e2, e1 unchanged. That transform is
not asserted — `--selftest` plants a known field, mirrors it, and requires the
recovered parameters to match.

REMOVAL CONDITION: this file exists to answer whether an official field-model tool
sees structure the in-house basis cannot express. If PSFEx (or a successor) is
adopted as the field-model instrument, the in-house spin-2 fit becomes the thing
being checked and this comparison inverts; if PSFEx reproduces the in-house fit
with nothing extra, the in-house fit stands and this file is a one-off record.
Either way it is not a pipeline component.
"""

import json
import os
import sys

import numpy as np
from astropy.io import fits

HERE = os.path.dirname(os.path.abspath(__file__))
WORK = os.path.normpath(os.path.join(HERE, "..", "set-01", "psfex_work"))
LSTDIR = os.path.normpath(os.path.join(HERE, "..", "set-01", "drift_work"))
sys.path.insert(0, HERE)
from pa_convention import (components, decompose, azimuth, wrap180,  # noqa: E402
                           fit_free_centre, read_lst)

CANVAS_W, CANVAS_H = 6064, 4040
FRAMES = [("g_00001", "f_00001"), ("g_00005", "f_00005"), ("g_00009", "f_00009")]


def poly_powers(deg, ndim=2):
    """Transcribed from psfex-3.21.1 src/wcs/poly.c poly_powers()."""
    group = [0] * ndim
    ncoeff = 1
    for d in range(ndim):
        ncoeff = ncoeff * (deg + d + 1) // (d + 1)
    expo = [0] * (ndim + 1)
    gexpo = [0] * (ndim + 1)
    gexpo[0] = deg
    if gexpo[group[0]]:
        gexpo[group[0]] -= 1
    powers = [tuple([0] * ndim)]
    expo[0] = 1
    for _ in range(ncoeff - 1):
        powers.append(tuple(expo[d] for d in range(ndim)))
        for d in range(ndim):
            old = gexpo[group[d]]
            gexpo[group[d]] = old - 1
            if old:
                expo[d] += 1
                break
            gexpo[group[d]] = expo[d]
            expo[d] = 0
    return powers


class PsfexModel:
    """PSFEx's own field model, reconstructed from its own coefficients."""

    def __init__(self, path):
        f = fits.open(path)
        h = f[1].header
        self.mask = np.array(f[1].data["PSF_MASK"][0], dtype=float)
        self.deg = int(h["POLDEG1"])
        self.zero = (float(h["POLZERO1"]), float(h["POLZERO2"]))
        self.scal = (float(h["POLSCAL1"]), float(h["POLSCAL2"]))
        self.samp = float(h["PSF_SAMP"])
        self.chi2 = float(h.get("CHI2", np.nan))
        self.accepted = int(h.get("ACCEPTED", -1))
        self.powers = poly_powers(self.deg)
        if len(self.powers) != self.mask.shape[0]:
            raise SystemExit("basis ordering gives %d terms but the model holds "
                             "%d — the transcription is wrong"
                             % (len(self.powers), self.mask.shape[0]))

    def at(self, x, y):
        """The PSF stamp at FITS image coordinates (x, y)."""
        X = (x - self.zero[0]) / self.scal[0]
        Y = (y - self.zero[1]) / self.scal[1]
        out = np.zeros(self.mask.shape[1:], dtype=float)
        for c, (a, b) in zip(self.mask, self.powers):
            out += c * (X ** a) * (Y ** b)
        return out

    def moments(self, x, y, nsig=2.5, iters=8):
        """Adaptive (Gaussian-weighted) second moments of the model stamp.

        Unweighted moments of a stamp diverge on the wings and are dominated by
        the stamp edge; a FIXED weight biases ellipticity toward zero. The
        adaptive scheme iterates the weight to match the object, which is the
        standard PSF-shape estimator and is what makes e1/e2 comparable to a
        fitted axis ratio rather than systematically smaller than it.
        """
        p = self.at(x, y)
        ny, nx = p.shape
        gy, gx = np.mgrid[0:ny, 0:nx].astype(float)
        p = np.clip(p, 0, None)
        if p.sum() <= 0:
            return None
        cx = (p * gx).sum() / p.sum()
        cy = (p * gy).sum() / p.sum()
        sig2 = 4.0
        for _ in range(iters):
            w = np.exp(-((gx - cx) ** 2 + (gy - cy) ** 2) / (2 * nsig ** 2 * sig2))
            q = p * w
            s = q.sum()
            if s <= 0:
                return None
            cx = (q * gx).sum() / s
            cy = (q * gy).sum() / s
            qxx = (q * (gx - cx) ** 2).sum() / s
            qyy = (q * (gy - cy) ** 2).sum() / s
            qxy = (q * (gx - cx) * (gy - cy)).sum() / s
            sig2 = max(0.5 * (qxx + qyy), 0.5)
        t = qxx + qyy
        if t <= 0:
            return None
        # in IMAGE pixels: the stamp is sampled at PSF_SAMP px per stamp pixel
        fwhm = 2.3548 * np.sqrt(0.5 * t) * self.samp
        return {"e1": (qxx - qyy) / t, "e2": 2 * qxy / t, "fwhm_px": fwhm}


def to_siril_frame(x, y, e1, e2):
    """FITS bottom-up -> Siril's mirrored frame. e1 invariant, e2 negates."""
    return x, (CANVAS_H - y), e1, -np.asarray(e2)


def fit_field(x, y, e1, e2, label, nboot=300):
    cx, cy = (CANVAS_W - 1) / 2.0, (CANVAS_H - 1) / 2.0
    phi = azimuth(x, y, cx, cy)
    rho = np.hypot(x - cx, y - cy) / np.hypot(cx, cy)
    flat = decompose(phi, e1, e2, None, nboot)
    grow = decompose(phi, e1, e2, rho, nboot)
    fc = fit_free_centre(x, y, e1, e2, CANVAS_W, CANVAS_H)
    return {"label": label, "n": int(len(x)),
            "fixed_amplitude": flat["fixed_amplitude"],
            "fixed_amplitude_SE_units": flat["fixed_amplitude_SE_units"],
            "fixed_direction_deg": flat["fixed_direction_theta0_deg"],
            "radial_R_flat": flat["radial_R"],
            "radial_flat_SE_units": flat["radial_SE_units"],
            "radial_R_rho": grow["radial_R"],
            "radial_rho_SE_units": grow["radial_SE_units"],
            "free_centre_offset_px": fc["offset_from_frame_centre_px"],
            "free_centre_offset_magnitude_px": fc["offset_magnitude_px"],
            "free_centre_1sigma_px": fc["centre_1sigma_px"],
            "F_free_centre_over_centred": fc["F_free_centre_over_centred"]}


def selftest():
    fails, notes = [], []

    def check(name, cond, detail=""):
        notes.append(("PASS" if cond else "FAIL") + "  " + name +
                     ("   " + detail if detail else ""))
        if not cond:
            fails.append(name)

    print("FIRE TEST — basis ordering and the frame mirror")
    print()
    p2 = poly_powers(2)
    check("basis ordering for degree 2 is the transcribed X-major order",
          p2 == [(0, 0), (1, 0), (2, 0), (0, 1), (1, 1), (0, 2)], str(p2))
    check("degree 3 gives 10 terms", len(poly_powers(3)) == 10)
    check("the ASSUMED ordering differs from the real one, so guessing matters",
          p2 != [(0, 0), (1, 0), (0, 1), (2, 0), (1, 1), (0, 2)],
          "the natural guess (1, X, Y, X^2, XY, Y^2) is NOT what PSFEx uses")

    # the mirror must leave a planted RADIAL field radial and invert a fixed one's
    # direction, exactly as a reflection should
    rng = np.random.default_rng(3)
    n = 20000
    x = rng.uniform(0, CANVAS_W, n)
    y = rng.uniform(0, CANVAS_H, n)
    cx, cy = (CANVAS_W - 1) / 2.0, (CANVAS_H - 1) / 2.0
    phi = np.arctan2(y - cy, x - cx)
    # noise is planted deliberately: a noiseless field fits exactly and would
    # exercise a degenerate branch the real data never reaches
    nz = lambda v: v + rng.normal(0, 0.05, n)
    for tag, e1, e2 in (("radial", nz(0.15 * np.cos(2 * phi)),
                         nz(0.15 * np.sin(2 * phi))),
                        ("fixed", nz(np.full(n, 0.15 * np.cos(np.radians(60.0)))),
                         nz(np.full(n, 0.15 * np.sin(np.radians(60.0)))))):
        a = fit_field(x, y, e1, e2, tag, nboot=80)
        mx, my, me1, me2 = to_siril_frame(x, y, e1, e2)
        b = fit_field(mx, my, me1, me2, tag + ":mirrored", nboot=80)
        if tag == "radial":
            check("mirror leaves a planted RADIAL amplitude invariant",
                  abs(a["radial_R_flat"] - b["radial_R_flat"]) < 0.002,
                  "R %.4f -> %.4f" % (a["radial_R_flat"], b["radial_R_flat"]))
        else:
            check("mirror leaves a planted FIXED amplitude invariant and "
                  "NEGATES its direction",
                  abs(a["fixed_amplitude"] - b["fixed_amplitude"]) < 0.002
                  and abs(wrap180(a["fixed_direction_deg"]
                                  + b["fixed_direction_deg"])) < 1.0,
                  "F %.4f -> %.4f, direction %+.2f -> %+.2f"
                  % (a["fixed_amplitude"], b["fixed_amplitude"],
                     a["fixed_direction_deg"], b["fixed_direction_deg"]))

    # a planted decentred field must survive the mirror with the offset's y sign
    # flipped and its x unchanged
    ox, oy = 1200.0, -700.0
    phio = np.arctan2(y - (cy + oy), x - (cx + ox))
    e1 = 0.15 * np.cos(2 * phio) + rng.normal(0, 0.05, n)
    e2 = 0.15 * np.sin(2 * phio) + rng.normal(0, 0.05, n)
    a = fit_field(x, y, e1, e2, "decentred", nboot=80)
    mx, my, me1, me2 = to_siril_frame(x, y, e1, e2)
    b = fit_field(mx, my, me1, me2, "decentred:mirrored", nboot=80)
    check("mirror maps a planted decentring to (+dx, -dy)",
          abs(a["free_centre_offset_px"][0] - b["free_centre_offset_px"][0]) < 60
          and abs(a["free_centre_offset_px"][1]
                  + b["free_centre_offset_px"][1]) < 60,
          "(%+.0f, %+.0f) -> (%+.0f, %+.0f), planted (%+.0f, %+.0f)"
          % (*a["free_centre_offset_px"], *b["free_centre_offset_px"], ox, oy))

    print()
    for nline in notes:
        print("  " + nline)
    print()
    if fails:
        print("SELFTEST FAILED: %d of %d" % (len(fails), len(notes)))
        return 1
    print("SELFTEST PASSED: %d of %d" % (len(notes), len(notes)))
    return 0


def main():
    if "--selftest" in sys.argv:
        return selftest()

    rec = {
        "what": "PSFEx 3.21.1 field model against the in-house spin-2 fit, on "
                "the SAME three single RAWs the corner work used "
                "(aug06/set-01 DSC_6239, DSC_6339, DSC_6439)",
        "scope": "MEASUREMENT, not adoption. No homogenisation, nothing touching "
                 "a deliverable.",
        "chain": "Siril debayer + green-plane split -> source-extractor 2.28.2 "
                 "with VIGNET(35,35) -> PSFEx 3.21.1 -> in-house reconstruction "
                 "of PSFEx's own model, adaptive second moments, and the same "
                 "fits used on Siril's measurements",
        "psfex_provenance": "official Debian bookworm binary, sha256 "
                            "749bd883d8a122a14d06e47f138cb36eae862e4090126154d1e"
                            "2de3b8a96ab78, verified against the archive Packages "
                            "index; extracted into a scratchpad with its deps, "
                            "nothing installed system-wide",
        "degrees": {},
    }

    for deg in (2, 3):
        dd = os.path.join(WORK, "deg%d" % deg)
        if not os.path.isdir(dd):
            continue
        per, allrows = {}, []
        for gname, fname in FRAMES:
            pf = os.path.join(dd, gname + ".psf")
            lf = os.path.join(LSTDIR, fname + ".lst")
            if not (os.path.exists(pf) and os.path.exists(lf)):
                continue
            m = PsfexModel(pf)
            sir, _ = read_lst(lf)
            # evaluate PSFEx's model AT EACH SIRIL STAR, in FITS coordinates
            sx = sir[:, 1]
            sy = CANVAS_H - sir[:, 2]          # Siril -> FITS
            keep = np.arange(0, len(sir), max(1, len(sir) // 2500))
            rows = []
            for i in keep:
                mo = m.moments(sx[i], sy[i])
                if mo:
                    rows.append((sx[i], sy[i], mo["e1"], mo["e2"],
                                 mo["fwhm_px"], i))
            if not rows:
                continue
            a = np.array(rows)
            px, py, pe1, pe2, pfw, idx = a.T
            idx = idx.astype(int)
            # Siril's own shape for the same stars, in Siril's frame
            se, se1, se2 = components(sir[idx, 3], sir[idx, 4], sir[idx, 5])
            # PSFEx into Siril's frame for a like-for-like comparison
            mx, my, me1, me2 = to_siril_frame(px, py, pe1, pe2)
            per[gname] = {
                "psfex_chi2_dof": m.chi2, "psfex_accepted": m.accepted,
                "psf_samp": m.samp, "n_compared": len(a),
                "psfex_median_fwhm_px": float(np.median(pfw)),
                "siril_median_fwhm_px": float(np.median(sir[idx, 3])),
                "corr_e1_psfex_vs_siril": float(np.corrcoef(me1, se1)[0, 1]),
                "corr_e2_psfex_vs_siril": float(np.corrcoef(me2, se2)[0, 1]),
                "psfex_field_fit": fit_field(mx, my, me1, me2,
                                             "%s deg%d" % (gname, deg)),
                "siril_same_stars_fit": fit_field(
                    sir[idx, 1], sir[idx, 2], se1, se2, "%s siril" % gname),
            }
            allrows.append((mx, my, me1, me2, sir[idx, 1], sir[idx, 2], se1, se2))
        if allrows:
            cat = [np.concatenate([r[k] for r in allrows]) for k in range(8)]
            per["POOLED"] = {
                "n": int(len(cat[0])),
                "corr_e1": float(np.corrcoef(cat[2], cat[6])[0, 1]),
                "corr_e2": float(np.corrcoef(cat[3], cat[7])[0, 1]),
                "psfex_field_fit": fit_field(cat[0], cat[1], cat[2], cat[3],
                                             "pooled psfex deg%d" % deg),
                "siril_field_fit": fit_field(cat[4], cat[5], cat[6], cat[7],
                                             "pooled siril"),
            }
        rec["degrees"]["deg%d" % deg] = per

    path = os.path.join(HERE, "psfex_compare.json")
    json.dump(rec, open(path, "w"), indent=1)
    print("wrote %s" % path)
    for dk, dv in rec["degrees"].items():
        p = dv.get("POOLED")
        if not p:
            continue
        pf, sf = p["psfex_field_fit"], p["siril_field_fit"]
        print()
        print("=== %s, pooled over 3 frames, n=%d ===" % (dk, p["n"]))
        print("  star-by-star correlation with Siril:  e1 %+.3f   e2 %+.3f"
              % (p["corr_e1"], p["corr_e2"]))
        print("  %-8s %12s %12s %14s %16s"
              % ("", "fixed F", "radial R_rho", "free centre", "F(free/centred)"))
        for nm, f in (("PSFEx", pf), ("Siril", sf)):
            print("  %-8s %12s %12s %14s %16.1f"
                  % (nm,
                     "%.4f (%.0f)" % (f["fixed_amplitude"],
                                      f["fixed_amplitude_SE_units"]),
                     "%.4f (%.0f)" % (f["radial_R_rho"],
                                      f["radial_rho_SE_units"]),
                     "(%+.0f,%+.0f) %.0fpx" % (*f["free_centre_offset_px"],
                                               f["free_centre_offset_magnitude_px"]),
                     f["F_free_centre_over_centred"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
