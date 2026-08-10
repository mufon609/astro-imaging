# The combine contract — what a night must keep to be stackable with a night years later

Multi-night accumulation is the project's core purpose, not an advanced feature:
the point of astrophotography is to shoot on different nights, under different
conditions, and stack it all. This file is the contract that makes that possible.
It binds every calibration, model and route decision — **a change that improves a
per-set product and degrades cross-night combinability is a regression**, and it
has happened twice (both measured, both in this file).

## 0. The two measured facts everything here rests on

1. **The chain is reproducible from raws + tracked records** — MEASURED, both
   halves (ledger `combine_contract_reproducibility`): all **30 group
   memberships across 7 sets** regenerate IDENTICALLY from tracked records alone,
   and a **sub-stack rebuilt from raws + records is PIXEL-IDENTICAL** to the
   preserved one (Siril's own `all nil` refusal on the difference image).

   **What that buys, and what it does not.** It makes the REBUILD path exact and
   it makes process integrity auditable — but it is *not* what makes a combine
   possible. Reproducibility says a member can be RECREATED from raws + this
   repo; the combine path must not need either. A future night must be able to
   stack against an archived member with nothing but that member's own file, on a
   machine that has never seen this repo. So: **records are the asset for the
   rebuild path and for process integrity; the stamped member file is the asset
   for the combine path.** (§4 checks that rule rather than asserting it.)
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

13. **The stamped sub-stacks — an off-rig archival tier of their own.** They are
    PRODUCTS, not cache: they are what a future night actually combines against
    (§5), and the combine must not depend on this repo existing. "Cache"
    describes only their ON-RIG WORKING COPIES, which are freely deleted and
    rebuilt.
    Cost, MEASURED on this rig — one arm per set, not every experiment's members:
    **7.2% of raw volume for aug06 (3.6 GB against 49.6 GB) and 8.6% for july31
    (4.7 GB against 54.5 GB)**. Counting all three aug06 experimental arms it is
    21.6%, which is the reason the tier is *one arm per set*: the arms are
    evidence, and evidence lives with the investigation, not in the archive.
    An UN-STAMPED archived sub-stack is **outside this contract** until
    `backfill_substack_provenance.sh` brings it in (§4, §5).

## 2. REGENERATES — on-rig working copies, delete freely

Master dark; sky flat; calibrated/debayered frames; warped TIFFs; the group
`g*.list` files; per-set stacks; unions; judge surfaces — **and the working
copies of the sub-stacks**, whose archival copies are KEEP (§1.13).

This is a MEASURED status, not an assumption — see §0.1. Storage on the working
rig is transient by design; nothing in §2 is worth protecting.

### 2.1 Degradation tiers — what each surviving thing still buys you

| what survives | what you can do | cost |
|---|---|---|
| **stamped sub-stacks alone** | **COMBINE.** Everything the compose consumes is in the member's own header or its own pixels (§4). No repo, no records, no machine state. | none — this is the design point |
| **raws + this repo** | REBUILD the members bit-identically (§0.1), then combine | one full chain run per set (~40 min/set on this rig) |
| **raws alone** | REPROCESS under whatever pipeline exists then | a different product; the cull, the flat recipe, the optical state and the group derivation are all gone, so it is a new dataset that happens to share photons |

The tiers degrade in that order and only that order. Losing the repo costs
reprocessing, not the archive; losing the stamped members costs a rebuild;
losing the raws is terminal.

## 3. Every sub-stack is SELF-DESCRIBING

An archived sub-stack is only useful later if it can say what made it, with **no
external lookup, no machine state, and no memory of the session that built it** —
because the lensfun user DB is global, unscoped, single-valued machine state that
nothing reverts, so "the model this set's record names" is only true while that
record is the one installed.

Stamped at warp time by `stamp_headers.sh` (`header_provenance_lines`):

| key | meaning |
|---|---|
| `DISTMODL` `DISTA` `DISTB` `DISTC` | the distortion model **verified live in the DB at build time** (from `lens_preflight.json`, never from the fit record's intent) |
| `DISTNORM` | the normalisation radius in px, `min(W,H)/2` — MEASURED: lensfun normalises ptlens by **half the short side**, which puts the frame corner at ρ = 1.80 |
| `DISTRHO` | the fit's control-point support ceiling (p99 ρ) — whether the corner was **fitted or extrapolated**. Describes **the model that warped this member**, so it is absent on pinned/inherited arms whose state has no local fit artifacts |
| `DISTSRC` | which set's fit, and whether inherited |
| `DISTPROV` | `stamped` (written at warp time from the model verified live) or `backfill` (reconstructed later from committed records) — a key of its own, machine-readable |
| `BKGLIGHT` | the lights-side background treatment: `none`, or `subsky1-nodither` |
| `CALSET` `CALDARK` `CALFLAT` | the set, and the masters' identity + depth |
| `PIPEREV` | the repo commit the build ran under |

alongside the acquisition keys (`FOCALLEN`, `XPIXSZ/YPIXSZ`, `EXPTIME`,
`DATE-OBS`, …), `STACKCNT`, `LIVETIME` and `GRPSIZE`.

A member with no `DIST*` keys is **UNKNOWN**, never "compatible".

## 4. THE DEPENDENCY RULE — combining requires only the stamped files

**Every input the compose consumes must come from a member's own header or its
own pixels. No record lookup, no machine state, no repo.** This is checked at
every compose (`run_undistort_compose.sh` T0), not asserted:

| consumer | what it needs | where it comes from |
|---|---|---|
| gate T0 / T1 | `DISTMODL DISTA DISTB DISTC DISTNORM` | member header |
| gate T2 | star positions | member pixels |
| `--weight=nbstack` | member depth | `STACKCNT` header |
| `--weight=noise` | member noise | member pixels (Siril) |
| `-norm=addscale -output_norm` | level + scale | member pixels (Siril) |
| `register -2pass` / `seqapplyreg` | geometry | member pixels (Siril) |
| `--ref` choice | which member is deepest/most central | `STACKCNT` header |
| the product's onward solve | plate scale | `FOCALLEN XPIXSZ` header |
| the record | identity, night, depth, processing state | `CALSET DISTSRC DISTPROV BKGLIGHT DATE-OBS EXPTIME LIVETIME INSTRUME` header |

Those 16 keys are the REQUIRED set. A member missing any is reported
**OUTSIDE THE CONTRACT** by name, with the backfill command. It is not
auto-blocked: T2 measures the real disagreement from pixels regardless, and a
header describes where only a measurement decides.

`DISTRHO` is deliberately **advisory, not required** — "unmeasured" is a
legitimate value for an inherited state whose fit artifacts do not exist, and a
required key with a legitimate empty value teaches readers to ignore the check.
It must describe **the model that actually warped the member**: the pinned and
inherited arms carry no `DISTRHO`, because stamping their set's *own* fit's
coverage there would make a header describe a different model than the
`DISTA/B/C` beside it.

**Background treatment is a processing state exactly like optical state.**
`BKGLIGHT` records it (`none`, or `subsky1-nodither` for the per-frame degree-1
lights-side subtraction), and a mixed-state compose is named loudly with which
members sit on which baseline. It is **not** auto-blocked: the one measured arm
came out judge-equivalent on the corners, so no measurement supports a threshold,
and inventing one here would be the guessing this repo forbids. (Measured aside:
a subsky'd and a non-subsky'd member of the same set separate by **0.00 px** —
the step is purely additive and moves no star.)

Audit status on this rig: **56/56 archived sub-stacks contract-complete.**

## 5. Every combine is GATED on measured model compatibility

Compatibility, not identity: identical models are only the cheap safe case, and
identical-across-nights is precisely the 4.07 px failure. `run_undistort_compose.sh`
runs three tiers and **only the third decides**:

- **T0 identity** — do the members' `DISTA/B/C` + `DISTNORM` match? Free, recorded.
- **T1 prediction** — the ptlens displacement difference between each member's
  model and the reference's, out to ρ = 1.80. A **screen only**: it
  over-predicts by construction (4.01 px predicted against 2.99 px realised),
  because the compose's homography absorbs part of any smooth field.
- **T2 measure** — `scripts/qa/member_separation.py` on the members' own frames:
  every member's `findstar` positions pushed through the homography
  `register -2pass` computed for it, so the same star has one position per
  member in one frame; the reported number is their px separation, **binned by
  each member's OWN field radius**. **This is the acceptance measure**, and a
  BLOCK stops before anything is stacked.
  It does NOT read the registered (`r_`) copies: `seqapplyreg -framing=max` on a
  variable-size sequence — which every compose here is — gives each output its
  own origin, MEASURED 611.9 px apart on the 28-member union, so their pixel
  coordinates are not comparable (`docs/dead-ends.md`).

Thresholds, each traced to a product the owner judged — **and each anchor
re-measured on the current instrument, because a threshold does not survive an
instrument change** (ledger `compose_gate_rezoned_by_member_field_radius`):

| verdict | band | anchor (re-measured / as originally measured) |
|---|---|---|
| PASS | ≤ 0.35 px | the july31 cross-set pair, from the union the owner PASSED: **0.38** / 0.352 |
| WARN | 0.35 – 1.00 px | aug06 under one shared model, round at 1:1 and never accepted: **1.23** / 0.934 |
| BLOCK | > 1.00 px | the two products the owner FAILED, both visibly doubled at 1:1: **3.04** / 2.991 and **3.28** / 2.112 |

Floor for scale, same set, same state, same model: **0.14 / 0.21 px** (0.144 / 0.194 as originally measured).

**THE BANDS ARE FROZEN AND CURRENTLY MISMATCHED TO THEIR ANCHORS. Do not tune
them.** The re-measured values keep the ordering and barely move the floors, but
they push the user-PASSED pair from PASS to WARN and the never-accepted cell from
WARN to BLOCK; a rebuild of the accepted cross-night union reads 7.53 px. A
threshold is only worth setting once the quantity it gates is understood, and the
disagreement is not yet attributed between its two measured sources — the
compose's own global registration and the members' optical state
(BACKLOG:`compose-homography-smear`). Re-anchoring before that would bake the
confusion in. Until it is closed the gate reports the measured number and
`--accept-separation` records any override; the bands are not evidence.

**Do not gate this defect class on corner FWHM or `seqtilt`** — both are MEASURED
blind to it (`docs/dead-ends.md`): corner FWHM ranked the failing union *better*
than the clean control; `seqtilt` read 0.34 px off-axis for the FAILING union
against 0.40 for the PASSING one.

## 6. What a future night needs to JOIN an old archive

1. **Its own corner-true optical-state model.** Not the old night's: states
   differ (§0.2).
2. **The old night's members** — from cache, or rebuilt from §1. Either way they
   must carry §3's headers (an old archive predating the stamp is brought inside
   the contract by `backfill_substack_provenance.sh`, which marks reconstructed
   values `backfill:<provenance>` so they never read as stamped-at-build).
3. **A §5 compatibility measurement** before anything composes.

An archive that predates the stamp is outside the contract until backfilled, and
the backfill is therefore not optional housekeeping — it is what makes an old
night combinable at all. Reconstructed values carry `DISTPROV = backfill` (a key
of its own, machine-readable — a prefix buried in a free-text field is not
something a gate can be relied on to parse) so they are never mistaken for values
stamped from the model verified live at warp time.

**The load-bearing hypothesis, labelled as one.** Cross-night combining should
not require a shared model — it should require each night's model to be CORRECT,
because two correctly-rectified members agree in the SKY regardless of which
coefficients produced them. The 4.07 px figure was measured under a *shared*
model, i.e. one necessarily wrong for one of the two nights, so it measures what
a wrong model failed to remove, not an inherent barrier. **This is untested:** no
corner-true fit existed when it was written (every fit ever shipped here stops at
ρ 1.47–1.51 against a corner at 1.80). The settling test is pre-registered — fit
two nights to corner support, compose one member from each, read §5's measure:
≤ 0.5 px confirms the route, ≥ 2.0 px refutes it.

## 7. The history this contract is built on

Recovered from git, not from the current tree:

- **Cross-night combining had been attempted exactly ONCE before this contract,
  and it failed.** Every path that has ever existed in this repo yields one
  cross-session product and its revoked recrop (`j31-3+a06-3_cov28`, built
  2026-08-08). Everything else — july14's 2/3/5-set, july23's 2-set, july31's
  4-set — is WITHIN one night. Multi-session accumulation was ratified as
  doctrine ~10 hours BEFORE that first attempt: an intent, never a report of an
  exercised capability.
- **Every combine ever accepted used ONE distortion model.** july14 under the
  july14 fit; july31 under it inherited (the union the owner passed); aug06 under
  three per-set fits, failing. The one constant of every passing combine is model
  homogeneity — and the tools agree: Siril's `register -disto=` applies one
  solution per sequence, so its own design assumes one optical state per compose.
- **The combine's value was flagged UNCONFIRMED in the very commit that created
  the compose tool** (rotation-limited field, depth not materialising,
  washed-out renders). The first cross-night combine the owner accepted is the
  six-set one-model union built under this contract.

## 8. The failure shape this contract exists to prevent

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

## 9. Scope — what is constant at which tier

Every calibration input has a scope over which it is valid, and the pipeline is
correct only when each is derived at its own scope and no finer. Getting it wrong
in either direction breaks something, and both failures have been measured here.

| tier | what is constant | derived at this scope | if derived FINER | if derived COARSER |
|---|---|---|---|---|
| **INSTRUMENT** — camera + lens + focal | optical design, sensor geometry, pixel scale, the distortion *family* | lens identity, the sensor geometry that sets ρ, the route | — | a different lens/focal warps on the wrong profile (the preflight stops this) |
| **OPTICAL STATE** — a focus setting | the distortion *coefficients* | the distortion model | **members stop agreeing** — 2.99 px corner disagreement, visible doubling, a product failed by eye | a state-mismatched model leaves residual — the whole of §8 |
| **NIGHT** | thermal regime, transparency family, dark current | the **master dark** | more darks than the regime justifies; no benefit | darks from another night mis-subtract |
| **SET** — one pointing, one run | the sky gradient seen, the pointing, the drift geometry | the **synthetic sky flat**, the cull, the group derivation | — | a flat from another pointing carries the wrong sky |
| **PRODUCT** | nothing; this is where the tiers must MEET | membership, framing, reference, weighting | — | — |

**The OPTICAL-STATE tier is not the SET tier, in either direction.** A state
changes when focus changes, which can span several nights or part of one set.
Assigning the model per SET was a guess about the boundary, and it was wrong both
ways: too fine across a night (it broke the combine, §8) and too coarse within
one, since aug06/set-01's optical state is MEASURED to change between its third
and fourth group (`docs/dead-ends.md`). A state boundary is something to DETECT,
never to assume — and the compose gate (§5) is the detector.

**What the industry does, stated first per the standards-first rule:**

| tier | industry practice | source |
|---|---|---|
| optical distortion | **derived per exposure from the sky**, carried in that exposure's own WCS (TPV/SIP); no shared instrument model at all | SWarp/SCAMP (Astromatic); the SDSS/CFHTLS/DES/Pan-STARRS lineage; PixInsight ImageSolver + StarAlignment with distortion; APP |
| coaddition | **resample every input onto one output WCS** using its own solution, then combine | SWarp |
| dark | per thermal regime, reused across nights when it matches | universal |
| flat | per optical configuration — **this repo deviates deliberately: synthetic per-set sky flats, which is the project's point** | universal |
| background matching | per input, before coaddition | SWarp `SUBTRACT_BACK`; PixInsight LocalNormalization/NSG; APP LNC |

The distortion row is the one that matters: **the industry does not have this
problem, because it does not have a shared instrument model whose scope could be
got wrong.** Distortion is a property of each exposure's own astrometric
solution. That route is BACKLOG:`compose-homography-smear`.
