#!/usr/bin/env bash
# THE PROMPT-SCOPE GUARD: every `.md` in `prompts/` declares its KIND, and the two
# kinds that every session reads at startup stay under a size ceiling.
#
#   scripts/qa/check_prompt_scope.sh            check the tree
#   scripts/qa/check_prompt_scope.sh --selftest prove it can go RED
#
# THE RULE IT ENFORCES LIVES IN `prompts/README.md`. Read that first — it carries
# the destination table (where a lesson goes instead of into a role doc), the
# discriminator that settles almost every case, and the measured history below.
# This file is only the mechanical part.
#
# WHY THIS EXISTS. `prompts/` was the one writable surface in this repo with no
# destination rule and no guard, so it became the sink for everything sessions
# learned. MEASURED, over one day:
#
#   PROJECT_MANAGER_PROMPT.md   419 -> 668 lines across 11 commits, then cut to 213
#   ORACLE_TEMPLATE.md          233 -> 565 lines,                   then cut to 222
#
# The role docs were not corrupted, they were DILUTED: at 555 lines the Oracle's
# stated reason for existing sat at LINE 455, behind 454 lines of "how you fail".
# No sentence in it was wrong. A fresh session reading top-down calibrates on the
# failure catalogue and never reaches the remit. That is invisible from inside,
# which is why it ran for a day and needed the owner to name it.
#
# STANDARDS-FIRST, AND THIS IS A DEVIATION RECORDED RATHER THAN AN INVENTION.
# The standard is DIATAXIS (Daniele Procida, https://diataxis.fr): partition docs
# by what the reader is DOING, on the claim that mixing modes degrades all of them
# and that the characteristic failure is accretion of EXPLANATION into
# INSTRUCTION. That is exactly the defect above. STATUS: DOCTRINE, source named,
# not measured here.
# **THE MEASURED CONSTRAINT THAT FORCES THE DEVIATION: Diataxis prescribes no
# enforcement, and no off-the-shelf linter checks file-scope mode purity.**
# `markdownlint`'s MD013 bounds LINE length, not file length or content class;
# Vale and textlint check prose style and terminology, never whether a paragraph
# belongs in the document it is sitting in. There is nothing for a standard
# validator to bind to. So this is a hand-rolled SIZE PROXY, and the honest
# statement is that it measures a correlate of the defect and not the defect. If a
# linter that classifies documentation mode ever ships, replace this with it.
#
# WHY TWO AXES. Line count alone is Goodhart-shaped — satisfiable by writing
# longer lines, and this directory already contains an 827-character line. Bytes
# are the backstop. Both are proxies.
#
# WHY 300 / 20000, calibrated against real data on BOTH sides:
#   ADVERSARY_TEMPLATE.md          98 lines   4,980 B   passes
#   WORKER_TEMPLATE.md            123 lines   7,247 B   passes
#   PROJECT_MANAGER_PROMPT.md     213 lines  13,147 B   passes
#   ORACLE_TEMPLATE.md            238 lines  13,494 B   passes
#   ORACLE_TEMPLATE.md @42e1f1e   565 lines  34,962 B   RED on both axes
#   PROJECT_MANAGER_PROMPT.md @deb4ef8  668 lines  45,494 B   RED on both axes
# 26% headroom in lines over the largest live role doc, 48% in bytes. And it fires
# where it should have: the Oracle's FIRST accretion commit that day took it
# 233 -> 362, which 300 catches.
#
# THE MARKER IS VISIBLE, NOT AN HTML COMMENT, AND THAT IS THE POINT. This
# directory's failure mode is text being cut without being read; an invisible
# marker is the first thing a cut loses.
#
# THE MARKER MUST BE IN THE FIRST 10 LINES, WHICH IS A REAL REQUIREMENT AND ALSO
# CLOSES A SELF-MATCH TRAP. `prompts/README.md` documents the marker and shows it
# in a fenced example, so a whole-file count reads THREE declarations in the file
# whose job is to define one. Scoping the declaration to the head makes the
# documentation inert without an exclusion rule that somebody has to remember —
# the same technique the registry records for the `pgrep` and
# `check_removal_conditions` self-match traps. Occurrences past line 10 are
# documentation by construction and are ignored; the head declaration governs.
#
# WHAT THIS STRUCTURALLY CANNOT SEE — read before treating GREEN as coverage.
# There are THREE holes and this guard covers NONE of them:
#   (a) WHETHER A SENTENCE IN A ROLE DOC HAS A FIRST HOME ELSEWHERE. That is the
#       actual defect. It is not greppable, and no metric should be invented to
#       stand in for it: a repo-local attempt to proxy "does this cite a source"
#       produced a count that FALSIFIED ITSELF ON COMMIT and generated the
#       opposite of the correct instruction.
#   (b) A DESTRUCTIVE CUT. 668 -> 213 passes every axis here while deleting
#       load-bearing text. `ced28ce` is the recorded instance: the cut kept the
#       prohibition "never report a negative from a structurally-impossible view"
#       and deleted every description of what makes a view structurally
#       impossible. The only defence is the destination rule, and it is prose.
#   (c) DILUTION UNDER THE CEILING. A 290-line role doc whose remit is at line 250
#       is the exact failure this exists to prevent, and it is GREEN.
# THE BOUND IS THE MORE USEFUL HALF: this catches unbounded ACCRETION, which is
# one of the three, and it is the only one of the three a machine can catch.
#
# AND ONE NAMED LOOPHOLE: `brief` and `register` carry no ceiling on purpose — a
# brief holds a full acceptance spec and then dies, a register is SUPPOSED to
# accumulate and shed. So text evicted from a role doc can be parked in an
# unceilinged brief that every session is then told to read. Nothing detects that.
# It is named so that doing it is a choice rather than a drift.
set -uo pipefail          # NOT -e: every file must be checked even after one fails
REPO=$(cd "$(dirname "${BASH_SOURCE[0]}")"/../.. && pwd)

HEAD_LINES=10
MAX_LINES=300
MAX_BYTES=20000
KNOWN_KINDS="contract role brief register"
CEILINGED="contract role"

# The declaration: a bold marker alone on its line, inside the head window.
MARK_RE='^\*\*PROMPT-KIND: [a-z]+\*\*$'

# The two real regressions this guard is calibrated on, with the sizes measured
# from them. If history is ever rewritten past these commits the selftest falls
# back to a synthesised fixture at the SAME size and says so out loud, rather
# than silently losing its positive control.
CTRL_PM_REF='deb4ef8:prompts/PROJECT_MANAGER_PROMPT.md'   ; CTRL_PM_LINES=668
CTRL_OR_REF='42e1f1e:prompts/ORACLE_TEMPLATE.md'          ; CTRL_OR_LINES=565

# SETS TWO GLOBALS AND RETURNS NOTHING ON STDOUT, DELIBERATELY. The obvious form
# — `kind=$(declared_kind "$f")` — runs the function in a SUBSHELL, so the marker
# COUNT it computes is discarded at the closing paren and the caller reads an
# unset `NMARK`. Measured here: the guard died on its own first fixture, and the
# arm that would have caught it (the unmarked file) is the one it died before
# reaching. Same class as an instrument that cannot see its own damage.
KIND="" ; NMARK=0
declared_kind() {         # <file> -> sets KIND ("" if not exactly one) and NMARK
  local f="$1"
  NMARK=$(head -n "$HEAD_LINES" "$f" | grep -cE "$MARK_RE")
  KIND=""
  [ "$NMARK" -eq 1 ] || return 0
  KIND=$(head -n "$HEAD_LINES" "$f" | grep -oE "$MARK_RE" \
         | sed -E 's/^\*\*PROMPT-KIND: //; s/\*\*$//')
}

# Tracked scope in the repo, plain glob in a fixture. Tracked is the right scope
# for a pre-push gate: you push what is tracked.
prompt_files() {          # <root>
  local root="$1"
  if [ -d "$root/.git" ]; then
    git -C "$root" ls-files 'prompts/*.md' | sed "s|^|$root/|"
  else
    ls -1 "$root"/prompts/*.md 2>/dev/null
  fi
}

NFILES=0 ; NOVER=0 ; NUNMARKED=0 ; NBAD=0
run_check() {             # <root> ; prints findings, sets the counters
  local root="$1" f kind lines bytes
  NFILES=0 ; NOVER=0 ; NUNMARKED=0 ; NBAD=0
  while read -r f; do
    [ -z "$f" ] && continue
    [ -f "$f" ] || continue
    NFILES=$((NFILES+1))
    declared_kind "$f" ; kind="$KIND"
    if [ -z "$kind" ]; then
      if [ "$NMARK" -eq 0 ]; then
        printf '  NO KIND       %-40s no **PROMPT-KIND: ...** line in the first %d lines\n' \
               "${f#"$root"/}" "$HEAD_LINES"
      else
        printf '  TWO KINDS     %-40s %d declarations in the first %d lines\n' \
               "${f#"$root"/}" "$NMARK" "$HEAD_LINES"
      fi
      NUNMARKED=$((NUNMARKED+1))
      continue
    fi
    case " $KNOWN_KINDS " in
      *" $kind "*) ;;
      *) printf '  BAD KIND      %-40s kind=%s not in {%s}\n' \
                "${f#"$root"/}" "$kind" "$KNOWN_KINDS"
         NBAD=$((NBAD+1)); continue ;;
    esac
    case " $CEILINGED " in *" $kind "*) ;; *) continue ;; esac
    lines=$(wc -l < "$f") ; bytes=$(wc -c < "$f")
    if [ "$lines" -gt "$MAX_LINES" ] || [ "$bytes" -gt "$MAX_BYTES" ]; then
      printf '  OVER CEILING  %-40s kind=%-8s lines=%-5s (max %d)  bytes=%-7s (max %d)\n' \
             "${f#"$root"/}" "$kind" "$lines" "$MAX_LINES" "$bytes" "$MAX_BYTES"
      NOVER=$((NOVER+1))
    fi
  done <<< "$(prompt_files "$root")"
  return 0
}

if [ "${1:-}" = "--selftest" ]; then
  # POSITIVE CONTROL — required by CLAUDE.md: an acceptance measure ships with
  # data on which it MUST fire. Two of the arms below run on the REAL historical
  # regressions rather than on invented fixtures, which is the strongest control
  # available: this guard is calibrated on the incident it exists to prevent.
  # The fixture lives under $HOME, never /tmp (the Siril flatpak has a private
  # /tmp) and never inside the repo, so a selftest run leaves the tree untouched.
  FIX=$(mktemp -d "${XDG_CACHE_HOME:-$HOME/.cache}/check_prompt_scope.XXXXXX") || exit 1
  trap 'rm -rf "$FIX"' EXIT
  mkdir -p "$FIX/prompts"
  fail=0

  # Stage a historical file WITH a valid marker injected, so the arm can only go
  # RED on the CEILING. Without the marker it would go RED on NO KIND and the arm
  # would prove the wrong thing.
  stage_ctrl() {          # <name> <gitref> <fallback-lines>
    # SPLIT DELIBERATELY: bash expands every word of a `local` before performing
    # any of its assignments, so `dest=...$name` on the same line reads an unset
    # `name` and dies under `set -u`. Measured here, not defensive style.
    local name="$1" ref="$2" n="$3"
    local dest="$FIX/prompts/$name"
    if git -C "$REPO" cat-file -e "$ref" 2>/dev/null; then
      { printf '# staged historical control\n**PROMPT-KIND: role**\n'
        git -C "$REPO" show "$ref"; } > "$dest"
      printf 'real'
    else
      { printf '# synthesised control (history unreachable for %s)\n' "$ref"
        printf '**PROMPT-KIND: role**\n'
        for _ in $(seq 1 "$n"); do printf 'filler line to reach the recorded size\n'; done
      } > "$dest"
      printf 'synth'
    fi
  }

  src_pm=$(stage_ctrl PM_REGRESSION.md   "$CTRL_PM_REF" "$CTRL_PM_LINES")
  src_or=$(stage_ctrl ORACLE_REGRESSION.md "$CTRL_OR_REF" "$CTRL_OR_LINES")
  [ "$src_pm" = synth ] && echo "  NOTE  historical control $CTRL_PM_REF unreachable — synthesised at $CTRL_PM_LINES lines"
  [ "$src_or" = synth ] && echo "  NOTE  historical control $CTRL_OR_REF unreachable — synthesised at $CTRL_OR_LINES lines"

  # A BYTE-AXIS fixture: comfortably under the line ceiling, over the byte one.
  # This is the arm that proves the anti-gaming backstop fires INDEPENDENTLY —
  # without it, a role doc could evade the guard by not wrapping.
  { printf '# byte axis\n**PROMPT-KIND: role**\n'
    for _ in $(seq 1 40); do head -c 600 /dev/zero | tr '\0' 'x'; printf '\n'; done
  } > "$FIX/prompts/LONGLINES.md"

  printf '# no marker anywhere\n\nbody\n'                       > "$FIX/prompts/UNMARKED.md"
  printf '# two\n**PROMPT-KIND: role**\n**PROMPT-KIND: brief**\n' > "$FIX/prompts/TWOKINDS.md"
  printf '# bad\n**PROMPT-KIND: rolez**\n'                      > "$FIX/prompts/BADKIND.md"
  # An unceilinged kind that is FAR over both numbers — proves the exemption is
  # real and that `brief`/`register` are not silently gated.
  { printf '# long brief\n**PROMPT-KIND: brief**\n'
    for _ in $(seq 1 900); do printf 'a brief may legitimately be long and then die\n'; done
  } > "$FIX/prompts/LONG_BRIEF.md"

  run_check "$FIX" > "$FIX/out1" 2>&1

  # (1) RED on the real 668-line PM regression, on the CEILING and not on a marker.
  if grep -q 'OVER CEILING .*PM_REGRESSION' "$FIX/out1"; then
    echo "  PASS  the $CTRL_PM_LINES-line PM regression goes RED on the ceiling ($src_pm history)"
  else
    echo "  *** FAIL *** the PM regression did not go RED on the ceiling"; cat "$FIX/out1"; fail=1
  fi

  # (2) RED on the real 565-line Oracle regression.
  if grep -q 'OVER CEILING .*ORACLE_REGRESSION' "$FIX/out1"; then
    echo "  PASS  the $CTRL_OR_LINES-line Oracle regression goes RED on the ceiling ($src_or history)"
  else
    echo "  *** FAIL *** the Oracle regression did not go RED on the ceiling"; cat "$FIX/out1"; fail=1
  fi

  # (3) the byte axis fires on its own, with lines well under the ceiling.
  if grep -qE 'OVER CEILING .*LONGLINES.*lines=4[0-9] ' "$FIX/out1"; then
    echo "  PASS  the byte axis fires independently (42 lines, >$MAX_BYTES bytes)"
  else
    echo "  *** FAIL *** the byte-axis fixture did not go RED with lines under the ceiling"
    grep LONGLINES "$FIX/out1"; fail=1
  fi

  # (4) fails CLOSED on an undeclared file — the hole the register calls the worse case.
  if grep -q 'NO KIND .*UNMARKED' "$FIX/out1"; then
    echo "  PASS  a file with no kind declaration goes RED (fails closed)"
  else
    echo "  *** FAIL *** an unmarked file was not reported"; fail=1
  fi

  # (5) ambiguity is RED, not first-wins.
  if grep -q 'TWO KINDS .*TWOKINDS' "$FIX/out1"; then
    echo "  PASS  two declarations in the head go RED rather than first-wins"
  else
    echo "  *** FAIL *** a doubly-declared file was not reported"; fail=1
  fi

  # (6) an unknown kind is RED — a typo must not silently buy an exemption.
  if grep -q 'BAD KIND .*BADKIND' "$FIX/out1"; then
    echo "  PASS  an unknown kind goes RED (a typo cannot buy an exemption)"
  else
    echo "  *** FAIL *** an unknown kind was not reported"; fail=1
  fi

  # (7) the exemption is REAL: a 900-line brief is clean.
  if grep -q 'LONG_BRIEF' "$FIX/out1"; then
    echo "  *** FAIL *** an unceilinged kind was gated"; grep LONG_BRIEF "$FIX/out1"; fail=1
  else
    echo "  PASS  a 900-line \`brief\` is clean — the exemption is real, not accidental"
  fi

  # (8) GREEN — remove every offender and the same fixture comes back clean.
  rm -f "$FIX"/prompts/{PM_REGRESSION,ORACLE_REGRESSION,LONGLINES,UNMARKED,TWOKINDS,BADKIND}.md
  run_check "$FIX" > "$FIX/out2" 2>&1
  if [ $((NOVER+NUNMARKED+NBAD)) -eq 0 ] && [ "$NFILES" -gt 0 ]; then
    echo "  PASS  the cleaned fixture comes back GREEN ($NFILES file(s), 0 findings)"
  else
    echo "  *** FAIL *** the cleaned fixture was not GREEN"; cat "$FIX/out2"; fail=1
  fi

  [ "$fail" -ne 0 ] && exit 1
  echo "SELFTEST PASSED"
  exit 0
fi

run_check "$REPO"
NFIND=$((NOVER+NUNMARKED+NBAD))
if [ "$NFIND" -ne 0 ]; then
  printf '\ncheck_prompt_scope: RED — %d finding(s) across %d files in prompts/.\n' "$NFIND" "$NFILES"
  printf '  The rule and the destination table are in prompts/README.md.\n'
  printf '  OVER CEILING is not "trim it": something must LEAVE, and the destination\n'
  printf '  table says where. Migrate FIRST, in the same commit, then cut — a cut that\n'
  printf '  kept a prohibition and deleted its detector is the recorded instance.\n'
  exit 1
fi
printf 'OK: %d files in prompts/, every kind declared, every ceilinged doc within %d lines / %d bytes.\n' \
       "$NFILES" "$MAX_LINES" "$MAX_BYTES"
printf '    Scope: this detects unbounded ACCRETION only. It is structurally blind to\n'
printf '    (a) whether a sentence has a first home elsewhere — the actual defect, and\n'
printf '        not greppable; do not invent a metric for it,\n'
printf '    (b) a destructive CUT, which passes every axis here, and\n'
printf '    (c) dilution UNDER the ceiling — a 290-line doc with its remit at line 250.\n'
printf '    `brief` and `register` are unceilinged by design, so text evicted from a\n'
printf '    role doc can be parked in a brief every session is told to read. Named in\n'
printf '    prompts/README.md so that doing it is a choice rather than a drift.\n'
