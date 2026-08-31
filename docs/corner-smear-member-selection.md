# Corner smear → member selection: the decision map

**Question / scope.** The composed multi-night wide-field corpus
(`stack_july31+aug06+aug09+aug14_*`) carries elongated ("smeared") stars in its
left band and bottom corners while its centre is round. What is the mechanism,
which forms of fix were built and measured, what rule stands, why each
alternative was rejected, and what is still open. This is the document a
contributor reads BEFORE touching member selection, the crop rule, or the
compose's weighting; the numbers live in `datasets/aug06/experiments.jsonl`
(lines 98–136), `datasets/corpus/smear_attribution/*.json` (the arms) and
`datasets/corpus/member_selection/*.json` (the stage, its acceptance, the
candidate, the promote), and this page is the map of them.

**Context.** Siril 1.4.4 flatpak; the undistort chain (`docs/pipeline-wide-field-untracked.md`);
77 per-set sub-stacks ("members", STACKCNT 8349 frames) from four nights composed
by `run_undistort_compose.sh` (per-member astrometric registration, lanczos4,
mean with `-norm=addscale -weight=nbstack`; the arms pinned reference member
36 = aug09/set-02/sub_02, the chain DERIVES its reference on the curated members
— 35 = aug09/set-02/sub_01, §3). Every star-shape number below is Siril `findstar`
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

### 3. Forms built and measured (all against the pre-stage canonical except the rowmin row, which is against the chain canonical; the arms share the pinned reference 36, the chain derives 35, rowmin pins 35)

| form | rule | band x10–x25 | centre x50 | BL corner | depth cost | verdict |
|---|---|---|---|---|---|---|
| canonical | — | 2.97/2.94/2.93/2.88 | 2.522 | 3.033 | — | the control |
| **sel57** (ledger 106–107) | RANK: drop the worst quartile (20 members) by +2400-station FWHM, whole | 2.76/2.75/2.79/2.76 | 2.480 | 2.800 | bgnoise +2.7/+0.2/+1.0 % (predicted +16 % by count) | positive test; REJECTED as a pipeline rule — a rank cuts 20 members on an equal-quality corpus too (owner, 2026-08-29: "should we have cut off thresholds opposed to blanket cut rules?") |
| **crop20** (109–110) | the same 20 members kept, only their entry-side columns beyond centre+900 px removed (Siril `crop` of copies, MEMCROP stamped) | 2.79/2.81/2.82/2.79 | 2.527 | 2.805 | 1.003/0.992/0.993 (full depth) | reproduces sel57's band gain at full depth and canvas, no seam at 20 boundaries; still a rank |
| **cropT** (111–114) | THRESHOLD: crop a member's entry columns beyond the onset where FWHM(+dx) − FWHM(−dx) > 0.20 px, x_c = onset − 300; intrinsic, rankless; 27 of 77 cropped (x_c 2100 ×15 / 1500 ×11 / 900 ×1) | 2.79/2.805/2.81/2.79 | 2.515 | 2.817 | 1.007/0.996/1.010 | = crop20 within 0.01 px, no seam at 27/27; **OWNER-APPROVED 2026-08-29** as a positive test |
| SWarp tapered weight (115–116) | per-member MAP_WEIGHT tapering the same columns to 2 % instead of removing them (keeps rim coverage) | not built | — | — | — | STOPPED by the owner: the rim is out of scope (§5); engine facts kept in `swtaper_probes.json` + the register row |
| **cropTselT** (117–119) | cropT + a FRAME-level threshold: exclude a member whole when S = mean FWHM over {centre, −600..−2400} exceeds the corpus's 25th percentile (2.444) by > 0.20 px; 13 members excluded (aug14 set-03 sub_03–06, set-04, set-05 — all inside cropT's 27) | 2.80/2.80/2.81/2.77 (= cropT within 0.024) | 2.510 (−0.017: NULL within the 0.02 bar) | 2.823 (= cropT) | −16.2 % of the frames (STACKCNT 8349 → 6997) | **NULL** on top of the portion rule: every station within 0.024 px of cropT, the top-left corners unchanged; REJECTED as a gate — the 13 members' degrading part was their entry zone, already removed |
| **the encoded stage, acceptance** (120–122) | `run_member_crop.sh` on the same 77: arm 1 with cropT's own recorded profiles, arm 2 with a fresh Siril `findstar` profile | = cropT by identity | = cropT | = cropT | none (no compose; the curated dir only) | **IDENTITY 27/27** — every copy pixel-identical to cropT's, 50/50 symlinks to the same targets, 77/77 onset/x_c equal, reference 36 untouched with the refusal path silent; **DETERMINISM 0/693** — the fresh profile re-measured every station identically (77 × 9, max Δ 0.000 px), 77/77 verdicts, the on-the-bar member 2.988/2.788 → 0.200 both times; the stage IS cropT |
| **the chain: `--portion-rule` → the canonical** (123–128) | `run_corpus_combine.sh --portion-rule`: stage (0 profiled / 77 cached) → compose → derived-reference check → finish, 170 s; then the `_full` rebuild under it | 2.775/2.805/2.805/2.795 (= cropT within 0.028 at every interior station; the x05 rim station 0.063) | 2.525 | 2.800 / 0.844 | full depth (STACKCNT 8349; 6.44 % of pixel-frames removed) | **OWNER-APPROVED 2026-08-29 and PROMOTED**: the rebuilt `stack_july31+aug06+aug09+aug14_full` is 0 differing pixels from the approved candidate on the stack and the `_spcc` (144,874,080 px each), its judge PNG byte-identical; the pre-stage canonical moved aside as `_nosel`. Reference DERIVED as 35, not the arms' 36: the compose picks the member whose centre-pixel pointing is nearest the median pointing, and the 27 crops move each cropped member's centre (W − kept)/2 columns toward its exit side, moving the median with it — deterministic, not a quality difference |
| **rowmin** (131–132) | the chain's selection with x_c = MIN over the member's three profiled rows on the six row-profiled members (900 ×5; the on-the-bar member 1500), reference pinned 35, nbstack; every other member as the chain | 2.772/2.812/2.798/2.792 (= the canonical within 0.007) | 2.525 (0.000) | 2.810 / 0.834 (+0.010) | STACKCNT 8349; 7.65 % of pixel-frames removed (+1.2 %) | **CLEAN NULL** — at the removed columns' own sky positions (pinned through both WCS: 600–1500 px inward of the corner boxes) −0.004..−0.033 px against a pre-registered ≥ 0.10; six seams clean; x05 (rim) and x85 read +0.038 while the bottom-right corner read −0.038 — the changed member set at re-placed boxes, not noise: the compose repeat floor is ZERO (`repeat_floor.json`); `rowmin_arm.json` |

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
a step between DIFFERENT members at flat stations — not measurement scatter:
`findstar` on identical input is deterministic (two independent profiles of the
77 at 17B differed at 0 of 693 station values; the on-the-bar member read
2.988/2.788 → 0.200 both times) — and the eight kept members just under it
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
- Weighting instead of exclusion ("make the most of what we have") was the
  standards-first alternative and is MEASURED a NULL (`weight_noise_arm.json`,
  ledger 134–136): Siril's `-weight=noise` — (scale/bgnoise)² on the registered
  image's non-null pixels, probed before the knob was turned — moved ~10 % of the
  weight from the sharpest night (july31 0.900, the noisiest by Siril's estimator)
  to the softest (aug14 1.094), and no station of 58 moved beyond +0.016 px against
  the nbstack canonical. On this corpus excluding the degrading PORTIONS is the
  lever; weighting whole members is not. The per-pixel weight (SWarp) stays closed
  by the owner's stop.
- The profile stays on the centre row by MEASUREMENT, not omission
  (`row_profiles.json`, `rowmin_arm.json`): profiled on the top and bottom rows,
  the bottom row crosses the bar ~600 px earlier on 5/5 cropped members, but the
  row-resolved crop (§3, rowmin) was a clean NULL — the columns it removes sit
  under deep four-night coverage (dilution, a hypothesis) — at +1.2 %
  pixel-frames. The TOP row is softer on EVERY night (`toprow_profiles.json`, all
  77: median top − centre at the centre station july31 +0.265, aug06 +0.240, aug09
  +0.335, aug14 +0.395 px — a vertical off-axis term of the lens, with the soft
  nights ~0.1–0.2 px worse and the entry-side asymmetry present there too), the
  bottom-left corner boxes are fed mostly by the SHARP nights' top strips
  (`toprow_corner_coverage.json`: 16 coverers at corner_700_4200, three of them
  over the bar), and the corpus-relative ROW-level exclusion RAN as an arm
  (`toprow_arm.json`, the 29 over-bar members' top 800 rows removed): a TRADE, not
  adopted — corner_1300_4900 −0.038 but the target corner_700_4200 +0.020, x05/x10
  +0.065/+0.053, the bottom-right corner's roundness −0.034 with 17 of 37 coverers
  gone, the union 204 rows shorter; the corpus-wide part is not removable by any
  exclusion (`docs/dead-ends/stacking-compose.md`, "THE TOP-ROW SOFTENING IS
  CORPUS-WIDE"). The +2400 blind spot is bounded (same-aperture Δ median +0.008 px;
  per-member calls unresolvable at r 200, scatter ±0.12 px).

## Sources

- Records: `datasets/aug06/experiments.jsonl` lines 98–136;
  `datasets/corpus/smear_attribution/{left_band_member_attribution, night_dependence_single_raws, corner_direction, member_selection_arm, crop20_arm, cropT_arm, cropTselT_arm, swtaper_probes, row_profiles, rowmin_arm, rowmin_curated, weight_noise_arm}.json`;
  `datasets/aug06/set-01/qa_work/drift_span_discriminator.json`;
  `datasets/corpus/member_selection/{acceptance_17B_armA, acceptance_17B_armB, candidate_msel, promote_manifest, profiles, july31+aug06+aug09+aug14_full_portion}.json`;
  `datasets/corpus/recipe.json` (the constants); `datasets/corpus/baseline.json`
  (the corpus's no-regression slot).
- Instruments: `scripts/qa/shape_at_sky.py`, `scripts/qa/star_stations.py`,
  `git show d374450:scripts/qa/star_shape.py` (seqtilt), `scripts/qa/regional_stat.py`, Siril
  `stat`/`bgnoise`.
- Siril `crop`, `findstar`, `stack -norm=addscale -weight=nbstack`:
  https://siril.readthedocs.io/en/stable/Commands.html
- SWarp (the stopped route): https://astromatic.github.io/swarp/ ; the engine
  facts measured here are in `swtaper_probes.json` and the BACKLOG register row.

## Verdict / recommendation

Member selection by measured quality is the fix for this class, and on this
corpus the PORTION rule alone carries it: the entry-side asymmetry threshold
(cropT — approved) removes the degrading part of the soft members and keeps
their interiors, which the frame rule showed are not degrading anything (NULL at
−16.2 % of the frames). It is encoded as ONE stage between the per-set
sub-stacks and the compose, its constant visible in the recipe, the frame score
S_i reported beside it as an advisory, every copy verified, a positive control in
the guard suite, a removal condition in the register — and the corpus canonical
is built under it. What follows is that stage as it stands.

### The stage as built

Hook point: a MEMBER stage between the per-set sub-stacks and the compose — its
own script, never inside `run_undistort_compose.sh`, whose contract is "dirs of
`sub_*.fit` → link, gate (T0/T1), preflight, register, stack" and which never
modifies a member. `run_corpus_combine.sh --portion-rule[=<bar>]` runs the stage
first and hands the compose the curated dir; without the flag the compose is the
pre-stage chain (the `_nosel` family is that product).

- **Scripts.** `scripts/stack/run_member_crop.sh` (the stage) +
  `scripts/stack/member_profile.py` (profile / rule / verify) +
  `scripts/lib/member_dirs.sh` (the ONE member-dir enumerator, shared with the
  combine). Profile = Siril `findstar` at `star_stations.py`'s geometry, one run
  per member, through the tracked profile CACHE
  (`datasets/corpus/member_selection/profiles.json`, keyed by content sha256 +
  measuring geometry; a run says which members it profiled — the canonical build
  reads "0 profiled, 77 cached"). Verdict = a pure function of a member's own
  profile and the recipe constants, so adding a night never changes an earlier
  verdict.
- **The constants** live in `datasets/corpus/recipe.json`
  `member_selection.portion_rule` — `bar_px` 0.20, `stations_px` 600/1200/1800/2400,
  `radius_px` 400, `top_n` 30, `half_width_px` 300 — never a script default; a
  missing key is a hard stop naming it; `--bar`/`--half-width` override aloud.
- **The rule**, per member: onset = the smallest station dx where FWHM(+dx) −
  FWHM(−dx) > bar and stays above outward; x_c = onset − half-width; the
  entry-side columns beyond W/2 + x_c are removed from a Siril-cropped 32-bit
  COPY (`crop 0 0 round(W/2+x_c) H`); no station over the bar → a symlink to the
  untouched original. Originals are never written. A station skipped for member
  width vetoes the outward tail (no crop on incomplete evidence), warned per
  member. The profile is CENTRE-ROW only (x_c and S_i alike): a member soft in
  its top/bottom rows passes both rules — stated in the docstring.
- **Provenance.** Per cropped copy, by Siril `update_key`: MEMCROP = x_c,
  MEMCRULE = "asym>0.20px@r400 top30" (the aggregation identity key), MEMCSCOR
  = S_i, MEMCPROV = the record path (via `header_apply_keys` — Siril truncates a
  string at `/`). Untouched members carry none. The composite aggregates
  NCROPPED / MEMCRULE (identical across the cropped members or the stamp
  refuses) / MEMCXCS ("2100x15/1500x11/900x1") / MEMCPROV
  (`stamp_headers.sh`); the canonical reads NCROPPED 27.
- **Verify, per copy**: kept pixels identical to the original's first kept
  columns; CRPIX/CRVAL and the matrix form exact; the T0 keys present; the four
  MEMC* keys; SIP asserted two ways (below). Per symlink: resolves to the
  original, no MEMC* keys. The verdict lands in the stage record
  (`datasets/corpus/member_selection/<tag>_portion.json`).
- **Naming.** The product TAG derives from `--out`'s basename `stack_<tag>.fit`:
  the curated dir is `curated_<tag>`, the stage record `<tag>_portion.json`, the
  finish's `_wcs`/`_spcc`/judge PNG carry the tag; with no `--out` the TAG is
  `<NAME>_full` — the canonical. A `--out` candidate therefore never writes onto
  the canonical's names.
- **The reference.** A PINNED reference (`--ref`) is refused for cropping — exit 3
  — unless `--allow-ref-crop` says it aloud (a cropped anchor is untested). The
  corpus combine DERIVES its reference after the stage
  (`derive_compose_ref.py`: nearest centre-pixel pointing to the median) and
  reads it back against the stage record: a cropped derived anchor is a loud
  line + `reference_cropped` in the record, never a refusal. On this corpus the
  derived reference 35 is uncropped (§3).
- **The guard, last.** `run_corpus_combine.sh` ends with `baseline_guard.py
  --baseline=datasets/corpus/baseline.json` against the finished `_spcc` — the
  corpus's own slot, because the combine files its finish under the reference
  SET and the per-set derivation would overwrite that set's baseline. Slot absent
  = first build (one line, exit 0; a build never seeds itself); a regression
  exits 8, nothing rewritten. The slot was seeded on the promoted product: corner
  spread 0.474 %, edge dipole −0.0095, centre medians 42.1/42.3/42.1, STACKNRM
  addscale, canvas 8520×5668.
- **Positive controls** (`run_member_crop.sh --selftest`, in `run_guards`): a
  planted member crossing the bar at +1800 MUST crop at 1500 with the four
  MEMC* keys and kept-pixel identity; a flat member MUST be a symlink with none;
  a SYMMETRIC both-sides rise MUST NOT crop (the refuted intrinsic form); the
  pinned-reference refusal MUST fire and `--allow-ref-crop` lift it aloud; the
  cache path MUST serve a run with 0 profiled, verdicts identical, cache
  byte-identical.
- **Removal condition** (the register row): retire when Siril's compose accepts
  per-member weight maps or a per-member region mask — a mask is the crop
  without the coverage cost; the same condition the SWarp scaffolding carries.

Two facts measured only after the stage existed (both in the dead-end registry,
`docs/dead-ends/siril-behaviors.md`):

- **Siril re-serializes SIP at 15 significant digits on crop+save.** The
  solver's headers carry 17-digit reprs, so across the 27 copies 36 of 1107 SIP
  coefficient values changed — max 4.49e-15 relative, max pixel→world effect
  4.41e-13 deg; key sets and orders identical. The owner-approved cropT copies
  carry the same re-serialized values behind a KEYS-only check that never
  measured values. Verify's criterion (ruled at 17B): key sets + orders
  identical AND every coefficient within 1e-12 relative (a thousandfold over the
  re-serialization, a millionfold below what a re-solve or a wrong crop does),
  AND pixel→world agreement between the original's WCS and the copy's < 1e-9 deg
  at the copy's four corners + centre; positive controls in both directions
  (17-digit fixture coefficients MUST pass with max_rel_sip > 0 — measured
  2.46e-15; one coefficient altered by 1e-6 relative MUST fail both — measured
  rel 1.00e-06, sky 5.06e-08 deg). Real run: max_rel_sip 4.49e-15, 27/27.
- **A union's corners are EMPTY, so the corpus baseline measures inside the
  coverage rectangle.** `framing=max` leaves uncovered triangles around the
  rotated members' quad: three of the four per-set canvas-edge corner boxes
  read a Green median of 6.1e-5 against 6.0e-4 of covered sky — a coverage
  ratio, not flatness — and Siril prints `Sigma: -nan` for a constant layer,
  which the first seed's numeric-only regex dropped (`KeyError 'ch1'`). The
  corpus slot therefore REQUIRES a rectangle source to seed
  (`--coverage=<coverage_frame.py record>` or `--rect=`), places its five
  regions inside it — here [852, 436, 6816, 4578], floor 27.15 Green, grid
  40×26 — records the rectangle with its provenance, and REUSES it on compare
  (a recomputed rectangle would compare unlike regions). The rim staircase is
  outside the rectangle by construction and is not in the baseline's measures;
  `regional_stat.py` accepts nan sigma and refuses loudly on a constant layer.

Caution carried: the stage changes the canvas (8520×5668 against the pre-stage
8540×5677) and every rim-fed corner, so the per-set style corner rows would
move by the rim change, not by a regression — which is why the corpus slot's
rectangle rule exists, and why a re-seed follows the owner's acceptance, never
precedes it.

## Status

EMPIRICALLY TESTED end to end: the attribution (§2); the portion rule (§3,
cropT — owner-approved); the frame rule (a NULL on top of it — not encoded as a
gate; its score is reported with a re-test condition: a corpus whose soft night
is soft in its INTERIOR beyond the entry zone); the encoded stage (identity
27/27 and determinism 0/693 against cropT); the chain (`--portion-rule` →
the owner-approved candidate → the promoted canonical, 0 differing pixels,
guarded by the corpus baseline slot); the rows and the outer station (§3
rowmin, §6: the row-resolved crop a clean NULL; the +2400 blind spot bounded at
+0.008 px median). Open: the constant's placement (§4, a policy in a continuum —
the owner's); the depth measure's regime (§6). MEASURED and closed: weighting vs
exclusion (§6, a NULL); the top row (§6 — corpus-wide softening, the row-level
exclusion a TRADE not adopted); the repeat floor (zero, `repeat_floor.json`); the
stage on a PER-SET compose (a clean NULL — inside one set nothing replaces the
removed band, the gain sits inside the pair's own spread, the canvas loses 19 %
at max framing and 41 % of its width at the deliverable's min framing;
`datasets/aug14/set-04/qa_work/portion_perset.json`) — the stage is corpus-only.

## Graduation

- The chain: `run_corpus_combine.sh --portion-rule` runs `run_member_crop.sh`;
  the constants in `datasets/corpus/recipe.json`; the corpus slot
  `datasets/corpus/baseline.json` seeded; `docs/pipeline-wide-field-untracked.md`
  §6 (the stage) and §11 (the smear item, closed by it).
- BACKLOG: `compose-homography-smear` (member selection is the chain; only the
  reprojection route and the model questions stay open), `final-best-percent-pass`
  (the member-tier threshold form has shipped; the per-frame cross-session
  surface stays open), the register row for `run_member_crop.sh` +
  `member_profile.py` (in the chain; the condition unchanged).
- The dead-end registry: `docs/dead-ends/stacking-compose.md` (the attributed
  mechanism, now closed by the stage), `docs/dead-ends/siril-behaviors.md` (the
  15-digit SIP re-serialization; the constant-layer `Sigma: -nan` lines and the
  empty-corner rectangle rule), `docs/dead-ends/verification-traps.md` (the
  shape_at_sky trap).
