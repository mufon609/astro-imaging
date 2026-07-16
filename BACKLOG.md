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
| `astrometrics.write_png16` (hand-rolled 16-bit PNG encoder + sRGB chunks) | a tool writes 16-bit RGB PNG with its ICC | **FIRED** — Siril `savepng` writes *"16 bits per channel if the loaded image is 16 or 32 bits"* + an iCCP chunk. Retirement is open work (item 6). |
| `compose.py` channel combine (`np.stack` + hand-rolled 3-plane FITS write) | a tool composes channels headless | **FIRED** — Siril `rgbcomp` verified on 1.4.4, and `rgbcomp -lum=` additionally closes the LRGB-join gap. Retirement is open work (item 6). |
| `judgment_package.read_png16_sampled` (hand-rolled PNG decoder) | a library reader or a 16-bit TIFF surface | **FIRED** — `tifffile` reads Siril's 16-bit TIFF; Siril `savepng` writes the PNG. Retirement is open work (item 6). |
| `crop_coverage.py` (post-stack coverage crop) | `seqapplyreg -framing=min` provably accounts for drift **and rotation** | **UNSETTLED** — a real 1500-px-drift, field-rotating set now runs through `-framing=min` in production and has never needed the script, but Siril's docs say only "the area it has in common with all images" and do not specify rotation handling. A border-vs-interior `stat` is confounded by the sky gradient. Needs a real coverage test (item 6). |
| `scripts/qa/star_shape.py` two-frame duplication | Siril exposes a headless single-image tilt, or builds a sequence from one frame | **not fired** — `tilt`/`inspector` are both *"Can be used in a script: NO"*, and Siril cannot build a sequence from a single frame (item 4). |
| Hand-rolled FITS parsers (5 sites) | `astropy` available | **not fired** — x86-gated; astropy 8.0.1 confirmed clean for the target. |
| `solve_field.detect_stars` peak centroids | a tool's extractor returns trailed sources *and* measures at least as well | **not fired** — `image2xy` is shape-blind (source-verified) but its trail knobs are not exposed by `solve-field`; a measured A/B, not a swap (item 7). |
| GraXpert `-correction Division` synthetic flat | a matching real flat exists for the set | **not fired** — not yet adopted; july14 is flatless by acquisition. |
| Siril-native sky flat (july14) | a matching real flat exists for the set | **not fired** — validated dust-safe for this set; tightening is item 5. |
| `frame_metrics.json` CFA-sampled FWHM | re-measure debayered where disk allows | **not fired** — still the arm rig. Absolute FWHM there is inflated by the Bayer mosaic; only relative comparison is valid. |
| 16-bit stack-time intermediates | RAM/disk headroom to carry 32-bit through stacking | **no condition was ever written** — the reduction is documented in `README.md` but nothing says when it ends. The x86 target (32 GB / 1 TB) removes the reason. Write the condition, then fire it there (item 6). |

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

The wide-field untracked route is validated, productionised and shipped
([`docs/wide-field-untracked-registration.md`](docs/wide-field-untracked-registration.md)),
but it exists as one dataset's chain rather than something the repo recommends to any
set with the same footprint. The generality question that gated this is **answered**:

- **Focal generality — MEASURED, and the answer is good.** darktable's lens module
  **re-detects focal from each image's EXIF and overrides the value baked into the
  style's `op_params`**. Same RAW with EXIF focal 70 vs 24 gives opposite-sign
  displacement fields (70 mm outward +26→+69 px; 24 mm inward −6→−19 px before
  crossing over) over ~400 matched stars — barrel at the wide end, pincushion at the
  long. **One style serves the lens's range**; the feared "a 24 mm frame silently gets
  a 70 mm correction" does not occur.
- **The style is pinned** (`scripts/darktable/*.dtstyle` + `install_styles.sh`,
  verified to reproduce the warp to 0.000 px in a fresh config). No GUI step remains.

What is left:

- **The autoscale question is CLOSED — it is a non-issue.** `scale` is baked but
  IGNORED: scale 1.046 vs 0 vs **1.5** produce warps identical to **0.000 px**, so
  darktable recomputes the autoscale per image. The same probe closed the rest of the
  blob: `focal`, `camera` and `lens` are all re-detected from EXIF too. **Only
  `modify_flags` carries**, so one style is camera-, lens- and focal-general.
- **BUILD THE PREFLIGHT GUARD — this is now the route's biggest risk, and it is the
  reason the above is not simply good news.** Because nothing is baked, **darktable never
  fails**: a lens the DB cannot match gets **NO correction, silently** (measured: 0.000 px
  over 413 stars, exit 0, nothing in the log), and a wrong-but-present lens gets a wrong,
  weaker model just as quietly. A set that trips this stacks UNCORRECTED and the only
  symptom is a worse `seqtilt` off-axis aberration in the final — the exact defect the
  route removes, reintroduced with no warning. The guard must, per set and BEFORE the run:
  assert EXIF camera+lens+focal against the lensfun DB **and** against the set's recorded
  `acquisition.json`, and STOP on a miss or on **mixed** focal/lens within the set (each
  frame silently gets its own EXIF's model — this is what makes mixed a hard stop rather
  than an interpolation, the acquisition checklist's "lock the zoom ring" surfacing as a
  processing consequence). A non-zero warp is only a secondary confirmation: **"did the
  warp happen" passes the wrong-lens case.** Mechanism: `docs/dead-ends.md`.
- **Wire it into the loop as the MATCH → RECOMMEND step for this footprint:** take the
  fingerprint (item 1) → check the lensfun DB → recommend the route with its reason (or
  a plain homography, with its reason) → report → user decides → execute → record the
  choice and its trade-off.
- lensfun carries CALIBRATED entries at 24/28/35/50/70 for this lens and interpolates
  between them; confirm interpolated behaviour at an intermediate focal, and that
  `crop=1.0` holds for the body.

## 3. Culling — assessed, never decided

`frame_metrics.json` flagged 4 of 373 at z>3.5 (6897, 6900, 7263, 7264) and
`cull_report` proposed excluding them. **No render has applied that.** It is an
unexamined default, not a decision — the gap this item closes.

- **Frame selection has been disk-bound, not chosen.** The shipped 168-frame render
  selected by even stride to fit the disk, not by quality, and **includes DSC_6900**
  — the frame flagged worst on all three axes — while an earlier 54-frame subset
  excluded all four by luck. Disk pressure silently became frame selection. A
  full-depth render must use ALL frames plus an EXPLICIT culling decision.
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
this on its last chunk.

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
Before it enters another stack, tighten:

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

Each has a **fired** removal condition (see the register); the finding is confirmed and
only the retirement is outstanding. Do not re-research these — implement them.

- **`astrometrics.write_png16` → Siril `savepng`.** Retires a from-scratch 16-bit RGB
  PNG encoder *and* its hand-built sRGB/gAMA/cHRM colorimetry. `savepng filename` takes
  no flags (16-bit auto-selected from a 16/32-bit source); the profile comes from a
  prior `icc_assign` + a save-time preference, and lands as an **iCCP** chunk (a full
  profile rather than the lightweight triplet — both standards-compliant).
- **`compose.py` channel combine → Siril `rgbcomp`.** The member ALIGN is already Siril;
  only the combine is in-house. `rgbcomp chR chG chB -out=` produces a 3-plane float32
  RGB FITS, and **`rgbcomp -lum=`** runs the LRGB join headless — which also closes the
  long-standing LRGB gap `compose` currently REFUSES. `compose` shrinks to: resolve
  `composition.json` → drive the Siril align → `rgbcomp`. Open: the CLI `-lum` blend
  colour space is undocumented (GUI offers HSL/HSV/Lab) — check on a real dual-band +
  mono-filter set.
- **`judgment_package.read_png16_sampled` → a library reader.** It hand-implements a
  full PNG decoder (all five scanline filters) for an integrity check. Once Siril writes
  the file, switch the lossless judgment surface to 16-bit TIFF read with `tifffile`, or
  read the PNG with a ~15-line stdlib chunk parser (IHDR/depth/colortype — an inspection,
  not a decode). Pairs with the `savepng` adoption. Reactivate with the render rebuild.
- **`crop_coverage.py` → `seqapplyreg -framing=min`, then REMOVE.** `-framing=min` crops
  to the common area BEFORE stacking, so no falloff band ever forms — earlier and
  cleaner than a post-stack crop, and it is already what production uses. **Settle the
  condition first:** confirm the common area accounts for rotation, not just
  translation. A border-vs-interior `stat` is confounded by the sky gradient; a real
  test needs per-pixel coverage (e.g. stack a constant-valued sequence through the same
  registration and look for a border falloff). `crop x y w h` remains the native
  primitive if a post-hoc crop is ever needed.
- **Write the missing removal condition for the 16-bit stack-time intermediates**, then
  fire it on x86. The quantization was measured ≈18× below per-frame noise (~+0.3% stack
  noise) and was forced by the arm rig's RAM/disk; 32 GB / 1 TB removes the reason. Note
  the shipped july14 stacks are `BITPIX=16` for this reason.

## 7. Open questions with a named test

- **Which mechanism drives the one-sided term.** Siril `seqtilt` measures it (sensor
  tilt 0.50/16% → 0.42/13% → 0.51/16% across control → corrected → shipped): a radial
  lens model does not touch it. Candidates are differential refraction (asymmetric with
  hour angle) and lens decentering. Discriminator: hour-angle dependence across sets —
  refraction varies with it, decentering does not.
- **`solve_field` peak detection → `image2xy` A/B.** `image2xy` (astrometry.net's own
  extractor) is source-verified to have NO shape/roundness gate, so it DOES return
  trailed sources — mechanically closer to our peak-centroid than to a rejecting fitter.
  But it is not strictly more tool-first: the trail-relevant knobs (`-a` saddle, which
  can FRAGMENT one rippled trail into spurious detections; `-p` significance; `-m` max
  deblend size) are not exposed by `solve-field`'s CLI, so tuning needs the standalone
  binary; and a symmetric Gaussian match kernel (`-w`) is SNR-mismatched to an elongated
  PSF. Test: tuned `image2xy` → `.xy.fits` → `solve-field --x-column X --y-column Y
  --width W --height H --no-remove-lines --uniformize 0` vs the current xylist. Record a
  dead-end with numbers either way. ASTAP is not the answer (its own docs: streaks
  ignored, "stars reasonably round").
- **Synthetic-flat gap → GraXpert `-correction Division`.** The headless-CPU
  multiplicative option; source-confirmed as per-channel `imarray/background*mean`, i.e.
  divide by the low-frequency model. Corrects smooth VIGNETTING only, not dust/PRNU
  (the model is built from a ~240 px downsample), so a real flat stays the correct fix
  and "a matching real flat exists" is the removal condition. Caveat: the installed
  GraXpert is a third-party fork (`geeksville`); official stable 3.0.2 is
  BGE+denoise-only but does include `-correction Division`. `-cli` is deprecated;
  `-bg_pts` is not a real flag.
- **A star-colour-neutral colour step.** The O3-sphere mechanism Siril has no single
  command for. Headless path identified, tool half confirmed on 1.4.4: measure mean star
  colour in the examine layer → apply a diagonal `ccm` (the only headless neutral-balance
  path). Run the design against a bracket (SPCC, Nightlight) on x86. Nightlight is a
  dormant mechanism reference only — its `OpRGBBalance` balances the brightest-quartile
  stars; the OIII-lift is our inference (`docs/dead-ends.md`).

## 8. Combine all 5 july14 sets into one deep render (~1865 frames)

july14 is 5 sets of the same object, same workflow, the camera re-centred on the target
every ~45 min. set-01 (373 frames, 43 min) is one such window; only set-01 + set-00 (4
frames) are local — the rest must be brought over.

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

Depends on items 2 (focal generality per set), 3 (culling), 4 (the chunk bug — chunking
is mandatory here) and 5 (the sky flat). Ordered:

1. **Verify every set's camera+lens+focal, and that ISO/exposure match the darks.**
   Both local sets are 70 mm; the other three are unverified. This is a **hard
   prerequisite, not a formality**: darktable silently applies NO correction to a lens it
   cannot match and a wrong model to one it mis-matches, so a single set with a different
   or unrecognised lens string would stack uncorrected into the combined result with no
   warning. Item 2's preflight guard is what enforces it — build it before this runs.
2. **Measure the re-aim scatter before committing to one combined stack.** `-framing=min`
   keeps only what is common to ALL frames: within a set the drift is ~1500 px, across
   sets it is drift + hand-re-centring error. If scatter is large the common area drops
   below set-01's 76% — fallback is stack-per-set then combine the 5 stacks (worse: 5
   discrete residuals rather than one fit).
3. **Rebuild the sky flat from all ~1865 un-registered frames** (item 5). Same
   dust-contamination validation gate.
4. **Storage: ~433 GB peak** (1865 × 232 MB uncompressed). Comfortable on the x86 1 TB;
   impossible on the arm rig. No GPU needed — Siril has no GPU path and the AI tier runs
   once per stack, not per frame.

## 9. Data-capability gaps (x86-gated)

Real imaging capabilities the pipeline does not yet have; each lands as a measured
declared delta during the x86 rebuild.

- **Full-size dual-band** — native Ha + 2× drizzle of OIII instead of downsampling OIII
  to Ha's half size, gated on measured dither coverage (the per-frame
  `dither_phase_frac` record already exists).
- **FITS I/O → astropy** (retires 5 hand-rolled parsers: `astrometrics`, `compose`,
  `solve_field`, `spcc_cone`, `fitsmeta`). astropy 8.0.1 confirmed clean. Gotchas,
  primary-verified: write float32 directly so BZERO/BSCALE auto-scaling stays off; numpy
  `[y,x]` ↔ FITS `NAXIS1` reversed (`.shape == (NAXIS2, NAXIS1)`); SIP needs
  `to_header(relax=True)` (default `relax=False` OMITS the `-SIP` CTYPE suffix). Interim
  on arm: read Siril outputs via `savetif` + `tifffile` (PIL misreads Siril's 16-bit RGB
  TIFF as uint8).
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
