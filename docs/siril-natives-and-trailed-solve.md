# Siril native capabilities (mid-2026) + the trailed-field solve — deep dive

- **Question / scope** — What is Siril's *current* native command set (mid-2026),
  what shipped since 1.4.0, and do the three gaps the toolkit relies on external
  tools to fill (chroma-noise, AI deconvolution, star-neutral narrowband) still
  stand natively? Plus: continue the trailed/ultra-wide plate-solving
  verification (does native `-localasnet` replace `solve_field.py`?). Siril is the
  free+headless substrate of the whole x86 stack, so its native surface sets what
  the orchestration layer must reach *outside* Siril for.
- **Context** — Siril **1.4.4** (2026-06-17) is the current stable;
  **1.5.0** is the active development branch (docs at readthedocs `en/latest`,
  bundled **sirilpy 1.1.13**), no 1.5 beta/RC announced. Target rig: x86-64 Kali,
  i7-14gen, 32 GB, **no GPU**, headless via `siril-cli -s`.

## Findings

### 1. Version state — 1.4.x is maintenance; 1.5.0 is where new native surface lands
- Release line, all maintenance after `.0`: **1.4.0** 2025-12-05 (the feature
  release) → 1.4.1 (2026-01-05) → 1.4.2 (2026-02-18) → 1.4.3 (2026-05) → **1.4.4**
  (2026-06-17). No 1.4.5, **no 1.5/1.6 stable**. Wikipedia's version box is stale
  (shows 1.4.2) — trust siril.org.
- Substance of the point releases is **build/scripting/catalogue robustness, not
  new processing**: 1.4.1 optional-dependency builds + sirilpy fixes; 1.4.2 a
  **GPU-library-management overhaul + `GPU_Manager` script** + SPCC catalogue-index
  caching; **1.4.3** the headless-relevant ones (below); 1.4.4 bug-fix only (now
  needs macOS 13+).
- **Headless-relevant additions (1.4.3):** `SirilInterface.save_undo_state` now
  works headless; new **`pyscript -async`** (background script execution);
  automatic startup-script execution; new `open_dialog()`. These matter to an
  orchestration layer that drives Siril non-interactively.

### 2. The three gaps — all CONFIRMED still open natively (fresh primary evidence)
This is the load-bearing result: the toolkit's decision to reach *outside* Siril
for these three is re-validated against current docs, including 1.5.0-dev.

- **(a) Chrominance / colour-noise — NO native tool, still.** The denoise docs
  (both 1.4.4-stable and 1.5.0-latest) carry the *identical* disclaimer:
  *"chrominance noise tends not to be well modelled as AWGN and requires different
  treatment. At present chrominance noise is best tackled in general purpose image
  manipulation software such as The GIMP."* `rmgreen` (SCNR) removes a green cast
  only, not chroma noise. → The gap the removed corings covered is real; fill it
  with an external AI denoiser (NoiseXTerminator / GraXpert), never a hand-roll.
- **(b) AI deconvolution — NO native.** Native deconvolution is classical only:
  **Richardson-Lucy (`rl`), Split-Bregman (`sb`), Wiener (`wiener`)**, driven by a
  PSF from **`makepsf`** (blind ℓ0/spectral, PSF-from-stars, or manual
  Gaussian/Moffat/disc/Airy). The two AI deconv paths are **orchestrated externals**:
  GraXpert (stellar+object) and BlurXTerminator. (Our dead-end on classical RL for
  in-exposure trailing stands; the reopening is the *learned* externals.)
- **(c) Star-neutral narrowband balance — NO native.** SPCC's `-narrowband` mode
  does *physical* filter-bandpass calibration (per-channel nominal wavelength
  `-rwl/-gwl/-bwl` + bandwidth `-rbw/-gbw/-bbw`); its white references are
  galaxy/star spectral templates (default "Average Spiral Galaxy") — **none is
  "star-neutral."** So the OIII-sphere star-neutral balance (dead-end registry)
  remains a *process choice* (`rgbcomp`/`ccm`/`pm`/manual or an external like
  Nightlight), not a Siril feature. See [[narrowband-star-neutral-options]].

### 3. Genuinely new native surface since the last pass (1.5.0-dev)
- **A `-mask` switch is being added across processing commands** — confirmed on
  `denoise`, `linstretch`, `autostretch`, `autoghs` — paired with a **new Python
  mask API** (`get/set_image_mask`, `mask_add/subtract_polygon`,
  `get/set_image_mask_state`, sirilpy ≥1.1.0) and a **background-sample API**
  (`get/set/clear_image_bgsamples`). This lets a script confine a native operation
  to a region (e.g. denoise only the starless/background) *without* a hand-rolled
  numpy mask-blend — directly in-bounds for the orchestrate-not-hand-roll model.
  It is **1.5.0-dev, not in 1.4.4** — provisional until the x86 rig runs 1.5.
- No other new *processing* command since 1.4.0; the command set is otherwise
  stable at the syntax the toolkit already documents.

### 4. Confirmed current syntax (headless-relevant, for the operator catalog)
All [PRIMARY-VERIFIED] from readthedocs `latest` / FreeAstro wiki:
- `denoise [-nocosmetic] [-mod=m] [ -vst | -da3d | -sos=n [-rho=r] ] [-indep] [-mask]`
- `ccm m00 m01 m02 m10 m11 m12 m20 m21 m22 [gamma]`
- `synthstar` (no args; synthetic round-PSF star mask for recombination) ·
  `unclipstars` (rebuilds clipped star cores; no documented args)
- `linstretch -BP= [-sat] [-clipmode=] [channels] [-mask]`
- `rgbcomp red green blue [-out=]` **or** `rgbcomp -lum=image {rgb | r g b} [-out=]` (LRGB)
- `subsky { -rbf | degree } [-dither] [-samples=20] [-tolerance=1.0] [-smooth=0.5]`
- `autostretch [-linked] [shadowsclip [targetbg]] [-mask]` ·
  `autoghs [-linked] shadowsclip stretchamount [-b=] [-hp=] [-lp=] [-clipmode=] [-mask]`
- `pm "expression" [-rescale [low] [high]] [-nosum]`
- `rmgreen [-nopreserve] [type] [amount]` (type 0 avg / 1 max / 2 max-mask / 3 additive-mask)
- `satu amount [background_factor [hue_range_index]]` (hue index 0–6)
- `starnet [-stretch] [-upscale] [-stride=] [-nostarmask]` · `seqstarnet seq [...]`
- **drizzle is NOT a standalone command** — it is `-drizzle` on `register` /
  `seqapplyreg`. (Correct the mental model: "drizzle" = a registration option.)
- `savepng filename` (no flags) writes 16-bit RGB PNG (color-type 2, depth 16)
  with an `iCCP` ICC chunk when the loaded image is 16/32-bit; `savetif filename
  [-astro] [-deflate]` writes 16-bit RGB TIFF + ICC (`savetif8`/`savetif32`
  variants). ICC content comes from a prior `icc_assign {sRGB|…}` + a save-time
  Preference. Tested on 1.4.4. (PIL misreads Siril's 16-bit RGB TIFF as uint8 —
  read it with `tifffile`.) These own the finals write; no in-house PNG encoder.
- GraXpert-in-Siril: via the bundled **`GraXpert-AI.py`** script (the old C
  interface was removed in 1.4.0-beta2), headless through `pyscript` with
  `-bge` / `-denoise` / `-deconv_obj` / `-deconv_stellar`. **Deconv needs GraXpert
  ≥ 3.1.0-RC2** (3.0.x = BGE+denoise only) — see [[graxpert-3x-and-workflow-order]].

### 5. Trailed / ultra-wide plate solving — verification SHARPENED (still provisional)
- `platesolve [...] [-localasnet [-blindpos] [-blindres]] [-nocrop] [-order=1..5]
  [-disto=] [-radius=] [-limitmag=] [-catalog=]`. `-localasnet` drives the local
  astrometry.net `solve-field`; `-blindpos` ignores given coords, `-blindres`
  ignores focal/pixel scale (use both when position+scale unknown; needs the index
  files).
- **How stars are fed (the crux):** *even in `-localasnet` mode Siril extracts the
  stars itself first* — *"By default, the star detection uses the **findstar**
  algorithm with the current settings"* — i.e. its **PSF-fitting** finder, on the
  **green layer** for RGB. This is exactly the detection our dead-end says fails on
  trailed stars (`solve_field.py` feeds trail-robust **peak** centroids instead).
- **Ultra-wide detail:** the FOV>5° detection auto-crop is a **Siril-INTERNAL-solver
  behaviour only** — the concept page states it is *"Ignored for astrometry.net
  solves."* So it is not a `-localasnet` failure mode and `-nocrop` is moot there;
  the round-PSF `findstar` detection is the sole mechanism working against trailed
  ultra-wide fields on the localasnet path.
- **`setfindstar ... [-roundness=] [-maxR=] [-relax=on|off] [-sigma=] [-radius=]`:**
  `-relax=on` *"allows relaxation of several of the star candidate quality checks …
  likely to result in a significant increase in false-positive star detections,
  often with wild parameters."* It loosens thresholds — it does **not** turn
  `findstar` into a general peak-centroid detector; the Gaussian/Moffat **roundness
  model still fights elongated/trailed stars**. The knobs to co-tune are `-maxR`
  (max roundness) and `-roundness`, plus `-nocrop`.
- **Assessment (MECHANISM, hypothesis):** native `-localasnet` likely still does
  NOT cleanly replace `solve_field.py` for the trailed ultra-wide class — the
  detector and the >5° crop both cut against it. Retirement of the custom script
  stays UNPROVEN until the x86 empirical test.
  - **Concrete test (x86):** on a real trailed ultra-wide stack, compare (i)
    `setfindstar -relax=on -roundness=0.1 -maxR=<large>` then
    `platesolve -localasnet -blindpos -blindres -nocrop`, vs (ii) `solve_field.py`
    (peak centroids), vs (iii) ASTAP. Metric: solve success + residual RMS +
    wall-clock. If (i) solves reliably, retire the custom script for this class.

### 6. sirilpy — current API + the design philosophy that informs the pyscript question
- **sirilpy 1.1.13** (1.5.0-dev; 1.4.4 line on 1.1.x). Connect
  `SirilInterface().connect()`, run any command via `.cmd()`, mode via `is_cli()`.
- Rich surface: `get_image()/get_image_pixeldata()/set_image_pixeldata()` (NumPy
  in/out), `get_image_stats/fits_header/keywords/iccprofile`, sequence ops,
  `get_image_stars()` (PSFStar) + `pix2radec()/radec2pix()`, and file ops that do
  **not** disturb the loaded image (`analyse_image_from_file`, `load_image_from_file`,
  `save_image_file`), plus a thread-safe `image_lock()`.
- **Design philosophy (decisive for the philosophy question):** the API's shape
  (characterization, not a verbatim doc quote) keeps most data read-only and routes
  edits through Siril commands, with `set_image_pixeldata()` as the one explicit
  direct-pixel-write path — i.e. sirilpy is built to ORCHESTRATE Siril, with a single
  escape hatch.
  A pyscript that stays on `.cmd()` is pure orchestration; one that leans on
  `set_image_pixeldata()` to do its own numpy image-processing is using the escape
  hatch — which is the exact line the "tool vs hand-roll" question must draw. Fed
  to [[siril-pyscript-headless]].

## Sources
- Siril news / releases — https://siril.org/posts/ · 1.4.0
  https://siril.org/download/2025-12-05-siril-1-4-0/ · 1.4.3
  https://siril.org/download/2026-05-06-siril-1-4-3/ · 1.4.4
  https://siril.org/download/2026-06-17-siril-1-4-4/
- Denoising (chroma-noise disclaimer, stable + latest) —
  https://siril.readthedocs.io/en/stable/processing/denoising.html ·
  https://siril.readthedocs.io/en/latest/processing/denoising.html
- Deconvolution (native rl/sb/wiener + makepsf) —
  https://siril.readthedocs.io/en/stable/processing/deconvolution.html
- SPCC (`-narrowband`, white refs) —
  https://siril.readthedocs.io/en/latest/processing/color-calibration/spcc.html
- Platesolving (`-localasnet`, findstar feeder, >5° crop) —
  https://siril.readthedocs.io/en/stable/astrometry/platesolving.html ·
  https://siril.readthedocs.io/en/latest/astrometry/platesolving.html
- Dynamic PSF / `setfindstar -relax` —
  https://siril.readthedocs.io/en/latest/Dynamic-PSF.html
- GraXpert-in-Siril — https://siril.readthedocs.io/en/stable/processing/graxpert.html
- Python API (sirilpy 1.1.13; mask/bgsample APIs) —
  https://siril.readthedocs.io/en/latest/Python-API.html
- Commands reference (1.5.0) — https://siril.readthedocs.io/en/latest/Commands.html
- FreeAstro wiki, Commands — https://free-astro.org/index.php/Siril:Commands
- RC-Astro tools in Siril — https://siril.org/2026/06/rc-astro-tools-available-in-siril/

## Verdict / recommendation
- **Keep Siril as the free+headless substrate**; the 1.4.x line is stable and the
  toolkit's native syntax is current. Nothing to chase (no 1.5 stable yet).
- **The three external-tool decisions stand, re-validated:** chroma-noise,
  AI deconvolution, and star-neutral narrowband are still *not* native — the
  toolkit correctly reaches outside Siril for them. Re-cite this evidence rather
  than re-deriving it.
- **Track 1.5.0's `-mask` + Python mask API** — it is the first native path to
  region-confined processing (e.g. denoise-on-starless) and is squarely in-bounds;
  adopt it when the x86 rig runs 1.5.
- **Trailed solve:** keep `solve_field.py` as the trailed-class tool; the native
  path is likely-insufficient because findstar PSF-fit detection works against
  trailed ultra-wide fields (the >5° detection crop does not apply to localasnet —
  it is "ignored for astrometry.net solves").
  Run the concrete x86 test before any retirement.

## Status
**PROVISIONAL (mechanism / doc-verified).** All native-syntax and gap findings are
primary-sourced from current Siril docs; the trailed-solve conclusion is a
mechanism assessment pending the named x86 empirical test. No image processing was
performed (research-only session).

## Graduation
- **TOOLS.md Tier 2** — sharpen the native-solve verification: add the `findstar`
  green-layer detail, the **`-nocrop` >5° crop** failure mode, and the specific
  `-maxR`/`-roundness` co-tune; keep `solve_field.py` for the trailed class.
- **TOOLS.md Tier 5/6/10** — add fresh-citation confirmation that the AI-deconv,
  chroma-noise, and star-neutral gaps remain non-native as of 1.5.0-dev.
- **TOOLS.md** — note **1.5.0-dev `-mask` + Python mask/bgsample API** as the
  coming native path to region-confined ops; note `drizzle` is `-drizzle` on
  register (not a standalone command).
- **The dead-end registry (`docs/dead-ends.md`)** — reinforce the trailed-solve entry with the findstar +
  >5°-crop mechanism; reinforce the chroma-noise-gap entry (still non-native in
  1.5.0-dev).
- Done in this commit (see below).
