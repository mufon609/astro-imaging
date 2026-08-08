# The wide-field-untracked chain, step by step

The complete raw-frames-to-judged-product process for the validated data class:
**camera raws, fixed (untracked) mount, wide field (≥ 10°)**. Every stage below
names what runs, which official tool touches the pixels, where the record lands,
and the measured reason the step is done this way rather than another. None of
it is a guessed knob: each choice traces to an instrument reading, and the
readings live in the tracked records this document cites.

Validated end to end by a blackbox rebuild from raws only (1,767 lights + 347
darks → five judged products; records under `datasets/july31/`, evidence cited
per stage below). The one-click driver for the whole chain is
`scripts/stack/run_set_chain.sh`; each stage is also runnable alone.

**The operating principle (CLAUDE.md, "WHERE THE GATE ACTUALLY IS"):** what the
data settles, the pipeline decides, announces, and records — mount, route, cull,
group size. What the data cannot settle — aesthetics, priorities, genuine
instrument disagreement — stops loudly for the user. The complete list of stops
is §10; everything else runs unattended.

---

## 1. Staging

`sessions/<session>/<set>/` holds raw frames ONLY; `sessions/<session>/darks/`
holds darks shot at the identical exposure/ISO in the same thermal window (the
acquisition checklist, `docs/dead-ends.md`). No flats staged means the flatless
route (§4); real flats present currently stop the undistort route (a documented
wiring gap, chain exit 6). All derived state lands elsewhere: records in
`datasets/<session>/<set>/`, bulk intermediates in `sessions/<session>/work/`,
products in `web/results/<session>/`.

## 2. MEASURE — what the dataset is

### 2.1 Acquisition facts → `acquisition.json`

`scripts/lib/acquisition.py` reads metadata only — exiftool for camera raws,
astropy FITS headers for astrocam frames — and derives camera, lens, focal
length, exposure, ISO/gain, geometry, field of view, nominal pixel scale,
cadence, time span. No pixel is read.

`mount` is the one fact headers cannot record. It is measured, not asked:

- **Trail-vs-roundness (cheap, one-sided).** A fixed mount smears every sub by
  `15.041 × cos(dec) × exposure / scale` px. Decisive only when that predicted
  trail exceeds the worst elongation the measured stars could hide by ≥ 10×
  with a real matched star population — it can rule OUT fixed, never prove it.
  On the validation corpus it correctly declined (predicted 1.56 px inside a
  ~2.3 px PSF).
- **Two-window drift probe (precise).** `scripts/qa/mount_probe.sh` solves two
  time-separated windows (§7 solver) and `scripts/lib/fingerprint.py` reads the
  RA rate against sidereal 15.041 deg/hr: fixed at 0.80–1.20×, tracked below
  0.20×, the gap deliberately unclassified. Validation: four independent probes
  read 15.0493 / 14.9909 / 14.9544 / 15.0649 deg/hr — all within 0.6% of
  sidereal → fixed.

A decisive signature is ADOPTED (`mount_source: "derived"`), announced, and the
run continues. A human declaration (`mount_source: "declared"`) is the override.
Declared-vs-measured disagreement is a CONTRADICT stop; a derived value that a
later measurement contradicts stops too (an unstable instrument). Only when the
instruments disagree or nothing measures does the chain stop and ask — exit 4.

### 2.2 Frame QA → `qa_work/frame_metrics.json`

`scripts/qa/run_frame_qa.sh` drives Siril `register -2pass` in disk-bounded
batches and pools the tool's own regdata: per-frame FWHM, roundness, background,
star count. **Order rule:** the drift probe runs BEFORE frame QA so
`fwhm_arcsec` rides the SOLVED plate scale, not the EXIF nominal (measured 6.0%
apart on the validation corpus: 16.979 vs 18.0031 ″/px —
BACKLOG:`frame-qa-order-dependent-scale`).

Defect-side outliers (robust z ≥ 3.5 on fwhm+, bg+, round−, nstars−) are
flagged. **Standing cull policy:** flagged frames auto-exclude like any
obstruction — the chain writes `recipe.json` `stack.exclude` with the flags as
the why and reports it; a hand-ratified stack block is never overwritten.
Validation: 7 flags = exactly the settling block at the session start, gaps of
82.7/119.3/127.0 s in the timeline record.

### 2.3 Obstruction audit → `audit_work/anomaly_audit.json`

`scripts/qa/anomaly_audit.py` classifies every transient obstruction —
AIRCRAFT / SATELLITE / UNKNOWN — with Siril doing every pixel op and measurement
(decode, green-extract, subsky, findstar); the in-house kernel computes only the
streak geometry and cross-frame linking no tool provides (the reference ALLOWED
gap-filler, CLAUDE.md bright line). It CULLS NOTHING — transients are
deliberately kept and left to the stack's sigma rejection. UNKNOWN is the honest
anomaly surface for human eyes.

The record is load-bearing: the groups builder derives its **dwell floor** from
the longest transient — `group ≥ ceil(max_dwell / 0.30)` (the GESD outlier
fraction) — so any transient stays a clear minority inside its group.
Validation: a 27-frame satellite forced floor 90 against a derived group of 100.

## 3. ROUTE — the fingerprint decides

`fingerprint.py` assembles what the set IS from tool outputs (header facts,
solves, frame metrics) and the chain routes on it:

- **tracked** → standard route (`run_pipeline.sh`: calibrate → register →
  stack); no inter-frame drift to fight.
- **fixed + fov ≥ 10°** → wide-field-untracked route, **groups builder, the
  STANDING route** (§6). Single-pass runs only as the recorded operator
  override `--route=single`.
- anything else → unroutable, exit 5 — the user picks.

Groups is standing because the fork is settled by measurement, not preference:
its retained sub-stacks are what keep the cross-set combine buildable
(single-pass deletes them and crops to `-framing=min`; composing per-set finals
is a registered dead end — each has discarded its outer drift zones, so the
combine holds holes exactly there), and its cost — one extra interpolation
pass — measured NULL (one-knob A/B: 9/9 drift-axis stations within 0.05 px
majFWHM / 0.014 roundness; the full-depth ledger's small unresolved delta runs
in groups' favor).

## 4. MASTERS

**Master dark** (`build_master_dark.sh`), once per session, from `darks/`. A
darks/lights exposure-ISO mismatch is DEGRADED, not fatal (the master still
carries bias level + hot-pixel map) and WARNs loudly.

**Flat — the per-set sky flat** (`build_sky_flat.sh`) on flatless sets: the
set's OWN un-registered, dark-subtracted lights, winsorized rejection (specks
measured 101 → 0 vs median), validation gates built in. Two hard rules, both
measured:

- **A flat calibrates ONLY the exact frames it was built from.** Cross-set
  reuse and shared/union flats are banned — a flat's low-order term carries its
  source set's sky gradient into every other set (`docs/dead-ends.md`).
- **Never `--desky`.** Running background extraction on raw (un-flat-fielded)
  frames fits a plane to `sky × V`, overshoots where vignetting curves hardest
  and inverts the edge asymmetry: corner spread 0.4% → 12.4%, a 31× regression,
  one knob, everything else identical.

**Carried open defect, stated honestly:** a sky flat converges to `sky × V`, so
calibration leaves the object carrying the sky's spatial profile (measured
3.11% at 241σ by differential star photometry). No processing step fixes this;
real flats at the session's optical state do. Acquisition outranks processing.

## 5. UNDISTORT — the stage that makes registration possible

An ultra-wide field drifting across the sensor cannot be registered by one
homography — lens distortion makes the frame-to-frame map non-projective. The
warp removes distortion so that every frame-to-frame map becomes a pure
homography, and homographies COMPOSE (the fact §6 rests on).

- `darktable-cli` (lensfun) applies the **distortion-only** model: the
  coefficients FITTED from the set class's own frames
  (`fit_lens_model.sh` / `install_lens_model.sh`), pinned in the repo, with the
  lens's vignetting/TCA stripped from the user DB. Styles are pinned in-repo
  and installed headlessly; `--style-overwrite` is required or the style is
  silently ignored. Re-install after every `lensfun-update-data` (it reverts
  the DB); `verify_lens_card.py` proves the state (grid control + uniform
  card — the card alone is vacuous).
- `lens_preflight.py --require-profile` runs FIRST and makes darktable PROVE it
  corrects the set (a lens lensfun cannot match warps nothing and says
  nothing), and asserts installed == pinned coefficients.
- **ICC discipline:** the 32-bit float leg ships the TIFF untagged and exports
  `--icc-type LIN_REC709` — a measured perfect identity (ratio 1.0000 every
  level/channel). `SRGB` belongs only on the 8/16-bit probe legs. Never
  `icc_remove` before `savetif32` (measured global ~1/12.92 scale).
- The TIFF hop drops FITS acquisition keys; `stamp_headers.sh` restores them
  (9 keys incl. the derived LIVETIME) so the solver keeps its scale hint.

## 6. STACK — balanced groups, GESD within, plain-mean compose

`run_undistort_groups.sh`, the standing builder:

- **Consecutive balanced groups** (validation: 5×100, 5×100, 5×100, 2×130),
  sized from frame count and floored by the audit's dwell floor (§2.3). Equal
  group sizes make each sub-stack an equal-weight mean, so the final mean
  equals the global mean.
- Each group runs the full chain (calibrate → warp → register → **GESD**
  rejection stack) and deletes its intermediates before the next group — the
  disk peak is per-group, derived from the set's own frame geometry
  (`disk_budget.sh`), never a per-camera constant.
- Every sub-stack is stamped **`GRPSIZE`** (the intended size, not `STACKCNT` —
  registration may legitimately drop a frame). A resume REFUSES a mismatched or
  unstamped sub-stack (mixed sizes would compose mixed depths and mixed
  rejection algorithms); `--plan` runs the same check dry.
- **Compose = register the sub-stacks + PLAIN MEAN.** Rejection across
  sub-stacks is a measured dead end: they are clean ~group-size means whose
  mutual scatter sits ~√group below per-frame noise, so a sigma gate clips real
  structure (measured: rewrites up to ~3800 ADU on a ~140 ADU sky).
- **Framing = min** at both levels. Per-group min trims a consecutive block's
  ~1% drift; the final min landed at 88% of the best available all-covered
  rectangle on the validation corpus (10.73 vs 12.20 Mpx, coverage-probe
  measured) — the pathological 36% case belongs to rotated members, which
  consecutive groups do not produce.
- **Cross-set combine** (`run_undistort_compose.sh`): register ALL sets'
  sub-stacks in one pass (validation: 17 sub-stacks → 1,760 frames / 73.3 min),
  reference chosen central in pointing and time, `--weight=nbstack` when member
  depths differ. This is the product the standing route keeps buildable.

**Multi-session accumulation — the standing practice for ONE target shot
across sessions (user-ratified).** Sessions accumulate FULL (~500-frame)
sets; short sets are stacked standalone (test/preview products) and are never
combine members — a short member's drift span cuts the common canvas, and the
combine takes the largest fully-covered crop, full sets only. Interim
combines compose the full sets' retained sub-stacks as above and re-run as
new sessions land. Once many full sets are gathered, the FINAL pass
re-selects from ALL sessions' raw frames: per-frame quality from the tools'
own registration metrics across every session, stacked at only the best
N% — the percentile is a quality LADDER decided during that final process
(one knob per arm, judged on full-frame lossless finals), never fixed in
advance. Interim products are working surfaces; the final-pass product is the
target's deliverable (BACKLOG:`final-best-percent-pass` holds the unbuilt
mechanics).

## 7. SOLVE → SPCC — astrometry and colour, with the three traps

- **Plate solve:** `scripts/calibrate/solve_field.py` — SExtractor core (`sep`)
  extraction + the astrometry.net engine. Siril's internal solver cannot match
  ultra-wide trailed-star fields (a data property, not an arch one). The WCS is
  injected into a `_wcs.fit` copy.
- **SPCC** (Siril): needs the FULL Gaia xpsamp cone (`spcc_cone.py` computes
  the nside=2 cover and fetches missing chunks, md5-verified) and THREE
  machine-local prerequisites — the chunks, the `catalogue_gaia_photo` config
  path, and the cloned `siril-spcc-database`. Missing the third SEGFAULTS
  silently (exit 139) looking like a data bug. Sensor spec comes from
  `recipe.json` when the database has an entry; otherwise the sensor-null
  generic curve, stated in the report. Validation: neutral everywhere,
  R/G 0.9986–1.0000, B/G 0.9959–0.9969.

## 8. JUDGE SURFACE — the diagnostic end of the chain

`finish_render.sh`: solve → SPCC → **linked** autostretch → full-frame 16-bit
PNG at `web/results/<session>/judge/<name>_spcc-linked.png`. Linked is
mandatory after SPCC (unlinked autostretch on a calibrated stack is the
chroma-blotch engine). The chain ENDS here: everything aesthetic beyond it (the
render tier) is per-rung and user-judged.

**The stretch rule for multi-surface sets** — one RULE for every member, chosen
by whether the surfaces share an absolute brightness scale:

- shared linear origin (a one-knob ladder off one stack) → one pinned `--mtf`
  triplet;
- independent products with honestly different sky levels (per-set stacks
  beside their combine — measured 45% sky-median spread) → per-product
  `autostretch -linked`, the sky-anchored rule. One raw triplet there renders
  honest sky differences as gross brightness differences.

**Judgment policy:** the 16-bit PNG is the ONLY surface a verdict is taken
on — whole frame, opened in the user's own viewers; no crops, no panels, no
reduced-depth copies. `judgment_package.py` verifies and assembles the set
(header-verified 16-bit, starless layers refused, INSPECTION.md mandatory).
Delivery surfaces are a separate, allowed category.

## 9. ACCEPT → BASELINE — the loop closes

The user's verdict on the finals is the acceptance. `baseline_guard.py --seed`
then records the accepted product's measures — corner spread, edge dipole,
centre medians (all Siril `stat`) — with visible tolerances into
`datasets/<session>/<set>/baseline.json`. Every later chain run re-measures the
finished product against it and exits 8 on a mismatch: loud, never blocking,
repeating until a human finds the cause or re-seeds with a note. A deliberate
improvement fails it too — that is correct. Stated blind spot: both measures
are stack corners, so the guard cannot see the open `sky × V` object tilt (§4).

Reproducibility evidence for the whole chain: a scratch rebuild from raws
reproduced the corner-spread ledger to the digit (0.40 / 0.49 / 1.03 / 1.17%)
and every stage's records landed identically (`datasets/july31/`).

## 10. The human moments — the complete list

The chain's measure phase ends at the **readiness report**
(`scripts/qa/readiness_report.py`): every criterion below §2–§9 on ONE
surface, GREEN (met — value + instrument stated) / YELLOW (met, but look —
never blocks) / RED (blocks HERE, exit 7) / PENDING (pre-run surfaces only:
not yet measured and the run itself produces it — the chain passes
`--post-measure`, so after the measure phase absence stays RED). One
approval — `--yes`, a terminal ask, or the web run click — then the build
runs unattended. The report is a tracked record (`readiness.json`), so what
was approved is auditable. The web renders the same evaluation as a per-set
rail, beside a per-set POSITION stepper whose step evidence is the chain's
own skip-if-exists tests (computed server-side in `web/serve.py`
`_set_position`; products and records prove done, the jobs table proves
running).

| stop | meaning |
|---|---|
| exit 2 | declared-vs-measured mount CONTRADICT — reconcile the label |
| exit 4 | mount underivable — instruments disagree or nothing measures |
| exit 5 | unroutable fingerprint — neither tracked nor fixed+wide |
| exit 6 | real flats staged on the undistort route (wiring gap) |
| exit 7 | readiness RED — the report names the blocker before anything builds |
| exit 8 | product regressed vs the accepted baseline (informative, post-build) |
| always | the ONE approval after the report; aesthetics on full-frame lossless finals |

## 11. Open defects and watch-list (with their records)

- `sky × V` object tilt, 3.11% at 241σ — real, uncorrected, needs real flats
  (§4; register row in BACKLOG).
- One-sided along-drift band — reproduced across nights and routes; mechanism
  open; the named discriminator needs matched-time, different-hour-angle sets
  (BACKLOG:`one-sided-band`).
- Session FWHM walk (+9.9%) / roundness walk (−6.5%) — airmass refuted by
  bounding (field rose while FWHM rose); dew refuted (star counts flat);
  cause open (`datasets/july31/experiments.jsonl`).
- SPCC sensor-null — no Z6III database entry; K factors ride the generic curve.
- `mount` is modelled per set but is a session-level fact (one tripod pays for
  up to four probes) — BACKLOG.
