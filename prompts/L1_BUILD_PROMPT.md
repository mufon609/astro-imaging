# Fresh-session brief — L1 build: run both arms of the background-level experiment

**SELF-RETIRING.** Delete this file in the commit that lands the verdict.

**The pre-registration IS the contract, and it is already written.** Read
`datasets/aug06/experiments.jsonl`, id `l1_background_level_perframe_vs_onstack`,
before anything else. It defines both arms, the held-fixed list, the control with
its exact header values, the directional hypothesis with its mechanism, a
separate falsifier for each arm, the instrument and how to read it, the judge
surfaces, and the rings status. **Do not restate it here and do not re-derive it.**
This brief adds only what the pre-registration does not cover, and one item it
does not pin that can waste the whole run.

The owner has authorised the full member rebuild and both arms, with time
explicitly not a constraint. What is asked for is a proper test, not a fast one.

## The one thing the pre-registration does not pin — fix it FIRST

The pre-registration's held-fixed list ends "reference pinned and mirrored into
each arm". That is the **compose** reference — which sub-stack the members are
composed against. It does **not** pin the per-group `register -2pass` reference
inside each member build, and that is a measured trap.

**Mechanism, and it is not hypothetical.** `register -2pass` chooses its
reference frame from image QUALITY. Arm A changes the calibrated lights — it
subtracts a degree-1 plane from every frame before the warp — which changes each
frame's statistics and therefore can change which frame wins the reference
ranking. The flat-differential session measured exactly this from a calibration
change: one arm picked image 1 and a 4896×3616 canvas, the other image 2 and
4887×3641.

**Why it matters HERE specifically, which is different from why it mattered
there.** The starlight instrument places its cells by WCS, so a different canvas
does not break it the way it broke a pixel-ratio. What it breaks is the
**pairing**: a different canvas covers different sky, so different lattice cells
end up `used`, and the paired retained fraction is then computed over
non-identical cell sets. The paired number is the whole resolving power —
5–16% against 43–55% for an absolute slope — so losing the pairing costs the
experiment its sensitivity.

**And the flag is not plumbed where you need it.** `--regdata=<lt_.seq>` exists
in `run_undistort_pipeline.sh` and is absent from `run_undistort_groups.sh` and
`run_set_chain.sh` — verified. Arm A runs through the groups route across 13
members, so as things stand it cannot pin.

**Do this, in this order, before building anything:**
1. **Measure whether the reference actually moves.** A ~12-frame pilot, one knob
   (`--subsky-lights`), comparing the chosen reference index and the output
   canvas. Cheap, and it is the pattern that caught the same class last time.
2. If it moves, **plumb `--regdata` through the groups driver** and pin every arm
   to the control's registration data. That is a build-path change, so it lands
   with its own verification that transforms are identical across arms.
3. If it does not move, **record the measurement** and proceed unpinned, with the
   pilot numbers in the record. Either way the answer is measured, not assumed.

## Order of operations — cheap arm first, and it can stop the run

**Run ARM B before ARM A.** Arm B reuses the control union and is cheap; arm A is
a 13-member rebuild over 1500 frames. Two reasons the order matters:

- **Falsifier B is a stop condition, not a result.** The pre-registration says a
  retained fraction below 0.90 at >2 SE on arm B means the instrument or the
  catalogue bound is wrong — "the run stops to resolve that before either arm is
  judged." Discovering that after the rebuild wastes the rebuild.
- It gives an early read on whether the paired instrument separates anything at
  this effect size, which is the pre-registered doubt.

Arm B also carries the pinned **crop-to-verified-coverage BEFORE the background
step** — the registry's order, because `subsky`'s sample grid ingests a union
canvas's zero-coverage rims and its `-tolerance` excludes only bright outliers,
not empty sky.

## Scope, verified on disk

13 members (5 + 4 + 4), 1500 frames across aug06 set-01/02/03, 873 G free. The
control is untouched and stays untouched: `sessions/aug06/work/groups_set-0{1,2,3}`
and `web/results/aug06/stack_set-01+02+03_full{,_wcs,_spcc}.fit`. Arm A writes to
its own paths; if the control is modified, the experiment is over.

## State this in the write-up, do not work around it

**Every retained value on these products will come back above 1** — 1.23 to 1.85
was measured on the research pass. Starlight is not being created: the open
`sky × V` residual is **anti-correlated** with the starlight and biases the raw
slope low, so removing any low-order surface raises it. The pre-registration says
to expect this and the paired form is what absorbs it.

The consequence worth stating plainly rather than burying: **this background
question and the paused flat defect are entangled in the measurement.** Say so in
the verdict. Do not use it as a reason to reach into the flat line, which the
owner has paused pending real flats — and do not let a background question drift
into a flat question.

## Fenced

- **The flat-residual line is PAUSED.** Do not touch it.
- **The stale `subsky1` records are NOT a control** — the pre-registration names
  them and says why; their products do not exist.
- **Corner spread is not an admissible judge**, and corner-vs-centre is
  self-fulfilling. The instrument, the grid-fitted ramp slope and the owner's
  eyes are the judges.
- Raw-domain de-sky (the flat-side half) stays dead, and the two halves must
  never share a flag again.
- Degree ≥2 is **not a third arm** — the research settled it: a quadratic can
  represent at most 36.2% of this field's starlight variance against a plane's
  10.0%, so degree is a real difference but not erasure, and it is out of scope
  here. Do not cite the parity dead-end against it either; that entry is about
  un-flat-fielded frames.
- **No acquisition answer.** The data is a given.

## Close the one gap the research could not

`member_separation.py --selftest` cannot run — no complete sequence survived the
from-raws rebuild, which is data availability rather than a code fault, and its
register row now says so. Arm A's build produces exactly the sequence it needs.
Run the selftest when one exists and update the row with the result.

## Acceptance — executable, each with what you ran

1. The reference-stability pilot is run and recorded BEFORE any arm is built,
   with the pinning decision following from its numbers.
2. Both arms built, control untouched and verified untouched afterwards.
3. Both falsifiers evaluated explicitly, by name, against their stated
   thresholds — including the CONFIRMED-AS-EQUIVALENT branch, which is a real
   pre-registered outcome and not a failure.
4. The paired retained fractions reported with their SE, alongside the
   catalogue-only bound and the shift-null p-value, per the pre-registration.
5. The judge triple rendered like-encoded to
   `web/results/aug06/judge/` and handed to the owner. **The instrument gates
   nothing**; the owner's eyes on the full-frame 16-bit PNG decide anything
   aesthetic.
6. Five guards and every selftest PASS, `member_separation` included once its
   sequence exists; `--plan` still walks a session clean.
7. Every number carries its instrument, n, and the box's `uptime`.
8. Any build-path change lands with its own verification and its register row in
   the same commit; `prompts/REPORT.md` updated; this file deleted in it.
9. `pgrep -f` any chain script before editing it, and if a peer session is
   running: stage explicit paths, never `git add -A`; hold build-path commits
   while their chain is in flight; re-read a whole section before writing to one
   they are also working (`CLAUDE.md`, parallel sessions).

## Honest failure

**A NULL here is pre-registered, expected as a live outcome, and must be reported
as one.** The arms may not separate: an on-stack plane is bounded at 10.0% and
the paired instrument resolves 5–16%, so they can only differ if the per-frame
step reaches structure a single sky-plane cannot. If retained_A and retained_B
agree within their combined SE, that kills the directional prediction and the
level choice falls to the other criterion and the owner's eyes — report it that
way, not as a failed experiment, and do not go hunting for a difference until one
turns up in the noise. **The NULL is the most valuable result this program
produces**, and it has banked several. Never "fixed/final/matched/close".

Verify everything in this brief against the repo before relying on it.
