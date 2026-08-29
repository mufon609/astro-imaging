#!/usr/bin/env python3
"""GO #9 eye-inspection aids for the 22 finals (17 per-set, 4 nights, corpus): 16-bit judge PNGs read
with cv2 (IMREAD_UNCHANGED, never an 8-bit path), each beside its _outnorm twin at like scale and
orientation. Regions are DATA-DERIVED from the new product (block-median luminance of the PNG:
object = brightest interior block, sky = darkest interior block; star = the brightest G pixel of the
linear _spcc.fit), mapped to the twin through both solved WCS headers (naxis=2) and the PNG row
convention measured on july31/set-01 (PNG row = NAXIS2-1-FITS row). Panels: (a) whole frame at fit,
new | old; (b) 1:1 480x480 crops at the three regions, new (top row) over old (bottom row, rotated by
the differential north angle). Metrics beside the eye (DIAGNOSTIC, from the linear _spcc.fit and the
PNG): covered R==0 count + rim fraction (<=50 px from the coverage edge), background R/G and B/G in
the brightest band vs the outer sky (64-px block medians), row/column background structure ratios
(banding), and PNG clip counts (65535 / 0 per channel)."""
import json, os, sys, cv2, numpy as np
from astropy.io import fits
from astropy.wcs import WCS
from scipy import ndimage
import warnings; warnings.filterwarnings("ignore")
R = "/home/samsung/Desktop/astro-imaging"; W = f"{R}/datasets/corpus/campaign_zeropoint/readout_work"; P = f"{W}/panels"; os.makedirs(P, exist_ok=True)
inv = json.load(open(f"{W}/inventory.json")); sel = sys.argv[1:]
def png_of(e):
    name = os.path.basename(e["path"])[6:-4]
    ses = "aug09" if e["tier"] == "corpus" else e["session"]
    return f"{R}/web/results/{ses}/judge/{name}_spcc-linked.png"
def twin_png_of(e):
    # the twin's OWN judge PNG: same session dir as the product (the corpus twin's PNG is the 08-26
    # derived-ref render in aug09/judge, the twin _outnorm.fit's own finish); never another night's set-NN
    name = os.path.basename(e["twin"])[6:-4]
    ses = "aug09" if e["tier"] == "corpus" else e["session"]
    p = f"{R}/web/results/{ses}/judge/{name}_spcc-linked.png"
    assert os.path.exists(p), p
    return p
def wcs(path):
    p = path.replace(".fit", "_wcs.fit"); h = fits.getheader(p if os.path.exists(p) else path); return WCS(h, naxis=2), h
def north(h): return float(np.degrees(np.arctan2(h["CD1_2"], h["CD2_2"])))
def to8(img16): return (img16 // 256).astype(np.uint8)
def crop_rot(img, cx, cy, size, angle):
    big = size * 2
    x0, y0 = int(round(cx - big / 2)), int(round(cy - big / 2))
    pad = np.zeros((big, big, 3), img.dtype)
    xs0, ys0 = max(0, x0), max(0, y0); xs1, ys1 = min(img.shape[1], x0 + big), min(img.shape[0], y0 + big)
    if xs1 > xs0 and ys1 > ys0: pad[ys0 - y0:ys1 - y0, xs0 - x0:xs1 - x0] = img[ys0:ys1, xs0:xs1]
    if abs(angle) > 0.01:
        M = cv2.getRotationMatrix2D((big / 2, big / 2), angle, 1.0); pad = cv2.warpAffine(pad, M, (big, big), flags=cv2.INTER_LINEAR)
    o = (big - size) // 2; return pad[o:o + size, o:o + size]
def label(img, text):
    cv2.rectangle(img, (0, 0), (min(img.shape[1], 12 + 9 * len(text)), 22), (0, 0, 0), -1)
    cv2.putText(img, text, (6, 16), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1, cv2.LINE_AA); return img
metrics = {}
for e in inv:
    if e["tier"] == "member" or (sel and e["id"] not in sel and e["tier"] not in sel): continue
    pn, po = png_of(e), twin_png_of(e)
    new = cv2.imread(pn, cv2.IMREAD_UNCHANGED); old = cv2.imread(po, cv2.IMREAD_UNCHANGED)
    assert new.dtype == np.uint16 and old.dtype == np.uint16, (pn, new.dtype, old.dtype)
    Hn, Wn = new.shape[:2]; Ho, Wo = old.shape[:2]
    wn, hn = wcs(e["path"]); wo, ho = wcs(e["twin"]); dang = north(hn) - north(ho)
    # --- linear metrics from the _spcc.fit (new) and the twin's _spcc.fit (old)
    def lin_metrics(fitpath):
        d = fits.getdata(fitpath, memmap=True); Rc, Gc, Bc = d[0], d[1], d[2]
        lin = fits.getdata(fitpath.replace("_spcc.fit", ".fit"), memmap=True)   # the LINEAR stack: padding == 0 exactly (SPCC's b-offsets make it non-zero in _spcc)
        cov = (np.array(lin[1]) != 0) & (np.array(lin[2]) != 0)               # covered = G and B non-zero in the linear product
        Rc = np.array(lin[0]); r0 = (Rc == 0) & cov                            # R==0 counted on the LINEAR product
        ncov = int(cov.sum()); n_r0 = int(r0.sum()); Rc = d[0]
        rim = 0.0
        if n_r0:
            dist = ndimage.distance_transform_edt(cov); rim = float((dist[r0] <= 50).mean())
        b = 64; Hh, Ww = Gc.shape[0] // b * b, Gc.shape[1] // b * b
        def blk(A): return np.median(np.array(A[:Hh, :Ww]).reshape(Hh // b, b, Ww // b, b), axis=(1, 3))
        bR, bG, bB = blk(Rc), blk(Gc), blk(Bc); bc = blk(cov.astype(np.float32)) >= 1.0
        bc = ndimage.binary_erosion(bc, iterations=2)
        L = (bR + bG + bB) / 3; Li = np.where(bc, L, np.nan)
        hi = Li >= np.nanpercentile(Li, 90); lo = Li <= np.nanpercentile(Li, 30)
        rg = lambda m: (float(np.nanmedian(bR[m] / bG[m])), float(np.nanmedian(bB[m] / bG[m])))
        rows = np.nanmedian(np.where(bc, bG, np.nan), axis=1); cols = np.nanmedian(np.where(bc, bG, np.nan), axis=0)
        rows, cols = rows[np.isfinite(rows)], cols[np.isfinite(cols)]
        return {"covered": ncov, "R_eq0_covered": n_r0, "R_eq0_pct": round(100 * n_r0 / max(ncov, 1), 3), "R_eq0_rim50_frac": round(rim, 3),
                "bright_band_RG_BG": [round(v, 4) for v in rg(hi)], "outer_sky_RG_BG": [round(v, 4) for v in rg(lo)],
                "row_structure_ratio_G": round(float(rows.max() / rows.min()), 3), "col_structure_ratio_G": round(float(cols.max() / cols.min()), 3),
                "median_G_ADU16": round(float(np.nanmedian(bG[bc])) * 65535, 2)}, bG, bc
    mn, bGn, bcn = lin_metrics(e["path"].replace(".fit", "_spcc.fit")); mo, _, _ = lin_metrics(e["twin"].replace(".fit", "_spcc.fit"))
    clip = lambda im: {"eq65535": [int((im[:, :, 2 - c] == 65535).sum()) for c in range(3)], "eq0_RGB": [int((im[:, :, 2 - c] == 0).sum()) for c in range(3)]}
    metrics[e["id"]] = {"new": mn, "old": mo, "png_clip_new": clip(new), "png_clip_old": clip(old), "north_new_old": [round(north(hn), 3), round(north(ho), 3)], "png_new": os.path.relpath(pn, R), "png_old": os.path.relpath(po, R)}
    # --- regions from the NEW png (block median luminance, interior only)
    b = 64; Hh, Ww = Hn // b * b, Wn // b * b
    lum = ((new[:Hh, :Ww, 0].astype(np.uint32) + new[:Hh, :Ww, 1] + new[:Hh, :Ww, 2]) // 3).astype(np.uint16)
    bl = np.median(lum.reshape(Hh // b, b, Ww // b, b), axis=(1, 3))
    # coverage in PNG row order: flip the FITS block coverage
    Gs = fits.getdata(e["path"], memmap=True)[1]   # LINEAR product: padding == 0
    Hh2, Ww2 = Gs.shape[0] // b * b, Gs.shape[1] // b * b
    full = (np.array(Gs[:Hh2, :Ww2]) != 0).reshape(Hh2 // b, b, Ww2 // b, b).min(axis=(1, 3)).astype(bool)   # every pixel of the block covered
    bcov = np.flipud(full)[:bl.shape[0], :bl.shape[1]]; inter = ndimage.binary_erosion(bcov, iterations=(6 if e["tier"] in ("night", "corpus") else 3))
    bli = np.where(inter, bl, np.nan)
    oy, ox = np.unravel_index(np.nanargmax(bli), bli.shape); sy, sx = np.unravel_index(np.nanargmin(bli), bli.shape)
    obj = (int(ox * b + b // 2), int(oy * b + b // 2)); sky = (int(sx * b + b // 2), int(sy * b + b // 2))
    G = fits.getdata(e["path"].replace(".fit", "_spcc.fit"), memmap=True)[1]
    bb = 16; gg = np.array(G[:G.shape[0] // bb * bb, :G.shape[1] // bb * bb]).reshape(G.shape[0] // bb, bb, G.shape[1] // bb, bb).max(axis=(1, 3))
    gy, gx = np.unravel_index(gg.argmax(), gg.shape); sub = np.array(G[gy * bb:(gy + 1) * bb, gx * bb:(gx + 1) * bb]); yy, xx = np.unravel_index(sub.argmax(), sub.shape)
    star_fits = (int(gx * bb + xx), int(gy * bb + yy)); star = (star_fits[0], int(Hn - 1 - star_fits[1]))
    regions = {"object": obj, "sky": sky, "star": star}
    # map to the twin: PNG(x,y) -> FITS (x, H-1-y) -> sky -> twin FITS -> twin PNG
    def to_twin(xy):
        ra, dec = wn.all_pix2world([[xy[0], Hn - 1 - xy[1]]], 0)[0]; xo, yo = wo.all_world2pix([[ra, dec]], 0)[0]
        return (float(xo), float(Ho - 1 - yo))
    tw = {k: to_twin(v) for k, v in regions.items()}
    metrics[e["id"]]["regions_new_png_xy"] = regions; metrics[e["id"]]["regions_old_png_xy"] = {k: [round(v[0], 1), round(v[1], 1)] for k, v in tw.items()}
    # --- panel (a): whole frame at fit
    fw = 960; sn = fw / Wn; so = fw / Wo
    a1 = label(to8(cv2.resize(new, (fw, int(Hn * sn)), interpolation=cv2.INTER_AREA)), f"{e['id']} NEW {Wn}x{Hn}")
    a2 = label(to8(cv2.resize(old, (fw, int(Ho * so)), interpolation=cv2.INTER_AREA)), f"{e['id']} OLD (_outnorm) {Wo}x{Ho}")
    for (x, y), c in zip(regions.values(), [(0, 255, 255), (255, 200, 0), (0, 0, 255)]):
        cv2.rectangle(a1, (int(x * sn) - 12, int(y * sn) - 12), (int(x * sn) + 12, int(y * sn) + 12), c, 1)
    h = max(a1.shape[0], a2.shape[0]); pa = np.zeros((h, 2 * fw + 8, 3), np.uint8); pa[:a1.shape[0], :fw] = a1; pa[:a2.shape[0], fw + 8:] = a2
    cv2.imwrite(f"{P}/{e['id'].replace('/', '_')}_fit.png", pa)
    # --- panel (b): 1:1 crops, new over old (old rotated by the differential north angle)
    sz = 480; tiles_n = []; tiles_o = []
    for k in ("object", "sky", "star"):
        x, y = regions[k]; xo, yo = tw[k]
        tn = label(to8(crop_rot(new, x, y, sz, 0.0)), f"NEW {k} 1:1 @({int(x)},{int(y)})")
        to_ = label(to8(crop_rot(old, xo, yo, sz, -dang)), f"OLD {k} 1:1 rot {dang:+.2f}")
        tiles_n.append(tn); tiles_o.append(to_)
        cn = crop_rot(new, x, y, sz, 0.0); co = crop_rot(old, xo, yo, sz, -dang)
        def chroma(c):
            m = [float(np.median(c[:, :, 2 - i][c[:, :, 1] > 0])) for i in range(3)]
            return {"median_RGB": [round(v, 1) for v in m], "R_over_G": round(m[0] / m[1], 4), "B_over_G": round(m[2] / m[1], 4)}
        metrics[e["id"]].setdefault("png_chroma", {})[k] = {"new": chroma(cn), "old": chroma(co)}
    pb = np.zeros((2 * sz + 8, 3 * sz + 16, 3), np.uint8)
    for i in range(3):
        pb[:sz, i * (sz + 8):i * (sz + 8) + sz] = tiles_n[i]; pb[sz + 8:, i * (sz + 8):i * (sz + 8) + sz] = tiles_o[i]
    cv2.imwrite(f"{P}/{e['id'].replace('/', '_')}_1to1.png", pb)
    print(f"{e['id']:34} regions obj{obj} sky{sky} star{star} dang {dang:+.2f} | new R==0 {mn['R_eq0_covered']} ({mn['R_eq0_pct']}%, rim {mn['R_eq0_rim50_frac']}) old {mo['R_eq0_covered']} ({mo['R_eq0_pct']}%, rim {mo['R_eq0_rim50_frac']}) | band R/G,B/G new {mn['bright_band_RG_BG']} old {mo['bright_band_RG_BG']} | outer new {mn['outer_sky_RG_BG']} old {mo['outer_sky_RG_BG']} | rows/cols new {mn['row_structure_ratio_G']}/{mn['col_structure_ratio_G']} old {mo['row_structure_ratio_G']}/{mo['col_structure_ratio_G']} | png65535 new {metrics[e['id']]['png_clip_new']['eq65535']} old {metrics[e['id']]['png_clip_old']['eq65535']}", flush=True)
    json.dump(metrics, open(f"{W}/inspect_metrics.json", "w"), indent=1)
print("panels in", P)
