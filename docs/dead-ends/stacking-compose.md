# Stacking, groups, and the sub-stack compose

Part of the dead-end registry — `docs/dead-ends.md` is the index, and
`00-registry-contract.md` governs how entries are read, cited, written and
deleted. Entries are maintained IN PLACE (pre-compression forms are in git;
the pre-split single-file registry is `docs/dead-ends.md`'s own history).
Cross-references to sibling files are written as (`<file>.md`) pointers.
Compose-defect status home: BACKLOG:`compose-homography-smear` (astrometric
route SHIPPED; surviving union band attributed member-borne, compose
exonerated for it).

<!-- registry content below; docs/dead-ends.md is the index -->
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
  field, sag does not. The site is tracked (`scripts/setup/site.json`,
  resolved into every acquisition record, no silent default) and the corpus
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
