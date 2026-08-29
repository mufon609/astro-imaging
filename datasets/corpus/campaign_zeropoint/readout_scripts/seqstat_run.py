#!/usr/bin/env python3
"""GO #9 level readout: Siril `seqstat full` (IKSS location/scale, median, min, max, noise) on
link-ed SYMLINK sequences built out of tree under readout_work/ — the products are never touched.
Groups: A = 22 campaign finals/nights/corpus + their 22 _outnorm twins (variable canvas sizes);
B = 77 members. Serial Siril via scripts/lib/siril_run.py (the repo lock). Output: seqstat.json
with per-product per-channel numbers (Siril's own [0,1] floats; x65535 = ADU16) and the
level-vs-anchor readings: location/ANCLOC, R/G and B/G vs the anchor's."""
import json, os, sys, csv, subprocess, time
R = "/home/samsung/Desktop/astro-imaging"
sys.path.insert(0, f"{R}/scripts/lib")
import siril_run
W = f"{R}/datasets/corpus/campaign_zeropoint/readout_work"
inv = json.load(open(f"{W}/inventory.json"))
groups = {"A_finals_nights_corpus": [], "B_members": [], "C_member_twins": []}
for e in inv:
    if e["tier"] == "member":
        groups["B_members"].append((e["id"], e["path"])); groups["C_member_twins"].append((e["id"] + " [outnorm twin]", e["twin"]))
    else:
        groups["A_finals_nights_corpus"].append((e["id"], e["path"]))
        groups["A_finals_nights_corpus"].append((e["id"] + " [outnorm twin]", e["twin"]))
only = sys.argv[1:]  # optional group names
out = json.load(open(f"{W}/seqstat.json")) if os.path.exists(f"{W}/seqstat.json") else {}
for g, items in groups.items():
    if only and g not in only: continue
    d = f"{W}/seq_{g}"; subprocess.run(["rm", "-rf", d]); os.makedirs(f"{d}/in"); os.makedirs(f"{d}/seq")
    order = []
    for i, (label, path) in enumerate(items, 1):
        os.symlink(path, f"{d}/in/p_{i:04d}.fit"); order.append(label)
    json.dump(order, open(f"{d}/order.json", "w"), indent=1)
    ssf = f"{d}/seqstat.ssf"; csvp = f"{d}/stats.csv"
    open(ssf, "w").write(f"requires 1.2.0\nset32bits\nsetcompress 0\nsetext fit\ncd {d}/in\nlink s -out={d}/seq\ncd {d}/seq\nseqstat s {csvp} full\n")
    t0 = time.time()
    r = siril_run.run(["-d", d, "-s", ssf], capture_output=True, text=True)
    open(f"{d}/siril.log", "w").write(r.stdout + "\n--- stderr ---\n" + r.stderr)
    print(f"[{g}] {len(items)} images, siril rc {r.returncode}, {time.time()-t0:.0f} s; csv exists: {os.path.exists(csvp)}")
    if not os.path.exists(csvp):
        print(r.stdout[-3000:]); continue
    rows = list(csv.DictReader(open(csvp), delimiter="\t"))
    print(f"  rows {len(rows)} (expected {3*len(items)})")
    for row in rows:
        lab = order[int(row["image"]) - 1]; ch = int(row["chan"])
        out.setdefault(lab, {})[f"ch{ch}"] = {k: float(row[k]) for k in ("mean","median","sigma","min","max","noise","avgDev","mad","sqrtbwmv","location","scale")}
    # keep the symlink dirs (tiny) but drop nothing else
json.dump(out, open(f"{W}/seqstat.json", "w"), indent=1)
print("saved seqstat.json with", len(out), "products")
