#!/usr/bin/env python3
"""Second-epoch prep for the jwst-jupiter wide-field FIELD-depth route: put
the o009 i2d pair (the observation repeated after one Jovian rotation — the
documented multi-frame S/N mechanism) onto the SAME reference grid and unit
scale as the o008 prep frames, so Siril can stack the FIELD component
(ring/galaxies register in the moving-target frame; the disc is NOT combined
across epochs — features do not line up without derotation; moons move and
ghost in any field combine, a recorded decide point).

Same contract as prepare_jupiter.py: reproject_interp onto the o008 F212N SW
grid, NaN -> 0, the SAME recorded divisors (f212n /50000, f335m /4000) so
prep units match across epochs. Writes work/jup_{f212n,f335m}_ep2_prep.fits
+ the record datasets/<session>/qa_work/j2_ep2_prepare.json.
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
prod = os.path.join(REPO, "sessions", session, "products")
DIVISORS = {"f212n": 50000.0, "f335m": 4000.0}
EP2 = {"f212n": "jw01373-o009_t006_nircam_clear-f212n_i2d.fits",
       "f335m": "jw01373-o009_t006_nircam_clear-f335m_i2d.fits"}

with fits.open(os.path.join(work, "f212n_sci.fits")) as h:
    ref_hdr = h[0].header
    ref_shape = (ref_hdr["NAXIS2"], ref_hdr["NAXIS1"])
ref_wcs = WCS(ref_hdr)

rec = {"session": session, "reference_grid": "o008 f212n (identical to the epoch-1 prep)",
       "reproject": "reproject_interp", "divisors": DIVISORS, "frames": {}}
for tag, fn in EP2.items():
    with fits.open(os.path.join(prod, fn)) as h:
        sci = h["SCI"]
        data, hdr = sci.data.astype(np.float32), sci.header
    print(f"reprojecting o009 {tag} -> o008 f212n grid ...", flush=True)
    out, _ = reproject_interp((data, WCS(hdr)), ref_wcs, shape_out=ref_shape)
    nan = ~np.isfinite(out)
    out = np.nan_to_num(out, nan=0.0).astype(np.float32) / DIVISORS[tag]
    rec["frames"][tag] = {
        "source": fn, "shape": list(out.shape),
        "nan_fraction": round(float(nan.mean()), 5),
        "post_norm_max": round(float(out.max()), 4)}
    fits.PrimaryHDU(data=out, header=ref_hdr).writeto(
        os.path.join(work, f"jup_{tag}_ep2_prep.fits"), overwrite=True)
    print(f"{tag}: NaN {nan.mean()*100:.2f}% max {out.max():.3f} -> jup_{tag}_ep2_prep.fits")

ds = os.path.join(REPO, "datasets", session, "qa_work")
json.dump(rec, open(os.path.join(ds, "j2_ep2_prepare.json"), "w"), indent=1)
print("-> j2_ep2_prepare.json")
