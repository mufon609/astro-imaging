#!/usr/bin/env bash
# THE GUARD RUNNER — runs every repo guard and every data-free instrument
# selftest, reports each, and exits non-zero if any fails.
#
#   scripts/qa/run_guards.sh [--list]
#
# WHY THIS EXISTS. Five guards existed and all passed, and NOTHING RAN THEM:
# `check_bitdepth.sh`'s own header says "PRE-RELEASE / CI GUARD" and there was no
# runner to be that CI. The measured cost of the gap is not hypothetical — a
# register row describing one of these guards as broken outlived its fix by three
# days because nothing re-executed it, and a verification instrument was found
# able to stamp a record "verified" on coverage it had not measured.
#
# HOW IT INVOKES, AND IT IS NOT PEDANTRY. Shell guards run as `./scripts/...`,
# never `bash scripts/...`. `bash <path>` SIDESTEPS THE EXECUTABLE BIT, so an
# audit that used it reported five passes while a guard could not actually be
# executed by the chain — the check's own mechanism excluded the failure mode it
# was testing for. Running them the way the chain runs them is the point, and the
# fire test below removes an executable bit to prove this runner sees it.
# Python selftests run as `python3 <path> --selftest`, which is how their own
# records specify them; their executable bit is NOT under test here.
#
# WHAT THIS DOES NOT COVER — read before treating a green run as coverage:
# - `check_bitdepth.sh` is PER-FILE and STATIC. A builder that already emits
#   `set32bits` in one generated `.ssf` PASSES even if a newly added emission in
#   the same file omits the pin. This is a deliberate deferral, not an oversight:
#   a parser that tried to prove it per-emission would be fragile in a way that
#   is worse than a stated limit. The guard says so itself.
# - These guards verify WIRING — that the code says what it must. They do not
#   verify OUTPUT. A guard cannot tell you a render is good.
# - RECORDS COVERAGE IS NOW NON-ZERO AND IT IS NARROW — do not read it as more.
#   Until `check_removal_conditions` was added this suite had ZERO coverage of
#   `.md`: MEASURED, the six shell guards contain nine recursive greps and every
#   one is `--include`-filtered to `*.py`/`*.sh`/`*.ssf`/`*.tmpl`, and the three
#   that mention a `.md` file do so only in comments. The consequence was that the
#   suite could not distinguish two commits whose only changes were in records —
#   which is where essentially every finding this repo produces is written. The
#   new check opens exactly ONE invariant (register rule (1), declared-but-no-row)
#   and is blind to the rest of the table, including whether a row is true, has
#   fired, or can be evaluated at all. `check_doc_pointers` opens a SECOND: every
#   backticked repo path, BACKLOG slug and relative link in a tracked or new
#   `.md` resolves — existence only, still wiring, never whether a target says
#   what its citation claims.
# - A green run says nothing about the checks listed under EXCLUDED below, which
#   need live products and are named there rather than silently skipped.
# - HOW THE ROSTER WAS BUILT IS ITSELF A LIMIT. It came from `grep -rln selftest`
#   over `scripts/` and `web/`, with every hit then classified by RUNNING it. So
#   a selftest exposed under a flag this grep does not match is invisible to the
#   roster and would be silently absent rather than reported missing — and the
#   naming is NOT uniform, which is not a worry but a measured fact:
#   `x86_bootstrap.sh` exposes `--selftest-gaia`, not `--selftest`. That one is
#   known and excluded on its own merits (below); the point is that others could
#   exist. Adding a check here is a manual act, and nothing detects one that was
#   never added. This is the same defect class the runner exists to catch, one
#   level up — so when you add a selftest anywhere, add its row to CHECKS in the
#   same commit.
# - One check reaches the NETWORK (starlight_preservation's catalogue control
#   queries the ESA Gaia archive). It is run unconditionally and labelled.
#   THIS COMMENT USED TO SAY "an offline failure is interpretable rather than
#   silently skipped. There is no --skip flag on purpose: a conditional path
#   that nobody exercises is the defect class this runner exists to catch."
#   BOTH HALVES WERE FALSE AGAINST THE CODE THEY DESCRIBE.
#   (a) OFFLINE DOES NOT FAIL. The archive step sits in a try/except
#       (starlight_preservation.py, step 5) whose handler prints "SKIPPED
#       (archive unreachable) — the catalogue half is UNVERIFIED in this run,
#       and a PASS below does not cover it" and NEVER TOUCHES `ok`. The
#       selftest then returns `0 if ok else 1`, so offline the step skips, the
#       check exits 0, this runner reports GREEN and pre-push passes. Offline
#       is a SOFT CAVEAT, not a failure. The caveat IS printed — it is not
#       silent — but nothing makes a reader see it, and GREEN is what gets read.
#   (b) THERE IS A CONDITIONAL PATH. "No --skip flag" described the FLAG and
#       not the behaviour: a try/except selected by the environment is the same
#       branch by another spelling. And NEITHER SIDE IS EXERCISED IN BOTH
#       STATES BY ANY ROUTINE GATE — online the handler never runs, offline the
#       query never does. That is precisely "a conditional path that nobody
#       exercises", inside the check whose comment claimed it was avoided.
#   NOT CHANGED HERE, deliberately: whether the skip should go RED, or whether
#   both branches should be exercised, is a decision about what this suite DOES
#   and is not a comment's to take. The comment now describes the code; the
#   behaviour question is open.
#
# EXCLUDED, each with the reason, because a runner that quietly drops checks is
# worse than one that names them:
# - `scripts/qa/member_separation.py --selftest` — REQUIRES a live <seq-dir>
#   holding members plus their `.seq`; it falsifies against real data and
#   refuses loudly without it (measured: exit 1). Not data-free, by design.
# - `scripts/qa/object_tilt_null.sh` — executes the instrument on REAL corpus
#   data, not a fixture.
# - `scripts/setup/x86_bootstrap.sh --selftest-gaia` — a bootstrap-LAYER fire
#   test (note the different flag), which downloads the Gaia catalogue into a
#   scratch dir. Not a repo guard and far too heavy for this runner.
# - `scripts/qa/check_solve_records.py` (the FULL run, not its selftest) — joins
#   plate-solve RECORDS against the ARTIFACTS they name, so it needs live products
#   under `web/results/`, which is gitignored and absent from a fresh clone. Its
#   `--selftest` IS data-free and IS in the roster above: it plants a disagreeing
#   record and asserts it fires, plants a matching one and asserts it does not, and
#   asserts CRVAL is distinguishable from the centre pixel — that last arm guards
#   the instrument's design decision rather than its code, since a future edit
#   swapping the comparand back to CRVAL would pass every other arm.
# - `scripts/qa/observer_frame_diversity.py --selftest` — plants the frozen-clock
#   defect on REAL group sub-stacks and asserts it reproduces, so unlike
#   check_solve_records' selftest it is NOT data-free and cannot run on a fresh
#   clone. Excluded whole rather than partly.
# - `datasets/aug06/corner_work/*.py --selftest` — PER-DATASET, with TWO
#   DELIBERATE EXCEPTIONS now in the roster. The rest depend on one dataset's
#   records and are not repo guards; they are listed here so nobody concludes
#   they were forgotten.
#   **THE EXCEPTIONS, AND WHY THE ORIGINAL RULE WAS THE WRONG SHAPE:**
#   `pa_convention.py` has SIX importers and `constancy_fit.py` has TWO — they
#   are shared LIBRARIES that happen to live in a per-dataset directory, and the
#   exclusion keyed on where a file LIVES rather than on what it IS. MEASURED
#   COST OF THAT: a change to `decompose()` left two sibling instruments dead on
#   their analysis path, and every check in play was structurally unable to see
#   it — the sibling selftests never reached the shared call, the runner skipped
#   the whole directory by this rule, and the library's own fixtures were updated
#   in the same commit as the rename. MEASURED SAFETY OF ADDING THEM: both pass
#   with NO arguments, and the records they read
#   (`datasets/aug06/set-01/acquisition.json`) are TRACKED, so they are present in
#   any clone — the exclusion's stated reason does not apply to these two. Cost
#   ~12 s. `constancy_fit --selftest` carries `contract_check()`, which calls each
#   sibling's OWN row builder and hands the result to the shared fitter, so this
#   is the check that would have caught that regression.
set -uo pipefail          # NOT -e: every check must run even after one fails
REPO=$(cd "$(dirname "${BASH_SOURCE[0]}")"/../.. && pwd)
cd "$REPO"

# label | invocation
# Shell guards first (the five the contract names), then the selftests.
CHECKS=(
  "guard   check_bitdepth|./scripts/stack/check_bitdepth.sh"
  "guard   check_calibrate|./scripts/stack/check_calibrate.sh"
  "guard   check_siril_invoke|./scripts/stack/check_siril_invoke.sh"
  "guard   check_stack_rejection|./scripts/stack/check_stack_rejection.sh"
  "guard   check_registration_pins|./scripts/stack/check_registration_pins.sh"
  "guard   check_manifest_verify|./scripts/qa/check_manifest_verify.sh"
  "guard   check_removal_conditions|./scripts/qa/check_removal_conditions.sh"
  "guard   check_doc_pointers|python3 scripts/qa/check_doc_pointers.py"
  "guard   check_site_privacy|python3 scripts/qa/check_site_privacy.py"
  "selftest check_registration_pins|./scripts/stack/check_registration_pins.sh --selftest"
  "selftest check_compose_flags|./scripts/stack/check_compose_flags.sh --selftest"
  "selftest check_removal_conditions|./scripts/qa/check_removal_conditions.sh --selftest"
  "selftest check_doc_pointers|python3 scripts/qa/check_doc_pointers.py --selftest"
  "selftest check_site_privacy|python3 scripts/qa/check_site_privacy.py --selftest"
  "selftest wait_for|./scripts/lib/wait_for.sh --selftest"
  "selftest fingerprint|python3 scripts/lib/fingerprint.py --selftest"
  "selftest route|python3 scripts/lib/route.py --selftest"
  "selftest compose_preflight|python3 scripts/stack/compose_preflight.py --selftest"
  "selftest derive_compose_ref|python3 scripts/stack/derive_compose_ref.py --selftest"
  "selftest lens_preflight|python3 scripts/stack/lens_preflight.py --selftest"
  "selftest object_tilt|python3 scripts/qa/object_tilt.py --selftest"
  "selftest flat_differential|python3 scripts/qa/flat_differential.py --selftest"
  "selftest grid_ramp|python3 scripts/qa/grid_ramp.py --selftest"
  "selftest coverage_frame|python3 scripts/qa/coverage_frame.py --selftest"
  "selftest regional_stat [siril]|python3 scripts/qa/regional_stat.py --selftest"
  "selftest shape_at_sky|python3 scripts/qa/shape_at_sky.py --selftest"
  "selftest run_member_crop [siril]|./scripts/stack/run_member_crop.sh --selftest"
  "selftest check_solve_records|python3 scripts/qa/check_solve_records.py --selftest"
  "selftest baseline_guard|python3 scripts/qa/baseline_guard.py --selftest"
  "selftest spcc_run|python3 scripts/calibrate/spcc_run.py --selftest"
  "selftest starlight_preservation [network]|python3 scripts/qa/starlight_preservation.py --selftest"
  # THE TWO SHARED LIBRARIES UNDER corner_work/, ADDED DELIBERATELY — see the
  # exclusion note above, which they are the stated exception to.
  "selftest pa_convention [lib]|python3 datasets/aug06/corner_work/pa_convention.py --selftest"
  "selftest constancy_fit [lib]|python3 datasets/aug06/corner_work/constancy_fit.py --selftest"
)

# check_compose_flags's SELFTEST is in the roster above; its FULL RUN is NOT,
# and this is a named omission rather than a forgotten row (the roster's own
# stated failure mode). The guard is RED on this tree BY DESIGN: it reports that
# three emitted commands leave --central / --ref undetermined
# (run_corpus_combine.sh x2, run_session_chain.sh x1). Adding it here now would
# turn pre-push red for every push until those are fixed, and the fix is
# pixel-affecting — it changes the union solve and the multi-night composite's
# reference, so it is gated on an A/B against the hand-built control, not on a
# guard's convenience. ADD THE ROW IN THE COMMIT THAT GREENS IT. Until then the
# selftest above proves the rules still fire, which is the half that can be
# proven on a red tree.

if [ "${1:-}" = "--list" ]; then
  printf 'run_guards: %d checks\n' "${#CHECKS[@]}"
  for row in "${CHECKS[@]}"; do printf '  %-42s %s\n' "${row%%|*}" "${row#*|}"; done
  exit 0
fi

LOGDIR=$(mktemp -d "${TMPDIR:-/tmp}/run_guards.XXXXXX")
# LOGS SURVIVE A RED RUN. They used to be deleted unconditionally on EXIT, and a
# transient failure was then UNDIAGNOSABLE: a run reported "17 passed, 1 failed"
# and by the time anyone looked the evidence was gone and the re-run was green.
# A CI-slot runner whose failures cannot be read afterwards is most of the way to
# useless, so the trap now only cleans up when everything passed.
KEEPLOGS=0
trap '[ "$KEEPLOGS" = 1 ] || rm -rf "$LOGDIR"' EXIT
FAILED=() ; NPASS=0 ; T0=$SECONDS

printf '=== run_guards: %d checks, invoked as the chain invokes them ===\n\n' "${#CHECKS[@]}"
for row in "${CHECKS[@]}"; do
  label=${row%%|*} ; cmd=${row#*|}
  log="$LOGDIR/$(echo "$label" | tr -cd '[:alnum:]_').log"
  t=$SECONDS
  # word-split $cmd deliberately: these are fixed, in-repo invocations
  # shellcheck disable=SC2086
  if $cmd > "$log" 2>&1; then
    printf '  PASS  %-42s %4ds\n' "$label" "$((SECONDS-t))"
    NPASS=$((NPASS+1))
  else
    rc=$?
    printf '  FAIL  %-42s %4ds  (exit %d)\n' "$label" "$((SECONDS-t))" "$rc"
    FAILED+=("$label|$log|$rc")
  fi
done

printf '\n=== %d passed, %d failed, %ds wall ===\n' "$NPASS" "${#FAILED[@]}" "$((SECONDS-T0))"

if [ ${#FAILED[@]} -gt 0 ]; then
  for f in "${FAILED[@]}"; do
    lbl=${f%%|*} ; rest=${f#*|} ; log=${rest%%|*} ; rc=${rest##*|}
    printf '\n--- FAILED: %s (exit %s) — last 15 lines ---\n' "$lbl" "$rc"
    tail -15 "$log" | sed 's/^/    /'
  done
  KEEPLOGS=1
  printf '\nrun_guards: RED. Nothing was rewritten; fix the cause and re-run.\n'
  printf '  full output of every check KEPT at: %s\n' "$LOGDIR"
  exit 1
fi

printf 'run_guards: GREEN — every guard and every data-free selftest passes.\n'
printf '  This verifies WIRING, not output, and check_bitdepth is per-FILE and\n'
printf '  static. Read the LIMITS block in this file before quoting it as coverage.\n'
