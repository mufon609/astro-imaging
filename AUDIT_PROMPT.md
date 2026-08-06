# Prompt for a fresh audit session — paste everything below this line

---

Audit this repo's pipeline. A full end-to-end run just completed and was accepted;
what follows is the list of things that run left unresolved, unmeasured, or
unverified. Your job is to close them, and to be hard on the ones that look
already-closed.

**READ FIRST, in this order** (the repo's read-order, and it is binding):
`CLAUDE.md` → `docs/dead-ends.md` → `TOOLS.md` → `MEMORY.md` → `README.md` →
`BACKLOG.md` → `datasets/README.md` → `web/README.md`.

## Where things stand

july31 ran from raw frames to judge surfaces, four sets, on the groups route.
**All four surfaces were judged PASS by the user** (`datasets/july31/judge_acceptance.json`).
**CORRECTED 2026-08-06 — this paragraph originally said two single-pass control
stacks and 17 sub-stacks were kept. They were deleted in a later cleanup and are
NOT on disk.** What survives: the four accepted `stack_set-0{1..4}_full{,_spcc}.fit`,
the accepted 1760-frame combine `stack_all4_full{,_spcc}.fit`, five judge
surfaces, the master dark and four sky flats, 2114 raw NEF, and every tracked
record. Gone: all sub-stacks, both single-pass controls, the `--group=250` arm,
every `_wcs.fit`, and all work trees. Consequences you must plan around — the
combine cannot be re-composed without a full re-warp from raws; the route A/B and
the dose-response cannot be re-read off disk and survive ONLY as numbers in
`datasets/july31/experiments.jsonl`. Rebuilding from raws is expected and endorsed
("i don't mind having to rerun any part of the process"), so treat a missing
intermediate as a cost, never as a fault.

Everything below is open. The order is mine; challenge it if the code says
otherwise.

## 1. The measurement gate — do this before trusting any route claim

**No REBUILD-REPEAT FLOOR has ever been measured on this chain.** A compose-repeat
floor exists (0.00 px, bit-identical, n=2) but it bounds only re-running the final
compose — not a full rebuild through warp → register → stack.

Every route number this repo currently asserts sits on unmeasured ground: the
single-pass-vs-groups effect is 0.12–0.18 px on one station, and the group=250
arm falsified its own pre-registered dose-response by 0.05 px. Neither can be
distinguished from rebuild variance until the floor exists.

**Rebuild one arm from the same frames with the same parameters, measure
`along+1300` with `scripts/qa/star_stations.py`, and report the delta.** If a
same-arm rebuild moves ≥0.05 px, several recorded conclusions become noise and
must be retracted with their numbers. `datasets/july31/experiments.jsonl` carries
the closed entries this would bear on.

## 2. Guards that nobody runs

`check_bitdepth.sh`, `check_calibrate.sh`, `check_stack_rejection.sh`,
`lens_preflight.py --selftest` all pass and all fail loudly — and **nothing
invokes any of them automatically** (BACKLOG:`guards-and-ci`). They have been run
by hand after every change, which is exactly the manual step a runner replaces.
`check_stack_rejection.sh` is also mode 100644 and cannot be executed directly.

## 3. The audit that the chain never calls

`README.md` documents the undistort prep as "frame QA + the anomaly audit → the
cull policy". `run_set_chain.sh` never calls `scripts/qa/anomaly_audit.py` — grep
it. Consequences, all live: the dwell floor reports `NOT CHECKED — UNVERIFIED` on
every set; july31/set-03's aircraft and its 27-frame satellite were only known
from a record recovered out of git history; and a chain-only run of any dataset
surfaces no obstructions at all.

## 4. Claims whose evidence is missing or unverifiable

- **The `sky x V` object tilt — 3.11% at 241 sigma.** Cited in six code and doc
  sites as the justification for a whole class of decisions. No tracked record
  holds the measurement; it entered the repo as prose. Either re-measure it or
  mark it as unverified everywhere it is cited.
- **set-01's `seqtilt` off-axis 0.42 → 0.18** between routes, which did NOT
  replicate on set-02 (0.44 → 0.45). Ruled out as a lens-model artifact with
  numbers (0.01 px between models). Genuinely unexplained — do not let it acquire
  a convenient story.
- **The approval tag.** `README`, `datasets/README`, `web/README` and `serve.py`
  all treat a `<session>-all<N>-<tag>-approved` git tag as the record that a
  render was approved. `git tag --list` is empty and always has been.
- **SPCC sensor response.** The database holds 395 sensors and no Z-series entry,
  so every K factor on this corpus was computed against a default curve while the
  docs call the step COMPLIANT.

## 5. Generality — the standard the repo is trying to meet

The pipeline must **pinpoint exact facts in the data to make its choices, while
staying general enough to make those same choices for a different rig.** The same
code has to be right for OSC raws on an untracked tripod AND for a monochrome,
tracked, long-exposure set with real flats and no lens distortion.

Known-open in that direction:

- **Routing is keyed on `fov >= 10`, written at FOUR sites** with nothing
  single-sourcing it (`fingerprint.py:242,288`, `run_set_chain.sh:145,425` — grep `fov >= 10` rather than trusting these numbers, they have drifted once already) —
  the exact defect `disk_budget.sh` was created to kill. The physically correct
  key is measured `drift_px`, which the fingerprint already computes: a fixed
  tripod at 200 mm has a small field and large drift, and today exits 5 as
  unroutable.
- **`mount` is asked of a human when the instrument has already answered.**
  Four independent two-window drift solves CONFIRMED `fixed` at worst 0.6% from
  sidereal. `run_set_chain.sh` computes `MOUNT_EFF` from the measurement, routes
  the plan on it, then stops because the string is absent. The policy belongs in
  `acquisition.resolve()`; keep the human field as an override that still raises
  CONTRADICT, and stop only on INDETERMINATE. It is also a session-level fact
  modelled per set — one tripod paid a ~9-minute probe four times.
- **A real-flat set on the undistort route exits 6 and refuses.** Doing
  acquisition right stops the one-click chain while the flatless path runs.
- **A fixed + wide + FITS set** routes to undistort, which globs camera raws only,
  and dies with "no raw frames" — right stop, wrong diagnosis.

## 6. One open observation, not yet a finding

Linear corner spread across the four sets, in capture order: **0.40 / 0.50 / 1.03
/ 1.17 %**. The user's acceptance of set-04's corners is well-founded — ~1% linear
renders as visibly odd through a stretch that amplifies 9–17× — but the roughly
monotonic doubling across the night is the signature the open `sky x V` defect
predicts, and frame count does not explain a trend in capture order. Stated as a
hypothesis with the test that would settle it, not as a result.

## How to work

- **One knob per experiment, hypothesis and threshold pre-registered BEFORE the
  run**, verdict closed into `experiments.jsonl`. A killed hypothesis becomes a
  `docs/dead-ends.md` entry with its numbers.
- **Verify a guard by BREAKING it.** Disable the mechanism, watch the test go red,
  restore. Reasoning from a fixture's construction is exactly as unreliable as
  reasoning from the code it tests — that produced three vacuous tests in one
  session.
- **Do not hand-roll a check when the tool has a reader.** Five verification
  failures in the last session, and *the thing being checked was correct every
  time*. Two independent sessions hit the same trap within an hour: a lensfun
  vendor DB holds many lenses and our block carries a comment with a decoy
  element, so any grep must be block-scoped AND comment-masked. Call
  `lens_preflight`'s own scanner instead.
- **Report MEASURED (with numbers and the instrument) or HYPOTHESIS (with the test
  that would settle it).** No "fixed/final/matched/close". A clean NULL is a
  result; a killed hypothesis is worth more than a tidy story.
- **Nothing output-shaping proceeds without the user.** Aesthetic judgement is
  theirs, on full-frame lossless finals.

Start by telling me which of these you can falsify from the code alone, before
running anything.
