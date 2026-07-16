#!/usr/bin/env python3
"""Record Siril's own spatial star-shape analysis (`seqtilt`) for an image.

Usage: star_shape.py <image.fit> [--json=<out.json>] [--label=<name>]

Why this exists: a registration model that cannot express the true frame-to-frame
mapping leaves a residual that GROWS WITH FIELD RADIUS — sharp at the centre,
smeared at the edges. A whole-frame median hides exactly that: it averages the
good centre into the bad edge and reports one mediocre number.

Siril measures this itself. `seqtilt` fits the PSF across the frame and reports:

  Stars                     how many it fitted
  Truncated mean[FWHM]      whole-frame FWHM, outlier-truncated
  Sensor tilt[FWHM]         best corner vs worst corner — the ASYMMETRIC term
  Off-axis aberration[FWHM] centre vs corners — the RADIAL term

"Off-axis aberration" is the radial degradation; "sensor tilt" is the one-sided
component. Both come from Siril. This script arranges the input, runs the tool,
parses its report and records it — it computes nothing, and reads no pixel.

Read the numbers as Siril defines them: they are FWHM DIFFERENCES in pixels
(bigger = worse), not the min/max roundness ratio, and not Siril's per-star
`findstar` "roundness" (FWHMy/FWHMx). Do not mix the three.

Do NOT re-derive these by binning a `findstar` star list by radius. That was
tried and it is circular: the binning origin gets inferred from the detections,
the defect suppresses detections at the edge, so the origin MOVES with the defect
and the profile flattens as the defect worsens (docs/dead-ends.md). `seqtilt`
has no origin to get wrong.

ADAPTATION — the two-frame sequence, with its removal condition: `seqtilt` takes a
SEQUENCE and Siril cannot build one from a single frame (`convert`/`link` write
the .fit but no .seq), while single-image `tilt` and `inspector` are both "Can be
used in a script: NO". So a lone stack is presented as a two-frame sequence of
itself; every measurement is still Siril's, on the real pixels, unchanged. Retire
the duplication the day Siril exposes a headless single-image tilt (or builds a
sequence from one frame). Pass a real sequence and it is used as-is.
"""
import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile

SIRIL = ["flatpak", "run", "--command=siril-cli", "org.siril.Siril"]

# "Stars: 5095, Truncated mean[FWHM]: 3.20, Sensor tilt[FWHM]: 0.50 (16%),
#  Off-axis aberration[FWHM]: 0.57"
REPORT = re.compile(
    r"Stars:\s*(\d+),\s*Truncated mean\[FWHM\]:\s*([0-9.]+),\s*"
    r"Sensor tilt\[FWHM\]:\s*([0-9.]+)\s*\((\d+)%\),\s*"
    r"Off-axis aberration\[FWHM\]:\s*([0-9.]+)")


def run_seqtilt(image, work):
    """Drive Siril `seqtilt` on one image and return its reported measures.

    Siril does every pixel operation and every measurement. This writes only
    into `work`; the input is never modified. The .ssf and the frames live
    under $HOME — the flatpak sandbox has a private /tmp.
    """
    seq_in = os.path.join(work, "in")
    seq_out = os.path.join(work, "seq")
    os.makedirs(seq_in, exist_ok=True)
    # Two frames because Siril cannot build a sequence from one (see the
    # ADAPTATION note above). Identical frames -> the measures are the image's.
    for i in (1, 2):
        shutil.copy2(image, os.path.join(seq_in, f"f_{i:05d}.fit"))
    ssf = os.path.join(work, "_tilt.ssf")
    with open(ssf, "w") as f:
        f.write("requires 1.4.4\n"          # seqtilt's report format is tested here
                f"cd {seq_in}\n"
                f"link f -out={seq_out}\n"
                f"cd {seq_out}\n"
                "seqtilt f\n")
    r = subprocess.run(SIRIL + ["-d", work, "-s", ssf],
                       capture_output=True, text=True)
    m = REPORT.search(r.stdout)
    if not m:
        raise RuntimeError(
            f"seqtilt reported nothing parseable for {image} — its report "
            f"format may have drifted, or too few stars were fitted:\n"
            + r.stdout[-800:] + r.stderr[-800:])
    return {"stars": int(m.group(1)),
            "truncated_mean_fwhm_px": float(m.group(2)),
            "sensor_tilt_fwhm_px": float(m.group(3)),
            "sensor_tilt_pct": int(m.group(4)),
            "off_axis_aberration_fwhm_px": float(m.group(5))}


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("image")
    ap.add_argument("--json")
    ap.add_argument("--label")
    a = ap.parse_args()
    if not os.path.exists(a.image):
        sys.exit(f"star_shape: no such image: {a.image}")

    # Under $HOME beside the image (the flatpak sandbox cannot see /tmp).
    work = tempfile.mkdtemp(prefix=".star_shape_",
                            dir=os.path.dirname(os.path.abspath(a.image)))
    try:
        meas = run_seqtilt(os.path.abspath(a.image), work)
    finally:
        shutil.rmtree(work, ignore_errors=True)

    rec = {"input": a.image, "label": a.label,
           "measured_by": "Siril seqtilt (this script only runs it and records "
                          "its report)",
           **meas}
    lab = f" [{a.label}]" if a.label else ""
    print(f"{os.path.basename(a.image)}{lab}")
    print(f"  stars fitted            {meas['stars']}")
    print(f"  truncated mean FWHM     {meas['truncated_mean_fwhm_px']:.2f} px")
    print(f"  sensor tilt (asymmetric){meas['sensor_tilt_fwhm_px']:6.2f} px "
          f"({meas['sensor_tilt_pct']}%)")
    print(f"  off-axis aberration     {meas['off_axis_aberration_fwhm_px']:.2f} px"
          "   <- the radial term: centre vs corners")
    if a.json:
        with open(a.json, "w") as f:
            json.dump(rec, f, indent=1)
        print(f"wrote {a.json}")


if __name__ == "__main__":
    main()
