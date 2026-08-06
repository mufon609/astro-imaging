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

# scripts/jwst/* is the archival-class chain, maintained in parallel; it has not
# adopted the invoker yet, so it is reported but not failed. Any OTHER python
# building its own SIRIL argv is a bypass.
py=$(grep -rn 'SIRIL *+' --include='*.py' . \
     | grep -vE 'scripts/lib/siril_run\.py:|scripts/jwst/' || true)
[ -z "$py" ] || { echo "FAIL: python builds its own siril-cli argv, bypassing siril_run.run():" >&2
                  echo "$py" >&2; exit 1; }

unadopted=$(grep -rln 'SIRIL *+' --include='*.py' scripts/jwst 2>/dev/null || true)
if [ -n "$unadopted" ]; then
  echo "NOTE: not yet routed through the shared invoker (cross-session protection"
  echo "      needs both sides to take the lock):"
  echo "$unadopted" | sed 's/^/        /'
fi

echo "OK: every pipeline Siril invocation is serialized through scripts/lib/siril_run.{sh,py}"
