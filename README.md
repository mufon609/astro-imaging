# Astrophotography processing pipeline

This repo tracks the **process** (Siril/Python scripts + notes), never image
data (`.gitignore`). `NOTES.md` is the lab notebook: every measured lesson,
every dead end with its numbers. This file is the **process contract**: what
each step is for, what the industry standard does there, where we diverge and
why, and how every step is reviewed.

## The reference standard

The industry deep-sky workflow (PixInsight/Siril practice) that this pipeline
follows, in order — linear until step 6:

| # | standard step | our implementation | status |
|---|---|---|---|
| 1 | calibrate (bias/dark/flat) → register → integrate | `run_pipeline.sh`: masters + per-set calibrate → 2-pass/sweep register → 32-bit rej stack | COMPLIANT (matched darks/biases; flats when optics match) |
| 1b | — | **self-flat branch** for sets without a matching flat (median → V(r) isotonic gray gain → rechroma → V2 divide; per-frame planar glow subtraction) | ADAPTATION — dies when real flats exist at the set's focal length (preflight auto-routes) |
| 2 | linear gradient removal on the stack, star-ful (DBE/GraXpert) | GraXpert BGE + `subsky 1`, star-ful (`starcomb bge_first`) | COMPLIANT — order measured MW-safe; BGE on starless ERASES the MW (never reorder) |
| 3 | photometric color calibration (SPCC/PCC via plate solve) | `solve_field.py` (blind astrometry.net solve, WCS inject) + siril `spcc` with local Gaia catalogs → `stack_<set>_spcc.fit` | COMPLIANT since 2026-07-06 (`rgb_equal` remains in 40d as an inert stack-time scaling; removal queued) |
| 4 | deconvolution (optional, data permitting) | skipped | COMPLIANT-SKIP — measured dead end on this data (in-exposure trailing, PSF unstable on ≈0 background) |
| 5 | linear noise reduction | none linear | MEASURED DEAD END on self-flat data: any noise-adaptive linear denoise imprints a radial signature (noise is radial by construction after V(r) division). Post-stretch `-vst -mod=0.5` on the starless render is the working replacement |
| 6 | star separation (StarNet/StarXTerminator) | `starsep.py` mask+inpaint (no aarch64 StarNet) | ADAPTATION — dies when a real star-removal net runs on this box; leaves the <6σ faint tail in the starless layer (known cost, see NOTES session 5) |
| 7 | stretch starless hard / stars gently; optional faint-tail treatment | `starcomb.py`: starless **linked** autostretch + significance corings + corridor MW lift; stars gray-MTF anchor + flux-percentile cull | COMPLIANT in shape; knob values are measured ladders (see NOTES "APPROVED RECIPE" + session 5 re-derivations) |
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
  re-derived (session 5 was exactly this audit).

## The review contract (who/what judges each step)

1. **Per-stage inspection** (`inspect_stage.py`, auto in every pipeline run):
   each stage rendered identically + metric bounds from the expectations
   table in NOTES. WARN only — inspection never aborts.
2. **The gate** (`bg_qa.py`, layer-appropriate scope ratified 2026-07-06):
   strict blocks/rings thresholds on the **starless render's sky** (MW
   corridor + branch masked as known signal/non-sky). Thresholds never
   loosen. Whole-frame QA on the recombine is reported as reference, never
   gated.
3. **Reported corridor metrics** (session 5, `astrometrics.corridor_report`):
   corridor floor Δ (P50/P5 vs sky), along-band chroma P2V, branch-mask seam
   steps. The gate masks the corridor, so these numbers exist to keep
   corridor-contained costs measurable. Reported in every starcomb run,
   never gated.
4. **Star metrics** (count / FWHM-eq / mid-tier peak / saturated fraction /
   halo) on the stars layer / combined render — reported.
5. **The user judges aesthetics on the recombine.** Objective fixes with
   pass/fail metrics may commit; recipe/aesthetic changes require the user's
   visual approval before they are baked as defaults.

## The experiment discipline

- One knob per experiment, values bracketing the control; hypothesis
  pre-registered in NOTES *before* the run.
- A measurement that kills a hypothesis becomes a dead end **written into
  NOTES with its numbers** before anything else is tried.
- Harnesses: `experiment.py` (legacy post chain), `starcomb.py --param
  --values --hypothesis` (current chain). Both emit per-value metrics +
  side-by-side strips into `results/exp_*/` and STOP for user judgment.
- Preserve the stack per pipeline experiment (`cp` to a tagged name).

## Running it

```bash
# full pipeline (session dir, set name; ~15 min)
scripts/run_pipeline.sh 07-02-26 set-03

# color-calibrate the stack once per stack rebuild (~1 min, local catalogs)
python3 scripts/solve_field.py 07-02-26/results/stack_set-03.fit \
    --inject=07-02-26/results/stack_set-03_wcs.fit   # then siril spcc → _spcc.fit

# final render, approved defaults (~2 min; add --lossless for the PNG final)
python3 scripts/starcomb.py 07-02-26 set-03 \
    --stack 07-02-26/results/stack_set-03_spcc.fit

# single-knob ladder
python3 scripts/starcomb.py 07-02-26 set-03 --stack ... \
    --param mw_boost --values 0.5,0.8 --hypothesis "..."

# quick-look legacy post chain + gate (no separation)
scripts/run_post.sh 07-02-26 set-03
```

Environment specifics (flatpak siril invocation, catalogs, GraXpert, timing)
live in NOTES "Environment" + auto-memory.

## Data layout

```
<session>/           e.g. 07-02-26/
  biases/ darks/ flats/ lights/ <set>/   raw DNGs (ignored)
  work/                                  masters, caches, generated scripts
  results/                               stacks, renders, exp_*/, inspect_*/
scripts/                                 the pipeline (tracked)
```
