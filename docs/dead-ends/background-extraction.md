# Background extraction

Phase-2 file of the dead-ends registry split (`README.md` here holds the index
and dispositions; pre-compression forms live in git and in the live
`docs/dead-ends.md` until the merge). Cross-references to sibling files are
written as (`<file>.md`) pointers.

<!-- phase-2: maintained in place; not regenerated from the manifest -->
- **DEGREE 2 DOES NOT ERASE THIS FIELD'S STARLIGHT — MEASURED, and the belief
  it replaces was mechanism only.** The claim was that the galactic-plane
  star field is frame-scale curvature at wide focal, so `seqsubsky 2`
  absorbs it and only degree 1 or a full BGE preserves it. The quantity that
  settles it needs no image and no arm: `subsky d` removes a degree-d
  surface, so the MOST it can take from the starlight is the fraction of the
  Gaia unresolved-starlight predictor's OWN spatial variance a degree-d
  surface can represent. MEASURED (`scripts/qa/starlight_preservation.py`,
  140-cell external lattice, Gaia DR3): the predictor spans 174% of its mean
  across the field, and a **plane represents 10.0%** of its spatial
  variance, a **quadratic 36.2%**, a **cubic 43.5%** — degree 1 can remove
  at most a tenth of the frame-scale starlight structure and degree 2 at
  most a third: a real difference, and nothing like erasure. A property of
  the catalogue over the lattice — no instrumental term can move it. SCOPE:
  this field, this lattice; an upper bound; recompute per field (the
  instrument prints it on every run). **And it does not rest on the
  inherited G-split:** swept G = 9 to 14 — far wider than any plausible
  error — the three fractions move only in the third decimal, so
  re-measuring the split is NOT a prerequisite for the L1 build (the tracked
  `gaia_cells_cache.json` keeps every magnitude bin for exactly this).
- **THE IMAGE-SIDE VERSION OF THE SAME TEST CANNOT SETTLE IT ON TODAY'S
  PRODUCTS — the frame-scale floor is mostly NOT starlight.** One knob,
  on-stack `subsky 1` vs `subsky 2` against the untouched stack, same 140
  cells, paired: the Gaia slope RISES (retained 1.232/1.274/1.237 at degree
  1, 1.517/1.846/1.604 at degree 2) — removing a surface IMPROVES the
  starlight relation because the open `sky × V` residual is anti-correlated
  with it and biases the raw slope LOW; confound-removed and
  starlight-removed land in the same statistic with opposite signs. Sizes:
  predicted starlight spans 0.71–0.86 ADU across the frame against a
  measured floor span of 2.50–4.00 — a fifth to a third of the frame-scale
  floor is starlight. Clean structural check from the same run: after
  residualising both arms by a quadratic, the degree-2 arm retains
  1.000/1.010/1.018 — `subsky` moves ONLY its own polynomial subspace.
- **"VISIBLE RINGS" IS NOT AN EYE OBSERVATION — it is a deleted IN-HOUSE
  METRIC's verdict, and the provenance was lost in a rewrite.** The sentence
  entered as a rings-gate failure; the commit that deleted the in-house
  measurement layer rewrote it to *"(visible rings, loses MW)"* in the same
  diff — turning a metric's verdict into what reads as a human seeing rings.
  The gate was the detrended peak-to-valley of a 40-bin RADIAL profile of
  the render: the reference FORBIDDEN class (an in-house gate reading the
  deliverable), and the same radial-binning family as trap 3
  (`registration-distortion.md`), whose profile flattened as the defect it
  was keyed to got worse. **Treat stack-level BGE as UNJUDGED: no image, no
  number, no n behind the ring claim.** The independent mechanism that IS
  documented for rings — too high a polynomial degree fitting vignetting
  (Shelley, *Diagnosing Baked-In Concentric Rings*) — is about DEGREE, not
  where in the chain the step runs; this repo's own measured instance is the
  polynomial radial V(r) constraint (`calibration-flats.md`).
- **VENDOR DOCTRINE, and our default already matches it — a standards-first
  alignment, not a deviation.** Siril's own documentation recommends
  background extraction on the SEQUENCE at degree 1 (*"in a single image,
  the background gradient … generally follows a simple linear function"*; a
  stack's gradient is *"the sum of all the gradients contained in each
  image"*; *"a too high degree can give strange results like
  overcorrection"*, maximum 4). PixInsight places DBE/ABE early, on LINEAR
  data, before colour calibration — the order this chain already runs. What
  is NOT vendor doctrine anywhere is the starlight-preservation argument for
  degree 1 — Siril's stated reason is gradient complexity.
- GraXpert AI smoothing is NOT faint-signal protection — smoothing blurs the
  model OUTPUT, not the inference; frame-filling faint structure reads as
  the trained light-pollution class and is absorbed. Use a plane/off for
  object-filling fields. BGE does NOT absorb a centred galaxy's halo (it
  measures STRONGER against a lower far-field sky).
- **GraXpert AI `-correction Division` as a synthetic flat on a field filled
  with UNRESOLVED STARLIGHT absorbs most of the extended structure —
  measured, even at max smoothing.** Four-arm probe (60-frame stacks, same
  chain, one knob), NAN-region contrast as % of local sky R/G/B: own sky
  flat 8.5/2.9/5.6; GraXpert Division (smoothing 1.0) **2.4/0.7/2.1** — the
  division ate ~2/3 of the nebula while flattening corners to ±2% (it
  flattens the REAL sky structure too; perfectly flat corners on a MW field
  are themselves a defect signature). The vignetting-only promise holds only
  where faint structure does not fill the frame — the same enabling
  condition as the sky flat. UNTESTED alternative: GraXpert's classical grid
  interpolators via `-preferences_file` (RBF/spline, no AI model). Also
  measured in the same probe: the 16-bit intermediates chain reads only
  ~55–70% of the 32-bit arm's extended contrast — integer round-tripping
  through calibrate/warp/register eats faint signal.
- On a union/max canvas, CROP to the verified coverage frame BEFORE any
  background step: `subsky`'s sample grid ingests the canvas's zero-coverage
  rims — its `-tolerance` excludes only BRIGHT outliers, not empty sky — and
  the fit skews. Crop-before-background is the pinned order.
  **FINDING THAT FRAME: the coverage test must name ONE reference channel,
  and it must not be the low one.** Requiring the sibling-class sky floor is
  right, but applied to the WORST channel it is unusable on this class: the
  LOW channel clips to zero on sky that is fully covered (measured on three
  `-framing=min` stacks — fully covered by construction — Red Min 0.0 on
  all three while Green reads 60–72 at healthy medians). A worst-channel bar
  cannot pass at ANY positive floor; `web/verify_framing.py --channel=`
  names the reference layer and every layer is still measured. **The floor
  is DERIVED, not picked**, from sibling stacks' Green Min/Median ratios
  (mean 0.8530 × the union's own median → 80.9 ADU here), and the data
  corroborates it independently: over an 80×50 grid, the clean population
  starts at 82.3 with only 31 boxes in (0, 80) — the derived floor lands
  inside the measured gap, not inside either population.
