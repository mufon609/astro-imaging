#!/usr/bin/env python3
"""Measure a sky flat's ODD component, and optionally the RATIO of two flats.

WHY THIS EXISTS. `docs/dead-ends.md` says of the `sky x V` defect: "judge it on
the FLAT's odd component, not the stack's corners" — and
`BACKLOG:calibration-evidence` records that that instrument "has no script", so
the measurement justifying a shipped default could not be re-run. This is that
script. Orchestration + record only: Siril does every pixel operation (load /
crop / fdiv) and every measurement (stat); nothing here reads a pixel.

WHAT IT MEASURES, and why each number answers a different question.
Vignetting is an EVEN RADIAL function, so it contributes EQUALLY to the
left-right and top-bottom dipoles and puts all four corners at one radius.
Therefore:
  - `corner_ratio` (brightest/darkest corner) reads 1.000 for vignetting alone;
    any excess is NON-RADIAL.
  - `LR` and `TB` split that excess BY AXIS. A term on one axis only cannot be
    vignetting by construction, and on this corpus the sky term is the L-R one
    while T-B is stable (see --ratio below).
  - `edge_dipole_x` / `_y` are the same question through baseline_guard.py's
    null (box 80 / margin 2), kept so the numbers stay comparable with the
    flat records `build_sky_flat.sh` already writes.

--ratio B is the sharpest form and needs no model at all. A ratio of two flats
built by the SAME builder from the SAME night, lens, focal and aperture cancels
vignetting and the instrumental base EXACTLY, leaving only what DIFFERS between
them. Measured on aug09's five flats, T/B cancels to 1.000 (0.984-1.008) while
L/R carries the whole dose — which is how the night's growing term was
identified as sky rather than optics.
  SCOPE: a ratio cancels what is COMMON, so it measures the CHANGE in sky, not
  the total. A sky term already present in the reference flat and not varying
  cancels into the "stable" part alongside the instrumental term. The ratio is
  a LOWER BOUND on sky contamination.

`idiv` is NEVER used: it clips at 1.0 silently (dead-end registry). MEASURED on
the aug09 set-05 / set-01 pair this script was validated against — a ratio whose
median is ~1.07, i.e. it STRADDLES 1.0, which is the case the registry says is
catastrophic rather than survivable: `idiv` returns a whole-frame **median of
exactly 65535.0** (mean 64718.8), and the TL corner reads 65534.9 where the true
ratio is **1.2085**. Over half the frame is pinned at the clip and the corner
structure is gone. `fdiv <B> <scalar>` with the scalar RECORDED is the contract.

--control re-runs the same ratio at HALF the scalar; every regional median must
then rescale by exactly 2. Measured on that pair: 2.0000 in all five regions.
WHAT THE CONTROL PROVES AND WHAT IT DOES NOT: it proves no truncation is moving
these medians, and it fires if `idiv` is ever substituted or a 16-bit mode is
active. It is NOT expected to fail under `fdiv` in 32-bit, where nothing clips
(values above 65535 survive) — so treat a pass as a regression guard, not as
evidence that the pair was near a clip. A whole-frame Max of 65535.0 at BOTH
scalars is a genuine divide-by-near-zero spike, not bulk clipping.

  flat_odd_component.py <flat.fit> <out.json> [--ratio=<other.fit>]
                        [--scalar=0.5] [--control] [--label=<name>]

REMOVAL CONDITION: a real flat exists for the set (which retires the sky-flat
builder itself), or the `sky x V` defect is measured absent on this rig — at
which point the odd component is no longer a thing to watch.
"""
import json
import os
import re
import subprocess
import sys

from astropy.io import fits

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "lib"))
import siril_run

GEOM = {"corner": (400, 200), "edge": (80, 2)}
# Siril prints `Sigma: -nan` for a region of ZERO variance — a perfectly uniform
# crop. The previous class `[0-9.eEn+-]*[0-9n]` carried an `n` (so it was MEANT
# to admit nan) but no `a`, so it matched neither `nan` nor `-nan`: the block
# simply did not parse, the caller's count assertion fired, and the run aborted.
# MEASURED cost: the UNIFORM-CARD control — the one arm whose entire purpose is a
# field with no gradient, i.e. the case that produces uniform crops — could not be
# measured at all. 2 of 9 midline boxes read `-nan` and the differential exited
# "parsed 7 stat blocks, expected 9". The failure is LOUD, never a wrong number,
# because every caller asserts the count.
# Sigma is captured and DISCARDED — every caller reads the MEDIAN (group 2) only —
# so widening this group cannot move any number this instrument has ever
# reported; it only lets a uniform region be measured instead of aborting.
STAT = re.compile(r"Mean: ([0-9.eE+-]+), Median: ([0-9.eE+-]+), "
                  r"Sigma: (-?nan|-?inf|[0-9.eE+-]+), Min: ([0-9.eE+-]+), "
                  r"Max: ([0-9.eE+-]+)")


def _run(wdir, lines, tag, expect=None):
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


def _regions(w, h, box, margin):
    return {"center": ((w - box) // 2, (h - box) // 2),
            "TL": (margin, margin), "TR": (w - margin - box, margin),
            "BL": (margin, h - margin - box),
            "BR": (w - margin - box, h - margin - box)}


def measure(img, wdir, tag):
    """Siril `stat` medians on centre + 4 corners at both geometries."""
    hdr = fits.getheader(img)
    w, h = int(hdr["NAXIS1"]), int(hdr["NAXIS2"])
    lines, order = [], []
    for g, (box, margin) in GEOM.items():
        for rname, (x, y) in _regions(w, h, box, margin).items():
            lines += [f"load {img}", f"crop {x} {y} {box} {box}", "stat"]
            order.append((g, rname))
    stats = _run(wdir, lines, tag, expect=len(order))
    out = {"image_wh": [w, h]}
    for g, (box, margin) in GEOM.items():
        med = {r: float(s[1]) for (gg, r), s in zip(order, stats) if gg == g}
        q = {k: med[k] for k in ("TL", "TR", "BL", "BR")}
        m4 = sum(q.values()) / 4.0
        out[g] = {
            "geometry_px": {"box": box, "corner_margin": margin},
            "median_ADU": med,
            "corner_ratio": round(max(q.values()) / min(q.values()), 4),
            "brightest": max(q, key=q.get), "darkest": min(q, key=q.get),
            "LR": round((q["TL"] + q["BL"]) / (q["TR"] + q["BR"]), 4),
            "TB": round((q["TL"] + q["TR"]) / (q["BL"] + q["BR"]), 4),
            "corner_over_center": round(m4 / med["center"], 4),
            "edge_dipole_x": round(((q["TR"] + q["BR"])
                                    - (q["TL"] + q["BL"])) / 2 / m4, 4),
            "edge_dipole_y": round(((q["TL"] + q["TR"])
                                    - (q["BL"] + q["BR"])) / 2 / m4, 4)}
    return out


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    opts = dict(a[2:].split("=", 1) for a in sys.argv[1:]
                if a.startswith("--") and "=" in a)
    flags = {a[2:] for a in sys.argv[1:] if a.startswith("--") and "=" not in a}
    if len(args) != 2:
        sys.exit(__doc__)
    flat, out_json = os.path.abspath(args[0]), os.path.abspath(args[1])
    other = os.path.abspath(opts["ratio"]) if opts.get("ratio") else None
    scalar = float(opts.get("scalar", 0.5))
    wdir = os.path.dirname(out_json)
    os.makedirs(wdir, exist_ok=True)

    rec = {
        "tool": "Siril 1.4.4 — load/crop/stat regional medians (and fdiv for "
                "--ratio); every pixel op and every measurement is Siril's",
        "flat": flat,
        "uptime": subprocess.run(["uptime"], capture_output=True,
                                 text=True).stdout.strip(),
        "how_to_read":
            "Vignetting is EVEN and RADIAL, so it contributes equally to LR and "
            "TB and puts all four corners at one radius (corner_ratio 1.000). "
            "An excess on ONE axis is non-radial BY CONSTRUCTION and cannot be "
            "vignetting; on this corpus the L-R term is the horizon-fixed sky "
            "gradient the flat absorbs, which then divides a multiplicative "
            "tilt into the object (docs/dead-ends.md). REPORTED, never gated: "
            "the defect is open with no shipped corrective, so a pass/fail line "
            "here is a user ratification, not this script's to invent.",
        "self": measure(flat, wdir, "self"),
    }

    if other:
        rec["ratio"] = {
            "denominator": other, "scalar": scalar,
            "why": "A ratio of two flats from the same night/lens/focal/aperture "
                   "cancels vignetting and the instrumental base EXACTLY — no "
                   "model, no fit. What survives is what DIFFERS.",
            "scope": "Cancels what is COMMON, so it measures the CHANGE in sky, "
                     "not the total: a static sky term cancels into the stable "
                     "part. LOWER BOUND on sky contamination.",
            "never_idiv": "idiv clips at 1.0 silently and understates a "
                          "between-flat corner spread by up to 9.1 points "
                          "(docs/dead-ends.md). fdiv only, scalar recorded."}
        tmp = os.path.join(wdir, "_ratio")
        _run(wdir, [f"load {flat}", f"fdiv {other} {scalar}", f"save {tmp}"],
             "mkratio")
        rec["ratio"]["measured"] = measure(f"{tmp}.fit", wdir, "ratio")
        if "control" in flags:
            _run(wdir, [f"load {flat}", f"fdiv {other} {scalar/2}",
                        f"save {tmp}"], "mkratio_c")
            ctl = measure(f"{tmp}.fit", wdir, "ratio_c")
            a, b = rec["ratio"]["measured"]["corner"], ctl["corner"]
            same = all(abs(a[k] - b[k]) < 5e-4 for k in ("LR", "TB",
                                                         "corner_ratio"))
            rec["ratio"]["no_clip_control"] = {
                "scalar": scalar / 2, "measured": ctl, "agrees": same,
                "reading": "Two scalars agreeing after rescale is the positive "
                           "control that no truncation is moving the medians. A "
                           "whole-frame Max of 65535.0 at BOTH scalars is a "
                           "genuine divide-by-near-zero spike, not bulk clipping."}
            if not same:
                print("WARNING: the two scalars DISAGREE — the ratio is being "
                      "truncated; do not trust these medians.", file=sys.stderr)
        os.remove(f"{tmp}.fit")

    if opts.get("label"):
        rec["label"] = opts["label"]
    with open(out_json, "w") as f:
        json.dump(rec, f, indent=1)

    for scope in ("self", "ratio"):
        blk = rec.get(scope)
        if not blk:
            continue
        m = blk["measured"]["corner"] if scope == "ratio" else blk["corner"]
        e = blk["measured"]["edge"] if scope == "ratio" else blk["edge"]
        print(f"{scope:<6} corner_ratio {m['corner_ratio']:.3f} "
              f"({m['brightest']} brightest, {m['darkest']} darkest)  "
              f"LR {m['LR']:.4f}  TB {m['TB']:.4f}  "
              f"corner/centre {m['corner_over_center']:.4f}")
        print(f"       edge dipole x {e['edge_dipole_x']:+.4f}  "
              f"y {e['edge_dipole_y']:+.4f}"
              + ("   |x| exceeds |y| -> NON-RADIAL, i.e. sky"
                 if abs(e["edge_dipole_x"]) > abs(e["edge_dipole_y"]) else ""))
    print(f"record: {out_json}")


if __name__ == "__main__":
    main()
