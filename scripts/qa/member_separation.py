#!/usr/bin/env python3
"""Measure how much a compose's MEMBERS disagree about where a star is.

Usage:
  member_separation.py <registered-seq-dir> [--prefix=r_] [--json=OUT]
                       [--label=NAME] [--tol=12] [--min-n=200]
                       [--pass=0.35] [--block=1.00] [--members=<name>,...]

This is the ACCEPTANCE MEASURE for any multi-member compose, and it exists
because the two instruments that were used before it are MEASURED BLIND to the
defect it catches (docs/dead-ends.md):

- background box medians cannot see star shape at all;
- corner `findstar` FWHM is a PSF FITTER, and on a DOUBLED star it fits one
  component rather than the blend — it ranked a failing union (4.95 px) as
  BETTER than the visually clean single-model control (5.29 px);
- Siril `seqtilt` is weaker still: 0.34 px off-axis aberration for the FAILING
  union against 0.40 px for the PASSING one.

So this measures the MECHANISM instead of a symptom. After the compose has
registered its members into one canvas, the same star has one position per
member. If the members were rectified by the same, correct optical model those
positions coincide; if they were not, they do not, and the mean of them is the
smear. The number reported is that separation, in px, by field zone.

WHY THIS IS IN BOUNDS (the bright line, CLAUDE.md). Every input is a tool's:
Siril registered the members, Siril's `findstar` fitted every PSF, darktable
warped the frames upstream. The in-house part is the cross-match and the median
by zone — a DERIVED result no tool provides (Siril reports within-sequence
registration residuals, never member-to-member star-position disagreement in a
composed canvas). It reads no deliverable pixel, reimplements no tool's
analysis, and gates a build on a tool-sourced number, which is the pipeline
deciding what the data settled: it announces the number and its instrument.

REMOVAL CONDITION: retire this the day an official tool reports headless
member-to-member POST-REGISTRATION positional residuals across a sequence
(a scriptable Siril registration-residual map, or a PixInsight equivalent).
Registered in BACKLOG.md `removal-conditions`.

THRESHOLDS — each traced to a product the owner judged, never to a round number
picked for looking reasonable (docs/combine-contract.md 5):

  PASS  <= 0.35 px  the july31 cross-set pair, from the union the owner PASSED.
                    PROVISIONAL: n=1 exemplar — re-anchor as corner-true fits
                    produce more passed products.
  WARN  <= 1.00 px  0.93 px is aug06 under one shared model: round at 1:1 when
                    looked at, but 2.7x the passed level and never accepted, so
                    the build proceeds and the surface must get eyes at 1:1.
  BLOCK  > 1.00 px  2.11 px and 2.99 px are the two products the owner FAILED,
                    both visibly doubled at 1:1. The threshold is a CHOICE
                    inside the measured interval (0.93, 2.11]; 1.00 is the
                    conservative end (user-set), pending the bisection arm.

For scale, the floor this instrument can read — same set, same optical state,
same model — is 0.14 px (aug06) / 0.19 px (july31).

A zone with fewer than --min-n matched stars reports n/a and is NOT passed;
silence is not evidence of agreement.

--min-n IS MEASURED, not guessed. The corner zone is a small slice of a
rectangular canvas and Siril's `findstar` caps at 2000 stars per image, so it
lands at n = 145-208 on real member pairs — a floor set by eye at 200 silently
discarded the decisive zone in five of six calibration cells. Bootstrap of the
corner median (2000 resamples, the six cells above), 5th-95th percentile band:

  cell (true corner median)   n=40         n=60         n=100        n=150
  A6  2.11 px                 1.37-2.62    1.55-2.47    1.69-2.31    1.84-2.24
  A2  2.99 px                 2.74-9.65    2.81-9.37    2.90-9.09    2.97-5.94
  A3  0.93 px                 0.48-1.13    0.55-1.06    0.66-1.03    0.76-1.01
  A4  0.35 px                 0.29-0.40    0.31-0.38    0.32-0.36    -

At n >= 100 every verdict is stable: the two user-FAILED cells stay BLOCK by a
wide margin and the user-PASSED cell stays PASS. The one cell whose band
straddles a threshold (A3, 0.66-1.03 against the 1.00 block line) does so
because its true value sits 7% from that line — no sample size fixes that, and
it is a property of the case, not of the floor. Hence the default of 100.
"""
import argparse
import glob
import json
import os
import re
import sys

import numpy as np
from astropy.io import fits            # header READ only — no pixel access here

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "lib"))
from siril_run import SIRIL, run as siril_run   # serialized invoker (BACKLOG item 18)

ZONES = (("centre", 0.00, 0.25), ("mid", 0.25, 0.55),
         ("outer", 0.55, 0.80), ("corner", 0.80, 1.01))
# open detection gate: an ELONGATED or doubled star must be DETECTED, not
# silently rejected — the whole point is to see the ones that disagree
FINDSTAR = "setfindstar reset -roundness=0.10 -relax=on -maxR=1.0"


def detect(seqdir, images, work):
    """Siril fits every PSF; this only writes the .ssf and reads the lists back."""
    ssf = os.path.join(work, "_msep.ssf")                 # MUST be under $HOME:
    lines = ["requires 1.2.0", "set32bits", "setcompress 0",  # flatpak private /tmp
             "setext fit", FINDSTAR]
    for tag, path in images:
        lines += [f"load {path}",
                  f"findstar -out={work}/msep_{tag}.lst -layer=1 -maxstars=2000"]
    open(ssf, "w").write("\n".join(lines) + "\n")
    siril_run(["-d", work, "-s", ssf], capture_output=True, text=True)
    out = {}
    for tag, _ in images:
        p = f"{work}/msep_{tag}.lst"
        if not os.path.exists(p):
            out[tag] = np.empty((0, 2))
            continue
        xy = []
        for ln in open(p):
            if ln.startswith("#") or not ln.strip():
                continue
            c = ln.split("\t")
            xy.append((float(c[5]), float(c[6])))
        out[tag] = np.array(xy) if xy else np.empty((0, 2))
    return out


def match(a, b, tol):
    """Mutual nearest neighbour. Mutual, because a one-way match silently pairs
    a crowded field's neighbours and reads as agreement."""
    if len(a) == 0 or len(b) == 0:
        return np.empty((0, 3))
    out = []
    for i in range(len(a)):
        d = np.hypot(b[:, 0] - a[i, 0], b[:, 1] - a[i, 1])
        j = int(np.argmin(d))
        if d[j] > tol:
            continue
        d2 = np.hypot(a[:, 0] - b[j, 0], a[:, 1] - b[j, 1])
        if int(np.argmin(d2)) != i:
            continue
        out.append((a[i, 0], a[i, 1], d[j]))
    return np.array(out) if out else np.empty((0, 3))


def optics(path):
    """The member's own optics provenance, from its header — no external lookup.
    Absent on any sub-stack built before the stamp existed; reported as such."""
    try:
        h = fits.getheader(path)
    except OSError:
        return {}
    k = {x: h.get(x) for x in ("DISTMODL", "DISTA", "DISTB", "DISTC",
                               "DISTNORM", "DISTRHO", "DISTSRC", "CALSET")}
    return {x: v for x, v in k.items() if v is not None}


def main():
    ap = argparse.ArgumentParser(add_help=False)
    ap.add_argument("seqdir")
    ap.add_argument("--prefix", default="r_")
    ap.add_argument("--json")
    ap.add_argument("--label", default="")
    ap.add_argument("--tol", type=float, default=12.0)
    ap.add_argument("--min-n", type=int, default=100)
    ap.add_argument("--pass", dest="pass_px", type=float, default=0.35)
    ap.add_argument("--block", type=float, default=1.00)
    ap.add_argument("-h", "--help", action="store_true")
    a = ap.parse_args()
    if a.help:
        sys.exit(__doc__)

    # ABSOLUTIZE: the flatpak Siril resolves -d and every path in the .ssf from
    # its OWN cwd, so a caller-relative seq dir makes every `load` miss — and
    # findstar then writes nothing, which reads as "no stars", i.e. as agreement.
    a.seqdir = os.path.abspath(a.seqdir)
    files = sorted(glob.glob(os.path.join(a.seqdir, a.prefix + "*.fit")))
    if len(files) < 2:
        sys.exit(f"member_separation: need >=2 registered members matching "
                 f"{a.prefix}*.fit in {a.seqdir}, found {len(files)}")
    tags = [re.sub(r"\.fit$", "", os.path.basename(f)) for f in files]
    h = fits.getheader(files[0])
    W, H = h["NAXIS1"], h["NAXIS2"]
    cx, cy, R = W / 2.0, H / 2.0, (W * W + H * H) ** 0.5 / 2.0

    work = a.seqdir
    stars = detect(a.seqdir, list(zip(tags, files)), work)
    n_det = {t: len(stars[t]) for t in tags}

    pairs, worst = [], None
    for i in range(len(tags)):
        for j in range(i + 1, len(tags)):
            m = match(stars[tags[i]], stars[tags[j]], a.tol)
            zres = {}
            if len(m):
                r = np.hypot(m[:, 0] - cx, m[:, 1] - cy) / R
                for name, lo, hi in ZONES:
                    sel = (r >= lo) & (r < hi)
                    zres[name] = ({"px": round(float(np.median(m[sel, 2])), 3),
                                   "n": int(sel.sum())} if sel.sum() >= a.min_n
                                  else {"px": None, "n": int(sel.sum())})
            else:
                zres = {name: {"px": None, "n": 0} for name, _, _ in ZONES}
            vals = [z["px"] for z in zres.values() if z["px"] is not None]
            mx = max(vals) if vals else None
            rec = {"a": tags[i], "b": tags[j], "matched": int(len(m)),
                   "zones": zres, "max_px": mx}
            pairs.append(rec)
            if mx is not None and (worst is None or mx > worst["max_px"]):
                worst = rec

    # every zone of every pair must be measurable or it is not evidence
    unmeasured = [f"{p['a']}|{p['b']}" for p in pairs if p["max_px"] is None]
    if worst is None:
        verdict, why = "UNMEASURED", ("no pair produced a zone with >= "
                                      f"{a.min_n} matched stars")
    # Decide at the precision the numbers are REPORTED and cited at (2 dp). The
    # PASS anchor is itself a measured product — the july31 cross-set pair, whose
    # corner reads 0.352 px — and a raw float comparison against the 0.35 px it
    # is quoted as would put the anchor 0.002 px outside its own threshold.
    elif round(worst["max_px"], 2) <= a.pass_px:
        verdict, why = "PASS", f"worst zone {worst['max_px']:.2f} px <= {a.pass_px} px"
    elif round(worst["max_px"], 2) <= a.block:
        verdict, why = "WARN", (f"worst zone {worst['max_px']:.2f} px is above the "
                                f"{a.pass_px} px passed level — build may proceed, "
                                "the surface needs eyes at 1:1 before it ships")
    else:
        verdict, why = "BLOCK", (f"worst zone {worst['max_px']:.2f} px exceeds "
                                 f"{a.block} px — this composes a visibly doubled "
                                 "product (2.11/2.99 px were user-FAILED)")

    rec = {"label": a.label or os.path.basename(os.path.dirname(a.seqdir)),
           "instrument": "Siril register (upstream) + Siril findstar per registered "
                         "member (open gate) + mutual-nearest cross-match, median "
                         "separation by canvas zone",
           "canvas": [W, H], "members": len(files), "detected": n_det,
           "zones_def": {n: [lo, hi] for n, lo, hi in ZONES},
           "tol_px": a.tol, "min_n": a.min_n,
           "thresholds_px": {"pass": a.pass_px, "block": a.block,
                             "pass_anchor": "july31 cross-set pair (user-PASSED "
                                            "union) — PROVISIONAL, n=1 exemplar",
                             "block_basis": "measured interval (0.93 round at 1:1, "
                                            "2.11 doubled at 1:1]; user-set at the "
                                            "conservative end"},
           "optics": {t: optics(f) for t, f in zip(tags, files)},
           "pairs": pairs, "worst": worst,
           "unmeasured_pairs": unmeasured,
           "verdict": verdict, "why": why}

    print(f"member separation ({len(files)} members, canvas {W}x{H}):")
    print(f"  {'pair':<24}" + "".join(f"{n:>10}" for n, _, _ in ZONES) + f"{'max':>9}")
    for p in sorted(pairs, key=lambda p: -(p["max_px"] or -1)):
        cells = "".join((f"{p['zones'][n]['px']:10.2f}"
                         if p["zones"][n]["px"] is not None
                         else f"{'n/a':>10}") for n, _, _ in ZONES)
        mx = f"{p['max_px']:9.2f}" if p["max_px"] is not None else f"{'-':>9}"
        print(f"  {p['a']}|{p['b']:<12}" + cells + mx)
    print(f"  VERDICT: {verdict} — {why}")
    if unmeasured:
        print(f"  {len(unmeasured)} pair(s) had no zone with >= {a.min_n} matches "
              "(reported n/a, never passed)")
    if a.json:
        os.makedirs(os.path.dirname(os.path.abspath(a.json)), exist_ok=True)
        json.dump(rec, open(a.json, "w"), indent=1)
        print(f"  record: {a.json}")
    return {"PASS": 0, "WARN": 0, "WARN_": 0}.get(verdict, 3 if verdict == "BLOCK" else 4)


if __name__ == "__main__":
    sys.exit(main())
