#!/usr/bin/env python3
"""ONE instrument for the star-shape ORIENTATION question, applied to BOTH samples.

WHY THIS EXISTS. Two records in this tree read the same physical quantity in
opposite directions and both are quoted as evidence:

  (a) BACKLOG:`compose-homography-smear` — "the major-axis angle tracks the field
      azimuth in 7 of 8 zones in every set (resultant 0.45-0.85 at the edges)",
      from 136k stars, 3 frames x 6 sets x 2 nights. The RADIAL/optical signature.
  (b) `mechanism_and_specs.json` — median PA near-CONSTANT across 8 azimuth
      sectors, spread 15.8 deg, from 8074 stars on 3 frames of aug06/set-01. The
      FIXED-DIRECTION/trailing signature.

Orientation is the one live discriminator left on the corner defect: in-exposure
trailing holds ONE fixed sensor direction, a radial optical term (coma) sweeps its
position angle with field azimuth. Hour angle, the other named discriminator, is
blocked — the headers carry DATE-OBS and no site coordinates.

A contradiction between two records made by two different code paths cannot be
settled by comparing the records. This is one code path, one convention, over both
samples' own tracked Siril `findstar` lists.

WHAT IS AND IS NOT IN-HOUSE HERE. Every pixel operation and every star measurement
is Siril's — position, both FWHM axes and the position angle are read verbatim out
of `findstar` .lst files that are already tracked records. In-house code holds only
the geometry (field azimuth about a fixed external origin), the binning, and the
fits. No measurement Siril provides is recomputed. This reports numbers; it sets no
threshold, gates nothing, and exits 0.

THE CONVENTION, STATED (the brief requires it explicit, and a wrong sign here
inverts the verdict, so none of it is assumed — every element is fixed by
recovering a PLANTED orientation field on a fixture, `--selftest`):

  theta  the PSF position angle = .lst column 12 ("angle"), used VERBATIM, no
         transform. MEASURED range over 2709 stars: -89.95 .. 89.98 — an AXIS
         angle mod 180, not a vector angle mod 360. It is the angle of the MAJOR
         axis: FWHMx >= FWHMy in 144063 of 144063 stars across both samples, so
         Siril sorts the axes, and column 8 is the major one.
  phi    the FIELD AZIMUTH of the star = atan2(Y - cy, X - cx), in the SAME pixel
         coordinates Siril writes into the .lst. Both angles therefore live in one
         frame by construction and no row-order convention can flip one against
         the other.
  cx,cy  FIXED EXTERNAL ORIGIN = (W-1)/2, (H-1)/2 from the set's own tracked
         acquisition.json image_wh. NEVER derived from the detections — registry
         trap 3: a metric keyed to the findstar bounding box moved 537 px on a
         detection-sigma change alone.
  e      ellipticity magnitude, reported in BOTH standard forms so a reader is
         never guessing which one a number is:
             DISTORTION  e = (a^2 - b^2) / (a^2 + b^2)
             SHEAR       g = (a - b) / (a + b)
         with a = FWHMx (major), b = FWHMy (minor).
  e1,e2  the ellipticity COMPONENTS, e1 = e*cos(2*theta), e2 = e*sin(2*theta).
         The doubling is what makes an axis angle averageable at all: theta and
         theta+180 are the same axis, so only 2*theta is single-valued on the
         circle. Averaging theta itself is not a weaker choice, it is an invalid
         one, and demonstrating that is half of what this instrument is for.

THE DECOMPOSITION. The two hypotheses are not "either/or" and forcing them into
one scalar is what lost the signal. Both terms can be present at once, and in the
component representation they are ORTHOGONAL and jointly linear:

    e1_i = c0 + R * w_i * cos(2*phi_i)
    e2_i = s0 + R * w_i * sin(2*phi_i)

  (c0, s0)  the FIXED-DIRECTION term — trailing. Amplitude F = hypot(c0, s0),
            direction theta0 = 0.5 * atan2(s0, c0). Constant over the field.
  R         the RADIAL term — coma. R > 0 major axis points AWAY from the field
            centre (radial); R < 0 tangential. w_i is 1 in the flat form and the
            normalised field radius rho_i in the growing form, since a field
            aberration grows with radius.

Stacking [e1; e2] into one response makes this an ordinary 3-parameter least
squares, and a fixed direction cannot masquerade as a radial term or the reverse:
the fixed term has no azimuth dependence and the radial term averages to zero over
azimuth. The model-free equivalents are reported alongside it — the global mean
(e1,e2) is the fixed term, and the mean TANGENTIAL component is minus the radial
term (weak-lensing convention, e_t = -(e1*cos2phi + e2*sin2phi), so a tangential
alignment reads positive and a radial one negative).

WHY A SCALAR COULD NOT HAVE ANSWERED THIS. Every corner number in this repo is a
roundness (minor/major) or an axis length. Roundness DISCARDS ORIENTATION — it is
|e| with the direction thrown away — and orientation is precisely the
discriminator. The components keep it, and they average correctly where angles do
not.

DEPTH MATCHING IS MANDATORY, and is not a detail: a findstar median across images
of different depth is a detection-depth comparison, not a quality one. One common
fitted-amplitude floor is applied across every arm, plus a rank-matched
N-brightest control, and n AND the faintest admitted amplitude ride with every
number.

REMOVAL CONDITION: an official tool reports, headless, the azimuthal decomposition
of PSF ellipticity components over a field (a scriptable Siril whisker/e1-e2 map,
or a PixInsight equivalent). Siril reports the per-star shape — it does not report
this decomposition of it — so what is in-house here is only the geometry and the
fits over Siril's own measurements. Re-check on any Siril version bump.

USAGE
    pa_convention.py --selftest      the fire test: planted orientation fields
    pa_convention.py                 measure both samples, write the JSON record
"""

import glob
import json
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
DATASETS = os.path.normpath(os.path.join(HERE, "..", ".."))

# .lst columns (0-based) as written by Siril 1.4.4 findstar
C_A, C_X, C_Y, C_FWHMX, C_FWHMY, C_ANGLE, C_MAG = 3, 5, 6, 7, 8, 11, 13


# --------------------------------------------------------------------------
# reading Siril's own records
# --------------------------------------------------------------------------

def read_lst(path):
    """Siril findstar .lst -> (amplitude, x, y, major_px, minor_px, angle_deg).

    The header's own detection parameters are returned with it: a number carries
    the depth it was measured at or it cannot be compared with another.
    """
    params = {}
    with open(path) as fh:
        for line in fh:
            if not line.startswith("#"):
                break
            for tok in line.replace("#", " ").split():
                if "=" in tok:
                    k, v = tok.split("=", 1)
                    try:
                        params[k] = float(v)
                    except ValueError:
                        params[k] = v
    d = np.loadtxt(path, comments="#",
                   usecols=(C_A, C_X, C_Y, C_FWHMX, C_FWHMY, C_ANGLE))
    if d.ndim == 1:
        d = d[None, :]
    if not (d[:, 3] >= d[:, 4]).all():
        raise SystemExit("%s: FWHMx < FWHMy — the major/minor sort this "
                         "instrument's convention rests on does not hold" % path)
    return d, params


def canvas(session, setname):
    acq = json.load(open(os.path.join(DATASETS, session, setname,
                                      "acquisition.json")))["exif"]
    return acq["image_wh"]


# --------------------------------------------------------------------------
# the convention, as code
# --------------------------------------------------------------------------

def components(major, minor, theta_deg, form="distortion"):
    """(major, minor, PA) -> (e, e1, e2) in the declared convention."""
    if form == "distortion":
        e = (major ** 2 - minor ** 2) / (major ** 2 + minor ** 2)
    elif form == "shear":
        e = (major - minor) / (major + minor)
    else:
        raise ValueError(form)
    t2 = 2.0 * np.radians(theta_deg)
    return e, e * np.cos(t2), e * np.sin(t2)


def azimuth(x, y, cx, cy):
    return np.arctan2(y - cy, x - cx)


def wrap180(a):
    """wrap a mod-180 axis angle in degrees into (-90, +90]."""
    return (a + 90.0) % 180.0 - 90.0


# --------------------------------------------------------------------------
# the fit
# --------------------------------------------------------------------------

def decompose(phi, e1, e2, w=None, nboot=400, seed=20260813, frame=None):
    """Joint fixed-direction + radial fit on the stacked [e1; e2] response.

    EVERY RETURNED SE NAMES ITS ERROR MODEL IN ITS KEY, and that is load-bearing
    rather than cosmetic. MEASURED cost of the neutral names this replaces: a
    star-level bootstrap inside ONE POOLED population understates a per-bin
    property's uncertainty by a median 5.76x (range 4.1-9.2x) against the frames
    treated as INDEPENDENT realisations, turning chi2/dof ~1.1 into 35.6 — i.e.
    manufacturing rejections. The rule that generalises: A PER-BIN PROPERTY
    ESTIMATED FROM N FRAMES HAS N INDEPENDENT REALISATIONS; RESAMPLING STARS
    INSIDE A POOL IS NOT AN ERROR BAR FOR IT.

    The defect this signature exists to prevent was measured in the very file
    that discovered the 5.76x: `constancy_fit.py` wrote the key `se_C1` from a
    correct frame-based scatter at one site and from `se_bootstrap` at another,
    and a weighted least squares downstream consumed `se_C1` without being able
    to tell which. One name, two quantities, one file. So the old neutral keys
    (`radial_se`, `radial_SE_units`, `fixed_amplitude_se`,
    `fixed_amplitude_SE_units`, `fixed_direction_se_deg`) are GONE rather than
    aliased: a stale reader gets a KeyError, which is the loud failure. An alias
    would have preserved exactly the silence being removed.

    `frame` — per-star frame labels, len(phi). Supply them whenever the sample
    pools MORE THAN ONE frame and the quantity is a per-bin property. The fit is
    then ALSO run per frame and `*_frame_based` SEs are returned from the
    between-frame scatter, with `se_ratio_frame_over_bootstrap` so the
    understatement is visible at the call site instead of in a doc. Without
    `frame` only `*_star_bootstrap` keys exist, and they must not be quoted as
    the significance of a per-bin property.

    'Read the lever, not the sigma': the design's singular values and rank are
    reported and a rank-deficient design RAISES. A pseudo-inverse would return a
    confident zero variance along a null direction instead of saying it is
    unidentified.
    """
    n = len(phi)
    w = np.ones(n) if w is None else w
    c, s = w * np.cos(2 * phi), w * np.sin(2 * phi)

    X = np.zeros((2 * n, 3))
    X[:n, 0] = 1.0
    X[n:, 1] = 1.0
    X[:n, 2] = c
    X[n:, 2] = s
    y = np.concatenate([e1, e2])

    sv = np.linalg.svd(X, compute_uv=False)
    rank = int((sv > sv[0] * 1e-10).sum())
    if rank < 3:
        raise SystemExit("design is rank %d of 3 — the terms are not separable "
                         "on this sample; refusing to report a fit" % rank)

    beta, *_ = np.linalg.lstsq(X, y, rcond=None)
    resid = y - X @ beta
    xtx_inv = np.linalg.inv(X.T @ X)
    sig2 = resid @ resid / (2 * n - 3)
    se_analytic = np.sqrt(np.diag(xtx_inv) * sig2)

    # star-level bootstrap via multinomial resampling weights
    rng = np.random.default_rng(seed)
    draws = np.empty((nboot, 3))
    for b in range(nboot):
        m = rng.multinomial(n, np.full(n, 1.0 / n)).astype(float)
        Sm, Sc, Ss = m.sum(), (m * c).sum(), (m * s).sum()
        A = np.array([[Sm, 0.0, Sc],
                      [0.0, Sm, Ss],
                      [Sc, Ss, (m * (c * c + s * s)).sum()]])
        rhs = np.array([(m * e1).sum(), (m * e2).sum(),
                        (m * (c * e1 + s * e2)).sum()])
        draws[b] = np.linalg.solve(A, rhs)
    se_boot = draws.std(axis=0, ddof=1)

    c0, s0, R = beta
    F = float(np.hypot(c0, s0))
    # SE of the fixed-term amplitude, propagated through the bootstrap draws
    F_boot = np.hypot(draws[:, 0], draws[:, 1])
    th0_boot = 0.5 * np.degrees(np.arctan2(draws[:, 1], draws[:, 0]))
    F_se_boot = float(F_boot.std(ddof=1))
    th0_se_boot = float(
        0.5 * np.degrees(np.std(np.unwrap(2 * np.radians(2 * th0_boot)) / 2,
                                ddof=1)))
    out = {
        "n_stars": int(n),
        "fixed_c0": float(c0), "fixed_s0": float(s0),
        "fixed_amplitude": F,
        "fixed_amplitude_se_star_bootstrap": F_se_boot,
        "fixed_amplitude_SE_units_star_bootstrap": float(F / F_se_boot),
        "fixed_direction_theta0_deg": float(
            0.5 * np.degrees(np.arctan2(s0, c0))),
        "fixed_direction_se_deg_star_bootstrap": th0_se_boot,
        "radial_R": float(R),
        "radial_se_star_bootstrap": float(se_boot[2]),
        "radial_SE_units_star_bootstrap": float(abs(R) / se_boot[2]),
        "se_analytic": [float(v) for v in se_analytic],
        "se_bootstrap": [float(v) for v in se_boot],
        "design_singular_values": [float(v) for v in sv],
        "design_rank": rank,
        "design_condition": float(sv[0] / sv[-1]),
        "error_model": "star_bootstrap",
        "error_model_caveat":
            "star_bootstrap captures SHOT NOISE INSIDE ONE POOLED SAMPLE only. "
            "For a per-bin property estimated from N frames it understates the "
            "SE (measured median 5.76x, range 4.1-9.2x) — pass frame= for the "
            "frame-based error and do not quote these as its significance.",
    }
    if frame is None:
        return out

    # ---- frame-based errors: the frames are INDEPENDENT realisations ----
    frame = np.asarray(frame)
    if len(frame) != n:
        raise SystemExit("decompose: frame= must have one label per star "
                         "(%d labels for %d stars)" % (len(frame), n))
    labels = list(dict.fromkeys(frame.tolist()))
    if len(labels) < 2:
        raise SystemExit("decompose: frame= carries %d distinct frame(s) — a "
                         "frame-based SE needs >= 2 independent realisations. "
                         "Omit frame= and quote only the *_star_bootstrap keys."
                         % len(labels))
    per = []
    for lab in labels:
        m = frame == lab
        if m.sum() < 4:                     # 3 parameters + 1
            continue
        sub = decompose(phi[m], e1[m], e2[m],
                        None if w is None else np.asarray(w)[m],
                        nboot=2, seed=seed)
        per.append([sub["fixed_c0"], sub["fixed_s0"], sub["radial_R"],
                    sub["fixed_amplitude"], sub["fixed_direction_theta0_deg"]])
    if len(per) < 2:
        raise SystemExit("decompose: only %d frame(s) carried enough stars to "
                         "fit; a frame-based SE is not available" % len(per))
    a = np.array(per, dtype=float)
    nf = a.shape[0]
    sem = a.std(axis=0, ddof=1) / np.sqrt(nf)     # SE of the mean over frames
    out.update({
        "n_frames_fitted": int(nf),
        "fixed_amplitude_se_frame_based": float(sem[3]),
        "fixed_amplitude_SE_units_frame_based": float(F / sem[3]) if sem[3] else None,
        "fixed_direction_se_deg_frame_based": float(sem[4]),
        "radial_se_frame_based": float(sem[2]),
        "radial_SE_units_frame_based": float(abs(R) / sem[2]) if sem[2] else None,
        "error_model": "star_bootstrap+frame_based",
        "se_ratio_frame_over_bootstrap": {
            "fixed_amplitude": float(sem[3] / F_se_boot) if F_se_boot else None,
            "fixed_direction_deg": float(sem[4] / th0_se_boot) if th0_se_boot else None,
            "radial_R": float(sem[2] / se_boot[2]) if se_boot[2] else None,
            "_read": "how many times LARGER the honest error bar is. The "
                     "recorded median across this thread's bins is 5.76x.",
        },
    })
    return out


def decompose_extended(phi, e1, e2, rho, nboot=200, seed=20260813):
    """The 3-parameter fit plus an m=1 term, which tests a DECENTRED radial field.

    Every fit in corner_work measures rho about the FIXED FRAME CENTRE. If the
    aberration field is centred somewhere else — which is what a decentred or
    tilted element gives, and what the repo's own asymmetric-amplitude reading
    already implies — then a centred model is wrong, and the error shows up at
    azimuthal frequency m=1:

        e1 = c0 + R*cos(2phi) + D1*cos(phi) + D2*sin(phi)
        e2 = s0 + R*sin(2phi) + D1*sin(phi) - D2*cos(phi)

    A significant (D1, D2) says the radial term is not centred on the frame
    centre, and the direction of the offset is 0.5*atan2(D2, D1) up to the usual
    axis ambiguity. This is reported as a DIAGNOSTIC of the centred model, not as
    a fitted optical centre.
    """
    n = len(phi)
    X = np.zeros((2 * n, 5))
    X[:n, 0] = 1.0
    X[n:, 1] = 1.0
    X[:n, 2] = rho * np.cos(2 * phi)
    X[n:, 2] = rho * np.sin(2 * phi)
    X[:n, 3] = np.cos(phi)
    X[n:, 3] = np.sin(phi)
    X[:n, 4] = np.sin(phi)
    X[n:, 4] = -np.cos(phi)
    y = np.concatenate([e1, e2])

    sv = np.linalg.svd(X, compute_uv=False)
    if int((sv > sv[0] * 1e-10).sum()) < 5:
        raise SystemExit("extended design is rank deficient — refusing to report")
    beta, *_ = np.linalg.lstsq(X, y, rcond=None)
    resid = y - X @ beta
    se = np.sqrt(np.diag(np.linalg.inv(X.T @ X)) *
                 (resid @ resid) / (2 * n - 5))
    names = ["fixed_c0", "fixed_s0", "radial_R_rho", "decentre_D1", "decentre_D2"]
    out = {k: float(v) for k, v in zip(names, beta)}
    out.update({k + "_SE_units": float(abs(v) / s)
                for k, v, s in zip(names, beta, se)})
    out["decentre_amplitude"] = float(np.hypot(beta[3], beta[4]))
    out["design_condition"] = float(sv[0] / sv[-1])
    out["residual_rms"] = float(np.sqrt(resid @ resid / (2 * n)))
    return out


def _rss_at_centre(x, y, e1, e2, x0, y0, norm):
    phi = np.arctan2(y - y0, x - x0)
    rho = np.hypot(x - x0, y - y0) / norm
    n = len(x)
    c, s = rho * np.cos(2 * phi), rho * np.sin(2 * phi)
    # normal equations for [c0, s0, R] in closed form — 6 sums, no 2n x 3 matrix
    Sc, Ss, Scc = c.sum(), s.sum(), (c * c + s * s).sum()
    A = np.array([[n, 0.0, Sc], [0.0, n, Ss], [Sc, Ss, Scc]])
    b = np.array([e1.sum(), e2.sum(), (c * e1 + s * e2).sum()])
    beta = np.linalg.solve(A, b)
    r1 = e1 - (beta[0] + beta[2] * c)
    r2 = e2 - (beta[1] + beta[2] * s)
    return float(r1 @ r1 + r2 @ r2), beta


def fit_free_centre(x, y, e1, e2, W, H, grid=25):
    """Is the radial term centred on the FRAME centre, or somewhere else?

    Every fit in corner_work assumes the frame centre. A radial field about a
    DISPLACED centre linearises, to first order, into a centred radial term plus
    a term linear in x — which is exactly the "radial term PLUS one-sided sensor-x
    term" the records report as two separate findings. So the two-term reading
    and a single decentred field are not distinguishable by those fits, and this
    one is built to tell them apart.

    The centre is found by profiling: for each trial centre the three linear
    parameters have a closed-form solution, so only the 2-D centre is searched.
    A coarse grid runs first and its shape is REPORTED, then Powell refines —
    because the failure mode that matters here is a FLAT likelihood, and a
    minimiser that converges on a plateau returns a confident wrong centre.
    The registry already carries the cost of exactly that error one directory
    over: an affine-nuisance lens fit manufactured a 210 x 164 px decentring
    that a homography reduced to 6 x 14 px.
    """
    from scipy.optimize import minimize
    norm = np.hypot((W - 1) / 2.0, (H - 1) / 2.0)
    cx, cy = (W - 1) / 2.0, (H - 1) / 2.0
    rss_centred, beta_centred = _rss_at_centre(x, y, e1, e2, cx, cy, norm)

    span = 1.5
    gx = np.linspace(cx - span * W / 2, cx + span * W / 2, grid)
    gy = np.linspace(cy - span * H / 2, cy + span * H / 2, grid)
    Z = np.empty((grid, grid))
    for i, yy in enumerate(gy):
        for j, xx in enumerate(gx):
            Z[i, j] = _rss_at_centre(x, y, e1, e2, xx, yy, norm)[0]
    i0, j0 = np.unravel_index(np.argmin(Z), Z.shape)

    res = minimize(lambda p: _rss_at_centre(x, y, e1, e2, p[0], p[1], norm)[0],
                   x0=[gx[j0], gy[i0]], method="Powell",
                   options={"xtol": 0.5, "ftol": 1e-10})
    x0b, y0b = float(res.x[0]), float(res.x[1])
    rss_free, beta_free = _rss_at_centre(x, y, e1, e2, x0b, y0b, norm)

    n = len(x)
    # a NOISELESS field fits exactly, so rss_free can be 0 and the F ratio is
    # undefined rather than infinite. Only a fixture reaches this, but a fit that
    # crashes on perfect data is a fit that cannot be tested on perfect data.
    if rss_free <= 0:
        F = float("inf") if rss_centred > 0 else 0.0
    else:
        F = ((rss_centred - rss_free) / 2.0) / (rss_free / (2 * n - 5))
    # curvature of the profiled RSS at the optimum, in px — the LEVER. A flat
    # direction here means the centre is not identified, whatever the optimiser
    # reported.
    h = 50.0
    d2x = (_rss_at_centre(x, y, e1, e2, x0b + h, y0b, norm)[0]
           - 2 * rss_free
           + _rss_at_centre(x, y, e1, e2, x0b - h, y0b, norm)[0]) / h ** 2
    d2y = (_rss_at_centre(x, y, e1, e2, x0b, y0b + h, norm)[0]
           - 2 * rss_free
           + _rss_at_centre(x, y, e1, e2, x0b, y0b - h, norm)[0]) / h ** 2
    sig2 = rss_free / (2 * n - 5)
    # 1-sigma half-width where the profiled RSS rises by sig2. A noiseless field
    # has sig2 = 0 and therefore a zero-width interval, which is correct: the
    # centre is exactly determined.
    sx_px = float(np.sqrt(2 * sig2 / d2x)) if d2x > 0 else float("inf")
    sy_px = float(np.sqrt(2 * sig2 / d2y)) if d2y > 0 else float("inf")

    return {
        "frame_centre_px": [cx, cy],
        "free_centre_px": [x0b, y0b],
        "offset_from_frame_centre_px": [x0b - cx, y0b - cy],
        "offset_magnitude_px": float(np.hypot(x0b - cx, y0b - cy)),
        "offset_magnitude_frac_of_halfdiag": float(
            np.hypot(x0b - cx, y0b - cy) / norm),
        "centre_1sigma_px": [sx_px, sy_px],
        "offset_in_sigma": [float(abs(x0b - cx) / sx_px) if sx_px > 0 else 0.0,
                            float(abs(y0b - cy) / sy_px) if sy_px > 0 else 0.0],
        "radial_R_centred": float(beta_centred[2]),
        "radial_R_free_centre": float(beta_free[2]),
        "fixed_amplitude_centred": float(np.hypot(*beta_centred[:2])),
        "fixed_amplitude_free_centre": float(np.hypot(*beta_free[:2])),
        "rss_centred": rss_centred, "rss_free_centre": rss_free,
        "F_free_centre_over_centred": float(F),
        "grid_min_at_edge": bool(i0 in (0, grid - 1) or j0 in (0, grid - 1)),
        "grid_rss_range": [float(Z.min()), float(Z.max())],
    }


def sided_bands_in_annuli(x, y, major, W, H, nann=4):
    """The sided-x MAJOR bands with rho HELD, which the record's own fit averaged.

    `mechanism_and_specs.json`'s model_free_sided_bands_major SIGN-FLIPS across
    |x| (-0.12, -0.17, -0.08, +0.14, +0.11) while its linear-in-x regression
    reads 0.13 SE and F = 0.017, and the verdict "star SIZE is purely radial"
    follows the regression. A linear regressor averages a sign-flipping pattern
    to zero, so that null is not evidence of absence — it is the wrong summary
    for the shape present. Here |x| is banded INSIDE narrow rho annuli, so the
    radial term is held and any genuine left-right asymmetry survives.
    """
    cx, cy = (W - 1) / 2.0, (H - 1) / 2.0
    rho = np.hypot(x - cx, y - cy) / np.hypot(cx, cy)
    xf = (x - cx) / (W / 2.0)
    qs = np.linspace(0, 1, nann + 1)
    edges = [np.quantile(rho, q) for q in qs]
    out = []
    for lo, hi in zip(edges[:-1], edges[1:]):
        a = (rho >= lo) & (rho < hi)
        if a.sum() < 200:
            continue
        row = {"rho_band": [float(lo), float(hi)], "n": int(a.sum())}
        for blo, bhi in ((0.0, 0.35), (0.35, 0.7), (0.7, 1.01)):
            mm = a & (np.abs(xf) >= blo) & (np.abs(xf) < bhi)
            neg, pos = mm & (xf < 0), mm & (xf > 0)
            if neg.sum() < 30 or pos.sum() < 30:
                continue
            row["absx_%.2f_%.2f" % (blo, bhi)] = {
                "n_minus": int(neg.sum()), "n_plus": int(pos.sum()),
                "minus_x_major": float(np.median(major[neg])),
                "plus_x_major": float(np.median(major[pos])),
                "difference": float(np.median(major[pos])
                                    - np.median(major[neg])),
            }
        out.append(row)
    return out


def tangential(phi, e1, e2):
    """Model-free split about the fixed origin (weak-lensing sign convention).

    e_t = -(e1 cos2phi + e2 sin2phi): TANGENTIAL alignment positive, RADIAL
    negative. e_x is the 45-degree component and is the null channel — a real
    radial or fixed term leaves it at zero, so a non-zero e_x is a warning that
    the origin or the sign is wrong.
    """
    c, s = np.cos(2 * phi), np.sin(2 * phi)
    et = -(e1 * c + e2 * s)
    ex = -(e2 * c - e1 * s)
    return et, ex


# --------------------------------------------------------------------------
# the two summary statistics, side by side
# --------------------------------------------------------------------------

def sector_table(phi, theta, e, nsect=8):
    """Per-azimuth-sector PA, computed BOTH ways on identical stars.

    naive_median_PA_deg   the prior record's statistic: a LINEAR median of theta.
    circ_PA_deg           the elongation-weighted circular mean on the DOUBLED
                          angle, which is the only correct mean of an axis angle.
    resultant             |sum e*exp(2 i theta)| / sum e — 1.0 is a perfectly
                          aligned sector, 0.0 is no preferred direction. This is
                          the statistic record (a) reports.
    pa_minus_sector_deg   the discriminator, wrapped to (-90, 90]. A RADIAL field
                          puts this at ~0 in EVERY sector; a FIXED direction makes
                          it track minus the sector centre.
    """
    edges = np.linspace(-180.0, 180.0, nsect + 1)
    deg = np.degrees(phi)
    rows = []
    for lo, hi in zip(edges[:-1], edges[1:]):
        m = (deg >= lo) & (deg < hi)
        if m.sum() < 50:
            continue
        t2 = 2 * np.radians(theta[m])
        z = np.sum(e[m] * np.exp(1j * t2))
        circ = 0.5 * np.degrees(np.angle(z))
        centre = 0.5 * (lo + hi)
        rows.append({
            "azimuth_centre_deg": float(centre),
            "n": int(m.sum()),
            "naive_median_PA_deg": float(np.median(theta[m])),
            "circ_PA_deg": float(circ),
            "resultant": float(np.abs(z) / np.sum(e[m])),
            "pa_minus_sector_deg": float(wrap180(circ - centre)),
        })
    return rows


def sector_summary(rows):
    naive = np.array([r["naive_median_PA_deg"] for r in rows])
    resid = np.array([r["pa_minus_sector_deg"] for r in rows])
    circ = np.array([r["circ_PA_deg"] for r in rows])
    return {
        "naive_PA_spread_deg": float(np.std(naive)),
        "circ_PA_spread_deg": float(np.std(circ)),
        "residual_vs_sector_rms_deg": float(np.sqrt(np.mean(resid ** 2))),
        "residual_vs_sector_max_abs_deg": float(np.max(np.abs(resid))),
        "sectors_tracking_azimuth_within_25deg": int((np.abs(resid) <= 25).sum()),
        "n_sectors": len(rows),
        "mean_resultant": float(np.mean([r["resultant"] for r in rows])),
    }


# --------------------------------------------------------------------------
# depth matching
# --------------------------------------------------------------------------

def apply_floor(d, floor):
    return d[d[:, 0] >= floor]


def rank_match(d, n_keep):
    return d[np.argsort(-d[:, 0])][:n_keep]


# --------------------------------------------------------------------------
# population selection — the difference the tension note did not name
# --------------------------------------------------------------------------

def population(d, W, H, which):
    """The two records did not measure the same STARS, not only not the same way.

    Record (a)'s own `_method` string (datasets/aug06/experiments.jsonl, M1b,
    verbatim): "eight 45-deg zones at rho>1200 px, bright half, roundness<0.85,
    elongation-weighted circular mean of the doubled angle". Record (b) applied
    NO cut of any kind. That is a third live difference on top of the statistic
    and the detection depth, and it is the one nobody had named.
    """
    if which == "all":
        return d
    if which == "record_a_cuts":
        cx, cy = (W - 1) / 2.0, (H - 1) / 2.0
        rho_px = np.hypot(d[:, 1] - cx, d[:, 2] - cy)
        keep = (rho_px > 1200.0)
        keep &= d[:, 0] >= np.median(d[:, 0])          # bright half
        keep &= (d[:, 4] / d[:, 3]) < 0.85             # roundness < 0.85
        return d[keep]
    if which == "round_only":
        # the Oracle's r=1 degeneracy null: Siril's psf ratio is
        # r = 0.5*(cos(FIT(5))+1), whose derivative vanishes at r = 1, so the
        # rotation angle of a near-round star is set by the optimiser and the
        # noise, not by the data. This population must carry NO orientation. If
        # it does, every unweighted PA statistic in this repo is contaminated.
        return d[(d[:, 4] / d[:, 3]) > 0.95]
    raise ValueError(which)


# --------------------------------------------------------------------------
# one measurement, end to end
# --------------------------------------------------------------------------

def measure(d, W, H, form="distortion", nboot=400, label="", nperm=200):
    cx, cy = (W - 1) / 2.0, (H - 1) / 2.0
    A, x, y, major, minor, theta = d.T
    phi = azimuth(x, y, cx, cy)
    rho = np.hypot(x - cx, y - cy) / np.hypot(cx, cy)
    e, e1, e2 = components(major, minor, theta, form)
    et, ex = tangential(phi, e1, e2)

    flat = decompose(phi, e1, e2, None, nboot)
    grow = decompose(phi, e1, e2, rho, nboot)
    rows = sector_table(phi, theta, e)

    n = len(A)
    out = {
        "label": label,
        "n_stars": n,
        "faintest_admitted_amplitude": float(A.min()),
        "brightest_amplitude": float(A.max()),
        "ellipticity_form": form,
        "median_roundness_minor_over_major": float(np.median(minor / major)),
        "median_e": float(np.median(e)),
        "median_major_px": float(np.median(major)),
        "model_free": {
            "mean_e1": float(e1.mean()), "mean_e2": float(e2.mean()),
            "fixed_amplitude_from_mean": float(np.hypot(e1.mean(), e2.mean())),
            "fixed_direction_deg": float(
                0.5 * np.degrees(np.arctan2(e2.mean(), e1.mean()))),
            "mean_tangential_et": float(et.mean()),
            "mean_cross_ex_NULL_CHANNEL": float(ex.mean()),
            "se_of_the_means": float(e1.std(ddof=1) / np.sqrt(n)),
        },
        "fit_flat_radial": flat,
        "fit_radius_growing_radial": grow,
        "fit_extended_decentring_m1": decompose_extended(phi, e1, e2, rho),
        "expected_mean_cross_ex_from_the_fixed_term_alone": float(
            -(flat["fixed_s0"] * np.mean(np.cos(2 * phi))
              - flat["fixed_c0"] * np.mean(np.sin(2 * phi)))),
        "sectors": rows,
        "sector_summary": sector_summary(rows),
    }
    # a 90-degree scramble between the sorted axes and the reported angle would
    # show as an antipodal second lobe in the doubled angle. Reported for the
    # well-determined tail, where PA is not noise.
    strong = e >= np.percentile(e, 90)
    t2 = 2 * np.radians(theta[strong])
    out["axis_angle_coherence_top_decile_e"] = {
        "n": int(strong.sum()),
        "resultant_of_doubled_angle": float(np.abs(np.mean(np.exp(1j * t2)))),
        "reads": "Siril's psf ratio is r = 0.5*(cos(FIT(5))+1), bounded to [0,1] "
                 "by the parameterisation, so sy <= sx holds by construction and "
                 "there is no sort and no star-dependent 90-degree scramble. "
                 "This is reported as a standing check on that, not as a verdict.",
    }
    out["permutation_null"] = permutation_null(phi, theta, e, out, nperm)
    return out


def permutation_null(phi, theta, e, out, nperm=200, seed=99):
    """The null record (b) never had, and without which its reading is unfounded.

    Record (b) read a small per-sector spread of the linear median as evidence of
    a FIXED direction. But a population with NO orientation information also
    returns a small spread under that statistic — a linear mean or median of a
    mod-180 angle is biased toward the middle of the stated range, which for
    Siril's [-90, 90] is 0. So "near-constant" is equally the signature of a
    trailing term and of nothing at all, and the two are told apart only against
    a null.

    The null breaks the position-angle relation by permuting theta across stars
    while holding the positions fixed. Anything a real fixed direction or a real
    radial term contributes is destroyed; the detection depth, the ellipticity
    distribution and the field sampling are untouched.
    """
    rng = np.random.default_rng(seed)
    naive, resid, fixedamp = [], [], []
    for _ in range(nperm):
        k = rng.permutation(len(theta))
        rows = sector_table(phi, theta[k], e[k])
        ss = sector_summary(rows)
        naive.append(ss["naive_PA_spread_deg"])
        resid.append(ss["residual_vs_sector_rms_deg"])
        _, p1, p2 = (None, e[k] * np.cos(2 * np.radians(theta[k])),
                     e[k] * np.sin(2 * np.radians(theta[k])))
        fixedamp.append(np.hypot(p1.mean(), p2.mean()))
    naive, resid, fixedamp = map(np.asarray, (naive, resid, fixedamp))
    obs_naive = out["sector_summary"]["naive_PA_spread_deg"]
    obs_resid = out["sector_summary"]["residual_vs_sector_rms_deg"]
    obs_fixed = out["model_free"]["fixed_amplitude_from_mean"]
    return {
        "nperm": nperm,
        "naive_PA_spread_deg": {
            "observed": obs_naive,
            "null_mean": float(naive.mean()), "null_sd": float(naive.std(ddof=1)),
            "null_p05_p95": [float(np.percentile(naive, 5)),
                             float(np.percentile(naive, 95))],
            "p_two_sided": float(
                2 * min((naive <= obs_naive).mean(), (naive >= obs_naive).mean())),
            "reads": "if the observed spread sits INSIDE the null, a small spread "
                     "carries no evidence of a fixed direction — it is what no "
                     "orientation information looks like under this statistic",
        },
        "circular_residual_vs_sector_rms_deg": {
            "observed": obs_resid,
            "null_mean": float(resid.mean()), "null_sd": float(resid.std(ddof=1)),
            "p_one_sided_smaller": float((resid <= obs_resid).mean()),
        },
        "fixed_amplitude_from_mean": {
            "observed": obs_fixed,
            "null_mean": float(fixedamp.mean()),
            "null_p95": float(np.percentile(fixedamp, 95)),
            "p_one_sided_larger": float((fixedamp >= obs_fixed).mean()),
        },
    }


# --------------------------------------------------------------------------
# THE FIRE TEST — planted orientation fields, and a RED on demand
# --------------------------------------------------------------------------

OFFSET_XY = (1500.0, -800.0)    # the planted decentring the fixture must recover


def _plant(mode, n=8000, W=6064, H=4040, e_amp=0.15, pa_noise_deg=0.0,
           theta0=30.0, seed=7, e_from=None, xy_from=None):
    """A synthetic .lst-shaped array with a KNOWN orientation field."""
    rng = np.random.default_rng(seed)
    if xy_from is not None:
        x, y = xy_from[:, 0], xy_from[:, 1]
        n = len(x)
    else:
        x = rng.uniform(0, W - 1, n)
        y = rng.uniform(0, H - 1, n)
    cx, cy = (W - 1) / 2.0, (H - 1) / 2.0
    phi_deg = np.degrees(np.arctan2(y - cy, x - cx))

    if mode == "fixed":
        theta = np.full(n, theta0)
    elif mode == "radial":
        theta = phi_deg.copy()
    elif mode == "radial_offset":
        # a radial field about a KNOWN DISPLACED centre — the case a centred
        # model reads as "radial term PLUS a one-sided term in x"
        theta = np.degrees(np.arctan2(y - (cy + OFFSET_XY[1]),
                                      x - (cx + OFFSET_XY[0])))
    elif mode == "radial_offset_plus_fixed":
        pr = np.radians(np.degrees(np.arctan2(y - (cy + OFFSET_XY[1]),
                                              x - (cx + OFFSET_XY[0]))))
        e1 = 0.10 * np.cos(np.radians(2 * theta0)) + 0.12 * np.cos(2 * pr)
        e2 = 0.10 * np.sin(np.radians(2 * theta0)) + 0.12 * np.sin(2 * pr)
        e = np.hypot(e1, e2)
        theta = 0.5 * np.degrees(np.arctan2(e2, e1))
        return _assemble(x, y, e, theta, rng, pa_noise_deg)
    elif mode == "mixed":
        # planted as COMPONENTS so both amplitudes are exactly known
        e1 = 0.10 * np.cos(np.radians(2 * theta0)) + 0.12 * np.cos(
            np.radians(2 * phi_deg))
        e2 = 0.10 * np.sin(np.radians(2 * theta0)) + 0.12 * np.sin(
            np.radians(2 * phi_deg))
        e = np.hypot(e1, e2)
        theta = 0.5 * np.degrees(np.arctan2(e2, e1))
        return _assemble(x, y, e, theta, rng, pa_noise_deg)
    elif mode == "blind":
        theta = rng.uniform(-90, 90, n)
    else:
        raise ValueError(mode)

    e = np.full(n, e_amp) if e_from is None else e_from
    return _assemble(x, y, e, theta, rng, pa_noise_deg)


def _assemble(x, y, e, theta, rng, pa_noise_deg):
    theta = wrap180(theta + rng.normal(0, pa_noise_deg, len(theta))
                    if pa_noise_deg else theta)
    # invert the DISTORTION form back to axis lengths so the instrument's own
    # forward transform is exercised rather than bypassed
    minor = np.ones(len(x)) * 2.0
    major = minor * np.sqrt((1 + e) / (1 - e))
    A = rng.uniform(1000, 50000, len(x))
    return np.column_stack([A, x, y, major, minor, theta])


def selftest():
    W, H = 6064, 4040
    fails, notes = [], []

    def check(name, cond, detail=""):
        notes.append(("PASS" if cond else "FAIL") + "  " + name +
                     ("   " + detail if detail else ""))
        if not cond:
            fails.append(name)

    print("FIRE TEST — planted orientation fields, %d x %d canvas" % (W, H))
    print()

    # ---- arm 1: a FIXED sensor direction must be recovered as fixed ----
    d = _plant("fixed", theta0=30.0, e_amp=0.15, pa_noise_deg=8.0, seed=11)
    r = measure(d, W, H, nboot=200, label="fixture:fixed")
    f = r["fit_flat_radial"]
    check("fixed fixture -> fixed amplitude recovered",
          abs(f["fixed_amplitude"] - 0.15) < 0.15 * 0.15,
          "planted 0.150  recovered %.4f" % f["fixed_amplitude"])
    check("fixed fixture -> direction recovered",
          abs(wrap180(f["fixed_direction_theta0_deg"] - 30.0)) < 3.0,
          "planted 30.0 deg  recovered %.2f deg"
          % f["fixed_direction_theta0_deg"])
    check("fixed fixture -> radial term is null",
          abs(f["radial_R"]) < 0.15 * 0.15,
          "planted 0.0  recovered %.4f  (%.1f SE)"
          % (f["radial_R"], f["radial_SE_units_star_bootstrap"]))

    # ---- arm 2: a RADIAL field must be recovered as radial ----
    d = _plant("radial", e_amp=0.15, pa_noise_deg=8.0, seed=12)
    r_rad = measure(d, W, H, nboot=200, label="fixture:radial")
    f = r_rad["fit_flat_radial"]
    check("radial fixture -> radial amplitude recovered",
          abs(f["radial_R"] - 0.15) < 0.15 * 0.15,
          "planted 0.150  recovered %.4f" % f["radial_R"])
    check("radial fixture -> fixed term is null",
          f["fixed_amplitude"] < 0.15 * 0.15,
          "planted 0.0  recovered %.4f" % f["fixed_amplitude"])
    check("radial fixture -> SIGN: mean tangential is NEGATIVE",
          r_rad["model_free"]["mean_tangential_et"] < 0,
          "e_t = %.4f (weak-lensing sign: radial negative)"
          % r_rad["model_free"]["mean_tangential_et"])
    check("radial fixture -> cross/null channel stays null",
          abs(r_rad["model_free"]["mean_cross_ex_NULL_CHANNEL"]) < 0.01,
          "e_x = %.5f" % r_rad["model_free"]["mean_cross_ex_NULL_CHANNEL"])
    check("radial fixture -> sector PA tracks azimuth in every sector",
          r_rad["sector_summary"]["sectors_tracking_azimuth_within_25deg"] == 8,
          "%d of %d sectors within 25 deg, rms residual %.2f deg"
          % (r_rad["sector_summary"]["sectors_tracking_azimuth_within_25deg"],
             r_rad["sector_summary"]["n_sectors"],
             r_rad["sector_summary"]["residual_vs_sector_rms_deg"]))

    # ---- arm 3: a MIXTURE must yield both, neither absorbing the other ----
    d = _plant("mixed", theta0=30.0, pa_noise_deg=8.0, seed=13)
    r = measure(d, W, H, nboot=200, label="fixture:mixed")
    f = r["fit_flat_radial"]
    check("mixed fixture -> fixed term recovered against a radial one present",
          abs(f["fixed_amplitude"] - 0.10) < 0.10 * 0.20,
          "planted 0.100  recovered %.4f" % f["fixed_amplitude"])
    check("mixed fixture -> radial term recovered against a fixed one present",
          abs(f["radial_R"] - 0.12) < 0.12 * 0.20,
          "planted 0.120  recovered %.4f" % f["radial_R"])

    # ---- arm 4: THE RED. Blind the orientation axis; recovery must FAIL ----
    d = _plant("blind", e_amp=0.15, seed=14)
    r_blind = measure(d, W, H, nboot=200, label="fixture:blinded")
    f = r_blind["fit_flat_radial"]
    radial_criterion = (abs(f["radial_R"] - 0.15) < 0.15 * 0.15)
    fixed_criterion = (abs(f["fixed_amplitude"] - 0.15) < 0.15 * 0.15)
    check("BLINDED fixture -> the radial acceptance criterion FAILS as required",
          not radial_criterion,
          "R = %.4f at %.2f SE (criterion would need 0.1275..0.1725)"
          % (f["radial_R"], f["radial_SE_units_star_bootstrap"]))
    check("BLINDED fixture -> the fixed acceptance criterion FAILS as required",
          not fixed_criterion,
          "F = %.4f at %.2f SE" % (f["fixed_amplitude"],
                                   f["fixed_amplitude_SE_units_star_bootstrap"]))
    check("BLINDED fixture -> both terms consistent with zero",
          f["radial_SE_units_star_bootstrap"] < 3 and f["fixed_amplitude_SE_units_star_bootstrap"] < 3,
          "radial %.2f SE, fixed %.2f SE" % (f["radial_SE_units_star_bootstrap"],
                                             f["fixed_amplitude_SE_units_star_bootstrap"]))

    # ---- arm 5: the naive statistic FAILS on a known-radial field ----
    # This is the demonstration the verdict rests on, so it is planted, not
    # argued. PA noise is swept: at zero noise the linear median still roughly
    # tracks, and it collapses toward the trailing signature as the noise rises.
    print("  the prior record's statistic on a KNOWN-RADIAL field, PA noise swept")
    print("  %-12s %-22s %-22s %s" % ("pa_noise", "naive_PA_spread_deg",
                                      "circ residual rms", "reads as"))
    sweep = []
    for noise in (0.0, 10.0, 20.0, 30.0, 40.0, 50.0):
        d = _plant("radial", e_amp=0.15, pa_noise_deg=noise, seed=21)
        rr = measure(d, W, H, nboot=50, label="sweep")
        ss = rr["sector_summary"]
        reads = ("RADIAL" if ss["naive_PA_spread_deg"] > 35 else
                 "TRAILING (WRONG)")
        sweep.append({"pa_noise_deg": noise,
                      "naive_PA_spread_deg": ss["naive_PA_spread_deg"],
                      "circ_residual_rms_deg":
                          ss["residual_vs_sector_rms_deg"],
                      "naive_statistic_reads": reads})
        print("  %-12.0f %-22.2f %-22.2f %s"
              % (noise, ss["naive_PA_spread_deg"],
                 ss["residual_vs_sector_rms_deg"], reads))
    collapsed = [s for s in sweep if s["naive_statistic_reads"].startswith("TRA")]
    check("the naive linear median MISREADS a known-radial field at some noise",
          len(collapsed) > 0,
          "misreads at pa_noise >= %.0f deg while the circular statistic still "
          "recovers it (residual rms %.2f deg)"
          % (collapsed[0]["pa_noise_deg"],
             collapsed[0]["circ_residual_rms_deg"]) if collapsed else "never")

    # ---- arm 5b: a DECENTRED radial field — the centre must be recovered ---
    # This is the case a centred model reads as "radial term PLUS one-sided x
    # term", i.e. the two findings the records report separately. If the free
    # centre cannot recover a planted offset, no claim about decentring stands.
    for mode, tag in (("radial_offset", "pure"),
                      ("radial_offset_plus_fixed", "with a fixed term on top")):
        d = _plant(mode, n=20000, theta0=30.0, e_amp=0.15, pa_noise_deg=8.0,
                   seed=41)
        A, xx, yy, maj, mnr, th = d.T
        e, e1, e2 = components(maj, mnr, th)
        fc = fit_free_centre(xx, yy, e1, e2, W, H)
        got = fc["offset_from_frame_centre_px"]
        err = np.hypot(got[0] - OFFSET_XY[0], got[1] - OFFSET_XY[1])
        check("decentred radial fixture (%s) -> centre recovered" % tag,
              err < 150.0,
              "planted (%+.0f, %+.0f) px  recovered (%+.0f, %+.0f) px  "
              "error %.0f px" % (OFFSET_XY[0], OFFSET_XY[1], got[0], got[1],
                                 err))
        check("decentred radial fixture (%s) -> free centre beats centred"
              % tag, fc["F_free_centre_over_centred"] > 50,
              "F = %.1f" % fc["F_free_centre_over_centred"])

    # a CENTRED field must NOT produce a spurious offset — the other direction,
    # and the one the registry's phantom-decentring entry was burned by
    d = _plant("radial", n=20000, e_amp=0.15, pa_noise_deg=8.0, seed=42)
    A, xx, yy, maj, mnr, th = d.T
    e, e1, e2 = components(maj, mnr, th)
    fc = fit_free_centre(xx, yy, e1, e2, W, H)
    check("CENTRED radial fixture -> free centre finds no offset",
          fc["offset_magnitude_px"] < 150.0,
          "recovered offset %.0f px (1-sigma %.0f x %.0f px)"
          % (fc["offset_magnitude_px"], fc["centre_1sigma_px"][0],
             fc["centre_1sigma_px"][1]))

    # ---- arm 6: a VERTICAL FLIP must leave the discriminator invariant -----
    # A reflection maps phi -> -phi AND theta -> -theta, so (theta - phi) ->
    # -(theta - phi): "radial" and "fixed" are both invariant, and no FITS
    # row-order convention can turn one into the other. Handedness IS flipped,
    # which is why nothing here is compared against a sky-derived direction.
    for mode, planted in (("radial", "radial"), ("fixed", "fixed")):
        d = _plant(mode, theta0=30.0, e_amp=0.15, pa_noise_deg=8.0, seed=15)
        flip = d.copy()
        flip[:, 2] = (H - 1) - flip[:, 2]          # y -> H-1-y
        flip[:, 5] = wrap180(-flip[:, 5])          # theta -> -theta
        a = measure(d, W, H, nboot=100, label="flip:orig")["fit_flat_radial"]
        b = measure(flip, W, H, nboot=100, label="flip:flipped")["fit_flat_radial"]
        if planted == "radial":
            check("vertical flip leaves the RADIAL term invariant",
                  abs(a["radial_R"] - b["radial_R"]) < 0.005,
                  "R %.4f -> %.4f" % (a["radial_R"], b["radial_R"]))
        else:
            check("vertical flip leaves the FIXED amplitude invariant",
                  abs(a["fixed_amplitude"] - b["fixed_amplitude"]) < 0.005,
                  "F %.4f -> %.4f, direction %.2f -> %.2f deg"
                  % (a["fixed_amplitude"], b["fixed_amplitude"],
                     a["fixed_direction_theta0_deg"],
                     b["fixed_direction_theta0_deg"]))

    # ---- arm 7: the round-star population must carry NO orientation --------
    # Siril's psf ratio r = 0.5*(cos(FIT(5))+1) has dr/dFIT(5) = 0 at r = 1, so
    # a near-round star's rotation angle is unidentified. If that population
    # carries an orientation, it is an instrument artefact and it contaminates
    # every unweighted PA statistic in this repo.
    rng = np.random.default_rng(31)
    d = _plant("blind", n=8000, e_amp=0.02, seed=32)
    d[:, 5] = rng.uniform(-90, 90, len(d))
    r_round = measure(d, W, H, nboot=200, label="fixture:round-only")
    fr = r_round["fit_flat_radial"]
    check("round-star fixture -> no fixed direction",
          fr["fixed_amplitude_SE_units_star_bootstrap"] < 3.0,
          "F = %.5f at %.2f SE" % (fr["fixed_amplitude"],
                                   fr["fixed_amplitude_SE_units_star_bootstrap"]))
    check("round-star fixture -> no radial term",
          fr["radial_SE_units_star_bootstrap"] < 3.0,
          "R = %+.5f at %.2f SE" % (fr["radial_R"], fr["radial_SE_units_star_bootstrap"]))

    print()
    for nline in notes:
        print("  " + nline)
    print()
    if fails:
        print("SELFTEST FAILED: %d of %d" % (len(fails), len(notes)))
        return 1
    print("SELFTEST PASSED: %d of %d" % (len(notes), len(notes)))
    return 0


# --------------------------------------------------------------------------
# the two samples
# --------------------------------------------------------------------------

SAMPLE_A = "pa_sample_a"        # 3 frames x 6 sets x 2 nights, sigma 0.50
SAMPLE_B = [("aug06", "set-01", "f%d.lst" % i) for i in (1, 2, 3)]


def materialise_sample_a():
    """Rebuild record (a)'s 18 star lists from git rather than duplicating them.

    9 of the 18 are still tracked (datasets/aug06/set-0{2,3}/psf_work/); the
    aug06/set-01 trio was replaced and the july31 nine were removed in the
    rebuild reset 41cb1ba. All 18 are in the commit that MADE the claim, ba9a7ff,
    so the provenance is a git ref rather than a copy — which is stronger, and
    keeps 136k duplicated lines out of the tree. The 9 still tracked are verified
    byte-identical to the recovered copies on every run.
    """
    import subprocess
    d = os.path.join(HERE, SAMPLE_A)
    if os.path.isdir(d) and len(glob.glob(os.path.join(d, "*.lst"))) == 18:
        return
    os.makedirs(d, exist_ok=True)
    for session in ("aug06", "july31"):
        for s in ("01", "02", "03"):
            for n in (1, 2, 3):
                src = "ba9a7ff:datasets/%s/set-%s/psf_work/stars_%d.lst" % (
                    session, s, n)
                dst = os.path.join(d, "%s_set-%s_%d.lst" % (session, s, n))
                with open(dst, "wb") as fh:
                    subprocess.run(["git", "show", src], check=True, stdout=fh,
                                   cwd=os.path.join(HERE, "..", "..", ".."))
    # the 9 that are still tracked must match what git history hands back
    for s in ("02", "03"):
        for n in (1, 2, 3):
            a = os.path.join(d, "aug06_set-%s_%d.lst" % (s, n))
            b = os.path.join(DATASETS, "aug06", "set-%s" % s, "psf_work",
                             "stars_%d.lst" % n)
            if open(a, "rb").read() != open(b, "rb").read():
                raise SystemExit("recovered %s differs from the tracked %s — "
                                 "the sample (a) provenance is broken" % (a, b))


def load_sample_a():
    materialise_sample_a()
    out, params = [], []
    for p in sorted(glob.glob(os.path.join(HERE, SAMPLE_A, "*.lst"))):
        d, pr = read_lst(p)
        out.append(d)
        params.append((os.path.basename(p), pr))
    return np.vstack(out), params


def load_sample_b():
    out, params = [], []
    for session, setname, fn in SAMPLE_B:
        p = os.path.join(DATASETS, session, setname, "psf_work", fn)
        d, pr = read_lst(p)
        out.append(d)
        params.append((fn, pr))
    return np.vstack(out), params


def main():
    if "--selftest" in sys.argv:
        return selftest()

    W, H = canvas("aug06", "set-01")
    rec = {
        "what_this_settles": "whether BACKLOG:compose-homography-smear's "
                             "'PA tracks field azimuth' and corner_work's "
                             "'PA near-constant' are one quantity or two",
        "convention": {
            "position_angle": "Siril findstar .lst column 12, verbatim, an AXIS "
                              "angle mod 180 measured in the same pixel frame as "
                              "X and Y",
            "field_azimuth": "atan2(Y - cy, X - cx), same pixel frame",
            "origin": "FIXED EXTERNAL (W-1)/2, (H-1)/2 from acquisition.json "
                      "image_wh — never from the detections",
            "ellipticity": "distortion e = (a^2-b^2)/(a^2+b^2), a = FWHMx major",
            "components": "e1 = e cos 2theta, e2 = e sin 2theta",
            "tangential_sign": "e_t = -(e1 cos2phi + e2 sin2phi); RADIAL "
                               "negative, TANGENTIAL positive",
            "verified_by": "planted-orientation fixture, --selftest",
        },
        "canvas": [W, H],
    }

    da, pa_params = load_sample_a()
    db, pb_params = load_sample_b()

    rec["samples"] = {
        "a_compose_homography_smear": {
            "source": "datasets/aug06/corner_work/pa_sample_a/*.lst — the 18 "
                      "tracked findstar lists behind the 136k-star claim, "
                      "recovered from git ba9a7ff (9 of them were replaced in "
                      "the rebuild reset 41cb1ba; the 6 still tracked under "
                      "datasets/aug06/set-0{2,3}/psf_work/ are byte-identical "
                      "to the recovered copies)",
            "frames": len(pa_params), "stars": int(len(da)),
            "detect_sigma": sorted({p["sigma"] for _, p in pa_params}),
            "roundness_floor": sorted({p["roundness"] for _, p in pa_params}),
            "layer": sorted({p["layer"] for _, p in pa_params}),
        },
        "b_corner_work": {
            "source": "datasets/aug06/set-01/psf_work/f{1,2,3}.lst",
            "frames": len(pb_params), "stars": int(len(db)),
            "detect_sigma": sorted({p["sigma"] for _, p in pb_params}),
            "roundness_floor": sorted({p["roundness"] for _, p in pb_params}),
            "layer": sorted({p["layer"] for _, p in pb_params}),
        },
        "channel_candidate_ELIMINATED_by_inspection":
            "every list in BOTH samples carries layer=1 and roundness=0.05 in "
            "its own header. Channel is not a live difference between the two "
            "records; no arm is spent on it.",
    }

    # ---------------- ARM 1: the 2 x 2 — statistic CROSSED with population ---
    # Both statistics come out of every cell, so the crossing is complete: the
    # prior records are two CORNERS of this table, not two experiments.
    #   record (b) = sample b, population "all",           naive statistic
    #   record (a) = sample a, population "record_a_cuts", circular statistic
    rec["ARM_1_statistic_crossed_with_population"] = {
        "why": "the two records differ in the STATISTIC and in the POPULATION at "
               "once. Record (a)'s own _method (experiments.jsonl M1b, verbatim): "
               "'eight 45-deg zones at rho>1200 px, bright half, roundness<0.85, "
               "elongation-weighted circular mean of the doubled angle'. Record "
               "(b) applied no cut of any kind and took a linear median. Crossing "
               "them separates the two.",
        "cells": {
            "%s__%s" % (sname, pop): measure(
                population(dd, W, H, pop), W, H, nboot=250, nperm=150,
                label="%s / %s" % (sname, pop))
            for sname, dd in (("sample_b", db), ("sample_a", da))
            for pop in ("all", "record_a_cuts")
        },
    }

    # the degeneracy null the Oracle flagged: Siril's psf ratio parameterisation
    # r = 0.5*(cos(FIT(5))+1) is stationary at r = 1, so a near-round star's
    # angle is unidentified. If this population carries an orientation, every
    # unweighted PA statistic in this repo is contaminated.
    rec["ARM_1b_round_star_degeneracy_null"] = {
        "why": "not a hypothesis about the sky — a check on the instrument. "
               "roundness > 0.95 stars have no identified position angle by the "
               "form of Siril's fit; they must carry no orientation.",
        "sample_b": measure(population(db, W, H, "round_only"), W, H,
                            nboot=250, nperm=150, label="sample b, round only"),
        "sample_a": measure(population(da, W, H, "round_only"), W, H,
                            nboot=250, nperm=150, label="sample a, round only"),
    }

    # ---------------- ARM 2: depth, on ONE byte-identical frame -------------
    f1a, _ = read_lst(os.path.join(HERE, SAMPLE_A, "aug06_set-01_1.lst"))
    f1b, _ = read_lst(os.path.join(DATASETS, "aug06", "set-01", "psf_work",
                                   "f1.lst"))
    floor = max(f1a[:, 0].min(), f1b[:, 0].min())
    rec["ARM_2_depth_one_frame_two_sigmas"] = {
        "frame": "aug06/set-01 frame 1 (DSC_6239) — the SAME frame in both "
                 "samples: 200 of sample (b)'s brightest matched into sample "
                 "(a) at 0.0000 px separation and 0.0000 deg angle difference",
        "common_amplitude_floor": float(floor),
        "sigma_0p50": measure(apply_floor(f1a, floor), W, H,
                              label="frame 1, sigma 0.50, floored"),
        "sigma_1p00": measure(apply_floor(f1b, floor), W, H,
                              label="frame 1, sigma 1.00, floored"),
        "sigma_0p50_unfloored": measure(f1a, W, H,
                                        label="frame 1, sigma 0.50, all"),
        "sigma_1p00_unfloored": measure(f1b, W, H,
                                        label="frame 1, sigma 1.00, all"),
    }

    # ---------------- ARM 3: sample composition, depth matched --------------
    floor_ab = max(da[:, 0].min(), db[:, 0].min())
    n_match = min(len(apply_floor(da, floor_ab)), len(apply_floor(db, floor_ab)))
    rec["ARM_3_sample_composition_depth_matched"] = {
        "common_amplitude_floor": float(floor_ab),
        "sample_a_floored": measure(apply_floor(da, floor_ab), W, H,
                                    label="sample a, floored"),
        "sample_b_floored": measure(apply_floor(db, floor_ab), W, H,
                                    label="sample b, floored"),
        "rank_matched_n": int(n_match),
        "sample_a_rank_matched": measure(rank_match(da, n_match), W, H,
                                         label="sample a, %d brightest"
                                               % n_match),
        "sample_b_rank_matched": measure(rank_match(db, n_match), W, H,
                                         label="sample b, %d brightest"
                                               % n_match),
    }

    # ---------------- sample (a) full, and per night, for the record --------
    rec["sample_a_full"] = measure(da, W, H, label="sample a, all 136k")
    per = {}
    for p in sorted(glob.glob(os.path.join(HERE, SAMPLE_A, "*.lst"))):
        key = os.path.basename(p).rsplit("_", 1)[0]
        d, _ = read_lst(p)
        per.setdefault(key, []).append(d)
    rec["per_set"] = {k: measure(np.vstack(v), W, H, nboot=200, label=k)
                      for k, v in sorted(per.items())}

    # ---------------- PER FRAME: does the "fixed" direction stay fixed? -----
    # Not in the brief, and it is the arm that turned out to matter. The two
    # candidate mechanisms make OPPOSITE predictions frame to frame, and this is
    # the cheapest place either could have been caught:
    #   a static optical asymmetry is fixed in SENSOR coordinates, so theta0 is
    #   the same in every frame of a set;
    #   in-exposure trailing points along the sky's apparent motion, whose
    #   direction in the sensor frame moves as the field is carried across the
    #   sky — and these fields sit at 72-77 deg altitude, near the zenith, where
    #   the parallactic angle sweeps fastest.
    # Frames are indexed in acquisition order within each set (sample a is
    # first/middle/last; sample b is frames 1, 101, 201 of aug06/set-01).
    frames = {}
    for p in sorted(glob.glob(os.path.join(HERE, SAMPLE_A, "*.lst"))):
        frames["a:" + os.path.basename(p)[:-4]] = read_lst(p)[0]
    for session, setname, fn in SAMPLE_B:
        frames["b:%s_%s_%s" % (session, setname, fn[:-4])] = read_lst(
            os.path.join(DATASETS, session, setname, "psf_work", fn))[0]
    rec["per_frame"] = {
        k: measure(v, W, H, nboot=200, nperm=60, label=k)
        for k, v in sorted(frames.items())
    }

    # ---------------- ARM 4: is the radial term CENTRED on the frame? -------
    rec["ARM_4_free_centre"] = {}
    for nm, dd in [("sample_a_all", da), ("sample_b_all", db),
                   ("sample_a_record_a_cuts", population(da, W, H,
                                                         "record_a_cuts"))]:
        A, xx, yy, maj, mnr, th = dd.T
        _, e1, e2 = components(maj, mnr, th)
        rec["ARM_4_free_centre"][nm] = fit_free_centre(xx, yy, e1, e2, W, H)

    # ---------------- ARM 5: sided MAJOR bands with rho HELD ----------------
    rec["ARM_5_sided_major_bands_within_rho_annuli"] = {
        "why": "the record's linear-in-x regression on major reads 0.13 SE and "
               "F = 0.017 and the verdict 'star SIZE is purely radial' follows "
               "it, but its own model-free bands SIGN-FLIP across |x| "
               "(-0.12, -0.17, -0.08, +0.14, +0.11). A linear regressor averages "
               "a sign-flipping pattern to zero, so that null is the wrong "
               "summary, not evidence of absence.",
        "sample_a": sided_bands_in_annuli(da[:, 1], da[:, 2], da[:, 3], W, H),
        "sample_b": sided_bands_in_annuli(db[:, 1], db[:, 2], db[:, 3], W, H),
    }

    # ---------------- ARM 6: the RADIAL EXPONENT, per set -------------------
    # Seidel field dependence: transverse coma grows LINEARLY with field height,
    # astigmatism QUADRATICALLY. The exponent of the radial amplitude against
    # rho therefore names the aberration family without any focus knowledge.
    # Reported on the ellipticity RATIO and on the UNNORMALISED second-moment
    # difference, because a ratio's denominator moves with seeing and with the
    # trail and can fake a change in the numerator.
    def annular_profile(dd):
        A, xx, yy, maj, mnr, th = dd.T
        cx, cy = (W - 1) / 2.0, (H - 1) / 2.0
        rho = np.hypot(xx - cx, yy - cy) / np.hypot(cx, cy)
        phi = azimuth(xx, yy, cx, cy)
        _, e1, e2 = components(maj, mnr, th)
        d2 = maj ** 2 - mnr ** 2                      # unnormalised, px^2
        u1 = d2 * np.cos(2 * np.radians(th))
        u2 = d2 * np.sin(2 * np.radians(th))
        qs = np.linspace(0.05, 0.95, 7)
        edges = np.quantile(rho, qs)
        rows = []
        for lo, hi in zip(edges[:-1], edges[1:]):
            m = (rho >= lo) & (rho < hi)
            if m.sum() < 300:
                continue
            f = decompose(phi[m], e1[m], e2[m], None, nboot=120)
            g = decompose(phi[m], u1[m], u2[m], None, nboot=120)
            rows.append({"rho_mid": float(np.median(rho[m])), "n": int(m.sum()),
                         "R_ratio": f["radial_R"],
                         "R_ratio_SE_units": f["radial_SE_units_star_bootstrap"],
                         "R_unnormalised_px2": g["radial_R"],
                         "R_unnorm_SE_units": g["radial_SE_units_star_bootstrap"],
                         "fixed_F_ratio": f["fixed_amplitude"],
                         "fixed_theta0_deg": f["fixed_direction_theta0_deg"]})
        out = {"annuli": rows}
        for key, lab in (("R_ratio", "ratio"),
                         ("R_unnormalised_px2", "unnormalised")):
            good = [r for r in rows if r[key] > 0]
            if len(good) >= 3:
                lr = np.log([r["rho_mid"] for r in good])
                lv = np.log([r[key] for r in good])
                sl, ic = np.polyfit(lr, lv, 1)
                pred = ic + sl * lr
                out["exponent_" + lab] = float(sl)
                out["exponent_%s_r2" % lab] = float(
                    1 - np.var(lv - pred) / np.var(lv))
            else:
                out["exponent_" + lab] = None
        out["any_negative_R_ratio"] = bool(any(r["R_ratio"] < 0 for r in rows))
        out["min_R_ratio"] = float(min(r["R_ratio"] for r in rows)) if rows else None
        return out

    rec["ARM_6_radial_exponent_per_set"] = {
        "why": "Seidel: transverse coma grows LINEARLY with field height, "
               "astigmatism QUADRATICALLY. Coma never flips sign; astigmatism "
               "flips radial<->tangential across the medial focus and passes "
               "through zero at it, so a set sitting near zero and a negative R "
               "anywhere are both astigmatism signatures.",
        "per_set": {k: annular_profile(np.vstack(v)) for k, v in sorted(per.items())},
        "sample_a_all": annular_profile(da),
    }

    # ---------------- ARM 7: does theta0 really move between frames? --------
    # The free consistency check: combining spin-2 terms whose direction rotates
    # partially cancels, so if theta0 genuinely swings, the amplitude of the
    # COMBINED fit must sit BELOW the mean of the individual amplitudes by
    # exactly the resultant length of the theta0 distribution. If it does not,
    # the frames are not really disagreeing and a per-frame theta0 swing is a fit
    # artefact rather than a rotation.
    amps, dirs = [], []
    for k, c in rec["per_frame"].items():
        f = c["fit_flat_radial"]
        amps.append(f["fixed_amplitude"])
        dirs.append(f["fixed_direction_theta0_deg"])
    amps, dirs = np.asarray(amps), np.asarray(dirs)
    z = np.mean(amps * np.exp(2j * np.radians(dirs)))
    rec["ARM_7_theta0_rotation_consistency"] = {
        "n_frames": len(amps),
        "mean_individual_amplitude": float(amps.mean()),
        "vector_combined_amplitude": float(np.abs(z)),
        "resultant_of_theta0_distribution": float(np.abs(z) / amps.mean()),
        "combined_fit_amplitude_sample_a": rec["sample_a_full"][
            "fit_flat_radial"]["fixed_amplitude"],
        "reads": "resultant 1.0 = theta0 identical in every frame (no rotation); "
                 "below 1.0 = the direction genuinely moves, and the shortfall "
                 "IS the amount it moves. A combined amplitude equal to the mean "
                 "individual one would mean the per-frame swing is an artefact.",
    }

    # ---------------- acquisition control: did the OPTICS change? -----------
    # Before any optical reasoning: both candidate aberrations scale with
    # aperture, and on a zoom a focal-length change re-shapes the whole
    # aberration field. If these are not constant across the six sets, the
    # 10x swing in the radial term needs no optics argument at all.
    exif = {}
    for session in ("aug06", "july31"):
        for setname in ("set-01", "set-02", "set-03"):
            try:
                a = json.load(open(os.path.join(DATASETS, session, setname,
                                                "acquisition.json")))["exif"]
            except OSError:
                continue
            exif["%s/%s" % (session, setname)] = {
                k: a.get(k) for k in ("lens", "focal_length_mm", "focal_mm",
                                      "f_number", "fnumber", "aperture",
                                      "iso", "exposure_s", "camera")}
    rec["acquisition_control_optics_constant_across_sets"] = exif

    # ---------------- the shear form, as a convention control ---------------
    rec["ellipticity_form_control_shear_not_distortion"] = measure(
        db, W, H, form="shear", label="sample b, shear form")

    rec["reports_only"] = "MEASUREMENT. No threshold, no verdict. Exits 0."

    out = os.path.join(HERE, "pa_convention.json")
    with open(out, "w") as fh:
        json.dump(rec, fh, indent=1)
    print("wrote %s" % out)

    # a compact console read
    print()
    print("%-34s %7s %9s %8s %9s %8s %7s %s"
          % ("cell", "n", "fixedF", "F_SE", "radialR", "R_SE", "naive", "track"))
    cells = list(rec["ARM_1_statistic_crossed_with_population"]["cells"].items())
    cells += [("frame1_sigma0.50_floored",
               rec["ARM_2_depth_one_frame_two_sigmas"]["sigma_0p50"]),
              ("frame1_sigma1.00_floored",
               rec["ARM_2_depth_one_frame_two_sigmas"]["sigma_1p00"]),
              ("round_only__sample_b",
               rec["ARM_1b_round_star_degeneracy_null"]["sample_b"]),
              ("round_only__sample_a",
               rec["ARM_1b_round_star_degeneracy_null"]["sample_a"])]
    for name, r in cells:
        f, ss = r["fit_flat_radial"], r["sector_summary"]
        print("%-34s %7d %9.4f %8.1f %+9.4f %8.1f %7.1f %d/%d"
              % (name, r["n_stars"], f["fixed_amplitude"],
                 f["fixed_amplitude_SE_units_star_bootstrap"], f["radial_R"],
                 f["radial_SE_units_star_bootstrap"], ss["naive_PA_spread_deg"],
                 ss["sectors_tracking_azimuth_within_25deg"], ss["n_sectors"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
