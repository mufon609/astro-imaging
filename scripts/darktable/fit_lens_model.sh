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
# Output: fitted a,b,c (panotools convention — lensfun `model="ptlens"`
# consumes them directly) printed with the matching install command, and the
# fit record at datasets/<session>/<set>/qa_work/lens_fit.json. The fit is
# accepted only by the downstream measures on a real stack (star_stations +
# seqtilt A/B against the incumbent model), never by its own residual.
set -euo pipefail
REPO=$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)
SESSION=${1:?usage: fit_lens_model.sh <session-dir> <set> --dark= --flat= --hfov= [--frames=12]}
SET=${2:?missing <set>}
DARK= FLAT= HFOV= FRAMES=12
for a in "${@:3}"; do case "$a" in
  --dark=*) DARK=${a#*=};; --flat=*) FLAT=${a#*=};;
  --hfov=*) HFOV=${a#*=};; --frames=*) FRAMES=${a#*=};;
  *) echo "unknown arg $a" >&2; exit 1;;
esac; done
[ -n "$DARK" ] && [ -n "$FLAT" ] && [ -n "$HFOV" ] || { echo "need --dark= --flat= --hfov=" >&2; exit 1; }

W=$REPO/datasets/$(basename "$SESSION")/$SET/qa_work
P=$W/lens_fit_work
sir(){ flatpak run --command=siril-cli org.siril.Siril -d "$P" -s "$1" >> "$P/siril.log" 2>&1; }

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
printf 'requires 1.2.0\nset16bits\nsetcompress 0\ncd %s\nconvert c -out=%s\ncd %s\ncalibrate c -dark=%s -flat=%s -cfa -equalize_cfa -debayer -prefix=pp_\n' \
  "$P/nef" "$P/proc" "$P/proc" "$DARK" "$FLAT" > "$P/c.ssf"
sir "$P/c.ssf"
i=0
for f in "$P/proc"/pp_c_*.fit; do
  i=$((i+1))
  printf 'requires 1.2.0\nsetcompress 0\nload %s\nautostretch\nsavetif8 %s\n' \
    "$f" "$P/st/st_$(printf %02d $i)" > "$P/e.ssf"
  sir "$P/e.ssf"; rm -f "$f"
done
rm -rf "$P/nef" "$P/proc"
echo "fit_lens_model: $i stretched frames for correspondence detection"

cd "$P/st"
pto_gen -p 0 -f "$HFOV" -o gen.pto st_*.tif > /dev/null
cpfind --fullscale -o cps.pto gen.pto > "$P/cpfind.log" 2>&1
cpclean -o clean.pto cps.pto > "$P/cpclean.log" 2>&1
pto_var --opt y,p,r -o s1.pto clean.pto > /dev/null
autooptimiser -n -o pos.pto s1.pto > /dev/null 2>&1
pto_var --opt y,p,r,a0,b0,c0 -o s2.pto pos.pto > /dev/null
autooptimiser -n -o fit_abc.pto s2.pto > /dev/null 2>&1
pto_var --opt y,p,r,a0,b0,c0,d0,e0 -o s3.pto fit_abc.pto > /dev/null
autooptimiser -n -o fit_abcde.pto s3.pto > /dev/null 2>&1

python3 - "$P" "$HFOV" "$FRAMES" "$W/lens_fit.json" <<'PY'
import json, re, subprocess, sys
P, hfov, frames, out = sys.argv[1], float(sys.argv[2]), int(sys.argv[3]), sys.argv[4]

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
       "accepted_by": "star_stations + seqtilt A/B on a real stack, never this fit's own residual"}
json.dump(rec, open(out, "w"), indent=1)
print(json.dumps(rec["fitted_ptlens"]))
print(f"record: {out}")
print(f"install: scripts/darktable/install_lens_model.sh {abc['a']:.8g} {abc['b']:.8g} {abc['c']:.8g}")
PY
rm -rf "$P"
