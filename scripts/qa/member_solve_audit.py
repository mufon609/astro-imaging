#!/usr/bin/env python3
"""Audit the PLATE SOLUTIONS of undistort sub-stack members against their own
population — the guard for the wrong-optimum member solve.

  member_solve_audit.py <member.fit|groups_dir>... [--json=<out>] [--tol=0.25]
                        [--sip-ratio=4]
  member_solve_audit.py --selftest

WHY IT EXISTS (measured, aug06+aug14, both the full and the crop5lr chains).
The astrometric compose warps each member by its own blind TAN+SIP solve, and
nothing checked those solves against anything. One optic took every frame, so
the members' solved scales must form a smooth per-set sequence (refraction
genuinely drifts the effective scale ~0.5% as an untracked field sinks — a
FIXED band is therefore wrong); against that sequence, the failed fits stand
out hard: solved 16.791 arcsec/px in a 17.02-17.08 sibling population, SIP
terms ~10x the siblings', and the same member re-solved under a tight scale
band moved its edge-of-field sky positions by 31.5 px (median star-matched
edge bow, n=1655) while a healthy member moved 0.000 px. Two such members
dominated the smeared rim of the crop5lr cross-night combine; the control
chain carried the single worst fit (16.791) diluted below the visible line.

WHAT IS THE TOOL'S AND WHAT IS IN-HOUSE (the bright line, CLAUDE.md): every
number read here is a solver's own product (the WCS the member already
carries: CD matrix, SIP coefficients) or a header fact (CALSET, DATE-OBS);
the in-house part is the per-set robust trend + outlier flagging — a derived
consistency check no tool provides. REPORTS ONLY: it rewrites nothing and
always exits 0 with a record; the fix it recommends is a solve_field
--scale-band re-solve, printed per flagged member.

FLAG RULES (both derived from the measured failures, not tuned to pass):
  scale   |solved - trend| / trend > --tol (default 0.25%) where trend is the
          set's Theil-Sen line over capture order — robust to <=50% bad
          members, and it does NOT flag the real ~0.5%/night refraction drift
          (the drift IS the line).
  sip     max |SIP a_ij, b_ij (i+j>=2)| > --sip-ratio x the set median
          (default 4x): the wrong optimum patches its wrong linear scale with
          oversized distortion terms (measured 2.2e-05 vs sibling 2e-06).

Removal condition: the member solve itself refuses population-inconsistent
solutions (e.g. solve_field growing a required neighbor-band check), making a
post-hoc audit redundant.
"""
import glob
import json
import math
import os
import sys

from astropy.io import fits


def member_stats(path):
    h = fits.getheader(path)
    try:
        det = h["CD1_1"] * h["CD2_2"] - h["CD1_2"] * h["CD2_1"]
    except KeyError:
        return {"path": path, "unsolved": True, "set": h.get("CALSET", "?")}
    sip = [abs(float(h[k])) for k in h
           if (k.startswith("A_") or k.startswith("B_"))
           and k not in ("A_ORDER", "B_ORDER", "A_DMAX", "B_DMAX")
           and sum(int(c) for c in k.split("_")[1:]) >= 2]
    return {"path": path, "set": h.get("CALSET", "?"),
            "date_obs": h.get("DATE-OBS", ""),
            "scale_arcsec_px": math.sqrt(abs(det)) * 3600.0,
            "rot_deg": math.degrees(math.atan2(h["CD2_1"], h["CD1_1"])),
            "max_sip": max(sip) if sip else 0.0}


def theil_sen(xs, ys):
    """Robust line through (xs, ys): median of pairwise slopes, median-anchored
    intercept. Stands up to <=50% contamination, which the measured case
    reaches (3 suspicious of 6 in one set)."""
    slopes = [(ys[j] - ys[i]) / (xs[j] - xs[i])
              for i in range(len(xs)) for j in range(i + 1, len(xs))
              if xs[j] != xs[i]]
    if not slopes:
        return 0.0, ys[0]
    slopes.sort()
    m = slopes[len(slopes) // 2]
    resid = sorted(y - m * x for x, y in zip(xs, ys))
    return m, resid[len(resid) // 2]


def audit(paths, tol, sip_ratio):
    mems = [member_stats(p) for p in paths]
    by_set = {}
    for m in mems:
        by_set.setdefault(m["set"], []).append(m)
    flagged = []
    for st, group in sorted(by_set.items()):
        solved = [m for m in group if not m.get("unsolved")]
        solved.sort(key=lambda m: (m["date_obs"], m["path"]))
        for i, m in enumerate(solved):
            m["order"] = i
        if len(solved) >= 3:
            slope, icept = theil_sen([m["order"] for m in solved],
                                     [m["scale_arcsec_px"] for m in solved])
        else:
            slope, icept = 0.0, (solved[0]["scale_arcsec_px"] if solved else 0)
        med_sip = sorted(m["max_sip"] for m in solved)[len(solved) // 2] \
            if solved else 0.0
        for m in group:
            if m.get("unsolved"):
                m["flags"] = ["UNSOLVED"]
                flagged.append(m)
                continue
            trend = slope * m["order"] + icept
            m["trend_arcsec_px"] = trend
            m["scale_dev_pct"] = 100.0 * (m["scale_arcsec_px"] - trend) / trend
            m["flags"] = []
            if abs(m["scale_dev_pct"]) > tol:
                m["flags"].append(
                    f"SCALE {m['scale_arcsec_px']:.4f} is "
                    f"{m['scale_dev_pct']:+.2f}% off the set trend {trend:.4f}")
            if med_sip > 0 and m["max_sip"] > sip_ratio * med_sip:
                m["flags"].append(
                    f"SIP max |coef| {m['max_sip']:.2e} is "
                    f"{m['max_sip'] / med_sip:.1f}x the set median {med_sip:.2e}")
            if m["flags"]:
                lo, hi = trend * (1 - tol / 100 * 0.8), trend * (1 + tol / 100 * 0.8)
                m["resolve_cmd"] = (
                    f"python3 scripts/calibrate/solve_field.py <copy-of-"
                    f"{os.path.basename(m['path'])}> "
                    f"--scale-band={lo:.3f},{hi:.3f} --max-stars=1500 "
                    f"--inject=<resolved.fit>")
                flagged.append(m)
    return mems, flagged


def run(paths, out_json, tol, sip_ratio):
    files = []
    for p in paths:
        if os.path.isdir(p):
            files += sorted(glob.glob(os.path.join(p, "sub_*.fit")))
        else:
            files.append(p)
    if not files:
        sys.exit("member_solve_audit: no members found")
    mems, flagged = audit(files, tol, sip_ratio)
    for m in mems:
        mark = " <<< " + "; ".join(m["flags"]) if m.get("flags") else ""
        if m.get("unsolved"):
            print(f"  {os.path.basename(m['path']):14s} {m['set']:14s} UNSOLVED{mark}")
        else:
            print(f"  {os.path.basename(m['path']):14s} {m['set']:14s} "
                  f"{m['scale_arcsec_px']:8.4f}\"/px  dev {m.get('scale_dev_pct', 0):+6.2f}%  "
                  f"maxSIP {m['max_sip']:.1e}{mark}")
    print(f"\n{len(flagged)} of {len(mems)} member solution(s) FLAGGED "
          f"(scale tol {tol}% off the set's own Theil-Sen trend; "
          f"SIP > {sip_ratio}x set median)")
    for m in flagged:
        if m.get("resolve_cmd"):
            print(f"  re-solve: {m['resolve_cmd']}")
    if out_json:
        json.dump({"instrument":
                   "header WCS only (each member's own solver product: CD "
                   "matrix det -> scale, SIP coefficient magnitudes) + "
                   "in-house per-set Theil-Sen trend and flag rules; "
                   "REPORTS ONLY",
                   "tol_pct": tol, "sip_ratio": sip_ratio,
                   "members": [{k: v for k, v in m.items()} for m in mems],
                   "n_flagged": len(flagged)},
                  open(out_json, "w"), indent=1)
        print(f"record -> {out_json}")
    return 0


# --------------------------------------------------------------- selftest ---
def selftest():
    """Plant defects the audit must catch AND legitimate structure it must not
    flag; run entirely on synthetic in-memory headers."""
    import tempfile
    ok = True
    with tempfile.TemporaryDirectory() as d:
        def write(name, scale, sipmag, calset, t):
            cd = scale / 3600.0
            h = fits.Header()
            h["CD1_1"], h["CD1_2"] = cd, 0.0
            h["CD2_1"], h["CD2_2"] = 0.0, -cd
            h["A_ORDER"] = h["B_ORDER"] = 3
            h["A_2_0"] = sipmag
            h["B_0_2"] = sipmag / 2
            h["CALSET"] = calset
            h["DATE-OBS"] = t
            fits.PrimaryHDU(header=h).writeto(os.path.join(d, name))
        # set A: a real refraction drift 17.03 -> 16.94 (0.5%), all healthy —
        # MUST NOT flag (a fixed-band rule would flag its ends; the trend rule
        # is the point of this tool)
        drift = [17.031, 17.013, 16.995, 16.977, 16.959, 16.941]
        for i, s in enumerate(drift):
            write(f"sub_0{i+1}.fit", s, 2e-06, "night/set-0A", f"2026-08-14T0{i}:00:00")
        # set B: one wrong-optimum member — scale -1.3% AND 10x SIP (the
        # measured signature) — MUST flag on both rules
        for i, (s, m) in enumerate([(17.030, 2e-06), (17.028, 2.2e-06),
                                    (16.808, 2.1e-05), (17.024, 1.8e-06)]):
            write(f"sub_1{i+1}.fit", s, m, "night/set-0B", f"2026-08-14T1{i}:00:00")
        files = sorted(glob.glob(os.path.join(d, "sub_*.fit")))
        _, flagged = audit(files, 0.25, 4)
        names = {os.path.basename(m["path"]) for m in flagged}
        s1 = names == {"sub_13.fit"}
        print(f"  step 1: exactly the planted wrong-optimum flagged -> "
              f"{'GREEN' if s1 else 'RED — flagged ' + str(sorted(names))}")
        ok &= s1
        both = next(m for m in flagged) if flagged else {}
        s2 = len(both.get("flags", [])) == 2
        print(f"  step 2: it fires on BOTH rules (scale + SIP) -> "
              f"{'GREEN' if s2 else 'RED — ' + str(both.get('flags'))}")
        ok &= s2
        # falsification: with the trend replaced by a set MEDIAN the drift set
        # WOULD misflag its ends — prove the trend rule is load-bearing
        drift_scales = drift
        med = sorted(drift_scales)[len(drift_scales) // 2]
        worst = max(abs(100 * (s - med) / med) for s in drift_scales)
        s3 = worst > 0.25
        print(f"  step 3: a set-median rule WOULD misflag the refraction drift "
              f"(worst dev {worst:.2f}% > 0.25%) — the trend rule is "
              f"load-bearing -> {'GREEN' if s3 else 'RED'}")
        ok &= s3
    print(f"SELFTEST {'PASS' if ok else 'FAIL'}")
    return 0 if ok else 1


def main():
    argv = sys.argv[1:]
    if "--selftest" in argv:
        return selftest()
    paths = [a for a in argv if not a.startswith("--")]
    opts = dict(a[2:].split("=", 1) for a in argv
                if a.startswith("--") and "=" in a)
    if not paths:
        sys.exit(__doc__)
    return run(paths, opts.get("json"), float(opts.get("tol", 0.25)),
               float(opts.get("sip-ratio", 4)))


if __name__ == "__main__":
    sys.exit(main())
