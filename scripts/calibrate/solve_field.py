#!/usr/bin/env python3
"""Blind astrometric solve of a linear stack; optionally inject the WCS.

Usage: solve_field.py <stack.fit> [--inject=<out.fit>] [--json=<wcs.json>]
                     [--ra=<deg> --dec=<deg> [--radius-deg=<N>]] [--central=<frac>]
                     [--field-width-arcmin=<N>] [--scales=<lo>-<hi>]
                     [--max-stars=<N>] [--accept-contradiction]

EXIT 9 = the accepted solution CONTRADICTS the hints this file carries; nothing
is injected and no record is written. It is a user decision, in the chain's gate
family (run_set_chain 2/4/5/6/7/8): re-solve with a correct hint, restrict
detection with --central, or take the solution deliberately with
--accept-contradiction. Exit 1 stays "no solution at all".

--max-stars sets how many detected stars are handed to the solver (default
200). 200 is ample to MATCH a field — the matcher needs only a handful of
quads — but the same list also constrains the solver's SIP distortion fit,
and an order-3 SIP is 20 free parameters per axis. Brightest-first selection
on a Milky-Way field clusters those stars in the band and leaves the corners
carrying almost no constraint, so the polynomial extrapolates freely exactly
where distortion is largest. Raise this when the SOLUTION's distortion terms
are the product being consumed rather than just its position.

--scales overrides the field-derived index-scale set (the operator's
download/breadth control: a narrow field derives scales whose low end
means multi-GB index downloads; the cached mid scales usually carry the
solution — quads 10-50% of the field width are the prime matching range).

Why this exists: Siril's internal solver cannot match this rig's ultra-wide
trailed-star fields (its online cone caps at ~2.5 deg, and with the local
Gaia catalog + correct center it still fails star matching at 52 and 26 deg
FOV). The astrometry.net engine with field-size-derived index scales solves
the same field from 200 peak-detected stars in seconds. SPCC accepts the
injected TAN-SIP WCS.

Position hint: --ra/--dec [+--radius-deg] localizes the search; when absent,
a header RA/DEC (a driven mount's pointing, standard in astrocam FITS) is
used AUTOMATICALLY — it is unverified metadata, so a header-hinted attempt
that fails falls back to BLIND before giving up (a wrong position hint
cannot mis-solve; it just fails, which makes the fallback safe — a CLI hint
is explicit intent and never falls back). A very wide, distorted field can
defeat the blind match: a fast wide lens warps the outer star quads, and
the true field then never surfaces above the all-sky false-match noise. Two
overrides for that case (a wide-field Milky-Way frame at 50 mm/41 deg
needed both): the position hint above, and --central=<frac>.

--central=<frac> keeps the central FRACTION OF THE FRAME — frac=0.5 is the
central half of each axis, i.e. |dx| <= frac*w/2, |dy| <= frac*h/2 — so the
quads it forms come from the low-distortion middle and actually match a TAN
projection. It also excludes the coverage SEAMS of a framing=max union canvas,
which false-detect. The retained box is printed in pixels every run, and frac
outside (0,1) is refused. Reading the flag as a HALF-WIDTH fraction makes
--central=0.5 keep |dx| <= 0.5w — the WHOLE frame — so an invocation reached
for during a failed union solve excludes nothing while reading like a recovery
attempt. Fraction-of-frame is what both this file and finish_render.sh
describe.

THE COVERAGE RUNG — --central IS DERIVED, BUT ONLY AS A RESCUE. When a solve
returns NO SOLUTION or lands FLOOR-CLASS (logodds < LOGODDS_FLOOR) and the
caller named no --central, this measures the canvas's covered region with
scripts/qa/coverage_frame.py (Siril does every pixel read: one `load` plus
`boxselect`+`stat` per grid box), takes the largest CENTRED box inscribed in
the covered rectangle, and re-solves with that fraction. The better of the two
solutions wins, so the rung cannot lower a result it was called to rescue.

WHY A LADDER AND NOT A DERIVED DECISION — measured, same stack, same hint,
--central the only knob:
    probe union   32.7 Mpx   no --central 144   at 0.692 -> 113   (-31)
    night combine 41.6 Mpx   no --central 114   at 0.617 -> 102   (-12)
    four-night    48.2 Mpx   no --central NO SOLUTION  at 0.694 -> 134
All three are framing=max unions carrying uncovered rim BY CONSTRUCTION, so rim
presence cannot decide anything: --central helps one and costs the other two 12
and 31 points. A canvas that already solves confidently never reaches this rung
and therefore cannot be regressed by it — true by construction, not by
measurement. It also means this design never asks what makes a union starve,
which is just as well: BOTH candidates the registry logged for that question
have since been directionally REFUTED (canvas size and seam fraction — see
docs/dead-ends.md). The rung is unaffected either way, because it responds to a
solve that actually starved rather than to a predicted cause.
The derived value BEATS a hand-picked one: on the corpus 0.694 posts 134 where
0.5 posts 106.

AND THE PRODUCT THAT MOTIVATED THIS RUNG NO LONGER NEEDS IT. The four-night
corpus composed against a derived, central registration reference solves at
logodds 507 on the FIRST attempt with no --central at all; the rung never fires.
Its NO SOLUTION was tracking the REFERENCE, not the seams. So this is a GENERAL
SAFETY NET for any union that starves — measured to rescue the old reference's
canvas from NO SOLUTION to 112 (shipped 400 stars) and 134 (200) — and not the
fix for that product. The reference derivation was.

THE FLOOR THE RUNG USES IS UNTUNED BECAUSE THE DATA IS BIMODAL — NOT BECAUSE IT
IS ROBUST. It takes half the covered population's median Siril Min. On all three
canvases measured, boxes are either 0 or >=133 with `edge_band_boxes = 0`, so
every cut from ~30 to ~130 yields the identical rectangle and the floor is
IRRELEVANT rather than validated. A canvas with a GRADED rim — partial-depth
edges instead of a hard covered/empty split — would exercise it, and none of
these three do. That case is UNTESTED.

THE DEPENDENCY IS SOFT BY CONTRACT. A missing, erroring or unusable
coverage_frame.py makes the rung print why and stand down; it never raises. A
rescue path that can itself throw converts a recoverable failure into a hard
error, which is worse than having no rescue.

REMOVAL CONDITION (the coverage rung): retire it the day the astrometry.net
engine itself accepts a detection-region/subarea constraint — the rung exists
because the blind engine consumes the full xylist or nothing, so confining the
solve to the covered region means re-deriving what is handed to it. Registered
in BACKLOG `removal-conditions` (condition authored by audit — the rung
shipped with a LIMITS block and no retirement trigger; RATIFIED by the owner
2026-08-19).

KNOWN LIMIT — THE RUNG IS FOREGROUND-BLIND AND THE DETECTOR IS NOT. The
fraction is derived from `coverage_frame.py`, which measures Siril box Min over
the whole canvas and has NO notion of the terrestrial foreground (zero
references to `astrometrics`, `branch_mask` or `CTX`). `detect_stars_sep`
DOES exclude it — `branch_mask` is applied whenever `CTX.foreground` is set,
which `--session`/`--set` install through `am.configure`. So on a dataset that
declares a foreground the two disagree about what is usable: terrain is bright
and passes the coverage floor, so it counts as covered and INFLATES the derived
fraction, and detection then discards that same region. The rung would hand the
solver a box sized to include ground it cannot use.
LATENT, NOT LIVE: `find datasets -name geometry.json` returns ZERO and no
tracked record declares a foreground, so `CTX.foreground` is None everywhere
today and `keep_mask` stays None. It cannot be exercised until a foreground
exists, which is also why it is recorded rather than fixed — a build-path change
with no way to test it is worse than a stated limit. When a foreground is first
declared, this is the thing to check before trusting a derived `--central`.

WHICH RECORD IS THE DURABLE ONE. The rung writes `<stem>_coverage.json` beside
the product, matching `compose_gate_*.json` and `solve_*.json` — but
`web/results/` is GITIGNORED, so that file is WORKING EVIDENCE and may not
survive. **`SOLVCENT` on the injected artifact is the durable record of the
value used**; the JSON is only the evidence for how it was derived. Do not
re-derive from the JSON a number the header already carries — that is the
failure this repo already paid for, when a composite's registration reference
had to be reconstructed from gate records that outlived their run by luck.

Index scales load CACHED-FIRST: the field-derived set splits into scales
whose index series are fully cached vs those needing download, and the
cached tier is attempted first (a narrow field's derived set reaches the
multi-GB low scales, while the cached mid scales — quads ~10-50% of the
field — usually carry the solution). Only when every cached attempt fails
does the run extend to the download tier, saying so. --scales bypasses the
split (an explicit set, attempted as-is).

Star detection: SExtractor's own core via the `sep` package — official
extraction, shape-blind so trailed sources feed the matcher (20 sigma over
the SExtractor background model, flux-ranked, 25 px de-crowding, brightest
200). The in-house peak-centroid fallback is RETIRED (register condition
fired: sep solved every x86 field at equal-or-higher odds with identical
SPCC K; extractor_ab.json). Solve runs in FITS pixel convention (1-based,
bottom-up rows) so the WCS can be written straight into the file.

Runs inside a private venv (~/.local/share/astrometry-venv) holding the
`astrometry` + `sep` pip packages (bundled astrometry.net engine +
SExtractor core; index files auto-download to the venv dir on first use).
Bootstraps itself: run with plain python3, it creates the venv and
re-execs.
"""
import json
import os
import subprocess
import sys

# scripts/lib holds the shared lib (astrometrics); locate it by
# walking up from this file so one bootstrap works at any nesting depth.
_libdir = os.path.dirname(os.path.abspath(__file__))
while _libdir != os.path.dirname(_libdir):
    if os.path.isdir(os.path.join(_libdir, "lib")):
        sys.path.insert(0, os.path.join(_libdir, "lib"))
        break
    _libdir = os.path.dirname(_libdir)

VENV = os.path.expanduser("~/.local/share/astrometry-venv")
CACHE = os.path.join(VENV, "index-cache")


def bootstrap():
    py = os.path.join(VENV, "bin", "python")
    # compare sys.prefix, not executable realpaths: the venv python is a
    # symlink to the system python, so realpath() says "already inside"
    # while running OUTSIDE the venv and the astrometry import then fails
    if os.path.realpath(sys.prefix) != os.path.realpath(VENV):
        if not os.path.exists(py):
            # PINNED, from scripts/setup/requirements-solve.txt. This used to be
            # a bare `pip install astrometry sep astropy numpy scipy` with NO
            # versions, so a clone got whatever pip resolved that day for the venv
            # holding `sep` — CLAUDE.md's "sole extractor" for the trailed-field
            # solve, with the in-house fallback RETIRED. An unpinned dependency of
            # the solve path is the machine-local-value problem in its most
            # load-bearing place.
            req = os.path.join(os.path.dirname(os.path.dirname(
                os.path.abspath(__file__))), "setup", "requirements-solve.txt")
            print(f"[solve_field] creating venv {VENV} + installing "
                  f"pinned deps from {os.path.relpath(req)} (one-time)")
            subprocess.run([sys.executable, "-m", "venv", VENV], check=True)
            if os.path.exists(req):
                subprocess.run([py, "-m", "pip", "install", "--quiet",
                                "-r", req], check=True)
            else:
                # A checkout without the pin file must say so rather than
                # silently reverting to an unpinned resolve.
                raise SystemExit(
                    f"solve_field: {req} is missing — refusing to bootstrap the "
                    "solve venv unpinned. Restore it from the repo; the solve "
                    "path's extractor version is not a detail.")
        else:
            # bring an older venv up to date with the current defaults
            for pkg in ("sep", "astropy"):
                if subprocess.run([py, "-c", f"import {pkg}"],
                                  capture_output=True).returncode != 0:
                    subprocess.run([py, "-m", "pip", "install", "--quiet", pkg],
                                   check=True)
        os.execv(py, [py] + sys.argv)


def detect_stars_sep(path, central=None, max_stars=200):
    """Official extraction: SExtractor's core (`sep`) — detection,
    deblending and windowed centroids are the tool's own measurement; this
    function only ranks, de-crowds and converts to FITS convention."""
    import astrometrics as am
    import numpy as np
    import sep

    data, _ = am.read_fits(path)
    g = np.ascontiguousarray(
        data[min(1, data.shape[0] - 1)].astype(np.float32))
    h, w = g.shape
    sep.set_extract_pixstack(2_000_000)
    bkg = sep.Background(g)
    obj = sep.extract(g - bkg.back(), thresh=20.0, err=bkg.globalrms)
    obj = np.sort(obj, order="flux")[::-1]
    keep_mask = None
    if am.CTX.foreground is not None:
        from scipy.ndimage import binary_erosion
        keep_mask = binary_erosion(am.branch_mask(h, w), np.ones((49, 49)))
    taken = np.zeros((h // 25 + 2, w // 25 + 2), bool)
    stars = []
    for o in obj:
        x0, y0 = float(o["x"]), float(o["y"])
        # FRACTION OF THE FRAME, not a half-width: frac=0.5 keeps the central
        # half of each axis. See the module docstring — the half-width reading
        # made --central=0.5 a silent no-op.
        if central is not None and (abs(x0 - w / 2) > central * w / 2
                                    or abs(y0 - h / 2) > central * h / 2):
            continue
        if keep_mask is not None and not keep_mask[
                min(h - 1, max(0, int(y0))), min(w - 1, max(0, int(x0)))]:
            continue
        cy, cx = int(y0) // 25, int(x0) // 25
        if taken[max(0, cy - 1):cy + 2, max(0, cx - 1):cx + 2].any():
            continue
        taken[cy, cx] = True
        # FITS convention: 1-based, bottom-up rows
        stars.append((x0 + 1.0, h - y0))
        if len(stars) >= max_stars:
            break
    return stars, h, w


def header_scale(path, width_arcmin=None):
    """NOMINAL pixel scale (arcsec/px) from the FITS header (siril propagates
    FOCALLEN + XPIXSZ from EXIF), or from an explicit --field-width-arcmin.
    None when the header carries neither. ONE source: both the solver's size
    hint and the contradiction gate read this, so they cannot drift apart."""
    from astropy.io import fits
    try:
        hdr = fits.getheader(path)
        if width_arcmin is not None:
            return width_arcmin * 60.0 / float(hdr["NAXIS1"])
        return 206.265 * float(hdr["XPIXSZ"]) / float(hdr["FOCALLEN"])
    except (KeyError, ValueError, OSError):
        return None


def scale_hint(path, width_arcmin=None):
    """Size hint handed to the solver: a deliberately WIDE envelope around the
    header nominal, so a wrong header narrows the search without ever excluding
    the true field. A hard-coded scale range fits only one rig/focal — 26-40"/px
    missed a 24mm field (~44-51"/px), which could never solve. Returns (lo, hi)
    or None (blind). The gate below is TIGHTER on purpose: this bounds where to
    LOOK, the gate judges whether the ANSWER contradicts the header."""
    s = header_scale(path, width_arcmin)
    if s is None:
        return None
    # wide envelope: wide-angle projection + integer-mm EXIF wobble
    return (0.6 * s, 1.5 * s)


# astrometry.net 42xx index scale -> (lo, hi) skymark/quad diameter, arcmin.
# Load index scales whose quad size spans ~7-100% of the field width. The
# low bound sits below the textbook 10% because a wide, star-rich blind
# field matches on quads well under 10% of the full frame (a wide field's
# solution can sit near ~6% of the width, and excluding it gives no
# solution). 0.07*W admits those low scales while still covering the higher
# scales a narrow telescope field needs. A fixed set
# fits only one focal length; loading dense low scales on a wide field just
# grinds — so the window is bounded on BOTH ends.
_SCALE_ARCMIN = {
    0: (2.0, 2.8), 1: (2.8, 4.0), 2: (4.0, 5.6), 3: (5.6, 8.0),
    4: (8.0, 11.0), 5: (11.0, 16.0), 6: (16.0, 22.0), 7: (22.0, 30.0),
    8: (30.0, 42.0), 9: (42.0, 60.0), 10: (60.0, 85.0), 11: (85.0, 120.0),
    12: (120.0, 170.0), 13: (170.0, 240.0), 14: (240.0, 340.0),
    15: (340.0, 480.0), 16: (480.0, 680.0), 17: (680.0, 1000.0),
    18: (1000.0, 1400.0), 19: (1400.0, 2000.0)}
_SCALE_FALLBACK = {13, 14, 15, 16, 17, 18, 19}

# 4200-series tile counts per scale (astrometry.net's healpix split):
# scales 0-4 ship 48 tiles (index-42XX-00..47), 5-7 ship 12, 8+ one file.
# A scale counts as CACHED only when its series is COMPLETE — the solver's
# index_files() silently completes a partial series, i.e. downloads.
_SCALE_TILES = {**{s: 48 for s in range(0, 5)},
                **{s: 12 for s in range(5, 8)},
                **{s: 1 for s in range(8, 20)}}


def scale_cached(s):
    import glob
    d = os.path.join(CACHE, "4200")
    if _SCALE_TILES[s] == 1:
        return os.path.exists(os.path.join(d, f"index-42{s:02d}.fits"))
    return len(glob.glob(os.path.join(d, f"index-42{s:02d}-*.fits"))) \
        >= _SCALE_TILES[s]


def scale_set(path, width_arcmin=None):
    """Index scales to load, derived from the field width (arcsec/px x
    NAXIS1, or an explicit --field-width-arcmin) so any focal length can
    solve. A ~55 deg wide-lens field -> {13..19}; a ~4 deg (500 mm scope)
    field -> {6..14}, which a fixed set could not. When the header
    lacks FOCALLEN/XPIXSZ and no width is given, the WIDE-FIELD scales
    are all that can be loaded (loading every scale grinds) — that
    fallback cannot solve a narrow field, so it warns loudly and names
    the override."""
    from astropy.io import fits
    w_arcmin = width_arcmin
    if w_arcmin is None:
        try:
            hdr = fits.getheader(path)
            w_arcmin = (206.265 * float(hdr["XPIXSZ"]) / float(hdr["FOCALLEN"])
                        * float(hdr["NAXIS1"]) / 60.0)
        except (KeyError, ValueError, OSError):
            print("[solve_field] WARNING: header has no FOCALLEN/XPIXSZ and "
                  "no --field-width-arcmin given — falling back to the "
                  f"WIDE-FIELD index scales {sorted(_SCALE_FALLBACK)} "
                  "(~3-33 deg quads). A narrow (telescope) field CANNOT "
                  "solve on these; pass --field-width-arcmin=<true field "
                  "width> to load the right scales.")
            return set(_SCALE_FALLBACK)
    lo, hi = 0.07 * w_arcmin, 1.0 * w_arcmin      # quads ~7-100% of the field
    sel = {s for s, (a, b) in _SCALE_ARCMIN.items() if b >= lo and a <= hi}
    return sel or set(_SCALE_FALLBACK)


def solve(stars, hint=None, scales=None, pos=None, required=True):
    import astrometry
    scales = set(scales) if scales else set(_SCALE_FALLBACK)
    solver = astrometry.Solver(
        astrometry.series_4200.index_files(
            cache_directory=CACHE, scales=scales))
    print(f"[solve_field] index scales {sorted(scales)} | scale hint: "
          + (f"{hint[0]:.1f}-{hint[1]:.1f} arcsec/px" if hint else "none (blind)")
          + (f" | position hint RA {pos[0]:.1f} Dec {pos[1]:+.1f} r{pos[2]:g} deg"
             if pos else ""))
    sol = solver.solve(
        stars=stars,
        size_hint=(astrometry.SizeHint(hint[0], hint[1]) if hint else None),
        position_hint=(astrometry.PositionHint(
            ra_deg=pos[0], dec_deg=pos[1], radius_deg=pos[2]) if pos else None),
        solution_parameters=astrometry.SolutionParameters(
            sip_order=3,
            # Stop at the first astronomically-confident match instead of
            # grinding every quad of every loaded scale. Field-derived
            # scale sets can be large (dense low scales for narrow fields),
            # and CONTINUE-to-exhaustion makes even a 55-deg field
            # minutes-slow with dense low scales in the set. logodds 100 = odds
            # ~1e43, far above both the ~20.7 default solve floor and the
            # 115-373 these blind solves reach — never stops on a spurious
            # match. The solver hands the callback the running list of match
            # log-odds, so test the best (max) against the threshold.
            logodds_callback=lambda los: (
                astrometry.Action.STOP if max(los) >= 100.0
                else astrometry.Action.CONTINUE)))
    if not sol.has_match():
        if required:
            sys.exit("solve_field: NO SOLUTION")
        return None
    return sol.best_match()


# ---- the contradiction gate ------------------------------------------------
# WHY IT EXISTS, measured on the corpus union: the hinted attempt failed on a
# seam-contaminated framing=max canvas and the BLIND fallback then shipped
# RA 6.03 Dec -65.10 at 12.96"/px, logodds 22.3 — against a header hint of
# RA 309.77 Dec +41.70 r15 and a 17"/px family. Nothing downstream could catch
# it: siril SPCC ran to COMPLETION on that WCS and produced plausible-looking K
# factors (R 1.000 G 0.592 B 0.817, "1790/5153 stars kept") rather than failing,
# so a confident falsehood is one step from the deliverable and the solve is the
# only place it can be stopped. The finish stage proceeded on it until it was
# killed by hand.
#
# The blind fallback stays — it is what solves a field whose header pointing is
# absent or wrong, and a hint that FAILS is not evidence the hint was wrong. What
# changes is that its answer must now survive the hints rather than replace them.

# The hint radius is the declared position uncertainty. Twice it is already
# generous — every hinted solve in this corpus lands within 0.27 deg of a 15 deg
# hint (68 records replayed) — while the measured false solve sat ~110 deg out,
# 7x the radius. So this separates by two orders of magnitude and is not a
# tuned number.
POSITION_RADIUS_FACTOR = 2.0
# Scale tolerance around the header nominal. Budgeted from MECHANISM, not fitted:
# integer-mm EXIF focal (70 +-0.5 mm = +-0.7%), XPIXSZ rounding, a real lens's
# infinity focal differing from its marked value by a few %, and the TAN
# projection's own centre-to-corner scale ratio across a 28.6 deg field
# (1/cos^2(14.3 deg) = 1.066). Those sum to well under 10%; 20% doubles it. The
# corpus then VERIFIES the headroom rather than setting the number: 67 real
# solves span 0.969-0.976 of nominal (a -2.4 to -3.1% systematic, 8x inside the
# band) and the false one sat at 0.740.
SCALE_TOLERANCE = 0.20
# A WARNING, never a refusal: nothing contradicts a solve that had no hint to
# contradict, and a genuinely hard field may legitimately land below this. 100 is
# this file's own confident-match threshold (the logodds_callback stops there);
# all 67 real solves in the corpus cleared it at 103-574, and the false one sat
# at 22.3 — just above astrometry.net's ~20.7 default acceptance floor, which is
# why the engine returned it at all.
LOGODDS_FLOOR = 100.0


def angular_sep_deg(ra1, dec1, ra2, dec2):
    import math
    r = math.radians
    c = (math.sin(r(dec1)) * math.sin(r(dec2))
         + math.cos(r(dec1)) * math.cos(r(dec2)) * math.cos(r(ra1 - ra2)))
    return math.degrees(math.acos(max(-1.0, min(1.0, c))))


def contradictions(match, pos, pos_src, nominal):
    """Every way the accepted solution disagrees with what this file already
    knew, as printable lines. Empty list = no contradiction.

    `pos` is the hint that EXISTED (CLI or header), NOT the winning attempt's —
    those differ exactly in the case this gate is for. In the measured incident
    the record shows `position_hint: null` with `position_hint_source: header`,
    because the hinted attempt failed and the blind fallback won; judging the
    result against the winning attempt's (absent) hint would see nothing wrong.
    """
    out = []
    if pos is not None:
        sep = angular_sep_deg(pos[0], pos[1],
                              match.center_ra_deg, match.center_dec_deg)
        lim = POSITION_RADIUS_FACTOR * pos[2]
        if sep > lim:
            out.append(
                f"POSITION: solved centre RA {match.center_ra_deg:.3f} Dec "
                f"{match.center_dec_deg:+.3f} is {sep:.1f} deg from the "
                f"{pos_src} hint RA {pos[0]:.3f} Dec {pos[1]:+.3f} "
                f"(radius {pos[2]:g} deg) — past {POSITION_RADIUS_FACTOR:g}x "
                f"that radius ({lim:g} deg)")
    if nominal:
        ratio = match.scale_arcsec_per_pixel / nominal
        if abs(ratio - 1.0) > SCALE_TOLERANCE:
            out.append(
                f"SCALE: solved {match.scale_arcsec_per_pixel:.3f} arcsec/px is "
                f"{ratio:.3f}x the header-derived {nominal:.3f} arcsec/px — past "
                f"the +-{SCALE_TOLERANCE:.0%} band "
                f"({(1 - SCALE_TOLERANCE) * nominal:.3f}-"
                f"{(1 + SCALE_TOLERANCE) * nominal:.3f})")
    return out


# --------------------------------------------------------------------------
# THE COVERAGE RUNG's instrument. SOFT BY CONTRACT: every failure path returns
# (None, reason) and never raises, because this sits on a RESCUE path — a
# fallback that can itself throw converts a recoverable solve failure into a
# hard error, which is worse than having no fallback at all.
#
# Every pixel here is Siril's: scripts/qa/coverage_frame.py drives one `load`
# plus `boxselect`+`stat` per grid box and reports the largest all-covered
# rectangle. The in-house part is one geometric step that instrument does not
# provide — the largest CENTRED box inscribed in that rectangle, which is what
# --central takes (it keeps |dx| <= frac*w/2, |dy| <= frac*h/2 about the frame
# centre, so an off-centre rectangle cannot be used directly).
COVERAGE_GRID = "40x26"          # 1040 boxes: ~2 s at 32.7 Mpx, ~3 s at 48.2 Mpx,
                                 # and a frac resolution of ~1/20 per axis, which
                                 # is the +-0.05 this rung needs and no finer.


def _tail(r):
    """Last meaningful line of a failed subprocess — a bare exit code is not a
    diagnosis, and this sits on a path that SKIPS rather than raising, so the
    message is the only trace the failure leaves."""
    for stream in (r.stderr, r.stdout):
        lines = [ln.strip() for ln in (stream or "").splitlines() if ln.strip()]
        if lines:
            return lines[-1][:160]
    return "no output"


def wdir_for(src):
    """The session work dir beside the product, else the product's own dir. Both
    are under $HOME, which the Siril flatpak requires of anything it must read."""
    w = os.path.normpath(os.path.join(os.path.dirname(src), "..", "work"))
    return w if os.path.isdir(w) else (os.path.dirname(src) or ".")


def derive_central_from_coverage(src, workdir):
    """-> (frac, info) or (None, reason). Never raises."""
    cf = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                      "..", "qa", "coverage_frame.py")
    if not os.path.isfile(cf):
        return None, "scripts/qa/coverage_frame.py is not present"
    out = os.path.join(workdir,
                       os.path.splitext(os.path.basename(src))[0] + "_coverage.json")
    try:
        # Pass 1 measures only (no --floor) so the floor is DERIVED from this
        # canvas's own distribution rather than carried in from another.
        # NOTE THE `=`: coverage_frame parses only `--opt=value` (it keeps argv
        # entries containing "="), so `--grid 40x26` silently drops the option
        # AND leaves "40x26" as a positional. Measured: it exits 1.
        r = subprocess.run([sys.executable, cf, src, out, f"--grid={COVERAGE_GRID}"],
                           capture_output=True, text=True, timeout=1800)
        if r.returncode != 0 or not os.path.isfile(out):
            return None, f"coverage_frame exited {r.returncode}: {_tail(r)}"
        rec = json.load(open(out))
        vals = sorted(c["min"].get(rec.get("channel", "Green"), 0.0)
                      for c in rec.get("cells", []))
        nz = [v for v in vals if v > 0.0]
        if not nz or len(nz) == len(vals):
            return None, ("no uncovered box on this canvas — nothing to exclude"
                          if nz else "no covered box at all")
        # THE FLOOR: half the covered population's median Min. It separates two
        # populations rather than sitting on a tuned edge — on the canvases
        # measured here the boxes are 0 or >=133 with ZERO in between, so every
        # cut from ~30 to ~130 gives the same rectangle. See the caveat in the
        # record: that makes the floor IRRELEVANT on bimodal data, not validated.
        floor = 0.5 * nz[len(nz) // 2]
        r = subprocess.run([sys.executable, cf, src, out, f"--grid={COVERAGE_GRID}",
                            f"--floor={floor:.3f}"],
                           capture_output=True, text=True, timeout=1800)
        if r.returncode != 0:
            return None, f"coverage_frame (floored) exited {r.returncode}: {_tail(r)}"
        rec = json.load(open(out))
        W, H = rec["canvas_wh"]
        x, y, bw, bh = rec["rect_fits"]
        cx, cy = W / 2.0, H / 2.0
        hw = min(cx - x, x + bw - cx)
        hh = min(cy - y, y + bh - cy)
        if hw <= 0 or hh <= 0:
            return None, ("the covered rectangle does not contain the frame "
                          "centre — no centred box exists")
        frac = min(2.0 * hw / W, 2.0 * hh / H)
        if not 0.0 < frac < 1.0:
            return None, f"derived fraction {frac:.3f} is not a usable restriction"
        return frac, {"floor": round(floor, 3), "record": out,
                      "covered_frac_of_canvas": rec.get("rect_frac_of_canvas"),
                      "edge_band_boxes": rec.get("edge_band_boxes"),
                      "frac_x": round(2.0 * hw / W, 4),
                      "frac_y": round(2.0 * hh / H, 4),
                      "binding_axis": "y" if (2.0 * hh / H) < (2.0 * hw / W) else "x"}
    except (OSError, ValueError, KeyError, subprocess.SubprocessError) as e:
        return None, f"{type(e).__name__}: {e}"


def inject(src, dst, wcs, logodds, central=None, max_stars=None):
    """Write a WCS-injected copy via astropy: the solver's WCS cards replace any
    existing ones; every other header card and the exact pixel data are preserved
    (do_not_scale_image_data keeps BITPIX/BZERO/BSCALE untouched, so the linear
    stack round-trips unchanged for SPCC).

    SOLVCENT / SOLVMAXS PUT THE RESOLVED DETECTION PARAMETERS ON THE ARTIFACT.
    Both are caller-supplied with a default that is wrong for the deep product,
    and neither was recoverable from the product afterwards: the sidecar
    `solve_<stem>.json` carries `central` but is a SEPARATE file that a copied,
    archived or re-hosted stack does not bring with it, and it never carried
    max-stars at all. MEASURED consequence of not stamping max-stars: the
    four-night corpus solved at logodds 63 (floor-class, against a confident
    floor of 100) because finish_render.sh hardcodes --max-stars=400, and the
    product could not be asked which value it had been solved with.

    SOLVCENT is 0.0 when no --central was applied — the WHOLE frame was
    searched. It is written in both cases: absent-because-unset and
    absent-because-old are otherwise indistinguishable on an artifact.
    """
    from astropy.io import fits
    with fits.open(src, do_not_scale_image_data=True) as hdul:
        hdr = hdul[0].header
        for k in wcs:                        # drop any prior value we replace
            hdr.remove(k, ignore_missing=True, remove_all=True)
        # The solve writes a CD matrix; the stack's own PC+CDELT(+CROTA) must
        # not survive beside it — FITS-WCS declares the forms mutually
        # exclusive, astropy silently prefers the leftover PC+CDELT (measured
        # 0.25 deg centre skew toward the stack's canvas WCS), and siril uses
        # the CD (measured: SPCC on dual vs CD-only, same 1946 stars, same K,
        # output pixels bit-identical — datasets/corpus/
        # wcs_dual_matrix_probe.json).
        for k in list(hdr):
            if k.startswith(("PC1_", "PC2_", "CDELT", "CROTA")):
                hdr.remove(k, ignore_missing=True, remove_all=True)
        hdr.add_comment("WCS injected by solve_field.py "
                        f"(astrometry.net, logodds {logodds:.0f})")
        for k, (v, com) in wcs.items():
            hdr[k] = (v.decode() if isinstance(v, bytes) else v, com)
        hdr["SOLVCENT"] = (float(central or 0.0),
                           "--central fraction; 0 = whole frame")
        hdr["SOLVMAXS"] = (int(max_stars),
                           "--max-stars handed to the solver")
        hdul.writeto(dst, overwrite=True)


def main():
    bootstrap()
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    # `+ [""]` so a BARE flag (--accept-contradiction) parses as an empty value
    # instead of raising on the 1-element split
    opts = dict((a[2:].split("=", 1) + [""])[:2]
                for a in sys.argv[1:] if a.startswith("--"))
    if not args:
        sys.exit(__doc__)
    src = args[0]
    if "session" in opts and "set" in opts:
        import astrometrics as am
        am.configure(opts["session"], opts["set"], quiet=True)
    central = float(opts["central"]) if "central" in opts else None
    if central is not None and not (0.0 < central < 1.0):
        sys.exit(f"solve_field: --central={central:g} is not a fraction of the "
                 "frame in (0,1). 1.0 keeps everything, so it is a no-op that "
                 "reads like a restriction — pass no --central instead. "
                 "(--central=0.5 = the central HALF of each axis.)")
    accept_contradiction = "accept-contradiction" in opts
    max_stars = int(opts.get("max-stars", 200))
    width_arcmin = (float(opts["field-width-arcmin"])
                    if "field-width-arcmin" in opts else None)
    pos, pos_src = None, "none"
    if "ra" in opts and "dec" in opts:
        pos = (float(opts["ra"]), float(opts["dec"]),
               float(opts.get("radius-deg", 15.0)))
        pos_src = "cli"
    else:
        # a driven mount's pointing rides in astrocam FITS headers — an
        # UNVERIFIED hint (it cannot mis-solve, only fail), so a
        # header-hinted failure falls back to blind in the attempt loop
        try:
            from astropy.io import fits as _f
            _h = _f.getheader(src)
            if "RA" in _h and "DEC" in _h:
                pos = (float(_h["RA"]), float(_h["DEC"]),
                       float(opts.get("radius-deg", 15.0)))
                pos_src = "header"
                print(f"[solve_field] position hint from header: RA "
                      f"{pos[0]:.2f} Dec {pos[1]:+.2f} r{pos[2]:g} deg "
                      "(unverified — falls back to blind on failure)")
        except (OSError, ValueError, TypeError):
            pass
    detector = opts.get("detect", "sep")
    if detector != "sep":
        sys.exit(f"solve_field: --detect={detector} is retired — sep "
                 "(SExtractor core) is the sole extractor (BACKLOG register: "
                 "condition fired on x86)")
    fn = detect_stars_sep
    stars, h, w = fn(src, central=central, max_stars=max_stars)
    # Print the RETAINED BOX in pixels, not just the fraction: a restriction
    # that restricts nothing is then impossible to mistake for one that does.
    print(f"[solve_field] {len(stars)} stars via sep (SExtractor core)"
          + (f" (central {central:g} of frame = the middle "
             f"{int(central * w)}x{int(central * h)} px of {w}x{h})"
             if central else ""))
    hint = scale_hint(src, width_arcmin)
    nominal = header_scale(src, width_arcmin)
    if "scales" in opts:
        lo, hi = (int(v) for v in opts["scales"].split("-", 1))
        scales = set(range(lo, hi + 1))
        print(f"[solve_field] index scales OVERRIDDEN to {lo}-{hi} "
              "(--scales; field-derived set not used)")
    else:
        scales = scale_set(src, width_arcmin)
    if "scales" in opts:
        tiers = [("override", scales)]
    else:
        cached = {s for s in scales if scale_cached(s)}
        uncached = sorted(scales - cached)
        if cached and uncached:
            tiers = [("cached", cached), (f"download {uncached}", scales)]
        elif cached:
            tiers = [("cached", cached)]
        else:
            tiers = [(f"download {uncached} (nothing cached)", scales)]
    attempts = []
    for tlabel, tset in tiers:
        attempts.append((tlabel, tset, pos))
        if pos is not None and pos_src == "header":
            attempts.append((f"{tlabel} + blind", tset, None))
    def run_attempts(star_list, tag=""):
        for alabel, aset, apos in attempts:
            print(f"[solve_field] attempt [{alabel}{tag}]")
            mm = solve(star_list, hint=hint, scales=aset, pos=apos, required=False)
            if mm is not None:
                return mm, (alabel + tag, sorted(aset), apos)
        return None, None

    m, winning = run_attempts(stars)

    # ---- THE COVERAGE RUNG ---------------------------------------------------
    # A UNION CANVAS THAT STARVES IS RESCUED BY RESTRICTING DETECTION TO THE
    # COVERED REGION — but only one that starves. MEASURED, same stack, same
    # hint, --central the only knob:
    #     probe  32.7 Mpx   no --central 144   at 0.692 -> 113   (-31)
    #     night  41.6 Mpx   no --central 114   at 0.617 -> 102   (-12)
    #     corpus 48.2 Mpx   no --central NO SOLUTION   at 0.694 -> 134
    # So --central HELPS ONE AND HARMS TWO, and every one of the three is a
    # framing=max union carrying uncovered rim by construction. Rim presence
    # therefore cannot decide whether to apply it, and this is a LADDER rather
    # than a predictor: a canvas that already solves confidently never reaches
    # this rung and cannot be regressed by it. That is true by construction, not
    # by measurement, and it is why this design does not rest on any account of
    # what makes a union starve. It never asks — which is just as well: canvas
    # size and seam fraction were both logged as candidates and both are now
    # directionally refuted (docs/dead-ends.md). The rung responds to a solve
    # that starved, not to a predicted cause, so a wrong account cannot mislead
    # it.
    #
    # The trigger is NO SOLUTION *or* FLOOR-CLASS. A floor-class SUCCESS must
    # escalate too: the corpus returned logodds 63 — a solve, below
    # LOGODDS_FLOOR — and a no-solution-only trigger would ship that unrescued,
    # which is the artifact whose bad solve this rung exists for.
    #
    # The coverage-derived value is not merely safe, it BEATS the hand-picked
    # one: on the corpus 0.694 posts 134 against 0.5's 106.
    #
    # An explicit --central from the caller wins outright and this never runs:
    # a stated restriction is intent, not a default to second-guess.
    coverage_note = None
    if central is None and (m is None or m.logodds < LOGODDS_FLOOR):
        why = "NO SOLUTION" if m is None else f"logodds {m.logodds:.0f} < {LOGODDS_FLOOR:.0f}"
        print(f"[solve_field] {why} — trying the COVERAGE RUNG "
              "(restrict detection to the measured covered region)")
        frac, info = derive_central_from_coverage(src, wdir_for(src))
        if frac is None:
            # SOFT: the rescue path must not turn a recoverable failure into a
            # hard error, so a missing or unhappy instrument is stated and skipped.
            print(f"[solve_field] coverage rung SKIPPED — {info}")
            coverage_note = f"skipped: {info}"
        else:
            print(f"[solve_field] coverage rung: --central={frac:.3f} "
                  f"(covered {info['covered_frac_of_canvas']:.1%} of canvas, "
                  f"binding axis {info['binding_axis']}, floor {info['floor']}, "
                  f"edge-band boxes {info['edge_band_boxes']})")
            stars2, _h2, _w2 = fn(src, central=frac, max_stars=max_stars)
            print(f"[solve_field] {len(stars2)} stars via sep within the "
                  f"central {frac:.3f} of frame")
            m2, winning2 = run_attempts(stars2, tag=" +coverage-central")
            # KEEP THE BETTER, not simply the later: a rescue that lands lower
            # than a floor-class original is not an improvement, and silently
            # preferring it would be a rung that can regress its own input.
            if m2 is not None and (m is None or m2.logodds > m.logodds):
                print(f"[solve_field] coverage rung ACCEPTED "
                      f"({'no prior solution' if m is None else f'{m.logodds:.0f} -> {m2.logodds:.0f}'})")
                m, winning, central = m2, winning2, frac
                coverage_note = {"applied": True, "central": round(frac, 4), **info}
            else:
                got = "no solution" if m2 is None else f"{m2.logodds:.0f}"
                print(f"[solve_field] coverage rung REJECTED — it returned {got}, "
                      f"not better than the existing {m.logodds:.0f}" if m is not None
                      else f"[solve_field] coverage rung REJECTED — {got}")
                coverage_note = {"applied": False, "central_tried": round(frac, 4),
                                 "logodds_tried": (None if m2 is None else round(m2.logodds, 1)),
                                 **info}
    if m is None:
        sys.exit("solve_field: NO SOLUTION")
    print(f"[solve_field] SOLVED: RA {m.center_ra_deg:.3f} "
          f"Dec {m.center_dec_deg:+.3f} scale "
          f"{m.scale_arcsec_per_pixel:.2f} arcsec/px logodds {m.logodds:.0f}")
    # Parity: det(CD) < 0 = the stored image displays SKY-TRUE (east
    # counter-clockwise from north); det > 0 = mirrored vs the sky. The
    # classic cause is top-down camera FITS carrying no ROWORDER keyword
    # ingested under the bottom-up default — self-consistent all the way
    # through, so only the solve can see it. Reported every solve.
    cd = {k: v[0] for k, v in m.wcs_fields.items()
          if k in ("CD1_1", "CD1_2", "CD2_1", "CD2_2")}
    det = (cd.get("CD1_1", 0) * cd.get("CD2_2", 0)
           - cd.get("CD1_2", 0) * cd.get("CD2_1", 0))
    par = "sky-true" if det < 0 else "MIRRORED vs sky"
    print(f"[solve_field] parity: det(CD) {det:+.2e} -> displayed image "
          f"is {par}")

    # ---- the gate: does the accepted solution contradict its own hints? -----
    # BEFORE inject/json/record, so a refused solve leaves NOTHING behind for a
    # later stage to pick up. The measured incident is exactly that: an injected
    # _wcs.fit that SPCC then consumed to completion.
    if m.logodds < LOGODDS_FLOOR:
        print(f"[solve_field] WARNING: logodds {m.logodds:.1f} is below the "
              f"confident-match floor of {LOGODDS_FLOOR:.0f} — this match is "
              "FLOOR-CLASS. Every real solve in this corpus posts 103-574; the "
              "one measured FALSE solve posted 22.3. Treat the position and "
              "scale below as unconfirmed.")
    bad = contradictions(m, pos, pos_src, nominal)
    if bad:
        print("", file=sys.stderr)
        print("solve_field: REFUSING this solution — it CONTRADICTS the hints "
              "this file already carried:", file=sys.stderr)
        for b in bad:
            print(f"    {b}", file=sys.stderr)
        print(f"    accepted attempt [{winning[0]}], logodds {m.logodds:.1f}, "
              f"{len(stars)} stars"
              + (f", central {central:g}" if central else ", no --central"),
              file=sys.stderr)
        if accept_contradiction:
            print("    --accept-contradiction given: PROCEEDING anyway, on the "
                  "operator's explicit say-so.", file=sys.stderr)
        else:
            print("    Nothing injected, no record written. A blind fallback "
                  "can ship a confident falsehood — SPCC ran to completion on "
                  "one and produced plausible K factors — so this stops here.",
                  file=sys.stderr)
            print("    Options: give the right hint (--ra/--dec "
                  "[--radius-deg]); restrict detection to the clean middle "
                  "(--central=<frac of the frame>, which also excludes a "
                  "framing=max union's coverage seams); or take it deliberately "
                  "with --accept-contradiction.", file=sys.stderr)
            sys.exit(9)

    wcs = {k: [v[0] if not isinstance(v[0], bytes) else v[0].decode(), v[1]]
           for k, v in m.wcs_fields.items()}
    if "json" in opts:
        json.dump(wcs, open(opts["json"], "w"), indent=1)
        print(f"[solve_field] wrote {opts['json']}")
    if "inject" in opts:
        inject(src, opts["inject"], wcs, m.logodds,
               central=central, max_stars=max_stars)
        print(f"[solve_field] wrote {opts['inject']} (WCS-injected copy)")
    # durable per-solve record next to the session's other capture files
    # (spcc_run keeps its siril log there the same way; a wrong solve needs
    # an after-the-fact trail: what was detected, hinted, loaded, and found)
    stem = os.path.splitext(os.path.basename(src))[0]
    wdir = wdir_for(src)
    rec = {"input": src, "detector": detector,
           "n_stars_detected": len(stars),
           "central": central, "max_stars": max_stars,
           "coverage_rung": coverage_note,
           "position_hint": winning[2], "position_hint_source": pos_src,
           "attempt": winning[0],
           "field_width_arcmin_arg": width_arcmin,
           "scale_hint_arcsec_px": list(hint) if hint else None,
           # The gate's own evidence, so a later audit replays it from the
           # record instead of re-deriving the nominal from the hint's 0.6x end.
           "header_scale_arcsec_px": nominal,
           "hint_available": list(pos) if pos else None,
           "contradictions": bad,
           "contradiction_accepted": bool(bad) and accept_contradiction,
           "index_scales": sorted(scales), "scales_solved": winning[1],
           "ra_deg": m.center_ra_deg, "dec_deg": m.center_dec_deg,
           "scale_arcsec_px": m.scale_arcsec_per_pixel,
           "logodds": m.logodds,
           "parity": par, "cd_det": det,
           "injected": opts.get("inject")}
    p_rec = os.path.join(wdir, f"solve_{stem}.json")
    json.dump(rec, open(p_rec, "w"), indent=1)
    print(f"[solve_field] record -> {p_rec}")
    # tracked home: when the caller names the dataset, the record also
    # lands in datasets/<session>/<set>/qa_work/ (the versioned measure);
    # the results-side copy stays the UI's product sidecar, regenerated
    # with every solve
    if "session" in opts and "set" in opts:
        repo = os.path.dirname(os.path.dirname(
            os.path.dirname(os.path.abspath(__file__))))
        qa = os.path.join(repo, "datasets", os.path.basename(
            os.path.normpath(opts["session"])), opts["set"], "qa_work")
        os.makedirs(qa, exist_ok=True)
        p_qa = os.path.join(qa, f"solve_{stem}.json")
        json.dump(rec, open(p_qa, "w"), indent=1)
        print(f"[solve_field] tracked record -> {p_qa}")


if __name__ == "__main__":
    main()
