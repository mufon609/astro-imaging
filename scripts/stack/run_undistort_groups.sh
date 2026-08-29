#!/usr/bin/env bash
# Full-depth stack builder for the wide-field UNTRACKED class — the STANDING
# route (the chain derives it; whole-set single-pass runs only as the
# --route=single operator override): consecutive GROUPS of frames are each
# run through the full undistort chain (calibrate -> warp -> register -> rej
# stack) with their intermediates deleted before the next group, then the
# group sub-stacks are registered and stacked into the final — and KEPT, which
# is the point: the cross-set combine composes sub-stacks, and single-pass
# deletes them (composing per-set finals is a registered dead end).
#
#   run_undistort_groups.sh <session-dir> <set> --dark=<master> --flat=<master> \
#                           [--group=<derived>] [--chunk=12] [--out=<stack.fit>] [--plan] \
#                           [--framing=min|max] [--subsky-lights] [--regdata-dir=<dir>]
#                           [--tag=<arm>]
#
# The pre-registration frame-width crop knob (--crop-lr) is RETIRED — refuted
# at the cross-night combine (starves a framing=max union's rims; mechanism +
# numbers: docs/dead-ends/stacking-compose.md, the frame-width-cropping entry;
# implementation recoverable at 6d9e568). Members built with it carry
# FRAMECRP + DIAGARM in their headers.
#
# --tag=<arm>  build into `work/groups_<set>_<arm>` instead of the canonical
#     `work/groups_<set>`. REQUIRED for any A/B arm: the work dir is derived
#     from session+set alone, so an arm run without it lands on the CONTROL's
#     members — and, because a present sub_NN.fit at the same GRPSIZE is a
#     legitimate RESUME, it would silently skip every group and compose the
#     control's members under the arm's name. The arm would look built and be
#     the control. Arm dirs are excluded from the corpus by name
#     (run_corpus_combine.sh takes `groups_set-NN` and nothing else).
#
# --regdata-dir=<dir>  PIN THE PER-GROUP REGISTRATION across the arms of an A/B,
#     the group-route counterpart of run_undistort_pipeline.sh's --regdata= (that
#     block carries the mechanism). One `<dir>/gNN.seq` per group: absent, the
#     group registers normally and WRITES its data there; present, the group is
#     handed it and does not re-register, so its reference frame and every
#     homography are the donor arm's. First arm writes, every later arm reads.
#     MEASURED here that this route needs it, one knob (--subsky-lights) over 12
#     consecutive aug06/set-01 frames: `register -2pass` chose reference index 8
#     unflagged and 11 flagged, delivering a 6038x4033 canvas against 6037x4030.
#     (The reference half of that is since closed by the sub-pipeline's own
#     `setref lt 1`; the flag still pins the TRANSFORMS, which move with the
#     calibration's star lists.)
#     Subtracting a plane per frame changes each frame's statistics and therefore
#     the QUALITY ranking the 2pass picks its reference from — a second knob
#     inside a one-knob experiment, and on a WCS-addressed instrument it is the
#     PAIRING it costs: a different member canvas covers different sky, so the
#     arms are compared over non-identical cell sets.
#     DIAGNOSTIC, like the flags it mirrors: the default path is untouched and
#     the one-click chain does not plumb it.
#
# !! The flat-side `--desky` (seqsubsky on the sky flat's RAW source frames) is
# a REGISTERED 31x REGRESSION — a domain error, background extraction on
# un-flat-fielded data — and is NOT selectable from this builder;
# build_sky_flat.sh keeps it only to reproduce the regressed configuration
# (docs/dead-ends.md + datasets/july31/set-01/qa_work/desky_regression.json).
# The problem it aimed at is real and open: a sky flat converges to sky x V and
# tilts the object. The tilt's MAGNITUDE is UNMEASURED — the long-quoted
# 3.11%/241 sigma has no tracked record and the catalogue-free re-measurement is a
# dead end (docs/dead-ends.md; datasets/aug09/corpus_object_tilt.json).
#
# --subsky-lights is the SEPARATE lights-side step, passed straight through to
# the per-group sub-pipeline: per-frame `subsky 1 -nodither` on the calibrated,
# debayered lights — the operator's correct domain, and the member
# background-matching step whose absence the combine-corner audit measured as a
# ~+1% full-coverage-corner term on the framing=max compose (absent from the
# min-framed control). Rationale, limits and the -nodither pin:
# run_undistort_pipeline.sh. Default OFF pending the BACKLOG:`render-ladder` L1
# arm verdict.
set -euo pipefail
REPO=$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)
source "$REPO/scripts/lib/siril_run.sh"   # serialized siril-cli invoker (BACKLOG:removal-conditions)
source "$REPO/scripts/stack/stamp_headers.sh"     # shared restore of the acquisition keys the warp's TIFF hop drops
source "$REPO/scripts/stack/disk_budget.sh"   # per-set disk derivation, shared with
                                              # the single-pass builder and the router
SESSION=${1:?usage: run_undistort_groups.sh <session-dir> <set> --dark= --flat= [--group=<derived>] [--chunk=12] [--out=] [--plan] [--subsky-lights]}
SET=${2:?missing <set>}
DARK= FLAT= GROUP= CHUNK=12 OUT= PLAN=0 FRAMING=min SUBSKYOPT= RDDIR= TAG=
for a in "${@:3}"; do case "$a" in
  --dark=*) DARK=${a#*=};; --flat=*) FLAT=${a#*=};; --group=*) GROUP=${a#*=};;
  --chunk=*) CHUNK=${a#*=};; --out=*) OUT=${a#*=};; --plan) PLAN=1;;
  --framing=*) FRAMING=${a#*=};;
  --subsky-lights) SUBSKYOPT=--subsky-lights;;
  --regdata-dir=*) RDDIR=${a#*=};;
  --tag=*) TAG=${a#*=};;
  *) echo "unknown arg $a" >&2; exit 1;;
esac; done
# The tag names a DIRECTORY, so anything that could climb out of the work tree
# or collide with the canonical name is refused rather than sanitised.
case "$TAG" in
  "" ) ;;
  *[!a-zA-Z0-9_-]* ) echo "--tag must be [A-Za-z0-9_-]+ (it names a work dir)" >&2; exit 1;;
esac
if [ -n "$RDDIR" ]; then
  mkdir -p "$RDDIR"
  RDDIR="$(cd "$RDDIR" && pwd)"   # the sub-pipeline resolves --regdata from ITS cwd
fi
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
G=$SESSION/work/groups_$SET${TAG:+_$TAG}
mkdir -p "$G" "$(dirname "$OUT")"
[ -z "$TAG" ] || echo "ARM BUILD: members -> $G (the canonical work/groups_$SET is untouched)"
# Absolutize: the flatpak Siril sandbox resolves the .ssf's -out= from the
# script's own CWD, so a relative --out lands the final INSIDE the work tree
# and the existence check fails on a stack that actually built.
OUT="$(cd "$(dirname "$OUT")" && pwd)/$(basename "$OUT")"
sir(){ siril_run_logged "$1" "$2" "$G/siril_final.log"; }

# CAPTURE ORDER, not filename order. Groups are consecutive TIME blocks, and the
# camera's frame counter wraps at 9999 -> 0001: on aug09/set-02 (456 frames, one
# continuous 22.8-min run) filename order puts 0/456 frames in their true
# position, so a group would straddle the wrap and join frames ~20 minutes and
# ~6 deg of sky apart into one sub-stack. See scripts/lib/frame_order.py.
mapfile -t SRC < <(find "$SESSION/$SET" -maxdepth 1 -type f \
     \( -iname '*.nef' -o -iname '*.dng' -o -iname '*.cr2' -o -iname '*.cr3' \
     -o -iname '*.arw' -o -iname '*.raf' \) | sort \
     | python3 "$REPO/scripts/lib/frame_order.py")
# A FITS set arrives here with SRC empty and would fall through to cullspec's
# "cull resolution failed" — the wrong diagnosis for the right stop. This route
# undistorts with darktable, which reads camera raws, not FITS.
[ ${#SRC[@]} -ge 2 ] || {
  nf=$(find "$SESSION/$SET" -maxdepth 1 -type f \( -iname '*.fit' -o -iname '*.fits' \) | wc -l)
  if [ "$nf" -gt 0 ]; then
    echo "ABORT: $SESSION/$SET holds $nf FITS frames and no camera raws. This route" >&2
    echo "  undistorts with darktable, which reads raws — a FITS (dedicated-astrocam)" >&2
    echo "  set cannot take it. Nothing is staged wrong; the route does not accept" >&2
    echo "  this frame format. Use scripts/stack/run_pipeline.sh for the standard" >&2
    echo "  route, or add a FITS path around the darktable stage (a BUILDER change)." >&2
  else
    echo "ABORT: no camera raws (*.nef/dng/cr2/cr3/arw/raf) and no FITS under $SESSION/$SET" >&2
  fi
  exit 1; }
# cull via the single-source cullspec (filename-digit convention; loud ABORT
# on a never-matching or ambiguous exclude)
RECIPE=$REPO/datasets/$(basename "$SESSION")/$SET/recipe.json
mapfile -t SRC < <(python3 "$REPO/scripts/lib/cullspec.py" keep "$RECIPE" "${SRC[@]}")
[ ${#SRC[@]} -ge 1 ] || { echo "ABORT: cull resolution failed or left no frames (see cullspec message above)" >&2; exit 1; }
N=${#SRC[@]}
# GROUP SIZE IS DERIVED, and it is a REJECTION decision, not a disk one. A bare
# `GROUP=15` is actively harmful on two counts that only show up in the final
# product:
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
# The floor must hold for the ACTUAL balanced sizes, not the requested GROUP:
# K = ceil(N/GROUP) then BASE = N/K can land BELOW the floor (135 frames at
# floor 77 -> K=2 -> groups of 67/68, dweller 23/67 = 34% > the 0.3 GESD cap,
# unrejectable) while the GROUP-level check above still passes.
if [ -n "$DWELL_FLOOR" ] && [ "$BASE" -lt "$DWELL_FLOOR" ]; then
  echo "ABORT: balanced groups of $BASE frame(s) fall below the dwell floor $DWELL_FLOOR ($N frames cannot split into >=2 groups meeting it) — the $MAXDWELL-frame transient would exceed GESD's $GESD_FRAC outlier-fraction cap inside a group and would NOT be rejected. Use run_undistort_pipeline.sh (single-pass rejects it at $MAXDWELL/$N of the full set) or cull the transient's frames." >&2
  exit 1
fi
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
echo "plan: $N frames -> $K groups ($REM x $((BASE+1)) + $((K-REM)) x $BASE), peak ~${NEED_GB}G${SUBSKYOPT:+, per-frame subsky 1 -nodither (--subsky-lights)}"
if [ -n "$RDDIR" ]; then
  # State per group which way the pin runs BEFORE the run, so an arm that is
  # silently writing donors when it meant to read them is visible up front.
  HAVE=0; for ((g=1; g<=K; g++)); do
    [ -f "$RDDIR/g$(printf %02d "$g").seq" ] && HAVE=$((HAVE + 1)); done
  echo "  registration: --regdata-dir=$RDDIR — $HAVE of $K group(s) PINNED from an existing gNN.seq, $((K - HAVE)) will register and WRITE their donor"
fi

# --plan MUST EXERCISE THE GUARDS THAT CAN REFUSE THE RUN, not just print the
# arithmetic. Both the dwell floor (above) and the resume check (below) are pure
# decisions over state that already exists, so they cost nothing to evaluate — and
# an operator about to commit hours wants to know a guard will stop them BEFORE
# they commit, not after.
# WHY THIS IS HERE AT ALL: a --plan that exits before the group loop leaves the
# resume guard reachable only by a REAL invocation, so testing it means running
# the builder, which skips the groups and then re-runs the final compose —
# overwriting a built product to exercise a guard. A dry-run surface that stops
# short of the guards is the wrong half of a dry run.
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
  RDOPT=; [ -z "$RDDIR" ] || RDOPT=--regdata=$RDDIR/g$(printf %02d "$g").seq
  "$REPO/scripts/stack/run_undistort_pipeline.sh" "$SESSION" "$SET" \
    --dark="$DARK" --flat="$FLAT" --select="$G/g$g.list" --chunk="$CHUNK" --out="$SUB.fit" \
    $SUBSKYOPT $RDOPT
  [ -f "$SUB.fit" ] || { echo "ABORT: group $g produced no sub-stack" >&2; exit 1; }
  # Stamp the INTENDED group size beside the tool's own STACKCNT. Intended, not
  # STACKCNT itself: registration may legitimately drop a frame, so STACKCNT can be
  # < size without the group being a different size. A header survives a rename;
  # the filename does not.
  python3 -c "
from astropy.io import fits;import sys
fits.setval(sys.argv[1],'GRPSIZE',value=int(sys.argv[2]),
            comment='frames intended in this group')" "$SUB.fit" "$size"
  # SOLVE THE MEMBER NOW, while it is the only thing in flight. Every combine
  # above this level registers ASTROMETRICALLY — from each member's own plate
  # solution, applying that member's own SIP undistortion — and
  # compose_preflight.py REFUSES a combine whose members are unsolved. Measured
  # cost of the star-pair fallback it prevents: roundness 0.458 against 0.974 on
  # the 28-member union. A member born solved makes every combine above it
  # possible; solving 28 of them later, by hand, is how it gets skipped.
  # 2-5 s per member against the minutes the member itself took to build.
  if [ ! -f "$SUB.solved" ]; then
    if python3 "$REPO/scripts/calibrate/solve_field.py" "$SUB.fit" \
         --inject="$SUB.solved.fit" --max-stars=1500 >> "$G/solve.log" 2>&1 \
       && [ -f "$SUB.solved.fit" ]; then
      mv -f "$SUB.solved.fit" "$SUB.fit"; : > "$SUB.solved"
      echo "  solved sub_$(printf %02d "$g") — astrometric combine available"
    else
      echo "  WARNING: sub_$(printf %02d "$g") did NOT solve — every combine above" >&2
      echo "  this set will be REFUSED by compose_preflight until it does (see $G/solve.log)" >&2
    fi
  fi
done

echo "=== final: register + stack $K sub-stacks ==="
rm -rf "$G/final" "$G/finalseq"; mkdir -p "$G/final" "$G/finalseq"
for f in "$G"/sub_*.fit; do ln -sf "$f" "$G/final/$(basename "$f")"; done
# setref 1 (time order) AFTER the 2pass: -norm=addscale matches every member's
# background TO THE REFERENCE and, with NO -output_norm, the product's level IS
# the pinned reference's own IKSS location per channel — stamped below as
# ANCLOC*/ANCSCL* (ANCREF, ANCSRC). -output_norm was a global min-max rescale
# that cancelled the reference's level and set the product's by a single
# resampling-undershoot pixel (MEASURED, one knob, four setref runs: <=2.4%
# moves where "the reference is the level anchor" predicted 1.7-2.3x;
# docs/dead-ends/stacking-compose.md, the -output_norm zero-point entry;
# the shipped design in the same entry). The pin also matters for GEOMETRY: it
# fixes the registration, hence which pixel lands darkest, which is what made
# 2pass's auto-pick a lottery across rebuilds (measured 67-vs-43 ADU on two
# builds of one set, a false baseline regression). Member 1 changes nothing
# else: registration quality is per-member, and the canvas orientation
# re-bases with setref (registry, pre-cropped-stacks entry).
# REMOVAL CONDITION: siril offers a reference-anchored (or per-channel,
# non-min-max) output normalization — then -output_norm returns and the ANC*
# anchor keys retire with it (the compose tier's condition, same wording).
printf 'requires 1.2.0\nset32bits\nsetcompress 0\nsetext fit\ncd %s\nlink s -out=%s\ncd %s\nregister s -2pass -transf=homography\nsetref s 1\nseqapplyreg s -framing=%s -prefix=r_ -interp=lanczos4\nstack r_s mean none -norm=addscale -out=%s\n' \
  "$G/final" "$G/finalseq" "$G/finalseq" "$FRAMING" "$OUT" > "$G/final.ssf"
# siril_final.log is APPEND-ONLY across every run in this work dir (sir() ->
# siril_run_logged >>), and the canonical dirs already hold one "Output
# normalization ...... enabled" line from their original build, so the
# post-assert reads ONLY what THIS run appends: byte offset taken before the
# run, grep scoped to the tail. `stack` prints exactly one of enabled|disabled.
LOGOFF=$(stat -c %s "$G/siril_final.log" 2>/dev/null || echo 0)
sir "$SESSION" "$G/final.ssf"
[ -f "$OUT.fit" ] || { echo "FINAL STACK MISSING — read $G/siril_final.log" >&2; exit 1; }
tail -c +$((LOGOFF + 1)) "$G/siril_final.log" | grep -q "Output normalization ...... disabled" \
  && ! tail -c +$((LOGOFF + 1)) "$G/siril_final.log" | grep -q "Output normalization ...... enabled" || {
  echo "ABORT: siril did not report 'Output normalization ...... disabled' for the" >&2
  echo "  per-set final — its zero point would be the min-max lottery this route" >&2
  echo "  retired (docs/dead-ends/stacking-compose.md). Read $G/siril_final.log" >&2; exit 1; }
ACQHDR=$SESSION/work/acq_header_$SET.json      # captured by the per-group sub-pipeline
if [ -f "$ACQHDR" ]; then
  # The per-set stack is SINGLE-set, so the plain per-set provenance is the
  # correct identity for it — but it was never applied here, so a finished
  # per-set stack carried the acquisition keys and NOT the optics that warped it
  # (measured: stack_set-01_full.fit had no DIST*/CAL* keys at all while its own
  # members did). It also records what registered it: this compose is star-pair,
  # and that is now stated on the product rather than inferable from the script.
  printf 'requires 1.2.0\nset32bits\nsetcompress 0\nsetext fit\nload %s\n%s\nsave %s\n' \
    "$OUT.fit" "$(header_stamp_lines "$ACQHDR" "$N")" "$OUT" > "$G/h.ssf"
  sir "$SESSION" "$G/h.ssf"
  echo "stamped acquisition keywords onto $(basename "$OUT.fit") (LIVETIME = $N x EXPTIME)"
else
  echo "WARNING: no acquisition-header capture — $OUT.fit ships without FOCALLEN/XPIXSZ (solve loses its scale hint)" >&2
fi
# The optics identity goes on unconditionally and through a FITS library, not
# siril: CALSET is `<session>/<set>` and siril's update_key cuts a string value
# at the first `/`. This per-set stack is single-set, so the plain per-set
# provenance IS its identity; it also records that this compose is star-pair.
# BKGLIGHT must name the treatment that RAN. It was hardcoded `none` here, so a
# --subsky-lights per-set stack shipped claiming the members' own BKGLIGHT was
# never applied — every member under it reads `subsky1-nodither` while their
# composite denies it, and the compose gate's MIXED-BACKGROUND warning reads that
# key. A composite that misdescribes its own processing state is worse than an
# unstamped one: the gate is told a confident falsehood.
# THE REFERENCE AND THE ANCHOR, from the sequence files siril wrote (the reads
# run_undistort_compose.sh makes; the mechanism comments live there). s_.seq's
# S line carries the reference `setref s 1` set (0-based). MEASURED on four
# kept compose scratches that `setref s N` before seqapplyreg propagates into
# r_s_.seq (setref s 16 -> r_s_ reference 15, x4); r_s_.seq's OWN S line is what
# `stack` normalized against and is what ANCREF stamps — a disagreement is
# printed. Window: before the `rm -rf "$G/finalseq"` below. The per-set product
# carried no REGREF before this; the pin's member is stamped, source `pinned`.
REFID= REFSRC= ANCHOR= ANCREF=
REF0=$(awk '$1=="S" && NF>=7 {print $7; exit}' "$G/finalseq/s_.seq" 2>/dev/null || true)
RS0=$(awk '$1=="S" && NF>=7 {print $7; exit}' "$G/finalseq/r_s_.seq" 2>/dev/null || true)
if [ -n "${RS0:-}" ] && [ "$RS0" -ge 0 ] 2>/dev/null && [ "$RS0" -lt "$K" ]; then
  [ "$RS0" = "${REF0:-}" ] || echo "WARNING: r_s_.seq reference $RS0 != s_.seq reference ${REF0:-?} (0-based) — the stack normalized against $RS0; ANCREF stamps that, REGREF the pin" >&2
  ANCREF=$((RS0 + 1))
  ANCHOR=$(awk -v r="$RS0" '$1=="M0-"r{l0=$10;s0=$11} $1=="M1-"r{l1=$10;s1=$11} $1=="M2-"r{l2=$10;s2=$11}
    END{ if (l0!="" && l1!="" && l2!="") printf "update_key ANCLOCR %s\nupdate_key ANCLOCG %s\nupdate_key ANCLOCB %s\nupdate_key ANCSCLR %s\nupdate_key ANCSCLG %s\nupdate_key ANCSCLB %s\n", l0, l1, l2, s0, s1, s2 }' "$G/finalseq/r_s_.seq")
  [ -n "$ANCHOR" ] || echo "WARNING: no M lines for reference $RS0 in $G/finalseq/r_s_.seq — ANCLOC*/ANCSCL* unstamped" >&2
else
  echo "WARNING: could not read the reference from $G/finalseq/r_s_.seq — anchor unstamped" >&2
fi
if [ -n "${REF0:-}" ] && [ "$REF0" -ge 0 ] 2>/dev/null && [ "$REF0" -lt "$K" ]; then
  # <1-based index>:<night>/<group dir>/<file>, the compose tier's form
  REFID="$((REF0 + 1)):$(echo "$G/sub_$(printf %02d $((REF0 + 1))).fit" | awk -F/ '{print $(NF-3)"/"$(NF-1)"/"$NF}')"
  REFSRC=pinned
fi
header_apply_keys "$OUT.fit" "$(header_provenance_lines "$REPO" "$SESSION" "$SET" \
    "$([ -n "$SUBSKYOPT" ] && echo subsky1-nodither || echo none)" "$DARK" "$FLAT")
$(header_registration_lines starpair F "$REFID" "$REFSRC")
update_key STACKNRM addscale
update_key ANCSRC \"r_s_.seq M-line IKSS loc/scale of ANCREF; [0,1] float, x65535=ADU16\"
${ANCREF:+update_key ANCREF $ANCREF}
$ANCHOR"
echo "stamped optics provenance + REGMODEL=starpair${REFID:+, REGREF=$REFID [pinned]}, STACKNRM=addscale${ANCREF:+, ANCREF=$ANCREF} onto $(basename "$OUT.fit")"
rm -rf "$G/final" "$G/finalseq"
echo "=== DONE: $OUT.fit (sub-stacks kept in $G for re-composition) ==="
ls -la "$OUT.fit"
df -h "$SESSION" | tail -1
