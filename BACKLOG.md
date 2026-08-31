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

## `removal-conditions` — the register (contract-mandated)

Every divergence from the standard workflow carries a removal condition
(`CLAUDE.md`). **A condition nobody re-checks is a divergence that never ends** —
that has already cost real work: `star_shape_profile.py`'s condition had fired,
nothing re-checked it, and the stale metric invented a false anomaly a whole session
chased. Re-check on a tool version change, on a rig change, and before working any
item below.

**WHAT ACTUALLY STOPS THIS REGISTER RETIRING THINGS — measured, because the obvious
answer is wrong.** It is not that the conditions are too long or too precise. The
shortest condition this register ever carried — *"`astropy` available"*, 19
characters, true on the rig from the day it was written — sat unfired for **five
weeks** and was then found by a dedicated audit, not by being checkable. Meanwhile
the three founding rows still here have SHORTER triggers now than at founding
(`anomaly_audit.py` 60 → 43 chars, `star_shape.py` 79 → 42, GraXpert 39 → 27) and
none has fired. **The variable is EVALUATION, not precision.**
What changed is the POPULATION. Of the founding 12 rows, five were
REIMPLEMENTATIONS — in-house code doing what a tool already did — and **5 of 5
fired, 100%**. Today there are none, because `CLAUDE.md`'s bright line forbids
writing one. What is left is gap-fillers and version waits, which no rewording
retires. **So: shortening a row is housekeeping; the thing that retires a row is
something that EVALUATES it.** Rows read "not fired" almost universally because a
row is DELETED when it fires — that is survivorship, not inertness.

**Rules for this table.**
1. **Every divergence declared in code belongs here.** A `REMOVAL CONDITION:` in a
   docstring with no row is invisible. Add the row in the same commit as the
   divergence. `scripts/qa/check_removal_conditions.sh` enforces this one
   direction — DECLARED-BUT-NO-ROW. It is structurally blind to the worse case, a
   divergence that declares NOTHING (`psf_calib.py` was one); that detector is
   unbuilt. **The divergence column is that guard's JOIN KEY, so every declaring
   file must be NAMED in it** — compressing three sibling scripts to "+3 siblings"
   turned the guard RED on all three, measured while writing this table.
2. **A row records WHAT was measured, never WHEN — no dates in this file; git
   carries the order.** Selftest-green and condition-re-probed are DIFFERENT
   statuses — if a sweep only confirmed `--selftest`, say so.
3. **Status is the current verdict and its evidence, not a history.** Mechanism
   narrative goes to `docs/dead-ends/`, design rationale to the script's own
   docstring, numbers to their record — cite it, do not copy it. No bright-line
   boilerplate: `CLAUDE.md` already says in-house code reads no deliverable pixel,
   and diagnostics are exempt outright.
4. **A condition that depends on the DATA** (disk, sensor size) is re-checked per
   dataset, and says so.
5. **Check the row against the ARTIFACT, never against what you remember it
   contains** — open the file, run the command, `df` the disk. **State the
   DENOMINATOR with any count**, or the next reader's sweep will not reproduce it.
6. **A COMPOUND CONDITION IS TWO CONDITIONS AND MUST BE REPORTED AS TWO.** A row
   reading "X, or Y" can have Y fire while the status reports X — measured twice.
7. **A HEADLINE NUMBER MUST EXIST IN A RECORD.** Before quoting a figure, open the
   record and find it (`docs/dead-ends/verification-traps.md`).
8. **A CONDITION MUST BE EVALUABLE** — "has this fired?" must have a determinate
   answer. Defect shapes: an UNDEFINED TERM (an event nothing in the tree defines);
   a SOFT EDGE (a real event with no threshold).
9. **AND IT MUST BE REACHABLE, WHICH IS A SEPARATE AXIS AND THE ONE THAT PRODUCED
   THIS TABLE'S CLUTTER.** A trigger can be perfectly evaluable and still never
   occur: *"has SWarp shipped a `COVSCALE` card"* is answerable and nobody outside
   this project wants it. **A trigger no external party has an incentive to satisfy
   is MALFORMED** — do not write it as the primary trigger. Give the row a
   `consumer` trigger instead (it retires when the thing that reads it goes away),
   and leave the vendor hope as at most one line in `TOOLS.md`. Rule 8 alone, without
   this, is what produced 224-character conditions that can never fire.
10. **A trigger that is a DECISION TO WORK is not a removal condition** — it is an
    open queue item. Those rows are flagged **BACKLOG** in the class column rather
    than classed, so a register full of them cannot look maintained while nothing
    in it can retire.

**The class column.** `version` — a named upstream feature lands; re-check at a
version bump. `consumer` — retires when the named consumer goes away. `data` — a
data or rig fact settles it. `gap` — no tool provides the mechanism, so the vendor
disjunct is unreachable and the consumer trigger is written as the primary one.
**BACKLOG** — rule 10. A row is not a divergence count: `prebuilt-master ingest` is
a declared NON-divergence kept as a marker.

| class | divergence | retires when | status |
|---|---|---|---|
| gap | `coverage_frame.py` maximal-covered-rectangle over Siril `stat` boxes (+ `verify_framing.py --channel=`, `--regdata-dir=`/`--tag=`) | nothing cites `*_full_coverage.json` (today `datasets/corpus/baseline.json`) | not fired — no tool proposes a rectangle. SWarp answers the canvas half; blocked on a missing `COVSCALE` card |
| version | optics/calibration FITS stamp (`header_provenance_lines`) | darktable gains a FITS **writer** (it reads FITS at 5.4.1) | not fired; the backfill clause FIRED and was executed. Why it exists: the lensfun user DB is global unscoped machine state |
| version | `derive_compose_ref.py` multi-night registration reference | siril picks a sequence reference by a stated order-independent rule | not fired — siril takes INDEX 0 (`stacking-compose.md`). DETERMINISM, not quality; multi-night only |
| version | `compose_preflight.py` + the compose's astrometric post-assert | siril refuses to register a sequence whose members carry no usable solution | not fired — `seqplatesolve` reports nothing when members lack SIP≥2 and ships a finished-looking product (0.458 vs 0.974 roundness) |
| version | `solve_field.py` hint-contradiction gate (exit 9) | the astrometry engine enforces a supplied position/size hint | not fired, and it FIRES on the one measured false solve. Thresholds budgeted from mechanism, not fitted. Census: 268 records / 176 solves / 34 hinted |
| **BACKLOG** | `route.py` `DRIFT_FRAC_MIN = 0.05` | *(not a removal condition — the trigger is an A/B this project must run)* | SELF-GATED. No knee measured; the floor is the smallest excursion at which the term is present, and the 12 sets sit 1.66x above it |
| gap | `anomaly_audit.py` in-house streak kernel | a tool detects/classifies transient streaks | not fired — siril 1.4.4 has cold/hot PIXEL correction only. Standing check: an extreme-elongation QA flag ADJACENT to an audited crossing is the same object until shown otherwise |
| gap | `star_stations.py` fixed-station `findstar` medians | a tool reports a headless LOCAL star-shape map | not fired — `inspector` refuses in a script; `seqtilt` is centre-vs-corners and blind to the drift-aligned band this exists for |
| gap | `shape_at_sky.py` sky-addressed `findstar` medians (combined-product acceptance) | a tool reports headless star-shape statistics for a WCS-addressed subregion | not fired — same gap as `star_stations.py`, at SKY positions. Box placement VERIFIED per run by the tool's own per-star RA/Dec; calibrated against the recorded union A/B |
| data | fitted lensfun entry, PINNED per lens/focal (`lens_models.json`) | an upstream lensfun entry measured for THIS unit at infinity focus | not fired — and RE-INSTATED: the earlier retirement is REVOKED, the per-set method refuted at its root (`TOOLS.md` darktable row). `register -disto=` is a shared-solution facility and does not retire this |
| version | lensfun user-DB strip of the fitted lens's `<vignetting>`/`<tca>` (`install_lens_model.sh`, enforced by `verify_lens_card.py`) | darktable honours a style's lens `op_params` | not fired — the card check runs EVERY set: the strip is machine-local state `lensfun-update-data` reverts, and the two cheaper checks are blind to it (4219 ADU on a 30000 ADU field). Fire-tested both ways |
| data | per-set sky flat (`build_sky_flat.sh`, NOT de-skied) | a matching REAL flat for the set | not fired — the flatless route, and it works (0.40–1.17% corner spread). `sky × V` open; `--desky` is NOT the fix; MAGNITUDE UNMEASURED — the long-quoted 3.11% / 241σ has no record |
| data | `flat_odd_component.py` odd/even decomposition + plane fit over Siril `fdiv`/`stat` | a real flat exists for the set (with `build_sky_flat.sh`), or `sky × V` is measured absent | not fired — the flatless route is the mission and the defect is uncorrected. Load-bearing for `calibration-evidence` and the L/R-is-SKY finding (edge dipole +0.436 → 0 → −0.385) |
| gap | `object_tilt.py` cross-match + weighted LS of magnitude against sensor position (+ `object_tilt_control.py`, `object_tilt_null.sh`, `object_tilt_corpus.py`) | nothing cites `corpus_object_tilt.json` | not fired — UNFILLABLE on this data: SCAMP's photometric solution is one scalar per exposure (`TOOLS.md` Tier 3b). The code survives as the record of that |
| gap | `flat_differential.py` subtraction + line fit (+2 siblings, `--regdata=`/`--nonorm`) | a tool reports the position-dependent photometric RATIO FIELD between two aligned exposures | not fired — no Siril command compares two images photometrically by position; `fdiv`+`stat` is adopted as the primary instrument via `flat_odd_component.py`. MEASURES only. `--regdata=` is not cosmetic: `register -2pass` re-picks the reference and the calibration changes that choice (`scripts/stack/run_undistort_pipeline.sh`) |
| gap | `grid_ramp.py` least-squares plane over Siril `stat` box medians | a tool reports a fitted low-order background ramp as NUMBERS (not a subtracted or model image) | not fired — probed: `bg` is one scalar, `subsky` reports no coefficients, `seqtilt` is star-shape, GraXpert `-bg` and ASTAP `-analyse` report neither. REPORTS ONLY, and the fitted slope is the candidate replacement for four-corner spread; swapping an acceptance measure stays a user ratification |
| gap | `starlight_preservation.py` per-cell floor vs Gaia catalogue regression | a tool reports catalogue-predicted vs measured background AGREEMENT (the joint, not the halves) | not fired. BASIS NOTE: the last sweep confirmed only that `--selftest` passes and did NOT re-probe. MEASURES only |
| data | GraXpert `-correction Division` synthetic flat | a matching real flat exists | not fired — not adopted; no pipeline script calls it. Vignetting-only fallback |
| gap | `baseline_guard.py` corner spread + edge dipole over Siril `stat` | a tool reports a headless PRODUCT-level regression verdict against a stored reference | not fired. A no-regression RECORD, never a quality gate; last in `run_set_chain.sh`, a regression exits 8. Owner rules: centre-median ADVISORY on a `STACKNRM` mismatch; corner ceiling warns on a CROSSING only. Blind to `sky × V` |
| gap | `fingerprint.py` derived trail/drift geometry | a tool reports headless trail/drift geometry with a declared-vs-measured mount cross-check | not fired. BASIS NOTE: the last sweep confirmed only `--selftest`, not the tool landscape. No solver exposes inter-epoch drift rate vs sidereal |
| gap | `inspect_stage.py` + `cull_report.py` robust-z per-frame flagging | a tool ships headless per-frame outlier flagging over its own registration metrics | not fired — siril has `seqstat` and `select`/`unselect`, no outlier GRADING over its regdata. Persisting the tool's regdata is not a divergence and stays regardless |
| — | prebuilt-master ingest (`run_pipeline.sh` `<session>/calib/`) | *(not a divergence — an accepted input class; it cannot fire and must not be counted)* | STATED LIMIT: such masters carry no exposure/gain/filter headers, so the filename token is the whole identity and the exposure match is unverifiable — printed per run |
| **BACKLOG** | 16-bit in `coverage_probe.sh`, `run_frame_qa.sh`, `fit_lens_model.sh`, `run_lunar_pipeline.sh` | *(the trigger is a design change this project must make)* | each re-verified; exemptions enforced by name in `check_bitdepth.sh`, which reports FOUR |
| **BACKLOG** | `run_undistort_groups.sh` group composition (one extra interpolation pass) | *(the trigger is an A/B this project must run; the combine-unit disjunct is a consumer gate on `final-best-percent-pass`)* | SELF-GATED. Second disjunct half-satisfied toward KEEPING groups (the canonical is a 77-member four-night compose). Single-pass deletes the sub-stacks the combine composes, so disk cannot retire it. Peak: `W × H × ch × 4 × 2` |
| version | `scripts/lib/siril_run.{sh,py}` flock-serialized siril-cli invoker | flatpak fixes the instance-dir lifecycle race | not fired — unfixed at 1.4.4, and every builder still spawns one siril-cli per step. The lock is per-USER, so it serializes across sessions. No exemption remains in `check_siril_invoke.sh` |
| version | `scripts/lib/siril_run.sh` bounded LAUNCH retry (`SIRIL_LAUNCH_TRIES`, default 4) | this rig completes a full-session build at `SIRIL_LAUNCH_TRIES=1` with no launch failure in any siril log | not fired — measured here, TRIGGER UNIDENTIFIED (the concurrency hypothesis is refuted). Discriminated on Siril's config-ini mtime because both failure branches exit 1; all four branches live-tested (`scripts/lib/siril_run.sh`) |
| version | `scripts/stack/stamp_headers.sh` capture + `update_key` restore of the keys the warp drops | darktable gains a FITS **writer** | not fired — the blocker is the WRITE side ALONE, and this governs the shared clause wherever it appears. LIVETIME is the one derived value (n_frames × EXPTIME) because per-frame EXPTIME was destroyed upstream |
| gap | `check_solve_records.py` record-vs-artifact pointing join | a tool joins a solve record's stated solution to the WCS of the file it names | not fired — astrometry.net validates against an IMAGE, not our records. It compares against the WCS AT THE CENTRE PIXEL, never `CRVAL` (BACKLOG:`pointing-record-names-the-wrong-frame`) |
| consumer | `scripts/darktable/cp_coverage.py` control-point radial-coverage analysis | nothing imports it (today `fit_lens_model.sh`) | not fired. Its CLI corner-support gate-exit has NO caller, so the exit-1 path is dead in practice and the analysis is promote-path evidence |
| version | `scripts/calibrate/spcc_cone.py` nside=2 nested ang2pix cover | siril 1.5 ships `healpix` and its pixel list matches the zenodo chunk names, or `astropy_healpix` reaches host python3 | not fired. Clause (b), `_tan_pix2sky`, FIRED and was executed: deleted for astropy WCS from the CD alone. Bound: chunk SELECTION only — siril names any missing chunk loudly |
| version | `scripts/stack/lens_preflight.py` pinned-model XML scan (literal a/b/c for the exact lens@focal) | lensfun/darktable expose a headless query of the installed model's coefficients | not fired — Debian ships no lensfun query CLI (`TOOLS.md` darktable row) |
| version | `scripts/calibrate/solve_field.py` coverage rescue rung | the astrometry.net engine accepts a detection-region constraint | not fired. A GENERAL SAFETY NET, not the fix for the corpus starvation; fires only on NO SOLUTION or floor-class, keeps the strictly better result |
| version | `run_undistort_compose.sh` + `run_undistort_groups.sh` + `run_undistort_pipeline.sh` stack without `-output_norm` + the normalization-anchor stamp (`ANC*`, `STACKNRM`, `REGREF*`) | Siril offers a reference-anchored (or per-channel, non-min-max) output normalization | not fired — a deviation TOWARD the linear-photometric standard; basis `stacking-compose.md`'s `-output_norm` entry (item CLOSED, owner-accepted). The post-assert greps Siril's own wording and exits 4 otherwise |
| version | `scripts/calibrate/spcc_run.py` `spcc_list oscsensor` preload + log-order assertion + database preflight | Siril loads SPCC metadata before resolving names in `do_pcc`; re-check every version bump | not fired — mechanism and the H0 probe: `siril-behaviors.md` (a spec-less headless run resolves to index 0 of each list). Record `spcc_h0_probe.json` |
| data | the **Nikon Z f proxy response** (`convert_curves.py` + `fetch_sources.sh`, pinned by every canonical `recipe.json`) | a curve measured on THIS body, or an upstream "Nikon Z6 III" `OSC_SENSOR` entry; re-check on every database-clone update | not fired — a proxy by dye family, not by die, measured by no one. Pinned on the owner's H4 approval; all 22 canonical products re-calibrated. Records: `datasets/corpus/spcc_pin_zf/pin_record.json` |
| version | `run_member_crop.sh` + `member_profile.py` (the corpus combine's MEMBER-SELECTION stage) | Siril's compose accepts per-member weight maps or a region mask | not fired — IN THE CHAIN; the corpus canonical is built under it. Every constant lives in `datasets/corpus/recipe.json`, never a script default. SCOPE: CORPUS-ONLY, measured (`stacking-compose.md`). Stage: `docs/corner-smear-member-selection.md` |
| version | `scripts/qa/check_site_privacy.py` observing-site guard | an off-the-shelf secret scanner carries a rule for this site AND the `site` block schema has no numeric key | not fired — in `run_guards` and the pre-push hook; a records guard, never a gate on a product. Limits: no local config → literal scan SKIPPED aloud; tree and index only, never history; an underived form is outside its scan (`evidence-provenance.md`) |

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
standard route stamps none of the three — measured 0 occurrences against 10 in
`run_undistort_compose.sh`; `docs/combine-contract.md`:179,
BACKLOG:`composite-header-identity`'s open (e)), guard advisory under the STACKNRM change; one
product, pre-registered as the undistort tiers were. Removal condition: the same as the undistort
rows' (Siril offering a reference-anchored output normalization).
**Closes when** the standard route ships without `-output_norm` on a measured product, or
records why it must keep it.

## `pending-owner` — decisions with the owner, and the input they ordered gathered

UNCHECKED, logged not discharged: *"self-picked targets outperformed assigned ones"* — no counterfactual measured,
it flatters both parties; the competing explanation is SEQUENCING (rule adopted: assign the first unit, then release).

1. **Whether `BACKLOG.md` and `docs/dead-ends.md` remain TWO files — held by the owner, NOT DECIDED**
   (removing the registry is one option under consideration). Consequence meanwhile: do not RESTRUCTURE the
   registry internally (effort that may dissolve); deleting entries whose test is solved and no longer valuable
   survives either outcome — prefer the operation robust to the ruling.

Owner rulings kept here because the quote is the record:
- **The per-member trim — RULED, RAN, REFUTED; no trim ships.** Owner, verbatim: trim *"each side by
  about 5% ... so the worse part of each image never makes it into the stack"*, and the mechanism, verbatim: *"the
  stars being stacked are the worse images possible"*. Outcome, numbers and ledgers:
  `docs/dead-ends/stacking-compose.md`, "PRE-REGISTRATION FRAME-WIDTH CROPPING (the retired `--crop-lr` knob)". The
  open half — properly centred frames — is acquisition-side, not a route this repo takes (MEMORY: the data is a given).
- **Recorded elsewhere, pointers kept because nothing else carries them:** the L1 judge triple and starlight
  preservation as a logged UNCHECKED premise that blocks nothing — `datasets/aug06/l1_work/owner_ratification.json`,
  `datasets/aug06/l1_work/unchecked_premises.json`.

**Closes when** the owner rules on the two-file question.

---

## `compose-homography-smear` — the smear is CLOSED by member selection; the reprojection route and the model questions stay open

CLOSED, homed: the union's band and corners are member-borne, in the photons, night-ordered —
`docs/dead-ends/stacking-compose.md`, "THE UNION'S LEFT-BAND / BOTTOM-CORNER SMEAR IS NOT A
REGISTRATION OR COMPOSE DEFECT" and "THE SUB-STACK COMPOSE IS A MOSAIC, NOT A STACK" (the
astrometric compose is the shipped route, owner-PASSED); the decision map
`docs/corner-smear-member-selection.md` (cropT owner-approved, §5); the attribution
records `datasets/aug09/smear_work/{smear_remarch,rho_march,rho_march_prereg}.json`; the blanket
trim (owner-directed, RAN, REFUTED — BACKLOG:`pending-owner`;
`docs/dead-ends/stacking-compose.md`, "PRE-REGISTRATION FRAME-WIDTH CROPPING (the retired
`--crop-lr` knob)"). Geometry: `docs/dead-ends/registration-distortion.md`, "FITTING A LENS MODEL
AGAINST A PLATE SOLUTION WITH AN AFFINE NUISANCE" (a centred ptlens model fits to a 0.27 px median;
the `<center>` entry beside it). Optics: `docs/dead-ends/star-shape-optics.md`, "THE ONE-SIDED
STAR-SHAPE GRADIENT IS IN THE OPTICS-AND-PHOTONS OF A SINGLE EXPOSURE". The drift arithmetic:
`docs/untracked-widefield-standards.md` §H.4. The SCAMP/SWarp facts and defaults: `TOOLS.md`, the
SCAMP and SWarp rows. The canvas-x trap: `docs/dead-ends/measurement-discipline.md`.

OPEN — each settled at the COMBINE, one knob, or withdrawn with its reason:
1. The SCAMP/SWarp TPV reprojection as a COADD against the shipped `seqplatesolve` compose — U
   (no defect motivates it now).
2. Interleaved rather than consecutive groups — D (stations + the dwell-floor / rejection
   denominators); a trade, not a free win.
3. A corner-true shared model — N: no fit constrains past ρ 1.47–1.51 against a corner at 1.80
   (`docs/combine-contract.md`; `docs/dead-ends/registration-distortion.md`, "CORNER CONTROL POINTS
   CANNOT BE RECOVERED BY REORDERING OR RELAXING").
4. Which single model — the pinned july14 fit or a fresh fit — D; the corner-supported candidate
   a,b,c (ledger `ptlens_joint_refit_free_centre`) judged at the combine on star_stations + seqtilt,
   then the owner's eyes (U).
5. A state-CHANGE detector with a RELATIVE trigger — D once the member-separation quantity is
   attributed (`docs/combine-contract.md` §5).

**Closes when** 1–5 are each measured at the combine or withdrawn.

## `intake-culling` — one measured intake pass, one visible formula

USER-DIRECTED. More photons are always obtainable; a bad frame stacked is permanent. Every recurring defect has a
signature measurable per frame at intake: measure ONCE, score by a formula whose constants are visible and
adjustable, report per frame with its reason. **The decision FORM is a THRESHOLD, not a rank or a percentile**
(owner-ratified — BACKLOG:`final-best-percent-pass`: a rank rule cuts N% from an equal-quality corpus
for nothing). The shipped auto-cull already conforms — `cull_report.py` flags on robust z vs the pooled
median/MAD, defect side only — so this is the form to extend, not to choose.

Standards-first: a SEARCHED NEGATIVE — no vendor publishes a default combining expression for per-frame quality
signatures (the community 15/15/20 weighting has underivable constants; the PixInsight source returned 403, so that
provenance is UNVERIFIED), so a visible in-house formula IS the standards-compliant choice, not a deviation.

| signature | what measures it | status |
|---|---|---|
| aircraft / satellite / bug | streak geometry | BUILT — `anomaly_audit.py` |
| shake / wind gust | per-frame FWHM + roundness spike; elongation angle off the trail axis | THE ANGLE TEST EXISTS AND FIRES on 2 of 21 frames, both the first exposure of a night (aug06/set-01 block 1: θ₀ 19.75° off the rest of the set while its own drift bearing departs 0.150° against a 0.062° SE — in the EXPOSURE, not the tracking or the sky; reproduces across detection depth and on july31/set-01 frame 1, −19.5°): `datasets/aug06/corner_work/drift_bearing.json`, commit `b512419`; mechanism `docs/dead-ends/star-shape-optics.md`, "ON A FIXED CAMERA THE STAR-DRIFT DIRECTION DOES NOT ROTATE". Still needed for adoption: a per-FRAME form (this is per-block) and a decision on whether one frame is worth culling |
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
  is REFUTED: BACKLOG:`pending-owner`). Adoption still gates on preserving the frame-filling UNRESOLVED STARLIGHT
  (degree 1 only; `docs/dead-ends/terminology-dust.md`, sense 2 — it is stars, not dust).
- **L2 denoise strength** — the proven chroma killer. Objective instrument is the `noise_split.sh` structured term,
  never whole-frame `bgnoise`. Cosmic Clarity's chroma knob saturates above 0.85 and no record says which
  `--denoise_mode` that was measured under — the OPEN probe, with the positive control it needs, is `TOOLS.md`'s
  Cosmic Clarity Denoise row; not duplicated here.
- **L3 stretch ladder** — GHS/`ght` arms against the current `mtf`, compared at a
  MATCHED background landing so curve shape is the knob, not brightness.
- **L4 thresholded `satu`.**
- **Riders:** seed `datasets/GENERIC.json` (still the `{"render": {}, "why": {}}`
  stub) with the six current knobs and a per-knob class-risk note; per-arm output
  tree (`web/results/<session>/exp_<param>_<stamp>/`) and the `<final>_stages/`
  labeled sequence, both binding requirements the tier does not yet emit;
  `judgment_package.py` re-wire (its `.metrics.json` producer — the old chain's
  renderer — no longer exists; the PNG16-only surface is already enforced).
- **Two known limits:** a set can carry only ONE ratified `render` block (keyed by
  name), so two kept looks are not expressible; and a mono set STOPS loudly — the
  luminance-only variant is unbuilt.

One knob per arm, hypothesis pre-registered, judged on full-frame lossless PNG16.
**Closes when** an approved, re-baselined render comes out of a laddered arm.

## `calibration-evidence` — three live threads; the rest is closed and lives in the registry

OPEN DEFECT, mechanism homed: a sky flat converges to `sky × V`, so the object carries the sky's spatial
profile — `docs/dead-ends/calibration-flats.md`: "A SKY FLAT BAKES IN ANY SKY GRADIENT THAT IS FIXED IN THE
ALT-AZ FRAME"; "DEAD END — `--desky`" (a 31× regression, reverted); "THE FLAT'S SHAPE DIFFERENCE REACHES THE
DELIVERED OBJECT ESSENTIALLY 1:1" (the differential delivers the transfer function, not the LEVEL); "A
FOUR-CORNER BOX METRIC IS NOT A GRADIENT MEASURE ON A STRUCTURED FIELD".

OPEN:
1. The with/without judgement pair on finals — U, blocked on BACKLOG:`render-ladder` (`render_tier.sh` exits 7
   without a ratified `render` block). The difference is MEASURED at −22.5 % of object flux; which arm preserves
   unresolved starlight is the owner's eyes. The arms' FITS were freed (`datasets/corpus/rig_cleanup_record.json`),
   the records are `datasets/aug09/set-05/flatdiff_work/*.json`, and rebuilding the production-normalization pair
   `arm_{An,Bn}.fit` (skyflat_set-05 vs skyflat_set-01, 125 frames each, registration pinned — the pair to judge)
   is part of the cost.
2. `build_sky_flat.sh`'s corner-vs-centre gate is self-fulfilling for this defect and under-claims (it records both
   edge dipoles beside it); the candidate replacement `scripts/qa/grid_ramp.py` fits the ramp as coefficients —
   swapping an acceptance measure is a USER RATIFICATION (U): a proposal to the owner, not a change to make.
3. SPCC order-robustness — D: a background step ahead of SPCC moved K_G −1.20 %/−1.48 % and K_B −0.47 %/−0.80 %
   on unchanged star counts (chain K scatter 0.006), confounded by the de-skied arm's real ~3 % object tilt
   (`datasets/aug06/set-03/qa_work/spcc_set-03_set-01+02+03_full{,_subsky1}.json`); the clean test is the SAME
   stack with and without an on-stack background step only.

**Closes when** the pair is judged, the gate is replaced by ratification or re-described, and SPCC
order-robustness is measured on one knob.

## `walking-noise` — WATCHLIST (class-gated): open gap

Faint DRIFT-ALIGNED streaks visible at native 1:1 and below whole-frame statistics: a
sensor-fixed pattern (readout FPN + residual warm pixels) dragged into lines by
coherent un-dithered drift. Rejection and cosmetic correction both measured NULL —
it is sub-sigma STRUCTURED signal, not discrete outliers. First quantification
(`noise_split.sh`): drift-phase term ≈0.34/0.48/0.42 ADU (R/G/B) per ~199-frame half,
against ≈1.0/1.5/1.2 ADU total static structure.

One measured CONTRIBUTOR is gone at the source: 16-bit master darks stored a
sensor-fixed ±0.5 ADU pattern subtracted into every light (0.2889 ADU RMS against a
0.4213 floor, +21%), fixed chain-wide and enforced by `check_bitdepth.sh`. **Do NOT
count that as a measured reduction** — the stack-level A/B cannot resolve it (the
chain's run-to-run variation is ~10× the effect). Whether the streaks shrank needs
`noise_split.sh` on a group-built pair.

**Gated on the class recurring** (an un-dithered untracked set; dithering is the
acquisition-side fix and removes the driver). First-contact levers: matched
shutter-mode darks; then drift-axis-aligned pattern removal or an AI denoiser weighed
against preservation of the unresolved starlight — a bandaid, last resort.


## `native-solve-and-sip` — one probe left

- **`platesolve -localasnet` on the mildly-trailed class** — D: one stack, one probe, either verdict recorded. The
  dead end was measured at roundness 0.615 (`docs/dead-ends/plate-solving-wcs.md`, "Siril's internal solver fails
  ultra-wide TRAILED fields" — `-localasnet` still feeds Siril's own `findstar` detection); the class is on the rig
  (set-01 roundness medians 0.786–0.852, `qa_work/frame_metrics.json`; july27/set-01 at 0.786 substitutes for the
  departed july23's 0.80). A pass gives `solve_field.py` a native sibling for this class, the external route staying
  for heavily-trailed data; the bracket is `docs/x86-empirical-test-plan.md`, Phase 3.
- `register -disto=master` — UNDETERMINED: the probe is specified in `docs/dead-ends/registration-distortion.md`, "A
  STANDALONE PER-MEMBER SIP WARP, APPLIED OUTSIDE SIRIL'S REGISTRATION, IS WORSE THAN THE SHIPPED ROUTE". The
  SCAMP/SWarp successor is BACKLOG:`compose-homography-smear`.

## `one-sided-band` — one unattributed radial term

CLOSED, homed: the term is in single raws and no chain stage causes it —
`docs/dead-ends/star-shape-optics.md`, "THE ONE-SIDED STAR-SHAPE GRADIENT IS IN THE
OPTICS-AND-PHOTONS OF A SINGLE EXPOSURE", "THE THREE-LEVEL SEPARATOR", "ON A RECTILINEAR LENS
THE PLATE SCALE IS NOT ONE NUMBER" (18 % to the gnomonic scale; the remainder at 5.9 SE), "AN
ELLIPTICITY EXPONENT IS NOT A BLUR EXPONENT", and "THE ONE-SIDED RADIAL TERM'S CANDIDATE
FAMILIES AND THEIR DISCRIMINATORS ARE DOCTRINE" (the table, the astigmatism × defocus falsifier,
the altitude bound, the centre commensurability); the union's band → BACKLOG:`compose-homography-smear`.
Records: `datasets/aug06/corner_work/` — `coherent_trail_bins.json` (trail ratio 0.3502, the
predicted ZP deficit 0.570), `phot_work/zero_point.json` (the structural degeneracy),
`cfa_control.json` (the CFA-axis arm, non-attributing by pre-declared design), `pa_convention.json`;
ledger `corner_radial_term_family_and_centre`.

OPEN:
1. The residual RADIAL term's family — N: coma-consistent, astigmatism not reached, the
   radial↔tangential sign flip absent; no installed instrument separates them here.
2. Unrun discriminators — D: per-Bayer-channel ellipticity (greens identified FROM THE DATA,
   `TOOLS.md`); whether the ±2400 FWHM asymmetry (night-ordered per-set medians −0.070 … +0.472 px,
   `datasets/corpus/member_selection/july31+aug06+aug09+aug14_full_portion.json`) is the odd
   ELLIPTICITY term — a per-set roundness asymmetry from `datasets/corpus/member_selection/profiles.json`
   `top30_round`, no new run. Cross-session altitude (atmospheric / gravity) — N, the lever
   unquantified at 63–88°.

**Closes when** the residual radial term is attributed, or a route ships that holds the corner at
the clean band's star shape on the owner's eyes (U).

## `pointing-record-names-the-wrong-frame` — two header fields that are not the pointing

Two independent traps, both MEASURED, both of which have already misled a session
each. Neither corrupts a shipped product — nothing on the build path consumes
either quantity as a pointing — but both are silent and both invite the same
mistake.

**1. `fingerprint.field_center` is the FIRST FRAME's solve, not the set's
pointing.** MEASURED: it equals `mount_probe.json`'s `solve_a` to machine
precision in all three sets checked, and the probe's window is the FIRST frame of
the longest contiguous capture run. A fixed mount sweeps RA through the set, so
the field's RA at the set MIDPOINT is higher — and the record is therefore
systematically LOW by about half a set span:

| set | first (`field_center`) | midpoint | authoritative (`OBJCTRA`) | first − auth | mid − auth |
|---|---|---|---|---|---|
| aug06/set-01 | 302.945 | 306.054 | 306.653 | **−3.708** | −0.599 |
| aug09/set-01 | 306.727 | 309.840 | 309.703 | **−2.977** | +0.136 |
| july31/set-01 | 308.558 | 312.399 | 312.856 | **−4.298** | −0.457 |

Always negative, never positive, and about half the 6.22 / 6.23 / 7.68° RA span
each set sweeps. The NAME is what causes the error — "field_center" reads as the
field's centre. **Consumers: none on the build path** (grep finds only
`fingerprint.py` itself and `verify_site.py`), so this is a naming/semantics
defect rather than a corrupted product. It has nonetheless misled two readers in
one session, including this manager.

**2. `CRVAL1/2` is the WCS TANGENT POINT and on these solves it is nowhere near
the pointing.** MEASURED across 13 products: **CRPIX sits 40–960 px from the
image centre**, and **CRVAL REPEATS across different sets and different nights** —
five discrete values serve all 13 products (306.62/42.00 covers july31/set-02,
aug06/set-03 and aug09/set-03; 310.62/43.24 covers aug06/set-02, aug09/set-01,
aug09/set-05 and july31/set-04). A quantity that repeats across unrelated
pointings is not a pointing. Reading it as one costs up to **3°**.

**What IS authoritative: the full solution evaluated at the central pixel**, which
is the pointing by construction — and `OBJCTRA`/`OBJCTDEC` reproduces it to
0.000–0.031° on 7 of 9 products (0.13–0.18° on the other two). Use `OBJCTRA`, or
evaluate the WCS at the centre; never `CRVAL`, never `field_center`.

**Closes when** `field_center` is either renamed to what it is
(`first_frame_center`) or computed as the set's actual pointing, and the two
`docs/`+`BACKLOG` sites that cite a "solved centre" name which one they mean.

## `corner-fix-landscape` — procurement or acceptance

Rule: every candidate is FIX / TRADE / BANDAID before it is listed; a trade or a concealment never
shares a list with a fix. CLOSED, homed: no route on this rig RECOVERS corner detail — a single
global PSF cannot (no field-constant trail scale on three grids:
`datasets/aug06/corner_work/{constancy_fit,frame_depth,cfa_control}.json`);
`docs/dead-ends/separation-deconv-psf.md`, "NO INSTALLED TOOL DELIVERS A FIELD-VARIABLE ANISOTROPIC
PSF CORRECTION" (per-region tiling is pixel surgery, FORBIDDEN) and "PSF HOMOGENISATION — REFUSED BY
THE OWNER" (zone down-weighting is the same act); the blanket trim (owner-directed, RAN,
REFUTED — BACKLOG:`pending-owner`). The FIX-class route that shipped is member SELECTION (cropT,
owner-approved; `docs/corner-smear-member-selection.md`); what it cannot remove is the
lens's SYMMETRIC radial softening, and this item is about THAT. The procurement facts:
`TOOLS.md`, Tier 5, the anisotropic row.

OPEN:
1. Procurement — N: `torchmfbd` (three documentation checks decide it), `pyimcom` (a survey
   OBSFILE schema and no bring-your-own-data path — weeks and a fork; `furry-parakeet`'s kernels
   the one cheap probe); `galsim.des.DES_PSFEx` is installed for PSF evaluation — also the only route to
   the OBJECT-detail question: a symmetric sharpener cannot de-trail an elongated PSF, classical RL is a
   measured dead end on in-exposure trailing, and Cosmic Clarity's non-stellar sharpen is ATTENDED-only with
   its CLI ignored (`TOOLS.md`, Tier 5).
2. `-noclamp` — a TRADE, U after D: the cost is measured (BACKLOG:`resample-cost-and-drizzle`),
   the ringing it prevents is not — the planted fixture with a sharp-edge target closes it.

**Closes when** an anisotropic treatment is procured and measured, or the owner accepts the
corner as-is (U).

## `resample-cost-and-drizzle` — the clamp is the resample cost, and it is a pinned trade

MEASURED (ledger `datasets/aug06/experiments.jsonl`: `resample_cost_arm_d_siril_pass`, `resample_cost_series_run`,
`resample_cost_arm_d_COMPLETE` — the LAST entry of each id): the clamped Lanczos4 pass costs ~6 % of PSF width and
the CLAMP is essentially all of it (kernel 0.45 %, nearest control exactly 0.00 %), ~12 % over the chain with the
darktable warp — quote ~6 %/~12 %, never three figures; ONE FWHM (2.10 px) and ONE phase set were planted, so the
fractional-phase spread and the FWHM dependence are unmeasured (`docs/dead-ends/separation-deconv-psf.md`, "PSF
HOMOGENISATION — REFUSED BY THE OWNER", the clamp clause). The clamp is a PIN and a TRADE
(`scripts/stack/check_registration_pins.sh`: *"clamping is the DEFAULT this repo keeps (lanczos4 rings on stars)"*;
ringing is judged, blur is measured); `-noclamp` is BACKLOG:`corner-fix-landscape` item 2, not restated here.

OPEN:
1. The planted arm across a spread of sub-pixel phases and ≥ 2 planted FWHM, reported as a range — D.
2. Whether ~1.4–1.9 px of trail on a 2.0–2.4 px PSF disqualifies drizzle — D/N, judged by minor-axis FWHM
   (`docs/dead-ends/stacking-compose.md`, the drizzle rule). Measured blockers: `seqapplyreg -drizzle` refuses a
   debayered RGB sequence (ledger `two_probes_drizzle_input_and_otf_zeros`), and Bayer drizzle needs UNDEBAYERED
   input while the undistort stage runs debayered (ledger `resample_cost_arm_d_siril_pass`); `split_cfa`'s mono
   green plane is the one path the refusal does not name — unprobed.

**Closes when** 1 reports a range and 2 is decided against the measured number rather than the category.

## `star-neutral-colour` — WATCHLIST (needs a narrowband corpus): the narrowband gap

SPCC-narrowband equalises O3=Ha and erases the O3 sphere; Siril has no single command
for a star-colour-neutral balance. Headless path identified and the tool half
confirmed on 1.4.4: measure mean star colour in the examine layer → apply a diagonal
`ccm`. UNTESTED design — do not cite as a method. Run it against a bracket (SPCC,
Nightlight) when a narrowband corpus arrives.

## `siril-1.5` — WATCHLIST (fires on a version bump): one load-bearing migration risk

1.4.4 is current stable; 1.5.0 is dev master. The trigger is a version bump, not the
rig (already x86).

- **RISK, now load-bearing: `starnet`/`seqstarnet` are REMOVED in 1.5.0-dev**,
  consolidated behind `pyscript StarNet.py`. `render_tier.sh` calls `starnet`, so a
  1.5 bump breaks the shipped render tier. Migrate before bumping.
- **Adopt on 1.5:** the native `mask_*` subsystem plus `-mask` on
  `denoise`/`rmgreen`/`epf`/`rl`/`sb`/`wiener` — the first native path to
  region-confined ops without a hand-rolled blend.
- **Retirement candidates:** `healpix` (lists the NESTED pixels overlapping a solved
  image — what `spcc_cone.py` hand-rolls; needs a check that its list maps to the
  zenodo chunk names) and `eqcrop ra1 dec1 ra2 dec2` (the natural consumer of a
  framing record's RA/Dec form).

## `final-best-percent-pass` — one target, many sessions: the FINAL pass selects by measured quality — thresholds, not a percentile

The standing multi-session practice's endgame (user-ratified): after many
~500-frame sets accumulate on one target, a FINAL pass re-selects from ALL
sessions' data. The owner's ruling fixes its FORM: a best-N% ladder is
a RANK rule and on an equal-quality corpus would drop N% for nothing ("consider
what happens if ALL the images were to be the same quality … should we have cut off
thresholds opposed to blanket cut rules?"), so the pass selects by QUALITY
THRESHOLDS that exclude nothing on an equal corpus. MEASURED at the MEMBER tier on
the 77-member four-night corpus (the corpus gate has fired): a PORTION threshold
(crop a member's entry-side columns beyond the onset where FWHM(+dx) − FWHM(−dx)
> 0.20 px — `cropT`, owner-approved) carries the gain, band 2.97 → 2.79 px at full
depth; a FRAME threshold (exclude a member whose interior+exit-side FWHM exceeds
the corpus's 25th percentile by > 0.20 px) is a NULL on top of it at −16.2 % of the
frames — reported, not gated (`docs/corner-smear-member-selection.md`). **SHIPPED
at the MEMBER tier:** the portion threshold is the chain for the corpus combine
(`run_corpus_combine.sh --portion-rule` → `run_member_crop.sh`; the canonical
corpus is built under it, 0 differing pixels from the owner-approved candidate;
guarded by `datasets/corpus/baseline.json`; the selection recorded per member in
`datasets/corpus/member_selection/<tag>_portion.json`). Unbuilt: the per-FRAME
cross-session quality surface (per-set `frame_metrics.json` exists; nothing ranks
or thresholds across sessions; `cullspec` excludes are per-set) — the same surface
BACKLOG:`intake-culling` is designing at intake, and its threshold form is this
ruling's. Selection is
adopted only through a measured arm with a pre-registered prediction, never as a
default.
**Closes when** the per-FRAME surface ships the same way — a final-pass product
from measured THRESHOLD selection at the frame tier across at least two sessions'
data, with its per-set selection recorded.

## `session-level-mount` — one tripod pays for up to four probes

`mount` is modelled PER SET while it is a session-level fact: one tripod on one
night still pays for a drift probe per set. **Closes when** a decisive
session-level measurement seeds every sibling set's record (provenance kept per
set — a re-aimed set still cross-checks).

## `per-group-flat-at-the-combine` — WATCHLIST (owner-PAUSED pending real flats): the trade is only decidable at the combine unit

**PAUSED BY THE OWNER pending real flats** — the flat-residual research line is
on hold until real flats exist to compare actual frames against the current
synthetic masters. This is an owner decision about sequencing, NOT a
recommendation from this repo to acquire them: the synthetic-flat route stays
the mission and "a real flat" remains the divergence's removal CONDITION.
Do not pick this item up before that comparison exists.

The per-group flat measurement is CLOSED at the per-set deliverable: composed
object tilt **+0.055% ± 0.083%, 0.7σ over 1217 stars** — indistinguishable from
zero, because the set flat already IS the mean of the group flats, so a
plain-mean compose cannot tell them apart (cancellation measured 75–94%, refined
from the flat-side sensor-frame arithmetic by the drift and the `-framing=min`
crop). What per-group flats change is the MEMBER: transfer 1:1, object tilt
moving 0.36–2.13% in x at 4.3–21.3σ, backgrounds 28–40× more consistent
member-to-member (recorded as the mechanism's SIZE, never as evidence of better
calibration — that is the self-fulfilling direction), and a COST of 3.271% (x) /
4.335% (y) member-to-member object-imprint disagreement where the shipped route
has exactly zero.

**Why this is not optional to resolve.** The member is the cross-night COMBINE
unit, and MEMORY's binding rule is that every calibration/model/route change is
evaluated against the COMBINE unit, not just per-set products — measured twice
already, per-set models smearing cross-set unions. A per-set verdict on a
member-level trade is therefore an incomplete verdict, and the sign of the trade
can invert at the combine: member imprints that cancel within one set need not
cancel across nights whose skies differ.

**Closes when** a combine-level A/B, one knob (the flat window), members from
both arms, is judged at the combine — the level where the disagreement either
averages away or compounds. No instrument here can say which member calibration
is closer to truth, so anything the data cannot settle goes to the owner under
the evidence gate. Numbers and the full trade:
`datasets/july31/set-03/pergroup_work/pergroup_flat_report.json`,
`docs/dead-ends.md`.


## `lunar-ladder` — WATCHLIST (needs the next lunar capture + a PSS venv): x86 ladder remains

**STATE: the first corpus is processed end to end and the chain is codified as
`scripts/stack/run_lunar_pipeline.sh`** (PROVISIONAL as-written — its first
fresh run is the next lunar corpus). Both sets' finals are user-ratified:
sb deconvolution + per-set disc-neutral WB (satu closed-fail; wiener arm
PAUSED on user order — equal on-disc, frame-edge artifact noted). Session raws, stacks and judge
surfaces are freed and re-stageable; every mechanism is in `docs/lunar-lucky-imaging.md`.

**Remains open:**
- **The x86 quality ladder** (best 10/15/20/25% vs the shipped q100 controls,
  PSS `--stack_percent` or AS!4 — pre-registered in both sets' ledgers).
  Needs: PSS venv on the x86 rig + re-staged data (NEFs from archive, replay
  `run_lunar_pipeline.sh` stages, or transfer nothing and re-shoot better).
- **Next lunar capture at the corrected card** (acquisition checklist lunar
  block: disc histogram 50–70% — f/4 · 1/320 s · ISO 800 at 70 mm class) —
  more photons beat every processing knob measured this corpus.
- **Siril 1.5 MPP adoption test** (unchanged — retires the GUI step when
  stable lands and it measures quality).
- Long-focal escalation ladder (unchanged, dormant until such a corpus):
  AS!4-under-Wine vs PSS vs 1.5-MPP head-to-head; waveSharp 3.0 (native
  Linux GUI, frozen) / ImPPG 2.1.0 as judgment-quality finishers; Hugin for
  mosaics; RGB-align only where dispersion is measured (≥ ~800 mm).

Class facts, records and the full mechanism set live in
[`docs/lunar-lucky-imaging.md`](docs/lunar-lucky-imaging.md), `docs/dead-ends.md`
(registration/aliasing/seq-hygiene/quality entries + the acquisition
checklist's lunar block), `datasets/july26/` (ledgers with every verdict),
and the builder's own docstring.

## `web-culled-frames` — one surface for every excluded frame

USER-ORDERED: the Sky Objects section becomes **Culled Frames**, the single
examination surface for every frame the pipeline excluded, grouped by CAUSE — sky
objects (anomaly audit) as one subset, frame-QA defect-side auto-culls as another,
hand-ratified `recipe.json` excludes as a third. Each entry shows frame + sequence n,
set, cause with its metrics, and the record it traces to. The existing culled rollup
MERGES into it. Selection surfaces only — any per-frame preview is Siril-made.
**Closes when** after a chain run with auto-culls the page lists every excluded frame
under its cause and the separate Sky Objects entry is gone from the grouped rail.

## `framing-radec` — reproduce a drawn frame after a stack rebuild

The capture side, the verification and the diagnostic consume side are built and
exercised: a drawn rectangle becomes
`datasets/<session>/framing_<product>.json` carrying BOTH coordinate conventions (the
measured y-flip trap) plus WCS RA/Dec corners, `verify_framing.py` stamps it with
Siril `crop`+`stat`, and `finish_render --crop-record` applies a VERIFIED record to
the LINEAR stack before solve/SPCC/stretch, refusing unverified records and canvas
mismatches.

UNBUILT: deriving the rect on a REBUILT canvas from the record's RA/Dec corners —
today a canvas mismatch is refused, not re-derived. Siril 1.5's `eqcrop` is the
natural consumer. **Closes when** a drawn box renders to a final matching it AND the
record reproduces that framing after a stack rebuild.

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
- **The undistort builders take camera raws only** (the route's first stage is
  darktable's lens correction, and darktable reads raws). A FITS
  dedicated-astrocam set now routes here on its measured drift and is refused by
  name (`exit 9`), pointing at the standard route. Closes when a FITS path
  around the darktable stage exists — a BUILDER change, and a real capability
  gap rather than a routing defect.

## `cross-set-record-home` — the corpus has a record home; the FINISH stage still cannot write to it

`datasets/corpus/` now IS the corpus-level home and holds the corpus records —
`baseline.json`, `recipe.json`, `member_selection/` (the stage records + the profile
cache), `smear_attribution/`, the first build's finish records
(`solve_stack_july31+aug06+aug09+aug14_outnorm_presolvefix.json` — NOT the canonical's;
its `_identity` block carries the numbers) and the rest
(`datasets/corpus/README.md`). What is still wrong is the FINISH stage:
`finish_render.sh` hard-requires `--session=` and `--set=` ("SPCC spec routing +
record naming"), so a combine's finish records file under the REFERENCE set. The live
wart, MEASURED — 24 files matching `*july31+aug06+aug09+aug14*` sit under
`datasets/aug09/set-02/qa_work/` alone (plus 1 under aug14/set-05, 4 under
`datasets/corpus/`): the promote of the member-selection canonical (e4468e1) wrote
`solve_stack_july31+aug06+aug09+aug14_full.json` and
`spcc_set-02_july31+aug06+aug09+aug14_full.json` under
`datasets/aug09/set-02/qa_work/` (their `_nosel` predecessors moved aside beside them)
— a session-level product filed as a per-set one, the same defect as the earlier
1760-frame four-set combine's SPCC record landing under set-03. `datasets/README.md`
reserves session-level records for exactly this case (`../render_<tag>.json` beside
`experiments.jsonl`) and the finish stage cannot write one. **Closes when** a cross-set
product's finish records write under `datasets/corpus/` (or the session-level home)
without borrowing a member set's directory.

## `frame-qa-order-dependent-scale` — the same data measures differently by run order

`qa_work/frame_metrics.json` prefers the solved plate scale only if the fingerprint
already carries one, so running frame QA BEFORE the mount probe makes the pooled
record's px→arcsec scale keep the nominal instead of a solved one — 17.5031
nominal vs 18.003 probe, 2.9% apart. It is self-documented via `pixel_scale_source`
and never re-derived once written. **AMENDED (measured during the optics-state
audit): the 18.003 "solved" figure is itself an artifact** — all nine stack
solves across three sessions read 16.98–17.08 ″/px, so the probe pipeline's
green-plane scale arithmetic inflates by ~5.6%; the 13 pooled records it seeded
(july31/aug06/aug09) carry its figure, aug14's five kept the nominal (the order
defect recurred) and per-frame arcsec columns embed the nominal throughout
(px figures unaffected; `datasets/aug06/experiments.jsonl`,
`solved_scale_artifact_18_vs_17`). **Closes when** the scale is re-derived from
a direct full-frame solve (or the record refreshed against the stack solve)
and the probe-pipeline arithmetic's error is root-caused.

## `l1-set02-nonreplication` — WATCHLIST (rides the flat pause): two powered surfaces, same night, opposite answers

**OPEN QUESTION, not a scheduled item, and it touches a PAUSED line — see the fence.**

The L1 per-frame-vs-on-stack supplement SPLIT between two surfaces that the
pre-committed power criterion both rates as POWERED, with comparable errors:
set-01 separates at **2.59/2.09/1.47 SE**, set-02 does not at **0.85/0.03/0.48**.
Resolved in the verdict by rule (a split is reported, never majority-voted)
because no mechanism was in hand.

**One candidate is already refuted, at the cost of one lookup.** "The effect grows
with sky span" cannot explain it: the two sets' inter-frame excursions are
`sky_sep_arcsec` 16497.76 and 16549.39 — **4.5827° vs 4.5971°, 0.31% apart**.

**The successor hypothesis, stated so it can be tested rather than re-derived.**
The union's paired deltas say the on-stack arm REVEALS the starlight relation
(+6.34/+12.93/+6.37, 2.22–2.96 SE) while the per-frame arm leaves it unmoved
(−1.39/−0.83/−0.72, 0.31–0.66 SE). If what an on-stack plane reveals is the
anti-correlated `sky × V` residual, then the size of the arm difference should
track **the magnitude of that confound on each surface**, which is a property of
the flat rather than of the geometry. Prediction: the split follows set-02's
FLAT, not set-02's sky. It also explains union-vs-per-set without sky span — the
union is where the most confound accumulates, not where the most sky is.

**FENCED.** Testing it reaches into the flat-residual line, which the owner has
PAUSED pending real flats (`per-group-flat-at-the-combine` carries the pause).
Recorded so the question survives, not to schedule work. **Closes when** the
flat-residual line unpauses — this item rides that pause.

## `composite-header-identity` — the tuple shipped; the rgbcomp/standard-route half remains

LANDED (`ebbce14`): composites stamp `PIPEREV` = HEAD-at-compose, `CALSET`/`CALFSUM`/`CALDSUM` as MIXED tuples,
`DATE-OBS` = the earliest member start, no `GRPSIZE`/`FILENAME` — `docs/dead-ends/evidence-provenance.md`, "A
PROVENANCE STAMP BUILT AS AN ALLOW-LIST IS A DENY-LIST FOR EVERY KEY IT OMITS"; read back on the canonical, every
key of the tuple equal to what was emitted (`datasets/corpus/piperev_inheritance.json` `readback_canonical`). No
WEIGHT key is stamped — Siril's HISTORY card is the only trace (`docs/dead-ends/siril-behaviors.md`, "WEIGHTED
STACKING PRINTS NO PER-IMAGE WEIGHT"); a weight that becomes a chain choice gets a stamped key (STACKWGT).

OPEN: (e) whether `compose.py` rgbcomp composites and `run_pipeline.sh` stacks get the tuple at all (today no
stamp — absent, not false) — U; a guard naming the tuple's key set — D/build. **Closes when** both are recorded.

## `set-identity-by-sort-order` — the routing fix landed; three glob-order picks remain

FIXED (measured colour-neutral): `run_corpus_combine.sh` and `run_session_chain.sh` derive session/set from the
product's OWN `REGREF` (loud exit if absent or unstaged); `finish_render.sh` refuses a `--set` outside the CALSETS
window / reference set (fire-tested: the set-0b case stops at exit 1 before any tool runs); the two mis-filed
records live in `datasets/corpus/`. Mechanism, the consumer list (the NAME is POLICY) and the header-only
signature: `docs/dead-ends/stacking-compose.md`, "AUTO IS INDEX 0, NOT A RANKING".

OPEN — three glob-order picks: the acquisition-header donor (`scripts/stack/run_undistort_pipeline.sh:286`,
`header_capture "$(ls "$P/proc"/pp_c_*.fit | head -1)"` — `frame_order.py`'s capture-order emit fixes it but
re-times the ACQHDR donor on wrapped sets); the starmask pick (`scripts/stack/render_tier.sh:269`); the corpus-level
record home (BACKLOG:`cross-set-record-home`). **Closes when** each pick is order-independent or recorded harmless.

## `capability-gaps` — WATCHLIST (each gated on a data class we do not have): real capabilities the pipeline lacks

Each lands as a measured declared delta when its gate opens.

- **Full-size dual-band** — native Ha + 2× drizzle of OIII instead of downsampling
  OIII to Ha's half size. Gated on measured dither coverage (the per-frame
  `dither_phase_frac` record exists).
- **LRGB join** — `compose` REFUSES a `luminance` member, because L joins after both
  parts are stretched and this compose-then-render flow cannot express a nonlinear
  step. `rgbcomp -lum=` is the headless mechanism when an L corpus arrives; the CLI
  `-lum` blend colour space is undocumented — resolve before first use.

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
   **Discriminator: the same pin on a SPARSE field** — a crowding-driven intercept
   would fall there, a curve-driven one would not. (A body-measured curve, §1.5 B1, is
   owner-gated and NOT implied by this item.)
2. The upstream MR for the Z f conversion (Apache-2.0 → GPLv3; the database's issue #3
   asks for it) — U, the owner's call. The Butcher Z6 stays local (CC BY-NC-SA).

**Closes when** the B/G residual has an owner — the sparse-field discriminator run, or
the residual registered as a property of dense fields.
