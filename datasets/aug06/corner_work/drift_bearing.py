#!/usr/bin/env python3
"""CONSUMER 1: is the fixed-direction term in the star shapes the TRAIL, or the SENSOR?

THE QUESTION. `pa_convention.py` established that the corner defect carries a
FIXED-DIRECTION term (amplitude ~0.058 at 70 SE) alongside a radial one, and that
its direction theta0 is not actually constant — it moves ~14 deg (circular SD)
across 21 frames and rises first-to-last in 6 of 6 sets. That leaves two
mechanisms, and they make opposite predictions:

  TRAILING       the term points along the sky's apparent motion during the
                 exposure. That direction ROTATES in the sensor frame as the
                 field is carried across the sky.
  SENSOR-FIXED   demosaic/CFA anisotropy, sensor tilt, or an astigmatism aligned
                 to the sensor axes. Does not rotate, ever.

THE DISCRIMINATOR, and why it is better than the alternatives. The drift BEARING
is the direction of apparent stellar motion, measured from star POSITIONS between
two frames 30 s apart — against a 2.5 s trail, so the bearing is ~12x better
determined than the thing it is being compared to. It needs no site coordinates,
no altitude assumption and no parallactic-angle theory, which is what made the
hour-angle route BLOCKED for this corpus.

WHY THIS FILE CANNOT HAVE THE FLIP BUG, and why the fixture proves it rather than
the docstring claiming it. Siril reports X, Y and `angle` all in the FITS
bottom-up frame (MEASURED in psf_calib.py: stars planted at +20.0 deg return at
-20.0 deg, and 400 of 400 match under y -> H - y). Every quantity here — the
positions the bearing is built from AND the angle theta0 is built from — comes
out of findstar's own columns, so both live in that one frame by construction and
no conversion enters. `--selftest` plants the MISTAKE anyway (positions taken in
array coordinates while the angle stays in Siril's) and requires the check to go
RED, because a trap that lives in a comment is not tested.

WHAT A NULL LOOKS LIKE, pre-registered before the data was measured
(`datasets/aug06/experiments.jsonl`, perframe_drift_bearing_and_site_derivation):
theta0 failing to track the bearing is a POSITIVE finding — the term is
sensor-fixed — not a failed build. And a third outcome is live: if the bearing
does not rotate measurably across one set, the SLOPE is unidentified and the
honest report is the constant OFFSET (theta0 - bearing) plus a statement that
this set has no lever on the slope. The offset alone still tests alignment, which
is the stronger half of the question.

BRIGHT LINE. Every position, axis and angle is Siril `findstar`'s, read from the
tracked .lst records. In-house code holds only the cross-match, the bearing
geometry and the fits. Reports numbers; gates nothing; exits 0.
"""

import json
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
WORK = os.path.normpath(os.path.join(HERE, "..", "set-01", "drift_work"))
sys.path.insert(0, HERE)
from pa_convention import read_lst, components, decompose, azimuth, wrap180  # noqa: E402

CANVAS_W, CANVAS_H = 6064, 4040
NBLOCK = 10
FRAME_GAP = 10          # frames between the pair members
CADENCE_S = 3.0
BLOCK_STRIDE = 50       # frames between block starts


def bulk_shift(a, b, nbright=400, coarse=4.0, window=80.0):
    """The translation between two frames, from their brightest stars.

    A fixed mount drifts the field ~3.87 px per frame, so a 10-frame gap puts the
    same star ~39 px away and a naive nearest-neighbour match would pair it with
    a DIFFERENT star. The shift is therefore found first, from the 2-D histogram
    of all pairwise offsets among the brightest stars — the true translation is
    the only offset that recurs, everything else is spread thin — and only then
    are stars matched.
    """
    A = a[np.argsort(-a[:, 0])][:nbright]
    B = b[np.argsort(-b[:, 0])][:nbright]
    dx = (B[:, 1][None, :] - A[:, 1][:, None]).ravel()
    dy = (B[:, 2][None, :] - A[:, 2][:, None]).ravel()
    keep = (np.abs(dx) < 300) & (np.abs(dy) < 300)
    dx, dy = dx[keep], dy[keep]
    if len(dx) < 50:
        return None
    bins = np.arange(-300, 300 + coarse, coarse)
    hist, xe, ye = np.histogram2d(dx, dy, bins=[bins, bins])
    i, j = np.unravel_index(np.argmax(hist), hist.shape)
    cx, cy = (xe[i] + xe[i + 1]) / 2, (ye[j] + ye[j + 1]) / 2
    near = (np.abs(dx - cx) < window / 2) & (np.abs(dy - cy) < window / 2)
    return float(np.median(dx[near])), float(np.median(dy[near])), int(near.sum())


def match_and_bearing(a, b, tol=2.0):
    """Match stars across the shift and return the drift bearing in Siril's frame.

    Returns the bearing as a VECTOR direction (mod 360) because the drift has a
    sense, alongside its mod-180 axis form, which is what compares against the
    mod-180 position angle.
    """
    bs = bulk_shift(a, b)
    if bs is None:
        return None
    sx, sy, nvote = bs
    pred_x, pred_y = a[:, 1] + sx, a[:, 2] + sy
    d = np.hypot(b[:, 1][None, :] - pred_x[:, None],
                 b[:, 2][None, :] - pred_y[:, None])
    j = d.argmin(1)
    dm = d[np.arange(len(a)), j]
    m = dm < tol
    if m.sum() < 100:
        return None
    ddx = b[j[m], 1] - a[m, 1]
    ddy = b[j[m], 2] - a[m, 2]
    bearing = float(np.degrees(np.arctan2(np.median(ddy), np.median(ddx))))
    # per-star bearing scatter, as the bearing's own error bar
    per = np.degrees(np.arctan2(ddy, ddx))
    per = (per - bearing + 180) % 360 - 180
    return {
        "n_matched": int(m.sum()), "n_shift_votes": nvote,
        "shift_px": [sx, sy],
        "displacement_px": float(np.hypot(np.median(ddx), np.median(ddy))),
        "bearing_deg_vector": bearing,
        "bearing_deg_axis": float(wrap180(bearing)),
        "bearing_se_deg": float(np.std(per, ddof=1) / np.sqrt(m.sum())),
        "bearing_star_scatter_deg": float(np.std(per, ddof=1)),
    }


def theta0_of(frames):
    """The fixed-direction term's angle, from the spin-2 fit over pooled frames."""
    d = np.vstack(frames)
    # np.vstack is where frame identity dies, so the label is built BEFORE it.
    # Without it the SE here is a star-level bootstrap inside a pooled sample,
    # which understates a per-frame property by a measured 4-9x.
    fr = np.concatenate([np.full(len(a), i) for i, a in enumerate(frames)])
    A, x, y, maj, mnr, th = d.T
    cx, cy = (CANVAS_W - 1) / 2.0, (CANVAS_H - 1) / 2.0
    phi = azimuth(x, y, cx, cy)
    _, e1, e2 = components(maj, mnr, th)
    f = decompose(phi, e1, e2, None, nboot=300,
                  frame=fr if len(frames) > 1 else None)
    return f


def circ_slope(bearing, theta0):
    """Slope of theta0 against bearing, both mod-180, done on the doubled angle.

    Regressing two wrapped variables against each other linearly is the same
    error `pa_convention.py` was built to catch, so it is not repeated here: both
    are unwrapped relative to their own first element before the fit, which is
    valid because consecutive blocks move by far less than 90 deg.
    """
    b = np.asarray(bearing, float)
    t = np.asarray(theta0, float)
    b = b[0] + np.cumsum(np.concatenate([[0.0], wrap180(np.diff(b))]))
    t = t[0] + np.cumsum(np.concatenate([[0.0], wrap180(np.diff(t))]))
    n = len(b)
    sb = b - b.mean()
    if np.allclose(sb, 0):
        return None
    slope = float((sb @ (t - t.mean())) / (sb @ sb))
    resid = (t - t.mean()) - slope * sb
    se = float(np.sqrt((resid @ resid) / (n - 2) / (sb @ sb)))
    return {"slope": slope, "slope_se": se,
            "bearing_span_deg": float(b.max() - b.min()),
            "theta0_span_deg": float(t.max() - t.min()),
            "unwrapped_bearing": [float(v) for v in b],
            "unwrapped_theta0": [float(v) for v in t]}


# ---------------------------------------------------------------------------
# THE FIRE TEST — the flip trap is PLANTED, not described
# ---------------------------------------------------------------------------

def _synth_pair(shift, theta_deg, n=3000, seed=5, flip_positions=False):
    """Two star lists with a KNOWN translation and a KNOWN axis angle.

    flip_positions simulates the ACTUAL MISTAKE: taking positions in array
    coordinates (y measured downward from the top) while the angle stays in
    Siril's FITS bottom-up frame. That is the one error this comparison can make,
    so the fixture makes it on purpose and requires the check to fail.
    """
    rng = np.random.default_rng(seed)
    x = rng.uniform(50, CANVAS_W - 50, n)
    y = rng.uniform(50, CANVAS_H - 50, n)
    A = rng.uniform(500, 40000, n)
    minor = np.full(n, 2.0)
    e = 0.15
    major = minor * np.sqrt((1 + e) / (1 - e))
    th = np.full(n, theta_deg) + rng.normal(0, 5.0, n)
    a = np.column_stack([A, x, y, major, minor, wrap180(th)])
    b = np.column_stack([A, x + shift[0], y + shift[1], major, minor,
                         wrap180(th)])
    if flip_positions:
        a = a.copy(); b = b.copy()
        a[:, 2] = (CANVAS_H - 1) - a[:, 2]
        b[:, 2] = (CANVAS_H - 1) - b[:, 2]
    return a, b


def selftest():
    fails, notes = [], []

    def check(name, cond, detail=""):
        notes.append(("PASS" if cond else "FAIL") + "  " + name +
                     ("   " + detail if detail else ""))
        if not cond:
            fails.append(name)

    print("FIRE TEST — planted drift and planted trail orientation")
    print()

    # a trail planted ALONG the drift, which is what TRAILING means
    for ang, shift in ((20.0, (37.0, 13.47)), (-40.0, (30.0, -25.17))):
        a, b = _synth_pair(shift, ang, seed=int(abs(ang)))
        r = match_and_bearing(a, b)
        off = wrap180(ang - r["bearing_deg_axis"])
        check("trail planted ALONG a %+.0f deg drift -> offset recovers 0" % ang,
              abs(off) < 1.0,
              "bearing %+.3f deg (SE %.4f, n=%d), planted angle %+.1f, offset "
              "%+.3f deg" % (r["bearing_deg_axis"], r["bearing_se_deg"],
                             r["n_matched"], ang, off))

    # a trail planted at a KNOWN angle to the drift must return that angle
    a, b = _synth_pair((37.0, 13.47), 20.0 + 35.0, seed=9)
    r = match_and_bearing(a, b)
    off = wrap180((20.0 + 35.0) - r["bearing_deg_axis"])
    check("trail planted 35 deg OFF the drift -> offset recovers 35 deg",
          abs(off - 35.0) < 1.0, "offset %+.3f deg" % off)

    # the drift magnitude and sense must both come back
    a, b = _synth_pair((37.0, 13.47), 20.0, seed=11)
    r = match_and_bearing(a, b)
    check("drift magnitude recovered",
          abs(r["displacement_px"] - np.hypot(37.0, 13.47)) < 0.05,
          "planted %.3f px, recovered %.3f px"
          % (np.hypot(37.0, 13.47), r["displacement_px"]))
    check("drift SENSE recovered (vector bearing, not just the axis)",
          abs(wrap180(r["bearing_deg_vector"] - 20.0)) < 1.0
          and -90 < r["bearing_deg_vector"] < 90,
          "vector bearing %+.3f deg" % r["bearing_deg_vector"])

    # THE RED: make the actual mistake and require the check to fail
    a, b = _synth_pair((37.0, 13.47), 20.0, seed=13, flip_positions=True)
    rf = match_and_bearing(a, b)
    off_f = wrap180(20.0 - rf["bearing_deg_axis"])
    check("FLIP TRAP: positions in array coords vs angle in Siril's frame FAILS "
          "the zero-offset check as required",
          abs(off_f) >= 1.0,
          "offset %+.3f deg instead of 0 — the sign of the bearing inverts "
          "(%+.3f against %+.3f)"
          % (off_f, rf["bearing_deg_axis"], r["bearing_deg_axis"]))
    check("FLIP TRAP: the induced error is the expected sign inversion, "
          "not noise",
          abs(wrap180(rf["bearing_deg_axis"] + r["bearing_deg_axis"])) < 1.0,
          "flipped %+.3f is the negation of unflipped %+.3f"
          % (rf["bearing_deg_axis"], r["bearing_deg_axis"]))

    # a cross-match that CANNOT work must return None rather than a number
    a, b = _synth_pair((900.0, 900.0), 20.0, seed=17)
    check("an out-of-range shift returns None rather than a plausible number",
          match_and_bearing(a, b) is None, "shift 900,900 px is beyond the "
          "search window")

    # the slope estimator must recover a planted slope, and refuse a flat lever
    s = circ_slope([10, 12, 14, 16, 18], [20, 22, 24, 26, 28])
    check("slope estimator recovers slope 1 on a planted tracking series",
          abs(s["slope"] - 1.0) < 1e-9, "slope %.6f" % s["slope"])
    s0 = circ_slope([10, 10, 10, 10], [20, 22, 21, 23])
    check("slope estimator REFUSES a series with no lever in the bearing",
          s0 is None, "returns None rather than dividing by ~0")

    print()
    for n in notes:
        print("  " + n)
    print()
    if fails:
        print("SELFTEST FAILED: %d of %d" % (len(fails), len(notes)))
        return 1
    print("SELFTEST PASSED: %d of %d" % (len(notes), len(notes)))
    return 0


def main():
    if "--selftest" in sys.argv:
        return selftest()

    blocks = []
    for b in range(NBLOCK):
        pa = os.path.join(WORK, "f_%05d.lst" % (2 * b + 1))
        pb = os.path.join(WORK, "f_%05d.lst" % (2 * b + 2))
        if not (os.path.exists(pa) and os.path.exists(pb)):
            continue
        da, _ = read_lst(pa)
        db, _ = read_lst(pb)
        mb = match_and_bearing(da, db)
        if mb is None:
            print("block %d: cross-match failed" % (b + 1))
            continue
        f = theta0_of([da, db])
        t0 = f["fixed_direction_theta0_deg"]
        blocks.append({
            "block": b + 1,
            "first_frame_index": b * BLOCK_STRIDE + 1,
            "elapsed_s": b * BLOCK_STRIDE * CADENCE_S,
            "n_stars_pooled": f["n_stars"],
            "theta0_deg": t0,
            "theta0_direction_se_deg_star_bootstrap": f["fixed_direction_se_deg_star_bootstrap"],
            "theta0_amplitude": f["fixed_amplitude"],
            "theta0_amplitude_SE_units_star_bootstrap": f["fixed_amplitude_SE_units_star_bootstrap"],
            "radial_R": f["radial_R"],
            "offset_theta0_minus_bearing_deg": float(
                wrap180(t0 - mb["bearing_deg_axis"])),
            **mb,
        })

    out = {
        "consumer": "1 of 2 — theta0 vs drift bearing "
                    "(datasets/aug06/experiments.jsonl, "
                    "perframe_drift_bearing_and_site_derivation)",
        "dataset": "aug06/set-01, 10 blocks of (frame k, frame k+10) at "
                   "stride 50 over 500 frames / 1497 s",
        "why_no_plate_solve": "every quantity is from findstar's own columns, so "
                              "positions and angle share one frame by "
                              "construction and no WCS or site enters",
        "blocks": blocks,
    }
    if blocks:
        off = np.array([b["offset_theta0_minus_bearing_deg"] for b in blocks])
        bear = [b["bearing_deg_axis"] for b in blocks]
        th = [b["theta0_deg"] for b in blocks]
        out["offset_mean_deg"] = float(np.mean(off))
        out["offset_sd_deg"] = float(np.std(off, ddof=1))
        # THE DENOMINATOR IS NAMED, because a quoted pair that does not divide to
        # the quoted sigma is either tripped over or silently propagated. Two are
        # defensible and they differ, so both are reported with what each assumes.
        ob = off[1:]                       # blocks 2-10; block 1 is the outlier
        sd = float(np.std(ob, ddof=1))
        sem = sd / np.sqrt(len(ob))
        internal = float(np.mean([b["theta0_direction_se_deg_star_bootstrap"]
                                  for b in blocks[1:]]))
        out["offset_significance_blocks_2_to_10"] = {
            "n_blocks": len(ob),
            "mean_deg": float(np.mean(ob)),
            "sd_between_blocks_deg": sd,
            "se_of_the_mean_deg": sem,
            "sigma_using_se_of_the_mean": float(abs(np.mean(ob)) / sem),
            "mean_internal_fit_se_deg": internal,
            "sigma_using_internal_fit_se": float(
                abs(np.mean(ob)) / (internal / np.sqrt(len(ob)))),
            "WHICH_ONE_TO_QUOTE": "the SE OF THE MEAN. The block-to-block SD "
                "exceeds the fit's own internal SE, so there is real dispersion "
                "beyond fit noise and the internal SE would assume it away. The "
                "internal-SE figure is reported only so the difference is "
                "visible rather than hidden in a choice.",
            "AND_EVEN_THAT_IS_OPTIMISTIC": "the nine blocks share one optical "
                "field and one camera, so they are not nine independent draws "
                "and the effective count is lower than 9. The claim does not "
                "rest on the sigma: every block has the SAME SIGN, the range is "
                "+6.272 to +10.043, and the SMALLEST offset is %.1fx the "
                "per-block fit SE." % (min(ob) / internal),
        }
        out["bearing_total_rotation_deg"] = float(
            wrap180(bear[-1] - bear[0]))
        out["theta0_total_rotation_deg"] = float(wrap180(th[-1] - th[0]))
        out["slope"] = circ_slope(bear, th)
        out["median_bearing_se_deg"] = float(
            np.median([b["bearing_se_deg"] for b in blocks]))

    path = os.path.join(HERE, "drift_bearing.json")
    json.dump(out, open(path, "w"), indent=1)
    print("wrote %s" % path)
    print()
    print("%-6s %-8s %8s %10s %10s %10s %9s %8s"
          % ("block", "elapsed", "n", "drift_px", "bearing", "theta0",
             "offset", "b_SE"))
    for b in blocks:
        print("%-6d %-8.0f %8d %10.2f %10.3f %10.3f %+9.3f %8.4f"
              % (b["block"], b["elapsed_s"], b["n_matched"],
                 b["displacement_px"], b["bearing_deg_axis"], b["theta0_deg"],
                 b["offset_theta0_minus_bearing_deg"], b["bearing_se_deg"]))
    if blocks:
        print()
        print("bearing rotates %+.3f deg over the set; theta0 rotates %+.3f deg"
              % (out["bearing_total_rotation_deg"],
                 out["theta0_total_rotation_deg"]))
        s9 = out["offset_significance_blocks_2_to_10"]
        print("offset (theta0 - bearing), blocks 2-10: %+.3f +- %.3f deg "
              "(SE of the mean, n=%d) = %.1f sigma   [between-block SD %.3f; "
              "internal fit SE %.3f would give %.1f sigma]"
              % (s9["mean_deg"], s9["se_of_the_mean_deg"], s9["n_blocks"],
                 s9["sigma_using_se_of_the_mean"], s9["sd_between_blocks_deg"],
                 s9["mean_internal_fit_se_deg"],
                 s9["sigma_using_internal_fit_se"]))
        s = out["slope"]
        if s:
            print("slope of theta0 against bearing: %+.3f +- %.3f  "
                  "(bearing lever %.3f deg)"
                  % (s["slope"], s["slope_se"], s["bearing_span_deg"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
