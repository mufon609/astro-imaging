#!/usr/bin/env python3
"""Controlled single-variable experiment harness for the post chain.

One parameter, a bracketed value list, a written hypothesis — reruns ONLY
the affected ops from a pinned input, emits per-value previews + a metric
table + side-by-side crops, then STOPS for user judgment. It never edits
the recipe templates.

Usage:
  experiment.py <session> <set> --param P --values a,b,c --hypothesis "..."
                [--chain baseline|candidate] [--name tag]

Params (op it belongs to):
  graxpert        off|on              (GraXpert AI background extraction)
  subsky          siril subsky arg: "1", "2", "-rbf -samples=30 ..."
  denoise         off|vst|vst_after_stretch
  stretch_sigma   autostretch shadow-clip sigma (e.g. -2.8,-2.0,-1.5)
  stretch_target  autostretch background target (e.g. 0.07,0.12,0.15)
  stretch_linked  linked|unlinked
  satu            off or amount (0.2,0.3)
  crop            edge margin px (0 = full frame)
  jpgq            JPEG quality (85,92,98)

Chains (the fixed context the knob varies inside) — LEGACY quicklook
post-chains for stage debugging only; the approved product recipe is B7
in starcomb.py, not any chain here:
  baseline   = subsky RBF(30/3/0.15) -> denoise vst ->
               autostretch linked -2.0 0.12 -> crop 150 -> jpg 92
  candidate  = graxpert -> subsky 2 ->
               autostretch unlinked -1.5 0.07 -> satu 0.2 -> crop 250 -> jpg 92

Numeric values must bracket the chain's current value; the current value is
auto-added to the list if missing (every ladder includes its control).
Everything lands in <session>/results/exp_<set>_<param>[_<name>]_<stamp>/.
"""
import argparse
import json
import os
import shlex
import subprocess
import sys
import time

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
import bg_qa  # noqa: E402

GRAXPERT = os.path.expanduser("~/.local/bin/graxpert")

CHAINS = {
    "baseline": {
        "graxpert": "off",
        "subsky": "-rbf -samples=30 -tolerance=3 -smooth=0.15",
        "denoise": "vst",
        "stretch_sigma": -2.0,
        "stretch_target": 0.12,
        "stretch_linked": "linked",
        "satu": "off",
        "crop": 150,
        "jpgq": 92,
    },
    "candidate": {
        "graxpert": "on",
        "subsky": "2",
        "denoise": "off",
        "stretch_sigma": -1.5,
        "stretch_target": 0.07,
        "stretch_linked": "unlinked",
        "satu": 0.2,
        "crop": 250,
        "jpgq": 92,
    },
    # candidate with a star-recovering stretch target: 0.12 restores
    # baseline-level star peaks (sat 13%/mid 255 vs baseline 12/254).
    "candidate_bright": {
        "graxpert": "on",
        "subsky": "2",
        "denoise": "off",
        "stretch_sigma": -1.5,
        "stretch_target": 0.12,
        "stretch_linked": "unlinked",
        "satu": 0.2,
        "crop": 250,
        "jpgq": 92,
    },
    # Full-frame QA PASS: gx -> subsky 1 -> unlinked -1.5 0.07 -> satu 0.2
    # -> NO crop. (higher subsky degrees overfit per channel and re-create
    # the color failure: deg1 |B-G| 6 PASS, deg2 8, deg3 9)
    "fullframe_v5": {
        "graxpert": "on",
        "subsky": "1",
        "denoise": "off",
        "stretch_sigma": -1.5,
        "stretch_target": 0.07,
        "stretch_linked": "unlinked",
        "satu": 0.2,
        "crop": 0,
        "jpgq": 92,
    },
    # candidate at FULL FRAME (crop 0): the rim rings pass here; the open
    # item is large-scale B-G.
    "candidate_full": {
        "graxpert": "on",
        "subsky": "2",
        "denoise": "off",
        "stretch_sigma": -1.5,
        "stretch_target": 0.07,
        "stretch_linked": "unlinked",
        "satu": 0.2,
        "crop": 0,
        "jpgq": 92,
    },
}

# op order in the chain; each param belongs to one op
OP_OF_PARAM = {
    "graxpert": "graxpert",
    "subsky": "subsky",
    "denoise": "denoise",
    "stretch_sigma": "stretch",
    "stretch_target": "stretch",
    "stretch_linked": "stretch",
    "satu": "satu",
    "crop": "crop",
    "jpgq": "jpg",
}
NUMERIC = {"stretch_sigma", "stretch_target", "satu", "crop", "jpgq"}


def op_order(chain):
    ops = []
    if chain["graxpert"] != "off":
        ops.append("graxpert")
    ops.append("subsky")
    if chain["denoise"] == "vst":
        ops.append("denoise")
    ops.append("stretch")
    if chain["denoise"] == "vst_after_stretch":
        ops.append("denoise_post")
    if chain["satu"] != "off":
        ops.append("satu")
    if int(chain["crop"]) > 0:
        ops.append("crop")
    ops.append("jpg")
    return ops


def op_lines(op, chain, dims, jpg_name):
    """Siril script lines for one op (cwd = results/)."""
    w, h = dims
    m = int(chain["crop"])
    if op == "subsky":
        return [f"subsky {chain['subsky']} -dither"]
    if op == "denoise" or op == "denoise_post":
        return ["denoise -vst"]
    if op == "stretch":
        link = "-linked" if chain["stretch_linked"] == "linked" else ""
        return [f"autostretch {link} {chain['stretch_sigma']} "
                f"{chain['stretch_target']}".replace("  ", " ")]
    if op == "satu":
        return [f"satu {chain['satu']}"]
    if op == "crop":
        return [f"crop {m} {m} {w - 2 * m} {h - 2 * m}"]
    if op == "jpg":
        return [f"savejpg {jpg_name} {int(chain['jpgq'])}"]
    raise KeyError(op)


def run_siril(session_dir, script_path):
    r = subprocess.run(
        ["flatpak", "run", "--command=siril-cli", "org.siril.Siril",
         "-d", session_dir, "-s", script_path],
        capture_output=True, text=True)
    if r.returncode != 0:
        sys.exit(f"experiment: siril failed on {script_path}:\n"
                 + r.stdout[-3000:] + r.stderr[-2000:])
    return r.stdout


def run_graxpert(stack_fit, work, log):
    """GraXpert AI background extraction on the pinned stack, cached by
    input identity (mtime+size) so ladders reuse it."""
    st = os.stat(stack_fit)
    key = f"gx_{st.st_size}_{int(st.st_mtime)}"
    out = os.path.join(work, f"{key}.fits")
    if os.path.exists(out):
        log(f"graxpert: cache hit {os.path.basename(out)}")
        return out
    log("graxpert: running background-extraction (first run downloads the "
        "AI model; takes minutes on this box)")
    r = subprocess.run([GRAXPERT, "-cmd", "background-extraction",
                        stack_fit, "-output", out[:-5], "-gpu", "false"],
                       capture_output=True, text=True)
    if not os.path.exists(out):
        sys.exit("experiment: graxpert produced no output:\n"
                 + r.stdout[-3000:] + "\n" + r.stderr[-2000:])
    return out


def sanitize(v):
    return str(v).replace(" ", "").replace("/", "_").replace("=", "") \
        .replace("-", "m").replace(".", "p")[:40]


def measure_jpg(path):
    from PIL import Image
    a8 = np.asarray(Image.open(path), dtype=np.float64)
    qa = bg_qa.qa_metrics(a8)
    data = (a8.transpose(2, 0, 1) / 255.0).astype(np.float32)
    stars = am.star_metrics(data[1])
    lev = am.channel_levels(data)
    return qa, stars, lev


def star_region(stack_path):
    """Pick a deterministic star-rich 1:1 crop region from the pinned stack
    (brightest measured star nearest the frame center, branch excluded).
    Returns (x0, y0) of a 700x450 rect in stack display coords."""
    data, _ = am.load_image(stack_path)
    g = data[min(1, data.shape[0] - 1)]
    h, w = g.shape
    from scipy import ndimage
    bg, sig = am.bg_stats(g)
    mx = ndimage.maximum_filter(g, size=9, mode="nearest")
    cand = (g >= mx) & (g > bg + 25 * sig)
    cand[:100] = cand[-100:] = False
    cand[:, :100] = cand[:, -100:] = False
    cand &= am.branch_mask(h, w)
    ys, xs = np.nonzero(cand)
    if len(ys) == 0:
        return (w // 2 - 350, h // 2 - 225)
    d2 = (ys - h / 2) ** 2 + (xs - w / 2) ** 2
    order = np.argsort(g[ys, xs])[::-1][:30]     # 30 brightest
    best = order[np.argmin(d2[order])]           # nearest center among them
    x0 = int(np.clip(xs[best] - 350, 0, w - 700))
    y0 = int(np.clip(ys[best] - 225, 0, h - 450))
    return (x0, y0)


def compose_rows(rows, labels, out_path):
    """Stack per-value rows (already same width) with a text label bar."""
    from PIL import Image, ImageDraw
    parts = []
    for lab, row in zip(labels, rows):
        bar = Image.new("RGB", (row.width, 26), (18, 18, 18))
        d = ImageDraw.Draw(bar)
        d.text((8, 6), lab, fill=(230, 230, 230))
        parts += [bar, row]
    wmax = max(p.width for p in parts)
    total_h = sum(p.height for p in parts)
    canvas = Image.new("RGB", (wmax, total_h), (24, 24, 24))
    y = 0
    for p in parts:
        canvas.paste(p, (0, y))
        y += p.height
    canvas.save(out_path, quality=88)


def value_row(jpg_path, crop_margin, star_xy, thumb_div=6):
    """One comparison row for a value: full thumb | star crop | corner crop.
    star_xy is in STACK coords; the jpg may be cropped by crop_margin."""
    from PIL import Image
    im = Image.open(jpg_path)
    w, h = im.size
    th = im.resize((w // thumb_div, h // thumb_div), Image.LANCZOS)
    sx = star_xy[0] - crop_margin
    sy = star_xy[1] - crop_margin
    sx = max(0, min(sx, w - 700))
    sy = max(0, min(sy, h - 450))
    star = im.crop((sx, sy, sx + 700, sy + 450))
    corner = im.crop((w - 760, 60, w - 60, 510))
    gutter = 10
    hrow = max(th.height, 450)
    row = Image.new("RGB", (th.width + 700 + 700 + 2 * gutter, hrow), (24, 24, 24))
    row.paste(th, (0, 0))
    row.paste(star, (th.width + gutter, 0))
    row.paste(corner, (th.width + 700 + 2 * gutter, 0))
    return row


def fmt(v, spec="{:.2f}"):
    return "" if v is None else spec.format(v)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("session")
    ap.add_argument("set")
    ap.add_argument("--param", required=True, choices=sorted(OP_OF_PARAM))
    ap.add_argument("--values", required=True,
                    help="comma-separated; numeric ladders must bracket the "
                         "chain's current value")
    ap.add_argument("--hypothesis", required=True,
                    help="'changing X should affect Y because Z'")
    ap.add_argument("--chain", default="baseline", choices=sorted(CHAINS))
    ap.add_argument("--name", default=None, help="tag for the output dir")
    ap.add_argument("--allow-unbracketed", action="store_true")
    args = ap.parse_args()

    repo = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    sdir = os.path.join(repo, args.session)
    stack = os.path.join(sdir, "results", f"stack_{args.set}.fit")
    if not os.path.exists(stack):
        sys.exit(f"experiment: no pinned input {stack} — run the pipeline first")
    work = os.path.join(sdir, "work")
    os.makedirs(os.path.join(sdir, "results"), exist_ok=True)

    chain = dict(CHAINS[args.chain])
    cur = chain[args.param]

    def parse_v(s):
        s = s.strip()
        if args.param in NUMERIC:
            if s == "off":
                return "off"
            return float(s) if "." in s or "e" in s or args.param in (
                "stretch_sigma", "stretch_target") else int(s)
        return s

    values = [parse_v(v) for v in args.values.split(",")]
    if cur not in values:
        values.append(cur)
        print(f"[exp] control value {cur!r} added to the ladder "
              f"(every ladder includes the chain's current value)")
    if args.param in NUMERIC:
        nums = [0.0 if v == "off" else float(v) for v in values]
        curn = 0.0 if cur == "off" else float(cur)
        if not (min(nums) <= curn <= max(nums)) and not args.allow_unbracketed:
            sys.exit(f"experiment: values {values} do not bracket the current "
                     f"value {cur} — bracket it or pass --allow-unbracketed")
        values = [v for _, v in sorted(zip(nums, values))]

    stamp = time.strftime("%Y%m%d_%H%M%S")
    tag = f"_{args.name}" if args.name else ""
    exp = os.path.join(sdir, "results",
                       f"exp_{args.set}_{args.param}{tag}_{stamp}")
    os.makedirs(exp, exist_ok=True)

    def log(msg):
        print(f"[exp] {msg}", flush=True)

    st = os.stat(stack)
    with open(os.path.join(exp, "hypothesis.md"), "w") as f:
        f.write(f"# Experiment: {args.param} @ {args.set} ({args.chain} chain)\n\n"
                f"- **hypothesis**: {args.hypothesis}\n"
                f"- **param**: `{args.param}` values {values} "
                f"(control = {cur!r})\n"
                f"- **chain**: {args.chain} = `{CHAINS[args.chain]}`\n"
                f"- **pinned input**: `{stack}` "
                f"(size {st.st_size}, mtime {int(st.st_mtime)})\n"
                f"- **date**: {stamp}\n\n"
                "Verdict: PENDING USER JUDGMENT\n")

    dims = am.fits_dims(stack)
    ops = op_order(chain)
    varied_op = OP_OF_PARAM[args.param]
    # ops present only when enabled: varying such a param (satu off->0.3,
    # graxpert off->on, denoise off->vst) changes the op list per value, so
    # the shared prefix must stop BEFORE where that op sits in ANY variant.
    chains = []
    for v in values:
        c = dict(chain)
        c[args.param] = v
        chains.append(c)
    orders = [op_order(c) for c in chains]
    # longest common prefix of op lists, then trim at the varied op if it
    # appears (a param value can also change the op's own line)
    common = []
    for i in range(min(len(o) for o in orders)):
        opset = {o[i] for o in orders}
        if len(opset) != 1 or opset == {varied_op} \
           or (varied_op == "stretch" and opset == {"stretch"} and args.param.startswith("stretch")):
            break
        op = orders[0][i]
        if op == varied_op:
            break
        common.append(op)
    # graxpert runs outside siril and is cached on its own; keep it out of
    # the siril prefix script
    siril_prefix = [o for o in common if o != "graxpert"]

    pinned = stack
    rel_pinned = f"stack_{args.set}"
    if "graxpert" in common:
        gx = run_graxpert(stack, work, log)
        pinned = gx
        rel_pinned = os.path.relpath(gx, os.path.join(sdir, "results"))
        if rel_pinned.endswith(".fits"):
            rel_pinned = rel_pinned[:-5]

    prefix_load = rel_pinned
    if siril_prefix:
        lines = ["requires 1.4.0", "cd results", f"load {rel_pinned}"]
        for op in siril_prefix:
            lines += op_lines(op, chain, dims, "unused")
        lines += ["save ../work/exp_prefix", "close"]
        sp = os.path.join(work, "exp_prefix.gen.ssf")
        with open(sp, "w") as f:
            f.write("\n".join(lines) + "\n")
        log(f"prefix ops {siril_prefix} -> work/exp_prefix.fit (runs once)")
        run_siril(sdir, sp)
        prefix_load = "../work/exp_prefix"

    results = []
    for i, (v, c) in enumerate(zip(values, chains)):
        vops = op_order(c)
        rest = vops[len(common):]
        jpg_base = f"v{i}_{sanitize(v)}"
        lines = ["requires 1.4.0", "cd results", f"load {prefix_load}"]
        # graxpert runs outside siril: when it is part of this value's op
        # list (only legal as the first op, i.e. empty common prefix), run
        # it now (cached) and load its output instead of the pinned stack.
        if "graxpert" in rest:
            if rest[0] != "graxpert" or prefix_load != rel_pinned:
                sys.exit("experiment: graxpert is only supported as the "
                         "first op of the chain")
            gx = run_graxpert(stack, work, log)
            rel = os.path.relpath(gx, os.path.join(sdir, "results"))
            lines[2] = "load " + (rel[:-5] if rel.endswith(".fits") else rel)
            rest = rest[1:]
        for op in rest:
            lines += op_lines(op, c, dims, jpg_base)
        lines += ["close"]
        sp = os.path.join(work, f"exp_value_{i}.gen.ssf")
        with open(sp, "w") as f:
            f.write("\n".join(lines) + "\n")
        log(f"value {v!r}: ops {rest}")
        run_siril(sdir, sp)
        src = os.path.join(sdir, "results", jpg_base + ".jpg")
        dst = os.path.join(exp, jpg_base + ".jpg")
        os.replace(src, dst)
        qa, stars, lev = measure_jpg(dst)
        results.append({"value": v, "jpg": os.path.basename(dst),
                        "qa": {k: val for k, val in qa.items()
                               if isinstance(val, (int, float, bool))},
                        "stars": stars,
                        "bg_med8": lev[1]["median"] * 255.0,
                        "crop": int(c["crop"])})
        log(f"  QA {'PASS' if qa['pass'] else 'FAIL'} blocks {qa['ratio']:.2f} "
            f"rings {qa['ring_l']:.1f}/{qa['ring_rg']:.1f}/{qa['ring_bg']:.1f} "
            f"| stars mid-peak {stars.get('mid_peak_med', 0) * 255:.0f} "
            f"sat {stars.get('sat_star_frac', 0) * 100:.0f}% "
            f"fwhm {fmt(stars.get('fwhm_med'), '{:.1f}')}")

    with open(os.path.join(exp, "metrics.jsonl"), "w") as f:
        for r in results:
            f.write(json.dumps(r) + "\n")

    # ---- metric table -----------------------------------------------------
    cols = ["value", "QA", "blocks", "|R-G|", "ring L", "ring RG", "ring BG",
            "bg med", "stars", "FWHM", "top100", "mid pk", "sat%", "halo",
            "contrast"]
    rows_txt = []
    for r in results:
        q, s = r["qa"], r["stars"]
        rows_txt.append([
            str(r["value"]), "PASS" if q["pass"] else "FAIL",
            f"{q['ratio']:.2f}", f"{max(q['worst_rg'], q['worst_bg']):.1f}",
            f"{q['ring_l']:.1f}", f"{q['ring_rg']:.1f}", f"{q['ring_bg']:.1f}",
            f"{r['bg_med8']:.0f}", str(s.get("n_stars", 0)),
            fmt(s.get("fwhm_med"), "{:.1f}"),
            fmt((s.get("top100_peak_med") or 0) * 255, "{:.0f}"),
            fmt((s.get("mid_peak_med") or 0) * 255, "{:.0f}"),
            fmt((s.get("sat_star_frac") or 0) * 100, "{:.0f}"),
            fmt(s.get("halo_med")), fmt((s.get("contrast_med") or 0) * 255, "{:.0f}")])
    widths = [max(len(c), *(len(r[j]) for r in rows_txt))
              for j, c in enumerate(cols)]
    header = "  ".join(c.ljust(widths[j]) for j, c in enumerate(cols))
    sep = "-" * len(header)
    table = [header, sep] + ["  ".join(r[j].ljust(widths[j])
                                       for j in range(len(cols)))
                             for r in rows_txt]
    md = ["| " + " | ".join(cols) + " |",
          "|" + "|".join("---" for _ in cols) + "|"]
    md += ["| " + " | ".join(r) + " |" for r in rows_txt]
    with open(os.path.join(exp, "hypothesis.md"), "a") as f:
        f.write("\n## Results\n\n" + "\n".join(md) + "\n")
    print()
    print("\n".join(table))

    # ---- side-by-side strips ----------------------------------------------
    sx = star_region(stack)
    rows = [value_row(os.path.join(exp, r["jpg"]), r["crop"], sx)
            for r in results]
    labels = [f"{args.param} = {r['value']}   "
              f"[{'PASS' if r['qa']['pass'] else 'FAIL'}]  "
              f"(full | star field 1:1 @ {sx} | top-right corner 1:1)"
              for r in results]
    compose_rows(rows, labels, os.path.join(exp, "side_by_side.jpg"))
    log(f"side-by-side: {os.path.join(exp, 'side_by_side.jpg')}")

    for i in range(len(values)):
        p = os.path.join(work, f"exp_value_{i}.gen.ssf")
        if os.path.exists(p):
            os.remove(p)
    for f_ in ("exp_prefix.fit", "exp_prefix.gen.ssf"):
        p = os.path.join(work, f_)
        if os.path.exists(p):
            os.remove(p)

    print(f"\n[exp] STOP — user judgment required. Review {exp}/ "
          "(side_by_side.jpg, per-value JPEGs, hypothesis.md) before any "
          "recipe change.")


if __name__ == "__main__":
    main()
