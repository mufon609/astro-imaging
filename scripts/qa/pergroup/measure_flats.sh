#!/usr/bin/env bash
# Flat-to-flat measurement: every group flat against the per-set flat, the
# extreme-group contrast, and the group-depth FLOOR — with both instruments.
#   corner/edge geometry: scripts/qa/flat_odd_component.py --ratio --control
#   ramp slope + axis:     scripts/qa/grid_ramp.py --ratio (registry 9x7, and
#                          the frame-filling auto grid)
set -euo pipefail
REPO=$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)
M=$REPO/sessions/july31/work/masters
P=$M/pergroup
REC=$REPO/datasets/july31/set-03/pergroup_work
mkdir -p "$REC"
SET=$M/skyflat_set-03.fit

pair() {   # <label> <numerator> <denominator>
  local lab=$1 num=$2 den=$3
  echo "=== $lab ==="
  python3 "$REPO/scripts/qa/flat_odd_component.py" "$num" "$REC/odd_$lab.json" \
    --ratio="$den" --control --label="$lab"
  python3 "$REPO/scripts/qa/grid_ramp.py" "$num" "$REC/grid_$lab.json" \
    --ratio="$den" --nx=9 --ny=7 --label="$lab"
  python3 "$REPO/scripts/qa/grid_ramp.py" "$num" "$REC/gridfull_$lab.json" \
    --ratio="$den" --label="${lab}_framefilling"
}

for k in 1 2 3 4 5; do pair "g${k}_over_set" "$P/skyflat_set-03_g$k.fit" "$SET"; done
pair "g1_over_g5"    "$P/skyflat_set-03_g1.fit"   "$P/skyflat_set-03_g5.fit"
pair "FLOOR_g3IA_over_g3IB" "$P/skyflat_set-03_g3IA.fit" "$P/skyflat_set-03_g3IB.fit"
echo "=== ALL FLAT-TO-FLAT MEASUREMENTS DONE ==="
