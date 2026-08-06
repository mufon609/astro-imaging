#!/usr/bin/env python3
"""J1 probe: measure the downloaded i2d products' data-class facts and stage
SCI extracts for the Siril behavior probes.

Per product: SCI shape/dtype/BUNIT, WCS pixel scale, NaN census (count,
fraction), finite min/max/median/99.9th percentile. Writes two SCI-only
float32 uncompressed FITS per filter into sessions/<session>/work/:
  <tag>_sci.fits   — SCI verbatim (NaN kept)     -> the Siril NaN probe
  <tag>_sci0.fits  — NaN replaced with 0         -> the working variant
(the NaN->0 step is the documented preparation move for i2d products; the
report records how much of each frame it touches). Report-only + staging;
the record lands in datasets/<session>/qa_work/j1_products.json.
"""
import json
import os
import sys

import numpy as np
from astropy.io import fits
from astropy.wcs import WCS

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
session = sys.argv[1] if len(sys.argv) > 1 else "jwst-jupiter"
prod = os.path.join(REPO, "sessions", session, "products")
work = os.path.join(REPO, "sessions", session, "work")
os.makedirs(work, exist_ok=True)

rows = []
for fn in sorted(os.listdir(prod)):
    if not fn.endswith("_i2d.fits"):
        continue
    tag = fn.split("nircam_")[1].replace("_i2d.fits", "").replace("clear-", "")
    with fits.open(os.path.join(prod, fn)) as hdul:
        sci = hdul["SCI"]
        data = sci.data.astype(np.float32)
        w = WCS(sci.header)
        scale_deg = np.sqrt(np.abs(np.linalg.det(w.pixel_scale_matrix)))
        nan = ~np.isfinite(data)
        finite = data[~nan]
        rows.append({
            "file": fn, "tag": tag,
            "shape": list(data.shape), "bunit": sci.header.get("BUNIT"),
            "pixel_scale_arcsec": round(float(scale_deg * 3600), 5),
            "nan_count": int(nan.sum()),
            "nan_fraction": round(float(nan.mean()), 5),
            "finite_min": float(finite.min()), "finite_max": float(finite.max()),
            "finite_median": float(np.median(finite)),
            "finite_p999": float(np.percentile(finite, 99.9)),
        })
        hdr = sci.header.copy()
        fits.PrimaryHDU(data=data, header=hdr).writeto(
            os.path.join(work, f"{tag}_sci.fits"), overwrite=True)
        fits.PrimaryHDU(data=np.nan_to_num(data, nan=0.0), header=hdr).writeto(
            os.path.join(work, f"{tag}_sci0.fits"), overwrite=True)
        print(f"{tag}: {data.shape} {sci.header.get('BUNIT')} "
              f"scale {scale_deg*3600:.4f}\"/px NaN {nan.mean()*100:.2f}% "
              f"finite[{finite.min():.3f}..{finite.max():.1f}] p999 {np.percentile(finite,99.9):.1f}")

ds = os.path.join(REPO, "datasets", session, "qa_work")
os.makedirs(ds, exist_ok=True)
json.dump({"session": session, "products": rows,
           "why": "J1 data-class census + SCI staging for the Siril probes"},
          open(os.path.join(ds, "j1_products.json"), "w"), indent=1)
print(f"-> {os.path.join(ds, 'j1_products.json')}")
