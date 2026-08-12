# Implementation report — what gets built next, and how it is judged

The rebuild-verification session's findings, distilled to the work they
demand. Companion to the prompt briefs in this directory; the audit session
checks each item against the acceptance stated here. Ordering within each
block is the priority.

## Prompts ready to run (in this directory)

| prompt | items | acceptance shape |
|---|---|---|
| `ROUTING_GENERALITY_PROMPT.md` | single-source the route key on measured `drift_px` (six `fov >= 10` sites today); the two refusals name their class | one grep-clean source; all 12 existing sets route IDENTICALLY via `--plan`; a 200 mm fixture routes instead of exiting 5; fire test shows all consumers move together |
| `COMMENT_HYGIENE_PROMPT.md` | mine git history for the comment-removal taxonomy; emit the standing `COMMENT_SWEEP_PROMPT.md`; audit the policy text | categories derived with counts + verbatim examples; sweep prompt carries detectors + the revise-never-drop safety rule; policy left short, single-homed, uncontradictory |

## Queued — needs prompts (medium; one session can take several)

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
