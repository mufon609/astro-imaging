#!/usr/bin/env bash
# Siril processing pipeline. Usage: scripts/run_pipeline.sh <session-dir> [lights-set]
#   e.g. scripts/run_pipeline.sh 07-02-26          # processes <session>/lights
#        scripts/run_pipeline.sh 07-02-26 set-03   # processes <session>/set-03
# A session dir holds shared calibration (darks/biases/flats) plus one or more
# light-frame sets; each set stacks to results/stack_<set>.fit + its previews.
# Masters in <session>/work/masters/ are reused when up to date; dropping new
# frames into a calibration dir triggers a rebuild of that master.
# Intermediates are deleted after each stage (disk is limited).
set -euo pipefail

REPO="$(cd "$(dirname "$0")/.." && pwd)"
SESSION="${1:?usage: run_pipeline.sh <session-dir> [lights-set]}"
SET="${2:-lights}"
S="$REPO/$SESSION"
W="$S/work"

for d in "$SET" darks biases flats; do
  [[ -d "$S/$d" ]] || { echo "missing $S/$d" >&2; exit 1; }
done
mkdir -p "$W/masters" "$S/results"

siril_run() { # absolute script path
  flatpak run --command=siril-cli org.siril.Siril -d "$S" -s "$1"
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
optics() { # dir -> sorted unique "focal<TAB>fnumber" lines (several if mixed)
  find "$1" -maxdepth 1 -iname '*.dng' -print0 \
    | xargs -0 exiftool -q -T -FocalLength -FNumber | sort -u
}

echo "=== preflight: metadata consistency (set: $SET) ==="
IFS=$'\t' read -r lexp liso <<<"$(uniform "$S/$SET")"
IFS=$'\t' read -r dexp diso <<<"$(uniform "$S/darks")"
IFS=$'\t' read -r bexp biso <<<"$(uniform "$S/biases")"
IFS=$'\t' read -r fexp fiso <<<"$(uniform "$S/flats")"
echo "$SET: ${lexp}s ISO${liso} | darks: ${dexp}s ISO${diso} | biases: ${bexp}s ISO${biso} | flats: ${fexp}s ISO${fiso}"
[[ "$dexp" == "$lexp" ]] || echo "WARNING: darks (${dexp}s) != $SET (${lexp}s) — dark works as bias+hot-pixel map only"
[[ "$diso" == "$liso" ]] || echo "WARNING: darks ISO${diso} != $SET ISO${liso}"
[[ "$fiso" == "$liso" ]] || echo "WARNING: flats ISO${fiso} != $SET ISO${liso}"
[[ "$biso" == "$liso" ]] || echo "WARNING: biases ISO${biso} != $SET ISO${liso}"

# Flats only correct vignetting shot at the SAME focal length + aperture.
lopt="$(optics "$S/$SET")"
fopt="$(optics "$S/flats")"
FLATOPT="-flat=masters/flat_master -equalize_cfa"
SUBSKY_DEG=1
if [[ "$lopt" != "$fopt" ]]; then
  echo "WARNING: flats optics ($(tr '\t' '/' <<<"$fopt" | tr '\n' ' ')) != $SET optics ($(tr '\t' '/' <<<"$lopt" | tr '\n' ' '))"
  echo "         calibrating WITHOUT flat — vignette stays; re-shoot flats at the lights' focal length to enable it"
  echo "         post-process will use subsky degree 2 to fit the vignette bowl"
  FLATOPT=""
  SUBSKY_DEG=2
fi
if [[ $(wc -l <<<"$lopt") -ne 1 ]]; then
  echo "WARNING: mixed focal/aperture inside $SET — homography registration absorbs scale, but vignetting varies between frames"
fi

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
  siril_run "$REPO/scripts/10_master_bias.ssf"
  rm -f "$W"/bias_*
fi

if fresh "$W/masters/flat_master.fit" "$S/flats" \
   && [[ "$W/masters/flat_master.fit" -nt "$W/masters/bias_master.fit" ]]; then
  echo "=== master flat up to date, skipping ==="
else
  echo "=== stage 2/5: master flat ==="
  rm -f "$W/masters/flat_master.fit"
  siril_run "$REPO/scripts/20_master_flat.ssf"
  rm -f "$W"/flat_* "$W"/pp_flat_*
fi

if fresh "$W/masters/dark_master.fit" "$S/darks"; then
  echo "=== master dark up to date, skipping ==="
else
  echo "=== stage 3/5: master dark ==="
  rm -f "$W/masters/dark_master.fit"
  siril_run "$REPO/scripts/30_master_dark.ssf"
  rm -f "$W"/dark_*
fi

# --- stage 4: per-set script generated from template -------------------------
GEN4="$W/40_lights.$SET.gen.ssf"
sed -e "s|@SET@|$SET|g" -e "s|@FLATOPT@|$FLATOPT|g" \
    "$REPO/scripts/40_lights.ssf.tmpl" > "$GEN4"
echo "=== stage 4/5: calibrate + register + stack $SET ==="
siril_run "$GEN4"
rm -f "$W"/light_* "$W"/pp_light_* "$W"/r_pp_light_*

echo "=== stage 5/5: post-process ==="
"$REPO/scripts/run_post.sh" "$SESSION" "$SET" "$SUBSKY_DEG"
df -h "$S" | tail -1
