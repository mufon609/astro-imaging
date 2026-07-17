#!/usr/bin/env python3
"""Record Siril `findstar` PSF fits at fixed stations along/across the drift axis.

Usage: star_stations.py <image.fit> --angle-deg <drift_axis_deg>
                        [--json=<out.json>] [--label=<name>]
                        [--radius=350] [--offsets=700,1300]

Why this exists: for the wide-field UNTRACKED class, `seqtilt`'s off-axis
aberration (centre vs corners) is BLIND to a drift-aligned defect band — a
centre band degrading toward the corners' level makes that number BETTER, so
it can improve while the best region of the frame gets worse. The band is the
measured signature of a paraxial distortion-model error: true distortion -> 0
at the optical axis, the radial unit vector flips sign as a star's sky
position crosses it during the drift, and a +-eps model error becomes a ~2*eps
along-drift smear precisely in the corridor the axis swept. Stations along
the drift axis see it; stations perpendicular to it sit at the in-exposure
floor. Whole-frame and centre-vs-corner measures average the two together.

What it does: Siril loads the image, `crop`s each station box, and `findstar`
fits every star (open gate, so elongated stars are DETECTED rather than
silently rejected). This script only writes the .ssf, reads the tool's star
lists back, and records medians of the tool's own per-star numbers — the same
summarisation the per-frame registration record uses. It performs no pixel
operation and no fit of its own.

The station geometry is FIXED AND EXTERNAL: the geometric image centre plus
offsets along/perpendicular to a drift axis that comes from the astrometric
solves — never from the detections being measured. (A binning origin inferred
from the data moves WITH the defect and flattens the profile as the defect
worsens: docs/dead-ends.md, trap 3. Fixed equal-area stations also make the
per-station counts directly comparable — read a shape median WITH its n.)
A near-horizontal axis makes the geometry robust to a solver-vs-Siril
vertical-flip convention mismatch (it tilts the axis by twice the
axis-to-horizontal angle; immaterial at these station radii).

A station that would fall outside the image is an ERROR, not a smaller box —
a silently shrunk station would break the equal-area count comparison.

Removal condition: retire this the day an official tool reports a headless
LOCAL star-shape map (region- or grid-resolved FWHM/roundness), e.g. a
scriptable equivalent of PixInsight's FWHMEccentricity contour analysis;
`seqtilt` stays the whole-frame radial/asymmetric measure either way.
"""
import argparse
import json
import math
import os
import re
import shutil
import statistics
import subprocess
import sys
import tempfile

SIRIL = ["flatpak", "run", "--command=siril-cli", "org.siril.Siril"]

DIMS = re.compile(r"Reading FITS: file .*?, \d+ layer\(s\), (\d+)x(\d+) pixels")


def run_siril(work, ssf):
    r = subprocess.run(SIRIL + ["-d", work, "-s", ssf],
                       capture_output=True, text=True)
    return r.stdout + r.stderr


def image_dims(image, work):
    """Ask Siril for the image dimensions (its load log reports them)."""
    ssf = os.path.join(work, "_dims.ssf")
    with open(ssf, "w") as f:
        f.write(f"requires 1.4.4\nload {image}\n")
    out = run_siril(work, ssf)
    m = DIMS.search(out)
    if not m:
        raise RuntimeError(f"could not read image dimensions from Siril's log "
                           f"for {image}:\n{out[-600:]}")
    return int(m.group(1)), int(m.group(2))


def stations_for(width, height, angle_deg, radius, offsets):
    """Fixed equal-area boxes: centre + along/perp offsets about the centre."""
    u = (math.cos(math.radians(angle_deg)), math.sin(math.radians(angle_deg)))
    v = (-u[1], u[0])
    cx, cy = width / 2.0, height / 2.0
    named = [("centre", 0.0, 0.0)]
    for d in offsets:
        named += [(f"along+{d}", d * u[0], d * u[1]),
                  (f"along-{d}", -d * u[0], -d * u[1]),
                  (f"perp+{d}", d * v[0], d * v[1]),
                  (f"perp-{d}", -d * v[0], -d * v[1])]
    out = []
    for name, dx, dy in named:
        x = int(round(cx + dx - radius))
        y = int(round(cy + dy - radius))
        w = h = 2 * radius
        if x < 0 or y < 0 or x + w > width or y + h > height:
            raise SystemExit(
                f"star_stations: station {name!r} box ({x},{y},{w},{h}) falls "
                f"outside the {width}x{height} image — shrink --offsets/--radius "
                f"(a silently clipped station breaks the equal-area count)")
        out.append({"name": name, "dx_px": round(dx, 1), "dy_px": round(dy, 1),
                    "box": [x, y, w, h]})
    return out


def read_lst(path):
    """Siril findstar list: X Y FWHMx FWHMy angle at columns 5/6/7/8/11."""
    rows = []
    with open(path) as f:
        for line in f:
            if line.startswith("#"):
                continue
            p = line.split()
            if len(p) < 13:
                continue
            rows.append((float(p[7]), float(p[8]), float(p[11])))
    return rows


def measure(image, work, sts):
    ssf = os.path.join(work, "_stations.ssf")
    with open(ssf, "w") as f:
        f.write("requires 1.4.4\n"
                "setfindstar reset -roundness=0.05 -sigma=0.5 -relax=on\n")
        for s in sts:
            x, y, w, h = s["box"]
            lst = os.path.join(work, f"{s['name']}.lst")
            f.write(f"load {image}\ncrop {x} {y} {w} {h}\n"
                    f"findstar -out={lst}\n")
        f.write("setfindstar reset\n")
    out = run_siril(work, ssf)
    for s in sts:
        lst = os.path.join(work, f"{s['name']}.lst")
        if not os.path.exists(lst):
            raise RuntimeError(f"findstar wrote no list for station "
                               f"{s['name']!r}:\n{out[-600:]}")
        rows = read_lst(lst)
        s["n"] = len(rows)
        if rows:
            s["maj_fwhm_px"] = round(statistics.median(r[0] for r in rows), 2)
            s["roundness"] = round(statistics.median(r[1] / r[0] for r in rows), 3)
            s["angle_deg_median"] = round(statistics.median(r[2] for r in rows), 1)
    return sts


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("image")
    ap.add_argument("--angle-deg", type=float, required=True,
                    help="drift axis in image coordinates (from the "
                         "astrometric solves — an external fact, never fitted "
                         "from the detections)")
    ap.add_argument("--json")
    ap.add_argument("--label")
    ap.add_argument("--radius", type=int, default=350)
    ap.add_argument("--offsets", default="700,1300")
    a = ap.parse_args()
    if not os.path.exists(a.image):
        sys.exit(f"star_stations: no such image: {a.image}")
    offsets = [int(x) for x in a.offsets.split(",") if x]

    image = os.path.abspath(a.image)
    # Under $HOME beside the image (the flatpak sandbox cannot see /tmp).
    work = tempfile.mkdtemp(prefix=".star_stations_",
                            dir=os.path.dirname(image))
    try:
        wpx, hpx = image_dims(image, work)
        sts = measure(image, work, stations_for(wpx, hpx, a.angle_deg,
                                                a.radius, offsets))
    finally:
        shutil.rmtree(work, ignore_errors=True)

    rec = {"input": a.image, "label": a.label,
           "measured_by": "Siril findstar PSF fits per station (open gate "
                          "-roundness=0.05 -sigma=0.5 -relax=on); Siril crop "
                          "does the cropping; this script records medians of "
                          "the tool's numbers",
           "drift_axis_deg_image": a.angle_deg,
           "image_wh": [wpx, hpx], "station_radius_px": a.radius,
           "reading_guide": "equal-area stations: n comparable across stations "
                            "and arms; the band signature = centre/along "
                            "stations worse than perp stations (majFWHM up, "
                            "roundness and n down)",
           "stations": sts}
    lab = f" [{a.label}]" if a.label else ""
    print(f"{os.path.basename(a.image)}{lab}  {wpx}x{hpx}  "
          f"axis {a.angle_deg:.1f} deg  r={a.radius}")
    for s in sts:
        if s["n"]:
            print(f"  {s['name']:<12} n={s['n']:4d}  majFWHM={s['maj_fwhm_px']:.2f}"
                  f"  roundness={s['roundness']:.3f}  angle={s['angle_deg_median']:+.1f}")
        else:
            print(f"  {s['name']:<12} n=   0")
    if a.json:
        with open(a.json, "w") as f:
            json.dump(rec, f, indent=1)
        print(f"wrote {a.json}")


if __name__ == "__main__":
    main()
