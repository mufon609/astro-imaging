#!/usr/bin/env python3
"""jwst-jupiter wide-field render: the documented original process expressed
in the sanctioned toolset (Siril pm/rgbcomp/savepng do every pixel op).

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
    pedestal - 2*sigma (sky noise straddles the pedestal; a black AT the
    pedestal would crush half the sky), white at the ring-anchored level:
    W212 = the feather top; W335 = W212 * (ring335/ring212 medians) so the
    RING lands equal in both layers — the reference's measured neutral ring.
- HDR composite: feathered value-keyed weight on the (gap-filled) F212N prep,
  ramp across the measured ring-max -> disc-min value gap — the headless
  equivalent of the documented Photoshop masked composite. One shared
  geometric weight for both filters (the F212N disc is hole-free).
- Palette: channel isolation + pseudogreen (R=F212N, G=half each, B=F335M) —
  Schmidt's documented JWST mechanism ("half of the red, half of the blue
  ... channels add up to 100 percent").
- FILLS (policy toggles, each the documented original mechanism, applied
  BEFORE transfers per the team's ordering rule):
  * --gap-fill: F212N SW chip gaps filled from F335M at prep level (team:
    "fill that in with the closest wavelength filter"; Schmidt: "either
    filter to complete the other"). Zero-mask arithmetic: NaN->0 regions are
    the only exact zeros in the prep frames.
  * --crescent-fill: F335M saturation-NaN limb crescents white-filled at
    display level inside the disc footprint (DePasquale pixel-clip: black
    saturated cores "set them to white").
- ONE bracketed knob: deep-arm asinh strength S (both filters share it);
  each value renders a full composite (default bracket 5 and 15).

Constants come from datasets/<session>/qa_work/j2_v2_levels.json (Siril stat
measurements) — never retyped here. Outputs: per-stage FITS in the session
work dir, finals + full-frame PNG16 judge surfaces + 800px previews under
web/results/<session>/. Run record: qa_work/j2_v2_run.json.
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
    ap.add_argument("--s-values", default="5,15",
                    help="deep-arm asinh strength bracket (comma-separated)")
    ap.add_argument("--gap-fill", action="store_true",
                    help="fill F212N chip gaps from F335M (documented team mechanism)")
    ap.add_argument("--crescent-fill", action="store_true",
                    help="white-fill F335M saturation crescents in-disc (pixel-clip equivalent)")
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
    Wd212 = lv["f212n"]["disc"]["max_prep"]
    Wd335 = lv["f335m"]["disc"]["max_prep"]
    ring212 = lv["f212n"]["ring_ansa"]["median_prep"]
    ring335 = lv["f335m"]["ring_ansa"]["median_prep"]

    FEATHER_LO, FEATHER_HI = 0.01, 0.04     # across the measured ring-max..disc-min gap
    Wf212 = FEATHER_HI                      # deep arm saturates exactly at handover
    Wf335 = Wf212 * ring335 / ring212       # ring-neutral anchor
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
        ssf.append("save p212f")
    else:
        ssf.append('pm "$jup_f212n_prep$ * 1"')
        ssf.append("save p212f")

    # shared geometric weight: disc footprint from the (filled) f212n prep
    ssf.append(f'pm "min(max(($p212f$ - {fnum(FEATHER_LO)}) / {fnum(FEATHER_HI - FEATHER_LO)}, 0), 1)"')
    ssf.append("save w")

    # disc arms (linear placed points, clamped)
    ssf.append(f'pm "min(max({sub("$p212f$", ped212)} / {fnum(Wd212 - ped212)}, 0), 1)"')
    ssf.append("save l212d")
    ssf.append(f'pm "min(max({sub("$jup_f335m_prep$", ped335)} / {fnum(Wd335 - ped335)}, 0), 1)"')
    ssf.append("save l335d")
    if args.crescent_fill:
        ssf.append(f'pm "max($l335d$, {zmask("$jup_f335m_prep$")} * $w$ * {fnum(CRESCENT_WHITE)})"')
        ssf.append("save l335df")
    disc335 = "l335df" if args.crescent_fill else "l335d"

    outputs = []
    for S in svals:
        tag = f"s{int(S)}"
        norm = math.asinh(S)
        ssf.append(f'pm "asinh({fnum(S)} * max({sub("$p212f$", Bf212)} / {fnum(Wf212 - Bf212)}, 0)) / {fnum(norm)}"')
        ssf.append(f"save l212f_{tag}")
        ssf.append(f'pm "asinh({fnum(S)} * max({sub("$jup_f335m_prep$", Bf335)} / {fnum(Wf335 - Bf335)}, 0)) / {fnum(norm)}"')
        ssf.append(f"save l335f_{tag}")
        ssf.append(f'pm "$w$ * $l212d$ + (1 - $w$) * min($l212f_{tag}$, 1)"')
        ssf.append(f"save l212_{tag}")
        ssf.append(f'pm "$w$ * ${disc335}$ + (1 - $w$) * min($l335f_{tag}$, 1)"')
        ssf.append(f"save l335_{tag}")
        ssf.append(f'pm "0.5 * $l212_{tag}$ + 0.5 * $l335_{tag}$"')
        ssf.append(f"save g_{tag}")
        ssf.append(f"rgbcomp l212_{tag} g_{tag} l335_{tag} -out={results_rel}/wf_v2_{tag}")
        ssf.append(f"load {results_rel}/wf_v2_{tag}")
        ssf.append(f"savepng {results_rel}/judge/widefield_v2_{tag}")
        ssf.append("resample -width=800 -interp=area")
        ssf.append(f"savepng {results_rel}/previews/wf_v2_{tag}_small")
        outputs.append(f"web/results/{args.session}/judge/widefield_v2_{tag}.png")
    ssf.append("close")

    ssf_path = os.path.join(work, "j2_v2_render.ssf")
    with open(ssf_path, "w") as f:
        f.write("\n".join(ssf) + "\n")
    print(f"wrote {ssf_path} ({len(ssf)} lines)")
    if args.dry_run:
        return

    r = subprocess.run(SIRIL + ["-d", sess, "-s", ssf_path],
                       capture_output=True, text=True)
    sys.stdout.write("\n".join(l for l in r.stdout.splitlines()
                               if "Error" in l or "error" in l or "Running command" in l) + "\n")
    missing = [o for o in outputs if not os.path.exists(os.path.join(REPO, o))]
    if r.returncode != 0 or missing:
        sys.exit(f"RENDER FAILED rc={r.returncode} missing={missing}\n--- tail ---\n"
                 + "\n".join(r.stdout.splitlines()[-30:]))

    rec = {
        "render": "j2_widefield_v2 — documented-process expression (see the ledger amendment + docs/jwst-official-rendering-process.md)",
        "inputs": "work/jup_{f212n,f335m}_prep.fits (recorded divisors 50000/4000)",
        "constants": {
            "disc_arm": {"f212n": {"B": ped212, "W": Wd212}, "f335m": {"B": ped335, "W": Wd335}, "curve": "linear (solar-system doctrine)"},
            "deep_arm": {"f212n": {"B": Bf212, "W": Wf212}, "f335m": {"B": Bf335, "W": Wf335},
                         "curve": "asinh placed-points, S bracket", "S_values": svals,
                         "W335_rule": "W212 * ring335/ring212 (ring-neutral anchor)"},
            "feather": [FEATHER_LO, FEATHER_HI],
            "palette": "R=f212n, B=f335m, G=0.5 each (pseudogreen)",
            "gap_fill": args.gap_fill, "crescent_fill": args.crescent_fill,
            "gap_scale": GAP_SCALE, "crescent_white": CRESCENT_WHITE,
        },
        "stages": "work/: p212f, w, l212d, l335d[, l335df], l212f_*, l335f_*, l212_*, l335_*, g_*",
        "outputs": outputs,
    }
    with open(os.path.join(ds, "j2_v2_run.json"), "w") as f:
        json.dump(rec, f, indent=1)
    print("-> j2_v2_run.json; judge surfaces:", ", ".join(outputs))


if __name__ == "__main__":
    main()
