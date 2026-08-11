# Fresh-session prompt — four small hardening items, one session

**Do not take this document's word for anything** — every claim is checkable
in the repo; check it. Read `CLAUDE.md` first, then `docs/dead-ends.md`, then
the named BACKLOG items, then `git log` for each item's arc.

**Scope rule:** these four are registered at minutes-to-an-hour each — do all
four in THIS session, in the order below. If one measures materially larger
once opened, STOP that item, write it its own prompt in `prompts/` (house
style: attackable claims, acceptance criteria, self-retiring), record it as
DEFERRED in your report with the acceptance criteria a later audit session
will check, and finish the rest.

**Before editing any chain script:** `pgrep -f run_set_chain; pgrep -f
run_session_chain; pgrep -f run_undistort; pgrep -f run_corpus` — a bash
script edited with an invocation in flight executes garbage (registered trap;
it corrupted a pilot build once).

---

## B1 — pin the registration defaults (BACKLOG `unpinned-registration-defaults`)

No generated `.ssf` in the stacking path pins `-transf=` or `-interp=`, so
both ride Siril's defaults and a version bump can silently change EVERY
stack. Same family as the `setext` / `setcompress 0` / `set32bits` pins
already enforced by `check_bitdepth.sh` (persisted-or-version-supplied state
that nothing asserts).

- Enumerate every `register` / `seqapplyreg` emission:
  `grep -rn "register \|seqapplyreg " scripts/stack/ scripts/qa/` — builders,
  compose, frame QA, probes. Decide per site whether the pin applies
  (an analysis-only register still deserves it for record stability; say so
  either way).
- The doctrine is homography + lanczos4 WITH clamping (`TOOLS.md`). Get the
  exact flag tokens from the tool, not from memory: `siril-cli` `help
  register` / `help seqapplyreg` on-rig, and note that clamping is a DEFAULT
  you preserve by NOT passing its off-switch — pinning means the explicit
  interp/transf flags plus asserting the off-switch is absent.
- Extend the guard (`check_bitdepth.sh` or a sibling with the same per-block
  limits) to require the pins in emitted blocks.

**Acceptance:** (1) guard goes RED when one pin is deleted, green restored —
executed, not argued; (2) NO behavior change, proven by a scratch recompose of
aug06/set-01's five members with the pinned flags, differenced against the
shipped `stack_set-01_full.fit` with siril `isub` + `stat` → all-nil three
channels, with a `fmul 1.01` positive control printing nonzero (the compose
stage is measured bit-reproducible — this exact method verified the `setref`
pin; see git log `tier-A(chain)`); (3) BACKLOG item removed entirely.

## B2 — the preflight proves vignetting is OFF (BACKLOG `route-recommendation`, bullet 1)

`verify_lens_card.py` exists and passes on this rig (grid positive control +
uniform card — the card ALONE is vacuous, the grid proves the module fires)
but NOTHING calls it from the chain: a `darktable`/`lensfun` update can
silently reintroduce vignetting double-correction (measured 1.27–1.37×
corner/centre when it was live). Wire it into the `lens_preflight.py
--require-profile` path (one call site; the builders and `run_set_chain.sh`
already run that). Record the per-run cost; if it is seconds-class, it runs
unconditionally with `--require-profile`.

**Acceptance:** fire test executed — reinstall the lens's `<vignetting>`
block into the live lensfun user DB (hand-edit; `install_lens_model.sh`
re-strips it, which is your restore path), run the preflight → it must
REFUSE naming the vignetting; restore → green. Update the item's remaining
bullet or remove it if this closes it.

## B3 — prove the aircraft actually rejected (BACKLOG `aircraft-rejection-retest`)

The user ratified KEEPING july31/set-03's aircraft crossing
(`DSC_5151..5158`, 8 consecutive frames of 500 — both audit objects are one
airframe, two parallel trails) on a mechanism argument that is
ROUTE-DEPENDENT and has never been measured. The item has the full brief;
the registry's ratified-fraction entry has the route trap.

- Build the control: the same set with the 8 frames excluded. The exclusion
  shifts every later group boundary, so the honest control is a full groups
  rebuild of set-03 to a SEPARATE `--out` (background it; ~an hour). Do NOT
  overwrite the shipped stack or its members.
- Difference ratified-vs-control (siril `isub`) and `stat` ALONG THE
  AIRCRAFT'S TRACK (geometry from
  `datasets/july31/set-03/audit_work/anomaly_audit.json`), not whole-frame —
  whole-frame statistics measured blind to exactly this class.
- Nil on-track residual → the keep is verified free depth. A visible trail
  or level step → the keep was wrong: it becomes a recorded cull with its
  numbers and a `docs/dead-ends.md` entry.

**Acceptance:** the verdict states its ROUTE and group size (groups@~100,
GESD `rej g 0.3 0.05` — the argument's denominator), lands in
`datasets/july31/experiments.jsonl`, and the BACKLOG item is removed either
way. Delete the control stack after the verdict is recorded.

## B5 — the blind solve must not contradict its own hints (from the corpus incident)

MEASURED, this week: the corpus union's hinted solve failed (seam-
contaminated detection on a framing=max canvas), and `solve_field.py`'s
blind fallback then SHIPPED a false solution — RA 6.0 Dec −65.1, scale
12.96″/px, logodds 22 — against header hints of RA 309.8 Dec +41.7 r15 and a
17″/px scale family. Every real solve on this corpus posts logodds 100–570.
The finish stage proceeded on the bogus WCS until killed by hand
(`scratchpad` corpus.log carries the sequence; the remedy that worked was
`--central=0.5`).

Two aggravators, both measured in the same incident: (a) siril SPCC ran to
completion on the bogus WCS and produced plausible-looking K factors
(R 1.000 G 0.592 B 0.817, "1790/5153 stars kept") instead of failing — a
confident falsehood one step downstream, so the solve is the ONLY place this
can be stopped; (b) `--central` is a HALF-WIDTH fraction (`|x−w/2| >
central·w`), so `--central=0.5` excludes NOTHING — a no-op that masqueraded
as a recovery attempt. Fix the semantics or refuse values ≥ 0.5, and align
the docstrings (`solve_field.py`, `finish_render.sh`) with whichever ships.

Design the gate in `solve_field.py`: when header/CLI hints exist and the
accepted solution contradicts them (position beyond ~2× the hint radius, or
scale outside a stated band around the header-derived value), REFUSE loudly,
print both the hint and the found solution, and name the escape hatch
(explicit `--ra/--dec` override, or an explicit accept flag). Consider a
floor-class logodds warning independently. State the thresholds' rationale
in the code where they live.

**Acceptance:** (1) the falsification case executed — the corpus stack
`web/results/aug09/stack_july31+aug06+aug09_full.fit` WITHOUT `--central`
must go from "ships a bogus WCS" to "refuses, naming the contradiction"
(do not overwrite the real `_wcs.fit`; solve to a scratch output);
(2) no false refusals on the rebuilt corpus: replay the gate's logic over
this rebuild's recorded solves (`web/results/*/solve_*.json`,
`sessions/*/work/groups_*/solve.log`) and show zero would have fired;
(3) the queue/register notes the new stop as a user-decision exit consistent
with the chain's gate numbering.

---

## Rules

- Official tools do every pixel operation and measurement; these items are
  guards, pins, and one measured retest — no new in-house analysis of any
  deliverable.
- One knob per experiment; a killed hypothesis goes to `docs/dead-ends.md`
  with its numbers. B3's verdict is WIN or clean NULL — never "fixed".
- A check that cannot fail is the repo's most persistent defect: every guard
  added here is proven by BREAKING it once (the fire tests above are the
  acceptance, not optional).
- Comments: load-bearing constraint + numbers, present tense, nothing that
  ages; no chronology (owner rule).
- Every BACKLOG closure removes the item ENTIRELY (history is git's); any new
  divergence gets its removal-conditions row IN THE SAME COMMIT.
- Do not `git push` unless asked. Do not delete raw frames. Retire this
  prompt (`git rm`) when all four items are closed or deferred-with-criteria.

## Deliverable

A cited `.md` at the repo root: per item — what changed, the fire-test
transcript (RED then green), B1's all-nil recompose proof, B3's on-track
numbers and verdict with route stated, B5's refusal output on the
falsification case and the zero-false-fire replay — plus commits, BACKLOG
diffs, and anything deferred with its audit criteria.
