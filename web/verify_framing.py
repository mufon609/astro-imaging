#!/usr/bin/env python3
"""Verify a user-drawn framing record with Siril's own crop+stat — the
coordinate-export guard (docs/dead-ends.md: an unverified numpy/screen-order
box once shipped a vertically mirrored, zero-coverage wedge; Siril's crop
y-origin is the OPPOSITE end from screen row order).

    python3 web/verify_framing.py <session> <product> \
        { --map=<coverage_map.fit> --map-min=<members> | --min-floor=<ADU> }

Two verification modes, both tool-measured (Siril `crop` + `stat`; this
script parses and records, it computes nothing from pixels):

  --map / --map-min    crop the per-pixel COVERAGE MAP (coverage_probe.sh
                       output: value = members*1000) with the record's
                       rect_siril_crop_args and require stat Min >=
                       map-min*1000 — every pixel of the frame is covered by
                       at least <map-min> members.
  --min-floor          no map available: crop the product STACK itself and
                       require stat Min >= <ADU> — the SIBLING-CLASS SKY
                       FLOOR rule (dead-ends: mere non-zero PASSES on
                       lanczos edge-ringing residue; the floor must be the
                       sibling stacks' sky level, e.g. ~80 ADU on july14).

PASS stamps the record status "verified" with the measured stats + method;
FAIL leaves it "unverified" and records the failure. The render chain must
refuse an unverified framing.
"""
import json
import os
import re
import subprocess
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SIRIL = ["flatpak", "run", "--command=siril-cli", "org.siril.Siril"]


def run_crop_stat(image, crop_args, workdir):
    os.makedirs(workdir, exist_ok=True)
    ssf = os.path.join(workdir, "verify_framing.gen.ssf")
    x, y, w, h = crop_args
    with open(ssf, "w") as f:
        f.write("requires 1.4.0\nsetcompress 0\n"
                f"load {image}\ncrop {x} {y} {w} {h}\nstat\n")
    r = subprocess.run(SIRIL + ["-d", workdir, "-s", ssf],
                       capture_output=True, text=True)
    log = r.stdout + r.stderr
    stats = []
    for m in re.finditer(r"(Red|Green|Blue|B&W) layer: Mean: ([0-9.]+), "
                         r"Median: ([0-9.]+), Sigma: ([0-9.]+), "
                         r"Min: ([0-9.]+), Max: ([0-9.]+)", log):
        stats.append({"layer": m.group(1), "mean": float(m.group(2)),
                      "median": float(m.group(3)), "min": float(m.group(5)),
                      "max": float(m.group(6))})
    if r.returncode != 0 or not stats:
        tail = "\n".join(log.splitlines()[-8:])
        sys.exit(f"verify_framing: siril crop+stat failed on {image}\n{tail}")
    return stats


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    opts = dict(a[2:].split("=", 1) for a in sys.argv[1:]
                if a.startswith("--") and "=" in a)
    if len(args) != 2:
        sys.exit(__doc__)
    session, product = args
    rec_path = os.path.join(REPO, "datasets", session,
                            f"framing_{product}.json")
    if not os.path.exists(rec_path):
        sys.exit(f"verify_framing: no record {rec_path} (draw it first: "
                 "web/crop.html)")
    rec = json.load(open(rec_path))
    crop = rec["rect_siril_crop_args"]
    workdir = os.path.join(REPO, "sessions", session, "work")

    if "map" in opts:
        if "map-min" not in opts:
            sys.exit("--map needs --map-min=<members> (the coverage "
                     "threshold; map value = members*1000)")
        image = os.path.abspath(opts["map"])
        floor = float(opts["map-min"]) * 1000.0
        method = (f"coverage map {os.path.relpath(image, REPO)}: require "
                  f"stat Min >= {opts['map-min']} members * 1000")
    elif "min-floor" in opts:
        image = os.path.join(REPO, "web", "results", session,
                             f"{product}.fit")
        floor = float(opts["min-floor"])
        method = (f"product stack sky floor: require stat Min >= {floor} ADU "
                  "(sibling-class floor rule — never mere non-zero)")
    else:
        sys.exit("pick a mode: --map=<map.fit> --map-min=<n>  OR  "
                 "--min-floor=<ADU>")
    if not os.path.exists(image):
        sys.exit(f"verify_framing: no such image {image}")

    stats = run_crop_stat(image, crop, workdir)
    worst_min = min(s["min"] for s in stats)
    ok = worst_min >= floor
    result = {"method": method, "image": os.path.relpath(image, REPO),
              "crop_args": crop, "floor": floor,
              "measured": stats, "worst_min": worst_min,
              "verdict": "PASS" if ok else "FAIL"}
    if ok:
        rec["status"] = "verified"
        rec["verified_by"] = result
    else:
        rec["status"] = "unverified"
        rec["last_verification_failure"] = result
    with open(rec_path, "w") as f:
        json.dump(rec, f, indent=1)
        f.write("\n")
    tag = "PASS — record VERIFIED" if ok else "FAIL — record stays unverified"
    print(f"[verify_framing] {tag}: worst-channel Min {worst_min} vs floor "
          f"{floor}\n[verify_framing] record: "
          f"{os.path.relpath(rec_path, REPO)}")
    sys.exit(0 if ok else 2)


if __name__ == "__main__":
    main()
