#!/usr/bin/env python3
"""The ROUTE key — ONE definition, every consumer.

Which chain a set takes is decided by one measured quantity, defined here and
nowhere else. `disk_budget.sh` is the precedent for the shape: a shared
DERIVATION that every caller invokes, never a constant each caller repeats.
Its two private copies of one figure diverged 2x and routed a set to a builder
that then aborted its own preflight; the route key had six copies of a
`fov`-width test at 10 deg (the fingerprint label and its route branch, the
chain's initial and post-preflight derivations, the readiness evaluator, the
web rail's set position).

WHY FIELD WIDTH IS THE WRONG KEY — the physics, not the multiplicity. The
undistort route exists because the true frame-to-frame map of a drifting field
is `distort o H o distort^-1` (Kukelova et al., CVPR 2015, "Radial Distortion
Homography"). For an IDEAL rectilinear lens a pure camera rotation is EXACTLY
an 8-DOF homography (Szeliski, *Image Alignment and Stitching* 2.3 — stars at
infinity, sky rotation SO(3)), so the only residual an optimal global fit
leaves is unmodelled radial distortion: a star displaced proportional to radius
samples a DIFFERENT local distortion as it drifts, and no global fit absorbs
the difference. Field width does not appear in that mechanism, and keying on it
INVERTS the physics — a fixed mount sweeps 0.2507 x cos(dec) deg/min whatever
the focal length, so a NARROW field crosses more of itself per minute than a
wide one. A 10 deg width floor therefore excluded exactly the sets with the
largest excursion: a fixed tripod at 200 mm (fov ~2 deg) sweeps a full field
width in ~8 min and was refused as unroutable.

THE KEY: `drift_frac` — the sky excursion over the registration span, as a
fraction of the field.

    drift_frac = (sky_sep_deg / probe_span_min) x set_span_min / fov_deg

    sky_sep_deg     haversine of two astrometry.net solves
                    (scripts/qa/mount_probe.sh -> fingerprint.py
                    inter_frame_drift.sky_sep_arcsec)
    probe_span_min  the two solved frames' capture epochs (EXIF / DATE-OBS)
    set_span_min    the set's own capture span (acquisition exif.time_span_s)
    fov_deg         plate scale x frame width (scripts/lib/acquisition.py)

Every term is a tool's measurement; this module only divides them. The RATE
comes from the probe window and is extrapolated to the SET's span because the
registration unit is the set, not whichever window the probe happened to fit
inside the longest continuous run.

WHY AN ANGLE AND NOT `drift_px`. The record's `drift_px` is not a sensor-pixel
count. Camera raws solve on Siril's extracted GREEN plane — half the full-res
grid — so the probe's own scale reads 35.28-36.28 arcsec/px against the
sensor's 16.979, a factor 2.078-2.137 across this corpus (mount_probe.json
`domain_note`). The same physical excursion therefore reads half as many "px"
on an OSC raw as on a mono FITS frame that solves at native scale, and a px
threshold would mean two different things on two rigs — the rig-specific defect
this file exists to kill, wearing a new costume. An ANGLE over a FIELD is free
of the pixel grid, of binning, and of the debayer path.

THE THRESHOLD: drift_frac >= 0.05. It is a floor of EVIDENCE, not a quality
knee — no knee has ever been measured, and the residual is monotonic in drift
("the residual scales with TIME SPAN, not frame count",
docs/wide-field-untracked-registration.md). 0.05 is the SMALLEST excursion at
which this repo has MEASURED the term present:

  - the class was established at drift_frac 0.247 (43 min, ~1500 px at
    18.02"/px across a 30.35 deg field): Siril `seqtilt` off-axis aberration
    0.57 -> 0.31 px with the fitted lens model at 54 frames, 0.25 px at 168;
  - the shortest arm measured on the mechanism is a 9-min / ~310 px window =
    drift_frac 0.051, whole-frame majFWHM 3.87 px against the full span's
    4.74 px — better, and still the same mechanism. Below 0.051 the repo has no
    measurement, so this router claims none.

The key UNDER-COUNTS in two directions, both absorbed by putting the floor at
the bottom of the measured range rather than inside it:

  - the total `-framing=min` trim runs 1.16-1.29x the pure translation in every
    measured set (field rotation + warp border), so a set reading 0.05 really
    sweeps 0.058-0.065 of its field;
  - a set whose probe windowed inside its longest continuous run has its
    re-aim excursion excluded from the rate.

Corpus: the 12 real sets measure 0.083-0.201, the nearest 1.7x the floor.

BELOW THE FLOOR a fixed mount routes STANDARD rather than stopping. `standard`
is defined by "no inter-frame drift to fight", and an excursion smaller than
the smallest one the distortion term has ever been measured at is that
condition. Undistorting there is not free: it is a second interpolation pass,
and with an UNFITTED (community) lens model it MEASURED an introduced centre
band — 5.30 px majFWHM at the frame centre against the uncorrected control's
4.03 px (star_stations, docs/wide-field-untracked-registration.md). The stop
survives exactly where CLAUDE.md's evidence gate puts it: the mount signature
is neither fixed nor tracked, or the key's own inputs were never measured.

The derived block is RECORDED into fingerprint.json, so every routing decision
carries its number, its threshold and its instruments on the tracked record.
Consumers still call `derive()`/`from_records()` rather than trusting that
block: a shared derivation cannot go stale, a cached decision can, and
disk_budget.sh's precedent is a shared derivation.

REMOVAL CONDITION: retire the 0.05 floor the day a measured knee exists — an
undistort-vs-homography A/B on this mechanism at two drift fractions below
0.25, closing where the removable term drops under the route's own irreducible
residual (0.25 px off-axis aberration at full depth). Until then the floor
states what has been measured, not what is believed.
"""
import argparse
import json
import math
import os
import sys

# The route key's floor. Provenance + why it is an evidence floor and not a
# quality knee: the module docstring above. Changing it changes every consumer,
# which is the point.
DRIFT_FRAC_MIN = 0.05

# The two DERIVED routes. Single-pass `undistort` is an operator override
# (run_set_chain.sh force_route), never a derived outcome — groups is the
# standing shape for the class.
STANDARD = "standard"
UNDISTORT = "undistort-groups"

# resolved from this file's own location, so a record path never depends on the
# caller's cwd (scripts/lib/route.py -> the repo root)
_REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

PROVENANCE = ("drift_frac = sky excursion / field width, from astrometry.net "
              "two-window solves (scripts/qa/mount_probe.sh) + header facts "
              "(scripts/lib/acquisition.py); threshold and derivation in "
              "scripts/lib/route.py")


def drift_fraction(exif, drift):
    """The key: the sky excursion over the SET's span as a fraction of the
    field. Returns (value, terms); value is None when an instrument has not
    reported yet, with terms["why"] naming the one that has not."""
    exif, drift = exif or {}, drift or {}
    fov = exif.get("fov_deg")
    sep = drift.get("sky_sep_arcsec")
    probe_s = drift.get("span_s")
    set_s = exif.get("time_span_s")
    if not fov:
        return None, {"why": "no fov_deg on the acquisition record — the field "
                             "is plate scale x frame width; run the chain "
                             "preflight (scripts/lib/acquisition.py)"}
    if not sep or not probe_s:
        return None, {"why": "no two-solve drift on record — the excursion is "
                             "measured by scripts/qa/mount_probe.sh and lands "
                             "in fingerprint.json inter_frame_drift"}
    rate = (sep / 3600.0) / (probe_s / 60.0)      # deg/min, free of the px grid
    span_s = set_s or probe_s                     # the registration unit is the set
    return round(rate * (span_s / 60.0) / fov, 4), {
        "sky_sep_deg": round(sep / 3600.0, 4),
        "drift_deg_per_min": round(rate, 4),
        "probe_span_s": probe_s,
        "set_span_s": set_s,
        "fov_deg": fov,
        # the probe windows inside the longest continuous run, so a set with a
        # re-aim break is rated on the rate x the FULL span, not the window
        "span_extrapolated": bool(set_s and abs(set_s - probe_s) > 1.0),
    }


def derive(exif, mount, drift):
    """Route a set from its measured terms. `mount` is the EFFECTIVE mount —
    the measured signature when there is one, else the declaration. Returns the
    block recorded into fingerprint.json; route None means the instruments have
    not settled it and the caller stops."""
    value, terms = drift_fraction(exif, drift)
    block = {"route": None, "key": "drift_frac", "value": value,
             "threshold": DRIFT_FRAC_MIN, "terms": terms,
             "provenance": PROVENANCE, "reason": ""}
    if mount == "tracked":
        block["route"] = STANDARD
        block["reason"] = ("tracked mount: no inter-frame drift to fight -> "
                           "calibrate / register / stack")
        return block
    if mount != "fixed":
        block["reason"] = (
            f"mount signature '{mount or 'unmeasured'}' is neither fixed nor "
            "tracked — the two-window drift solve (scripts/qa/mount_probe.sh) "
            "or the user picks the route")
        return block
    if value is None:
        block["reason"] = ("fixed mount, but the route key is not measured "
                           "yet: " + terms["why"])
        return block
    span = ("the set" if not terms["span_extrapolated"]
            else "the set (rate from a %.0f s probe window inside a %.0f s set)"
                 % (terms["probe_span_s"], terms["set_span_s"]))
    if value >= DRIFT_FRAC_MIN:
        block["route"] = UNDISTORT
        block["reason"] = (
            f"fixed mount: the sky sweeps {value:.3f} of the field over {span} "
            f"({terms['sky_sep_deg']:.2f} deg at {terms['drift_deg_per_min']:.3f} "
            f"deg/min across a {terms['fov_deg']} deg field), at or above the "
            f"{DRIFT_FRAC_MIN} floor the distortion term is measured at — the "
            "frame-to-frame map is distort o H o distort^-1, so the route "
            "undistorts before the homography; groups is the STANDING shape")
    else:
        block["route"] = STANDARD
        block["reason"] = (
            f"fixed mount, but the sky sweeps only {value:.3f} of the field "
            f"over {span} — below the {DRIFT_FRAC_MIN} floor, the smallest "
            "excursion the distortion term has been measured at. No drift "
            "differential to fight, and undistorting would cost a second "
            "interpolation pass")
    return block


def from_records(acq, fp):
    """Route from a set's tracked records (acquisition.json, fingerprint.json
    as dicts). The one entry point every consumer outside fingerprint.py
    uses — so the key is imported, never repeated."""
    acq, fp = acq or {}, fp or {}
    mount = ((fp.get("mount_check") or {}).get("measured")) or acq.get("mount")
    return derive(acq.get("exif") or {}, mount, fp.get("inter_frame_drift"))


def from_dataset_dir(droot):
    """Route from a per-set record directory (datasets/<session>/<set>)."""
    def rd(name):
        try:
            return json.load(open(os.path.join(droot, name)))
        except (OSError, ValueError):
            return {}
    return from_records(rd("acquisition.json"), rd("fingerprint.json"))


def _selftest():
    """Route the classes the key must serve, through the SAME derive() the
    chain calls. Fixtures are stated in the RECORD's own shape (an exif block
    and an inter_frame_drift block), so what is exercised is the live branch.
    The corpus rows are read from the tracked records, not restated here."""
    ok = True

    def flag(name, cond, detail=""):
        nonlocal ok
        ok = ok and cond
        print(f"  [{'PASS' if cond else 'FAIL'}] {name}" + (f" — {detail}" if detail else ""))

    def sky(exposure_deg_per_min, span_s, dec=0.0):
        """An inter_frame_drift block in the record's shape."""
        sep = exposure_deg_per_min * (span_s / 60.0) * 3600.0
        return {"span_s": span_s, "sky_sep_arcsec": round(sep, 2)}

    SIDEREAL_DEG_PER_MIN = 15.041 * 60.0 / 3600.0     # 0.2507 deg/min at dec 0

    # --- the corpus, from its own tracked records -------------------------
    corpus, lo = [], None
    for sess in ("july31", "aug06", "aug09"):
        for n in range(1, 6):
            d = os.path.join(_REPO, "datasets", sess, f"set-{n:02d}")
            if not os.path.isdir(d):
                continue
            b = from_dataset_dir(d)
            corpus.append((f"{sess}/set-{n:02d}", b))
            if b["value"] is not None and (lo is None or b["value"] < lo[1]):
                lo = (f"{sess}/set-{n:02d}", b["value"])
    flag(f"corpus: {len(corpus)} real sets all derive {UNDISTORT}",
         len(corpus) == 12 and all(b["route"] == UNDISTORT for _, b in corpus),
         f"nearest the floor: {lo[0]} at {lo[1]} = {lo[1] / DRIFT_FRAC_MIN:.2f}x")

    # --- 200 mm on APS-C, fixed tripod: fov 6.74 deg, BELOW any 10 deg width
    # floor, and sweeping 3.5x the drift floor over a 5 min set ------------
    aps_c = {"fov_deg": 6.74, "time_span_s": 300.0}
    b = derive(aps_c, "fixed", sky(SIDEREAL_DEG_PER_MIN * math.cos(math.radians(20)),
                                   300.0))
    flag("200 mm / APS-C fixed (fov 6.74 deg) routes to the undistort class",
         b["route"] == UNDISTORT, f"drift_frac {b['value']}")

    # --- the prompt's 2 deg case: small field, large drift ----------------
    narrow = {"fov_deg": 2.0, "time_span_s": 180.0}
    b2 = derive(narrow, "fixed", sky(SIDEREAL_DEG_PER_MIN, 180.0))
    flag("fixed, fov 2.0 deg routes to the undistort class",
         b2["route"] == UNDISTORT, f"drift_frac {b2['value']}")

    # --- mono, tracked, narrow (colonnello-m20's shape): standard, and the
    # roundness check leaves no drift record to key on --------------------
    b3 = derive({"fov_deg": 0.88, "time_span_s": 1372.0}, "tracked", None)
    flag("mono/tracked (fov 0.88 deg, no drift record) routes standard",
         b3["route"] == STANDARD, b3["reason"][:46])

    # --- below the floor: a fixed set too short to sweep 0.05 of its field
    b4 = derive({"fov_deg": 28.6, "time_span_s": 240.0},
                "fixed", sky(SIDEREAL_DEG_PER_MIN * math.cos(math.radians(41.5)), 240.0))
    flag("fixed but below the floor routes standard, not to a stop",
         b4["route"] == STANDARD and b4["value"] < DRIFT_FRAC_MIN,
         f"drift_frac {b4['value']}")

    # --- the stops: only where the instruments cannot settle it -----------
    b5 = derive({"fov_deg": 28.6, "time_span_s": 1497.0}, None, None)
    flag("unclassified mount signature -> no route (the caller stops)",
         b5["route"] is None)
    b6 = derive({"fov_deg": 28.6, "time_span_s": 1497.0}, "fixed", None)
    flag("fixed but drift never measured -> no route, naming the probe",
         b6["route"] is None and "mount_probe" in b6["reason"])

    # --- GRID INDEPENDENCE: the property drift_px lacks. The same physical
    # excursion recorded on the half-res green grid and at native scale must
    # give ONE key value; drift_px differs by the scale ratio -------------
    d_green = sky(SIDEREAL_DEG_PER_MIN * math.cos(math.radians(41.5)), 1837.9)
    exif = {"fov_deg": 28.6, "time_span_s": 1837.9}
    v_green, _ = drift_fraction(exif, dict(d_green, drift_px=575.3))
    v_native, _ = drift_fraction(exif, dict(d_green, drift_px=575.3 * 2.121))
    flag("drift_frac is identical on the green-plane and native grids",
         v_green == v_native,
         f"{v_green} both; drift_px would read 575.3 vs {575.3 * 2.121:.1f}")

    print("SELFTEST", "PASS" if ok else "FAIL")
    return 0 if ok else 1


def main():
    ap = argparse.ArgumentParser(description="print a set's derived route")
    ap.add_argument("session", nargs="?", help="session dir (sessions/<name>)")
    ap.add_argument("set", nargs="?")
    ap.add_argument("--json", action="store_true", help="print the whole block")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        return _selftest()
    if not (a.session and a.set):
        ap.error("session and set are required (or --selftest)")
    droot = os.path.join(_REPO, "datasets",
                         os.path.basename(os.path.normpath(a.session)), a.set)
    block = from_dataset_dir(droot)
    if a.json:
        print(json.dumps(block, indent=1))
        return 0
    # two lines, so a shell consumer reads both without parsing: route (empty
    # when the instruments have not settled it), then the reason
    print(block["route"] or "")
    print(block["reason"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
