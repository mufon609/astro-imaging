# Optics-state adoption — executed run report

Execution of `OPTICS_STATE_AUDIT_PROMPT.md` (f9ddadc). Every number below is
an instrument's; controls preserved beside every rebuild; nothing here is
"final" — the per-set adoptions and the combine choice await the user's eyes
on the paired judge surfaces listed at the end.

## 1. Per-set fits (step 1)

Working geometry: 12-frame mid-burst subsets staged as their own dirs,
step 13, windows chosen clear of every audited satellite crossing (set-01's
step-14 window had caught one — its strict prune was likely paying for that).
Both new fits still needed the strict prune: the default cpclean left
multi-px CP contamination in each.

| set | window | raw CPs | default clean | strict prune | checkpto (mean/max px) | ptlens a / b / c |
|---|---|---|---|---|---|---|
| set-02 | DSC_6810..6953 | 233 | 195 (13.57 px max — abc degenerate, d/e exploded) | **125** | 0.02 / 0.08 | 0.00192 / 0.01994 / −0.00071 |
| set-03 | DSC_7350..7493 | 306 | 268 (4.19 px max) | **150** | 0.02 / 0.07 | 0.00428 / 0.01194 / 0.00157 |

Displacement matrix extended to five states (min-half-dim norm, max over
r≤1.0 px; the arithmetic reproduces the d2 ledger's three known cells to the
digit): every one of the 10 pairs exceeds the 0.47 px equivalence bound —
pinned↔s02 2.15, pinned↔s03 0.72, s02↔s03 2.86, s00↔s03 1.77, s01↔s02 1.77,
s01↔s03 1.32. Per-SET optical state stands across all four sets.

## 2. Rebuilds (step 2)

All four sets rebuilt warp-onward under their OWN models. Controls preserved
first: `stack_set-00_pinned*`, `stack_set-0{1,2,3}_full-pinned*`, their judge
surfaces, and the `groups_set-0*_pinned` sub-stack dirs. Preflight wiring
bridged (committed 1b66101): a `--from-fit` install whose coefficients equal
the set's own `lens_fit.json` passes as a loudly-printed CANDIDATE state
(readiness YELLOW); any other installed model still MISMATCH-stops — verified
by executing both directions.

## 3. A/B acceptance instruments (step 3)

seqtilt (pinned → own model), full-frame on the `_spcc` products:

| set | FWHM px | sensor tilt px (%) | off-axis px | verdict |
|---|---|---|---|---|
| set-00 | 3.03 → 3.04 | 0.28 (9) → 0.26 (9) | 0.48 → 0.46 | NULL |
| set-01 | 2.99 → **2.81** | 0.53 (18) → **0.24 (9)** | 0.82 → **0.48** | **WIN** |
| set-02 | 2.87 → 2.89 | 0.23 (8) → 0.21 (7) | 0.57 → 0.60 | NULL |
| set-03 | 2.91 → 2.93 | 0.23 (8) → 0.23 (8) | 0.60 → 0.62 | NULL |

Drift-axis stations (majFWHM px, pinned → own; axis per arm from its own WCS
+ the probe's sky positions): set-01's along-drift band collapses —
along−1300 **3.98 → 3.49**, along−700 **3.34 → 3.08**, perp stations already
at the floor in both arms. Sets 00/02/03: all nine stations within ±0.07 px.

**Adoption per the prompt's rule** (a rebuild that does not measurably
improve does not adopt):

- **set-01 — ADOPT indicated.** Both instruments improve decisively; off-axis
  lands at the family edge (0.48), matching set-00. Awaits the user's eyes:
  `judge/set-01_full_spcc-linked.png` (own model) vs
  `judge/set-01_full-pinned_spcc-linked.png` (control).
- **set-00, set-02, set-03 — NULL.** Measurement-equivalent arms; per the
  rule these do NOT auto-adopt. The user picks which arm each set ships
  (both judge surfaces exist per set). Note the asymmetry honestly: the d2
  displacement curves predicted s02 the FARTHEST from pinned (2.15 px) yet
  its product A/B is NULL — the ledger's curve-to-FWHM caveat measured real.
- **OPEN, unattributed:** the +0.1–0.15 px residual of sets 00/02/03 over
  july31's 0.16–0.47 off-axis family SURVIVES their own models — it is not
  optical-state displacement. Candidates untested: night seeing structure,
  the different pointings' distortion sampling, dec difference.

## 4. july31 diagnosis (step 4) — fit untrustworthy, session stays pinned

The preserved "66 CP / 152 px" state was pre-gauss starvation debris. A clean
re-run (patched fitter, satellite-free window DSC_3893..4036) removes the
starvation — 217 raw CPs — but converges to a sign-alternating curve an order
too large (a=−0.031, b=+0.099, c=−0.066 after strict prune; checkpto
0.02/0.06 reads CLEAN), which contradicts product-level evidence: july31's
products under the PINNED model are the family floor. **Mechanism, measured
from the CP coordinates: the coverage is radially BANDED** — quarter-bins
[0, 45, 5, 143, 15, 0] (a 5-CP hole across r 0.5–0.75, zero corner support,
x reaching only 540–5254 of 6064) vs aug06's full-field
[3, 46, 65, 45, 54, 36]. Two narrow bands cannot constrain a radial cubic;
the banding is night-level (the moonlit gradient), so another window faces
the same coverage. Record: `datasets/july31/set-01/qa_work/
lens_fit_DIAGNOSTIC.json` (deliberately NOT `lens_fit.json` — that path is
what `--from-fit` installs, and this fit must never install). Lesson for the
standing preflight design, now in the BACKLOG item: **CP radial coverage
predicts fit trustworthiness; checkpto residuals do not** (0.02/0.06 on a
banded set that was wrong).

## 5. Baselines (step 5)

No aug06 baselines have ever been seeded (they seed on first user
acceptance), so nothing failed and nothing was re-seeded. The seed commands
print at the end of each chain run; they remain the user's act after
acceptance.

## 6. Twin combines (step 6) — built, measured, awaiting the user's choice

Members: full sets only (ratified — aug06/set-00 and july31/set-04 stay
standalone). aug06 members are the own-model rebuilds (per the prompt; for
sets 02/03 the arms are measurement-equivalent, and the `_pinned` sub-stack
dirs are preserved so recomposing on pinned members is one command if the
user prefers). july31 members stay pinned per the diagnosis — **the
six-member combine is model-heterogeneous and this is its record**: three
members warped under the pinned incumbent, three under per-set fits; every
member is correctly rectified per its own state, which is what the compose
requires (a WRONG model, not a different one, re-enters the dead-end).

Both arms: `--framing=max`, `--weight=nbstack` (depths differ; the two
nights' per-frame sky differs only ~6%, so nbstack ≈ inverse-variance),
reference pinned to the SAME member in both (aug06 set-03 `sub_02` —
pointing-central in both lists) for probe and compose alike, so each map
matches its compose canvas by construction (probe `--ref` added for this,
committed f97ce02).

| arm | members | frames | union canvas | full-cov pixels | largest full-cov rect |
|---|---|---|---|---|---|
| aug06-only | 13 subs (3 sets) | 1,454 | 7511×4881 | 16.38 Mpx | **4159×3272 = 13.61 Mpx** |
| six-member | 28 subs (6 sets) | 2,954 | 8574×5416 | 13.01 Mpx | **3339×3068 = 10.24 Mpx** |

The measured trade the user decides: the six-member arm carries **2.03× the
frames (√ ≈ 1.43× background SNR)** on a **24.8% smaller fully-covered
canvas** (−820 × −204 px vs the aug06-only rectangle; the prompt's ~700×300
estimate measured 820×204). Coverage maps: `covmap_aug06x3.fit`,
`covmap_j31x3+a06x3.fit` (linear k/n member steps verified). Both crops were
verified through the Siril-crop guard (map cropped with identical args reads
full coverage everywhere — the y-flip trap checked, not assumed).

Judge pair (like-encoded, per-product linked autostretch after SPCC on the
verified full-coverage crops):

- `web/results/aug06/judge/set-01+02+03_cov13_spcc-linked.png`
- `web/results/aug06/judge/j31-3+a06-3_cov28_spcc-linked.png`

Gradient context, MEASURED on the finished crops (Siril `stat` regional
medians, green): aug06-only corner spread **0.80%**; six-member **1.88%**
(TL high) — the two nights' flipped gradient orientations did NOT net-cancel
at these corners. Cross-arm caveat per the registry: the two crops frame
different sky, and a four-corner metric on a structured field partly reads
which sky landed in the boxes; the per-arm records are
`datasets/aug06/set-03/qa_work/regional_stat_cov{13,28}.json`.

**Record-home degradation, loud:** the combine finishes were run with
`--set=set-03`, so their solve/SPCC records live under
`datasets/aug06/set-03/qa_work/` — a session-spanning product filed under a
member set, same degradation as july31's 4-set combine. This is
BACKLOG:`cross-set-record-home`, still open; no new location was invented.

## 7. What only the user can decide (stated as options)

1. **set-01 adoption** — instruments say adopt; your eyes on the pair
   (`set-01_full` vs `set-01_full-pinned`) close it. On acceptance:
   `baseline_guard.py --seed` per the chain's printed command.
2. **set-00/02/03 arms** — NULL both ways; pick own-model (consistent with
   the per-set doctrine) or pinned (fewer moving parts); the unpicked arm's
   products are preserved either way.
3. **The combine** — aug06-only canvas vs six-member depth, on the paired
   cov surfaces + the table above.
4. **The residual +0.1–0.15 px elevation** of sets 00/02/03 over july31's
   family — chase it (next instrument: station sweeps on a july31-vs-aug06
   matched pair at matched depth) or accept it as the night's floor.

## Repo state this run leaves

- All fits, A/B records, the diagnosis, the BACKLOG update and the wiring
  patches committed as they landed (b5f9a36, f9ad45f, 1b66101, c402f20,
  dd38019, f97ce02, + this report's commit).
- The live lensfun DB holds the LAST-installed model (aug06 set-03's). Any
  future chain run on other data will read MISMATCH and stop loudly until
  the operator installs the pinned model (one command) — the loud-state
  design makes that safe; the standing per-state wiring is the BACKLOG
  item's closing condition.
- Sub-stacks for BOTH arms of every aug06 set and july31's three full sets
  remain on disk; every alternative compose is one command away.
