#!/usr/bin/env bash
# Guard: every Siril invocation must route through the ONE shared invoker
# (scripts/lib/siril_run.{sh,py}), which serializes siril-cli behind an flock.
# Run it in CI / before a release. It fails if:
#   - the shared sources lost their lock,
#   - any script spawns `flatpak run --command=siril-cli` directly, or
#   - any python builds `SIRIL + [...]` into its own subprocess call.
#
# A bypass is not cosmetic: two siril-cli processes starting at once hit the
# flatpak instance-dir race (bwrap "Can't get type of source .../tmp"), which
# kills the caller mid-chain and prints nothing useful — measured once in ~150
# paired invocations. One bypassing caller is enough to reintroduce it, because
# an flock only serializes the processes that take it.
set -euo pipefail
REPO=$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)
cd "$REPO"
fail() { echo "FAIL: $*" >&2; exit 1; }

grep -q 'flock' scripts/lib/siril_run.sh || fail "siril_run.sh no longer takes the lock"
grep -q 'fcntl.flock' scripts/lib/siril_run.py || fail "siril_run.py no longer takes the lock"
grep -q 'SIRIL_LOCK' scripts/lib/siril_run.sh || fail "siril_run.sh lost its lock-path variable"

# The shell invoker itself is the ONE legitimate spawn site. x86_bootstrap.sh
# only prints probe strings for the operator (it drives no pipeline work).
raw=$(grep -rn 'flatpak run --command=siril-cli' --include='*.sh' . \
      | grep -vE 'scripts/lib/siril_run\.sh:|scripts/setup/x86_bootstrap\.sh:|check_siril_invoke\.sh:' || true)
[ -z "$raw" ] || { echo "FAIL: shell scripts spawn siril-cli directly, bypassing siril_cli():" >&2
                   echo "$raw" >&2; exit 1; }

# Any python building its own SIRIL argv is a bypass. There is no exemption:
# the one that existed (scripts/jwst/*, an archival chain maintained in parallel
# that had never adopted the invoker) is gone with that class, so the check is
# now unconditional and every hit is a real failure.
py=$(grep -rn 'SIRIL *+' --include='*.py' . \
     | grep -vE 'scripts/lib/siril_run\.py:' || true)
[ -z "$py" ] || { echo "FAIL: python builds its own siril-cli argv, bypassing siril_run.run():" >&2
                  echo "$py" >&2; exit 1; }

echo "OK: every pipeline Siril invocation is serialized through scripts/lib/siril_run.{sh,py}"
