# Registration and lens distortion (wide-field untracked)

Phase-1 split of `docs/dead-ends.md` (organize-only; the original file stays
the live registry until the merge is decided). Content below the marker is
VERBATIM from the original, so in-text "above"/"below"/section references may
point at entries now homed in a sibling file — `README.md` in this directory
carries the index, the assignment rule, and the block manifest that resolves
them. Do not edit below the marker while the refactor is in phase 1; the split
is re-derivable from the manifest and verified byte-identical by `split.py`.

<!-- == verbatim content from docs/dead-ends.md below this marker == -->
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
  `register -disto=` has no model to eat. SUBJECT: SINGLE TRAILED FRAMES; on stacked
  MEMBERS this is SUPERSEDED — `seqplatesolve -order=3` residual ~0.9 px meets this
  entry's own bar (the "Siril's internal plate solver DOES handle this class on STACKED
  members" entry below), and members are what the shipped compose registers.** Fixed
  tripod (distortion physically identical
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
  trail LENGTH; the ~3.6 per-frame FWHM was CFA-sampled (Bayer-inflated, so it is a
  RELATIVE figure only — **the divergence that produced it is RETIRED and this
  pointer used to send readers to a register row that no longer exists**;
  `run_frame_qa.sh` now runs `convert c -debayer`, and `CFA-sampled` matches ZERO
  rows in the register today, so the number is a historical one and nothing in the
  register governs it); station values are debayered majFWHM medians
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
- **A STANDALONE PER-MEMBER SIP WARP, APPLIED OUTSIDE SIRIL'S REGISTRATION, IS
  WORSE THAN THE SHIPPED ROUTE — the polynomial is not identity-preserving
  alone.** Applying each member's OWN SIP as a standalone warp and then composing
  measured 3.99 / 6.42 / 6.19 px (centre/mid/outer) against the shipped route's
  0.29 / 0.63 / 2.10 / 2.99 px, and worst at the CENTRE, which no distortion story
  explains. Isolated: warping ONE member by its own solution and composing it
  against its own unwarped self gives **8.50 / 9.45 / 6.76 px**.
  **HEADLINE CORRECTED — it read *"Siril `register -disto=` IS NOT PER-IMAGE
  REPROJECTION"*, and NEITHER MEASUREMENT ABOVE INVOKES `-disto=`.** Both are
  standalone SIP warps performed outside siril's registration. The px figures are
  untouched and stand; what did not follow from them is a claim about a siril flag
  the evidence never ran. This is the same widening that seeded the
  `seqplatesolve` closure — see the pattern entry under "QA / scope".
  **AND `-disto=` IS THREE VALUES, NOT ONE.** Siril's docs and this rig's own
  `help register` (identical wording, so not a version gap): it takes **`image`**
  (solution in the loaded image), **`file <path>`**, or **`master`** — *"to load
  automatically the matching distortion master corresponding to each image"*.
  `image` and `file` are single shared solutions. **`master` is UNDETERMINED and
  must not be resolved by reading harder:** that wording permits per-image, while
  the platesolving page's *"**This file** can then be used to undistort image**s**"*
  leans shared-but-auto-selected. Both readings survive the text and the binary's
  help. **The probe that would settle it, SPECIFIED AND UNRUN:** set the
  master-distortion path in preferences, place solutions for two frames of
  differing solve, run `register <seq> -disto=master`, and read which solution
  siril reports loading per image — the same console channel the compose gate
  greps at `run_undistort_compose.sh:355`. One run distinguishes per-image from
  auto-selected-shared.
  **CORRECTED — this entry previously read *"Siril's own design therefore assumes
  one optical state per sequence"* and *"Siril has no such command", and both are
  FALSE.** `seqplatesolve` + `seqapplyreg` IS the per-image operation: it derives
  registration from each member's OWN solution and composes that member's OWN SIP
  undistortion with the linear projection in a SINGLE pixel mapping
  (siril.readthedocs.io, Registration). It is the SHIPPED DEFAULT of
  `run_undistort_compose.sh:330`, gated by `compose_preflight.py` and by an exit-4
  assert on siril's own log; `-2pass` survives only behind `--starpair`. Measured
  one-knob on the 28-member union (`02cf170`): star-pair 4.383 px / **0.458**
  roundness at the defect against astrometric 2.678 / **0.974**, control
  0.968 -> 0.961; owner-PASSED (`e04077f`). **The over-generalisation from ONE
  command to "Siril's design" is what travelled** — it was quoted into `TOOLS.md`
  and `BACKLOG:compose-homography-smear` to close the astrometric route, four days
  after that route shipped. The `-disto=` measurement above is unaffected and
  stands; only the generalisation was wrong.
  The industry operation this WAS mistaken for
  — resampling each exposure onto a COMMON output WCS using its own full
  solution (CD matrix *and* distortion) — is SWarp's model, and Siril reaches it
  by a different construction. SWarp IS installed: `/usr/bin/SWarp`, version 2.41.5, from the distro
  `swarp` package — note the capital S and W, since lowercase `swarp` is not on
  PATH and the shell misdirects to suckless-tools.

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

