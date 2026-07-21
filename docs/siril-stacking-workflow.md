# Siril headless stacking workflow (calibrate / register / integrate) — deep dive

- **Question / scope** — 2026 best practice for Tier 1 (calibration → registration →
  integration), Siril-first and headless, with the *current* command syntax — because
  the kept `stack/run_pipeline.sh` + `.ssf` orchestration must re-verify against Siril
  1.4.4, and several 1.4 syntax changes will **break migrated scripts**. Also: what
  Siril lacks vs PixInsight WBPP.
- **Context** — Siril **1.4.4** stable (1.4.0 = 2025-12-05). Syntax verified
  against the **git tag `1.4.4`** source (`command_list.h`/`command_def.h`) + the shipped
  `.ssf`, not just prose. Rig: x86-64, 32 GB, no GPU, headless. Ties to the kept core.

## Findings

### Corrections that will BREAK migrated scripts (check these first)
- **The old `-weight_from_noise` / `_wfwhm` / `_nbstars` flags are DEAD** (removed at
  1.4.0-beta1). The only accepted form is unified **`-weight={noise|wfwhm|nbstars|nbstack}`**.
  A migrated `.ssf` using the separate flags errors ("unexpected argument"). [PRIMARY]
- **`-cc=bothpasses` does not exist.** Cosmetic-correction modes are only
  `-cc=dark [siglo sighi]` and `-cc=bpm <file>`. [PRIMARY absence]
- **Normalization is lights-vs-flats, NOT broadband-vs-narrowband.** `-norm=addscale`
  is the default for **all** light frames (broadband *and* narrowband); `-norm=mul` is
  for flats (frames used for division). No doc recommends multiplicative for NB lights. [PRIMARY]
- **The old `register -noout` is gone** — its role is now `-2pass` (compute transforms
  without writing `r_` images). [PRIMARY absence]
- **Bare `rej 3 3` defaults to Winsorized — SETTLED on-rig**: `help stack` on the
  installed 1.4.4 states *"If omitted, the default Winsorized is used"* (and default
  normalization for rej/med is addscale). Writing the letter explicitly
  (`rej w 3 3`) remains best practice for unambiguous headless scripts.

### Calibration (headless)
- **Master stacking** (per the shipped scripts): bias/dark **`-nonorm`**, flats
  **`-norm=mul`** — *"bias and dark masters should not be normalised; multiplicative
  normalisation must be used with flat-field frames."*
  ```
  stack bias    rej 3 3 -nonorm    -out=../masters/bias_stacked
  stack dark    rej 3 3 -nonorm    -out=../masters/dark_stacked
  stack pp_flat rej 3 3 -norm=mul  -out=../masters/pp_flat_stacked
  ```
- **`calibrate`**: `calibrate seq [-bias=] [-dark=] [-flat=] [-cc=dark [siglo sighi] |
  -cc=bpm file] [-cfa] [-debayer] [-equalize_cfa] [-opt[=exp]] [-cfa] [-fitseq]`
  (default prefix `pp_`). Official OSC light line: `calibrate light -dark=… -flat=…
  -cc=dark -cfa -equalize_cfa -debayer`. Omit `-debayer` if doing CFA drizzle later.
- **Dark optimization `-opt`** scales the thermal component (needs bias + dark;
  `-opt=exp` uses the exposure keyword) — use for unmatched darks, skip for matched.
- **Cosmetic:** bare `-cc=dark` = **hot-only at σ=3**; `-cc=dark 3 3` adds cold; `-cfa`
  for OSC. `-cc=bpm` uses a Bad-Pixel-Map (from `find_hot` on a masterdark). Standalone:
  `find_hot`, `find_cosme`, `find_cosme_cfa`. **No command literally named `cosmetic`.**
- **Synthetic bias for flats** (modern-sensor guidance): `calibrate flat -bias="=256"`
  (the `=`/`$`/quotes are mandatory; `-bias="=10*$OFFSET"` reads the FITS OFFSET) —
  sets the flat's zero point, *not* noise removal. **Use dark-flats instead of bias when
  there's significant ampglow / long flat exposures / no thermal regulation.** Synthetic
  bias is valid for flats only — **lights still need a real masterdark.**

### Registration
- `register seq [-2pass] [-transf=shift|similarity|affine|homography] [-drizzle …]
  [-minpairs=] [-maxstars=] [-interp=] [-noclamp] [-disto=]` → DynamicPSF detection →
  triangle-similarity match → RANSAC → projection. **`-2pass` computes transforms +
  auto-picks the best reference, writes no `r_` images → follow with `seqapplyreg`**
  (which also does quality filtering `-filter-fwhm=/-filter-round=/…` + framing
  `-framing=`). 1-pass writes `r_` in one step off the first frame.
- **Transforms:** shift (2-DOF, translation) · similarity (4, +rot+scale) · affine (6,
  +shear) · **homography (8, +perspective) = default, "strongly recommended for
  wide-field."** Min pairs 3 (shift/sim/affine), 4 (homography). Sparse fields → drop to
  similarity/affine (homography over-fits with few stars — reasoned, not doc-stated).
- **Interp:** default **lanczos4** with **clamping ON** (only `-noclamp` disables — keep
  it on for star fields to avoid ringing). `-interp=none` for pure shift or with drizzle
  (drizzle resamples itself); `-interp=area` for downscale. Manual reference: `setref`.

### Integration (`stack`)
- `stack seq {rej|mean} [rejtype siglo sighi] [-norm=addscale] [-weight=…] [-feather=]
  [-rgb_equal] [-output_norm] [-32b] [-rejmaps] [-out=]`. `rej`/`mean` are synonyms
  (average-with-rejection). `sum|min|max|med` take no rejection/weight.
- **Rejection by sub count:** **≤6 → percentile (`p`)**; **~7–50 → winsorized (`w 3 3`)**;
  **>50 → GESD (`g 0.3 0.05` — a max-outlier *fraction* + *significance*, NOT sigmas)**;
  **large + differing sky gradients → linear-fit (`l 3 3`)**. Also `s` sigma, `a` MAD, `m`
  median-sigma. [PRIMARY thresholds; GESD-params-not-sigmas cross-corroborated SECONDARY]
- **Weighting `-weight=`** (the shipped light stacks use NONE): `wfwhm` best all-round
  (unreliable in star-sparse fields); `noise` inverse-bg-noise but barely varies within a
  session + inflated by gradients (best across sessions); `nbstars` biased by density;
  `nbstack` only for stacks-of-stacks. [PRIMARY syntax; failure modes part mechanism]
- **Normalization** = global only: `add`/`addscale`(default lights)/`mul`(flats)/`mulscale`,
  `-nonorm` (darks/bias). `-overlap_norm` is **mosaic-only** (not a within-frame gradient
  fix). Output: `-32b`, `-rgb_equal` (OSC per-channel bg), `-feather=<px>` (dithered/mosaic
  seams), `-rejmaps` (QA maps).
- **Canonical OSC light stack:** `stack r_pp_light rej w 3 3 -norm=addscale -weight=wfwhm
  -output_norm -rgb_equal -32b -out=result` (large → `rej g 0.3 0.05`; +gradients → `rej l 3 3`).

### Drizzle — lives on REGISTRATION, not `stack`
- `-drizzle [-scale=0.1..3] [-pixfrac=1.0] [-kernel=point|square|gaussian|lanczos2/3]
  [-flat=]` on `register`/`seqapplyreg`; drizzled frames are then stacked normally. **True
  drizzle (Fruchter-Hook) shipped in 1.4.0**, replacing the pre-1.4 "glorified upscale."
- Rule: **pixfrac ≈ 1/scale** (slightly larger to avoid holes). **CFA/Bayer drizzle** for
  OSC = register the *undebayered* sequence with `-drizzle`; Siril recommends **scale=1.0,
  pixfrac=1.0** even at nominal sampling (cleaner colour noise than interpolated demosaic;
  script `OSC_Preprocessing_BayerDrizzle.ssf`). Full sampling analysis in
  [[plate-solving-and-drizzle]].

### WBPP-equivalent + what Siril LACKS
- Bundled one-shot `.ssf`: `OSC_Preprocessing`, `…_BayerDrizzle`, `Mono_Preprocessing`,
  `OSC_Extract_Ha/HaOIII`, `RGB_Composition` — rigid **single-group, single-session**.
  Community `preprocessing/` variants + **`AMSP.py` ("Automatic Multi-Session Processing")**,
  FITS-keyword-driven (claimed ~4× faster than WBPP — [SECONDARY, AstroBin]), `GPS_Preprocess.py`.
- **PixInsight WBPP does what Siril does NOT:** auto frame grouping by filter/exp/temp/gain;
  per-group master matching; auto-detect cosmetic correction; **Local Normalization**
  (gradient-aware — *no Siril equivalent*); **PSF Signal Weight** (*no Siril equivalent* —
  our audit layer can compute a proxy, [[objective-qa-defect-metrics]]); drizzle wired into
  the batch.

### 2026 shifts — mostly OLD; the genuine 1.4 advance is narrow
- **Genuinely new in 1.4.0:** true Drizzle; mosaic astrometric registration + edge
  feathering (`-feather`/`-overlap_norm`); distortion correction/**SIP** (`-disto=`, to
  5th order); unified `-weight=`; parallel min/max; Python (`sirilpy`) + Git-synced scripts.
- **NOT new (corrects the premise):** GESD = 0.99.10 (2021); noise weighting = 0.99.10;
  nbstars + wFWHM = 1.2.0 (2023); drizzle-script + overlap-norm + dark-scaling = 1.2.0.
- **Still absent (even in 1.5.0-dev):** local/gradient-aware normalization; a PSF-Signal-
  Weight-equivalent metric. Next stable = 1.6; only stated roadmap is expanding mosaics.

## Sources
- Calibration/Registration/Stacking/Drizzle (readthedocs stable) —
  https://siril.readthedocs.io/en/stable/preprocessing/calibration.html ·
  /registration.html · /stacking.html · /drizzle.html · Commands https://siril.readthedocs.io/en/stable/Commands.html
- **Exact 1.4.4 syntax (git tag):** `command_list.h`/`command_def.h` —
  https://gitlab.com/free-astro/siril/-/raw/1.4.4/src/core/command_list.h
- Shipped scripts — https://gitlab.com/free-astro/siril/-/raw/master/scripts/OSC_Preprocessing.ssf ·
  community repo https://gitlab.com/free-astro/siril-scripts/-/tree/main
- ChangeLog (feature dating) — https://gitlab.com/free-astro/siril/-/raw/master/ChangeLog ·
  1.4.0 notes https://siril.org/download/2025-12-05-siril-1-4-0/ · synthetic biases https://siril.org/tutorials/synthetic-biases/
- `-weight=` change (SECONDARY) — https://discuss.pixls.us/t/sirilic-argument-error-weight-from-wfwhm/49972 ·
  AMSP https://app.astrobin.com/forum/topic/233018/ · WBPP feature overview https://astroguide.starlust.de/html/WBPPWeightedBatchPre-Processing.html

## Verdict / recommendation
- **Keep Siril for the headless stack**, but **re-verify every migrated `.ssf` against
  1.4.4 syntax** before trusting it (unified `-weight=`, `-2pass`+`seqapplyreg`, no
  `-noout`/`-cc=bothpasses`). Pick rejection by sub count (percentile ≤6 / winsorized
  7–50 / GESD >50 / linfit for gradients); `-norm=addscale` lights, `-nonorm` darks/bias,
  `-norm=mul` flats; homography for wide fields.
- **Drizzle is a registration option** — use CFA-drizzle 1×/1.0 for OSC, and upscale
  drizzle only when sampling + dithering justify it ([[plate-solving-and-drizzle]]).
- **Accept two real gaps vs WBPP** (Local Normalization, PSF-Signal-Weight) — the audit
  layer can supply a PSFSW proxy for frame weighting; local-normalization has no FOSS
  headless equal (a documented gap, not a hand-roll).

## Status
**PROVISIONAL (doc/source-verified syntax; not re-run on our data).** All commands are
PRIMARY-VERIFIED against the Siril 1.4.4 tag + shipped scripts. The bare-`rej`
default is now SETTLED on-rig (Winsorized — `help stack`, 1.4.4). Still flagged
UNCERTAIN: `-minpairs`/detection-sigma defaults. The kept `run_pipeline.sh`/
`.ssf` must be re-run on x86 Siril 1.4.4 and its syntax reconciled — the acceptance test
is a clean calibrate→register→stack on a known set with the corrected flags.

## Graduation
- **TOOLS.md Tier 1** — add the stacking specifics: rejection-by-sub-count, unified
  `-weight=` (with the failure modes), `-norm` lights/darks/flats, homography-for-wide,
  drizzle-on-register, and the WBPP gaps (Local Norm / PSF-Signal-Weight — none native).
- **The dead-end registry (`docs/dead-ends.md`)** — record the migrated-script breakage (unified `-weight=`, no `-noout`/
  `-cc=bothpasses`) as a rebuild gotcha for `run_pipeline.sh`; note drizzle is a
  registration option and CFA-drizzle 1× is Siril's recommended OSC setting.
- Applied in this deep-dive's commit.
