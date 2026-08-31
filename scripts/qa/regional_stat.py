#!/usr/bin/env python3
"""Regional Siril `stat` on a LINEAR stack: centre + 4 corners, per channel.

Orchestration + record only — Siril does every measurement (load / crop /
stat); this drives it and records the numbers. Gradient reads MUST be taken
in the linear domain (dead-end registry: an autostretch can compress or
amplify a background ratio by several x), so run this on the linear
(pre-stretch) stack — the _spcc surface for cross-arm comparisons.

Usage: regional_stat.py <stack.fit> <out.json> [--box=400] [--margin=200]
                        [--rect=x,y,w,h | --coverage=<coverage.json>]
       regional_stat.py --selftest        (Siril-driven, on planted canvases)

The .ssf + Siril workdir live beside the OUTPUT record (a per-set qa_work
dir under $HOME — the Siril flatpak has a private /tmp, so a script placed
there would be invisible to it).

WHERE THE REGIONS GO. Without a placement flag the five regions sit on the
CANVAS: centre at the middle, the corners `margin` px in from the canvas
edges — right for a per-set product, whose canvas is fully covered sky, and
byte-for-byte the behaviour every per-set baseline was seeded under. A
framing=max UNION is different: its axis-aligned bounding box has EMPTY
corners (the rotated members' quad leaves triangles of no coverage), so
canvas-edge corners measure the compose's empty-canvas pedestal, not sky.
MEASURED on the corpus stack_july31+aug06+aug09+aug14_full_spcc (8520x5668):
three of the four canvas-edge corner boxes read a Green median of 6.1e-5
against 6.0e-4 of covered sky — a 10x "spread" that is COVERAGE, not
flatness — and Siril printed ONE layer line for the two constant ones, which
the old per-line parser stored as ch0 alone (baseline_guard then raised
KeyError 'ch1'). Hence:
  --rect=x,y,w,h        place the regions INSIDE this rectangle (Siril crop
                        convention: x,y from the top-left, y downward): the
                        corners `margin` px in from the rectangle's edges, the
                        centre at the rectangle's centre.
  --coverage=<json>     the same, taking the rectangle from a coverage_frame.py
                        record's `rect_siril_crop_args` (its largest fully
                        covered axis-aligned rectangle at the record's own
                        floor/channel/grid); the record's `canvas_wh` must equal
                        the product's NAXIS or the run refuses. The record
                        carries the placement and the coverage record's identity
                        (path + head/tail sha) so a later compare can REUSE the
                        same rectangle rather than recompute it.
A rectangle that does not fit the canvas, or that cannot hold the five boxes
with their margins, refuses.

THE CONSTANT-REGION REFUSAL, and what Siril actually prints (measured, this
rig, flatpak 1.4.4). On the corpus's canvas-edge BL corner
(`crop 200 5068 400 400` of stack_…_full_spcc.fit) Siril prints ALL THREE
layers — a constant layer carries `Sigma: -nan`:
  log: Red layer: Mean: 10.2, Median: 10.2, Sigma: -nan, Min: 10.2, Max: 10.2, bgnoise: 0.0
  log: Green layer: Mean: 4.0, Median: 4.0, Sigma: 0.0, Min: 4.0, Max: 4.0, bgnoise: 0.0
  log: Blue layer: Mean: 6.1, Median: 6.1, Sigma: -nan, Min: 6.1, Max: 6.1, bgnoise: 0.0
The previous parser required a NUMERIC sigma, so the two `-nan` lines were
dropped and the region was recorded with ONE channel — that, not a short Siril
output, is how the corpus's first seed died in a KeyError downstream. (A file
whose every layer is constant everywhere prints a single line —
`log: Red layer: Mean: 4.0, Median: 4.0, Sigma: -nan, Min: 4.0, Max: 4.0, bgnoise: 0.0`
— the degenerate case, also covered.) A near-constant region prints
`Sigma: 0.0` with Min != Max (measured on a planted 6.1e-5 ± 5e-7 region:
Min 3.9, Max 4.1). Hence two refusals, both loud, both naming the region, its
crop box and the layer(s), exit non-zero, NO partial record:
  (a) fewer layer lines than the product has layers;
  (b) a CONSTANT layer (Sigma nan, or Min == Max) — a region that reads a
      constant is not measuring sky (an empty union corner): place the regions
      with --rect/--coverage. `sigma` is recorded as null for a nan.
"""
import json
import os
import re
import subprocess
import sys

from astropy.io import fits

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "lib"))
from siril_run import SIRIL, run as siril_run   # serialized invoker

STAT_RE = re.compile(r"(?:^log:\s*)?(\w+)?[:\s]*Mean: ([0-9.]+), "
                     r"Median: ([0-9.]+), Sigma: (-?nan|[0-9.]+), Min: ([0-9.]+), Max: ([0-9.]+)")
CONSTANT_LAYER_VERBATIM = ("log: Red layer: Mean: 10.2, Median: 10.2, Sigma: -nan, Min: 10.2, "
                           "Max: 10.2, bgnoise: 0.0")


def parse_rect(s):
    try:
        x, y, w, h = (int(v) for v in s.split(","))
    except ValueError:
        sys.exit(f"regional_stat: --rect wants x,y,w,h integers (got {s!r})")
    return [x, y, w, h]


def regions_for(w, hgt, box, margin, rect=None):
    """The five region origins (Siril crop convention). rect=None -> the canvas
    placement (unchanged); rect=[x,y,rw,rh] -> inside the rectangle."""
    if rect is None:
        return {"center": ((w - box) // 2, (hgt - box) // 2), "TL": (margin, margin),
                "TR": (w - margin - box, margin), "BL": (margin, hgt - margin - box),
                "BR": (w - margin - box, hgt - margin - box)}
    x, y, rw, rh = rect
    if x < 0 or y < 0 or rw <= 0 or rh <= 0 or x + rw > w or y + rh > hgt:
        sys.exit(f"regional_stat: REFUSED — rect {rect} does not fit the {w}x{hgt} canvas")
    if rw < box + 2 * margin or rh < box + 2 * margin:
        sys.exit(f"regional_stat: REFUSED — rect {rect} cannot hold {box}-px boxes at margin {margin}")
    return {"center": (x + (rw - box) // 2, y + (rh - box) // 2), "TL": (x + margin, y + margin),
            "TR": (x + rw - margin - box, y + margin), "BL": (x + margin, y + rh - margin - box),
            "BR": (x + rw - margin - box, y + rh - margin - box)}


def _headtail(path, blocks=64):
    import hashlib
    h = hashlib.sha256(); sz = os.path.getsize(path); h.update(str(sz).encode())
    with open(path, "rb") as fh:
        h.update(fh.read(blocks * 4096))
        if sz > blocks * 8192:
            fh.seek(-blocks * 4096, os.SEEK_END); h.update(fh.read())
    return h.hexdigest()[:32]


def rect_from_coverage(path, canvas_wh):
    rec = json.load(open(path))
    r = rec.get("rect_siril_crop_args")
    if not r:
        sys.exit(f"regional_stat: REFUSED — {path} proposes no rectangle (rect_fits {rec.get('rect_fits')!r}: "
                 "nothing cleared its floor); run coverage_frame.py with a floor that yields one")
    if [int(v) for v in rec.get("canvas_wh", [])] != [int(v) for v in canvas_wh]:
        sys.exit(f"regional_stat: REFUSED — the coverage record's canvas {rec.get('canvas_wh')} is not this "
                 f"product's {list(canvas_wh)}; a rectangle from another canvas would place the regions elsewhere")
    return [int(v) for v in r], {"coverage_record": os.path.abspath(path), "coverage_record_sha": _headtail(path),
                                  "coverage_source": rec.get("source"), "coverage_floor": rec.get("floor"),
                                  "coverage_channel": rec.get("channel"), "coverage_grid": rec.get("grid"),
                                  "rect_fits": rec.get("rect_fits")}


def measure(stack, out_json, box=400, margin=200, rect=None, placement=None):
    """Drive Siril over the five regions; write the record only when every region
    yielded every layer. Returns the record."""
    stack, out_json = os.path.abspath(stack), os.path.abspath(out_json)
    hdr = fits.getheader(stack)
    w, hgt = int(hdr["NAXIS1"]), int(hdr["NAXIS2"])
    nchan = int(hdr.get("NAXIS3", 1))
    regions = regions_for(w, hgt, box, margin, rect)
    wdir = os.path.dirname(out_json)
    os.makedirs(wdir, exist_ok=True)
    ssf = os.path.join(wdir, "_stat.ssf")
    rec = {"input": stack, "domain": "linear (run this on the pre-stretch "
           "surface; cross-arm comparisons use the _spcc stack)",
           "box_px": box, "corner_margin_px": margin,
           "image_wh": [w, hgt], "channels": nchan, "regions": {}}
    if rect is not None:
        rec["placement"] = dict({"source": "rect", "rect_siril_crop_args": list(rect),
                                 "note": "regions placed INSIDE the rectangle (corners `margin` px in from its edges, centre at its centre)"},
                                **(placement or {}))
    try:
        for name, (x, y) in regions.items():
            with open(ssf, "w") as f:
                f.write(f"requires 1.2.0\nsetcompress 0\nsetext fit\nload {stack}\n"
                        f"crop {x} {y} {box} {box}\nstat\n")
            r = siril_run(["-d", wdir, "-s", ssf], capture_output=True, text=True)
            chans = {}
            for line in (r.stdout + r.stderr).splitlines():
                m = STAT_RE.search(line)
                if m:
                    ch = m.group(1) if m.group(1) in ("Red", "Green", "Blue", "B", "R", "G") else f"ch{len(chans)}"
                    sig = m.group(4)
                    chans[ch] = {"mean": float(m.group(2)), "median": float(m.group(3)),
                                 "sigma": None if "nan" in sig else float(sig),
                                 "min": float(m.group(5)), "max": float(m.group(6))}
            where = f"region {name} (crop {x} {y} {box} {box} on {stack})"
            if len(chans) < nchan:
                missing = [f"ch{i}" for i in range(len(chans), nchan)]
                sys.exit(f"regional_stat: REFUSED — {where}: Siril printed {len(chans)} of {nchan} layer lines; missing "
                         f"{', '.join(missing)} — the region is not measuring sky (an empty union corner: place the regions "
                         f"with --rect/--coverage). No record written.\nsiril said:\n{(r.stdout + r.stderr)[-600:]}")
            const = [c for c, v in chans.items() if v["sigma"] is None or v["min"] == v["max"]]
            if const:
                detail = "; ".join(f"{c} min {chans[c]['min']} max {chans[c]['max']} sigma {chans[c]['sigma']}" for c in const)
                sys.exit(f"regional_stat: REFUSED — {where}: layer(s) {', '.join(const)} are CONSTANT ({detail}; "
                         f"Siril prints a constant layer as e.g. {CONSTANT_LAYER_VERBATIM!r}) — a constant region is not sky "
                         "(an empty union corner: place the regions with --rect/--coverage). No record written.")
            rec["regions"][name] = chans
    finally:
        if os.path.exists(ssf):
            os.remove(ssf)
    with open(out_json, "w") as f:
        json.dump(rec, f, indent=1)
    for name, chans in rec["regions"].items():
        meds = " ".join(f"{c}={v['median']:.1f}" for c, v in chans.items())
        print(f"{name}: {meds}")
    print(f"record: {out_json}")
    return rec


def selftest():
    """Siril-driven positive controls on planted canvases (scratch under $HOME/.cache):
    (1) a union-like canvas — constant sky 6.0e-4 inside a rotated-quad coverage,
        the empty corners at 1/10 of it with a little noise so Siril prints all
        three layers — WITH a planted rect inside the coverage MUST read the sky
        value at all four corners; (2) the same canvas WITHOUT the rect MUST read
        the empty value at the corners (the canvas-edge failure the fix names);
    (3) a canvas whose TL corner is EXACTLY constant MUST refuse naming TL and its
        crop box, and write no record."""
    import shutil
    import numpy as np
    T = os.path.join(os.path.expanduser("~"), ".cache", "astro-imaging", "regional_stat_selftest")
    shutil.rmtree(T, ignore_errors=True); os.makedirs(T)
    # A union-like canvas: a rectangle of half-extents 1700x1100 rotated 25 deg (its
    # own corners clipped by the canvas) leaves the four canvas corners EMPTY — the
    # canvas-edge corner boxes (200..600 px in) lie entirely outside it, while the
    # planted rect [1200,800,2400,1600] and its corner boxes lie entirely inside
    # (worked through corner by corner; the selftest measures it anyway). The empty
    # corners carry a little noise so Siril prints all three layers with Min != Max
    # and the canvas-edge run RECORDS the wrong medians rather than refusing.
    W, H, SKY, EMPTY = 4800, 3200, 6.0e-4, 6.1e-5
    rng = np.random.default_rng(3)
    yy, xx = np.mgrid[0:H, 0:W]
    cx, cy, th = W / 2, H / 2, np.radians(25.0)
    u = (xx - cx) * np.cos(th) + (yy - cy) * np.sin(th); v = -(xx - cx) * np.sin(th) + (yy - cy) * np.cos(th)
    covered = (np.abs(u) < 1700) & (np.abs(v) < 1100)
    img = np.where(covered, SKY + rng.normal(0, 1e-5, (H, W)), EMPTY + rng.normal(0, 5e-7, (H, W))).astype(np.float32)
    union = os.path.join(T, "union.fit"); fits.PrimaryHDU(np.stack([img] * 3)).writeto(union, overwrite=True)
    const = img.copy(); const[H - 800:, :800] = EMPTY                 # FITS bottom rows = Siril's TOP-left: an exactly constant TL crop
    constf = os.path.join(T, "const_tl.fit"); fits.PrimaryHDU(np.stack([const] * 3)).writeto(constf, overwrite=True)
    rect = [1200, 800, 2400, 1600]                                      # inside the coverage, symmetric so y-convention cannot matter
    sky16, empty16 = SKY * 65535, EMPTY * 65535
    bad = 0
    def check(label, ok, detail=""):
        nonlocal bad
        print(f"  selftest {'ok  ' if ok else 'WRONG'} {label} {detail}"); bad |= not ok
    r1 = measure(union, os.path.join(T, "with_rect.json"), rect=rect)
    meds = {k: r1["regions"][k]["ch1"]["median"] for k in ("TL", "TR", "BL", "BR", "center")}
    check("(1) --rect inside the coverage: all four corners read the SKY value", all(abs(m - sky16) < 0.1 * sky16 for m in meds.values()), f"medians {meds} (sky {sky16:.1f}, empty {empty16:.1f})")
    check("    the record carries the placement", r1.get("placement", {}).get("rect_siril_crop_args") == rect)
    r2 = measure(union, os.path.join(T, "canvas_edge.json"))
    meds2 = {k: r2["regions"][k]["ch1"]["median"] for k in ("TL", "TR", "BL", "BR")}
    check("(2) canvas-edge placement on the union: the corners read the EMPTY value — the failure the fix names", all(abs(m - empty16) < 0.5 * empty16 for m in meds2.values()), f"medians {meds2}")
    check("    the canvas-edge record carries no placement field (per-set behaviour unchanged)", "placement" not in r2)
    rc, msg = None, ""
    try:
        measure(constf, os.path.join(T, "const.json"))
    except SystemExit as e:
        rc, msg = 1, str(e)
    check("(3) an exactly constant corner REFUSES naming the region, its box and the layers, exit non-zero", rc == 1 and "REFUSED" in msg and "region TL" in msg and "crop 200 200 400 400" in msg and "CONSTANT" in msg, msg[:160].replace("\n", " "))
    check("    no partial record written on refusal", not os.path.exists(os.path.join(T, "const.json")))
    try:
        measure(union, os.path.join(T, "bad_rect.json"), rect=[4000, 2400, 1600, 1600]); rc4 = 0
    except SystemExit as e:
        rc4, m4 = 1, str(e)
    check("(4) a rect outside the canvas REFUSES", rc4 == 1 and "does not fit" in m4)
    shutil.rmtree(T, ignore_errors=True)
    if bad:
        print("regional_stat --selftest: FAIL"); return 1
    print("OK: regional_stat — a planted union canvas reads sky at all four corners with a rect inside the coverage and the "
          "empty level without it; an exactly constant corner refuses by name with no record; a rect outside the canvas refuses")
    return 0


def main():
    if len(sys.argv) > 1 and sys.argv[1] == "--selftest":
        return selftest()
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    opts = dict(a[2:].split("=", 1) for a in sys.argv[1:]
                if a.startswith("--") and "=" in a)
    if len(args) != 2:
        sys.exit(__doc__)
    stack, out_json = os.path.abspath(args[0]), os.path.abspath(args[1])
    box, margin = int(opts.get("box", 400)), int(opts.get("margin", 200))
    rect, placement = None, None
    if "rect" in opts and "coverage" in opts:
        sys.exit("regional_stat: give --rect OR --coverage, not both")
    if "rect" in opts:
        rect = parse_rect(opts["rect"])
    elif "coverage" in opts:
        hdr = fits.getheader(stack)
        rect, placement = rect_from_coverage(opts["coverage"], (int(hdr["NAXIS1"]), int(hdr["NAXIS2"])))
        placement["source"] = "coverage"
    measure(stack, out_json, box, margin, rect, placement)
    return 0


if __name__ == "__main__":
    sys.exit(main())
