# Combine-corner audit — independent report

Executed per `COMBINE_CORNERS_AUDIT_PROMPT.md`: an audit of the failed twin
combines and of the process that produced them. **No fixes were made; no
product was modified.** Every inherited mechanism claim was re-derived or
re-labelled; every deciding number was traced to its source. New measurements
live in `datasets/aug06/set-03/qa_work/audit_combine_corners_measurements.json`
(same record home as the investigation's own records — the
`BACKLOG:cross-set-record-home` degradation, still open). Instrument for the
new numbers: astropy box medians (sanctioned diagnostic), **cross-validated
against the session's own Siril `stat` record to ≤0.1 across 15 values**
before anything was trusted (the registry's y-flip trap checked, not
assumed); reads taken at load average 0.89.

Labels used throughout: **MEASURED** (instrument + numbers, this audit or a
registry entry with its own), **ARITHMETIC** (exact consequence of measured
inputs), **DOC** (official documentation / published practice, cited),
**HYPOTHESIS** (consistent with evidence, no discriminating test run).

---

## 1. Verdict: is this normal for our rig?

**YES for the route as built — the corners are the documented, expected
symptom of composing members whose background gradients were never matched,
rendered through a stretch whose gradient amplification grows with depth.
The defect is real, linear, and in the data — specifically in the MEMBERS'
uncorrected residual backgrounds, which the repo already carries as open
defects.** Nothing rig-specific, version-specific, or code-defective was
found in the compose itself: the crops are exactly full-coverage (re-verified
§2.1), the reference was pinned, the mean is the correct combiner for
sub-stacks (registry), and normalization did what it is documented to do.

The compose applies `-norm=addscale` — one offset and one scale **per
member** (global). [DOC] Siril: "Normalisation matches the mean background of
all input images" (siril.readthedocs.io/en/stable/preprocessing/stacking.html).
What no step in the route touches is each member's **spatial** residual — and
this project's members measurably carry one: per-set L–R ramps ±0.36% with
alternating sign (`docs/dead-ends.md`, four-corner-metric entry), a
±1.7%-class corner term from the within-burst flat drift (flat-window
entries), and the open `sky × V` object tilt (3.11% at 241σ,
`BACKLOG:calibration-evidence`). Where the full-coverage crop's corners sit,
8–12 member footprint edges converge within ~100 px (MEASURED, §2.2), so the
mean there is taken over the members' own worst-residual zones, which no
longer average out. The mainstream statement of exactly this failure mode is
the NSG author's demonstration [DOC/EXPERT]: with global-only normalization a
region not covered evenly by all frames integrates visibly darker/brighter
"due to gradients in the individual images … The standard normalization is
doing exactly what it was asked to do"
(pixinsight.com/forum/index.php?threads/normalizescalegradient-bookmark-website-now.16507/).
SWarp's manual makes per-input background subtraction the professional
default for the same reason: without it, co-addition of exposures with
differing backgrounds "will often produce an ugly patchwork", and inputs to a
composite larger than any single exposure "must be background-subtracted
prior to coaddition, to avoid generating discontinuites" [DOC]
(SWarp User's Guide §5.7; `SUBTRACT_BACK Y` is the shipped default,
github.com/astromatic/swarp `src/preflist.h`).

Size of the effect here (MEASURED, §2.3): a **combine-introduced ~+1%
(0.8–1.3%) linear excess confined to ~0–500 px of the anomalous full-coverage
corners**, superposed on **+1.5–2% real sky structure** that the per-set
stacks show at the identical sky. The judge surfaces then rendered that
through per-product linked autostretch at **2.1–2.9× the amplification of a
per-set surface** (registered √(sky·N) law + verified inputs; ARITHMETIC) —
which is how a ~1% linear term that is invisible on an accepted per-set
surface becomes a failed corner on the combine. Both halves are real: the
linear excess exists, and the encoding magnifies it by depth.

So the answer to "is this normal": corner residuals of roughly this size are
what **register + globally-normalized mean with no gradient matching** is
documented to produce from members like ours — and no mainstream pipeline
ships that combination. Every surveyed tool inserts the missing step
(§4). The user's revocation reasoning was correct on both counts: the i450
inset hid a symptom whose cause is in the data — and "the data" means the
members' backgrounds, which are fixable process-side, not a property of the
sky the project must live with.

---

## 2. What was measured (independent re-derivation)

### 2.1 The crops are what they claim to be

The Siril-verified map crops survive
(`sessions/aug06/work/covcrop/mapcrop_*.fit`). Re-read directly: **min = max
= 1.0 across both full crops** — full coverage everywhere; the session's
y-flip guard ran and its verification stands (MEASURED). One contract
mismatch found on the way: the maps on disk are **k/n normalized to 1.0 at
full coverage** (13 discrete 1/13 steps), while `coverage_probe.sh`'s
docstring still promises "value/1000 = members" and warns about a 65535 sum
ceiling that this output shape makes moot. The session verified the real
contract empirically ("linear k/n member steps verified", commit 295aa26) and
left the docstring stale — a consumer following the documented contract today
would divide by 1000 and read every threshold as passed-vacuously. Small,
but it is an in-house instrument whose written interface does not match its
output.

### 2.2 Boundary geometry — the "member sensor-corners converge" claim

MEASURED, from the coverage maps, outward along each crop-corner diagonal
(distance at which coverage first drops to ≤m members):

| corner (Siril-coord labels) | edge bunching just outside | linear behavior just inside |
|---|---|---|
| cov13 c00 — the profiled corner | 13→10 by 20 px, →8 by 40 px, →5 by 85 px (**8–9 member edges within ~100 px**) | **+2.5–2.8% plateau, 0–300 px** |
| cov13 c11 | →11 by 30 px, →9 by 150 px | −1 to −1.7% dip, ~500 px |
| cov13 c10 / c01 | one edge at the corner, next 200–225 px out | ≤±1% |
| cov28 c00 — the patch corner | 28→16 by 110 px (**12 member edges within ~110 px**) | −1.5% at the corner, +5.6% peak at 200–300 px (100 px boxes) |
| cov28 c11 | →21 by 200 px | ±2–4% swings (structured region) |
| cov28 c10 / c01 | one edge at the corner, next 130–205 px out | ≤±1% |

The correlation is consistent across all eight corners: **the anomalous
corners are exactly the corners where many member footprint edges bunch; the
quiet corners have one or two.** The geometric half of the prior session's
boundary claim is CONFIRMED (MEASURED). By construction of a
maximal inscribed rectangle this bunching is not an accident: the rectangle's
corners land where the intersection boundary pinches, and the boundary is
made of member edges.

### 2.3 Same-sky cross-arm — how much is real sky, how much the combine

The decisive test the prior session ran only once (n=1, on the now-deleted
i450 products): measure the identical sky in every arm that contains it,
through each product's solved WCS. Re-run on the surviving products with
three independent per-set controls (MEASURED; excess vs the mean of three
same-sky flanks, per arm; flank systematic ±0.3–0.5%, largely common-mode):

**cov13 c00 corner** (boxes at 0/100/200/300/500 px along the diagonal):

| arm | excess % |
|---|---|
| cov13 | **+3.0, +2.9, +2.1, +0.1, +1.6** |
| set-01 | (sky outside canvas), +1.6, +0.9, −0.9, +1.1 |
| set-02 | (outside), +2.8, +1.8, −0.5, +1.7 |
| set-03 | +1.8, +1.9, +1.0, −1.1, +1.0 |

The corner sky is genuinely +1–2% bright (it is in every per-set arm) — and
cov13 sits **+0.8–1.2% above the per-set mean at identical sky over the
first ~300 px**, decaying to ~+0.3% by 500 px. That increment is the
combine-introduced term. (Note the first row: the corner sky is not even
inside set-01/set-02's per-set canvases — their `-framing=min` composes
discarded it. Only the combine ever showed this sky, so no per-set judgment
could have caught it.)

**cov28 c00 patch** (boxes at 0/150/250/350/500/800 px):

| arm | excess % |
|---|---|
| cov28 | +0.2, **+2.7, +2.4, +2.2**, +0.6, +1.2 |
| cov13 | −0.3, +2.3, +2.1, +1.9, +0.5, +1.3 |
| set-01/02/03 | −0.8..−1.5 at the corner; **+1.4–2.1% through the patch**; +1.2–1.4% at 800 px |

The 150–350 px "patch" is **predominantly real sky** — present at +1.4–2.1%
in every single-set control. The six-member-specific increment over cov13 is
**+0.3–0.4%**, within ~2× the flank systematic. At the corner itself (box 0)
the combine again carries ~+1% vs the per-set truth (+0.2 rendered where
−0.8..−1.5 is real).

### 2.4 Display amplification

The law is a registered MEASURED mechanism, not this session's invention:
autostretch amplification of a fractional background residual scales
~√(sky·N), measured at 17× on one set with the √-law verified at a 2.0×
prediction reading 1.95 (`docs/dead-ends.md`, stretched-judge-surface entry).
This audit re-verified the inputs (sky medians from validated reads; N from
`STACKCNT` headers: 1454 / 2954 / 456–500) — the combines were judged at
**2.1–2.2× (cov13) and 2.8–2.9× (cov28)** the amplification of a
set-03-class surface, while the accepted per-set surfaces sit at 1.0–1.2×
(ARITHMETIC from the measured law). [DOC] Siril's own docs call the
autostretch rendering "only a display trick"
(siril.readthedocs.io/en/stable/processing/stretching.html).

### 2.5 Status of the three inherited hypotheses

| prior session's claim | audit status |
|---|---|
| **Boundary**: corner excess decays to field by ~420 px; member sensor-corners converge at the coverage boundary; flats' non-radial residuals add instead of averaging | Geometry **CONFIRMED, MEASURED** (§2.2); combine-specific ~+1%/≤500 px term **CONFIRMED, MEASURED** with per-set controls (§2.3). The *attribution* — which member-side residual (flat drift, `sky×V` tilt, distortion-model residual) dominates — remains **HYPOTHESIS**; magnitudes are consistent (members' known corner-zone residuals are 0.4–1.7%-class), and the discriminating test is the one-knob background-matching arm in §5: if matching members' backgrounds removes the corner term, the attribution is settled in the only way that matters |
| **Display amplification** ~√(sky·N): 2.1×/2.8× | **CONFIRMED** — the law was already a registry MEASURED entry; factors re-derived from verified inputs (§2.4) |
| **Residual patch** (cov28, ~1 kpx, no boundary decay): ~half real sky, ~half july31-member excess (+1.97% vs +1.03%, n=1) | **REVISED, MEASURED**: predominantly real sky (+1.4–2.1% in every per-set control at identical sky); the six-member-specific increment is +0.3–0.4%, not ~+0.9%, and near the flank systematic. The n=1 position is not exactly re-measurable (i450 products deleted; the surviving solve record carries no full WCS). The "july31 moonlit flat residual" attribution stays **HYPOTHESIS**, now with less amplitude to explain |

---

## 3. Provenance of every deciding number (audit question 2)

| deciding quantity | value used | provenance class | audit finding |
|---|---|---|---|
| Combine membership + "largest fully-covered crop" policy | full sets only; crop at cov == all members | **USER-RATIFIED** (commit bcecf0b) + repo doctrine (`TOOLS.md` Tier 1: probe true coverage, crop the max compose to a verified threshold) | Clean. The threshold itself (all members) is the ratified choice |
| Coverage maps | `covmap_*.fit`, k/n steps | **OFFICIAL TOOL** via tracked instrument (`coverage_probe.sh`: Siril fill/register/seqapplyreg/sum) | Instrument sound; **docstring contract stale** (says value/1000; disk says k/n→1.0 — §2.1) |
| Crop rectangles | `crop 1699 715 4159 3272`, `crop 2530 1297 3339 3068` | **IN-SESSION UNREVIEWED numpy** (largest-rectangle over the map; generator not tracked, only its outputs) | The *result* was verified through the registered tool-sourced guard (map cropped with identical args reads full coverage — re-verified §2.1). So: unreviewed derivation, verified product. Maximality is unverifiable but affects only yield, not correctness |
| 450 px inset (i450) | mask-erosion + largest rectangle, from ~420 px decay reading | **IN-SESSION UNREVIEWED numpy** over in-session profile boxes | REVOKED by the user as a bandaid — correctly; the registry's "never hide a rim defect with a crop" is the controlling entry. Dead |
| Corner-spread numbers (0.80% / 1.88%) | Siril `stat` regional medians | **OFFICIAL TOOL** via tracked instrument (`regional_stat.py`) | Numbers correct but **geometry-blind to this defect**: at box 400/margin 200 the cov13 corner term is mostly outside the boxes (the excess lives at 0–400 px). Registry already flags the four-corner metric as sky-confounded on structured fields; this adds: it also under-reaches a boundary-local term |
| bg-grid / corner-profile numbers | Siril `stat` medians via ad-hoc `.ssf` (preserved in `sessions/aug06/work/covcrop/`) | **OFFICIAL-TOOL numbers, IN-SESSION harness** — geometry choices (200 px/550 pitch; 100 px marches; one corner) unreviewed, generators untracked | The numbers themselves reproduce (this audit's reader agrees to ≤0.1). The *summaries* drawn from them ("−1.3..+2.7% vs ≤+1.0%", "~420 px decay") were in-session arithmetic; this audit's §2.3 replaces them with controlled same-sky comparisons |
| `--weight=nbstack` | compose weighting | **OFFICIAL TOOL option**, documented for exactly this pattern ("weight input images based on how many images were used to create them… useful for live stacking" — Siril 1.4 command reference) | The *choice* is doctrinally supported; its recorded justification is not: "the two nights' per-frame sky differs only ~6%, so nbstack ≈ inverse-variance" traces to **no record**, and the members on disk read **~60% apart** (night medians ~124 vs ~197, identical 2.5 s subs — MEASURED §record). The compose docstring itself already prescribes `noise` for the multi-night regime. Consequence is SNR-suboptimality and over-weighting the brighter night's residuals, not the corner mechanism |
| Pinned compose reference (set-03 `sub_02`, both arms, probe = compose) | `--ref` | **RECORDED DECISION** with measured mechanism in the tracked docstring (auto-ref sets canvas + addscale balance base; K_B 0.846 vs 0.951) + probe `--ref` wired (f97ce02) | Clean |
| Compose normalization | `-norm=addscale -output_norm`, plain mean | **OFFICIAL TOOL**; mean-not-rejection is a registry MEASURED entry (sigma across sub-stacks carves stars) | Correct as far as it goes — and **structurally global**: Siril's normalization "matches the mean background" per image [DOC]. The missing spatial step is not a Siril knob the session skipped; it does not exist inside `stack` except as the mosaic-stitching provisions (§4) |
| Judge stretch policy | per-product `autostretch -linked` after SPCC | **PINNED REPO POLICY** (registry multi-surface entry; `finish_render.sh` documents both regimes) using an **OFFICIAL TOOL** | The policy is self-consistent and its amplification behavior is a registry MEASURED entry — but the pinned rule was written for same-depth ladders. Applied across a 3–6× depth spread it *guarantees* the combines are judged 2–3× harsher than the per-set surfaces on the same question (§2.4). Known-property, unexamined-application: a policy gap, not a tool error |

Summary: the deciding numbers split into (a) ratified decisions and official-
tool measurements with clean provenance, (b) two tracked instruments with
stated-vs-actual gaps (coverage_probe contract; regional_stat geometry
blind spot for this defect class), (c) in-session unreviewed derivations
whose *outputs* were tool-verified (crop rectangles) or which are now
superseded/revoked (grids' summaries, i450), and (d) **one deciding claim
that traces to nothing and fails re-measurement (the ~6% night-sky figure
behind nbstack)**. The user's worry — guessing and drifting into in-house
numbers — is confirmed for class (c)/(d) specifically; the load-bearing
skeleton (membership, coverage, crops, reference, combiner) traces clean.

---

## 4. What the mainstream does (audit question 3)

Researched from primary sources; full sourced reports summarized here.

**Siril's own doctrine (the tool this repo drives).** [DOC]
- First choice for the same field across nights is **not stack-of-stacks**:
  "You still want to stack the images of the different sessions together …
  Calibrate all sessions independently … Register all preprocessed images
  together" (siril.org/faq). Community statement of why: one integration has
  "no seams between the panels"
  (discuss.pixls.us/t/stacking-two-highly-overlapping-panels-together-causes-some-mis-registered-stars/42306).
- Where per-panel stacks ARE combined, the official mosaics tutorial
  (siril.org/tutorials/mosaics/) attaches three provisions the audited
  compose used none of: **per-frame degree-1 background correction inside
  each member** ("It is recommended to make a background correction with
  polynomial of order 1 on the individual frames"), **`-overlap_norm`** (gain
  compensation computed on overlaps — Brown 2007; requires `-maximize`), and
  **`-feather=`** border blending. The 1.4 release notes name "Blending masks
  and normalization on overlaps: to stitch mosaics" as a headline feature
  (siril.org/download/2025-12-05-siril-1-4-0/).
- Background docs recommend per-frame extraction when the gradient varies
  across the sequence: "the gradient may have rotated with the acquisition
  session … you may consider removing the gradient in the subexposures: in a
  single image, the background gradient … generally follows a simple linear
  (degree 1) function"
  (siril.readthedocs.io/en/stable/processing/background.html). **This is
  exactly the open, user-gated `BACKLOG:render-ladder` L1 choice — Siril's
  own doctrine picks the per-frame arm for session-varying gradients.**
- Crop doctrine: "First operation: cropping the image … the dark bands on
  the sides will skew image statistics" (siril.org/tutorials/tuto-scripts/);
  the repo's crop-to-verified-coverage-before-background is already the
  registered pinned order and matches mainstream practice everywhere.

**PixInsight (the reference platform).** [DOC]
- ImageIntegration normalization is explicitly **global per-image scalars**
  (official reference doc), and the platform's answer to differing gradients
  is a family of **spatially-varying normalizations**: LocalNormalization
  (MMT-based, auto-run by WBPP since 1.8.9 — release notes), Adaptive
  Normalization ("per-pixel additive/scaling normalization functions …
  intended to solve … strong gradients of varying orientations and
  intensities" — 1.8.8-6 notes), and NormalizeScaleGradient ("normalizes the
  scale and gradient to that of the reference image" by stellar photometry +
  surface spline — astroprocessing.com/nsg.html). The NSG author's controlled
  demonstration of the skip-it failure mode is quoted in §1.
- Multi-night: calibrate per session, **integrate all frames in ONE
  ImageIntegration**; "Don't create two separate master lights … you'll lose
  the benefits of the integration for the common/overlapping pixels"
  (pixinsight.com forum 15048).
- True mosaics: register to union, **flatten each panel (DBE/ABE) before
  merging**, LinearFit/Frame Adaptation for intensity, then a seam-aware
  merge — GradientMergeMosaic (gradient-domain blend; its doc: linear
  matching alone "still leaves small seams"; partial-value coverage borders
  "cannot successfully merge … you will continue to see seams" → Shrink
  Radius + feathering) or PhotometricMosaic (scale + relative-gradient fit in
  the overlap).
- A forum case is the audited scenario almost verbatim (two pointings,
  multi-night, one combine): persistent banded color defects exactly where
  coverage drops, resolved by crop-to-common-coverage or mosaic-class
  handling of the extension (forum 15048).

**APP + professional pipelines.** [DOC]
- APP: normalization (background + dispersion, overlap-based) is always on —
  disabling it: "the results will be worse", especially multi-night; **LNC**
  (polynomial local normalization) exists precisely for "combining data with
  deviating gradients (multiple imaging sessions…)"; **MBB** feathers member
  borders ("reduce stack artefacts at the borders of regular integrations and
  … remove seams in mosaics"); the official mosaic tutorial's combine of
  per-panel integrations uses LNC 2nd-degree + MBB 10%
  (astropixelprocessor.com — FAQ + mosaic tutorial). Crop-the-uncovered-
  borders-then-remove-light-pollution is the moderator-stated standard order.
- Professional: **per-input background subtraction before co-addition is
  universal** — SWarp `SUBTRACT_BACK Y` default (§1); SDSS Stripe 82 coadds
  sky-subtract every frame (arxiv.org/abs/1405.7382); Pan-STARRS subtracts a
  superpixel background model per chip and flux-normalizes to a common
  zeropoint before stacking (arxiv.org/abs/1612.05245); Rubin/LSST runs
  full-focal-plane SkyCorrection before coaddition (pipelines.lsst.io).
- **No surveyed source documents "register + mean, fix the background later"
  as a route.** The un-normalized combine of offset panels appears in the
  literature only as the defective case (SWarp's "ugly patchwork"; APP-
  community "the lines are pronounced and the banding very noticeable").

**Answer to "is the repo's compose the amateur shortcut?"** The compose is
*half* the mainstream pattern: global normalization + mean of sub-stacks with
depth weighting is Siril's own live-stacking/panel-stitch shape, and plain
mean over sub-stacks is the registry-correct combiner. What every mainstream
route adds — and this one lacks entirely — is **member background/gradient
treatment** (per-frame degree-1, LN/NSG/LNC-class matching, or per-input
subtraction) **plus border handling at member edges** (feather/MBB/shrink,
or rejection where depth allows). The repo knew the general shape: the linear
background step is `BACKLOG:render-ladder` L1, scope-fenced and user-gated;
the `sky × V` member tilt is a registered open defect. The combines walked
into the gap between those two records: **members that each carry a known
uncorrected background tilt were composed by a mechanism whose documented
requirement is that member backgrounds be matched first.**

---

## 5. Toward fewer in-house surfaces (audit question 4) and the recommended path

The user decides; nothing below was executed. Ordered by leverage.

**5.1 The missing pipeline step (the root cause) — one decision, already
gated.** Adopt a member background-matching step for the combine class, as
the mainstream requires. This is `BACKLOG:render-ladder` L1 with its scope
extended from "render background" to "combine prerequisite", and Siril
provides three tool-native arms for a one-knob ladder, judged on the linear
grid + the user's eyes:
  - **per-frame `seqsubsky 1`** at calibration (Siril's documented
    recommendation for session-varying gradients; degree 1 only — the class
    limit protecting unresolved starlight stands; note the registered
    `--desky` dead end constrains WHERE it runs: on calibrated lights, never
    on the sky-flat's raw source frames);
  - **on-stack `subsky 1` per member sub-stack** before composing (the
    stack-level arm; crop-before-background already pinned);
  - **compose-side stitching**: `stack … -maximize -overlap_norm -feather=N`
    (native 1.4 machinery built for stitching stacked tiles; gain
    compensation is still global, so this arm tests border blending more
    than gradient matching).
  A same-sky corner probe (§2.3 method) before/after any arm is the
  objective instrument: the ~+1% combine-specific term either vanishes or it
  does not. This also settles the §2.5 attribution without any new in-house
  metric.

**5.2 Weighting.** Either record a measured justification for `nbstack` or
switch the multi-night compose to `--weight=noise` — the tracked docstring
already derives why (inverse-variance in both regimes); the recorded ~6%
claim is contradicted at ~60% by the members on disk. Same-night composes:
nbstack stands.

**5.3 Judge policy for cross-depth sets.** The pinned per-product
autostretch rule guarantees deeper products are judged through a steeper
transfer (√(sky·N), registered). Options for the user: (a) keep the rule and
require the linear-domain corner/grid numbers to accompany any cross-depth
judgment (the registry already commands "judge background uniformity from
LINEAR regional numbers"); (b) extend the pinned-MTF regime of
`finish_render.sh --mtf=` to expectation-matched cross-depth sets; (c) keep
judging combines harshly on the diagnostic surface as a deliberate high bar —
but then a per-set PASS at 1× is not evidence the combine class will pass at
3×, and the acceptance flow should say so. This is an aesthetics/policy call
the data cannot settle.

**5.4 Retire the in-session measurement surfaces.** The box-grid and
corner-march instruments earned their keep and should stop being session
improvisations: fold them into the tracked instrument (`regional_stat.py`
gaining `--grid`/`--march` modes, still 100% Siril `stat`), or adopt the
registry's already-registered candidate (ramp slope fitted over a grid) —
either way an acceptance-measure change needs explicit user ratification.
The same-sky cross-arm probe (WCS-mapped boxes) is the strongest instrument
this investigation produced and exists nowhere as reviewed code; if combines
remain a product class, it deserves the same promotion.

**5.5 Small hygiene, no decisions needed beyond assent:** fix
`coverage_probe.sh`'s stale value/1000 docstring to the measured k/n
contract; the crop-rectangle derivation (numpy largest-rectangle) should
live as a tiny reviewed script or be replaced by the existing framing UI
(`web/crop.html` + `verify_framing.py`) so a human-drawn, Siril-verified
rectangle is the only unreviewed-free path; `BACKLOG:cross-set-record-home`
already covers the records filed under set-03.

**5.6 What NOT to do (already registered, reaffirmed by this audit):** no
rejection across sub-stacks; no recrop-to-hide (i450 class); no in-house
gradient model on the deliverable — every candidate step above is an
official-tool mechanism; and no acceptance of the corner spread at box
400/margin 200 as evidence about this defect class (it under-reaches the
boundary term, §3).

---

## 6. One-paragraph summary for the record

The twin combines failed on a real, measured ~+1% linear corner term the
compose itself introduced — concentrated exactly where 8–12 member footprint
edges converge at the full-coverage corners — sitting on +1.5–2% genuine sky
structure, and rendered 2–3× harsher than any accepted surface by the pinned
depth-dependent judge stretch. The term is the documented consequence,
stated by Siril's tutorial, PixInsight's normalization authors, APP's docs
and SWarp's manual alike, of composing members whose background gradients
were never matched — a step every mainstream pipeline inserts and this
route omits, and which the repo already holds open as
`BACKLOG:render-ladder` L1 while its members carry the open `sky × V` tilt.
The compose's skeleton (membership, coverage, crops, reference, mean) traces
to ratified decisions and verified tool outputs; the drift the user feared
is confirmed at the margins — unreviewed in-session derivations, one
deciding claim (~6% night-sky delta) that re-measures at ~60%, and two
tracked instruments whose stated contracts lag their behavior. The fix
direction is a user decision among tool-native background-matching arms
(§5.1), not more cropping and not new in-house code.
