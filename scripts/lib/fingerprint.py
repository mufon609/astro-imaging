#!/usr/bin/env python3
"""Derive a set's CONFIG FINGERPRINT from the data — the MEASURE->MATCH input.

The fingerprint is what a dataset IS, worked out from tool measurements rather
than declared: {exposure, focal, plate scale, predicted in-exposure trail,
measured per-frame roundness, inter-frame drift rate vs sidereal} -> a label
like "untracked, wide, drifting 34 px/min" that selects the processing route.

Every term is tool-measured. This module reads those tool outputs and computes
only the DERIVED trail/drift geometry NO tool reports; it reads no pixel and
runs no solver:
  - EXIF (exposure, focal, nominal scale)     scripts/lib/acquisition.py (exiftool)
  - field RA/Dec + TRUE plate scale           scripts/calibrate/solve_field.py (astrometry.net)
  - per-frame roundness                        Siril findstar (frame_metrics.json)

`mount` STAYS a declared fact — EXIF cannot record it and a consumer must never
assume one (acquisition.py stops if it is undeclared). What this module adds is
a CROSS-CHECK: two astrometric solves separated in time MEASURE the sky motion,
and a fixed mount advances RA at the sidereal rate with Dec constant while a
tracked mount holds both. So a measured signature can CONFIRM or CONTRADICT the
declaration — strictly better than either alone. `mount_verdict` returns
CONTRADICT when a set declared one way moves the other; the consumer STOPS and
reconciles. It never silently re-labels: the declaration is the human's, the
measurement only checks it.

The fingerprint RECOMMENDS a route (the MATCH step). It does not execute one —
the operating loop keeps the user as the gate before any output-shaping run.

REMOVAL CONDITION: retire the derived-geometry computation the day an official
tool reports headless trail/drift geometry with a declared-vs-measured mount
cross-check (e.g. a solver exposing inter-epoch drift rate vs sidereal); the
record schema and the STOP-on-CONTRADICT contract stay wherever that lands.
"""
import argparse
import json
import math
import os
import sys

_here = os.path.dirname(os.path.abspath(__file__))
if _here not in sys.path:
    sys.path.insert(0, _here)
import acquisition  # noqa: E402
import astrometrics as am  # noqa: E402

# Sidereal rate. A star's RA coordinate advances at 15.041 arcsec per second of
# time; numerically the same constant is 15.041 deg/hr (1 deg = 3600 arcsec, 1
# hr = 3600 s), so it serves both the arcsec/s trail math and the deg/hr mount
# check. The star's LINEAR sky speed is this * cos(dec).
SIDEREAL = 15.041

# Mount classification bands on the measured RA rate as a fraction of sidereal:
# a fixed mount sits at ~1.0 (measured 0.997 on july14/set-01), a tracked mount
# near 0. The gap between is deliberately left UNCLASSIFIED (partial tracking /
# drift / bad polar alignment) rather than forced into a label.
_FIXED_BAND = (0.80, 1.20)
_TRACKED_MAX = 0.20


def trail_px(exposure_s, dec_deg, scale_arcsec_px):
    """In-exposure star elongation (px) — the untracked sharpness FLOOR. No
    registration removes it; it is set at capture by exposure x sky rate."""
    return SIDEREAL * math.cos(math.radians(dec_deg)) * exposure_s / scale_arcsec_px


def sidereal_drift_px_per_min(dec_deg, scale_arcsec_px):
    """The inter-frame drift a FIXED mount MUST show at this dec/scale — the
    expected value the measured drift is checked against."""
    return SIDEREAL * math.cos(math.radians(dec_deg)) * 60.0 / scale_arcsec_px


def angular_sep_arcsec(ra1, dec1, ra2, dec2):
    """Great-circle separation of two sky points (arcsec), haversine."""
    r1, d1, r2, d2 = map(math.radians, (ra1, dec1, ra2, dec2))
    h = (math.sin((d2 - d1) / 2) ** 2
         + math.cos(d1) * math.cos(d2) * math.sin((r2 - r1) / 2) ** 2)
    return math.degrees(2 * math.asin(min(1.0, math.sqrt(h)))) * 3600.0


def _wrap180(deg):
    """Signed RA difference in (-180, 180], so a solve pair spanning 0h/24h or
    ordered either way gives the true small angle."""
    return (deg + 180.0) % 360.0 - 180.0


def drift_between_solves(a, b):
    """Field motion between two solves. a, b = {ra_deg, dec_deg, time_s,
    scale_arcsec_px}; time_s is each solved frame's capture epoch (seconds).
    Returns the RA rate (deg/hr), Dec drift (arcsec), on-sky separation
    (arcsec) and the on-sensor drift (px, px/min). This is the derived
    geometry no tool reports; every input is a tool's solve."""
    span = abs(b["time_s"] - a["time_s"])
    ra_rate = _wrap180(b["ra_deg"] - a["ra_deg"]) / (span / 3600.0) if span else None
    dec_drift = (b["dec_deg"] - a["dec_deg"]) * 3600.0
    sep = angular_sep_arcsec(a["ra_deg"], a["dec_deg"], b["ra_deg"], b["dec_deg"])
    scale = a.get("scale_arcsec_px") or b.get("scale_arcsec_px")
    px = sep / scale if scale else None
    return {"span_s": round(span, 1),
            "ra_rate_deg_per_hr": round(ra_rate, 4) if ra_rate is not None else None,
            "dec_drift_arcsec": round(dec_drift, 2),
            "sky_sep_arcsec": round(sep, 2),
            "drift_px": round(px, 1) if px is not None else None,
            "drift_px_per_min": round(px / (span / 60.0), 2)
            if (px is not None and span) else None}


def classify_mount(ra_rate_deg_per_hr):
    """The mount SIGNATURE the measured RA rate implies: 'fixed' at ~sidereal,
    'tracked' near 0, None in the ambiguous gap between (never forced)."""
    if ra_rate_deg_per_hr is None:
        return None
    frac = abs(ra_rate_deg_per_hr) / SIDEREAL
    if _FIXED_BAND[0] <= frac <= _FIXED_BAND[1]:
        return "fixed"
    if frac < _TRACKED_MAX:
        return "tracked"
    return None


def mount_verdict(declared, measured, ra_rate=None):
    """Cross-check the DECLARED mount against the MEASURED signature.
    CONFIRM / CONTRADICT (consumer STOPS) / INDETERMINATE (report, no stop)."""
    if measured is None:
        return {"verdict": "INDETERMINATE", "declared": declared, "measured": measured,
                "reason": ("no two-solve drift measured yet, or the RA rate "
                           f"({ra_rate}) is neither a clean sidereal nor a "
                           "stationary signature — declaration stands unchecked")}
    if declared is None:
        return {"verdict": "INDETERMINATE", "declared": declared, "measured": measured,
                "reason": f"mount undeclared; the data reads as {measured}"}
    if declared == measured:
        return {"verdict": "CONFIRM", "declared": declared, "measured": measured,
                "reason": f"declared {declared} matches the measured {measured} sky-motion signature"}
    return {"verdict": "CONTRADICT", "declared": declared, "measured": measured,
            "reason": (f"declared {declared} but the sky moves like a {measured} mount "
                       "— a labelling error. STOP and reconcile the declaration "
                       "with the frames before routing.")}


def _label(exif, drift, mount):
    """Human-readable fingerprint: mount x field-width x drift."""
    fov = exif.get("fov_deg")
    width = "wide" if (fov and fov >= 10) else ("normal" if fov else "?")
    m = mount or "?mount"
    ppm = (drift or {}).get("drift_px_per_min")
    tail = f", drifting {ppm:.0f} px/min" if ppm else ""
    kind = {"fixed": "untracked", "tracked": "tracked"}.get(m, m)
    return f"{kind}, {width}{tail}"


def fingerprint(exif, declared_mount, *, solve=None, drift=None, roundness=None):
    """Assemble the fingerprint from tool outputs. Pure: no I/O, no solving.

    exif           acquisition.json `exif` block
    declared_mount acquisition.json `mount` (the human field; may be None)
    solve          {ra_deg, dec_deg, scale_arcsec_px} field solve, or None
    drift          drift_between_solves() output, or None
    roundness      measured median per-frame roundness (findstar), or None
    """
    dec = (solve or {}).get("dec_deg")
    scale = (solve or {}).get("scale_arcsec_px")
    scale_src = "solved"
    if not scale:                       # fall back to the EXIF-nominal scale
        scale = exif.get("pixel_scale_arcsec")
        scale_src = "exif-nominal"
    exp = exif.get("exposure_s")

    trail = (round(trail_px(exp, dec, scale), 2)
             if (exp and dec is not None and scale) else None)
    sid_ppm = (round(sidereal_drift_px_per_min(dec, scale), 2)
               if (dec is not None and scale) else None)

    measured_sig = classify_mount((drift or {}).get("ra_rate_deg_per_hr"))
    verdict = mount_verdict(declared_mount, measured_sig,
                            (drift or {}).get("ra_rate_deg_per_hr"))
    if drift is not None:               # attach the expected value for context
        drift = {**drift, "sidereal_px_per_min_expected": sid_ppm}

    return {
        "measured_by": ("EXIF (acquisition.py/exiftool) + astrometry.net solve "
                        "(solve_field.py) + Siril findstar roundness; this module "
                        "computes only the derived trail/drift geometry and records it"),
        "declared_mount": declared_mount,
        "plate_scale_arcsec_px": round(scale, 4) if scale else None,
        "plate_scale_source": scale_src,
        "field_center": ({"ra_deg": solve.get("ra_deg"), "dec_deg": dec}
                         if solve else None),
        "in_exposure_trail": {
            "predicted_px": trail,
            "measured_roundness": roundness,
            "note": ("floor set at capture; no registration removes it. predicted "
                     "= 15.041 * cos(dec) * exposure / plate_scale")},
        "inter_frame_drift": drift,
        "mount_check": verdict,
        "label": _label(exif, drift, measured_sig or declared_mount),
        "route_hint": ("wide-field-untracked (undistort -> homography) — a wide "
                       "field on a fixed mount with measurable drift"
                       if (measured_sig or declared_mount) == "fixed"
                       and (exif.get("fov_deg") or 0) >= 10
                       else "unclassified — measure before routing"),
    }


def load_solve(path, time_s=None):
    """Read a solve_field.py record ({ra_deg, dec_deg, scale_arcsec_px}) and
    attach a capture epoch for the drift math. Times come from the solved
    frames' EXIF (acquisition.timeline), never invented here."""
    r = json.load(open(path))
    out = {"ra_deg": r["ra_deg"], "dec_deg": r["dec_deg"],
           "scale_arcsec_px": r.get("scale_arcsec_px")}
    if time_s is not None:
        out["time_s"] = time_s
    return out


def derive(session_dir, set_name, *, solve_a=None, solve_b=None,
           roundness=None, write=True):
    """Build (and optionally record) a set's fingerprint from its tracked
    acquisition record plus optional window solves.

    solve_a/solve_b: two solves as {ra_deg, dec_deg, time_s, scale_arcsec_px}
    (start and end of the set) — both present drives the drift + mount check.
    Writes datasets/<session>/<set>/fingerprint.json when `write`."""
    apath = acquisition.record_path(session_dir, set_name)
    if not os.path.exists(apath):
        raise FileNotFoundError(
            f"fingerprint: no acquisition.json for {session_dir}/{set_name} — "
            "seed it first (acquisition.resolve); mount must be declared")
    acq = json.load(open(apath))
    exif = acq.get("exif") or {}
    declared = acq.get("mount")

    drift = None
    solve = solve_a
    if solve_a and solve_b and "time_s" in solve_a and "time_s" in solve_b:
        drift = drift_between_solves(solve_a, solve_b)

    fp = fingerprint(exif, declared, solve=solve, drift=drift, roundness=roundness)
    if write:
        out = os.path.join(am.dataset_dir(session_dir, set_name), "fingerprint.json")
        os.makedirs(os.path.dirname(out), exist_ok=True)
        json.dump(fp, open(out, "w"), indent=1)
        fp["_written"] = out
    return fp


def _selftest():
    """Validate the derived geometry against july14/set-01's independently
    recorded numbers (registration_qa.json): trail 3.40 px, drift 34 px/min, RA
    14.99 deg/hr vs sidereal, mount CONFIRM fixed."""
    ok = True

    def check(name, got, want, tol):
        nonlocal ok
        p = abs(got - want) <= tol
        ok = ok and p
        print(f"  [{'PASS' if p else 'FAIL'}] {name}: {got:.3f} (want {want} +-{tol})")

    check("trail_px(6, 47.04, 18.02)", trail_px(6, 47.044, 18.02), 3.40, 0.05)
    check("sidereal_drift_px_per_min(47.04, 18.02)",
          sidereal_drift_px_per_min(47.044, 18.02), 34.1, 0.5)
    # two solves 43 min apart (registration_qa.json endpoints)
    a = {"ra_deg": 306.047, "dec_deg": 47.043, "time_s": 0.0, "scale_arcsec_px": 18.02}
    b = {"ra_deg": 306.047 + 10.816, "dec_deg": 47.045, "time_s": 2597.0,
         "scale_arcsec_px": 18.02}
    d = drift_between_solves(a, b)
    check("drift RA rate deg/hr", d["ra_rate_deg_per_hr"], 14.99, 0.05)
    check("drift px/min", d["drift_px_per_min"], 34.0, 0.6)
    check("drift dec arcsec", d["dec_drift_arcsec"], 7.2, 0.5)
    sig = classify_mount(d["ra_rate_deg_per_hr"])
    v = mount_verdict("fixed", sig)
    print(f"  [{'PASS' if v['verdict'] == 'CONFIRM' else 'FAIL'}] "
          f"mount fixed -> {v['verdict']} (measured {sig})")
    ok = ok and v["verdict"] == "CONFIRM"
    # a mislabelled set must be caught
    vt = mount_verdict("tracked", sig)
    print(f"  [{'PASS' if vt['verdict'] == 'CONTRADICT' else 'FAIL'}] "
          f"mislabel tracked -> {vt['verdict']}")
    ok = ok and vt["verdict"] == "CONTRADICT"
    print("SELFTEST", "PASS" if ok else "FAIL")
    return 0 if ok else 1


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("session", nargs="?")
    ap.add_argument("set", nargs="?")
    ap.add_argument("--solve-a", help="start-window solve JSON (solve_field.py record)")
    ap.add_argument("--solve-b", help="end-window solve JSON")
    ap.add_argument("--time-a", type=float, help="capture epoch (s) of solve-a's frame")
    ap.add_argument("--time-b", type=float, help="capture epoch (s) of solve-b's frame")
    ap.add_argument("--roundness", type=float, help="measured median per-frame roundness")
    ap.add_argument("--no-write", action="store_true")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        return _selftest()
    if not (a.session and a.set):
        ap.error("session and set are required (or --selftest)")
    sa = load_solve(a.solve_a, a.time_a) if a.solve_a else None
    sb = load_solve(a.solve_b, a.time_b) if a.solve_b else None
    fp = derive(a.session, a.set, solve_a=sa, solve_b=sb,
                roundness=a.roundness, write=not a.no_write)
    print(json.dumps(fp, indent=1))
    if fp.get("mount_check", {}).get("verdict") == "CONTRADICT":
        print(fp["mount_check"]["reason"], file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
