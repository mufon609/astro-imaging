#!/usr/bin/env bash
# The delivered measurement: how much of each group flat's difference from the
# per-set flat reaches the product, at BOTH levels the brief demands.
#
#   member level   arm B member k over arm A member k, k = 1..5
#   composed level arm B's compose over arm A's compose (registration pinned at
#                  both levels, so the pair is pixel-comparable)
#   controls       IDENTITY (same flat through the arm-B slot), UNIFORM card
#                  (level moves, gradient must not), PLANTED ramp (the recovery
#                  systematic every delivered figure is corrected against), and
#                  the production-normalization pair (what the shipped clause
#                  absorbs)
#   apples-to-apples: each flat ratio cropped to the member's own delivered
#                  canvas and measured with the SAME instrument, which is what
#                  the delivered field must be compared against — the delivered
#                  field is the flats' ratio smeared by the drift and baselined
#                  on the -framing=min canvas, not on the 6064 px frame.
set -euo pipefail
REPO=/home/samsung/Desktop/astro-imaging
S=$REPO/sessions/july31
W=$S/work/pergroup
M=$S/work/masters
P=$M/pergroup
SET=$M/skyflat_set-03.fit
REC=$REPO/datasets/july31/set-03/pergroup_work
mkdir -p "$REC/window"
source "$REPO/scripts/lib/siril_run.sh"

diff_pair() {   # <label> <ref.fit> <alt.fit>
  local lab=$1 ref=$2 alt=$3
  [ -f "$REC/delivered_$lab.json" ] && { echo "=== $lab measured, skipping ==="; return 0; }
  echo "=== delivered: $lab ($(date +%H:%M:%S)) ==="
  python3 "$REPO/scripts/qa/flat_differential.py" "$ref" "$alt" \
    --json="$REC/delivered_$lab.json" --work="$REC/work_$lab" --label="$lab"
}

# ---- 1. the five member pairs ---------------------------------------------
for k in 1 2 3 4 5; do
  diff_pair "member_g$k" "$W/armA/sub_0$k.fit" "$W/armB/sub_0$k.fit"
done

# ---- 2. controls, all at group 1 ------------------------------------------
diff_pair "control_identity" "$W/armA/sub_01.fit" "$W/armI/sub_01.fit"
diff_pair "control_uniform"  "$W/armA/sub_01.fit" "$W/armX/U_01.fit"
diff_pair "control_planted"  "$W/armA/sub_01.fit" "$W/armX/P_01.fit"
diff_pair "control_prodnorm" "$W/armX/An_01.fit"  "$W/armX/Bn_01.fit"

# ---- 3. composed level -----------------------------------------------------
diff_pair "composed"          "$W/armA/compose_armA.fit" "$W/armB/compose_armB.fit"
diff_pair "composed_identity" "$W/armA/compose_armA.fit" "$W/armI/compose_armI.fit"

# ---- 4. each flat ratio cropped to its member's delivered canvas -----------
# Siril crops (centred on the frame, the drift's own mean pointing) and the
# shipped odd-component instrument measures; nothing here reads a pixel.
for k in 1 2 3 4 5; do
  out=$REC/flatratio_window_g$k.json     # records in pergroup_work ITSELF: a
  [ -f "$out" ] && continue              # negation inside an excluded dir is dead
  read -r CW CH < <(python3 -c "
from astropy.io import fits;h=fits.getheader('$W/armA/sub_0$k.fit')
print(int(h['NAXIS1']), int(h['NAXIS2']))")
  read -r FW FH < <(python3 -c "
from astropy.io import fits;h=fits.getheader('$SET');print(int(h['NAXIS1']), int(h['NAXIS2']))")
  X=$(( (FW - CW) / 2 )); Y=$(( (FH - CH) / 2 ))
  X=$((X - X % 2)); Y=$((Y - Y % 2))
  # SET / GROUP, not group / set. A member is light / flat, so the delivered
  # ratio armB/armA is flat_A / flat_B = set / g_k — the INVERSE of the
  # flat-to-flat ratio measured earlier. Comparing the delivered field against
  # g_k/set would compare it with the wrong SIGN and read as a total failure of
  # transfer. Built in the orientation the delivered field is measured in.
  printf 'requires 1.2.0\nset32bits\nsetcompress 0\nsetext fit\nload %s\nfdiv %s 0.5\ncrop %s %s %s %s\nsave %s\n' \
    "$SET" "$P/skyflat_set-03_g$k.fit" "$X" "$Y" "$CW" "$CH" \
    "$REC/window/ratio_win_g$k" > "$REC/window/mk_g$k.ssf"
  siril_cli -d "$REC/window" -s "$REC/window/mk_g$k.ssf" > "$REC/window/mk_g$k.log" 2>&1
  python3 "$REPO/scripts/qa/flat_odd_component.py" "$REC/window/ratio_win_g$k.fit" "$out" \
    --label="flat_ratio_SET_over_g${k}_cropped_to_delivered_canvas_${CW}x${CH}_the_orientation_the_delivered_field_is_measured_in"
  rm -f "$REC/window/ratio_win_g$k.fit"
done

# ---- 5. per-member background ramp, both arms, green plane ----------------
# The registry calls stack background flatness SELF-FULFILLING for flat
# contamination (a stack reads flat precisely BECAUSE the flat absorbed the
# gradient), so this is recorded as the mechanism's size, never as evidence of a
# better calibration. Siril `split` extracts the plane; grid_ramp fits it.
for arm in armA armB; do
  for k in 1 2 3 4 5; do
    out=$REC/memberramp_${arm}_g$k.json
    [ -f "$out" ] && continue
    g=$REC/window/${arm}_g${k}_G
    printf 'requires 1.2.0\nset32bits\nsetcompress 0\nsetext fit\nload %s\nsplit %s %s %s\n' \
      "$W/$arm/sub_0$k.fit" "${g}R" "${g}" "${g}B" > "$REC/window/split_${arm}_$k.ssf"
    siril_cli -d "$REC/window" -s "$REC/window/split_${arm}_$k.ssf" \
      > "$REC/window/split_${arm}_$k.log" 2>&1
    python3 "$REPO/scripts/qa/grid_ramp.py" "${g}.fit" "$out" \
      --label="${arm}_member_g${k}_green_background_ramp"
    rm -f "${g}R.fit" "${g}.fit" "${g}B.fit"
  done
done
echo "=== ALL DELIVERED MEASUREMENTS DONE ($(date +%H:%M:%S)) ==="
