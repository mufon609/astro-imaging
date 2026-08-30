#!/usr/bin/env python3
"""toprow_profiles.py — the member-selection stage's profile on the TOP ROW of ALL 77
members. A DIAGNOSTIC (measurement only): nothing here builds, gates or changes a
product; the stage (run_member_crop.sh / member_profile.py) is untouched and its
centre-row default unchanged. Record: toprow_profiles.json beside this file; scratch
(Siril lists, .ssf) under datasets/corpus/qa_work/toprow_work/ (gitignored).

WHY A SIBLING OF row_profiles.py: that driver hard-codes its eight members and runs the
bottom row and the outer station too; this one runs ONE row on every member with the
identical method — the member's own CACHED centre-row station x-boxes (clamps included)
moved to the top row (box y 0..800), r 400, top-30, the recipe's constants, the rule
applied per row exactly as on the centre row (member_profile.apply_rule, imported).
Centre-row values are READ FROM THE CACHE (datasets/corpus/member_selection/profiles.json)
and never re-profiled; the cache's content premise is MEASURED here by re-hashing every
member before the first Siril run.

WHAT IT ANSWERS (ledger id toprow_profile_all77): whether the top-row softness the six
row-profiled members showed (+0.36..+0.50 px at the centre station, SYMMETRIC entry vs
exit — the case the asymmetry rule is blind to by design) is night-dependent across the
whole corpus, and the top-row frame score S_top for a corpus-relative row-level rule's
pre-registration (reported, not scored).

Every pixel op and every star is Siril's (load, crop, findstar via star_stations.measure);
the top-30 arithmetic is member_profile.py's own (imported). In-house: box placement and
bookkeeping.
"""
import datetime, json, os, statistics, sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
for p in ("scripts/stack", "scripts/qa", "scripts/lib"):
    sys.path.insert(0, os.path.join(REPO, p))
import member_profile as mp          # read_rows, apply_rule, sha256_of — the stage's own arithmetic
import star_stations as ss           # measure (Siril crop + findstar)

CACHE = os.path.join(REPO, "datasets/corpus/member_selection/profiles.json")
STAGE = os.path.join(REPO, "datasets/corpus/member_selection/july31+aug06+aug09+aug14_full_portion.json")
RECIPE = os.path.join(REPO, "datasets/corpus/recipe.json")
WORK = os.path.join(REPO, "datasets/corpus/qa_work/toprow_work")
OUT = os.path.join(HERE, "toprow_profiles.json")
SOFT_SETS = {"aug14/set-01", "aug14/set-02", "aug14/set-03", "aug14/set-04", "aug14/set-05", "aug09/set-04", "aug09/set-05"}
CONTROL_SETS = {"july31/set-01", "july31/set-02", "july31/set-03", "july31/set-04", "aug06/set-01", "aug06/set-02", "aug06/set-03"}


def tag(m):
    p = m.replace("\\", "/").split("/")
    return f"{p[-4]}/{p[-2].replace('groups_', '')}/{p[-1][:-4]}"


def top30(lst, top):
    rows = mp.read_rows(lst)
    bright = sorted(rows, key=lambda t: -t[0])[:top]
    return (round(statistics.median((t[1] + t[2]) / 2 for t in bright), 3) if bright else None,
            round(statistics.median(min(t[1], t[2]) / max(t[1], t[2]) for t in bright), 3) if bright else None,
            len(bright), len(rows))


def measure_boxes(m, wd, boxes, top):
    os.makedirs(wd, exist_ok=True)
    sts = [dict(b) for b in boxes]
    ss.measure(m, wd, sts)
    res = {}
    for s in sts:
        lst = os.path.join(wd, f"{s['name']}.lst")
        f, r, n, ntot = top30(lst, top)
        res[s["name"]] = {"box": s["box"], "top30_fwhm": f, "top30_round": r, "top_n": n, "n_all": ntot,
                          "lst": os.path.relpath(lst, REPO)}
    return res


def q25(xs):
    xs = sorted(xs); i = (len(xs) - 1) * 0.25; lo = int(i)
    return round(xs[lo] + (xs[min(lo + 1, len(xs) - 1)] - xs[lo]) * (i - lo), 4)


def main():
    recipe = json.load(open(RECIPE))["member_selection"]["portion_rule"]
    bar, hw, dxs, top, r = recipe["bar_px"], recipe["half_width_px"], tuple(recipe["stations_px"]), recipe["top_n"], recipe["radius_px"]
    cache = json.load(open(CACHE))["members"]
    stage = json.load(open(STAGE))
    members = sorted(stage["table"].values(), key=lambda row: row["index"])
    started = datetime.datetime.now().astimezone().isoformat(timespec="seconds")
    rec = {"_what": __doc__.strip(), "started_at": started,
           "constants": {"bar_px": bar, "half_width_px": hw, "stations_px": list(dxs), "radius_px": r, "top_n": top, "row": "TOP (box y 0..%d)" % (2 * r)},
           "instrument": "Siril findstar via star_stations.measure (gate 'setfindstar reset -roundness=0.05 -sigma=0.5 -relax=on'; load + crop + findstar -out per station); top-30-by-amplitude median of (FWHMx+FWHMy)/2 and of min/max roundness = member_profile.py profile()'s arithmetic (read_rows/apply_rule imported); centre-row values from the tracked cache, not re-profiled",
           "cache_premise": {}, "members": {}, "ledger": "datasets/aug06/experiments.jsonl id toprow_profile_all77"}
    # the cache-content premise, MEASURED before any Siril run: re-hash every member
    mismatched = []
    for row in members:
        m = os.path.realpath(row["member"]); ent = cache[m]
        sha = mp.sha256_of(m)
        if sha != ent["sha256"]:
            mismatched.append(tag(m))
    rec["cache_premise"] = {"members_rehashed": len(members), "sha256_matches_cache": len(members) - len(mismatched), "mismatched": mismatched,
                            "geometry": {"stations_px": list(dxs), "radius_px": r, "top_n": top}}
    print(f"cache premise: {len(members) - len(mismatched)}/{len(members)} members re-hashed equal to the cache", flush=True)
    if mismatched:
        sys.exit("cache content mismatch on %s — refusing to compare against stale centre-row values" % mismatched)
    json.dump(rec, open(OUT, "w"), indent=1)

    for row in members:
        m = os.path.realpath(row["member"]); ent = cache[m]; W, H = ent["wh"]
        centre_sts = ent["stations"]
        centre = mp.apply_rule(centre_sts, bar, hw, dxs)
        t = tag(m); night_set = "/".join(t.split("/")[:2])
        boxes = [{"name": s["name"], "box": [s["box"][0], 0, s["box"][2], s["box"][3]]} for s in centre_sts if "skipped" not in s]
        wd = os.path.join(WORK, t.replace("/", "_"))
        print(f"[{row['index']:2d}/77] {t}: {len(boxes)} stations on the top row", flush=True)
        meas = measure_boxes(m, wd, boxes, top)
        sts = [{"name": n, "top30_fwhm": v["top30_fwhm"], "shift_px": 0} for n, v in meas.items()]
        for s in centre_sts:
            if "skipped" in s:
                sts.append({"name": s["name"], "skipped": s["skipped"]})
        toprule = mp.apply_rule(sts, bar, hw, dxs)
        cst = {s["name"]: s for s in centre_sts}
        deltas = {n: (round(v["top30_fwhm"] - cst[n]["top30_fwhm"], 3) if v["top30_fwhm"] is not None and cst[n].get("top30_fwhm") is not None else None) for n, v in meas.items()}
        sym = {str(d): (round(abs(toprule["entry"][str(d)] - toprule["exit"][str(d)]), 3) if toprule["entry"][str(d)] is not None and toprule["exit"][str(d)] is not None else None) for d in dxs}
        rec["members"][t] = {
            "index": row["index"], "night_set": night_set, "class": "soft" if night_set in SOFT_SETS else ("control" if night_set in CONTROL_SETS else "unpredicted"),
            "wh": [W, H], "stackcnt": ent.get("stackcnt"), "stage_record": {"cropped": row["cropped"], "x_c": row["x_c"], "onset": row["onset"], "S_advisory_centre": row["S_advisory"]},
            "centre_row_cache": {**centre, "stations": {s["name"]: {"top30_fwhm": s.get("top30_fwhm"), "top30_round": s.get("top30_round"), "n": s.get("n")} for s in centre_sts}},
            "top_row": {"box_y": 0, **toprule, "stations": meas},
            "delta_top_minus_centre_fwhm": deltas,
            "top_row_abs_entry_minus_exit": sym,
            "centre_station_delta": deltas.get("centre"),
        }
        json.dump(rec, open(OUT, "w"), indent=1)

    # ---------------- reductions ----------------
    M = rec["members"]
    soft = [v for v in M.values() if v["class"] == "soft"]; ctrl = [v for v in M.values() if v["class"] == "control"]; unp = [v for v in M.values() if v["class"] == "unpredicted"]
    def frac(vals, pred):
        vals = [v for v in vals if v is not None]; return (sum(1 for v in vals if pred(v)), len(vals))
    p1 = frac([v["centre_station_delta"] for v in soft], lambda x: x >= 0.30)
    p2 = frac([v["centre_station_delta"] for v in ctrl], lambda x: x <= 0.20)
    p3 = frac([(v["top_row_abs_entry_minus_exit"].get("1200"), v["top_row_abs_entry_minus_exit"].get("1800")) for v in soft
               if v["top_row_abs_entry_minus_exit"].get("1200") is not None and v["top_row_abs_entry_minus_exit"].get("1800") is not None],
              lambda ab: ab[0] <= 0.10 and ab[1] <= 0.10)
    S_top = {k: v["top_row"]["S_advisory"] for k, v in M.items() if v["top_row"]["S_advisory"] is not None}
    p25 = q25(list(S_top.values())); over = sorted([(k, s) for k, s in S_top.items() if s > p25 + bar], key=lambda kv: -kv[1])
    by_night = {}
    for k, v in M.items():
        n = k.split("/")[0]; d = v["centre_station_delta"]
        by_night.setdefault(n, []).append(d)
    rec["outcomes"] = {
        "P1_soft_members_top_minus_centre_ge_0p30": {"count": p1[0], "of": p1[1], "fraction": round(p1[0] / p1[1], 3) if p1[1] else None, "held": p1[1] > 0 and p1[0] / p1[1] >= 0.80},
        "P2_control_members_top_minus_centre_le_0p20": {"count": p2[0], "of": p2[1], "fraction": round(p2[0] / p2[1], 3) if p2[1] else None, "held": p2[1] > 0 and p2[0] / p2[1] >= 0.80},
        "P3_soft_members_symmetric_at_1200_and_1800_le_0p10": {"count": p3[0], "of": p3[1], "fraction": round(p3[0] / p3[1], 3) if p3[1] else None, "held": p3[1] > 0 and p3[0] / p3[1] >= 0.80},
        "P4_S_top": {"definition": "mean of the top-row top-30 FWHM over {centre, exit -600..-2400} (member_profile.apply_rule S_advisory on the top-row stations)", "p25": p25, "bar_px": bar,
                     "n_over_p25_plus_bar": len(over), "members_over_p25_plus_bar": over, "all": dict(sorted(S_top.items(), key=lambda kv: -kv[1]))},
        "unpredicted_aug09_set01_03": {"count_ge_0p30": frac([v["centre_station_delta"] for v in unp], lambda x: x >= 0.30)[0], "of": len(unp)},
        "by_night_centre_station_delta": {n: {"n": len(ds), "median": round(statistics.median(ds), 3), "min": min(ds), "max": max(ds)} for n, ds in by_night.items()},
    }
    rec["finished_at"] = datetime.datetime.now().astimezone().isoformat(timespec="seconds")
    json.dump(rec, open(OUT, "w"), indent=1)
    print(json.dumps({k: v for k, v in rec["outcomes"].items() if k != "P4_S_top"}, indent=1))
    print("P4 S_top p25 %.3f; %d over p25+%.2f: %s" % (p25, len(over), bar, over[:20]))
    print("DONE", OUT, flush=True)


if __name__ == "__main__":
    main()
