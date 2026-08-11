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
#                           [--framing=min|max] [--subsky-lights]
#
# !! The flat-side `--desky` (seqsubsky on the sky flat's RAW source frames) is
# a REGISTERED 31x REGRESSION — a domain error, background extraction on
# un-flat-fielded data — and is NOT selectable from this builder;
# build_sky_flat.sh keeps it only to reproduce the regressed configuration
# (docs/dead-ends.md + datasets/july31/set-01/qa_work/desky_regression.json).
# The problem it aimed at is real and open: a sky flat converges to sky x V and
# tilts the object (3.11% at 241 sigma).
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
source "$REPO/scripts/lib/siril_run.sh"   # serialized siril-cli invoker (BACKLOG item 18)
source "$REPO/scripts/stack/stamp_headers.sh"     # shared restore of the acquisition keys the warp's TIFF hop drops
source "$REPO/scripts/stack/disk_budget.sh"   # per-set disk derivation, shared with
                                              # the single-pass builder and the router
SESSION=${1:?usage: run_undistort_groups.sh <session-dir> <set> --dark= --flat= [--group=<derived>] [--chunk=12] [--out=] [--plan] [--subsky-lights]}
SET=${2:?missing <set>}
DARK= FLAT= GROUP= CHUNK=12 OUT= PLAN=0 FRAMING=min SUBSKYOPT=
for a in "${@:3}"; do case "$a" in
  --dark=*) DARK=${a#*=};; --flat=*) FLAT=${a#*=};; --group=*) GROUP=${a#*=};;
  --chunk=*) CHUNK=${a#*=};; --out=*) OUT=${a#*=};; --plan) PLAN=1;;
  --framing=*) FRAMING=${a#*=};;
  --subsky-lights) SUBSKYOPT=--subsky-lights;;
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

# CAPTURE ORDER, not filename order. Groups are consecutive TIME blocks, and the
# camera's frame counter wraps at 9999 -> 0001: on aug09/set-02 (456 frames, one
# continuous 22.8-min run) filename order puts 0/456 frames in their true
# position, so a group would straddle the wrap and join frames ~20 minutes and
# ~6 deg of sky apart into one sub-stack. See scripts/lib/frame_order.py.
mapfile -t SRC < <(find "$SESSION/$SET" -maxdepth 1 -type f \
     \( -iname '*.nef' -o -iname '*.dng' -o -iname '*.cr2' -o -iname '*.cr3' \
     -o -iname '*.arw' -o -iname '*.raf' \) | sort \
     | python3 "$REPO/scripts/lib/frame_order.py")
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
    $SUBSKYOPT
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
# background TO THE REFERENCE and -output_norm re-zeroes at the darkest pixel,
# so the reference IS the product's level anchor — and 2pass's auto-pick made
# that a lottery across rebuilds (member skies span up to 1.7x within a set;
# measured 67-vs-43 ADU on two builds of one set, a false baseline regression).
# Member 1 changes nothing else: registration quality is per-member, and the
# canvas orientation re-bases with setref (registry, pre-cropped-stacks entry).
printf 'requires 1.2.0\nset32bits\nsetcompress 0\nsetext fit\ncd %s\nlink s -out=%s\ncd %s\nregister s -2pass\nsetref s 1\nseqapplyreg s -framing=%s -prefix=r_\nstack r_s mean none -norm=addscale -output_norm -out=%s\n' \
  "$G/final" "$G/finalseq" "$G/finalseq" "$FRAMING" "$OUT" > "$G/final.ssf"
sir "$SESSION" "$G/final.ssf"
[ -f "$OUT.fit" ] || { echo "FINAL STACK MISSING — read $G/siril_final.log" >&2; exit 1; }
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
fi
# The optics identity goes on unconditionally and through a FITS library, not
# siril: CALSET is `<session>/<set>` and siril's update_key cuts a string value
# at the first `/`. This per-set stack is single-set, so the plain per-set
# provenance IS its identity; it also records that this compose is star-pair.
if true; then
  header_apply_keys "$OUT.fit" "$(header_provenance_lines "$REPO" "$SESSION" "$SET" none)
$(header_registration_lines starpair F)"
  echo "stamped optics provenance + REGMODEL=starpair onto $(basename "$OUT.fit")"
else
  echo "WARNING: no acquisition-header capture — $OUT.fit ships without FOCALLEN/XPIXSZ (solve loses its scale hint)" >&2
fi
rm -rf "$G/final" "$G/finalseq"
echo "=== DONE: $OUT.fit (sub-stacks kept in $G for re-composition) ==="
ls -la "$OUT.fit"
df -h "$SESSION" | tail -1
