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
are not all the same kind of thing, and for three sessions they were formatted as
if they were. Three classes:
- **MEASURED** — an actual controlled comparison with numbers and a named
  instrument. Cite freely, within its stated scope.
- **MECHANISM** — a physical or tool-behaviour argument, sometimes with a
  worked example, but no controlled A/B on this data. Reasonable to act on;
  NOT evidence, and it should not be quoted as a result.
- **DOCTRINE** — a practice adopted from vendor documentation or the field's
  consensus. Legitimate, but its authority is the source, not our data.
An entry with no numbers and no hedge is MECHANISM or DOCTRINE, whatever its
tone. An audit on 2026-08-03 found 28 such entries reading as established
results; the load-bearing ones are now flagged in place. **Anything asserting a
result should carry its n, its instrument and its scope — and if a claim covers
one dataset, it says so.**

**TERMINOLOGY — the word "dust" is BANNED in this repo, and this entry says why.**
For three sessions the registry used "cosmic dust", "MW", "IFN" and "dust-safe"
interchangeably for FOUR physically unrelated things. The term was never defined,
was never independently identified, and its whole doctrinal chain traced back to a
citation (`[[preserve-cosmic-dust-is-the-priority]]`) pointing at a machine-local
memory file that no longer exists. Everything downstream of it — the background
class limit, the GraXpert-Division rejection, the sky-flat enabling condition, the
denoise strength limit — rested on a term nobody had measured. Use these four
instead, and say which one you mean:

**WHERE THE WORD CAME FROM (user, 2026-08-03) — it was an ACQUISITION artefact,
not a sky object.** The term entered this project from early wide-field frames shot
at **24 mm, 20+ s, ISO 200**. At that focal length the plate scale is ~3x coarser
than the 70 mm work, so the star field below the detection limit never resolves and
reads as a smooth diffuse "dust". The same sky at **70 mm, ISO 1600** resolves those
same features into individual stars — which is exactly what sense 2 below then
MEASURED against Gaia. So "Milky Way dust" was never a thing that exists; it was
undersampled starlight, and the word survived a change of optics that had already
falsified it. There is no Milky Way dust. There is nebular EMISSION (sense 3), there
is real interstellar dust seen in SILHOUETTE (sense 4), and there are faint stars
(sense 2). A term that is an artefact of one focal length must not set doctrine for
another.

1. **OPTICAL DUST MOTES** — physical dust on the sensor or optics. A flat-field
   feature, fixed in SENSOR coordinates. Well defined and routinely measured
   (`findstar` speck counts on the flats). This is the only sense in which
   "dust" was ever correct, and it has nothing to do with the sky.
2. **UNRESOLVED STARLIGHT** — the frame-filling faint diffuse field. At this
   data's 17.0"/px in the galactic plane it is the integrated light of Milky Way
   stars fainter than the detection limit. **MEASURED (july23 set-01+02, Gaia DR3
   vs Siril, `qa_work/dust_identification.json`): the star layer's per-cell
   diffuse floor tracks Gaia's unresolved-starlight prediction at R² 0.9631 over a
   140-cell external lattice; detection limit G ≈ 11.0 at 50% completeness (one-to-
   one matched); ~0.2 catalogued sources per PIXEL brighter than G=17.** It is
   STARS — not dust, and not nebulosity.
   SCOPE, stated because it is easy to over-read the R²: flux and source-count
   predictors are 97.7% collinear in this field, so that fit constrains rather than
   proves "flux specifically" — the clean separation is UNRESOLVED flux (R² 0.963)
   beating TOTAL flux (R² 0.503), which is not a collinear pair. The integrated
   starlight figure of 22.74 mag/arcsec² is ONE 0.25° cone at the field centre; no
   frame-wide value was computed. The absolute photometric scale carries a 20-30%
   systematic (Gaussian-fit photometry on trailed stars) — every CORRELATION above
   is scale-free and unaffected, but any ADU prediction derived from it is not.
   ONE dataset, one field, one pixel scale.
3. **HII EMISSION** — NGC 7000, IC 1318 and the like. Real diffuse emission,
   LOCALIZED, Hα-red. Measured on ONE region only: NGC 7000 sits +2.5σ above the
   starlight relation and reads R/G 1.1918 against a 0.9303 field. **SCOPE — this
   is 1 of 3 regions tested, and the other two did NOT stand out** (IC 1318 −0.07σ,
   NGC 6888 −0.72σ), partly because the 1.4° cells are coarse for objects that size
   and my IC 1318 and "dark lane" test coordinates landed in the SAME cell. So the
   honest claim is: emission IS separable from starlight by this instrument on a
   large bright region, and the instrument was not shown sensitive enough for
   smaller ones. A nebula is not dust and is not "IFN" regardless — that part is
   definitional, not measured.
4. **DUST SILHOUETTE** — real interstellar dust, which at this scale appears as
   ABSENCE, not emission: the Cygnus Rift dark lanes. **NOT PROPERLY MEASURED —
   treat as a working model, not a result.** What exists: Gaia integrated flux in
   0.3° cones runs lowest near the plane (1.76e-3 at b=−2 against 1.27e-2 at
   b=−10), which is CONSISTENT with foreground extinction. But those cones are
   small enough to be dominated by their few brightest stars — noted as noisy when
   taken — and no test separated extinction from ordinary structure in the stellar
   distribution. The physical expectation (dust obscures rather than emits at
   17"/px) is textbook and is why this sense belongs in the list at all; the
   NUMBERS above do not establish it. The test that would: per-cell Gaia flux
   against a reddening map, or Gaia's own extinction estimates, over the same
   lattice used for sense 2.

**The rendering consequence, and it is not optional.** Sense 2 is stars, so it is
rendered AS STARS — preserving the brightness hierarchy of the population. It is
NOT a diffuse glow to be amplified. Treating it as one produced a uniform
speckle-field with no hierarchy and was rejected on sight (see the `star_asinh`
entry under "Stretch / colour").

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
  the flat, and division then ATTENUATES it. The only fix is manual clone-stamping
  (GUI, non-reproducible). So a sky flat is safe for this class ONLY when faint
  structure is a small part of the frame; validate before use
  ([`synthetic-flats-and-bias.md`](synthetic-flats-and-bias.md)).
  **CORRECTED 2026-08-03 — what gets attenuated is UNRESOLVED STARLIGHT, not
  "cosmic dust".** The original wording asserted a dust complex that was never
  measured and does not exist in this field (terminology entry above). The
  MECHANISM stands unchanged — a frame-filling signal cannot reject out of a
  median of un-registered lights, whatever it is made of — but the thing at risk
  is the integrated light of stars below the detection limit, which is ~81% of the
  catalogued starlight here. Naming it correctly matters because the two imply
  opposite handling: diffuse emission would be protected by smoothing, whereas
  starlight is protected by keeping stars resolvable.
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
  The clean fix is a REAL flat (the sky-flat builder's existing removal
  condition). Where sky flats must be used, the flat's low-order ODD component
  has to be removed before use, and the sky gradient handled ADDITIVELY (a
  background step), never multiplicatively by the flat.
- A sky flat applied ACROSS SETS imprints the SOURCE set's sky. The flat's
  low-order component carries the residual sky gradient of the lights it was
  built from; the sensor-fixed content (vignetting/motes/PRNU) transfers between
  same-session sets but the sky term does NOT — dividing another pointing's
  lights by it prints that gradient into them. Measured (one knob, linear
  regional medians on the SPCC'd stacks): set-03 under set-01's flat = ±6% L-R
  tilt (corners 88–101 on a ~94.5 centre); under its own flat = flat to ~1–2%;
  stars +8%/Mpx, off-axis aberration 0.49 → 0.37 px
  (`datasets/july14/set-03/experiments.jsonl` flat_source_set03). **USER-RATIFIED
  RULE: a flat calibrates ONLY the exact frames it was built from** — never
  another set, and never a multi-set combine under any single set's (or a
  union) flat: each member set calibrates with its OWN flat before composing.
  Per-set builder with validation gates: `scripts/stack/build_sky_flat.sh`.

**Calibration masters:**
- **NEVER store a calibration master at 16-bit integer.** A master dark/bias/flat
  is a many-frame MEAN, so its precision is far finer than one integer step;
  rounding to 16 bits does not lose "a bit of noise", it stores a SENSOR-FIXED
  quantization pattern that is then subtracted (or divided) identically into
  every light — the input to walking noise, which no rejection or cosmetic
  correction removes. MEASURED on a 200-frame master dark: the 16-bit-vs-32-bit
  difference is exactly uniform ±0.5 ADU (σ 0.2889 vs theory 1/√12 = 0.2887,
  zero bias), against a split-half-measured statistical floor of 0.4213 ADU —
  so 16-bit storage inflates the master's fixed-pattern residual
  0.4213 → 0.5109 ADU, **+21%**. The error is per-pixel RANDOM, not low-order:
  it vanishes in a flat's 400 px regional medians (L-R 0.9974 both ways), so it
  cannot cause — or be cured by — any gradient or colour-cast symptom. Enforced
  by `scripts/stack/check_bitdepth.sh`; if a rig genuinely cannot afford 32-bit
  that is a new adaptation needing its own written removal condition.
- **The near-miss that made the above expensive: a fix that lives in a session's
  scratch dir is not a fix.** The 16-bit retirement reached the light path but
  missed the master templates. One session hit it, worked around it with a
  session-local builder pinning `set32bits`, and that builder's own comment
  claimed it was "identical to" the repo template it directly contradicted — so
  the repo went on emitting 16-bit masters for every later session while the
  correct behaviour sat in one session's work dir. Graduate the fix or write a
  guard; a corrected comment fails silently, a guard fails loudly (this one
  immediately caught four more unfixed sites its author had already missed).

**Background:**
- **MECHANISM, NOT MEASURED** (flagged 2026-08-03): the galactic-plane star field
  is frame-scale curvature at wide focal, so `seqsubsky 2` is expected to absorb
  it and only a first-degree plane or a full BGE to preserve it. What would be
  preserved is UNRESOLVED STARLIGHT (terminology entry above), not a dust complex.
  **No controlled degree-1-vs-degree-2 comparison on this data is on record** — no
  numbers, no instrument, no n. This entry has been gating the background policy
  (and the README class limit) as though it were a result. The test that would
  settle it: one knob, `seqsubsky 1` vs `2` on the same frames, judged on the same
  Gaia-vs-cell instrument used for the terminology entry, since that measures the
  very signal at issue.
- **MECHANISM, NOT MEASURED** (same flag): stack-level-only BGE is reported to
  leave a structured residual with visible rings and to eat the same frame-scale
  starlight, making per-frame `subsky 1` the preferred step. "Visible rings" is an
  unrecorded eye observation — no image, no metric, no n. Treat the per-frame
  default as a reasonable prior, not an established result.
- **`seqsubsky` DITHERS BY DEFAULT — the opposite of `subsky`, and the dither is
  UNSEEDED, so a per-frame background step silently makes every calibrated frame
  irreproducible.** `subsky` takes an opt-IN `[-dither]`; `seqsubsky` takes an
  opt-OUT `[-nodither]`, so reasoning from one command's signature to the other
  inverts the default. MEASURED (two real frames, four independent runs, Siril's
  own `isub` + `stat`): the calibrated INPUT is bit-identical run to run (`isub`
  all-nil, so the difference is attributable to `seqsubsky` alone), yet two runs
  of plain `seqsubsky pp_c 1` differ by **σ 0.4 ADU** (min −1.0, max +1.0) while
  two `-nodither` runs are bit-identical; default-minus-`-nodither` is a uniform
  **[0,1] ADU** term (mean +0.5, i.e. NOT zero-mean — normalization absorbs it).
  Siril states it in the log as `dithering: enabled`/`disabled` — read that line,
  it is the only warning. The dither exists to break quantization terracing when a
  smooth model is subtracted from coarsely quantized data; that case needs the
  step to be comparable to the noise, and here the frames' own **bgnoise is 17.7
  ADU on a 42.7 ADU sky — 35× the 0.5 ADU step**, so there is no terracing to
  break. Pin `-nodither` in every generated `.ssf`: it buys nothing on this data
  and costs the no-unseeded-step requirement, which had already cost `subsky` its
  `-dither` once. Photometrically it is negligible either way
  (0.4/√401 = 0.02 ADU = 0.047% of sky, below the chain's own 0.073% flat-sky
  run-to-run floor) — this is a reproducibility rule, not a photometry one, and
  flats built before the pin do NOT need rebuilding for that reason.
- GraXpert AI smoothing is NOT faint-signal protection — smoothing blurs the
  model OUTPUT, not the inference; frame-filling faint structure reads as the
  trained light-pollution class and is absorbed. Use a plane/off for
  object-filling fields. BGE does NOT absorb a centred galaxy's halo (it measures
  STRONGER against a lower far-field sky).
- **GraXpert AI `-correction Division` as a synthetic flat on a field filled with
  UNRESOLVED STARLIGHT absorbs most of the extended structure — measured, even at
  max smoothing.** (Wording corrected 2026-08-03: the measurement below is
  unchanged and stands; what it ate was integrated starlight, not a dust complex.)
  Four-arm probe (july23 set-03, 60-frame stacks, same chain, one knob):
  NAN-region contrast as % of local sky R/G/B — own sky flat 8.5/2.9/5.6; GraXpert
  Division (smoothing 1.0, AI 1.0.1) **2.4/0.7/2.1** — the division ate ~2/3 of the
  nebula while flattening corners to ±2% (it flattens the REAL sky structure too;
  perfectly flat corners on a MW field are themselves a defect signature). The
  vignetting-only promise holds only where faint structure does not fill the frame
  — same enabling condition as the sky flat. UNTESTED alternative: GraXpert's
  classical grid interpolators via `-preferences_file` (RBF/spline, no AI model).
  Also measured in the same probe: the 16-bit intermediates chain (same flat, same
  frames) reads only ~55-70% of the 32-bit arm's extended contrast (4.8/2.4/3.9 vs
  8.5/2.9/5.6) — integer round-tripping through calibrate/warp/register eats faint
  signal; the arm-era adaptation cost real structure, not just +0.3% noise.
- On a union/max canvas, CROP to the verified coverage frame BEFORE any
  background step: `subsky`'s sample grid ingests the canvas's zero-coverage
  rims — its `-tolerance` excludes only BRIGHT outliers, not empty sky — and
  the fit skews. Crop-before-background is the pinned order.

**Stretch / colour:**
- **A LAYER THAT HOLDS A SMALL RESIDUAL AMPLIFIES ANY ERROR IN THE LAYER THAT HOLDS
  THE LIGHT — and a single per-channel gain cannot correct a layer with two
  populations.** MEASURED on the july23 separation (Siril `stat main` under
  `fmul 1000`; at plain `stat` the star layer's medians print 1.6/1.7/1.5 and its
  R/G is quantization-limited to ±6%, larger than the effect):
  linear stack median R/G 0.9992 / B/G 0.9988 (the SPCC truth); starless layer
  1.0022 / 1.0048 (+0.30% red); star layer 0.8977 / 0.8600 (−10.2%, −13.9%).
  The split is mass-balanced, so the third line is not a stellar colour — it is
  the second line's 0.30% error levered by the mask carrying only ~4% of the
  stack's level: `(0.9992·G − 1.0022·G_less)/(G − G_less) = 0.9306` reproduces the
  measured value from the other two.
  **Two traps found trying to correct it, both worth more than the fix.**
  (1) WRONG STATISTIC: a diagonal `ccm` whose gains came from the layer's MEDIAN
  (its diffuse floor) was applied to the whole layer including the star cores.
  Validated on the median alone, it reported a perfect 1.0001/0.9992 while the
  STARS came out +8.3% R / +11.0% B — visibly neon blue, user-caught. Mirror of the
  halo-photometry entry below: a median is robust against exactly the population
  under test. Targeting the star-weighted MEAN instead fixed the stars (0.9991/
  0.9991) and pushed the FLOOR off (0.9226/0.8986) — the defect moved, it did not
  go. A single gain cannot serve both populations; REPORT BOTH STATISTICS.
  (2) WRONG ORDER: the populations' colours AGREE on the raw stack (cores-vs-floor
  spread −1.1%/+0.0%, so one gain is valid there) and DIVERGE once a stellar
  sharpen runs before the separation (+8.4%/+11.2%), because concentrating flux
  into cores changes what the separation assigns to each layer. Sharpen AFTER
  separating, on the star layer only (measured spread then −3.1%/−3.7%).
  **Also refuted here:** darkstar's colour-true STARLESS (0.9990/0.9987) does NOT
  imply a colour-true star layer — its cores-vs-floor spread is −18.2%/−30.7%
  stretched, far worse than StarNet2. Do not adopt it as the separator on that
  inference. NOTE the scope: all of this is ONE dataset and one separation; the
  leverage ARITHMETIC is general, the specific numbers are not.
- **COSMIC CLARITY'S CLI ARGUMENTS ARE NOT A CONTROL SURFACE — verify every one
  against output before trusting it.** Three found on one rig: `--sharpening_mode`
  IGNORED (the Qt dialog's value wins); `--color_denoise_strength` SATURATED above
  ~0.85 (0.85 and 1.00 byte-identical); and the sharpen binary BLOCKS on a modal
  dialog so it cannot run unattended at all (`TOOLS.md`). Two of the three fail
  SILENTLY — the tool reports success and produces output, just not the output you
  asked for. The saturation was caught only because two band measurements agreed
  to three decimals across all three channels, which is a no-op signature rather
  than a null result; md5 + Siril `isub` confirmed it. **Cheap guards, both learned
  the expensive way: probe a new neural tool with an EMPTY input directory first
  (a working one reports "no files" in seconds — this one hangs), and check
  `uptime` before concluding a tool is broken (a first pass at the above was
  attributed to the binary while the box sat at load average 300 from an unrelated
  job, costing ~30 min of CPU and a wrong registry entry that had to be retracted).**
- **RAISING `star_asinh` TO AMPLIFY THE STAR LAYER IS A DEAD END — it destroys the
  stellar brightness hierarchy and renders a uniform speckle field.** The shipped
  value is 1000; 20000 was tried on the reasoning that the star layer carries this
  field's unresolved starlight (true, R² 0.9631) and should therefore be lifted to
  reveal it (FALSE, and the error). `asinh` is a COMPRESSOR: gain runs 1362× at
  input 1e-4 but only 7.8× at 0.1, so **two stars differing 100:1 in real measured
  flux render 2.25:1 — a 44× compression of dynamic range** (17× at the shipped
  1000). MEASURED consequences, all visible at 1:1 and rejected on sight: no
  brightness hierarchy, uniform same-size speckle, soft blobs rather than points, and
  random per-dot colour. The compression ratios are ARITHMETIC from the asinh
  transform and are exact; the visual consequences were user-judged on full-frame
  finals. TWO MECHANISMS HERE ARE INFERRED, NOT ISOLATED BY EXPERIMENT: that the
  wing-lift (~1362× at the faint end vs 7.8× at 0.1) is what cancels an upstream
  sharpening — no before/after FWHM was measured ON THE RENDER, only on the linear
  layer; and that the random colour comes from the star layer being amplified with
  its chroma noise intact — the tier does denoise only the starless layer (a
  structural fact, readable in the script), but no arm isolated that as the cause.
  Both are plausible and neither was controlled.
  The rule this establishes: unresolved starlight is rendered AS STARS, preserving
  the population's brightness hierarchy — never amplified as a diffuse glow. A
  "low" `star_asinh` is not timidity; it is what keeps the compressor in a range
  where stars still look like stars. Do not re-attempt the lift, and do not
  reach for it when a field looks empty.
- Unlinked autostretch on a calibrated stack is the chroma-blotch ("rainbow")
  engine — after SPCC there is no cast to compensate; use linked. Unlinked
  sky-anchored stretch as a narrowband line-lift is a NO-OP (BGE+SPCC already
  equalize the channel skies; the line imbalance is OBJECT flux, not sky).
- SPCC narrowband equalizes O3=Ha and erases the O3 sphere (raw O3/Ha ~1.5 →
  ~1.0; sphere B/R 0.77 vs 3.21). Siril's own docs confirm SPCC-NB gives "real
  intensities"/"a huge green cast" and recommend Manual Color Calibration for
  SHO — i.e. for a narrowband SHO target, SPCC is the *cause* of the lost sphere,
  not the fix. (The star-colour-neutral fix is a candidate DESIGN, UNTESTED —
  `docs/narrowband-star-neutral-options.md`; not settled, do not cite as a method.)
- `rmgreen`/SCNR on a sky that is not green-dominant prints a global magenta cast.
- Siril has NO native GENERAL chrominance-noise tool (its own docs punt to GIMP,
  byte-identical disclaimer in 1.4.4 AND 1.5.0-dev). `rmgreen` IS a native
  SCNR-style filter but SINGLE-HUE (green cast only) — it does not close the general
  chroma gap. NEVER hand-roll a chroma coring; close the gap with an AI denoiser on
  x86 (tool options + their chroma-vs-luminance flags: `TOOLS.md`).

**Separation** (informs the x86 tool choice):
- **MECHANISM, NOT MEASURED** (flagged 2026-08-03): a mask+inpaint separator is
  reported to destroy resolved-object structure (inpainting HII knots out as stars
  and screening them back as blobs), where a learned separator (StarNet2/StarXT)
  keeps field-star flux and far less object structure — hence use the learned one
  on resolved objects. No side-by-side numbers are recorded. The conclusion is
  consistent with how the two methods work and with the fact that the shipped
  chain's StarNet2 separation measures cleanly, but it is not a controlled result.
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
  (`extractor_ab.json`). Robustness ranking: (1) asnet + **sep** xylist — the sole extractor
  (the in-house peak-xylist fallback is RETIRED: sep passed every x86 solve
  at equal-or-higher odds, identical SPCC K); (2) `image2xy` xylist (shape-blind, untested — its
  trail knobs `-a`/`-p`/`-m` aren't exposed by solve-field and `-a` can fragment one trail
  into spurious detections); (4) `-localasnet` and ASTAP LEAST — both PSF-fit/roundness-gated
  (ASTAP docs: *"star streaks … will be ignored"*; wide DBs W08 FOV>20°, G05 FOV>6°, G17/H17/H18
  deprecated). Caveats: `--no-remove-lines --uniformize 0` (or list filters) still thin a
  supplied xylist; and two valid fits' centres can differ by hundreds of arcsec (the SIP
  wobble below), which never reaches SPCC (it re-matches stars from the seed).
- **Siril SPCC SIGSEGVs (exit 139) in aperture photometry when the sensor DATABASE
  is missing — not a data/field bug.** MEASURED on a fresh x86 rig: the crash hit
  at "Applying aperture photometry to N stars" on ANY star count (5305, 106, 291),
  any field size (full 20° or a 7.5° crop), and single- or multi-thread — because
  siril's SPCC sensor/filter/white-reference database dir was absent, so it applied
  a `(null)` sensor response and dereferenced it. The catalog (Gaia chunks) being
  present is NOT enough; the sensor database is a SEPARATE git repo. The tell is
  `spcc_list oscsensor` returning EMPTY and a log line "Unable to open directory:
  .../siril-spcc-database". Fix = clone it (CLAUDE.md Environment, SPCC
  prerequisites). Do NOT chase the star count, field width, catalog format, or bit
  depth — all ruled out; the crash prints nothing useful and mimics a data bug.
- 1-pass sequence-start registration strands drifting tail frames; 2-pass + low
  detection sigma recovers them; on trailed frames a reference sweep beats the
  auto-reference. Keep all frames (dropping a minority sub-focal subset buys no
  matching gain and pays the full √N noise penalty).
- **Wide UNTRACKED edge smear: "field rotation / gnomonic projection" is NOT the
  cause.** For an IDEAL rectilinear lens a pure camera rotation maps EXACTLY to an
  8-DOF homography (stars are at infinity; sky rotation is SO(3), linear in
  homogeneous coordinates) — zero residual. Szeliski, *Image Alignment and
  Stitching* §2.3, names the residuals that survive an optimal global fit, and for
  a star field only one applies: **unmodelled RADIAL LENS DISTORTION**. The real
  map is `distort ∘ H ∘ distort⁻¹`. Distortion displaces stars ∝ radius → centre
  sharp, edges smeared; as a star drifts it samples a different local distortion
  and no global fit absorbs the difference. So the fix is **undistort → homography**,
  NOT a local/elastic transform. Do not chase "better global transforms"
  (`-transf=` tops out at homography, which is already exactly right).
  MEASURED on a 43-min/1500-px-drift set, two independent ways: a 9-min
  (310 px) window is better whole-frame (majFWHM 3.87 vs 4.74 px) and undistorting
  the frames collapses Siril `seqtilt`'s off-axis aberration 0.57 → 0.25 px at FULL
  depth — remove the drift *or* remove the distortion and the homography becomes
  exact, which is the same statement twice
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
  medians must equal centre — **but the uniform card ALONE is a VACUOUS test.** Warping a uniform
  field yields the same uniform field, so corner==centre passes whether vignetting was stripped OR
  the module never fired at all (MEASURED on x86: the uniform card's `lensdist` vs `nodist` renders
  came back PIXEL-IDENTICAL, Siril `isub` → "all nil", while the module was demonstrably live). It
  needs a GRID positive control that MUST differ (grid card gave sigma 45613–45620, max ~54000) to
  prove the module fires; only then does the uniform card's flat corner-vs-centre mean "no
  photometric correction". `scripts/darktable/verify_lens_card.py` runs both legs and fails if
  either fails. Do NOT compare the rendered files byte-wise — `cmp` reported those same
  pixel-identical renders as DIFFERING (TIFF metadata). This checks the correction SET, never its
  CORRECTNESS: a wrong-but-present distortion model passes both legs.
- **The trap (same mechanism, other side): a lens the DB cannot match gets NO correction,
  SILENTLY** — an unrecognised `LensModel` gave max |dr| = 0.000 px over 413 stars, exit 0, not
  one word in the log; a wrong-but-present lens is worse (a wrong, weaker model, also silent).
  darktable never degrades loudly, so a missing-lens set stacks UNCORRECTED and the only symptom
  is a worse `seqtilt` off-axis in the final. "Did the warp happen?" is NOT a sufficient guard
  (it passes the wrong-lens case): assert EXIF camera+lens+focal against the DB AND the set's
  `acquisition.json`, per set, BEFORE the run. Corollary: a mixed-focal/mixed-lens set is a HARD
  STOP, not an interpolation — every frame silently gets its own model.
- **Round-tripping linear astro data through a raw converter: the tag and the
  export profile must CANCEL — and "verified identity" is only as good as the
  LEVELS it was verified at.** Siril's `savetif` embeds **`sRGB-elle-V2-srgbtrc.icc`**
  — an sRGB TONE CURVE — on LINEAR pixels, and **`icc_assign sRGBlinear` does NOT
  change what `savetif` embeds** (the export profile comes from a save-time
  preference). A converter reading that TIFF applies an sRGB→linear DECODE to
  already-linear data. Exporting LINEAR against the sRGB-tagged input leaves the
  decode UNCANCELLED: measured A_out/A_in climbing **0.1008 → 0.2121** (effective
  gamma ≈1.34) — silently destroying photometry while looking fine on a preview.
  The 16-bit-era rule — MATCH the output profile to the input tag
  (`--icc-type SRGB`) — verified as identity **at star amplitudes on 6s-class
  data** (0.9996–1.0000)… and later measured to carry a **TRC toe-segment
  mismatch below linear ≈0.003**: +4.7% at 0.0015 → +2.2% at 0.0017 → identity
  by 0.003 (Siril's elle sRGB toe vs darktable's SRGB toe). A 6 s sky sits above
  the band; a **3 s sky sits inside it** → ~1–2% per-channel global shift on
  that whole class, invisible to a star-amplitude check. **The float-leg
  contract (measured 2026-07-26, adopted): strip the ICC tag (exiftool
  `-icc_profile:all=`, same pass as the lens-tag copy) and export
  `--icc-type LIN_REC709` — a PERFECT identity, ratio 1.0000 at EVERY level and
  channel, warp confirmed firing (corner 0.22 vs centre 0.003).** Two traps
  beside it: (1) NEVER strip with siril `icc_remove` before `savetif32` — the
  same leg then applies a global **~1/12.92** scale (the sRGB linear-segment
  slope) to every pixel; (2) verify any ICC change with a ratio-vs-level curve
  DOWN TO the exposure class's SKY level (`bisect/iccprobe` method), never with
  star amplitudes or a mean alone — a toe error hides above the knee.
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
  OSC-only win (cleaner colour noise). `docs/plate-solving-and-drizzle.md`.
- CLASSICAL deconvolution (makepsf + RL) where trailing is in-exposure fails —
  unstable symmetric PSF on ≈0 background. (A LEARNED deconvolver is NOT classical RL
  and is a live x86 option, not a dead-end — tool choice + CPU costs in `TOOLS.md`.)

**QA / scope:**
- The GATE must be a composition-agnostic STATISTICAL sky scope — whole-frame
  reads real MW/object signal as a defect, and a geometric sky mask can't fix it
  (a bright object has no fixed band). Hand-picked patches miss defects a
  whole-scope measurement catches (the lesson that created the gate).
- **A LOG-MESSAGE REGEX IS NOT A MEASUREMENT INTERFACE — parse the tool's
  structured output, and prove the tool RAN.** A validation gate read
  `grep -oE 'Found [0-9]+ star' … || echo 0` off Siril's `findstar` log; Siril
  1.4.4 actually prints **"Found N Gaussian profile stars in image"** — the
  profile word sits between the count and "stars" — so the regex never matched
  and the fallback supplied a 0 **unconditionally**. A gate that cannot fail,
  and two flat records plus a ledger entry carried a speck count that was never
  measured. (Re-measured from the tool's own `-out=` list: 0–1 specks on every
  july23 flat, de-skied and control alike — the conclusion had been right for
  three sessions by luck.) Same family as the vacuous uniform-card test above:
  the check passed whether or not anything was measured. The wording is also
  version- AND parameter-dependent (the profile word changes with
  `setfindstar -profile=`), so it was never a stable interface.
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
  ones — so a COMMON black point renders a neutral sky as a tinted one.** Write the
  black point as f below the sky (autostretch's 2.8·MAD, or an explicit k·MAD);
  then any per-channel fractional sky difference is magnified by ≈1/f, because the
  render's sky is (sky_c − lo)/(hi − lo) and lo is close to sky. MEASURED on a
  starless+denoised layer whose linear sky was B/G **1.0048** (0.48%): a common
  black point renders B/G **1.1147** at f=0.0527 (19×) and **1.0596** at f=0.1391
  (7.2×) — an 11% or 6% visible background tint out of half a percent. Setting lo
  PER CHANNEL at the same fraction below each channel's own sky (i.e. background
  neutralization, the step the mainstream puts before colour calibration) while
  keeping ONE common window width and midtone renders **1.0057**, +0.09% from the
  truth; the "use linked" rule governs the CURVE and is satisfied by the common
  width/midtone. Scaling the width per channel too forces the sky to exactly
  1.0000 — which discards the colour SPCC measured rather than rendering it.
  Corollary for any deep-black-point render: a SHALLOWER black point is not free.
  It preserves faint signal but raises this amplification as 1/f, so black-point
  depth trades faint-signal crush against background colour fidelity, and the
  trade has to be made against the numbers, not by feel.
- **Never read a LINEAR residual off a STRETCHED surface.** An autostretch places the
  sky low on a steep curve, so it can compress or amplify a background ratio by
  several× depending on where the background lands — the same class of gradient read
  "corner/centre 1.06" on an autostretched preview and **1.27–1.37 linear** on the
  shipped stack (2.2–2.6 in its stretched judge PNGs). A display-domain ratio answers
  "what does the eye see", never "how big is the residual": measure gradients with
  Siril `stat` regional medians on the LINEAR image, and state the domain with the
  number. (Same trap in reverse: a pedestal-included ADU ratio understates a light-
  domain falloff — a ~1 EV vignetting read "6.3%" with the ~1007 ADU pedestal in.)
- **Do NOT assume "neural / ONNX / multi-threaded" means non-reproducible — MEASURE
  it. On this rig the whole render tier is BIT-IDENTICAL run to run.** Two identical
  runs of each stage, compared with Siril `isub` (all-nil = bit-identical):
  StarNet2 via siril `starnet -stretch` — identical, and identical AGAIN across
  thread counts (default 28 vs `setcpu 1`, and cross-compared); Cosmic Clarity
  denoise (`--disable_gpu`, separate mode) — identical, and identical across thread
  counts too (28 vs `OMP_NUM_THREADS=1`), so the determinism is not an artifact of one
  machine state; Siril's stretch +
  `asinh -human` + `pm` recombine — identical. So byte-identity IS the available
  bar here and a re-render reproduces exactly. Neither binary even exposes a
  thread/seed/device flag to pin (StarNet2's CLI is I/O + weights + stride +
  upsample only), so the reproducibility came free rather than from pinning.
- **The trap that replaced: a "run-to-run floor" derived from two runs whose inputs
  were never recorded.** A 1.34% colour floor was taken from two render records —
  one committed, one left uncommitted — read as a same-arm repeat, and hardcoded
  into a verdict that then called anything below 1.34% "unmeasurable". The old
  record logged NEITHER its linear source NOR its knob provenance, so nothing in it
  established that the two runs shared inputs and knobs; once every stage measured
  deterministic, two identical runs could not have produced different ratios, so
  something unrecorded differed. **A floor is a MEASUREMENT, not a subtraction of
  two numbers you happen to have** — bracket it deliberately with both arms'
  provenance recorded, or you build a threshold that hides real effects. The cost
  here was a verdict permissive enough to call a real 1% colour shift noise. (The
  stack-level floor in this registry — 2.06% at star edges, 0.073% in flat sky — is
  real, but it measures INTERPOLATION variance between separately REGISTERED
  stacks; it does not apply to two renders of one stack.)
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
- Compare finals in LIKE encodings (q92+4:2:0 loses star-edge chroma to
  subsampling). Judgment is the user's eyes on FULL-FRAME LOSSLESS finals
  (16-bit PNG only — never an 8-bit/reduced-depth/lossy copy), opened
  independently; one bracketed knob per experiment; nothing
  aesthetic commits before the user's eyes.
- **A multi-product judgment set rendered by data-dependent `autostretch` is NOT
  like-encoded — each surface gets its own histogram-derived transfer.** MEASURED
  (five surfaces from one chain): statistically identical linear stacks rendered
  as "rich MW field" vs "single-frame-looking flat gray" purely by the per-stack
  transfer. The trap bites comparisons too: a fixed-MTF probe against an
  autostretched PNG "refutes" correct hypotheses until re-run like-for-like.
  Multi-surface judgment sets pin ONE stretch RULE for every member — and the rule
  must be SKY-ANCHORED per product, not one raw MTF triplet: separately
  output-normalized stacks put their sky at different normalized levels, so a
  single triplet renders honest sky-level differences as gross brightness
  differences (measured: the brightest-sky set washed out under a combine-derived
  triplet). With healthy 32-bit statistics, per-product `autostretch -linked` at
  identical parameters IS the pinned rule (its 16-bit failure was the MAD
  collapse, not the rule); the render tier's stretch policy is the durable home.
- **NEVER measure a faint BROAD halo with region MEDIANS — the median is robust
  against exactly the wide low tail under test.** MEASURED cost (july23 Deneb
  disc): a median-based two-point control read the halo "identical before vs
  inside the haze window" and a session mechanism was mis-attributed on it;
  the MEAN-based 9-timepoint timeline over the same data shows the halo GROWING
  all night — G-channel star-box-minus-flanks 6.25 → 7.6 → 7.7 → 8.5 → 10.3 ADU
  (sets 01–03) and 7.1 → 9.9 → 12.0 WITHIN set-04 (+91% session-wide,
  accelerating late), alongside a monotonic FWHM rise 2.627 → 2.72 px and the
  terminal nstars crash (−13–16%, last ~20 min). Two lessons: (1) means (or
  outer-annulus statistics) for broad-glow photometry, medians only for
  compact-source-robust background; (2) a two-point control CANNOT test a
  monotonic-growth hypothesis — sample the full span. The growth pattern +
  conditions make DEW ON THE LENS the leading attribution (user field call;
  investigation record `docs/july23-dew-and-corner-chroma.md`); the per-set
  flat-cancellation variance on the FINAL stacks (Deneb-box excess 0/0/0 →
  +2.5/+5.8/+10 ADU across sets 01→04) remains measured and stands — a
  lights-built flat both bakes in and partially cancels a time-varying glow,
  inconsistently per set.

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
  `docs/july23-dew-and-corner-chroma.md`).
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
- Lock the zoom ring (tape); don't touch the camera mid-set (a focal-length step
  forces a mixed-optics stack). Dither between subs; avoid the moon (star fringes
  on trailed PSFs are dispersion — physical, not removable in processing). Stop a
  fast lens down ≥1 stop for bright-star fields (wide open adds a red veiling-glare
  halo — an honest optical signature, not a bandaid to remove).
