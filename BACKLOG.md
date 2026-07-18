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
| Hand-rolled FITS parsers (5 sites) + the fixed eq→galactic 3×3 | `astropy` available | **FIRED** — astropy 8.0.1 installed on the arm rig (FITS I/O + WCS/SIP + coordinates probed working); retirement is ARM-DOABLE open work (item 6, itemized per site), not x86-gated. |
| `solve_field.detect_stars` peak centroids | a tool's extractor returns trailed sources *and* measures at least as well | **FIRED** — SExtractor core (`sep`) returns trailed sources, solves at higher odds, and gives identical SPCC K end-to-end (`qa_work/extractor_ab.json`). Default is `--detect=sep`; `--detect=peaks` remains the fallback until the x86 day-1 solve passes on sep, then delete it. |
| GraXpert `-correction Division` synthetic flat | a matching real flat exists for the set | **not fired** — not yet adopted; july14 is flatless by acquisition. |
| Siril-native sky flat (july14) | a matching real flat exists for the set | **not fired** — validated dust-safe for this set; tightening is item 5. |
| `frame_metrics.json` CFA-sampled FWHM | re-measure debayered where disk allows | **not fired** — still the arm rig. Absolute FWHM there is inflated by the Bayer mosaic; only relative comparison is valid. |
| 16-bit stack-time intermediates | RAM/disk headroom to carry 32-bit through stacking | **no condition was ever written** — the reduction is documented in `README.md` but nothing says when it ends. The x86 target (32 GB / 1 TB) removes the reason. Write the condition, then fire it there (item 6). |
| lensfun user-DB strip of this lens's `<vignetting>`/`<tca>` (`install_lens_model.sh`) — darktable ignores a style's lens op_params, so the DB is the only place distortion-only can be enforced | darktable honors a style's lens op_params (or another headless per-invocation param channel) — re-check per darktable version bump with the uniform-card test (warp a uniform card through `lensdist`; corner medians must equal centre) | **not fired** — measured ignored on darktable 5.4.1 (`docs/dead-ends.md`; `datasets/july14/set-01/qa_work/gradient_qa.json`). |
| `run_undistort_groups.sh` group-composition stacking (per-group stacks → compose; one extra interpolation pass) | free disk ≥ the single-pass peak (~231 MB/frame — the x86 1 TB) → use `run_undistort_pipeline.sh` | **not fired** — arm-rig disk is the reason it exists; valid only post-undistort (homographies compose). QUALITY-UNVALIDATED for production: requires the item-7 single-pass-vs-groups A/B (and the in-group rejection ladder) to pass on identical frames first. |

## 1. Derive the config fingerprint from the data

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

## 4. BUG — chunked front ends must guard a remainder of 1

**Siril cannot build a sequence from a SINGLE frame.** `convert`/`link` write the .fit
but no .seq, so the next command dies with `No sequence 'x' found` → `invalid input
sequence`. Any chunked front end whose frame count leaves a remainder of exactly 1 hits
this on its last chunk. `run_undistort_pipeline.sh` asserts `n % CHUNK != 1` up front —
any NEW chunked front end (the ~1865-frame item 8 run) must carry the same guard.

It cost a real run: a 169-frame render chunked at 12 → 14 full chunks + **1 leftover**;
chunk 15 failed to calibrate and `set -euo pipefail` (correctly) killed the script. The
168 warped frames survived and the stack was recovered from them, but the register/stack
tail never ran unattended.

This is a landmine for the ~1865-frame 5-set render (item 8), where chunking is
mandatory. Fix when that front end is built: pad the final chunk, merge a remainder of 1
into the previous chunk, or assert `n % CHUNK != 1` up front. Prefer failing at the
ASSERT, before hours of warping. The failure mode is LOUD (the script aborts) — the good
case; the danger is the opposite temptation, since dropping `set -e` to "get past it"
would silently produce a short stack.

The same limitation forces the two-frame duplication in `scripts/qa/star_shape.py`.

## 5. Sky-flat tightening

The Siril-native sky flat is the recommended flat for this flatless set and is
validated dust-safe ([`docs/synthetic-flats-and-bias.md`](docs/synthetic-flats-and-bias.md)).
(The large stack-level bright-corner bowl is the warp stage's vignetting
double-correction, fixed at the lensfun DB — `qa_work/gradient_qa.json`; this
flat's own residuals are the smaller figures in `skyflat_qa.json`.) Before the
flat enters another stack, tighten:

- winsorized/sigma rejection instead of pure median, to drop the faint un-rejected star
  specks flagged in `skyflat_qa.json`;
- smooth the flat to radial-only so division corrects vignetting without flattening the
  low-order sky/IFN gradient (leave that to the first-degree `subsky 1` step);
- dark-subtract the lights before building the flat;
- the deciding test is a with/without comparison on full-frame lossless finals, with
  dust preservation the metric (the user's eyes).

Rebuilding it from all ~1865 frames (item 8) directly addresses the star specks — more
frames reject better. GraXpert `-correction Division` stays the vignetting-only
fallback. A real matching flat retires the whole branch.

## 6. Retire the reinventions whose replacements are confirmed

- **Retire the 5 hand-rolled FITS parsers + the eq→galactic 3×3 → `astropy`
  (ARM-DOABLE NOW).** astropy 8.0.1 is installed and probed on the rig (FITS I/O +
  WCS/SIP + ICRS→Galactic); it is the identical tool on both rigs, so the method
  transfers to x86 unchanged. **Nothing is done — no script imports astropy yet;** all
  five still parse 2880-byte FITS blocks by hand. Swap one site at a time, each verified
  byte-behaviour-equivalent against the current output FIRST (a wrong FITS read corrupts
  every downstream stage):
  1. `scripts/calibrate/solve_field.py` — the header read + the hand-built WCS-card
     writer (`inject()`/`fmt_card()`) → `astropy.wcs.WCS.to_header(relax=True)` (SIP) +
     `astropy.io.fits`; verify an identical solve + SPCC on a solved stack.
     **Highest value / most fragile — start here.**
  2. `scripts/lib/astrometrics.py` — `read_fits()` → `astropy.io.fits`, and the fixed
     eq→galactic 3×3 → `astropy.coordinates` (must agree to arcsec).
  3. `scripts/stack/compose.py` — `read_fits_raw()` + the `np.stack` 3-plane FITS write →
     `astropy.io.fits`; retire jointly with the `rgbcomp` combine swap below, at first
     contact with a dual-band / mono-filter set.
  4. `scripts/calibrate/spcc_cone.py` — the FOCALLEN/XPIXSZ/NAXIS + WCS header read →
     `astropy.io.fits` / `astropy.wcs`.
  5. `scripts/stack/fitsmeta.py` — the 2880-block metadata probe → `astropy.io.fits`.
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
- **Pin the sky-flat build as a script.** The flat recipe lives only in prose
  (a QA record) and session commands; an unpinned build is why reproduction
  was impossible when the artifact was lost. A `scripts/stack/` flat builder
  (recipe verbatim, validation gates included) closes it — item 5's ladder
  lands on top of it.
- **Does `seqapplyreg -framing=min` account for rotation, not just translation?**
  Siril's docs say only "the area it has in common with all images". A
  border-vs-interior `stat` is confounded by the sky gradient; the real test is
  per-pixel coverage — stack a constant-valued sequence through a rotating
  registration and look for border falloff.

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
remainder-of-1 guard is in `run_undistort_pipeline.sh` (item 4). Prep state: set-01
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
3. **Rebuild the sky flat from all ~1865 un-registered frames** (item 5). Same
   dust-contamination validation gate.
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
  `solve_field`, `spcc_cone`, `fitsmeta`, plus the fixed eq→galactic 3×3). **astropy
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
outliers. **Untried levers, to test on the existing data:** (1) whether the master
dark captures the electronic-shutter pattern — check the darks' shutter mode / re-shoot
matched darks and rebuild; (2) directional/pattern removal aligned to the measured
174.4-deg drift axis, or an AI denoiser (x86) weighed against dust preservation (a
bandaid, last resort). The go-forward acquisition fix is unsettled — do NOT assume a
shutter-mode change removes it. OPEN gap, not a dead-end.
