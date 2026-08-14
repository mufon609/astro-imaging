#!/usr/bin/env python3
"""Put FRAMES behind the verdict: the per-rho-bin axis and the constancy fit at N=40.

  frame_depth.py <out.json>
  frame_depth.py --selftest

WHY. `constancy_fit.py` established that the dominant error term on a per-bin
fixed term is FRAME-TO-FRAME scatter — a median 5.76x the star-level bootstrap —
and then the route-killing verdict turned out to rest on 4 frames against 5.
Frames were both the error term and the fragility, and the set holds 500 of them
while the measurement used five. This re-runs it on 40.

THE SAMPLE IS DESIGNED, NOT CONVENIENT. aug06/set-01 is DSC_6239..6738 in five
groups of 100. From each group: the first FOUR frames (index 0-3) and four spread
through it (index 25, 50, 75, 99). That gives 20 early-in-run and 20 mid/late
frames, and it answers a question the 5-frame sample could not:

  IS "FIRST FRAME OF A RUN" A CLASS, OR IS DSC_6239 UNIQUE? If the other four
  group-starts share its signature, the exclusion used throughout this thread is a
  SYSTEMATIC and changes meaning everywhere it has been applied — including the
  injection rebuild, and including `psf_work/f{1,2,3}.lst`, which is Gate 1A's
  sample and is built from DSC_6239 / 6339 / 6439: the first frames of groups
  1, 2 and 3.

All five of the original memraw frames (6239, 6264, 6289, 6314, 6338) are in the
sample, so the 5-frame result is an exact SUBSET BRACKET rather than a re-run.

WHAT IS THE TOOL'S AND WHAT IS IN-HOUSE (the bright line, CLAUDE.md):
  Siril            every star: `convert -debayer` then `findstar`, the same call
                   the rest of this thread used, verbatim.
  astrometry.net   the WCS behind the trail prediction.
  Siril            the conversion constant (psf_calib.json's fitted kappa).
  in-house         the binning, the spin-2 bookkeeping, the least squares.
Reads no pixel: .lst text, a WCS header, JSON records.

CARRIED FORWARD, NOT RE-ARGUED: the demosaic confound (`constancy_fit.json`)
applies here identically — every frame passed through Siril's demosaic, which
cannot be pinned from a script.

REMOVAL CONDITION. Retire with `constancy_fit.py`, which it re-runs at depth.

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

WORK = os.path.join(HERE, "frames_work")
NBIN = 5


def load_frames():
    m = json.load(open(os.path.join(WORK, "frame_map.json")))
    acq = json.load(open(os.path.join(os.path.dirname(HERE), "set-01",
                                      "acquisition.json")))["exif"]
    W, H = acq["image_wh"]
    cx, cy = (W - 1) / 2.0, (H - 1) / 2.0
    rmax = math.hypot(cx, cy)
    out = []
    for tag in sorted(m):
        p = os.path.join(WORK, "s_%s.lst" % tag.split("_")[1])
        if not os.path.exists(p):
            continue
        d, _ = read_lst(p)
        d = d[d[:, 0] >= np.median(d[:, 0])]
        D, D1, D2 = anisotropy(d[:, 3], d[:, 4], d[:, 5])
        k = D <= TAILCUT
        x, y = d[k, 1], d[k, 2]
        rec = dict(m[tag])
        rec.update({"tag": tag, "x": x, "y": y, "D1": D1[k], "D2": D2[k],
                    "n": int(k.sum()),
                    "phi": np.arctan2(y - cy, x - cx),
                    "rho": np.hypot(x - cx, y - cy) / rmax})
        out.append(rec)
    return out


def whole_frame_axis(frames):
    """One fixed-term axis per frame — the simplest statistic for the class test."""
    for f in frames:
        fit = decompose(f["phi"], f["D1"], f["D2"], nboot=60)
        f["axis_deg"] = fit["fixed_direction_theta0_deg"]
        f["amp"] = fit["fixed_amplitude"]
    return frames


def per_bin(frames, T1f, T2f, drop=()):
    """Per-bin fixed term as a MEAN over frames with a FRAME-BASED SE."""
    allrho = np.concatenate([f["rho"] for f in frames])
    e = np.linspace(allrho.min(), allrho.max(), NBIN + 1)
    rows = []
    for b in range(NBIN):
        per = []
        for j, f in enumerate(frames):
            if f["frame"] in drop:
                continue
            m = (f["rho"] >= e[b]) & (f["rho"] <= e[b + 1] if b == NBIN - 1
                                      else f["rho"] < e[b + 1])
            if m.sum() < 150:
                continue
            fit = decompose(f["phi"][m], f["D1"][m], f["D2"][m], nboot=60)
            per.append((fit["fixed_c0"], fit["fixed_s0"],
                        fit["fixed_direction_theta0_deg"],
                        float(np.mean(T1f[j][m])), float(np.mean(T2f[j][m]))))
        if len(per) < 3:
            continue
        a = np.array(per)
        nn = len(a)
        rows.append({
            "bin": b + 1, "rho_lo": float(e[b]), "rho_hi": float(e[b + 1]),
            "n_frames": nn,
            "C1": float(a[:, 0].mean()), "C2": float(a[:, 1].mean()),
            "error_model": "frame_based",   # the frames ARE independent
            "se_C1_frame_based": float(a[:, 0].std(ddof=1) / math.sqrt(nn)),
            "se_C2_frame_based": float(a[:, 1].std(ddof=1) / math.sqrt(nn)),
            "fixed_magnitude": float(math.hypot(a[:, 0].mean(), a[:, 1].mean())),
            "fixed_axis_deg": float(a[:, 2].mean()),
            "fixed_axis_se_deg_frame_based": float(a[:, 2].std(ddof=1) / math.sqrt(nn)),
            "T1": float(a[:, 3].mean()), "T2": float(a[:, 4].mean()),
            "T_magnitude": float(math.hypot(a[:, 3].mean(), a[:, 4].mean())),
            "T_axis_deg": 0.0,
        })
    return rows


def selftest():
    """The class test must be able to find NOTHING when nothing is there."""
    rng = np.random.default_rng(3)
    a = rng.normal(10.0, 2.0, 40)
    early = np.zeros(40, bool)
    early[::8] = True
    d = a[early].mean() - a[~early].mean()
    s = math.hypot(a[early].std(ddof=1) / math.sqrt(early.sum()),
                   a[~early].std(ddof=1) / math.sqrt((~early).sum()))
    ok1 = abs(d / s) < 3
    a2 = a.copy()
    a2[early] -= 30.0                       # plant a real class offset
    d2 = a2[early].mean() - a2[~early].mean()
    s2 = math.hypot(a2[early].std(ddof=1) / math.sqrt(early.sum()),
                    a2[~early].std(ddof=1) / math.sqrt((~early).sum()))
    ok2 = abs(d2 / s2) > 5
    print("  %-52s %s (%.1f sigma)" % ("no planted class -> not detected",
                                       "OK" if ok1 else "*** FAIL ***", d / s))
    print("  %-52s %s (%.1f sigma)" % ("planted class -> detected",
                                       "OK" if ok2 else "*** FAIL ***", d2 / s2))
    print()
    if ok1 and ok2:
        print("SELFTEST PASSED")
        return 0
    print("SELFTEST FAILED")
    return 1


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return 2
    if sys.argv[1] == "--selftest":
        return selftest()
    frames = whole_frame_axis(load_frames())
    Tf = [trail_vectors(f["x"], f["y"]) for f in frames]
    T1f, T2f = [t[0] for t in Tf], [t[1] for t in Tf]

    # --- Q3: is "first frame of a run" a CLASS? -----------------------------
    ax = np.array([f["axis_deg"] for f in frames])
    idx = np.array([f["index_in_group"] for f in frames])
    grp = np.array([f["group"] for f in frames])
    cls = {}
    for lab, sel in (("index_0_group_starts", idx == 0),
                     ("index_1", idx == 1), ("index_2", idx == 2),
                     ("index_3", idx == 3), ("index_25_plus", idx >= 25)):
        cls[lab] = {"n": int(sel.sum()), "mean_axis_deg": float(ax[sel].mean()),
                    "sd": float(ax[sel].std(ddof=1)) if sel.sum() > 1 else None,
                    "frames": [frames[i]["frame"] for i in np.where(sel)[0]],
                    "axes": [float(v) for v in ax[sel]]}
    ref = ax[idx >= 25]
    st = cls["index_0_group_starts"]
    sd = math.hypot(np.std(ax[idx == 0], ddof=1) / math.sqrt((idx == 0).sum()),
                    ref.std(ddof=1) / math.sqrt(len(ref)))
    cls["VERDICT"] = {
        "offset_deg": st["mean_axis_deg"] - float(ref.mean()),
        "se_deg": float(sd),
        "sigma": float(abs(st["mean_axis_deg"] - ref.mean()) / sd),
        "reads": "group-starts against index>=25 frames, whole-frame fixed axis"}

    out = {"what": "the per-rho-bin axis and the constancy fit at N=40 frames, "
                   "with FRAME-BASED errors sampled from the frame population",
           "n_frames": len(frames), "nbin": NBIN,
           "frames": [{k: f[k] for k in ("frame", "group", "index_in_group",
                                         "n", "axis_deg", "amp")}
                      for f in frames],
           "Q3_is_first_frame_of_a_run_a_class": cls,
           "arms": {}}

    memraw5 = ("DSC_6239", "DSC_6264", "DSC_6289", "DSC_6314", "DSC_6338")
    for lab, keep, drop in (
            ("N40_all", None, ()),
            ("N40_drop_DSC_6239", None, ("DSC_6239",)),
            ("N40_drop_all_group_starts", None,
             tuple(f["frame"] for f in frames if f["index_in_group"] == 0)),
            ("SUBSET_the_original_5", memraw5, ()),
            ("SUBSET_the_original_5_drop_6239", memraw5, ("DSC_6239",))):
        fs = frames if keep is None else [f for f in frames if f["frame"] in keep]
        ii = [i for i, f in enumerate(frames) if f in fs]
        rows = per_bin(fs, [T1f[i] for i in ii], [T2f[i] for i in ii], drop=drop)
        if not rows:
            continue
        out["arms"][lab] = {"n_frames_used": len(fs) - len(drop),
                            "bins": rows, "axis_constancy": axis_constancy(rows),
                            "constancy_fit": constancy(rows)}
    json.dump(out, open(sys.argv[1], "w"), indent=1)

    print("Q3 group-starts vs index>=25: offset %+.2f +- %.2f deg = %.1f sigma"
          % (cls["VERDICT"]["offset_deg"], cls["VERDICT"]["se_deg"],
             cls["VERDICT"]["sigma"]))
    for lab, a in out["arms"].items():
        ac, cf = a["axis_constancy"], a["constancy_fit"]
        print("%-34s n=%2d  axis span %5.1f  chi2 %7.1f/%d %-14s | fit chi2/dof %6.2f  f=%6.2f+-%.2f"
              % (lab, a["n_frames_used"], ac["span_deg"], ac["chi2"], ac["dof"],
                 "REJECTS" if ac["rejects_constant_axis_95pct"] else "no reject",
                 cf["chi2_per_dof"], cf["f"], cf["f_se"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
