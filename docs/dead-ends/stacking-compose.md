# Stacking, groups, and the sub-stack compose

Phase-1 split of `docs/dead-ends.md` (organize-only; the original file stays
the live registry until the merge is decided). Content below the marker is
VERBATIM from the original, so in-text "above"/"below"/section references may
point at entries now homed in a sibling file — `README.md` in this directory
carries the index, the assignment rule, and the block manifest that resolves
them. Do not edit below the marker while the refactor is in phase 1; the split
is re-derivable from the manifest and verified byte-identical by `split.py`.

<!-- == verbatim content from docs/dead-ends.md below this marker == -->
- **A `-framing=min` CANVAS IS SIZED BY TIME SPAN, NOT FRAME COUNT — so a
  metric taken at a margin relative to each canvas's own edge is not
  like-for-like across sets.** The intersection keeps only what every frame
  covers, so the trim is how far the sky swept, which at a fixed cadence is the
  burst duration. MEASURED, july31: set-04 ran 777 s and lost 605 px of x;
  sets 01-03 ran 1497-1624 s and lost 1153-1163 px, leaving set-04 with the
  LARGEST canvas (5459x3858) and the FEWEST frames (260) — the same fact stated
  twice. `regional_stat.py` at margin 200 puts set-04's boxes 279 px further
  out in x than set-01's; re-measuring all four at a common physical extent
  moved the numbers 0.40/0.49/1.03/1.17 -> 0.48/0.49/1.09/1.33 — set-04 got
  WORSE, so the geometry is not the explanation, but the corrected shape is a
  STEP between set-02 and set-03 rather than a monotonic doubling.
  Second-order but unmodelled, and live: the total trim runs **1.16-1.29x the
  pure translation** in every set. The excess is field rotation — a
  non-tracking alt-az head rotates the field as well as drifting it — plus the
  warp border and the groups route's two-stage framing. `fingerprint.py`
  computes translation only, so every disk and framing figure derived from
  `drift_px` under-counts.

- **THE SUB-STACK COMPOSE IS A MOSAIC, NOT A STACK — and a single HOMOGRAPHY cannot
  align members whose optical axes are degrees apart while any lens-model residual
  survives. This is the largest star-shape defect measured in this repo's products,
  and it is invisible to every per-member measurement.** A group is a CONSECUTIVE
  time block, so within one 1497 s burst the sky sweeps 6.25° of RA and the five
  members of one set solve to centres **4.28° apart** (aug06/set-01: RA 303.87 /
  304.78 / 306.03 / 307.41 / 308.16). Composing them is stitching different
  pointings, and the registry's own Szeliski result then applies one level up: the
  true member-to-member map is `distort ∘ H ∘ distort⁻¹`, and `register -2pass`
  fits `H` alone.
  MEASURED (Siril `findstar`, open gate, 800 px boxes placed by each product's own
  solved WCS and VERIFIED by Siril's own per-star RA/Dec; FWHM/roundness = medians
  of the 30 brightest fits, so products of very different depth are rank-matched):
  at **RA 294.86 / Dec +44.99** all five set-01 members read **2.42–2.54 px /
  roundness 0.924–0.942** at own-field radius 0.41–0.62 — mid-field, not an edge —
  and their own 5-member compose reads **3.48 / 0.582**. The 13-member 3-set union
  adds 0.530, the 28-member cross-night union 0.458: **the within-set step is most
  of it.** Control, same instrument, same members, RA 314.72: members 2.23–2.38 /
  0.903–0.958, compose **2.43 / 0.949** — the compose costs nothing there.
  **The discriminator that names the fix:** the members' OWN astrometric solutions
  place the same stars within **0.10 px median / 0.26 px p90** (10 pairs, n=1151)
  at exactly the sky where the homography compose loses 1.06 px of FWHM and 0.34 of
  roundness. The alignment information exists; the homography discards it. That is
  the measured case for per-image astrometric resampling
  (BACKLOG:`compose-homography-smear`, SWarp) rather than a better
  shared lens model.
  **Blind to it:** every per-member measure (each member is clean), and — as the
  accepted product shipped — the compose's own geometry measurement, whose zones
  were then CANVAS-radial and which returned **UNMEASURED** on this union
  (378/378 pairs, no zone with ≥100 matched stars). `member_separation.py` has
  since been rebuilt (member-own field radius, 0/378 unmeasured) and its
  threshold layer removed by user ratification — it measures, it does not gate
  (`docs/combine-contract.md` §5).
  **The disagreement is TWO terms, both measured, neither yet sized against the
  other.**
  *(a) The compose makes part of it.* The same members disagree more when
  registered inside a big sequence than when composed among themselves:
  july31/set-01 **1.12 → 3.02 px**, aug06/set-03 **0.95 → 3.38 px** going from
  their own 4–5-member compose to the 41°, 28-member union. `register -2pass`
  fits ONE homography per member against a common reference, so a member
  overlapping that reference over a limited region gets a compromise fit that
  extrapolates badly elsewhere — and two members compromised over *different*
  regions disagree with each other.
  *(b) One set carries a genuine OPTICAL-STATE CHANGE MID-BURST.* aug06/set-01's
  groups 1,2,3 agree to **0.21–0.34 px** and groups 4,5 sit **2.95–4.91 px**
  away, across a boundary that is 100 consecutive frames into a 1497 s burst.
  Three things rule out the alternatives: it is not pointing spread (members 1
  and 3 are **2.16° apart at 0.34 px**, members 3 and 4 are **1.38° apart at
  3.14 px** — a smaller separation giving 9× the disagreement); it is not the
  registration reference (1|4 reads **2.95 / 2.98 / 3.02 px** with the reference
  set to member 1, 3 and 5 in turn, every other pair moving <2%); and the
  disagreement NORMALISED BY AXIS SEPARATION — the quantity a single shared
  optical state holds constant — is flat at **0.21 / 0.23 / 0.32 px per degree**
  for groups 1,2,3 and reads **3.07 and 3.58 px/deg** for 3|4 and 4|5, with 4|5
  reaching 1.97 px at the SMALLEST adjacent separation of the five (0.55°).
  Acquisition is exonerated as a cause of any interruption: all 500 frames are
  2.5 s / ISO 1600 / f/4 / 70 mm at a 3.00 s interval (min 2.99, max 3.01) with
  **no gap anywhere**, including at that boundary.
  **A TRAP WORTH KEEPING: the residual's cos(θ) DIPOLE is NOT evidence of a
  decentring.** Two members sit at different pointings, so differencing ONE
  radial field about two displaced centres gives a dipole by construction, with
  amplitude proportional to their axis separation — the null expectation, not a
  mechanism. Reading it as "the optical axis moved" was an error made and
  retracted here; only the separation-normalised ratio discriminates, and it says
  the optics changed without saying what kind of change it was.
  **RESOLVED — it is BOTH, and they are separable. MEASURED, one knob, 250 frames
  warped once and shared by every arm.**
  *(i) The per-group AUTO-PICKED registration reference is worth 6.5x on its own.*
  The picks wander badly — read straight out of the `.seq` at frames
  **6, 26, 15, 3, 26 of 50** — and the break always lands on whichever member's
  reference sits LATEST. Five independent per-block registrations give a worst
  pair of **3.12 px**; ONE global reference over the same frames gives **0.48 px**.
  The split position moves with the picks (3|4 in the shipped 100-frame build,
  4|5 here), which is the tell.
  *(ii) But one reference only MOVES the error, it does not remove it* — from
  between-member DOUBLING into within-member BLUR, 0.25-0.27 px against 3.12 px.
  *(iii) The underlying change is PHYSICAL, TIME-PROGRESSIVE and ONE-SIDED.*
  A first single-reference arm is USELESS for this question if the reference
  auto-lands at an end (it did: frame 6 of 250), because then "late" and "far
  from the reference" are the same thing. Pinning it to the MIDDLE (frame 125)
  separates them: at MATCHED drift distance the late block beats its early twin
  by **+0.25 px / -0.064 roundness** (99f vs 101f) and **+0.27 px / -0.104**
  (49f vs 51f) — on the LEFT field only, while the right field is flat across all
  five blocks (2.49-2.59 px, roundness 0.850-0.874). The ordering is TIME, not
  distance: block 3 sits ONE frame from the reference and reads 2.67 px on the
  left where block 1, 99 frames away, reads 2.54.
  **Mechanism undetermined; two candidates, one discriminator.** Differential
  atmospheric REFRACTION is horizon-fixed and therefore sensor-fixed on a fixed
  tripod, progressive as altitude changes, and non-homographic by construction —
  the same open question as BACKLOG:`one-sided-band`. Mechanical SAG of an
  extended zoom barrel is also progressive and one-sided. Refraction scales with
  zenith distance and reverses sense between a rising and a setting field; sag
  does not. **THE SITE BLOCKER IS GONE — it was a RECORDS gap, not a data gap.**
  The EXIF still carries no GPS, but the observing site is tracked:
  `scripts/setup/site.json` (SITELAT **+REDACTED_SITELAT**, SITELONG **−REDACTED_SITELONG**,
  positive-east), resolved into every acquisition record by
  `scripts/lib/acquisition.py` with a per-session override and no silent default.
  Hour angle is therefore derivable and the rising-vs-setting sense test is
  runnable. **AND THE CORPUS CARRIES BOTH SENSES — MEASURED, not assumed:** over
  the 23 solved products the signed hour angle spans **−2.35 h to +0.98 h**, i.e.
  **20 pre-meridian against 3 post-meridian**, so the test is not unrunnable for
  want of a setting field. **THREE LIMITS TRAVEL WITH THAT, because a blocker
  replaced by an overstated capability is not an improvement.** (1) The
  coordinates are OWNER-SUPPLIED and TRANSCRIBED, not derived, and
  `scripts/setup/verify_site.py` bounds them at the DEGREE level ONLY — it refutes
  a flipped longitude sign (min altitude **−7.78°**) and a lat/long transposition
  (**−50.18°**) by putting a photographed target below the horizon, but a
  transposed digit shifts every altitude by just **0.290° in latitude and 0.068°
  in longitude** and is undetectable. A transcription error has already happened
  in this chain once and was caught by a second source, not by re-reading. The
  derivation that would close it — latitude and LST recovered from field rotation
  across solved frames — needs per-frame solves and is unbuilt. (2) SITEELEV is
  still unrecorded, so the derived OBSGEO triple is computed at h = 0 m. (3) The
  whole corpus sits at **altitude 63.4–87.7°, |HA| ≤ 2.35 h** — the flat end of
  the refraction curve — so both senses being present does not make the lever
  large, and how much sense-reversal signal survives at these zenith distances is
  UNQUANTIFIED. The second disjunct, the same middle-pinned build on sets shot at
  different altitudes, is unchanged and needs no coordinate at all.
  **What that does and does not license.** It does NOT revive per-set models — a
  per-set model would be wrong for part of its own set. It establishes that the
  OPTICAL-STATE tier can be finer than the SET tier and that a state boundary is
  something to DETECT, which is what this measure now is. Still open: what
  physically changed at that boundary (focus/temperature drift and a mechanical
  shift both predict a radial term), and the split of the union's 2.43 px corner
  median between (a) and (b).
- **A PRODUCT-LEVEL A/B cannot audit a transient's rejection — the dilution is
  the instrument's blind spot.** Differencing a full-depth stack against a
  control with the transient's frames excluded is the obvious test and it is
  UNDER-POWERED by construction: the groups route divides the transient's
  per-frame amplitude by the group size and then again by the compose's member
  count. MEASURED on july31/set-03's aircraft: a trail pixel carries ~766 ADU
  above a ~1140 ADU sky per frame, which after a 100-frame group mean and a
  5-member plain-mean compose is 1.5-4.1 ADU per trail pixel — 0.02-0.06 ADU
  once spread over a 400 px box, against that difference's own 0.2 ADU
  box-to-box spread. So a FLAT product difference is equally consistent with
  rejection and with no rejection, and reading it as a pass is the same error
  as any other blind instrument here. Audit rejection where it HAPPENS: Siril
  `stack ... -rejmaps` writes the per-pixel record of which samples were
  discarded, and differencing the map of the group WITH the transient against
  the same group WITHOUT it leaves the transient's own track and nothing else
  (its median equals the arithmetic scale step between the two frame counts,
  which calibrates the map for free). The on-track residual is then measured at
  GROUP level, where the signal is 5x larger and a 60 px box sees an unrejected
  trail at ~0.9 ADU against a +-0.2 ADU spread.
- wFWHM weighting at low FWHM spread is WORSE than none (`-weight=wfwhm` is a
  min-max ramp → worst frame ~0 weight at any spread).
  **SCOPED — this was written as *"Siril `-weight` is a min-max ramp"*, which is
  TRUE of `wfwhm` and `nbstars` and FALSE of `noise`.** `-weight=noise` is
  inverse-variance, as this repo's own shipped compose has said all along
  (`run_undistort_compose.sh:342`, *"weighted by member noise, inverse-variance"*,
  with the n/s² derivation at `:101-108`). **This is the instance the SUBJECT axis
  MISSES** — the widening is inside the flag rather than across it — so it is the
  worked example for the granularity bound stated in this file's preamble. The
  wFWHM finding itself is unaffected. (Mode split: the Oracle's.)
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
  map);
  **SCOPE OF THOSE TWO NUMBERS, ADDED BECAUSE THEY WERE QUOTED OUT OF IT TWICE:
  they are STAR-PAIR-route measurements** — the sentence says so in its own
  wording (*"AFTER the 2pass"*) and `register -2pass` is now the REGRESSION ARM
  behind `--starpair`, not the shipped route. The shipped route is
  `seqplatesolve`. The mechanism was RE-MEASURED there and the practical claim
  SURVIVES while the stated mechanism does not: one knob (4 members, 2 nights,
  same framing/weight/order, only `--ref` moved) gives canvas 7071×4629 →
  7095×4622, north +9.6244° → +7.7633°, centre-median R/G/B [39.9, 157.4, 116.9]
  → [26.9, 90.5, 47.6], B/G 0.7427 → 0.5260 (Siril `stat` via
  `scripts/qa/regional_stat.py`, box 400 margin 200). **So the reference is LIVE
  on the astrometric route — but the canvas does NOT inherit the reference's
  orientation there**: m_1's own north is −164.85° and its canvas is +9.62°. It
  TRACKS the reference without equalling it, and the relation is uncharacterised
  (two points). The `-framing=max` canvas differed by 24×7 px between arms, so
  the centre box samples slightly different sky — that BOUNDS the balance shift,
  it does not isolate it. **Do not cite the K_B pair as evidence about the
  shipped route, and do not cite the astrometric numbers as evidence about
  star-pair.**
  **AND THE BALANCE HALF IS REAL AT THE COMPOSE AND IMMATERIAL AT THE
  DELIVERABLE — SPCC ABSORBS IT, MEASURED, 64x.** The compose is not the product:
  `spcc_run` fits K factors against the Gaia catalogue afterwards, and the
  reference's balance imprint is most of what it removes. Same two arms, Siril
  `stat` (box 400 / margin 200) on the linear surface before and after:
  B/G **0.7427 vs 0.5260 (delta -0.2167)** at the compose, **0.9962 vs 0.9927
  (delta -0.0034)** after SPCC; R/G +0.0437 -> -0.0016. The mechanism is visible
  in siril's own K factors, which move to compensate: B 0.862 -> 0.923,
  G 0.678 -> 0.672. Both arms carry the SAME documented sensor gap (no matching
  sensor; generic response), so it cancels rather than confounds.
  **CONSEQUENCE FOR THE CHOICE OF REFERENCE: it is a GEOMETRY decision, not a
  colour one.** What survives SPCC is the canvas (SPCC does not touch it); what
  does not survive is the balance. A reference criterion should therefore be
  argued on coverage, not on channel balance — the raw compose numbers make it
  look like a colour decision and it is not.
  **BOUNDS, and they are load-bearing:** 4 members / 2 nights, so the canvas
  difference here is 24x7 px on ~7000x4600 (0.34% / 0.15%) and NOTHING here
  measures what it is at 77 members. The residual B/G 0.0034 is ~3 steps of the
  instrument's resolution (`stat` medians resolve ~0.1 ADU on ~105), so it is
  small, not zero. The arms' absolute LEVELS differ (104.5 vs 54.8) and that is
  NOT attributed here — different canvases sample different sky, so level and
  sky are confounded in this pair.
  **AUTO IS INDEX 0, NOT A RANKING** — verified across ten `compose_gate_*.json`
  records at 13/17/22/25/52/77 members, every one `reference_member = s_00001`,
  and confirmed by a probe whose auto arm measured **0 differing pixels of
  98,194,977** against an explicit `--ref=1`. A build record asserting the
  auto-pick *"ranks over the whole member pool"* was wrong. The consequence is
  narrower and sharper than a ranking: **the reference is whatever sorts FIRST**,
  so appending a night re-bases nothing and reordering the arguments re-bases
  everything.
  **THE REFERENCE IS NOW ON THE ARTIFACT** (`REGREF`/`REGREFSR`, siril's own
  value parsed from the `.seq`) — before that it survived only in
  `compose_gate_*.json`, which outlive the run only because they are written
  outside the scratch dir `rm -rf "$W"` deletes. Products built earlier carry no
  `REGREF` and are not backfilled; the corpus's is in
  `datasets/corpus/corpus4_build_record.json`.
  Also measured alongside: a crop-coverage guard of `Min > 0` PASSES on
  lanczos edge-ringing residue (Min 7–26 on a ~90 sky) — require the SIBLING-CLASS SKY FLOOR
  (Min ≈ 80s here), never mere non-zero.
  **THE SAME PIN ALSO MOVES THE CANVAS SIZE, AND A ONE-SET VERIFICATION OF IT
  CAN BE FOOLED BY COINCIDENCE.** MEASURED on aug06, identical members proven
  bit-identical first (0 differing of 893,212,122 px across 13 members): the
  same three sets composed WITHOUT `setref s 1` and WITH it deliver
  set-01 4907×3598 / 4907×3598, set-02 4894×3752 / **4902×3633**, set-03
  4900×3719 / **4903×3675**. Set-01 is unchanged only because its unpinned
  auto-pick already landed on member 1 — the very member the pin selects. So a
  product built before the pin and one built after are NOT interchangeable as
  each other's baseline, and checking agreement on one set can report
  "bit-identical" for a change that moves two others. Check every set, or check
  the set whose auto-pick differs. **Consequence for A/B work: a baseline must
  be built by the SAME code as its arm, not merely from the same frames** — the
  cheap tell is that both routes leave their generated `.ssf` on disk, so
  diffing those two files names the difference without running anything.
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
  OSC-only win (cleaner colour noise).
- **THE FRAME COUNTER WRAPS AT 9999 -> 0001, AND FILENAME SORT IS THEN THE WRONG
  ORDER — groups are consecutive TIME blocks.** Measured on aug09/set-02: 456
  frames, ONE continuous 22.8-minute run at a uniform 3.00 s cadence (epoch
  deltas min 3.0, max 3.0 — no gap anywhere), wrapping DSC_9999 -> DSC_0001.
  | order | sequence |
  |---|---|
  | by NAME | DSC_0001 … DSC_0264 , DSC_9808 … DSC_9999 |
  | by TIME | DSC_9808 … DSC_9999 , DSC_0001 … DSC_0264 |
  **0 of 456 frames occupy the same position under the two orderings.** The
  groups builder sliced `find | sort`, so the first group would have been the
  LAST 100 frames shot and one group would have straddled the wrap — joining
  frames ~20 minutes and ~6 deg of sky apart into a single sub-stack whose
  pointing is the average of two ends of the drift. Nothing downstream could see
  it: the member simply registers and stacks worse, with the cause invisible in
  the product.
  IT IS NOT A RE-AIM, and it is worth saying because the symptom looks like one:
  `segment_runs` reports such a set as TWO capture runs, because it treats a
  frame-number discontinuity as a boundary. That is what made `mount_probe.sh`
  confine its windows to 264 of 456 frames here. The probe still read a decisive
  fixed signature (15.076 deg/hr against sidereal 15.041), so that is a NARROWED
  BASELINE rather than a wrong answer — but a set whose two runs are really one
  should not be split, and any future consumer of `segment_runs` needs to know
  a wrap looks like a boundary to it.
  FIX: `scripts/lib/frame_order.py` orders by EXIF epoch and is wired into
  `run_undistort_groups.sh`; it reads paths from STDIN rather than argv, because
  a 500-path list through `xargs` can be split at ARG_MAX into chunks that would
  each be ordered independently — reintroducing the bug in a subtler form. It
  warns loudly whenever capture order and filename order differ, and falls back
  to the given order with a warning when epochs are unreadable.
  BLAST RADIUS, measured across the corpus: 12 of 13 sets have name order ==
  time order exactly. Only aug09/set-02 differs, and it differs completely.
  **THE SECOND EDGE — FILENAMES ARE REUSED AFTER THE WRAP.** The counter cycles
  every 10,000 frames and this corpus is already **6,938 frames into that
  cycle** (6,938 distinct basenames across 6,938 frames — zero collisions
  TODAY). The next wrap reuses names this corpus already holds: aug09/set-02
  owns DSC_0001–DSC_0264, and a future night crossing 9999 will produce those
  names again. So **a frame's identity is (session, set, basename); the basename
  alone is not a key** and must never be used as one across units. Checked
  today: `cullspec.py` matches filename digits WITHIN one set (unique there, and
  it already ABORTs loudly on an ambiguous exclude), `frame_order.py` maps names
  per-set, and the ingest manifests are per-unit — nothing currently pools raw
  frames across units by name. This is recorded because it is guaranteed to
  arrive, not because it has bitten yet.

- **`DATE-OBS` ON A GROUP SUB-STACK NAMES THE SET'S FIRST FRAME, NOT THAT GROUP'S
  EPOCH — SO PAIRING IT WITH THE GROUP'S OWN WCS MANUFACTURES A DRIFT.** MEASURED:
  every `sub_*.fit` of a set carries an IDENTICAL `DATE-OBS` while each group's
  WCS centre has moved with the sky — aug06/set-01 runs **303.663 → 308.545 deg of
  RA across five groups**, july31/set-03 **311.782 → 316.745**. Anything that reads
  a group's pointing and its timestamp together is therefore combining a MOVED
  position with a FROZEN clock. **Cost when it bit: an observer-frame alt/az
  measurement read 3.933 deg of within-set spread on a FIXED tripod, where the
  physical answer is zero. Recovering each group's epoch from the drift itself
  (`t0 + ΔRA / 15.041 deg/hr`) dropped it to 0.088 deg — 45x.**
  Same family as `fingerprint.field_center` being the FIRST frame's solve rather
  than the set's pointing: a per-set quantity stamped on a per-group artifact,
  where the name gives no hint which it is. **The tell is that the error is
  PLAUSIBLE** — 3.9 deg looks like a real re-aim, so nothing about the number
  invites a re-check; only a control that knows the true answer is zero catches it.
  Consumers wanting a group epoch must derive it; `LIVETIME` is per-group exposure
  and does not carry wall-clock cadence, so it is not the shortcut either.

- **`seqapplyreg -framing=max` ON A VARIABLE-SIZE SEQUENCE GIVES EVERY OUTPUT ITS
  OWN ORIGIN — so registered copies are NOT in a common coordinate frame, and
  anything that cross-matches their pixel coordinates is measuring nothing.**
  Every compose here is variable-size: each member is its own group's
  `-framing=min` product, and those differ by tens of px. MEASURED two ways on
  the 28-member union. (1) Solving three registered members: the same sky lands
  **611.9 px apart in x and 416.0 px in y** between `r_s_00001` and `r_s_00026`,
  and the offset is CONSTANT to 0.4 px across three widely separated sky points
  — a pure translation, so scale and rotation ARE common and only the origin is
  not. (2) Matching two consecutive members of ONE set: **zero** pairs within
  1 px, 1 within 2, 12 within 5, 67 of 2000 within 12, 459 within 30 — growth
  smooth in tolerance, the signature of chance nearest neighbours in a dense
  field rather than of correspondences.
  **What this cost: `member_separation.py` — then the compose's ACCEPTANCE GATE,
  now report-only — read those copies, so every number it produced was a chance
  distance between two offset frames.** It ranked its six calibration cells correctly by luck of a
  monotone confound (a bigger optical disagreement also means a bigger framing
  offset), and it starved to UNMEASURED (378/378 pairs) precisely where the
  offsets were largest — the wide multi-night union it exists for. The fix is
  not to solve every member: `register -2pass` already wrote one homography per
  member into the `.seq`, so pushing each member's OWN `findstar` positions
  through `H_ref⁻¹·H_m` puts everything in the reference member's frame by
  construction. MEASURED on a real cell: **67 matches before, 1721 after** (25×),
  and 0/378 pairs unmeasured on the union, in 12 s.
  **The general rule: never assume a tool's batch output shares a frame — verify
  it, cheaply, with the tool's own coordinates.** Two solves, or one known
  displacement pushed through the pipeline, settles it in a minute; this went
  unverified through a build, a validation exercise and a shipped product.

- **`member_separation.py`'s zones WERE CANVAS-radial, which is the wrong
  variable: a member's residual distortion is a function of ITS OWN field
  radius.** Canvas radius equals field radius only when the members are near
  co-pointed — true for every cell it was validated on (98–500 px offsets),
  false across a re-aim, where the canvas centre lies between two optical axes.
  MEASURED symptoms on a cross-night pair: the profile went non-monotonic (outer
  2.07 worse than corner 0.71), the corner median swung **0.71 → 3.38** on a
  0.10 change of the zone bound, and the bootstrap band was 0.55–3.89. Now binned
  by `max(ρ_a, ρ_b)` — each star's radius in its own member, worse of the two —
  and the profile is monotone and tight: on the 28-member union the medians run
  **0.22 / 0.48 / 1.30 / 2.43 px** across centre/mid/outer/corner, at 142–783
  matched stars per zone, and the worst cell reads identically at `--tol` 8, 12,
  20 and 30.
  **Two results the fixed binning delivers immediately.** The disagreement is
  NOT a function of night or of set — same-night pairs median **2.44 px**,
  cross-night **2.39**, same-SET **2.21** — so cross-night combining is
  exonerated as a source and the within-set compose is implicated, independently
  of the star-shape ladder that found it. And the recorded "cross-night state
  difference 4.07 px", downgraded to unmeasured on the old instrument, stays
  unmeasured: it was taken with the canvas zoning AND the broken frame.
  **THRESHOLDS DO NOT SURVIVE AN INSTRUMENT CHANGE — AND A THRESHOLD ON AN
  UNATTRIBUTED QUANTITY IS NOT WORTH WRITING AT ALL.** The 0.35/1.00 px bands
  were anchored to six cells measured on the broken instrument; re-measured on
  the fixed one they read 0.14 / 0.21 / 0.38 / 1.23 / 3.04 / 3.28 against
  0.144 / 0.194 / 0.352 / 0.934 / 2.991 / 2.112 — the ordering holds and the
  floors barely move, but the user-PASSED product's own pair crosses out of PASS.
  **RESOLVED, user-ratified: the whole threshold layer is REMOVED rather than
  re-anchored** (no PASS/WARN/BLOCK, no `--accept-separation`, no abort; the
  number is measured, printed and stamped on the product). Re-anchoring was the
  wrong question, on two measured grounds beyond the instrument change: the
  quantity is a SUM OF TWO TERMS and the compose itself creates one of them
  (1.12 / 0.95 px composed among themselves against 3.02 / 3.38 px inside a 41°
  28-member sequence — 2.5–4.7×, from sequence size alone), and any band that
  separated the accepted products would fire on every real compose, which trains
  the operator to bypass it. **The general rule: a band belongs to a quantity
  whose good-vs-bad is established. Until the driver is attributed there is no
  such boundary, so measure and record — inventing a number to gate on is the
  guessing this repo forbids, and re-raising the decision is re-doing settled
  work** (`docs/combine-contract.md` §5 carries the current state; the
  discriminator that needs no constant is the RELATIVE break-away, 2.5–3× the
  member cluster's own scatter in five sets and ~15× in the sixth).

- **A PSF FITTER IS THE WRONG INSTRUMENT FOR STAR DOUBLING** — it fits one
  component, not the blend, so a doubled corner can read BETTER than a merely
  soft one. MEASURED: corner `findstar` FWHM ranked the failing own-model union
  (4.95 px) as better than the visually-clean single-model control (5.29 px) —
  the ordering the eye reverses; re-measured at matched canvas boxes the two
  read 3.92 vs 3.31 px at c11, a gap far smaller than the visual one. Siril
  `seqtilt` is weaker still: off-axis aberration 0.34 px for the FAILING union
  against 0.40 px for the PASSING one. For member-to-member disagreement use the
  mechanism directly — register the members, `findstar` EACH one separately, and
  mutually match the star lists; the separation of the same star as two members
  place it is the defect, in px, with no fitter in the way. (Box medians are
  blind to it too — that cost this investigation two prior sessions.)

