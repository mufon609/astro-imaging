# BACKLOG

What is queued, why it matters, and what gates it — ordered. Each item states the
mechanism and the test that would close it, not a narrative.

Where things live: mechanism lessons + the acquisition checklist in
[`docs/dead-ends.md`](docs/dead-ends.md); the toolkit in [`TOOLS.md`](TOOLS.md);
per-dataset state under `datasets/<session>/<set>/`; the x86 build order in
[`docs/x86-empirical-test-plan.md`](docs/x86-empirical-test-plan.md). Completed work
is not carried here — it is in the operating docs and in `git log`.

## Removal-condition register

Every divergence from the standard workflow carries a removal condition
(`CLAUDE.md`). **A condition nobody re-checks is a divergence that never ends** — and
that has already cost real work: `star_shape_profile.py`'s condition ("retire this
when a tool reports a headless star-shape profile directly") had fired, nothing
re-checked it, and the stale metric went on to invent a false anomaly that a whole
follow-up session was scoped to chase. Re-check this register when a tool version
changes, when the rig changes, and before any item below is worked.

| divergence | condition that retires it | status |
|---|---|---|
| `anomaly_audit.py` in-house streak kernel | a tool provides streak detection / geometry / classification | **not fired** — no Siril command detects or classifies streaks (`cosme`/`find_hot` are defect correction; the `satellite` hit is the annotation catalogue). ASTAP has no such mechanism either. Keep. |
| `compose.py` channel combine (`np.stack` + hand-rolled 3-plane FITS write) | a tool composes channels headless | **FIRED** — Siril `rgbcomp` verified on 1.4.4, and `rgbcomp -lum=` additionally closes the LRGB-join gap. Retirement is open work (item 6). |
| `scripts/qa/star_shape.py` two-frame duplication | Siril exposes a headless single-image tilt, or builds a sequence from one frame | **not fired** — `tilt`/`inspector` are both *"Can be used in a script: NO"*, and Siril cannot build a sequence from a single frame (item 4). |
| `scripts/qa/star_stations.py` fixed-station medians of `findstar` fits | an official tool reports a headless LOCAL star-shape map (region/grid-resolved FWHM/roundness) | **not fired** — `tilt`/`inspector` are GUI-only and whole-frame; `seqtilt` is centre-vs-corners and blind to the drift-aligned band this measure exists for (`docs/dead-ends.md` paraxial-band entry). |
| fitted lensfun entry for the 24-70/4 S @ 70 (`install_lens_model.sh`, replaces the community line) | an upstream lensfun entry measured for THIS unit at infinity focus, or a chain consuming the model another way (`register -disto=` with a trustworthy source) | **not fired** — re-fit (`fit_lens_model.sh`) and re-install per rig, after every `lensfun-update-data`, and on any lens/body/focal change. |
| Hand-rolled FITS parsers (5 sites) | `astropy` available | **FIRED** — astropy 8.0.1 installed on the arm rig; retirement is ARM-DOABLE open work (item 6), not x86-gated. 4 of 5 done (git log); only `compose.py` remains, blocked on a multi-channel dataset. |
| `solve_field.detect_stars` peak centroids | a tool's extractor returns trailed sources *and* measures at least as well | **FIRED** — SExtractor core (`sep`) returns trailed sources, solves at higher odds, and gives identical SPCC K end-to-end (`qa_work/extractor_ab.json`). Default is `--detect=sep`; `--detect=peaks` remains the fallback until the x86 day-1 solve passes on sep, then delete it. |
| GraXpert `-correction Division` synthetic flat | a matching real flat exists for the set | **not fired** — not yet adopted; july14 is flatless by acquisition. |
| Siril-native sky flat (july14) | a matching real flat exists for the set | **not fired** — validated dust-safe for this set; tightening is item 5. |
| `skyflat373` (set-01's sky flat) reused for set-02/03 in the multi-set combine | a per-set flat, or a flat rebuilt from ALL the combine's frames, measured to differ materially (gradient QA + dust) | **FIRED for per-set renders** — measured on set-03 (one-knob A/B, `datasets/july14/set-03/experiments.jsonl` flat_source_set03): the SENSOR content transfers (both flats' falloff shapes agree, corner/centre ~0.45–0.63) but the flat's LOW-ORDER term imprints the SOURCE set's sky gradient — set-03 rendered with set-01's flat carries a ±6% L-R linear tilt that its own flat reduces to ~1–2%. **USER-RATIFIED, divergence ENDED**: a flat calibrates ONLY the exact frames it was built from — cross-set reuse AND any shared/union flat on a combine are banned; combines calibrate each member set with its own flat before composing (item 8 step 3). Wrong-flat artifacts removed; set-01's raws are re-staged on this rig (373 NEF back in `july14/set-01/`), set-02's still need re-staging for any set-02 re-render. |
| `frame_metrics.json` CFA-sampled FWHM | re-measure debayered where disk allows | **not fired** — still the arm rig. Absolute FWHM there is inflated by the Bayer mosaic; only relative comparison is valid. |
| 16-bit stack-time intermediates | RAM/disk headroom to carry 32-bit through stacking | **no condition was ever written** — the reduction is documented in `README.md` but nothing says when it ends. The x86 target (32 GB / 1 TB) removes the reason. Write the condition, then fire it there (item 6). |
| lensfun user-DB strip of this lens's `<vignetting>`/`<tca>` (`install_lens_model.sh`) — darktable ignores a style's lens op_params, so the DB is the only place distortion-only can be enforced | darktable honors a style's lens op_params (or another headless per-invocation param channel) — re-check per darktable version bump with the uniform-card test (warp a uniform card through `lensdist`; corner medians must equal centre) | **not fired** — measured ignored on darktable 5.4.1 (`docs/dead-ends.md`; `datasets/july14/set-01/qa_work/gradient_qa.json`). |
| `run_undistort_groups.sh` group-composition stacking (per-group stacks → compose; one extra interpolation pass) | free disk ≥ the single-pass peak (~231 MB/frame — the x86 1 TB) → use `run_undistort_pipeline.sh` | **not fired** — arm-rig disk is the reason it exists; valid only post-undistort (homographies compose). QUALITY-UNVALIDATED for production: requires the item-7 single-pass-vs-groups A/B (and the in-group rejection ladder) to pass on identical frames first. |

## 1. Derive the config fingerprint from the data

STATUS (core landed): `scripts/lib/fingerprint.py` derives the fingerprint from tool
outputs only — EXIF (`acquisition.py`), astrometry.net solves (`solve_field.py`) and
Siril findstar roundness — computing just the derived trail/drift geometry no tool
reports, and records `datasets/<session>/<set>/fingerprint.json`. It CROSS-CHECKS the
declared mount against the measured sky motion (a fixed mount advances RA at the sidereal
rate, Dec constant; tracked holds both): `mount_verdict` returns CONFIRM / CONTRADICT
(consumer STOPS on a mislabel) / INDETERMINATE. Self-tested against set-01's recorded
numbers (trail 3.41 px, drift 34 px/min, RA 14.99°/hr); set-01 recorded CONFIRM fixed,
set-02 seeded. REMAINS: run the two-window solve per new set to drive the check live
(set-02 pending its solves), and wire the fingerprint into the builders' MATCH→RECOMMEND
preflight (still user-gated — it recommends a route, never auto-executes).

**The pipeline should READ the gathered data and work out what it is**, then organise
processing around that. The route a dataset needs is selected by a config fingerprint
— today "untracked drift at wide focal" — and that fingerprint is DERIVABLE, not
something the user should have to declare.

july14 proves it is derivable; every term below is measured by a tool:

- **In-exposure trail, predicted from EXIF alone:** 15″/s × cos(dec) × exposure ÷
  pixel scale. At 6 s, dec +47, 18.02″/px → **3.40 px**. Siril's per-frame `findstar`
  measures roundness 0.615 (uniform across all 373), implying **~3.6 px**. Agreement
  within 6%. Mild trailing at 6 s is exactly the untracked signature at this focal.
- **Inter-frame drift:** **34 px/min**; two astrometric solves 43 min apart give RA
  advancing **14.99°/hr vs the sidereal 15.041°/hr (0.3%)** with **Dec constant to 7
  arcsec**. A direction fixed in the rotating Earth frame traces a rotation about the
  polar axis: Dec preserved, RA at the sidereal rate. That is a FIXED MOUNT, proven
  from the data.
- So the fingerprint = {exposure, focal, sensor/pixel scale, measured drift rate vs
  sidereal, per-frame roundness} → "untracked, wide, drifting N px/min".

**Why this matters beyond convenience:** `mount` is a DECLARED fact because EXIF
cannot record it, and that rule stays — a consumer must never ASSUME. But a derived
measurement can **CONFIRM or CONTRADICT** the declaration, which is strictly better
than either alone. A set declared `tracked` whose stars drift at exactly the sidereal
rate is a labelling error the pipeline should catch and STOP on, loudly.

Scope: what is derivable vs what must stay declared; how the fingerprint drives the
operating loop's MEASURE → MATCH step; where it is recorded; how a declared-vs-measured
contradiction surfaces. It should not re-litigate the distortion route — that route is
settled and is one fingerprint's answer.

## 2. Make the distortion route a repo process

The route is validated, productionised and scripted (`run_undistort_pipeline.sh`;
[`docs/wide-field-untracked-registration.md`](docs/wide-field-untracked-registration.md)).
Its generality is settled — one style is camera-, lens- and focal-general (the style
carries only its enabled bit; the correction set is enforced at the lensfun DB —
the register's vignetting/tca-strip row); the style and the fitted model are pinned
in-repo and the preflight guard is wired in. What is left is making the repo
RECOMMEND it:

- **Wire it into the loop as the MATCH → RECOMMEND step for this footprint:** take the
  fingerprint (item 1) → check the lensfun DB → recommend the route with its reason (or
  a plain homography, with its reason) → report → user decides → execute → record the
  choice and its trade-off.
- lensfun carries CALIBRATED entries at 24/28/35/50/70 for this lens and interpolates
  between them; confirm interpolated behaviour at an intermediate focal, and that
  `crop=1.0` holds for the body. The FITTED entry covers focal=70 only — any other
  focal rides the community entries until fitted (`fit_lens_model.sh` per focal).
- **The model source is per-rig and per-lens.** A community profile can be right at
  the corner and wrong in the paraxial region (the centre-band mechanism,
  `docs/dead-ends.md`); the route's standard companions are the fit-from-own-frames
  procedure (`scripts/darktable/fit_lens_model.sh` → `install_lens_model.sh`) and the
  drift-axis station measure (`scripts/qa/star_stations.py`) in the class checklist,
  since `seqtilt` cannot see the band.
- **Wire the vignetting-off assertion into `lens_preflight.py --require-profile`:**
  warp a uniform card through `lensdist` and require corner medians == centre via
  Siril `stat`. darktable ignores a style's lens op_params, so the DB strip is the
  enforcement and this card test is its per-run verification — today it is a manual
  step documented in `install_lens_model.sh` (`docs/dead-ends.md` entry). Two bounded limits, by design: the fitted
  entry carries a,b,c only — the centre shift maps to lensfun's `<center>` element,
  which is undocumented (absent from the shipped DTD/XSD) with an unverified sign
  convention, so it enters only as a separately-bracketed knob if a set shows band
  residue, carrying a lensfun-version-bump removal condition; and the preflight
  cannot catch lensfun fuzzy-matching a correct EXIF string to a wrong-but-present
  DB entry — the station measure is the backstop.

## 3. Culling — decided and recorded; no render has consumed it yet

The per-set decision is RATIFIED and recorded in each set's `recipe.json`
stack block (exclusions with per-frame reasons; assessed keeps recorded the
same way), and both undistort builders consume `stack.exclude`. Open: the
first full-depth render that applies it closes this item.

**Per-set culling policy (user-ratified; drivers `scripts/qa/anomaly_audit.py` +
`scripts/qa/run_frame_qa.sh`):** run the anomaly audit per set and cull
aircraft-classified frames; cull a set's FIRST and LAST frame when either is
anomaly-flagged or QA-degraded (session-edge frames carry settle/handling risk);
cull a QA-flagged frame whose degradation is FRAME-WIDE (verified against a
neighbour frame in fixed quadrants — the vibration/wind class).
Everything else goes to the user as a full frames-with-objects list + the cull
report for an explicit per-set call, recorded in the set's `recipe.json` stack
block with its reason. Satellites are not culled by default — a moving minority
trail stacks clean through `rej 3 3` (dead-end registry); they are listed, not
excluded.

- **Frame selection has been disk-bound, not chosen.** The approved render (168 of
  373 by even stride, the disk ceiling; `run_undistort_pipeline.sh --frames=`)
  is quality-blind and **includes DSC_6900** — the frame flagged worst on all three
  axes — while the 54-frame A/B arms excluded all four by luck. Disk pressure
  silently became frame selection. A full-depth render must use ALL frames plus an
  EXPLICIT culling decision.
- **The likely right answer is still "keep all", but it must be decided and recorded.**
  The spread is tiny — worst FWHM 3.857 vs median 3.634 (6.1%), background flat to
  0.35%, 98% of frames within ±2% of median FWHM — and the dead-end registry already
  holds that dropping a minority subset buys no matching gain and pays the full √N
  noise penalty, and that wFWHM weighting at low spread is WORSE than none.
- **Re-assess after the warp, not before.** The distortion correction made 2
  previously-unmatchable frames register (52/54 → 54/54), so frames that would have
  been culled as match failures are now usable. Any cull computed on un-warped frames
  measures the wrong pipeline.
- Decide + record per set (accept/reject each candidate with its reason) in the
  per-dataset record, so "keep all" is a ratified choice rather than a default.

## 4. RESOLVED — chunked front ends guard a remainder of 1

**Siril cannot build a sequence from a SINGLE frame** (`convert`/`link` write the .fit
but no .seq → the next sequence command dies `No sequence 'x' found`). A chunked front
end whose frame count leaves a remainder of exactly 1 hits this on its last chunk.
Guarded UP FRONT, before any warping, in BOTH chunked builders:
`run_undistort_pipeline.sh` asserts `FRAMES % CHUNK != 1`; `run_undistort_groups.sh`
asserts every group size it will use at plan time (a base-size offender would otherwise
die only at group REM+1, hours into warping — e.g. 1865 frames at `--group=14 --chunk=12`
→ base size 13). Verified on Siril 1.4.4 (1-frame `link` → no .seq) and by good/bad
plan-time cases. Never drop `set -e` to "get past it" — that silently produces a short stack.

The same limitation forces the two-frame duplication in `scripts/qa/star_shape.py`.

## 5. Sky-flat tightening

The Siril-native sky flat is the recommended flat for this flatless set and is
validated dust-safe ([`docs/synthetic-flats-and-bias.md`](docs/synthetic-flats-and-bias.md)).
(The large stack-level bright-corner bowl is the warp stage's vignetting
double-correction, fixed at the lensfun DB — `qa_work/gradient_qa.json`; this
flat's own residuals are the smaller figures in `skyflat_qa.json`.) Before the
flat enters another stack, tighten:

- ~~winsorized/sigma rejection instead of pure median~~ — DONE in
  `build_sky_flat.sh` (`--rej=wins` default): specks measured 101 (median 373-flat)
  → 0 (winsorized set-03 flat);
- ~~dark-subtract the lights before building the flat~~ — pinned in the builder
  (the 373 production flat already did);
- smooth the flat to radial-only so division corrects vignetting without flattening the
  low-order sky/IFN gradient (leave that to the first-degree `subsky 1` step) — OPEN,
  and now in tension with a measured result: in a chain with NO background stage, the
  own-flat's MATCHED low-order term is precisely what removed set-03's ±6% tilt
  (flat_source_set03). Settle radial-only TOGETHER with the item-7 background-step A/B,
  not alone;
- the deciding test is a with/without comparison on full-frame lossless finals, with
  dust preservation the metric (the user's eyes) — the set-03 pair
  (`judge/set-03_full_spcc-linked.png` vs `judge/set-03_ownflat_spcc-linked.png`)
  is staged for exactly this call.

Rebuilding it from all ~1865 frames (item 8) directly addresses the star specks — more
frames reject better. GraXpert `-correction Division` stays the vignetting-only
fallback. A real matching flat retires the whole branch.

**Cross-set flat question — SETTLED: per-set flats, user-ratified.** The per-set A/B
(`flat_source_set03`) measured the mismatch the old hypothesis missed: a sky flat's
low-order term imprints its SOURCE set's sky gradient (±6% L-R tilt on set-03 under
set-01's flat; ~1–2% under its own; sensor content transfers, the sky term does not —
`docs/dead-ends.md`). **RULE (user-ratified): a flat calibrates ONLY the exact frames
it was built from** — no cross-set reuse, no single-set or union flat on a combine; a
multi-set render calibrates each member set with its OWN flat BEFORE composing. Any
future combine re-render therefore needs each member set's raws (set-01's are
re-staged on this rig; set-02's are not — re-stage from the originals, or build on
x86).

## 6. Retire the reinventions whose replacements are confirmed

- **Retire the last hand-rolled FITS parser (`compose.py`) → `astropy` — BLOCKED on data.**
  astropy 8.0.1 is installed and probed on the rig; it is the identical tool on both rigs,
  so the method transfers to x86 unchanged. Done (git log, each verified
  byte-behaviour-equivalent): `solve_field.py` (same solve + SPCC K),
  `scripts/lib/astrometrics.py` (byte-identical data + solve), `scripts/calibrate/spcc_cone.py`
  (field/cone identical), `scripts/stack/fitsmeta.py` (metadata line identical). Only
  `compose.py` remains — `read_fits_raw()` + the `np.stack` 3-plane FITS write →
  `astropy.io.fits`, retired jointly with the `rgbcomp` combine swap below. It is verifiable
  only on a dual-band / mono-filter set (none staged), so retire it at first contact,
  verified byte-behaviour-equivalent FIRST.
  Gotchas: write float32 directly (BZERO/BSCALE auto-scale off); numpy `[y,x]` ↔ FITS
  NAXIS reversed; `WCS(header, naxis=2)` on an RGB cube; astropy reads Siril's 16-bit RGB
  FITS directly (retires the `savetif`+`tifffile` read workaround). Each swap lands as a
  declared delta; the removal-register row is FIRED.

- **`compose.py` channel combine → Siril `rgbcomp`.** The member ALIGN is already Siril;
  only the combine is in-house. `rgbcomp chR chG chB -out=` produces a 3-plane float32
  RGB FITS, and **`rgbcomp -lum=`** runs the LRGB join headless — which also closes the
  long-standing LRGB gap `compose` currently REFUSES. `compose` shrinks to: resolve
  `composition.json` → drive the Siril align → `rgbcomp`. Blocked on real data: the swap
  is testable only on a dual-band / mono-filter set (none staged) — implement + verify
  at first contact, never swap untested. Open: the CLI `-lum` blend colour space is
  undocumented (GUI offers HSL/HSV/Lab).
- **Write the missing removal condition for the 16-bit stack-time intermediates**, then
  fire it on x86. The quantization was measured ≈18× below per-frame noise (~+0.3% stack
  noise) and was forced by the arm rig's RAM/disk; 32 GB / 1 TB removes the reason. Note
  the shipped july14 stacks are `BITPIX=16` for this reason.

## 7. Open questions with a named test

- **Group composition vs single-pass — the architecture A/B.** Same frames, same
  masters, one knob (the architecture): single-pass register+stack vs
  `run_undistort_groups.sh`. Judged on full-frame lossless finals + `seqtilt` +
  drift-axis stations; settles the second-interpolation cost and whether the
  route may ship production stacks. Companion ladder: in-group rejection at
  small n (none / percentile / winsorized) — Siril's docs prescribe percentile
  ≤6 and GESD >50 and are silent between.
- **Background-step LEVEL: per-frame vs on-stack `subsky 1`.** The dead-end
  registry records "per-frame subsky 1 is the MW-safe background step;
  stack-level-only leaves a structured residual" (measured on an earlier chain)
  while README's reference-standard row 2 runs gradient removal ON THE STACK —
  a standing contradiction. Settle with a one-knob A/B on a trusted stack
  before the render chain's background stage is built; dust preservation is
  the deciding metric.
- ~~Pin the sky-flat build as a script~~ — LANDED: `scripts/stack/build_sky_flat.sh`
  (recipe verbatim: CFA, dark-subtracted, un-registered, `-norm=mul`; `--rej=wins`
  default per item 5's tightening, `median` kept as the attribution arm; validation
  gates built in: regional `stat`, `findstar` speck count, autostretch preview, qa
  record). First end-to-end run built + validated `skyflat361_set03` (specks 101→0
  vs the median-built flat). Item 5's remaining ladder (radial-only smoothing)
  lands on top of it.
- **`seqapplyreg -framing=min` vs rotation — MEASURED (the named probe ran).**
  The constant-frame coverage probe (`scripts/qa/coverage_probe.sh`; 50 rotated
  members, 01+03 compose): the true all-members common area is **15.25 Mpx**, the
  `-framing=min` canvas kept only **5.50 Mpx (36%)** — min's axis-aligned rectangle
  discards ~2/3 of genuinely full-depth sky when members are mutually rotated
  (measured cost: the NAN complex sat at 50/50 coverage and was cut). Corrective:
  the coverage-thresholded crop (`coverage_threshold_frame_0103`) or the item-12
  hand-crop; the probe is the standing instrument for any rotated compose. Still
  open here: whether min's rule is per-member inscribed axis-rects or another
  heuristic — irrelevant to practice now that the probe measures the truth.

- **Which mechanism drives the RESIDUAL one-sided term.** Siril `seqtilt` measures it;
  the fitted lens model reduced it 0.51 → 0.31 px (16% → 10%) at full depth — that
  fraction was paraxial model error, not tilt. For the 0.31 px remainder the candidates
  stay differential refraction (asymmetric with hour angle) and lens decentering.
  Discriminator: hour-angle dependence across sets — refraction varies with it,
  decentering does not.
- **`solve_field` official-extractor swap — DONE via `sep`; `image2xy` stays an
  optional cross-check.** Measured on the set-01 stack (`qa_work/extractor_ab.json`):
  SExtractor core (`sep` pip package — the same packaging precedent as the pip
  astrometry engine) returns trailed sources, solves at higher odds than the peaks
  arm, and its WCS gives identical SPCC K factors. Default is `--detect=sep`; peaks
  is the labeled fallback until the x86 day-1 solve passes on sep. Open (optional):
  the `image2xy` binary variant (`apt install astrometry.net`) as a second official
  arm — its trail knobs (`-a` fragmentation / `-p` / `-m`) remain the caveats;
  ASTAP is not the answer (roundness-gated by its own docs).
- **Synthetic-flat gap → GraXpert `-correction Division`.** The headless-CPU
  multiplicative option; source-confirmed as per-channel `imarray/background*mean`, i.e.
  divide by the low-frequency model. Corrects smooth VIGNETTING only, not dust/PRNU
  (the model is built from a ~240 px downsample), so a real flat stays the correct fix
  and "a matching real flat exists" is the removal condition. Caveat: the installed
  GraXpert is a third-party fork (`geeksville`); official stable 3.0.2 is
  BGE+denoise-only but does include `-correction Division`. `-cli` is deprecated on
  the fork while official 3.0.x docs treat it as mandatory — build-specific, resolve
  on the pinned official build; `-bg_pts` is not a real flag.
- **A star-colour-neutral colour step.** The O3-sphere mechanism Siril has no single
  command for. Headless path identified, tool half confirmed on 1.4.4: measure mean star
  colour in the examine layer → apply a diagonal `ccm` (the only headless neutral-balance
  path). Run the design against a bracket (SPCC, Nightlight) on x86. Nightlight is a
  dormant mechanism reference only — its `OpRGBBalance` balances the brightest-quartile
  stars; the OIII-lift is our inference (`docs/dead-ends.md`).

## 8. Combine all 5 july14 sets into one deep render (~1865 frames)

STATUS — set-01+02+03 were rendered and combined on the arm base rig. **The route
RUNS but its VALUE is UNCONFIRMED; finish and settle it on the x86 target.** Measured
findings (all x86-portable, since Siril/astrometry/darktable are the identical tools):

- **Re-aim scatter (item 8.2 — `datasets/july14/reaim_scatter.json`).** The re-aims
  worked (each set's field jumps back on the sky; set-01/03 align to 45 px, set-02 is
  ~400 px / 0.8° Dec off). But the `-framing=min` FIELD is ROTATION-limited, not
  re-aim-limited: measured **57% (single) → 42% (2-set) → 24% (3-set, 5.9 Mpx)** as
  field rotation over the ~2.5-h span compounds. The centre-offset 66% estimate was
  optimistic — rotation dominates.
- **DEPTH BENEFIT — FIRST TASK EXECUTED; background σ is measured DEPTH-FLAT (the
  floor is structure, not shot noise).** The normalization-invariant instrument
  (`scripts/qa/snr_regions.py`: internal ratio, Siril `stat` means + `bgnoise`,
  WCS-anchored boxes; record `qa_work/snr_ladder_july14.json`) measured bgnoise
  1.81–1.88 (R) / 2.05–2.24 (G) / 1.77–1.88 (B) ADU across 369 / 361 / ~730-class /
  ~1128-class stacks at matched sky scale (~93–95 ADU; set-01's ~107 scales to ~1.65)
  — √N predicts 0.57× at the deep end and the measured change is ~none. HYPOTHESIS
  (mechanism, untested): the background estimator is floored by DEPTH-INDEPENDENT
  static structure — unresolved-star confusion mottle at 17″/px in Cygnus, plus the
  item-11 sensor-pattern residual — which repeats every frame and cannot average
  down; the random component is already below that floor at ~360 frames. NEXT
  INSTRUMENT (discriminates random vs structural, compose-cheap from existing
  sub-stacks): half-split difference — one registration of a set's sub-stacks, two
  subset means A/B (`select`/`unselect`), `isub` → `bgnoise` on the difference =
  √2 × per-half RANDOM σ (all static structure cancels); compare its √N scaling
  across depths. Matched faint-star photometric SNR is the companion measure. What
  IS measured as depth gains so far: sharper stars (seqtilt off-axis 0.30 → 0.14 →
  0.12), stronger rejection.
  **SPLIT TEST RAN — the depth question CLOSES (scripts/qa/noise_split.sh; records
  in set-04's and set-01's qa_work):** the RANDOM background component scales √N
  exactly (per-half σ 0.64/0.76/0.76 → 0.39/0.46/0.49 ADU, ratios 0.60–0.64 vs the
  predicted 0.594) — the combine IS deeper and the group route injects no excess
  random noise; the VISIBLE background is floored by a depth-independent static
  structure (σ≈1.0/1.5/1.2: unresolved-star confusion texture — real sky — plus the
  item-11 pattern, whose drift-phase component measured 0.34/0.48/0.42 ADU per half
  on set-04). Consequence: more integration keeps buying faint-source SNR at √N,
  but background smoothness is structure-limited at these depths — the pattern part
  is the x86 denoise tier's target; the confusion part is signal.
- **WASHED-OUT render + rainbow streaks — OPEN FLAW, ROOT CAUSE NOT DETERMINED (do not
  reshoot; INVESTIGATE).** MEASURED SYMPTOMS ONLY: the combines stretch washed-out; the
  3-set combine has a ~4% centre→corner linear gradient vs a single set's ~1%, and the
  auto-stretch places its background ~2× higher (0.00019 → 0.00038). A stack-level
  `subsky` removed the linear tilt but left/produced bottom-to-top rainbow streaks — that
  was a MISUSE (a per-frame/early step applied to a final stack), not a diagnosis, and it
  is reverted. **The cause of the gradient, the washed-out look, and the streaks is NOT
  established.** Candidate hypotheses, NONE controlled-tested: shared-flat mismatch across
  sets (flat-A/B row), walking noise (item 11), the cross-set registration / second
  interpolation (item 7), or simply no per-frame background stage. NEXT: isolate each
  candidate on the real data (one variable at a time) — e.g. does a per-set (not combined)
  render show the streaks; do they scale with set count; are they present pre-combine.
  Carry NO single cause as settled, and a reshoot is one untested hypothesis, not the fix.
  **First isolation measured (set-03, flat_source_set03):** the shared-flat candidate is
  REAL for the gradient component — set-01's flat imprints a ±6% L-R tilt on set-03's
  per-set render that set-03's own flat removes (linear regional medians); and the
  per-set renders show NO rainbow streaks at fit view or inspected 1:1 zones, so the
  streaks remain combine-associated (or sub-threshold per-set).
  **Second isolation (combine_0103_compliant_flats, set-01's ledger): the shared flat
  was the DOMINANT cause.** A 01+03 compose whose member sets each carry their OWN
  flat measures per-set-class flat (min arm 92–93 ADU all regions, ~1% vs the old
  ~4% class), stretches with NO washout, and shows no streaks or join artifacts at
  inspected zones; its min arm is the project's sharpest stack (seqtilt FWHM 3.02,
  off-axis 0.12). Still open: the depth-benefit SNR measure (normalization-invariant
  instrument), the second-interpolation A/B (item 7), walking noise (item 11), and
  the min-vs-max framing verdict (the user's eyes).
- **Per-set colour (resolved).** Independent per-set SPCC gives different K/levels
  (set-01 K_B 0.911, set-02 0.811, set-03 0.899; background 107/97/95) — expected, since
  each set is a separate calibration. Resolved by SPCC-ing the COMBINE as ONE unit
  (measured neutral R=G=B); never finish per-set.

Tooling that landed this pass, all x86-portable: `run_undistort_compose.sh` (cross-set
sub-stack compose, min/max), `finish_render.sh` (solve → SPCC → linked stretch → 16-bit
PNG), `fingerprint.py` (item 1). The combine stacks/renders and every wrong-flat
artifact (set-02/03 products calibrated with set-01's flat) were REMOVED under the
ratified per-set-flat rule — the findings above stand on their recorded numbers.
Retained: set-01's sub-stacks + stacks (own flat — valid), set-03's own-flat
sub-stacks/stack/render, and the set-03 A/B control stack + render (preserved
experiment artifact, `flat_source_set03`).

july14 is 5 sets of the same object, same workflow, the camera re-centred on the target
every ~45 min. set-01 (373 frames, 43 min) is one such window and is the only set with raws
on this rig; the others stage per-set as they arrive.

**The re-aims cost nothing — the validated route already covers them.** A manual
re-centre is a rotation about the optical centre, and pure rotation with all scene
points at infinity is EXACTLY a homography (Szeliski — the same result that pins the
root cause). Stars are at infinity, so even a translated tripod head adds no parallax.
Once undistorted, a re-aim is indistinguishable from drift: same `register -2pass`, no
new mechanism. Lens distortion is fixed in SENSOR coordinates, so moving the camera does
not invalidate the lensfun warp either. Expect ~5× integration = **~2.24× SNR** over
set-01 alone.

This also retires the fixed-tripod drift wall for this data: the field slides off the
sensor after ~3.0 h at 70 mm (34 px/min measured), so a single 2000-frame untracked
window would have ZERO common area — but each 45-min set sits at 76% field retained. The
re-centring solved it in acquisition.

Depends on items 3 (culling) and 5 (the sky flat); chunking is mandatory here and the
remainder-of-1 guard is now in BOTH undistort builders (item 4). The disk-bound route
per set is the group composition (`run_undistort_groups.sh`), and
`run_undistort_compose.sh` combines the per-set sub-stacks into one cross-set stack
(undistorted sub-stacks compose as homographies — the re-aim is then just more drift).
Prep state: set-01
is prepped and ratified with complete tracked records; sets 02–05 get the same
per-set prep (`run_frame_qa.sh` + the anomaly audit + the cull policy + window
solves) ON THE DESKTOP as they stage. Ordered:

1. **Verify every set's camera+lens+focal, and that ISO/exposure match the darks.**
   set-01 is 70 mm; the others are unverified. This is a **hard
   prerequisite, not a formality**: darktable silently applies NO correction to a lens it
   cannot match and a wrong model to one it mis-matches, so a single set with a different
   or unrecognised lens string would stack uncorrected into the combined result with no
   warning. `lens_preflight.py` (run by the builder) enforces it per set — and the
   FITTED entry covers focal=70 only, so a set at any other focal needs
   `fit_lens_model.sh` for that focal first or it silently rides the community entry
   and reintroduces the centre band.
2. **Measure the re-aim scatter before committing to one combined stack.** `-framing=min`
   keeps only what is common to ALL frames: within a set the drift is ~1500 px, across
   sets it is drift + hand-re-centring error. If scatter is large the common area drops
   below set-01's 76% — fallback is stack-per-set then combine the 5 stacks (worse: 5
   discrete residuals rather than one fit).
3. **Per-set sky flats — the user-ratified rule; no union or shared flat.** Each
   set builds + validates its OWN flat (`build_sky_flat.sh`) and calibrates with it
   before any compose (measured imprint mechanism, `docs/dead-ends.md`; same
   dust-contamination validation gate per flat).
4. **Storage: ~433 GB peak** (1865 × 232 MB uncompressed) for single-pass — comfortable
   on the x86 1 TB; on the arm rig only the group-composition route fits, and it is
   gated on its item-7 quality A/B. No GPU needed — Siril has no GPU path and the AI tier runs
   once per stack, not per frame.

## 9. Data-capability gaps (x86-gated)

Real imaging capabilities the pipeline does not yet have; each lands as a measured
declared delta during the x86 rebuild.

- **Full-size dual-band** — native Ha + 2× drizzle of OIII instead of downsampling OIII
  to Ha's half size, gated on measured dither coverage (the per-frame
  `dither_phase_frac` record already exists).
- **FITS I/O → astropy** (retires 5 hand-rolled parsers: `astrometrics`, `compose`,
  `solve_field`, `spcc_cone`, `fitsmeta`). **astropy
  8.0.1 is installed on the arm rig** (FITS I/O + WCS/SIP + ICRS→Galactic probed
  working), so this is ARM-DOABLE now, not x86-gated — astropy is the identical tool on
  both rigs. Gotchas, primary-verified: write float32 directly so BZERO/BSCALE
  auto-scaling stays off; numpy `[y,x]` ↔ FITS `NAXIS1` reversed
  (`.shape == (NAXIS2, NAXIS1)`); SIP needs `to_header(relax=True)` (default
  `relax=False` OMITS the `-SIP` CTYPE suffix) and `WCS(header, naxis=2)` on an RGB cube.
  astropy reads Siril's 16-bit RGB FITS directly — the `savetif`+`tifffile` read
  workaround is retired.
- **Deconvolution** — a measured dead-end on arm64 data (unstable symmetric PSF on
  in-exposure trailing); BlurXTerminator reopens it on x86 (`--correct-only`).
- **`run_pipeline` auto-routing to a large-sequence path** — largely unnecessary at
  32 GB, but a very large sequence may still want common-reference partitioning; decide
  against the real x86 memory headroom.
- **Under-used Siril natives to adopt opportunistically.** `pm` (PixelMath) is
  scriptable headless — variables need **`$name$` tokens** (the naked-name form errors;
  confirmed on-rig), ≤10 input images per expression. `seqstat seq out.csv
  {basic|main|full}` and `seqheader seq KEY… -out=file.csv` emit clean headless CSVs
  beyond the `register` regdata `inspect_stage` already pulls. **Caveat `seqpsf`/`psf`:**
  the PSF-fit photometry is real but headless CSV is not a documented flag (docs say it
  console-prints; the GUI's "Export to CSV" is GUI-only) — capturing it means
  log-parsing; test before relying on it. Note Siril's **"roundness" = FWHMy/FWHMx, not
  eccentricity** — use the right term.

## 10. Siril 1.5.0-dev — pre-register before the x86 upgrade

1.4.4 is current stable; 1.5.0 is unreleased (dev master). Nothing to adopt today; three
things to plan for when the x86 rig moves.

- **Native image-mask subsystem** — 12 `mask_*` commands plus a `-mask` flag on
  `denoise`/`rmgreen`/`epf`/`rl`/`sb`/`wiener` and a Python mask API. The first NATIVE
  path to region-confined ops (e.g. denoise the starless/background only) without a
  hand-rolled mask blend — squarely in bounds; adopt for the render on 1.5.0. (`-mask`
  is dev-only; absent from 1.4.4, confirmed.)
- **`healpix` / `eqcrop`** — `healpix` lists the NESTED HEALPix pixels (Nside=2 / 256)
  overlapping a plate-solved image: exactly the cover `scripts/calibrate/spcc_cone.py`
  hand-rolls, so it is that script's retirement candidate. Needs an empirical check that
  its pixel list maps to the zenodo chunk filenames the fetcher expects. `eqcrop ra1
  dec1 ra2 dec2` is an RA/Dec-box crop (coordinate-defined, reproducible framing).
- **MIGRATION RISK: `starnet`/`seqstarnet` are REMOVED in 1.5.0-dev** — consolidated
  behind `pyscript StarNet.py`. Capability kept, command surface gone: any `.ssf` or
  template calling them must migrate before a 1.5.0 bump. Also: `sb` deconv is **Split
  Bregman** — correct any doc naming it otherwise.

## 11. Walking noise in the wide-untracked data — OPEN gap

Faint DRIFT-ALIGNED streaks the user sees at native 1:1, below whole-frame statistics
— a sensor-fixed pattern (electronic-shutter readout FPN + residual hot/warm pixels)
dragged into lines by the coherent, un-dithered drift. **Measured NULLs
(`experiments.jsonl`):** `-cc=dark` cosmetic correction (`cc_dark_warped_spcc`) and
GESD-vs-winsorized rejection (`reject_gesd_vs_winsorized`) — neither removes it,
because the streaks are a sub-sigma structured pattern, not discrete rejectable
outliers. **Possible (UNPROVEN) link to the multi-set combine (item 8):** the combine's
whole-frame bgnoise did not visibly drop across 369 → 1032 frames — but that read is
confounded (`-output_norm`), and the rainbow streaks seen on a stack-`subsky`'d combine
could equally be an artifact of that misapplied step. Neither the combine's depth
shortfall nor the streaks has been TRACED to walking noise by a controlled test; treat
this as a hypothesis to investigate (item 8), not a finding. **Untried levers, to test on the existing data:** (1) whether the master
dark captures the electronic-shutter pattern — check the darks' shutter mode / re-shoot
matched darks and rebuild; (2) directional/pattern removal aligned to the measured
174.4-deg drift axis, or an AI denoiser (x86) weighed against dust preservation (a
bandaid, last resort). The go-forward acquisition fix is unsettled — do NOT assume a
shutter-mode change removes it. OPEN gap, not a dead-end.
**First direct quantification (noise_split.sh, set-04):** the drift-phase
structured component — the walking-noise-class power — measures ≈0.34/0.48/0.42
ADU (R/G/B) per ~199-frame half (timehalf-vs-interleaved split excess), i.e.
roughly a third of the total static-structure budget (≈1.0/1.5/1.2 ADU, the rest
being unresolved-star confusion texture) and comparable to the random noise left
at that depth. The x86 denoise tier now has a measured target size.

## 12. Hand-crop framing via web browser — the user draws the final frame

Framing is a COMPOSITION judgment and belongs to the user, not to the mechanical
extremes: `-framing=min` is the binary intersection (measured discarding sky
covered by ALL 50 sub-stacks — the NAN sat at 50/50 coverage and was still cut),
`max` is the raw union with single-coverage rims, and the coverage-threshold crop
(`coverage_threshold_frame_0103`) is instrument-driven but still machine-chosen.
Build the mechanism that captures the user's own frame and makes it THE framing:

- **UI**: a local, browser-only page (no external service) that displays the
  union/max judgment surface (a downscale is fine for panning — it is a SELECTION
  surface, never a judgment surface) with the per-pixel coverage map overlaid as
  ≥N contours (the Siril constant-frame probe, `scripts/qa/coverage_probe.sh`),
  so the choice is depth-informed. The user drags/adjusts one rectangle.
- **Record is the product**: the chosen box is saved to the tracked per-product
  record (native-pixel box + WCS RA/Dec corners from the solved stack, so the
  framing survives re-registration and canvas changes) — nothing renders from an
  unrecorded box. The UI captures a human decision; it never touches pixels.
  **Coordinate export MUST be stat-verified**: Siril `crop`'s y-origin is the
  opposite end from numpy/FITS row order (y_siril = H − y_np − h — measured: an
  unverified export shipped a zero-coverage wedge); crop the coverage MAP with
  the same args and require the stat to hold before any product crop.
- **The chain consumes it**: the render chain applies the recorded crop to the
  LINEAR stack (Siril `crop`; crop-before-stretch doctrine) on every rebuild.
  Siril 1.5's `eqcrop ra1 dec1 ra2 dec2` (item 10) is the natural consumer of the
  RA/Dec form when the x86 rig lands on 1.5.
- **Close condition**: a box drawn on the 01+03 union renders through the chain
  to a final whose framing matches the drawn box, and the record reproduces that
  framing after a stack rebuild (RA/Dec-anchored). The `cov25` crop from
  `coverage_threshold_frame_0103` is the machine-chosen precursor whose
  record+Siril-crop plumbing this item reuses — only the rectangle CHOICE moves
  to the user's hand.
