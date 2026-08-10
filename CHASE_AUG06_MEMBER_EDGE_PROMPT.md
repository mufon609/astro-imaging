# Fresh-session prompt — chase the aug06 member EDGE defect

Read `CLAUDE.md` first; it is the briefing and the read order (`docs/dead-ends.md`,
`TOOLS.md`, `MEMORY.md`, `README.md`, `BACKLOG.md`). Then two documents written
during the arc that produced this task:
`docs/combine-contract.md` (what a night must keep to be stackable with a night
years later) and `docs/consistency-tiers.md` (which calibration input is valid at
which scope, and why getting that wrong in either direction breaks something).

`MEMORY.md` is binding. Three lines of it especially: **synthetic flats are the
project's point** — every fix is a software fix inside the flatless route and
"shoot real flats" is never a recommendation; **night-to-night stacking is the
core purpose** — no change may improve a per-set product at the combine's
expense; and the owner judges by eye on full-frame lossless surfaces, which has
now caught two defects that instruments missed.

---

## 1. Where the project is

The wide-field-untracked route (calibrate → undistort → register → stack →
compose) works, and multi-night combining works. The owner has accepted:

- the aug06 3-set union under one model (`set-01+02+03_full_pinnedmodel`);
- **the six-set CROSS-NIGHT union** (`j31-3+a06-3_full_onemodel`, 28 members,
  2954 frames, july31 ×3 + aug06 ×3) — *"the most detailed image yet… it is a
  win"*. That is the first successful cross-night combine in this repo's history.

## 2. What was just fixed, so you do not re-open it

A per-set optical-state doctrine ("focus recalibrates every session; the lens
model keys on the OPTICAL STATE, per set") was adopted and has been **refuted at
its root and reverted**. Full entry in `docs/dead-ends.md`; the closed item is
BACKLOG `optical-state-models`.

The short version, because it is the cautionary tale this repo now runs on:

- Its founding evidence — aug06/set-01 measuring 0.82 px off-axis under the
  pinned model against a 0.16–0.62 family — is a **compose artifact**. Every one
  of set-01's five 100-frame groups reads **0.40/0.42/0.44/0.43/0.45 px** under
  that same model. The 0.82 exists only in the 500-frame product.
- Its discriminator never discriminated: four independent fits of ONE set span
  **0.36–6.30 px** against a between-set spread of 4.01–10.99 px. They overlap.
- Adopted on **1 WIN / 3 NULL**, it gave new models to three sets that measured
  no benefit, and that heterogeneity broke the combine: **2.99 px** corner
  disagreement within a night, **5.34 px** across nights, visible star doubling
  the owner failed by eye.

The model is now PINNED per `<lens>@<focal>` in `scripts/darktable/lens_models.json`.
A per-set fit is a CANDIDATE promoted by an explicit act and judged at the
COMBINE — never on a per-set product, where a compose artifact masquerades as
optics. **Do not re-derive per-set models.** If you think you need one, the
answer is a state-CHANGE detector (BACKLOG), not a per-set default.

## 3. THE DEFECT TO CHASE

The owner, on the accepted cross-night union: *"the left side of the image is
smeared while the right side is sharp — the right side is sharp even when it is
noisy, unlike the left side."* That distinction is exact: **noise is a depth
property, smear is a geometry property**, and they have different causes.

### 3.1 What it is — MEASURED

The union canvas spans 41.0° (8659 px × 17.06″/px). aug06's members centre at
RA 303.5–306.7 and july31's at 308.7–312.0, each with a 28.6° FOV, so the
union's **left edge is reachable only by aug06's field edge and its right edge
only by july31's**. Left/right is aug06/july31.

Star shape at the **member** level — one member each, **same pinned model, no
compose involved** (Siril `findstar`, open gate, 800 px boxes marched across the
frame at x = 8/30/50/70/92%):

| member | centre FWHM / round | edge FWHM / round (x=8%, x=92%) |
|---|---|---|
| aug06 set-01 | 2.52 / 0.909 | **3.11 / 0.903** , **2.96 / 0.849** |
| aug06 set-02 | 2.51 / 0.915 | **3.10 / 0.877** , **3.13 / 0.799** |
| july31 set-01 | 2.54 / 0.911 | 2.58 / 0.969 , 2.56 / 0.948 |
| july31 set-02 | 2.44 / 0.917 | 2.60 / 0.967 , 2.66 / 0.893 |

**Identical at centre; aug06 markedly worse at the edges** — +0.5 px FWHM and
roundness down to 0.799 (a nearly 1.25:1 elongation) against july31's 0.893–0.969.

Corroborating, independently: astrometry.net's own SIP fit (order 3) measures the
residual distortion each member still carries after the warp — **aug06 26.1–29.9
px outer-field, july31 12.8–20.9 px**.

### 3.2 What it is NOT — each ruled out by measurement

- **Not the model.** Both arms above are under the same pinned july14 model.
- **Not the compose.** Measured on single members.
- **Not the optics, and this is the key clue.** aug06's RAW SINGLES are the
  *more* field-uniform of the two sessions (corner/centre **1.174** vs july31's
  **1.220** — `qa_work/singles_field_check.json`). So the degradation is
  **introduced between single frame and member**, i.e. inside the within-group
  registration/stack, and only for aug06.
- **Not framing, background level, member content, or re-aim geometry** — all
  eliminated during the earlier arc (`COMPOSE_SMEAR_INVESTIGATION_report.md` §1).

### 3.3 The sibling observation — probably the same mechanism

Composing set-01's five PINNED members into its per-set product adds **+0.39 px**
off-axis, where every other measured cell adds **+0.06–0.12** (set-01 own +0.06,
set-02 pinned +0.11, set-02 own +0.12). Same code, same frames, same group
derivation. Ledger: `within_set_compose_amplification_residue`. Treat this and
§3.1 as **one open question** until a measurement separates them.

## 4. Where to start — the test that splits the field

**Step 1, before anything else: measure SINGLE FRAMES with the SAME instrument
as §3.1.** The existing `singles_field_check.json` used a different gate and
corner boxes; §3.1 marched horizontally with an open gate. Until one instrument
measures both levels, "the degradation enters between frame and member" is an
inference across two instruments, not a measurement.

Calibrate + warp (no registration, no stack) a few aug06 and july31 singles under
the pinned model, march the same 800 px boxes at x = 8/30/50/70/92%, and read
FWHM + roundness. Two outcomes, both decisive:

- **Singles equal at the edges, members differ** → the defect is in within-group
  registration/stacking. Go to §5.
- **Singles already differ at the edges** → it is upstream of registration
  (warp residual for aug06's state at large radius, or acquisition), and the
  §5 candidates are the wrong tree.

## 5. Candidate mechanisms if it IS the within-group stage

One knob each, pre-registered, control preserved. Listed with what makes each
testable — not ranked, because nothing yet separates them:

1. **Drift span per group.** A group spans the sky drift of ~100–125 frames;
   more drift means more residual-distortion mismatch for a single homography to
   absorb, and it lands hardest at large field radius. aug06's groups are 100
   (set-01), 125/124 (set-02), 114 (set-03); july31's are 100. Measure the actual
   angular span per group from the solved members and correlate with edge
   roundness. Note set-01 is also 100 and still bad — so size alone will not
   explain it.
2. **Registration residual per frame.** Siril `register` reports its own
   residuals. Compare the distribution for an aug06 group against a july31 group,
   and check whether aug06's grows with field radius.
3. **Transform class.** `register -2pass` defaults to homography. A radial
   residual is exactly what a homography cannot absorb; whether affine/similarity
   changes the edge behaviour is a one-knob arm.
4. **The warp's own residual for aug06's state at large radius.** The pinned
   model is july14's state. §3.2 says the raws are fine and the model is shared,
   but "shared" does not mean "correct at the edges for both nights". The A/B
   already exists in preserved form: aug06 members under the pinned model
   (`groups_set-0*_pinned`) vs under their own fits (`groups_set-0*`). Measure
   edge roundness on both with §3.1's instrument. *(Beware: this is how the
   per-set doctrine was born. A per-set model is not the fix even if it measures
   better here — the fix would be a better SHARED model or a state-change
   detector. Read §2.)*
5. **Acquisition-side differences.** Both sessions are 2.5 s, ISO 1600, fixed
   mount, 28.6° FOV. july31 was moonlit (the banded-CP diagnosis on its refit);
   aug06 was not. Dew, wind, or focus drift within an aug06 set would show as a
   TIME-dependent edge degradation — measurable per group, since the groups are
   consecutive time blocks.

## 6. Instruments — what to use and what is measured BLIND

The registry (`docs/dead-ends.md`) carries these; they cost this investigation
two whole sessions, so read them before choosing a measure.

**Measured blind to this defect class — do not draw verdicts from them:**
- background box medians (cannot see star shape at all);
- corner `findstar` FWHM as a *doubling* measure — a PSF fitter fits one
  component, and it once ranked a FAILING union above the visually clean control;
- Siril `seqtilt` off-axis — read 0.34 px for the FAILING union against 0.40 for
  the PASSING one.

**Use:** `findstar` FWHM **and roundness** in fixed boxes (roundness is what
carries the elongation the owner sees), and `scripts/qa/member_separation.py` —
the acceptance measure for any multi-member compose.

**`member_separation.py`'s three registered limitations** — all in the registry:
1. zones are CANVAS-radial, so **no absolute cross-night number from it is
   trustworthy** (across a re-aim the canvas centre sits between two optical
   axes; a corner median swings 0.71→3.38 on a 0.10 zone-bound change). One-knob
   comparisons on a fixed pair stay sound — the geometry is common and cancels.
2. it returns **UNMEASURED** on a wide multi-night max-framed union (378/378
   pairs had no zone with ≥100 matched stars).
3. the fix for both is the same: bin by each member's OWN field radius via its
   own WCS instead of by canvas radius. **This is worth doing first if you need
   absolute numbers** — it is contained to one script.

**Every surface you judge, look at yourself at 1:1** (Siril crop + `savepng`,
then view it). Both defects in this arc were found by eye after instruments
passed them.

## 7. What exists that you should not rebuild

- **Preserved members**, provenance-stamped, 56/56 contract-complete:
  `sessions/aug06/work/groups_set-0{1,2,3}` (own models),
  `..._pinned` (the shared model), `..._subsky1`,
  `sessions/july31/work/groups_set-0{1,2,3,4}`. Every sub-stack's header answers
  what warped and calibrated it (`DISTA/B/C`, `DISTNORM`, `DISTSRC`, `DISTPROV`,
  `CALSET`, `CALDARK`, `CALFLAT`, `BKGLIGHT`, `STACKCNT`, `GRPSIZE`).
- **The chain is reproducible**: 30/30 group memberships regenerate identically
  from tracked records, and a rebuilt sub-stack is pixel-identical. Rebuild
  freely; nothing is precious except the raws and the records.
- Products and evidence in `web/results/{aug06,july31}/` — including the FAILED
  originals, kept deliberately as controls. **Do not overwrite or delete them.**
- `datasets/aug06/experiments.jsonl` — the ledger, including every entry cited
  here.

## 8. Disciplines (binding, from `CLAUDE.md` + `MEMORY.md`)

- One knob per experiment, control bracketed, **hypothesis pre-registered before
  the run**; verdicts with numbers into the ledger; killed hypotheses into
  `docs/dead-ends.md` with their numbers.
- Every claim carries its status: **MEASURED** (with the instrument) or
  **HYPOTHESIS** (with the test that would settle it). A story consistent with
  the evidence is not a finding.
- Official tools do all pixel work; in-house code orchestrates, records, and may
  compute only a derived result no tool provides, with a removal condition.
  Diagnostics are exempt — any tool is fine for investigating.
- No bandaids. A crop that hides a rim defect is the registered dead-end class.
- Nothing ships without the owner's eyes on full-frame lossless surfaces.
- **Report a null as plainly as a win.** If the chase dead-ends, that is the
  result; say so with numbers.

## 9. Deliverable

A report at the repo root, committed, that states:

- which level the defect enters at (§4's answer), with its instrument;
- the mechanism, MEASURED or labelled HYPOTHESIS with the test that would settle
  it — including a plain null if that is what the evidence gives;
- what it costs the deliverable: how much of the accepted cross-night union is
  affected, and whether a fix would change the owner's verdict;
- ranked fix proposals inside the flatless route, for the owner to decide.
  Nothing executed on the deliverable; the accepted products stay untouched.

If the chase resolves it, the natural follow-on is already queued in
`docs/consistency-tiers.md` §6: fix `member_separation.py`'s zoning, then trial
**SWarp** (packaged for this distro, not installed) as the standards-track
route — per-image astrometric resampling onto a common WCS, which is how the
industry combines exposures across nights and would make the model-scope question
moot.
