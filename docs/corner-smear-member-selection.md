# Corner smear → member selection: the decision map

**Question / scope.** The composed multi-night wide-field corpus
(`stack_july31+aug06+aug09+aug14_*`) carries elongated ("smeared") stars in its
left band and bottom corners while its centre is round. What is the mechanism,
which forms of fix were built and measured, what rule stands, why each
alternative was rejected, and what is still open. This is the document a
contributor reads BEFORE touching member selection, the crop rule, or the
compose's weighting; the numbers live in `datasets/aug06/experiments.jsonl`
(lines 98–116 landed; 117–118 are the frame rule's pre-registration and verdict,
pending) and `datasets/corpus/smear_attribution/*.json`, and this page is the
map of them.

**Context.** Siril 1.4.4 flatpak; the undistort chain (`docs/pipeline-wide-field-untracked.md`);
77 per-set sub-stacks ("members", STACKCNT 8349 frames) from four nights composed
by `run_undistort_compose.sh` (per-member astrometric registration, lanczos4,
mean with `-norm=addscale -weight=nbstack`, reference member 36 =
aug09/set-02/sub_02 pinned). Every star-shape number below is Siril `findstar`
through `scripts/qa/shape_at_sky.py` (800-px boxes placed by each product's own
WCS, top-30 FWHM in px and roundness) or `star_stations.py` on a member; depth is
Siril `bgnoise`; rim levels are an 8-bit diagnostic. Owner rulings are quoted
with their date because the date is the register datum.

## Findings

### 1. The defect, measured on the canonical corpus

| where | FWHM / roundness | note |
|---|---|---|
| left band x10–x25 | 2.88–2.97 / 0.84–0.86 | the DEFECT stations |
| centre x45–x55 | 2.51–2.52 / 0.96–0.97 | the clean control |
| bottom-left corner (700,4200) | 3.03 / 0.83 | the worst box |
| right side x70–x95 | 2.70–2.81 / 0.92–0.98 | soft (lens radial term) but ROUND |
| top-right corners | 2.68–2.71 / 0.976–0.987 | round |

The elongation is a LEFT-band / bottom-corner phenomenon. The right side is
softened symmetrically by the lens and is not smeared — there is nothing
night-dependent to exclude there (`cropT_arm.json`, the position table).

### 2. Attribution — four measurements, each pre-registered, each one knob

1. **Registration is NOT the mechanism** (`drift_span_discriminator_exit_edge`,
   ledger 98–99). Three nested arms of aug06/set-01 with 26.1 / 104.3 / 235.7 px
   of stacked drift span: the exit-side blur is flat across the 9× span change
   (ΔFWHM(L−S) −0.025..+0.055 px, roundness within 0.018), so a registration
   error that grows with the span is refuted. The one span-dependent station is
   at the far ENTRY side (+0.085 px, monotone).
2. **The band is member-borne** (`left_band_member_attribution`, ledger 100–101,
   108). The corpus's left band is built exclusively from the members' ENTRY-side
   columns (400–1470 px from their entry edge), and those columns read on the
   members what the corpus reads: median 2.66–2.75 px vs corpus 2.89–2.98 = the
   compose floor + 0.03–0.11. (The instrument's y-convention defect found here
   and fixed with a positive control: `docs/dead-ends/verification-traps.md`.)
3. **It is in the photons, night-dominated** (`night_dependence_single_raws`,
   ledger 102–103). Eighteen single raws (6 sets × first/middle/last), debayered
   uncalibrated: at along+2400 aug14's raws read 2.94–3.03 px / 0.53 against
   july31/set-01's 2.18 / 0.80; member − raw sits in the stacking-floor band on
   11 of 12 pairings; the by-night ordering of the raws reproduces the members'.
   aug14 is softer EVERYWHERE (+0.4 px at the centre) and its entry-side excess
   over the exit side is itself night-dependent (+0.41/+0.45 aug14, +0.29 aug09).
4. **The corners: the lens's asymmetric term** (`corner_direction`, ledger
   104–105). On raws, members and corpus: the two BOTTOM corners are radial
   (coma-like; bottom-right strongest, e 0.30–0.49, night-ordered like the
   mid-row), the TOP corners are not; stacking rounds the exit-side corners and
   keeps the entry-side ones. The corpus's bottom-left corner is the members'
   top-right corners through the ~180° member↔canvas flip (RA rises with x on
   every member; the corpus canvas is RA-flipped).

Consequence: the fix belongs to MEMBER SELECTION — which members, and which
columns of them, enter the mean — not to registration, the reference, or the
kernel. Selection cannot remove the lens's symmetric radial softening (every
frame has it, the best available at the edge is the edge); it can remove the
night-dependent entry-side excess and the frames that are softer than the rest.

### 3. Forms built and measured (all against the canonical, same pinned reference)

| form | rule | band x10–x25 | centre x50 | BL corner | depth cost | verdict |
|---|---|---|---|---|---|---|
| canonical | — | 2.97/2.94/2.93/2.88 | 2.522 | 3.033 | — | the control |
| **sel57** (ledger 106–107) | RANK: drop the worst quartile (20 members) by +2400-station FWHM, whole | 2.76/2.75/2.79/2.76 | 2.480 | 2.800 | bgnoise +2.7/+0.2/+1.0 % (predicted +16 % by count) | positive test; REJECTED as a pipeline rule — a rank cuts 20 members on an equal-quality corpus too (owner, 2026-08-29: "should we have cut off thresholds opposed to blanket cut rules?") |
| **crop20** (109–110) | the same 20 members kept, only their entry-side columns beyond centre+900 px removed (Siril `crop` of copies, MEMCROP stamped) | 2.79/2.81/2.82/2.79 | 2.527 | 2.805 | 1.003/0.992/0.993 (full depth) | reproduces sel57's band gain at full depth and canvas, no seam at 20 boundaries; still a rank |
| **cropT** (111–114) | THRESHOLD: crop a member's entry columns beyond the onset where FWHM(+dx) − FWHM(−dx) > 0.20 px, x_c = onset − 300; intrinsic, rankless; 27 of 77 cropped (x_c 2100 ×15 / 1500 ×11 / 900 ×1) | 2.79/2.805/2.81/2.79 | 2.515 | 2.817 | 1.007/0.996/1.010 | = crop20 within 0.01 px, no seam at 27/27; **OWNER-APPROVED 2026-08-29** as a positive test |
| SWarp tapered weight (115–116) | per-member MAP_WEIGHT tapering the same columns to 2 % instead of removing them (keeps rim coverage) | not built | — | — | — | STOPPED by the owner: the rim is out of scope (§5); engine facts kept in `swtaper_probes.json` + the register row |
| **cropTselT** (117–118, building) | cropT + a FRAME-level threshold: exclude a member whole when S = mean FWHM over {centre, −600..−2400} exceeds the corpus's 25th percentile by > 0.20 px; predicted 13 members (aug14 set-03 sub_03–06, set-04, set-05) | predicted ≤ cropT | predicted −0.02..−0.05 | ≈ cropT | to be read per the bgnoise regime probe | pending |

Forms refuted BEFORE building, from the same profiles (`cropT_arm.json`):
the intrinsic gradient FWHM(+dx) − FWHM(centre) > 0.20 trips on 66/77 members
at the entry side AND 67/77 at the exit side — it measures the lens's radial term
present on both sides, would drop the band's depth 3–10× (coverers x10 4→1,
x15 13→3, x20 36→7) and crop the reference; an absolute FWHM(+dx) > 2.80 px bar
(35 members) keys on delivered shape and would crop a uniformly soft night whole.
A CENTRE-only frame score is refused for the frame-level rule: july31/set-01 and
aug09/set-01 have soft centres (2.44–2.54) with the sharpest edges in the corpus
(+2400 2.41–2.46); a centre bar would cut the best edge frames.

### 4. The constant, honestly

0.20 px was chosen from the per-set entry-minus-exit asymmetries at +2400
(aug14 +0.27..+0.47 and aug09/set-04/05 +0.23..+0.28 against ≤ 0.13 elsewhere)
and then MEASURED to sit in a continuum, not a gap: the values around it run
…0.147 | 0.165 … 0.200 | 0.222 … 0.233 | 0.263…, the step at the bar (0.022) is
the profile's own run-to-run scatter, and the eight kept members just under it
have corners indistinguishable from the five cropped just over it (BR-corner
medians 2.718 vs 2.757 px; the 42 clearly-under read 2.547). Two kept members are
individually worse than four cropped ones because their EXIT sides are soft too
and the asymmetry subtracts that. Bounded cost of keeping the eight: ≤ 0.04 px
at the band (`cropT_arm.json`, `bar_placement_0p20`). The frame-level rule's cut
(2.644) sits in a continuum the same way (step 0.006). Options recorded for the
owner, none built: keep 0.20; move to the 0.16 step (takes the eight); key on the
delivered corner (re-opens the uniformly-soft-night objection). Any bar in a
continuum is a policy, and the policy is the owner's (§5).

### 5. Owner rulings that shape the rule (register data)

- 2026-08-29 — "one knob at a time so we can fully analyze the impact — you
  decide"; "test what you need before turning the knobs".
- 2026-08-29 — on sel57: "consider this win as a positive test until we have it
  refined and tested — then it can become the new pipeline"; on rank vs
  threshold: "consider what happens if ALL the images were to be the same
  quality — then we would lose depth for no reason … should we have cut off
  thresholds opposed to blanket cut rules?" → every pipeline rule is a QUALITY
  THRESHOLD that excludes nothing on an equal-quality corpus.
- 2026-08-29 — `july31+aug06+aug09+aug14_cropT_spcc-linked.png` approved.
- 2026-08-29 — the priorities: "im not focused on the rim, im focused on the
  smears in the corner. the edges have already been ruled to be fixed with more
  depth, as in frames. the focus isn't to fix what more frames naturally buys us
  — it's to make the most of what we have or at least do not let in frames (or
  portions of a frame) that degrade the other frames present. after the full
  image is tuned — i will manually crop what i want to keep OR/AND i will expand
  the frame overtime with more sessions." → coverage steps at the rim are an
  accepted, reported cost; exclusion of degrading frames/portions is the goal.
- Standing (memory): the data is a given — never recommend acquisition or
  equipment changes; fixes live in the chain at the stage where the defect is
  well-defined (here: member selection before the compose).

### 6. What the measurements settle, and the trade

- A member's entry-side excess and a night's overall softness are both in the
  photons; neither is recoverable downstream. The mean of the members is only
  as sharp as what enters it, so the honest optimum is to let in the best
  available at each field position and nothing worse.
- Exclusion costs coverage where the excluded columns were the only cover (the
  bottom-left rim staircase: first-covered-column levels 39/53/58/66 vs the
  canonical's 64/65/65/67 on the 8-bit profile) and depth where many members
  cover — measured small at the centre (bgnoise +0.2..+2.7 % for 26 % of the
  frames removed), with the premise that `bgnoise` is photon-limited on this
  field still to be probed (GO #16).
- Weighting instead of exclusion ("make the most of what we have") is the
  standards-first alternative (inverse-variance; SWarp MAP_WEIGHT or Siril
  `-weight=noise`). It is queued behind the exclusion rules because a scalar
  per-frame weight cannot address portions, and a per-pixel weight needs the
  SWarp engine whose control arm was never built.

## Sources

- Records: `datasets/aug06/experiments.jsonl` lines 98–116 (117–118 pending);
  `datasets/corpus/smear_attribution/{left_band_member_attribution, night_dependence_single_raws, corner_direction, member_selection_arm, crop20_arm, cropT_arm, swtaper_probes}.json` (+ `cropTselT_arm.json` when the frame rule lands);
  `datasets/aug06/set-01/qa_work/drift_span_discriminator.json`.
- Instruments: `scripts/qa/shape_at_sky.py`, `scripts/qa/star_stations.py`,
  `scripts/qa/star_shape.py` (seqtilt), Siril `stat`/`bgnoise`.
- Siril `crop`, `findstar`, `stack -norm=addscale -weight=nbstack`:
  https://siril.readthedocs.io/en/stable/Commands.html
- SWarp (the stopped route): https://astromatic.github.io/swarp/ ; the engine
  facts measured here are in `swtaper_probes.json` and the BACKLOG register row.

## Verdict / recommendation

Member selection by measured quality is the fix for this class: a PORTION rule
(the entry-side asymmetry threshold, cropT — approved) and a FRAME rule (the
interior+exit-side threshold, cropTselT — under test), both intrinsic or
corpus-relative, both excluding nothing on an equal-quality corpus. Encode them
as ONE stage between the per-set sub-stacks and the compose — profile every
member with `star_stations.py`, apply the two rules with their constants
visible in the record, write cropped COPIES (never touch a member), compose the
curated set — with a positive control (a planted soft member that MUST be
excluded) and a removal condition (Siril's `stack` offers per-member spatial
weights or a per-member quality cull of its own). Only after the frame rule's
verdict and the owner's word.

## Status

EMPIRICALLY TESTED for the attribution (§2) and the portion rule (§3, cropT —
owner-approved); the frame rule is PRE-REGISTERED and building; the encoding
is UNBUILT. Open: the constant's placement (§4); the +2400 outermost station's
blind spot (a defect confined to a member's last ~100–500 px is invisible to
every form above); the depth measure's regime; weighting vs exclusion (§6).

## Graduation

BACKLOG `compose-homography-smear` (the item this closes as a registration
question), `one-sided-band`, `corner-fix-landscape`, `final-best-percent-pass`
(the frame rule is its threshold form) point here; the dead-end registry
carries the refuted registration mechanism (`docs/dead-ends/stacking-compose.md`)
and the shape_at_sky trap (`docs/dead-ends/verification-traps.md`);
`docs/pipeline-wide-field-untracked.md` names the selection stage.
