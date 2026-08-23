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
# THE RETRY — the complement this file's own note reserved for "a
# non-participating third party", now built, because that party turned up.
# MEASURED: two full undistort builds died mid-chunk with
#   error: Extension org.freedesktop.Platform.GL.default has invalid merge-dirs
# from `flatpak run` itself. Siril never started, so the lock cannot prevent it —
# there is no second siril-cli to serialize against. NOT REPRODUCIBLE ON DEMAND:
# 0 failures in 55 locked invocations under concurrent `flatpak list`/`info` AND
# concurrent `flatpak run`, 0 across a 100-minute 1454-frame build, so the
# concurrency hypothesis is REFUTED and the trigger is unidentified. What is
# certain is the SAFETY of retrying it: the launcher refused to start the app, so
# nothing ran and no partial state exists to re-do.
#
# THE DISCRIMINATOR, and it is the whole design. A launch failure and a genuine
# Siril script failure BOTH exit 1, so the exit code cannot separate them, and
# the note above was right that the output is unreachable — the caller has
# already redirected it. What IS reachable is Siril's own config ini: Siril
# rewrites it at the end of every run it reaches. MEASURED on this rig, with the
# positive control the acceptance rule demands:
#   A  siril ran, script OK ......................... exit 0, ini mtime CHANGED
#   B  siril ran, script FAILED (load a missing file)  exit 1, ini mtime CHANGED
#   C  launch FAILED, siril never ran (positive control,
#      `flatpak run` against an uninstalled app) ....  exit 1, ini mtime UNCHANGED
# So an UNCHANGED mtime after a non-zero exit means Siril never started. B is the
# case that must never be retried — re-running a failing script wastes the whole
# stack and can double side effects — and it is exactly the case the ini
# separates. Nanosecond mtime (`stat -c %y`) is used, not whole seconds, so two
# runs inside one second cannot alias B into C.
#
# RETRY REMOVAL CONDITION: retire the retry when `flatpak run` stops failing to
# launch an installed app — i.e. when this rig completes a full-session build
# with SIRIL_LAUNCH_TRIES=1 and no launch failure in the logs. It is bounded
# (SIRIL_LAUNCH_TRIES, default 4) and every attempt is announced, so a launcher
# that is quietly degrading shows up in the build log instead of hiding.
#
# REMOVAL CONDITION: flatpak fixes the instance-dir lifecycle race, or Siril
# invocations stop being per-frame process spawns (e.g. pyscript batching), so
# there is no longer a window to collide in.

SIRIL_LOCK=${SIRIL_LOCK:-$HOME/.cache/astro-imaging/siril-cli.lock}
# Total attempts, not extra ones. 1 disables the retry (and is how the removal
# condition above is tested).
SIRIL_LAUNCH_TRIES=${SIRIL_LAUNCH_TRIES:-4}
SIRIL_CONFIG_INI=${SIRIL_CONFIG_INI:-$HOME/.var/app/org.siril.Siril/config/siril/config.1.4.ini}

siril_cli() {
  local rc try=1 before after
  mkdir -p "$(dirname "$SIRIL_LOCK")"
  while :; do
    # Read BEFORE taking the lock is wrong — another holder could write the ini
    # between the read and our run and alias its work into ours. Inside the lock,
    # ours is the only Siril that can touch it.
    rc=0
    # append-open: never truncates, and the fd is what carries the lock
    exec {_SIRIL_FD}>>"$SIRIL_LOCK"
    if ! flock -n "$_SIRIL_FD" 2>/dev/null; then
      echo "[siril_cli] another Siril job holds the lock — waiting (BACKLOG:removal-conditions)" >&2
      flock "$_SIRIL_FD"
    fi
    before=$(stat -c %y "$SIRIL_CONFIG_INI" 2>/dev/null || echo absent)
    flatpak run --command=siril-cli org.siril.Siril "$@" || rc=$?
    after=$(stat -c %y "$SIRIL_CONFIG_INI" 2>/dev/null || echo absent)
    exec {_SIRIL_FD}>&-        # closing the fd releases the lock
    [ "$rc" -eq 0 ] && return 0
    # Siril reached its exit and rewrote the ini => it RAN. Whatever failed is
    # Siril's or the script's, and re-running it would repeat real work.
    [ "$after" = "$before" ] || return "$rc"
    if [ "$try" -ge "$SIRIL_LAUNCH_TRIES" ]; then
      echo "[siril_cli] flatpak failed to LAUNCH Siril $try time(s) running (exit $rc); Siril never started, so no work was done — giving up" >&2
      return "$rc"
    fi
    echo "[siril_cli] flatpak failed to LAUNCH Siril (exit $rc) — Siril never started (config ini untouched), nothing to re-do; retry $((try+1))/$SIRIL_LAUNCH_TRIES" >&2
    try=$((try + 1)); sleep "$try"
  done
}

# REPORT-ON-FAILURE wrapper — the second half of the same defect. Every builder
# writes Siril's output to a log (`siril_cli ... >> "$LOG" 2>&1`), so under
# `set -e` a failure kills the caller with NOTHING on the caller's own stderr:
# the build stops mid-step and reads as a mystery rather than a tool failure.
# MEASURED: two undistort builds died exactly that way, and the cause was only
# recoverable by opening the work-dir log by hand. This is the same defect the
# darktable path already fixed by keeping dt_last.log and printing its tail on
# WARP FAILED; the Siril path never got the treatment.
#
#   sir(){ siril_run_logged "$P" "$1" "$P/siril.log"; }
#
# The redirection applies to the siril_cli call ONLY, so the tail goes to the
# CALLER's stderr — the build log — which is the surface that was blank.
siril_run_logged() {   # <workdir> <siril script> <logfile>
  local wd=$1 ssf=$2 log=$3 rc=0
  mkdir -p "$(dirname "$log")"
  siril_cli -d "$wd" -s "$ssf" >> "$log" 2>&1 || rc=$?
  [ "$rc" -eq 0 ] && return 0
  echo "SIRIL FAILED (exit $rc) on $(basename "$ssf") — last lines of $log:" >&2
  tail -12 "$log" >&2
  return "$rc"
}
