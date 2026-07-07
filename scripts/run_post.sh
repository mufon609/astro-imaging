#!/usr/bin/env bash
# LEGACY QUICK-LOOK post-process of an existing stack (single stretch, no
# star separation; fast iteration — no re-registration). The PRODUCT chain
# is scripts/starcomb.py (approved recipe B6); this path serves pipeline
# debugging + the historical QA anchors. Its bg_qa runs whole-frame scope
# = REFERENCE numbers, not the gate.
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
rm -f "$S/work"/post_*.fit
flatpak run --command=siril-cli org.siril.Siril -d "$S" -s "$GEN"

stamp="$(date +%Y%m%d_%H%M%S)"
mv "$S/results/preview_$SET.jpg" "$S/results/preview_${SET}_${stamp}.jpg"
echo "=== done: $S/results/preview_${SET}_${stamp}.jpg (subsky $SUBSKY) ==="

# Per-op inspection: reuse the pipeline's inspect dir when called from
# run_pipeline.sh (INSPECT_DIR), else open a post-only one.
if [[ -n "${INSPECT_DIR:-}" && -d "${INSPECT_DIR:-}" ]]; then
  INSPECT="$INSPECT_DIR"
else
  INSPECT="$S/results/inspect_${SET}_post_$stamp"
  mkdir -p "$INSPECT"
fi
INS() {
  python3 "$REPO/scripts/inspect_stage.py" "$@" --dir "$INSPECT" \
    || echo "WARNING: inspection failed for: $* (run continues)" >&2
}
[[ -f "$S/work/post_subsky.fit" ]]  && INS stage post_subsky  --in "$S/work/post_subsky.fit"
[[ -f "$S/work/post_denoise.fit" ]] && INS stage post_denoise --in "$S/work/post_denoise.fit"
if [[ -f "$S/work/post_stretch.fit" ]]; then
  TARGET=$(awk '/^autostretch/ {print $NF; exit}' "$GEN")
  INS stage post_stretch --target "${TARGET:-0.12}" --in "$S/work/post_stretch.fit"
fi
[[ -f "$S/work/post_satu.fit" ]] && INS stage post_satu --in "$S/work/post_satu.fit"
INS stage final --in "$S/results/preview_${SET}_${stamp}.jpg"
cp "$GEN" "$INSPECT/recipe_post.ssf"

# Whole-frame background QA gate: block-median map of the ENTIRE frame,
# luminance spread + per-channel color deviation thresholds. Reports PASS or
# FAIL with offender locations — recipes are graded by this, not by eye alone.
python3 "$REPO/scripts/bg_qa.py" "$S/results/preview_${SET}_${stamp}.jpg" \
  | tee "$INSPECT/qa.txt" || true
INS report --title "$SESSION $SET — $stamp" --qa "$INSPECT/qa.txt"
rm -f "$S/work"/post_*.fit
echo "=== inspection report: $INSPECT/index.html ==="
