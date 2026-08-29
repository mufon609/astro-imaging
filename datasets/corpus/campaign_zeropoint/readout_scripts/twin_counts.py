#!/usr/bin/env python3
"""The _outnorm twins' own counts (the 'before' column): n(>=1.0), n(==0) interior vs padding, max, per channel.
Same instrument as counts.py, no attribution. Read-only memmap."""
import json, numpy as np
from astropy.io import fits
from scipy import ndimage
R = "/home/samsung/Desktop/astro-imaging"; W = f"{R}/datasets/corpus/campaign_zeropoint/readout_work"
inv = json.load(open(f"{W}/inventory.json")); res = {}
for e in inv:
    if not e["twin"]: continue
    with fits.open(e["twin"], memmap=True, mode="readonly") as hd:
        D = hd[0].data; rec = {"shape": list(D.shape), "ch": {}}
        for ch in range(3):
            A = D[ch]; n1 = int((A >= 1.0).sum()); n0 = int((A == 0).sum()); pad = 0
            if n0:
                lab, ncomp = ndimage.label(A == 0, structure=np.ones((3, 3)))
                border = set(np.unique(np.concatenate([lab[0], lab[-1], lab[:, 0], lab[:, -1]]))) - {0}
                sizes = ndimage.sum(np.ones_like(lab, dtype=np.uint8), lab, np.arange(1, ncomp + 1))
                pad = sum(int(sizes[i - 1]) for i in border)
            rec["ch"][f"ch{ch}"] = {"n_ge1": n1, "n_eq0": n0, "padding_zero_px": pad, "hole_px": n0 - pad, "max": float(A.max())}
    res[e["id"]] = rec
    print(f"{e['id']:45} twin ge1 {[rec['ch'][k]['n_ge1'] for k in rec['ch']]} holes {[rec['ch'][k]['hole_px'] for k in rec['ch']]} pad {[rec['ch'][k]['padding_zero_px'] for k in rec['ch']]}", flush=True)
json.dump(res, open(f"{W}/twin_counts.json", "w"), indent=1); print("done")
