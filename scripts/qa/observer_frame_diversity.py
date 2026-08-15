#!/usr/bin/env python3
"""Regenerate `datasets/corpus/observer_frame_diversity.json` — the camera's
pointing in the OBSERVER (alt/az) frame, per set, across every group-built set.

    scripts/qa/observer_frame_diversity.py             rewrite the record
    scripts/qa/observer_frame_diversity.py --print     report, write nothing
    scripts/qa/observer_frame_diversity.py --selftest  prove it can go RED

WHY THIS EXISTS AS A SCRIPT RATHER THAN A TRANSCRIPT. The record it writes was
first produced by a one-off probe, which made it reproducible in principle and not
by command. A record nobody can regenerate goes stale silently with no way back —
the corpus grows and nothing re-establishes even the present state.

WHAT IT MEASURES, AND THE ONE THING THAT MAKES IT NON-TRIVIAL. A term fixed in the
observer frame (a horizon-fixed sky gradient) averages down across a combine only
if the CAMERA's alt/az changes between the combined frames. On a fixed tripod the
alt/az is constant WITHIN a set, so the quantity is the change ACROSS sets.

THE TRAP THIS SCRIPT EXISTS TO NOT FALL INTO — and it is why `--selftest` plants
it deliberately: every group sub-stack of a set carries the SET's first `DATE-OBS`
while each group's WCS centre has drifted with the sky (up to 4.9 deg of RA across
one set). Reading the two together pairs a MOVED position with a FROZEN clock and
manufactures a drift: measured 3.933 deg of within-set altitude spread on a fixed
tripod where the physical answer is ZERO. Each group's epoch is therefore DERIVED
as `t0 + dRA / 15.041 deg/hr`, which drops it to 0.088 deg. See `docs/dead-ends.md`.

Azimuth is NOT the statistic: it is degenerate near the zenith and one set here
sits 1.60 deg from it, which reads as 141 deg of spurious spread. The statistic is
ANGULAR SEPARATION in the horizon frame.

Reads FITS headers and the tracked site record only. Opens no pixel. Gates nothing,
always exits 0.

REMOVAL CONDITION: the sub-stack builder stamps each group's OWN epoch (rather than
the set's first `DATE-OBS`), so no derivation is needed and this reduces to an
astropy coordinate transform anyone can run inline.
"""
import argparse, glob, json, math, os, subprocess, sys, warnings

warnings.filterwarnings("ignore")
from astropy.io import fits
from astropy.wcs import WCS
from astropy.coordinates import EarthLocation, SkyCoord, AltAz
from astropy.time import Time
import astropy.units as u

REPO = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
SIDEREAL_DEG_PER_HR = 15.041


def site_location(repo=REPO):
    s = json.load(open(os.path.join(repo, "scripts", "setup", "site.json")))
    return EarthLocation(lat=s["sitelat_deg"] * u.deg, lon=s["sitelong_deg"] * u.deg,
                         height=0 * u.m), s


def centre_and_stamp(path):
    """WCS evaluated AT THE CENTRE PIXEL — never CRVAL, which is the tangent point."""
    h = fits.getheader(path)
    w = WCS(h, naxis=2)
    sky = w.pixel_to_world_values([[h["NAXIS1"] / 2.0, h["NAXIS2"] / 2.0]])[0]
    return float(sky[0]) % 360.0, float(sky[1]), h["DATE-OBS"]


def alt_az(ra, dec, iso, loc):
    a = SkyCoord(ra * u.deg, dec * u.deg, frame="icrs").transform_to(
        AltAz(obstime=Time(iso, format="isot", scale="utc"), location=loc))
    return float(a.alt.deg), float(a.az.deg)


def angsep(a1, z1, a2, z2):
    a1, z1, a2, z2 = map(math.radians, (a1, z1, a2, z2))
    c = math.sin(a1) * math.sin(a2) + math.cos(a1) * math.cos(a2) * math.cos(z1 - z2)
    return math.degrees(math.acos(max(-1.0, min(1.0, c))))


def set_pointings(subs, loc, derive_epoch=True):
    """alt/az for each group of one set. `derive_epoch=False` reproduces the
    frozen-clock defect and exists so the selftest can plant it."""
    ra0, _, t0s = centre_and_stamp(subs[0])
    t0 = Time(t0s, format="isot", scale="utc")
    out = []
    for s in subs:
        ra, dec, stamp = centre_and_stamp(s)
        if derive_epoch:
            dt = ((ra - ra0) % 360.0) / SIDEREAL_DEG_PER_HR * 3600.0
            iso = (t0 + dt * u.s).isot
        else:
            iso = stamp
        out.append(alt_az(ra, dec, iso, loc))
    return out, t0s


def scan(repo=REPO):
    loc, _ = site_location(repo)
    sets, control = [], []
    for d in sorted(glob.glob(os.path.join(repo, "sessions", "*", "work", "groups_set-0[0-9]"))):
        subs = sorted(glob.glob(os.path.join(d, "sub_*.fit")))
        if not subs:
            continue
        vals, t0s = set_pointings(subs, loc)
        ra0, dec0, _ = centre_and_stamp(subs[0])
        alt, az = vals[0]
        parts = d.split(os.sep)
        sets.append({"session": parts[-3], "set": parts[-1].replace("groups_", ""),
                     "n_groups": len(subs),
                     "field_centre_ra_deg": round(ra0, 4), "field_centre_dec_deg": round(dec0, 4),
                     "epoch_utc": t0s, "altitude_deg": round(alt, 3), "azimuth_deg": round(az, 3),
                     "zenith_distance_deg": round(90 - alt, 3)})
        control.append({"session": parts[-3], "set": parts[-1].replace("groups_", ""),
                        "within_set_alt_spread_deg":
                            round(max(v[0] for v in vals) - min(v[0] for v in vals), 4)})
    return sets, control


def selftest():
    """Plant the frozen-clock defect on real data and assert it REPRODUCES, then
    assert the derivation catches it. Neither arm can pass by construction."""
    loc, _ = site_location()
    cand = sorted(glob.glob(os.path.join(REPO, "sessions", "*", "work",
                                         "groups_set-0[0-9]", "sub_*.fit")))
    by_dir = {}
    for f in cand:
        by_dir.setdefault(os.path.dirname(f), []).append(f)
    usable = [sorted(v) for v in by_dir.values() if len(v) >= 3]
    if not usable:
        print("  SKIP  no group dir with >= 3 sub-stacks on this rig — cannot falsify without data")
        return 0
    subs = usable[0]
    fail = 0
    bad, _ = set_pointings(subs, loc, derive_epoch=False)
    good, _ = set_pointings(subs, loc, derive_epoch=True)
    sb = max(v[0] for v in bad) - min(v[0] for v in bad)
    sg = max(v[0] for v in good) - min(v[0] for v in good)
    if sb > 1.0:
        print(f"  PASS  the frozen-clock defect REPRODUCES ({sb:.3f} deg on a FIXED mount)")
    else:
        print(f"  *** FAIL *** planted defect did not reproduce ({sb:.3f} deg) — "
              "the fixture cannot show the derivation doing anything")
        fail = 1
    if sg < 0.5:
        print(f"  PASS  derived epochs recover a constant pointing ({sg:.3f} deg)")
    else:
        print(f"  *** FAIL *** derived epochs still drift ({sg:.3f} deg)")
        fail = 1
    if sb > 0 and sg > 0 and sb / sg > 5:
        print(f"  PASS  derivation improves the control by {sb/sg:.0f}x")
    else:
        print(f"  *** FAIL *** derivation bought less than 5x ({sb:.3f} -> {sg:.3f})")
        fail = 1
    if fail:
        return 1
    print("SELFTEST PASSED")
    return 0


def main(write):
    sets, control = scan()
    if not sets:
        print("no group-built sets found — nothing to measure"); return 0
    pair = [angsep(a["altitude_deg"], a["azimuth_deg"], b["altitude_deg"], b["azimuth_deg"])
            for i, a in enumerate(sets) for b in sets[i + 1:]]
    alts = [s["altitude_deg"] for s in sets]
    print(f"{'night':<8}{'set':<8}{'ALT':>8}{'AZ':>9}{'ZD':>7}")
    for s in sets:
        print(f"{s['session']:<8}{s['set']:<8}{s['altitude_deg']:8.2f}"
              f"{s['azimuth_deg']:9.2f}{s['zenith_distance_deg']:7.2f}")
    print(f"\n  n_sets {len(sets)}   max pairwise separation {max(pair):.2f} deg"
          f"   median {sorted(pair)[len(pair)//2]:.2f}   altitude {min(alts):.1f}-{max(alts):.1f}")
    print(f"  worst within-set alt spread (the control) {max(c['within_set_alt_spread_deg'] for c in control):.4f} deg")
    if not write:
        return 0
    rec_path = os.path.join(REPO, "datasets", "corpus", "observer_frame_diversity.json")
    rec = json.load(open(rec_path))
    rec["_measured_at_commit"] = subprocess.run(
        ["git", "-C", REPO, "rev-parse", "--short", "HEAD"],
        capture_output=True, text=True).stdout.strip()
    rec["_regenerated_by"] = "scripts/qa/observer_frame_diversity.py"
    rec["per_set"] = sets
    rec["control"]["per_set"] = control
    rec["control"]["with_derived_epochs_deg"] = max(c["within_set_alt_spread_deg"] for c in control)
    rec["result"].update({"n_sets": len(sets),
                          "max_pairwise_separation_deg": round(max(pair), 3),
                          "median_pairwise_separation_deg": round(sorted(pair)[len(pair) // 2], 3),
                          "altitude_range_deg": [min(alts), max(alts)]})
    json.dump(rec, open(rec_path, "w"), indent=1)
    print(f"  rewrote {os.path.relpath(rec_path, REPO)}")
    return 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--print", dest="print_only", action="store_true")
    a = ap.parse_args()
    sys.exit(selftest() if a.selftest else main(write=not a.print_only))
