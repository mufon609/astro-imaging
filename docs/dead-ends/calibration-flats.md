# Calibration — synthetic sky flats, darks, masters

Phase-1 split of `docs/dead-ends.md` (organize-only; the original file stays
the live registry until the merge is decided). Content below the marker is
VERBATIM from the original, so in-text "above"/"below"/section references may
point at entries now homed in a sibling file — `README.md` in this directory
carries the index, the assignment rule, and the block manifest that resolves
them. Do not edit below the marker while the refactor is in phase 1; the split
is re-derivable from the manifest and verified byte-identical by `split.py`.

<!-- == verbatim content from docs/dead-ends.md below this marker == -->
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
  is UNRESOLVED STARLIGHT (terminology entry above), ~81% of the catalogued
  starlight in this field; naming it correctly matters because the two imply
  opposite handling (diffuse emission would be protected by smoothing,
  starlight is protected by keeping stars resolvable). The only fix is manual
  clone-stamping (GUI, non-reproducible). So a sky flat is safe for this class
  ONLY when faint structure is a small part of the frame; validate before use
  (the builder's own gates: `scripts/stack/build_sky_flat.sh`; routes: `TOOLS.md` Tier 1).
- **A SKY FLAT BAKES IN ANY SKY GRADIENT THAT IS FIXED IN THE ALT-AZ FRAME — the
  drift cannot reject it, because the CAMERA is fixed in alt-az too.** The
  method's stated enabling condition ("the sky drifts across the sensor, so the
  moving sky rejects out") is true of STARS and of sky structure fixed on the
  CELESTIAL sphere. It is FALSE for brightness structure fixed relative to the
  HORIZON — moonlight, and the airmass/horizon gradient — which sits still on the
  sensor for the whole set and integrates straight into the flat.
  MEASURED, two sessions, by isolating each flat's ODD component about centre
  (which cancels the even/radial vignetting) and fitting a plane: the odd plane
  runs **4.8-19.4%** of centre level on a moonless night and **16.8-22.6%** on a
  98%-moonlit one. It is NOT optical decentering: the component normal to the
  rotation flips SIGN between sessions (-4.4% vs +16.8%) on the same lens, focal
  and aperture, while the in-plane component walks monotonically through each
  session as the sky rotates against the sensor. On the moonlit night the odd
  plane's DIRECTION tracks the moon's bearing in SENSOR coordinates to 23 deg
  scatter, where a random relation scatters ~104 deg.
  **Why it is a defect and not free background extraction:** a sky gradient is
  ADDITIVE and a flat DIVIDES. Lights are (sky+object) x vignetting; the
  contaminated flat is vignetting x (1+g); dividing yields (sky+object)/(1+g) —
  the sky's own gradient does come out, but the OBJECT is left modulated by a
  5-23% multiplicative tilt it never had. Real nebulosity is photometrically
  tilted across the frame.
  **It also makes the usual flatness check self-fulfilling**: corner-vs-centre
  reads flat on the FINAL stack precisely BECAUSE the flat absorbed the gradient
  and divided it out — so a good flatness number is not evidence the calibration
  is clean. Judge it on the FLAT's odd component, not the stack's corners.
  **SCOPE CORRECTION — the odd-plane percentages above are a MIXTURE, not a sky
  measurement.** They come from a WHOLE-FRAME plane fit, which cannot separate
  the sky term from a repeatable instrumental one. The MECHANISM above (a
  horizon-fixed gradient cannot drift out, and a flat that absorbs it tilts the
  object) stands on its own physics and on the L/R decomposition below. **It is
  NOT supported by the "3916-star differential photometry at 241 sigma" this
  paragraph used to cite: that measurement has no tracked record, and the
  rebuilt catalogue-free version of it is a registered DEAD END below — the
  linear mode is degenerate under translational drift, and the atmosphere is
  sensor-fixed for a fixed camera, so no such fit can size this defect.** Only
  the magnitudes are overstated as sky.
  **EVIDENCE REPLACED — the cross-session pair this scope correction originally
  cited (-0.44 july14, -0.55 july31, read as "same sign across 17 days, so most
  of the odd plane is instrumental") was measured on `--desky` FLATS, i.e. on the
  operator the next entry records as a 31x regression whose defining signature is
  a SIGN INVERSION of exactly this term.** Two negatives agreeing is what the
  regression produces, so that pair could not support the conclusion drawn from
  it. Re-measured on a flat built by the shipped (non-de-skied) builder —
  july31/set-01, 507 frames, Siril `stat` corner medians, `edge_dipole_x` =
  `((TR+BR)-(TL+BL))/2` over the four-corner mean (`baseline_guard.py`):
  **+0.4312 at box 42 / margin 2 and +0.4360 at box 80 / margin 2** (the two
  geometries agree to 1.1%, so the registry's 42 px figures and
  `baseline_guard`'s 80 px convention ARE comparable — a box-size difference is
  not a reason to withhold a comparison, a box-vs-EDGE difference is). That is
  the SAME SIGN as the raw dark-subtracted light (+0.426) and as the pre-`--desky`
  flat (+0.365), and it is 3.6x the same flat's top-bottom dipole (+0.1211).
  **That ratio is the load-bearing number, and it needs no threshold**: vignetting
  is an EVEN RADIAL function and contributes equally to x and y, so an excess in x
  is non-radial BY CONSTRUCTION and cannot be vignetting. july14's -0.44 is NOT
  re-measured (that session is staged raws-only and its records are wiped) and
  should be treated as `--desky`-era until it is. `build_sky_flat.sh` now measures
  both dipoles at the edge geometry and records them in the flat's own qa record —
  reported, never gated, because the `sky x V` defect is open and unfixed.
  **What must NOT be inferred from this entry: that removing the sky from the
  flat's SOURCE FRAMES is the fix.** That was tried (`--desky`, 2026-07-29) and
  was a 31x regression — see the next entry. No corrective is currently shipped;
  the object tilt is a known, open defect.
  **THE ODD COMPONENT IS NOW DECOMPOSED, AND THE OBVIOUS AXIS SPLIT IS WRONG.**
  Instrument (`scripts/qa/flat_odd_component.py` — the script
  `BACKLOG:calibration-evidence` recorded as MISSING): Siril `fdiv` ratios of
  flats built by the same builder from the same night/lens/focal/aperture, which
  cancels vignetting and the instrumental base EXACTLY with no model and no fit,
  plus Siril `stat` regional medians. NEVER `idiv`; two scalars agreeing after
  rescale is the no-clip control (measured identical at 0.5 and 0.25).
  *The left-right term is SKY, decisively.* It rises monotonically WITHIN all
  three nights (july31 L/R 0.634 -> 0.789, aug06 0.895 -> 1.005, aug09
  1.073 -> 1.381) — focus is untouched inside a night, so a within-night change
  on fixed optics can only be sky — and its edge dipole sweeps continuously
  across the corpus from **+0.436 (july31/set-01) through zero (aug06/set-03,
  -0.0255) to -0.385 (aug09/set-05)**, which a sensor-fixed term cannot do on one
  body, lens and focal. Within aug09 the dose composes multiplicatively to 0.08%
  (four consecutive increments multiply to 1.2944 against a directly measured
  1.2955).
  *But the top-bottom term is NOT demonstrably the instrument, and assuming it is
  would be a design error.* T/B cancels to 1.000 in every aug09 ratio
  (0.984-1.008), which invites exactly that reading. Across the corpus it fails:
  july31 runs **1.139 -> 1.216**, above 1 and drifting +6.7% monotonically
  through that night, while aug06 and aug09 sit BELOW 1 (0.968, 0.946-0.960). So
  T/B flips sides between nights and drifts within one — it carries sky too, and
  **neither axis isolates the instrument.**
  SCOPE, and it is the load-bearing caveat: a ratio cancels what is COMMON, so it
  measures the CHANGE in sky, not the total. A static sky term cancels into the
  constant part. The within-night-constant term therefore stays UNATTRIBUTED
  between optics and static sky, and per-session focus recalibration (standing
  practice) is a live alternative explanation for a per-session-constant term.
  Do not design a corrective that preserves the T-B term on the grounds that it
  is optics — that is not established. Numbers:
  `datasets/aug09/flat_ratio_decomposition.json`,
  `datasets/aug09/corpus_flat_odd_component.json`,
  `datasets/aug09/experiments.jsonl`.
  **AND THE FLAT'S SHAPE DIFFERENCE REACHES THE DELIVERED OBJECT ESSENTIALLY 1:1 —
  MEASURED, so the mechanism above is no longer only an argument.** The
  DIFFERENTIAL that survives both blockers of the dead entry below: two flats of
  the same optical state and different sky dose (aug09 set-01 vs set-05, Δedge
  dipole 0.2827, the corpus maximum WITHIN a night) applied to the SAME 125
  set-05 lights through the SAME chain, one knob. `M_i` cancels identically —
  the same star in the same photons — so nothing per-star is fitted and the lever
  is the spread of star POSITIONS: **1603 px against the absolute measurement's
  29.1 px median**. Identical frames also carry identical extinction and skyglow
  at every sensor position, so blocker 2's term cancels in the subtraction.
  **Delivered: −22.477 ± 0.077% (r = 10 px, 914 stars, Siril `psf` against its own
  local annulus) and −22.450 ± 0.082% (r = 16), against a pixel-ratio field
  (Siril `fdiv` + `stat`) of edge dipole_x −0.2356 green.** The apples-to-apples
  form is not a model: the flats' OWN ratio field cropped to the delivered canvas
  measures −0.2383 (edge) and −0.2010 (corner) against the delivered −0.2356 and
  −0.2021 — **98.9% and 100.6%**, tracking point-by-point along 9 midline boxes to
  ≤0.008. A planted ramp of known dipole +0.1583 over that same window recovers at
  97.7%, so correcting the real number by the control's own systematic gives
  **101.2%: no measurable attenuation.**
  **The floor is EXACTLY ZERO**, on both instruments and all three channels — an
  identity rebuild is bit-identical, and the non-vacuous version (a uniform 1.05
  card, which changes 74.10% of the pixels) still moves every dipole by exactly
  0.0000. That control also measured why: **Siril `calibrate` normalizes the flat
  by its own level, so a flat's absolute LEVEL cannot reach the product — only
  its SHAPE can.** Discrimination is therefore unbounded (planted movement 0.1547
  against 0.0000), where the object-tilt instrument managed 0.20x.
  **The shipped normalization does NOT swallow it: 0.3%** on the object
  (−22.477% at `-nonorm` vs −22.550% at `-norm=addscale -output_norm`). The same
  pair moves the BACKGROUND dipole +48.6% and splits the channels — a pedestal
  artefact, not imprint, since psf's local annulus removes an additive term and
  regional medians cannot (measured: `An/A` is a uniform 2.02x while `Bn/B` runs
  1.859 left to 1.667 right). **Take the pixel field on `-nonorm` arms only.**
  SCOPE — read this before citing the 22.5%: it is the DIFFERENCE of two imprints,
  so it gives the delivered sensitivity to a KNOWN dose difference and NOT the
  absolute object tilt, which needs the flats' COMMON sky content and is still
  unmeasured. It does not resurrect the 3.11% / 241 sigma figure (UNVERIFIED), and
  the T/B attribution caveat above is untouched. What it does establish is the
  TRANSFER FUNCTION: any future measurement of a flat's absolute sky content
  converts to an object tilt essentially 1:1, and a corrective that changes a
  flat's shape by X changes the delivered object by X. Instrument:
  `scripts/qa/flat_differential.py` (+ `flat_differential_arms.sh`,
  `flat_differential_report.py`); numbers:
  `datasets/aug09/flatdiff_prediction.json` (committed before the arms) and
  `datasets/aug09/set-05/flatdiff_work/flat_differential.json`.

- **DEAD END — MEASURING THE OBJECT TILT BY DIFFERENTIAL STAR PHOTOGRAPHY ACROSS
  THE DRIFT. Two independent blockers, either one fatal; and the `3.11% at 241
  sigma` figure this repo has quoted for the defect is UNVERIFIED — it has no
  tracked record and this measurement does not reproduce it.** The design is the
  survey lineage's photometric self-calibration / star flat (SDSS ubercal,
  Padmanabhan et al. 2008; PS1 forward global calibration, Schlafly et al. 2012;
  SNLS/DES star flats, Regnault et al. 2009) with the dither supplied free by not
  tracking: measure the same stars in consecutive time blocks and fit measured
  flux against sensor position, since correct calibration makes a star's flux
  independent of where it landed. Instrument, controls and 12-set corpus:
  `scripts/qa/object_tilt.py`, `datasets/aug09/corpus_object_tilt.json`.

  **BLOCKER 1 — GEOMETRIC: a pure translation carries NO information about the
  linear mode, so the 503-1220 px of drift is not the lever.** Write the model
  `m_ij = M_i + z_j + a*u_ij`. Under a translation `u_ij = u_i + c_j`, the term
  splits as `a*u_i` + `a*c_j`, which the per-star and per-block nuisances absorb
  EXACTLY — `a` is formally unidentifiable at any drift size. This is the known
  low-order degeneracy of self-calibration under translational dithers, and the
  surveys break it with camera ROTATION.
  **CORRECTED — "with camera ROTATION" IS SINGULAR AND THE LINEAGE NAMES THREE
  LEVERS. Read this before proposing a new one, because the other two are already
  spent here and the route is still dead.** (DOCTRINE — the ORACLE's read of the
  SDSS ubercal lineage, which also names the degeneracy and its firing condition;
  not measured here. `Bernstein` occurred in no tracked `.md` BEFORE this entry,
  which is why this is its first home; the string now resolves to this file and to
  `datasets/aug06/experiments.jsonl`, so a bare search returns the entries asserting it
  and cannot be read as absence. The ubercal LEVERS are a CONTENT claim rather than
  a string one, and that search does not cover them.) The three are
  **camera ROTATION**, **AIRMASS
  VARIATION**, and an **EXTERNAL ANCHOR**, plus **CONNECTING GEOMETRY** where
  overlapping pointings tie separate fields together. Their status here:
  - **ROTATION** — present and measured, 0.69-3.76 deg per set, and it is what
    gives the 29.1 px median lever below. Not enough by itself.
  - **EXTERNAL ANCHOR** — already tried and already answered in this entry: a
    catalogue kills BLOCKER 1 ONLY, and BLOCKER 2 does not care where the
    reference magnitudes came from.
  - **AIRMASS VARIATION** — and this one COLLIDES with blocker 2 rather than
    helping, which is why it must not be reached for: the sensor-fixed atmosphere
    IS an airmass-shaped term, so varying airmass moves the confound and the
    signal together.
  - **CONNECTING GEOMETRY** — the only one this corpus has not spent. Re-aims
    between sets do connect different pointings. It is NOT proposed: blocker 2 is
    untouched by it, and this entry's controls put the instrument's floor at the
    size of the measurement.
  **So the correction adds no route. It exists so the next reader does not go
  hunting for "the lever the surveys used" believing there was one.**
  Here the rotation is what an untracked
  camera gets free: **0.69-3.76 deg per set**, which leaves a median effective
  lever of **29.1 px against a 5769 px frame — 0.5%, a ~200x extrapolation**
  (range 9.2-34.3 px). `object_tilt.py --selftest` executes this: on a
  pure-translation panel a planted +0.100 mag comes back as **-0.046 +- 0.0001**,
  and the lever collapses to 0.00 px while the sigma does NOT. **Read the lever,
  never the sigma** — `numpy.linalg.pinv` reports variance ZERO along a null
  direction, so a degenerate fit returns confidently wrong rather than loudly
  unidentified.

  **BLOCKER 2 — PHYSICAL, and it survives any improvement to blocker 1: for a
  FIXED camera the atmosphere is sensor-fixed too.** Every sensor position maps
  to a fixed altitude and azimuth, so extinction and the skyglow gradient across
  this 27-degree field are sensor-fixed exactly like the flat's residual — and
  both are functions of AIRMASS, i.e. nearly the same spatial shape. The fit sees
  their SUM and cannot apportion it without an external anchor. A real flat is one
  such anchor and IS the fix. **The other anchor was recorded here as "a catalogue
  is structurally impossible (trailed stars at 17"/px)" — THAT IS REFUTED, and the
  two halves of the correction must be read together or the next reader reopens a
  route that is still dead.** MEASURED: astrometry.net's own index tag-along
  (`solve-field --tag-all`) matched **37 Tycho-2 stars on exactly such a raw** —
  trailed, at that plate scale — so the stated mechanism fails on its own terms,
  and that route issues no catalogue query at all. The sample is thin but real
  against the field's own yardstick, which states the requirement as a per-cell
  OCCUPANCY rather than a count (Pan-STARRS, Magnier et al. 2016 Table 5: 4 stars
  per cell at order 1): these 37 occupy **4/4 cells of a 2×2 grid, minimum 5 per
  cell** — clearing order 1 — and **8/9 cells of a 3×3, minimum 1** against a
  requirement of 6, so order 2 fails outright. They also span only **x 1162–4384
  of 6064 (53% of the width)**, so a linear sensor-fixed term fitted on them
  EXTRAPOLATES to the very edges it exists to measure. The honest word is
  **SPARSE and order-1-only, not impossible.** What IS blocked is the DEEP
  catalogue cone route, and on TOOLING rather than on trailing — Siril's
  `conesearch` aborts unconditionally when run headless, and separately timed out
  on a 20.6° cone against TAPVizieR (`TOOLS.md`). **AND THE ROUTE STAYS DEAD,
  because a catalogue kills BLOCKER 1 ONLY.** Known catalogue magnitudes fix the
  per-star nuisance `M_i`, so the translational degeneracy does go — but the fit
  then measures `ZP + f(sensor position)` where `f` is the flat error PLUS
  extinction and skyglow, still a sum, still both airmass-shaped. Blocker 2 does
  not care where the reference magnitudes came from.
  **The time-varying half is measured, not
  argued:** letting every block carry its own gradient gives a within-set drift of
  **0.040-0.425 mag across the frame (median 0.149), MONOTONE in block order in 10
  of 12 sets**. A gradient drift `delta` enters a shared-gradient fit at about
  `delta/theta`, so every set's leak capacity (**0.74-13.45 mag**) exceeds its own
  measured shared gradient.

  **THE INSTRUMENT IS NOT AT FAULT — the controls say so, and they also say it is
  UNUSABLE.** A Siril `imul` ramp card of known edge ratio 1.2222 is recovered at
  **1.24x** overall and **0.95x** on the best-levered block pair (rotation
  2.37 deg), while a UNIFORM card moves every number by **exactly 0.00**. Recovery
  tracks the lever: the same set's pairs recover 0.14x-5.2x as their rotation runs
  0.66-2.37 deg. **DISCRIMINATION AGAINST THE FLOOR IS 0.20x** — the planted ramp
  moves the answer 9.85 points against a measured floor of 49.08, i.e. the signal
  is five times SMALLER than what the instrument reports when the truth is zero.
  The iterative-flat NULL met 48-62x on the same standard. Re-running the controls
  reproduced -54.40% / +9.85 points / recovery 1.2408 to every digit.

  **THE NULL CONTROL IS THE SHARPEST NUMBER HERE — THE FLOOR IS 49 PERCENTAGE
  POINTS.** aug09/set-01 was rebuilt as interleaved halves (249 even frames
  against 249 odd, same undistort chain, each solved). The halves span the same
  drift, so every star's flux is the average of the SAME sensor positions in both
  and the predicted tilt is EXACTLY ZERO. Measured **+49.08 ± 4.97% at r = 10 px
  and +50.82 ± 5.65% at r = 16 px**, 3086 stars, residual 0.0085 mag, chi2/dof
  3.74 — an **11.8-sigma reading of a quantity that is zero by construction**, and
  the aperture agreement rules out a PSF-fit artefact. It is not a degenerate
  configuration either: Siril picked a different reference frame for each half, so
  the two canvases sit **2.37 deg and 103 px apart** and the lever is 27.9 px,
  comparable to the live runs. Ten of the 12 corpus sets read above this floor and
  two below it, which is the point — the floor is the same size as the measurement.
  Record: `datasets/aug09/set-01/tilt_work/object_tilt_null.json`; reproducer:
  `scripts/qa/object_tilt_null.sh`.

  **THE INTERNAL FALSIFICATION THAT KILLS THE PER-SET NUMBER.** One sensor-fixed
  field must give ONE answer from every pair of blocks. Median within-set pair
  spread across the corpus: **529 percentage points** (aug09/set-01: +57, -20,
  -65, -80, -88, -93%).

  **THE PRE-REGISTERED CORPUS PREDICTION FAILED 4 OF 5**
  (`datasets/aug09/tilt_corpus_prediction.json`, committed before the corpus ran).
  If the tilt were the flat's baked-in sky gradient, `g(right)/g(left)` would
  equal the flat's own L/R. Measured across 12 sets, three nights: **every set
  exceeds its flat's dose, by 1.4x to 86x (median 8.1x)** — the flat cannot
  produce more tilt than it carries. **aug06/set-03, pre-registered as the
  built-in null (L/R 1.0259, predicted +2.6%), measures +223 +- 28%.** The
  measured range is **-77%..+1605%** against a predicted -35.8%..+47.7%. Spearman
  rho is **+0.68 (p 0.015)** — a real positive ordering, but it cannot be read as
  confirmation while the magnitudes miss by up to 86x, because the flat's L/R
  sweeps as the NIGHT'S SKY STATE sweeps and blocker 2 is driven by the same
  thing.

  **WHAT THE PREDICTION'S FAILURE DOES AND DOES NOT ESTABLISH — read this before
  citing it.** It establishes that the READINGS are not the flat's dose. It does
  NOT establish that the flat is a minor term of the real defect, and this entry
  must not be cited for that. The excess argument ("the flat cannot produce more
  tilt than it carries") treats each reading as an estimate of a physical tilt,
  and the same controls above say it is not one: the floor is +49 points where
  truth is zero, discrimination against that floor is 0.20x, the median
  within-set block-pair spread is 529 points, and the corpus mean reads **+299%**
  with a range to **+1605%** — magnitudes no throughput tilt can have. A reading
  dominated by degeneracy leak plus the sensor-fixed atmosphere exceeds the
  flat's dose whatever the flat is doing, so the comparison has no power to
  apportion. **The flat attribution is therefore UNTESTED by this measurement,
  not falsified** — and rho +0.68 is, if anything, weak evidence FOR a flat
  contribution, confounded exactly as stated above. The MECHANISM in the entry
  above is likewise untouched: a horizon-fixed gradient cannot drift out of a
  median of un-registered lights, and dividing by a flat that absorbed it does
  tilt the object. What is refuted is that this measurement can size it.
  **Consequence for the roadmap: better sky-flat construction is NOT retired by
  this result.** It stays the calibration-side lever inside the flatless route
  (per-group flats remain the untested candidate), because nothing here measured
  it down. **And the differential form of the question IS answerable — it is
  measured, in the entry above.** Two flats of the same optical state and
  different sky dose on the SAME lights kills both blockers structurally (`M_i`
  cancels identically, so the lever goes from a 29.1 px median to 1603 px; the
  sensor-fixed atmosphere cancels in the subtraction), and it returns
  −22.5% delivered for a Δedge-dipole of 0.2851, with a floor of EXACTLY zero.
  What stays dead is the ABSOLUTE measurement, and what stays unmeasured is the
  flats' COMMON sky content — not the transfer from flat shape to object.

  **WHAT NOT TO RE-ATTEMPT.** More blocks (rotation is a property of the set, not
  the block count); more depth (the blocker is systematic, not statistical — 2545
  to 3823 stars per set already); freeing the per-block gradients (a constant
  added to every delta IS the quantity wanted, so `a` becomes unidentified rather
  than clean); interleaved halves (they share their rotation as well as their
  drift, so the lever goes to zero). A HIGHER-ORDER mode of `g` is not degenerate
  under translation and would be well-posed geometrically — but blocker 2 applies
  to it unchanged, so it measures the atmosphere-plus-flat sum too.

  **TOOL SEARCH, recorded because it had to fail first.** Siril `seqpsf -wcs=`
  looks like the answer and is not: it converts the sky coordinate to pixels ONCE
  and measures that same pixel area in every image. MEASURED on one real star
  across aug09/set-01's four blocks: **m = -2.104 in the reference block against
  +3.55 / +5.05 / +3.63** in the others, and `-followstar` does not repair it
  without registration data (+3.55 / +3.87 / +2.86). `light_curve` is
  differential against comparison stars, not position-dependent throughput.
  **SCAMP** — the standards answer for a photometric solution across overlapping
  exposures — has **no apt candidate** on this distro (`apt-cache policy scamp`:
  Installed (none), Candidate (none)) but **IS INSTALLED**, built from Debian
  source: `/home/samsung/.local/bin/scamp`, `SCAMP version 2.10.0 (2020-12-01)`
  (`TOOLS.md`; corrected here at the third site). **An earlier wording read "is NOT
  packaged on this distro", which is true of the binary index and false as the
  route-closing claim it functions as** — the identical shape `TOOLS.md` already
  corrected for PSFEx. **It reopens nothing:** SCAMP 2.10.0's own source has no
  position-dependent photometric solution, and the object-tilt route is dead on two
  structural blockers regardless. `source-extractor` 2.28.2 IS
  installed and runs on these sub-stacks (47,971 objects in 3.1 s, `FLUX_APER` at
  two radii with `BACKPHOTO_TYPE LOCAL` and `ALPHA/DELTA_J2000`) — a viable
  alternative per-image photometer, not adopted because Siril `psf` gives the same
  measurement natively on the 3-layer float cube and on the green layer the rest
  of the chain uses, and because neither closes the actual gap, which is the
  cross-image SOLUTION.

- **DEAD END — `--desky`: running `seqsubsky` on the sky flat's RAW source
  frames. Shipped, then reverted: a 31x regression in background flatness.**
  MEASURED, july31/set-01, 500 frames, one knob, everything else identical
  (Siril `stat`, medians, box 400 / margin 200):

  | arm | corner spread | edge dipole-X |
  |---|---|---|
  | `--desky` ON (as shipped) | **12.4%** | +0.148 |
  | `--desky` OFF (prior pipeline) | **0.4%** | +0.004 |

  All four july31 sets land 0.4-1.0% with it off; 0.4% reproduces the 0.3-0.7%
  the route delivered before it landed.
  **MECHANISM — a domain error, not a tuning error.** `seqsubsky` is a
  BACKGROUND EXTRACTION operator, defined on a FLAT-FIELDED image; the flat
  builder ran it on raw frames that still carry vignetting, so the frame is
  `sky x V`, not `sky`. Fitting an additive plane to that product and
  subtracting it overshoots where V curves hardest — the frame edge — and
  drives the local left-right asymmetry through zero: the raw dark-subtracted
  light measures **+0.426** there and the `--desky` flat **-0.550** — sign
  INVERTED, in every session tested, while the master dark measures +0.000.
  Dividing by that flat roughly DOUBLES the error instead of removing it. The
  pre-`--desky` flat measured **+0.365** — same sign as the light, ~85% of its
  magnitude — i.e. it was correcting the asymmetry.
  **A COROLLARY worth keeping: degree 2 is not the fix either, on PARITY
  grounds.** Vignetting is an EVEN radial function; a degree-1 plane is
  odd-plus-constant and cannot touch an even term by construction. Degree 2 is
  the first degree with even terms and they are the same functional form as
  vignetting, so `subsky` cannot separate them. MEASURED: at degree 2 the
  flat's corner/centre went 0.513-0.563 to **0.937-1.006** — the vignetting
  profile gone entirely, failing the builder's own "corners < centre" gate. No
  degree of `subsky` on un-flat-fielded frames is safe.
  **WHY NO GUARD CAUGHT IT — read this before adding a validation suite.** The
  shipping commit validated with a whole-frame odd-PLANE fit, a
  centre-vs-corner RADIAL ratio, PRNU correlation and mote depth; none can see
  a left-right sign flip localised at the edge (the radial ratio averages all
  four corners, PRNU and motes are high-frequency). Worse, **the cited proof of
  success is what the defect produces** — a partial sign inversion makes a
  whole-frame plane fit cancel, so "odd plane -59% and -69%" is the
  regression's own signature read as a win; the commit also measured a
  degradation (level spread 2.48% -> 3.10%) and shipped it as an accepted trade
  while the real figure was 12.4% vs 0.4%; and `baseline.json` — the
  no-regression harness that compares PRODUCTS — has never been built, so
  nothing downstream checked. Every guard that exists (`check_bitdepth`,
  `check_calibrate`, `check_stack_rejection`) verifies WIRING, not output.
  **STILL OPEN, and do not confuse it with this entry:** a sky flat converges
  to `sky x V`, so calibration leaves the object carrying the sky's spatial
  profile. The defect's MECHANISM is REAL and currently UNCORRECTED; its
  MAGNITUDE is UNMEASURED — the long-quoted "3.11% at 241 sigma" has no tracked
  record and the catalogue-free re-measurement is a dead end (the entry above).
  `--desky` was not a valid fix for it. Numbers:
  `datasets/july31/set-01/qa_work/desky_regression.json`.
  **THE REVERT REMOVED TWO COUPLED HALVES — ONLY THE FLAT-SIDE ONE IS THIS DEAD
  END.** The `--desky` flag gated (1) the flat-side `seqsubsky` on RAW source
  frames — the domain error and the 31x regression above, dead — and (2)
  per-frame `subsky 1 -nodither` on the CALIBRATED, debayered lights: the
  operator's correct domain (flat-fielded data), Siril's own per-frame degree-1
  doctrine for sequence-varying gradients, removed only by the flag coupling
  and never measured on its own. The combine-corner audit measured the cost of
  losing (2): a ~+1% combine-introduced term at the framing=max compose's
  full-coverage corners — where 8-12 member footprint edges converge — absent
  (<=0.2%) from the min-framed control built by the same chain
  (`datasets/aug06/set-03/qa_work/audit_combine_corners_measurements.json`).
  (2) is restored UNCOUPLED as `--subsky-lights` (run_undistort_pipeline.sh;
  default OFF). Do not re-couple the halves, and do not cite this entry
  against the lights-side step.

- **DEAD END — THE DOMAIN-CORRECTED ITERATIVE SKY FLAT (calibrate the flat's own
  source frames WITH `F0`, run `seqsubsky` in that flat-fielded domain, restore
  each frame's sky level, multiply back by `F0`, restack). It is a NO-OP: the
  iteration RECONSTRUCTS WHICHEVER FLAT IT IS HANDED, so handing it `F0` returns
  `F0`.** Proposed as the fix for the `sky x V` object tilt that `--desky` failed
  to fix, and it does genuinely repair `--desky`'s domain error — `seqsubsky`
  runs on flat-fielded data, which is where the operator is defined. It still
  cannot work, for a structural reason no parameter reaches.
  **MECHANISM, exact.** Dividing by `F0` is WHAT REMOVES the gradient from the
  sky — that is what a flat does — so in the flat-fielded domain the sky is
  already flat, the degree-1 plane is a CONSTANT, and `imul F0` restores
  precisely what the division took out. With `P_t` the fitted plane and `m_t` the
  frame's pre-`subsky` median, the five steps compose to
  `F1 = k*F0 - <P_t - m_t>*F0`, and the correction term is zero TWICE OVER:
  `P_t - m_t = 0` because the sky in that domain is flat, and `<P_t - m_t> = 0`
  over the set because `F0` IS the time-average the per-frame deviations are
  measured against. **`F1 = k*F0`.** A second pass cannot help — the fixed point
  is reached on the first.
  **MEASURED, one knob throughout (the round-trip flat), with POSITIVE CONTROLS
  that make the null a measurement rather than a check that cannot fail.**
  *Synthetic fixture, truth known* — frames `(sky x (1+g) + moving stars) x V`,
  `V` even-radial so its L/R is 1.0000 by construction; `F0` bakes the gradient
  in at L/R 1.2378. The scheme returns **1.2338 (1.7% of the defect removed)**;
  the same code with the round-trip flat set to the true `V` returns **1.0436
  (81.7% removed)**. The intermediates show why: in the scheme's arm `seqsubsky`
  moves the frame median by **0.0 ADU** (46.3 -> 46.3) because there is nothing
  to remove, against -0.9 ADU in the control.
  *Real data, live path* (aug09/set-05, 100 frames, control `F0_100` built from
  the SAME frames, L/R 1.3939): the scheme returns **1.3891 (1.2% removed)** and
  `F1/F0` is flat to 0.33% in L/R and 0.04% in T/B. Handed a DIFFERENT set's flat
  instead (set-01, L/R 1.0729) the same code on the same set-05 frames returns
  **1.0940** — set-01's value, closing 93.4% of the distance — and its edge
  dipole comes back at -0.1154 against set-01's -0.1026, not set-05's -0.3920.
  **The output is a function of the flat handed in, not of the frames' own sky
  dose.** Discrimination 62x (L/R moved 0.2999 against 0.0048).
  *Downstream*: the same lights calibrated with `F0` vs `F1` differ by <0.1 ADU
  on a 49 ADU sky (`isub`, both directions), against 0.2 ADU for a
  deliberately-broken guard arm whose own arithmetic checks out (its calibrated
  light reads L/R 1.29919 = exactly 1.3939/1.0729, the two flats' dose ratio).
  **WHAT THIS DOES NOT KILL.** The `sky x V` defect itself is untouched and still
  uncorrected. Per-frame degree-1 `subsky` on the CALIBRATED LIGHTS
  (`--subsky-lights`) is a different step in a different place and this entry
  must not be cited against it. Numbers: `datasets/aug09/experiments.jsonl`.

- **PER-FRAME DEGREE-1 SUBSKY ON CALIBRATED LIGHTS DOES NOT REMOVE THE
  COMBINE'S FULL-COVERAGE-CORNER TERM — the term is not additive-planar
  member drift; do not re-attempt additive/global background matching as the
  corner fix.** MEASURED (`subsky_lights_restoration` ledger arm, one knob,
  aug06 3-set framing=max union, members rebuilt with `--subsky-lights`,
  controls preserved): the stage ran (union sky 107.5 → 40.4 ADU, MAD
  unchanged 2.67 → 2.46), yet the combine-specific increment (union minus its
  own member family at identical sky, ADU) held — c00 1.35→0.55 at the corner
  but 0.98→0.94 at 300 px; c11 0.99→1.37 — and the like-encoded judge
  surfaces are corner-EQUIVALENT (16-bit DN corner-minus-flank: +2823 vs
  +2941 at c00; −1526 vs −1653 at c11). Two mechanism consequences:
  (1) equal ADU structure at equal MAD renders equally whatever the sky
  level — the autostretch re-anchors, so lowering the sky buys no corner
  visibility; (2) surviving ADDITIVE matching discriminates the driver as
  the MULTIPLICATIVE member-corner class (the open `sky × V` object tilt /
  vignetting residual at member sensor corners), unreachable by ANY
  background subtraction. The fix search stays INSIDE the flatless route
  (synthetic flats are the project's point — user-ratified, MEMORY.md):
  the residual class is CONSTANT across all products, so the shipped-product
  lever is GEOMETRY — which member zones the compose ships (min framing, or
  a per-member edge shrink at compose input: the mainstream GMM-shrink
  mechanism) — and the calibration-side lever is better sky-flat
  construction (the within-burst flat term is the measured member-to-member
  differencer within a set; per-group flats are the untested candidate).
  A spatially-varying matching mechanism remains a toolkit gap (no
  free-headless tool; a full per-member BGE is class-blocked on MW-filled
  fields — the GraXpert-Division entry).
  SECONDARY, same run (scope: these regions, one dataset): degree-1
  preserved the real local structure (total c00 excess 3.26 → 3.16 ADU) and
  the noise — the render-stage background question (L1) is untouched by
  this kill and stays open.

- **A SKY FLAT'S LOW-ORDER TERM CHANGES MATERIALLY WITHIN ONE 25-MINUTE BURST —
  so a set-mean flat is the wrong flat for the ENDS of the burst — but the
  change is NOT driven by elapsed time; the time-dose hypothesis is DEAD.**
  Instrument: a ratio of two flats built from the SAME set, same dark, same
  `rej w 3 3`, same `-norm=mul`, same builder — which cancels vignetting
  EXACTLY (same lens/focal/aperture/night), with no model and no fit; Siril
  `stat` medians only, corner spread at box 400 / margin 200 and a 63-box grid
  (200 px boxes, 550 px pitch) for the ramp slope.
  **The floor:** the same set split INTERLEAVED (even frames vs odd) spans the
  whole burst in both halves, so any time-evolving term cancels and only the
  build floor remains — corner spread **0.035%** (set-03, 250+250) and
  **0.046%** (set-04, 130+130), grid range 0.092/0.128%. That is this builder's
  flat-build floor.
  **The effect:** contiguous first-half/second-half corner spread **3.481%**
  (july31 set-03, 750 s between half-midpoints) and **4.177%** (set-04, 390 s)
  — **100.0x and 90.6x the floor**. Dividing the first frames of a burst by a
  flat built from all of them leaves a corner-to-corner error of order half
  that, ~1.7%, with opposite sign at the other end — against the +0.70%
  across-frame calibration residual the 500-frame stack actually carries.
  **WHAT IS KILLED: "the gradient evolves with time."** A dose-response on
  burst duration falsified it on its own pre-registered falsifier: set-04 ran
  777 s against set-03's 1497 s, so a time-driven term predicted 0.52x; it
  measured **1.200x** — the SHORTER burst produced MORE half-to-half change. Do
  not re-attempt burst duration as the explanatory variable, and do not size a
  flat-window policy from elapsed time. What is specific to a set is
  unattributed; a re-aim happens between sets, so duration is not the only
  difference.
  **A second discriminator worth keeping: it is the WRONG AXIS to be the
  stack's residual.** The within-set term is predominantly TOP-BOTTOM (y-slope
  +0.8178 vs x-slope +0.0705 %/1000px on set-03, an 11.6x excess), whereas the
  sensor-fixed calibration residual the stack carries is LEFT-RIGHT
  (+0.171 %/1000px). Two different axes are two different terms; a within-burst
  flat policy is not automatically a fix for the stack's ramp. Numbers:
  `flat_window_within_set_set03` and `flat_window_dose_set04` in
  `git show c7db472:datasets/july31/experiments.jsonl` — the records are NOT in
  the live ledger, because the deliberate july31 raw-frames-only reset removed
  all 93 tracked july31 records and the blackbox re-run re-created only what it
  re-measured. They are not re-imported: a pre-reset measurement must not enter
  a post-reset ledger unmarked. Anything relying on these numbers therefore
  carries them as INHERITED (the standing rule for a measurement not re-made in
  its current context).

- **NARROWING THE FLAT WINDOW (one flat per 100-frame GROUP instead of one per
  500-frame set) DOES NOT IMPROVE THE PER-SET PRODUCT, AND THE "a flat calibrates
  ONLY the frames it was built from" RULE IS NOT GROUNDS FOR IT.** The upstream
  fix the entry above SPECIFIED was built and measured on july31/set-03, one
  knob, registration pinned at BOTH levels, all four controls run.
  **WHY THE DOCTRINAL ARGUMENT DOES NOT TRANSFER — the load-bearing point, and
  NOT because the rule is about optics.** A ratio of two flats from one night,
  lens, focal and aperture cancels vignetting EXACTLY, so what differs between a
  group flat and the set flat IS THE SKY TERM; the optical state (V, dust, focus)
  does not change inside a 25-minute burst. That much is measured — but "so the
  rule is about optical-state matching" is WRONG, and was corrected by audit: the
  rule's OWN justification is a sky divergence (`build_sky_flat.sh`: a mid-set
  re-aim measured L-R corner ratio 1.162 against 1.032 while the top-bottom
  optical term was identical at 1.143 vs 1.142 — "the divergence is sky").
  **The real discriminator is what the flat DESCRIBES.** The rule fires when a
  flat averages frames that saw DIFFERENT skies, so it describes a blend NO frame
  saw and dividing either block by it prints the other block's gradient in. Under
  ONE continuous pointing there is no such blend: the set flat IS the mean of the
  sky its own frames saw, which is exactly what the rule asks for, and the groups
  deviate symmetrically about that mean. So BOTH arms imprint a sky and NEITHER is
  less contaminated — only the UNIFORMITY of the imprint across members changes.
  That is why the composed difference is zero BY CONSTRUCTION rather than by
  luck, and it is the reason a narrower window has nothing left to fix at the
  composed level.
  **THE PER-SET PRODUCT DOES NOT MOVE, AND THAT WAS PREDICTED BEFORE IT WAS
  MEASURED.** The per-set flat IS the groups' average: the mean of the five
  per-group departures is 0.82% (x) and 0.76% (y) of a typical departure, so a
  plain-mean compose cancels them. Delivered, the composed object L/R tilt moves
  **+0.055% ± 0.083%, 0.7σ — indistinguishable from zero** (Siril `psf`, 1217
  stars), and the composed pixel field is 7-25% of the mean member magnitude.
  Cancellation is 75-94% rather than the >99% the sensor-frame arithmetic gives,
  because the compose is a SKY-frame mean of sensor-fixed patterns that drifted
  ~453 px across the set. **Do not read that null as a null for the method** —
  it is arithmetic, and it was recorded before the composed stack existed.
  **AT MEMBER LEVEL THE CORRECTION IS REAL, LARGE, AND A TRADE RATHER THAN A
  GAIN.** It reaches the member at **1:1** (planted-corrected transfer 1.007 in
  x, 1.077 in y), moving each member's object tilt 0.36-2.13% in x (4.3-21.3σ)
  and up to 3.42% in y. It BUYS member backgrounds 28-40x more consistent
  member-to-member — but that is the SELF-FULFILLING direction this registry
  already warns about, so it is the mechanism's size and NOT evidence of a better
  calibration. It COSTS **3.271% (x) / 4.335% (y) of member-to-member OBJECT-
  imprint disagreement, where the shipped per-set flat has EXACTLY ZERO** by
  construction, since one flat serves every member. No instrument here can say
  which side is closer to truth — the absolute residual is the dead end above —
  so this is a trade-off the DATA CANNOT SETTLE and the owner decides.
  **What is NOT killed:** the input error is real and 20-62x its own build floor,
  the group flats cost nothing in baked-in structure (ZERO findstar specks on
  every one, against ONE on the set flat, despite averaging 90.9 px of celestial
  motion against 453.3 px), and the member is the cross-night COMBINE unit — so a
  combine-level A/B is the open question, not a re-run of this one.
  Numbers: `datasets/july31/experiments.jsonl`,
  `pergroup_flat_window_july31_set03`; pre-registration
  `datasets/july31/pergroup_flat_prediction.json`, committed before the first
  flat was built.

- **A FOUR-CORNER BOX METRIC IS NOT A GRADIENT MEASURE ON A STRUCTURED FIELD.**
  Corner-vs-corner spread is the repo's background-flatness number
  (`judge_acceptance.json`'s `linear_corner_spread_pct`, `build_sky_flat.sh`'s
  1.20 corner-asymmetry WARN, `baseline_guard.py`'s edge dipoles); on a
  Milky-Way field it measures **which bit of sky landed in four boxes**,
  because real nebulosity at that scale is the same size as the calibration
  residual it is supposed to detect. MEASURED on the matched pair july31 set-02
  vs set-03 — 500 frames each, 1497 s each, drift 912 vs 906 px, canvases
  within 10 px — whose corner spreads read **0.49% vs 1.09%**, a factor of two.
  63-box background maps (Siril `stat` medians, green, linear `_spcc`, 200 px
  boxes on a 550 px pitch) decompose that into two comparable terms:
  **(1) a smooth left-right ramp that is SENSOR-FIXED**, slope +0.160 vs
  +0.171 %/1000 px — the two independent builds agree to 7% — i.e. ~0.70%
  across the frame: the calibration residual.
  **(2) a patchy term, sd 0.43-0.52%**, which correlates BETTER in SKY
  coordinates (r +0.579, n=50) than in SENSOR coordinates (r +0.366, n=63) and
  sits 15-20x above measurement noise: real sky structure — SIGNAL.
  **The discriminator is the re-aim.** A between-set re-point decouples the two
  frames, so a sensor-fixed term correlates in canvas coordinates and a
  sky-fixed term correlates in sky coordinates; without a re-aim the two are
  degenerate and no corner metric can separate them. The corners of different
  sets do not even see the same sky: mapping one set's four corner boxes
  through both solved WCS puts THREE of four outside the other set's canvas,
  and the one that survives shifts 0.27% from the sky offset alone — as large
  as the effect being measured.
  What to use instead: the **ramp slope fitted over a grid** — reproducible to
  7% between independent builds, immune to which sky lands in any one box, and
  the term a background-extraction stage actually targets. Changing an
  acceptance measure needs user ratification, so this is recorded as the
  candidate, not as a swap. Numbers: `datasets/july31/experiments.jsonl`,
  `background_residual_decomposition_set02_vs_set03`.

- **NEVER store a calibration master at 16-bit integer.** A master
  dark/bias/flat is a many-frame MEAN, so its precision is far finer than one
  integer step; rounding to 16 bits stores a SENSOR-FIXED quantization pattern
  that is then subtracted (or divided) identically into every light — the input
  to walking noise, which no rejection or cosmetic correction removes. MEASURED
  on a 200-frame master dark: the 16-bit-vs-32-bit difference is exactly
  uniform ±0.5 ADU (σ 0.2889 vs theory 1/√12 = 0.2887, zero bias), against a
  split-half-measured statistical floor of 0.4213 ADU — so 16-bit storage
  inflates the master's fixed-pattern residual 0.4213 → 0.5109 ADU, **+21%**.
  The error is per-pixel RANDOM, not low-order: it vanishes in a flat's 400 px
  regional medians (L-R 0.9974 both ways), so it cannot cause — or be cured by
  — any gradient or colour-cast symptom. Enforced by
  `scripts/stack/check_bitdepth.sh`; if a rig genuinely cannot afford 32-bit
  that is a new adaptation needing its own written removal condition.

