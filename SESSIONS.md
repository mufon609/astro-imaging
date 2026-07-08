# Sessions — datasets this repo has processed

The pipeline is dataset-generic (`run_pipeline.sh <session> <set>`; `raw_find`
ingests any camera raw — NEF/DNG/CR2/…). This indexes the datasets it has
handled so the repo is a multi-workflow tool, not a single-set project. Raw
frames live in **gitignored** session dirs; the approved recipe + provenance
live in **git** (recipe tags) and NOTES.

| session dir | camera / gear | sets | status | record |
|---|---|---|---|---|
| `07-02-26/` | Nikon Z6III · 37–38 mm f/4 · ISO 200 · 25 s | `set-03` (Cygnus, **self-flat**) · `lights` (Boötes, matched-flat) | **DONE** — `set-03` recipe **B7** (tag `B7-approved`, byte-reproduces); `lights` unapproved (generalization testbed) | NOTES STATUS + `07-02-26/config_{set-03,lights}.json` |
| `nikon-test/` | Nikon D810A · 180 mm f/2.8 + 50 mm f/4 · ISO 800 · 181 s | `lmc_180mm` · `smc_180mm` (**matched-flat**) · `wide_50mm` (**self-flat**) · `nebula_180mm` (mosaic panel — single-field pipeline skips it) | **QUEUED** — NEF ingest fixed + verified; awaiting first stack → solve → SPCC → render | `nikon-test/README.md` (gitignored — Wei-Hao Wang's archive, practice-only, never commit/redistribute) |

## Adding a dataset

1. Lay it out as a session dir: `<session>/{darks,flats,biases}/` (calibration,
   each one internally-uniform exposure/optics group) + one `<session>/<set>/`
   per single-pointing light set. Any siril-readable raw works — no conversion.
2. `scripts/stack/run_pipeline.sh <session> <set>` (auto-routes matched-flat vs
   self-flat by whether flats' optics match the set) → `results/stack_<set>.fit`.
3. Plate-solve (`scripts/calibrate/solve_field.py`) → SPCC (`spcc_run.py`) →
   render (`scripts/render/starcomb.py`).
4. A set with no `config_<set>.json` **degrades loudly** (whole-frame gate, no
   MW-corridor / foreground masks, `mw_boost` skipped) — safe, just generic.
   Derive geometry once the field is solved.

Per-dataset state (own approved recipe, own byte-reproduce, tracked config for
a copyright-ignored dataset) is still thin — see the multi-dataset architecture
item in BACKLOG.
