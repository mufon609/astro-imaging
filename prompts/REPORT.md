# Implementation report — what gets built next, and how it is judged

The rebuild-verification session's findings, distilled to the work they
demand. Companion to the prompt briefs in this directory; the audit session
checks each item against the acceptance stated here. Ordering within each
block is the priority.

## Prompts ready to run (in this directory)

- **[`OBJECT_TILT_MEASUREMENT_PROMPT.md`](OBJECT_TILT_MEASUREMENT_PROMPT.md)** —
  measure the `sky × V` object tilt catalogue-free, and retire the untracked
  3.11%/241σ figure. Runs on the 52 already-solved groups sub-stacks (4–5
  consecutive-time blocks per set, scale 17.008–17.028″/px), so no rebuild:
  match the same stars across blocks by each product's own WCS and fit flux
  against sensor position. Three required controls — interleaved halves for the
  floor (predicted tilt zero: mean sensor positions differ ~2 px against a
  ~774 px baseline), a planted ramp for discrimination, and the 12-set corpus
  prediction that the tilt tracks the flats' L/R dose **through a sign change**,
  with aug06/set-03 (dipole −0.0255) as the built-in null. Decision rule per the
  owner's ratification: small → route floor; significant → the fix's foundation,
  its own brief; too noisy → report the floor with numbers.

`COMMENT_SWEEP_PROMPT.md` is a **standing utility, not a queue item**: it does
not retire, and it is run on demand rather than scheduled here.

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

`8d370dd` `-transf=`/`-interp=` pinned at all 20 emissions + `check_registration_pins.sh` (per COMMAND, `--selftest`), proven no-behaviour-change by an all-nil recompose · `3072fd0` `verify_lens_card.py` wired into `lens_preflight --require-profile` unconditionally (11.1 s), fire-tested — and `install_lens_model.sh`'s idempotence test fixed, since it reported "already installed" on a DB whose vignetting was back · `4d70455` the solve refuses a solution contradicting its own hints (exit 9), `--central` corrected to fraction-of-frame at three sites; falsification fires, 0/69 false · `e7cb2be` the aircraft rejection CONFIRMED via Siril `-rejmaps` (the product-level A/B the item specified is under-powered by the group+compose dilution — recorded in `docs/dead-ends.md`) · `7d4946e` `TIER_B_HARDENING.md` + prompt retired.

**Full transcripts: [`../TIER_B_HARDENING.md`](../TIER_B_HARDENING.md).**

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

**Full transcript: [`../ITERATIVE_FLAT_VERDICT.md`](../ITERATIVE_FLAT_VERDICT.md).**

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

**Full transcripts: [`../ROUTE_KEY_GENERALITY.md`](../ROUTE_KEY_GENERALITY.md).**

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

**Full transcript: [`../COMMENT_HYGIENE.md`](../COMMENT_HYGIENE.md).**

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
  them the taxonomy's own teaching examples in `COMMENT_HYGIENE.md` and the
  sweep prompt — sanctioned, not misses.
- **Category 7**: the surviving `file:NNN` cites are six in
  `ROUTE_KEY_GENERALITY.md`, a session transcript rather than a live contract.
- **Regression check**: all five guards and all three selftests PASS after the
  edits, and `run_session_chain.sh sessions/aug09 --plan` walks five sets clean.

**One gap found in the standing prompt, fixed here.** Its `Scope` named the root
session reports neither IN nor OUT while its own detectors return live hits
there. They are now explicitly OUT as transcripts, with category 1 still
applying where a report is cited as current guidance — the sweep is non-retiring,
so an ambiguity in it recurs every run.
