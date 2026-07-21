#!/usr/bin/env python3
"""Normalization-invariant regional SNR ladder across stacks (the depth
instrument BACKLOG item 8 names).

SNR here = (median of a signal region − median of a sky region) / the
image's background-noise estimate — computed WITHIN each stack, so the
per-stack `-output_norm` scale cancels and the ratios compare across
stacks of different depth. Every measurement is Siril's own (`crop` +
`stat` regional medians, `bgnoise` estimator); astropy maps the SAME sky
boxes into each stack's pixels via its WCS. The only in-house computation
is the ratio itself — a derived result no tool provides regionally
(removal condition: a tool exposing headless regional SNR retires this).

Usage: snr_regions.py <out.json> <stack.fit>... \
           --signal=RA,DEC --sky=RA,DEC [--box-arcmin=20]

Boxes are squares centred on the given coordinates; a stack whose WCS
places a box outside (or partially outside) its frame is reported SKIPPED,
never silently included. Run on LIKE surfaces only (e.g. the linear _spcc
stacks) — the ratio is scale-free but not stretch-free.
"""
import json
import os
import re
import subprocess
import sys

import numpy as np
from astropy.io import fits
from astropy.wcs import WCS

SIRIL = ["flatpak", "run", "--command=siril-cli", "org.siril.Siril"]


def siril_lines(workdir, script):
    ssf = os.path.join(workdir, "_snr.ssf")
    with open(ssf, "w") as f:
        f.write(script)
    r = subprocess.run(SIRIL + ["-d", workdir, "-s", ssf],
                       capture_output=True, text=True)
    os.remove(ssf)
    return (r.stdout + r.stderr).splitlines()


def region_medians(stack, x, y, box, workdir):
    lines = siril_lines(workdir,
                        f"requires 1.2.0\nsetcompress 0\nload {stack}\n"
                        f"crop {x} {y} {box} {box}\nstat\n")
    meds = []
    for line in lines:
        m = re.search(r"Mean: ([0-9.]+), Median: ([0-9.]+), Sigma:", line)
        if m:
            # mean carries sub-ADU resolution the integer-quantized median
            # lacks (16-bit stacks); record both, SNR uses the mean
            meds.append({"mean": float(m.group(1)), "median": float(m.group(2))})
    return meds


def bgnoise(stack, workdir):
    lines = siril_lines(workdir,
                        f"requires 1.2.0\nsetcompress 0\nload {stack}\nbgnoise\n")
    vals = []
    for line in lines:
        m = re.search(r"Background noise value \(channel: #\d\): ([0-9.]+)", line)
        if m:
            vals.append(float(m.group(1)))
    return vals


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    opts = dict(a[2:].split("=", 1) for a in sys.argv[1:]
                if a.startswith("--") and "=" in a)
    if len(args) < 2 or "signal" not in opts or "sky" not in opts:
        sys.exit(__doc__)
    out_json, stacks = os.path.abspath(args[0]), [os.path.abspath(a) for a in args[1:]]
    sig_rd = [float(v) for v in opts["signal"].split(",")]
    sky_rd = [float(v) for v in opts["sky"].split(",")]
    box_am = float(opts.get("box-arcmin", 20))
    workdir = os.path.dirname(out_json)
    os.makedirs(workdir, exist_ok=True)

    rec = {"method": "internal ratio (median_signal - median_sky) / bgnoise per "
                     "channel; Siril crop+stat medians + bgnoise; boxes "
                     "WCS-anchored (astropy); normalization-invariant across "
                     "stacks, valid on LIKE (linear) surfaces only",
           "signal_radec": sig_rd, "sky_radec": sky_rd,
           "box_arcmin": box_am, "stacks": {}}
    for stack in stacks:
        name = os.path.basename(stack)
        hdr = fits.getheader(stack)
        w, hgt = hdr["NAXIS1"], hdr["NAXIS2"]
        try:
            wcs = WCS(hdr, naxis=2)
            scale_deg = np.sqrt(abs(np.linalg.det(wcs.pixel_scale_matrix)))
        except Exception as e:
            rec["stacks"][name] = {"skipped": f"no usable WCS ({e})"}
            continue
        box_px = int(round(box_am / 60.0 / scale_deg))
        entry = {"box_px": box_px, "regions": {}}
        ok = True
        for label, (ra, dec) in (("signal", sig_rd), ("sky", sky_rd)):
            px = wcs.all_world2pix([[ra, dec]], 0)[0]
            x_np = int(round(px[0])) - box_px // 2
            y_np = int(round(px[1])) - box_px // 2
            if x_np < 0 or y_np < 0 or x_np + box_px > w or y_np + box_px > hgt:
                entry["regions"][label] = "outside frame"
                ok = False
                continue
            # Siril crop's y-origin is the OPPOSITE end from FITS row order
            # (measured; docs/dead-ends.md) — flip for the tool call.
            y_sir = hgt - y_np - box_px
            meds = region_medians(stack, x_np, y_sir, box_px, workdir)
            if not meds:
                entry["regions"][label] = "stat parse failed"
                ok = False
                continue
            entry["regions"][label] = meds
        if ok:
            noise = bgnoise(stack, workdir)
            entry["bgnoise"] = noise
            sig, sky = entry["regions"]["signal"], entry["regions"]["sky"]
            if noise and len(noise) == len(sig):
                entry["snr_per_channel"] = [
                    round((s["mean"] - k["mean"]) / n, 2) for s, k, n in
                    zip(sig, sky, noise)]
        rec["stacks"][name] = entry
    with open(out_json, "w") as f:
        json.dump(rec, f, indent=1)
    for name, e in rec["stacks"].items():
        print(name, "->", e.get("snr_per_channel", e.get("skipped", e.get("regions"))))
    print("record:", out_json)


if __name__ == "__main__":
    main()
