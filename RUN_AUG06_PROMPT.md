# Fresh-session prompt — process aug06 from raws, then the two-session combine

Read `CLAUDE.md` first. It states what this repo is, the binding rules, and the
order to read everything else in — including
`docs/pipeline-wide-field-untracked.md`, the validated chain this data class
runs. That is the whole briefing; the repo carries the rest.

`sessions/aug06/` holds raw frames only: four light sets + a darks group
(source inventory, verified against the tracked
`datasets/aug06/source_manifest.md5`: set-00 140, set-01 502, set-02 500,
set-03 500 lights + 328 darks = 1,970 NEFs — VERIFY the staged counts and
checksums yourself: `cd sessions/aug06 && md5sum -c
../../datasets/aug06/source_manifest.md5 --quiet`). Same
target, camera and settings as the validated july31 corpus (Z6III,
24-70 @ 70 mm, 2.5 s, ISO 1600) per the acquisition plan — the solves verify
the field; report if it does not overlap july31's instead of assuming.

## Goals, in order

1. **Every aug06 set through the chain to judged products** — the walkthrough's
   route exactly: measure → ONE readiness report → the single approval → build
   → judge surfaces. The chain derives everything derivable (mount, route,
   cull, groups); baselines seed only after the user accepts the products.

2. **The combine is the point.** After the per-set products, compose across
   BOTH sessions: july31's retained sub-stacks
   (`sessions/july31/work/groups_*/`) plus aug06's. Verify what
   `run_undistort_compose.sh` actually supports for a cross-session member
   list before assuming it composes one — and the cross-set record home is a
   known gap (BACKLOG:`cross-set-record-home`): a session-spanning product's
   records must not be filed under a member set; degrade loudly and report
   rather than inventing a location silently.

3. **Combine membership is RATIFIED (user): FULL sets only — the largest
   fully-covered crop wins.** A short member's drift span cuts the common
   canvas, so sets under ~500 frames are OUT of the combine:
   aug06/set-00 (140 — single-pass by user order, a standalone test set,
   never a combine member) and, by the same criterion, july31/set-04 (260 —
   confirm that reading with the user before composing). Members: the
   ~500-frame sets of both sessions. STILL MEASURE it: run
   `scripts/qa/coverage_probe.sh` on the ratified member list — and cheaply
   on the all-members counterfactual — so the combine's record carries the
   measured canvas-vs-depth numbers BEHIND the decision (fully-covered
   area, member count, effective frames). That is a record of a decided
   question, not a re-opened one.

Work the way the contract says: the tools measure, the chain routes what the
data settles, you stop only where a decision is genuinely the user's, and
every result is reported as measured — WIN, clean NULL, or needs-eyes, with
its instrument and numbers. Nothing is "fixed" or "final" until measured;
aesthetics are the user's eyes on full-frame lossless finals. Report what you
measured, what you chose, what you rejected, and anything you could not
explain.
