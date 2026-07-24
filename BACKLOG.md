# BACKLOG

What is queued, why it matters, and what gates it — ordered. Each item states the
mechanism and the test that would close it, not a narrative.

Where things live: mechanism lessons + the acquisition checklist in
[`docs/dead-ends.md`](docs/dead-ends.md); the toolkit in [`TOOLS.md`](TOOLS.md);
per-dataset state under `datasets/<session>/<set>/`; the render-tier ladder
skeleton in item 0 (re-anchored per dataset by the operating loop); the x86 build
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

**Exemplar status:** the ORIGINAL july14 processing records + finals (the source
of many measures cited below — `gradient_qa.json`, `registration_qa.json`,
`flat_source_set03`, etc.) were WIPED from the working tree on user order; git
history + the approved tag (`july14-all5-cov25frame-approved`) hold the full
record. july14 has since been REPOPULATED as the live dataset (the full real
acquisition under correct server naming — set-00…set-05 + darks — at
`sessions/july14/`, with the x86 set-01 lens work + the realigned set-04/set-05
records under `datasets/july14/`; the earlier `july14_fresh-start` scaffold name
is retired). So a cited record path resolves to the current dataset's lineage but
the specific wiped file is historical: those measured mechanisms stand as lessons,
and a row's numbers re-verify when that set is re-processed here.

| divergence | condition that retires it | status |
|---|---|---|
| `anomaly_audit.py` in-house streak kernel | a tool provides streak detection / geometry / classification | **not fired** — no Siril command detects or classifies streaks (`cosme`/`find_hot` are defect correction; the `satellite` hit is the annotation catalogue). ASTAP has no such mechanism either. Keep. **Known miss mode (user-caught):** the set-02 aircraft's ENTRY frame (DSC_7573) was not linked to the object — 2 of 3 crossing frames classified; the entry frame's own QA z-signature carried the signal (roundness z −16.7 with nstars z +5.9 = elongated EXTRA detections). Standing check: an extreme-elongation QA flag ADJACENT to an audited crossing is the same object until shown otherwise. |
| `scripts/qa/star_shape.py` two-frame duplication | Siril exposes a headless single-image tilt, or builds a sequence from one frame | **not fired** — `tilt`/`inspector` are both *"Can be used in a script: NO"*, and Siril cannot build a sequence from a single frame (item 4). |
| `scripts/qa/star_stations.py` fixed-station medians of `findstar` fits | an official tool reports a headless LOCAL star-shape map (region/grid-resolved FWHM/roundness) | **not fired** — `tilt`/`inspector` are GUI-only and whole-frame; `seqtilt` is centre-vs-corners and blind to the drift-aligned band this measure exists for (`docs/dead-ends.md` paraxial-band entry). |
| fitted lensfun entry for the 24-70/4 S @ 70 (`install_lens_model.sh`, replaces the community line) | an upstream lensfun entry measured for THIS unit at infinity focus, or a chain consuming the model another way (`register -disto=` with a trustworthy source) | **not fired** — re-fit (`fit_lens_model.sh`) and re-install per rig, after every `lensfun-update-data`, and on any lens/body/focal change. x86: **re-installed** (`install_lens_model.sh` replaced the community focal=70 line and stripped 55 vignetting/tca entries) and PROVEN to correct real frames (`qa_work/lens_preflight.json`, Siril stat max 63446 over 373 frames). The per-rig **RE-FIT is DONE and CONFIRMS the incumbent**: hugin 2025.0.1 on set-01 (solved hfov 30.4421°, dark+sky-flat calibrated, residual 0.29→0.02 px mean with a,b,c) fitted a=0.0033627/b=0.0149465/c=0.0005744 — sub-pixel-equivalent to the carried-over arm fit (a,b within 3-4%; max displacement diff 0.47 px mid-field, 0.34 px area-weighted RMS; 0.2 px at r=0.9). Difference is within fit noise; the arm-era model STANDS (re-installing the lateral new fit would change the production deliverable by ≤0.47 px with no measured benefit). `qa_work/lens_fit.json`. |
| `solve_field.detect_stars` peak centroids | a tool's extractor returns trailed sources *and* measures at least as well | **FIRED** — SExtractor core (`sep`) returns trailed sources, solves at higher odds, and gives identical SPCC K end-to-end (`qa_work/extractor_ab.json`). Default is `--detect=sep`; `--detect=peaks` remains the fallback until the x86 day-1 solve passes on sep, then delete it. (Optional second official arm, untested: the `image2xy` binary — shape-blind, but its trail knobs `-a`/`-p`/`-m` are unexposed by solve-field and `-a` can fragment a rippled trail; ASTAP is NOT an arm — roundness-gated by its own docs.) |
| GraXpert `-correction Division` synthetic flat | a matching real flat exists for the set | **not fired** — not yet adopted; the vignetting-only fallback for a flatless set (none staged). |
| Siril-native sky flat (july14) | a matching real flat exists for the set | **not fired** — the validated per-set route for flatless sets (`build_sky_flat.sh` gates); dust-safety validates PER SET before use (dead-ends); tightening is item 5. |
| `frame_metrics.json` CFA-sampled FWHM | re-measure debayered where disk allows | **not fired** — still the arm rig. Absolute FWHM there is inflated by the Bayer mosaic; only relative comparison is valid. |
| 16-bit stack-time intermediates | a rig whose RAM/disk carries 32-bit through stacking end-to-end (the x86 32 GB / 1 TB target): drop `set16bits`, re-measure stack noise vs the 16-bit path, land as a declared delta | **not fired** — arm RAM/disk forced it; the quantization is measured ≈18× below per-frame noise (~+0.3% stack noise) and the shipped july14 stacks are BITPIX=16 under it. |
| lensfun user-DB strip of this lens's `<vignetting>`/`<tca>` (`install_lens_model.sh`) — darktable ignores a style's lens op_params, so the DB is the only place distortion-only can be enforced | darktable honors a style's lens op_params (or another headless per-invocation param channel) — re-check per darktable version bump AND per rig with `scripts/darktable/verify_lens_card.py` (grid positive control + uniform card; the uniform card ALONE is vacuous — see `docs/dead-ends.md`) | **not fired** — measured ignored on darktable 5.4.1 (`docs/dead-ends.md`; `datasets/july14/set-01/qa_work/gradient_qa.json`). RE-CHECKED on the x86 rig (darktable 5.4.1, upstream lensfun DB): grid control fires (Siril sigma 45620), uniform card corner-vs-centre delta **0.000 ADU** → distortion-only holds (`datasets/july14/set-01/qa_work/lens_card.json`). |
| `run_undistort_groups.sh` group-composition stacking (per-group stacks → compose; one extra interpolation pass) | free disk ≥ the single-pass peak (~231 MB/frame — the x86 1 TB) → use `run_undistort_pipeline.sh` | **not fired** — arm-rig disk is the reason it exists; valid only post-undistort (homographies compose). QUALITY-UNVALIDATED for production — and the APPROVED full-session render rode this route, so the item-7 single-pass-vs-groups A/B (plus the in-group rejection ladder) is now the standing validation DEBT on the deliverable, payable on x86 disk. |
| 5-set combine via TWO interleaved-half composes + a 2-member `-weight=nbstack` join (the 107-sub single-registration max compose needs ~37G transient vs ~24G reclaimable on this rig) | x86 disk → re-compose all 107 sub-stacks in ONE registration (every `groups_*` dir is kept for exactly this) | **not fired** — declared cost: the non-reference half carries one extra interpolation; halves span all five sets (interleaved), STACKCNT propagates exact frame weights (794+781=1575); the join landed natively in the cov25 orientation family. The 5-member per-set-stack shortcut is a measured dead-end (pre-cropped members — registry). |

## 0. THE RENDER-TIER BUILD — user-gated, the one open product gap

The render tier is UNBUILT — a POLICY gap (the user gates every
output-shaping run), not a rig gap: the full Siril native render surface is
probed present + scriptable on this arm rig, and only the neural/separation
x86-64 binaries are environment-blocked (per-tool evidence: `TOOLS.md`).

**The plan is re-derived PER DATASET by the operating loop** (MEASURE the
staged corpus → MATCH → RECOMMEND → the user's GO); the pre-registered ladder
skeleton it instantiates: L1 background-step level A/B (item 7's named test;
on an MW-filling field only a first-degree plane or none is dust-safe) → L2
linear denoise (objective instrument = the noise-split structured term, never
whole-frame `bgnoise` — dead-ends) → L3 GHS stretch ladder replacing the
diagnostic autostretch (arms compared at a MATCHED background landing, so
curve shape — not brightness — is the knob) → L4 thresholded satu; one knob
per experiment, hypotheses pre-registered, judged on full-frame lossless
PNG16, STOPPED at the user's gate. (The retired exemplar's fully-anchored
instance of this plan is in git history.) Riding on completion: re-seed
`datasets/GENERIC.json` + recipe `render` blocks, first `baseline.json` via
the no-regression harness, `finish_render.sh`'s stretch stage swap, and the
`judgment_package.py` re-wire (its PNG8 pairing predates the 16-bit-only
judgment policy; its `.metrics.json` producer — the wiped chain's renderer —
must be replaced by the new chain's stage records). Close condition: an
approved, re-baselined, tagged render from the new tier.

## 1. Derive the config fingerprint from the data

STATUS (core + broadening landed; live on colonnello-m20): `scripts/lib/fingerprint.py`
derives the fingerprint from tool outputs only — header facts (`acquisition.py`, incl.
the FITS pointing RA/Dec the capture software records), astrometry.net solves
(`solve_field.py`) and Siril findstar/register metrics (`frame_metrics.json`) —
computing just the derived trail/drift geometry no tool reports, and records
`datasets/<session>/<set>/fingerprint.json` (content-compare write; `refresh()` is the
idempotent seeding entry). The declared mount is cross-checked by TWO instruments:
(1) **trail-vs-roundness** (cheap, no solve, one-sided): decisive only when the
predicted-if-fixed trail exceeds the worst elongation the measured stars could hide by
≥10× with a real matched star population — live on all three colonnello-m20 sets
(predicted 1625 px vs implied ≤3 px, margins 538–713×, CONFIRM tracked); (2) the
**two-window drift solves** (precise, either signature — the instrument near the
boundary, e.g. 3.4 px predicted on a 3.5 px PSF; self-tested against the retired
exemplar's numbers: trail 3.41 px, drift 34 px/min, RA 14.99°/hr). Disagreeing
instruments yield INDETERMINATE, never a coin toss. SEEDING IS AUTOMATIC (never
waiting to be asked): the web mount declaration derives on write (verdict returned in
the response), `run_frame_qa.sh` refreshes when roundness lands (exits loud on
CONTRADICT), and the web run gate re-derives before every output-shaping run.
CONSUMERS STOP: `acquisition.resolve()` raises `MountContradicted` on a contradicted
record (every declare-or-stop consumer inherits the stop), and `/api/run` refuses
calibrate/execute/finish stages for a CONTRADICT set (measure stages stay runnable —
measuring is how a contradiction resolves). Derivation + record only: it recommends
and checks; the user stays the gate on every output-shaping run. REMAINS: run the
two-window solve live on the next camera-raw (boundary-regime) corpus, and wire the
fingerprint into the builders' MATCH→RECOMMEND preflight (still user-gated — it
recommends a route, never auto-executes).

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
- Per-lens facts re-derive at the next wide-untracked set (the retired 24-70/4 S
  facts — calibrated focals 24/28/35/50/70, fitted-at-70-only, `crop=1.0` — are in
  git): confirm the NEW body/lens's lensfun coverage, interpolation behaviour and
  crop factor before first use. The fitted-entry rule stands: any focal not fitted
  rides the community entries until fitted (`fit_lens_model.sh` per focal).
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

_(CLOSED items carry no blocks here — completed work lives in git. Items
**3** — per-set culling, ratified + CONSUMED by the approved 1575-frame
render; **4** — the remainder-of-1 guards, built into both chunked builders;
**6** — the reinvention retirements: all five hand-rolled FITS-parser sites →
`astropy`, and the `compose.py` channel combine + write → Siril `rgbcomp`,
verified pixel-identical on real aligned members before the swap
(`compose_ab.json`; the 16-bit-intermediates condition stays in the register);
**8** — the 5-set combine, rendered and APPROVED (tag
`july14-all5-cov25frame-approved`; residue lives in the removal register +
items 0/12); **14** — dashboard↔Claude communication, resolved no-new-surface (no MCP
server, no SDK bridge; Claude reads the existing job logs + records,
deep tool logs grep-first). Mechanisms live in
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
  A/B (= item 0's L1), not alone;
- the deciding test is a with/without comparison on full-frame lossless finals, with
  dust preservation the metric (the user's eyes) — the exemplar's staged
  judgment pair was wiped with july14; re-stage the with/without pair on the
  next flatless set.

Building it from the set's FULL frame count directly addresses the star specks — more
frames reject better. GraXpert `-correction Division` stays the vignetting-only
fallback. A real matching flat retires the whole branch.

Cross-set flat question — SETTLED (user-ratified per-set-flat rule; mechanism +
numbers in `docs/dead-ends.md`, ledger `flat_source_set03`).

## 7. Open questions with a named test

- **Group composition vs single-pass — the architecture A/B.** Same frames, same
  masters, one knob (the architecture): single-pass register+stack vs
  `run_undistort_groups.sh`. Judged on full-frame lossless finals + `seqtilt` +
  drift-axis stations; settles the second-interpolation cost and whether the
  route may ship production stacks. Data-gated: re-arms when the groups route
  next carries a production stack on this rig's disk; retires with the route
  on x86 disk (removal register). Companion ladder: in-group rejection at
  small n (none / percentile / winsorized) — Siril's docs prescribe percentile
  ≤6 and GESD >50 and are silent between.
- **Background-step LEVEL: per-frame vs on-stack `subsky 1` — item 0's L1**,
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
  decentering does not (data-gated: needs multiple sets of the class from the
  next corpus).
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

## 9. Data-capability gaps (gated per item — read each gate)

Real imaging capabilities the pipeline does not yet have; each lands as a measured
declared delta when its gate opens.

- **Full-size dual-band** — native Ha + 2× drizzle of OIII instead of downsampling OIII
  to Ha's half size, gated on measured dither coverage (the per-frame
  `dither_phase_frac` record already exists).
- **LRGB join** — `compose` REFUSES a `luminance` member (L joins after both
  parts are stretched — a nonlinear-space step this compose-then-render flow
  cannot express). `rgbcomp -lum=` is the headless mechanism when an L corpus
  arrives; open: the CLI `-lum` blend colour space is undocumented (GUI offers
  HSL/HSV/Lab) — resolve before first use.
- **FITS-path `setfindstar` asymmetry** (audit-found): the raw-camera template
  lowers detection to `-sigma=0.5` (measured: the matcher needs the extra
  triangles on this class) but the FITS `_fits_lights`/`_fits_dualband` paths
  register at the default sigma. Mechanism: the two paths were built from
  different data classes. Named test: on the first FITS-class set, a one-knob
  registration ladder (default vs `-sigma=0.5`) — adopt per measured
  match-rate, never by symmetry alone. MEASURED at first contact (three
  mono filter sets): default sigma registered 46/46 at ~1500–2000
  stars/frame — no match-rate to recover; the ladder stays dormant until
  a FITS set shows matching loss.
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

## 11. Walking noise in the wide-untracked data — OPEN gap, class-gated

**Item 0's L2 denoise ladder targets this defect's drift-phase term as its
objective instrument** (the noise-split structured excess, re-measured per
corpus). L2 treats the SYMPTOM budget; the acquisition-side mechanism work
below stays open either way (a denoiser must never be this defect's only
answer — bandaid rule).

Faint DRIFT-ALIGNED streaks the user sees at native 1:1, below whole-frame
statistics — a sensor-fixed pattern (electronic-shutter readout FPN + residual
hot/warm pixels) dragged into lines by the coherent, un-dithered drift.
Rejection and cosmetic correction measured NULL against it — the streaks are
sub-sigma STRUCTURED signal, not discrete rejectable outliers (mechanism +
numbers in `docs/dead-ends.md`). **First direct quantification
(`noise_split.sh`, on the retired exemplar):** the drift-phase structured
component ≈0.34/0.48/0.42 ADU (R/G/B) per ~199-frame half
(timehalf-vs-interleaved split excess) — roughly a third of the total
static-structure budget (≈1.0/1.5/1.2 ADU, the rest unresolved-star confusion
texture = real sky) and comparable to the random noise left at that depth: the
denoise tier's measured target size for this class.

**Gated on the class recurring** (an un-dithered untracked set — the
acquisition checklist's dither line is the acquisition-side fix; dithered or
tracked acquisition removes the driver and this goes dormant, not dead).
First-contact levers on the next comparable set: (1) whether the master dark
captures the electronic-shutter pattern — shoot matched shutter-mode darks and
rebuild; (2) directional/pattern removal aligned to the measured drift axis,
or an AI denoiser (x86) weighed against dust preservation (a bandaid, last
resort). Do NOT assume a shutter-mode change removes it — unsettled.

## 13. july14 naming divergence — RESOLVED (records realigned)

The M1 front-end test run mislabeled two sets: what it staged as `set-01`/`set-02`
are physically the exemplar's **set-04 (DSC_7941–8339, 399 fr)** and **set-05
(DSC_8341–8487, 147 fr)** — USER-CONFIRMED. Rather than purge (the original plan
when it was a throwaway test), the location was promoted to the REAL dataset: the
full acquisition was downloaded to `sessions/july14/` under correct
server naming (set-00…set-05 + darks), so the mislabel was fixed at the source.
The tracked records were realigned to match: the M1 `datasets/.../set-01` records
→ `set-04`, `set-02` → `set-05` (acquisition/recipe/frame_metrics/anomaly_audit +
`skyflat_set-0{1,2}_qa.json` → `skyflat_set-0{4,5}_qa.json`), and
`framing_stack_set-01+02_max_spcc.json` → `…set-04+05…`. `datasets/.../set-01` now
correctly holds the REAL set-01 (373 fr) lens work only. No flats were shot for any
set (sky-flat route). OPEN: real set-01/02/03 have raws but no acquisition/recipe
records yet — those seed when each set is processed (the deriver's design; a
missing record is handled gracefully). OPEN (user call): the session dir is still
named `july14`; rename to `july14` now that it is the real dataset, or
leave it.

## 15. Run-page job logs repopulate cross-session at job start — OPEN, reported

USER-OBSERVED (first july23 chain run): with the per-session job filter live
(jobs carry `session`, the Run page filters its table — verified clean on
page load), STARTING a job made previous sessions' logs/jobs repopulate the
page. Not yet reproduced or diagnosed — recorded on user order before any
fix attempt. Suspects, in test order: (1) the job-start client path
(`openStageForm`'s run handler → `refreshJobs()`/`watchJob`) racing the
session-model global `M` (an undefined `M.session` makes the filter show-all
by design); (2) a `/api/jobs` answer from a stale-rev server process whose
adopted JOBS table predates the session backfill; (3) the log-pane WATCH
poll's end-of-job `refreshJobs()` re-render. Close condition: on a session
page with another session's job records present, start a job — the jobs
table shows only the current session's rows (plus rig-level) at job start,
during the run, and at completion.

## 12. Hand-crop framing via web browser — the user draws the final frame

Framing is a COMPOSITION judgment and belongs to the user, not to the mechanical
extremes: `-framing=min` is the binary intersection (measured discarding sky
covered by ALL 50 sub-stacks — the NAN sat at 50/50 coverage and was still cut),
`max` is the raw union with single-coverage rims, and the coverage-threshold crop
(`coverage_threshold_frame_0103`) is instrument-driven but still machine-chosen.

**STATUS — capture side, site shell, Tier-1 execution AND the render consume
side are BUILT and EXERCISED END-TO-END (`web/`); the item-0 render chain
inherits the same record.** On the retired test corpus a user-drawn
union-stack framing was Siril-VERIFIED (coverage-map mode) and rendered
through `finish_render --crop-record` → solve → SPCC → linked stretch → judge
PNG (git). `finish_render --crop-record` applies a VERIFIED framing to the
LINEAR stack before solve/SPCC/stretch (refuses unverified records and a
record/stack canvas mismatch); the RA/Dec-anchored reproduction after a stack
rebuild is the UNBUILT half of the close condition (below). Landed: `web/serve.py` (127.0.0.1-only static
server + the framing POST + the mount-declaration POST +
`GET /api/session/<name>`, the read-only joined session
model: per-set records normalized for display, surfaces with recipe-vs-header
frame-count confirmation from FITS metadata, approvals from git tags only;
plus the Tier-1 registry — measure/calibrate/execute/finish/surfaces stages
with derived defaults, per-stage status, path datalists — and the
Environment page: rig probes + setup actions kept out of the pipeline view),
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
Deliberately NOT in the registry yet: any render-tier stage (item 0,
user-gated). The
record (`datasets/<session>/framing_<product>.json`) carries BOTH coordinate
conventions (screen top-left AND Siril bottom-left — the measured y-flip trap)
plus WCS RA/Dec corners so the framing survives re-registration.

Open, in order:
- **Coverage overlay in the UI — mechanism CLOSED** (proven end-to-end on the
  retired exemplar; records in git history): `coverage_probe.sh` map →
  `make_previews.sh` pm veil (white where coverage < N, threshold at
  N*1000/65535 in pm's [0,1] domain) → manifest `kind: coverage` → crop.html
  canvas-matched tinted toggle. Per-compose maps regenerate at need; the
  probe's measured limits are pinned in its docstring (members×1000 saturates
  at 65535 → thresholds ≤65 valid; full-sequence single-pass apply only). A
  compose whose membership exceeds one pass on this rig rides the bigger-rig
  re-compose.
- **The chain consumes it — the diagnostic chain DOES** (`finish_render
  --crop-record`: verified-only, canvas-checked, crop on the LINEAR stack —
  crop-before-stretch); remaining: the item-0 render chain consumes the same
  record on every rebuild, and the RA/Dec-anchored reproduction is UNBUILT —
  deriving the rect on a REBUILT canvas from the record's WCS corners (today a
  canvas mismatch is refused, not re-derived). Build + exercise it at the next
  union stack. Siril 1.5's `eqcrop ra1 dec1 ra2 dec2` (item 10) is the
  natural consumer of the RA/Dec form when the x86 rig lands on 1.5.
- **Close condition** (unchanged): a box drawn on a union surface renders
  through the chain to a final whose framing matches the drawn box, and the
  record reproduces that framing after a stack rebuild (RA/Dec-anchored). The
  `cov25` crop is the machine-chosen precursor whose record+Siril-crop
  plumbing this reuses — only the rectangle CHOICE moves to the user's hand.
