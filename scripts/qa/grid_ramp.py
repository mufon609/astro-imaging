#!/usr/bin/env python3
"""Fit the low-order RAMP of an image over a grid of Siril `stat` boxes.

  grid_ramp.py <image.fit> <out.json> [--ratio=<denom.fit>] [--scalar=0.5]
               [--box=200] [--pitch=550] [--nx=N] [--ny=N] [--layer=1]
               [--label=NAME]
  grid_ramp.py --selftest [--work=DIR]

WHY THIS EXISTS, AND WHY IT IS NOT THE CORNER METRIC. `docs/dead-ends.md`:
"A FOUR-CORNER BOX METRIC IS NOT A GRADIENT MEASURE ON A STRUCTURED FIELD" —
on a Milky-Way field it measures which bit of sky landed in four boxes, and
corner-vs-centre is self-fulfilling for flat contamination by construction. The
registry's named replacement candidate is "the ramp slope fitted over a grid —
reproducible to 7% between independent builds, immune to which sky lands in any
one box, and the term a background-extraction stage actually targets". That
candidate had NO SCRIPT, so the measurement behind a registered finding could
not be re-run. This is that script, at the geometry the finding used: 200 px
boxes on a 550 px pitch about frame centre.

CHANGING AN ACCEPTANCE MEASURE IS A USER RATIFICATION, NOT THIS SCRIPT'S TO
INVENT. This reports the candidate; it replaces nothing, gates nothing, and has
no thresholds (CLAUDE.md: acceptance measures come from the tools and do not
loosen without explicit ratification).

TOOL SEARCH — run as probes on this rig, not reasoned about, because "every
number came from a tool" does not make an in-house analysis in-bounds; what
makes it in-bounds is that no tool does it, and that claim goes stale:
  - siril `bg`            -> ONE scalar for the whole image. No position
                             dependence at all. (`help bg`, Siril 1.4.4.)
  - siril `stat`          -> ADOPTED as the measurement. Regional Mean/Median/
                             Sigma inside a selection; every median here is its.
  - siril `subsky`/`seqsubsky` -> FITS a polynomial or RBF background and
                             SUBTRACTS it, writing an image. It reports no
                             coefficients, so the slope cannot be read out of
                             it. (`help subsky`.)
  - siril `tilt`/`seqtilt`-> WRONG QUANTITY, and probed rather than assumed
                             because the repo's own rule says a GUI-only command
                             may have a headless sibling: `seqtilt` IS
                             scriptable, but both compute "the sensor tilt as
                             the FWHM difference between the best and worst
                             corner truncated mean values" — a STAR-SHAPE
                             measure, not a background level. `tilt` and
                             `inspector` also answer "Can be used in a script:
                             NO".
  - GraXpert 3.0.2 `-bg`  -> writes the background MODEL as an IMAGE; no numeric
                             slope. Also class-blocked on MW-filled fields
                             (registry) and meaningless on a flat RATIO field.
  - ASTAP CLI-2026.07.16  -> `-analyse` reports median HFD + star count,
                             `-extract` exports per-star rows. No background
                             gradient report.
  CONCLUSION: no installed tool reports a fitted background RAMP SLOPE headless.
  Siril measures every box; the in-house part is the least-squares plane over
  the tool's own medians — the same derived-arithmetic shape as the shipped
  `flat_odd_component.py` dipoles.

WHAT IT MEASURES.
  - `slope_x` / `slope_y`: least-squares plane through the box medians,
    normalised to the grid mean, in %/1000 px. On a COMPLETE rectangular grid
    the plane's coefficients equal the two independent 1-D fits exactly (the
    design columns are orthogonal); both are computed and their agreement is
    asserted, so a grid that silently lost a box cannot pass unnoticed.
  - `range_pct`: peak-to-trough over the same medians, the model-free companion.
  - the ratio `|slope_y| / |slope_x|`: vignetting is an EVEN RADIAL function and
    contributes EQUALLY to both axes, so an excess on one axis is non-radial BY
    CONSTRUCTION. That is the whole content of the axis question.

--ratio B divides by B first, with Siril `fdiv` and a RECORDED scalar. `idiv` is
NEVER used: it clips at 1.0 silently, and a ratio of two comparable images
straddles 1.0 by construction (registry — a measured case returned a whole-frame
median of exactly 65535.0). A ratio of two flats from the same night, lens,
focal and aperture cancels vignetting and the instrumental base EXACTLY, so what
the slope then measures is only what DIFFERS between them.

BOX ORIGINS ARE FORCED EVEN. A flat is CFA, so a box's Bayer phase mix must not
depend on where the box landed; an even origin and an even box size give every
box the identical mix.

ORDERING CONTROL, because the medians are parsed from one Siril run in emission
order: the first and last boxes are RE-MEASURED in their own invocations and
must reproduce the batched values exactly. A scrambled parse cannot survive it.

REMOVAL CONDITION: retire the day an official tool reports, headless, the FITTED
low-order background ramp of an image as NUMBERS — a slope or plane coefficients,
not a subtracted image, not a background-model image, and not a star-shape tilt.

REPORTS, GATES NOTHING. No thresholds and no verdict: it writes the numbers, the
geometry they were taken at, the controls, and the reader decides.
"""
import atexit
import json
import math
import os
import re
import subprocess
import sys
import shutil
import tempfile

import numpy as np
from astropy.io import fits

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "..", "lib"))
import siril_run
# ONE definition of how a Siril `stat` line is read, imported rather than copied.
# The copy this replaced could not parse `Sigma: -nan` (a zero-variance crop), and
# a second copy is exactly how one instrument keeps a defect the other has fixed.
from flat_odd_component import STAT


def _run(wdir, lines, tag, expect=None):
    """One Siril invocation; returns its parsed `stat` blocks in emission order."""
    ssf = os.path.join(wdir, f"_{tag}.ssf")
    with open(ssf, "w") as f:
        f.write("requires 1.2.0\nset32bits\nsetcompress 0\nsetext fit\n"
                + "\n".join(lines) + "\n")
    r = siril_run.run(["-d", wdir, "-s", ssf], capture_output=True, text=True)
    out = r.stdout + r.stderr
    os.remove(ssf)
    if r.returncode != 0:
        sys.exit(f"siril failed ({tag}):\n{out[-3000:]}")
    stats = [m.groups() for m in STAT.finditer(out)]
    if expect is not None and len(stats) != expect:
        sys.exit(f"{tag}: parsed {len(stats)} stat blocks, expected {expect}. "
                 f"An all-zero region reports 'all nil' and yields none.\n"
                 f"{out[-3000:]}")
    return stats


def grid_geometry(w, h, box, pitch, nx=None, ny=None):
    """Boxes centred on the frame centre, origins forced EVEN (CFA phase)."""
    if nx is None:
        nx = max(1, (w - box) // pitch + 1)
        nx -= 1 - nx % 2                      # keep it odd so one column is central
    if ny is None:
        ny = max(1, (h - box) // pitch + 1)
        ny -= 1 - ny % 2
    if (nx - 1) * pitch + box > w or (ny - 1) * pitch + box > h:
        sys.exit(f"grid {nx}x{ny} at box {box} / pitch {pitch} does not fit {w}x{h}")
    x0 = (w - ((nx - 1) * pitch + box)) // 2
    y0 = (h - ((ny - 1) * pitch + box)) // 2
    x0 -= x0 % 2
    y0 -= y0 % 2
    boxes = [(x0 + i * pitch, y0 + j * pitch, i, j)
             for j in range(ny) for i in range(nx)]
    return nx, ny, boxes


def fit_plane(x, y, v):
    """LS plane v = c + bx*x + by*y over the box medians, plus the two 1-D fits.

    The in-house part of this instrument, and all of it: Siril measured every
    v. Slopes are returned normalised to the grid mean and scaled to %/1000 px.
    """
    x, y, v = np.asarray(x, float), np.asarray(y, float), np.asarray(v, float)
    mean = float(v.mean())
    if mean == 0:
        sys.exit("grid mean is zero — cannot normalise a slope to it")
    A = np.stack([np.ones_like(x), x, y], axis=-1)
    beta, *_ = np.linalg.lstsq(A, v, rcond=None)
    resid = v - A @ beta
    out = {
        "slope_x_pct_per_1000px": 100.0 * beta[1] * 1000.0 / mean,
        "slope_y_pct_per_1000px": 100.0 * beta[2] * 1000.0 / mean,
        "intercept_ADU": float(beta[0]),
        "grid_mean_ADU": mean,
        "range_pct": 100.0 * (float(v.max()) - float(v.min())) / mean,
        "resid_rms_pct": 100.0 * float(np.sqrt((resid ** 2).mean())) / mean,
        "n_boxes": int(v.size),
    }
    # the two independent 1-D fits: identical to the plane on a COMPLETE grid,
    # so disagreement means the grid is not the rectangle it claims to be.
    # A position column with NO spread carries no slope at all — polyfit raises
    # a bare LinAlgError there, which is exactly the state the falsification
    # step drives the instrument into, so it is handled rather than crashed on.
    for pos, key in ((x, "x"), (y, "y")):
        if float(np.ptp(pos)) == 0.0:
            out[f"slope_{key}_1d_pct_per_1000px"] = 0.0
            out[f"axis_{key}_degenerate"] = True
            continue
        p = np.polyfit(pos, v, 1)
        out[f"slope_{key}_1d_pct_per_1000px"] = 100.0 * p[0] * 1000.0 / mean
    out["plane_vs_1d_agree"] = all(
        abs(out[f"slope_{k}_pct_per_1000px"] - out[f"slope_{k}_1d_pct_per_1000px"])
        <= 1e-6 + 1e-4 * abs(out[f"slope_{k}_pct_per_1000px"]) for k in ("x", "y"))
    sx, sy = out["slope_x_pct_per_1000px"], out["slope_y_pct_per_1000px"]
    out["axis_ratio_y_over_x"] = abs(sy) / abs(sx) if sx else None
    out["dominant_axis"] = ("T/B" if abs(sy) > abs(sx) else "L/R")
    return out


def measure(img, wdir, tag, box, pitch, nx=None, ny=None, is_ratio=False):
    hdr = fits.getheader(img)
    w, h = int(hdr["NAXIS1"]), int(hdr["NAXIS2"])
    if int(hdr.get("NAXIS3", 1)) != 1:
        sys.exit(f"{img} has {hdr['NAXIS3']} layers — extract one with Siril "
                 "`split` first (this instrument measures a mono plane, so a "
                 "per-channel parse can never mis-attribute a box)")
    # THE GUARD ABOVE COULD NOT SEE THE CASE IT IS WORDED TO PREVENT. A CFA MOSAIC
    # IS NAXIS=2 with four filters INTERLEAVED, so it passes a NAXIS3 check while
    # every box median blends R/G/G/B into one number — exactly the
    # "mis-attribute a box" failure that wording promises to exclude.
    #
    # BUT THE BLEND IS ONLY HARMFUL IN ABSOLUTE MODE, WHICH IS WHY PRODUCTION USES
    # --ratio. `fdiv` divides pixel by pixel, so in a ratio each pixel is
    # same-filter over same-filter and a box median averages four filters' RATIOS,
    # which sit near unity when the two images share optics. In ABSOLUTE mode the
    # same median averages four filters' LEVELS, and a sky flat is the worst case:
    # the sky has COLOUR, `sky x V` is the term being chased, and a
    # colour-dependent gradient would collapse into one achromatic ramp silently.
    #
    # MEASURED, and it is why absolute mode is REFUSED rather than warned: on
    # aug06/set-01's sky flat the plane leaves an rms residual of 15.9% against a
    # range of 69.6% — a sky flat is dominated by RADIAL vignetting, a plane is not
    # a radial model, and the fitted slope is read off a large unmodelled bowl.
    if str(hdr.get("BAYERPAT", "")).strip() and not is_ratio:
        sys.exit(f"{img} carries BAYERPAT={hdr['BAYERPAT']} — CFA MOSAIC in "
                 "ABSOLUTE mode. Box medians would blend R/G/G/B levels, and on a "
                 "sky flat the plane also fits through an unmodelled radial bowl "
                 "(measured 15.9% rms residual against a 69.6% range). Use --ratio "
                 "against a sibling from the same night and lens, which cancels "
                 "both; or debayer and pass a single channel.")
    nx, ny, boxes = grid_geometry(w, h, box, pitch, nx, ny)
    lines = []
    for (x, y, _i, _j) in boxes:
        lines += [f"load {img}", f"crop {x} {y} {box} {box}", "stat"]
    stats = _run(wdir, lines, f"grid_{tag}", expect=len(boxes))
    med = [float(s[1]) for s in stats]
    # ORDERING CONTROL: the two extreme boxes, each in its OWN invocation
    ctl = {}
    for name, idx in (("first", 0), ("last", len(boxes) - 1)):
        x, y, _i, _j = boxes[idx]
        s = _run(wdir, [f"load {img}", f"crop {x} {y} {box} {box}", "stat"],
                 f"ord_{tag}_{name}", expect=1)
        ctl[name] = {"box_xy": [x, y], "batched": med[idx],
                     "standalone": float(s[0][1]),
                     "agrees": abs(float(s[0][1]) - med[idx]) <= 1e-9}
    if not all(c["agrees"] for c in ctl.values()):
        sys.exit(f"ORDERING CONTROL FAILED on {img}: a box re-measured alone "
                 f"disagrees with its batched value — the emission-order parse "
                 f"is not aligned with the boxes. {json.dumps(ctl)}")
    fit = fit_plane([b[0] + box / 2.0 for b in boxes],
                    [b[1] + box / 2.0 for b in boxes], med)
    return {
        "image_wh": [w, h],
        "geometry_px": {"box": box, "pitch": pitch, "nx": nx, "ny": ny,
                        "origin_forced_even": True,
                        "note": "200/550 about frame centre is the geometry the "
                                "registry's background-residual decomposition "
                                "used (63 boxes on a 6064x4040 frame)"},
        "box_median_ADU": med,
        "box_centres_xy": [[b[0] + box / 2.0, b[1] + box / 2.0] for b in boxes],
        "fit": fit,
        "ordering_control": ctl,
    }


def main(argv):
    args = [a for a in argv if not a.startswith("--")]
    opts = dict(a[2:].split("=", 1) for a in argv if a.startswith("--") and "=" in a)
    if len(args) != 2:
        sys.exit(__doc__)
    img, out_json = os.path.abspath(args[0]), os.path.abspath(args[1])
    box, pitch = int(opts.get("box", 200)), int(opts.get("pitch", 550))
    nx = int(opts["nx"]) if opts.get("nx") else None
    ny = int(opts["ny"]) if opts.get("ny") else None
    scalar = float(opts.get("scalar", 0.5))
    other = os.path.abspath(opts["ratio"]) if opts.get("ratio") else None
    wdir = os.path.dirname(out_json)
    os.makedirs(wdir, exist_ok=True)

    rec = {
        "tool": "Siril 1.4.4 — load / crop / stat regional medians (and fdiv for "
                "--ratio); every pixel op and every measurement is Siril's. "
                "In-house: the least-squares plane over the tool's own medians.",
        "image": img,
        "uptime": subprocess.run(["uptime"], capture_output=True,
                                 text=True).stdout.strip(),
        "how_to_read":
            "Vignetting is EVEN and RADIAL, so it contributes EQUALLY to the x "
            "and y slopes. An excess on one axis is NON-RADIAL by construction "
            "and cannot be vignetting. Slopes are %/1000 px normalised to the "
            "grid mean; range_pct is the model-free peak-to-trough over the same "
            "medians. REPORTED, never gated — this is the registry's CANDIDATE "
            "gradient measure, and swapping an acceptance measure is a user "
            "ratification.",
    }
    if opts.get("label"):
        rec["label"] = opts["label"]

    target = img
    if other:
        tmp = os.path.join(wdir, f"_gridratio_{os.getpid()}")
        _run(wdir, [f"load {img}", f"fdiv {other} {scalar}", f"save {tmp}"],
             "mkratio")
        target = tmp + ".fit"
        rec["ratio"] = {
            "numerator": img, "denominator": other, "scalar": scalar,
            "never_idiv": "idiv clips at 1.0 silently and a ratio of two "
                          "comparable images straddles 1.0 by construction "
                          "(docs/dead-ends.md). fdiv only, scalar recorded.",
            "why": "a ratio of two flats from the same night/lens/focal/aperture "
                   "cancels vignetting and the instrumental base EXACTLY — no "
                   "model, no fit. What survives is what DIFFERS."}
    rec["measured"] = measure(target, wdir, "t", box, pitch, nx, ny,
                              is_ratio=other is not None)
    if other:
        os.remove(target)

    with open(out_json, "w") as f:
        json.dump(rec, f, indent=1)
    f_ = rec["measured"]["fit"]
    g = rec["measured"]["geometry_px"]
    print(f"grid {g['nx']}x{g['ny']} box {g['box']} pitch {g['pitch']} "
          f"({f_['n_boxes']} boxes)")
    print(f"  slope_x {f_['slope_x_pct_per_1000px']:+.4f} %/1000px   "
          f"slope_y {f_['slope_y_pct_per_1000px']:+.4f} %/1000px   "
          f"|y|/|x| {f_['axis_ratio_y_over_x']:.2f} -> {f_['dominant_axis']} dominant")
    print(f"  range {f_['range_pct']:.4f} %   plane residual rms "
          f"{f_['resid_rms_pct']:.4f} %   plane-vs-1d {f_['plane_vs_1d_agree']}")
    print(f"  record: {out_json}")
    return 0


# ---------------------------------------------------------------- selftest

def selftest(work):
    """Falsify the mechanism in process: break it, watch it go RED, restore."""
    ok = True

    def check(name, cond, detail=""):
        nonlocal ok
        print(("  PASS  " if cond else "  FAIL  ") + name
              + ("   " + detail if detail else ""))
        ok &= bool(cond)

    print("grid_ramp --selftest")
    os.makedirs(work, exist_ok=True)

    print(" 1. the fit recovers a planted plane exactly (arithmetic)")
    auto = grid_geometry(6064, 4040, 200, 550)
    check(f"auto geometry FILLS the frame: 11x7 on 6064x4040 (got "
          f"{auto[0]}x{auto[1]}, span {(auto[0]-1)*550+200} of 6064 px)",
          (auto[0], auto[1], len(auto[2])) == (11, 7, 77))
    nx, ny, boxes = grid_geometry(6064, 4040, 200, 550, nx=9, ny=7)
    cx = np.array([b[0] + 100.0 for b in boxes])
    cy = np.array([b[1] + 100.0 for b in boxes])
    check(f"explicit 9x7 reproduces the registry's 63 boxes (got {nx}x{ny}, "
          f"{len(boxes)})", (nx, ny, len(boxes)) == (9, 7, 63))
    base, kx, ky = 30000.0, 0.15, -0.60      # %/1000px, planted
    v = base * (1 + kx / 100 / 1000 * (cx - cx.mean())
                + ky / 100 / 1000 * (cy - cy.mean()))
    f = fit_plane(cx, cy, v)
    check(f"planted x {kx:+.2f} recovered {f['slope_x_pct_per_1000px']:+.5f}",
          abs(f["slope_x_pct_per_1000px"] - kx) < 1e-6)
    check(f"planted y {ky:+.2f} recovered {f['slope_y_pct_per_1000px']:+.5f}",
          abs(f["slope_y_pct_per_1000px"] - ky) < 1e-6)
    check("plane and the two 1-D fits agree on a complete grid",
          f["plane_vs_1d_agree"])
    check(f"axis call is T/B at |y|/|x| = {f['axis_ratio_y_over_x']:.2f}",
          f["dominant_axis"] == "T/B")

    print(" 2. FALSIFICATION — blind the position axis, the planted slope must die")
    print("    and the step-1 acceptance check must then read RED")

    def recovers(fit):                       # step 1's own check, reapplied
        return abs(fit["slope_x_pct_per_1000px"] - kx) < 1e-6

    fb = fit_plane(np.zeros_like(cx), cy, v)
    print(f"       blinded:  slope_x {fb['slope_x_pct_per_1000px']:+.6f}  ->  "
          f"recovery check reads {'GREEN' if recovers(fb) else 'RED'}")
    check("blinded instrument reports slope_x 0",
          abs(fb["slope_x_pct_per_1000px"]) < 1e-12)
    check("and the acceptance check it must fail DOES fail", not recovers(fb))
    fr = fit_plane(cx, cy, v)
    print(f"       restored: slope_x {fr['slope_x_pct_per_1000px']:+.6f}  ->  "
          f"recovery check reads {'GREEN' if recovers(fr) else 'RED'}")
    check("the SAME check catches it again once restored", recovers(fr))

    print(" 3. LEVEL is not GRADIENT — a uniform scale must not move a slope")
    fu = fit_plane(cx, cy, v * 1.05)
    check("slopes unchanged under a 5% uniform scale",
          abs(fu["slope_x_pct_per_1000px"] - fr["slope_x_pct_per_1000px"]) < 1e-9
          and abs(fu["slope_y_pct_per_1000px"] - fr["slope_y_pct_per_1000px"]) < 1e-9)
    fz = fit_plane(cx, cy, np.full_like(v, 12345.0))
    check("a perfectly uniform field reads slope 0 on both axes and range 0",
          abs(fz["slope_x_pct_per_1000px"]) < 1e-12
          and abs(fz["slope_y_pct_per_1000px"]) < 1e-12
          and abs(fz["range_pct"]) < 1e-12)

    print(" 4. END TO END through Siril on a synthetic card (plumbing + parse order)")
    W, H, K = 2000, 1400, 0.20
    card = os.path.join(work, "card_ramp.fit")
    x = np.arange(W, dtype=np.float32)
    ramp = (10000.0 * (1.0 + K * (x / float(W) - 0.5))).astype(np.float32)
    fits.PrimaryHDU(np.broadcast_to(ramp, (H, W)).astype(np.float32)).writeto(
        card, overwrite=True)
    m = measure(card, work, "st", 200, 550)
    # analytic: a linear ramp of full-frame amplitude K about the mean
    expect = 100.0 * K / float(W) * 1000.0
    got = m["fit"]["slope_x_pct_per_1000px"]
    check(f"Siril-measured slope_x {got:+.5f} matches the analytic "
          f"{expect:+.5f} %/1000px", abs(got - expect) < 1e-3 * abs(expect) + 1e-6)
    check(f"slope_y is nil on an x-only ramp "
          f"({m['fit']['slope_y_pct_per_1000px']:+.2e})",
          abs(m["fit"]["slope_y_pct_per_1000px"]) < 1e-6)
    check("the ordering control ran and agreed on both extreme boxes",
          all(c["agrees"] for c in m["ordering_control"].values()))

    print(" 5. the ORDERING CONTROL itself is falsified — scramble the parse and")
    print("    it must refuse")
    scrambled = dict(m["ordering_control"]["first"])
    scrambled["standalone"] = scrambled["batched"] * 1.0001
    scrambled["agrees"] = abs(scrambled["standalone"] - scrambled["batched"]) <= 1e-9
    check("a 0.01% disagreement is caught by the control's own test",
          not scrambled["agrees"])

    uni = os.path.join(work, "card_uniform.fit")
    fits.PrimaryHDU(np.full((H, W), 10000.0, dtype=np.float32)).writeto(
        uni, overwrite=True)
    mu = measure(uni, work, "stu", 200, 550)
    check(f"a UNIFORM card through the whole Siril path reads slope 0/0 "
          f"({mu['fit']['slope_x_pct_per_1000px']:+.2e} / "
          f"{mu['fit']['slope_y_pct_per_1000px']:+.2e})",
          abs(mu["fit"]["slope_x_pct_per_1000px"]) < 1e-9
          and abs(mu["fit"]["slope_y_pct_per_1000px"]) < 1e-9)
    for p in (card, uni):
        os.remove(p)

    print("SELFTEST PASS" if ok else "SELFTEST FAIL")
    return 0 if ok else 1


if __name__ == "__main__":
    argv = sys.argv[1:]
    if "--selftest" in argv:
        # PER-RUN dir, NOT a fixed shared one. MEASURED RACE: a fixed path plus an
        # entry-time rmtree let two concurrent runs clobber each other mid-flight —
        # run A wrote a fixture, run B re-entered and wiped the dir, run A's siril
        # then failed to load a file that had existed seconds earlier. Reproduced:
        # two concurrent selftests -> one exit 1 (FileNotFoundError), one exit 0.
        # siril_run's flock serialises the TOOL CALL; it does not cover the
        # DIRECTORY LIFECYCLE around it. Stays under $HOME: the Siril flatpak has a
        # private /tmp, so a fixture in a system temp dir is invisible to the tool.
        explicit = next((a.split("=", 1)[1] for a in argv
                         if a.startswith("--work=")), None)
        if explicit:
            w = explicit
        else:
            os.makedirs(os.path.expanduser("~/.cache/astro-imaging"), exist_ok=True)
            w = tempfile.mkdtemp(prefix="grid_ramp_selftest.", dir=os.path.expanduser("~/.cache/astro-imaging"))
            atexit.register(shutil.rmtree, w, True)
        # under $HOME deliberately: the Siril flatpak has a private /tmp, so a
        # fixture written to a scratchpad there is invisible to the tool
        sys.exit(selftest(os.path.abspath(w)))
    sys.exit(main(argv))
