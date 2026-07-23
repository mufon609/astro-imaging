#!/usr/bin/env python3
"""Persist siril's registration measurements + assemble the run report.

Usage:
  inspect_stage.py reg    --dir <inspect-dir> --registered N --total M
                   [--ref R] [--sweep "11:19,12:21"] [--seq seqfile] [--label L]
  inspect_stage.py report --dir <inspect-dir> [--title T]

This tool EXAMINES and REPORTS only — it never reads or grades the
deliverable's pixels. Its one measurement source is siril's registration
regdata: `reg` parses the .seq siril `register` already computed (FWHM /
wFWHM / roundness / background / star count / homography per frame) and
persists the full per-frame records — including the shift list the drizzle
path needs — into <dir>/metrics.jsonl plus a .seq copy, BEFORE per-stage
cleanup prunes the sequence. The recorded numbers are siril's; the only
in-house computation is derived summaries over them (median/spread, and
robust-z outlier flags) — report-only evidence for a future recipe-level
cull ladder, never an auto-gate. Weighting/culling POLICY lives elsewhere
(the optional per-dataset "stack" recipe block, applied by run_pipeline at
stack time); this stage only records what the registration tool measured
and names the frames its numbers flag.

`report` assembles index.html + index.md from the recorded entries. No
per-frame quality THRESHOLDS are applied here: grading an image is the
tools' job, out of scope of this examine/orchestrate layer.

REMOVAL CONDITION (the derived summaries + robust-z flags only): retire them
the day a tool reports headless per-frame outlier flagging over its own
registration metrics (SubframeSelector-class, scriptable); persisting the
tool's regdata — this file's real job — stays regardless.
"""
import argparse
import json
import os
import re
import sys

import numpy as np

# scripts/lib holds the shared lib (astrometrics); locate it by walking up
# from this file so one bootstrap works at any nesting depth.
_libdir = os.path.dirname(os.path.abspath(__file__))
while _libdir != os.path.dirname(_libdir):
    if os.path.isdir(os.path.join(_libdir, "lib")):
        sys.path.insert(0, os.path.join(_libdir, "lib"))
        break
    _libdir = os.path.dirname(_libdir)
import astrometrics as am  # noqa: E402

D16 = 65535.0


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
    s = entry.get("summary", {})
    vals = ", ".join(f"{k}={v}" for k, v in s.items() if v is not None)
    lbl = f" {entry['label']}" if entry.get("label") else ""
    print(f"[inspect] {entry['stage']}{lbl}: recorded"
          + (f"  ({vals})" if vals else ""))


def out_base(d, label):
    return os.path.join(d, "00_registration" + (f"_{label}" if label else ""))


# --- siril registration regdata -> per-frame records -------------------------

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
# +4.4/+5.5, one trailing spike at round -3.9 with nstars -13.6. This flags;
# it never culls (the cull decision is a recipe with/without ladder).
OUTLIER_Z = 3.5


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
    summary = {"reg_fraction": round(frac, 4)}
    entry = {"stage": "registration", "label": args.label, "summary": summary,
             "registered": args.registered, "total": args.total,
             "ref": args.ref, "sweep": args.sweep}
    if args.seq and os.path.exists(args.seq):
        # Persist the ground truth alongside the parsed record: the .seq
        # dies in per-stage cleanup, and a future format question is only
        # answerable from the file itself (KB-scale, kept per run).
        base = out_base(d, args.label)
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
            _reg_frames(entry, summary, parsed, args)
    emit(d, entry)


def _reg_frames(entry, summary, parsed, args):
    """Per-frame quality records + distribution summaries from parsed
    regdata. Everything lands in the metrics.jsonl entry BEFORE the runner
    prunes the sequence: records first, cleanup after. All numbers are
    siril's; the summaries (median/spread, robust-z outlier flags) are
    derived over them and are RECORDED, never a bound/gate."""
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
              "distribution summaries skipped")
        return
    fwhm = [f["fwhm_px"] for f in sel]
    wfw = [f["wfwhm_px"] for f in sel]
    rnd = [f["round"] for f in sel]
    bg = [f["bg16"] for f in sel]
    nst = [f["nstars"] for f in sel]
    fmed = float(np.median(fwhm))
    fmad = 1.4826 * float(np.median(np.abs(np.array(fwhm) - fmed)))
    bmed = float(np.median(bg))
    # derived distribution summaries over siril's per-frame measures
    # (recorded context, not bounds): PSF size + spread, roundness, the
    # background drift span, the weakest frame's star fraction, wFWHM excess
    summary["fwhm_med_px"] = round(fmed, 3)
    summary["fwhm_med_arcsec"] = round(fmed * scale, 3) if scale else None
    summary["fwhm_cv_pct"] = round(100.0 * fmad / fmed, 2) if fmed > 0 else None
    summary["round_med"] = round(float(np.median(rnd)), 4)
    summary["bg_span_pct"] = (round(100.0 * (float(np.percentile(bg, 90))
                                             - float(np.percentile(bg, 10)))
                                    / bmed, 1) if bmed > 0 else None)
    summary["nstars_min_frac"] = round(
        min(nst) / max(float(np.median(nst)), 1.0), 3)
    summary["wfwhm_excess_pct"] = (
        round(100.0 * (float(np.median(wfw)) / fmed - 1.0), 1)
        if fmed > 0 else None)

    # per-frame outliers: each metric graded against the sequence's own
    # distribution, defect side only (fwhm/bg high = seeing-focus/cloud;
    # roundness/nstars low = trailing/cloud). Recorded as evidence, never
    # a cull (the cull is a recipe with/without ladder — README).
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
    summary["outlier_frames"] = len(outliers)

    dx = [f["dx"] for f in sel]
    dy = [f["dy"] for f in sel]
    entry["shift_range_px"] = [round(max(dx) - min(dx), 1),
                               round(max(dy) - min(dy), 1)]
    # dither-phase coverage: sub-pixel phase of each shift, binned 4x4 —
    # the drizzle upgrade's gating question is whether these phases are
    # DIVERSE, and ranges alone cannot answer it (the recorded lesson)
    bins = {(int((x % 1.0) * 4), int((y % 1.0) * 4)) for x, y in zip(dx, dy)}
    summary["dither_phase_frac"] = round(len(bins) / 16.0, 3)


def handle_report(args):
    d = args.dir
    entries = prev_entries(d)
    entries.sort(key=lambda e: e["seq"])
    title = args.title or os.path.basename(d)

    intro = ("Per-frame quality from siril's registration regdata "
             "(FWHM / roundness / background / star count / homography). "
             "Report-only: it records what the registration tool measured and "
             "flags robust-z outliers as evidence for a future recipe-level "
             "cull ladder — it never gates or aborts a run.")
    md = [f"# Registration report — {title}", "", intro, ""]
    html = ["<!DOCTYPE html><html><head><meta charset='utf-8'>",
            f"<title>{title}</title><style>",
            "body{font-family:system-ui,sans-serif;margin:20px;"
            "background:#111;color:#ddd}",
            "table{border-collapse:collapse;margin:8px 0}",
            "td,th{border:1px solid #444;padding:3px 8px;font-size:13px}",
            "h2{margin-top:28px;border-bottom:1px solid #333}",
            "details{margin:6px 0}</style></head><body>",
            f"<h1>{title}</h1>", f"<p>{intro}</p>"]
    if not entries:
        html.append("<p>(no registration records)</p>")
        md.append("_(no registration records)_")
    for e in entries:
        label = e["stage"] + (f" ({e['label']})" if e.get("label") else "")
        ref = e["ref"] if e.get("ref") is not None else "auto (2-pass)"
        info = (f"registered {e.get('registered')}/{e.get('total')} @ ref "
                f"{ref}"
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
                f"{o['n']} ({','.join(o['flags'])})" for o in e["outliers"])
        html.append(f"<h2>{label}</h2><p>{info}</p>")
        md += [f"## {label}", info, ""]
        s = e.get("summary", {})
        if s:
            html.append("<table><tr><th>metric</th><th>value</th></tr>")
            for k, v in s.items():
                html.append(f"<tr><td>{k}</td><td>{v}</td></tr>")
                md.append(f"- {k} = {v}")
            html.append("</table>")
            md.append("")
        fr = e.get("frames") or []
        if fr:
            oflag = {o["n"]: ",".join(o["flags"])
                     for o in e.get("outliers", [])}
            html.append("<details><summary>per-frame registration quality "
                        "(siril regdata)</summary><table>")
            html.append("<tr><th>frame</th><th>incl</th><th>FWHM px</th>"
                        "<th>FWHM \"</th><th>wFWHM px</th><th>round</th>"
                        "<th>bg(16b)</th><th>stars</th><th>dx</th><th>dy</th>"
                        "<th>flags</th></tr>")
            for f in fr:
                def c(v):
                    return "" if v is None else v
                html.append(
                    f"<tr><td>{f['n']}</td><td>{f['incl']}</td>"
                    f"<td>{c(f['fwhm_px'])}</td><td>{c(f['fwhm_arcsec'])}</td>"
                    f"<td>{c(f['wfwhm_px'])}</td><td>{c(f['round'])}</td>"
                    f"<td>{c(f['bg16'])}</td><td>{c(f['nstars'])}</td>"
                    f"<td>{f['dx']}</td><td>{f['dy']}</td>"
                    f"<td>{oflag.get(f['n'], '')}</td></tr>")
            html.append("</table></details>")
    html.append("</body></html>")
    with open(os.path.join(d, "index.html"), "w") as f:
        f.write("\n".join(html))
    with open(os.path.join(d, "index.md"), "w") as f:
        f.write("\n".join(md) + "\n")
    print(f"[inspect] report: {os.path.join(d, 'index.html')} "
          f"({len(entries)} registration record(s))")


def main():
    ap = argparse.ArgumentParser()
    # --session/--set are accepted for run_pipeline's shared INS wrapper;
    # this examine/report tool needs no per-set geometry (it works on
    # siril's regdata, never the deliverable's pixels).
    ctxp = argparse.ArgumentParser(add_help=False)
    ctxp.add_argument("--session", default=None)
    ctxp.add_argument("--set", dest="set_name", default=None)
    sub = ap.add_subparsers(dest="cmd", required=True)
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
    p = sub.add_parser("report", parents=[ctxp])
    p.add_argument("--dir", required=True)
    p.add_argument("--title", default=None)
    args = ap.parse_args()
    if args.cmd == "reg":
        handle_reg(args)
    else:
        handle_report(args)


if __name__ == "__main__":
    main()
