# Rebuild verification — the astrometric compose holds from raws

The brief (`VERIFY_REBUILD_PROMPT.md`, retired with this report): rebuild the
corpus from raws with the current chain and settle whether the astrometric
compose fix survives a clean run. **It does — at every level, by instrument
and by eye.**

## What was rebuilt

Every product from `sessions/<night>/<set>/` raws by the shipped chain:
12 real sets (july31 01–04, aug06 01–03, aug09 01–05; **set-00 is the owner's
spare-frames bucket, never a light set** — reclassified mid-rebuild, skipped
everywhere, and structurally excluded from the corpus glob), three night
combines, one 52-member corpus union. 5,723 real-set frames; 58 auto-culled
by the standing ratified policy (1.0%, every one tool-flagged, every one
recorded in its set's `recipe.json`); corpus `STACKCNT=5665` = exactly the
arithmetic. Owner's "all images, not culled" resolved as: no set excluded, no
selection beyond the standing auto-cull. The per-set compose stays star-pair
(its own A/B measured a wash; `REGMODEL=starpair` stated on those products);
every combine above is astrometric by construction and guarded both sides.

## Acceptance protocol

`scripts/qa/shape_at_sky.py` — Siril `findstar` (`reset -roundness=0.10
-relax=on -maxR=1.0`), 800 px boxes placed by each product's OWN solved WCS
and verified by the tool's own per-star RA/Dec; FWHM = median (FWHMx+FWHMy)/2,
roundness = median min/max, over the 30 brightest; n on every number.
Calibrated against the kept old union before use: reproduced its recorded
4.383/0.458 (defect) and 2.448/0.968 (control) to the third decimal.

## Results — FWHM px / roundness / n

| product | defect RA 294.86 | mid1 RA 301.58 | mid2 RA 308.20 | control RA 314.72 |
|---|---|---|---|---|
| OLD union (star-pair, 28 m) | 4.383 / 0.458 / 1064 | 2.980 / 0.736 / 1210 | 2.498 / 0.938 / 1199 | 2.448 / 0.968 / 1102 |
| july31 night (17 m) | 2.660 / **0.985** / 872 | 2.672 / 0.927 / 1065 | 2.545 / 0.927 / 1135 | 2.440 / 0.957 / 1042 |
| aug06 night (13 m) | 2.653 / **0.948** / 1085 | 2.542 / 0.923 / 1198 | 2.410 / 0.964 / 1160 | 2.443 / 0.957 / 1029 |
| aug09 night (22 m) | 2.700 / **0.989** / 1070 | 2.630 / 0.925 / 1192 | 2.520 / 0.948 / 1185 | 2.502 / 0.988 / 1089 |
| **CORPUS union (52 m)** | **2.685 / 0.980 / 1082** | 2.623 / 0.917 / 1188 | 2.498 / 0.948 / 1175 | 2.465 / 0.976 / 1121 |

The defect position reads AT the clean band on every combined product (corpus
0.980 vs control 0.976), FWHM down 1.70 px from the old union, star counts
within 2% (not survivorship), and the corpus reproduces the prior session's
one-knob A/B arm (2.678/0.974) from a clean rebuild: **2.685/0.980**. Same-
night direct comparison: aug06's own 3-set union read 0.530 at the defect
under star-pair-era composition; its rebuild reads 0.948. Every combined
product carries `REGMODEL=astrometric / REGUNDIS=T` (checked on the `_spcc`
derivatives too), full `CALSETS` identity, `NDISTMOD=1`.

1:1 inspection of all four combined renders at the defect and control
positions: round point stars, no directional smear, no doubling; the faint
drift-aligned background weave is the registered walking-noise class (open,
acquisition-side), not the compose defect. Owner's eyes: july31 night PASSED
("sharp from corner to corner"); the corpus render PASSED ("the final render
passes") — `BACKLOG:astrometric-compose` is closed and removed.

## The corpus solve incident (the one fight of the endgame)

The union canvas (8510×5475, 52 member footprints) defeated the plate solve:
the hinted attempt failed on contaminated detection and the blind fallback
SHIPPED a false solution — RA 6.0 Dec −65.1, scale 12.96″/px, logodds 22
against a healthy family of 100–570 — which siril SPCC then consumed,
producing plausible-looking K factors (G 0.592, outside the 0.649–0.682
family) instead of failing. Caught by the odds/position watch; all bogus
products deleted. Two recovery traps measured on the way: `--central` is a
HALF-WIDTH fraction so `=0.5` restricts nothing, and `--max-stars=1500`
explodes the quad search on a 46 Mpx canvas (64 min CPU, no result). The
route that worked, and the durable pattern for union canvases: **crop the
central region to scratch, solve it like a member (logodds 130, 17.06″/px),
shift CRPIX back by the exact crop offset** — header-only, pixels untouched,
validated by the instrument's own per-star verification at all four
positions including far outside the solved crop. SPCC on the correct WCS:
K_G 0.669, in family. The solve sanity gate (refuse a blind result that
contradicts present hints) is queued with this incident as its falsification
case — `prompts/TIER_B_HARDENING_PROMPT.md`.

## Audit findings and hardening (all landed, with commits)

1. `check_stack_rejection.sh` was mode 664 — unexecutable guard; fixed, all
   guards + selftests green (`dd7a13d`).
2. Member provenance still routed through siril `update_key` → `CALSET`
   truncated at the slash on every member; fixed to the FITS-library path,
   17 built members + night product repaired header-only (`a1dc91b`).
   The compose-level fix (`ebbce14`) had been half-landed.
3. Corpus glob hardened against set-00 (`3f1980d`); session chain skips
   set-00 (`739c626`).
4. Per-set compose reference pinned (`setref` member 1): the auto-pick made
   absolute level a rebuild lottery — measured as a false −36% baseline
   regression on aug06/set-01, root-caused to `-norm=addscale` anchoring on
   the reference + `-output_norm` re-zeroing at the darkest pixel; pin
   verified bit-identical on the shipped product (`739c626`). aug06/set-01's
   baseline re-seeded with the mechanism in its note (owner-ratified).
5. `member_separation` on an astrometric compose measures H-only separations
   INCLUDING each member's SIP (~8–10 px) — records/stamps now carry the
   caveat, and a bare `--selftest` refuses instead of exiting into the
   docstring (it had read as a pass twice); real falsification now verified
   on live members (`739c626`).
6. `snr_regions.py` triple fix on first cross-night use: negative-value
   regex, cross-session basename collision, flatpak-private-/tmp workdir
   (`f43e482`).
7. Master-dark rejection closed by research: the template is the vendor's
   own command verbatim (10/10 bundled scripts); reason recorded on the
   command, BACKLOG item removed (`1791bb4`).
8. BACKLOG pruned of closed items and struck rows; `optical-state-models`
   removed with its two open bullets salvaged into
   `compose-homography-smear` (`82f67f8`).
9. New standing instrument: `shape_at_sky.py` (registered in the
   removal-conditions table; its self-verification caught the siril crop
   y-origin trap on first use).

## Measured side-findings (owner questions during the rebuild)

- **aug09 vs aug06 quality**: real and atmospheric — 16,913 matched stars
  read +0.160 mag fainter on aug09 (uniform across brightness), sky +15–18%,
  stack contrast-to-noise 18–24% worse; moon ELIMINATED (aug09 had the
  darker moon), thermal ELIMINATED (masters identical), bad frames
  ELIMINATED (tight distributions). Thin haze; motivates the queued
  `--weight=noise` corpus arm.
- **Within-night variation**: aug09 is a uniform veil (best/worst star ratio
  1.14× — nothing to cull); aug06 clear with one already-culled cloud block;
  july31 (the moonlit night) varies most — the future intake-culling
  transparency surface's positive controls are named from this data.

## State handed forward

Fresh baselines seeded for aug09's five sets; july31/aug06 sets passed their
existing guards (set-01 re-seeded as above). The old union and its surfaces
are deleted (measured, superseded, owner-directed). Night/corpus combines
have no baseline home yet (`cross-set-record-home`, queued). The
implementation queue with acceptance criteria: `prompts/REPORT.md`; ready
briefs: `prompts/TIER_B_HARDENING_PROMPT.md`,
`prompts/ROUTING_GENERALITY_PROMPT.md`, `prompts/COMMENT_HYGIENE_PROMPT.md`.
