# Combine-corner audit — independent report

Executed per `COMBINE_CORNERS_AUDIT_PROMPT.md`, extended at the user's order
to answer **"how come past combination stacks never had this issue"** by
auditing the code history and measuring the surviving past products. **No
fixes were made; no product was modified; nothing below proposes processing
the corner-defective composites** — every candidate fix is upstream of the
compose, executed as a rebuild if the user adopts it. Measurements live in
`datasets/aug06/set-03/qa_work/audit_combine_corners_measurements.json`
(same record home as the investigation's records — the
`BACKLOG:cross-set-record-home` degradation, still open). Instrument:
astropy box medians (sanctioned diagnostic), **cross-validated against the
session's own Siril `stat` record to ≤0.1 across 15 values** before anything
was trusted (the registry's y-flip trap checked, not assumed); reads at load
average 0.89.

Labels: **MEASURED** (instrument + numbers), **ARITHMETIC** (exact
consequence of measured inputs), **DOC** (official documentation / published
practice, cited), **HYPOTHESIS** (consistent with evidence, no
discriminating test run).

---

## 1. Verdict

**The corner defect is real, linear, combine-introduced — and it is NOT
intrinsic to cross-set composing on this chain.** The matched control proves
it: the july31 four-set combine (built two days earlier by the **byte-
identical compose algorithm** on the same post-revert chain state, same
sky-flat route, same night-class members, under a 93.8% moon) measures
**+0.0–0.2%** combine-specific corner excess at all four corners — clean —
where the aug06 twins carry **+0.8–1.3%** (MEASURED, same-sky cross-arm
probes against per-set controls, §2.3/§2.6).

What separates the failed twins from every prior clean combine is a
**conjunction of two chain-level facts, both of which changed recently and
neither of which is a property of the data**:

1. **The chain currently has no background-matching step anywhere — and it
   briefly had one, in the correct domain, which was removed as collateral
   damage.** `--desky` (shipped f170540) added per-frame `seqsubsky … 1` **on
   each calibrated light** — exactly the member-gradient matching Siril's
   own doctrine prescribes — hard-coupled by one flag to the flat-side
   desky, which was a measured 31× regression (a domain error: `seqsubsky`
   on raw, un-flat-fielded flat sources). The revert (895f268) removed
   **both halves**. The lights-side half was never re-examined on its own;
   `BACKLOG:render-ladder` L1 records the resulting gap. (MEASURED in git:
   the added line ran on `pp_c` — calibrated lights — while the killed
   mechanism was specific to un-flat-fielded frames.)
2. **The aug06 twins are the first combines ever shipped on the
   `-framing=max` + full-coverage-crop route** (ratified bcecf0b for yield,
   after `-framing=min`'s measured 36%-of-true-area case). That route moves
   the product corners into a zone min-framing never ships: MEASURED, three
   of four cov13 crop corners lie **outside** at least one per-set canvas
   (−13 to −129 px), i.e. in the outer drift band covered only by the
   member sub-stacks' own edge regions — where 8–12 member footprint edges
   bunch within ~110 px (§2.2, §2.7). Every july31 min-framing corner sits
   **inside** all four per-set canvases by 37–727 px.

On top of both, the pinned judge stretch renders the twins at **2.1–2.9×**
the amplification of the accepted per-set surfaces (registered √(sky·N)
law; inputs re-verified) — which converts a ~1% linear term into a failed
corner.

The members' residual gradients — the raw material of the term — are the
repo's standing open defects (`sky × V` tilt 3.11% at 241σ; the ±1.7%-class
within-burst flat corner term; per-set ramps ±0.36% alternating sign), not
something new in the aug06 data. Every mainstream pipeline inserts the
member-matching step this chain lacks (§4); the repo's own july23-era
investigation said the same thing three weeks earlier, verbatim: the
industry-standard chain "runs a background/gradient-removal stage that our
chain DOES NOT HAVE" (`docs/july23-dew-and-corner-chroma.md`, at 8d0920c).

## 2. What was measured

### 2.1 The crops are what they claim to be

The Siril-verified map crops survive
(`sessions/aug06/work/covcrop/mapcrop_*.fit`). Re-read directly: **min = max
= 1.0 across both full crops** — full coverage everywhere; the session's
y-flip guard ran and its verification stands (MEASURED). One contract
mismatch found: the maps on disk are **k/n normalized to 1.0 at full
coverage** (13 discrete 1/13 steps), while `coverage_probe.sh`'s docstring
still promises "value/1000 = members" and warns about a sum ceiling this
output shape makes moot. The session verified the real contract empirically
("linear k/n member steps verified", 295aa26) and left the docstring stale.

### 2.2 Boundary geometry — where the member edges are

MEASURED from the coverage maps, outward along each crop-corner diagonal
(distance at which coverage first falls to ≤m members):

| corner (Siril-coord labels) | edge bunching just outside | linear behavior just inside |
|---|---|---|
| cov13 c00 — the profiled corner | 13→10 by 20 px, →8 by 40 px, →5 by 85 px (**8–9 member edges within ~100 px**) | **+2.5–2.8% plateau, 0–300 px** |
| cov13 c11 | →11 by 30 px, →9 by 150 px | −1 to −1.7% dip, ~500 px |
| cov13 c10 / c01 | one edge at the corner, next 200–225 px out | ≤±1% |
| cov28 c00 — the patch corner | 28→16 by 110 px (**12 member edges within ~110 px**) | −1.5% at the corner, +5.6% peak at 200–300 px (100 px boxes) |
| cov28 c11 | →21 by 200 px | ±2–4% swings (structured region) |
| cov28 c10 / c01 | one edge at the corner, next 130–205 px out | ≤±1% |

Consistent across all eight corners: **the anomalous corners are exactly the
corners where many member edges bunch** (MEASURED).

### 2.3 Same-sky cross-arm — how much is real sky, how much the combine

Probe boxes defined on the combine, mapped through each product's solved
TAN-SIP WCS into every arm containing that sky; excess vs the mean of three
same-sky flanks, within each arm (flank systematic ±0.3–0.5%, largely
common-mode):

**cov13 c00 corner** (0/100/200/300/500 px along the diagonal):

| arm | excess % |
|---|---|
| cov13 | **+3.0, +2.9, +2.1, +0.1, +1.6** |
| set-01 | (sky outside canvas), +1.6, +0.9, −0.9, +1.1 |
| set-02 | (outside), +2.8, +1.8, −0.5, +1.7 |
| set-03 | +1.8, +1.9, +1.0, −1.1, +1.0 |

The corner sky is genuinely +1–2% bright — and cov13 sits **+0.8–1.2%
above the per-set mean at identical sky over the first ~300 px**, decaying
to ~+0.3% by 500 px. That increment is the combine-introduced term.

**cov28 c00 patch** (0/150/250/350/500/800 px):

| arm | excess % |
|---|---|
| cov28 | +0.2, **+2.7, +2.4, +2.2**, +0.6, +1.2 |
| cov13 | −0.3, +2.3, +2.1, +1.9, +0.5, +1.3 |
| set-01/02/03 | −0.8..−1.5 at the corner; **+1.4–2.1% through the patch**; +1.2–1.4% at 800 px |

The 150–350 px "patch" is **predominantly real sky** (present in every
single-set control). The six-member-specific increment over cov13 is
**+0.3–0.4%**; at the corner itself the combine again carries ~+1% vs the
per-set truth.

### 2.4 Display amplification

Registered MEASURED mechanism (`docs/dead-ends.md`): autostretch
amplification of a fractional background residual scales ~√(sky·N), 17×
measured on one set, the √-law verified at ratio 1.95 vs 2.0 predicted.
Inputs re-verified here (sky medians from validated reads; N from
`STACKCNT`): the twins were judged at **2.1–2.2× / 2.8–2.9×** a
set-03-class surface's amplification; the accepted per-set surfaces sit at
1.0–1.2× (ARITHMETIC). [DOC] Siril calls the autostretch rendering "only a
display trick" (siril.readthedocs.io/en/stable/processing/stretching.html).

### 2.5 Status of the three inherited hypotheses

| prior session's claim | audit status |
|---|---|
| **Boundary**: corner excess decays by ~420 px; member sensor-corners converge; flats' non-radial residuals add | Geometry **CONFIRMED MEASURED** (§2.2); combine-specific ~+1%/≤500 px term **CONFIRMED MEASURED** with per-set controls (§2.3). *Which* member-side residual dominates (burst-end flat term, `sky × V` tilt, model residual) remains **HYPOTHESIS** — magnitudes consistent; the §6 one-knob arm is the discriminating test |
| **Display amplification** ~√(sky·N): 2.1×/2.8× | **CONFIRMED** (registry law + re-derived inputs, §2.4) |
| **Residual patch** (cov28): ~half real / ~half july31-member (+1.97 vs +1.03, n=1) | **REVISED MEASURED**: predominantly real sky; six-member increment +0.3–0.4% (prior n=1 position not reconstructible — i450 products deleted, solve record has no full WCS) |

### 2.6 The matched control: the july31 four-set combine is CLEAN

`web/results/july31/stack_set-01+02+03+04_full*.fit` survives (1,760
frames, 17 sub-stacks, `-framing=min`, built d17e777 on the post-revert
chain — sub-stacks and sky flats all rebuilt post-revert, mtimes 08-06).
Same-sky cross-arm at **all four canvas corners** vs its four per-set
stacks (MEASURED):

| corner | combine excess (0/100/200/300/500 px) | per-set controls at identical sky |
|---|---|---|
| c00 | +0.5, +0.5, +0.0, −0.1, −0.5 | s01 +0.7…, s02 +0.7…, s03 +0.6…, s04 −0.2… |
| c10 | +0.3, +0.3, +0.1, +0.2, −0.1 | all four: same to ±0.1 |
| c01 | +0.2, +0.3, +0.1, −0.2, −0.1 | same to ±0.2 |
| c11 | −0.1, +0.0, +0.2, +0.1, +0.1 | same to ±0.1 |

**Combine-specific increment ≈ 0.0–0.2% everywhere** — the compose
algorithm, the plain mean, `-norm=addscale`, the sky-flat members and the
no-background chain state all produce a clean combine here. Regional corner
spread re-read at 0.79% (recorded 0.59% at the exact original geometry;
both sub-1%). Its judge package asked the combine question explicitly and
its inspection recorded "no rim/edge artifact". Note the per-set controls
also show the member families differ by ~1% at the same sky (s04 vs
s01–03 at c00) — member-gradient dispersion exists on july31 too; it does
not reach the product because of §2.7.

### 2.7 Where each route puts its corners (the discriminating geometry)

Combine corner positions mapped through the WCS into every member set's
per-set canvas — minimum distance to that canvas's edge (**negative =
outside it**), MEASURED:

| product | c00 | c10 | c01 | c11 |
|---|---|---|---|---|
| aug06 cov13 (max + cov-crop) | s1 **−113**, s2 **−105**, s3 +184 | s1 **−15**, s2 +266, s3 +181 | s1 +300, s2 **−129**, s3 +261 | s1 **−13**, s2 +171, s3 +260 |
| july31 all4 (min) | +133…+727 (all four sets) | +148…+391 | +180…+497 | +37…+350 |

Three of four cov13 corners lie **outside at least one per-set canvas** —
in the outer drift band that only the member sub-stacks' edge zones cover
(full coverage by count, member-edge pixels by content). Every min-framing
corner sits inside every per-set canvas. **This is why the same chain
produced a clean four-set combine and defective twins**: min never ships
the member-edge band; max+cov-crop ships it right up to the boundary — and
without member background matching, that band carries the members'
systematic corner-zone residuals (the ~+1% term of §2.3). The revoked i450
inset is the same fact seen from the other side: receding 450 px from the
boundary removed the boundary term — by not shipping the band.

## 3. What changed vs past combines (the user's question)

Every multi-set combine this project has made, in chain order, with its
background-handling state and its corner outcome:

| combine | framing | member background matching in the chain | corner outcome |
|---|---|---|---|
| july14 cov25 (5 sets, 1,575 fr) | max + coverage frame | none (pre-desky) | **not a usable control**: 16-bit-era chain (measured to keep only ~55–70% of 32-bit faint contrast — residuals crushed), products and dataset records deleted, judgment surfaces of a different era |
| july23 3-set / 2-set combines | min | none (pre-desky) | **HAD a user-flagged corner defect** (corner chroma ~5–7% R/G). Investigated then: `subsky 1` on the composite = PARTIAL (removed the one-sided term, structurally cannot touch the rest); root cause routed UPSTREAM to per-channel calibration; the era's doc names the missing standard background stage (8d0920c) |
| july23 rebuild, the **approved** combine render | min | **YES — desky era**: per-frame `seqsubsky … 1` on calibrated lights (f170540) | approved (2026-07-30). The only combine approval on record sits on the only chain state that matched member gradients — and on the regressed desky flats, so it is not a trustworthy reference either way (`BACKLOG:render-ladder`) |
| july31 4-set (17 subs, 1,760 fr) | **min** | none (post-revert) | **CLEAN — MEASURED this audit** (§2.6): ≤0.2% combine-specific at all four corners; inspected and packaged with "no rim/edge artifact" |
| aug06 cov13 / cov28 twins | **max + full-coverage crop (first execution of the ratified route)** | none (post-revert) | **FAILED**: +0.8–1.3% combine-specific corner term (§2.3), judged at 2.1–2.9× amplification |

So "past combines never had this issue" decomposes, on the record, into:
(a) the issue **did** occur before — july23 — and was already diagnosed to
the missing background stage and upstream calibration; (b) the one approved
combine was built during the only window when the chain matched member
gradients; (c) the post-revert chain still produces clean combines **on
min framing** (july31, measured); and (d) the twins are the first products
of the max+cov-crop route, whose corners reach the member-edge band that
min framing structurally avoids. The compose code itself did not change
between the clean four-set and the failed twins (diff: serialized invoker +
`setext` pin only — cosmetic to the algorithm), and the per-set optical-
model change is ruled out as the driver (a ~2 px geometric difference
cannot move a smooth background ~1%; the per-set aug06 products' own
corners are clean at their margins).

**Root cause, stated once:** members carry systematic background residuals
in their sensor-edge zones (standing open defects); nothing in the current
chain matches or removes them (the correctly-domained per-frame step was
removed as collateral of the desky revert; the old era's render-side
background stage was never rebuilt — L1); the new max+cov-crop route is the
first to ship the zone where those residuals converge instead of averaging
out; and the depth-scaled judge stretch renders the result 2–3× harsher
than any surface the user had previously accepted.

## 4. Provenance of every deciding number (audit question 2)

| deciding quantity | value used | provenance class | audit finding |
|---|---|---|---|
| Combine membership + "largest fully-covered crop" | full sets; crop at cov == all members | **USER-RATIFIED** (bcecf0b) + `TOOLS.md` doctrine | Clean as a decision; §2.7 is the consequence nothing modeled: full coverage counts members, not their interior-ness — the route change is half the root cause |
| Coverage maps | k/n steps | **OFFICIAL TOOL** via tracked `coverage_probe.sh` | Sound; docstring contract stale (§2.1) |
| Crop rectangles | `crop 1699 715 4159 3272` / `2530 1297 3339 3068` | **IN-SESSION UNREVIEWED numpy** (largest-rectangle; generator untracked) | Output verified through the registered Siril guard (re-verified §2.1); derivation unreviewed |
| 450 px inset | in-session, from in-session marches | **IN-SESSION UNREVIEWED**; REVOKED | Correctly dead (registry: never hide a rim defect with a crop) |
| Corner spreads 0.80% / 1.88% | Siril `stat` | **OFFICIAL TOOL** via tracked `regional_stat.py` | Numbers right; geometry (box 400 / margin 200) under-reaches this 0–400 px defect class |
| Grid / march numbers | Siril `stat` via ad-hoc `.ssf` (preserved) | **TOOL numbers, IN-SESSION harness** | Reproduce to ≤0.1; the summaries drawn from them were in-session arithmetic, replaced by §2.3's controlled comparisons |
| `--weight=nbstack` | compose weighting | **OFFICIAL TOOL option** (documented for stacks-of-stacks) | Recorded justification ("two nights' per-frame sky differs only ~6%") traces to **no record** and re-measures at **~60%** (night medians ~124 vs ~197, same 2.5 s subs — MEASURED). The tracked docstring already derives `noise` as the multi-night weight. Affects SNR weighting, not the corner mechanism |
| Pinned compose reference (set-03 `sub_02`) | `--ref` | **RECORDED DECISION**, measured mechanism in the docstring | Clean |
| Compose normalization | `-norm=addscale -output_norm`, plain mean | **OFFICIAL TOOL**; mean-not-rejection is registry-MEASURED | Correct and structurally global — Siril normalization "matches the mean background" per image [DOC]; no spatial matching exists in `stack` outside the mosaic-stitching provisions |
| Judge stretch policy | per-product `autostretch -linked` after SPCC | **PINNED POLICY** + official tool; amplification law registry-MEASURED | Written for same-depth ladders; across a 3–6× depth spread it guarantees combines are judged 2–3× harsher (§2.4). Policy gap, not tool error |

## 5. What the mainstream does (audit question 3)

Researched from primary sources; every claim carries its URL in the agents'
full reports (summarized).

- **Siril** [DOC]: first choice for one field over multiple nights is one
  integration of all calibrated frames (siril.org/faq). Where per-panel
  stacks are combined, the official mosaics tutorial adds per-frame
  degree-1 background correction inside each member, `-overlap_norm` gain
  compensation and `-feather=` blending (siril.org/tutorials/mosaics/;
  1.4.0 release notes). Background docs recommend per-frame degree-1 when
  the gradient varies across the sequence
  (siril.readthedocs.io/en/stable/processing/background.html) — **this is
  the L1 per-frame arm, and Siril's own doctrine picks it for
  session-varying gradients**. Crop-before-statistics is standard
  (siril.org/tutorials/tuto-scripts/).
- **PixInsight** [DOC]: integration normalization is global per-image
  scalars by design; differing gradients are handled by spatially-varying
  normalization — LocalNormalization (auto-run by WBPP since 1.8.9),
  Adaptive Normalization, or NSG ("normalizes the scale and gradient to
  that of the reference image"). The NSG author's controlled demonstration
  of the skip-it failure is the exact defect signature: with global-only
  normalization the unevenly-covered region integrates visibly
  darker/brighter "due to gradients in the individual images … The standard
  normalization is doing exactly what it was asked to do"
  (pixinsight.com/forum, thread 16507). Mosaics: per-panel DBE/ABE before a
  seam-aware merge; GradientMergeMosaic's doc requires shrinking
  partial-value borders or "you will continue to see seams".
- **APP** [DOC]: normalization always on; LNC exists precisely for
  "combining data with deviating gradients (multiple imaging sessions…)";
  MBB feathers member borders ("stack artefacts at the borders of regular
  integrations"); crop-uncovered-borders-then-remove-light-pollution is the
  stated standard order (astropixelprocessor.com FAQ/tutorials).
- **Professional coadds** [DOC]: per-input background subtraction before
  co-addition is universal — SWarp `SUBTRACT_BACK Y` default, with the
  manual warning that unsubtracted inputs "will often produce an ugly
  patchwork" and that composites larger than any input "must be
  background-subtracted prior to coaddition, to avoid generating
  discontinuites" (SWarp User's Guide §5.7); SDSS Stripe 82
  (arxiv.org/abs/1405.7382), Pan-STARRS (arxiv.org/abs/1612.05245),
  Rubin/LSST SkyCorrection (pipelines.lsst.io).
- **No surveyed source documents "register + mean, fix background later"**
  as a route; the un-normalized combine of offset members appears only as
  the documented-defective case.

## 6. Recommended path — all user decisions, all upstream, none touching the failed composites

The user's constraint is honored structurally: every option below changes
the CHAIN or a ROUTE DECISION and takes effect only through rebuilds from
raws or re-composes from sub-stacks. The failed composites are evidence,
not inputs. Re-running is cheap by standing principle.

1. **Restore the member background-matching step the chain lost — the
   root-cause fix.** The desky revert removed two things one flag had
   coupled: the flat-side desky (correctly dead — a domain error, registry)
   and per-frame `seqsubsky … 1` **on calibrated lights** — the correct
   domain, Siril's own recommendation for session-varying gradients, the
   step whose absence every mainstream comparison in §5 names, and the step
   present in the only combine window the user ever approved. This is
   `BACKLOG:render-ladder` L1, re-scoped with what this audit adds: the
   decision is no longer "is a background step needed" but "which arm" —
   per-frame on lights vs per-member on sub-stacks (the july23 probe
   MEASURED that a composite-level plane structurally cannot fix a
   corner-local term, so composite-only is not a candidate for THIS
   defect). Pre-registered test, one knob: rebuild one set's members with
   the lights-side step only, recompose max+cov-crop, re-run the §2.3
   same-sky corner probe — the ~+1% term vanishes or the attribution
   hypothesis dies. Uncoupling the flag so the flat-side desky can never
   return with it is part of the same decision.
2. **Decide the framing trade with the corner cost now on the table.** The
   max+cov-crop route was ratified for yield; §2.7 shows its corners ship
   the member-edge band that min framing structurally avoids — and the
   july31 control shows min is clean on this chain TODAY. Options: keep
   max+cov-crop and make member matching (item 1) its prerequisite; or
   accept min's yield cost where it suffices. A min-framed re-compose of
   the same aug06 sub-stacks is available without reprocessing a single
   frame if the user wants the comparison — that is a route decision on
   untouched inputs, not a fix of the defective products.
3. **What this audit recommends AGAINST, agreeing with the user's
   bandaid instinct:** compose-side feathering/`-overlap_norm` for this
   class — mainstream for low-overlap tile mosaics, but for co-pointed
   members with systematic corner-zone residuals it blends the step instead
   of matching the members; any recrop-inset of the i450 class (registered
   dead end); and any composite-level background model offered as the fix
   for the corner term (measured structurally incapable — july23 probe).
4. **Weighting**: switch multi-night composes to `--weight=noise` per the
   compose docstring's own derivation, or record a measured justification
   for nbstack (the ~6% claim is contradicted at ~60%). Same-night: nbstack
   stands.
5. **Judge policy for cross-depth sets** (aesthetics/policy — the user's
   alone): keep per-product autostretch with mandatory linear corner
   numbers beside any cross-depth judgment; or extend `finish_render.sh
   --mtf=` pinning to expectation-matched cross-depth sets; or keep the
   harsh diagnostic bar knowingly — in which case a per-set PASS at 1× is
   not evidence a combine will pass at 3×.
6. **Instrument hygiene** (assent-level): promote the ad-hoc grid/march and
   same-sky cross-arm probes into the tracked instrument or adopt the
   registry's ramp-slope candidate (acceptance-measure changes need
   ratification); fix `coverage_probe.sh`'s stale contract line; replace
   the in-session largest-rectangle numpy with a reviewed script or the
   existing framing UI (`web/crop.html` + `verify_framing.py`);
   `BACKLOG:cross-set-record-home` already covers the record filing.

## 7. Summary for the record

The failed twins and every clean past combine are explained by one measured
conjunction, not by a data anomaly: members carry systematic edge-zone
background residuals (standing open defects, unchanged); the chain's only
member-matching step — per-frame `subsky 1` on calibrated lights, the
correctly-domained half of `--desky` — was removed together with the
incorrectly-domained half it shared a flag with; the max+full-coverage-crop
route, executed for the first time on the twins, is the first to ship the
member-edge band where those residuals converge (min-framed combines,
including the measured-clean july31 four-set control on the identical chain
state, never ship it); and the depth-scaled judge stretch rendered the
resulting ~1% linear term at 2–3× the amplification of any previously
accepted surface. The corner class was seen once before (july23), was
diagnosed then to the same missing stage, and the only combine the user
ever approved was built in the one window when the stage existed. The fix
direction is upstream — restore the matching step and settle the framing
trade — decided by the user, executed as rebuilds; the defective
composites themselves are evidence and stay untouched.

---

## 8. Addendum — the restoration arm's measured verdict

The §6-item-1 experiment ran (`subsky_lights_restoration`, pre-registered):
members rebuilt with `--subsky-lights`, controls preserved, identical compose
(framing=max, nbstack, pinned reference), like-encoded judge pair finished.

**REFUTED as the corner fix; NULL on the rendered surface.** The stage
demonstrably fired (union sky 107.5 → 40.4 ADU, MAD unchanged 2.67 → 2.46),
but the combine-specific corner increment did not collapse — ADU: c00
1.35→0.55 at the corner yet 0.98→0.94 at 300 px, c11 0.99→1.37 — and the two
judge PNGs are corner-equivalent (DN corner-minus-flank +2823 vs +2941 at
c00, −1526 vs −1653 at c11): equal ADU structure at equal noise renders
equally, whatever the sky level, because the autostretch re-anchors.

**What the refutation buys — the mechanism narrows.** The corner term
survives per-frame ADDITIVE degree-1 matching, so it is predominantly NOT
additive-planar member sky drift. That leaves the MULTIPLICATIVE
member-corner class — the open `sky × V` object tilt and vignetting-residual
at member sensor corners — which no background subtraction can remove by
construction. Registry entry recorded.

**Scope correction (user-ratified, supersedes this addendum's first
wording): the fix search stays INSIDE the flatless route — synthetic flats
are the project's point, and "shoot real flats" is never a recommendation.**
The residual class is CONSTANT across every product this repo ever shipped
(all sky-flat calibrated, passing and failing alike), which is exactly why
it cannot explain a NEW defect: the onset is the ROUTE change (§3), not the
calibration. The levers, all in-scope, all user-gated:

1. **Geometry — which member zones the compose ships.** Min framing keeps
   corners in member interiors (measured clean; the user-confirmed passing
   july31 product is this class). For a max-canvas deliverable, the
   mainstream mechanism is a **per-member edge shrink at compose input**
   (PixInsight GradientMergeMosaic "Shrink Radius": partial-value member
   borders "cannot successfully merge … you will continue to see seams") —
   each sub-stack contributes only its interior; the union stays max-class,
   marginally smaller; input-zone exclusion like a frame cull, not a crop of
   the shipped result.
2. **Better synthetic-flat construction.** The measured member-to-member
   differencer WITHIN a set is the within-burst flat term (±1.7%-class at
   corners, 90–100× the build floor — registry flat-window entries);
   per-group sky flats are the untested in-route candidate that targets it.
   The across-set half (per-set `sky × V` tilts differing) is the standing
   `calibration-evidence` work.
3. Spatially-varying member matching (LN/NSG/LNC-class) is the mainstream
   tool for exactly this — and no free-headless tool in this toolkit
   provides it (Siril has none; per-member full BGE is class-blocked on
   MW-filled fields per the registry). A documented gap, not a build item.
4. `--subsky-lights` stays available, default OFF; its original render-stage
   question (L1 background level) is untouched by this kill and remains the
   open, user-gated ladder — with one new measured fact in its favor:
   degree-1 preserved local structure and noise in these regions.

---

## 9. Addendum 2 — the defect re-identified: corner star SMEAR, and the compose creates it

Eyes on 1:1 corner crops (extracted from the judge surfaces) show the failed
corners as **smeared stars** — coherent diagonal dashes, brushed fabric,
faint stars suppressed — where the passing july31 corner is round pinpoint
stars. Every instrument in this investigation up to here, both sessions',
measured background box statistics and was structurally blind to the actual
observable. Star instrument (Siril `findstar`, open gate, 800 px boxes):

| surface | corner FWHM px | center FWHM px | corner/center |
|---|---|---|---|
| aug06 union, max+covcrop (own models) | 4.95 | 3.32 | **+49%** — FAILED |
| aug06 union, min (own models) | 4.83 | 3.38 | **+43%** — same smear |
| aug06 union, max (single pinned model) | 5.29 | 3.30 | **+60%** — same smear |
| july31 union, min (single model) | 3.44 | 2.74 | +26% — PASSES |
| aug06 per-set products (own model each) | 3.87–4.18 | 3.17–3.30 | +22–29% — PASS |
| aug06/july31 sub-stacks (members) | 3.55 / 3.28 | 3.19 / 2.89 | +11/+13% |

**Eliminated as drivers, each by direct measurement**: framing (min smears
equally), model heterogeneity (single-model union smears equally), member
background matching (subsky arm renders corner-equivalent), re-aim geometry
(july31 spans BIGGER offsets, 6.2° vs 3.2°, and rotations, 16.3° vs 8.5°,
and passes), member corner content (sub-stacks enter at ~3.5 px), and
member-edge-zone shipping (the min union's corners sit inside the per-set
canvases and still smear). **The smear is created at the cross-set compose:
members enter ~3.5 px and exit 4.9–5.3 px at like zones — on aug06's
members only.**

**Leading hypothesis (labeled):** residual distortion in the aug06 members
under BOTH model eras — the pinned model is state-mismatched to aug06
(measured 2× field-term elevation in the optics ledger) and the own-model
fits sit above july31's family floor (+0.1–0.15 px, unattributed) — breaks
cross-pointing homography registration at large radii. july31's union
composes clean because its members' optical state matches the model that
warped them. This is the route's founding mechanism (unmodelled radial
distortion is the one residual a global registration cannot absorb),
resurfacing one level up. The earlier ~1% corner median excess re-reads, in
part, as smeared-star flux raised into the diffuse floor (HYPOTHESIS).

**Discriminating next test (user-gated, from preserved sub-stacks, no
reprocessing):** pairwise two-member composes — co-pointed s01+s03 (0.0°
offset, 8.5° rotation) vs s01+s02 (3.2°, 1.0°) vs s02+s03 (3.2°, 7.6°) —
corner `findstar` + `seqtilt` per pair separates offset-driven from
rotation-driven mismatch and ranks which member family carries the
residual. The min-framed and subsky unions built this session are
discriminator surfaces, not candidates — the min union fails the same
smear.
