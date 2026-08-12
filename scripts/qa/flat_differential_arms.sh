#!/usr/bin/env bash
# Build the FLAT-DIFFERENTIAL A/B arms: the same lights through the same chain,
# one knob — the flat.
#
#   flat_differential_arms.sh <session-dir> <set> --ref-flat=<master> \
#                             --alt-flat=<master> [--frames=125] [--out=<dir>]
#
# THE QUESTION. A sky flat converges to `(mean sky) x V`, so calibration leaves
# the object carrying a multiplicative residual it never had (docs/dead-ends.md).
# The ABSOLUTE size of that residual is a registered DEAD END — a linear
# sensor-fixed mode is exactly degenerate with the per-star and per-block
# nuisances under translational drift, and for a fixed camera the atmosphere is
# sensor-fixed too, with the same airmass shape as the flat's residual. This is
# the DIFFERENTIAL that survives both blockers: two flats of the same optical
# state and different sky dose, applied to the SAME lights. Every sensor-fixed
# term the two arms share — extinction, skyglow, vignetting, the instrumental
# base, the stars' own brightnesses — cancels identically, and what is left is
# only the two flats' imprint difference.
#
# ONE KNOB, ENFORCED BY CONSTRUCTION, NOT BY HOPE. Same raws, same master dark,
# same lens model, same warp, same rejection — and the same REGISTRATION, which
# is the one that had to be forced: `register -2pass` re-chooses the reference
# frame from image quality, and the calibration changes that choice. MEASURED,
# 12 frames of aug09/set-05: skyflat_set-05 -> reference image 1, canvas
# 4896x3616; skyflat_set-01 -> reference image 2, canvas 4887x3641. Arms with
# different canvases are not pixel-comparable at all. The reference arm writes
# its `lt_.seq` and every other arm is handed it (`--regdata=`), so the
# homographies are bit-identical and only the calibration differs.
#
# THE ARMS. Two measure, five control:
#   A   the set's own flat        the production calibration, and the donor of
#                                 the registration data
#   B   the ALTERNATE flat        the counterfactual dose
#   A2  the set's own flat again  IDENTITY floor. Predicted ratio exactly 1.000
#                                 everywhere. Measured here: two unpinned
#                                 rebuilds of one arm are already BIT-identical
#                                 in pixels, so this floor is a true zero and a
#                                 non-zero reading means something
#                                 non-deterministic entered the arm.
#   U   own flat / uniform 1.05   RESPONSE floor. Every pixel differs by 5%, the
#                                 GRADIENT does not: the instrument must move the
#                                 level and leave every dipole at 0.0000. This is
#                                 what makes the identity floor non-vacuous — it
#                                 exercises the whole card path (object_tilt_control's
#                                 uniform-card argument, same shape).
#   P   own flat / ramp k=0.20    PLANTED difference of KNOWN edge ratio 1.2222,
#                                 sign OPPOSITE to the real signal so a
#                                 sign-blind artefact cannot fake it.
#   An/Bn  A and B at the production `-norm=addscale -output_norm`, to MEASURE
#                                 how much of a calibration difference the
#                                 shipped normalization silently absorbs.
#
# THE CARDS ARE SYNTHETIC FIXTURES, never deliverables and never calibration
# frames: generated here, divided in by Siril, measured, kept only as the
# control's own record. The precedent is object_tilt_control.py's `imul` ramp.
# Siril does every pixel operation; this script orchestrates and records.
#
# WHY THE OUTPUTS ARE NOT IN web/results/. Arm B is the cross-set flat reuse
# README step 1b BANS for deliverables. It is admissible here only as a
# DIAGNOSTIC, so its product must not be able to become a deliverable by
# accident: the arms land in the session work tree, and the builder stamps
# DIAGARM/CALXSET/STACKNRM on the FITS itself so the tag travels with the file
# rather than with a directory name.
set -euo pipefail
REPO=$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)
SESSION=${1:?usage: flat_differential_arms.sh <session-dir> <set> --ref-flat= --alt-flat= [--frames=125] [--out=]}
SET=${2:?missing <set>}
REF= ALT= FRAMES=125 OUT=
for a in "${@:3}"; do case "$a" in
  --ref-flat=*) REF=${a#*=};; --alt-flat=*) ALT=${a#*=};;
  --frames=*) FRAMES=${a#*=};; --out=*) OUT=${a#*=};;
  *) echo "unknown arg $a" >&2; exit 1;;
esac; done
[ -n "$REF" ] && [ -n "$ALT" ] || { echo "need --ref-flat= --alt-flat=" >&2; exit 1; }
SESSION=$(cd "$SESSION" && pwd)
OUT=${OUT:-$SESSION/work/flatdiff}
mkdir -p "$OUT"
REF=$(cd "$(dirname "$REF")" && pwd)/$(basename "$REF")
ALT=$(cd "$(dirname "$ALT")" && pwd)/$(basename "$ALT")
REC=$REPO/datasets/$(basename "$SESSION")/$SET/flatdiff_work
mkdir -p "$REC"
source "$REPO/scripts/lib/siril_run.sh"

# ---- the two cards, and the flats derived from them ------------------------
# A card is W x H x 1 float32 (the flat's own geometry — the flat is CFA, so the
# card must be too, and a smooth x-ramp lands equally on every Bayer position).
python3 - "$REF" "$OUT/card_ramp.fit" "$OUT/card_uniform.fit" "$REC/cards.json" <<'PY'
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
# the card's OWN edge-geometry dipole, at the geometry the instrument reads
# (box 80, margin 2 -> box centres at x=42 and x=W-42), stated before the arm runs
lo, hi = float(ramp[42]), float(ramp[w - 42])
json.dump({
    "geometry": [w, hh],
    "ramp": {"k": K, "form": "R(x) = 1 + k*(x/W - 0.5)",
             "edge_ratio_full_frame": float(ramp[-1] / ramp[0]),
             "edge_dipole_x_at_box80_margin2": (hi - lo) / ((hi + lo) / 2)},
    "uniform": {"scalar": S,
                "edge_dipole_x_at_box80_margin2": 0.0,
                "why": "level moves, gradient does not — the instrument must "
                       "respond to gradient and not to level"},
    "role": "synthetic FIXTURES: divided into the flat by Siril, never delivered, "
            "never a calibration frame outside these control arms",
}, open(rec_p, "w"), indent=1)
print(f"cards: ramp k={K} edge ratio {ramp[-1]/ramp[0]:.4f} "
      f"(dipole {(hi-lo)/((hi+lo)/2):+.4f} at box80/margin2), uniform {S}")
PY

for pair in "ramp P" "uniform U"; do
  card=${pair%% *}; tag=${pair##* }
  printf 'requires 1.2.0\nset32bits\nsetcompress 0\nsetext fit\nload %s\nfdiv %s 1.0\nsave %s\n' \
    "$REF" "$OUT/card_$card.fit" "$OUT/flat_$tag" > "$OUT/mkflat_$tag.ssf"
  siril_cli -d "$OUT" -s "$OUT/mkflat_$tag.ssf" > "$OUT/mkflat_$tag.log" 2>&1
  [ -f "$OUT/flat_$tag.fit" ] || { echo "card division failed for $tag — see $OUT/mkflat_$tag.log" >&2; exit 1; }
  echo "derived flat_$tag = $(basename "$REF") / card_$card"
done

# ---- the arms. A FIRST: it writes the registration data every other arm reuses.
SEQ=$OUT/armreg.seq
rm -f "$SEQ"
arm() {  # <tag> <flat> <extra builder args...>
  local tag=$1 flat=$2; shift 2
  echo "=== arm $tag: $(basename "$flat") $* ==="
  "$REPO/scripts/stack/run_undistort_pipeline.sh" "$SESSION" "$SET" \
    --dark="$SESSION/work/masters/dark_master.fit" --flat="$flat" \
    --frames="$FRAMES" --regdata="$SEQ" --out="$OUT/arm_$tag" "$@" \
    > "$OUT/arm_$tag.log" 2>&1 \
    || { echo "ARM $tag FAILED — tail of $OUT/arm_$tag.log:" >&2; tail -20 "$OUT/arm_$tag.log" >&2; exit 1; }
  grep -E 'registration (PINNED|data SAVED)|NORMALIZATION DISABLED|CALXSET' "$OUT/arm_$tag.log" || true
  ls -la "$OUT/arm_$tag.fit"
}
arm A  "$REF"          --nonorm
arm B  "$ALT"          --nonorm
arm A2 "$REF"          --nonorm
arm U  "$OUT/flat_U.fit" --nonorm
arm P  "$OUT/flat_P.fit" --nonorm
arm An "$REF"
arm Bn "$ALT"
echo "=== all arms built in $OUT (registration pinned to $SEQ) ==="
