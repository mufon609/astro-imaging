#!/usr/bin/env python3
"""Narrowband SHO render by driving Nightlight — the reference author's own
open tool — the tool-honest way to reproduce a professional narrowband
finish on our stacks.

WHY THIS EXISTS (the mechanism our chain lacks). On an SHO target the
defining feature — the blue O3 sphere — comes from a STAR-COLOR-NEUTRAL
colour balance: narrowband stars carry almost no O3 (measured star colour
R2.7/G0.9/B0.4 %), so neutralising them boosts O3 ~13x, and THAT reveals
the sphere. Siril SPCC does PHOTOMETRIC calibration that instead equalises
O3=Ha (star-neutral in a different sense) and erases the sphere (measured:
sphere B/R 0.77 our chain vs 3.21 reproduced). Nightlight's `rgbBalance`
does the star-neutral balance natively, then develops with ONE global
stretch and NO star-separation / corings / denoise — the un-conservative
process our default chain fights. Reproduced 0.1% identical to the author's
own output on our data.

This drives Nightlight as a SANCTIONED TOOL (orchestrate-not-hand-roll: the
author's own open tool, staged on this aarch64 rig) for the narrowband
colour+combine+develop step. It is NOT a numpy reimplementation — every
image operation is Nightlight's. The palette that results is the natural
green-teal SHO look; the published GOLD reference is the author's MANUAL
GIMP finish (selective colour/curves), an aesthetic finishing choice this
tool does not fabricate — apply a hue finish (recipe `hue_offset`, or our
huerot downstream) on the user's judgement.

Usage:
  nightlight_sho.py <session> <set> [--lossless]

Inputs: the composition's per-line member stacks (results/stack_<member>.fit,
mapped R/G/B by composition.json). Recipe `nightlight` block tunes the
develop (all Nightlight params; brightness = stretch scale):
  {"stretch_scale": 0.012, "stretch_loc": 0.1, "saturation": 1.5,
   "black_sigma": 2, "scnr": 0.5,
   "hue_from": 100, "hue_to": 190, "hue_offset": 0}
The author's exact develop is scale 0.004 (dark, then GIMP-brightened); we
default brighter so the reproducible output is viewable without a manual
step.
"""
import argparse
import json
import os
import subprocess
import sys

NIGHTLIGHT = os.path.expanduser(
    "~/.cache/astro_stage/nightlight/nightlight_linux_arm64")

_libdir = os.path.dirname(os.path.abspath(__file__))
while _libdir != os.path.dirname(_libdir):
    if os.path.isdir(os.path.join(_libdir, "lib")):
        sys.path.insert(0, os.path.join(_libdir, "lib"))
        break
    _libdir = os.path.dirname(_libdir)
import astrometrics as am  # noqa: E402

DEFAULTS = {"stretch_scale": 0.012, "stretch_loc": 0.1, "saturation": 1.5,
            "black_sigma": 2, "scnr": 0.5,
            "hue_from": 100, "hue_to": 190, "hue_offset": 0,
            # HONEST O3 emphasis: the bubble shell is measured Ha-dominant
            # (O3/Ha ~0.45), so its true colour is green. o3_emphasis > 1
            # scales the O3(B) channel of the star-neutral-balanced LINEAR to
            # push the shell teal — an EXPLICIT aesthetic emphasis BEYOND the
            # data's ratio, labelled in the output, never a hidden boost. 1.0
            # = the honest colour.
            "o3_emphasis": 1.0}


def combine_job(members, cfg, out_fits):
    """The author's combine recipe (star-neutral rgbBalance -> the O3 boost;
    SCNR; black-point), tunable saturation + optional hue finish. Members
    are the R,G,B channel file basenames in the run dir."""
    return {"type": "seq", "steps": [
        {"type": "loadMany", "filePatterns": members},
        {"type": "starDetect", "radius": 16, "sigma": 15,
         "badPixelSigma": 0, "inOutRatio": 1.4,
         "save": {"type": "save", "filePattern": ""}},
        {"type": "selectRef", "mode": 4, "fileName": "", "fileID": 0,
         "starDetect": {"type": "starDetect", "radius": 16, "sigma": 15,
                        "badPixelSigma": 0, "inOutRatio": 1.4,
                        "save": {"type": "save", "filePattern": ""}}},
        # ALIGN the channels before combining. Our per-filter member stacks
        # are each registered to their OWN reference, so they are NOT
        # mutually aligned (measured: O3 offset ~57 px from Ha) — without
        # this the O3 shell fringes into a crescent instead of a filled
        # sphere. The author's own stacks were pre-aligned; ours are not.
        {"type": "align", "k": 20, "threshold": 1.0, "oobMode": 2},
        {"type": "rgbCombine"},
        # star-color-neutral balance -> the ~13x O3 boost that reveals the
        # sphere (targets neutral background + neutral mean star colour)
        {"type": "rgbBalance", "block": 16, "border": 0.1, "skipBright": 0,
         "skipDim": 0.5, "shadows": {"R": 1, "G": 1, "B": 1},
         "highlights": {"R": 1, "G": 1, "B": 1}},
        {"type": "rgbToHSLuv"},
        {"type": "hslApplyLum"},
        {"type": "hslNeutralizeBackground", "sigmaLow": -1, "sigmaHigh": -1},
        {"type": "hslSaturationGamma",
         "gamma": float(cfg["saturation"]), "sigma": 1},
        {"type": "hslRotateHue", "from": float(cfg["hue_from"]),
         "to": float(cfg["hue_to"]), "offset": float(cfg["hue_offset"]),
         "sigma": 1},
        {"type": "hslSCNR", "factor": float(cfg["scnr"])},
        {"type": "hslMidtones", "mid": 0, "black": float(cfg["black_sigma"])},
        {"type": "hsluvToRGB"},
        {"type": "save", "filePattern": out_fits}]}


def stretch_job(in_fits, cfg, out_fits, out_jpg):
    """One global develop stretch (loc target, scale = the brightness lever
    at fixed noise-width). No corings, no denoise — the author's develop."""
    return {"type": "seq", "steps": [
        {"type": "loadMany", "filePatterns": [in_fits]},
        {"type": "normRange"},
        {"type": "stretch", "location": float(cfg["stretch_loc"]),
         "scale": float(cfg["stretch_scale"])},
        {"type": "save", "filePattern": out_fits},
        {"type": "save", "filePattern": out_jpg}]}


def run_job(run_dir, job, name):
    p = os.path.join(run_dir, name)
    with open(p, "w") as f:
        json.dump(job, f)
    r = subprocess.run([NIGHTLIGHT, "-job", p, "run"],
                       cwd=run_dir, capture_output=True, text=True)
    if r.returncode != 0:
        sys.exit(f"nightlight_sho: Nightlight failed ({name}):\n"
                 + r.stdout[-2000:] + r.stderr[-800:])
    return r.stdout


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("session")
    ap.add_argument("set")
    ap.add_argument("--lossless", action="store_true",
                    help="also write PNG16 next to the PNG8 final")
    ap.add_argument("--o3-emphasis", type=float, default=None,
                    help="override the recipe o3_emphasis (labelled aesthetic "
                         "O3/teal boost beyond the honest shell ratio); the "
                         "output is suffixed _o3x<N> so it never overwrites "
                         "the honest render")
    args = ap.parse_args()

    repo = os.path.dirname(os.path.dirname(os.path.dirname(
        os.path.abspath(__file__))))
    sdir = os.path.join(repo, args.session)
    if not os.path.exists(NIGHTLIGHT):
        sys.exit(f"nightlight_sho: Nightlight binary not at {NIGHTLIGHT} — "
                 "it is the reference author's own open tool (aarch64), "
                 "staged in the cache; restage it to reproduce the finish")

    dsdir = am.dataset_dir(sdir, args.set)
    comp_p = os.path.join(dsdir, "composition.json")
    if not os.path.exists(comp_p):
        sys.exit(f"nightlight_sho: no composition.json at {comp_p} — this "
                 "drives a mono-filters SHO composition (R/G/B members)")
    comp = json.load(open(comp_p))
    ch = comp.get("channels", {})
    members = comp.get("members", {})
    order = [ch.get("R"), ch.get("G"), ch.get("B")]
    if not all(order):
        sys.exit(f"nightlight_sho: composition.json channels must map "
                 f"R/G/B -> members; got {ch}")

    cfg = dict(DEFAULTS)
    recipe_p = os.path.join(dsdir, "recipe.json")
    if os.path.exists(recipe_p):
        nl = json.load(open(recipe_p)).get("nightlight", {})
        unknown = set(nl) - set(DEFAULTS)
        if unknown:
            sys.exit(f"nightlight_sho: unknown nightlight recipe keys "
                     f"{sorted(unknown)} (known: {sorted(DEFAULTS)})")
        cfg.update(nl)
    if args.o3_emphasis is not None:
        cfg["o3_emphasis"] = args.o3_emphasis

    run_dir = os.path.join(sdir, "work", "nl_sho")
    os.makedirs(run_dir, exist_ok=True)
    # link each channel's member stack as <MEMBER>.fit in the run dir
    chan_files = []
    for chan in order:
        member = members.get(chan, chan)   # channel value IS the member name
        src = os.path.join(sdir, "results", f"stack_{member}.fit")
        if not os.path.exists(src):
            sys.exit(f"nightlight_sho: missing member stack {src} "
                     f"(channel maps to member {member!r})")
        link = os.path.join(run_dir, f"{chan}.fit")
        if os.path.islink(link) or os.path.exists(link):
            os.remove(link)
        os.symlink(os.path.relpath(src, run_dir), link)
        chan_files.append(f"{chan}.fit")

    # MANDATORY input alignment check: our per-filter member stacks are each
    # registered to their OWN reference, so they can be mutually
    # MISALIGNED — and a misaligned emission shell fringes to a crescent AND
    # corrupts the star-neutral balance (misregistered stars read as
    # channel-deficient). Measure it, report it, and confirm the Nightlight
    # align step has real work to do; a large offset that Nightlight cannot
    # resolve would need compose.py's aligned data instead.
    import numpy as np
    from numpy.fft import fft2, ifft2
    planes_in = [am.read_fits_planes(os.path.join(run_dir, f))[1][0]
                 for f in chan_files]
    H, W = planes_in[1].shape
    yy, xx, ss = int(0.5 * H), int(0.5 * W), min(400, H // 4, W // 4)

    def _shift(a, b):
        pa = a[yy - ss:yy + ss, xx - ss:xx + ss]
        pb = b[yy - ss:yy + ss, xx - ss:xx + ss]
        cc = np.abs(ifft2(fft2(pa - pa.mean()) * np.conj(fft2(pb - pb.mean()))))
        oy, ox = np.unravel_index(int(np.argmax(cc)), cc.shape)
        return (oy - 2 * ss if oy > ss else oy,
                ox - 2 * ss if ox > ss else ox)
    offs = [_shift(planes_in[i], planes_in[1]) for i in (0, 2)]
    maxoff = max(abs(v) for o in offs for v in o)
    print(f"[nightlight_sho] input channel offsets vs G: R{offs[0]} B{offs[1]} "
          f"px — {'ALIGNING (Nightlight align step)' if maxoff > 1 else 'already aligned'}")
    if maxoff > 1:
        print("[nightlight_sho] NOTE: per-filter member stacks are NOT "
              "mutually aligned; the Nightlight `align` step registers them "
              "(else the emission shell renders as a crescent and the star "
              "balance is corrupted).")

    print(f"[nightlight_sho] {args.session}/{args.set}: driving Nightlight "
          f"(the author's tool) on {chan_files} (R,G,B)")
    print(f"[nightlight_sho] develop: scale {cfg['stretch_scale']} "
          f"(brightness) loc {cfg['stretch_loc']} saturation "
          f"{cfg['saturation']} scnr {cfg['scnr']} black {cfg['black_sigma']}"
          f"sigma hue_offset {cfg['hue_offset']}")
    log = run_job(run_dir, combine_job(chan_files, cfg, "sho_balanced.fits"),
                  "job_combine.json")
    for line in log.splitlines():
        if "star color" in line or line.strip().startswith("r=") \
                or "Location is" in line:
            print(f"[nightlight_sho]   {line.strip()}")
    balanced = "sho_balanced.fits"
    o3e = float(cfg["o3_emphasis"])
    if o3e != 1.0:
        # HONEST, LABELLED O3 emphasis: scale the O3(B) channel of the
        # star-neutral-balanced LINEAR to push the shell teal — beyond the
        # measured shell ratio (O3/Ha ~0.45), an explicit aesthetic choice,
        # never a hidden boost. No corings follow (Nightlight develops
        # plainly), so a linear channel weight is admissible here.
        cards, pl, _ = am.read_fits_planes(os.path.join(run_dir, balanced))
        pl[2] = np.clip(pl[2] * o3e, 0.0, 1.0)
        balanced = "sho_balanced_o3.fits"
        am.write_fits_planes(os.path.join(run_dir, balanced), cards, pl)
        print(f"[nightlight_sho] O3 EMPHASIS {o3e:g}x on the balanced B(O3) "
              "channel — EXPLICIT aesthetic teal boost beyond the honest "
              "shell ratio (O3/Ha ~0.45), NOT the data's true colour")
    run_job(run_dir, stretch_job(balanced, cfg,
                                 "sho_final.fits", "sho_final.jpg"),
            "job_stretch.json")

    # convert the linear-display FITS to a lossless PNG final (the judgment
    # surface); Nightlight already wrote a JPEG preview
    import numpy as np
    from PIL import Image
    _, planes, _ = am.read_fits_planes(os.path.join(run_dir, "sho_final.fits"))
    u8 = (np.clip(planes.transpose(1, 2, 0), 0, 1) * 255 + .5).astype(np.uint8)
    tag = "" if o3e == 1.0 else f"_o3x{o3e:g}"
    out = os.path.join(sdir, "results", f"nightlight_{args.set}{tag}.png")
    Image.fromarray(u8).save(out, pnginfo=am.png_srgb_info())
    print(f"[nightlight_sho] wrote {out}")
    if args.lossless:
        u16 = (np.clip(planes.transpose(1, 2, 0), 0, 1) * 65535 + .5
               ).astype(np.uint16)
        am.write_png16(out[:-4] + "_16bit.png", u16)
        print(f"[nightlight_sho] wrote {out[:-4]}_16bit.png")


if __name__ == "__main__":
    main()
