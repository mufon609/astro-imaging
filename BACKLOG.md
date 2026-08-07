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
| `anomaly_audit.py` in-house streak kernel | a tool detects/classifies transient streaks | 2026-08-05 | **not fired** — probed siril 1.4.4's own command list: `cosme`/`find_cosme`/`find_hot`/`seqfind_cosme` are cold/hot PIXEL defect correction; no streak, trail, satellite or Hough command exists. Standing check: an extreme-elongation QA flag ADJACENT to an audited crossing is the same object until shown otherwise |
| `star_shape.py` two-frame duplication | Siril exposes a headless single-image tilt | 2026-08-05 | **not fired** — `tilt` IS listed by `help` but REFUSES in a script ("This command cannot be used in a script: tilt", probed on-rig). Siril cannot sequence one frame, so the duplication stands. A `help` listing is not evidence of scriptability |
| `star_stations.py` fixed-station `findstar` medians | a tool reports a headless LOCAL star-shape map | 2026-08-05 | **not fired** — `inspector` (the aberration-inspector grid, the closest native thing) also refuses in a script, probed the same way; `seqtilt` is centre-vs-corners and blind to the drift-aligned band this exists for |
| fitted lensfun entry, per lens/focal (`install_lens_model.sh` from the PINNED `scripts/darktable/lens_models.json`) | an upstream entry measured for THIS unit, or a chain consuming the model another way | 2026-08-05 | **not fired.** The shipped model is `a=0.00350093 b=0.01453356 c=0.00043983` — fitted 2026-07-17 on the previous rig, and every product under `web/results/` was warped with it. It is NOT regenerable: the same procedure on the same frames under this rig's Hugin returns coefficients 3.9%/30.6% apart (887eb00), so a re-fit is a NEW model, never a reproduction — yet displacement-EQUIVALENT at product level (max diff 0.47 px mid-field, 0.34 px area-weighted RMS, 0.2 px at r=0.9; `qa_work/lens_fit.json`), so the incumbent stands on measurement as well as provenance: re-installing the lateral new fit would change the deliverable by ≤0.47 px with no measured benefit. It is now PINNED as data and installed from the record, which is how a measured constant is reproduced. Until 2026-08-05 it existed only as a script literal and bytes in a machine-local DB, so no clone could rebuild the optics its own products were built with; this register watched the removal condition and never noticed the thing it guarded was unrecorded. `lens_preflight.py --require-profile` now asserts installed == pinned, which catches the `lensfun-update-data` wipe the warp-happened proof is blind to. The x86 re-fit stays a CANDIDATE (recorded in the pinned file), untested at product level |
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

## `render-ladder` — the render tier's remaining tiers, user-gated

The first tier is BUILT (`scripts/stack/render_tier.sh`: separate → denoise the
starless → stretch → screen-recombine, every pixel op and every measurement a
tool's, gated by a ratified `render` block) and one render is user-approved —
**but that approval (july23 `set-01+02_desky_linked`, 2026-07-30) sits on a stack
built by the REGRESSED `--desky` pipeline, reverted 2026-08-04. Not revoked, but
not a trustworthy reference either; see the caveat in that set's `recipe.json`.**
What remains is the LADDER around it and the harness it feeds.

- **L1 background level** — there is NO shipped background step as of 2026-08-04:
  `--desky` was reverted (31x regression, `docs/dead-ends.md`) and it took the
  per-frame `subsky 1` on the lights with it, since the chain passed one flag to
  both halves. So this is now an OPEN choice, not a challenge to a default. The
  open question is now a CHALLENGE to a default, not a choice between unknowns:
  on-stack vs per-frame, one knob, preservation of the frame-filling UNRESOLVED
  STARLIGHT deciding (`docs/dead-ends.md` terminology entry — it is stars, not dust).
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

## `render-reproducibility` — CLOSED: the tier is bit-reproducible

**Measured, so this is done.** Two identical runs of each stage, compared with Siril
`isub` (all-nil = bit-identical): StarNet2 via `starnet -stretch` — identical, and
identical again across thread counts (default 28 vs `setcpu 1`, cross-compared);
Cosmic Clarity denoise (`--disable_gpu`, separate mode) — identical; Siril's stretch
+ `asinh -human` + `pm` recombine — identical. Nothing needed pinning, and neither
binary exposes a thread/seed/device flag to pin with.

**A number this corrected.** The 1.34% "run-to-run floor" that motivated this item was
a misattribution: it came from two render records read as a same-arm repeat, where the
old record logged neither its linear source nor its knob provenance. It is gone from
`web/serve.py`, and the render colour check now reports an EXACT shift with no
NULL-below-floor verdict — because with a deterministic chain there is no floor to
hide an effect under, and between two ladder arms off one stack any difference is the
knob. Mechanism + the "a floor is a measurement, not a subtraction" lesson:
`docs/dead-ends.md`.

Thread-count invariance holds for BOTH neural stages: StarNet2 at siril's default 28
threads vs `setcpu 1`, and Cosmic Clarity at 28 vs `OMP_NUM_THREADS=1` — bit-identical
each way and cross-compared. So the determinism is not an artifact of one machine
state, and a rig with a different core count reproduces the same bytes.

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
- **Then Siril-native SIP undistort vs the darktable warp.** Siril 1.4 fits SIP and
  `register -disto=` consumes it — a DIFFERENT SIP source than the index-constrained
  fit the registry killed. This is the fitted-lens-model removal-condition test with
  a concrete native route. One knob, judged on `seqtilt` off-axis + drift-axis
  stations + full-frame finals. Precondition: the probe above must solve this class.

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

## `derive-mount-from-data` — CLOSED: the data answers, and the pipeline listens

**DONE 2026-08-06.** `acquisition.resolve()` now ADOPTS a decisive measured mount
signature from `fingerprint.json` instead of stopping for a human to retype it,
and `run_set_chain.sh` continues instead of exiting 4. It stops only when the
instruments genuinely could not decide.

This item had been written down three times — here, and in two audit prompts — and
built zero times. The measurement machinery was all present and running: the chain
measured the signature, recorded it, printed it, and then asked anyway.

**The argument it had to answer, because it was a real one.** `acquisition.py` held
that "the measurement never self-adopts, because the declared-vs-measured pair is
what makes CONTRADICT detectable at all" — auto-adoption makes declared == measured
by construction, so the cross-check can never fire. Half true. CONTRADICT catches a
human MISLABEL, and a set nobody labelled has no mislabel to catch. What must
survive is the ability to tell the cases apart, so the record now carries
`mount_source`:
- `declared` — a human value; the full human-vs-data cross-check, CONTRADICT stops.
- `derived` — adopted from the instruments; a LATER measurement that disagrees
  still stops, which is no longer a mislabel but an unstable instrument, and is
  worth stopping on too.

**Verified by execution, six cases from clean state:** no measurement -> STOP;
decisive signature -> derive and proceed (`mount_source=derived`); instruments
disagree (`measured` nulled by `mount_verdict`) -> STOP; derived then contradicted
by a later measurement -> STOP CONTRADICT; human declaration -> proceeds as
`declared`; human mislabel -> STOP CONTRADICT.

The verdict vocabulary is UNCHANGED (CONFIRM / CONTRADICT / INDETERMINATE) — the
web UI, `serve.py` and `fingerprint.py --selftest` all consume those strings, and
the selftest still passes. What changed is who acts on `measured`.

Two wiring constraints in `run_set_chain.sh`: capture the adopted mount from the
resolve() call that adopts it (`derived_now` appears only on that call — a
throwaway seed call swallows the adoption and mis-reads as instrument
disagreement, exit 4 with the answer already on the record), and re-derive ROUTE
after an adopt (handed to the post-preflight re-derivation; left unrouted, no
builder arm matches and the run dies after spending the masters).

Still open, and deliberately not done here: `mount` is modelled PER SET, so one
tripod on one night still pays for up to four probes. It is a session-level fact.

## `approval-tag-never-used` — the approval mechanism is fiction

`README.md`, `datasets/README.md`, `web/README.md` and `serve.py` all treat a
`<session>-all<N>-<tag>-approved` git tag as THE record that a render was judged
and re-baselined. `git tag --list` is EMPTY and always has been — no approval tag
has ever been created, so `serve.py`'s tag query returns nothing for every session
and the "two things called approved" distinction in `web/README.md` has only ever
had one half in existence. Either the tag becomes a real step at the point a
render is accepted (and something creates it), or the docs stop describing it as
the record. **Closes when** an approved render either carries a tag or the
mechanism is retired from all four sites.

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

## `flatpak-race` — CLOSED: one flock-serialized invoker

CLOSED — the hardening fork this item posed (bounded retry vs flock) is decided
and built: every shell and python call site sources
`scripts/lib/siril_run.{sh,py}`, one per-user flock serializing every siril-cli
spawn, with `scripts/stack/check_siril_invoke.sh` failing any bypass. Retry lost
because it recovers after the fact and needs a log the invoker cannot see. The
bwrap mechanism, measured serialization numbers, and the removal condition live
in the invoker's own docstring and the register row above. The one unadopted
caller went with the JWST cut, so the guard is now unconditional.

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

## `readiness-report` — ONE traffic-light gate, not N scattered stops

**USER-ORDERED 2026-08-06, and it is the structural fix for the doctrine bug
`CLAUDE.md` now records.** The chain currently interrupts at each gate in turn, so
a run can stop three hours in for something knowable in the first ten seconds, and
each stop asks the human to re-answer a call they already ratified the criteria
for. Replace that with one surface: evaluate EVERY ratified criterion up front,
report them together with a status colour, take ONE approval, then run unattended.

**The colour contract (user-stated):**
- **GREEN — go.** The criterion is met from the data. State the value and the
  instrument, not just the tick.
- **YELLOW — wait / look at this.** Met, but with something the user should SEE
  before it runs. It does not block; it is the reason the report exists rather
  than an auto-run.
- **RED — bad or missing.** Blocks. This is the only thing that stops the run, and
  it stops HERE rather than mid-build.

**Criteria the report must cover** (every existing gate, plus what is currently
only discoverable by reading logs):

| criterion | GREEN | YELLOW | RED |
|---|---|---|---|
| mount | derived or declared, instruments CONFIRM | derived (not human-declared) — say so | instruments disagree, or CONTRADICT |
| route | fingerprint decisive | forced with `--route=` | unroutable |
| frame QA + cull | ran, cull ratified in recipe | standing auto-cull will apply N frames | not run |
| obstruction audit | ran, dwell floor cleared with headroom | cleared under ~20% headroom, or any UNKNOWN object | floor exceeds the group size |
| optics | installed == pinned, warp proven | community entry, not the fitted one | mixed optics, or lensfun cannot match the lens |
| masters | dark + flat present | flat is a sky flat (flatless route) | missing, or a real-flat set on the undistort route |
| flat quality | corner asymmetry under the WARN | above it — the open `sky x V` defect | builder gate failed |
| disk | covers the peak with margin | covers it without margin | below the derived peak |
| SPCC | Gaia cone complete, sensor matched | sensor-null generic curve | chunks missing |
| baseline | present, product will be compared | none yet — nothing to regress against | product regressed (exit 8) |

The single-pass vs groups fork inside the undistort class is NOT one of the
report's questions — groups is the standing route (`force_route`; the
`run_undistort_groups.sh` register row above) and rides the route criterion:
GREEN derived, YELLOW only when `--route=` forces it.

**Then:** print it, ask once, run. `--yes` skips the ask for an unattended re-run;
`--plan` keeps its current meaning (show and exit).

**The website gets the same data, same colours** — the set page shows the rail as
green/yellow/red so the state is readable without a terminal, and the run button is
the same single approval. One evaluator feeds both; the report is a record, written
beside the other per-set records so what was approved is auditable afterwards.

**Closes when** a set goes from raw frames to a finished product with exactly one
human interaction — reviewing the report and approving it — and any genuinely
undecidable criterion is RED in that report rather than a stop discovered later.

## `scope-own-photons-only` — JWST is CUT, and the boundary it establishes

**DONE 2026-08-06: every JWST surface is removed from this repo** — `scripts/jwst/`
(13 files), the web tab (`serve.py` stage registry + `index.html` pgJwst, 144 lines
of UI), `TOOLS.md` Tier A, `docs/jwst-*.md`, the `datasets/jwst-jupiter/` records,
and the two JWST-pipeline entries in `docs/dead-ends.md`. The invoker guard
(`check_siril_invoke.sh`) lost its only exemption with it and is now unconditional.

**The decision this records, which outlives the deletion.** The archival
space-telescope class was CLOSED-FAIL by user verdict (2026-07-28) after five
judgment rounds failed the user's eyes while passing their own instruments. But
the reason it is CUT rather than merely closed is scope, not failure: this repo
processes photons WE shot — raws off a camera on a mount, calibrated and stacked
by tools we drive. Reprojecting somebody else's calibrated space-telescope mosaics
is a different craft with different inputs, different tools and a different notion
of "correct", and carrying it forced a parallel chain that shared almost nothing
with the real pipeline while diluting every operating doc that had to describe both.

**The standing rule:** a data class earns a place here only if it starts at raw
frames from a camera and ends at a judged render through the pipeline in
`README.md`. An archival, pre-calibrated or vendor-finished corpus is out of scope
— do not re-add one, and do not reason about this pipeline's behaviour from one.

Its removed lessons were tool-specific to the STScI pipeline (`skymethod=match`
absorbing planetary glow, ramp-level `clean_flicker_noise` eating extended
emission) and do not transfer to any tool this repo drives, which is why they went
with it rather than staying in the registry. Full text is in git.

## `web-jobs-filter` — DIAGNOSED, one-line fix

USER-OBSERVED: starting a job made other sessions' jobs repopulate the Run page. The
mechanism is in the code: `web/index.html` filters on `M.session`, which LAGS a fetch
(`loadSession` sets `SESSION` synchronously, then awaits `M`) and falsy-defaults to
SHOW ALL; the running-strip a few lines below already uses `SESSION`. Use `SESSION` in
both and never default to show-all. **Closes when** starting a job on a session page
with another session's records present leaves the table showing only this session's
rows, at start, during, and at completion.

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
- ~~Run the two-window drift solve live on a boundary-regime camera-raw corpus~~
  **DONE** — exercised exactly there on july31: the roundness check correctly
  declined (predicted trail 1.56 px inside a ~2.3 px PSF) and four independent
  probes decided the mount at 15.0493/14.9909/14.9544/15.0649 deg/hr vs
  sidereal 15.041 (`datasets/july31/*/qa_work/mount_probe.json`).

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

## `groups-resume-size-blind` — CLOSED: the builder stamps GRPSIZE and refuses a mixed resume

The closing condition ("a resume across a changed group size either reuses
nothing or refuses loudly") is shipped in `run_undistort_groups.sh`: every
sub-stack is stamped `GRPSIZE` (the INTENDED group size, not `STACKCNT` —
registration may legitimately drop a frame); the build loop refuses to skip an
existing `sub_NN.fit` whose `GRPSIZE` mismatches the run (exit 1, both sizes
named); an unstamped legacy sub-stack reads 0 and fails closed as an UNRECORDED
size; and `--plan` runs the same check dry (`plan_resume_check`), so the refusal
is reachable without touching a product. Verified on a 17-sub-stack session:
stamps {100: 15, 130: 2} match the derived sizes exactly. The mixed-rejection
hazard closes with it — group size selects the rejection algorithm, and no
mismatched size composes.

## `routing-generality` — the router encodes ONE rig's assumptions, at four sites

The pipeline is supposed to pinpoint exact facts in the data and still make the
right call for a different rig — the same code right for OSC raws on an untracked
tripod AND for a mono, tracked, long-exposure set with real flats. Three confirmed
places where it is keyed to this rig instead:

- **`fov >= 10` is the route key, written at FOUR sites, single-sourced nowhere**
  (`grep -rniE "fov[^0-9]*>= *10" scripts/` — two in `fingerprint.py`, `_label`
  and the route branch of `fingerprint()`; two in `run_set_chain.sh`, the initial
  decision and the post-preflight re-derivation). This is the exact defect
  `disk_budget.sh` was created to kill. The physically correct key is measured
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
and never re-derived once written. A measurement whose value depends on which step
ran first is not reproducible from the data alone. **Closes when** the scale is
re-derived (or the record refreshed) once a solve exists.

## `spcc-sensor-null-unstated` — COMPLIANT in the docs, generic curve in the run

SPCC's premise is convolving Gaia spectra with THIS sensor's response. The
installed database carries no Z-series entry, so every K factor on this corpus was
computed against the sensor-null generic default. `spcc_run.py` handles this
honestly — it prints `sensor-null (generic default)` and rides `sensor_spec` /
`sensor_spec_source` / `matched` with every product record — but `README.md`'s
reference-standard table still calls step 3 COMPLIANT with no caveat, so the
limitation is visible in the records and invisible in the contract. **Closes when**
the README row states the sensor-match limitation, or a measured Z-series response
is contributed to the database.

## `capability-gaps` — real capabilities the pipeline lacks

Each lands as a measured declared delta when its gate opens.

- **Full-size dual-band** — native Ha + 2× drizzle of OIII instead of downsampling
  OIII to Ha's half size. Gated on measured dither coverage (the per-frame
  `dither_phase_frac` record exists).
- **LRGB join** — `compose` REFUSES a `luminance` member, because L joins after both
  parts are stretched and this compose-then-render flow cannot express a nonlinear
  step. `rgbcomp -lum=` is the headless mechanism when an L corpus arrives; the CLI
  `-lum` blend colour space is undocumented — resolve before first use.
