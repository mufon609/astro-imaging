#!/usr/bin/env python3
"""Which local Gaia SPCC catalog chunks does a plate-solved field need?

SPCC (siril `spcc -catalog=localgaia`) reads the xpsamp catalog split into
nside=2 NESTED HEALPix pixels (files `siril_cat1_healpix8_xpsamp_<N>.dat`,
N in 0..47, equatorial/ICRS). Siril fails, naming ONE missing chunk at a
time, if the field's cone is not fully covered — painful for a southern
field when only northern chunks are installed. This computes the cover up
front from the solved header and (optionally) fetches the missing chunks.

Usage:
  spcc_cone.py <solved_stack.fit> [--radius-deg=N] [--fetch]
  spcc_cone.py --ra=R --dec=D --radius-deg=N [--fetch]

Centre = the full WCS evaluated at the image-centre pixel (astropy; CRVAL
alone is the tangent point, not the pointing); the cone radius defaults to the
centre-to-corner maximum + 0.5 deg margin (override with --radius-deg).
`--fetch` downloads any missing chunk from the Zenodo record (md5-verified,
decompressed in place).

The HEALPix ang2pix (nested) is the standard algorithm in numpy — no healpy.
Validated against a hand-checked reference cover (an 11-chunk cover for a
33.5 deg cone).

REMOVAL CONDITION (two clauses, each evaluated separately): (a) the nested
ang2pix cover retires when siril 1.5's `healpix` command is adopted and its
pixel list is verified to map to the zenodo chunk names (BACKLOG `siril-1.5`),
or when astropy_healpix is adopted into this script's interpreter (installed
in /opt/astro-venv, ABSENT from host python3 — TOOLS.md). NOT FIRED.
(b) FIRED, owner-directed, the day it was ratified: the hand-rolled
`_tan_pix2sky` gnomonic step moved to astropy WCS built from the CD ALONE.
Measured A/B over every solved product on disk: chunk lists identical on all
34; the retired hand-roll carried up to 162 arcsec centre and 0.33 deg radius
error against the CD-only evaluation, whose centres agree with the headers'
own OBJCTRA/OBJCTDEC at median 1.7 / worst 36.5 arcsec (the hand-roll: median
17.8 / worst 151.6). The swap's first attempt exposed the dual-matrix trap
the in-function comment states (astropy fed the leftover PC+CDELT: 0.25 deg
skew) — registry + BACKLOG `wcs-dual-matrix-inject`. Consequence bound
stands: chunk SELECTION only, and siril names any missing chunk loudly.
Registered in BACKLOG `removal-conditions` (conditions authored by audit —
this divergence shipped with none; RATIFIED by the owner 2026-08-19).
"""
import os
import re
import sys
import subprocess

import numpy as np

ZENODO_RECORD = "14738271"
SPCC_DIR = os.path.expanduser("~/.local/share/siril/siril_catalogues/spcc")
CHUNK = "siril_cat1_healpix8_xpsamp_{}.dat"


def ang2pix_nest_nside2(ra_deg, dec_deg):
    """HEALPix ang2pix, NESTED, nside=2, equatorial (ICRS) coords."""
    nside = 2
    ra_deg = np.asarray(ra_deg, float)
    dec_deg = np.asarray(dec_deg, float)
    z = np.sin(np.radians(dec_deg))            # cos(colatitude) = sin(dec)
    phi = np.radians(ra_deg % 360.0)
    za = np.abs(z)
    tt = (phi / (np.pi / 2.0)) % 4.0
    # equatorial belt (|z| <= 2/3)
    temp1 = nside * (0.5 + tt)
    temp2 = nside * (z * 0.75)
    jp = np.floor(temp1 - temp2).astype(np.int64)
    jm = np.floor(temp1 + temp2).astype(np.int64)
    ifp, ifm = jp // nside, jm // nside
    face_eq = np.where(ifp == ifm, (ifp % 4) + 4,
                       np.where(ifp < ifm, ifp % 4, (ifm % 4) + 8)).astype(np.int64)
    ix_eq = (jm % nside).astype(np.int64)
    iy_eq = (nside - (jp % nside) - 1).astype(np.int64)
    # polar caps (|z| > 2/3)
    ntt = np.minimum(np.floor(tt).astype(np.int64), 3)
    tp = tt - ntt
    tmp = nside * np.sqrt(np.maximum(3.0 * (1.0 - za), 0.0))
    jpp = np.minimum(np.floor(tp * tmp).astype(np.int64), nside - 1)
    jmp = np.minimum(np.floor((1.0 - tp) * tmp).astype(np.int64), nside - 1)
    north = z >= 0
    face_pol = np.where(north, ntt, ntt + 8).astype(np.int64)
    ix_pol = np.where(north, nside - jmp - 1, jpp).astype(np.int64)
    iy_pol = np.where(north, nside - jpp - 1, jmp).astype(np.int64)
    eq = za <= 2.0 / 3.0
    face = np.where(eq, face_eq, face_pol)
    ix = np.where(eq, ix_eq, ix_pol)
    iy = np.where(eq, iy_eq, iy_pol)
    return (face * nside * nside + ix + 2 * iy).astype(np.int64)  # nside=2: ix+2*iy


def _offset(ra0, dec0, d_deg, pa_deg):
    """Sky points at angular distance d, position angle pa from (ra0, dec0),
    by rotating the centre's unit vector in the local (north, east) tangent
    basis. Vector rotation stays well-defined at the poles: a spherical
    RA-offset formula degenerates there (cos(dec0) -> 0 collapses the
    position-angle sweep onto a few meridians, so a polar cone samples only
    a cross and under-reports the chunks it truly covers)."""
    ra0r, dec0r = np.radians(ra0), np.radians(dec0)
    d, pa = np.radians(d_deg), np.radians(pa_deg)
    n = np.array([np.cos(dec0r) * np.cos(ra0r),
                  np.cos(dec0r) * np.sin(ra0r),
                  np.sin(dec0r)])                          # cone axis
    east = np.array([-np.sin(ra0r), np.cos(ra0r), 0.0])
    north = np.array([-np.sin(dec0r) * np.cos(ra0r),
                      -np.sin(dec0r) * np.sin(ra0r),
                      np.cos(dec0r)])                      # tangent basis
    t = np.cos(pa) * north[:, None] + np.sin(pa) * east[:, None]  # PA: N->E
    v = np.cos(d) * n[:, None] + np.sin(d) * t                   # (3, N) dirs
    dec = np.degrees(np.arcsin(np.clip(v[2], -1.0, 1.0)))
    ra = np.degrees(np.arctan2(v[1], v[0])) % 360.0
    return ra, dec


def cone_chunks(ra0, dec0, radius_deg, n_r=80, n_pa=720):
    """nside=2 nested pixels a cone of the given radius covers. Densely
    samples the disk + boundary (the pixels are ~29 deg, the sampling
    resolves any that a small cone clips)."""
    rs = np.linspace(0.0, radius_deg, n_r)
    pas = np.linspace(0.0, 360.0, n_pa, endpoint=False)
    RR, PP = np.meshgrid(rs, pas)
    ra, dec = _offset(ra0, dec0, RR.ravel(), PP.ravel())
    return sorted(set(ang2pix_nest_nside2(ra, dec).tolist()))


def _angsep(ra1, dec1, ra2, dec2):
    """Angular separation (deg), haversine."""
    r1, d1, r2, d2 = map(np.radians, (ra1, dec1, ra2, dec2))
    h = (np.sin((d2 - d1) / 2) ** 2 +
         np.cos(d1) * np.cos(d2) * np.sin((r2 - r1) / 2) ** 2)
    return np.degrees(2 * np.arcsin(np.sqrt(np.clip(h, 0, 1))))


def field_from_header(path):
    """(ra, dec, radius_deg) = the WCS evaluated at the IMAGE-CENTRE pixel +
    the centre-to-corner maximum + 0.5 deg margin (astropy WCS — the same
    evaluate-at-centre-pixel form as derive_compose_ref/verify_site). CRVAL
    alone is the reference pixel (astrometry.net places CRPIX off-centre —
    often a corner), so the centre must be projected, not read. The presence
    check stays EXPLICIT: astropy builds an identity WCS from a bare header,
    which would return a silently wrong field where this exits loudly. Needs
    the CD-matrix WCS (the solve_field-injected `_wcs.fit`); siril's SPCC
    re-save drops CD1_1, so point this at the `_wcs.fit`, not `_spcc.fit`."""
    import warnings
    from astropy.io import fits
    from astropy.wcs import WCS
    hdr = fits.getheader(path)
    need = ("CRPIX1", "CRPIX2", "CRVAL1", "CRVAL2",
            "CD1_1", "CD1_2", "CD2_1", "CD2_2", "NAXIS1", "NAXIS2")
    missing = [k for k in need if k not in hdr]
    if missing:
        sys.exit(f"spcc_cone: {path} lacks a CD-matrix WCS ({missing}). Point "
                 "at the solve_field `_wcs.fit`, or pass --ra/--dec/--radius-deg.")
    nx, ny = int(hdr["NAXIS1"]), int(hdr["NAXIS2"])
    # The _wcs headers carry BOTH matrix forms: siril's PC+CDELT (the stack's
    # own canvas WCS) beside the solve-injected CD — non-standard (FITS-WCS
    # says mutually exclusive) — and astropy resolves the conflict toward
    # PC+CDELT: MEASURED 0.25 deg centre skew on the corpus against both the
    # CD evaluation and the header's own OBJCTRA/OBJCTDEC. This function's
    # contract is the SOLVE, so the leftover form is stripped in memory and
    # the WCS is built from the CD alone.
    for k in list(hdr):
        if k.startswith(("PC", "CDELT", "CROTA")):
            del hdr[k]
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        w = WCS(hdr, naxis=2)
        ra, dec = (float(v) for v in
                   w.pixel_to_world_values((nx - 1) / 2.0, (ny - 1) / 2.0))
        cras, cdecs = w.pixel_to_world_values(
            np.array([-0.5, nx - 0.5, -0.5, nx - 0.5]),
            np.array([-0.5, -0.5, ny - 0.5, ny - 0.5]))
    radius = float(_angsep(ra, dec, cras, cdecs).max()) + 0.5
    return ra % 360.0, dec, radius


def zenodo_files():
    """{chunk_int: (url, md5)} from the Zenodo record (curl + json)."""
    import json
    r = subprocess.run(["curl", "-sL", "--max-time", "60",
                        f"https://zenodo.org/api/records/{ZENODO_RECORD}"],
                       capture_output=True, text=True)
    out = {}
    for f in json.loads(r.stdout).get("files", []):
        m = re.match(r"siril_cat1_healpix8_xpsamp_(\d+)\.dat\.bz2$", f["key"])
        if m:
            out[int(m.group(1))] = (f["links"]["self"],
                                    f["checksum"].split(":", 1)[-1])
    return out


def fetch(missing):
    os.makedirs(SPCC_DIR, exist_ok=True)
    files = zenodo_files()
    for n in missing:
        if n not in files:
            print(f"  chunk {n}: NOT in Zenodo record {ZENODO_RECORD} — skip")
            continue
        url, md5 = files[n]
        dat = os.path.join(SPCC_DIR, CHUNK.format(n))
        bz = dat + ".bz2"
        print(f"  chunk {n}: downloading …", flush=True)
        r = subprocess.run(["curl", "-sL", "--fail", "--retry", "3",
                            "--max-time", "1800", url, "-o", bz])
        if r.returncode != 0:
            print(f"  chunk {n}: DOWNLOAD FAILED"); continue
        got = subprocess.run(["md5sum", bz], capture_output=True, text=True
                             ).stdout.split()[0]
        if got != md5:
            print(f"  chunk {n}: MD5 MISMATCH got={got} want={md5}")
            os.remove(bz); continue
        subprocess.run(["bunzip2", "-f", bz])
        print(f"  chunk {n}: OK")


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    opts = dict(a[2:].split("=", 1) for a in sys.argv[1:]
                if a.startswith("--") and "=" in a)
    do_fetch = "--fetch" in sys.argv[1:]
    if "ra" in opts and "dec" in opts:
        ra, dec = float(opts["ra"]), float(opts["dec"])
        radius = float(opts.get("radius-deg", 8.0))
    elif args:
        ra, dec, radius = field_from_header(args[0])
        if "radius-deg" in opts:
            radius = float(opts["radius-deg"])
    else:
        sys.exit(__doc__)

    need = cone_chunks(ra, dec, radius)
    have = set()
    if os.path.isdir(SPCC_DIR):
        for f in os.listdir(SPCC_DIR):
            m = re.match(r"siril_cat1_healpix8_xpsamp_(\d+)\.dat$", f)
            if m:
                have.add(int(m.group(1)))
    missing = sorted(set(need) - have)
    print(f"[spcc_cone] field RA {ra:.3f} Dec {dec:+.3f} radius {radius:.1f} deg")
    print(f"[spcc_cone] cone needs {len(need)} chunks: {need}")
    print(f"[spcc_cone] on disk: {sorted(have & set(need))}")
    print(f"[spcc_cone] MISSING: {missing or 'none — SPCC has full coverage'}")
    if missing and do_fetch:
        print(f"[spcc_cone] fetching {len(missing)} from Zenodo {ZENODO_RECORD} …")
        fetch(missing)
        print("[spcc_cone] done — re-run without --fetch to confirm coverage")
    elif missing:
        print("[spcc_cone] re-run with --fetch to download them")


if __name__ == "__main__":
    main()
