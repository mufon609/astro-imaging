#!/usr/bin/env python3
"""jwst-jupiter CLOSE-UP render: per-exposure-derotated channels -> combine
-> placed-points transfers -> straight 3-filter chromatic palette -> PNG16.

Stages (Siril owns every deliverable pixel op):
1. COMBINE per channel: the derotated frames and their coverage masks
   (work/j3derot/, from derotate_exposures.py) are staged per channel and
   summed with Siril stack; the channel master = pm sum/(cov+eps). This is
   the coverage-aware mean — frames cover different tiles, a plain mean
   would dilute by zeros.
2. MEASURE: Siril stat boxes on each master (sky corner, disc center,
   aurora pole) — the placed-point inputs, recorded.
3. TRANSFER per channel: pm asinh placed-points asinh(S*(x-B)/(W-B))/asinh(S)
   (probe-verified exact), B = sky pedestal - 2 sigma, W = the measured disc
   white per channel, S = one shared bracketed knob.
4. PALETTE: straight chromatic R=F360M, G=F212N, B=F150W2xF164N (the
   documented 3-filter default; the reference family's own mapping) via
   rgbcomp; savepng = the single 16-bit hop.

Knobs surface as CLI args; every measured value and constant lands in
datasets/<session>/qa_work/j3_render_<tag>.json.
"""
import argparse
import glob
import json
import math
import os
import re
import subprocess
import sys

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SIRIL = ["flatpak", "run", "--command=siril-cli", "org.siril.Siril"]
SESS = os.path.join(REPO, "sessions", "jwst-jupiter")
WORK = os.path.join(SESS, "work")
DR = os.path.join(WORK, "j3derot")
DS = os.path.join(REPO, "datasets", "jwst-jupiter", "qa_work")
RES_REL = "../../../web/results/jwst-jupiter"

CHANNELS = {"f360m": "jw01373006001_03102_0000?_nrcblong",
            "f212n": "jw01373008001_03101_0000?_nrcb3",
            "f150w2": "jw01373006001_03102_0000?_nrcb[1-4]"}


def fnum(v):
    s = f"{v:.9f}".rstrip("0")
    return s + "0" if s.endswith(".") else s


def sub(tok, v):
    return f"({tok} - {fnum(v)})" if v >= 0 else f"({tok} + {fnum(-v)})"


def run_siril(ssf_name, lines):
    path = os.path.join(WORK, ssf_name)
    with open(path, "w") as f:
        f.write("requires 1.4.0\nsetcompress 0\nset32bits\n" + "\n".join(lines) + "\nclose\n")
    r = subprocess.run(SIRIL + ["-d", SESS, "-s", path], capture_output=True, text=True)
    if r.returncode != 0:
        sys.exit(f"siril failed for {ssf_name}:\n" + "\n".join(r.stdout.splitlines()[-15:]))
    return r.stdout


def stat_triplets(out):
    """parse 'B&W layer: Mean: x, Median: y, Sigma: z, ...' lines -> list of dicts"""
    rows = []
    for m in re.finditer(r"B&W layer: Mean: ([-\d.e+]+), Median: ([-\d.e+]+), Sigma: ([-\d.e+]+),"
                         r" Min: ([-\d.e+]+), Max: ([-\d.e+]+)", out):
        rows.append({k: float(v) / 65535.0 for k, v in
                     zip(("mean", "median", "sigma", "min", "max"), m.groups())})
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tag", default="cu1")
    ap.add_argument("--s-values", default="2,6", help="shared asinh strength bracket")
    ap.add_argument("--gains", default="1,1,1", help="post-transfer channel gains r,g,b")
    ap.add_argument("--sky-floor", type=float, default=None)
    ap.add_argument("--skip-combine", action="store_true", help="channel masters already built")
    args = ap.parse_args()

    os.makedirs(os.path.join(REPO, "web", "results", "jwst-jupiter", "judge"), exist_ok=True)
    os.makedirs(os.path.join(REPO, "web", "results", "jwst-jupiter", "previews"), exist_ok=True)

    # ---- 1. combine per channel (Siril stack sum / coverage sum) ----
    if not args.skip_combine:
        for chan, pat in CHANNELS.items():
            frames = sorted(glob.glob(os.path.join(DR, pat + "_dr.fits")))
            covs = sorted(glob.glob(os.path.join(DR, pat + "_cov.fits")))
            if not frames:
                sys.exit(f"no derotated frames for {chan} ({pat})")
            for kind, files in (("img", frames), ("cov", covs)):
                d = os.path.join(WORK, f"stk_{chan}_{kind}")
                os.makedirs(d, exist_ok=True)
                for f in files:
                    os.link(f, os.path.join(d, os.path.basename(f))) \
                        if not os.path.exists(os.path.join(d, os.path.basename(f))) else None
            print(f"{chan}: {len(frames)} frames", flush=True)
            run_siril(f"j3_stk_{chan}.ssf", [
                f"cd work/stk_{chan}_img", f"convert {chan}i -out=.", f"stack {chan}i sum -nonorm",
                f"load {chan}i_stacked", f"save ../m_{chan}_sum",
                f"cd ../stk_{chan}_cov", f"convert {chan}c -out=.", f"stack {chan}c sum -nonorm",
                f"load {chan}c_stacked", f"save ../m_{chan}_cov",
                "cd ..",
                f'pm "$m_{chan}_sum$ / max($m_{chan}_cov$, 0.02)"',
                f"save m_{chan}",
            ])

    # ---- 2. measure: masters + reference anchors ----
    # boxes on the o006 F150W2 grid (1631x1641, Siril y-flip): disc center,
    # sky corner, aurora pole (poles lie along the equator-perpendicular; from
    # the component previews the aurora arcs sit at the LEFT/RIGHT limbs)
    H = 1631
    boxes = {"sky": (30, H - 230 - 30, 200, 230),
             "disc": (620, H - 1020, 400, 400),
             "pole": (60, H - 900, 160, 300)}
    out = run_siril("j3_measure.ssf", sum((
        [f"cd work", f"load m_{chan}"] +
        sum(([f"boxselect {x} {y} {w} {h}", "stat main"] for x, y, w, h in
             (boxes["sky"], boxes["disc"], boxes["pole"])), [])
        for chan in ("f360m", "f212n", "f150w2")), []))
    rows = stat_triplets(out)
    if len(rows) != 9:
        sys.exit(f"measure parse: expected 9 stat rows, got {len(rows)}")
    levels = {}
    for i, chan in enumerate(("f360m", "f212n", "f150w2")):
        sky, disc, pole = rows[3 * i], rows[3 * i + 1], rows[3 * i + 2]
        levels[chan] = {"sky": sky, "disc": disc, "pole": pole}
        print(f"{chan}: sky {sky['median']:.5g} disc_med {disc['median']:.5g} "
              f"disc_max {disc['max']:.5g} pole_max {pole['max']:.5g}", flush=True)

    # ---- 3+4. transfers + chromatic composite, one file per S arm ----
    gains = [float(g) for g in args.gains.split(",")]
    outputs = []
    for S in (float(s) for s in args.s_values.split(",")):
        tag = f"{args.tag}_s{int(S)}"
        norm = math.asinh(S)
        lines = ["cd work"]
        for chan, gain in zip(("f360m", "f212n", "f150w2"), gains):
            lv = levels[chan]
            B = lv["sky"]["median"] - 2 * lv["sky"]["sigma"]
            W = max(lv["disc"]["max"], lv["pole"]["max"])   # disc white incl. aurora tops
            expr = (f'asinh({fnum(S)} * max({sub(f"$m_{chan}$", B)} / {fnum(W - B)}, 0)) '
                    f'/ {fnum(norm)}')
            if gain != 1.0:
                expr = f"({expr}) * {fnum(gain)}"
            if args.sky_floor:
                expr = f"(({expr}) + {fnum(args.sky_floor)}) / {fnum(1 + args.sky_floor)}"
            lines += [f'pm "min({expr}, 1)"', f"save t_{chan}_{tag}"]
            levels[chan][f"transfer_{tag}"] = {"B": B, "W": W, "S": S, "gain": gain}
        lines += [
            f"rgbcomp t_f360m_{tag} t_f212n_{tag} t_f150w2_{tag} -out={RES_REL}/cu_{tag}",
            f"load {RES_REL}/cu_{tag}",
            f"savepng {RES_REL}/judge/closeup_{tag}",
            "resample -width=800 -interp=area",
            f"savepng {RES_REL}/previews/cu_{tag}_small",
        ]
        run_siril(f"j3_render_{tag}.ssf", lines)
        outputs.append(f"web/results/jwst-jupiter/judge/closeup_{tag}.png")
        print(f"rendered {tag}", flush=True)

    rec = {"render": "j3 close-up — per-exposure-derotated masters, placed-points transfers, straight chromatic palette (R=F360M G=F212N B=F150W2xF164N)",
           "levels_and_transfers": levels, "gains": gains, "sky_floor": args.sky_floor,
           "outputs": outputs}
    json.dump(rec, open(os.path.join(DS, f"j3_render_{args.tag}.json"), "w"), indent=1)
    print("->", f"j3_render_{args.tag}.json;", "judge:", ", ".join(outputs))


if __name__ == "__main__":
    main()
