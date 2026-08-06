#!/usr/bin/env python3
"""Per-exposure derotation for the jwst-jupiter close-up — the original
team's documented mechanism (Hueso Methods: every exposure navigated and
derotated individually before combining), expressed with planetmapper.

For EACH _cal exposure of the three channels, at its own MID-exposure epoch
(MJD-AVG — start-time epochs measured as a +19 px residual in the i2d-level
pass): planetmapper places the disc from the frame's own (SIP) WCS; every
ON-DISC pixel of the common target grid (the o006 F150W2 grid at its
mid-epoch) maps target lon/lat -> source x,y -> bilinear sample
(scipy map_coordinates — declared resampling, the sanctioned reproject
class; planetmapper owns all geometry). Off-disc content takes the mt-frame
sky reproject of the same frame; layers blend on a feathered disc mask.
A far-side guard drops surface points invisible at the frame's epoch.

Outputs per frame: work/j3derot/<base>_dr.fits (target grid, MJy/sr) and a
matching <base>_cov.fits coverage mask, so the per-channel combine stays
tool-owned (Siril: stack sum of frames / stack sum of coverages, pm divide).
Record: datasets/<session>/qa_work/j3_derot_exposures.json.
"""
import glob
import json
import os

import numpy as np
import planetmapper
from astropy.io import fits
from astropy.time import Time
from astropy.wcs import WCS
from reproject import reproject_interp
from scipy.ndimage import gaussian_filter, map_coordinates

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PROD = os.path.join(REPO, "sessions", "jwst-jupiter", "products")
WORK = os.path.join(REPO, "sessions", "jwst-jupiter", "work")
OUT = os.path.join(WORK, "j3derot")
DS = os.path.join(REPO, "datasets", "jwst-jupiter", "qa_work")
os.makedirs(OUT, exist_ok=True)

TARGET = os.path.join(PROD, "jw01373-o006_t006_nircam_f150w2-f164n-sub640_i2d.fits")

CHANNELS = {
    "f150w2": sorted(glob.glob(PROD + "/jw01373006001_03102_0000?_nrcb[1-4]_cal.fits")),
    "f360m":  sorted(glob.glob(PROD + "/jw01373006001_03102_0000?_nrcblong_cal.fits")),
    "f212n":  sorted(glob.glob(PROD + "/jw01373008001_03101_0000?_nrcb3_cal.fits")),
}


def mid_utc(path):
    h0 = fits.open(path)[0].header
    for k in ("MJD-AVG",):
        if h0.get(k):
            return Time(h0[k], format="mjd").isot
    sci = fits.open(path)["SCI"].header
    if sci.get("MJD-AVG"):
        return Time(sci["MJD-AVG"], format="mjd").isot
    return h0["DATE-OBS"] + "T" + h0["TIME-OBS"][:12]


# --- target geometry, computed once ---
with fits.open(TARGET) as h:
    tgt_hdr = h["SCI"].header
    tgt_shape = (tgt_hdr["NAXIS2"], tgt_hdr["NAXIS1"])
tgt_utc = mid_utc(TARGET)
tmp = os.path.join(WORK, "_pm_target.fits")
fits.PrimaryHDU(data=np.zeros(tgt_shape, dtype=np.float32), header=tgt_hdr).writeto(tmp, overwrite=True)
tgt_obs = planetmapper.Observation(tmp, target="JUPITER", utc=tgt_utc, observer="JWST")
tgt_obs.disc_from_wcs(suppress_warnings=True)
lon_bp = tgt_obs.get_backplane_img("LON-GRAPHIC")
lat_bp = tgt_obs.get_backplane_img("LAT-GRAPHIC")
ondisc = np.isfinite(lon_bp) & np.isfinite(lat_bp)
iy, ix = np.where(ondisc)
lons, lats = lon_bp[ondisc], lat_bp[ondisc]
tgt_wcs = WCS(tgt_hdr)
print(f"target: {tgt_utc} sub-obs lon {tgt_obs.subpoint_lon:.2f}; on-disc {ondisc.sum()} px", flush=True)

rec = {"target_epoch": tgt_utc, "target_grid": "o006 F150W2 (0.0309\"/px)",
       "epoch_rule": "each frame at its own MJD-AVG mid-exposure", "frames": {}}

for chan, files in CHANNELS.items():
    print(f"=== {chan}: {len(files)} frames ===", flush=True)
    for f in files:
        base = os.path.basename(f).replace("_cal.fits", "")
        of = os.path.join(OUT, base + "_dr.fits")
        if os.path.exists(of):
            print(f"skip {base}", flush=True)
            continue
        with fits.open(f) as h:
            sdata = h["SCI"].data.astype(np.float32)
            shdr = h["SCI"].header
        utc = mid_utc(f)
        stmp = os.path.join(WORK, "_pm_src.fits")
        fits.PrimaryHDU(data=sdata, header=shdr).writeto(stmp, overwrite=True)
        sobs = planetmapper.Observation(stmp, target="JUPITER", utc=utc, observer="JWST")
        sobs.disc_from_wcs(suppress_warnings=True)

        sx, sy = sobs.lonlat2xy(lons, lats)
        sx = np.asarray(sx, float); sy = np.asarray(sy, float)
        cl, cb = sobs.xy2lonlat(sx, sy)
        dl = np.abs(((np.asarray(cl) - lons + 180) % 360) - 180)
        db = np.abs(np.asarray(cb) - lats)
        H, W = sdata.shape
        inframe = (sx > 1) & (sx < W - 2) & (sy > 1) & (sy < H - 2)
        ok = np.isfinite(dl) & (dl < 1.0) & (db < 1.0) & inframe

        clean = np.nan_to_num(sdata, nan=0.0)
        good = np.isfinite(sdata).astype(np.float32)
        samp = map_coordinates(clean, [sy[ok], sx[ok]], order=1, mode="constant", cval=0.0)
        wsamp = map_coordinates(good, [sy[ok], sx[ok]], order=1, mode="constant", cval=0.0)

        disc_img = np.zeros(tgt_shape, np.float32)
        disc_cov = np.zeros(tgt_shape, np.float32)
        disc_img[iy[ok], ix[ok]] = samp
        disc_cov[iy[ok], ix[ok]] = (wsamp > 0.99).astype(np.float32)

        sky, foot = reproject_interp((np.where(np.isfinite(sdata), sdata, np.nan), WCS(shdr)),
                                     tgt_wcs, shape_out=tgt_shape)
        skyv = np.nan_to_num(sky, nan=0.0).astype(np.float32)
        skyc = (np.isfinite(sky)).astype(np.float32)

        a = gaussian_filter(disc_cov, 3.0)
        a = np.clip((a - 0.25) / 0.5, 0, 1)
        img = a * disc_img + (1 - a) * skyv
        cov = np.maximum(a * disc_cov, (1 - a) * skyc)

        fits.PrimaryHDU(data=img * cov, header=tgt_hdr).writeto(of, overwrite=True)
        fits.PrimaryHDU(data=cov, header=tgt_hdr).writeto(
            os.path.join(OUT, base + "_cov.fits"), overwrite=True)
        rec["frames"][base] = {"channel": chan, "utc": utc,
                               "sub_obs_lon": round(float(sobs.subpoint_lon), 3),
                               "disc_px_mapped": int(ok.sum()),
                               "cov_fraction": round(float(cov.mean()), 4)}
        print(f"{base}: {utc} mapped {ok.sum()} disc px, cov {cov.mean():.3f}", flush=True)

json.dump(rec, open(os.path.join(DS, "j3_derot_exposures.json"), "w"), indent=1)
print("-> j3_derot_exposures.json")
