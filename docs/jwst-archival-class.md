# JWST archival class — acquisition, processing, and the Jupiter recreation — deep dive

- **Question / scope** — The workspace's first ARCHIVAL data class: no photons
  shot here — acquisition means querying MAST and pulling the official STScI
  pipeline's calibrated products; processing means turning per-filter float
  mosaics into palette composites under the same contract as every other class
  (official tools own pixels + measurements; the user gates downloads and every
  aesthetic step; records pin provenance). First goal, user-declared: recreate
  the famous 2022-08-22 JWST Jupiter releases from their public data.
- **Context** — 2026-07. astropy 8 on both rigs; astroquery in the
  auto-bootstrapped `~/.local/share/jwst-venv` (`scripts/jwst/acquire.py`);
  `reproject` = pip on x86 (aarch64 wheels unverified); Siril 1.4.4;
  FITS Liberator v5 (2025-11, python, batch) available if the GUI reference
  route is wanted. The web GUI has a dedicated JWST page (Acquire / Process /
  Examine) over the fixed stage registry.

## Findings

### 1. Acquisition (rig-verified through `query`)

- **Public JWST data needs no MAST account or token** (EAP data out of scope).
  The scripted route is `astroquery.mast`: `query_criteria` by **proposal ID**
  (never cone-search for moving targets — MAST's own guidance), chunked
  `get_product_list` (≤5 obs/call, STScI bulk guidance), `filter_products` to
  **per-filter stage-3 `_i2d`** (SCIENCE / I2D / calib_level 3 — what release
  composites are built from), `download_products(curl_flag=True)` for a
  resumable pull. An anonymous AWS mirror exists for large volumes.
- **Products**: `_i2d` = drizzled, CR-cleaned, background-matched, distortion-
  free float32 **MJy/sr** mosaics; extensions SCI/ERR/CON/WHT/VAR_* (no DQ —
  quality lives in weights + NaN); the header FITS WCS on resampled products
  matches the authoritative gwcs to ~1e-4 px. NaN fills the out-of-footprint
  region — a known GUI-tool killer (PixInsight 1.9.4 chokes); handle NaN
  explicitly in the prepare stage.
- **Reproducibility anchors**: `CAL_VER` + `CRDS_CTX` headers pin which
  quarterly STScI reprocessing built each product (the whole archive re-runs
  ~every 3 months) — `acquire.py verify` records them in the tracked
  `acquisition_manifest.json`. Full `jwst`-pipeline reprocessing is OVERKILL
  for aesthetics (50–100 GB CRDS cache); the one useful middle path if grids
  misbehave: re-run stage 3 only, with a shared output grid.
- **Cross-filter astrometry caveat**: stage-3 tweakreg aligns to Gaia when it
  can; same-instrument filters of one observation are usually consistent, but
  MIRI↔NIRCam (and unlucky fields) can carry silent offsets — verify by star
  centroids after reprojection, never assume.

### 2. Processing (the consensus shape, tool-fit for this workspace)

Every practitioner route — STScI's own imagers included — reduces to:
**per-filter `_i2d` → SCI extract → reproject onto ONE grid → per-filter
float-domain stretch (asinh-class) → chromatic-order palette (short λ = blue …
long λ = red; interposed hues for >3 filters) → composite → cosmetic pass →
one 16-bit quantization at export.**

- **Alignment**: astropy `reproject` onto a chosen reference WCS is the
  STScI-notebook-sanctioned route. MJy/sr is surface brightness — exactly
  reproject's assumption, so values carry across pixel scales unscaled.
  `reproject_interp` (fast) or `reproject_adaptive` (downsampling hops);
  **`reproject_exact` is documented-wrong below 0.05″/px** (NIRCam SW is
  0.031″). Siril's global star registration also demonstrably aligns JWST
  mixed-scale filters (community-verified) — the fallback if reproject's
  result disagrees with star centroids.
- **Stretch**: asinh is the field standard (STScI: FITS Liberator). Headless:
  Siril `asinh`/`autoghs` per filter (bracketed, recorded), or FITS Liberator
  v5 batch with sidecar params. All stretching in float; **16-bit exactly once
  at export** (Siril `savepng` from 32-bit is the clean final hop).
- **Palette**: chromatic ordering is a CONVENTION, not calibration — SPCC/PCC
  are meaningless here (recorded skip). 3-filter composites map straight to
  R/G/B (Siril `rgbcomp`); >3 filters need weighted pre-mixes (astropy
  `make_rgb` / Trilogy territory, or `pm` channel math).
- **Known artifact classes in stage-3 products**: NIRCam wisps/claws/1-f
  striping remnants, MIRI cruciform, saturated cores arriving as black/NaN
  holes, ragged mosaic borders. Cosmetic handling is per-corpus, documented,
  never silent.
- **Siril probes needed before it joins the chain** (pre-registered): float
  MJy/sr load behavior (auto-rescale heuristic per file — decouples filters'
  common scale; acceptable for independent per-filter stretches), NaN
  tolerance headless, and whether `seqapplyreg`-class astrometric registration
  can consume the archive WCS without a Siril re-solve.

### 3. The Jupiter recreation (PID 1373, ERS — the declared first goal)

Provenance (verified from the APT file, NASA/ESA captions, MAST CAOM):

| release image | observations | filters → display colors (caption-verbatim) | epochs |
|---|---|---|---|
| Wide-field (rings + Amalthea/Adrastea + trailed "photobombing" galaxies) | **obs 8** (FULL, Module B) | **F212N → orange, F335M → cyan**; "combination of short and long exposures" spans the ~10⁶ disc-to-ring contrast | SW+LW **simultaneous** — 2022-07-27 10:51–11:00 UT |
| Close-up (two-hemisphere aurora) | **obs 6** (SUB640 4-tile) + **obs 8** | **F360M → red, F212N → yellow-green, F150W2(×F164N) → cyan** (the asset page lists F164N — the pupil-wheel element crossed with F150W2) | obs 6 10:24–10:36 + obs 8 10:51–11:00 → **9–22° of rotation between components** |

- Processed by **Judy Schmidt** (close-up; wide-field with **Ricardo Hueso**),
  Photoshop, from MAST level-3 products. No full step-by-step was published
  (honest gap); her stated crux: Jupiter rotates ~0.6°/min, so she built
  "three congruent images" — derotation/warping to a common epoch — before
  compositing; the disc also spans detector tiles (obs 6's 4-tile mosaic,
  ~7° of rotation within the observation itself).
- **The L3 `_i2d` products are stacked in Jupiter's rest frame** (the
  pipeline's `assign_mtwcs` moving-target step) — background stars/galaxies
  trail by construction; the disc does not.
- **The minimal dataset is measured and small**: o006 F360M 15.5 MB + o006
  F150W2-F164N 75.2 MB + o008 F212N 525.1 MB + o008 F335M 120.5 MB ≈
  **0.75 GB** (second epoch o007/o009 doubles it to ~1.6 GB). Fits either rig
  trivially.
- **The science team's own derotated Jupiter composites are published CC-BY**
  (github.com/JWSTGiantPlanets/Jupiter-Atmosphere-NIRCAM) — the legitimate
  answer key for the close-up's derotation, alongside the released PNGs as
  the aesthetic reference (`sessions/jwst-jupiter/reference/`).
- Expected data quirks: saturated disc-core holes in F212N FULL frames (the
  short+long combination in the release is the workaround — level-2 `_cal`
  products (+~2 GB) are the deeper route if L3 holes block), Io's scattered
  light + aurora-driven diffraction spikes (real signatures, keep), obs 11
  failed → obs 33 replaced it (ring ansa portraits — out of scope for the
  two famous images).

### 4. The recreation plan (phases; each user-gated where output-shaping)

- **J0 — ACQUIRE (the next gate, ~0.75 GB)**: from the JWST tab —
  `list --proposal=1373 --filters=o006,o008` (the filename filter doubles as
  an observation selector; sizes on screen) → `download … --go` →
  `verify` (manifest + anchors). Stage the released PNGs + the team's CC-BY
  derotated frames into `sessions/jwst-jupiter/reference/` (the answer key —
  study before tuning, per the standing rule).
- **J1 — PROBES on the real files** (pre-registered, one knob each): astropy
  SCI/NaN/WCS read; reproject F335M (0.063″) ↔ F212N (0.031″) both
  directions; Siril float-load + NaN behavior; star-centroid cross-check of
  the archive WCS alignment; saturation-hole census on the F212N disc.
- **J2 — WIDE-FIELD recreation first** (simultaneous filters — no
  derotation): reproject to the SW grid → per-filter asinh brackets (the
  10⁶ contrast is the experiment: disc detail vs ring visibility) → 2-filter
  palette (F212N orange, F335M cyan — an rgbcomp/pm mix, orange ≠ pure R) →
  composite → judge vs the reference PNG, like-encoded.
- **J3 — CLOSE-UP recreation** (the hard one): the derotation gap is the
  class decision — candidates: compose from the team's CC-BY derotated
  frames (official science-team products), WinJUPOS-under-Wine (the amateur
  derotation standard), or accept the ~9–22° mismatch and document the
  ghosting. USER DECIDES the route when J2 is judged.
- **J4 — codify**: the prepare/stretch/compose scripts graduate into the
  registry + the JWST tab's Process section as they harden (same pattern as
  the lunar builder).

## Sources

Agent-verified primary sources: astroquery/MAST docs + STScI bulk-download
notebook; jwst-pipeline readthedocs (product types, naming, assign_mtwcs,
calwebb_image3); JDox (EAP, instruments, known issues); DJA on i2d FITS-WCS
accuracy; reproject docs; astropy visualization docs; siril.readthedocs +
ChangeLog + pixls.us JWST thread; ESA/Webb image-processing page;
webbtelescope.org "How are Webb's full-color images made"; DePasquale
tutorial (Sky at Night) + STScI lecture; NASA blog 2022-08-22 (Jupiter
captions verbatim) + ESA mirrors (jupiter-auroras1/2) + science.nasa.gov
asset metadata; STScI APT PDF 1373; Schmidt's Flickr note + Planetary Radio
interview; Berkeley release; Hueso et al. 2023 Nature Astronomy +
JWSTGiantPlanets GitHub (CC-BY derotated composites); NOIRLab FITS
Liberator v5. (Full URL lists live in the three research reports; the
load-bearing ones are cited inline above.)

## Verdict / recommendation

Acquire J0 through the JWST tab (user gate; 0.75 GB), run the J1 probes,
then recreate the WIDE-FIELD image first — it is the honest entry point
(simultaneous filters, no derotation) and settles the stretch/palette/
dynamic-range craft on real data before the close-up's derotation decision.
The class stays astropy+Siril-first (headless, both official); FITS
Liberator v5 is the sanctioned GUI alternative if interactive stretch
tuning earns its place.

## Status

**PROVISIONAL** except: the acquisition route through `query` is
RIG-VERIFIED (venv bootstrap + live MAST query of PID 1373 returned the 30
expected level-3 observations), and the provenance facts are
document-verified. Every processing claim awaits the J1 probes on real
files.

## Graduation

- `TOOLS.md` — the archival-class tier (this doc distilled).
- `BACKLOG.md` item 22 — the phase plan + the J0 gate.
- `scripts/jwst/acquire.py` + the web JWST page (Acquire live; Process
  fills as J2/J4 scripts land).
- `docs/dead-ends.md` — nothing yet; J1/J2 findings graduate with numbers.
