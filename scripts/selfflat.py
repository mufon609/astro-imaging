#!/usr/bin/env python3
"""Fit a smooth multiplicative gain surface (self-flat) from the median of
unregistered calibrated light frames.

Usage: selfflat.py <median_stack.fit> <gain_out.fit>

The median of an unregistered, drift-dithered sequence keeps only what is
static in sensor coordinates: vignette x sky level (+ dust, + any static
foreground). A degree-4 polynomial is fitted per channel to a block-median
grid with iterative sigma clipping, so localized structure that must NOT
enter a gain surface — foreground silhouettes, star residue, dust dips —
is rejected as outliers. Output: 3-channel float32 FITS, mean 1.0 per
channel, ready for `calibrate ... -flat=`.

Pure numpy; minimal FITS reader/writer (Siril-produced files only).
"""
import sys
import numpy as np

BLOCK = 101          # px per grid cell; big enough to reject star cores
DEGREE = 4           # 2D poly degree: captures cos^4-style falloff incl. r^4
CLIP_SIGMA = 2.5
CLIP_ITERS = 4
GUARD = (0.15, 3.0)  # sane gain range, x mean


def read_fits(path):
    """Minimal FITS: returns float64 array shaped (nchan, ny, nx)."""
    with open(path, "rb") as f:
        raw = f.read()
    hdr = {}
    off = 0
    while True:
        block = raw[off:off + 2880].decode("ascii", "replace")
        off += 2880
        cards = [block[i:i + 80] for i in range(0, 2880, 80)]
        done = False
        for c in cards:
            key = c[:8].strip()
            if key == "END":
                done = True
                break
            if "=" in c:
                val = c[10:].split("/")[0].strip()
                hdr[key] = val
        if done:
            break
        if off >= len(raw):
            sys.exit("selfflat: no END card in FITS header")
    bitpix = int(hdr["BITPIX"])
    naxis = int(hdr["NAXIS"])
    nx = int(hdr["NAXIS1"])
    ny = int(hdr["NAXIS2"])
    nc = int(hdr.get("NAXIS3", "1")) if naxis == 3 else 1
    bzero = float(hdr.get("BZERO", "0"))
    bscale = float(hdr.get("BSCALE", "1"))
    dt = {-32: ">f4", -64: ">f8", 16: ">i2", 32: ">i4", 8: "u1"}[bitpix]
    n = nc * ny * nx
    data = np.frombuffer(raw, dtype=dt, count=n, offset=off).astype(np.float64)
    data = data * bscale + bzero
    return data.reshape(nc, ny, nx)


def write_fits(path, arr):
    """3D float32 FITS (nchan, ny, nx), big-endian, no extras."""
    nc, ny, nx = arr.shape
    cards = [
        "SIMPLE  =                    T",
        "BITPIX  =                  -32",
        "NAXIS   =                    3",
        f"NAXIS1  = {nx:>20d}",
        f"NAXIS2  = {ny:>20d}",
        f"NAXIS3  = {nc:>20d}",
        "END",
    ]
    hdr = "".join(c.ljust(80) for c in cards)
    hdr += " " * (2880 - len(hdr) % 2880)
    body = arr.astype(">f4").tobytes()
    pad = (-len(body)) % 2880
    with open(path, "wb") as f:
        f.write(hdr.encode("ascii"))
        f.write(body)
        f.write(b"\0" * pad)


def block_median_grid(ch):
    ny, nx = ch.shape
    gy, gx = ny // BLOCK, nx // BLOCK
    trimmed = ch[:gy * BLOCK, :gx * BLOCK]
    blocks = trimmed.reshape(gy, BLOCK, gx, BLOCK).transpose(0, 2, 1, 3)
    med = np.median(blocks.reshape(gy, gx, -1), axis=2)
    # block centers in normalized [-1, 1] full-image coordinates
    cy = (np.arange(gy) * BLOCK + BLOCK / 2) / ny * 2 - 1
    cx = (np.arange(gx) * BLOCK + BLOCK / 2) / nx * 2 - 1
    return med, cy, cx


def poly_terms(x, y):
    """All x^i y^j with i+j <= DEGREE; x,y broadcastable."""
    return [x**i * y**j for i in range(DEGREE + 1)
            for j in range(DEGREE + 1 - i)]


def fit_channel(ch, label):
    med, cy, cx = block_median_grid(ch)
    Y, X = np.meshgrid(cy, cx, indexing="ij")
    A = np.stack([t.ravel() for t in poly_terms(X, Y)], axis=1)
    b = med.ravel()
    keep = np.isfinite(b) & (b > 0)
    for _ in range(CLIP_ITERS):
        coef, *_ = np.linalg.lstsq(A[keep], b[keep], rcond=None)
        resid = b - A @ coef
        s = resid[keep].std()
        newkeep = keep & (np.abs(resid) < CLIP_SIGMA * s)
        if newkeep.sum() == keep.sum() or newkeep.sum() < A.shape[1] * 3:
            break
        keep = newkeep
    rejected = 100.0 * (1 - keep.sum() / b.size)
    if rejected > 25:
        sys.exit(f"selfflat: {label}: {rejected:.0f}% of grid rejected — "
                 "median too structured for a gain surface, aborting")

    # evaluate full-res in row chunks (memory-light on this box)
    ny, nx = ch.shape
    xs = np.linspace(-1, 1, nx)
    surf = np.empty(ch.shape, np.float32)
    for r0 in range(0, ny, 256):
        r1 = min(r0 + 256, ny)
        yy = np.linspace(-1, 1, ny)[r0:r1][:, None]
        rows = np.zeros((r1 - r0, nx))
        for c, t in zip(coef, poly_terms(xs[None, :], yy)):
            rows += c * t
        surf[r0:r1] = rows
    surf /= surf.mean()
    lo, hi = GUARD
    surf = np.clip(surf, lo, hi)
    g = surf
    print(f"selfflat {label}: grid rejected {rejected:4.1f}% | gain "
          f"TL {g[0,0]:.3f} TR {g[0,-1]:.3f} BL {g[-1,0]:.3f} "
          f"BR {g[-1,-1]:.3f} min {g.min():.3f} max {g.max():.3f}")
    return surf


def main():
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    data = read_fits(sys.argv[1])
    print(f"selfflat: median stack {data.shape[2]}x{data.shape[1]} "
          f"x{data.shape[0]}ch, level ~{np.median(data):.4g}")
    gain = np.stack([fit_channel(data[c], f"ch{c}")
                     for c in range(data.shape[0])])
    write_fits(sys.argv[2], gain)
    print(f"selfflat: wrote {sys.argv[2]}")


if __name__ == "__main__":
    main()
