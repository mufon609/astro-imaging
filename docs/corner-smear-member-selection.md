# Corner smear → member selection: the decision map

**Question / scope.** The composed multi-night wide-field corpus
(`stack_july31+aug06+aug09+aug14_*`) carries elongated ("smeared") stars in its
left band and bottom corners while its centre is round. What is the mechanism,
which forms of fix were built and measured, what rule stands, why each
alternative was rejected, and what is still open. This is the document a
contributor reads BEFORE touching member selection, the crop rule, or the
compose's weighting; the numbers live in `datasets/aug06/experiments.jsonl`
(lines 98–119) and `datasets/corpus/smear_attribution/*.json`, and this page is
the map of them.

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
| **cropTselT** (117–119) | cropT + a FRAME-level threshold: exclude a member whole when S = mean FWHM over {centre, −600..−2400} exceeds the corpus's 25th percentile (2.444) by > 0.20 px; 13 members excluded (aug14 set-03 sub_03–06, set-04, set-05 — all inside cropT's 27) | 2.80/2.80/2.81/2.77 (= cropT within 0.024) | 2.510 (−0.017: NULL within the 0.02 bar) | 2.823 (= cropT) | −16.2 % of the frames (STACKCNT 8349 → 6997) | **NULL** on top of the portion rule: every station within 0.024 px of cropT, the top-left corners unchanged; REJECTED as a gate — the 13 members' degrading part was their entry zone, already removed |

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
  canonical's 64/65/65/67 on the 8-bit profile) and depth wherever the excluded
  data was not the only cover. **`bgnoise` is BLIND to that depth cost on this
  field** (MEASURED, GO #16: one member's centre box reads only 2.44/1.77/2.49×
  the canonical's against the 8.8× a photon-limited mean would give — the
  Milky Way's unresolved texture sets the floor), so sel57's "+0.2..+2.7 %" was
  a blind reading, not a free cull; every cull's depth cost is its STACKCNT
  fraction (sel57 −25.8 %, cropTselT −16.2 %), and the portion rule's cost is
  the 6.44 % of pixel-frames it removes, mostly where the band's depth was
  never at stake.
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

Member selection by measured quality is the fix for this class, and on this
corpus the PORTION rule alone carries it: the entry-side asymmetry threshold
(cropT — approved) removes the degrading part of the soft members and keeps
their interiors, which the frame rule showed are not degrading anything (NULL at
−16.2 % of the frames). Encode the portion rule as ONE stage between the per-set
sub-stacks and the compose — profile every member with `star_stations.py`, apply
the rule with its constant visible in the record, report the frame score S_i
beside it (an advisory, not a gate), write cropped COPIES (never touch a member),
compose the curated set — with a positive control (a planted asymmetric member
that MUST be cropped) and a removal condition (Siril's `stack` offers per-member
spatial weights or a per-member quality cull of its own). On the owner's word.

### Encoding design — READY, UNBUILT (awaits the owner's go)

Hook point: a MEMBER stage between the per-set sub-stacks and the compose — its
own script, never inside `run_undistort_compose.sh`, whose contract is "dirs of
`sub_*.fit` → link, gate (T0/T1), preflight, register, stack" and which never
modifies a member; both arms reached it through exactly that door (a curated dir
of symlinks + cropped copies in canonical order), and a stage inside it would
re-crop on every compose and hide the copies where nothing can measure them.
`run_corpus_combine.sh` enumerates the `groups_set-NN` dirs and hands them to the
compose; the stage sits there.

- `scripts/stack/run_member_crop.sh <session-dir>... --out=<curated dir> --bar=0.20
  [--ref=<member>]`: enumerate the canonical member dirs with the combine's own
  allow-list (one shared function, not a copy of its loop); profile every member at
  the ±600..±2400 stations with `star_stations.py`'s geometry (the GO #13 driver as
  a script, one Siril run per member, lists kept); apply the asymmetry rule with the
  constant VISIBLE on the command line and stamped; write the interior score S_i
  beside it as an ADVISORY (reported, never a gate — the GO #16 NULL); write the
  curated dir (symlinks for untouched members, Siril-cropped 32-bit copies for the
  rest, canonical order) and a tracked JSON record (the per-member table, the rule,
  x_c per member, the cut, what was cropped and why); assert per copy what GO #12/#13
  verified (kept pixels identical to the original's first kept columns, CRPIX/CRVAL/
  SIP unchanged, provenance keys present, a single matrix form).
- Positive control: a planted member whose profile crosses the bar at a known
  station MUST come out cropped at onset − 300; a flat-profile member MUST come out
  a symlink.
- `run_corpus_combine.sh` gains one flag (`--portion-rule=<bar>`, or the recipe
  key) that runs the stage and passes the curated dir to the compose; with it absent
  the chain is byte-for-byte the current one (the canonical stays reproducible).
- Provenance, per member: structured keys written by Siril `update_key` at crop time
  — MEMCROP = x_c (int), MEMCRULE = "asym>0.20px@r400 top30", MEMCPROV = the
  record's path/sha, MEMCSCOR = S_i; untouched members carry NONE (their absence is
  the fact that they are originals — the stage never writes to an original).
  Composite: `header_composite_provenance_lines()` (`stamp_headers.sh`) aggregates
  MEMCROP as it does CALPROV/DISTPROV — NCROPPED, MEMCRULE (identical across the
  cropped members or the stamp refuses: one rule per compose), MEMCXCS (the
  "2100x15/1500x11/900x1" histogram), MEMCPROV. The T0 gate's required tuple is
  unchanged (a cropped copy carries every required key: 27/27, 14/14 measured).
- The reference: pinned by PATH as today; the stage refuses to crop the pinned
  reference unless the rule crops it, and then says so (the anchor's IKSS statistics
  change with its columns — a cropped anchor is UNTESTED; 36 was uncropped in both
  arms).
- The constant lives in the corpus recipe block (a tracked file), not a script
  default. Removal condition (the register row): "retire when Siril's compose accepts
  per-member weight maps or a per-member region mask" — a mask is the crop without
  the coverage cost — the same condition the SWarp scaffolding carries.
- Cautions carried from the measurements: the profile is CENTRE-ROW only (x_c and S_i
  alike) — a member soft in its top/bottom rows passes both rules, stated in the
  docstring; a canonical rebuild under the stage changes the canvas (cropT −16 × −6
  px) and every rim-fed corner as cropT did, so the baseline guard's corner-spread
  rows move by the rim change, not by a regression — re-seed after the owner's
  acceptance, not before.

## Status

EMPIRICALLY TESTED for the attribution (§2), the portion rule (§3, cropT —
owner-approved) and the frame rule (a NULL on top of it — not encoded as a gate;
its score stays a reported measurement with a re-test condition: a corpus whose
soft night is soft in its INTERIOR beyond the entry zone); the encoding is
UNBUILT. Open: the constant's placement (§4); the +2400 outermost station's
blind spot (a defect confined to a member's last ~100–500 px is invisible to
every form above); the depth measure's regime; weighting vs exclusion (§6).

## Graduation

BACKLOG `compose-homography-smear` (the item this closes as a registration
question), `one-sided-band`, `corner-fix-landscape`, `final-best-percent-pass`
(the frame rule is its threshold form) point here; the dead-end registry
carries the refuted registration mechanism (`docs/dead-ends/stacking-compose.md`)
and the shape_at_sky trap (`docs/dead-ends/verification-traps.md`);
`docs/pipeline-wide-field-untracked.md` names the selection stage.
