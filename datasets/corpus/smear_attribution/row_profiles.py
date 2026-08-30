#!/usr/bin/env python3
"""row_profiles.py — the member-selection stage's profile OFF the centre row and PAST its
last station. A DIAGNOSTIC (measurement only): nothing here builds, gates or changes a
product; the stage (run_member_crop.sh / member_profile.py) is untouched and its default
behaviour unchanged. Record: row_profiles.json beside this file; scratch (Siril lists,
.ssf) under datasets/corpus/qa_work/row_profiles_work/ (gitignored).

Knob d — ROW-RESOLVED PROFILE: the member's own cached station x-boxes (centre + along
+-600/1200/1800/2400, r 400, clamps included) moved to the TOP row (box y 0..800) and the
BOTTOM row (box y H-800..H); the rule (bar / half-width from datasets/corpus/recipe.json)
applied per row exactly as on the centre row. Centre-row values are READ FROM THE CACHE
(datasets/corpus/member_selection/profiles.json), never re-profiled.
Knob c — OUTER STATION: centre row, dx +2700 with r 200 (+ the -2700 mirror) on the
uncropped members; a box that does not fit is REFUSED and named, never clamped.
Variant c' — the same zone EDGE-ANCHORED (entry box x W-416..W-16, exit mirror 16..416,
r 200) on every uncropped member, a separate block.

Every pixel op and every star is Siril's (load, crop, findstar via star_stations.measure);
the top-30 arithmetic is member_profile.py's own (imported). In-house here: box placement
and bookkeeping. Removal condition: a tool reporting a headless row-resolved star-shape
map (the star_stations.py row of the register) retires this with it.
"""
import datetime, json, os, statistics, sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
for p in ("scripts/stack", "scripts/qa", "scripts/lib"):
    sys.path.insert(0, os.path.join(REPO, p))
import member_profile as mp          # read_rows, apply_rule — the stage's own arithmetic
import star_stations as ss           # measure (Siril crop + findstar), image_dims

CACHE = os.path.join(REPO, "datasets/corpus/member_selection/profiles.json")
STAGE = os.path.join(REPO, "datasets/corpus/member_selection/july31+aug06+aug09+aug14_full_portion.json")
RECIPE = os.path.join(REPO, "datasets/corpus/recipe.json")
WORK = os.path.join(REPO, "datasets/corpus/qa_work/row_profiles_work")
OUT = os.path.join(HERE, "row_profiles.json")

D_MEMBERS = [  # knob d: the six corner_direction members + two controls
    "sessions/aug14/work/groups_set-04/sub_01.fit", "sessions/aug14/work/groups_set-04/sub_04.fit",
    "sessions/aug14/work/groups_set-05/sub_01.fit", "sessions/aug14/work/groups_set-05/sub_02.fit",
    "sessions/aug09/work/groups_set-05/sub_01.fit", "sessions/aug09/work/groups_set-05/sub_02.fit",
    "sessions/july31/work/groups_set-01/sub_01.fit", "sessions/aug06/work/groups_set-01/sub_01.fit"]
CONTROLS = {"sessions/july31/work/groups_set-01/sub_01.fit", "sessions/aug06/work/groups_set-01/sub_01.fit"}
R_OUT = 200; DX_OUT = 2700; EDGE_IN = 16   # knob c: r 200 at +2700; c': box ends 16 px inside the edge


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
    """boxes: list of {name, box}; returns {name: {top30_fwhm, top30_round, top_n, n, lst}}"""
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


def main():
    recipe = json.load(open(RECIPE))["member_selection"]["portion_rule"]
    bar, hw, dxs, top, r = recipe["bar_px"], recipe["half_width_px"], tuple(recipe["stations_px"]), recipe["top_n"], recipe["radius_px"]
    cache = json.load(open(CACHE))["members"]
    stage = json.load(open(STAGE))
    started = datetime.datetime.now().astimezone().isoformat(timespec="seconds")
    rec = {"_what": __doc__.strip(), "started_at": started, "constants": {"bar_px": bar, "half_width_px": hw, "stations_px": list(dxs), "radius_px": r, "top_n": top},
           "instrument": "Siril findstar via star_stations.measure (gate 'setfindstar reset -roundness=0.05 -sigma=0.5 -relax=on'; load + crop + findstar -out per station); top-30-by-amplitude median of (FWHMx+FWHMy)/2 and of min/max roundness = member_profile.py profile()'s arithmetic (read_rows/apply_rule imported); centre-row values from the tracked cache, not re-profiled",
           "knob_d_rows": {}, "knob_c_outer_station": {}, "knob_c_prime_edge_anchored": {}}

    # ---------------- knob d: rows ----------------
    for rel in D_MEMBERS:
        m = os.path.realpath(os.path.join(REPO, rel))
        ent = cache[m]; W, H = ent["wh"]
        centre_sts = ent["stations"]
        centre = mp.apply_rule(centre_sts, bar, hw, dxs)
        out = {"wh": [W, H], "control": rel in CONTROLS, "stage_record": {"x_c": None, "cropped": False}, "centre_row": {"from": "cache", **centre,
               "stations": {s["name"]: {"box": s.get("box"), "top30_fwhm": s.get("top30_fwhm"), "top30_round": s.get("top30_round"), "n": s.get("n")} for s in centre_sts}}}
        for row in stage["table"].values():
            if os.path.realpath(row["member"]) == m:
                out["stage_record"] = {"x_c": row["x_c"], "cropped": row["cropped"], "onset": row["onset"]}
        for rowname, y in (("top", 0), ("bottom", H - 2 * r)):
            boxes = []
            for s in centre_sts:
                if "skipped" in s:
                    continue
                x, _, w, h = s["box"]
                boxes.append({"name": s["name"], "box": [x, y, w, h]})
            wd = os.path.join(WORK, tag(m).replace("/", "_"), rowname)
            print(f"[d] {tag(m)} {rowname} row: {len(boxes)} stations, box y {y}", flush=True)
            meas = measure_boxes(m, wd, boxes, top)
            sts = [{"name": n, "top30_fwhm": v["top30_fwhm"], "shift_px": 0} for n, v in meas.items()]
            for s in centre_sts:
                if "skipped" in s:
                    sts.append({"name": s["name"], "skipped": s["skipped"]})
            rule = mp.apply_rule(sts, bar, hw, dxs)
            out[f"{rowname}_row"] = {"box_y": y, **rule, "stations": meas}
        rec["knob_d_rows"][tag(m)] = out
        json.dump(rec, open(OUT, "w"), indent=1)

    # ---------------- knob c: outer station on the uncropped members ----------------
    unc = [row for row in stage["table"].values() if not row["cropped"]]
    for row in unc:
        m = os.path.realpath(row["member"]); ent = cache[m]; W, H = ent["wh"]
        cx, cy = W / 2.0, H / 2.0
        c24 = mp.apply_rule(ent["stations"], bar, hw, dxs)
        base = {"wh": [W, H], "centre_row_cache": {"asym_2400": c24["asymmetry"][str(dxs[-1])], "entry_2400": c24["entry"][str(dxs[-1])], "exit_2400": c24["exit"][str(dxs[-1])], "onset": c24["onset"]}}
        boxes = []
        xp = int(round(cx + DX_OUT - R_OUT)); xm = int(round(cx - DX_OUT - R_OUT)); y = int(round(cy - R_OUT))
        fits = (xp + 2 * R_OUT <= W) and (xm >= 0)
        if fits:
            boxes += [{"name": "c27_plus", "box": [xp, y, 2 * R_OUT, 2 * R_OUT]}, {"name": "c27_minus", "box": [xm, y, 2 * R_OUT, 2 * R_OUT]}]
            rec["knob_c_outer_station"][tag(m)] = {**base, "boxes": {"plus": [xp, y, 2 * R_OUT, 2 * R_OUT], "minus": [xm, y, 2 * R_OUT, 2 * R_OUT]}}
        else:
            rec["knob_c_outer_station"][tag(m)] = {**base, "refused": f"+2700 r200 box x {xp}..{xp + 2 * R_OUT} exceeds W={W} by {xp + 2 * R_OUT - W} px (no clamp)"}
        xe = W - 2 * R_OUT - EDGE_IN; xe_m = EDGE_IN
        boxes += [{"name": "ce_plus", "box": [xe, y, 2 * R_OUT, 2 * R_OUT]}, {"name": "ce_minus", "box": [xe_m, y, 2 * R_OUT, 2 * R_OUT]}]
        rec["knob_c_prime_edge_anchored"][tag(m)] = {**base, "dx_equiv": round(xe + R_OUT - cx, 1), "boxes": {"plus": [xe, y, 2 * R_OUT, 2 * R_OUT], "minus": [xe_m, y, 2 * R_OUT, 2 * R_OUT]}}
        wd = os.path.join(WORK, tag(m).replace("/", "_"), "outer")
        print(f"[c] {tag(m)} W={W}: {'+2700 fits' if fits else 'REFUSED'}; {len(boxes)} boxes", flush=True)
        meas = measure_boxes(m, wd, boxes, top)
        if fits:
            a = meas["c27_plus"]["top30_fwhm"]; b = meas["c27_minus"]["top30_fwhm"]
            rec["knob_c_outer_station"][tag(m)].update({"plus": meas["c27_plus"], "minus": meas["c27_minus"], "asym_2700": round(a - b, 3) if a is not None and b is not None else None})
        a = meas["ce_plus"]["top30_fwhm"]; b = meas["ce_minus"]["top30_fwhm"]
        rec["knob_c_prime_edge_anchored"][tag(m)].update({"plus": meas["ce_plus"], "minus": meas["ce_minus"], "asym_edge": round(a - b, 3) if a is not None and b is not None else None})
        json.dump(rec, open(OUT, "w"), indent=1)
    rec["finished_at"] = datetime.datetime.now().astimezone().isoformat(timespec="seconds")
    json.dump(rec, open(OUT, "w"), indent=1)
    print("DONE", OUT, flush=True)


if __name__ == "__main__":
    main()
