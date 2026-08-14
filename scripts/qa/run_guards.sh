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
#   queries the ESA Gaia archive). It is run unconditionally and labelled, so an
#   offline failure is interpretable rather than silently skipped. There is no
#   --skip flag on purpose: a conditional path that nobody exercises is the
#   defect class this runner exists to catch.
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
  "selftest check_registration_pins|./scripts/stack/check_registration_pins.sh --selftest"
  "selftest wait_for|./scripts/lib/wait_for.sh --selftest"
  "selftest fingerprint|python3 scripts/lib/fingerprint.py --selftest"
  "selftest route|python3 scripts/lib/route.py --selftest"
  "selftest compose_preflight|python3 scripts/stack/compose_preflight.py --selftest"
  "selftest lens_preflight|python3 scripts/stack/lens_preflight.py --selftest"
  "selftest object_tilt|python3 scripts/qa/object_tilt.py --selftest"
  "selftest flat_differential|python3 scripts/qa/flat_differential.py --selftest"
  "selftest grid_ramp|python3 scripts/qa/grid_ramp.py --selftest"
  "selftest coverage_frame|python3 scripts/qa/coverage_frame.py --selftest"
  "selftest starlight_preservation [network]|python3 scripts/qa/starlight_preservation.py --selftest"
  # THE TWO SHARED LIBRARIES UNDER corner_work/, ADDED DELIBERATELY — see the
  # exclusion note above, which they are the stated exception to.
  "selftest pa_convention [lib]|python3 datasets/aug06/corner_work/pa_convention.py --selftest"
  "selftest constancy_fit [lib]|python3 datasets/aug06/corner_work/constancy_fit.py --selftest"
)

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
