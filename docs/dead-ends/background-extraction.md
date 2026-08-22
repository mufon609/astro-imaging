# Background extraction

Phase-1 split of `docs/dead-ends.md` (organize-only; the original file stays
the live registry until the merge is decided). Content below the marker is
VERBATIM from the original, so in-text "above"/"below"/section references may
point at entries now homed in a sibling file — `README.md` in this directory
carries the index, the assignment rule, and the block manifest that resolves
them. Do not edit below the marker while the refactor is in phase 1; the split
is re-derivable from the manifest and verified byte-identical by `split.py`.

<!-- == verbatim content from docs/dead-ends.md below this marker == -->
**Background:**
- **DEGREE 2 DOES NOT ERASE THIS FIELD'S STARLIGHT — MEASURED, and the belief
  it replaces was mechanism only.** The claim was that the galactic-plane star
  field is frame-scale curvature at wide focal, so `seqsubsky 2` absorbs it and
  only degree 1 or a full BGE preserves it. The quantity that settles it needs
  no image and no arm: `subsky d` removes a degree-d surface, so the MOST it can
  take from the starlight is the fraction of the Gaia unresolved-starlight
  predictor's OWN spatial variance a degree-d surface can represent over the
  field. MEASURED (`scripts/qa/starlight_preservation.py`, aug06/set-01,
  23.3 x 17.1 deg, 140-cell external lattice, Gaia DR3 per-cell aggregate):
  the predictor spans **174% of its mean** across the field, and a **plane
  represents 10.0%** of its spatial variance, a **quadratic 36.2%**, a
  **cubic 43.5%**. So degree 1 can remove at most a tenth of the frame-scale
  starlight structure and degree 2 at most a third — a real difference between
  the two degrees, and nothing like erasure. Because it is a property of the
  catalogue over the lattice, no instrumental term can move it. SCOPE: this
  field, this lattice; the bound is an upper one (it assumes the fitted surface
  is the best-fit surface to the starlight itself), and it must be recomputed
  per field — the instrument prints it on every run.
  **AND IT DOES NOT REST ON THE INHERITED G-SPLIT — audited by recomputing the
  bound directly from the retained per-magnitude bins.** The split (G = 11.0 at
  50% completeness) is INHERITED from the july23 identification record and is a
  hypothesis on this corpus until re-measured, so the obvious worry is that the
  bound moves with it. It does not: swept G = 9 to 14, five magnitudes and far
  wider than any plausible error in the inherited value, the plane term runs
  **0.090-0.118**, the quadratic **0.360-0.380** and the cubic **0.430-0.453**
  against the recorded 0.0997 / 0.3624 / 0.4349. "Degree 2 costs at most a
  third" therefore holds wherever the split actually sits, and re-measuring the
  split is NOT a prerequisite for the L1 build. Reproduce with the tracked
  `gaia_cells_cache.json`, which keeps every magnitude bin for exactly this.
- **THE IMAGE-SIDE VERSION OF THE SAME TEST CANNOT SETTLE IT ON TODAY'S
  PRODUCTS, and the reason is a second measurement worth keeping: the
  frame-scale floor is mostly NOT starlight.** One knob, on-stack `subsky 1` vs
  `subsky 2` against the untouched stack, same 140 cells, paired: the Gaia slope
  RISES — retained **1.232 / 1.274 / 1.237** (R/G/B) at degree 1 and **1.517 /
  1.846 / 1.604** at degree 2, standard errors 0.056-0.155. Removing a surface
  IMPROVES the starlight relation because the open `sky x V` residual is
  anti-correlated with it and biases the raw slope LOW; confound-removed and
  starlight-removed land in the same statistic with opposite signs. Sizes:
  predicted starlight spans **0.71-0.86 ADU** across the frame against a
  measured floor span of **2.50-4.00 ADU**, so about a fifth to a third of the
  frame-scale floor variation is starlight. A clean structural check falls out
  of the same run — after residualising both arms by a quadratic the degree-2
  arm retains **1.000 / 1.010 / 1.018**, i.e. `subsky` moves ONLY its own
  polynomial subspace and nothing above it.
- **"VISIBLE RINGS" IS NOT AN EYE OBSERVATION — it is a deleted IN-HOUSE
  METRIC's verdict, and the provenance was lost in a rewrite.** The sentence
  entered as *"Stack-level-only BGE leaves a STRUCTURED residual (fails the
  rings gate, loses MW)"*. Commit `870bf7d`, which deleted the in-house
  measurement layer, rewrote it to *"(visible rings, loses MW)"* in the same
  diff that removed the gate — turning a metric's verdict into what reads as a
  human seeing rings. The gate was `bg_qa.ring_amp`: the detrended
  peak-to-valley of a 40-bin RADIAL profile of the render. That is the
  reference FORBIDDEN class (an in-house gate reading the deliverable), and the
  same radial-binning family as trap 3 below, whose profile flattened as the
  defect it was keyed to got worse. Treat stack-level BGE as UNJUDGED: there is
  no image, no number and no n behind the ring claim, and the metric that
  produced it is not one this repo would accept today. The independent
  mechanism that IS documented for rings — too high a polynomial degree used to
  fit vignetting (Shelley, *Diagnosing Baked-In Concentric Rings*) — is a
  statement about DEGREE, not about where in the chain the step runs, and this
  repo has its own measured instance of it (a polynomial radial V(r) oscillates
  into rings, "Gain / flat" above).
- **VENDOR DOCTRINE, and our default already matches it — this is a
  standards-first alignment, not a deviation.** Siril's own documentation
  recommends background extraction on the SEQUENCE at degree 1: *"in a single
  image, the background gradient is much simpler and generally follows a simple
  linear (degree 1) function"*, against a stack whose gradient is *"the sum of
  all the gradients contained in each image"*; *"a too high degree can give
  strange results like overcorrection"*, maximum 4, beyond which *"the model is
  generally unstable"* (siril.readthedocs.io, Background Extraction;
  siril.org/tutorials/gradient). PixInsight's doctrine places DBE/ABE early, on
  LINEAR data, before colour calibration. Both vendors put background
  extraction before colour calibration, which is the order this chain already
  runs. What is NOT vendor doctrine anywhere is the starlight-preservation
  argument for degree 1 — Siril's stated reason is gradient complexity, and the
  faint-signal concern appears only as the sampling design ("a smoothed
  function to avoid removing nebulae with it").
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
  **FINDING THAT FRAME: the coverage test must name ONE reference channel, and
  it must not be the low one.** The registry rule above it — require the
  SIBLING-CLASS SKY FLOOR, never mere non-zero — is right, but applying it to
  the WORST channel is unusable on this class: the LOW channel clips to zero on
  sky that is fully covered. MEASURED on the three aug06 per-set stacks, which
  are `-framing=min` products and therefore fully covered by construction —
  Siril `stat` reads **Red Min 0.0** on all three (Red medians 14.6 / 32.1 /
  28.3) while Green reads **Min 60.4 / 72.4 / 67.7** at medians 71.8 / 83.8 /
  79.3. A worst-channel bar therefore cannot pass at ANY positive floor and
  calls covered sky uncovered; `web/verify_framing.py --channel=` names the
  reference layer and every layer is still measured. Same convention as
  `starlight_preservation.py`'s own coverage guard, which counts a cell
  uncovered only when EVERY channel reads zero.
  **The floor is DERIVED, not picked**, from the same sibling stacks: their
  Green Min/Median ratios are 0.841 / 0.864 / 0.854 (mean 0.8530), and the
  aug06 3-set union's own Green median is 94.8, so the floor is 80.9 ADU. The
  data corroborates it independently — over an 80x50 grid of 91x91 px boxes,
  260 boxes read Green Min 0.0 and only **31 fall in (0, 80)** against a clean
  population starting at **82.3**, so the derived floor lands inside the
  measured gap rather than inside either population. Delivered frame: 6643x3549
  of 7355x4590 (69.8%), whose whole-crop Siril Min is **81.6 Green / 52.5 Blue
  / 14.1 Red** — no zero-coverage pixel in any channel.
