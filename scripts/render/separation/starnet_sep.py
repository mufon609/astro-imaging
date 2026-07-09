#!/usr/bin/env python3
"""Star separation by StarNet2 ONNX inference.

Usage: starnet_sep.py <stack.fit> <outdir> [--session=<dir> --set=<name>]
                      [--stride=256] [--target=0.25] [--upsample]
                      [--base-starless=<fit>]

--base-starless runs the net on that layer instead of the stack (the
hybrid engine): with the mask+inpaint starless as base, bright star
disks are already flat-filled (the net leaves a residual halo pedestal
under bright stars when it removes them itself — measured +8/+7
counts16 at r0-4/4-8, vs +0.3 for the inpaint fill) and the net only
has to remove what the mask engine cannot: the <6 sigma faint tail.
stars and the catalog are still computed against the ORIGINAL stack.

The official StarNet2 CLI (v2.5.3) ships Linux x64 only, but its
package carries the model as a loose file — StarNet2_weights.onnx
(131 MB, 32.9M params, NHWC 1x512x512x3 float32; input/output in
[0,1], a clip-to-[0,1] tail is baked into the graph). This driver runs
those weights on aarch64 through the onnxruntime wheel (~0.3 s per
512px tile on 4 ARM cores, bit-deterministic between calls):

- linked MTF pre-stretch with ZERO shadow clip, midtone solved so the
  background median lands on `target` (the net is trained on stretched
  images; siril's own starnet command wraps linear data the same way).
  Zero clip keeps the transfer bijective, so the inverse MTF
  (midtone 1-m) restores the linear domain exactly (roundtrip error
  asserted < 1e-5 at runtime).
- 512px processing window at `stride` (official CLI default 256),
  reflect padding, output assembled from each tile's central
  stride x stride block — overlap-consistent, no seams to blend.
- stars = clip(original - starless, 0) and the SAME detection catalog
  as starsep.py (build_star_mask imported from it), so culling,
  anchoring and star-shell sampling measure both engines identically.

Weights file: ~/.local/share/starnet/StarNet2_weights.onnx — copied
from the official starnet2_linux_*_ORT_x64_cli.zip
(download.starnetastro.com). Its license grants personal
astrophotography use only; keep the weights out of the repo. Runs in
its own auto-bootstrapped venv (~/.local/share/starnet/venv:
onnxruntime + numpy + scipy + pillow).

Outputs in <outdir>: starless_<stem>.fit, stars_<stem>.fit,
starsep_<stem>.npz with stem = {size}_{mtime}_net — the starsep.py
trio contract, cached by stack identity.
"""
import os
import subprocess
import sys
import time

# scripts/lib holds the shared libs (astrometrics, bg_qa); locate it by
# walking up from this file so one bootstrap works at any nesting depth.
_libdir = os.path.dirname(os.path.abspath(__file__))
while _libdir != os.path.dirname(_libdir):
    if os.path.isdir(os.path.join(_libdir, "lib")):
        sys.path.insert(0, os.path.join(_libdir, "lib"))
        break
    _libdir = os.path.dirname(_libdir)

VENV = os.path.expanduser("~/.local/share/starnet/venv")
WEIGHTS = os.path.expanduser("~/.local/share/starnet/StarNet2_weights.onnx")
WINDOW = 512


def bootstrap():
    py = os.path.join(VENV, "bin", "python")
    # compare sys.prefix, not executable realpaths: the venv python is a
    # symlink to the system python, so realpath() says "already inside"
    # while running OUTSIDE the venv and the onnxruntime import fails
    if os.path.realpath(sys.prefix) != os.path.realpath(VENV):
        if not os.path.exists(py):
            print(f"[starnet_sep] creating venv {VENV} + installing "
                  "onnxruntime/numpy/scipy/pillow (one-time)")
            subprocess.run([sys.executable, "-m", "venv", VENV], check=True)
            subprocess.run([py, "-m", "pip", "install", "--quiet",
                            "onnxruntime", "numpy", "scipy", "pillow"],
                           check=True)
        os.execv(py, [py] + sys.argv)


def solve_mtf_m(x0, y0):
    """Midtone m such that mtf(x0, m) = y0 (closed form)."""
    return x0 * (y0 - 1.0) / (2.0 * x0 * y0 - y0 - x0)


def run_tiled(sess, img_hwc, stride):
    """512px window over reflect-padded input; keep each output tile's
    central stride x stride block. With window - stride of context on
    every side of each kept block, adjacent tiles agree and no blend
    weighting is needed."""
    import numpy as np
    h, w, _ = img_hwc.shape
    margin = (WINDOW - stride) // 2
    ny = -(-h // stride)
    nx = -(-w // stride)
    ph = (ny - 1) * stride + WINDOW
    pw = (nx - 1) * stride + WINDOW
    pad = ((margin, ph - h - margin), (margin, pw - w - margin), (0, 0))
    padded = np.pad(img_hwc, pad, mode="reflect")
    del img_hwc     # 2x-upsampled inputs are ~1.2 GB; keep one copy live
    out = np.empty_like(padded)
    t0 = time.time()
    for iy in range(ny):
        for ix in range(nx):
            y0, x0 = iy * stride, ix * stride
            tile = padded[y0:y0 + WINDOW, x0:x0 + WINDOW][None]
            res = sess.run(None, {"x:0": tile})[0][0]
            out[y0 + margin:y0 + margin + stride,
                x0 + margin:x0 + margin + stride] = \
                res[margin:margin + stride, margin:margin + stride]
        done = (iy + 1) * nx
        rate = done / (time.time() - t0)
        print(f"[starnet_sep] tiles {done}/{ny * nx} "
              f"({rate:.1f}/s)", flush=True)
    return out[margin:margin + h, margin:margin + w]


def main():
    bootstrap()
    import numpy as np

    import astrometrics as am
    import starsep

    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    opts = dict(a[2:].split("=", 1) for a in sys.argv[1:]
                if a.startswith("--") and "=" in a)
    if len(args) != 2:
        sys.exit(__doc__)
    stack_path, outdir = args
    stride = int(opts.get("stride", 256))
    target = float(opts.get("target", 0.25))
    upsample = "--upsample" in sys.argv[1:]
    base_starless = opts.get("base-starless")
    if stride % 2 or not (2 <= stride <= WINDOW):
        sys.exit("starnet_sep: stride must be even and in [2, 512]")
    if not os.path.exists(WEIGHTS):
        sys.exit(f"starnet_sep: weights missing at {WEIGHTS}\n"
                 "Fetch the official Linux x64 CLI package from "
                 "download.starnetastro.com (starnet2_linux_*_ORT_x64_cli"
                 ".zip) and copy StarNet2_weights.onnx there.")
    if "session" in opts and "set" in opts:
        am.configure(opts["session"], opts["set"], quiet=True)

    os.makedirs(outdir, exist_ok=True)
    st = os.stat(stack_path)
    stem = f"{st.st_size}_{int(st.st_mtime)}_net"
    if base_starless:
        stem += "h"
    if stride != 256:
        stem += f"_s{stride}"
    if upsample:
        stem += "_u"
    if target != 0.25:
        stem += f"_t{target:g}"
    p_starless = os.path.join(outdir, f"starless_{stem}.fit")
    p_stars = os.path.join(outdir, f"stars_{stem}.fit")
    p_cat = os.path.join(outdir, f"starsep_{stem}.npz")
    if all(os.path.exists(p) for p in (p_starless, p_stars, p_cat)):
        print(f"starnet_sep: cache hit {os.path.basename(p_starless)}")
        starsep.emit_trio(p_starless, p_stars, p_cat)
        return

    data, _ = am.load_image(stack_path)
    if data.shape[0] == 1:
        data = np.repeat(data, 3, axis=0)
    clipped = float(np.mean((data < 0) | (data > 1)))
    if clipped > 0:
        print(f"[starnet_sep] input outside [0,1]: {clipped * 100:.3f}% "
              "clipped before stretch")
    data = np.clip(data, 0.0, 1.0)
    c, h, w = data.shape
    if h < WINDOW or w < WINDOW:
        sys.exit(f"starnet_sep: image {w}x{h} smaller than the "
                 f"{WINDOW}px window")
    if base_starless:
        net_in, _ = am.load_image(base_starless)
        net_in = np.clip(net_in, 0.0, 1.0)
        if net_in.shape != data.shape:
            sys.exit(f"starnet_sep: base starless shape {net_in.shape} "
                     f"!= stack {data.shape}")
        print(f"[starnet_sep] hybrid: net runs on "
              f"{os.path.basename(base_starless)}")
    else:
        net_in = data

    # linked pre-stretch: one m from the G-channel background median,
    # zero shadow clip -> exactly invertible
    med, _ = am.bg_stats(net_in[min(1, c - 1)])
    m_pre = solve_mtf_m(float(med), target)
    grid = np.linspace(0.0, 1.0, 1025)
    err = float(np.abs(am.mtf(am.mtf(grid, m_pre), 1.0 - m_pre) - grid).max())
    assert err < 1e-5, f"MTF roundtrip error {err}"
    stretched = am.mtf(net_in.astype(np.float64), m_pre).astype(np.float32)
    if base_starless:
        del net_in
    print(f"[starnet_sep] pre-stretch: bg med {med:.5f} -> {target} "
          f"(m {m_pre:.5f}, roundtrip err {err:.1e})")

    import onnxruntime as ort
    so = ort.SessionOptions()
    so.intra_op_num_threads = os.cpu_count()
    sess = ort.InferenceSession(WEIGHTS, sess_options=so,
                                providers=["CPUExecutionProvider"])
    print(f"[starnet_sep] {w}x{h}x{c}ch, window {WINDOW} stride {stride}"
          + (" 2x-upsampled" if upsample else ""))
    if upsample:
        # the official CLI's bright-star mode: infer on a 2x bilinear
        # upsample, then exact 2x2-mean back down — the net sees big
        # star profiles at half their apparent scale, where its removal
        # is more complete (4x the tiles, ~4x the runtime)
        from scipy import ndimage as _nd
        sl2 = run_tiled(sess, _nd.zoom(stretched.transpose(1, 2, 0),
                                       (2.0, 2.0, 1.0), order=1), stride)
        sl_stretched = sl2.reshape(h, 2, w, 2, c).mean(axis=(1, 3),
                                                       dtype=np.float32)
        del sl2
    else:
        sl_stretched = run_tiled(sess, stretched.transpose(1, 2, 0), stride)

    starless = am.mtf(np.clip(sl_stretched, 0.0, 1.0).astype(np.float64)
                      .transpose(2, 0, 1), 1.0 - m_pre)
    starless = np.clip(starless, 0.0, 1.0).astype(np.float32)

    # the foreground branch is not sky: the net treats its bright pixels
    # as stars and eats them (measured -221 counts16 structure loss in
    # the treeline patch). Same policy as the mask engine (which excludes
    # the branch from detection): starless keeps the input there, stars
    # carry nothing. 8px cosine feather so the boundary does not print
    # as a texture step.
    sky = am.branch_mask(h, w)
    if not sky.all():
        from scipy import ndimage
        dist = ndimage.distance_transform_edt(sky)
        wgt = np.where(dist >= 8.0, 1.0,
                       0.5 - 0.5 * np.cos(np.pi * dist / 8.0)).astype(np.float32)
        starless = data + wgt[None] * (starless - data)
        print(f"[starnet_sep] foreground restored from input "
              f"({(~sky).mean() * 100:.2f}% of frame, 8px feather)")
    stars = np.clip(data - starless, 0.0, None)

    # same detection catalog as the mask+inpaint engine: the catalog is
    # a measurement of the sky (components above local bg), not of the
    # separation — identical machinery keeps the engines comparable
    _, labels, cat, stats = starsep.build_star_mask(data)
    starsep.write_fits_fitsorder(p_starless, starless)
    starsep.write_fits_fitsorder(p_stars, stars)
    np.savez_compressed(p_cat, labels=labels.astype(np.uint32),
                        ids=cat["ids"], flux=cat["flux"], peak=cat["peak"],
                        area=cat["area"], mask_frac=stats["mask_frac"])
    resid = am.star_metrics(starless[min(1, starless.shape[0] - 1)])
    print(f"starnet_sep: catalog stars {stats['n_stars']}, starless "
          f"residual star count {resid.get('n_stars', 0)}")
    starsep.emit_trio(p_starless, p_stars, p_cat)


if __name__ == "__main__":
    main()
