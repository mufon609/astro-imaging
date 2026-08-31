#!/usr/bin/env python3
"""Measure how much of two flats' DIFFERENCE reaches the delivered object.

  flat_differential.py <arm_ref.fit> <arm_alt.fit> [--json=OUT] [--label=NAME]
                       [--work=DIR] [--aperture=10,16] [--inner=20] [--outer=30]
                       [--amin=0.005] [--margin=40] [--layer=1] [--keep]
  flat_differential.py --selftest

THE QUESTION, AND WHY IT IS ASKED DIFFERENTIALLY. A sky flat converges to
`(mean sky) x V`; horizon-fixed sky structure cannot drift out of a median of
un-registered lights, so it bakes into the flat, and dividing by it leaves the
object carrying a multiplicative residual `g(sensor)` it never had. The
ABSOLUTE size of that residual is a registered DEAD END (docs/dead-ends.md),
for two independent reasons:

  BLOCKER 1, GEOMETRIC. Fitting `m_ij = M_i + z_j + a*u_ij` under a pure
  translational drift splits `a*u_ij` into `a*u_i + a*c_j`, which the per-star
  and per-block nuisances absorb EXACTLY. `a` is unidentifiable at any drift
  size; the only lever is field rotation, measured at a median 29.1 px against
  a 5769 px frame.
  BLOCKER 2, PHYSICAL. For a FIXED camera every sensor position maps to a fixed
  altitude, so extinction and skyglow are sensor-fixed too and airmass-shaped —
  the same spatial shape as the flat's residual. One fit sees their sum.

BOTH DIE HERE, AND THAT IS THIS INSTRUMENT'S ENTIRE JUSTIFICATION. Two arms
built from the SAME frames with different flats give, for star i,

    dm_i = m_i(alt) - m_i(ref) = c + ax*u_i + ay*v_i

`M_i` cancels IDENTICALLY — it is the same star in the same photons — so
nothing per-star is fitted and nothing is left free to absorb a linear mode.
The lever is no longer the rotation: it is the full canvas, because the
identifying spread is the spread of STAR POSITIONS, not of the drift. Identical
frames also carry identical extinction and identical skyglow at every sensor
position, so blocker 2's term cancels in the subtraction along with everything
else the two arms share. `--selftest` proves the first claim on the SAME
pure-translation panel that broke the absolute design: where `object_tilt.py`
returns -0.046 for a planted +0.100 with the lever collapsed to 0.00 px, this
fit returns the planted value with a lever of ~1600 px. Same fixture, opposite
verdict.

WHAT IT DOES NOT MEASURE. The DIFFERENCE of two imprints, never the absolute
tilt. A null BOUNDS the object's sensitivity to a known dose difference; it
cannot resurrect the 3.11% / 241-sigma figure, which stays UNVERIFIED. Neither
outcome licenses a statement about the flat's share of the TOTAL defect.

THE TWO ARMS MUST BE PIXEL-ALIGNED, AND THAT IS NOT FREE. `register -2pass`
re-chooses the reference frame from image quality and the CALIBRATION changes
that choice (measured: one flat picked image 1 and a 4896x3616 canvas, the other
picked image 2 and 4887x3641). Build the arms with
`run_undistort_pipeline.sh --regdata=<lt_.seq>`, which hands every arm the first
arm's registration data. This script REFUSES a pair whose canvases differ, and
reports the psf centroid agreement between arms as a live alignment check —
a pair that drifted apart shows up as a centroid offset, not as a wrong answer.

WHY THIS IS IN BOUNDS (the bright line, CLAUDE.md). Every pixel operation and
every measurement is a tool's: Siril `split` extracts the channel, Siril
`findstar` detects every star and reports its position, Siril `psf` does every
flux measurement as APERTURE photometry at a forced radius against its own local
background annulus (`setphot`), and the pixel-ratio field is measured by the
shipped `flat_odd_component.py` (Siril `fdiv` + Siril `stat`), invoked as its own
CLI rather than reimplemented. The in-house part is the SUBTRACTION of two tool
measurements and the straight-line fit — a derived result no tool provides. It
reads no deliverable pixel, gates nothing, and rewrites nothing.

TWO INSTRUMENTS, ONE QUESTION, AND THEY ARE INDEPENDENT. The pixel-ratio field
measures the delivered imprint over the whole frame including the sky; the
matched-star differential measures it on the OBJECT'S OWN FLUX, which is the
defect's stated harm. Report both. If they disagree, that disagreement is the
finding, and neither number ships until it is attributed.

INSTRUMENT FACTS (pinned by probe on Siril 1.4.4 — re-probe on a version change;
inherited from object_tilt.py, whose photometry this reuses):
  - `psf`'s aperture magnitude is stable across box sizes where the FITTED
    background is not, so the annulus is read from the IMAGE, not the selection.
  - a failed measurement returns `m=<value>+/-9.9990`; 9.999 is the tool's own
    invalid sentinel, rejected here, never averaged.
  - `boxselect` REFUSES a box crossing the frame edge and ABORTS the script, so
    stars within `--margin` of any edge are dropped.
  - `findstar`'s default roundness floor 0.50 truncates exactly the elongated
    tail this data is made of; pinned to 0.05.

REMOVAL CONDITION: retire the day an official tool reports, headless, the
position-dependent PHOTOMETRIC RATIO FIELD between two aligned exposures — i.e.
the subtraction and the fit, not just the two flux lists.

REPORTS, GATES NOTHING. No thresholds and no verdict: it writes the number, its
uncertainty, its lever, its n, and the reader decides.
"""
import json
import math
import os
import subprocess
import sys

import numpy as np
from astropy.io import fits

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "..", "lib"))
import object_tilt                      # psf photometry + the star-list reader
import siril_run

CHANNELS = ("R", "G", "B")

# Recorded in every run because "every number came from a tool" does not make an
# in-house analysis in-bounds — what makes it in-bounds is that no tool does it,
# and that claim goes stale. Re-probe on a Siril version change or a new install.
TOOL_SEARCH = {
    "siril fdiv + stat (via flat_odd_component.py)": "ADOPTED as the PRIMARY "
        "instrument — the delivered imprint-ratio field needs no fit and no "
        "cross-match at all once the arms are pixel-aligned: Siril divides the "
        "two stacks and Siril's own regional medians measure the result. The "
        "shipped CLI is invoked, not reimplemented.",
    "siril psf + setphot": "ADOPTED as the CONFIRMING instrument — aperture "
        "photometry at a forced radius against its own local annulus, headless, "
        "on the layer the rest of the chain uses.",
    "siril seqpsf -at=": "APPLICABLE HERE, unlike the absolute measurement, and "
        "PROBED rather than reasoned about. Its disqualifying behaviour there — it "
        "converts a position ONCE and measures that same pixel area in every image "
        "— is CORRECT for an aligned pair, where the star does not move. Run on the "
        "two arms as a 2-image sequence it returns m = -2.055611 +- 0.001089 (arm A) "
        "and -2.071396 +- 0.001081 (arm B), against -2.0556 / -2.0714 from the "
        "adopted per-image `psf` path — agreement 1.1e-5 mag, which is the psf log's "
        "own printing precision. NOT ADOPTED (it measures one star per invocation "
        "from a selection, i.e. the same per-star, per-image call as `psf`, with a "
        "parser that is not the one already validated here) but recorded as a "
        "POSITIVE cross-validation of the photometry: "
        "datasets/<night>/<set>/flatdiff_work/seqpsf_crosscheck.json.",
    "source-extractor 2.28.2 dual-image mode": "AVAILABLE and VIABLE, NOT "
        "ADOPTED. Documented to detect on one image and measure FLUX_APER at "
        "those positions in a second — the two flux lists this needs. Not "
        "probed, because nothing here depends on it working: it would still "
        "leave the SUBTRACTION and the FIT in-house, it reads plane 1 of the "
        "cube rather than the green layer the chain uses, and Siril's psf is "
        "already validated for aperture invariance in this repo.",
    "conclusion": "no installed tool reports the position-dependent photometric "
        "RATIO FIELD between two aligned exposures, so the subtraction and the "
        "straight-line fit are the in-house part.",
}


def run_ssf(wdir, lines, ssf_path, logpath):
    with open(ssf_path, "w") as f:
        f.write("requires 1.2.0\nset32bits\nsetcompress 0\nsetext fit\n"
                + "\n".join(lines) + "\n")
    with open(logpath, "w") as lg:
        r = siril_run.run(["-d", wdir, "-s", ssf_path], stdout=lg,
                          stderr=subprocess.STDOUT)
    if r.returncode != 0:
        raise SystemExit(f"siril failed (rc={r.returncode}) — see {logpath}")


def split_channels(img, work, tag):
    """Siril `split`: the 3-layer stack -> three mono planes. Siril's pixel op."""
    outs = [os.path.join(work, f"{tag}_{c}") for c in CHANNELS]
    if all(os.path.exists(o + ".fit") for o in outs):
        return [o + ".fit" for o in outs]
    run_ssf(work, [f"load {img}", "split " + " ".join(outs)],
            os.path.join(work, f"split_{tag}.ssf"),
            os.path.join(work, f"split_{tag}.log"))
    return [o + ".fit" for o in outs]


# ------------------------------------------------------- PRIMARY: pixel ratio

def profile_x(ref_ch, alt_ch, work, tag, n=9, box=80):
    """Siril `stat` medians of the ratio field along the x midline.

    THE ATTRIBUTION TOOL, and it exists because the two instruments will not
    agree exactly. The pixel field's LR is anchored on the four CORNER boxes;
    the star fit is a straight line weighted by where the stars actually are,
    i.e. the middle. If the delivered field departs from a straight line those
    two summaries MUST differ, and by how much is a measurement rather than a
    guess. Siril does the division and every median; the profile is just where
    the boxes were placed.
    """
    from flat_odd_component import STAT
    hdr = fits.getheader(alt_ch)
    W, H = int(hdr["NAXIS1"]), int(hdr["NAXIS2"])
    tmp = os.path.join(work, f"_prof_{tag}")
    # ref_ch=None profiles the image AS GIVEN — used to run this same instrument
    # over the two FLATS' own ratio, which is what the delivered field is compared
    # against.
    mk = [f"load {alt_ch}"] + ([] if ref_ch is None else [f"fdiv {ref_ch} 0.5"])
    run_ssf(work, mk + [f"save {tmp}"],
            os.path.join(work, f"prof_mk_{tag}.ssf"),
            os.path.join(work, f"prof_mk_{tag}.log"))
    xs = [int(round(2 + i * (W - 4 - box) / (n - 1))) for i in range(n)]
    y = (H - box) // 2
    lines = []
    for x in xs:
        lines += [f"load {tmp}", f"crop {x} {y} {box} {box}", "stat"]
    logp = os.path.join(work, f"prof_{tag}.log")
    run_ssf(work, lines, os.path.join(work, f"prof_{tag}.ssf"), logp)
    med = [float(m.group(2)) for m in STAT.finditer(open(logp, errors="replace").read())]
    os.remove(tmp + ".fit")
    if len(med) != n:
        raise SystemExit(f"profile parsed {len(med)} stat blocks, expected {n} — {logp}")
    centres = [x + box / 2.0 for x in xs]
    # the straight line through the two END boxes, against the measured middle:
    # the departure IS the non-linearity the two instruments summarise differently
    lin = [med[0] + (med[-1] - med[0]) * (c - centres[0]) / (centres[-1] - centres[0])
           for c in centres]
    dep = [(m - l) / ((med[0] + med[-1]) / 2) for m, l in zip(med, lin)]
    return {
        "box_px": box, "y_row": y, "x_box_centres": centres,
        "median_ratio": med,
        "departure_from_the_end_to_end_straight_line": dep,
        "max_abs_departure": max(abs(x) for x in dep),
        "reading": "a positive departure in the middle means the delivered field "
                   "is CONVEX there, so a star-weighted straight-line fit reads a "
                   "different slope than the corner-anchored dipole. This is the "
                   "attribution for any disagreement between the two instruments.",
    }


def ratio_field(ref_ch, alt_ch, work, out_json, label):
    """The shipped odd-component instrument, on the two arms' channel planes.

    `flat_odd_component.py --ratio` is exactly this measurement: Siril `fdiv`
    of one image by another (never `idiv`, which clips at 1.0 silently), then
    Siril `stat` regional medians, with the two-scalar no-clip control built in.
    It is invoked as its own CLI so there is ONE definition of the measurement.
    """
    cmd = [sys.executable, os.path.join(HERE, "flat_odd_component.py"),
           alt_ch, out_json, f"--ratio={ref_ch}", "--control", f"--label={label}"]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0 or not os.path.exists(out_json):
        raise SystemExit(f"flat_odd_component failed:\n{r.stdout}\n{r.stderr}")
    return json.load(open(out_json))


# --------------------------------------------- CONFIRMING: star flux differential

def fit_differential(dm, sdm, u, v, clip=4.0):
    """Weighted LS of dm_ij = c_j + ax*u_ij + ay*v_ij.

    dm has shape (J, N): J=1 for a real arm pair (one stack each, so one zero
    point), J>1 only for the selftest's block-structured panel. There is NO
    per-star term — that is the whole point. `M_i` cancelled in the subtraction,
    so the identifying spread is the spread of STAR POSITIONS across the canvas,
    not the drift's departure from a translation.

    THE LEVER is reported the same way object_tilt.fit_tilt reports it — the
    residual of the position column after the other design columns take their
    share — so the two are directly comparable. There it collapses to ~29 px on
    a 5769 px frame; here it is the canvas.
    """
    J, N = dm.shape
    good = np.isfinite(dm) & np.isfinite(sdm) & (sdm > 0)
    keep = good.all(axis=0)
    if keep.sum() < 20:
        return None
    dm, sdm, u, v = dm[:, keep], sdm[:, keep], u[:, keep], v[:, keep]
    N = dm.shape[1]
    w = 1.0 / sdm ** 2

    cols = [np.zeros((J, N)) for _ in range(J)]      # one zero point per arm-pair
    for j in range(J):
        cols[j][j, :] = 1.0
    cols += [u, v]

    n_clipped = 0
    for it in range(3):
        X = np.stack(cols, axis=-1)
        A = (X * np.sqrt(w)[..., None]).reshape(-1, X.shape[-1])
        b = (dm * np.sqrt(w)).reshape(-1)
        beta, *_ = np.linalg.lstsq(A, b, rcond=None)
        r = dm - (X * beta).sum(axis=-1)
        s = np.sqrt(np.average(r ** 2, weights=w))
        if it == 2:
            break
        bad = (np.abs(r) > clip * s).any(axis=0)     # a star, not a point
        if not bad.any():
            break
        alive = ~bad
        if alive.sum() < 20:
            return None
        n_clipped += int(bad.sum())
        dm, w = dm[:, alive], w[:, alive]
        cols = [c[:, alive] for c in cols]
        N = dm.shape[1]

    n_obs = int((w > 0).sum())
    dof = max(n_obs - (J + 2), 1)
    chi2 = float((w * r ** 2).sum())
    cov = np.linalg.pinv(A.T @ A)
    scale = math.sqrt(chi2 / dof)
    err = np.sqrt(np.diag(cov))
    sqw = np.sqrt(w).reshape(-1)
    scal = np.mean(sqw[sqw > 0])
    lever = []
    for c in (J, J + 1):
        Q = A[:, :J]
        res = A[:, c] - Q @ np.linalg.lstsq(Q, A[:, c], rcond=None)[0]
        lever.append(float(np.std(res) / scal))
    sv = np.linalg.svd(A, compute_uv=False)
    return {
        "ax": float(beta[-2]), "ay": float(beta[-1]),
        "ax_err": float(err[-2] * scale), "ay_err": float(err[-1] * scale),
        "ax_err_formal": float(err[-2]),
        "zero_points": [float(x) for x in beta[:J]],
        "n_stars": int(N), "n_obs": n_obs, "dof": int(dof),
        "n_stars_clipped": n_clipped, "clip_sigma": clip,
        "chi2_per_dof": float(chi2 / dof), "resid_rms_mag": float(s),
        "lever_frac_x": lever[0], "lever_frac_y": lever[1],
        "design_condition_number": float(sv[0] / sv[-1]) if sv[-1] > 0 else None,
    }


def star_differential(ref, alt, work, args):
    """Siril findstar on the reference arm, Siril psf on BOTH at those positions."""
    hr, ha = fits.getheader(ref), fits.getheader(alt)
    if (hr["NAXIS1"], hr["NAXIS2"]) != (ha["NAXIS1"], ha["NAXIS2"]):
        raise SystemExit(
            f"the two arms have different canvases ({hr['NAXIS1']}x{hr['NAXIS2']} "
            f"vs {ha['NAXIS1']}x{ha['NAXIS2']}) — they are not pixel-comparable. "
            "Build them with run_undistort_pipeline.sh --regdata=<lt_.seq> so "
            "every arm is handed the first arm's registration data.")
    W, H = float(hr["NAXIS1"]), float(hr["NAXIS2"])

    lst = os.path.join(work, "fs_ref.lst")
    run_ssf(work, [f"setfindstar reset -roundness={args['roundness']}",
                   f"load {ref}",
                   f"findstar -out={lst} -layer={args['layer']}"],
            os.path.join(work, "findstar.ssf"),
            os.path.join(work, "findstar.log"))
    rows = object_tilt.read_lst(lst)
    if not len(rows):
        raise SystemExit(f"findstar found nothing in {ref}")
    mg = args["margin"]
    ok = ((rows[:, 1] >= args["amin"]) & (rows[:, 7] == 0)
          & (rows[:, 2] > mg) & (rows[:, 2] < W - mg)
          & (rows[:, 3] > mg) & (rows[:, 3] < H - mg))
    pos = rows[ok][:, 2:4]
    if len(pos) < 50:
        raise SystemExit(f"only {len(pos)} usable stars in {ref}")

    out = {
        "n_detected": int(len(rows)), "n_admitted": int(len(pos)),
        "detection": {"roundness_floor": args["roundness"], "layer": args["layer"],
                      "amplitude_floor": args["amin"], "edge_margin_px": mg,
                      "detected_on": os.path.basename(ref)},
        "canvas_wh": [W, H], "apertures": {},
    }
    for ap in args["apertures"]:
        setphot = (f"setphot -inner={args['inner']} -outer={args['outer']} "
                   f"-aperture={ap} -dyn_ratio=0.5")
        # object_tilt.measure drives `boxselect` + `psf` per star per image and
        # parses the tool's own output, including its invalid sentinel.
        m, sm, px, py = object_tilt.measure(
            work, [ref, alt], [pos, pos], setphot, work, f"ap{ap}")
        valid = (np.isfinite(m) & (sm < object_tilt.BAD_SMAG) & (sm > 0)).all(axis=0)
        dm = (m[1] - m[0])[None, :]
        sdm = np.sqrt(sm[0] ** 2 + sm[1] ** 2)[None, :]
        # ALIGNMENT CHECK, free from the same photometry: the tool re-centroids
        # inside each box, so if the arms had drifted apart the centroids would
        # separate. This is the live guard behind the canvas-size refusal.
        dx = (px[1] - px[0])[valid]
        dy = (py[1] - py[0])[valid]
        u = (px[0] / W - 0.5)[None, :]
        v = (py[0] / H - 0.5)[None, :]
        sdm = np.where(valid[None, :], sdm, np.nan)
        fit = fit_differential(dm, sdm, u, v)
        if fit is None:
            out["apertures"][str(ap)] = {"error": "fit failed — too few survivors"}
            continue
        fit["aperture_radius_px"] = ap
        fit["annulus_px"] = [args["inner"], args["outer"]]
        fit["background"] = "Siril psf local annulus (setphot -inner/-outer)"
        fit["delivered_ratio_alt_over_ref_edge_to_edge"] = float(10 ** (-0.4 * fit["ax"]))
        fit["delivered_frac_x"] = object_tilt.as_fraction(fit["ax"])
        fit["delivered_frac_x_err"] = abs(
            object_tilt.as_fraction(fit["ax"] + fit["ax_err"])
            - object_tilt.as_fraction(fit["ax"]))
        fit["delivered_frac_y"] = object_tilt.as_fraction(fit["ay"])
        fit["sigma_x"] = abs(fit["ax"] / fit["ax_err"]) if fit["ax_err"] else None
        fit["lever_px_x"] = fit["lever_frac_x"] * W
        fit["lever_px_y"] = fit["lever_frac_y"] * H
        fit["valid_fraction"] = float(valid.mean())
        fit["centroid_agreement_px"] = {
            "median_abs_dx": float(np.median(np.abs(dx))) if len(dx) else None,
            "median_abs_dy": float(np.median(np.abs(dy))) if len(dy) else None,
            "max_abs_dx": float(np.max(np.abs(dx))) if len(dx) else None,
            "reading": "the same star measured in both arms. A pair that is not "
                       "pixel-aligned separates here before it lies in the fit.",
        }
        np.savez_compressed(os.path.join(work, f"phot_ap{ap}.npz"),
                            m=m, sm=sm, px=px, py=py, W=W, H=H)
        out["apertures"][str(ap)] = fit
    if not args["keep"]:
        for f in os.listdir(work):
            if f.startswith("psf_") and f.endswith(".log"):
                os.remove(os.path.join(work, f))
    return out


# ------------------------------------------------------------------- driver

def run_pair(ref, alt, args):
    work = args["work"]
    os.makedirs(work, exist_ok=True)
    tagr, taga = "ref", "alt"
    ref_ch = split_channels(ref, work, tagr)
    alt_ch = split_channels(alt, work, taga)
    lab = args["label"] or os.path.basename(alt) + "_over_" + os.path.basename(ref)

    field = {}
    for i, c in enumerate(CHANNELS):
        rec = ratio_field(ref_ch[i], alt_ch[i], work,
                          os.path.join(work, f"ratio_{c}.json"), f"{lab}_{c}")
        m = rec["ratio"]["measured"]
        field[c] = {
            "edge": {k: m["edge"][k] for k in
                     ("edge_dipole_x", "edge_dipole_y", "LR", "TB",
                      "corner_ratio", "corner_over_center", "median_ADU")},
            "corner": {k: m["corner"][k] for k in
                       ("edge_dipole_x", "edge_dipole_y", "LR", "TB",
                        "corner_ratio", "corner_over_center", "median_ADU")},
            "no_clip_control_agrees": rec["ratio"].get("no_clip_control", {}).get("agrees"),
            "record": os.path.join(work, f"ratio_{c}.json"),
        }
        if c == CHANNELS[args["layer"]]:
            field[c]["profile_x"] = profile_x(ref_ch[i], alt_ch[i], work, c)

    hdr = fits.getheader(ref)
    hdra = fits.getheader(alt)
    return {
        "label": lab,
        "arm_ref": {"file": ref, "CALFLAT": hdr.get("CALFLAT"),
                    "STACKNRM": hdr.get("STACKNRM", "addscale+output_norm"),
                    "REGPIN": hdr.get("REGPIN"), "DIAGARM": hdr.get("DIAGARM"),
                    "STACKCNT": hdr.get("STACKCNT"), "LIVETIME": hdr.get("LIVETIME"),
                    "canvas": [hdr["NAXIS1"], hdr["NAXIS2"]]},
        "arm_alt": {"file": alt, "CALFLAT": hdra.get("CALFLAT"),
                    "STACKNRM": hdra.get("STACKNRM", "addscale+output_norm"),
                    "REGPIN": hdra.get("REGPIN"), "DIAGARM": hdra.get("DIAGARM"),
                    "CALXSET": hdra.get("CALXSET"),
                    "STACKCNT": hdra.get("STACKCNT"), "LIVETIME": hdra.get("LIVETIME"),
                    "canvas": [hdra["NAXIS1"], hdra["NAXIS2"]]},
        "uptime": object_tilt.uptime(),
        "tool_search": TOOL_SEARCH,
        "instrument": (
            "PRIMARY: Siril fdiv + Siril stat regional medians via the shipped "
            "flat_odd_component.py, per channel (Siril split). CONFIRMING: Siril "
            "findstar (detection + position) + Siril psf aperture photometry at a "
            "forced radius against its own local annulus (setphot), the same star "
            "at the same pixel in both arms; in-house: the subtraction of the two "
            "tool measurements and a weighted straight-line fit against position."),
        "primary_pixel_ratio_field": field,
        "confirming_star_differential": star_differential(ref, alt, work, args),
        "how_to_read":
            "edge_dipole_x is ((TR+BR)-(TL+BL))/2 over the four-corner mean of the "
            "RATIO alt/ref, i.e. the delivered imprint difference. Compare it with "
            "the two flats' own ratio measured by the same instrument: the "
            "delivered field is that ratio SMEARED by the drift, so |delivered| <= "
            "|flat ratio|, and the shortfall is the -framing=min canvas baseline "
            "against the frame's. The star differential answers the same question "
            "on the OBJECT'S OWN FLUX and is independent of it. REPORTED, never "
            "gated.",
    }


# ---------------------------------------------------------------- selftest

def selftest():
    ok = True

    def check(name, cond, detail=""):
        nonlocal ok
        print(("  PASS  " if cond else "  FAIL  ") + name
              + ("   " + detail if detail else ""))
        ok &= bool(cond)

    print("flat_differential --selftest")
    rng = np.random.default_rng(3)
    W = 5769.0
    blocks = [(0, 0, 0), (-253, -19, 0.97), (-516, -58, 1.64), (-779, -105, 2.37)]
    flat = [(0, 0, 0), (-253, -19, 0), (-516, -58, 0), (-779, -105, 0)]

    def arms(bl, planted, rotate=True, seed=7, noise=0.002):
        """One fixture, two arms: the SAME frames, one carrying a flat difference."""
        mA, sm, u, v = object_tilt._panel(3000, bl, 0.0, seed=seed, rotate=rotate)
        d = planted * u + rng.normal(0, noise, u.shape)
        return mA, mA + d, np.full_like(u, noise), u, v

    print(" 1. recovery — a planted flat difference, rotation present")
    for planted in (0.10, -0.04):
        mA, mB, s, u, v = arms(blocks, planted)
        f = fit_differential(mB - mA, s, u, v)
        check(f"planted {planted:+.3f} recovered {f['ax']:+.5f} +- {f['ax_err']:.5f}",
              abs(f["ax"] - planted) < 4 * f["ax_err"])

    print(" 2. null — no planted difference reads zero within its own error")
    mA, mB, s, u, v = arms(blocks, 0.0)
    f0 = fit_differential(mB - mA, s, u, v)
    check(f"ax={f0['ax']:+.6f} +- {f0['ax_err']:.6f}",
          abs(f0["ax"]) < 4 * f0["ax_err"])

    print(" 3. DEGENERACY IMMUNITY — the SAME pure-translation panel that broke")
    print("    the absolute design (object_tilt --selftest 4a), one screen")
    mA, mB, s, u, v = arms(flat, 0.10, rotate=False)
    fabs = object_tilt.fit_tilt(mB, np.full_like(u, 0.01), u, v)
    fdif = fit_differential(mB - mA, s, u, v)
    print(f"       absolute     ax={fabs['ax']:+.4f} +- {fabs['ax_err']:.4f}   "
          f"lever {fabs['lever_frac_x']*W:8.2f} px")
    print(f"       differential ax={fdif['ax']:+.4f} +- {fdif['ax_err']:.4f}   "
          f"lever {fdif['lever_frac_x']*W:8.2f} px")
    check("the absolute instrument does NOT recover the planted 0.100 here",
          abs(fabs["ax"] - 0.10) > 4 * fabs["ax_err"] or fabs["ax_err"] > 0.05,
          "-> the registered blocker, reproduced")
    check(f"and its lever has collapsed to {fabs['lever_frac_x']*W:.2f} px",
          fabs["lever_frac_x"] * W < 1.0)
    check(f"the DIFFERENTIAL recovers it ({fdif['ax']:+.5f}) on that same panel",
          abs(fdif["ax"] - 0.10) < 4 * fdif["ax_err"])
    check(f"because its lever is the CANVAS: {fdif['lever_frac_x']*W:.0f} px",
          fdif["lever_frac_x"] * W > 1000.0)

    print(" 4. FALSIFICATION — break the mechanism, the instrument must go RED")
    print("    4a. blind the position axis (u := 0): a planted difference must die,")
    print("        and step 1's OWN acceptance check must then read RED")
    mA, mB, s, u, v = arms(blocks, 0.10)
    fb = fit_differential(mB - mA, s, np.zeros_like(u), v)

    def recovers(f, planted=0.10):      # step 1's check, applied to any fit
        return abs(f["ax"] - planted) < 4 * f["ax_err"]

    print(f"       blinded:  ax={fb['ax']:+.6f}  ->  recovery check reads "
          f"{'GREEN' if recovers(fb) else 'RED'}")
    check(f"blinded instrument reports ax={fb['ax']:+.6f}", abs(fb["ax"]) < 1e-6)
    check("and the acceptance check it must fail DOES fail", not recovers(fb))
    print("    4b. restore it: the SAME code, the SAME check, must catch it again")
    fr = fit_differential(mB - mA, s, u, v)
    print(f"       restored: ax={fr['ax']:+.6f}  ->  recovery check reads "
          f"{'GREEN' if recovers(fr) else 'RED'}")
    check(f"caught again (ax={fr['ax']:+.5f})", recovers(fr))
    print("    4c. LEVEL is not GRADIENT — a uniform arm-to-arm offset must not")
    print("        move ax (the uniform-card control, in the fit)")
    fu = fit_differential((mB - mA) + 0.0537, s, u, v)
    check(f"ax unchanged to {abs(fu['ax']-fr['ax']):.2e} while the zero point "
          f"moved {fu['zero_points'][0]-fr['zero_points'][0]:+.4f} mag",
          abs(fu["ax"] - fr["ax"]) < 1e-9)
    print("    4d. per-star brightness cannot leak: the differential has NO")
    print("        per-star term because M_i cancelled — re-draw it and check")
    mA2 = mA + rng.uniform(-3, 3, mA.shape[1])[None, :]
    check("ax unchanged when every star's own magnitude is re-drawn",
          abs(fit_differential((mB + (mA2 - mA)) - mA2, s, u, v)["ax"]
              - fr["ax"]) < 1e-12)

    print(" 5. conversions")
    check("ax=0 -> ratio 1.0", abs(10 ** (-0.4 * 0.0) - 1.0) < 1e-12)
    check("g ratio 0.9 round-trips",
          abs(object_tilt.as_fraction(-2.5 * math.log10(0.9)) + 0.1) < 1e-12)

    print("SELFTEST PASS" if ok else "SELFTEST FAIL")
    return 0 if ok else 1


def main(argv):
    if "--selftest" in argv:
        return selftest()
    prof = next((a.split("=", 1)[1] for a in argv if a.startswith("--profile=")), None)
    if prof:
        # the profile instrument alone, on one image — how the delivered field is
        # compared like-for-like against the two flats' own ratio
        outp = next((os.path.abspath(a.split("=", 1)[1]) for a in argv
                     if a.startswith("--json=")), None)
        work = next((os.path.abspath(a.split("=", 1)[1]) for a in argv
                     if a.startswith("--work=")), os.path.dirname(os.path.abspath(prof)))
        os.makedirs(work, exist_ok=True)
        r = profile_x(None, os.path.abspath(prof), work, "single")
        r["image"] = os.path.abspath(prof)
        r["uptime"] = object_tilt.uptime()
        if outp:
            os.makedirs(os.path.dirname(outp), exist_ok=True)
            open(outp, "w").write(json.dumps(r, indent=1) + "\n")
        m = r["median_ratio"]
        print("x:", [round(c) for c in r["x_box_centres"]])
        print("median/first:", [round(v / m[0], 4) for v in m])
        print(f"max|departure from the end-to-end line| {r['max_abs_departure']:.4f}")
        if outp:
            print(f"record: {outp}")
        return 0
    pos = [a for a in argv if not a.startswith("--")]
    if len(pos) != 2:
        print(__doc__)
        return 2
    ref, alt = (os.path.abspath(p) for p in pos)
    args = {"apertures": [10, 16], "inner": 20, "outer": 30, "amin": 0.005,
            "margin": 40, "layer": 1, "roundness": 0.05, "keep": False,
            "label": None, "work": None}
    outp = None
    for a in argv:
        if not a.startswith("--"):
            continue
        if a.startswith("--aperture="):
            args["apertures"] = [float(x) for x in a.split("=", 1)[1].split(",")]
        elif a.startswith("--inner="):
            args["inner"] = float(a.split("=", 1)[1])
        elif a.startswith("--outer="):
            args["outer"] = float(a.split("=", 1)[1])
        elif a.startswith("--amin="):
            args["amin"] = float(a.split("=", 1)[1])
        elif a.startswith("--margin="):
            args["margin"] = int(a.split("=", 1)[1])
        elif a.startswith("--layer="):
            args["layer"] = int(a.split("=", 1)[1])
        elif a.startswith("--roundness="):
            args["roundness"] = float(a.split("=", 1)[1])
        elif a.startswith("--label="):
            args["label"] = a.split("=", 1)[1]
        elif a.startswith("--work="):
            args["work"] = os.path.abspath(a.split("=", 1)[1])
        elif a.startswith("--json="):
            outp = os.path.abspath(a.split("=", 1)[1])
        elif a == "--keep":
            args["keep"] = True
        else:
            print(f"unknown arg {a}", file=sys.stderr)
            return 2
    args["work"] = args["work"] or os.path.join(
        os.path.dirname(outp or ref), "flatdiff_work")
    res = run_pair(ref, alt, args)
    txt = json.dumps(res, indent=1)
    if outp:
        os.makedirs(os.path.dirname(outp), exist_ok=True)
        open(outp, "w").write(txt + "\n")

    print(f"\n{res['label']}")
    print("  PRIMARY — delivered pixel-ratio field (Siril fdiv + stat), edge geometry")
    for c in CHANNELS:
        e = res["primary_pixel_ratio_field"][c]["edge"]
        print(f"    {c}: edge dipole x {e['edge_dipole_x']:+.4f}  y {e['edge_dipole_y']:+.4f}"
              f"   LR {e['LR']:.4f}  TB {e['TB']:.4f}  corner/centre {e['corner_over_center']:.4f}")
    print("  CONFIRMING — matched-star flux differential (Siril psf)")
    sd = res["confirming_star_differential"]
    for ap, f in sd["apertures"].items():
        if "error" in f:
            print(f"    r={ap}px  {f['error']}")
            continue
        # sigma_x is None when ax_err is EXACTLY zero, which is not a failure:
        # it is what the identity control produces when the two arms are
        # bit-identical and every dm_i is exactly 0.
        sig = f"{f['sigma_x']:.1f} sigma" if f["sigma_x"] is not None else "exact zero"
        print(f"    r={ap}px  delivered_x = {100*f['delivered_frac_x']:+.3f}% "
              f"+- {100*f['delivered_frac_x_err']:.3f}%  ({sig})"
              f"   n={f['n_stars']}  lever {f['lever_px_x']:.0f} px")
        ca = f["centroid_agreement_px"]
        print(f"           chi2/dof {f['chi2_per_dof']:.2f}  resid "
              f"{f['resid_rms_mag']:.4f} mag  centroid agreement "
              f"{ca['median_abs_dx']:.3f}/{ca['median_abs_dy']:.3f} px (median |dx|/|dy|)")
    if outp:
        print(f"  record: {outp}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
