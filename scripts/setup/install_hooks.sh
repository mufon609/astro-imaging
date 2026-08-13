#!/usr/bin/env bash
# Install this repo's git hooks. `.git/hooks/` is machine-local and untracked, so
# the hooks live under scripts/setup/hooks/ and are installed from there — the
# same tracked-source-plus-installer pattern the darktable styles and the fitted
# lens model use, for the same reason: a fact that is not reproducible from
# tracked files is the bug (CLAUDE.md, Environment).
#
#   scripts/setup/install_hooks.sh [--check]
#
# --check verifies the installed hooks match the tracked sources and exits
# nonzero if they do not, without writing anything.

set -euo pipefail
REPO=$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)
SRC="$REPO/scripts/setup/hooks"
DST=$(git -C "$REPO" rev-parse --git-path hooks)

CHECK=0
[ "${1:-}" = "--check" ] && CHECK=1

rc=0
for src in "$SRC"/*; do
  name=$(basename "$src")
  dst="$DST/$name"
  if [ "$CHECK" = 1 ]; then
    if [ ! -f "$dst" ]; then
      echo "MISSING: $name is not installed" >&2; rc=1
    elif ! cmp -s "$src" "$dst"; then
      echo "STALE:   $name differs from the tracked source" >&2; rc=1
    else
      echo "ok:      $name"
    fi
  else
    install -m 755 "$src" "$dst"
    echo "installed: $name -> $dst"
  fi
done
exit "$rc"
