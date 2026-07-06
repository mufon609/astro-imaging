#!/usr/bin/env python3
"""Starless/stars split processing + recombination (standard-DSO style).

Single run:
  starcomb.py <session> <set> [--starless-target 0.12] [--starless-denoise off|vst]
              [--cull-pct 0] [--stars-peak 0.85] [--tag name]

Ladder (single-knob, bracketed, stops for judgment — same discipline as
experiment.py):
  starcomb.py <session> <set> --param starless_target --values 0.07,0.12,0.15
              --hypothesis "..."
  params: starless_target | starless_denoise | cull_pct | stars_peak

Chain per configuration (the pieces the standard workflow separates):
  starless = inpainted stack (starsep.py, cached)
    -> GraXpert BGE (cached) -> subsky 1 -> [denoise -vst] ->
       autostretch (unlinked) -1.5 <starless_target>
  stars    = stack - starless, faint components culled below the
             <cull_pct> flux percentile, gray MTF anchored so the median
             top-500 star amplitude renders at <stars_peak>
  combine  = screen: 1 - (1-starless)(1-stars) -> JPEG q92

Reported per configuration: bg_qa + star metrics on the COMBINED image,
bg_qa on the STARLESS render alone (the honest rim/ring check — nothing
for a dark render to hide behind), and MW-vs-dark-sky contrast (G median
delta between fixed boxes, 8-bit counts).
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
from starsep import write_fits_fitsorder  # noqa: E402

# MW core vs dark-sky boxes (fractions of w,h; display orientation).
MW_BOX = (0.40, 0.30, 0.70, 0.55)
SKY_BOX = (0.05, 0.25, 0.25, 0.50)

# MW band corridor (display fractions): the band runs from the bottom
# center-left to the top-right corner. Endpoints + half-width set from the
# band-course measurement on the L2 starless layer (see NOTES). Used to
# EXCLUDE background samples (mode 'banded') and to LOCALIZE the mw_boost.
BAND_P0 = (0.30, 1.00)   # (x, y) fractions, bottom end
BAND_P1 = (0.80, 0.00)   # top-right exit (widened after the overlay check)
BAND_HALFW = 0.19        # fraction of the frame diagonal

BLOCK = 101


def band_mask_frac(h, w, feather=0.0):
    """Soft [0..1] corridor mask of the MW band (1 inside). feather is an
    extra half-width over which the mask rolls off smoothly."""
    ys = (np.arange(h) + 0.5) / h
    xs = (np.arange(w) + 0.5) / w
    X, Y = np.meshgrid(xs, ys)
    x0, y0 = BAND_P0
    x1, y1 = BAND_P1
    dx, dy = x1 - x0, y1 - y0
    n2 = dx * dx + dy * dy
    t = ((X - x0) * dx + (Y - y0) * dy) / n2
    t = np.clip(t, 0.0, 1.0)
    px, py = x0 + t * dx, y0 + t * dy
    d = np.hypot(X - px, Y - py)  # distance in frame-fraction units
    if feather <= 0:
        return (d <= BAND_HALFW).astype(np.float32)
    return np.clip((BAND_HALFW + feather - d) / feather, 0.0, 1.0) \
        .astype(np.float32)


def background_model(data, mode):
    """Smooth background for the STARLESS layer, MW-protecting.

    mode='border': samples ONLY in a 2-block border ring (MW exit corner
    and branch excluded). REFUTED on this data: a border-pinned membrane
    cannot represent the glow's interior curvature (over-subtracted the MW
    region by ~19 counts) and sample noise wiggles the rim (ring L 8.6).
    Kept for reference.

    mode='envelope': grid samples EVERYWHERE (branch excluded), p30 block
    values (star-residue resistant), thin-plate RBF with real smoothing,
    then 4 rounds of LOWER-ENVELOPE rejection: drop samples sitting above
    the fit (bg + MW), keep those at/below (pure bg — the MW's dark lanes
    anchor the surface under the band). DBE's target-protection, automated.
    Border samples are in the grid, so the rim is interpolated, not
    extrapolated. Returns model with median removed.
    REFUTED for rings (9.4): rejection leaves local extrapolation pockets
    and the surface still tracks the broad band partially.

    mode='banded': like envelope but the MW protection is GEOMETRIC and
    deterministic — no samples inside the band corridor (band_mask_frac),
    no rejection iterations. The glow's interior curvature is modeled from
    everywhere else; the corridor is bridged smoothly by the thin-plate
    surface. This is DBE with target-avoiding sample placement, exactly
    what the L3 lesson demands (rim curvature and MW are the same
    frequency — only geometry separates them)."""
    from scipy.interpolate import RBFInterpolator
    from scipy import ndimage
    c, h, w = data.shape
    gy, gx = h // BLOCK, w // BLOCK
    pts, vals = [], []
    for by in range(gy):
        for bx in range(gx):
            edge_y = min(by, gy - 1 - by)
            edge_x = min(bx, gx - 1 - bx)
            cy = (by + 0.5) * BLOCK / h
            cx = (bx + 0.5) * BLOCK / w
            if mode == "border":
                if min(edge_y, edge_x) >= 2:
                    continue
                if cy < 2 * BLOCK / h and cx > 0.55:
                    continue
                if cx > 1 - 2 * BLOCK / w and cy < 0.45:
                    continue
            if cy > 0.72 and cx < 0.25:
                continue  # branch corner is not sky
            block = data[:, by * BLOCK:(by + 1) * BLOCK,
                         bx * BLOCK:(bx + 1) * BLOCK]
            pts.append((cy, cx))
            q = 30 if mode == "envelope" else 50
            vals.append(np.percentile(block.reshape(c, -1), q, axis=1))
    pts = np.array(pts)
    vals = np.array(vals)  # (n, c)
    keep = np.ones(len(pts), bool)
    smoothing = 1e-4 if mode in ("envelope", "banded") else 1e-7
    gl = min(1, c - 1)
    if mode == "banded":
        bm = band_mask_frac(200, 200)  # coarse lookup is plenty for points
        for i, (cy, cx) in enumerate(pts):
            if bm[min(int(cy * 200), 199), min(int(cx * 200), 199)] > 0:
                keep[i] = False
    if mode == "envelope":
        for it in range(4):
            rbf = RBFInterpolator(pts[keep], vals[keep, gl],
                                  kernel="thin_plate_spline",
                                  smoothing=smoothing)
            fit = rbf(pts)
            resid = vals[:, gl] - fit
            mad = 1.4826 * np.median(np.abs(resid[keep] - np.median(resid[keep])))
            new = resid <= 0.6 * mad          # keep lower envelope
            if new.sum() < 0.4 * len(pts):    # never starve the fit
                break
            keep = new
    ys = np.linspace(0, 1, h // 4)
    xs = np.linspace(0, 1, w // 4)
    Y, X = np.meshgrid(ys, xs, indexing="ij")
    grid = np.stack([Y.ravel(), X.ravel()], axis=1)
    model = np.empty_like(data)
    for ch in range(c):
        rbf = RBFInterpolator(pts[keep], vals[keep, ch],
                              kernel="thin_plate_spline", smoothing=smoothing)
        small = rbf(grid).reshape(len(ys), len(xs)).astype(np.float32)
        full = ndimage.zoom(small, (h / small.shape[0], w / small.shape[1]),
                            order=1)[:h, :w]
        model[ch] = full - np.median(full)
    print(f"[starcomb] {mode} background: {int(keep.sum())}/{len(pts)} samples, "
          f"model span G {model[gl].min() * 65535:.0f}"
          f"..{model[gl].max() * 65535:.0f} counts")
    return model


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


def ensure_starsep(repo, sdir, input_fit):
    """Run (cached) star separation on any linear FITS."""
    outdir = os.path.join(sdir, "work", "starsep")
    r = subprocess.run([sys.executable, os.path.join(repo, "scripts", "starsep.py"),
                        input_fit, outdir], capture_output=True, text=True)
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
    if cfg["order"] == "bge_first":
        # background removed on the STAR-FUL linear (MW-safe, rim-best),
        # THEN separation; the starless branch only denoises/stretches.
        bgelin = ensure_bge_linear(ctx)
        starless_fit, stars_fit, cat_npz = ensure_starsep(
            ctx["repo"], sdir, bgelin)
        ctx = {**ctx, "stars_fit": stars_fit, "cat_npz": cat_npz}
        rel = os.path.relpath(starless_fit, sdir)
        lines = ["requires 1.4.0", f"load {rel[:-4]}"]
    elif cfg["starless_bge"] in ("border", "envelope", "banded"):
        # numpy MW-protecting model (rim interpolated, not extrapolated),
        # then siril for denoise/stretch on the subtracted layer
        raw, _ = am.load_image(ctx["starless_fit"])
        model = background_model(raw, cfg["starless_bge"])
        sub = np.clip(raw - model, 0.0, 1.0)
        from starsep import write_fits_fitsorder
        p_sub = os.path.join(work, "starless_bsub.fit")
        write_fits_fitsorder(p_sub, sub)
        del raw, model, sub
        lines = ["requires 1.4.0", "load work/starless_bsub"]
    else:
        gx = exp.run_graxpert(ctx["starless_fit"], work,
                              lambda m: print(f"[starcomb] {m}", flush=True))
        rel_gx = os.path.relpath(gx, sdir)
        lines = ["requires 1.4.0",
                 f"load {rel_gx[:-5] if rel_gx.endswith('.fits') else rel_gx}",
                 "subsky 1 -dither"]
    if cfg["starless_denoise"] == "vst":
        lines.append("denoise -vst")
    lines.append(f"autostretch -1.5 {cfg['starless_target']}")
    lines.append("save work/starless_st")
    lines.append("close")
    run_siril(sdir, lines, "starcomb_starless.gen.ssf")
    starless_st, _ = am.load_image(st_out)

    if cfg.get("mw_boost", 0) > 0:
        # band-localized midtone lift on the stretched starless layer:
        # out = bg + (x - bg) * (1 + k*M), M = feathered band corridor.
        # Lifts the MW's above-background signal without touching the rim
        # (corridor only), stars (separate layer) or the background level.
        c2, h2, w2 = starless_st.shape
        M = band_mask_frac(h2, w2, feather=0.10)
        g2 = min(1, c2 - 1)
        bglev, _ = am.bg_stats(starless_st[g2])
        k = float(cfg["mw_boost"])
        gain = 1.0 + k * M
        starless_st = np.clip(
            bglev + (starless_st - bglev) * gain[None, :, :], 0.0, 1.0)
        print(f"[starcomb] mw_boost {k}: band lift around bg {bglev:.3f}")

    # honest rim check: QA the starless render ALONE
    from PIL import Image
    tmp8 = (np.clip(starless_st.transpose(1, 2, 0), 0, 1) * 255 + .5).astype(np.uint8)
    slpath = jpg_out.replace(".jpg", "_starless.jpg")
    Image.fromarray(tmp8).save(slpath, quality=92)
    qa_sl = bg_qa.qa_metrics(np.asarray(Image.open(slpath), dtype=np.float64))

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
    u8 = (np.clip(out.transpose(1, 2, 0), 0, 1) * 255 + .5).astype(np.uint8)
    Image.fromarray(u8).save(jpg_out, quality=92)

    qa, smet, lev = exp.measure_jpg(jpg_out)
    a8 = np.asarray(Image.open(jpg_out), dtype=np.float32).transpose(2, 0, 1)
    mw = box_median_g(a8, MW_BOX) - box_median_g(a8, SKY_BOX)
    return {"qa": {k: v for k, v in qa.items() if isinstance(v, (int, float, bool))},
            "qa_starless": {k: v for k, v in qa_sl.items()
                            if isinstance(v, (int, float, bool))},
            "stars": smet, "bg_med8": lev[1]["median"] * 255.0,
            "mw_contrast8": mw, "starless_jpg": os.path.basename(slpath)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("session")
    ap.add_argument("set")
    ap.add_argument("--starless-target", type=float, default=0.12)
    ap.add_argument("--starless-denoise", default="off", choices=["off", "vst"])
    ap.add_argument("--starless-bge", default="banded",
                    choices=["banded", "envelope", "border", "gx"])
    ap.add_argument("--cull-pct", type=float, default=0)
    ap.add_argument("--stars-peak", type=float, default=0.85)
    ap.add_argument("--mw-boost", type=float, default=0)
    ap.add_argument("--order", default="bge_first",
                    choices=["bge_first", "sep_first"],
                    help="bge_first: gx+subsky on the STAR-FUL stack, then "
                         "separation (standard order; gx measured MW-safe "
                         "only with stars present). sep_first: the earlier "
                         "arrangement, kept for reference.")
    ap.add_argument("--tag", default=None)
    ap.add_argument("--param", default=None,
                    choices=["starless_target", "starless_denoise",
                             "starless_bge", "cull_pct", "stars_peak",
                             "mw_boost"])
    ap.add_argument("--values", default=None)
    ap.add_argument("--hypothesis", default=None)
    args = ap.parse_args()

    repo = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    sdir = os.path.join(repo, args.session)
    work = os.path.join(sdir, "work")
    stack = os.path.join(sdir, "results", f"stack_{args.set}.fit")
    if not os.path.exists(stack):
        sys.exit(f"starcomb: no {stack}")
    ctx = {"repo": repo, "sdir": sdir, "work": work, "stack": stack}
    if args.order == "sep_first":
        starless_fit, stars_fit, cat_npz = ensure_starsep(repo, sdir, stack)
        ctx.update({"starless_fit": starless_fit, "stars_fit": stars_fit,
                    "cat_npz": cat_npz})

    base = {"starless_target": args.starless_target,
            "starless_denoise": args.starless_denoise,
            "starless_bge": args.starless_bge,
            "cull_pct": args.cull_pct, "stars_peak": args.stars_peak,
            "mw_boost": args.mw_boost, "order": args.order}

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
    enum_params = ("starless_denoise", "starless_bge")
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
        print(f"[starcomb]   combined QA {'PASS' if q['pass'] else 'FAIL'} "
              f"blocks {q['ratio']:.2f} rings {q['ring_l']:.1f}/{q['ring_rg']:.1f}/{q['ring_bg']:.1f}"
              f" | starless-only rings {qs['ring_l']:.1f}/{qs['ring_rg']:.1f}/{qs['ring_bg']:.1f}"
              f" | MW contrast {met['mw_contrast8']:.1f} | stars mid "
              f"{(s.get('mid_peak_med') or 0) * 255:.0f} sat "
              f"{(s.get('sat_star_frac') or 0) * 100:.0f}%")

    with open(os.path.join(exp_dir, "metrics.jsonl"), "w") as f:
        for r in results:
            f.write(json.dumps(r) + "\n")

    cols = ["value", "QA", "blocks", "ring L", "ring RG", "ring BG",
            "SL ringL", "SL ringRG", "MW", "bg", "stars", "mid pk", "sat%",
            "FWHM", "halo"]
    rows = []
    for r in results:
        q, qs, s = r["qa"], r["qa_starless"], r["stars"]
        rows.append([str(r["value"]), "PASS" if q["pass"] else "FAIL",
                     f"{q['ratio']:.2f}", f"{q['ring_l']:.1f}",
                     f"{q['ring_rg']:.1f}", f"{q['ring_bg']:.1f}",
                     f"{qs['ring_l']:.1f}", f"{qs['ring_rg']:.1f}",
                     f"{r['mw_contrast8']:.1f}", f"{r['bg_med8']:.0f}",
                     str(s.get("n_stars", 0)),
                     exp.fmt((s.get("mid_peak_med") or 0) * 255, "{:.0f}"),
                     exp.fmt((s.get("sat_star_frac") or 0) * 100, "{:.0f}"),
                     exp.fmt(s.get("fwhm_med"), "{:.1f}"),
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
              f"[{'PASS' if r['qa']['pass'] else 'FAIL'}]" for r in results]
    exp.compose_rows(strips, labels, os.path.join(exp_dir, "side_by_side.jpg"))
    print(f"\n[starcomb] STOP — user judgment required. Review {exp_dir}/")


if __name__ == "__main__":
    main()
