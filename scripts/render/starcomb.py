#!/usr/bin/env python3
"""Starless/stars split processing + recombination (standard-DSO style).

The product chain. Knob values resolve CLI > the dataset's tracked
recipe (datasets/<session>/<set>/recipe.json) > the GENERIC defaults —
so an approved look is pinned per dataset, and a dataset without a
recipe renders honestly generic and says so:

  starcomb.py <session> <set> --stack results/stack_<set>_norgbeq_spcc.fit [--lossless]

Chain (input is the SPCC-calibrated stack — solve_field.py --inject +
siril spcc; every generic value came from a measured single-knob ladder):
  1. GraXpert BGE + subsky 1 on the STAR-FUL linear (cached; the only
     order measured MW-safe — BGE on starless ERASES the MW)
  2. star separation (cached): StarNet2 ONNX (net) or mask+inpaint
     (inpaint); auto = net when the weights are installed
  starless: stretch per <stretch_linked> — linked autostretch -1.5
       <starless_target> (broadband standard; auto resolves here for
       any non-narrowband dataset) or per-line OBJECT-anchored MTF +
       sky re-pin (perline; auto resolves here for a narrowband
       palette composition — one linked MTF renders only the dominant
       emission line)
    -> post-stretch denoise -vst -mod=0.5 (<starless_denoise=vstpost>;
       every linear placement imprints a radial signature on self-flat
       data)
    -> chroma_core  (multi-scale Wiener chroma coring toward neutral)
    -> lum_core     (sky luminance coring; real structure Wiener-protected)
    -> black_point  (output levels on the starless layer: gaps clip to
       true black, real signal sits above the clip)
  stars: faint components culled below the <cull_pct> flux percentile,
    skirt cored below <stars_floor> x sigma (the ghost-aura fix: only
    genuine star signal reaches the stretch), gray MTF anchored so the
    median top-500 amplitude (on the fixed G basis) renders at
    <stars_peak>
  combine: screen 1-(1-a)(1-b) -> satu -> JPEG q100/4:4:4 [+ PNG].

Ladder mode (single knob, control auto-bracketed, STOPS for judgment):
  starcomb.py <session> <set> --stack ... --param chroma_core \\
      --values 2,6 --hypothesis "..."

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


def chroma_core(starless_st, k=3.0):
    """Multi-scale significance coring of chroma toward NEUTRAL.

    The stretch amplifies per-channel noise into colored blotches at ALL
    scales (measured 1-3 counts at 16-128 px on a linear floor of ~0.1);
    blurring chroma just moves speckle up in scale, and saturation then
    re-amplifies it. Instead: decompose R-G and B-G into a gaussian
    pyramid (sigma 2/8/32/128 + residual), measure each level's noise on
    the statistical dark sky, and Wiener-shrink each level by its local
    energy e/(e + (k*sigma)^2). Chroma that is not significantly above
    its own noise goes to gray; genuinely colored signal (bright star
    hues, real tint standing above noise) passes near-unchanged by
    construction. G (luminance) is never touched."""
    from scipy.ndimage import gaussian_filter
    c, h, w = starless_st.shape
    g2 = min(1, c - 1)
    G = starless_st[g2]
    # noise estimated on the statistical dark sky (bright signal + foreground
    # excluded) — composition-agnostic
    sky = am.sky_pixel_mask(G)
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
    """Sky LUMINANCE significance coring — the gray-patch fix.

    The stretch amplifies G noise into 1.2-2.7 counts of mid-scale gray
    patchiness on a sky whose linear floor is 0.06-0.10 (measured); with the
    chroma cored to neutral, the eye picks up that luminance unevenness. The
    sky should be FLAT, so mid-scale sky structure below significance is
    shrunk toward the smooth background: gaussian pyramid (sigma 8/32/128) of
    G, per-level sky-noise, Wiener shrinkage, applied identically to R/G/B (no
    chroma created). Noise is estimated on the statistical dark sky; the
    correction is Wiener-gated everywhere, so real structure (a galaxy, the
    MW, a treeline: energy >> noise => correction ~ 0) keeps its honest
    structure with no geometric mask (a hard mask multiplied into the
    correction printed a 4.5x blotch-texture seam at its edge)."""
    from scipy.ndimage import gaussian_filter
    c, h, w = starless_st.shape
    g2 = min(1, c - 1)
    G = starless_st[g2].astype(np.float64)
    skyb = am.sky_pixel_mask(starless_st[g2])
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
    out = np.clip(starless_st - correction[None, :, :], 0.0, 1.0)
    print(f"[starcomb] lum_core k={k}: insignificant sky luminance -> "
          f"smooth bg (real structure Wiener-protected)")
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


def perline_starless_stretch(starless_fit, out_fit, sky_target,
                             width_target):
    """Per-LINE NOISE-WIDTH-CAPPED stretch — the narrowband-palette
    stretch (stretch_linked=perline). Each emission line is stretched
    separately (one linked MTF renders only the dominant line — the
    drowned-O3-sphere defect), and the stretch is bounded by a display
    NOISE BUDGET, not an object anchor: per channel, gamma-then-black-pin
    y = (x^(1/g) - b)/(1 - b) with b always solving sky -> sky_target and
    g solved (fixed 24-step bisection, deterministic) so the sky NOISE
    WIDTH lands at width_target. The stretch therefore stops before
    amplifying noise into visibility — the reference finish's own
    mechanism (its chain carries no denoiser at all), and the fix for the
    coring-mottle class: noise that is never lifted needs no smoothing.
    Sky-anchored per-channel stretching (siril unlinked) cannot do this
    (no width control), and the earlier object-anchored form lifted the
    faint end past its noise budget. A gamma of 1 already over budget
    means the data is noisier than the target at unity stretch — stated,
    never forced. numpy end to end; file order and header cards
    round-trip untouched."""
    cards, planes, _ = am.read_fits_planes(starless_fit)
    out = np.empty_like(planes)
    for ci in range(planes.shape[0]):
        ch = planes[ci]
        sub = ch[::4, ::4].astype(np.float64)

        def width_at(g):
            y = np.clip(sub, 0.0, 1.0) ** (1.0 / g)
            loc, sig = am.bg_stats(y.astype(np.float32), stride=1)
            b = (loc - sky_target) / max(1.0 - sky_target, 1e-9)
            b = min(b, 0.999)
            return sig / max(1.0 - b, 1e-9), loc, b

        w1, _, _ = width_at(1.0)
        if w1 >= width_target:
            g = 1.0
            print(f"[starcomb] perline ch{ci}: width {w1 * 100:.2f}% >= "
                  f"budget {width_target * 100:.2f}% at unity gamma — no "
                  "stretch headroom, black-pin only")
        else:
            lo, hi = 1.0, 10.0
            for _ in range(24):
                mid = 0.5 * (lo + hi)
                w, _, _ = width_at(mid)
                if w < width_target:
                    lo = mid
                else:
                    hi = mid
            g = lo
        _, loc_g, b = width_at(g)
        y = np.clip(ch, 0.0, 1.0) ** np.float32(1.0 / g)
        z = (y - np.float32(b)) / np.float32(max(1.0 - b, 1e-9))
        out[ci] = np.clip(z, 0.0, 1.0)
        clip0 = float((z <= 0).mean())
        _, w_fin = am.bg_stats(out[ci])
        print(f"[starcomb] perline ch{ci}: gamma {g:.3f} black "
              f"{b * 100:+.2f}% -> sky {sky_target * 100:.1f}% width "
              f"{w_fin * 100:.3f}% (budget {width_target * 100:.2f}%) "
              f"clip0 {clip0 * 100:.2f}%")
    am.write_fits_planes(out_fit, cards, out)


def perline_finish(starless_st, cfg):
    """Narrowband finishing on the per-line-stretched starless — the
    reference chain's operator set, in its order, each gated at the sky
    significance threshold so the noise floor is never touched:

    1. saturation gamma (satgamma): LCh chroma C -> Cref*(C/Cref)^(1/y)
       for pixels above the luminance gate (Cref = p99.9 of gated C);
    2. hue rotation (huerot_from/to/by, LCh hue degrees): the Hubble-
       palette shift — the reference's golds ARE its rotated Ha greens;
    3. SCNR (scnr): average-neutral green blend g' = (1-a)g +
       a*min(g,(r+b)/2), ungated (the classic full-frame operator);
    4. post-peak luminance lift (ppgamma): partial gamma on Luv L over
       [gate,1], applied as an RGB-ratio-preserving gain — LUMINANCE
       ONLY, chroma noise is never stretched (the anti-mottle property).

    Gate = sky L + ppsigma * sky L width, measured on the stretched
    image's Luv luminance. All-neutral knobs (satgamma 1, huerot_by 0,
    scnr 0, ppgamma 1) make this an exact no-op."""
    satg = float(cfg.get("satgamma", 1.0))
    rot_by = float(cfg.get("huerot_by", 0.0))
    scnr_a = float(cfg.get("scnr", 0.0))
    ppg = float(cfg.get("ppgamma", 1.0))
    pps = float(cfg.get("ppsigma", 1.0))
    if satg == 1.0 and rot_by == 0.0 and scnr_a == 0.0 and ppg == 1.0:
        return starless_st

    L, C, h = am.rgb_to_lch(starless_st)
    Ln = L / 100.0
    loc, wid = am.bg_stats(Ln)
    gate = np.float32(loc + pps * wid)
    # smooth significance blend, not a hard cut: a binary gate stipples
    # the boundary (pixels flickering across the threshold get binary
    # treatment — measured as a speckle fringe around the dust edges);
    # ramp the ops in over two noise widths above the gate instead
    ramp = np.float32(max(2.0 * wid, 1e-6))
    w01 = np.clip((Ln - gate) / ramp, 0.0, 1.0).astype(np.float32)
    gm = w01 > 0
    gfrac = float((w01 >= 1.0).mean())
    print(f"[starcomb] perline finish: L gate {loc * 100:.2f}% + "
          f"{pps:g}*{wid * 100:.3f}% -> {float(gate) * 100:.2f}%, "
          f"ramp +{float(ramp) * 100:.3f}% "
          f"({gfrac * 100:.1f}% of px fully above)")

    if satg != 1.0 and gm.any():
        cref = float(np.percentile(C[w01 >= 1.0], 99.9)) \
            if (w01 >= 1.0).any() else 0.0
        if cref > 0:
            cn = np.clip(C / cref, 0.0, None)
            C = C + w01 * (cref * cn ** np.float32(1.0 / satg) - C)
            print(f"[starcomb]   satgamma {satg:g} (Cref {cref:.2f})")
    if rot_by != 0.0:
        f0 = float(cfg.get("huerot_from", 0.0))
        t0 = float(cfg.get("huerot_to", 360.0))
        # feather the interval edges (8 deg cosine ramps): a hard hue
        # boundary splits adjacent pixels of one structure into rotated
        # vs unrotated colour — measured as a neon seam where the object
        # hue straddles the interval edge
        fw = np.float32(8.0)
        lo_r = np.clip((h - np.float32(f0)) / fw, 0.0, 1.0)
        hi_r = np.clip((np.float32(t0) - h) / fw, 0.0, 1.0)
        hue_w = (lo_r * hi_r).astype(np.float32)
        sel_w = w01 * hue_w
        h = (h + sel_w * np.float32(rot_by)) % 360.0
        print(f"[starcomb]   huerot [{f0:g},{t0:g}]±8 by {rot_by:+g} deg "
              f"({float((sel_w > 0.5).mean()) * 100:.1f}% of px)")
    out = am.lch_to_rgb(L, C, h)
    del L, C, h
    if scnr_a > 0.0:
        gmin = np.minimum(out[1], 0.5 * (out[0] + out[2]))
        out[1] = (1.0 - scnr_a) * out[1] + scnr_a * gmin
        print(f"[starcomb]   scnr {scnr_a:g}")
    if ppg != 1.0:
        L2, _, _ = am.rgb_to_lch(out)
        Ln2 = L2 / 100.0
        del L2
        t = float(gate)
        span = max(1.0 - t, 1e-9)
        lifted = t + span * ((np.clip(Ln2, t, 1.0) - t) / span) \
            ** np.float32(1.0 / ppg)
        gain = np.where(Ln2 > t, lifted / np.maximum(Ln2, 1e-6), 1.0) \
            .astype(np.float32)
        out = np.clip(out * gain[None, :, :], 0.0, 1.0)
        print(f"[starcomb]   ppgamma {ppg:g} above {t * 100:.2f}% "
              f"(max gain x{float(gain.max()):.2f})")
    return out.astype(starless_st.dtype)


def _inspect_stage(ctx, name, arr, stretched, note=""):
    """Render-chain provenance (--inspect): one consistent JPEG + one
    metrics line per render stage, so a defect in the final render can be
    localized to the stage that introduced it without re-running the
    chain. Linear stages go through the shared inspection autostretch;
    stretched stages are written as-is (they ARE display-referred)."""
    d = ctx.get("inspect_dir")
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
    Image.fromarray(u8[::3, ::3]).save(
        os.path.join(d, f"{n:02d}_{name}.jpg"), quality=90)
    g = arr[min(1, arr.shape[0] - 1)]
    bg, sig = am.bg_stats(g)
    rec = {"stage": name, "stretched": bool(stretched),
           "bg_g": round(float(bg), 6), "sigma_g": round(float(sig), 7),
           "p99_g": round(float(np.percentile(g[::4, ::4], 99)), 6),
           "note": note}
    with open(os.path.join(d, "metrics.jsonl"), "a") as f:
        f.write(_json.dumps(rec) + "\n")
    print(f"[inspect-render] {name}: bg {bg:.5f} sigma {sig:.6f}")


def _stage_line(name, arr):
    """Always-on one-line stage metric (bg / sigma / p99 of G): every
    transform that mutates the image reports itself, so a defect in a
    final render localizes to a stage from the normal run's log alone
    (--inspect adds the per-stage JPEGs on top)."""
    g = arr[min(1, arr.shape[0] - 1)]
    bg, sig = am.bg_stats(g)
    p99 = float(np.percentile(g[::4, ::4], 99))
    print(f"[starcomb] {name}: bg {bg:.5f} sigma {sig:.6f} p99 {p99:.5f}")


def render_config(ctx, cfg, jpg_out):
    """Run one configuration; returns metrics dict (also writes jpg)."""
    sdir, work = ctx["sdir"], ctx["work"]
    st_out = os.path.join(work, "starless_st.fit")
    if os.path.exists(st_out):
        os.remove(st_out)
    # Background removed on the STAR-FUL linear (the standard order and
    # the only one measured MW-safe: gx on starless erased the MW +38 ->
    # +0.4), THEN separation; the starless branch only denoises/stretches.
    bgelin = ensure_bge_linear(ctx, mode=cfg.get("bgelin_mode", "gx"))
    if ctx.get("inspect_dir"):
        b, _ = am.load_image(bgelin)
        _inspect_stage(ctx, "bgelin", b, False, "BGE'd linear (star-ful)")
        del b
    starless_fit, stars_fit, cat_npz = ensure_starsep(
        ctx["repo"], sdir, bgelin, prom=cfg.get("sep_prom", 6.0),
        set_name=ctx.get("set"),
        engine=cfg.get("sep_engine", "auto"))
    ctx = {**ctx, "stars_fit": stars_fit, "cat_npz": cat_npz}
    if ctx.get("inspect_dir"):
        b, _ = am.load_image(starless_fit)
        _inspect_stage(ctx, "starless_linear", b, False,
                       "separation output, linear")
        del b
    if cfg["starless_denoise"] == "gx":
        # AI denoise, linear, starless (standard step-5 placement; a
        # measured FAIL on this self-flat data, kept as an option because
        # new data may have a different noise structure)
        starless_fit = run_graxpert_denoise(work, starless_fit)
    perline_fit = None
    if cfg.get("stretch_linked") == "perline":
        # narrowband-palette stretch: each line noise-width-capped in
        # numpy, THEN the siril tail (ghs finishing / vstpost denoise)
        # runs on the pre-stretched file exactly like on an autostretch
        # result; the LCh finishing ops apply after load (below)
        perline_fit = os.path.join(work, "perline_st.fit")
        perline_starless_stretch(starless_fit, perline_fit,
                                 float(cfg["starless_target"]),
                                 float(cfg["perline_scale"]) / 100.0)
        starless_fit_for_siril = perline_fit
    else:
        starless_fit_for_siril = starless_fit
    rel = os.path.relpath(starless_fit_for_siril, sdir)
    suffix = rel[:-5] if rel.endswith(".fits") else rel[:-4]
    lines = ["requires 1.4.0", f"load {suffix}"]
    if cfg["starless_denoise"] == "vst":
        lines.append("denoise -vst")
    # Stretch linkage: unlinked equalizes per-channel backgrounds (cast
    # compensation) but per-channel curves differentially amplify
    # per-channel noise into chroma blotches. On an SPCC-calibrated
    # BROADBAND stack there is no cast to compensate — linked is the
    # standard there. perline is the narrowband-palette mode (per-line
    # noise-width-capped stretch above); any siril-side pass that follows
    # it (ghs finishing) runs linked — the lines are already equalized.
    linkflag = "-linked " if cfg.get("stretch_linked") != "unlinked" else ""
    if cfg.get("stretch_linked") != "perline":
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
        lines.append("denoise -vst -mod=0.5")
    lines.append("save work/starless_st")
    lines.append("close")
    run_siril(sdir, lines, "starcomb_starless.gen.ssf")
    starless_st = am.load_linear(st_out)
    os.remove(st_out)  # 294 MB scratch: free it now (all in memory)
    if perline_fit and os.path.exists(perline_fit):
        os.remove(perline_fit)  # same-size scratch, consumed by the save

    # A single-filter (mono) stack carries luminance only. Replicate it to RGB
    # so the gate, star-shell audit and 8-bit writers see the three channels
    # they expect, and skip the colour operators: chroma coring and saturation
    # both act on channel differences that are identically zero here, so they
    # can only cost time (chroma_core also indexes a blue channel that a
    # 1-channel stack does not have).
    mono = starless_st.shape[0] == 1
    if mono:
        starless_st = np.repeat(starless_st, 3, axis=0)
        print("[starcomb] mono stack -> luminance render "
              "(chroma_core / satu skipped: no colour)")
    ghs_tag = (f" + ghs k{cfg.get('ghs_sp_k')}/D{cfg.get('ghs_amount')}"
               f"/b{cfg.get('ghs_focus')}"
               if cfg.get("stretch_mode", "mtf") == "ghs" else "")
    pl_tag = (f" width->{cfg.get('perline_scale'):g}%"
              if cfg.get("stretch_linked") == "perline" else "")
    _stage_line(f"stretch [{cfg.get('stretch_linked')}{pl_tag} "
                f"{cfg['starless_target']:g}{ghs_tag} + "
                f"{cfg['starless_denoise']}]", starless_st)
    _inspect_stage(ctx, "starless_stretch", starless_st, True,
                   f"stretch {cfg.get('stretch_linked')}{pl_tag} "
                   f"{cfg['starless_target']}{ghs_tag} + "
                   f"{cfg['starless_denoise']}")

    if not mono and cfg.get("stretch_linked") == "perline":
        # narrowband finishing (the reference chain's operator set:
        # gated saturation gamma, Hubble hue rotation, SCNR, post-peak
        # luminance-only lift) — LUMINANCE is lifted, chroma never
        # stretched, so the noise floor stays at the stretch's budget
        starless_st = perline_finish(starless_st, cfg)
        _stage_line("perline finish [satgamma/huerot/scnr/ppgamma]",
                    starless_st)
        _inspect_stage(ctx, "perline_finish", starless_st, True,
                       f"satgamma {cfg.get('satgamma')} huerot "
                       f"{cfg.get('huerot_by')} scnr {cfg.get('scnr')} "
                       f"ppgamma {cfg.get('ppgamma')}")

    if not mono and cfg.get("chroma_core", 0) > 0 and cfg.get("core_order", "pre") == "pre":
        # chroma coring BEFORE lum_core (default): chroma is neutralized on
        # the raw stretched sky, then lum_core smooths only luminance and
        # cannot revive the neutralized chroma.
        starless_st = chroma_core(starless_st, float(cfg["chroma_core"]))

    if cfg.get("lum_core", 0) > 0:
        starless_st = lum_core(starless_st, float(cfg["lum_core"]))

    if not mono and cfg.get("chroma_core", 0) > 0 and cfg.get("core_order", "pre") == "post":
        starless_st = chroma_core(starless_st, float(cfg["chroma_core"]))

    _inspect_stage(ctx, "starless_cored", starless_st, True,
                   f"chroma_core {cfg.get('chroma_core')} / lum_core "
                   f"{cfg.get('lum_core')}")

    if cfg.get("black_point", 0) > 0:
        # output black point on the starless layer — the only place the
        # render sets its own zero. Linear + linked (no cast, differences
        # preserved), BEFORE the gate jpg so QA sees it.
        b = float(cfg["black_point"]) / 255.0
        c2, h2, w2 = starless_st.shape
        keepb = am.branch_mask(h2, w2)
        g2 = min(1, c2 - 1)
        pre = starless_st[g2]
        clip_sky = float(((pre <= b) & keepb).sum() / max(keepb.sum(), 1))
        starless_st = np.clip((starless_st - b) / (1.0 - b), 0.0, 1.0)
        print(f"[starcomb] black_point {cfg['black_point']:g}/255: "
              f"clip0 sky {clip_sky * 100:.2f}%")

    _inspect_stage(ctx, "starless_final", starless_st, True,
                   f"black_point {cfg.get('black_point')} — the gate input")

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
    # visible whichever mode is active
    gain0 = am.mtf(1e-4, m) / 1e-4
    print(f"[starcomb] stars anchor {anchor:.4f} [{mode}] -> m {m:.5f} "
          f"(low-end gain x{gain0:.0f})")
    stars_st = am.mtf(np.clip(stars, 0, 1), m)
    _inspect_stage(ctx, "stars_mtf", stars_st, True,
                   f"cull {cfg.get('cull_pct')} / floor "
                   f"{cfg.get('stars_floor')} / anchor {mode} m {m:.5f}")

    # --- combine ----------------------------------------------------------
    k_st = float(cfg.get("stars_opacity", 1.0))
    if k_st != 1.0:
        # industry star-subduing: screen with stars*k so the star field
        # stops competing with the object (the standard reduced-opacity
        # recombine); 1.0 = the plain screen, bit-exact
        stars_st = stars_st * np.float32(k_st)
        print(f"[starcomb] stars_opacity {k_st:g}")
    out = 1.0 - (1.0 - np.clip(starless_st, 0, 1)) * (1.0 - np.clip(stars_st, 0, 1))
    if not mono and cfg.get("satu", 0) > 0:
        # chroma gain on the combined render, AFTER the corings — so it
        # amplifies only significant (surviving) color: star hues and
        # honest MW tint, not noise chroma.
        s = float(cfg["satu"])
        mean = out.mean(axis=0, keepdims=True)
        out = np.clip(mean + (1.0 + s) * (out - mean), 0.0, 1.0)
        print(f"[starcomb] satu {s}: chroma gain on the combined render")
    _stage_line(f"combine [screen + satu {cfg.get('satu')}]", out)
    _inspect_stage(ctx, "combine", out, True,
                   f"screen combine + satu {cfg.get('satu')}")
    u8 = (np.clip(out.transpose(1, 2, 0), 0, 1) * 255 + .5).astype(np.uint8)
    # Final-export encoding, measured vs the lossless PNG on this
    # grain-heavy content: q92 + default 4:2:0 subsampling costs mean
    # 2.29 counts / max 176 at star edges / 9.7 star-pixel chroma error;
    # q100 + subsampling=0 costs mean 0.44 / max 5. Finals carry embedded
    # sRGB colorimetry (JPEG ICC + PNG sRGB/gAMA/cHRM — the chain's LCh
    # math already treats display RGB as sRGB-companded; pixels are
    # untouched). The STARLESS jpg (gate input) is untouched entirely —
    # its q92 encoding is part of the gate identity.
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

    qa, smet, lev = rh.measure_jpg(jpg_out)
    return {"qa": {k: v for k, v in qa.items() if isinstance(v, (int, float, bool))},
            "qa_starless": {k: v for k, v in qa_sl.items()
                            if isinstance(v, (int, float, bool))},
            "stars": smet, "bg_med8": lev[1]["median"] * 255.0,
            "star_shells": shell,
            "starless_jpg": os.path.basename(slpath)}


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
    "chroma_core", "lum_core", "core_order", "stretch_linked",
    "perline_scale", "ppgamma", "ppsigma", "satgamma",
    "huerot_from", "huerot_to", "huerot_by", "scnr", "satu",
    "cull_pct", "stars_peak", "stars_anchor", "stars_floor",
    "stars_opacity",
    "black_point", "jpg_quality", "jpg_subsampling", "noise_anchor_k",
)

ENUM_CHOICES = {
    "bgelin_mode": ["gx", "plane", "off"],
    "starless_denoise": ["off", "vst", "gx", "vstpost"],
    "stretch_mode": ["mtf", "ghs"],
    "sep_engine": ["auto", "inpaint", "net"],
    "core_order": ["pre", "post"],
    "stretch_linked": ["auto", "unlinked", "linked", "perline"],
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
        # class resolution from tracked per-dataset state: a narrowband
        # PALETTE composition (the recipe's spcc.narrowband marker — the
        # same fact that drives SPCC's -narrowband mode) stretches
        # per-line; everything else takes the broadband linked standard
        nb = bool(rec.get("spcc", {}).get("narrowband"))
        base["stretch_linked"] = "perline" if nb else "linked"
        print(f"[recipe] stretch_linked auto -> {base['stretch_linked']} "
              + ("(narrowband palette composition: per-line "
                 "noise-width-capped stretch + LCh finishing)" if nb
                 else "(broadband/mono: single linked stretch)"))
    if srcs:
        print("[recipe] non-generic: " + " ".join(srcs))
    return base


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
    ap.add_argument("--chroma-core", type=float, default=None,
                    help="significance k for multi-scale chroma coring "
                         "toward neutral; 0 = off")
    ap.add_argument("--lum-core", type=float, default=None,
                    help="significance k for sky-only luminance coring "
                         "(gray-patch fix); 0 = off")
    ap.add_argument("--core-order", default=None,
                    choices=ENUM_CHOICES["core_order"],
                    help="chroma coring before (pre, generic) or after "
                         "(post) lum_core")
    ap.add_argument("--stretch-linked", default=None,
                    choices=ENUM_CHOICES["stretch_linked"],
                    help="stretch channel coupling: linked = one transfer "
                         "(broadband standard); unlinked = per-channel "
                         "SKY-anchored (cast compensation; amplifies "
                         "channel noise into chroma blotches, and a "
                         "measured no-op on bg-equalized narrowband); "
                         "perline = per-line OBJECT-anchored + sky re-pin "
                         "(the narrowband-palette standard); auto = "
                         "perline when the recipe marks a narrowband "
                         "composition, else linked (generic)")
    ap.add_argument("--perline-scale", type=float, default=None,
                    help="perline stretch: sky NOISE-WIDTH budget in %% "
                         "of range — the stretch stops when the sky "
                         "width reaches it (sky location pins at "
                         "starless-target); noise never lifts past the "
                         "budget")
    ap.add_argument("--ppgamma", type=float, default=None,
                    help="perline finishing: post-peak gamma on Luv "
                         "LUMINANCE only, applied above the sky "
                         "significance gate; 1 = off")
    ap.add_argument("--ppsigma", type=float, default=None,
                    help="perline finishing: the significance gate = "
                         "sky L + ppsigma * sky L width (gates ppgamma, "
                         "satgamma, huerot)")
    ap.add_argument("--satgamma", type=float, default=None,
                    help="perline finishing: LCh chroma gamma above the "
                         "gate (saturation of significant signal; the "
                         "noise floor untouched); 1 = off")
    ap.add_argument("--huerot-from", type=float, default=None,
                    help="perline finishing: hue rotation interval "
                         "start, LCh degrees")
    ap.add_argument("--huerot-to", type=float, default=None,
                    help="perline finishing: hue rotation interval end")
    ap.add_argument("--huerot-by", type=float, default=None,
                    help="perline finishing: rotate hues in the "
                         "interval by this many degrees (Hubble gold = "
                         "rotate the Ha greens negative); 0 = off")
    ap.add_argument("--scnr", type=float, default=None,
                    help="perline finishing: average-neutral green "
                         "removal amount in [0,1]; 0 = off")
    ap.add_argument("--stars-opacity", type=float, default=None,
                    help="screen combine with stars*k — star-field "
                         "subduing (industry reduced-opacity "
                         "recombine); 1 = plain screen")
    ap.add_argument("--satu", type=float, default=None,
                    help="chroma gain on the combined render, AFTER the "
                         "corings (amplifies only significant color); "
                         "0 = off")
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
    ap.add_argument("--inspect", action="store_true",
                    help="write per-stage render provenance (consistent "
                         "JPEG + metrics line for bgelin / separation / "
                         "stretch / corings / stars / combine) into "
                         "results/inspect_render_<set>_<stamp>/ — localize "
                         "a render defect to its stage in one run")
    ap.add_argument("--param", default=None,
                    choices=["bgelin_mode",
                             "starless_target", "starless_denoise",
                             "stretch_mode", "ghs_sp_k", "ghs_amount",
                             "ghs_focus",
                             "cull_pct", "stars_peak", "stars_anchor",
                             "sep_prom", "sep_engine",
                             "chroma_core", "satu", "core_order",
                             "stretch_linked", "perline_scale",
                             "ppgamma", "ppsigma", "satgamma",
                             "huerot_from", "huerot_to", "huerot_by",
                             "scnr", "stars_opacity",
                             "lum_core",
                             "stars_floor", "black_point"])
    ap.add_argument("--values", default=None)
    ap.add_argument("--hypothesis", default=None)
    args = ap.parse_args()

    # repo root is three up: this file is scripts/render/starcomb.py
    repo = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    sdir = os.path.join(repo, args.session)
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
           "inspect_dir": (os.path.join(
               sdir, "results", f"inspect_render_{args.set}_{stamp}")
               if args.inspect else None)}

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
                   "stretch_mode", "core_order", "stretch_linked",
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


if __name__ == "__main__":
    main()
