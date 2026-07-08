#!/usr/bin/env python3
"""Per-stage pipeline inspection: consistent-stretch JPEG + metrics +
PASS/WARN against the expectations table (NOTES.md "Per-stage expectations").

Usage:
  inspect_stage.py stage <stage-name> --dir <inspect-dir> --in F [F ...]
                   [--label L]
  inspect_stage.py reg   --dir <inspect-dir> --registered N --total M
                   --ref R [--sweep "11:19,12:21"] [--seq seqfile]
  inspect_stage.py report --dir <inspect-dir> [--title T] [--qa qa.txt]

Stage names: calibrated, selfflat_median, subsky_frame, gain, divided,
stack, post_subsky, post_denoise, post_stretch, final.

Every 'stage' call appends one JSON line to <dir>/metrics.jsonl and writes
<NN>_<stage>.jpg (one CONSISTENT autostretch: linked MTF, shadow clip
median-2.8*bgnoise, bg target 0.25 — every stage, every run) plus
<NN>_<stage>_radial.png. 'report' assembles index.html + index.md.
Inspection WARNs, it never fails a run — the hard gate stays bg_qa.py.
"""
import argparse
import json
import os
import sys
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import astrometrics as am  # noqa: E402
import bg_qa  # noqa: E402

D16 = 65535.0

# stage -> metric -> (lo, hi, note); units: 16-bit display counts for linear
# stages, 8-bit counts for stretched. THIS table is authoritative (NOTES.md
# carries a summary). Bounds are WARN bounds (inspection), not the bg_qa
# gate. They are sanity ENVELOPES calibrated on set-03 (some
# self-flat-specific: corner_gain, stack noise%) — a new data class may
# WARN legitimately; revisit bounds there instead of ignoring the WARNs.
EXPECTATIONS = {
    "calibrated": {
        "bg_median16": (100, 1500, "sky level, offset subtracted"),
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
    },
    "stack": {
        "noise_over_median_pct": (1.2, 2.2, "G diff-MAD noise/median; reads ~25% above siril bgnoise (measured 1.84 == siril 1.46)"),
        "p2v_inner_rel": (None, 0.20, "radial flatness r<=0.85 (glow+MW still in: absolute flatness lands after subsky)"),
        "n_stars": (300, None, ""),
        "bg_median16": (150, 1500, "normalized stack level"),
    },
    "post_subsky": {
        "block_spread_over_noise": (None, 4.0, "(P95-P5 block medians)/bgnoise"),
        "ring_p2v16": (None, None, "info: rings in 16-bit counts"),
    },
    "post_denoise": {
        "bgnoise_ratio": (0.5, 0.75, "vs previous stage"),
        "star_delta_pct": (-10.0, None, "star count change"),
    },
    "post_stretch": {
        "bg_target_err8": (-6.0, 6.0, "bg median - target*255 (8-bit)"),
        "bg_cast8": (None, 3.0, "bg |R-G|,|B-G| (8-bit)"),
        "top100_peak8": (200.0, None, "star peaks (8-bit); below = washed out"),
    },
    "final": {
        "qa_pass": (1, None, "bg_qa gate (hard gate)"),
        "top100_peak8": (200.0, None, "star peaks (8-bit)"),
    },
}

ORDER = ["calibrated", "selfflat_median", "subsky_frame", "gain", "divided",
         "registration", "stack", "post_subsky", "post_denoise",
         "post_stretch", "final"]


def check(stage, metric, value):
    lo, hi, note = EXPECTATIONS[stage][metric]
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
        want_stars = stage not in ("gain",)
        data, m = measure_frame(p, want_stars=want_stars,
                                mask_branch=stage.startswith("post") or stage in ("stack", "final"))
        m["file"] = os.path.basename(p)
        per_frame.append(m)
        if i == rep_idx:
            rep = (data, m)
        else:
            del data
    data, mrep = rep
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

    if stage == "calibrated":
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
        nm = 100.0 * lev["bgnoise"] / max(lev["median"], 1e-9)
        checks.append(check(stage, "noise_over_median_pct", nm))
        checks.append(check(stage, "p2v_inner_rel", mrep["radial"].get("p2v_inner_rel")))
        checks.append(check(stage, "n_stars", mrep["stars"].get("n_stars", 0)))
        checks.append(check(stage, "bg_median16", lev["median"] * D16))
    elif stage == "post_subsky":
        # block spread on the subsky'd linear image, star-robust
        sub = data[:, ::2, ::2]
        h2, w2 = sub.shape[1:]
        gy, gx = h2 // 100, w2 // 100
        blocks = sub[g][:gy * 100, :gx * 100].reshape(gy, 100, gx, 100)
        bmed = np.median(blocks.transpose(0, 2, 1, 3).reshape(gy, gx, -1), axis=2)
        if am.CTX.foreground == "mask":   # block-level foreground fraction
            fg = am._fg_mask(h2, w2)[:gy * 100, :gx * 100] \
                .reshape(gy, 100, gx, 100).mean(axis=(1, 3))
            bm = fg <= 0.5
        elif am.CTX.foreground is not None:  # foreground rect (block centers)
            fx0, fy0, fx1, fy1 = am.CTX.foreground
            ys = (np.arange(gy) + 0.5) * 100 / h2
            xs = (np.arange(gx) + 0.5) * 100 / w2
            bm = ~(((ys[:, None] >= fy0) & (ys[:, None] < fy1))
                   & ((xs[None, :] >= fx0) & (xs[None, :] < fx1)))
        else:
            bm = np.ones((gy, gx), bool)
        vals = bmed[bm]
        spread = float(np.percentile(vals, 95) - np.percentile(vals, 5))
        checks.append(check(stage, "block_spread_over_noise",
                            spread / max(lev["bgnoise"], 1e-9)))
        rp = mrep["radial"].get("ring_p2v")
        checks.append(check(stage, "ring_p2v16", rp * D16 if rp is not None else None))
    elif stage == "post_denoise":
        pv = find_stage("post_subsky")
        if pv:
            pn = pv["per_frame"][0]["levels"][g]["bgnoise"]
            checks.append(check(stage, "bgnoise_ratio", lev["bgnoise"] / max(pn, 1e-12)))
            ps = pv["per_frame"][0]["stars"].get("n_stars", 0)
            ns = mrep["stars"].get("n_stars", 0)
            if ps:
                checks.append(check(stage, "star_delta_pct", 100.0 * (ns - ps) / ps))
    elif stage == "post_stretch":
        target = args.target if args.target is not None else 0.12
        checks.append(check(stage, "bg_target_err8", lev["median"] * 255.0 - target * 255.0))
        meds = [l["median"] * 255.0 for l in mrep["levels"]]
        cast = max(abs(meds[0] - meds[g]), abs(meds[-1] - meds[g])) if len(meds) == 3 else 0.0
        checks.append(check(stage, "bg_cast8", cast))
        tp = mrep["stars"].get("top100_peak_med")
        checks.append(check(stage, "top100_peak8", tp * 255.0 if tp is not None else None))
    elif stage == "final":
        from PIL import Image
        a = np.asarray(Image.open(args.inputs[rep_idx]), dtype=np.float64)
        qa = bg_qa.qa_metrics(a)
        checks.append(check(stage, "qa_pass", 1 if qa["pass"] else 0))
        tp = mrep["stars"].get("top100_peak_med")
        checks.append(check(stage, "top100_peak8", tp * 255.0 if tp is not None else None))
        mrep["qa"] = {k: v for k, v in qa.items()
                      if isinstance(v, (int, float, bool))}

    entry = {"stage": stage, "label": args.label, "inputs": args.inputs,
             "panel": os.path.basename(base + ".jpg"),
             "radial_png": os.path.basename(base + "_radial.png"),
             "panel_note": panel_note, "checks": checks,
             "per_frame": [{k: v for k, v in m.items() if k not in ("centers", "profile")}
                           for m in per_frame],
             "centers": mrep["centers"], "profile": mrep["profile"]}
    emit(d, entry)


def parse_seq_shifts(seqfile):
    """Best-effort: pull per-frame translation from siril .seq regdata
    (9-float homography rows). Returns list of (dx, dy) or None."""
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


def handle_reg(args):
    d = args.dir
    os.makedirs(d, exist_ok=True)
    frac = args.registered / max(args.total, 1)
    checks = [check("registration", "reg_fraction", frac)]
    entry = {"stage": "registration", "label": None,
             "inputs": [], "checks": checks,
             "registered": args.registered, "total": args.total,
             "ref": args.ref, "sweep": args.sweep}
    if args.seq and os.path.exists(args.seq):
        sh = parse_seq_shifts(args.seq)
        if sh:
            dx = [s[0] for s in sh]
            dy = [s[1] for s in sh]
            entry["shift_range_px"] = [round(max(dx) - min(dx), 1),
                                       round(max(dy) - min(dy), 1)]
    emit(d, entry)


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
            info = (f"registered {e['registered']}/{e['total']} @ ref {e['ref']}"
                    + (f", sweep {e['sweep']}" if e.get("sweep") else "")
                    + (f", shift range {e.get('shift_range_px')} px"
                       if e.get("shift_range_px") else ""))
            html.append(f"<p>{info}</p>")
            md.append(info)
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
    s.add_argument("--target", type=float, default=None,
                   help="autostretch bg target (post_stretch check)")
    r = sub.add_parser("reg", parents=[ctxp])
    r.add_argument("--dir", required=True)
    r.add_argument("--registered", type=int, required=True)
    r.add_argument("--total", type=int, required=True)
    r.add_argument("--ref", type=int, required=True)
    r.add_argument("--sweep", default=None)
    r.add_argument("--seq", default=None)
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
    else:
        handle_report(args)


if __name__ == "__main__":
    main()
