# Combine-corner audit — report (maintained current-state)

Scope: the failed aug06 twin combines and the process that produced them —
executed per `COMBINE_CORNERS_AUDIT_PROMPT.md`, then extended by the user's
follow-ups (what changed vs past combines; the restoration experiment; the
defect's re-identification by eye). This file is kept CURRENT-STATE: earlier
verdicts that later measurements superseded are folded in below with their
numbers, not preserved as narrative. Measurement records:
`datasets/aug06/set-03/qa_work/audit_combine_corners_measurements.json` and
the `combine_corner_fail_investigation` / `subsky_lights_restoration` ledger
entries. The open root-cause investigation continues under
`COMPOSE_SMEAR_INVESTIGATION_PROMPT.md`.

Binding scope facts (user-ratified): **synthetic flats are the project's
point — every fix lives inside the flatless route; real flats are never a
recommendation** (`MEMORY.md`). The deliverable class is the framing=max
union, judged by the user's eyes on full lossless surfaces.

Labels: **MEASURED** (instrument + numbers), **ARITHMETIC** (exact
consequence of measured inputs), **DOC** (documentation/published practice),
**HYPOTHESIS** (consistent with evidence, no discriminating test run).

---

## 1. Current verdict

**The defect the user failed is corner STAR SMEAR, and it is CREATED at the
cross-set compose of the aug06 members.** At 1:1 the failing corners show
stars drawn into coherent diagonal dashes over a brushed fabric; the passing
july31 union's corners are round pinpoints. MEASURED (Siril `findstar`, open
gate, 800 px corner/center boxes, green):

| surface | corner FWHM px | center FWHM px | state |
|---|---|---|---|
| aug06 union, max+covcrop (own models) | 4.95 | 3.32 | FAILED by user |
| aug06 union, min framing (own models) | 4.83 | 3.38 | same smear |
| aug06 union, max (single pinned model) | 5.29 | 3.30 | same smear |
| july31 union, min (matched model) | 3.44 | 2.74 | PASSES (user-confirmed) |
| aug06 per-set products | 3.87–4.18 | 3.17–3.30 | PASS |
| member sub-stacks entering the compose | 3.28–3.55 | 2.89–3.19 | mild |

Members enter at ~3.5 px and exit the union at 4.9–5.3 px at like zones —
the smear appears between sub-stack and union, only for aug06's members.

**CORRECTION (superseding measurement — `COMPOSE_SMEAR_INVESTIGATION_report.md`):
the "per-set model heterogeneity eliminated" row below is REFUTED.** It rested
on the corner FWHM column of the table above, and that instrument is a PSF
fitter, which on a doubled star fits one component rather than the blend — so it
ranked the failing own-model union (4.95) as better than the visually CLEAN
single-model control (5.29). Measured directly instead, as the px separation of
the same star as two registered members place it: **2.99 px at the composed
corner under the sets' own models vs 0.93 px for the SAME member pair under one
model**, and at 1:1 the single-model union's corner shows round single stars
where the own-model union's shows multi-component dashes. Heterogeneity is the
DOMINANT driver. Every other elimination below stands.

**Eliminated as drivers, each by direct measurement:**
- framing — the min-framed union smears equally (4.83);
- ~~per-set model HETEROGENEITY — a single-model (pinned) union smears equally
  (5.29)~~ — **REFUTED, see the correction above**;
- member background matching — the `--subsky-lights` arm renders
  corner-equivalent judge surfaces (registry dead-end entry);
- re-aim geometry — july31 spans BIGGER offsets (6.18° vs 3.20°) and
  rotation differences (16.3° vs 8.5°, solved-WCS) and composes clean;
- member corner CONTENT — sub-stacks enter at ~3.5 px;
- member-edge-zone shipping — the min union's corners sit +96..+486 px
  INSIDE the per-set canvases (one −99) and still smear.

**CLOSED — see `COMPOSE_SMEAR_INVESTIGATION_report.md`.** The hypothesis below
was half right: the aug06 members ARE less well rectified than july31's
(astrometry.net SIP outer-field residual 26–30 px vs 13–21 px), and that is the
SECONDARY term (0.93 vs 0.35 px member disagreement under matched single-model
conditions). But the DOMINANT term is the one this section eliminated in error —
composing members warped under three different per-set models. Kept below as
written, for the record.

**Leading HYPOTHESIS (superseded — was the active investigation):** the aug06 members
are insufficiently rectified at large field radii under BOTH available
optical models — the pinned (july-fitted) model is state-mismatched to aug06
(optics ledger: 2× field-term elevation, the very problem the per-set
adoption resolved for set-01), and the aug06 own fits came from a
mid-campaign-modified fit instrument (2.5 s subs, gauss-3 fattening, strict
prune; ledger `fit_instrument_cp_starvation`) with weak corner CP support,
their products already measured +0.1–0.15 px above july31's residual floor,
unattributed (`BACKLOG:optical-state-models`). Residual radial distortion is
the one term a global registration cannot absorb (the undistort route's
founding, measured law) — here acting between members that meet at different
offsets/rotations, so their residuals stop cancelling. july31's members
compose clean because their model was fitted to their own state family.

## 2. The background-level findings (real, SECONDARY — not the failed observable)

The investigation's first two rounds measured background statistics, which
are structurally blind to star smear; their findings stand as true but
secondary, and box medians are FORBIDDEN as this defect's acceptance
measure.

- **Combine-specific corner level term** MEASURED: same-sky cross-arm boxes
  (validated reader, ≤0.1 agreement with Siril `stat` across 15 values) show
  the cov13 corner at +0.8–1.2% above the per-set mean at identical sky over
  the first ~300 px, on top of +1–2% REAL sky structure present in every
  per-set control; the cov28 "patch" is predominantly real sky (+1.4–2.1% in
  all controls), six-member increment +0.3–0.4%. In ADU: ~1 ADU-class.
  HYPOTHESIS: part of this median excess is smeared-star flux raised into
  the diffuse floor (compact stars resist a median; smeared ones do not).
- **Boundary geometry** MEASURED from the coverage maps: the anomalous
  corners are where 8–12 member footprint edges bunch within ~110 px; the
  max+covcrop corners lie outside per-set canvases (−13..−129 px) where
  july31's min corners sit +37..+727 px inside. (This explained the LEVEL
  term's location; it does not explain the smear — see §1 eliminations.)
- **Display amplification** — registered measured law (~√(sky·N)): the twins
  were judged at 2.1–2.9× a per-set surface's amplification (ARITHMETIC from
  verified inputs). Context for how a ~1% level term renders; not the smear.
- **Crop integrity** MEASURED: both coverage crops verified full-coverage
  (map crops min=max=1.0); the `coverage_probe.sh` docstring contract is
  stale (maps are k/n normalized to 1.0, not "value/1000").

## 3. What changed vs past combines (the onset question)

| combine | framing | outcome |
|---|---|---|
| july14 cov25 (5 sets) | max + coverage frame | not a usable control: 16-bit-era chain (kept ~55–70% of faint contrast), products and records deleted |
| july23 combines | min | HAD a user-flagged corner defect (chroma class) — diagnosed then to calibration residuals + the missing background stage; that era's fix arc (desky) shipped and was reverted |
| july31 4-set (17 subs, 1,760 fr) | min | **PASSES** (user's eyes + measured 3.44 px corners) — members matched to their model's state family |
| aug06 twins | max + covcrop | **FAIL — corner star smear** (4.8–5.3 px), also present in the min-framed and single-model discriminator unions built from the same members |

Superseded explanation, kept with its refutation: an earlier pass of this
audit attributed the failure to a conjunction of (a) the missing member
background-matching step (the desky revert's collateral removal of
per-frame `subsky 1` on calibrated lights) and (b) the first execution of
the max+covcrop framing route. Both were then ELIMINATED for the visible
defect by measurement — the restored lights-side step changed nothing the
eye sees (§4), and the min-framed union smears equally. What those factors
govern is the secondary LEVEL term (§2), not the smear.

**Current onset statement: the smear appears with cross-set composition of
the aug06-era members — the first combine-class products built from members
whose optical-state rectification is not at july31's residual floor.** The
per-set optical-state model adoption (the repo's most recent one-variable
change in this area) resolved a measured real problem — set-01 under the
pinned model: off-axis 0.82→0.48 px, the decisive WIN — and its aug06 FITS,
made with the modified fit instrument, are the open suspect for the corner
residual. Note the sharpened form: reverting the change does NOT fix it
(the pinned-member union smears identically), so the suspect is the aug06
fits'/states' corner quality, not the per-set method itself.

## 4. The `--subsky-lights` restoration (closed, measured)

The desky flag coupled two halves; the split is permanent (registry): the
flat-side desky (seqsubsky on RAW flat sources — domain error, 31×
regression) stays dead; the lights-side half (per-frame `subsky 1
-nodither` on calibrated, debayered lights — the correct domain, Siril
doctrine) is restored uncoupled as `--subsky-lights`, default OFF.
One-knob arm MEASURED (members rebuilt, controls preserved): the stage
fired (union sky 107.5→40.4 ADU, MAD unchanged 2.67→2.46) and **did not fix
the corners** — judge surfaces corner-equivalent (DN corner-minus-flank
+2823 vs +2941; −1526 vs −1653), ADU increments c00 1.35→0.55 at the corner
but 0.98→0.94 at 300 px, c11 0.99→1.37. REFUTED as the corner fix; the
render-stage background question (L1) is untouched and open, with one fact
in its favor: degree-1 preserved local structure and noise everywhere
measured.

## 5. Provenance of the deciding numbers (audit question 2 — stands)

The compose skeleton traces clean: membership + largest-fully-covered-crop
(USER-RATIFIED, bcecf0b), coverage maps (official tool via tracked
`coverage_probe.sh`), crop rectangles (in-session numpy, outputs verified
through the registered Siril guard, re-verified), pinned compose reference
(recorded decision, measured mechanism), plain mean + `-norm=addscale`
(official tool; registry-correct). Findings at the margins: the ~6%
night-sky claim behind `--weight=nbstack` traces to no record and
re-measures at ~60% (night medians ~124 vs ~197, same 2.5 s subs — the
tracked docstring already derives `noise` for multi-night); the grid/march
summaries were in-session arithmetic (superseded by controlled same-sky
probes); `regional_stat.py`'s standard geometry under-reaches 0–400 px
corner terms; the judge stretch policy was written for same-depth ladders
and guarantees deeper products are judged 2–3× harsher.

## 6. Mainstream research (audit question 3 — stands, with its scope)

The register+globally-normalized-mean of members with unmatched backgrounds
is documented mainstream-deficient: Siril's own doctrine (one integration of
all frames first-choice; per-frame degree-1 + `-overlap_norm` + `-feather`
for panel stitches; siril.org/faq, tutorials/mosaics), PixInsight
(LocalNormalization/Adaptive/NSG — spatially-varying matching; the NSG
author's demonstration of the skip-it artifact), APP (LNC + MBB), and
professional coadds (SWarp `SUBTRACT_BACK Y` default; SDSS/Pan-STARRS/LSST
per-input sky models). SCOPE: all of that addresses the background/LEVEL
class (§2). The failed observable (§1) is registration/PSF-class, for which
the mainstream reference points are distortion-aware registration and
member rectification quality — the route's own domain.

## 7. Status

- FAILED products, discriminator unions (min, pinnedmodel, subsky1), judge
  surfaces, inspection crops (`sessions/aug06/work/subsky_arm/insp_*.png`)
  and findstar lists are preserved as evidence.
- The root-cause investigation is delegated to a fresh session:
  `COMPOSE_SMEAR_INVESTIGATION_PROMPT.md` — including the user's standing
  questions (full calibration-input provenance per build; the lens-model
  lifecycle across sessions; the exact onset commit/build; whether the last
  change's target issue was truly resolved and whether its implementation
  caused this one).
- No fix is adopted; nothing ships; the user decides on the report's
  proposals.
