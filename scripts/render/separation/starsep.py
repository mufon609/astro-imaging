#!/usr/bin/env python3
"""Star separation on the linear stack: starless + stars layers.

Usage: starsep.py <stack.fit> <outdir>

The standard DSO workflow isolates stars (StarNet/StarXTerminator) so the
extended emission and the stars can be stretched independently and the
background model sees clean data. No StarNet build exists for aarch64, so
this is a classic mask+inpaint separation, tuned for THIS data (trailed
8px smears, no diffraction spikes — friendlier than tight PSFs):

- detection on max-over-channels vs a LOCAL background map (large-scale
  median), so the MW glow does not raise the threshold
- component filter keeps STARS and protects MW structure: compact area,
  peak prominence >= 6 sigma; big areas allowed only for very bright cores
  (saturated star halos)
- the foreground branch region (bottom-left, bg_qa geometry) is left
  untouched: it is not sky
- inpaint: coarse masked-mean pyramid seed + Jacobi 3x3 diffusion iterations
  confined to the mask, then matched gaussian noise so the fill does not
  render as smooth blobs under a hard stretch
- stars = clip(original - starless, 0); a component catalog (label id,
  flux, peak, area) is saved so recombination can cull faint stars

Outputs in <outdir>: starless_<stem>.fit, stars_<stem>.fit,
starsep_<stem>.npz (labels + catalog), all cached by stack identity.
"""
import os
import sys
import numpy as np
from scipy import ndimage

# scripts/lib holds the shared libs (astrometrics, bg_qa); locate it by
# walking up from this file so one bootstrap works at any nesting depth.
_libdir = os.path.dirname(os.path.abspath(__file__))
while _libdir != os.path.dirname(_libdir):
    if os.path.isdir(os.path.join(_libdir, "lib")):
        sys.path.insert(0, os.path.join(_libdir, "lib"))
        break
    _libdir = os.path.dirname(_libdir)
import astrometrics as am  # noqa: E402

K_DETECT = 4.0        # detection threshold above local bg, in sigma
K_PROM = 6.0          # component peak prominence to count as a star
AREA_MAX = 1500       # px, normal stars (trailed smears included)
AREA_MAX_BRIGHT = 12000   # px, saturated cores + halos
K_BRIGHT = 40.0       # prominence that unlocks AREA_MAX_BRIGHT
DILATE_ALL = 3        # skirt for every star, px
DILATE_BRIGHT = 5     # extra skirt for bright stars
JACOBI_ITERS = 40

# Machine-readable output contract: both separators end with ONE line of this
# form carrying the three output paths, tab-separated (fresh run AND cache
# hit). starcomb._run_sep parses THIS sentinel, not "lines ending .fit/.npz",
# so a future diagnostic print can never be mistaken for an output path.
TRIO_SENTINEL = "SEPTRIO"


def emit_trio(p_starless, p_stars, p_cat):
    """Print the starless/stars/catalog trio as the machine-readable sentinel
    line starcomb parses. Keep it the last line the separator prints."""
    print(f"{TRIO_SENTINEL}\t{p_starless}\t{p_stars}\t{p_cat}")


def write_fits_fitsorder(path, data_display):
    """float32 (C,H,W) display-oriented -> FITS (bottom-up rows).

    A single-channel image is written as a 2D FITS (NAXIS=2, no NAXIS3) — the
    convention siril writes and reads for mono. A degenerate NAXIS3=1 cube is
    legal FITS but siril's reader rejects it."""
    arr = data_display[:, ::-1, :]
    nc, ny, nx = arr.shape
    cards = ["SIMPLE  =                    T", "BITPIX  =                  -32",
             f"NAXIS   = {2 if nc == 1 else 3:>20d}",
             f"NAXIS1  = {nx:>20d}", f"NAXIS2  = {ny:>20d}"]
    if nc > 1:
        cards.append(f"NAXIS3  = {nc:>20d}")
    cards.append("END")
    hdr = "".join(c.ljust(80) for c in cards)
    hdr += " " * (2880 - len(hdr) % 2880)
    body = arr.astype(">f4").tobytes()
    pad = (-len(body)) % 2880
    with open(path, "wb") as f:
        f.write(hdr.encode("ascii"))
        f.write(body)
        f.write(b"\0" * pad)


def local_background(L, stride=4, size=33):
    """Large-scale background map (median filter on a downsample)."""
    small = L[::stride, ::stride]
    bg = ndimage.median_filter(small, size=size, mode="nearest")
    return ndimage.zoom(bg, (L.shape[0] / bg.shape[0],
                             L.shape[1] / bg.shape[1]), order=1)


def build_star_mask(data, k_prom=None):
    if k_prom is None:
        k_prom = K_PROM
    L = data.max(axis=0)
    h, w = L.shape
    bgmap = local_background(L)
    _, sig = am.bg_stats(L)
    resid = L - bgmap
    cand = resid > K_DETECT * sig
    cand &= am.branch_mask(h, w)          # never treat the branch as stars
    labels, n = ndimage.label(cand)
    if n == 0:
        sys.exit("starsep: no components found — wrong input?")
    idx = np.arange(1, n + 1)
    area = ndimage.sum_labels(cand, labels, idx)
    peak = ndimage.maximum(resid, labels, idx)
    is_star = (peak >= k_prom * sig) & (
        (area <= AREA_MAX) | ((peak >= K_BRIGHT * sig) & (area <= AREA_MAX_BRIGHT)))
    star_ids = idx[is_star]
    mask = np.isin(labels, star_ids)
    bright_ids = idx[is_star & (peak >= K_BRIGHT * sig)]
    mask = ndimage.binary_dilation(mask, iterations=DILATE_ALL)
    if len(bright_ids):
        bm = np.isin(labels, bright_ids)
        bm = ndimage.binary_dilation(bm, iterations=DILATE_ALL + DILATE_BRIGHT)
        mask |= bm
    # catalog on the undilated labels: flux above local bg per component
    flux = ndimage.sum_labels(np.clip(resid, 0, None), labels, idx)
    cat = {"ids": star_ids,
           "flux": flux[is_star],
           "peak": peak[is_star],
           "area": area[is_star]}
    stats = {"n_components": int(n), "n_stars": int(is_star.sum()),
             "mask_frac": float(mask.mean()), "sigma": float(sig)}
    return mask, labels, cat, stats


def inpaint(ch, mask):
    """Multi-scale seed + Jacobi diffusion confined to the mask."""
    out = ch.copy()
    # coarse seed: masked mean pooling at /8, nan-fill, upsample
    s = 8
    h, w = ch.shape
    hh, ww = h // s, w // s
    val = np.where(mask, np.nan, ch)[:hh * s, :ww * s].reshape(hh, s, ww, s)
    with np.errstate(invalid="ignore"):
        coarse = np.nanmean(val.transpose(0, 2, 1, 3).reshape(hh, ww, -1), axis=2)
    for _ in range(50):
        nans = np.isnan(coarse)
        if not nans.any():
            break
        m = np.where(np.isnan(coarse), 0, coarse)
        cnt = ndimage.uniform_filter((~np.isnan(coarse)).astype(np.float32), 3)
        sm = ndimage.uniform_filter(m, 3)
        est = np.where(cnt > 0, sm / np.maximum(cnt, 1e-6), np.nan)
        coarse[nans] = est[nans]
    coarse = np.nan_to_num(coarse, nan=float(np.nanmedian(coarse)))
    seed = ndimage.zoom(coarse, (h / hh, w / ww), order=1)[:h, :w]
    out[mask] = seed[mask]
    # diffusion: repeated 3x3 mean, replacing only masked px
    for _ in range(JACOBI_ITERS):
        sm = ndimage.uniform_filter(out, 3)
        out[mask] = sm[mask]
    return out


def main():
    global AREA_MAX, AREA_MAX_BRIGHT
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    opts = dict(a[2:].split("=", 1) for a in sys.argv[1:]
                if a.startswith("--") and "=" in a)
    k_prom = float(opts.get("prom", K_PROM))
    if len(args) != 2:
        sys.exit(__doc__)
    stack_path, outdir = args
    if "session" in opts and "set" in opts:
        # per-set geometry (foreground never-star zone) + optional starsep
        # overrides (area caps are px^2: tuned on 8px-trailed 37mm stars,
        # config-overridable for very different scales)
        ctx = am.configure(opts["session"], opts["set"], quiet=True)
        AREA_MAX = int(ctx.starsep.get("area_max", AREA_MAX))
        AREA_MAX_BRIGHT = int(ctx.starsep.get("area_max_bright",
                                              AREA_MAX_BRIGHT))
    os.makedirs(outdir, exist_ok=True)
    st = os.stat(stack_path)
    # prom is part of the separation identity; default keeps the original names
    stem = f"{st.st_size}_{int(st.st_mtime)}"
    if k_prom != K_PROM:
        stem += f"_p{k_prom:g}"
    p_starless = os.path.join(outdir, f"starless_{stem}.fit")
    p_stars = os.path.join(outdir, f"stars_{stem}.fit")
    p_cat = os.path.join(outdir, f"starsep_{stem}.npz")
    if all(os.path.exists(p) for p in (p_starless, p_stars, p_cat)):
        print(f"starsep: cache hit {os.path.basename(p_starless)}")
        emit_trio(p_starless, p_stars, p_cat)
        return
    data, _ = am.load_image(stack_path)
    print(f"starsep: {data.shape[2]}x{data.shape[1]}x{data.shape[0]}ch "
          f"(prominence {k_prom:g} sigma)")
    mask, labels, cat, stats = build_star_mask(data, k_prom)
    print(f"starsep: components {stats['n_components']}, stars kept "
          f"{stats['n_stars']}, masked {stats['mask_frac'] * 100:.2f}% of frame")
    starless = np.empty_like(data)
    rng = np.random.default_rng(20260706)
    for c in range(data.shape[0]):
        starless[c] = inpaint(data[c], mask)
        _, sigc = am.bg_stats(data[c])
        noise = rng.normal(0.0, 0.7 * sigc, size=int(mask.sum())).astype(np.float32)
        starless[c][mask] = np.clip(starless[c][mask] + noise, 0.0, 1.0)
    stars = np.clip(data - starless, 0.0, None)
    write_fits_fitsorder(p_starless, starless)
    write_fits_fitsorder(p_stars, stars)
    np.savez_compressed(p_cat, labels=labels.astype(np.uint32),
                        ids=cat["ids"], flux=cat["flux"], peak=cat["peak"],
                        area=cat["area"], mask_frac=stats["mask_frac"])
    resid = am.star_metrics(starless[min(1, starless.shape[0] - 1)])
    print(f"starsep: starless residual star count {resid.get('n_stars', 0)} "
          f"(detector w/ prominence floor; input had thousands)")
    emit_trio(p_starless, p_stars, p_cat)


if __name__ == "__main__":
    main()
