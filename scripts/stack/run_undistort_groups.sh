#!/usr/bin/env bash
# Full-depth stack builder for the wide-field UNTRACKED class on a disk too
# small for single-pass registration: consecutive GROUPS of frames are each
# run through the full undistort chain (calibrate -> warp -> register -> rej
# stack) with their intermediates deleted before the next group, then the
# group sub-stacks are registered and rejection-stacked into the final.
#
#   run_undistort_groups.sh <session-dir> <set> --dark=<master> --flat=<master> \
#                           [--group=15] [--chunk=12] [--out=<stack.fit>] [--plan] \
#                           [--framing=min|max] [--desky]
#
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
# --desky is passed straight through to the per-group sub-pipeline, and it is
# MANDATORY whenever the --flat was built de-skied (build_sky_flat --desky, the
# default). The two are halves of one correction and neither substitutes for the
# other: a de-skied flat stops the calibration from dividing the object by the
# sky's own profile, and leaves the sky gradient in the frames ADDITIVELY, which
# is the domain the per-frame background step removes it in. Omitting it here
# while the flat is de-skied leaves the FULL sky gradient in the product with no
# background step anywhere in the chain — and the judge stretch amplifies a
# background gradient 9-17x (docs/dead-ends.md), so it is worse than either
# consistent choice. run_set_chain.sh passes it by default.
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
# - rejection runs ONLY within groups (satellites reject there, at full
#   strength). The final compose is a PLAIN MEAN — sub-stacks are clean
#   ~group-size means whose mutual scatter is ~sqrt(group) below per-frame
#   noise, so a sigma gate across them clips real structure instead of
#   outliers (measured: rej 3 3 across 25 sub-stacks rewrote pixels by up to
#   ~3800 ADU on a ~140 ADU sky, carving star cores and dark streaks along
#   steep gradients — docs/dead-ends.md);
# - groups are CONSECUTIVE blocks, sized as equally as possible, so each
#   sub-stack is an equal-weight mean and the final mean equals the global
#   mean; per-group -framing=min trims only that group's small drift, and the
#   final -framing=min lands on the same global intersection as single-pass.
#
# REMOVAL CONDITION: free disk >= the single-pass peak — `undistort_peak_gib` in
# scripts/stack/disk_budget.sh, which DERIVES it from the set's own frame
# geometry (the ~231 MB/frame this line used to quote was the retired 16-bit
# figure, and any fixed per-frame number is really one sensor's). It is therefore
# a PER-DATASET condition: a disk that retires this route for 24 Mpx OSC frames
# may not retire it for a 61 MP body or a much deeper set. Then use
# run_undistort_pipeline.sh for that dataset.
#
# GUARDS: balanced group sizes (never a 1-frame group); every group size is
# checked UP FRONT against --chunk for the 1-frame final chunk Siril cannot
# sequence (deferring it to the per-group sub-pipeline would let a base-size
# offender abort only at group REM+1, hours into warping); disk re-checked
# before EVERY group (sub-stacks accumulate); >=2 groups or it tells you to use
# the single-pass builder.
#
# NOTHING in the chain is compressed — the pipeline-wide rule; every
# generated .ssf pins `setcompress 0`. Sub-stacks accumulate uncompressed, which
# the disk guard accounts for by DERIVING every figure from the set's own frame
# geometry (disk_budget.sh) rather than carrying this rig's sensor as a constant.
set -euo pipefail
REPO=$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)
source "$REPO/scripts/stack/disk_budget.sh"   # per-set disk derivation, shared with
                                              # the single-pass builder and the router
SESSION=${1:?usage: run_undistort_groups.sh <session-dir> <set> --dark= --flat= [--group=15] [--chunk=12] [--out=] [--plan] [--desky]}
SET=${2:?missing <set>}
DARK= FLAT= GROUP=15 CHUNK=12 OUT= PLAN=0 FRAMING=min DESKYOPT=
for a in "${@:3}"; do case "$a" in
  --dark=*) DARK=${a#*=};; --flat=*) FLAT=${a#*=};; --group=*) GROUP=${a#*=};;
  --chunk=*) CHUNK=${a#*=};; --out=*) OUT=${a#*=};; --plan) PLAN=1;;
  --framing=*) FRAMING=${a#*=};;
  --desky) DESKYOPT=--desky;;
  *) echo "unknown arg $a" >&2; exit 1;;
esac; done
case "$FRAMING" in min|max) ;; *) echo "--framing must be min or max" >&2; exit 1;; esac
[ -n "$DARK" ] && [ -n "$FLAT" ] || { echo "need --dark= --flat= (matched masters)" >&2; exit 1; }
# Absolutize the masters (embedded into the sub-pipeline's calibrate .ssf,
# resolved from the flatpak's script CWD — a caller-relative path fails there).
[ -f "$DARK" ] || { echo "no such dark: $DARK" >&2; exit 1; }
[ -f "$FLAT" ] || { echo "no such flat: $FLAT" >&2; exit 1; }
DARK="$(cd "$(dirname "$DARK")" && pwd)/$(basename "$DARK")"
FLAT="$(cd "$(dirname "$FLAT")" && pwd)/$(basename "$FLAT")"
SESSION=$(cd "$SESSION" && pwd)
OUT=${OUT:-$REPO/web/results/$(basename "$SESSION")/stack_${SET}_full}
OUT=${OUT%.fit}
G=$SESSION/work/groups_$SET
mkdir -p "$G" "$(dirname "$OUT")"
# Absolutize: the flatpak Siril sandbox resolves the .ssf's -out= from the
# script's own CWD, so a relative --out lands the final INSIDE the work tree
# and the existence check fails on a stack that actually built.
OUT="$(cd "$(dirname "$OUT")" && pwd)/$(basename "$OUT")"
sir(){ flatpak run --command=siril-cli org.siril.Siril -d "$1" -s "$2" >> "$G/siril_final.log" 2>&1; }

mapfile -t SRC < <(find "$SESSION/$SET" -maxdepth 1 -type f \
  \( -iname '*.nef' -o -iname '*.dng' -o -iname '*.cr2' -o -iname '*.cr3' \
     -o -iname '*.arw' -o -iname '*.raf' \) | sort)
# cull via the single-source cullspec (filename-digit convention; loud ABORT
# on a never-matching or ambiguous exclude)
RECIPE=$REPO/datasets/$(basename "$SESSION")/$SET/recipe.json
mapfile -t SRC < <(python3 "$REPO/scripts/lib/cullspec.py" keep "$RECIPE" "${SRC[@]}")
[ ${#SRC[@]} -ge 1 ] || { echo "ABORT: cull resolution failed or left no frames (see cullspec message above)" >&2; exit 1; }
N=${#SRC[@]}
K=$(( (N + GROUP - 1) / GROUP ))
[ "$K" -ge 2 ] || { echo "only one group at --group=$GROUP for $N frames — use run_undistort_pipeline.sh" >&2; exit 1; }
BASE=$((N / K)); REM=$((N % K))     # REM groups of BASE+1, K-REM of BASE
[ "$BASE" -ge 2 ] || { echo "ABORT: groups of $BASE frame(s) — raise --group" >&2; exit 1; }
MAXG=$BASE; [ "$REM" -eq 0 ] || MAXG=$((BASE + 1))
# Chunk remainder-of-1 guard, UP FRONT: the per-group pipeline chunks each group
# at --chunk and Siril cannot build a sequence from a 1-frame final chunk, so a
# group size ≡1 (mod CHUNK) dies in the sub-pipeline — and for a base-size
# offender only at group REM+1, hours into warping. Assert every group size that
# will actually be used, here, before any frame is touched.
GSIZES=("$BASE"); [ "$REM" -eq 0 ] || GSIZES+=("$((BASE + 1))")
for gsize in "${GSIZES[@]}"; do
  [ $((gsize % CHUNK)) -ne 1 ] || { echo "ABORT: a group of $gsize frame(s) chunked at --chunk=$CHUNK leaves a final chunk of 1 (Siril cannot sequence one frame) — adjust --group or --chunk (plan: $N frames -> $K groups: $REM x $((BASE+1)) + $((K-REM)) x $BASE)" >&2; exit 1; }
done
# Budget DERIVED from this set's own frame geometry (disk_budget.sh), never a
# per-camera constant: the per-group phase runs the full single-pass chain over
# one group (max_group x 2 frames) while the finished sub-stacks accumulate, and
# the final phase holds all K sub-stacks beside their registered copies.
NEED_GB=$(undistort_groups_peak_gib "$SESSION" "$SET" "$MAXG" "$K") \
  || { echo "ABORT: cannot size the disk budget for $SET — see above" >&2; exit 1; }
SPPEAK_MIB=$(undistort_singlepass_peak_mib "$SESSION" "$SET")
echo "plan: $N frames -> $K groups ($REM x $((BASE+1)) + $((K-REM)) x $BASE), peak ~${NEED_GB}G${DESKYOPT:+, per-frame subsky 1 (--desky)}"
[ "$PLAN" -eq 0 ] || exit 0

i=0
for ((g=1; g<=K; g++)); do
  size=$BASE; [ "$g" -le "$REM" ] && size=$((BASE + 1))
  SUB=$G/sub_$(printf %02d "$g")
  if [ -f "$SUB.fit" ]; then
    echo "=== group $g/$K: $SUB.fit exists, skipping (resume) ==="; i=$((i + size)); continue
  fi
  FREE_GB=$(df -BG --output=avail "$SESSION" | tail -1 | tr -dc 0-9)
  GNEED=$(( size * SPPEAK_MIB / 1024 + 1 ))   # one group = one single-pass run
  [ "$FREE_GB" -ge "$GNEED" ] || { echo "ABORT before group $g: ~${GNEED}G needed, ${FREE_GB}G free" >&2; exit 1; }
  : > "$G/g$g.list"
  for ((k=0; k<size; k++, i++)); do printf '%s\n' "${SRC[$i]}" >> "$G/g$g.list"; done
  echo "=== group $g/$K: $(wc -l < "$G/g$g.list") frames ==="
  "$REPO/scripts/stack/run_undistort_pipeline.sh" "$SESSION" "$SET" \
    --dark="$DARK" --flat="$FLAT" --select="$G/g$g.list" --chunk="$CHUNK" --out="$SUB.fit" \
    $DESKYOPT
  [ -f "$SUB.fit" ] || { echo "ABORT: group $g produced no sub-stack" >&2; exit 1; }
done

echo "=== final: register + stack $K sub-stacks ==="
rm -rf "$G/final" "$G/finalseq"; mkdir -p "$G/final" "$G/finalseq"
for f in "$G"/sub_*.fit; do ln -sf "$f" "$G/final/$(basename "$f")"; done
printf 'requires 1.2.0\nset32bits\nsetcompress 0\ncd %s\nlink s -out=%s\ncd %s\nregister s -2pass\nseqapplyreg s -framing=%s -prefix=r_\nstack r_s mean none -norm=addscale -output_norm -out=%s\n' \
  "$G/final" "$G/finalseq" "$G/finalseq" "$FRAMING" "$OUT" > "$G/final.ssf"
sir "$SESSION" "$G/final.ssf"
[ -f "$OUT.fit" ] || { echo "FINAL STACK MISSING — read $G/siril_final.log" >&2; exit 1; }
rm -rf "$G/final" "$G/finalseq"
echo "=== DONE: $OUT.fit (sub-stacks kept in $G for re-composition) ==="
ls -la "$OUT.fit"
df -h "$SESSION" | tail -1
