#!/usr/bin/env python3
"""Siril's own BACKGROUND NOISE and level inside boxes another instrument has
already verified — the DEPTH axis of the corner-quality question.

  regional_noise.py <stack.fit> <shape_at_sky.json> <out.json>

WHY IT EXISTS AND WHY IT IS NOT A NEW INSTRUMENT. Coverage depth cannot move
star shape; what it moves is noise. `snr_regions.py` compares stacks at ONE sky
pair and divides by a WHOLE-IMAGE `bgnoise`, so it cannot answer "does noise
track depth ACROSS positions of one union". Siril answers that itself: `crop`
replaces the loaded image, so `bgnoise` after `crop` IS the tool's own regional
background-noise estimate, and `stat` gives the box's level in the same load.
Every number here is Siril's; in-house is the tabulation and the sqrt(n) ratio.

BOX PLACEMENT IS INHERITED, NEVER RE-DERIVED. The crop rectangles come out of
the `shape_at_sky.py` record, whose placement that instrument VERIFIED against
the tool's own per-star RA/Dec (the crop y-flip trap). Re-deriving them here
would re-open a resolved question with no verifier attached.

REPORTS ONLY: no threshold, no verdict, always exits 0.
"""
import json
import os
import re
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "..",
                                "scripts", "lib"))
from siril_run import run as siril_run          # serialized invoker

NOISE_RE = re.compile(r"Background noise value \(channel: #(\d)\): ([0-9.]+)")
STAT_RE = re.compile(r"(\w+) layer: Mean: (-?[0-9.e+-]+), "
                     r"Median: (-?[0-9.e+-]+), Sigma: (-?[0-9.ena+-]+)")


def main():
    stack, shape_json, out_json = (os.path.abspath(p) for p in sys.argv[1:4])
    rows = [r for r in json.load(open(shape_json))["positions"]
            if not r.get("out_of_canvas")]
    workdir = os.path.dirname(out_json) or "."
    ssf = os.path.join(workdir, "_regional_noise.ssf")
    with open(ssf, "w") as fh:
        fh.write("requires 1.4.4\nsetcompress 0\nsetext fit\n")
        for r in rows:
            x, y, w, h = r["crop"]
            fh.write(f"load {stack}\ncrop {x} {y} {w} {h}\nbgnoise\nstat\n")
    res = siril_run(["-d", workdir, "-s", ssf], capture_output=True, text=True)
    text = res.stdout + res.stderr
    os.remove(ssf)

    # One block per position, in emission order, anchored on Siril's own
    # "Running command: bgnoise" echo — the same discipline coverage_frame.py
    # uses: anchor on the COMMAND, never on the value lines, or a box that
    # prints nothing shifts every later box's numbers one box up with no error
    # anywhere.
    blocks, cur = [], None
    for line in text.splitlines():
        if "Running command: bgnoise" in line:
            cur = {"noise": {}, "stat": {}}
            blocks.append(cur)
            continue
        if cur is None:
            continue
        m = NOISE_RE.search(line)
        if m:
            cur["noise"][int(m.group(1))] = float(m.group(2))
        m = STAT_RE.search(line)
        if m:
            cur["stat"][m.group(1)] = {"mean": float(m.group(2)),
                                       "median": float(m.group(3))}
    if len(blocks) != len(rows):
        sys.exit(f"regional_noise: siril produced {len(blocks)} load blocks for "
                 f"{len(rows)} boxes — siril said:\n{text[-1500:]}")

    out = []
    for r, b in zip(rows, blocks):
        out.append({"label": r["label"], "ra": r["ra"], "dec": r["dec"],
                    "crop": r["crop"], "bgnoise": b["noise"], "level": b["stat"]})
        n = b["noise"]
        s = b["stat"]
        print(f"  {r['label']:<22} bgnoise "
              + " ".join(f"{n.get(c, float('nan')):7.3f}" for c in (0, 1, 2))
              + "   median "
              + " ".join(f"{s.get(k, {}).get('median', float('nan')):8.2f}"
                         for k in ("Red", "Green", "Blue")))
    json.dump({"stack": stack, "shape_record": shape_json,
               "instrument": "Siril load + crop + bgnoise + stat, in boxes "
                             "whose placement shape_at_sky.py verified against "
                             "the tool's own per-star RA/Dec",
               "reports_only": "no threshold, no verdict",
               "positions": out}, open(out_json, "w"), indent=1)
    print(f"  record -> {out_json}")


if __name__ == "__main__":
    main()
