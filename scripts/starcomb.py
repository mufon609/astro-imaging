#!/usr/bin/env python3
"""Starless/stars split processing + recombination (standard-DSO style).

The product chain. Defaults = APPROVED RECIPE B6 (2026-07-06, session 5;
see NOTES.md "APPROVED RECIPE — B6"):

  starcomb.py <session> <set> --stack results/stack_<set>_spcc.fit [--lossless]

Chain (each knob set by a measured single-knob ladder; input is the
SPCC-calibrated stack — solve_field.py --inject + siril spcc):
  1. GraXpert BGE + subsky 1 on the STAR-FUL linear (cached; the only
     order measured MW-safe — BGE on starless ERASES the MW)
  2. starsep.py mask+inpaint separation (cached)
  starless: LINKED autostretch -1.5 <starless_target=0.07>
    -> post-stretch denoise -vst -mod=0.5 (<starless_denoise=vstpost>;
       every linear placement imprints a radial signature on self-flat
       data)
    -> chroma_core <4>  (multi-scale Wiener chroma coring, PRE-boost)
    -> lum_core <2>     (sky-only luminance coring; corridor protected)
    -> mw_boost <1.2> on the LUMINOSITY-WEIGHTED corridor mask
       (<boost_mask=lum>; the flat geometric gain lifted noise floor and
       dark gaps alongside the glow)
  stars: faint components culled below the <cull_pct=50> flux
    percentile, gray MTF anchored so the median top-500 amplitude
    renders at <stars_peak=0.97>
  combine: screen 1-(1-a)(1-b) -> satu <0.2> -> JPEG q92 [+ PNG].

Ladder mode (single knob, control auto-bracketed, STOPS for judgment):
  starcomb.py <session> <set> --stack ... --param mw_boost \\
      --values 0.8,1.6 --hypothesis "..."

Reported per configuration: THE GATE = bg_qa starless-sky scope
(corridor+branch masked, thresholds never loosen) on the starless
render; whole-frame bg_qa on the recombine as reference; corridor_report
(floor delta / along-band chroma / seam texture — the costs the gate
scope cannot see); star metrics; MW-vs-dark-sky box contrast.

Refuted/superseded paths were removed from this file with their numbers
kept in NOTES.md (sep_first order + numpy background models S5-S7,
chroma_nr blur H, vst_after_boost G).
"""
import argparse
import json
import os
import subprocess
import sys
import time

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import astrometrics as am  # noqa: E402
import bg_qa  # noqa: E402
import experiment as exp  # noqa: E402  (run_graxpert, strips, measure_jpg)

# MW core vs dark-sky boxes (fractions of w,h; display orientation).
MW_BOX = (0.40, 0.30, 0.70, 0.55)
SKY_BOX = (0.05, 0.25, 0.25, 0.50)

# MW band corridor geometry lives in astrometrics (shared with bg_qa's
# layer-appropriate sky scope); names re-exported for existing callers.
from astrometrics import BAND_P0, BAND_P1, BAND_HALFW, band_mask_frac  # noqa: E402,F401


def box_median_g(img_chw, box):
    c, h, w = img_chw.shape
    x0, y0, x1, y1 = (int(box[0] * w), int(box[1] * h),
                      int(box[2] * w), int(box[3] * h))
    return float(np.median(img_chw[min(1, c - 1), y0:y1, x0:x1]))


def run_siril(session_dir, lines, name):
    p = os.path.join(session_dir, "work", name)
    with open(p, "w") as f:
        f.write("\n".join(lines) + "\n")
    r = subprocess.run(["flatpak", "run", "--command=siril-cli",
                        "org.siril.Siril", "-d", session_dir, "-s", p],
                       capture_output=True, text=True)
    if r.returncode != 0:
        sys.exit(f"starcomb: siril failed ({name}):\n" + r.stdout[-2500:])


def ensure_starsep(repo, sdir, input_fit, prom=6.0):
    """Run (cached) star separation on any linear FITS. prom = the
    component prominence cut in sigma (starsep K_PROM; lower moves the
    faint 4-6 sigma tail out of the starless layer into the stars layer,
    where cull_pct can reach it)."""
    outdir = os.path.join(sdir, "work", "starsep")
    cmd = [sys.executable, os.path.join(repo, "scripts", "starsep.py"),
           input_fit, outdir]
    if prom != 6.0:
        cmd.append(f"--prom={prom:g}")
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        sys.exit("starcomb: starsep failed:\n" + r.stdout[-2000:] + r.stderr[-1000:])
    print(r.stdout.rstrip())
    paths = [l for l in r.stdout.strip().splitlines() if l.endswith((".fit", ".npz"))]
    return paths[-3], paths[-2], paths[-1]


def ensure_bge_linear(ctx):
    """GraXpert BGE + subsky 1 on the STAR-FUL stack (the order the
    standard workflow uses, and the only one measured MW-safe here: gx on
    starless erased the MW +38 -> +0.4, gx on the star-ful stack kept it),
    cached by stack identity."""
    sdir, work, stack = ctx["sdir"], ctx["work"], ctx["stack"]
    st = os.stat(stack)
    out = os.path.join(work, f"bgelin_{st.st_size}_{int(st.st_mtime)}.fit")
    if os.path.exists(out):
        print(f"[starcomb] bge-linear cache hit {os.path.basename(out)}")
        return out
    gx = exp.run_graxpert(stack, work,
                          lambda m: print(f"[starcomb] {m}", flush=True))
    rel_gx = os.path.relpath(gx, sdir)
    rel_out = os.path.relpath(out, sdir)
    run_siril(sdir, ["requires 1.4.0",
                     f"load {rel_gx[:-5] if rel_gx.endswith('.fits') else rel_gx}",
                     "subsky 1 -dither",
                     f"save {rel_out[:-4]}",
                     "close"], "starcomb_bgelin.gen.ssf")
    return out


def chroma_core(starless_st, k=3.0):
    """Multi-scale significance coring of chroma toward NEUTRAL.

    The stretch amplifies per-channel noise into colored blotches at ALL
    scales (measured 1-3 counts at 16-128 px on a linear floor of ~0.1);
    blurring chroma just moves speckle up in scale, and saturation then
    re-amplifies it. Instead: decompose R-G and B-G into a gaussian
    pyramid (sigma 2/8/32/128 + residual), measure each level's noise on
    the corridor-excluded sky, and Wiener-shrink each level by its local
    energy e/(e + (k*sigma)^2). Chroma that is not significantly above
    its own noise goes to gray; genuinely colored signal (bright star
    hues, real tint standing above noise) passes near-unchanged by
    construction. G (luminance) is never touched."""
    from scipy.ndimage import gaussian_filter
    import bg_qa
    c, h, w = starless_st.shape
    g2 = min(1, c - 1)
    G = starless_st[g2]
    sky = ~bg_qa.sky_signal_mask(h, w) & am.branch_mask(h, w)
    out = {0: None, 2: None}
    for ci in (0, 2):
        cch = starless_st[ci] - G
        levels = []
        prev = cch
        for s in (2, 8, 32, 128):
            sm = gaussian_filter(cch, s)
            levels.append(prev - sm)
            prev = sm
        levels.append(prev)                      # sigma-128 residual
        rec = np.zeros_like(cch)
        for lev in levels:
            v = lev[sky]
            sig = 1.4826 * np.median(np.abs(v - np.median(v)))
            e = gaussian_filter(lev * lev, 4)
            rec += lev * (e / (e + (k * sig) ** 2 + 1e-20))
        out[ci] = rec
    R = np.clip(G + out[0], 0.0, 1.0)
    B = np.clip(G + out[2], 0.0, 1.0)
    print(f"[starcomb] chroma_core k={k}: insignificant chroma -> neutral")
    return np.clip(np.stack([R, G, B]), 0.0, 1.0)


def lum_core(starless_st, k=3.0):
    """Sky-only LUMINANCE significance coring — the gray-patch fix.

    The stretch amplifies G noise into 1.2-2.7 counts of mid-scale gray
    patchiness on a sky whose linear floor is 0.06-0.10 (measured); with
    the chroma cored to neutral, the eye picks up that luminance
    unevenness. The sky is supposed to be FLAT (the gate's own premise),
    so mid-scale sky structure below significance is shrunk toward the
    smooth background: gaussian pyramid (sigma 8/32/128) of G, per-level
    sky-noise, Wiener shrinkage. The correction is applied identically to
    R/G/B (no chroma created) and ONLY on the sky — the MW corridor
    (feathered) and branch keep their honest structure untouched."""
    from scipy.ndimage import gaussian_filter
    import bg_qa
    c, h, w = starless_st.shape
    g2 = min(1, c - 1)
    G = starless_st[g2].astype(np.float64)
    # M0 (session 5): NO branch factor in the applied weight. The hard
    # branch rectangle printed a seam (measured 4.5x blotch-texture step
    # at y=0.75h on B5), and even feathered it leaves a rectangle of
    # un-cored patchy sky. The Wiener gate below already protects real
    # structure (trees/halo energy >> noise => correction ~ 0), so the
    # geometric protection was redundant for the foreground and harmful
    # for the sky sharing its rectangle. The branch stays excluded from
    # the noise ESTIMATE (skyb, hard mask — statistics scope).
    sky_w = 1.0 - band_mask_frac(h, w, feather=0.10)
    skyb = (sky_w > 0.9) & am.branch_mask(h, w)
    levels = []
    prev = G
    for s in (8, 32, 128):
        sm = gaussian_filter(G, s)
        levels.append(prev - sm)
        prev = sm
    correction = np.zeros_like(G)
    for lev in levels:
        v = lev[skyb]
        sig = 1.4826 * np.median(np.abs(v - np.median(v)))
        e = gaussian_filter(lev * lev, 4)
        keep_frac = e / (e + (k * sig) ** 2 + 1e-20)
        correction += lev * (1.0 - keep_frac)
    correction *= sky_w
    out = np.clip(starless_st - correction[None, :, :], 0.0, 1.0)
    print(f"[starcomb] lum_core k={k}: insignificant sky luminance -> "
          f"smooth bg (corridor/branch protected)")
    return out.astype(starless_st.dtype)


def run_graxpert_denoise(work, fit):
    """GraXpert AI denoising on a linear FITS (Ladder D rung 'gx'),
    cached by input identity. Standard-order placement: linear, on the
    STARLESS layer, before the stretch."""
    st = os.stat(fit)
    out = os.path.join(work, f"gxdn_{st.st_size}_{int(st.st_mtime)}.fits")
    if os.path.exists(out):
        print(f"[starcomb] gx-denoise cache hit {os.path.basename(out)}")
        return out
    print("[starcomb] graxpert denoising (linear, starless) ...", flush=True)
    r = subprocess.run([exp.GRAXPERT, "-cmd", "denoising", fit,
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


def render_config(ctx, cfg, jpg_out):
    """Run one configuration; returns metrics dict (also writes jpg)."""
    sdir, work = ctx["sdir"], ctx["work"]
    st_out = os.path.join(work, "starless_st.fit")
    if os.path.exists(st_out):
        os.remove(st_out)
    # Background removed on the STAR-FUL linear (the standard order and
    # the only one measured MW-safe: gx on starless erased the MW +38 ->
    # +0.4), THEN separation; the starless branch only denoises/stretches.
    # (A sep_first order + three numpy background models lived here until
    # session 5 — all REFUTED, numbers in NOTES S5-S7.)
    bgelin = ensure_bge_linear(ctx)
    starless_fit, stars_fit, cat_npz = ensure_starsep(
        ctx["repo"], sdir, bgelin, prom=cfg.get("sep_prom", 6.0))
    ctx = {**ctx, "stars_fit": stars_fit, "cat_npz": cat_npz}
    if cfg["starless_denoise"] == "gx":
        # AI denoise, linear, starless (standard step-5 placement; a
        # measured FAIL on this self-flat data — kept as a ladder rung
        # because new data changes the noise structure)
        starless_fit = run_graxpert_denoise(work, starless_fit)
    rel = os.path.relpath(starless_fit, sdir)
    suffix = rel[:-5] if rel.endswith(".fits") else rel[:-4]
    lines = ["requires 1.4.0", f"load {suffix}"]
    if cfg["starless_denoise"] == "vst":
        lines.append("denoise -vst")
    # Stretch linkage: unlinked was the historical cast bandaid (per-
    # channel bg equalization) and is also the chroma-blotch engine
    # (per-channel curves differentially amplify per-channel noise).
    # On the SPCC-calibrated stack there is no cast to compensate —
    # linked is the standard, tested by ladder J2.
    linkflag = "-linked " if cfg.get("stretch_linked") == "linked" else ""
    lines.append(f"autostretch {linkflag}-1.5 {cfg['starless_target']}")
    if cfg["starless_denoise"] == "vstpost":
        # post-stretch, half-modulated: the linear placements imprint a
        # radial signature (Ladder D); after the stretch the radial noise
        # differential is already rendered, and -mod blends 50% original
        # back — the halved-ring hypothesis from the star-ful near miss.
        lines.append("denoise -vst -mod=0.5")
    lines.append("save work/starless_st")
    lines.append("close")
    run_siril(sdir, lines, "starcomb_starless.gen.ssf")
    starless_st, _ = am.load_image(st_out)

    if cfg.get("chroma_core", 0) > 0 and cfg.get("core_order", "pre") == "pre":
        # coring BEFORE the boost (default): thresholds are calibrated on
        # the un-boosted sky, so they are valid frame-wide; the boost then
        # amplifies already-neutralized chroma and cannot re-create color.
        # (post-boost coring left boosted corridor noise-chroma alive —
        # the user's "leftover coloration toward the middle", ladder J3.)
        starless_st = chroma_core(starless_st, float(cfg["chroma_core"]))

    if cfg.get("lum_core", 0) > 0:
        starless_st = lum_core(starless_st, float(cfg["lum_core"]))

    if cfg.get("mw_boost", 0) > 0:
        # band-localized midtone lift on the stretched starless layer:
        # out = bg + (x - bg) * (1 + k*M). Lifts the MW's above-background
        # signal without touching the rim (corridor only), stars (separate
        # layer) or the background level. The branch is excluded smoothly
        # (M0: the flat mask used to lift the branch halo too).
        c2, h2, w2 = starless_st.shape
        M = (band_mask_frac(h2, w2, feather=0.10)
             * (1.0 - am.branch_mask_frac(h2, w2, feather=0.05)))
        g2 = min(1, c2 - 1)
        bglev, _ = am.bg_stats(starless_st[g2])
        k = float(cfg["mw_boost"])
        if cfg.get("boost_mask", "geo") == "lum":
            # M1: LUMINOSITY-WEIGHTED lift (the standard luminosity-mask /
            # masked-stretch idiom) — the geometric corridor gain is flat,
            # so it multiplies the noise floor and the dark gaps by the
            # same (1+k) as the glow (measured: corridor starless floor
            # P50 +7 counts over sky = the user's issue 3). Weighting the
            # corridor by the smoothed above-bg glow makes the lift follow
            # the actual signal; gaps and floor stay at sky black. The
            # weight is capped at 1 so k keeps the same meaning at the
            # glow peaks; it can only reduce the lift elsewhere.
            from scipy.ndimage import gaussian_filter
            sig = gaussian_filter(
                np.maximum(starless_st[g2] - bglev, 0.0), 64)
            core = M > 0.5
            ref = float(np.percentile(sig[core], 95)) if core.any() else 0.0
            if ref > 1e-6:
                M = M * np.clip(sig / ref, 0.0, 1.0).astype(np.float32)
                print(f"[starcomb] boost_mask lum: glow-weighted "
                      f"(ref p95 {ref * 255:.1f} counts)")
        gain = 1.0 + k * M
        starless_st = np.clip(
            bglev + (starless_st - bglev) * gain[None, :, :], 0.0, 1.0)
        print(f"[starcomb] mw_boost {k}: band lift around bg {bglev:.3f}")

    if cfg.get("chroma_core", 0) > 0 and cfg.get("core_order", "pre") == "post":
        starless_st = chroma_core(starless_st, float(cfg["chroma_core"]))

    # THE GATE (layer-appropriate QA, ratified 2026-07-06): strict
    # blocks/rings on the starless render's SKY — MW corridor (incl. the
    # boost feather zone) + branch masked as known signal/non-sky,
    # thresholds byte-identical. The recombined whole-frame QA below stays
    # as a reported reference, never the gate.
    from PIL import Image
    tmp8 = (np.clip(starless_st.transpose(1, 2, 0), 0, 1) * 255 + .5).astype(np.uint8)
    slpath = jpg_out.replace(".jpg", "_starless.jpg")
    Image.fromarray(tmp8).save(slpath, quality=92)
    a_sl = np.asarray(Image.open(slpath), dtype=np.float64)
    qa_sl = bg_qa.qa_metrics(
        a_sl, bg_qa.sky_signal_mask(a_sl.shape[0], a_sl.shape[1]))
    # REPORTED corridor + seam metrics (session 5): the gate masks the
    # corridor, so corridor-contained costs (boost floor lift, chroma
    # bands) and mask seams need their own numbers — reported, never gated.
    corr = am.corridor_report(tmp8)
    print(f"[starcomb]   corridor floor Δ P50 {corr['floor_p50']:+.1f} / "
          f"P5 {corr['floor_p5']:+.1f} | band chroma RG {corr['band_rg']:.1f} "
          f"BG {corr['band_bg']:.1f} | seam tex y {corr['seam_y']:.2f} "
          f"x {corr['seam_x']:.2f} (1=none)")

    # --- stars branch (numpy) --------------------------------------------
    stars, _ = am.load_image(ctx["stars_fit"])
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
    amps = np.sort(cat["peak"])[::-1]
    anchor = float(np.median(amps[:min(500, len(amps))]))
    m = solve_mtf_m(anchor, cfg["stars_peak"])
    stars_st = am.mtf(np.clip(stars, 0, 1), m)

    # --- combine ----------------------------------------------------------
    out = 1.0 - (1.0 - np.clip(starless_st, 0, 1)) * (1.0 - np.clip(stars_st, 0, 1))
    if cfg.get("satu", 0) > 0:
        # chroma gain on the combined render, AFTER the corings — so it
        # amplifies only significant (surviving) color: star hues and
        # honest MW tint, not noise chroma (I'/M5).
        s = float(cfg["satu"])
        mean = out.mean(axis=0, keepdims=True)
        out = np.clip(mean + (1.0 + s) * (out - mean), 0.0, 1.0)
        print(f"[starcomb] satu {s}: chroma gain on the combined render")
    u8 = (np.clip(out.transpose(1, 2, 0), 0, 1) * 255 + .5).astype(np.uint8)
    Image.fromarray(u8).save(jpg_out, quality=92)
    if ctx.get("lossless"):
        # lossless deliverable: PNG (deflate is lossless), same 8-bit
        # pixels the JPEG quantizes — for final-product verification
        png_out = jpg_out[:-4] + ".png"
        Image.fromarray(u8).save(png_out)
        print(f"[starcomb] lossless PNG: {png_out}")

    qa, smet, lev = exp.measure_jpg(jpg_out)
    a8 = np.asarray(Image.open(jpg_out), dtype=np.float32).transpose(2, 0, 1)
    mw = box_median_g(a8, MW_BOX) - box_median_g(a8, SKY_BOX)
    return {"qa": {k: v for k, v in qa.items() if isinstance(v, (int, float, bool))},
            "qa_starless": {k: v for k, v in qa_sl.items()
                            if isinstance(v, (int, float, bool))},
            "stars": smet, "bg_med8": lev[1]["median"] * 255.0,
            "mw_contrast8": mw, "corridor": corr,
            "starless_jpg": os.path.basename(slpath)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("session")
    ap.add_argument("set")
    # Defaults = the APPROVED RECIPE B5 (2026-07-06, user-approved; see
    # NOTES.md "APPROVED RECIPE"). Run against the SPCC-calibrated stack:
    #   starcomb.py <session> <set> --stack results/stack_<set>_spcc.fit
    # Every default below was set by a measured single-knob ladder.
    ap.add_argument("--starless-target", type=float, default=0.07)
    ap.add_argument("--starless-denoise", default="vstpost",
                    choices=["off", "vst", "gx", "vstpost"],
                    help="vstpost = post-stretch -vst -mod=0.5 (B6). vst/gx "
                         "are the LINEAR placements: measured FAIL on "
                         "self-flat data (radial imprint, NOTES ladder D) — "
                         "kept as rungs for future data")
    ap.add_argument("--sep-prom", type=float, default=6.0,
                    help="starsep component prominence cut (sigma); lower "
                         "moves the faint tail into the stars layer "
                         "(measured NULL on this data, NOTES F)")
    ap.add_argument("--chroma-core", type=float, default=4,
                    help="significance k for multi-scale chroma coring "
                         "toward neutral; 0 = off")
    ap.add_argument("--lum-core", type=float, default=2,
                    help="significance k for sky-only luminance coring "
                         "(gray-patch fix); 0 = off")
    ap.add_argument("--core-order", default="pre", choices=["pre", "post"],
                    help="chroma coring before (pre, default) or after "
                         "(post) the mw_boost")
    ap.add_argument("--stretch-linked", default="linked",
                    choices=["unlinked", "linked"],
                    help="autostretch channel linkage (unlinked = the "
                         "historical cast bandaid, retired by J2; linked = "
                         "standard on a calibrated stack)")
    ap.add_argument("--satu", type=float, default=0.2,
                    help="chroma gain on the combined render, AFTER the "
                         "corings (amplifies only significant color); "
                         "0 = off")
    ap.add_argument("--cull-pct", type=float, default=50)
    ap.add_argument("--stars-peak", type=float, default=0.97)
    ap.add_argument("--mw-boost", type=float, default=1.2)
    ap.add_argument("--boost-mask", default="lum", choices=["geo", "lum"],
                    help="mw_boost mask: geo = flat geometric corridor "
                         "(control; lifts glow AND floor/gaps by 1+k), "
                         "lum = corridor x glow-luminosity weight (M1: "
                         "lift follows the signal, gaps stay at sky black)")
    ap.add_argument("--stack", default=None,
                    help="override input stack path (default "
                         "results/stack_<set>.fit) — for pipeline-variant "
                         "stacks, e.g. stack_set-03_bgeonly.fit")
    ap.add_argument("--tag", default=None)
    ap.add_argument("--lossless", action="store_true",
                    help="also write a lossless PNG next to each jpg")
    ap.add_argument("--param", default=None,
                    choices=["starless_target", "starless_denoise",
                             "cull_pct", "stars_peak", "mw_boost",
                             "sep_prom", "chroma_core", "satu",
                             "core_order", "stretch_linked", "lum_core",
                             "boost_mask"])
    ap.add_argument("--values", default=None)
    ap.add_argument("--hypothesis", default=None)
    args = ap.parse_args()

    # Defaults = APPROVED RECIPE B6 (2026-07-06 session 5, user-approved:
    # "C1 chain + the far-right judgment panel" = the C3_maxremoval render).
    # Delta to B5: boost_mask lum (M1), chroma_core 4 (M3), satu 0.2 (M5);
    # cull stays 50 (M4, the user's max-removal pole). See NOTES "APPROVED
    # RECIPE — B6".
    repo = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    sdir = os.path.join(repo, args.session)
    work = os.path.join(sdir, "work")
    stack = (os.path.abspath(args.stack) if args.stack
             else os.path.join(sdir, "results", f"stack_{args.set}.fit"))
    if not os.path.exists(stack):
        sys.exit(f"starcomb: no {stack}")
    ctx = {"repo": repo, "sdir": sdir, "work": work, "stack": stack,
           "lossless": args.lossless}

    base = {"starless_target": args.starless_target,
            "starless_denoise": args.starless_denoise,
            "cull_pct": args.cull_pct, "stars_peak": args.stars_peak,
            "mw_boost": args.mw_boost, "boost_mask": args.boost_mask,
            "sep_prom": args.sep_prom,
            "chroma_core": args.chroma_core, "satu": args.satu,
            "core_order": args.core_order,
            "stretch_linked": args.stretch_linked,
            "lum_core": args.lum_core}

    stamp = time.strftime("%Y%m%d_%H%M%S")
    if not args.param:
        tag = args.tag or "single"
        out = os.path.join(sdir, "results", f"starcomb_{args.set}_{tag}_{stamp}.jpg")
        met = render_config(ctx, base, out)
        print(json.dumps(met, indent=1))
        print(f"[starcomb] wrote {out}")
        return

    if not args.hypothesis:
        sys.exit("starcomb: ladders require --hypothesis (discipline)")
    enum_params = ("starless_denoise", "core_order", "stretch_linked",
                   "boost_mask")
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

    exp_dir = os.path.join(sdir, "results",
                           f"exp_starsep_{args.param}_{stamp}")
    os.makedirs(exp_dir, exist_ok=True)
    st = os.stat(stack)
    with open(os.path.join(exp_dir, "hypothesis.md"), "w") as f:
        f.write(f"# Starsep experiment: {args.param}\n\n"
                f"- **hypothesis**: {args.hypothesis}\n"
                f"- **values**: {vals} (control {cur!r})\n"
                f"- **fixed**: {base}\n"
                f"- **pinned stack**: size {st.st_size} mtime {int(st.st_mtime)}\n\n"
                "Verdict: PENDING USER JUDGMENT\n")

    results = []
    for i, v in enumerate(vals):
        cfg = dict(base)
        cfg[args.param] = v
        jpg = os.path.join(exp_dir, f"v{i}_{exp.sanitize(v)}.jpg")
        print(f"[starcomb] value {v!r}")
        met = render_config(ctx, cfg, jpg)
        met["value"] = v
        met["jpg"] = os.path.basename(jpg)
        met["crop"] = 0
        results.append(met)
        q, qs, s = met["qa"], met["qa_starless"], met["stars"]
        print(f"[starcomb]   GATE starless-sky {'PASS' if qs['pass'] else 'FAIL'} "
              f"blocks {qs['ratio']:.2f} rings {qs['ring_l']:.1f}/{qs['ring_rg']:.1f}/{qs['ring_bg']:.1f}"
              f" | ref whole-frame {'PASS' if q['pass'] else 'FAIL'} "
              f"blocks {q['ratio']:.2f} rings {q['ring_l']:.1f}/{q['ring_rg']:.1f}/{q['ring_bg']:.1f}"
              f" | MW contrast {met['mw_contrast8']:.1f} | stars mid "
              f"{(s.get('mid_peak_med') or 0) * 255:.0f} sat "
              f"{(s.get('sat_star_frac') or 0) * 100:.0f}%")

    with open(os.path.join(exp_dir, "metrics.jsonl"), "w") as f:
        for r in results:
            f.write(json.dumps(r) + "\n")

    cols = ["value", "GATE", "SLblk", "SLringL", "SLringRG", "SLringBG",
            "refQA", "blocks", "ring L", "MW", "bg", "stars", "mid pk",
            "sat%", "halo"]
    rows = []
    for r in results:
        q, qs, s = r["qa"], r["qa_starless"], r["stars"]
        rows.append([str(r["value"]), "PASS" if qs["pass"] else "FAIL",
                     f"{qs['ratio']:.2f}", f"{qs['ring_l']:.1f}",
                     f"{qs['ring_rg']:.1f}", f"{qs['ring_bg']:.1f}",
                     "PASS" if q["pass"] else "FAIL",
                     f"{q['ratio']:.2f}", f"{q['ring_l']:.1f}",
                     f"{r['mw_contrast8']:.1f}", f"{r['bg_med8']:.0f}",
                     str(s.get("n_stars", 0)),
                     exp.fmt((s.get("mid_peak_med") or 0) * 255, "{:.0f}"),
                     exp.fmt((s.get("sat_star_frac") or 0) * 100, "{:.0f}"),
                     exp.fmt(s.get("halo_med"))])
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

    sx = exp.star_region(stack)
    strips = [exp.value_row(os.path.join(exp_dir, r["jpg"]), 0, sx)
              for r in results]
    labels = [f"{args.param} = {r['value']}   "
              f"[{'PASS' if r['qa_starless']['pass'] else 'FAIL'}]"
              for r in results]
    exp.compose_rows(strips, labels, os.path.join(exp_dir, "side_by_side.jpg"))
    print(f"\n[starcomb] STOP — user judgment required. Review {exp_dir}/")


if __name__ == "__main__":
    main()
