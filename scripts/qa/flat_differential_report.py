#!/usr/bin/env python3
"""Roll the flat-differential arm pairs into ONE record, against the prediction.

  flat_differential_report.py <out.json> --pred=<prediction.json>
        --flat-ratio=<flat_odd_component record> [--frame-w=6064] [--card=<cards.json>]
        <role>=<pair record>...

  roles: measurement | floor_identity | floor_uniform | planted | prodnorm

RECORD-KEEPING, NOT A MEASUREMENT. Every number it prints was measured by a tool
and already written to a pair record by scripts/qa/flat_differential.py; this
script only puts them beside the PRE-REGISTERED prediction, forms the ratios the
standard asks for (smear factor, planted recovery, discrimination against the
floor, normalization absorption), and states which predictions held. It reads no
pixel and re-measures nothing.

THE SMEAR FACTOR, and why it is a prediction rather than a fudge. Each canvas
point is the flux-weighted average of the sensor-fixed ratio field over the
sensor positions that sky point visited during the drift. For a LINEAR field the
average is the value at the MEAN position, so the amplitude per pixel survives
intact — what shrinks is the BASELINE, because `-framing=min` crops the canvas
to the intersection of all the frames' footprints. Hence

    factor = (W_canvas - 84) / (W_frame - 84)

the separation of the edge boxes' centres (box 80, margin 2) on the canvas over
the same separation on the full frame. The canvas is measured independently of
the ratio, so this is not a free parameter.

DISCRIMINATION AGAINST THE FLOOR is reported in the form the registry asks for:
how far the planted card moves the answer against what the instrument reports
when the truth is zero (the iterative-flat NULL met 48-62x; the object-tilt
instrument managed 0.20x and was unusable). A floor of EXACTLY zero makes the
ratio unbounded, so the honest statement is then the floor's exact value and how
many measured quantities sit at it.
"""
import json
import math
import os
import subprocess
import sys

ROLES = ("measurement", "floor_identity", "floor_uniform", "planted", "prodnorm")
CH = ("R", "G", "B")


def star_edge(ax, W, box=80, margin=2):
    """The star fit's slope expressed at the PIXEL instrument's own geometry.

    The fit is magnitudes across the full canvas (u in [-0.5, +0.5]); the pixel
    instrument reads medians in boxes whose centres sit at x = margin+box/2 and
    x = W - margin - box/2. Converting makes the two comparable without moving
    either one's number.

    THE COMMON CURRENCY IS THE RATIO, NOT THE DIPOLE, and the difference is not
    cosmetic: the star fit is linear in MAGNITUDES, so its field is exponential
    in position, while the pixel field's dipole is linear in FLUX. Over a 22%
    excursion the two parameterisations disagree by ~4 points on the dipole while
    agreeing on the edge-to-edge ratio — comparing dipole-to-dipole would
    manufacture an instrument disagreement out of the model choice alone. The
    ratio `right/left` is what both instruments measure directly: for the pixel
    field it is 1/LR, straight from Siril's medians.
    """
    c = margin + box / 2.0
    uL, uR = c / W - 0.5, (W - c) / W - 0.5
    fL, fR = 10 ** (-0.4 * ax * uL), 10 ** (-0.4 * ax * uR)
    return {"right_over_left": fR / fL,
            "equivalent_edge_dipole_x": (fR - fL) / ((fR + fL) / 2.0)}


def main(argv):
    pos = [a for a in argv if "=" not in a or a.split("=", 1)[0] in ROLES]
    if not argv or argv[0].startswith("--"):
        print(__doc__)
        return 2
    out_json = os.path.abspath(argv[0])
    opts = dict(a[2:].split("=", 1) for a in argv[1:] if a.startswith("--"))
    pairs = {}
    for a in argv[1:]:
        if a.startswith("--") or "=" not in a:
            continue
        role, path = a.split("=", 1)
        if role not in ROLES:
            print(f"unknown role {role} (want one of {', '.join(ROLES)})", file=sys.stderr)
            return 2
        pairs[role] = json.load(open(path))
        pairs[role]["_path"] = path
    if "measurement" not in pairs:
        print("need measurement=<pair record>", file=sys.stderr)
        return 2

    W_frame = float(opts.get("frame-w", 6064))
    pred = json.load(open(opts["pred"])) if opts.get("pred") else {}
    fr = json.load(open(opts["flat-ratio"]))["ratio"]["measured"] if opts.get("flat-ratio") else None
    card = json.load(open(opts["card"])) if opts.get("card") else None

    def dip(rec, c="G", geom="edge"):
        return rec["primary_pixel_ratio_field"][c][geom]["edge_dipole_x"]

    def dipy(rec, c="G", geom="edge"):
        return rec["primary_pixel_ratio_field"][c][geom]["edge_dipole_y"]

    meas = pairs["measurement"]
    W_canvas = float(meas["arm_ref"]["canvas"][0])
    factor = (W_canvas - 84.0) / (W_frame - 84.0)

    rec = {
        "what": "FLAT DIFFERENTIAL — how much of two flats' dose difference "
                "reaches the delivered object",
        "uptime": subprocess.run(["uptime"], capture_output=True,
                                 text=True).stdout.strip(),
        "prediction_record": opts.get("pred"),
        "canvas": meas["arm_ref"]["canvas"],
        "frame_width_px": W_frame,
        "smear_factor_geometric": round(factor, 4),
        "smear_factor_formula": "(W_canvas - 84) / (W_frame - 84) — the edge "
                                "boxes' centre separation on the canvas over the "
                                "same separation on the frame",
        "flat_ratio_input": ({"edge_dipole_x": fr["edge"]["edge_dipole_x"],
                              "edge_dipole_y": fr["edge"]["edge_dipole_y"],
                              "LR": fr["edge"]["LR"],
                              "record": opts.get("flat-ratio")} if fr else None),
        "arms": {},
        "derived": {},
    }

    # --- per pair: the delivered field, both instruments -----------------
    for role, p in pairs.items():
        ap = p["confirming_star_differential"]["apertures"]
        rec["arms"][role] = {
            "label": p["label"],
            "ref": os.path.basename(p["arm_ref"]["file"]),
            "alt": os.path.basename(p["arm_alt"]["file"]),
            "ref_flat": p["arm_ref"]["CALFLAT"], "alt_flat": p["arm_alt"]["CALFLAT"],
            "stack_norm": [p["arm_ref"]["STACKNRM"], p["arm_alt"]["STACKNRM"]],
            "canvas": p["arm_ref"]["canvas"],
            "pixel_ratio_edge_dipole_x": {c: dip(p, c) for c in CH},
            "pixel_ratio_edge_dipole_y": {c: dipy(p, c) for c in CH},
            "pixel_ratio_LR": {c: p["primary_pixel_ratio_field"][c]["edge"]["LR"] for c in CH},
            "no_clip_control_agrees": {c: p["primary_pixel_ratio_field"][c]["no_clip_control_agrees"] for c in CH},
            "star_differential": {
                r: ({"error": f["error"]} if "error" in f else {
                    "ax_mag": f["ax"], "ax_err": f["ax_err"],
                    "delivered_frac_x": f["delivered_frac_x"],
                    "delivered_frac_x_err": f["delivered_frac_x_err"],
                    "equivalent_edge_dipole_x": star_edge(f["ax"], float(p["arm_ref"]["canvas"][0]))["equivalent_edge_dipole_x"],
                    "right_over_left": star_edge(f["ax"], float(p["arm_ref"]["canvas"][0]))["right_over_left"],
                    "n_stars": f["n_stars"], "sigma_x": f["sigma_x"],
                    "lever_px_x": f["lever_px_x"],
                    "chi2_per_dof": f["chi2_per_dof"],
                    "resid_rms_mag": f["resid_rms_mag"],
                    "centroid_agreement_px": f["centroid_agreement_px"]})
                for r, f in ap.items()},
            "record": p["_path"],
        }

    d = rec["derived"]
    mg = dip(meas)

    # --- the floor -------------------------------------------------------
    floors = {}
    for role in ("floor_identity", "floor_uniform"):
        if role in pairs:
            floors[role] = {
                "pixel_max_abs_dipole_x": max(abs(dip(pairs[role], c)) for c in CH),
                "pixel_max_abs_dipole_y": max(abs(dipy(pairs[role], c)) for c in CH),
                "star_max_abs_delivered_frac_x": max(
                    abs(f["delivered_frac_x"])
                    for f in pairs[role]["confirming_star_differential"]["apertures"].values()
                    if "error" not in f),
            }
    if floors:
        fl = max(v["pixel_max_abs_dipole_x"] for v in floors.values())
        d["floor"] = {
            "per_control": floors,
            "pixel_floor_abs_dipole_x": fl,
            "reading": "the largest |edge dipole x| any control reports where the "
                       "truth is exactly zero. A floor of 0.0000 is a TRUE zero, "
                       "not a small number — this chain is bit-reproducible.",
        }

    # --- the measurement against the prediction --------------------------
    if fr:
        fd = fr["edge"]["edge_dipole_x"]
        d["delivered_vs_flats"] = {
            "flat_ratio_edge_dipole_x": fd,
            "delivered_edge_dipole_x_green": mg,
            "fraction_of_the_flats_dose_delivered": round(mg / fd, 4),
            "predicted_by_geometry": round(factor, 4),
            "departure_from_prediction_pct": round(100 * (mg / fd / factor - 1), 2),
            "upper_bound_respected": abs(mg) <= abs(fd),
            "reading": "the delivered field is the flats' ratio smeared by the "
                       "drift, so the fraction cannot exceed 1 and should sit at "
                       "the geometric factor if the field is linear.",
        }

    # --- the APPLES-TO-APPLES comparison ---------------------------------
    # The geometric factor above assumes the delivered field is the flats' ratio
    # with the canvas's shorter baseline and nothing else. The exact form of that
    # prediction is to CROP the flats' own ratio to the canvas and measure it with
    # the same instrument — no model at all. The planted card, cropped the same
    # way, then measures what this whole comparison chain does to a KNOWN input,
    # which is the systematic to quote the real number against.
    win = json.load(open(opts["window"]))["self"] if opts.get("window") else None
    cardwin = json.load(open(opts["card-window"]))["self"] if opts.get("card-window") else None
    if win:
        d["delivered_vs_flats_same_window"] = {
            "flat_ratio_cropped_to_the_canvas": {
                "edge_dipole_x": win["edge"]["edge_dipole_x"],
                "corner_dipole_x": win["corner"]["edge_dipole_x"],
                "edge_LR": win["edge"]["LR"], "corner_LR": win["corner"]["LR"],
                "record": opts["window"]},
            "delivered_green": {
                "edge_dipole_x": mg,
                "corner_dipole_x": dip(meas, "G", "corner"),
                "edge_LR": meas["primary_pixel_ratio_field"]["G"]["edge"]["LR"],
                "corner_LR": meas["primary_pixel_ratio_field"]["G"]["corner"]["LR"]},
            "delivered_over_window_edge": round(mg / win["edge"]["edge_dipole_x"], 4),
            "delivered_over_window_corner": round(
                dip(meas, "G", "corner") / win["corner"]["edge_dipole_x"], 4),
            "caveat": "the crop is CENTRED on the frame and the flats' ratio is "
                      "un-warped, while the delivered field has been through the "
                      "lens-distortion warp and sits at the drift-averaged window. "
                      "Both effects are percent-level and BOTH apply to the planted "
                      "card too, which is why the card's recovery is the systematic "
                      "to read this against.",
        }
        if cardwin and "planted" in pairs:
            rec_card = dip(pairs["planted"]) / cardwin["edge"]["edge_dipole_x"]
            d["delivered_vs_flats_same_window"]["planted_recovery_same_window"] = round(rec_card, 4)
            d["delivered_vs_flats_same_window"]["delivered_fraction_corrected_by_the_control"] = round(
                (mg / win["edge"]["edge_dipole_x"]) / rec_card, 4)

    # --- the planted card ------------------------------------------------
    if "planted" in pairs and card:
        pl = dip(pairs["planted"])
        cd = card["ramp"]["edge_dipole_x_at_box80_margin2"]
        d["planted"] = {
            "card_edge_dipole_x": cd,
            "card_edge_ratio": card["ramp"]["edge_ratio_full_frame"],
            "predicted_delivered": round(cd * factor, 4),
            "measured_delivered_green": pl,
            "recovery": round(pl / (cd * factor), 4),
            "sign_opposite_to_the_real_signal": (pl > 0) != (mg > 0),
        }
        if floors:
            fl = d["floor"]["pixel_floor_abs_dipole_x"]
            d["planted"]["discrimination_against_floor"] = (
                None if fl == 0 else round(abs(pl) / fl, 2))
            d["planted"]["discrimination_reading"] = (
                "the floor is EXACTLY zero, so the ratio is unbounded — the "
                "planted card moves the answer by "
                f"{abs(pl):.4f} against a floor of 0.0000. Compare: the "
                "iterative-flat NULL met 48-62x, the object-tilt instrument "
                "0.20x." if fl == 0 else
                "planted movement over the floor; the iterative-flat NULL met "
                "48-62x and the object-tilt instrument 0.20x on this standard.")

    # --- the uniform card: level moves, gradient must not -----------------
    if "floor_uniform" in pairs:
        u = pairs["floor_uniform"]
        med = u["primary_pixel_ratio_field"]["G"]["edge"]["median_ADU"]
        d["uniform_card"] = {
            "region_medians_of_the_ratio_field": med,
            "max_abs_dipole_x": max(abs(dip(u, c)) for c in CH),
            "reading": "every pixel differs by the card's scalar and no dipole "
                       "may move. This is what makes the identity floor "
                       "non-vacuous: the card path itself is exercised.",
        }

    # --- what the shipped normalization absorbs ---------------------------
    if "prodnorm" in pairs:
        pn = dip(pairs["prodnorm"])
        sa = meas["confirming_star_differential"]["apertures"]
        sp = pairs["prodnorm"]["confirming_star_differential"]["apertures"]
        star = {r: {"nonorm": sa[r]["delivered_frac_x"],
                    "prodnorm": sp[r]["delivered_frac_x"],
                    "absorbed_fraction": round(
                        1 - abs(sp[r]["delivered_frac_x"]) / abs(sa[r]["delivered_frac_x"]), 4)}
                for r in sa if r in sp and "error" not in sa[r] and "error" not in sp[r]}
        d["normalization_absorption"] = {
            "the_question": "how much of a calibration difference does the shipped "
                            "-norm=addscale -output_norm swallow before it reaches "
                            "the deliverable?",
            "ON_THE_OBJECT_star_flux": star,
            "ON_THE_BACKGROUND_pixel_field": {
                "nonorm_edge_dipole_x_green": mg,
                "production_norm_edge_dipole_x_green": pn,
                "change_fraction": round(abs(pn) / abs(mg) - 1, 4) if mg else None,
                "per_channel": {c: {"nonorm": dip(meas, c),
                                    "prodnorm": dip(pairs["prodnorm"], c)} for c in CH},
            },
            "reading": "THE TWO ANSWERS DIFFER AND THE DIFFERENCE IS THE FINDING. "
                       "The star flux is measured against psf's LOCAL annulus, so it "
                       "is immune to an additive pedestal; the regional medians are "
                       "not. -norm=addscale gives every frame its own additive AND "
                       "multiplicative coefficient computed from that frame's own "
                       "statistics — and in the counterfactual arm those statistics "
                       "shift with the drift, because the frame's own window slides "
                       "across the imprint. So the background field acquires a "
                       "position-dependent pedestal that is NOT imprint, while the "
                       "object's flux ratio barely moves. Read the object number as "
                       "the absorption; read the background number as a pedestal "
                       "artefact and take the pixel field on -nonorm arms only.",
        }

    # --- do the two instruments agree? -----------------------------------
    ap = meas["confirming_star_differential"]["apertures"]
    pix_rl = 1.0 / meas["primary_pixel_ratio_field"]["G"]["edge"]["LR"]
    agree = {}
    for r, f in ap.items():
        if "error" in f:
            continue
        st = star_edge(f["ax"], W_canvas)
        agree[r] = {
            "star_right_over_left": round(st["right_over_left"], 5),
            "pixel_right_over_left_green": round(pix_rl, 5),
            "difference_pct_of_pixel": round(
                100 * (st["right_over_left"] - pix_rl) / pix_rl, 3),
            "star_equivalent_edge_dipole_x": round(st["equivalent_edge_dipole_x"], 4),
            "pixel_edge_dipole_x_green": round(mg, 4),
        }
    d["instrument_agreement"] = {
        "compared_on": "the edge-to-edge RATIO right/left at the pixel "
                       "instrument's own box centres — the only currency both "
                       "instruments measure directly (1/LR for the pixel field). "
                       "Dipole-to-dipole would compare a flux-linear number with "
                       "a magnitude-linear one and manufacture a disagreement.",
        "per_aperture": agree,
        "reading": "the two instruments measure the same delivered field by "
                   "independent routes — Siril's regional medians on the SKY "
                   "background, and Siril's aperture photometry on the STARS' own "
                   "flux against a local annulus. A disagreement is the finding "
                   "and is attributed, never averaged.",
        "aperture_invariance": (
            {"r10_minus_r16_frac_x": round(
                ap["10"]["delivered_frac_x"] - ap["16"]["delivered_frac_x"], 5)}
            if "10" in ap and "16" in ap and "error" not in ap["10"]
            and "error" not in ap["16"] else None),
    }

    if pred:
        rec["prediction_committed_before_the_arms"] = pred.get("prediction")

    os.makedirs(os.path.dirname(out_json), exist_ok=True)
    open(out_json, "w").write(json.dumps(rec, indent=1) + "\n")

    print(f"canvas {rec['canvas'][0]}x{rec['canvas'][1]}  geometric smear factor "
          f"{factor:.4f}")
    for role in ROLES:
        if role not in rec["arms"]:
            continue
        a = rec["arms"][role]
        st = a["star_differential"].get("10", {})
        print(f"  {role:<15} pixel dipole_x R/G/B "
              + " ".join(f"{a['pixel_ratio_edge_dipole_x'][c]:+.4f}" for c in CH)
              + (f"   star {100*st['delivered_frac_x']:+.2f}%" if "delivered_frac_x" in st else ""))
    if "delivered_vs_flats" in d:
        v = d["delivered_vs_flats"]
        print(f"  delivered / flats' ratio = {v['fraction_of_the_flats_dose_delivered']:.4f} "
              f"against a geometric {v['predicted_by_geometry']:.4f} "
              f"({v['departure_from_prediction_pct']:+.2f}%)")
    if "planted" in d:
        print(f"  planted recovery {d['planted']['recovery']:.4f}  "
              f"discrimination {d['planted'].get('discrimination_against_floor')}")
    if "normalization_absorption" in d:
        na = d["normalization_absorption"]
        s10 = na["ON_THE_OBJECT_star_flux"].get("10", {})
        print(f"  normalization absorbs {100*s10.get('absorbed_fraction', 0):+.2f}% of the "
              f"OBJECT's difference, while the BACKGROUND field moves "
              f"{100*na['ON_THE_BACKGROUND_pixel_field']['change_fraction']:+.1f}% "
              "(pedestal artefact — see the record)")
    print(f"record: {out_json}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
