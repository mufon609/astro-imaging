# Sessions — datasets this repo has processed

The pipeline is dataset-generic (`run_pipeline.sh <session> <set>`; `raw_find`
ingests any camera raw — NEF/DNG/CR2/…). This indexes the datasets it has
handled so the repo is a multi-workflow tool, not a single-set project. Raw
frames live in **gitignored** session dirs; the approved recipe + provenance
live in **git** (recipe tags) and NOTES.

| session dir | camera / gear | sets | status | record |
|---|---|---|---|---|
| `07-02-26/` | Nikon Z6III · 37–38 mm f/4 · ISO 200 · 25 s | `set-03` (Cygnus, **self-flat**) · `lights` (Boötes, matched-flat) | **DONE** — `set-03` recipe = corridor-free starcomb defaults (approved 2026-07-08; the B5/B6/B7 corridor recipes are retired); `lights` unapproved (generalization testbed) | NOTES STATUS + `07-02-26/config_{set-03,lights}.json` |
| `imx585c/` | Player One Uranus-M Pro · Sony IMX585 **mono** · Takahashi TOA-130 (992 mm f/7.7) · gain 0 · −15 °C · L filter · 120 s | `m74_toa130` · `ngc7331_toa130` (both mono **L**; dark + flat + dark-flat) | **`m74_toa130` DONE** — the first dedicated-astrocam (FITS) set, and the first **mono** one. Ingested by the FITS branch (`fitsmeta.py` preflight: filter/exposure/gain read from headers), flats matched by FILTER and calibrated with **dark-flats** (the CMOS standard), lights never debayered. 47/47 registered; mono luminance render, **gate PASS** (colour 0.0, grad 0.5, blotch 0.1, rings 1.0). The stack-inspection WARNs are measured data-class artifacts (a centred galaxy in a radial sky profile; a 38-count background), not defects — the flat master is clean (1.3% falloff). Render uses the set-03-tuned defaults and is **not** an approved look. `ngc7331_toa130` queued (partial download). | `imx585c/README.md` (gitignored — John Stone's raws via AstroBin, practice-only, never commit/redistribute) |
| `nikon-test/` | Nikon D810A · 180 mm f/2.8 + 50 mm f/4 · ISO 800 · 181 s | `lmc_180mm` · `smc_180mm` (**matched-flat**) · `wide_50mm` (**self-flat**) · `nebula_180mm` (mosaic panel — single-field pipeline skips it) | **`lmc_180mm` + `smc_180mm` + `wide_50mm` DONE**. LMC/SMC (matched-flat) drove the corridor removal: 12–13/13 registered, solved, SPCC, composition-agnostic gate PASS; renders honest — the set-03-tuned `chroma_core`/`satu` desaturate real colour + over-saturate the SMC's OIII (per-dataset recipe = BACKLOG C1); the bright-star red halo is a Sigma-180-wide-open optical signature (NOTES), left as-is. `wide_50mm` (self-flat, 28/28 frames): a Crux/Carina southern-Milky-Way field at 50 mm/41° — the blind plate-solve FAILS on the wide-lens edge distortion; solved via `solve_field.py --central=0.25 --ra=186.7 --dec=-62.2 --radius-deg=15` (region read off a first no-WCS render), SPCC K R1.00/G0.83/B0.86 on 3087 stars, gate PASS (grad 6.4, rings 4.2). `nebula_180mm` (mosaic) queued. | `nikon-test/README.md` (gitignored — Wei-Hao Wang's archive, practice-only, never commit/redistribute) |

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
4. A set with no `config_<set>.json` **degrades loudly** (whole-frame gate, no
   MW-corridor / foreground masks, `mw_boost` skipped) — safe, just generic.
   Derive geometry once the field is solved.

Per-dataset state (own approved recipe, own byte-reproduce, tracked config for
a copyright-ignored dataset) is still thin — see the multi-dataset architecture
item in BACKLOG.
