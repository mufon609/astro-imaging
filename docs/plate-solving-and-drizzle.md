# Plate-solving the trailed/ultra-wide class + drizzle sampling — deep dive

- **Question / scope** — Deep-verify Tier 2 for the TRAILED ultra-wide class: ASTAP vs
  astrometry.net vs Siril native — which detection method survives trailing, and is
  feeding astrometry.net peak centroids (our `solve_field.py`) the right move? Plus:
  correct the drizzle guidance for wide/short-focal data.
- **Context** — 2026-07-14. Rig x86-64, no GPU, headless. Our dead-end: Siril's internal
  solver fails ultra-wide trailed fields; we blind-solve astrometry.net from peak
  centroids. Detection-method rankings below are **mechanism inference** (grounded in
  source/doc reads) — HYPOTHESES until one bracketed empirical solve on real trailed data.

## Findings

### Two premise corrections (both primary-verified)
- **ASTAP's wide-field DBs are W08 + G05 — the D-series caps at 6°, and G17/H17/H18 are
  DEPRECATED.** hnsky: *"If you have one of the older H17, H18, V17, G17, G18 star
  databases, they can be uninstalled/deleted."* (So subagent-C's "D50 for ASTAP" is right
  only for *narrow* fields; for OUR ultra-wide class install **W08** + **G05**.)
- **"Wide / short-focal ⇒ oversampled" is BACKWARDS.** `arcsec/px = 206.265 · pixel_µm /
  FL_mm` → short FL (or large pixels) → *large* arcsec/px → a star spans *few* pixels →
  **under**sampled, which is drizzle's home turf, not a reason to skip it. Over-vs-under
  is an empirical FWHM measurement, not implied by "wide." (This refines our dead-end —
  see Graduation.)

### ASTAP as a solver
- **Install (headless):** current **v2026.06.29** (date-versioned); `.deb` available →
  `/opt/astap` (fallback `/usr/share/astap/data/`). Use the barebone **`astap_cli`** (no
  pop-ups, no raw files) headless; `libssl-dev` if TLS errors. (`astap_cli` may be a
  separate download from the GUI `.deb` — verify.)
- **DB → FOV** (verbatim ranges; all Gaia-based): **W08 "80°>FOV>20°" (only 276 kB!)** ·
  **G05 "20°>FOV>3°" (101 MB)** · D05 "6°..0.6°" · D50 "6°..0.2°" (867 MB, narrow default)
  · D80 (1.2 GB) · V50/V05 (photometry). → **ultra-wide = W08 + G05.** A wrong-DB pick
  (D-series above 6°) is a top wide-field failure cause.
- **Detection = HFD (half-flux-diameter) flux-weighted centroid, NOT a PSF fit.** Source
  reads (`unit_stack.pas`) show the accept test is size + SNR only — `((hfd1<=~15) and
  (snr>snr_min) and (hfd1>hfd_min))` — **no roundness/axis-ratio term** (HFD is radially
  symmetric). The quad matcher hashes 4-star asterisms into a rotation/scale/flip-invariant
  code (tol 0.007) — **star shape never enters it.**
- **Trailing tolerance: better than Siril findstar for MILD/MODERATE trailing, with a
  ceiling.** No shape filter → a trailed star is kept while its peak SNR stays up and HFD
  stays under the cap; a flux-weighted centroid sits at the trail midpoint, so *uniform*
  mild trailing shifts all centroids consistently and preserves the quad ratios. **But
  ASTAP's own docs:** *"Oval stars due to tracking errors or severe optical distortion
  will be ignored and solving could fail."* Risk case (inference): non-uniform/rotational
  trailing shifts centroids differently per star and distorts ratios.
- **Key levers for trailed/wide:** **`-z` downsample (0=auto)** (bins → raises SNR, shrinks
  trail px-length under the HFD cap), `-speed slow`, accurate `-fov`, `-s` up to 1000.
  ```
  astap_cli -f widefield.fits -fov 0 -r 180 -z 0 -d /opt/astap -wcs -update -log   # blind
  astap_cli -f img.fits -ra 5.279 -spd 135 -fov 1.56 -r 15 -update                 # hinted (spd=Dec+90)
  ```

### astrometry.net — and why peak-centroids are the INTENDED path
- **Index series:** **4100 (Tycho-2), scales 7–19 = the wide-field set** (">1°");
  5200-LITE (Tycho-2+Gaia-DR2, scales 0–6) = narrow; 4200 = 2MASS (not Gaia). Numbering
  is scale-based (last two digits = quad-size tier); scale 19 ≈ 23–33° is the ceiling.
  Install the **whole 4100 set (4107–4119, 13 tiny files)** for wide/ultra-wide → apt
  `astrometry-data-tycho2` → `/usr/share/astrometry/`; `astrometry.cfg` `add_path`/
  `autoindex`/`index`. Rule: index quads 10–100% of image width.
- **Built-in extractor `simplexy`/`image2xy` = PEAK-pixel flux, NOT a PSF fit** (source:
  *"the flux of each object as the value of the image at the peak"*). And solve-field
  **accepts an XYLIST directly** (FITS BINTABLE of X,Y) — when supplied, **no source
  extraction runs at all**. The matcher (Lang et al. 2010) is **purely geometric /
  shape-blind** — inputs are ordered (x,y) only; brightness is sort-order alone. → **feeding
  our peak centroids is the *intended* override, not a workaround** — precisely what
  `solve_field.py` does. The one measurable cost: a trail displaces the peak from the true
  position by up to ½ the trail length → sets the astrometric residual floor, does not
  prevent a match.
- **solve-field for trailed/wide:** `--downsample 2..4`, `--sigma` (raise to kill spurious
  detections), `--objs`/`--depth`, **`--scale-units degwidth --scale-low 20 --scale-high 60`**
  (pinning scale is a big robustness/speed win), `--no-plots`, `--overwrite`, `--cpulimit`.
  ```
  solve-field --x-column X --y-column Y --sort-column FLUX --width W --height H \
    --scale-units degwidth --scale-low 20 --scale-high 60 --no-plots --overwrite peaks.xyls
  ```

### Head-to-head ranking for the TRAILED ultra-wide class (mechanism inference)
1. **astrometry.net fed our own peak-centroid xylist — most robust.** No shape filter, we
   control the centroids; matches the untracked all-sky / meteor-network precedent. **Validates
   `solve_field.py`.**
2. **ASTAP + W08/G05 — second.** HFD/centroid, no roundness gate, shape-blind quads;
   tolerates mild trailing where Siril rejects it, **but needs the correct wide DB** or it
   silently fails; severe/rotational trailing still breaks it.
3. **Siril native (internal AND `-localasnet`) — least robust here.** Load-bearing:
   `-localasnet` does **not** hand the raw image to astrometry.net — Siril *"extracts the
   stars from your images [with findstar] and submits this list to solve-field."* findstar
   is a **PSF fit with an explicit roundness reject** (default 0.5 keeps stars ≤2× wide-as-high;
   trailed stars fall below and are discarded *before* matching), **plus the FOV>5° detection
   crop unless `-nocrop`.** This is the documented mechanism behind our dead-end.

### 2026 solver improvements
- **Siril 1.4.0 (2025-12-05):** SIP-convention solving + astrometry.net blindsolve;
  distortion correction in registration; new offline **Gaia-DR3** catalogs (~1.5 GB).
- **ASTAP (2026):** relaxed max-HFD 10→~15–16 (accepts more diffuse/slightly-trailed blobs);
  overhauled bright-star extraction; *"solving improved for star-poor images; removed triples."*
- **astrometry.net:** engine stable ~18 mo; active work is Gaia-based custom indices.

### Drizzle — the sampling truth for the wide/short-focal class
- **What it is:** Fruchter & Hook 2002, *"Variable-Pixel Linear Reconstruction of
  **Undersampled** Images"* — undersampling is the design target. Each input pixel is shrunk
  (pixfrac) then rained onto a finer grid (scale). Reconstruction, **not** sharpening.
- **Helps only with ALL THREE:** (1) **undersampled** data, (2) **sub-pixel dither** across
  frames, (3) **many** frames. Nyquist: critically sampled ≈ **2 px across the FWHM**;
  **<2 px = undersampled (drizzle can help); >2–3 px = oversampled (it can't)** — Siril:
  *"If your sampling is correct… Drizzle can't produce detail beyond the diffraction limit."*
- **Pointless/harmful on oversampled/under-dithered data:** bigger files, **amplified +
  correlated noise**, holes/gridding (small pixfrac + few frames), an SNR hit (scale 2 /
  pixfrac 0.5 ≈ ÷4 signal/px), 4× disk/CPU at 2×.
- **The honest answer for our class:** decide from **measured FWHM, not the "wide/short-focal"
  label** (which points the wrong way — short FL is usually *under*sampled). **If measured
  FWHM ≥ ~2–3 px** (soft/aberrated fast lens, bloated stars) → skip upscale-drizzle (our
  intuition holds *for that measured case*). **If FWHM < 2 px** → 2× can help, **but only**
  with real sub-pixel dither + many accurately-registered frames.
- **Two nuances for trailed data:** (a) a trail is wide along one axis, narrow across —
  **judge sampling by the minor-axis (across-trail) FWHM**; a trailed field can be optically
  *undersampled* even though trails look large (inference — verify). (b) **Drizzle can't
  de-trail** (it renders a sharper *smeared* star), and trailing tends to break the
  dither/registration preconditions → the pragmatic default for a trailed ultra-wide
  sequence is **skip upscale-drizzle unless FWHM + dithering both check out.**
- **CFA/Bayer drizzle (separate axis):** for OSC, Siril recommends **scale=1.0, pixfrac=1.0**
  even at nominal sampling (cleaner colour noise than interpolated demosaic) — an
  always-consider 1× option; 2×/3× CFA drizzle still needs genuine undersampling + dither.
  pixfrac ≈ 1/scale; scale 2× practical max.

## Sources
- ASTAP — https://www.hnsky.org/astap.htm (v2026.06.29, obsolete-DB quote, solve conditions) ·
  quad mechanism https://www.hnsky.org/astap_astrometric_solving.htm · changelog https://www.hnsky.org/history_astap.htm ·
  DB→FOV https://sourceforge.net/projects/astap-program/files/star_databases/ · source `unit_stack.pas` (github.com/han-k59/astap, indigo-astronomy/astap) · "oval stars ignored" https://ap-i.net/ccdciel/en/documentation/astap
- astrometry.net — https://data.astrometry.net/ · readme/build-index (github.com/dstndstn/astrometry.net) ·
  `util/simplexy.c` ("flux = value at the peak") · `etc/astrometry.cfg` · solve-field(1) manpage · Lang et al. 2010 https://arxiv.org/abs/0910.2233
- Siril — platesolving https://siril.readthedocs.io/en/stable/astrometry/platesolving.html (localasnet extracts stars itself; FOV>5° crop) ·
  Dynamic-PSF https://siril.readthedocs.io/en/stable/Dynamic-PSF.html (findstar roundness 0.5) · 1.4.0 https://siril.org/download/2025-12-05-siril-1-4-0/
- Drizzle — Fruchter & Hook https://arxiv.org/abs/astro-ph/9808087 · STScI drizzlepac · Nyquist https://vikdhillon.staff.shef.ac.uk/teaching/phy217/instruments/phy217_inst_sampling.html · Siril drizzle https://siril.readthedocs.io/en/latest/preprocessing/drizzle.html

## Verdict / recommendation
- **Keep `solve_field.py` (astrometry.net + peak-centroid xylist) as the trailed-class
  tool — it is the *intended* shape-blind override, now confirmed from source.** Pin the
  scale (`--scale-low/high`) for wide fields.
- **Add ASTAP + W08/G05 as a fast complementary solver** for mild/moderate trailing
  (`-z auto`, `-speed slow`) — worth a bracketed comparison on real data; it needs the
  correct wide DB.
- **Native Siril `-localasnet` stays least-robust here** (findstar PSF-fit + roundness
  reject + >5° crop) — use `-nocrop` + relaxed findstar only as the x86 test, not the default.
- **Drizzle: measure the minor-axis FWHM.** Oversampled → skip; genuinely undersampled +
  dithered + many-frame → 2× can help; but trailing usually breaks the preconditions, so
  default to skipping upscale-drizzle for trailed data. **CFA-drizzle 1× is the OSC default.**

## Status
**PROVISIONAL.** Install/CLI/detection-method facts are PRIMARY-VERIFIED (vendor docs +
source). The trailing-robustness *ranking* and the trailed-FWHM/minor-axis reasoning are
mechanism inference — the settling test: one real trailed ultra-wide set solved three ways
(own-xylist solve-field / ASTAP+W08 / Siril `-localasnet -nocrop`), report solve-rate +
residual RMS + wall-clock; and measure minor-axis FWHM + dither before any drizzle.

## Graduation
- **TOOLS.md Tier 2** — ASTAP row: **W08/G05 for wide** (D-series caps at 6°; G17/H17
  deprecated), HFD-centroid (no roundness gate) tolerates mild trailing; add the 3-way
  robustness ranking; note astrometry.net xylist-of-peaks is the *intended* override
  (validates `solve_field.py`); `--scale-low/high` pin.
- **REDESIGN dead-ends** — (a) strengthen the trailed-solve entry with the detection-method
  ranking + the xylist-is-intended confirmation; (b) **CORRECT the drizzle entry**: "short
  focal / large pixels ⇒ oversampled" is backwards (that geometry is *under*sampled); the
  data is oversampled only if star *trailing/bloat* spreads it — judge by **minor-axis
  FWHM**; drizzle is pointless for trailed data because trailing breaks dither/registration
  and drizzle can't de-trail, NOT because short-focal implies oversampling.
- Applied in this deep-dive's commit.
