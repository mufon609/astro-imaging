#!/usr/bin/env python3
"""Derive a set's CONFIG FINGERPRINT from the data — the MEASURE->MATCH input.

The fingerprint is what a dataset IS, worked out from tool measurements rather
than declared: {exposure, focal, plate scale, predicted in-exposure trail,
measured per-frame roundness, inter-frame drift rate vs sidereal} -> a label
like "untracked, wide, drifting 34 px/min" that selects the processing route.

Every term is tool-measured. This module reads those tool outputs and computes
only the DERIVED trail/drift geometry NO tool reports; it reads no pixel and
runs no solver:
  - header facts (exposure, scale, pointing)     scripts/lib/acquisition.py
  - field RA/Dec + TRUE plate scale              scripts/calibrate/solve_field.py (astrometry.net)
  - per-frame roundness / FWHM / star counts     Siril findstar+register (frame_metrics.json)

`mount` STAYS a declared fact — headers cannot be trusted to record it and a
consumer must never assume one (acquisition.py stops if it is undeclared).
What this module adds is a CROSS-CHECK by two instruments, each measuring the
sky against the declaration:

  1. TRAIL-vs-ROUNDNESS (cheap — no solve). A fixed mount smears every sub by
     15.041"/s x cos(dec) x exposure / scale. When that predicted trail is
     DECISIVELY beyond the elongation the measured stars could hide (>= 10x,
     with a real matched star population), the mount must be tracking. The
     check is one-sided by construction: it can rule OUT fixed, never prove
     it — elongation has non-mount causes (wind, flexure, guiding), so
     agreement with the prediction stays consistent-with-fixed, not proof.
  2. DRIFT SOLVES (precise — two solves separated in time). A fixed mount
     advances RA at the sidereal rate with Dec constant; a tracked mount
     holds both. The instrument near the boundary, where roundness cannot
     decide (e.g. a 3.4 px predicted trail on a 3.5 px PSF).

`mount_verdict` returns CONTRADICT when a set declared one way measures the
other; the consumer STOPS and reconciles. It never silently re-labels: the
declaration is the human's, the measurement only checks it.

The fingerprint RECOMMENDS a route (the MATCH step). It does not execute one —
the operating loop keeps the user as the gate before any output-shaping run.
`refresh()` is the automatic seeding entry: it derives from whatever tracked
records exist and rewrites the record only when its content changes, so every
record-landing moment (mount declaration, frame QA) can call it idempotently.

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

# The trail-vs-roundness check calls itself decisive only when the predicted
# trail exceeds the worst elongation the measured stars could hide by an order
# of magnitude — "~1600 px vs round" decides; "3.4 px vs a 3.5 px PSF" does
# not (that is the drift solves' regime).
DECISIVE_RATIO = 10.0


def trail_px(exposure_s, dec_deg, scale_arcsec_px):
    """In-exposure star elongation (px) a FIXED mount would put in every sub —
    the untracked sharpness FLOOR. No registration removes it; it is set at
    capture by exposure x sky rate."""
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


def trail_roundness_check(predicted_px, metrics):
    """The cheap mount instrument: predicted-if-fixed in-exposure trail vs the
    elongation Siril's own findstar fits actually measured. One-sided — it can
    only ever conclude 'tracked' (rule out fixed), and only when DECISIVE:

      implied_trail_max = worst FWHM x sqrt(1/roundness_worst^2 - 1)
        (Siril roundness = FWHMy/FWHMx, minor/major — the largest in-exposure
         trail the measured star shapes could be hiding, worst case)
      decisive          = predicted >= 10x that bound, AND the tool matched a
                          real star field (median >= 100 stars/frame and at
                          least half the frames registered — a truly smeared
                          set cannot produce stable cross-matched star fields,
                          so this guards against reading roundness off noise)

    Near the boundary it declines (returns signature None) and names the
    two-window drift solve as the instrument. `metrics` is the tracked
    frame_metrics.json distribution (see _load_metrics)."""
    if not predicted_px or not metrics:
        return None
    r_med = metrics.get("roundness_median")
    f_med = metrics.get("fwhm_median_px")
    if r_med is None or f_med is None:
        return None
    r_w = min(max(metrics.get("roundness_min") or r_med, 1e-3), 0.999)
    f_w = metrics.get("fwhm_max_px") or f_med
    implied_max = f_w * math.sqrt(1.0 / (r_w * r_w) - 1.0)
    margin = predicted_px / max(implied_max, 1.0)
    nstars = metrics.get("nstars_median")
    reg, tot = metrics.get("registered"), metrics.get("frames_total")
    population_ok = (nstars is not None and nstars >= 100
                     and reg is not None and bool(tot) and reg >= tot / 2.0)
    decisive = margin >= DECISIVE_RATIO and population_ok
    if decisive:
        reason = (f"a fixed mount here would smear every sub by ~{predicted_px:.0f} px; "
                  f"the measured stars could hide at most {implied_max:.1f} px "
                  f"(findstar roundness {r_med} / FWHM {f_med} px over {tot} frames, "
                  f"~{nstars:.0f} stars/frame, {reg}/{tot} registered) — "
                  f"{margin:.0f}x apart: the mount is tracking. No solve needed.")
    elif not population_ok:
        reason = ("star population too thin or unmatched for a decisive "
                  "roundness read — the two-window drift solve is the instrument")
    else:
        reason = (f"predicted-if-fixed trail {predicted_px:.1f} px vs up to "
                  f"{implied_max:.1f} px of measured elongation — within "
                  f"{DECISIVE_RATIO:.0f}x: not decisive; the two-window drift "
                  "solve is the instrument near the boundary")
    return {"predicted_if_fixed_px": round(predicted_px, 1),
            "implied_trail_max_px": round(implied_max, 2),
            "margin": round(margin, 1), "population_ok": population_ok,
            "decisive": decisive,
            "signature": "tracked" if decisive else None,
            "reason": reason}


def mount_verdict(declared, drift_sig=None, ra_rate=None, trail_check=None):
    """Cross-check the DECLARED mount against the MEASURED signature(s).
    CONFIRM / CONTRADICT (consumer STOPS) / INDETERMINATE (report, no stop).
    Two instruments feed it: the drift solves (precise, either signature) and
    the trail-vs-roundness check (cheap, 'tracked' only when decisive). When
    both measure and disagree the verdict is INDETERMINATE with both readings
    — two instruments in conflict is a measurement problem, not a label."""
    tc_sig = (trail_check or {}).get("signature")
    if drift_sig and tc_sig and drift_sig != tc_sig:
        return {"verdict": "INDETERMINATE", "declared": declared, "measured": None,
                "method": "drift-solves vs trail-vs-roundness",
                "reason": (f"instruments disagree: drift solves read {drift_sig} "
                           f"(RA rate {ra_rate} deg/hr) but trail-vs-roundness "
                           f"reads {tc_sig} — re-measure before trusting either; "
                           "declaration stands unchecked")}
    measured = drift_sig or tc_sig
    method = ("drift-solves + trail-vs-roundness" if (drift_sig and tc_sig)
              else "drift-solves" if drift_sig
              else "trail-vs-roundness" if tc_sig else None)
    if measured is None:
        reason = ((trail_check or {}).get("reason")
                  or ("no two-solve drift measured yet, or the RA rate "
                      f"({ra_rate}) is neither a clean sidereal nor a "
                      "stationary signature — declaration stands unchecked"))
        return {"verdict": "INDETERMINATE", "declared": declared,
                "measured": None, "method": None, "reason": reason}
    detail = (trail_check["reason"] if tc_sig
              else f"RA advances {ra_rate} deg/hr vs sidereal {SIDEREAL}")
    if declared is None:
        return {"verdict": "INDETERMINATE", "declared": declared,
                "measured": measured, "method": method,
                "reason": f"mount undeclared; the data reads as {measured} ({detail})"}
    if declared == measured:
        return {"verdict": "CONFIRM", "declared": declared, "measured": measured,
                "method": method,
                "reason": (f"declared {declared} matches the measured {measured} "
                           f"signature — {detail}")}
    return {"verdict": "CONTRADICT", "declared": declared, "measured": measured,
            "method": method,
            "reason": (f"declared {declared} but the data measures {measured} "
                       f"({detail}) — a labelling error. STOP and reconcile the "
                       "declaration with the frames before routing.")}


def _label(exif, drift, mount):
    """Human-readable fingerprint: mount x field-width x drift."""
    fov = exif.get("fov_deg")
    width = ("wide" if fov >= 10 else "narrow" if fov < 2 else "normal") \
        if fov else "?"
    m = mount or "?mount"
    ppm = (drift or {}).get("drift_px_per_min")
    tail = f", drifting {ppm:.0f} px/min" if ppm else ""
    kind = {"fixed": "untracked", "tracked": "tracked"}.get(m, m)
    return f"{kind}, {width}{tail}"


def fingerprint(exif, declared_mount, *, solve=None, drift=None, metrics=None):
    """Assemble the fingerprint from tool outputs. Pure: no I/O, no solving.

    exif           acquisition.json `exif` block (incl. header pointing when
                   the capture software recorded it)
    declared_mount acquisition.json `mount` (the human field; may be None)
    solve          {ra_deg, dec_deg, scale_arcsec_px} field solve, or None
    drift          drift_between_solves() output, or None
    metrics        _load_metrics() output (tracked frame_metrics.json), or None
    """
    dec = (solve or {}).get("dec_deg")
    dec_src = "solved" if dec is not None else None
    if dec is None:
        dec = exif.get("pointing_dec_deg")
        dec_src = "header-pointing" if dec is not None else None
    scale = (solve or {}).get("scale_arcsec_px")
    scale_src = "solved"
    if not scale:                       # fall back to the header-nominal scale
        scale = exif.get("pixel_scale_arcsec")
        scale_src = "exif-nominal"
    exp = exif.get("exposure_s")

    trail = (round(trail_px(exp, dec, scale), 2)
             if (exp and dec is not None and scale) else None)
    sid_ppm = (round(sidereal_drift_px_per_min(dec, scale), 2)
               if (dec is not None and scale) else None)

    tcheck = trail_roundness_check(trail, metrics)
    drift_sig = classify_mount((drift or {}).get("ra_rate_deg_per_hr"))
    verdict = mount_verdict(declared_mount, drift_sig,
                            (drift or {}).get("ra_rate_deg_per_hr"), tcheck)
    measured = verdict.get("measured")
    if drift is not None:               # attach the expected value for context
        drift = {**drift, "sidereal_px_per_min_expected": sid_ppm}

    effective = measured or declared_mount
    fov = exif.get("fov_deg") or 0
    if effective == "fixed" and fov >= 10:
        route = ("wide-field-untracked (undistort -> homography) — a wide "
                 "field on a fixed mount with measurable drift")
    elif effective == "tracked":
        route = ("standard (calibrate -> register -> stack) — tracked mount: "
                 "no inter-frame drift to fight")
    else:
        route = "unclassified — measure before routing"

    return {
        "measured_by": ("header facts (acquisition.py) + astrometry.net solves "
                        "(solve_field.py) + Siril findstar/register metrics "
                        "(frame_metrics.json); this module computes only the "
                        "derived trail/drift geometry and records it"),
        "declared_mount": declared_mount,
        "plate_scale_arcsec_px": round(scale, 4) if scale else None,
        "plate_scale_source": scale_src,
        "field_center": ({"ra_deg": (solve or {}).get("ra_deg",
                                     exif.get("pointing_ra_deg")),
                          "dec_deg": dec, "source": dec_src}
                         if dec is not None else None),
        "in_exposure_trail": {
            "predicted_if_fixed_px": trail,
            "measured_roundness": (metrics or {}).get("roundness_median"),
            "measured_fwhm_px": (metrics or {}).get("fwhm_median_px"),
            "check": tcheck,
            "note": ("predicted = 15.041 * cos(dec) * exposure / plate_scale — "
                     "the smear a FIXED mount would put in every sub; no "
                     "registration removes it")},
        "inter_frame_drift": drift,
        "mount_check": verdict,
        "label": _label(exif, drift, effective),
        "route_hint": route,
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


def _load_metrics(session_dir, set_name):
    """The tracked frame-QA distribution, reshaped for the roundness check.
    None when the set has no frame_metrics.json yet (the check just waits)."""
    p = os.path.join(am.dataset_dir(session_dir, set_name),
                     "qa_work", "frame_metrics.json")
    try:
        rec = json.load(open(p))
    except (OSError, ValueError):
        return None
    dist = rec.get("distribution") or {}
    r = dist.get("roundness") or {}
    f = dist.get("fwhm_px") or {}
    n = dist.get("nstars") or {}
    if r.get("median") is None:
        return None
    return {"roundness_median": r.get("median"), "roundness_min": r.get("min"),
            "fwhm_median_px": f.get("median"), "fwhm_max_px": f.get("max"),
            "nstars_median": n.get("median"),
            "registered": rec.get("registered"),
            "frames_total": rec.get("frames_total")}


def derive(session_dir, set_name, *, solve_a=None, solve_b=None,
           metrics=None, write=True):
    """Build (and optionally record) a set's fingerprint from its tracked
    records plus optional window solves.

    solve_a/solve_b: two solves as {ra_deg, dec_deg, time_s, scale_arcsec_px}
    (start and end of the set) — both present drives the drift + mount check.
    metrics: override for the frame-QA stats (auto-loaded from the tracked
    frame_metrics.json when None). Writes fingerprint.json only when its
    content changes, so record-landing hooks can call this idempotently."""
    apath = acquisition.record_path(session_dir, set_name)
    if not os.path.exists(apath):
        raise FileNotFoundError(
            f"fingerprint: no acquisition.json for {session_dir}/{set_name} — "
            "seed it first (acquisition.resolve); mount must be declared")
    acq = json.load(open(apath))
    exif = acq.get("exif") or {}
    declared = acq.get("mount")

    if metrics is None:
        metrics = _load_metrics(session_dir, set_name)
    drift = None
    solve = solve_a
    if solve_a and solve_b and "time_s" in solve_a and "time_s" in solve_b:
        drift = drift_between_solves(solve_a, solve_b)

    fp = fingerprint(exif, declared, solve=solve, drift=drift, metrics=metrics)
    if write:
        out = os.path.join(am.dataset_dir(session_dir, set_name),
                           "fingerprint.json")
        try:
            unchanged = json.load(open(out)) == fp
        except (OSError, ValueError):
            unchanged = False
        if not unchanged:
            os.makedirs(os.path.dirname(out), exist_ok=True)
            json.dump(fp, open(out, "w"), indent=1)
        fp["_written"] = out
    return fp


def refresh(session_dir, set_name):
    """The automatic seeding entry (record-landing hooks + run gates): derive
    from whatever tracked records exist, quietly skipping a set that has no
    acquisition record yet (nothing derivable). Returns the fingerprint dict
    or None. Never raises on missing inputs — an undeclared mount simply
    yields an INDETERMINATE verdict for the UI to surface."""
    if not os.path.exists(acquisition.record_path(session_dir, set_name)):
        return None
    return derive(session_dir, set_name, write=True)


def _selftest():
    """Validate the derived geometry against independently recorded numbers:
    july14/set-01 (registration_qa.json: trail 3.40 px, drift 34 px/min, RA
    14.99 deg/hr, CONFIRM fixed via drift solves) and colonnello-m20
    (frame_metrics.json: 80 s @ 1150 mm / 0.682"/px at dec -22.89 predicts
    ~1625 px if fixed vs 0.896 median roundness -> decisive CONFIRM tracked
    with no solve)."""
    ok = True

    def check(name, got, want, tol):
        nonlocal ok
        p = abs(got - want) <= tol
        ok = ok and p
        print(f"  [{'PASS' if p else 'FAIL'}] {name}: {got:.3f} (want {want} +-{tol})")

    def flag(name, cond):
        nonlocal ok
        ok = ok and cond
        print(f"  [{'PASS' if cond else 'FAIL'}] {name}")

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
    v = mount_verdict("fixed", drift_sig=sig)
    flag(f"mount fixed -> {v['verdict']} (measured {sig}, drift solves)",
         v["verdict"] == "CONFIRM")
    vt = mount_verdict("tracked", drift_sig=sig)
    flag(f"mislabel tracked -> {vt['verdict']}", vt["verdict"] == "CONTRADICT")

    # trail-vs-roundness, decisive regime: colonnello-m20 (ASI mono @ 1150 mm,
    # 80 s, dec -22.89, 0.682"/px; frame_metrics medians)
    t = trail_px(80, -22.8896, 0.682)
    check("trail_px(80, -22.89, 0.682)", t, 1625.0, 5.0)
    m20 = {"roundness_median": 0.8962, "roundness_min": 0.8558,
           "fwhm_median_px": 3.515, "fwhm_max_px": 3.882,
           "nstars_median": 1531, "registered": 16, "frames_total": 16}
    tc = trail_roundness_check(t, m20)
    flag(f"roundness check decisive (margin {tc['margin']}x)",
         tc["decisive"] and tc["signature"] == "tracked" and tc["margin"] > 100)
    vc = mount_verdict("tracked", trail_check=tc)
    flag(f"declared tracked -> {vc['verdict']} ({vc['method']})",
         vc["verdict"] == "CONFIRM" and vc["method"] == "trail-vs-roundness")
    vf = mount_verdict("fixed", trail_check=tc)
    flag(f"mislabel fixed -> {vf['verdict']}", vf["verdict"] == "CONTRADICT")

    # boundary regime (july14 numbers): a 3.4 px predicted trail on a ~3.5 px
    # PSF must NOT be decisive — the drift solves decide there
    jb = {"roundness_median": 0.615, "roundness_min": 0.55,
          "fwhm_median_px": 3.6, "fwhm_max_px": 3.8,
          "nstars_median": 3000, "registered": 373, "frames_total": 373}
    tb = trail_roundness_check(3.40, jb)
    flag(f"boundary not decisive (margin {tb['margin']}x)",
         not tb["decisive"] and tb["signature"] is None)
    vb = mount_verdict("fixed", trail_check=tb)
    flag(f"boundary declared fixed -> {vb['verdict']} (declaration unchecked)",
         vb["verdict"] == "INDETERMINATE")
    # instruments in conflict -> INDETERMINATE, never a coin toss
    vx = mount_verdict("tracked", drift_sig="fixed", ra_rate=15.0, trail_check=tc)
    flag(f"conflicting instruments -> {vx['verdict']}",
         vx["verdict"] == "INDETERMINATE")

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
                write=not a.no_write)
    print(json.dumps(fp, indent=1))
    if fp.get("mount_check", {}).get("verdict") == "CONTRADICT":
        print(fp["mount_check"]["reason"], file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
