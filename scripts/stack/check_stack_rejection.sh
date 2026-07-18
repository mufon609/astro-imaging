#!/usr/bin/env bash
# Guard: every stack builder must get its integration rejection clause from the
# ONE shared function in stack_rejection.sh (doctrine-driven by sub count), so a
# deep stack is never under-rejected by a hard-coded default. Run it in CI /
# before a release. It fails if:
#   - the shared source lost a doctrine branch,
#   - a builder stopped calling stack_rejection_for, or
#   - any builder/template hard-writes a `rej <...>` on a `stack` line that
#     bypasses the function.
set -euo pipefail
cd "$(dirname "$0")"
fail() { echo "FAIL: $*" >&2; exit 1; }

for clause in 'rej p 0.2 0.1' 'rej w 3 3' 'rej g 0.3 0.05'; do
  grep -qF "$clause" stack_rejection.sh || fail "stack_rejection.sh lost the '$clause' branch"
done

for b in run_pipeline.sh run_undistort_pipeline.sh; do
  grep -q 'stack_rejection_for' "$b" || fail "$b does not call stack_rejection_for"
done

# A literal rejection on a LIGHT `stack` line (in a builder/template) bypasses
# the doctrine helper. Scope: light sequences only (name carries `light`/`lt`);
# calibration-master stacks (flats/darks/biases, e.g. `pp_fl`) keep their own
# winsorized rejection and are out of the doctrine's domain. The compose of
# clean sub-stacks uses `mean none` (the sub-stack rejection dead-end), which is
# not a `rej` and is allowed.
hard=$(grep -rnE 'stack +[A-Za-z_]*(light|lt)[A-Za-z_0-9]* +rej +[0-9wpgl]' --include='*.sh' --include='*.tmpl' . \
       | grep -vE 'stack_rejection\.sh:|check_stack_rejection\.sh:' || true)
[ -z "$hard" ] || { echo "FAIL: hard-coded stack rejection bypasses stack_rejection_for:" >&2
                    echo "$hard" >&2; exit 1; }

echo "OK: stack rejection is single-sourced; doctrine-driven by sub count (percentile <=6 / winsorized <=50 / GESD >50)"
