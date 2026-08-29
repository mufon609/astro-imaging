#!/usr/bin/env python3
"""GO #9 U-S5 (D2): sky footprint of each campaign product vs its _outnorm twin, from the two solved
WCS headers alone (astropy WCS incl. SIP; header-only). Method: a fine RA/Dec lattice over the union
of both bounding boxes; membership = all_world2pix (iterative inverse SIP) lands inside the canvas;
cell area = dRA*cos(dec)*dDec. Reports each footprint, the overlap, the symmetric difference (sq deg),
IoU, the tangent-point shift and the north angle of each. POSITIVE CONTROLS: self vs self ->
symdiff 0; self vs CRPIX1+100 px -> symdiff = 2 strips of 100 px x NAXIS2 x scale^2."""
import json, os, sys, numpy as np
from astropy.io import fits
from astropy.wcs import WCS
import warnings; warnings.filterwarnings("ignore")
R = "/home/samsung/Desktop/astro-imaging"; W = f"{R}/datasets/corpus/campaign_zeropoint/readout_work"
N = int(os.environ.get("LATTICE", 1400))
def load(path):
    p = path.replace(".fit", "_wcs.fit"); p = p if os.path.exists(p) else path
    h = fits.getheader(p); return WCS(h, naxis=2), h
def bbox(w, h):
    nx, ny = h["NAXIS1"], h["NAXIS2"]
    xs = np.concatenate([np.linspace(0, nx-1, 200), np.full(200, nx-1), np.linspace(nx-1, 0, 200), np.zeros(200)])
    ys = np.concatenate([np.zeros(200), np.linspace(0, ny-1, 200), np.full(200, ny-1), np.linspace(ny-1, 0, 200)])
    ra, dec = w.all_pix2world(np.c_[xs, ys], 0).T
    return ra.min(), ra.max(), dec.min(), dec.max()
def inside(w, h, ra, dec):
    try: xy = w.all_world2pix(np.c_[ra, dec], 0, tolerance=1e-3, maxiter=30, quiet=True)
    except Exception: xy = w.wcs_world2pix(np.c_[ra, dec], 0)
    x, y = xy.T
    return (x >= -0.5) & (x < h["NAXIS1"] - 0.5) & (y >= -0.5) & (y < h["NAXIS2"] - 0.5)
def north_angle(h):
    cd = np.array([[h["CD1_1"], h["CD1_2"]], [h["CD2_1"], h["CD2_2"]]])
    return float(np.degrees(np.arctan2(cd[0, 1], cd[1, 1])))   # PA of +y (up) axis, east of north (sign convention stated)
def compare(wa, ha, wb, hb):
    r0, r1, d0, d1 = bbox(wa, ha); s0, s1, e0, e1 = bbox(wb, hb)
    ra = np.linspace(min(r0, s0), max(r1, s1), N); dec = np.linspace(min(d0, e0), max(d1, e1), N)
    RA, DE = np.meshgrid(ra, dec); RA, DE = RA.ravel(), DE.ravel()
    cell = (ra[1] - ra[0]) * (dec[1] - dec[0]) * np.cos(np.radians(DE))
    A = inside(wa, ha, RA, DE); B = inside(wb, hb, RA, DE)
    aA, aB, aAB = cell[A].sum(), cell[B].sum(), cell[A & B].sum()
    return {"area_A_sqdeg": round(float(aA), 3), "area_B_sqdeg": round(float(aB), 3), "overlap_sqdeg": round(float(aAB), 3),
            "symdiff_sqdeg": round(float(aA + aB - 2 * aAB), 3), "only_A_sqdeg": round(float(aA - aAB), 3), "only_B_sqdeg": round(float(aB - aAB), 3),
            "IoU": round(float(aAB / (aA + aB - aAB)), 4), "lattice": N, "cell_sqdeg_at_centre": round(float(np.median(cell)), 6)}
inv = json.load(open(f"{W}/inventory.json")); sel = sys.argv[1:]
res = {}
for e in inv:
    if sel and e["tier"] not in sel: continue
    if not e["twin"]: continue
    try:
        wa, ha = load(e["path"]); wb, hb = load(e["twin"])
        if "CTYPE1" not in ha or "CTYPE1" not in hb: res[e["id"]] = {"error": "no WCS"}; continue
        c = compare(wa, ha, wb, hb)
        c["tangent_shift_deg"] = round(float(np.degrees(np.arccos(np.clip(np.sin(np.radians(ha["CRVAL2"])) * np.sin(np.radians(hb["CRVAL2"])) + np.cos(np.radians(ha["CRVAL2"])) * np.cos(np.radians(hb["CRVAL2"])) * np.cos(np.radians(ha["CRVAL1"] - hb["CRVAL1"])), -1, 1)))), 4)
        c["north_angle_new_old_deg"] = [round(north_angle(ha), 3), round(north_angle(hb), 3)]
        c["scale_new_old_arcsec"] = [round(3600 * np.sqrt(abs(ha["CD1_1"] * ha["CD2_2"] - ha["CD1_2"] * ha["CD2_1"])), 4), round(3600 * np.sqrt(abs(hb["CD1_1"] * hb["CD2_2"] - hb["CD1_2"] * hb["CD2_1"])), 4)]
        c["canvas_new_old"] = [[ha["NAXIS1"], ha["NAXIS2"]], [hb["NAXIS1"], hb["NAXIS2"]]]
        res[e["id"]] = c
        print(f"{e['id']:40} new {c['area_A_sqdeg']:8.3f} old {c['area_B_sqdeg']:8.3f} overlap {c['overlap_sqdeg']:8.3f} symdiff {c['symdiff_sqdeg']:6.3f} IoU {c['IoU']:.4f} shift {c['tangent_shift_deg']:.3f} deg  north {c['north_angle_new_old_deg']}", flush=True)
    except Exception as ex:
        res[e["id"]] = {"error": str(ex)[:200]}; print(e["id"], "ERR", ex)
# positive controls on the first final
e = next(x for x in inv if x["tier"] == "final"); wa, ha = load(e["path"])
c_self = compare(wa, ha, wa, ha)
hs = ha.copy(); hs["CRPIX1"] = ha["CRPIX1"] + 100; ws = WCS(hs, naxis=2); c_shift = compare(wa, ha, ws, hs)
scale_deg = np.sqrt(abs(ha["CD1_1"] * ha["CD2_2"] - ha["CD1_2"] * ha["CD2_1"]))
expected = 2 * 100 * ha["NAXIS2"] * scale_deg ** 2
res["_positive_controls"] = {"self_vs_self_symdiff": c_self["symdiff_sqdeg"], "self_vs_CRPIX1+100_symdiff": c_shift["symdiff_sqdeg"], "expected_two_strips_sqdeg": round(float(expected), 3), "ratio": round(c_shift["symdiff_sqdeg"] / expected, 3)}
print("positive controls:", res["_positive_controls"])
json.dump(res, open(f"{W}/footprints{'_'+'_'.join(sel) if sel else ''}.json", "w"), indent=1)
