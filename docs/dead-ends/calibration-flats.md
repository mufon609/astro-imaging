# Calibration — synthetic sky flats, darks, masters

Phase-2 file of the dead-ends registry split (`README.md` here holds the index
and dispositions; pre-compression forms live in git and in the live
`docs/dead-ends.md` until the merge). Entries are maintained IN PLACE.
Cross-references to sibling files are written as (`<file>.md`) pointers.
The `sky × V` object tilt is an OPEN defect — status home:
BACKLOG:`calibration-evidence`.

<!-- phase-2: maintained in place; not regenerated from the manifest -->
**Gain / flat** (self-calibration — real flats are the primary path; when they
have issues, synthetic-flat / vignetting correction is a GAP to fill with an
OFFICIAL tool, never an in-house fit. The entries below are methods that FAIL —
the constraints any such tool must satisfy):
- A free-form gain fit bakes sky glow into the gain (peaks off-axis toward the
  glow) — sanity-check any gain by its centre.
- A polynomial radial V(r) oscillates → concentric RINGS after division; only a
  monotone isotonic V is admissible. A per-channel V tints the corners (glow
  contaminates the per-channel falloff) → V must be GRAY.
- The true V lies between the multiplicative and additive fits of the median;
  only the empirical V2 of the frames ACTUALLY being divided is flat.
- Never refine the gain from the STACK's residual — the sky's own structure
  (MW/glow/clouds) exceeds the residual, giving opposite-sign results.
- A SKY FLAT (median of un-registered lights) captures vignetting + optical dust
  motes + PRNU, but frame-filling faint structure does NOT reject — it bakes into
  the flat, and division then ATTENUATES it. The MECHANISM is
  composition-independent — a frame-filling signal cannot reject out of a median
  of un-registered lights, whatever it is made of — and the thing at risk here
  is UNRESOLVED STARLIGHT (`terminology-dust.md`), ~81% of the catalogued
  starlight in this field; naming it correctly matters because the two imply
  opposite handling. The only fix is manual clone-stamping (GUI,
  non-reproducible). So a sky flat is safe for this class ONLY when faint
  structure is a small part of the frame; validate before use (the builder's
  own gates: `scripts/stack/build_sky_flat.sh`; routes: `TOOLS.md` Tier 1).
- **A SKY FLAT BAKES IN ANY SKY GRADIENT THAT IS FIXED IN THE ALT-AZ FRAME — the
  drift cannot reject it, because the CAMERA is fixed in alt-az too.** The
  method's stated enabling condition ("the sky drifts across the sensor, so the
  moving sky rejects out") is true of STARS and of celestial-sphere structure,
  FALSE for brightness structure fixed relative to the HORIZON — moonlight, and
  the airmass gradient — which sits still on the sensor for the whole set and
  integrates straight into the flat. MEASURED via each flat's ODD component
  about centre (cancels the even/radial vignetting): odd plane **4.8–19.4%** of
  centre level on a moonless night, **16.8–22.6%** on a 98%-moonlit one, whose
  DIRECTION tracks the moon's bearing in sensor coordinates to 23° scatter
  (random: ~104°). SCOPE: those percentages are a MIXTURE — a whole-frame plane
  fit cannot separate sky from a repeatable instrumental term, so only the
  magnitudes are overstated as sky; the mechanism stands on its own physics and
  on the decomposition below. (Sizing the defect absolutely is the registered
  dead end below.)
  **Why it is a defect and not free background extraction:** a sky gradient is
  ADDITIVE and a flat DIVIDES. Lights are (sky+object) × vignetting; the
  contaminated flat is vignetting × (1+g); dividing yields (sky+object)/(1+g) —
  the sky's own gradient does come out, but the OBJECT is left modulated by a
  multiplicative tilt it never had. **It also makes the usual flatness check
  self-fulfilling**: corner-vs-centre reads flat on the FINAL stack precisely
  BECAUSE the flat absorbed the gradient and divided it out. Judge the FLAT's
  odd component, not the stack's corners.
  **The shipped builder's flat measures the term directly** (july31/set-01, 507
  frames, Siril `stat` corner medians): `edge_dipole_x` **+0.4312 at box 42 and
  +0.4360 at box 80** (the two geometries agree to 1.1%, so 42 px figures and
  `baseline_guard`'s 80 px convention ARE comparable) — the SAME SIGN as the
  raw dark-subtracted light (+0.426), and **3.6× the same flat's top-bottom
  dipole (+0.1211)**. That ratio is the load-bearing number and needs no
  threshold: vignetting is EVEN and radial, contributing equally to x and y,
  so an excess in x is non-radial BY CONSTRUCTION and cannot be vignetting.
  (july14's −0.44 was measured on a `--desky`-era flat and is not re-measured —
  that session is staged raws-only.) `build_sky_flat.sh` measures both dipoles
  at the edge geometry and records them in the flat's own qa record — reported,
  never gated, because the defect is open and unfixed. **What must NOT be
  inferred: that removing the sky from the flat's SOURCE FRAMES is the fix** —
  that was `--desky`, a 31× regression (next entry). No corrective is shipped.
  **THE ODD COMPONENT IS DECOMPOSED, AND THE OBVIOUS AXIS SPLIT IS WRONG.**
  Instrument (`scripts/qa/flat_odd_component.py`): Siril `fdiv` ratios of flats
  from the same night/lens/focal/aperture — cancels vignetting and the
  instrumental base EXACTLY, no model, no fit — plus `stat` regional medians;
  NEVER `idiv`, and two scalars agreeing after rescale is the no-clip control.
  *The left-right term is SKY, decisively*: it rises monotonically WITHIN all
  three nights (focus untouched inside a night, so a within-night change on
  fixed optics can only be sky), and its edge dipole sweeps continuously across
  the corpus **+0.436 → −0.0255 → −0.385**, which a sensor-fixed term cannot do
  on one body, lens and focal; within aug09 the dose composes multiplicatively
  to 0.08%. *But the top-bottom term is NOT demonstrably the instrument*: T/B
  cancels to 1.000 in every aug09 ratio — and across the corpus it flips sides
  between nights (july31 1.139→1.216 above 1, drifting +6.7% within the night;
  aug06/aug09 below 1) — so T/B carries sky too and **neither axis isolates the
  instrument**. SCOPE, the load-bearing caveat: a ratio cancels what is COMMON,
  so it measures the CHANGE in sky, not the total — the within-night-constant
  term stays UNATTRIBUTED between optics and static sky (per-session focus
  recalibration is a live alternative). Do not design a corrective that
  preserves the T−B term on the grounds that it is optics. Numbers:
  `datasets/aug09/flat_ratio_decomposition.json`,
  `datasets/aug09/corpus_flat_odd_component.json`.
- **THE FLAT'S SHAPE DIFFERENCE REACHES THE DELIVERED OBJECT ESSENTIALLY 1:1 —
  MEASURED, so the bake-in mechanism is no longer only an argument.** The
  DIFFERENTIAL kills both blockers of the absolute dead end below by design:
  two flats of the same optical state and different sky dose (aug09 set-01 vs
  set-05, Δedge dipole 0.2827) applied to the SAME 125 lights through the SAME
  chain — `M_i` cancels identically, so the lever is star POSITIONS (1603 px
  against the absolute measurement's 29.1 px median) and the sensor-fixed
  atmosphere cancels in the subtraction. **Delivered: −22.477 ± 0.077% (r=10,
  914 stars, Siril `psf`) and −22.450 ± 0.082% (r=16), against the flats' OWN
  ratio field cropped to the delivered canvas at −0.2383/−0.2010 — 98.9% and
  100.6%, tracking point-by-point along 9 midline boxes to ≤0.008; a planted
  ramp control recovers at 97.7%, so the corrected transfer is 101.2%: no
  measurable attenuation.** The floor is EXACTLY ZERO on both instruments and
  all three channels — an identity rebuild is bit-identical, and a uniform
  1.05 card (74.10% of pixels changed) moves every dipole by exactly 0.0000,
  which also measured why: **Siril `calibrate` normalizes the flat by its own
  LEVEL, so only its SHAPE can reach the product.** The shipped normalization
  does not swallow it (0.3% on the object); the same pair moves the BACKGROUND
  dipole +48.6% as a pedestal artefact, so **take the pixel field on `-nonorm`
  arms only**. SCOPE: this is the DIFFERENCE of two imprints — the delivered
  sensitivity to a KNOWN dose difference, not the absolute object tilt, which
  needs the flats' COMMON sky content and is still unmeasured. What it
  establishes is the TRANSFER FUNCTION: a corrective that changes a flat's
  shape by X changes the delivered object by X. Instruments:
  `scripts/qa/flat_differential.py` (+arms/report); numbers:
  `datasets/aug09/flatdiff_prediction.json` (committed before the arms),
  `datasets/aug09/set-05/flatdiff_work/flat_differential.json`.

- **DEAD END — MEASURING THE OBJECT TILT ABSOLUTELY BY DIFFERENTIAL STAR
  PHOTOMETRY ACROSS THE DRIFT. Two independent blockers, either one fatal —
  and the `3.11% at 241 sigma` figure this repo long quoted for the defect is
  UNVERIFIED: no tracked record, and this measurement does not reproduce it.**
  The design is the survey lineage's photometric self-calibration / star flat
  (SDSS ubercal, Padmanabhan et al. 2008; PS1, Schlafly et al. 2012; SNLS/DES
  star flats, Regnault et al. 2009) with the dither supplied free by not
  tracking. Instrument, controls and 12-set corpus: `scripts/qa/object_tilt.py`,
  `datasets/aug09/corpus_object_tilt.json`.
  **BLOCKER 1 — GEOMETRIC: a pure translation carries NO information about the
  linear mode.** Write `m_ij = M_i + z_j + a·u_ij`; under a translation the
  term splits into pieces the per-star and per-block nuisances absorb EXACTLY —
  `a` is formally unidentifiable at any drift size. The surveys break this
  degeneracy with camera ROTATION; here rotation is only what an untracked
  camera gets free (0.69–3.76°/set), leaving a median effective lever of
  **29.1 px against a 5769 px frame — 0.5%, a ~200× extrapolation**.
  `object_tilt.py --selftest` executes it: on a pure-translation panel a
  planted +0.100 mag comes back **−0.046 ± 0.0001** and the lever collapses to
  0.00 px while the sigma does NOT — **read the lever, never the sigma**
  (`numpy.linalg.pinv` reports variance zero along a null direction, so a
  degenerate fit returns confidently wrong rather than loudly unidentified).
  **The lineage names three levers and the route is still dead** (DOCTRINE —
  kept so the next reader does not hunt for "the lever the surveys used"):
  ROTATION is present and insufficient (above); an EXTERNAL ANCHOR kills
  blocker 1 ONLY; AIRMASS VARIATION *collides* with blocker 2 — the
  sensor-fixed atmosphere IS an airmass-shaped term, so varying airmass moves
  confound and signal together; CONNECTING GEOMETRY is unspent but blocker 2
  is untouched by it.
  **BLOCKER 2 — PHYSICAL, and it survives any fix to blocker 1: for a FIXED
  camera the atmosphere is sensor-fixed too.** Every sensor position maps to a
  fixed alt/az, so extinction and skyglow across this 27° field are
  sensor-fixed exactly like the flat's residual — nearly the same airmass
  shape — and the fit sees their SUM. A real flat is the anchor and IS the fix.
  The recorded blocker *"a catalogue is structurally impossible (trailed stars
  at 17″/px)"* is REFUTED — astrometry.net's own index tag-along matched 37
  Tycho-2 stars on exactly such a raw (4/4 cells of a 2×2 at order-1 occupancy;
  order 2 fails outright; x-span 53% of the width) — so the honest word is
  SPARSE and order-1-only, not impossible; the deep catalogue cone route is
  blocked on TOOLING (headless `conesearch` aborts; TAPVizieR timed out —
  `TOOLS.md`). **And the route stays dead either way: known magnitudes fix
  `M_i`, killing blocker 1 only — the fit then measures flat error PLUS
  extinction and skyglow, still a sum, still airmass-shaped.** The
  time-varying half is measured: within-set gradient drift 0.040–0.425 mag
  (median 0.149), monotone in block order in 10 of 12 sets; every set's leak
  capacity (0.74–13.45 mag) exceeds its own shared gradient.
  **THE CONTROLS SAY THE INSTRUMENT IS NOT AT FAULT AND ALSO THAT IT IS
  UNUSABLE.** A Siril `imul` ramp card of known edge ratio recovers at 1.24×
  overall (0.95× on the best-levered pair; recovery tracks rotation
  0.14×–5.2×); a uniform card moves nothing. **The NULL control is the
  sharpest number: interleaved halves of one set — predicted tilt EXACTLY
  ZERO — measure +49.08 ± 4.97%, an 11.8σ reading of a zero**; ten of 12
  corpus sets read above that floor. Discrimination against the floor is
  **0.20×**. The internal falsification: one sensor-fixed field must give ONE
  answer from every block pair; median within-set pair spread is **529
  percentage points**. Record: `datasets/aug09/set-01/tilt_work/
  object_tilt_null.json`; reproducer: `scripts/qa/object_tilt_null.sh`.
  **THE PRE-REGISTERED CORPUS PREDICTION FAILED 4 OF 5**
  (`datasets/aug09/tilt_corpus_prediction.json`, committed first): if the tilt
  were the flat's baked-in gradient, `g(right)/g(left)` would equal the flat's
  own L/R; every set exceeds its flat's dose 1.4×–86× and the built-in null
  set measures +223 ± 28%. **What that does and does not establish:** the
  READINGS are not the flat's dose — but a reading dominated by degeneracy
  leak plus the sensor-fixed atmosphere exceeds the dose whatever the flat is
  doing, so **the flat attribution is UNTESTED by this measurement, not
  falsified** (Spearman +0.68 is weak evidence FOR a flat contribution,
  confounded by the night's sky state driving both). The bake-in MECHANISM is
  untouched; **better sky-flat construction is NOT retired by this result**,
  and the DIFFERENTIAL form of the question is answered — the transfer-function
  entry above. What stays dead is the ABSOLUTE measurement; what stays
  unmeasured is the flats' COMMON sky content.
  **WHAT NOT TO RE-ATTEMPT.** More blocks (rotation is a property of the set);
  more depth (the blocker is systematic — 2545–3823 stars/set already);
  freeing the per-block gradients (`a` becomes unidentified rather than
  clean); interleaved halves (they share rotation as well as drift — lever
  zero). A higher-order mode of `g` is geometrically well-posed and blocker 2
  applies unchanged. **Tool search, recorded because it had to fail first:**
  Siril `seqpsf -wcs=` converts the sky coordinate ONCE and measures that
  pixel area in every image (measured: m = −2.104 reference vs +3.55/+5.05/
  +3.63 elsewhere; `-followstar` does not repair it); `light_curve` is
  differential, not position-dependent throughput; SCAMP 2.10.0 IS installed
  (built from Debian source) and its source has no position-dependent
  photometric solution, so it reopens nothing; `source-extractor` 2.28.2 is a
  viable per-image photometer, not adopted — Siril `psf` measures the same
  natively, and neither closes the actual gap, the cross-image SOLUTION.

- **DEAD END — `--desky`: running `seqsubsky` on the sky flat's RAW source
  frames. Shipped, then reverted: a 31× regression in background flatness.**
  MEASURED, july31/set-01, 500 frames, one knob (Siril `stat` medians, box 400
  / margin 200):

  | arm | corner spread | edge dipole-X |
  |---|---|---|
  | `--desky` ON (as shipped) | **12.4%** | +0.148 |
  | `--desky` OFF (prior pipeline) | **0.4%** | +0.004 |

  All four july31 sets land 0.4–1.0% with it off.
  **MECHANISM — a domain error, not a tuning error.** `seqsubsky` is a
  background-extraction operator defined on a FLAT-FIELDED image; run on raw
  frames the field is `sky × V`, not `sky`, and subtracting a fitted additive
  plane overshoots where V curves hardest — the edge — driving the local
  left-right asymmetry through zero: the raw light measures **+0.426** there,
  the `--desky` flat **−0.550** (sign INVERTED, every session tested; master
  dark +0.000), while the pre-`--desky` flat measured **+0.365** — same sign
  as the light, i.e. correcting it. Dividing by the de-skied flat roughly
  DOUBLES the error.
  **Degree 2 is not the fix either, on PARITY grounds:** vignetting is EVEN
  radial; degree 1 is odd-plus-constant and cannot touch it; degree 2's even
  terms are the same functional form as vignetting, so `subsky` cannot
  separate them — measured, the flat's corner/centre went 0.513–0.563 to
  **0.937–1.006**, the vignetting profile erased entirely. No degree of
  `subsky` on un-flat-fielded frames is safe.
  **WHY NO GUARD CAUGHT IT — read before adding a validation suite.** The
  shipping commit's own validation READ THE REGRESSION'S SIGNATURE AS A WIN: a
  partial sign inversion makes a whole-frame odd-plane fit cancel, so "odd
  plane −59% and −69%" was the defect reporting itself as an improvement; and
  every guard then in the tree verified WIRING, not output. The product-level
  gap is since closed — `baseline_guard.py` shipped and runs last in the
  chain, 13 seeded baselines tracked.
  **THE REVERT REMOVED TWO COUPLED HALVES — ONLY THE FLAT-SIDE ONE IS THIS
  DEAD END.** (2), per-frame `subsky 1 -nodither` on the CALIBRATED lights —
  the operator's correct domain, Siril's own per-frame doctrine — was removed
  only by the flag coupling and is restored UNCOUPLED as `--subsky-lights`
  (`run_undistort_pipeline.sh`, default OFF); the combine-corner audit
  measured the cost of losing it (~+1% at the framing=max full-coverage
  corners, ≤0.2% in the min-framed control). Do not re-couple the halves, and
  do not cite this entry against the lights-side step.
  Numbers: `datasets/july31/set-01/qa_work/desky_regression.json`. The
  `sky × V` mechanism itself remains REAL and UNCORRECTED; its magnitude is
  unmeasured (the dead end above is the sole home of that caveat).

- **DEAD END — THE DOMAIN-CORRECTED ITERATIVE SKY FLAT (calibrate the flat's
  own source frames WITH `F0`, run `seqsubsky` in that flat-fielded domain,
  restore each frame's sky level, multiply back by `F0`, restack). It is a
  NO-OP: the iteration RECONSTRUCTS WHICHEVER FLAT IT IS HANDED.** It does
  repair `--desky`'s domain error — and still cannot work, for a structural
  reason no parameter reaches. **MECHANISM, exact:** dividing by `F0` is what
  removes the gradient from the sky, so in the flat-fielded domain the sky is
  already flat, the degree-1 plane is a CONSTANT, and `imul F0` restores
  precisely what the division took out; the five steps compose to
  `F1 = k·F0` (the correction term is zero twice over), and a second pass
  cannot help — the fixed point is reached on the first.
  **MEASURED, with positive controls that make the null a measurement:** on a
  synthetic fixture of known truth the scheme removes **1.7%** of the defect
  while the same code handed the TRUE V removes **81.7%**; on real data it
  removes 1.2%, and handed a DIFFERENT set's flat it returns THAT flat's value
  (closing 93.4% of the distance) — **the output is a function of the flat
  handed in, not of the frames' own sky dose** (discrimination 62×).
  Downstream, `F0`-vs-`F1` calibrated lights differ <0.1 ADU on a 49 ADU sky
  against 0.2 ADU for a deliberately-broken guard arm. The `sky × V` defect is
  untouched; `--subsky-lights` is a different step in a different place and
  this entry must not be cited against it. Numbers:
  `datasets/aug09/experiments.jsonl`.

- **PER-FRAME DEGREE-1 SUBSKY ON CALIBRATED LIGHTS DOES NOT REMOVE THE
  COMBINE'S FULL-COVERAGE-CORNER TERM — the term is not additive-planar member
  drift; do not re-attempt additive/global background matching as the corner
  fix.** MEASURED (one knob, aug06 3-set framing=max union, members rebuilt
  with `--subsky-lights`): the stage ran (union sky 107.5 → 40.4 ADU, MAD
  unchanged), yet the combine-specific increment held — c00 1.35→0.55 at the
  corner but 0.98→0.94 at 300 px; c11 0.99→1.37 — and the like-encoded judge
  surfaces are corner-EQUIVALENT. Two consequences: (1) equal ADU structure at
  equal MAD renders equally whatever the sky level — the autostretch
  re-anchors, so lowering the sky buys no corner visibility; (2) surviving
  ADDITIVE matching discriminates the driver as the MULTIPLICATIVE
  member-corner class (the open `sky × V` tilt / vignetting residual at member
  sensor corners), unreachable by ANY background subtraction. The fix search
  stays INSIDE the flatless route: the shipped-product lever is GEOMETRY
  (which member zones the compose ships), the calibration-side lever is better
  sky-flat construction; a spatially-varying matching mechanism is a toolkit
  gap (a full per-member BGE is class-blocked on MW-filled fields — the
  GraXpert-Division entry, `background-extraction.md`). SECONDARY, same run:
  degree-1 preserved the real local structure and the noise — the render-stage
  background question is untouched by this kill.

- **A SKY FLAT'S LOW-ORDER TERM CHANGES MATERIALLY WITHIN ONE 25-MINUTE
  BURST — so a set-mean flat is the wrong flat for the ENDS of the burst — but
  the change is NOT driven by elapsed time; the time-dose hypothesis is
  DEAD.** Instrument: a ratio of two flats built from the SAME set (cancels
  vignetting exactly; Siril `stat` medians only). **The floor:** the same set
  split INTERLEAVED spans the whole burst in both halves, so any time-evolving
  term cancels — corner spread **0.035%/0.046%** (two sets). **The effect:**
  contiguous first-half/second-half spread **3.481%** (1497 s burst) and
  **4.177%** (777 s) — **100.0× and 90.6× the floor**; dividing a burst's
  first frames by a set-mean flat leaves an error of order half that, ~1.7%,
  opposite-signed at the other end. **WHAT IS KILLED: "the gradient evolves
  with time."** The pre-registered falsifier fired: the SHORTER burst
  produced MORE half-to-half change (1.200× measured against 0.52× predicted).
  Do not re-attempt burst duration as the explanatory variable, and do not
  size a flat-window policy from elapsed time. **Second discriminator: it is
  the WRONG AXIS to be the stack's residual** — the within-set term is
  predominantly TOP-BOTTOM (y/x slope excess 11.6×) while the sensor-fixed
  calibration residual the stack carries is LEFT-RIGHT. Numbers:
  `flat_window_within_set_set03` / `flat_window_dose_set04` in
  `git show c7db472:datasets/july31/experiments.jsonl` — pre-reset records,
  deliberately NOT re-imported into the live ledger; anything citing them
  carries them as INHERITED.

- **NARROWING THE FLAT WINDOW (one flat per 100-frame GROUP instead of one per
  500-frame set) DOES NOT IMPROVE THE PER-SET PRODUCT, AND THE "a flat
  calibrates ONLY the frames it was built from" RULE IS NOT GROUNDS FOR IT.**
  Built and measured on july31/set-03, one knob, registration pinned at both
  levels, all four controls run. **Why the doctrinal argument does not
  transfer:** the rule fires when a flat averages frames that saw DIFFERENT
  skies — it describes a blend NO frame saw. Under ONE continuous pointing the
  set flat IS the mean of the sky its own frames saw, and the groups deviate
  symmetrically about that mean — so BOTH arms imprint a sky, NEITHER is less
  contaminated, and the composed difference is zero BY CONSTRUCTION (the mean
  of the five per-group departures is 0.8% of a typical departure).
  **Measured at the composed product: +0.055% ± 0.083%, 0.7σ —
  indistinguishable from zero** (1217 stars; cancellation 75–94%, predicted
  before it was measured). **At MEMBER level the correction is real, large,
  and a TRADE:** it reaches the member at 1:1 (planted transfer 1.007/1.077),
  BUYS member backgrounds 28–40× more consistent (the self-fulfilling
  direction this registry already warns about), and COSTS 3.271%/4.335% of
  member-to-member OBJECT-imprint disagreement where the per-set flat has
  EXACTLY ZERO by construction. No instrument here can say which side is
  closer to truth — the absolute residual is the dead end above — so this is a
  trade the DATA CANNOT SETTLE. **Not killed:** the input error is real
  (20–62× its own build floor), the group flats cost nothing in baked-in
  structure (zero findstar specks on every one), and the member is the
  cross-night COMBINE unit — the combine-level A/B is the open question:
  BACKLOG:`per-group-flat-at-the-combine`. Numbers:
  `datasets/july31/experiments.jsonl` (`pergroup_flat_window_july31_set03`);
  pre-registration `datasets/july31/pergroup_flat_prediction.json`.

- **A FOUR-CORNER BOX METRIC IS NOT A GRADIENT MEASURE ON A STRUCTURED
  FIELD.** Corner-vs-corner spread is the repo's background-flatness number;
  on a Milky-Way field it measures **which bit of sky landed in four boxes**,
  because real nebulosity at that scale is the same size as the calibration
  residual under test. MEASURED on the matched pair july31 set-02 vs set-03
  (500 frames each, canvases within 10 px): corner spreads **0.49% vs
  1.09%**, a factor of two. 63-box background maps decompose it into **(1) a
  smooth SENSOR-FIXED left-right ramp**, slope +0.160 vs +0.171 %/1000 px —
  two independent builds agreeing to 7%: the calibration residual — and
  **(2) a patchy term (sd 0.43–0.52%) that correlates better in SKY
  coordinates than sensor coordinates: real sky structure, SIGNAL.** The
  discriminator is the re-aim (it decouples the frames; without one the two
  are degenerate) — and the corners of different sets do not even see the same
  sky: three of four corner boxes map outside the other set's canvas. **Use
  the ramp slope fitted over a grid instead** — reproducible to 7%, immune to
  which sky lands in a box, and the term a background-extraction stage
  actually targets. Changing an acceptance measure needs user ratification, so
  this is recorded as the CANDIDATE, not as a swap. Numbers:
  `background_residual_decomposition_set02_vs_set03` at
  `git show c7db472:datasets/july31/experiments.jsonl` (swept in the july31
  raws-only reset; carried as INHERITED).

- **NEVER store a calibration master at 16-bit integer.** A master
  dark/bias/flat is a many-frame MEAN, so its precision is far finer than one
  integer step; rounding to 16 bits stores a SENSOR-FIXED quantization pattern
  subtracted (or divided) identically into every light — the input to walking
  noise, which no rejection or cosmetic correction removes. MEASURED on a
  200-frame master dark: the 16-vs-32-bit difference is exactly uniform
  ±0.5 ADU (σ 0.2889 vs theory 0.2887), inflating the master's fixed-pattern
  residual 0.4213 → 0.5109 ADU, **+21%**; per-pixel RANDOM, not low-order, so
  it cannot cause — or be cured by — any gradient or colour-cast symptom.
  Enforced by `scripts/stack/check_bitdepth.sh`; a rig that genuinely cannot
  afford 32-bit is a new adaptation needing its own removal condition.
