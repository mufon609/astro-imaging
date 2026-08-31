# Stretch, colour, and judgment surfaces

Part of the dead-end registry — `docs/dead-ends.md` is the index, and
`00-registry-contract.md` governs how entries are read, cited, written and
deleted. Entries are maintained IN PLACE (pre-compression forms are in git;
the pre-split single-file registry is `docs/dead-ends.md`'s own history).
Cross-references to sibling files are written as (`<file>.md`) pointers.

<!-- registry content below; docs/dead-ends.md is the index -->
- **A LAYER THAT HOLDS A SMALL RESIDUAL AMPLIFIES ANY ERROR IN THE LAYER THAT
  HOLDS THE LIGHT — and a single per-channel gain cannot correct a layer with
  two populations.** MEASURED on a separation (Siril `stat main` under
  `fmul 1000` — at plain `stat` the star layer's R/G is
  quantization-limited to ±6%, larger than the effect): linear stack R/G
  0.9992 (the SPCC truth); starless layer 1.0022 (+0.30% red); star layer
  0.8977 / 0.8600 (−10.2%, −13.9%). The split is mass-balanced, so the third
  line is not a stellar colour — it is the second line's 0.30% error levered
  by the mask carrying only ~4% of the stack's level (the arithmetic
  reproduces the measured value exactly). **Two traps found trying to
  correct it, both worth more than the fix:** (1) WRONG STATISTIC — a
  diagonal `ccm` whose gains came from the layer's MEDIAN validated perfect
  on the median while the STARS came out +8.3% R / +11.0% B, visibly neon
  blue, user-caught (a median is robust against exactly the population under
  test); targeting the star-weighted MEAN fixed the stars and pushed the
  FLOOR off — the defect moved, it did not go. A single gain cannot serve
  both populations; REPORT BOTH STATISTICS. (2) WRONG ORDER — the
  populations' colours AGREE on the raw stack and DIVERGE once a stellar
  sharpen runs before the separation (+8.4%/+11.2%): concentrating flux into
  cores changes what the separation assigns to each layer. Sharpen AFTER
  separating, on the star layer only. **Also refuted here:** darkstar's
  colour-true STARLESS does NOT imply a colour-true star layer (its
  cores-vs-floor spread is −18.2%/−30.7% stretched, far worse than
  StarNet2) — do not adopt it as the separator on that inference. SCOPE: one
  dataset, one separation; the leverage ARITHMETIC is general, the specific
  numbers are not.
- **RAISING `star_asinh` TO AMPLIFY THE STAR LAYER IS A DEAD END — it
  destroys the stellar brightness hierarchy and renders a uniform speckle
  field.** The shipped value is 1000; 20000 was tried on the reasoning that
  the star layer carries this field's unresolved starlight (true, R² 0.9631)
  and should be lifted to reveal it (FALSE, and the error). `asinh` is a
  COMPRESSOR: gain runs 1362× at input 1e-4 but only 7.8× at 0.1, so **two
  stars differing 100:1 in real flux render 2.25:1 — a 44× compression of
  dynamic range** (17× at the shipped 1000). Measured consequences, rejected
  on sight at 1:1: no brightness hierarchy, uniform same-size speckle, soft
  blobs, random per-dot colour. (The compression ratios are exact
  arithmetic; two mechanisms — the wing-lift cancelling an upstream sharpen,
  and the random colour being un-denoised star-layer chroma — are INFERRED,
  NOT ISOLATED.) The rule: unresolved starlight is rendered AS STARS,
  preserving the population's hierarchy — never amplified as a diffuse glow.
  A "low" `star_asinh` is what keeps the compressor in a range where stars
  still look like stars; do not reach for the lift when a field looks empty.
- Unlinked autostretch on a calibrated stack is the chroma-blotch
  ("rainbow") engine — after SPCC there is no cast to compensate; use
  linked. Unlinked sky-anchored stretch as a narrowband line-lift is a NO-OP
  (BGE+SPCC already equalize the channel skies; the line imbalance is OBJECT
  flux, not sky).
- SPCC narrowband equalizes O3=Ha and erases the O3 sphere (raw O3/Ha ~1.5 →
  ~1.0; sphere B/R 0.77 vs 3.21). Siril's own docs confirm SPCC-NB gives
  "real intensities"/"a huge green cast" and recommend Manual Color
  Calibration for SHO — for a narrowband SHO target, SPCC is the *cause* of
  the lost sphere, not the fix. (The star-colour-neutral fix is a candidate
  DESIGN, UNTESTED — `TOOLS.md` Tier 10; do
  not cite as a method.)
- `rmgreen`/SCNR on a sky that is not green-dominant prints a global magenta
  cast.
- Siril has NO native GENERAL chrominance-noise tool (its own docs punt to
  GIMP, byte-identical disclaimer in 1.4.4 AND 1.5.0-dev); `rmgreen` is
  SINGLE-HUE and does not close the gap. NEVER hand-roll a chroma coring;
  close the gap with an AI denoiser on x86 (tool options + chroma flags:
  `TOOLS.md`).
- **The stretched judge surface AMPLIFIES background gradients, by a factor
  that grows with sky brightness and stack depth — a flat image can render
  as a visibly tinted, vignetted one.** Autostretch puts its black point at
  ≈ median − 2.8·MAD, so the amplification of a fractional background
  variation goes as sky/noise ∝ √(sky × N). MEASURED: linear
  corner-to-corner spread 0.47% in level / 0.53% in R/G rendering as **7.9%
  and 9.4% — a ~17× gain**; the same chain on a 4×-darker sky amplified 8.7×
  (predicted √4 = 2.0× ratio, measured 1.95). Consequences: a corner "going
  black" on a judge PNG may be ~23% grey and ±0.3% flat in the data, and
  stacking DEEPER makes the artefact worse unless the members' residual
  gradients cancel. **Judge background uniformity from LINEAR regional
  numbers, never from the stretched surface.**
  **The same 1/f amplification applies to CHANNEL differences — a COMMON
  black point renders a neutral sky as a tinted one.** Any per-channel
  fractional sky difference is magnified by ≈1/f (f = how far below the sky
  the black point sits): measured, a linear B/G of 1.0048 renders 1.1147 at
  f=0.0527 (19×) — an 11% visible tint out of half a percent. Setting lo PER
  CHANNEL at the same fraction below each channel's own sky (background
  neutralization, the step the mainstream puts before colour calibration)
  while keeping ONE common window width and midtone renders 1.0057 — +0.09%
  from the truth; the "use linked" rule governs the CURVE and is satisfied
  by the common width/midtone (scaling the width per channel too forces the
  sky to exactly 1.0000, discarding the colour SPCC measured). Corollary: a
  SHALLOWER black point is not free — it preserves faint signal but raises
  this amplification as 1/f; black-point depth trades faint-signal crush
  against background colour fidelity, against the numbers, not by feel.
  **Never read a LINEAR residual off a STRETCHED surface at all** — the same
  class of gradient read corner/centre 1.06 on an autostretched preview and
  **1.27–1.37 linear** on the shipped stack. A display-domain ratio answers
  "what does the eye see", never "how big is the residual": measure with
  Siril `stat` regional medians on the LINEAR image and state the domain
  with the number. (Reverse trap: a pedestal-included ADU ratio understates
  a light-domain falloff — a ~1 EV vignetting read "6.3%" with the
  ~1007 ADU pedestal in.)
- Never judge a denoiser by whole-frame `bgnoise`: the estimator conflates
  revealed texture with noise, so a real denoise can RAISE it (measured on
  one 1024² tile: Siril `denoise` 2.05→2.55 while GraXpert read 1.14 on the
  same input). Judge denoise on a decomposition instrument (the
  `noise_split.sh` structured term must SHRINK while real sky texture
  stays) + the user's eyes on the unresolved starlight at 1:1.
- Never hide a rim defect with a darker sky target or a crop — the rim is in
  the data (estimator extrapolation × stretch amplification), fix it there.
- **A multi-product judgment set rendered by data-dependent `autostretch` is
  NOT like-encoded — each surface gets its own histogram-derived transfer**
  (and unlike encodings lie in general: q92+4:2:0 loses star-edge chroma to
  subsampling). MEASURED: statistically identical linear stacks rendered as
  "rich MW field" vs "single-frame-looking flat gray" purely by the
  per-stack transfer; a fixed-MTF probe against an autostretched PNG
  "refutes" correct hypotheses until re-run like-for-like. Multi-surface
  judgment sets pin ONE stretch RULE for every member — and the rule must be
  SKY-ANCHORED per product, not one raw MTF triplet (separately
  normalized stacks, each at its own reference's sky, sit at different
  levels, so a single triplet renders honest sky-level differences as gross
  brightness differences). With healthy 32-bit statistics, per-product
  `autostretch -linked` at identical parameters IS the pinned rule (its
  16-bit failure was the MAD collapse, not the rule); the render tier's
  stretch policy is the durable home.
- **A JUDGMENT SURFACE IS NOT `load` + `autostretch` + `savepng` — IT IS
  `finish_render.sh`, AND SKIPPING SPCC DOES NOT "REMOVE A VARIABLE", IT
  BREAKS THE RENDER.** Measured: two union surfaces rendered with a linked
  autostretch on the raw stacks came out with channel medians **R 0, G 193,
  B 127** — the shadow clip on uncalibrated OSC data crushed the RED CHANNEL
  TO ZERO. Not a green cast: a dead channel. Through `finish_render.sh`
  (solve → SPCC → linked stretch → full-frame 16-bit PNG) the same stacks
  read R 70 / G 70 / B 69. The reasoning that produced the broken pair —
  "SPCC adds a variable to an A/B, so leave it out" — is backwards: in a
  comparison the variable is controlled by applying the SAME finish to both
  arms, never by deleting a stage from both. Every surface in
  `web/results/<session>/judge/` is `*_spcc-linked.png` for this reason, and
  the naming is the tell. **The second half is what let it reach the user:
  bit depth and dimensions were verified and the images were never OPENED**
  — `file` said "16-bit/color RGB" and that was taken as the check. Look at
  the pixels before calling anything a judgment surface.
