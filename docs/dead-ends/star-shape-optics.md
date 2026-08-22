# Star-shape, PSF, and optics measurement

Phase-1 split of `docs/dead-ends.md` (organize-only; the original file stays
the live registry until the merge is decided). Content below the marker is
VERBATIM from the original, so in-text "above"/"below"/section references may
point at entries now homed in a sibling file — `README.md` in this directory
carries the index, the assignment rule, and the block manifest that resolves
them. Do not edit below the marker while the refactor is in phase 1; the split
is re-derivable from the manifest and verified byte-identical by `split.py`.

<!-- == verbatim content from docs/dead-ends.md below this marker == -->
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
  radius at an asymmetric amplitude.
  **CORRECTED, and the correction is in two parts (see the spin-2 entry below,
  `datasets/aug06/corner_work/pa_convention.json`).** First, the RESIDUAL-MOTION
  elimination does not hold: a fixed-direction term IS present in these very
  stars, at 0.0581 / 69.6 SE, alongside the radial one at 0.0395 / 51.0 SE. Both
  terms are real and the elimination was an artefact of a statistic that can
  express only one at a time. Second, the field is not CENTRED: a free-centre fit
  beats the centred model at F 169–999. The family reading is NOT retired —
  see the exponent-scale trap below, which is what a first pass here got wrong.
  What is NOT corrected: it is still in the optics-and-photons of a single
  unregistered exposure, and no distortion model or re-registration reaches it.
  **Consistent with the centred distortion** — distortion and coma respond
  differently to a decentred or tilted element, so well-centred distortion and an
  off-centre aberration field coexist without contradiction.
  TRAP for anyone re-measuring this: `setfindstar`'s DEFAULT roundness floor is
  **0.50**, which truncates exactly the elongated tail being measured and biases
  the bad side rounder. Drop it to 0.05. Second trap: `seqfindstar` reports
  "Sequence processing succeeded" in ~1.5 ms and writes NO star lists headless on
  1.4.4 — use per-image `findstar -out=`.

- **A STAR-SHAPE ANGLE IS A SPIN-2 QUANTITY. AVERAGING IT LINEARLY, OR
  SUMMARISING IT WITH A SCALAR, MANUFACTURES CONTRADICTIONS BETWEEN RECORDS THAT
  BOTH MEASURED CORRECTLY.** Two entries in this tree read the same star shapes
  in opposite directions — one "the major-axis angle tracks field azimuth"
  (radial/optical), one "median PA is near-constant across azimuth sectors"
  (fixed-direction/trailing) — and both were quoted as evidence. Measured with
  ONE instrument over BOTH samples' own tracked `findstar` lists
  (`datasets/aug06/corner_work/pa_convention.py`, record `pa_convention.json`):
  **both terms are present in both samples at once**, radial +0.0524 / 31.1 SE
  alongside fixed 0.0464 / 30.4 SE on the 8074-star sample, and fixed 0.0581 /
  69.6 SE alongside radial +0.0395 / 51.0 SE on the 136k one. Each record's
  exclusive claim is refuted BY ITS OWN DATA. **Neither measurement was wrong;
  each reported the term its statistic and its population could see.** The
  mechanisms, all four reusable:
  - **Siril's `angle` is an AXIS angle mod 180** — verified in
    `src/algos/PSF.c` at the 1.4.4 tag: `psf->angle = -FIT(6) * 180.0 / M_PI`
    wrapped by `while (fabs(psf->angle) > 90.0)`. Only *2θ* is single-valued on
    the circle, so the only correct mean is on the doubled angle, i.e. the
    ellipticity components **e1 = e·cos2θ, e2 = e·sin2θ** (the distortion form
    e = (a²−b²)/(a²+b²), the PSF-diagnostics standard). A linear mean or median
    of θ is not a weaker summary, it is an invalid one.
  - **ROUNDNESS DISCARDS ORIENTATION.** Every corner number in this repo was a
    roundness or an axis length — |e| with the direction thrown away — and the
    direction was the whole discriminator. In the component form the two
    hypotheses are ORTHOGONAL basis functions on the azimuth circle and are
    fitted together: `e1 = c0 + R·cos2φ`, `e2 = s0 + R·sin2φ`, stacked into one
    ordinary 3-parameter least squares. Fixed direction and radial term then stop
    competing, each gets its own SE, and the collinearity that forced the
    either/or disappears (design condition 1.08–1.27).
  - **THE POPULATION CHOOSES THE ANSWER.** The cuts one record used
    (ρ>1200 px, bright half, roundness<0.85) roughly TRIPLE the radial amplitude
    (0.0395 → 0.1261) while barely moving the fixed one (0.0581 → 0.0805),
    because they select the outer field where a radial term is strongest. Two
    records, two populations, two "conclusions" — from one field.
  - **"NEAR-CONSTANT" NEEDS A NULL, AND THE OBVIOUS NULL IS THE WRONG ONE.** The
    8074-star record read a 15.8° sector-median spread as near-constant and
    therefore as trailing. Permuting θ across stars while holding positions (200
    permutations) puts the no-information spread at **1.8 ± 0.5°** — the observed
    15.8° is ~28 null-SDs of *structure*, so the number refuted the reading drawn
    from it. Note the trap that inverts this: the SD of INDIVIDUAL axis angles
    under no information is ~52°, but the relevant null is the SD of eight
    ~1000-star sector MEDIANS, ~25× smaller. Comparing 15.8 against 52 concludes
    the opposite of the truth.
  Two further traps for anyone re-measuring: **a near-round star has NO defined
  angle** — Siril parameterises the axis ratio as `r = 0.5*(cos(FIT(5)) + 1.)`,
  whose derivative vanishes at r = 1, so the rotation of a round star is set by
  the optimiser, and the roundness>0.95 population does carry a small real
  orientation (0.0011 at 10.3 SE on 15487 stars — ~2% of signal, so a live hazard
  for any UNWEIGHTED PA statistic, and an explanation of nothing here). And **a
  FITS row-order flip cannot invert this discriminator** — a reflection maps
  φ → −φ and θ → −θ together, so both hypotheses are invariant (verified on the
  fixture: planted radial 0.1442 → 0.1442, planted fixed 0.1442 → 0.1442 with
  direction +30.10 → −30.10). Handedness IS flipped, so re-test before comparing
  any of this against a sky-derived direction.

- **COMPUTE THE COMPONENT AND THE WHOLE IN THE SAME UNITS AND COMPARE THEM — a
  component cannot exceed the thing it is a component of, and that one check has
  now caught THREE errors nothing else caught.** It is cheap, needs no fixture,
  and each time the error was invisible to every other check in place:
  - a predicted trail contribution of **0.146** against a measured *total*
    field-constant term of **0.047–0.073** — which turned out to mean the trail
    prediction was too large, not that something cancelled it;
  - an unnormalised field-constant term of **25.81 px²** fitted against a median
    a²−b² of **7.61** — which exposed a detection list half made of noise fits;
  - **29.4% of stars carrying NEGATIVE anisotropy along an axis** a coherent
    1.3555 px² term was supposed to occupy — which broke a degeneracy that had
    been recorded as unbreakable.
  The check has no threshold and no free parameter: form the ratio and see
  whether it exceeds 1. **Do it before believing any decomposition**, because
  a fit will happily return a component larger than its whole and report a
  confident SE beside it.

- **A SYSTEMATIC THAT CO-VARIES WITH THE LEVER YOU INTRODUCED TO BREAK A
  DEGENERACY IS WORSE THAN THE DEGENERACY.** A second exposure was staged to
  separate a trail-amplitude error (scales as L²) from a physical term (does
  not) — and longer exposures at longer cadence admit more and fainter spurious
  detections, so **the contamination scaled with the lever**. MEASURED: at
  matched detection sigma, the 3.0 s night carried 5.3% NEGATIVE-amplitude fits
  against 0.0% on the 2.5 s night, and median fitted amplitude 66.7 against
  187.9. Worse, exposure and NIGHT were perfectly aliased — no 3.0 s set exists
  on the other night — so two observations faced two unknowns. **Before staging a
  lever, ask what else varies with it, and check that the new axis is not aliased
  with an existing one.** The corpus-level version of this is cheap to check and
  was not: `datasets/` holds the record of every night, and which exposures
  co-exist on which night is one query.

- **A CRITERION CHOSEN FOR A DEFECT THAT HAS NOT BEEN CHARACTERISED WILL PASS
  THE DEFECT THROUGH.** A 297 px detection was called "a satellite or aircraft
  trail" on its length alone, and the streak-geometry detector was reached for on
  that basis. The detection had **fitted amplitude 47.6 ADU**, 5.3% of that
  night's detections had **NEGATIVE** amplitude, and their position angles were
  random (doubled-angle resultant 0.009) and spatially spread rather than
  colinear. They were noise fits. `anomaly_audit.py` classifies streak GEOMETRY
  and would have returned a clean bill of health while leaving every one of them
  in place. **Characterise the defect — amplitudes, angles, spatial distribution
  — before choosing the instrument**, and note that the wrong instrument here
  fails SILENTLY and in the reassuring direction.

- **A WRONG-BASIS ARTEFACT SCALES DIFFERENTLY FROM A PHYSICAL EFFECT — RUN THE
  TEST AT TWO PLANTED AMPLITUDES AND THE ARTEFACT ANNOUNCES ITSELF.** "Projecting
  a spin-2 field onto a scalar" has now cost **five** corrections in this tree,
  and the fifth was committed *in the act of testing for the first*: a check of
  whether star anisotropy is additive through a Gaussian fit compared the SCALAR
  a²−b² and returned ratios of **0.469 and 0.628**, which read as a large
  additivity failure. It was not one. The two planted terms sat at 70° and 5° —
  nearly perpendicular — so they **cancel in spin-2 by construction**, and a
  scalar cannot represent their sum at all. Redone in COMPONENTS, the same data
  gives absolute errors of **−0.0146 and −0.0161** and additivity holds.
  **THE TELL, which is the reusable part:** a real physical effect gives a roughly
  CONSTANT RATIO across planted amplitudes; a wrong-basis artefact does not,
  because the cancellation depends on the amplitudes themselves. Here the ratio
  moved 0.469 → 0.628 across two amplitudes while the absolute error stayed at
  ~0.015 — *constant in the right basis, varying in the wrong one*. So run any
  such test at **two or more planted amplitudes** and ask whether the discrepancy
  is constant in ABSOLUTE or in RELATIVE terms; whichever it is constant in is the
  basis the quantity actually lives in. A single-amplitude test cannot tell them
  apart and will read a basis error as physics.

- **AN ELLIPTICITY EXPONENT IS NOT A BLUR EXPONENT — THEY DIFFER BY A FACTOR OF
  TWO, AND CONFUSING THEM RETIRES THE WRONG ABERRATION.** Seidel gives the BLUR
  SIZE: transverse coma grows LINEARLY with field height, astigmatism
  QUADRATICALLY. But ellipticity is not a blur size. Blurs convolve, so VARIANCES
  add: `a² = w² + κℓ²`, giving `a² − b² = κℓ²` and
  `e = (a²−b²)/(a²+b²) ≈ κℓ²/2w²`. **Both the ellipticity and the second-moment
  difference go as ℓ², so the reference exponents against field radius are 2 for
  coma and 4 for astigmatism — not 1 and 2.** MEASURED here on the ellipticity
  amplitude per set: 2.09–3.80 (and 1.12–2.81 on the unnormalised
  second-moment difference), i.e. **blur exponents of 0.56–1.90 clustering near
  1**. That STRADDLES coma and falls well short of astigmatism, so the
  coma-family reading is CONSISTENT with the radial profile and is not retired.
  A first pass compared the ellipticity exponent (2.1–3.8) against coma's BLUR
  exponent (1), concluded "never near 1, therefore not coma", and had the
  conclusion exactly backwards. State which quantity's exponent you are quoting,
  every time. (What DOES stand from that pass: the profile is not a clean power
  law — one set peaks at ρ 0.53 and falls beyond it — and no significant negative
  R appears anywhere, so the radial↔tangential flip that would establish
  astigmatism is not demonstrated either. The family is UNRESOLVED between the
  two, not settled for one.)

- **A PER-BIN PROPERTY ESTIMATED FROM N FRAMES HAS N INDEPENDENT REALISATIONS —
  RESAMPLING STARS INSIDE ONE POOLED POPULATION IS NOT AN ERROR BAR FOR IT, AND
  IT MANUFACTURES REJECTIONS.** A star-level bootstrap inside a pool captures shot
  noise only. MEASURED against five raws treated as INDEPENDENT realisations, the
  frame-to-frame scatter is **4.1–9.2× the bootstrap SE, median 5.76×**, and a
  χ²/dof of **35.6** on bootstrap errors becomes **~1.1** on frame-based ones. A
  published rotation significance of "10 to 20σ" (from bootstrap SEs of 1.07–1.39°)
  was WITHDRAWN on this alone. When a gate is a χ², the error model IS the verdict:
  take the denominator from what varies between independent draws, never from what
  is merely plentiful inside one draw.

- **THE THREE-LEVEL SEPARATOR — SINGLE UNREGISTERED FRAME → MEMBER → COADD — IS
  IMMUNE TO THE REGISTRATION-REFERENCE CONFOUND, BECAUSE THE FIRST LEVEL INVOLVES
  NO REFERENCE AT ALL.** The LEVELS are already used throughout this file
  (raw → warped single → member; raw / member / per-set / union), so what is new is
  only the DESIGN claim about what they buy: any experiment that changes the
  registration reference also changes the output canvas, and a canvas change is a
  first-order sub-pixel-phase confound on every star measurement. A ladder anchored
  at a SINGLE UNREGISTERED FRAME sidesteps it by construction — that level has no
  reference, no canvas choice and no resampling — so a term that is present at
  level 1 cannot have been made by the compose, and a term that appears only at
  level 3 cannot be optical.
  **This is the discriminator this registry already used twice without naming it:**
  the aug06 member edge deficit was killed by marching one instrument across
  calibrated single → warped single → member (+0.174 / +0.130 / +0.175 px, flat),
  and the star-shape ladder located the compose smear by the same shape.
  **BOUND, and it is what stops this being a general-purpose answer:** the levels
  differ in DEPTH as well as in reference, so every comparison across them must be
  flux-matched or rank-matched first — the detection-depth artefact recorded under
  "QA / scope" manufactured a 2.6× amplification on exactly this ladder when the
  full detected population was used instead. Level 1 is also the noisiest, so a
  small term may simply be unmeasurable there, and "absent at level 1" must be
  reported with the depth at which it would have been visible.
  (The design is the ORACLE's; the two worked instances and the bound are this
  file's own.)

- **STACKED PRODUCTS CARRY HEAVY NON-STELLAR TAILS THAT THE RAWS DO NOT, SO EVERY
  COHERENT OR AGGREGATE STATISTIC TAKEN ON A STACK IS TAIL-DRIVEN UNLESS IT IS
  CUT.** MEASURED on the anisotropy magnitude |D|: mean/median runs **raw 1.07,
  member 2.07, per-set stack 2.88, union 5.77**, with max |D| at **53.7 / 2368 /
  1.54e4 / 3.38e4**. The tail GROWS WITH STACKING DEPTH, so a statistic that looks
  monotone in depth may be measuring contamination rather than an effect — an
  apparent registration signature reading 0.69 / 4.31 / 5.16 across increasing
  drift span read **0.245 / 0.787 / 0.726** under a matched upper-|D| cut: flatter,
  NOT monotone, and with the deepest product BELOW a shallower one. It would have
  been reported as established had a component-exceeds-the-whole check not fired
  first. A matched cut is validated by the RAWS barely moving under it (0.7264 →
  0.7131). **A box-median summarisation is not automatically safe here either** —
  a median is more robust than a mean, but that has never been verified against
  this distribution, and it must be before any station table is rebuilt on stacked
  members.

- **AN AZIMUTHAL AVERAGE CANCELS A RADIAL TERM ONLY WHERE THE AZIMUTH IS
  COMPLETELY SAMPLED — AND ON A RECTANGULAR FRAME THAT STOPS AT ρ = 0.554, WHICH
  IS INSIDE THE FIELD.** A statistic projecting onto a fixed axis with weight
  `cos 2φ` cancels a radial term only over full azimuth. On a 6064×4040 frame
  (half-short 2020, half-long 3032, half-diagonal 3643.3) the inscribed circle
  holds only to **ρ = 0.5544**, and beyond **ρ = 0.8322** only the four corners
  remain. ⟨cos 2φ⟩ over the azimuths still inside the frame:

  | ρ | azimuth kept | ⟨cos 2φ⟩ |
  |---|---|---|
  | ≤ 0.554 | 100% | **−0.0000** |
  | 0.620 | 70.5% | **+0.3615** |
  | 0.700 | 58.2% | +0.5290 |
  | 0.830 | 46.6% | +0.6795 |
  | 0.976 | 3.5% | +0.4047 |

  **Exactly zero while the circle fits, strongly positive the moment it clips**,
  because the azimuths excluded are those near ±90° where `cos 2φ = −1`; at the
  corners the radial direction sits at **33.67°** to x, so `cos(2·33.67°) = +0.385`
  at all four with the SAME sign and they reinforce rather than cancel. A radial
  term therefore leaks into the fixed-axis projection with a POSITIVE sign, and the
  leak switches on at a GEOMETRIC threshold, not a physical one — which is what
  makes it read as data. MEASURED cost: a five-quintile radial split read
  0.409 / 0.351 / 0.358 / 0.472 / 0.736 and was taken as a radius trend damaging
  two hypotheses at once; the geometric break falls inside quintile 4
  (0.490–0.626) **to the bin**. **THE FIX IS A DIFFERENT ESTIMATOR, NOT A CUT:**
  fit the spin-2 pair PER ρ BIN — `e1(φ) = A·cos2φ + C1`, `e2(φ) = A·sin2φ + C2` —
  which estimates the radial and fixed terms JOINTLY and is immune by construction,
  because it FITS the radial term instead of assuming it averages away. Re-measured
  that way the leak is real and PARTIAL: bin 4 drops 0.472 → 0.392 (22% of the
  excess remaining) and bin 5 only 0.736 → 0.603 (64% remaining, still 7.9σ above
  bin 1) — so "artefact" is too strong, it is partly one. **Read that residue with
  its own caveat:** quintiles are by COUNT and stars concentrate centrally, so the
  outer bin is ~3× wider in ρ and a constant-R model is misspecified across it (its
  fitted R falls to +0.33 where bin 4 reads +1.10). Cheapest guard before trusting
  any outer-field number from an azimuthal average: restrict to ρ < 0.554 and
  re-run.

- **ON A RECTILINEAR LENS THE PLATE SCALE IS NOT ONE NUMBER, AND IT CORRELATES
  WITH FIELD RADIUS AT −0.952 — SO A SINGLE-SCALE PREDICTION SILENTLY LOADS A
  RADIAL TERM.** `r = f·tan(θ)` makes the LOCAL scale vary across the field.
  MEASURED from each member's own solved WCS (differentiated numerically, full
  solution INCLUDING SIP — not the ideal sec² form): **15.904–17.064 ″/px, a 6.93%
  spread**, where every prediction had used one header value of 16.979 ″/px, with
  **correlation −0.952 against ρ**. That correlation is why it is invisible as a
  separate effect and why it lands on precisely the radial term nobody could
  attribute. Substituting the local scale into a joint fit over 148 stations
  absorbs **0.2282 px², 18.1% of the radial coefficient** (radial ρ coef 1.2599 at
  7.3 SE → 1.0317 at 5.9 SE), and it is a subtraction rather than a knob on three
  counts: the radial term SURVIVES at 5.9 SE, so this is partial attribution and
  not an explanation; the one-sided x term is untouched (0.4120 → 0.3971, 3.6%),
  which is what a purely radial mechanism must do and was not arranged; and a
  separately attributed sky-rate term is undamaged (0.67σ → 0.65σ from unity).
  **THE TRAP IT CREATES, which is the half that generalises:** with the local scale
  in, the PREDICTOR itself carries a radial component, so in any fit that does not
  hold ρ it partly proxies for the unmodelled radial term and its slope inflates —
  a predictor-only check moves **1.280 ± 0.239 (1.17σ) to 1.516 ± 0.212 (2.44σ)
  while its R² *improves* 0.164 → 0.260**, i.e. it looks better and means less.
  **Once a position-dependent scale is in the predictor, a predictor-only slope is
  no longer a valid check of the conversion — read the joint fit.**

- **"REFRACTION" NAMES THREE DIFFERENT QUANTITIES HERE. TWO ARE CLOSED, BY
  DIFFERENT ARGUMENTS, AND ONE IS OPEN — NAME WHICH BEFORE CITING EITHER CLOSURE.**
  (1) **As a per-star SHAPE (second-moment) effect it is CLOSED on arithmetic.**
  Differential refraction as a shape term is atmospheric DISPERSION across the
  passband, and measurement here is on the debayered GREEN plane (~480–610 nm), far
  narrower than the 400–650 nm span the standard CTIO 1.40″-at-z=45 figure
  describes. Conservatively **≤0.6″ at z=45 and ≤1.7″ at z=70**, which at this
  corpus's 16.979 ″/px is **≤0.035 px and ≤0.10 px**. Entering as a top-hat in
  second moments on a 2.01 px minor axis, that moves FWHM by ~1e-4 to ~1e-3 px
  against measured effects of **+0.5 px centre-to-corner** on size and **0.11–0.14**
  one-sided — **two to three orders of magnitude below what is being attributed to
  it.** GEOMETRIC differential refraction is not a within-exposure shape effect at
  all (~5.6e-4 anisotropic plate-scale change at z=45, ~0.001 px on a 2.4 px star).
  (2) **As a POSITIONAL displacement it is closed separately and by different
  arithmetic** — the nonlinear residual a projective transform cannot absorb is
  ≈1.1″ ≈ **0.065 px** (`docs/untracked-widefield-standards.md` §F.1). (3) **As a
  TIME-VARYING positional term leaving a registration residual in a stack it is
  OPEN** — that is the candidate in the optical-state-boundary entry above, and
  neither closure reaches it, because (1) is a within-exposure quantity and (2) is
  a single-epoch one. Three quantities, one word: the shape closure does not
  discharge the positional question and the positional closure does not discharge
  the shape one.

- **THE FIT-VS-MOMENT SHAPE BIAS HAS NO ESTABLISHED SIGN — ONLY A MAGNITUDE — SO
  "OUR GRADIENT IS A FLOOR" IS UNSUPPORTED, AND IT HAS TRIED TO ENTER TWICE, BOTH
  TIMES IN THE FLATTERING DIRECTION.** A Gaussian PSF FIT and a weighted SECOND
  MOMENT do not measure the same quantity on a non-Gaussian profile, and this repo
  compares them freely (Siril `psf`/`findstar` fits against the `a²−b²` and
  spin-2 component work). **What IS homed is the MAGNITUDE — ~0.84× a planted
  value (`TOOLS.md` PSFEx row; `BACKLOG:removal-conditions` row 146) — and a
  magnitude is not a direction.** The literature the figure is argued from gives
  the same: Bernstein 2010 bounds the SIZE of the discrepancy and does not fix its
  SIGN for an arbitrary profile. (DOCTRINE — the ORACLE's; `Bernstein` occurred in
  no tracked `.md`, `.py` or `.sh`, and exactly once tree-wide in
  `datasets/aug06/experiments.jsonl`, BEFORE this entry — which is why this is the
  first home for the sign question. **Both counts are now stale BY CONSTRUCTION:**
  this entry and the ubercal entry above both carry the
  string. **A string-search finding cannot be documented by pasting the string —
  state it in the past tense, as here, or split the literal.**)
  **WHY IT MATTERS AND WHY IT KEEPS COMING BACK:** "our measured gradient is a
  FLOOR" converts an unknown-sign bias into a one-sided guarantee, which makes any
  measured star-shape gradient a lower bound on a real defect — the version that
  makes the finding look stronger. **It is a sign claim resting on a magnitude
  result.** Without an established sign the honest statement is that the bias could
  inflate or deflate the gradient, so a measured gradient bounds nothing in either
  direction until the sign is settled for THIS profile class.
  **The test that would settle it, unrun:** plant a known anisotropy on this data's
  own trailed profile and compare the fit-derived and moment-derived recoveries at
  two or more planted amplitudes — the two-amplitude form this registry already
  requires, since a basis or definition error announces itself by a ratio that
  moves while an absolute error stays put.

- **A COHERENT MAGNITUDE AND A PROJECTION ON A NAMED AXIS ARE DIFFERENT
  QUANTITIES, AND ONLY ONE OF THEM IS UNBIASED — SO COMPARING THEM FLATTERS THE
  BIASED ONE.** A direction-free coherent MAGNITUDE is the norm of a mean 2-vector
  and is positively noise-biased; a PROJECTION on a stated axis is unbiased. Two
  figures quoted side by side as the same deficit (0.53× and 0.43×) were these two
  quantities, on differently-cut populations, with nothing beside either saying
  which — and the more generous number was the biased one. Same family as the
  scalar-vs-spin-2 and ellipticity-vs-blur-exponent entries above, and **the tell
  is identical in every instance: two numbers compared with neither one's quantity
  stated beside it.** State the quantity — magnitude, projection, scalar,
  component, ellipticity, blur — every time a figure is quoted for comparison.

- **ON A FIXED CAMERA THE STAR-DRIFT DIRECTION DOES NOT ROTATE — SO "THE ANGLE
  DRIFTS WITH TIME, THEREFORE IT IS TRAILING" IS BACKWARDS.** The sky's apparent
  motion, expressed in the GROUND frame, is a rigid rotation about a pole that is
  itself fixed in that frame. The flow is therefore TIME-INDEPENDENT, and the
  drift direction at a given sensor position is constant. What the parallactic
  angle rotates is the orientation of celestial NORTH in the sensor frame — which
  governs a WCS position angle and has nothing to do with the direction a star
  moves. MEASURED over a full 1497 s set (`drift_bearing.json`, aug06/set-01, ten
  blocks of a 10-frame cross-match): the drift bearing spans **1.027°**, per-block
  SE 0.062°. The instrument validates against pure geometry at the same time —
  measured drift **1.9064 px/frame** against **1.9581** predicted by
  15.041·cos(dec)·cadence/pixel_scale with nothing fitted, 2.64%.
  Two sessions reasoned the other way and sized the expected sweep from the
  field-rotation rate before this was measured; a θ₀ that drifts across a set is
  NOT evidence of trailing, and that reading is withdrawn.
  **What it enables:** the drift bearing is a direct, site-free measurement of the
  trail direction on a ~30 s baseline against a 2.5 s trail, so it is ~12× better
  determined than the trail it tests. Against it, the fixed-direction term in the
  star shapes is **misaligned by 7.85° ± 0.40, i.e. 19.4σ** — so that term is not
  the in-exposure trail **ALONE**. **CORRECTED, and the correction changes what
  the 19.4σ means:** the trail is present at full predicted strength, and the
  measured field-constant term is the RESULTANT of two comparable, nearly
  ANTI-PARALLEL spin-2 terms. MEASURED — a pure trail of L = 1.66 px pushed
  through `findstar` contributes **mean e1 = +0.1555** (per-star prediction on the
  real data: +0.1449), while the real field-constant term measures only
  **+0.0477**. The difference is a field-constant component of **≈0.096 at
  −87.8°** against a trail at +4.7°: 92.5° apart in θ, which in spin-2 is
  ANTI-PARALLEL. So the 7.85° offset is the signature of a small resultant of two
  large near-cancelling vectors, not of the trail being absent — and it explains
  two things previously recorded as puzzles, namely why θ₀ is hypersensitive to
  population (+7.7° on all stars against +23.6° on outer-field cuts) and why it
  drifts across a set. A small difference of two large terms is hypersensitive to
  anything that moves their ratio. **The arithmetic route was eliminated before
  this was concluded:** ellipticity COMPONENTS are additive through a Gaussian fit
  to ~0.015 absolute in e1, verified on two independent planted optical amplitudes,
  so the shortfall is not a failure of additivity. (± is the SE of the mean over nine blocks; the
  between-block SD is 1.21°. **Name the denominator when quoting a σ**: the fit's
  own internal SE would read 33.1σ, and it is the wrong one because the
  between-block scatter *exceeds* it, so real dispersion would be assumed away.
  Even 19.4σ is optimistic — the nine blocks share one optical field and are not
  nine independent draws. The claim does not rest on the σ: every block has the
  same sign, the range is +6.27 to +10.04°, and the smallest offset is 8.8× the
  per-block fit SE.) Confounds not separated and recorded with it: the field
  drifts 953 px over a set so the star population changes, and θ₀ is known to be
  population-sensitive; and the fit's constant term absorbs part of the decentred
  radial field.
  **And it localises the first-frame anomaly to the EXPOSURE, not the sky.** The
  first frames of a night read θ₀ **19.75° (23.9σ)** away from the rest of the set
  while their drift bearing departs by **0.150°**. The sky was doing the normal
  thing; only the star shapes were not — which is what vibration or settling on
  the first exposure after setup looks like, and it reproduces across detection
  depth and across both nights.

- **A LINEAR REGRESSOR AVERAGES A SIGN-FLIPPING PATTERN TO ZERO, AND THAT NULL IS
  NOT EVIDENCE OF ABSENCE.** `mechanism_and_specs.json`'s own model-free sided
  bands on the MAJOR axis sign-flip across |x| (−0.12, −0.17, −0.08, **+0.14,
  +0.11**) while its linear-in-x regression on the same stars reads 0.13 SE and
  F = 0.017 — and the published verdict "star SIZE is purely radial" follows the
  regression. Re-measured with ρ HELD in four annuli, the +x side's median major
  axis exceeds the −x side's in EVERY annulus and EVERY |x| band on the 18-frame
  sample, +0.04 to +0.43 px. Before reading a regression null as absence, plot
  the model-free bands the regression was fitted through. (Caveat carried with
  it: the per-side detection counts are strongly imbalanced there, 2332 against
  4599 in one band, so that re-measurement is a flag for a cleaner pass, not a
  verdict.)

