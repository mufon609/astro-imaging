#!/usr/bin/env bash
# Guard: every light-frame calibration must route through the ONE shared command
# in calibrate_light.sh (which injects the mandatory -cc=dark cosmetic hot/cold-
# pixel correction). Run it in CI / before a release. It fails if:
#   - the shared source lost -cc=dark,
#   - a builder stopped calling calibrate_light_cmd, or
#   - any builder/template hand-writes a light calibrate (`calibrate light|c
#     -dark=...`) that bypasses the function.
# That last case is exactly how the undistort builder once dropped -cc=dark and
# shipped walking noise: a second, hand-written calibrate line that silently
# diverged from the documented one.
set -euo pipefail
cd "$(dirname "$0")"
fail() { echo "FAIL: $*" >&2; exit 1; }

grep -q -- '-cc=dark 3 3' calibrate_light.sh \
  || fail "calibrate_light.sh no longer injects -cc=dark 3 3"

for b in run_pipeline.sh run_undistort_pipeline.sh; do
  grep -q 'calibrate_light_cmd' "$b" || fail "$b does not call calibrate_light_cmd"
done

# A LIGHT calibrate uses sequence name 'light' or 'c'; flats/darks use other
# names and legitimately calibrate without -cc. Any hand-written light calibrate
# outside the shared function (and this guard) is a divergence.
hand=$(grep -rnE 'calibrate +(light|c) +-dark=' --include='*.sh' --include='*.tmpl' . \
       | grep -vE 'calibrate_light\.sh:|check_calibrate\.sh:' || true)
[ -z "$hand" ] || { echo "FAIL: hand-written light calibrate bypasses calibrate_light_cmd:" >&2
                    echo "$hand" >&2; exit 1; }

echo "OK: light calibration is single-sourced; -cc=dark enforced across all builders"
