#!/usr/bin/env python3
"""Round-2 per-exposure derotation with NAVIGATION REFINEMENT — the Hueso
per-frame navigation step, mechanized.

Round 1 measured a 31% sharpness loss at the combine caused by per-frame
position scatter (SIP unmodeled by planetmapper, +/-0.2-0.7 px). Round 2:
1. Each frame derotates exactly as round 1 (same geometry, same epochs).
2. Its residual offset is MEASURED by phase correlation (parabolic sub-pixel
   peak) against the ROUND-1 channel master over the frame's own coverage —
   a blurred reference does not bias a correlation peak.
3. The offset feeds back as a SOURCE-SPACE sampling correction through the
   local Jacobian of the target->source mapping at disc center (no extra
   resampling hop; the geometry stays planetmapper's). Frame 1 runs a sign
   self-check: after correction the re-measured offset must shrink, else the
   Jacobian sign flips (recorded).
4. Image sampling is cubic (order=3) this round; coverage stays order=1.

Outputs to work/j3derot2/ + record datasets/.../qa_work/j3_derot_refined.json.
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
OUT = os.path.join(WORK, "j3derot2")
DS = os.path.join(REPO, "datasets", "jwst-jupiter", "qa_work")
os.makedirs(OUT, exist_ok=True)

TARGET = os.path.join(PROD, "jw01373-o006_t006_nircam_f150w2-f164n-sub640_i2d.fits")
CHANNELS = {
    "f150w2": "jw01373006001_03102_0000?_nrcb[1-4]",
    "f360m": "jw01373006001_03102_0000?_nrcblong",
    "f212n": "jw01373008001_03101_0000?_nrcb3",
}


def mid_utc(path):
    h0 = fits.open(path)[0].header
    if h0.get("MJD-AVG"):
        return Time(h0["MJD-AVG"], format="mjd").isot
    sci = fits.open(path)["SCI"].header
    if sci.get("MJD-AVG"):
        return Time(sci["MJD-AVG"], format="mjd").isot
    return h0["DATE-OBS"] + "T" + h0["TIME-OBS"][:12]


def phase_offset(ref, img, mask):
    """sub-pixel (dy,dx) of img vs ref over mask (parabolic peak refine)"""
    a = np.where(mask, ref, 0.0); b = np.where(mask, img, 0.0)
    a = a - a.mean(); b = b - b.mean()
    f = np.fft.rfft2(a) * np.conj(np.fft.rfft2(b))
    c = np.fft.irfft2(f / (np.abs(f) + 1e-12), s=a.shape)
    p = np.unravel_index(np.argmax(c), c.shape)
    off = []
    for axis, n in enumerate(a.shape):
        i = p[axis]
        im, ip = (i - 1) % n, (i + 1) % n
        cm = c[(im, p[1]) if axis == 0 else (p[0], im)]
        cp = c[(ip, p[1]) if axis == 0 else (p[0], ip)]
        c0 = c[p]
        denom = (cm - 2 * c0 + cp)
        frac = 0.5 * (cm - cp) / denom if abs(denom) > 1e-12 else 0.0
        v = i + frac
        off.append((v + n // 2) % n - n // 2)
    return off  # [dy, dx]: img content sits at +off relative to ref


# --- target geometry (identical to round 1) ---
with fits.open(TARGET) as h:
    tgt_hdr = h["SCI"].header
    tgt_shape = (tgt_hdr["NAXIS2"], tgt_hdr["NAXIS1"])
tgt_utc = mid_utc(TARGET)
tmp = os.path.join(WORK, "_pm_target.fits")
fits.PrimaryHDU(data=np.zeros(tgt_shape, np.float32), header=tgt_hdr).writeto(tmp, overwrite=True)
tobs = planetmapper.Observation(tmp, target="JUPITER", utc=tgt_utc, observer="JWST")
tobs.disc_from_wcs(suppress_warnings=True)
lon_bp = tobs.get_backplane_img("LON-GRAPHIC")
lat_bp = tobs.get_backplane_img("LAT-GRAPHIC")
ondisc = np.isfinite(lon_bp) & np.isfinite(lat_bp)
iy, ix = np.where(ondisc)
lons, lats = lon_bp[ondisc], lat_bp[ondisc]
tgt_wcs = WCS(tgt_hdr)
tcx, tcy = tobs.get_disc_params()[:2]
print(f"target {tgt_utc}; on-disc {ondisc.sum()} px", flush=True)

rec = {"round": 2, "nav_reference": "round-1 channel masters", "sampling": "cubic (image), linear (coverage)",
       "frames": {}, "sign_check": None}
sign = None

for chan, pat in CHANNELS.items():
    master = fits.open(os.path.join(WORK, f"m_{chan}.fits"))[0].data
    files = sorted(glob.glob(os.path.join(PROD, pat + "_cal.fits")))
    print(f"=== {chan}: {len(files)} frames ===", flush=True)
    for f in files:
        base = os.path.basename(f).replace("_cal.fits", "")
        r1 = os.path.join(WORK, "j3derot", base + "_dr.fits")
        r1c = os.path.join(WORK, "j3derot", base + "_cov.fits")
        with fits.open(f) as h:
            sdata = h["SCI"].data.astype(np.float32)
            shdr = h["SCI"].header
        utc = mid_utc(f)
        stmp = os.path.join(WORK, "_pm_src.fits")
        fits.PrimaryHDU(data=sdata, header=shdr).writeto(stmp, overwrite=True)
        sobs = planetmapper.Observation(stmp, target="JUPITER", utc=utc, observer="JWST")
        sobs.disc_from_wcs(suppress_warnings=True)

        # nav: offset of the ROUND-1 frame vs the round-1 master, disc overlap only
        img1 = fits.open(r1)[0].data
        cov1 = fits.open(r1c)[0].data
        m = (cov1 > 0.6) & ondisc & (np.nan_to_num(master) > 0)
        if m.sum() < 5000:
            dy = dx = 0.0
        else:
            dy, dx = phase_offset(np.log1p(np.clip(master, 0, None)),
                                  np.log1p(np.clip(img1, 0, None)), m)

        # local Jacobian of target->source at disc center
        p0 = np.array(sobs.lonlat2xy(*tobs.xy2lonlat(tcx, tcy)))
        px = np.array(sobs.lonlat2xy(*tobs.xy2lonlat(tcx + 1, tcy)))
        py = np.array(sobs.lonlat2xy(*tobs.xy2lonlat(tcx, tcy + 1)))
        Jx = px - p0   # d(source xy) per +1 target x
        Jy = py - p0
        if sign is None:
            sign = 1.0
        ex = sign * (Jx[0] * dx + Jy[0] * dy)
        ey = sign * (Jx[1] * dx + Jy[1] * dy)

        sx, sy = sobs.lonlat2xy(lons, lats)
        sx = np.asarray(sx, float) + ex
        sy = np.asarray(sy, float) + ey
        cl, cb = sobs.xy2lonlat(sx - ex, sy - ey)
        dl = np.abs(((np.asarray(cl) - lons + 180) % 360) - 180)
        db = np.abs(np.asarray(cb) - lats)
        H, W = sdata.shape
        okv = np.isfinite(dl) & (dl < 1.0) & (db < 1.0) & \
            (sx > 2) & (sx < W - 3) & (sy > 2) & (sy < H - 3)

        clean = np.nan_to_num(sdata, nan=0.0)
        good = np.isfinite(sdata).astype(np.float32)
        samp = map_coordinates(clean, [sy[okv], sx[okv]], order=3, mode="constant", cval=0.0)
        wsamp = map_coordinates(good, [sy[okv], sx[okv]], order=1, mode="constant", cval=0.0)

        disc_img = np.zeros(tgt_shape, np.float32)
        disc_cov = np.zeros(tgt_shape, np.float32)
        disc_img[iy[okv], ix[okv]] = np.clip(samp, None, None)
        disc_cov[iy[okv], ix[okv]] = (wsamp > 0.99).astype(np.float32)

        # sign self-check on the very first refined frame with a real offset
        if rec["sign_check"] is None and (abs(dx) > 0.15 or abs(dy) > 0.15):
            m2 = (disc_cov > 0.6) & ondisc & (np.nan_to_num(master) > 0)
            dy2, dx2 = phase_offset(np.log1p(np.clip(master, 0, None)),
                                    np.log1p(np.clip(disc_img, 0, None)), m2)
            if np.hypot(dx2, dy2) > np.hypot(dx, dy):
                sign = -1.0
                rec["sign_check"] = {"frame": base, "before": [dy, dx], "after_bad": [dy2, dx2],
                                     "action": "sign flipped to -1, frame redone"}
                ex, ey = sign * (Jx[0] * dx + Jy[0] * dy), sign * (Jx[1] * dx + Jy[1] * dy)
                sx2, sy2 = sobs.lonlat2xy(lons, lats)
                sx2 = np.asarray(sx2, float) + ex; sy2 = np.asarray(sy2, float) + ey
                samp = map_coordinates(clean, [sy2[okv], sx2[okv]], order=3, mode="constant", cval=0.0)
                disc_img[iy[okv], ix[okv]] = samp
            else:
                rec["sign_check"] = {"frame": base, "before": [dy, dx], "after": [dy2, dx2],
                                     "action": "sign +1 confirmed"}
            print(f"  sign check: {rec['sign_check']}", flush=True)

        sky, _ = reproject_interp((np.where(np.isfinite(sdata), sdata, np.nan), WCS(shdr)),
                                  tgt_wcs, shape_out=tgt_shape)
        skyv = np.nan_to_num(sky, nan=0.0).astype(np.float32)
        skyc = np.isfinite(sky).astype(np.float32)
        a = gaussian_filter(disc_cov, 3.0)
        a = np.clip((a - 0.25) / 0.5, 0, 1)
        img = a * disc_img + (1 - a) * skyv
        cov = np.maximum(a * disc_cov, (1 - a) * skyc)
        fits.PrimaryHDU(data=img * cov, header=tgt_hdr).writeto(
            os.path.join(OUT, base + "_dr.fits"), overwrite=True)
        fits.PrimaryHDU(data=cov, header=tgt_hdr).writeto(
            os.path.join(OUT, base + "_cov.fits"), overwrite=True)
        rec["frames"][base] = {"channel": chan, "utc": utc,
                               "nav_offset_target_px": [round(float(dy), 3), round(float(dx), 3)],
                               "src_correction_px": [round(float(ex), 3), round(float(ey), 3)]}
        print(f"{base}: nav (dy,dx)=({dy:+.2f},{dx:+.2f}) -> src corr ({ex:+.2f},{ey:+.2f})", flush=True)

json.dump(rec, open(os.path.join(DS, "j3_derot_refined.json"), "w"), indent=1)
print("-> j3_derot_refined.json")
