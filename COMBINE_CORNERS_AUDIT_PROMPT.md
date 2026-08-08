# Fresh-session prompt — INDEPENDENT audit: the combine-corner defect, and the process that produced it

Read `CLAUDE.md` first — it is the briefing and the read order. This prompt
adds only the audit's scope and its independence rules.

**The work is PAUSED at the user's order. This is an AUDIT, not a build.** Do
not modify products, do not attempt fixes, do not write new pipeline code.
The deliverable is a report: findings, researched comparisons, and a
recommended path — every recommendation carrying its source (official docs,
tool forums, published workflows) or its measured basis.

## What happened (state, not conclusions)

The twin cross-set combines — aug06-only
(`web/results/aug06/stack_set-01+02+03_full.fit`, 13 sub-stacks / 1,454
frames) and six-member (`stack_j31-3+a06-3_full.fit`, 28 sub-stacks / 2,954
frames, spanning two nights) — were coverage-cropped
(`stack_*_cov13.fit` / `*_cov28.fit`) and judged by the user: **both FAILED
on bad corners, while every per-set stack's corners look fine.** A 450 px
inset recrop was then built and was **revoked by the user as a bandaid** (it
cropped out the symptom, halving the canvas; the defect is in the data).
Everything stands preserved for you: the composes, the coverage maps
(`covmap_*.fit`), the failed judge surfaces (`web/results/aug06/judge/
set-01+02+03_cov13_spcc-linked.png`, `j31-3+a06-3_cov28_spcc-linked.png`),
and the prior session's measurements under
`datasets/aug06/set-03/qa_work/` (`bg_grid_*.json`, `corner_profile_*.json`,
`regional_stat_cov*.json`) with ledger entries in
`datasets/aug06/experiments.jsonl` (`combine_corner_fail_investigation`).

## Independence rules (the basic brief)

- The prior session's mechanism claims — boundary sensor-corner convergence,
  depth-dependent stretch amplification, a half-sky/half-member residual
  patch — are **HYPOTHESES you audit, not findings you inherit.** Re-derive
  anything you rely on; distrust anything that traces only to that session's
  own in-session arithmetic.
- The user is explicitly worried the project has been **guessing at this
  problem and drifting into in-house code, metrics and decisions.** Treat
  every number, threshold and derivation in this area as a claim whose
  provenance you must trace to an official tool, a published source, or a
  recorded measurement — and say plainly which ones trace to none of those.
- Nothing you conclude is final until it carries its source or its
  instrument. MEASURED vs HYPOTHESIS labels throughout.

## The audit's questions (the user's, verbatim in spirit)

1. **Is this normal for our rig?** Are corner residuals of this size the
   expected behavior when composing multi-pointing, sky-flat-calibrated,
   wide-field sub-stacks by register + mean? Establish what "normal" looks
   like from primary sources, not from this repo's own records.
2. **Where are the deciding numbers coming from?** Audit the provenance of
   every deciding quantity in this area: the coverage full-coverage
   threshold, the crop-rectangle derivation (an in-session numpy
   largest-rectangle over the coverage map — never reviewed as pipeline
   code), the 450 px inset (derived from an in-session box-profile over
   Siril stats), the corner-spread and grid metrics themselves, the
   `--weight=nbstack` choice, the pinned compose reference, and the judge
   stretch policy applied to combines 3–6× deeper than any per-set product.
   Which of these are official-tool numbers, which are in-house analysis,
   and which are unreviewed session improvisation?
3. **What do others do?** Research online — official documentation and
   community practice (Siril docs/forum, PixInsight forums/WBPP+mosaic
   tooling, Astro Pixel Processor's multi-session/mosaic normalization,
   published mosaic workflows) — how the mainstream combines overlapping
   pointings and multi-night data: background/overlap normalization before
   or during the combine, gradient removal placement relative to the
   combine, mosaic-specific tools vs plain register+stack, edge/feathering
   handling, and how they frame/crop the result. The repo's compose is a
   plain register + mean with no background matching between members — is
   that the amateur shortcut, and what is the professional-standard step it
   is missing? Note that a linear background step for this repo is already
   an open, user-gated item (`BACKLOG:render-ladder` L1, scope-fenced until
   now) and the sky-flat `sky × V` object tilt is a known open defect —
   connect the research to those existing records rather than duplicating
   them.
4. **How does this workflow become more professional?** Enumerate the
   in-house code, metrics and decision points this area currently relies on,
   and for each: the official tool or published method that could replace
   it, or the honest statement that no tool provides it (a documented gap
   per the bright line in `CLAUDE.md`). The north star is fewer in-house
   surfaces, not more.

## Deliverable

One report at the repo root (`COMBINE_CORNERS_AUDIT_report.md`, committed):
the provenance audit table, the researched mainstream comparison with
sources, a verdict on whether the corner behavior is defect or expectation
(MEASURED/HYPOTHESIS-labelled), and a recommended path that the USER decides
on — including what to adopt, what to test first, and what in-house pieces
to retire. Stop there; no fixes in this session.
