#!/usr/bin/env python3
"""GO #9 K table: old (git HEAD record, paired to the moved _outnorm product by input path + size;
ties by input_mtime == file mtime, else latest) vs new (the campaign's record) for 17 finals,
4 nights, the corpus. Scored BOTH ways (D1): per product vs the frozen H1 bar (|dK_G|<=0.009,
|dK_B|<=0.018) and vs its own night's OLD per-set K spread (min..max of the night's old finals);
aggregate per tier: mean, sd, sign count per channel. b-offsets x65535 (D5), stars kept."""
import json, os, re, subprocess, glob
R = "/home/samsung/Desktop/astro-imaging"; W = f"{R}/datasets/corpus/campaign_zeropoint/readout_work"
inv = json.load(open(f"{W}/inventory.json"))
tracked = subprocess.run(["git", "-C", R, "ls-files", "datasets/*/*/qa_work/spcc_*.json", "datasets/corpus/spcc_*.json"], capture_output=True, text=True).stdout.split()
old_recs = []
for t in tracked:
    d = json.loads(subprocess.run(["git", "-C", R, "show", f"HEAD:{t}"], capture_output=True, text=True).stdout)
    old_recs.append((t, d))
def old_for(twin_path):
    """twin = web/results/<ses>/stack_<name>_outnorm.fit ; old records name web/results/<ses>/stack_<name>_full_wcs.fit"""
    wcs = twin_path.replace("_outnorm.fit", "_outnorm_wcs.fit")
    size = os.path.getsize(wcs); mt = int(os.path.getmtime(wcs))
    pre = os.path.relpath(twin_path.replace("_outnorm.fit", "_full_wcs.fit"), R)   # pre-move name
    cands = [(t, d) for t, d in old_recs if os.path.normpath(os.path.join(R, "datasets", "x", "y", d["input"])).endswith(pre.replace("web/results/", "")) and d.get("input_size") == size]
    cands = [(t, d) for t, d in cands if d["input"].replace("../../", "") == pre]
    if not cands: return None, "NO RECORD (path+size)"
    exact = [(t, d) for t, d in cands if d.get("input_mtime") == mt]
    if exact: return exact[0], "path+size+mtime"
    cands.sort(key=lambda td: td[1].get("input_mtime", 0)); return cands[-1], f"path+size (latest of {len(cands)})"
def new_for(e):
    # the campaign's record: under REGREF's set for nights/corpus, the set itself for finals
    ses = e["session"]; st = e["set"]
    if e["tier"] == "final":
        p = f"{R}/datasets/{ses}/{st}/qa_work/spcc_{st}_{st}_full.json"
    else:
        h = e.get("header_spcc") or e["header"]; m = re.match(r"\d+:([^/]+)/groups_(set-[0-9a-z]+)/", str(h.get("REGREF", "")))
        rses, rset = m.group(1), m.group(2)
        name = os.path.basename(e["path"])[6:-4]   # stack_<name>_full
        p = f"{R}/datasets/{rses}/{rset}/qa_work/spcc_{rset}_{name}.json"
    return (os.path.relpath(p, R), json.load(open(p))) if os.path.exists(p) else (os.path.relpath(p, R), None)
rows = []
for e in inv:
    if e["tier"] == "member": continue
    (ot, od), how = old_for(e["twin"]) if e["twin"] else ((None, None), "no twin")
    nt, nd = new_for(e)
    k_o = od["k_factors"] if od else None; k_n = nd["k_factors"] if nd else None
    rows.append({"id": e["id"], "tier": e["tier"], "session": e["session"], "set": e["set"],
                 "old_record": ot, "old_pairing": how, "new_record": nt,
                 "K_old": [k_o["R"], k_o["G"], k_o["B"]] if k_o else None, "K_new": [k_n["R"], k_n["G"], k_n["B"]] if k_n else None,
                 "b_old_ADU16": [round(v * 65535, 1) for v in od["b_offsets"].values()] if od and od.get("b_offsets") else None,
                 "b_new_ADU16": [round(v * 65535, 1) for v in nd["b_offsets"].values()] if nd and nd.get("b_offsets") else None,
                 "kept_old": [od["n_kept"], od["n_photometry"]] if od else None, "kept_new": [nd["n_kept"], nd["n_photometry"]] if nd else None})
# the night's old per-set K spread (from the finals' old records)
spread = {}
for r in rows:
    if r["tier"] == "final" and r["K_old"]:
        spread.setdefault(r["session"], {"G": [], "B": []}); spread[r["session"]]["G"].append(r["K_old"][1]); spread[r["session"]]["B"].append(r["K_old"][2])
for s in spread:
    spread[s] = {c: [min(v), max(v), round(max(v) - min(v), 3)] for c, v in spread[s].items()}
BAR = {"G": 0.009, "B": 0.018}
for r in rows:
    if r["K_old"] and r["K_new"]:
        dG = round(r["K_new"][1] - r["K_old"][1], 3); dB = round(r["K_new"][2] - r["K_old"][2], 3)
        r["dK_G"], r["dK_B"] = dG, dB
        r["H1_frozen"] = {"G": "MET" if abs(dG) <= BAR["G"] else "NOT MET", "B": "MET" if abs(dB) <= BAR["B"] else "NOT MET"}
        sp = spread.get(r["session"]) or spread.get("aug09")   # corpus: scored vs every night below
        r["vs_own_night_old_spread"] = {"G": "within" if abs(dG) <= sp["G"][2] else "outside", "B": "within" if abs(dB) <= sp["B"][2] else "outside", "night_spread_G_B": [sp["G"][2], sp["B"][2]]} if r["tier"] != "corpus" else {c: {s: ("within" if abs(d) <= spread[s][c][2] else "outside") for s in spread} for c, d in (("G", dG), ("B", dB))}
import statistics as st
agg = {}
for tier in ("final", "night"):
    for c, key in (("G", "dK_G"), ("B", "dK_B")):
        v = [r[key] for r in rows if r["tier"] == tier and key in r]
        if v: agg[f"{tier}_{c}"] = {"n": len(v), "mean": round(st.mean(v), 4), "sd": round(st.stdev(v), 4) if len(v) > 1 else None, "neg": sum(1 for x in v if x < 0), "pos": sum(1 for x in v if x > 0), "zero": sum(1 for x in v if x == 0), "min": min(v), "max": max(v), "sem": round(st.stdev(v) / len(v) ** 0.5, 4) if len(v) > 1 else None}
out = {"bar": BAR, "night_old_K_spread": spread, "rows": rows, "aggregate": agg}
json.dump(out, open(f"{W}/ktable.json", "w"), indent=1)
print(f"{'product':32} {'K_old G/B':12} {'K_new G/B':12} {'dG':>7} {'dB':>7}  H1(G/B)     night-spread   kept old->new        b_R old->new")
for r in rows:
    if not r["K_new"]: print(r["id"], "NEW RECORD MISSING", r["new_record"]); continue
    ko = f"{r['K_old'][1]:.3f}/{r['K_old'][2]:.3f}" if r["K_old"] else "-"
    print(f"{r['id']:32} {ko:12} {r['K_new'][1]:.3f}/{r['K_new'][2]:.3f}   {r.get('dK_G','-'):>7} {r.get('dK_B','-'):>7}  {r.get('H1_frozen',{}).get('G','-')[:7]:7}/{r.get('H1_frozen',{}).get('B','-')[:7]:7} {str(r.get('vs_own_night_old_spread',{}).get('G','-'))[:7]:7}/{str(r.get('vs_own_night_old_spread',{}).get('B','-'))[:7]:7} {str(r['kept_old'])}->{r['kept_new']}  {r['b_old_ADU16'][0] if r['b_old_ADU16'] else '-'}->{r['b_new_ADU16'][0] if r['b_new_ADU16'] else '-'}   [{r['old_pairing']}]")
print("night old-K spreads:", json.dumps(spread)); print("aggregate:", json.dumps(agg, indent=0))
