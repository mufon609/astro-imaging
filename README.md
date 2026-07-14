# Astrophotography processing pipeline

> **⚠ MID-RESET to x86.** The durable core — calibrate → register → stack →
> solve → SPCC → compose — runs today. The final **render is a GAP pending
> x86**: a per-dataset toolkit of official tools (StarXTerminator / native
> StarNet, NoiseXTerminator / GraXpert / Cosmic Clarity, BlurXTerminator, Siril
> `synthstar`/`rgbcomp`/natives — [`TOOLS.md`](TOOLS.md)), built in the order in
> [`docs/x86-empirical-test-plan.md`](docs/x86-empirical-test-plan.md). The
> process contract, review contract, acceptance model, experiment discipline,
> per-dataset state, and north star below are all portable and stand.

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
chain + the old NOTES.md are at the `checkpoint` commit). Each dataset's
approved recipe lives in `datasets/<session>/<set>/recipe.json` (see
"Per-dataset state" below).

## The reference standard

The industry deep-sky workflow (PixInsight/Siril practice) that this pipeline
follows, in order — linear until step 6:

| # | standard step | our implementation | status |
|---|---|---|---|
| 1 | calibrate (bias/dark/flat) → register → integrate; per-frame quality assessment (SubframeSelector/weighting) | `run_pipeline.sh`: masters + per-set calibrate → 2-pass/sweep register → 32-bit rej stack; per-frame quality MEASURED at registration on every path (`inspect_stage.py` reg: .seq regdata distribution + outliers, WARN-only, records persisted before cleanup); weighting/culling POLICY = the optional per-dataset `"stack"` recipe block (`-weight=wfwhm\|nbstars`, exclude via `unselect`+`-filter-incl`), resolved by run_pipeline at stack time with provenance printed — ABSENT block is the generic default (unweighted `rej 3 3`, byte-identical generated scripts) | COMPLIANT (matched darks/biases; flats when optics match; frame QA measured + policy surface per-dataset only: siril's `-weight` is a min-max ramp = SOFT-CULLING (it drives the worst frame toward zero weight at any spread, adding sky noise for no crispness gain at low spread) — weighting stays off generically, adopted only through a measured ladder on a recorded trigger) |
| 1b | — | **flatless sets** — the in-house numpy self-flat branch was REMOVED; a set without a matching flat loudly STOPS | GAP — fill with a real flat (primary) or an official synthetic flat (GraXpert `-correction Division`, BACKLOG), never an in-house fit |
| 1c | multi-channel targets: dual-band OSC line extraction (the standard Ha/OIII workflow) and mono filter-wheel channels, composed to one linear stack | `composition.json` routes it: `dualband-osc` — CFA calibrate → `seqextract_HaOIII -resample=oiii` (honest half size, no invented detail) → same-reference per-line stacks; `mono-filters` — sibling per-filter sets aligned to the composition's reference member (one interpolation pass). Both: `compose.py` palette compose (channel alignment measured, bound 1.0 px) → SPCC (narrowband mode per recipe where lines demand it) | COMPLIANT (2× drizzle full-size dual-band variant + LRGB post-stretch L-join still BACKLOG) |
| 2 | linear gradient removal on the stack, star-ful (DBE/GraXpert) | `bgelin_mode`: `gx` = GraXpert BGE + `subsky 1`, star-ful (generic); `plane` = `subsky 1` only — the retention mode for fields that ARE mostly object | COMPLIANT — order measured MW-safe; BGE on starless ERASES the MW (never reorder). CLASS LIMIT: a full extraction model cannot distinguish frame-filling faint nebulosity from a sky gradient and absorbs it — a plane keeps that signal (it removes only the first-degree gradient) and still clears the gate's gradient class |
| 3 | photometric color calibration (SPCC/PCC via plate solve) | `solve_field.py` (blind astrometry.net solve, WCS inject) + `spcc_run.py` (siril `spcc` with local Gaia catalogs, K factors captured to `work/spcc_<set>.{json,log}`) → `stack_<set>_norgbeq_spcc.fit` | COMPLIANT — SPCC calibrates the raw stack directly; spcc rerun measured pixel-deterministic. Canonical chains order BGE before SPCC; running SPCC before or after background extraction gives the same star-colour fit — per-star local-annulus photometry cancels the smooth background. SPCC is BROADBAND-only: a mono/single-filter set skips it (no colour to calibrate) |
| 4 | deconvolution (optional, data permitting) | skipped | COMPLIANT-SKIP — measured dead end on this data (in-exposure trailing, PSF unstable on ≈0 background) |
| 5 | linear noise reduction | PENDING x86 — a tool step | On x86 this is a real tool (NoiseXTerminator / GraXpert / Cosmic Clarity — the chroma-noise gap closes, `docs/dead-ends.md`). The old "radial noise after self-flat V(r) division" dead-end retired with the self-flat branch |
| 6–8 | star separation → stretch (starless hard / stars gently; narrowband per-line + palette colour) → recombine + export | **GAP (pending x86)** — a per-dataset tool toolkit: StarXTerminator / native StarNet (separation), NoiseXTerminator / GraXpert / Cosmic Clarity (denoise — closes the coring gap), BlurXTerminator (deconv), siril `synthstar`/`unclipstars` (stars), `rgbcomp` (recombine). Build order: `docs/x86-empirical-test-plan.md` | PENDING x86 |

Principles that keep this honest:

- **The mapping above is re-verified against current Siril/PixInsight
  doctrine at every siril MAJOR-version bump** (e.g. 1.4→1.6), plus a
  **changelog scan** on point releases that re-audits only a stage a release
  actually touches (stretch guidance, SPCC modes, separation/drizzle models) —
  tool positions move, so the comparison is standing work, not a one-time audit;
  a full re-audit every *minor* version is over-frequent and gets skipped.
  Per-item verifications carry their dates in the BACKLOG entries they feed.

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
   whole-frame lossless images (PNG16 + PNG8) with clean names and a
   QUESTION.md, nothing else: no crops, no composited panels, no lossy
   surface — the judge pulls each file into their own viewers and
   environments. Assemble it with `judgment_package.py` (orchestration +
   record: it verifies every PNG8+PNG16 pair pixel-wise for export integrity
   before linking — never by hand, embeds the tool-reported candidate-vs-control
   deltas + an objective WIN|NULL|needs-eyes verdict, writes QUESTION.md).
   Crops/panels (`judgment_crops.py`) are an on-request supplement,
   never the judgment surface. Objective fixes with tool pass/fail metrics may
   commit; recipe/aesthetic changes require the user's visual approval
   before they are baked as defaults.

   **Pre-handoff inspection is mandatory** (measured failure: two
   packages in a row shipped defects the assembler had not seen — a
   faint-dust allocation gap, then coring-mottle "blotch" visible at
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
   demanding one is the wrong bar on the tool-first x86 chain: its multi-threaded
   neural inference (RC-Astro BXT/NXT/SXT, Cosmic Clarity, StarNet) uses ONNX
   reductions that are often not bit-reproducible, so byte-identity would fail a
   *correct* render — and it already cost `subsky` its `-dither` (anti-banding
   sacrificed to the check; re-enable it). Verify **cheaply** (a fast canary + the
   deterministic orchestration, not a doubled full-res render) to a documented
   **tolerance**: byte-identity where a tool actually gives it (siril native
   single-thread, deterministic float32 temp-FITS round-trips), reproducibility
   within a tolerance negligible vs the metrics we judge on where it can't (a
   stage that varies above that tolerance is flagged and pinned to deterministic
   settings — single-thread / fixed device — if it can be). This extends the
   existing **STACK exemption** (its register sweep is already non-deterministic →
   verified by gate + inspection, not bytes) to the neural render tools. The
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
   render — a GAP pending x86; the no-regression standard is binding now,
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
path is linear FITS end to end: 32-bit float stacks/products, with ONE
documented precision reduction — 16-bit stack-time intermediates
(quantization measured ≈18× below per-frame noise, ~+0.3% stack noise).
Lossy/display files exist ONLY as OUTPUT surfaces: a lossy preview jpg
(never a judgment surface), the q100/4:4:4 final jpg, and judgment panels. GUARDS keep it that way: processing loads
go through `astrometrics.load_linear` (refuses non-FITS) and `compose.py`
asserts float32 inputs.
Human judgment uses the LOSSLESS artifacts: `--lossless` exports PNG8 +
PNG16 for the final **and the starless layer** (PNG8 = the 8-bit display
pixels; PNG16 = the float layer at 65536 levels).
Never judge a q92 surface. Finals carry EMBEDDED sRGB COLORIMETRY (JPEG
ICC + PNG sRGB/gAMA/cHRM chunks): the render's display-referred output is
sRGB-companded (siril's autostretch/mtf/satu operate in display RGB), so
the tag declares that instead of leaving viewers to assume it — pixels
untouched, profile vendored at `scripts/lib/srgb.icc` with timestamp/ID
zeroed for byte-determinism.

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
  `results/exp_<param>_<stamp>/`, appended to the tracked per-dataset
  `experiments.jsonl`, and STOPs for user judgment. (The ladder that automates
  this rides the render — a GAP pending x86; the discipline is binding now.)
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

### New-class triage (BEFORE the first judgment package)

The GENERIC layer was tuned on specific data classes and a knob correct
there can silently damage another class until a human notices the defect
(measured twice: post-stretch vst crushed 40–50% of a high-SNR nebula's
chroma across four judged renders; the linked stretch drowned a
narrowband target's O3 sphere). When a dataset CLASS first arrives (new
sensor class, new SNR regime, new target-brightness class, new
composition kind), ladder the generic knobs whose `datasets/GENERIC.json`
why-notes name a class risk — that file is the checklist's source of
truth; today: `bgelin_mode` (the proven signal eater: full AI
background extraction absorbs frame-filling faint nebulosity — trace
object-region retention stack→bgelin before trusting any faint-object
render), `starless_denoise` (the proven chroma killer — the tool VST/GX
denoise strength, now the only sky-noise lever since the numpy corings
were removed), `black_point` (crushes faint extended signal),
`starless_target` (darker than necessary on clean data), `stars_peak`
(blows star tops on deep data), and `stretch_linked` (linked vs the
per-channel measurement rung). Each is a single-knob ladder the harness
already runs; the user judges once per class instead of debugging after.
(Narrowband-palette colour is not laddered here — the star-neutral colour
balance is a GAP, `docs/dead-ends.md`.)

## Per-dataset state (`datasets/<session>/<set>/`, tracked)

Session data dirs are gitignored (several hold third-party raws that must
never be committed), so everything the repo versions about a dataset lives
in `datasets/<session>/<set>/` — see `datasets/README.md` for the contract:

- `geometry.json` — the only per-set **composition fact**: the terrestrial
  **foreground** (`rect` fractions or a derived pixel-`mask` npz, session-
  relative) plus `judgment_crops` and optional `starsep` overrides. Resolved
  by `astrometrics.configure()` in the entry points that need it (inspect_stage,
  judgment_crops, solve_field, compose). No file: foreground **none** (whole
  frame is eligible sky).
  A new set NEVER inherits another set's foreground silently. A configured
  foreground must TOUCH A FRAME BORDER (terrestrial obstructions are
  border-anchored by construction; the foreground is excluded from the
  gate's sky scope, so a floating interior one would carve graded sky out
  of the gate's jurisdiction) — refused loudly at configure time.
- `recipe.json` — the processing knobs: the `render` dict (the render chain
  resolves CLI > recipe > `datasets/GENERIC.json` and prints the provenance; a
  dataset with no recipe renders data-class-blind generic and says so — the
  render dict's schema is PENDING x86) plus the optional `spcc` spec
  (sensor/filter names or narrowband wavelengths, same resolution order in
  `spcc_run.py`). An **approved** recipe pins every knob so a later
  generic-default change cannot silently restyle it.
- `GENERIC.json` (one per repo, beside this contract's per-set dirs) —
  the tracked base layer every render inherits: the generic value AND a
  per-knob "why" note naming what it encodes (most were measured on one
  underexposed DSLR wide-field) and its known class limits. Tweakable at
  any time — but a change restyles every non-approved dataset, so it
  lands as a declared delta. The knob SCHEMA stays in code; the render chain
  hard-fails on any file/schema drift (pending x86).
- `baseline.json` — the measured no-regression record (pinned stack sha,
  expected tool measures, artifact hashes), written only by the no-regression
  harness (pending x86).
- `composition.json` — only for multi-line/multi-filter targets: how the
  composed linear stack is BUILT (kind, extraction, lines, palette
  channel mapping). Absent = ordinary single-stack set.
- `experiments.jsonl` — the tuning-experiment ledger (append-only): one
  record per ladder (param, values, control, hypothesis, pinned stack,
  verdict), closed by `--verdict`. The durable tracked index of what was
  tried; heavy per-value finals stay in gitignored `results/exp_*/`.

The background is NOT a per-set composition fact: the gate selects its sky
STATISTICALLY (dark blocks, foreground excluded — see the review contract),
so no galactic band or object region is ever configured per set (a bright
object has no fixed geometry a mask could scope — see `docs/dead-ends.md`).

A rectangular foreground (`rect`) covers most terrestrial obstructions; a
non-rectangular pixel `mask` npz is still honoured by `geometry.json`, but the
in-house mask-DERIVATION tool was removed (it read the stack pixels). Deriving a
mask is now a documented gap — an official tool or a hand-drawn mask, never an
in-house fit.

## Running it

```bash
# full pipeline (session dir, set name; ~15 min)
scripts/stack/run_pipeline.sh <session> <set>

# color-calibrate the stack once per stack rebuild (~1 min, local catalogs)
python3 scripts/calibrate/solve_field.py <session>/results/stack_<set>.fit \
    --inject=<session>/results/stack_<set>_wcs.fit
# NEW FIELD: make sure the local Gaia chunks cover it before SPCC (a southern
# field needs southern chunks); --fetch downloads any missing ones
python3 scripts/calibrate/spcc_cone.py <session>/results/stack_<set>_wcs.fit --fetch
# then siril spcc (spcc_run.py) → _spcc.fit

# final render — a GAP pending x86 (tool toolkit: TOOLS.md; build order:
# docs/x86-empirical-test-plan.md). Everything ABOVE (stack → solve → spcc →
# compose) is the durable core and runs today.
```

Environment specifics (siril invocation, catalogs, GraXpert, the x86 target)
live in CLAUDE.md "Environment".

## Repo map (`scripts/`, by stage directory)

**`lib/`** — shared FITS-I/O + per-set geometry helper, imported via the walk-up bootstrap

| file | role |
|---|---|
| `astrometrics.py` | shared FITS/PNG I/O + per-set foreground geometry (`branch_mask`) — no in-house pixel analysis, the tools measure (the hand-rolled I/O itself moves to astropy/Siril — BACKLOG) |

**`stack/`** — build the integrated stack

| file | role |
|---|---|
| `run_pipeline.sh` | stack builder: preflight → masters → calibrate → register (2-pass/sweep) → rejection stack; forks camera-raw vs dedicated-astrocam FITS, loudly STOPS a flatless set demanding a matching flat (synthetic-flat is a documented gap — BACKLOG), and routes a `composition.json` dual-band set through line extraction → same-reference per-line stacks → compose |
| `compose.py` | the convergence stage: per-line / per-filter member stacks → ONE composed linear colour stack per the composition record's palette mapping (mono-filters members aligned to the reference member by Siril first). Its channel combine + FITS I/O should move to Siril `rgbcomp` — BACKLOG |
| `fitsmeta.py` | FITS acquisition-metadata probe for the dedicated-astrocam preflight (exposure/gain/offset/filter/mono); normalizes the free-text `FILTER` keyword to a canonical token and fails loud on a mixed dir |
| `crop_coverage.py` | crop a drift-composited stack to its coverage-complete rectangle; replaceable by Siril `seqapplyreg -framing=min` — BACKLOG |
| `siril/master_{bias,flat,dark}.ssf`, `siril/lights.ssf.tmpl` | siril stages for the matched-flat path |

**`calibrate/`** — astrometric + photometric calibration

| file | role |
|---|---|
| `solve_field.py` | blind astrometric solve (astrometry.net) + TAN-SIP WCS injection — unblocks siril `spcc`; scale hint derived from the FITS header, foreground-masked star detection |
| `spcc_cone.py` | which local Gaia SPCC chunks a solved field needs (nside=2 nested HEALPix cover from the WCS) + `--fetch` to download the missing ones (md5-verified) — turnkey SPCC coverage for any field |
| `spcc_run.py` | siril SPCC runner that CAPTURES the K factors + star counts into `work/spcc_<set>.{json,log}` |

**`render/`** — **GAP, pending x86.** The render is a thin orchestration over
official tools, picked per dataset ([`TOOLS.md`](TOOLS.md)): StarXTerminator /
native StarNet (separation), NoiseXTerminator / GraXpert / Cosmic Clarity
(denoise), BlurXTerminator (deconv), Siril `autostretch`/`mtf`/`pm`/`satu`/
`synthstar`/`rgbcomp` (stretch / stars / recombine). Build order:
[`docs/x86-empirical-test-plan.md`](docs/x86-empirical-test-plan.md).

**`qa/`** — standing audits + diagnostics (WARN-only)

| file | role |
|---|---|
| `inspect_stage.py` | orchestration + record: persists the TOOLS' per-frame measures (Siril `register`'s .seq regdata — FWHM px+arcsec, roundness, background, star count, shifts) into metrics.jsonl before cleanup, and writes the per-stage diagnostic sequence; the checklist reads the tools' numbers |
| `judgment_package.py` | assembles a judgment set from render FINALS: verifies each PNG8+PNG16 pair pixel-wise before linking (a hand-linked package once shipped starless PNG16s as finals), refuses starless layers, embeds the measured candidate-vs-`--control` deltas + an objective WIN\|NULL\|needs-eyes verdict (no "fixed/final/matched/close" language), writes the QUESTION.md skeleton |
| `cull_report.py` | frame-cull analysis over pooled per-frame registration records (WARN-only): robust-z defect-side flags at the calibrated threshold — reports candidates for a with/without cull ladder, never decides |
| `judgment_crops.py` | fixed defect-zone 1:1 crop panels for user judgment |
| `diag_flat.ssf` | master-flat diagnostic (Siril) |

## Data layout

```
<session>/           one acquisition session (any directory name)
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
  results/                               stacks, renders, exp_*/, inspect_*/
datasets/<session>/<set>/                tracked per-dataset state: geometry.json,
                                         recipe.json, baseline.json, composition.json
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
1. Lay it out as a session dir: `<session>/{darks,flats,biases,darkflats}/`
   (calibration, each an internally-uniform group) + one `<session>/<set>/` per
   single-pointing light set. Any siril-readable camera raw works with no
   conversion, as do dedicated-astrocam **FITS** frames (`darkflats/` = darks
   matched to the flat exposure). A master-only corpus stages prebuilt masters
   as `<session>/calib/{dark,flat}_<token>.fits` instead (FITS sets only; the
   normalized filename token is the identity — such masters carry no headers).
2. `scripts/stack/run_pipeline.sh <session> <set>` — forks on the data class
   (camera raw vs FITS) → `stack_<set>.fit` (matched-flat path; a flatless set
   hard-stops — synthetic-flat is a gap, BACKLOG).
   Flats match lights by filter on the FITS path; mono lights never debayer.
3. Plate-solve (`solve_field.py`) → SPCC (`spcc_run.py`) → render (a GAP
   pending x86 — the tool toolkit, `TOOLS.md`). A **mono** (single-filter) set
   skips SPCC and renders luminance-only.
4. A set with no `datasets/<session>/<set>/` state **degrades loudly**
   (whole-frame gate, no foreground mask, GENERIC knobs, printed as such) —
   safe, just generic. Add `geometry.json` once solved, pin a `recipe.json`
   when a look is chosen, and record the no-regression baseline (pending x86).
