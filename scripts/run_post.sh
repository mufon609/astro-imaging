#!/usr/bin/env bash
# Post-process an existing stack (fast iteration loop — no re-registration).
# Usage: scripts/run_post.sh <session-dir> [lights-set] [subsky-degree]
#   e.g. scripts/run_post.sh 07-02-26 set-03 2
set -euo pipefail

REPO="$(cd "$(dirname "$0")/.." && pwd)"
SESSION="${1:?usage: run_post.sh <session-dir> [lights-set] [subsky-degree]}"
SET="${2:-lights}"
SUBSKY="${3:-1}"
S="$REPO/$SESSION"
[[ -f "$S/results/stack_$SET.fit" ]] || { echo "no stack_$SET.fit in $S/results — run run_pipeline.sh first" >&2; exit 1; }
mkdir -p "$S/work"

GEN="$S/work/50_post.$SET.gen.ssf"
sed -e "s|@SET@|$SET|g" -e "s|@SUBSKY@|$SUBSKY|g" \
    "$REPO/scripts/50_postprocess.ssf.tmpl" > "$GEN"
flatpak run --command=siril-cli org.siril.Siril -d "$S" -s "$GEN"

stamp="$(date +%Y%m%d_%H%M%S)"
mv "$S/results/preview_$SET.jpg" "$S/results/preview_${SET}_${stamp}.jpg"
echo "=== done: $S/results/preview_${SET}_${stamp}.jpg (subsky $SUBSKY) ==="
