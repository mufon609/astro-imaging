#!/usr/bin/env bash
# THE INVENTORY GUARD: every `verify` command in scripts/setup/manifest.tsv must
# actually execute and exit 0.
#
#   scripts/qa/check_manifest_verify.sh            run every row's verify command
#   scripts/qa/check_manifest_verify.sh --selftest prove it can go RED
#
# WHY THIS EXISTS. `manifest.tsv` is the tracked answer to "what is installed on
# this rig and how do I confirm it", and CLAUDE.md's Environment section makes it
# load-bearing: a fact not reproducible from tracked files is the bug. The file
# has a `verify` column precisely so a reader can CHECK a row rather than trust
# it — and nobody had ever executed that column AS A SET.
#
# MEASURED WHEN IT FIRST RAN: 22 of 24 rows passed and TWO DID NOT.
#   Nightlight  rc=127  "nightlight: command not found"
#   lensfun     rc=1    "Info: root privileges needed for updating the system database."
# Neither tool was missing. `Nightlight`'s binary is installed at
# $OPT/nightlight-0.2.6/nightlight and is NOT on PATH, while its column said bare
# `nightlight version`; `lensfun-update-data` exits 1 unprivileged EVEN FOR
# --help, so that column could never pass as a non-root check. **Both rows
# asserted an install their own check could not confirm** — the same class as
# every other defect this repo measured today: a check whose mechanism cannot do
# what its column promises.
#
# WHAT IT DOES NOT DO, stated so a green run is not over-read:
# - It proves each row's verify command RUNS and exits 0. It does NOT prove the
#   row's VERSION, SHA or NOTES are accurate — a row can be honest about its
#   check and wrong about its contents.
# - It runs whatever column 6 contains. That column is tracked repo content, so
#   this is the same trust level as running any script here — but a row is a
#   place code can be added, and that is worth knowing.
# - Some rows verify PRESENCE only (`command -v`), which is weaker than running
#   the tool. That is deliberate where the tool needs root; the row says so.
set -uo pipefail          # NOT -e: every row must run even after one fails
REPO=$(cd "$(dirname "${BASH_SOURCE[0]}")"/../.. && pwd)
SCRATCH=$(mktemp -d "${TMPDIR:-/tmp}/manifest_verify.XXXXXX")
trap 'rm -rf "$SCRATCH"' EXIT
MANIFEST="$REPO/scripts/setup/manifest.tsv"

run_column() {            # <manifest-path> ; prints failures, returns count
  local mf="$1" tool cmd out rc bad=0 n=0
  while IFS=$'\t' read -r tool _ _ _ _ cmd _; do
    [ "$tool" = "tool" ] && continue          # header
    [ -z "${tool:-}" ] && continue
    n=$((n+1))
    # SHAPE FIRST. MEASURED GAP THIS CLOSES: a row written with SIX arguments
    # where the schema takes SEVEN shifts every field left — path lands in the
    # sha256 column, verify lands in path, notes land in verify — and the row
    # STILL PASSED this guard, because column 6 happened to hold a runnable
    # command. A verify that executes is not evidence the row is well formed.
    if [ "$(awk -F'\t' -v k="$tool" '$1==k{print NF; exit}' "$mf")" != "7" ]; then
      printf '  FAIL %-20s malformed row: %s fields, schema is 7 (tool version source sha256 path verify notes)\n' \
        "$tool" "$(awk -F'\t' -v k="$tool" '$1==k{print NF; exit}' "$mf")"
      bad=$((bad+1)); continue
    fi
    if [ -z "${cmd:-}" ]; then
      printf '  FAIL %-20s (no verify command)\n' "$tool"; bad=$((bad+1)); continue
    fi
    # RUN IN A SCRATCH CWD, NOT THE REPO ROOT. MEASURED: Nightlight's verify
    # command writes `out.log` into the CURRENT DIRECTORY, so running this column
    # from the repo root left an untracked file behind on EVERY run — a guard that
    # dirties the tree it guards, and one that `git status` then reports as a
    # mystery. A verify command is someone else's binary; assume side effects.
    out=$(cd "$SCRATCH" && eval "$cmd" 2>&1); rc=$?
    if [ $rc -ne 0 ]; then
      printf '  FAIL rc=%-4s %-20s %s\n' "$rc" "$tool" "$(printf '%s' "$out" | head -1 | cut -c1-70)"
      bad=$((bad+1))
    fi
  done < "$mf"
  printf '%s %s' "$n" "$bad" > /tmp/.cmv.$$
  return 0
}

if [ "${1:-}" = "--selftest" ]; then
  # POSITIVE CONTROL — required by CLAUDE.md: an acceptance measure ships with
  # data on which it MUST fire. A guard nobody has seen go RED is not a guard.
  tmp=$(mktemp)
  # NOTE: traps REPLACE, they do not accumulate — every trap here must re-list
  # SCRATCH or the scratch dir leaks on every run.
  trap 'rm -rf "$SCRATCH"; rm -f "$tmp" /tmp/.cmv.$$' EXIT
  head -1 "$MANIFEST" > "$tmp"
  printf 'planted\t0\tfixture\tnone\t/nonexistent\t/nonexistent/definitely-not-here --version\tplanted row that MUST fail\n' >> "$tmp"
  run_column "$tmp" >/dev/null
  read -r n bad < /tmp/.cmv.$$
  if [ "$bad" -lt 1 ]; then
    echo "  *** FAIL *** a planted unrunnable row did NOT fail — the guard cannot go RED"
    exit 1
  fi
  echo "  PASS  a planted unrunnable row FAILS ($bad of $n)"
  # and the real manifest must pass, or the control proves nothing about today
  run_column "$MANIFEST" >/dev/null
  read -r n bad < /tmp/.cmv.$$
  if [ "$bad" -ne 0 ]; then
    echo "  *** FAIL *** the real manifest has $bad failing row(s) of $n"
    exit 1
  fi
  echo "  PASS  the real manifest passes ($n rows)"
  echo "SELFTEST PASSED"
  exit 0
fi

trap 'rm -rf "$SCRATCH"; rm -f /tmp/.cmv.$$' EXIT
run_column "$MANIFEST"
read -r n bad < /tmp/.cmv.$$
if [ "$bad" -ne 0 ]; then
  printf 'check_manifest_verify: RED — %d of %d rows failed their own verify command\n' "$bad" "$n"
  exit 1
fi
printf 'OK: all %d manifest rows execute their verify command and exit 0.\n' "$n"
printf '    Scope: proves the CHECK runs, not that version/sha/notes are right.\n'
