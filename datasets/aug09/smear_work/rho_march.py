"""rho_march — attribute the union's surviving one-sided band to member-own
sampling composition, or fail to (pre-registered: rho_march_prereg.json,
committed BEFORE this ran; the reading rules there are frozen).

    python3 rho_march.py            # writes rho_march.json beside itself

MEASURES ONLY. Reads FITS *headers* (astropy WCS) and already-recorded tool
measurements (smear_remarch.json + its findstar lists) — no pixel is read,
nothing is gated, always exits 0 on a completed run (STOP conditions exit 3).

Every star position, FWHMx/FWHMy and amplitude is Siril findstar's, recorded
by the re-march; every member geometry is the member's own solved WCS
(astrometry.net via solve_field.py). In-house is only the projection
bookkeeping and the least squares — the same standing as `member_separation.py`
and `shape_at_sky.py`, and the same gap: no official tool attributes star shape
on a coadd to the contributing members' own field positions.

REMOVAL CONDITION: an official tool reports, headless, coadd star-shape
statistics attributed by contributing-member field position (a per-member
shape decomposition on a union), or neither `compose-homography-smear` nor
`one-sided-band` still consumes a member-attribution quantity.
"""
import json
import math
import os
import sys

import numpy as np
from astropy.io import fits
from astropy.wcs import WCS
import warnings
warnings.filterwarnings("ignore")

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
GATE = os.path.join(REPO, "web/results/aug09/compose_gate_stack_july31+aug06+aug09_full.json")
REMARCH = os.path.join(HERE, "smear_remarch.json")
LISTS = os.path.join(HERE, "lists")
OUT = os.path.join(HERE, "rho_march.json")

PAIRS = [(5, 95), (10, 90), (15, 85), (20, 80), (25, 75),
         (30, 70), (35, 65), (40, 60), (45, 55)]


def enumerate_members():
    """The frozen rule: groups_set-0N sub-stacks, no _l1*/_rev2; multiset must
    equal the gate record's CALSET multiset (STOP condition)."""
    import glob
    from collections import Counter
    files, disk = [], Counter()
    for sess in ("july31", "aug06", "aug09"):
        for p in sorted(glob.glob(os.path.join(REPO, f"sessions/{sess}/work/groups_set-0*/sub_*.fit"))):
            d = os.path.basename(os.path.dirname(p))
            if "_l1" in d or "_rev2" in d:
                continue
            disk[f"{sess}/{d.replace('groups_', '')}"] += 1
            files.append(p)
    gate = json.load(open(GATE))
    want = Counter(v["CALSET"] for v in gate["optics"].values())
    if dict(disk) != dict(want):
        print(f"STOP: enumeration mismatch disk={dict(disk)} gate={dict(want)}")
        sys.exit(3)
    return files


def member_geometry(files):
    """Header-only: dims, linear WCS, rotation angle. Orientation control per
    prereg AMENDMENT 1: roll is a per-SET aim fact (ballhead re-aim), so the
    check is WITHIN-set spread < 2 deg; the between-set spread is reported as
    measured geometry, not a stop."""
    mems = []
    for p in files:
        h = fits.getheader(p)
        w = WCS(h, naxis=2)
        cd = w.pixel_scale_matrix
        rot = math.degrees(math.atan2(cd[1, 0], cd[0, 0]))
        parts = os.path.normpath(p).split(os.sep)
        setid = f"{parts[-4]}/{parts[-2]}"  # <session>/groups_set-0N
        mems.append({"path": p, "W": h["NAXIS1"], "H": h["NAXIS2"],
                     "wcs": w, "rot_deg": rot, "set": setid})
    bysets = {}
    for m in mems:
        ra, dec = m["wcs"].wcs_pix2world([[m["W"] / 2, m["H"] / 2]], 0)[0]
        bysets.setdefault(m["set"], []).append((m["rot_deg"], ra, dec))
    set_rows = {}
    for s, rows in bysets.items():
        rots = [r[0] for r in rows]
        ras = [r[1] for r in rows]
        dec = sum(r[2] for r in rows) / len(rows)
        meas = max(rots) - min(rots)
        pred = (max(ras) - min(ras)) * math.sin(math.radians(dec))
        set_rows[s] = {"rot_spread_deg": round(meas, 3),
                       "meridian_convergence_pred_deg": round(pred, 3)}
        # AMENDMENT 2: the bound is mechanism-derived (north converges with the
        # meridians at ~dRA*sin(dec) across a fixed camera's sweep); it exists
        # to catch flip/axis-swap-class solve defects, which sit far outside it.
        if meas > pred + 1.5:
            print(f"STOP: within-set rotation spread {meas:.3f} deg in {s} exceeds "
                  f"meridian-convergence bound {pred:.3f}+1.5 — solve/geometry bug")
            sys.exit(3)
    rots = np.array([m["rot_deg"] for m in mems])
    spread = float(rots.max() - rots.min())
    return mems, spread, set_rows


def sip_tolerance(mems, stars_radec):
    """Median |all_world2pix - wcs_world2pix| on >=100 stars x 3 members (one
    per night). If > 20 px the run switches to all_world2pix (prereg)."""
    sample = stars_radec[:120]
    picks = [mems[0], mems[20], mems[35]]  # july31 / aug06 / aug09 territory
    deltas = []
    for m in picks:
        lin = np.array(m["wcs"].wcs_world2pix(sample, 0))
        try:
            full = np.array(m["wcs"].all_world2pix(sample, 0, maxiter=30,
                                                   tolerance=1e-4, quiet=True))
        except Exception:
            continue
        deltas.append(np.hypot(*(lin - full).T))
    med = float(np.median(np.concatenate(deltas))) if deltas else float("nan")
    return med, med > 20.0


def project(mems, radec, use_full):
    """radec (n,2) -> per star: n_cover, mean member-own signed_x, mean rho."""
    n = len(radec)
    cover = np.zeros(n, int)
    sx_sum = np.zeros(n)
    rho_sum = np.zeros(n)
    for m in mems:
        if use_full:
            xy = np.array(m["wcs"].all_world2pix(radec, 0, maxiter=30,
                                                 tolerance=1e-4, quiet=True))
        else:
            xy = np.array(m["wcs"].wcs_world2pix(radec, 0))
        x, y = xy[:, 0], xy[:, 1]
        inf = (x >= 0) & (x < m["W"]) & (y >= 0) & (y < m["H"])
        hw, hh = m["W"] / 2.0, m["H"] / 2.0
        sx = (x - hw) / hw
        rho = np.hypot(x - hw, y - hh) / hh
        cover += inf
        sx_sum += np.where(inf, sx, 0.0)
        rho_sum += np.where(inf, rho, 0.0)
    ok = cover > 0
    mean_sx = np.where(ok, sx_sum / np.maximum(cover, 1), np.nan)
    mean_rho = np.where(ok, rho_sum / np.maximum(cover, 1), np.nan)
    return cover, mean_sx, mean_rho


def read_list(label, top_n):
    """Top-N stars by amplitude A from a re-march findstar list (the
    instrument's own selection rule: 'the 30 brightest fits')."""
    rows = []
    with open(os.path.join(LISTS, f"{label}.lst")) as fh:
        for ln in fh:
            if ln.startswith("#"):
                continue
            c = ln.split()
            if len(c) < 18:
                continue
            rows.append((float(c[3]), float(c[7]), float(c[8]),
                         float(c[16]), float(c[17])))
    rows.sort(key=lambda r: -r[0])
    rows = rows[:top_n]
    out = []
    for a, fx, fy, ra, dec in rows:
        out.append({"A": a, "major": max(fx, fy), "minor": min(fx, fy),
                    "round": (min(fx, fy) / max(fx, fy)) if max(fx, fy) > 0 else np.nan,
                    "ra": ra, "dec": dec})
    return out


def pair_key(label):
    if not label.startswith("x"):
        return None
    return int(label[1:3])


def analyse(top_n, positions, mems, use_full):
    """One full pass at a selection depth. Returns (per_box, pair_rows, t4)."""
    per_box, star_pool = {}, []
    for p in positions:
        lab = p["label"]
        stars = read_list(lab, top_n)
        radec = np.array([[s["ra"], s["dec"]] for s in stars])
        cover, msx, mrho = project(mems, radec, use_full)
        if int((cover > 0).sum()) == 0:
            print(f"STOP: position {lab} covered by zero members — geometry bug")
            sys.exit(3)
        for i, s in enumerate(stars):
            s.update({"n_cover": int(cover[i]), "mean_sx": float(msx[i]),
                      "mean_rho": float(mrho[i]), "box": lab})
        star_pool.extend(stars)
        per_box[lab] = {
            "n_stars": len(stars),
            "median_major": float(np.median([s["major"] for s in stars])),
            "median_round": float(np.median([s["round"] for s in stars])),
            "mean_n_cover": float(np.mean(cover)),
            "mean_member_sx": float(np.nanmean(msx)),
            "mean_member_rho": float(np.nanmean(mrho)),
        }
    # pair deltas (left - mirror)
    bykey = {}
    for p in positions:
        k = pair_key(p["label"])
        if k is not None:
            bykey[k] = per_box[p["label"]]
    pair_rows = []
    for l, r in PAIRS:
        L, R = bykey[l], bykey[r]
        pair_rows.append({
            "pair": f"x{l:02d}/x{r:02d}",
            "d_major": L["median_major"] - R["median_major"],
            "d_round": L["median_round"] - R["median_round"],
            "d_rho": L["mean_member_rho"] - R["mean_member_rho"],
            "d_sx": L["mean_member_sx"] - R["mean_member_sx"],
            "d_cover": L["mean_n_cover"] - R["mean_n_cover"],
        })
    # T4: composition-only OLS on banded-box stars, dedup by exact (ra,dec)
    banded = [s for s in star_pool if pair_key(s["box"]) is not None
              and np.isfinite(s["mean_sx"])]
    seen, uniq = set(), []
    for s in banded:
        key = (s["ra"], s["dec"])
        if key in seen:
            continue
        seen.add(key)
        uniq.append(s)
    X = np.array([[1.0, s["mean_rho"], s["mean_sx"], s["n_cover"]] for s in uniq])
    t4 = {}
    for q in ("major", "round"):
        y = np.array([s[q] for s in uniq])
        beta, *_ = np.linalg.lstsq(X, y, rcond=None)
        resid = y - X @ beta
        rbox = {}
        for s, r in zip(uniq, resid):
            rbox.setdefault(pair_key(s["box"]), []).append(r)
        diffs = np.array([np.mean(rbox[l]) - np.mean(rbox[r]) for l, r in PAIRS])
        mean, se = float(diffs.mean()), float(diffs.std(ddof=1) / math.sqrt(len(diffs)))
        rng = np.random.default_rng(20260822)
        null = [abs(np.mean(diffs * rng.choice([-1, 1], size=len(diffs))))
                for _ in range(500)]
        t4[q] = {"beta_[1,rho,sx,cover]": [float(b) for b in beta],
                 "pair_resid_diffs": [float(d) for d in diffs],
                 "mean_resid_diff": mean, "se_over_pairs": se,
                 "mean_over_se": (mean / se) if se > 0 else float("nan"),
                 "perm_null_p": float(np.mean(np.array(null) >= abs(mean))),
                 "n_stars_pooled": len(uniq)}
    return per_box, pair_rows, t4


def main():
    remarch = json.load(open(REMARCH))
    positions = remarch["positions"]
    files = enumerate_members()
    mems, rot_spread, set_rows = member_geometry(files)
    probe_stars = read_list(positions[0]["label"], 200)
    radec0 = np.array([[s["ra"], s["dec"]] for s in probe_stars])
    sip_med, use_full = sip_tolerance(mems, radec0)

    out = {"_what": "member-own composition attribution of the surviving one-sided band. "
                    "MEASURES ONLY; prereg: rho_march_prereg.json (committed before the run).",
           "subject": remarch["image"],
           "members": len(mems), "member_rot_spread_deg": rot_spread,
           "per_set_rotation": set_rows,
           "sip_linear_vs_full_median_px": sip_med,
           "projection_used": "all_world2pix" if use_full else "wcs_world2pix"}
    for depth, tag in ((30, "primary_top30"), (100, "secondary_top100")):
        per_box, pair_rows, t4 = analyse(depth, positions, mems, use_full)
        out[tag] = {"per_box": per_box, "pairs": pair_rows, "T4": t4}
    with open(OUT, "w") as fh:
        json.dump(out, fh, indent=1)
    # console: the load-bearing table at primary depth
    P = out["primary_top30"]
    print(f"members {len(mems)}  rot_spread {rot_spread:.4f} deg  "
          f"SIP lin-vs-full median {sip_med:.3f} px  -> {out['projection_used']}")
    print(f"{'pair':10} {'d_major':>8} {'d_round':>8} {'d_rho':>8} {'d_sx':>8} {'d_cover':>8}")
    for r in P["pairs"]:
        print(f"{r['pair']:10} {r['d_major']:>8.3f} {r['d_round']:>8.3f} "
              f"{r['d_rho']:>8.4f} {r['d_sx']:>8.4f} {r['d_cover']:>8.2f}")
    for q in ("major", "round"):
        t = P["T4"][q]
        print(f"T4 {q}: composition-unexplained pair residual "
              f"{t['mean_resid_diff']:+.4f} ± {t['se_over_pairs']:.4f} "
              f"({t['mean_over_se']:+.1f} SE, perm p={t['perm_null_p']:.3f}, "
              f"n={t['n_stars_pooled']})")
    print(f"wrote {OUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
