# Astrophotography processing pipeline

This repo tracks the **process** (Siril/Python scripts + notes), never image
data (`.gitignore`). `NOTES.md` is the lab notebook: every measured lesson,
every dead end with its numbers. This file is the **process contract**: what
each step is for, what the industry standard does there, where we diverge and
why, and how every step is reviewed.

**New contributor start here:** (1) this file top to bottom; (2)
`NOTES.md` top to bottom — it is deliberately short: STATUS (current
state + reproduce contracts), the current design with every knob's
measured WHY, and the **DEAD ENDS registry** (read it before
proposing ANY experiment — if it was tried, its killing number is
there). Full chronological history lives in git (`git log`; every
commit carries the NOTES of its time). Each dataset's approved recipe
lives in `datasets/<session>/<set>/recipe.json` (see "Per-dataset
state" below); the corridor-era `B5/B6/B7-approved` tags are history.

## The reference standard

The industry deep-sky workflow (PixInsight/Siril practice) that this pipeline
follows, in order — linear until step 6:

| # | standard step | our implementation | status |
|---|---|---|---|
| 1 | calibrate (bias/dark/flat) → register → integrate | `run_pipeline.sh`: masters + per-set calibrate → 2-pass/sweep register → 32-bit rej stack | COMPLIANT (matched darks/biases; flats when optics match) |
| 1b | — | **self-flat branch** for sets without a matching flat (median → V(r) isotonic gray gain → rechroma → V2 divide; per-frame planar glow subtraction) | ADAPTATION — dies when real flats exist at the set's focal length (preflight auto-routes) |
| 1c | multi-channel targets: dual-band OSC line extraction (the standard Ha/OIII workflow) and mono filter-wheel channels, composed to one linear stack | `composition.json` routes it: `dualband-osc` — CFA calibrate → `seqextract_HaOIII -resample=oiii` (honest half size, no invented detail) → same-reference per-line stacks; `mono-filters` — sibling per-filter sets aligned to the composition's reference member (one interpolation pass). Both: `compose.py` palette compose (channel alignment measured, bound 1.0 px) → SPCC (narrowband mode per recipe where lines demand it) | COMPLIANT (2× drizzle full-size dual-band variant + LRGB post-stretch L-join still BACKLOG) |
| 2 | linear gradient removal on the stack, star-ful (DBE/GraXpert) | `bgelin_mode`: `gx` = GraXpert BGE + `subsky 1`, star-ful (generic); `plane` = `subsky 1` only — the retention mode for fields that ARE mostly object | COMPLIANT — order measured MW-safe; BGE on starless ERASES the MW (never reorder). MEASURED CLASS LIMIT: a full extraction model absorbs frame-filling faint nebulosity (75–98% of the Bubble complex; the reference author runs no extraction at all) — a plane keeps 93–97% and still clears the gate's gradient class |
| 3 | photometric color calibration (SPCC/PCC via plate solve) | `solve_field.py` (blind astrometry.net solve, WCS inject) + `spcc_run.py` (siril `spcc` with local Gaia catalogs, K factors captured to `work/spcc_<set>.{json,log}`) → `stack_<set>_norgbeq_spcc.fit` | COMPLIANT — SPCC calibrates the raw stack directly; spcc rerun measured pixel-deterministic. Canonical chains order BGE before SPCC; running SPCC on the un-BGE'd stack is measured harmless (K moves ≤0.3% on the strongest-gradient field on hand — NOTES knob table). SPCC is BROADBAND-only: a mono/single-filter set skips it (no colour to calibrate) |
| 4 | deconvolution (optional, data permitting) | skipped | COMPLIANT-SKIP — measured dead end on this data (in-exposure trailing, PSF unstable on ≈0 background) |
| 5 | linear noise reduction | none linear | MEASURED DEAD END on self-flat data: any noise-adaptive linear denoise imprints a radial signature (noise is radial by construction after V(r) division). Post-stretch `-vst -mod=0.5` on the starless render is the working replacement |
| 6 | star separation (StarNet/StarXTerminator) | `starnet_sep.py` StarNet2-ONNX on aarch64, run LINEAR under an invertible MTF pre-stretch (the vendor-sanctioned placement) — the generic default (`sep_engine auto` → `net` when the weights are installed). `starsep.py` mask+inpaint is the WEIGHTS-ABSENT FALLBACK: it destroys resolved-object structure (measured: 26% of M74's detections were HII knots) and warns when it measures that risk. A recipe pins the engine only on measurement (one exists: wide_50mm, where net fails the gate) | COMPLIANT (learned separator, standard placement); fallback is the documented adaptation |
| 7 | stretch starless hard / stars gently; narrowband palettes stretch each line separately and finish with palette colour work (Siril/PixInsight doctrine; a linked-only stretch of an unequalized narrowband composite is the documented green-SHO failure mode) | `starcomb.py`: starless stretch per class — **linked** autostretch (broadband; one calibrated scene, one transfer) or **per-line NOISE-WIDTH-CAPPED stretch** (`stretch_linked auto` → `perline` on a narrowband-palette composition: per line, gamma∘black-pin solved so sky location = `starless_target` and sky noise width = `perline_scale` — the stretch stops before amplifying noise into visibility) + the **gated LCh finishing set** (saturation gamma, Hubble hue rotation, SCNR, post-peak LUMINANCE-only lift `ppgamma` — chroma is never stretched); + significance corings (chroma/lum, Wiener-gated); stars gray-MTF anchor + flux-percentile cull + `stars_opacity` reduced-opacity screen | COMPLIANT (the reference-corpus author's own published chain implements exactly this mechanism set — noise-budgeted stretch, post-peak L-only lift, LCh colour ops, no denoiser; verified from his open-source tool + recipe and reproduced on this rig; sky-anchored unlinked measured a no-op, NOTES dead ends) |
| 8 | recombine (screen) + final touches, export | `starcomb.py` screen combine + `satu` chroma gain; JPEG q92 + `--lossless` PNG for finals | COMPLIANT |

Principles that keep this honest:

- **The mapping above is re-verified against current Siril/PixInsight
  doctrine at every siril minor-version bump** — tool positions move
  (stretch guidance, SPCC modes, separation models), so the comparison is
  standing work, not a one-time audit; per-item verifications carry their
  dates in the BACKLOG entries they feed.

- **A divergence from the standard is a bandaid unless it is a measured,
  documented adaptation forced by this data** — each one carries its removal
  condition in NOTES ("REMAINING BANDAIDS" ledger).
- **Full frame is mandatory.** No crops hiding defects; the foreground branch
  never drives decisions (it is masked in QA statistics, feathered in
  rendering operators).
- **Root-cause rule:** when a root cause is found and fixed, every knob that
  was tuned while the root cause was still present is STALE and must be
  re-derived.

## The review contract (who/what judges each step)

1. **Per-stage inspection** (`inspect_stage.py`, auto in every pipeline run):
   each STACK stage rendered identically + metric bounds from the
   expectations table in NOTES. WARN only — inspection never aborts. The
   RENDER chain has the same provenance on demand: `starcomb.py --inspect`
   writes one consistent JPEG + metrics line per render stage (bgelin /
   separation / stretch / corings / black point / stars / combine) into
   `results/inspect_render_<set>_<stamp>/`, so a defect in a final render is
   localized to the stage that introduced it in one run; diff any two runs'
   stages with `judgment_crops.py <outdir> a=<x.jpg> b=<y.jpg>
   --question="..."` (every judgment package states its question and ships
   a full-frame pair + lossless 1:1 crops).
2. **The gate** (`bg_qa.py`, composition-agnostic sky scope): strict
   thresholds on the **starless render's sky**, selected STATISTICALLY (dark
   blocks ≤ P50+2.5·MAD, terrestrial foreground excluded) — colour ≤ 7,
   plane-fit gradient ≤ 8, blotch ≤ 5, rings ≤ 8. Thresholds never loosen.
   Real signal (a galaxy / the MW / a nebula) is bright and drops out of the
   sky selection, so it is never read as a defect and no per-set corridor is
   needed. Whole-frame QA on the recombine is reported as reference, never
   gated.
3. **Star metrics** (count / FWHM-eq / mid-tier peak / saturated fraction /
   halo) on the stars layer / combined render — reported.
4. **Star-shell audit** (`astrometrics.star_shell_report`, every starcomb
   run): the ghost-aura defect class lives ON stars where the background
   gate cannot see it — bright-tier annulus metrics, `aura_lum` WARN > 4.0
   (calibrated: fixed recipe +2.0, defect era +12.0), `shell_chroma`
   reported as a trend (honest PSF fringe dominates it). The stars anchor +
   its MTF low-end gain print per run so normalization drift is visible.
5. **The user judges aesthetics on the recombine — from FULL-FRAME
   LOSSLESS FINALS, opened independently.** A judgment set is a folder of
   whole-frame lossless images (PNG16 + PNG8) with clean names and a
   QUESTION.md, nothing else: no crops, no composited panels, no lossy
   surface — the judge pulls each file into their own viewers and
   environments. Assemble it with `judgment_package.py`, which verifies
   every PNG8+PNG16 pair pixel-wise before linking — never by hand. Ladder runs emit per-value lossless finals for exactly
   this. Crops/panels (`judgment_crops.py`) are an on-request supplement,
   never the judgment surface. Objective fixes with pass/fail metrics may
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

### How a change is accepted

Byte-identity with one dataset's render is **not** the bar. It answers "did the
output change?", never "is the output right?" — so it promotes a single
imperfect recipe into the definition of correct, and the cheapest way to stay
green becomes a bandaid that special-cases that dataset. Three checks replace
it, each answering a question it can actually answer:

1. **Determinism.** The render is reproducible *from its own inputs*: run it
   twice on the same stack — cold caches included — and the artifacts are
   byte-identical. This is a property of the CODE (no hidden RNG, no thread
   nondeterminism; measured: GraXpert BGE, the ONNX net and siril's
   autostretch/denoise all reproduce bit-exactly, and the chain carries no
   unseeded step — `subsky` runs without `-dither` for exactly this
   reason). Verify with `scripts/qa/sweep.py --determinism`. A STACK is
   exempt — its register sweep is non-deterministic; verify a stack by the
   gate + inspection.
2. **No regression, across data classes.** Every registered dataset
   (`SESSIONS.md`) still PASSES the gate, shows no star-shell WORSENING vs
   its own recorded baseline (regression semantics — a clean dataset rotting
   toward the defect class fails long before any absolute line; recording a
   baseline above the audit WARN bound requires an explicit
   `--ack-aura-warn`), and passes the per-stage inspection. **Gate
   thresholds never loosen.** An emission-flooded field whose ONLY failing
   metric is colour (real sky colour outside the current colour scope's
   reach — the ratified colour-redesign class) is kept inside the
   regression net by a scope-ACKNOWLEDGED baseline
   (`sweep.py --rebaseline <ds> --ack-color-scope`): the achromatic
   thresholds stay fully enforced, colour is graded ONE-SIDED against the
   record (worsening fails), and bytes/shells/drift are checked as normal.
   The ack is explicit, per-dataset, refused when any achromatic metric
   fails, and is tracking — never colour judgment: full colour admission
   still waits on the redesign. The reference suite spans the classes the
   pipeline actually meets — self-flat underexposed DSLR wide-field,
   matched-flat off-centre object, self-flat wide, and mono FITS with a
   frame-centred galaxy — so no single dataset can hold the pipeline
   hostage. One command runs it: `python3 scripts/qa/sweep.py` (renders
   every dataset with a `datasets/*/*/baseline.json`, requires gate PASS +
   baseline-relative shell check, diffs every metric against the baseline,
   and flags any byte delta as a declared-delta prompt; absent third-party
   data SKIPs loudly).
3. **Declared delta.** A change that alters a registered render is *expected*,
   not forbidden. It must report the metric deltas and side-by-side panels in
   LIKE encodings. Strictly-better-or-equal objective metrics may commit; any
   aesthetic change needs the user's eyes before it is baked as a default. An
   approved render is re-baselined and git-tagged — the tag is the record, not
   a frozen file.

Pinned narrowly: the starless gate JPEG's q92 encoding **is** the gate's
identity (change it and the gate measures something else). Pin that, not the
whole product chain.

**Data integrity (what is lossy, where, and the guards).** The processing
path is linear FITS end to end: 32-bit float stacks/products, with ONE
documented precision reduction — 16-bit stack-time intermediates
(quantization measured ≈18× below per-frame noise, ~+0.3% stack noise).
Lossy/display files exist ONLY as OUTPUT surfaces: the gate's pinned q92
starless jpg (its identity, never a judgment surface), the q100/4:4:4
final jpg, and judgment panels. GUARDS keep it that way: processing loads
go through `astrometrics.load_linear` (refuses non-FITS), `starcomb
--stack` refuses non-FITS paths, and `compose.py` asserts float32 inputs.
Human judgment uses the LOSSLESS artifacts: `--lossless` exports PNG8 +
PNG16 for the final **and the starless layer** (PNG8 = the exact pixels
the gate encoder consumed; PNG16 = the float layer at 65536 levels).
Never judge a q92 surface. Finals carry EMBEDDED sRGB COLORIMETRY (JPEG
ICC + PNG sRGB/gAMA/cHRM chunks): the chain's LCh math already treats
display RGB as sRGB-companded, so the tag declares that instead of
leaving viewers to assume it — pixels untouched, profile vendored at
`scripts/lib/srgb.icc` with timestamp/ID zeroed for byte-determinism.
The gate's pinned q92 starless jpg stays byte-untouched (gate identity).

**North star:** every stage audits itself with numbers so that eventually
ANY dataset can be dropped into a session dir and be properly judged and
processed to its best honest outcome — composition facts from config or
derivation, defects caught by the standing checks, aesthetics decided by
the user from measured candidates, and every divergence carrying its
removal condition.

## The experiment discipline

- One knob per experiment, values bracketing the control; hypothesis
  pre-registered in NOTES *before* the run.
- A measurement that kills a hypothesis becomes a dead end **written into
  NOTES with its numbers** before anything else is tried.
- Harness: `starcomb.py --param --values --hypothesis` emits per-value
  metrics + side-by-side strips into `results/exp_*/` and STOPs for user
  judgment.
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
render), `starless_denoise` (the proven chroma killer),
`chroma_core` (over-neutralizes faint real colour), `black_point`
(crushes faint extended signal), `starless_target` (darker than
necessary on clean data), `stars_peak` (blows star tops on deep data),
and the stretch architecture itself (`stretch_linked` — a narrowband
palette needs the per-line mode, auto-resolved from the recipe's
narrowband marker). Each is a single-knob ladder the harness already
runs; the user judges once per class instead of debugging after.

## Per-dataset state (`datasets/<session>/<set>/`, tracked)

Session data dirs are gitignored (several hold third-party raws that must
never be committed), so everything the repo versions about a dataset lives
in `datasets/<session>/<set>/` — see `datasets/README.md` for the contract:

- `geometry.json` — the only per-set **composition fact**: the terrestrial
  **foreground** (`rect` fractions or a derived pixel-`mask` npz, session-
  relative) plus `judgment_crops` and optional `starsep` overrides. Resolved
  by `astrometrics.configure()` in every product entry point (starcomb,
  starsep, bg_qa CLI, inspect_stage, judgment_crops, measure_stack,
  solve_field). No file: foreground **none** (whole frame is eligible sky).
  A new set NEVER inherits another set's foreground silently. A configured
  foreground must TOUCH A FRAME BORDER (terrestrial obstructions are
  border-anchored by construction; the foreground is excluded from the
  gate's sky scope, so a floating interior one would carve graded sky out
  of the gate's jurisdiction) — refused loudly at configure time.
- `recipe.json` — the processing knobs: the `render` dict (starcomb
  resolves CLI > recipe > `datasets/GENERIC.json` and prints the
  provenance; a dataset with no recipe renders data-class-blind generic
  and says so) plus the optional `spcc` spec (sensor/filter names or
  narrowband wavelengths, same resolution order in `spcc_run.py`). An
  **approved** recipe pins every knob so a later generic-default change
  cannot silently restyle it.
- `GENERIC.json` (one per repo, beside this contract's per-set dirs) —
  the tracked base layer every render inherits: the generic value AND a
  per-knob "why" note naming what it encodes (most were measured on one
  underexposed DSLR wide-field) and its known class limits. Tweakable at
  any time — but a change restyles every non-approved dataset, so it
  lands as a declared delta through the sweep. The knob SCHEMA stays in
  code; starcomb hard-fails on any file/schema drift.
- `baseline.json` — the measured no-regression record (pinned stack sha,
  expected gate/shell numbers, artifact hashes), written only by
  `scripts/qa/sweep.py --rebaseline`.
- `composition.json` — only for multi-line/multi-filter targets: how the
  composed linear stack is BUILT (kind, extraction, lines, palette
  channel mapping). Absent = ordinary single-stack set.

The background is NOT a per-set composition fact: the gate selects its sky
STATISTICALLY (dark blocks, foreground excluded — see the review contract),
so no galactic band or object region is ever configured per set (a bright
object has no fixed geometry a mask could scope — see NOTES dead ends).

Foreground masks for non-rectangular compositions (treelines) are derived
from the linear stack: `scripts/geometry/suggest_foreground.py <stack>
<out.npz> --overlay=<review.jpg>` — eyeball the overlay, then point the config
at the npz. (The derivation itself is flagged for redesign — see BACKLOG.)

## Running it

```bash
# full pipeline (session dir, set name; ~15 min)
scripts/stack/run_pipeline.sh 07-02-26 set-03

# color-calibrate the stack once per stack rebuild (~1 min, local catalogs)
python3 scripts/calibrate/solve_field.py 07-02-26/results/stack_set-03.fit \
    --inject=07-02-26/results/stack_set-03_wcs.fit
# NEW FIELD: make sure the local Gaia chunks cover it before SPCC (a southern
# field needs southern chunks); --fetch downloads any missing ones
python3 scripts/calibrate/spcc_cone.py 07-02-26/results/stack_set-03_wcs.fit --fetch
# then siril spcc (spcc_run.py) → _spcc.fit

# final render, approved defaults (~3 min; --lossless adds PNG8 + PNG16)
python3 scripts/render/starcomb.py 07-02-26 set-03 \
    --stack 07-02-26/results/stack_set-03_norgbeq_spcc.fit --lossless

# single-knob ladder
python3 scripts/render/starcomb.py 07-02-26 set-03 --stack ... \
    --param chroma_core --values 2,6 --hypothesis "..."
```

Environment specifics (flatpak siril invocation, catalogs, GraXpert, timing)
live in NOTES "Environment" + auto-memory.

## Repo map (`scripts/`, by stage directory)

**`lib/`** — shared measurement + gate, imported everywhere via the walk-up bootstrap

| file | role |
|---|---|
| `astrometrics.py` | shared measurement lib: FITS reader, bg/star metrics, radial profiles, foreground (`branch_mask`) + statistical-sky (`sky_pixel_mask`) masks, `star_shell_report` |
| `bg_qa.py` | THE GATE (composition-agnostic statistical sky scope on the starless render); thresholds never loosen |
| `render_helpers.py` | shared helpers for the ladder harnesses: GraXpert runner, `measure_jpg`, side-by-side strips |

**`stack/`** — build the integrated stack

| file | role |
|---|---|
| `run_pipeline.sh` | stack builder: preflight → masters → calibrate → register (sweep) → stack; forks camera-raw vs dedicated-astrocam FITS, auto-routes flatless sets to the self-flat branch, and routes a `composition.json` dual-band set through line extraction → same-reference per-line stacks → compose |
| `compose.py` | the convergence stage: per-line / per-filter member stacks → ONE composed linear colour stack per the composition record's palette mapping (mono-filters members aligned to the reference member first); measures the channel-alignment residual (inspected, bound 1.0 px) |
| `fitsmeta.py` | FITS acquisition-metadata probe for the dedicated-astrocam preflight (exposure/gain/offset/filter/mono); normalizes the free-text `FILTER` keyword to a canonical token and fails loud on a mixed dir |
| `siril/master_{bias,flat,dark}.ssf`, `siril/lights.ssf.tmpl` | siril stages for the matched-flat path |
| `siril/selfflat/{1_median,2_median2,3_divide,4_stack}.ssf.tmpl`, `selfflat.py`, `rechroma.py` | the self-flat branch (V(r) isotonic gray gain, V2 re-fit, chroma re-centering) — dies when real flats exist |

**`calibrate/`** — astrometric + photometric calibration

| file | role |
|---|---|
| `solve_field.py` | blind astrometric solve (astrometry.net) + TAN-SIP WCS injection — unblocks siril `spcc`; scale hint derived from the FITS header, foreground-masked star detection |
| `spcc_cone.py` | which local Gaia SPCC chunks a solved field needs (nside=2 nested HEALPix cover from the WCS) + `--fetch` to download the missing ones (md5-verified) — turnkey SPCC coverage for any field |
| `spcc_run.py` | siril SPCC runner that CAPTURES the K factors + star counts into `work/spcc_<set>.{json,log}` |

**`render/`** — the product chain + star separation

| file | role |
|---|---|
| `starcomb.py` | **the product chain** (knobs: CLI > `datasets/<session>/<set>/recipe.json` > GENERIC) + single-knob ladder harness |
| `separation/starnet_sep.py` | star separation by StarNet2 ONNX inference on aarch64 (the generic default via `auto`; needs the official weights file at `~/.local/share/starnet/`) |
| `separation/starsep.py` | star separation by mask+inpaint — the weights-absent fallback; warns when the frame holds a resolved object it would damage; also builds the engine-invariant detection catalog |

**`qa/`** — standing audits + diagnostics (WARN-only)

| file | role |
|---|---|
| `inspect_stage.py` | per-stage inspection reports (WARN-only), wired into the runners |
| `capture_report.py` | per-channel capture report card for composed targets (WARN-only, run at compose time + re-run after SPCC): member rates from dark-subtracted raw lights, sky rates, stack SNRs, SNR-parity hours, captured-vs-displayed line ratios |
| `judgment_package.py` | assembles a judgment set from render FINALS: verifies each PNG8+PNG16 pair pixel-wise before linking (a hand-linked package once shipped starless PNG16s as finals), refuses starless layers, writes the QUESTION.md skeleton |
| `sweep.py` | **the no-regression sweep**: renders every baselined dataset, enforces gate PASS + no shell worsening vs each baseline, diffs metrics + artifact bytes vs `datasets/*/*/baseline.json`; `--determinism` double-renders; `--rebaseline` records a new baseline (`--ack-aura-warn` to record over the audit bound) |
| `judgment_crops.py` | fixed defect-zone 1:1 crop panels for user judgment |
| `measure_stack.py`, `diag_flat.ssf` | stack stats, master-flat diagnostic |

**`geometry/`** — per-set composition facts

| file | role |
|---|---|
| `suggest_foreground.py` | derive a foreground pixel mask (treelines etc.) from the linear stack for the dataset's `geometry.json` — always eyeball the `--overlay` |

## Data layout

```
<session>/           e.g. 07-02-26/ or nikon-test/ or imx585c/
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
SESSIONS.md                              dataset registry (what's been processed)
```
