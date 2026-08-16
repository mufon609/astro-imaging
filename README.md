# Astrophotography processing pipeline

> **STATUS.** The durable core — calibrate → [undistort] → register → stack →
> solve → SPCC → compose — runs today, and the **first render tier is BUILT**
> (`scripts/stack/render_tier.sh`: separate → denoise the starless → stretch →
> screen-recombine, user-gated by a ratified recipe block, every pixel op and
> every measurement a tool's). The LADDER around it — one knob per arm into
> `exp_<param>_<stamp>/`, the no-regression harness, and the `GENERIC.json` knob
> schema — is still UNBUILT (BACKLOG:`render-ladder`).
>
> Siril 1.4.4's native render surface (`subsky`, GHS via `ght`/`autoghs`,
> `mtf`/`asinh`, `denoise`, `satu`, `synthstar`/`unclipstars`, `rl`/`sb`/
> `wiener`, `epf`, `pm`, `rgbcomp`, `ccm`, plus `wavelet`/`wrecons` and
> `starnet`) is present and scriptable, as are StarNet2, Cosmic Clarity, DeepSNR
> and GraXpert under `/opt`. RC-Astro BXT/NXT/SXT and PixInsight are UNINSTALLED
> by choice (both are paid and both run on this hardware) — a deliberate gap, not
> a platform block, so a **learned deconvolver is an open, unmeasured option**
> (Cosmic Clarity ships non-stellar sharpen models beside the denoiser the render
> tier already drives; BACKLOG:`learned-deconvolution`). Per-tool evidence:
> [`TOOLS.md`](TOOLS.md).
>
> **Numbers inherited from a previous rig are HYPOTHESES until re-measured
> here** — the order is
> [`docs/x86-empirical-test-plan.md`](docs/x86-empirical-test-plan.md).

This repo is a **checklist + knowledge workspace** for astrophotography
processing — official tools do ALL pixel work (processing AND analysis); the
repo's own code never processes or analyzes the deliverable's pixels (full
identity + the ALLOWED/FORBIDDEN line + the anti-drift test: `CLAUDE.md` "What
this repo IS"). It tracks the **process** (Siril/Python orchestration + notes),
never image data (`.gitignore`). This file is the **process contract**: what each
step is for, what the industry tool does there, where we diverge and why, and how
every step is reviewed (tools measure, the checklist records, the user judges).
[`docs/dead-ends.md`](docs/dead-ends.md) holds the **dead-end registry** (every
measured lesson with its numbers) + the acquisition checklist; the x86 build
order is [`docs/x86-empirical-test-plan.md`](docs/x86-empirical-test-plan.md).

**New contributor start here:** (1) [`docs/dead-ends.md`](docs/dead-ends.md) —
the dead-end registry (read it before proposing ANY experiment — if it does not
work, the mechanism why is there); (2) this file top to bottom — the process
contract; (3) the kept scripts' docstrings for each stage's technical why.
Full chronological history lives in git (`git log`; the complete pre-reset
chain + the old NOTES.md are at the commit whose message begins
`checkpoint:` — `git log --oneline --grep='^checkpoint:'`; it is a message
prefix, not a tag). Each dataset's
approved recipe lives in `datasets/<session>/<set>/recipe.json` (see
"Per-dataset state" below).

## The operating loop (per dataset)

The repo does not run a fixed chain — it PROPOSES one from the data and lets the
user decide before it runs. For each dataset:

1. **MEASURE** — the tools measure the data (frame/dark QA, field, the declared
   priorities, e.g. faint-signal-first).
2. **MATCH** — those characteristics map to the best-practice routes in the
   toolkit ([`TOOLS.md`](TOOLS.md)); many routes exist for different situations.
3. **RECOMMEND** — the optimum process for THIS data, with the reason it beats
   the alternatives.
4. **REPORT** — a summary of what the data showed + the recommended pipeline is
   presented to the user.
5. **DECIDE** — the user **accepts / adjusts / reroutes / clarifies**. The gate
   is on what the DATA CANNOT SETTLE: anything an instrument answers decisively
   (route, mount, group size, cull) the pipeline decides and records; aesthetics
   and unmeasurable trade-offs are always the user's; an undecidable measurement
   is the only unplanned stop (`CLAUDE.md`, "Where the gate actually is").
6. **EXECUTE + RECORD** — run the chosen route, then record the choice AND its
   trade-off in the per-dataset state, so every honest compromise is legible and
   improvable later.

The data selects the route; priorities steer it; the user decides; the record
keeps us honest. This is the model the x86 render chain is built around. (The
durable stacking core already defaults sanely when no per-dataset policy is set;
the loop is the full go-forward workflow the render chain completes.)

## The reference standard

The industry deep-sky workflow (PixInsight/Siril practice) that this pipeline
follows, in order — linear until step 6:

| # | standard step | our implementation | status |
|---|---|---|---|
| 1 | calibrate (bias/dark/flat) → register → integrate; per-frame quality assessment (SubframeSelector/weighting) | `run_pipeline.sh`: masters + per-set calibrate → 2-pass/sweep register → 32-bit rej stack; per-frame quality MEASURED at registration on every path (`inspect_stage.py` reg: .seq regdata distribution + outliers, WARN-only, records persisted before cleanup); weighting/culling POLICY = the optional per-dataset `"stack"` recipe block (`-weight=wfwhm\|nbstars`, exclude via `unselect`+`-filter-incl`), resolved by run_pipeline at stack time with provenance printed — ABSENT block is the generic default (unweighted, rejection by sub count via `stack_rejection.sh`: percentile ≤6 / winsorized ≤50 / GESD >50; deterministic generated scripts) | COMPLIANT (matched darks/biases; flats when optics match; frame QA measured + policy surface per-dataset only: siril's `-weight` is a min-max ramp = SOFT-CULLING (it drives the worst frame toward zero weight at any spread, adding sky noise for no crispness gain at low spread) — weighting stays off generically, adopted only through a measured ladder on a recorded trigger) |
| 1a | (no standard step — a telescope's distortion is not modelled this way) | **undistort, between calibration and registration** — a wide UNTRACKED field drifting far cannot be registered by one homography: the real map is `distort ∘ H ∘ distort⁻¹`, so unmodelled radial lens distortion smears the edges. An OFFICIAL measured lens profile (darktable-cli + lensfun) applied to the calibrated, debayered frames removes it. Order is forced: darks/flats are sensor-grid properties, so calibration finishes in SENSOR space first, and a CFA mosaic cannot be interpolated | ADAPTATION, measured + shipped — off-axis aberration 0.57 → **0.25 px** and the centre station at the perpendicular-station level (**3.67 px** majFWHM) with the model FITTED from the set's own frames; a community profile's paraxial error writes an along-drift centre band `seqtilt` cannot see (`star_stations.py` is the band measure — `docs/dead-ends.md` paraxial-band entry). The chain is scripted as `run_undistort_pipeline.sh`. It is a DIVERGENCE for a camera-lens data class the standard workflow does not address, not a bandaid: it fixes the cause (an unmodelled lens), and it is skipped for any set whose fingerprint does not call for it. Removal condition: a distortion model that Siril's own `register -disto=` can consume reproducibly. Route + traps: [`docs/wide-field-untracked-registration.md`](docs/wide-field-untracked-registration.md); routing it automatically is BACKLOG:`route-recommendation` |
| 1b | — | **flatless sets** — a set without a matching flat loudly STOPS; the validated flatless route is the PER-SET sky flat (`build_sky_flat.sh`: the set's own un-registered, dark-subtracted lights, winsorized, validation gates built in). **A flat calibrates ONLY the exact frames it was built from** — cross-set reuse and any shared/union flat on a multi-set combine are banned (user-ratified; the measured imprint mechanism is in `docs/dead-ends.md`: the flat's low-order term carries its source set's sky gradient) | real flat (primary, shot at the session's optical state) → per-set sky flat (validated route) → GraXpert `-correction Division` (vignetting-only fallback, x86); never an in-house fit |
| 1c | multi-channel targets: dual-band OSC line extraction (the standard Ha/OIII workflow) and mono filter-wheel channels, composed to one linear stack | `composition.json` routes it: `dualband-osc` — CFA calibrate → `seqextract_HaOIII -resample=oiii` (honest half size, no invented detail) → same-reference per-line stacks; `mono-filters` — sibling per-filter sets aligned to the composition's reference member (one interpolation pass). Both: the composition record drives the Siril align (mono-filters members to the reference) and Siril `rgbcomp` composes + writes the cube (`compose.py` orchestrates; guards are FITS-header-only) → SPCC (narrowband mode per recipe where lines demand it) | COMPLIANT (2× drizzle full-size dual-band variant + LRGB post-stretch L-join still BACKLOG) |
| 2 | linear gradient removal, star-ful (DBE/GraXpert); Siril doctrine adds: per-frame degree-1 on the subs when the gradient rotates with the session | **not in the shipped chain yet** — the wiped arm chain's `bgelin_mode` (gx = GraXpert BGE; plane = `subsky 1`) re-lands with the render-tier build. The LEVEL (per-frame `seqsubsky 1` vs on-stack `subsky 1 -dither`) is BACKLOG:`render-ladder` L1 — Siril's own background docs recommend per-frame degree-1 for session-rotated gradients | GAP (user-gated build; item-7 A/B first). CLASS LIMIT, now MEASURED rather than assumed (`docs/dead-ends.md`, Background): a full extraction model cannot distinguish frame-filling faint structure from a sky gradient and absorbs what it can reach — but "only a first-degree plane preserves it" was mechanism, and the bound is smaller than that implied. Over this field a **plane can represent 10.0% of the Gaia unresolved-starlight predictor's spatial variance, a quadratic 36.2%, a cubic 43.5%** (`starlight_preservation.py`, aug06/set-01, 140-cell external lattice) — so degree 2 is a real but bounded cost, not erasure, and the number is recomputed per field. The diffuse field IS stars (`docs/dead-ends.md` terminology entry: at 17"/px it is the integrated light of stars below the detection limit); BGE on the starless layer ERASES it (never reorder) |
| 3 | photometric color calibration (SPCC/PCC via plate solve) | `solve_field.py` (blind astrometry.net solve, WCS inject) + `spcc_run.py` (siril `spcc` with local Gaia catalogs, K factors captured to `work/spcc_<set>.{json,log}`) → `stack_<set>_spcc.fit` | COMPLIANT, with ONE stated sensor limitation: the SPCC database carries no Z-series entry, so K factors ride the sensor-null generic curve until a measured response is contributed (`spcc_run.py` prints it per run; the readiness report shows it YELLOW). SPCC calibrates the raw stack directly; spcc rerun measured pixel-deterministic. Both vendors' doctrine orders BGE before SPCC; the repo's mechanism claim (per-star local-annulus photometry cancels a smooth background, so the K fit is order-robust) is CHECKED, not assumed, when the render build inserts the background step before SPCC — the recorded K delta is the check. SPCC is BROADBAND-only: a mono/single-filter set skips it (no colour to calibrate) |
| 4 | deconvolution (optional, data permitting) | skipped | COMPLIANT-SKIP — measured dead end on this data (in-exposure trailing, PSF unstable on ≈0 background) |
| 5 | linear noise reduction (Siril doctrine: NL denoisers work best on unstretched data) | RUNNABLE NOW on this rig, user-gated: Siril native `denoise` (NL-Bayes) and the installed GraXpert `-cmd denoising` are both verified on-rig (probe: 1024² tile — GraXpert 71 s ≈ 13–14 min full-frame extrapolated; Siril seconds-class). The ladder + its objective instrument (the noise-split structured term) are pre-registered as BACKLOG:`render-ladder`'s L2 | GAP until laddered + judged. The general CHROMA-noise fill is INSTALLED and unmeasured: Cosmic Clarity's `--color_denoise_strength` runs here (NXT-AI3 is the paid alternative, uninstalled by choice — `TOOLS.md`); Siril has no native general-chroma tool (`docs/dead-ends.md`) |
| 6–8 | star separation → stretch (starless hard / stars gently; narrowband per-line + palette colour) → recombine + export | **Separation is BUILT and shipping**: StarNet2 is installed and driven by `render_tier.sh` via siril's `starnet`. `synthstar` outputs a star MASK that needs a starless layer to recombine (on-rig probe + official docs), so it is not a substitute. **The rest is present** (on-rig probe): stretch (`ght`/`autoghs`/`mtf`/`asinh`, linked after SPCC), star desaturation (`unclipstars`, linear-only), thresholded `satu`, `pm`, `rgbcomp`, 16-bit `savepng`. The no-separation build is pre-registered as BACKLOG:`render-ladder`'s L1; the ladder rides BACKLOG:`render-ladder` | GAP (user-gated LADDER; the tier itself is built) |

Principles that keep this honest:

- **The mapping above is re-verified against current Siril/PixInsight
  doctrine at every siril MAJOR-version bump** (e.g. 1.4→1.6), plus a
  **changelog scan** on point releases that re-audits only a stage a release
  actually touches (stretch guidance, SPCC modes, separation/drizzle models) —
  tool positions move, so the comparison is standing work, not a one-time audit;
  a full re-audit every *minor* version is over-frequent and gets skipped.
  Verification recency lives in git history, not in the entries themselves.

- **A divergence from the standard is a bandaid unless it is a measured,
  documented adaptation forced by this data** — each one carries its removal
  condition (recorded with the adaptation in its script docstring or recipe;
  full ledger in git).
- **Full frame is mandatory.** No crops hiding defects; the foreground branch
  never drives decisions (it is masked in QA statistics, feathered in
  rendering operators).
- **Root-cause rule:** when a root cause is found and fixed, every knob that
  was tuned while the root cause was still present is STALE and must be
  re-derived.

## The review contract (who/what judges each step)

1. **The tools measure (orchestrated + recorded).** Frame and render quality come
   from the tools' own analysis, driven headless and captured to the dataset's
   record — Siril `stat` / `register` (background, noise, FWHM, roundness, star
   count) + its SubframeSelector-class metrics, ASTAP (HFD, star count), the solver
   + SPCC logs. The repo never recomputes these in numpy: it runs the tool, parses
   its report, records it. [`TOOLS.md`](TOOLS.md) maps which tool measures what. A
   labeled per-stage sequence still stands on every render (each stage written
   full-frame + the tool's measured numbers into `<final>_stages/`), so a defect
   localizes to the stage that introduced it — a DIAGNOSTIC surface, never the
   aesthetic-judgment surface (that stays the full-frame lossless finals).
2. **The checklist decides pass/fail from the tools' numbers.** A per-dataset
   checklist applies the acceptance criteria (see "How a change is accepted") to
   the *tool-reported* measures — decision logic over tool outputs, never in-house
   pixel analysis. Criteria don't loosen without explicit user ratification.
3. **The user judges aesthetics on the recombine — from FULL-FRAME
   LOSSLESS FINALS, opened independently.** A judgment set is a folder of
   whole-frame 16-bit lossless PNGs with clean names and a
   QUESTION.md, nothing else. **Project policy: the judgment surface is the
   16-bit PNG ONLY — no 8-bit/reduced-depth or lossy copy, no crop and no
   composited panel is ever JUDGED** (no PNG8, no JPEG). It scopes what the
   verdict is taken on, not what the repo may write: delivery surfaces (a
   shareable q100 final, browser previews, an on-request tool-made zoom crop)
   are allowed and are listed under "Data integrity" below — the judge pulls
   each full-precision file into their own viewers and environments. Assemble it
   with `judgment_package.py` (orchestration + record: it refuses starless
   layers before linking, embeds the tool-reported candidate-vs-control
   deltas + an objective WIN|NULL|needs-eyes verdict, writes QUESTION.md).
   An on-request zoom crop, if ever needed, is produced tool-sourced (Siril
   `crop` + 16-bit `savepng`) — never an in-house pixel path, never the
   judgment surface. Objective fixes with tool pass/fail metrics may
   commit; recipe/aesthetic changes require the user's visual approval
   before they are baked as defaults.

   **Pre-handoff inspection is mandatory** (measured failure: two
   packages in a row shipped defects the assembler had not seen — a
   faint-starlight allocation gap, then coring-mottle "blotch" visible at
   1:1 — because candidates were checked only in downscaled views and
   one crop). Before a package is handed over, its assembler inspects
   every candidate AT NATIVE 1:1 in the object region, the sky, and the
   star field, plus whole-frame at fit — and, when the dataset carries a
   reference finish (`<session>/reference/`, the answer key), compares
   at like scale and orientation. The findings go into the package as
   inspection notes; `judgment_package.py` REFUSES to assemble without
   them. The notes state what the assembler sees wrong or unresolved —
   a package with unstated known defects is a contract violation, not a
   judgment set. The user's eyes remain the judgment; the inspection
   exists so they are never spent discovering what the assembler could
   have seen.

**Defect coverage.** The gradient / blotch / ring / aura / chroma-neutralization
defect classes are caught by the tools' own analysis + the checklist. Where no tool
measures a defect, that is a documented gap — a candidate for a standalone ALLOWED
detector (like `anomaly_audit.py`) or a tool to adopt, never a numpy gate.

### How a change is accepted

Byte-identity with one dataset's render is **not** the bar. It answers "did the
output change?", never "is the output right?" — so it promotes a single
imperfect recipe into the definition of correct, and the cheapest way to stay
green becomes a bandaid that special-cases that dataset. Three checks replace
it, each answering a question it can actually answer:

1. **Reproducibility (not byte-identity).** The render is a function of its
   *pinned* inputs — tool versions (the install manifest), every param and seed
   pinned, no unseeded step. It does NOT require a byte-identical re-render, and
   demanding one is the wrong bar in general — but do not ASSUME a neural stage
   cannot give it. MEASURED on this rig, per stage, two identical runs compared with
   Siril `isub`: StarNet2 (also across thread counts), Cosmic Clarity denoise, and
   Siril's stretch + `asinh` + `pm` recombine are all **bit-identical**, so the
   render tier reproduces byte for byte and byte-identity IS the available bar here
   (`docs/dead-ends.md`). The general caution still stands for tools not yet
   measured (RC-Astro BXT/NXT/SXT are uninstalled) — and the no-unseeded-step rule
   already cost `subsky` its `-dither`, which is what made `seqsubsky`'s opt-OUT
   dither a defect when it shipped. Verify **cheaply** (a fast canary + the
   deterministic orchestration, not a doubled full-res render) to a documented
   **tolerance**: byte-identity where a tool actually gives it (siril native
   single-thread, deterministic float32 temp-FITS round-trips), reproducibility
   within a tolerance negligible vs the metrics we judge on where it can't (a
   stage that varies above that tolerance is flagged and pinned to deterministic
   settings — single-thread / fixed device — if it can be). This extends the
   existing **STACK exemption** (its register sweep is assumed non-deterministic →
   verified by gate + inspection, not bytes) to the neural render tools — but that
   assumption now has a COUNTER-MEASUREMENT and is narrower than it reads. The
   groups route's COMPOSE stage (`register s -2pass` → `seqapplyreg` → `stack mean`
   over the sub-stacks) recomposes **BIT-IDENTICALLY**: measured on july31 set-01
   and set-02, each recomposed from its own unchanged sub-stacks and differenced
   against the original with Siril `isub` — all three channels nil, both sets.
   SCOPE, because it is easy to over-read: n=2, same-arm, one rig, siril 1.4.4, and
   the COMPOSE register sweep only — 5 members, not the per-frame `register -2pass`
   over 500 warped raws, which is a different problem size and stays unmeasured.
   So the exemption holds where it was written (the per-frame sweep) and does NOT
   hold for the compose, where byte-identity is available and should be used. The
   intent survives: a candidate-vs-control delta reflects the CHANGE, because the
   tolerance sits far below the deltas we judge on. (An unrealistic byte-identity
   check on a slow, non-deterministic chain doesn't add rigor — it gets skipped or
   blocks valid work; a right-sized one actually runs.)
2. **No regression, across data classes.** Every registered dataset (each
   baselined under `datasets/`) must still PASS the **tool-sourced acceptance
   checklist** and show no WORSENING of the tools' recorded measures vs its own
   baseline (regression semantics — a clean dataset rotting toward the defect
   class fails long before any absolute line). **The criteria never loosen.** The
   reference suite spans the classes the pipeline actually meets — underexposed
   DSLR wide-field, matched-flat off-centre object, wide-field, and mono FITS
   with a frame-centred galaxy — so no single dataset can hold the pipeline
   hostage. The **per-change cost is tiered**: run the affected class(es) + one
   canary per change; the **full suite** on a cadence / before a re-baseline or
   release / when a change touches shared code — not every commit. (The harness
   that renders every baselined dataset and diffs the tools' measures rides the
   render-tier build — user-gated; the no-regression standard is binding now,
   enforced by the checklist + declared-delta.)
3. **Declared delta.** A change that alters a registered render is *expected*,
   not forbidden. It must report the metric deltas and side-by-side panels in
   LIKE encodings. Strictly-better-or-equal objective metrics may commit; any
   aesthetic change needs the user's eyes before it is baked as a default. An
   approved render is re-baselined and git-tagged — the tag is the record, not
   a frozen file.

Pin narrowly where identity IS the contract — a tool's exact invocation +
version that a recorded measure depends on — not the whole product chain.

**Data integrity (what is lossy, where, and the guards).** The processing
path is linear FITS end to end, **UNCOMPRESSED at every stage** (a foundational
rule: no compression anywhere in the pipeline — every generated `.ssf` pins
`setcompress 0`, since siril persists that preference across sessions); 32-bit
float **end to end, with NO precision reduction anywhere**. The 16-bit
stack-time intermediates are RETIRED and no exception remains:
their removal condition fired on this rig, and the "+0.3% stack noise"
figure that made them look cheap was wrong — re-measured, the 16-bit chain kept
only **~55–70% of the 32-bit arm's extended faint contrast** (NAN-region contrast
4.8/2.4/3.9 vs 8.5/2.9/5.6 % of local sky, R/G/B), i.e. it cost real structure,
and a 16-bit calibration MASTER additionally stores a sensor-fixed ±0.5 ADU
quantization pattern (0.2889 ADU RMS against a 0.4213 ADU floor, **+21%**) that
is subtracted identically into every light. Mechanisms + numbers:
[`docs/dead-ends.md`](docs/dead-ends.md) "Calibration masters".
Lossy/display files exist ONLY as OUTPUT surfaces: a lossy preview jpg
(never a judgment surface), the q100/4:4:4 final jpg, and judgment panels.
GUARDS on the surviving core: `compose.py` asserts float32 inputs;
**`scripts/stack/check_bitdepth.sh` fails the build if any master template or
product builder stops pinning `set32bits`/`setcompress 0`** (both are PERSISTED
siril preferences, so an unpinned script inherits whatever ran last); a
FITS-only load guard returns with the render rebuild.
Human judgment uses the LOSSLESS artifact: the 16-bit PNG for the final
**and the starless layer** (the full-precision layer at 65536 levels; project
policy — NO 8-bit/reduced-depth or lossy copy is produced or judged), written
by Siril `savepng` (16-bit
auto-selected from a 16/32-bit source, sRGB declared via its own iCCP
embed). Never judge a q92 surface.

**North star:** every stage's TOOLS report their numbers so that eventually
ANY dataset can be dropped into a session dir and be properly judged and
processed to its best honest outcome — composition facts from config or
derivation, defects caught by the tools' analysis + the checklist, aesthetics decided by
the user from measured candidates, and every divergence carrying its
removal condition.

## The experiment discipline

- One knob per experiment, values bracketing the control; hypothesis
  pre-registered *before* the run (`docs/dead-ends.md`). Each value is rendered
  as a full-frame lossless final + stage sequence into
  `web/results/<session>/exp_<param>_<stamp>/`, appended to the tracked per-dataset
  `experiments.jsonl`, and STOPs for user judgment. (The ladder that automates
  this rides the render-tier build — user-gated; the discipline is binding now.)
- The verdict round-trips: once judged, the ledger entry is closed
  win|null|deadend with its reason. A measurement that kills a hypothesis
  becomes a dead end **written into `docs/dead-ends.md` with its numbers**
  before anything else is tried (the ledger indexes it; `docs/dead-ends.md`
  states the mechanism).
- Comparisons are honest: `judgment_package.py --control=<label>` embeds the
  measured candidate-vs-control deltas + an objective **WIN | NULL | needs-eyes**
  verdict on the tools' metrics (auto-discovered from the `<final>.metrics.json`
  sidecar). A WIN names the delta that earns it; needs-eyes = mixed or aesthetic
  (the user's eyes on the finals). Report each result as a WIN or a clean NULL —
  never "fixed/final/matched/close".
- Processing is a TOOL, not hand-rolled numpy — the ALLOWED/FORBIDDEN doctrine
  (`CLAUDE.md` "What this repo IS") is the guard. When a target's honest best
  outcome needs a stage turned off or swapped, that is the toolkit working as
  intended (each choice carries its reason).
- Preserve the stack per pipeline experiment (`cp` to a tagged name).
- **An experiment's SCOPE is set by BUILD-PATH OCCUPANCY, not by whether the work
  is called an experiment (user-ratified 2026-08-16).** A read-only probe stays
  inside whatever unit is running — a tool's `--help`, a FITS header read, `stat`
  on a product that already exists. Anything that drives the chain, writes to the
  build path, or runs long enough that a commit could land while it is running
  takes **its own session**.
  **The deciding test is mechanical and needs no judgement about importance: would
  a commit landing during this run be unsafe?** If yes, it is a session. The hazard
  is the one `CLAUDE.md` already states — `PIPEREV` is stamped from the commit at
  build time, so a commit mid-run is a second knob inside your own experiment —
  and this keys that rule to the chain actually running rather than to the label on
  the work. A long read-only measurement can qualify on duration alone.

### New-class triage (BEFORE the first judgment package)

The GENERIC layer was tuned on specific data classes and a knob correct
there can silently damage another class until a human notices the defect
(measured twice: post-stretch vst crushed 40–50% of a high-SNR nebula's
chroma across four judged renders; the linked stretch drowned a
narrowband target's O3 sphere). When a dataset CLASS first arrives (new
sensor class, new SNR regime, new target-brightness class, new
composition kind), ladder the generic knobs whose `datasets/GENERIC.json`
why-notes name a class risk — one knob per ladder, the user judges once
per class instead of debugging after.

**Both halves of that are PENDING the render-tier build today:**
`datasets/GENERIC.json` is a
stub (`"render": {}, "why": {}`) because the render-knob schema was wiped
with the retired chain, and the ladder harness rides that build (user-gated;
the ladder is BACKLOG:`render-ladder`). The knobs the previous chain
laddered — background extraction mode
(the proven signal eater: full AI extraction absorbs the frame-filling
unresolved starlight), starless denoise strength (the proven chroma killer), black
point (crushes faint extended signal), starless target, star peak, and
linked-vs-unlinked stretch — are the *class risks the rebuilt chain must
re-surface as knobs*, and their mechanisms are all in
[`docs/dead-ends.md`](docs/dead-ends.md). The DISCIPLINE below is binding
now; the file and the harness get re-seeded by the rebuild.
(Narrowband-palette colour is not laddered — the star-neutral colour
balance is a GAP, `docs/dead-ends.md`.)

## Per-dataset state (`datasets/<session>/<set>/`, tracked)

Session data dirs are gitignored (several hold third-party raws that must
never be committed), so everything the repo versions about a dataset lives
in `datasets/<session>/<set>/` — see `datasets/README.md` for the contract:

- `geometry.json` — the only per-set **composition fact**: the terrestrial
  **foreground** (`rect` fractions or a derived pixel-`mask` npz, session-
  relative) plus optional `starsep` overrides. Resolved
  by `astrometrics.configure()` in the entry points that need it (inspect_stage,
  solve_field, compose). No file: foreground **none** (whole
  frame is eligible sky).
  A new set NEVER inherits another set's foreground silently. A configured
  foreground must TOUCH A FRAME BORDER (terrestrial obstructions are
  border-anchored by construction; the foreground is excluded from the
  measured sky scope, so a floating interior one would carve graded sky out
  of that scope) — refused loudly at configure time.
- `recipe.json` — the processing knobs: the `render` dict (the render chain
  resolves CLI > recipe > `datasets/GENERIC.json` and prints the provenance; a
  dataset with no recipe renders data-class-blind generic and says so — the
  render dict's schema is PENDING the render-tier build) plus the optional `spcc` spec
  (sensor/filter names or narrowband wavelengths, same resolution order in
  `spcc_run.py`). An **approved** recipe pins every knob so a later
  generic-default change cannot silently restyle it.
- `GENERIC.json` (one per repo, beside this contract's per-set dirs) —
  the tracked base layer every render inherits: the generic value AND a
  per-knob "why" note naming what it encodes (most were measured on one
  underexposed DSLR wide-field) and its known class limits. Tweakable at
  any time — but a change restyles every non-approved dataset, so it
  lands as a declared delta. The knob SCHEMA stays in code; the render chain
  hard-fails on any file/schema drift (pending the render-tier build).
- `baseline.json` — the measured no-regression record (pinned stack sha,
  expected tool measures, artifact hashes), written only by the no-regression
  harness (rides the render-tier build).
- `composition.json` — only for multi-line/multi-filter targets: how the
  composed linear stack is BUILT (kind, extraction, lines, palette
  channel mapping). Absent = ordinary single-stack set.
- `experiments.jsonl` — the tuning-experiment ledger (append-only): one
  record per ladder (param, values, control, hypothesis, pinned stack,
  verdict), closed by `--verdict`. The durable tracked index of what was
  tried; heavy per-value finals stay in gitignored `web/results/<session>/exp_*/`.

The background is NOT a per-set composition fact: sky scope is selected
STATISTICALLY (dark blocks, foreground excluded — see the review contract),
so no galactic band or object region is ever configured per set (a bright
object has no fixed geometry a mask could scope — see `docs/dead-ends.md`).

A rectangular foreground (`rect`) covers most terrestrial obstructions; a
non-rectangular pixel `mask` npz is still honoured by `geometry.json`, but the
mask-DERIVATION step is a documented gap — an official tool or a hand-drawn
mask, never an in-house fit (in-house derivation would read the stack pixels).

## Running it

```bash
# stack builder (session dir, set name; ~15 min) — the standard class
#   calibrate -> register -> stack
scripts/stack/run_pipeline.sh sessions/<session> <set>

# flatless set: build + validate the PER-SET sky flat FIRST (the ratified rule:
#   a flat calibrates only the exact frames it was built from — dead-ends entry)
scripts/stack/build_sky_flat.sh sessions/<session> <set> --dark=<master> --out=sessions/<session>/work/masters/skyflat_<set>.fit

# wide-field UNTRACKED class: calibrate -> UNDISTORT -> register -> stack
#   (a far-drifting set cannot be registered by one homography; the warp uses
#   the lensfun model — fitted per rig/lens via scripts/darktable/
#   fit_lens_model.sh + install_lens_model.sh where the community entry is
#   inadequate). The whole chain, step by step with its measured basis:
#   docs/pipeline-wide-field-untracked.md; registration route + traps:
#   docs/wide-field-untracked-registration.md. Auto-routing by fingerprint is
#   BUILT (run_set_chain.sh); remaining wiring: BACKLOG:`route-recommendation`.
scripts/stack/run_undistort_pipeline.sh sessions/<session> <set> --dark=<master> --flat=<master> [--frames=N]
# the STANDING stack route for the class: balanced consecutive groups ->
#   per-group GESD stacks -> register + stack the sub-stacks, which STAY on
#   disk so the cross-set combine (run_undistort_compose.sh) remains buildable
#   — single-pass forecloses it (composing per-set finals is a registered dead
#   end) for a quality delta measured NULL. Group size derives from frame count
#   and the obstruction audit's dwell floor; disk peak is per-group, derived
#   from the set's own frame geometry (disk_budget.sh). Valid post-undistort ONLY.
scripts/stack/run_undistort_groups.sh sessions/<session> <set> --dark=<master> --flat=<master> [--group=N] [--plan]

# color-calibrate the stack once per stack rebuild (~1 min, local catalogs)
python3 scripts/calibrate/solve_field.py web/results/<session>/stack_<set>.fit \
    --inject=web/results/<session>/stack_<set>_wcs.fit
# NEW FIELD: make sure the local Gaia chunks cover it before SPCC (a southern
# field needs southern chunks); --fetch downloads any missing ones
python3 scripts/calibrate/spcc_cone.py web/results/<session>/stack_<set>_wcs.fit --fetch
# then siril spcc (spcc_run.py) → _spcc.fit

# final render — UNBUILT, user-gated (ladder: BACKLOG:`render-ladder`;
# the neural tiers are installed and driven; what is unbuilt is the LADDER —
# TOOLS.md, BACKLOG:`render-ladder`). Everything ABOVE
# (stack → solve → spcc → compose) is the durable core and runs today.
```

Environment specifics (siril invocation, catalogs, GraXpert, the x86 target)
live in CLAUDE.md "Environment".

## Repo map (`scripts/`, by stage directory)

**`lib/`** — shared helpers (FITS-I/O + geometry, acquisition), imported via the walk-up bootstrap

| file | role |
|---|---|
| `astrometrics.py` | minimal FITS read (feeds the plate-solve extraction) + per-set foreground geometry (`branch_mask`) — no in-house pixel analysis, the tools measure. The FITS parse is astropy's (`read_fits` → `fits.open`, `fits_pixel_scale` → `fits.getheader`), so the hand-rolled-parser removal condition has FIRED; its row is in BACKLOG:`removal-conditions` |
| `acquisition.py` | per-dataset acquisition record: EXIF-derived facts (exposure/focal/ISO/FOV+pixel-scale/cadence) + the `mount` (DERIVED from the measured drift signature when decisive, human-declared otherwise, provenance in `mount_source`); `resolve()` seeds `datasets/<session>/<set>/acquisition.json` and STOPS if `mount` is undeclared (no silent camera model), `timeline()` feeds the audit's capture-run segmentation. Reads EXIF only, never deliverable pixels |
| `route.py` | THE ROUTE KEY — one definition, every consumer. The single source for which chain a set takes; `DRIFT_FRAC_MIN` and its floor live here (removal-conditions register) |
| `fingerprint.py` | derives a set's CONFIG FINGERPRINT from the data — the MEASURE→MATCH input, and the reference ALLOWED router `CLAUDE.md` names: every input is a tool's (astrometry.net solve, Siril `findstar`, header facts), the in-house part is only the derived trail/drift geometry no tool reports |
| `cullspec.py` | THE one meaning of `recipe.json`'s `stack.exclude` — trailing FILENAME digits, matched within one set, aborting loudly on an ambiguous exclude |
| `frame_order.py` | emits a set's frames in CAPTURE ORDER rather than filename order, reading paths from STDIN so an `ARG_MAX` split cannot re-order chunks independently. Exists because the frame counter wraps at 9999 (`docs/dead-ends.md`) |
| `siril_run.sh`, `siril_run.py` | single source of truth for INVOKING Siril, flock-serialised because the flatpak's instance-dir lifecycle races (removal-conditions register); `check_siril_invoke.sh` is the guard that every caller uses it |
| `wait_for.sh` | wait for processes matching a pattern WITHOUT matching yourself — the registered `pgrep`-matches-its-own-argv deadlock, fixed at the source |

**`stack/`** — build the integrated stack

| file | role |
|---|---|
| `lens_preflight.py` | optics guard, run first by `run_pipeline.sh`: reads EVERY frame's camera/lens/focal via exiftool and STOPS on a MIXED-optics set (`acquisition.json` derives optics from the FIRST FRAME ONLY, so it structurally cannot see a zoom bump mid-set) or on a set whose frames contradict the tracked record. With `--require-profile` it also makes darktable PROVE it corrects the set — rendering one frame through the pinned `lensdist`/`nodist` pair and asking Siril for the difference — because darktable silently applies NO correction to a lens lensfun cannot match and never says so | Also asserts the installed distortion coefficients equal the PINNED model for this lens@focal (`scripts/darktable/lens_models.json` — THE authority): `lensfun-update-data` reverting the DB, or a candidate fit left installed, still warps — so the warp-happened proof passes while the set stacks with different optics than every product it will be compared against. The per-set-record variant was REFUTED and reverted (`docs/dead-ends.md`): its founding evidence was a compose artifact, and per-set models broke the combine.
| `run_pipeline.sh` | stack builder: preflight → masters → calibrate → register (2-pass/sweep) → rejection stack; forks camera-raw vs dedicated-astrocam FITS, loudly STOPS a flatless set demanding a matching flat (synthetic-flat is a documented gap — BACKLOG), and routes a `composition.json` dual-band set through line extraction → same-reference per-line stacks → compose |
| `run_undistort_pipeline.sh` | stack builder for the wide-field UNTRACKED class: `lens_preflight --require-profile` → chunked calibrate (CFA, sensor space) → debayer → darktable lens warp (distortion only via the stripped lensfun DB, incl. the fitted entry) → register 2-pass → rejection stack. Guards up front: the 1-frame-final-chunk trap (Siril cannot sequence one frame) and the uncompressed disk peak — registration holds the warped set and the registered set at once, so the budget is `W x H x channels x 4 bytes x 2`, DERIVED per set from the tracked `acquisition.json` geometry (exiftool for raws, FITS `NAXIS` for astrocam frames) rather than a per-camera constant, and it STOPS if the geometry is not on record instead of assuming a frame size. The derivation AND the arithmetic live in `scripts/stack/disk_budget.sh`, shared with `run_set_chain.sh` (plan disclosure + a forced `--route=single`) so a forced route and the builder cannot disagree; `--frames=N` selects an even stride that preserves the full time span; `--select=<list>` processes an exact frame block (the groups driver's hook — whole-set single-pass runs only as the `--route=single` operator override) |
| `run_undistort_groups.sh` | the STANDING stack route for the undistort class: consecutive balanced GROUPS each run the full chain and rejection-stack (intermediates deleted per group), then the sub-stacks register + stack into the final — and stay on disk, keeping the cross-set combine buildable (single-pass deletes them and crops to `-framing=min`; composing per-set finals is a registered dead end). Valid ONLY post-undistort (homographies compose; pre-undistort composition was a measured dead end). Declared cost: one extra interpolation pass, measured NULL (9/9 drift-axis stations within 0.05 px). Removal condition: a measured quality cost of the extra pass at established magnitude, or cross-set composition leaving the project's goals |
| `build_sky_flat.sh` | PER-SET sky-flat builder for flatless sets (the ratified rule: a flat calibrates only the exact frames it was built from — `docs/dead-ends.md` imprint entry): the set's own un-registered lights, dark-subtracted, CFA, `-norm=mul`, `--rej=wins` default (specks measured 101→0 vs median; `median` kept as the attribution arm); validation gates built in (regional `stat`, `findstar` speck count, autostretch preview, tracked qa record). Removal condition: a matching real flat for the set |
| `run_undistort_compose.sh` | compose already-built undistort SUB-STACKS across sets into one deep stack (register `-2pass` → `-framing=min\|max` → PLAIN MEAN — sigma rejection across sub-stack composes is a measured dead end); valid post-undistort only (homographies compose) |
| `render_tier.sh` | the RENDER TIER past the diagnostic judge surface: Siril `starnet` separation → Cosmic Clarity denoise on the starless → per-channel-black-point / common-gain `mtf` stretch → `asinh -human` stars → `pm` screen recombine → 16-bit PNG. User-gated: with no ratified `render` block for the name it measures, writes `render_proposed`, prints it and STOPS (exit 7). Knobs resolve CLI > recipe > `GENERIC.json` > built-in with the provenance PRINTED; the recipe pins only scale-free FRACTIONS and the absolute mtf triplet is re-derived every run from the layer actually being stretched (measured: deriving it from the star-ful input stack put the sky at 0.063 for a 0.100 target and cast it +5.6% in B/G). Every measurement is Siril's own — `findstar` for the separation gate, `pm`+`isub`+`bgnoise` for the recombine residual, `wavelet`/`wrecons`+`bgnoise` for the per-scale denoise profile, `stat main` for the colour record. Refuses to overwrite an existing product without `--overwrite`, and reuses cached layers so ratifying costs one stretch, not another separation + denoise |
| `check_bitdepth.sh` | the 32-bit guard, run in CI / before a release: no `set16bits` anywhere under `scripts/` outside four documented instrument exemptions, and every master template + product builder must EMIT `set32bits` and `setcompress 0` (comment lines stripped, since a pin that exists only in prose is the failure mode it is guarding against). Both are PERSISTED siril preferences, so an unpinned script inherits whatever ran last |
| `check_registration_pins.sh` | the REGISTRATION guard, same CI/pre-release slot: every emitted `register` pins `-transf=homography` and every emitted resample pins `-interp=lanczos4`, with `-noclamp` absent everywhere (clamping is a default that only an off-switch can lose). Both flags are Siril DEFAULTS, so unpinned they are a version-supplied input to every stack. Judged per COMMAND, not per file — it parses the emitted lines out of every `.ssf` and `.ssf` emitter; `--selftest` falsifies the rules against fixture commands. One exemption: `run_lunar_pipeline.sh`'s explicit `-interp=none` |
| `qa/run_guards.sh` | **the RUNNER for every guard above — the CI slot they were written for and did not have.** Five guards existed and NOTHING executed them, which is how a register row calling one of them broken outlived its fix by three days. Runs 24 checks (the eight `check_*.sh` plus every data-free instrument `--selftest`), reports each with its duration, prints a failing check's last 15 lines, exits non-zero if any fails; `--list` shows the roster without running it. **MEASURED: 24 passed, 0 failed** — cheap enough that there is no cost argument against running it routinely, which is the point. **THE WALL TIME IS DELIBERATELY NOT A LITERAL HERE, and that is a finding rather than an omission: four figures for it have been published in this repo and NO TWO AGREE** — a 27-to-33 band, an about-30 point estimate, a 44-to-48 band and a 41-to-43 band, each one a session quoting the spread of ITS OWN runs as the quantity's range. (Those four are written out in words on purpose: a record that retracts a literal by PASTING it becomes a hit for every sweep looking for live instances of it — the registry's own rule, applied here so `grep -F` for any of the four returns zero.) The runner PRINTS its own wall time and every check's duration on every run, so read the live figure from the artifact — the same treatment `scripts/setup/hooks/pre-push` already gives the check COUNT, for the reason it states there: a quantity with several homes and no guard goes stale by default. **The run-to-run spread is UNATTRIBUTED.** An earlier revision of this cell blamed roster growth over contention and sized `pa_convention` at 9 to 14 s; neither half is supported — one session has ruled load out (its fastest run carried its highest load), the `[network]` check measured dead flat at 18 s over four consecutive runs, and no session's own runs span the range the sessions collectively report. **It invokes shell guards as `./scripts/…`, never `bash scripts/…`, and that is not pedantry: `bash <path>` SIDESTEPS THE EXECUTABLE BIT.** Fire-tested both ways — with the bit removed from `check_stack_rejection.sh`, `bash` PASSES blind while the runner FAILS at exit 126; and a fixture emitting an unpinned `set16bits` drives `check_bitdepth` to exit 1 and the runner to RED, so a guard's own verdict propagates and not merely a failure to launch. **LIMITS, carried here because a runner that implies coverage it lacks is how a gap goes invisible: these guards verify WIRING, never OUTPUT — none can tell you a render is good; `check_bitdepth` is per-FILE and STATIC, so a builder already emitting `set32bits` in one generated `.ssf` passes even if a newly added emission omits the pin (a deliberate deferral — a per-emission parser would be fragile in a way worse than a stated limit); and one check reaches the NETWORK** (`starlight_preservation`'s ESA Gaia catalogue control), labelled `[network]` and run unconditionally — there is no `--skip` flag on purpose, since a conditional path nobody exercises is the defect class the runner exists to catch. Checks are EXCLUDED only with a reason named in the file rather than silently dropped (`member_separation` and `object_tilt_null` need live products, `check_solve_records`'s FULL run needs live products under the gitignored `web/results/` while its data-free `--selftest` IS rostered, and `x86_bootstrap --selftest-gaia` downloads a catalogue). **The `datasets/aug06/corner_work/*.py` selftests are NOT excluded as a class: `pa_convention` and `constancy_fit` are IN the roster, marked `[lib]`, by the deliberate exception `e939f26` landed for — the exclusion keys on what a file IS, not where it lives.** An earlier revision of this cell listed them as excluded, which understated coverage |
| `finish_render.sh` | finish a stack into the judgeable render: blind solve (`--central=` = the central FRACTION OF THE FRAME, seam guard for union canvases; the solve REFUSES a result contradicting the header's own pointing/scale, exit 9) → SPCC as one unit (`--session/--set` route the recipe spec + record naming) → linked autostretch → full-frame 16-bit PNG in `web/results/<session>/judge/` |
| `compose.py` | the convergence stage: resolves the composition record, drives the Siril align (mono-filters members to the reference member) and composes via Siril `rgbcomp` under `set32bits` — the tool owns the combine and the write; in-house guards are FITS-header-only (astropy: float32 contract, mono, geometry agreement) |
| `fitsmeta.py` | FITS acquisition-metadata probe for the dedicated-astrocam preflight (exposure/gain/offset/filter/mono); normalizes the free-text `FILTER` keyword to a canonical token and fails loud on a mixed dir |
| `siril/master_{bias,flat,dark}.ssf`, `siril/lights.ssf.tmpl` | siril stages for the matched-flat path |
| `run_session_chain.sh` | the ONE-CLICK durable-core chain for EVERY light set in a session — the session-level driver that routes each set by its fingerprint and runs `baseline_guard.py` last |
| `run_corpus_combine.sh` | THE FINAL COMBINE — every member from every night into one stack, then one finish. Skips arm variants and `set-00` by allow-list, not by a deny-list of the suffixes that happen to exist today |
| `calibrate_light.sh` | single source of truth for the light-frame calibration command, shared by every route so no caller can drift |
| `check_calibrate.sh` | the guard that every light calibration routes through that one command |
| `check_siril_invoke.sh` | the guard that every Siril invocation routes through `lib/siril_run.{sh,py}` |
| `build_master_dark.sh` | builds the session's MASTER DARK from raw `darks/`, driving the pinned Siril template; 32-bit, uncompressed, `setext` pinned |
| `compose_preflight.py` | compose preflight: STOPS before a union silently regresses to star-pair registration — the gate that makes the astrometric compose provable rather than assumed (removal-conditions register) |
| `stamp_headers.sh` | single source of truth for restoring the ACQUISITION FITS keywords the undistort TIFF round trip drops, and for stamping `PIPEREV` — which is why a commit landing mid-build is a second knob inside your own experiment |
| `backfill_substack_provenance.sh` | ONE-TIME backfill of optics/calibration provenance onto sub-stacks built before those keys existed; writes with a FITS library, never siril `update_key`, which truncates a string at the first `/` |

**`calibrate/`** — astrometric + photometric calibration

| file | role |
|---|---|
| `solve_field.py` | blind astrometric solve (astrometry.net) + TAN-SIP WCS injection — unblocks siril `spcc`; scale hint derived from the FITS header, foreground-masked star detection |
| `spcc_cone.py` | which local Gaia SPCC chunks a solved field needs (nside=2 nested HEALPix cover from the WCS) + `--fetch` to download the missing ones (md5-verified) — turnkey SPCC coverage for any field |
| `spcc_run.py` | siril SPCC runner that CAPTURES the K factors + star counts into `work/spcc_<set>.{json,log}` |

**`darktable/`** — the pinned UNDISTORT stage

| file | role |
|---|---|
| `lensdist.dtstyle`, `nodist.dtstyle` | the darktable lens-module styles: `lensdist` = module ENABLED, `nodist` = DISABLED (the one-knob control). The styles carry ONLY that bit — darktable ignores a style's lens `op_params` (modify_flags included) and re-detects the lens per image with its DEFAULT correction set (measured, `docs/dead-ends.md`); distortion-only is enforced in the lensfun DB by `install_lens_model.sh`. The `op_params` blob stays pinned for byte-reproducibility — never re-create it by hand in the GUI |
| `install_styles.sh` | installs them headlessly into a darktable configdir (darktable has no CLI style import, and only a real export job creates its `data.db`). Verified: from a fresh config the warp reproduces to 0.000 px |
| `fit_lens_model.sh` | fit THIS unit's radial distortion model from a set's own frames — Siril calibrates/stretches, Hugin (`cpfind`/`cpclean`/staged `autooptimiser`, hfov pinned at the solved value) fits between-frame star correspondences; prints ptlens a,b,c + the install command, records the fit to the set's `qa_work/lens_fit.json`. Run for a new lens/body/focal, or when the drift-axis stations show a centre band a DB profile cannot remove. PROVISIONAL as-written (the procedure it encodes was proven step by step; the script's first end-to-end run is the next fit) |
| `install_lens_model.sh` | installs the PINNED model for this lens@focal (`scripts/darktable/lens_models.json` — THE authority, keyed `<lens>@<focal>` because a model is a property of the LENS AND OPTICAL STATE, not of a dataset) into the live lensfun user DB AND strips that lens's `<vignetting>`/`<tca>`, the distortion-only enforcement point. A per-set fit is a CANDIDATE promoted by an explicit act, judged at the COMBINE. The per-set-as-authority variant is a registered dead end: one shared model is what every accepted combine here ever used, and per-set models measured 2.99 px corner disagreement within a night and 5.34 px across nights. Lens + focal come from the set's `acquisition.json`; the DB FILE is found by searching for the lens. Records what it replaced in an XML marker; a different fitted entry needs `--replace`, so a deliberately staged A/B is never undone silently (the chain does NOT pass it; the preflight stops on the mismatch and says so). Machine-local like `lensfun-update-data`, which WIPES the patch: the chain re-installs per run |
| `verify_lens_card.py` | proves darktable's lens correction is DISTORTION-ONLY on this rig — two synthetic fixtures, grid control (must differ) + uniform card (must not), because the uniform card ALONE is vacuous. Run every set by `lens_preflight --require-profile` |
| `cp_coverage.py` | control-point RADIAL COVERAGE of a hugin fit: does it constrain the CORNER? Imported, not invoked — the corner-support deficit is a matching problem, not a pruning one (`docs/dead-ends.md`) |

**`setup/`** — x86 bring-up

| file | role |
|---|---|
| `x86_bootstrap.sh` | fail-closed integrity-checked install of the x86 toolchain into `/opt` + a venv; the emitted inventory (versions, sources, checksums) is [`scripts/setup/manifest.tsv`](scripts/setup/manifest.tsv) |
| `requirements.txt`, `requirements-solve.txt`, `requirements-tools.txt`, `requirements.lock` | FOUR pinned dependency sets across TWO venvs, and the distinction is load-bearing — `TOOLS.md`'s `sip_tpv` correction turns on which interpreter a consumer resolves to, so name the venv with any availability claim rather than saying "that venv" |
| `install_hooks.sh`, `hooks/pre-push`, `hooks/prepare-commit-msg` | installs this repo's git hooks from tracked source — `.git/hooks/` is machine-local and untracked, so a fresh clone gets neither the guard runner (`pre-push`) nor the staged-numstat stamp (`prepare-commit-msg`) without it. Layer 0 of `x86_bootstrap.sh` |
| `install_astromatic.sh` | PSFEx and SCAMP, built from the Debian SOURCE packages (neither is a binary candidate here); invoked three times by `x86_bootstrap.sh` |
| `install_python_tools.sh` | the pinned Python TOOL layer, separate from the measurement layer, installable onto a rig's venv |
| `install_cosmicclarity.sh` | installs the Cosmic Clarity Suite to `/opt`, user-owned |
| `verify_site.py` | falsifies the tracked observing-site coordinates against the corpus's own solves — bounds them at the DEGREE level only (a flipped sign or a lat/long transposition puts a photographed target below the horizon; a transposed digit does not) |

**`ingest/`** — pull a capture session from the remote host, verified

| file | role |
|---|---|
| `remote_publish.sh` | the REMOTE half: publishes a capture directory for verified pull over HTTP, and is the SOURCE-SIDE HASH PRODUCER. **Evidenced by its output rather than by any caller** — 9 tracked `ingest_work/ingest.json` records name it, all reading `integrity: transfer-verified`; nothing in code or docs invokes it |
| `fetch_session.sh` | the LOCAL half of that pull. **UNCLEAR, and that is the verdict rather than a gap** — no caller, no doc, and no record it left behind. Absence of evidence is exactly what the output-evidenced case warns against, so no purpose is invented for it here; the operator or the owner settles what it is |
| `link_heartbeat.sh` | watches the link to the remote publisher (reachability, latency, progress). **UNCLEAR on the same three counts** |

**`session_archive.sh`** (directly in `scripts/`) — archive a session's DERIVED
state (`datasets/<session>/`, `web/results/<session>/`, `sessions/<session>/work/`)
and optionally `--reset` the session to raw frames only. Never touches a raw frame
dir, and asserts the raw count is unchanged afterwards. The archive is a HOLDING
AREA for comparing a re-run against what preceded it — not a backup of record:
raws live off-rig, tracked records live in git, and an archive should be deleted
once its comparison is done. Root is `$ASTRO_ARCHIVE_ROOT` (default
`~/astro-archive/`), one timestamped dir per run, never overwritten. It exists
because resetting a session by hand was a cp/rm/git-rm sequence that kept leaving
gitignored scratch behind — `git rm` removes only what git tracks, so a "clean"
session still carried `qa_work/frameqa/*.seq` and `audit_work/_stars.lst` for a
fresh run to inherit.

**`makeSpace.sh`** (directly in `scripts/`) — MANUAL-RUN disk reclaim: clears the
VM's file-transfer staging cache (`~/.cache/vmware/drag_and_drop`), which keeps a
full duplicate of every file dragged into the guest. Run it by hand after
confirming a transfer landed; nothing in the pipeline invokes it.

**`render/` — no such directory; the render tier landed as
`stack/render_tier.sh`** (above), a thin orchestration over the tools. What
remains unbuilt is the LADDER around it (per-arm `exp_*` trees, the
no-regression harness, the `GENERIC.json` knob schema) — BACKLOG. The rest of
this paragraph described the plan and is kept for the tool inventory: it is a
thin orchestration over the natives verified present by on-rig probe
(`subsky`, `ght`/`autoghs`/`mtf`, `denoise`, `satu`, `unclipstars`, `pm`,
`rgbcomp`) plus the installed GraXpert — the pre-registered ladder is
BACKLOG:`render-ladder`, re-anchored per dataset by the operating loop. The
separation/neural tiers are INSTALLED (StarNet2, Cosmic Clarity, DeepSNR,
GraXpert under `/opt`); RC-Astro and PixInsight are uninstalled by choice
([`TOOLS.md`](TOOLS.md)).

**`web/`** (top-level, beside `scripts/`) — the local front end: `serve.py`
(127.0.0.1-only static server over the repo + the framing-record POST),
`index.html` (session/judge gallery — SELECTION surfaces, never judgment),
`crop.html` (the BACKLOG-item-12 framing UI), `make_previews.sh` (Siril-made
previews + manifest), `verify_framing.py` (mandatory Siril crop+stat check
before any render consumes a framing record). Contract + usage: `web/README.md`;
the durable output data tree lives beneath it at `web/results/<session>/`.

**`qa/`** — standing audits + diagnostics (WARN-only)

| file | role |
|---|---|
| `anomaly_audit.py` | transient-obstruction classifier (aircraft / satellite / unknown) over a frame set — the reference **ALLOWED** gap-filler: Siril does every pixel op + measurement (decode / green-extract / subsky / findstar), the in-house kernel does only the streak geometry + cross-frame linking no tool provides; report-only, removal-conditioned. Requires the declared `mount` (STOPS if absent), confines linking to capture runs (`segment_runs`); artifacts + the `anomaly_audit.json` record land in `datasets/<session>/<set>/audit_work/` |
| `inspect_stage.py` | orchestration + record: persists the TOOLS' per-frame measures (Siril `register`'s .seq regdata — FWHM px+arcsec, roundness, background, star count, shifts) into metrics.jsonl before cleanup, and writes the per-stage diagnostic sequence; the checklist reads the tools' numbers |
| `judgment_package.py` | assembles a judgment set from render FINALS (DORMANT pending the render rebuild): refuses starless layers (a hand-linked package once shipped starless PNG16s as finals), embeds the measured candidate-vs-`--control` deltas + an objective WIN\|NULL\|needs-eyes verdict (no "fixed/final/matched/close" language), writes the QUESTION.md skeleton. Two re-wires ride the rebuild: its PNG8+PNG16 pairing predates the 16-bit-ONLY judgment policy, and its `.metrics.json` producer (the old chain's renderer) no longer exists — BACKLOG |
| `cull_report.py` | frame-cull analysis over pooled per-frame registration records (WARN-only): robust-z defect-side flags at the calibrated threshold — reports candidates for a with/without cull ladder, never decides |
| `run_frame_qa.sh` | the per-set frame-QA driver: raw → CFA FITS → `register -2pass` (analysis pass only, disk-bounded batches, 1-frame-batch guard) → `inspect_stage` persists Siril's per-frame regdata → flattened records + `cull_report` flags + the tracked `frame_metrics.json`. The cull decision stays the user's, recorded in `recipe.json`'s stack block per the per-set policy. PROVISIONAL as-written (generalized from the driver that produced set-02's record; first fresh run = the next set's prep) |
| `star_shape.py` | orchestration + record: runs Siril `seqtilt` and records its report — off-axis aberration (centre vs corners = the RADIAL term) and sensor tilt (best vs worst corner = the ASYMMETRIC term). The tool's own spatial star-shape analysis and the only headless one (`tilt`/`inspector` are GUI-only); it computes nothing. Never re-derive this by binning a `findstar` list by radius — that is circular and fails silently (`docs/dead-ends.md`, trap 3) |
| `star_stations.py` | orchestration + record: Siril `crop` + `findstar` (open gate) at fixed equal-area stations along/perpendicular to the measured drift axis — the band measure `seqtilt` cannot see (a drift-aligned defect leaves centre-vs-corners clean while the centre station degrades); geometry is fixed and EXTERNAL (geometric centre + the solves' drift axis) so the trap-3 circularity cannot bite; records medians of the tool's own per-star fits, removal-conditioned on a tool shipping a headless local star-shape map |
| `coverage_probe.sh` | per-pixel COVERAGE MAP for any sub-stack compose (the framing instrument): register the real members, swap in `fill` constant twins, apply the STORED transforms, `stack sum` → value/1000 = members covering each pixel. Measured: `-framing=min` keeps 36% of the true common area on rotated members; coverage-thresholded crops verify against this map (`stat` Min ≥ threshold — also the numpy-vs-Siril crop y-flip guard, `docs/dead-ends.md`) |
| `snr_regions.py` | normalization-invariant regional SNR: (signal − sky region mean) / `bgnoise`, computed WITHIN each stack (per-stack `-output_norm` cancels); boxes WCS-anchored so the same sky is measured in every stack. Removal condition: a tool exposing headless regional SNR |
| `noise_split.sh` | background-noise composition: half-split difference over a compose's sub-stacks (one registration; A−B cancels all static content) — interleaved split reads pure RANDOM σ, timehalf excess reads the drift-phase STRUCTURED component (the walking-noise measure). Measured: random σ scales √N exactly; the visible background is floored by depth-independent structure |
| `baseline_guard.py` | PRODUCT-level no-regression guard, run last by `run_set_chain.sh`: Siril `stat` (via `regional_stat.py`) on the finished linear stack — corner spread, edge dipole, per-channel centre level — compared against the baseline a human ACCEPTED for that set. A regression exits **8**, a user decision like the mount/route stops; nothing is blocked or rewritten. Every other guard here checks WIRING, which is why a 31x background regression once shipped with every wire intact. NOT a quality gate: it has no opinion about whether a render is good, and a deliberate improvement fails it (re-seed with `--reseed` and a note). Its measures are stack CORNERS, so it is blind to a flat that absorbed the sky gradient — a PASS is not evidence the calibration is clean |
| `regional_stat.py` | Siril `stat` regional medians (centre + 4 corners, per channel) on a LINEAR stack — the gradient instrument (never read gradients off a stretched surface — `docs/dead-ends.md`) |
| `diag_flat.ssf` | master-flat diagnostic (Siril) |
| `readiness_report.py` | ONE readiness surface for a set — every ratified criterion evaluated up front, one report and one approval, so nothing undecidable surfaces three hours into a build (`CLAUDE.md`, "where the gate actually is") |
| `run_guards.sh` | THE RUNNER for every guard — see its row under `stack/` above |
| `check_removal_conditions.sh` | the REGISTER guard: every file declaring a `REMOVAL CONDITION` must appear in BACKLOG's divergence column. Detects declared-but-no-row only; blind to a divergence that declares nothing |
| `check_prompt_scope.sh` | the PROMPT-SCOPE guard: every `.md` in `prompts/` declares its KIND, and the ceilinged kinds stay under their size limit |
| `check_manifest_verify.sh` | the INVENTORY guard: every `verify` command in `scripts/setup/manifest.tsv` must actually run |
| `check_solve_records.py` | joins every plate-solve RECORD against the ARTIFACT it names — compares the record's field CENTRE against the target's own WCS at the centre pixel, never `CRVAL` |
| `coverage_frame.py` | proposes the VERIFIED COVERAGE FRAME of a `framing=max` union — the largest all-covered rectangle over Siril `stat` boxes. Reports only; crops nothing |
| `member_separation.py` | measures how much a compose's MEMBERS disagree about where a star is, binned by each star's own field radius. Measures, does not gate (`docs/combine-contract.md` §5) |
| `shape_at_sky.py` | records Siril `findstar` PSF fits in boxes placed at SKY positions by the solved WCS, so products of different framing are comparable |
| `grid_ramp.py` | fits the low-order background RAMP over a grid of Siril `stat` boxes — the reproducible alternative to a four-corner spread on a structured field |
| `flat_odd_component.py` | measures a sky flat's ODD component about frame centre, and the RATIO of two flats, over Siril `fdiv` + `stat` (never `idiv`, which clips at 1.0) |
| `flat_differential.py`, `flat_differential_arms.sh`, `flat_differential_report.py` | how much of two flats' DIFFERENCE reaches the delivered object — the differential form that survives both blockers of the absolute measurement |
| `object_tilt.py`, `object_tilt_control.py`, `object_tilt_null.sh`, `object_tilt_corpus.py` | the catalogue-free object-tilt measurement with its positive, identity and NULL controls, and the corpus aggregation that tested its pre-registered prediction. **The route is a registered DEAD END** — kept because the controls are what killed it |
| `fit_ptlens_joint.py` | JOINT refit of ptlens (a,b,c) AND the distortion centre against a plate solution, with a PROJECTIVE nuisance — an affine one manufactures a decentring signal |
| `mount_probe.sh` | TWO-WINDOW mount drift probe, both windows confined to one contiguous capture run (dir-endpoint windows measure re-aim + drift, which is neither mount signature) |
| `observer_frame_diversity.py` | regenerates `datasets/corpus/observer_frame_diversity.json` — the camera's alt/az diversity across the corpus, deriving each group's epoch from the drift rather than its frozen `DATE-OBS` |
| `pergroup_flat_report.py` | rolls the per-group flat-window arms into ONE record against the prediction committed before the arms ran |

**`qa/pergroup/`** — the flat-window A/B arms (build → compose → measure, one knob: which flat calibrates each group's 100 frames). **It carries its own tracked `scripts/qa/pergroup/README.md` and is deliberately NOT restated here** — a second home is a second place to drift. Its five scripts derive `REPO` from their own location like the rest of `scripts/`; the TARGET SET (`july31`/`set-03`) stays hardcoded on purpose, because they are the record of one measurement rather than reusable tooling.

## Data layout

Three stores, joined by the session name — each a different lifecycle:
`sessions/` is TRANSIENT staging (raws re-stage from off-rig; freed when a
set's chain completes), `web/results/` is the DURABLE output tree (servable
by the local web front end), `datasets/` is the TRACKED record.

```
sessions/<session>/  one acquisition session (transient staging, gitignored)
  biases/ darks/ flats/ darkflats/       calibration (darkflats = the FITS path's
                                         matched darks for the flats)
  calib/                                 OR prebuilt master calibration for
                                         master-only corpora (FITS sets only):
                                         {dark,flat}_<filter-token>.fits, matched
                                         by the normalized FILENAME token (such
                                         masters carry no headers); raw dirs win
                                         when both exist
  <set>/                                 lights: camera raw (NEF/DNG/CR2/…) or
                                         dedicated-astrocam FITS (all ignored)
  work/                                  masters, caches, generated scripts
                                         (the session tree is raws + work ONLY)
web/                                     the local front end (code TRACKED)
  index.html, crop.html, serve.py, …     session browser + the framing/crop UI
                                         (serve.py binds 127.0.0.1 only)
  results/<session>/                     DURABLE derived outputs (gitignored):
                                         stack_<set>_<recipe-tag>[_wcs|_spcc].fit
                                         render_<set>_<recipe-tag>.fit  (RENDER-TIER
                                           products live in their OWN namespace: a
                                           render is not a stack, carries no frame
                                           count to confirm against a recipe, and
                                           must not be offered to solve/SPCC as if
                                           it were one)
                                         exp_*/, inspect_*/,
                                         judge/ (judgment surfaces — image data),
                                         previews/ (tool-made selection
                                         downscales for the browser — NEVER a
                                         judgment surface)
datasets/<session>/<set>/                tracked per-dataset RECORDS ONLY (no image data):
                                         acquisition.json, geometry.json, recipe.json,
                                         baseline.json, composition.json, experiments.jsonl,
                                         qa_work/*.json, audit_work/anomaly_audit.json
                                         (see datasets/README.md)
scripts/                                 the pipeline (tracked)
```

## Adding a dataset

0. **If the corpus ships a reference finish** (`<session>/reference/`, the
   answer key), STUDY IT BEFORE tuning any look: like-scale/like-orientation
   comparison notes, and — when the author's processing is documented or their
   tool is open — recover the actual recipe/mechanisms first (measured lesson:
   two judgment rounds were burned tuning toward an unstudied reference whose
   maker's recipe was published in the dataset's own repo).
1. Lay it out as a session dir: `sessions/<session>/{darks,flats,biases,darkflats}/`
   (calibration, each an internally-uniform group) + one `<session>/<set>/` per
   single-pointing light set. Any siril-readable camera raw works with no
   conversion, as do dedicated-astrocam **FITS** frames (`darkflats/` = darks
   matched to the flat exposure). A master-only corpus stages prebuilt masters
   as `sessions/<session>/calib/{dark,flat}_<token>.fits` instead (FITS sets only; the
   normalized filename token is the identity — such masters carry no headers).
2. `scripts/stack/run_pipeline.sh sessions/<session> <set>` — forks on the data class
   (camera raw vs FITS) → `stack_<set>.fit` (matched-flat path; a flatless set
   hard-stops — synthetic-flat is a gap, BACKLOG).
   Flats match lights by filter on the FITS path; mono lights never debayer.
   A wide-field UNTRACKED set uses `run_undistort_pipeline.sh` instead (the
   undistort class), after the per-set prep: `run_frame_qa.sh` + the anomaly
   audit → the cull policy → the ratified `recipe.json` stack
   block the builder consumes.
3. Plate-solve (`solve_field.py`) → SPCC (`spcc_run.py`) → render (UNBUILT,
   user-gated — BACKLOG:`render-ladder`; the toolkit map is `TOOLS.md`).
   A **mono** (single-filter) set skips SPCC and renders luminance-only.
4. A set with no `datasets/<session>/<set>/` state **degrades loudly**
   (whole-frame gate, no foreground mask, GENERIC knobs, printed as such) —
   safe, just generic. Add `geometry.json` once solved, pin a `recipe.json`
   when a look is chosen, and record the no-regression baseline (rides the
   render-tier build).
