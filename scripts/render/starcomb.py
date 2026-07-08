#!/usr/bin/env python3
"""Starless/stars split processing + recombination (standard-DSO style).

The product chain. Defaults = the user-approved recipe B7 (byte-verified
to reproduce the approved render; recipe provenance in NOTES.md):

  starcomb.py <session> <set> --stack results/stack_<set>_norgbeq_spcc.fit [--lossless]

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
    -> black_point <8> (output levels on the starless layer: bg ~16 ->
       ~8; gaps clip to true black, the lifted MW glow sits above the
       clip by measurement)
  stars: faint components culled below the <cull_pct=50> flux
    percentile, skirt cored below <stars_floor=3.0> x sigma (the
    ghost-aura fix: only genuine star signal reaches the stretch), gray
    MTF anchored so the median top-500 amplitude renders at
    <stars_peak=0.97>
  combine: screen 1-(1-a)(1-b) -> satu <0.2> -> JPEG q100/4:4:4 [+ PNG].

Ladder mode (single knob, control auto-bracketed, STOPS for judgment):
  starcomb.py <session> <set> --stack ... --param mw_boost \\
      --values 0.8,1.6 --hypothesis "..."

Reported per configuration: THE GATE = bg_qa starless-sky scope
(corridor+branch masked, thresholds never loosen) on the starless
render; whole-frame bg_qa on the recombine as reference; corridor_report
(floor delta / along-band chroma / seam texture — the costs the gate
scope cannot see); star metrics; MW-vs-dark-sky box contrast.
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

# All corridor / foreground / report-box geometry lives in the per-set
# context (astrometrics.CTX): main() calls am.configure(session, set,
# stack) — config_<set>.json values, else WCS-derived corridor, else none
# (warned). An unconfigured CTX carries no geometry (none/None), so a
# forgotten configure() degrades loudly, never to set-03's masks.
from astrometrics import band_mask_frac  # noqa: E402


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
    """One separation subprocess; returns its starless/stars/catalog
    trio (the last three printed paths — cache hits print the same)."""
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
    paths = [l for l in r.stdout.strip().splitlines() if l.endswith((".fit", ".npz"))]
    return paths[-3], paths[-2], paths[-1]


def ensure_starsep(repo, sdir, input_fit, prom=6.0, set_name=None,
                   engine="inpaint"):
    """Run (cached) star separation on any linear FITS. engine picks the
    separator: 'inpaint' = starsep.py mask+inpaint (detection-bounded:
    leaves the <6 sigma faint tail in the starless layer); 'net' =
    starnet_sep.py StarNet2 ONNX inference (removes the faint tail but
    leaves a halo pedestal under bright stars); 'hybrid' = the net run
    ON the inpaint starless (flat-filled bright disks + net faint-tail
    removal; stars recomputed against the stack). prom = the component
    prominence cut in sigma (inpaint detection only). All engines run
    as subprocesses, so the per-set geometry context is passed
    explicitly, and all print the same starless/stars/catalog trio."""
    if prom != 6.0 and engine != "inpaint":
        # the net has no prominence cut, and the hybrid's cache stem
        # does not encode prom — only the default-prom base is valid
        print(f"[starcomb] sep_prom ignored by the {engine} engine")
        prom = 6.0
    prom_args = [f"--prom={prom:g}"] if prom != 6.0 else []
    if engine == "net":
        return _run_sep(repo, sdir, "starnet_sep.py", input_fit, set_name)
    trio = _run_sep(repo, sdir, "starsep.py", input_fit, set_name,
                    prom_args)
    if engine != "hybrid":
        return trio
    return _run_sep(repo, sdir, "starnet_sep.py", input_fit, set_name,
                    [f"--base-starless={trio[0]}"])


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
    gx = rh.run_graxpert(stack, work,
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
    # NO foreground factor in the applied weight: a hard rectangle
    # multiplied into the correction prints a seam (measured 4.5x
    # blotch-texture step at its edge), and even feathered it leaves a
    # rectangle of un-cored patchy sky. The Wiener gate below already
    # protects real structure (trees/halo energy >> noise => correction
    # ~ 0) — geometric protection is redundant for the foreground and
    # harmful for the sky sharing its rectangle. The foreground stays
    # excluded from the noise ESTIMATE (skyb, hard mask — statistics
    # scope).
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


def render_config(ctx, cfg, jpg_out):
    """Run one configuration; returns metrics dict (also writes jpg)."""
    sdir, work = ctx["sdir"], ctx["work"]
    st_out = os.path.join(work, "starless_st.fit")
    if os.path.exists(st_out):
        os.remove(st_out)
    # Background removed on the STAR-FUL linear (the standard order and
    # the only one measured MW-safe: gx on starless erased the MW +38 ->
    # +0.4), THEN separation; the starless branch only denoises/stretches.
    bgelin = ensure_bge_linear(ctx)
    starless_fit, stars_fit, cat_npz = ensure_starsep(
        ctx["repo"], sdir, bgelin, prom=cfg.get("sep_prom", 6.0),
        set_name=ctx.get("set"),
        engine=cfg.get("sep_engine", "inpaint"))
    ctx = {**ctx, "stars_fit": stars_fit, "cat_npz": cat_npz}
    if cfg["starless_denoise"] == "gx":
        # AI denoise, linear, starless (standard step-5 placement; a
        # measured FAIL on this self-flat data, kept as an option because
        # new data may have a different noise structure)
        starless_fit = run_graxpert_denoise(work, starless_fit)
    rel = os.path.relpath(starless_fit, sdir)
    suffix = rel[:-5] if rel.endswith(".fits") else rel[:-4]
    lines = ["requires 1.4.0", f"load {suffix}"]
    if cfg["starless_denoise"] == "vst":
        lines.append("denoise -vst")
    # Stretch linkage: unlinked equalizes per-channel backgrounds (cast
    # compensation) but per-channel curves differentially amplify
    # per-channel noise into chroma blotches. On an SPCC-calibrated
    # stack there is no cast to compensate — linked is the standard.
    linkflag = "-linked " if cfg.get("stretch_linked") == "linked" else ""
    lines.append(f"autostretch {linkflag}-1.5 {cfg['starless_target']}")
    if cfg["starless_denoise"] == "vstpost":
        # post-stretch, half-modulated: every linear placement imprints a
        # radial signature on self-flat data (noise is radial after V(r)
        # division and adaptive denoisers smooth it unevenly); after the
        # stretch the differential is already rendered, and -mod blends
        # 50% original back.
        lines.append("denoise -vst -mod=0.5")
    lines.append("save work/starless_st")
    lines.append("close")
    run_siril(sdir, lines, "starcomb_starless.gen.ssf")
    starless_st, _ = am.load_image(st_out)
    os.remove(st_out)  # 294 MB scratch: free it now (all in memory)

    if cfg.get("chroma_core", 0) > 0 and cfg.get("core_order", "pre") == "pre":
        # coring BEFORE the boost (default): thresholds are calibrated on
        # the un-boosted sky, so they are valid frame-wide; the boost then
        # amplifies already-neutralized chroma and cannot re-create color.
        # (post-boost coring leaves boosted corridor noise-chroma alive —
        # measured as leftover coloration toward the frame middle.)
        starless_st = chroma_core(starless_st, float(cfg["chroma_core"]))

    if cfg.get("lum_core", 0) > 0:
        starless_st = lum_core(starless_st, float(cfg["lum_core"]))

    if cfg.get("mw_boost", 0) > 0 and am.CTX.corridor_mode == "none":
        print("[starcomb] WARNING: mw_boost skipped — no corridor defined "
              "for this set (no config, no WCS)")
    elif cfg.get("mw_boost", 0) > 0:
        # band-localized midtone lift on the stretched starless layer:
        # out = bg + (x - bg) * (1 + k*M). Lifts the MW's above-background
        # signal without touching the rim (corridor only), stars (separate
        # layer) or the background level. The foreground is excluded
        # smoothly (a flat mask would lift the tree halo too).
        c2, h2, w2 = starless_st.shape
        M = (band_mask_frac(h2, w2, feather=0.10)
             * (1.0 - am.branch_mask_frac(h2, w2, feather=0.05)))
        g2 = min(1, c2 - 1)
        bglev, _ = am.bg_stats(starless_st[g2])
        k = float(cfg["mw_boost"])
        if cfg.get("boost_mask", "geo") == "lum":
            # LUMINOSITY-WEIGHTED lift (the standard luminosity-mask /
            # masked-stretch idiom) — a flat geometric corridor gain
            # multiplies the noise floor and the dark gaps by the same
            # (1+k) as the glow (measured: corridor starless floor P50
            # +7 counts over sky). Weighting the corridor by the
            # smoothed above-bg glow makes the lift follow the actual
            # signal; gaps and floor stay at sky black. The weight is
            # capped at 1 so k keeps the same meaning at the glow peaks;
            # it can only reduce the lift elsewhere.
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

    if cfg.get("black_point", 0) > 0:
        # output black point on the starless layer — the only place the
        # render sets its own zero. Linear + linked (no cast, differences
        # preserved), AFTER the boost so the lifted MW sits above the
        # clip, BEFORE the gate jpg so QA sees it.
        b = float(cfg["black_point"]) / 255.0
        c2, h2, w2 = starless_st.shape
        corr_m = band_mask_frac(h2, w2, feather=0.10) > 0.5
        keepb = am.branch_mask(h2, w2)
        g2 = min(1, c2 - 1)
        pre = starless_st[g2]
        clip_cor = float(((pre <= b) & corr_m & keepb).sum()
                         / max((corr_m & keepb).sum(), 1))
        clip_sky = float(((pre <= b) & ~corr_m & keepb).sum()
                         / max((~corr_m & keepb).sum(), 1))
        starless_st = np.clip((starless_st - b) / (1.0 - b), 0.0, 1.0)
        print(f"[starcomb] black_point {cfg['black_point']:g}/255: "
              f"clip0 corridor {clip_cor * 100:.2f}% sky "
              f"{clip_sky * 100:.2f}% (corridor must stay ~0)")

    # THE GATE (layer-appropriate QA): strict blocks/rings on the starless
    # render's SKY — MW corridor (incl. the boost feather zone) + branch
    # masked as known signal/non-sky. The recombined whole-frame QA below
    # stays a reported reference, never the gate.
    from PIL import Image
    tmp8 = (np.clip(starless_st.transpose(1, 2, 0), 0, 1) * 255 + .5).astype(np.uint8)
    slpath = jpg_out.replace(".jpg", "_starless.jpg")
    Image.fromarray(tmp8).save(slpath, quality=92)
    a_sl = np.asarray(Image.open(slpath), dtype=np.float64)
    qa_sl = bg_qa.qa_metrics(
        a_sl, bg_qa.sky_signal_mask(a_sl.shape[0], a_sl.shape[1]))
    # REPORTED corridor + seam metrics: the gate masks the corridor, so
    # corridor-contained costs (boost floor lift, chroma bands) and mask
    # seams need their own numbers — reported, never gated.
    corr = am.corridor_report(tmp8)

    def _f(v, spec="{:+.1f}"):
        return spec.format(v) if v is not None else "n/a"
    print(f"[starcomb]   corridor floor Δ P50 {_f(corr['floor_p50'])} / "
          f"P5 {_f(corr['floor_p5'])} | band chroma RG "
          f"{_f(corr['band_rg'], '{:.1f}')} BG {_f(corr['band_bg'], '{:.1f}')}"
          f" | seam tex y {_f(corr['seam_y'], '{:.2f}')} "
          f"x {_f(corr['seam_x'], '{:.2f}')} (1=none)")

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
    sigs = None
    if cfg.get("stars_floor", 0) > 0:
        # ghost-aura fix: the skirt annulus (star core -> dilated mask
        # edge) carries subtraction noise that the stars MTF amplifies
        # into a visible halo (measured +7..11 counts luminance / chroma
        # MAD 20-30 vs 6 for an unseparated stretch). Floor the stars
        # layer at k*sigma (per-channel linear sky noise from the linear
        # starless layer) so only genuine star signal reaches the
        # stretch.
        sl_lin, _ = am.load_image(starless_fit)
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
        # noise-relative anchor: k * sigma_G of the linear starless.
        # sigma and per-channel star amplitudes scale together under a
        # stack-normalization change, so this renders the same physical
        # star at the same brightness across builds of the same sky —
        # the catalog anchor (median top-500 max-over-channel amplitude)
        # instead mixes channels and drifted the low-end gain x864 ->
        # x996 (+15% shell brightness) between two builds. k calibrated
        # so the canonical set-03 stack renders identically in both
        # modes (anchor 0.0284109 / sigma_G 5.78673e-5).
        K_NOISE_ANCHOR = 490.9663661574939
        if sigs:
            sig_g = sigs[min(1, stars.shape[0] - 1)]
        else:
            sl_lin, _ = am.load_image(starless_fit)
            _, sig_g = am.bg_stats(sl_lin[min(1, sl_lin.shape[0] - 1)])
            del sl_lin
        anchor = float(K_NOISE_ANCHOR * sig_g)
        mode = f"noise ({K_NOISE_ANCHOR:.1f}*sigma_G)"
    else:
        amps = np.sort(cat["peak"])[::-1]
        anchor = float(np.median(amps[:min(500, len(amps))]))
        mode = "catalog"
    m = solve_mtf_m(anchor, cfg["stars_peak"])
    # print anchor + low-end gain every run so normalization drift stays
    # visible whichever mode is active
    gain0 = am.mtf(1e-4, m) / 1e-4
    print(f"[starcomb] stars anchor {anchor:.4f} [{mode}] -> m {m:.5f} "
          f"(low-end gain x{gain0:.0f})")
    stars_st = am.mtf(np.clip(stars, 0, 1), m)

    # --- combine ----------------------------------------------------------
    out = 1.0 - (1.0 - np.clip(starless_st, 0, 1)) * (1.0 - np.clip(stars_st, 0, 1))
    if cfg.get("satu", 0) > 0:
        # chroma gain on the combined render, AFTER the corings — so it
        # amplifies only significant (surviving) color: star hues and
        # honest MW tint, not noise chroma.
        s = float(cfg["satu"])
        mean = out.mean(axis=0, keepdims=True)
        out = np.clip(mean + (1.0 + s) * (out - mean), 0.0, 1.0)
        print(f"[starcomb] satu {s}: chroma gain on the combined render")
    u8 = (np.clip(out.transpose(1, 2, 0), 0, 1) * 255 + .5).astype(np.uint8)
    # Final-export encoding, measured vs the lossless PNG on this
    # grain-heavy content: q92 + default 4:2:0 subsampling costs mean
    # 2.29 counts / max 176 at star edges / 9.7 star-pixel chroma error;
    # q100 + subsampling=0 costs mean 0.44 / max 5. The prior encoding
    # reproduces with --jpg-quality 92 --jpg-subsampling -1. The STARLESS
    # jpg (gate input) is untouched — its q92 encoding is part of the
    # gate identity.
    jq = int(cfg.get("jpg_quality", 100))
    jsub = int(cfg.get("jpg_subsampling", 0))
    if jsub < 0:
        Image.fromarray(u8).save(jpg_out, quality=jq)
    else:
        Image.fromarray(u8).save(jpg_out, quality=jq, subsampling=jsub)
    if ctx.get("lossless"):
        # lossless deliverables: 8-bit PNG (deflate is lossless; the same
        # pixels the JPEG quantizes — the byte-verification artifact) and
        # a 16-bit PNG quantized straight from the float render (65536
        # levels vs 256: everything the chain computes, in a file viewers
        # can open)
        png_out = jpg_out[:-4] + ".png"
        Image.fromarray(u8).save(png_out)
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

    qa, smet, lev = rh.measure_jpg(jpg_out)
    a8 = np.asarray(Image.open(jpg_out), dtype=np.float32).transpose(2, 0, 1)
    mwb, skb = am.report_boxes(a8.shape[1], a8.shape[2])
    mw = (am.box_median_g(a8, mwb) - am.box_median_g(a8, skb)
          if mwb and skb else float("nan"))
    return {"qa": {k: v for k, v in qa.items() if isinstance(v, (int, float, bool))},
            "qa_starless": {k: v for k, v in qa_sl.items()
                            if isinstance(v, (int, float, bool))},
            "stars": smet, "bg_med8": lev[1]["median"] * 255.0,
            "mw_contrast8": mw, "corridor": corr, "star_shells": shell,
            "starless_jpg": os.path.basename(slpath)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("session")
    ap.add_argument("set")
    # Run against the SPCC-calibrated stack:
    #   starcomb.py <session> <set> --stack results/stack_<set>_spcc.fit
    # Every default below was set by a measured single-knob ladder.
    ap.add_argument("--starless-target", type=float, default=0.07)
    ap.add_argument("--starless-denoise", default="vstpost",
                    choices=["off", "vst", "gx", "vstpost"],
                    help="vstpost = post-stretch -vst -mod=0.5 (default). "
                         "vst/gx are the LINEAR placements: measured FAIL "
                         "on self-flat data (radial imprint) — kept as "
                         "rungs for future data")
    ap.add_argument("--sep-prom", type=float, default=6.0,
                    help="starsep component prominence cut (sigma); lower "
                         "moves the faint tail into the stars layer "
                         "(measured null on this data)")
    ap.add_argument("--sep-engine", default="inpaint",
                    choices=["inpaint", "net", "hybrid"],
                    help="star separation engine: inpaint = mask+inpaint "
                         "(starsep.py), net = StarNet2 ONNX on the stack "
                         "(removes the <6 sigma faint tail but leaves a "
                         "bright-star halo pedestal), hybrid = net run "
                         "on the inpaint starless (flat bright disks + "
                         "net faint-tail removal)")
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
                    help="autostretch channel linkage (linked = standard "
                         "on a calibrated stack; unlinked compensates "
                         "casts but amplifies per-channel noise into "
                         "chroma blotches)")
    ap.add_argument("--satu", type=float, default=0.2,
                    help="chroma gain on the combined render, AFTER the "
                         "corings (amplifies only significant color); "
                         "0 = off")
    ap.add_argument("--cull-pct", type=float, default=50)
    ap.add_argument("--stars-peak", type=float, default=0.97)
    ap.add_argument("--stars-anchor", default="catalog",
                    choices=["catalog", "noise"],
                    help="MTF anchor source: catalog = median top-500 "
                         "catalog amplitude (data-dependent — drifted "
                         "x864->x996 between builds of the same sky), "
                         "noise = k*sigma_G of the linear starless "
                         "(k calibrated so the canonical set-03 stack "
                         "renders identically in both modes)")
    ap.add_argument("--stars-floor", type=float, default=3.0,
                    help="core the stars layer below k*sigma (linear) "
                         "before its MTF — kills the amplified-skirt "
                         "ghost aura around stars; 0 = off")
    ap.add_argument("--black-point", type=float, default=8,
                    help="output black point on the starless layer, "
                         "8-bit counts (bg ~16 -> ~8); 0 = off")
    ap.add_argument("--mw-boost", type=float, default=1.2)
    ap.add_argument("--boost-mask", default="lum", choices=["geo", "lum"],
                    help="mw_boost mask: geo = flat geometric corridor "
                         "(lifts glow AND floor/gaps by 1+k), lum = "
                         "corridor x glow-luminosity weight (lift follows "
                         "the signal, gaps stay at sky black)")
    ap.add_argument("--stack", default=None,
                    help="override input stack path (default "
                         "results/stack_<set>.fit) — for pipeline-variant "
                         "stacks, e.g. stack_set-03_bgeonly.fit")
    ap.add_argument("--tag", default=None)
    ap.add_argument("--jpg-quality", type=int, default=100,
                    help="final jpg quality (default 100 + subsampling 0 "
                         "= mean 0.44 counts vs the lossless PNG; 92 + "
                         "subsampling -1 reproduces the prior encoding)")
    ap.add_argument("--jpg-subsampling", type=int, default=0,
                    help="PIL subsampling for the final jpg (0=4:4:4; "
                         "-1=encoder default 4:2:0, the prior encoding)")
    ap.add_argument("--lossless", action="store_true",
                    help="also write a lossless PNG next to each jpg")
    ap.add_argument("--param", default=None,
                    choices=["starless_target", "starless_denoise",
                             "cull_pct", "stars_peak", "stars_anchor",
                             "mw_boost", "sep_prom", "sep_engine",
                             "chroma_core", "satu", "core_order",
                             "stretch_linked", "lum_core", "boost_mask",
                             "stars_floor", "black_point"])
    ap.add_argument("--values", default=None)
    ap.add_argument("--hypothesis", default=None)
    args = ap.parse_args()

    # repo root is three up: this file is scripts/render/starcomb.py
    repo = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    sdir = os.path.join(repo, args.session)
    work = os.path.join(sdir, "work")
    stack = (os.path.abspath(args.stack) if args.stack
             else os.path.join(sdir, "results", f"stack_{args.set}.fit"))
    if not os.path.exists(stack):
        sys.exit(f"starcomb: no {stack}")
    # per-set geometry (corridor / foreground / boxes): config_<set>.json,
    # else WCS-derived corridor, else none — never silent set-03 defaults
    am.configure(sdir, args.set, stack=stack)
    ctx = {"repo": repo, "sdir": sdir, "work": work, "stack": stack,
           "set": args.set, "lossless": args.lossless}

    base = {"starless_target": args.starless_target,
            "starless_denoise": args.starless_denoise,
            "cull_pct": args.cull_pct, "stars_peak": args.stars_peak,
            "stars_anchor": args.stars_anchor,
            "mw_boost": args.mw_boost, "boost_mask": args.boost_mask,
            "sep_prom": args.sep_prom, "sep_engine": args.sep_engine,
            "chroma_core": args.chroma_core, "satu": args.satu,
            "core_order": args.core_order,
            "stretch_linked": args.stretch_linked,
            "lum_core": args.lum_core,
            "stars_floor": args.stars_floor,
            "black_point": args.black_point,
            "jpg_quality": args.jpg_quality,
            "jpg_subsampling": args.jpg_subsampling}

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
                   "boost_mask", "sep_engine", "stars_anchor")
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
        jpg = os.path.join(exp_dir, f"v{i}_{rh.sanitize(v)}.jpg")
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

    sx = rh.star_region(stack)
    strips = [rh.value_row(os.path.join(exp_dir, r["jpg"]), 0, sx)
              for r in results]
    labels = [f"{args.param} = {r['value']}   "
              f"[{'PASS' if r['qa_starless']['pass'] else 'FAIL'}]"
              for r in results]
    rh.compose_rows(strips, labels, os.path.join(exp_dir, "side_by_side.jpg"))
    print(f"\n[starcomb] STOP — user judgment required. Review {exp_dir}/")


if __name__ == "__main__":
    main()
