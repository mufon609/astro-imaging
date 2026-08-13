# Implementation report — what gets built next, and how it is judged

The rebuild-verification session's findings, distilled to the work they
demand. Companion to the prompt briefs in this directory; the audit session
checks each item against the acceptance stated here. Ordering within each
block is the priority.

## Prompts ready to run (in this directory)

- **[`L1_BUILD_PROMPT.md`](L1_BUILD_PROMPT.md)** — run both arms of the L1
  background-level experiment. The pre-registration
  (`datasets/aug06/experiments.jsonl`, `l1_background_level_perframe_vs_onstack`)
  IS the contract and the brief deliberately does not restate it; the brief adds
  the one thing it does not pin — the per-group `register -2pass` reference,
  which arm A can move by changing the calibrated lights, and which costs the
  experiment its PAIRING (different canvas → different `used` cells → the 5–16%
  paired resolving power collapses toward the 43–55% absolute). `--regdata` is
  verified ABSENT from the groups driver, so a 12-frame reference-stability pilot
  runs first and the pinning decision follows its numbers. Arm B before arm A:
  it is cheap, and its falsifier is a stop condition that would otherwise fire
  after the 13-member rebuild. A NULL is a live pre-registered outcome.

None. `COMMENT_SWEEP_PROMPT.md` is a **standing utility, not a queue item**: it
does not retire, and it is run on demand rather than scheduled here.

## Queued — needs prompts (medium; one session can take several)

- **`per-group-flat-at-the-combine`** — FIRST, because MEMORY makes it binding:
  a calibration change is evaluated against the COMBINE unit, and the member IS
  the cross-night combine unit. The per-set question is closed (composed tilt
  +0.055% ± 0.083%, 0.7σ — zero by construction, the set flat already being the
  mean of the group flats). What is open is the trade the change makes at the
  member: backgrounds 28–40× more consistent against 3.271%/4.335%
  member-to-member object-imprint disagreement where the shipped route has zero.
  The sign can invert at the combine — imprints that cancel within one set have
  no reason to cancel across nights whose skies differ. One knob, members from
  both arms; the half no instrument can settle goes to the owner.
- **Real-flats HANDLED path** — wire master-flat builds into the undistort
  route so staged real flats are USED, not just accurately refused (routing
  session shipped "named"; owner precedence: real flats WIN when present).
- **`cross-set-record-home`** — night/corpus SPCC records and baselines file
  under a borrowed member set (bitten twice this rebuild). Multi-set products
  write session-level records; combine products get a baseline home.
- **Guards runner** (`guards-and-ci`) — one command executes the five guards +
  their selftests (`check_registration_pins.sh` joined the family); RED on a deliberately broken mechanism; named in README as
  the pre-release step. (The unexecutable-guard half is already fixed.)
- **`frame-qa-order-dependent-scale`** — every `fwhm_arcsec` rides a ~5.6%
  scale artifact; re-derive against the stack-solve family (16.98–17.08″/px)
  and root-cause the probe arithmetic.
- **`--weight=noise` corpus arm** — motivated by a MEASURED 18–24% cross-night
  noise gap (aug09 haze: +0.16 mag extinction, 16,913 matched stars);
  pre-registered one-knob A/B vs the shipped nbstack corpus, judged on
  `snr_regions` + `shape_at_sky` + the owner's eyes.
- **Pooled master darks** (under `dark-optimization-fork`) — gated on the
  nights' masters measuring identical (these did: Δ0.1 ADU, noise within 1%);
  judged on the `noise_split.sh` structured term. Per-session stays default.
- **`session-level-mount`** — one decisive probe seeds sibling sets (five
  redundant probes measured on aug09).

## Large — one session each, own prompt when scheduled

- **`render-ladder` L1** (user-gated; the owner's declared focus) — the
  on-stack background-level ladder.
- **`intake-culling` transparency surface** — per-frame sky + rate-of-change +
  nstars (+ matched-flux anchor), visible constants; positive controls that
  MUST fire: aug06/set-03's 44-frame cloud block and july31's moonrise ramp.
  Fix the item's stale "per-frame background is NOT recorded" row
  (`records.jsonl` carries it for every frame).
- **`final-best-percent-pass`** — UNBLOCKED by this rebuild (a 12-set,
  three-night corpus on one target now exists).
- **`routing-generality`** — prompt already written (above); listed here
  because it is large.

## Watch-only (work exists only if they fire)

- Union-canvas solves: the corpus hinted solve failed on seam-contaminated
  detection and the blind fallback shipped a false solution — `--central` is
  the remedy and the Tier-B solve gate is the fix; night-level solves also
  run hintless of `--central` (aug06's logodds 156 was depressed).
- `findstar` detection-count jitter ~0.3% between identical runs (top-30
  medians stable to the third decimal) — an instrument fact to carry, not fix.
- aug09 ingest is local-hash verified only; no source-side hashes exist for
  that night. A fact about the record, not fixable after the fact.

## Landed during the per-group flat session — NULL at the product, a measured TRADE at the member

**Narrowing the flat window from 500 frames to 100 does not improve the per-set
product, and the rule the brief leaned on is not grounds for it.** july31/set-03,
one knob, 19 arms of 100 frames, registration pinned at BOTH levels, all four
controls run.

**The doctrinal argument does not transfer, and this is the finding.** A ratio of
two flats from one night, lens, focal and aperture cancels vignetting EXACTLY, so
what differs between a group flat and the set flat **is the sky term** — the
optical state does not change inside a 25-minute burst. **The discriminator is
what the flat DESCRIBES**, not whether the rule is "about optics" (an earlier
framing said that and it was wrong — the rule's own justification is a *sky*
divergence: a mid-set re-aim measured L-R 1.162 vs 1.032 while the top-bottom
optical term was identical at 1.143 vs 1.142). The rule fires when a flat
averages frames that saw **different** skies, so it describes a blend **no frame
saw**. Under one continuous pointing there is no blend — the set flat **is** the
mean of the sky its own frames saw, which is what the rule asks for. So the rule
is already satisfied at the set level, **both arms imprint a sky, neither is less
contaminated**, and only the **uniformity** of that imprint across members
changes. That is why the composed difference is zero **by construction** rather
than by luck.

**The product does not move, and that was recorded before it was measured.** The
per-set flat IS the groups' average — the mean of the five departures is **0.82%
(x) and 0.76% (y) of a typical departure** — so a plain-mean compose cancels
them. Delivered: the composed object L/R tilt moves **+0.055% ± 0.083%, 0.7σ**
(Siril `psf`, 1217 stars), the composed pixel field 7–25% of the mean member
magnitude. Cancellation is 75–94%, not the >99% the sensor-frame arithmetic
gives, because the compose is a SKY-frame mean of patterns that drifted ~453 px.

**At member level the correction is real and 1:1** — planted-corrected transfer
**1.007 (x) / 1.077 (y)** — moving each member's object tilt **0.36–2.13% in x
(4.3–21.3σ)** and up to **3.42% in y**. It **buys** member backgrounds **28–40×**
more consistent (the registry's SELF-FULFILLING direction — the mechanism's size,
not evidence of better calibration) and **costs 3.271% (x) / 4.335% (y) of
member-to-member object-imprint disagreement where the shipped route has exactly
zero**. No instrument here can say which side is closer to truth, so by the
evidence gate it is a trade the DATA CANNOT SETTLE — **the owner decides**.

**Controls.** FLOOR at the group's own depth, built not inherited: **0.0546%**
corner spread, every effect **20–62×** it. IDENTITY: **0 differing pixels** on all
five groups and the compose, with the same comparison firing at **99.9995–
99.9998%** on the one-knob pair, so the zero is discriminating rather than
vacuous. PLANTED: **0.9926** recovery against the card over the delivered canvas.
UNIFORM: every dipole **+0.0000** and star differential **+0.000%** — level cannot
reach the product, only shape.

**Predictions: 5 held, 2 split, 2 falsified.** The inherited anchor **reproduces
to 0.02%** on post-reset flats (|g1 vs g5| predicted 1.3085 %/1000px, measured
+1.3088). Falsified: the "smallest departure at the middle group" clause (the
zero-crossing sits between g2 and g3, 4.7 floors apart), and the enabling-condition
worry — every group flat measures **ZERO** findstar specks against the set flat's
**ONE**, despite averaging 90.9 px of celestial motion against 453.3 px.

**Open, and it is the right next question:** the member is the cross-night COMBINE
unit, so a combine-level A/B is where the member-level trade could pay or cost.
Not run here.

**Deferred, gate-blocked not forgotten:** the owner's eyes on full-frame finals.
`render_tier.sh` exits 7 without a ratified `render` block and july31/set-03 has
none (`BACKLOG:render-ladder`). Both arms' linear stacks and all three composes
are preserved and tagged on the FITS (`DIAGARM`/`CALXSET`/`STACKNRM`/`REGPIN`) in
`sessions/july31/work/pergroup/`, deliberately NOT in `web/results/`.

**Two shipped fixes fell out of it.** `grid_ramp.py` — the registry's named
candidate gradient measure, which had no script, so the measurement behind a
registered finding could not be re-run; tool search PROBED, reports without
gating, selftest falsifies its own mechanism. And Siril prints `Sigma: -nan` on a
zero-variance crop while the shipped STAT regex carried an `n` but no `a`, so the
UNIFORM control — the one arm that produces uniform crops — could not be measured
at all; fixed, provably neutral (sigma is parsed and discarded), second copy
removed.

**Numbers:** `datasets/july31/pergroup_flat_prediction.json` (committed before the
first flat), `datasets/july31/experiments.jsonl`
(`pergroup_flat_window_july31_set03`), the 50 records in
`datasets/july31/set-03/pergroup_work/`, `docs/dead-ends.md`.

## Landed during the flat-differential session — WIN with controls

**The flat's dose difference reaches the delivered object essentially 1:1.** Two
flats of the same optical state and different sky dose (aug09 set-01 vs set-05,
Δedge dipole 0.2827 — the corpus maximum within a night) applied to the SAME 125
set-05 lights, one knob. **Delivered: −22.477 ± 0.077% object-flux tilt (r = 10 px,
914 stars, Siril `psf` against its own local annulus; −22.450 ± 0.082% at r = 16)
and edge dipole_x −0.2356 on the pixel-ratio field (Siril `fdiv` + `stat`).**

**The apples-to-apples comparison needs no model.** The flats' OWN ratio field,
cropped to the delivered canvas and measured with the same shipped instrument,
reads −0.2383 (edge) and −0.2010 (corner) against the delivered −0.2356 and
−0.2021 — **98.9% and 100.6%**, tracking point-by-point along nine midline boxes
to ≤0.008. A planted ramp of known dipole +0.1583 over that same window recovers
at **97.7%**, so the real number corrected by the control's own systematic is
**101.2%: no measurable attenuation.**

**Both blockers that killed the absolute tilt die structurally, and the selftest
proves it on the SAME fixture.** `M_i` cancels identically (the same star in the
same photons), so nothing per-star is fitted and the lever becomes the spread of
star positions: **1603 px against the absolute measurement's 29.1 px median**;
identical frames carry identical extinction and skyglow, so the sensor-fixed
atmosphere cancels in the subtraction. On `object_tilt --selftest` 4a's
pure-translation panel, one screen: **absolute −0.0464 ± 0.0001 with the lever at
0.00 px, differential +0.0999 ± 0.0001 with a 1548 px lever.**

**The floor is EXACTLY ZERO** — both instruments, all three channels, both
apertures. The identity rebuild is bit-identical; the non-vacuous version (a
uniform 1.05 card) changes **74.10% of the pixels** and still moves every dipole
by 0.0000. That control also measured the mechanism: **Siril `calibrate`
normalizes the flat by its own level, so a flat's LEVEL cannot reach the product
— only its SHAPE can.** Discrimination is unbounded (planted movement 0.1547
against 0.0000), where the object-tilt instrument managed 0.20×.

**The shipped normalization absorbs 0.3%** of the object's difference (−22.477%
at `-nonorm` vs −22.550% at `-norm=addscale -output_norm`), so nothing is hiding
the defect. The same pair moves the BACKGROUND dipole **+48.6%** and splits the
channels — a pedestal artefact, not imprint (psf's local annulus removes an
additive term, regional medians cannot; measured: `An/A` is a uniform 2.02× while
`Bn/B` runs 1.859 left to 1.667 right). **Read the pixel field on `-nonorm` arms
only.**

**The two instruments differ by 1.34% and it is attributed, not averaged**: the
delivered field's x-slope varies with y (max departure from the end-to-end line
0.0204 along the midline), so a corner-anchored dipole, a plane fit over stars and
a midline profile are three summaries of one field — on the exactly-linear planted
card the same two instruments agree to 0.32%.

**The brief's own load-bearing premise was false and had to be fixed first.** It
asserted the arms are pixel-aligned because they share a chain; `register -2pass`
re-chooses its reference from image quality and the CALIBRATION changes that
choice — measured, one knob: reference image 1 / canvas 4896×3616 against image 2
/ 4887×3641. `run_undistort_pipeline.sh` gained `--regdata=` (every arm is handed
the first arm's registration data) and `--nonorm`, both default-off; `CALFLAT`
also stamped the set's RECORDED flat rather than the one that RAN, now corrected
with `CALXSET` marking a cross-set calibration on the product itself.

**SCOPE, stated before the result and unchanged by it:** this is the DIFFERENCE
of two imprints. It gives the delivered sensitivity to a KNOWN dose difference —
the number a corrective needs — and NOT the absolute tilt, which needs the flats'
COMMON sky content and is still unmeasured. It does not resurrect the 3.11%/241σ
figure (UNVERIFIED), and the T/B attribution caveat stands.

**Deferred, gate-blocked not forgotten:** the with/without pair on FINALS.
`render_tier.sh` exits 7 without a ratified `render` block and aug09/set-05 has
none (`BACKLOG:render-ladder`) — re-verified. Both arms' linear stacks are
preserved and tagged (`DIAGARM`/`CALXSET`/`STACKNRM`/`REGPIN` on the FITS),
including the production-normalization pair, which is the one to judge.

**Numbers:** `datasets/aug09/flatdiff_prediction.json` (committed before the
arms), `datasets/aug09/set-05/flatdiff_work/flat_differential.json` + the five
pair records, `docs/dead-ends.md`, `datasets/aug09/experiments.jsonl`.

## Landed during the object-tilt session — NULL with controls

The catalogue-free `sky × V` object-tilt measurement was BUILT, run over all 12
sets, and is now a registered **DEAD END**; the untracked 3.11%/241σ figure is
retired as **UNVERIFIED** at all 13 code and doc sites and in the 13
`readiness.json` records (via their generator, which was the real site).

**Two independent blockers, either fatal.** (1) A linear sensor-fixed mode is
EXACTLY absorbed by the per-star and per-block nuisances under a pure
translation, so the 503–1220 px of drift carries none of it; the lever is the
FIELD ROTATION, 0.69–3.76°/set, leaving a **29.1 px median lever on a 5769 px
frame — a ~200× extrapolation**. (2) For a FIXED camera every sensor position
maps to a fixed altitude, so atmospheric extinction and skyglow across this
27° field are sensor-fixed too and airmass-shaped like the flat's own sky term;
the fit sees their SUM, and both external anchors are closed (a catalogue is
structurally impossible at 17″/px on trailed stars, a real flat IS the fix).

**The instrument is sound and the controls prove it**: a Siril `imul` ramp of
edge ratio 1.2222 recovers at **1.24×** (0.95× on the best-levered block pair)
and a uniform card moves every number by **exactly 0.00** — but its
**discrimination against the floor is 0.20×** (planted 9.85 points against a
49.08-point floor), where the iterative-flat NULL met 48–62×. **The floor is 49
percentage points** — aug09/set-01 rebuilt as interleaved halves has a predicted
tilt of exactly zero and measures **+49.08 ± 4.97% (r = 10 px) / +50.82 ± 5.65%
(r = 16 px), 3086 stars, 11.8σ**. `--selftest`
falsifies the mechanism in process — a pure-translation panel returns a planted
+0.100 mag as **−0.046 ± 0.0001** with the lever at 0.00 px, so a degenerate fit
reads confidently WRONG; read the lever, never the sigma.

**The pre-registered corpus prediction failed 4 of 5**: every set exceeds its
own flat's dose by **1.4–86× (median 8.1×)**, and aug06/set-03 — pre-registered
as the built-in null — measures **+223 ± 28%** against a predicted +2.6%.
ρ = +0.68 (p 0.015) is a real ordering but cannot confirm at those magnitudes,
since the flat's L/R sweeps with the night's sky state and so does the
confounder. Median within-set block-pair spread **529 points**, where one
sensor-fixed field must give one answer.

**By-product worth its own item:** the per-block fit measures a real within-set
sensor-fixed gradient DRIFT of **0.040–0.425 mag (median 0.149), monotone in
block order in 10 of 12 sets** — a transparency-drift measure
`BACKLOG:intake-culling` does not have.

**Numbers:** `datasets/aug09/corpus_object_tilt.json`,
`datasets/aug09/tilt_corpus_prediction.json` (committed before the corpus ran),
the 12 per-set `tilt_work/object_tilt.json`, `docs/dead-ends.md`, and the three
nights' `experiments.jsonl`.

## Landed during the verification session (audit's done-ledger)

`dd7a13d` guard made executable + `shape_at_sky.py` acceptance instrument
(calibrated to the recorded union A/B to the third decimal) · `a1dc91b`
member-provenance CALSET truncation fix + header repairs · `3f1980d` corpus
glob can never ingest set-00 · `1791bb4` master-dark rejection recorded as the
vendor's own command (item closed) · `82f67f8` BACKLOG prune (closed items
removed entirely) · `f43e482` `snr_regions` triple fix (negative-value regex,
cross-session basename collision, flatpak-private-/tmp workdir) · `739c626`
Tier A: set-00 skipped by the session chain, per-set compose reference pinned
(**verified on aug06/set-01 ONLY — this ledger previously said "verified
bit-identical" unqualified, which widened the commit's own scope. The L1 session
measured the pin MOVING the canvas on aug06 set-02 and set-03; set-01 was
bit-identical because its unpinned auto-pick already landed on member 1, which is
what the pin selects. The pin is right; the recorded scope was not**),
astrometric caveat on separation records, bare
`--selftest` refuses instead of masquerading as help · `fa40ef1`/`28b91cf`
the prompt briefs.

## Landed during the Tier-B hardening session

`8d370dd` `-transf=`/`-interp=` pinned at all 20 emissions + `check_registration_pins.sh` (per COMMAND, `--selftest`), proven no-behaviour-change by an all-nil recompose · `3072fd0` `verify_lens_card.py` wired into `lens_preflight --require-profile` unconditionally (11.1 s), fire-tested — and `install_lens_model.sh`'s idempotence test fixed, since it reported "already installed" on a DB whose vignetting was back · `4d70455` the solve refuses a solution contradicting its own hints (exit 9), `--central` corrected to fraction-of-frame at three sites; falsification fires, 0/69 false · `e7cb2be` the aircraft rejection CONFIRMED via Siril `-rejmaps` (the product-level A/B the item specified is under-powered by the group+compose dilution — recorded in `docs/dead-ends.md`) · `7d4946e` the Tier-B report + its prompt retired.

**Numbers: BACKLOG's removal-conditions rows for the solve gate and the lens-card wiring; the aircraft entry in `docs/dead-ends.md`.**

## Landed during the iterative-flat session

The domain-corrected iterative sky flat is **NULL, structurally**: the iteration
reconstructs whichever flat it is handed (`F1 = F_roundtrip`), because dividing
by `F0` is what removes the gradient from the sky and multiplying back restores
it. It repaired `--desky`'s domain error and still could not work, so "run the
operator in the correct domain" is exhausted as an angle. Positive controls move
the same code 81.7% (fixture, round-trip flat = the known true `V`) and 93.4%
(real data, handed another set's flat — it returned THAT set's flat from set-05's
frames) where the scheme moves it 1.7% / 1.2%; a 48–62× discrimination, so the
null is a measurement and not a check that cannot fail. No builder flag was
added and no removal-conditions row created — a flag selecting an inert
mechanism is dead code and there is no divergence to retire; `build_sky_flat.sh`
is byte-unchanged.

What the session leaves behind is worth more than the arm: `flat_odd_component.py`
— the odd-component instrument `BACKLOG:calibration-evidence` recorded as MISSING
— and the decomposition it produced. The left-right term is SKY (monotonic within
all three nights; edge dipole sweeping +0.436 → 0 → −0.385 across the corpus,
impossible for a sensor-fixed term), but the brief's premise that the stable base
is "a real instrumental odd component" is **refuted**: T/B sits above 1 on july31
and drifts +6.7% through that night while sitting below 1 on aug06/aug09, so
neither axis isolates the instrument and the constant-within-a-night part stays
unattributed. Four Siril behaviours pinned by probe, two of which silently
corrupt data — `offset` clips at 0 in 32-bit against its own documentation, and
`stat` excludes zeros, which compound into damage that reads back as clean
numbers.

**Numbers: `docs/dead-ends.md` (the iterative-flat entry) + `datasets/aug09/experiments.jsonl`.**

## Landed during the routing-generality session

The route key is one derivation (`scripts/lib/route.py`) on the sky excursion as
a fraction of the field, replacing six private copies of a `fov`-width test that
also inverted the physics — a fixed mount sweeps 0.2507 × cos(dec) °/min at any
focal length, so a narrow field crosses more of itself per minute than a wide
one, and the width floor excluded exactly the sets with the most drift. Keyed on
an ANGLE, not `drift_px`: camera raws solve on the half-res green plane, so the
recorded px figures read 2.078–2.137× the sensor's scale and would mean two
different things on two rigs. Floor 0.05 is EVIDENCE (the smallest excursion the
term is measured present at), not a knee — none has ever been measured. All 12
real sets route identically; the fire test moves five consumers together; the
200 mm and mono/tracked fixtures route through the live chain; both refusals name
their class with the resolving step. `routing-generality` removed from BACKLOG.

**Numbers: `scripts/lib/route.py` (+ its `--selftest`) and BACKLOG's removal-conditions row for the floor.**

## Landed during the comment-hygiene session

The removal taxonomy is derived from all 638 commits, not assumed: seven
categories over 1,403 removed comment lines and 15,397 removed record lines
(in-place edits only — 52 wholesale `.md` retirements excluded as a different
mechanism). The costly category is **drift**, prose asserting what the code
contradicts, and it is the only one that recurred — six instances of the ICC
leg rule alone, one of which pointed a future session at `docs/dead-ends.md`
trap 3 as "the cheapest available win". One anticipated category is **refuted**:
victory language has never once been removed, and its obvious detector matches
only domain vocabulary (*fixed mount*, *matched-flat*).

The policy audit found the date rule **false as written**. "Doctrine
ratification stamps are the one exception" would have a literal sweep delete
`BACKLOG.md`'s entire re-verify column, `CLAUDE.md`'s own rig stamp, and the
dated Context line `docs/README.md` requires of every deep-dive. The rule now
states the principle that covers all three: a date is allowed where the date IS
the information — what supersedes what, or how stale a claim is.

Shipped: [`COMMENT_SWEEP_PROMPT.md`](COMMENT_SWEEP_PROMPT.md) (non-retiring),
the `CLAUDE.md` rule revision, `COMMENT_HYGIENE_PROMPT.md` retired. No sweep was
run — that is the standing prompt's job, on the owner's schedule.

**The taxonomy, detectors and policy live in [`COMMENT_SWEEP_PROMPT.md`](COMMENT_SWEEP_PROMPT.md).**

## The standing sweep's first run — AUDITED PASS

`bd1c675`, audited by re-execution rather than on the report's assertion.

- **Category 1 (drift) CONFIRMED live.** `check_bitdepth.sh` names four
  exemptions and prints "the 4 documented instrument exemptions"; `README.md`
  said three and `BACKLOG.md`'s register row said three while omitting
  `run_lunar_pipeline.sh` entirely — prose contradicting the guard that enforces
  it. Both corrected, and the guard still exits 0. This is the finding that
  justifies the run.
- **Category 6 CONFIRMED.** `grep -cE '^## \`?[0-9]' BACKLOG.md` returns **0**,
  so all 30 numbered refs did point at nothing. Three survive tree-wide, all of
  them the taxonomy's own teaching examples in the sweep prompt — sanctioned,
  not misses.
- **Category 7**: the surviving `file:NNN` cites are six in
  the route-key session's transcript rather than a live contract (retired since).
- **Regression check**: all five guards and all three selftests PASS after the
  edits, and `run_session_chain.sh sessions/aug09 --plan` walks five sets clean.

**One gap found in the standing prompt, fixed here.** Its `Scope` named the root
session reports neither IN nor OUT while its own detectors return live hits
there. They are now explicitly OUT as transcripts, with category 1 still
applying where a report is cited as current guidance — the sweep is non-retiring,
so an ambiguity in it recurs every run.

## Landed during the L1 research session — the gate now exists, and two beliefs resolved against themselves

The brief's premise held: L1's adoption gate was unresolved-starlight
preservation and nothing in the tree measured it. It does now, and building it
changed what the build session should expect.

**The instrument** — `scripts/qa/starlight_preservation.py`, an ALLOWED
gap-filler: Siril `boxselect`+`stat` measures every per-cell floor, the ESA Gaia
archive's TAP service aggregates the catalogue server-side, and in-house code
holds only the lattice, the WCS projection and the fits. It gates nothing and
always exits 0. The tool search behind the removal condition was run rather than
reasoned — Siril `stat`/`bg`/`bgnoise` measure the image only and `conesearch`
is not even usable at this field size (20.6° radius at G≤17 against TAPVizieR,
killed at 600 s with no output); `source-extractor -CHECKIMAGE_TYPE BACKGROUND`
writes a background map in 1.7 s but compares it to nothing; GraXpert `-bg`
writes a model image; ASTAP reports HFD and star rows. Two probes replaced
assumptions: `boxselect`+`stat` is identical to `crop`+`stat` to every printed
digit in ONE load, and `jsonmetadata -stats_from_loaded` silently ignores a
selection.

**The selftest earned its place on its first run.** `boxselect` counts y from the
TOP; the mirrored lattice still recovered 54% of a planted relation at R² 0.30 —
a half-right number a fixture-free instrument would have shipped. Fixed, the
positive control reads 299.14 against 300.00 planted at R² 0.99993, an orthogonal
predictor returns R² 0.00017, Siril `subsky 2` collapses the planted relation to
26.9% and the pristine copy re-reads 299.14 to 1e-6.

**Degree 1 vs 2 is MEASURED, and the answer needed no image.** `subsky d` removes
a degree-d surface, so the most it can take is the fraction of the Gaia
predictor's own spatial variance a degree-d surface can represent: over
aug06/set-01, **plane 10.0%, quadratic 36.2%, cubic 43.5%** (140-cell external
lattice, predictor spanning 174% of its mean). Degree 2 costs a third at worst,
not erasure — the registry's "seqsubsky 2 erases it" was mechanism, and the
bound is smaller than it implied. No confound can move this number.

**The image-side version of that test cannot settle it on today's products, and
why is a second result.** One knob, on-stack `subsky 1` vs `2`, paired on the
same cells: the Gaia slope RISES — retained 1.232/1.274/1.237 at degree 1 and
1.517/1.846/1.604 at degree 2 (SE 0.056–0.155). The open `sky × V` residual is
anti-correlated with the starlight and biases the raw slope low, so
confound-removed and starlight-removed land in one statistic with opposite signs.
Sizes fall out: predicted starlight spans 0.71–0.86 ADU across the frame against
a measured floor span of 2.50–4.00 ADU, so **roughly a fifth to a third of the
frame-scale floor variation is starlight and the rest is not.** A clean
structural check comes free — residualise both arms by a quadratic and the
degree-2 arm retains 1.000/1.010/1.018, i.e. `subsky` moves only its own
polynomial subspace.

**"Visible rings" is not an eye observation.** It entered as *"fails the rings
gate"* and commit `870bf7d` rewrote it to *"visible rings"* in the same diff that
deleted the gate — `bg_qa.ring_amp`, the detrended peak-to-valley of a 40-bin
RADIAL profile of the render. That is the reference FORBIDDEN class and the same
radial-binning family as trap 3. Stack-level BGE is UNJUDGED; if the on-stack arm
loses, that is discovered, not predicted.

**Standards-first: our default already matches the vendors.** Siril's own docs
recommend per-frame degree 1 (*"in a single image, the background gradient is
much simpler and generally follows a simple linear (degree 1) function"*), and
both Siril and PixInsight put background extraction before colour calibration —
the order this chain runs. What is NOT vendor doctrine anywhere is the
starlight-preservation argument for degree 1; Siril's stated reason is gradient
complexity.

**Numbers: `docs/dead-ends.md` (Background), the register row in `BACKLOG.md`,
and `datasets/aug06/set-01/starlight_work/*.json`.**

### What the build session inherits — the unknowns, stated

1. **The two arms may not be separable on this criterion.** An on-stack plane is
   bounded at 10.0% by the catalogue, and the paired instrument resolves 5–16%.
   The arms can only differ materially if the per-frame step reaches structure a
   single sky-plane cannot — which is exactly the pre-registered directional
   prediction (a sum of planes fitted in SENSOR coordinates to frames drifting
   across the sky is not one sky-plane). If that mechanism is weak, expect a
   NULL, and the level choice will have to be made on other grounds.
2. **Degree 2 is NOT a third arm.** Two arms, degree held at 1, dither held off.
   The degree question is answered by the bound above and does not need a build.
3. **`--gsplit` is inherited, not measured here.** G = 11.0 at 50% completeness
   comes from the archived july23 record. Every magnitude bin is kept, so a
   re-measured limit re-splits the record offline without re-querying.
4. **Expect `retained > 1` and do not read it as starlight being added** — see
   the confound above. The catalogue bound is the number no confound touches.
5. **`member_separation.py --selftest` cannot run on today's tree** — no complete
   registered `s_*.fit` sequence survived the from-raws rebuild. One
   `register -2pass` on any groups dir restores it. Pre-existing, unrelated to
   this session's changes, and now stated in its register row.

The pre-registration covering both arms is
`datasets/aug06/experiments.jsonl`, `l1_background_level_perframe_vs_onstack`,
with a falsifier for each arm and every path re-verified against disk.
