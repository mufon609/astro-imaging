#!/usr/bin/env python3
"""Regional Siril `stat` on a LINEAR stack: centre + 4 corners, per channel.

Orchestration + record only — Siril does every measurement (load / crop /
stat); this drives it and records the numbers. Gradient reads MUST be taken
in the linear domain (dead-end registry: an autostretch can compress or
amplify a background ratio by several x), so run this on the linear
(pre-stretch) stack — the _spcc surface for cross-arm comparisons.

Usage: regional_stat.py <stack.fit> <out.json> [--box=400] [--margin=200]

The .ssf + Siril workdir live beside the OUTPUT record (a per-set qa_work
dir under $HOME — the Siril flatpak has a private /tmp, so a script placed
there would be invisible to it).
"""
import json
import os
import re
import subprocess
import sys

from astropy.io import fits

SIRIL = ["flatpak", "run", "--command=siril-cli", "org.siril.Siril"]


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    opts = dict(a[2:].split("=", 1) for a in sys.argv[1:]
                if a.startswith("--") and "=" in a)
    if len(args) != 2:
        sys.exit(__doc__)
    stack, out_json = os.path.abspath(args[0]), os.path.abspath(args[1])
    box, margin = int(opts.get("box", 400)), int(opts.get("margin", 200))
    hdr = fits.getheader(stack)
    w, hgt = int(hdr["NAXIS1"]), int(hdr["NAXIS2"])
    nchan = int(hdr.get("NAXIS3", 1))

    regions = {
        "center": ((w - box) // 2, (hgt - box) // 2),
        "TL": (margin, margin),
        "TR": (w - margin - box, margin),
        "BL": (margin, hgt - margin - box),
        "BR": (w - margin - box, hgt - margin - box),
    }
    wdir = os.path.dirname(out_json)
    os.makedirs(wdir, exist_ok=True)
    ssf = os.path.join(wdir, "_stat.ssf")
    rec = {"input": stack, "domain": "linear (run this on the pre-stretch "
           "surface; cross-arm comparisons use the _spcc stack)",
           "box_px": box, "corner_margin_px": margin,
           "image_wh": [w, hgt], "channels": nchan, "regions": {}}
    for name, (x, y) in regions.items():
        with open(ssf, "w") as f:
            f.write(f"requires 1.2.0\nsetcompress 0\nload {stack}\n"
                    f"crop {x} {y} {box} {box}\nstat\n")
        r = subprocess.run(SIRIL + ["-d", wdir, "-s", ssf],
                           capture_output=True, text=True)
        chans = {}
        for line in (r.stdout + r.stderr).splitlines():
            m = re.search(r"(?:^log:\s*)?(\w+)?[:\s]*Mean: ([0-9.]+), "
                          r"Median: ([0-9.]+), Sigma: ([0-9.]+)", line)
            if m:
                ch = m.group(1) if m.group(1) in ("Red", "Green", "Blue",
                                                  "B", "R", "G") else \
                    f"ch{len(chans)}"
                chans[ch] = {"mean": float(m.group(2)),
                             "median": float(m.group(3)),
                             "sigma": float(m.group(4))}
        if not chans:
            sys.exit(f"regional_stat: no stat lines parsed for {name} — "
                     f"siril said:\n{(r.stdout + r.stderr)[-800:]}")
        rec["regions"][name] = chans
    os.remove(ssf)
    with open(out_json, "w") as f:
        json.dump(rec, f, indent=1)
    for name, chans in rec["regions"].items():
        meds = " ".join(f"{c}={v['median']:.1f}" for c, v in chans.items())
        print(f"{name}: {meds}")
    print(f"record: {out_json}")


if __name__ == "__main__":
    main()
