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
#                             [--frames=N] [--chunk=12] [--out=<stack.fit>]
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
#   count leaving a remainder of exactly 1 aborts HERE, not hours in.
# - disk: registration keeps the warped input set resident while seqapplyreg
#   writes the registered set beside it (~231 MB/frame peak, uncompressed —
#   `setcompress` quantisation is silently lossy on float, so nothing here is
#   compressed). Aborts up front if the selected frame count cannot fit;
#   --frames=N selects an EVEN STRIDE over the whole set, which preserves the
#   TIME SPAN (what the registration geometry depends on) and trades only depth.
#
# PROVISIONAL AS-WRITTEN: this script was assembled from the chain that shipped
# the approved render (identical stages), but the artifact itself has not yet
# run end to end — its first as-written run is the x86 set-01 full-depth job.
#
# The stack is `rej 3 3 -norm=addscale` — the chain the approved render pinned.
# --icc-type SRGB is MATCHED to the sRGB-TRC tag Siril's savetif embeds
# (verified identity round trip; forcing a linear tag leaves the decode
# uncancelled and silently destroys photometry).
set -euo pipefail
REPO=$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)
SESSION=${1:?usage: run_undistort_pipeline.sh <session-dir> <set> --dark= --flat= [--frames=N] [--chunk=12] [--out=]}
SET=${2:?missing <set>}
DARK= FLAT= FRAMES=0 CHUNK=12 OUT=
for a in "${@:3}"; do case "$a" in
  --dark=*) DARK=${a#*=};; --flat=*) FLAT=${a#*=};; --frames=*) FRAMES=${a#*=};;
  --chunk=*) CHUNK=${a#*=};; --out=*) OUT=${a#*=};;
  *) echo "unknown arg $a" >&2; exit 1;;
esac; done
[ -n "$DARK" ] && [ -n "$FLAT" ] || { echo "need --dark= --flat= (matched masters)" >&2; exit 1; }
SESSION=$(cd "$SESSION" && pwd)
OUT=${OUT:-$SESSION/results/stack_$SET}
OUT=${OUT%.fit}
mkdir -p "$(dirname "$OUT")" "$SESSION/work"
P=$SESSION/work/undistort_$SET
CFG=$SESSION/work/dtcfg
sir(){ flatpak run --command=siril-cli org.siril.Siril -d "$P" -s "$1" >> "$P/siril.log" 2>&1; }

python3 "$REPO/scripts/stack/lens_preflight.py" "$SESSION" "$SET" --require-profile
"$REPO/scripts/darktable/install_styles.sh" "$CFG"

mapfile -t SRC < <(find "$SESSION/$SET" -maxdepth 1 -type f \
  \( -iname '*.nef' -o -iname '*.dng' -o -iname '*.cr2' -o -iname '*.cr3' \
     -o -iname '*.arw' -o -iname '*.raf' \) | sort)
[ ${#SRC[@]} -ge 2 ] || { echo "no raw frames under $SESSION/$SET" >&2; exit 1; }
# The ratified per-set cull: recipe.json stack.exclude lists frame numbers that
# never enter the stack (the decision + reasons live in the recipe's why block).
RECIPE=$REPO/datasets/$(basename "$SESSION")/$SET/recipe.json
mapfile -t SRC < <(python3 - "$RECIPE" "${SRC[@]}" <<'PY'
import json, os, re, sys
recipe, frames = sys.argv[1], sys.argv[2:]
excl = set()
if os.path.exists(recipe):
    excl = {int(n) for n in (json.load(open(recipe)).get("stack") or {}).get("exclude") or []}
kept = [f for f in frames
        if not (m := re.search(r"(\d+)\D*$", os.path.basename(f))) or int(m.group(1)) not in excl]
for f in kept: print(f)
d = len(frames) - len(kept)
print(f"cull: recipe excludes {d} frame(s); {len(kept)} eligible" if d
      else f"cull: no recipe exclusions; {len(kept)} eligible", file=sys.stderr)
PY
)
[ "$FRAMES" -gt 0 ] || FRAMES=${#SRC[@]}
[ $((FRAMES % CHUNK)) -ne 1 ] || { echo "ABORT: $FRAMES frames leave a final chunk of 1 (Siril cannot sequence one frame) — adjust --frames/--chunk" >&2; exit 1; }
NEED_GB=$((FRAMES * 231 / 1024 + 3))
FREE_GB=$(df -BG --output=avail "$SESSION" | tail -1 | tr -dc 0-9)
[ "$FREE_GB" -ge "$NEED_GB" ] || { echo "ABORT: ~${NEED_GB}G peak needed for $FRAMES frames, ${FREE_GB}G free — pass a smaller --frames (even stride keeps the full time span)" >&2; exit 1; }

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
  printf 'requires 1.2.0\nset16bits\nsetcompress 0\ncd %s\nconvert c -out=%s\ncd %s\ncalibrate c -dark=%s -flat=%s -cfa -equalize_cfa -debayer -prefix=pp_\n' \
    "$P/nef" "$P/proc" "$P/proc" "$DARK" "$FLAT" > "$P/c.ssf"
  sir "$P/c.ssf"
  rm -f "$P/proc"/c_*.fit "$P/proc"/c_.seq
  for f in "$P/proc"/pp_c_*.fit; do
    b=$(basename "$f" .fit)
    printf 'requires 1.2.0\nset16bits\nsetcompress 0\nload %s\nsavetif %s\n' "$f" "$P/tif/$b" > "$P/e.ssf"
    sir "$P/e.ssf"; rm -f "$f"
  done
  rm -f "$P/proc"/*.seq
  j=0
  for t in "$P/tif"/*.tif; do
    j=$((j+1))
    exiftool -q -overwrite_original -TagsFromFile "${SRC[0]}" -Make -Model -LensModel -FocalLength -FNumber "$t" 2>/dev/null || true
    timeout 900 darktable-cli "$t" "$P/tif/w_$(printf %02d $ci)_$(printf %02d $j).tif" \
      --style lensdist --style-overwrite --icc-type SRGB --core \
      --configdir "$CFG" --library ":memory:" \
      --conf plugins/imageio/format/tiff/bpp=16 >/dev/null 2>&1 \
      || { echo "WARP FAILED $b" >&2; exit 1; }
    rm -f "$t"
  done
  printf 'requires 1.2.0\nset16bits\nsetcompress 0\ncd %s\nconvert k%02d -out=%s\n' "$P/tif" "$ci" "$P/out" > "$P/v.ssf"
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
printf 'requires 1.2.0\nset16bits\nsetcompress 0\ncd %s\nregister lt -2pass\nseqapplyreg lt -framing=min -prefix=r_\nstack r_lt rej 3 3 -norm=addscale -output_norm -out=%s\n' \
  "$P/out" "$OUT" > "$P/s.ssf"
sir "$P/s.ssf"
rm -rf "$P/out"
echo "=== DONE: $OUT.fit ==="
ls -la "$OUT.fit"
df -h "$SESSION" | tail -1
