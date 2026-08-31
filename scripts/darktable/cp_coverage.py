#!/usr/bin/env python3
"""Control-point RADIAL COVERAGE of a hugin fit — does it constrain the CORNER?

Usage:
  cp_coverage.py <project.pto> --wh WxH [--json OUT] [--print]

A ptlens fit is a cubic in normalised radius, and lensfun evaluates it with the
radius normalised by HALF THE SHORT SIDE — MEASURED end-to-end through the
production warp, not read off a doc: fitting the four installed models at once
against a warped fixture gives RMS 4.47 px for half-short-side, 18.27 px for
half-long-side and 22.22 px for half-diagonal, and a free normalisation lands at
2000 px against 2020 (ledger `undistort_normalization_and_corner_divergence`).

On a 6064x4040 frame that puts the image CORNER at rho = 1.80, while a fit's
control points are wherever `cpfind` happened to find matched stars. THE FIT IS
ONLY EVIDENCE WHERE ITS CONTROL POINTS ARE; past them the cubic runs free, and
two fits that are interchangeable inside the supported field can diverge by
6-8 px outside it — which is the measured cause of the cross-set compose's
corner star doubling (docs/dead-ends.md).

MEASURED CENSUS of every fit this repo has ever shipped (ledger
`fit_corner_support_census`): median support rho 0.62-0.86, p99 1.43-1.48,
MAXIMUM 1.47-1.51 — against a corner at 1.80. None of them constrains the
corner. The fit REJECTED on banded coverage tops out at 1.24, so this census and
that diagnosis agree independently.

So a fit's own residual (0.02-0.10 px on fits that produce 2.99 px of corner
disagreement) is NOT evidence about the corner: it is computed only where the
control points are. This is the number that says whether the corner was FITTED
or EXTRAPOLATED, and it rides on every sub-stack as DISTRHO.

The tool does the fitting; this reads hugin's OWN control-point coordinates out
of its OWN project file and reports where they are. It fits nothing.

REMOVAL CONDITION: retire the radial-coverage analysis when hugin/lensfun
report per-radius control-point support against the model's own normalisation,
or when the fitting route pins control points to a corner-inclusive station
grid by construction (corner support guaranteed rather than measured).
Condition authored by audit — this divergence shipped with none; RATIFIED by
the owner 2026-08-19.
"""
import argparse
import json
import os
import re
import sys

import numpy as np

# Corner-true criterion — PRE-REGISTERED before the first refit that aims at it
# (ledger `corner_true_fit_pilot`). Each threshold is placed against the measured
# census above and the corner at rho = 1.80, never picked for looking round:
#   rho_max   >= 1.75  control points essentially AT the corner (census: 1.47-1.51)
#   rho_p99   >= 1.60  the bulk of the outer support reaches past every fit so far
#   frac>1.50 >= 5%    the corner is represented by a POPULATION, not by one or two
#                      points an optimiser can average away (census: 0.0-0.4%)
#   n         >= 100   the fit as a whole is constrained (the discarded 8-CP fit
#                      is the registry precedent for under-constrained)
CRITERION = {"rho_max_min": 1.75, "rho_p99_min": 1.60,
             "frac_beyond_1_50_min": 0.05, "n_min": 100}


def coverage(pto, w, h):
    """Every control point contributes BOTH endpoints: a CP constrains the model
    at the radius it occupies in each image it links."""
    cx, cy = w / 2.0, h / 2.0
    norm = min(w, h) / 2.0                      # MEASURED lensfun convention
    rho = []
    for ln in open(pto):
        if not ln.startswith("c "):
            continue
        m = dict(re.findall(r"\b([xyXY])(-?[0-9.]+)", ln))
        for a, b in (("x", "y"), ("X", "Y")):
            if a in m and b in m:
                rho.append(((float(m[a]) - cx) ** 2
                            + (float(m[b]) - cy) ** 2) ** 0.5 / norm)
    if not rho:
        return None
    r = np.array(rho)
    rec = {"n": len(r) // 2, "n_endpoints": len(r),
           "normalisation_px": norm,
           "corner_rho": round(((w / 2) ** 2 + (h / 2) ** 2) ** 0.5 / norm, 3),
           "rho_p50": round(float(np.percentile(r, 50)), 3),
           "rho_p90": round(float(np.percentile(r, 90)), 3),
           "rho_p99": round(float(np.percentile(r, 99)), 3),
           "rho_max": round(float(r.max()), 3),
           "frac_beyond_1_20": round(float((r > 1.20).mean()), 4),
           "frac_beyond_1_50": round(float((r > 1.50).mean()), 4),
           "frac_beyond_1_75": round(float((r > 1.75).mean()), 4)}
    fails = []
    if rec["rho_max"] < CRITERION["rho_max_min"]:
        fails.append(f"rho_max {rec['rho_max']} < {CRITERION['rho_max_min']}")
    if rec["rho_p99"] < CRITERION["rho_p99_min"]:
        fails.append(f"rho_p99 {rec['rho_p99']} < {CRITERION['rho_p99_min']}")
    if rec["frac_beyond_1_50"] < CRITERION["frac_beyond_1_50_min"]:
        fails.append(f"frac>1.50 {rec['frac_beyond_1_50']} < "
                     f"{CRITERION['frac_beyond_1_50_min']}")
    if rec["n"] < CRITERION["n_min"]:
        fails.append(f"n {rec['n']} < {CRITERION['n_min']}")
    rec["criterion"] = CRITERION
    rec["corner_support"] = ("true" if not fails
                             else "partial" if rec["rho_max"] >= 1.40 else "none")
    rec["criterion_fails"] = fails
    return rec


def main():
    ap = argparse.ArgumentParser(add_help=False)
    ap.add_argument("pto")
    ap.add_argument("--wh", required=True)
    ap.add_argument("--json")
    ap.add_argument("--print", action="store_true", dest="show")
    ap.add_argument("-h", "--help", action="store_true")
    a = ap.parse_args()
    if a.help:
        sys.exit(__doc__)
    w, h = (int(x) for x in a.wh.lower().split("x"))
    rec = coverage(a.pto, w, h)
    if rec is None:
        sys.exit(f"cp_coverage: no control points in {a.pto}")
    if a.show or not a.json:
        print(f"  CP coverage ({rec['n']} CPs, corner at rho {rec['corner_rho']}): "
              f"p50 {rec['rho_p50']}  p90 {rec['rho_p90']}  p99 {rec['rho_p99']}  "
              f"max {rec['rho_max']}  |  beyond 1.20 {rec['frac_beyond_1_20']*100:.1f}%  "
              f"beyond 1.50 {rec['frac_beyond_1_50']*100:.1f}%")
        print(f"  corner support: {rec['corner_support'].upper()}"
              + ("" if not rec["criterion_fails"]
                 else " — " + "; ".join(rec["criterion_fails"])))
    if a.json:
        json.dump(rec, open(a.json, "w"), indent=1)
    return 0 if rec["corner_support"] == "true" else 1


if __name__ == "__main__":
    sys.exit(main())
