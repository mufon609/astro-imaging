#!/usr/bin/env python3
"""GO #9 guard tables: every `baseline_guard <ses>/<set>` block in the campaign log (now vs baseline,
advisory lines, verdict), cross-read against the guard's own scratch records
datasets/<ses>/<set>/qa_work/baseline_{corners,edge}.json through baseline_guard._derive (the same
arithmetic the guard ran), and the aug14 'no baseline' lines."""
import json, re, sys, os
R = "/home/samsung/Desktop/astro-imaging"; W = f"{R}/datasets/corpus/campaign_zeropoint/readout_work"
sys.path.insert(0, f"{R}/scripts/qa"); import baseline_guard as bg
log = open(f"{R}/sessions/campaign_zeropoint.log").read().splitlines()
res = {"tables": [], "no_baseline": []}
i = 0
while i < len(log):
    m = re.match(r"^baseline_guard (\w+)/(set-\d\d)$", log[i])
    if m:
        ses, st = m.groups(); blk = {"set": f"{ses}/{st}", "rows": {}, "advisory": [], "fails": [], "verdict": None}
        j = i + 1
        while j < len(log) and not re.match(r"^(PASS|REGRESSION)", log[j]):
            r = re.match(r"^\s+(corner_spread_pct|edge_dipole_x|centre_ch\d|stacknrm)\s+(\S+)\s+(\S+)", log[j])
            if r: blk["rows"][r.group(1)] = [r.group(2), r.group(3)]
            if log[j].startswith("  ~ "): blk["advisory"].append(log[j].strip()[2:])
            if log[j].startswith("  - "): blk["fails"].append(log[j].strip()[2:])
            j += 1
        blk["verdict"] = log[j] if j < len(log) else None
        # recompute from the scratch records
        try:
            corners = json.load(open(f"{R}/datasets/{ses}/{st}/qa_work/baseline_corners.json")); edge = json.load(open(f"{R}/datasets/{ses}/{st}/qa_work/baseline_edge.json"))
            dc, de = corners["regions"], edge["regions"]
            chc = "ch1" if "ch1" in dc["TL"] else "ch0"; che = "ch1" if "ch1" in de["TL"] else "ch0"
            spread, dip = bg._derive({k: dc[k][chc]["median"] for k in ("TL", "TR", "BL", "BR", "center")}, {k: de[k][che]["median"] for k in ("TL", "TR", "BL", "BR", "center")})
            chans = {k: v["median"] for k, v in dc["center"].items()}
            blk["recomputed_from_scratch"] = {"corner_spread_pct": spread, "edge_dipole_x": dip, "centre": chans, "image_wh": corners.get("image_wh"), "stack": corners.get("stack") or corners.get("input")}
            blk["scratch_matches_log"] = (abs(spread - float(blk["rows"]["corner_spread_pct"][0])) < 0.0015 and abs(dip - float(blk["rows"]["edge_dipole_x"][0])) < 0.00015 and all(abs(chans[c] - float(blk["rows"]["centre_" + c][0])) < 0.06 for c in chans))
        except Exception as ex:
            blk["recomputed_from_scratch"] = f"ERR {ex}"
        base = json.load(open(f"{R}/datasets/{ses}/{st}/baseline.json"))["measures"]
        blk["baseline_file"] = {"corner_spread_pct": base["corner_spread_pct"], "edge_dipole_x": base["edge_dipole_x"], "centre": base["centre_median_per_channel"], "stacknrm": base.get("stacknrm", "(absent)")}
        res["tables"].append(blk); i = j
    elif "no-regression: no baseline for this set yet" in log[i]:
        res["no_baseline"].append(log[i].strip()); i += 1
    else: i += 1
json.dump(res, open(f"{W}/guard_tables.json", "w"), indent=1)
print(f"{'set':14} {'spread now/base':18} {'dipole now/base':20} {'centre now (ch0/1/2)':22} {'base':20} verdict / advisory / scratch==log")
for b in res["tables"]:
    r = b["rows"]; print(f"{b['set']:14} {r['corner_spread_pct'][0]:>7}/{r['corner_spread_pct'][1]:<9} {r['edge_dipole_x'][0]:>8}/{r['edge_dipole_x'][1]:<10} {r['centre_ch0'][0]}/{r['centre_ch1'][0]}/{r['centre_ch2'][0]:<9} {r['centre_ch0'][1]}/{r['centre_ch1'][1]}/{r['centre_ch2'][1]:<8} {b['verdict']} | {len(b['advisory'])} adv | {b.get('scratch_matches_log')}")
print("no-baseline lines:", len(res["no_baseline"])); [print("  ", l[:120]) for l in res["no_baseline"]]
