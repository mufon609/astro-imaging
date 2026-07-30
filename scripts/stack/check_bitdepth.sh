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
#
# WHAT THIS GUARD DOES AND DOES NOT PROVE. It is a STATIC, per-FILE check over
# the whole scripts/ tree. It proves no product builder is missing the pin
# entirely. It does NOT prove that every individual generated .ssf inside a
# multi-.ssf builder carries it — a builder that already pins set32bits in one
# emission passes even if a newly added emission omits it. Per-emission-block
# granularity needs real parsing of the printf/heredoc blocks; it is BACKLOG.
# Two earlier holes are closed: the search root was `dirname $0` = scripts/stack,
# so FIVE live `set16bits` pins under scripts/qa and scripts/darktable were
# invisible to a check whose message claimed "no set16bits anywhere"; and the
# product-builder list named 2 of the 9 scripts that write image products, so
# spcc_run.py — which writes stack_<set>_spcc.fit, the render tier's own input —
# was unpinned and unchecked.
set -euo pipefail
cd "$(dirname "$0")/../.."          # repo root: the whole tree, not one stage dir
fail() { echo "FAIL: $*" >&2; exit 1; }
S=scripts

# 1. no script may pin set16bits, except these THREE, each for a stated reason
#    that makes 32-bit buy nothing. Anything else is a FAIL. An exemption is a
#    claim about where the leg TERMINATES, so re-check it if that changes.
#    - qa/coverage_probe.sh: the coverage MAP instrument. Its members are
#      `fill 1000` constant twins and the map is an integer count x 1000, which
#      16 bits holds exactly; it switches to set32bits before the sum stack. Not
#      a deliverable, and float would not make an integer count more exact.
#    - qa/run_frame_qa.sh: analysis-only `register -2pass` pass. It saves no
#      product — only the tool's regdata is kept — and the inputs are 14-bit
#      raws, which 16 bits holds exactly.
#    - darktable/fit_lens_model.sh: its calibrate leg terminates in `savetif8`
#      for Hugin's feature matcher, so the leg's precision is capped at 8 bits
#      downstream regardless. (The FITTED model does shape products, but through
#      star CORRESPONDENCE geometry, whose precision is SNR-limited, not
#      quantization-limited.)
EXEMPT='qa/coverage_probe\.sh|qa/run_frame_qa\.sh|darktable/fit_lens_model\.sh'
hits=$(grep -rn 'set16bits' --include='*.ssf' --include='*.tmpl' --include='*.sh' \
        --include='*.py' "$S" | grep -vE "check_bitdepth\.sh:|$EXEMPT" || true)
[ -z "$hits" ] || { echo "$hits" >&2; fail "set16bits is pinned above (not an exempt instrument)"; }

# 2. every master-building template must pin set32bits explicitly. Siril
#    PERSISTS the bit-depth setting across runs, so an unpinned script inherits
#    whatever ran last — the same non-determinism setcompress 0 is pinned for.
for t in $S/stack/siril/master_dark.ssf $S/stack/siril/master_bias.ssf \
         $S/stack/siril/master_flat.ssf $S/stack/siril/lights.ssf.tmpl; do
  grep -q '^set32bits' "$t" || fail "$t does not pin set32bits"
  grep -q '^setcompress 0' "$t" || fail "$t does not pin setcompress 0"
done

# 3+4. EVERY script that generates an .ssf which WRITES an image product must pin
#    set32bits AND setcompress 0. This list was verified by reading what each
#    script emits, not by grepping for the word "stack" (which also appears in
#    every stack_*.fit path and in prose, and produced a false inventory).
#    COMMENT LINES ARE STRIPPED FIRST. Searching the raw file matches a pin that
#    only exists in prose — caught by mutation-testing this very guard: deleting
#    the real `"set32bits\n"` emission from spcc_run.py left the word in the
#    comment ABOVE it and the check still passed. That is the registry's own
#    lesson ("a corrected comment fails silently, a guard fails loudly") turned
#    on the guard itself, so it is asserted here rather than trusted.
#    ONE awk process, deliberately not `grep -v ... | grep -q`: under the
#    `set -o pipefail` this script runs with, `grep -q` exits as soon as it
#    matches, the upstream grep takes SIGPIPE (141), and the pipeline reports
#    FAILURE for a file that PASSES — nondeterministically, depending on how
#    early the match lands. That made this guard report a false FAIL on
#    render_tier.sh on one run and pass on the next.
emits() {   # emits <file> <needle> — needle present on a non-comment line
  awk -v n="$2" '!/^[[:space:]]*#/ && index($0, n) { found = 1 } END { exit !found }' "$1"
}
for b in stack/run_pipeline.sh stack/run_undistort_pipeline.sh \
         stack/run_undistort_groups.sh stack/run_undistort_compose.sh \
         stack/build_sky_flat.sh stack/compose.py stack/render_tier.sh \
         stack/finish_render.sh calibrate/spcc_run.py; do
  emits "$S/$b" 'set32bits'   || fail "$S/$b writes an image product but never EMITS set32bits (a mention in a comment does not count)"
  emits "$S/$b" 'setcompress 0' || fail "$S/$b does not EMIT setcompress 0"
done

cat <<EOF
OK: no set16bits outside the 3 documented instrument exemptions;
    4 master templates pin set32bits + setcompress 0;
    9 product builders pin set32bits + setcompress 0.
    Scope: per-FILE and static — it does not prove every individual generated
    .ssf inside a multi-.ssf builder carries the pin (BACKLOG).
EOF
