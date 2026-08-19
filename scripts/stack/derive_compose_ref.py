#!/usr/bin/env python3
"""Derive the registration REFERENCE for a multi-night compose, deterministically.

Usage: derive_compose_ref.py <member.fit>...  [--json=<out>] [--quiet]
       derive_compose_ref.py --selftest

Prints the 1-based index of the member to pin, or 0 meaning KEEP AUTO. The
caller pins it with `setref`; run_undistort_compose.sh does exactly that.

WHY IT EXISTS. `register -2pass`/`seqplatesolve`'s auto reference is INDEX 0 —
the first member in link order. MEASURED: ten `compose_gate_*.json` records at
13/17/22/25/52/77 members all read `reference_member = s_00001`, and an auto arm
measured 0 differing pixels of 98,194,977 against an explicit `--ref=1`. It does
not rank; it takes whatever sorts first. So the reference — and with it the
composed canvas — is a function of ARGUMENT ORDER, and `run_corpus_combine.sh`'s
session arguments decide it. Appending a night re-bases nothing; reordering the
arguments re-bases everything, with nothing in any record to show for it.

WHAT THE REFERENCE ACTUALLY DECIDES, measured on the SHIPPED astrometric route
(one knob, 4 members over 2 nights, same framing/weight/order):
  canvas 7071x4629 -> 7095x4622, north +9.6244 -> +7.7633 deg, and at the
  compose B/G 0.7427 -> 0.5260.
The BALANCE half does NOT reach the deliverable — SPCC absorbs it 64x (B/G delta
-0.2167 at the compose, -0.0034 after SPCC; siril's own K factors move to
compensate, B 0.862 -> 0.923). What survives SPCC is the CANVAS.

AND THE SURVIVING DIFFERENCE IS NOT MORE SKY. At `-framing=max` every arm
includes every member, so the sky UNION is identical BY CONSTRUCTION. What moves
is the tangent point and orientation, so the axis-aligned bounding box around the
SAME sky changes shape: 7071x4629 = 32,731,659 px against 7095x4622 =
32,793,090 px, +0.19% of EMPTY CORNER. A bounding box around a rotated quad is
not a coverage measure and must not be quoted as one.

SO NO CHOICE OF REFERENCE IS MATERIALLY BETTER, AND THAT — NOT A WINNER — IS WHY
THIS RULE EXISTS. Colour is absorbed, coverage is identical, the bounding box
moves by empty corner. What IS defective is that the product depends on ARGUMENT
ORDER, which is a reproducibility fault at any magnitude. The rule below is
therefore chosen for being deterministic, order-independent and interpretable,
NOT for winning on a measure. Do not argue it on coverage
(`docs/dead-ends.md`, the setref entry).

THE RULE, and it is deterministic by construction:

  1. FIRES ONLY ON A MULTI-NIGHT COMPOSE. Night key = `(DATE-OBS - 12h).date()`
     — the standard observing-"night of" convention, not a calendar date. This is
     not cosmetic: july31's members carry `DATE-OBS 2026-08-01 02:51`, and a
     calendar-date key would split one night in two. VALIDATED on the corpus: the
     key partitions its 77 members into exactly 4 nights, 17/13/22/25, matching
     `datasets/corpus/corpus4_build_record.json`. One night -> return 0, KEEP
     AUTO, so no single-night product moves.
  2. THE PICK: the member whose pointing is CLOSEST TO THE MEDIAN POINTING of all
     members. Chosen because it is stable under adding a member and independent
     of argument order, and because "the middle of what we shot" is a statement a
     reader can check — not because centrality measures better (it does not; see
     above). Any total, order-independent rule would satisfy the defect; this one
     is also interpretable.
  3. POINTING IS THE WCS EVALUATED AT THE CENTRE PIXEL, NEVER `CRVAL`. CRVAL is
     the tangent point. MEASURED on the corpus's 77 members: CRVAL sits a median
     1.877 deg and up to 5.814 deg from the centre-pixel pointing, which is
     enough to pick a different member. (`check_solve_records.centre_world` is
     the same decision in the same tree; BACKLOG:`pointing-record-names-the-wrong-frame`.)
  4. TIE-BREAKS, in order: larger STACKCNT (deeper), then earlier DATE-OBS, then
     lower linked index. REQUIRED, not theoretical — on the corpus two members
     tie at STACKCNT 130, so depth alone does not resolve. The final index
     tie-break makes the result total: two members at the same position, depth
     and time are genuinely interchangeable for this purpose.

WELL-CONDITIONED ON THE DATA IT WAS BUILT FOR, which is a property of the corpus
and not of the rule: the most-central member sits 0.1622 deg from the median
against a runner-up at 0.4712 — a 0.309 deg gap, not a knife-edge. A corpus
whose two most central members were microns apart would resolve by depth, then
time, then index, and the answer would still be stable across runs.

DEFAULT WITH OVERRIDE. An explicit `--ref=` always wins and is reported PINNED;
this only runs when the caller passed none. Deliberate: raising or pinning these
by hand is a real workflow (A/B arms, a deliberate no-combine build), and an
unconditional derivation would delete a capability the repo uses.

BRIGHT LINE. Reads FITS HEADERS only — no pixel is opened. Every input is a
tool's: the WCS is astrometry.net's solution (via each member's own solve),
DATE-OBS and STACKCNT are the capture/stack record. The derived part is only
"which member is most central", which no tool reports. It gates nothing and
rewrites nothing; it returns an index the caller announces and stamps
(`REGREF`/`REGREFSR=derived`).

REMOVAL CONDITION: retire when siril chooses a sequence reference by a stated,
deterministic, order-independent rule of its own — at which point AUTO is
already what this computes. Today it takes index 0.
"""
import datetime as dt
import glob
import json
import math
import os
import sys
import warnings

warnings.filterwarnings("ignore")


def night_key(date_obs):
    """The observing night, not the calendar date: DATE-OBS shifted back 12 h."""
    return (dt.datetime.fromisoformat(date_obs) - dt.timedelta(hours=12)).date().isoformat()


def angsep(r1, d1, r2, d2):
    """Great-circle separation in degrees."""
    r1, d1, r2, d2 = (math.radians(v) for v in (r1, d1, r2, d2))
    c = (math.sin(d1) * math.sin(d2)
         + math.cos(d1) * math.cos(d2) * math.cos(r1 - r2))
    return math.degrees(math.acos(max(-1.0, min(1.0, c))))


def centre_world(header):
    """The member's OWN solution at its CENTRE PIXEL. Never CRVAL — that is the
    tangent point, measured a median 1.877 / max 5.814 deg away on this corpus."""
    from astropy.wcs import WCS
    if not header.get("CTYPE1"):
        return None
    # naxis=2 explicitly: these are 3-plane cubes carrying SIP, and astropy
    # REFUSES to build a 3-axis WCS with SIP ("SIP distortions only work in 2
    # dimensions"). Without it every member reads as unsolved, silently.
    w = WCS(header, naxis=2)
    sky = w.pixel_to_world_values([[(header["NAXIS1"] - 1) / 2.0,
                                    (header["NAXIS2"] - 1) / 2.0]])[0]
    return float(sky[0]) % 360.0, float(sky[1])


def rows_from_headers(headers):
    """headers: list of mapping, in LINK ORDER. -> rows with the derived fields."""
    rows = []
    for i, h in enumerate(headers, start=1):
        do = h.get("DATE-OBS")
        cw = centre_world(h)
        rows.append({"index": i,
                     "date_obs": do,
                     "night": night_key(do) if do else None,
                     "stackcnt": h.get("STACKCNT"),
                     "ra": cw[0] if cw else None,
                     "dec": cw[1] if cw else None})
    return rows


def derive(rows):
    """-> (index or 0, reason dict). 0 means KEEP AUTO."""
    nights = sorted({r["night"] for r in rows if r["night"]})
    usable = [r for r in rows if r["ra"] is not None and r["night"]]
    info = {"members": len(rows), "nights": nights,
            "usable": len(usable), "rule": "most-central member vs the member median"}
    if len(nights) <= 1:
        info["verdict"] = ("single night — AUTO is harmless (the members share a "
                           "balance family and one canvas geometry)")
        return 0, info
    if not usable:
        info["verdict"] = ("multi-night but NO member carries a usable WCS — nothing "
                           "measured, so nothing is derived and AUTO stands")
        return 0, info
    if len(usable) < len(rows):
        info["partial"] = (f"{len(rows) - len(usable)} member(s) carry no usable WCS "
                           "and cannot be the reference; the median is over the rest")
    ra = sorted(r["ra"] for r in usable)
    dec = sorted(r["dec"] for r in usable)
    mid = len(ra) // 2
    # median per axis; even n takes the lower-middle so the value is a MEMBER's,
    # not an interpolation between two members
    mra, mdec = ra[mid if len(ra) % 2 else mid - 1], dec[mid if len(dec) % 2 else mid - 1]
    for r in usable:
        r["sep_deg"] = angsep(r["ra"], r["dec"], mra, mdec)
    # tie-breaks: closest, then DEEPER, then EARLIER, then lowest index
    best = min(usable, key=lambda r: (round(r["sep_deg"], 6),
                                      -(r["stackcnt"] or 0),
                                      r["date_obs"] or "",
                                      r["index"]))
    runner = sorted(usable, key=lambda r: (round(r["sep_deg"], 6), r["index"]))
    info.update({"median_pointing": [round(mra, 4), round(mdec, 4)],
                 "picked_index": best["index"],
                 "picked_sep_deg": round(best["sep_deg"], 4),
                 "runner_up_sep_deg": (round(runner[1]["sep_deg"], 4)
                                       if len(runner) > 1 else None),
                 "verdict": f"{len(nights)} nights — reference DERIVED"})
    return best["index"], info


def selftest():
    """Falsify the RULES on synthetic headers — data-free, so it can run anywhere.

    Every case asserts a behaviour the rule PROMISES; a rule that cannot be made
    to return the wrong answer on demand is decoration (CLAUDE.md: every
    acceptance measure ships with data on which it must fire)."""
    def hdr(date_obs, ra, dec, stackcnt=100, wcs=True):
        h = {"DATE-OBS": date_obs, "STACKCNT": stackcnt,
             "NAXIS1": 1001, "NAXIS2": 801}
        if wcs:
            h.update({"CTYPE1": "RA---TAN", "CTYPE2": "DEC--TAN",
                      "CRPIX1": 500.0, "CRPIX2": 400.0,
                      "CRVAL1": ra, "CRVAL2": dec,
                      "CD1_1": -0.001, "CD1_2": 0.0, "CD2_1": 0.0, "CD2_2": 0.001})
        return h

    N1, N2 = "2026-08-01T02:00:00", "2026-08-15T02:00:00"
    cases = []

    # 1. SINGLE NIGHT -> 0. Two members far apart, same night: must NOT fire.
    cases.append(("single night keeps AUTO",
                  [hdr(N1, 300.0, 40.0), hdr("2026-08-01T04:00:00", 310.0, 40.0)], 0))
    # 2. THE NIGHT KEY IS THE OBSERVING NIGHT. 23:00 and 02:00 next day are ONE
    #    night; a calendar-date key would call them two and wrongly derive.
    cases.append(("22:00 + 02:00-next-day is ONE night",
                  [hdr("2026-08-01T22:00:00", 300.0, 40.0),
                   hdr("2026-08-02T02:00:00", 310.0, 40.0)], 0))
    # 3. MULTI-NIGHT -> the CENTRAL member. Median of (300,305,320) is 305 -> idx 2.
    cases.append(("multi-night picks the central member",
                  [hdr(N1, 300.0, 40.0), hdr(N1, 305.0, 40.0), hdr(N2, 320.0, 40.0)], 2))
    # 4. ARGUMENT ORDER MUST NOT MATTER — the same members reordered pick the same
    #    MEMBER (now at index 1). This is the whole defect being fixed.
    cases.append(("order-independent: same member, new index",
                  [hdr(N1, 305.0, 40.0), hdr(N1, 300.0, 40.0), hdr(N2, 320.0, 40.0)], 1))
    # 5. TIE ON POSITION -> DEEPER wins (two members at the median, different depth)
    cases.append(("tie on position breaks to DEEPER",
                  [hdr(N1, 305.0, 40.0, stackcnt=100), hdr(N2, 305.0, 40.0, stackcnt=130),
                   hdr(N2, 320.0, 40.0)], 2))
    # 6. TIE ON POSITION AND DEPTH -> EARLIER wins
    cases.append(("tie on position+depth breaks to EARLIER",
                  [hdr("2026-08-15T04:00:00", 305.0, 40.0), hdr(N2, 305.0, 40.0),
                   hdr(N1, 320.0, 40.0)], 2))
    # 7. NO WCS ANYWHERE on a multi-night set -> 0, not a guess.
    cases.append(("multi-night with no WCS derives nothing",
                  [hdr(N1, 300.0, 40.0, wcs=False), hdr(N2, 320.0, 40.0, wcs=False)], 0))
    # 8. A member with no WCS cannot BE the reference but does not block the rest.
    #    Index 1 sits at 305 — the centre of all three, so it is exactly what
    #    would be picked if unsolved members counted. Usable are 300 and 310,
    #    whose lower-middle median is 300 -> index 2.
    cases.append(("unsolved member cannot be the pick even when central",
                  [hdr(N1, 305.0, 40.0, wcs=False), hdr(N1, 300.0, 40.0),
                   hdr(N2, 310.0, 40.0)], 2))

    bad = 0
    for name, headers, want in cases:
        got, info = derive(rows_from_headers(headers))
        if got == want:
            print(f"  selftest ok   [{got}] {name}")
        else:
            print(f"  selftest WRONG (wanted {want}, got {got}): {name}", file=sys.stderr)
            bad = 1
    if bad:
        sys.exit("derive_compose_ref: the rules do not fire as stated")
    print(f"OK: {len(cases)} rule cases — night key, centrality, order-independence,")
    print("    all three tie-breaks, and both no-WCS paths, each verdict as stated.")
    return 0


def main():
    if "--selftest" in sys.argv:
        sys.exit(selftest())
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    opts = dict((a[2:].split("=", 1) + [""])[:2] for a in sys.argv[1:] if a.startswith("--"))
    files = []
    for a in args:
        files.extend(sorted(glob.glob(a)) if any(c in a for c in "*?[") else [a])
    if not files:
        sys.exit("usage: derive_compose_ref.py <member.fit>... [--json=OUT] [--quiet]")
    from astropy.io import fits             # HEADERS ONLY — no pixel access
    # DEGRADE LOUDLY. An unreadable member used to become an empty header, which
    # reads downstream as "no DATE-OBS" and quietly collapses a multi-night set
    # to "single night — keep AUTO" — the safe-looking answer, for the wrong
    # reason. MEASURED while testing this script: zsh does NOT word-split an
    # unquoted expansion (unlike bash), so a caller's `$MEMBERS` arrived as ONE
    # argument holding 77 newline-separated paths, and the run reported a
    # confident single-night verdict on garbage.
    headers, unreadable = [], []
    for f in files:
        try:
            headers.append(fits.getheader(f))
        except (OSError, ValueError) as e:
            unreadable.append(f"{os.path.basename(f)[:60]}: {type(e).__name__}")
            headers.append({})
    if unreadable:
        for u in unreadable:
            print(f"[derive_compose_ref] UNREADABLE member: {u}", file=sys.stderr)
        sys.exit(f"derive_compose_ref: {len(unreadable)} of {len(files)} members "
                 "could not be read — refusing to derive a reference from a "
                 "membership it cannot see (a silent 'keep AUTO' here is the "
                 "same answer for the wrong reason)")
    idx, info = derive(rows_from_headers(headers))
    # A BASENAME CANNOT IDENTIFY A MEMBER — `sub_02.fit` exists in every group
    # dir — so the record carries the path tail, the same identity REGREF uses.
    def tail(f):
        parts = os.path.normpath(os.path.abspath(f)).split(os.sep)
        return "/".join(parts[-4:-2:1] + parts[-2:]) if len(parts) >= 4 else f
    info["files"] = [tail(f) for f in files]
    if idx:
        info["picked_file"] = tail(files[idx - 1])
    if "json" in opts and opts["json"]:
        json.dump(info, open(opts["json"], "w"), indent=1)
    if "quiet" not in opts:
        print(f"[derive_compose_ref] {info['verdict']}", file=sys.stderr)
        if idx:
            print(f"[derive_compose_ref] member {idx} ({info['picked_file']}) at "
                  f"{info['picked_sep_deg']} deg from the median pointing "
                  f"{info['median_pointing']}; runner-up {info['runner_up_sep_deg']} deg",
                  file=sys.stderr)
    print(idx)


if __name__ == "__main__":
    main()
