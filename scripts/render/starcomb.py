#!/usr/bin/env python3
"""Starless/stars split render + recombination (standard-DSO style).

The product chain ORCHESTRATES industry tools — every operator that
rewrites the deliverable's pixels drives a real tool (Siril / GraXpert /
StarNet2), never hand-rolled numpy. Knob values resolve CLI > the
dataset's tracked recipe (datasets/<session>/<set>/recipe.json) > the
GENERIC defaults — so an approved look is pinned per dataset, and a
dataset without a recipe renders honestly generic and says so:

  starcomb.py <session> <set> --stack results/stack_<set>_norgbeq_spcc.fit [--lossless]

Chain (input is the SPCC-calibrated stack — solve_field.py --inject +
siril spcc):
  1. GraXpert BGE + siril subsky 1 on the STAR-FUL linear (cached; the
     only order measured MW-safe — BGE on starless ERASES the MW)
  2. star separation (cached): StarNet2 ONNX (net) or mask+inpaint
     (inpaint); auto = net when the weights are installed
  starless: siril autostretch -1.5 <starless_target> (linked broadband
       standard; unlinked is a measurement rung)
    -> siril denoise -vst -mod=0.5 (<starless_denoise=vstpost>; a linear
       placement imprints a radial signature on self-flat data)
    -> black_point via siril `mtf b 0.5 1` (linear black-point rescale:
       gaps clip to true black, real signal sits above the clip)
  stars: faint components culled below the <cull_pct> flux percentile,
    skirt cored below <stars_floor> x sigma (the ghost-aura fix: only
    genuine star signal reaches the stretch), then rendered by siril
    `mtf 0 m 1` with a data-derived anchor m so the median top-500
    amplitude (on the fixed G basis) renders at <stars_peak>
  combine: siril pm screen 1-(1-a)(1-b) -> siril satu -> JPEG q100/4:4:4
    [+ PNG].

Narrowband SHO colour+develop (the O3-sphere star-neutral mechanism
Siril has no equivalent for) is NOT in this chain: it is Nightlight's
job (scripts/render/nightlight_sho.py), auto-routed via render_engine.

Ladder mode (single knob, control auto-bracketed, STOPS for judgment):
  starcomb.py <session> <set> --stack ... --param starless_target \\
      --values 0.05,0.09 --hypothesis "..."

Reported per configuration: THE GATE = bg_qa on the starless render
(composition-agnostic statistical sky scope, foreground excluded,
thresholds never loosen: color / gradient / blotch / rings); whole-frame
bg_qa on the recombine as reference; star metrics + star-shell audit.
"""
import argparse
import json
import os
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
import render_helpers as rh  # noqa: E402  (run_graxpert, strips, measure_jpg)

# The only per-set geometry left is the terrestrial foreground (astrometrics
# .CTX): main() calls am.configure(session, set) — datasets/<session>/<set>/
# geometry.json values, else foreground None. An unconfigured CTX carries no
# geometry, so a forgotten configure() degrades to whole-frame, never another
# set's mask.
# The background gate (bg_qa) selects its sky statistically, not from any
# per-set composition input.


def run_siril(session_dir, lines, name):
    p = os.path.join(session_dir, "work", name)
    with open(p, "w") as f:
        f.write("\n".join(lines) + "\n")
    r = subprocess.run(["flatpak", "run", "--command=siril-cli",
                        "org.siril.Siril", "-d", session_dir, "-s", p],
                       capture_output=True, text=True)
    if r.returncode != 0:
        sys.exit(f"starcomb: siril failed ({name}):\n" + r.stdout[-2500:])


def _run_sep(repo, sdir, script, input_fit, set_name, extra=()):
    """One separation subprocess; returns its (starless, stars, catalog)
    trio, parsed from the machine-readable SEPTRIO sentinel line both
    separators emit last (fresh run and cache hit alike). Parsing the
    sentinel — not "the last lines ending .fit/.npz" — means a future
    diagnostic print can never be mistaken for an output path."""
    outdir = os.path.join(sdir, "work", "starsep")
    cmd = [sys.executable,
           os.path.join(repo, "scripts", "render", "separation", script),
           input_fit, outdir]
    if set_name:
        cmd += [f"--session={sdir}", f"--set={set_name}"]
    cmd += list(extra)
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        sys.exit("starcomb: starsep failed:\n" + r.stdout[-2000:] + r.stderr[-1000:])
    print(r.stdout.rstrip())
    trio = None
    for line in r.stdout.splitlines():
        if line.startswith("SEPTRIO\t"):
            parts = line.split("\t")[1:]
            if len(parts) == 3:       # index guard: ignore a malformed line
                trio = parts
    if trio is None:
        sys.exit("starcomb: separator emitted no valid SEPTRIO trio line "
                 f"({script}):\n" + r.stdout[-2000:])
    return trio[0], trio[1], trio[2]


def ensure_starsep(repo, sdir, input_fit, prom=6.0, set_name=None,
                   engine="auto"):
    """Run (cached) star separation on any linear FITS. engine picks the
    separator: 'net' = starnet_sep.py StarNet2 ONNX inference (learned
    star/structure discrimination — the fail-safe on a resolved object;
    its worst case is a cosmetic bright-star shell); 'inpaint' =
    starsep.py mask+inpaint (detection-bounded: leaves the <6 sigma
    faint tail in the starless layer, and DESTROYS resolved-object
    structure it classifies as stars — it warns when that risk is
    measured); 'auto' = net when the StarNet2 weights are installed,
    else inpaint with the risk stated. prom = the component prominence
    cut in sigma (inpaint detection only). Engines run as subprocesses,
    so the per-set geometry context is passed explicitly, and both
    print the same starless/stars/catalog trio."""
    if engine == "auto":
        sys.path.insert(0, os.path.join(repo, "scripts", "render",
                                        "separation"))
        import starnet_sep
        if os.path.exists(starnet_sep.WEIGHTS):
            engine = "net"
        else:
            engine = "inpaint"
            print("[starcomb] sep_engine auto -> inpaint: StarNet2 weights "
                  f"not found at {starnet_sep.WEIGHTS}. The mask+inpaint "
                  "fallback destroys resolved-object structure (galaxy "
                  "knots read as stars) — install the weights for any "
                  "frame holding a resolved object.")
        print(f"[starcomb] sep_engine auto -> {engine}")
    if prom != 6.0 and engine != "inpaint":
        # the net has no prominence cut
        print(f"[starcomb] sep_prom ignored by the {engine} engine")
        prom = 6.0
    prom_args = [f"--prom={prom:g}"] if prom != 6.0 else []
    if engine == "net":
        return _run_sep(repo, sdir, "starnet_sep.py", input_fit, set_name)
    return _run_sep(repo, sdir, "starsep.py", input_fit, set_name,
                    prom_args)


def ensure_bge_linear(ctx, mode="gx"):
    """Linear background handling on the STAR-FUL stack, cached by stack
    identity + mode:

    - `gx` — GraXpert BGE + `subsky 1` (the standard full extraction). It
      runs before star separation: on a star-removed frame the
      frame-filling Milky Way reads as background and is absorbed, so the
      star-ful order preserves it. CLASS LIMIT: GraXpert's model cannot
      distinguish frame-filling FAINT nebulosity from a sky gradient and
      absorbs it as background (bright compact objects saturate out of
      its input clip and survive).
    - `plane` — `subsky 1` only: a first-degree plane removes the gate's
      gradient class but cannot absorb localized nebulosity by
      construction. The retention mode for fields that ARE mostly object.
    - `off` — the stack passes through untouched (measurement rungs; the
      gate still judges the result).
    """
    sdir, work, stack = ctx["sdir"], ctx["work"], ctx["stack"]
    if mode == "off":
        print("[starcomb] bgelin off — stack passes through (gate judges)")
        return stack
    st = os.stat(stack)
    suffix = "" if mode == "gx" else f"_{mode}"
    out = os.path.join(work,
                       f"bgelin_{st.st_size}_{int(st.st_mtime)}{suffix}.fit")
    if os.path.exists(out):
        print(f"[starcomb] bge-linear cache hit {os.path.basename(out)}")
        return out
    if mode == "gx":
        src = rh.run_graxpert(stack, work,
                              lambda m: print(f"[starcomb] {m}", flush=True))
    else:
        src = stack
    rel_src = os.path.relpath(src, sdir)
    rel_out = os.path.relpath(out, sdir)
    # subsky WITHOUT -dither: dither injects ±1 LSB16 random noise to mask
    # quantization banding, which cannot occur on this 32-bit float chain —
    # and it is unseeded, so it was the one nondeterministic step in the
    # render (measured: two cold builds differ on 100% of pixels, RMS 0.41
    # counts16 = 0.08 sigma; downstream star detection moved 852 -> 858).
    run_siril(sdir, ["requires 1.4.0",
                     f"load {rel_src[:-5] if rel_src.endswith('.fits') else rel_src}",
                     "subsky 1",
                     f"save {rel_out[:-4]}",
                     "close"], "starcomb_bgelin.gen.ssf")
    # the GraXpert intermediate is consumed the moment bgelin exists —
    # per-stage cleanup (200-450 MB per dataset on this disk); a cold
    # rebuild regenerates it from the stack deterministically
    if mode == "gx" and os.path.exists(out) \
            and os.path.exists(src):
        os.remove(src)
    return out


def run_graxpert_denoise(work, fit):
    """GraXpert AI denoising on a linear FITS (the --starless-denoise gx
    option), cached by input identity. Standard-order placement: linear,
    on the STARLESS layer, before the stretch."""
    st = os.stat(fit)
    out = os.path.join(work, f"gxdn_{st.st_size}_{int(st.st_mtime)}.fits")
    if os.path.exists(out):
        print(f"[starcomb] gx-denoise cache hit {os.path.basename(out)}")
        return out
    print("[starcomb] graxpert denoising (linear, starless) ...", flush=True)
    r = subprocess.run([rh.GRAXPERT, "-cmd", "denoising", fit,
                        "-output", out[:-5], "-gpu", "false"],
                       capture_output=True, text=True)
    if not os.path.exists(out):
        sys.exit("starcomb: graxpert denoising produced no output:\n"
                 + r.stdout[-2000:] + "\n" + r.stderr[-1000:])
    return out


def solve_mtf_m(x0, y0):
    x0 = min(max(x0, 1e-6), 0.9999)
    m = x0 * (y0 - 1.0) / (2.0 * x0 * y0 - x0 - y0)
    return min(max(m, 1e-4), 1 - 1e-4)


def _minimal_fits_cards(nc, h, w):
    """A minimal valid float32 header (write_fits_planes patches the NAXIS
    geometry from the array) — for round-tripping an in-memory array
    through a siril command that has no numpy equivalent we should use."""
    def card(k, v):
        return f"{k:<8}= {v:>20}".ljust(80)
    return [card("SIMPLE", "T"), card("BITPIX", "-32"),
            card("NAXIS", 3 if nc == 3 else 2),
            card("NAXIS1", w), card("NAXIS2", h)] \
        + ([card("NAXIS3", nc)] if nc == 3 else [])


def siril_apply(ctx, arr, ops, tag):
    """Apply siril image commands to an in-memory float array by round-
    tripping through a temp FITS: write, `load`, run <ops>, `save`, read
    back. The PROCESSING is siril's (the ops); write/load/save/read are I/O.
    Deterministic: the commands driven here (mtf/pm) carry no RNG and the
    float32 FITS round-trips exactly."""
    work, sdir = ctx["work"], ctx["sdir"]
    nc, h, w = arr.shape
    tmp = os.path.join(work, f"siril_{tag}.fit")
    am.write_fits_planes(tmp, _minimal_fits_cards(nc, h, w),
                         np.clip(arr, 0.0, 1.0).astype(np.float32))
    rel = os.path.relpath(tmp, sdir)[:-4]
    run_siril(sdir, ["requires 1.4.0", f"load {rel}"] + list(ops)
              + [f"save {rel}", "close"], f"starcomb_{tag}.gen.ssf")
    _, planes, _ = am.read_fits_planes(tmp)
    os.remove(tmp)
    return planes.astype(arr.dtype)


def siril_combine(ctx, starless, stars, opacity, satu_amt):
    """Recombine + saturate by SIRIL (the tools): screen the star layer over
    the starless with siril `pm` (PixelMath), then siril `satu`. The screen
    blend and the saturation are siril's algorithms; the star-layer opacity
    is folded into the pm expression (a scalar inside the tool). Screen =
    1-(1-starless)(1-stars*opacity). satu background_factor 0 saturates all
    pixels (the render carries no background saturation threshold), hue index
    6 = all hues."""
    work, sdir = ctx["work"], ctx["sdir"]
    nc, h, w = starless.shape
    cards = _minimal_fits_cards(nc, h, w)
    sl = os.path.join(work, "combine_starless.fit")
    stf = os.path.join(work, "combine_stars.fit")
    out = os.path.join(work, "combine_out.fit")
    am.write_fits_planes(sl, cards, np.clip(starless, 0, 1).astype(np.float32))
    am.write_fits_planes(stf, cards, np.clip(stars, 0, 1).astype(np.float32))
    relsl = os.path.relpath(sl, sdir)[:-4]
    relst = os.path.relpath(stf, sdir)[:-4]
    relout = os.path.relpath(out, sdir)[:-4]
    star_term = (f"${relst}$" if float(opacity) == 1.0
                 else f"${relst}$ * {float(opacity):g}")
    lines = ["requires 1.4.0",
             f'pm "1 - (1 - ${relsl}$) * (1 - {star_term})"']
    if satu_amt and float(satu_amt) > 0:
        lines.append(f"satu {float(satu_amt):g} 0 6")
    lines += [f"save {relout}", "close"]
    run_siril(sdir, lines, "starcomb_combine.gen.ssf")
    _, planes, _ = am.read_fits_planes(out)
    for f in (sl, stf, out):
        if os.path.exists(f):
            os.remove(f)
    return planes.astype(starless.dtype)


def _stage(ctx, name, arr, stretched, note="", extra=None):
    """Per-stage visibility — STANDING on every build (unless
    --no-stage-vis). One consistent full-frame image + one metrics row per
    processing stage, in chain order, so the treatment at each step is
    visible and a defect in the final render localizes to the stage that
    introduced it — every build, not on demand. Linear stages go through
    the shared inspection autostretch; stretched stages are display-
    referred and shown as-is.

    Always prints a one-line stage metric to the log (the textual trace,
    even when images are disabled); writes the full-frame JPEG + metrics
    row when a stage dir is active. This is a DIAGNOSTIC surface — it never
    touches the float artifact chain, so determinism is unaffected, and it
    is NOT the aesthetic-judgment surface (that stays the full-frame
    lossless finals from judgment_package)."""
    g = arr[min(1, arr.shape[0] - 1)]
    bg, sig = am.bg_stats(g)
    p99 = float(np.percentile(g[::4, ::4], 99))
    tail = ("  " + "  ".join(f"{k} {v}" for k, v in extra.items())) \
        if extra else ""
    print(f"[stage] {name}: bg {bg:.5f} sigma {sig:.6f} p99 {p99:.5f}{tail}")
    d = ctx.get("stage_dir")
    if not d:
        return
    import json as _json
    from PIL import Image
    os.makedirs(d, exist_ok=True)
    n = len([f for f in os.listdir(d) if f.endswith(".jpg")])
    if stretched:
        u8 = (np.clip(arr.transpose(1, 2, 0), 0, 1) * 255 + .5).astype(np.uint8)
    else:
        u8 = am.autostretch_u8(arr)
    # full-frame, high quality: a diagnostic surface inspected at native
    # scale (the user's stage-image choice), never downsampled
    Image.fromarray(u8).save(os.path.join(d, f"{n:02d}_{name}.jpg"),
                             quality=93)
    rec = {"stage": name, "stretched": bool(stretched),
           "bg_g": round(float(bg), 6), "sigma_g": round(float(sig), 7),
           "p99_g": round(p99, 6), "note": note}
    if extra:
        rec.update(extra)
    with open(os.path.join(d, "metrics.jsonl"), "a") as f:
        f.write(_json.dumps(rec) + "\n")


def _write_stage_index(ctx):
    """Assemble index.html + index.md over the stage sequence: the labeled,
    ordered full-frame stage images + their metrics in chain order, so the
    whole treatment of one build reads as a sequence in one place."""
    d = ctx.get("stage_dir")
    if not d or not os.path.exists(os.path.join(d, "metrics.jsonl")):
        return
    import json as _json
    rows = [_json.loads(x) for x in
            open(os.path.join(d, "metrics.jsonl")) if x.strip()]
    jpgs = sorted(f for f in os.listdir(d) if f.endswith(".jpg"))
    std = ("stage", "stretched", "bg_g", "sigma_g", "p99_g", "note")
    md = [f"# Render stage sequence — {ctx.get('set', '?')}", "",
          "Full-frame diagnostic images, one per processing stage, in chain",
          "order. DIAGNOSTIC surface (how the image is treated at each",
          "step) — aesthetics are judged on the lossless finals, never here.",
          "", "| # | stage | bg_g | sigma_g | p99_g | note |",
          "|---|---|---|---|---|---|"]
    html = ["<!doctype html><meta charset=utf-8>",
            f"<title>stages {ctx.get('set', '?')}</title>",
            "<style>body{background:#111;color:#ddd;font:14px sans-serif;"
            "margin:0 auto;max-width:1100px;padding:1em}img{width:100%;"
            "border:1px solid #333}h2{margin:1.4em 0 .2em}"
            "pre{color:#9c9;white-space:pre-wrap;margin:.2em 0}</style>",
            f"<h1>Render stages — {ctx.get('set', '?')}</h1>",
            "<p>Diagnostic full-frame sequence in chain order. Aesthetics "
            "are judged on the lossless finals, not here.</p>"]
    for i, jpg in enumerate(jpgs):
        r = rows[i] if i < len(rows) else {}
        note = r.get("note", "")
        md.append(f"| {i:02d} | {r.get('stage', '')} | {r.get('bg_g', '')} "
                  f"| {r.get('sigma_g', '')} | {r.get('p99_g', '')} | "
                  f"{note} |")
        extra = {k: v for k, v in r.items() if k not in std}
        html.append(f"<h2>{i:02d} — {r.get('stage', '')}</h2>")
        html.append(f"<pre>bg {r.get('bg_g', '')}  sigma "
                    f"{r.get('sigma_g', '')}  p99 {r.get('p99_g', '')}"
                    + (f"  {extra}" if extra else "")
                    + (f"\n{note}" if note else "") + "</pre>")
        html.append(f"<img src='{jpg}'>")
    open(os.path.join(d, "index.md"), "w").write("\n".join(md) + "\n")
    open(os.path.join(d, "index.html"), "w").write("\n".join(html) + "\n")
    print(f"[stage] sequence + index -> "
          f"{os.path.relpath(d, ctx['sdir'])}/index.html")


def render_config(ctx, cfg, jpg_out):
    """Run one configuration; returns metrics dict (also writes jpg)."""
    sdir, work = ctx["sdir"], ctx["work"]
    if ctx.get("stage_vis"):
        # per-render stage-visibility dir, fresh so the sequence counter
        # resets: <final without ext>_stages/, beside the final it explains.
        # Single renders, ladder values and sweep renders each get their own
        # labeled full-frame sequence + index.
        import glob
        import shutil as _sh
        sd = jpg_out[:-4] + "_stages"
        if os.path.exists(sd):
            _sh.rmtree(sd)
        # disk hygiene: full-frame stage JPEGs accumulate every build, so
        # keep only the most recent single/sweep stage dirs for this set
        # (ladder stage dirs live under their exp_ dir and are untouched)
        old = sorted(glob.glob(os.path.join(
            os.path.dirname(jpg_out),
            f"starcomb_{ctx.get('set', '')}_*_stages")))
        for p in old[:-3]:
            _sh.rmtree(p, ignore_errors=True)
        os.makedirs(sd, exist_ok=True)
        ctx = {**ctx, "stage_dir": sd}
    st_out = os.path.join(work, "starless_st.fit")
    if os.path.exists(st_out):
        os.remove(st_out)
    # Background removed on the STAR-FUL linear (the standard order and
    # the only one measured MW-safe: gx on starless erased the MW +38 ->
    # +0.4), THEN separation; the starless branch only denoises/stretches.
    bgelin = ensure_bge_linear(ctx, mode=cfg.get("bgelin_mode", "gx"))
    if ctx.get("stage_dir"):
        b, _ = am.load_image(bgelin)
        _stage(ctx, "bgelin", b, False,
               f"background: bgelin_mode={cfg.get('bgelin_mode', 'gx')} "
               "(BGE'd linear, star-ful)")
        del b
    starless_fit, stars_fit, cat_npz = ensure_starsep(
        ctx["repo"], sdir, bgelin, prom=cfg.get("sep_prom", 6.0),
        set_name=ctx.get("set"),
        engine=cfg.get("sep_engine", "auto"))
    ctx = {**ctx, "stars_fit": stars_fit, "cat_npz": cat_npz}
    if ctx.get("stage_dir"):
        b, _ = am.load_image(starless_fit)
        _stage(ctx, "starless_linear", b, False,
               f"star separation: sep_engine={cfg.get('sep_engine', 'auto')} "
               "(starless layer, linear)")
        del b
    if cfg["starless_denoise"] == "gx":
        # AI denoise, linear, starless (standard step-5 placement; a
        # measured FAIL on this self-flat data, kept as an option because
        # new data may have a different noise structure)
        starless_fit = run_graxpert_denoise(work, starless_fit)
        if ctx.get("stage_dir"):
            b, _ = am.load_image(starless_fit)
            _stage(ctx, "denoise_gx_linear", b, False,
                   "denoise: GraXpert AI (linear, starless — standard "
                   "step-5 placement)")
            del b
    rel = os.path.relpath(starless_fit, sdir)
    suffix = rel[:-5] if rel.endswith(".fits") else rel[:-4]
    lines = ["requires 1.4.0", f"load {suffix}"]
    if cfg["starless_denoise"] == "vst":
        lines.append("denoise -vst")
    # Stretch linkage: unlinked equalizes per-channel backgrounds (cast
    # compensation) but per-channel curves differentially amplify
    # per-channel noise into chroma blotches. On an SPCC-calibrated
    # BROADBAND stack there is no cast to compensate — linked is the
    # standard there. (Narrowband-palette colour+develop is Nightlight's
    # job — nightlight_sho.py — not an in-house per-line numpy stretch.)
    linkflag = "-linked " if cfg.get("stretch_linked") != "unlinked" else ""
    lines.append(f"autostretch {linkflag}-1.5 {cfg['starless_target']}")
    if cfg.get("stretch_mode", "mtf") == "ghs":
        # GHS FINISHING pass on the autostretched starless: SP placed
        # ghs_sp_k sigma ABOVE the stretched sky so the gain lands on the
        # object's mid-tones, not the sky (a single autoghs from linear
        # measured +0.2..+1.1/255 object-above-sky across a full (k,D,b)
        # grid vs the MTF's +6.5 — its gain concentrates at SP, so it
        # cannot replace the MTF; the composite lifts the object 2-3x
        # while siril's default highlight protection (HP 0.7, rgbblend)
        # holds the top).
        lines.append(f"autoghs {linkflag}{float(cfg['ghs_sp_k']):g} "
                     f"{float(cfg['ghs_amount']):g} "
                     f"-b={float(cfg['ghs_focus']):g}")
    if cfg["starless_denoise"] == "vstpost":
        # post-stretch, half-modulated: every linear placement imprints a
        # radial signature on self-flat data (noise is radial after V(r)
        # division and adaptive denoisers smooth it unevenly); after the
        # stretch the differential is already rendered, and -mod blends
        # 50% original back.
        if ctx.get("stage_dir"):
            # vis-only: capture the pre-denoise stretch so denoise shows as
            # its own stage; the float path still loads the denoised
            # starless_st below, so the artifact is unchanged
            lines.append("save work/starless_prestretch_vis")
        lines.append("denoise -vst -mod=0.5")
    lines.append("save work/starless_st")
    lines.append("close")
    run_siril(sdir, lines, "starcomb_starless.gen.ssf")
    starless_st = am.load_linear(st_out)
    os.remove(st_out)  # 294 MB scratch: free it now (all in memory)
    # denoise its own visible stage: the post-stretch VST runs inside the
    # siril stretch call, and a vis-only pre-denoise save (above) lets the
    # stretch and the denoise show as two stages in true chain order
    pre_vis = os.path.join(work, "starless_prestretch_vis.fit")
    pre_dn = (am.load_linear(pre_vis)
              if (ctx.get("stage_dir") and os.path.exists(pre_vis)) else None)

    # A single-filter (mono) stack carries luminance only. Replicate it to RGB
    # so the gate, star-shell audit and 8-bit writers see the three channels
    # they expect, and skip the final saturation (it acts on channel
    # differences that are identically zero here, so it can only cost time).
    mono = starless_st.shape[0] == 1
    if mono:
        starless_st = np.repeat(starless_st, 3, axis=0)
        if pre_dn is not None:
            pre_dn = np.repeat(pre_dn, 3, axis=0)
        print("[starcomb] mono stack -> luminance render "
              "(satu skipped: no colour)")
    ghs_tag = (f" + ghs k{cfg.get('ghs_sp_k')}/D{cfg.get('ghs_amount')}"
               f"/b{cfg.get('ghs_focus')}"
               if cfg.get("stretch_mode", "mtf") == "ghs" else "")
    stretch_lbl = (f"stretch: {cfg.get('stretch_linked')} "
                   f"target {cfg['starless_target']:g}{ghs_tag}")
    if pre_dn is not None:
        # pre-denoise stretch, then the denoise itself, as two stages
        _stage(ctx, "stretch", pre_dn, True, stretch_lbl + " (pre-denoise)")
        _, sig_pre = am.bg_stats(pre_dn[min(1, pre_dn.shape[0] - 1)])
        _, sig_post = am.bg_stats(
            starless_st[min(1, starless_st.shape[0] - 1)])
        drop = 100.0 * (1.0 - sig_post / max(sig_pre, 1e-12))
        _stage(ctx, "denoise", starless_st, True,
               f"denoise: {cfg['starless_denoise']} -mod=0.5 "
               "(post-stretch VST)",
               extra={"sky_sigma_drop_pct": round(float(drop), 1)})
        del pre_dn
    else:
        _stage(ctx, "stretch", starless_st, True,
               stretch_lbl + f" + denoise={cfg['starless_denoise']}")
    if os.path.exists(pre_vis):
        os.remove(pre_vis)

    clip_sky = 0.0
    if cfg.get("black_point", 0) > 0:
        # output black point on the starless layer — the only place the
        # render sets its own zero — driven by siril `mtf b 0.5 1`: a
        # midtones balance of 0.5 is the identity transfer, so `mtf` with a
        # low shadow clip at b is exactly a linear black-point rescale
        # (x-b)/(1-b), no cast, all differences preserved. The clip fraction
        # is MEASURED in numpy (examining); the transform is siril's. Runs
        # BEFORE the gate jpg so QA sees it.
        b = float(cfg["black_point"]) / 255.0
        c2, h2, w2 = starless_st.shape
        keepb = am.branch_mask(h2, w2)
        g2 = min(1, c2 - 1)
        pre = starless_st[g2]
        clip_sky = float(((pre <= b) & keepb).sum() / max(keepb.sum(), 1))
        starless_st = siril_apply(ctx, starless_st, [f"mtf {b:g} 0.5 1"],
                                  "blackpoint")
        print(f"[starcomb] black_point {cfg['black_point']:g}/255 "
              f"[siril mtf {b:g} 0.5 1]: clip0 sky {clip_sky * 100:.2f}%")

    _stage(ctx, "starless_final", starless_st, True,
           f"black_point: {cfg.get('black_point')}/255 — the gate input",
           extra={"clip0_sky_pct": round(clip_sky * 100, 2)})

    # THE GATE (bg_qa on the starless render): a composition-agnostic sky
    # scope (statistical dark-sky blocks, terrestrial foreground excluded)
    # grades color / gradient / blotch / rings. The recombined whole-frame
    # QA below stays a reported reference, never the gate.
    from PIL import Image
    tmp8 = (np.clip(starless_st.transpose(1, 2, 0), 0, 1) * 255 + .5).astype(np.uint8)
    slpath = jpg_out.replace(".jpg", "_starless.jpg")
    Image.fromarray(tmp8).save(slpath, quality=92)
    if ctx.get("lossless"):
        # the q92 jpg above is THE GATE'S pinned identity, never a
        # judgment surface — human eyes get the lossless pair: PNG8 =
        # the exact pixels the gate encoder consumed, PNG16 = the float
        # starless layer itself
        Image.fromarray(tmp8).save(slpath.replace(".jpg", ".png"),
                                   pnginfo=am.png_srgb_info())
        am.write_png16(slpath.replace(".jpg", "_16bit.png"),
                       (np.clip(starless_st.transpose(1, 2, 0), 0, 1)
                        * 65535 + .5).astype(np.uint16))
        print("[starcomb] starless lossless: "
              + os.path.basename(slpath.replace(".jpg", ".png"))
              + " + _16bit.png")
    a_sl = np.asarray(Image.open(slpath), dtype=np.float64)
    qa_sl = bg_qa.qa_metrics(a_sl)
    print(f"[starcomb]   GATE sky floor {qa_sl['floor']:.0f} | color "
          f"{qa_sl['color']:.1f} grad {qa_sl['grad']:.1f} blotch "
          f"{qa_sl['resid']:.1f} rings {qa_sl['ring_l']:.1f} "
          f"({qa_sl['skyfrac']*100:.0f}% sky) -> "
          f"{'PASS' if qa_sl['pass'] else 'FAIL'}")

    # --- stars branch (numpy) --------------------------------------------
    stars = am.load_linear(ctx["stars_fit"])
    if mono:
        stars = np.repeat(stars, 3, axis=0)
    cat = np.load(ctx["cat_npz"])
    if cfg["cull_pct"] > 0:
        flux, ids = cat["flux"], cat["ids"]
        thr = np.percentile(flux, cfg["cull_pct"])
        kill = ids[flux < thr]
        # labels are undilated; dilate the kill mask a little to take the
        # star skirts with the cores
        from scipy import ndimage
        km = np.isin(cat["labels"], kill)
        km = ndimage.binary_dilation(km, iterations=4)
        stars[:, km] = 0.0
        print(f"[starcomb] culled {len(kill)}/{len(ids)} stars "
              f"(< p{cfg['cull_pct']} flux)")
    sigs = None
    if cfg.get("stars_floor", 0) > 0:
        # ghost-aura fix: the skirt annulus (star core -> dilated mask
        # edge) carries subtraction noise that the stars MTF amplifies
        # into a visible halo (measured +7..11 counts luminance / chroma
        # MAD 20-30 vs 6 for an unseparated stretch). Floor the stars
        # layer at k*sigma (per-channel linear sky noise from the linear
        # starless layer) so only genuine star signal reaches the
        # stretch.
        sl_lin = am.load_linear(starless_fit)
        if mono:
            sl_lin = np.repeat(sl_lin, 3, axis=0)
        k = float(cfg["stars_floor"])
        sigs = []
        for c in range(stars.shape[0]):
            _, sig_c = am.bg_stats(sl_lin[c])
            sigs.append(sig_c)
            stars[c] = np.clip(stars[c] - k * sig_c, 0.0, None)
        del sl_lin
        print(f"[starcomb] stars_floor {k}: skirt cored below k*sigma "
              f"(sigma16 {'/'.join(f'{s * 65535:.1f}' for s in sigs)})")
    if cfg.get("stars_anchor", "catalog") == "noise":
        # noise-relative anchor: k * sigma_G of the linear starless —
        # renders the same physical star at the same brightness across
        # rebuilds of the SAME sky (sigma and star amplitudes rescale
        # together). k has NO universal value: it encodes one dataset's
        # star statistics over its noise (a k calibrated on one field is
        # an 11x brightness error on another — measured 44 sigma vs 491
        # sigma anchors on two real fields), so it must come from the
        # dataset's recipe, never a default.
        k = cfg.get("noise_anchor_k")
        if not k:
            sys.exit("starcomb: stars_anchor=noise needs noise_anchor_k in "
                     "the dataset recipe (datasets/<session>/<set>/"
                     "recipe.json). The k is per-dataset by construction — "
                     "calibrate it against this dataset's catalog anchor "
                     "(k = anchor / sigma_G) if same-sky stability is "
                     "wanted; there is no cross-dataset value.")
        k = float(k)
        if sigs:
            sig_g = sigs[min(1, stars.shape[0] - 1)]
        else:
            sl_lin = am.load_linear(starless_fit)
            _, sig_g = am.bg_stats(sl_lin[min(1, sl_lin.shape[0] - 1)])
            del sl_lin
        anchor = float(k * sig_g)
        mode = f"noise ({k:.1f}*sigma_G)"
    else:
        # catalog anchor on the FIXED G/luminance basis: a
        # max-over-channels amplitude follows whichever channel wins, so
        # a per-channel recalibration (SPCC K factors) would move the
        # anchor and drift the low-end gain (measured x864 -> x996
        # between builds of one sky); the G-basis amplitude rescales
        # WITH its channel and cannot drift.
        if "peak_g" not in cat:
            sys.exit(f"starcomb: catalog {ctx['cat_npz']} predates the "
                     "peak_g anchor basis — delete the work/starsep "
                     "cache and re-run so the separator regenerates it")
        amps = np.sort(cat["peak_g"])[::-1]
        anchor = float(np.median(amps[:min(500, len(amps))]))
        mode = "catalog[g]"
    m = solve_mtf_m(anchor, cfg["stars_peak"])
    # print anchor + low-end gain every run so normalization drift stays
    # visible whichever mode is active (evaluating the MTF at one point is a
    # reported diagnostic, not the star render — that is siril below)
    gain0 = am.mtf(1e-4, m) / 1e-4
    print(f"[starcomb] stars anchor {anchor:.4f} [{mode}] -> m {m:.5f} "
          f"(low-end gain x{gain0:.0f})")
    # star layer rendered by siril `mtf 0 m 1` (the midtones transfer with a
    # data-derived anchor m computed above): shadows 0, highlights 1, so it
    # is exactly the single-parameter midtones stretch on the star layer.
    stars_st = siril_apply(ctx, np.clip(stars, 0, 1), [f"mtf 0 {m:g} 1"],
                           "starsmtf")
    _stage(ctx, "stars_mtf", stars_st, True,
           f"star rendering: cull {cfg.get('cull_pct')} / floor "
           f"{cfg.get('stars_floor')} / anchor {mode}",
           extra={"anchor": round(float(anchor), 4), "mtf_m": round(m, 5),
                  "low_end_gain": round(float(gain0), 0)})

    # --- combine (siril) --------------------------------------------------
    # Recombine + saturate by siril: screen the star layer over the starless
    # with siril PixelMath (industry star-subduing folded in as the opacity
    # scalar in the pm expression), then siril `satu` for the final chroma
    # gain. A mono render carries no colour, so satu is skipped.
    k_st = float(cfg.get("stars_opacity", 1.0))
    satu_amt = 0.0 if mono else float(cfg.get("satu", 0) or 0.0)
    out = siril_combine(ctx, starless_st, stars_st, k_st, satu_amt)
    print(f"[starcomb] combine [siril pm screen, stars_opacity {k_st:g}]"
          + (f" + satu {satu_amt:g} [siril satu]" if satu_amt > 0 else ""))
    _stage(ctx, "combine", out, True,
           f"combine: siril pm screen (stars_opacity {cfg.get('stars_opacity', 1.0)}) "
           f"+ siril satu {cfg.get('satu')}")
    u8 = (np.clip(out.transpose(1, 2, 0), 0, 1) * 255 + .5).astype(np.uint8)
    # Final-export encoding, measured vs the lossless PNG on this
    # grain-heavy content: q92 + default 4:2:0 subsampling costs mean
    # 2.29 counts / max 176 at star edges / 9.7 star-pixel chroma error;
    # q100 + subsampling=0 costs mean 0.44 / max 5. Finals carry embedded
    # sRGB colorimetry (JPEG ICC + PNG sRGB/gAMA/cHRM — the render output is
    # display-referred sRGB-companded; pixels are untouched). The STARLESS
    # jpg (gate input) is untouched entirely — its q92 encoding is part of
    # the gate identity.
    jq = int(cfg.get("jpg_quality", 100))
    jsub = int(cfg.get("jpg_subsampling", 0))
    if jsub < 0:
        Image.fromarray(u8).save(jpg_out, quality=jq,
                                 icc_profile=am.srgb_icc())
    else:
        Image.fromarray(u8).save(jpg_out, quality=jq, subsampling=jsub,
                                 icc_profile=am.srgb_icc())
    if ctx.get("lossless"):
        # lossless deliverables: 8-bit PNG (deflate is lossless; the same
        # pixels the JPEG quantizes — the byte-verification artifact) and
        # a 16-bit PNG quantized straight from the float render (65536
        # levels vs 256: everything the chain computes, in a file viewers
        # can open)
        png_out = jpg_out[:-4] + ".png"
        Image.fromarray(u8).save(png_out, pnginfo=am.png_srgb_info())
        print(f"[starcomb] lossless PNG: {png_out}")
        u16 = (np.clip(out.transpose(1, 2, 0), 0, 1) * 65535.0
               + 0.5).astype(np.uint16)
        png16_out = jpg_out[:-4] + "_16bit.png"
        am.write_png16(png16_out, u16)
        print(f"[starcomb] 16-bit PNG: {png16_out}")

    # REPORTED star-shell metrics (the ghost-aura defect class — lives ON
    # stars where the background gate cannot see it; WARN-only)
    shell = am.star_shell_report(u8, ctx["cat_npz"])
    warn = ""
    if shell["aura_lum"] is not None:
        over = [k for k, b in am.STAR_SHELL_WARN.items()
                if shell[k] is not None and shell[k] > b]
        warn = ("  WARN: " + ",".join(over) + " over bound") if over else ""
    print(f"[starcomb]   star shells: aura_lum "
          f"{shell['aura_lum']:+.1f} (warn >{am.STAR_SHELL_WARN['aura_lum']}) "
          f"| shell_chroma {shell['shell_chroma']:.1f} (trend, no bound) "
          f"| n {shell['n_sample']}{warn}")

    # standing OBJECT-INTEGRITY audit (WARN-only): grade the OBJECT region the
    # gate is blind to, against this render's OWN input stack (same balance,
    # co-registered). Reliable for chroma-neutralization + coring mottle;
    # gross-flattening for structure (a small local hollow is an upstream
    # alignment concern, not this render audit — see the tool's docstring).
    oi = subprocess.run(
        [sys.executable, os.path.join(ctx["repo"], "scripts", "qa",
                                      "object_integrity.py"),
         jpg_out, ctx["stack"], "--session", sdir, "--set", ctx["set"]],
        capture_output=True, text=True)
    if oi.stdout.strip():
        print(oi.stdout.rstrip())

    _write_stage_index(ctx)

    qa, smet, lev = rh.measure_jpg(jpg_out)
    met = {"qa": {k: v for k, v in qa.items()
                  if isinstance(v, (int, float, bool))},
           "qa_starless": {k: v for k, v in qa_sl.items()
                           if isinstance(v, (int, float, bool))},
           "stars": smet, "bg_med8": lev[1]["median"] * 255.0,
           "star_shells": shell,
           "starless_jpg": os.path.basename(slpath)}
    if ctx.get("lossless"):
        # metrics sidecar beside the lossless final so the comparison
        # harness (judgment_package) auto-discovers each candidate's
        # measured numbers and computes control-relative deltas
        with open(jpg_out[:-4] + ".metrics.json", "w") as f:
            json.dump(met, f, indent=1)
    return met


# The knob SCHEMA lives in code (argparse flags, enum validation, the
# render logic); the generic VALUES live in the tracked config
# datasets/GENERIC.json — the base layer every render inherits, with a
# per-knob "why" note naming what each value encodes and its known class
# limits. A dataset's recipe overrides per knob; CLI overrides both. The
# file and this schema must agree exactly or the render refuses to run.
KNOBS = (
    "bgelin_mode",
    "starless_target", "starless_denoise", "stretch_mode", "ghs_sp_k",
    "ghs_amount", "ghs_focus", "sep_prom", "sep_engine",
    "stretch_linked", "satu",
    "cull_pct", "stars_peak", "stars_anchor", "stars_floor",
    "stars_opacity",
    "black_point", "jpg_quality", "jpg_subsampling", "noise_anchor_k",
)

ENUM_CHOICES = {
    "bgelin_mode": ["gx", "plane", "off"],
    "starless_denoise": ["off", "vst", "gx", "vstpost"],
    "stretch_mode": ["mtf", "ghs"],
    "sep_engine": ["auto", "inpaint", "net"],
    "stretch_linked": ["auto", "unlinked", "linked"],
    "stars_anchor": ["catalog", "noise"],
}


def load_generic(repo):
    """datasets/GENERIC.json 'render' values, validated against KNOBS —
    missing file or a key mismatch is repo corruption, never a silent
    code fallback."""
    p = os.path.join(repo, "datasets", "GENERIC.json")
    if not os.path.exists(p):
        sys.exit(f"starcomb: {p} missing — the generic base layer is a "
                 "tracked file; restore it from git")
    vals = json.load(open(p)).get("render", {})
    if set(vals) != set(KNOBS):
        missing = set(KNOBS) - set(vals)
        extra = set(vals) - set(KNOBS)
        sys.exit(f"starcomb: datasets/GENERIC.json disagrees with the knob "
                 f"schema (missing {sorted(missing)}, unknown "
                 f"{sorted(extra)}) — fix the file, the schema owns the "
                 "knob set")
    return vals


def resolve_recipe(repo, sdir, set_name, args):
    """CLI > datasets/<session>/<set>/recipe.json > datasets/GENERIC.json,
    per knob. Prints where each non-generic value came from; a dataset
    with no recipe file renders generic and says so — it never inherits
    another dataset's look."""
    generic = load_generic(repo)
    recipe_p = os.path.join(am.dataset_dir(sdir, set_name), "recipe.json")
    recipe, rec = {}, {}
    if os.path.exists(recipe_p):
        rec = json.load(open(recipe_p))
        recipe = rec.get("render", {})
        unknown = set(recipe) - set(KNOBS)
        if unknown:
            sys.exit(f"starcomb: unknown recipe knobs {sorted(unknown)} in "
                     f"{recipe_p}")
        print(f"[recipe] {rec.get('dataset', set_name)}: "
              f"{rec.get('status', 'provisional')}"
              + (f" — {rec['approved']}" if rec.get("approved") else ""))
    else:
        print(f"[recipe] NONE for {set_name} — GENERIC defaults "
              "(honest but not an approved look); create "
              f"{os.path.relpath(recipe_p)} to pin one. First render of a "
              "NEW data class? Run the new-class triage ladders (README, "
              "experiment discipline) before any judgment package")
    base, srcs = {}, []
    for k in KNOBS:
        cli = getattr(args, k)
        if cli is not None:
            base[k] = cli
            srcs.append(f"{k}={cli!r}(cli)")
        elif k in recipe:
            base[k] = recipe[k]
            srcs.append(f"{k}={recipe[k]!r}")
        else:
            base[k] = generic[k]
        if k in ENUM_CHOICES and base[k] is not None \
                and base[k] not in ENUM_CHOICES[k]:
            sys.exit(f"starcomb: {k}={base[k]!r} not in {ENUM_CHOICES[k]}")
    if base["stretch_linked"] == "auto":
        # In-house starcomb serves the broadband/mono class: one calibrated
        # scene, one linked transfer. Narrowband-palette colour+develop is
        # Nightlight's job (render_engine routes an SHO composition to
        # nightlight_sho.py before this chain runs), so auto = linked here.
        base["stretch_linked"] = "linked"
        if bool(rec.get("spcc", {}).get("narrowband")):
            print("[recipe] stretch_linked auto -> linked. NOTE: this is a "
                  "narrowband set on the in-house chain (a linked stretch "
                  "renders the dominant line only) — the honest narrowband "
                  "render is Nightlight (render_engine=nightlight / "
                  "nightlight_sho.py).")
        else:
            print("[recipe] stretch_linked auto -> linked (broadband/mono: "
                  "single linked stretch)")
    if srcs:
        print("[recipe] non-generic: " + " ".join(srcs))
    return base


def _experiments_path(sdir, set_name):
    return os.path.join(am.dataset_dir(sdir, set_name), "experiments.jsonl")


def ledger_append(sdir, set_name, entry):
    """Append one experiment record to the TRACKED per-dataset ledger
    (datasets/<session>/<set>/experiments.jsonl): a durable index of what
    was laddered, its pinned inputs, and its verdict. The heavy per-value
    finals stay in gitignored results/exp_*/; this is the record that
    outlives them. Append-only; a verdict closes the entry in place by its
    exp name."""
    p = _experiments_path(sdir, set_name)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "a") as f:
        f.write(json.dumps(entry, sort_keys=True) + "\n")


def ledger_close(sdir, set_name, exp_name, verdict, because):
    """Close a PENDING experiment (matched by its exp dir name) with its
    verdict + measured reason — the round-trip the discipline requires: a
    measurement that kills a hypothesis is recorded, never left open.
    Rewrites the small ledger."""
    p = _experiments_path(sdir, set_name)
    if not os.path.exists(p):
        sys.exit(f"starcomb: no experiments ledger at "
                 f"{os.path.relpath(p)} — run the ladder first")
    recs = [json.loads(x) for x in open(p) if x.strip()]
    hit = [r for r in recs if r.get("exp") == exp_name]
    if not hit:
        openx = [r["exp"] for r in recs if r.get("verdict") == "PENDING"]
        sys.exit(f"starcomb: no experiment {exp_name!r} in "
                 f"{os.path.relpath(p)} (open: {openx})")
    for r in hit:
        r["verdict"], r["because"] = verdict, because
    with open(p, "w") as f:
        for r in recs:
            f.write(json.dumps(r, sort_keys=True) + "\n")
    return hit[0]


def close_experiment(sdir, set_name, exp_dir, verdict, because):
    """The --verdict closing step: stamp the ledger AND the exp dir's
    human-facing hypothesis.md so the record is complete in both places."""
    if not because:
        sys.exit("starcomb: --verdict requires --because \"<the measured "
                 "reason>\" — a killed hypothesis is recorded WITH ITS "
                 "NUMBERS, not left open (experiment discipline)")
    exp_name = os.path.basename(os.path.normpath(exp_dir))
    ledger_close(sdir, set_name, exp_name, verdict, because)
    hp = os.path.join(exp_dir, "hypothesis.md")
    if os.path.exists(hp):
        with open(hp, "a") as f:
            f.write(f"\n## Verdict: {verdict.upper()}\n\n{because}\n")
    print(f"[starcomb] experiment {exp_name} closed: {verdict.upper()} — "
          f"{because}")
    if verdict == "deadend":
        print("[starcomb] REMINDER: a dead end becomes a NOTES dead-end "
              "entry WITH ITS NUMBERS (the mechanism why), per the "
              "experiment discipline — the ledger indexes it, NOTES states "
              "the mechanism.")


def resolve_engine(sdir, set_name):
    """Which RENDER ENGINE a dataset uses: `render_engine` in recipe.json
    (auto|starcomb|nightlight), auto-resolved. A mono-filters NARROWBAND
    (SHO) composition defaults to `nightlight` — the reference author's own
    tool, whose star-neutral colour balance recovers the O3 sphere that our
    chain's SPCC photometric fit equalises away (NOTES dead ends). Everything
    else is `starcomb`, the in-house chain."""
    dsdir = am.dataset_dir(sdir, set_name)
    recipe = {}
    p = os.path.join(dsdir, "recipe.json")
    if os.path.exists(p):
        recipe = json.load(open(p))
    eng = recipe.get("render_engine", "auto")
    if eng not in ("auto", "starcomb", "nightlight"):
        sys.exit(f"starcomb: render_engine={eng!r} in {p} not in "
                 "auto|starcomb|nightlight")
    if eng != "auto":
        return eng
    comp_p = os.path.join(dsdir, "composition.json")
    if os.path.exists(comp_p):
        comp = json.load(open(comp_p))
        if comp.get("kind") == "mono-filters" \
                and bool(recipe.get("spcc", {}).get("narrowband")):
            return "nightlight"
    return "starcomb"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("session")
    ap.add_argument("set")
    # Run against the SPCC-calibrated stack:
    #   starcomb.py <session> <set> --stack results/stack_<set>_spcc.fit
    # Knob defaults resolve CLI > dataset recipe > datasets/GENERIC.json
    # (see resolve_recipe); the generic values were each set by a measured
    # single-knob ladder and carry per-knob provenance in that file.
    ap.add_argument("--bgelin-mode", default=None,
                    choices=ENUM_CHOICES["bgelin_mode"],
                    help="linear background handling: gx = GraXpert AI "
                         "BGE + subsky 1 (full extraction; absorbs "
                         "frame-filling faint nebulosity), plane = "
                         "subsky 1 only, off = passthrough")
    ap.add_argument("--starless-target", type=float, default=None)
    ap.add_argument("--stretch-mode", default=None,
                    choices=ENUM_CHOICES["stretch_mode"],
                    help="mtf = linked autostretch only (generic); ghs = "
                         "autostretch + autoghs FINISHING pass (SP above "
                         "the stretched sky lifts the object's mid-tones; "
                         "a single autoghs from linear cannot replace the "
                         "MTF — measured)")
    ap.add_argument("--ghs-sp-k", type=float, default=None,
                    help="ghs finishing: SP = stretched-sky median + "
                         "k*sigma (higher k = gain lands higher above the "
                         "sky, sky stays darker)")
    ap.add_argument("--ghs-amount", type=float, default=None,
                    help="ghs finishing stretch amount D")
    ap.add_argument("--ghs-focus", type=float, default=None,
                    help="ghs finishing focus b (siril default 13 is too "
                         "SP-concentrated for object lifting — measured)")
    ap.add_argument("--starless-denoise", default=None,
                    choices=ENUM_CHOICES["starless_denoise"],
                    help="vstpost = post-stretch -vst -mod=0.5 (generic). "
                         "vst/gx are the LINEAR placements: measured FAIL "
                         "on self-flat data (radial imprint) — standard "
                         "rungs for data classes without that structure")
    ap.add_argument("--sep-prom", type=float, default=None,
                    help="starsep component prominence cut (sigma); lower "
                         "moves the faint tail into the stars layer "
                         "(measured null on this data)")
    ap.add_argument("--sep-engine", default=None,
                    choices=ENUM_CHOICES["sep_engine"],
                    help="star separation engine: net = StarNet2 ONNX "
                         "(fail-safe on resolved objects; bright-star "
                         "shell is its worst case), inpaint = mask+"
                         "inpaint (destroys resolved-object structure — "
                         "it warns when it measures that risk), auto = "
                         "net when the weights are installed else "
                         "inpaint (generic)")
    ap.add_argument("--stretch-linked", default=None,
                    choices=ENUM_CHOICES["stretch_linked"],
                    help="siril autostretch channel coupling: linked = one "
                         "transfer (broadband standard); unlinked = "
                         "per-channel SKY-anchored (cast compensation; "
                         "amplifies channel noise into chroma blotches — a "
                         "measurement rung); auto = linked (generic). "
                         "Narrowband colour+develop is Nightlight's job, not "
                         "an in-house stretch mode.")
    ap.add_argument("--stars-opacity", type=float, default=None,
                    help="screen combine with stars*k — star-field "
                         "subduing (industry reduced-opacity "
                         "recombine); 1 = plain screen")
    ap.add_argument("--satu", type=float, default=None,
                    help="final chroma gain by siril `satu` on the combined "
                         "render (amplifies surviving colour: star hues, "
                         "honest tint); 0 = off")
    ap.add_argument("--cull-pct", type=float, default=None)
    ap.add_argument("--stars-peak", type=float, default=None)
    ap.add_argument("--stars-anchor", default=None,
                    choices=ENUM_CHOICES["stars_anchor"],
                    help="MTF anchor source: catalog = median top-500 "
                         "G-basis catalog amplitude, noise = k*sigma_G "
                         "with k from the dataset recipe (same-sky "
                         "stability tool; k is per-dataset by "
                         "construction)")
    ap.add_argument("--noise-anchor-k", type=float, default=None,
                    help="k for stars_anchor=noise (per-dataset; no "
                         "generic value exists)")
    ap.add_argument("--stars-floor", type=float, default=None,
                    help="core the stars layer below k*sigma (linear) "
                         "before its MTF — kills the amplified-skirt "
                         "ghost aura around stars; 0 = off")
    ap.add_argument("--black-point", type=float, default=None,
                    help="output black point on the starless layer, "
                         "8-bit counts (bg ~16 -> ~8); 0 = off")
    ap.add_argument("--stack", default=None,
                    help="override input stack path (default "
                         "results/stack_<set>.fit) — for pipeline-variant "
                         "stacks, e.g. stack_<set>_bgeonly.fit")
    ap.add_argument("--tag", default=None)
    ap.add_argument("--jpg-quality", type=int, default=None,
                    help="final jpg quality (generic 100 + subsampling 0 "
                         "= mean 0.44 counts vs the lossless PNG)")
    ap.add_argument("--jpg-subsampling", type=int, default=None,
                    help="PIL subsampling for the final jpg (0=4:4:4; "
                         "-1=encoder default 4:2:0)")
    ap.add_argument("--lossless", action="store_true",
                    help="also write a lossless PNG next to each jpg")
    ap.add_argument("--metrics-out", default=None,
                    help="write the single-run metrics dict to this JSON "
                         "path (the no-regression sweep's interface)")
    ap.add_argument("--no-stage-vis", action="store_true",
                    help="disable per-stage visibility (default ON, EVERY "
                         "build): the labeled full-frame stage sequence "
                         "(background -> separation -> stretch -> denoise -> "
                         "black point -> stars -> combine) + index.html "
                         "written beside each final as <final>_stages/ — "
                         "the escape hatch for a fast run")
    ap.add_argument("--inspect", action="store_true",
                    help="deprecated no-op: per-stage visibility is now "
                         "standing on every build (see --no-stage-vis)")
    ap.add_argument("--param", default=None,
                    choices=["bgelin_mode",
                             "starless_target", "starless_denoise",
                             "stretch_mode", "ghs_sp_k", "ghs_amount",
                             "ghs_focus",
                             "cull_pct", "stars_peak", "stars_anchor",
                             "sep_prom", "sep_engine",
                             "satu", "stretch_linked", "stars_opacity",
                             "stars_floor", "black_point"])
    ap.add_argument("--values", default=None)
    ap.add_argument("--hypothesis", default=None)
    # experiment close-out (no render): record the judged outcome of a
    # ladder back into the tracked per-dataset ledger + its hypothesis.md
    ap.add_argument("--verdict", default=None,
                    choices=["win", "null", "deadend"],
                    help="close a laddered experiment (needs --exp + "
                         "--because): win = a value pins, null = no "
                         "measured difference, deadend = killed (then a "
                         "NOTES dead-end entry with its numbers)")
    ap.add_argument("--because", default=None,
                    help="the measured reason for --verdict (required)")
    ap.add_argument("--exp", default=None,
                    help="the results/exp_<param>_<stamp>/ dir to close "
                         "(printed at the ladder's STOP)")
    args = ap.parse_args()

    # repo root is three up: this file is scripts/render/starcomb.py
    repo = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    sdir = os.path.join(repo, args.session)
    if args.verdict:
        # close-out mode: no render, no stack needed
        if not args.exp:
            sys.exit("starcomb: --verdict needs --exp <results/exp_*/ dir> "
                     "(the ladder prints the exact command at its STOP)")
        exp_dir = args.exp if os.path.isabs(args.exp) \
            else os.path.join(repo, args.exp)
        close_experiment(sdir, args.set, exp_dir, args.verdict, args.because)
        return
    # render-engine routing (BEFORE the stack check: a nightlight dataset has
    # no single stack_<set>.fit — it composes per-channel member stacks). A
    # ladder (--param) or an explicit --stack stays on the in-house chain.
    if not args.param and not args.stack:
        engine = resolve_engine(sdir, args.set)
        if engine == "nightlight":
            print(f"[starcomb] render_engine=nightlight — delegating "
                  f"{args.set} to nightlight_sho.py (SHO narrowband: the "
                  "author's tool, star-neutral balance recovers the O3 "
                  "sphere our SPCC equalises)")
            cmd = [sys.executable,
                   os.path.join(repo, "scripts", "render", "nightlight_sho.py"),
                   args.session, args.set]
            if args.lossless:
                cmd.append("--lossless")
            sys.exit(subprocess.run(cmd).returncode)
    work = os.path.join(sdir, "work")
    os.makedirs(work, exist_ok=True)  # render scratch (bgelin, gen scripts, starsep); not guaranteed to exist
    stack = (os.path.abspath(args.stack) if args.stack
             else os.path.join(sdir, "results", f"stack_{args.set}.fit"))
    if not os.path.exists(stack):
        sys.exit(f"starcomb: no {stack}")
    if not stack.lower().endswith((".fit", ".fits", ".fts")):
        sys.exit(f"starcomb: --stack must be a linear FITS, got {stack} "
                 "(jpg/png are QA/judgment surfaces, never inputs)")
    # per-set geometry (terrestrial foreground only): the dataset's
    # geometry.json, else foreground none — never silent inheritance of
    # another set's mask
    am.configure(sdir, args.set)
    stamp = time.strftime("%Y%m%d_%H%M%S")
    ctx = {"repo": repo, "sdir": sdir, "work": work, "stack": stack,
           "set": args.set, "lossless": args.lossless,
           "stage_vis": not args.no_stage_vis}

    base = resolve_recipe(repo, sdir, args.set, args)
    if not args.param:
        tag = args.tag or "single"
        out = os.path.join(sdir, "results", f"starcomb_{args.set}_{tag}_{stamp}.jpg")
        met = render_config(ctx, base, out)
        met["recipe"] = base
        print(json.dumps(met, indent=1))
        if args.metrics_out:
            met["jpg"] = out
            with open(args.metrics_out, "w") as f:
                json.dump(met, f, indent=1)
        print(f"[starcomb] wrote {out}")
        return

    if not args.hypothesis:
        sys.exit("starcomb: ladders require --hypothesis (discipline)")
    # every ladder value is a judgment surface: lossless, always
    ctx = {**ctx, "lossless": True}
    enum_params = ("bgelin_mode", "starless_denoise",
                   "stretch_mode", "stretch_linked",
                   "sep_engine", "stars_anchor")
    vals = []
    for v in args.values.split(","):
        v = v.strip()
        vals.append(v if args.param in enum_params else float(v))
    cur = base[args.param]
    if cur not in vals:
        vals.append(cur)
        print(f"[starcomb] control value {cur!r} added to the ladder")
    if args.param not in enum_params:
        vals = sorted(vals)

    exp_dir = os.path.join(sdir, "results", f"exp_{args.param}_{stamp}")
    os.makedirs(exp_dir, exist_ok=True)
    st = os.stat(stack)
    with open(os.path.join(exp_dir, "hypothesis.md"), "w") as f:
        f.write(f"# Experiment: {args.param}\n\n"
                f"- **hypothesis**: {args.hypothesis}\n"
                f"- **values**: {vals} (control {cur!r})\n"
                f"- **fixed**: {base}\n"
                f"- **pinned stack**: size {st.st_size} mtime {int(st.st_mtime)}\n\n"
                "Verdict: PENDING USER JUDGMENT\n")
    # durable, TRACKED index of the experiment (the per-value finals below
    # live in gitignored results/); closed later by --verdict
    ledger_append(sdir, args.set, {
        "exp": os.path.basename(exp_dir), "stamp": stamp,
        "param": args.param, "values": [str(v) for v in vals],
        "control": str(cur), "hypothesis": args.hypothesis,
        "stack_size": st.st_size, "stack_mtime": int(st.st_mtime),
        "verdict": "PENDING"})

    results = []
    for i, v in enumerate(vals):
        cfg = dict(base)
        cfg[args.param] = v
        jpg = os.path.join(exp_dir, f"v{i}_{rh.sanitize(v)}.jpg")
        print(f"[starcomb] value {v!r}")
        met = render_config(ctx, cfg, jpg)
        met["value"] = v
        met["jpg"] = os.path.basename(jpg)
        met["crop"] = 0
        results.append(met)
        q, qs, s = met["qa"], met["qa_starless"], met["stars"]
        print(f"[starcomb]   GATE starless {'PASS' if qs['pass'] else 'FAIL'} "
              f"color {qs['color']:.1f} grad {qs['grad']:.1f} blotch "
              f"{qs['resid']:.1f} rings {qs['ring_l']:.1f} | ref whole-frame "
              f"{'PASS' if q['pass'] else 'FAIL'} color {q['color']:.1f} "
              f"grad {q['grad']:.1f} | stars mid "
              f"{(s.get('mid_peak_med') or 0) * 255:.0f} sat "
              f"{(s.get('sat_star_frac') or 0) * 100:.0f}%")

    with open(os.path.join(exp_dir, "metrics.jsonl"), "w") as f:
        for r in results:
            f.write(json.dumps(r) + "\n")

    cols = ["value", "GATE", "SLcolor", "SLgrad", "SLblotch", "SLringL",
            "refQA", "bg", "stars", "mid pk", "sat%", "halo"]
    rows = []
    for r in results:
        q, qs, s = r["qa"], r["qa_starless"], r["stars"]
        rows.append([str(r["value"]), "PASS" if qs["pass"] else "FAIL",
                     f"{qs['color']:.1f}", f"{qs['grad']:.1f}",
                     f"{qs['resid']:.1f}", f"{qs['ring_l']:.1f}",
                     "PASS" if q["pass"] else "FAIL",
                     f"{r['bg_med8']:.0f}",
                     str(s.get("n_stars", 0)),
                     rh.fmt((s.get("mid_peak_med") or 0) * 255, "{:.0f}"),
                     rh.fmt((s.get("sat_star_frac") or 0) * 100, "{:.0f}"),
                     rh.fmt(s.get("halo_med"))])
    widths = [max(len(c), *(len(r[j]) for r in rows)) for j, c in enumerate(cols)]
    print()
    print("  ".join(c.ljust(widths[j]) for j, c in enumerate(cols)))
    print("-" * (sum(widths) + 2 * len(widths)))
    for r in rows:
        print("  ".join(r[j].ljust(widths[j]) for j in range(len(cols))))
    md = ["| " + " | ".join(cols) + " |",
          "|" + "|".join("---" for _ in cols) + "|"]
    md += ["| " + " | ".join(r) + " |" for r in rows]
    with open(os.path.join(exp_dir, "hypothesis.md"), "a") as f:
        f.write("\n## Results\n\n" + "\n".join(md) + "\n")

    print(f"\n[starcomb] STOP — user judgment required: open the per-value "
          f"FULL lossless finals in {exp_dir}/ independently (no panels, "
          "no crops — the judge sees whole frames in their own viewer)")
    print("[starcomb] once judged, record the outcome (closes the ledger):\n"
          f"  python3 scripts/render/starcomb.py {args.session} {args.set} "
          f"--verdict win|null|deadend --because \"...\" "
          f"--exp {os.path.relpath(exp_dir, repo)}")


if __name__ == "__main__":
    main()
