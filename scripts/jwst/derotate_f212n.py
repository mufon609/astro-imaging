#!/usr/bin/env python3
"""Derotate the F212N channel to the o006 epoch for the jwst-jupiter close-up.

The three close-up channels span two epochs: o006 (F360M + F150W2xF164N,
simultaneous) and o008 F212N, 27.5 min later = 16.6 deg of Jovian rotation
(~200 px of feature motion at the composite scale). The ratified route maps
every ON-DISC pixel of the target grid through planet-surface coordinates:

  target pixel -> lon/lat  (planetmapper backplanes, o006 epoch + F150W2 WCS)
              -> source x,y (planetmapper lonlat2xy, o008 epoch + F212N WCS)
              -> bilinear sample of the F212N SCI (scipy map_coordinates —
                 the same declared-resampling class as the sanctioned
                 astropy reproject usage; planetmapper does ALL geometry)

OFF-DISC (sky, above-limb aurora/glow) cannot map through surface lon/lat:
it takes the plain moving-target sky reproject (reproject_interp), which is
honest there — the mt-frame WCS registers the planet center across epochs,
and above-limb emission sits at the poles where 16.6 deg of rotation moves
features least. A far-side guard drops target pixels whose surface point was
behind the limb at the F212N epoch (they fall back to the sky layer); the
two layers blend on a feathered disc mask.

Verdict instrument (recorded): the GRS-region phase-correlation offset
between F150W2 and F212N, raw-reproject vs derotated — the rotation shift
must collapse toward 0.

Writes work/j3_f212n_derot.fits (F150W2 grid, MJy/sr) + the record
datasets/<session>/qa_work/j3_derotation.json.
"""
import json
import os

import numpy as np
import planetmapper
from astropy.io import fits
from astropy.wcs import WCS
from reproject import reproject_interp
from scipy.ndimage import gaussian_filter, map_coordinates

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PROD = os.path.join(REPO, "sessions", "jwst-jupiter", "products")
WORK = os.path.join(REPO, "sessions", "jwst-jupiter", "work")
DS = os.path.join(REPO, "datasets", "jwst-jupiter", "qa_work")

TARGET = os.path.join(PROD, "jw01373-o006_t006_nircam_f150w2-f164n-sub640_i2d.fits")
SOURCE = os.path.join(PROD, "jw01373-o008_t006_nircam_clear-f212n_i2d.fits")


def obs_utc(path):
    h0 = fits.open(path)[0].header
    return h0["DATE-OBS"] + "T" + h0["TIME-OBS"][:12]


def make_obs(path):
    with fits.open(path) as h:
        sci = h["SCI"]
        data = sci.data.astype(np.float32)
        hdr = sci.header
    tmp = os.path.join(WORK, "_pm_" + os.path.basename(path))
    fits.PrimaryHDU(data=data, header=hdr).writeto(tmp, overwrite=True)
    o = planetmapper.Observation(tmp, target="JUPITER", utc=obs_utc(path), observer="JWST")
    o.disc_from_wcs(suppress_warnings=True)
    return o, data, hdr


print("building observations ...", flush=True)
tgt, tgt_data, tgt_hdr = make_obs(TARGET)
src, src_data, src_hdr = make_obs(SOURCE)
d_lon = (src.subpoint_lon - tgt.subpoint_lon) % 360
print(f"target epoch {tgt.utc} sub-obs lon {tgt.subpoint_lon:.2f}")
print(f"source epoch {src.utc} sub-obs lon {src.subpoint_lon:.2f}  (rotation {d_lon:.2f} deg)")

print("target lon/lat backplanes ...", flush=True)
lon_bp = tgt.get_backplane_img("LON-GRAPHIC")
lat_bp = tgt.get_backplane_img("LAT-GRAPHIC")
ondisc = np.isfinite(lon_bp) & np.isfinite(lat_bp)
print(f"on-disc: {ondisc.sum()} px ({100*ondisc.mean():.1f}%)")

print("mapping through the source epoch (vectorized lonlat2xy) ...", flush=True)
lons = lon_bp[ondisc]
lats = lat_bp[ondisc]
sx, sy = src.lonlat2xy(lons, lats)
sx = np.asarray(sx, dtype=np.float64)
sy = np.asarray(sy, dtype=np.float64)
if sx.shape != lons.shape:
    raise SystemExit(f"lonlat2xy not vectorized as expected: {sx.shape} vs {lons.shape}")

# far-side guard: the surface point must have been VISIBLE at the source
# epoch — verify by asking the source geometry for the lon/lat at the mapped
# pixel and requiring agreement (far-side points disagree or go NaN)
chk_lon, chk_lat = src.xy2lonlat(sx, sy)
dl = np.abs(((np.asarray(chk_lon) - lons + 180) % 360) - 180)
db = np.abs(np.asarray(chk_lat) - lats)
visible = np.isfinite(dl) & (dl < 1.0) & (db < 1.0)
print(f"visible at source epoch: {visible.sum()}/{len(lons)} ({100*visible.mean():.1f}%)")

src_clean = np.nan_to_num(src_data, nan=0.0)
samp = map_coordinates(src_clean, [sy[visible], sx[visible]], order=1, mode="constant", cval=0.0)

derot_disc = np.zeros_like(tgt_data, dtype=np.float32)
alpha = np.zeros(tgt_data.shape, dtype=np.float32)
iy, ix = np.where(ondisc)
derot_disc[iy[visible], ix[visible]] = samp
alpha[iy[visible], ix[visible]] = 1.0

print("off-disc sky layer (mt-frame reproject) ...", flush=True)
sky, _ = reproject_interp((np.nan_to_num(src_data, nan=np.nan), WCS(src_hdr)),
                          WCS(tgt_hdr), shape_out=tgt_data.shape)
sky = np.nan_to_num(sky, nan=0.0).astype(np.float32)

alpha = gaussian_filter(alpha, 4.0)
alpha = np.clip((alpha - 0.2) / 0.6, 0, 1)   # feathered blend band
out = alpha * derot_disc + (1 - alpha) * sky

# verdict instrument: GRS-region phase shift, raw sky-reproject vs derotated,
# each against the target-epoch F150W2 morphology
def phase_shift(a, b):
    a = np.nan_to_num(a, nan=0.0); b = np.nan_to_num(b, nan=0.0)
    a = a - a.mean(); b = b - b.mean()
    f = np.fft.rfft2(a) * np.conj(np.fft.rfft2(b))
    c = np.fft.irfft2(f / (np.abs(f) + 1e-12), s=a.shape)
    p = np.unravel_index(np.argmax(c), c.shape)
    return [int((v + n // 2) % n - n // 2) for v, n in zip(p, a.shape)]

win = (slice(560, 880), slice(950, 1270))     # GRS quadrant on the o006 grid
ref = np.log1p(np.clip(np.nan_to_num(tgt_data, nan=0.0)[win], 0, None))
sh_raw = phase_shift(ref, np.log1p(np.clip(sky[win], 0, None)))
sh_der = phase_shift(ref, np.log1p(np.clip(out[win], 0, None)))
print(f"GRS-window shift vs F150W2: raw reproject {sh_raw} px -> derotated {sh_der} px")

fits.PrimaryHDU(data=out, header=tgt_hdr).writeto(os.path.join(WORK, "j3_f212n_derot.fits"),
                                                  overwrite=True)
rec = {
    "route": "planetmapper surface derotation (user-ratified): target lon/lat backplanes (o006) -> lonlat2xy (o008) -> bilinear sample; off-disc = mt-frame sky reproject; feathered blend",
    "epochs": {"target_o006": tgt.utc, "source_o008_f212n": src.utc},
    "rotation_deg": round(float(d_lon), 3),
    "on_disc_px": int(ondisc.sum()),
    "visible_fraction": round(float(visible.mean()), 4),
    "grs_window_shift_px": {"raw_reproject": sh_raw, "derotated": sh_der},
    "output": "work/j3_f212n_derot.fits (F150W2 grid, MJy/sr)",
}
os.makedirs(DS, exist_ok=True)
json.dump(rec, open(os.path.join(DS, "j3_derotation.json"), "w"), indent=1)
print("-> j3_derotation.json")
