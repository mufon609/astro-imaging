#!/usr/bin/env python3
"""Anomalous-transient audit: flag frames holding an OUT-OF-THE-ORDINARY
streak (a curved or brightness-modulated track, not the straight uniform line
a satellite or plane leaves). REPORT-ONLY — it never moves, deletes, or
rewrites any input frame, and it does not gate or feed the final-product
pipeline; it emits a list of flagged frames with the measured evidence.

  Usage: anomaly_audit.py <frame.NEF | dir | glob> [--work=<dir>]
                          [--session=<dir> --set=<name>] [--curv=<ratio>]
                          [--json=<out>] [--keep-resid]

ORDINARY (never flagged): stars (any trailing), and a straight, uniform
streak — a satellite or aircraft, which rejection stacking already removes.
Grading the subs (FWHM / roundness / background / star count) is a SEPARATE,
already-solved job (Siril `register` -> `cull_report.py`); this tool does not
touch it.

ANOMALOUS (flagged): a streak whose pixels bend off a straight line (curvature
>= --curv over a track long enough to trust), or whose along-track brightness
is strongly non-uniform / periodic (tumbler flare, unexpected strobe). No
off-the-shelf tool detects this.

WHAT SIRIL DOES vs WHAT IS IN-HOUSE  (mechanism honesty — the repo sources
every pixel operation and every STANDARD measurement from a tool, and writes
in-house code only for a derived result no tool provides):

  Siril (subprocess per frame, like solve_field.py drives astrometry.net):
    load          decode the native NEF (a Bayer CFA mosaic)
    extract_Green CFA -> a CLEAN single-channel GREEN image (half the full-
                  frame linear resolution). Explicit, so the analysis DOMAIN is
                  deterministic — never the ambient debayer setting. Everything
                  below runs on this green, never the mosaic. (extract_Green
                  saves the green to a file that MUST be re-loaded, else subsky/
                  findstar run on the mosaic — verified failure mode.)
    subsky        background extraction (flatten vignette + Milky-Way glow so a
                  faint track clears threshold) -> the residual image
    save          write the residual FITS the kernel reads
    findstar      the stellar PSF table (median trail length -> the adaptive
                  streak-length floor), the star catalog, AND the background
                  level + noise it reports -> the detection threshold, parsed
                  from Siril, NOT recomputed in-house. On the clean green these
                  EQUAL Siril `stat`'s Median/bgnoise exactly (verified 1117 /
                  14.50 both), so either is correct here; findstar's is used
                  because findstar is already invoked for the star table. (The
                  earlier CFA-mosaic domain inflated `stat` bgnoise ~2x via the
                  Bayer checkerboard; extracting green removes that entirely.)

  In-house kernel (numpy/scipy, EXAMINE only — reads Siril's products, writes
  no deliverable). These ARE pixel operations; they are not Siril:
    - reads Siril's green residual FITS (shared read_fits) + findstar's star list
    - STREAK DETECTION: threshold the green residual at bg + k*noise (both from
      findstar's report) and connected-component label it (ndimage.label).
      findstar emits STARS; no tool emits streaks, so the streak-finding is
      in-house.
    - reads residual pixel brightness inside each component (for the weights)
    - STREAK GEOMETRY: principal-axis fit -> curvature (deviation from a
      straight line); along-track brightness profile -> uniformity
  Reused from scripts/lib (shared EXAMINE helpers, not new mechanism):
  read_fits (FITS I/O of Siril's product), branch_mask (per-set foreground
  exclusion).

  The in-house parts (streak DETECTION + GEOMETRY) are a SANCTIONED gap-filler:
  no compiled tool detects or measures anomalous-streak morphology. REMOVAL
  CONDITION: retire them the day a tool (a Siril-native streak/anomaly
  detector, or an adoptable streak library) provides the mechanism.

VALIDATION (real-data status — honest; lengths are extracted-green px):
  NULL confirmed on REAL data (clean-green domain): the BRIGHT satellite pass
  (july13 set-07 frames 6644-6646, ~360 px straight streaks, curv 0.006-0.015),
  the FAINT pass (6540-6545, now detected in EVERY frame on the green — it was
  mostly missed on the mosaic), and clean Milky-Way frames all -> 0 anomalies
  (neither the glow nor star trailing false-triggers).
  POSITIVE tested on SYNTHETIC only: a synthetic curved arc (curv 0.045) and a
  synthetic strobe (cv 0.81) are flagged; NO real curved/flaring transient has
  been tested. OPEN ITEM — the flag thresholds are PROVISIONAL and cannot be
  trusted as a detector until confirmed against a real anomalous transient.
  Until then this is a candidate-surfacer for human confirmation, not a
  verified detector.

KNOWN LIMITATIONS (open items, not defects hidden as features):
  - faint tracks that dip below 5-sigma along their path fragment into short
    segments — genuine faintness, NOT the Bayer/connectivity artifact the green
    extraction fixed. A short segment is below the curvature length floor, so a
    faint CURVED anomaly could be missed. Cross-frame + cross-segment track
    linking is the fix (not yet built).
  - per-frame only: no trajectory continuity across frames yet.

THRESHOLDS: every magic number is derived or PROVISIONAL — see the inline
comment at each site (min_len, elong, curvature, length floor, bright_cv, the
5-sigma detection cut). All lengths are extracted-green px.

COMPLIANCE self-audit (allowed iff ALL hold):
  (a) outside the final-product pipeline, never gates/processes the
      deliverable: YES — emits a report; no gate, no pixel output.
  (b) every pixel + standard measurement tool-sourced: YES — decode, green
      extraction, subsky, the star table, and the background level + noise
      (findstar's report) are all Siril; the kernel only reads those products.
  (c) computes only a derived result no tool provides: YES — streak detection
      (threshold + connected components) and streak geometry (curvature,
      brightness uniformity).
  (d) examine/report only, rewrites no deliverable, never modifies an input:
      YES — Siril reads the NEF and writes to a work dir; this tool writes only
      a report + transient residuals it deletes.
  (e) carries a removal condition: YES — see above.
"""
import glob
import json
import os
import re
import subprocess
import sys

import numpy as np
from scipy import ndimage

_lib = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                    "lib")
sys.path.insert(0, _lib)
import astrometrics as am  # noqa: E402

SIRIL = ["flatpak", "run", "--command=siril-cli", "org.siril.Siril"]


def run_siril(nef, work):
    """Drive Siril headless on ONE frame and return its products:
    (residual_fits, star_lst, bg, noise). Siril does every pixel operation and
    every standard measurement — decode, GREEN-CHANNEL extraction from the CFA
    (explicit, so the analysis domain is deterministic — never the ambient
    debayer setting), background extraction, the star table, and the background
    level + noise (findstar's report). Reads `nef`, writes only into `work`
    (the input is never modified). The .ssf lives under $HOME (the flatpak
    sandbox has a private /tmp). bg/noise are returned in [0,1] to match
    read_fits' normalization."""
    stem = os.path.splitext(os.path.basename(nef))[0]
    green = f"Green_{stem}"                   # extract_Green's output basename
    resid = os.path.join(work, "_resid")      # siril appends .fit
    stars = os.path.join(work, "_stars.lst")
    ssf = os.path.join(work, "_audit.ssf")
    # extract_Green SAVES the green plane to a file but leaves the mosaic in
    # memory, so it must be re-loaded before processing — otherwise subsky and
    # findstar run on the Bayer mosaic (verified: identical bgnoise/adjacent-
    # MAD to the raw CFA), and threshold + connected-components on a quincunx
    # green pattern fragments faint tracks. Working on the extracted green
    # makes every downstream measurement single-channel and mosaic-free.
    with open(ssf, "w") as f:
        f.write("requires 1.4.4\n"           # findstar stdout format tested here
                f"load {os.path.abspath(nef)}\n"
                "extract_Green\n"            # CFA -> clean single-channel green
                f"load {green}\n"            # process the GREEN, not the mosaic
                "subsky 4\n"                 # background extraction (a tool)
                f"save {resid}\n"
                f"findstar -out={stars}\n")  # stars + its bg level + noise
    r = subprocess.run(SIRIL + ["-d", work, "-s", ssf],
                       capture_output=True, text=True)
    for gf in glob.glob(os.path.join(work, f"{green}.fit*")):
        os.remove(gf)                        # drop the intermediate green file
    fit = resid + ".fit"
    if not os.path.exists(fit):
        raise RuntimeError(f"siril produced no residual for {nef}:\n"
                           + r.stdout[-600:] + r.stderr[-600:])
    # Background level + noise from findstar's report ("Threshold: T
    # (background level: B, noise: N, norm: M)"). On the extracted green these
    # equal Siril `stat`'s Median/bgnoise exactly (verified 1117 / 14.50 both),
    # so either tool is correct here; findstar's is used because findstar is
    # already invoked for the star table (no redundant command). norm rescales
    # to read_fits' [0,1]. Loud-fail if the format ever drifts.
    m = re.search(r"background level:\s*([0-9.eE+-]+),\s*noise:\s*"
                  r"([0-9.eE+-]+),\s*norm:\s*([0-9.eE+-]+)", r.stdout)
    if not m:
        raise RuntimeError(f"could not parse findstar bg/noise for {nef} "
                           f"(Siril output format drift?):\n{r.stdout[-600:]}")
    bg, noise, norm = float(m.group(1)), float(m.group(2)), float(m.group(3))
    return fit, stars, bg / norm, noise / norm


def stellar_trail_px(star_lst):
    """Median stellar trail length (px) from Siril's PSF table = the length
    of an ORDINARY point source in this frame (short if tracked, ~the drift
    if not). The streak threshold is a multiple of it, so the audit adapts to
    tracked and untracked data alike instead of a hard-coded length."""
    fx = []
    if os.path.exists(star_lst):
        for l in open(star_lst):
            if l[:1] in "#s":
                continue
            p = l.split()
            if len(p) >= 9:
                try:
                    fx.append(max(float(p[7]), float(p[8])))
                except ValueError:
                    pass
    return float(np.median(fx)) if fx else 6.0


def measure_streak(ys, xs, w):
    """Geometry of one candidate component. Principal-axis fit, then the
    deviation of the pixels from that straight line:
      length    extent along the major axis (px)
      sagitta   max |deviation| of the pixels from the straight-line fit (px)
      curvature sagitta / length — ~0 for a straight satellite/plane, grows
                with any real bend (the flag discriminant)
      width     intrinsic thickness: perpendicular RMS AFTER removing the curve
                (parabola) so a real bend can't hide in the spread. Reported
                only (diagnostic), not a flag input.
      bright_cv along-track brightness coefficient of variation (uniform
                satellite ~ low; flaring/strobing ~ high)
    """
    x = xs.astype(float); y = ys.astype(float)
    wsum = w.sum()
    cx = (w * x).sum() / wsum; cy = (w * y).sum() / wsum
    xx = ((w * (x - cx) ** 2).sum()) / wsum
    yy = ((w * (y - cy) ** 2).sum()) / wsum
    xy = ((w * (x - cx) * (y - cy)).sum()) / wsum
    tr = xx + yy; disc = max((xx - yy) ** 2 + 4 * xy * xy, 0.0)
    l1 = (tr + disc ** .5) / 2; l2 = (tr - disc ** .5) / 2
    ang = 0.5 * np.arctan2(2 * xy, xx - yy)
    ux, uy = np.cos(ang), np.sin(ang)          # along-track unit vector
    t = (x - cx) * ux + (y - cy) * uy          # position along the axis
    n = -(x - cx) * uy + (y - cy) * ux         # perpendicular offset
    length = float(t.max() - t.min())
    # sagitta = max deviation of the pixels from the straight (line) fit; the
    # curve signal. WIDTH must be the intrinsic thickness, so measure it as the
    # residual AFTER fitting the curve (parabola) — otherwise a real bend
    # inflates the perpendicular spread and hides itself. A straight track has
    # sagitta ~ width; a curved one has sagitta >> width.
    if length > 4 and np.ptp(t) > 0:
        line = np.polyval(np.polyfit(t, n, 1, w=w), t)
        sagitta = float(np.max(np.abs(n - line)))
        curvature = sagitta / length
        resid = n - np.polyval(np.polyfit(t, n, 2, w=w), t)
        width = float(2.0 * np.sqrt(np.average(resid ** 2, weights=w)))
    else:
        sagitta, curvature = 0.0, 0.0
        width = float(np.sqrt(max(l2, 0.0)) * 2.354)
    # along-track brightness uniformity
    nb = max(8, int(length // 6))
    edges = np.linspace(t.min(), t.max(), nb + 1)
    prof = np.array([w[(t >= edges[i]) & (t < edges[i + 1])].sum()
                     for i in range(nb)])
    prof = prof[prof > 0]
    bright_cv = float(prof.std() / prof.mean()) if prof.size and prof.mean() > 0 else 0.0
    return dict(length=length, width=width, sagitta=sagitta,
                elong=float((l1 / max(l2, 1e-6)) ** .5),
                curvature=curvature, bright_cv=bright_cv,
                pa_deg=float(np.degrees(ang)),
                cx=float(cx), cy=float(cy), npix=int(len(ys)))


def audit_frame(nef, work, curv_thr):
    # Siril: decode + green extraction + background extraction + star table +
    # bg/noise (findstar). The residual is the CLEAN extracted green (mono).
    fit, star_lst, bg, sig = run_siril(nef, work)
    data, _ = am.read_fits(fit)               # read Siril's residual (I/O)
    g = data[0]                               # single-channel extracted green
    h, wid = g.shape
    trail = stellar_trail_px(star_lst)
    # a streak is far longer than a point source; 5x the Siril-measured median
    # stellar trail (green px) adapts to tracked (round stars) vs untracked
    # (trailed). PROVISIONAL: the 5x multiplier is a heuristic — a with/without
    # sweep on a labelled streak/star set would settle it.
    min_len = max(5 * trail, 40)
    # streak DETECTION (in-house — no tool emits streaks): threshold the clean
    # green residual at 5x findstar's reported noise — the standard astronomical
    # source-detection significance (~1-2 false clusters/frame on Gaussian
    # noise, which the streak-shape filter below removes). Foreground excluded,
    # then connected-component label; findstar catalogs STARS, streaks are the
    # elongated components left over. Detecting on the extracted green (NOT the
    # Bayer mosaic) is what lets a faint track survive as one component: on the
    # mosaic the quincunx green pattern + a single green threshold across all
    # channels dropped it (verified — the faint 6540-6545 pass detects on green,
    # not on the mosaic). Faint tracks that still dip below 5-sigma along their
    # path fragment into short segments (genuine faintness, not a Bayer
    # artifact); those skip the curvature test (length floor below).
    det = (g > bg + 5 * sig) & am.branch_mask(h, wid)
    lbl, n = ndimage.label(det)
    streaks = []
    for k, sl in enumerate(ndimage.find_objects(lbl), start=1):
        ys, xs = np.where(lbl[sl] == k)
        if ys.size < 12:                      # ignore hot-pixel/noise specks
            continue
        yy = ys + sl[0].start; xx = xs + sl[1].start
        wv = np.clip(g[yy, xx] - bg, 0, None)
        if wv.sum() <= 0:
            continue
        m = measure_streak(yy, xx, wv)
        # a streak candidate must be long (>= min_len) and thin: elong >= 6 is
        # well above the stellar population (trailed stars here reach ~2-3), so
        # no star cluster qualifies. PROVISIONAL: derived from this data's
        # stellar elongation ceiling.
        if m["length"] >= min_len and m["elong"] >= 6:
            # curved = bend fraction (sagitta/length) >= curv_thr over a track
            # long enough to trust. All lengths are EXTRACTED-GREEN px (half the
            # full-frame linear resolution — see run_siril).
            #  curv_thr default 0.03 sits above the 0.006-0.015 that real
            #    straight satellites reach on the clean green here; PROVISIONAL
            #    until a real curved transient is measured.
            #  length>=200 — sagitta/length is unstable for short segments
            #    (small denominator; a neighbour star bends the axis): entry/
            #    exit + faint fragments (<=152 px) read spurious curv up to 0.05
            #    while the >=360 px bright track sat at ~0.01. PROVISIONAL floor
            #    from this dataset. It also implies sagitta = curv*length >= 6
            #    px, so a tiny wiggle cannot flag (no separate sagitta cut).
            curved = m["length"] >= 200 and m["curvature"] >= curv_thr
            # non-uniform: along-track brightness CV. Uniform satellites read
            # ~0.06; a synthetic strobe read 0.81. PROVISIONAL 0.6 — only
            # synthetic tested; needs a real strobing/tumbling example.
            nonunif = m["bright_cv"] >= 0.6
            m["anomaly"] = curved or nonunif
            m["why"] = (("curved " if curved else "")
                        + ("non-uniform" if nonunif else "")).strip() \
                or "straight+uniform (ordinary sat/plane)"
            streaks.append(m)
    return dict(file=os.path.basename(nef), n_streaks=len(streaks),
                stellar_trail_px=round(trail, 1),
                anomalies=[s for s in streaks if s["anomaly"]],
                streaks=streaks)


def main():
    argv = [a for a in sys.argv[1:] if not a.startswith("--")]
    opts = dict(a[2:].split("=", 1) if "=" in a else (a[2:], True)
                for a in sys.argv[1:] if a.startswith("--"))
    if not argv:
        sys.exit(__doc__)
    target = argv[0]
    if os.path.isdir(target):
        frames = sorted(glob.glob(os.path.join(target, "*.NEF"))
                        + glob.glob(os.path.join(target, "*.nef")))
    else:
        frames = sorted(glob.glob(target))
    if not frames:
        sys.exit(f"anomaly_audit: no frames match {target}")
    work = os.path.abspath(opts.get("work")
                           or os.path.join(os.path.dirname(frames[0]) or ".",
                                           "audit_work"))
    os.makedirs(work, exist_ok=True)
    if "session" in opts and "set" in opts:
        am.configure(opts["session"], opts["set"])
    curv_thr = float(opts.get("curv", 0.03))

    print(f"anomaly audit: {len(frames)} frames | curve flag: curvature "
          f"(sagitta/length) >= {curv_thr} | work={work}\n(Siril: decode / "
          f"extract_Green / subsky / findstar + bg/noise; in-house kernel reads "
          f"the green residual and does streak detection + geometry on it; "
          f"inputs never modified)")
    results, flagged = [], []
    for i, nef in enumerate(frames, 1):
        try:
            res = audit_frame(nef, work, curv_thr)
        except Exception as e:
            res = {"file": os.path.basename(nef), "error": str(e)[:200]}
            print(f"  [{i}/{len(frames)}] {res['file']}: ERROR {res['error']}")
            results.append(res)
            continue
        results.append(res)
        tag = ""
        if res["anomalies"]:
            flagged.append(res)
            tag = "  <== ANOMALY: " + "; ".join(
                f"{a['why']} (curv {a['curvature']:.3f}, cv {a['bright_cv']:.2f}, "
                f"len {a['length']:.0f}px)" for a in res["anomalies"])
        elif res["n_streaks"]:
            tag = "  " + "; ".join(
                f"ordinary streak len {s['length']:.0f}px curv {s['curvature']:.3f}"
                for s in res["streaks"])
        print(f"  [{i}/{len(frames)}] {res['file']}: {res['n_streaks']} streak(s)"
              f"{tag}")
        if not opts.get("keep-resid"):
            for f in glob.glob(os.path.join(work, "_resid.fit*")):
                os.remove(f)

    print(f"\n{len(flagged)} of {len(frames)} frames flagged as ANOMALOUS "
          f"(curved or non-uniform streak).")
    for r in flagged:
        print(f"  {r['file']}: "
              + "; ".join(f"{a['why']} curv={a['curvature']:.3f} "
                          f"cv={a['bright_cv']:.2f} len={a['length']:.0f}px "
                          f"PA={a['pa_deg']:.0f}" for a in r["anomalies"]))
    if "json" in opts:
        json.dump(results, open(opts["json"], "w"), indent=1)
        print(f"\nrecord -> {opts['json']}")


if __name__ == "__main__":
    main()
