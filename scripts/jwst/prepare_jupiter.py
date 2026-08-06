#!/usr/bin/env python3
"""J2 prepare stage for the jwst-jupiter wide-field recreation: put both
filters on ONE grid and hand Siril normalized float frames.

- Reference grid = F212N's SW mosaic (0.0307"/px — the finest; the plan's
  choice). F335M (LW, 0.0630"/px) is reprojected onto it with
  reproject_interp (bilinear — the documented choice for an UP-sampling hop;
  MJy/sr is surface brightness so values carry unscaled).
- NaN policy: reproject in NaN space (holes/gaps stay NaN, never smeared),
  then NaN->0 for the working frames; per-filter NaN counts recorded.
- Normalization: fixed RECORDED divisors chosen from the J1 census p999
  (f212n /50000, f335m /4000) map each filter into Siril's [0,1] working
  range. A divisor is a linear scale — structure and ratios survive; the
  per-filter stretch that follows is the documented independent-stretch
  practice.
Writes sessions/<session>/work/jup_{f212n,f335m}_prep.fits (float32,
uncompressed, F212N WCS carried) + the record
datasets/<session>/qa_work/j2_prepare.json.
"""
import json
import os
import sys

import numpy as np
from astropy.io import fits
from astropy.wcs import WCS
from reproject import reproject_interp

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
session = sys.argv[1] if len(sys.argv) > 1 else "jwst-jupiter"
work = os.path.join(REPO, "sessions", session, "work")
DIVISORS = {"f212n": 50000.0, "f335m": 4000.0}

with fits.open(os.path.join(work, "f212n_sci.fits")) as h:
    ref_data, ref_hdr = h[0].data.astype(np.float32), h[0].header
ref_wcs = WCS(ref_hdr)

with fits.open(os.path.join(work, "f335m_sci.fits")) as h:
    lw_data, lw_hdr = h[0].data.astype(np.float32), h[0].header

print("reprojecting f335m -> f212n grid ...", flush=True)
lw_on_ref, footprint = reproject_interp((lw_data, WCS(lw_hdr)), ref_wcs,
                                        shape_out=ref_data.shape)
lw_on_ref = lw_on_ref.astype(np.float32)

rec = {"session": session, "reference_grid": "f212n (0.0307 arcsec/px)",
       "reproject": "reproject_interp (bilinear; up-sampling hop LW->SW)",
       "divisors": DIVISORS, "frames": {}}
for tag, data in (("f212n", ref_data), ("f335m", lw_on_ref)):
    nan = ~np.isfinite(data)
    out = np.nan_to_num(data, nan=0.0) / DIVISORS[tag]
    rec["frames"][tag] = {
        "shape": list(out.shape), "nan_fraction": round(float(nan.mean()), 5),
        "post_norm_max": round(float(out.max()), 4),
        "post_norm_median": round(float(np.median(out[~nan])), 6)}
    fits.PrimaryHDU(data=out.astype(np.float32), header=ref_hdr).writeto(
        os.path.join(work, f"jup_{tag}_prep.fits"), overwrite=True)
    print(f"{tag}: shape {out.shape} NaN {nan.mean()*100:.2f}% "
          f"post-norm max {out.max():.3f} -> jup_{tag}_prep.fits")

ds = os.path.join(REPO, "datasets", session, "qa_work")
os.makedirs(ds, exist_ok=True)
json.dump(rec, open(os.path.join(ds, "j2_prepare.json"), "w"), indent=1)
print("-> j2_prepare.json")
