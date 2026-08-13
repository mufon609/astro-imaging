#!/usr/bin/env python3
"""Falsify the tracked observing-site coordinates against the corpus's own solves.

WHY THIS EXISTS. `scripts/setup/site.json` carries owner-supplied coordinates
whose provenance chain is owner -> chat -> transcription -> tracked file. No step
in that chain has an independent check, and a coordinate typo would be SILENT and
load-bearing: it propagates into every altitude, hour angle and parallactic angle
derived downstream, and one of those closed a refraction branch.

WHAT THIS DOES, AND WHAT IT CANNOT DO — read the second half before quoting it.
It is a FALSIFICATION test, not a derivation. For every solved product carrying a
DATE-OBS and a plate-solved centre, it computes the target's altitude and hour
angle at the supplied site, then recomputes them under the transcription errors
that are actually plausible — a longitude sign flip, a latitude/longitude
transposition, a shifted decimal point, a transposed digit. An error that puts a
photographed target below the horizon is refuted outright.

  IT CATCHES:      sign errors, whole-coordinate transposition, decimal-place
                   errors — the failure modes that move the answer by tens of
                   degrees.
  IT DOES NOT CATCH: sub-degree digit errors. MEASURED: transposing a digit in the
                   latitude (REDACTED_SITELAT -> REDACTED_SITELAT_PLUS, a 0.63 deg error) moves every
                   altitude by only 0.53 deg, and the same in the longitude by
                   0.07 deg. Nothing here would notice.

So a PASS bounds the transcription at roughly the degree level and no better. The
check that closes it properly is a DERIVATION: field rotation between per-frame
solves constrains cos(lat)*cos(azimuth)*sec(altitude), so latitude and LST are
recoverable from the corpus alone and can be compared against the supplied value.
That needs per-frame plate solves, which do not exist yet — it is a real build,
not a fold-in, and `verified` in site.json stays false until it runs.

This reads FITS HEADERS only (DATE-OBS, CRVAL1/2 written by the plate solve) and
never a deliverable's pixels.
"""

import glob
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.normpath(os.path.join(HERE, "..", ".."))
SITE = os.path.join(HERE, "site.json")

# the transcription errors worth testing, as (label, lat, lon) builders
PERTURBATIONS = [
    ("longitude SIGN flipped", lambda a, o: (a, -o)),
    ("lat/long TRANSPOSED", lambda a, o: (o, a)),
    ("latitude decimal shifted", lambda a, o: (a / 10.0, o)),
    ("latitude digit transposed", lambda a, o: (a + 0.63, o)),
    ("longitude digit transposed", lambda a, o: (a, o + 0.09)),
]


def solved_products():
    """Every solved stack with a timestamp, and its FIELD CENTRE — evaluated.

    WHICH POINTING, and it matters: three different "centres" live in this tree
    and they disagree by up to 3.2 deg, which is larger than the bound this whole
    script claims to establish.

      CRVAL1/2            the WCS TANGENT POINT, not the pointing. CRPIX is NOT
                          at the image centre on these solves — MEASURED offsets
                          of 40 to 906 px — and CRVAL values repeat across
                          different sets and nights, so the solver is placing the
                          tangent point somewhere discrete. A first version of
                          this script used CRVAL and was WRONG by up to 3 deg.
      fingerprint         `field_center` in datasets/<session>/<set>/
                          fingerprint.json sits 0.7-3.2 deg from the true centre,
                          almost all of it in RA and always LOWER. A set sweeps
                          6.24 deg of RA in its 1497 s, and these offsets are
                          about half of that, which is what you get if one
                          quantity is the FIRST member and the other the set
                          mean. CANDIDATE mechanism, not confirmed here.
      WCS at image centre what this uses. Evaluating the full solution (SIP and
                          all) at the central pixel is the pointing by
                          construction, and it agrees with the header's own
                          OBJCTRA/OBJCTDEC to 0.000-0.031 deg on 7 of 9 products
                          and 0.13-0.18 deg on the other two.
    """
    import warnings
    from astropy.io import fits
    from astropy.wcs import WCS
    out = []
    pat = os.path.join(REPO, "web", "results", "*", "stack_set-*_wcs.fit")
    for p in sorted(glob.glob(pat)):
        try:
            h = fits.getheader(p)
        except OSError:
            continue
        if not (h.get("DATE-OBS") and h.get("CRVAL1") is not None):
            continue
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            w = WCS(h, naxis=2)
            c = w.pixel_to_world((h["NAXIS1"] - 1) / 2.0,
                                 (h["NAXIS2"] - 1) / 2.0)
        out.append({"product": os.path.relpath(p, REPO),
                    "date_obs": h["DATE-OBS"],
                    "ra_deg": float(c.ra.deg), "dec_deg": float(c.dec.deg),
                    "pointing_source": "WCS evaluated at the central pixel"})
    return out


def horizon(prods, lat, lon):
    from astropy.coordinates import SkyCoord, EarthLocation, AltAz
    from astropy.time import Time
    import astropy.units as u
    loc = EarthLocation.from_geodetic(lon=lon * u.deg, lat=lat * u.deg,
                                      height=0 * u.m)
    rows = []
    for d in prods:
        t = Time(d["date_obs"], scale="utc")
        aa = SkyCoord(d["ra_deg"] * u.deg, d["dec_deg"] * u.deg).transform_to(
            AltAz(obstime=t, location=loc))
        ha = (t.sidereal_time("apparent",
                              longitude=lon * u.deg).deg - d["ra_deg"]) / 15.0
        rows.append({"product": d["product"], "altitude_deg": float(aa.alt.deg),
                     "hour_angle_h": float((ha + 12) % 24 - 12)})
    return rows


def main():
    site = json.load(open(SITE))
    lat, lon = site["sitelat_deg"], site["sitelong_deg"]
    prods = solved_products()
    if not prods:
        print("no solved products with DATE-OBS + CRVAL found — nothing to "
              "falsify against")
        return 1

    base = horizon(prods, lat, lon)
    alts = [r["altitude_deg"] for r in base]
    has = [abs(r["hour_angle_h"]) for r in base]
    print("SUPPLIED SITE  lat %+.6f  lon %+.6f   (%d solved products)"
          % (lat, lon, len(prods)))
    for r in base:
        print("  %-56s altitude %6.2f deg   HA %+6.2f h"
              % (os.path.basename(r["product"]), r["altitude_deg"],
                 r["hour_angle_h"]))
    print("  altitude range %.2f..%.2f deg, max |HA| %.2f h"
          % (min(alts), max(alts), max(has)))

    result = {
        "supplied": {"sitelat_deg": lat, "sitelong_deg": lon},
        "n_solved_products": len(prods),
        "altitude_range_deg": [min(alts), max(alts)],
        "max_abs_hour_angle_h": max(has),
        "all_above_horizon": bool(min(alts) > 0),
        "perturbations": [],
    }

    print()
    print("FALSIFICATION — the same products under plausible transcription errors")
    for label, fn in PERTURBATIONS:
        pa, po = fn(lat, lon)
        rows = horizon(prods, pa, po)
        pal = [r["altitude_deg"] for r in rows]
        shift = max(abs(a["altitude_deg"] - b["altitude_deg"])
                    for a, b in zip(rows, base))
        refuted = min(pal) < 0
        result["perturbations"].append({
            "label": label, "lat": pa, "lon": po,
            "altitude_range_deg": [min(pal), max(pal)],
            "max_altitude_shift_deg": shift,
            "refuted_target_below_horizon": bool(refuted)})
        print("  %-30s altitudes %7.2f..%7.2f   max shift %6.2f deg%s"
              % (label, min(pal), max(pal), shift,
                 "   REFUTED (below horizon)" if refuted else ""))

    caught = [p for p in result["perturbations"]
              if p["refuted_target_below_horizon"]]
    missed = [p for p in result["perturbations"]
              if p["max_altitude_shift_deg"] < 1.0]
    result["verdict"] = (
        "The supplied coordinates put every photographed target %.1f-%.1f deg "
        "above the horizon within %.2f h of the meridian, which is consistent "
        "with a deliberate observing plan. %d of %d plausible transcription "
        "errors are REFUTED outright (target below the horizon). %d are NOT "
        "detectable here, shifting every altitude by under 1 deg — so this "
        "bounds the transcription at roughly the DEGREE level and no better. "
        "It is not a derivation and does not set verified=true."
        % (min(alts), max(alts), max(has), len(caught),
           len(result["perturbations"]), len(missed)))
    result["what_would_close_it"] = site.get("provenance", {}).get(
        "the_check_that_closes_it")
    result["which_pointing_this_consumed_and_why_it_matters"] = (
        "the WCS evaluated at the central pixel — the pointing by construction, "
        "and it agrees with the header's own OBJCTRA/OBJCTDEC to 0.000-0.031 deg "
        "on 7 of 9 products. THE TREE CARRIES THREE DIFFERENT 'CENTRES' AND THEY "
        "DISAGREE BY UP TO 3.2 deg, which is LARGER than the degree-level bound "
        "this script establishes — so the bound is only as good as the pointing "
        "fed in, and naming it is part of the result. CRVAL is the WCS tangent "
        "point and is NOT the pointing (CRPIX sits 40-906 px off the image "
        "centre, and CRVAL values repeat across different nights); a first "
        "version of this script used it and was wrong by up to 3 deg. "
        "fingerprint.json's field_center sits 0.7-3.2 deg away, almost all in RA "
        "and always lower, which is about half the 6.24 deg of RA a 1497 s set "
        "sweeps — consistent with one being the first member and the other the "
        "set mean, though that mechanism is a CANDIDATE and is not confirmed "
        "here. NONE OF THIS TOUCHES THE CONCLUSION: every pointing from every "
        "source puts every target 63-86 deg up within ~2.4 h of the meridian, so "
        "the refraction regime is closed regardless of which is chosen.")

    out = os.path.join(HERE, "site_verification.json")
    json.dump(result, open(out, "w"), indent=1)
    print()
    print(result["verdict"])
    print("wrote %s" % os.path.relpath(out, REPO))
    return 0


if __name__ == "__main__":
    sys.exit(main())
