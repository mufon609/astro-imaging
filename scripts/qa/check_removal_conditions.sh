#!/usr/bin/env bash
# THE REGISTER GUARD: every file that DECLARES a `REMOVAL CONDITION` in code must
# appear as a row in BACKLOG.md's removal-conditions table.
#
#   scripts/qa/check_removal_conditions.sh            check the repo against the register
#   scripts/qa/check_removal_conditions.sh --selftest prove it can go RED
#
# WHY THIS EXISTS. It is register rule (1), which until now nothing executed:
# "Every divergence declared in code belongs here — a `REMOVAL CONDITION:` in a
# docstring that is not in this table is invisible." That rule was written BECAUSE
# an audit found four such holes, and a later artifact-first sweep found three
# more. Every one was found by a human running the join by hand.
#
# AND THE GAP IS WIDER THAN THIS ONE RULE: the guard suite had ZERO coverage of
# `.md` before this check. MEASURED — the six pre-existing guards contain nine
# recursive greps and every one is `--include`-filtered to `*.py`/`*.sh`/`*.ssf`/
# `*.tmpl`; the three that mention a `.md` file do so only in comments. So the
# records — where essentially every finding this repo produces is written — were
# behind no gate at all. This is the first check that opens one.
#
# STANDARDS-FIRST, AND THIS IS A DEVIATION RECORDED RATHER THAN AN INVENTION.
# `CLAUDE.md` requires naming the industry-standard way FIRST. **What this check is
# is REFERENTIAL INTEGRITY** — every declared X has a row in Y — and that is an
# off-the-shelf test, not a bespoke one: dbt calls it the `relationships` test,
# Great Expectations a foreign-key expectation, and in schema terms it is JSON
# Schema `required` plus a cross-document key check. STATUS: DOCTRINE, sources
# named, not measured here.
# **THE MEASURED CONSTRAINT THAT FORCES THE DEVIATION: every one of those tools
# needs a KEY COLUMN, and this register has none.** It is a Markdown table whose
# divergence column is PROSE — the subject is a backticked name embedded in a
# sentence, sometimes a brace glob (`siril_run.{sh,py}`), sometimes a path,
# sometimes a concept with no file at all (`header_provenance_lines`). There is no
# field to join on, so a standard validator has nothing to bind to until the
# register is restructured into a keyed record. That restructuring is an
# owner-level architecture decision about the repo's most-read file, not something
# a guard should do as a side effect — so the hand-rolled join is the deviation and
# THIS is its reason. `python3-jsonschema` 4.26.0-2 is packaged and NOT installed;
# if the register ever gains a structured form, this file should be replaced by the
# standard validator rather than extended.
#
# THE JOIN IS ON THE DIVERGENCE COLUMN, NOT THE WHOLE TABLE, AND THAT IS THE
# WHOLE DESIGN. MEASURED, on the two cases that pull in opposite directions:
#   - `scripts/lib/siril_run.sh` declares a condition and the register writes its
#     row as `scripts/lib/siril_run.{sh,py}`. A literal basename match calls it
#     MISSING — a FALSE POSITIVE, and the one a hand-run of this join produced.
#     Brace forms are expanded generically below rather than special-cased, so the
#     next brace form somebody writes is handled without a code change.
#   - `scripts/qa/flat_odd_component.py` declares a condition and its ONLY
#     occurrence in BACKLOG.md is inside ANOTHER row's status prose (the
#     `flat_differential.py` row names it as an instrument). Matching "anywhere in
#     the table" therefore calls it COVERED — a FALSE NEGATIVE, and it is the
#     dangerous direction: an under-reporting check reads as "everything is
#     covered", which is the answer that ends the search.
# A mention is not a row. Rule (1) asks whether the divergence HAS a row, and the
# divergence column is what names a row's subject, so that is what is joined.
#
# WHAT THIS STRUCTURALLY CANNOT DETECT — read before treating GREEN as coverage.
# There are TWO holes and this is a detector for ONE of them:
#   (a) DECLARED-BUT-NO-ROW — a file says `REMOVAL CONDITION` and the register has
#       no row for it. That is what this finds.
#   (b) NO-CONDITION-ANYWHERE — a divergence that declares nothing at all. It is
#       INVISIBLE to this check by construction, because the check starts from the
#       declarations. `psf_calib.py` is the live example: it declared nothing, is
#       load-bearing for three rows, and was found only by a human reading. The
#       register's own header calls (b) "the worse case".
# A detector for (a) cannot see (b). The second detector is UNBUILT. Nothing here
# should be read as evidence that (b) is clean.
#
# Also not checked: whether a row's condition is TRUE, whether it has FIRED, and
# whether it can be EVALUATED at all. Those are three further questions and this
# answers none of them.
set -uo pipefail          # NOT -e: every file must be checked even after one fails
REPO=$(cd "$(dirname "${BASH_SOURCE[0]}")"/../.. && pwd)

REGISTER="$REPO/BACKLOG.md"
ROOT="$REPO"
# The roots a declaration can live in. `datasets/` is included deliberately: two
# of the shared libraries under `corner_work/` declare conditions and carry rows.
SCAN_DIRS=(scripts web datasets)

# Extract the divergence column of the removal-conditions table and brace-expand
# it. No `eval` anywhere: the register is tracked content, but a table cell is a
# place text can be added and a guard must not execute it.
register_subjects() {     # <register-path>
  awk '
    function expand_token(t,   pre, grp, post, n, parts, i, res, guard) {
      guard = 0
      while (match(t, /\{[^{}]*\}/) && guard++ < 8) {
        pre  = substr(t, 1, RSTART-1)
        grp  = substr(t, RSTART+1, RLENGTH-2)
        post = substr(t, RSTART+RLENGTH)
        n = split(grp, parts, ",")
        res = ""
        for (i = 1; i <= n; i++) res = res pre parts[i] post "\n"
        return res                      # each alternative re-enters via the caller
      }
      return t "\n"
    }
    /^\| divergence \| retires when/ { intable = 1; next }
    /^\|---/                          { next }
    intable && /^$/                   { exit }
    intable && /^\|/ {
      split($0, cell, "|")
      col1 = cell[2]
      n = split(col1, toks, /[ \t]+/)
      for (i = 1; i <= n; i++) if (toks[i] != "") printf "%s", expand_token(toks[i])
    }
  ' FS='\n' "$1" \
  | awk '                                # second pass: expand any residual braces
      { line = $0
        while (match(line, /\{[^{}]*\}/)) {
          pre  = substr(line, 1, RSTART-1)
          grp  = substr(line, RSTART+1, RLENGTH-2)
          post = substr(line, RSTART+RLENGTH)
          n = split(grp, parts, ",")
          for (i = 1; i <= n; i++) print pre parts[i] post
          next
        }
        print line
      }' \
  | tr -d '`' | sort -u
}

# THE DECLARATION PATTERN IS DERIVED FROM THE 28 REAL DECLARATIONS, NOT ASSUMED —
# and the two obvious tightenings are both WRONG, each measured against them:
#   - ANCHORING TO LINE START drops `anomaly_audit.py`, whose declaration sits
#     mid-line ("...a SANCTIONED gap-filler. `REMOVAL CONDITION:` retire it the").
#     That is the false-NEGATIVE direction, on a real divergence.
#   - REQUIRING A COLON drops the six that write `REMOVAL CONDITION.` and the one
#     that writes `REMOVAL CONDITION (the derived summaries only):`.
# What separates a DECLARATION from a DISCUSSION of one is the terminator plus the
# absence of a backtick: prose quotes the phrase, a declaration punctuates it.
# MEASURED: this matched 28 of 28 declarations IN ITS DERIVATION SET and drops 6 of
# the 7 self-matches this very file used to produce.
#
# DO NOT READ 28 AS A CENSUS — THE LIVE COUNT IS PRINTED BY THIS CHECK (`NDECL`)
# AND IS NOT WRITTEN ANYWHERE. It read 28 when the pattern was derived and 30 now.
#
# AND THE RECALL HOLE IS `A-Z` — THE PATTERN IS CASE-SENSITIVE, SO EVERY
# Title-case declaration IS INVISIBLE TO THE JOIN. Measured by enumerating the
# phrase independently of this pattern (any case, any of ` `/`-`/`_` between the
# words) over the same roots and file types, then READING all 33 non-matching
# files rather than counting them:
#
#     files containing the phrase at all                63
#     files matched by DECL_PAT                          30
#     of the 33 misses: register-slug references + discussions   25
#                       genuine punctuated declarations           8
#
# So recall against declarations is 30 of 38. The 8 missed are `verify_lens_card`,
# `install_lens_model`, `shape_at_sky`, `star_stations`,
# `backfill_substack_provenance`, `run_lunar_pipeline` (Title case) and
# `star_shape`, `snr_regions` (lower case, punctuated). `disk_budget.sh` reads
# like a ninth and is NOT one — it says a FUTURE 16-bit adaptation "needs its own
# `removal condition`", which is a statement about a condition, not one.
#
# THE HOLE WAS LOAD-BEARING WHEN MEASURED, AND THE POSITIVE CONTROL IS ONE
# CHARACTER CLASS: `verify_lens_card.py` declared a condition whose ONLY appearance
# in the register was inside ANOTHER row's status prose — the exact false negative
# this file's own JOIN-ON-THE-DIVERGENCE-COLUMN design exists to prevent, reached
# by a second mechanism it did not anticipate. Flipping ONLY the case of those two
# words in that file (numstat 1/1, nothing else touched) took this check from
# `OK: all 30` to `RED — 1 of 31`. It is GREEN again on the merits: that file is
# now named in the divergence column of the row whose condition it shares.
#
# WIDENING THE PATTERN IS NOT A ONE-LINER AND IS DELIBERATELY NOT DONE HERE. The
# registry records the trap: case-insensitivity closes the MISS and WIDENS the
# self-match, because it then matches both casings of a file's own prose about the
# phrase. Any widening must be re-fire-tested against the 7 self-matches above.
DECL_PAT='(^|[^`])REMOVAL CONDITION *[:.(]'

declaring_files() {       # <root>
  local root="$1" d
  for d in "${SCAN_DIRS[@]}"; do
    [ -d "$root/$d" ] || continue
    grep -rlE "$DECL_PAT" --include='*.py' --include='*.sh' "$root/$d" 2>/dev/null
  done | sed "s|^$root/||" | sort -u
}

# prints one line per unrostered declaration; returns the count via NMISS/NDECL
NMISS=0 ; NDECL=0
run_join() {              # <root> <register-path>
  local root="$1" reg="$2" subj f base
  NMISS=0 ; NDECL=0
  subj=$(register_subjects "$reg")
  while read -r f; do
    [ -z "$f" ] && continue
    NDECL=$((NDECL+1))
    base=$(basename "$f")
    if ! printf '%s\n' "$subj" | grep -qF -- "$base"; then
      printf '  MISSING ROW  %-52s declares REMOVAL CONDITION, no divergence-column entry\n' "$f"
      NMISS=$((NMISS+1))
    fi
  done <<< "$(declaring_files "$root")"
  return 0
}

if [ "${1:-}" = "--selftest" ]; then
  # POSITIVE CONTROL — required by CLAUDE.md: an acceptance measure ships with
  # data on which it MUST fire. A guard nobody has seen go RED is decoration.
  # The fixture lives under $HOME, never /tmp (the Siril flatpak has a private
  # /tmp) and never inside the repo, so a selftest run leaves the tree untouched.
  FIX=$(mktemp -d "${XDG_CACHE_HOME:-$HOME/.cache}/check_removal_conditions.XXXXXX") || exit 1
  trap 'rm -rf "$FIX"' EXIT
  mkdir -p "$FIX/scripts/qa"
  printf '| divergence | retires when | last checked | status |\n|---|---|---|---|\n' > "$FIX/reg.md"
  printf '| `rostered.py` derived thing | a tool does it | 2026-01-01 | not fired |\n'   >> "$FIX/reg.md"
  printf '| `scripts/lib/braced.{sh,py}` invoker | flatpak fixes it | 2026-01-01 | not fired |\n' >> "$FIX/reg.md"
  printf '| `other.py` thing | x | 2026-01-01 | mentions `prose_only.py` in its status |\n' >> "$FIX/reg.md"
  printf '\n' >> "$FIX/reg.md"
  # THE LITERAL IS SPLIT ON PURPOSE. A detector for a phrase otherwise CONTAINS the
  # phrase and reports itself — measured: this file produced 7 self-matches on its
  # first real run and the tightened pattern left exactly this one. Splitting it so
  # the source never holds the contiguous string is the same technique the registry
  # already records for the `pgrep` self-match trap, and it is better than an
  # exclusion rule: nothing has to remember to exempt this file.
  for n in rostered.py braced.sh prose_only.py; do
    printf '"""REMOVAL ''CONDITION: fixture."""\n' > "$FIX/scripts/qa/$n"
  done

  fail=0

  # (1) RED — a declaration whose only appearance is another row's PROSE must be
  #     reported. This is the false-NEGATIVE direction and the dangerous one.
  run_join "$FIX" "$FIX/reg.md" > "$FIX/out1" 2>&1
  if [ "$NMISS" -ne 1 ] || ! grep -q 'prose_only.py' "$FIX/out1"; then
    echo "  *** FAIL *** a prose-only mention was not reported as MISSING (miss=$NMISS)"
    cat "$FIX/out1"; fail=1
  else
    echo "  PASS  a declaration mentioned only in another row's PROSE goes RED ($NMISS of $NDECL)"
  fi

  # (2) the brace form must NOT be reported — the false-POSITIVE regression.
  if grep -q 'braced.sh' "$FIX/out1"; then
    echo "  *** FAIL *** the brace form \`braced.{sh,py}\` was reported MISSING (false positive)"
    fail=1
  else
    echo "  PASS  a brace-form row \`braced.{sh,py}\` matches its \`braced.sh\` declaration"
  fi

  # (3) GREEN — give the offender a row and the same fixture must come back clean.
  #     Built by dropping the fixture's terminating blank line, appending the row,
  #     and re-terminating, so arm 3 differs from arm 1 by EXACTLY one table row.
  head -n -1 "$FIX/reg.md" > "$FIX/reg2.md"
  printf '| `prose_only.py` now rostered | its tool arrives | 2026-01-01 | not fired |\n\n' >> "$FIX/reg2.md"
  run_join "$FIX" "$FIX/reg2.md" > "$FIX/out2" 2>&1
  if [ "$NMISS" -ne 0 ]; then
    echo "  *** FAIL *** adding the row did not clear the finding (miss=$NMISS)"
    cat "$FIX/out2"; fail=1
  else
    echo "  PASS  adding the missing row turns it GREEN (0 of $NDECL)"
  fi

  [ "$fail" -ne 0 ] && exit 1
  echo "SELFTEST PASSED"
  exit 0
fi

run_join "$ROOT" "$REGISTER"
if [ "$NMISS" -ne 0 ]; then
  printf '\ncheck_removal_conditions: RED — %d of %d declared conditions have no register row.\n' "$NMISS" "$NDECL"
  printf '  Rule (1), BACKLOG.md: add the row in the same commit as the divergence.\n'
  printf '  A declaration with no row is invisible to every re-check the register drives.\n'
  exit 1
fi
printf 'OK: all %d files declaring a REMOVAL CONDITION appear in the register.\n' "$NDECL"
printf '    Scope: detects DECLARED-BUT-NO-ROW only. It is structurally blind to a\n'
printf '    divergence that declares NOTHING (the register calls that the worse case;\n'
printf '    `psf_calib.py` was one). That second detector is UNBUILT.\n'
printf '    Not checked: whether a row is true, has fired, or can be evaluated.\n'
printf '\n'
printf '    YIELD — this class is a MINORITY of record-level defects, so do not read\n'
printf '    a GREEN run as "the records are covered". Measured instances of THIS\n'
printf '    class: 3 (`pa_convention.py` and `psfex_compare.py` at 4872db4, whose own\n'
printf '    message reads "THREE DIVERGENCES HAD NO ROW"; `flat_odd_component.py`,\n'
printf '    found by this check on its first run). The third in that commit was\n'
printf '    `psf_calib.py`, which declared nothing and needed the OTHER detector.\n'
printf '    Against that, one heavy day produced ~10 record-level defects this cannot\n'
printf '    see: stale negative tool claims, compression of a measured result, a\n'
printf '    circular positive control, an assumed constant, a live-tree measurement,\n'
printf '    a constant in the wrong home, narrative-in-table.\n'
printf '    THE BOUND IS THE MORE USEFUL HALF, and it is evidence not opinion: three\n'
printf '    cheap proxies for narrative-in-table were built and calibrated against\n'
printf '    rows whose answer was known, and ALL THREE FAILED — one INVERTED. So a\n'
printf '    records gate has a small mechanical core and a large UNGATABLE remainder.\n'
printf '    Method caveat: the classification above was made from commit MESSAGES,\n'
printf '    not full diffs, by two readers sharing that method — UNCHECKED, not\n'
printf '    confirmed. The instance counts are exact; the denominator is an estimate.\n'
