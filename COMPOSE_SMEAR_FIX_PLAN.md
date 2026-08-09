# Implementation plan — F2 / F3 / F4, under the ratified combine fundamentals

Scope: the plan only. Nothing here is wired. Sources for every number:
`COMPOSE_SMEAR_INVESTIGATION_report.md`, `datasets/aug06/experiments.jsonl`
(`pairwise_member_compose_discriminator`, `cross_night_state_difference`,
`undistort_normalization_and_corner_divergence`, `fit_corner_support_census`),
`datasets/aug06/set-03/qa_work/compose_smear_measurements.json`.

Labels: **MEASURED**, **ARITHMETIC**, **HYPOTHESIS** (with the test that settles it).

---

## 0. The measured basis this plan is built on

| quantity | value | where |
|---|---|---|
| lensfun ptlens normalisation | half the SHORT side (2020 px here) | probe, RMS 4.47 vs 18.3 / 22.2 px |
| frame corner in that convention | **ρ = 1.80** | ARITHMETIC |
| CP support of every fit ever shipped | p50 0.62–0.86, p99 1.43–1.48, **max 1.47–1.51** | `fit_corner_support_census` |
| same-set member disagreement (floor) | **0.14 px** (aug06), **0.19 px** (july31) | member-separation instrument |
| cross-set, one model, matched state | **0.35 px** (july31 — user-PASSED product) | same |
| cross-set, one model, mismatched state | **0.93 px** (aug06 under pinned; round at 1:1) | same |
| cross-set, different models | **2.99 / 2.11 px** (user-FAILED products; doubled at 1:1) | same |
| **cross-NIGHT, one shared model** | **4.07 px** | `cross_night_state_difference` |
| model-pair divergence through the warp | up to **8.19 px** | grid fixture |
| member residual distortion (SIP, order 3) | aug06 26–30 px, july31 13–21 px | astrometry.net |

**The one-line reading:** disagreement below ~0.35 px has produced a product the
owner accepted; disagreement at 2.1–3.0 px has produced products the owner
failed; 0.93 px is the only measured point in between and it looks round at 1:1.

---

## 1. Point 1 — every item below is evaluated against the COMBINE unit

The failure shape being designed out: *correct per-set, degrading to the
combine, silently*. Each work item therefore states what it does to the combine,
not only to the per-set product.

| item | per-set effect | **combine effect** |
|---|---|---|
| F3-header (stamp optics+calibration provenance) | none | makes a sub-stack self-describing months later — the precondition for every other gate |
| F3-gate (compose asserts compatibility) | none | **makes a smearing combine impossible to build silently** |
| F4-instrument (member separation) | none | gives the combine an acceptance measure that is not blind |
| F2 (corner-true fits) | may raise in-field residual — trade in §7 | **the only route to cross-night combining**; 4.07 px says a shared model is not one |
| F1 (shared family model) | costs each set its own state | same-night fallback only; **measured not to cross nights** |

A change that improves a per-set number and is not measured at the combine is,
by this table, unfinished work.

---

## 2. Point 2 — THE COMBINE CONTRACT (the deliverable of this section)

*Proposed to live at `docs/combine-contract.md`, linked from `CLAUDE.md`'s read
order and `datasets/README.md`.*

### 2.1 The claim it rests on

The chain is reproducible from raws + tracked records — pinned tool versions in
`scripts/setup/manifest.tsv`, no unseeded step on this route, and the render tier
measured bit-reproducible on this rig. **Therefore image data is a cache and
records are the asset.** Everything below follows from that and nothing else.

### 2.2 KEEP — the archival keep-set, per set (loss of any item is unrecoverable)

**Off-rig, the only irreplaceable bytes:**
1. The set's raw frames.
2. The session's dark raws (the master dark is regenerable, the darks are not).
3. The source-integrity manifest (server-side md5s — aug06 has 1,971 of them).

**In git, the per-set records (small, already the repo's job):**
4. `acquisition.json` — EXIF facts + the derived `mount`.
5. `recipe.json` — the ratified cull (`stack.exclude`). *Determines which frames
   are in; without it the rebuild is a different stack.*
6. `geometry.json` — foreground mask/rect.
7. `qa_work/skyflat_<set>_qa.json` — the sky flat's build recipe, its dark
   identity, and its QA gate. *The flat is synthetic and rebuilt from the set's
   own frames; this record is the recipe.*
8. `qa_work/lens_fit.json` — the optical-state model, its provenance
   (`inherited_from` where applicable), and — **new, F2** — its CP corner-support
   census.
9. `qa_work/lens_preflight.json` — what was actually installed and verified live.
10. `qa_work/anomaly_audit.json` + `qa_work/frame_metrics.json` — the cull's
    evidence AND the dwell floor the group size is derived from.
11. `readiness.json` — the approval the build ran under.
12. The repo commit + `scripts/setup/manifest.tsv` (tool versions).

### 2.3 REGENERATES — cache, never load-bearing

Master dark; sky flat; calibrated/debayered frames; warped TIFFs; the group
`g*.list` files; sub-stacks (`sub_NN.fit`); per-set stacks; unions; judge
surfaces. Delete freely.

**Group membership regenerates deterministically** — consecutive blocks over the
sorted, culled frame list, with the group size derived from N and the dwell floor
in the tracked `anomaly_audit.json` (`run_undistort_groups.sh`). This is stated
as a **HYPOTHESIS with a cheap test**: re-derive the groups for aug06/set-01 from
the tracked records alone and diff against the preserved `g*.list`. Until that
passes, treat `g*.list` as KEEP, not cache. *(This is the one place the
"records are enough" claim is currently unverified, and it is a one-command
check.)*

### 2.4 What a future night needs to JOIN an old archive

1. **Its own corner-true optical-state model** (F2). Not the old night's — states
   differ, MEASURED at 4.07 px corner disagreement between a july31 and an aug06
   member under one shared model.
2. **The old night's members**, either from its cached sub-stacks or rebuilt from
   §2.2 — and either path must yield sub-stacks whose headers answer §3.
3. **A compatibility measurement between them** (§4) before anything composes.

**HYPOTHESIS, and it is the load-bearing one for the whole multi-night road:**
cross-night combining does not require a shared model — it requires each night's
model to be CORRECT. Two members each correctly rectified agree in the SKY
regardless of which coefficients produced them; the 4.07 px number was measured
under a *shared* model, i.e. a model necessarily wrong for one of the two nights,
so it measures the state difference that a wrong model failed to remove, not an
inherent barrier. **Nobody has yet measured two corner-true models composing
across nights, because no corner-true fit exists (§0).** The test that settles
it is exactly F2's acceptance run: fit july31 and aug06 each to corner support,
compose one member from each, and read the member separation. If it lands at the
0.14–0.35 px floor, multi-night combining is solved; if it stays near 4.07 px,
the per-state route is refuted and that is a finding the owner must see.

---

## 3. Point 3 — self-describing sub-stacks (F3a)

Every sub-stack must answer *"what warped you, what calibrated you"* with no
external lookup, no machine state, no memory of the session.

### 3.1 Keys (FITS 8-char, added to `stamp_headers.sh`'s `_STAMP_KEYS` block)

| key | value | source |
|---|---|---|
| `DISTMODL` | `ptlens` | the installed DB entry |
| `DISTA` `DISTB` `DISTC` | the coefficients **verified live in the DB** at build time | `lens_preflight.json` → `state_model.coefficients` |
| `DISTNORM` | `2020` (px) — the normalisation radius | ARITHMETIC from `min(W,H)/2`; the convention is MEASURED |
| `DISTRHO` | the fit's CP support ceiling (p99 ρ) | `lens_fit.json` census (F2) |
| `DISTSRC` | `aug06/set-01` or `inherited:july14/set-01` | `lens_fit.json` provenance |
| `CALSET` | `aug06/set-01` | the build |
| `CALDARK` | master dark identity (basename + frame count) | `skyflat_*_qa.json` / dark log |
| `CALFLAT` | sky flat identity (basename + frame count) | `skyflat_*_qa.json` |
| `PIPEREV` | repo commit short hash | `git rev-parse --short HEAD` |

Alongside the existing `FOCALLEN XPIXSZ YPIXSZ EXPTIME APERTURE ISOSPEED
INSTRUME DATE-OBS` + `LIVETIME`/`STACKCNT`.

Values are read from tracked records and handed to Siril's own `update_key` —
in-house code reads headers/records and writes none of the pixels, which is the
same posture `stamp_headers.sh` already holds.

### 3.2 Where it fires

`run_undistort_pipeline.sh` already stamps at the end of every build, and the
group driver invokes it once per group — so **stamping there covers every
sub-stack automatically**. `run_undistort_compose.sh` then aggregates onto the
composite: `NMEMBERS`, `NDISTMOD` (count of distinct models), and `MAXMSEP` (the
gate's measured worst zone, §4).

Source of the coefficients is deliberately `lens_preflight.json`, not
`lens_fit.json`: the preflight records what was **live in the DB and verified**,
the fit record what was *intended*. Stamping the intention would re-create the
class of bug this whole arc is about.

### 3.3 Backfill for the existing archive

The aug06 and july31 sub-stacks predate this and carry nothing. Their models are
known exactly from the committed records (report §2), so a one-time
`backfill_substack_provenance.sh` stamps them from those records with
`DISTSRC` suffixed `(backfilled from record)`. Cheap, and it keeps the existing
archive inside the contract instead of stranding it.

### 3.4 Removal condition

Retire the optics block the day an official tool carries the distortion model
through the warp into the product header (darktable gaining FITS I/O, or Siril
`register -disto=` consuming the model natively — BACKLOG item 7). Registered in
`BACKLOG.md` `removal-conditions` alongside the existing `stamp_headers.sh` entry.

---

## 4. Point 4 — the compose gate: model COMPATIBILITY, measured (F3b + F4)

### 4.1 Three tiers, only the third decides

- **T0 — identity (free).** All members' `DISTA/B/C` + `DISTNORM` equal → the
  cheap safe case. Recorded, and it still does not skip T2 for a **cross-night**
  compose, because identical models across nights is exactly the 4.07 px failure.
- **T1 — predicted divergence (arithmetic, screens only).** Evaluate the ptlens
  displacement difference between each member's model and the reference member's
  over ρ ∈ [0, 1.80]. A screen, never a pass: the homography absorbs part of any
  smooth field, so T1 over-predicts (8.19 px predicted vs 2.99 px realised).
  Its job is to fail fast and to name the offending pair before an hour of
  registration.
- **T2 — the member-separation measure. THE ACCEPTANCE GATE.** Register the
  members (the compose does this anyway), `findstar` each registered member
  separately, mutually match against the **reference** member, report median
  separation by zone.

### 4.2 Thresholds, each traced to a measured product

Gate on the **maximum over zones** (the corner in every cell measured so far),
per member against the reference:

| verdict | band | traced to |
|---|---|---|
| **PASS** | **≤ 0.35 px** | july31's cross-set pair — the union the owner's eyes PASSED |
| **WARN** | 0.35 – 1.00 px | 0.93 px = aug06 under one model; round at 1:1 when I looked, but 2.7× the passed level and never user-accepted → build proceeds, number recorded, **surface must be judged at 1:1 before it ships** |
| **BLOCK** | **> 1.00 px** | 2.11 px and 2.99 px are the two products the owner FAILED, both visibly doubled at 1:1 |

Floors for context: 0.14 / 0.19 px is the same-set, same-state floor — the best
this instrument can read, i.e. what "no disagreement" looks like.

**The BLOCK threshold is a choice inside a measured interval, and the owner
should set it.** What is MEASURED is that 0.93 px reads round and 2.11 px reads
doubled; the threshold belongs anywhere in **(0.93, 2.11] px**. 1.00 px is the
conservative end — it blocks everything above the highest level observed clean.
An experiment would narrow it: compose one july31 pair repeatedly under
deliberately perturbed models to place its disagreement at ~1.2 / 1.5 / 1.8 px,
look at each at 1:1, and bisect. One knob, controls preserved, ~1 h. **Offered,
not assumed.**

Validity floor: a zone with fewer than 200 matched stars is reported `n/a`, not
passed. Measured cells carried 1,900–12,658 matches, so this is generous.

### 4.3 Where it lives and what it costs

Inside `run_undistort_compose.sh`, between `seqapplyreg` and `stack` — the
registered members exist there and are currently deleted unread. Cost is one
`findstar` per member plus an O(n) match against the reference (not O(n²)),
minutes for 13 members. On BLOCK: stop **before** stacking, print the table with
each offending member's `DISTSRC`/`DISTA/B/C` from its own header, write the
record, exit non-zero. `--accept-separation=<px>` exists as an explicit override
and **records the number it overrode** into the product's record and header.

Record: `datasets/<session>/<set>/qa_work/compose_gate_<product-tag>.json`,
following the existing `solve_stack_<tag>.json` convention (the set that owns the
product). `readiness_report.py` gains a combine row that quotes it.

### 4.4 Bright-line position (stated so a future session does not refuse to build it)

Every input is a tool's: Siril's registration, Siril's `findstar` PSF fits,
darktable's warp upstream. The in-house part is the cross-match and the median —
a **derived result no tool provides** (Siril reports within-sequence registration
residuals, never member-to-member star-position disagreement in a composed
canvas). It gates a build on a tool-sourced number, which `CLAUDE.md` assigns to
the pipeline: announce it, record the number and the instrument, continue. It
processes no deliverable pixel and replaces no tool's analysis.

**Removal condition:** retire the day an official tool reports headless
member-to-member post-registration positional residuals across a sequence
(a scriptable Siril registration-residual map, or a PixInsight equivalent).
Registered in `BACKLOG.md`.

### 4.5 F4 proper — retiring the blind instruments

`docs/dead-ends.md` already carries both. The wiring change is that the combine's
acceptance row in `readiness_report.py` and in every combine record quotes
**member separation**, and corner `findstar` FWHM / `seqtilt` off-axis are
demoted to context, never verdicts, for this defect class. Their measured
blindness: corner FWHM ranked the failing union (4.95) above the clean control
(5.29); `seqtilt` read 0.34 px off-axis for the FAILING union against 0.40 px
for the PASSING one.

---

## 5. Point 5 — F2, corner-true per-STATE fits (the multi-night requirement)

The per-set doctrine stands. What was never finished is the corner.

### 5.1 Record the census (cheap, do first)

`fit_lens_model.sh` already preserves the `.pto` artifacts; nothing reads them.
Add to `lens_fit.json`: `control_point_coverage` = {n, ρ p50/p90/p99/max,
fraction beyond 1.2 / 1.5 / 1.8, and the ρ at which support becomes sparser than
2% of CPs}. Pure arithmetic on hugin's own CP coordinates.

Backfill from the preserved artifacts — done for the census in §0; wire it so
every future fit carries it.

### 5.2 Classify, do not yet block

`corner_support: none | partial | true`, from the measured ceiling against
ρ = 1.80. **As designed this classifies every existing fit as `none`
(max 1.47–1.51).** That is the finding, not a mis-set threshold — so the fit-side
gate WARNS and records, and the empirical T2 measure stays the acceptance gate.
The classification is what makes a WARN legible: *"this member was warped by a
model with no corner support"*.

### 5.3 Get control points to the corner (the actual work)

A star yields a CP at radius ρ only if it is detected at that radius **in both
frames**. Candidate levers, one knob each, in the order their mechanism is
strongest:

1. **Cross-pointing pairs** (the owner's own lever, and mechanically the right
   one): frames from different sets the same night see the same stars at very
   different field radii, which is precisely how a star lands at corner-vs-midfield.
   Today `fit_lens_model.sh` samples an even stride within ONE set, so nothing
   forces large radial excursions. Discriminator: refit with a mixed-set frame
   list, re-run the census, then run T2 on a cross-set compose under the new
   model.
2. **Pair selection by overlap rather than even stride** — the current stride
   maximises time span, not shared field.
3. **Radius-stratified CP subsampling before the optimize** so ~5% of CPs beyond
   ρ 1.2 are not outvoted 20:1 by the centre.
4. **Detection at large radii** — stars there are dimmer and more aberrated;
   the gauss-3 fattening was tuned on centre-scale stars.

### 5.4 Guard the extrapolation while support is short

A constrained fit (`c = 0`, i.e. the 2-parameter model) cannot run away past the
support ceiling. Trade in §7. Bracketed as its own arm, judged on T2, never on
the fit's own residual — which, note, is computed only where CPs exist and
therefore says nothing about the corner (0.02–0.10 px on fits that produce 2.99 px
of corner disagreement).

### 5.5 F5 folds in here

aug06's 0.93 px residual under one model vs july31's 0.35 px is the same
corner-quality deficit; F2's acceptance run measures it.

---

## 6. Order of work, and why

1. **F2 §5.1 census into `lens_fit.json`** — hours; every later record depends on it.
2. **F4 instrument extracted to `scripts/qa/member_separation.py`** — the
   measurement already exists in this investigation's scratch; it must become a
   tracked, removal-conditioned tool before anything gates on it.
3. **F3a headers + backfill** — the gate needs members that can describe themselves.
4. **F3b compose gate wired on T0/T1/T2** — the smearing build becomes impossible.
5. **F2 §5.3 corner CPs** — the long one; its verification *requires* steps 2–4.
6. **The cross-night acceptance run** (§2.4's hypothesis) — the run that decides
   whether the multi-night road is open.

Steps 1–4 are pure additions: they gate and record, they change no pixel and no
existing product. Step 5 changes models and therefore requires rebuilds.

---

## 7. Trades — stated with numbers, for the owner

### T-1 — What happens to the aug06 union while F2 is unfinished (decision needed)

| option | corner member separation | cost |
|---|---|---|
| (a) ship nothing; wait for F2 | — | the aug06 3-set combine stays unavailable |
| (b) rebuild the union under ONE aug06 model (F1 as same-night fallback) | **0.93 px** — WARN band, needs your eyes at 1:1 | ~40 min/set re-warp × 2 sets; each set's own per-set product loses its own state (set-01 off-axis 0.48 → 0.82 px measured) |
| (c) leave the failed union as evidence, per-set products stand | — | no combine |

**My recommendation: (a) or (c).** (b) buys a combine at 2.7× the measured clean
level, in a band no product has ever shipped from, and it degrades the accepted
per-set products. But it is a real option and the number is known, so it is
yours.

### T-2 — Where the BLOCK threshold sits inside (0.93, 2.11] px

1.00 px recommended (conservative end). Moving it up to ~1.5 px would admit
combines nobody has looked at. §4.2 offers the bisection experiment if you want
the interval narrowed before choosing.

### T-3 — Constrained (c = 0) vs free cubic fits

Unmeasured on this rig. The free cubic buys in-field accuracy and pays with
unbounded corner extrapolation; `c = 0` bounds the corner and may raise in-field
residual. Both are measurable in one bracketed arm (§5.4), judged on T2. **Not a
decision to take now** — flagged so the arm is not skipped.

### T-4 — Per-set fits cost CPs

The aug06 fits needed strict pruning to 114–150 CPs, and set-03's prune left 4.7%
of its CPs past ρ 1.2. Fewer, cleaner CPs make a better in-field fit and a worse
corner. §5.3's cross-pointing lever is the way out; if it fails, the trade
becomes explicit and returns to you.

---

## 8. What this plan does NOT do

- No fix executed, no product replaced, no model reinstalled.
- Does not touch the flatless route — no step here reads or needs a real flat.
- Does not adopt F1: it is recorded as a same-night fallback only, measured not
  to cross nights (4.07 px).
- Does not claim the multi-night route works. §2.4 states it as the hypothesis it
  is, with the run that settles it.
