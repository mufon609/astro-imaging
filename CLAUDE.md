# CLAUDE.md — operating manual for agents working in this repo

**Read order, every session:** (1) this file; (2) `README.md` — the
process contract (workflow mapping, review contract + standing audits,
per-set geometry, experiment discipline, north star); (3) `NOTES.md`
top to bottom — the technical pipeline: the environment, the design
with each knob's technical why, the DEAD-END registry (never re-attempt
those), bandaid ledger, acquisition checklist; (4) `BACKLOG.md` —
deferred work + the pick-up order (self-governing; its IDs never leave
that file). Full history lives in `git log` (every commit carries the
NOTES of its time; approved recipes are git-tagged).
Per-dataset state (what is approved for a set, its measured baseline)
is the tracked `datasets/<session>/<set>/` records — trust them over
anything here.

## Environment (this rig)

- Siril 1.4.4 as a **user flatpak**, not on PATH:
  `flatpak run --command=siril-cli org.siril.Siril -d <workdir> -s <script>`
  The sandbox has home/host access but **its own private /tmp**: `.ssf`
  scripts MUST live under $HOME (repo `scripts/` or `<session>/work/`),
  never /tmp or a scratchpad.
- Kali linux arm64, 4 cores, 7.7 GB RAM, tight disk (single ~118 GB
  volume shared with everything else — check `df` at session start;
  it has run as low as ~6 GB free). The disk is why intermediates are
  16-bit with per-stage cleanup (quantization measured ≈18× below
  per-frame noise → ~+0.3% stack noise: negligible) and why big FITS
  get pruned once their numbers are recorded.
- Host python3: numpy + scipy + PIL, **no astropy** (equatorial→galactic
  is a fixed 3×3 in `scripts/lib/astrometrics.py`), no rawpy.
- GraXpert 3.2 at `~/.local/bin/graxpert` (BGE + denoise only, no star
  removal). exiftool/exiv2 present. Outbound network works.
- Nightlight (the reference author's own open tool) staged as an aarch64
  binary at `~/.cache/astro_stage/nightlight/nightlight_linux_arm64` — the
  SANCTIONED narrowband SHO colour+develop tool (`scripts/render/nightlight_sho.py`):
  star-colour-neutral balance (boosts O3 → reveals the O3 sphere SPCC
  erases) + one global stretch, no star-sep/corings/denoise. Reproduces the
  author's finish on our stacks; `run1/` holds his exact JSON recipe.
- StarNet2 ONNX weights at `~/.local/share/starnet/StarNet2_weights.onnx`
  (from the official Linux x64 CLI zip at download.starnetastro.com;
  license = personal astrophotography use, keep out of the repo) +
  its venv at `~/.local/share/starnet/venv` (onnxruntime aarch64).
  `scripts/render/separation/starnet_sep.py` bootstraps the venv and
  errors loudly if the weights are missing.
- Plate solving: siril's internal solver cannot match this rig's
  ultra-wide trailed-star fields — use `scripts/calibrate/solve_field.py` (blind
  astrometry.net from peak centroids; venv auto-bootstraps at
  `~/.local/share/astrometry-venv`; scale hint derives from the FITS
  header; the configured foreground is excluded from detection).
- Local Gaia catalogs at `~/.local/share/siril/siril_catalogues/`
  (astro + SPCC xpsamp chunks; siril settings already point there).
  SPCC needs the FULL cone of chunks — siril names the first missing
  one. `scripts/calibrate/spcc_cone.py <solved_wcs.fit> [--fetch]` computes
  the nside=2 nested cover from the solved WCS and downloads any missing
  chunk (md5-verified). Re-download source: zenodo 14692304 (astro) +
  14738271 (chunks).

## Binding rules (the contract in README, distilled for agents)

- **One knob per experiment**, control bracketed, hypothesis
  pre-registered in NOTES BEFORE the run. A measurement that kills a
  hypothesis becomes a dead-end entry WITH ITS NUMBERS before anything
  else is tried.
- **Orchestrate industry tools; NEVER hand-roll the image processing.**
  The bright line is PROCESSING vs EXAMINING. Examining numpy (metrics,
  the gate, masks, inspection rendering) is what the pipeline is FOR.
  Processing numpy — anything that rewrites the deliverable's pixels (a
  stretch, denoise, colour transform, saturation, SCNR, combine,
  background fit) — must drive a real tool (Siril / GraXpert / StarNet /
  astrometry.net, or a reference author's own open tool), UNLESS no
  available tool provides the mechanism on this rig, documented as a
  sanctioned alternative with a removal condition (the StarNet-aarch64 /
  DNG / astrometry.net precedent). Every render-chain processing operator
  is catalogued in `scripts/render/operators.json`; `scripts/qa/hand_roll_audit.py`
  (standing, wired into the sweep) fails on an unregistered hand-rolled
  processing function or an incoherent entry. When a tool cannot run here,
  say so and use the sanctioned alternative — never a silent numpy
  substitute. The render chain (`starcomb.py`) is currently TOOL-ONLY:
  every pixel-rewriting operator drives Siril (autostretch/mtf/pm/satu/
  denoise/subsky), GraXpert (BGE/denoise) or StarNet2, and narrowband SHO
  colour+develop routes to Nightlight (`nightlight_sho.py`) — no
  sanctioned-numpy processing operator remains in the catalog (the
  carve-out stays available for a future mechanism no tool provides).
- **No bandaids.** Never compress, darken, crop, or otherwise HIDE a
  symptom instead of fixing its cause. A blown star means the
  stretch/balance upstream is wrong; a rim artifact is in the data — fix
  the cause or do not ship it. If a step's only purpose is to mask what a
  prior step broke, it is a bandaid. (A linear black-point shift that
  preserves all differences is NOT a bandaid; compressing the histogram to
  hide blown tops IS.)
- **Every build emits per-stage visibility; every tuning run is a measured
  experiment; every result is a WIN or a clean NULL.** Stage visibility
  (`<final>_stages/` + `index.html`, standing on every render) shows the
  treatment at each step. A tuning experiment is one knob, control
  bracketed, `--hypothesis` required, judged on full-frame lossless
  finals, closed with `--verdict` into the tracked per-dataset
  `experiments.jsonl` (a killed hypothesis also becomes a NOTES dead-end
  with its numbers). Comparisons report measured deltas with an objective
  WIN | NULL | needs-eyes verdict — NEVER "fixed/final/matched/close"
  language; aesthetics are the user's eyes on the finals.
- **The gate never loosens** (`bg_qa.py`'s statistical sky-scope
  thresholds; scope changes need explicit user ratification).
  Star-shell/clip0 metrics are REPORTED or WARN context — never
  silently gated.
- **Aesthetic changes need the user's eyes on FULL-FRAME LOSSLESS
  finals** (PNG16+PNG8, opened independently in the user's own viewers)
  before any bake — never crops, composited panels, or any lossy
  surface; objective fixes with pass/fail metrics may commit. Compare
  renders in LIKE encodings.
- **A change is accepted by three checks, never by byte-identity with one
  dataset** (README "How a change is accepted"): the render is DETERMINISTIC
  (run twice on the same inputs → identical artifacts); every registered
  dataset still PASSES the gate + star-shell + inspection (gate thresholds
  never loosen); and any render the change alters is a **declared delta** —
  report metric deltas + like-encoding panels, objective-better-or-equal may
  commit, anything aesthetic needs the user's eyes, then re-baseline and tag.
  Freezing one imperfect render as "correct" only breeds bandaids to preserve
  it.
- **No session/stream/ladder tags in script comments** — plain,
  standalone descriptions with their measured numbers; provenance
  narrative lives in NOTES/git only.
- **Maintain NOTES.md in its refactored shape**: update the design /
  knob-provenance / dead-ends / ledger IN PLACE; never append
  chronological session narrative.
- **New datasets get tracked per-dataset state** in
  `datasets/<session>/<set>/` — `geometry.json` (foreground mask/rect),
  `recipe.json` (render knobs; approved looks pin every knob),
  `baseline.json` (written by `sweep.py --rebaseline` only) — never
  dataset-specific script patches; a dataset without them must degrade
  loudly, not inherit silently.
- Background long siril/render runs and keep working; preserve stacks
  per experiment (`cp` to tagged names); track disk.

## North star (the user's standing goal)

A pipeline that constantly audits its images and process steps so that
eventually ANY dataset can be dropped into a session dir and be
properly judged and processed to its best honest outcome. Every
divergence from the standard workflow is a measured adaptation carrying
its removal condition; finals as close to lossless as possible; and
acquisition quality (the checklist in NOTES) outranks processing —
never bandaid what photons must fix.
