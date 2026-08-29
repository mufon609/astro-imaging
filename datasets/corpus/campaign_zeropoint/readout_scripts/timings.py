#!/usr/bin/env python3
"""GO #9 timings + disk: the campaign's own clock — session START/END stamps and free= figures from the
log; per-member intervals from sub_NN.fit mtimes (previous product's mtime -> this member's); finals
and judge PNG mtimes; the corpus stage. Budget: 17.7 h."""
import json, os, re, time, glob
R = "/home/samsung/Desktop/astro-imaging"; W = f"{R}/datasets/corpus/campaign_zeropoint/readout_work"
log = open(f"{R}/sessions/campaign_zeropoint.log").read().splitlines()
stamps = [l for l in log if re.match(r"^2026-", l)]
def ts(s): return time.mktime(time.strptime(s[:19], "%Y-%m-%dT%H:%M:%S"))
inv = json.load(open(f"{W}/inventory.json"))
events = []
for e in inv:
    events.append((e["mtime"], e["tier"], e["id"], e["header"].get("STACKCNT"), e["header"].get("GRPSIZE")))
    if "mtime_spcc" in e: events.append((e["mtime_spcc"], e["tier"] + "_spcc", e["id"], None, None))
for p in glob.glob(f"{R}/web/results/*/judge/*_full_spcc-linked.png"):
    if os.path.getmtime(p) > 1787934000: events.append((os.path.getmtime(p), "judge_png", os.path.relpath(p, R), None, None))
for s in stamps: events.append((ts(s), "stamp", s[20:], None, None))
events.sort()
rows = []; prev = events[0][0]
for t, kind, ident, cnt, gs in events:
    rows.append({"t": time.strftime("%m-%d %H:%M:%S", time.localtime(t)), "kind": kind, "id": ident, "dt_min": round((t - prev) / 60, 2), "frames": cnt, "grpsize": gs}); prev = t
members = [r for r in rows if r["kind"] == "member"]
per100 = [r["dt_min"] * 100 / r["frames"] for r in members if r["frames"]]
by_ses = {}
for r in members:
    by_ses.setdefault(r["id"].split("/")[0], []).append(r["dt_min"] * 100 / r["frames"])
start = ts(stamps[0]); end = ts([s for s in stamps if "CAMPAIGN DONE" in s][0])
free = [(s[20:].split("free=")[0].strip(), s.split("free=")[1]) for s in stamps if "free=" in s]
out = {"campaign_start": stamps[0][:19], "campaign_end": [s for s in stamps if "CAMPAIGN DONE" in s][0][:19], "wall_h": round((end - start) / 3600, 3), "budget_h": 17.7,
       "sessions": [s[20:] for s in stamps if "session" in s or "corpus" in s], "member_intervals_min": [round(r["dt_min"], 2) for r in members],
       "min_per_100_frames": {"mean": round(sum(per100) / len(per100), 2), "min": round(min(per100), 2), "max": round(max(per100), 2), "n": len(per100),
                              "by_session": {s: round(sum(v) / len(v), 2) for s, v in by_ses.items()}},
       "free_stamps": free, "events": rows}
json.dump(out, open(f"{W}/timings.json", "w"), indent=1)
print(f"campaign {out['campaign_start']} -> {out['campaign_end']} = {out['wall_h']} h (budget 17.7 h)")
print("min per 100 frames:", out["min_per_100_frames"]); print("free stamps:", free)
for r in rows:
    if r["kind"] in ("member", "final", "night", "corpus", "judge_png", "stamp"): print(f"  {r['t']} {r['kind']:10} {str(r['id'])[:60]:60} +{r['dt_min']:6.2f} min {('n='+str(r['frames'])) if r['frames'] else ''}")
