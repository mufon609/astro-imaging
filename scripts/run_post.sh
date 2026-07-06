#!/usr/bin/env bash
# Post-process an existing stack (fast iteration loop — no re-registration).
# Usage: scripts/run_post.sh <session-dir> [lights-set] [subsky-arg]
#   subsky-arg: polynomial degree (1..4) or a full RBF spec, e.g.
#   "-rbf -samples=30 -tolerance=3 -smooth=0.15". Defaults to 1.
set -euo pipefail

REPO="$(cd "$(dirname "$0")/.." && pwd)"
SESSION="${1:?usage: run_post.sh <session-dir> [lights-set] [subsky-arg]}"
SET="${2:-lights}"
SUBSKY="${3:-1}"
S="$REPO/$SESSION"
STACK="$S/results/stack_$SET.fit"
[[ -f "$STACK" ]] || { echo "no stack_$SET.fit in $S/results — run run_pipeline.sh first" >&2; exit 1; }
mkdir -p "$S/work"

# Edge crop: 150px margin trims the background-model extrapolation zone and
# the thin stacking coverage; dimensions read from the stack header.
read -r W H < <(python3 - "$STACK" <<'PY'
import re, sys
raw = open(sys.argv[1], "rb").read(2880 * 4).decode("ascii", "replace")
print(re.search(r"NAXIS1\s*=\s*(\d+)", raw).group(1),
      re.search(r"NAXIS2\s*=\s*(\d+)", raw).group(1))
PY
)
M=150

GEN="$S/work/50_post.$SET.gen.ssf"
sed -e "s|@SET@|$SET|g" -e "s|@SUBSKY@|$SUBSKY|g" \
    -e "s|@CROPX@|$M|g" -e "s|@CROPY@|$M|g" \
    -e "s|@CROPW@|$((W - 2 * M))|g" -e "s|@CROPH@|$((H - 2 * M))|g" \
    "$REPO/scripts/50_postprocess.ssf.tmpl" > "$GEN"
flatpak run --command=siril-cli org.siril.Siril -d "$S" -s "$GEN"

stamp="$(date +%Y%m%d_%H%M%S)"
mv "$S/results/preview_$SET.jpg" "$S/results/preview_${SET}_${stamp}.jpg"
echo "=== done: $S/results/preview_${SET}_${stamp}.jpg (subsky $SUBSKY) ==="
# Whole-frame background QA gate: block-median map of the ENTIRE frame,
# luminance spread + per-channel color deviation thresholds. Reports PASS or
# FAIL with offender locations — recipes are graded by this, not by eye alone.
python3 "$REPO/scripts/bg_qa.py" "$S/results/preview_${SET}_${stamp}.jpg" || true
