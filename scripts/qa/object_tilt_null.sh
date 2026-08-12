#!/usr/bin/env bash
# NULL control for scripts/qa/object_tilt.py — the interleaved-halves floor.
#
#   object_tilt_null.sh <session-dir> <set> --dark=<master> --flat=<master> \
#                       [--out-dir=<dir>]
#
# THE SHAPE. One set's frames are split INTERLEAVED in capture order — even
# frames against odd — and each half is built into its own stack through the
# SAME undistort chain and solved the same way. Interleaved halves span the
# same drift, so the two products see the same sensor-position distribution and
# their mean sensor positions differ by ONE FRAME INTERVAL (~2 px against the
# set's ~780 px baseline). Any sensor-fixed multiplicative field is therefore
# common to both, and THE PREDICTED TILT IS ZERO. What the instrument reports
# on that pair is its floor.
#
# WHAT THIS CONFIGURATION ALSO TESTS, and why it is worth the rebuild even
# though the answer is predictable. object_tilt.py's identifying lever is the
# FIELD ROTATION between blocks, not the translation, and interleaved halves
# share their rotation as well as their drift — so the lever should collapse to
# ~0 and the fit should become formally unidentifiable. The instrument reports
# `lever_px_x` precisely so that state is legible instead of arriving as a
# confident wrong number: --selftest 4a shows the degenerate case returning a
# planted +0.100 as -0.046 +- 0.0001. This run is that selftest executed on
# real data.
#
# Interleaving, not halving in time, is the point: two CONSECUTIVE halves would
# differ in mean sensor position by half the set's drift and would measure the
# tilt rather than the floor.
#
# REMOVAL CONDITION: retires with scripts/qa/object_tilt.py.
set -euo pipefail
REPO=$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)
SESSION=${1:?usage: object_tilt_null.sh <session-dir> <set> --dark= --flat= [--out-dir=]}
SET=${2:?missing <set>}
DARK= FLAT= OUTDIR=
for a in "${@:3}"; do case "$a" in
  --dark=*) DARK=${a#*=};; --flat=*) FLAT=${a#*=};; --out-dir=*) OUTDIR=${a#*=};;
  *) echo "unknown arg $a" >&2; exit 1;;
esac; done
[ -n "$DARK" ] && [ -n "$FLAT" ] || { echo "need --dark= --flat=" >&2; exit 1; }
SESSION=$(cd "$SESSION" && pwd)
OUTDIR=${OUTDIR:-$SESSION/work/tiltnull_$SET}
rm -rf "$OUTDIR"; mkdir -p "$OUTDIR"

# CAPTURE ORDER then the set's own cull — the same two steps the group builder
# takes, so the halves are drawn from exactly the population the real blocks were
mapfile -t SRC < <(find "$SESSION/$SET" -maxdepth 1 -type f -iname '*.nef' | sort \
                   | python3 "$REPO/scripts/lib/frame_order.py")
mapfile -t SRC < <(python3 "$REPO/scripts/lib/cullspec.py" keep \
                   "$REPO/datasets/$(basename "$SESSION")/$SET/recipe.json" "${SRC[@]}")
N=${#SRC[@]}
: > "$OUTDIR/even.list"; : > "$OUTDIR/odd.list"
for ((i = 0; i < N; i++)); do
  if [ $((i % 2)) -eq 0 ]; then echo "${SRC[$i]}" >> "$OUTDIR/even.list"
  else echo "${SRC[$i]}" >> "$OUTDIR/odd.list"; fi
done
echo "$N culled frames -> even $(wc -l < "$OUTDIR/even.list") / odd $(wc -l < "$OUTDIR/odd.list")"

i=1
for half in even odd; do
  echo "=== building $half half ==="
  "$REPO/scripts/stack/run_undistort_pipeline.sh" "$SESSION" "$SET" \
      --dark="$DARK" --flat="$FLAT" --select="$OUTDIR/$half.list" \
      --out="$OUTDIR/$half" >> "$OUTDIR/build_$half.log" 2>&1
  SUB=$(printf "%s/sub_%02d" "$OUTDIR" "$i")
  python3 "$REPO/scripts/calibrate/solve_field.py" "$OUTDIR/$half.fit" \
      --inject="$SUB.fit" --max-stars=1500 >> "$OUTDIR/solve.log" 2>&1
  [ -f "$SUB.fit" ] || { echo "ABORT: $half half did not solve — $OUTDIR/solve.log" >&2; exit 1; }
  rm -f "$OUTDIR/$half.fit"
  i=$((i + 1))
done

python3 "$REPO/scripts/qa/object_tilt.py" "$OUTDIR" --work="$OUTDIR/tilt_work" \
    --json="$REPO/datasets/$(basename "$SESSION")/$SET/tilt_work/object_tilt_null.json" \
    --label="interleaved-halves NULL, predicted tilt zero"
