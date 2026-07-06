#!/usr/bin/env bash
# Experiment G1 (NOTES.md): divide-first + stack-level BGE variant.
# Single architectural knob vs the canonical self-flat path: the per-frame
# glow handling (seqsubsky 1 + rechroma + V2) is REMOVED; the untouched
# calibrated frames are divided by the multiplicative-fit V (the
# self-consistent divisor for glow-retaining frames) and the glow is
# removed ONCE, on the stack, by GraXpert BGE (run separately via
# starcomb --stack ... afterwards). Everything else — calibrate line,
# median parameters, reference sweep, stack parameters — is byte-identical
# to run_pipeline.sh's self-flat branch.
# Output: results/stack_<set>_bgeonly.fit (canonical stack untouched).
set -euo pipefail

REPO="$(cd "$(dirname "$0")/.." && pwd)"
SESSION="${1:?usage: exp_bgeonly.sh <session-dir> [lights-set]}"
SET="${2:-set-03}"
S="$REPO/$SESSION"
W="$S/work"

siril_run() { flatpak run --command=siril-cli org.siril.Siril -d "$S" -s "$1"; }

INSPECT="$S/results/inspect_${SET}_bgeonly_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$INSPECT"
export INSPECT_DIR="$INSPECT"
INS() {
  python3 "$REPO/scripts/inspect_stage.py" "$@" --dir "$INSPECT" \
    || echo "WARNING: inspection failed for: $* (run continues)" >&2
}

NFRAMES=$(find "$S/$SET" -maxdepth 1 -iname '*.dng' | wc -l)
MID=$(( (NFRAMES + 1) / 2 ))
F1=$(printf '%05d' 1); FM=$(printf '%05d' "$MID"); FN=$(printf '%05d' "$NFRAMES")

rm -f "$W"/light_* "$W"/pp_light_* "$W"/bkg_pp_light_* "$W"/pp_bkg_pp_light_* \
      "$W"/r_pp_light_* "$W"/r_pp_bkg_pp_light_* "$W"/pp_pp_light_* \
      "$W"/r_pp_pp_light_* "$W"/selfflat_med*.* "$W"/selfflat_gain*.*

GEN4A="$W/40a_bgeonly.$SET.gen.ssf"
cat > "$GEN4A" <<EOF
requires 1.4.0
set16bits
cd $SET
convert light -out=../work
cd ../work
calibrate light -dark=masters/dark_master -cc=dark 3 3 -cfa -debayer
set32bits
stack pp_light med -norm=mul -out=selfflat_med_var
set16bits
close
EOF
echo "=== bgeonly 1/5: calibrate + untouched median ==="
siril_run "$GEN4A"
INS stage calibrated --in "$W/pp_light_$F1.fit" "$W/pp_light_$FM.fit" "$W/pp_light_$FN.fit"
INS stage selfflat_median --in "$W/selfflat_med_var.fit" --label untouched

echo "=== bgeonly 2/5: multiplicative V fit ==="
python3 "$REPO/scripts/selfflat.py" "$W/selfflat_med_var.fit" \
        "$W/selfflat_gain_var.fit" --model=mult
cp "$W/selfflat_gain_var.fit" "$W/masters/selfflat_${SET}_bgeonly.fit"
INS stage gain --in "$W/selfflat_gain_var.fit" --label mult

GEN4B="$W/40b_bgeonly.$SET.gen.ssf"
cat > "$GEN4B" <<EOF
requires 1.4.0
set16bits
cd work
calibrate pp_light -flat=selfflat_gain_var
close
EOF
echo "=== bgeonly 3/5: divide untouched frames by mult-V ==="
siril_run "$GEN4B"
INS stage divided --in "$W/pp_pp_light_$F1.fit" "$W/pp_pp_light_$FM.fit" "$W/pp_pp_light_$FN.fit" --label glowretained

echo "=== bgeonly 4/5: registration reference sweep ==="
best_ref=0 best_n=0 last_ref=0 sweep_log=""
for ref in "$MID" "$((MID+1))" "$((MID-1))" "$((MID+2))" "$((MID-2))"; do
  (( ref >= 1 && ref <= NFRAMES )) || continue
  GENREG="$W/40c_bgeonly.$SET.gen.ssf"
  {
    echo "requires 1.4.0"
    echo "set16bits"
    echo "cd work"
    echo "setref pp_pp_light $ref"
    echo "register pp_pp_light"
    echo "close"
  } > "$GENREG"
  siril_run "$GENREG" | tee "$W/reg_attempt_var.log"
  last_ref=$ref
  n=$(tr '\r' '\n' < "$W/reg_attempt_var.log" \
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
  sed -i "s|setref pp_pp_light $last_ref|setref pp_pp_light $best_ref|" "$GENREG"
  siril_run "$GENREG"
fi
INS reg --registered "$best_n" --total "$NFRAMES" --ref "$best_ref" \
    --sweep "$sweep_log" --seq "$W/pp_pp_light_.seq"

GEN4D="$W/40d_bgeonly.$SET.gen.ssf"
cat > "$GEN4D" <<EOF
requires 1.4.0
set32bits
cd work
stack r_pp_pp_light rej 3 3 -norm=addscale -output_norm -rgb_equal -out=../results/stack_${SET}_bgeonly
close
EOF
echo "=== bgeonly 5/5: stack ($best_n/$NFRAMES frames, ref $best_ref) ==="
siril_run "$GEN4D"
INS stage stack --in "$S/results/stack_${SET}_bgeonly.fit" --label bgeonly

rm -f "$W"/light_* "$W"/pp_light_* "$W"/pp_pp_light_* "$W"/r_pp_pp_light_* \
      "$W"/selfflat_med_var* "$W"/selfflat_gain_var*

echo "=== variant stack measurements (vs canonical L2) ==="
python3 "$REPO/scripts/measure_stack.py" \
    "$S/results/stack_${SET}_bgeonly.fit" "$S/results/stack_${SET}_L2.fit"
df -h "$S" | tail -1
echo "=== bgeonly pipeline done — post-BGE comparison via: starcomb.py --stack results/stack_${SET}_bgeonly.fit ==="
