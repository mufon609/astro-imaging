#!/usr/bin/env python3
"""Frame-cull analysis over pooled per-frame registration records
(WARN-only: this tool reports and suggests; the DECISION is per-dataset
recipe state adopted through a with/without ladder — README's stack-policy
doctrine).

Input: the records_<variant>.jsonl a partitioned_stack.py run harvests
(one record per staged frame: n, fwhm, wfwhm, round, bg, nstars,
registered, ref_copy) or any file of the same shape. Pooling is valid
across partitions because every partition registers to the SAME pinned
reference frame.

Flags use the registration inspection's calibrated rule: robust z vs the
pooled median/MAD, DEFECT SIDE ONLY (fwhm+, bg+, round-, nstars-), at
z >= 3.5 (the 11-sequence calibration where non-event frames stay under
|z|~3.4 and every 3.5+ flag mapped to a physical event). wfwhm excess is
REPORTED, never a cull input here: with one common reference it mixes
matching loss with honest drift distance (measured: clear frames at 60+
frame distance read wfwhm 5.3-6.6 vs 2.6 at the reference).

Registration FAILURES are listed separately: siril already drops them
from every stack, so they never enter an exclude list.
"""
import argparse
import json
import os
import sys

import numpy as np

DEFECT_SIDE = {"fwhm": +1, "bg": +1, "round": -1, "nstars": -1}


def robust_z(vals):
    v = np.asarray(vals, dtype=float)
    med = np.median(v)
    mad = np.median(np.abs(v - med)) * 1.4826
    mad = max(mad, 1e-9)
    return (v - med) / mad, med, mad


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("records", help="records_<variant>.jsonl")
    ap.add_argument("--z", type=float, default=3.5)
    ap.add_argument("--preview", default=None,
                    help="optional preview area_metrics.json to cross-"
                         "reference (advisory column only)")
    args = ap.parse_args()

    recs = [json.loads(l) for l in open(args.records)]
    recs = [r for r in recs if not r.get("ref_copy")]
    reg = [r for r in recs if r["registered"]]
    fail = [r for r in recs if not r["registered"]]
    if len(reg) < 8:
        sys.exit(f"only {len(reg)} registered records — nothing to pool")

    prev = {}
    if args.preview and os.path.isfile(args.preview):
        for p in json.load(open(args.preview)):
            prev[p["n"]] = p.get("area25")

    zs, stats = {}, {}
    for m in DEFECT_SIDE:
        z, med, mad = robust_z([r[m] for r in reg])
        zs[m] = z * DEFECT_SIDE[m]   # positive = defect direction
        stats[m] = (med, mad)
    wex = [r["wfwhm"] / max(r["fwhm"], 1e-6) - 1 for r in reg]

    print(f"pooled frame QA: {len(reg)} registered / {len(fail)} "
          f"match-failed of {len(recs)} kept frames")
    for m in DEFECT_SIDE:
        med, mad = stats[m]
        print(f"  {m:7s} median {med:9.3f}  MAD*1.4826 {mad:8.3f}  "
              f"defect side {'+' if DEFECT_SIDE[m] > 0 else '-'}")
    print(f"  wfwhm excess (reported only): median "
          f"{np.median(wex):.3f}, p90 {np.percentile(wex, 90):.3f}")

    flagged = {}
    for i, r in enumerate(reg):
        hits = {m: round(float(zs[m][i]), 2) for m in DEFECT_SIDE
                if zs[m][i] >= args.z}
        if hits:
            flagged[r["n"]] = (r, hits)
    if flagged:
        print(f"\nflagged at defect-side z >= {args.z}:")
        print("   n  file            part  "
              + "".join(f"{m:>9s}" for m in DEFECT_SIDE)
              + "   flags" + ("   area25%" if prev else ""))
        for n in sorted(flagged):
            r, hits = flagged[n]
            i = reg.index(r)
            row = "".join(f"{float(zs[m][i]):9.2f}" for m in DEFECT_SIDE)
            extra = f"   {prev.get(n, ''):>6}" if prev else ""
            print(f" {n:3d}  {r['file']:14s}  {r['part']:3d} {row}   "
                  f"{','.join(hits)}{extra}")
    else:
        print(f"\nno frame flags at defect-side z >= {args.z}")
    if fail:
        print("\nmatch-failed (never stack; no exclude needed): "
              + ", ".join(f"{r['n']}({r['file']})" for r in fail))

    if flagged:
        excl = sorted(flagged)
        print(f"\nsuggested recipe stack block (rung E1 — adopt only on a "
              f"measured with/without ladder):")
        print(json.dumps({"stack": {"weight": None, "exclude": excl}},
                         indent=2))


if __name__ == "__main__":
    main()
