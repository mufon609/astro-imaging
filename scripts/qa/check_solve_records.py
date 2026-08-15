#!/usr/bin/env python3
"""Join every plate-solve RECORD against the ARTIFACT it names, and report where
they disagree.

    scripts/qa/check_solve_records.py            report over web/results/
    scripts/qa/check_solve_records.py --selftest prove it can go RED

WHY THIS EXISTS. A tracked solve record positively asserted a false solution for
a product that is on disk and carries the correct one: the record read
RA 6.0319 / Dec -65.1006 at 12.96"/px, logodds 22.3, while the file it names in
its own `injected` field reads a healthy solution 115.4 deg away. The crop-solve
recovery landed in the ARTIFACT and never came back to the RECORD. Anyone
validating that union from its record gets the false solve; only the header is
right. A record exists for the reader who will NOT open the artifact, so a record
that is confidently wrong is worse than one that is silent.

WHAT IT COMPARES, AND WHY NOT `CRVAL`. The record's `ra_deg`/`dec_deg` are the
solver's FIELD CENTRE (`solve_field.py`: `m.center_ra_deg`). The header's `CRVAL`
is the WCS TANGENT POINT, which on these solves is nowhere near the pointing
(BACKLOG:`pointing-record-names-the-wrong-frame`; CRPIX sits 40-960 px off centre
and CRVAL repeats across unrelated pointings). MEASURED on the one product that
matters: CRVAL sits 1.662 deg from the same solution evaluated at the centre
pixel, against a clean-population spread of 0.012-0.364 deg over 22 pairs -- so a
CRVAL join carries a baseline error ~5x the entire signal range and is useless
for anything subtler than the case it was built from. This evaluates the target's
own WCS AT ITS CENTRE PIXEL and compares like with like.

NO THRESHOLD WAS TUNED, AND THAT IS A PROPERTY OF THE RESULT RATHER THAN OF THE
DESIGN. The one disagreement measures 115.4 deg against a worst clean case of
0.364 deg -- three orders of magnitude -- so every cut between them gives the
same answer. FLAG_DEG sits at 1.0 because it is between them and for no other
reason. A detector that needed tuning to find its own founding case would be a
weaker claim and this one did not.

READS HEADERS AND RECORDS ONLY -- no pixel is opened, nothing is gated, exit is
always 0. REMOVAL CONDITION: an official tool reports, headless, whether a
plate-solve record's stated solution matches the WCS of the file it names.
"""
import argparse, glob, json, math, os, sys, tempfile, warnings

warnings.filterwarnings("ignore")
from astropy.io import fits
from astropy.wcs import WCS

FLAG_DEG = 1.0


def angsep(r1, d1, r2, d2):
    r1, d1, r2, d2 = map(math.radians, (r1, d1, r2, d2))
    c = math.sin(d1) * math.sin(d2) + math.cos(d1) * math.cos(d2) * math.cos(r1 - r2)
    return math.degrees(math.acos(max(-1.0, min(1.0, c))))


def centre_world(path):
    """The target's OWN solution evaluated at its centre pixel. Never CRVAL."""
    h = fits.getheader(path)
    if not h.get("CTYPE1"):
        return None
    w = WCS(h, naxis=2)
    sky = w.pixel_to_world_values([[h["NAXIS1"] / 2.0, h["NAXIS2"] / 2.0]])[0]
    return float(sky[0]) % 360.0, float(sky[1])


def scan(root):
    rows, unnamed, gone, unusable = [], [], [], []
    for f in sorted(glob.glob(os.path.join(root, "**", "solve_*.json"), recursive=True)):
        try:
            rec = json.load(open(f))
        except (OSError, ValueError):
            unusable.append((f, "record unreadable"))
            continue
        target = rec.get("injected")
        if not target:
            unnamed.append(f)
            continue
        if not os.path.exists(target):
            gone.append((f, target))
            continue
        if rec.get("ra_deg") is None or rec.get("dec_deg") is None:
            unusable.append((f, "record states no ra_deg/dec_deg"))
            continue
        try:
            cw = centre_world(target)
        except Exception as e:                                   # noqa: BLE001
            unusable.append((f, f"target WCS unreadable: {e}"))
            continue
        if cw is None:
            unusable.append((f, "target carries no WCS"))
            continue
        rows.append((angsep(rec["ra_deg"], rec["dec_deg"], *cw), f, rec, cw))
    rows.sort(key=lambda r: -r[0])
    return rows, unnamed, gone, unusable


def report(root):
    rows, unnamed, gone, unusable = scan(root)
    print(f"=== solve RECORD vs ARTIFACT: {len(rows)} pair(s) compared under {root} ===")
    print(f"{'sep(deg)':>10}  {'attempt':<16} {'logodds':>8}  record")
    bad = 0
    for sep, f, rec, _ in rows:
        lo = rec.get("logodds")
        flag = ""
        if sep > FLAG_DEG:
            bad += 1
            flag = "  <-- RECORD DISAGREES WITH THE FILE IT NAMES"
        print(f"{sep:10.4f}  {str(rec.get('attempt')):<16} "
              f"{'' if lo is None else round(lo,1):>8}  {os.path.basename(f)}{flag}")
    print()
    print(f"{bad} record(s) disagree above {FLAG_DEG} deg.")
    print("  The threshold was NOT tuned: the known case measures 115.4 deg against a")
    print("  worst clean case of 0.364 deg, so any cut between them gives this answer.")
    print()
    print("WHAT THIS CANNOT SEE -- read before treating a clean run as coverage:")
    print(f"  (a) records naming no target        : {len(unnamed)}"
          + (f"  {[os.path.basename(x) for x in unnamed]}" if unnamed else ""))
    print(f"  (b) records whose target is GONE    : {len(gone)}"
          + (f"  {[os.path.basename(a) for a, _ in gone]}" if gone else ""))
    print(f"  (c) unusable record or target       : {len(unusable)}")
    for f, why in unusable:
        print(f"        {os.path.basename(f)}: {why}")
    print("  (d) IT VALIDATES THE PRESENT, NOT THE HISTORY. A record that was wrong and")
    print("      was later fixed by a re-solve of the same file reads CLEAN here. A match")
    print("      proves record == header NOW, never that the record was right when written.")
    print("  (e) it compares POINTING only -- a record whose scale, parity or logodds is")
    print("      wrong while its centre is right is invisible to this join.")
    return 0


def selftest():
    """Falsify the mechanism in process: a planted disagreement MUST fire, and a
    matching pair MUST stay quiet. Neither arm can pass by construction."""
    import numpy as np
    fail = 0
    with tempfile.TemporaryDirectory(prefix="check_solve_records.",
                                     dir=os.environ.get("XDG_CACHE_HOME",
                                                        os.path.expanduser("~/.cache"))) as d:
        sub = os.path.join(d, "results", "fixture")
        os.makedirs(sub)
        fit = os.path.join(sub, "stack_fixture_wcs.fit")
        hdu = fits.PrimaryHDU(np.zeros((64, 64), dtype="float32"))
        h = hdu.header
        h["CTYPE1"], h["CTYPE2"] = "RA---TAN", "DEC--TAN"
        h["CRVAL1"], h["CRVAL2"] = 310.0, 43.0
        h["CRPIX1"], h["CRPIX2"] = 32.0, 32.0
        h["CD1_1"], h["CD1_2"], h["CD2_1"], h["CD2_2"] = -0.0047, 0.0, 0.0, 0.0047
        hdu.writeto(fit)
        truth = centre_world(fit)

        def write(name, ra, dec):
            json.dump({"ra_deg": ra, "dec_deg": dec, "logodds": 100.0,
                       "attempt": "fixture", "injected": fit},
                      open(os.path.join(sub, name), "w"))

        # ARM 1 -- planted disagreement, MUST fire
        write("solve_bad.json", (truth[0] + 90.0) % 360.0, -truth[1])
        rows, *_ = scan(os.path.join(d, "results"))
        got = [s for s, f, _, _ in rows if f.endswith("solve_bad.json")]
        if got and got[0] > FLAG_DEG:
            print(f"  PASS  a planted disagreement fires ({got[0]:.2f} deg > {FLAG_DEG})")
        else:
            print(f"  *** FAIL *** planted disagreement did not fire: {got}")
            fail = 1
        os.remove(os.path.join(sub, "solve_bad.json"))

        # ARM 2 -- record agreeing with the artifact, MUST stay quiet
        write("solve_good.json", truth[0], truth[1])
        rows, *_ = scan(os.path.join(d, "results"))
        got = [s for s, f, _, _ in rows if f.endswith("solve_good.json")]
        if got and got[0] <= FLAG_DEG:
            print(f"  PASS  a matching record stays quiet ({got[0]:.4f} deg)")
        else:
            print(f"  *** FAIL *** matching record did not stay quiet: {got}")
            fail = 1

        # ARM 3 -- the CRVAL trap: prove centre-pixel != CRVAL on a CRPIX-offset file,
        # so a future edit swapping the comparand is caught rather than silently wrong.
        h2 = fits.getheader(fit).copy()
        h2["CRPIX1"], h2["CRPIX2"] = 4.0, 4.0          # tangent point far off centre
        off = os.path.join(sub, "offset.fit")
        fits.PrimaryHDU(np.zeros((64, 64), dtype="float32"), header=h2).writeto(off)
        cw = centre_world(off)
        d_crval = angsep(h2["CRVAL1"], h2["CRVAL2"], *cw)
        if d_crval > 0.05:
            print(f"  PASS  CRVAL is NOT the centre on a CRPIX-offset file ({d_crval:.3f} deg)")
        else:
            print(f"  *** FAIL *** CRVAL/centre indistinguishable ({d_crval:.4f}) -- "
                  "the fixture cannot catch a comparand swap")
            fail = 1

    if fail:
        return 1
    print("SELFTEST PASSED")
    return 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--root", default=os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "..", "..", "web", "results"))
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    sys.exit(selftest() if a.selftest else report(os.path.normpath(a.root)))
