#!/usr/bin/env python3
"""Fit the multiplicative vignette (self-flat) from the median of
unregistered calibrated light frames.

Usage: selfflat.py <median_stack.fit> <gain_out.fit>

The median of an unregistered, drift-dithered sequence keeps only what is
static in sensor coordinates: vignette x sky (+ dust, + any static
foreground). That surface is a PRODUCT of two different things and only one
of them may be divided out:

    median(x,y) ~ V(r) * S(x,y)

  V(r)   multiplicative lens vignette — radial, centered on the optical
         axis (image center). This is the gain to remove by division.
  S(x,y) the sky itself — level + glow gradient (moon/horizon), additive
         in origin. Modeled as PLANAR so it cannot absorb V's curvature
         (a planar surface has no r^2 component); subsky removes it later.

Fitting one free-form surface and dividing (v1 of this script) bakes the
glow into the gain: the fitted peak lands off-center toward the bright sky
and division distorts regional brightness. The alternating fit below
separates the factors. Block-median grid + iterative sigma clipping keeps
foreground silhouettes, star residue and dust out of both factors.
Output: 3-channel float32 FITS of V only, V(center)=1, ready for
`calibrate ... -flat=`.

Pure numpy; minimal FITS reader/writer (Siril-produced files only).
"""
import sys
import numpy as np

BLOCK = 101          # px per grid cell; big enough to reject star cores
RADIAL_POWERS = (2, 4, 6)   # V(r) = 1 + k1 r^2 + k2 r^4 + k3 r^6
ALT_ITERS = 6        # alternating V/S refits
CLIP_SIGMA = 2.5
CLIP_ITERS = 4
GUARD = (0.15, 3.0)  # sane gain range


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


def vignette_of(r2, k):
    """V = 1 + k1 r^2 + k2 r^4 + k3 r^6 given r^2 (any shape)."""
    v = np.ones_like(r2)
    for kk, p in zip(k, RADIAL_POWERS):
        v = v + kk * r2 ** (p // 2)
    return v


def fit_channel(ch, label):
    med, cy, cx = block_median_grid(ch)
    Y, X = np.meshgrid(cy, cx, indexing="ij")
    r2 = (X**2 + Y**2) / 2.0          # r^2 normalized: 1.0 at the corners
    b = med.ravel()
    x, y, r2f = X.ravel(), Y.ravel(), r2.ravel()
    keep = np.isfinite(b) & (b > 0)

    # Alternating separation: m ~ V(r; k) * S(planar). Planar S has no r^2
    # term, so all radial curvature is forced into V — no degeneracy.
    k = np.zeros(len(RADIAL_POWERS))
    for it in range(ALT_ITERS):
        V = vignette_of(r2f, k)
        As = np.stack([np.ones_like(x), x, y], axis=1)
        cs, *_ = np.linalg.lstsq(As[keep], (b / V)[keep], rcond=None)
        S = As @ cs
        Av = np.stack([r2f ** (p // 2) for p in RADIAL_POWERS], axis=1)
        target = b / S - 1.0
        k, *_ = np.linalg.lstsq(Av[keep], target[keep], rcond=None)
        resid = b - vignette_of(r2f, k) * S
        s = resid[keep].std()
        if it >= 1:                    # first pass: model still settling
            newkeep = keep & (np.abs(resid) < CLIP_SIGMA * s)
            if newkeep.sum() >= 30:
                keep = newkeep
    rejected = 100.0 * (1 - keep.sum() / b.size)
    if rejected > 25:
        sys.exit(f"selfflat: {label}: {rejected:.0f}% of grid rejected — "
                 "median too structured for a gain surface, aborting")

    # evaluate V full-res in row chunks (memory-light on this box)
    ny, nx = ch.shape
    xs = np.linspace(-1, 1, nx)[None, :]
    surf = np.empty(ch.shape, np.float32)
    for row0 in range(0, ny, 256):
        row1 = min(row0 + 256, ny)
        yy = np.linspace(-1, 1, ny)[row0:row1][:, None]
        surf[row0:row1] = vignette_of((xs**2 + yy**2) / 2.0,
                                      k).astype(np.float32)
    lo, hi = GUARD
    surf = np.clip(surf, lo, hi)       # V(center)=1 by construction
    g = surf
    tilt = 100.0 * np.hypot(cs[1], cs[2]) / cs[0]
    print(f"selfflat {label}: grid rejected {rejected:4.1f}% | vignette "
          f"corners TL {g[0,0]:.3f} TR {g[0,-1]:.3f} BL {g[-1,0]:.3f} "
          f"BR {g[-1,-1]:.3f} | glow tilt {tilt:.1f}%/half-frame "
          f"(left additive, for subsky)")
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
