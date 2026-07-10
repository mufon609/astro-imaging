#!/usr/bin/env bash
# Siril processing pipeline. Usage: scripts/stack/run_pipeline.sh <session-dir> [lights-set]
#   e.g. scripts/stack/run_pipeline.sh 07-02-26          # processes <session>/lights
#        scripts/stack/run_pipeline.sh 07-02-26 set-03   # processes <session>/set-03
# A session dir holds shared calibration (darks required; biases+flats
# optional) plus one or more light-frame sets; each set stacks to
# results/stack_<set>.fit + its previews. Sets without a usable flat
# (missing dirs or focal/aperture mismatch) take the self-flat path.
# Masters in <session>/work/masters/ are rebuilt whenever the source frame
# manifest (names+sizes+mtimes) changes — catches re-shot frames even when
# copied with older timestamps. Intermediates are deleted per stage.
set -euo pipefail

# repo root is two up: this script is scripts/stack/run_pipeline.sh
REPO="$(cd "$(dirname "$0")/../.." && pwd)"
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

# Last sequence-op summary count from a captured siril log ("Total: N
# failed, M registered"). Prints the registered count, or NOTHING when the
# pattern is absent — callers must treat an empty result as "parser found
# no summary" (siril output format change / aborted run), never as 0.
reg_count() {
  tr '\r' '\n' < "$1" \
    | grep -oE 'Total: [0-9]+ failed, [0-9]+ registered' | tail -1 \
    | grep -oE '[0-9]+ registered' | grep -oE '[0-9]+' || true
}

# Per-run inspection dir: every stage drops a consistent-stretch JPEG +
# metrics (PASS/WARN vs the NOTES.md expectations table); the run assembles
# them into index.html at the end. Inspection failures warn but never abort.
INSPECT="$S/results/inspect_${SET}_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$INSPECT"
export INSPECT_DIR="$INSPECT"
INS() {
  python3 "$REPO/scripts/qa/inspect_stage.py" "$@" --dir "$INSPECT" \
      --session "$S" --set "$SET" \
    || echo "WARNING: inspection failed for: $* (run continues)" >&2
}

# --- preflight helpers -------------------------------------------------------
# Ingestable raw frames, any camera format: siril debayers these and exiftool
# reads their EXIF, so a session may hold NEF, DNG, CR2/CR3, ARW, etc. directly.
# DNG conversion is only a fallback for a raw this rig's siril cannot decode
# (e.g. Nikon HE/TicoRAW), never a requirement.
raw_find() { # <dir> [extra find args...]
  find "$1" -maxdepth 1 -type f \( \
      -iname '*.dng' -o -iname '*.nef' -o -iname '*.cr2' -o -iname '*.cr3' \
      -o -iname '*.arw' -o -iname '*.raf' -o -iname '*.orf' -o -iname '*.rw2' \
      -o -iname '*.pef' -o -iname '*.srw' \) "${@:2}"
}
uniform() { # dir -> "exposure<TAB>iso"; hard-fails on empty or mixed frames
  local vals n
  n=$(raw_find "$1" | wc -l)
  if [[ "$n" -eq 0 ]]; then
    echo "ERROR: no raw frames in $1" >&2
    exit 1
  fi
  vals=$(raw_find "$1" -print0 \
         | xargs -0 exiftool -q -T -ExposureTime -ISO | sort -u)
  if [[ $(wc -l <<<"$vals") -ne 1 ]]; then
    echo "ERROR: mixed exposure/ISO inside $1 — remove stale frames:" >&2
    echo "$vals" >&2
    exit 1
  fi
  printf '%s' "$vals"
}
optics() { # dir -> sorted unique "focal<TAB>fnumber" lines (several if mixed)
  raw_find "$1" -print0 \
    | xargs -0 exiftool -q -T -FocalLength -FNumber | sort -u
}
manifest() { # dir -> one line per frame: name size mtime (identity of the set)
  raw_find "$1" -printf '%P %s %T@\n' | sort
}
fresh() { # masterfile srcdir manifestfile — master is current iff the
          # recorded source manifest matches exactly (adds/removals/replaces
          # all count, regardless of mtime direction)
  [[ -f "$1" && -f "$3" ]] || return 1
  diff -q <(manifest "$2") "$3" >/dev/null 2>&1
}

# --- dedicated-astrocam (FITS) ingest ---------------------------------------
# A cooled mono/OSC camera writes 16-bit FITS carrying its own acquisition
# metadata (FILTER, EXPTIME, GAIN, OFFSET, BAYERPAT), so the preflight reads
# headers (fitsmeta.py) instead of EXIF. Frame TYPE stays the directory
# convention (darks/ darkflats/ flats/ <set>/). Calibration rules that differ
# from the camera-raw path:
#   - flats are per-FILTER (vignetting and dust shadows are wavelength
#     dependent), so a flat set whose filter differs from the lights is refused
#   - flats are calibrated with DARK-FLATS (darks matched to the flat exposure),
#     the CMOS standard: multi-second flats carry dark current a bias cannot
#     remove. biases/ is the fallback when no darkflats/ exist.
#   - darks/biases are filter-independent, matched by exposure/gain/offset
#   - a MONO light is never debayered; an OSC CFA FITS (BAYERPAT present) is
fits_glob() { find "$1" -maxdepth 1 -type f \( -iname '*.fit' -o -iname '*.fits' \
    -o -iname '*.fts' \) "${@:2}"; }
manifest_fits() { fits_glob "$1" -printf '%P %s %T@\n' | sort; }
fresh_fits() { [[ -f "$1" && -f "$3" ]] || return 1
  diff -q <(manifest_fits "$2") "$3" >/dev/null 2>&1; }
fits_meta() { python3 "$REPO/scripts/stack/fitsmeta.py" "$1"; }

# convert+stack a dark-type dir into a master: <srcdir-name> <prefix> <outname>
_fits_dark_master() {
  { echo "requires 1.4.0"; echo "set16bits"
    echo "cd $1"; echo "convert $2 -out=../work"
    echo "cd ../work"; echo "stack $2 rej 3 3 -nonorm -out=masters/$3"
    echo "close"; } > "$W/fits_master_$2.gen.ssf"
  siril_run "$W/fits_master_$2.gen.ssf"
}
# master flat, calibrated by $1 (-dark=masters/darkflat_master | -bias=...)
_fits_flat_master() {
  { echo "requires 1.4.0"; echo "set16bits"
    echo "cd flats"; echo "convert fl -out=../work"
    echo "cd ../work"; echo "calibrate fl $1"
    echo "stack pp_fl rej 3 3 -norm=mul -out=masters/flat_master"
    echo "close"; } > "$W/fits_flat.gen.ssf"
  siril_run "$W/fits_flat.gen.ssf"
}
# Dual-band OSC lights: calibrate the CFA mosaic (no debayer — the lines
# live on distinct photosites), split each frame into its emission lines
# (Ha from the R sites at half size; -resample=oiii brings OIII to the
# same half size so neither channel carries invented detail), then
# register BOTH line sequences to the SAME mid-sequence reference frame
# (same-ref by construction — the composed channels must overlay without
# a second interpolation pass) and stack each line. $1 = flat option.
_fits_dualband() {
  local MIDX="$2"
  { echo "requires 1.4.0"; echo "set16bits"
    echo "cd $SET"; echo "convert light -out=../work"
    echo "cd ../work"
    echo "calibrate light -dark=masters/dark_master $1 -cc=dark 3 3 -cfa"
    echo "seqextract_HaOIII pp_light -resample=oiii"
    echo "setref Ha_pp_light $MIDX"
    echo "register Ha_pp_light"
    echo "setref OIII_pp_light $MIDX"
    echo "register OIII_pp_light"
    echo "set32bits"
    echo "stack r_Ha_pp_light rej 3 3 -norm=addscale -output_norm -out=../results/stack_${SET}_Ha"
    echo "stack r_OIII_pp_light rej 3 3 -norm=addscale -output_norm -out=../results/stack_${SET}_OIII"
    echo "close"; } > "$W/fits_dualband.gen.ssf"
  siril_run "$W/fits_dualband.gen.ssf" | tee "$W/lights_run.log"
}

# lights: calibrate -> 2-pass register -> rejection stack. $1 = cfa/debayer
# flags (empty for mono), $2 = flat option (empty when no usable flat).
_fits_lights() {
  { echo "requires 1.4.0"; echo "set16bits"
    echo "cd $SET"; echo "convert light -out=../work"
    echo "cd ../work"
    echo "calibrate light -dark=masters/dark_master $2 -cc=dark 3 3 $1"
    echo "register pp_light -2pass"; echo "seqapplyreg pp_light"
    echo "set32bits"
    echo "stack r_pp_light rej 3 3 -norm=addscale -output_norm -out=../results/stack_$SET"
    echo "close"; } > "$W/fits_lights.gen.ssf"
  siril_run "$W/fits_lights.gen.ssf" | tee "$W/lights_run.log"
}

fits_ingest() {
  echo "=== preflight: FITS acquisition metadata (set: $SET) ==="
  local lexp lgain loff lfilt lmono dexp dgain doff _f _m sm
  sm=$(fits_meta "$S/$SET") || exit 1
  IFS=$'\t' read -r lexp lgain loff lfilt lmono <<<"$sm"
  echo "$SET: ${lexp}s gain${lgain} offset${loff} filter=${lfilt:-none} mono=${lmono}"
  [[ -d "$S/darks" ]] || { echo "missing $S/darks" >&2; exit 1; }
  sm=$(fits_meta "$S/darks") || exit 1
  IFS=$'\t' read -r dexp dgain doff _f _m <<<"$sm"
  echo "darks: ${dexp}s gain${dgain} offset${doff}"
  [[ "$dexp" == "$lexp" ]] || echo "WARNING: darks (${dexp}s) != $SET (${lexp}s) — dark works as bias+hot-pixel map only"
  [[ "$dgain" == "$lgain" && "$doff" == "$loff" ]] || \
    echo "WARNING: darks gain/offset ${dgain}/${doff} != $SET ${lgain}/${loff}"

  # mono lights carry no CFA: no debayer, no cfa-aware cosmetic correction
  local CFAOPT="" FLATOPT="" FLATCAL="" FLATCALOPT=""
  [[ "$lmono" == "1" ]] || CFAOPT="-cfa -debayer"

  if [[ -d "$S/flats" ]]; then
    local fexp ffilt fmono dfexp
    sm=$(fits_meta "$S/flats") || exit 1
    IFS=$'\t' read -r fexp _f _m ffilt fmono <<<"$sm"
    if [[ "$ffilt" != "$lfilt" ]]; then
      echo "WARNING: flats filter '${ffilt}' != $SET filter '${lfilt}' — flats NOT applied (a flat is only valid for its own filter)"
    else
      if [[ -d "$S/darkflats" ]] && fits_glob "$S/darkflats" | grep -q .; then
        sm=$(fits_meta "$S/darkflats") || exit 1
        IFS=$'\t' read -r dfexp _f _m _f _m <<<"$sm"
        [[ "$dfexp" == "$fexp" ]] || echo "WARNING: darkflats (${dfexp}s) != flats (${fexp}s) — dark-flat must match the flat exposure"
        FLATCAL="darkflat"; FLATCALOPT="-dark=masters/darkflat_master"
      elif [[ -d "$S/biases" ]] && fits_glob "$S/biases" | grep -q .; then
        FLATCAL="bias"; FLATCALOPT="-bias=masters/bias_master"
        echo "note: no darkflats/ — calibrating flats with bias (dark-flats are the CMOS standard)"
      else
        echo "WARNING: flats/ present but neither darkflats/ nor biases/ — flats NOT applied"
      fi
      [[ -n "$FLATCAL" ]] && { FLATOPT="-flat=masters/flat_master"
        echo "flats: ${fexp}s filter=${ffilt}, calibrated with ${FLATCAL}"; }
    fi
  else
    echo "no flats/ — lights calibrated with dark only"
  fi

  # --- masters ---
  if fresh_fits "$W/masters/dark_master.fit" "$S/darks" "$W/masters/dark.manifest"; then
    echo "=== master dark up to date, skipping ==="
  else
    echo "=== master dark ==="; rm -f "$W/masters/dark_master.fit"
    _fits_dark_master darks dk dark_master
    manifest_fits "$S/darks" > "$W/masters/dark.manifest"; rm -f "$W"/dk_*
  fi

  if [[ -n "$FLATCAL" ]]; then
    local calsrc="$S/darkflats" calname=darkflat
    [[ "$FLATCAL" == "bias" ]] && { calsrc="$S/biases"; calname=bias; }
    if fresh_fits "$W/masters/${calname}_master.fit" "$calsrc" "$W/masters/${calname}.manifest"; then
      echo "=== master ${calname} up to date, skipping ==="
    else
      echo "=== master ${calname} ==="; rm -f "$W/masters/${calname}_master.fit"
      _fits_dark_master "$(basename "$calsrc")" df "${calname}_master"
      manifest_fits "$calsrc" > "$W/masters/${calname}.manifest"; rm -f "$W"/df_*
    fi
    if fresh_fits "$W/masters/flat_master.fit" "$S/flats" "$W/masters/flat.manifest" \
       && [[ "$W/masters/flat_master.fit" -nt "$W/masters/${calname}_master.fit" ]]; then
      echo "=== master flat up to date, skipping ==="
    else
      echo "=== master flat (calibrated with ${calname}) ==="
      rm -f "$W/masters/flat_master.fit"
      _fits_flat_master "$FLATCALOPT"
      manifest_fits "$S/flats" > "$W/masters/flat.manifest"; rm -f "$W"/fl_* "$W"/pp_fl_*
    fi
  fi

  # --- lights ---
  local NF F1 FM FN
  NF=$(fits_glob "$S/$SET" | wc -l)
  F1=$(printf '%05d' 1); FM=$(printf '%05d' $(( (NF + 1) / 2 ))); FN=$(printf '%05d' "$NF")

  # Composition record (datasets/<session>/<set>/composition.json) drives a
  # convergence build: a dual-band OSC set splits into per-line stacks and
  # composes them. No record -> the ordinary single-stack path (a dual-band
  # set then debayers like broadband: legal, but its lines stay merged —
  # the record is what encodes the data's goal).
  local COMP COMP_KIND=""
  COMP="$REPO/datasets/$SESSION/$SET/composition.json"
  if [[ -f "$COMP" ]]; then
    COMP_KIND=$(python3 -c "import json,sys; print(json.load(open(sys.argv[1])).get('kind',''))" "$COMP")
    echo "composition: $COMP_KIND ($COMP)"
  fi

  if [[ "$COMP_KIND" == "dualband-osc" ]]; then
    [[ "$lmono" == "1" ]] && { echo "ERROR: composition kind dualband-osc but $SET is mono (no CFA to split)" >&2; exit 1; }
    local MID=$(( (NF + 1) / 2 ))
    echo "=== lights: calibrate + extract Ha/OIII + register (ref $MID) + stack $SET ($NF frames) ==="
    _fits_dualband "$FLATOPT" "$MID"
    INS stage calibrated --in "$W/Ha_pp_light_$F1.fit" "$W/Ha_pp_light_$FM.fit" "$W/Ha_pp_light_$FN.fit" --label Ha
    INS stage calibrated --in "$W/OIII_pp_light_$F1.fit" "$W/OIII_pp_light_$FM.fit" "$W/OIII_pp_light_$FN.fit" --label OIII
    # two register runs in one log -> per-line counts, in order
    local RCOUNTS
    mapfile -t RCOUNTS < <(tr '\r' '\n' < "$W/lights_run.log" \
      | grep -oE 'Total: [0-9]+ failed, [0-9]+ registered' \
      | grep -oE '[0-9]+ registered' | grep -oE '[0-9]+')
    if [[ ${#RCOUNTS[@]} -eq 2 ]]; then
      echo "=== registration: Ha ${RCOUNTS[0]}/$NF, OIII ${RCOUNTS[1]}/$NF (ref $MID) ==="
      INS reg --registered "${RCOUNTS[0]}" --total "$NF" --ref "$MID" --seq "$W/Ha_pp_light_.seq"
      INS reg --registered "${RCOUNTS[1]}" --total "$NF" --ref "$MID" --seq "$W/OIII_pp_light_.seq"
    else
      echo "WARNING: expected 2 registration summaries, parsed ${#RCOUNTS[@]} (siril format change?) — tail:" >&2
      tail -8 "$W/lights_run.log" >&2
    fi
    INS stage stack --in "$S/results/stack_${SET}_Ha.fit" --label Ha
    INS stage stack --in "$S/results/stack_${SET}_OIII.fit" --label OIII
    echo "=== compose: per-line stacks -> composed linear ==="
    python3 "$REPO/scripts/stack/compose.py" "$SESSION" "$SET" | tee "$W/compose_run.log"
    local CR
    CR=$(grep -oE 'COMPOSE_RESID [0-9.]+ [0-9.]+' "$W/compose_run.log" | tail -1) || true
    if [[ -n "$CR" ]]; then
      INS compose --resid "$(awk '{print $2}' <<<"$CR")" --p95 "$(awk '{print $3}' <<<"$CR")"
    else
      echo "WARNING: compose emitted no COMPOSE_RESID line" >&2
    fi
    rm -f "$W"/light_* "$W"/pp_light_* "$W"/Ha_pp_light_* "$W"/OIII_pp_light_* \
          "$W"/r_Ha_pp_light_* "$W"/r_OIII_pp_light_*
  else
    echo "=== lights: calibrate + register + stack $SET ($NF frames) ==="
    _fits_lights "$CFAOPT" "$FLATOPT"
    INS stage calibrated --in "$W/pp_light_$F1.fit" "$W/pp_light_$FM.fit" "$W/pp_light_$FN.fit"
    local rn
    rn=$(reg_count "$W/lights_run.log")
    if [[ -n "$rn" ]]; then
      echo "=== registration: $rn/$NF frames (2-pass auto reference) ==="
      INS reg --registered "$rn" --total "$NF" --seq "$W/pp_light_.seq"
    else
      echo "WARNING: no registration summary parsed from siril output (format change?) — tail:" >&2
      tail -5 "$W/lights_run.log" >&2
    fi
    INS stage stack --in "$S/results/stack_$SET.fit"
    rm -f "$W"/light_* "$W"/pp_light_* "$W"/r_pp_light_*
  fi
}

# Data-class fork: a set of dedicated-camera FITS frames takes the FITS ingest
# above; camera raws (DSLR/OSC) take the raw path below. A set holding both is
# ambiguous and must be split, not guessed.
if fits_glob "$S/$SET" | grep -q .; then
  if raw_find "$S/$SET" | grep -q .; then
    echo "ERROR: $SET holds BOTH camera raws and FITS frames — split them" >&2
    exit 1
  fi
  fits_ingest
  echo "=== assembling inspection report ==="
  INS report --title "$SESSION $SET"
  echo "=== inspection report: $INSPECT/index.html ==="
  df -h "$S" | tail -1
  exit 0
fi

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
FLATOPT=""
if [[ -d "$S/flats" && -d "$S/biases" ]]; then
  fopt="$(optics "$S/flats")"
  if [[ "$lopt" == "$fopt" ]]; then
    IFS=$'\t' read -r fexp fiso <<<"$(uniform "$S/flats")"
    IFS=$'\t' read -r bexp biso <<<"$(uniform "$S/biases")"
    echo "flats: ${fexp}s ISO${fiso} | biases: ${bexp}s ISO${biso}"
    [[ "$fiso" == "$liso" ]] || echo "WARNING: flats ISO${fiso} != $SET ISO${liso}"
    [[ "$biso" == "$liso" ]] || echo "WARNING: biases ISO${biso} != $SET ISO${liso}"
    FLATOPT="-flat=masters/flat_master -equalize_cfa"
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
    echo "=== master bias ==="
    rm -f "$W/masters/bias_master.fit"
    siril_run "$REPO/scripts/stack/siril/master_bias.ssf"
    manifest "$S/biases" > "$W/masters/bias.manifest"
    rm -f "$W"/bias_*
  fi

  if fresh "$W/masters/flat_master.fit" "$S/flats" "$W/masters/flat.manifest" \
     && [[ "$W/masters/flat_master.fit" -nt "$W/masters/bias_master.fit" ]]; then
    echo "=== master flat up to date, skipping ==="
  else
    echo "=== master flat ==="
    rm -f "$W/masters/flat_master.fit"
    siril_run "$REPO/scripts/stack/siril/master_flat.ssf"
    manifest "$S/flats" > "$W/masters/flat.manifest"
    rm -f "$W"/flat_* "$W"/pp_flat_*
  fi
fi

if fresh "$W/masters/dark_master.fit" "$S/darks" "$W/masters/dark.manifest"; then
  echo "=== master dark up to date, skipping ==="
else
  echo "=== master dark ==="
  rm -f "$W/masters/dark_master.fit"
  siril_run "$REPO/scripts/stack/siril/master_dark.ssf"
  manifest "$S/darks" > "$W/masters/dark.manifest"
  rm -f "$W"/dark_*
fi

# --- stage 4: per-set script generated from template -------------------------
NFRAMES=$(raw_find "$S/$SET" | wc -l)
MID=$(( (NFRAMES + 1) / 2 ))
F1=$(printf '%05d' 1); FM=$(printf '%05d' "$MID"); FN=$(printf '%05d' "$NFRAMES")
if [[ -n "$FLATOPT" ]]; then
  GEN_LIGHTS="$W/lights.$SET.gen.ssf"
  sed -e "s|@SET@|$SET|g" -e "s|@FLATOPT@|$FLATOPT|g" \
      "$REPO/scripts/stack/siril/lights.ssf.tmpl" > "$GEN_LIGHTS"
  echo "=== lights: calibrate + register + stack $SET ==="
  siril_run "$GEN_LIGHTS" | tee "$W/lights_run.log"
  INS stage calibrated --in "$W/pp_light_$F1.fit" "$W/pp_light_$FM.fit" "$W/pp_light_$FN.fit"
  rn=$(reg_count "$W/lights_run.log")
  if [[ -n "$rn" ]]; then
    echo "=== registration: $rn/$NFRAMES frames (2-pass auto reference) ==="
    INS reg --registered "$rn" --total "$NFRAMES" --seq "$W/pp_light_.seq"
  else
    echo "WARNING: no registration summary parsed from siril output (format change?) — tail:" >&2
    tail -5 "$W/lights_run.log" >&2
  fi
  INS stage stack --in "$S/results/stack_$SET.fit"
else
  # Self-flat path (see NOTES.md): median of unregistered calibrated frames
  # -> fit radial gain V(r) (glow left additive) -> median of glow-subtracted
  # frames + V2 fit -> divide -> register reference sweep -> stack. The four
  # siril steps are stack/siril/selfflat/{1..4}.
  GEN_MEDIAN="$W/selfflat_1_median.$SET.gen.ssf"
  sed -e "s|@SET@|$SET|g" "$REPO/scripts/stack/siril/selfflat/1_median.ssf.tmpl" > "$GEN_MEDIAN"
  echo "=== self-flat 1/4: calibrate + median $SET ==="
  siril_run "$GEN_MEDIAN"
  INS stage calibrated --in "$W/pp_light_$F1.fit" "$W/pp_light_$FM.fit" "$W/pp_light_$FN.fit"
  INS stage selfflat_median --in "$W/selfflat_med.fit"
  echo "=== self-flat: fit gain surface V(r) ==="
  python3 "$REPO/scripts/stack/selfflat.py" "$W/selfflat_med.fit" "$W/selfflat_gain.fit"
  cp "$W/selfflat_gain.fit" "$W/masters/selfflat_$SET.fit"   # for inspection
  INS stage gain --in "$W/selfflat_gain.fit"
  # Zero each frame's additive residual per channel (constants only):
  # division by V(r) returns a flat sky only for purely multiplicative
  # frames; siril's seqsubsky re-centers channels on their own medians
  # (magenta rim, R-G +148 at the stack rim) and leaves a pedestal whose
  # division printed the -16% luminance rim. Targets = C_c x median(V)
  # from selfflat_levels.json. See NOTES.md "RIM/RING ROOT CAUSE" + "(L)".
  python3 "$REPO/scripts/stack/rechroma.py" "$W" "$NFRAMES"
  INS stage subsky_frame --in "$W/bkg_pp_light_$F1.fit" "$W/bkg_pp_light_$FM.fit" "$W/bkg_pp_light_$FN.fit"
  # The divisor V2 is measured from the frames actually being divided:
  # siril's plane subtraction also removes the planar share of the bowl,
  # so neither the multiplicative fit (0.537 corner: -16% rim) nor the
  # additive fit (0.472: +7%) matches the frames — their own median does,
  # by construction.
  GEN_MEDIAN2="$W/selfflat_2_median2.$SET.gen.ssf"
  sed -e "s|@SET@|$SET|g" "$REPO/scripts/stack/siril/selfflat/2_median2.ssf.tmpl" > "$GEN_MEDIAN2"
  echo "=== self-flat 2/4: median of glow-subtracted frames + V2 fit ==="
  siril_run "$GEN_MEDIAN2"
  mv "$W/selfflat_gain.fit" "$W/selfflat_gain1.fit"
  python3 "$REPO/scripts/stack/selfflat.py" "$W/selfflat_med2.fit" "$W/selfflat_gain.fit"
  cp "$W/selfflat_gain.fit" "$W/masters/selfflat_$SET.fit"
  INS stage gain --in "$W/selfflat_gain.fit" --label v2
  GEN_DIVIDE="$W/selfflat_3_divide.$SET.gen.ssf"
  sed -e "s|@SET@|$SET|g" "$REPO/scripts/stack/siril/selfflat/3_divide.ssf.tmpl" > "$GEN_DIVIDE"
  echo "=== self-flat 3/4: divide by gain $SET ==="
  siril_run "$GEN_DIVIDE"
  INS stage divided --in "$W/pp_bkg_pp_light_$F1.fit" "$W/pp_bkg_pp_light_$FM.fit" "$W/pp_bkg_pp_light_$FN.fit"

  # Registration reference sweep: with trailed stars, star matching succeeds
  # or fails depending on the reference frame (measured on set-03: ref 11 ->
  # 19/21, 12 -> 21/21, 2-pass auto-pick 14 -> 18/21). Sweep candidates from
  # the drift-central middle outward, keep the best, stop early on all-in.
  best_ref=0 best_n=0 last_ref=0 sweep_log=""
  for ref in "$MID" "$((MID+1))" "$((MID-1))" "$((MID+2))" "$((MID-2))"; do
    (( ref >= 1 && ref <= NFRAMES )) || continue
    GEN_REGISTER="$W/selfflat_register.$SET.gen.ssf"
    {
      echo "requires 1.4.0"
      echo "set16bits"
      echo "cd work"
      echo "setref pp_bkg_pp_light $ref"
      echo "register pp_bkg_pp_light"
      echo "close"
    } > "$GEN_REGISTER"
    siril_run "$GEN_REGISTER" | tee "$W/reg_attempt.log"
    last_ref=$ref
    n=$(reg_count "$W/reg_attempt.log")
    if [[ -z "$n" ]]; then
      echo "WARNING: no registration summary parsed for ref $ref (siril format change?) — tail:" >&2
      tail -5 "$W/reg_attempt.log" >&2
      n=0
    fi
    echo "=== registration reference $ref: $n/$NFRAMES frames ==="
    sweep_log+="$ref:${n:-0} "
    if (( n > best_n )); then best_n=$n; best_ref=$ref; fi
    (( n == NFRAMES )) && break
  done
  (( best_n > 0 )) || { echo "ERROR: registration failed for every candidate reference" >&2; exit 1; }
  if (( last_ref != best_ref )); then
    echo "=== re-running best reference $best_ref ($best_n/$NFRAMES) ==="
    sed -i "s|setref pp_bkg_pp_light $last_ref|setref pp_bkg_pp_light $best_ref|" "$GEN_REGISTER"
    siril_run "$GEN_REGISTER"
  fi
  INS reg --registered "$best_n" --total "$NFRAMES" --ref "$best_ref" \
      --sweep "$sweep_log" --seq "$W/pp_bkg_pp_light_.seq"

  GEN_STACK="$W/selfflat_4_stack.$SET.gen.ssf"
  sed -e "s|@SET@|$SET|g" "$REPO/scripts/stack/siril/selfflat/4_stack.ssf.tmpl" > "$GEN_STACK"
  echo "=== self-flat 4/4: stack $SET ($best_n/$NFRAMES frames, ref $best_ref) ==="
  siril_run "$GEN_STACK"
  INS stage stack --in "$S/results/stack_$SET.fit"
fi
rm -f "$W"/light_* "$W"/pp_light_* "$W"/bkg_pp_light_* "$W"/pp_bkg_pp_light_* \
      "$W"/r_pp_light_* "$W"/r_pp_bkg_pp_light_* \
      "$W"/selfflat_med*.* "$W"/selfflat_gain*.*

echo "=== assembling inspection report ==="
INS report --title "$SESSION $SET"
echo "=== inspection report: $INSPECT/index.html ==="
df -h "$S" | tail -1
