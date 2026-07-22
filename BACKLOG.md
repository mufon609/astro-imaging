# BACKLOG

What is queued, why it matters, and what gates it — ordered. Each item states the
mechanism and the test that would close it, not a narrative.

Where things live: mechanism lessons + the acquisition checklist in
[`docs/dead-ends.md`](docs/dead-ends.md); the toolkit in [`TOOLS.md`](TOOLS.md);
per-dataset state under `datasets/<session>/<set>/`; the user-gated render-tier
plan for THIS rig in
[`docs/render-tier-arm-plan.md`](docs/render-tier-arm-plan.md); the x86 build
order in
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
| `anomaly_audit.py` in-house streak kernel | a tool provides streak detection / geometry / classification | **not fired** — no Siril command detects or classifies streaks (`cosme`/`find_hot` are defect correction; the `satellite` hit is the annotation catalogue). ASTAP has no such mechanism either. Keep. **Known miss mode (user-caught):** the set-02 aircraft's ENTRY frame (DSC_7573) was not linked to the object — 2 of 3 crossing frames classified; the entry frame's own QA z-signature carried the signal (roundness z −16.7 with nstars z +5.9 = elongated EXTRA detections). Standing check: an extreme-elongation QA flag ADJACENT to an audited crossing is the same object until shown otherwise. |
| `compose.py` channel combine (`np.stack` + hand-rolled 3-plane FITS write) | a tool composes channels headless | **FIRED** — Siril `rgbcomp` verified on 1.4.4, and `rgbcomp -lum=` additionally closes the LRGB-join gap. Retirement is open work (item 6). |
| `scripts/qa/star_shape.py` two-frame duplication | Siril exposes a headless single-image tilt, or builds a sequence from one frame | **not fired** — `tilt`/`inspector` are both *"Can be used in a script: NO"*, and Siril cannot build a sequence from a single frame (item 4). |
| `scripts/qa/star_stations.py` fixed-station medians of `findstar` fits | an official tool reports a headless LOCAL star-shape map (region/grid-resolved FWHM/roundness) | **not fired** — `tilt`/`inspector` are GUI-only and whole-frame; `seqtilt` is centre-vs-corners and blind to the drift-aligned band this measure exists for (`docs/dead-ends.md` paraxial-band entry). |
| fitted lensfun entry for the 24-70/4 S @ 70 (`install_lens_model.sh`, replaces the community line) | an upstream lensfun entry measured for THIS unit at infinity focus, or a chain consuming the model another way (`register -disto=` with a trustworthy source) | **not fired** — re-fit (`fit_lens_model.sh`) and re-install per rig, after every `lensfun-update-data`, and on any lens/body/focal change. |
| Hand-rolled FITS parsers (5 sites) | `astropy` available | **FIRED** — astropy 8.0.1 installed on the arm rig; retirement is ARM-DOABLE open work (item 6), not x86-gated. 4 of 5 done (git log); only `compose.py` remains, blocked on a multi-channel dataset. |
| `solve_field.detect_stars` peak centroids | a tool's extractor returns trailed sources *and* measures at least as well | **FIRED** — SExtractor core (`sep`) returns trailed sources, solves at higher odds, and gives identical SPCC K end-to-end (`qa_work/extractor_ab.json`). Default is `--detect=sep`; `--detect=peaks` remains the fallback until the x86 day-1 solve passes on sep, then delete it. (Optional second official arm, untested: the `image2xy` binary — shape-blind, but its trail knobs `-a`/`-p`/`-m` are unexposed by solve-field and `-a` can fragment a rippled trail; ASTAP is NOT an arm — roundness-gated by its own docs.) |
| GraXpert `-correction Division` synthetic flat | a matching real flat exists for the set | **not fired** — not yet adopted; july14 is flatless by acquisition. |
| Siril-native sky flat (july14) | a matching real flat exists for the set | **not fired** — validated dust-safe for this set; tightening is item 5. |
| `frame_metrics.json` CFA-sampled FWHM | re-measure debayered where disk allows | **not fired** — still the arm rig. Absolute FWHM there is inflated by the Bayer mosaic; only relative comparison is valid. |
| 16-bit stack-time intermediates | a rig whose RAM/disk carries 32-bit through stacking end-to-end (the x86 32 GB / 1 TB target): drop `set16bits`, re-measure stack noise vs the 16-bit path, land as a declared delta | **not fired** — arm RAM/disk forced it; the quantization is measured ≈18× below per-frame noise (~+0.3% stack noise) and the shipped july14 stacks are BITPIX=16 under it. |
| lensfun user-DB strip of this lens's `<vignetting>`/`<tca>` (`install_lens_model.sh`) — darktable ignores a style's lens op_params, so the DB is the only place distortion-only can be enforced | darktable honors a style's lens op_params (or another headless per-invocation param channel) — re-check per darktable version bump with the uniform-card test (warp a uniform card through `lensdist`; corner medians must equal centre) | **not fired** — measured ignored on darktable 5.4.1 (`docs/dead-ends.md`; `datasets/july14/set-01/qa_work/gradient_qa.json`). |
| `run_undistort_groups.sh` group-composition stacking (per-group stacks → compose; one extra interpolation pass) | free disk ≥ the single-pass peak (~231 MB/frame — the x86 1 TB) → use `run_undistort_pipeline.sh` | **not fired** — arm-rig disk is the reason it exists; valid only post-undistort (homographies compose). QUALITY-UNVALIDATED for production — and the APPROVED full-session render rode this route, so the item-7 single-pass-vs-groups A/B (plus the in-group rejection ladder) is now the standing validation DEBT on the deliverable, payable on x86 disk. |
| 5-set combine via TWO interleaved-half composes + a 2-member `-weight=nbstack` join (the 107-sub single-registration max compose needs ~37G transient vs ~24G reclaimable on this rig) | x86 disk → re-compose all 107 sub-stacks in ONE registration (every `groups_*` dir is kept for exactly this) | **not fired** — declared cost: the non-reference half carries one extra interpolation; halves span all five sets (interleaved), STACKCNT propagates exact frame weights (794+781=1575); the join landed natively in the cov25 orientation family. The 5-member per-set-stack shortcut is a measured dead-end (pre-cropped members — registry). |

## 0. THE RENDER-TIER BUILD — user-gated, starts on THIS rig

The one open product gap. The approved deliverable
(`july14-all5-cov25frame-approved`) ends at a diagnostic `autostretch
-linked`; the real render tier is UNBUILT — a POLICY gap (the user gates every
output-shaping run), not a rig gap: the full Siril native render surface is
probed present + scriptable on this arm rig, and only the neural/separation
x86-64 binaries are environment-blocked (per-tool evidence: `TOOLS.md`).

**The pre-registered plan is [`docs/render-tier-arm-plan.md`](docs/render-tier-arm-plan.md)**
— ladder sequence L1 background-level A/B (item 7's named test) → L2 linear
denoise (Siril native vs installed GraXpert; objective target = the measured
drift-phase structured term 0.34–0.48 ADU/half) → L3 GHS stretch ladder
(replaces the diagnostic autostretch) → L4 thresholded satu; one knob per
experiment, hypotheses pre-registered, judged on full-frame lossless PNG16,
STOPPED at the user's gate. Riding on completion: re-seed
`datasets/GENERIC.json` + recipe `render` blocks, first `baseline.json` via
the no-regression harness, `finish_render.sh`'s stretch stage swap, and the
`judgment_package.py` re-wire (its PNG8 pairing predates the 16-bit-only
judgment policy; its `.metrics.json` producer — the wiped chain's renderer —
must be replaced by the new chain's stage records). Close condition: an
approved, re-baselined, tagged render from the new tier.

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

_(Items **3** — per-set culling, ratified + CONSUMED by the approved
1575-frame render — and **4** — the remainder-of-1 guards, built into both
chunked builders — are CLOSED; item **8** below likewise. Mechanisms live in
the builders' docstrings, the per-set recipes and `docs/dead-ends.md`; full
text in git. Numbering is preserved so cross-references stay valid.)_

## 5. Sky-flat tightening

The Siril-native sky flat is the recommended flat for this flatless set and is
validated dust-safe ([`docs/synthetic-flats-and-bias.md`](docs/synthetic-flats-and-bias.md)).
(The large stack-level bright-corner bowl is the warp stage's vignetting
double-correction, fixed at the lensfun DB — `qa_work/gradient_qa.json`; this
flat's own residuals are the smaller figures in `skyflat_qa.json`.) Before the
flat enters another stack, tighten:

- smooth the flat to radial-only so division corrects vignetting without flattening the
  low-order sky/IFN gradient (leave that to the first-degree `subsky 1` step) — OPEN,
  and in tension with a measured result: in a chain with NO background stage, the
  own-flat's MATCHED low-order term is precisely what removed set-03's ±6% tilt
  (flat_source_set03). Settle radial-only TOGETHER with the item-7 background-step
  A/B (= the render plan's L1, `docs/render-tier-arm-plan.md`), not alone;
- the deciding test is a with/without comparison on full-frame lossless finals, with
  dust preservation the metric (the user's eyes) — the set-03 pair
  (`judge/set-03_full_spcc-linked.png` vs `judge/set-03_ownflat_spcc-linked.png`)
  is staged for exactly this call.

Rebuilding it from all ~1865 frames (item 8) directly addresses the star specks — more
frames reject better. GraXpert `-correction Division` stays the vignetting-only
fallback. A real matching flat retires the whole branch.

Cross-set flat question — SETTLED (user-ratified per-set-flat rule; mechanism +
numbers in `docs/dead-ends.md`, ledger `flat_source_set03`). Operational residue
only: a combine re-render needs each member's raws — set-01's are staged on this
rig, set-02's are not (re-stage from originals, or build on x86).

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
- The 16-bit stack-time intermediates' removal condition is now WRITTEN in the
  register above (fire it on x86: drop `set16bits`, re-measure, declared delta).

## 7. Open questions with a named test

- **Group composition vs single-pass — the architecture A/B.** Same frames, same
  masters, one knob (the architecture): single-pass register+stack vs
  `run_undistort_groups.sh`. Judged on full-frame lossless finals + `seqtilt` +
  drift-axis stations; settles the second-interpolation cost and whether the
  route may ship production stacks. Companion ladder: in-group rejection at
  small n (none / percentile / winsorized) — Siril's docs prescribe percentile
  ≤6 and GESD >50 and are silent between.
- **Background-step LEVEL: per-frame vs on-stack `subsky 1` — now the render
  plan's L1** ([`docs/render-tier-arm-plan.md`](docs/render-tier-arm-plan.md)),
  pre-registered and user-gated. The doctrine fork it settles: Siril's own docs
  recommend per-frame degree-1 for session-rotated gradients (this dataset's
  exact geometry) while the general default is once-on-the-stack; the registry
  holds the same fork from the pre-reset chain. Dust preservation is the
  deciding metric; the SPCC K delta is the free order-robustness check.
- **Which mechanism drives the RESIDUAL one-sided term.** Siril `seqtilt` measures it;
  the fitted lens model reduced it 0.51 → 0.31 px (16% → 10%) at full depth — that
  fraction was paraxial model error, not tilt. For the 0.31 px remainder the candidates
  stay differential refraction (asymmetric with hour angle) and lens decentering.
  Discriminator: hour-angle dependence across sets — refraction varies with it,
  decentering does not.
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

## 8. CLOSED — the 5-set combine is rendered and APPROVED

The full-session combine (1575 frames at the cov25 frame) PASSED the user's
eyes — tag `july14-all5-cov25frame-approved`. Everything durable from this
item graduated: the compose/rejection/framing dead-ends and the coverage-probe
instrument to `docs/dead-ends.md` + `TOOLS.md`; the depth question CLOSED by
the split test (random noise scales exactly √N; the visible floor is static
structure — item 11 carries the structured part, the render plan's L2 targets
it); the washout root cause was the shared flat (per-set-flat rule, ratified);
per-set colour resolved by one-unit SPCC on the combine. Standing residue
lives where it belongs: the x86 single-registration re-compose + the
groups-route validation debt in the removal register, framing-by-the-user in
item 12, the formal `baseline.json` in item 0's harness. Full narrative in git.

## 9. Data-capability gaps (gated per item — read each gate)

Real imaging capabilities the pipeline does not yet have; each lands as a measured
declared delta when its gate opens.

- **Full-size dual-band** — native Ha + 2× drizzle of OIII instead of downsampling OIII
  to Ha's half size, gated on measured dither coverage (the per-frame
  `dither_phase_frac` record already exists).
- **FITS I/O → astropy** — the last parser (`compose.py`) and its gotchas live in
  item 6 + the removal register (ARM-doable, data-gated on a multi-channel set).
- **FITS-path `setfindstar` asymmetry** (audit-found): the raw-camera template
  lowers detection to `-sigma=0.5` (measured: the matcher needs the extra
  triangles on this class) but the FITS `_fits_lights`/`_fits_dualband` paths
  register at the default sigma. Mechanism: the two paths were built from
  different data classes. Named test: on the first FITS-class set, a one-knob
  registration ladder (default vs `-sigma=0.5`) — adopt per measured
  match-rate, never by symmetry alone.
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

**The render plan's L2 denoise ladder targets this defect's drift-phase term**
(`docs/render-tier-arm-plan.md`: objective instrument = the set-04 half-split
re-run on denoised halves; target 0.34/0.48/0.42 ADU/half). L2 treats the
SYMPTOM budget; the acquisition-side mechanism work below stays open either
way (a denoiser must never be this defect's only answer — bandaid rule).

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

**STATUS — the capture side AND the site shell are BUILT (`web/`); the consume
side rides item 0.** Landed: `web/serve.py` (127.0.0.1-only static server +
the framing POST + `GET /api/session/<name>`, the read-only joined session
model: per-set records normalized for display, surfaces with recipe-vs-header
frame-count confirmation from FITS metadata, approvals from git tags only),
`web/index.html` (the shell: rail-routed pages — per-set Frames
decision/confirmation, culled rollup, surfaces, sky objects, experiments,
framing, records viewer; absent artifacts render as designed states),
`web/crop.html` (draws the rectangle over a Siril-made selection preview with
existing `*_map.json` reference boxes overlaid, plus the coverage-veil toggle
when a map's canvas matches), `web/make_previews.sh`
(tool-driven previews + manifest, including the coverage-veil class),
`web/verify_framing.py` (the mandatory
Siril crop+stat verification — coverage-map `Min >= members*1000` or the
sibling-class sky-floor mode; a render must refuse an unverified record),
and the **Tier-1 execution surface** (user-ratified amendment in
`web/README.md`): `/api/stages` + `/api/run` — a fixed registry of the
pinned scripts run one-at-a-time from an explicit per-click DECIDE gate,
exact command shown before the run, logs under `sessions/.webjobs/`.
Deliberately NOT in the registry yet: `coverage_probe.sh` (heavy,
variable-membership args) and any render-tier stage (item 0, user-gated). The
record (`datasets/<session>/framing_<product>.json`) carries BOTH coordinate
conventions (screen top-left AND Siril bottom-left — the measured y-flip trap)
plus WCS RA/Dec corners so the framing survives re-registration.

Open, in order:
- **Coverage overlay as ≥N contours in the UI** — the MAP for the 4-set max
  canvas now EXISTS (`web/results/july14/coverage_01345_max.fit`, 8493×6428 ==
  the product, STACKCNT 87; rebuilt from the stored probe registration —
  record + the probe's measured limits:
  `datasets/july14/set-01/qa_work/coverage_01345.json`; values clip at the
  65-member ceiling, thresholds ≤65 valid). Remaining: render it to a
  tool-made ≥N preview PNG for crop.html (Siril `pm` threshold + `savepng`,
  manifest-recorded); the all-5 map still needs the x86 single-registration
  re-compose (its members exceed one pass on this rig).
- **The chain consumes it**: the render chain applies the recorded, VERIFIED
  crop to the LINEAR stack (Siril `crop`; crop-before-stretch doctrine) on
  every rebuild — wired into the render-tier build (item 0). Siril 1.5's
  `eqcrop ra1 dec1 ra2 dec2` (item 10) is the natural consumer of the RA/Dec
  form when the x86 rig lands on 1.5.
- **Close condition** (unchanged): a box drawn on a union surface renders
  through the chain to a final whose framing matches the drawn box, and the
  record reproduces that framing after a stack rebuild (RA/Dec-anchored). The
  `cov25` crop is the machine-chosen precursor whose record+Siril-crop
  plumbing this reuses — only the rectangle CHOICE moves to the user's hand.
