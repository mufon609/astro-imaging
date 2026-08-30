# Stacking, groups, and the sub-stack compose

Part of the dead-end registry — `docs/dead-ends.md` is the index, and
`00-registry-contract.md` governs how entries are read, cited, written and
deleted. Entries are maintained IN PLACE (pre-compression forms are in git;
the pre-split single-file registry is `docs/dead-ends.md`'s own history).
Cross-references to sibling files are written as (`<file>.md`) pointers.
Compose-defect status home: BACKLOG:`compose-homography-smear` (astrometric
route SHIPPED; the surviving union band is ATTRIBUTED member-borne, night-
dominated and in the photons — registration refuted across a 9× drift span —
and answered by member selection: the decision map with every form's numbers is
`docs/corner-smear-member-selection.md`).

<!-- registry content below; docs/dead-ends.md is the index -->
- **THE UNION'S LEFT-BAND / BOTTOM-CORNER SMEAR IS NOT A REGISTRATION OR
  COMPOSE DEFECT — it is what the MEMBERS carry on their entry side, and the
  only lever is what enters the mean.** MEASURED by four pre-registered
  discriminators (`datasets/aug06/experiments.jsonl` 98–105): (1) three nested
  arms of one set with 26.1 / 104.3 / 235.7 px of stacked drift span read the
  exit-side blur FLAT (ΔFWHM(L−S) −0.025..+0.055 px, roundness within 0.018) —
  a registration error growing with the span is refuted; (2) the union's band
  is built exclusively from the members' entry-side columns 400–1470 px from
  their entry edge, which read on the members what the union reads (2.66–2.75
  vs 2.89–2.98 px = the compose floor + 0.03–0.11); (3) the term is in SINGLE
  RAWS and night-ordered (along+2400: aug14 raws 2.94–3.03 px / 0.53 against
  july31/set-01's 2.18 / 0.80; member − raw within the stacking floor on 11 of
  12 pairings); (4) the bottom corners are radial (coma-like, bottom-right
  strongest, e 0.30–0.49), the top corners not — the lens's asymmetric term,
  with the union's bottom-left corner being the members' top-right corners
  through the ~180° member↔canvas flip. Consequences: no reference choice,
  kernel, or registration model can remove it; a rank cull (worst quartile)
  and a per-member entry-side crop both move the band 2.97 → 2.79 px, and the
  THRESHOLD form (crop beyond the onset where FWHM(+dx) − FWHM(−dx) > 0.20 px)
  does it with no seam at 27 boundaries at full depth — owner-approved. What
  selection cannot fix: the lens's SYMMETRIC radial softening (67/77 members
  rise > 0.20 px on the exit side too — every frame has it, so excluding it
  buys nothing and costs depth). The fix is IN THE CHAIN: `run_corpus_combine.sh
  --portion-rule` runs the stage (`run_member_crop.sh`) and the corpus canonical
  is built under it, 0 differing pixels from the owner-approved arm (ledger
  128), guarded by the corpus slot `datasets/corpus/baseline.json`. The decision
  map, the refuted rule forms with their numbers, the constant's measured
  continuum and the stage as built: `docs/corner-smear-member-selection.md`.
- **A ROW-RESOLVED CROP (x_c = min over the member's top / centre / bottom rows)
  BUYS NOTHING ON THIS CORPUS — the bottom row reaches the bar ~600 px earlier,
  but the columns that removes sit under deep four-night coverage.** MEASURED
  (`datasets/corpus/smear_attribution/row_profiles.json`, `rowmin_arm.json`;
  `datasets/aug06/experiments.jsonl` 129–132). The stage's own profile re-run on
  the members' TOP (box y 0..800) and BOTTOM (H−800..H) rows, six
  corner_direction members + two controls, centre row from the cache: the
  bottom row crosses the 0.20-px asymmetry bar at 1200 on 5/5 cropped members
  (centre row 1800 ×4 / 2400 ×1; bottom-row asymmetry at 1200 +0.284 / +0.352 /
  +0.289 / +0.290 / +0.202 against +0.093 / +0.037 / +0.020 / +0.128 / +0.042)
  with the SAME far-station asymmetry (bottom − centre at 2400 +0.006..+0.102),
  and the on-the-bar member aug09/set-05/sub_01 (0.200, uncropped) crosses on
  both rows. The arm built on it — ONE knob: x_c 900 on the five, 1500 on the
  on-the-bar member, every other member as the chain, reference pinned 35,
  nbstack — is a CLEAN NULL: with the rows PINNED through both WCS (member top
  row → the canonical's bottom-left region, member bottom row → top-left, the
  removed columns 600–1500 px INWARD of the corner boxes, canvas x ~2400–3500),
  the top-30 FWHM at the removed columns' own sky positions moved −0.004..−0.033
  px (pre-registered ≥ 0.10 on ≥ 6/10 → 0/10), the corner boxes ≤ 0.02, the
  band ≤ 0.007, x50 0.000, six seams clean (Siril `stat` steps ≤ 0.24 %), at
  +1.205 % pixel-frames (7.646 vs 6.441 %) and a rim step (x05 +0.038 px). Two
  untargeted stations moved ±0.038 in opposite directions far from any removed
  column (x85 +0.038, the bottom-right corner −0.038): the same-reference repeat
  is ~±0.04 px here, a PREMISE to re-measure, not the 0.03 assumed. HYPOTHESIS,
  untested: dilution — a +0.3-px excess is a small share of an nbstack-weighted
  mean under deep coverage, where cropT's 0.18-px band gain came from the THIN
  band (coverers x10 4→1, x15 13→3, x20 36→7). What the rows DID find, open and
  not a crop question: the TOP row of the aug14 / aug09-set-05 members is 0.4–0.5
  px softer than their centre row SYMMETRICALLY (centre station 2.947–3.067 vs
  2.535–2.600; aug14/set-04/sub_01's top row entry 600..2400 3.07 / 3.42 / 3.45 /
  2.91 against exit 3.15 / 3.33 / 3.05 / 2.63; controls +0.05 / +0.19) — the
  uniformly-soft case the asymmetry rule is blind to BY DESIGN (the threshold
  ruling), feeding the canonical's bottom-left region through the flip. The
  candidate knob, named not run: a corpus-relative ROW-level exclusion (the
  frame-level analogue was a NULL at the centre row, where the night difference
  is ~0.3 px; at the top row it is ~0.5 px). Companion NULL: the +2400 station's
  blind spot (the last 86–116 px of a member's entry side) is BOUNDED —
  same-aperture Δ(+2700 − +2400) median +0.008 px on 30 members — and per-member
  calls there are unresolvable at r 200 (that box's asymmetry scatters ±0.12 px
  against the r-400 reading, half the bar; a 400-px box cannot be placed there).
- **SIRIL'S NOISE WEIGHT IS (scale/bgnoise)² ON THE REGISTERED IMAGE'S NON-NULL
  PIXELS — coverage does not enter, and on this corpus it is nearly uniform: the
  sharpest night is the noisiest.** SOURCE (Siril 1.4.4
  `src/stacking/median_and_mean.c`, `compute_noise_weights()`):
  `pweights[layer][i] = 1 / (coeff.pscale[layer][i]² × seq->stats[layer][idx]->bgnoise²)`,
  divided by the mean over frames per layer; `pscale_i = scale_ref/scale_i` is the
  addscale normalization, so the weight is `(scale_i / (scale_ref · bgnoise_i))²`
  — the member's dispersion-to-noise ratio squared, NOT `1/bgnoise²` (on a
  3-member probe 0.889 / 1.031 / 1.080 against 0.594 / 1.092 / 1.316 for
  `1/bgnoise²`). MEASURED (`datasets/corpus/smear_attribution/weight_noise_arm.json`,
  `datasets/aug06/experiments.jsonl` 134–136): the registered sequence's `.seq`
  statistics carry `ngoodpix` equal to each registered image's NONZERO-pixel count
  to the pixel (22,999,612 / 22,888,326 / 22,854,455 against totals 37,047,290 /
  28,399,680 / 29,704,448; zero fractions 0.379 / 0.194 / 0.231), the `.seq` bgnoise
  equals Siril `bgnoise` on the whole registered frame (Green 2.2003e-05 /
  1.6224e-05 / 1.4778e-05 vs 2.2e-05 / 1.622e-05 / 1.478e-05), and the
  whole/centre-crop ratio (1.121 / 0.996 / 1.031) is the member's own noise gradient
  — identical on the unregistered original (1.119 / 1.002 / 1.036) — so the
  zero-filled `framing=max` margins do not enter. Two side terms: resampling lowers a
  non-reference member's noise ~2.3 % (registered/original 0.998 / 0.977 / 0.976:
  ~+5 % weight for everyone but the reference), and the pscale term above. On the
  77-member corpus Siril's own weights (Green, mean 1) run july31 0.900, aug06
  0.971, aug09 0.988, aug14 1.094 (nbstack 0.955 / 1.032 / 1.027 / 0.990): by
  Siril's estimator the NOISIEST night is july31 (bgnoise 1.457 ADU16 against
  0.96–1.01), the night with the SHARPEST members, and the softest night (aug14) is
  the quietest — the 18–24 % aug09 haze figure is a THROUGHPUT gap on the stars,
  which a background-noise weight does not see. The one-knob arm (nbstack → noise,
  the same curated members, reference pinned 35) is a CLEAN NULL: all 58 stations
  within −0.015..+0.016 px / ±0.012 roundness of the canonical (floor ±0.04 / 0.02),
  the band +0.003..+0.013, the corners 0.000 at six of eight and +0.007
  (corner_700_1400) / −0.015 (corner_7750_1100) at two (floor ±0.04), the 27
  seams identical, SPCC K within 0.004, depth unchanged within the
  structure-limited reading. CAVEAT — the per-member weights above are
  RECONSTRUCTED, not printed: Siril prints no per-image weight; they are the
  `.seq` M-line statistics through `compute_noise_weights()` as READ from the
  1.4.4 source, unverified on this rig. Positive control named, NOT run: a
  two-member compose with a planted noise ratio (one member and a copy of it
  carrying added Gaussian noise of known σ, Siril `bgnoise` measured on both)
  whose composite mean must match the reconstructed weights; until it runs,
  "Siril's own weights" here means "Siril's own statistics through the source
  formula". Consequence: nbstack
  stays the chain's default; a per-member weight is not the lever for a
  night-quality difference here — the weights differ by ~10 % while the members'
  FWHM differ by ~0.3 px, so the weighted mean moves ~0.01 px; the lever that
  measured is exclusion of the degrading PORTIONS (the portion rule). The compose
  stamps no weight key — the weighting is recoverable only from Siril's HISTORY
  card (BACKLOG:`composite-header-identity`; `siril-behaviors.md`).
- **A `-framing=min` CANVAS IS SIZED BY TIME SPAN, NOT FRAME COUNT — so a
  metric taken at a margin relative to each canvas's own edge is not
  like-for-like across sets.** The intersection keeps only what every frame
  covers, so the trim is how far the sky swept — at fixed cadence, the burst
  duration. MEASURED, july31: set-04 ran 777 s and lost 605 px of x; sets
  01–03 ran 1497–1624 s and lost 1153–1163 px, leaving set-04 with the
  LARGEST canvas and the FEWEST frames — the same fact stated twice.
  Re-measuring all four at a common physical extent moved the numbers and
  set-04 got WORSE, so the geometry is not the explanation. Second-order but
  unmodelled and live: the total trim runs **1.16–1.29× the pure translation**
  in every set — the excess is field rotation plus the warp border and the
  groups route's two-stage framing; `fingerprint.py` computes translation
  only, so every disk and framing figure derived from `drift_px`
  under-counts.

- **THE SUB-STACK COMPOSE IS A MOSAIC, NOT A STACK — a single HOMOGRAPHY
  cannot align members whose optical axes are degrees apart while any
  lens-model residual survives. The largest star-shape defect measured in a
  shipped product, invisible to every per-member measurement — and the fix
  has since SHIPPED.** A group is a CONSECUTIVE time block, so within one
  1497 s burst the sky sweeps 6.25° of RA and one set's five members solve to
  centres **4.28° apart**; composing them is stitching different pointings,
  and the registry's Szeliski result applies one level up: the true
  member-to-member map is `distort ∘ H ∘ distort⁻¹`, and `register -2pass`
  fits `H` alone. MEASURED (Siril `findstar`, 800 px boxes placed by each
  product's own solved WCS, medians of the 30 brightest = rank-matched): at
  RA 294.86 all five set-01 members read **2.42–2.54 px / roundness
  0.924–0.942** (mid-field) while their own 5-member compose reads
  **3.48 / 0.582**; the 28-member cross-night union 0.458; a control position
  shows the compose costing nothing — **the within-set step is most of it.**
  **The discriminator that named the fix:** the members' OWN astrometric
  solutions place the same stars within **0.10 px median / 0.26 px p90**
  exactly where the homography compose loses 1.06 px of FWHM — the alignment
  information existed and the homography discarded it. **The fix shipped:**
  `seqplatesolve` composes each member's own SIP undistortion with the linear
  projection in a single mapping and is the compose default, owner-PASSED —
  one-knob on the 28-member union: star-pair **4.383 px / 0.458** at the
  defect against astrometric **2.678 / 0.974**, control unchanged
  (`-2pass` survives only as the `--starpair` regression arm; route history:
  `registration-distortion.md`, the standalone-SIP-warp entry, and the
  BACKLOG item). **The union's SURVIVING band is since ATTRIBUTED
  member-borne — the compose is EXONERATED for it** (carrier: member +x-edge
  proximity; `datasets/aug09/smear_work/rho_march.json`). The compose's own
  geometry measurement was blind to the original defect (its zones were then
  canvas-radial and returned UNMEASURED on this union) — `member_separation.py`
  has since been rebuilt and its threshold layer removed (entries below;
  `docs/combine-contract.md` §5).
  **The disagreement decomposed to TWO terms, both measured:**
  *(a) The compose made part of it* — the same members disagree more inside a
  big sequence than composed among themselves (1.12 → 3.02 px, 0.95 →
  3.38 px going to the 41° 28-member union): one homography per member
  against a common reference is a compromise fit over the overlap region that
  extrapolates badly elsewhere. The `-2pass` mechanism — now the regression
  arm's.
  *(b) One set carries a genuine OPTICAL-STATE CHANGE MID-BURST.* aug06/
  set-01's groups 1,2,3 agree to 0.21–0.34 px and groups 4,5 sit
  2.95–4.91 px away, 100 consecutive frames into the burst. Ruled out:
  pointing spread (2.16° apart at 0.34 px vs 1.38° apart at 3.14 px),
  the registration reference (the pair reads 2.95–3.02 px under three
  different references), and acquisition interruption (uniform 3.00 s
  cadence, no gap anywhere); the disagreement normalised by axis
  separation — what a single shared optical state holds constant — is flat
  at 0.21–0.32 px/deg for groups 1–3 and reads 3.07/3.58 px/deg across the
  boundary.
  **A TRAP WORTH KEEPING: the residual's cos(θ) dipole is NOT evidence of a
  decentring.** Differencing ONE radial field about two displaced centres
  gives a dipole by construction, amplitude ∝ axis separation — the null
  expectation, not a mechanism; only the separation-normalised ratio
  discriminates, and it says the optics changed without saying how.
  **The reference half is separable and since RESOLVED:** per-group
  AUTO-PICKED references wander (picks at frames 6, 26, 15, 3, 26 of 50; the
  break lands on whichever reference sits latest) and are worth 6.5× on their
  own — five independent per-block registrations give a worst pair of
  3.12 px, ONE global reference 0.48 px; the shipped compose now registers
  all members in one sweep with the reference setref-pinned. But one
  reference only MOVES the error (into 0.25–0.27 px within-member blur):
  **the underlying change is PHYSICAL, TIME-PROGRESSIVE and ONE-SIDED** — with
  the reference pinned mid-sequence, the late block beats its early twin at
  MATCHED drift distance by +0.25–0.27 px on the LEFT field only, and the
  ordering is TIME, not distance from the reference.
  **Mechanism undetermined; two candidates, one discriminator.** Differential
  refraction (horizon-fixed, progressive, non-homographic — the open question
  shared with BACKLOG:`one-sided-band`) vs mechanical SAG of the extended
  zoom barrel: refraction reverses sense between a rising and a setting
  field, sag does not. The site is a gitignored local config (the tracked
  template is `scripts/setup/site.example.json`; `scripts/lib/acquisition.py`
  reads it, every acquisition record carries its sha256 only, no silent
  default — a home address in a tree meant for publication) and the corpus
  carries both senses (20 pre-meridian / 3 post-meridian over 23 solved
  products), so the sense test is runnable — with limits: the coordinates
  are owner-transcribed and bounded at the DEGREE level only
  (`verify_site.py`), SITEELEV is unrecorded (OBSGEO at h = 0), and the
  corpus sits at altitude 63.4–87.7°, the flat end of the refraction curve,
  so the surviving lever is UNQUANTIFIED; the second disjunct — the same
  middle-pinned build on sets at different altitudes — needs no coordinate
  at all. **What this does and does not license:** it does NOT revive
  per-set lens models (a per-set model would be wrong for part of its own
  set); it establishes the OPTICAL-STATE tier can be finer than the SET tier
  and a state boundary is something to DETECT. Still open: what physically
  changed at that boundary, and the (a)/(b) split of the union's corner
  median.
- **A PRODUCT-LEVEL A/B CANNOT AUDIT A TRANSIENT'S REJECTION — the dilution
  is the instrument's blind spot.** The groups route divides a transient's
  per-frame amplitude by the group size and again by the member count:
  july31/set-03's aircraft carries ~766 ADU per frame and lands at
  0.02–0.06 ADU in a 400 px box of the full-depth difference, against that
  difference's own 0.2 ADU box-to-box spread — a FLAT difference is equally
  consistent with rejection and no rejection. **Audit rejection where it
  HAPPENS:** `stack ... -rejmaps` writes the per-pixel record of discarded
  samples; differencing the group-with against the group-without leaves the
  transient's own track (its median equals the frame-count scale step, which
  calibrates the map for free), and the on-track residual is measured at
  GROUP level, where the signal is 5× larger.
- wFWHM weighting at low FWHM spread is WORSE than none (`-weight=wfwhm` is a
  min-max ramp → worst frame ~0 weight at any spread).
  **SCOPED — this was written as *"Siril `-weight` is a min-max ramp"*, TRUE
  of `wfwhm` and `nbstars` and FALSE of `noise`**, which is inverse-variance
  as the shipped compose has said all along (`run_undistort_compose.sh`).
  The widening-inside-a-flag is the worked example for the SUBJECT axis's
  granularity bound (`00-registry-contract.md`); the wFWHM finding itself is
  unaffected.
- Rejection and cosmetic correction CANNOT remove walking noise
  (drift-aligned streaks: sensor-fixed FPN dragged into lines by coherent
  un-dithered drift). The pattern is sub-sigma STRUCTURED signal, not
  discrete outliers — measured NULL twice (`-cc=dark`, and
  GESD-vs-winsorized, no change either way); drift-phase structured term
  ≈0.34/0.48/0.42 ADU per ~199-frame half vs ≈1.0/1.5/1.2 total static
  (`noise_split.sh`). Acquisition owns the fix (dither between subs); a
  denoiser is symptom budget only (BACKLOG:`walking-noise`).
- **Never compose PRE-CROPPED per-set stacks to deliver a frame beyond any
  member's crop** — a per-set `-framing=min` stack has already discarded its
  outer drift zones, so a compose of such members has holes exactly where
  only the discarded zones covered (measured: a zero-coverage staircase
  across the cov25 frame's right region that the 107-sub-stack compose
  covers at Min 84–88 ADU). Compose from the UN-cropped sub-stacks.
  **The registration reference facts, per route:** on the star-pair route
  (`register -2pass`, now the regression arm) `setref` AFTER the 2pass
  re-bases both the canvas orientation and (via `-norm=addscale`) the raw
  channel balance. On the SHIPPED astrometric route the reference is LIVE
  but the canvas does NOT inherit its orientation — one knob (only `--ref`
  moved): canvas 7071×4629 → 7095×4622, north +9.6244° → +7.7633°,
  centre-median B/G 0.7427 → 0.5260 — it TRACKS the reference without
  equalling it (two points; uncharacterised).
  **The balance half is real at the compose and immaterial at the
  deliverable — SPCC ABSORBS IT, 64×:** B/G 0.7427 vs 0.5260 at the compose
  becomes 0.9962 vs 0.9927 after SPCC, the K factors moving to compensate —
  so **the choice of reference is a GEOMETRY decision, not a colour one**
  (argue it on coverage; bounds: 4 members / 2 nights, canvas delta
  0.34%/0.15%, nothing here measures 77 members).
  **AUTO IS INDEX 0, NOT A RANKING** — verified across ten
  `compose_gate_*.json` records at 13–77 members (every one
  `reference_member = s_00001`) and by a probe measuring **0 differing
  pixels of 98,194,977** against an explicit `--ref=1`. The reference is
  whatever sorts FIRST: appending a night re-bases nothing, reordering the
  arguments re-bases everything. It is now stamped on the artifact
  (`REGREF`/`REGREFSR`); products built earlier carry none and are not
  backfilled.
  **Two guard rules measured alongside:** a crop-coverage guard of `Min > 0`
  PASSES on lanczos edge-ringing residue (Min 7–26 on a ~90 sky) — require
  the SIBLING-CLASS SKY FLOOR, never mere non-zero; and **the same reference
  pin also moves the CANVAS SIZE, where a one-set verification can be fooled
  by coincidence** — pinned-vs-unpinned delivered identical canvases on the
  one set whose auto-pick already landed on member 1 and different canvases
  on the other two (members proven bit-identical first). **An A/B baseline
  must be built by the SAME code as its arm, not merely from the same
  frames** — the cheap tell is diffing the two generated `.ssf` files.
- **Never sigma-reject across SUB-STACK composes.** Sub-stacks are clean
  ~group-size means, so their mutual scatter is ~√group below per-frame
  noise — a 3σ gate at that tiny σ fires on the systematic differences
  sub-pixel registration leaves along steep gradients, not on outliers.
  Measured (`rej 3 3` across 25 fifteen-frame sub-stacks vs a plain mean):
  pixels rewritten by up to **±3800 ADU on a ~140 ADU sky**, star cores
  carved out — while whole-frame `seqtilt` medians stayed FLAT, so the
  damage is invisible to frame-wide statistics. Reject within groups (full
  per-frame strength, where satellites die); compose sub-stacks with a
  PLAIN MEAN.
- Drizzle: "short focal / large pixels ⇒ oversampled" is BACKWARDS (that
  geometry gives large arcsec/px → few px per star → UNDER-sampled,
  drizzle's home turf). Judge sampling by measured **minor-axis FWHM**:
  ≥~2–3 px = oversampled (skip), <2 px = undersampled (2× drizzle can help
  IF real sub-pixel dither + many registered frames). Trailed data is
  oversampled only where trailing spreads the star; drizzle is pointless
  there (it renders a sharper *smeared* star). CFA-drizzle 1×/pixfrac 1.0 is
  a separate OSC-only win.
- **THE FRAME COUNTER WRAPS AT 9999 → 0001, AND FILENAME SORT IS THEN THE
  WRONG ORDER — groups are consecutive TIME blocks.** Measured on
  aug09/set-02: 456 frames, ONE continuous run at uniform 3.00 s cadence,
  wrapping DSC_9999 → DSC_0001 — by NAME the last ~192 frames shot sort
  FIRST, and **0 of 456 frames occupy the same position under the two
  orderings**. The groups builder sliced `find | sort`, so one group would
  have straddled the wrap, joining frames ~20 minutes and ~6° of sky apart
  into one sub-stack — invisible downstream (the member just registers and
  stacks worse). IT IS NOT A RE-AIM, though the symptom looks like one:
  `segment_runs` treats a frame-number discontinuity as a boundary, so it
  reports such a set as TWO capture runs (a narrowed baseline for
  `mount_probe.sh`, not a wrong answer — but a consumer must know a wrap
  looks like a boundary to it). FIX shipped: `scripts/lib/frame_order.py`
  orders by EXIF epoch, wired into `run_undistort_groups.sh`; it reads paths
  from STDIN, not argv (an ARG_MAX split through `xargs` would re-introduce
  the bug per-chunk), warns loudly when capture and filename order differ,
  and falls back to the given order with a warning when epochs are
  unreadable. Blast radius: 12 of 13 sets have name order == time order;
  only aug09/set-02 differs — completely. **The second edge is GUARANTEED to
  arrive: filenames are REUSED after the wrap** (the corpus is 6,938 frames
  into the 10,000-frame cycle; the next wrap reuses names aug09/set-02
  already holds), so **a frame's identity is (session, set, basename)** —
  never the basename alone across units. Checked: `cullspec.py` matches
  within one set and aborts on ambiguity; `frame_order.py` maps per-set;
  ingest manifests are per-unit — nothing currently pools raw frames across
  units by name.
- **`DATE-OBS` ON A GROUP SUB-STACK NAMES THE SET'S FIRST FRAME, NOT THAT
  GROUP'S EPOCH — pairing it with the group's own WCS manufactures a
  drift.** Every `sub_*.fit` of a set carries an IDENTICAL `DATE-OBS` while
  each group's WCS centre has moved with the sky (~5° of RA across five
  groups), so anything reading a group's pointing and timestamp together
  combines a MOVED position with a FROZEN clock. Cost when it bit: an
  observer-frame alt/az measurement read 3.933° of within-set spread on a
  FIXED tripod (true answer zero); recovering each group's epoch from the
  drift itself (`t0 + ΔRA / 15.041°/hr`) dropped it to 0.088° — **45×**
  (implemented: `observer_frame_diversity.py` derives per-group epochs).
  **The tell is that the error is PLAUSIBLE** — 3.9° looks like a real
  re-aim, so only a control that knows the true answer catches it.
  `LIVETIME` is per-group exposure, not wall-clock cadence — not the
  shortcut either. Same family as `fingerprint.field_center` being the first
  frame's solve: a per-set quantity stamped on a per-group artifact, with
  nothing in the name saying which.
- **`seqapplyreg -framing=max` ON A VARIABLE-SIZE SEQUENCE GIVES EVERY OUTPUT
  ITS OWN ORIGIN — registered copies are NOT in a common coordinate frame,
  and anything cross-matching their pixel coordinates is measuring nothing.**
  Every compose here is variable-size (each member is its own group's
  `-framing=min` product). MEASURED on the 28-member union: the same sky
  lands **611.9 px apart in x / 416.0 in y** between two registered copies,
  constant to 0.4 px across three sky points — a pure translation, so only
  the ORIGIN differs; and matching two consecutive members yields the smooth
  tolerance-growth signature of chance nearest neighbours, not
  correspondences. **What it cost:** `member_separation.py` — then the
  compose's acceptance gate — read those copies, so every number it produced
  was a chance distance (it ranked its calibration cells correctly by luck
  of a monotone confound, and starved to UNMEASURED exactly on the union it
  existed for). The fix is not to solve every member: `register -2pass`
  already wrote one homography per member into the `.seq`, so pushing each
  member's OWN `findstar` positions through `H_ref⁻¹·H_m` puts everything in
  the reference frame by construction — **67 matches before, 1721 after
  (25×)**, 0/378 pairs unmeasured. **The general rule: never assume a tool's
  batch output shares a frame — verify with the tool's own coordinates**
  (two solves, or one known displacement pushed through, settles it in a
  minute; this went unverified through a build, a validation exercise and a
  shipped product).
- **`member_separation.py`'s ZONES WERE CANVAS-RADIAL, WHICH IS THE WRONG
  VARIABLE: a member's residual distortion is a function of ITS OWN field
  radius.** Canvas radius equals field radius only when members are near
  co-pointed — true for every cell it was validated on, false across a
  re-aim, where the canvas centre lies between two optical axes (measured
  symptoms: a non-monotonic profile and a corner median swinging
  0.71 → 3.38 on a 0.10 change of zone bound). Re-binned by
  `max(ρ_a, ρ_b)` — each star's radius in its own member, worse of the two —
  the profile is monotone and tight: **0.22 / 0.48 / 1.30 / 2.43 px** across
  centre/mid/outer/corner on the 28-member union, stable across `--tol` 8–30.
  **Two results the fixed binning delivered:** the disagreement is NOT a
  function of night or set — same-night pairs median 2.44 px, cross-night
  2.39, same-SET 2.21 — so **cross-night combining is exonerated and the
  within-set compose implicated**, independently of the star-shape ladder.
  **THRESHOLDS DO NOT SURVIVE AN INSTRUMENT CHANGE — and a threshold on an
  unattributed quantity is not worth writing at all:** re-measured on the
  fixed instrument, the old bands' ordering held but the user-PASSED
  product's own pair crossed out of PASS. **RESOLVED, user-ratified: the
  whole threshold layer is REMOVED** (no PASS/WARN/BLOCK; the number is
  measured, printed and stamped) — the quantity is a SUM of two terms, one
  created by the compose itself (2.5–4.7× from sequence size alone), and any
  band separating the accepted products would fire on every real compose.
  **A band belongs to a quantity whose good-vs-bad is established; until the
  driver is attributed, measure and record** (`docs/combine-contract.md` §5
  carries the current state; the constant-free discriminator is the RELATIVE
  break-away, 2.5–3× the member cluster's own scatter in five sets, ~15× in
  the sixth).
- **A PSF FITTER IS THE WRONG INSTRUMENT FOR STAR DOUBLING** — it fits one
  component, not the blend, so a doubled corner can read BETTER than a
  merely soft one. MEASURED: corner `findstar` FWHM ranked the failing
  own-model union (4.95 px) as better than the visually-clean single-model
  control (5.29 px) — the ordering the eye reverses; `seqtilt` is weaker
  still (0.34 px for the FAILING union against 0.40 for the PASSING one).
  For member-to-member disagreement use the mechanism directly: register the
  members, `findstar` EACH separately, and mutually match the star lists —
  the separation of the same star as two members place it is the defect, in
  px, with no fitter in the way. (Box medians are blind to it too — that
  cost this investigation two prior sessions.)
- **PRE-REGISTRATION FRAME-WIDTH CROPPING (the retired `--crop-lr` knob)
  STARVES A framing=max UNION'S RIMS — a 5%/side crop is a ~100% cut of the
  rim's cross-set supply, because rim sky is covered ONLY through members'
  frame-edge bands.** MEASURED at the cross-night combine (aug06+aug14, 38
  members, 4138 frames, same reference pinned, one knob): every hypothesis
  the knob was built on failed — cross-night centre member agreement WORSE
  (pair separation 0.718 → 0.895 px, +25%, later attributed to the unguarded
  member solves, `plate-solving-wcs.md`), amplitude-matched stars −3.43%,
  roundness NULL — and the union's smeared left rim fell from 7 members / 4
  sets to 2–3 members of ONE set: aug14/set-04's own field-edge PSF
  (3.34–3.44 px / roundness 0.65–0.69, measured on the members, identical
  cropped vs uncropped at n≈1800 matched stars) standing nearly alone where
  the control still blended aug06/set-02's 2.735/0.814. Composite tracked its
  contributors, 3.257 → 3.487. After the member-solve repair the
  geometry-class rim positions healed (+0.133 → +0.055, +0.155 → +0.102) but
  the composition core stayed (+0.22…+0.32): the sharp sets' data for that
  sky no longer exists in the cropped frames, and nothing downstream can
  restore it. Owner-rejected as a route; a rim-trim workaround (crop the
  product to a measured-parity frame) was built, passed its pre-registered
  bars, and was REJECTED as symptom-treatment — the records live under
  `datasets/corpus/crop_work/`. The knob's implementation (Siril `seqcrop`
  after the darktable warp, before register — that insertion point was
  correct and probed bit-identical) is recoverable at `690746c`. What the
  knob DID buy: removing rim dilution exposed the latent member-solve defect
  both chains carried (`plate-solving-wcs.md`).
- **THE DELIVERED ZERO POINT OF ANY `-output_norm` STACK IS (the composite's
  sky − its darkest non-zero pixel) OVER (brightest − darkest), ONE global
  (min, max) across all three channels — so the linear product's LEVEL and
  its R:G:B BALANCE are set by a single pixel, and the normalization
  reference's level CANCELS.** MEASURED (Siril 1.4.4 tag source
  `median_and_mean.c` `norm_to_0_1_range`, read independently by two
  sessions; instruments Siril `seqstat full`, `stat`+`boxselect`, the
  kept-scratch `r_s_.seq` M lines; `datasets/corpus/pedestal_work/`, ledger
  aug14 `pedestal_8pct_hypothesis_C_output_norm_minmax`): the model
  O_c = (L_c − μ)/D closes on six framing=max products (D across channel
  pairs within 0.1–0.4%, n = 13/38 members) and EXACTLY on the two aug06 arms
  re-stacked without `-output_norm` (D 1.0323 ×3 / 1.0645 ×3; μ 31.16 / 47.39
  = the darkest pixel to 0.001 ADU16). The crop5lr "+8.3% pedestal" is
  (L−μ) 1.12–1.28× times D 0.97 — the reference member's own group-tier level
  plus a darkest pixel that moved 31.2 → 47.4; on the aug14 pair the reference
  level was identical (66.55 vs 66.56) and R still HALVED from μ 25.9 → 46.8,
  and re-solving the members moved it back to 27.3. **The reference is NOT
  the level anchor**: one knob, `setref` on the same registered copies (4
  runs, 2 arms), moved the products ≤2.4% where the anchor reading predicted
  1.7–2.3× and a 42% drop (director re-measure by Siril `stat` medians:
  1.0222/1.0243/1.0089 for setref 4); the `setref s 1` pin works by fixing
  the registration GEOMETRY (which pixel is darkest), not the level. **The
  darkest pixel is lanczos4 undershoot two columns from a bright star**
  (11,237- and 1,977-ADU16 neighbours, 285–1584 px from any edge, no zero
  within 5×5 — a numpy DIAGNOSTIC, because Siril's `stat` min INCLUDES zeros
  and cannot report the darkest non-zero pixel), not a rim blend.
  **Consumers that read the lottery as signal:** `baseline_guard.py`
  `centre_median_per_channel` (25% tolerance; +56% and −49% moves with the
  data unchanged) and any cross-product level/colour comparison on linear
  stacks. **Two traps:** "maxima agree, so `-output_norm` is excluded" tests
  the max half of a min–max formula (those maxima are the R value of the star
  whose G peak is the global max, 65535.0 in both); and the composite's own
  location sits 0.34–0.44 ADU16 (0.3–0.5%) below the reference's on both
  arms, nearly channel-independent — the coverage/gradient term a
  three-channel closure cannot see. **Design consequence SHIPPED at every undistort
  stack line and OWNER-ACCEPTED 2026-08-29** (the queue item `output-norm-zero-point`
  is closed; its measured record is `datasets/corpus/campaign_zeropoint/campaign_record.json`
  + ledger aug06 `output_norm_zero_point_*`): no `-output_norm` at the compose,
  per-set-final and sub-stack tiers, the sub-stack reference pinned (`setref lt 1`),
  the anchor stamped (`ANCLOC*`/`ANCSCL*`/`ANCREF`/`ANCSRC`, `STACKNRM=addscale`),
  Siril's own "Output normalization ...... disabled" asserted; `baseline_guard`'s
  level rows advisory while STACKNRM differs from the baseline's, and its absolute
  corner-spread ceiling a manual-examination WARNING on a crossing only (owner-directed after it misfired
  on aug14/set-05's Milky Way gradient — a true 4.38% spread the measure cannot tell
  from a flat error; the over-baseline rule still catches the `--desky` class). From-raws rebuild of
  the whole corpus under one HEAD: level = the anchor on 99/99 products (finals
  0.1-0.4% under; members 0.25-0.87% under, unattributed), 0 clamps, 0 holes on every
  composed product (29 single-pixel undershoot pits on 21 of 77 members, all beside
  bright stars), K old-vs-new scattered (finals ΔK_G −0.004 ± 0.003), finals visually
  indistinguishable from their `-output_norm` twins; every canonical member had been
  STRETCHED ×2.6-2.8 by its group's min-max (14-bit raws saturate at 0.25 of the
  container). The standard route (`run_pipeline.sh`) still stacks with `-output_norm`
  — BACKLOG:`standard-route-output-norm`.
