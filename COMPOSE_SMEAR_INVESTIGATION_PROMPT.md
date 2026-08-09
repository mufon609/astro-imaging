# Fresh-session prompt — ROOT-CAUSE the cross-set compose corner SMEAR (undistort/lens-model forensics)

Read `CLAUDE.md` first — it is the briefing and the read order (registry,
TOOLS, MEMORY, README, BACKLOG). This prompt adds the investigation's scope,
its evidence base, and its discipline. **Report-first: diagnostic builds and
probes are allowed and expected; no shipped product is replaced, no default
changes, no fix lands without the user's decision.** MEMORY.md is binding:
synthetic flats are the project's point — flat-related mechanics are fixed in
software, and "real flats" is never a recommendation.

## The defect (re-identified by eyes — do not regress to background metrics)

Cross-set combines of the aug06 sets FAIL on **corner star smear**: at 1:1
the union corners show stars drawn into coherent diagonal dashes over a
brushed fabric; the passing july31 union's corners are round pinpoints.
**Box-median/background instruments are structurally blind to this defect
and are FORBIDDEN as its acceptance measure** — two sessions burned on that
mistake (`COMBINE_CORNERS_AUDIT_report.md` §9; the background findings there
remain true but secondary). The instrument for this defect is the star
surface: Siril `findstar` (open gate) on fixed corner/center boxes +
`seqtilt` + eyes on 1:1 crops. Protocol that produced the numbers below:
`setfindstar -relax=on -roundness=0.05 -sigma=0.5` (NEVER `setfindstar
-reset` inside an `.ssf` — it exits 1 on success and aborts the script,
registry), 800 px boxes, green channel; corner crops viewed at 1:1 before
any verdict.

## Evidence already MEASURED (re-derive what you rely on; instruments and
records in `datasets/aug06/experiments.jsonl` + `COMBINE_CORNERS_AUDIT_report.md`)

Corner-vs-center FWHM (px), Siril findstar:

| surface | corner | center |
|---|---|---|
| aug06 union max+covcrop (own models) — FAILED by user | 4.95 | 3.32 |
| aug06 union min framing (own models) | 4.83 | 3.38 |
| aug06 union max (single PINNED model, from `groups_*_pinned`) | 5.29 | 3.30 |
| aug06 union subsky-lights arm | corner-equivalent to control (judge-PNG DN) | — |
| july31 union min (single matched model) — PASSES | 3.44 | 2.74 |
| aug06 per-set products (own model each) — PASS | 3.87–4.18 | 3.17–3.30 |
| member sub-stacks going in (aug06 / july31) | 3.55 / 3.28 | 3.19 / 2.89 |

**ELIMINATED as drivers, each by one of the measurements above — do not
re-litigate:** framing (min smears equally), model HETEROGENEITY (a
single-model union smears equally), member background matching (subsky arm:
registry dead-end entry), re-aim geometry (july31 spans 6.2° offsets and
16.3° rotations and passes; aug06 spans 3.2°/8.5°), member corner CONTENT
(sub-stacks enter at ~3.5 px), member-edge-zone shipping (the min union's
corners sit +96..+486 px inside per-set canvases, one −99, and still smear).

**The smear is therefore CREATED at the cross-set compose** (members ~3.5 px
→ union 4.9–5.3 px at like zones), on aug06's members only. Pointing
geometry from the solved WCS (aug06: s01↔s03 co-pointed with 8.5° rotation
difference; s02 offset 3.2°; july31: offsets to 6.2°, rotations to 16.3°).

## The hypothesis you are testing (user-steered), and its shape

**The aug06 members are insufficiently rectified at large field radii under
BOTH available models, and cross-pointing registration exposes it**: the
pinned (july-fitted) model is state-mismatched to aug06 (measured, optics
ledger: 2× field-term elevation — the very thing the per-set adoption
resolved for set-01), and the aug06 OWN fits came from a mid-campaign-
modified instrument (short 2.5 s subs, gauss-3 fattening, strict prune —
ledger `fit_instrument_cp_starvation`) with weak corner CP support, and
their products sit +0.1–0.15 px above july31's residual floor —
**unattributed at the time** (`BACKLOG:optical-state-models`, open item a).
july31's members compose clean because their model was fitted to their own
state family (july14 fit, inherited by diagnosis). Mechanism class: the
route's founding law — residual radial distortion is the one term a global
registration cannot absorb — acting at the SUB-STACK composition level,
where members meeting at different offsets/rotations stop sharing a common
residual.

## Pre-registered discriminators, in order

1. **Pairwise two-member composes** (from the preserved sub-stack dirs —
   `sessions/aug06/work/groups_set-0{1,2,3}[,_pinned]`,
   `sessions/july31/work/groups_set-0*` — via
   `run_undistort_compose.sh --framing=max --ref=<first member>`; each pair
   is minutes):
   - a. aug06 s01+s03 sub (co-pointed, ΔPA 8.5°) — rotation-only arm
   - b. aug06 s01+s02 sub (3.2° offset, ΔPA 1.0°) — offset-only arm
   - c. aug06 s02+s03 sub (3.2°, ΔPA 7.6°) — both
   - d. CONTROL: two subs of ONE aug06 set (drift-only; must stay ~3.5 px)
   - e. KILLER CONTROL: july31 cross-set pair at 6.2° offset (expect clean)
   Corner+center findstar on each. Readout: which geometry (offset vs
   rotation) drives the smear, per set — and (e) vs (b) isolates member
   rectification quality from compose geometry outright.
2. **Fit forensics** on the aug06 own models: the preserved fit diagnostics
   (`datasets/aug06/set-0*/qa_work/lens_fit.json`, `lens_fit_work/`) — CP
   radial quarter-bins and CORNER support per fit (the trustworthiness
   predictor: july31's refit read clean checkpto residuals 0.02/0.06 and was
   still WRONG on banded coverage); compare against the july14 fit's
   coverage. The fit-instrument delta (gauss-3, short subs) is the suspect
   the user named — "the recent change to the lens variables".
3. **Chain forensics** ("is something just broken / cross-referenced"):
   pin the exact HEADs the july31 members (mtimes 08-06 21:47–23:45) and
   aug06 members (08-07 21:00–08-08 07:38, own and pinned arms) were built
   at; diff `run_undistort_pipeline.sh`/`run_undistort_groups.sh` between
   them; verify per-build model installs from each set's
   `qa_work/lens_preflight.json` + darktable/dtcfg logs (the lensfun user DB
   is GLOBAL machine state — last install wins; only the preflight guards
   it). Known cross-session couplings to verify, not assume: the lensfun DB,
   and july31's inherited-from-july14 model record.
4. Only if (1) implicates rotation specifically: research + design the
   registration-side options (Siril `-disto=` with a trustworthy model,
   member refits with corner-gated windows) — as PROPOSALS.

## Discipline

- One knob per arm; hypothesis stated before each run; verdicts WIN/NULL/
  REFUTED with numbers into `datasets/aug06/experiments.jsonl`
  (`compose_smear_root_cause`); killed hypotheses become registry entries.
- Star instruments + 1:1 eyes for this defect; background instruments only
  as secondary context. View corner crops (Siril crop+savepng) yourself
  before any claim about a surface.
- Preserved discriminator surfaces from the prior session (do not rebuild:
  measure them): `stack_set-01+02+03_{full,min,full_pinnedmodel,
  full_subsky1}*` + judge PNGs + `sessions/aug06/work/subsky_arm/insp_*.png`
  + `st_*.lst`.
- Candidate fixes are proposals ranked with evidence; the user decides.
  Route-policy interim options (e.g., combines only from matched-state
  members) are proposals too, never defaults.

## Deliverable

`COMPOSE_SMEAR_INVESTIGATION_report.md` at the repo root, committed: the
discriminator table with numbers, the fit/chain forensics findings, a
MEASURED/HYPOTHESIS-labelled root-cause statement, and the ranked fix
proposals for the user. Ledger entries as you go. Stop at the report.
