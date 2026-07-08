#!/usr/bin/env python3
"""Linear-stack comparison numbers: MW contrast (starcomb boxes), radial G
profile at key radii, rim-vs-mid deviation, and per-channel rim chroma.

Usage: measure_stack.py <stack.fit> [reference_stack.fit ...]
       [--session=<dir> --set=<name>]  (per-set report boxes; without
       these there is no corridor, so MW contrast reads n/a)

All values in 16-bit counts (read_fits returns [0,1]; scaled here).
rim_dev = mean(G, r>0.93) / mean(G, 0.3<r<0.7) - 1 — the G luminance rim
number that tracks V(r)/glow rim correction quality.
"""
import os
import sys

import numpy as np

# scripts/lib holds the shared libs (astrometrics, bg_qa); locate it by
# walking up from this file so one bootstrap works at any nesting depth.
_libdir = os.path.dirname(os.path.abspath(__file__))
while _libdir != os.path.dirname(_libdir):
    if os.path.isdir(os.path.join(_libdir, "lib")):
        sys.path.insert(0, os.path.join(_libdir, "lib"))
        break
    _libdir = os.path.dirname(_libdir)
import astrometrics as am  # noqa: E402
from starcomb import box_median_g  # noqa: E402


def measure(path):
    d, _ = am.read_fits(path)
    d16 = d * 65535.0
    c, h0, w0 = d16.shape
    mwb, skb = am.report_boxes(h0, w0)
    mw = (box_median_g(d16, mwb) - box_median_g(d16, skb)
          if mwb and skb else float("nan"))
    c, h, w = d16.shape
    yy = (np.arange(h) - h / 2)[:, None] / (h / 2)
    xx = (np.arange(w) - w / 2)[None, :] / (w / 2)
    r = np.sqrt((yy ** 2 + xx ** 2) / 2.0)
    g = d16[min(1, c - 1)]
    sub = slice(None, None, 4)          # 4x subsample: plenty for medians
    rs, gs = r[sub, sub], g[sub, sub]
    rr = d16[0][sub, sub]
    bb = d16[2][sub, sub] if c >= 3 else gs
    prof = {}
    for lo, hi, name in ((0.3, 0.7, "mid"), (0.85, 0.93, "outer"),
                         (0.93, 1.01, "rim")):
        m = (rs >= lo) & (rs < hi)
        prof[name] = (float(np.median(gs[m])),
                      float(np.median(rr[m] - gs[m])),
                      float(np.median(bb[m] - gs[m])))
    bins = np.linspace(0, 1, 21)
    gprof = []
    for i in range(20):
        m = (rs >= bins[i]) & (rs < bins[i + 1])
        if m.sum() > 200:
            gprof.append(float(np.median(gs[m])))
    rim_dev = prof["rim"][0] / prof["mid"][0] - 1 if prof["mid"][0] else 0.0
    return {"mw": mw, "prof": prof, "rim_dev": rim_dev, "gprof": gprof}


def main():
    paths = [a for a in sys.argv[1:] if not a.startswith("--")]
    opts = dict(a[2:].split("=", 1) for a in sys.argv[1:]
                if a.startswith("--") and "=" in a)
    if "session" in opts and "set" in opts:
        am.configure(opts["session"], opts["set"],
                     stack=paths[0] if paths else None)
    if not paths:
        sys.exit(__doc__)
    for p in paths:
        m = measure(p)
        pr = m["prof"]
        print(f"{os.path.basename(p)}:")
        print(f"  MW contrast (G, MW_BOX - SKY_BOX): {m['mw']:+.1f} counts")
        print(f"  G median mid {pr['mid'][0]:.1f} | outer(0.85-0.93) "
              f"{pr['outer'][0]:.1f} | rim(>0.93) {pr['rim'][0]:.1f} "
              f"-> rim_dev {100 * m['rim_dev']:+.1f}%")
        print(f"  chroma R-G / B-G: mid {pr['mid'][1]:+.1f}/{pr['mid'][2]:+.1f}"
              f" | rim {pr['rim'][1]:+.1f}/{pr['rim'][2]:+.1f}")
        print("  G radial (20 bins): "
              + " ".join(f"{v:.0f}" for v in m["gprof"]))


if __name__ == "__main__":
    main()
