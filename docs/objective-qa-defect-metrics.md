# Objective image-quality & processing-defect metrics for the audit layer — deep dive

- **Question / scope** — The AUDIT side (the measurement layer IS the product): what
  MODERN + STANDARD objective image-quality and **processing-defect** metrics could a
  numpy/scipy measurement layer (no GPU) ADOPT to grade images and — the high-value
  part — **objectively detect over-processing** (deconvolution ringing, denoise
  over-smoothing, background over-flattening, star-colour loss, chroma noise)? This
  extends `lib/astrometrics.py`, `lib/bg_qa.py`, `qa/object_integrity.py`,
  `qa/inspect_stage.py` — the durable core the reset kept.
- **Context** — 2026-07-14. Rig: x86-64, numpy/scipy/**astropy** (photutils
  optional), **no GPU**. Existing harness already computes: the statistical-sky gate,
  `star_shell_report`, radial profiles, chroma-neutralization / mid-scale-mottle /
  gross-flattening audits, per-frame registration QA. Every metric below is
  CPU/numpy/scipy-computable. This is EXAMINING, not processing — squarely in-bounds.

## Findings

### Area 1 — Frame / subframe grading (the SubframeSelector vocabulary, defined)
Primary-verified via the PixInsight "New Image Weighting Algorithms" doc (Conejero,
Radice, Sartori 2022), which reproduces the full SubframeSelector property list.
Each is per-subframe; PSF ones need PSF fits (elliptical Gaussian/Moffat via
Levenberg–Marquardt; Auto keeps least-absolute-residual over Moffat β∈{2.5,4,6,10}).

- **FWHM** — robust mean of per-star FWHM (lower = sharper). **Eccentricity** —
  robust mean of per-star eccentricity (0 round → 1 elongated; tracking/wind).
  Closed forms after fitting: Gaussian `FWHM=2.3548σ`; Moffat
  `FWHM=2α√(2^(1/β)−1)`; `e=√(1−(b/a)²)`; Siril roundness `r=FWHMy/FWHMx`.
- **StarResidual** — robust mean of the per-star Winsorized MAD of PSF-fit residuals.
  **This is a PSF goodness-of-fit metric** — how well a clean Gaussian/Moffat
  describes the stars. It RISES when stars are distorted/aberrated/over-processed →
  a first-class **over-processing sensor** (see Area 3).
- **Noise** — MRS estimate by default (Area 2). **SNR** — ratio-of-powers (Area 2);
  **SNRWeight is just an alias for SNR** (not a separate algorithm — a common
  misconception to avoid). **Stars** — detected+fitted count (transparency/clouds).
- **MStar (M\*)** / **NStar (N\*)** — robust background / robust noise (Area 2).
  **PSFFlux** (Σ flux, transparency), **PSFTotalMeanFlux** (Σ mean flux; signal
  *concentration* → resolution; inverse-correlates with FWHM).
- **PSFSignalWeight (PSFSW)** — the comprehensive weight; structure:
  `PSFSW ∝ (ΣPSFFlux · ΣPSFTotalMeanFlux) / (σ_noise · M\*)` × constants tuned so
  median≈1. Deliberately sensitive to gradients (via M\*) and clouds (flux), which
  plain SNR is not. **Numpy proxy** (no proprietary constants):
  `(sum_flux*sum_meanflux)/(noise*Mstar)`, ranked within a dataset. It reproduces to
  R²≈95–99% from just `SNR², SNR, Stars` — so even without PSF photometry a numpy
  layer can approximate it.
- **Sigma variants** — every property also exposes a value "in sigma units of the
  MAD from the median," i.e. a **robust z-score** ready for outlier gating.
- **Siril's own** frame metrics (Plot page): FWHM, roundness `r=FWHMy/FWHMx`,
  Background, #Stars, X/Y shift, Amplitude, SNR, and **wFWHM** (FWHM weighted by star
  count — more stars → better at equal FWHM, down-weighting thin-cloud frames) and a
  planetary **Quality** [0,1] score. (wFWHM/Quality exact formulas UNCONFIRMED.)

### Area 2 — Robust noise / SNR / background (lift near-verbatim)
- **MAD std** (workhorse): `σ = 1.4826·median(|x−median(x)|)`
  (`scipy.stats.median_abs_deviation(x, scale='normal')`). Robust to sources.
- **Sigma-clipped stats** (astropy `sigma_clipped_stats`, default sigma=3, maxiters=10)
  → robust (mean, median, std).
- **Background2D** (photutils): tile → per-tile sigma-clipped estimator (default
  SExtractor `2.5·median−1.5·mean`) → median-filter the mesh → interpolate. Builds a
  reference background model — the machinery for the over-flattening detector (Area 5).
- **MRS multiresolution noise** (Starck & Murtagh 1998; PixInsight default): à-trous
  (B3-spline) wavelet transform → iterative k-sigma "multiresolution support" of
  significant structure → σ = std of non-support pixels, on the first ~4 layers,
  ~1% accurate; falls back to k-sigma clipping. Fully numpy/scipy (à-trous = fixed
  separable convolutions).
- **N\*** (robust, distribution-free): `N* = c·MAD(MMT_background_residual(scale=256))`
  (or Rousseeuw–Croux `Sn`). MMT = iterative `scipy.ndimage.median_filter` at radii
  1,2,4,…,256; residual isolates non-structure pixels. Relative estimator (compare
  like images). **M\*** = robust mean of pixels below the same 256-px background model
  → gradient-immune background level (reuse for gross-flattening).
- **SNR** (ratio of powers): `SNR=scale²/σ_noise²`. Per-channel: compute all
  independently on R,G,B. Caveat: SNR treats gradients/LP as "signal" — don't weight
  cloud/gradient-varying sets by it (use PSFSW/N\*).

### Area 3 — Over-sharpening / deconvolution-RINGING detection (high-value, reuses radial profiles)
Deconvolution/USM overshoot makes a **dark ring (negative "moat") + outer bright
ridge** around bright stars. Objective detectors a numpy layer can build:
1. **Radial-profile undershoot (best; reuses the existing radial-profile code):** for
   each bright non-saturated star, azimuthally-average I(r); a clean star decays
   monotonically to background B. Ringing ⇒ `min_r I(r) < B − τ·σ_bg` just outside
   the FWHM, often followed by `I(r) > B`. Metrics: undershoot depth `(B−minI)/σ_bg`
   and fraction of bright stars showing it → a scalar ringing score.
2. **StarResidual rise** (Area 1): over-processing pushes stars off a clean
   Gaussian/Moffat → PSF-fit residual increases objectively. Cheap if PSFs already fit.
3. **High-frequency energy ratio:** starlet layer-1 (or FFT annulus) energy / total;
   over-sharpening raises it vs the un-sharpened baseline.
4. **Edge overshoot:** at strong edges, (max-above − min-below)/step-height; inflated
   by over-sharpening. (Also the literature's histogram-aberration + PSF-frequency
   ringing detectors, heavier to implement.)

### Area 4 — Denoise over-smoothing ("plastic") detection
1. **Residual-whiteness / autocorrelation (the principled one):** residual
   `R = pre − post` should be white noise. 2-D autocorr via `ifft2(|fft2(R)|²)` — a
   clean denoise gives a sharp central spike, ~0 elsewhere; **over-smoothing leaves
   STRUCTURE in R** (side-lobes = signal eaten). Quantify: % of autocorr coeffs
   outside ±1.96/√N (≫5% ⇒ over-smoothed), or a Ljung–Box-type statistic.
2. **Fine-scale-energy vs noise floor:** map local variance
   (`scipy.ndimage.uniform_filter` of x²−mean²) or starlet fine-layer energy in
   background/nebulosity; if `finescale_std ≪ σ_noise` (Area 2), texture below the
   physical shot-noise floor was removed → "plastic."
3. **Entropy / KL** of local histograms before/after flags aggressive redistribution.

### Area 5 — Background over-flattening (nebulosity eaten by BGE)
1. **Removed-model spectral content:** the *removed* component (`input − output`, the
   BGE model) should be smooth/low-order. If it carries high-spatial-frequency power
   or correlates with a masked structure map, real signal was subtracted. Flag when
   the removed-model gradient magnitude exceeds a low-order polynomial/spline fit.
2. **Negative-bowl detection:** after flattening, `background_near_object <
   background_far` (a mexican-hat suppression around bright nebulosity) = over-flattened;
   residual large-scale gradient (`scipy.ndimage.gaussian_gradient_magnitude` on the
   source-masked background) = under-flattened. (Directly formalizes the existing
   gross-flattening audit + the dead-end registry's "BGE absorbs frame-filling faint
   nebulosity.")
3. **Faint-flux conservation:** integrated flux in faint outer-nebulosity annuli
   before/after; a drop beyond noise = nebulosity eaten.

### Area 6 — Clipping / star-colour / chroma noise
- **Clip fractions:** highlight `mean(x≥1−ε)` + black `mean(x≤ε)` per channel (both
  tails). A linear black-point shift is fine; histogram compression that clips is a
  bandaid — this measures it.
- **Star-colour loss:** fraction of detected stars with cores saturated in all 3
  channels (irreversible white); per-star core chroma (HSV S, or |a\*|,|b\*|) — a
  declining trend over processing = colour loss. Measure colour on unsaturated ring
  pixels.
- **Chroma noise:** convert to YCbCr / CIELAB, measure MAD noise in the **chroma
  channels separately** on the source-masked background; chroma noise shows as
  elevated σ at **coarse** scales (starlet coarse-layer chroma energy). Formalizes the
  chroma-neutralization audit and quantifies the gap NXT-AI3/GraXpert fill.

### Area 7 — 2024–2026 blind / no-reference IQA
- **Gradient-decay sharpness** (arXiv 2410.10488, 2024; numpy-ready): 5×5 Sobel →
  keep 98.5–99.5th-pct edges → Gaussian-blur (σ=1) → decay `(G−G_blur)/G`,
  `S=100·mean`. Sharper images lose more on re-blur ⇒ larger S. Per-frame sharpness
  grade AND an over-smoothing sensor. All `scipy.ndimage`.
- **Classic focus operators** (relative grading within a dataset): variance-of-Laplacian,
  Tenengrad (noise-robust), Brenner, normalized variance (Pertuz 2013; MDPI Sensors
  2025 re-eval).
- **Blind NSS** (NIQE opinion-unaware / BRISQUE): MSCN + GGD features are pure numpy,
  but the "pristine natural-image" prior does NOT match starfields → astro scores are
  **relative only**, never absolute.
- **Astronomy-specific IQA** exists but is early/ML: AutoML-on-FITS quality rating
  (arXiv 2311.10617, DATA2024); a 2025 low-compute astro-IQA paper; a 2025 labelled
  FITS IQA dataset (unconfirmed). Useful as direction, not drop-in.

## Sources
- PixInsight Image Weighting (PSFSW/PSFSNR, M\*/N\*, MRS, full SubframeSelector list, PSF fitting) — https://pixinsight.com/doc/docs/ImageWeighting/ImageWeighting.html
- photutils Background (MAD/sigma-clip/Background2D/SExtractor) — https://photutils.readthedocs.io/en/stable/user_guide/background.html
- Starck & Murtagh 1998, MRS noise (PASP 110:193) — https://iopscience.iop.org/article/10.1086/316124
- No-reference gradient-decay sharpness (arXiv 2410.10488) — https://arxiv.org/html/2410.10488
- Siril Plot metrics — https://siril.readthedocs.io/en/stable/Plot.html
- getimages background/flattening (A&A 2017) — https://www.aanda.org/articles/aa/full_html/2017/11/aa30925-17/aa30925-17.html
- Geometric background estimation (arXiv 2411.17566) — https://arxiv.org/html/2411.17566v1
- Deconvolution ringing (dark rings) — https://siril.readthedocs.io/en/latest/processing/deconvolution.html · https://astrodoc.ca/revealing-hidden-detail-deep-sky-images-deconvolution/
- Residual whiteness diagnostics — https://otexts.com/fpp3/diagnostics.html
- Focus measures (Pertuz 2013; MDPI Sensors 2025 25(10):3144) — http://isp-utb.github.io/seminario/papers/Pattern_Recognition_Pertuz_2013.pdf · https://www.mdpi.com/1424-8220/25/10/3144
- NIQE — https://www.mathworks.com/help/images/ref/niqe.html · Astro-IQA AutoML — https://arxiv.org/abs/2311.10617
- Chroma noise (ISO 15739) — https://www.imatest.com/docs/color-tone-esfriso-noise/ · Star-colour loss — https://www.astropix.com/html/processing/starcolr.html

## Verdict / recommendation
The high-value, fully-numpy additions for the x86 measurement layer, prioritized:
1. **Radial-profile undershoot ringing detector** — reuses the existing radial
   profiles; turns "deconv over-sharpened?" into a scalar. Cheapest high-value win.
2. **Residual-autocorrelation whiteness + fine-scale-energy-vs-noise** — objective
   denoise over-smoothing detection (the "plastic" test). Pairs with the new NR tools.
3. **Removed-background-model spectral/negative-bowl analysis** — objective
   over-flattening detection; formalizes the gross-flattening audit + the BGE
   dead-end.
4. **N\* / M\* / MRS noise + background** — lift near-verbatim; a robust,
   gradient-immune noise+background pair the gate and all defect detectors can share.
5. **PSFSW proxy + StarResidual** — a composition-agnostic frame-quality weight and a
   PSF-goodness over-processing sensor; approximable from SNR²,SNR,Stars.
6. **Gradient-decay sharpness (2024)** — per-frame sharpness grade + over-smoothing
   sensor.
These are candidates for the ported/rebuilt audit layer — **measurement, not
processing** — and none needs a GPU. They EXTEND the gate/audits; they never loosen
the gate (per the contract).

## Status
**PROVISIONAL (methods established/computable; not yet implemented or validated
here).** All definitions are primary-verified or standard. This session RECORDS the
candidates; it writes no code and processes no pixels. The concrete test for each,
on a future (non-research) session: implement it, then validate that it fires on
known-bad renders (deliberately over-sharpened / over-smoothed / over-flattened
examples) and stays quiet on known-good ones, on real data — before it can gate.

## Graduation
- **REDESIGN** — add an "audit-layer adoption candidates" note (the measurement
  harness is the crown jewel; these six are the researched next metrics, each a
  measured experiment, gate-never-loosens preserved).
- **MEMORY** — a reference note that the audit side has a concrete, cited metric
  roadmap (SubframeSelector vocabulary, MRS/N\*/M\* noise, and the three
  over-processing detectors), so a future session starts from it rather than re-deriving.
- No TOOLS.md change (TOOLS is the *processing* toolkit; this is the measurement layer).
- Applied in the graduation commit.
