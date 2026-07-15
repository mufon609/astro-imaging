# CLAUDE.md — operating manual for agents working in this repo

## What this repo IS (read first, every session)

A **checklist + knowledge workspace** for astrophotography image processing —
**NOT an image processor, and NOT an in-house measurement engine.** Every pixel
operation AND every measurement of an image is performed by an **official
industry tool** (Siril, PixInsight, ASTAP, GraXpert, RC-Astro, StarNet,
astrometry.net, …); the repo's own code never processes or analyzes the
deliverable's pixels. It does four things:

- **ORCHESTRATE** — drive those tools headless, per dataset, as a sequenced
  checklist; resolve config; package judgment sets.
- **RECORD** — version the *process* (scripts, docs, per-dataset state, the
  dead-end registry, git), never image data: what was done, what each tool
  measured, what's approved, what's ruled out *with its mechanism*.
- **RESEARCH** — constantly, from official docs + forums, to get the most out of
  each tool and keep the toolkit ([`TOOLS.md`](TOOLS.md)) current. First-class
  and ongoing, not occasional.
- **AUDIT THE PROCESS** — inspect config / logic / sequence / tuning for errors
  and drive every fix from a **researched root cause**; never thrash knobs
  hoping the output changes.

**The bright line — what in-house code may and may not do:**
- **FORBIDDEN** if it does ANY of: (1) reads or analyzes the deliverable's
  pixels; (2) makes an automated judgment / threshold call that gates, shapes,
  or tunes the final product; (3) reimplements an analysis an official tool
  already provides.
- **ALLOWED** only if ALL hold: (1) it is *outside* the final-product pipeline
  (a checklist / record / orchestrator / standalone detector — never a gate or
  processor on the deliverable); (2) every pixel and every standard measurement
  it uses comes from an official tool; (3) it computes only a *derived* result
  no tool provides; (4) it examines and reports only — rewrites no deliverable,
  never auto-decides the final product; (5) it carries a removal condition.

`scripts/qa/anomaly_audit.py` is the reference **ALLOWED** example (Siril does
every pixel op + measurement; the in-house kernel does only the streak geometry
no tool provides; report-only; removal-conditioned). An in-house **gate or audit
that reads the render and blocks it** would be the reference **FORBIDDEN** case;
the tools' own analysis + the checklist do that job.

**Anti-drift test:** if you are about to hand-tune a knob to make one image look
right, write numpy that reads / transforms / analyzes the deliverable's pixels,
or reimplement a measurement a tool already gives — STOP. Research the tool, drive
it, record what it measured, and fix the PROCESS from the root cause, not the
picture.

**This repo targets x86.** Processing and measurement are done entirely by
industry tools ([`TOOLS.md`](TOOLS.md) — the toolkit); the target environment is
in "Environment" below and the x86 build order is
[`docs/x86-empirical-test-plan.md`](docs/x86-empirical-test-plan.md). The repo is
the orchestration + records + discipline around the tools.

**Read order, every session:** (1) this file; (2) [`docs/dead-ends.md`]
(docs/dead-ends.md) — the **DEAD-END registry** (never re-attempt those — read it
before proposing any experiment) + the acquisition checklist;
(2b) `TOOLS.md` — the tier-by-tier tool audit (every option per pipeline
stage, when/why, cost/Linux/CPU/headless) — the TOOLKIT the x86 render is
built from; (2c) `MEMORY.md` — the collaboration context (who the user is,
how they judge/work) + residual lessons migrated off the machine-local
auto-memory so they transfer with the repo; (3) `README.md` — the process
contract (review
contract + standing audits, per-set geometry, experiment discipline, north
star). The DURABLE stage design (stack/calibrate/compose/solve/SPCC) lives in
the kept scripts' own docstrings. `docs/` holds research
deep-dives (one cited `.md` per major investigation — see `docs/README.md`),
whose durable findings graduate into TOOLS / `docs/dead-ends.md` / MEMORY.
`BACKLOG.md` is a stub (superseded by the x86 test plan). Full history lives in
`git log` — the complete pre-reset chain AND the old NOTES.md are at the
`checkpoint` commit.
Per-dataset state is the tracked `datasets/<session>/<set>/` records; NOTE
its `recipe.json` render blocks + `baseline.json` are chain-coupled and
PENDING the new chain.

## Environment

**Target (go-forward): x86-64 Kali** — Intel i7 14th-gen, 32 GB RAM, 1 TB
NVMe, **no GPU**. The full tool inventory + the reasons the arm64
workarounds die are in [`TOOLS.md`](TOOLS.md). In one line: x86 unlocks native
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
  `df` at session start). These constraints DIE on x86.
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
  pre-registered BEFORE the run (the experiment record + the dead-end
  registry, `docs/dead-ends.md`). A measurement that kills a hypothesis becomes
  a dead-end entry in `docs/dead-ends.md` WITH ITS NUMBERS before anything else
  is tried.
- **Nothing is final until it is empirically tested on real data.** A
  mechanism analysis, a doc reading, or a comparison of source is a
  HYPOTHESIS, not a verified fact — mark it as such and state the concrete
  test that would settle it. (Live example: native Siril solve was
  *mechanism-verified* not to replace `solve_field.py` for trailed fields —
  TOOLS.md — but that is provisional until the x86 empirical test runs.)
  Especially across the rig migration: every arm-era finding is a
  hypothesis on the desktop until re-measured there.
- **Official tools do ALL pixel work — processing AND analysis** (the bright
  line in "What this repo IS"). In-house code never reads, transforms, or
  analyzes the deliverable's pixels, never auto-gates the final product, and
  never reimplements a measurement a tool provides. It may only orchestrate,
  record, research, and run *standalone* gap-filler detectors that source every
  pixel + measurement from a tool and carry a removal condition
  (`scripts/qa/anomaly_audit.py` is the model; the astrometry.net precedent).
  When no tool provides a mechanism, that is a **documented gap** — never a
  silent numpy substitute.
- **Root cause over thrash.** When output is wrong, AUDIT the config / logic /
  sequence / tuning and RESEARCH the tool (official docs + forums) to find the
  cause, then fix THAT. Never try random knob values hoping the output changes —
  a change with no researched cause is a bandaid.
- **Research is standing work.** Keep the toolkit ([`TOOLS.md`](TOOLS.md))
  current from primary sources; a tool's best setting is discovered by reading
  its docs + the community, not guessed.
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
  dead-end entry in `docs/dead-ends.md` with its numbers). Comparisons report measured deltas with an
  objective WIN | NULL | needs-eyes verdict — NEVER "fixed/final/matched/
  close" language; aesthetics are the user's eyes on the finals.
- **Acceptance measures come from the tools and don't loosen.** The measures that
  gate a candidate are the tools' own numbers, recorded in the per-dataset
  checklist (README review-contract); loosening one needs explicit user ratification.
- **Aesthetic changes need the user's eyes on FULL-FRAME LOSSLESS
  finals** (PNG16+PNG8, opened independently in the user's own viewers)
  before any bake — never crops, composited panels, or any lossy
  surface; objective fixes with pass/fail metrics may commit. Compare
  renders in LIKE encodings.
- **A change is accepted by three checks, never by byte-identity with one
  dataset** (README "How a change is accepted"): the render is REPRODUCIBLE
  (pinned tool versions/params/seeds, no unseeded step; verified cheaply to a
  documented tolerance — NOT a byte-identical double-render, since the neural
  tools' multi-threaded inference isn't bit-reproducible); the affected data
  class(es) + a canary still PASS the tool-sourced acceptance checklist (its
  measures never loosen; the full-suite sweep is a cadence / pre-release run,
  not every commit); and any render the change alters is a **declared delta** —
  report metric deltas + like-encoding panels, objective-better-or-equal may
  commit, anything aesthetic needs the user's eyes, then re-baseline and tag.
  Freezing one imperfect render as "correct" only breeds bandaids to preserve
  it.
- **No session/stream/ladder tags in script comments** — plain,
  standalone descriptions with their measured numbers; provenance
  narrative lives in git only.
- **Maintain the dead-end registry (`docs/dead-ends.md`) IN PLACE**: add/refine
  the mechanism entries (data/physics/tool-doctrine); never append chronological
  session narrative. The durable stage-design "why" lives in each kept
  script's docstring — keep it there, update in place.
- **New datasets get tracked per-dataset state** in
  `datasets/<session>/<set>/` — `acquisition.json` (EXIF facts auto-derived +
  the declared `mount` fixed/tracked that EXIF can't record; a consumer needing
  it STOPS and asks rather than assume — `scripts/lib/acquisition.py`),
  `geometry.json` (foreground mask/rect),
  `recipe.json` (render knobs; approved looks pin every knob),
  `baseline.json` (written only by the no-regression harness — pending x86) —
  never dataset-specific script patches; a dataset without them must
  degrade loudly, not inherit silently. (The existing recipe render blocks +
  baselines are chain-coupled and PENDING the new chain's schema.)
- Background long siril/render runs and keep working; preserve stacks
  per experiment (`cp` to tagged names); track disk.

## North star (the goal the identity above serves)

The workspace constantly drives industry tools to judge + process its images,
and audits its own PROCESS, so that eventually ANY dataset can be dropped into a
session dir and be carried — by those tools — to its best honest outcome.
Every divergence from the standard workflow is a measured adaptation carrying
its removal condition; the tools are a toolkit picked per dataset; finals as
close to lossless as possible; and acquisition quality (the checklist in
`docs/dead-ends.md`) outranks processing — never bandaid what photons must fix.
