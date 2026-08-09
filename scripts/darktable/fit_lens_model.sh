#!/usr/bin/env bash
# Fit this camera+lens's radial distortion model FROM A SET'S OWN FRAMES, with
# official tools end to end: Siril calibrates/stretches, Hugin detects the
# between-frame star correspondences and fits the model, this script only
# orchestrates and records.
#
#   fit_lens_model.sh <session-dir> <set> --dark=<master> --flat=<master> \
#                     --hfov=<deg> [--frames=12]
#
# When to run: a new lens/body/focal meets the undistort route, or the
# drift-axis station measure (scripts/qa/star_stations.py) shows a centre band
# a DB profile cannot remove. Star fields beat calibration charts for this
# purpose: point sources at infinity, zero parallax, pure rotation between
# frames — exactly the geometry the panotools model assumes — and the fit
# happens at infinity focus, where chart-based profiles differ.
#
# Mechanism and its traps (all measured):
# - Correspondences come from `cpfind --fullscale` over ALL pairs of a
#   multi-image project on Siril-AUTOSTRETCHED 8-bit copies (geometry
#   unchanged; linear frames starve SIFT). align_image_stack is NOT usable
#   here (its correlation search dies at ~130 px inter-frame drift).
# - `cpclean` prunes mismatches (raw CP sets carry ~20 px outliers that make
#   the fit swing wildly and non-physically).
# - `--hfov` is REQUIRED and comes from the astrometric solve
#   (pixel scale x width; e.g. 18.02"/px x 6064 px = 30.35 deg): the optimizer
#   holds it PINNED. A free hfov collapses degenerate (v -> 0.93 deg, a = 98).
# - The optimize is STAGED: rotations only, then +a,b,c. A joint start from
#   zero with everything free lands in the same degenerate basin.
# - d,e (distortion-centre shift) is fitted LAST and only REPORTED: carrying
#   it needs lensfun's `<center>` element, which is undocumented (absent from
#   the shipped DTD/XSD) with an unverified sign convention — a
#   separately-bracketed knob that has not been needed.
#
# PROVISIONAL AS-WRITTEN: the procedure this script encodes was proven step by step
# on real frames (the fitted entry now in production came from it), but the
# script artifact has not yet run end to end — its first as-written run is the
# next lens/focal fit on the x86 rig.
#
# Output: fitted a,b,c (panotools convention — lensfun `model="ptlens"`
# consumes them directly) printed with the matching install command, and the
# fit record at datasets/<session>/<set>/qa_work/lens_fit.json. The fit is
# accepted only by the downstream measures on a real stack (star_stations +
# seqtilt A/B against the incumbent model), never by its own residual.
set -euo pipefail
REPO=$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)
source "$REPO/scripts/lib/siril_run.sh"   # serialized siril-cli invoker (BACKLOG item 18)
SESSION=${1:?usage: fit_lens_model.sh <session-dir> <set> --dark= --flat= --hfov= [--frames=12]}
SET=${2:?missing <set>}
DARK= FLAT= HFOV= FRAMES=12 OUTJSON=
for a in "${@:3}"; do case "$a" in
  --dark=*) DARK=${a#*=};; --flat=*) FLAT=${a#*=};;
  --hfov=*) HFOV=${a#*=};; --frames=*) FRAMES=${a#*=};;
  --out=*) OUTJSON=${a#*=};;
  *) echo "unknown arg $a" >&2; exit 1;;
esac; done
[ -n "$DARK" ] && [ -n "$FLAT" ] && [ -n "$HFOV" ] || { echo "need --dark= --flat= --hfov=" >&2; exit 1; }
# Absolutize the masters — they are embedded into a generated .ssf that `cd`s
# into the work tree, where a caller-relative path resolves to nothing (the
# same trap run_undistort_groups.sh guards; measured here: calibrate died
# "invalid arguments" on the relative path, this script's first as-written run)
[ -f "$DARK" ] || { echo "no such dark: $DARK" >&2; exit 1; }
[ -f "$FLAT" ] || { echo "no such flat: $FLAT" >&2; exit 1; }
DARK="$(cd "$(dirname "$DARK")" && pwd)/$(basename "$DARK")"
[ -z "$OUTJSON" ] || { mkdir -p "$(dirname "$OUTJSON")"; OUTJSON="$(cd "$(dirname "$OUTJSON")" && pwd)/$(basename "$OUTJSON")"; }
FLAT="$(cd "$(dirname "$FLAT")" && pwd)/$(basename "$FLAT")"

W=$REPO/datasets/$(basename "$SESSION")/$SET/qa_work
P=$W/lens_fit_work
sir(){ siril_cli -d "$P" -s "$1" >> "$P/siril.log" 2>&1; }

rm -rf "$P"; mkdir -p "$P/nef" "$P/proc" "$P/st"
mapfile -t SRC < <(find "$SESSION/$SET" -maxdepth 1 -type f \
  \( -iname '*.nef' -o -iname '*.dng' -o -iname '*.cr2' -o -iname '*.cr3' \
     -o -iname '*.arw' -o -iname '*.raf' \) | sort)
[ ${#SRC[@]} -ge "$FRAMES" ] || { echo "only ${#SRC[@]} frames" >&2; exit 1; }
python3 - "$P/nef" "${SRC[@]}" <<PY
import os, sys
dst, src = sys.argv[1], sys.argv[2:]
for i in range($FRAMES):
    s = src[round(i*(len(src)-1)/($FRAMES-1))]
    os.symlink(os.path.abspath(s), os.path.join(dst, os.path.basename(s)))
PY
printf 'requires 1.2.0\nset16bits\nsetcompress 0\nsetext fit\ncd %s\nconvert c -out=%s\ncd %s\ncalibrate c -dark=%s -flat=%s -cfa -equalize_cfa -debayer -prefix=pp_\n' \
  "$P/nef" "$P/proc" "$P/proc" "$DARK" "$FLAT" > "$P/c.ssf"
sir "$P/c.ssf"
i=0
for f in "$P/proc"/pp_c_*.fit; do
  i=$((i+1))
  # gauss 3 on the DETECTION COPIES only (never the data): short-sub star
  # points (~2-3 px at 2.5 s) sit below cpfind's blob scale — measured 0
  # matches at --fullscale on a 3-frame probe, 15 CPs with gauss 3 (10 at
  # 1.5); longer subs' fatter stars never needed it
  printf 'requires 1.2.0\nsetcompress 0\nsetext fit\nload %s\nautostretch\ngauss 3\nsavetif8 %s\n' \
    "$f" "$P/st/st_$(printf %02d $i)" > "$P/e.ssf"
  sir "$P/e.ssf"; rm -f "$f"
done
rm -rf "$P/nef" "$P/proc"
echo "fit_lens_model: $i stretched frames for correspondence detection"

cd "$P/st"
pto_gen -p 0 -f "$HFOV" -o gen.pto st_*.tif > /dev/null
cpfind --fullscale -o cps.pto gen.pto > "$P/cpfind.log" 2>&1
# The pre-fit prune is the standard `cpclean` (both steps). A pairwise-only
# variant keeps the corner points but the fit on them is DEGENERATE — measured,
# registry. See the CP PRUNING note below.
cpclean -o clean.pto cps.pto > "$P/cpclean.log" 2>&1
pto_var --opt y,p,r -o s1.pto clean.pto > /dev/null
autooptimiser -n -o pos.pto s1.pto > /dev/null 2>&1
pto_var --opt y,p,r,a0,b0,c0 -o s2.pto pos.pto > /dev/null
autooptimiser -n -o fit_abc.pto s2.pto > /dev/null 2>&1
# CP PRUNING. `cpclean` removes correspondences whose residual is an outlier.
# MEASURED and registered (docs/dead-ends.md): its step 2 (whole-panorama) is
# what strips the corner control points — rho_max collapses 1.76->1.24 on
# july31/set-01 — but reordering or relaxing it does NOT recover them. Pruning
# against a model that ALREADY carries a,b,c removes the same population
# (219->183, rho_max 1.77->1.65), the -n threshold saturates (n=3..8 identical),
# and keeping them produces a DEGENERATE fit (a=-1.02 b=3.03 c=-2.37). Those
# points are bad SIFT matches on aberrated corner stars. Corner support is a
# MATCHING problem; a `--prune=model-first` arm was tried and refuted.
pto_var --opt y,p,r,a0,b0,c0,d0,e0 -o s3.pto fit_abc.pto > /dev/null
autooptimiser -n -o fit_abcde.pto s3.pto > /dev/null 2>&1

WH=$(python3 -c "
import json;print('x'.join(str(v) for v in json.load(open('$REPO/datasets/'+'$(basename "$SESSION")'+'/$SET/acquisition.json'))['exif']['image_wh']))")
python3 - "$P" "$HFOV" "$FRAMES" "${OUTJSON:-$W/lens_fit.json}" "$SESSION" "$SET" "$WH" "$REPO" <<'PY'
import json, os, re, subprocess, sys
P, hfov, frames, out = sys.argv[1], float(sys.argv[2]), int(sys.argv[3]), sys.argv[4]
wh, repo = sys.argv[7], sys.argv[8]
sys.path.insert(0, os.path.join(repo, "scripts", "darktable"))
from cp_coverage import coverage
w, h = (int(x) for x in wh.lower().split("x"))

def cps(p):
    return sum(1 for l in open(f"{P}/st/{p}") if l.startswith("c "))

def params(p):
    i = next(l for l in open(f"{P}/st/{p}") if l.startswith("i "))
    return {k: float(m) for k, m in re.findall(r" ([abcde])(-?[0-9.]+)", i)}

def resid(p):
    r = subprocess.run(["checkpto", f"{P}/st/{p}"], capture_output=True, text=True).stdout
    m = re.search(r"Mean error\s*:\s*([0-9.]+).*?Maximum\s*:\s*([0-9.]+)", r, re.S)
    return {"mean_px": float(m.group(1)), "max_px": float(m.group(2))} if m else None

abc = params("fit_abc.pto")
de = params("fit_abcde.pto")
rec = {"tool": "hugin-tools cpfind --fullscale / cpclean / staged autooptimiser on "
               "Siril-autostretched calibrated frames; hfov pinned at the solved value",
       "hfov_deg_pinned": hfov, "frames": frames,
       "control_points": {"raw": cps("cps.pto"), "after_cpclean": cps("clean.pto")},
       "residual_rotation_only": resid("pos.pto"), "residual_with_abc": resid("fit_abc.pto"),
       "fitted_ptlens": {"a": abc["a"], "b": abc["b"], "c": abc["c"]},
       "centre_shift_informational_px": {"d": de.get("d"), "e": de.get("e"),
           "note": "reported only — carrying it needs lensfun's undocumented <center> element"},
       # The number that says whether the CORNER was fitted or extrapolated. A
       # fit's own residual cannot say: it is computed only where the control
       # points are, and 0.02-0.10 px residuals accompanied 2.99 px of corner
       # disagreement in the product (ledger `fit_corner_support_census`).
       "control_point_coverage": coverage(f"{P}/st/fit_abc.pto", w, h),
       "status": "CANDIDATE — a fresh fit is not a shipped model. The AUTHORITY is "
                 "scripts/darktable/lens_models.json, keyed <lens>@<focal>, because a "
                 "model is a property of the LENS AND OPTICAL STATE, not of a dataset. "
                 "Promoting a candidate is an explicit act, judged at the COMBINE "
                 "(scripts/qa/member_separation.py on a real cross-set compose) and on "
                 "the owner's eyes — never on this fit's own residual, and never on a "
                 "per-set product, where a compose artifact masquerades as optics "
                 "(docs/dead-ends.md).",
       "accepted_by": null}
json.dump(rec, open(out, "w"), indent=1)
cov = rec["control_point_coverage"] or {}
print(json.dumps(rec["fitted_ptlens"]))
print(f"CP coverage: n={cov.get('n')} p99={cov.get('rho_p99')} max={cov.get('rho_max')} "
      f"beyond1.5={100*(cov.get('frac_beyond_1_50') or 0):.1f}% -> corner support "
      f"{str(cov.get('corner_support')).upper()}")
for f in cov.get("criterion_fails") or []:
    print(f"  criterion FAIL: {f}")
print(f"record: {out}")
print(f"install: scripts/darktable/install_lens_model.sh {sys.argv[5]} {sys.argv[6]}")
print("  (it reads the lens, the focal and these coefficients from the set's own records)")
PY
# keep the ptos/logs (tiny, gitignored qa_work scratch — the fit's audit
# trail; blanket cleanup ate the diagnostics of three failed runs); drop only
# the bulky detection TIFFs
rm -f "$P"/st/*.tif
