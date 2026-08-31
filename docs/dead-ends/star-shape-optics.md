# Star-shape, PSF, and optics measurement

Part of the dead-end registry — `docs/dead-ends.md` is the index, and
`00-registry-contract.md` governs how entries are read, cited, written and
deleted. Entries are maintained IN PLACE (pre-compression forms are in git;
the pre-split single-file registry is `docs/dead-ends.md`'s own history).
Cross-references to sibling files are written as (`<file>.md`) pointers.
The one-sided band is an OPEN question — status home: BACKLOG:`one-sided-band`
(the raw-frame term is real and pipeline-exonerated; the UNION band's carrier
is the members' own entry-side columns, night-dominated and in the photons —
attributed and answered by member selection, `docs/corner-smear-member-selection.md`;
BACKLOG:`compose-homography-smear`).

<!-- registry content below; docs/dead-ends.md is the index -->
- **A STAR-SHAPE MEDIAN COMPARED ACROSS IMAGES OF DIFFERENT DEPTH IS A
  DETECTION-DEPTH COMPARISON, NOT A QUALITY ONE — flux-match the population or
  the deeper image loses every time.** `findstar` goes as faint as the image
  allows and marginal fits are inflated, so a deeper stack (or a darker sky at
  equal depth) drags its own median up. The mirror of the survivorship trap
  (`registration-distortion.md`, the comparison-traps entry): there a worse
  image measured better; here a deeper one measures worse — together they mean
  **a raw `findstar` median is not comparable across levels of a chain at
  all**. MEASURED chasing the aug06 member edge deficit: at one 800 px box the
  session difference reads **+0.055 px on the 30 brightest and +0.518 on the
  full detected population** — a factor of 9 across the same two files, driven
  by the moonless night detecting to amplitude A≥0.00031 where the moonlit one
  stops at A≥0.00060; the full-population reading manufactured an apparent
  2.6× amplification by the stacking stage that does not exist (flux-matched:
  flat +0.174/+0.130/+0.175 px across single → warped single → member).
  **The fix costs nothing:** one common fitted-amplitude threshold across
  every box and arm (picked so the thinnest box keeps ≥60 stars), or
  rank-match on the N brightest — legitimate because the same sky box holds
  the same physical stars in every image of it. Report n and the faintest
  admitted amplitude with every number.
- **`findstar` SETTINGS ARE DUAL-PURPOSE AND THE TWO PURPOSES WANT OPPOSITE
  VALUES.** MEASURING a shape distribution needs the roundness floor DROPPED —
  the default 0.50 truncates exactly the elongated tail under study and biases
  the bad side rounder (use 0.05). BUILDING a PSF for deconvolution needs the
  DEFAULTS — relaxed settings let junk into the average: the same `makepsf
  stars` call returned 6.7 px / 0.42-ratio kernels on relaxed detection
  (uncorrelated with anything) and 2.0–2.7 px / 0.76–0.86 on defaults,
  tracking findstar band for band. The garbage was caught only by RENDERING
  the kernel — a fitted number alone would have shipped it. Two tool facts
  from the same probe: **`rl` with no arguments is a NO-OP** on this data
  (use `-mul`), and **`seqfindstar` writes no star lists headless on 1.4.4**
  ("Sequence processing succeeded" in ~1.5 ms; use per-image
  `findstar -out=`).

- **THE ONE-SIDED STAR-SHAPE GRADIENT IS IN THE OPTICS-AND-PHOTONS OF A SINGLE
  EXPOSURE — stop looking for it in the chain.** Measured on single
  Siril-debayered RAWs (no dark, flat, warp, registration or stack), 3 frames
  × 6 sets × 2 nights, 136k stars. Candidates ELIMINATED by measurement: a
  DETECTION/BRIGHTNESS artefact (the gradient survives inside amplitude
  quartiles in 6/6 sets); PURE DEFOCUS / tilted focal plane ON THE RAWS (that inflates
  BOTH axes on the soft side — the MINOR axis measures symmetric left-vs-right
  while the major does not; on the UNION the odd size term +0.180 px re-opened
  defocus in the candidate families below, since attributed to the members'
  entry-side columns — `stacking-compose.md`, the union-smear entry); RESIDUAL DISTORTION (the geometry fits a centred
  ptlens model to a 0.27 px median — `registration-distortion.md`, the
  affine-nuisance entry). The RESIDUAL-MOTION elimination did NOT hold: a
  fixed-direction term IS present in these very stars (0.0581 / 69.6 SE)
  alongside the radial one (0.0395 / 51.0 SE) — both real; the either/or was
  an artefact of a statistic that can express only one at a time (the spin-2
  entry below). And the field is not CENTRED: a free-centre fit beats the
  centred model at F 169–999 — a finding the open item's decentring reading
  rests on, with the restraint about quoting a centre recorded there.
  Consistent physics: distortion and coma respond differently to a decentred
  or tilted element, so well-centred distortion and an off-centre aberration
  field coexist. Re-measurement traps: the dual-purpose entry above
  (roundness floor, `seqfindstar`).
- **A STAR-SHAPE ANGLE IS A SPIN-2 QUANTITY. AVERAGING IT LINEARLY, OR
  SUMMARISING IT WITH A SCALAR, MANUFACTURES CONTRADICTIONS BETWEEN RECORDS
  THAT BOTH MEASURED CORRECTLY.** Two records read the same star shapes in
  opposite directions (radial/optical vs fixed-direction/trailing); one
  instrument over both samples' own tracked `findstar` lists
  (`git show d2c4591:datasets/aug06/corner_work/pa_convention.py`, record
  `pa_convention.json`) shows **both terms present in both samples at once**
  — radial +0.0524 / 31.1 SE beside fixed 0.0464 / 30.4 SE on the 8074-star
  sample; fixed 0.0581 / 69.6 SE beside radial +0.0395 / 51.0 SE on the 136k
  one. Each record's exclusive claim is refuted by its own data; neither
  measurement was wrong — each reported the term its statistic and population
  could see. The mechanisms, all four reusable:
  - **Siril's `angle` is an AXIS angle mod 180** (verified in
    `src/algos/PSF.c` at the 1.4.4 tag). Only 2θ is single-valued on the
    circle, so the only correct mean is on the ellipticity components
    **e1 = e·cos2θ, e2 = e·sin2θ** (e = (a²−b²)/(a²+b²), the PSF-diagnostics
    standard). A linear mean or median of θ is not a weaker summary, it is an
    invalid one.
  - **ROUNDNESS DISCARDS ORIENTATION** — |e| with the direction thrown away,
    and the direction was the whole discriminator. In component form the two
    hypotheses are ORTHOGONAL basis functions on the azimuth circle, fitted
    together (`e1 = c0 + R·cos2φ`, `e2 = s0 + R·sin2φ`, one 3-parameter least
    squares): fixed and radial stop competing and each gets its own SE
    (design condition 1.08–1.27).
  - **THE POPULATION CHOOSES THE ANSWER.** Cuts selecting the outer field
    roughly TRIPLE the radial amplitude (0.0395 → 0.1261) while barely moving
    the fixed one — two records, two populations, two "conclusions", one
    field.
  - **"NEAR-CONSTANT" NEEDS A NULL, AND THE OBVIOUS NULL IS THE WRONG ONE.**
    A 15.8° sector-median spread read as near-constant is **~28 null-SDs of
    structure** — permuting θ across stars puts the no-information spread of
    eight ~1000-star sector MEDIANS at 1.8 ± 0.5°, while the SD of INDIVIDUAL
    axis angles is ~52°; comparing against the individual-angle null
    concludes the opposite of the truth.
  Two further re-measurement traps: **a near-round star has NO defined
  angle** (Siril parameterises r = 0.5·(cos FIT(5)+1), whose derivative
  vanishes at r=1, so a round star's rotation is set by the optimiser; the
  roundness>0.95 population still carries a small real orientation, 0.0011 at
  10.3 SE — a live hazard for any UNWEIGHTED PA statistic); and **a FITS
  row-order flip cannot invert this discriminator** (a reflection maps φ→−φ
  and θ→−θ together, both hypotheses invariant — but handedness IS flipped,
  so re-test before comparing against a sky-derived direction).
- **COMPUTE THE COMPONENT AND THE WHOLE IN THE SAME UNITS AND COMPARE THEM — a
  component cannot exceed the thing it is a component of, and that one check
  has caught THREE errors nothing else caught:** a predicted trail
  contribution of 0.146 against a measured *total* field-constant term of
  0.047–0.073 (the trail prediction was too large, not cancelled); an
  unnormalised field-constant 25.81 px² fitted against a median a²−b² of 7.61
  (a detection list half made of noise fits); and 29.4% of stars carrying
  NEGATIVE anisotropy along an axis a coherent 1.3555 px² term was supposed
  to occupy (a degeneracy recorded as unbreakable, broken). No threshold, no
  free parameter: form the ratio and see whether it exceeds 1, **before
  believing any decomposition** — a fit will happily return a component
  larger than its whole with a confident SE beside it.
- **A SYSTEMATIC THAT CO-VARIES WITH THE LEVER YOU INTRODUCED TO BREAK A
  DEGENERACY IS WORSE THAN THE DEGENERACY.** A second exposure was staged to
  separate a trail-amplitude error (scales as L²) from a physical term — and
  longer exposures at longer cadence admit more and fainter spurious
  detections, so **the contamination scaled with the lever** (at matched
  detection sigma the 3.0 s night carried 5.3% negative-amplitude fits
  against 0.0%, median fitted amplitude 66.7 against 187.9). Worse, exposure
  and NIGHT were perfectly aliased — two observations, two unknowns. **Before
  staging a lever, ask what else varies with it, and check the new axis is
  not aliased with an existing one** — which exposures co-exist on which
  night is one query against `datasets/`.
- **A CRITERION CHOSEN FOR A DEFECT THAT HAS NOT BEEN CHARACTERISED WILL PASS
  THE DEFECT THROUGH.** A 297 px detection was called "a satellite or
  aircraft trail" on its length alone and the streak-geometry detector
  reached for — but it had fitted amplitude 47.6 ADU, 5.3% of that night's
  detections had NEGATIVE amplitude, and their position angles were random
  (doubled-angle resultant 0.009): noise fits, which `anomaly_audit.py`
  classifies by streak GEOMETRY and would have passed clean. **Characterise
  the defect — amplitudes, angles, spatial distribution — before choosing the
  instrument**; the wrong instrument fails silently and in the reassuring
  direction.
- **A WRONG-BASIS ARTEFACT SCALES DIFFERENTLY FROM A PHYSICAL EFFECT — RUN THE
  TEST AT TWO PLANTED AMPLITUDES AND THE ARTEFACT ANNOUNCES ITSELF.**
  Projecting a spin-2 field onto a scalar has cost five corrections in this
  tree, the fifth committed in the act of testing for the first: an
  additivity check on the SCALAR a²−b² returned ratios 0.469 and 0.628 (reads
  as a large additivity failure) for two planted terms at 70° and 5° — nearly
  perpendicular, so they cancel in spin-2 BY CONSTRUCTION. In COMPONENTS the
  same data gives absolute errors −0.0146 and −0.0161: additivity holds.
  **The reusable tell: a real effect gives a roughly constant RATIO across
  planted amplitudes; a wrong-basis artefact does not** — here the ratio
  moved 0.469 → 0.628 while the absolute error stayed ~0.015. Whichever the
  discrepancy is constant in is the basis the quantity lives in; a
  single-amplitude test cannot tell them apart and reads a basis error as
  physics.
- **AN ELLIPTICITY EXPONENT IS NOT A BLUR EXPONENT — THEY DIFFER BY A FACTOR
  OF TWO, AND CONFUSING THEM RETIRES THE WRONG ABERRATION.** Seidel gives the
  BLUR SIZE (coma linear in field height, astigmatism quadratic); but blurs
  convolve, so VARIANCES add: `a² = w² + κℓ²` gives `a²−b² = κℓ²` and
  e ≈ κℓ²/2w² — **the reference exponents against field radius are 2 for
  coma and 4 for astigmatism, not 1 and 2.** Measured here: ellipticity
  exponents 2.09–3.80 = blur exponents 0.56–1.90 clustering near 1 — that
  STRADDLES coma and falls short of astigmatism, so the coma-family reading
  is CONSISTENT; a first pass compared the ellipticity exponent against
  coma's blur exponent and had the conclusion exactly backwards. **State
  which quantity's exponent you are quoting, every time.** (What stands from
  that pass: the profile is not a clean power law, and no significant
  negative R appears anywhere, so the radial↔tangential flip that would
  establish astigmatism is not demonstrated — the family is UNRESOLVED
  between the two.)
- **A PER-BIN PROPERTY ESTIMATED FROM N FRAMES HAS N INDEPENDENT REALISATIONS
  — RESAMPLING STARS INSIDE ONE POOLED POPULATION IS NOT AN ERROR BAR FOR IT,
  AND IT MANUFACTURES REJECTIONS.** A star-level bootstrap inside a pool
  captures shot noise only. MEASURED against five raws treated as independent
  realisations: the frame-to-frame scatter is **4.1–9.2× the bootstrap SE,
  median 5.76×**, and the χ²/dof pairs move **35.60 → 1.81 and 40.95 → 1.57**
  from bootstrap to frame-based errors (the long-published "~1.1" crossed two
  binnings — the register's headline-number row carries the enumeration). A
  published rotation significance of "10 to 20σ" (from bootstrap SEs of
  1.07–1.39°) was WITHDRAWN on this alone. When a gate is a χ², the error
  model IS the verdict: take the denominator from what varies between
  independent draws, never from what is merely plentiful inside one draw.
- **THE THREE-LEVEL SEPARATOR — SINGLE UNREGISTERED FRAME → MEMBER → COADD —
  IS IMMUNE TO THE REGISTRATION-REFERENCE CONFOUND, BECAUSE THE FIRST LEVEL
  INVOLVES NO REFERENCE AT ALL.** Any experiment that changes the
  registration reference also changes the output canvas — a first-order
  sub-pixel-phase confound on every star measurement; a ladder anchored at a
  single unregistered frame sidesteps it by construction, so a term present
  at level 1 cannot have been made by the compose, and a term appearing only
  at level 3 cannot be optical. This registry used the shape twice: the aug06
  member edge deficit was killed by marching one instrument across the levels
  (flat +0.174/+0.130/+0.175 px), and the star-shape ladder located the
  compose smear. **BOUND: the levels differ in DEPTH as well as reference, so
  every cross-level comparison must be flux- or rank-matched first** (the
  detection-depth entry above manufactured a 2.6× artefact on exactly this
  ladder), level 1 is the noisiest, and "absent at level 1" must be reported
  with the depth at which it would have been visible.
- **STACKED PRODUCTS CARRY HEAVY NON-STELLAR TAILS THAT THE RAWS DO NOT, SO
  EVERY COHERENT OR AGGREGATE STATISTIC TAKEN ON A STACK IS TAIL-DRIVEN
  UNLESS IT IS CUT.** MEASURED on the anisotropy magnitude |D|: mean/median
  runs raw 1.07 → member 2.07 → per-set 2.88 → union 5.77, max |D| 53.7 →
  3.38e4 — **the tail GROWS WITH STACKING DEPTH**, so a statistic monotone in
  depth may be measuring contamination: an apparent registration signature
  reading 0.69 / 4.31 / 5.16 across increasing drift span read **0.245 /
  0.787 / 0.726 under a matched upper-|D| cut** — flatter, not monotone, the
  deepest product BELOW a shallower one; it would have shipped had a
  component-exceeds-the-whole check not fired first. A matched cut is
  validated by the RAWS barely moving under it (0.7264 → 0.7131). A
  box-median summarisation is not automatically safe against this
  distribution — verify before rebuilding any station table on stacked
  members.
- **AN AZIMUTHAL AVERAGE CANCELS A RADIAL TERM ONLY WHERE THE AZIMUTH IS
  COMPLETELY SAMPLED — AND ON A RECTANGULAR FRAME THAT STOPS AT ρ = 0.554,
  INSIDE THE FIELD.** A fixed-axis projection with weight `cos 2φ` cancels a
  radial term only over full azimuth; on a 6064×4040 frame the inscribed
  circle holds to ρ = 0.5544, and ⟨cos 2φ⟩ over the azimuths still inside the
  frame:

  | ρ | azimuth kept | ⟨cos 2φ⟩ |
  |---|---|---|
  | ≤ 0.554 | 100% | **−0.0000** |
  | 0.620 | 70.5% | **+0.3615** |
  | 0.830 | 46.6% | +0.6795 |
  | 0.976 | 3.5% | +0.4047 |

  Exactly zero while the circle fits, strongly positive the moment it clips —
  the excluded azimuths are those near ±90° where cos 2φ = −1, and at the
  corners the radial direction reinforces with the SAME sign at all four. A
  radial term therefore leaks into the fixed-axis projection at a GEOMETRIC
  threshold, which is what makes it read as data: a five-quintile radial
  split was taken as a radius trend damaging two hypotheses, and the
  geometric break falls inside quintile 4 to the bin. **THE FIX IS A
  DIFFERENT ESTIMATOR, NOT A CUT: fit the spin-2 pair PER ρ BIN**
  (`e1 = A·cos2φ + C1`, `e2 = A·sin2φ + C2`) — immune by construction because
  it FITS the radial term instead of assuming it averages away. Re-measured
  that way the leak is real and PARTIAL (bin 4 drops 0.472 → 0.392; bin 5
  0.736 → 0.603, still 7.9σ above bin 1) — "artefact" is too strong, it is
  partly one; and count-quantiles make the outer bin ~3× wider in ρ, so a
  constant-R model is misspecified across it. Cheapest guard before trusting
  any outer-field number from an azimuthal average: restrict to ρ < 0.554 and
  re-run.
- **ON A RECTILINEAR LENS THE PLATE SCALE IS NOT ONE NUMBER, AND IT CORRELATES
  WITH FIELD RADIUS AT −0.952 — SO A SINGLE-SCALE PREDICTION SILENTLY LOADS A
  RADIAL TERM.** `r = f·tan θ` makes the LOCAL scale vary: measured from each
  member's own solved WCS (numerically differentiated, full solution
  including SIP), **15.904–17.064″/px, a 6.93% spread**, where every
  prediction had used one header value — correlation −0.952 against ρ, which
  is why it lands on precisely the radial term nobody could attribute.
  Substituting the local scale into a joint fit over 148 stations absorbs
  **0.2282 px², 18.1% of the radial coefficient** (1.2599 → 1.0317 at 5.9 SE)
  — a subtraction, not a knob: the radial term SURVIVES, the one-sided x term
  is untouched (3.6%), and a separately attributed sky-rate term is
  undamaged. **THE TRAP IT CREATES:** with the local scale in, the PREDICTOR
  itself carries a radial component and partly proxies for the unmodelled
  radial term — a predictor-only check moves 1.17σ → 2.44σ while its R²
  *improves* — so **once a position-dependent scale is in the predictor, a
  predictor-only slope is no longer a valid check of the conversion; read the
  joint fit.**
- **"REFRACTION" NAMES THREE DIFFERENT QUANTITIES HERE. TWO ARE CLOSED, BY
  DIFFERENT ARGUMENTS, AND ONE IS OPEN — NAME WHICH BEFORE CITING EITHER
  CLOSURE.** (1) As a per-star SHAPE effect it is CLOSED on arithmetic:
  dispersion across the debayered GREEN plane (~480–610 nm) is ≤0.6″ at z=45
  and ≤1.7″ at z=70 — ≤0.035/0.10 px at 16.979″/px, entering second moments
  at ~1e-4 to 1e-3 px against measured effects of +0.5 px — two to three
  orders of magnitude below what was being attributed to it. (2) As a
  POSITIONAL displacement it is closed separately: the nonlinear residual a
  projective transform cannot absorb is ≈1.1″ ≈ 0.065 px
  (`docs/untracked-widefield-standards.md` §F.1). (3) As a TIME-VARYING
  positional term leaving a registration residual in a stack it is OPEN — the
  candidate in the optical-state-boundary material (`stacking-compose.md`,
  the sub-stack compose entry), which neither closure reaches: (1) is a
  within-exposure quantity and (2) a single-epoch one. Three quantities, one
  word; neither closure discharges the others' questions.
- **THE FIT-VS-MOMENT SHAPE BIAS HAS NO ESTABLISHED SIGN — ONLY A MAGNITUDE —
  SO "OUR GRADIENT IS A FLOOR" IS UNSUPPORTED, AND IT HAS TRIED TO ENTER
  TWICE, BOTH TIMES IN THE FLATTERING DIRECTION.** A Gaussian PSF FIT and a
  weighted SECOND MOMENT do not measure the same quantity on a non-Gaussian
  profile, and this repo compares them freely. What IS homed is the
  MAGNITUDE — ~0.84× a planted value (`TOOLS.md` PSFEx row) — and a
  magnitude is not a direction; the literature (Bernstein 2010) likewise
  bounds the size, not the sign, for an arbitrary profile (DOCTRINE).
  **"A floor" converts an unknown-sign bias into a one-sided guarantee** —
  the version that makes any measured star-shape gradient look stronger.
  Without an established sign the bias could inflate or deflate the gradient,
  so a measured gradient bounds nothing in either direction until the sign is
  settled for THIS profile class. **The test that would settle it, still
  unrun:** plant a known anisotropy on this data's own trailed profile and
  compare fit- and moment-derived recoveries at two or more planted
  amplitudes (the two-amplitude form above).
- **A COHERENT MAGNITUDE AND A PROJECTION ON A NAMED AXIS ARE DIFFERENT
  QUANTITIES, AND ONLY ONE OF THEM IS UNBIASED — SO COMPARING THEM FLATTERS
  THE BIASED ONE.** A direction-free coherent MAGNITUDE is the norm of a mean
  2-vector and is positively noise-biased; a PROJECTION on a stated axis is
  unbiased. Two figures quoted side by side as the same deficit (0.53× and
  0.43×) were these two quantities, on differently-cut populations, with
  nothing beside either saying which — and the more generous number was the
  biased one. **The tell is identical in every instance of this family: two
  numbers compared with neither one's quantity stated beside it. State the
  quantity — magnitude, projection, scalar, component, ellipticity, blur —
  every time a figure is quoted for comparison.**
- **ON A FIXED CAMERA THE STAR-DRIFT DIRECTION DOES NOT ROTATE — SO "THE ANGLE
  DRIFTS WITH TIME, THEREFORE IT IS TRAILING" IS BACKWARDS.** The sky's
  apparent motion in the GROUND frame is a rigid rotation about a pole fixed
  in that frame: the flow is TIME-INDEPENDENT and the drift direction at a
  given sensor position is constant. What the parallactic angle rotates is
  celestial NORTH in the sensor frame — a WCS position angle, nothing to do
  with the direction a star moves. MEASURED over a full 1497 s set
  (`drift_bearing.json`): drift bearing spans **1.027°**, per-block SE
  0.062°, and the instrument validates against pure geometry with nothing
  fitted (measured 1.9064 px/frame vs 1.9581 predicted, 2.64%). A θ₀ that
  drifts across a set is NOT evidence of trailing.
  **What it enables:** the drift bearing is a direct, site-free measurement
  of the trail direction, ~12× better determined than the trail it tests.
  Against it the fixed-direction shape term is **misaligned 7.85° ± 0.40
  (19.4σ)** — and the resolved reading is that **the trail is present at FULL
  predicted strength and the field-constant term is the RESULTANT of two
  comparable, nearly ANTI-PARALLEL spin-2 terms**: a pure trail of L=1.66 px
  contributes mean e1 ≈ +0.15 while the measured field-constant term is only
  +0.0477 — the difference is a component of ≈0.096 at −87.8° against the
  trail at +4.7°, 92.5° apart in θ = anti-parallel in spin-2. A small
  resultant of two large near-cancelling vectors explains why θ₀ is
  hypersensitive to population and why it drifts across a set. The
  arithmetic route was eliminated first: ellipticity COMPONENTS are additive
  through a Gaussian fit to ~0.015 absolute, verified on two planted
  amplitudes. **Name the denominator when quoting the σ**: 19.4σ uses the
  between-block SE (between-block SD 1.21°); the fit's internal SE would
  read 33.1σ and is the wrong one — and even 19.4σ is optimistic (nine
  blocks share one optical field); the claim rests on every block having the
  same sign (range +6.27° to +10.04°), not on the σ. Confounds recorded: the
  field drifts 953 px over a set so the population changes, and the fit's
  constant term absorbs part of the decentred radial field.
  **And it localises the first-frame anomaly to the EXPOSURE, not the sky:**
  a night's first frames read θ₀ 19.75° (23.9σ) away from the rest while
  their drift bearing departs by 0.150° — the sky was doing the normal
  thing, only the star shapes were not: the signature of vibration/settling
  on the first exposure after setup, reproducing across detection depth and
  both nights.
- **A LINEAR REGRESSOR AVERAGES A SIGN-FLIPPING PATTERN TO ZERO, AND THAT NULL
  IS NOT EVIDENCE OF ABSENCE.** `mechanism_and_specs.json`'s own model-free
  sided bands on the MAJOR axis sign-flip across |x| (−0.12, −0.17, −0.08,
  **+0.14, +0.11**) while its linear-in-x regression on the same stars reads
  F = 0.017 — and the published verdict "star SIZE is purely radial" followed
  the regression. Re-measured with ρ HELD in four annuli, the +x side's
  median major axis exceeds the −x side's in EVERY annulus and EVERY |x|
  band, +0.04 to +0.43 px. **Before reading a regression null as absence,
  plot the model-free bands the regression was fitted through.** (Caveat
  carried: the per-side detection counts are strongly imbalanced, so that
  re-measurement is a flag for a cleaner pass, not a verdict.)
- **THE ONE-SIDED RADIAL TERM'S CANDIDATE FAMILIES AND THEIR DISCRIMINATORS ARE
  DOCTRINE (Jarvis, Schechter & Jain 2008, arXiv:0810.0027), NOT MEASUREMENTS ON THIS
  CORPUS — no row is promoted to a finding by being quoted.** Decentred / misaligned
  optic: astigmatism grows linearly from a DISPLACED centre, ellipticity ∝ astigmatism ×
  defocus (odd in shape, even in size) — a spin-2 fit per ρ-bin with a FREE centre.
  Off-axis coma: radial, centred, linear — a one-sided term is not coma unless the axis
  is displaced. Defocus / focal-plane tilt: a one-sided SIZE gradient — on the list.
  Atmospheric dispersion: along the elevation vector, CHROMATIC, ∝ tan z — the
  per-Bayer-channel ellipticity is the cheapest discriminator here, with the greens
  identified FROM THE DATA (`TOOLS.md`, "IDENTIFY THE GREENS"). Tracking / mount:
  field-constant — the spin-2 fit separates it. Gravity / flexure: cross-session at
  differing altitude. Registration / resampling residual: REFUTED as the union band's
  carrier by the 9× drift-span discriminator (`stacking-compose.md`). NOT candidates:
  the coadd's orientation mixing (a corollary of the single-frame term reaching the
  coadd, not a source) and the clamp acting across a trail (field-constant — a component
  the spin-2 fit absorbs, named so it does not contaminate a radial term). The
  astigmatism × defocus row is a good FALSIFIER and a weak confirmer: a CONSTANT
  asymmetry amplitude across sessions with refocus between them kills it; variation is
  consistent and confirms nothing (field curvature keeps off-axis defocus non-zero at
  best focus, the lever's size is unmeasured, sessions are confounded). MEASURED: the
  per-set ±2400 entry-minus-exit FWHM asymmetry runs night-ordered, −0.070 … +0.472 px
  (`datasets/corpus/member_selection/july31+aug06+aug09+aug14_full_portion.json`), so
  the kill does not fire; UNCHECKED that this FWHM asymmetry is the odd ELLIPTICITY term
  — a per-set roundness asymmetry from the profile cache's `top30_round` checks it with
  no new run. The altitude bound binds the atmospheric and gravity rows: the corpus sits
  63–88° above the horizon within 2.4 h of the meridian, so the sense-reversal lever is
  UNQUANTIFIED. Commensurability: the DISTORTION centre ((−6, +14) px, the centred
  ptlens fit — `registration-distortion.md`, the affine-nuisance entry) and the
  ELLIPTICITY-field centre (a free-centre fit wins at F 169–999 with offsets 443–531 px,
  three populations disagreeing by ~300 px at 10–20 of their own sigmas — no centre is
  quoted) are different quantities; a distortion centre at zero refutes nothing about the
  other. Records: `datasets/aug06/corner_work/`.
