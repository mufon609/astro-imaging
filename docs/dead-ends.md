# Dead-end registry + acquisition checklist

Durable, arch-independent field lessons: the processing dead-ends never to
re-attempt (each with its mechanism), and the acquisition choices that outrank
any processing knob. **Read the dead-end registry before proposing ANY
experiment** — if a thing does not work, the mechanism why is here. Full detail
+ the original numbers live in git history (the NOTES at the commit whose message
begins `checkpoint:` — `git log --oneline --grep='^checkpoint:'`).

## Dead-end registry — do NOT re-attempt

Data / physics / tool-doctrine mechanism lessons.

**EVIDENCE STATUS — read this before citing any entry as settled.** Entries here
are not all the same kind of thing. Three classes:
- **MEASURED** — an actual controlled comparison with numbers and a named
  instrument. Cite freely, within its stated scope.
- **MECHANISM** — a physical or tool-behaviour argument, sometimes with a
  worked example, but no controlled A/B on this data. Reasonable to act on;
  NOT evidence, and it should not be quoted as a result.
- **DOCTRINE** — a practice adopted from vendor documentation or the field's
  consensus. Legitimate, but its authority is the source, not our data.
An entry with no numbers and no hedge is MECHANISM or DOCTRINE, whatever its
tone; the load-bearing ones are flagged in place. **Anything asserting a
result should carry its n, its instrument and its scope — and if a claim covers
one dataset, it says so.**

**TERMINOLOGY — the word "dust" is BANNED in this repo, and this entry says why.**
"Cosmic dust", "MW", "IFN" and "dust-safe" were used interchangeably for FOUR
physically unrelated things; the term was never defined and never independently
identified, and everything downstream of it — the background class limit, the
GraXpert-Division rejection, the sky-flat enabling condition, the denoise
strength limit — rested on a term nobody had measured. Use these four instead,
and say which one you mean:

**WHERE THE WORD CAME FROM — an ACQUISITION artefact, not a sky object.** The
term entered this project from early wide-field frames shot at **24 mm, 20+ s,
ISO 200**. At that focal length the plate scale is ~3x coarser than the 70 mm
work, so the star field below the detection limit never resolves and reads as a
smooth diffuse "dust". The same sky at **70 mm, ISO 1600** resolves those same
features into individual stars — which is exactly what sense 2 below then
MEASURED against Gaia. "Milky Way dust" was never a thing that exists; it was
undersampled starlight, and the word survived a change of optics that had
already falsified it. There is no Milky Way dust. There is nebular EMISSION
(sense 3), there is real interstellar dust seen in SILHOUETTE (sense 4), and
there are faint stars (sense 2). A term that is an artefact of one focal length
must not set doctrine for another.

1. **OPTICAL DUST MOTES** — physical dust on the sensor or optics. A flat-field
   feature, fixed in SENSOR coordinates, routinely measured (`findstar` speck
   counts on the flats). The only sense in which "dust" was ever correct, and
   it has nothing to do with the sky.
2. **UNRESOLVED STARLIGHT** — the frame-filling faint diffuse field: at this
   data's 17.0"/px in the galactic plane, the integrated light of Milky Way
   stars fainter than the detection limit. **MEASURED (july23 set-01+02, Gaia
   DR3 vs Siril, `qa_work/dust_identification.json`): the star layer's per-cell
   diffuse floor tracks Gaia's unresolved-starlight prediction at R² 0.9631
   over a 140-cell external lattice; detection limit G ≈ 11.0 at 50%
   completeness (one-to-one matched); ~0.2 catalogued sources per PIXEL
   brighter than G=17.** It is STARS — not dust, and not nebulosity.
   SCOPE: flux and source-count predictors are 97.7% collinear in this field,
   so that fit constrains rather than proves "flux specifically" — the clean
   separation is UNRESOLVED flux (R² 0.963) beating TOTAL flux (R² 0.503),
   which is not a collinear pair. The integrated starlight figure of
   22.74 mag/arcsec² is ONE 0.25° cone at the field centre; no frame-wide value
   was computed. The absolute photometric scale carries a 20-30% systematic
   (Gaussian-fit photometry on trailed stars) — every CORRELATION above is
   scale-free and unaffected, but any ADU prediction derived from it is not.
   ONE dataset, one field, one pixel scale.
3. **HII EMISSION** — NGC 7000, IC 1318 and the like: real diffuse emission,
   LOCALIZED, Hα-red. Measured on ONE region only: NGC 7000 sits +2.5σ above
   the starlight relation and reads R/G 1.1918 against a 0.9303 field.
   **SCOPE — 1 of 3 regions tested, and the other two did NOT stand out**
   (IC 1318 −0.07σ, NGC 6888 −0.72σ) — partly because the 1.4° cells are coarse
   for objects that size and the IC 1318 and "dark lane" test coordinates
   landed in the SAME cell. The honest claim: emission IS separable from
   starlight by this instrument on a large bright region, and the instrument
   was not shown sensitive enough for smaller ones. A nebula is not dust and is
   not "IFN" regardless — definitional, not measured.
4. **DUST SILHOUETTE** — real interstellar dust, which at this scale appears as
   ABSENCE, not emission: the Cygnus Rift dark lanes. **NOT PROPERLY MEASURED —
   treat as a working model, not a result.** Gaia integrated flux in 0.3° cones
   runs lowest near the plane (1.76e-3 at b=−2 against 1.27e-2 at b=−10), which
   is CONSISTENT with foreground extinction — but those cones are small enough
   to be dominated by their few brightest stars (noted as noisy when taken),
   and no test separated extinction from ordinary structure in the stellar
   distribution. The physical expectation (dust obscures rather than emits at
   17"/px) is textbook and is why this sense belongs in the list at all; the
   NUMBERS above do not establish it. The test that would: per-cell Gaia flux
   against a reddening map, or Gaia's own extinction estimates, over the
   sense-2 lattice.

**The rendering consequence, and it is not optional.** Sense 2 is stars, so it
is rendered AS STARS — preserving the brightness hierarchy of the population,
never amplified as a diffuse glow (that produced a uniform speckle-field with
no hierarchy and was rejected on sight — the `star_asinh` entry under
"Stretch / colour").

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
  surveys break it with camera ROTATION. Here the rotation is what an untracked
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
  their SUM and cannot apportion it without an external anchor, and both anchors
  are closed: a catalogue is structurally impossible here (trailed stars at
  17"/px) and a real flat IS the fix. **The time-varying half is measured, not
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
  exposures — is NOT packaged on this distro (`apt-cache policy scamp`: no
  candidate; `source-extractor` and `swarp` ARE). `source-extractor` 2.28.2 IS
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

- **SIRIL `offset` CLIPS AT ZERO IN 32-BIT FLOAT — its own help says it does not
  — and `stat` EXCLUDES zero pixels, so the two COMPOUND into a corruption that
  reads back as clean numbers.** `help offset` states *"In 32-bit mode, no
  clipping occurs"*. MEASURED by writing a uniform 300 ADU card, applying
  `offset -500`, and reading the SAVED FILE with an independent reader: it
  contains **all zeros**, not -200. Separately, a card that is half 0 and half
  400 ADU statts as **Mean 400.0, Median 400.0, Sigma 0.0, Min 0.0** where the
  truth is 200/200/200 — zeros are dropped from every estimator while `Min`
  still shows 0.0, and an all-zero region reports *"Statistics computation
  failed for channel N (all nil?)"*.
  **Why this bites here specifically:** a pedestal-free dark-subtracted sky sits
  ~1.5 sigma above zero, so every real light has a negative minority by
  construction (0.24% measured on aug09 lights, far more after flat division).
  An `offset` anywhere in a chain silently zeroes it and `stat` then reports the
  survivors as healthy. This corrupted a whole real-data run of the
  iterative-flat experiment — a -56443 ADU `offset` drove a flat's corners to
  zero, which read back as "all nil" — and it was caught only by reading saved
  pixels with a non-siril reader.
  **The clip-free equivalents, all probed:** `isub` of a constant card preserves
  negatives exactly (300 - 500 = -200.0), `imul` and `fmul` do not clip in either
  direction (`fmul` reached 90000, i.e. >65535 survives in 32-bit). To subtract a
  large constant from signed data, use `isub`, never `offset`; if an `offset` is
  unavoidable, order it so the operand is POSITIVE. Two further behaviours from
  the same probe: **`stack` writes no negative values** (frames 99.99% negative
  produced a 100%-zero stack), and **`subsky` leaves a constant pedestal rather
  than zeroing the level** (a 500->800 ADU ramp comes back uniform at 627.00).
  **Corollary for verification:** siril's own `stat` cannot be used to check
  whether a siril operation damaged an image, because the damage is invisible to
  it. Read the saved pixels with an independent reader.

- **`seqsubsky` REFUSES A FRAME CARRYING NEGATIVE PIXELS** — *"Failed to generate
  background samples for image 0: removing the gradient on negative images is
  not supported"*. Pedestal-free dark-subtracted lights always carry them and
  flat division amplifies them (calibrated aug09/set-05 frames measure a minimum
  of **-2635 ADU**, from division by the flat's near-zero pixels), so any
  background operator run on flat-fielded pedestal-free data needs a constant
  pedestal added first. The pedestal **cancels exactly** out of the operator —
  the plane fitted to `C+P` is `(plane of C)+P`, so `subsky` returns
  `C - P_t + c_t` either way — and costs nothing numerically (a 30% gradient
  still resolves to ~2250 float32 levels at a 56k pedestal). Verify positivity
  with a guard that can fail, and remove the pedestal with `isub`, not `offset`
  (entry above).

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
  **WHY THE DOCTRINAL ARGUMENT DOES NOT TRANSFER — the load-bearing point.** A
  ratio of two flats from one night, lens, focal and aperture cancels vignetting
  EXACTLY, so what differs between a group flat and the set flat IS THE SKY TERM;
  the OPTICAL state (V, dust, focus) does not change inside a 25-minute burst.
  The ratified rule is about optical-state matching. What a narrower window
  tracks better is the SKY — which is the sky flat's DEFECT, not its purpose — so
  narrowing does not reduce the contamination, it changes WHICH sky is imprinted
  on the object and makes that imprint DIFFER between members.
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

- **A `-framing=min` CANVAS IS SIZED BY TIME SPAN, NOT FRAME COUNT — so a
  metric taken at a margin relative to each canvas's own edge is not
  like-for-like across sets.** The intersection keeps only what every frame
  covers, so the trim is how far the sky swept, which at a fixed cadence is the
  burst duration. MEASURED, july31: set-04 ran 777 s and lost 605 px of x;
  sets 01-03 ran 1497-1624 s and lost 1153-1163 px, leaving set-04 with the
  LARGEST canvas (5459x3858) and the FEWEST frames (260) — the same fact stated
  twice. `regional_stat.py` at margin 200 puts set-04's boxes 279 px further
  out in x than set-01's; re-measuring all four at a common physical extent
  moved the numbers 0.40/0.49/1.03/1.17 -> 0.48/0.49/1.09/1.33 — set-04 got
  WORSE, so the geometry is not the explanation, but the corrected shape is a
  STEP between set-02 and set-03 rather than a monotonic doubling.
  Second-order but unmodelled, and live: the total trim runs **1.16-1.29x the
  pure translation** in every set. The excess is field rotation — a
  non-tracking alt-az head rotates the field as well as drifting it — plus the
  warp border and the groups route's two-stage framing. `fingerprint.py`
  computes translation only, so every disk and framing figure derived from
  `drift_px` under-counts.

- **A BARE md5 OF FITS PIXEL DATA IS ONLY COMPARABLE WITHIN ONE BYTE-ORDER
  CONVENTION — quote a pixel-difference COUNT, never a digest, when the question
  is "did this product change?"** FITS stores pixels BIG-ENDIAN on disk, so
  `astropy` hands back a `>f4` array; hashing it AS READ and hashing it after any
  native-order cast (`<f4`, or an implicit `.astype`) give DIFFERENT digests for
  BIT-IDENTICAL pixels. MEASURED on one file, both ways, by two sessions
  independently: `armA` reads `7ea062fb217e6254` as-read and `91237e3e98fe7477`
  native; `armB` reads `15c99af99b5e0c6b` and `3a23c8725ec6d972`. Both sessions
  were right and the products were identical. **The failure mode is a
  false POSITIVE**: two readers comparing digests across that boundary conclude a
  product changed when nothing did — the expensive direction, because it sends a
  session chasing a corruption that does not exist. A difference COUNT
  (`(a != b).sum()` with `max|diff|`) is convention-free and is what the verdict
  should quote; if a digest is recorded at all, the convention is recorded beside
  it. Related trap, same family: **a whole-file `cmp` is the wrong test for "are
  these pixels the same"** — siril stamps its own creation `DATE` and the chain
  stamps `PIPEREV` (`git rev-parse --short HEAD`; what that couples across
  parallel sessions is a BINDING RULE in `CLAUDE.md`, not restated here), so two
  pixel-identical products always differ as FILES. The identity control here read "NOT byte-identical"
  while measuring 0 differing pixels of 69,359,745, max\|diff\| exactly 0. A check
  that fires spuriously trains the operator to bypass it, which is how a real
  failure gets waved through later.

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

**Background:**
- **MECHANISM, NOT MEASURED:** the galactic-plane star field is frame-scale
  curvature at wide focal, so `seqsubsky 2` is expected to absorb it and only a
  first-degree plane or a full BGE to preserve it — what would be preserved is
  UNRESOLVED STARLIGHT (terminology entry above), not a dust complex. **No
  controlled degree-1-vs-degree-2 comparison on this data is on record** — no
  numbers, no instrument, no n — yet this has been gating the background policy
  (and the README class limit) as though it were a result. The test that would
  settle it: one knob, `seqsubsky 1` vs `2` on the same frames, judged on the
  same Gaia-vs-cell instrument used for the terminology entry, since that
  measures the very signal at issue. Same flag: stack-level-only BGE is
  reported to leave a structured residual with visible rings and to eat the
  same frame-scale starlight, making per-frame `subsky 1` the preferred step —
  "visible rings" is an unrecorded eye observation (no image, no metric, no n);
  treat the per-frame default as a reasonable prior, not an established result.
- GraXpert AI smoothing is NOT faint-signal protection — smoothing blurs the
  model OUTPUT, not the inference; frame-filling faint structure reads as the
  trained light-pollution class and is absorbed. Use a plane/off for
  object-filling fields. BGE does NOT absorb a centred galaxy's halo (it measures
  STRONGER against a lower far-field sky).
- **GraXpert AI `-correction Division` as a synthetic flat on a field filled with
  UNRESOLVED STARLIGHT absorbs most of the extended structure — measured, even
  at max smoothing.** Four-arm probe (july23 set-03, 60-frame stacks, same
  chain, one knob), NAN-region contrast as % of local sky R/G/B: own sky flat
  8.5/2.9/5.6; GraXpert Division (smoothing 1.0, AI 1.0.1) **2.4/0.7/2.1** —
  the division ate ~2/3 of the nebula while flattening corners to ±2% (it
  flattens the REAL sky structure too; perfectly flat corners on a MW field are
  themselves a defect signature). The vignetting-only promise holds only where
  faint structure does not fill the frame — same enabling condition as the sky
  flat. UNTESTED alternative: GraXpert's classical grid interpolators via
  `-preferences_file` (RBF/spline, no AI model). Also measured in the same
  probe: the 16-bit intermediates chain (same flat, same frames) reads only
  ~55-70% of the 32-bit arm's extended contrast (4.8/2.4/3.9 vs 8.5/2.9/5.6) —
  integer round-tripping through calibrate/warp/register eats faint signal; the
  16-bit-era adaptation cost real structure, not just +0.3% noise.
- On a union/max canvas, CROP to the verified coverage frame BEFORE any
  background step: `subsky`'s sample grid ingests the canvas's zero-coverage
  rims — its `-tolerance` excludes only BRIGHT outliers, not empty sky — and
  the fit skews. Crop-before-background is the pinned order.

**Stretch / colour:**
- **A LAYER THAT HOLDS A SMALL RESIDUAL AMPLIFIES ANY ERROR IN THE LAYER THAT
  HOLDS THE LIGHT — and a single per-channel gain cannot correct a layer with
  two populations.** MEASURED on the july23 separation (Siril `stat main` under
  `fmul 1000`; at plain `stat` the star layer's medians print 1.6/1.7/1.5 and
  its R/G is quantization-limited to ±6%, larger than the effect): linear stack
  median R/G 0.9992 / B/G 0.9988 (the SPCC truth); starless layer 1.0022 /
  1.0048 (+0.30% red); star layer 0.8977 / 0.8600 (−10.2%, −13.9%). The split
  is mass-balanced, so the third line is not a stellar colour — it is the
  second line's 0.30% error levered by the mask carrying only ~4% of the
  stack's level: `(0.9992·G − 1.0022·G_less)/(G − G_less) = 0.9306` reproduces
  the measured value from the other two.
  **Two traps found trying to correct it, both worth more than the fix.**
  (1) WRONG STATISTIC: a diagonal `ccm` whose gains came from the layer's
  MEDIAN (its diffuse floor) was applied to the whole layer including the star
  cores; validated on the median alone it reported a perfect 1.0001/0.9992
  while the STARS came out +8.3% R / +11.0% B — visibly neon blue, user-caught
  (a median is robust against exactly the population under test — mirror of the
  halo-photometry entry below). Targeting the star-weighted MEAN instead fixed
  the stars (0.9991/0.9991) and pushed the FLOOR off (0.9226/0.8986) — the
  defect moved, it did not go. A single gain cannot serve both populations;
  REPORT BOTH STATISTICS.
  (2) WRONG ORDER: the populations' colours AGREE on the raw stack
  (cores-vs-floor spread −1.1%/+0.0%, so one gain is valid there) and DIVERGE
  once a stellar sharpen runs before the separation (+8.4%/+11.2%), because
  concentrating flux into cores changes what the separation assigns to each
  layer. Sharpen AFTER separating, on the star layer only (measured spread then
  −3.1%/−3.7%).
  **Also refuted here:** darkstar's colour-true STARLESS (0.9990/0.9987) does
  NOT imply a colour-true star layer — its cores-vs-floor spread is
  −18.2%/−30.7% stretched, far worse than StarNet2. Do not adopt it as the
  separator on that inference. SCOPE: all of this is ONE dataset and one
  separation; the leverage ARITHMETIC is general, the specific numbers are not.
- **RAISING `star_asinh` TO AMPLIFY THE STAR LAYER IS A DEAD END — it destroys
  the stellar brightness hierarchy and renders a uniform speckle field.** The
  shipped value is 1000; 20000 was tried on the reasoning that the star layer
  carries this field's unresolved starlight (true, R² 0.9631) and should
  therefore be lifted to reveal it (FALSE, and the error). `asinh` is a
  COMPRESSOR: gain runs 1362× at input 1e-4 but only 7.8× at 0.1, so **two
  stars differing 100:1 in real measured flux render 2.25:1 — a 44× compression
  of dynamic range** (17× at the shipped 1000). MEASURED consequences, all
  visible at 1:1 and rejected on sight: no brightness hierarchy, uniform
  same-size speckle, soft blobs rather than points, and random per-dot colour.
  The compression ratios are ARITHMETIC from the asinh transform and are exact;
  the visual consequences were user-judged on full-frame finals. TWO MECHANISMS
  HERE ARE INFERRED, NOT ISOLATED BY EXPERIMENT: that the wing-lift (~1362× at
  the faint end vs 7.8× at 0.1) is what cancels an upstream sharpening — no
  before/after FWHM was measured ON THE RENDER, only on the linear layer; and
  that the random colour comes from the star layer being amplified with its
  chroma noise intact — the tier does denoise only the starless layer (a
  structural fact, readable in the script), but no arm isolated that as the
  cause. Both are plausible and neither was controlled.
  The rule this establishes: unresolved starlight is rendered AS STARS,
  preserving the population's brightness hierarchy — never amplified as a
  diffuse glow. A "low" `star_asinh` is not timidity; it is what keeps the
  compressor in a range where stars still look like stars. Do not re-attempt
  the lift, and do not reach for it when a field looks empty.
- Unlinked autostretch on a calibrated stack is the chroma-blotch ("rainbow")
  engine — after SPCC there is no cast to compensate; use linked. Unlinked
  sky-anchored stretch as a narrowband line-lift is a NO-OP (BGE+SPCC already
  equalize the channel skies; the line imbalance is OBJECT flux, not sky).
- SPCC narrowband equalizes O3=Ha and erases the O3 sphere (raw O3/Ha ~1.5 →
  ~1.0; sphere B/R 0.77 vs 3.21). Siril's own docs confirm SPCC-NB gives "real
  intensities"/"a huge green cast" and recommend Manual Color Calibration for
  SHO — i.e. for a narrowband SHO target, SPCC is the *cause* of the lost sphere,
  not the fix. (The star-colour-neutral fix is a candidate DESIGN, UNTESTED —
  BACKLOG:`star-neutral-colour` + `TOOLS.md` Tier 10; not settled, do not cite as a method.)
- `rmgreen`/SCNR on a sky that is not green-dominant prints a global magenta cast.
- Siril has NO native GENERAL chrominance-noise tool (its own docs punt to GIMP,
  byte-identical disclaimer in 1.4.4 AND 1.5.0-dev). `rmgreen` IS a native
  SCNR-style filter but SINGLE-HUE (green cast only) — it does not close the general
  chroma gap. NEVER hand-roll a chroma coring; close the gap with an AI denoiser on
  x86 (tool options + their chroma-vs-luminance flags: `TOOLS.md`).

**Separation** (informs the x86 tool choice):
- **MECHANISM, NOT MEASURED:** a mask+inpaint separator is reported to destroy
  resolved-object structure (inpainting HII knots out as stars and screening
  them back as blobs), where a learned separator (StarNet2/StarXT) keeps
  field-star flux and far less object structure — hence use the learned one on
  resolved objects. No side-by-side numbers are recorded. The conclusion is
  consistent with how the two methods work and with the fact that the shipped
  chain's StarNet2 separation measures cleanly, but it is not a controlled
  result.
- A bright-star residual/shell is a per-DATA property (tight PSF vs big trailed
  PSF) — measure per dataset, never carry one set's number to another.

**Detection / solve / registration:**
- Frame QA + registration run on DEBAYERED data only — CFA-lattice registration
  false-positives on cloud texture (adjacent cloud frames cross-match → a cloud
  reference).
- **Siril's internal solver fails ultra-wide TRAILED fields — the blocker is its star
  MATCHER, not detection or catalogue depth (both tested and ELIMINATED).** Measured
  (36.45° field, correct centre from a blind solve, local Gaia, `-nocrop`): relaxed
  detection (`setfindstar -relax=on -roundness=0.05 -sigma=0.5`) raised candidates
  3316→8694 and still failed; `-limitmag=+4` raised the fetch 2177→138,498 Gaia stars
  (limit mag 7.81→11.81) and still failed — do NOT re-attempt those two knobs.
  `platesolve -localasnet` does not rescue it: it still feeds astrometry.net Siril's
  `findstar` PSF detection, which IS the failure mode (the FOV>5° detection auto-crop is
  *"Ignored for astrometry.net solves"*, so `-nocrop` is moot there). Side fact: Siril's
  AUTO limit mag for a 36° field is only 7.81 while detection goes far deeper — a
  population mismatch, not the blocker.
- **The fix: feed astrometry.net a SHAPE-BLIND xylist (its INTENDED override — solve-field
  on an xylist runs NO pixel extraction, matcher geometry-only, Lang 2010). Blind-solve
  first, label after.** Best source is SExtractor's core `sep`: returns trailed sources
  (median elongation ~1.3), blind-solves at HIGHER odds than in-house peak centroids
  (logodds 299 vs 289, scale Δ 1.2e-5), identical SPCC K — `solve_field.py` defaults to it
  (`extractor_ab.json`). Robustness ranking: (1) asnet + **sep** xylist — the sole
  extractor (the in-house peak-xylist fallback is RETIRED: sep passed every x86 solve at
  equal-or-higher odds, identical SPCC K); (2) `image2xy` xylist (shape-blind, untested —
  its trail knobs `-a`/`-p`/`-m` aren't exposed by solve-field and `-a` can fragment one
  trail into spurious detections); (4) `-localasnet` and ASTAP LEAST — both
  PSF-fit/roundness-gated (ASTAP docs: *"star streaks … will be ignored"*; wide DBs W08
  FOV>20°, G05 FOV>6°, G17/H17/H18 deprecated). Caveats: `--no-remove-lines
  --uniformize 0` (or list filters) still thin a supplied xylist; and two valid fits'
  centres can differ by hundreds of arcsec (the SIP wobble below), which never reaches
  SPCC (it re-matches stars from the seed).
- **Siril SPCC SIGSEGVs (exit 139) in aperture photometry when the sensor DATABASE
  is missing — not a data/field bug.** MEASURED on a fresh x86 rig: the crash hit
  at "Applying aperture photometry to N stars" on ANY star count (5305, 106, 291),
  any field size (full 20° or a 7.5° crop), and single- or multi-thread — the SPCC
  sensor/filter/white-reference database dir was absent, so siril applied a
  `(null)` sensor response and dereferenced it. The catalog (Gaia chunks) being
  present is NOT enough; the sensor database is a SEPARATE git repo. The tell is
  `spcc_list oscsensor` returning EMPTY and a log line "Unable to open directory:
  .../siril-spcc-database". Fix = clone it (CLAUDE.md Environment, SPCC
  prerequisites). Do NOT chase the star count, field width, catalog format, or bit
  depth — all ruled out; the crash prints nothing useful and mimics a data bug.

- **A BIG UNION CANVAS DEFEATS THE SOLVE, AND THE ROUTE THAT WORKS IS TO SOLVE A
  CENTRAL CROP LIKE A MEMBER AND SHIFT `CRPIX` BACK BY THE CROP OFFSET —
  header-only, pixels untouched.** MEASURED on the 52-member corpus union
  (8510×5475, 46 Mpx, 52 member footprints): the hinted attempt failed on
  seam-contaminated detection and the blind fallback SHIPPED a false solution —
  RA 6.0 Dec −65.1 at 12.96″/px, logodds 22 against a healthy family of 100–570 —
  which siril SPCC then consumed to completion, producing plausible-looking K
  factors (G 0.592 against a 0.649–0.682 family) instead of failing. The
  recovery: crop the central region to scratch, solve it as if it were a member
  (logodds 130, 17.06″/px), then shift `CRPIX` by the exact crop offset. Validated
  by `shape_at_sky.py`'s own per-star RA/Dec verification at four positions
  INCLUDING ones far outside the solved crop, and SPCC on the corrected WCS
  returned K_G 0.669, in family.
  **Two traps measured on the way, both of which waste a session.**
  (1) `--central` is a fraction of the FRAME, i.e. a half-width per axis, so
  `--central=0.5` keeps the central half of each axis and `=1.0` restricts
  nothing — the semantics are pinned in `solve_field.py`'s docstring.
  (2) **`--max-stars=1500` explodes the quad search on a canvas this size: 64 min
  of CPU and NO result.** The default 200 is ample to MATCH; raise it only when
  the SIP distortion terms are the product being consumed, and not on a union
  canvas. The blind-fallback half of this incident is now gated — `solve_field.py`
  refuses a solution contradicting its own hints at exit 9, and this union is its
  recorded falsification case.

- **A TWO-WINDOW DRIFT INSTRUMENT MUST CONFINE BOTH WINDOWS TO ONE CONTIGUOUS
  CAPTURE RUN — dir-endpoint windows measure re-aim + drift, a rate that is
  neither mount signature.** A re-aim can only occur ACROSS a capture-run
  boundary (the audit's segment_runs law: within a run the interval timer
  leaves no time to recompose), so first/last-of-dir on a dir holding a stray
  pre-burst frame straddles the re-aim. MEASURED (140-frame dir: 1 aim frame,
  a 661 s pause carrying a 0.373 deg-RA re-aim (981 arcsec sky-projected), then a contiguous 139-frame burst
  at 3.0 s cadence): first/last read RA rate 6.9751 deg/hr — 0.46x sidereal,
  neither fixed nor tracked, a spurious mount-underivable stop on a rigid
  tripod — while the run-confined window on the same dir read 14.8724 deg/hr
  = 0.99x sidereal, a clean fixed signature (dec drift −19.4 arcsec over
  414 s). Generalizes to ANY rate derived from dir-endpoint epochs (cadence,
  drift px/min). `mount_probe.sh` windows inside the longest run
  (acquisition.timeline + segment_runs — the audit's own boundary logic, not
  a re-derivation) and records the window facts in `mount_probe.json`; a dir
  with no readable epochs/frame numbers segments to ONE run = endpoint
  behavior. Corollary: a stray aim frame also EXTENDS the `-framing=min` trim
  (the canvas is sized by TIME SPAN — framing entry above), so it is a cull
  candidate on canvas grounds independent of its optical quality (~58 px of
  width against 1/140 of depth here).
- **Siril planetary registrations (Image Pattern Alignment AND KOMBAT) fail — quietly
  producing garbage shifts — when the drawn selection does not CONTAIN THE TARGET'S
  WHOLE MOVEMENT across the sequence** (the official docs state the precondition; a
  drifting target that exits the box leaves the correlation/template matcher with
  noise, and nothing fails loudly). MEASURED (july26 lunar, ~110 px disc, 230/665 px
  untracked drift, selection ~250 px = smaller than the track): tail-frame shifts
  (41,10)/(50,20) where the physical drift demands ≈(10,185); 809 frames "registered"
  in 984 ms (~1 ms/frame — no real per-frame work) vs 220 frames in 23.5 s; every
  regdata quality field −1 → `stack -filter-quality=25%` computed threshold 0.000000
  and filtered in ZERO frames; the applied-registration control stack rejected the
  misaligned disc to a faint smudge (winsorized 3/3 — the per-pixel disc minority
  rejected as outlier). THE RULE: size the selection to the full drift track (a
  staging crop that already bounds the track makes "nearly the whole frame" the
  correct selection) — and after registering, verify per-frame quality was actually
  WRITTEN (regdata ≠ −1) before any quality-filtered stack; the registration docs do
  not promise quality storage, only the stacking docs imply it.
  **KOMBAT specifically is DEAD on this rig's 1.4.4 for this corpus** — four
  configurations measured (tight template + default 25% area; whole-frame selection +
  100% area; tight template + 100% area — the mechanically correct template-matching
  pairing — twice): every run left 219/220 frames with a NULL H (no match) and
  quality −1, failing silently in the GUI. Do not re-attempt KOMBAT on 32-bit float
  3-channel crops of this class; the surviving in-Siril candidate is Image Pattern
  Alignment with a track-covering selection, and the cross-tool route is PSS.
- **Siril 1.4.4 planetary registrations write NO per-frame quality — even on a
  VERIFIED-successful run — so a `-filter-quality` stack has nothing to consume.**
  MEASURED end-to-end (july26 set-01): Image Pattern Alignment with a track-covering
  selection produced physically-correct translations (tail (10,187–190) vs predicted
  ≈(10,185); limb coherent on the applied-registration control stack) yet every
  regdata quality field stayed −1 and `stack -filter-quality=25%` still computed
  threshold 0.000000 / filtered-in 0. The stacking docs' "quality (planetary DFT or
  Kombat registrations)" filter criterion is a dead letter in 1.4.4. Quality-ranked
  ("lucky") frame selection therefore needs a RANKING tool (PSS `--stack_percent`,
  AS!4 — both x86-only), or Siril 1.5's MPP if it measures quality — verify before
  designing on it.
- **Failed Siril GUI registration attempts leave the sequence's SELECTION state
  corrupted — silently.** Symptom: after repeated failed planetary registrations the
  .seq held frames 2–220 deselected with nb_selected = −218 (a counter driven
  negative), making a later `seqapplyreg` abort with "registration data is a set of
  null matrices" even though layer R1 held valid transforms — the failure surfaces
  one step downstream, mislabeled. Repair is scriptable: `select <seq> 1 <N>` before
  applying; after ANY failed GUI registration, inspect the .seq header (S-line
  nb_selected + I-line flags) before trusting the next step's error — or take the
  safe reset: DELETE the .seq and let the next sequence search rebuild it clean
  (cheap, and it removes the selection debris).
- **Planetary DFT registration ALIASES shifts beyond ±half its correlation window —
  and stacks a SECOND coherent disc exactly one window away.** Circular (FFT)
  correlation resolves translation only within ±window/2; a target whose drift from
  the REFERENCE frame exceeds that wraps modulo the window, silently. MEASURED
  (july26 set-02, 1024×1536 crop, 809 frames, reference = frame 1 at one end of a
  ~670 px monotonic track): frames with true shift ≤ +379 registered exactly; the
  tail's true +670 was recorded as −355 = 670 − 1024 (the frame's SHORT dimension —
  the effective window), off by exactly one window; the stack rendered TWO clean
  discs ~1024 px apart (each wrap-class coherent at its own position), REPRODUCED
  identically on a clean rebuilt sequence — the method's arithmetic, not stale
  state. Set-01 (max shift 190 px) never hit it. THE RULE: put the REFERENCE near
  the TRACK MIDDLE (`setref` before registering) so max |shift| < window/2 —
  halving the reach requirement; verify tail shifts against the physical drift after
  EVERY planetary registration (predicted-vs-regdata is a 10-second check). Stack
  verification is WHOLE-FRAME first, zoom second — a limb/zoom coherence check on
  ONE region cannot see a second disc (the registry's trap-1 in new clothing). Keep
  all frames (dropping a minority sub-focal subset buys no matching gain and pays
  the full √N noise penalty).
- **Wide UNTRACKED edge smear: "field rotation / gnomonic projection" is NOT the
  cause.** For an IDEAL rectilinear lens a pure camera rotation maps EXACTLY to an
  8-DOF homography (stars are at infinity; sky rotation is SO(3), linear in
  homogeneous coordinates) — zero residual. Szeliski, *Image Alignment and
  Stitching* §2.3: the only residual that survives an optimal global fit on a star
  field is **unmodelled RADIAL LENS DISTORTION** — the real map is
  `distort ∘ H ∘ distort⁻¹`. Distortion displaces stars ∝ radius → centre sharp,
  edges smeared; as a star drifts it samples a different local distortion and no
  global fit absorbs the difference. So the fix is **undistort → homography**, NOT
  a local/elastic transform; do not chase "better global transforms" (`-transf=`
  tops out at homography, which is already exactly right). MEASURED on a
  43-min/1500-px-drift set, two independent ways: a 9-min (310 px) window is better
  whole-frame (majFWHM 3.87 vs 4.74 px) and undistorting the frames collapses Siril
  `seqtilt`'s off-axis aberration 0.57 → 0.25 px at FULL depth — remove the drift
  *or* remove the distortion and the homography becomes exact, which is the same
  statement twice
  ([`wide-field-untracked-registration.md`](wide-field-untracked-registration.md)).
  (The short-window arm's per-radius numbers came from a retired in-house radial
  metric — trap 3 below — and its stacks are gone, so they are not quoted; the
  whole-frame and `seqtilt` evidence above is what the conclusion rests on.)
- **astrometry.net's SIP is NOT a reproducible lens model at wide index scales — so
  `register -disto=` has no model to eat.** Fixed tripod (distortion physically identical
  every frame), yet two solves 43 min apart disagree at the same sensor positions by
  65 px median / 128 px worst (a real lens model must agree to ~1 px). A 1500-star cap cut
  it only to 44 px (worst 132) while sharply improving the LINEAR solve (RA-drift error
  6%→0.3%, logodds 127→782) — more stars fix the POSITION, not the distortion. Mechanism:
  the SIP tweak is constrained by *matched index* stars, and the 4200-series index at the
  scales an ultra-wide field needs (12–19) is Tycho-2-based and sparse. Feeding this SIP to
  `register -disto=` is a measured LOSS (whole-frame majFWHM 4.74→6.02 px, stars
  17,770→7,561, smear frame-wide); this also blocks WCS-reprojection (SWarp / astropy
  `reproject` need the same per-frame solution). **The lesson: for a wide UNTRACKED field,
  fit-distortion-from-sparse-trailed-stars is the dead end; an OFFICIAL *measured* lens
  profile is the route** (darktable + lensfun, `TOOLS.md` Tier 2b) — immune to index
  sparsity, and a measured WIN: `seqtilt` off-axis aberration (radial term) 0.57 → 0.31 →
  0.25 px, stars 5095 → 10707 → 11805, 54/54 registered (control → corrected → full depth).
  (Fitting from star correspondences BETWEEN frames — PixInsight/APP — is a different, viable
  mechanism; only the per-frame *catalog* solve fails.)
  **What the model does NOT buy (same runs):** sharpness is NULL (truncated-mean FWHM
  3.20 → 3.28 → 3.27 px — the in-exposure floor is untouched), and the one-sided component
  is NOT corrected (sensor tilt 0.50/16% → 0.42/13% → 0.51/16%) — a radial model cannot fix
  a one-sided term. It buys star COUNT and radial UNIFORMITY, not FWHM.
- **THE SUB-STACK COMPOSE IS A MOSAIC, NOT A STACK — and a single HOMOGRAPHY cannot
  align members whose optical axes are degrees apart while any lens-model residual
  survives. This is the largest star-shape defect measured in this repo's products,
  and it is invisible to every per-member measurement.** A group is a CONSECUTIVE
  time block, so within one 1497 s burst the sky sweeps 6.25° of RA and the five
  members of one set solve to centres **4.28° apart** (aug06/set-01: RA 303.87 /
  304.78 / 306.03 / 307.41 / 308.16). Composing them is stitching different
  pointings, and the registry's own Szeliski result then applies one level up: the
  true member-to-member map is `distort ∘ H ∘ distort⁻¹`, and `register -2pass`
  fits `H` alone.
  MEASURED (Siril `findstar`, open gate, 800 px boxes placed by each product's own
  solved WCS and VERIFIED by Siril's own per-star RA/Dec; FWHM/roundness = medians
  of the 30 brightest fits, so products of very different depth are rank-matched):
  at **RA 294.86 / Dec +44.99** all five set-01 members read **2.42–2.54 px /
  roundness 0.924–0.942** at own-field radius 0.41–0.62 — mid-field, not an edge —
  and their own 5-member compose reads **3.48 / 0.582**. The 13-member 3-set union
  adds 0.530, the 28-member cross-night union 0.458: **the within-set step is most
  of it.** Control, same instrument, same members, RA 314.72: members 2.23–2.38 /
  0.903–0.958, compose **2.43 / 0.949** — the compose costs nothing there.
  **The discriminator that names the fix:** the members' OWN astrometric solutions
  place the same stars within **0.10 px median / 0.26 px p90** (10 pairs, n=1151)
  at exactly the sky where the homography compose loses 1.06 px of FWHM and 0.34 of
  roundness. The alignment information exists; the homography discards it. That is
  the measured case for per-image astrometric resampling
  (BACKLOG:`compose-homography-smear`, SWarp) rather than a better
  shared lens model.
  **Blind to it:** every per-member measure (each member is clean), and — as the
  accepted product shipped — the compose's own geometry measurement, whose zones
  were then CANVAS-radial and which returned **UNMEASURED** on this union
  (378/378 pairs, no zone with ≥100 matched stars). `member_separation.py` has
  since been rebuilt (member-own field radius, 0/378 unmeasured) and its
  threshold layer removed by user ratification — it measures, it does not gate
  (`docs/combine-contract.md` §5).
  **The disagreement is TWO terms, both measured, neither yet sized against the
  other.**
  *(a) The compose makes part of it.* The same members disagree more when
  registered inside a big sequence than when composed among themselves:
  july31/set-01 **1.12 → 3.02 px**, aug06/set-03 **0.95 → 3.38 px** going from
  their own 4–5-member compose to the 41°, 28-member union. `register -2pass`
  fits ONE homography per member against a common reference, so a member
  overlapping that reference over a limited region gets a compromise fit that
  extrapolates badly elsewhere — and two members compromised over *different*
  regions disagree with each other.
  *(b) One set carries a genuine OPTICAL-STATE CHANGE MID-BURST.* aug06/set-01's
  groups 1,2,3 agree to **0.21–0.34 px** and groups 4,5 sit **2.95–4.91 px**
  away, across a boundary that is 100 consecutive frames into a 1497 s burst.
  Three things rule out the alternatives: it is not pointing spread (members 1
  and 3 are **2.16° apart at 0.34 px**, members 3 and 4 are **1.38° apart at
  3.14 px** — a smaller separation giving 9× the disagreement); it is not the
  registration reference (1|4 reads **2.95 / 2.98 / 3.02 px** with the reference
  set to member 1, 3 and 5 in turn, every other pair moving <2%); and the
  disagreement NORMALISED BY AXIS SEPARATION — the quantity a single shared
  optical state holds constant — is flat at **0.21 / 0.23 / 0.32 px per degree**
  for groups 1,2,3 and reads **3.07 and 3.58 px/deg** for 3|4 and 4|5, with 4|5
  reaching 1.97 px at the SMALLEST adjacent separation of the five (0.55°).
  Acquisition is exonerated as a cause of any interruption: all 500 frames are
  2.5 s / ISO 1600 / f/4 / 70 mm at a 3.00 s interval (min 2.99, max 3.01) with
  **no gap anywhere**, including at that boundary.
  **A TRAP WORTH KEEPING: the residual's cos(θ) DIPOLE is NOT evidence of a
  decentring.** Two members sit at different pointings, so differencing ONE
  radial field about two displaced centres gives a dipole by construction, with
  amplitude proportional to their axis separation — the null expectation, not a
  mechanism. Reading it as "the optical axis moved" was an error made and
  retracted here; only the separation-normalised ratio discriminates, and it says
  the optics changed without saying what kind of change it was.
  **RESOLVED — it is BOTH, and they are separable. MEASURED, one knob, 250 frames
  warped once and shared by every arm.**
  *(i) The per-group AUTO-PICKED registration reference is worth 6.5x on its own.*
  The picks wander badly — read straight out of the `.seq` at frames
  **6, 26, 15, 3, 26 of 50** — and the break always lands on whichever member's
  reference sits LATEST. Five independent per-block registrations give a worst
  pair of **3.12 px**; ONE global reference over the same frames gives **0.48 px**.
  The split position moves with the picks (3|4 in the shipped 100-frame build,
  4|5 here), which is the tell.
  *(ii) But one reference only MOVES the error, it does not remove it* — from
  between-member DOUBLING into within-member BLUR, 0.25-0.27 px against 3.12 px.
  *(iii) The underlying change is PHYSICAL, TIME-PROGRESSIVE and ONE-SIDED.*
  A first single-reference arm is USELESS for this question if the reference
  auto-lands at an end (it did: frame 6 of 250), because then "late" and "far
  from the reference" are the same thing. Pinning it to the MIDDLE (frame 125)
  separates them: at MATCHED drift distance the late block beats its early twin
  by **+0.25 px / -0.064 roundness** (99f vs 101f) and **+0.27 px / -0.104**
  (49f vs 51f) — on the LEFT field only, while the right field is flat across all
  five blocks (2.49-2.59 px, roundness 0.850-0.874). The ordering is TIME, not
  distance: block 3 sits ONE frame from the reference and reads 2.67 px on the
  left where block 1, 99 frames away, reads 2.54.
  **Mechanism undetermined; two candidates, one discriminator.** Differential
  atmospheric REFRACTION is horizon-fixed and therefore sensor-fixed on a fixed
  tripod, progressive as altitude changes, and non-homographic by construction —
  the same open question as BACKLOG:`one-sided-band`. Mechanical SAG of an
  extended zoom barrel is also progressive and one-sided. Refraction scales with
  zenith distance and reverses sense between a rising and a setting field; sag
  does not. The test needs the observing SITE (this corpus's EXIF carries no GPS)
  or the same middle-pinned build on sets shot at different altitudes.
  **What that does and does not license.** It does NOT revive per-set models — a
  per-set model would be wrong for part of its own set. It establishes that the
  OPTICAL-STATE tier can be finer than the SET tier and that a state boundary is
  something to DETECT, which is what this measure now is. Still open: what
  physically changed at that boundary (focus/temperature drift and a mechanical
  shift both predict a radial term), and the split of the union's 2.43 px corner
  median between (a) and (b).
- **DEAD END — "the aug06 member EDGE deficit is introduced by the within-group
  registration/stack." It is not: the session difference is FLAT across the whole
  chain once the star population is flux-matched.** MEASURED, one instrument at
  three levels (the *same* 800 px march that produced the finding — calibrated
  single, the same single after the darktable warp, and the 100-frame member those
  frames built), edge-minus-centre FWHM, aug06 minus july31, pooled over two sets
  and both edges: **+0.174 px (single) → +0.130 (warped single) → +0.175 (member)**
  at a common fitted-amplitude cut. The FULL-population reading that suggested
  amplification (+0.176 → +0.162 → **+0.456**) is a DETECTION-DEPTH artefact — see
  the depth-mismatch entry under "QA / scope". Also killed in the same run:
  **drift span within a group** as the differentiator — one knob, 10 frames per
  arm, consecutive (21 px span) vs full-span (235 px): edge excess moves +0.053 px
  for aug06 and +0.042 for july31, i.e. an 11× span increase costs ~0.05 px
  *equally in both sessions*. The `framing=min` trim at matched group size is
  itself equal (aug06 234×80 px vs july31 232×88). What survives is small and
  frame-level: at the field edges the two sessions' FWHM is nearly equal
  (2.08–2.18 vs 2.10–2.16 px) and aug06's CENTRE is sharper (1.76 vs 1.83–2.06) —
  a centre advantage plus a right-edge roundness deficit (0.756/0.725 vs
  0.829/0.809). EXIF records no difference (f/4, 70 mm, 2.5 s, ISO 1600, manual
  focus, same body and lens), so the residual candidate is focus/field state,
  which no processing knob reaches.
- **In-exposure trailing is the unremovable FLOOR** — no registration method touches
  it. On a fixed tripod at 6 s / dec +47 / 18″px it is ~3.4 px predicted and ~3.6 px
  measured (per-frame roundness 0.615, uniform across the set). Stars are elongated
  ~1.6:1 at BEST; success is the EDGE matching the CENTRE, never round stars. That
  the per-frame roundness is *uniform* is also the proof the radial smear is
  introduced by register+stack, not by the frames.
  **Measure note — the floor's px numbers are not one statistic.** ~3.4 is a predicted
  trail LENGTH; the ~3.6 per-frame FWHM was CFA-sampled (Bayer-inflated, relative-only
  — removal-condition register); station values are debayered majFWHM medians
  (3.4–3.8 px at the perpendicular stations); `seqtilt`'s truncated mean mixes axes
  and reads 3.0–3.1 px on the same stacks. Compare within one statistic; the operative
  claim is edge ≈ centre, never an absolute px value across statistics.
- **A community lens profile can fix the edges yet WRITE A NEW DEFECT into the centre —
  the paraxial-error × drift band.** True distortion → 0 at the optical axis, so an
  UNCORRECTED wide-untracked stack has a pristine centre; a community radial profile
  carries a small paraxial error ε(r), and as a star crosses the axis during the drift the
  radial unit vector flips sign, turning ±ε into a ~2ε smear ALONG THE DRIFT — a band
  through frame centre, worst at the centre, invisible perpendicular. MEASURED (findstar at
  fixed 350 px stations about the geometric centre): full-depth centre majFWHM 5.30 /
  roundness 0.480 vs perpendicular 3.60–4.12 / up to 0.706; the no-model control INVERTS it
  (centre 4.03/0.556, its best). It is a FAINT-star/texture defect (a stretch shows it,
  bright-star medians hide it), and **`seqtilt` is BLIND to it — off-axis aberration even
  IMPROVES as the centre degrades toward the corners' mean**, so never accept a
  wide-untracked render on `seqtilt` alone; measure fixed drift-axis stations
  (`scripts/qa/star_stations.py`). A tracked rig never sees it (no drift). **The fix: a
  model fitted FROM THIS UNIT'S OWN FRAMES by between-frame star-correspondence
  (`fit_lens_model.sh` → `install_lens_model.sh`)** — removes the band (centre 5.30 → 3.67 px
  at full depth, every station at the perpendicular floor) and sharpens the whole frame
  (`seqtilt` truncated-mean 3.27 → 3.06 px). ε-source candidates (open, fix is the same):
  centre-pinned a/b/c absorbing the calibrator's decentering; focus-distance; unit variation.
  Also KILLED: the solved effective focal (67.8) as the lensfun key — the interpolated 50–70
  model is WORSE at the centre (5.42 vs 4.88 px); calibrated focal=70 is the best community key.
- **A darktable lens STYLE carries NOTHING but the enabled bit.** darktable IGNORES the
  `op_params` blob (method/flags/camera/lens/focal/aperture/scale), re-detects the lens from
  each image's EXIF, and applies its DEFAULT correction set (distortion + TCA + **vignetting**).
  Measured (uniform/grid card, Siril `stat`): EXIF focal 70 vs 24 → opposite-sign fields
  (+26→+69 px vs −6→−19 px); `scale` 1.046 vs 0 vs 1.5 → identical to 0.000 px; a BLANKED blob
  (or flags 0–7, method/inverse flips) → byte-identical output. So ONE style is
  camera/lens/focal-general, and the correction SET cannot be chosen in a style — enforce it
  in the DATA lensfun reads: strip `<vignetting>`/`<tca>` from the lens's DB block
  (`install_lens_model.sh`) so distortion is the only correction darktable CAN apply (the
  unwanted vignetting DOUBLE-corrects flat-corrected lights — corner/centre 1.27–1.37× linear,
  2.2–2.6× stretched). Verify after any darktable/lensfun bump with a uniform-card warp: corner
  medians must equal centre — **but the uniform card ALONE is a VACUOUS test.** Warping a
  uniform field yields the same uniform field, so corner==centre passes whether vignetting was
  stripped OR the module never fired at all (MEASURED on x86: the uniform card's `lensdist` vs
  `nodist` renders came back PIXEL-IDENTICAL, Siril `isub` → "all nil", while the module was
  demonstrably live). It needs a GRID positive control that MUST differ (grid card gave sigma
  45613–45620, max ~54000) to prove the module fires; only then does the uniform card's flat
  corner-vs-centre mean "no photometric correction".
  `scripts/darktable/verify_lens_card.py` runs both legs and fails if either fails. Do NOT
  compare the rendered files byte-wise — `cmp` reported those same pixel-identical renders as
  DIFFERING (TIFF metadata). This checks the correction SET, never its CORRECTNESS: a
  wrong-but-present distortion model passes both legs.
- **Round-tripping linear astro data through a raw converter: the ICC tag and the
  export profile must CANCEL — and "verified identity" is only as good as the
  LEVELS it was verified at.** Siril's `savetif` embeds **`sRGB-elle-V2-srgbtrc.icc`**
  — an sRGB TONE CURVE — on LINEAR pixels, and **`icc_assign sRGBlinear` does NOT
  change what `savetif` embeds** (the export profile comes from a save-time
  preference). A converter reading that TIFF applies an sRGB→linear DECODE to
  already-linear data; exporting LINEAR against the sRGB-tagged input leaves the
  decode UNCANCELLED — measured A_out/A_in climbing **0.1008 → 0.2121** (effective
  gamma ≈1.34), silently destroying photometry while looking fine on a preview.
  The 16-bit-era rule — MATCH the output profile to the input tag
  (`--icc-type SRGB`) — verified as identity **at star amplitudes on 6s-class
  data** (0.9996–1.0000)… and later measured to carry a **TRC toe-segment
  mismatch below linear ≈0.003**: +4.7% at 0.0015 → +2.2% at 0.0017 → identity
  by 0.003 (Siril's elle sRGB toe vs darktable's SRGB toe). A 6 s sky sits above
  the band; a **3 s sky sits inside it** → ~1–2% per-channel global shift on
  that whole class, invisible to a star-amplitude check. **The float-leg
  contract, adopted: strip the ICC tag (exiftool `-icc_profile:all=`, same pass
  as the lens-tag copy) and export `--icc-type LIN_REC709` — a PERFECT identity,
  ratio 1.0000 at EVERY level and channel, warp confirmed firing (corner 0.22 vs
  centre 0.003).** Two traps beside it: (1) NEVER strip with siril `icc_remove`
  before `savetif32` — the same leg then applies a global **~1/12.92** scale
  (the sRGB linear-segment slope) to every pixel; (2) verify any ICC change with
  a ratio-vs-level curve DOWN TO the exposure class's SKY level
  (`bisect/iccprobe` method), never with star amplitudes or a mean alone — a toe
  error hides above the knee.
- **Three traps that make a registration comparison lie (all hit one set).**
  (1) **Survivorship bias** — a bad registration spreads flux below the detection threshold,
  so the SURVIVING stars' median can *improve* while the image gets worse (the `-disto=` LOSS
  above showed a BETTER edge median, 4.61 vs 6.46 px, on a destroyed frame). Read a star-shape
  metric with its **n** and confirm on full-frame crops.
  (2) **Area confound** — `-framing=min` gives each variant a DIFFERENT frame size (less drift
  ⇒ larger intersection), so raw counts aren't comparable (a short-window stack's higher count
  was entirely its 56% larger frame; per Mpx it was LOWER). Compare **stars per Mpx**, and open
  the detection gate (`setfindstar -roundness=0.05 -relax=on`) when measuring elongation or the
  metric silently rejects the stars under test.
  (3) **Circular metric** — a radial profile binned about the `findstar` BOUNDING-BOX centre
  has an origin that MOVES with the defect (the smear suppresses edge detections → box shrinks
  → origin shifts; **537 px** measured from a detection-sigma change alone), after which it
  reads roundness *improving* outward on a stack whose right third has no detections. Never key
  a metric to a geometry derived from the measurement itself — use a FIXED external origin or
  the tool's own measure (`seqtilt`, no origin to get wrong, but WHOLE-FRAME and blind to a
  drift-aligned band; `tilt`/`inspector` are script-NO). Star count per radial bin is not a
  quality measure either — it is sky density × detection efficiency, which peaks where the sky
  is poorest.
- **A PRODUCT-LEVEL A/B cannot audit a transient's rejection — the dilution is
  the instrument's blind spot.** Differencing a full-depth stack against a
  control with the transient's frames excluded is the obvious test and it is
  UNDER-POWERED by construction: the groups route divides the transient's
  per-frame amplitude by the group size and then again by the compose's member
  count. MEASURED on july31/set-03's aircraft: a trail pixel carries ~766 ADU
  above a ~1140 ADU sky per frame, which after a 100-frame group mean and a
  5-member plain-mean compose is 1.5-4.1 ADU per trail pixel — 0.02-0.06 ADU
  once spread over a 400 px box, against that difference's own 0.2 ADU
  box-to-box spread. So a FLAT product difference is equally consistent with
  rejection and with no rejection, and reading it as a pass is the same error
  as any other blind instrument here. Audit rejection where it HAPPENS: Siril
  `stack ... -rejmaps` writes the per-pixel record of which samples were
  discarded, and differencing the map of the group WITH the transient against
  the same group WITHOUT it leaves the transient's own track and nothing else
  (its median equals the arithmetic scale step between the two frame counts,
  which calibrates the map for free). The on-track residual is then measured at
  GROUP level, where the signal is 5x larger and a 60 px box sees an unrejected
  trail at ~0.9 ADU against a +-0.2 ADU spread.
- Cloud culling is by per-pixel MAJORITY risk, not visibility: a moving minority
  band stacks clean through `rej 3 3`; a DWELLING band becomes the per-pixel
  majority and survives. `nstars` is a blind cloud discriminant on rich fields
  (detection saturates at the star cap — the background channel carries the cloud
  signal).
- wFWHM weighting at low FWHM spread is WORSE than none (Siril `-weight` is a
  min-max ramp → worst frame ~0 weight at any spread).
- Rejection and cosmetic correction CANNOT remove walking noise (drift-aligned
  streaks: sensor-fixed FPN dragged into lines by coherent un-dithered drift).
  The pattern is sub-sigma STRUCTURED signal, not discrete outlier pixels —
  measured NULL twice on a ~200-frame/half wide-untracked set: `-cc=dark`
  cosmetic correction, and GESD-vs-winsorized rejection (no visible or
  measured change either way). Size there: drift-phase structured term
  ≈0.34/0.48/0.42 ADU (R/G/B) per ~199-frame half vs ≈1.0/1.5/1.2 total
  static structure (`noise_split.sh`). Acquisition owns the fix (dither
  between subs); a denoiser is symptom budget only (BACKLOG:`walking-noise`).
- **Never compose PRE-CROPPED per-set stacks to deliver a frame beyond any
  member's crop** — a per-set `-framing=min` stack has already discarded its
  outer drift zones, so a compose of such members has holes exactly where only
  the discarded zones covered (measured: a 5-member compose of per-set full
  stacks left a zero-coverage staircase across the cov25 frame's right region
  that the 107-sub-stack compose covers at Min 84–88 ADU). Compose from the
  UN-cropped sub-stacks. Two mechanisms measured alongside: `register -2pass`'s
  auto-reference sets the output CANVAS ORIENTATION and (via `-norm=addscale`)
  the composite's raw channel balance — `setref <n>` AFTER the 2pass re-bases
  both (a set-02-referenced compose read K_B 0.846 = that set's own balance and
  a rotated frame map; set-03-family reference restored K_B 0.951 and an exact
  map); and a crop-coverage guard of `Min > 0` PASSES on lanczos edge-ringing
  residue (Min 7–26 on a ~90 sky) — require the SIBLING-CLASS SKY FLOOR
  (Min ≈ 80s here), never mere non-zero.
- **Never sigma-reject across SUB-STACK composes.** Sub-stacks are clean
  ~group-size means, so their mutual scatter is ~√group below per-frame noise —
  a 3σ gate at that tiny σ fires on the systematic differences sub-pixel
  registration leaves along steep gradients (star edges, MW lanes), not on
  outliers. Measured (`rej 3 3` across 25 fifteen-frame sub-stacks vs a plain
  mean of the same registered set): pixels rewritten by up to **±3800 ADU on a
  ~140 ADU sky**, star cores carved out, dark rip-like streaks through
  structured regions — while whole-frame `seqtilt` medians stayed FLAT (stars
  13,903 vs 13,784; FWHM 3.07 vs 3.10), so the damage is invisible to
  frame-wide statistics and shows on the stretched final. Reject within groups
  (full per-frame strength, where satellites die); compose sub-stacks with a
  PLAIN MEAN.
- Drizzle: "short focal / large pixels ⇒ oversampled" is BACKWARDS (that geometry
  gives large arcsec/px → *few* px per star → UNDER-sampled, drizzle's home turf).
  Judge sampling by measured **minor-axis FWHM**, not the "wide" label: ≥~2–3 px =
  oversampled (skip), <2 px = undersampled (2× drizzle *can* help IF real
  sub-pixel dither + many registered frames). Trailed data is oversampled only
  where *trailing/bloat* spreads the star; drizzle is pointless there because
  trailing breaks the dither/registration preconditions AND drizzle can't de-trail
  (it renders a sharper *smeared* star). CFA-drizzle 1×/pixfrac 1.0 is a separate
  OSC-only win (cleaner colour noise).
- CLASSICAL deconvolution (makepsf + RL) where trailing is in-exposure fails —
  unstable symmetric PSF on ≈0 background. (A LEARNED deconvolver is NOT classical RL
  and is a live x86 option, not a dead-end — tool choice + CPU costs in `TOOLS.md`.)

**Tool state / plumbing** (a persisted preference and a dropped header are both
SILENT — pin the state, never inherit it):
- **Siril `idiv` CLIPS AT 1.0, SILENTLY — so a ratio of two comparable images (the
  standard flat-vs-flat instrument) loses its whole upper tail with no warning.**
  The tell is a whole-frame `stat` printing **Max exactly 65535.0**. MEASURED on a
  ratio of two 250-frame sky flats: `idiv` reported Max 65535.0 and mean 63073.6,
  while the SAME division via `fdiv <B> 0.5` and `fdiv <B> 0.25` agreed exactly
  with each other after rescaling — true max **112156** (ratio 1.711 on the 65535
  scale) and mean 63115.4: idiv truncated everything above 1.0 and dragged the
  mean 0.066% with it. **Use `fdiv <B> <scalar>` with a scalar that keeps the
  result inside range** (0.5 suffices when the two images are comparable); the
  scalar is global and cancels out of any ratio-of-medians statistic.
  **What saves you depends entirely on WHERE the ratio sits.** When the bulk of
  the frame is below 1.0, regional MEDIANS survive a truncated tail (a within-set
  flat ratio at median 0.963 read corner spread 3.4817 clipped vs 3.4814
  unclipped, identical +0.0705 %/1000px slope). When the ratio straddles or
  exceeds 1.0 the medians go too, catastrophically — MEASURED on the five july31
  between-set flat ratios (corner spread at box 400 / margin 200, `idiv` against
  an unclipped `fdiv` leg): **−2.4, −0.7, −5.7, −3.3 and −9.1 percentage points**
  (flat01/flat04 reading 18.715 against a true 27.843 — **33% understated**), and
  flat03/flat04's `idiv` leg has a whole-frame MEDIAN of exactly 65535.0, i.e.
  over half the frame pinned at the clip. Never reason about whether the medians
  are safe — rebuild with `fdiv` and compare. Two scalars that agree after
  rescaling (0.25 vs 0.5) is the positive control that no truncation is moving
  them; a Max still at 65535.0 at BOTH scalars is a genuine divide-by-near-zero
  spike, not bulk clipping.
  **The corollary: RECORD THE SCALAR.**
  `datasets/july31/flat_gradient_measurement.json` states its instrument as
  "`idiv` of one flat by another"; its two surviving artifacts are reproduced
  exactly by `fdiv <B> 0.5` and are exactly 0.5000x a plain `idiv` of the same
  flats. An undocumented scalar is what kept that record's numbers off the clip,
  and anyone reproducing it AS WRITTEN would have understated every figure by up
  to 9.1 points. The measurement was right and the method line was wrong, which
  is the harder failure to catch.
- **Siril's FITS extension is a PERSISTED preference; every generated `.ssf`
  must pin `setext`.** `extension=` in `config.1.4.ini` decides what `convert`,
  `save` and `-out=` write, and a script that does not set it inherits whatever
  ran last — including another project's chain sharing the same rig. Measured
  against the repo's `.fit` globs with the setting on `.fits`:
  `build_master_dark.sh` reported *"siril exited clean but wrote no master"* on
  a master that had built **correctly**, and its `rm -f work/dark_*.fit` cleanup
  matched nothing, leaking **9.2 GB**; `build_sky_flat.sh` and
  `run_undistort_pipeline.sh` abort with *"calibrated nothing"*. Siril logs
  *"Script execution finished successfully"* throughout, so the cause reads as a
  data or Siril bug. Exactly the class `setcompress 0` is already pinned for.
  Bash `*.fit` does not match `*.fits` — an extension is not a glob prefix.
- **Calibration dirs are PLURAL — Siril's own convention** (`lights` / `flats` /
  `darks` / `biases`, never a singular). A singular staged dir (`dark/`) holds
  ≥8 raws, so the session chain and the web set-kind rule classified it as a
  **LIGHT set** and would carry the dark frames to frame QA, mount derivation
  and a full stack; both now list the singulars as calibration, and the
  builders still require the plural and stop loudly.

**QA / scope:**
- **A STAR-SHAPE MEDIAN COMPARED ACROSS IMAGES OF DIFFERENT DEPTH IS A DETECTION-DEPTH
  COMPARISON, NOT A QUALITY ONE — flux-match the population or the deeper image loses
  every time.** `findstar` goes as faint as the image allows, and marginal fits are
  inflated, so a deeper stack (or a darker sky at equal depth) drags its own median up.
  This is the MIRROR of the survivorship trap under "Detection / solve / registration"
  (there a *worse* image measured better because the smear suppressed detections; here a
  *deeper* image measures worse because it admits fits the shallow one never saw), and
  the two together mean **a raw `findstar` median is not comparable across levels of a
  chain at all**. MEASURED chasing the aug06 member edge deficit: at one 800 px box the
  aug06-vs-july31 member difference reads **+0.055 px on the 30 brightest, +0.081 at 60,
  +0.119 at 120, +0.180 at 250, +0.308 at 400 and +0.518 on the full detected
  population** — a factor of 9 across the same two files, driven by aug06 (moonless)
  detecting to fitted amplitude A≥0.00031 where july31 (moonlit) stops at A≥0.00060.
  The corresponding session difference in edge-minus-centre FWHM went from a flat
  +0.174/+0.130/+0.175 px across single → warped single → member (flux-matched) to a
  spurious +0.176/+0.162/+0.456 (full population), i.e. the artefact manufactured an
  apparent 2.6× amplification by the stacking stage that does not exist.
  **The fix, and it costs nothing:** apply ONE common fitted-amplitude threshold across
  every box and every arm being compared (pick it as the level at which the thinnest box
  still keeps ≥60 stars), or rank-match on the N brightest; report **n and the faintest
  admitted amplitude with every number**. Rank-matching across levels is legitimate
  because the same sky box holds the same physical stars in every image of it.
- The GATE must be a composition-agnostic STATISTICAL sky scope — whole-frame
  reads real MW/object signal as a defect, and a geometric sky mask can't fix it
  (a bright object has no fixed band). Hand-picked patches miss defects a
  whole-scope measurement catches (the lesson that created the gate).
- **A RATIFIED DECISION WHOSE JUSTIFICATION CITES A FRAME COUNT IS CONDITIONAL ON
  THE ROUTE THAT PRODUCES THAT COUNT — record the route with the ratification, or
  the decision silently means something else on another route.** A user decision
  is ratified against a MECHANISM, and a mechanism stated as a fraction ("a
  minority per-pixel sigma rejection removes", "1 frame in 500") carries a
  denominator that belongs to the pipeline, not to the sky. MEASURED instance:
  `BACKLOG:aircraft-rejection-retest` ratified KEEPING an 8-frame aircraft
  crossing on "any pixel carries it in ~1 frame of 500" — true single-pass. The
  groups route stacks CONSECUTIVE BLOCKS, so the same 8 frames land whole inside
  one group — 53% of a group of 15, a per-pixel MAJORITY, which this registry
  says survives — and the compose is a plain mean with no rejection. The
  identical ratified decision rejects the transient on one route and ships it on
  another. The class is wider than rejection: any acceptance argument of the
  form "X is a small fraction of N" is invalidated by any change that alters N —
  group size, a cull, a sub-stack compose, a frame-count-derived algorithm
  switch. When ratifying, write the ROUTE and the count the argument assumes;
  when changing a route, grep the ratified decisions for fractions before
  assuming they carry.
  **And grep the REVERTS, not just the keeps.** A revert is a ratified decision
  too, and this registry's most expensive one states itself as a fraction: the
  `--desky` entry's headline — corner spread 12.4% vs 0.4% — is qualified "500
  frames, one knob", i.e. measured on the single-pass denominator; nothing says
  what it measures on a 5x100 groups build. The rule is symmetric: a decision to
  STOP doing something inherits its route just as a decision to keep does.
- **THE REPO'S MOST PERSISTENT DEFECT: A CHECK THAT CANNOT FAIL — AND THE THING
  MEANT TO PROVE IT COULD FAIL IS USUALLY DEFECTIVE TOO. VERIFY BY EXECUTING:
  break the mechanism, watch the assertion go RED, restore.** Reasoning about a
  fixture's construction is not verification; it has failed three times in a
  row, each time for a different reason, each time looking green:
  1. `grep -oE 'Found [0-9]+ star' … || echo 0` — the regex never matched Siril
     1.4.4's actual wording, so the fallback supplied 0 unconditionally.
  2. The uniform lens card — warping a uniform field yields a uniform field, so
     corner==centre passes whether vignetting was stripped OR the module never
     fired; needed a GRID positive control that MUST differ.
  3. `lens_preflight.check_pinned_model`'s mutation test, TWICE — a counted-less
     `str.replace` moved the live element AND the decoy together (a mutation
     that changes every copy cannot distinguish "reads the right copy" from
     "reads any copy"), and its replacement's decoy was written `focal=70` where
     the scanner requires `focal="70"`, so the fixture contained no decoy at all
     and passed with masking disabled.
  The common shape is not "bad metric": **the falsification step was argued
  rather than run.** The executable form, shipped in
  `lens_preflight.py --selftest`: neutralise the mechanism in-process (which is
  why `live()` is module-level and not a closure), assert the incident
  REPRODUCES, restore, assert it is caught again. A test that cannot be made to
  fail on demand is decoration. Corollary for a fixture with a decoy: assert the
  decoy MATCHES the scanner's own pattern before trusting any result built on it
  (measured: 2 pattern matches in the raw block, 1 after masking).
- **A RUNNING BASH SCRIPT IS A LIVE FILE, NOT A SNAPSHOT — never edit one that
  has an invocation in flight.** bash reads a script lazily and remembers a BYTE
  OFFSET, so inserting lines ABOVE the current execution point makes it resume
  mid-token and execute garbage. The recovery shape: kill the shells whose
  offsets are invalidated, LEAVE any child builder running (a separate process
  with its own unmodified file), and re-enter the chain from a clean read once
  it lands — built products skip, so the cost is zero. Check
  `pgrep -f <script>` before editing anything the chain drives.
- **A LOG-MESSAGE REGEX IS NOT A MEASUREMENT INTERFACE — parse the tool's
  structured output, and prove the tool RAN.** A validation gate read
  `grep -oE 'Found [0-9]+ star' … || echo 0` off Siril's `findstar` log; Siril
  1.4.4 actually prints **"Found N Gaussian profile stars in image"** — the
  profile word sits between the count and "stars" — so the regex never matched
  and the fallback supplied a 0 **unconditionally**. A gate that cannot fail,
  and two flat records plus a ledger entry carried a speck count that was never
  measured. (Re-measured from the tool's own `-out=` list: 0–1 specks on every
  july23 flat, de-skied and control alike — the conclusion had been right by
  luck.) The wording is also version- AND parameter-dependent (the profile word
  changes with `setfindstar -profile=`), so it was never a stable interface.
  **Three `findstar` behaviours a replacement must respect** (probed on-rig,
  1.4.4): (1) with zero stars it writes **NO list file at all** — which is a
  flat's IDEAL result, so a missing list must read as 0, never as an error;
  (2) it still exits **0** in that case, so `set -e` on the run is a valid
  failure check but tells you nothing about the count; (3) its
  `Candidates for stars: N` line IS printed whether or not any candidate
  survives the PSF gate, so that line — not the count — is the positive control
  proving the measurement happened. Unrelated landmine found in the same probe:
  **`setfindstar -reset` returns exit 1** on success in 1.4.4, so an `.ssf`
  ending in it fails a `set -e` caller for no reason.
- **A NUMBER READ OFF A LOADED BOX IS NOT A MEASUREMENT — record the load with
  the reading, for EVERY tool, not just the slow neural ones.** MEASURED:
  `verify_lens_card.py`'s grid positive control read Siril sigma **14666**
  while 500 concurrent darktable warps were running, and **45398.0** on three
  independent idle runs — a 3x error on identical inputs, identical optics and
  an identical pinned model. This is an instrument fact, not a tool fact (first
  hit reading a Cosmic Clarity probe while an unrelated job held the box at
  load average 300 — ~30 min of CPU and a registry entry that had to be
  retracted). Check `uptime` before quoting any number, and put the load in the
  record.
  **SCOPE, because the obvious inference is wrong:** this does NOT mean the
  pipeline's own output moves with load. The production undistort warp was
  bracketed deliberately — the exact `run_undistort_pipeline.sh` invocation on
  one real calibrated frame, three arms at 1-min loadavg 25.06 / 28.22 / 26.12,
  compared with Siril `isub`+`stat` — and every pair is **all nil,
  bit-identical**
  (`datasets/july31/set-01/qa_work/warp_load_determinism.json`). The
  deliverable is deterministic; it is the FIXTURE reading that moved.
  Distinguish the two before concluding a route is unreproducible, and note
  that the anomaly's own leg (a synthetic 16-bit card at `--icc-type SRGB`) is
  still unexplained.
- **A stack-level A/B on this chain cannot resolve anything below its run-to-run
  floor — and the chain is NOT pixel-reproducible.** MEASURED (identical frames,
  identical recipe, two runs of the undistort chain, identical output geometry):
  the two products differ by **2.06% of sky at star edges and 0.073% in flat
  sky**, the difference tracking local gradient (star-edge/flat-sky ratio
  **28.4×**) exactly as resampling error does — it is interpolation variance in
  registration, not the knob under test. Cost of not knowing this: a
  calibration A/B whose whole-frame difference read "√2 × the per-arm noise",
  which looks like a large real effect and is entirely the floor. **Bracket a
  stack-level experiment with a SAME-ARM REPEAT RUN, not just an A/B**, and
  treat any claimed effect under ~0.07% flat-sky / ~2% star-edge as unmeasured.
  Corollary: measure a calibration change where it is unambiguous (on the
  MASTER) rather than where it is swamped (on the finished stack).
- **The stretched judge surface AMPLIFIES background gradients, by a factor that
  grows with sky brightness and with stack depth — so a flat image can render as
  a visibly tinted, vignetted one.** Siril's autostretch puts its black point at
  ≈ median − 2.8·MAD, so the amplification of a fractional background variation
  goes as sky/noise ∝ √(sky × N): a BRIGHTER sky or a DEEPER stack pushes the
  black point proportionally closer to the sky level and steepens the transfer
  at the floor. MEASURED on one set: linear corner-to-corner spread 0.47% in
  level and 0.53% in R/G rendering as **7.9% and 9.4%** — a ~17× gain, with the
  left edge reading a visible 6% green where the linear data is 1.0034. The same
  chain on a 4×-darker sky amplified 8.7× (predicted ratio √4 = 2.0, measured
  1.95). Consequences: a corner "going black" on a judge PNG may be ~23% grey
  and ±0.3% flat in the data; and stacking DEEPER makes the artefact worse, not
  better, unless the members' residual gradients are uncorrelated enough to
  cancel (measured: per-set L-R residuals alternating in sign, mean 1.0005 vs
  individual 0.36%). Judge background uniformity from LINEAR regional numbers,
  never from the stretched surface.
  **The same 1/f amplification applies to CHANNEL differences, not just spatial
  ones — so a COMMON black point renders a neutral sky as a tinted one.** Write
  the black point as f below the sky (autostretch's 2.8·MAD, or an explicit
  k·MAD); then any per-channel fractional sky difference is magnified by ≈1/f,
  because the render's sky is (sky_c − lo)/(hi − lo) and lo is close to sky.
  MEASURED on a starless+denoised layer whose linear sky was B/G **1.0048**
  (0.48%): a common black point renders B/G **1.1147** at f=0.0527 (19×) and
  **1.0596** at f=0.1391 (7.2×) — an 11% or 6% visible background tint out of
  half a percent. Setting lo PER CHANNEL at the same fraction below each
  channel's own sky (i.e. background neutralization, the step the mainstream
  puts before colour calibration) while keeping ONE common window width and
  midtone renders **1.0057**, +0.09% from the truth; the "use linked" rule
  governs the CURVE and is satisfied by the common width/midtone. Scaling the
  width per channel too forces the sky to exactly 1.0000 — which discards the
  colour SPCC measured rather than rendering it. Corollary for any
  deep-black-point render: a SHALLOWER black point is not free — it preserves
  faint signal but raises this amplification as 1/f, so black-point depth
  trades faint-signal crush against background colour fidelity, and the trade
  has to be made against the numbers, not by feel.
  **Never read a LINEAR residual off a STRETCHED surface at all.** An
  autostretch places the sky low on a steep curve, so it can compress or
  amplify a background ratio by several× depending on where the background
  lands — the same class of gradient read "corner/centre 1.06" on an
  autostretched preview and **1.27–1.37 linear** on the shipped stack (2.2–2.6
  in its stretched judge PNGs). A display-domain ratio answers "what does the
  eye see", never "how big is the residual": measure gradients with Siril
  `stat` regional medians on the LINEAR image, and state the domain with the
  number. (Same trap in reverse: a pedestal-included ADU ratio understates a
  light-domain falloff — a ~1 EV vignetting read "6.3%" with the ~1007 ADU
  pedestal in.)
- **THE STACK ROUTE'S COMPOSE STAGE IS BIT-REPRODUCIBLE — the "register sweep is
  non-deterministic" exemption does not cover it.** MEASURED, two sets: july31
  set-01 and set-02 each recomposed from their own UNCHANGED sub-stacks
  (`register s -2pass` → `seqapplyreg -framing=min` → `stack mean none`) and
  differenced against the original with Siril `isub` — **all three channels nil,
  both times**. SCOPE: n=2, same-arm, one rig, siril 1.4.4, and the COMPOSE
  sweep only (5 members). A compose-level A/B may therefore be judged on BYTES,
  and a same-arm compose repeat is a real zero rather than a tolerance.
  **EXTENDED — the WHOLE GROUPS ROUTE is bit-reproducible, not just the compose,
  so a full rebuild has a repeat floor of ZERO.** july31/set-01 rebuilt TWICE
  from the same 500 culled raws through the entire chain (calibrate → darktable
  warp → per-group `register -2pass` → GESD stack → compose) at `--group=100`,
  and both differenced against the ARCHIVED product: **all six pairwise
  directions all-nil, all three channels**. So the rebuild-repeat floor the
  route claims were gated on is 0.00 px, and the three commits that landed
  between the archived build and the rebuilds are MEASURED pixel-neutral rather
  than assumed so.
  **Two controls that make this a result instead of a check that cannot fail**,
  both required because Siril reports an all-zero difference as a FAILURE string
  (*"Statistics computation failed for channel N (all nil?)"*): (1) the guard
  was BROKEN on purpose — `(x1.01) − x` prints Red/Green/Blue mean 0.3/2.1/1.5,
  so the nil is a measured zero; (2) every pair was differenced in BOTH
  directions, since a one-way nil would only prove A ≤ B if `isub` clipped — and
  a `(x0.99) − x` probe showed it does NOT clip (means −0.3/−2.1/−1.5, minima
  −589.3/−655.3/−567.2).
  **SCOPE, and it is narrower than "the chain is deterministic":** the groups
  route never runs a 500-frame sweep. It runs five INDEPENDENT 100-frame
  `register -2pass` sweeps plus the 5-member compose. So per-frame registration
  is measured deterministic at **n=100** (×5 groups, ×2 arms) and the compose at
  n=5; the SINGLE-PASS 500-frame sweep is still a different problem size and
  still unmeasured, so the README exemption survives exactly where it was
  written and nowhere wider. Numbers: `datasets/july31/experiments.jsonl`,
  `rebuild_repeat_floor_set01`. **A dry-run surface that stops short of the
  guards that can refuse the run is the wrong half of a dry run** — `--plan` now
  exercises the resume guard and the dwell floor and exits.
- **Do NOT assume "neural / ONNX / multi-threaded" means non-reproducible — MEASURE
  it. On this rig the whole render tier is BIT-IDENTICAL run to run.** Two
  identical runs of each stage, compared with Siril `isub` (all-nil =
  bit-identical): StarNet2 via siril `starnet -stretch` — identical, and
  identical AGAIN across thread counts (default 28 vs `setcpu 1`, and
  cross-compared); Cosmic Clarity denoise (`--disable_gpu`, separate mode) —
  identical, and identical across thread counts too (28 vs `OMP_NUM_THREADS=1`),
  so the determinism is not an artifact of one machine state; Siril's stretch +
  `asinh -human` + `pm` recombine — identical. So byte-identity IS the available
  bar here and a re-render reproduces exactly. Neither binary even exposes a
  thread/seed/device flag to pin (StarNet2's CLI is I/O + weights + stride +
  upsample only), so the reproducibility came free rather than from pinning.
- **The trap that replaced: a "run-to-run floor" derived from two runs whose
  inputs were never recorded.** A 1.34% colour floor was taken from two render
  records read as a same-arm repeat and hardcoded into a verdict that then
  called anything below 1.34% "unmeasurable" — but the old record logged NEITHER
  its linear source NOR its knob provenance, so nothing in it established that
  the two runs shared inputs and knobs; once every stage measured deterministic,
  two identical runs could not have produced different ratios, so something
  unrecorded differed. **A floor is a MEASUREMENT, not a subtraction of two
  numbers you happen to have** — bracket it deliberately with both arms'
  provenance recorded, or you build a threshold that hides real effects. The
  cost here was a verdict permissive enough to call a real 1% colour shift
  noise. (The stack-level floor in this registry — 2.06% at star edges, 0.073%
  in flat sky — is real, but it measures INTERPOLATION variance between
  separately REGISTERED stacks; it does not apply to two renders of one stack.)
- Never judge a denoiser by whole-frame `bgnoise`: the estimator conflates
  revealed texture with noise, so a real denoise can RAISE it (measured on one
  1024² tile: Siril `denoise` 2.05→2.55 while GraXpert denoise read 1.14 on
  the same input). Judge denoise on a decomposition instrument (the
  `noise_split.sh` structured term must SHRINK while confusion texture — real
  sky — stays) + the user's eyes on the unresolved starlight at 1:1.
- Never hide a rim defect with a darker sky target or a crop — the rim is in the
  data (estimator extrapolation × stretch amplification), fix it there.
- **Never export a numpy/FITS-row-order pixel box to Siril `crop` unverified** —
  Siril's crop y-origin is the OPPOSITE end (y_siril = H − y_np − h), so an
  unverified export ships a vertically mirrored window. Measured: a
  coverage-validated box (map Min = 25 sub-stacks everywhere in numpy coords)
  statted **Min 0** after export — a zero-coverage wedge shipped in a render.
  The guard is tool-sourced and cheap: crop the instrument MAP with the exact
  same args and require Siril `stat` to reproduce the claimed bound before any
  product crop.
- **A multi-product judgment set rendered by data-dependent `autostretch` is NOT
  like-encoded — each surface gets its own histogram-derived transfer** (and
  unlike encodings lie in general: q92+4:2:0 loses star-edge chroma to
  subsampling). MEASURED (five surfaces from one chain): statistically identical
  linear stacks rendered as "rich MW field" vs "single-frame-looking flat gray"
  purely by the per-stack transfer. The trap bites comparisons too: a fixed-MTF
  probe against an autostretched PNG "refutes" correct hypotheses until re-run
  like-for-like. Multi-surface judgment sets pin ONE stretch RULE for every
  member — and the rule must be SKY-ANCHORED per product, not one raw MTF
  triplet: separately output-normalized stacks put their sky at different
  normalized levels, so a single triplet renders honest sky-level differences as
  gross brightness differences (measured: the brightest-sky set washed out under
  a combine-derived triplet). With healthy 32-bit statistics, per-product
  `autostretch -linked` at identical parameters IS the pinned rule (its 16-bit
  failure was the MAD collapse, not the rule); the render tier's stretch policy
  is the durable home.
- **NEVER measure a faint BROAD halo with region MEDIANS — the median is robust
  against exactly the wide low tail under test.** MEASURED cost (july23 Deneb
  disc): a median-based two-point control read the halo "identical before vs
  inside the haze window" and a mechanism was mis-attributed on it; the
  MEAN-based 9-timepoint timeline over the same data shows the halo GROWING
  all night — G-channel star-box-minus-flanks 6.25 → 7.6 → 7.7 → 8.5 → 10.3 ADU
  (sets 01–03) and 7.1 → 9.9 → 12.0 WITHIN set-04 (+91% session-wide,
  accelerating late), alongside a monotonic FWHM rise 2.627 → 2.72 px and the
  terminal nstars crash (−13–16%, last ~20 min). Two lessons: (1) means (or
  outer-annulus statistics) for broad-glow photometry, medians only for
  compact-source-robust background; (2) a two-point control CANNOT test a
  monotonic-growth hypothesis — sample the full span. The growth pattern +
  conditions make DEW ON THE LENS the leading attribution (user field call;
  the full investigation record is in git history — the july23 session is
  archived); the per-set
  flat-cancellation variance on the FINAL stacks (Deneb-box excess 0/0/0 →
  +2.5/+5.8/+10 ADU across sets 01→04) remains measured and stands — a
  lights-built flat both bakes in and partially cancels a time-varying glow,
  inconsistently per set.

- **PER-SET LENS-DISTORTION MODELS — REFUTED AT THE ROOT, REVERTED.** The
  doctrine ("the lens model keys on the OPTICAL STATE, per set; focus
  recalibrates every session") was generalised from ONE number: aug06/set-01
  measuring 0.82 px off-axis under the pinned model against a 0.16–0.62 px
  family, read as "the field-dependent signature of a state change". **It is not
  a state change.** MEASURED on the preserved sub-stacks: every one of set-01's
  five 100-frame groups reads **0.40 / 0.42 / 0.44 / 0.43 / 0.45** px under that
  same pinned model — indistinguishable from set-02's groups (0.45–0.46) and
  *better* on truncated-mean FWHM (2.74–2.79 vs 2.82–2.84). The 0.82 exists only
  in the 500-frame product, i.e. it is created at the group→set compose. Set-02
  is the built-in depth control: same 100→500 increase, +0.11 where set-01 gets
  +0.39. The chronology said so first — 0.48 → **0.82** → 0.57 → 0.60 across
  strictly sequential, frame-contiguous sets, and a focus change is a STEP, not a
  spike that returns.
  The adoption A/B then read **1 WIN / 3 NULL** (set-00 0.48→0.46, set-02
  0.57→0.60, set-03 0.60→0.62) and gave all four sets their own model, including
  the three that measured no benefit. That heterogeneity is what broke the
  combine: 2.99 px corner disagreement within a night, 5.34 px across nights,
  visible star doubling the owner failed by eye — against 0.93 px / 0.71 px for
  the same member pairs under one model, and 0.14–0.35 px for same-night members.
  Compounding it: a fitted model is not reproducible to better than ~3 px in the
  outer field (four fits of ONE set span 0.36–6.30 px against a 4.01–10.99 px
  between-set spread — the distributions OVERLAP), so the coefficient differences
  never discriminated a state from a fit, and the 0.47 px equivalence bound used
  to adopt per-set granularity is exceeded 7–23× by refits of a single set.
  **What is NOT dead: fitting a model from a set's own frames.** That is how the
  shipped july14 model was made, and it beat the community profile at full depth
  (centre station 5.30 → 3.67 px, all-station spread 1.70 → 0.52) on the owner's
  eyes. What died is treating each SET as its own optical state by default, and
  making a per-set record the install authority. The authority is
  `scripts/darktable/lens_models.json`, keyed `<lens>@<focal>`; a fresh fit is a
  CANDIDATE promoted by an explicit act, judged at the COMBINE — never on a
  per-set product, where a compose artifact masquerades as optics.

- **NEVER compose sub-stacks that were warped under DIFFERENT distortion
  models.** A lens model is a per-set property only until the members meet;
  from the compose's point of view the model is a property of the COMBINE, and
  members rectified by different models cannot be brought into agreement by the
  registration, because a global homography cannot absorb a radial field.
  MEASURED (aug06, one knob, byte-identical group membership — the 13 `g*.list`
  files diff IDENTICAL between the two arms — and the same two pointings, only
  the installed model differing): the px separation of the SAME star as two
  registered members place it, at the composed canvas corner, is **2.99 px
  under the sets' own per-set models and 0.93 px under one shared model**.
  Same-set pairs sit at 0.1–0.2 px, so neither the compose code nor Siril's
  registration is implicated. By eye at 1:1 the own-model union's corner shows
  stars drawn into multi-component dashes over brushed fabric; the single-model
  union's SAME corner, same framing, same members, shows round single stars.
  The cause is structural, not a bad fit: **lensfun normalises the ptlens radius
  by HALF THE SHORT SIDE** — MEASURED by probe (seeded star-field fixture at
  sensor geometry through the production warp; fitting all four installed models
  at once gives RMS 4.47 px for half-short-side, 18.3 px for half-long-side,
  22.2 px for half-diagonal; a free normalisation lands at 2000 px against
  2020) — so the frame CORNER sits at ρ = 1.80 while hugin's control points
  constrain the fit only to ρ ≤ 1.0. The cubic extrapolates 80% past its
  support exactly at the corners, and fits that are interchangeable inside the
  supported field diverge freely outside it: measured model-pair divergence
  through the production warp reaches **8.2 px** (s02-vs-s03), 6.2 px
  (s01-vs-s03), 6.3 px (s02-vs-pinned).
  Corollary for the fitting instrument: a fit's own residual (0.02–0.10 px) is
  computed only where control points exist and says NOTHING about the corners.

- **THE FRAME COUNTER WRAPS AT 9999 -> 0001, AND FILENAME SORT IS THEN THE WRONG
  ORDER — groups are consecutive TIME blocks.** Measured on aug09/set-02: 456
  frames, ONE continuous 22.8-minute run at a uniform 3.00 s cadence (epoch
  deltas min 3.0, max 3.0 — no gap anywhere), wrapping DSC_9999 -> DSC_0001.
  | order | sequence |
  |---|---|
  | by NAME | DSC_0001 … DSC_0264 , DSC_9808 … DSC_9999 |
  | by TIME | DSC_9808 … DSC_9999 , DSC_0001 … DSC_0264 |
  **0 of 456 frames occupy the same position under the two orderings.** The
  groups builder sliced `find | sort`, so the first group would have been the
  LAST 100 frames shot and one group would have straddled the wrap — joining
  frames ~20 minutes and ~6 deg of sky apart into a single sub-stack whose
  pointing is the average of two ends of the drift. Nothing downstream could see
  it: the member simply registers and stacks worse, with the cause invisible in
  the product.
  IT IS NOT A RE-AIM, and it is worth saying because the symptom looks like one:
  `segment_runs` reports such a set as TWO capture runs, because it treats a
  frame-number discontinuity as a boundary. That is what made `mount_probe.sh`
  confine its windows to 264 of 456 frames here. The probe still read a decisive
  fixed signature (15.076 deg/hr against sidereal 15.041), so that is a NARROWED
  BASELINE rather than a wrong answer — but a set whose two runs are really one
  should not be split, and any future consumer of `segment_runs` needs to know
  a wrap looks like a boundary to it.
  FIX: `scripts/lib/frame_order.py` orders by EXIF epoch and is wired into
  `run_undistort_groups.sh`; it reads paths from STDIN rather than argv, because
  a 500-path list through `xargs` can be split at ARG_MAX into chunks that would
  each be ordered independently — reintroducing the bug in a subtler form. It
  warns loudly whenever capture order and filename order differ, and falls back
  to the given order with a warning when epochs are unreadable.
  BLAST RADIUS, measured across the corpus: 12 of 13 sets have name order ==
  time order exactly. Only aug09/set-02 differs, and it differs completely.
  **THE SECOND EDGE — FILENAMES ARE REUSED AFTER THE WRAP.** The counter cycles
  every 10,000 frames and this corpus is already **6,938 frames into that
  cycle** (6,938 distinct basenames across 6,938 frames — zero collisions
  TODAY). The next wrap reuses names this corpus already holds: aug09/set-02
  owns DSC_0001–DSC_0264, and a future night crossing 9999 will produce those
  names again. So **a frame's identity is (session, set, basename); the basename
  alone is not a key** and must never be used as one across units. Checked
  today: `cullspec.py` matches filename digits WITHIN one set (unique there, and
  it already ABORTs loudly on an ambiguous exclude), `frame_order.py` maps names
  per-set, and the ingest manifests are per-unit — nothing currently pools raw
  frames across units by name. This is recorded because it is guaranteed to
  arrive, not because it has bitten yet.

- **SIRIL `update_key` SILENTLY TRUNCATES A STRING VALUE AT THE FIRST `/` — it
  begins the FITS comment field.** Probed directly on a 16x16 test FITS through
  siril 1.4.4:
  | written | stored |
  |---|---|
  | `update_key K1 "aug06/set-01"` | `'aug06'` |
  | `update_key K3 "aug06/set-01,july31/set-01"` | `'aug06'` |
  | `update_key K2 "a,b"` | `'a,b'` (commas are fine) |
  | `update_key K4 "aug06_set-01+july31_set-01"` | intact |
  | `update_key K5 T` | `True` (a FITS boolean, not the string) |
  No error, no warning, exit 0. **CALSET is `<session>/<set>` by construction**,
  so every provenance stamp routed through siril loses the set and claims the
  whole session — and the stamp is the thing a compose gate reads to decide
  whether members are compatible. The existing corpus escaped only by accident:
  `backfill_substack_provenance.sh` wrote its keys with astropy `fits.setval`,
  which is why the backfilled `CALSET = july31/set-01` values kept their slash
  while a live build would not have. It would have corrupted the first rebuild.
  FIX, and it follows the repo's own precedent: provenance keys are applied with
  a FITS library (`header_apply_keys`, headers only, no pixel access) while the
  acquisition keys stay on siril's `update_key`, which is siril's own data and
  slash-free. Anything with a path, a date-with-slashes or a ratio in it must not
  go through `update_key`.

- **A JUDGMENT SURFACE IS NOT `load` + `autostretch` + `savepng` — IT IS
  `finish_render.sh`, AND SKIPPING SPCC DOES NOT "REMOVE A VARIABLE", IT BREAKS
  THE RENDER.** Measured: two union surfaces rendered with `autostretch -linked
  -2.8 0.25` on the raw stacks came out with channel medians **R 0, G 193,
  B 127** over covered pixels — the shadow clip on uncalibrated OSC data crushed
  the RED CHANNEL TO ZERO. Not a green cast: a dead channel. Through
  `scripts/stack/finish_render.sh` (solve → SPCC → linked stretch → full-frame
  16-bit PNG) the same two stacks read **R 70 / G 70 / B 69** and **69 / 69 /
  68**, K factors R 1.000 G 0.688 B 0.881 and R 1.000 G 0.666 B 0.859.
  The reasoning that produced the broken pair — "SPCC adds a variable to an A/B,
  so leave it out" — is backwards: in a comparison the variable is controlled by
  applying the SAME finish to both arms, never by deleting a stage from both.
  Every surface in `web/results/<session>/judge/` is `*_spcc-linked.png` for this
  reason, and the naming is the tell.
  SECOND HALF OF THE TRAP, and it is the one that let it reach the user: bit
  depth and dimensions were verified and the images were never OPENED. `file`
  said "16-bit/color RGB, 8659 x 6009" and that was taken as the check. Look at
  the pixels before calling anything a judgment surface.

- **NO INSTALLED TOOL CAN CORRECT A FIELD-VARIABLE ANISOTROPIC PSF — and a GLOBAL
  PSF cannot close a field gradient at all.** Three arms on one raw frame, every
  arm measured with identical Siril `findstar` settings (baseline whole-frame
  FWHM major 2.340 px, roundness 0.807, 7083 detections; roundness gradient
  across x −0.099).
  **Cosmic Clarity** (Stellar Only, Auto Detect PSF ON, amount 0.50, 704 chunks):
  2.310 / 0.802 / 6913, gradient **−0.093**. NULL, and ARCHITECTURAL rather than
  tuning — its own help says `--auto_detect_psf` measures the PSF per chunk and
  chooses "the two nearest **radius** models", and its models are named
  `radius_1/2/4/8`. Radius is a scalar; there is no ratio or angle in its
  interface, so an oriented elongation has no representation. The field-variable
  path was exercised and still could not express the defect.
  **Siril `rl` global** (`-mul -iters=10`): a genuine 10% FWHM gain rank-matched
  on the brightest 1500 (2.260 → 2.035) — but gradient **−0.091**, roundness
  slightly WORSE, and 77% of detections destroyed. Not tuning: one PSF over the
  whole frame sharpens everywhere by the same factor and leaves a field
  variation where it was.
  **`makepsf stars` is the POSITIVE result**: per 1500 px band its kernel ratio
  reads 0.863 / 0.851 / 0.816 / 0.804 / 0.758 against findstar's 0.832 / 0.836 /
  0.805 / 0.790 / 0.733 — gradient −0.105 against −0.099, FWHM tracking band for
  band. Siril CAN measure the anisotropy; it just applies one PSF per image.
  What remains with installed tools is Siril's PSF per REGION — tiling and
  reassembly, i.e. pixel surgery on the deliverable. The prior blocker is SNR,
  not seams: `-tv`/`-fh` regularisation with `-alpha=` is unbracketed, and if
  regularised RL still eats the faint population, per-region RL will too.

- **`findstar` SETTINGS ARE DUAL-PURPOSE AND THE TWO PURPOSES WANT OPPOSITE
  VALUES.** MEASURING a shape distribution needs the roundness floor DROPPED —
  the default 0.50 truncates exactly the elongated tail under study and biases
  the bad side rounder. BUILDING a PSF for deconvolution needs the DEFAULTS —
  relaxed settings let junk into the average. Measured on the same frame with
  the same `makepsf stars` call: relaxed detection returned kernels of 6.7 px
  major / 0.42 ratio, uncorrelated with anything and not monotone across the
  field; default detection returned 2.0–2.7 px / 0.76–0.86, tracking findstar
  band for band. The garbage was caught only by RENDERING the kernel and seeing
  it was not credible — a fitted number alone would have shipped it.
  Two smaller tool facts from the same probe: **`rl` with no arguments is a
  NO-OP** on this data (default gradient descent, step 0.0005, 10 iterations —
  FWHM, roundness and detection count unchanged to 3 decimals; use `-mul`), and
  **`seqfindstar` writes no star lists headless on 1.4.4** (reports "Sequence
  processing succeeded" in ~1.5 ms; use per-image `findstar -out=`).

- **THE ONE-SIDED STAR-SHAPE GRADIENT IS A RADIAL FIELD ABERRATION IN THE OPTICS —
  stop looking for it in the chain.** Measured on single Siril-debayered RAWs (no
  dark, flat, warp, registration or stack), 3 frames x 6 sets x 2 nights, 136k
  stars from Siril `findstar`. Four candidates ELIMINATED, each by measurement:
  a DETECTION/BRIGHTNESS artefact (the gradient survives inside amplitude
  quartiles in 6/6 sets although median brightness varies 2–10x across x); PURE
  DEFOCUS / tilted focal plane (that inflates BOTH axes on the soft side — the
  MINOR axis measures symmetric left-vs-right, 2.08 against 2.00 px, while the
  major does not, 2.46 against 2.63); RESIDUAL MOTION (in-exposure trailing holds
  ONE fixed sensor direction — the major-axis angle instead tracks the field
  azimuth in 7 of 8 zones in every set, resultant 0.45–0.85 at the edges);
  RESIDUAL DISTORTION (the geometry fits a centred ptlens model to a 0.27 px
  median — entry below). What is left is radial elongation growing with field
  radius at an asymmetric amplitude: coma with a decentred aberration field.
  **Consistent with the centred distortion** — distortion and coma respond
  differently to a decentred or tilted element, so well-centred distortion and an
  off-centre aberration field coexist without contradiction.
  TRAP for anyone re-measuring this: `setfindstar`'s DEFAULT roundness floor is
  **0.50**, which truncates exactly the elongated tail being measured and biases
  the bad side rounder. Drop it to 0.05. Second trap: `seqfindstar` reports
  "Sequence processing succeeded" in ~1.5 ms and writes NO star lists headless on
  1.4.4 — use per-image `findstar -out=`.

- **FITTING A LENS MODEL AGAINST A PLATE SOLUTION WITH AN AFFINE NUISANCE
  MANUFACTURES A DECENTRING SIGNAL. Use a HOMOGRAPHY.** The linear WCS is a
  gnomonic (TAN) projection about ITS tangent point and rotation; the ideal
  camera frame a lens model lives in is a gnomonic projection about the optical
  axis. Two gnomonic projections of the same sky differ by a plane projective
  transform EXACTLY — the same Szeliski result this repo already records for
  registration. Over ±14° the projective part reaches ~180 px, so an affine
  nuisance cannot absorb it, and what it leaves behind is **quadratic and EVEN
  in x** — indistinguishable by eye from decentring, and partly absorbable by
  Brown's tangential pair (`p2(r²+2u²)` is the same even quadratic).
  MEASURED, same 970 catalogue-matched pairs across 6 frames, 2 nights, 6
  pointings, one knob — the nuisance transform:
  | nuisance | ptlens RMS | median | free centre it "finds" | Brown peak |
  |---|---|---|---|---|
  | affine (6 DOF) | 14.24 px | 7.63 px | **(+210, −164) px** | ~59 px |
  | homography (8 DOF) | 3.19 px | **0.27 px** | **(−6, +14) px** | **2.89 px** |
  The median improves **28×** and the "decentring" collapses by a factor of ~20
  to consistent with zero. Adding a free centre to the homography fit changes
  the median 0.272 → 0.212 px and the RMS not at all; adding Brown's p1,p2 gives
  0.217 px. **A centred ptlens model already describes this lens to a 0.27 px
  median.** RETRACTS the earlier reading of this same data (8.35/6.71/8.54 px
  "irreducible" residual, a reproducible ~180–240 px centre offset, an even-in-x
  term "no radial model can produce") — every one of those was the unabsorbed
  projective term, and it reproduced across frames precisely because every
  frame's linear WCS has a similar tangent-point offset. Reproducibility across
  frames does NOT distinguish a lens property from a projection artefact.
  Do not re-derive a lens model against a plate solution without a projective
  nuisance, and do not read an even-in-x residual as decentring until one is in
  the fit. Instrument: `scripts/qa/fit_ptlens_joint.py`.

- **lensfun's `<center>` element EXISTS and WORKS in 0.3.4 — and installing it
  on top of coefficients fitted for centre=0 is a LOSS in every direction.**
  (The tool facts below stand; the decentring they were chasing does not — see
  the entry above.)
  The element is absent from lensfun's shipped DTD/XSD but is parsed
  (`database.cpp`, context `lens`) and applied (`mod-coord.cpp`
  `ApplyGeometryDistortion` subtracts the centre before the radial callbacks and
  adds it back after); the installed `liblensfun.so.0.3.4` carries the `center`
  string, and darktable honours it — the production warp's output md5 changes.
  Unit confirmed twice: `modifier.cpp` puts the distortion origin at
  `Width/2 + CenterX·(size/2)` with `size` = image height, i.e. 2020 px here —
  the same 2020 px the radius-normalisation probe measured independently
  (entry above). Axes are darktable's image convention (x right, y DOWN).
  MEASURED on one frame through the production invocation, residual
  displacement field against the frame's own linear WCS (sep + astrometry.net;
  `datasets/aug06/set-01/disto_work/`), centred-radial model at radial degree 8:
  no centre **2.59 px RMS** (total displacement median 2.3, max 9.3) against
  (+0.0906,−0.1089) **6.24**, (+0.0906,+0.1089) **7.61**, (−0.0906,−0.1089)
  **6.52**, (−0.0906,+0.1089) **4.24**. All four worse; the solve degrades too
  (logodds 221 → 115–220, matched stars 73 → 42–75).
  MECHANISM: **a,b,c are fitted ABOUT a centre.** Moving the centre under
  coefficients fitted for centre=0 is a different model, not a refinement of the
  same one, so the standalone knob cannot help at any sign. The joint refit that
  would have used it has since been RUN (entry above) and puts the centre at
  (−6,+14) px — zero. So the element has no live use on this lens, and the two
  facts worth keeping are the tool facts: it exists and is honoured in 0.3.4,
  and `install_lens_model.sh --center X,Y` writes it (`--center 0,0` removes
  it) if a future lens ever needs one.

- **Siril `register -disto=` IS NOT PER-IMAGE REPROJECTION — it cancels only
  when every member shares the solution.** Applying each member's OWN SIP as a
  standalone warp and then composing measured WORSE than the shipped route:
  3.99 / 6.42 / 6.19 px (centre/mid/outer) against 0.29 / 0.63 / 2.10 / 2.99 px,
  and worst at the CENTRE, which no distortion story explains. Isolated: warping
  ONE member by its own solution and composing it against its own unwarped self
  gives **8.50 / 9.45 / 6.76 px** — the polynomial is not identity-preserving
  alone. It is designed for a sequence sharing one plate solution, where the
  absolute warp is common and cancels. **Siril's own design therefore assumes
  one optical state per sequence.** The industry operation this is mistaken for
  — resampling each exposure onto a COMMON output WCS using its own full
  solution (CD matrix *and* distortion) — is SWarp's model; Siril has no such
  command and SWarp is not installed here.

- **Siril's internal plate solver DOES handle this class on STACKED members.**
  The standing belief ("cannot match ultra-wide trailed-star fields") was
  measured on single TRAILED frames and had silently widened past its evidence.
  MEASURED on aug06 member sub-stacks: `seqplatesolve -order=3` solved 2/2 with
  388 and 371 matched stars, residual sigx/sigy ~0.9 px, centres agreeing with
  astrometry.net to 0.001°. Stacked members have round stars; single 2.5 s
  ultra-wide frames do not. Keep `solve_field.py` for frames; Siril is usable
  for members.

- **A FITTED ptlens MODEL IS NOT REPRODUCIBLE TO BETTER THAN ~3 px IN THE OUTER
  FIELD, so a coefficient comparison cannot tell an optical STATE from a FIT.**
  MEASURED on four independent fits of ONE set (aug06/set-01, same night, same
  frame pool; varying only the frame subset and the prune): pairwise peak
  displacement difference over the control-point-supported field is **0.36–6.30
  px, median 3.22**, where the three *between-set* models differ by 4.01–10.99
  px, median 7.04. The distributions overlap, and both exceed the 0.47 px
  register-equivalence bound the per-set doctrine was adopted against by 7–23×.
  "All pairs exceed the bound" was therefore never evidence of distinct states —
  any two fits exceed it, including two fits of the same set. Sharpest form: a
  refit of set-01 lands 0.83 px from set-02's shipped model and 3.26 px from
  set-01's own. Per-set granularity is not refuted (between-set is systematically
  larger), but **fit reproducibility is a PREREQUISITE for any per-state model
  work, because ±3 px of procedural uncertainty is the same size as the 2.99 px
  member disagreement it must fix.** A fit's own residual (0.02–0.10 px) says
  nothing about this: it is computed only where the control points are.

- **CORNER CONTROL POINTS CANNOT BE RECOVERED BY REORDERING OR RELAXING
  `cpclean`** — the corner-support deficit is a MATCHING problem, not a pruning
  one. `cpfind`'s raw points do reach the corner (ρ_max 1.60–1.78 against a
  corner at ρ 1.80) and `cpclean` removes essentially all of them (9.9% → 0.0%
  beyond ρ 1.50 on july31/set-01). Decomposed, MEASURED: step 1 (pairwise)
  removes ONE point of 225 and keeps corner support; **step 2 (whole-panorama) is
  the whole effect**. But the tempting mechanism — "step 2 judges points against
  a model with no a,b,c, and unmodelled distortion's residual grows with radius"
  — is REFUTED: seeding step 2 with a project that already carries a fitted
  a,b,c (`pto_template` + `cpclean -w -s`) removes the same population
  (219 → 183, ρ_max 1.77 → 1.65). The `-n` threshold is exhausted too: n = 3, 4,
  5, 6, 8 all return the identical 178 points. Those corner points have large
  residuals under *any* model — they are predominantly bad SIFT matches on
  aberrated, low-SNR corner stars. Keeping them anyway is a measured dead end:
  the fit on the pairwise-only set is DEGENERATE (a = −1.02, b = 3.03, c = −2.37
  against shipped values ~0.001–0.02), confirming the documented degenerate
  basin. A corner-true fit needs corner CORRESPONDENCES that are actually good.

- **`seqapplyreg -framing=max` ON A VARIABLE-SIZE SEQUENCE GIVES EVERY OUTPUT ITS
  OWN ORIGIN — so registered copies are NOT in a common coordinate frame, and
  anything that cross-matches their pixel coordinates is measuring nothing.**
  Every compose here is variable-size: each member is its own group's
  `-framing=min` product, and those differ by tens of px. MEASURED two ways on
  the 28-member union. (1) Solving three registered members: the same sky lands
  **611.9 px apart in x and 416.0 px in y** between `r_s_00001` and `r_s_00026`,
  and the offset is CONSTANT to 0.4 px across three widely separated sky points
  — a pure translation, so scale and rotation ARE common and only the origin is
  not. (2) Matching two consecutive members of ONE set: **zero** pairs within
  1 px, 1 within 2, 12 within 5, 67 of 2000 within 12, 459 within 30 — growth
  smooth in tolerance, the signature of chance nearest neighbours in a dense
  field rather than of correspondences.
  **What this cost: `member_separation.py` — then the compose's ACCEPTANCE GATE,
  now report-only — read those copies, so every number it produced was a chance
  distance between two offset frames.** It ranked its six calibration cells correctly by luck of a
  monotone confound (a bigger optical disagreement also means a bigger framing
  offset), and it starved to UNMEASURED (378/378 pairs) precisely where the
  offsets were largest — the wide multi-night union it exists for. The fix is
  not to solve every member: `register -2pass` already wrote one homography per
  member into the `.seq`, so pushing each member's OWN `findstar` positions
  through `H_ref⁻¹·H_m` puts everything in the reference member's frame by
  construction. MEASURED on a real cell: **67 matches before, 1721 after** (25×),
  and 0/378 pairs unmeasured on the union, in 12 s.
  **The general rule: never assume a tool's batch output shares a frame — verify
  it, cheaply, with the tool's own coordinates.** Two solves, or one known
  displacement pushed through the pipeline, settles it in a minute; this went
  unverified through a build, a validation exercise and a shipped product.

- **`member_separation.py`'s zones WERE CANVAS-radial, which is the wrong
  variable: a member's residual distortion is a function of ITS OWN field
  radius.** Canvas radius equals field radius only when the members are near
  co-pointed — true for every cell it was validated on (98–500 px offsets),
  false across a re-aim, where the canvas centre lies between two optical axes.
  MEASURED symptoms on a cross-night pair: the profile went non-monotonic (outer
  2.07 worse than corner 0.71), the corner median swung **0.71 → 3.38** on a
  0.10 change of the zone bound, and the bootstrap band was 0.55–3.89. Now binned
  by `max(ρ_a, ρ_b)` — each star's radius in its own member, worse of the two —
  and the profile is monotone and tight: on the 28-member union the medians run
  **0.22 / 0.48 / 1.30 / 2.43 px** across centre/mid/outer/corner, at 142–783
  matched stars per zone, and the worst cell reads identically at `--tol` 8, 12,
  20 and 30.
  **Two results the fixed binning delivers immediately.** The disagreement is
  NOT a function of night or of set — same-night pairs median **2.44 px**,
  cross-night **2.39**, same-SET **2.21** — so cross-night combining is
  exonerated as a source and the within-set compose is implicated, independently
  of the star-shape ladder that found it. And the recorded "cross-night state
  difference 4.07 px", downgraded to unmeasured on the old instrument, stays
  unmeasured: it was taken with the canvas zoning AND the broken frame.
  **THRESHOLDS DO NOT SURVIVE AN INSTRUMENT CHANGE — AND A THRESHOLD ON AN
  UNATTRIBUTED QUANTITY IS NOT WORTH WRITING AT ALL.** The 0.35/1.00 px bands
  were anchored to six cells measured on the broken instrument; re-measured on
  the fixed one they read 0.14 / 0.21 / 0.38 / 1.23 / 3.04 / 3.28 against
  0.144 / 0.194 / 0.352 / 0.934 / 2.991 / 2.112 — the ordering holds and the
  floors barely move, but the user-PASSED product's own pair crosses out of PASS.
  **RESOLVED, user-ratified: the whole threshold layer is REMOVED rather than
  re-anchored** (no PASS/WARN/BLOCK, no `--accept-separation`, no abort; the
  number is measured, printed and stamped on the product). Re-anchoring was the
  wrong question, on two measured grounds beyond the instrument change: the
  quantity is a SUM OF TWO TERMS and the compose itself creates one of them
  (1.12 / 0.95 px composed among themselves against 3.02 / 3.38 px inside a 41°
  28-member sequence — 2.5–4.7×, from sequence size alone), and any band that
  separated the accepted products would fire on every real compose, which trains
  the operator to bypass it. **The general rule: a band belongs to a quantity
  whose good-vs-bad is established. Until the driver is attributed there is no
  such boundary, so measure and record — inventing a number to gate on is the
  guessing this repo forbids, and re-raising the decision is re-doing settled
  work** (`docs/combine-contract.md` §5 carries the current state; the
  discriminator that needs no constant is the RELATIVE break-away, 2.5–3× the
  member cluster's own scatter in five sets and ~15× in the sixth).

- **A PSF FITTER IS THE WRONG INSTRUMENT FOR STAR DOUBLING** — it fits one
  component, not the blend, so a doubled corner can read BETTER than a merely
  soft one. MEASURED: corner `findstar` FWHM ranked the failing own-model union
  (4.95 px) as better than the visually-clean single-model control (5.29 px) —
  the ordering the eye reverses; re-measured at matched canvas boxes the two
  read 3.92 vs 3.31 px at c11, a gap far smaller than the visual one. Siril
  `seqtilt` is weaker still: off-axis aberration 0.34 px for the FAILING union
  against 0.40 px for the PASSING one. For member-to-member disagreement use the
  mechanism directly — register the members, `findstar` EACH one separately, and
  mutually match the star lists; the separation of the same star as two members
  place it is the defect, in px, with no fitter in the way. (Box medians are
  blind to it too — that cost this investigation two prior sessions.)

## Acquisition checklist — the real quality lever

Acquisition quality outranks processing; never bandaid what photons must fix.

- Record **14-bit Lossless-compressed** raw, NOT High-Efficiency (HE/HE★ is
  TicoRAW-compressed, lossy-ish, and forces a DNG fallback); confirm 14-bit
  (high-speed continuous can drop to 12-bit).
- Use the sensor's higher conversion-gain stage (a dual-gain CMOS drops read
  noise above its switch ISO); keep subs ≤ 500/focal-mm — star trailing, not read
  noise, caps sharpness on an untracked/lightly-tracked rig.
- MORE integration is the real lever: when band signal/grain ≈ 1, every processing
  knob is only polishing until more photons arrive.
- Flats per focal length used that night, BEFORE touching the zoom; METER to a
  ~50% histogram peak (don't trust a shutter value); diffuse the source (a bare
  screen shows its pixel grid). VERIFY uniformity: shoot a flat, rotate the camera
  180° against the source, shoot another — the two corner/centre ratios must match
  (an over-peaked source adds falloff the lens lacks and the flat is unusable; the
  lights' own sky corner/centre is the cross-check).
- Darks at the lights' exposure/ISO at night temperatures; biases at the flats'
  shutter (= exact flat-darks) — shoot them, it is 30 seconds.
- **DEW CONTROL (measured cost, july23: two of four sets excluded from the
  final combine).**
  A clear still humid night radiation-cools the lens below the dew point even
  in summer; the film NEVER self-clears and faint-star loss precedes the
  visible film. Run a low-power lens heater band from session START (2–3.4 W
  suffices for a camera lens; minimum power that prevents dew — excess heat
  makes convection/soft stars), riding the extended barrel; the 24-70's petal
  hood is sized for 24 mm and is weak protection at 70 mm; a small fan works
  where a band is absent. Watch the brightest star's halo live and flashlight
  the front element when in doubt; if dew is found, warm and continue — never
  stack through it (a contiguous dewed block is NOT rejectable per-pixel; the
  cull is by frame, post-hoc identifiable by the halo/FWHM/nstars timeline —
  mean-based star-box-minus-flanks ministacks + the frame-QA trends, numbers in
  the halo-photometry entry above).
- **VERIFY FOCUS ON THE FIRST FEW FRAMES, then leave it alone — and if you must
  refocus, do it AT A SET BOUNDARY, never mid-set.** MEASURED on one session: the
  first 149 frames ran 9% soft (registration FWHM 2.944 px vs 2.680 achievable)
  and the deficit was present in frame ONE at 2.910 — the lens was never focused,
  not drifting out of focus. A mid-set correction then cost 205 s of pause, three
  handling-ruined frames, and a 1.2 deg re-aim that split the set into two
  pointing swaths — forcing a 152-frame block exclusion, a separate flat, and a
  smaller min-framing intersection for every product that set entered. The same
  correction 15 min later at the set boundary (where a re-aim pause already
  happens) would have cost nothing. Post-correction focus then held for 90+ min:
  the apparent later "drift" (2.672 -> 2.797 -> 2.730 px) REVERSED with nothing
  touched, so it was seeing, not focus — periodic refocusing was not supported by
  the data, and the per-set QA FWHM is the self-check that would show a real
  drift. Cheap check up front: shoot a handful, read the frame-QA FWHM/star
  counts, fix it then.
- **DO NOT SHOOT A FAINT BROADBAND TARGET UNDER HEAVY MOONLIGHT — measured, the
  integration does not buy it back.** A 98%-lit moon 24 deg up, 72 deg off the
  field, raised the sky **4.2x** against a moonless night at the SAME hour on the
  same rig (single raw frames, matched to 3 s of clock time: R/G/B 116/219/166 ADU
  above pedestal vs 27/52/40; the excess is colour-NEUTRAL — R/G 0.53 vs 0.52,
  B/G 0.75 vs 0.77 — which is what identifies moonlight rather than a light
  dome). Consequences, all measured: per-frame noise ~2.4x worse against fixed
  star flux; ~2.7x fewer stars detected per frame (700 vs 1877); and **1030
  moonlit frames FAILED to improve on 799 moonless frames** — a 7-member
  cross-session combine came out **29% WORSE** in background-limited SNR than the
  moonless session alone, and on a smaller frame. Moonlight also worsens the two
  display/calibration defects above: it doubles the autostretch's gradient
  amplification (17x vs 8.7x) and roughly doubles the sky gradient the flat bakes
  in. There is no processing remedy; more integration is not one. Check moon
  phase and altitude when PLANNING, not after.
- Focus recalibration each session is STANDING PRACTICE, and the lens's
  distortion/field-curvature profile moves with it — so the processing-side
  model is per optical state (BACKLOG:`optical-state-models`), and the
  BLUR half is acquisition's alone: if SINGLE frames measure corner-vs-centre
  FWHM elevation, that is field curvature no warp can fix — the refocus
  procedure is the lever, not processing.
- Lock the zoom ring (tape); don't touch the camera mid-set (a focal-length step
  forces a mixed-optics stack). Dither between subs; avoid the moon (star fringes
  on trailed PSFs are dispersion — physical, not removable in processing). Stop a
  fast lens down ≥1 stop for bright-star fields (wide open adds a red veiling-glare
  halo — an honest optical signature, not a bandaid to remove).

**LUNAR (small-disc lucky imaging) — the class block (first corpus measured):**
- **Lossless-compressed NEF only** (HE/HE★ are TicoRAW — no libraw/open decode; a
  set shot HE is unprocessable on this stack). Electronic shutter is safe (9.3 ms
  readout smears 0.14″ at lunar drift) and shock-free — use it.
- **EXPOSE THE DISC: histogram peak 50–70%, never clip the highlands.** The
  measured miss: f/4 · 1/2500 s · ISO 800 at 70 mm put the disc median at ~4% of
  the 14-bit range (peak ~9%) — 2.5–3 stops under; the corrected card for that
  optic is **f/4 · 1/320 s · ISO 800**. At undersampled focal lengths EXPOSURE
  TIME is the free lever (drift 15″/s × 1/320 s ≈ 0.003 px at 17″/px; seeing is
  sub-pixel — nothing to freeze): raise time, not ISO (gain adds no photons and
  burns headroom; ISO 800 already sits at the dual-gain stage). From ~800 mm at
  this pixel pitch seeing becomes resolved, the 1/500–1/1000 s freeze-floor
  returns, and ISO reluctantly becomes the second lever.
- Shoot darks at the LIGHTS' exact tuple in the same thermal window (the between-
  sets slot works); matched short darks ≈ bias + FPN and calibrate cleanly.
- Frame count buys selection depth: 1000+ frames/target at ~1 fps or bursts; keep
  fractions are a stack-time knob, never a capture-time one. Focus on the
  terminator in magnified live view; VR/IBIS off on a rigid tripod; moon > ~40°
  altitude; terminator phases carry the relief.
