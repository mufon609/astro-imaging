#!/usr/bin/env python3
"""Per-stage pipeline inspection: consistent-stretch JPEG + metrics +
PASS/WARN against the expectations table (NOTES.md "Per-stage expectations").

Usage:
  inspect_stage.py stage <stage-name> --dir <inspect-dir> --in F [F ...]
                   [--label L]
  inspect_stage.py reg   --dir <inspect-dir> --registered N --total M
                   --ref R [--sweep "11:19,12:21"] [--seq seqfile] [--label L]
  inspect_stage.py report --dir <inspect-dir> [--title T] [--qa qa.txt]

The reg call is the pipeline's per-frame quality assessment stage (the
SubframeSelector step of the standard workflow, measurement half only):
it parses the registration .seq regdata siril already computed — FWHM /
wFWHM / roundness / background / star count / homography per frame — and
persists the full per-frame records (including the shift list, the
dither-phase input the drizzle path needs) into metrics.jsonl plus a .seq
copy, BEFORE per-stage cleanup prunes the sequence. Distribution checks
are WARN-only like every inspection; weighting/culling POLICY lives
elsewhere (the optional per-dataset "stack" recipe block, applied by
run_pipeline at stack time) — this stage only measures, and its per-frame
"n" numbers are the frame identity that block's exclude list names.

Stage names: calibrated, selfflat_median, subsky_frame, gain, divided, stack.

Every 'stage' call appends one JSON line to <dir>/metrics.jsonl and writes
<NN>_<stage>.jpg (one CONSISTENT autostretch: linked MTF, shadow clip
median-2.8*bgnoise, bg target 0.25 — every stage, every run) plus
<NN>_<stage>_radial.png. 'report' assembles index.html + index.md.
Inspection WARNs, it never fails a run — the hard gate stays bg_qa.py.
"""
import argparse
import json
import os
import re
import sys
import numpy as np

# scripts/lib holds the shared libs (astrometrics, bg_qa); locate it by
# walking up from this file so one bootstrap works at any nesting depth.
_libdir = os.path.dirname(os.path.abspath(__file__))
while _libdir != os.path.dirname(_libdir):
    if os.path.isdir(os.path.join(_libdir, "lib")):
        sys.path.insert(0, os.path.join(_libdir, "lib"))
        break
    _libdir = os.path.dirname(_libdir)
import astrometrics as am  # noqa: E402

D16 = 65535.0

# stage -> metric -> (lo, hi, note); units: 16-bit display counts for linear
# stages, 8-bit counts for stretched. THIS table is authoritative (NOTES.md
# carries a summary). Bounds are WARN bounds (inspection), not the bg_qa
# gate. They are sanity ENVELOPES (some self-flat-specific: corner_gain,
# stack noise%) — a new data class may
# WARN legitimately; revisit bounds there instead of ignoring the WARNs.
EXPECTATIONS = {
    "master_dark": {
        "bg_median16": (None, None, "INFO: master level — an offset/sensor fact (measured: bias 155, matched darks 168-501 counts16; a prebuilt ADU-scale master is normalized /65535 first)"),
        "clip_frac": (None, None, "INFO: pixels at ceiling — saturated hot pixels, a sensor/gain fact (the hot-pixel map is the -cc=dark win, not a defect)"),
        "hot_frac": (None, None, "INFO: fraction > median+10*noise — the hot-pixel population (measured: 0.02-0.35% cooled low gain, 1.5% at gain 150)"),
    },
    "master_flat": {
        "flat_level_pct": (None, None, "INFO: median % of full scale — the exposure-checklist fact (goal ~50%; measured corpora 28-37%)"),
        "corner_over_center": (0.35, 1.02, "field illumination falloff to the corner (a clean flat sits ~0.85-1.0; below 0.35 exceeds every honest falloff class, above 1.02 is not a flat)"),
        "dust_min_rel": (None, 0.05, "deepest coherent small-scale dip vs the smooth field (measured clean flats 0.3-0.9%); a >5% shadow is a real mote — verify it matches the lights' dust or it prints a ring downstream"),
        "clip_frac": (None, 0.005, "a clipped flat is broken by construction"),
    },
    "calibrated": {
        "bg_median16": (None, None, "INFO: sky level, offset subtracted — a SITE/SENSOR fact, not a defect signal (dark-site cooled mono reads ~35 counts, light-polluted DSLR ~370-600; same pedestal-ratio class as the demoted stack metrics)"),
        "clip_frac": (None, 0.005, "saturated fraction"),
        "n_stars": (150, None, "detected stars (numpy detector)"),
    },
    "selfflat_median": {
        "star_ratio_vs_calibrated": (None, 0.05, "star residue after median"),
        "corner_over_center": (0.35, 0.75, "V x S falloff"),
    },
    "subsky_frame": {
        "plane_tilt_pct": (None, None, "INFO: bowl-contaminated (the vignette is still in these frames; a plane fit reads its truncation as ~9-13% tilt) — divided-stage flatness is the real check"),
        "median_shift_pct": (-10.0, 10.0, "G median vs calibrated after rechroma: model-consistent target C_G x median(V) sits within a few % of the calibrated level"),
    },
    "gain": {
        "monotone_violation": (None, 1e-4, "V(r) must be non-increasing — THE ring guard (monotone V cannot print rings)"),
        "corner_gain": (0.38, 0.58, "additive-glow model: true V corner ~0.43, consistent with ~1.3EV lens falloff"),
        "channel_spread": (None, 1e-6, "gray by construction"),
        "ring_p2v_rel": (None, None, "INFO: moving-average detrend lags the knee of a 46%-deep monotone curve (~2.6% false P2V); monotonicity is the enforced check"),
    },
    "divided": {
        "p2v_inner_rel": (None, 0.20, "radial flatness r<=0.85 (full range/median; the recorded ±9% = 0.18)"),
        "rim_dev_rel": (None, 0.25, "rim r>0.9 vs r=0.85 level (open defect)"),
    },
    "registration": {
        "reg_fraction": (0.9, None, "registered/total"),
        "fwhm_med_px": (None, None, "INFO: sampling ratio — px per FWHM; < 2.0 is undersampled (Nyquist) where deconvolution has nothing to recover and drizzle becomes the upgrade path; a deconvolution eligibility input"),
        "fwhm_med_arcsec": (None, None, "INFO: the same FWHM on the sky via the header-derived scale (206.265*XPIXSZ/FOCALLEN, the plate-solve hint derivation); null = header carries no FOCALLEN/XPIXSZ, px-only stated per run"),
        "fwhm_cv_pct": (None, 45.0, "robust FWHM spread (1.4826*MAD/median) across included frames = PSF stability, a deconvolution eligibility input; measured honest corpus (11 sequences, 5 classes): guided short-sub classes 2.0-16.2%, a multi-hour 400-600s archive session 21.6-34.0% (seeing drift, still stacked clean) — the bound clears the worst honest case by ~1.3x"),
        "round_med": (0.30, None, "median roundness fwhmy/fwhmx in (0,1]; measured honest corpus 0.71-0.90 (0.71 = Sigma-180 wide open); the trailed-tripod class (off-disk) reads ~2:1 elongation ~= 0.5 by its recorded star geometry and must pass — 0.30 sits under it with margin; below, stars are >3:1 streaks frame-wide"),
        "bg_span_pct": (None, 130.0, "background level spread (p90-p10)/median of the PSF-fit local background — the cloud/glow drift detector; measured honest corpus: stable-sky classes 2.5-9.6%, dawn-flank archive members 51-103% (final-frame glow the rejection+normalization stack absorbed into an approved base) — the bound clears the worst honest case; a stable-rig dataset can tighten via recipe frame_qa"),
        "nstars_min_frac": (0.35, None, "weakest frame's detected stars / sequence median — the cloud-hit / trailing-spike collapse detector (thin cloud kills the star count while RAISING the background); measured honest corpus: stable classes 0.74-1.00, dawn-flank members 0.47-0.62"),
        "outlier_frames": (None, None, "INFO: frames flagged by robust z (|z|>3.5, the modified-z convention) on fwhm+/bg+/round-/nstars- vs the sequence's own distribution; the per-frame evidence list for any future recipe-level cull ladder — flags in the record, frames named in the report"),
        "wfwhm_excess_pct": (None, None, "INFO: median wFWHM/FWHM - 1; wfwhm = fwhm*(1 + 2*(lost ref matches)/ref stars) per siril 1.4.4, so excess is matching LOSS (cloud/trailing), not seeing"),
        "dither_phase_frac": (None, None, "INFO: fraction of 4x4 sub-pixel phase bins covered by the included frames' registration shifts — the dither-coverage input the full-size drizzle upgrade is gated on"),
    },
    "stack": {
        "p2v_inner_rel": (None, 0.20, "THE flatness check: radial P2V over r<=0.85 of the dark sky with extended objects excluded, so it measures the VIGNETTING RESIDUAL it exists to catch on any framing (empty field, off-centre object, or a galaxy at frame centre)"),
        "n_stars": (300, None, "detected stars — registration/detection sanity"),
        "noise_over_median_pct": (None, None, "INFO: sky diff-MAD noise / sky median. A RATIO TO AN ARBITRARY PEDESTAL — the sky level depends on site darkness and focal ratio, and on siril's -output_norm rescaling by the saturated-star max (38 counts on a dark-sky cooled mono stack vs ~370-600 on a light-polluted DSLR). Not a defect signal; reported as a trend"),
        "bg_median16": (None, None, "INFO: normalized stack level — a normalization and site fact, not a defect"),
        "sky_frac": (None, None, "INFO: fraction of frame graded as sky after the dark-sky and extended-object cuts; an object-dominated field reads low — that is the data class"),
    },
    "compose": {
        "chan_align_px": (None, 1.0, "median star-centroid offset between composed channels — the lines must overlay without a second interpolation pass; measured by compose.py on the composed stack"),
        "chan_align_p95_px": (None, None, "INFO: p95 of the same offsets — outlier tail (field-edge distortion residue)"),
    },
}

ORDER = ["master_dark", "master_flat", "calibrated", "selfflat_median",
         "subsky_frame", "gain", "divided", "registration", "stack",
         "compose"]


def check(stage, metric, value, bounds=None):
    lo, hi, note = EXPECTATIONS[stage][metric]
    if bounds is not None:
        # dataset recipe frame_qa override — same resolution direction as
        # every knob (dataset state > generic), provenance stated in the note
        lo, hi = bounds
        note = f"{note} [dataset frame_qa bounds]"
    if value is None:
        return {"metric": metric, "value": None, "status": "INFO", "note": note}
    st = "PASS"
    if lo is None and hi is None:
        st = "INFO"
    if lo is not None and value < lo:
        st = "WARN"
    if hi is not None and value > hi:
        st = "WARN"
    bound = (f">= {lo}" if hi is None else f"<= {hi}" if lo is None
             else f"{lo} .. {hi}")
    return {"metric": metric, "value": round(float(value), 6),
            "bound": bound, "status": st, "note": note}


def prev_entries(d):
    p = os.path.join(d, "metrics.jsonl")
    if not os.path.exists(p):
        return []
    with open(p) as f:
        return [json.loads(l) for l in f if l.strip()]


def emit(d, entry):
    entry["seq"] = len(prev_entries(d)) + 1
    with open(os.path.join(d, "metrics.jsonl"), "a") as f:
        f.write(json.dumps(entry) + "\n")
    worst = "PASS"
    for c in entry.get("checks", []):
        if c["status"] == "WARN":
            worst = "WARN"
    vals = ", ".join(f"{c['metric']}={c['value']}" for c in entry.get("checks", [])
                     if c["value"] is not None)
    print(f"[inspect] {entry['stage']}{' ' + entry.get('label', '') if entry.get('label') else ''}: {worst}  ({vals})")


def measure_frame(path, want_stars=True, mask_branch=False):
    data, kind = am.load_image(path)
    lv = am.channel_levels(data)
    g = min(1, data.shape[0] - 1)
    centers, prof = am.radial_profile(data, mask_branch=mask_branch)
    rm = am.radial_metrics(centers, prof)
    stars = am.star_metrics(data[g]) if want_stars else {}
    return data, {"levels": lv, "radial": rm, "stars": stars, "kind": kind,
                  "centers": centers.tolist(),
                  "profile": np.where(np.isnan(prof), None, prof).tolist()}


def dust_depth(ch, stride=2, sigma=48):
    """Deepest COHERENT small-scale dip of a flat vs its smooth field:
    1 - min(flat / gaussian(flat, sigma)) over the interior (border band
    excluded — the vignette knee is not dust). A 3 px pre-smooth makes the
    minimum a spatial feature, not a noise tail; dust donuts are 50-500 px
    multiplicative dips, the exact class a flat exists to correct."""
    from scipy import ndimage
    sub = ch[::stride, ::stride].astype(np.float32)
    sub = ndimage.gaussian_filter(sub, 3.0)
    smooth = ndimage.gaussian_filter(sub, sigma / stride)
    ratio = sub / np.maximum(smooth, 1e-6)
    b = max(4, int(0.02 * min(ratio.shape)))
    inner = ratio[b:-b, b:-b]
    return float(1.0 - np.nanmin(inner)) if inner.size else None


def stage_index(stage):
    return ORDER.index(stage) if stage in ORDER else 99


def out_base(d, stage, label):
    n = f"{stage_index(stage):02d}_{stage}"
    if label:
        n += f"_{label}"
    return os.path.join(d, n)


def handle_stage(args):
    d = args.dir
    os.makedirs(d, exist_ok=True)
    stage = args.stage
    prev = prev_entries(d)
    per_frame = []
    rep_idx = len(args.inputs) // 2  # representative: middle sample
    rep = None
    for i, p in enumerate(args.inputs):
        want_stars = stage not in ("gain", "master_dark", "master_flat")
        data, m = measure_frame(p, want_stars=want_stars,
                                mask_branch=stage == "stack")
        m["file"] = os.path.basename(p)
        per_frame.append(m)
        if i == rep_idx:
            rep = (data, m)
        else:
            del data
    data, mrep = rep
    if stage in ("master_dark", "master_flat") \
            and float(np.nanmax(data)) > 1.5:
        # prebuilt header-less masters store ADU-scale floats (measured on
        # the SHO corpus: max 65504); normalize so the level checks and the
        # panel read in the same [0,1] units as built masters — the ratio
        # metrics (corner/center, dust) are scale-invariant either way
        data = data / 65535.0
        mrep["levels"] = am.channel_levels(data)
    base = out_base(d, stage, args.label)
    panel_note = am.render_panel(data, base + ".jpg")
    is8 = mrep.get("kind") == "jpg"
    scale = 255.0 if is8 else D16
    am.plot_radial(np.array(mrep["centers"]),
                   np.array([[np.nan if v is None else v for v in row]
                             for row in mrep["profile"]]),
                   base + "_radial.png",
                   title=f"{stage} {args.label or ''} radial profile",
                   display_scale=scale,
                   ylabel=f"counts ({'8' if is8 else '16'}-bit)")

    g = 1 if len(mrep["levels"]) == 3 else 0
    lev = mrep["levels"][g]
    checks = []

    def find_stage(name):
        for e in reversed(prev):
            if e["stage"] == name:
                return e
        return None

    if stage == "master_dark":
        checks.append(check(stage, "bg_median16", lev["median"] * D16))
        checks.append(check(stage, "clip_frac",
                            max(l["clip_frac"] for l in mrep["levels"])))
        hot = float((data[g] > lev["median"]
                     + 10 * max(lev["bgnoise"], 1e-9)).mean())
        checks.append(check(stage, "hot_frac", hot))
    elif stage == "master_flat":
        checks.append(check(stage, "flat_level_pct", lev["median"] * 100.0))
        profg = [row[g] for row in mrep["profile"] if row[g] is not None]
        cc = (float(np.mean(profg[-2:]) / max(np.mean(profg[:2]), 1e-9))
              if len(profg) > 4 else None)
        checks.append(check(stage, "corner_over_center", cc))
        checks.append(check(stage, "dust_min_rel", dust_depth(data[g])))
        checks.append(check(stage, "clip_frac",
                            max(l["clip_frac"] for l in mrep["levels"])))
    elif stage == "calibrated":
        checks.append(check(stage, "bg_median16", lev["median"] * D16))
        checks.append(check(stage, "clip_frac", max(l["clip_frac"] for l in mrep["levels"])))
        checks.append(check(stage, "n_stars", mrep["stars"].get("n_stars", 0)))
    elif stage == "selfflat_median":
        cal = find_stage("calibrated")
        ratio = None
        if cal:
            counts = [m["stars"].get("n_stars", 0) for m in cal["per_frame"]]
            ncal = float(np.mean(counts)) if counts else 0
            if ncal:
                ratio = mrep["stars"].get("n_stars", 0) / ncal
        checks.append(check(stage, "star_ratio_vs_calibrated", ratio))
        profg = [row[g] for row in mrep["profile"] if row[g] is not None]
        if len(profg) > 4:
            cc = (np.mean(profg[-2:]) / max(np.mean(profg[:2]), 1e-9))
            checks.append(check(stage, "corner_over_center", cc))
    elif stage == "subsky_frame":
        tilt = am.plane_tilt(data[g])
        checks.append(check(stage, "plane_tilt_pct", tilt))
        cal = find_stage("calibrated")
        if cal:
            # compare same sample position (middle) medians
            cmed = cal["per_frame"][min(rep_idx, len(cal["per_frame"]) - 1)]["levels"][g]["median"]
            if cmed > 0:
                checks.append(check(stage, "median_shift_pct",
                                    100.0 * (lev["median"] - cmed) / cmed))
    elif stage == "gain":
        profg = np.array([row[g] for row in mrep["profile"] if row[g] is not None])
        viol = float(np.max(np.diff(profg))) if len(profg) > 2 else None
        checks.append(check(stage, "monotone_violation", viol if viol and viol > 0 else 0.0))
        checks.append(check(stage, "corner_gain", float(profg[-1]) if len(profg) else None))
        arr = np.array([[np.nan if v is None else v for v in row]
                        for row in mrep["profile"]], dtype=float)
        spread = float(np.nanmax(np.nanmax(arr, axis=1) - np.nanmin(arr, axis=1)))
        checks.append(check(stage, "channel_spread", spread))
        rp = mrep["radial"].get("ring_p2v")
        checks.append(check(stage, "ring_p2v_rel",
                            rp / max(float(np.nanmean(arr)), 1e-9) if rp is not None else None))
    elif stage == "divided":
        checks.append(check(stage, "p2v_inner_rel", mrep["radial"].get("p2v_inner_rel")))
        checks.append(check(stage, "rim_dev_rel", mrep["radial"].get("rim_dev_rel")))
    elif stage == "stack":
        # flatness + noise on the statistical dark sky (composition-agnostic):
        # a frame-filling object (galaxy / nebula / MW) is real signal, not a
        # flat-field defect, so it must not read as one — the gate's lesson,
        # applied to the linear stack. The whole-frame radial plot still shows
        # the object; only the graded numbers use the sky scope.
        sf = am.sky_flatness(data)
        nm = (100.0 * sf["sky_noise"] / max(sf["sky_median"], 1e-9)
              if sf["sky_noise"] and sf["sky_median"] else None)
        checks.append(check(stage, "noise_over_median_pct", nm))
        checks.append(check(stage, "p2v_inner_rel", sf["sky_p2v_inner"]))
        checks.append(check(stage, "sky_frac", sf["sky_frac"]))
        checks.append(check(stage, "n_stars", mrep["stars"].get("n_stars", 0)))
        checks.append(check(stage, "bg_median16", lev["median"] * D16))

    entry = {"stage": stage, "label": args.label, "inputs": args.inputs,
             "panel": os.path.basename(base + ".jpg"),
             "radial_png": os.path.basename(base + "_radial.png"),
             "panel_note": panel_note, "checks": checks,
             "per_frame": [{k: v for k, v in m.items() if k not in ("centers", "profile")}
                           for m in per_frame],
             "centers": mrep["centers"], "profile": mrep["profile"]}
    emit(d, entry)


def parse_seq_regdata(seqfile):
    """Full parse of siril .seq registration data. Structure verified
    against siril 1.4.4 (seqfile.c, R-line format v4+):

        R<layer> fwhm wfwhm roundness quality background_lvl nstars H h00..h22

    Semantics per the official regdata reference: fwhm = PSF fwhmx (px on
    these unsolved work frames); roundness = fwhmy/fwhmx in (0,1];
    background_lvl = PSF-fit local background, UNITS BITDEPTH-DEPENDENT
    (measured on this rig's 16-bit sequences: 16-bit ADU counts, not
    [0,1] — the caller normalizes to counts16 by value range); wfwhm =
    fwhm*(1 + 2*(ref stars - matched)/ref stars) — a matching-loss metric;
    quality is the planetary registration score (unset for star reg); H
    maps this frame -> reference, h02/h12 = translation px. Returns
    {"name", "fixed", "reference", "images": [(filenum, incl), ...],
    "layers": {layer: [row, ...]}} or None when ANY line deviates from the
    known structure — a siril format change must fall back loudly, never
    mis-parse silently."""
    try:
        name, fixed, reference = None, 5, -1
        images, layers = [], {}
        with open(seqfile) as f:
            for line in f:
                if line.startswith("S "):
                    m = re.match(
                        r"S '(.*)' (-?\d+) (\d+) (\d+) (\d+) (-?\d+)", line)
                    if not m:
                        return None
                    name = m.group(1)
                    fixed = int(m.group(5))
                    reference = int(m.group(6))
                elif line.startswith("I "):
                    t = line.split()
                    if len(t) < 3:
                        return None
                    images.append((int(t[1]), int(t[2])))
                elif line.startswith("R") and len(line) > 1 \
                        and (line[1].isdigit() or line[1] == "*"):
                    t = line.split()
                    if len(t) < 17 or t[7] != "H":
                        return None
                    row = {"fwhm": float(t[1]), "wfwhm": float(t[2]),
                           "round": float(t[3]), "quality": float(t[4]),
                           "bg": float(t[5]), "nstars": int(t[6]),
                           "H": [float(x) for x in t[8:17]]}
                    layers.setdefault(t[0][1:], []).append(row)
        if name is None or not images or not layers:
            return None
        return {"name": name, "fixed": fixed, "reference": reference,
                "images": images, "layers": layers}
    except (OSError, ValueError):
        return None


def parse_seq_shifts(seqfile):
    """Fallback shift extraction when parse_seq_regdata refuses a .seq
    (unknown structure): pull per-frame translation from any 9-float
    homography-looking window. Returns list of (dx, dy) or None."""
    try:
        shifts = []
        with open(seqfile) as f:
            for line in f:
                if not line.startswith("R"):
                    continue
                toks = line.replace("=", " ").split()
                floats = []
                for t in toks[1:]:
                    try:
                        floats.append(float(t))
                    except ValueError:
                        pass
                # find a 9-window that looks like [1,a,tx, b,1,ty, ~0,~0,1]
                for i in range(0, max(0, len(floats) - 8)):
                    w = floats[i:i + 9]
                    if (abs(w[0] - 1) < 0.2 and abs(w[4] - 1) < 0.2
                            and abs(w[8] - 1) < 0.05):
                        shifts.append((w[2], w[5]))
                        break
        return shifts or None
    except OSError:
        return None


def handle_compose(args):
    d = args.dir
    os.makedirs(d, exist_ok=True)
    checks = [check("compose", "chan_align_px", args.resid),
              check("compose", "chan_align_p95_px", args.p95)]
    emit(d, {"stage": "compose", "label": None, "inputs": [],
             "checks": checks})


def _robust_z(vals):
    """Per-value robust z vs the list's own median/MAD (1.4826*MAD ~ sigma).
    MAD 0 (constant metric) -> all z 0: a flat distribution has no outliers."""
    a = np.asarray(vals, dtype=float)
    med = float(np.median(a))
    s = 1.4826 * float(np.median(np.abs(a - med)))
    return [(float(v) - med) / s if s > 0 else 0.0 for v in a]


# Robust per-frame outlier flag threshold: the modified-z convention (a
# metric 3.5 robust sigmas from the sequence's own median). Calibrated on
# the 11-sequence on-disk corpus: non-event frames stay under |z| ~3.4,
# while every flag at 3.5+ maps to an interpretable physical event —
# dawn-glow frames at bg z +3.8..+119, seeing excursions at fwhm z
# +4.4/+5.5, one trailing spike at round -3.9 with nstars -13.6.
OUTLIER_Z = 3.5


def _frame_qa_bounds(session, set_name):
    """Per-dataset WARN-bound overrides: optional 'frame_qa' block in the
    dataset recipe ({metric: [lo, hi]}), same resolution direction as every
    knob (dataset state > generic). Returns ({metric: (lo, hi)}, provenance
    string) — datasets without state degrade to the generic EXPECTATIONS
    table, and the provenance line says which layer applied either way."""
    if not (session and set_name):
        return {}, "generic (no dataset context)"
    p = os.path.join(am.dataset_dir(session, set_name), "recipe.json")
    if not os.path.exists(p):
        return {}, "generic (no dataset recipe)"
    try:
        fq = json.load(open(p)).get("frame_qa", {})
    except (OSError, ValueError) as e:
        return {}, f"generic (recipe unreadable: {e})"
    known = set(EXPECTATIONS["registration"])
    unknown = set(fq) - known
    if unknown:
        print(f"[inspect] WARNING: recipe frame_qa names unknown metrics "
              f"{sorted(unknown)} — ignored (known: {sorted(known)})")
    ov = {k: (v[0], v[1]) for k, v in fq.items() if k in known}
    if ov:
        return ov, "recipe frame_qa: " + ", ".join(
            f"{k}={list(v)}" for k, v in sorted(ov.items()))
    return {}, "generic (recipe has no frame_qa)"


def _seq_frame_path(seqdir, name, fixed, filenum):
    for ext in (".fit", ".fits", ".fts"):
        p = os.path.join(seqdir, f"{name}{filenum:0{fixed}d}{ext}")
        if os.path.exists(p):
            return p
    return None


def handle_reg(args):
    d = args.dir
    os.makedirs(d, exist_ok=True)
    frac = args.registered / max(args.total, 1)
    ov, prov = _frame_qa_bounds(args.session, args.set_name)

    def rcheck(metric, value):
        return check("registration", metric, value, bounds=ov.get(metric))

    checks = [rcheck("reg_fraction", frac)]
    entry = {"stage": "registration", "label": args.label,
             "inputs": [], "checks": checks,
             "registered": args.registered, "total": args.total,
             "ref": args.ref, "sweep": args.sweep}
    print(f"[inspect] registration bounds: {prov}")
    if args.seq and os.path.exists(args.seq):
        # Persist the ground truth alongside the parsed record: the .seq
        # dies in per-stage cleanup, and a future format question is only
        # answerable from the file itself (KB-scale, kept per run).
        base = out_base(d, "registration", args.label)
        with open(args.seq) as fsrc, open(base + ".seq", "w") as fdst:
            fdst.write(fsrc.read())
        entry["seq_copy"] = os.path.basename(base + ".seq")
        parsed = parse_seq_regdata(args.seq)
        if parsed is None:
            print("[inspect] WARNING: .seq regdata structure not the known "
                  "siril 1.4 form — per-frame stats NOT parsed (format "
                  "change?); shift range from fallback heuristic only")
            sh = parse_seq_shifts(args.seq)
            if sh:
                dx = [s[0] for s in sh]
                dy = [s[1] for s in sh]
                entry["shift_range_px"] = [round(max(dx) - min(dx), 1),
                                           round(max(dy) - min(dy), 1)]
        else:
            _reg_frames(entry, checks, parsed, args, rcheck)
    emit(d, entry)


def _reg_frames(entry, checks, parsed, args, rcheck):
    """Per-frame quality records + distribution checks from parsed regdata.
    Everything lands in the metrics.jsonl entry BEFORE the runner prunes
    the sequence: records first, cleanup after."""
    # registration layer = the layer that carries star data (green for
    # colour by siril default, 0 for mono); a layer with no stars anywhere
    # is transform-only padding
    layers = {L: rows for L, rows in parsed["layers"].items()
              if any(r["nstars"] > 0 or r["fwhm"] > 0 for r in rows)}
    if not layers:
        print("[inspect] WARNING: .seq carries no star regdata on any "
              "layer — per-frame stats empty")
        return
    reg_layer = max(layers, key=lambda L: sum(r["nstars"]
                                              for r in layers[L]))
    rows = layers[reg_layer]
    if len(rows) != len(parsed["images"]):
        print(f"[inspect] WARNING: regdata rows ({len(rows)}) != images "
              f"({len(parsed['images'])}) — per-frame stats skipped")
        return

    # pixel scale from the sequence's own reference frame header (frames
    # still on disk at this point; the derivation is the plate-solve hint's)
    seqdir = os.path.dirname(os.path.abspath(args.seq))
    ref_i = parsed["reference"] if 0 <= parsed["reference"] < len(rows) \
        else next((i for i, (_, inc) in enumerate(parsed["images"]) if inc),
                  0)
    spath = _seq_frame_path(seqdir, parsed["name"], parsed["fixed"],
                            parsed["images"][ref_i][0])
    scale = am.fits_pixel_scale(spath) if spath else None
    if scale:
        print(f"[inspect] registration scale: {scale:.3f} arcsec/px "
              f"(FOCALLEN/XPIXSZ, {os.path.basename(spath)})")
    else:
        print("[inspect] registration scale: UNKNOWN (no FOCALLEN/XPIXSZ "
              "in frame header) — FWHM px only")

    # background_lvl units are sequence-bitdepth dependent (measured on this
    # rig's 16-bit sequences: values land in 16-bit ADU counts, ~1060 on a
    # ~958-count sky — NOT [0,1]); a float sequence stores [0,1]. Normalize
    # to counts16 either way so the record reads like every other bg metric.
    bgraw = [r["bg"] for r in rows if r["nstars"] > 0 or r["fwhm"] > 0]
    bg_is_float = bool(bgraw) and max(bgraw) <= 1.5
    frames = []
    for (filenum, incl), r in zip(parsed["images"], rows):
        has = r["nstars"] > 0 or r["fwhm"] > 0
        frames.append({
            "n": filenum, "incl": incl,
            "fwhm_px": round(r["fwhm"], 3) if has else None,
            "fwhm_arcsec": (round(r["fwhm"] * scale, 3)
                            if has and scale else None),
            "wfwhm_px": round(r["wfwhm"], 3) if has else None,
            "round": round(r["round"], 4) if has else None,
            "bg16": (round(r["bg"] * D16 if bg_is_float else r["bg"], 1)
                     if has else None),
            "nstars": r["nstars"] if has else None,
            "quality": round(r["quality"], 6),
            "dx": round(r["H"][2], 3), "dy": round(r["H"][5], 3)})
    entry["seq_name"] = parsed["name"]
    entry["reg_layer"] = reg_layer
    entry["pixel_scale_arcsec"] = round(scale, 4) if scale else None
    entry["frames"] = frames

    sel = [f for f in frames if f["incl"] and f["fwhm_px"] is not None]
    if not sel:
        print("[inspect] WARNING: no included frame carries regdata — "
              "distribution checks skipped")
        return
    fwhm = [f["fwhm_px"] for f in sel]
    wfw = [f["wfwhm_px"] for f in sel]
    rnd = [f["round"] for f in sel]
    bg = [f["bg16"] for f in sel]
    nst = [f["nstars"] for f in sel]
    fmed = float(np.median(fwhm))
    fmad = 1.4826 * float(np.median(np.abs(np.array(fwhm) - fmed)))
    bmed = float(np.median(bg))
    checks.append(rcheck("fwhm_med_px", fmed))
    checks.append(rcheck("fwhm_med_arcsec",
                         fmed * scale if scale else None))
    checks.append(rcheck("fwhm_cv_pct",
                         100.0 * fmad / fmed if fmed > 0 else None))
    checks.append(rcheck("round_med", float(np.median(rnd))))
    checks.append(rcheck("bg_span_pct",
                         (100.0 * (float(np.percentile(bg, 90))
                                   - float(np.percentile(bg, 10))) / bmed
                          if bmed > 0 else None)))
    checks.append(rcheck("nstars_min_frac",
                         min(nst) / max(float(np.median(nst)), 1.0)))
    checks.append(rcheck("wfwhm_excess_pct",
                         (100.0 * (float(np.median(wfw)) / fmed - 1.0)
                          if fmed > 0 else None)))

    # per-frame outliers: each metric graded against the sequence's own
    # distribution, defect side only (fwhm/bg high = seeing-focus/cloud;
    # roundness/nstars low = trailing/cloud)
    zf, zb = _robust_z(fwhm), _robust_z(bg)
    zr, zn = _robust_z(rnd), _robust_z(nst)
    outliers = []
    for i, f in enumerate(sel):
        flags = []
        if zf[i] > OUTLIER_Z:
            flags.append(f"fwhm+{zf[i]:.1f}z")
        if zb[i] > OUTLIER_Z:
            flags.append(f"bg+{zb[i]:.1f}z")
        if zr[i] < -OUTLIER_Z:
            flags.append(f"round{zr[i]:.1f}z")
        if zn[i] < -OUTLIER_Z:
            flags.append(f"nstars{zn[i]:.1f}z")
        if flags:
            outliers.append({"n": f["n"], "flags": flags})
    entry["outliers"] = outliers
    checks.append(rcheck("outlier_frames", float(len(outliers))))

    dx = [f["dx"] for f in sel]
    dy = [f["dy"] for f in sel]
    entry["shift_range_px"] = [round(max(dx) - min(dx), 1),
                               round(max(dy) - min(dy), 1)]
    # dither-phase coverage: sub-pixel phase of each shift, binned 4x4 —
    # the drizzle upgrade's gating question is whether these phases are
    # DIVERSE, and ranges alone cannot answer it (the recorded lesson)
    bins = {(int((x % 1.0) * 4), int((y % 1.0) * 4)) for x, y in zip(dx, dy)}
    checks.append(rcheck("dither_phase_frac", len(bins) / 16.0))


BADGE = {"PASS": "#2e7d32", "WARN": "#e65100", "INFO": "#546e7a"}


def handle_report(args):
    d = args.dir
    entries = prev_entries(d)
    entries.sort(key=lambda e: (stage_index(e["stage"]), e["seq"]))
    qa_text = ""
    if args.qa and os.path.exists(args.qa):
        qa_text = open(args.qa).read()

    def worst(e):
        sts = [c["status"] for c in e.get("checks", [])]
        return "WARN" if "WARN" in sts else ("PASS" if "PASS" in sts else "INFO")

    md = [f"# Inspection report — {args.title or os.path.basename(d)}", ""]
    md += ["| stage | verdict | key metrics |", "|---|---|---|"]
    html = ["<!DOCTYPE html><html><head><meta charset='utf-8'>",
            f"<title>{args.title or 'inspection'}</title><style>",
            "body{font-family:system-ui,sans-serif;margin:20px;background:#111;color:#ddd}",
            "img{max-width:100%;border:1px solid #333;border-radius:4px}",
            "table{border-collapse:collapse;margin:8px 0}",
            "td,th{border:1px solid #444;padding:3px 8px;font-size:13px}",
            ".badge{padding:2px 8px;border-radius:4px;color:#fff;font-size:12px}",
            "h2{margin-top:28px;border-bottom:1px solid #333}",
            "pre{background:#1b1b1b;padding:8px;border-radius:4px}",
            "details{margin:6px 0}</style></head><body>",
            f"<h1>{args.title or os.path.basename(d)}</h1>"]
    html.append("<table><tr><th>stage</th><th>verdict</th><th>key metrics</th></tr>")
    for e in entries:
        w = worst(e)
        kv = ", ".join(f"{c['metric']}={c['value']}" for c in e.get("checks", [])
                       if c.get("value") is not None)
        label = f"{e['stage']}" + (f" ({e['label']})" if e.get("label") else "")
        md.append(f"| {label} | {w} | {kv} |")
        html.append(f"<tr><td><a href='#s{e['seq']}'>{label}</a></td>"
                    f"<td><span class='badge' style='background:{BADGE[w]}'>{w}</span></td>"
                    f"<td>{kv}</td></tr>")
    html.append("</table>")
    md.append("")

    for e in entries:
        w = worst(e)
        label = f"{e['stage']}" + (f" ({e['label']})" if e.get("label") else "")
        html.append(f"<h2 id='s{e['seq']}'>{label} "
                    f"<span class='badge' style='background:{BADGE[w]}'>{w}</span></h2>")
        md.append(f"## {label} — {w}")
        if e["stage"] == "registration":
            ref = e["ref"] if e.get("ref") is not None else "auto (2-pass)"
            info = (f"registered {e['registered']}/{e['total']} @ ref {ref}"
                    + (f", sweep {e['sweep']}" if e.get("sweep") else "")
                    + (f", shift range {e.get('shift_range_px')} px"
                       if e.get("shift_range_px") else "")
                    + (f", layer {e['reg_layer']}"
                       if e.get("reg_layer") is not None else "")
                    + (f", scale {e['pixel_scale_arcsec']} arcsec/px"
                       if e.get("pixel_scale_arcsec")
                       else ", scale unknown (px only)"))
            if e.get("outliers"):
                info += ", outlier frames: " + "; ".join(
                    f"{o['n']} ({','.join(o['flags'])})"
                    for o in e["outliers"])
            html.append(f"<p>{info}</p>")
            md.append(info)
            fr = e.get("frames") or []
            if fr:
                oflag = {o["n"]: ",".join(o["flags"])
                         for o in e.get("outliers", [])}
                html.append("<details><summary>per-frame registration "
                            "quality (regdata)</summary><table>")
                html.append("<tr><th>frame</th><th>incl</th>"
                            "<th>FWHM px</th><th>FWHM \"</th>"
                            "<th>wFWHM px</th><th>round</th>"
                            "<th>bg(16b)</th><th>stars</th>"
                            "<th>dx</th><th>dy</th><th>flags</th></tr>")
                for f in fr:
                    def c(v):
                        return "" if v is None else v
                    html.append(
                        f"<tr><td>{f['n']}</td><td>{f['incl']}</td>"
                        f"<td>{c(f['fwhm_px'])}</td>"
                        f"<td>{c(f['fwhm_arcsec'])}</td>"
                        f"<td>{c(f['wfwhm_px'])}</td>"
                        f"<td>{c(f['round'])}</td><td>{c(f['bg16'])}</td>"
                        f"<td>{c(f['nstars'])}</td><td>{f['dx']}</td>"
                        f"<td>{f['dy']}</td>"
                        f"<td>{oflag.get(f['n'], '')}</td></tr>")
                html.append("</table></details>")
        if e.get("panel"):
            html.append(f"<p><img src='{e['panel']}' loading='lazy'></p>"
                        f"<p style='color:#888;font-size:12px'>{e.get('panel_note', {}).get('panels', '')}</p>")
            md.append(f"![{label}]({e['panel']})")
        if e.get("radial_png"):
            html.append(f"<p><img src='{e['radial_png']}' style='max-width:640px' loading='lazy'></p>")
            md.append(f"![radial]({e['radial_png']})")
        if e.get("checks"):
            html.append("<table><tr><th>check</th><th>value</th><th>bound</th>"
                        "<th>status</th><th>note</th></tr>")
            for c in e["checks"]:
                html.append(f"<tr><td>{c['metric']}</td><td>{c.get('value')}</td>"
                            f"<td>{c.get('bound', '')}</td>"
                            f"<td><span class='badge' style='background:{BADGE[c['status']]}'>{c['status']}</span></td>"
                            f"<td>{c.get('note', '')}</td></tr>")
                md.append(f"- {c['metric']} = {c.get('value')} ({c.get('bound', 'info')}) {c['status']}")
            html.append("</table>")
        pf = e.get("per_frame") or []
        if pf:
            html.append("<details><summary>per-frame raw metrics</summary><table>")
            html.append("<tr><th>file</th><th>G median(16b)</th><th>G bgnoise(16b)</th>"
                        "<th>stars</th><th>FWHM-eq</th><th>elong</th><th>halo</th>"
                        "<th>top100 peak</th></tr>")
            def cell(v, fmt="{:.2f}", scale=1.0):
                return "" if v is None else fmt.format(v * scale)
            for m in pf:
                g = 1 if len(m["levels"]) == 3 else 0
                s = m.get("stars", {})
                pk_scale = 255.0 if m.get("kind") == "jpg" else D16
                html.append(
                    "<tr><td>" + str(m.get("file", "")) + "</td>"
                    + "<td>" + cell(m["levels"][g]["median"], "{:.1f}", D16) + "</td>"
                    + "<td>" + cell(m["levels"][g]["bgnoise"], "{:.2f}", D16) + "</td>"
                    + "<td>" + str(s.get("n_stars", "")) + "</td>"
                    + "<td>" + cell(s.get("fwhm_med"), "{:.1f}") + "</td>"
                    + "<td>" + cell(s.get("elong_med")) + "</td>"
                    + "<td>" + cell(s.get("halo_med")) + "</td>"
                    + "<td>" + cell(s.get("top100_peak_med"), "{:.0f}", pk_scale)
                    + "</td></tr>")
            html.append("</table></details>")
        md.append("")
    if qa_text:
        html.append("<h2>bg_qa gate (final preview)</h2><pre>"
                    + qa_text.replace("<", "&lt;") + "</pre>")
        md += ["## bg_qa gate", "```", qa_text.rstrip(), "```", ""]
    html.append("</body></html>")
    with open(os.path.join(d, "index.html"), "w") as f:
        f.write("\n".join(html))
    with open(os.path.join(d, "index.md"), "w") as f:
        f.write("\n".join(md) + "\n")
    warns = sum(1 for e in entries if worst(e) == "WARN")
    print(f"[inspect] report: {os.path.join(d, 'index.html')} "
          f"({len(entries)} stages, {warns} WARN)")


def main():
    ap = argparse.ArgumentParser()
    ctxp = argparse.ArgumentParser(add_help=False)
    ctxp.add_argument("--session", default=None,
                      help="session dir (per-set geometry context)")
    ctxp.add_argument("--set", dest="set_name", default=None)
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("stage", parents=[ctxp])
    s.add_argument("stage", choices=[k for k in ORDER if k != "registration"])
    s.add_argument("--dir", required=True)
    s.add_argument("--in", dest="inputs", nargs="+", required=True)
    s.add_argument("--label", default=None)
    r = sub.add_parser("reg", parents=[ctxp])
    r.add_argument("--dir", required=True)
    r.add_argument("--label", default=None,
                   help="distinguishes multiple registrations in one run "
                        "(dual-band line sequences)")
    r.add_argument("--registered", type=int, required=True)
    r.add_argument("--total", type=int, required=True)
    r.add_argument("--ref", type=int, default=None,
                   help="reference frame index (omit when siril's 2-pass "
                        "auto-pick chose it)")
    r.add_argument("--sweep", default=None)
    r.add_argument("--seq", default=None)
    c = sub.add_parser("compose", parents=[ctxp])
    c.add_argument("--dir", required=True)
    c.add_argument("--resid", type=float, required=True,
                   help="median channel-registration residual, px")
    c.add_argument("--p95", type=float, default=None)
    p = sub.add_parser("report", parents=[ctxp])
    p.add_argument("--dir", required=True)
    p.add_argument("--title", default=None)
    p.add_argument("--qa", default=None)
    args = ap.parse_args()
    if args.session and args.set_name:
        am.configure(args.session, args.set_name, quiet=True)
    if args.cmd == "stage":
        handle_stage(args)
    elif args.cmd == "reg":
        handle_reg(args)
    elif args.cmd == "compose":
        handle_compose(args)
    else:
        handle_report(args)


if __name__ == "__main__":
    main()
