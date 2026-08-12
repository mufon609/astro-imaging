#!/usr/bin/env python3
"""Roll the per-group flat-window arms into ONE record, against the prediction.

  pergroup_flat_report.py <out.json> --rec=<pergroup_work dir>
                          --pred=<prediction.json> [--groups=5] [--frame-w=6064]
                          [--frame-h=4040]

RECORD-KEEPING, NOT A MEASUREMENT. Every number it prints was measured by a tool
and already written to a record by scripts/qa/flat_differential.py,
flat_odd_component.py or grid_ramp.py. This only puts them beside the
PRE-REGISTERED prediction, forms the ratios the standard asks for (transfer
against the flats' own ratio over the delivered canvas, planted recovery,
discrimination against the floor, normalization absorption), and states which
predictions held. It reads no pixel and re-measures nothing.

THE SIGN, which is the trap this measurement invites. A member is `light /
flat`, so the delivered ratio armB/armA equals flat_A / flat_B = set / g_k — the
INVERSE of the flat-to-flat ratio g_k / set. The comparison window is therefore
built in the delivered orientation (set over group); comparing against g_k / set
would compare the right magnitude with the wrong sign and read as a total
failure of transfer.

THE TWO LEVELS ARE DIFFERENT QUESTIONS. Per member, the correction is the whole
flat difference. Composed, the five members are a PLAIN MEAN, so what survives is
the MEAN of the five corrections — and their SPREAD is the member-to-member
disagreement per-group flats introduce, which arm A does not have at all (one
flat for every member). Both are computed from the same five numbers, so they
cannot drift apart.

`star_edge` is imported from flat_differential_report rather than copied: the
magnitude-to-ratio conversion is the same one, and a second copy of it is how two
instruments start disagreeing by parameterisation alone.
"""
import json
import math
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from flat_differential_report import star_edge      # single-sourced conversion

CH = ("R", "G", "B")


def load(path):
    return json.load(open(path)) if os.path.exists(path) else None


def dip(rec, axis="x", c="G", geom="edge"):
    return rec["primary_pixel_ratio_field"][c][geom][f"edge_dipole_{axis}"]


def spread(med):
    """100*(max-min)/mean over the four corner medians — the registry's form."""
    q = [med[k] for k in ("TL", "TR", "BL", "BR")]
    return 100.0 * (max(q) - min(q)) / (sum(q) / 4.0)


def main(argv):
    if not argv or argv[0].startswith("--"):
        print(__doc__)
        return 2
    out_json = os.path.abspath(argv[0])
    opts = dict(a[2:].split("=", 1) for a in argv[1:] if a.startswith("--"))
    REC = os.path.abspath(opts["rec"])
    K = int(opts.get("groups", 5))
    W_frame, H_frame = float(opts.get("frame-w", 6064)), float(opts.get("frame-h", 4040))
    pred = load(opts["pred"]) if opts.get("pred") else None

    rec = {
        "what": "PER-GROUP FLATS — does narrowing the flat window from 500 "
                "frames to 100 pay, and where?",
        "uptime": subprocess.run(["uptime"], capture_output=True,
                                 text=True).stdout.strip(),
        "prediction_record": opts.get("pred"),
        "records_dir": REC,
        "sign_convention": "delivered armB/armA = flat_A/flat_B = set/g_k, the "
                           "INVERSE of the flat-to-flat ratio g_k/set. The "
                           "comparison windows are built in the delivered "
                           "orientation.",
        "flat_to_flat": {}, "members": {}, "controls": {}, "composed": {},
        "derived": {},
    }

    # ---- 1. the flats against each other (no stack involved) --------------
    floor_odd = load(f"{REC}/odd_FLOOR_g3IA_over_g3IB.json")
    floor_grid = load(f"{REC}/grid_FLOOR_g3IA_over_g3IB.json")
    rec["flat_to_flat"]["floor_group_depth"] = {
        "pair": "two flats from INTERLEAVED halves of ONE group (50 + 50)",
        "why": "both halves span the same sub-burst, so any time-evolving term "
               "cancels and only the build floor remains",
        "corner_spread_pct": round(spread(
            floor_odd["ratio"]["measured"]["corner"]["median_ADU"]), 4),
        "grid_slope_x_pct_per_1000px": floor_grid["measured"]["fit"]["slope_x_pct_per_1000px"],
        "grid_slope_y_pct_per_1000px": floor_grid["measured"]["fit"]["slope_y_pct_per_1000px"],
        "grid_range_pct": floor_grid["measured"]["fit"]["range_pct"],
    }
    for k in range(1, K + 1):
        o = load(f"{REC}/odd_g{k}_over_set.json")
        g = load(f"{REC}/grid_g{k}_over_set.json")
        if not o or not g:
            continue
        f = g["measured"]["fit"]
        rec["flat_to_flat"][f"g{k}_over_set"] = {
            "corner_spread_pct": round(spread(
                o["ratio"]["measured"]["corner"]["median_ADU"]), 4),
            "edge_dipole_x": o["ratio"]["measured"]["edge"]["edge_dipole_x"],
            "edge_dipole_y": o["ratio"]["measured"]["edge"]["edge_dipole_y"],
            "grid_slope_x_pct_per_1000px": f["slope_x_pct_per_1000px"],
            "grid_slope_y_pct_per_1000px": f["slope_y_pct_per_1000px"],
            "axis_ratio_y_over_x": f["axis_ratio_y_over_x"],
            "dominant_axis": f["dominant_axis"],
            "grid_range_pct": f["range_pct"],
            "no_clip_control_agrees": o["ratio"]["no_clip_control"]["agrees"],
        }

    # ---- 2. the delivered difference, per member -------------------------
    def pair_block(p, win=None):
        if not p:
            return None
        ap = p["confirming_star_differential"]["apertures"]
        cw, chh = float(p["arm_ref"]["canvas"][0]), float(p["arm_ref"]["canvas"][1])
        b = {
            "ref": os.path.basename(p["arm_ref"]["file"]),
            "alt": os.path.basename(p["arm_alt"]["file"]),
            "ref_flat": p["arm_ref"]["CALFLAT"], "alt_flat": p["arm_alt"]["CALFLAT"],
            "stack_norm": [p["arm_ref"]["STACKNRM"], p["arm_alt"]["STACKNRM"]],
            "regpin": p["arm_ref"]["REGPIN"],
            "canvas": p["arm_ref"]["canvas"],
            "pixel_edge_dipole_x": {c: dip(p, "x", c) for c in CH},
            "pixel_edge_dipole_y": {c: dip(p, "y", c) for c in CH},
            "no_clip_control_agrees": {
                c: p["primary_pixel_ratio_field"][c]["no_clip_control_agrees"]
                for c in CH},
            "star": {},
        }
        for r, f in ap.items():
            if "error" in f:
                b["star"][r] = {"error": f["error"]}
                continue
            b["star"][r] = {
                "delivered_frac_x": f["delivered_frac_x"],
                "delivered_frac_x_err": f["delivered_frac_x_err"],
                "delivered_frac_y": f["delivered_frac_y"],
                "equivalent_edge_dipole_x":
                    star_edge(f["ax"], cw)["equivalent_edge_dipole_x"],
                "equivalent_edge_dipole_y":
                    star_edge(f["ay"], chh)["equivalent_edge_dipole_y"],
                "n_stars": f["n_stars"], "sigma_x": f["sigma_x"],
                "lever_px_x": f["lever_px_x"], "lever_px_y": f["lever_px_y"],
                "chi2_per_dof": f["chi2_per_dof"],
                "centroid_agreement_px": f["centroid_agreement_px"],
            }
        if win:
            e = win["self"]["edge"]
            b["expected_from_flats_over_the_delivered_canvas"] = {
                "edge_dipole_x": e["edge_dipole_x"],
                "edge_dipole_y": e["edge_dipole_y"],
                "source": "the two flats' own ratio (set / group), Siril fdiv, "
                          "cropped to this member's delivered canvas and measured "
                          "with the SAME instrument",
            }
            for ax in ("x", "y"):
                exp = e[f"edge_dipole_{ax}"]
                got = b[f"pixel_edge_dipole_{ax}"]["G"]
                b[f"transfer_{ax}_pixel"] = (got / exp) if exp else None
        return b

    for k in range(1, K + 1):
        p = load(f"{REC}/delivered_member_g{k}.json")
        win = load(f"{REC}/flatratio_window_g{k}.json")
        blk = pair_block(p, win)
        if blk:
            rec["members"][f"g{k}"] = blk

    for role, fn in (("identity", "control_identity"),
                     ("uniform", "control_uniform"),
                     ("planted", "control_planted"),
                     ("prodnorm", "control_prodnorm")):
        blk = pair_block(load(f"{REC}/delivered_{fn}.json"))
        if blk:
            rec["controls"][role] = blk
    card = load(f"{REC}/cards.json")
    if card:
        rec["controls"]["card_definitions"] = card

    for role, fn in (("measured", "composed"), ("identity", "composed_identity")):
        blk = pair_block(load(f"{REC}/delivered_{fn}.json"))
        if blk:
            rec["composed"][role] = blk

    # ---- 3. per-member background ramp, both arms ------------------------
    ramps = {}
    for arm in ("armA", "armB"):
        for k in range(1, K + 1):
            r = load(f"{REC}/memberramp_{arm}_g{k}.json")
            if r:
                ramps.setdefault(arm, {})[f"g{k}"] = {
                    "slope_x_pct_per_1000px": r["measured"]["fit"]["slope_x_pct_per_1000px"],
                    "slope_y_pct_per_1000px": r["measured"]["fit"]["slope_y_pct_per_1000px"],
                    "range_pct": r["measured"]["fit"]["range_pct"]}
    if ramps:
        rec["member_background_ramp_green"] = {
            "by_arm": ramps,
            "READ_THIS_FIRST": "the registry calls stack background flatness "
                               "SELF-FULFILLING for flat contamination — a stack "
                               "reads flat precisely BECAUSE the flat absorbed "
                               "the gradient. Recorded as the size of the "
                               "mechanism, NEVER as evidence of a better "
                               "calibration."}
        for arm, byg in ramps.items():
            for ax in ("x", "y"):
                v = [byg[g][f"slope_{ax}_pct_per_1000px"] for g in sorted(byg)]
                rec["member_background_ramp_green"].setdefault("summary", {})[
                    f"{arm}_slope_{ax}_mean"] = sum(v) / len(v)
                rec["member_background_ramp_green"]["summary"][
                    f"{arm}_slope_{ax}_spread"] = max(v) - min(v)

    # ---- 4. the two levels, from the same five numbers -------------------
    d = rec["derived"]
    for ax in ("x", "y"):
        vals = [rec["members"][f"g{k}"][f"pixel_edge_dipole_{ax}"]["G"]
                for k in range(1, K + 1) if f"g{k}" in rec["members"]]
        if len(vals) != K:
            continue
        mean = sum(vals) / K
        d[f"member_delivered_dipole_{ax}"] = {
            "per_group": vals,
            "mean": mean,
            "mean_abs": sum(abs(v) for v in vals) / K,
            "spread_max_minus_min": max(vals) - min(vals),
            "reading": "the MEAN is what a plain-mean compose can carry; the "
                       "SPREAD is the member-to-member disagreement per-group "
                       "flats introduce, which arm A does not have at all "
                       "(one flat for every member).",
        }
        comp = rec["composed"].get("measured")
        if comp:
            got = comp[f"pixel_edge_dipole_{ax}"]["G"]
            d[f"composed_vs_member_{ax}"] = {
                "composed_measured": got,
                "predicted_from_the_mean_of_the_five": mean,
                "mean_abs_member": d[f"member_delivered_dipole_{ax}"]["mean_abs"],
                "composed_over_mean_abs_member":
                    got / d[f"member_delivered_dipole_{ax}"]["mean_abs"]
                    if d[f"member_delivered_dipole_{ax}"]["mean_abs"] else None,
            }

    # discrimination against the floor, in the form the standard asks for
    idn = rec["controls"].get("identity")
    pl = rec["controls"].get("planted")
    if idn and pl:
        fl = max(abs(idn["pixel_edge_dipole_x"][c]) for c in CH)
        fly = max(abs(idn["pixel_edge_dipole_y"][c]) for c in CH)
        d["discrimination"] = {
            "identity_floor_max_abs_dipole_x": fl,
            "identity_floor_max_abs_dipole_y": fly,
            "planted_moved_dipole_x": pl["pixel_edge_dipole_x"]["G"],
            "ratio": (abs(pl["pixel_edge_dipole_x"]["G"]) / fl) if fl else None,
            "reading": "a floor of EXACTLY zero makes the ratio unbounded, so "
                       "the honest statement is then the floor's exact value and "
                       "how many measured quantities sit at it.",
        }
        if pl.get("expected_from_flats_over_the_delivered_canvas"):
            d["discrimination"]["planted_recovery"] = pl.get("transfer_x_pixel")
    un = rec["controls"].get("uniform")
    if un:
        d["uniform_card_control"] = {
            "dipole_x": {c: un["pixel_edge_dipole_x"][c] for c in CH},
            "dipole_y": {c: un["pixel_edge_dipole_y"][c] for c in CH},
            "reading": "every pixel differs by 5%, the GRADIENT does not: every "
                       "dipole must stay at the identity floor. This is what "
                       "makes the identity floor non-vacuous.",
        }
    pn = rec["controls"].get("prodnorm")
    if pn and "g1" in rec["members"]:
        a = rec["members"]["g1"]["pixel_edge_dipole_x"]["G"]
        b = pn["pixel_edge_dipole_x"]["G"]
        d["production_normalization_absorption"] = {
            "nonorm_dipole_x": a, "prodnorm_dipole_x": b,
            "ratio_prodnorm_over_nonorm": (b / a) if a else None,
            "star_nonorm_delivered_frac_x":
                rec["members"]["g1"]["star"].get("10.0", {}).get("delivered_frac_x"),
            "star_prodnorm_delivered_frac_x":
                pn["star"].get("10.0", {}).get("delivered_frac_x"),
            "reading": "the shipped clause is measured to absorb 0.3-0.4% of a "
                       "calibration difference on the OBJECT while moving the "
                       "BACKGROUND pixel field ~48.6% (a pedestal artefact — "
                       "psf's local annulus is immune, regional medians are "
                       "not). The pixel field is valid on -nonorm arms only.",
        }
    if pred:
        rec["prediction_committed_before_the_arms"] = pred.get("prediction")

    os.makedirs(os.path.dirname(out_json), exist_ok=True)
    with open(out_json, "w") as f:
        json.dump(rec, f, indent=1)

    # ---------------------------------------------------------------- print
    print("FLAT-TO-FLAT (no stack involved)")
    fl = rec["flat_to_flat"]["floor_group_depth"]
    print(f"  FLOOR at the group's own depth: corner spread {fl['corner_spread_pct']:.4f}%  "
          f"grid range {fl['grid_range_pct']:.4f}%  "
          f"slope y {fl['grid_slope_y_pct_per_1000px']:+.4f} %/1000px")
    print(f"  {'pair':<12} {'spread%':>8} {'slope_x':>9} {'slope_y':>9} {'|y/x|':>6} "
          f"{'xfloor':>7}")
    for k in range(1, K + 1):
        b = rec["flat_to_flat"].get(f"g{k}_over_set")
        if not b:
            continue
        print(f"  g{k}/set      {b['corner_spread_pct']:8.4f} "
              f"{b['grid_slope_x_pct_per_1000px']:+9.4f} "
              f"{b['grid_slope_y_pct_per_1000px']:+9.4f} "
              f"{b['axis_ratio_y_over_x']:6.2f} "
              f"{b['corner_spread_pct']/fl['corner_spread_pct']:6.1f}x")

    print("\nDELIVERED, per member (Siril fdiv+stat green; star = Siril psf)")
    print(f"  {'member':<8} {'dip_x':>8} {'dip_y':>8} | {'exp_x':>8} {'exp_y':>8} | "
          f"{'T_x':>6} {'T_y':>6} | {'star dx%':>9} {'n':>5}")
    for k in range(1, K + 1):
        b = rec["members"].get(f"g{k}")
        if not b:
            continue
        e = b.get("expected_from_flats_over_the_delivered_canvas", {})
        s = b["star"].get("10.0", {})
        tx = b.get("transfer_x_pixel")
        ty = b.get("transfer_y_pixel")
        print(f"  g{k}       {b['pixel_edge_dipole_x']['G']:+8.4f} "
              f"{b['pixel_edge_dipole_y']['G']:+8.4f} | "
              f"{e.get('edge_dipole_x', float('nan')):+8.4f} "
              f"{e.get('edge_dipole_y', float('nan')):+8.4f} | "
              f"{(tx if tx is not None else float('nan')):6.2f} "
              f"{(ty if ty is not None else float('nan')):6.2f} | "
              f"{100*s.get('delivered_frac_x', float('nan')):+9.3f} "
              f"{s.get('n_stars', 0):5d}")
    for ax in ("x", "y"):
        m = rec["derived"].get(f"member_delivered_dipole_{ax}")
        if m:
            print(f"  {ax}: mean {m['mean']:+.4f}   mean|.| {m['mean_abs']:.4f}   "
                  f"spread {m['spread_max_minus_min']:.4f}")
        c = rec["derived"].get(f"composed_vs_member_{ax}")
        if c:
            print(f"  {ax}: COMPOSED {c['composed_measured']:+.4f}  = "
                  f"{c['composed_over_mean_abs_member']:+.3f} x the mean member "
                  f"magnitude (predicted from the mean of the five: "
                  f"{c['predicted_from_the_mean_of_the_five']:+.4f})")

    print("\nCONTROLS")
    for role in ("identity", "uniform", "planted", "prodnorm"):
        b = rec["controls"].get(role)
        if not b:
            continue
        s = b["star"].get("10.0", {})
        print(f"  {role:<9} dip_x {b['pixel_edge_dipole_x']['G']:+.4f}  "
              f"dip_y {b['pixel_edge_dipole_y']['G']:+.4f}  "
              f"star dx {100*s.get('delivered_frac_x', float('nan')):+.3f}%  "
              f"n={s.get('n_stars', 0)}")
    ci = rec["composed"].get("identity")
    if ci:
        print(f"  composed-identity dip_x {ci['pixel_edge_dipole_x']['G']:+.4f}  "
              f"dip_y {ci['pixel_edge_dipole_y']['G']:+.4f}")
    print(f"\nrecord: {out_json}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
