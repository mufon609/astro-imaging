#!/usr/bin/env bash
# Guard: the chain is 32-bit float END TO END — no generated or templated .ssf
# may pin `set16bits`. Run it in CI / before a release.
#
# WHY THIS GUARD EXISTS. 16-bit intermediates were a RAM/disk adaptation for a
# tight rig. Its removal condition fired when the chain moved to a machine with
# headroom, and the retirement was applied to the wide-field light path — but
# the CALIBRATION-MASTER templates (dark/bias/flat) and the standard chain's
# light template were missed, so the repo went on silently emitting 16-bit
# masters for an otherwise-float32 chain. It survived undetected because one
# session worked around it with a SESSION-LOCAL builder pinning set32bits whose
# own comment claimed it was "identical to" the repo template it contradicted.
# A guard, not a comment, is what makes that impossible to repeat.
#
# WHAT IT COSTS, measured, so the rule is not doctrine:
# - A master dark is a many-frame MEAN, so its precision is far finer than one
#   integer step. Rounding to 16 bits stores a SENSOR-FIXED quantization
#   pattern that is then subtracted identically into every light — the input to
#   walking noise, which no rejection or cosmetic correction removes. On a
#   200-frame master: quantization 0.2889 ADU RMS (uniform +-0.5, matching
#   1/sqrt(12) = 0.2887 to four figures) against a statistical floor of 0.4213
#   ADU (split-half measured), inflating the fixed-pattern residual
#   0.4213 -> 0.5109 ADU, i.e. +21%.
# - On the LIGHT path, integer round-tripping through calibrate/warp/register
#   kept only ~55-70% of the 32-bit arm's extended faint contrast (NAN-region
#   contrast 4.8/2.4/3.9 vs 8.5/2.9/5.6 % of local sky, R/G/B) — lost
#   structure, not merely added noise.
#
# If a future rig genuinely cannot afford 32-bit, that is a new adaptation and
# needs its own written removal condition in BACKLOG.md — not a silent edit.
set -euo pipefail
cd "$(dirname "$0")"
fail() { echo "FAIL: $*" >&2; exit 1; }

# 1. no template or builder may pin set16bits
hits=$(grep -rn 'set16bits' --include='*.ssf' --include='*.tmpl' --include='*.sh' \
        --include='*.py' . | grep -vE 'check_bitdepth\.sh:' || true)
[ -z "$hits" ] || { echo "$hits" >&2; fail "set16bits is pinned above"; }

# 2. every master-building template must pin set32bits explicitly. Siril
#    PERSISTS the bit-depth setting across runs, so an unpinned script inherits
#    whatever ran last — the same non-determinism setcompress 0 is pinned for.
for t in siril/master_dark.ssf siril/master_bias.ssf siril/master_flat.ssf \
         siril/lights.ssf.tmpl; do
  grep -q '^set32bits' "$t" || fail "$t does not pin set32bits"
  grep -q '^setcompress 0' "$t" || fail "$t does not pin setcompress 0"
done

# 3. the builders that generate .ssf inline must pin it too
for b in run_undistort_pipeline.sh build_sky_flat.sh; do
  grep -q 'set32bits' "$b" || fail "$b does not pin set32bits in its generated .ssf"
done

echo "OK: no set16bits anywhere; all master templates and inline builders pin set32bits + setcompress 0"
