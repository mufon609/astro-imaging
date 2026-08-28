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
| `solve_stack_july31+aug06+aug09+aug14_full.json`, `spcc_set-0b_july31+aug06+aug09+aug14_full.json` | `solve_field.py` / Siril SPCC | the canonical corpus product's solve + colour calibration — KEPT route |
| `solve_audit_corpus.json` | `scripts/qa/member_solve_audit.py` over all 77 members | the wrong-scale member-solve class (ledger `corpus4_member_solve_fix`; guard's register row in BACKLOG:`removal-conditions`) — fix KEPT |
| `corpus_sweep_{old,new}.json` | Siril findstar, 44+39 WCS-placed 700 px boxes | rebuild verification, superseded vs repaired corpus (ledger `corpus4_member_solve_fix` P2/P3) — KEPT route |
| `crop5lr_norm_px.json`, `crop5lr_sep_{crop5lr,full}_normmatched.json` | `member_separation.py --norm-px` (shared 3513.8 px normaliser) | the crop5lr H1 alignment verdict + the cross-size normaliser-bias method fix (ledger `crop5lr_cross_night_combine_aug06_plus_aug14`) — route RETIRED |
| `crop_work/` | the crop5lr paired-audit engagement | its own section below — crop RETIRED; parity rim-trim REJECTED; member-solve fix KEPT |
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
- `datasets/aug06/crop_work/lst_{arm,ctrl}/*.lst` (the within-night arc) —
  recover: `git show 6d9e568:<path>`.

## Subject drift note (registry-contract MOOTED class)

`corpus_sweep_old.json`'s `image` path names
`web/results/aug14/stack_july31+aug06+aug09+aug14_full_wcs.fit`, which after
the canonical rebuild holds the REPAIRED pixels; the surface that record
measured survives at `…_full_presolvefix_wcs.fit`. Read `old` = the pre-fix
product and `new` = the repaired product, whatever those paths now hold.
