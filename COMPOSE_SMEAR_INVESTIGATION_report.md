# Compose-smear root-cause investigation — report

> **STATUS — the root cause stands; the fix ranking in §7 and the scope note in
> §9 do NOT.** Members warped under different models is confirmed and was fixed
> by REVERTING to one pinned model per lens@focal, not by the F-ranking here.
> §9's 4.07 px cross-night figure is downgraded to instrument-limited
> (`docs/dead-ends.md`: canvas-radial zoning is invalid across a re-aim).
> Current state: `docs/combine-contract.md`, `docs/consistency-tiers.md`,
> BACKLOG `optical-state-models`.


Scope: the corner star smear in the aug06 cross-set combines, run as an
independent audit per `COMPOSE_SMEAR_INVESTIGATION_PROMPT.md`. Everything the
two prior sessions produced was treated as claims to re-derive, not findings to
inherit. Where my measurements contradict the trail, the records have been
corrected (`COMBINE_CORNERS_AUDIT_report.md` §1, `TOOLS.md` hugin row,
`docs/dead-ends.md`).

Labels: **MEASURED** (instrument + numbers), **ARITHMETIC** (exact consequence
of measured inputs), **HYPOTHESIS** (consistent, no discriminating test run).

Measurement records: `datasets/aug06/experiments.jsonl`
(`undistort_normalization_and_corner_divergence`,
`pairwise_member_compose_discriminator`); evidence surfaces and star lists under
`sessions/aug06/work/{smear_probe,smear_arm}/`.

---

## 0. The answer in one paragraph

**MEASURED: the smear is caused by composing sub-stacks that were warped under
DIFFERENT lens-distortion models.** The per-set optical-state adoption made the
distortion model a property of the SET; the cross-set combine makes it a
property of the COMBINE, and nothing reconciled the two. Members rectified by
different models disagree about where a star is, by an amount that grows with
field radius, and a global homography cannot absorb a radial field — so the mean
of them doubles the stars. The disagreement is structural rather than a bad fit:
**lensfun normalises the ptlens radius by half the SHORT side (MEASURED)**, which
puts the frame corner at ρ = 1.80 while hugin's control points constrain the fit
only to ρ ≈ 1.5 (MEASURED census, §3e: median CP support ρ 0.62–0.86, p99
1.43–1.48, max 1.47–1.51 across every preserved fit). The cubic extrapolates
beyond its support exactly at the corners, so fits that are interchangeable inside the field diverge by 6–8 px
outside it. A second, smaller term rides on top: aug06's members are less well
rectified than july31's under **both** model eras. july31 composes clean at
larger offsets and rotations because all four of its sets share ONE model (its
recorded july14 inheritance) — the dominant term is exactly zero there.

---

## 1. The owner's four questions

### Q1 — What is broken in the undistort pipeline? Is something referenced from one session to another?

**Nothing is broken inside a set's undistort, and no build referenced another
session.** The per-set stage is correct and well guarded: the model is installed
from the set's own record before the masters are built
(`run_set_chain.sh:543`), and `lens_preflight.py` **hard-stops** on
`MISMATCH` if the model live in the lensfun DB is not the one the set's
`lens_fit.json` names — so a set physically cannot warp on another set's optics
without the chain aborting. I verified the guard's logic and, independently, the
recorded evidence of every build (§2).

**What is broken is one level up: the COMBINE has no optical-model contract.**
`run_undistort_compose.sh` accepts any sub-stack directories and mean-combines
them. It never asks whether the members were rectified by the same model, and
its own docstring asserts the opposite of what happened — *"after the
lens-distortion warp every frame-to-frame map is a pure homography, and
homographies COMPOSE"*. That is true only when the undistortion is the SAME map
for every member. The moment models became per-set, that premise silently
stopped holding, and no guard, record, or doc noticed.

MEASURED consequence — the px separation of the same star as two registered
members place it, at the composed canvas corner (one knob; identical group
membership, verified by diffing all 13 `g*.list` files; same two pointings; only
the installed model differs):

| composed pair | centre | mid | outer | **corner** |
|---|---|---|---|---|
| aug06 cross-set, sets' OWN models | 0.29 | 0.63 | 2.10 | **2.99 px** |
| aug06 cross-set, ONE (pinned) model | 0.15 | 0.17 | 0.44 | **0.93 px** |
| july31 cross-set, ONE model | 0.25 | 0.11 | 0.18 | **0.35 px** |
| aug06 same-set (control) | 0.14 | 0.06 | 0.09 | **0.14 px** |
| july31 same-set (control) | 0.13 | 0.04 | 0.08 | **0.19 px** |

The same-set controls at 0.1–0.2 px **exonerate the compose code and Siril's
registration** — they are doing their job. Removing model heterogeneity alone
cuts the corner disagreement 3.2×.

### Q2 — Does every calibration input come from that session's/set's own images? What is the lifecycle of the lens-DB tweak? Does one night's fit calibrate it forever?

**Provenance: clean. Lifecycle: unbounded — and that is a real, separate risk
that did not fire here.**

Full input provenance is in §3. Every aug06 build consumed only aug06 data. The
single cross-session reference anywhere in the chain is **deliberate and
recorded**: july31's four sets inherit the july14-fitted model, because july31's
own refit was diagnosed untrustworthy (radially banded CP coverage,
`july31/set-01/qa_work/lens_fit_DIAGNOSTIC.json`), and each set carries an
`inherited_from` provenance string.

On the lifecycle, the owner's instinct is right:

- `install_lens_model.sh` writes into `~/.local/share/lensfun/updates/version_1/mil-nikon.xml`
  — **global machine state, one `<distortion focal="70">` line, no per-session
  scoping, and nothing ever reverts it.** As I write this the DB holds
  **aug06/set-03's** model; it will hold it until some other chain run
  overwrites it or `lensfun-update-data` wipes the patch.
- Inside `run_set_chain.sh` the risk is closed: install-then-preflight, and the
  preflight stops on mismatch.
- **Outside** that path it is open. `run_undistort_pipeline.sh` invoked directly
  runs the preflight but does **not** install; any other darktable render on
  this rig (`verify_lens_card.py`, a manual `darktable-cli`) silently uses
  whatever was last left. Two concurrent builds of different sets would clobber
  each other's model — the builder's lock is on its work dir, not on the DB.
- The DB file's own mtime is the only trace of when it changed, and the XML
  marker records only the LAST install and the coefficients it replaced.

So: one night's fit does calibrate the DB indefinitely. It did not corrupt any
aug06 build (§2 proves that from the records), but the fix proposals in §7
include closing it, because it is one interrupted chain run away from doing so.

### Q3 — When exactly did this start?

**The boundary is the model-granularity change, and it is visible on the same
data with the same chain.**

| product | built | models across members | outcome |
|---|---|---|---|
| july31 4-set union `stack_set-01+02+03+04_full.fit` | 2026-08-07 00:05 | **ONE** (july14 inheritance, all 4 sets) | **PASSES** (user's eyes) |
| aug06 pinned-arm members `groups_set-0{1,2,3}_pinned` | 2026-08-07 22:20 → 08-08 05:20 | **ONE** (pinned) | corners **clean by eye** when composed |
| aug06 own-model members `groups_set-0{1,2,3}` | 2026-08-08 05:45 → 07:37 | **THREE** (per-set fits) | — |
| aug06 union `stack_set-01+02+03_full.fit` | **2026-08-08 07:44** | **THREE** | **FAILS — the first smeared product** |

Commits: the per-set fitted models first entered a *build* at **`1b66101`**
(08-08 05:33, `wiring(optics): the --from-fit A/B state passes the preflight as
CANDIDATE`) — the own-model rebuilds ran under it, 05:45–07:37 — and the method
was ratified at **`9388b8f`** (08-08 09:55, `method(optics): per-set
optical-state records ARE the model authority — pinned incumbent removed
clean`). The chain code, compose code, framing route and calibration method were
otherwise the same across the july31 and aug06 builds (july31 built Aug 6–7,
aug06 Aug 7–8, both via `run_undistort_groups.sh` + `run_undistort_compose.sh`).

**The discriminating measurement, not just the chronology:** the aug06
pinned-arm members — built BEFORE the adoption, from byte-identical frame
groups — compose into a union whose corners are visually clean, where the
own-model members from the same frames compose into dashes. Same data, same
code, one knob.

### Q4 — Was the mitigated issue resolved, and did the change cause this one?

**Yes to both, and they are the same coin.**

- **Resolved.** The mitigation targeted a measured, real problem: the july-fitted
  model against aug06's optical state showed ~2× elevated field terms, and
  set-01's own-model rebuild removed it (off-axis 0.82 → 0.48 px — the decisive
  WIN in `dd38019`). The per-set products were accepted on the user's eyes. The
  cross-session-leak concern is also genuinely closed for production, by the
  preflight's MISMATCH stop (§Q1) — with the caveat about non-chain callers.
- **And it caused this one.** The mitigation moved the model's granularity to
  the SET. The combine's unit is the SESSION-GROUP of sets. Making a model
  per-set is *correct for a per-set product* and *incorrect for anything that
  composes sets*, and nothing in the design, the guards, or the A/B noticed the
  difference — the whole own-vs-pinned A/B (`dd38019`) was run on **per-set
  products only**. The combine consequence was never measured before it shipped.

---

## 2. Calibration-provenance table (what each build ACTUALLY consumed)

Traced from the tracked records at the commits contemporaneous with each build,
the machine-local DB, and file timestamps — not from the design.

| build | dark | flat | lens model | proof |
|---|---|---|---|---|
| aug06 set-01 members (own arm, 08-08 05:45–06:22) | `aug06/work/masters/dark_master.fit` — 328 **aug06** darks | `skyflat_set-01.fit` — set-01's own 502 frames | a=0.00808615 b=0.00191793 c=0.01238601 = **set-01's own fit** | `lens_preflight.json` @`295aa26` records the coefficients read live from the DB at that build; `skyflat_set-01_qa.json` records dark+frame source; `master_dark.log` records 328 frames |
| aug06 set-02 members (08-08 06:22–07:00) | same session dark | `skyflat_set-02.fit` — set-02's own 500 frames | a=0.00191581 b=0.01993761 c=−0.00071097 = **set-02's own fit** | same records @`295aa26` |
| aug06 set-03 members (08-08 07:01–07:37) | same session dark | `skyflat_set-03.fit` — set-03's own 500 frames | a=0.00428142 b=0.01194427 c=0.00157443 = **set-03's own fit** | same records @`295aa26` |
| aug06 set-01/02/03 members (PINNED control arm, 08-07 22:20 → 08-08 05:20) | same session dark | same per-set flats | a=0.00350093 b=0.01453356 c=0.00043983 for **all three** | `lens_preflight.json` @`4771780` (set-01) and @`b5f9a36` (set-02/03) |
| **aug06 union `stack_set-01+02+03_full.fit`** (08-08 07:44) | — | — | **THREE different models across its 13 members** | membership = the three own-arm `groups_set-0*` dirs; each member's model per the rows above |
| july31 set-01…04 members (08-06 21:40 → 08-07 00:05) | july31's own master dark | per-set sky flats from each set's own frames | a=0.00350093 b=0.01453356 c=0.00043983 for **all four** | `july31/set-0*/qa_work/lens_preflight.json`, state `ok` |
| **july31 union** (08-07 00:05) | — | — | **ONE model across all 17 members** | as above |

**Cross-session references found:**

1. **DELIBERATE, recorded** — july31's four sets inherit the july14-fitted
   optical state. Every `july31/set-0*/qa_work/lens_fit.json` carries
   `inherited_from` + `why_inherited` (own refit untrustworthy: banded CP
   coverage) + `accepted_by` (the products' own 0.16–0.47 px off-axis floor).
   This is the correct handling of an untrustworthy fit, and — measured here —
   it is also why july31's combine passes.
2. **ACCIDENTAL: none found in any build.** Every aug06 dark, flat and model
   traces to aug06 data.
3. **LATENT (structural, did not fire)** — the lensfun user DB is unscoped
   global state with no revert; it currently holds aug06/set-03's model and will
   serve it to any non-chain darktable invocation on this rig, for any session.
   See §7 F3.

---

## 3. The mechanism, measured

### 3a. The radius normalisation — pinned by probe, and it is the reason the corner is special

The optics ledger recorded its px verdicts under a min-half-dim convention while
explicitly flagging it as unpinned (*"radius-normalization convention must be
pinned from lensfun source before final px verdicts"*), and `TOOLS.md` asserted
that lensfun internally rescales hugin-convention coefficients. Neither had been
probed. Both are now settled by measurement, end-to-end through the production
warp (seeded synthetic star-field fixture at the sensor's own geometry
6064×4040; `darktable-cli --style lensdist` vs `--style nodist`, identical but
for the module's enabled bit; Siril `findstar`; 150 dots at 400 px pitch so no
match can be ambiguous; identity control closes at median |tangential| 0.50 px,
max |radial| 0.71 px):

| assumed normalisation radius | RMS residual of the fit over all four models |
|---|---|
| **half SHORT side, 2020 px** | **4.47 px** |
| half long side, 3032 px | 18.27 px |
| half diagonal, 3643 px | 22.22 px |
| free | lands at **2000 px** (1% from 2020) |

**MEASURED: lensfun uses hugin's own convention — half the short side. No
rescaling happens or is needed.**

**ARITHMETIC consequence, and it is the whole story of why this defect is
corner-only:** the frame corner is at ρ = 3643/2020 = **1.80**, while `cpfind`'s
control points reach only ρ ≈ 1.5 and are sparse past 1.2 (§3e). The ptlens cubic
**extrapolates past its support precisely where the defect appears.** Two
fits that agree inside the supported field are free to disagree outside it — and
a fit's own reported residual (0.02–0.10 px on these fits) is computed only
where control points exist and says nothing at all about the corners.

MEASURED model-pair divergence through the production warp (peak radial px):

| pair | peak divergence |
|---|---|
| set-02 vs set-03 | **8.19 px** |
| set-02 vs pinned | 6.27 px |
| set-01 vs set-03 | 6.24 px |
| set-01 vs pinned | 4.91 px |
| set-01 vs set-02 | 2.80 px |
| set-03 vs pinned | 1.91 px |

For scale, the correction itself peaks at ~94 px, so the per-set fits disagree
by up to ~9% of the whole warp.

### 3b. On real members: the disagreement, and what survives registration

The table in §Q1 is the direct measurement. A global homography absorbs the
similarity part of a radial bowl, which is why 6–8 px of model divergence lands
as ~3 px of irreducible corner disagreement rather than the full amount.

**ARITHMETIC check against the observable:** two copies of a 2.92 px-FWHM member
star separated by 2.99 px average to a blend of ≈4.6 px FWHM — i.e. a visible
double, which is exactly what the eye reports.

### 3c. The secondary term — aug06's members are less well rectified than july31's

Even with heterogeneity removed, the aug06 cross-set pair sits at 0.93 px
against july31's 0.35 px. That ratio is independently confirmed by
astrometry.net's own SIP fit (tweak-order 3), which measures the residual
distortion each member still carries after the warp:

| member | SIP outer-field mean | SIP max |
|---|---|---|
| aug06 s01 g1 / s02 g1 / s03 g1 / s01 g2 | 29.9 / 28.9 / 26.1 / 26.1 px | 44.5 / 49.0 / 58.0 / 40.9 px |
| july31 s01 g1 / s02 g1 / s01 g2 | **12.8 / 20.9 / 14.7 px** | 31.1 / 39.7 / 37.5 px |

**MEASURED: this is NOT the optics or the seeing.** The raw singles run the
other way — aug06/set-01's single frames are the more field-uniform
(corner/centre 1.174 vs july31/set-01's 1.220,
`qa_work/singles_field_check.json`). The corner degradation in aug06's members
is introduced by the undistort+register+stack chain and only there. Under both
model eras aug06's members retain a corner/centre FWHM ratio of 1.15–1.18×
where july31's members fall to 1.05–1.08×.

**HYPOTHESIS for the residual (test stated, not run):** the aug06 fits came from
a mid-campaign-modified instrument on 2.5 s subs (`fit_instrument_cp_starvation`)
and every one needed strict CP pruning down to 114–150 points; corner support was
never measured. The test that would settle it is to record the CP radial
coverage per fit and refit with corner-weighted control points, then re-measure
the member SIP residual.

### 3d. Why july31 composes clean at bigger offsets and rotations

Because the dominant term is identically zero for july31 — one model across all
17 members — and the secondary term is ~2.7× smaller. Offset and rotation are
not the driver: the aug06 pair with the LARGEST rotation (9.28°) and the
SMALLEST offset (98 px) is among the worst, and july31 at 4.73° / 411 px shows
no penalty at all. Geometry only sets how much of each member's radial residual
field fails to overlap; with no residual difference to expose, more geometry
costs nothing.

| composed pair | offset | rotation | corner disagreement |
|---|---|---|---|
| aug06 same-set | 225 px | 0.27° | 0.14 px |
| aug06 cross s01+s02 (own models) | 500 px | 2.08° | 2.99 px |
| aug06 cross s01+s03 (own models) | 98 px | 9.28° | 2.11 px |
| july31 cross s01+s02 (one model) | 411 px | 4.73° | 0.35 px |

---

### 3e. Corner support of every fit — census, MEASURED

Computed from hugin's own control-point coordinates in the `.pto` artifacts
`fit_lens_model.sh` preserves, as normalised radius ρ = r / 2020 (the measured
half-short-side normalisation). The frame corner is ρ = **1.80**.

| fit | CPs | ρ p50 | p90 | p99 | max | beyond 1.2 | beyond 1.5 |
|---|---|---|---|---|---|---|---|
| aug06 set-00 (`clean`) | 317 | 0.86 | 1.38 | 1.47 | 1.51 | 28.1% | 0.2% |
| aug06 set-02 (`strict2`) | 125 | 0.82 | 1.28 | 1.48 | 1.50 | 22.4% | 0.4% |
| aug06 set-03 (`strict2`) | 150 | 0.62 | 1.12 | 1.43 | 1.47 | 4.7% | 0.0% |
| july31 set-01 — the REJECTED fit (`strict2`) | 104 | 0.81 | 0.89 | 1.22 | 1.24 | 1.9% | 0.0% |

**MEASURED: no fit in this repo constrains the corner.** Support is real but
sparse out to ρ ≈ 1.5 and absent beyond it; the corner at 1.80 is extrapolation
in every model that has ever shipped here. The strict CP pruning the aug06 fits
required cut support hardest exactly there (set-03 keeps 4.7% of its CPs past
ρ 1.2). The fit rejected on banded coverage tops out at 1.24, so the census and
that diagnosis agree. aug06/set-01's `lens_fit_work` was not preserved — the one
fit whose coverage is unmeasured. Ledger: `fit_corner_support_census`.

---

## 4. Root-cause statement

**MEASURED — dominant.** The aug06 cross-set unions were built from sub-stacks
warped under three different ptlens models. Those models diverge by up to 8.2 px
in the outer field, and ~3 px of that survives the compose's homography
registration at the canvas corners, doubling the stars. Removing only that
variable — same frames, same pointings, same code — drops corner disagreement
from 2.99 px to 0.93 px and restores round stars to the eye.

**MEASURED — structural enabler.** lensfun normalises ptlens by half the short
side, so the corner sits at ρ = 1.80 against fits whose control points stop at
ρ 1.47–1.51 (§3e).
Any two independently fitted models are unconstrained there. This is why the
defect is corner-only and why it does not show up in the fits' own residuals or
in any per-set product.

**MEASURED — secondary.** aug06's members carry ~2× july31's residual
distortion after the warp (SIP 26–30 px vs 13–21 px) under BOTH model eras, so
even a single-model aug06 combine starts from 0.93 px of corner disagreement
where july31 starts from 0.35 px. Not optics: the raw singles are comparable and
aug06's are marginally better.

**Explains the full evidence set**, including the items that defeated the
earlier passes: the min-framed union smears (framing is irrelevant to a
model-difference field); the per-set products pass (one model per product by
construction); the members enter at ~3.5 px and the union exits at 4.9–5.3 px
(the disagreement is created at the join, not carried in); july31 passes at
larger geometry (dominant term zero); `--subsky-lights` changed nothing (an
additive background step cannot move a star).

**Why two sessions missed it — MEASURED, and it belongs in the record.** The
instruments were blind, in two successive ways. Round one used background box
medians, which cannot see star shape at all. Round two used corner `findstar`
FWHM, which is a PSF fitter: on a doubled star it fits one component rather than
the blend, so it ranked the failing own-model union (4.95 px) as *better* than
the visually clean single-model control (5.29 px) — and that single inverted
number is what "eliminated" model heterogeneity. Re-measured at matched canvas
boxes the two read 3.92 vs 3.31 px at c11 — the right ordering, but a gap far
smaller than the eye's. Siril `seqtilt` is weaker still: off-axis aberration
0.34 px for the FAILING union against 0.40 px for the PASSING one. The
instrument that works is the mechanism itself: register the members, `findstar`
each separately, mutually match, and read the separation in px. Registered in
`docs/dead-ends.md`.

---

## 5. Evidence you can look at

Corner crops at 1:1, same corner, same framing, same members, `autostretch`,
under `sessions/aug06/work/smear_arm/`:

- `u_union_own_c00.png`, `u_union_own_c11.png` — the FAILED union: stars drawn
  into multi-component dashes over brushed fabric.
- `u_union_pinned_c00.png`, `u_union_pinned_c11.png` — the same corners of the
  single-model control: round single stars.
- `insp_aug06_cross_copointed_c00.png` — the two-member cross-set pair: every
  star cleanly doubled.
- `insp_aug06_sameset_c00.png`, `insp_july31_cross_c00.png` — the controls:
  single round stars.

Also preserved: the grid-fixture warps and star lists (`smear_probe/`), the six
composed cells `A1`–`A6` with their registered member pairs (`reg_A*/seq/`), the
per-member plate solves (`wcs_*.fit`, `solve_*.json`), and the `star_shape`
records.

---

## 6. Corrections applied to the records

- `COMBINE_CORNERS_AUDIT_report.md` §1 — the "per-set model heterogeneity
  eliminated" row is marked REFUTED with the superseding measurement; the
  leading hypothesis is closed as half-right (its secondary term stands).
- `docs/dead-ends.md` — two new entries: never compose sub-stacks warped under
  different models (with the normalisation mechanism and the numbers); and a PSF
  fitter is the wrong instrument for star doubling.
- `TOOLS.md` hugin row — the unprobed "lensfun rescales hugin-convention
  coefficients internally" is replaced by the measured convention and its
  ρ = 1.80 corner consequence.
- `datasets/aug06/experiments.jsonl` — two experiments pre-registered before
  their runs and closed with numbers.

---

## 7. Ranked fix proposals — for the owner to decide

Nothing below is executed. No product is replaced. All are software-side, inside
the flatless route.

### F1 — One optical model per COMBINE FAMILY, not per set (the root fix)

Make the model's granularity match the unit that gets composed. Concretely: a
combine family declares one model; every member that will be composed is warped
under it; per-set fits become *candidates* that a family adopts, not authorities
that ship independently.

- Rebuild cost: re-warp the sets that don't already carry the family model
  (~40 min/set measured, and the owner has said re-running is cheap).
- Keeps the mitigation's real win — the family model is still fitted from THIS
  campaign's frames, never inherited across a focus change, so the
  cross-session-leak problem the per-set change solved stays solved.
- Open sub-decision the data can settle: which model the aug06 family adopts.
  Candidates are set-01's, set-02's, set-03's, or a joint fit over frames from
  all three sets. **Recommendation: a joint fit**, because it is the only one
  whose control points span all three pointings, and per §3a the corner is
  decided entirely by where the control points are. Discriminator: build the
  three-set union under each candidate and measure corner disagreement with the
  §Q1 instrument.
- Risk to state honestly: if the sets' optical states genuinely differ (the
  user's recalled mid-night refocus), one family model is worse for each
  individual set than its own. That trade is measurable — per-set product
  off-axis vs union corner disagreement — and it is the owner's call.

### F2 — Constrain the fit where the product is judged (fixes the enabler)

The fits are unconstrained beyond ρ ≈ 1.5 and the defect lives at ρ = 1.80.

- Record CP radial coverage in `lens_fit.json` and refuse a fit whose support
  does not reach the corners (the "corner-support trustworthiness predictor"
  the optics ledger recorded but never applied as a gate).
- Weight or seed `cpfind` toward corner overlap; failing that, drop to a
  2-parameter model (c = 0) so the extrapolation cannot run away.
- Cheap, additive, and it makes every future fit safer whether or not F1 is
  adopted.

### F3 — Guards for what has no guard

- **Compose-time model assertion** (the missing one): `run_undistort_compose.sh`
  should read each member's set record and STOP when the members' models differ,
  naming them. This defect would have been impossible to build.
- **Stamp the model into the member's FITS header** at warp time, so a
  sub-stack carries its own optics provenance and the assertion needs no
  lookup — this also fixes the fact that a sub-stack on disk currently has no
  way to say what warped it.
- **Bound the lensfun-DB lifecycle**: have `run_undistort_pipeline.sh` install
  (not merely verify) the set's model, and/or restore the DB after a run, so a
  non-chain caller cannot inherit the last set's optics.
- Correct `run_undistort_compose.sh`'s docstring, which currently asserts the
  premise this defect broke.

### F4 — Retire the blind instruments for this defect class

Adopt the register-and-mutually-match measurement as the acceptance measure for
any multi-member compose, and stop quoting corner FWHM or `seqtilt` off-axis for
it. Both are recorded in `docs/dead-ends.md` as measured-blind. This costs
nothing and is what would have caught the defect on the first pass.

### F5 — Chase the secondary term (lowest priority; do after F1)

aug06's 0.93 px residual under one model vs july31's 0.35 px is worth closing,
but F1 removes the visible defect and this does not. The test is in §3c.

---

## 8. Status

- Root cause MEASURED and reproduced on demand with a one-knob control.
- No fix executed; the failed products stand untouched as evidence; nothing
  ships.
- The owner decides F1's model choice; F2–F4 are cheap and independent of it.

---

## 9. Review addendum — F1's scope, measured (the owner's multi-night question)

The owner asked whether F1 (one model per combine family) extends to
multi-night combining — the project's core use. MEASURED (X1 cell, this
report's own instrument, whole-frame match n=12,658): a july31 member and an
aug06 member warped under the IDENTICAL pinned model — so the shared model
cancels and only the true between-night state difference remains — disagree
by **0.33 / 0.99 / 1.87 / 4.07 px** (centre/mid/outer/corner). 4.07 px
exceeds the 2.99 px own-models failure: **a shared family model does not
extend across nights.** F1 is same-night-scoped (0.35–0.93 px measured
within-night).

Revised ranking, for the owner's decision: **F2 is the multi-night
requirement** (corner-true per-set fits — corner-support gate + control
points reaching toward ρ=1.8, e.g. cross-pointing frame pairs that place the
same star at corner-vs-midfield radii); the per-set model doctrine STANDS;
F1 demotes to a same-night fallback where a trustworthy fit is missing; F3's
compose assertion generalizes to model-COMPATIBILITY (identical or
measured-agreeing members); F4's member-separation measure is the combine
acceptance instrument; F5 folds into F2.
