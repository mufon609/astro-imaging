#!/usr/bin/env python3
"""Transient-obstruction classifier + anomaly surface: for each frame, decide
what each in-frame obstruction is — AIRCRAFT, SATELLITE, or UNKNOWN. REPORT-ONLY
— it never moves, deletes, or rewrites any input frame, and it does not gate or
feed the final-product pipeline; it emits a per-frame classification with the
measured evidence. UNKNOWN is the honest anomaly surface: an obstruction that
matches no known signature and deserves human eyes.

  Usage: anomaly_audit.py <frame.NEF | dir | glob> [--work=<dir>]
                          [--session=<dir> --set=<name>] [--curv=<f>]
                          [--json=<out>] [--keep-resid]

CLASSIFICATION MODEL — a registry of "callouts". Detected light-trails are
grouped into candidate OBJECTS (an aircraft leaves several trails; a satellite
one), then each object is run past CALLOUTS in order; the first signature that
matches wins, and an object matching none is UNKNOWN. To teach the tool a
newly-identified object, ADD a callout with its MEASURED signature — nothing
else changes. Current callouts (most specific first):
  aircraft   two or more PARALLEL twin trails (separate lights on one airframe)
             — a signature a single-point satellite cannot make.
  satellite  a single STRAIGHT continuous trail (one light on an orbital path).
  <else>     UNKNOWN (curved track, unmatched multi-trail, anything odd).
Across frames, per-frame objects are LINKED into UNIQUE physical objects: on a
fixed (untracked) camera each crossing traces a straight sensor-plane line, so
same-class + colinear + consecutive detections are ONE object (a satellite over
4 frames = 1 object, 4 detections). The final report gives per-frame contents,
the unique-object list with frame spans, and BOTH totals (unique vs per-frame).
Grading the subs themselves (FWHM / roundness / background / star count) is a
SEPARATE, already-solved job (Siril `register` -> `cull_report.py`); not here.

WHAT SIRIL DOES vs WHAT IS IN-HOUSE  (mechanism honesty — the repo sources
every pixel operation and every STANDARD measurement from a tool, and writes
in-house code only for a derived result no tool provides):

  Siril (subprocess per frame, like solve_field.py drives astrometry.net):
    load          decode the native NEF (a Bayer CFA mosaic)
    extract_Green CFA -> a CLEAN single-channel GREEN image (half the full-
                  frame linear resolution). Explicit, so the analysis DOMAIN is
                  deterministic — never the ambient debayer setting. Everything
                  below runs on this green, never the mosaic. (extract_Green
                  saves the green to a file that MUST be re-loaded before
                  processing, or subsky/findstar run on the mosaic instead.)
    subsky        background extraction (flatten vignette + Milky-Way glow so a
                  faint track clears threshold) -> the residual image
    save          write the residual FITS the kernel reads
    findstar      the stellar PSF table (median trail length -> the adaptive
                  streak-length floor), the star catalog, AND the background
                  level + noise it reports -> the detection threshold, parsed
                  from Siril, NOT recomputed in-house. On the extracted green
                  these equal Siril `stat`'s background/noise (both measure the
                  same background), so either is correct; findstar's is used
                  because findstar is already invoked for the star table. (On
                  the raw CFA mosaic `stat`'s noise is inflated by the Bayer
                  R/G/B channel-level checkerboard; extracting green removes it.)

  In-house kernel (numpy/scipy, EXAMINE only — reads Siril's products, writes
  no deliverable). These ARE pixel operations; they are not Siril:
    - reads Siril's green residual FITS (shared read_fits) + findstar's star list
    - STREAK DETECTION: threshold the green residual at bg + k*noise (both from
      findstar's report) and connected-component label it (ndimage.label).
    - reads residual pixel brightness inside each component (for the weights)
    - STREAK GEOMETRY: principal-axis fit -> curvature; along-track brightness
    - OBJECT GROUPING + CLASSIFICATION: group trails into objects, then match
      each against the callout signatures.
    - CROSS-FRAME LINKING: chain per-frame objects into unique physical objects
      by class + colinearity + frame adjacency (fixed-camera line assumption).
  No tool detects/measures/classifies transient obstructions; that whole
  in-house layer is a SANCTIONED gap-filler. REMOVAL CONDITION: retire it the
  day a tool provides the streak detection/geometry/classification mechanism.
  Reused from scripts/lib (shared EXAMINE helpers, not new mechanism):
  read_fits (FITS I/O of Siril's product), branch_mask (per-set foreground).

VALIDATION (maturity per class — honest; lengths are extracted-green px):
  satellite — well exercised: real straight-trail passes and clean frames
    classify correctly with no false object.
  aircraft  — the twin-trail signature is confirmed on a single real example,
    so its thresholds are PROVISIONAL; a strobe-periodicity callout (for a
    single-light aircraft, which the twin rule cannot catch) is NOT yet built.
  unknown   — the residual bucket by construction; a candidate surface for
    human confirmation, never a verified "anomaly" claim on its own.
  linking   — collapses a night's per-frame detections into its distinct
    passes; PROVISIONAL colinearity/gap/PA tolerances, and it assumes a fixed/
    untracked camera.

PLANNED CALLOUTS (each an "unknown" until measured on a real example):
  strobe-periodicity aircraft (single light, regular beading along the trail);
  colinear regular-dash vs irregular-fragment (strobe aircraft vs faint broken
  satellite); meteor (brightens-then-fades profile); Starlink train (many
  colinear equal trails). Add each as a callout with its measured signature.

THRESHOLDS: every magic number is derived or PROVISIONAL — see the inline
comment at each site. All lengths are extracted-green px.

COMPLIANCE self-audit (allowed iff ALL hold):
  (a) outside the final-product pipeline, never gates/processes the
      deliverable: YES — emits a report; no gate, no pixel output.
  (b) every pixel + standard measurement tool-sourced: YES — decode, green
      extraction, subsky, the star table, and the background level + noise
      (findstar's report) are all Siril; the kernel only reads those products.
  (c) computes only a derived result no tool provides: YES — streak detection,
      geometry, object grouping, and classification.
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
    # findstar run on the Bayer mosaic, whose channel-level checkerboard inflates
    # the noise estimate and whose quincunx green pattern breaks threshold +
    # connected-components apart, fragmenting faint tracks. Working on the
    # extracted green makes every downstream measurement single-channel and
    # mosaic-free.
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
    # equal Siril `stat`'s background/noise (both measure the same background),
    # so either tool is correct; findstar's is used because findstar is already
    # invoked for the star table (no redundant command). norm rescales to
    # read_fits' [0,1]. Loud-fail if the format ever drifts.
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


# --- object grouping + classification ("callouts") ---------------------------
# A detected trail is one light-track. A real object can leave MORE than one
# trail in a frame (an aircraft's separate lights) or a broken one (a strobe).
# group_objects() assembles related trails into candidate OBJECTS; each object
# is then classified by the CALLOUTS registry — first signature that matches
# wins; an object matching none is UNKNOWN. To teach the tool a newly-identified
# object, add a callout below with its MEASURED signature; nothing else changes.

def _twin(a, b):
    """True if two trails are parallel twin lights of ONE airframe: shared
    heading (PA within 5 deg — a rigid airframe), matched length (both lights
    trace the same path), a small RESOLVED perpendicular offset (the light
    separation, << the trail length), and co-located along-track (side by side,
    not lead/trail). PROVISIONAL — the tolerances are calibrated on a single
    real aircraft."""
    dpa = abs(((a["pa_deg"] - b["pa_deg"] + 90) % 180) - 90)
    if dpa > 5.0:
        return False
    if not 0.75 <= a["length"] / max(b["length"], 1e-6) <= 1.33:
        return False
    pa = np.radians((a["pa_deg"] + b["pa_deg"]) / 2)
    ux, uy = np.cos(pa), np.sin(pa)
    dcx, dcy = b["cx"] - a["cx"], b["cy"] - a["cy"]
    offset = abs(-dcx * uy + dcy * ux)         # perpendicular separation
    along = abs(dcx * ux + dcy * uy)           # along-track separation
    minlen = min(a["length"], b["length"])
    return 3.0 <= offset <= 0.2 * minlen and along <= 0.5 * minlen


def _related(a, b):
    """True if two trails belong to ONE physical object in a frame: shared
    heading and lying on ~one line (small perpendicular offset). Covers BOTH a
    faint trail broken into colinear fragments (offset ~0, separated along the
    line) AND an aircraft's side-by-side twin lights (a small resolved offset).
    Length is NOT required to match — the fragments of one broken trail vary
    widely. PROVISIONAL near-line tolerance: it must exceed the twin-light
    offset and the fragment scatter while staying well below the perpendicular
    separation of distinct parallel passes."""
    if abs(((a["pa_deg"] - b["pa_deg"] + 90) % 180) - 90) > 5.0:
        return False
    pa = np.radians((a["pa_deg"] + b["pa_deg"]) / 2)
    dcx, dcy = b["cx"] - a["cx"], b["cy"] - a["cy"]
    return abs(-dcx * np.sin(pa) + dcy * np.cos(pa)) <= 30.0


def _track_span(obj):
    """Along-track extent (px) across all of an object's fragments — the whole
    trail's length even when broken into pieces."""
    pa = np.radians(float(np.median([s["pa_deg"] for s in obj])))
    ux, uy = np.cos(pa), np.sin(pa)
    ts = []
    for s in obj:
        c = s["cx"] * ux + s["cy"] * uy
        ts += [c - s["length"] / 2, c + s["length"] / 2]
    return float(max(ts) - min(ts))


def _perp_span(obj):
    """Perpendicular spread of an object's trail centroids (px) about their
    shared heading — the light-separation reported as aircraft evidence."""
    pa = np.radians(float(np.median([s["pa_deg"] for s in obj])))
    ux, uy = np.cos(pa), np.sin(pa)
    perp = [(-s["cx"] * uy + s["cy"] * ux) for s in obj]
    return float(max(perp) - min(perp))


def group_objects(streaks):
    """Assemble detected trails into candidate objects: parallel-twin trails
    merge (union-find over _twin); every other trail is its own object."""
    n = len(streaks)
    parent = list(range(n))

    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]; i = parent[i]
        return i
    for i in range(n):
        for j in range(i + 1, n):
            if _related(streaks[i], streaks[j]):
                parent[find(i)] = find(j)
    groups = {}
    for i in range(n):
        groups.setdefault(find(i), []).append(streaks[i])
    return list(groups.values())


def _reliably_curved(s, curv_thr):
    """A trail counts as CURVED only when the bend is trustworthy: curvature
    (sagitta/length) is unstable on short segments — the denominator is small and
    a neighbouring star can bias the axis fit — so require a minimum length,
    where a straight track's residual curvature settles low. curv_thr must sit
    above that residual (the small bend a straight track shows from wide-field
    projection + subsky residual). Both PROVISIONAL; the length floor means a
    faint SHORT curved fragment is not assessed (needs cross-segment linking)."""
    return s["length"] >= 200 and s["curvature"] >= curv_thr


def classify_aircraft(obj, curv_thr):
    """AIRCRAFT: the object contains a PARALLEL TWIN pair — two lights side by
    side on one airframe (resolved perpendicular offset, co-located along-track,
    matched length), which a single-point satellite cannot make. (A strobe-
    periodicity callout for single-light aircraft is planned, not yet built.)"""
    if not any(_twin(a, b) for i, a in enumerate(obj) for b in obj[i + 1:]):
        return None
    off = _perp_span(obj)
    return dict(cls="aircraft", confidence=0.9,
                reason=f"parallel twin pair among {len(obj)} trail(s), offset {off:.0f}px",
                evidence=dict(n_trails=len(obj), offset_px=round(off, 1),
                              pa_deg=round(float(np.median([s["pa_deg"] for s in obj])), 1),
                              length_px=round(float(np.median([s["length"] for s in obj])))))


def classify_satellite(obj, curv_thr):
    """SATELLITE: one light on an orbital path — a single STRAIGHT trail, OR
    several COLINEAR fragments of one faint broken trail (grouped onto one line,
    so straight by construction). A single long trail that is RELIABLY curved is
    NOT a satellite (it falls to UNKNOWN); a short fragment with unstable
    curvature stays a satellite. bright_cv is reported (a distorted sub can read
    high) but does not change the class."""
    if len(obj) == 1:
        s = obj[0]
        if _reliably_curved(s, curv_thr):
            return None
        return dict(cls="satellite", confidence=0.8,
                    reason=f"single straight trail (curv {s['curvature']:.3f})",
                    evidence=dict(span_px=round(s["length"]), n_fragments=1,
                                  pa_deg=round(s["pa_deg"], 1),
                                  curvature=round(s["curvature"], 3),
                                  bright_cv=round(s["bright_cv"], 2)))
    span = _track_span(obj)
    return dict(cls="satellite", confidence=0.7,
                reason=f"{len(obj)} colinear fragments of one trail, span {span:.0f}px",
                evidence=dict(span_px=round(span), n_fragments=len(obj),
                              pa_deg=round(float(np.median([s["pa_deg"] for s in obj])), 1)))


CALLOUTS = [classify_aircraft, classify_satellite]   # most specific first


def classify_object(obj, curv_thr):
    """Run the callout registry; first match wins. No match -> UNKNOWN (a curved
    track, an unmatched multi-trail, anything out of the ordinary): the surface
    that deserves human eyes."""
    for callout in CALLOUTS:
        v = callout(obj, curv_thr)
        if v:
            v["streaks"] = obj
            return v
    s0 = obj[0]
    return dict(cls="unknown", confidence=1.0, streaks=obj,
                reason=(f"curved track (curv {s0['curvature']:.3f} over "
                        f"{s0['length']:.0f}px)" if _reliably_curved(s0, curv_thr)
                        else f"{len(obj)} trail(s) matching no known signature"),
                evidence=dict(n_trails=len(obj), length_px=round(s0["length"]),
                              curvature=round(s0["curvature"], 3),
                              bright_cv=round(s0["bright_cv"], 2),
                              pa_deg=round(s0["pa_deg"], 1)))


# --- cross-frame linking (per-frame objects -> unique physical objects) ------
# A per-frame object is one crossing captured in one 8s exposure. The SAME
# physical object reappears in consecutive frames as it crosses. On a fixed
# (untracked) camera its path is a straight LINE across the sensor, so a track =
# same class + colinear + consecutive-ish frames. (A satellite spanning 4 frames
# is ONE object, four detections.) EXAMINE-only: this groups detections, it
# reads no pixels.

def _obj_geom(o):
    """Object's representative centroid (cx, cy) and heading (pa_deg) from its
    member trails."""
    ss = o["streaks"]
    return (float(np.mean([s["cx"] for s in ss])),
            float(np.mean([s["cy"] for s in ss])),
            float(np.median([s["pa_deg"] for s in ss])))


def _colinear(a, b, pa_tol, colin_tol):
    """True if two per-frame objects lie on ~one line: headings agree, and each
    centroid sits within colin_tol of the other's line (the object advances
    ALONG its track between frames, so centroids are far apart but co-linear)."""
    ax, ay, apa = a; bx, by, bpa = b
    if abs(((apa - bpa + 90) % 180) - 90) > pa_tol:
        return False
    for (px, py), (ox, oy, opa) in (((bx, by), a), ((ax, ay), b)):
        u = np.radians(opa)
        if abs((px - ox) * -np.sin(u) + (py - oy) * np.cos(u)) > colin_tol:
            return False
    return True


def link_objects(results, max_gap=2, pa_tol=12.0, colin_tol=60.0):
    """Greedy cross-frame chaining of per-frame objects into UNIQUE physical
    objects (tracks). Returns [{cls, files:[...], first, last, n, pa}]. Assumes
    a fixed/untracked camera (each object's ground track is a sensor-plane
    line). PROVISIONAL params (max_gap 2 frames to bridge a missed detection,
    pa_tol 12 deg for slow apparent rotation, colin_tol 60 green px): a
    with/without check on hand-labelled tracks would settle them."""
    tracks = []
    for fi, r in enumerate(results):
        for o in r.get("objects", []):
            g = _obj_geom(o)
            cand = [t for t in tracks if t["cls"] == o["cls"]
                    and 0 < fi - t["_fi"] <= max_gap
                    and _colinear(g, t["_geom"], pa_tol, colin_tol)]
            if cand:
                t = min(cand, key=lambda t: fi - t["_fi"])   # freshest track
                t["files"].append(r["file"]); t["n"] += 1
                t["last"] = r["file"]; t["_fi"] = fi; t["_geom"] = g
            else:
                tracks.append(dict(cls=o["cls"], files=[r["file"]],
                                   first=r["file"], last=r["file"], n=1,
                                   pa=round(g[2], 1), _fi=fi, _geom=g))
    for t in tracks:
        t.pop("_fi"); t.pop("_geom")
    return tracks


def audit_frame(nef, work, curv_thr):
    # Siril: decode + green extraction + background extraction + star table +
    # bg/noise (findstar). The residual is the CLEAN extracted green (mono).
    fit, star_lst, bg, sig = run_siril(nef, work)
    data, _ = am.read_fits(fit)               # read Siril's residual (I/O)
    g = data[0]                               # single-channel extracted green
    h, wid = g.shape
    trail = stellar_trail_px(star_lst)
    # a trail is far longer than a point source; 5x the Siril-measured median
    # stellar trail (green px) adapts to tracked (round stars) vs untracked
    # (trailed). PROVISIONAL: the 5x multiplier is a heuristic — a with/without
    # sweep on a labelled streak/star set would settle it.
    min_len = max(5 * trail, 40)
    # trail DETECTION (in-house — no tool emits trails): threshold the clean
    # green residual at 5x findstar's reported noise — the standard astronomical
    # source-detection significance (~1-2 false clusters/frame on Gaussian
    # noise, which the shape filter below removes). Foreground excluded, then
    # connected-component label; findstar catalogs STARS, trails are the
    # elongated components left over. Detecting on the extracted green (NOT the
    # Bayer mosaic) is what lets a faint track survive as one component.
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
        # a trail candidate must be long (>= min_len) and thin: elong >= 6 is
        # well above any point source — even a trailed star stays far rounder —
        # so no star or star cluster qualifies. PROVISIONAL threshold.
        if m["length"] >= min_len and m["elong"] >= 6:
            streaks.append(m)
    objects = [classify_object(o, curv_thr) for o in group_objects(streaks)]
    counts = {}
    for o in objects:
        counts[o["cls"]] = counts.get(o["cls"], 0) + 1
    return dict(file=os.path.basename(nef), n_trails=len(streaks),
                stellar_trail_px=round(trail, 1), counts=counts, objects=objects)


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

    print(f"obstruction classifier: {len(frames)} frames | callouts: "
          + ", ".join(c.__name__.replace("classify_", "") for c in CALLOUTS)
          + f", else unknown | work={work}\n(Siril: decode / extract_Green / "
          f"subsky / findstar + bg/noise; in-house kernel groups + classifies "
          f"the green residual's trails; inputs never modified)")
    results, totals = [], {}
    for i, nef in enumerate(frames, 1):
        try:
            res = audit_frame(nef, work, curv_thr)
        except Exception as e:
            print(f"  [{i}/{len(frames)}] {os.path.basename(nef)}: ERROR {str(e)[:160]}")
            results.append({"file": os.path.basename(nef), "error": str(e)[:200]})
            continue
        results.append(res)
        for o in res["objects"]:
            totals[o["cls"]] = totals.get(o["cls"], 0) + 1
        summary = "; ".join(f"{o['cls'].upper()} — {o['reason']}"
                            for o in res["objects"]) or "clear"
        print(f"  [{i}/{len(frames)}] {res['file']}: {summary}")
        if not opts.get("keep-resid"):
            for f in glob.glob(os.path.join(work, "_resid.fit*")):
                os.remove(f)

    tracks = link_objects(results)

    print("\n" + "=" * 64 + "\nOVERALL REPORT\n" + "=" * 64)
    graded = [r for r in results if "objects" in r]
    withobj = [r for r in graded if r["objects"]]
    print(f"frames: {len(frames)} | with an object: {len(withobj)} | clear: "
          f"{len(graded) - len(withobj)}"
          + (f" | errors: {len(results) - len(graded)}"
             if len(results) > len(graded) else ""))

    print("\nper-frame (objects only):")
    for r in withobj:
        by = {}
        for o in r["objects"]:
            by[o["cls"]] = by.get(o["cls"], 0) + 1
        print(f"  {r['file']}: "
              + ", ".join(f"{k} x{v}" for k, v in sorted(by.items())))

    print(f"\nunique physical objects — linked across frames: {len(tracks)}")
    for i, t in enumerate(sorted(tracks, key=lambda t: t["first"]), 1):
        span = t["first"] if t["n"] == 1 else f"{t['first']}..{t['last']}"
        print(f"  #{i:<2} {t['cls']:9} {span:30} "
              f"({t['n']} frame{'s' if t['n'] > 1 else ''})  PA {t['pa']:+.0f}")

    uniq = {}
    for t in tracks:
        uniq[t["cls"]] = uniq.get(t["cls"], 0) + 1
    print("\ntotals:")
    print(f"  unique objects:       {sum(uniq.values())}  ("
          + (", ".join(f"{k}={v}" for k, v in sorted(uniq.items())) or "none") + ")")
    print(f"  per-frame detections: {sum(totals.values())}  ("
          + (", ".join(f"{k}={v}" for k, v in sorted(totals.items())) or "none")
          + ")   [same object across N frames counts N times here, once above]")

    unk = [t for t in tracks if t["cls"] == "unknown"]
    if unk:
        print(f"\nUNKNOWN — {len(unk)} object(s) matching no known signature "
              f"(human review; the anomaly surface):")
        for t in unk:
            span = t["first"] if t["n"] == 1 else f"{t['first']}..{t['last']}"
            print(f"  {span} ({t['n']} frame(s))  PA {t['pa']:+.0f}")
    else:
        print("\nUNKNOWN: none (every object matched a known signature).")

    if "json" in opts:
        json.dump({"frames": results, "unique_objects": tracks},
                  open(opts["json"], "w"), indent=1)
        print(f"\nrecord -> {opts['json']}")


if __name__ == "__main__":
    main()
