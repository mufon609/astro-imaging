#!/usr/bin/env python3
"""Round-3 per-exposure derotation — the four documented steps the step-map
found missing or partial (Hueso Methods, clause by clause):

1. LIMB-DARKENING CORRECTION ("limb-darkened corrected"): each frame is
   divided by its OWN epoch's illumination model before derotation
   (Minnaert, first arm k=1 => divide by mu0 = cos(incidence), from
   planetmapper's INCIDENCE backplane on the source grid), so the combine
   happens in illumination-flat space. The common TARGET-epoch illumination
   map is exported (illum_target.fits: mu0 on-disc, 1 off-disc) and the
   render multiplies it back — one illumination for all channels, which is
   the wedge/band mechanism's fix. Terminator guard: mu0 < 0.10 leaves
   coverage (no division blowup).
2. DQ-STRICT ingestion ("adaptive median filter to remove bad pixels", the
   coverage way): DO_NOT_USE-flagged pixels are excluded via the coverage
   weight — no invented values, the combine's other frames fill them.
3. 2x OVERSAMPLED working grid ("map-projected, oversampling the initial
   resolution"): the target WCS is scaled 2x (CD/2, CRPIX'=2*CRPIX-0.5).
   COST CONTROL: the SPICE mapping (lonlat2xy) runs at 1x and the smooth
   (sx,sy) coordinate fields upsample bilinearly to 2x — sub-0.01 px field
   error, ~unchanged wall-clock; cubic image sampling runs at 2x density.
4. (High-pass enhancement is a RENDER-side stage — the render driver's arm.)

Navigation refinement from round 2 is dropped: measured null (+/-0.01 px).
Outputs work/j3derot3/ + illum_target.fits + record qa_work/j3_derot_illum.json.
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
from scipy.ndimage import gaussian_filter, map_coordinates, zoom

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PROD = os.path.join(REPO, "sessions", "jwst-jupiter", "products")
WORK = os.path.join(REPO, "sessions", "jwst-jupiter", "work")
OUT = os.path.join(WORK, "j3derot3")
DS = os.path.join(REPO, "datasets", "jwst-jupiter", "qa_work")
os.makedirs(OUT, exist_ok=True)

TARGET = os.path.join(PROD, "jw01373-o006_t006_nircam_f150w2-f164n-sub640_i2d.fits")
CHANNELS = {
    "f150w2": "jw01373006001_03102_0000?_nrcb[1-4]",
    "f360m": "jw01373006001_03102_0000?_nrcblong",
    "f212n": "jw01373008001_03101_0000?_nrcb3",
}
K_MINNAERT = 1.0
MU0_MIN = 0.10
OVER = 2


def mid_utc(path):
    h0 = fits.open(path)[0].header
    if h0.get("MJD-AVG"):
        return Time(h0["MJD-AVG"], format="mjd").isot
    sci = fits.open(path)["SCI"].header
    if sci.get("MJD-AVG"):
        return Time(sci["MJD-AVG"], format="mjd").isot
    return h0["DATE-OBS"] + "T" + h0["TIME-OBS"][:12]


def illum(obs, shape):
    """mu0 map (cos incidence) on the observation's grid; NaN off-disc"""
    inc = obs.get_backplane_img("INCIDENCE")
    return np.cos(np.radians(inc))


# --- 1x target geometry ---
with fits.open(TARGET) as h:
    hdr1 = h["SCI"].header.copy()
shape1 = (hdr1["NAXIS2"], hdr1["NAXIS1"])
tgt_utc = mid_utc(TARGET)
tmp = os.path.join(WORK, "_pm_target.fits")
fits.PrimaryHDU(data=np.zeros(shape1, np.float32), header=hdr1).writeto(tmp, overwrite=True)
tobs = planetmapper.Observation(tmp, target="JUPITER", utc=tgt_utc, observer="JWST")
tobs.disc_from_wcs(suppress_warnings=True)
lon1 = tobs.get_backplane_img("LON-GRAPHIC")
lat1 = tobs.get_backplane_img("LAT-GRAPHIC")
mu0_t1 = illum(tobs, shape1)

# --- 2x target header (CD/2, CRPIX' = 2*CRPIX - 0.5) ---
hdr2 = hdr1.copy()
for k in ("CD1_1", "CD1_2", "CD2_1", "CD2_2"):
    if k in hdr2:
        hdr2[k] /= OVER
for k in ("CDELT1", "CDELT2"):
    if k in hdr2:
        hdr2[k] /= OVER
hdr2["CRPIX1"] = OVER * hdr1["CRPIX1"] - 0.5
hdr2["CRPIX2"] = OVER * hdr1["CRPIX2"] - 0.5
hdr2["NAXIS1"] = shape1[1] * OVER
hdr2["NAXIS2"] = shape1[0] * OVER
shape2 = (shape1[0] * OVER, shape1[1] * OVER)
tgt_wcs2 = WCS(hdr2)

# target illumination at 2x: mu0 on-disc (>=MU0_MIN), 1 off-disc
mu0_t2 = zoom(np.nan_to_num(mu0_t1, nan=0.0), OVER, order=1)[:shape2[0], :shape2[1]]
disc_t2 = zoom(np.isfinite(mu0_t1).astype(np.float32), OVER, order=1)[:shape2[0], :shape2[1]] > 0.5
illum_t = np.where(disc_t2, np.clip(mu0_t2, MU0_MIN, 1.0) ** K_MINNAERT, 1.0).astype(np.float32)
fits.PrimaryHDU(data=illum_t, header=hdr2).writeto(os.path.join(WORK, "illum_target.fits"),
                                                   overwrite=True)
print(f"target {tgt_utc}; 1x disc px {np.isfinite(lon1).sum()}; 2x grid {shape2}", flush=True)

rec = {"round": 3, "k_minnaert": K_MINNAERT, "mu0_min": MU0_MIN, "oversample": OVER,
       "dq_strict": True, "nav_refinement": "dropped (round-2 null)", "frames": {}}

ondisc1 = np.isfinite(lon1) & np.isfinite(lat1)
lons1, lats1 = lon1[ondisc1], lat1[ondisc1]

for chan, pat in CHANNELS.items():
    files = sorted(glob.glob(os.path.join(PROD, pat + "_cal.fits")))
    print(f"=== {chan}: {len(files)} frames ===", flush=True)
    for f in files:
        base = os.path.basename(f).replace("_cal.fits", "")
        of = os.path.join(OUT, base + "_dr.fits")
        if os.path.exists(of):
            print(f"skip {base}", flush=True)
            continue
        with fits.open(f) as h:
            sdata = h["SCI"].data.astype(np.float32)
            sdq = h["DQ"].data
            shdr = h["SCI"].header
        utc = mid_utc(f)
        stmp = os.path.join(WORK, "_pm_src.fits")
        fits.PrimaryHDU(data=sdata, header=shdr).writeto(stmp, overwrite=True)
        sobs = planetmapper.Observation(stmp, target="JUPITER", utc=utc, observer="JWST")
        sobs.disc_from_wcs(suppress_warnings=True)

        # illumination-flat source frame (k=1: divide by mu0), terminator-guarded
        mu0_s = illum(sobs, sdata.shape)
        good = np.isfinite(sdata) & ((sdq & 1) == 0)
        flat = np.where(np.isfinite(mu0_s) & (mu0_s >= MU0_MIN),
                        sdata / np.clip(mu0_s, MU0_MIN, None) ** K_MINNAERT, sdata)
        offdisc_src = ~np.isfinite(mu0_s)
        usable = good & (offdisc_src | (mu0_s >= MU0_MIN))

        # 1x mapping through SPICE, upsampled coordinate fields to 2x
        sx1 = np.full(shape1, np.nan, np.float64)
        sy1 = np.full(shape1, np.nan, np.float64)
        vx, vy = sobs.lonlat2xy(lons1, lats1)
        sx1[ondisc1] = np.asarray(vx, float)
        sy1[ondisc1] = np.asarray(vy, float)
        cl, cb = sobs.xy2lonlat(sx1[ondisc1], sy1[ondisc1])
        dl = np.abs(((np.asarray(cl) - lons1 + 180) % 360) - 180)
        db = np.abs(np.asarray(cb) - lats1)
        vis1 = np.zeros(shape1, bool)
        vis1[ondisc1] = np.isfinite(dl) & (dl < 1.0) & (db < 1.0)

        sx2 = zoom(np.nan_to_num(sx1, nan=-1e6), OVER, order=1)[:shape2[0], :shape2[1]]
        sy2 = zoom(np.nan_to_num(sy1, nan=-1e6), OVER, order=1)[:shape2[0], :shape2[1]]
        vis2 = zoom(vis1.astype(np.float32), OVER, order=1)[:shape2[0], :shape2[1]] > 0.75
        H, W = sdata.shape
        vis2 &= (sx2 > 2) & (sx2 < W - 3) & (sy2 > 2) & (sy2 < H - 3)

        cy, cx = np.where(vis2)
        samp = map_coordinates(np.where(usable, flat, 0.0), [sy2[vis2], sx2[vis2]],
                               order=3, mode="constant", cval=0.0)
        wsamp = map_coordinates(usable.astype(np.float32), [sy2[vis2], sx2[vis2]],
                                order=1, mode="constant", cval=0.0)
        disc_img = np.zeros(shape2, np.float32)
        disc_cov = np.zeros(shape2, np.float32)
        disc_img[cy, cx] = samp
        disc_cov[cy, cx] = (wsamp > 0.99).astype(np.float32)

        # off-disc: mt-frame sky reproject at 2x (illumination untouched)
        sky, _ = reproject_interp((np.where(usable, sdata, np.nan), WCS(shdr)),
                                  tgt_wcs2, shape_out=shape2)
        skyv = np.nan_to_num(sky, nan=0.0).astype(np.float32)
        skyc = np.isfinite(sky).astype(np.float32) * (~disc_t2).astype(np.float32)

        a = gaussian_filter(disc_cov, 5.0)
        a = np.clip((a - 0.25) / 0.5, 0, 1)
        img = a * disc_img + (1 - a) * skyv
        cov = np.maximum(a * disc_cov, (1 - a) * skyc)
        fits.PrimaryHDU(data=img * cov, header=hdr2).writeto(of, overwrite=True)
        fits.PrimaryHDU(data=cov, header=hdr2).writeto(os.path.join(OUT, base + "_cov.fits"),
                                                       overwrite=True)
        rec["frames"][base] = {"channel": chan, "utc": utc,
                               "disc_px_2x": int(vis2.sum()),
                               "dq_excluded_px": int((~good & np.isfinite(sdata)).sum())}
        print(f"{base}: {utc} disc2x {vis2.sum()} dq_excl {(~good & np.isfinite(sdata)).sum()}",
              flush=True)

json.dump(rec, open(os.path.join(DS, "j3_derot_illum.json"), "w"), indent=1)
print("-> j3_derot_illum.json")
