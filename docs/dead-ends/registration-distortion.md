# Registration and lens distortion (wide-field untracked)

Part of the dead-end registry — `docs/dead-ends.md` is the index, and
`00-registry-contract.md` governs how entries are read, cited, written and
deleted. Entries are maintained IN PLACE (pre-compression forms are in git;
the pre-split single-file registry is `docs/dead-ends.md`'s own history).
Cross-references to sibling files are written as (`<file>.md`) pointers.
Operational forms of the darktable/lensfun and ICC contracts live in
`CLAUDE.md` Environment; this file holds the measured mechanisms behind them.

<!-- registry content below; docs/dead-ends.md is the index -->
- **Wide UNTRACKED edge smear: "field rotation / gnomonic projection" is NOT
  the cause.** For an IDEAL rectilinear lens a pure camera rotation maps
  EXACTLY to an 8-DOF homography (stars at infinity; sky rotation is SO(3),
  linear in homogeneous coordinates) — zero residual. Szeliski, *Image
  Alignment and Stitching* §2.3: the only residual surviving an optimal
  global fit on a star field is **unmodelled RADIAL LENS DISTORTION** — the
  real map is `distort ∘ H ∘ distort⁻¹`. Distortion displaces stars ∝ radius
  → centre sharp, edges smeared; as a star drifts it samples a different
  local distortion and no global fit absorbs the difference. **The fix is
  undistort → homography, NOT a local/elastic transform** (`-transf=` tops
  out at homography, which is already exactly right). MEASURED two
  independent ways on a 43-min/1500-px-drift set: a 9-min window is better
  whole-frame (majFWHM 3.87 vs 4.74 px), and undistorting the frames
  collapses `seqtilt`'s off-axis aberration 0.57 → 0.25 px at FULL depth —
  remove the drift *or* remove the distortion and the homography becomes
  exact, the same statement twice
  ([`wide-field-untracked-registration.md`](../wide-field-untracked-registration.md)).
- **astrometry.net's SIP is NOT a reproducible lens model at wide index
  scales — so `register -disto=` has no model to eat. SUBJECT: SINGLE TRAILED
  FRAMES; on stacked MEMBERS this is SUPERSEDED** — `seqplatesolve -order=3`
  residual ~0.9 px meets this entry's own bar (`plate-solving-wcs.md`, the
  solver-on-stacked-members entry), and members are what the shipped compose
  registers. Fixed tripod (distortion physically identical every frame), yet
  two solves 43 min apart disagree at the same sensor positions by **65 px
  median / 128 px worst** (a real lens model must agree to ~1 px); a
  1500-star cap cut it only to 44 px while sharply improving the LINEAR
  solve — more stars fix the POSITION, not the distortion. Mechanism: the
  SIP tweak is constrained by *matched index* stars, and the 4200-series
  index at ultra-wide scales is Tycho-2-based and sparse. Feeding this SIP
  to `register -disto=` is a measured LOSS (majFWHM 4.74→6.02 px, stars
  17,770→7,561, smear frame-wide). **The lesson: for a wide UNTRACKED field,
  fit-distortion-from-sparse-trailed-stars is the dead end; an OFFICIAL
  *measured* lens profile is the route** (darktable + lensfun, `TOOLS.md`
  Tier 2b) — measured WIN: `seqtilt` off-axis 0.57 → 0.25 px, stars 5095 →
  11805, 54/54 registered. **What the model does NOT buy (same runs):**
  sharpness is NULL (truncated-mean FWHM 3.20 → 3.27 px — the in-exposure
  floor is untouched) and the one-sided component is NOT corrected — a
  radial model cannot fix a one-sided term. It buys star COUNT and radial
  UNIFORMITY, not FWHM.
- **DEAD END — "the aug06 member EDGE deficit is introduced by the
  within-group registration/stack." It is not: the session difference is
  FLAT across the whole chain once the star population is flux-matched.**
  MEASURED, one instrument at three levels (calibrated single → warped
  single → member), edge-minus-centre FWHM, aug06 minus july31:
  **+0.174 → +0.130 → +0.175 px** at a common fitted-amplitude cut; the
  full-population reading that suggested amplification (+0.456 at member) is
  the detection-depth artefact (`star-shape-optics.md`). Also killed in the
  same run: drift span within a group as the differentiator (an 11× span
  increase costs ~0.05 px *equally in both sessions*), and the framing trim
  at matched group size is equal. What survives is small and frame-level:
  nearly equal edges, aug06's CENTRE sharper, a right-edge roundness
  deficit — EXIF records no difference, so the residual candidate is
  focus/field state, which no processing knob reaches.
- **In-exposure trailing is the unremovable FLOOR** — no registration method
  touches it. On a fixed tripod at 6 s / dec +47 / 18″px it is ~3.4 px
  predicted, ~3.6 px measured (per-frame roundness 0.615, uniform across the
  set). Stars are elongated ~1.6:1 at BEST; success is the EDGE matching the
  CENTRE, never round stars. That per-frame roundness is *uniform* is also
  the proof the radial smear is introduced by register+stack, not by the
  frames. **Measure note — the floor's px numbers are not one statistic:**
  ~3.4 is a predicted trail LENGTH; the ~3.6 per-frame FWHM was CFA-sampled
  (Bayer-inflated, relative only — historical; `run_frame_qa.sh` now
  debayers); station values are debayered majFWHM medians (3.4–3.8 px);
  `seqtilt`'s truncated mean mixes axes (3.0–3.1 px). Compare within one
  statistic; the operative claim is edge ≈ centre, never an absolute px
  value across statistics.
- **A community lens profile can fix the edges yet WRITE A NEW DEFECT into
  the centre — the paraxial-error × drift band.** True distortion → 0 at the
  optical axis, so an UNCORRECTED wide-untracked stack has a pristine
  centre; a community radial profile carries a small paraxial error ε(r),
  and as a star crosses the axis during the drift the radial unit vector
  flips sign, turning ±ε into a ~2ε smear ALONG THE DRIFT — a band through
  frame centre, worst there, invisible perpendicular. MEASURED (fixed 350 px
  stations about the geometric centre): full-depth centre majFWHM 5.30 /
  roundness 0.480 vs perpendicular 3.60–4.12; the no-model control INVERTS
  it (centre 4.03, its best). A FAINT-star/texture defect — **`seqtilt` is
  BLIND to it** (off-axis aberration even IMPROVES as the centre degrades
  toward the corners' mean), so never accept a wide-untracked render on
  `seqtilt` alone; measure fixed drift-axis stations
  (`scripts/qa/star_stations.py`). A tracked rig never sees it. **The fix,
  shipped: a model fitted FROM THIS UNIT'S OWN FRAMES by between-frame
  star-correspondence** (`fit_lens_model.sh` → `install_lens_model.sh`;
  authority `lens_models.json`, keyed `<lens>@<focal>` — the per-set-models
  entry below) — removes the band (centre 5.30 → 3.67 px at full depth) and
  sharpens the whole frame. ε-source candidates open (centre-pinned a/b/c
  absorbing the calibrator's decentering; focus-distance; unit variation).
  Also KILLED: the solved effective focal (67.8) as the lensfun key — the
  interpolated 50–70 model is WORSE at the centre; calibrated focal=70 is
  the best community key.
- **A darktable lens STYLE carries NOTHING but the enabled bit.** darktable
  IGNORES the `op_params` blob, re-detects the lens from each image's EXIF,
  and applies its DEFAULT correction set (distortion + TCA + **vignetting**)
  — measured: EXIF focal 70 vs 24 gives opposite-sign fields; `scale` and a
  BLANKED blob give byte-identical output. So ONE style is
  camera/lens/focal-general, and the correction SET cannot be chosen in a
  style — enforce it in the DATA lensfun reads: strip
  `<vignetting>`/`<tca>` from the lens's DB block (`install_lens_model.sh`),
  or the unwanted vignetting DOUBLE-corrects flat-corrected lights
  (corner/centre 1.27–1.37× linear, 2.2–2.6× stretched). Verify after any
  darktable/lensfun bump with `verify_lens_card.py` — **the uniform card
  ALONE is a VACUOUS test**: warping a uniform field yields the same uniform
  field, so corner==centre passes whether vignetting was stripped OR the
  module never fired (measured: pixel-identical `lensdist`/`nodist` renders
  while the module was demonstrably live); it needs the GRID positive
  control that MUST differ (grid sigma ~45.6k) before the uniform card's
  flat corners mean "no photometric correction". Do NOT compare the
  rendered files byte-wise — `cmp` reports pixel-identical renders as
  DIFFERING (TIFF metadata). This checks the correction SET, never its
  CORRECTNESS. Operational form: `CLAUDE.md` Environment.
- **Round-tripping linear astro data through a raw converter: the ICC tag
  and the export profile must CANCEL — and "verified identity" is only as
  good as the LEVELS it was verified at.** Siril's `savetif` embeds an sRGB
  TONE-CURVE profile on LINEAR pixels (and `icc_assign` does NOT change what
  `savetif` embeds); a converter then applies an sRGB→linear DECODE to
  already-linear data, and exporting LINEAR against that input leaves the
  decode UNCANCELLED — measured A_out/A_in climbing 0.1008 → 0.2121,
  silently destroying photometry while looking fine on a preview. The
  16-bit-era rule (match the output profile: `--icc-type SRGB`) verified as
  identity at star amplitudes — and later measured to carry a **TRC
  toe-segment mismatch below linear ≈0.003** (+4.7% at 0.0015 → identity by
  0.003): a 6 s sky sits above the band, a **3 s sky sits inside it** — a
  ~1–2% per-channel global shift invisible to a star-amplitude check. **The
  float-leg contract, adopted and shipped: strip the ICC tag (exiftool, same
  pass as the lens-tag copy) and export `--icc-type LIN_REC709` — a PERFECT
  identity, ratio 1.0000 at every level and channel.** Two traps beside it:
  (1) NEVER strip with siril `icc_remove` before `savetif32` — that leg
  applies a global **~1/12.92** scale to every pixel; (2) verify any ICC
  change with a ratio-vs-level curve DOWN TO the exposure class's SKY level,
  never with star amplitudes or a mean alone — a toe error hides above the
  knee. Operational form: `CLAUDE.md` Environment.
- **Three traps that make a registration comparison lie (all hit one set).**
  (1) **Survivorship bias** — a bad registration spreads flux below the
  detection threshold, so the SURVIVING stars' median can *improve* while
  the image gets worse (the `-disto=` LOSS above showed a BETTER edge
  median, 4.61 vs 6.46 px, on a destroyed frame). Read a star-shape metric
  with its **n** and confirm on full-frame crops.
  (2) **Area confound** — `-framing=min` gives each variant a DIFFERENT
  frame size (less drift ⇒ larger intersection), so raw counts aren't
  comparable (a short-window stack's higher count was entirely its 56%
  larger frame; per Mpx it was LOWER). Compare **stars per Mpx**, and open
  the detection gate (`setfindstar -roundness=0.05 -relax=on`) when
  measuring elongation or the metric silently rejects the stars under test.
  (3) **Circular metric** — a radial profile binned about the `findstar`
  BOUNDING-BOX centre has an origin that MOVES with the defect (the smear
  suppresses edge detections → box shrinks → origin shifts; **537 px**
  measured from a detection-sigma change alone), after which it reads
  roundness *improving* outward on a stack whose right third has no
  detections. Never key a metric to a geometry derived from the measurement
  itself — use a FIXED external origin or the tool's own measure (`seqtilt`,
  no origin to get wrong, but WHOLE-FRAME and blind to a drift-aligned
  band). Star count per radial bin is not a quality measure either — it is
  sky density × detection efficiency, which peaks where the sky is poorest.
- **PER-SET LENS-DISTORTION MODELS — REFUTED AT THE ROOT, REVERTED.** The
  doctrine ("the lens model keys on the OPTICAL STATE, per set") was
  generalised from ONE number: aug06/set-01 measuring 0.82 px off-axis under
  the pinned model, read as a state change. **It is not:** every one of
  set-01's five groups reads 0.40–0.45 px under that same model —
  indistinguishable from set-02's — and the 0.82 exists only in the
  500-frame product, i.e. it is created at the group→set compose (the
  chronology said so first: 0.48 → 0.82 → 0.57 → 0.60 across sequential
  sets, and a focus change is a STEP, not a spike that returns). The
  adoption A/B then read 1 WIN / 3 NULL yet gave all four sets their own
  model, and that heterogeneity is what broke the combine: **2.99 px corner
  disagreement within a night, 5.34 px across nights, visible star doubling
  the owner failed by eye — against 0.93 / 0.71 px for the same pairs under
  one model.** Compounding it: a fitted model is not reproducible to better
  than ~3 px in the outer field (entry below), so the coefficient
  differences never discriminated a state from a fit. **What is NOT dead:
  fitting a model from a set's own frames** — that made the shipped model
  that beat the community profile on the owner's eyes. What died is
  treating each SET as its own optical state by default. **The authority is
  `scripts/darktable/lens_models.json`, keyed `<lens>@<focal>`; a fresh fit
  is a CANDIDATE promoted by an explicit act, judged at the COMBINE — never
  on a per-set product, where a compose artifact masquerades as optics.**
- **NEVER compose sub-stacks that were warped under DIFFERENT distortion
  models.** From the compose's point of view the model is a property of the
  COMBINE, because a global homography cannot absorb a radial field.
  MEASURED (one knob, byte-identical group membership, same two pointings,
  only the installed model differing): the px separation of the SAME star as
  two registered members place it, at the composed canvas corner, is
  **2.99 px under per-set models and 0.93 px under one shared model**
  (same-set pairs 0.1–0.2 px, so neither the compose nor Siril's
  registration is implicated); by eye the own-model corner shows
  multi-component dashes, the single-model corner round single stars. The
  cause is structural: **lensfun normalises the ptlens radius by HALF THE
  SHORT SIDE** — measured by probe (fitting all four installed models at
  once: RMS 4.47 px for half-short-side against 18.3/22.2 for the
  alternatives; a free normalisation lands at 2000 px against 2020) — so
  the frame CORNER sits at ρ = 1.80 while hugin's control points constrain
  only to ρ ≤ 1.0: the cubic extrapolates 80% past its support exactly at
  the corners, and fits interchangeable inside the supported field diverge
  freely outside it (measured model-pair divergence through the production
  warp reaches 8.2 px). Corollary: a fit's own residual (0.02–0.10 px) is
  computed only where control points exist and says NOTHING about the
  corners.
- **FITTING A LENS MODEL AGAINST A PLATE SOLUTION WITH AN AFFINE NUISANCE
  MANUFACTURES A DECENTRING SIGNAL. Use a HOMOGRAPHY.** The linear WCS is a
  gnomonic projection about ITS tangent point; the ideal camera frame a lens
  model lives in is a gnomonic projection about the optical axis; two
  gnomonic projections of the same sky differ by a plane projective
  transform EXACTLY (the same Szeliski result, one level down). Over ±14°
  the projective part reaches ~180 px — an affine nuisance cannot absorb
  it, and what it leaves is **quadratic and EVEN in x**, indistinguishable
  by eye from decentring and partly absorbable by Brown's tangential pair.
  MEASURED, same 970 catalogue-matched pairs, one knob — the nuisance:

  | nuisance | ptlens RMS | median | free centre it "finds" |
  |---|---|---|---|
  | affine (6 DOF) | 14.24 px | 7.63 px | **(+210, −164) px** |
  | homography (8 DOF) | 3.19 px | **0.27 px** | **(−6, +14) px** |

  The median improves 28× and the "decentring" collapses to consistent with
  zero — **a centred ptlens model already describes this lens to a 0.27 px
  median.** RETRACTS the earlier reading of this same data (an
  "irreducible" 8 px residual, a reproducible ~180–240 px centre offset, an
  even-in-x term "no radial model can produce"): every one was the
  unabsorbed projective term, and it reproduced across frames precisely
  because every frame's linear WCS has a similar tangent-point offset.
  **Reproducibility across frames does NOT distinguish a lens property from
  a projection artefact.** Do not re-derive a lens model against a plate
  solution without a projective nuisance, and do not read an even-in-x
  residual as decentring until one is in the fit. Instrument:
  `scripts/qa/fit_ptlens_joint.py`.
- **lensfun's `<center>` element EXISTS and WORKS in 0.3.4 — and installing
  it on top of coefficients fitted for centre=0 is a LOSS in every
  direction.** (The decentring it was chasing is dead — entry above.) The
  element is absent from lensfun's shipped DTD/XSD but is parsed and
  applied; darktable honours it; the distortion origin is
  `Width/2 + CenterX·(size/2)` with `size` = image height (2020 px here,
  independently confirming the radius-normalisation probe); axes are
  darktable's image convention (x right, y DOWN). MEASURED through the
  production invocation: no centre 2.59 px RMS against 4.24–7.61 for all
  four trial signs — all worse, and the solve degrades too. MECHANISM:
  **a,b,c are fitted ABOUT a centre** — moving the centre under coefficients
  fitted for centre=0 is a different model, not a refinement. The joint
  refit that would have used it puts the centre at (−6, +14) px — zero — so
  the element has no live use on this lens; the tool facts stand, and
  `install_lens_model.sh --center X,Y` writes it if a future lens needs one.
- **A STANDALONE PER-MEMBER SIP WARP, APPLIED OUTSIDE SIRIL'S REGISTRATION,
  IS WORSE THAN THE SHIPPED ROUTE — the polynomial is not
  identity-preserving alone.** Applying each member's OWN SIP as a
  standalone warp and composing measured **3.99 / 6.42 / 6.19 px**
  (centre/mid/outer) against the shipped route's 0.29–2.99 px, worst at the
  CENTRE, which no distortion story explains; warping ONE member by its own
  solution against its own unwarped self gives 8.50 / 9.45 / 6.76 px.
  **HEADLINE CORRECTED — it read "Siril `register -disto=` IS NOT PER-IMAGE
  REPROJECTION", and neither measurement invokes `-disto=`** (the widening
  that seeded the `seqplatesolve` closure — the SUBJECT axis,
  `00-registry-contract.md`). **`-disto=` IS THREE VALUES:** `image` and
  `file` are single shared solutions; **`master` — "load automatically the
  matching distortion master corresponding to each image" — is UNDETERMINED
  and must not be resolved by reading harder** (the wording permits
  per-image; the platesolving page leans shared-but-auto-selected; both
  survive the text and the binary's help). The probe that would settle it,
  specified and unrun: solutions for two frames of differing solve,
  `register -disto=master`, read which solution siril reports loading per
  image. **ALSO CORRECTED AS FALSE: "Siril's own design assumes one optical
  state per sequence" and "Siril has no such command"** —
  `seqplatesolve` + `seqapplyreg` IS the per-image operation, deriving
  registration from each member's OWN solution and composing that member's
  OWN SIP undistortion with the linear projection in a single mapping
  (siril.readthedocs.io, Registration); it is the SHIPPED DEFAULT, guarded,
  owner-PASSED (numbers: `stacking-compose.md`, the mosaic entry). The
  over-generalisation from ONE command to "Siril's design" is what
  travelled into other records to close the astrometric route four days
  after that route shipped; the `-disto=` measurement above stands, only
  the generalisation was wrong. The industry operation this was mistaken
  for — resampling each exposure onto a common WCS with its own full
  solution — is SWarp's model, and Siril reaches it by a different
  construction. (SWarp IS installed: `/usr/bin/SWarp` 2.41.5 — capital S
  and W; lowercase `swarp` misdirects to suckless-tools.)
- **A FITTED ptlens MODEL IS NOT REPRODUCIBLE TO BETTER THAN ~3 px IN THE
  OUTER FIELD, so a coefficient comparison cannot tell an optical STATE
  from a FIT.** Four independent fits of ONE set (same night, same frame
  pool; only the frame subset and prune varying): pairwise peak displacement
  difference **0.36–6.30 px, median 3.22**, where the between-set models
  differ by 4.01–10.99, median 7.04 — the distributions OVERLAP, and both
  exceed the 0.47 px equivalence bound the per-set doctrine was adopted
  against by 7–23× (sharpest: a refit of set-01 lands 0.83 px from set-02's
  shipped model and 3.26 px from set-01's own). Per-set granularity is not
  refuted (between-set is systematically larger), but **fit reproducibility
  is a PREREQUISITE for any per-state model work — ±3 px of procedural
  uncertainty is the same size as the 2.99 px member disagreement it must
  fix.** A fit's own residual (0.02–0.10 px) says nothing about this: it is
  computed only where the control points are.
- **CORNER CONTROL POINTS CANNOT BE RECOVERED BY REORDERING OR RELAXING
  `cpclean`** — the corner-support deficit is a MATCHING problem, not a
  pruning one. `cpfind`'s raw points do reach the corner (ρ_max 1.60–1.78)
  and `cpclean` removes essentially all of them; decomposed, step 1
  (pairwise) removes ONE point of 225 and keeps corner support — **step 2
  (whole-panorama) is the whole effect** — but the tempting mechanism
  ("step 2 judges against a model with no a,b,c") is REFUTED: seeding step
  2 with a fitted a,b,c removes the same population, and the `-n` threshold
  is exhausted (n = 3–8 all return the identical 178 points). Those corner
  points have large residuals under *any* model — predominantly bad SIFT
  matches on aberrated, low-SNR corner stars — and keeping them anyway is a
  measured dead end: the pairwise-only fit is DEGENERATE (a = −1.02 against
  shipped ~0.001–0.02). A corner-true fit needs corner CORRESPONDENCES that
  are actually good.
