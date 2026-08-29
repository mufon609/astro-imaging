#!/usr/bin/env python3
"""GO #9 clamp/hole readout — DIAGNOSTIC numpy (memmap, read-only) for the counts Siril's stat
cannot report (its min/max include zeros). Per product, per channel: n(>=1.0), n(==0), max,
non-zero min; zero pixels split into PADDING (8-connected zero components touching the image
border; only framing=max unions have any) and HOLES (interior zero components), each hole
attributed by its 5x5 neighbourhood in R/G/B, the brightest G within 3 px, and the _outnorm
twin's value at the WCS-mapped position. Clamp components likewise. POSITIVE CONTROL per
product: on a copied 256x256 window, plant one 1.0 and one interior 0 -> each count rises by
exactly 1. Products are opened memmap read-only; nothing is written to them."""
import json, os, sys, numpy as np
from astropy.io import fits
from astropy.wcs import WCS
from scipy import ndimage
import warnings; warnings.filterwarnings("ignore")
R = "/home/samsung/Desktop/astro-imaging"
W = f"{R}/datasets/corpus/campaign_zeropoint/readout_work"
inv = json.load(open(f"{W}/inventory.json"))
def wcs_of(path):
    for p in (path.replace(".fit", "_wcs.fit"), path):
        if os.path.exists(p):
            try:
                h = fits.getheader(p)
                if "CTYPE1" in h: return WCS(h, naxis=2), h
            except Exception: pass
    return None, None
def counts(A):
    return int((A >= 1.0).sum()), int((A == 0).sum())
def control(A):
    y0, x0 = A.shape[0]//2, A.shape[1]//2
    Wd = np.array(A[y0:y0+256, x0:x0+256]); c0 = counts(Wd)
    Wd[10, 10] = 1.0; Wd[100, 100] = 0.0; c1 = counts(Wd)
    return {"before": c0, "after_plant": c1, "ok": (c1[0] == c0[0] + 1) and (c1[1] == c0[1] + 1)}
res = {}
sel = sys.argv[1:]  # optional tier filter
for e in inv:
    if sel and e["tier"] not in sel: continue
    rec = {"tier": e["tier"], "shape": None, "ch": {}, "positive_control": None}
    with fits.open(e["path"], memmap=True, mode="readonly") as hd:
        D = hd[0].data
        rec["shape"] = list(D.shape)
        H, Wd_ = D.shape[1], D.shape[2]
        wn, hn = wcs_of(e["path"]); wo, ho = (wcs_of(e["twin"]) if e["twin"] else (None, None))
        twin = fits.open(e["twin"], memmap=True, mode="readonly")[0].data if e["twin"] else None
        for ch in range(3):
            A = D[ch]
            n1, n0 = counts(A)
            nz = A != 0
            r = {"n_ge1": n1, "n_eq0": n0, "max": float(A.max()), "nonzero_min": float(A[nz].min()) if nz.any() else None,
                 "covered": int(nz.sum())}
            # zeros: padding (border-connected) vs holes (interior)
            if n0:
                lab, ncomp = ndimage.label(A == 0, structure=np.ones((3, 3)))
                border = set(np.unique(np.concatenate([lab[0], lab[-1], lab[:, 0], lab[:, -1]]))) - {0}
                sizes = ndimage.sum(np.ones_like(lab, dtype=np.uint8), lab, np.arange(1, ncomp + 1))
                pad = sum(int(sizes[i - 1]) for i in border)
                holes = [i for i in range(1, ncomp + 1) if i not in border]
                r["padding_zero_px"] = pad; r["n_hole_components"] = len(holes); r["hole_px"] = int(n0 - pad)
                r["holes"] = []
                for i in holes[:50]:
                    ys, xs = np.nonzero(lab == i); y, x = int(ys[0]), int(xs[0])
                    y0, y1, x0, x1 = max(0, y-2), min(H, y+3), max(0, x-2), min(Wd_, x+3)
                    nb = {c: np.round(np.array(D[c, y0:y1, x0:x1]) * 65535, 1).tolist() for c in range(3)}
                    gmax = float(np.array(D[1, y0:y1, x0:x1]).max() * 65535)
                    h = {"size": int(len(ys)), "xy0": [x, y], "xy1_fits": [x + 1, y + 1], "G_max_5x5_ADU16": round(gmax, 1), "nb5x5_ADU16": nb}
                    if wn is not None and wo is not None and twin is not None:
                        try:
                            ra, dec = wn.all_pix2world([[x, y]], 0)[0]
                            xo, yo = wo.all_world2pix([[ra, dec]], 0)[0]
                            xo, yo = int(round(xo)), int(round(yo))
                            if 0 <= xo < twin.shape[2] and 0 <= yo < twin.shape[1]:
                                h["twin_xy0"] = [xo, yo]; h["twin_value_ADU16"] = round(float(twin[ch, yo, xo]) * 65535, 2)
                                h["twin_nb3x3_ADU16"] = np.round(np.array(twin[ch, max(0,yo-1):yo+2, max(0,xo-1):xo+2]) * 65535, 1).tolist()
                        except Exception as ex:
                            h["twin_map_error"] = str(ex)[:80]
                    r["holes"].append(h)
            else:
                r["padding_zero_px"] = 0; r["n_hole_components"] = 0; r["hole_px"] = 0; r["holes"] = []
            if n1:
                lab, ncomp = ndimage.label(A >= 1.0, structure=np.ones((3, 3)))
                comps = []
                for i in range(1, min(ncomp, 50) + 1):
                    ys, xs = np.nonzero(lab == i)
                    comps.append({"size": int(len(ys)), "cx0": float(xs.mean()), "cy0": float(ys.mean()),
                                  "other_ch_max": [float(np.array(D[c][ys, xs]).max()) for c in range(3)]})
                r["clamp_components"] = ncomp; r["clamps"] = comps
            rec["ch"][f"ch{ch}"] = r
        rec["positive_control"] = control(D[0])
        # border check for framing=min products: any zero on the border row/col?
        rec["border_zero_px"] = int(sum(int((np.array(D[c][0]) == 0).sum() + (np.array(D[c][-1]) == 0).sum() + (np.array(D[c][:, 0]) == 0).sum() + (np.array(D[c][:, -1]) == 0).sum()) for c in range(3)))
    res[e["id"]] = rec
    c = rec["ch"]
    print(f"{e['id']:45} {rec['shape'][2]}x{rec['shape'][1]}  ge1 {[c[k]['n_ge1'] for k in c]}  eq0 {[c[k]['n_eq0'] for k in c]}  holes {[c[k]['hole_px'] for k in c]}  pad {[c[k]['padding_zero_px'] for k in c]}  max {[round(c[k]['max'],3) for k in c]}  ctrl {rec['positive_control']['ok']}", flush=True)
    json.dump(res, open(f"{W}/counts{'_'+'_'.join(sel) if sel else ''}.json", "w"), indent=1)
print("done")
