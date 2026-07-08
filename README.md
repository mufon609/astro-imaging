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
| 3 | photometric color calibration (SPCC/PCC via plate solve) | `solve_field.py` (blind astrometry.net solve, WCS inject) + `spcc_run.py` (siril `spcc` with local Gaia catalogs, K factors captured to `work/spcc_<set>.{json,log}`) → `stack_<set>_norgbeq_spcc.fit` | COMPLIANT — SPCC calibrates the raw stack directly (`rgb_equal` removed 2026-07-07, user-approved); spcc rerun measured pixel-deterministic |
| 4 | deconvolution (optional, data permitting) | skipped | COMPLIANT-SKIP — measured dead end on this data (in-exposure trailing, PSF unstable on ≈0 background) |
| 5 | linear noise reduction | none linear | MEASURED DEAD END on self-flat data: any noise-adaptive linear denoise imprints a radial signature (noise is radial by construction after V(r) division). Post-stretch `-vst -mod=0.5` on the starless render is the working replacement |
| 6 | star separation (StarNet/StarXTerminator) | `starsep.py` mask+inpaint (default) · `starnet_sep.py` StarNet2-ONNX runs on aarch64 (engines `net`/`hybrid` in starcomb) | ADAPTATION, removal candidate VALIDATED — the `hybrid` engine (net on the inpaint starless) meets every objective bar incl. the faint-tail removal (residual 589 vs ~5.1k) and awaits user judgment (NOTES ledger #4); `inpaint` stays default |
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
   each stage rendered identically + metric bounds from the expectations
   table in NOTES. WARN only — inspection never aborts.
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

## Per-set geometry (data-generalization)

The only per-set **composition fact** is the terrestrial **foreground** (a
treeline to exclude from sky statistics and the fixed judgment-crop boxes) —
it lives in `<session>/config_<set>.json` (tracked) and is resolved by
`astrometrics.configure()` in every product entry point (starcomb, starsep,
bg_qa CLI, inspect_stage, judgment_crops, measure_stack, solve_field):

1. `config_<set>.json` values — `foreground` (`rect` fractions or a derived
   pixel-`mask` npz), `judgment_crops`, optional `starsep` overrides.
2. No config: foreground **none** (whole frame is eligible sky). A new set
   NEVER inherits another set's foreground silently.

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
    --inject=07-02-26/results/stack_set-03_wcs.fit   # then siril spcc → _spcc.fit

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
| `run_pipeline.sh` | stack builder: preflight → masters → calibrate → register (sweep) → stack; auto-routes flatless sets to the self-flat branch |
| `siril/master_{bias,flat,dark}.ssf`, `siril/lights.ssf.tmpl` | siril stages for the matched-flat path |
| `siril/selfflat/{1_median,2_median2,3_divide,4_stack}.ssf.tmpl`, `selfflat.py`, `rechroma.py` | the self-flat branch (V(r) isotonic gray gain, V2 re-fit, chroma re-centering) — dies when real flats exist |

**`calibrate/`** — astrometric + photometric calibration

| file | role |
|---|---|
| `solve_field.py` | blind astrometric solve (astrometry.net) + TAN-SIP WCS injection — unblocks siril `spcc`; scale hint derived from the FITS header, foreground-masked star detection |
| `spcc_run.py` | siril SPCC runner that CAPTURES the K factors + star counts into `work/spcc_<set>.{json,log}` |

**`render/`** — the product chain + star separation

| file | role |
|---|---|
| `starcomb.py` | **the product chain** (corridor-free approved defaults) + single-knob ladder harness |
| `separation/starsep.py` | star separation by mask+inpaint; catalog for culling |
| `separation/starnet_sep.py` | star separation by StarNet2 ONNX inference on aarch64 (same output trio as starsep.py; needs the official weights file — see NOTES ledger #4; experimental until user-approved) |

**`qa/`** — standing audits + diagnostics (WARN-only)

| file | role |
|---|---|
| `inspect_stage.py` | per-stage inspection reports (WARN-only), wired into the runners |
| `judgment_crops.py` | fixed defect-zone 1:1 crop panels for user judgment |
| `measure_stack.py`, `diag_flat.ssf` | stack stats, master-flat diagnostic |

**`geometry/`** — per-set composition facts

| file | role |
|---|---|
| `suggest_foreground.py` | derive a foreground pixel mask (treelines etc.) from the linear stack for `config_<set>.json` — always eyeball the `--overlay` |

## Data layout

```
<session>/           e.g. 07-02-26/ or nikon-test/
  biases/ darks/ flats/ <set>/           raw frames (NEF/DNG/CR2/…, ignored)
  work/                                  masters, caches, generated scripts
  results/                               stacks, renders, exp_*/, inspect_*/
scripts/                                 the pipeline (tracked)
SESSIONS.md                              dataset registry (what's been processed)
```
