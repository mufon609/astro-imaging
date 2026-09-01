# BACKLOG

Open work: what it is, why it matters, and the test that closes it. Completed work
is not carried here — it lives in the operating docs and in `git log`.

**Items are keyed by SLUG, never by number.** Reference one by slug from code or docs — e.g. ``BACKLOG:`render-ladder` ``. Numbered items were the previous scheme and
they failed twice, silently: items 19 and 20 were closed and removed, their numbers
were reused for unrelated work, and seven code/doc sites went on pointing at the
wrong content with nothing to catch it. A slug cannot be recycled by accident, and a
reference to a deleted item is greppable.

An item earns its place by mattering to the REPO. Per-dataset findings live in
`datasets/<session>/<set>/`, mechanism lessons in
[`docs/dead-ends.md`](docs/dead-ends.md), tool facts in [`TOOLS.md`](TOOLS.md).
Anything unintelligible, superseded, or true of only one wiped dataset is deleted
rather than carried.

---

## `standard-route-output-norm` — WATCHLIST (gated on tracked-mount raws being staged): the tracked-mount route still stacks with `-output_norm`

`run_pipeline.sh:331,333,348` (×3 light stacks via `$STACKPOL`) and
`scripts/stack/siril/lights.ssf.tmpl:37` carry `-norm=addscale -output_norm`, the global min-max
rescale the undistort route retired (mechanism + the shipped design:
`docs/dead-ends/stacking-compose.md`, the `-output_norm` zero-point entry). The route is LIVE —
`run_set_chain.sh:773` dispatches it, `route.py:169` sends every tracked mount there — and it HAS
been exercised: `datasets/colonnello-m20/lights_Red/fingerprint.json` records `"route": "standard"`
for a tracked ASI/Takahashi set (three filter sets, 1150 mm, 0.682 ″/px, 15 frames each) whose
composed product's records survive under `m20_rgb/`. What blocks a delta is that those raws are no
longer staged under `sessions/`; every session that still has staged raws is fixed-mount.

Work, when tracked raws are staged: the same shape as the undistort tiers — drop the flag, assert
Siril's own "Output normalization ...... disabled" line, stamp `STACKNRM`/`ANC*`/`REGREF` (the
standard route stamps none of the three — measured 0 lines against 12 in
`run_undistort_compose.sh`; `docs/combine-contract.md`:179,
BACKLOG:`composite-header-identity`'s open (e)), guard advisory under the STACKNRM change; one
product, pre-registered as the undistort tiers were. Removal condition: the same as the undistort
rows' (Siril offering a reference-anchored output normalization).
**Closes when** the standard route ships without `-output_norm` on a measured product, or
records why it must keep it.

## `compose-homography-smear` — CLOSED and homed; one unmeasured trade remains

The union's band and corners are MEMBER-BORNE, in the photons, night-ordered, and answered by
member SELECTION (cropT, owner-approved). Mechanism, refuted alternatives and every number:
`docs/dead-ends/stacking-compose.md` ("THE UNION'S LEFT-BAND / BOTTOM-CORNER SMEAR IS NOT A
REGISTRATION OR COMPOSE DEFECT", "THE SUB-STACK COMPOSE IS A MOSAIC, NOT A STACK",
"PRE-REGISTRATION FRAME-WIDTH CROPPING"); the decision map is
`docs/corner-smear-member-selection.md`; the attribution records are
`datasets/aug09/smear_work/{smear_remarch,rho_march,rho_march_prereg}.json`.

OPEN — one, and it is a TRADE rather than a defect: **interleaved rather than consecutive
GROUPS.** Interleaving moves the station coverage and the dwell-floor / rejection denominators
together, so it is not a free win, and nothing has measured it on this corpus. **Closes when** an
A/B at the combine reports the trade, or the consecutive form is recorded as the deliberate choice.

ALSO OPEN, and deferred rather than dead: **a state-CHANGE detector with a RELATIVE trigger.**
`docs/combine-contract.md` §5 measures model compatibility at every combine and reports it, but the
quantity it reports is ABSOLUTE, and §5's own stated ground for refusing thresholds is that the
number is a SUM OF TWO TERMS whose compose-created half scales with sequence size — two healthy sets
read 1.12 and 0.95 px among themselves and 3.02 / 3.38 px inside a 41° 28-member sequence, 2.5–4.7×
from sequence size alone, so *"no band separates that from a real optical disagreement"*. A RELATIVE
trigger compares a configuration against its OWN prior state, holding that term constant so it
cancels — which is the one shape §5's objection does not reach. The two answer different questions:
§5 asks "is this compatible now?", this asks "has it changed?" — the same split the repo draws
between a quality gate and `baseline_guard.py`'s no-regression record. Its precondition (the
member-separation quantity attributed) is §5's own and has NOT fired.

WITHDRAWN, each with its reason, so that none is re-proposed:
- **The SCAMP/SWarp TPV reprojection as a coadd** — no defect motivates it (the smear is
  member-borne, not a reprojection artifact), and it would COST: Siril composes the SIP
  undistortion with the linear projection in ONE operation *"so as to avoid interpolating pixel
  values twice"* (`docs/untracked-widefield-standards.md` §A.3), so a reprojection coadd adds a
  second interpolation — and it cannot help at ρ 1.80, where the limit is the MODEL's missing
  corner constraint rather than the engine. The scaffolding is retired.
- **A corner-true shared model** — no fit constrains past ρ 1.47–1.51 against a corner at 1.80
  (`docs/dead-ends/registration-distortion.md`, "CORNER CONTROL POINTS CANNOT BE RECOVERED BY
  REORDERING OR RELAXING").
- **A fresh single-model refit against the pinned july14 fit** — withdrawn because nothing
  motivates spending a fit, NOT because doctrine forbids one. `scripts/darktable/lens_models.json`
  carries TWO distinct rules and they must not be conflated: `_why_this_file_exists` governs
  REPRODUCTION ("re-fitting is how you MAKE one; it is not how you reproduce one"), while
  `_how_to_add_one` explicitly PRESCRIBES selection — *"a fresh fit is a CANDIDATE; it becomes the
  shipped model only by being pinned here, and swapping a shipped model is a declared delta judged
  on star_stations + seqtilt (never on the fit's own residual)"*. That path is live:
  `fit_lens_model.sh` and `star_stations.py` both exist and `seqtilt` is a Siril command; only the
  free-centre JOINT fitter is retired.

## `intake-culling` — one measured intake pass, one visible formula

USER-DIRECTED. More photons are always obtainable; a bad frame stacked is permanent. Every recurring defect has a
signature measurable per frame at intake: measure ONCE, score by a formula whose constants are visible and
adjustable, report per frame with its reason. **The decision FORM is a THRESHOLD, not a rank or a percentile**
(owner-ratified — BACKLOG:`final-best-percent-pass`: a rank rule cuts N% from an equal-quality corpus
for nothing). The shipped auto-cull already conforms — the rule is stated and implemented in `cull_report.py`
(robust z vs the pooled median/MAD, defect side only) and re-implemented citing it by
`run_frame_qa.sh:249`, which is what the chain actually reads via `frame_metrics.json`'s
`flagged_defect_side_z`; `cull_report.txt` itself is a printed suggestion nothing consumes — so this is the form to extend, not to choose.

Standards-first: a SEARCHED NEGATIVE — no vendor publishes a default combining expression for per-frame quality
signatures (the community 15/15/20 weighting has underivable constants; the PixInsight source returned 403, so that
provenance is UNVERIFIED), so a visible in-house formula IS the standards-compliant choice, not a deviation.

| signature | what measures it | status |
|---|---|---|
| aircraft / satellite / bug | streak geometry | BUILT — `anomaly_audit.py` |
| shake / wind gust | per-frame FWHM + roundness spike; elongation angle off the trail axis | THE ANGLE TEST WAS MEASURED AND FIRED on 2 of 21 frames, both the first exposure of a night (aug06/set-01 block 1: θ₀ 19.75° off the rest of the set while its own drift bearing departs 0.150° against a 0.062° SE — in the EXPOSURE, not the tracking or the sky; reproduces across detection depth and on july31/set-01 frame 1, −19.5°): `datasets/aug06/corner_work/drift_bearing.json`, commit `b512419` — the RECORD survives, the instrument does not (`git show 426f2d2^:datasets/aug06/corner_work/drift_bearing.py`), so a per-frame form is a rebuild rather than a port; mechanism `docs/dead-ends/star-shape-optics.md`, "ON A FIXED CAMERA THE STAR-DRIFT DIRECTION DOES NOT ROTATE". Still needed for adoption: a per-FRAME form (this is per-block) and a decision on whether one frame is worth culling |
| cloud | background level and its rate of change — star COUNT is measured blind on rich fields (detection saturates at the cap) | per-frame `bg` IS recorded (`scripts/qa/run_frame_qa.sh` → `qa_work/frameqa/records.jsonl`, gitignored; the tracked `frame_metrics.json` carries the distribution). Separability MEASURED — `datasets/aug06/cloud_work/cloud_separability.json`: bg separates aug06/set-03's block at Z +4.05 (n 15, selected without reference to bg) against +1.12 in a matched clean set; nstars carries nothing; the control is the auto-cull's own output, so on this corpus the bar is "agrees with or improves on the z-flagger", never "detects cloud" — closing needs a bad-sky record independent of the QA fields, on a second night |
| light pollution / moon | background gradient magnitude + bearing (the odd-plane term tracks the moon's bearing to 23 deg) | measured once ad hoc; `scripts/qa/flat_odd_component.py` measures it for a FLAT — no per-frame form |
| transparency drift within a set | the STARS' own throughput gradient, block to block — `object_tilt.py`'s per-block gradient term measures a within-set drift of **0.040–0.425 mag across the frame (median 0.149), MONOTONE in block order in 10 of 12 sets**, from Siril aperture photometry on matched stars | MEASURED as a by-product of the object-tilt dead end (`datasets/aug09/corpus_object_tilt.json`); it is a real per-block transparency signal this surface does not otherwise have, and unlike background level it is measured on the OBJECT's own flux. No per-FRAME form — the instrument works on sub-stacks |
| file inconsistency | per-frame mean/median step, EXIF constancy, truncation | not built |
| optical-state change mid-set | geometry residual step (BACKLOG:`compose-homography-smear`) | member-level only; no per-frame form |

Design constraints, each from a measured failure here:

- **Measure once.** One per-frame table, every column a tool's number, written at intake and never re-derived —
  AND naming the ARTIFACT it measured: today's names the raw while every metric is regdata from the debayered
  conversion (`scripts/qa/run_frame_qa.sh`'s docstring carries the mechanism and the 0.151× measurement).
- **One visible constants file**, per-dataset override in `recipe.json`. The aggressive-vs-conservative dial is the
  user's; the pipeline applies what is set and records it.
- **Every signature ships with a POSITIVE CONTROL** — data on which it MUST fire. Three checks have shipped green
  while broken (`docs/dead-ends/verification-traps.md`, "THE REPO'S MOST PERSISTENT DEFECT: A CHECK THAT CANNOT
  FAIL"); a signature that cannot be made to fail on demand is decoration.
- **A cull is not the answer to every defect.** A mid-set optical-state change is not a bad-frame problem: the set
  wants SPLITTING at the boundary, not thinning. The report proposes the action, not just the exclusion.
- Reuse rather than rebuild: `run_frame_qa.sh` / `frame_metrics.json`, `anomaly_audit.py`, `cull_report.py`,
  `inspect_stage.py`, `cullspec.py` (which already aborts loudly on an exclude matching zero frames).

**Closes when** one intake pass writes every signature for a set, a tracked formula turns them into a proposed
action per frame with its reason, and each signature has a control that demonstrates it firing.

## `render-ladder` — the render tier's remaining tiers, user-gated

The first tier is BUILT (`scripts/stack/render_tier.sh`: separate → denoise the starless → stretch →
screen-recombine, every pixel op and every measurement a tool's, gated by a ratified `render` block; it exits 7
without one) — and NO block is ratified: 0 of 24 tracked `recipe.json` carry one (re-measured), `datasets/GENERIC.json` is the `{"render": {}, "why": {}}`
stub, and the tier has never run on this corpus (`datasets/aug06/l1_work/owner_ratification.json`). What remains
is the LADDER around it and the harness it feeds.

- **L1 background level — the FOCUS item (user-ratified), MEASURED at both stages.** Lights-side: per-frame
  `subsky 1 -nodither` on calibrated, debayered lights is restored UNCOUPLED as `--subsky-lights` (default OFF); its
  arm RAN — ledger `datasets/aug06/experiments.jsonl` `subsky_lights_restoration`: REFUTED on its pre-registered
  criterion, NULL on the judge surface (`docs/dead-ends/calibration-flats.md`, "PER-FRAME DEGREE-1 SUBSKY ON
  CALIBRATED LIGHTS DOES NOT REMOVE THE COMBINE'S FULL-COVERAGE-CORNER TERM"). Render-stage: per-frame vs on-stack
  degree-1 (ledger `l1_background_level_perframe_vs_onstack`) MEASURED, and the owner RATIFIED the on-stack degree-1
  PROCESS (`datasets/aug06/l1_work/owner_ratification.json`, the reason verbatim in substance: *"approved
  NOT because the difference is easily visible but because it is NOT. Most improvements on this project have been
  obvious to the eye; this one is not, and catching it anyway is what the honest-checks system was built for."*) —
  a process, not a render block. Framing rulings (user-ratified): the framing=max union is the deliverable (manual
  crop later), no yield excuses; *"more worried about stacking bad sections than about not stacking enough"* governs
  what goes INTO the combine — member selection, `docs/corner-smear-member-selection.md` (the blanket trim RAN and
  is REFUTED: `docs/dead-ends/stacking-compose.md`, the frame-width-cropping entry). Adoption still gates on preserving the frame-filling UNRESOLVED STARLIGHT
  (degree 1 only; `docs/dead-ends/terminology-dust.md`, sense 2 — it is stars, not dust).
- **L2 denoise strength** — the proven chroma killer. Objective instrument is the `noise_split.sh` structured
  term, never whole-frame `bgnoise`. The SHIPPED mode is pinned and is not in doubt: `render_tier.sh:338` runs
  `--denoise_mode separate --denoise_strength <lum> --color_denoise_strength <chroma>`. What is unknown is
  narrower than this item used to claim — whether the historical "chroma saturates above 0.85" observation was
  made under `separate` or under one of the other two modes. The vendor publishes no guidance to settle it
  (setiastro.com documents only "Choose Full or Luminance and the amount", and does not mention `separate`, the
  chroma knob, or ordering), so the CLI is richer than its documentation and the probe is ours to run. The
  positive control it needs is `TOOLS.md`'s Cosmic Clarity Denoise row; not duplicated here.
- **L3 stretch ladder** — GHS/`ght` arms against the current `mtf`, compared at a MATCHED background landing
  so curve shape is the knob, not brightness. RUNNABLE TODAY, probed on the rig: `ght -D= [-B=] [-LP=] [-SP=]
  [-HP=] [-clipmode=] [-human|-even|-independent|-sat]`, which Siril credits to the ghsastro.co.uk team. The
  structural difference from `mtf` is what the arm tests: GHS places the contrast (`SP`) and protects both ends
  (`HP` linear above it, vendor-named as preventing star bloat; `LP` linear below it), where `mtf` has three
  points and no protected regions. NOTHING NEEDS DESIGNING — and nothing published settles it either: ghsastro
  makes no comparative claim against `mtf`, so GHS's standing is adopted practice, not measured superiority.
- **L4 thresholded `satu`.**
- **Riders:** seed `datasets/GENERIC.json` (still the `{"render": {}, "why": {}}`
  stub) with the six current knobs and a per-knob class-risk note; per-arm output
  tree (`web/results/<session>/exp_<param>_<stamp>/`) and the `<final>_stages/`
  labeled sequence, both binding requirements the tier does not yet emit;
  `judgment_package.py` re-wire (its `.metrics.json` producer — the old chain's
  renderer — no longer exists; the PNG16-only surface is already enforced).
- **An UNRECORDED DIVERGENCE in the tier's order, and it should say so.** The one firm mainstream principle
  — noise reduction never before deconvolution, which requires linear data that has not been noise-reduced —
  the tier SATISFIES. But mainstream removes stars AFTER the stretch, and this tier removes them BEFORE and
  denoises the starless while linear. That is defensible and Siril-native (`starnet -stretch` applies an
  INVERTIBLE pre-stretch precisely so a linear stack can be separated), but it is a deviation and nothing in
  the tree records it as one. Siril's own Workflow page publishes no definitive post-stack order, so the
  asserted order rests on community practice rather than vendor doctrine and should not be cited as the latter.
- **One real gap:** a mono set STOPS loudly — the luminance-only variant is unbuilt. (A set carries ONE
  `render` block, `render_tier.sh:195` reading `rec["render"]` as a single dict, so two kept looks are not
  expressible. That is ALIGNMENT, not a limit: the published deliverable is one final per target, and an
  approved look pins every knob.)

One knob per arm, hypothesis pre-registered, judged on full-frame lossless PNG16.
**Closes when** an approved, re-baselined render comes out of a laddered arm.

## `calibration-evidence` — the sky-flat defect is real and PUBLISHED; two of its three threads ride the owner's pause

OPEN DEFECT, mechanism homed: a sky flat converges to `sky × V`, so the object carries the sky's spatial
profile — `docs/dead-ends/calibration-flats.md`: "A SKY FLAT BAKES IN ANY SKY GRADIENT THAT IS FIXED IN THE
ALT-AZ FRAME"; "DEAD END — `--desky`" (a 31× regression, reverted); "THE FLAT'S SHAPE DIFFERENCE REACHES THE
DELIVERED OBJECT ESSENTIALLY 1:1" (the differential delivers the transfer function, not the LEVEL); "A
FOUR-CORNER BOX METRIC IS NOT A GRADIENT MEASURE ON A STRUCTURED FIELD".

**FENCED: threads 1 and 2 sit inside the flat-residual line the owner PAUSED pending real flats**
(BACKLOG:`per-group-flat-at-the-combine` carries the pause and its reason). This item did not say so, and a
session could have picked up thread 1 without ever seeing the pause. Thread 3 is SPCC ordering and is outside it.

**STANDARDS-FIRST, UNAPPLIED — the defect is PUBLISHED and the repo cites none of it.** arXiv 1407.8283,
*"Problems with twilight/supersky flat-field for wide-field robotic telescopes and the solution"*: even at the
null point *"there is still a gradient of 1% across AST3's field-of-view of 4.3 square degrees"*; the authors
*"tested various approaches to remove the varying gradients in individual flat-field images"* and conclude *"the
final optimal method can reduce the spatially dependent errors caused by the gradient to the negligible level"*.
See also Chromey & Hasselbacher 1996, "The Flat Sky" (10.1086/133817). **The technique is NOT in the abstract —
read the paper before acting on this.** And note WHERE it applies: it removes a gradient from each FLAT FRAME
before those frames are combined, which is exactly what `build_sky_flat.sh` does with sky frames. It is a
candidate INSIDE the flatless route, not an argument for acquiring real flats — the synthetic route is the
mission and both flat methods stay available to the pipeline.

**THE `--desky` DEAD END IS NARROWER THAN IT READS, by its own mechanism.** It ran `seqsubsky` on the sky flat's
RAW source frames, subtracting an ADDITIVE plane from a field that is `sky × V`, and the entry's own verdict is
*"a domain error, not a tuning error"*. The published method removes the gradient from each flat-field FRAME
before combination — a different operation in a different domain. The dead end therefore closes the ADDITIVE
form on raw frames; it does not close gradient removal, and the standard form has never been tried here.

OPEN:
1. The with/without judgement pair on finals — the OWNER'S EYES, blocked twice: on BACKLOG:`render-ladder`
   (`render_tier.sh` exits 7 without a ratified block) and on the pause above. The difference is MEASURED at
   −22.5 % of object flux; which arm preserves unresolved starlight is not measurable here. The arms' FITS were
   freed (`datasets/corpus/rig_cleanup_record.json`), the records are `datasets/aug09/set-05/flatdiff_work/*.json`
   (19 of them), and rebuilding the production-normalization pair `arm_{An,Bn}.fit` (skyflat_set-05 vs
   skyflat_set-01, 125 frames each, registration pinned) is part of the cost.
2. `build_sky_flat.sh`'s corner-vs-centre gate is self-fulfilling for this defect and under-claims (it records
   both edge dipoles beside it); the candidate replacement `scripts/qa/grid_ramp.py` fits the ramp as
   coefficients. Swapping an acceptance measure is a USER RATIFICATION — a proposal to the owner, never a change
   to make — and it rides the pause.
3. SPCC order-robustness, NOT fenced by the pause — a background step ahead of SPCC moved K_G −1.20 %/−1.48 %
   and K_B −0.47 %/−0.80 % on unchanged star counts (chain K scatter 0.006), confounded by the de-skied arm's
   real ~3 % object tilt (`datasets/aug06/set-03/qa_work/spcc_set-03_set-01+02+03_full{,_subsky1}.json`); the
   clean test is the SAME stack with and without an on-stack background step only.

**Closes when** the pair is judged, the gate is replaced by ratification or re-described, and SPCC
order-robustness is measured on one knob.

## `walking-noise` — an accepted property of the fixed-tripod class; one measurement remains

Faint DRIFT-ALIGNED streaks visible at native 1:1 and below whole-frame statistics: a sensor-fixed
pattern (readout FPN + residual warm pixels) dragged into lines by coherent un-dithered drift.
QUANTIFIED by `noise_split.sh`, which differences time-halves against interleaved halves so the
excess IS the drift-phase term: ≈0.34/0.48/0.42 ADU (R/G/B) per ~199-frame half, against ≈1.0/1.5/1.2
ADU total static structure.

**NOT OPEN WORK — and the reason is external, not a local verdict.** Rejection and cosmetic
correction both measured NULL here (it is sub-sigma STRUCTURED signal, not discrete outliers), and
the field reports the same: there is no post-processing cure, *"you can only really get rid of
walking noise with dithering"*, and the deeper advice is to cure the field drift itself. NEITHER
remedy exists for this class — 22 of 25 tracked sets are fixed-mount, where coherent drift IS the
imaging mode rather than a fault to cure, and dithering requires moving the mount between subs, an
acquisition change this repo does not recommend. The levers this item used to carry (drift-axis
pattern removal, an AI denoiser) are therefore DELETED: they chase what the field reports does not
work, and the item already called them a bandaid of last resort.

One measured CONTRIBUTOR is gone at the source: 16-bit master darks stored a sensor-fixed ±0.5 ADU
pattern subtracted into every light (0.2889 ADU RMS against a 0.4213 floor, +21%), fixed chain-wide
and enforced by `check_bitdepth.sh`. **Do NOT count that as a measured reduction** — the stack-level
A/B cannot resolve it, the chain's run-to-run variation being ~10× the effect.

**Closes when** `noise_split.sh` runs on a group-built pair and reports whether the drift-phase term
moved after the 16-bit dark fix. That is the one open measurement, on an instrument that exists.

## `native-solve-and-sip` — one probe, and a PASS RETIRES an external dependency

- **Can a native solve retire `solve_field.py` on the mildly-trailed class?** This discharges a
  hypothesis CLAUDE.md names as its own worked example of "nothing is final until it is empirically
  tested": *"native Siril solve was mechanism-verified not to replace `solve_field.py` for trailed
  fields — but that is provisional until the x86 empirical test runs"*. Until it runs, the repo
  asserts that provisionally while maintaining the external venv route on its strength.
  The test is ALREADY SPECIFIED — three arms, one stack, pass criterion "(a) is the baseline; retire
  only if (c) matches" — at `docs/x86-empirical-test-plan.md`, Phase 3 remainder; not restated here.
  Two things worth carrying into the run, because this item previously understated both: arm (c) is
  `platesolve -localasnet -blindpos -blindres` WITH `setfindstar -relax=on -roundness=0.1
  -maxR=large`, and that detection relaxation is aimed squarely at the stated blocker (`-localasnet`
  feeds Siril's own `findstar`, which is why the dead end measured roundness 0.615 —
  `docs/dead-ends/plate-solving-wcs.md`, "Siril's internal solver fails ultra-wide TRAILED fields");
  and arm (b) is ASTAP, a second candidate this item omitted entirely. All three commands exist on
  the rig — `platesolve` in 1.4.4 carries `[-localasnet [-blindpos] [-blindres]]`, probed.
  The class is present: july27/set-01 at roundness 0.786 (`qa_work/frame_metrics.json`) substitutes
  for the departed july23's 0.80.
- `register -disto=master` — UNDETERMINED, and distinct from the `-disto=` TRIGGER that has already
  landed: the option shipped in Siril 1.4.0 and 1.4.4 carries it on both `register` and `platesolve`,
  but the SIP form was measured a LOSS here (majFWHM 4.74 → 6.02 px), and `-disto=master`
  specifically is unprobed. The probe is specified in `docs/dead-ends/registration-distortion.md`,
  "A STANDALONE PER-MEMBER SIP WARP, APPLIED OUTSIDE SIRIL'S REGISTRATION, IS WORSE THAN THE SHIPPED
  ROUTE".

## `one-sided-band` — one unattributed radial term; the STATUS HOME nine docs point at

CLOSED, homed: the term is in single raws and no chain stage causes it —
`docs/dead-ends/star-shape-optics.md`, "THE ONE-SIDED STAR-SHAPE GRADIENT IS IN THE
OPTICS-AND-PHOTONS OF A SINGLE EXPOSURE", "THE THREE-LEVEL SEPARATOR", "ON A RECTILINEAR LENS
THE PLATE SCALE IS NOT ONE NUMBER" (18 % to the gnomonic scale; the remainder at 5.9 SE), "AN
ELLIPTICITY EXPONENT IS NOT A BLUR EXPONENT", and "THE ONE-SIDED RADIAL TERM'S CANDIDATE
FAMILIES AND THEIR DISCRIMINATORS ARE DOCTRINE"; the union's band →
BACKLOG:`compose-homography-smear`. Records: `datasets/aug06/corner_work/` —
`coherent_trail_bins.json` (trail ratio 0.3502, predicted ZP deficit 0.570),
`phot_work/zero_point.json`, `cfa_control.json`, `pa_convention.json`; ledger
`corner_radial_term_family_and_centre`.

**THE FAMILY CANNOT BE ATTRIBUTED BY ANYTHING INSTALLED, and that is the item's real state.** Coma-
consistent, astigmatism not reached, the radial↔tangential sign flip absent — and no installed
instrument separates them. The wider field reports the same limit rather than a gap in this repo:
corner stars are too scarce to constrain a rapidly-varying corner PSF. So "attributed" is not a
condition this rig can meet on its own, and the item must not be read as scheduling that.

WHAT IS ACTUALLY REACHABLE — three threads, all cheap, and this item had LOST all three while
`docs/untracked-widefield-standards.md` §H.3/§H.5 went on citing them:
1. **The decentring-model blocker is ANSWERED.** lensfun's `acm` (Adobe Camera Model) carries
   Brown's decentring pair as `k4`,`k5`, but it is ABSENT from the installed 0.3.4 — MEASURED,
   0 occurrences of ACM in `liblensfun.so` against 7 for poly3/poly5/ptlens — and appears only at
   v0.3.95, implemented in the CORRECTING direction only, which is the direction darktable needs.
   So it is a version wait, not a design blocker (§H.3).
2. **Read `d,e` out of the existing `lens_fit.json` records** — FREE, it sizes the asymmetric term
   from data already on disk before any new fit is commissioned (§H.3.2).
3. **The `lensdist` vs `nodist` arm**, one knob, both styles pinned in-repo
   (`scripts/darktable/{lensdist,nodist}.dtstyle`) — it separates the model from everything else.
   Re-derive the drift rate first (§H.4); it is an input to the arm and to the discriminator, which
   is defined in units of drift span.

The unrun per-set discriminator (whether the ±2400 FWHM asymmetry is the odd ELLIPTICITY term) reads
`top30_round` from `datasets/corpus/member_selection/profiles.json` — the data is there, 693 entries
— but running it means WRITING A NEW IN-HOUSE ANALYSIS, the class this repo has just retired. It is
recorded as available, not as scheduled.

**Closes when** threads 1–3 are read out, or the term is registered as an accepted, characterised
property of this lens. A REMEDY is not this item's business — that is BACKLOG:`corner-fix-landscape`.

## `pointing-record-names-the-wrong-frame` — two header fields that are not the pointing

Two traps, both real, neither corrupting a shipped product — nothing on the build path consumes
either quantity as a pointing — but both silent and both inviting the same mistake. **The fuller
statement of both already lives in `scripts/setup/site_verification.json`**, which states them
together ("THE TREE CARRIES THREE DIFFERENT 'CENTRES' AND THEY DISAGREE BY UP TO 3.2 deg") and is
the better record; this item is the queue entry, not the explanation.

**1. `fingerprint.field_center` is the FIRST FRAME's solve, not the set's pointing.** MEASURED and
still true: it equals `mount_probe.json`'s `solve_a` to every digit in all three sets checked
(302.945 / 306.727 / 308.558), and the probe's window is the FIRST frame of the longest contiguous
run. A fixed camera holds a fixed alt-az direction whose RA rises at ~15.041°/hr, so the first frame
is always the LOWEST and the record is systematically low by about half a set's RA span — re-measured
against current products, −3.733 / −3.719 / −5.311° for aug06/set-01, aug09/set-01, july31/set-01.
The sign is forced by the geometry, not a coincidence.
**The name is not the defect — the SCOPE is.** "Field center" is astrometry.net's own term for one
exposure's solved centre (verbatim in `solve-field`), and the record holds exactly that; what is
missing is that it sits in a per-SET record. So `first_frame_center` is the right rename because it
keeps the tool's noun and supplies the scope. No external vocabulary exists for a set-level centre.

**2. `CRVAL1/2` is the WCS TANGENT POINT, and the FITS standard says so.** Greisen & Calabretta 2002
(Paper I, astro-ph/0207407) §2.1.4: *"the reference point location need not be integer nor need it
even occur within the image"*. So this is a DOCUMENTED property, not a local discovery — CRVAL is the
world coordinate at the reference point and CRPIX says where that point sits, neither defined against
the image centre. MEASURED over 84 products carrying both: CRPIX sits **21.7–1354.4 px** from the
image centre, and the repeat is the tell — `(306.62, 42.00)` serves 12 products across aug06/aug09/
aug14 and `(310.62, 43.24)` serves 12 across aug09/aug14/july31. A quantity repeating across
unrelated pointings on three separate nights is not a pointing.

**WHAT IS AUTHORITATIVE — and the item previously got this backwards.** The standard pointing keyword
is `RA_PNT`/`DEC_PNT` (HEASARC dictionary: *"the Right Ascension of the pointing direction"*), and it
is ABSENT from every product here — measured. `OBJCTRA`/`OBJCTDEC` are not standard keywords at all
and by convention name the OBJECT, so their close agreement with the field centre is EMPIRICAL, not
definitional, and holds only while the object is centred. **The primary is therefore the full WCS
solution evaluated at the CENTRAL PIXEL** — which is what astrometry.net itself reports as a field
centre — with `OBJCTRA` as a cross-check, never the authority.

**Closes when** `field_center` is renamed to `first_frame_center` (or computed as the set's actual
pointing). Scope, measured, because "a two-file edit" understates it: NOTHING reads the key by string
— the only code site is the writer `fingerprint.py:312`, and `verify_site.py`'s two hits are prose —
but 25 of 25 tracked `fingerprint.json` carry it, and they regenerate LAZILY (the writer rewrites only
on a whole-dict change), so the tree holds a mixed population until every set re-runs, and a set never
re-run keeps the old key. About six sites plus that migration.

## `corner-fix-landscape` — the anisotropic class IS procurable; this is now an owner decision, not research

Rule: every candidate is FIX / TRADE / BANDAID before it is listed; a trade or a concealment never
shares a list with a fix. CLOSED, homed: no route ON THIS RIG recovers corner detail — a single
global PSF cannot (no field-constant trail scale on three grids:
`datasets/aug06/corner_work/{constancy_fit,frame_depth,cfa_control}.json`);
`docs/dead-ends/separation-deconv-psf.md`, "NO INSTALLED TOOL DELIVERS A FIELD-VARIABLE ANISOTROPIC
PSF CORRECTION" (per-region tiling is pixel surgery, FORBIDDEN) and "PSF HOMOGENISATION — REFUSED BY
THE OWNER" (zone down-weighting is the same act); the blanket trim (owner-directed, RAN, REFUTED —
`docs/dead-ends/stacking-compose.md`, the frame-width-cropping entry). The FIX-class route that
SHIPPED is member SELECTION (cropT, owner-approved; `docs/corner-smear-member-selection.md`); what it
cannot remove is the lens's SYMMETRIC radial softening, and this item is about THAT.

**THE PROCUREMENT QUESTION HAS COLLAPSED TO ONE PURCHASE, and the old list was excluding the answer
on a false reason.** `TOOLS.md`'s anisotropic row said "BXT is PixInsight-hosted (uninstalled by
choice)" while the BXT row five lines above it records a standalone `rc-astro` v1.0.0 CLI plus a
Siril script, no PixInsight host, Linux supported, CPU fallback on a no-GPU rig. Both cannot be true;
the row is corrected. And BXT is spatially varying BY THE VENDOR'S OWN ACCOUNT (BlurXTerminator
Technical Manual): aberrations *"vary across the field of view, with stars in the corners of an image
rarely being as sharp as stars in the center"*, and BXT *"uses stars in an image as PSF references in
a local fashion ... apply[ing] different corrections to different parts of the image"*. That is this
item's defect, named by the vendor. It is an OFFICIAL TOOL doing the pixel work, so the bright line
permits it outright.

OPEN — and both are the owner's, neither is research:
1. **Buy a BXT licence ($99.95, perpetual, CLI free to holders and offline after activation) and
   measure it, or accept the corner as-is.** THE CAVEAT IS PHYSICS AND MUST BE CARRIED INTO ANY
   TRIAL: BXT estimates its local PSF FROM STARS, and this corpus's corners are star-poor by the very
   scarcity that defeats a corner-true fit — so its correction is weakest exactly where the defect is
   worst. Vendor capability is not evidence about THIS data; only a trial on a real corner is.
   The multi-week alternatives are superseded and no longer worth carrying as candidates
   (`torchmfbd`'s three documentation checks, `pyimcom`'s survey-schema fork); `galsim.des.DES_PSFEx`
   stays installed for PSF EVALUATION only. Details: `TOOLS.md`, Tier 5.
2. **`-noclamp`** — a TRADE, and the owner's after one measurement: the cost is measured
   (BACKLOG:`resample-cost-and-drizzle`), the ringing it prevents is NOT. A planted fixture with a
   sharp-edge target closes it.

**Closes when** BXT is trialled on a real corner or the corner is accepted as-is, and `-noclamp`'s
ringing is measured against its known cost.

## `resample-cost-and-drizzle` — the clamp is the resample cost and a pinned trade; drizzle is DECIDED OUT

MEASURED (ledger `datasets/aug06/experiments.jsonl`: `resample_cost_arm_d_siril_pass`,
`resample_cost_series_run`, `resample_cost_arm_d_COMPLETE` — the LAST entry of each id): the clamped
Lanczos4 pass costs ~6 % of PSF width and the CLAMP is essentially all of it (kernel 0.45 %, nearest
control exactly 0.00 %), ~12 % over the chain with the darktable warp — quote ~6 %/~12 %, never three
figures; ONE FWHM (2.10 px) and ONE phase set were planted, so the fractional-phase spread and the
FWHM dependence are unmeasured (`docs/dead-ends/separation-deconv-psf.md`, "PSF HOMOGENISATION —
REFUSED BY THE OWNER", the clamp clause). The clamp is a PIN and a TRADE
(`scripts/stack/check_registration_pins.sh:60`: *"clamping is the DEFAULT this repo keeps (lanczos4
rings on stars)"*; ringing is judged, blur is measured). Whether to KEEP the pin is
BACKLOG:`corner-fix-landscape` item 2, which needs the ringing measured — not restated here.

**DRIZZLE IS DECIDED OUT, on three independent grounds rather than a category judgement.** It was
listed as an open question; it is not one.
1. **SAMPLING.** Drizzle is the documented fix for UNDER-sampled data, and the field's own rule is
   that on oversampled data it "makes no sense ... you will only get more noise". These stars run
   2.0–2.4 px FWHM — at or above critical sampling, where the documented benefit has already ended.
2. **ARCHITECTURE, and it is a hard either/or.** Bayer drizzle needs UNDEBAYERED input, while the
   undistort route must debayer BEFORE the geometric warp because a CFA mosaic cannot be warped
   without destroying the pattern (`run_undistort_pipeline.sh:58`, and `:277` calibrates with
   `-cfa -debayer`). `seqapplyreg -drizzle` accordingly refuses a debayered RGB sequence (ledger
   `two_probes_drizzle_input_and_otf_zeros`). You can have the undistort route or Bayer drizzle,
   never both.
3. **THE ONE "UNPROBED" PATH PRODUCES A DIFFERENT PRODUCT.** `split_cfa` exists in 1.4.4 but
   "splits the loaded CFA image into four distinct files" — a mono green-plane route, not the colour
   deliverable. It is not an untried option for this product; it is another product.
Recorded honestly: this is the one place the field would say a 24–70 mm wide-field class DESERVES
drizzle and this chain's geometry forbids it.

OPEN — one, and it is subordinate: the planted arm across a spread of sub-pixel phases and ≥ 2
planted FWHM, reported as a RANGE rather than the current single-point ~6 %/~12 %. It only matters
if the clamp pin is revisited, and that decision waits on the RINGING measurement in
`corner-fix-landscape`, not on a tighter cost figure. **Closes when** that arm reports a range, or
the pin is reaffirmed and the range is recorded as not needed.

## `siril-1.5` — WATCHLIST (fires on a version bump), and the one risk is MIGRATABLE TODAY

1.4.4 is current stable (no 1.5 release exists — siril.org/download, siril.org/posts and the
free-astro GitLab tags all agree); 1.5 is dev master. The trigger is a version bump, not the rig.
**Every claim below is verified against master's own `src/core/command_list.h`, not inferred.**

- **RISK, load-bearing and CONFIRMED: `starnet`/`seqstarnet` are GONE in master** — neither is
  defined in `command_list.h`, while both exist in 1.4.4. `render_tier.sh` calls `starnet` (4 sites,
  the only caller in the tree), so a 1.5 bump breaks the shipped render tier.
  **BUT THE MIGRATION DOES NOT NEED 1.5 AND CAN BE DONE NOW, which removes the coupling entirely:**
  `pyscript` already exists on 1.4.4 (`pyscript [-async] scriptname.py [script_argv]`, probed), and
  `StarNetAstro/StarNet.py` is published in the `free-astro/siril-scripts` repository. That repo is
  NOT cloned on this rig — `find / -name StarNet.py` returns nothing — so the one prerequisite is a
  clone, the same pattern `CLAUDE.md` already documents for the SPCC database. Migrating
  `render_tier.sh` to `pyscript` on 1.4.4 makes the bump a non-event instead of a break.
- **Adopt on 1.5: the native `mask_*` subsystem**, confirmed present in master and richer than this
  item claimed — `mask_autostretch`, `mask_bitpix`, `mask_blur`, `mask_feather`, `mask_fmul`,
  `mask_from_channel`, `mask_from_color`, `mask_from_lum`, `mask_from_stars`, `mask_invert`,
  `mask_threshold`. The first native path to region-confined ops without a hand-rolled blend. All
  are ABSENT from 1.4.4 (zero occurrences in its help output).
- **Retirement candidates, both confirmed in master:** `healpix` (defined as
  `{"healpix", 0, "healpix", process_healpix, ...}`) lists the NESTED pixels overlapping a solved
  image — what `spcc_cone.py` hand-rolls; adopting it still needs a check that its list maps to the
  zenodo chunk names. And `eqcrop ra1 dec1 ra2 dec2` — with `-marginpx=`/`-marginasec=` options this
  item did not mention — the natural consumer of a framing record's RA/Dec form
  (BACKLOG:`framing-radec`).
- **Noted for BACKLOG:`corner-fix-landscape`:** the same `siril-scripts` repo carries
  `RC-Astro/BlurXTerminator.py`, `NoiseXTerminator.py` and `StarXTerminator.py` — the concrete
  mechanism behind the RC-Astro-from-Siril route that item now turns on.

**Closes when** `render_tier.sh` no longer depends on a command 1.5 removes, at which point this
becomes an ordinary adopt-on-bump list rather than a break risk.

## `final-best-percent-pass` — the CROSS-SESSION final pass; the member tier already shipped

The standing multi-session practice's endgame (user-ratified): once many ~500-frame sets accumulate
on ONE target, a final pass re-selects from ALL sessions' data. That cross-session scope is this
item's whole content — the FORM and the member-tier results are homed elsewhere and are not
restated:

- **The FORM is ruled and recorded** — every pipeline rule is a QUALITY THRESHOLD that excludes
  nothing on an equal-quality corpus, never a rank or a percentile. The owner's reasoning, verbatim
  and in fuller form than this item ever carried it, is `docs/corner-smear-member-selection.md`
  (the rulings list, rank-vs-threshold).
- **The MEMBER tier is SHIPPED**, with its full arm table — sel57, crop20, cropT, the SWarp taper,
  cropTselT, the encoded stage and the chain — in the same document. In the tree:
  `run_corpus_combine.sh --portion-rule` → `run_member_crop.sh`, the canonical corpus built under
  it, guarded by `datasets/corpus/baseline.json`, per-member selection recorded in
  `datasets/corpus/member_selection/*_portion.json`.

**WHAT IS ACTUALLY OPEN, and where the boundary with BACKLOG:`intake-culling` sits.** The per-FRAME
cross-session quality surface does not exist: per-set `frame_metrics.json` does, but nothing
thresholds ACROSS sessions and `cullspec` excludes are per-set. The two items are one surface at two
layers and neither should describe the other's work — **`intake-culling` builds the MEASUREMENT
layer** (one pass, every signature, per frame, at intake, each with a positive control);
**this item is the SELECTION layer that consumes it across sessions**. Its form is already fixed by
the ruling above, so nothing here needs designing once that surface exists.

Selection is adopted only through a measured arm with a pre-registered prediction, never as a
default. **Closes when** a final-pass product is built from measured THRESHOLD selection at the
FRAME tier across at least two sessions' data, with its per-set selection recorded.

## `session-level-mount` — one tripod pays for up to FIVE probes, and the redundant part is the RATE

`mount` is modelled PER SET while it is a session-level fact. MEASURED across the corpus: all 7
sessions carry ONE mount value across every set — none mixes fixed and tracked — and two sessions
(aug09, aug14) hold 5 sets each, so "up to four" understated it. 20 `mount_probe.json` records exist
against 25 sets.

**WHAT IS ACTUALLY REDUNDANT IS THE MEASURED RATE, not just the label** — which is why this is worth
closing rather than a naming quibble. The probe plate-solves TWO time-separated frames per set
(`mount_probe.sh`, on the build path at `run_set_chain.sh:352` and `:539`), and the route key is
`drift_frac = (sky_sep_deg / probe_span_min) × set_span_min / fov_deg` (`route.py:31`). The first
factor is the sky RATE, which on one tripod on one night is the sidereal rate and identical for every
sibling set; only `set_span_min` is per-set. So a session-level rate lets each set derive its own
`drift_frac` from its own span with no second probe — the cost being two plate solves per redundant
set, ~36 solves across the current corpus.

Two constraints on the seeding, both already known: a re-aim changes the POINTING but not the rate,
so the rate seeds safely while provenance stays per set and a re-aimed set still cross-checks; and
the probe's window must stay inside the longest contiguous capture run, since a naive first/last
window mixes sky drift with a mid-run re-aim (measured: 6.9751 vs 14.8724 deg/hr on the same frames).
Note also that the probe's plate-scale output is separately defective
(BACKLOG:`frame-qa-order-dependent-scale`), so a single session-level probe CONTAINS that defect to
one measurement instead of seeding it per set.

**Closes when** a decisive session-level measurement seeds every sibling set's record.

## `per-group-flat-at-the-combine` — WATCHLIST (owner-PAUSED pending real flats): the trade is only decidable at the combine unit

**PAUSED BY THE OWNER pending real flats** — the flat-residual research line is on hold until real
flats exist to compare actual frames against the current synthetic masters. This is an owner decision
about sequencing, NOT a recommendation from this repo to acquire them: the synthetic-flat route stays
the mission and "a real flat" remains the divergence's removal CONDITION. Do not pick this item up
before that comparison exists.

**The measurement is CLOSED and lives in full at `docs/dead-ends/calibration-flats.md`** — the
composed +0.055% ± 0.083% at 0.7σ over 1217 stars, why it is zero BY CONSTRUCTION, the 75–94%
cancellation (predicted before it was measured), the 1:1 member transfer with its planted 1.007/1.077,
the 28–40× background consistency flagged as the self-fulfilling direction, and the 3.271%/4.335%
member-to-member object-imprint COST against exactly zero for the per-set flat. That document states
it more completely than this item ever did and is the reference; the record is
`datasets/july31/set-03/pergroup_work/pergroup_flat_report.json` (its member figures are the `"10"`
subset — recomputing across all entries gives different numbers).

**WHY THIS IS NOT OPTIONAL TO RESOLVE — the part that is only here.** The member is the cross-night
COMBINE unit, and the binding rule is that every calibration/model/route change is evaluated against
the COMBINE unit, not just per-set products — measured twice already, per-set models smearing
cross-set unions. A per-set verdict on a member-level trade is therefore an incomplete verdict, and
the SIGN of the trade can invert at the combine: member imprints that cancel within one set need not
cancel across nights whose skies differ. No instrument here can say which member calibration is
closer to truth, so what the data cannot settle goes to the owner under the evidence gate.

**Closes when** a combine-level A/B, one knob (the flat window), members from both arms, is judged at
the combine — the level where the disagreement either averages away or compounds.

## `lunar-ladder` — WATCHLIST (needs the next lunar capture + a PSS venv): set-02 STILL AWAITS A VERDICT

**STATE: the first corpus is processed end to end and the chain is codified as
`scripts/stack/run_lunar_pipeline.sh`** (PROVISIONAL as-written — its first fresh run is the next
lunar corpus, and it must be, because the session tree is freed: `sessions/july26` and
`web/results/july26` are both absent). Mechanisms: `docs/lunar-lucky-imaging.md`.

**RATIFICATION IS HALF DONE, and the item previously claimed it was whole.** set-01 IS ratified —
its ledger carries three closed verdicts: sb deconvolution selected as the primary arm (both sb and
wiener passed on the user's eyes, sb cleaner, wiener carrying a top-edge artifact band), per-set
disc-neutral WB PASS (kR=1.1936, kB=2.1116), and mineral `satu` CLOSED-FAIL on both arms with the
natural disc-neutral WB control winning. **set-02 is NOT ratified**: its ledger's last entry is
`approved_chain_replication` at `status: "awaiting user verdict"` with no verdict key, and no
ratification for set-02 exists anywhere under `datasets/july26/`. That is a LIVE OPEN VERDICT and
the previous wording hid it.

**Remains open:**
- **The x86 quality ladder** vs the shipped q100 controls (PSS `--stack_percent` or AS!4 —
  pre-registered in both sets' ledgers). Needs a PSS venv on the x86 rig + re-staged data (NEFs from
  archive, replay the pipeline stages, or re-shoot better).
  **THE BRACKET AS WRITTEN IS TOO NARROW and should be widened before it runs.** It reads
  10/15/20/25%, every arm at the aggressive end. The field's own comparison set is 10/25/50/75%, and
  the general rule for frames of similar quality is nearer 50% — a ladder topping out at 25% cannot
  find an optimum at 40%. The METHOD is right and is exactly what the field does (the optimum is
  seeing-dependent and not knowable in advance, which is why it is bracketed per dataset rather than
  fixed), so this is a parameter list to widen, not machinery to design.
- **Next lunar capture at the corrected card** (acquisition checklist lunar block: disc histogram
  50–70% — f/4 · 1/320 s · ISO 800 at 70 mm class) — more photons beat every processing knob
  measured this corpus.
- **Siril 1.5 MPP adoption test** — retires the GUI step when stable lands and it measures quality.
- Long-focal escalation ladder (dormant until such a corpus): AS!4-under-Wine vs PSS vs 1.5-MPP.
  **AS!4-under-Wine is a documented path, not wishful** — a dedicated Linux/Wine install guide
  exists and the stated requirement is Wine >= 6.x, so the risk is configuration rather than
  feasibility. Also dormant: Hugin for mosaics; RGB-align only where dispersion is measured
  (>= ~800 mm). **UNCHECKED: whether waveSharp 3.0 / ImPPG 2.1.0 are still the state of the art for
  lunar finishing** — recorded when they were, not re-verified since, and the planetary-stacking
  landscape has moved.

Class facts, records and the full mechanism set live in
[`docs/lunar-lucky-imaging.md`](docs/lunar-lucky-imaging.md), `docs/dead-ends.md`
(registration/aliasing/seq-hygiene/quality entries + the acquisition checklist's lunar block),
`datasets/july26/` (ledgers with every verdict), and the builder's own docstring.

## `web-culled-frames` — one surface for every excluded frame; the DATA LAYER IS ALREADY DONE

USER-ORDERED: the Sky Objects section becomes **Culled Frames**, the single examination surface for
every frame the pipeline excluded, grouped by CAUSE — sky objects (anomaly audit) as one subset,
frame-QA defect-side auto-culls as another, hand-ratified `recipe.json` excludes as a third. Each
entry shows frame + sequence n, set, cause with its metrics, and the record it traces to. The
existing culled rollup MERGES into it. Selection surfaces only — any per-frame preview is Siril-made.

**SCOPE, MEASURED, because this reads like plumbing and is not.** All three causes are ALREADY on
the per-set model `serve.py` hands the front end: `"anomaly"` from `audit_work/anomaly_audit.json`
(`serve.py:431`), `"flagged"` from the frame-QA record (`:219`, and `_norm_frame_qa` already
normalises both historical spellings — `flagged_defect_side_z3p5` from set-01 and
`flagged_defect_side_z` from later sets — so no schema migration), and `"recipe"` → `.exclude`
(`:426`). **NO `serve.py` CHANGE AND NO NEW RECORD ARE NEEDED.**

What the existing rollup covers is ONE of the three: `index.html:174`,
`const culledIds = s => ((s.recipe || {}).exclude) || []` — hand-ratified excludes only, and it is
read at 8 sites in that file. The work is `web/index.html` alone: widen `culledIds` to union the
three sources with a cause tag, merge `totals.culled`/`totals.objects` (:326), group the `#culled`
table and give it per-cause metric columns, and delete the `sky objects` card (:414-416) with its
`#objects` route. Known limit already recorded in place (:704): thumbnails for culled frames need
raws re-staged, so the surface stays selection-only.

**Closes when** after a chain run with auto-culls the page lists every excluded frame under its
cause and the separate Sky Objects entry is gone from the grouped rail.

## `framing-radec` — the built half is BUILT; the unbuilt half has an industry format we do not consume

The capture, verification and diagnostic-consume sides are built and exercised. VERIFIED in the two
tracked records (`datasets/aug06/framing_stack_set-01+02+03_full_wcs.json`,
`datasets/aug14/framing_stack_aug06+aug14_crop5lr.json`, both `status: verified`): each carries BOTH
coordinate conventions with the y-flip trap visible in the data — same x/w/h, different y
(`rect_fits` [364, **546**, 6643, 3549] against `rect_siril_crop_args` [364, **495**, …]; and
[2889, **844**, …] against [2889, **426**, …]) — plus four WCS RA/Dec corners.
`web/verify_framing.py` stamps a record with Siril `crop`+`stat` (its docstring carries the reason:
an unverified screen-order box once shipped a vertically mirrored, zero-coverage wedge), and
`finish_render --crop-record` applies a VERIFIED record to the LINEAR stack before solve/SPCC/stretch
(`finish_render.sh:163`), refusing an unverified record (`:115-117`) and a canvas mismatch
(`:121-124`).

UNBUILT, confirmed absent: deriving the rect on a REBUILT canvas from the record's RA/Dec corners.
A canvas mismatch is refused, never re-derived, and `eqcrop` appears nowhere in `scripts/` or `web/`
(word-boundary checked — the apparent hits are all `seqcrop`). Siril 1.5's `eqcrop ra1 dec1 ra2 dec2`
is the natural consumer (BACKLOG:`siril-1.5`).

**STANDARDS-FIRST, and the standard covers only HALF of this.** SERIALISING a region against a WCS
is solved: the DS9/funtools REGION FILE FORMAT declares shapes in a sky frame (`fk5`, `galactic`, …)
— e.g. `box(11:24:39.213,-59:16:53.91,42.804",23.616",19.0384)`. **What the standard does NOT cover
is this repo's actual requirement**, because the mainstream does not have it: PixInsight's crop is
pixel-based and its process icons re-apply PIXEL parameters, so the accepted workflow is to RE-CROP
after a rebuild rather than restore a framing. A repo that rebuilds products and wants the framing to
survive is asking a question the field does not ask — so `framing_<product>.json` is an ADDITION
where the standard is silent, not a departure from it. **Adopting the DS9 serialisation buys nothing
today either, for a measured reason: nothing in this chain reads DS9 regions.** Siril does not
consume them, `eqcrop` takes ra/dec ARGUMENTS rather than a region file, and astropy's `regions`
package is not installed here (`ModuleNotFoundError`). Converting would add a dependency and change
no behaviour. Revisit if `eqcrop` lands, at which point RA/Dec corners are the input format anyway.

**Closes when** a drawn box renders to a final matching it AND the record reproduces that framing
after a stack rebuild.

## `route-recommendation` — the last wiring on the distortion route

The route is validated, scripted, and the chain routes on the measured key
(`scripts/lib/route.py`: tracked → standard; fixed with `drift_frac` ≥ 0.05 →
undistort groups; below the floor → standard). Remaining:

- **Per-lens facts re-derive at the next new lens/body/focal:** confirm lensfun
  coverage, interpolation behaviour and crop factor before first use. Any focal not
  fitted rides the community entry until fitted (`fit_lens_model.sh` per focal). A
  community profile can be right at the corner and wrong paraxially — the drift-axis
  station measure is the backstop `seqtilt` cannot provide.
- **The undistort route's FLAT source is the per-set sky flat only.** A session
  with real flats staged is refused (`run_set_chain.sh` exit 6; readiness goes
  RED first on the one-click path) with the two commands that resolve it by
  hand (owner precedence: real flats WIN when present — the wiring makes staged
  flats USED, never a recommendation to acquire them). Closes when the chain
  builds a master flat from a staged `flats*`/`calib` dir and passes it as
  `--flat=` — the builder already takes any master, so this is chain wiring,
  not a builder change.
- **The undistort route refuses a FITS dedicated-astrocam set (`exit 9`) — the refusal is RIGHT and
  its STATED REASON IS FALSE.** It reads "the undistort builders take camera raws (darktable's lens
  stage reads raws)". MEASURED: `darktable-cli` 5.4.1 INGESTS FITS — a synthetic 3-plane float FITS
  exported to TIFF at exit 0. `darktable` reading FITS at 5.4.1 is a fact this repo already held; only
  a FITS *writer* is missing. **The real blocker is the LENS PROFILE, not the file format.** A
  dedicated-astrocam frame carries no camera/lens/focal EXIF (`exiv2`: "unknown image type"), so
  lensfun matches nothing and darktable applies NO CORRECTION SILENTLY — precisely the trap
  `lens_preflight.py` exists for ("an unmatched lens gets NO correction, silently", :23). That reason
  is also more durable: it does not evaporate if darktable's FITS support improves.
  **It is NOT permanent, and should not be recorded as a closed door.** `fit_lens_model.sh` fits
  a,b,c from a SET'S OWN FRAMES via Hugin star correspondences — a method indifferent to whether the
  glass is a camera lens or a telescope — so a telescope's distortion could be fitted and pinned the
  way the Nikkor's is. That, not a FITS reader, is what would open this route to the class.
  **Note the guard is currently UNREACHABLE:** it fires only on `ROUTE != standard && LIGHTS_KIND =
  fits` (`run_set_chain.sh:280`), and the only FITS sets on the rig (`colonnello-m20/lights_{R,G,B}`)
  are TRACKED, so `route.py:169` sends them to the standard route before the check is reached. The
  guard is correct and dormant, not firing in practice.

## `cross-set-record-home` — the corpus has a record home; the FINISH stage still cannot write to it

`datasets/corpus/` IS the corpus-level home and holds the corpus records — `baseline.json`,
`recipe.json`, `member_selection/` (stage records + the profile cache), `smear_attribution/`, the
first build's finish records and the rest (`datasets/corpus/README.md`). What is still wrong is the
FINISH stage: `finish_render.sh:66` hard-requires `--session=` and `--set=` ("SPCC spec routing +
record naming"), so a combine's finish records file under the REFERENCE set instead.

**THE WART, RE-MEASURED and unchanged: of 29 tracked files naming the four-night product, 24 sit
under `datasets/aug09/set-02/qa_work/` alone**, 1 under `aug14/set-05`, and only 4 under
`datasets/corpus/`. So a reader who goes to the corpus home for the canonical's records finds 4 of
29, and the rest are filed under one MEMBER of the combine — a session-level product recorded as a
per-set one. This is the second occurrence of the same defect; the earlier 1760-frame four-set
combine's SPCC record landed under set-03 the same way. `datasets/README.md:59` already reserves the
right destination for exactly this case (`../render_<tag>.json`, beside `experiments.jsonl`), and
the finish stage cannot write one.

**SIZE OF THE FIX, measured so nobody assumes it is a one-liner or a rewrite.** `finish_render.sh`
uses the pair for four things: the judge output path (`:168`, `:214`), and pass-through to
`solve_field.py` (`:191`) and `spcc_run.py` (`:221`), which takes its target positionally. So the
change is a corpus-target path through two scripts, not one — and the input it would need already
exists: `datasets/corpus/recipe.json` is present, so the SPCC spec has a source at the corpus tier.
Nothing here touches pixels; this is record placement and discoverability only.

**Closes when** a cross-set product's finish records write under `datasets/corpus/` (or the
session-level home) without borrowing a member set's directory.

## `frame-qa-order-dependent-scale` — the same data measures differently by run order, and the "solved" figure is itself wrong

`qa_work/frame_metrics.json` prefers the solved plate scale only if the fingerprint already carries
one, so running frame QA BEFORE the mount probe leaves the pooled record on the nominal — 17.5031
nominal against 18.003 from the probe, 2.9% apart. It is self-documented via `pixel_scale_source`
and never re-derived once written. **AMENDED: the 18.003 "solved" figure is ITSELF an artifact** —
all nine stack solves across three sessions read 16.98–17.08 ″/px, so the probe pipeline's
green-plane scale arithmetic inflates by ~5.6% (ledger `solved_scale_artifact_18_vs_17`).

RE-MEASURED, and the population is exactly as described: of the pooled records, **13 carry
`pixel_scale_source = "astrometry.net solve (mount_probe), green-plane scale halved to the full-res
debayered grid"` and 5 carry `"header FOCALLEN/XPIXSZ (nominal)"`** — the order defect recurred on
aug14, which kept the nominal. Per-frame arcsec columns embed the nominal throughout; px figures are
unaffected.

**THE BLAST RADIUS IS CONTAINED, and the item never said so.** The inflated figure does NOT reach
any decision. `fov_deg` — the denominator of the route key `drift_frac` — is derived in
`acquisition.py` from the acquisition record's own scale, and those records carry
`pixel_scale_arcsec: 16.979`, which sits INSIDE the stack-solve range rather than at the probe's
18.003 or the nominal 17.5031. So routing is computed on the correct scale. The auto-cull is also
unaffected: it thresholds robust z on FWHM, background, roundness and star count — px, ADU and
dimensionless, never arcsec. **What is wrong is 13 records' arcsec columns, which are reported and
not consumed.**

A session-level probe would CONTAIN the defect to one measurement instead of seeding it per set
(BACKLOG:`session-level-mount`), so the two items pull the same way.

**Closes when** the scale is re-derived from a direct full-frame solve (or the record refreshed
against the stack solve) and the probe-pipeline arithmetic's error is root-caused.

## `composite-header-identity` — the tuple shipped; the rgbcomp/standard-route half remains

LANDED (`ebbce14`): composites stamp `PIPEREV` = HEAD-at-compose, `CALSET`/`CALFSUM`/`CALDSUM` as MIXED tuples,
`DATE-OBS` = the earliest member start, no `GRPSIZE`/`FILENAME` — `docs/dead-ends/evidence-provenance.md`, "A
PROVENANCE STAMP BUILT AS AN ALLOW-LIST IS A DENY-LIST FOR EVERY KEY IT OMITS"; read back on the canonical, every
key of the tuple equal to what was emitted (`datasets/corpus/piperev_inheritance.json` `readback_canonical`). No
WEIGHT key is stamped — Siril's HISTORY card is the only trace (`docs/dead-ends/siril-behaviors.md`, "WEIGHTED
STACKING PRINTS NO PER-IMAGE WEIGHT"); a weight that becomes a chain choice gets a stamped key (STACKWGT).

**OPEN, and it is an ASYMMETRY BETWEEN THE TWO SUPPORTED WORKFLOWS rather than a loose end.** MEASURED:
`scripts/stack/compose.py` and `scripts/stack/run_pipeline.sh` contain zero occurrences of `PIPEREV` or
`CALSET` — the tuple is ABSENT from them, not false. `run_pipeline.sh` is the STANDARD route, which is where
`route.py:169` sends every TRACKED mount. So today an untracked/fixed-mount product carries a full provenance
stamp and a tracked-mount product carries none, and rgbcomp composites carry none either. Both mount classes
are first-class in this project permanently, so provenance should not depend on which one a set took.
Deciding whether those two routes get the tuple is the owner's; a guard naming the tuple's key set is a build.
**Closes when** both are recorded.

## `set-identity-by-sort-order` — the routing fix landed; ONE glob pick closes here, one remains

FIXED (measured colour-neutral): `run_corpus_combine.sh` and `run_session_chain.sh` derive session/set
from the product's OWN `REGREF`, each with its own loud exit for the two failure modes — REGREF absent
or unparseable (`run_session_chain.sh:129`, `run_corpus_combine.sh:142`) and REGREF naming an unstaged
session (`:171`). `finish_render.sh:88-102` refuses a `--set` that is neither in the composite's
`CALSETS` window nor its registration-reference set, and does so BEFORE any tool runs — that block ends
at `:104` while `solve_field.py` is at `:191`, so the refusal is structural rather than incidental.
Mechanism, the consumer list (the NAME is POLICY) and the header-only signature:
`docs/dead-ends/stacking-compose.md`, "AUTO IS INDEX 0, NOT A RANKING".

**Standards note, recorded because it is a WEAKER deviation than it looks:** IRAF `imcombine`'s
`IMCMBnnn` is the recognised convention for naming a coadd's CONTRIBUTORS, but nothing in the FITS or
drizzle-family conventions standardises WHICH input is a product's registration REFERENCE — that
question has no reserved keyword. Siril follows neither (zero `IMCMB` in its source; it writes
`STACKCNT`, `LIVETIME` and HISTORY). So `REGREF` names a quantity the standards leave unnamed, which
standards-first permits outright. Nothing to convert.

OPEN — exactly TWO `ls … | head -1` picks exist in all of `scripts/`, and only one of them matters:
- **The acquisition-header donor, `run_undistort_pipeline.sh:286` — NEEDS A CHANGE, not a note.**
  `header_capture "$(ls "$P/proc"/pp_c_*.fit | head -1)"` stamps eight keys, and `DATE-OBS` varies per
  frame BY CONSTRUCTION, so the glob choice re-times the record. "Recorded harmless" is unavailable:
  `lens_preflight.check_uniform` asserts uniformity over only camera, lens and focal_mm, so FOCALLEN
  and INSTRUME are guarded while `DATE-OBS`, EXPTIME, APERTURE and ISOSPEED are not. `frame_order.py`
  is the fix and is PROVEN — it is already wired at `run_undistort_groups.sh:125` and measured against
  the wrap corruption (aug09/set-02: 0 of 456 frames in the same position by name and by time) — but
  it is not applied at this site.
- **The starmask pick — CLOSED, recorded harmless, provably.** `render_tier.sh:267` does
  `rm -f "$W"/starmask_*.fit` immediately before the separation, and the pick sits at `:274`, so the
  glob can match at most ONE file per run. `head -1` is order-independent BY CONSTRUCTION rather than
  by luck, and no code change is needed.

The corpus-level record home is BACKLOG:`cross-set-record-home`, not a glob-order question.
**Closes when** the acquisition-header donor is order-independent.

## `spcc-sensor-curve` — the Nikon Z f proxy is pinned; the B/G residual remains

SHIPPED and owner-accepted: the accidental index-0 response model is
retired, "Nikon Z f" is pinned in every canonical `recipe.json`, all 22 products were
re-calibrated as a declared delta, the 17 baselines re-seeded and the 44 `_idx0_` twins
disposed. Every number, the four-proxy comparison and the H0–H4 outcomes:
`datasets/corpus/spcc_pin_zf/pin_record.json` and `docs/spcc-sensor-curve-z6iii.md`
(evidence-classed; §4 the pre-registered test, §5 the untested premises). The headless
name-resolution trap is a `docs/dead-ends/siril-behaviors.md` entry. The proxy's
divergence carries its removal condition in the register.

**The proxy is by dye family, not by die** — Z f / Z6 share Nikon's CFA dyes and
hot-mirror generation with the Z6 III by assumption, measured by no one.

OPEN:
1. The B/G fit's intercept — closed by no proxy (share 0.39–0.44, σ > 0.10 under every
   curve). Suspects, none measured: photometry in a dense 17″/px field (blended stars,
   §4's NULL branch); Gaia XP's BP/RP junction at 640–680 nm and its systematics below
   400 nm (§1.6); the blue edge of the response that no proxy measures on this body.
   **THE STATED DISCRIMINATOR IS CONFOUNDED — "the same pin on a SPARSE field" cannot
   attribute the intercept, and should not be run as written.** MEASURED: the corpus sits in
   the GALACTIC PLANE — converting the pointings gives b = +2.19° (aug06/set-01) and +0.60°
   (the CRVAL cluster), i.e. Cygnus. A sparse field is NECESSARILY a high-|b| field, so the
   swap moves at least three things besides crowding: INTERSTELLAR REDDENING (wavelength-
   dependent, acts directly on a B/G ratio, large and patchy in-plane and near zero at high
   |b| — and it biases in the SAME direction as the hypothesis under test, the worst case);
   STELLAR POPULATION (young reddened disk against bluer metal-poor thick-disk/halo, i.e.
   different intrinsic colours feeding the same fit); and STATISTICAL POWER, which moves the
   wrong way — fewer Gaia XP calibrators raise σ on a fit already at σ > 0.10, so a null
   could mean "underpowered" rather than "not crowding". Four variables at once, against the
   one-knob rule.
   **THE RIGHT-SHAPED REPLACEMENT IS TO VARY CROWDING WITHIN THE EXISTING FIELD — but it is
   NOT cheap on the current wiring, and that is the first thing to settle.** MEASURED:
   `spcc_run.py` never handles a star list — it passes `-catalog=` in (`:388`) and parses
   "aperture photometry to N stars" out of the log (`:449`), so calibrator selection happens
   INSIDE Siril's `spcc` and there is no per-star record to attach a neighbour distance to.
   An isolation cut therefore needs a separate star-list source (a `findstar` pass, or the local
   Gaia catalogue) AND some way to hand SPCC a filtered calibrator set — which Siril may not
   accept at all. **That is a TOOL-CAPABILITY question, not a scripting one, and it gates the
   whole approach.** The shape of the experiment is still right:
   Re-run the same pin on the same stars with an ISOLATION CUT (drop any calibrator with a
   neighbour inside some radius) and compare the intercept against the uncut fit — same field,
   same reddening, same population, same epoch, same optics, same night, so crowding is the
   only thing that moved. If the intercept follows the cut it is crowding; if not, the suspect
   list narrows to the curve. Also unquantified: the reddening confound is
   argued from a measured galactic latitude, not from a dust-map lookup.
   (A body-measured curve, §1.5 B1, is owner-gated and NOT implied by this item.)
2. The upstream MR for the Z f conversion (Apache-2.0 → GPLv3; the database's issue #3
   asks for it) — the owner's call. The Butcher Z6 stays local (CC BY-NC-SA).

**Closes when** the B/G residual has an owner — the sparse-field discriminator run, or
the residual registered as a property of dense fields.
