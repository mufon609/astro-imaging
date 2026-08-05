#!/usr/bin/env bash
# Stack builder for the wide-field UNTRACKED class: calibrate -> UNDISTORT ->
# register -> stack. A far-drifting set cannot be registered by one homography
# (the real frame-to-frame map is distort . H . distort^-1), so the lens
# distortion is removed BEFORE registration by darktable + the lensfun model
# this rig carries (community DB entry, or the entry fitted from the set's own
# frames via scripts/darktable/fit_lens_model.sh + install_lens_model.sh where
# the community profile is inadequate — docs/wide-field-untracked-registration.md).
#
#   run_undistort_pipeline.sh <session-dir> <set> --dark=<master> --flat=<master> \
#                             [--frames=N | --select=<list-file>] [--chunk=12] [--out=<stack.fit>]
#
# --select=<file> (one raw path per line) processes exactly those frames in
# order — the group-composition driver (run_undistort_groups.sh) uses it to
# feed consecutive blocks; mutually exclusive with --frames.
#
# Ordering is load-bearing: darks/flats are sensor-grid properties, so
# calibration finishes in SENSOR space, debayer follows (a CFA mosaic cannot be
# interpolated), and only then the geometric warp.
#
# GUARDS, in order:
# - scripts/stack/lens_preflight.py --require-profile: STOPS on a mixed-optics
#   set and makes darktable PROVE it corrects this set — darktable applies NO
#   correction to a lens lensfun cannot match, silently (exit 0, empty log).
# - chunk remainder: Siril cannot build a sequence from ONE frame, so a frame
#   count leaving a remainder of exactly 1 auto-shrinks the chunk by one and
#   states it (chunk size only bounds working-set residency, so it is free) —
#   the same recovery run_frame_qa.sh makes for its batches.
# - disk: registration keeps the warped input set resident while seqapplyreg
#   writes the registered set beside it, so the peak is the SUM of two frames.
#   `undistort_peak_gib` (scripts/stack/disk_budget.sh) DERIVES it from this
#   set's own frame geometry — W x H x channels x 4 bytes x 2 — rather than a
#   per-camera constant, and is SHARED with run_set_chain.sh's routing decision
#   (the two were separate constants once and diverged by 2x). NOTHING in the pipeline is
#   compressed, the pipeline-wide rule; every .ssf pins `setcompress 0`. Aborts
#   up front if the selected frame count cannot fit; --frames=N selects an EVEN
#   STRIDE over the whole set, which preserves the TIME SPAN (what the
#   registration geometry depends on) and trades depth.
#
# BIT DEPTH: 32-bit float end-to-end (set32bits + savetif32 + darktable
# bpp=32). The 16-bit intermediates were an arm-rig RAM/disk adaptation whose
# removal condition fired on the x86 rig — and 16-bit integer quantization was
# a MEASURED defect: a stack's ultra-tight channel histogram quantized to
# MAD=0, degenerating Siril's autostretch statistics (docs/dead-ends.md).
#
#
# The stack rejection is doctrine-selected by sub count (stack_rejection.sh:
# percentile / winsorized / GESD — a deep stack gets GESD), with
# `-norm=addscale -output_norm`.
# ICC on the FLOAT leg: the TIFF ships UNTAGGED (exiftool strips the profile
# in the same pass that copies the lens EXIF) and darktable exports
# --icc-type LIN_REC709 — measured a PERFECT identity round trip (ratio
# 1.0000 at every level, every channel) with the warp confirmed firing
# (corner 0.22 vs centre 0.003). The former SRGB/SRGB tag-matching contract
# (the 16-bit-era rule) carries a TRC toe-segment mismatch that inflates
# 3s-class sky levels +2..5% below linear ~0.003 (the ICC-toe probe;
# docs/dead-ends.md ICC entry). NEVER use siril `icc_remove` for the strip —
# measured applying a global ~1/12.92 scale through the same leg.
set -euo pipefail
REPO=$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)
source "$REPO/scripts/stack/calibrate_light.sh"   # shared light-calibration command (mandatory -cc=dark)
source "$REPO/scripts/stack/stack_rejection.sh"   # shared integration rejection (doctrine-driven by sub count)
source "$REPO/scripts/stack/disk_budget.sh"       # per-set disk peak — shared with the ROUTER, or they drift
SESSION=${1:?usage: run_undistort_pipeline.sh <session-dir> <set> --dark= --flat= [--frames=N] [--chunk=12] [--out=] [--desky]}
SET=${2:?missing <set>}
DARK= FLAT= FRAMES=0 CHUNK=12 OUT= SELECT= DESKY=0
for a in "${@:3}"; do case "$a" in
  --dark=*) DARK=${a#*=};; --flat=*) FLAT=${a#*=};; --frames=*) FRAMES=${a#*=};;
  --chunk=*) CHUNK=${a#*=};; --out=*) OUT=${a#*=};; --select=*) SELECT=${a#*=};;
  --desky) DESKY=1;;
  *) echo "unknown arg $a" >&2; exit 1;;
esac; done
# !! REVERTED 2026-08-04 — `--desky` IS OFF BY DEFAULT AND IS A KNOWN REGRESSION.
# It shipped ON 2026-07-29 (f170540) and cost 31x in background flatness: july31/
# set-01 measured corner spread 12.4% with it against 0.4% without, one knob, 500
# frames, everything else identical. CAUSE: `seqsubsky` is a BACKGROUND EXTRACTION
# operator, defined on a FLAT-FIELDED image, and this ran it on RAW frames still
# carrying vignetting — the frame is sky x V, not sky. The additive plane overshoots
# where V curves hardest (the frame edge) and INVERTS the asymmetry there: raw light
# +0.426, --desky flat -0.550, so dividing by it doubles the error. The analysis
# below is preserved because its PROBLEM STATEMENT is still correct — a sky flat does
# bake in the horizon-fixed gradient and does tilt the object (3.11% at 241 sigma).
# Its PROPOSED FIX is not. Full record: docs/dead-ends.md + datasets/july31/set-01/
# qa_work/desky_regression.json.
#
# --desky: per-frame `subsky 1` on each CALIBRATED light, in sensor space,
# before the geometric warp. It is the mandatory COMPANION to a de-skied flat
# (build_sky_flat --desky), not an independent option:
#   contaminated flat  ~ S.V   ->  calibration gives (S+O)V / S.V = 1 + O/S
#                                  i.e. sky flat, but the OBJECT divided by S
#   de-skied flat      ~ V     ->  calibration gives S + O
#                                  i.e. object CORRECT, sky gradient retained
# So the flat fix moves the sky term out of a multiplicative correction, and
# this removes it additively, which is the domain it actually lives in. Neither
# half substitutes for the other: a background step alone cannot undo a
# multiplicative tilt already applied at calibration, and a de-skied flat alone
# leaves the gradient in the render.
# Degree 1 because the MW band IS frame-scale curvature at this focal length and
# degree >= 2 erases it; per-frame rather than stack-level because stack-level-
# only leaves a structured residual with visible rings (both in the registry).
# Runs on DEBAYERED frames here, so no CFA caveat applies.
# `-nodither` is REQUIRED: `seqsubsky` dithers by DEFAULT (unlike `subsky`, where
# -dither is opt-IN) and the dither is UNSEEDED, so without it every calibrated
# light is irreproducible run to run. MEASURED (Siril isub+stat, two frames, four
# runs): identical calibrated input, yet two default runs differ by sigma 0.4 ADU
# (+-1.0) where two -nodither runs are bit-identical. The dither breaks
# quantization terracing, which cannot occur here — the frames' own bgnoise is
# 17.7 ADU against the 0.5 ADU step, 35x. Rationale + numbers: build_sky_flat.sh.
DESKYCMD= LPREFIX=pp_
if [ "$DESKY" = 1 ]; then
  DESKYCMD='seqsubsky pp_c 1 -nodither\n'; LPREFIX=bkg_pp_
fi
[ -z "$SELECT" ] || [ "$FRAMES" -eq 0 ] || { echo "--select and --frames are mutually exclusive" >&2; exit 1; }
[ -n "$DARK" ] && [ -n "$FLAT" ] || { echo "need --dark= --flat= (matched masters)" >&2; exit 1; }
# Absolutize the masters too: they are embedded into the calibrate .ssf, and
# the flatpak Siril resolves them from the SCRIPT's CWD (work/undistort_*),
# so a caller-relative path fails with "…[any_allowed_extension] not found".
[ -f "$DARK" ] || { echo "no such dark: $DARK" >&2; exit 1; }
[ -f "$FLAT" ] || { echo "no such flat: $FLAT" >&2; exit 1; }
DARK="$(cd "$(dirname "$DARK")" && pwd)/$(basename "$DARK")"
FLAT="$(cd "$(dirname "$FLAT")" && pwd)/$(basename "$FLAT")"
SESSION=$(cd "$SESSION" && pwd)
OUT=${OUT:-$REPO/web/results/$(basename "$SESSION")/stack_$SET}
OUT=${OUT%.fit}
mkdir -p "$(dirname "$OUT")" "$SESSION/work"
# Absolutize: the flatpak Siril sandbox resolves the .ssf's -out= from the
# script's own CWD, so a relative --out lands the final INSIDE the work tree
# and the existence check fails on a stack that actually built.
OUT="$(cd "$(dirname "$OUT")" && pwd)/$(basename "$OUT")"
P=$SESSION/work/undistort_$SET
CFG=$SESSION/work/dtcfg
sir(){ flatpak run --command=siril-cli org.siril.Siril -d "$P" -s "$1" >> "$P/siril.log" 2>&1; }

LPJ=$REPO/datasets/$(basename "$SESSION")/$SET/qa_work/lens_preflight.json
mkdir -p "$(dirname "$LPJ")"
python3 "$REPO/scripts/stack/lens_preflight.py" "$SESSION" "$SET" --require-profile --json="$LPJ"
"$REPO/scripts/darktable/install_styles.sh" "$CFG"

mapfile -t SRC < <(find "$SESSION/$SET" -maxdepth 1 -type f \
  \( -iname '*.nef' -o -iname '*.dng' -o -iname '*.cr2' -o -iname '*.cr3' \
     -o -iname '*.arw' -o -iname '*.raf' \) | sort)
[ ${#SRC[@]} -ge 2 ] || { echo "no raw frames under $SESSION/$SET" >&2; exit 1; }
# The ratified per-set cull: recipe.json stack.exclude names frames by their
# trailing FILENAME digits — resolved by the single-source cullspec (loud
# ABORT on an exclude that matches zero or several frames; a cull must never
# silently no-op — a measured trap).
RECIPE=$REPO/datasets/$(basename "$SESSION")/$SET/recipe.json
mapfile -t SRC < <(python3 "$REPO/scripts/lib/cullspec.py" keep "$RECIPE" "${SRC[@]}")
[ ${#SRC[@]} -ge 1 ] || { echo "ABORT: cull resolution failed or left no frames (see cullspec message above)" >&2; exit 1; }
if [ -n "$SELECT" ]; then
  mapfile -t SRC < <(grep -v '^\s*$' "$SELECT")
  for f in "${SRC[@]}"; do [ -f "$f" ] || { echo "ABORT: --select names missing frame $f" >&2; exit 1; }; done
  FRAMES=${#SRC[@]}
fi
[ "$FRAMES" -gt 0 ] || FRAMES=${#SRC[@]}
# A final chunk of exactly ONE frame cannot be sequenced by Siril. Shrink the
# chunk until the remainder is not 1, and say so — aborting here instead was a
# dead end on the one-click chain, which calls this builder WITHOUT a --chunk and
# so had no way to satisfy a demand to "adjust --chunk": any set whose frame count
# was 1 mod 12 simply could not be built from the session button. Chunk size only
# bounds working-set residency, so shrinking it is free.
# It must LOOP. A single decrement can land on a remainder of 1 again, because
# FRAMES = q*CHUNK + 1 gives FRAMES mod (CHUNK-1) = (q+1) mod (CHUNK-1), which is
# 1 whenever q is a multiple of CHUNK-1 — i.e. at the default CHUNK=12 for every
# FRAMES = 132k+1: 133, 265, 397. Those are ordinary set sizes here (july23's sets
# run 399-401), and the single-decrement version failed at the LAST chunk, hours
# in, after warping every earlier frame — strictly worse than the up-front abort
# it replaced. Floor of 2 because a chunk of 1 is the thing being avoided.
if [ $((FRAMES % CHUNK)) -eq 1 ]; then
  ORIGCHUNK=$CHUNK
  while [ "$CHUNK" -gt 2 ] && [ $((FRAMES % CHUNK)) -eq 1 ]; do CHUNK=$((CHUNK - 1)); done
  [ $((FRAMES % CHUNK)) -ne 1 ] || { echo "ABORT: $FRAMES frames leave a final chunk of 1 at every chunk size down to 2 — pass --frames to change the count" >&2; exit 1; }
  echo "chunk shrunk $ORIGCHUNK -> $CHUNK ($FRAMES frames leave a final chunk of 1 at $ORIGCHUNK, which cannot be sequenced; remainder is now $((FRAMES % CHUNK)))"
fi
PEAK_MIB=$(undistort_singlepass_peak_mib "$SESSION" "$SET") \
  || { echo "ABORT: cannot size the disk budget for $SET — see above" >&2; exit 1; }
NEED_GB=$(undistort_peak_gib "$SESSION" "$SET" "$FRAMES")
FREE_GB=$(df -BG --output=avail "$SESSION" | tail -1 | tr -dc 0-9)
[ "$FREE_GB" -ge "$NEED_GB" ] || { echo "ABORT: ~${NEED_GB}G peak needed for $FRAMES frames (${PEAK_MIB} MiB/frame, derived from this set's own frame geometry — disk_budget.sh), ${FREE_GB}G free — pass a smaller --frames (even stride keeps the full time span), or use run_undistort_groups.sh for full depth" >&2; exit 1; }

rm -rf "$P"; mkdir -p "$P/out"
mapfile -t ALL < <(python3 -c "
import sys
src = sys.argv[1:]; n = $FRAMES
for i in range(n): print(src[round(i*(len(src)-1)/(n-1))] if n > 1 else src[0])
" "${SRC[@]}")
echo "selected ${#ALL[@]} of ${#SRC[@]} lights (even stride over the full window)"

n=0; ci=0
while [ $n -lt ${#ALL[@]} ]; do
  ci=$((ci+1))
  rm -rf "$P/nef" "$P/proc" "$P/tif"; mkdir -p "$P/nef" "$P/proc" "$P/tif"
  for ((k=0; k<CHUNK && n<${#ALL[@]}; k++, n++)); do
    ln -sf "${ALL[$n]}" "$P/nef/$(basename "${ALL[$n]}")"
  done
  CAL=$(calibrate_light_cmd c "$DARK" -flat="$FLAT" -equalize_cfa -cfa -debayer -prefix=pp_)
  printf 'requires 1.2.0\nset32bits\nsetcompress 0\ncd %s\nconvert c -out=%s\ncd %s\n%s\n%b' \
    "$P/nef" "$P/proc" "$P/proc" "$CAL" "$DESKYCMD" > "$P/c.ssf"
  sir "$P/c.ssf"
  rm -f "$P/proc"/c_*.fit "$P/proc"/c_.seq
  for f in "$P/proc"/${LPREFIX}c_*.fit; do
    b=$(basename "$f" .fit)
    printf 'requires 1.2.0\nset32bits\nsetcompress 0\nload %s\nsavetif32 %s\n' "$f" "$P/tif/$b" > "$P/e.ssf"
    sir "$P/e.ssf"; rm -f "$f"
  done
  rm -f "$P/proc"/*.seq
  j=0
  for t in "$P/tif"/*.tif; do
    j=$((j+1))
    exiftool -q -overwrite_original -TagsFromFile "${SRC[0]}" -Make -Model -LensModel -FocalLength -FNumber -icc_profile:all= "$t" 2>/dev/null || true
    timeout 900 darktable-cli "$t" "$P/tif/w_$(printf %02d $ci)_$(printf %02d $j).tif" \
      --style lensdist --style-overwrite --icc-type LIN_REC709 --core \
      --configdir "$CFG" --library ":memory:" \
      --conf plugins/imageio/format/tiff/bpp=32 \
      --conf plugins/imageio/format/tiff/compress=0 >/dev/null 2>&1 \
      || { echo "WARP FAILED $b" >&2; exit 1; }
    rm -f "$t"
  done
  printf 'requires 1.2.0\nset32bits\nsetcompress 0\ncd %s\nconvert k%02d -out=%s\n' "$P/tif" "$ci" "$P/out" > "$P/v.ssf"
  sir "$P/v.ssf"
  rm -rf "$P/tif" "$P/nef" "$P/proc"
  echo "chunk $ci: $n/${#ALL[@]}  $(df -h "$SESSION" | tail -1 | awk '{print $4" free"}')"
done

python3 - "$P/out" <<'PY'
import os, re, sys
d = sys.argv[1]
fs = sorted((int(m.group(1)), int(m.group(2)), f) for f in os.listdir(d)
            if (m := re.match(r'k(\d+)_(\d+)\.fit$', f)))
for i, (c, j, f) in enumerate(fs, 1):
    os.rename(os.path.join(d, f), os.path.join(d, f'lt_{i:05d}.fit'))
print(f"one sequence: {len(fs)} frames")
PY
rm -f "$P/out"/*.seq
REJ=$(stack_rejection_for "$FRAMES")
printf 'requires 1.2.0\nset32bits\nsetcompress 0\ncd %s\nregister lt -2pass\nseqapplyreg lt -framing=min -prefix=r_\nstack r_lt %s -norm=addscale -output_norm -out=%s\n' \
  "$P/out" "$REJ" "$OUT" > "$P/s.ssf"
sir "$P/s.ssf"
rm -rf "$P/out"
echo "=== DONE: $OUT.fit ==="
ls -la "$OUT.fit"
df -h "$SESSION" | tail -1
