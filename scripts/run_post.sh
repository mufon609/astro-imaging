#!/usr/bin/env bash
# Post-process an existing stack (fast iteration loop — no re-registration).
# Usage: scripts/run_post.sh <session-dir>
set -euo pipefail

REPO="$(cd "$(dirname "$0")/.." && pwd)"
SESSION="${1:?usage: run_post.sh <session-dir>}"
S="$REPO/$SESSION"
[[ -f "$S/results/stack_latest.fit" ]] || { echo "no stack in $S/results — run run_pipeline.sh first" >&2; exit 1; }

flatpak run --command=siril-cli org.siril.Siril -d "$S" -s "$REPO/scripts/50_postprocess.ssf"

stamp="$(date +%Y%m%d_%H%M%S)"
mv "$S/results/preview.jpg" "$S/results/preview_${stamp}.jpg"
echo "=== done: $S/results/preview_${stamp}.jpg ==="
