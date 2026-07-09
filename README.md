# Astrophotography processing pipeline

This repo tracks the **process** (Siril/Python scripts + notes), never image
data (`.gitignore`). `NOTES.md` is the lab notebook: every measured lesson,
every dead end with its numbers. This file is the **process contract**: what
each step is for, what the industry standard does there, where we diverge and
why, and how every step is reviewed.

**New contributor start here:** (1) this file top to bottom; (2)
`NOTES.md` top to bottom — it is deliberately short: STATUS (current
approved recipe + reproduce contract), the current design with every
knob's measured WHY, and the **DEAD ENDS registry** (read it before
proposing ANY experiment — if it was tried, its killing number is
there). Full chronological history lives in git (`git log`; every
commit carries the NOTES of its time). The current approved recipe is
**the starcomb defaults, corridor-free** (the MW-corridor + `mw_boost`
bandaid was removed 2026-07-08, user-approved); the corridor-era
`B5/B6/B7-approved` tags are history.

## The reference standard

The industry deep-sky workflow (PixInsight/Siril practice) that this pipeline
follows, in order — linear until step 6:

| # | standard step | our implementation | status |
|---|---|---|---|
| 1 | calibrate (bias/dark/flat) → register → integrate | `run_pipeline.sh`: masters + per-set calibrate → 2-pass/sweep register → 32-bit rej stack | COMPLIANT (matched darks/biases; flats when optics match) |
| 1b | — | **self-flat branch** for sets without a matching flat (median → V(r) isotonic gray gain → rechroma → V2 divide; per-frame planar glow subtraction) | ADAPTATION — dies when real flats exist at the set's focal length (preflight auto-routes) |
| 2 | linear gradient removal on the stack, star-ful (DBE/GraXpert) | GraXpert BGE + `subsky 1`, star-ful (`starcomb bge_first`) | COMPLIANT — order measured MW-safe; BGE on starless ERASES the MW (never reorder) |
| 3 | photometric color calibration (SPCC/PCC via plate solve) | `solve_field.py` (blind astrometry.net solve, WCS inject) + `spcc_run.py` (siril `spcc` with local Gaia catalogs, K factors captured to `work/spcc_<set>.{json,log}`) → `stack_<set>_norgbeq_spcc.fit` | COMPLIANT — SPCC calibrates the raw stack directly (`rgb_equal` removed 2026-07-07, user-approved); spcc rerun measured pixel-deterministic. SPCC is BROADBAND-only: a mono/single-filter set skips it (no colour to calibrate) |
| 4 | deconvolution (optional, data permitting) | skipped | COMPLIANT-SKIP — measured dead end on this data (in-exposure trailing, PSF unstable on ≈0 background) |
| 5 | linear noise reduction | none linear | MEASURED DEAD END on self-flat data: any noise-adaptive linear denoise imprints a radial signature (noise is radial by construction after V(r) division). Post-stretch `-vst -mod=0.5` on the starless render is the working replacement |
| 6 | star separation (StarNet/StarXTerminator) | `starnet_sep.py` StarNet2-ONNX on aarch64, run LINEAR under an invertible MTF pre-stretch (the vendor-sanctioned placement) — the generic default (`sep_engine auto` → `net` when the weights are installed). `starsep.py` mask+inpaint is the WEIGHTS-ABSENT FALLBACK: it destroys resolved-object structure (measured: 26% of M74's detections were HII knots) and warns when it measures that risk. Per-dataset recipes pin the engine; set-03's approved look pins `inpaint` pending user judgment of net's bright-star shell | COMPLIANT (learned separator, standard placement); fallback is the documented adaptation |
| 7 | stretch starless hard / stars gently; optional faint-tail treatment | `starcomb.py`: starless **linked** autostretch + significance corings (chroma/lum, Wiener-gated on the statistical dark sky); stars gray-MTF anchor + flux-percentile cull | COMPLIANT in shape; every knob value is a measured ladder (NOTES "Knob provenance") |
| 8 | recombine (screen) + final touches, export | `starcomb.py` screen combine + `satu` chroma gain; JPEG q92 + `--lossless` PNG for finals | COMPLIANT |

Principles that keep this honest:

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
   stages with `judgment_crops.py <outdir> a=<stage.jpg> b=<stage.jpg>`.
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
5. **The user judges aesthetics on the recombine.** Objective fixes with
   pass/fail metrics may commit; recipe/aesthetic changes require the user's
   visual approval before they are baked as defaults.

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
   autostretch/denoise all reproduce bit-exactly, and the one unseeded step
   the chain used to carry, `subsky -dither`, was removed for exactly this
   reason). Verify with `scripts/qa/sweep.py --determinism`. A STACK is
   exempt — its register sweep is non-deterministic; verify a stack by the
   gate + inspection.
2. **No regression, across data classes.** Every registered dataset
   (`SESSIONS.md`) still PASSES the gate, the star-shell bounds and the
   per-stage inspection. **Gate thresholds never loosen.** The reference suite
   spans the classes the pipeline actually meets — self-flat underexposed DSLR
   wide-field, matched-flat off-centre object, self-flat wide, and mono FITS
   with a frame-centred galaxy — so no single dataset can hold the pipeline
   hostage. One command runs it: `python3 scripts/qa/sweep.py` (renders every
   dataset with a `datasets/*/*/baseline.json`, requires gate PASS + shell
   bounds, diffs every metric against the baseline, and flags any byte delta
   as a declared-delta prompt; absent third-party data SKIPs loudly).
3. **Declared delta.** A change that alters a registered render is *expected*,
   not forbidden. It must report the metric deltas and side-by-side panels in
   LIKE encodings. Strictly-better-or-equal objective metrics may commit; any
   aesthetic change needs the user's eyes before it is baked as a default. An
   approved render is re-baselined and git-tagged — the tag is the record, not
   a frozen file.

Pinned narrowly: the starless gate JPEG's q92 encoding **is** the gate's
identity (change it and the gate measures something else). Pin that, not the
whole product chain.

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
  A new set NEVER inherits another set's foreground silently.
- `recipe.json` — the render knobs. starcomb resolves CLI > recipe >
  GENERIC and prints the provenance; a dataset with no recipe renders
  data-class-blind generic and says so. An **approved** recipe pins every
  knob so a later generic-default change cannot silently restyle it.
- `baseline.json` — the measured no-regression record (pinned stack sha,
  expected gate/shell numbers, artifact hashes), written only by
  `scripts/qa/sweep.py --rebaseline`.

The background is NOT a per-set composition fact: the gate selects its sky
STATISTICALLY (dark blocks, foreground excluded — see the review contract),
so there is no MW corridor to configure or derive. That geometric band was a
set-03-specific bandaid that broke on an object-dominated field.

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
| `run_pipeline.sh` | stack builder: preflight → masters → calibrate → register (sweep) → stack; forks camera-raw vs dedicated-astrocam FITS, and auto-routes flatless sets to the self-flat branch |
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
| `sweep.py` | **the no-regression sweep**: renders every baselined dataset, enforces gate + shell bounds, diffs metrics + artifact bytes vs `datasets/*/*/baseline.json`; `--determinism` double-renders; `--rebaseline` records a new baseline |
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
  <set>/                                 lights: camera raw (NEF/DNG/CR2/…) or
                                         dedicated-astrocam FITS (all ignored)
  work/                                  masters, caches, generated scripts
  results/                               stacks, renders, exp_*/, inspect_*/
datasets/<session>/<set>/                tracked per-dataset state: geometry.json,
                                         recipe.json, baseline.json (see datasets/README.md)
scripts/                                 the pipeline (tracked)
SESSIONS.md                              dataset registry (what's been processed)
```
