# datasets/corpus/ — cross-session records (the index)

Records whose subject spans sessions: corpus-level builds, cross-night A/B
engagements, and audits over the whole member population.
`datasets/<session>/<set>/` is the wrong shape for these by construction
(`corpus4_build_record.json` `_home`), and `web/results/` is gitignored.

**Retention (the convention — `datasets/README.md`):** the tracked RECORD of a
measurement is its JSON — instrument, inputs, exact command, the tool's own
numbers. Bulk tool output (findstar `.lst` star lists) is EVIDENCE and leaves
the tree when its route closes; recover any pruned file with
`git show <adding-commit>:<path>` using the resolvers below.

## Records

| record | instrument | question / route status |
|---|---|---|
| `corpus4_build_record.json` | run_corpus_combine parameters + product headers | what the four-night corpus product was built with (the product itself is gitignored) — KEPT route |
| `solve_stack_july31+aug06+aug09+aug14_outnorm_presolvefix.json`, `spcc_set-0b_july31+aug06+aug09+aug14_outnorm_presolvefix.json` (renamed from `…_full.json` 2026-08-30; the `set-0b` in the SPCC name is the sort-order defect's own trace, kept) | `solve_field.py` / Siril SPCC | NOT the canonical's: the finish records of the four-night product as it stood on 2026-08-19 — its FIRST `_full` build (with `-output_norm`, before the member-solve fix, generic SPCC response), filed under aug14/set-0b by the sort-order defect and relocated here (179c1d0): solve RA 309.858 / Dec +41.327 / 16.952 arcsec/px / logodds 507; SPCC K 1.000/0.669/0.899 on a 582,612,480-byte `_wcs`. That product was replaced in place by the member-solve-fix rebuild (2026-08-26; `_full` re-finished at 309.761 / +41.296 / 17.006 / logodds 105 on 582,917,760 bytes — the file the zero-point campaign moved aside as `_outnorm` and later disposed); its pixels are gone, the records kept — each carries an `_identity` block with the numbers. The CANONICAL's finish records live under `datasets/aug09/set-02/qa_work/` (BACKLOG:`cross-set-record-home`) |
| `solve_audit_corpus.json` | `scripts/qa/member_solve_audit.py` over all 77 members | the wrong-scale member-solve class (ledger `corpus4_member_solve_fix`; guard's register row in BACKLOG:`removal-conditions`) — fix KEPT |
| `corpus_sweep_{old,new}.json` | Siril findstar, 44+39 WCS-placed 700 px boxes | rebuild verification, superseded vs repaired corpus (ledger `corpus4_member_solve_fix` P2/P3) — KEPT route |
| `crop5lr_norm_px.json`, `crop5lr_sep_{crop5lr,full}_normmatched.json` | `member_separation.py --norm-px` (shared 3513.8 px normaliser) | the crop5lr H1 alignment verdict + the cross-size normaliser-bias method fix (ledger `crop5lr_cross_night_combine_aug06_plus_aug14`) — route RETIRED |
| `crop_work/` | the crop5lr paired-audit engagement | its own section below — crop RETIRED; parity rim-trim REJECTED; member-solve fix KEPT |
| `pedestal_work/` | Siril `seqstat full` + kept-scratch `.seq` M lines + Siril `stat`/`boxselect`; `analyze.py` (derived mu, D from those numbers) RETIRED — its removal condition fired when no undistort stack line carried `-output_norm` any more; recover from git | where a composite's zero point comes from: `-output_norm` is a global min-max rescale, so the level is (reference sky − darkest pixel)/(brightest − darkest) — PROPERTY, closed E0-E3 (ledger aug14 `pedestal_8pct_hypothesis_C_output_norm_minmax`); ratified: compose tier shipped without `-output_norm` (ledger aug06 `output_norm_zero_point_compose_tier`); the campaign is CLOSED — `docs/dead-ends/stacking-compose.md`, "THE DELIVERED ZERO POINT OF ANY `-output_norm` STACK" + `campaign_zeropoint/campaign_record.json`; the residual work is BACKLOG `standard-route-output-norm` |
| `campaign_zeropoint/` | `campaign_zeropoint.sh` (the driver: `run_session_chain.sh --yes` ×4 then `run_corpus_combine.sh`), `moveaside_manifest.json` (the 142 `_outnorm` moves, 43.8 GB, with identities), `unchecked_premises.json`, `campaign_record.json` (Siril `seqstat full` levels vs the stamped anchors on 99 products, DIAGNOSTIC numpy clamp/hole counts with a positive control per product, the old-vs-new K table scored both ways, the 12 guard tables, PNG IHDRs, WCS sky footprints, timings, disk, the diff audit, the eye-inspection notes) + `readout_scripts/` (the diagnostics, sha256 quoted in the record); `readout_work/` scratch gitignored | the from-raws rebuild of every product under one HEAD without `-output_norm` at any tier (ledger aug06 `output_norm_zero_point_campaign_from_raws`): level = the pinned reference's own sky on 99/99, 0 clamps, 0 holes at every composed tier, K scattered within the within-night spread — awaiting the owner's eyes on the 22 finals + the 13 re-seeds |
| `observer_frame_diversity.json` | per-set alt/az pointing derivation from header facts + solves | whether horizon-fixed terms average down across a multi-pointing combine |
| `piperev_inheritance.json` | header census over composites | the reference-member header-leak surface (PIPEREV instance; cited by `CLAUDE.md`) |
| `rebuild_scope.json` | per-level era-equivalence measurement | whether a from-raws corpus rebuild is REPAIR or VERIFICATION |
| `wcs_dual_matrix_probe.json` | Siril + astropy on a dual-matrix WCS header | which matrix form each tool prefers; strip colour-neutrality (registry entry) |

## crop_work/ — the crop5lr engagement's records

Contract trio: `audit_prereg.json` (bars pre-registered before the product
existed) → `audit_worker_report.json` → `director_audit_verdict.json`.
Per-instrument records, each self-describing in its own `instrument` field —
every number Siril findstar / seqtilt / Siril stat / header-WCS sourced:
`sky_grid.json` + `shape_{arm,ctrl}.json` + `dropped_sky.json` (18 shared-sky
positions — the H2/H3 verdicts), `seqtilt_{arm,ctrl}.json`, `xsweep*.json`
(the 30-position rim sweep), `memprobe/` + `setq/` (per-member edge-distance
and set-quality probes, ledger-cited), `audit_member_coverage.json` (38
members × 30 positions × both products), `audit_coverage_arm*.json` (the C6
proposal-fail evidence), `audit_dgrid_{arm,ctrl}.json` (11×7 grid),
`audit_c1_{dlv,ctrl}.json` (prereg C1 on the delivered parity product),
`director_grid.json` + `dir_{arm,ctrl,dlv}.json` (the director's independent
35-position scoring), `audit_solution_drift.json` +
`audit_member_solve_ctrl.json` (the member-solve defect evidence),
`audit_fsweep_{arm,ctrl}_fix.json` (the sweep re-run on the solvefix
rebuilds), `prefix_baseline.txt` (the C5 protected-artifact baseline).

## Evidence resolvers (pruned bulk `.lst`)

A closed route's star-list evidence left the tree with this convention's
adoption; the JSON records above carry the numbers (spot-verified:
`xsweep_arm.json` hix05/midx02 and `audit_dgrid_arm.json` g05y3 recompute
from their lists to the printed digit).

- `crop_work/{c1_ctrl,c1_dlv,da_arm,da_ctrl,da_dlv,dgrid_arm,dgrid_ctrl,fsweep_arm_fix,fsweep_ctrl_fix,lst_arm,lst_ctrl,sw_arm,sw_ctrl}/*.lst`
  and `corpus_sweep_{old,new}/*.lst` — recover: `git show 2654d31:<path>`.
  This resolver also serves the paths `audit_worker_report.json` cites in its
  `artifacts` block (`dgrid_{arm,ctrl}/ + c1_{dlv,ctrl}/ (findstar lists)`).
- `git show 7775fdd:datasets/aug06/crop_work/lst_{arm,ctrl}/` — the within-night
  arc's `*.lst` star lists, pruned when the route closed; recover any one file
  with `git show 7775fdd:<path>`.

## Subject drift note (registry-contract MOOTED class)

`corpus_sweep_old.json`'s `image` path names
`web/results/aug14/stack_july31+aug06+aug09+aug14_full_wcs.fit`, which after
the canonical rebuild holds the REPAIRED pixels; the surface that record
measured survives at `…_full_presolvefix_wcs.fit`. Read `old` = the pre-fix
product and `new` = the repaired product, whatever those paths now hold.
