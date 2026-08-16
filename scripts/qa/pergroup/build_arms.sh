#!/usr/bin/env bash
# The flat-window arms, one knob: which flat calibrates each group's 100 frames.
#
#   A_k  the per-set flat (production)      — writes group k's registration data
#   B_k  group k's OWN flat                 — handed A_k's registration data
#   I_k  the per-set flat again, through the arm-B slot — IDENTITY control,
#        predicted bit-identical to A_k
# then, on group 1 only:
#   P    the set flat / ramp card k=0.20    — PLANTED, known edge ratio, the
#        recovery systematic every delivered figure is corrected against
#   U    the set flat / uniform 1.05 card   — every pixel differs, the GRADIENT
#        does not: the instrument must move the level and leave dipoles at zero
#   An/Bn  A and B at the production -norm=addscale -output_norm, to MEASURE
#        what the shipped normalization absorbs
#
# Every arm is --nonorm except An/Bn: the production normalization coefficients
# are computed from the frames' own statistics, so on a calibration A/B they are
# computed from data that DIFFERS between arms and partially absorb the effect
# under test (measured: 0.3-0.4% absorbed on the object, but the background pixel
# field moves 48.6% — a pedestal artefact). The pixel instrument is valid on
# -nonorm arms only.
#
# Sequential by necessity: the sub-pipeline locks one work dir per set, siril is
# serialized, and the lensfun user DB is global machine state.
set -euo pipefail
REPO=$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)
S=$REPO/sessions/july31
G=$S/work/groups_set-03
W=$S/work/pergroup
M=$S/work/masters
P=$M/pergroup
DARK=$M/dark_master.fit
SET=$M/skyflat_set-03.fit
REC=$REPO/datasets/july31/set-03/pergroup_work
mkdir -p "$W/armA" "$W/armB" "$W/armI" "$W/armX" "$REC"
source "$REPO/scripts/lib/siril_run.sh"

# ---- the two synthetic cards, and the flats derived from them --------------
# W x H x 1 float32 at the flat's own geometry (the flat is CFA, so the card
# must be too; a smooth x-ramp lands equally on every Bayer position). Synthetic
# FIXTURES: divided into the flat by Siril, never delivered, never a calibration
# frame outside these control arms. Precedent: flat_differential_arms.sh.
if [ ! -f "$W/flat_P.fit" ] || [ ! -f "$W/flat_U.fit" ]; then
python3 - "$SET" "$W/card_ramp.fit" "$W/card_uniform.fit" "$REC/cards.json" <<'PY'
import json, sys
import numpy as np
from astropy.io import fits
ref, ramp_p, unif_p, rec_p = sys.argv[1:5]
h = fits.getheader(ref)                      # HEADER only — the card is synthetic
w, hh = int(h["NAXIS1"]), int(h["NAXIS2"])
K, S = 0.20, 1.05
x = np.arange(w, dtype=np.float32)
ramp = (1.0 + K * (x / float(w) - 0.5)).astype(np.float32)
fits.PrimaryHDU(np.broadcast_to(ramp, (hh, w)).astype(np.float32)).writeto(ramp_p, overwrite=True)
fits.PrimaryHDU(np.full((hh, w), S, dtype=np.float32)).writeto(unif_p, overwrite=True)
lo, hi = float(ramp[42]), float(ramp[w - 42])
json.dump({
    "geometry": [w, hh],
    "ramp": {"k": K, "form": "R(x) = 1 + k*(x/W - 0.5)",
             "edge_ratio_full_frame": float(ramp[-1] / ramp[0]),
             "edge_dipole_x_at_box80_margin2": (hi - lo) / ((hi + lo) / 2)},
    "uniform": {"scalar": S, "edge_dipole_x_at_box80_margin2": 0.0,
                "why": "level moves, gradient does not"},
    "role": "synthetic FIXTURES divided into the per-set flat by Siril; never "
            "delivered, never a calibration frame outside these control arms",
}, open(rec_p, "w"), indent=1)
print(f"cards: ramp k={K} edge ratio {ramp[-1]/ramp[0]:.4f} "
      f"(dipole {(hi-lo)/((hi+lo)/2):+.4f} at box80/margin2), uniform {S}")
PY
for pair in "ramp P" "uniform U"; do
  card=${pair%% *}; tag=${pair##* }
  printf 'requires 1.2.0\nset32bits\nsetcompress 0\nsetext fit\nload %s\nfdiv %s 1.0\nsave %s\n' \
    "$SET" "$W/card_$card.fit" "$W/flat_$tag" > "$W/mkflat_$tag.ssf"
  siril_cli -d "$W" -s "$W/mkflat_$tag.ssf" > "$W/mkflat_$tag.log" 2>&1
  [ -f "$W/flat_$tag.fit" ] || { echo "card division failed for $tag — see $W/mkflat_$tag.log" >&2; exit 1; }
  echo "derived flat_$tag = skyflat_set-03 / card_$card"
done
fi

arm() {   # <outdir> <tag> <group> <flat> [extra args...]
  local dir=$1 tag=$2 g=$3 flat=$4; shift 4
  local out=$W/$dir/sub_$(printf %02d "$g")
  [ -f "$out.fit" ] && { echo "=== $tag g$g exists, skipping ==="; return 0; }
  echo "=== arm $tag group $g: $(basename "$flat") $* ($(date +%H:%M:%S)) ==="
  "$REPO/scripts/stack/run_undistort_pipeline.sh" "$S" set-03 \
    --dark="$DARK" --flat="$flat" --select="$G/g$g.list" \
    --regdata="$W/armreg_g$g.seq" --out="$out.fit" "$@" \
    > "$W/$dir/arm_${tag}_g$g.log" 2>&1 \
    || { echo "ARM $tag g$g FAILED — tail:" >&2; tail -20 "$W/$dir/arm_${tag}_g$g.log" >&2; exit 1; }
  # CALFSUM: the cross-set operator NOTE stopped saying CALXSET when that key was
  # deprecated as a write target. The warning is still emitted; without this it
  # lands in a log nobody greps for it.
  grep -E 'registration (PINNED|data SAVED)|NORMALIZATION DISABLED|CALXSET|CALFSUM' \
    "$W/$dir/arm_${tag}_g$g.log" || true
}

for g in 1 2 3 4 5; do
  arm armA "A" "$g" "$SET"                          --nonorm
  arm armB "B" "$g" "$P/skyflat_set-03_g$g.fit"     --nonorm
  arm armI "I" "$g" "$SET"                          --nonorm
  # IDENTITY, checked the moment it can be: the route is measured
  # bit-reproducible on this rig, so this must be a TRUE zero.
  cmp -s "$W/armA/sub_$(printf %02d "$g").fit" "$W/armI/sub_$(printf %02d "$g").fit" \
    && echo "  IDENTITY g$g: byte-identical to arm A" \
    || echo "  IDENTITY g$g: NOT byte-identical — pixels checked by the instrument" >&2
done

# group 1 only: the planted / uniform / production-normalization arms. Each
# writes the same sub_01.fit slot, so the slot is cleared first and the product
# renamed straight after — the outer guard is what makes a resume safe.
xarm() {   # <tag> <flat> [extra...]
  local tag=$1 flat=$2; shift 2
  [ -f "$W/armX/${tag}_01.fit" ] && { echo "=== $tag exists, skipping ==="; return 0; }
  rm -f "$W/armX/sub_01.fit"
  arm armX "$tag" 1 "$flat" "$@"
  mv "$W/armX/sub_01.fit" "$W/armX/${tag}_01.fit"
}
xarm P  "$W/flat_P.fit"              --nonorm
xarm U  "$W/flat_U.fit"              --nonorm
xarm An "$SET"
xarm Bn "$P/skyflat_set-03_g1.fit"
echo "=== ALL ARMS BUILT ($(date +%H:%M:%S)) ==="
ls -la "$W"/arm*/*.fit
df -h "$S" | tail -1
