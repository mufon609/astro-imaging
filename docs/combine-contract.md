# The combine contract — what a night must keep to be stackable with a night years later

Multi-night accumulation is the project's core purpose, not an advanced feature:
the point of astrophotography is to shoot on different nights, under different
conditions, and stack it all. This file is the contract that makes that possible.
It binds every calibration, model and route decision — **a change that improves a
per-set product and degrades cross-night combinability is a regression**, and it
has happened twice (both measured, both in this file).

## 0. The two measured facts everything here rests on

1. **The chain is reproducible from raws + tracked records.** MEASURED, both
   halves (ledger `combine_contract_reproducibility`): all **30 group
   memberships across 7 sets** regenerate IDENTICALLY from tracked records alone,
   and a **sub-stack rebuilt from raws + records is PIXEL-IDENTICAL** to the
   preserved one (Siril's own `all nil` refusal on the difference image).
   Therefore **image data is a cache and records are the asset.**
2. **A distortion model describes ONE optical state, and states differ per set
   and per night.** MEASURED: under one *shared* model a july31 member and an
   aug06 member disagree by **4.07 px** at the corner
   (`cross_night_state_difference`) — worse than the 2.99 px disagreement that
   produced a product the owner failed. A shared model is a same-night fallback
   at best. The multi-night road is per-STATE models that are each CORRECT.

## 1. KEEP — the archival keep-set, per set

Losing any of these loses the night.

**Off-rig (the only irreplaceable bytes):**

1. The set's raw frames.
2. The session's dark raws — the master dark regenerates, the darks do not.
3. The source-integrity manifest (server-side md5s).

**In git (small; this is what the repo is for):**

4. `acquisition.json` — EXIF facts + the derived `mount`.
5. `recipe.json` — the ratified cull. Determines which frames are in; without it
   a rebuild is a *different stack*.
6. `geometry.json` — foreground mask/rect.
7. `qa_work/skyflat_<set>_qa.json` — the synthetic sky flat's build recipe, its
   dark identity and its QA gate. **The flat is rebuilt from the set's own
   frames; this record is the recipe.** (Synthetic flats are the project's point;
   there is no real flat to archive and there never will be.)
8. `qa_work/lens_fit.json` — the optical-state model, its provenance
   (`inherited_from` where a set's own fit is untrustworthy), and its
   **control-point corner-support census** (`control_point_coverage`).
9. `qa_work/lens_preflight.json` — what was actually installed and verified live.
10. `qa_work/anomaly_audit.json` + `qa_work/frame_metrics.json` — the cull's
    evidence, and the dwell floor the group size is derived from.
11. `readiness.json` — the approval the build ran under.
12. The repo commit + `scripts/setup/manifest.tsv` (pinned tool versions).

## 2. REGENERATES — cache, delete freely

Master dark; sky flat; calibrated/debayered frames; warped TIFFs; the group
`g*.list` files; sub-stacks (`sub_NN.fit`); per-set stacks; unions; judge
surfaces.

This is a MEASURED status, not an assumption — see §0.1. Storage on the working
rig is transient by design; nothing in §2 is worth protecting.

## 3. Every sub-stack is SELF-DESCRIBING

A cached sub-stack is only useful later if it can say what made it, with **no
external lookup, no machine state, and no memory of the session that built it** —
because the lensfun user DB is global, unscoped, single-valued machine state that
nothing reverts, so "the model this set's record names" is only true while that
record is the one installed.

Stamped at warp time by `stamp_headers.sh` (`header_provenance_lines`):

| key | meaning |
|---|---|
| `DISTMODL` `DISTA` `DISTB` `DISTC` | the distortion model **verified live in the DB at build time** (from `lens_preflight.json`, never from the fit record's intent) |
| `DISTNORM` | the normalisation radius in px, `min(W,H)/2` — MEASURED: lensfun normalises ptlens by **half the short side**, which puts the frame corner at ρ = 1.80 |
| `DISTRHO` | the fit's control-point support ceiling (p99 ρ) — whether the corner was **fitted or extrapolated** |
| `DISTSRC` | which set's fit, and whether inherited or backfilled |
| `CALSET` `CALDARK` `CALFLAT` | the set, and the masters' identity + depth |
| `PIPEREV` | the repo commit the build ran under |

alongside the acquisition keys (`FOCALLEN`, `XPIXSZ/YPIXSZ`, `EXPTIME`,
`DATE-OBS`, …), `STACKCNT`, `LIVETIME` and `GRPSIZE`.

A member with no `DIST*` keys is **UNKNOWN**, never "compatible".

## 4. Every combine is GATED on measured model compatibility

Compatibility, not identity: identical models are only the cheap safe case, and
identical-across-nights is precisely the 4.07 px failure. `run_undistort_compose.sh`
runs three tiers and **only the third decides**:

- **T0 identity** — do the members' `DISTA/B/C` + `DISTNORM` match? Free, recorded.
- **T1 prediction** — the ptlens displacement difference between each member's
  model and the reference's, out to ρ = 1.80. A **screen only**: it
  over-predicts by construction (4.01 px predicted against 2.99 px realised),
  because the compose's homography absorbs part of any smooth field.
- **T2 measure** — `scripts/qa/member_separation.py` on the registered members:
  the px separation of the same star as two members place it, by field zone.
  **This is the acceptance measure**, and a BLOCK stops before anything is stacked.

Thresholds, each traced to a product the owner judged:

| verdict | band | anchor |
|---|---|---|
| PASS | ≤ 0.35 px | the july31 cross-set pair, from the union the owner PASSED (**provisional — n=1 exemplar; re-anchor as corner-true fits produce more passed products**) |
| WARN | 0.35 – 1.00 px | 0.93 px = aug06 under one shared model: round at 1:1, never accepted → build proceeds, **surface must get eyes at 1:1 before it ships** |
| BLOCK | > 1.00 px | 2.11 and 2.99 px are the two products the owner FAILED, both visibly doubled at 1:1 |

Floor for scale: 0.14 / 0.19 px, same set, same state, same model.

**Do not gate this defect class on corner FWHM or `seqtilt`** — both are MEASURED
blind to it (`docs/dead-ends.md`): corner FWHM ranked the failing union *better*
than the clean control; `seqtilt` read 0.34 px off-axis for the FAILING union
against 0.40 for the PASSING one.

## 5. What a future night needs to JOIN an old archive

1. **Its own corner-true optical-state model.** Not the old night's: states
   differ (§0.2).
2. **The old night's members** — from cache, or rebuilt from §1. Either way they
   must carry §3's headers (an old archive predating the stamp is brought inside
   the contract by `backfill_substack_provenance.sh`, which marks reconstructed
   values `backfill:<provenance>` so they never read as stamped-at-build).
3. **A §4 compatibility measurement** before anything composes.

**The load-bearing hypothesis, labelled as one.** Cross-night combining should
not require a shared model — it should require each night's model to be CORRECT,
because two correctly-rectified members agree in the SKY regardless of which
coefficients produced them. The 4.07 px figure was measured under a *shared*
model, i.e. one necessarily wrong for one of the two nights, so it measures what
a wrong model failed to remove, not an inherent barrier. **This is untested:** no
corner-true fit existed when it was written (every fit ever shipped here stops at
ρ 1.47–1.51 against a corner at 1.80). The settling test is pre-registered — fit
two nights to corner support, compose one member from each, read §4's measure:
≤ 0.5 px confirms the route, ≥ 2.0 px refutes it.

## 6. The failure shape this contract exists to prevent

Twice, a change that was right for the per-set product silently broke the
combine:

- **Per-set optical models.** Fixed a real problem (set-01 off-axis 0.82 → 0.48
  px, a decisive per-set WIN) and made the cross-set union's members mutually
  inconsistent — 2.99 px of corner disagreement, visible star doubling, the
  product failed by eye. The A/B that adopted it was run on per-set products
  only; the combine consequence was never measured before it shipped.
- **A shared family model** as the obvious repair: 4.07 px across nights, worse
  than the defect it was meant to fix.

So: **evaluate every calibration, model and route change against the COMBINE
unit, not only against the per-set product.** A change measured only per-set is
unfinished work.
