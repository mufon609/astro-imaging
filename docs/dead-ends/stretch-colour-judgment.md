# Stretch, colour, and judgment surfaces

Phase-1 split of `docs/dead-ends.md` (organize-only; the original file stays
the live registry until the merge is decided). Content below the marker is
VERBATIM from the original, so in-text "above"/"below"/section references may
point at entries now homed in a sibling file — `README.md` in this directory
carries the index, the assignment rule, and the block manifest that resolves
them. Do not edit below the marker while the refactor is in phase 1; the split
is re-derivable from the manifest and verified byte-identical by `split.py`.

<!-- == verbatim content from docs/dead-ends.md below this marker == -->
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
- Never judge a denoiser by whole-frame `bgnoise`: the estimator conflates
  revealed texture with noise, so a real denoise can RAISE it (measured on one
  1024² tile: Siril `denoise` 2.05→2.55 while GraXpert denoise read 1.14 on
  the same input). Judge denoise on a decomposition instrument (the
  `noise_split.sh` structured term must SHRINK while confusion texture — real
  sky — stays) + the user's eyes on the unresolved starlight at 1:1.
- Never hide a rim defect with a darker sky target or a crop — the rim is in the
  data (estimator extrapolation × stretch amplification), fix it there.
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

