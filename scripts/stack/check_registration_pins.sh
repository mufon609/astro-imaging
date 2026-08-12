#!/usr/bin/env bash
# Guard: every emitted Siril registration command pins its TRANSFORM MODEL and,
# where it resamples, its INTERPOLATION KERNEL. Run it in CI / before a release.
#
# WHY. `-transf=` and `-interp=` are both Siril DEFAULTS. An unpinned command
# therefore takes whatever the installed version supplies, so a tool bump can
# change the geometry and the resampling of EVERY stack in this repo with
# nothing in any record to show for it — the same failure shape as the persisted
# `setext` / `setcompress 0` / `set32bits` state that check_bitdepth.sh pins,
# except supplied by the version rather than by the last run.
#
# THE DOCTRINE PINNED HERE (TOOLS.md): homography for wide fields, lanczos4 with
# clamping. Clamping is itself a default and there is no switch that turns it ON
# — `-noclamp` turns it OFF — so pinning it means asserting that flag is ABSENT
# everywhere, which is a check this guard can make and a flag nothing may add
# without failing here first.
#
# WHY LITERALS AT EVERY SITE AND NOT ONE SHARED CONSTANT. The emissions live in
# bash printf strings, bash echo lines, a python string literal and a literal
# .ssf template — three languages, so no single shared symbol reaches them all.
# This guard asserts the exact tokens instead, which gives the same protection:
# a site that drifts to a different model or kernel fails here rather than
# shipping a differently-registered product.
#
# SCOPE — per COMMAND, not per file. check_bitdepth.sh states its own limit
# (per-FILE, so a builder that pins in one emission passes even if a second
# emission omits it). This one parses the emitted command lines out of every
# .ssf and every .ssf emitter, so each `register` / `seqapplyreg` is judged on
# its own. What it does NOT prove: that the command a builder emits is the one
# that runs (a runtime override, an operator's hand-written .ssf).
#
# WHAT COUNTS AS A COMMAND. Emissions are `\n`-joined printf strings, quoted
# echo arguments and python string literals, so the parse expands `\n` and
# splits on quotes/semicolons, then keeps lines shaped like a real siril
# command: the verb, one sequence name, then flags only. That shape is what
# separates the emissions from PROSE that begins with the same word — GUI
# instructions ("register ALL images -> Go") and a log-description string both
# sit in these files and are neither.
set -euo pipefail
cd "$(dirname "$0")/../.."          # repo root: the whole tree, not one stage dir
fail() { echo "FAIL: $*" >&2; exit 1; }

TRANSF='-transf=homography'
INTERP='-interp=lanczos4'

# The one interpolation exemption. run_lunar_pipeline.sh pins `-interp=none`,
# which forces a pixel-wise integer shift: the lunar route registers on a
# circular correlation of the disc and any resampling there is a second
# aliasing pass over an already-aliased crop. It is an explicit pin, not a
# default, so it satisfies the reason this guard exists.
INTERP_EXEMPT_FILE='scripts/stack/run_lunar_pipeline.sh'
INTERP_EXEMPT_VALUE='-interp=none'

# One command per line, judged on its own. $1 = file (for the exemption), $2 =
# command. Echoes a reason and returns 1 when the command is unpinned.
check_cmd() {
  local f=$1 c=$2
  case "$c" in
    *-noclamp*)
      echo "$c: passes -noclamp — clamping is the DEFAULT this repo keeps (lanczos4 rings on stars); there is no flag that turns it back on"
      return 1;;
  esac
  case "$c" in
    register*)
      case "$c" in
        *"$TRANSF"*) ;;
        *) echo "$c: no $TRANSF — the transform model rides Siril's default"; return 1;;
      esac
      # `-2pass` computes transforms and writes no image; a bare `register`
      # resamples in the same command, so only that form needs the kernel.
      case "$c" in
        *-2pass*) ;;
        *"$INTERP"*) ;;
        *) echo "$c: one-pass register RESAMPLES and carries no $INTERP"; return 1;;
      esac;;
    seqapplyreg*)
      case "$c" in
        *"$INTERP"*) ;;
        *"$INTERP_EXEMPT_VALUE"*)
          [ "$f" = "$INTERP_EXEMPT_FILE" ] || {
            echo "$c: $INTERP_EXEMPT_VALUE is exempt only in $INTERP_EXEMPT_FILE"; return 1; };;
        *) echo "$c: no $INTERP — the resampling kernel rides Siril's default"; return 1;;
      esac;;
  esac
  return 0
}

# --selftest proves the RULES can fail, independently of what the tree happens
# to contain today: a guard whose tree is clean is indistinguishable from a
# guard whose checks do nothing (this repo's most persistent defect shape).
if [ "${1:-}" = "--selftest" ]; then
  bad=0
  # each case: expected-verdict<TAB>file<TAB>command
  while IFS=$'\t' read -r want f c; do
    [ -n "${want:-}" ] || continue
    got=PASS; check_cmd "$f" "$c" >/dev/null || got=FAIL
    if [ "$got" = "$want" ]; then echo "  selftest ok   [$got] $c"
    else echo "  selftest WRONG (wanted $want, got $got): $c" >&2; bad=1; fi
  done <<EOF
PASS	x	register s -2pass -transf=homography
FAIL	x	register s -2pass
FAIL	x	register s -2pass -transf=affine
PASS	x	register s -transf=homography -interp=lanczos4
FAIL	x	register s -transf=homography
FAIL	x	register s -2pass -transf=homography -noclamp
PASS	x	seqapplyreg s -framing=min -prefix=r_ -interp=lanczos4
FAIL	x	seqapplyreg s -framing=min -prefix=r_
FAIL	x	seqapplyreg s -interp=nearest
FAIL	x	seqapplyreg s -interp=lanczos4 -noclamp
PASS	$INTERP_EXEMPT_FILE	seqapplyreg pp_moon -interp=none
FAIL	x	seqapplyreg pp_moon -interp=none
EOF
  [ "$bad" = 0 ] || fail "the rules do not fire as stated"
  echo "OK: 12 rule cases (6 pinned, 6 unpinned/wrong) all verdict as stated"
  exit 0
fi

# Every .ssf and every file that emits one — DISCOVERED, so a new builder is
# covered the day it is written rather than when someone remembers this list.
files=$(grep -rl '\.ssf' --include='*.sh' --include='*.py' --include='*.ssf' \
          --include='*.tmpl' scripts web | sort)
files="$files
$(find scripts -name '*.ssf' -o -name '*.ssf.tmpl' | sort)"

ncmd=0; nfile=0; bad=0
for f in $(printf '%s\n' "$files" | sort -u); do
  case "$f" in */check_registration_pins.sh) continue;; esac
  cmds=$(awk '/^[[:space:]]*#/ { next }
              { gsub(/\\n/, "\n"); gsub(/["\047;]/, "\n"); print }' "$f" \
         | sed -E 's/^[[:space:]]*//; s/^(%[a-zA-Z])+//; s/^[[:space:]]*//' \
         | grep -E '^(register|seqapplyreg)[[:space:]]+[A-Za-z0-9_%${}]+([[:space:]]+-[^[:space:]]+)*[[:space:]]*$' \
         || true)
  [ -n "$cmds" ] || continue
  nfile=$((nfile + 1))
  while IFS= read -r c; do
    ncmd=$((ncmd + 1))
    if why=$(check_cmd "$f" "$c"); then
      echo "  ok   $f: $c"
    else
      echo "  PIN  $f: $why" >&2; bad=1
    fi
  done <<< "$cmds"
done

[ "$bad" = 0 ] || fail "unpinned registration above — a Siril version bump changes those products silently"

# A parse that finds nothing asserts nothing. These floors are the canary: they
# fail when the emission style changes out from under the extractor, and they
# fail (deliberately) when a site is retired, which is the moment to re-read
# them rather than to lower them.
[ "$nfile" -ge 10 ] || fail "only $nfile files carry a registration command (expected >= 10) — the extractor is not seeing the emissions"
[ "$ncmd" -ge 20 ] || fail "only $ncmd registration commands found (expected >= 20) — the extractor is not seeing the emissions"

hits=$(grep -rn 'noclamp' --include='*.ssf' --include='*.tmpl' --include='*.sh' \
        --include='*.py' scripts web | grep -vE 'check_registration_pins\.sh:|^[^:]+:[0-9]+:[[:space:]]*#' || true)
[ -z "$hits" ] || { echo "$hits" >&2; fail "-noclamp appears above — clamping is the default this repo keeps"; }

cat <<EOF
OK: $ncmd registration commands in $nfile files, every one pinned
    ($TRANSF on every register; $INTERP on every resample,
    $INTERP_EXEMPT_VALUE exempt in $INTERP_EXEMPT_FILE);
    no -noclamp anywhere, so lanczos4 clamping stays on.
    Scope: per COMMAND, static. It does not prove the emitted command is the
    one that ran. Rules are falsified by --selftest.
EOF
