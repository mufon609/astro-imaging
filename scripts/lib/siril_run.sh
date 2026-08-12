#!/usr/bin/env bash
# Single source of truth for INVOKING Siril, shared by every script that drives
# it — the invocation counterpart to calibrate_light.sh (the command) and
# stack_rejection.sh (the rejection clause).
#
#   source scripts/lib/siril_run.sh
#   siril_cli -d "$WORKDIR" -s "$SCRIPT"        # exactly the siril-cli args
#
# The caller keeps its own redirection: `siril_cli -d "$W" -s "$1" >> log 2>&1`.
#
# WHY THIS EXISTS. The flatpak Siril tears down its per-app instance dir when a
# short-lived instance exits exactly as another is starting its sandbox:
#
#   bwrap: Can't get type of source /run/user/1000/.flatpak/org.siril.Siril/tmp:
#   No such file or directory
#
# MEASURED once in ~150 paired invocations, from two concurrent siril-cli loops.
# It kills the caller mid-chain (`set -e`), and the failing script prints
# NOTHING — the bwrap line lands in the siril log — so it reads as a data or
# Siril bug hours into a run. It is neither: it is a flatpak instance-dir
# lifecycle race, and the fix is to never have two siril-cli processes starting
# at once.
#
# HOW. An exclusive flock on ONE well-known file, held for the lifetime of each
# siril-cli process. The lock is advisory but every invocation in this repo
# routes through here, so the only way to race is to bypass this function —
# which scripts/stack/check_siril_invoke.sh exists to catch.
#
# The lock is released by the KERNEL when the holding process dies, crash
# included, so a stale lock cannot persist and the wait is unbounded ON PURPOSE:
# waiting is the correct behaviour (a long stack legitimately holds it for an
# hour), and there is no failure mode where waiting forever is worse than
# proceeding unserialized. A one-line notice prints when a wait actually starts,
# so a chain that looks stalled is legible.
#
# CROSS-SESSION SCOPE: the lock file is per-USER, not per-checkout, so any other
# process on this rig that routes through this helper (or takes the same lock)
# is serialized against us too. A process that does NOT take it is invisible to
# this mechanism — protection requires participation from both sides.
#
# The alternative candidate was a bounded RETRY on the bwrap signature. Not
# chosen: it recovers after the fact rather than preventing, and detecting the
# signature means parsing a log the caller has already redirected somewhere this
# function cannot see. Retry remains the complement for a non-participating
# third party, and would be its own change.
#
# REMOVAL CONDITION: flatpak fixes the instance-dir lifecycle race, or Siril
# invocations stop being per-frame process spawns (e.g. pyscript batching), so
# there is no longer a window to collide in.

SIRIL_LOCK=${SIRIL_LOCK:-$HOME/.cache/astro-imaging/siril-cli.lock}

siril_cli() {
  local rc=0
  mkdir -p "$(dirname "$SIRIL_LOCK")"
  # append-open: never truncates, and the fd is what carries the lock
  exec {_SIRIL_FD}>>"$SIRIL_LOCK"
  if ! flock -n "$_SIRIL_FD" 2>/dev/null; then
    echo "[siril_cli] another Siril job holds the lock — waiting (BACKLOG:removal-conditions)" >&2
    flock "$_SIRIL_FD"
  fi
  flatpak run --command=siril-cli org.siril.Siril "$@" || rc=$?
  exec {_SIRIL_FD}>&-          # closing the fd releases the lock
  return $rc
}
