#!/usr/bin/env bash
# wait_for.sh — wait for processes matching a pattern, WITHOUT matching yourself.
#
#   wait_for.sh <pattern> [--interval=30] [--timeout=0] [--selftest]
#
# THE TRAP THIS EXISTS TO REMOVE, measured twice at seven hours of wall-clock:
#
#     while pgrep -f build_arms.sh > /dev/null; do sleep 30; done
#
# looks correct and never terminates. `pgrep -f` matches against the full command
# line, and the waiting shell's OWN command line contains the pattern — so the
# loop finds itself, forever. Worse with two waiters: each matches the other, so
# killing one is not enough. A session hit this twice in one run after the same
# shape had already stranded four immortal shells in an earlier one.
#
# THE FIX IS STRUCTURAL, NOT CAREFUL. Resolve the pattern to PIDs ONCE, excluding
# this process and every ancestor of it, then wait on those PIDs with `kill -0`,
# which cannot self-match because it takes a number rather than a string. If
# nothing matches at resolve time, there is nothing to wait for and we say so and
# exit 0 — a waiter that blocks on an already-finished job is the same seven
# hours in a different costume.
#
# Deliberate semantics: it waits for the processes that existed WHEN IT STARTED,
# not for "no process ever matches again". That is predictable, and it is what a
# caller waiting on a known job actually means.

set -euo pipefail

PATTERN=""; INTERVAL=30; TIMEOUT=0; SELFTEST=0
for a in "$@"; do case "$a" in
  --interval=*) INTERVAL=${a#*=} ;;
  --timeout=*)  TIMEOUT=${a#*=} ;;
  --selftest)   SELFTEST=1 ;;
  -*) echo "unknown arg $a" >&2; exit 2 ;;
  *) PATTERN=$a ;;
esac; done

# Every PID from here up to init. ANCESTORS ONLY — see resolve(), which also has
# to handle descendants, and finding that out required running the thing.
self_tree() {
  local p=$$
  while [ -n "$p" ] && [ "$p" -gt 1 ] 2>/dev/null; do
    printf '%s\n' "$p"
    p=$(ps -o ppid= -p "$p" 2>/dev/null | tr -d ' ')
  done
}

# pattern -> PIDs, with this process's whole tree removed.
#
# SELF AND ANCESTORS IS NOT ENOUGH, which the selftest found and no amount of
# reasoning had: a SUBSHELL inherits its parent's command line, so every child
# this script spawns while resolving — the right-hand side of a pipe, a command
# substitution — ALSO matches the pattern. Measured while building this: pgrep
# returned three hits for a marker with no job running, one ancestor, one self,
# and one descendant that did not exist when the exclusion list was built.
#
# EXCLUDING BY PROCESS GROUP WAS ALSO WRONG, and the selftest caught that too: a
# job the CALLER launched from the same shell shares our PGID, so a PGID rule
# refuses to wait on exactly the job it was asked about. Two wrong exclusion
# rules in a row, both found by running step 3 rather than by thinking about it.
#
# The precise rule is COMMAND-LINE IDENTITY. A subshell matches because it
# INHERITS our command line verbatim, so anything whose /proc cmdline equals ours
# is us; a real job's cmdline is the job's, and differs. Ancestors keep their own
# explicit walk, since a parent `bash -c` carrying the pattern has a different
# cmdline from ours.
cmdline_of() { tr '\0' ' ' < "/proc/$1/cmdline" 2>/dev/null; }

resolve() {
  local pat=$1 excl mycmd
  excl=$(self_tree | paste -sd'|' -)
  mycmd=$(cmdline_of $$)
  pgrep -f -- "$pat" 2>/dev/null | while read -r pid; do
    printf '%s\n' "$pid" | grep -Eq "^(${excl})$" && continue
    [ "$(cmdline_of "$pid")" = "$mycmd" ] && continue
    printf '%s\n' "$pid"
  done || true
}

if [ "$SELFTEST" = 1 ]; then
  echo "wait_for --selftest"
  MARK="wait_for_selftest_marker_$$"
  SELF=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/$(basename "${BASH_SOURCE[0]}")
  # 1. FALSIFICATION — reproduce the trap faithfully. The bug needs the PATTERN
  #    to be in the WAITER'S OWN command line, which only happens when a shell is
  #    invoked with the pattern written into it. An earlier version of this test
  #    generated the marker inside the script, where it never reaches any command
  #    line, so `pgrep` correctly found nothing and the test "failed" while the
  #    real bug was untouched — a fixture that could not reproduce the defect it
  #    was written to demonstrate.
  naive=$(bash -c "pgrep -f -- '$MARK' | wc -l" | tr -d ' ')
  if [ "$naive" -gt 0 ]; then
    echo "  PASS  naive 'pgrep -f' finds $naive match with NO such job running -> it matched itself"
  else
    echo "  FAIL  could not reproduce the self-match; this selftest proves nothing" >&2; exit 1
  fi
  # 2. the resolver, called from a shell whose command line carries the marker,
  #    must see through it and report nothing to wait for
  out=$(bash -c "bash '$SELF' '$MARK' --interval=1 --timeout=5" 2>&1)
  if printf '%s' "$out" | grep -q 'not waiting'; then
    echo "  PASS  resolver called from a marker-carrying shell excludes self+ancestors"
  else
    echo "  FAIL  resolver did not exclude its own tree: $out" >&2; exit 1
  fi
  # 3. and it must still find a REAL job, so it is not just always-empty
  sleep 5 &
  real=$!
  found=$(resolve "sleep 5" | grep -c "^${real}$" || true)
  kill "$real" 2>/dev/null || true; wait "$real" 2>/dev/null || true
  [ "$found" = 1 ] && echo "  PASS  resolver finds a real matching job (pid $real)" \
                   || { echo "  FAIL  resolver missed a live job" >&2; exit 1; }
  echo "SELFTEST PASS"; exit 0
fi

[ -n "$PATTERN" ] || { echo "usage: wait_for.sh <pattern> [--interval=N] [--timeout=N]" >&2; exit 2; }

PIDS=$(resolve "$PATTERN")
if [ -z "$PIDS" ]; then
  echo "[wait_for] nothing matches '$PATTERN' — not waiting"
  exit 0
fi
echo "[wait_for] waiting on: $(printf '%s ' $PIDS)"

start=$SECONDS
while :; do
  alive=""
  for p in $PIDS; do kill -0 "$p" 2>/dev/null && alive="$alive $p"; done
  [ -n "$alive" ] || break
  if [ "$TIMEOUT" -gt 0 ] && [ $((SECONDS - start)) -ge "$TIMEOUT" ]; then
    echo "[wait_for] TIMEOUT after ${TIMEOUT}s; still alive:$alive" >&2
    exit 1
  fi
  sleep "$INTERVAL"
done
echo "[wait_for] done after $((SECONDS - start))s"
