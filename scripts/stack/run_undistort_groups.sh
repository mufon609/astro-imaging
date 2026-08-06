#!/usr/bin/env bash
# Full-depth stack builder for the wide-field UNTRACKED class on a disk too
# small for single-pass registration: consecutive GROUPS of frames are each
# run through the full undistort chain (calibrate -> warp -> register -> rej
# stack) with their intermediates deleted before the next group, then the
# group sub-stacks are registered and rejection-stacked into the final.
#
#   run_undistort_groups.sh <session-dir> <set> --dark=<master> --flat=<master> \
#                           [--group=<derived>] [--chunk=12] [--out=<stack.fit>] [--plan] \
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
source "$REPO/scripts/lib/siril_run.sh"   # serialized siril-cli invoker (BACKLOG item 18)
source "$REPO/scripts/stack/stamp_headers.sh"     # shared restore of the acquisition keys the warp's TIFF hop drops
source "$REPO/scripts/stack/disk_budget.sh"   # per-set disk derivation, shared with
                                              # the single-pass builder and the router
SESSION=${1:?usage: run_undistort_groups.sh <session-dir> <set> --dark= --flat= [--group=<derived>] [--chunk=12] [--out=] [--plan] [--desky]}
SET=${2:?missing <set>}
DARK= FLAT= GROUP= CHUNK=12 OUT= PLAN=0 FRAMING=min DESKYOPT=
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
sir(){ siril_cli -d "$1" -s "$2" >> "$G/siril_final.log" 2>&1; }

mapfile -t SRC < <(find "$SESSION/$SET" -maxdepth 1 -type f \
  \( -iname '*.nef' -o -iname '*.dng' -o -iname '*.cr2' -o -iname '*.cr3' \
     -o -iname '*.arw' -o -iname '*.raf' \) | sort)
# cull via the single-source cullspec (filename-digit convention; loud ABORT
# on a never-matching or ambiguous exclude)
RECIPE=$REPO/datasets/$(basename "$SESSION")/$SET/recipe.json
mapfile -t SRC < <(python3 "$REPO/scripts/lib/cullspec.py" keep "$RECIPE" "${SRC[@]}")
[ ${#SRC[@]} -ge 1 ] || { echo "ABORT: cull resolution failed or left no frames (see cullspec message above)" >&2; exit 1; }
N=${#SRC[@]}
# GROUP SIZE IS DERIVED, and it is a REJECTION decision, not a disk one. It used
# to be a bare `GROUP=15` with no rationale written anywhere, and 15 is actively
# harmful on two counts that only show up in the final product:
#
#  1. ALGORITHM. Each group runs the full single-pass chain, so the group size
#     picks the rejection through stack_rejection_for(): <=50 gets winsorized
#     `rej w 3 3`, >50 gets GESD. At 15 EVERY group sits in the shallow band,
#     when the doctrine for a deep stack is GESD.
#  2. TRANSIENTS. Groups are CONSECUTIVE blocks, so a crossing lands whole inside
#     one. july31/set-03's aircraft crosses 8 consecutive frames: that is 53% of
#     a group of 15 — a per-pixel MAJORITY, which docs/dead-ends.md says SURVIVES
#     rejection ("a DWELLING band becomes the per-pixel majority and survives").
#     The final compose is a PLAIN MEAN with no rejection (sigma-rejection across
#     sub-stacks is a measured dead end), so it would go straight into the
#     product — while the single-pass arm rejects the same 8 frames out of 500
#     with GESD. At 100 the same crossing is 8% of a group: a clear minority.
#
# The cost of a bigger group is only the -framing=min trim per sub-stack, because
# a longer group spans more drift: at july31's 18.8 px/min that is 188 px (3.1%
# of frame width) at 100 against 28 px at 15. Cheap. The extra interpolation pass
# this route declares is a property of the ROUTE and does not change with size.
#
# So: target ~100 frames per group, keep at least 2 groups (one group is the
# single-pass route), and say so when the arithmetic cannot reach the GESD band.
# THE DWELL FLOOR. The band rule above is arithmetic; "any transient a clear
# minority" was an ASSERTION until this block — nothing read a dwell length, so the
# size was right on july31 by arithmetic accident. GESD's FIRST parameter is its
# maximum outlier FRACTION (`rej g 0.3 0.05`), so a transient dwelling n frames
# inside a group of G occupies n/G and is only eligible for rejection while
# n/G < that fraction. Binding constraint: G >= ceil(max_dwell / fraction).
# MEASURED on july31/set-03: a 27-frame satellite against a derived group of 100 is
# 0.270 of 0.30 — clears by ten frames. A 31-frame dweller would have exceeded the
# cap outright and GESD would have stopped treating it as an outlier AT ALL, with no
# symptom except the trail surviving into the product.
# The fraction is read from stack_rejection.sh, not written again here — a fourth
# copy of a constant is exactly what disk_budget.sh exists to prevent.
GESD_FRAC=$(grep -oE 'rej g ([0-9.]+)' "$REPO/scripts/stack/stack_rejection.sh" | head -1 | awk '{print $3}')
GESD_FRAC=${GESD_FRAC:-0.3}
AUDIT=$REPO/datasets/$(basename "$SESSION")/$SET/audit_work/anomaly_audit.json
MAXDWELL=$(python3 - "$AUDIT" <<'PYD' 2>/dev/null || echo ""
import json,sys
try: objs=json.load(open(sys.argv[1])).get("unique_objects") or []
except (OSError,ValueError): sys.exit(1)
print(max((o.get("n") or 0) for o in objs) if objs else 0)
PYD
)
DWELL_FLOOR=""
if [ -n "$MAXDWELL" ]; then
  DWELL_FLOOR=$(python3 -c "import math;print(math.ceil($MAXDWELL/$GESD_FRAC))")
fi
if [ -z "$GROUP" ]; then
  K_TARGET=$(( N / 100 )); [ "$K_TARGET" -lt 2 ] && K_TARGET=2
  GROUP=$(( (N + K_TARGET - 1) / K_TARGET ))
  WHY="target ~100/group to keep every group in the GESD rejection band"
  if [ -n "$DWELL_FLOOR" ] && [ "$DWELL_FLOOR" -gt "$GROUP" ]; then
    GROUP=$DWELL_FLOOR
    WHY="RAISED to the dwell floor: the set's longest transient is $MAXDWELL frames and GESD's outlier fraction is $GESD_FRAC, so a group must exceed $MAXDWELL/$GESD_FRAC = $DWELL_FLOOR or the transient is not even eligible for rejection"
  fi
  echo "group size DERIVED: $GROUP ($N frames; $WHY)"
  [ "$GROUP" -gt 50 ] || echo "  NOTE: $N frames cannot give 2 groups above the GESD threshold of 50 — groups of $GROUP use winsorized rejection. Stated, not silently accepted."
fi
if [ -n "$DWELL_FLOOR" ]; then
  echo "  dwell floor: longest transient $MAXDWELL frames / GESD fraction $GESD_FRAC -> group must be >= $DWELL_FLOOR; using $GROUP ($(python3 -c "print(f'{100*(1-$DWELL_FLOOR/$GROUP):.0f}')")% headroom)"
  [ "$GROUP" -ge "$DWELL_FLOOR" ] || { echo "ABORT: --group=$GROUP is below the dwell floor $DWELL_FLOOR — the set's $MAXDWELL-frame transient would occupy $(python3 -c "print(f'{$MAXDWELL/$GROUP:.2f}')") of a group, at or past GESD's $GESD_FRAC outlier-fraction cap, so it would NOT be rejected. Raise --group." >&2; exit 1; }
else
  echo "  dwell floor: NOT CHECKED — no anomaly_audit.json for this set, so the "\
"'transient is a clear minority' half of the group-size rationale is UNVERIFIED. "\
"Run scripts/qa/anomaly_audit.py to close it."
fi
K=$(( (N + GROUP - 1) / GROUP ))   # AFTER the derivation above: GROUP must exist first
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

# --plan MUST EXERCISE THE GUARDS THAT CAN REFUSE THE RUN, not just print the
# arithmetic. Both the dwell floor (above) and the resume check (below) are pure
# decisions over state that already exists, so they cost nothing to evaluate — and
# an operator about to commit hours wants to know a guard will stop them BEFORE
# they commit, not after.
# WHY THIS IS HERE AT ALL: the resume guard was previously reachable only by a REAL
# invocation, because --plan exited before the group loop. Testing it therefore
# meant running the builder, which skipped the groups and then re-ran the final
# compose — overwriting a built product to exercise a guard. The tooling forced the
# error. A dry-run surface that stops short of the guards is the wrong half of a
# dry run.
plan_resume_check() {
  local g size sub prior bad=0
  for ((g=1; g<=K; g++)); do
    size=$BASE; [ "$g" -le "$REM" ] && size=$((BASE + 1))
    sub=$G/sub_$(printf %02d "$g").fit
    [ -f "$sub" ] || continue
    prior=$(python3 -c "
from astropy.io import fits;import sys
try: print(int(fits.getheader(sys.argv[1]).get('GRPSIZE') or 0))
except Exception: print(0)" "$sub")
    if [ "$prior" = "$size" ]; then
      echo "  resume: $(basename "$sub") exists at group size $size — will be REUSED"
    else
      local was="group size $prior"
      [ "$prior" = 0 ] && was="an UNRECORDED group size (built before GRPSIZE was stamped)"
      echo "  resume: $(basename "$sub") carries $was but this run wants $size — WILL REFUSE" >&2
      bad=1
    fi
  done
  [ "$bad" = 0 ] || { echo "  => a real run would ABORT here: resuming across a group-size change composes mixed depths AND mixed rejection algorithms. Delete $G or re-run with the original --group." >&2; return 1; }
  return 0
}
if [ "$PLAN" -eq 1 ]; then
  plan_resume_check || exit 1
  exit 0
fi
plan_resume_check >/dev/null || plan_resume_check   # re-run to surface the message

i=0
for ((g=1; g<=K; g++)); do
  size=$BASE; [ "$g" -le "$REM" ] && size=$((BASE + 1))
  SUB=$G/sub_$(printf %02d "$g")
  if [ -f "$SUB.fit" ]; then
    # A RESUME MUST NOT MIX GROUP SIZES. The sub-stack name encodes only the INDEX,
    # so a run interrupted at one --group and resumed at another would skip the old
    # sub-stacks, build the rest at the new size, and compose a final from mixed
    # depths — and, since the size selects the rejection algorithm, from mixed
    # rejection algorithms too. Silent: every wire intact, product present. july31
    # hit the precondition twice (an abort at group 6/34 under the old default, and
    # stale empty groups_set-0{3,4} dirs); only an empty payload prevented it.
    PRIOR=$(python3 -c "
from astropy.io import fits;import sys
try: print(int(fits.getheader(sys.argv[1]).get('GRPSIZE') or 0))
except Exception: print(0)" "$SUB.fit")
    if [ "$PRIOR" != "$size" ]; then
      WAS="group size $PRIOR"
      [ "$PRIOR" = 0 ] && WAS="an UNRECORDED group size (built before GRPSIZE was stamped)"
      echo "ABORT: $SUB.fit carries $WAS but this run wants $size." >&2
      echo "       Resuming across a group-size change would compose mixed depths AND mixed" >&2
      echo "       rejection algorithms into one product. Delete $G and rebuild, or re-run" >&2
      echo "       with the original --group." >&2
      exit 1
    fi
    echo "=== group $g/$K: $SUB.fit exists at the same group size ($size), skipping (resume) ==="
    i=$((i + size)); continue
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
  # Stamp the INTENDED group size beside the tool's own STACKCNT. Intended, not
  # STACKCNT itself: registration may legitimately drop a frame, so STACKCNT can be
  # < size without the group being a different size. A header survives a rename;
  # the filename does not.
  python3 -c "
from astropy.io import fits;import sys
fits.setval(sys.argv[1],'GRPSIZE',value=int(sys.argv[2]),
            comment='frames intended in this group')" "$SUB.fit" "$size"
done

echo "=== final: register + stack $K sub-stacks ==="
rm -rf "$G/final" "$G/finalseq"; mkdir -p "$G/final" "$G/finalseq"
for f in "$G"/sub_*.fit; do ln -sf "$f" "$G/final/$(basename "$f")"; done
printf 'requires 1.2.0\nset32bits\nsetcompress 0\nsetext fit\ncd %s\nlink s -out=%s\ncd %s\nregister s -2pass\nseqapplyreg s -framing=%s -prefix=r_\nstack r_s mean none -norm=addscale -output_norm -out=%s\n' \
  "$G/final" "$G/finalseq" "$G/finalseq" "$FRAMING" "$OUT" > "$G/final.ssf"
sir "$SESSION" "$G/final.ssf"
[ -f "$OUT.fit" ] || { echo "FINAL STACK MISSING — read $G/siril_final.log" >&2; exit 1; }
ACQHDR=$SESSION/work/acq_header_$SET.json      # captured by the per-group sub-pipeline
if [ -f "$ACQHDR" ]; then
  printf 'requires 1.2.0\nset32bits\nsetcompress 0\nsetext fit\nload %s\n%s\nsave %s\n' \
    "$OUT.fit" "$(header_stamp_lines "$ACQHDR" "$N")" "$OUT" > "$G/h.ssf"
  sir "$SESSION" "$G/h.ssf"
  echo "stamped acquisition keywords onto $(basename "$OUT.fit") (LIVETIME = $N x EXPTIME)"
else
  echo "WARNING: no acquisition-header capture — $OUT.fit ships without FOCALLEN/XPIXSZ (solve loses its scale hint)" >&2
fi
rm -rf "$G/final" "$G/finalseq"
echo "=== DONE: $OUT.fit (sub-stacks kept in $G for re-composition) ==="
ls -la "$OUT.fit"
df -h "$SESSION" | tail -1
