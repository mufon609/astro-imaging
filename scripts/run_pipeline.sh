#!/usr/bin/env bash
# Siril processing pipeline. Usage: scripts/run_pipeline.sh <session-dir>
#   e.g. scripts/run_pipeline.sh 07-02-26
# Masters in <session>/work/masters/ are reused when up to date; dropping new
# frames into a calibration dir triggers a rebuild of that master.
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

# --- preflight: each dir must be internally uniform in exposure+ISO ---------
uniform() { # dir -> "exposure<TAB>iso"; hard-fails on mixed frames
  local vals
  vals=$(find "$1" -maxdepth 1 -iname '*.dng' -print0 \
         | xargs -0 exiftool -q -T -ExposureTime -ISO | sort -u)
  if [[ $(wc -l <<<"$vals") -ne 1 ]]; then
    echo "ERROR: mixed exposure/ISO inside $1 — remove stale frames:" >&2
    echo "$vals" >&2
    exit 1
  fi
  printf '%s' "$vals"
}

echo "=== preflight: metadata consistency ==="
IFS=$'\t' read -r lexp liso <<<"$(uniform "$S/lights")"
IFS=$'\t' read -r dexp diso <<<"$(uniform "$S/darks")"
IFS=$'\t' read -r bexp biso <<<"$(uniform "$S/biases")"
IFS=$'\t' read -r fexp fiso <<<"$(uniform "$S/flats")"
echo "lights: ${lexp}s ISO${liso} | darks: ${dexp}s ISO${diso} | biases: ${bexp}s ISO${biso} | flats: ${fexp}s ISO${fiso}"
[[ "$dexp" == "$lexp" ]] || echo "WARNING: darks (${dexp}s) != lights (${lexp}s) — dark works as bias+hot-pixel map only"
[[ "$diso" == "$liso" ]] || echo "WARNING: darks ISO${diso} != lights ISO${liso}"
[[ "$fiso" == "$liso" ]] || echo "WARNING: flats ISO${fiso} != lights ISO${liso}"
[[ "$biso" == "$liso" ]] || echo "WARNING: biases ISO${biso} != lights ISO${liso}"

# --- masters: rebuild when missing or older than any source frame -----------
fresh() { # masterfile srcdir
  [[ -f "$1" ]] || return 1
  [[ -z "$(find "$2" -iname '*.dng' -newer "$1" -print -quit)" ]]
}

if fresh "$W/masters/bias_master.fit" "$S/biases"; then
  echo "=== master bias up to date, skipping ==="
else
  echo "=== stage 1/5: master bias ==="
  rm -f "$W/masters/bias_master.fit"
  siril_run 10_master_bias.ssf
  rm -f "$W"/bias_*
fi

if fresh "$W/masters/flat_master.fit" "$S/flats" \
   && [[ "$W/masters/flat_master.fit" -nt "$W/masters/bias_master.fit" ]]; then
  echo "=== master flat up to date, skipping ==="
else
  echo "=== stage 2/5: master flat ==="
  rm -f "$W/masters/flat_master.fit"
  siril_run 20_master_flat.ssf
  rm -f "$W"/flat_* "$W"/pp_flat_*
fi

if fresh "$W/masters/dark_master.fit" "$S/darks"; then
  echo "=== master dark up to date, skipping ==="
else
  echo "=== stage 3/5: master dark ==="
  rm -f "$W/masters/dark_master.fit"
  siril_run 30_master_dark.ssf
  rm -f "$W"/dark_*
fi

echo "=== stage 4/5: calibrate + register + stack lights ==="
siril_run 40_lights.ssf
rm -f "$W"/light_* "$W"/pp_light_* "$W"/r_pp_light_*

echo "=== stage 5/5: post-process ==="
"$REPO/scripts/run_post.sh" "$SESSION"
df -h "$S" | tail -1
