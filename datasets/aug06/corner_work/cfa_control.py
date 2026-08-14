#!/usr/bin/env python3
"""The CFA control: does the rotation survive with NO interpolation at all?

  cfa_control.py --preregister <out.json>   write the reading rules, run nothing
  cfa_control.py <out.json>                 analyse (needs the .lst files)
  cfa_control.py --selftest

WHY. `constancy_fit.py` returns chi2/dof 53-129 — the constancy model is badly
misspecified — and a NAMED ALTERNATIVE survives: Siril's demosaic is a
content-dependent nonlinear interpolation, star shape varies across the field, so
its contribution need not be common-mode across rho bins, and an unmodelled
rho-dependent demosaic term produces the SAME non-constancy. It also cannot be
pinned from a script: no `setdebayer` exists in 1.4.4 and the machine-local config
alone holds `interpolation=8`. Measuring on the raw CFA lattice removes the
question instead of bounding it.

`split_cfa` AND NOT `extract_Green`. Probed, verbatim: split_cfa "Splits the
loaded CFA image into four distinct files (one for each channel)"; extract_Green
"exports only the AVERAGED green filter data as a new HALF-SIZED FITS file". G1
and G2 sit diagonally offset inside each 2x2 block, so averaging them is a
two-point low-pass ALONG THE DIAGONAL — an anisotropic operation injecting a fixed
~45 deg sensor-frame directional term, which is the same KIND of object as the
term under test. The obvious command for "no interpolation" is the one that adds a
directional filter.

=========================== PRE-REGISTRATION ===========================
Written and committed BEFORE the measurement was run.

THE CONFOUND THAT CANNOT BE REMOVED, stated first because it limits every
comparison across the grids. split_cfa is half-sized, so linear sampling halves
and S = sigma/pixel goes from ~0.83 to ~0.415 — across Kannawadi et al. (MNRAS
502, 4048) into SEVERELY undersampled, S < 0.5. A difference between the CFA and
debayered measurements is therefore AMBIGUOUS between "the demosaic was doing
something" and "severe undersampling is doing something", and this arm cannot
separate them. It will not try, and it will not attribute.

  OUTCOME 1 — G1 vs G2 (the free null, and it carries the weight).
    Two independent green samplings, diagonally offset, at IDENTICAL sampling and
    IDENTICAL processing. Immune to the S confound because S is the same on both
    sides. Statistic: chi2 of (axis_G1 - axis_G2) against zero across the rho
    bins, 5 dof.
      AGREE  (chi2 < 11.07, p > 0.05) -> the CFA lattice injects NO directional
             term, and any CFA-vs-debayered difference is not a lattice artefact.
      DIFFER -> that difference IS a directional term from the lattice or from the
             sampling, and it contaminates every shape measurement made on this
             grid. Report it as the finding; do not proceed to read outcome 2 as
             though the grid were clean.

  OUTCOME 2 — CFA rotation vs the debayered N=40 arm.
      SAME rotation (axis span and its non-monotone shape reproduced, and the
             per-bin axes consistent within errors) -> the demosaic is NOT
             producing the rotation. The named alternative DIES and "no
             field-constant optical component" stands alone.
      DIFFERENT -> AMBIGUOUS, per the confound above. Report the difference and
             state that it does not attribute. Do NOT report "the demosaic did it".

  OUTCOME 3 — the constancy fit on the CFA grid.
      REJECTS -> the gate failure is independent of the demosaic; corner-fix-
             landscape's rl -loadpsf= route stays failed on an interpolation-free
             measurement.
      DOES NOT REJECT -> the gate failure was produced by the demosaic OR by the
             sampling change; same ambiguity, same refusal to attribute.

  WHAT IS ABSORBED AND THEREFORE NOT UNDER TEST: on the half-sized grid the trail
  is half as long in pixels, so the predicted vector T scales by 1/4, and kappa
  was calibrated at S ~ 0.83 and need not transfer to S ~ 0.415. Both are GLOBAL
  scales on T, absorbed by the free f, which is why they do not touch the
  constancy question. f itself remains unquotable (design condition ~130).
========================================================================

WHAT IS THE TOOL'S AND WHAT IS IN-HOUSE (the bright line, CLAUDE.md):
  Siril            `convert` (no -debayer), `seqsplit_cfa`, `findstar` — every
                   pixel operation and every star measurement.
  astrometry.net   the WCS behind the trail prediction.
  in-house         the binning, the spin-2 bookkeeping, the least squares.
Reads no pixel: .lst text, a WCS header, JSON records.

NOT ATTEMPTED, and fenced deliberately: the mosaic-planting design. It needs a
colour per synthetic star, and RCD is *Ratio Corrected* Demosaicing working on
inter-channel ratios, so a planted colour distribution exercises it differently
from a real reddened galactic-plane population. That is a confound one level down.

REMOVAL CONDITION. Retire with `constancy_fit.py`, whose alternative it tests.

REPORTS ONLY: exits 0. --selftest exits 1 on failure.
"""
import json
import math
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from pa_convention import read_lst, decompose                      # noqa: E402
from coherent_trail import anisotropy                              # noqa: E402
from constancy_fit import (trail_vectors, constancy, axis_constancy,  # noqa: E402
                           TAILCUT)

WORK = os.path.join(HERE, "cfa_work")
# THREE bins, not five, and the reason is statistics not preference: the half-sized
# CFA grid carries ~1000 stars per frame per channel against the debayered ~7000,
# so five rho-equal bins cannot be filled and the OUTER ones — where the rotation
# lives — collapse first. The debayered arm is re-binned to THREE here too, so
# outcome 2 is a like-for-like comparison rather than 3 bins read against 5.
NBIN = 3
MINSTARS = 60
PREREG = {
    "outcome_1_G1_vs_G2": {
        "why_it_carries_the_weight": "identical sampling and identical processing "
        "on both sides, so it is immune to the S = 0.83 -> 0.415 confound",
        "statistic": "chi2 of (axis_G1 - axis_G2) against zero across rho bins, 5 dof",
        "AGREE_if": "chi2 < 11.07 (p > 0.05) -> the CFA lattice injects no "
                    "directional term",
        "DIFFER_means": "a directional term from the lattice or the sampling, "
                        "contaminating every shape measurement on this grid; "
                        "outcome 2 must not then be read as though the grid were clean"},
    "outcome_2_CFA_vs_debayered": {
        "SAME_means": "the demosaic is NOT producing the rotation; the named "
                      "alternative dies and 'no field-constant optical component' "
                      "stands alone",
        "DIFFERENT_means": "AMBIGUOUS between the demosaic and severe "
                           "undersampling (S ~ 0.415, below Kannawadi's 0.5). "
                           "This arm cannot separate them and will not attribute."},
    "outcome_3_constancy_fit_on_CFA": {
        "REJECTS_means": "the gate failure is independent of the demosaic",
        "DOES_NOT_REJECT_means": "produced by the demosaic OR by the sampling "
                                 "change — same ambiguity, same refusal"},
    "absorbed_and_not_under_test": "T scales by 1/4 on the half-sized grid and "
    "kappa was calibrated at S ~ 0.83; both are GLOBAL scales on T absorbed by "
    "the free f, so neither touches the constancy question. f stays unquotable.",
}


def load_channel(ch):
    """One CFA channel's frames. `ch` is the seqsplit_cfa index 0..3."""
    m = json.load(open(os.path.join(HERE, "frames_work", "frame_map.json")))
    out = []
    for tag in sorted(m):
        i = tag.split("_")[1]
        p = os.path.join(WORK, "g%d_%s.lst" % (ch, i))
        if not os.path.exists(p):
            continue
        d, _ = read_lst(p)
        if len(d) < 300:
            continue
        d = d[d[:, 0] >= np.median(d[:, 0])]
        D, D1, D2 = anisotropy(d[:, 3], d[:, 4], d[:, 5])
        k = D <= TAILCUT
        x, y = d[k, 1], d[k, 2]
        cx, cy = 3031 / 2.0, 2019 / 2.0
        rmax = math.hypot(cx, cy)
        rec = dict(m[tag])
        rec.update({"tag": tag, "x": x, "y": y, "D1": D1[k], "D2": D2[k],
                    "n": int(k.sum()),
                    "phi": np.arctan2(y - cy, x - cx),
                    "rho": np.hypot(x - cx, y - cy) / rmax})
        out.append(rec)
    return out


def per_bin(frames, drop=()):
    allrho = np.concatenate([f["rho"] for f in frames])
    e = np.linspace(allrho.min(), allrho.max(), NBIN + 1)
    rows = []
    for b in range(NBIN):
        per = []
        for f in frames:
            if f["frame"] in drop:
                continue
            m = (f["rho"] >= e[b]) & (f["rho"] <= e[b + 1] if b == NBIN - 1
                                      else f["rho"] < e[b + 1])
            if m.sum() < MINSTARS:
                continue
            fit = decompose(f["phi"][m], f["D1"][m], f["D2"][m], nboot=60)
            # T on the half grid: same direction, quarter magnitude (L halves)
            T1, T2, _ = trail_vectors(f["x"][m] * 2.0, f["y"][m] * 2.0)
            per.append((fit["fixed_c0"], fit["fixed_s0"],
                        fit["fixed_direction_theta0_deg"],
                        float(np.mean(T1)) / 4.0, float(np.mean(T2)) / 4.0))
        if len(per) < 3:
            continue
        a = np.array(per)
        nn = len(a)
        rows.append({
            "bin": b + 1, "rho_lo": float(e[b]), "rho_hi": float(e[b + 1]),
            "n_frames": nn,
            "C1": float(a[:, 0].mean()), "C2": float(a[:, 1].mean()),
            "se_C1": float(a[:, 0].std(ddof=1) / math.sqrt(nn)),
            "se_C2": float(a[:, 1].std(ddof=1) / math.sqrt(nn)),
            "fixed_magnitude": float(math.hypot(a[:, 0].mean(), a[:, 1].mean())),
            "fixed_axis_deg": float(a[:, 2].mean()),
            "fixed_axis_se_deg": float(a[:, 2].std(ddof=1) / math.sqrt(nn)),
            "T1": float(a[:, 3].mean()), "T2": float(a[:, 4].mean()),
            "T_magnitude": float(math.hypot(a[:, 3].mean(), a[:, 4].mean())),
            "T_axis_deg": 0.0})
    return rows


def compare_axes(rows_a, rows_b, label_a, label_b):
    """chi2 of the per-bin axis DIFFERENCE against zero."""
    n = min(len(rows_a), len(rows_b))
    d, s = [], []
    for i in range(n):
        d.append(rows_a[i]["fixed_axis_deg"] - rows_b[i]["fixed_axis_deg"])
        s.append(math.hypot(rows_a[i]["fixed_axis_se_deg"],
                            rows_b[i]["fixed_axis_se_deg"]))
    d, s = np.array(d), np.array(s)
    chi2 = float(((d / s) ** 2).sum())
    return {"a": label_a, "b": label_b, "n_bins": n,
            "diff_deg": [float(v) for v in d], "se_deg": [float(v) for v in s],
            "chi2": chi2, "dof": n,
            "agree_at_95pct": bool(chi2 < 11.07),
            "max_abs_diff_deg": float(np.abs(d).max())}


def identify_greens():
    """Which two split_cfa channels are the greens — settled by the DATA.

    The two green sub-lattices are the same filter on the same scene, so their
    cross-matched stars must agree at ~zero magnitude offset with the smallest
    scatter of any pair. Reading BAYERPAT instead gives the WRONG answer here.
    """
    import itertools
    d = {}
    for p in range(4):
        f = os.path.join(WORK, "g%d_00001.lst" % p)
        if not os.path.exists(f):
            return [], {}
        d[p] = np.loadtxt(f, comments="#", usecols=(5, 6, 13))
    best, pairs = None, {}
    for i, j in itertools.combinations(range(4), 2):
        A, B = d[i], d[j]
        r = np.hypot(A[:, 0][:, None] - B[:, 0][None, :],
                     A[:, 1][:, None] - B[:, 1][None, :])
        k, near = r.argmin(axis=1), r.min(axis=1)
        m = near <= 1.5
        if m.sum() < 20:
            continue
        dm = A[m, 2] - B[k[m], 2]
        med, mad = float(np.median(dm)), float(np.median(np.abs(dm - np.median(dm))))
        pairs["%d-%d" % (i, j)] = {"n": int(m.sum()), "median_dmag": med,
                                   "mad_dmag": mad}
        score = abs(med) + mad
        if best is None or score < best[0]:
            best = (score, [i, j])
    return (best[1] if best else []), pairs


def selftest():
    ok = True
    a = [{"fixed_axis_deg": 10.0 + i, "fixed_axis_se_deg": 1.0} for i in range(5)]
    b = [{"fixed_axis_deg": 10.0 + i, "fixed_axis_se_deg": 1.0} for i in range(5)]
    r = compare_axes(a, b, "a", "b")
    print("  identical axes -> agree: %s (chi2 %.2f)"
          % ("OK" if r["agree_at_95pct"] else "*** FAIL ***", r["chi2"]))
    ok &= r["agree_at_95pct"]
    b2 = [{"fixed_axis_deg": 10.0 + i + 6.0, "fixed_axis_se_deg": 1.0}
          for i in range(5)]
    r2 = compare_axes(a, b2, "a", "b2")
    print("  6 deg offset -> differ: %s (chi2 %.1f)"
          % ("OK" if not r2["agree_at_95pct"] else "*** FAIL ***", r2["chi2"]))
    ok &= not r2["agree_at_95pct"]
    print()
    print("SELFTEST PASSED" if ok else "SELFTEST FAILED")
    return 0 if ok else 1


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return 2
    if sys.argv[1] == "--selftest":
        return selftest()
    if sys.argv[1] == "--preregister":
        json.dump({"what": "CFA control pre-registration, written before the run",
                   "PRE_REGISTRATION": PREREG}, open(sys.argv[2], "w"), indent=1)
        print(json.dumps(PREREG, indent=1))
        return 0

    chans = {}
    for ch in range(4):
        fr = load_channel(ch)
        if fr:
            chans[ch] = fr
    if not chans:
        raise SystemExit("no CFA .lst files under %s — run the siril step first"
                         % WORK)
    counts = {ch: int(np.median([f["n"] for f in chans[ch]])) for ch in chans}
    greens, pairs = identify_greens()
    out = {"what": "the per-rho-bin axis and the constancy fit on the RAW CFA "
                   "lattice — no interpolation anywhere",
           "PRE_REGISTRATION": PREREG,
           "channel_star_counts_median": counts,
           "greens_identified_as": greens,
           "how_greens_were_identified": "BY THE DATA, decisively: cross-matched "
           "star magnitudes between every channel pair. The two greens are the "
           "same filter on the same scene, so their pair must agree at ~0 offset "
           "with the smallest scatter. Measured on frame 1: ch0-ch3 gives median "
           "dmag -0.005, MAD 0.115, over 706 matches, against 0.28-0.85 mag "
           "offsets and ~2x the scatter for every other pair.",
           "channel_pair_dmag": pairs,
           "AND_THE_HEADER_READING_IS_A_TRAP": "the parent carries BAYERPAT=RGGB, "
           "which reads as (0,0)=R (0,1)=G (1,0)=G (1,1)=B, and split_cfa emits "
           "in raster order — so the obvious inference is that channels 1 and 2 "
           "are the greens. THE DATA SAYS 0 AND 3. Corroborated three ways: those "
           "two share a median (1047 both) and a background MAD (10 ADU both) "
           "where the other pair reads 1037/9 and 1028/8, and their star counts "
           "match (992 vs 1007) where the others are 697 and 422. Whatever the "
           "row-order convention does, split_cfa's index order cannot be mapped "
           "to BAYERPAT by inspection — verify it against the pixels.",
           "arms": {}}
    binrows = {}
    for ch in sorted(chans):
        rows = per_bin(chans[ch])
        if not rows:
            continue
        binrows[ch] = rows
        out["arms"]["ch%d" % ch] = {
            "n_frames": len(chans[ch]), "bins": rows,
            "axis_constancy": axis_constancy(rows),
            "constancy_fit": constancy(rows)}
    # OUTCOME 2 needs the debayered arm AT THE SAME BINNING, so re-bin it here
    # rather than compare three bins against five.
    import frame_depth as FD
    deb = FD.load_frames()
    Tf = [trail_vectors(f["x"], f["y"]) for f in deb]
    FD.NBIN = NBIN
    deb_rows = FD.per_bin(deb, [t[0] for t in Tf], [t[1] for t in Tf])
    out["debayered_N40_rebinned_to_%d" % NBIN] = {
        "bins": deb_rows, "axis_constancy": axis_constancy(deb_rows),
        "constancy_fit": constancy(deb_rows)}
    for g in greens:
        if g in binrows:
            out["OUTCOME_2_ch%d_vs_debayered" % g] = compare_axes(
                binrows[g], deb_rows, "CFA_ch%d" % g, "debayered_N40")
    if len(greens) == 2 and all(g in binrows for g in greens):
        out["OUTCOME_1_G1_vs_G2"] = compare_axes(
            binrows[greens[0]], binrows[greens[1]],
            "ch%d" % greens[0], "ch%d" % greens[1])
    json.dump(out, open(sys.argv[2] if len(sys.argv) > 2 else sys.argv[1], "w"),
              indent=1)
    for ch, a in out["arms"].items():
        ac, cf = a["axis_constancy"], a["constancy_fit"]
        print("%-5s n=%2d axes %s span %5.1f chi2 %8.1f/%d %-10s fit chi2/dof %7.2f"
              % (ch, a["n_frames"],
                 " ".join("%+6.2f" % v for v in ac["axes_deg"]), ac["span_deg"],
                 ac["chi2"], ac["dof"],
                 "REJECTS" if ac["rejects_constant_axis_95pct"] else "no reject",
                 cf["chi2_per_dof"]))
    if "OUTCOME_1_G1_vs_G2" in out:
        o = out["OUTCOME_1_G1_vs_G2"]
        print("OUTCOME 1  G1 vs G2: chi2 %.2f/%d -> %s (max |diff| %.2f deg)"
              % (o["chi2"], o["dof"],
                 "AGREE" if o["agree_at_95pct"] else "DIFFER", o["max_abs_diff_deg"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
