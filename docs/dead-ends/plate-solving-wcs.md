# Plate solving and WCS consumption

Phase-1 split of `docs/dead-ends.md` (organize-only; the original file stays
the live registry until the merge is decided). Content below the marker is
VERBATIM from the original, so in-text "above"/"below"/section references may
point at entries now homed in a sibling file — `README.md` in this directory
carries the index, the assignment rule, and the block manifest that resolves
them. Do not edit below the marker while the refactor is in phase 1; the split
is re-derivable from the manifest and verified byte-identical by `split.py`.

<!-- == verbatim content from docs/dead-ends.md below this marker == -->
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
  **SCOPE — THIS CLAIM IS ABOUT SINGLE TRAILED FRAMES ONLY, AND IT ONCE WIDENED
  PAST THAT SILENTLY.** Every measurement above is on single 2.5 s ultra-wide
  exposures. On STACKED MEMBERS, whose stars are round, Siril's own solver DOES
  handle this class — `seqplatesolve -order=3`, 2/2 solved, 388 and 371 matched
  stars (the *"Siril's internal plate solver DOES handle this class on STACKED
  members"* entry below). **Read this entry with that one or it reads as a
  capability claim about the tool rather than about the DATA**, which is how the
  belief widened before.
- **The fix: feed astrometry.net a SHAPE-BLIND xylist (its INTENDED override — solve-field
  on an xylist runs NO pixel extraction, matcher geometry-only, Lang 2010). Blind-solve
  first, label after.** Best source is SExtractor's core `sep`: returns trailed sources
  (median elongation ~1.3), blind-solves at HIGHER odds than in-house peak centroids
  (logodds 299 vs 289, scale Δ 1.2e-5), identical SPCC K — `solve_field.py` defaults to it
  (`extractor_ab.json`). Robustness ranking: (1) asnet + **sep** xylist — the sole
  extractor (the in-house peak-xylist fallback is RETIRED: sep passed every x86 solve at
  equal-or-higher odds, identical SPCC K); (2) `image2xy` xylist (shape-blind, untested —
  its trail knobs `-a`/`-p`/`-m` aren't exposed by solve-field and `-a` can fragment one
  trail into spurious detections); (4) `-localasnet` and ASTAP LEAST — both
  PSF-fit/roundness-gated (ASTAP docs: *"star streaks … will be ignored"*; wide DBs W08
  FOV>20°, G05 FOV>6°, G17/H17/H18 deprecated). Caveats: `--no-remove-lines
  --uniformize 0` (or list filters) still thin a supplied xylist; and two valid fits'
  centres can differ by hundreds of arcsec (the SIP wobble below), which never reaches
  SPCC (it re-matches stars from the seed).
- **A BIG UNION CANVAS DEFEATS THE SOLVE, AND THE ROUTE THAT WORKS IS TO SOLVE A
  CENTRAL CROP LIKE A MEMBER AND SHIFT `CRPIX` BACK BY THE CROP OFFSET —
  header-only, pixels untouched.** MEASURED on the 52-member corpus union
  (8510×5475, 46 Mpx, 52 member footprints): the hinted attempt failed on
  seam-contaminated detection and the blind fallback SHIPPED a false solution —
  RA 6.0 Dec −65.1 at 12.96″/px, logodds 22 against a healthy family of 100–570 —
  which siril SPCC then consumed to completion, producing plausible-looking K
  factors (G 0.592 against a 0.649–0.682 family) instead of failing. The
  recovery: crop the central region to scratch, solve it as if it were a member
  (logodds 130, 17.06″/px), then shift `CRPIX` by the exact crop offset. Validated
  by `shape_at_sky.py`'s own per-star RA/Dec verification at four positions
  INCLUDING ones far outside the solved crop, and SPCC on the corrected WCS
  returned K_G 0.669, in family.
  **Two traps measured on the way, both of which waste a session.**
  (1) `--central` is a fraction of the FRAME, i.e. a half-width per axis, so
  `--central=0.5` keeps the central half of each axis and `=1.0` restricts
  nothing — the semantics are pinned in `solve_field.py`'s docstring.
  (2) **`--max-stars=1500` explodes the quad search on a canvas this size: 64 min
  of CPU and NO result.** The default 200 is ample to MATCH; raise it only when
  the SIP distortion terms are the product being consumed, and not on a union
  canvas. The blind-fallback half of this incident is now gated — `solve_field.py`
  refuses a solution contradicting its own hints at exit 9, and this union is its
  recorded falsification case.

- **WHAT MAKES A `framing=max` UNION STARVE THE SOLVE: CANVAS SIZE AND SEAM
  FRACTION ARE BOTH DIRECTIONALLY REFUTED. The registration REFERENCE is the only
  candidate left standing — and it is a SURVIVING HYPOTHESIS, not a cause.**
  Two accounts were carried while a coverage-derived `--central` rescue was built:
  that big canvases starve, and that seam-contaminated ones do. **One knob killed
  both.** The four-night corpus composed twice from the SAME 77 members, same
  `-framing=max`, same `-weight=nbstack`, `STACKCNT 8349` / `LIVETIME 20872.5` /
  `NMEMBER 77` and byte-identical siril HISTORY — only the reference differs:

      reference member 1  (july31/set-01/sub_01, 0.746 deg from the median pointing)
          canvas 8515x5666 = 48.25 Mpx, 818/1040 boxes covered, rect 64.8%
          -> NO SOLUTION  (400 stars, no --central, position-hinted)
      reference member 36 (aug09/set-02/sub_02, 0.162 deg from the median pointing)
          canvas 8540x5685 = 48.55 Mpx, 803/1040 boxes covered, rect 61.2%
          -> logodds 507  (400 stars, no --central, FIRST attempt)

  **SIZE predicted larger-is-worse and the LARGER canvas solves. SEAM FRACTION
  predicted less-coverage-is-worse and the canvas with WORSE coverage and MORE
  uncovered boxes solves.** Both fail on DIRECTION, not on magnitude, and the
  effect spans the entire range from no solution to the highest logodds this
  corpus has produced. Coverage measured by `coverage_frame.py` (Siril
  `boxselect`+`stat`), both canvases on the same 40x26 grid.
  **WHAT SURVIVES IS WHATEVER THE REFERENCE CARRIES.** A more central anchor
  gives a smaller maximum off-axis angle across the members, which is a
  TAN-projection-breakdown reading rather than a seam one. **DO NOT PROMOTE THAT
  TO THE MECHANISM.** It is n=1, and moving `--ref` moves canvas geometry, tangent
  point and orientation TOGETHER — centrality is not isolated from them by this
  measurement, only from size and seam fraction, and those two are refuted rather
  than centrality being confirmed. The honest status is: **two corpses, one
  survivor, and the survivor is a bundle.**
  **CONSEQUENCE FOR THE COVERAGE RUNG (`solve_field.py`), which is NOT devalued:**
  it responds to a solve that ACTUALLY STARVED, never to a predicted cause, so a
  wrong account of the cause cannot mislead it. It measurably rescued the member-1
  canvas from NO SOLUTION to logodds 112 (shipped 400 stars) and 134 (200). But
  **the product that motivated it no longer needs it** — the member-36 canvas
  solves at 507 with the rung never firing. It is a GENERAL SAFETY NET for any
  union that starves; the REFERENCE DERIVATION is what fixed this product. An
  earlier revision of this repo's own guard attributed that starvation to coverage
  seams; that attribution was wrong and is corrected in place.

- **`--max-stars` DOES NOT HAVE A DERIVABLE OPTIMUM, AND TWO POINTS ON ITS CURVE
  ARE NOT A TREND.** A `--max-stars` derivation was SCOPED and then REFUSED on
  measurement; this entry is what the investigation produced instead.
  MEASURED on the four-night corpus at the coverage-derived `--central=0.694`,
  only this knob moving, and **deterministic** (three repeat runs at N=400 return
  `RA 309.682 Dec +41.281 scale 16.85 logodds 112`, every digit):

      100 -> logodds  84   (floor-class)
      200 -> logodds 134
      300 -> logodds 148   <- best
      400 -> logodds 112
      800 -> logodds 116

  **NON-MONOTONE and reproducible**, so the scatter is real rather than run-to-run
  variance. The pair that motivated the derivation — 400 -> 63 and 200 -> 106 at
  `--central=0.5` — reads as *"fewer is better"* and does not survive five points:
  300 beats 200, and 800 beats 400. **A rule fitted to this would encode which
  quads happen to match on one stack.** Do not tune this knob by intuition, and do
  not read two of its points as a direction.
  **THE SPATIAL-CLUSTERING ACCOUNT IS NOT VISIBLE IN THE DETECTIONS.** The
  derivation was to key on *"brightest-first selection clusters those stars in the
  band and leaves the corners carrying almost no constraint"*. Measured, sep's own
  detections on a 20x13 occupancy grid, at `--central=0.694`:

      N=100   85/260 cells   evenness 0.791   sd_x/w 0.186  sd_y/h 0.197
      N=200  140/260         evenness 0.874   sd_x/w 0.187  sd_y/h 0.190
      N=400  208/260         evenness 0.933   sd_x/w 0.184  sd_y/h 0.193
      N=800  248/260         evenness 0.964   sd_x/w 0.190  sd_y/h 0.196
      N=1600 258/260         evenness 0.986   sd_x/w 0.191  sd_y/h 0.198

  Occupancy RISES with N and the spread is flat across a 16x range. On the full
  frame the outer ring holds 42/43/44 of 62 cells at N=200/400/800 — flat — and
  the ~30% of outer cells that never fill at ANY N are the union's **uncovered
  rim**, not a selection effect. So the corner starvation is a COVERAGE fact and
  does not vary with the star count.
  **AND THIS DOES NOT REFUTE THE DOCSTRING, WHICH IS ABOUT A DIFFERENT QUANTITY —
  read this bound before citing the entry.** `solve_field.py` says *"raise this
  when the SOLUTION'S DISTORTION TERMS are the product being consumed rather than
  just its position"*: that is a claim about **SIP fit quality**. Everything above
  is **logodds**, which is MATCH CONFIDENCE. The first was not measured here.
  `run_undistort_groups.sh:340` uses `--max-stars=1500` on exactly that reasoning
  and is the standing counter-case: **more stars IS right somewhere in this tree,
  just not for this quantity on this canvas.** An entry that blurred the two would
  retire a correct practice.
  **WHAT WAS DONE INSTEAD:** `finish_render.sh` had hardcoded 400 with no way for
  a caller to reach it — the actual defect, which was never *"the pipeline needs a
  smarter value"* but *"the pipeline forbids any value"*. It is now
  `--max-stars=`, default UNCHANGED at 400 (preserved, not endorsed). The default
  was NOT moved to 300 on the strength of one stack: that is the knob-thrash the
  contract forbids.
  **THE RESIDUAL CASE IS COVERED BY A WARNING, NOT BY A GAP.** A canvas still
  below `LOGODDS_FLOOR` after the coverage rung gets `solve_field`'s FLOOR-CLASS
  warning — which is how the original logodds 63 was caught. That is the right
  status quo; no rung was left unbuilt over an unhandled hole.

- **A `-SIP` CTYPE IS NOT EVIDENCE OF SIP, AND ASTROPY DOES NOT WARN.** MEASURED on
  the shipped four-night corpus and reproduced on a probe build:

      corpus `_wcs.fit`    CTYPE1 = 'RA---TAN-SIP'   SIP cards 0    A_ORDER absent
      corpus `_spcc.fit`   CTYPE1 = 'RA---TAN'       SIP cards 0    A_ORDER absent
      a member             CTYPE1 = 'RA---TAN-SIP'   SIP cards 44   A_ORDER = 3

  `solve_field.py`'s injected WCS carries the `-SIP` projection label with **no SIP
  coefficient cards at all**. `WCS(h, naxis=2)` builds it silently and returns
  `wcs.sip is None` — no exception, no warning. **The header states a claim the file
  does not back, and the standard reader resolves it quietly to a plain TAN.**
  THREE THINGS ARE ESTABLISHED AND NOTHING ELSE IS:
  (a) the label is untrue on `_wcs.fit`, and nothing in the tool chain says so;
  (b) **`compose_preflight.py` is NOT foolable by it** — checked, because it is the
  guard that could be: it tests `A_ORDER` FIRST and only then CTYPE, and its
  `--selftest` carries a `linear` case (the SIP-labelled header minus `A_ORDER`)
  asserting `NO_SIP`. A TAN-SIP-labelled linear header is correctly REJECTED;
  (c) **siril's own `load`/`save` relabels it to `RA---TAN`**, which is the honest
  label — so `_spcc` disagreeing with `_wcs` on CTYPE is siril being correct, not an
  SPCC defect. (The same round-trip PRESERVES every repo provenance key tested:
  REGREF, REGREFSR, SOLVCENT, SOLVMAXS, REGMODEL, REGUNDIS, DISTA, CALSETS,
  PIPEREV, STACKCNT.)
  **WHETHER astrometry.net COMPUTES SIP IT DOES NOT SURFACE IS OPEN, AND IS
  DELIBERATELY LEFT WITH NO VERDICT.** `wcs_fields` arrives from the engine's C
  extension, so neither reader has looked where the answer is; recording "the
  solver cannot emit SIP" from that would be the promote-a-limit error this
  registry already carries twice (`tilt`/`inspector` listed-but-refusing, and
  `seqapplyreg`'s help closing the astrometric route).
  **THIS IS THE THIRD WAY THIS CORPUS'S WCS MISLEADS A READER, and all three are
  silent.** (1) `WCS(h)` on a member RAISES on 3-axis+SIP, so a probe without
  `naxis=2` reports every member unsolved — measured, 0 of 77, when all 77 carry
  `RA---TAN-SIP`. (2) `CRVAL` is the TANGENT POINT, not the pointing: median
  **1.877 deg** and max **5.814 deg** from the centre-pixel value across those 77,
  enough to select a different member or fake a mount contradiction
  (BACKLOG:`pointing-record-names-the-wrong-frame`). (3) this entry. A fourth is
  recorded elsewhere: SPCC drops `WCSAXES/LATPOLE/CD1_1..CD2_2` while the WCS still
  resolves, so a literal key-by-key comparison of `_wcs` against `_spcc` reports a
  difference that is a representation change. **Evaluate the WCS; never read its
  cards as the answer.**

- **THE `_wcs` HEADERS CARRY BOTH MATRIX FORMS, AND ASTROPY SILENTLY PREFERS
  THE WRONG ONE FOR THE SOLVE — the fifth silent way this corpus's WCS
  misleads a reader.** `solve_field.py --inject` writes the solve's CD matrix
  into a copy of the stack whose header KEEPS siril's PC1_1..PC2_2 + CDELT1/2
  (the stack's own canvas WCS). FITS-WCS declares the forms mutually
  exclusive; on a header carrying both, `astropy.wcs.WCS` resolves toward
  PC+CDELT with no warning. MEASURED on the corpus `_wcs`: as-is centre dec
  +41.003 (the PC solution) against CD-only +41.257 — 0.25 deg = 913 arcsec —
  and across all 34 solved products the as-is evaluation sits at median 101 /
  worst 913 arcsec from the headers' own OBJCTRA/OBJCTDEC, where CD-only
  reads median 1.7 / worst 36.5. **A consumer that evaluates a `_wcs` product
  with astropy is reading the STACK's canvas WCS, not the solve, unless it
  strips PC*/CDELT*/CROTA* first** (`spcc_cone.py` now does — its contract is
  the solve). This is what `verify_site.py`'s own docstring recorded without
  a mechanism: 7 of 9 products agreeing with OBJCTRA to 0.031 deg *"and
  0.13-0.18 deg on the other two"* — the two are this skew, immaterial at
  that instrument's DEGREE-level bound. **CLOSED, MEASURED ON SIRIL'S OWN
  SPCC (owner-directed probe): siril prefers the CD** — dual-matrix and
  CD-only runs identical at every reported figure (48.31 deg cone, 1946
  stars, both colour regressions to six decimals, K 1.000/0.669/0.899) with
  OUTPUT PIXELS bit-identical, while PC-only degrades to a wrong solution
  (1462 stars, near-flat regressions). So the strip is colour-neutral on both
  halves: `inject()` now deletes PC*/CDELT*/CROTA* when writing the CD, and
  the 34 on-disk `_wcs` products are backfilled the same way (204 cards
  removed, every data block sha-unchanged; `spcc_cone.py` keeps an in-memory
  strip for archived pre-backfill files). `_spcc` products were single-form
  all along — siril's re-save converts the CD it used into PC+CDELT. Full
  numbers: `datasets/corpus/wcs_dual_matrix_probe.json`.

- **Siril's internal plate solver DOES handle this class on STACKED members.**
  The standing belief ("cannot match ultra-wide trailed-star fields") was
  measured on single TRAILED frames and had silently widened past its evidence.
  MEASURED on aug06 member sub-stacks: `seqplatesolve -order=3` solved 2/2 with
  388 and 371 matched stars, residual sigx/sigy ~0.9 px, centres agreeing with
  astrometry.net to 0.001°. Stacked members have round stars; single 2.5 s
  ultra-wide frames do not. Keep `solve_field.py` for frames; Siril is usable
  for members.

