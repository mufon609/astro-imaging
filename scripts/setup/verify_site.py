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
    """Every solved stack that carries both a timestamp and a solved centre."""
    from astropy.io import fits
    out = []
    pat = os.path.join(REPO, "web", "results", "*", "stack_set-*_wcs.fit")
    for p in sorted(glob.glob(pat)):
        try:
            h = fits.getheader(p)
        except OSError:
            continue
        if h.get("DATE-OBS") and h.get("CRVAL1") is not None:
            out.append({"product": os.path.relpath(p, REPO),
                        "date_obs": h["DATE-OBS"],
                        "ra_deg": float(h["CRVAL1"]),
                        "dec_deg": float(h["CRVAL2"])})
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

    out = os.path.join(HERE, "site_verification.json")
    json.dump(result, open(out, "w"), indent=1)
    print()
    print(result["verdict"])
    print("wrote %s" % os.path.relpath(out, REPO))
    return 0


if __name__ == "__main__":
    sys.exit(main())
