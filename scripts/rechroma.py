#!/usr/bin/env python3
"""Zero the additive residual of glow-subtracted frames (per channel).

Usage: rechroma.py <workdir> <nframes>

WHY (measured 2026-07-06, NOTES.md "RIM/RING ROOT CAUSE" + "(L) ROOT
CAUSE"): the pipeline divides glow-subtracted frames by the self-flat
V(r). Division only returns a flat sky if the frame is purely
multiplicative, bkg_c ≈ V(r)·S̄_c. siril's seqsubsky leaves each channel
re-centered on its own median (flipping rim chroma positive: the magenta
rim) and an arbitrary additive pedestal (whose division by V(r) prints
the -16% luminance rim).

FIX: shift every channel of every frame by ONE constant so its median
equals the model-consistent target C_c * median(V) computed by
selfflat.py (work/selfflat_levels.json). With the additive part ~zero,
bkg_c/V ≈ S̄_c: flat in luminance and chroma. Constants cannot create
spatial structure.

Reads bkg_pp_light_NNNNN.fit, rewrites in place (same layout).
"""
import json
import os
import sys
import numpy as np


def read_fits_raw(path):
    """(header_bytes, data float32 (C,H,W) in FILE units, bitpix, bzero)."""
    with open(path, "rb") as f:
        raw = f.read()
    hdr = {}
    off = 0
    while True:
        block = raw[off:off + 2880].decode("ascii", "replace")
        off += 2880
        done = False
        for i in range(0, 2880, 80):
            c = block[i:i + 80]
            if c[:8].strip() == "END":
                done = True
                break
            if "=" in c:
                hdr[c[:8].strip()] = c[10:].split("/")[0].strip()
        if done:
            break
        if off >= len(raw):
            sys.exit(f"rechroma: no END card in {path}")
    bitpix = int(hdr["BITPIX"])
    nx, ny = int(hdr["NAXIS1"]), int(hdr["NAXIS2"])
    nc = int(hdr.get("NAXIS3", "1")) if int(hdr["NAXIS"]) == 3 else 1
    bzero = float(hdr.get("BZERO", "0"))
    dt = {-32: ">f4", 16: ">i2"}[bitpix]
    data = np.frombuffer(raw, dtype=dt, count=nc * ny * nx, offset=off)
    data = data.astype(np.float32) + bzero
    return raw[:off], data.reshape(nc, ny, nx), bitpix, bzero


def write_back(path, header_bytes, data, bitpix, bzero):
    if bitpix == 16:
        body = np.clip(np.rint(data - bzero), -32768, 32767) \
                 .astype(">i2").tobytes()
    else:
        body = (data - bzero).astype(">f4").tobytes()
    pad = (-len(body)) % 2880
    with open(path, "wb") as f:
        f.write(header_bytes)
        f.write(body)
        f.write(b"\0" * pad)


def main():
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    w = sys.argv[1]
    n = int(sys.argv[2])
    levels = json.load(open(os.path.join(w, "selfflat_levels.json")))
    targets = levels["target_median_16bit"]
    print(f"rechroma: targets per channel (16-bit counts): "
          f"{['%.1f' % t for t in targets]} = C x median(V) "
          f"({levels['median_V']:.4f})")
    for i in range(1, n + 1):
        bk = os.path.join(w, f"bkg_pp_light_{i:05d}.fit")
        if not os.path.exists(bk):
            print(f"rechroma: frame {i}: missing, skipped")
            continue
        hdr, bkg, bitpix, bzero = read_fits_raw(bk)
        if bkg.shape[0] != len(targets):
            sys.exit("rechroma: channel count mismatch vs selfflat_levels")
        shifts = []
        for c in range(bkg.shape[0]):
            med = float(np.median(bkg[c][::4, ::4]))
            if bitpix == -32:
                med *= 65535.0  # float frames: compare in 16-bit counts
            shift = targets[c] - med
            # Sanity guard: a constant re-centering is a small correction.
            # A target far from the current median means a unit mismatch or
            # a model breakdown — abort BEFORE touching any file (the first
            # L1 attempt exported float-unit targets that would have zeroed
            # every background).
            if abs(shift) > 0.75 * max(med, 1.0):
                sys.exit(f"rechroma: frame {i} ch{c}: target {targets[c]:.1f}"
                         f" vs median {med:.1f} — shift {shift:+.1f} exceeds"
                         " 60% of the level; unit mismatch/model breakdown,"
                         " aborting with frames untouched")
            shifts.append(shift)
        for c in range(bkg.shape[0]):
            bkg[c] += shifts[c] / (65535.0 if bitpix == -32 else 1.0)
        write_back(bk, hdr, bkg, bitpix, bzero)
        print(f"rechroma: frame {i:2d}: "
              + " ".join(f"{'RGB'[c]}{shifts[c]:+7.1f}"
                         for c in range(len(shifts))))


if __name__ == "__main__":
    main()
