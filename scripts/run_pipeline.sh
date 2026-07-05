#!/usr/bin/env bash
# Siril processing pipeline. Usage: scripts/run_pipeline.sh <session-dir>
#   e.g. scripts/run_pipeline.sh 07-02-26
# Masters in <session>/work/masters/ are reused if present; delete to rebuild.
# Intermediates are deleted after each stage (disk is limited).
set -euo pipefail

REPO="$(cd "$(dirname "$0")/.." && pwd)"
SESSION="${1:?usage: run_pipeline.sh <session-dir>}"
S="$REPO/$SESSION"
W="$S/work"

for d in lights darks biases flats; do
  [[ -d "$S/$d" ]] || { echo "missing $S/$d" >&2; exit 1; }
done
mkdir -p "$W/masters" "$S/results"

siril_run() {
  flatpak run --command=siril-cli org.siril.Siril -d "$S" -s "$REPO/scripts/$1"
}

if [[ -f "$W/masters/bias_master.fit" ]]; then
  echo "=== master bias exists, skipping ==="
else
  echo "=== stage 1/4: master bias ==="
  siril_run 10_master_bias.ssf
  rm -f "$W"/bias_*
fi

if [[ -f "$W/masters/flat_master.fit" ]]; then
  echo "=== master flat exists, skipping ==="
else
  echo "=== stage 2/4: master flat ==="
  siril_run 20_master_flat.ssf
  rm -f "$W"/flat_* "$W"/pp_flat_*
fi

if [[ -f "$W/masters/dark_master.fit" ]]; then
  echo "=== master dark exists, skipping ==="
else
  echo "=== stage 3/4: master dark ==="
  siril_run 30_master_dark.ssf
  rm -f "$W"/dark_*
fi

echo "=== stage 4/4: calibrate + register + stack lights ==="
siril_run 40_lights.ssf
rm -f "$W"/light_* "$W"/pp_light_* "$W"/r_pp_light_*

stamp="$(date +%Y%m%d_%H%M%S)"
mv "$S/results/preview.jpg" "$S/results/preview_${stamp}.jpg"
echo "=== done: $S/results/stack_latest.fit + preview_${stamp}.jpg ==="
df -h "$S" | tail -1
