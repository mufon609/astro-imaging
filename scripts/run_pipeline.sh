#!/usr/bin/env bash
# Siril processing pipeline. Usage: scripts/run_pipeline.sh <session-dir> [lights-set]
#   e.g. scripts/run_pipeline.sh 07-02-26          # processes <session>/lights
#        scripts/run_pipeline.sh 07-02-26 set-03   # processes <session>/set-03
# A session dir holds shared calibration (darks required; biases+flats
# optional) plus one or more light-frame sets; each set stacks to
# results/stack_<set>.fit + its previews. Sets without a usable flat
# (missing dirs or focal/aperture mismatch) take the self-flat path.
# Masters in <session>/work/masters/ are rebuilt whenever the source frame
# manifest (names+sizes+mtimes) changes — catches re-shot frames even when
# copied with older timestamps. Intermediates are deleted per stage.
set -euo pipefail

REPO="$(cd "$(dirname "$0")/.." && pwd)"
SESSION="${1:?usage: run_pipeline.sh <session-dir> [lights-set]}"
SET="${2:-lights}"
S="$REPO/$SESSION"
W="$S/work"

for d in "$SET" darks; do
  [[ -d "$S/$d" ]] || { echo "missing $S/$d" >&2; exit 1; }
done
mkdir -p "$W/masters" "$S/results"

siril_run() { # absolute script path
  flatpak run --command=siril-cli org.siril.Siril -d "$S" -s "$1"
}

# Per-run inspection dir: every stage drops a consistent-stretch JPEG +
# metrics (PASS/WARN vs the NOTES.md expectations table); run_post assembles
# index.html. Inspection failures warn but never abort a run.
INSPECT="$S/results/inspect_${SET}_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$INSPECT"
export INSPECT_DIR="$INSPECT"
INS() {
  python3 "$REPO/scripts/inspect_stage.py" "$@" --dir "$INSPECT" \
      --session "$S" --set "$SET" \
    || echo "WARNING: inspection failed for: $* (run continues)" >&2
}

# --- preflight helpers -------------------------------------------------------
uniform() { # dir -> "exposure<TAB>iso"; hard-fails on empty or mixed frames
  local vals n
  n=$(find "$1" -maxdepth 1 -iname '*.dng' | wc -l)
  if [[ "$n" -eq 0 ]]; then
    echo "ERROR: no DNG frames in $1" >&2
    exit 1
  fi
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
manifest() { # dir -> one line per DNG: name size mtime (identity of the set)
  find "$1" -maxdepth 1 -iname '*.dng' -printf '%P %s %T@\n' | sort
}
fresh() { # masterfile srcdir manifestfile — master is current iff the
          # recorded source manifest matches exactly (adds/removals/replaces
          # all count, regardless of mtime direction)
  [[ -f "$1" && -f "$3" ]] || return 1
  diff -q <(manifest "$2") "$3" >/dev/null 2>&1
}

# --- preflight: metadata consistency ----------------------------------------
echo "=== preflight: metadata consistency (set: $SET) ==="
IFS=$'\t' read -r lexp liso <<<"$(uniform "$S/$SET")"
IFS=$'\t' read -r dexp diso <<<"$(uniform "$S/darks")"
echo "$SET: ${lexp}s ISO${liso} | darks: ${dexp}s ISO${diso}"
[[ "$dexp" == "$lexp" ]] || echo "WARNING: darks (${dexp}s) != $SET (${lexp}s) — dark works as bias+hot-pixel map only"
[[ "$diso" == "$liso" ]] || echo "WARNING: darks ISO${diso} != $SET ISO${liso}"

lopt="$(optics "$S/$SET")"
if [[ $(wc -l <<<"$lopt") -ne 1 ]]; then
  echo "WARNING: mixed focal/aperture inside $SET — homography registration absorbs scale, but vignetting varies between frames"
fi

# A flat is usable only if flats AND biases exist (flat calibration needs the
# bias) and the flats' optics match this set. Otherwise: self-flat path.
# Self-flat sets subtract per-frame planar glow (seqsubsky) BEFORE the
# vignette division; post uses RBF background extraction (dense samples,
# raised tolerance so the horizon glow is SAMPLED not rejected, low
# smoothing to follow cloud-scale color) — the approved neutral-sky
# recipe. Landscape (flat-matched) sets keep polynomial subsky.
FLATOPT=""
SUBSKY_DEG="-rbf -samples=30 -tolerance=3 -smooth=0.15"
if [[ -d "$S/flats" && -d "$S/biases" ]]; then
  fopt="$(optics "$S/flats")"
  if [[ "$lopt" == "$fopt" ]]; then
    IFS=$'\t' read -r fexp fiso <<<"$(uniform "$S/flats")"
    IFS=$'\t' read -r bexp biso <<<"$(uniform "$S/biases")"
    echo "flats: ${fexp}s ISO${fiso} | biases: ${bexp}s ISO${biso}"
    [[ "$fiso" == "$liso" ]] || echo "WARNING: flats ISO${fiso} != $SET ISO${liso}"
    [[ "$biso" == "$liso" ]] || echo "WARNING: biases ISO${biso} != $SET ISO${liso}"
    FLATOPT="-flat=masters/flat_master -equalize_cfa"
    # Quicklook background extraction (run_post): flat-matched landscape
    # sets use polynomial degree 1 — RBF carves around treelines; the
    # self-flat RBF default (set above) stays for pure-sky sets.
    SUBSKY_DEG="1"
  else
    echo "WARNING: flats optics ($(tr '\t' '/' <<<"$fopt" | tr '\n' ' ')) != $SET optics ($(tr '\t' '/' <<<"$lopt" | tr '\n' ' '))"
    echo "         self-flat path (median of unregistered lights -> fitted radial gain -> division)"
  fi
else
  echo "no flats+biases dirs — self-flat path"
fi

# --- masters (only the ones this run uses) -----------------------------------
if [[ -n "$FLATOPT" ]]; then
  if fresh "$W/masters/bias_master.fit" "$S/biases" "$W/masters/bias.manifest"; then
    echo "=== master bias up to date, skipping ==="
  else
    echo "=== stage 1/5: master bias ==="
    rm -f "$W/masters/bias_master.fit"
    siril_run "$REPO/scripts/10_master_bias.ssf"
    manifest "$S/biases" > "$W/masters/bias.manifest"
    rm -f "$W"/bias_*
  fi

  if fresh "$W/masters/flat_master.fit" "$S/flats" "$W/masters/flat.manifest" \
     && [[ "$W/masters/flat_master.fit" -nt "$W/masters/bias_master.fit" ]]; then
    echo "=== master flat up to date, skipping ==="
  else
    echo "=== stage 2/5: master flat ==="
    rm -f "$W/masters/flat_master.fit"
    siril_run "$REPO/scripts/20_master_flat.ssf"
    manifest "$S/flats" > "$W/masters/flat.manifest"
    rm -f "$W"/flat_* "$W"/pp_flat_*
  fi
fi

if fresh "$W/masters/dark_master.fit" "$S/darks" "$W/masters/dark.manifest"; then
  echo "=== master dark up to date, skipping ==="
else
  echo "=== stage 3/5: master dark ==="
  rm -f "$W/masters/dark_master.fit"
  siril_run "$REPO/scripts/30_master_dark.ssf"
  manifest "$S/darks" > "$W/masters/dark.manifest"
  rm -f "$W"/dark_*
fi

# --- stage 4: per-set script generated from template -------------------------
NFRAMES=$(find "$S/$SET" -maxdepth 1 -iname '*.dng' | wc -l)
MID=$(( (NFRAMES + 1) / 2 ))
F1=$(printf '%05d' 1); FM=$(printf '%05d' "$MID"); FN=$(printf '%05d' "$NFRAMES")
if [[ -n "$FLATOPT" ]]; then
  GEN4="$W/40_lights.$SET.gen.ssf"
  sed -e "s|@SET@|$SET|g" -e "s|@FLATOPT@|$FLATOPT|g" \
      "$REPO/scripts/40_lights.ssf.tmpl" > "$GEN4"
  echo "=== stage 4/5: calibrate + register + stack $SET ==="
  siril_run "$GEN4"
  INS stage calibrated --in "$W/pp_light_$F1.fit" "$W/pp_light_$FM.fit" "$W/pp_light_$FN.fit"
  INS stage stack --in "$S/results/stack_$SET.fit"
else
  # Self-flat path (see NOTES.md). 4a median of unregistered calibrated
  # frames -> 4b fit radial gain V(r), glow left additive -> 4c divide ->
  # registration reference sweep -> 4d stack.
  GEN4A="$W/40a_selfflat.$SET.gen.ssf"
  sed -e "s|@SET@|$SET|g" "$REPO/scripts/40a_selfflat_median.ssf.tmpl" > "$GEN4A"
  echo "=== stage 4a/5: calibrate + median self-flat $SET ==="
  siril_run "$GEN4A"
  INS stage calibrated --in "$W/pp_light_$F1.fit" "$W/pp_light_$FM.fit" "$W/pp_light_$FN.fit"
  INS stage selfflat_median --in "$W/selfflat_med.fit"
  echo "=== stage 4b/5: fit self-flat gain surface ==="
  python3 "$REPO/scripts/selfflat.py" "$W/selfflat_med.fit" "$W/selfflat_gain.fit"
  cp "$W/selfflat_gain.fit" "$W/masters/selfflat_$SET.fit"   # for inspection
  INS stage gain --in "$W/selfflat_gain.fit"
  # Zero each frame's additive residual per channel (constants only):
  # division by V(r) returns a flat sky only for purely multiplicative
  # frames; siril's seqsubsky re-centers channels on their own medians
  # (magenta rim, R-G +148 at the stack rim) and leaves a pedestal whose
  # division printed the -16% luminance rim. Targets = C_c x median(V)
  # from selfflat_levels.json. See NOTES.md "RIM/RING ROOT CAUSE" + "(L)".
  python3 "$REPO/scripts/rechroma.py" "$W" "$NFRAMES"
  INS stage subsky_frame --in "$W/bkg_pp_light_$F1.fit" "$W/bkg_pp_light_$FM.fit" "$W/bkg_pp_light_$FN.fit"
  # The divisor V2 is measured from the frames actually being divided:
  # siril's plane subtraction also removes the planar share of the bowl,
  # so neither the multiplicative fit (0.537 corner: -16% rim) nor the
  # additive fit (0.472: +7%) matches the frames — their own median does,
  # by construction.
  GEN4A2="$W/40a2_selfflat.$SET.gen.ssf"
  sed -e "s|@SET@|$SET|g" "$REPO/scripts/40a2_selfflat_median2.ssf.tmpl" > "$GEN4A2"
  echo "=== stage 4b2/5: median of glow-subtracted frames + V2 fit ==="
  siril_run "$GEN4A2"
  mv "$W/selfflat_gain.fit" "$W/selfflat_gain1.fit"
  python3 "$REPO/scripts/selfflat.py" "$W/selfflat_med2.fit" "$W/selfflat_gain.fit"
  cp "$W/selfflat_gain.fit" "$W/masters/selfflat_$SET.fit"
  INS stage gain --in "$W/selfflat_gain.fit" --label v2
  GEN4B="$W/40b_selfflat.$SET.gen.ssf"
  sed -e "s|@SET@|$SET|g" "$REPO/scripts/40b_selfflat_divide.ssf.tmpl" > "$GEN4B"
  echo "=== stage 4c/5: divide by self-flat $SET ==="
  siril_run "$GEN4B"
  INS stage divided --in "$W/pp_bkg_pp_light_$F1.fit" "$W/pp_bkg_pp_light_$FM.fit" "$W/pp_bkg_pp_light_$FN.fit"

  # Registration reference sweep: with trailed stars, star matching succeeds
  # or fails depending on the reference frame (measured on set-03: ref 11 ->
  # 19/21, 12 -> 21/21, 2-pass auto-pick 14 -> 18/21). Sweep candidates from
  # the drift-central middle outward, keep the best, stop early on all-in.
  best_ref=0 best_n=0 last_ref=0 sweep_log=""
  for ref in "$MID" "$((MID+1))" "$((MID-1))" "$((MID+2))" "$((MID-2))"; do
    (( ref >= 1 && ref <= NFRAMES )) || continue
    GENREG="$W/40c_register.$SET.gen.ssf"
    {
      echo "requires 1.4.0"
      echo "set16bits"
      echo "cd work"
      echo "setref pp_bkg_pp_light $ref"
      echo "register pp_bkg_pp_light"
      echo "close"
    } > "$GENREG"
    siril_run "$GENREG" | tee "$W/reg_attempt.log"
    last_ref=$ref
    n=$(tr '\r' '\n' < "$W/reg_attempt.log" \
        | grep -oE 'Total: [0-9]+ failed, [0-9]+ registered' | tail -1 \
        | grep -oE '[0-9]+ registered' | grep -oE '[0-9]+' || echo 0)
    echo "=== registration reference $ref: ${n:-0}/$NFRAMES frames ==="
    sweep_log+="$ref:${n:-0} "
    if (( n > best_n )); then best_n=$n; best_ref=$ref; fi
    (( n == NFRAMES )) && break
  done
  (( best_n > 0 )) || { echo "ERROR: registration failed for every candidate reference" >&2; exit 1; }
  if (( last_ref != best_ref )); then
    echo "=== re-running best reference $best_ref ($best_n/$NFRAMES) ==="
    sed -i "s|setref pp_bkg_pp_light $last_ref|setref pp_bkg_pp_light $best_ref|" "$GENREG"
    siril_run "$GENREG"
  fi
  INS reg --registered "$best_n" --total "$NFRAMES" --ref "$best_ref" \
      --sweep "$sweep_log" --seq "$W/pp_bkg_pp_light_.seq"

  GEN4D="$W/40d_selfflat.$SET.gen.ssf"
  sed -e "s|@SET@|$SET|g" "$REPO/scripts/40d_selfflat_stack.ssf.tmpl" > "$GEN4D"
  echo "=== stage 4d/5: stack $SET ($best_n/$NFRAMES frames, ref $best_ref) ==="
  siril_run "$GEN4D"
  INS stage stack --in "$S/results/stack_$SET.fit"
fi
rm -f "$W"/light_* "$W"/pp_light_* "$W"/bkg_pp_light_* "$W"/pp_bkg_pp_light_* \
      "$W"/r_pp_light_* "$W"/r_pp_bkg_pp_light_* \
      "$W"/selfflat_med*.* "$W"/selfflat_gain*.*

echo "=== stage 5/5: post-process ==="
"$REPO/scripts/run_post.sh" "$SESSION" "$SET" "$SUBSKY_DEG"
df -h "$S" | tail -1
