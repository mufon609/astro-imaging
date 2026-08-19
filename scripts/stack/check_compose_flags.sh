#!/usr/bin/env bash
# Guard: every emitted compose/finish command DETERMINES the two parameters
# whose defaults are wrong for the product it is building — the union canvas's
# detection crop (`--central`) and the multi-night compose's registration
# reference (`--ref`). Run it in CI / before a release.
#
# WHY. Both are CALLER-SUPPLIED and both have a silent default that is correct
# for the common case and wrong for the deep one, so the lower layer knows the
# rule and the upper layer has to remember it:
#
#   --central  solve_field.py's own docstring: a framing=max union canvas has
#              coverage SEAMS that false-detect, and brightest-first selection
#              on a Milky-Way field clusters the star list in the band so an
#              order-3 SIP (20 free parameters per axis) extrapolates freely in
#              the corners. Omitted, the union solve starves. MEASURED on the
#              four-night corpus: logodds 63 against a confident floor of 100.
#              web/serve.py already derives it from the product tag; the shell
#              emitters do not, which is the divergence this guard names.
#   --ref      run_undistort_compose.sh's own header: `register -2pass`'s AUTO
#              reference sets the output canvas ORIENTATION and, through
#              `-norm=addscale`, the composite's raw channel BALANCE. Within one
#              night the members share a balance family and the auto pick is
#              harmless; across NIGHTS the families genuinely differ (measured
#              on this rig: K_G 0.662-0.668 one night vs 0.697 another, both
#              chain-clean), so the auto pick silently decides the composite's
#              starting balance from argument order. Measured cost of the wrong
#              family: K_B 0.846 with a rotated frame map, against 0.951 and an
#              exact map from the right reference.
#
# SCOPE — per COMMAND, not per file, for the shell emitters (section A). The
# same reason check_registration_pins.sh gives: an emitter that determines a
# parameter in one emission must not hide a second that does not. Section B is
# weaker BY CONSTRUCTION and says so: a python emitter builds an argv LIST, not
# a command line, so it is judged per FILE on whether the derivation is present.
#
# WHAT IT DOES NOT PROVE. That the command an emitter builds is the one that
# ran (a runtime override, an operator's hand-written invocation) — the same
# limit check_registration_pins.sh states. And it judges the CALLER: it cannot
# see a parameter the callee derives for itself. It also checks that the flag is
# PRESENT, never that its value RESOLVES: `--ref=""` passes here (found while
# fire-testing this guard green, where a substitution left the value empty).
# The callee validates the value — run_undistort_compose.sh resolves --ref to a
# linked index and aborts if it does not resolve; solve_field.py refuses a
# --central outside (0,1). Presence is this guard's question; validity is theirs.
#
# AMENDMENT CONDITION, and it is not hypothetical — it is the next unit of this
# same work. Deriving `--central` / `--ref` INSIDE the callee (from the union's
# zero-coverage rims and from the members' DATE-OBS spread) makes the caller's
# flag unnecessary, at which point RULE 1 and RULE 2 become FALSE as written:
# they would fail a correct tree. When that lands, the rules move from "the
# caller passes it" to "the callee derives it", and the assertion becomes the
# presence of the derivation site plus a caller override that still parses.
# Do not delete this guard then — re-point it, or it takes its coverage with it.
#
# WHAT COUNTS AS A COMMAND. Shell prose and shell commands both name these
# scripts in these files: run_set_chain.sh prints three `say "  5.
# scripts/stack/finish_render.sh ..."` operator instructions, and
# check_bitdepth.sh carries both script names inside a `for f in ...` list.
# After comments are stripped and `\`-continuations joined, a COMMAND is a
# logical line whose FIRST token resolves to the target script; `say`, `echo`
# and `for` are first tokens that do not, so prose is excluded by the same
# shape test rather than by a list of exceptions.
set -euo pipefail
cd "$(dirname "$0")/../.."          # repo root: the whole tree, not one stage dir
fail() { echo "FAIL: $*" >&2; exit 1; }

# THE COMPOSER REGISTER. Whether a compose spans nights is not readable off the
# command line — both forms are `run_undistort_compose.sh --out= --framing= <dirs>`
# and the dirs are shell arrays — so it is DECLARED here and the declaration is
# asserted COMPLETE below: a new composer that is in neither list fails this
# guard rather than defaulting into the harmless class. That completeness check
# is the whole reason this is a register and not a heuristic.
MULTINIGHT='scripts/stack/run_corpus_combine.sh'          # <session-dir>... , >= 2 group dirs across nights
SINGLENIGHT='scripts/stack/run_session_chain.sh web/serve.py'  # one session, loops its SETS

listed_in() { case " $2 " in *" $1 "*) return 0;; esac; return 1; }

# ---- extraction ---------------------------------------------------------
# comments out, `\`-continuations joined, leading blanks trimmed.
logical_lines() {
  sed -E 's/^[[:space:]]*#.*$//' "$1" \
  | awk '{ if (sub(/\\[[:space:]]*$/, " ")) { printf "%s", $0 } else { print } }' \
  | sed -E 's/^[[:space:]]+//'
}

# emits "<script-basename><TAB><command>" for every real invocation in $1
commands_in() {
  logical_lines "$1" | awk '
    { t = $1; gsub(/^["\047]|["\047]$/, "", t)
      if (t ~ /\/?run_undistort_compose\.sh$/) print "run_undistort_compose.sh\t" $0
      else if (t ~ /\/?finish_render\.sh$/)    print "finish_render.sh\t" $0 }'
}

# 0 if this emitter can build a UNION canvas: a literal --framing=max, or
# --framing=$VAR / --framing="$VAR" where the file itself assigns VAR=max.
union_capable() {
  local f=$1 line var
  while IFS= read -r line; do
    case "$line" in *--framing=max*) return 0;; esac
    var=$(printf '%s\n' "$line" \
          | grep -oE -- '--framing="?\$\{?[A-Za-z_][A-Za-z0-9_]*' | head -1 \
          | sed -E 's/.*\$\{?//') || true
    [ -n "$var" ] || continue
    grep -qE "(^|[[:space:];])$var=max([[:space:]]|;|$)" "$f" && return 0
  done < <(logical_lines "$f")
  return 1
}

# ---- the rules, pure so --selftest can falsify them ---------------------
# $1 kind  $2 union-capable(0|1)  $3 multi-night(0|1)  $4 command
# echoes a reason and returns 1 when the command leaves the parameter undetermined.
check_cmd() {
  local kind=$1 union=$2 multi=$3 c=$4
  case "$kind" in
    finish_render.sh)
      [ "$union" = 1 ] || return 0
      case "$c" in
        *--central=*) ;;
        *) echo "renders a framing=max UNION and carries no --central= — the coverage seams false-detect and the solve starves (measured: logodds 63 against a confident floor of 100)"; return 1;;
      esac;;
    run_undistort_compose.sh)
      [ "$multi" = 1 ] || return 0
      case "$c" in
        *--ref=*) ;;
        *) echo "composes across NIGHTS and carries no --ref= — register -2pass's auto pick then decides the composite's orientation and channel balance from argument order (measured: K_B 0.846 + a rotated map, against 0.951 and an exact map)"; return 1;;
      esac;;
  esac
  return 0
}

# --selftest proves the RULES can fail, independently of what the tree happens
# to contain today: a guard whose tree is clean is indistinguishable from a
# guard whose checks do nothing (this repo's most persistent defect shape).
if [ "${1:-}" = "--selftest" ]; then
  bad=0
  while IFS=$'\t' read -r want kind union multi c; do
    [ -n "${want:-}" ] || continue
    got=PASS; check_cmd "$kind" "$union" "$multi" "$c" >/dev/null || got=FAIL
    if [ "$got" = "$want" ]; then echo "  selftest ok   [$got] union=$union multi=$multi  $c"
    else echo "  selftest WRONG (wanted $want, got $got): $c" >&2; bad=1; fi
  done <<EOF
FAIL	finish_render.sh	1	0	finish_render.sh \$OUT \${NAME}_full --session=\$S --set=\$T
PASS	finish_render.sh	1	0	finish_render.sh \$OUT \${NAME}_full --session=\$S --set=\$T --central=0.35
PASS	finish_render.sh	0	0	finish_render.sh \$STACK \$NAME --session=\$S --set=\$T
PASS	finish_render.sh	0	0	finish_render.sh \$STACK \$NAME --central=0.35
FAIL	run_undistort_compose.sh	1	1	run_undistort_compose.sh --out=\$OUT --framing=max --weight=nbstack \$DIRS
PASS	run_undistort_compose.sh	1	1	run_undistort_compose.sh --out=\$OUT --framing=max --ref=\$M --weight=nbstack \$DIRS
PASS	run_undistort_compose.sh	1	0	run_undistort_compose.sh --out=\$NIGHT --framing=max --weight=nbstack \$DIRS
PASS	run_undistort_compose.sh	0	0	run_undistort_compose.sh --out=\$OUT --framing=min \$DIRS
EOF
  [ "$bad" = 0 ] || fail "the rules do not fire as stated"
  echo "OK: 8 rule cases (5 determined/not-applicable, 3 undetermined) all verdict as stated"
  echo "    Both rules are falsified in BOTH directions: each fires on the bare"
  echo "    command and stands down on the same command carrying its flag, and"
  echo "    each stands down when its predicate (union / multi-night) is false."
  exit 0
fi

# ---- section A: shell emitters, per COMMAND -----------------------------
# DISCOVERED, so a new emitter is covered the day it is written rather than
# when someone remembers this list.
files=$(grep -rlE 'run_undistort_compose\.sh|finish_render\.sh' \
          --include='*.sh' scripts web | sort -u)

ncmd=0; nfile=0; bad=0; composers=''
for f in $files; do
  case "$f" in */check_compose_flags.sh) continue;; esac
  cmds=$(commands_in "$f") || true
  [ -n "$cmds" ] || continue
  nfile=$((nfile + 1))
  union=0; union_capable "$f" && union=1
  multi=0; listed_in "$f" "$MULTINIGHT" && multi=1
  while IFS=$'\t' read -r kind c; do
    [ -n "${kind:-}" ] || continue
    ncmd=$((ncmd + 1))
    [ "$kind" = run_undistort_compose.sh ] && composers="$composers $f"
    if why=$(check_cmd "$kind" "$union" "$multi" "$c"); then
      echo "  ok   $f: $kind (union=$union multi=$multi)"
    else
      echo "  FLAG $f: $kind $why" >&2; bad=1
    fi
  done <<< "$cmds"
done

# ---- section B: python emitters, per FILE (weaker, and stated as such) --
# A python emitter builds an argv LIST, so there is no command line to judge
# per command. What IS checkable is that the derivation exists at all: serve.py
# derives --central from the product tag (max-tag -> 0.35), which is the rule
# the shell emitters are missing, so its ABSENCE would be the same defect.
for pf in $(grep -rlE '"scripts/stack/(run_undistort_compose|finish_render)\.sh"' \
              --include='*.py' scripts web | sort -u); do
  grep -q 'run_undistort_compose\.sh' "$pf" && composers="$composers $pf"
  if grep -q '"scripts/stack/finish_render\.sh"' "$pf"; then
    if grep -q -- '--central=' "$pf"; then
      echo "  ok   $pf: python emitter, --central derivation present (per-FILE check)"
    else
      echo "  FLAG $pf: emits finish_render.sh and contains no --central derivation" >&2
      bad=1
    fi
  else
    echo "  ok   $pf: python emitter, compose only (no finish_render emission to check)"
  fi
done

# ---- the register is COMPLETE ------------------------------------------
# Every file that emits a compose is classified. An unclassified one fails
# here rather than defaulting into the single-night (unchecked) class.
for f in $(printf '%s\n' $composers | sort -u); do
  listed_in "$f" "$MULTINIGHT" || listed_in "$f" "$SINGLENIGHT" \
    || { echo "  FLAG $f: emits a compose and is in NEITHER register list — classify it multi-night or single-night; it cannot default into the unchecked class" >&2; bad=1; }
done

[ "$bad" = 0 ] || fail "the commands above leave --central / --ref undetermined — the union solve starves and the multi-night composite takes its balance from argument order"

# A parse that finds nothing asserts nothing. These floors are the canary: they
# fail when the emission style changes out from under the extractor, and they
# fail (deliberately) when a site is retired, which is the moment to re-read
# them rather than to lower them.
[ "$nfile" -ge 3 ] || fail "only $nfile shell files carry a compose/finish command (expected >= 3) — the extractor is not seeing the emissions"
[ "$ncmd" -ge 4 ]  || fail "only $ncmd compose/finish commands found (expected >= 4) — the extractor is not seeing the emissions"

cat <<EOF
OK: $ncmd compose/finish commands in $nfile shell files, every one determined
    (--central on every framing=max union render; --ref on every multi-night
    compose), and every composing file classified in the register.
    Scope: section A per COMMAND, section B per FILE, both static. Neither
    proves the emitted command is the one that ran. Rules are falsified by
    --selftest.
EOF
