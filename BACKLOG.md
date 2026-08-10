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

**Rules for this table, because it failed as a register twice.** (1) Every
divergence declared in code belongs here — a `REMOVAL CONDITION:` in a docstring
that is not in this table is invisible, and an audit on 2026-08-05 found FOUR of
them plus one adaptation with no condition written at all. When you add a
divergence, add the row in the same commit. (2) Every row carries the date it was
last CHECKED against reality, not the date it was written — "not fired" with no
date is the exact state that let a fired condition sit unnoticed. (3) Status is
the current verdict and its evidence, not a history of the divergence; mechanism
narrative belongs in `docs/dead-ends.md` and the script's own docstring.
(4) A condition that depends on the DATA (disk, sensor size) is re-checked per
dataset, and says so.

| divergence | retires when | last checked | status |
|---|---|---|---|
| `member_separation.py` cross-match + zone medians | an official tool reports headless member-to-member POST-REGISTRATION positional residuals across a sequence (a scriptable Siril registration-residual map, or a PixInsight equivalent) | 2026-08-10 | **not fired — REBUILT, and the rebuild found the instrument had been measuring nothing.** It cross-matched the REGISTERED copies, and `seqapplyreg -framing=max` on a variable-size sequence gives each output its OWN origin (MEASURED 611.9 px apart on the 28-member union; two members of ONE set shared 67 of 2000 stars within 12 px, 1721 once re-based). It now reads the members plus the homographies `register -2pass` wrote into the `.seq`, and bins by MEMBER-OWN field radius: 0/378 pairs unmeasured on that union against 378/378 before, in 12 s, with a monotone profile (0.22/0.48/1.30/2.43 px median). `--selftest` executes the falsification. Anchors re-measured on the fixed instrument: 0.14 / 0.21 / 0.38 / 1.23 / 3.04 / 3.28 against 0.144 / 0.194 / 0.352 / 0.934 / 2.991 / 2.112 — **thresholds NOT re-anchored, a user decision.** Original grounds unchanged: Siril `register` prints WITHIN-sequence residuals only; nothing reports where two members each place the same star. Built because the two prior instruments are MEASURED BLIND: corner `findstar` FWHM ranked a FAILING union (4.95 px) above the visually clean control (5.29 px), `seqtilt` read 0.34 px off-axis for the FAILING union against 0.40 for the PASSING one |
| optics/calibration FITS stamp (`header_provenance_lines`) + `backfill_substack_provenance.sh` | the warp stops being a TIFF round trip, so the model rides through natively (darktable gains FITS I/O, or Siril `register -disto=` — BACKLOG item 7); the BACKFILL retires once no un-stamped sub-stack remains on any rig | 2026-08-09 | **not fired** — the warp is still Siril `savetif32` -> darktable -> Siril `convert`, which carries no FITS header. Load-bearing: the lensfun user DB is global, unscoped, single-valued machine state that nothing reverts, so a sub-stack that cannot state its own optics cannot be composed safely later — 13 aug06 members under 3 different models composed into a doubled union and nothing in the product could see it |
| `anomaly_audit.py` in-house streak kernel | a tool detects/classifies transient streaks | 2026-08-05 | **not fired** — probed siril 1.4.4's own command list: `cosme`/`find_cosme`/`find_hot`/`seqfind_cosme` are cold/hot PIXEL defect correction; no streak, trail, satellite or Hough command exists. Standing check: an extreme-elongation QA flag ADJACENT to an audited crossing is the same object until shown otherwise |
| `star_shape.py` two-frame duplication | Siril exposes a headless single-image tilt | 2026-08-05 | **not fired** — `tilt` IS listed by `help` but REFUSES in a script ("This command cannot be used in a script: tilt", probed on-rig). Siril cannot sequence one frame, so the duplication stands. A `help` listing is not evidence of scriptability |
| `star_stations.py` fixed-station `findstar` medians | a tool reports a headless LOCAL star-shape map | 2026-08-05 | **not fired** — `inspector` (the aberration-inspector grid, the closest native thing) also refuses in a script, probed the same way; `seqtilt` is centre-vs-corners and blind to the drift-aligned band this exists for |
| fitted lensfun entry, PINNED per lens/focal (`lens_models.json`) | an upstream lensfun entry measured for THIS unit at infinity focus, or a chain that consumes the model another way (Siril `register -disto=` with a trustworthy source — probed 2026-08-09, it is a SHARED-solution facility, not per-image reprojection, so it does not retire this) | 2026-08-09 | **not fired — and RE-INSTATED.** The 2026-08-08 retirement ("condition fired: the chain consumes the model another way — per-set optical-state records") is REVOKED: the per-set method was refuted at its root (`docs/dead-ends.md`) and reverted. Its founding number, aug06/set-01's 0.82 px off-axis, is a COMPOSE artifact — set-01's own groups read 0.40-0.45 px under that same pinned model. Per-set models broke the combine (2.99 px within a night, 5.34 px across nights) where one shared model composes clean and is what every accepted combine here ever used |
| lensfun user-DB strip of the fitted lens's `<vignetting>`/`<tca>` (`install_lens_model.sh`) | darktable honours a style's lens `op_params` | 2026-08-05 | **not fired** — live block verified: vignetting and tca absent, exactly one focal=70 ptlens line. darktable still 5.4.1 / lensfun 0.3.4, so no bump has triggered a re-verify. Re-verify with `verify_lens_card.py` (grid control + uniform card; the card ALONE is vacuous) |
| per-set sky flat (`build_sky_flat.sh`, NOT de-skied) | a matching REAL flat for the set | 2026-08-07 | **not fired** — the flatless route, and it works: july31 sets measure 0.40/0.49/1.03/1.17% corner spread (a scratch rebuild from raws reproduced the experiments-ledger figures to the digit). The flat still converges to `sky x V`, so the object carries the sky's spatial profile (3.11% at 241 sigma) — REAL, open, and NOT fixed by de-skying the source frames (`--desky` was a 31x regression; `docs/dead-ends.md`) |
| GraXpert `-correction Division` synthetic flat | a matching real flat exists | 2026-08-05 | **not fired** — not adopted; no pipeline script calls it. Vignetting-only fallback |
| `baseline_guard.py` derived summaries (corner spread, edge dipole) over Siril `stat` | a tool reports a headless PRODUCT-level regression verdict against a stored reference | 2026-08-05 | **not fired** — nothing does. WIRED into `run_set_chain.sh` as the last step: it measures the finished product, and a regression exits **8** (a user decision, like the mount/route stops) without blocking or rewriting anything. Also a web stage for seeding/re-seeding. It is a no-regression RECORD, never a quality gate — a deliberate improvement fails it and the human re-seeds with a note. Blind spot to state when reading a PASS: both measures are STACK corners, which `docs/dead-ends.md` calls self-fulfilling for flat contamination, so it cannot see the open `sky x V` object tilt |
| `snr_regions.py` in-house SNR ratio over Siril `stat`/`bgnoise` | a tool exposes headless REGIONAL SNR | 2026-08-05 | **not fired** — `stat` and `bgnoise` are whole-image/selection; no regional-SNR command in 1.4.4. Every input number is the tool's; only the ratio is in-house. *(Was missing from this register until 2026-08-05.)* |
| `fingerprint.py` derived trail/drift geometry | an official tool reports headless trail/drift geometry with a declared-vs-measured mount cross-check | 2026-08-05 | **not fired** — no solver here exposes inter-epoch drift rate vs sidereal. The record schema and the STOP-on-CONTRADICT contract stay wherever it lands. *(Was missing from this register until 2026-08-05.)* |
| `inspect_stage.py` + `cull_report.py` robust-z per-frame flagging | a tool ships headless per-frame outlier flagging over its own registration metrics (SubframeSelector-class, scriptable) | 2026-08-05 | **not fired** — siril has `seqstat` (per-frame statistics to a file) and `select`/`unselect`, but no outlier GRADING over its own regdata. Persisting the tool's regdata is not a divergence and stays regardless. *(Was missing from this register until 2026-08-05.)* |
| prebuilt-master ingest (`run_pipeline.sh` `<session>/calib/`) | never — this is a supported INPUT class, not a divergence | 2026-08-05 | **CONDITION WRITTEN 2026-08-05, previously absent.** The code calls it "the adaptation for master-only data", which made it look like an unconditioned divergence. It is not one: a corpus that ships masters instead of raw calibration is a data class the repo accepts. What IS a stated limit: such masters carry no exposure/gain/filter headers, so the filename token is the whole identity and the exposure match is unverifiable — printed per run. Raw calibration dirs take precedence |
| 16-bit in three instruments (`coverage_probe.sh`, `run_frame_qa.sh`, `fit_lens_model.sh`) | the leg stops terminating in an integer/8-bit product | 2026-08-05 | **not fired** — each re-verified: `coverage_probe` switches to `set32bits` before its sum stack, `run_frame_qa` saves no product at all (analysis-only register), `fit_lens_model` terminates in `savetif8` for Hugin. Exemptions are enforced by name in `check_bitdepth.sh` |
| `run_undistort_groups.sh` group composition (one extra interpolation pass) | a measured quality cost of the extra pass at established magnitude (the along+1300 ledger resolving AGAINST groups), or cross-set composition leaving the project's goals | 2026-08-06 | **CONDITION REWRITTEN — the old trigger (free disk ≥ the single-pass peak) fired and was judged the WRONG condition: disk cannot retire groups.** Single-pass deletes the sub-stacks the cross-set combine composes and crops to `-framing=min` (composing per-set finals is a registered dead end), so a big disk buys nothing back; groups is the STANDING route (`force_route`), single-pass operator-only (`--route=single`, printed FORCED). Quality, two consistent accounts: the item-scoped one-knob A/B (60 frames even-stride) is **NULL — the route does not cause the one-sided band** (9/9 stations within 0.05 px majFWHM / 0.014 roundness; the band sits in BOTH arms at 1.27x/1.24x); the full-depth ledger records a small along+1300 improvement UNDER groups (0.12–0.18 px, direction replicates across two sets and two group sizes) whose proposed baseline mechanism was FALSIFIED (g250 landed outside the interval) and whose magnitude is UNESTABLISHED until the pre-registered `rebuild_repeat_floor_set01` runs (`datasets/july31/experiments.jsonl`). Peak math stays data-dependent, `W × H × channels × 4 × 2`: 560 MiB/frame at 6064×4040 OSC, 8 MiB mono astrocam, 1378 MiB at 61 MP |
| `scripts/lib/siril_run.{sh,py}` flock-serialized siril-cli invoker | flatpak fixes the instance-dir lifecycle race, or Siril invocations stop being per-frame process spawns (e.g. pyscript batching) so there is no window to collide in | 2026-07-28 | **not fired** — the race is a flatpak lifecycle bug, unfixed at 1.4.4/current flatpak, and every builder still spawns one siril-cli per step. MEASURED serializing: 4 concurrent jobs 1.74 s vs 0.47 s single (3.7x, matching serialized 1.88 s not concurrent 0.47 s), 3 of 4 reporting the wait; shell and python share ONE lock (cross-language test 0.93 s = 2x single). The lock is per-USER so it serializes across sessions on this rig. Every participant is now adopted: the one hold-out (`scripts/jwst/*`) went with the JWST cut, so `check_siril_invoke.sh` carries no exemption and any bypass FAILS rather than being reported |
| `scripts/stack/stamp_headers.sh` — capture + `update_key` restore of the acquisition keys the undistort warp drops | the warp stage stops being a TIFF round trip: darktable gains FITS I/O, or the distortion is consumed natively (Siril `register -disto=`, BACKLOG:`native-solve-and-sip`) so the keys are never dropped | 2026-07-28 | **not fired** — darktable 5.4.1 has no FITS reader, so the warp leg is TIFF and the loss is structural. Values are Siril's own (read from the raw into the calibrated frame's header); in-house code only READS the header and hands them back to `update_key`. LIVETIME is the one derived value (n_frames × EXPTIME, both tool-sourced) because the per-frame EXPTIME Siril would sum was destroyed upstream. MEASURED restored on july27 set-01: 9 keys, LIVETIME 789.0 s = 263 × 3 s, and the solve regained its hint (`scale hint: 10.5-26.3 arcsec/px`, index scales 11-19, vs the prior blind WIDE-FIELD fallback) |
| 5-set combine via TWO interleaved-half composes + a 2-member `-weight=nbstack` join (the 107-sub single-registration max compose needed ~37G transient vs ~24G reclaimable on the previous rig) | x86 disk → re-compose all 107 sub-stacks in ONE registration (every `groups_*` dir is kept for exactly this) | 2026-08-06 | **condition MET on this rig (950 G free, per the groups-row measurement) — the re-compose has NOT been run**, so the divergence stands in every shipped product until it is. Declared cost while it stands: the non-reference half carries one extra interpolation; halves span all five sets (interleaved), STACKCNT propagates exact frame weights (794+781=1575); the join landed natively in the cov25 orientation family. The 5-member per-set-stack shortcut is a measured dead-end (pre-cropped members — registry) |
| ~~unpinned neural stages in the render tier~~ | — | 2026-08-04 | **RETIRED, not fired: there was no divergence.** MEASURED bit-identical per stage (StarNet2 also across thread counts, Cosmic Clarity denoise, Siril's stretch/asinh/pm). Numbers in `docs/dead-ends.md` |
| ~~`frame_metrics.json` CFA-sampled FWHM~~ | — | 2026-08-04 | **RETIRED, condition fired and honoured.** `run_frame_qa.sh` debayers at convert (+9.1% FWHM inflation measured on the CFA arm). Records written the old way keep the caveat in their own `method` string |

---

## `compose-homography-smear` — the largest measured defect in any shipped product

**The sub-stack compose is a MOSAIC and is being aligned with a single homography.**
A group is a consecutive time block, so within one 1497 s burst the sky sweeps 6.25°
and a set's five members solve to centres **4.28° apart**. MEASURED at RA 294.86 /
Dec +44.99 (Siril `findstar`, 800 px boxes placed by each product's own solved WCS,
30 brightest fits so depth is rank-matched): all five aug06/set-01 members read
**2.42–2.54 px / roundness 0.924–0.942** at own-field radius 0.41–0.62, and their own
5-member compose reads **3.48 / 0.582**; the 13-member union 0.530, the 28-member
cross-night union 0.458. Control at RA 314.72: compose **2.43 / 0.949** against members
at 0.903–0.958. Mechanism and the full numbers: [`docs/dead-ends.md`](docs/dead-ends.md).

Cost on the accepted cross-night union, 19 columns marched at 5% steps: **roundness
0.448–0.613 over x = 15–30% of the canvas width** against 0.916–0.968 in the clean
band x = 45–70%. That is the smear the owner named.

Ordered work — nothing here is executed on an accepted product:

1. ~~**Fix the gate first.**~~ **DONE.** `member_separation.py` now bins by
   member-own field radius — and the rebuild found it had been cross-matching the
   REGISTERED copies, which `seqapplyreg -framing=max` writes with per-member
   origins (611.9 px apart, measured), so every number it produced was a chance
   nearest-neighbour distance. On this union: 0/378 pairs unmeasured against
   378/378, worst zone **7.53 px**, and the profile is monotone in member-own
   radius (0.22 / 0.48 / 1.30 / 2.43 px median). It confirms the pre-registered
   prediction — aug06/set-01's five members read **4.91 px** at the corner against
   set-03's **0.95** — and it shows the disagreement is NOT a function of night or
   set (same-night 2.44, cross-night 2.39, same-SET 2.21 px median).
   **Left open for the owner: the thresholds.** They were anchored to the broken
   instrument; re-measured anchors are 0.14 / 0.21 / 0.38 / 1.23 / 3.04 / 3.28.
   Nothing was re-anchored — an acceptance measure does not loosen without
   ratification — so the gate is currently strict enough to BLOCK a rebuild of
   the accepted union.
2. **Trial SWarp** (packaged 2.41.5-3, not installed) — resample each member onto one
   output WCS by its own solution. MEASURED support, not argument: the members' own
   astrometric solutions place the same stars within **0.10 px median / 0.26 px p90**
   at exactly the sky where the homography compose loses 1.06 px of FWHM. Per-member
   solving is measured working (8/8, logodds 113–201).
3. **Interleaved rather than consecutive groups** — one knob, cheap, collapses the
   within-set pointing spread to ~0. Trades the swept-field mosaic for consistency
   (co-pointed members compose to one member's area) and changes the dwell-floor and
   transient-rejection denominators, so it is a real trade, not a free win.
4. **A corner-true shared model** — reduces the residual the homography must absorb.
   No fit here constrains past ρ 1.47–1.51 against a corner at 1.80. The per-set trap
   is registered; a candidate is judged at the COMBINE, never per-set.
5. **Compose-input edge shrink / min framing** — ships less sky rather than fixing the
   cause. Last resort, and it must be called what it is.

**Open and unexplained:** why set-01 and not set-03 (0.582 vs 0.910, same sky, same
night, same model, same code), and why the low-RA side of the swept field — member
field radius does not predict it (ρ spread 0.21 vs 0.22 in both). Item 1 is the
instrument that answers it. **Closes when** a compose measures its members' realised
disagreement by member-own field radius and a route ships that holds
x = 15–30% at the clean band's roundness on the owner's eyes.

## `render-ladder` — the render tier's remaining tiers, user-gated

The first tier is BUILT (`scripts/stack/render_tier.sh`: separate → denoise the
starless → stretch → screen-recombine, every pixel op and every measurement a
tool's, gated by a ratified `render` block) and one render is user-approved —
**but that approval (july23 `set-01+02_desky_linked`, 2026-07-30) sits on a stack
built by the REGRESSED `--desky` pipeline, reverted 2026-08-04. Not revoked, but
not a trustworthy reference either; see the caveat in that set's `recipe.json`.**
What remains is the LADDER around it and the harness it feeds.

- **L1 background level — the FOCUS item (user-ratified), and no longer a
  choice between unknowns.** The desky revert removed two coupled halves; the
  lights-side half — per-frame `subsky 1 -nodither` on calibrated, debayered
  lights, the operator's correct domain and Siril's own per-frame degree-1
  doctrine — is restored UNCOUPLED as `--subsky-lights` (default OFF; the
  registry's desky entry carries the split). The combine-corner audit measured
  the cost of its absence: a ~+1% combine-introduced term at the framing=max
  compose's full-coverage corners, absent (<=0.2%) from the min-framed control
  on the same chain. The arm is pre-registered
  (`datasets/aug06/experiments.jsonl`, `subsky_lights_restoration`): one knob,
  members rebuilt, same flats/models/culls/compose args; judged on the
  same-sky linear corner probe AND the user's eyes on a like-encoded
  framing=max union pair — user-ratified requirement: the max union is the
  deliverable (manual crop later), no yield excuses. The composite-level arm
  is DEMOTED for this defect (a composite plane structurally cannot fit a
  corner-local term — measured, july23 subsky-on-combine probe); on-stack
  background remains the render-stage question for the sky's own gradient.
  Adoption still gates on preservation of the frame-filling UNRESOLVED
  STARLIGHT (degree 1 only; `docs/dead-ends.md` terminology entry — it is
  stars, not dust).
- **L2 denoise strength** — the proven chroma killer. Objective instrument is the
  `noise_split.sh` structured term, never whole-frame `bgnoise`.
- **L3 stretch ladder** — GHS/`ght` arms against the current `mtf`, compared at a
  MATCHED background landing so curve shape is the knob, not brightness.
- **L4 thresholded `satu`.**
- **Riders:** seed `datasets/GENERIC.json` (still the `{"render": {}, "why": {}}`
  stub) with the six current knobs and a per-knob class-risk note; first
  `baseline.json` via the no-regression harness; per-arm output tree
  (`web/results/<session>/exp_<param>_<stamp>/`) and the `<final>_stages/` labeled
  sequence, both binding requirements the tier does not yet emit;
  `judgment_package.py` re-wire (its PNG8 pairing predates the 16-bit-only policy).
- **Two known limits:** a set can carry only ONE ratified `render` block (keyed by
  name), so two kept looks are not expressible; and a mono set STOPS loudly — the
  luminance-only variant is unbuilt.

One knob per arm, hypothesis pre-registered, judged on full-frame lossless PNG16.
**Closes when** an approved, re-baselined render comes out of a laddered arm.

## `learned-deconvolution` — unmeasured, and the tool is installed

`render_tier.sh` skips deconvolution on three grounds that all hold — classical RL is
a measured dead end on in-exposure trailing, BlurXTerminator is not installed,
GraXpert's is the immature path. The fourth was never checked:
`/opt/cosmicclarity-6.6` ships `SetiAstroCosmicClarity` with
`deep_nonstellar_sharp_cnn_radius_{1,2,4,8}`, beside the denoiser the tier already
drives, and the registry explicitly does NOT dead-end a learned deconvolver.

The mainstream runs deconvolution with stars PRESENT, so it goes before the
separation. **Test:** one knob, non-stellar sharpen on the linear SPCC stack vs none,
bracketed by a same-arm repeat, judged on `star_stations.py` majFWHM per station +
`seqtilt` + the user's eyes at 1:1. The hypothesis under test is OBJECT detail — a
symmetric sharpener cannot de-trail an elongated PSF. Until it runs, the skip is a
hypothesis and the docstring says so.

## `calibration-evidence` — the de-sky work's unfinished evidence

**REVERTED 2026-08-04 — `--desky` is off by default; it was a 31x regression
(`docs/dead-ends.md`). The grounds it shipped on (flat odd plane 4.84%→1.98%
set-01, 7.82%→2.42% set-02; vignetting held ≤0.12%; PRNU correlation 0.999951)
were all measured with instruments blind to the failure: the odd plane is a
whole-frame fit that CANCELS under a partial sign inversion, and "vignetting held"
was a centre-vs-corner radial ratio that averages the two sides together.**
The underlying problem the work was aimed at is still real and still uncorrected —
a sky flat converges to `sky x V` and tilts the object 3.11% at 241 sigma. These
evidence gaps therefore remain open for whatever the eventual fix is:

- **The 3.11% / 241-sigma figure itself has NO TRACKED RECORD.** It is cited across
  six code and doc sites as the justification for a whole class of decisions, and
  it entered the repo as PROSE — no `datasets/` record holds the measurement, its
  instrument, or its n. Either re-measure it into a record or mark it unverified at
  every citation; a number that cannot be traced to a measurement is the same class
  as the run-to-run floor that was "a subtraction of two numbers you happen to
  have".
- **The odd-component instrument has no script.** The measurement that justified the
  default exists only as numbers in an `experiments.jsonl` sentence, so it cannot be
  re-run — and `build_sky_flat.sh`'s built-in gate is still corner-vs-centre, which
  the registry entry written alongside it calls SELF-FULFILLING for exactly this
  defect ("judge it on the FLAT's odd component, not the stack's corners"). Either
  the odd term becomes a script whose every pixel op is a tool's (Siril `stat` on
  quadrant crops gives it without in-house pixel maths), or the gate stops claiming
  to check what it does not. The probe's own invocation is preserved: DSC_8647/8/9 →
  `convert` → `calibrate -dark` → `load pp_c_00001` → `save before` → `subsky 1` →
  `save after`.
- **Which arm is CORRECT still rests on estimator arithmetic.** The 3.11%
  differential star-flux plane proves the two calibrations DIFFER; only the
  derivation says de-skied is right, and the Gaia check was structurally impossible
  (trailed stars at 17″/px). **The test that needs no catalogue:** within one set the
  drift carries every star ~1500 px across the sensor, so stack the FIRST third and
  the LAST third separately, match the same stars between them, and fit measured flux
  against sensor position. The correct calibration makes a star's flux independent of
  where it landed.
- **A with/without judgement pair on finals** — both flats exist for set-01/02, so
  this is stageable now. Unresolved-starlight preservation is the metric, the user's eyes decide.

Related and open: **SPCC order-robustness is UNTESTED, not verified.** Inserting the
background step ahead of SPCC moved K_G −1.20%/−1.48% and K_B −0.47%/−0.80% on
unchanged star counts — larger than the chain's own recorded K scatter (0.006).
Confounded, because the de-skied arm also removes a real ~3% object tilt. Clean test:
SPCC the SAME stack with and without an on-stack background step only.

## `walking-noise` — open gap, class-gated

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

## `dark-optimization-fork` — `-opt` vs matched darks on the uncooled body

Siril-FAQ doctrine fork: non-cooled cameras "should" use dark optimisation, while
base doctrine and both vendors say matched darks need none. A/B on one set, one
knob, judged on dark-residual / walking-noise metrics (feeds the
BACKLOG:`walking-noise` mechanism work). Low priority — our darks are same-night,
session-end temperature.

## `native-solve-and-sip` — two probes, in order

- **`platesolve -localasnet` on the mildly-trailed class.** The solver dead-end was
  measured on roundness-0.615 frames; july23 measures 0.80. If Siril's own blind
  solve handles this class, `solve_field.py` gains a native sibling (the external
  route stays for heavily-trailed data). One stack, one probe, record either verdict.
- ~~**Then Siril-native SIP undistort vs the darktable warp.**~~ **RUN 2026-08-09 —
  REFUTED AS INVOKED, and two beliefs corrected on the way.**
  (a) The precondition is MET for MEMBERS: `seqplatesolve -order=3` solved both
  aug06 members natively, 388/371 matched stars, residual sigx/sigy ~0.9 px,
  centres agreeing with astrometry.net to 0.001 deg. The "Siril cannot solve this
  class" belief was measured on single ULTRA-WIDE TRAILED frames and had widened
  past its evidence — stacked members have round stars.
  (b) But `register -disto=` is a SHARED-solution facility, not per-image
  reprojection: each member undistorted by its OWN SIP then composed measured
  3.99/6.42/6.19 px against the shipped route's 0.29/0.63/2.10/2.99, and ONE
  member warped by its own solution disagrees with its own unwarped self by
  8.50/9.45/6.76 px. The polynomial cancels only when every member shares it —
  so Siril's own design assumes ONE optical state per sequence.
  (c) The stated acceptance measures here (`seqtilt` off-axis + drift-axis
  stations) are both MEASURED BLIND to the star-doubling defect
  (`docs/dead-ends.md`); the re-run used `member_separation.py`.
  SUCCESSOR, unmeasured candidate: the industry operation is resampling each
  exposure onto a COMMON output WCS using its own full solution (CD matrix AND
  distortion) — SWarp's model, the SDSS/CFHTLS/DES/Pan-STARRS lineage. Nothing
  installed does it; SWarp is packaged for this distro at 2.41.5-3, python
  `reproject` is absent. See `docs/consistency-tiers.md` 4.2.

## `one-sided-band` — two mechanisms left on the residual drift-axis term

MEASURED on july27 (3 s subs, so the in-exposure trail is half july14's and no
longer masks it): a one-sided along-drift band at the +1300 station only — set-02
majFWHM 3.65 / roundness 0.684 against centre 2.56 / 0.901, elongation position
angle (+4.3°) aligned to the drift axis; the −side and both perpendicular stations
sit at the centre's floor. ELIMINATED:
- **the optics and the sky** — a single RAW frame (no calibration, warp or stack)
  is uniform across the field (0.712–0.810, +1300 marginally BETTER than centre),
  so nothing in-exposure produces it;
- **the lens correction misfiring** — `verify_lens_card.py` PASSES on this rig
  (grid control fires, Siril sigma 45644.8; uniform card corner-vs-centre
  0.000 ADU), and the community entry carries vignetting the fitted one does not,
  so a zero photometric delta proves the FITTED distortion-only entry is the one
  matching despite the EXIF string matching the community entry's capitalisation;
- **the stack architecture** — the july27 route A/B returned NULL: the band sits
  in BOTH arms at the same magnitude (register, groups row). The july31
  full-depth ledger adds a small groups-side improvement at the same station
  (0.12–0.18 px), mechanism unattributed and magnitude gated on the unmeasured
  rebuild floor (`datasets/july31/experiments.jsonl`) — a modifier of the band,
  not its driver.

REMAINING: distortion-model residual vs differential refraction. The named
discriminator is unchanged (hour-angle dependence: refraction varies with it, a
model residual does not) and has two same-night sets 30 min apart at different
pointings — set-01 reads a 13% along+1300 FWHM excess, set-02 43% — suggestive of
refraction but confounded by the pointing change. Cheapest next cut: a `lensdist`
vs `nodist` arm on the same 60-frame A/B input, which separates the model from
everything else in one knob.

## `star-neutral-colour` — the narrowband gap

SPCC-narrowband equalises O3=Ha and erases the O3 sphere; Siril has no single command
for a star-colour-neutral balance. Headless path identified and the tool half
confirmed on 1.4.4: measure mean star colour in the examine layer → apply a diagonal
`ccm`. UNTESTED design — do not cite as a method. Run it against a bracket (SPCC,
Nightlight) when a narrowband corpus arrives.

## `siril-1.5` — one load-bearing migration risk

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

## `optical-state-models` — CLOSED, REFUTED AND REVERTED

**The doctrine this item carried ("focus recalibrates every session; the lens
model keys on the OPTICAL STATE, per set") is dead.** Kept as a closed item
because the reasoning is instructive and the measurements are real.

**Its founding evidence was a compose artifact.** The item opened with "the
july-fitted pinned model measured against aug06: off-axis 0.82 vs 0.16–0.47 px —
the field-dependent signature of a state change". MEASURED on the preserved
sub-stacks: every one of aug06/set-01's five 100-frame groups reads **0.40 /
0.42 / 0.44 / 0.43 / 0.45 px** under that same pinned model — indistinguishable
from set-02's groups (0.45–0.46) and better on FWHM (2.74–2.79 vs 2.82–2.84).
The 0.82 exists only in the 500-frame product; set-02 is the depth control
(+0.11 over the same 100→500 increase, against set-01's +0.39). The chronology
said it first: 0.48 → **0.82** → 0.57 → 0.60 across strictly sequential,
frame-contiguous sets, and a focus change is a step, not a spike that returns.

**Its discriminators do not discriminate.** "All five fitted states differ beyond
the 0.47 px bound" was never evidence of distinct optical states: four independent
fits of ONE set span **0.36–6.30 px** (median 3.22) against a between-set spread
of 4.01–10.99 px (median 7.04) — the distributions overlap, and the bound is
exceeded 7–23× by refits of a single set. A refit of set-01 lands 0.83 px from
set-02's model and 3.26 px from set-01's own.

**Its adoption cost the project its core capability.** Adopted on 1 WIN / 3 NULL,
it gave new models to three sets that measured no benefit. Members warped under
different models disagree **2.99 px** at the composed corner within a night and
**5.34 px** across nights — visible star doubling, failed by eye — against
0.93 px / 0.71 px for the same pairs under one model and 0.14–0.35 px same-night.
One shared model is what every combine ever accepted here used, and the six-set
cross-night union rebuilt under one model was accepted by the owner as the most
detailed product to date.

**What survives, and where it went:** fitting a model from real frames (that is
how the shipped july14 model was made, and it beat the community profile at full
depth — centre station 5.30 → 3.67 px, on the owner's eyes); the corner-support
census (`cp_coverage.py` — no fit here constrains the corner, support stops at
ρ 1.47–1.51 against a corner at 1.80); and the instrument-fix and
architecture questions now carried by `docs/consistency-tiers.md` and
`docs/combine-contract.md`.

**Open, inherited from this item, NOT closed by the revert:**
- **Which single model.** For set-01 the pinned and own models produce
  indistinguishable MEMBERS (group medians 0.430 vs 0.420 px) and differ only in
  how those members compose (+0.39 vs +0.06). The july14 fit is the default on
  history and provenance; a per-set fit is a legitimate CANDIDATE. The comparison
  that settles it is at the COMBINE, one knob — never on a per-set product.
- ~~**The within-set compose amplification residue**~~ — **LOCALISED, and promoted to
  its own item: BACKLOG:`compose-homography-smear`.** It is not a residue and not the
  same family as the model question: the within-set 5-member compose turns members
  measuring roundness 0.924–0.942 into 0.582 at one sky and costs nothing at another,
  because a single homography cannot align members pointed 4.28° apart while any
  lens-model residual survives.
- **A state-CHANGE detector.** The concern the doctrine was reaching for is real:
  a genuine refocus mid-campaign would need a new model. Replace "per-set by
  default" with "one model per instrument state, plus a measured trigger" — the
  compose gate is the trigger, since members that disagree beyond its threshold
  are what a state change looks like.

## `final-best-percent-pass` — one target, many sessions, stack the best N%

The standing multi-session practice's endgame (user-ratified; walkthrough §6):
after many ~500-frame sets accumulate on one target, a FINAL pass analyzes
ALL sessions' raws and stacks only the best percentile. Unbuilt mechanics: a
cross-session frame-quality surface (per-set `frame_metrics.json` exists;
nothing ranks across sessions), a global best-N% selection the builders can
consume (`cullspec` excludes are per-set), and the ladder itself — N% arms,
one knob per arm, judged on full-frame lossless finals; README's
reference-standard row 1 soft-culling caution applies (selection adopted
through a measured ladder, never a default). Gated on the corpus existing.
**Closes when** a final-pass product ships from a measured best-N% ladder
across at least two sessions' raws with its per-set selection recorded.

## `session-level-mount` — one tripod pays for up to four probes

`mount` is modelled PER SET while it is a session-level fact: one tripod on one
night still pays for a drift probe per set. **Closes when** a decisive
session-level measurement seeds every sibling set's record (provenance kept per
set — a re-aimed set still cross-checks).

## `guards-and-ci` — nothing runs the guards

`check_bitdepth.sh` says "run it in CI / before a release" and no runner exists; the
web session smoke test added to it inherits that. **And one guard cannot be run at
all: `scripts/stack/check_stack_rejection.sh` is mode 664**, so `./scripts/…` is
permission-denied and only `bash scripts/…` works — a guard that fails to execute
is indistinguishable from a guard that passed, which is this repo's most persistent
defect shape. Also open: the bit-depth check is
per-FILE, so a builder that already emits `set32bits` in one generated `.ssf` passes
even if a newly added emission omits it — per-block granularity needs the
printf/heredoc blocks split on the `> "$X.ssf"` boundary every builder here uses.
Deferred deliberately: a fragile parser is worse than a stated limit, and the limit is
printed in the guard's own OK line.

## `lunar-ladder` — lunar lucky imaging: x86 ladder + next capture remain

**STATE: the first corpus is processed end to end and the chain is codified as
`scripts/stack/run_lunar_pipeline.sh`** (PROVISIONAL as-written — its first
fresh run is the next lunar corpus). Both sets' finals are user-ratified:
sb deconvolution + per-set disc-neutral WB (satu closed-fail; wiener arm
PAUSED on user order — equal on-disc, frame-edge artifact noted). Session
raws/intermediates freed (re-stageable); stacks + judge surfaces in
`web/results/july26/`; every mechanism in `docs/dead-ends.md`.

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

The route is validated, scripted, and the chain already routes by fingerprint
(`run_set_chain.sh`: tracked → standard, fixed+wide → undistort). Remaining:

- **Wire the vignetting-off assertion into `lens_preflight.py --require-profile`.**
  `verify_lens_card.py` exists and passes on x86 (grid control fires, uniform card
  corner-vs-centre 0.000 ADU) but nothing calls it from the preflight — today it is a
  manual step, so a darktable/lensfun bump can silently reintroduce double-corrected
  vignetting.
- **Per-lens facts re-derive at the next new lens/body/focal:** confirm lensfun
  coverage, interpolation behaviour and crop factor before first use. Any focal not
  fitted rides the community entry until fitted (`fit_lens_model.sh` per focal). A
  community profile can be right at the corner and wrong paraxially — the drift-axis
  station measure is the backstop `seqtilt` cannot provide.

## `aircraft-rejection-retest` — prove the aircraft actually rejected

The "satellites stay" policy was ratified on satellites and july23 recorded **no
aircraft**. july31/set-03 has one — both audit objects open on `DSC_5151` at
33.3/37.2 deg PA, the two-parallel-trails signature of a single airframe — crossing
`DSC_5151..5158`, 8 of 500 frames. The user ratified KEEPING it on the stated
mechanism: the trail MOVES, so any pixel carries it in ~1 frame of 500, which is the
minority per-pixel sigma rejection removes. That mechanism is sound but is an
argument, not a measurement — `check_stack_rejection.sh` guards the rejection CLAUSE,
not the rejection OUTCOME.

**THE RATIFIED KEEP IS ROUTE-DEPENDENT, and nothing recorded that.** "1 frame in
500" is the SINGLE-PASS denominator. The groups route stacks CONSECUTIVE BLOCKS, and
the crossing is 8 consecutive frames, so it lands whole inside one group: at the old
`--group=15` default that is **8/15 = 53% — a per-pixel MAJORITY**, which
`docs/dead-ends.md` says SURVIVES rejection, and the final compose is a plain mean
with no rejection at all. The same ratified decision therefore rejects the aircraft
on one route and ships it on another. Group size is now DERIVED to keep every group
in the GESD band (~100/group → 8%), which restores the argument — but the retest
below must state its ROUTE and its group size, because the answer is not a property
of the data alone.

**Closes when** set-03 is stacked twice — the ratified stack, and a control with
`DSC_5151..5158` excluded — and the two are differenced (Siril `isub` + `stat`) along
the aircraft's track. Nil residual on the track = rejection did its job and the frames
are free depth. A visible trail or a level step = the keep was wrong, and it becomes a
cull with its numbers. Cheap: one extra 492-frame stack, no new tooling. More data is
always obtainable, so a cull that buys certainty is not a loss.

## `routing-generality` — the router encodes ONE rig's assumptions, at six sites

The pipeline is supposed to pinpoint exact facts in the data and still make the
right call for a different rig — the same code right for OSC raws on an untracked
tripod AND for a mono, tracked, long-exposure set with real flats. Three confirmed
places where it is keyed to this rig instead:

- **`fov >= 10` is the route key, written at SIX sites, single-sourced nowhere**
  (`grep -rniE "fov[^0-9]*>= *10" scripts/ web/` — two in `fingerprint.py`,
  `_label` and the route branch of `fingerprint()`; two in `run_set_chain.sh`,
  the initial decision and the post-preflight re-derivation; and two grew with
  the readiness/position work: `readiness_report.py` `evaluate()` and
  `serve.py` `_set_position()`). This is the exact defect
  `disk_budget.sh` was created to kill, and it is spreading. The physically correct key is measured
  `drift_px`, which the fingerprint ALREADY computes: a fixed tripod at 200 mm has
  a small field and large drift, and today exits 5 as unroutable despite being the
  same class with *more* drift.
- **A real-flat set on the undistort route exits 6 and refuses.** Doing
  acquisition right stops the one-click chain while the flatless path runs.
- **A fixed + wide + FITS set** routes to undistort, which globs camera raws only,
  and dies with "no raw frames" — the right stop with the wrong diagnosis.

**Closes when** the route key is single-sourced on a measured quantity and the two
refusals either handle their class or name it accurately.

## `master-rejection-bypasses-doctrine` — the masters do not use the shared helper

`scripts/stack/siril/master_dark.ssf` hardcodes `stack dark rej 3 3` (winsorized).
The repo's own doctrine in `scripts/stack/stack_rejection.sh` selects GESD
(`rej g 0.3 0.05`) above 50 subs. july31's master dark is 347 frames, so it was
winsorized where the doctrine the repo enforces everywhere else says GESD. Lights
route through the shared helper; masters do not, so the two can drift apart
silently — the same shape as the per-builder disk constant `disk_budget.sh` exists
to prevent. **Closes when** the master templates resolve their rejection from
`stack_rejection.sh` or the divergence is recorded with its reason.

## `unpinned-registration-defaults` — a Siril update can change every stack silently

No generated `.ssf` in the stacking path pins `-transf=` or `-interp=`, so both
come from Siril's defaults. `TOOLS.md` names homography + lanczos4-with-clamp as
the doctrine for this class. Same family as the `setext` / `setcompress 0` /
`set32bits` pins already enforced by `check_bitdepth.sh`: a persisted or
version-supplied default that nothing asserts is a silent input to every product.
**Closes when** both are pinned in the generated scripts and the guard checks for
them.

## `cross-set-record-home` — a multi-set product has nowhere to write

`finish_render.sh` hard-requires `--set` (it exits with "--session= and --set= are
required"), so the 1760-frame four-set combine's SPCC record landed under set-03 —
a session-level product filed as a per-set one. `datasets/README.md` already
reserves session-level records for exactly this case (`../render_<tag>.json`
beside `experiments.jsonl`) and the finish stage cannot write one. **Closes when**
a cross-set product writes a session-level record without borrowing a member set's
directory.

## `frame-qa-order-dependent-scale` — the same data measures differently by run order

`qa_work/frame_metrics.json` prefers the solved plate scale only if the fingerprint
already carries one, so running frame QA BEFORE the mount probe makes every
`fwhm_arcsec` inherit the nominal scale instead of the solved one — a 2.8% error
(17.5031 nominal vs 18.003 solved). It is self-documented via `pixel_scale_source`
and never re-derived once written. **AMENDED (measured during the optics-state
audit): the 18.003 "solved" figure is itself an artifact** — all nine stack
solves across three sessions read 16.98–17.08 ″/px, so the probe pipeline's
green-plane scale arithmetic inflates by ~5.6% and every `fwhm_arcsec` in the
corpus rides it (px figures unaffected; `datasets/aug06/experiments.jsonl`,
`solved_scale_artifact_18_vs_17`). **Closes when** the scale is re-derived from
a direct full-frame solve (or the record refreshed against the stack solve)
and the probe-pipeline arithmetic's error is root-caused.

## `capability-gaps` — real capabilities the pipeline lacks

Each lands as a measured declared delta when its gate opens.

- **Full-size dual-band** — native Ha + 2× drizzle of OIII instead of downsampling
  OIII to Ha's half size. Gated on measured dither coverage (the per-frame
  `dither_phase_frac` record exists).
- **LRGB join** — `compose` REFUSES a `luminance` member, because L joins after both
  parts are stretched and this compose-then-render flow cannot express a nonlinear
  step. `rgbcomp -lum=` is the headless mechanism when an L corpus arrives; the CLI
  `-lum` blend colour space is undocumented — resolve before first use.
