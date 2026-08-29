#!/usr/bin/env python3
"""GO #9 level table from seqstat.json (Siril seqstat full, IKSS location/scale) + the stamped anchor
(ANCLOC*, Siril's own M-line location of the reference): location/ANCLOC per channel, R/G and B/G of the
product vs the anchor's, per tier; the _outnorm twins' own levels for the declared delta."""
import json, statistics as st
R = "/home/samsung/Desktop/astro-imaging"; W = f"{R}/datasets/corpus/campaign_zeropoint/readout_work"
inv = json.load(open(f"{W}/inventory.json")); ss = json.load(open(f"{W}/seqstat.json"))
rows = []
for e in inv:
    s = ss.get(e["id"]); h = e["header"]
    if not s: continue
    loc = [s[f"ch{c}"]["location"] for c in range(3)]; med = [s[f"ch{c}"]["median"] for c in range(3)]
    anc = [h.get("ANCLOCR"), h.get("ANCLOCG"), h.get("ANCLOCB")]
    r = {"id": e["id"], "tier": e["tier"], "location_ADU16": [round(v * 65535, 3) for v in loc], "median_ADU16": [round(v * 65535, 3) for v in med],
         "ANCLOC_ADU16": [round(v * 65535, 3) for v in anc] if all(anc) else None, "min_ADU16": [round(s[f"ch{c}"]["min"] * 65535, 2) for c in range(3)],
         "max": [round(s[f"ch{c}"]["max"], 5) for c in range(3)], "noise_ADU16": [round(s[f"ch{c}"]["noise"] * 65535, 3) for c in range(3)],
         "scale_ADU16": [round(s[f"ch{c}"]["scale"] * 65535, 3) for c in range(3)]}
    if all(anc):
        r["loc_over_ANCLOC"] = [round(loc[c] / anc[c], 5) for c in range(3)]
        r["RG_BG_product"] = [round(loc[0] / loc[1], 4), round(loc[2] / loc[1], 4)]
        r["RG_BG_anchor"] = [round(anc[0] / anc[1], 4), round(anc[2] / anc[1], 4)]
        r["RG_BG_delta_pct"] = [round(100 * (r["RG_BG_product"][i] / r["RG_BG_anchor"][i] - 1), 3) for i in range(2)]
    t = ss.get(e["id"] + " [outnorm twin]")
    if t:
        tl = [t[f"ch{c}"]["location"] for c in range(3)]
        r["twin_location_ADU16"] = [round(v * 65535, 3) for v in tl]; r["twin_RG_BG"] = [round(tl[0] / tl[1], 4), round(tl[2] / tl[1], 4)]
        r["level_ratio_new_over_old"] = [round(loc[c] / tl[c], 4) for c in range(3)]
        r["twin_min_max"] = [[round(t[f"ch{c}"]["min"] * 65535, 2), round(t[f"ch{c}"]["max"], 5)] for c in range(3)]
    rows.append(r)
agg = {}
for tier in ("member", "final", "night", "corpus"):
    v = [r for r in rows if r["tier"] == tier and "loc_over_ANCLOC" in r]
    if not v: continue
    agg[tier] = {"n": len(v)}
    for c, nm in enumerate("RGB"):
        x = [r["loc_over_ANCLOC"][c] for r in v]
        agg[tier][f"loc_over_ANCLOC_{nm}"] = {"min": min(x), "max": max(x), "mean": round(st.mean(x), 5)}
    for i, nm in enumerate(("RG", "BG")):
        x = [r["RG_BG_delta_pct"][i] for r in v]
        agg[tier][f"{nm}_delta_pct"] = {"min": min(x), "max": max(x), "mean": round(st.mean(x), 3), "max_abs": max(abs(a) for a in x)}
json.dump({"rows": rows, "aggregate": agg}, open(f"{W}/level_table.json", "w"), indent=1)
print(json.dumps(agg, indent=1))
print(f"\n{'product':34} {'location R/G/B ADU16':28} {'loc/ANCLOC R/G/B':26} {'R/G,B/G vs anchor %':20} {'twin loc':26} new/old")
for r in rows:
    if r["tier"] == "member": continue
    print(f"{r['id']:34} {'/'.join(f'{v:.2f}' for v in r['location_ADU16']):28} {'/'.join(f'{v:.4f}' for v in r.get('loc_over_ANCLOC', [0,0,0])):26} {str(r.get('RG_BG_delta_pct')):20} {'/'.join(f'{v:.2f}' for v in r.get('twin_location_ADU16', [0,0,0])):26} {r.get('level_ratio_new_over_old')}")
m = [r for r in rows if r["tier"] == "member"]
print(f"\nmembers: {len(m)}; loc/ANCLOC R range {min(r['loc_over_ANCLOC'][0] for r in m):.4f}-{max(r['loc_over_ANCLOC'][0] for r in m):.4f}; worst |R/G,B/G delta| {max(max(abs(a) for a in r['RG_BG_delta_pct']) for r in m):.3f}%")
print("member level/old-member level (R):", sorted(round(r['level_ratio_new_over_old'][0], 3) for r in m if 'level_ratio_new_over_old' in r)[:3], "...", sorted(round(r['level_ratio_new_over_old'][0], 3) for r in m if 'level_ratio_new_over_old' in r)[-3:])
print("member R sky (ANCLOC R ADU16) range:", min(r['ANCLOC_ADU16'][0] for r in m), max(r['ANCLOC_ADU16'][0] for r in m))
