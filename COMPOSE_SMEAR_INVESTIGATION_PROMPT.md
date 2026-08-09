# Fresh-session prompt — INDEPENDENT investigation: cross-set combines smear at the corners. Find when this broke, and why.

Read `CLAUDE.md` first — it is the briefing and the read order (dead-end
registry, TOOLS, MEMORY, README, BACKLOG). `MEMORY.md` is binding; two lines
of it especially: **synthetic flats are the point of this project — every
fix is a software fix inside the flatless route, and "shoot real flats" is
never a recommendation** — and the user judges by eye on full lossless
surfaces; tool metrics alone have already missed this defect once.

## The situation, as the project owner has explained it

Multi-session, multi-pointing combining is NOT new in this repo. It has been
done repeatedly, and it works: the july31 four-set combine
(`web/results/july31/judge/set-01+02+03+04_full_spcc-linked.png`, 1,760
frames) passes the owner's eyes today. The new aug06 combines FAIL — their
corners are smeared. **The problem is new. This repo changes one variable at
a time, so a new problem points at a recent change.**

The recent change in this area is the lens/optical-state work: the pipeline
stopped using one pinned lens-distortion model and moved to a PER-SET model,
fitted from each set's own frames and installed into the (public) lensfun
database at build time. That change was itself the mitigation of an issue
the owner considered well defined and resolved: **calibration state from one
night silently serving another night's processing.** The owner's concern is
that this mitigation — or its implementation — is what is now causing the
corner smears.

The owner's questions, which the report must answer explicitly:

1. **What is broken in the undistort pipeline?** Is something just broken,
   or is something being referenced from one session to another?
2. **Does every calibration input used in each build come from that
   session's/set's own images?** Dark, sky flat, lens model — audit the full
   provenance chain of what each build ACTUALLY consumed (records, logs,
   file timestamps), not what the design says it should consume. Using the
   public lens database is fine — but when the pipeline tweaks it, what is
   the lifecycle of that tweak? **Does one night's fit calibrate it
   forever?** Surface every carryover, deliberate or accidental.
3. **When exactly did this start being an issue?** Tie the onset to specific
   commits and specific builds. Past combines pass; these fail; the boundary
   between those two facts is in the git history and the build records.
4. **Was the issue the last change was mitigating actually resolved — and
   did the change cause this one?** The owner thought the cross-session
   calibration problem was closed. Verify that it is, and whether its fix
   introduced the smear.

## History of this issue in the repo (verify everything in git — do not take this summary on faith)

- Cross-set combining is standing practice; the groups route exists so
  sub-stacks stay on disk for it. Combines shipped from july14 (cov25 era,
  old 16-bit chain, products deleted), july23 (a corner-chroma defect was
  found there, investigated, and driven to a calibration-side diagnosis; the
  `--desky` fix arc shipped and was reverted as a 31× regression), july31
  (the four-set combine that passes today), and aug06 (the failing twins).
- The optical-state arc immediately precedes the failures: the pinned
  (july-fitted) model was measured mismatched on aug06 (2× field-term
  elevation), per-set fits were adopted (set-01 decisively better; other
  sets measurement-equivalent), and the fitting instrument itself was
  modified mid-campaign for aug06's short subs (`fit_instrument_cp_starvation`
  ledger entry). july31's sets deliberately INHERIT the july14-fitted model
  (recorded provenance) because july31's own refit was diagnosed
  untrustworthy. Relevant records: `BACKLOG:optical-state-models`,
  `datasets/*/set-*/qa_work/lens_fit.json`, the optics commits around the
  aug06 builds.
- Two audit sessions have since worked the corner failure. Their trail:
  `COMBINE_CORNERS_AUDIT_report.md` (maintained current-state),
  `datasets/aug06/experiments.jsonl` (`combine_corner_fail_investigation`,
  `subsky_lights_restoration`), registry entries in `docs/dead-ends.md`,
  and preserved evidence surfaces (failed products, discriminator unions
  `stack_set-01+02+03_{min,full_pinnedmodel,full_subsky1}*`, judge PNGs,
  1:1 inspection crops and findstar lists under
  `sessions/aug06/work/subsky_arm/`).

## Hypothesis state going in — rank it against your own evidence

Two candidate roots survive the prior sessions' eliminations, and the order
of work matters:

- **Verify execution/provenance FIRST (owner's questions 1–2) — it is cheap
  and it gates everything else.** If any build consumed a different model
  than its record claims (the lensfun DB is global machine state; the
  preflight guards it, but this repo's registry documents three consecutive
  guards that could not fail), the fit investigation below is moot until
  corrected. Prove what each build actually used; do not accept the guard's
  design as the proof.
- **The LEAD hypothesis, once execution is cleared: the aug06 fits' corner
  quality.** Measured bracketing: the pinned model smears aug06 (it is
  state-mismatched, measured), aug06's OWN fits also smear (so they too
  leave corner residual), and july31's matched fit composes clean at larger
  offsets/rotations (exonerating the per-set method and the compose code).
  Supporting records: the fit instrument was modified mid-campaign for the
  2.5 s subs (`fit_instrument_cp_starvation`); every aug06 fit needed strict
  CP pruning; the corner-support trustworthiness predictor was recorded but
  never applied as a gate; and the own-model products' +0.1–0.15 px
  elevation over july31's floor sits in the optics ledger as "unattributed"
  — a corner-concentrated error averages down to exactly that kind of
  whole-frame signal. Both points are claims to verify, not conclusions.

## The prior sessions' work is AUDIT MATERIAL, not findings you inherit

Everything in that trail — the re-identification of the defect as corner
STAR SMEAR (not background level), the elimination measurements (framing,
model heterogeneity, background matching, re-aim geometry, member content,
member-edge zones), the "members enter ~3.5 px / union exits ~4.9–5.3 px"
compose-created finding, and the leading hypothesis (aug06 members
insufficiently rectified at large radii under BOTH model eras) — is a set of
claims with recorded instruments. **Re-derive what you rely on. Audit the
prior sessions' work the way the first audit was told to audit its
predecessor: trace every deciding number to an official tool, a record, or
say plainly that it traces to nothing.** If your independent measurements
contradict the trail, the measurements win and the records get corrected.

Design your own investigation. The preserved sub-stack dirs
(`sessions/{aug06,july31}/work/groups_*`) make cheap diagnostic composes
possible in minutes if you want discriminators; the choice of method is
yours. Two disciplines are not optional, because their absence already
burned this investigation once: **look at every surface you judge, yourself,
at 1:1** (Siril crop + savepng, then view) — the defect is visible star
smear, and background box statistics are blind to it; and one knob per
experiment, hypothesis pre-registered, verdicts with numbers into the
ledger, killed hypotheses into the registry.

## Deliverable

`COMPOSE_SMEAR_INVESTIGATION_report.md` at the repo root, committed:

- The owner's four questions answered explicitly, each with its evidence.
- A calibration-provenance table for the builds involved: every input each
  build consumed (dark, flat, lens model — with WHERE it came from and WHAT
  proves that), and every cross-session reference found, labeled deliberate
  (with its record) or accidental.
- The onset: which commit/build boundary separates passing combines from
  smeared ones, with the discriminating measurements.
- A root-cause statement, MEASURED vs HYPOTHESIS labelled, that explains ALL
  of the evidence — including why july31 composes clean at larger offsets
  and rotations than aug06.
- Ranked fix proposals — software-side, inside the flatless route — for the
  owner to decide. No fixes executed; no products replaced; nothing ships.
