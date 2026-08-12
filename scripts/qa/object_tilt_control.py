#!/usr/bin/env python3
"""POSITIVE + IDENTITY controls for scripts/qa/object_tilt.py.

  object_tilt_control.py <groups-dir> [--ramp=0.20,0.0] [--floor=F]
                         [--json=OUT] [--keep]

An instrument that cannot recover a PLANTED tilt cannot be trusted to report a
real one, and this repo's most persistent defect is a check that cannot fail.
So the tilt instrument is run twice more on the SAME real sub-stacks, with a
known multiplicative field put in by the tool:

  RAMP  a linear card `R(x) = 1 + k*(x/W - 0.5)`, applied with Siril `imul`.
        It is sensor-fixed and identical for every block, which is exactly the
        shape of the defect under test, so the instrument MUST report the
        un-ramped tilt shifted by the card's own edge-to-edge ratio
        `(1 + k/2)/(1 - k/2)`. Recovery is reported as a fraction of planted.
  UNIFORM  the same machinery with k = 0. A card of exactly 1.0 must leave the
        answer BIT-unchanged; anything else means the card path itself moves
        the measurement, and the ramp arm would be measuring the path.

The card is a synthetic FIXTURE, never a deliverable and never a calibration
frame: it is generated, multiplied in by Siril, measured, and deleted. Siril
does the pixel operation and every measurement, as in the flat-side work's
discrimination pattern.

DISCRIMINATION is reported two ways, because they answer different questions.
Against the INERT arm it asks "does the instrument respond only to a real
sensor-fixed field" — the uniform card must move nothing. Against the measured
FLOOR (`--floor=`, from `object_tilt_null.sh`) it asks the question that decides
whether the instrument is usable at all: is the planted signal bigger than what
the instrument reports when the truth is zero? That is the form the iterative-flat
NULL reported (48-62x there), and it is the number to quote.

`imul` + `save` PRESERVE the astrometric solution — measured on this rig: Siril
rewrites CD into CDELT+PC and keeps every SIP term, and the two headers agree
to 2.8e-13 deg over the frame. That matters because the instrument's whole
cross-match runs through each product's own WCS.

REMOVAL CONDITION: retires with scripts/qa/object_tilt.py.
"""
import glob
import json
import os
import shutil
import subprocess
import sys

import numpy as np
from astropy.io import fits

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "lib"))
import object_tilt
import siril_run


def build_card(path, w, h, k):
    x = np.arange(w, dtype=np.float32)
    ramp = (1.0 + k * (x / float(w) - 0.5)).astype(np.float32)
    fits.PrimaryHDU(np.broadcast_to(ramp, (3, h, w)).astype(np.float32)).writeto(
        path, overwrite=True)
    return float(ramp[-1] / ramp[0])


def main(argv):
    if not argv or argv[0].startswith("--"):
        print(__doc__)
        return 2
    gdir = os.path.abspath(argv[0])
    ks = [0.20, 0.0]
    outp = None
    keep = False
    floor = None
    for a in argv[1:]:
        if a.startswith("--ramp="):
            ks = [float(x) for x in a.split("=", 1)[1].split(",")]
        elif a.startswith("--floor="):
            floor = float(a.split("=", 1)[1])
        elif a.startswith("--json="):
            outp = a.split("=", 1)[1]
        elif a == "--keep":
            keep = True
        else:
            print(f"unknown arg {a}", file=sys.stderr)
            return 2

    subs = sorted(glob.glob(os.path.join(gdir, "sub_*.fit")))
    session = os.path.dirname(os.path.dirname(gdir))
    ctl = os.path.join(session, "work", "tiltctl_" + os.path.basename(gdir))
    args = {"apertures": [10], "inner": 20, "outer": 30, "amin": 0.005,
            "tol_arcsec": 34.0, "margin": 40, "layer": 1, "roundness": 0.05,
            "keep": False}

    base = object_tilt.run_set(gdir, args)
    b10 = base["apertures"]["10"]
    res = {
        "uptime": object_tilt.uptime(),
        "groups_dir": gdir,
        "instrument": "scripts/qa/object_tilt.py under a Siril-applied card",
        "baseline": {"tilt_frac_x": b10["tilt_frac_x"],
                     "tilt_frac_x_err": b10["tilt_frac_x_err"],
                     "n_stars": b10["n_stars"],
                     "lever_px_x": b10["lever_px_x"],
                     "block_pair_spread_frac": b10.get("block_pair_spread_frac")},
        "arms": [],
    }

    for k in ks:
        os.makedirs(ctl, exist_ok=True)
        lines, planted = [], None
        for j, s in enumerate(subs):
            h = fits.getheader(s)
            card = os.path.join(ctl, f"card_{j:02d}.fit")
            planted = build_card(card, h["NAXIS1"], h["NAXIS2"], k)
            lines += [f"load {s}", f"imul {card}",
                      f"save {os.path.join(ctl, f'sub_{j:02d}')}"]
        # `setcompress 0` is re-pinned here even though run_ssf already emits it:
        # siril PERSISTS the setting between runs, and check_bitdepth.sh reads
        # each emitter TEXTUALLY, so an emitter that pins it only through a
        # helper is indistinguishable from one that forgot.
        rc = object_tilt.run_ssf(ctl, ["set32bits", "setcompress 0"] + lines,
                                 os.path.join(ctl, "apply.ssf"),
                                 os.path.join(ctl, "apply.log"))
        if rc != 0:
            raise SystemExit(f"card application failed (rc={rc}) — {ctl}/apply.log")
        for c in glob.glob(os.path.join(ctl, "card_*.fit")):
            os.remove(c)

        arm = object_tilt.run_set(ctl, args, work=os.path.join(ctl, "tilt_work"))
        a10 = arm["apertures"]["10"]
        # a multiplicative card multiplies the throughput ratio
        expect = (1.0 + b10["tilt_frac_x"]) * planted - 1.0
        moved = a10["tilt_frac_x"] - b10["tilt_frac_x"]
        should_move = expect - b10["tilt_frac_x"]
        res["arms"].append({
            "k": k,
            "planted_edge_ratio": planted,
            "planted_tilt_frac": planted - 1.0,
            "measured_tilt_frac_x": a10["tilt_frac_x"],
            "measured_tilt_frac_x_err": a10["tilt_frac_x_err"],
            "expected_tilt_frac_x": expect,
            "moved_by": moved,
            "should_have_moved_by": should_move,
            "recovery_fraction": (moved / should_move) if should_move else None,
            "n_stars": a10["n_stars"],
            "lever_px_x": a10["lever_px_x"],
            "block_pair_spread_frac": a10.get("block_pair_spread_frac"),
            "block_pairs": [{"blocks": p["blocks"], "tilt_frac_x": p["tilt_frac_x"]}
                            for p in a10.get("block_pairs", [])],
        })
        print(f"  k={k:+.2f}  card R/L={planted:.6f}  measured tilt "
              f"{100*a10['tilt_frac_x']:+.2f}% (expected {100*expect:+.2f}%)  "
              f"moved {100*moved:+.2f}% of {100*should_move:+.2f}%  "
              f"recovery={res['arms'][-1]['recovery_fraction']}")
        if not keep:
            shutil.rmtree(ctl, ignore_errors=True)

    live = [a for a in res["arms"] if a["k"] != 0.0]
    inert = [a for a in res["arms"] if a["k"] == 0.0]
    if live:
        res["discrimination"] = {
            "planted_response_points": 100 * live[0]["moved_by"],
            "inert_response_points": (100 * inert[0]["moved_by"]) if inert else None,
            "vs_inert": ("the uniform card moves the answer by exactly 0.00 points, "
                         "so the response is to the planted field and not to the "
                         "card path" if inert and inert[0]["moved_by"] == 0.0
                         else "inert arm NOT run — discrimination unproven"),
            "floor_points": (100 * floor) if floor is not None else None,
            "signal_over_floor": ((live[0]["moved_by"] / floor) if floor else None),
            "note": ("signal_over_floor is the number that decides usability: "
                     "below 1 the planted signal is smaller than what the "
                     "instrument reports when the truth is zero."),
        }
        if floor:
            print(f"  discrimination: planted {100*live[0]['moved_by']:+.2f} points "
                  f"vs floor {100*floor:.2f} points = "
                  f"{live[0]['moved_by']/floor:.2f}x  (inert arm moved "
                  f"{100*inert[0]['moved_by'] if inert else float('nan'):+.2f})")
    txt = json.dumps(res, indent=1)
    if outp:
        os.makedirs(os.path.dirname(os.path.abspath(outp)), exist_ok=True)
        open(outp, "w").write(txt + "\n")
        print(f"wrote {outp}")
    else:
        print(txt)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
