#!/usr/bin/env python3
"""Prove darktable's lens correction is DISTORTION-ONLY on this rig.

Usage:
  verify_lens_card.py --from-frame <raw>  [--work DIR] [--json OUT]
  verify_lens_card.py --camera M --lens L --focal F [--work DIR] [--json OUT]

WHY THIS EXISTS. darktable applies its DEFAULT correction set (distortion + TCA +
vignetting) and a style cannot choose otherwise — only the module's enabled bit
survives in a style, every op_params field is ignored. The unwanted vignetting
correction DOUBLE-corrects lights already flat-corrected upstream (measured
corner/centre 1.27-1.37x linear on a full-depth stack). Distortion-only is
therefore enforced in the DATA lensfun reads: install_lens_model.sh strips this
lens's <vignetting>/<tca> from the user DB, and `lensfun-update-data` OVERWRITES
that strip. This script is the behavioural check that the strip is actually
holding — prescribed per rig and after any darktable/lensfun bump.

THE TRAP THIS SCRIPT EXISTS TO AVOID — a uniform card alone proves NOTHING.
Warping a perfectly uniform field yields the same uniform field (darktable's edge
handling keeps the boundary constant too), so "corner medians == centre" passes
IDENTICALLY whether vignetting was stripped or the lens module never fired at
all. MEASURED here: on the uniform card, lensdist vs nodist came back
pixel-identical (Siril: "all nil") even though the module was live. So the test
runs TWO fixtures:

  1. GRID (positive control) — a non-uniform field. lensdist vs nodist MUST differ,
     which proves the module fires for these optics on this fixture type.
  2. UNIFORM — corner medians must equal the centre median. With (1) passing, a
     null here means no PHOTOMETRIC correction, i.e. vignetting is out of the path.

Both must pass. (1) alone says nothing about vignetting; (2) alone is vacuous.

DO NOT compare the rendered files byte-wise. MEASURED here: `cmp` reported the two
uniform-card renders as DIFFERING while Siril `isub` proved them pixel-identical —
the difference is TIFF metadata. Never gate this route on a file hash.

WHAT THIS DOES NOT CHECK: the correction SET, not its CORRECTNESS. A wrong-but-
present distortion model passes. Use lens_preflight.py --require-profile per set
for the per-set assertion, and fit_lens_model.sh when the model itself is suspect.

darktable does every pixel operation; Siril does every measurement (isub, stat,
boxselect). This script generates two synthetic TEST FIXTURES (never a
deliverable), drives the two tools, and compares the numbers they printed.

Removal condition: retires when darktable honours a style's lens op_params
headless, at which point the correction set can be pinned in the style and the
DB strip is no longer load-bearing.
"""
import argparse
import json
import os
import re
import subprocess
import sys

SIRIL = ["flatpak", "run", "--command=siril-cli", "org.siril.Siril"]
W, H = 6064, 4040          # Z6III full-frame sensor; any size works
BOX = 400                  # region side for the median comparison
INSET = 300                # keep corner boxes off the warp's edge


def sh(cmd, **kw):
    return subprocess.run(cmd, capture_output=True, text=True, **kw)


def optics_from_frame(path):
    r = sh(["exiftool", "-json", "-Model", "-LensModel", "-FocalLength", path])
    d = json.loads(r.stdout)[0]
    focal = re.match(r"([0-9.]+)", str(d.get("FocalLength", "")))
    return (d.get("Model"), d.get("LensModel"),
            float(focal.group(1)) if focal else None)


def make_fixtures(work):
    """Two synthetic cards at sensor size. Fixtures, not deliverables."""
    from PIL import Image, ImageDraw
    uni = os.path.join(work, "card_uniform.tif")
    Image.new("I;16", (W, H), 30000).save(uni, compression=None)
    grid = os.path.join(work, "card_grid.tif")
    im = Image.new("I;16", (W, H), 8000)
    d = ImageDraw.Draw(im)
    for x in range(0, W, 200):
        d.line([(x, 0), (x, H)], fill=60000, width=5)
    for y in range(0, H, 200):
        d.line([(0, y), (W, y)], fill=60000, width=5)
    im.save(grid, compression=None)
    return uni, grid


def stamp_exif(path, camera, lens, focal):
    """lensfun matches on EXIF; a fixture has none until we write it."""
    sh(["exiftool", "-overwrite_original", "-q",
        "-Make=NIKON CORPORATION", f"-Model={camera}",
        f"-LensModel={lens}", f"-FocalLength={focal}", "-FNumber=4", path])


def render(src, style, work):
    out = os.path.join(work, f"{os.path.basename(src)[:-4]}_{style}.tif")
    r = sh(["darktable-cli", src, out, "--style", style, "--style-overwrite",
            "--icc-type", "SRGB", "--core", "--configdir",
            os.path.expanduser("~/.config/darktable"), "--library", ":memory:",
            "--conf", "plugins/imageio/format/tiff/bpp=16"])
    if not os.path.exists(out):
        sys.exit(f"verify_lens_card: darktable produced no output for {style} "
                 f"on {os.path.basename(src)}\n{r.stdout[-500:]}")
    return out


def siril(work, lines):
    ssf = os.path.join(work, "_card.ssf")           # MUST be under $HOME:
    with open(ssf, "w") as f:                       # the flatpak has a private /tmp
        f.write("requires 1.4.4\nsetcompress 0\n" + "\n".join(lines) + "\n")
    return sh(SIRIL + ["-d", work, "-s", ssf]).stdout


def difference(work, a, b, tag):
    """Siril measures; we only read what it printed."""
    out = siril(work, [f"load {b}", f"save {tag}_ref", f"load {a}",
                       f"isub {tag}_ref", "stat"])
    if re.search(r"Statistics computation failed.*all nil", out):
        return {"identical": True, "sigma": [], "max": []}
    sig = [float(x) for x in re.findall(r"Sigma:\s*([0-9.eE+-]+)", out)]
    mx = [float(x) for x in re.findall(r"Max:\s*([0-9.eE+-]+)", out)]
    if not sig:
        sys.exit("verify_lens_card: Siril reported neither statistics nor its "
                 "all-nil refusal — output format may have drifted:\n" + out[-600:])
    return {"identical": False, "sigma": sig, "max": mx}


def region_medians(work, img):
    boxes = [("centre", (W - BOX) // 2, (H - BOX) // 2),
             ("corner_TL", INSET, INSET),
             ("corner_TR", W - INSET - BOX, INSET),
             ("corner_BL", INSET, H - INSET - BOX),
             ("corner_BR", W - INSET - BOX, H - INSET - BOX)]
    lines = [f"load {img}"]
    for _, x, y in boxes:
        lines += [f"boxselect {x} {y} {BOX} {BOX}", "stat"]
    out = siril(work, lines)
    med = [float(m) for m in re.findall(r"Median:\s*([0-9.eE+-]+)", out)]
    if len(med) < len(boxes) * 3:                   # 3 channels per stat
        sys.exit("verify_lens_card: Siril returned fewer medians than regions "
                 "requested — cannot judge:\n" + out[-600:])
    return {name: med[i * 3:(i + 1) * 3] for i, (name, _, _) in enumerate(boxes)}


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--from-frame", help="read camera/lens/focal from this raw's EXIF")
    ap.add_argument("--camera")
    ap.add_argument("--lens")
    ap.add_argument("--focal", type=float)
    ap.add_argument("--work", help="scratch dir; MUST be under $HOME (Siril "
                                   "flatpak has a private /tmp). Default: "
                                   "./lenscard_work")
    ap.add_argument("--json", help="write the record here")
    ap.add_argument("--tol", type=float, default=1.0,
                    help="max |corner-centre| median difference to PASS (ADU)")
    a = ap.parse_args()

    if a.from_frame:
        camera, lens, focal = optics_from_frame(a.from_frame)
    else:
        camera, lens, focal = a.camera, a.lens, a.focal
    if not (camera and lens and focal):
        sys.exit("verify_lens_card: need --from-frame or all of "
                 "--camera/--lens/--focal")

    work = os.path.abspath(a.work or "lenscard_work")
    if not work.startswith(os.path.expanduser("~")):
        sys.exit(f"verify_lens_card: --work must be under $HOME (Siril's flatpak "
                 f"cannot see {work})")
    os.makedirs(work, exist_ok=True)

    print(f"verify_lens_card: {camera!r} + {lens!r} @ {focal}mm")
    uni, grid = make_fixtures(work)
    for f in (uni, grid):
        stamp_exif(f, camera, lens, focal)

    # 1. POSITIVE CONTROL — the module must fire on a non-uniform field.
    g = difference(work, render(grid, "lensdist", work),
                   render(grid, "nodist", work), "grid")
    if g["identical"]:
        print("  grid control: lensdist == nodist — module did NOT fire", file=sys.stderr)
        sys.exit("verify_lens_card: FAIL — the lens module produced no change on "
                 "the grid fixture, so lensfun matched nothing for these optics. "
                 "The uniform-card result would be vacuous. Check the lensfun DB "
                 "(lensfun-update-data) and that the EXIF strings match a DB entry.")
    print(f"  grid control: module FIRES (Siril sigma {max(g['sigma']):.1f})")

    # 2. UNIFORM — with the control passing, a null here means no vignetting.
    u_l = render(uni, "lensdist", work)
    u = difference(work, u_l, render(uni, "nodist", work), "uni")
    med = region_medians(work, u_l)
    centre = max(med["centre"])
    # max() over the corners, not a `>` accumulator seeded at 0.0: a perfect PASS
    # has every delta == 0.0, which never beats the seed and would report no corner.
    deltas = {name: max(abs(v - centre) for v in vals)
              for name, vals in med.items() if name != "centre"}
    worst = max(deltas, key=deltas.get)
    worst_d = deltas[worst]
    ok = worst_d <= a.tol
    print(f"  uniform card: centre median {centre:.1f}; worst corner "
          f"{worst} differs by {worst_d:.3f} ADU (tol {a.tol})")
    print(f"  uniform card lensdist vs nodist: "
          f"{'pixel-identical' if u['identical'] else 'differs'}")

    rec = {"camera": camera, "lens": lens, "focal_mm": focal,
           "grid_control": g, "uniform_diff": u, "region_medians": med,
           "centre_median": centre, "worst_corner": worst,
           "worst_delta_adu": worst_d, "tol_adu": a.tol,
           "verdict": "PASS" if ok else "FAIL"}
    if a.json:
        with open(a.json, "w") as f:
            json.dump(rec, f, indent=1)
        print(f"  wrote {a.json}")

    if not ok:
        sys.exit(f"verify_lens_card: FAIL — corner median differs from centre by "
                 f"{worst_d:.3f} ADU at {worst}. Vignetting is back in darktable's "
                 f"path: re-run scripts/darktable/install_lens_model.sh (a "
                 f"lensfun-update-data overwrites its <vignetting>/<tca> strip).")
    print("  VERDICT: PASS — distortion-only holds (module fires, no photometric change)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
