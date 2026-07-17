#!/usr/bin/env bash
# Full-depth stack builder for the wide-field UNTRACKED class on a disk too
# small for single-pass registration: consecutive GROUPS of frames are each
# run through the full undistort chain (calibrate -> warp -> register -> rej
# stack) with their intermediates deleted before the next group, then the
# group sub-stacks are registered and rejection-stacked into the final.
#
#   run_undistort_groups.sh <session-dir> <set> --dark=<master> --flat=<master> \
#                           [--group=15] [--chunk=12] [--out=<stack.fit>] [--plan] \
#                           [--framing=min|max]
#
# --framing applies to the FINAL compose only (per-group registration always
# uses min — a consecutive block's ~1% trim). min (default) keeps the area
# common to every sub-stack: full depth at every pixel, uniform SNR. max keeps
# the union: a canvas larger than the sensor frame whose edges are covered by
# fewer sub-stacks — depth, rejection strength and SNR fall off toward the
# union boundary. Re-invoking with all sub-stacks present re-runs just the
# compose, so both framings can be produced from one set of groups.
#
# WHY THIS IS VALID (and when it was not): after the lens-distortion warp,
# every frame-to-frame map is a pure homography and homographies COMPOSE — a
# sub-stack registered to the final reference carries no model error. Before
# the undistort stage this exact composition was a measured dead end (the
# residual distortion error re-entered at the group-to-group registration and
# turned a smooth smear into discrete ghosts). Do NOT use this builder on
# un-warped frames.
#
# DECLARED COSTS vs the single-pass builder (run_undistort_pipeline.sh):
# - one extra interpolation pass (each pixel is resampled twice: frame->group
#   reference, group->final reference) — a small softening, judged on finals;
# - rejection runs within groups (satellites reject there, at full strength)
#   and then across the K sub-stacks (3-sigma over K samples — weaker, but the
#   per-group pass has already cleaned the transients);
# - groups are CONSECUTIVE blocks, sized as equally as possible, so each
#   sub-stack is an equal-weight mean and the final mean equals the global
#   mean; per-group -framing=min trims only that group's small drift, and the
#   final -framing=min lands on the same global intersection as single-pass.
#
# REMOVAL CONDITION: free disk >= the single-pass peak (~231 MB/frame; the
# x86 1 TB target) — then use run_undistort_pipeline.sh and delete this route.
#
# GUARDS: balanced group sizes (never a 1-frame group; per-group chunk
# remainder-of-1 asserted by the pipeline it calls); disk re-checked before
# EVERY group (sub-stacks accumulate); >=2 groups or it tells you to use the
# single-pass builder.
#
# NOTHING in the chain is compressed — the pipeline-wide rule; every
# generated .ssf pins `setcompress 0`. Sub-stacks accumulate uncompressed
# (~145 MB each), which the disk guard accounts for.
set -euo pipefail
REPO=$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)
SESSION=${1:?usage: run_undistort_groups.sh <session-dir> <set> --dark= --flat= [--group=15] [--chunk=12] [--out=] [--plan]}
SET=${2:?missing <set>}
DARK= FLAT= GROUP=15 CHUNK=12 OUT= PLAN=0 FRAMING=min
for a in "${@:3}"; do case "$a" in
  --dark=*) DARK=${a#*=};; --flat=*) FLAT=${a#*=};; --group=*) GROUP=${a#*=};;
  --chunk=*) CHUNK=${a#*=};; --out=*) OUT=${a#*=};; --plan) PLAN=1;;
  --framing=*) FRAMING=${a#*=};;
  *) echo "unknown arg $a" >&2; exit 1;;
esac; done
case "$FRAMING" in min|max) ;; *) echo "--framing must be min or max" >&2; exit 1;; esac
[ -n "$DARK" ] && [ -n "$FLAT" ] || { echo "need --dark= --flat= (matched masters)" >&2; exit 1; }
SESSION=$(cd "$SESSION" && pwd)
OUT=${OUT:-$SESSION/results/stack_${SET}_full}
OUT=${OUT%.fit}
G=$SESSION/work/groups_$SET
mkdir -p "$G" "$(dirname "$OUT")"
sir(){ flatpak run --command=siril-cli org.siril.Siril -d "$1" -s "$2" >> "$G/siril_final.log" 2>&1; }

mapfile -t SRC < <(find "$SESSION/$SET" -maxdepth 1 -type f \
  \( -iname '*.nef' -o -iname '*.dng' -o -iname '*.cr2' -o -iname '*.cr3' \
     -o -iname '*.arw' -o -iname '*.raf' \) | sort)
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
print(f"cull: recipe excludes {len(frames)-len(kept)} frame(s); {len(kept)} eligible", file=sys.stderr)
PY
)
N=${#SRC[@]}
K=$(( (N + GROUP - 1) / GROUP ))
[ "$K" -ge 2 ] || { echo "only one group at --group=$GROUP for $N frames — use run_undistort_pipeline.sh" >&2; exit 1; }
BASE=$((N / K)); REM=$((N % K))     # REM groups of BASE+1, K-REM of BASE
[ "$BASE" -ge 2 ] || { echo "ABORT: groups of $BASE frame(s) — raise --group" >&2; exit 1; }
MAXG=$BASE; [ "$REM" -eq 0 ] || MAXG=$((BASE + 1))
# per-group transient ~290 MB/frame (full-frame warped + near-full registered:
# a consecutive block drifts only ~60 px, so -framing=min barely crops);
# sub-stacks accumulate uncompressed at ~145 MB each; the final phase holds
# them beside their registered copies (~85 MB each)
NEED_GB=$(( MAXG * 290 / 1024 + (K * 145) / 1024 + 2 ))
FINAL_GB=$(( K * 230 / 1024 + 2 ))
[ "$FINAL_GB" -gt "$NEED_GB" ] && NEED_GB=$FINAL_GB
echo "plan: $N frames -> $K groups ($REM x $((BASE+1)) + $((K-REM)) x $BASE), peak ~${NEED_GB}G"
[ "$PLAN" -eq 0 ] || exit 0

i=0
for ((g=1; g<=K; g++)); do
  size=$BASE; [ "$g" -le "$REM" ] && size=$((BASE + 1))
  SUB=$G/sub_$(printf %02d "$g")
  if [ -f "$SUB.fit" ]; then
    echo "=== group $g/$K: $SUB.fit exists, skipping (resume) ==="; i=$((i + size)); continue
  fi
  FREE_GB=$(df -BG --output=avail "$SESSION" | tail -1 | tr -dc 0-9)
  GNEED=$(( size * 290 / 1024 + 1 ))
  [ "$FREE_GB" -ge "$GNEED" ] || { echo "ABORT before group $g: ~${GNEED}G needed, ${FREE_GB}G free" >&2; exit 1; }
  : > "$G/g$g.list"
  for ((k=0; k<size; k++, i++)); do printf '%s\n' "${SRC[$i]}" >> "$G/g$g.list"; done
  echo "=== group $g/$K: $(wc -l < "$G/g$g.list") frames ==="
  "$REPO/scripts/stack/run_undistort_pipeline.sh" "$SESSION" "$SET" \
    --dark="$DARK" --flat="$FLAT" --select="$G/g$g.list" --chunk="$CHUNK" --out="$SUB.fit"
  [ -f "$SUB.fit" ] || { echo "ABORT: group $g produced no sub-stack" >&2; exit 1; }
done

echo "=== final: register + stack $K sub-stacks ==="
rm -rf "$G/final" "$G/finalseq"; mkdir -p "$G/final" "$G/finalseq"
for f in "$G"/sub_*.fit; do ln -sf "$f" "$G/final/$(basename "$f")"; done
printf 'requires 1.2.0\nset16bits\nsetcompress 0\ncd %s\nlink s -out=%s\ncd %s\nregister s -2pass\nseqapplyreg s -framing=%s -prefix=r_\nstack r_s rej 3 3 -norm=addscale -output_norm -out=%s\n' \
  "$G/final" "$G/finalseq" "$G/finalseq" "$FRAMING" "$OUT" > "$G/final.ssf"
sir "$SESSION" "$G/final.ssf"
[ -f "$OUT.fit" ] || { echo "FINAL STACK MISSING — read $G/siril_final.log" >&2; exit 1; }
rm -rf "$G/final" "$G/finalseq"
echo "=== DONE: $OUT.fit (sub-stacks kept in $G for re-composition) ==="
ls -la "$OUT.fit"
df -h "$SESSION" | tail -1
