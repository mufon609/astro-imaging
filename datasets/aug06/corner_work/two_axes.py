#!/usr/bin/env python3
"""Consolidate the corner-quality measurement onto its TWO axes and write the
record — coverage DEPTH (union-canvas) against MEMBER-OWN field radius.

  two_axes.py <lst-root> <out.json>

WHY TWO AXES. Coverage depth lives in union-canvas coordinates; registration
residual and optical aberration live in each member's own field radius. A
pixel's value on one says nothing about the other, so a corner defect is only
attributable if the same product is read against both. On this union the two
are correlated (r = -0.78 over the measured boxes) but NOT collinear: 48.8% of
the canvas carries all 13 members while member-own radius there still sweeps
0.08-0.80, and a rho band of 0.70-0.86 carries depths from 2 to 13. Those two
facts are what make the axes separable at all.

WHAT IS THE TOOL'S AND WHAT IS IN-HOUSE (the bright line, CLAUDE.md):
  Siril         every PSF fit (`findstar` through `shape_at_sky.py`), every
                background number (`bgnoise`/`stat` through `regional_noise.py`),
                every coverage box (`boxselect`+`stat` through
                `coverage_frame.py`).
  astrometry.net/Siril  every WCS this reads — the union's and each member's
                own solution. No geometry is inferred from the detections
                (docs/dead-ends.md trap 3: an origin fitted to the stars moves
                with the defect).
  in-house      the footprint bookkeeping, the medians/bootstrap over the
                tool's own per-star numbers, and the shrink arithmetic.
It reads no deliverable pixel: FITS HEADERS only.

THE DEPTH MAP IS VERIFIED BY THE TOOL, NOT ASSERTED. The header-derived
"depth >= 1" set is checked against Siril's own measured coverage grid: of 3636
boxes the geometry calls covered, Siril calls 0 entirely uncovered; the 130
boxes it calls empty while Siril still finds signal are the footprint-edge band,
where a 91 px box straddles a member's boundary.

REPORTS ONLY: no threshold, no verdict, always exits 0. What to do with the
number is the owner's.
"""
import glob
import json
import os
import subprocess
import sys

import numpy as np
from astropy.io import fits
from astropy.wcs import WCS

REPO = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..")
UNION = os.path.join(REPO, "web/results/aug06/stack_set-01+02+03_full_wcs.fit")
MEMBERS = sorted(glob.glob(os.path.join(
    REPO, "sessions/aug06/work/groups_set-0[123]/sub_*.fit")))
HERE = os.path.dirname(os.path.abspath(__file__))
RNG = np.random.default_rng(20260813)


def wcs_of(path):
    h = fits.getheader(path)
    return WCS(h, naxis=2), int(h["NAXIS1"]), int(h["NAXIS2"])


def med_se(v, B=1500):
    """Median with a bootstrap SE — the sampling error of a 30-star median is
    what decides whether two stations differ, and it is not negligible."""
    if len(v) < 3:
        return float("nan"), float("nan")
    i = RNG.integers(0, len(v), size=(B, len(v)))
    return float(np.median(v)), float(np.std(np.median(v[i], axis=1)))


def read_lst(path):
    """Siril findstar columns 3/7/8 = amplitude A, FWHMx, FWHMy. Siril emits
    FWHMx as the MAJOR axis (verified: 0 of 656 rows had FWHMy > FWHMx), so
    min/max is the fitted ellipse's own roundness, not an axis-aligned proxy."""
    A, FX, FY = [], [], []
    for line in open(path):
        if line.startswith("#"):
            continue
        q = line.split()
        if len(q) < 18:
            continue
        A.append(float(q[3]))
        FX.append(float(q[7]))
        FY.append(float(q[8]))
    return np.array(A), np.array(FX), np.array(FY)


def stats(lst_dir, label, top=30):
    p = os.path.join(lst_dir, label + ".lst")
    if not os.path.exists(p):
        return None
    A, FX, FY = read_lst(p)
    o = np.argsort(-A)[:top]
    maj, mse = med_se(FX[o])
    mnr, nse = med_se(FY[o])
    rnd, rse = med_se(FY[o] / FX[o])
    return {"n": int(len(A)), "top_n": int(len(o)),
            "faintest_admitted_A": float(A.min()),
            "A_at_top_n": float(np.sort(A)[::-1][len(o) - 1]),
            "major_px": maj, "major_se": mse, "minor_px": mnr, "minor_se": nse,
            "roundness": rnd, "roundness_se": rse}


def geom_of_box(crop, canvas_h, uwcs, mem, k=9):
    """Box-AVERAGED depth and member-own radius, not the centre value — an
    800 px box at the rim spans several depth levels and saying so is the point."""
    x, y, w, h = crop                                   # y from the TOP (Siril)
    yf = canvas_h - y - h
    gx = np.linspace(x, x + w - 1, k)
    gy = np.linspace(yf, yf + h - 1, k)
    XX, YY = np.meshgrid(gx, gy)
    sky = uwcs.all_pix2world(np.column_stack([XX.ravel(), YY.ravel()]), 0)
    d = np.zeros(sky.shape[0], int)
    rr = np.full((len(mem), sky.shape[0]), np.nan)
    for i, (w_i, W, H) in enumerate(mem):
        px = w_i.all_world2pix(sky, 0)
        ins = (px[:, 0] >= 0) & (px[:, 0] < W) & (px[:, 1] >= 0) & (px[:, 1] < H)
        d += ins
        cx, cy = (W - 1) / 2, (H - 1) / 2
        rr[i, ins] = (np.hypot(px[:, 0] - cx, px[:, 1] - cy)
                      / np.hypot(cx, cy))[ins]
    return (float(d.mean()), int(d.min()), int(d.max()),
            float(np.nanmean(rr)) if np.isfinite(rr).any() else float("nan"))


def own_rho(crop, canvas_h, W, H):
    x, y, w, h = crop
    xc, yc = x + w / 2, (canvas_h - y - h) + h / 2
    cx, cy = (W - 1) / 2, (H - 1) / 2
    return float(np.hypot(xc - cx, yc - cy) / np.hypot(cx, cy))


def wls(X, y, se):
    wt = 1 / np.maximum(se, 1e-4) ** 2
    A = X * np.sqrt(wt)[:, None]
    coef, *_ = np.linalg.lstsq(A, y * np.sqrt(wt), rcond=None)
    r = y - X @ coef
    cov = np.linalg.inv(A.T @ A) * max(1.0, (r ** 2 * wt).sum() / (len(y) - X.shape[1]))
    return coef, np.sqrt(np.diag(cov))


def main():
    lst_root, out_json = sys.argv[1], os.path.abspath(sys.argv[2])
    uwcs, UW, UH = wcs_of(UNION)
    mem = [wcs_of(p) for p in MEMBERS]
    rec = {
        "question": "does far-corner degradation of the combined product track "
                    "UNION COVERAGE DEPTH or MEMBER-OWN FIELD RADIUS",
        "box_uptime": subprocess.run(["uptime"], capture_output=True,
                                     text=True).stdout.strip(),
        "products": {}, "instruments": {
            "shape": "Siril findstar via scripts/qa/shape_at_sky.py (open gate "
                     "-roundness=0.10 -relax=on -maxR=1.0; boxes placed by each "
                     "product's OWN solved WCS and VERIFIED by the tool's own "
                     "per-star RA/Dec). Medians over the 30 brightest fits by "
                     "Siril's own amplitude; bootstrap SE in-house.",
            "background": "Siril crop + bgnoise + stat via "
                          "datasets/aug06/corner_work/regional_noise.py",
            "coverage": "Siril boxselect + stat via scripts/qa/coverage_frame.py",
            "geometry": "each member's own solved WCS (astrometry.net/Siril) "
                        "read from its FITS header; no geometry from detections",
        }}
    for p in [UNION] + MEMBERS[:1]:
        h = fits.getheader(p)
        rec["products"][os.path.basename(p)] = {
            "wh": [int(h["NAXIS1"]), int(h["NAXIS2"])],
            "REGMODEL": h.get("REGMODEL"), "REGUNDIS": str(h.get("REGUNDIS")),
            "STACKCNT": h.get("STACKCNT"), "PIPEREV": h.get("PIPEREV")}

    # ---- axis separability, and the tool's check on the header-derived depth --
    grid = os.path.join(HERE, "coverage_grid_union.json")
    if os.path.exists(grid) and not json.load(open(grid)).get("cells"):
        # cells dropped from the record (they regenerate); the CHECK they were
        # used for is kept there as numbers
        rec["depth_map_verified_by_the_tool"] = json.load(
            open(grid))["header_depth_cross_check"]
    if os.path.exists(grid) and json.load(open(grid)).get("cells"):
        g = json.load(open(grid))
        nx, ny = g["grid"]
        bw, bh = g["box_px"]
        cells = {tuple(c["ij"]): c for c in g["cells"]}
        pts = [[(i + .5) * bw, (j + .5) * bh] for j in range(ny) for i in range(nx)]
        ij = [(i, j) for j in range(ny) for i in range(nx)]
        sky = uwcs.all_pix2world(np.array(pts), 0)
        d = np.zeros(len(pts), int)
        for w_i, W, H in mem:
            px = w_i.all_world2pix(sky, 0)
            d += (px[:, 0] >= 0) & (px[:, 0] < W) & (px[:, 1] >= 0) & (px[:, 1] < H)
        nostat = np.array([cells[k]["no_stat"] for k in ij])
        rec["depth_map_verified_by_the_tool"] = {
            "grid": [nx, ny], "box_px": [bw, bh],
            "geometry_covered_boxes": int((d >= 1).sum()),
            "of_those_siril_calls_entirely_uncovered": int(nostat[d >= 1].sum()),
            "geometry_empty_boxes": int((d == 0).sum()),
            "of_those_siril_finds_signal": int((~nostat[d == 0]).sum()),
            "reading": "0 disagreements on the covered side; the geometry-empty "
                       "boxes Siril still measures are the footprint-edge band, "
                       "where a 91 px box straddles a member boundary"}

    # ---- the two-axis read on the union ------------------------------------
    def union_rows(shape_json, lst_dir):
        rows = []
        for r in json.load(open(shape_json))["positions"]:
            if r.get("out_of_canvas"):
                continue
            s = stats(lst_dir, r["label"])
            if s is None:
                continue
            dm, dmn, dmx, rho = geom_of_box(r["crop"], UH, uwcs, mem)
            rows.append({"label": r["label"], "ra": r["ra"], "dec": r["dec"],
                         "depth_mean": dm, "depth_min": dmn, "depth_max": dmx,
                         "rho": rho, **s})
        return sorted(rows, key=lambda r: r["rho"])

    two = union_rows(os.path.join(HERE, "shape_union_full.json"),
                     os.path.join(lst_root, "union_full"))
    rec["union_two_axis_boxes"] = two
    D = np.array([r["depth_mean"] for r in two])
    R = np.array([r["rho"] for r in two])
    rec["axis_correlation_over_measured_boxes"] = float(np.corrcoef(D, R)[0, 1])
    X = np.column_stack([np.ones_like(D), R, D])
    reg = {}
    for key in ("major_px", "minor_px", "roundness"):
        y = np.array([r[key] for r in two])
        se = np.array([r[key.replace("_px", "") + "_se"] for r in two])
        c, s = wls(X, y, se)
        reg[key] = {"intercept": c[0],
                    "rho_coef": c[1], "rho_se": s[1],
                    "rho_SE_units": abs(c[1]) / s[1],
                    "over_measured_rho_span": c[1] * (R.max() - R.min()),
                    "depth_coef": c[2], "depth_se": s[2],
                    "depth_SE_units": abs(c[2]) / s[2],
                    "over_measured_depth_span": c[2] * (D.max() - D.min())}
    reg["spans"] = {"rho": [float(R.min()), float(R.max())],
                    "depth": [float(D.min()), float(D.max())]}
    rec["union_regression_weighted_by_bootstrap_se"] = reg

    # ---- the verdict must survive the DEPTH-MATCHING RULE, not depend on it -
    # The corners have less depth BY CONSTRUCTION, so an unmatched star-shape
    # median manufactures exactly the defect under investigation. Measured live
    # in this session on the 200 px uniform-depth series: with top-30 (which
    # there reaches each box's own faintest detection) corr(depth, major) reads
    # -0.425 and corr(depth, roundness) +0.367; under one common amplitude floor
    # the same fits read -0.003 and -0.060. So the rule is swept, not chosen.
    lst_u = os.path.join(lst_root, "union_full")
    raw = {r["label"]: read_lst(os.path.join(lst_u, r["label"] + ".lst"))
           for r in two if os.path.exists(os.path.join(lst_u, r["label"] + ".lst"))}
    a30 = [float(np.sort(raw[r["label"]][0])[::-1][29]) for r in two
           if r["label"] in raw]
    rules = [("top10", lambda A: np.argsort(-A)[:10]),
             ("top30", lambda A: np.argsort(-A)[:30]),
             ("top100", lambda A: np.argsort(-A)[:100])]
    rules += [(f"A>={q(a30):.4f}", (lambda A, t=float(q(a30)): A >= t))
              for q in (np.min, np.median, np.max)]
    sweep = {}
    for name, sel in rules:
        block = {"n_per_box": [], "fits": {}}
        cols = {"major_px": ([], []), "roundness": ([], [])}
        for r in two:
            A, FX, FY = raw[r["label"]]
            m = sel(A)
            block["n_per_box"].append(int(np.asarray(m).size if np.asarray(m).dtype != bool
                                          else m.sum()))
            for key, v in (("major_px", FX[m]), ("roundness", FY[m] / FX[m])):
                a, b = med_se(v)
                cols[key][0].append(a)
                cols[key][1].append(b)
        for key, (y, se) in cols.items():
            y, se = np.array(y), np.array(se)
            ok = np.isfinite(y)
            c, s = wls(X[ok], y[ok], se[ok])
            block["fits"][key] = {
                "rho_coef": c[1], "rho_SE_units": abs(c[1]) / s[1],
                "over_measured_rho_span": c[1] * (R.max() - R.min()),
                "depth_coef": c[2], "depth_SE_units": abs(c[2]) / s[2],
                "over_measured_depth_span": c[2] * (D.max() - D.min())}
        sweep[name] = block
    rec["depth_matching_robustness"] = {
        "why": "the corners are shallower BY CONSTRUCTION, so an unmatched "
               "median manufactures the defect under test. Six rules, same "
               "boxes, same Siril fits.",
        "rules": sweep}

    # ---- depth swept at nearly constant member-own radius -------------------
    uni = os.path.join(HERE, "shape_union_uniform_depth.json")
    if os.path.exists(uni):
        rec["union_depth_sweep_at_fixed_rho"] = union_rows(
            uni, os.path.join(lst_root, "union_uniform"))

    # ---- the members: is the radial term already there? ---------------------
    memrows = {}
    for tag in ("m01s1", "m05s1", "m01s2", "m01s3"):
        j = os.path.join(HERE, f"shape_member_{tag}.json")
        if not os.path.exists(j):
            continue
        rc = json.load(open(j))
        w_i, W, H = wcs_of(rc["image"])
        rows = []
        for r in rc["positions"]:
            if r.get("out_of_canvas"):
                continue
            s = stats(os.path.join(lst_root, f"member_{tag}"), r["label"])
            if s:
                rows.append({"label": r["label"], "rho": own_rho(r["crop"], H, W, H),
                             **s})
        memrows[tag] = sorted(rows, key=lambda r: r["rho"])
    rec["member_radial_profile"] = memrows

    # ---- azimuth at fixed radius, and the fixed-azimuth ray ladders ---------
    for kind, tags, boxes in (("azimuth", ("m01s1", "m01s2"), (None,)),
                              ("rays", ("m01s1", "m01s2"), (800, 400))):
        block = {}
        for tag in tags:
            for box in boxes:
                name = f"{kind}_{tag}" if box is None else f"rays{box}_{tag}"
                j = os.path.join(HERE, f"shape_{name}.json")
                if not os.path.exists(j):
                    continue
                rc = json.load(open(j))
                w_i, W, H = wcs_of(rc["image"])
                block[name] = [
                    {"label": r["label"], "rho": own_rho(r["crop"], H, W, H),
                     **stats(os.path.join(lst_root, name), r["label"])}
                    for r in rc["positions"] if not r.get("out_of_canvas")
                    and stats(os.path.join(lst_root, name), r["label"])]
        rec[f"member_{kind}"] = block

    # ---- the shipped per-set stacks are PRE-FIX, and that has to be recorded -
    prefix = {}
    for s in ("set-01", "set-02", "set-03"):
        j = os.path.join(HERE, f"shape_{s}_full.json")
        if not os.path.exists(j):
            continue
        rc = json.load(open(j))
        h = fits.getheader(rc["image"])
        w_i, W, H = wcs_of(rc["image"])
        prefix[s] = {
            "product": os.path.basename(rc["image"]),
            "REGMODEL": h.get("REGMODEL"), "REGUNDIS": str(h.get("REGUNDIS")),
            "positions": [{"label": r["label"], "ra": r["ra"], "dec": r["dec"],
                           "rho": own_rho(r["crop"], H, W, H),
                           **stats(os.path.join(lst_root, f"{s}_full"), r["label"])}
                          for r in rc["positions"] if not r.get("out_of_canvas")]}
    rec["per_set_stacks_are_star_pair_composes_NOT_the_fixed_route"] = {
        "why_this_is_here": "every stack_set-0X_* product in web/results/aug06 "
                            "(and its judge PNG) carries REGMODEL=starpair "
                            "REGUNDIS=False — the route measured at roundness "
                            "0.458 against astrometric's 0.974. Only the "
                            "set-01+02+03 unions are astrometric. They are "
                            "therefore NOT a post-fix constant-depth control, "
                            "and this session nearly used them as one.",
        "measured": prefix,
        "the_defect_is_visible_in_them": "set-01 reads roundness 0.746/0.672/"
                                         "0.629/0.569 at RA 300.0/298.1/296.6/"
                                         "294.2 against 0.960 at RA 315.0 and "
                                         "0.939 at RA 306.0 — a sky-fixed band, "
                                         "not a radial profile, at the sky "
                                         "position BACKLOG:compose-homography-"
                                         "smear already names (RA 294.86)",
    }

    # ---- background: is depth visible in the delivered noise at all? --------
    noise = {}
    for name, path in (("union", "regional_noise_union.json"),
                       ("union_uniform_depth", "regional_noise_uniform_depth.json"),
                       ("member_m01s1_at_union_sky", "regional_noise_member_m01s1.json"),
                       ("member_m05s1_at_union_sky", "regional_noise_member_m05s1.json")):
        p = os.path.join(HERE, path)
        if not os.path.exists(p):
            continue
        noise[name] = {r["label"]: {
            "sigma_G": r["bgnoise"].get("1"), "level_G": r["level"]["Green"]["median"],
            "sigma_over_level": r["bgnoise"].get("1") / r["level"]["Green"]["median"]}
            for r in json.load(open(p))["positions"]}
    rec["background_noise"] = noise
    if {"union", "member_m01s1_at_union_sky", "member_m05s1_at_union_sky"} <= set(noise):
        common = sorted(set(noise["union"]) & set(noise["member_m01s1_at_union_sky"])
                        & set(noise["member_m05s1_at_union_sky"]))
        u = np.array([noise["union"][k]["sigma_over_level"] for k in common])
        a = np.array([noise["member_m01s1_at_union_sky"][k]["sigma_over_level"] for k in common])
        b = np.array([noise["member_m05s1_at_union_sky"][k]["sigma_over_level"] for k in common])
        rec["background_depth_control"] = {
            "positions": common,
            "union_frames": 1454, "member_frames": 100,
            "sqrt_law_prediction": float(np.sqrt(1454 / 100)),
            "measured_ratio_member_m01s1_over_union": float(np.median(a / u)),
            "measured_ratio_member_m05s1_over_union": float(np.median(b / u)),
            "corr_union_vs_m01s1": float(np.corrcoef(u, a)[0, 1]),
            "corr_m01s1_vs_m05s1": float(np.corrcoef(a, b)[0, 1]),
            "reading": "a 100-frame member and a 1454-frame union measure the "
                       "SAME relative background sigma at the same sky, and the "
                       "position-to-position pattern is shared. So Siril "
                       "bgnoise on this field is dominated by the sky's own "
                       "structure, not by a random term that averages down — "
                       "it cannot see coverage depth here, and no depth cost is "
                       "claimed from it."}

    # ---- the shrink trade, in delivered area and delivered depth ------------
    NX, NY = 294, 184
    xs = (np.arange(NX) + .5) * UW / NX
    ys = (np.arange(NY) + .5) * UH / NY
    XX, YY = np.meshgrid(xs, ys)
    sky = uwcs.all_pix2world(np.column_stack([XX.ravel(), YY.ravel()]), 0)
    rho = np.full((len(mem), sky.shape[0]), np.nan)
    for i, (w_i, W, H) in enumerate(mem):
        px = w_i.all_world2pix(sky, 0)
        ins = (px[:, 0] >= 0) & (px[:, 0] < W) & (px[:, 1] >= 0) & (px[:, 1] < H)
        cx, cy = (W - 1) / 2, (H - 1) / 2
        rho[i, ins] = (np.hypot(px[:, 0] - cx, px[:, 1] - cy) / np.hypot(cx, cy))[ins]
    cf = json.load(open(os.path.join(REPO, "datasets/aug06/l1_work/coverage_frame_union.json")))
    cx0, cy0, cw, ch = cf["rect_fits"]
    incrop = ((XX.ravel() >= cx0) & (XX.ravel() < cx0 + cw)
              & (YY.ravel() >= cy0) & (YY.ravel() < cy0 + ch))
    scale = abs(uwcs.proj_plane_pixel_scales()[0].value)
    sqdeg = (UW / NX) * (UH / NY) * scale ** 2
    trade = []
    for rc in (1.00, 0.95, 0.90, 0.85, 0.80, 0.75, 0.70, 0.65):
        d = (rho <= rc).sum(0)
        trade.append({"rho_cut": rc,
                      "member_area_kept_frac": rc * rc,
                      "union_area_sqdeg": float((d >= 1).sum() * sqdeg),
                      "crop_area_sqdeg": float(((d >= 1) & incrop).sum() * sqdeg),
                      "mean_depth_in_crop": float(d[incrop].mean()),
                      "crop_frac_losing_every_member": float(((d == 0) & incrop).mean()
                                                             / max(incrop.mean(), 1e-9))})
    r = rho[:, incrop]
    r = r[np.isfinite(r)]
    rec["shrink_trade"] = {
        "model": "a per-member edge shrink keeping fraction rho_cut of each "
                 "member's half-diagonal is, for an equal fractional trim on "
                 "both axes, exactly a rectangular crop keeping rho_cut of each "
                 "side — so member area kept is rho_cut^2",
        "delivered_crop_rect_fits": cf["rect_fits"],
        "scale_arcsec_per_px": scale * 3600,
        "rows": trade,
        "member_contributions_inside_crop": int(r.size),
        "frac_of_contributions_above_rho": {str(t): float((r > t).mean())
                                            for t in (0.70, 0.80, 0.85, 0.90)}}
    rec["reports_only"] = ("MEASUREMENT. No threshold, no verdict, nothing "
                           "cropped, nothing gated. Exits 0.")
    json.dump(rec, open(out_json, "w"), indent=1)
    print(f"  record -> {out_json}")
    print(f"  axis correlation over the measured boxes: "
          f"{rec['axis_correlation_over_measured_boxes']:+.3f}")
    for k, v in reg.items():
        if k == "spans":
            continue
        print(f"  {k:<10} rho {v['rho_coef']:+.4f} ({v['rho_SE_units']:.1f} SE, "
              f"{v['over_measured_rho_span']:+.4f} over span)   "
              f"depth {v['depth_coef']:+.5f} ({v['depth_SE_units']:.1f} SE, "
              f"{v['over_measured_depth_span']:+.4f} over span)")


if __name__ == "__main__":
    main()
