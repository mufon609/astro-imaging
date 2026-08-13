#!/usr/bin/env python3
"""Starlight-preservation instrument: does a background step still leave the
frame-filling UNRESOLVED STARLIGHT this field is made of?

The adoption gate for the render-stage background question (L1) is
"preservation of the frame-filling unresolved starlight", and nothing in the
tree measured it. This measures it, and it MEASURES ONLY — no threshold, no
verdict, no exit code that blocks anything, and it rewrites no product. What
counts as enough preservation is the owner's call on the finals.

  Usage: starlight_preservation.py <solved.fit> <out.json>
                                   [--cells=14x10] [--margin=0] [--gsplit=11]
                                   [--baseline=<ctrl.json>] [--offline]
         starlight_preservation.py --selftest [--keep]

THE MEASUREMENT.  On a plate-solved LINEAR surface, over an EXTERNAL lattice of
cells fixed in the image and mapped to sky by the header WCS:

  y_i   Siril `stat` MEDIAN of cell i — the cell's diffuse floor, in ADU.
  x_i   Gaia DR3's integrated flux from sources FAINTER than the detection
        limit inside cell i, per square degree — the unresolved-starlight
        prediction, from the ESA Gaia archive's own aggregate.

and then the regressions no tool provides: y on x; and, because `subsky 1`
removes a plane and `subsky 2` removes a quadratic, y-minus-its-own-fitted-plane
on x and y-minus-its-own-fitted-quadratic on x. Those last two are the degree
question stated as a measurement — the starlight relation that SURVIVES an
operator of that degree.

Run it on the control and on each arm with `--baseline` and read the PAIRED
retained fraction: the two arms see the same sky through the same cells, so the
field's own structure cancels in the per-cell difference and the comparison is
far sharper than either absolute slope. MEASURED on aug06/set-01, 140 cells: an
absolute slope carries a 22-28% standard error (it can only resolve a 43-55%
attenuation at 2 sigma) while the paired difference resolves 5-16%. Same
mechanism as `flat_differential.py`, whose selftest measures the absolute fit
failing where the differential succeeds.

AND ONE NUMBER THAT NEEDS NO IMAGE — `catalogue_absorbable`. `subsky d` removes
a degree-d surface, so the most it can take from the starlight is the fraction
of the PREDICTOR's own spatial variance a degree-d surface can represent. That
is a property of the catalogue over the lattice, so no instrumental term can
move it, and it is the honest way to bound the degree question. On aug06/set-01
(23.3 x 17.1 deg, 140 cells): plane 10.0%, quadratic 36.2%, cubic 43.5%.

WHY GAIA AND NOT JUST "HOW MUCH STRUCTURE IS LEFT".  A background step removes
structure by construction; the question is WHICH structure. Gaia is the
external reference that separates "it ate the gradient" from "it ate the
starlight". Without it the instrument would be keyed to the very signal under
test.

WHY THE LATTICE IS EXTERNAL.  Cells are a fixed grid in image coordinates,
never derived from detections, so they cannot move with the defect being
measured. `docs/dead-ends.md` trap 3 is the measured cost of the alternative: a
binning origin inferred from the detections moved WITH the defect and flattened
the profile as the defect got worse. With `--baseline` the arm inherits the
control's cells verbatim, so both arms are read on ONE lattice.

WHAT THE TOOLS DO vs WHAT IS IN-HOUSE (the bright line, `CLAUDE.md`):

  Siril 1.4.4   `load` + `boxselect` + `stat` — every pixel is read by Siril and
                every per-cell number (mean/median/sigma/min/max/bgnoise) is
                Siril's. PROBED, not assumed: `boxselect`+`stat` returns values
                identical to the `crop`+`stat` route `regional_stat.py` already
                uses, to every printed digit, in ONE load instead of N.
                (`jsonmetadata -stats_from_loaded` does NOT honour a selection —
                probed, it stats the whole frame — so `stat`'s log line is the
                only per-cell surface.)
  Gaia DR3      the ESA archive's TAP service does the catalogue aggregation
                server-side: per-cell counts and summed G flux binned by
                magnitude. The magnitude split is applied to the archive's own
                bins, so no source-level arithmetic happens here.
  in-house      the lattice bookkeeping, the WCS projection of cell corners
                (header data, no pixels), and the least-squares fits above.
                NO pixel of any image is read by this file.

`boxselect` COUNTS y FROM THE TOP — the opposite of the FITS row order astropy
addresses, so a cell's sky position and its selection differ by
`y_select = H - y_fits - h`. MEASURED, not inferred: a 200x400 ramp whose pixel
value equals its FITS row index reads Median 374.0 at `boxselect 0 0 200 50` and
Median 25.0 at `boxselect 0 350 200 50` — the first selection returns the LAST
rows on disk. Getting this wrong is not a small error and it does not look like
one: the first run of this instrument's own positive control recovered 54% of a
planted relation at R2 0.30, because a mirrored lattice still half-correlates
with a pattern that is roughly symmetric about the frame centre. The convention
is pinned here and re-verified by `--selftest` step 1, which goes RED if a Siril
change ever flips it.
REMOVAL CONDITION: an official tool reports, headless, the agreement between a
star catalogue's predicted diffuse surface brightness and an image's own
measured per-region background — i.e. the JOINT, not the two halves. Probed on
this rig, none does: Siril `stat`/`bg`/`bgnoise` measure the image only and
`conesearch` returns the catalogue only (and at this field size it is not even
usable — 20.6 deg radius at G<=17 against TAPVizieR, killed at 600 s with no
output); `source-extractor` 2.28.2 `-CHECKIMAGE_TYPE BACKGROUND` writes a local
background MAP (1.7 s on a 4907x3598 stack) but compares it to nothing;
GraXpert 3.0.2 `-bg` writes a background MODEL image; ASTAP CLI-2026.07.16
`-analyse`/`-extract` report HFD, star counts and per-star rows. Register row in
BACKLOG:`removal-conditions`.

SCOPE LIMITS, stated because they bound every number this prints:
 1. The predictor is degenerate with position at low order. Galactic latitude
    runs diagonally across this field, so a plain plane already explains much of
    the floor. That is WHY the fits report the partial contribution of x AFTER a
    plane and AFTER a quadratic — the raw `r2` of x alone cannot separate
    starlight from an instrumental gradient, and must not be read as if it can.
 2. Cell shape: the floor is measured over a pixel BOX, the prediction over the
    circle INSCRIBED in it (a circle is what the archive indexes efficiently —
    a per-cell POLYGON query did not return in 120 s where the circle takes
    0.7 s). Both quantities are intensive (ADU per pixel, flux per square
    degree), so the concentric area mismatch smooths the predictor slightly and
    does not bias the slope.
 3. `--gsplit` is the detection limit and it is INHERITED, not measured here:
    G = 11.0 at 50% completeness comes from the july23 identification record
    (`docs/dead-ends.md`, UNRESOLVED STARLIGHT), whose per-set record went with
    that archived session. On this corpus it is a hypothesis. The record carries
    every magnitude bin, so a re-measured limit re-splits without re-querying.
 4. Gaia DR3 is itself incomplete in a crowded plane, so x is a proxy that
    tracks the true faint-star flux rather than equalling it. Every number here
    is a RELATIVE comparison between arms read on one lattice, which that
    proxy supports; an absolute surface brightness is not claimed.
 5. THE IMAGE-SIDE SLOPE IS NOT A CLEAN PRESERVATION MEASURE ON A SURFACE THAT
    STILL CARRIES A LOW-ORDER INSTRUMENTAL TERM, and on these products it does.
    MEASURED, aug06/set-01: removing a plane RAISES the Gaia slope 23-27% and
    removing a quadratic raises it 52-85%, because the open `sky x V` residual
    is anti-correlated with the starlight and biases the raw slope LOW. Both
    effects — confound removed, starlight removed — land in the same number
    with opposite signs, so a retained fraction above 1 does not mean starlight
    was added and one below 1 does not by itself mean starlight was eaten. Read
    it alongside `catalogue_absorbable`, which no confound touches. The same
    measurement puts a size on the confound: the predicted starlight spans
    0.71-0.86 ADU across this frame against a measured floor span of
    2.50-4.00 ADU, so roughly a fifth to a third of the frame-scale floor
    variation is starlight and the rest is not.
 6. The significance of the relation is computed against a SPATIALLY MATCHED
    null, not a textbook p-value: `shift_null` re-fits with the predictor
    circularly shifted over the lattice, which keeps its spatial structure and
    only breaks its registration with the image. It matters — on aug06/set-01
    the naive F-test reads p ~ 6e-4 for Green while 2 of 139 shifts beat the
    observed R2, i.e. p = 0.014. Cells are not independent and a null that
    assumes they are overstates every claim built on it.
"""
import json
import math
import os
import re
import shutil
import subprocess
import sys

import numpy as np
from astropy.io import fits
from astropy.wcs import WCS

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "lib"))
from siril_run import run as siril_run   # serialized invoker (BACKLOG:removal-conditions)

TAP = "https://gea.esac.esa.int/tap-server/tap/sync"
CHANNELS = ("Red", "Green", "Blue")
STAT_RE = re.compile(
    r"(Red|Green|Blue|B&W) layer: Mean: (?P<mean>[-+0-9.eE]+), "
    r"Median: (?P<median>[-+0-9.eE]+), Sigma: (?P<sigma>[-+0-9.eE]+), "
    r"Min: (?P<min>[-+0-9.eE]+), Max: (?P<max>[-+0-9.eE]+), "
    r"bgnoise: (?P<bgnoise>[-+0-9.eE]+)")
SEL_RE = re.compile(r"Current selection \[x, y, w, h\]: "
                    r"(-?\d+) (-?\d+) (-?\d+) (-?\d+)")


# ---------------------------------------------------------------- lattice ---
def build_lattice(header, nx, ny, margin):
    """Cells as pixel boxes on a fixed grid, each with its sky centre and the
    radius of the circle inscribed in it. Independent of any detection.

    `box` is [x, y, w, h] in FITS pixel coordinates (y from the BOTTOM row) —
    the frame astropy's WCS addresses. `select_y()` converts to the top-down y
    `boxselect` takes."""
    w, h = int(header["NAXIS1"]), int(header["NAXIS2"])
    # naxis=2 explicitly: these products are 3-plane cubes carrying SIP, and
    # astropy refuses SIP alongside a 3-D core WCS.
    wcs = WCS(header, naxis=2)
    scale = math.sqrt(abs(np.linalg.det(wcs.pixel_scale_matrix)))   # deg/px
    cw, ch = (w - 2 * margin) // nx, (h - 2 * margin) // ny
    if cw < 16 or ch < 16:
        sys.exit(f"starlight_preservation: {nx}x{ny} cells leaves {cw}x{ch} px "
                 f"per cell on a {w}x{h} image — too small to measure a floor")
    cells = []
    for j in range(ny):
        for i in range(nx):
            x, y = margin + i * cw, margin + j * ch
            ra, dec = wcs.all_pix2world([[x + cw / 2.0, y + ch / 2.0]], 0)[0]
            cells.append({"id": f"c{i:02d}{j:02d}", "ij": [i, j],
                          "box": [x, y, cw, ch],
                          "ra": float(ra), "dec": float(dec),
                          "radius_deg": min(cw, ch) / 2.0 * scale})
    return cells, {"image_wh": [w, h], "scale_deg_per_px": scale,
                   "grid": [nx, ny], "cell_px": [cw, ch], "margin_px": margin,
                   "box_frame": "FITS pixels, y from the bottom row; "
                                "boxselect is emitted top-down"}


def select_y(box, image_h):
    """`boxselect`'s top-down y for a box held in FITS pixel coordinates."""
    return image_h - box[1] - box[3]


def cap_area_deg2(radius_deg):
    """Exact spherical-cap area of the prediction circle, in square degrees."""
    sr = 2.0 * math.pi * (1.0 - math.cos(math.radians(radius_deg)))
    return sr * (180.0 / math.pi) ** 2


# ------------------------------------------------------- Siril measurement ---
def measure_cells(surface, cells, workdir, image_h):
    """One Siril load, then boxselect+stat per cell. Every number is Siril's."""
    os.makedirs(workdir, exist_ok=True)
    ssf = os.path.join(workdir, "_starlight_stat.ssf")
    with open(ssf, "w") as fh:
        fh.write("requires 1.2.0\nsetcompress 0\nsetext fit\n"
                 f"load {surface}\n")
        for c in cells:
            x, _, bw, bh = c["box"]
            fh.write(f"boxselect {x} {select_y(c['box'], image_h)} "
                     f"{bw} {bh}\nstat\n")
        fh.write("boxselect -clear\n")
    r = siril_run(["-d", workdir, "-s", ssf], capture_output=True, text=True)
    text = r.stdout + r.stderr
    os.remove(ssf)

    # Parse by SELECTION anchor: a cell whose stat failed simply carries fewer
    # layers rather than silently stealing the next cell's numbers.
    per_sel, cur = [], None
    for line in text.splitlines():
        m = SEL_RE.search(line)
        if m:
            cur = {"box": [int(v) for v in m.groups()], "chans": {}}
            per_sel.append(cur)
            continue
        m = STAT_RE.search(line)
        if m and cur is not None:
            cur["chans"][m.group(1)] = {k: float(v) for k, v
                                        in m.groupdict().items()}
    if len(per_sel) != len(cells):
        sys.exit(f"starlight_preservation: siril echoed {len(per_sel)} "
                 f"selections for {len(cells)} cells — siril said:\n"
                 f"{text[-1200:]}")
    out = []
    for cell, sel in zip(cells, per_sel):
        want = [cell["box"][0], select_y(cell["box"], image_h),
                cell["box"][2], cell["box"][3]]
        if sel["box"] != want:
            sys.exit(f"starlight_preservation: selection echo {sel['box']} "
                     f"does not match requested {want} for {cell['id']}")
        rec = dict(cell)
        rec["stat"] = sel["chans"]
        # Siril `stat` EXCLUDES zero pixels from every estimator but still
        # prints Min 0.0 (docs/dead-ends.md) — so Min == 0 is the only visible
        # signature of a zero inside the box. It cannot report HOW MANY, so the
        # guard is deliberately narrow: only a cell zeroed in EVERY channel is
        # uncovered canvas. A single channel reading 0 is ordinary clipping on
        # a low-level channel and does not invalidate a 125,000-pixel median —
        # measured here on an INTERIOR cell whose Red floor sits at 13.9 ADU
        # while Green and Blue read 62.8 and 30.3. Partial coverage is handled
        # upstream by the pinned crop-to-coverage order, not by this guard.
        zeros = [c for c, v in sel["chans"].items() if v["min"] <= 0.0]
        rec["min_zero_channels"] = zeros
        rec["covered"] = len(zeros) < len(sel["chans"])
        out.append(rec)
    return out


# ------------------------------------------------------------ Gaia via TAP ---
def tap_query(adql, timeout=300, maxrec=100000):
    import requests
    resp = requests.post(TAP, timeout=timeout, data={
        "REQUEST": "doQuery", "LANG": "ADQL", "FORMAT": "csv",
        "QUERY": adql, "MAXREC": str(maxrec)})
    if resp.status_code != 200:
        raise RuntimeError(f"Gaia TAP {resp.status_code}: {resp.text[:400]}")
    return [ln.split(",") for ln in resp.text.strip().split("\n")]


def gaia_magnitude_bins(ra, dec, radius_deg):
    """The archive's own aggregate: per-integer-G counts and summed G flux in
    the circle. One round trip; the split is applied to these bins later."""
    adql = ("SELECT gbin, COUNT(*) AS n, SUM(f) AS fsum FROM ("
            "SELECT FLOOR(phot_g_mean_mag) AS gbin, "
            "POWER(10,-0.4*phot_g_mean_mag) AS f "
            "FROM gaiadr3.gaia_source WHERE 1=CONTAINS(POINT('ICRS',ra,dec),"
            f"CIRCLE('ICRS',{ra:.7f},{dec:.7f},{radius_deg:.7f})) "
            "AND phot_g_mean_mag IS NOT NULL) AS t GROUP BY gbin ORDER BY gbin")
    return {int(float(r[0])): {"n": int(r[1]), "fsum": float(r[2])}
            for r in tap_query(adql)[1:]}


def gaia_for_cells(cells, cache_path, offline):
    cache = {}
    if os.path.exists(cache_path):
        with open(cache_path) as fh:
            cache = json.load(fh)
    fetched = 0
    for c in cells:
        key = f"{c['ra']:.6f},{c['dec']:.6f},{c['radius_deg']:.6f}"
        if key not in cache:
            if offline:
                sys.exit(f"starlight_preservation: --offline and cell "
                         f"{c['id']} is not in {cache_path}")
            cache[key] = {str(k): v for k, v
                          in gaia_magnitude_bins(c["ra"], c["dec"],
                                                 c["radius_deg"]).items()}
            fetched += 1
            if fetched % 20 == 0:
                print(f"  gaia: {fetched} cells fetched", flush=True)
        c["gaia_bins"] = {int(k): v for k, v in cache[key].items()}
    if fetched:
        with open(cache_path, "w") as fh:
            json.dump(cache, fh)
    return fetched


def predictors(cell, gsplit):
    """Unresolved and total Gaia G flux per square degree for one cell."""
    area = cap_area_deg2(cell["radius_deg"])
    unres = sum(b["fsum"] for g, b in cell["gaia_bins"].items() if g >= gsplit)
    total = sum(b["fsum"] for b in cell["gaia_bins"].values())
    nun = sum(b["n"] for g, b in cell["gaia_bins"].items() if g >= gsplit)
    return {"area_deg2": area, "f_unresolved_per_deg2": unres / area,
            "f_total_per_deg2": total / area, "n_unresolved": nun,
            "n_total": sum(b["n"] for b in cell["gaia_bins"].values())}


# ------------------------------------------------------------------- fits ---
def ols(design, y):
    """Least squares on tool numbers. Returns coefficients and R^2."""
    coef, *_ = np.linalg.lstsq(design, y, rcond=None)
    resid = y - design @ coef
    ss_res = float(resid @ resid)
    ss_tot = float(((y - y.mean()) @ (y - y.mean())))
    return coef, (1.0 - ss_res / ss_tot if ss_tot > 0 else float("nan")), ss_res


def slope_se(x, y):
    """Standard error of the slope in a straight-line fit — the number that
    says how large an attenuation this instrument can actually resolve."""
    n = len(y)
    design = np.column_stack([np.ones_like(x), x])
    coef, _, ss_res = ols(design, y)
    sxx = float(((x - x.mean()) @ (x - x.mean())))
    if n <= 2 or sxx <= 0:
        return float("nan")
    return float(math.sqrt(ss_res / (n - 2) / sxx))


def shift_null(x, y, grid, ncells_x):
    """Empirical null that SURVIVES spatial autocorrelation: re-measure the
    same fit with the predictor circularly SHIFTED over the lattice, which
    keeps the predictor's own spatial structure intact and only breaks its
    registration with the image. A plain permutation would destroy that
    structure and report a null far too optimistic, since neighbouring cells
    are not independent. Returns the fraction of shifts reaching |R2| at least
    as large as the observed one — a p-value the instrument computes on itself
    rather than assuming."""
    _, r2_obs, _ = ols(np.column_stack([np.ones_like(x), x]), y)
    idx = {g: i for i, g in enumerate(grid)}
    nx, ny = ncells_x
    hits, tried, r2s = 0, 0, []
    for dx in range(nx):
        for dy in range(ny):
            if dx == 0 and dy == 0:
                continue
            # A dropped cell only costs the PAIRS that land on it, never the
            # whole shift — rejecting the shift outright left zero usable
            # shifts on a lattice missing one cell.
            keep, order = [], []
            for k, (gx, gy) in enumerate(grid):
                src = ((gx + dx) % nx, (gy + dy) % ny)
                if src in idx:
                    keep.append(k)
                    order.append(idx[src])
            if len(keep) < 0.8 * len(grid):
                continue
            _, r2, _ = ols(np.column_stack([np.ones(len(keep)), x[order]]),
                           y[keep])
            r2s.append(float(r2))
            hits += r2 >= r2_obs
            tried += 1
    if not tried:
        return {"shifts": 0, "p": None, "r2_observed": float(r2_obs)}
    return {"shifts": tried, "p": hits / tried, "r2_observed": float(r2_obs),
            "r2_null_max": max(r2s), "r2_null_median": float(np.median(r2s))}


def fit_family(x, y, px, py):
    """Two families over the same numbers, answering two different questions.
    `px`/`py` are cell centres in normalised image position, so the plane and
    the quadratic are the surfaces `subsky 1` and `subsky 2` remove.

    SEQUENTIAL (`slope_resid_*`) — the PRESERVATION question. Fit the surface to
    the floor ALONE, subtract it, regress the residual on the catalogue. That is
    what the operator does: it cannot tell starlight from gradient, so it fits
    and removes both, and what is left is compared to the catalogue afterwards.

    JOINT (`delta_r2_x_after_*`) — the DISCRIMINATION question. Fit the surface
    and the catalogue together and ask what the catalogue explains that position
    alone cannot. This is NOT the preservation number and must not be read as
    one: with a predictor that is itself a smooth function of position, OLS can
    leave the catalogue term carrying nearly its full marginal slope while the
    operator would still have removed the signal. MEASURED on this instrument's
    own fixture — joint 298.16 against the tool's actual 80.84 — which is why
    both are reported and only the sequential one answers the gate."""
    one = np.ones_like(x)
    plane = np.column_stack([one, px, py])
    quad = np.column_stack([one, px, py, px * px, px * py, py * py])
    c_x, r2_x, _ = ols(np.column_stack([one, x]), y)
    out = {"n": int(len(y)), "slope": float(c_x[1]), "intercept": float(c_x[0]),
           "slope_se": slope_se(x, y), "r2_x_alone": float(r2_x)}
    out["slope_rel_se"] = (abs(out["slope_se"] / out["slope"])
                           if out["slope"] else None)
    for name, design in (("plane", plane), ("quadratic", quad)):
        coef, r2_s, _ = ols(design, y)
        resid = y - design @ coef
        c_r, r2_r, _ = ols(np.column_stack([one, x]), resid)
        _, r2_sx, _ = ols(np.column_stack([design, x]), y)
        out[f"r2_{name}"] = float(r2_s)
        out[f"slope_resid_{name}"] = float(c_r[1])
        out[f"slope_resid_{name}_se"] = slope_se(x, resid)
        out[f"r2_resid_{name}"] = float(r2_r)
        out[f"delta_r2_x_after_{name}"] = float(r2_sx - r2_s)
    return out


# ------------------------------------------------------------------- main ---
def run(surface, out_json, nx, ny, margin, gsplit, baseline, offline):
    surface, out_json = os.path.abspath(surface), os.path.abspath(out_json)
    header = fits.getheader(surface)
    workdir = os.path.dirname(out_json) or "."
    os.makedirs(workdir, exist_ok=True)

    base = None
    if baseline:
        with open(baseline) as fh:
            base = json.load(fh)
        cells = [{k: c[k] for k in
                  ("id", "ij", "box", "ra", "dec", "radius_deg")}
                 for c in base["cells"]]
        geom = base["lattice"]
        if [int(header["NAXIS1"]), int(header["NAXIS2"])] != geom["image_wh"]:
            sys.exit("starlight_preservation: the baseline's lattice was built "
                     f"on {geom['image_wh']} and this surface is "
                     f"{[int(header['NAXIS1']), int(header['NAXIS2'])]} — one "
                     "lattice cannot address both; rebuild without --baseline")
        print(f"lattice: {len(cells)} cells inherited from {baseline}")
    else:
        cells, geom = build_lattice(header, nx, ny, margin)
        print(f"lattice: {geom['grid'][0]}x{geom['grid'][1]} = {len(cells)} "
              f"cells of {geom['cell_px'][0]}x{geom['cell_px'][1]} px "
              f"({geom['cell_px'][0] * geom['scale_deg_per_px']:.2f} x "
              f"{geom['cell_px'][1] * geom['scale_deg_per_px']:.2f} deg)")

    cells = measure_cells(surface, cells, workdir, int(header["NAXIS2"]))
    if baseline:
        kept = {c["id"] for c in base["cells"] if c["used"]}
        for c in cells:
            c["used"] = c["id"] in kept and c["covered"]
    else:
        for c in cells:
            c["used"] = c["covered"]
    dropped = [c["id"] for c in cells if not c["used"]]
    if dropped:
        print(f"dropped {len(dropped)} cell(s) (uncovered canvas or dropped by "
              f"the baseline): {' '.join(dropped[:8])}"
              f"{' ...' if len(dropped) > 8 else ''}")

    used = [c for c in cells if c["used"]]
    if len(used) < 12:
        sys.exit(f"starlight_preservation: only {len(used)} usable cells — "
                 "too few for the fits to mean anything")
    cache = os.path.join(workdir, "gaia_cells_cache.json")
    fetched = gaia_for_cells(used, cache, offline)
    print(f"gaia: {len(used)} cells ({fetched} fetched, "
          f"{len(used) - fetched} from cache)")
    for c in used:
        c["predictors"] = predictors(c, gsplit)

    w, h = geom["image_wh"]
    px = np.array([(c["box"][0] + c["box"][2] / 2.0) / w - 0.5 for c in used])
    py = np.array([(c["box"][1] + c["box"][3] / 2.0) / h - 0.5 for c in used])
    x_un = np.array([c["predictors"]["f_unresolved_per_deg2"] for c in used])
    x_tot = np.array([c["predictors"]["f_total_per_deg2"] for c in used])

    # CATALOGUE-ONLY, and it is the cleanest number here: how much of the
    # predictor's OWN spatial variance a surface of each degree can represent.
    # `subsky d` removes a degree-d surface, so this is the UPPER BOUND on the
    # fraction of the frame-scale starlight structure that operator can take —
    # worst case, the fitted surface being the best-fit surface to the
    # starlight itself. No image is involved, so no instrumental confound can
    # move it, which is exactly what the image-side slopes cannot promise.
    one = np.ones_like(px)
    bases = {
        "plane": np.column_stack([one, px, py]),
        "quadratic": np.column_stack([one, px, py, px * px, px * py, py * py]),
        "cubic": np.column_stack([one, px, py, px * px, px * py, py * py,
                                  px ** 3, px * px * py, px * py * py,
                                  py ** 3]),
    }
    absorbable = {}
    for pname, xv in (("unresolved", x_un), ("total", x_tot)):
        absorbable[pname] = {
            "span_frac_of_mean": float((xv.max() - xv.min()) / xv.mean()),
            **{b: ols(D, xv)[1] for b, D in bases.items()}}

    grid = [tuple(c["ij"]) for c in used]
    fits_out = {}
    for chan in CHANNELS:
        if not all(chan in c["stat"] for c in used):
            continue
        y = np.array([c["stat"][chan]["median"] for c in used])
        fits_out[chan] = {
            "floor_adu": {"min": float(y.min()), "max": float(y.max()),
                          "mean": float(y.mean()), "sd": float(y.std(ddof=1))},
            "unresolved": fit_family(x_un, y, px, py),
            "total": fit_family(x_tot, y, px, py),
            "shift_null": shift_null(x_un, y, grid, geom["grid"]),
        }

    rec = {
        "surface": surface,
        "instrument": "Siril stat medians on an external image-fixed lattice "
                      "vs Gaia DR3 per-cell unresolved flux (ESA archive TAP "
                      "aggregate); in-house part is the lattice and the fits",
        "domain": "LINEAR — run this on the pre-stretch surface; an autostretch "
                  "rescales the floor and invalidates every slope",
        "gsplit_G": gsplit,
        "gsplit_provenance": "INHERITED from the july23 identification record "
                             "(G=11.0 at 50% completeness); a hypothesis on this "
                             "corpus until re-measured. Every magnitude bin is "
                             "kept so the split can be re-applied offline",
        "lattice": geom,
        # str(): HISTORY comes back as a commentary-card object, not a scalar
        "header": {k: str(header[k]) for k in
                   ("PIPEREV", "STACKCNT", "LIVETIME", "EXPTIME", "HISTORY")
                   if k in header},
        "cells": cells,
        "catalogue_absorbable": absorbable,
        "fits": fits_out,
    }
    if base:
        rec["baseline"] = baseline
        rec["retained"] = {}
        for chan, f in fits_out.items():
            bf = base["fits"].get(chan)
            if not bf:
                continue
            rec["retained"][chan] = {
                key: {m: _ratio(f[key][m], bf[key][m]) for m in
                      ("slope", "slope_resid_plane", "slope_resid_quadratic")}
                for key in ("unresolved", "total")}
            # PAIRED, and this is the number to read. The two arms see the same
            # sky through the same cells, so the field's own structure — the
            # scatter that makes each ABSOLUTE slope imprecise — cancels in the
            # per-cell DIFFERENCE. Same mechanism as flat_differential.py,
            # whose selftest measures the absolute fit failing where the
            # differential succeeds.
            byid = {c["id"]: c for c in base["cells"] if c.get("used")}
            dy = np.array([used[i]["stat"][chan]["median"]
                           - byid[used[i]["id"]]["stat"][chan]["median"]
                           for i in range(len(used))])
            d_coef, d_r2, _ = ols(np.column_stack([np.ones_like(x_un), x_un]),
                                  dy)
            d_se = slope_se(x_un, dy)
            ctrl_slope = bf["unresolved"]["slope"]
            rec["retained"][chan]["paired"] = {
                "delta_slope": float(d_coef[1]), "delta_slope_se": d_se,
                "delta_r2": float(d_r2),
                "baseline_slope": float(ctrl_slope),
                "retained": _ratio(ctrl_slope + d_coef[1], ctrl_slope),
                "retained_se": (abs(d_se / ctrl_slope) if ctrl_slope else None),
                "mean_level_shift_adu": float(dy.mean()),
            }
    with open(out_json, "w") as fh:
        json.dump(rec, fh, indent=1)

    print(f"\nsurface: {os.path.basename(surface)}   cells used: {len(used)}")
    au = absorbable["unresolved"]
    print(f"  CATALOGUE-ONLY BOUND (no image): the unresolved-starlight "
          f"predictor spans {100 * au['span_frac_of_mean']:.0f}% of its mean "
          f"across this field, and a fitted surface can represent")
    print(f"        plane {100 * au['plane']:.1f}%   quadratic "
          f"{100 * au['quadratic']:.1f}%   cubic {100 * au['cubic']:.1f}% "
          f"of its spatial variance — the most `subsky 1` / `subsky 2` / "
          f"`subsky 3` could remove from the starlight structure")
    for chan, f in fits_out.items():
        u = f["unresolved"]
        print(f"  {chan:5s} floor {f['floor_adu']['min']:.2f}-"
              f"{f['floor_adu']['max']:.2f} ADU (sd {f['floor_adu']['sd']:.3f})")
        print(f"        unresolved: slope {u['slope']:.4g}  R2 "
              f"{u['r2_x_alone']:.4f}   surviving a plane: slope "
              f"{u['slope_resid_plane']:.4g} ({100 * u['slope_resid_plane'] / u['slope']:.1f}%)"
              f"  R2 {u['r2_resid_plane']:.4f}   surviving a quadratic: slope "
              f"{u['slope_resid_quadratic']:.4g} "
              f"({100 * u['slope_resid_quadratic'] / u['slope']:.1f}%)  R2 "
              f"{u['r2_resid_quadratic']:.4f}")
        print(f"        slope SE {u['slope_se']:.4g} "
              f"({100 * u['slope_rel_se']:.1f}% of the slope) — the smallest "
              f"attenuation this can resolve at 2 sigma is "
              f"{200 * u['slope_rel_se']:.0f}%")
        print(f"        discrimination (joint dR2 of the catalogue over "
              f"position alone): plane {u['delta_r2_x_after_plane']:.4f}  "
              f"quadratic {u['delta_r2_x_after_quadratic']:.4f}")
        sn = f["shift_null"]
        print(f"        shift null ({sn['shifts']} lattice shifts, keeps the "
              f"predictor's own spatial structure): p={sn['p']}, best null R2 "
              f"{sn.get('r2_null_max', float('nan')):.4f} against observed "
              f"{sn['r2_observed']:.4f}")
        print(f"        total-flux control: R2 {f['total']['r2_x_alone']:.4f} "
              f"(the unresolved predictor must beat this to mean anything)")
        if base and chan in rec.get("retained", {}):
            r = rec["retained"][chan]["unresolved"]
            p = rec["retained"][chan]["paired"]
            print(f"        RETAINED vs baseline, unpaired: slope "
                  f"{_fmt(r['slope'])}  surviving a plane "
                  f"{_fmt(r['slope_resid_plane'])}  surviving a quadratic "
                  f"{_fmt(r['slope_resid_quadratic'])}")
            print(f"        RETAINED vs baseline, PAIRED (read this one): "
                  f"{p['retained']:+.4f} +- {p['retained_se']:.4f}   "
                  f"(delta slope {p['delta_slope']:+.4g} +- "
                  f"{p['delta_slope_se']:.4g} on a baseline "
                  f"{p['baseline_slope']:.4g}; mean level shift "
                  f"{p['mean_level_shift_adu']:+.3f} ADU)")
    print(f"\nrecord: {out_json}")
    return rec


def _ratio(a, b):
    return float(a / b) if b not in (0, None) and abs(b) > 0 else None


def _fmt(v):
    return "n/a" if v is None else f"{v:+.3f}"


# --------------------------------------------------------------- selftest ---
def _synth(path, gain, pattern, size=(1400, 1000)):
    """A fixture with KNOWN truth: sky + gain * pattern(ra, dec), plus seeded
    noise. Not a deliverable and not read by any pipeline — the instrument's
    own falsification surface."""
    w, h = size
    wcs = WCS(naxis=2)
    wcs.wcs.crpix = [w / 2.0, h / 2.0]
    wcs.wcs.crval = [305.5, 42.3]
    rot = math.radians(6.0)
    s = 17.075 / 3600.0
    wcs.wcs.cd = np.array([[-s * math.cos(rot), s * math.sin(rot)],
                           [s * math.sin(rot), s * math.cos(rot)]])
    wcs.wcs.ctype = ["RA---TAN", "DEC--TAN"]
    yy, xx = np.mgrid[0:h, 0:w]
    ra, dec = wcs.all_pix2world(xx.ravel(), yy.ravel(), 0)
    p = pattern(ra.reshape(h, w), dec.reshape(h, w))
    rng = np.random.default_rng(20260812)          # seeded: no unseeded step
    data = (1000.0 + gain * p + rng.normal(0, 2.0, (h, w))).astype("float32")
    cube = np.repeat(data[None, :, :], 3, axis=0) / 65535.0
    hdr = wcs.to_header()
    fits.writeto(path, cube.astype("float32"), hdr, overwrite=True)
    return wcs, p


def _band(ra, dec):
    """A smooth frame-scale band — what unresolved starlight looks like at this
    scale, and exactly the shape a low-order surface can absorb."""
    return np.exp(-(((dec - 42.6) / 1.6) ** 2))


def _cross(ra, dec):
    """Orthogonal to `_band` by construction: varies along the other axis."""
    return np.exp(-(((ra - 305.0) / 2.0) ** 2))


def _cell_truth(cells, wcs, pattern):
    return np.array([pattern(np.array([c["ra"]]), np.array([c["dec"]]))[0]
                     for c in cells])


def selftest(keep=False):
    work = os.path.expanduser("~/.cache/astro-imaging/starlight_selftest")
    if os.path.isdir(work):
        shutil.rmtree(work)
    os.makedirs(work)
    gain, ok = 300.0, True
    pristine = os.path.join(work, "synth.fit")
    wcs, _ = _synth(pristine, gain, _band)

    def measured(surface, truth_pattern=_band):
        hdr = fits.getheader(surface)
        cells, geom = build_lattice(hdr, 10, 7, 0)
        cells = measure_cells(surface, cells, work, int(hdr["NAXIS2"]))
        y = np.array([c["stat"]["Green"]["median"] for c in cells])
        x = _cell_truth(cells, wcs, truth_pattern)
        w_, h_ = geom["image_wh"]
        px = np.array([(c["box"][0] + c["box"][2] / 2.0) / w_ - 0.5
                       for c in cells])
        py = np.array([(c["box"][1] + c["box"][3] / 2.0) / h_ - 0.5
                       for c in cells])
        return fit_family(x, y, px, py)

    def slope_of(surface, truth_pattern=_band):
        f = measured(surface, truth_pattern)
        return f["slope"], f["r2_x_alone"]

    print("=== step 1: POSITIVE CONTROL — the planted relation is recovered")
    s0, r0 = slope_of(pristine)
    # Siril prints ADU on a 0-65535 scale; the fixture was written in the same
    # units, so the recovered slope is directly comparable to `gain`.
    step1 = abs(s0 - gain) / gain < 0.05 and r0 > 0.99
    print(f"    slope {s0:.2f} against planted {gain:.2f} "
          f"({100 * (s0 - gain) / gain:+.2f}%), R2 {r0:.5f} -> "
          f"{'GREEN' if step1 else 'RED'}")
    ok &= step1

    print("=== step 2: NEGATIVE CONTROL — an orthogonal pattern must NOT fit")
    s_n, r_n = slope_of(pristine, _cross)
    step2 = r_n < 0.20 and abs(s_n) < 0.35 * gain
    print(f"    slope {s_n:.2f}, R2 {r_n:.5f} -> "
          f"{'GREEN' if step2 else 'RED'}  (a smooth predictor must not fit "
          f"by being smooth)")
    ok &= step2

    print("=== step 3: FALSIFICATION IN PROCESS — remove the signal with the "
          "tool and watch the instrument go RED")
    degraded = {}
    for degree in (1, 2):
        arm = os.path.join(work, f"synth_subsky{degree}.fit")
        ssf = os.path.join(work, f"_sub{degree}.ssf")
        with open(ssf, "w") as fh:
            fh.write(f"requires 1.2.0\nsetcompress 0\nsetext fit\n"
                     f"load {pristine}\nsubsky {degree}\n"
                     f"save {arm[:-4]}\n")
        siril_run(["-d", work, "-s", ssf], capture_output=True, text=True)
        if not os.path.exists(arm):
            sys.exit(f"selftest: siril did not write {arm}")
        s_d, r_d = slope_of(arm)
        degraded[degree] = (s_d, r_d)
        print(f"    subsky {degree}: slope {s_d:.2f} = {100 * s_d / gain:.1f}% "
              f"of planted, R2 {r_d:.5f}")
    r1_, r2_ = degraded[1][0] / gain, degraded[2][0] / gain
    # The bar tests the HARNESS, not the physics: the instrument must resolve a
    # removal it did not perform, and must order the two degrees the way the
    # mechanism says. It is NOT a prediction of how much a quadratic absorbs —
    # that is a property of the planted shape (a 1.13 deg sigma band across a
    # 4.7 deg frame) and would be a fitted threshold if asserted.
    step3 = r2_ < 0.50 and (r1_ - r2_) > 0.20
    print(f"    retained: degree 1 {r1_:.3f}, degree 2 {r2_:.3f} against a "
          f"pristine {s0 / gain:.3f} repeatable to 1e-6 -> "
          f"{'RED as required' if step3 else 'NOT RED — instrument is blind'}")
    ok &= step3

    print("=== step 3b: CROSS-CHECK — the fit family predicts what the tool "
          "actually removes")
    fam = measured(pristine)
    step3b = True
    for name, degree in (("plane", 1), ("quadratic", 2)):
        pred, truth = fam[f"slope_resid_{name}"], degraded[degree][0]
        conservative = pred <= truth * 1.02          # 2% for arithmetic noise
        step3b &= conservative
        print(f"    residual-of-{name:9s} predicts {pred:7.2f} survives, "
              f"subsky {degree} actually left {truth:7.2f} "
              f"({truth / pred:.2f}x more) -> "
              f"{'conservative' if conservative else 'OPTIMISTIC — unsafe'}")
    print(f"    -> {'GREEN' if step3b else 'RED'}  (the bar is DIRECTION, not "
          f"agreement: Siril fits the image on a clipped sample grid and the "
          f"family least-squares-fits the cell medians, so the family absorbs "
          f"MORE and its surviving slope is a floor. A proxy that predicted "
          f"more survival than the tool delivers would be unsafe to quote; "
          f"one that predicts less is a conservative indicator, and the arms "
          f"still have to be built to get the real number)")
    ok &= step3b

    print("=== step 4: RESTORE — the same code catches it again")
    s1, r1 = slope_of(pristine)
    step4 = abs(s1 - s0) < 1e-6 and abs(s1 - gain) / gain < 0.05
    print(f"    slope {s1:.2f}, R2 {r1:.5f} -> "
          f"{'GREEN' if step4 else 'RED'}")
    ok &= step4

    print("=== step 5: CATALOGUE CONTROL — the archive aggregate is sane")
    try:
        plane = gaia_magnitude_bins(305.5, 42.3, 0.4)
        pole = gaia_magnitude_bins(192.86, 27.13, 0.4)
        fp = sum(b["fsum"] for b in plane.values())
        fq = sum(b["fsum"] for b in pole.values())
        rows = tap_query(
            "SELECT COUNT(*) AS n, SUM(POWER(10,-0.4*phot_g_mean_mag)) AS f "
            "FROM gaiadr3.gaia_source WHERE 1=CONTAINS(POINT('ICRS',ra,dec),"
            "CIRCLE('ICRS',305.5000000,42.3000000,0.4000000)) "
            "AND phot_g_mean_mag IS NOT NULL")
        ungrouped = float(rows[1][1])
        agree = abs(fp - ungrouped) / ungrouped < 1e-6
        contrast = fp / fq
        # The bar is a MECHANISM bar, not a fitted one: two circles 90 deg
        # apart in galactic latitude must differ a lot, and a ratio near 1
        # would mean the CIRCLE constraint is not being applied at all.
        step5 = agree and contrast > 3
        print(f"    binned sum {fp:.6e} vs ungrouped {ungrouped:.6e} "
              f"(agree: {agree}); plane/pole flux ratio {contrast:.1f}x "
              f"(bar 3x) -> {'GREEN' if step5 else 'RED'}")
        ok &= step5
    except Exception as exc:                        # noqa: BLE001 — reported
        print(f"    SKIPPED (archive unreachable: {type(exc).__name__}: "
              f"{str(exc)[:200]}) — the catalogue half is UNVERIFIED in this "
              f"run, and a PASS below does not cover it")

    if not keep:
        shutil.rmtree(work)
    else:
        print(f"\nfixture kept at {work}")
    print(f"\nSELFTEST {'PASS' if ok else 'FAIL'}")
    return 0 if ok else 1


def main():
    argv = sys.argv[1:]
    if "--selftest" in argv:
        return selftest(keep="--keep" in argv)
    args = [a for a in argv if not a.startswith("--")]
    opts = dict(a[2:].split("=", 1) for a in argv
                if a.startswith("--") and "=" in a)
    if len(args) != 2:
        sys.exit(__doc__)
    nx, ny = (int(v) for v in opts.get("cells", "14x10").split("x"))
    gsplit = opts.get("gsplit", "11")
    if not re.fullmatch(r"-?\d+", gsplit):
        sys.exit("starlight_preservation: --gsplit must be an INTEGER — the "
                 "archive aggregates by FLOOR(G), so a fractional split would "
                 "be silently rounded")
    run(args[0], args[1], nx, ny, int(opts.get("margin", 0)), int(gsplit),
        opts.get("baseline"), "--offline" in argv)
    return 0


if __name__ == "__main__":
    sys.exit(main())
