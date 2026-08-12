# Implementation report — what gets built next, and how it is judged

The rebuild-verification session's findings, distilled to the work they
demand. Companion to the prompt briefs in this directory; the audit session
checks each item against the acceptance stated here. Ordering within each
block is the priority.

## Prompts ready to run (in this directory)

None. `COMMENT_SWEEP_PROMPT.md` is a **standing utility, not a queue item**: it
does not retire, and it is run on demand rather than scheduled here.

## Queued — needs prompts (medium; one session can take several)

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
(verified bit-identical), astrometric caveat on separation records, bare
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
