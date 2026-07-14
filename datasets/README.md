# datasets/ — tracked per-dataset state

Session data dirs are gitignored (raw frames; several are third-party
sets that must never be committed), so everything the repo must VERSION
about a dataset lives here, keyed `datasets/<session>/<set>/`:

| file | role | consumed by |
|---|---|---|
| `geometry.json` | per-set composition facts: terrestrial `foreground` (rect \| npz `mask` path, session-relative), `judgment_crops`, optional `starsep` overrides | `astrometrics.configure()` in every product entry point |
| `recipe.json` | the processing knobs for this dataset: `render` dict (same names as starcomb's GENERIC table), optional `spcc` dict (broadband: `oscsensor`/`oscfilter`/`whiteref` — names from siril `spcc_list`; narrowband: `narrowband: true` + `rwl`/`gwl`/`bwl` wavelengths in nm [+ `rbw`/`gbw`/`bbw` bandwidths] — the marker that also resolves `stretch_linked: auto` to the per-line palette stretch; absent = sensor-null broadband, the generic default), optional `frame_qa` dict (`{metric: [lo, hi]}` WARN-bound overrides for the registration inspection's per-frame quality checks — a known-drifty class states its measured envelope here instead of warning forever), optional `stack` dict (`{"weight": "wfwhm"\|"nbstars"\|null, "exclude": [frame numbers]}` — per-dataset stack policy; ABSENT block, null weight and empty list are all the generic default: today's unweighted `rej 3 3` over all registered frames, generated scripts byte-identical. Frame numbers in `exclude` are the sequence file numbers the registration inspection records as `n` — the same numbers its outlier flags name; a dual-band set's one list governs BOTH extracted line stacks. The runner verifies after every excluded stack that exactly the named file numbers were deselected and hard-fails, removing the stack, if registration drops broke the mapping (siril's `unselect` is positional; a reduced sequence keeps its numbers with gaps — measured). A weight or cull is only ever adopted through a measured with-vs-without ladder: siril's `-weight` is a min-max RAMP over the sequence — soft-culling, measured +21% sky noise at 7.4% FWHM CV — and every change here rebuilds the stack = declared delta), optional `render_engine` (`auto`\|`starcomb`\|`nightlight`; auto -> `nightlight` for a mono-filters narrowband SHO composition, so `starcomb.py` delegates to `nightlight_sho.py` — the author's tool recovers the O3 sphere; else the in-house chain) + its `nightlight` dict (develop params: `stretch_scale` [brightness], `saturation`, `scnr`, `black_sigma`, `hue_*`, `o3_emphasis` [labelled teal boost]), `status` (`approved` \| `provisional`) + `approved` provenance + per-knob `notes` | `starcomb.resolve_recipe()`/`resolve_engine()`, `nightlight_sho.py` and `spcc_run.py` — resolution is CLI > recipe > GENERIC, printed per run; `inspect_stage.py` reads `frame_qa` the same way (recipe > generic EXPECTATIONS, provenance printed); `run_pipeline.sh` reads `stack` at stack time (recipe-only knob — no generic layer to override — provenance printed per run) |
| `baseline.json` | the recorded no-regression target: pinned stack identity (sha256), rebuild command, expected gate/shell metrics, artifact hashes; written by `sweep.py --rebaseline`, never by hand. A `color_scope_ack: true` record (written only via `--ack-color-scope`, legal only when colour is the SOLE failing gate metric — the emission-flooded class) is swept with the achromatic thresholds fully enforced and colour graded one-sided vs the record; full colour admission waits on the colour-gate redesign | `scripts/qa/sweep.py` |
| `experiments.jsonl` | the tuning-experiment ledger: one append-only record per `starcomb.py` ladder (param, values, control, hypothesis, pinned stack identity, verdict), closed by `--verdict win\|null\|deadend --because "…"`. The durable, tracked index of what was tried and how it resolved — the heavy per-value finals live in gitignored `results/exp_*/`; a killed hypothesis is ALSO written to NOTES with its mechanism | `starcomb.py` ladder (append) + `--verdict` (close) |
| `../GENERIC.json` | the repo-wide base layer: generic knob values + per-knob provenance notes (what each value encodes, known class limits). Changes are declared deltas through the sweep; approved recipes are immune (they pin every knob) | `starcomb.load_generic()` — hard-fails on schema drift |
| `composition.json` | how a multi-line/multi-filter target's composed linear stack is BUILT. `kind: dualband-osc` — extraction params + `lines` (the ingest splits one set's CFA frames). `kind: mono-filters` — `members` (channel name → sibling per-filter SET), `reference` (the member the others align to; it alone stays un-interpolated), keyed by a VIRTUAL target name with no lights dir of its own. Both carry the `channels` R/G/B palette mapping. Build-side facts ONLY — calibration/render knobs stay in `recipe.json`. Absent file = ordinary single stack (degrade-loudly rule) | `run_pipeline.sh` (ingest fork) + `scripts/stack/compose.py` |

Rules (the same contract as README "How a change is accepted"):

- A dataset with **no recipe** renders with the GENERIC defaults and
  says so loudly — generic is honest, not approved. It never inherits
  another dataset's look.
- An **approved** recipe pins EVERY knob (a later change to a generic
  default must not silently restyle an approved render). A provisional
  recipe pins only what it means to pin.
- `baseline.json` is measurement output. After an approved change:
  re-render, get the delta judged if aesthetic, then
  `sweep.py --rebaseline <session>/<set>` and git-tag. The tag is the
  record.
- Geometry mask files (`*.npz`) are DERIVED data — they live in the
  session dir (`work/`) and are regenerated by
  `scripts/geometry/suggest_foreground.py`; `geometry.json` only points
  at them.
