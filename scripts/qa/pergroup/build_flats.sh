#!/usr/bin/env bash
# Per-group flat builds for the flat-window arms + the group-depth floor control.
# Sequential by necessity: build_sky_flat.sh wipes and reuses one work dir per
# set, and every siril call is serialized anyway.
set -euo pipefail
REPO=$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)
S=$REPO/sessions/july31
G=$S/work/groups_set-03
W=$S/work/pergroup
M=$S/work/masters/pergroup
DARK=$S/work/masters/dark_master.fit
mkdir -p "$M"
for tag in g1 g2 g3 g4 g5; do
  out=$M/skyflat_set-03_$tag
  [ -f "$out.fit" ] && { echo "=== $tag exists, skipping ==="; continue; }
  echo "=== flat $tag: $(wc -l < "$G/$tag.list") frames ==="
  "$REPO/scripts/stack/build_sky_flat.sh" "$S" set-03 --dark="$DARK" \
    --out="$out" --select="$G/$tag.list"
done
for tag in IA IB; do
  out=$M/skyflat_set-03_g3$tag
  [ -f "$out.fit" ] && { echo "=== g3$tag exists, skipping ==="; continue; }
  echo "=== FLOOR control flat g3$tag: $(wc -l < "$W/g3_$tag.list") frames (interleaved half of g3) ==="
  "$REPO/scripts/stack/build_sky_flat.sh" "$S" set-03 --dark="$DARK" \
    --out="$out" --select="$W/g3_$tag.list"
done
echo "=== ALL FLATS BUILT ==="
ls -la "$M"/*.fit
