#!/usr/bin/env python3
"""GO #9 judge-surface check: PNG IHDR (width, height, bit depth, colour type) of every campaign judge PNG,
against the product's NAXIS; plus where the corpus PNG landed (U-C4)."""
import json, os, struct, glob, time
R = "/home/samsung/Desktop/astro-imaging"; W = f"{R}/datasets/corpus/campaign_zeropoint/readout_work"
inv = json.load(open(f"{W}/inventory.json")); res = []
for e in inv:
    if e["tier"] == "member": continue
    name = os.path.basename(e["path"])[6:-4]   # <name>_full
    cands = glob.glob(f"{R}/web/results/*/judge/{name}_spcc-linked.png") if e["tier"] == "corpus" else glob.glob(f"{R}/web/results/{e['session']}/judge/{name}_spcc-linked.png")
    for p in sorted(cands):
        b = open(p, "rb").read(33); w, h, bd, ct = struct.unpack(">IIBB", b[16:26])
        res.append({"id": e["id"], "png": os.path.relpath(p, R), "w": w, "h": h, "bit_depth": bd, "colour_type": ct, "bytes": os.path.getsize(p),
                    "mtime": time.strftime("%m-%d %H:%M:%S", time.localtime(os.path.getmtime(p))), "naxis": [e["header"]["NAXIS1"], e["header"]["NAXIS2"]],
                    "canvas_match": (w, h) == (e["header"]["NAXIS1"], e["header"]["NAXIS2"]), "campaign_fresh": os.path.getmtime(p) > 1787934000})
    if not cands: res.append({"id": e["id"], "png": None})
json.dump(res, open(f"{W}/png_ihdr.json", "w"), indent=1)
for r in res: print(f"{r['id']:36} {r.get('png')}  {r.get('w')}x{r.get('h')} bd{r.get('bit_depth')} ct{r.get('colour_type')} match={r.get('canvas_match')} fresh={r.get('campaign_fresh')} {r.get('mtime')}")
