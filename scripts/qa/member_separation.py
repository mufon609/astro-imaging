#!/usr/bin/env python3
"""Measure how much a compose's MEMBERS disagree about where a star is.

Usage:
  member_separation.py <seq-dir> [--prefix=s_] [--json=OUT] [--label=NAME]
                       [--tol=12] [--min-n=100] [--selftest]

This is the ACCEPTANCE MEASURE for any multi-member compose, and it exists
because the two instruments that were used before it are MEASURED BLIND to the
defect it catches (docs/dead-ends.md):

- background box medians cannot see star shape at all;
- corner `findstar` FWHM is a PSF FITTER, and on a DOUBLED star it fits one
  component rather than the blend — it ranked a failing union (4.95 px) as
  BETTER than the visually clean single-model control (5.29 px);
- Siril `seqtilt` is weaker still: 0.34 px off-axis aberration for the FAILING
  union against 0.40 px for the PASSING one.

So this measures the MECHANISM instead of a symptom. `register -2pass` computes
one homography per member; the compose applies exactly those. Push every
member's own detected stars through its own homography and the same star has
one position per member, in one common frame. If the members were rectified by
the same, correct optical model those positions coincide; if they were not,
they do not, and the mean of them is the smear. The number reported is that
separation, in px, BY EACH MEMBER'S OWN FIELD RADIUS.

TWO THINGS THIS FIXES, both MEASURED (docs/dead-ends.md):

1. **It no longer reads the REGISTERED copies, because they do not share a
   coordinate frame.** `seqapplyreg -framing=max` on a variable-size sequence —
   which every compose here is, since each member is its own group's
   `-framing=min` product — writes each output cropped to its OWN footprint with
   its OWN origin. MEASURED on the accepted 28-member union by solving three
   registered members: the same sky lands 611.9 px apart in x and 416.0 px in y
   between `r_s_00001` and `r_s_00026`, and the offset is CONSTANT to 0.4 px
   across three widely separated sky points, i.e. a pure translation, not a
   scale or rotation difference. Cross-matching raw pixel coordinates across
   those files compares two offset frames: two consecutive members of ONE set
   shared **zero** stars within 1 px and 67 of 2000 within 12 px, with the count
   growing smoothly with tolerance — the signature of chance nearest neighbours
   in a dense field. Mapping through the members' own stored homographies puts
   everything in the reference member's frame by construction, so no origin can
   differ.
2. **Zones are the member's OWN field radius, not canvas radius.** They were
   canvas-radial, which equals field-radial only when the members are nearly
   co-pointed. Across a re-aim the canvas centre sits between two optical axes,
   so a corner median swung 0.71 -> 3.38 px on a 0.10 change of zone bound. A
   member's residual distortion is a function of ITS OWN radius, so that is what
   the disagreement has to be binned by. Each matched star is binned by
   max(rho_a, rho_b) — the worse-placed of the two members, which is what sets
   the disagreement.

WHY THIS IS IN BOUNDS (the bright line, CLAUDE.md). Every input is a tool's:
Siril's `register -2pass` computed every homography and this only reads them out
of the sequence file it wrote, Siril's `findstar` fitted every PSF, darktable
warped the frames upstream. The in-house part is the cross-match and the median
by field zone — a DERIVED result no tool provides (Siril reports within-sequence
registration residuals, never member-to-member star-position disagreement). It
reads no deliverable pixel, reimplements no tool's analysis, and gates a build
on a tool-sourced number, which is the pipeline deciding what the data settled:
it announces the number and its instrument.

REMOVAL CONDITION: retire this the day an official tool reports headless
member-to-member POST-REGISTRATION positional residuals across a sequence
(a scriptable Siril registration-residual map, or a PixInsight equivalent).
Registered in BACKLOG.md `removal-conditions`.

NO THRESHOLDS, NO VERDICT — this MEASURES, it does not gate (user-ratified).
It carried PASS/WARN/BLOCK bands anchored to six products the owner had judged.
They were removed for three measured reasons, not for convenience:

1. **The quantity is a sum of two terms and the compose creates one of them.**
   Two internally healthy sets read 1.12 px (july31/set-01) and 0.95 px
   (aug06/set-03) composed among themselves, and 3.02 and 3.38 px when the same
   members are registered inside a 41-degree 28-member sequence — 2.5-4.7x, from
   nothing but the size of the sequence. A band cannot separate that from a real
   optical disagreement.
2. **The bands were anchored on a broken instrument.** The six cells were
   measured before the frame bug above was found; re-measured they read
   0.14 / 0.21 / 0.38 / 1.23 / 3.04 / 3.28 against 0.144 / 0.194 / 0.352 /
   0.934 / 2.991 / 2.112, which moves the user-PASSED pair out of PASS.
3. **A band would have fired on every real compose**, so it would have been
   overridden every time — and a check that ALWAYS fires trains the operator to
   bypass it, the same disease as a check that cannot fail (docs/dead-ends.md).

What actually discriminates is RELATIVE, and it needs no ratified constant:
every set measured here shows a tight cluster of members plus one or two that
break away at an end of the burst, and the break-away sits at 2.5-3x the
cluster's own scatter in five sets and at ~15x in the sixth (aug06/set-01, 4.91
px against siblings agreeing to 0.21-0.34). That is the shape a future detector
should key on. It is deliberately NOT implemented yet: the physical cause of the
break-away is still open (BACKLOG:`compose-homography-smear`), and a detector
designed before the mechanism is understood is how the last one went wrong.

A zone with fewer than --min-n matched stars reports n/a and is NOT passed;
silence is not evidence of agreement.

--selftest EXECUTES the falsification rather than arguing it (docs/dead-ends.md,
"a check that cannot fail"): it re-runs the cross-match on one member against a
copy of itself displaced by a known vector and asserts the measured separation
IS that vector, then asserts that skipping the homography re-basing REPRODUCES
the incident this file was rewritten for.
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
from siril_run import run as siril_run   # serialized invoker (BACKLOG:removal-conditions)

ZONES = (("centre", 0.00, 0.25), ("mid", 0.25, 0.55),
         ("outer", 0.55, 0.80), ("corner", 0.80, 1.01))
# open detection gate: an ELONGATED or doubled star must be DETECTED, not
# silently rejected — the whole point is to see the ones that disagree
FINDSTAR = "setfindstar reset -roundness=0.10 -relax=on -maxR=1.0"


def parse_seq(path):
    """Read Siril's OWN registration output: one homography per member, plus the
    reference index. The R1 line is `R1 <fwhm> <wfwhm> <round> .. H h00..h22 `."""
    H, ref = [], None
    for ln in open(path):
        f = ln.split()
        if not f:
            continue
        if f[0] == "S" and len(f) >= 7:
            ref = int(f[6])                      # reference_image, 0-based
        elif f[0].startswith("R") and "H" in f:
            k = f.index("H")
            H.append(np.array([float(v) for v in f[k + 1:k + 10]]).reshape(3, 3))
    return H, ref


def detect(images, work):
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
        if not os.path.exists(p):        # findstar writes NO list at zero stars
            out[tag] = np.empty((0, 2))
            continue
        xy = [(float(c[5]), float(c[6]))
              for c in (ln.split("\t") for ln in open(p)
                        if not ln.startswith("#") and ln.strip())]
        out[tag] = np.array(xy) if xy else np.empty((0, 2))
    return out


def to_common(xy, M):
    """Member pixels -> the reference member's frame, via Siril's own transform."""
    if len(xy) == 0:
        return xy
    p = M @ np.vstack([xy[:, 0], xy[:, 1], np.ones(len(xy))])
    return np.column_stack([p[0] / p[2], p[1] / p[2]])


def own_rho(xy, w, h):
    """Each star's radius in ITS OWN member, 0 at the optical axis, 1 at the
    frame corner. This is what a residual distortion is a function of."""
    if len(xy) == 0:
        return xy
    return np.hypot(xy[:, 0] - w / 2.0, xy[:, 1] - h / 2.0) / ((w * w + h * h) ** 0.5 / 2.0)


def match(a, b, tol):
    """Mutual nearest neighbour, returning the index pairs and the separation.
    Mutual, because a one-way match silently pairs a crowded field's neighbours
    and reads as agreement. A KD-tree only makes the same search tractable at
    378 pairs x 2000 stars — the semantics are identical and `--selftest`
    asserts it against a known displacement."""
    if len(a) == 0 or len(b) == 0:
        return np.empty((0, 3))
    from scipy.spatial import cKDTree
    ta, tb = cKDTree(a), cKDTree(b)
    dab, jab = tb.query(a, k=1)                 # a -> nearest in b
    dba, iba = ta.query(b, k=1)                 # b -> nearest in a
    i = np.nonzero((dab <= tol) & (iba[jab] == np.arange(len(a))))[0]
    if not len(i):
        return np.empty((0, 3))
    return np.column_stack([i, jab[i], dab[i]])


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


def selftest(stars, tags, Hc, dims, tol):
    """Break the mechanism, watch the assertion go RED, restore. Reasoning about a
    fixture is not verification — it has failed three times in this repo."""
    t = tags[0]
    base = to_common(stars[t], Hc[t])
    if len(base) < 50:
        sys.exit("selftest: need >= 50 detections on the first member")
    shift = np.array([2.75, -1.40])
    m = match(base, base + shift, tol)
    got = float(np.median(m[:, 2]))
    want = float(np.hypot(*shift))
    ok_known = abs(got - want) < 0.01
    print(f"  [selftest] known displacement {want:.3f} px -> measured {got:.3f} px"
          f"   {'OK' if ok_known else 'FAILED'}")

    # and the incident: WITHOUT the re-basing, two real members do not correspond
    if len(tags) > 1:
        a_raw, b_raw = stars[tags[0]], stars[tags[1]]
        a_com = to_common(a_raw, Hc[tags[0]])
        b_com = to_common(b_raw, Hc[tags[1]])
        n_raw = len(match(a_raw, b_raw, tol))
        n_com = len(match(a_com, b_com, tol))
        ok_inc = n_com > 2 * max(n_raw, 1)
        print(f"  [selftest] matches WITHOUT re-basing {n_raw}, WITH {n_com}"
              f"   {'OK — the incident reproduces' if ok_inc else 'FAILED'}")
    else:
        ok_inc = True
    return ok_known and ok_inc


def main():
    ap = argparse.ArgumentParser(add_help=False)
    ap.add_argument("seqdir", nargs="?")     # optional so -h prints the docstring
    ap.add_argument("--prefix", default="s_")
    ap.add_argument("--json")
    ap.add_argument("--label", default="")
    # the caller states what registered the compose: under ASTROMETRIC
    # registration these separations are computed through the LINEAR
    # homographies only and so INCLUDE each member's SIP field (~8-10 px at
    # the corner) — the very term seqapplyreg consumes at resample. The
    # number is then an upper bound on nothing; it is NOT the star-pair-era
    # quantity and must not be compared against those profiles.
    ap.add_argument("--regmodel", default="", choices=["", "starpair", "astrometric"])
    ap.add_argument("--tol", type=float, default=12.0)
    ap.add_argument("--min-n", type=int, default=100)
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("-h", "--help", action="store_true")
    a = ap.parse_args()
    if a.selftest and not a.seqdir:
        # the falsification runs against REAL members (it needs detections and
        # the .seq homographies), so a bare --selftest cannot run it — and
        # exiting into the generic docstring here read as a pass twice
        sys.exit("member_separation --selftest requires a <seq-dir> holding "
                 "members + their .seq (it falsifies against real data): "
                 "member_separation.py <seq-dir> --selftest")
    if a.help or not a.seqdir:
        sys.exit(__doc__)
    if a.prefix.startswith("r_"):
        sys.exit("member_separation: refusing the REGISTERED members (r_*). "
                 "`seqapplyreg -framing=max` gives each output its own origin "
                 "(measured 611.9 px apart on the accepted union), so their pixel "
                 "coordinates are not comparable. Point at the UNREGISTERED "
                 "members and their .seq — the homographies are in it.")

    # ABSOLUTIZE: the flatpak Siril resolves -d and every path in the .ssf from
    # its OWN cwd, so a caller-relative seq dir makes every `load` miss — and
    # findstar then writes nothing, which reads as "no stars", i.e. as agreement.
    a.seqdir = os.path.abspath(a.seqdir)
    files = sorted(glob.glob(os.path.join(a.seqdir, a.prefix + "[0-9]*.fit")))
    if len(files) < 2:
        sys.exit(f"member_separation: need >=2 members matching "
                 f"{a.prefix}*.fit in {a.seqdir}, found {len(files)}")
    seqfile = os.path.join(a.seqdir, a.prefix + ".seq")
    if not os.path.exists(seqfile):
        sys.exit(f"member_separation: no {seqfile} — run `register {a.prefix} -2pass` "
                 "first; its homographies are what puts the members in one frame")
    Hs, ref = parse_seq(seqfile)
    if len(Hs) != len(files):
        sys.exit(f"member_separation: {seqfile} holds {len(Hs)} registration rows "
                 f"for {len(files)} members — refusing to guess the pairing")
    if ref is None or not 0 <= ref < len(files):
        sys.exit(f"member_separation: {seqfile} names no usable reference image")

    tags = [re.sub(r"\.fit$", "", os.path.basename(f)) for f in files]
    dims = {}
    for t, f in zip(tags, files):
        h = fits.getheader(f)
        dims[t] = (h["NAXIS1"], h["NAXIS2"])
    # re-base onto the REFERENCE member's own frame, which is the frame the
    # compose's output is in; a common translation cancels in every pair anyway
    Href_inv = np.linalg.inv(Hs[ref])
    Hc = {t: Href_inv @ H for t, H in zip(tags, Hs)}

    work = a.seqdir
    stars = detect(list(zip(tags, files)), work)
    n_det = {t: len(stars[t]) for t in tags}
    common = {t: to_common(stars[t], Hc[t]) for t in tags}
    rho = {t: own_rho(stars[t], *dims[t]) for t in tags}

    if a.selftest:
        sys.exit(0 if selftest(stars, tags, Hc, dims, a.tol) else 1)

    pairs, worst = [], None
    for i in range(len(tags)):
        for j in range(i + 1, len(tags)):
            ta, tb = tags[i], tags[j]
            m = match(common[ta], common[tb], a.tol)
            zres = {}
            if len(m):
                ia = m[:, 0].astype(int)
                ib = m[:, 1].astype(int)
                r = np.maximum(rho[ta][ia], rho[tb][ib])   # the worse-placed member
                for name, lo, hi in ZONES:
                    sel = (r >= lo) & (r < hi)
                    zres[name] = ({"px": round(float(np.median(m[sel, 2])), 3),
                                   "n": int(sel.sum())} if sel.sum() >= a.min_n
                                  else {"px": None, "n": int(sel.sum())})
            else:
                zres = {name: {"px": None, "n": 0} for name, _, _ in ZONES}
            vals = [z["px"] for z in zres.values() if z["px"] is not None]
            mx = max(vals) if vals else None
            rec = {"a": ta, "b": tb, "matched": int(len(m)),
                   "zones": zres, "max_px": mx}
            pairs.append(rec)
            if mx is not None and (worst is None or mx > worst["max_px"]):
                worst = rec

    # every zone of every pair must be measurable or it is not evidence
    unmeasured = [f"{p['a']}|{p['b']}" for p in pairs if p["max_px"] is None]

    rec = {"label": a.label or os.path.basename(os.path.dirname(a.seqdir)),
           "instrument": "Siril register -2pass (its own per-member homographies, "
                         "read from the .seq) + Siril findstar per UNREGISTERED "
                         "member (open gate) + mutual-nearest cross-match in the "
                         "reference member's frame, median separation binned by "
                         "MEMBER-OWN field radius",
           "reference_member": tags[ref], "members": len(files),
           "member_dims": {t: list(dims[t]) for t in tags}, "detected": n_det,
           "zones_def": {n: [lo, hi] for n, lo, hi in ZONES},
           "zone_basis": "max(rho_a, rho_b), each star's radius in its OWN member "
                         "normalised by that member's half-diagonal",
           "tol_px": a.tol, "min_n": a.min_n,
           **({"regmodel_caveat":
               "ASTROMETRIC compose: separations are computed through the "
               "LINEAR homographies only and INCLUDE each member's SIP field "
               "(~8-10 px at the corner), which seqapplyreg consumes at "
               "resample — NOT comparable to star-pair-era profiles"}
              if a.regmodel == "astrometric" else {}),
           "reports_only": "MEASUREMENT, not a gate — no threshold, no verdict. "
                           "The quantity mixes a real member disagreement with one "
                           "the compose's own global registration creates (measured "
                           "2.5-4.7x from sequence size alone), so a band on it "
                           "would not mean what it appears to mean.",
           "optics": {t: optics(f) for t, f in zip(tags, files)},
           "pairs": pairs, "worst": worst,
           "unmeasured_pairs": unmeasured}

    print(f"member separation ({len(files)} members, reference {tags[ref]}, "
          "binned by MEMBER-OWN field radius):")
    print(f"  {'pair':<24}" + "".join(f"{n:>10}" for n, _, _ in ZONES) + f"{'max':>9}")
    for p in sorted(pairs, key=lambda p: -(p["max_px"] or -1))[:40]:
        cells = "".join((f"{p['zones'][n]['px']:10.2f}"
                         if p["zones"][n]["px"] is not None
                         else f"{'n/a':>10}") for n, _, _ in ZONES)
        mx = f"{p['max_px']:9.2f}" if p["max_px"] is not None else f"{'-':>9}"
        print(f"  {p['a']}|{p['b']:<12}" + cells + mx)
    if len(pairs) > 40:
        print(f"  … {len(pairs) - 40} further pairs in the record")
    if worst is not None:
        print(f"  worst zone {worst['max_px']:.2f} px  ({worst['a']}|{worst['b']}) "
              "— MEASURED, not gated: no threshold is applied here")
    else:
        print("  UNMEASURED — no pair produced a zone with "
              f">= {a.min_n} matched stars")
    if unmeasured:
        print(f"  {len(unmeasured)} pair(s) had no zone with >= {a.min_n} matches "
              "(reported n/a, never passed)")
    if a.json:
        os.makedirs(os.path.dirname(os.path.abspath(a.json)), exist_ok=True)
        json.dump(rec, open(a.json, "w"), indent=1)
        print(f"  record: {a.json}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
