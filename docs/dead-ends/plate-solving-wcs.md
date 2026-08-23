# Plate solving and WCS consumption

Phase-2 file of the dead-ends registry split (`README.md` here holds the index
and dispositions; pre-compression forms live in git and in the live
`docs/dead-ends.md` until the merge). Entries are maintained IN PLACE.
Cross-references to sibling files are written as (`<file>.md`) pointers.

<!-- phase-2: maintained in place; not regenerated from the manifest -->
- **Siril's internal solver fails ultra-wide TRAILED fields — the blocker is
  its star MATCHER, not detection or catalogue depth (both tested and
  ELIMINATED).** Measured (36.45° field, correct centre from a blind solve,
  local Gaia, `-nocrop`): relaxed detection
  (`setfindstar -relax=on -roundness=0.05 -sigma=0.5`) raised candidates
  3316→8694 and still failed; `-limitmag=+4` raised the fetch to 138,498 Gaia
  stars and still failed — **do NOT re-attempt those two knobs.**
  `platesolve -localasnet` does not rescue it: it still feeds astrometry.net
  Siril's `findstar` PSF detection, which IS the failure mode. Side fact:
  Siril's AUTO limit mag for a 36° field is only 7.81 while detection goes
  far deeper — a population mismatch, not the blocker.
  **SCOPE — SINGLE TRAILED FRAMES ONLY, AND IT ONCE WIDENED PAST THAT
  SILENTLY.** Every measurement above is on single 2.5 s roundness-0.615
  exposures; on STACKED MEMBERS Siril's own solver DOES handle this class
  (entry below) — read the two together or this reads as a capability claim
  about the tool rather than about the DATA, which is how the belief widened
  before. The mildly-trailed boundary (roundness ~0.80) is
  BACKLOG:`native-solve-and-sip`'s one open probe.
- **The fix: feed astrometry.net a SHAPE-BLIND xylist (its INTENDED
  override — solve-field on an xylist runs NO pixel extraction, matcher
  geometry-only, Lang 2010). Blind-solve first, label after.** Best source is
  SExtractor's core `sep`: returns trailed sources (median elongation ~1.3),
  blind-solves at HIGHER odds than in-house peak centroids (logodds 299 vs
  289), identical SPCC K — `solve_field.py` defaults to it
  (`extractor_ab.json`). Robustness ranking: (1) asnet + **sep** xylist — the
  sole extractor (the in-house peak-xylist fallback is RETIRED: sep passed
  every x86 solve at equal-or-higher odds, identical SPCC K);
  (2) `image2xy` xylist (shape-blind, untested — its trail knobs aren't
  exposed by solve-field and `-a` can fragment one trail into spurious
  detections); (3) `-localasnet` and ASTAP — both PSF-fit/roundness-gated
  (ASTAP docs: *"star streaks … will be ignored"*). Caveats:
  `--no-remove-lines --uniformize 0` (or list filters) still thin a supplied
  xylist; and two valid fits' centres can differ by hundreds of arcsec (the
  SIP wobble — `registration-distortion.md`), which never reaches SPCC (it
  re-matches stars from the seed).
- **A BIG UNION CANVAS DEFEATS THE SOLVE, AND THE ROUTE THAT WORKS IS TO
  SOLVE A CENTRAL CROP LIKE A MEMBER AND SHIFT `CRPIX` BACK BY THE CROP
  OFFSET — header-only, pixels untouched.** MEASURED on the 52-member corpus
  union (46 Mpx, 52 member footprints): the hinted attempt failed on
  seam-contaminated detection and the blind fallback SHIPPED a false
  solution — RA 6.0 Dec −65.1 at 12.96″/px, **logodds 22 against a healthy
  family of 100–570** — which siril SPCC then consumed to completion,
  producing plausible-looking K factors instead of failing. The recovery:
  crop the central region to scratch, solve it as if it were a member
  (logodds 130), shift `CRPIX` by the exact crop offset — validated by
  per-star RA/Dec verification at positions far outside the solved crop, and
  SPCC on the corrected WCS returned K_G 0.669, in family. **Two traps
  measured on the way:** `--central` is a fraction of the FRAME (`=1.0`
  restricts nothing — semantics pinned in `solve_field.py`'s docstring), and
  `--max-stars=1500` explodes the quad search on a canvas this size (64 min
  of CPU, NO result — the entry below). **The blind-fallback half is now
  gated:** `solve_field.py` refuses a solution contradicting its own hints
  at exit 9, and this union is the gate's recorded falsification case.
- **WHAT MAKES A `framing=max` UNION STARVE THE SOLVE: CANVAS SIZE AND SEAM
  FRACTION ARE BOTH DIRECTIONALLY REFUTED. The registration REFERENCE is the
  only candidate left standing — a SURVIVING HYPOTHESIS, not a cause.** Two
  accounts were carried while a coverage-derived `--central` rescue was
  built; one knob killed both. The four-night corpus composed twice from the
  SAME 77 members, byte-identical siril HISTORY, only the reference
  differing:

      reference member 1  (0.746 deg from the median pointing)
          canvas 48.25 Mpx, 818/1040 boxes covered  -> NO SOLUTION
      reference member 36 (0.162 deg from the median pointing)
          canvas 48.55 Mpx, 803/1040 boxes covered  -> logodds 507, FIRST attempt

  **SIZE predicted larger-is-worse and the LARGER canvas solves; SEAM
  FRACTION predicted less-coverage-is-worse and the canvas with MORE
  uncovered boxes solves.** Both fail on DIRECTION, spanning the whole range
  from no solution to the corpus's highest logodds. What survives is
  whatever the reference carries — a more central anchor gives a smaller
  maximum off-axis angle, a TAN-breakdown reading — **but do not promote
  that to the mechanism**: n=1, and moving `--ref` moves canvas geometry,
  tangent point and orientation TOGETHER; centrality is not isolated, only
  size and seam fraction are refuted. **The coverage rung is NOT devalued**
  — it responds to a solve that ACTUALLY starved, never to a predicted
  cause, and measurably rescued the member-1 canvas (NO SOLUTION → logodds
  112) — but the product that motivated it no longer needs it: the
  member-36 canvas solves at 507 with the rung never firing. A general
  safety net; the reference derivation is what fixed this product.
- **`--max-stars` DOES NOT HAVE A DERIVABLE OPTIMUM, AND TWO POINTS ON ITS
  CURVE ARE NOT A TREND.** A derivation was scoped and then REFUSED on
  measurement. MEASURED at the coverage-derived `--central=0.694`, only this
  knob moving, and **deterministic** (three repeats at N=400 identical to
  every digit):

      100 -> logodds  84   (floor-class)
      200 -> logodds 134
      300 -> logodds 148   <- best
      400 -> logodds 112
      800 -> logodds 116

  **NON-MONOTONE and reproducible**, so the scatter is real. The pair that
  motivated the derivation (400→63, 200→106 at `--central=0.5`) reads as
  "fewer is better" and does not survive five points; a rule fitted to this
  would encode which quads happen to match on one stack. **The
  spatial-clustering account is not visible in the detections:** sep's own
  occupancy RISES with N (85/260 cells at N=100 → 258/260 at N=1600) with
  flat spread, and the ~30% of outer cells that never fill at ANY N are the
  union's uncovered rim — a COVERAGE fact, not a selection effect.
  **AND THIS DOES NOT REFUTE THE DOCSTRING, WHICH IS ABOUT A DIFFERENT
  QUANTITY:** everything above is **logodds** (match confidence);
  `solve_field.py`'s "raise this when the solution's DISTORTION TERMS are
  the product being consumed" is about **SIP fit quality**, not measured
  here — and `run_undistort_groups.sh` uses `--max-stars=1500` on exactly
  that reasoning, the standing counter-case: more stars IS right somewhere
  in this tree, just not for this quantity on this canvas. **What was done:
  `finish_render.sh --max-stars=`** (the hardcoded 400 was the actual
  defect — "the pipeline forbids any value", never "needs a smarter one";
  the default is preserved, not endorsed — the script's own comment carries
  it). The residual case is covered by `solve_field`'s FLOOR-CLASS warning —
  which is how the original logodds 63 was caught.
- **A `-SIP` CTYPE IS NOT EVIDENCE OF SIP, AND ASTROPY DOES NOT WARN.**
  MEASURED on the shipped corpus and reproduced on a probe build:

      corpus `_wcs.fit`    CTYPE1 = 'RA---TAN-SIP'   SIP cards 0    A_ORDER absent
      corpus `_spcc.fit`   CTYPE1 = 'RA---TAN'       SIP cards 0    A_ORDER absent
      a member             CTYPE1 = 'RA---TAN-SIP'   SIP cards 44   A_ORDER = 3

  `solve_field.py`'s injected WCS carries the `-SIP` label with no SIP
  coefficient cards; `WCS(h, naxis=2)` builds it silently and returns
  `wcs.sip is None` — the header states a claim the file does not back, and
  the standard reader resolves it quietly to plain TAN. THREE things are
  established and nothing else: (a) the label is untrue on `_wcs.fit` and
  nothing in the tool chain says so; (b) **`compose_preflight.py` is NOT
  foolable by it** — it tests `A_ORDER` first, and its `--selftest` carries
  a linear case asserting `NO_SIP`; (c) siril's own `load`/`save` relabels
  to `RA---TAN`, the honest label (and the round-trip PRESERVES every repo
  provenance key tested). **Whether astrometry.net computes SIP it does not
  surface is OPEN, deliberately left with no verdict** — recording "the
  solver cannot emit SIP" from where nobody has looked would be the
  promote-a-limit error this registry already carries twice.
  **This is one of the silent ways this corpus's WCS misleads a reader —
  the full set:** (1) `WCS(h)` on a member RAISES on 3-axis+SIP, so a probe
  without `naxis=2` reports every member unsolved (measured: 0 of 77 when
  all 77 carry SIP); (2) `CRVAL` is the TANGENT POINT, not the pointing —
  median 1.877° and max 5.814° from the centre-pixel value across 77
  members, enough to select a wrong member or fake a mount contradiction
  (BACKLOG:`pointing-record-names-the-wrong-frame`); (3) this entry;
  (4) SPCC drops `WCSAXES/LATPOLE/CD*` while the WCS still resolves, so a
  literal key-by-key `_wcs`-vs-`_spcc` comparison reports a representation
  change as a difference; (5) the dual-matrix preference, next entry.
  **Evaluate the WCS; never read its cards as the answer.**
- **THE `_wcs` HEADERS CARRIED BOTH MATRIX FORMS, AND ASTROPY SILENTLY
  PREFERS THE WRONG ONE FOR THE SOLVE.** `solve_field.py --inject` wrote the
  solve's CD matrix into a copy that KEPT siril's PC1_1..PC2_2 + CDELT1/2
  (the stack's own canvas WCS); FITS-WCS declares the forms mutually
  exclusive, and on a header carrying both, `astropy.wcs.WCS` resolves
  toward PC+CDELT with no warning — measured skew up to **913 arcsec** (the
  as-is evaluation read the STACK's canvas WCS, not the solve; across 34
  solved products, median 101 arcsec vs CD-only's 1.7). **CLOSED, measured
  on siril's own SPCC (owner-directed probe): siril prefers the CD** —
  dual-matrix and CD-only runs identical to six decimals with output pixels
  bit-identical, while PC-only degrades to a wrong solution. So the strip is
  colour-neutral on both halves: **`inject()` now deletes PC*/CDELT*/CROTA*
  when writing the CD** (the mechanism lives in the code comment beside it),
  the 34 on-disk `_wcs` products are backfilled the same way (204 cards
  removed, every data block sha-unchanged), and `spcc_cone.py` keeps an
  in-memory strip for archived pre-backfill files. `_spcc` products were
  single-form all along. Full numbers:
  `datasets/corpus/wcs_dual_matrix_probe.json`.
- **Siril's internal plate solver DOES handle this class on STACKED
  members.** The standing belief ("cannot match ultra-wide trailed-star
  fields") was measured on single TRAILED frames and had silently widened
  past its evidence. MEASURED on aug06 member sub-stacks:
  `seqplatesolve -order=3` solved 2/2 with 388 and 371 matched stars,
  residual sigx/sigy ~0.9 px, centres agreeing with astrometry.net to
  0.001°. Stacked members have round stars; single 2.5 s ultra-wide frames
  do not. Keep `solve_field.py` for frames; Siril is usable for members.
