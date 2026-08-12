#!/usr/bin/env python3
"""Measure the flatless route's OBJECT TILT catalogue-free, from the drift.

  object_tilt.py <groups-dir> [--aperture=10,16] [--inner=20] [--outer=30]
                 [--amin=0.005] [--tol-arcsec=34] [--margin=40] [--layer=1]
                 [--json=OUT] [--label=NAME] [--work=DIR] [--keep]
  object_tilt.py --selftest

THE DEFECT. A sky flat converges to `(mean sky) x V`. Horizon-fixed sky
structure cannot drift out of a median of un-registered lights, so it bakes
into the flat, and dividing by it leaves the OBJECT carrying a multiplicative
residual `g(sensor) ~ 1/sky` it never had. Backgrounds then look flat BY
CONSTRUCTION, so the corner-vs-centre check is self-fulfilling for exactly this
defect, and star shapes are untouched. The harm is photometric.

THE PRINCIPLE — separability, used diagnostically. `g` is fixed in SENSOR
coordinates; the star field is fixed on the SKY; the untracked drift decouples
them. Every star is measured at several sensor positions within one set, and
all of those measurements were calibrated by the SAME per-set flat, so `g` is
common to them. Correct calibration makes a star's measured flux independent of
where on the sensor it landed. This is the survey lineage's PHOTOMETRIC
SELF-CALIBRATION / STAR FLAT (SDSS ubercal, Padmanabhan et al. 2008; PS1 forward
global calibration, Schlafly et al. 2012; SNLS/DES star flats, Regnault et al.
2009) with the dither pattern supplied for free by not tracking.

THE MODEL, fitted by weighted least squares over one set's sub-stacks:

    m_ij = M_i + z_j + ax*u_ij + ay*v_ij

  m_ij  Siril aperture magnitude of star i in block j
  M_i   the star's own magnitude          (nuisance, eliminated analytically)
  z_j   the block's zero point            (nuisance, dummy per block)
  u,v   sensor position, frame-normalised to [-0.5, +0.5]
  ax    THE MEASUREMENT: magnitudes across the frame's width, along x

`ax` reported as a fractional throughput tilt, g(right)/g(left) - 1.

WHAT IDENTIFIES `ax`, AND THE TRAP UNDER IT — measured, not assumed. If the
block-to-block mapping were a PURE TRANSLATION, u_ij = u_i + c_j, then

    ax*u_ij = (ax*u_i) + (ax*c_j)

and the two halves are absorbed EXACTLY by M_i and z_j: the linear mode of the
flat is then formally unidentifiable, whatever the drift's size. This is the
known low-order degeneracy of self-calibration under translational dithers, and
it means the 503-1220 px of drift is NOT the lever. The lever is the drift's
DEPARTURE from a pure translation, which here is the FIELD ROTATION an
untracked camera gets for free: measured 2.4 deg over aug09/set-01 and 3.4 deg
over july31/set-01, which spreads the same-star displacement by 182 and 269 px
ACROSS the field. The fit reports that lever (`lever_px`) with every number,
`--selftest` FALSIFIES the instrument against a pure-translation panel, and the
planted-ramp control on real data measures what it actually recovers.

Two consequences of the model being LINEAR, both load-bearing:
  - a per-block constant position offset is absorbed by z_j, so the sub-stacks
    NOT sharing a pixel origin (`-framing=min` crops each to its own footprint)
    cannot bias `ax`. `--selftest` proves this by injecting offsets.
  - a block averages a star over that block's own drift, so `g` is seen through
    a boxcar ~244 px wide; the boxcar mean of a LINEAR function is its value at
    the midpoint, so the linear term is unsmeared. Curvature is not measured.

WHY THIS IS IN BOUNDS (the bright line, CLAUDE.md). Every pixel operation and
every measurement is a tool's: astrometry.net solved each sub-stack, Siril
`findstar` detected every star and reported its position and its RA/Dec through
that solve, Siril `psf` did every flux measurement as APERTURE photometry at a
forced radius against its own local background annulus (`setphot`). The
in-house part is the cross-match and the fit — a derived result no tool
provides. It reads no deliverable pixel, gates nothing, and rewrites nothing.
The tool search that had to fail first is recorded in the JSON (`tool_search`);
the load-bearing negative is that Siril `seqpsf -wcs=` converts the sky
coordinate to pixels ONCE and measures that same pixel area in every image, so
it cannot follow a star across a drifting sequence — measured, one real star,
m = -2.104 in the reference block against +3.55/+5.05/+3.63 in the other three,
and `-followstar` does not repair it without registration data.

WHY APERTURE PHOTOMETRY AND NOT THE STAR LIST'S `mag`. A Gaussian-fit magnitude
moves with the PSF, and the PSF varies across this field (registered radial
aberration: roundness gradient -0.099 across x). That is the signal under test,
so a fitted magnitude cannot measure it. `psf` reports the aperture magnitude
instead, and its local annulus is what makes the measure admissible at all:
every light stack pins `-norm=addscale -output_norm`, so each block carries its
own ADDITIVE pedestal, and a pedestal does not divide out of a flux ratio the
way a scale does. Report both aperture radii — a real throughput tilt does not
move with aperture, a PSF-fit artefact does.

INSTRUMENT FACTS, all pinned by probe on 1.4.4 (re-probe on a version change):
  - `boxselect` REFUSES a box crossing the frame edge and ABORTS the script, so
    stars within `--margin` of any edge are dropped (they would also carry a
    truncated background annulus).
  - `psf`'s aperture magnitude is stable across box sizes where the FITTED
    background is not: over boxes 40-160 px, m moves 5e-4 mag (and is identical
    to 1e-4 from 50 px up) while B moves 18%. So the annulus is read from the
    IMAGE, not from the selection. A 30 px box fails outright.
  - a failed measurement is returned as `m=<value>+/-9.9990`; 9.999 is the
    tool's own invalid sentinel and is rejected here, never averaged.
  - `psf` on empty sky returns a result or nothing, and does not abort.
  - `setfindstar reset` returns exit 1 ON SUCCESS, so it never ends an .ssf.
  - `findstar`'s default roundness floor 0.50 truncates exactly the elongated
    tail this data is made of; pinned to 0.05.

REMOVAL CONDITION: retire this the day an official tool reports a headless
position-dependent photometric solution across overlapping exposures without an
external catalogue — SCAMP's photometric mode is the candidate and is NOT
packaged on this distro (checked: apt has no `scamp`; `source-extractor` and
`swarp` are), or a PixInsight equivalent. Registered in BACKLOG.md
`removal-conditions`.

REPORTS, GATES NOTHING. No thresholds, no verdict, no PASS/FAIL: it writes the
number, its uncertainty, its lever and its n, and the reader decides.
"""
import glob
import json
import math
import os
import re
import subprocess
import sys

import numpy as np
from astropy.io import fits
from astropy.wcs import WCS

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "lib"))
import siril_run

# Siril's star list: 0 star# 1 layer 2 B 3 A 4 beta 5 X 6 Y 7 FWHMx 8 FWHMy
# 9 FWHMx" 10 FWHMy" 11 angle 12 RMSE 13 mag 14 Sat 15 profile 16 RA 17 Dec
LST_COLS = {"B": 2, "A": 3, "X": 5, "Y": 6, "FWHMx": 7, "FWHMy": 8,
            "mag": 13, "Sat": 14, "RA": 16, "Dec": 17}
BOX = 60                      # >= the 40 px stability plateau, with margin
BAD_SMAG = 9.9                # Siril's invalid-photometry sentinel is 9.9990
RE_SEL = re.compile(r"Current selection \[x, y, w, h\]: (-?\d+) (-?\d+) (\d+) (\d+)")
RE_X0 = re.compile(r"x0=([0-9.]+)px")
RE_Y0 = re.compile(r"y0=([0-9.]+)px")
RE_MAG = re.compile(r"m=(-?[0-9.]+)\xb1([0-9.]+)")
RE_B = re.compile(r"B=(-?[0-9.eE+-]+)")
RE_A = re.compile(r"^\s+A=(-?[0-9.eE+-]+)", re.M)


def uptime():
    return subprocess.run(["uptime"], capture_output=True, text=True).stdout.strip()


def sh(cmd):
    return subprocess.run(cmd, shell=True, capture_output=True, text=True).stdout.strip()


def run_ssf(wdir, lines, ssf_path, logpath):
    with open(ssf_path, "w") as f:
        f.write("requires 1.2.0\nsetcompress 0\nsetext fit\n" + "\n".join(lines) + "\n")
    with open(logpath, "w") as lg:
        r = siril_run.run(["-d", wdir, "-s", ssf_path], stdout=lg,
                          stderr=subprocess.STDOUT)
    return r.returncode


# ---------------------------------------------------------------- detection

def read_lst(path):
    rows = []
    for ln in open(path):
        if ln.startswith("#"):
            continue
        p = ln.rstrip("\n").split("\t")
        if len(p) < 18:
            continue
        rows.append([float(p[LST_COLS[k]]) for k in
                     ("B", "A", "X", "Y", "FWHMx", "FWHMy", "mag", "Sat", "RA", "Dec")])
    return np.array(rows, dtype=float) if rows else np.zeros((0, 10))


def unit_vec(ra, dec):
    r, d = np.radians(ra), np.radians(dec)
    return np.column_stack([np.cos(d) * np.cos(r), np.cos(d) * np.sin(r), np.sin(d)])


def cross_match(lists, tol_arcsec):
    """Match by SKY position through each product's OWN solved WCS.

    Never by pixel coordinates: the sub-stacks do not share a pixel origin
    (`-framing=min` crops each to its own footprint), which is the same fact
    that made member_separation.py match 67 of 2000 stars until it was re-based.
    A match is kept only if the nearest neighbour is inside `tol` AND the second
    nearest is beyond 3*tol, so a blend or a chance neighbour in this dense
    field is dropped rather than silently averaged.
    """
    from scipy.spatial import cKDTree
    tol = 2 * math.sin(math.radians(tol_arcsec / 3600.0) / 2)   # chord length
    ref = lists[0]
    uref = unit_vec(ref[:, 8], ref[:, 9])
    keep = np.ones(len(ref), bool)
    idx = [np.arange(len(ref))]
    stats = []
    for other in lists[1:]:
        tree = cKDTree(unit_vec(other[:, 8], other[:, 9]))
        d, j = tree.query(uref, k=2)
        ok = (d[:, 0] < tol) & (d[:, 1] > 3 * tol)
        stats.append({"within_tol": int((d[:, 0] < tol).sum()),
                      "unique": int(ok.sum())})
        keep &= ok
        idx.append(j[:, 0])
    return keep, idx, stats


# --------------------------------------------------------------- photometry

def measure(wdir, subs, pos, setphot, work, tag):
    """Siril `psf` at every (block, star) position. Returns m, s_m, x, y arrays.

    `pos[j]` is the block's OWN findstar position for each star, so the box is
    guaranteed to contain the star; the tool re-centroids inside it and does the
    aperture photometry at its own centroid.
    """
    n_st = pos[0].shape[0]
    m = np.full((len(subs), n_st), np.nan)
    sm = np.full((len(subs), n_st), np.nan)
    px = np.full((len(subs), n_st), np.nan)
    py = np.full((len(subs), n_st), np.nan)
    h = BOX // 2
    for j, sub in enumerate(subs):
        lines = [setphot, f"load {sub}"]
        for x, y in pos[j]:
            lines.append(f"boxselect {int(round(x)) - h} {int(round(y)) - h} {BOX} {BOX}")
            lines.append("psf 1")
        logp = os.path.join(work, f"psf_{tag}_{j:02d}.log")
        rc = run_ssf(wdir, lines, os.path.join(work, f"psf_{tag}_{j:02d}.ssf"), logp)
        if rc != 0:
            raise SystemExit(f"siril psf run failed for {sub} (rc={rc}) — see {logp}")
        # one segment per boxselect; a segment with no m= is a failed measure
        txt = open(logp, errors="replace").read()
        segs = txt.split("Running command: boxselect")[1:]
        if len(segs) != n_st:
            raise SystemExit(f"psf log has {len(segs)} boxselect segments, "
                             f"expected {n_st} — {logp}")
        for i, seg in enumerate(segs):
            mm = RE_MAG.search(seg)
            if not mm:
                continue
            m[j, i] = float(mm.group(1))
            sm[j, i] = float(mm.group(2))
            xx, yy = RE_X0.search(seg), RE_Y0.search(seg)
            if xx and yy:
                px[j, i], py[j, i] = float(xx.group(1)), float(yy.group(1))
    return m, sm, px, py


# --------------------------------------------------------------------- fit

def fit_tilt(m, sm, u, v, clip=4.0):
    """Weighted LS of m_ij = M_i + z_j + ax*u_ij + ay*v_ij.

    M_i is eliminated by the WEIGHTED within-star transform, which is exact for
    this model (the star block of the normal matrix is diagonal). What is left
    is a small dense system in the block dummies and the two position terms.
    """
    J, N = m.shape
    good = np.isfinite(m) & np.isfinite(sm) & (sm < BAD_SMAG) & (sm > 0)
    keep_star = good.all(axis=0)                 # same population in every block
    if keep_star.sum() < 20:
        return None
    m, sm, u, v = m[:, keep_star], sm[:, keep_star], u[:, keep_star], v[:, keep_star]
    N = m.shape[1]
    w = 1.0 / sm ** 2

    cols = [np.zeros((J, N)) for _ in range(J - 1)]     # block dummies, first dropped
    for j in range(1, J):
        cols[j - 1][j, :] = 1.0
    cols += [u, v]
    X = np.stack(cols, axis=-1)                        # (J, N, P)

    def within(a):                                      # weighted, per star
        wsum = w.sum(axis=0)
        if a.ndim == 3:
            return a - (w[..., None] * a).sum(axis=0)[None, ...] / wsum[None, :, None]
        return a - (w * a).sum(axis=0)[None, :] / wsum[None, :]

    # fit, clip whole stars, refit — the last pass is never clipped, so the
    # reported beta / residuals / design always describe the surviving sample
    n_clipped = 0
    for it in range(3):
        Xt, mt = within(X), within(m)
        A = (Xt * np.sqrt(w)[..., None]).reshape(-1, Xt.shape[-1])
        b = (mt * np.sqrt(w)).reshape(-1)
        beta, *_ = np.linalg.lstsq(A, b, rcond=None)
        r = (mt - (Xt * beta).sum(axis=-1))
        s = np.sqrt(np.average(r ** 2, weights=w))
        if it == 2:
            break
        bad = (np.abs(r) > clip * s).any(axis=0)        # a star, not a point
        if not bad.any():
            break
        alive = ~bad
        if alive.sum() < 20:
            return None
        n_clipped += int(bad.sum())
        m, w, X = m[:, alive], w[:, alive], X[:, alive]
        N = m.shape[1]

    n_obs = int((w > 0).sum())
    n_par = N + (J - 1) + 2                             # stars + dummies + ax,ay
    dof = max(n_obs - n_par, 1)
    chi2 = float((w * r ** 2).sum())
    cov = np.linalg.pinv(A.T @ A)
    err_formal = np.sqrt(np.diag(cov))
    scale = math.sqrt(chi2 / dof)

    # THE LEVER, and why the error bar cannot be trusted to stand in for it.
    # What identifies ax is whatever survives of the position column after the
    # star means and the block zero points have taken their share. Under a pure
    # translation NOTHING survives, the normal matrix is singular, and pinv
    # then reports variance ZERO along the null direction — so a degenerate fit
    # comes back CONFIDENTLY WRONG rather than loudly unidentified (measured in
    # --selftest 4a: a planted +0.100 returns -0.046 +- 0.0001). Read the lever,
    # not the sigma.
    sqw = np.sqrt(w).reshape(-1)
    scal = np.mean(sqw[sqw > 0])
    lever = []
    for c in (J - 1, J):                                # the u and v columns
        Q = A[:, :J - 1]
        res = A[:, c] - Q @ np.linalg.lstsq(Q, A[:, c], rcond=None)[0] if J > 1 \
            else A[:, c]
        lever.append(float(np.std(res) / scal))
    sv = np.linalg.svd(A, compute_uv=False)
    return {
        "ax": float(beta[-2]), "ay": float(beta[-1]),
        "ax_err": float(err_formal[-2] * scale), "ay_err": float(err_formal[-1] * scale),
        "ax_err_formal": float(err_formal[-2]), "ay_err_formal": float(err_formal[-1]),
        "n_stars": int(N), "n_obs": n_obs, "dof": int(dof),
        "n_stars_clipped": n_clipped, "clip_sigma": clip,
        "chi2_per_dof": float(chi2 / dof), "resid_rms_mag": float(s),
        "zero_points": [0.0] + [float(x) for x in beta[:J - 1]],
        "lever_frac_x": lever[0], "lever_frac_y": lever[1],
        "design_condition_number": float(sv[0] / sv[-1]) if sv[-1] > 0 else None,
    }


def fit_per_block_gradient(m, sm, u, v):
    """Let every block carry its OWN gradient, and report the deltas.

    THE CONFOUNDER THIS EXISTS TO MEASURE, and it is the one that decides
    whether the shared-gradient number above means anything. For a FIXED camera
    a sensor position maps to a FIXED altitude and azimuth, so atmospheric
    extinction and the skyglow gradient across a 27-degree field are sensor-fixed
    too — and unlike the flat's residual they DRIFT with transparency. Write the
    per-block gradient as `a + delta_j`; then for a block pair related by a
    rotation `theta` the measured magnitude difference carries

        delta_j * u          at FULL frame lever
        a * theta * (J u)    at the rotation lever only

    so a shared-gradient fit converts a gradient DRIFT of `delta` into a
    spurious constant of about `delta / theta`. With theta ~ 1 deg that is a
    ~60x amplification of the contaminant against the signal.

    `a` itself is NOT identifiable once the deltas are free — a constant added
    to every delta is exactly `a` — so this reports the DELTAS and their time
    ordering, never a corrected `a`. A monotone ordering in block index is the
    drift's signature.
    """
    J, N = m.shape
    good = np.isfinite(m) & np.isfinite(sm) & (sm < BAD_SMAG) & (sm > 0)
    keep = good.all(axis=0)
    if keep.sum() < 20:
        return None
    m, sm, u, v = m[:, keep], sm[:, keep], u[:, keep], v[:, keep]
    N = m.shape[1]
    w = 1.0 / sm ** 2

    def within(a):
        ws = w.sum(axis=0)
        if a.ndim == 3:
            return a - (w[..., None] * a).sum(axis=0)[None] / ws[None, :, None]
        return a - (w * a).sum(axis=0)[None] / ws[None]

    def solve(cols):
        X = np.stack(cols, axis=-1)
        Xt, mt = within(X), within(m)
        A = (Xt * np.sqrt(w)[..., None]).reshape(-1, X.shape[-1])
        b = (mt * np.sqrt(w)).reshape(-1)
        beta, *_ = np.linalg.lstsq(A, b, rcond=None)
        r = mt - (Xt * beta).sum(axis=-1)
        return beta, float((w * r ** 2).sum())

    dum = [np.zeros((J, N)) for _ in range(J - 1)]
    for j in range(1, J):
        dum[j - 1][j, :] = 1.0
    _, chi_shared = solve(dum + [u, v])
    gx = [np.zeros((J, N)) for _ in range(J - 1)]
    gy = [np.zeros((J, N)) for _ in range(J - 1)]
    for j in range(1, J):
        gx[j - 1][j, :] = u[j]
        gy[j - 1][j, :] = v[j]
    beta, chi_free = solve(dum + [u, v] + gx + gy)
    dax = [0.0] + [float(beta[J + 1 + j - 1]) for j in range(1, J)]
    day = [0.0] + [float(beta[J + 1 + (J - 1) + j - 1]) for j in range(1, J)]
    return {
        "delta_ax_by_block_mag": dax,
        "delta_ay_by_block_mag": day,
        "delta_ax_spread_mag": float(np.ptp(dax)),
        "delta_ax_spread_frac": float(10 ** (-0.4 * np.ptp(dax)) - 1.0),
        "monotone_in_block_order": bool(
            np.all(np.diff(dax) > 0) or np.all(np.diff(dax) < 0)),
        "chi2_shared": chi_shared, "chi2_free": chi_free,
        "n_stars": int(N),
    }


def as_fraction(ax):
    """ax is magnitudes across the full frame width; return g(right)/g(left)-1."""
    return 10 ** (-0.4 * ax) - 1.0


# ------------------------------------------------------------------- driver

def run_set(gdir, args, work=None):
    subs = sorted(glob.glob(os.path.join(gdir, "sub_*.fit")))
    if len(subs) < 2:
        raise SystemExit(f"{gdir}: need >=2 sub-stacks, found {len(subs)}")
    night = os.path.basename(os.path.dirname(os.path.dirname(gdir)))
    setname = os.path.basename(gdir).replace("groups_", "")
    repo = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    work = work or os.path.join(repo, "datasets", night, setname, "tilt_work")
    os.makedirs(work, exist_ok=True)

    heads, geom = [], []
    for s in subs:
        h = fits.getheader(s)
        heads.append(h)
        geom.append((h["NAXIS1"], h["NAXIS2"]))
    W = float(np.median([g[0] for g in geom]))
    H = float(np.median([g[1] for g in geom]))

    # ---- detection: one findstar per block, roundness floor dropped to 0.05
    lines = [f"setfindstar reset -roundness={args['roundness']}"]
    for j, s in enumerate(subs):
        lines += [f"load {s}",
                  f"findstar -out={work}/fs_{j:02d}.lst -layer={args['layer']}"]
    rc = run_ssf(gdir, lines, os.path.join(work, "findstar.ssf"),
                 os.path.join(work, "findstar.log"))
    if rc != 0:
        raise SystemExit(f"findstar run failed (rc={rc})")
    lists = [read_lst(os.path.join(work, f"fs_{j:02d}.lst")) for j in range(len(subs))]

    keep, idx, mstats = cross_match(lists, args["tol_arcsec"])
    sel = np.where(keep)[0]
    # common population: detected in every block, unsaturated everywhere, above
    # one common amplitude floor everywhere, and clear of every edge everywhere
    mg = args["margin"]
    for j, lst in enumerate(lists):
        r = lst[idx[j][sel]]
        ok = ((r[:, 1] >= args["amin"]) & (r[:, 7] == 0)
              & (r[:, 2] > mg) & (r[:, 2] < geom[j][0] - mg)
              & (r[:, 3] > mg) & (r[:, 3] < geom[j][1] - mg))
        sel = sel[ok]
    pos = [lists[j][idx[j][sel]][:, 2:4] for j in range(len(subs))]
    amps = np.array([lists[j][idx[j][sel]][:, 1] for j in range(len(subs))])
    if len(sel) < 50:
        raise SystemExit(f"{night}/{setname}: only {len(sel)} common stars")

    out = {
        "night": night, "set": setname, "groups_dir": gdir, "work_dir": work,
        "uptime": uptime(),
        "instrument": (
            "Siril 1.4.4 findstar (detection + position + RA/Dec through each "
            "sub-stack's own astrometry.net solve) + Siril psf (aperture "
            "photometry, forced radius, local background annulus via setphot); "
            "in-house: sky cross-match + weighted LS fit of magnitude against "
            "sensor position with per-star and per-block nuisance terms"),
        "n_blocks": len(subs),
        "blocks": [{"file": os.path.basename(s),
                    "naxis": list(geom[j]),
                    "stackcnt": int(heads[j].get("STACKCNT", 0)),
                    "livetime": float(heads[j].get("LIVETIME", 0.0))}
                   for j, s in enumerate(subs)],
        "frame_norm": {"width_px": W, "height_px": H},
        "detection": {
            "roundness_floor": args["roundness"], "layer": args["layer"],
            "per_block_found": [int(len(l)) for l in lists],
            "match_tol_arcsec": args["tol_arcsec"], "match_stats": mstats,
            "matched_all_blocks": int(keep.sum()),
            "amplitude_floor": args["amin"],
            "faintest_admitted_amplitude": float(amps.min()) if len(sel) else None,
            "edge_margin_px": mg,
            "common_population": int(len(sel)),
        },
        "geometry": block_geometry(subs, heads),
        "apertures": {},
    }

    for ap in args["apertures"]:
        setphot = (f"setphot -inner={args['inner']} -outer={args['outer']} "
                   f"-aperture={ap} -dyn_ratio=0.5")
        m, sm, px, py = measure(gdir, subs, pos, setphot, work, f"ap{ap}")
        u = px / W - 0.5
        v = py / H - 0.5
        fit = fit_tilt(m, sm, u, v)
        if fit is None:
            out["apertures"][str(ap)] = {"error": "fit failed — too few survivors"}
            continue
        fit["aperture_radius_px"] = ap
        fit["annulus_px"] = [args["inner"], args["outer"]]
        fit["background"] = "Siril psf local annulus (setphot -inner/-outer)"
        fit["tilt_frac_x"] = as_fraction(fit["ax"])
        fit["tilt_frac_x_err"] = abs(as_fraction(fit["ax"] + fit["ax_err"])
                                     - as_fraction(fit["ax"]))
        fit["tilt_frac_y"] = as_fraction(fit["ay"])
        fit["tilt_frac_y_err"] = abs(as_fraction(fit["ay"] + fit["ay_err"])
                                     - as_fraction(fit["ay"]))
        fit["sigma_x"] = abs(fit["ax"] / fit["ax_err"]) if fit["ax_err"] else None
        fit["valid_fraction"] = float(np.mean(np.isfinite(m) & (sm < BAD_SMAG)))
        fit["lever_px_x"] = fit["lever_frac_x"] * W
        fit["lever_px_y"] = fit["lever_frac_y"] * H

        # INTERNAL FALSIFICATION, free from the same photometry. A sensor-fixed
        # multiplicative field is ONE field, so every pair of blocks must
        # report the same ax — even though each pair carries its own rotation
        # (0.7 to 2.4 deg here) and therefore its own lever. A term that scales
        # with the rotation instead, or that is being manufactured by the
        # ~270x extrapolation from a ~20 px lever to the frame width, does not
        # survive this: the pairs disagree.
        pairs = []
        for a in range(len(subs)):
            for b in range(a + 1, len(subs)):
                pf = fit_tilt(m[[a, b]], sm[[a, b]], u[[a, b]], v[[a, b]])
                if pf is None:
                    continue
                rot = [g for g in out["geometry"]["vs_block_0"]]
                pairs.append({
                    "blocks": [a, b],
                    "tilt_frac_x": as_fraction(pf["ax"]),
                    "tilt_frac_x_err": abs(as_fraction(pf["ax"] + pf["ax_err"])
                                           - as_fraction(pf["ax"])),
                    "lever_px_x": pf["lever_frac_x"] * W,
                    "n_stars": pf["n_stars"],
                    "rotation_deg": (
                        (rot[b - 1]["rotation_deg"] if b > 0 else 0.0)
                        - (rot[a - 1]["rotation_deg"] if a > 0 else 0.0)),
                })
        fit["block_pairs"] = pairs
        fit["per_block_gradient"] = fit_per_block_gradient(m, sm, u, v)
        rots = [0.0] + [g["rotation_deg"] for g in out["geometry"]["vs_block_0"]]
        theta = math.radians(max(rots) - min(rots))
        pbg = fit["per_block_gradient"]
        if pbg and theta > 0:
            # what a gradient DRIFT of this size costs a shared-gradient fit
            fit["drift_amplification"] = 1.0 / theta
            fit["drift_leaked_as_shared_mag"] = pbg["delta_ax_spread_mag"] / theta
        if len(pairs) > 1:
            vals = np.array([p["tilt_frac_x"] for p in pairs])
            fit["block_pair_spread_frac"] = float(np.ptp(vals))
            fit["block_pair_std_frac"] = float(np.std(vals))
        np.savez_compressed(os.path.join(work, f"phot_ap{ap}.npz"),
                            m=m, sm=sm, px=px, py=py, W=W, H=H)
        out["apertures"][str(ap)] = fit

    if not args["keep"]:
        for f in glob.glob(os.path.join(work, "psf_*.log")):
            os.remove(f)
    return out


def refit(jsonpath):
    """Recompute every fit from the photometry this run already saved.

    The per-(block, star) magnitude matrix is written to `phot_ap<r>.npz` beside
    the star lists, so a change to the FIT never needs Siril re-run — which also
    means a corpus stays internally consistent when the analysis is extended.
    """
    res = json.load(open(jsonpath))
    repo = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    work = res.setdefault("work_dir", os.path.join(
        repo, "datasets", res["night"], res["set"], "tilt_work"))
    W, H = res["frame_norm"]["width_px"], res["frame_norm"]["height_px"]
    rots = [0.0] + [g["rotation_deg"] for g in res["geometry"]["vs_block_0"]]
    theta = math.radians(max(rots) - min(rots))
    for ap, old in list(res["apertures"].items()):
        npz = os.path.join(work, f"phot_ap{ap}.npz")
        if not os.path.exists(npz):
            npz = os.path.join(work, f"phot_ap{float(ap):g}.npz")
        if not os.path.exists(npz):
            print(f"  no photometry dump for r={ap} — skipped")
            continue
        d = np.load(npz)
        m, sm, px, py = d["m"], d["sm"], d["px"], d["py"]
        u, v = px / W - 0.5, py / H - 0.5
        fit = fit_tilt(m, sm, u, v)
        if fit is None:
            continue
        for k in ("aperture_radius_px", "annulus_px", "background"):
            if k in old:
                fit[k] = old[k]
        fit["tilt_frac_x"] = as_fraction(fit["ax"])
        fit["tilt_frac_x_err"] = abs(as_fraction(fit["ax"] + fit["ax_err"])
                                     - as_fraction(fit["ax"]))
        fit["tilt_frac_y"] = as_fraction(fit["ay"])
        fit["tilt_frac_y_err"] = abs(as_fraction(fit["ay"] + fit["ay_err"])
                                     - as_fraction(fit["ay"]))
        fit["sigma_x"] = abs(fit["ax"] / fit["ax_err"]) if fit["ax_err"] else None
        fit["lever_px_x"] = fit["lever_frac_x"] * W
        fit["lever_px_y"] = fit["lever_frac_y"] * H
        pairs = []
        for a in range(m.shape[0]):
            for b in range(a + 1, m.shape[0]):
                pf = fit_tilt(m[[a, b]], sm[[a, b]], u[[a, b]], v[[a, b]])
                if pf is None:
                    continue
                pairs.append({
                    "blocks": [a, b],
                    "tilt_frac_x": as_fraction(pf["ax"]),
                    "tilt_frac_x_err": abs(as_fraction(pf["ax"] + pf["ax_err"])
                                           - as_fraction(pf["ax"])),
                    "lever_px_x": pf["lever_frac_x"] * W,
                    "n_stars": pf["n_stars"],
                    "rotation_deg": rots[b] - rots[a],
                })
        fit["block_pairs"] = pairs
        if len(pairs) > 1:
            vals = np.array([p["tilt_frac_x"] for p in pairs])
            fit["block_pair_spread_frac"] = float(np.ptp(vals))
            fit["block_pair_std_frac"] = float(np.std(vals))
        pbg = fit_per_block_gradient(m, sm, u, v)
        fit["per_block_gradient"] = pbg
        if pbg and theta > 0:
            fit["drift_amplification"] = 1.0 / theta
            fit["drift_leaked_as_shared_mag"] = pbg["delta_ax_spread_mag"] / theta
        res["apertures"][ap] = fit
    open(jsonpath, "w").write(json.dumps(res, indent=1) + "\n")
    return res


def block_geometry(subs, heads):
    """Block-to-block field mapping, from the solved WCS alone.

    Reports what identifies the fit: the rotation, and the SPREAD of the
    same-star displacement across the field. A pure translation has zero spread
    and the measurement is then formally impossible.
    """
    ws = [WCS(h, naxis=2) for h in heads]
    n1, n2 = heads[0]["NAXIS1"], heads[0]["NAXIS2"]
    gx, gy = np.meshgrid(np.linspace(200, n1 - 200, 9), np.linspace(200, n2 - 200, 9))
    gx, gy = gx.ravel(), gy.ravel()
    sky = ws[0].pixel_to_world_values(gx, gy)
    M = np.column_stack([gx, gy, np.ones_like(gx)])
    rows = []
    for j in range(1, len(ws)):
        qx, qy = ws[j].world_to_pixel_values(sky[0], sky[1])
        cx, *_ = np.linalg.lstsq(M, qx, rcond=None)
        cy, *_ = np.linalg.lstsq(M, qy, rcond=None)
        A = np.array([[cx[0], cx[1]], [cy[0], cy[1]]])
        rows.append({
            "block": j,
            "rotation_deg": float(np.degrees(np.arctan2(A[1, 0] - A[0, 1],
                                                        A[0, 0] + A[1, 1]))),
            "scale": float(math.sqrt(abs(np.linalg.det(A)))),
            "dx_mean_px": float(np.mean(qx - gx)),
            "dx_spread_px": float(np.ptp(qx - gx)),
            "dy_mean_px": float(np.mean(qy - gy)),
            "dy_spread_px": float(np.ptp(qy - gy)),
        })
    return {"vs_block_0": rows,
            "note": ("dx_spread is the lever: a pure translation (spread 0) "
                     "makes the linear tilt formally unidentifiable")}


# ---------------------------------------------------------------- selftest

def _panel(n_stars, blocks, ax_true, ay_true=0.0, noise=0.01, seed=1,
           rotate=True, offsets=None, W=5769.0, H=3950.0):
    """Synthetic (star, block) panel with a KNOWN planted sensor-fixed tilt."""
    rng = np.random.default_rng(seed)
    x0 = rng.uniform(200, W - 200, n_stars)
    y0 = rng.uniform(200, H - 200, n_stars)
    M = rng.uniform(-2, 3, n_stars)
    z = rng.uniform(-0.2, 0.2, len(blocks))
    m = np.zeros((len(blocks), n_stars))
    U = np.zeros_like(m)
    V = np.zeros_like(m)
    for j, (tx, ty, th) in enumerate(blocks):
        t = math.radians(th) if rotate else 0.0
        cx, cy = W / 2, H / 2
        xr = cx + (x0 - cx) * math.cos(t) - (y0 - cy) * math.sin(t) + tx
        yr = cy + (x0 - cx) * math.sin(t) + (y0 - cy) * math.cos(t) + ty
        off = offsets[j] if offsets else (0.0, 0.0)
        U[j] = (xr + off[0]) / W - 0.5
        V[j] = (yr + off[1]) / H - 0.5
        # the TRUE tilt lives in true sensor coords; the canvas offset is the
        # nuisance the block zero point must absorb
        m[j] = M + z[j] + ax_true * (xr / W - 0.5) + ay_true * (yr / H - 0.5) \
            + rng.normal(0, noise, n_stars)
    return m, np.full_like(m, noise), U, V


def selftest():
    ok = True

    def check(name, cond, detail=""):
        nonlocal ok
        print(("  PASS  " if cond else "  FAIL  ") + name + ("   " + detail if detail else ""))
        ok &= bool(cond)

    print("object_tilt --selftest")

    print(" 1. parser — the tool's own invalid sentinel and a good measurement")
    seg = ("\n\t\tx0=4708.08px\n\t\ty0=1023.27px\n\t\tB=0.001845\n"
           "\t\tA=0.868630\n\t\tm=-2.1045\xb10.0011\n")
    mm = RE_MAG.search(seg)
    check("good psf parsed", mm and abs(float(mm.group(1)) + 2.1045) < 1e-9
          and abs(float(mm.group(2)) - 0.0011) < 1e-9)
    bad = RE_MAG.search("m=-2.0190\xb19.9990")
    check("invalid sentinel is above the reject floor",
          bad and float(bad.group(2)) >= BAD_SMAG)

    print(" 2. recovery — a planted tilt, with rotation present")
    blocks = [(0, 0, 0), (-253, -19, 0.97), (-516, -58, 1.64), (-779, -105, 2.37)]
    for planted in (0.10, -0.04):
        m, sm, u, v = _panel(3000, blocks, planted, seed=7)
        f = fit_tilt(m, sm, u, v)
        d = abs(f["ax"] - planted)
        check(f"ax={planted:+.3f} recovered {f['ax']:+.4f} +- {f['ax_err']:.4f}",
              d < 4 * f["ax_err"], f"|delta|={d:.4f}")

    print(" 3. null — no planted tilt reads zero within its own error")
    m, sm, u, v = _panel(3000, blocks, 0.0, seed=11)
    f0 = fit_tilt(m, sm, u, v)
    check(f"ax={f0['ax']:+.5f} +- {f0['ax_err']:.5f}",
          abs(f0["ax"]) < 4 * f0["ax_err"])

    print(" 4. FALSIFICATION — break the mechanism, the instrument must go RED")
    print("    4a. pure translation: the lever is removed, so a real planted")
    print("        tilt MUST become unrecoverable (this is the degeneracy)")
    flat = [(0, 0, 0), (-253, -19, 0), (-516, -58, 0), (-779, -105, 0)]
    m, sm, u, v = _panel(3000, flat, 0.10, seed=7, rotate=False)
    fdeg = fit_tilt(m, sm, u, v)
    check("planted 0.100 is NOT recovered without rotation "
          f"(ax={fdeg['ax']:+.4f} +- {fdeg['ax_err']:.4f})",
          abs(fdeg["ax"] - 0.10) > 4 * fdeg["ax_err"] or fdeg["ax_err"] > 0.05,
          "-> the rotation is the lever, not the translation")
    check(f"and the LEVER collapses to {fdeg['lever_frac_x']*5769:.2f} px "
          "(the sigma does NOT — read the lever)",
          fdeg["lever_frac_x"] * 5769 < 1.0)
    print("    4b. restore the rotation: the SAME code must catch it again")
    m, sm, u, v = _panel(3000, blocks, 0.10, seed=7)
    fres = fit_tilt(m, sm, u, v)
    check(f"caught again (ax={fres['ax']:+.4f} +- {fres['ax_err']:.4f})",
          abs(fres["ax"] - 0.10) < 4 * fres["ax_err"])
    check(f"and the lever is back at {fres['lever_frac_x']*5769:.1f} px",
          fres["lever_frac_x"] * 5769 > 10.0)
    print("    4c. corrupt the position axis (u := 0): a planted tilt must die")
    m, sm, u, v = _panel(3000, blocks, 0.10, seed=7)
    fbad = fit_tilt(m, sm, np.zeros_like(u), v)
    check(f"blinded instrument reports ax={fbad['ax']:+.4f}", abs(fbad["ax"]) < 1e-6)

    print(" 5. per-block canvas offsets must NOT bias ax (framing=min)")
    offs = [(0, 0), (611.9, -416.0), (-250.0, 300.0), (900.0, 120.0)]
    m, sm, u, v = _panel(3000, blocks, 0.10, seed=7, offsets=offs)
    foff = fit_tilt(m, sm, u, v)
    check(f"ax={foff['ax']:+.4f} +- {foff['ax_err']:.4f} with 611.9 px offsets",
          abs(foff["ax"] - 0.10) < 4 * foff["ax_err"])

    print(" 6. fraction conversion")
    check("ax=0 -> 0%", abs(as_fraction(0.0)) < 1e-12)
    check("g ratio 0.9 round-trips",
          abs(as_fraction(-2.5 * math.log10(0.9)) - (-0.1)) < 1e-12)

    print(("SELFTEST PASS" if ok else "SELFTEST FAIL"))
    return 0 if ok else 1


def main(argv):
    if "--selftest" in argv:
        return selftest()
    if argv and argv[0] == "--refit":
        for p in argv[1:]:
            r = refit(p)
            f = r["apertures"].get("10", {})
            print(f"{r['night']}/{r['set']:12s} tilt {100*f.get('tilt_frac_x', 0):+8.2f}% "
                  f"pair-spread {100*f.get('block_pair_spread_frac', 0):8.1f}  "
                  f"drift-delta {f.get('per_block_gradient', {}).get('delta_ax_spread_mag', 0):.4f} mag "
                  f"x{f.get('drift_amplification', 0):.0f} = "
                  f"{f.get('drift_leaked_as_shared_mag', 0):+.2f} mag leaked")
        return 0
    if not argv or argv[0].startswith("--"):
        print(__doc__)
        return 2
    gdir = os.path.abspath(argv[0])
    args = {"apertures": [10, 16], "inner": 20, "outer": 30, "amin": 0.005,
            "tol_arcsec": 34.0, "margin": 40, "layer": 1, "roundness": 0.05,
            "keep": False}
    outp = None
    label = None
    for a in argv[1:]:
        if a.startswith("--aperture="):
            args["apertures"] = [float(x) for x in a.split("=", 1)[1].split(",")]
        elif a.startswith("--inner="):
            args["inner"] = float(a.split("=", 1)[1])
        elif a.startswith("--outer="):
            args["outer"] = float(a.split("=", 1)[1])
        elif a.startswith("--amin="):
            args["amin"] = float(a.split("=", 1)[1])
        elif a.startswith("--tol-arcsec="):
            args["tol_arcsec"] = float(a.split("=", 1)[1])
        elif a.startswith("--margin="):
            args["margin"] = int(a.split("=", 1)[1])
        elif a.startswith("--layer="):
            args["layer"] = int(a.split("=", 1)[1])
        elif a.startswith("--json="):
            outp = a.split("=", 1)[1]
        elif a.startswith("--label="):
            label = a.split("=", 1)[1]
        elif a.startswith("--work="):
            args["work"] = a.split("=", 1)[1]
        elif a == "--keep":
            args["keep"] = True
        else:
            print(f"unknown arg {a}", file=sys.stderr)
            return 2
    res = run_set(gdir, args, work=args.get("work"))
    if label:
        res["label"] = label
    txt = json.dumps(res, indent=1)
    if outp:
        os.makedirs(os.path.dirname(os.path.abspath(outp)), exist_ok=True)
        open(outp, "w").write(txt + "\n")
        print(f"wrote {outp}")
    for ap, f in res["apertures"].items():
        if "error" in f:
            print(f"  r={ap}px  {f['error']}")
            continue
        print(f"  r={ap}px  tilt_x = {100*f['tilt_frac_x']:+.3f}% "
              f"+- {100*f['tilt_frac_x_err']:.3f}%  ({f['sigma_x']:.1f} sigma)   "
              f"tilt_y = {100*f['tilt_frac_y']:+.3f}% +- {100*f['tilt_frac_y_err']:.3f}%")
        print(f"           n_stars={f['n_stars']} n_obs={f['n_obs']} "
              f"chi2/dof={f['chi2_per_dof']:.2f} resid={f['resid_rms_mag']:.4f}mag "
              f"lever={f['lever_px_x']:.1f}px(x)/{f['lever_px_y']:.1f}px(y)")
        if f.get("block_pairs"):
            pr = "  ".join(f"{p['blocks'][0]}{p['blocks'][1]}:{100*p['tilt_frac_x']:+.1f}%"
                           for p in f["block_pairs"])
            print(f"           block pairs  {pr}   "
                  f"spread {100*f.get('block_pair_spread_frac', 0):.1f}%")
    if not outp:
        print(txt)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
