"""DIAGNOSTIC PROBE — does sirilpy's `analyse_image_from_file` agree with what
`run_frame_qa.sh` already records, and is it faster?

    pyscript probe_analyse.py <filelist.txt> <out.json>

MEASURES ONLY. Wires nothing, writes no intake table, gates nothing. This is a
diagnostic under CLAUDE.md's scope clarification ("to judge and examine an issue
... whatever is easiest is fine"); every number in it is Siril's own.

WHY THE COMPARISON NEEDS TWO ARMS AND NOT ONE. `records.jsonl` names a RAW
(`DSC_1265.NEF`) but its numbers were NOT measured on that raw:
`run_frame_qa.sh:108` runs `convert c -debayer` and then `register c -2pass`, so
the recorded fwhm/round/nstars are REGDATA ON DEBAYERED FRAMES. Comparing them
against `analyse_image_from_file(<NEF>)` would confound two differences at once —
a different ESTIMATOR and a different SAMPLING — and the registry already sizes the
sampling one at 9.1% FWHM (CFA 2.564 px / roundness 0.825 against debayered
2.350 / 0.850). So the raw arm alone could manufacture a mismatch that is not the
API's doing. The caller runs both arms over the SAME frames.

THE QUANTITY TRAP THIS PROBE EXISTS TO CATCH, and it is verified from the artifact
rather than assumed: `ImageAnalysis` carries `bgnoise` — `models.py:1429`, commented
"RMS background noise" — and carries NO background LEVEL field at all.
`records.jsonl` carries `bg`, a LEVEL (1065.1 ADU on the first aug09/set-05 record,
i.e. sky above the ~1007 pedestal). The cloud signature's Z +4.05 floor is built on
LEVEL. So `bgnoise` is NOT a drop-in for `bg`, and anything that treats it as one
swaps the quantity under the signature silently. This probe reports both names
separately and never maps one onto the other.
"""
import json
import sys
import time

import sirilpy


def main() -> int:
    if len(sys.argv) < 3:
        print("usage: probe_analyse.py <filelist.txt> <out.json>")
        return 2
    listfile, outfile = sys.argv[1], sys.argv[2]

    with open(listfile) as fh:
        paths = [ln.strip() for ln in fh if ln.strip()]

    siril = sirilpy.SirilInterface()
    siril.connect()

    rows, failures = [], []
    # A per-call clock, not a total divided by n: the first call in a session can
    # carry one-off setup and an average would hide it. The caller reads both.
    for p in paths:
        t0 = time.perf_counter()
        try:
            a = siril.analyse_image_from_file(p)
        except Exception as exc:                      # noqa: BLE001 - report, never mask
            failures.append({"file": p, "error": f"{type(exc).__name__}: {exc}"})
            continue
        rows.append({
            "file": p,
            "seconds": round(time.perf_counter() - t0, 4),
            # NAMED AS THE API NAMES THEM. No renaming to the record's vocabulary —
            # that is exactly how a quantity swap becomes invisible.
            "bgnoise": a.bgnoise,
            "fwhm": a.fwhm,
            "wfwhm": a.wfwhm,
            "nbstars": a.nbstars,
            "roundness": a.roundness,
            "width": a.width,
            "height": a.height,
            "channels": a.channels,
        })

    out = {
        "_what": "sirilpy analyse_image_from_file, raw output. MEASURES ONLY.",
        "_quantity_note": ("bgnoise is RMS background NOISE (models.py:1429). It is "
                           "NOT records.jsonl's `bg`, which is a LEVEL. Not interchangeable."),
        "n_ok": len(rows),
        "n_failed": len(failures),
        "rows": rows,
        "failures": failures,
    }
    with open(outfile, "w") as fh:
        json.dump(out, fh, indent=2)
    print(f"probe_analyse: {len(rows)} ok, {len(failures)} failed -> {outfile}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
