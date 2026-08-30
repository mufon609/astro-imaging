#!/usr/bin/env python3
"""toprow_corner_coverage.py — WHICH MEMBERS' ROWS FEED THE CANONICAL'S BOTTOM CORNER
BOXES, and what a row-level exclusion would leave there. RECORDS-ONLY: header + record
reads (astropy WCS, both sides SIP), no pixel opened, no product, no build-path file.
Record: toprow_corner_coverage.json beside this file (ledger id toprow_corner_coverage).

METHOD. For each of the 77 members a 100-px sample grid over the member's KEPT extent
(a cropped copy keeps round(W/2 + x_c) columns) is projected member WCS -> sky -> the
canonical _wcs.fit -> canvas; a canvas box is the 800-px square centred on its sky
position (the four bottom corner boxes from cropT_arm.json's rows; the 22 rowmin probe
boxes rebuilt at the six rowmin members' +1200/+1800/+2400 station centres on their
top / bottom rows, exactly as that arm placed them). A member COVERS a box when any of
its sample points lands inside; its LANDING BAND is the median member y of those points.
Y CONVENTION (the trap docs/dead-ends/verification-traps.md records): astropy works in
FITS pixel rows (y up), Siril's crop boxes count y DOWN — the profiled "top row" (Siril
y 0..800) is FITS y >= H - 800, and that is what "top strip" means everywhere here.

ESTIMATOR (with its positive control): the box's FWHM ~ the STACKCNT-weighted mean over
the covering members of the member's own profiled top-30 FWHM at the station nearest the
landing point — the top-row profile (toprow_profiles.json) for a top-strip landing, the
cache's centre-row profile for a centre-band landing, the nearer of the two otherwise
(flagged). CONTROL: on the CURRENT set it must reproduce the canonical's measured corner
values within 0.10 px, or the U5 prediction it yields is not usable.

U5: the 29 members over S_top p25 + 0.20 lose their top 800 rows -> coverage and the
estimate recomputed from what remains. DILUTION (rowmin): at each probe the six rowmin
members' REMOVED-column share of the weighted coverage.
"""
import datetime, json, os, re, statistics, sys, warnings
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
warnings.filterwarnings("ignore")
from astropy.io import fits
from astropy.wcs import WCS

STAGE = os.path.join(REPO, "datasets/corpus/member_selection/july31+aug06+aug09+aug14_full_portion.json")
CACHE = os.path.join(REPO, "datasets/corpus/member_selection/profiles.json")
TOPROW = os.path.join(HERE, "toprow_profiles.json")
CROPT = os.path.join(HERE, "cropT_arm.json")
ROWMIN = os.path.join(HERE, "rowmin_arm.json")
WNOISE = os.path.join(HERE, "weight_noise_arm.json")
CANON = os.path.join(REPO, "web/results/aug14/stack_july31+aug06+aug09+aug14_full_wcs.fit")
OUT = os.path.join(HERE, "toprow_corner_coverage.json")
CORNERS = ["corner_700_4200", "corner_1300_4900", "corner_7000_4900", "corner_7500_4400"]
STEP, HALF, TOPSTRIP = 100, 400, 800
ROWMIN_XC = {"aug14/set-04/sub_01": 900, "aug14/set-04/sub_04": 900, "aug14/set-05/sub_01": 900, "aug14/set-05/sub_02": 900,
             "aug09/set-05/sub_02": 900, "aug09/set-05/sub_01": 1500}


def tag(m):
    p = m.replace("\\", "/").split("/")
    return f"{p[-4]}/{p[-2].replace('groups_', '')}/{p[-1][:-4]}"


def main():
    stage = json.load(open(STAGE)); cache = json.load(open(CACHE))["members"]
    top = json.load(open(TOPROW)); crop = json.load(open(CROPT))["measurement"]["rows"]
    canon_vals = {k: v["canonical"] for k, v in json.load(open(WNOISE))["collateral_table_wnoise_minus_canonical"].items()}
    over29 = {k for k, _ in top["outcomes"]["P4_S_top"]["members_over_p25_plus_bar"]}
    hc = fits.getheader(CANON); wc = WCS(hc, naxis=2)
    canvas_wh = [hc["NAXIS1"], hc["NAXIS2"]]
    members = sorted(stage["table"].values(), key=lambda r: r["index"])

    # ---- per member: WCS, kept extent, grid + station centres projected to the canvas
    proj = {}
    for row in members:
        m = os.path.realpath(row["member"]); t = tag(m); ent = cache[m]; W, H = ent["wh"]
        Wk = int(round(W / 2.0 + row["x_c"])) if row["cropped"] else W
        wm = WCS(fits.getheader(m), naxis=2)
        xs = np.arange(50, Wk, STEP); ys = np.arange(50, H, STEP)
        gx, gy = np.meshgrid(xs, ys); gx = gx.ravel(); gy = gy.ravel()
        ra, dec = wm.all_pix2world(gx, gy, 0)
        cx, cy = wc.all_world2pix(ra, dec, 0)
        st_top = {n: s for n, s in top["members"][t]["top_row"]["stations"].items()}
        st_cen = {s["name"]: s for s in ent["stations"] if "skipped" not in s}
        def centres(stations, yrow):
            names = list(stations); bx = np.array([stations[n]["box"][0] + HALF for n in names], float); by = np.full(len(names), yrow, float)
            r_, d_ = wm.all_pix2world(bx, by, 0); px, py = wc.all_world2pix(r_, d_, 0)
            return {n: {"member_xy": [float(bx[i]), float(by[i])], "canvas_xy": [round(float(px[i]), 1), round(float(py[i]), 1)]} for i, n in enumerate(names)}
        proj[t] = {"member": m, "wh": [W, H], "kept_width": Wk, "cropped": row["cropped"], "stackcnt": ent.get("stackcnt") or int(fits.getheader(m).get("STACKCNT", 0)),
                   "night": t.split("/")[0], "night_set": "/".join(t.split("/")[:2]), "over_bar": t in over29,
                   "gx": gx, "gy": gy, "cx": cx, "cy": cy, "wcs": wm,
                   "top_stations": centres(st_top, H - 1 - HALF), "centre_stations": centres(st_cen, H / 2.0),
                   "top_fwhm": {n: s["top30_fwhm"] for n, s in st_top.items()}, "cen_fwhm": {n: s.get("top30_fwhm") for n, s in st_cen.items()}}
        print(f"[{row['index']:2d}/77] {t}: kept {Wk}x{H}, {len(gx)} grid points -> canvas x {cx.min():.0f}..{cx.max():.0f}", flush=True)

    # ---- the boxes: four corners (sky -> canvas) + 22 rowmin probes (station centres of the six members)
    boxes = {}
    for k in CORNERS:
        px, py = wc.all_world2pix(crop[k]["ra"], crop[k]["dec"], 0)
        boxes[k] = {"kind": "corner", "ra": crop[k]["ra"], "dec": crop[k]["dec"], "canvas_centre": [round(float(px), 1), round(float(py), 1)], "measured_canonical": canon_vals[k]}
    rm = json.load(open(ROWMIN))["collateral_table_rowmin_minus_canonical"]
    for k, v in rm.items():
        mm = re.match(r"probe_(\w+)_(set-\d+)_(sub_\d+)_(top|bot)_\+(\d+)", k)
        if not mm:
            continue
        t = f"{mm.group(1)}/{mm.group(2)}/{mm.group(3)}"; rowname = mm.group(4); dx = int(mm.group(5))
        p = proj[t]; W, H = p["wh"]; name = f"along+{dx}"
        sx = p["top_stations"][name]["member_xy"][0]; sy = (H - 1 - HALF) if rowname == "top" else HALF   # Siril top row = FITS y near H
        r_, d_ = p["wcs"].all_pix2world(np.array([sx]), np.array([sy]), 0); px, py = wc.all_world2pix(r_, d_, 0)
        boxes[k] = {"kind": "probe", "of_member": t, "row": rowname, "station": name, "member_xy": [sx, sy],
                    "canvas_centre": [round(float(px[0]), 1), round(float(py[0]), 1)], "measured_canonical": v["canonical"], "rowmin_arm": v["rowmin"]}

    # ---- coverage + estimator
    def local_fwhm(p, mx, my):
        H = p["wh"][1]
        if my >= H - TOPSTRIP:            # the profiled TOP row (Siril y 0..800 = FITS y >= H-800)
            band = "top"; sts, fw = p["top_stations"], p["top_fwhm"]
        elif abs(my - H / 2.0) <= HALF:
            band = "centre"; sts, fw = p["centre_stations"], p["cen_fwhm"]
        else:
            band = "other_top_nearest" if my > H / 2.0 else "other_centre_nearest"
            sts, fw = (p["top_stations"], p["top_fwhm"]) if my > H / 2.0 else (p["centre_stations"], p["cen_fwhm"])
        n = min(sts, key=lambda nm: abs(sts[nm]["member_xy"][0] - mx))
        return band, n, fw.get(n)

    results = {}
    for k, b in boxes.items():
        bx, by = b["canvas_centre"]
        cov = {}
        for t, p in proj.items():
            inside = (np.abs(p["cx"] - bx) < HALF) & (np.abs(p["cy"] - by) < HALF)
            n_in = int(inside.sum())
            if not n_in:
                continue
            my_ = p["gy"][inside]; mx_ = p["gx"][inside]
            n_top = int((my_ >= p["wh"][1] - TOPSTRIP).sum())
            mx, my = float(np.median(mx_)), float(np.median(my_))
            band, stn, f = local_fwhm(p, mx, my)
            e = {"night": p["night"], "night_set": p["night_set"], "over_bar": p["over_bar"], "stackcnt": p["stackcnt"], "n_points": n_in, "n_points_top_strip": n_top,
                 "landing_member_xy_median": [round(mx), round(my)], "band": band, "station": stn, "fwhm_local": f}
            # after the U5 exclusion: the 29 lose their top strip
            if p["over_bar"]:
                rest = inside & (p["gy"] < p["wh"][1] - TOPSTRIP)
                if rest.sum():
                    mx2, my2 = float(np.median(p["gx"][rest])), float(np.median(p["gy"][rest]))
                    band2, stn2, f2 = local_fwhm(p, mx2, my2)
                    e["after"] = {"covers": True, "n_points": int(rest.sum()), "band": band2, "station": stn2, "fwhm_local": f2}
                else:
                    e["after"] = {"covers": False}
            else:
                e["after"] = {"covers": True, "n_points": n_in, "band": band, "station": stn, "fwhm_local": f}
            # rowmin dilution: the six members' REMOVED columns (x >= rowmin kept width)
            if t in ROWMIN_XC:
                kept_rm = int(round(p["wh"][0] / 2.0 + ROWMIN_XC[t]))
                e["rowmin_removed_points"] = int((inside & (p["gx"] >= kept_rm)).sum())
            cov[t] = e
        def est(sel):
            ws = [(cov[t]["stackcnt"], (cov[t]["after"]["fwhm_local"] if sel == "after" else cov[t]["fwhm_local"])) for t in cov
                  if (cov[t]["after"]["covers"] if sel == "after" else True)]
            ws = [(w, f) for w, f in ws if f is not None]
            return (round(sum(w * f for w, f in ws) / sum(w for w, _ in ws), 3) if ws else None), (round(statistics.mean(f for _, f in ws), 3) if ws else None), len(ws)
        e_now, u_now, n_now = est("now"); e_aft, u_aft, n_aft = est("after")
        by_night = lambda sel: {n: sum(1 for t in cov if cov[t]["night"] == n and (cov[t]["after"]["covers"] if sel == "after" else True)) for n in ("july31", "aug06", "aug09", "aug14")}
        tot_w = sum(cov[t]["stackcnt"] * cov[t]["n_points"] for t in cov)
        rm_w = sum(cov[t]["stackcnt"] * cov[t].get("rowmin_removed_points", 0) for t in cov)
        results[k] = {**b, "coverers_before": len(cov), "coverers_after_U5": sum(1 for t in cov if cov[t]["after"]["covers"]),
                      "by_night_before": by_night("now"), "by_night_after_U5": by_night("after"),
                      "over_bar_coverers": sum(1 for t in cov if cov[t]["over_bar"]), "top_strip_only_coverers": sum(1 for t in cov if cov[t]["n_points_top_strip"] == cov[t]["n_points"]),
                      "bands_before": {b_: sum(1 for t in cov if cov[t]["band"] == b_) for b_ in ("top", "centre", "other_top_nearest", "other_centre_nearest")},
                      "estimate_now": {"stackcnt_weighted": e_now, "unweighted": u_now, "n": n_now, "measured": b["measured_canonical"][0],
                                       "delta": round(e_now - b["measured_canonical"][0], 3) if e_now is not None else None},
                      "estimate_after_U5": {"stackcnt_weighted": e_aft, "unweighted": u_aft, "n": n_aft},
                      "rowmin_removed_share_of_weighted_coverage": round(rm_w / tot_w, 4) if tot_w else None,
                      "members": cov}
        print(f"{k:38s} coverers {len(cov):2d} -> {results[k]['coverers_after_U5']:2d}  by night {results[k]['by_night_before']} -> {results[k]['by_night_after_U5']}  est {e_now} (meas {b['measured_canonical'][0]}) -> {e_aft}", flush=True)

    control = {k: results[k]["estimate_now"]["delta"] for k in CORNERS}
    held = all(abs(d) <= 0.10 for d in control.values())
    gate = json.load(open(os.path.join(REPO, "web/results/aug14/compose_gate_stack_july31+aug06+aug09+aug14_full.json")))
    rec = {"_what": __doc__.strip(), "started_at": None, "canvas_wh": canvas_wh, "grid_step_px": STEP, "box_half_px": HALF, "top_strip_px": TOPSTRIP,
           "over_bar_members_29": sorted(over29), "rowmin_members_kept_width_x_c": ROWMIN_XC,
           "estimator_control": {"criterion": "|estimate_now - measured| <= 0.10 px at the four bottom corner boxes", "deltas": control, "held": held},
           "compose_gate_record": {"path": "web/results/aug14/compose_gate_stack_july31+aug06+aug09+aug14_full.json", "size_B": os.path.getsize(os.path.join(REPO, "web/results/aug14/compose_gate_stack_july31+aug06+aug09+aug14_full.json")),
                                   "keys": list(gate.keys()), "carries": "per-member dims (member_dims), per-member detected star counts (detected), per-member optics stamps (optics), and PAIRWISE cross-match separations by member-own radius zone (pairs, %d pairs; worst; unmeasured_pairs) — the member-separation instrument's output" % len(gate["pairs"]),
                                   "cannot_answer": "it holds NO per-member canvas placement, homography or coverage: the separations are computed in the reference member's frame through register -2pass homographies that are not stored in the record (instrument text), so which members cover which canvas box is not derivable from it — the WCS pin above is the only source for that; the record can say which member PAIRS disagree most where they overlap (its 'worst' pair s_00052|s_00069 at 11.4 px in the mid zone), not where on the canvas"},
           "boxes": results, "written_at": datetime.datetime.now().astimezone().isoformat(timespec="seconds")}
    json.dump(rec, open(OUT, "w"), indent=1)
    print("estimator control:", control, "HELD" if held else "FAILED")
    print("DONE", OUT)


if __name__ == "__main__":
    main()
