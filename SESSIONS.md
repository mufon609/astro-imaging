# Sessions — datasets this repo has processed

The pipeline is dataset-generic (`run_pipeline.sh <session> <set>`; `raw_find`
ingests any camera raw — NEF/DNG/CR2/…). This indexes the datasets it has
handled so the repo is a multi-workflow tool, not a single-set project. Raw
frames live in **gitignored** session dirs; the approved recipe + provenance
live in **git** (recipe tags) and NOTES.

| session dir | camera / gear | sets | status | record |
|---|---|---|---|---|
| `07-02-26/` | Nikon Z6III · 37–38 mm f/4 · ISO 200 · 25 s | `set-03` (Cygnus, **self-flat**) · `lights` (Boötes, matched-flat) | **DONE** — `set-03` approved 2026-07-08 (corridor-free); `lights` unapproved (generalization testbed) | `datasets/07-02-26/set-03/` (recipe + baseline + geometry), `datasets/07-02-26/lights/geometry.json` |
| `imx585c/` | Player One Uranus-M Pro · Sony IMX585 **mono** · Takahashi TOA-130 (992 mm f/7.7) · gain 0 · −15 °C · L filter · 120 s | `m74_toa130` · `ngc7331_toa130` (both mono **L**; dark + flat + dark-flat) | **`m74_toa130` DONE** — the first dedicated-astrocam (FITS) set, and the first **mono** one. Ingested by the FITS branch (`fitsmeta.py` preflight), flats matched by FILTER and calibrated with **dark-flats**, lights never debayered. 47/47 registered; mono luminance render, **gate PASS** (colour 0.0, grad 0.3, blotch 0.1, rings 1.0). Recipe pins `sep_engine net` on measurement (mask+inpaint destroyed the galaxy's HII knots — see the recipe's notes). Look **not** user-approved. `ngc7331_toa130` queued (partial download). | `datasets/imx585c/m74_toa130/` + `imx585c/README.md` (gitignored — John Stone's raws via AstroBin, practice-only, never commit/redistribute) |
| `nikon-test/` | Nikon D810A · 180 mm f/2.8 + 50 mm f/4 · ISO 800 · 181 s | `lmc_180mm` · `smc_180mm` (**matched-flat**) · `wide_50mm` (**self-flat**) · `nebula_180mm` (mosaic panel — single-field pipeline skips it) | **`lmc_180mm` + `smc_180mm` + `wide_50mm` DONE**. LMC/SMC (matched-flat) drove the corridor removal: 12–13/13 registered, solved, SPCC, composition-agnostic gate PASS; LMC approved 2026-07-08 (recipe pinned); the set-03-tuned `chroma_core`/`satu` desaturate real colour + over-saturate the SMC's OIII (now expressible per-dataset in the recipes); the bright-star red halo is a Sigma-180-wide-open optical signature (NOTES), left as-is. `wide_50mm` (self-flat, 28/28 frames): a Crux/Carina southern-Milky-Way field at 50 mm/41° — the blind plate-solve FAILS on the wide-lens edge distortion; solved via `solve_field.py --central=0.25 --ra=186.7 --dec=-62.2 --radius-deg=15` (region read off a first no-WCS render), SPCC K R1.00/G0.83/B0.86 on 3087 stars, gate PASS (grad 6.4, rings 4.2). `nebula_180mm` (mosaic) queued. | `datasets/nikon-test/{lmc_180mm,smc_180mm,wide_50mm}/` + `nikon-test/README.md` (gitignored — Wei-Hao Wang's archive, practice-only, never commit/redistribute) |
| `siril-m8m20/` | ZWO ASI2600MC Pro (**OSC**, Sony IMX571, RGGB) · Takahashi FSQ-106 @ 531 mm f/5 · gain 100 · −10 °C · 180 s | `lpro_180s` (15× L-Pro broadband) · `hoo_180s` (20× HOO dual-band) — shared darks; per-filter flats; 3 s offsets that double as dark-flats | **STAGED, unprocessed** — Siril's own tutorial set (M8+M20), downloaded as the OSC-CFA + dual-band coverage corpus: `lpro_180s` is the C7 OSC-CFA branch verification case (and the first SPCC run with a REAL chip profile — Sony IMX571 is in the SPCC database); `hoo_180s` is the dual-band extraction case (BACKLOG C6). CAVEATS from headers: **no FILTER keyword anywhere** (filter identity is directory-only — stage `flats/` per set before running) and the author's finished masters sit in `reference/` as the answer key. | `siril-m8m20/README.md` (gitignored — colmic's tutorial data, process only, never redistribute) |
| `colonnello-m20/` | ASI1600MM-class **mono** (4656×3520, MN34230) · gain 75 · filter wheel | `lights_{Red,Green,Blue}` (15× each) + per-filter flats + darks + biases + stage-by-stage `reference/` | **STAGED, unprocessed** — the mono-RGB filter-wheel case for the multi-filter combine (BACKLOG C6); ships the author's masters at every stage, so channel-combination is checkable against ground truth. Filenames carry SPACES — verify the shell paths in `run_pipeline.sh` survive them before the first run. | `colonnello-m20/README.md` (gitignored — Diego Colonnello via astropixelprocessor.com, attribution required, never redistribute) |
| `mlnoga-ngc7635/` | ASI183MM **mono** · SHO narrowband | `calib/` + `reference/` staged; the NB lights zip is still DOWNLOADING (a prior session's stager runs in the background → `~/.cache/astro_stage/nb.zip`) | **DOWNLOAD IN PROGRESS** — the mono-SHO palette case for BACKLOG C6 (CC BY-NC-SA 4.0). The `app-ngc292` LRGB set that stager also offered was **skipped by user request** (marker dir only). | `mlnoga-ngc7635/README.md` (gitignored) |

## Adding a dataset

1. Lay it out as a session dir: `<session>/{darks,flats,biases,darkflats}/`
   (calibration, each one internally-uniform group) + one `<session>/<set>/` per
   single-pointing light set. Any siril-readable camera raw works — no
   conversion — as do dedicated-astrocam **FITS** frames, where `darkflats/`
   (darks matched to the flat exposure) calibrates the flats.
2. `scripts/stack/run_pipeline.sh <session> <set>` — forks on the data class
   (camera raw vs FITS; `fitsmeta.py` reads filter/exposure/gain from the FITS
   headers), then routes matched-flat vs self-flat → `results/stack_<set>.fit`.
   Flats are matched to lights **by filter** on the FITS path; mono lights are
   never debayered.
3. Plate-solve (`scripts/calibrate/solve_field.py`) → SPCC (`spcc_run.py`) →
   render (`scripts/render/starcomb.py`). A **mono** (single-filter) set skips
   SPCC and renders luminance-only — no chroma coring, no saturation.
4. A set with no `datasets/<session>/<set>/` state **degrades loudly**
   (whole-frame gate, no foreground mask, GENERIC render knobs, printed as
   such) — safe, just generic. Add `geometry.json` once the field is solved,
   pin a `recipe.json` when a look is chosen, and record the no-regression
   target with `scripts/qa/sweep.py --rebaseline <session>/<set>`.
