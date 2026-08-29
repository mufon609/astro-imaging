#!/usr/bin/env python3
"""GO #9 inventory: every campaign product with its _outnorm twin, tier, session, set.
Header-only (astropy). Writes readout_work/inventory.json. Read-only on the tree."""
import glob, json, os, re, sys
from astropy.io import fits
R = "/home/samsung/Desktop/astro-imaging"
SES = ["july31", "aug06", "aug09", "aug14"]
KEYS = ["NAXIS1","NAXIS2","STACKNRM","ANCSRC","ANCREF","ANCLOCR","ANCLOCG","ANCLOCB","ANCSCLR","ANCSCLG","ANCSCLB",
        "REGREF","REGREFSR","REGMODEL","REGUNDIS","NMEMBER","STACKCNT","GRPSIZE","PIPEREV","CALSETS","CALSET",
        "MAXMSEP","NDISTMOD","MSEPVERD","FILENAME","DATE","LIVETIME","SOLVCENT","SOLVMAXS","BKGLIGHT","DISTSRC"]
def hdr(p):
    h = fits.getheader(p)
    d = {k: h.get(k) for k in KEYS if h.get(k) is not None}
    d["HISTORY_stack"] = next((str(x) for x in (h.get("HISTORY", []) if "HISTORY" in h else []) if "stacking" in str(x)), None)
    return d
inv = []
for s in SES:
    for gd in sorted(glob.glob(f"{R}/sessions/{s}/work/groups_set-[0-9][0-9]")):
        st = os.path.basename(gd).replace("groups_", "")
        for sub in sorted(glob.glob(f"{gd}/sub_*.fit")):
            twin = f"{gd}_outnorm/{os.path.basename(sub)}"
            inv.append({"tier": "member", "session": s, "set": st, "id": f"{s}/{st}/{os.path.basename(sub)}",
                        "path": sub, "twin": twin if os.path.exists(twin) else None})
    for fin in sorted(glob.glob(f"{R}/web/results/{s}/stack_set-[0-9][0-9]_full.fit")):
        st = re.search(r"stack_(set-\d\d)_full", fin).group(1)
        twin = fin.replace("_full.fit", "_outnorm.fit")
        inv.append({"tier": "final", "session": s, "set": st, "id": f"{s}/{st}", "path": fin,
                    "twin": twin if os.path.exists(twin) else None})
    for night in sorted(glob.glob(f"{R}/web/results/{s}/stack_set-*+*_full.fit")):
        twin = night.replace("_full.fit", "_outnorm.fit")
        inv.append({"tier": "night", "session": s, "set": None, "id": f"{s}/{os.path.basename(night)[6:-9]}", "path": night,
                    "twin": twin if os.path.exists(twin) else None})
corp = f"{R}/web/results/aug14/stack_july31+aug06+aug09+aug14_full.fit"
inv.append({"tier": "corpus", "session": "aug14", "set": None, "id": "corpus/july31+aug06+aug09+aug14", "path": corp,
            "twin": corp.replace("_full.fit", "_outnorm.fit") if os.path.exists(corp.replace("_full.fit", "_outnorm.fit")) else None})
for e in inv:
    e["header"] = hdr(e["path"])
    e["mtime"] = os.path.getmtime(e["path"]); e["bytes"] = os.path.getsize(e["path"])
    for v in ("_wcs", "_spcc"):
        p = e["path"].replace(".fit", v + ".fit")
        if os.path.exists(p):
            e["header" + v] = hdr(p); e["mtime" + v] = os.path.getmtime(p)
    if e["twin"]:
        e["twin_header"] = hdr(e["twin"])
        tw = e["twin"].replace(".fit", "_wcs.fit")
        if os.path.exists(tw): e["twin_header_wcs"] = hdr(tw)
        e["twin_bytes"] = os.path.getsize(e["twin"])
out = f"{R}/datasets/corpus/campaign_zeropoint/readout_work/inventory.json"
json.dump(inv, open(out, "w"), indent=1)
from collections import Counter
print(Counter(e["tier"] for e in inv), "twins missing:", [e["id"] for e in inv if not e["twin"]])
print("saved", out)
