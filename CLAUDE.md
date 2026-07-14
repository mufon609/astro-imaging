# CLAUDE.md — operating manual for agents working in this repo

## What this repo IS (read first, every session)

A **self-auditing orchestration harness** for astrophotography — **NOT an
image processor.** It does three things, and refuses a fourth:

- **RECORD** — versions the *process* (scripts, docs, per-dataset state, the
  dead-end registry, git history), never the image data. The durable memory
  of what was tried, what's approved, and what's ruled out *with its mechanism*.
- **AUDIT** — measures everything. Each image is graded by the gate + the
  standing audits; each process step by the orchestrate guard, the
  no-regression sweep, and the determinism check — against objective,
  never-loosening measures. **The measurement layer IS the product.**
- **AUTOMATE** — sequences and drives industry tools headless, resolves
  per-dataset config, and packages judgment sets, so ANY dataset can be
  dropped in and carried to its best honest outcome.

The fourth thing it **refuses to do — process pixels itself.** Every
operation that rewrites the deliverable's pixels drives a real,
industry-standard tool (Siril, GraXpert, StarNet, RC-Astro, astrometry.net,
or a reference author's own open tool). The repo's own code only EXAMINES
(measures) and ORCHESTRATES (sequences / config / judgment). No tool for a
mechanism = a documented gap, **never a numpy hand-roll.**

**This inversion is the whole point.** Processing is commoditized — great
free and paid tools exist ([`TOOLS.md`](TOOLS.md)) — so the repo spends ALL
its effort on the parts that aren't: rigorous measurement, honest
orchestration, and a permanent record. It is therefore NOT an image
processor, NOT a home for hand-rolled processing, NOT a chaser of one image's
look (aesthetics are the user's eyes on lossless finals — the repo emits
measured *candidates*, not a hand-crafted picture), and NOT a frozen chain
(the tools are a TOOLKIT, picked per dataset for a stated reason).

**Anti-drift test for any session:** if you are about to hand-tune a knob to
make one image look right, or to write numpy that transforms deliverable
pixels — STOP, you have left the mission. Drive a tool, measure the result,
and change the PROCESS, not the picture.

**This repo is mid-migration to x86 — read [`REDESIGN.md`](REDESIGN.md)
first.** The render chain and the aarch64 workarounds were wiped in the
x86 reset; the durable core (measurement/audit + calibration/stack/compose)
is kept and the chain is rebuilt tool-first on x86. REDESIGN.md is the
go-forward authority (target env, keep/wipe manifest, rebuild order).

**Read order, every session:** (1) this file; (2) `REDESIGN.md` — the x86
redesign plan AND the durable technical reference: the keep/wipe manifest,
the target architecture, the **DEAD-END registry** (never re-attempt those —
read it before proposing any experiment), and the acquisition checklist;
(2b) `TOOLS.md` — the tier-by-tier tool audit (every option per pipeline
stage, when/why, cost/Linux/CPU/headless) — the TOOLKIT the x86 render is
built from; (2c) `MEMORY.md` — the collaboration context (who the user is,
how they judge/work) + residual lessons migrated off the machine-local
auto-memory so they transfer with the repo; (3) `README.md` — the process
contract (review
contract + standing audits, per-set geometry, experiment discipline, north
star). The DURABLE stage design (stack/calibrate/compose/solve/SPCC/
self-flat) lives in the kept scripts' own docstrings. `docs/` holds research
deep-dives (one cited `.md` per major investigation — see `docs/README.md`),
whose durable findings graduate into TOOLS/REDESIGN/MEMORY. `BACKLOG.md` is a
stub (superseded by REDESIGN). Full history lives in `git log` — the complete
pre-reset chain AND the old NOTES.md are at the `checkpoint` commit.
Per-dataset state is the tracked `datasets/<session>/<set>/` records; NOTE
its `recipe.json` render blocks + `baseline.json` are chain-coupled and
PENDING the new chain.

## Environment

**Target (go-forward): x86-64 Kali** — Intel i7 14th-gen, 32 GB RAM, 1 TB
NVMe, **no GPU**. The full tool inventory + the reasons the arm64
workarounds die are in REDESIGN.md. In one line: x86 unlocks native
StarNet/StarXTerminator, NoiseXTerminator/Cosmic Clarity (the denoise gap),
BlurXTerminator (deconv), and astropy; 32 GB/1 TB relax the RAM/disk
adaptations (32-bit intermediates, no partitioned stacking); no GPU means
CPU-only AI inference (measure wall-clock). Tool paths are set during x86
setup.

**Current BASE rig (arm64, until migration) — the facts to run the durable
core here now:**
- Siril 1.4.4 as a **user flatpak**, not on PATH:
  `flatpak run --command=siril-cli org.siril.Siril -d <workdir> -s <script>`
  The sandbox has home/host access but **its own private /tmp**: `.ssf`
  scripts MUST live under $HOME (repo `scripts/` or `<session>/work/`),
  never /tmp or a scratchpad. Siril also has an integrated Python API
  (`pyscript` + bundled `sirilpy`) that runs headless via an `.ssf` wrapper
  (`requires 1.4.0` + `pyscript foo.py`) — proven on this rig.
- Kali linux arm64, 4 cores, 7.7 GB RAM, tight ~118 GB shared disk (check
  `df` at session start). These constraints DIE on x86 (REDESIGN).
- Host python3: numpy + scipy + PIL, **no astropy** (equatorial→galactic
  is a fixed 3×3 in `scripts/lib/astrometrics.py`), no rawpy. astropy is
  available on x86.
- GraXpert 3.2 at `~/.local/bin/graxpert` (BGE + denoise). exiftool/exiv2
  present. Outbound network works.
- Plate solving: siril's internal solver cannot match ultra-wide
  trailed-star fields (a DATA issue, not arch) — use
  `scripts/calibrate/solve_field.py` (blind astrometry.net from peak
  centroids; venv auto-bootstraps at `~/.local/share/astrometry-venv`;
  scale hint from the FITS header; configured foreground excluded).
- Local Gaia catalogs at `~/.local/share/siril/siril_catalogues/`
  (astro + SPCC xpsamp chunks; siril settings already point there).
  SPCC needs the FULL cone of chunks — siril names the first missing
  one. `scripts/calibrate/spcc_cone.py <solved_wcs.fit> [--fetch]` computes
  the nside=2 nested cover from the solved WCS and downloads any missing
  chunk (md5-verified). Re-download source: zenodo 14692304 (astro) +
  14738271 (chunks).

## Binding rules (the contract in README, distilled for agents)

- **One knob per experiment**, control bracketed, hypothesis
  pre-registered BEFORE the run (the experiment record + REDESIGN's
  dead-end registry). A measurement that kills a hypothesis becomes a
  dead-end entry in REDESIGN WITH ITS NUMBERS before anything else is tried.
- **Nothing is final until it is empirically tested on real data.** A
  mechanism analysis, a doc reading, or a comparison of source is a
  HYPOTHESIS, not a verified fact — mark it as such and state the concrete
  test that would settle it. (Live example: native Siril solve was
  *mechanism-verified* not to replace `solve_field.py` for trailed fields —
  TOOLS.md — but that is provisional until the x86 empirical test runs.)
  Especially across the rig migration: every arm-era finding is a
  hypothesis on the desktop until re-measured there.
- **Orchestrate industry tools; NEVER hand-roll the image processing.**
  The bright line is PROCESSING vs EXAMINING. Examining numpy (metrics,
  the gate, masks, inspection rendering) is what the pipeline is FOR.
  Processing numpy — anything that rewrites the deliverable's pixels (a
  stretch, denoise, colour transform, saturation, SCNR, combine,
  background fit) — must drive a real tool (Siril / GraXpert / StarNet /
  StarXTerminator / NoiseXTerminator / BlurXTerminator / astrometry.net, or a
  reference author's own open tool), UNLESS no available tool provides the
  mechanism, documented as a sanctioned alternative with a removal condition
  (the astrometry.net precedent). This is the whole thesis of the x86
  redesign (REDESIGN.md): a THIN orchestration layer over best-in-class
  tools. The wiped chain proved it end-to-end (tool-only, in history at the
  `checkpoint` commit); the x86 rebuild re-establishes the operator catalog +
  the standing hand-roll guard around the new chain. When a tool cannot run,
  say so and use the sanctioned alternative — never a silent numpy substitute.
- **No bandaids.** Never compress, darken, crop, or otherwise HIDE a
  symptom instead of fixing its cause. A blown star means the
  stretch/balance upstream is wrong; a rim artifact is in the data — fix
  the cause or do not ship it. If a step's only purpose is to mask what a
  prior step broke, it is a bandaid. (A linear black-point shift that
  preserves all differences is NOT a bandaid; compressing the histogram to
  hide blown tops IS.)
- **Every build emits per-stage visibility; every tuning run is a measured
  experiment; every result is a WIN or a clean NULL.** (A REQUIREMENT the
  rebuilt x86 chain carries: a labeled per-stage sequence on every render, so
  a final-render defect localizes to the stage that introduced it.) A tuning
  experiment is one knob, control bracketed, hypothesis required, judged on
  full-frame lossless finals, closed with a verdict into the tracked
  per-dataset `experiments.jsonl` (a killed hypothesis also becomes a
  dead-end entry in REDESIGN with its numbers). Comparisons report measured deltas with an
  objective WIN | NULL | needs-eyes verdict — NEVER "fixed/final/matched/
  close" language; aesthetics are the user's eyes on the finals.
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
  narrative lives in git only.
- **Maintain REDESIGN's dead-end registry IN PLACE**: add/refine the
  mechanism entries (data/physics/tool-doctrine); never append chronological
  session narrative. The durable stage-design "why" lives in each kept
  script's docstring — keep it there, update in place.
- **New datasets get tracked per-dataset state** in
  `datasets/<session>/<set>/` — `geometry.json` (foreground mask/rect),
  `recipe.json` (render knobs; approved looks pin every knob),
  `baseline.json` (written only by the no-regression sweep, re-ported on
  x86) — never dataset-specific script patches; a dataset without them must
  degrade loudly, not inherit silently. (The existing recipe render blocks +
  baselines are chain-coupled and PENDING the new chain's schema —
  REDESIGN.md.)
- Background long siril/render runs and keep working; preserve stacks
  per experiment (`cp` to tagged names); track disk.

## North star (the goal the identity above serves)

The harness constantly audits its images and process steps so that
eventually ANY dataset can be dropped into a session dir and be properly
judged and processed — by industry tools — to its best honest outcome.
Every divergence from the standard workflow is a measured adaptation carrying
its removal condition; the tools are a toolkit picked per dataset; finals as
close to lossless as possible; and acquisition quality (the checklist in
REDESIGN) outranks processing — never bandaid what photons must fix.
