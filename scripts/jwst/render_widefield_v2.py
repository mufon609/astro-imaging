#!/usr/bin/env python3
"""jwst-jupiter wide-field render: the documented original process expressed
in the sanctioned toolset (Siril pm/mtf/gauss/rgbcomp/savepng do every pixel op).

Mechanism set (research + measurement records, all tracked):
- Per-filter PLACED-POINTS transfers (docs/jwst-official-rendering-process.md):
  each filter gets the team's documented two-transfer split (the Neptune
  doctrine — separate stretches composited; the L3-faithful form of the
  wide-field caption's "combination of short and long exposures"):
  * DISC arm: LINEAR, black at the measured background pedestal, white at the
    filter's own measured disc-box max — puts both filters' GRS/EZ tops at
    1.0, the captions' "Great Red Spot ... appears white" anchor.
  * DEEP arm: asinh placed-points pm transfer asinh(S*(x-B)/(W-B))/asinh(S)
    (probe-verified exact: qa_work/j2_v2_stretch_probe.json), black at
    pedestal - 2*sigma (sky noise straddles the pedestal), white at a
    field-anchored level (decouple it from the feather top via --w212-deep,
    or the R deep arm saturates across the outer feather = the measured
    orange-rim mechanism).
- HDR composite: feathered value-keyed weight on the (gap-filled) F212N prep,
  ramp across the measured ring-max -> disc-min value gap — the headless
  equivalent of the documented Photoshop masked composite. One shared
  geometric weight for both filters (the F212N disc is hole-free).
- FINISHING (the documented per-layer curves stage, headless): --m335 warms
  the disc (midtone-only MTF on the F335M disc arm — endpoints fixed so the
  GRS/EZ white anchor survives), --m-disc lifts both disc arms to the
  reference disc brightness, --sky-floor applies the neutral
  slightly-above-black lift (x+f)/(1+f) to all three channels. Knob values
  are SOLVED from tool-measured anchors (qa_work/j2_v3_anchors.json), not
  hand-tuned.
- Palette: channel isolation + pseudogreen (R=F212N, G=half each, B=F335M) —
  Schmidt's documented JWST mechanism.
- FILLS (policy toggles, documented mechanisms, BEFORE transfers): --gap-fill
  (F212N chip gaps <- F335M, prep level); --crescent-fill (F335M saturation
  NaN -> white at display level, in-disc); --feather-crescent blurs the fill
  mask with Siril gauss so the fill edge is not a zero-mask staircase.
- --measure: Siril stat on the recorded disc/sky boxes of each composite —
  the rung verdict numbers.

Constants come from datasets/<session>/qa_work/j2_v2_levels.json. Outputs:
per-stage FITS in the session work dir, finals + full-frame PNG16 judge
surfaces + 800px previews under web/results/<session>/. Run record:
qa_work/<tag>_run.json.
"""
import argparse
import json
import math
import os
import subprocess
import sys

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SIRIL = ["flatpak", "run", "--command=siril-cli", "org.siril.Siril"]


def fnum(v):
    """pm-safe literal: fixed-point, no scientific notation (unprobed in pm)."""
    s = f"{v:.9f}".rstrip("0")
    return s + "0" if s.endswith(".") else s


def sub(tok, v):
    """pm-safe '(tok - v)' — folds a negative v into '+' (no unary-minus chains)."""
    return f"({tok} - {fnum(v)})" if v >= 0 else f"({tok} + {fnum(-v)})"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--session", default="jwst-jupiter")
    ap.add_argument("--tag", default="v2", help="output family name (wf_<tag>_sN)")
    ap.add_argument("--s-values", default="5,15",
                    help="deep-arm asinh strength bracket (comma-separated)")
    ap.add_argument("--gap-fill", action="store_true",
                    help="fill F212N chip gaps from F335M (documented team mechanism)")
    ap.add_argument("--crescent-fill", action="store_true",
                    help="white-fill F335M saturation crescents in-disc (pixel-clip equivalent)")
    ap.add_argument("--feather-crescent", type=float, default=None, metavar="PX",
                    help="gauss-blur the crescent fill mask by PX (kills the zero-mask staircase)")
    ap.add_argument("--w212-deep", type=float, default=None,
                    help="F212N deep-arm white point (default: the feather top — known rim mechanism)")
    ap.add_argument("--w212-disc", type=float, default=None,
                    help="F212N disc-arm white point override (EZ-top anchor; default: disc-box max)")
    ap.add_argument("--m335", type=float, default=None,
                    help="midtone MTF on the F335M disc arm (warms the disc; endpoints fixed)")
    ap.add_argument("--m-disc", type=float, default=None,
                    help="midtone MTF on BOTH disc arms after --m335 (disc brightness to reference)")
    ap.add_argument("--m-disc-212", type=float, default=None,
                    help="midtone MTF on the F212N disc arm ONLY (colorize-palette form: disc brightness is F212N's job)")
    ap.add_argument("--colorize-a", type=float, default=None, metavar="A",
                    help="palette = documented colorize: c212 = A*(1,0.93,0.90), c335 = 1-c212, additive sum-to-white (supersedes channel isolation + pseudogreen)")
    ap.add_argument("--hue-purity", type=float, default=0.0, metavar="P",
                    help="interpolate the c212 hue vector from the measured-neutral (1,0.93,0.90) toward caption-pure orange (1,0.5,0) by P (0..1)")
    ap.add_argument("--disc-shoulder", default=None, metavar="S,K",
                    help="soft shoulder on the F212N disc arm above S (L-units), curve strength K; Lmax from the recorded prep frame max — un-blows the limb band")
    ap.add_argument("--field-gray", action="store_true",
                    help="field below the feather = GRAY luminance (Schmidt's documented grayscale-background mechanism); replaces the colorized deep arms")
    ap.add_argument("--field-epochs", type=int, default=1, choices=(1, 2),
                    help="1 = epoch-1 field only (default; the sky-frame two-epoch mean ghosts the planet — measured dead end); 2 = the coverage-aware two-epoch mean (evidence arm)")
    ap.add_argument("--sky-floor", type=float, default=None,
                    help="neutral floor lift f: out=(x+f)/(1+f) on all three channels")
    ap.add_argument("--measure", action="store_true",
                    help="Siril stat the recorded disc/sky boxes on each composite")
    ap.add_argument("--dry-run", action="store_true", help="write the .ssf, do not run Siril")
    args = ap.parse_args()

    sess = os.path.join(REPO, "sessions", args.session)
    work = os.path.join(sess, "work")
    ds = os.path.join(REPO, "datasets", args.session, "qa_work")
    results_rel = f"../../../web/results/{args.session}"
    for f in ("jup_f212n_prep.fits", "jup_f335m_prep.fits"):
        if not os.path.exists(os.path.join(work, f)):
            sys.exit(f"missing prepared frame: {f} (run prepare_jupiter.py first)")
    os.makedirs(os.path.join(REPO, "web", "results", args.session, "judge"), exist_ok=True)
    os.makedirs(os.path.join(REPO, "web", "results", args.session, "previews"), exist_ok=True)

    lv = json.load(open(os.path.join(ds, "j2_v2_levels.json")))
    ped212 = lv["f212n"]["sky"]["median_prep"]
    sig212 = lv["f212n"]["sky"]["sigma_prep"]
    ped335 = lv["f335m"]["sky"]["median_prep"]
    sig335 = lv["f335m"]["sky"]["sigma_prep"]
    Wd212 = args.w212_disc if args.w212_disc else lv["f212n"]["disc"]["max_prep"]
    Wd335 = lv["f335m"]["disc"]["max_prep"]
    ring212 = lv["f212n"]["ring_ansa"]["median_prep"]
    ring335 = lv["f335m"]["ring_ansa"]["median_prep"]

    FEATHER_LO, FEATHER_HI = 0.01, 0.04     # across the measured ring-max..disc-min gap
    Wf212 = args.w212_deep if args.w212_deep else FEATHER_HI
    Wf335 = 0.04 * ring335 / ring212        # v2's anchor, kept for reproducibility (see levels
    #                                         record: the box was the scatter fan — the ring
    #                                         itself is a Phase-2 data problem, not a knob here)
    Bf212 = ped212 - 2 * sig212
    Bf335 = ped335 - 2 * sig335
    GAP_SCALE = 4000.0 / 50000.0            # recorded prep divisors f335m/f212n
    CRESCENT_WHITE = 0.95

    svals = [float(s) for s in args.s_values.split(",")]
    ssf = ["requires 1.4.0", "setcompress 0", "set32bits", "cd work"]

    # zero-mask helper: 1 where the prep value is EXACTLY 0 (NaN-fill regions), else 0
    zmask = lambda tok: f"(1 - min({tok} * {tok} * 1000000000000000000, 1))"

    if args.gap_fill:
        ssf.append(f'pm "$jup_f212n_prep$ + {zmask("$jup_f212n_prep$")} '
                   f'* max($jup_f335m_prep$, 0) * {fnum(GAP_SCALE)}"')
    else:
        ssf.append('pm "$jup_f212n_prep$ * 1"')
    ssf.append("save p212f")

    # shared geometric weight: disc footprint from the (filled) f212n prep
    ssf.append(f'pm "min(max(($p212f$ - {fnum(FEATHER_LO)}) / {fnum(FEATHER_HI - FEATHER_LO)}, 0), 1)"')
    ssf.append("save w")

    # disc arms (linear placed points, clamped), then the finishing curves
    if args.disc_shoulder:
        s_sh, k_sh = (float(v) for v in args.disc_shoulder.split(","))
        prep_rec = json.load(open(os.path.join(ds, "j2_prepare.json")))
        lmax = (prep_rec["frames"]["f212n"]["post_norm_max"] - ped212) / (Wd212 - ped212)
        Lexpr = f"({sub('$p212f$', ped212)} / {fnum(Wd212 - ped212)})"
        norm_sh = math.asinh(k_sh * (lmax - s_sh))
        ssf.append(f'pm "max(min({Lexpr}, {fnum(s_sh)}) + {fnum(1 - s_sh)} * '
                   f'asinh({fnum(k_sh)} * max({Lexpr} - {fnum(s_sh)}, 0)) / {fnum(norm_sh)}, 0)"')
    else:
        ssf.append(f'pm "min(max({sub("$p212f$", ped212)} / {fnum(Wd212 - ped212)}, 0), 1)"')
    ssf.append("save l212d")
    d212 = "l212d"
    if args.m_disc or args.m_disc_212:
        ssf.append("load l212d")
        ssf.append(f"mtf 0 {fnum(args.m_disc or args.m_disc_212)} 1")
        ssf.append("save l212dx")
        d212 = "l212dx"

    ssf.append(f'pm "min(max({sub("$jup_f335m_prep$", ped335)} / {fnum(Wd335 - ped335)}, 0), 1)"')
    ssf.append("save l335d")
    d335 = "l335d"
    if args.m335 or args.m_disc:
        ssf.append("load l335d")
        if args.m335:
            ssf.append(f"mtf 0 {fnum(args.m335)} 1")
        if args.m_disc:
            ssf.append(f"mtf 0 {fnum(args.m_disc)} 1")
        ssf.append("save l335dx")
        d335 = "l335dx"

    if args.crescent_fill:
        if args.feather_crescent:
            ssf.append(f'pm "{zmask("$jup_f335m_prep$")} * $w$"')
            ssf.append("save m335m")
            ssf.append("load m335m")
            ssf.append(f"gauss {fnum(args.feather_crescent)}")
            ssf.append("save m335g")
            # normalize the blurred mask: a sigma-scale blur on a thin arc dilutes
            # its peak (measured ~0.4 on ~30px crescents) — rescale so the arc
            # interior returns to 1.0 while the feathered edge survives
            ssf.append(f'pm "max(${d335}$, min($m335g$ * 2.5, 1) * {fnum(CRESCENT_WHITE)})"')
        else:
            ssf.append(f'pm "max(${d335}$, {zmask("$jup_f335m_prep$")} * $w$ * {fnum(CRESCENT_WHITE)})"')
        ssf.append("save l335df")
        d335 = "l335df"

    if args.field_gray:
        if args.field_epochs == 2:
            for f in ("jup_f212n_ep2_prep.fits", "jup_f335m_ep2_prep.fits"):
                if not os.path.exists(os.path.join(work, f)):
                    sys.exit(f"--field-epochs=2 needs {f} (run prepare_epoch2.py)")
            # coverage-aware two-epoch mean — EVIDENCE ARM ONLY: registers the
            # sky, so the ep2 planet ghosts (measured; ledger amendment)
            ssf.append('pm "min($jup_f212n_ep2_prep$ * $jup_f212n_ep2_prep$ * 1000000000000000000, 1)"')
            ssf.append("save m2a")
            ssf.append('pm "$p212f$ + 0.5 * $m2a$ * ($jup_f212n_ep2_prep$ - $p212f$)"')
            ssf.append("save fld212")
            ssf.append('pm "min($jup_f335m_ep2_prep$ * $jup_f335m_ep2_prep$ * 1000000000000000000, 1)"')
            ssf.append("save m2b")
            ssf.append('pm "$jup_f335m_prep$ + 0.5 * $m2b$ * ($jup_f335m_ep2_prep$ - $jup_f335m_prep$)"')
            ssf.append("save fld335")
            ssf.append('pm "($fld212$ + $fld335$) * 0.5"')
        else:
            ssf.append('pm "($p212f$ + $jup_f335m_prep$) * 0.5"')
        ssf.append("save fldsum")
        ped_mix = 0.5 * (ped212 + ped335)
        sig_mix = 0.5 * math.sqrt(sig212 ** 2 + sig335 ** 2)
        Bfield = ped_mix - 2 * sig_mix
        Wfield = FEATHER_HI

    outputs = []
    for S in svals:
        stag = f"s{int(S)}"
        name = f"{args.tag}_{stag}"
        norm = math.asinh(S)
        if args.field_gray:
            a = args.colorize_a or 0.65
            pp = args.hue_purity
            hue = tuple((1 - pp) * v0 + pp * v1 for v0, v1 in
                        zip((1.0, 0.93, 0.90), (1.0, 0.5, 0.0)))
            c212 = tuple(a * v for v in hue)
            c335 = (1 - c212[0], 1 - c212[1], 1 - c212[2])
            ssf.append(f'pm "asinh({fnum(S)} * max({sub("$fldsum$", Bfield)} / {fnum(Wfield - Bfield)}, 0)) / {fnum(norm)}"')
            ssf.append(f"save lfield_{stag}")
            chans = []
            for ch, i in (("r", 0), ("g", 1), ("b", 2)):
                ssf.append(f'pm "$w$ * ({fnum(c212[i])} * ${d212}$ + {fnum(c335[i])} * ${d335}$) '
                           f'+ (1 - $w$) * min($lfield_{stag}$, 1)"')
                ssf.append(f"save {ch}_{name}")
                chans.append(f"{ch}_{name}")
            if args.sky_floor:
                f = args.sky_floor
                fl = []
                for c in chans:
                    ssf.append(f'pm "(${c}$ + {fnum(f)}) / {fnum(1 + f)}"')
                    ssf.append(f"save {c}fl")
                    fl.append(c + "fl")
                chans = fl
            ssf.append(f"rgbcomp {chans[0]} {chans[1]} {chans[2]} -out={results_rel}/wf_{name}")
            ssf.append(f"load {results_rel}/wf_{name}")
            if args.measure:
                ssf.append("boxselect 715 916 384 384")
                ssf.append("stat main")
                ssf.append("boxselect 1920 2527 128 256")
                ssf.append("stat main")
                ssf.append("boxselect 800 2219 200 200")
                ssf.append("stat main")
            ssf.append(f"savepng {results_rel}/judge/widefield_{name}")
            ssf.append("resample -width=800 -interp=area")
            ssf.append(f"savepng {results_rel}/previews/wf_{name}_small")
            outputs.append(f"web/results/{args.session}/judge/widefield_{name}.png")
            continue
        ssf.append(f'pm "asinh({fnum(S)} * max({sub("$p212f$", Bf212)} / {fnum(Wf212 - Bf212)}, 0)) / {fnum(norm)}"')
        ssf.append(f"save l212f_{stag}")
        ssf.append(f'pm "asinh({fnum(S)} * max({sub("$jup_f335m_prep$", Bf335)} / {fnum(Wf335 - Bf335)}, 0)) / {fnum(norm)}"')
        ssf.append(f"save l335f_{stag}")
        ssf.append(f'pm "$w$ * ${d212}$ + (1 - $w$) * min($l212f_{stag}$, 1)"')
        ssf.append(f"save l212_{name}")
        ssf.append(f'pm "$w$ * ${d335}$ + (1 - $w$) * min($l335f_{stag}$, 1)"')
        ssf.append(f"save l335_{name}")
        if args.colorize_a:
            a = args.colorize_a
            pp = args.hue_purity
            hue = tuple((1 - pp) * v0 + pp * v1 for v0, v1 in
                        zip((1.0, 0.93, 0.90), (1.0, 0.5, 0.0)))
            c212 = tuple(a * v for v in hue)
            c335 = (1 - c212[0], 1 - c212[1], 1 - c212[2])
            chans = []
            for ch, i in (("r", 0), ("g", 1), ("b", 2)):
                ssf.append(f'pm "{fnum(c212[i])} * $l212_{name}$ + {fnum(c335[i])} * $l335_{name}$"')
                ssf.append(f"save {ch}_{name}")
                chans.append(f"{ch}_{name}")
        else:
            ssf.append(f'pm "0.5 * $l212_{name}$ + 0.5 * $l335_{name}$"')
            ssf.append(f"save g_{name}")
            chans = [f"l212_{name}", f"g_{name}", f"l335_{name}"]
        if args.sky_floor:
            f = args.sky_floor
            for c in chans:
                ssf.append(f'pm "(${c}$ + {fnum(f)}) / {fnum(1 + f)}"')
                ssf.append(f"save {c}fl")
            chans = [c + "fl" for c in chans]
        ssf.append(f"rgbcomp {chans[0]} {chans[1]} {chans[2]} -out={results_rel}/wf_{name}")
        ssf.append(f"load {results_rel}/wf_{name}")
        if args.measure:
            ssf.append("boxselect 715 916 384 384")
            ssf.append("stat main")
            ssf.append("boxselect 1920 2527 128 256")
            ssf.append("stat main")
        ssf.append(f"savepng {results_rel}/judge/widefield_{name}")
        ssf.append("resample -width=800 -interp=area")
        ssf.append(f"savepng {results_rel}/previews/wf_{name}_small")
        outputs.append(f"web/results/{args.session}/judge/widefield_{name}.png")
    ssf.append("close")

    ssf_path = os.path.join(work, f"j2_render_{args.tag}.ssf")
    with open(ssf_path, "w") as f:
        f.write("\n".join(ssf) + "\n")
    print(f"wrote {ssf_path} ({len(ssf)} lines)")
    if args.dry_run:
        return

    r = subprocess.run(SIRIL + ["-d", sess, "-s", ssf_path],
                       capture_output=True, text=True)
    for l in r.stdout.splitlines():
        if "layer:" in l or "Current selection" in l or "Error" in l or "error" in l:
            print(l)
    missing = [o for o in outputs if not os.path.exists(os.path.join(REPO, o))]
    if r.returncode != 0 or missing:
        sys.exit(f"RENDER FAILED rc={r.returncode} missing={missing}\n--- tail ---\n"
                 + "\n".join(r.stdout.splitlines()[-30:]))

    rec = {
        "render": f"j2 widefield {args.tag} — documented-process expression + finishing stage (ledger: j2_v3_finishing_ladder)",
        "inputs": "work/jup_{f212n,f335m}_prep.fits (recorded divisors 50000/4000)",
        "constants": {
            "disc_arm": {"f212n": {"B": ped212, "W": Wd212}, "f335m": {"B": ped335, "W": Wd335}, "curve": "linear (solar-system doctrine)"},
            "deep_arm": {"f212n": {"B": Bf212, "W": Wf212}, "f335m": {"B": Bf335, "W": Wf335},
                         "curve": "asinh placed-points, S bracket", "S_values": svals},
            "feather": [FEATHER_LO, FEATHER_HI],
            "palette": "R=f212n, B=f335m, G=0.5 each (pseudogreen)",
            "gap_fill": args.gap_fill, "crescent_fill": args.crescent_fill,
            "feather_crescent_px": args.feather_crescent,
            "w212_disc": args.w212_disc,
            "m335": args.m335, "m_disc": args.m_disc, "m_disc_212": args.m_disc_212,
            "hue_purity": args.hue_purity, "disc_shoulder": args.disc_shoulder,
            "colorize_a": args.colorize_a, "sky_floor": args.sky_floor,
            "gap_scale": GAP_SCALE, "crescent_white": CRESCENT_WHITE,
        },
        "outputs": outputs,
    }
    with open(os.path.join(ds, f"{args.tag}_run.json"), "w") as f:
        json.dump(rec, f, indent=1)
    print(f"-> {args.tag}_run.json; judge surfaces:", ", ".join(outputs))


if __name__ == "__main__":
    main()
