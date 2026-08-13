#!/usr/bin/env python3
"""What a per-member shrink at compose input is PREDICTED to deliver — from the
members' own measured profiles, not from a model of the optics.

  shrink_prediction.py <corner_quality.json> <out.json>

A shrink does not change any member's star shape; it changes WHICH members
contribute at each sky position. So the delivered shape under a shrink is
predictable from two things this session already measured with Siril: each
member's own shape profile across its own frame, and (from the members' WCS)
which members reach each union position and at what own-frame coordinate. This
computes that, for a RADIAL cut and for a ONE-SIDED +x cut, because the two
quantities the corners lose behave differently — star SIZE is radial, star
ROUNDNESS is one-sided.

IT IS A PREDICTION AND IS LABELLED ONE. The only thing that settles it is the
one-knob A/B (build the union with and without the trim, same members, same
compose args, judged on shape_at_sky at the same sky). Nothing here builds it:
adopting an area-for-quality trade is the owner's call under the evidence gate,
and this measures so they can make it.

Validation available without that build: the same construction predicts TODAY's
union from TODAY's members, and that comparison IS in the output
(`prediction_vs_measured_today`) — a consistency check on the construction, not
independent evidence, since it reuses the same measurements.

Every shape number is Siril `findstar`'s (through `shape_at_sky.py`); every
footprint is a member's own solved WCS. In-house: the interpolation and the
averaging. Reads no pixel. REPORTS ONLY, exits 0.
"""
import glob
import json
import os
import sys

import numpy as np
from astropy.io import fits
from astropy.wcs import WCS

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.join(HERE, "..", "..", "..")
UNION = os.path.join(REPO, "web/results/aug06/stack_set-01+02+03_full_wcs.fit")
MEMBERS = sorted(glob.glob(os.path.join(
    REPO, "sessions/aug06/work/groups_set-0[123]/sub_*.fit")))


def member_stations(rec):
    """Every member station this session measured, with its own-frame position."""
    out = []
    blocks = [(k, v) for k, v in rec["member_rays"].items()]
    blocks += [(k, v) for k, v in rec["member_azimuth"].items()]
    blocks += [(f"member_{t}", v) for t, v in rec["member_radial_profile"].items()]
    for name, rows in blocks:
        j = os.path.join(HERE, f"shape_{name}.json")
        if not os.path.exists(j):
            continue
        rc = json.load(open(j))
        h = fits.getheader(rc["image"])
        W, H = int(h["NAXIS1"]), int(h["NAXIS2"])
        by = {r["label"]: r for r in rows}
        for r in rc["positions"]:
            if r.get("out_of_canvas") or r["label"] not in by:
                continue
            x, y, w, hh = r["crop"]                      # y from the TOP (Siril)
            xc, yc = x + w / 2, (H - y - hh) + hh / 2
            out.append({"xf": (xc - (W - 1) / 2) / (W / 2),
                        "yf": (yc - (H - 1) / 2) / (H / 2),
                        "rho": float(np.hypot(xc - (W - 1) / 2, yc - (H - 1) / 2)
                                     / np.hypot((W - 1) / 2, (H - 1) / 2)),
                        "major": by[r["label"]]["major_px"],
                        "roundness": by[r["label"]]["roundness"]})
    return out


def binned(x, y, edges, minn=3):
    c, v = [], []
    for a, b in zip(edges[:-1], edges[1:]):
        m = (x >= a) & (x < b)
        if m.sum() >= minn:
            c.append((a + b) / 2)
            v.append(float(np.median(y[m])))
    return np.array(c), np.array(v)


def main():
    rec = json.load(open(sys.argv[1]))
    out_json = os.path.abspath(sys.argv[2])
    st = member_stations(rec)
    xf = np.array([s["xf"] for s in st])
    rho = np.array([s["rho"] for s in st])
    rnd = np.array([s["roundness"] for s in st])
    maj = np.array([s["major"] for s in st])

    xc, xr = binned(xf, rnd, np.array([-1.01, -.8, -.6, -.4, -.2, 0, .2, .4, .6, .8, 1.01]))
    rc_, rm = binned(rho, maj, np.array([0, .15, .25, .35, .45, .55, .65, .75, .85, 1.01]))

    uh = fits.getheader(UNION)
    UH = int(uh["NAXIS2"])
    uwcs = WCS(uh, naxis=2)
    mem = []
    for p in MEMBERS:
        h = fits.getheader(p)
        mem.append((WCS(h, naxis=2), int(h["NAXIS1"]), int(h["NAXIS2"])))

    two = {r["label"]: r for r in rec["union_two_axis_boxes"]}
    boxes = []
    for r in json.load(open(os.path.join(HERE, "shape_union_full.json")))["positions"]:
        if r.get("out_of_canvas"):
            continue
        x, y, w, h = r["crop"]
        yf = UH - y - h
        gx = np.linspace(x, x + w - 1, 9)
        gy = np.linspace(yf, yf + h - 1, 9)
        XX, YY = np.meshgrid(gx, gy)
        sky = uwcs.all_pix2world(np.column_stack([XX.ravel(), YY.ravel()]), 0)
        px_f, rho_f = [], []
        for w_i, W, H in mem:
            px = w_i.all_world2pix(sky, 0)
            ins = ((px[:, 0] >= 0) & (px[:, 0] < W)
                   & (px[:, 1] >= 0) & (px[:, 1] < H))
            if not ins.any():
                continue
            px_f.append(float(np.mean(((px[:, 0] - (W - 1) / 2) / (W / 2))[ins])))
            rho_f.append(float(np.mean((np.hypot(px[:, 0] - (W - 1) / 2,
                                                 px[:, 1] - (H - 1) / 2)
                                        / np.hypot((W - 1) / 2, (H - 1) / 2))[ins])))
        boxes.append({"label": r["label"], "xf": np.array(px_f),
                      "rho": np.array(rho_f),
                      "roundness": two[r["label"]]["roundness"],
                      "major": two[r["label"]]["major_px"]})

    pr = np.array([np.interp(b["xf"], xc, xr).mean() for b in boxes])
    pm = np.array([np.interp(b["rho"], rc_, rm).mean() for b in boxes])
    mr = np.array([b["roundness"] for b in boxes])
    mm = np.array([b["major"] for b in boxes])
    off_r, off_m = float(np.median(mr - pr)), float(np.median(mm - pm))

    def sweep(key, cut_on, cuts, prof_x, prof_y, off):
        rows = []
        for c in cuts:
            allv, corners = [], []
            for b in boxes:
                q = b[cut_on][b[cut_on] <= c] if cut_on == "xf" else b["rho"][b["rho"] <= c]
                if q.size == 0:
                    continue
                v = float(np.interp(q, prof_x, prof_y).mean() + off)
                allv.append(v)
                if b["label"].startswith("crop") and b["label"] != "cropC":
                    corners.append(v)
            rows.append({"cut": c,
                         "member_area_kept": min(1.0, (c + 1) / 2 if cut_on == "xf" else c * c),
                         "predicted_mean": float(np.mean(allv)),
                         "predicted_at_the_4_crop_corners": float(np.mean(corners)) if corners else None,
                         "predicted_worst_box": float(np.min(allv)) if key == "roundness" else float(np.max(allv)),
                         "boxes_losing_every_member": int(len(boxes) - len(allv))})
        return rows

    rec_out = {
        "what_this_is": "a PREDICTION of what a per-member shrink delivers, "
                        "built from the members' own measured profiles. Only a "
                        "one-knob A/B settles it.",
        "member_stations_used": len(st),
        "profiles_from_the_tool": {
            "roundness_by_member_frame_x": {"x_frac": xc.tolist(), "median": xr.tolist()},
            "major_px_by_member_own_radius": {"rho": rc_.tolist(), "median": rm.tolist()}},
        "prediction_vs_measured_today": {
            "roundness_corr": float(np.corrcoef(pr, mr)[0, 1]),
            "roundness_median_offset": off_r,
            "major_corr": float(np.corrcoef(pm, mm)[0, 1]),
            "major_median_offset": off_m,
            "caveat": "same measurements on both sides — a consistency check on "
                      "the construction, not independent evidence"},
        "one_sided_plus_x_trim": sweep("roundness", "xf", [1.01, .9, .8, .7, .6, .5],
                                       xc, xr, off_r),
        "radial_shrink_on_star_size": sweep("major", "rho", [1.01, .9, .85, .8, .75, .7],
                                            rc_, rm, off_m),
        "reports_only": "no threshold, no verdict, nothing built. Exits 0."}
    json.dump(rec_out, open(out_json, "w"), indent=1)
    print(f"  record -> {out_json}")
    print(f"  roundness prediction vs today's union: r={rec_out['prediction_vs_measured_today']['roundness_corr']:+.3f}, "
          f"offset {off_r:+.4f}")
    for nm, key in (("+x trim keep x_frac<=", "one_sided_plus_x_trim"),
                    ("radial  keep rho<=   ", "radial_shrink_on_star_size")):
        for r in rec_out[key]:
            c = r["predicted_at_the_4_crop_corners"]
            print(f"  {nm}{r['cut']:.2f}  member area {100*r['member_area_kept']:5.1f}%  "
                  f"predicted mean {r['predicted_mean']:.3f}  corners "
                  + (f"{c:.3f}" if c is not None else "  n/a")
                  + f"  worst {r['predicted_worst_box']:.3f}"
                  + (f"  ({r['boxes_losing_every_member']} boxes lose every member)"
                     if r["boxes_losing_every_member"] else ""))


if __name__ == "__main__":
    main()
