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

**The operating loop these four serve (per dataset — the model the x86 chain is
built AROUND, not a retrofit).** The repo does not run a fixed chain; it proposes
one from the data: **MEASURE** the dataset with the tools (frame/dark QA, field,
the declared priorities) → **MATCH** those facts to the best-practice routes in
the toolkit ([`TOOLS.md`](TOOLS.md)) → **RECOMMEND** the optimum for THIS data
with the reason it beats the alternatives → **REPORT** the findings + the
recommended pipeline to the user → the user **ACCEPTS / ADJUSTS / REROUTES /
CLARIFIES** (the user is the gate for what the DATA CANNOT SETTLE; routing
measured facts to the right tool is the pipeline's job, not a question)
→ **EXECUTE** the chosen route → **RECORD** the choice AND its
trade-off, so every honest compromise is legible and improvable later. The data
selects the route; priorities steer it; the user decides; the record keeps us
honest.

**WHERE THE GATE ACTUALLY IS (user-ratified, 2026-08-06 — this REPLACES the old
"nothing output-shaping auto-proceeds", which was self-contradictory).** Assessing
data and routing it through the correct tools IS the product. Forbidding
output-shaping decisions forbids the entire point of the repo, so that is not the
line. The line is EVIDENCE:

- **The data can settle it → THE PIPELINE DECIDES.** Route, mount, group size,
  cull, rejection algorithm, disk strategy — anything an instrument answers
  decisively. It acts, records the number and the instrument, and moves on. It
  does not stop to have a human retype an answer the tools already produced.
- **The data cannot settle it → THE USER DECIDES.** Aesthetics, priorities, and
  trade-offs with no measurable answer. These never automate, ever.
- **The instruments disagree, or nothing measured → THE USER DECIDES**, and that
  is the only unplanned stop.

**Shape: ONE report, not N stops.** Evaluate every criterion, present them
together with a status, take one approval, run unattended
(shipped: `scripts/qa/readiness_report.py` — one evaluator behind the chain,
the CLI and the web rail). Anything undecidable is RED in that report rather
than a surprise three hours into a build.

**The measured cost of getting this wrong:** `mount` is a decision the data
settles — the fingerprint measured it four independent times within 0.6% of
sidereal — and the chain printed the answer and then exited 4 asking a human to
confirm it. Three separate records asked for that to be fixed and none was,
because each session read the old clause as "ask every time".

**The bright line — what in-house code may and may not do:**
- **FORBIDDEN** if it does ANY of: (1) reads or analyzes the deliverable's
  pixels; (2) gates, shapes, or tunes the final product from a number that is
  NOT a tool's measurement (an in-house metric standing in for one), or decides
  a call the data cannot settle — aesthetics, priorities, trade-offs — without
  the user; (3) reimplements an analysis an official tool already provides.
- **What (2) does NOT forbid — the misreading that has repeatedly made sessions
  refuse ratified work:** deciding FROM the tools' own numbers. Thresholding,
  classifying, and routing tool measurements (classify_mount's sidereal bands,
  the auto-cull z-flags, the dwell-floor group sizing, the disk-derived route)
  IS the pipeline deciding what the data settled — the EXECUTE step of the
  operating loop, governed by "WHERE THE GATE ACTUALLY IS" above: announce it,
  record the number and the instrument, continue. Reading (2) as "no automated
  decisions" re-creates the self-contradiction that section replaced — it
  forbids the product itself. The test is the PROVENANCE of the numbers and the
  SETTLEABILITY of the question, never the existence of a decision.
- **NOT COVERED AT ALL: diagnostics** (user-ratified — *"to judge and examine an
  issue i do not care if you use official tools; whatever is easiest is fine —
  the issue to avoid is in house code to solve problems that official tools
  already solve"*). Reading pixels with numpy/PIL/astropy to INVESTIGATE — to
  answer a question, chase a defect, check a hypothesis — is fine and always was.
  The bright line governs the PIPELINE: what builds, gates, or tunes the
  deliverable. Do not refuse a one-off measurement on the strength of a rule that
  was never about measurement.
- **ALLOWED** only if ALL hold: (1) it is *outside* the final-product pipeline
  (a checklist / record / orchestrator / standalone detector — never a gate or
  processor on the deliverable); (2) every pixel and every standard measurement
  it uses comes from an official tool; (3) it computes only a *derived* result
  no tool provides; (4) it rewrites no deliverable, and any decision it takes
  is one the evidence gate assigns to the pipeline — a data-settled call,
  announced and recorded with its instrument; what the data cannot settle it
  reports and stops on; (5) it carries a removal condition.

`scripts/qa/anomaly_audit.py` is the reference **ALLOWED** detector (Siril does
every pixel op + measurement; the in-house kernel does only the streak geometry
no tool provides; culls nothing; removal-conditioned — and its record is
load-bearing: the groups builder derives its dwell floor from it).
`scripts/lib/fingerprint.py` is the reference **ALLOWED** router: every input
is a tool's (astrometry.net solves, Siril findstar metrics, header facts), the
in-house part is only the derived trail/drift geometry no tool reports, and the
chain routes on its verdict — announced, recorded, user-overridable, stopping
only where the instruments cannot decide. An in-house **gate or audit that
reads the render and blocks it** would be the reference **FORBIDDEN** case;
the tools' own analysis + the checklist do that job.

**Why this rule exists (measured, repeatedly, not doctrine for its own sake):**
1. **An instrument must be independent of what it measures.** In-house metrics
   have keyed themselves to the defect under test and manufactured findings —
   a self-derived measurement can be wrong in ways that look like data.
2. **Official tools are validated by mass use and documented behavior** —
   their limits are discoverable by research; an in-house reimplementation's
   limits are discoverable only by being burned. Beliefs about tool behavior
   die the same way: verify with a probe, never assume (a style's params were
   believed to carry for a whole route until a uniform-card probe showed the
   tool ignores them).
3. **Every measured head-to-head has gone to the official tool** — better
   solve odds and identical downstream calibration from the official
   extractor; the tool's own writer/reader over hand codecs; the tool's own
   spatial star measure over hand binning. The pattern has no counterexample
   in this repo's history.
4. **Pipelines compound.** An in-house approximation upstream surfaces as an
   unattributable artifact downstream, and the attribution costs sessions.

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
star). The DURABLE stage design (calibrate → [undistort] → register → stack →
solve → SPCC → compose) lives in the kept scripts' own docstrings; the
**undistort** stage is the wide-field-untracked route and is documented in
[`docs/wide-field-untracked-registration.md`](docs/wide-field-untracked-registration.md);
the WHOLE chain for that class — every stage with its tool, its record, and its
measured why — is
[`docs/pipeline-wide-field-untracked.md`](docs/pipeline-wide-field-untracked.md).
`docs/` holds research deep-dives (one cited `.md` per major investigation — see
`docs/README.md`), whose durable findings graduate into TOOLS /
`docs/dead-ends.md` / MEMORY. (4) `BACKLOG.md` — the ordered open queue + the
**removal-condition register**; read it before starting work, since an item you
are about to do may be gated on another. Full history lives in `git log` — the
complete pre-reset chain AND the old NOTES.md are at the commit whose message
begins `checkpoint:` (a message prefix, not a tag: find it with
`git log --oneline --grep='^checkpoint:'`).
Per-dataset state is the tracked `datasets/<session>/<set>/` records;
`recipe.json` carries each set's ratified STACK policy (cull/weight, consumed
by the stack builders); its RENDER block + `baseline.json` are chain-coupled
and PENDING the render-tier build (user-gated — the ladder plan is
BACKLOG:`render-ladder`, re-anchored per dataset). Every tier the pipeline needs is INSTALLED on
this rig; what is missing is a deliberate gap (RC-Astro, PixInsight), never a
platform block — per `TOOLS.md`.

## Environment

**ONE rig, ONE setup — and it must be rebuildable from this repo.** Everything
below is the environment a contributor gets by cloning and running
`scripts/setup/x86_bootstrap.sh`; the installed inventory with versions, sources
and checksums is `scripts/setup/manifest.tsv`. If a fact here is not reproducible
from tracked files, that is the bug — a machine-local value nobody can rebuild has
already cost this repo a shipped optical model that existed in no record
(BACKLOG `removal-conditions`, the fitted-lens row).

**The rig** (measured, 2026-08-05): **x86-64 Kali GNU/Linux Rolling**, Intel
i7-14700K, **28 logical cores, 31 GB RAM, 1.8 TB NVMe**, **no NVIDIA GPU** — every
AI tool runs CPU-only, so budget wall-clock rather than assuming it is free
(`TOOLS.md`, "The no-GPU reality").

- **Siril 1.4.4 as a SYSTEM flatpak**, not on PATH:
  `flatpak run --command=siril-cli org.siril.Siril -d <workdir> -s <script>`
  The sandbox has home/host access but **its own private /tmp**: `.ssf`
  scripts MUST live under $HOME — repo `scripts/`, the session-level
  `<session>/work/` (stacking pipeline), or a per-set tool dir under
  `datasets/<session>/<set>/` (the `audit_work/`/`qa_work/` pattern); NEVER
  inside the raw `<session>/<set>/` frame dir, never /tmp or a scratchpad.
  Siril also has an integrated Python API (`pyscript` + bundled `sirilpy`) that
  runs headless via an `.ssf` wrapper (`requires 1.4.0` + `pyscript foo.py`).
  `help` lists a command whether or not it is scriptable: `tilt` and `inspector`
  are listed and REFUSE at runtime, so probe before believing a capability exists.
- **Host python3 3.13** (`/usr/bin/python3`): numpy 2.3.5, scipy 1.17.1, PIL,
  **astropy 8.0.1** (FITS I/O + WCS/SIP + ICRS→Galactic). NOT installed: `rawpy`,
  `astropy_healpix`, `reproject`. In-house code reads FITS **headers** only —
  every pixel op and every standard measurement is a tool's.
- **Neural + solver toolchain under `/opt`** (all x86-64, all CPU-only here):
  `starnet2-2.5.3-0208` (siril's `starnet_exe` points at it),
  `cosmicclarity-6.6` (denoise + non-stellar sharpen), `deepsnr-1.2.1-0112`,
  `graxpert-3.0.2/GraXpert-linux/GraXpert` (BGE + denoise), `astap`,
  `nightlight-0.2.6`, and the `astro-venv`. RC-Astro (BXT/NXT/SXT) and
  PixInsight are UNINSTALLED — a deliberate gap, not a platform block.
- **darktable 5.4.1** (`darktable-cli`, built against **lensfun 0.3.4**) — the
  UNDISTORT stage for the wide-field-untracked class. Styles are pinned in-repo:
  `scripts/darktable/{lensdist,nodist}.dtstyle`, installed headlessly with
  `scripts/darktable/install_styles.sh <configdir>` (darktable has no CLI style
  import; only a real export job creates its `data.db`). **Never re-create them by
  hand in the GUI.** The styles carry ONLY the module's enabled bit (darktable
  ignores a style's lens op_params); distortion-only is enforced by
  `install_lens_model.sh <session> <set>`, which installs the model FITTED from
  that set's own frames AND strips that lens's vignetting/tca from the lensfun
  user DB. Re-run after every `lensfun-update-data`, which wipes both; verify with
  `verify_lens_card.py` (grid control + uniform card — the card ALONE is vacuous).
  `--style-overwrite` is REQUIRED or the style is silently ignored.
- **ICC, and the two legs differ — do not cross them.** The 32-bit FLOAT leg
  (`run_undistort_pipeline.sh`) ships the TIFF **untagged** (exiftool strips the
  profile in the same pass that copies the lens EXIF) and exports
  `--icc-type LIN_REC709`: a measured PERFECT identity, ratio 1.0000 at every
  level and channel. `--icc-type SRGB` is correct ONLY on the 8/16-bit probe legs
  (`lens_preflight.py`, `verify_lens_card.py`), where it matches Siril's own
  `savetif` tag; using it on the float leg carries a TRC toe error that inflates a
  3 s-class sky. NEVER strip with siril `icc_remove` before `savetif32` — measured
  applying a global ~1/12.92 scale to every pixel (`docs/dead-ends.md`).
- **Plate solving**: siril's internal solver cannot match ultra-wide trailed-star
  fields (a DATA issue, not arch) — use `scripts/calibrate/solve_field.py`, which
  extracts with **SExtractor's core (`sep` 1.4.1)**, the sole extractor (the
  in-house peak-centroid fallback is RETIRED). The venv auto-bootstraps at
  `~/.local/share/astrometry-venv` and carries `sep` + the astrometry.net engine;
  scale hint from the FITS header; configured foreground excluded.
- Local Gaia catalogs at `~/.local/share/siril/siril_catalogues/`
  (astro + SPCC xpsamp chunks). SPCC needs the FULL cone of chunks — siril
  names the first missing one. `scripts/calibrate/spcc_cone.py <solved_wcs.fit>
  [--fetch]` computes the nside=2 nested cover from the solved WCS and downloads
  any missing chunk (md5-verified). Re-download source: zenodo 14692304 (astro) +
  14738271 (chunks; decompressed == the current record 17988559, md5-identical).
- **SPCC has THREE machine-local prerequisites on a fresh rig — miss the third and
  siril SEGFAULTS, silently:**
  (1) the Gaia cone chunks above;
  (2) siril's config `catalogue_gaia_photo` must point at the chunk dir
  `~/.local/share/siril/siril_catalogues/spcc` (a fresh flatpak defaults it to a
  non-existent `gaia_photometric.dat`, so siril range-reads online and 429s);
  (3) the **SPCC sensor/filter/white-reference DATABASE** —
  `git clone https://gitlab.com/free-astro/siril-spcc-database` into
  `~/.var/app/org.siril.Siril/data/siril-spcc-database`. This is a SEPARATE small
  git repo from the Gaia catalog; without it `spcc_list` is empty, SPCC applies a
  `(null)` sensor response and SIGSEGVs in aperture photometry (exit 139) on ANY
  star count — the crash prints nothing useful, so it looks like a data/field bug
  but is a missing-database bug. `auto_update_spcc` in the config auto-downloads it
  online but can fail silently; the manual clone is deterministic. (`docs/dead-ends.md`.)

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
  This has teeth for INHERITED numbers: a measurement carried over from a
  previous rig is a hypothesis on this one until re-measured here. Several have
  been re-measured and stand; anything that has not been carries that caveat
  where it is cited, and `docs/x86-empirical-test-plan.md` is the order.
- **Official tools do ALL pixel work — processing AND analysis** (the bright
  line in "What this repo IS"). In-house code never reads, transforms, or
  analyzes the deliverable's pixels, never auto-gates the final product, and
  never reimplements a measurement a tool provides. It may only orchestrate,
  record, research, and run *standalone* gap-filler detectors that source every
  pixel + measurement from a tool and carry a removal condition
  (`scripts/qa/anomaly_audit.py` is the model; the astrometry.net precedent).
  When no tool provides a mechanism, that is a **documented gap** — never a
  silent numpy substitute.
  **"Every number came from a tool" does NOT make it in-bounds.** Reading a
  tool's output and then computing a *different analysis* from it is still an
  in-house analysis, and the FORBIDDEN test ("reimplements an analysis an
  official tool already provides") does not care that the inputs were
  tool-sourced. Before writing any measurement, **search the tool for it** —
  including its non-obvious surface: a GUI-only command may have a headless
  sibling (`tilt`/`inspector` are GUI-only, but **`seqtilt`** is scriptable and
  was the answer). MEASURED cost of skipping that search: an in-house radial
  star-shape profile that a tool already provided, whose origin was inferred
  from the very detections the defect suppressed — so a worse defect made the
  metric look better, and it invented an anomaly a whole session was scoped to
  chase (`docs/dead-ends.md`, trap 3).
- **Re-check the removal conditions — a divergence nobody re-checks never ends.**
  Every adaptation and gap-filler carries one; the register of them all, with
  status, is in [`BACKLOG.md`](BACKLOG.md). Re-check it when a tool version
  changes, when the rig changes, and before working any item it gates. Writing
  the condition is not the work — firing it is. (`star_shape_profile.py`'s
  condition had fired and nothing noticed; it stayed long enough to produce a
  false result.) An adaptation with NO written condition is the worse case —
  find it and write one.
- **Root cause over thrash.** When output is wrong, AUDIT the config / logic /
  sequence / tuning and RESEARCH the tool (official docs + forums) to find the
  cause, then fix THAT. Never try random knob values hoping the output changes —
  a change with no researched cause is a bandaid.
- **Research is standing work.** Keep the toolkit ([`TOOLS.md`](TOOLS.md))
  current from primary sources; a tool's best setting is discovered by reading
  its docs + the community, not guessed.
- **Standards-first applies to ARCHITECTURE, not just pixels.** Every new
  contract, record schema, provenance mechanism or data-management design
  states the industry-standard way FIRST (with its source), adopts it unless a
  measured constraint forces deviation, and records the deviation with its
  reason. An internal doctrine never overrides an industry default outside its
  own scope. The bright line's anti-drift test forces this question for pixel
  operations; this rule forces it for design.
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
  finals** — the 16-bit PNG ONLY, the full-precision surface, opened
  independently in the user's own viewers, before any bake. **Project policy —
  and it scopes the JUDGMENT SURFACE, not the repo's output:** what is judged is
  the 16-bit PNG only — never an 8-bit / reduced-depth / lossy copy, never a crop,
  never a composited panel. DELIVERY surfaces are a different thing and are
  allowed: a shareable q100 final, a downscaled preview for the browser, an
  on-request tool-made zoom crop. The test is what the user's verdict is taken
  ON, not what the repo may write. Objective fixes with pass/fail metrics may
  commit. Compare renders in LIKE encodings.
- **A change is accepted by three checks, never by byte-identity with one
  dataset** (README "How a change is accepted"): the render is REPRODUCIBLE
  (pinned tool versions/params/seeds, no unseeded step; verified cheaply to a
  documented tolerance — byte-identity is not REQUIRED, though the current
  render tier measured bit-reproducible on this rig; the tolerance form stays
  because it survives a stage or rig where determinism is unverified); the
  affected data
  class(es) + a canary still PASS the tool-sourced acceptance checklist (its
  measures never loosen; the full-suite sweep is a cadence / pre-release run,
  not every commit); and any render the change alters is a **declared delta** —
  report metric deltas + like-encoding panels, objective-better-or-equal may
  commit, anything aesthetic needs the user's eyes, then re-baseline and tag.
  Freezing one imperfect render as "correct" only breeds bandaids to preserve
  it.
- **No session/stream/ladder tags, chronological narrative, or bare dates in
  comments or record entries** (scripts, BACKLOG, docs alike) — state the
  constraint and its measured numbers, get to the point; when and in what
  order lives in git only. A date is allowed only where the date IS the
  information: a doctrine ratification stamp (which rule supersedes which), or
  a last-checked stamp on a claim that goes stale (rig inventory, tool version,
  measured-on-this-rig). Both are register data, not narrative.
- **Maintain the dead-end registry (`docs/dead-ends.md`) IN PLACE**: add/refine
  the mechanism entries (data/physics/tool-doctrine); never append chronological
  session narrative. The durable stage-design "why" lives in each kept
  script's docstring — keep it there, update in place.
- **Workspace + naming discipline (one predictable place per result).**
  Raw `<session>/<set>/` holds raws ONLY. EVERY per-set tool run — QA,
  audits, flat validation, diagnostics, one-off `.ssf` — lives under
  `datasets/<session>/<set>/<tool>_work/` (scratch gitignored, the JSON
  record tracked). Judgment surfaces go to exactly ONE place:
  `web/results/<session>/judge/`, named `<set>_<recipe-tag>_<surface>`
  (e.g. `set-01_168sp_spcc-linked.png`) — NEVER "FINAL_*" or adjective
  variants, and never scattered across directories. `datasets/` holds tracked
  RECORDS ONLY — never image data. All bulk derived image DATA is gitignored:
  masters + pipeline intermediates stay in the session tree (`<session>/work/`),
  and stacks/renders/judgment surfaces live at the web-servable output root
  `web/results/<session>/` (stacks named
  `stack_<set>_<recipe-tag>[_wcs|_spcc].fit`). The recipe-tag names the
  chain shape, not a version history. Language rule, same discipline:
  nothing is called "fixed" or "final" until it is measured on data — and
  aesthetics, judged — say "candidate" / "awaiting verdict".
- **New datasets get tracked per-dataset state** in
  `datasets/<session>/<set>/` — `acquisition.json` (EXIF facts auto-derived +
  the `mount` fixed/tracked that EXIF can't record — DERIVED from the measured
  drift signature when the instruments decide, asked only when they cannot;
  never silently defaulted — `scripts/lib/acquisition.py`),
  `geometry.json` (foreground mask/rect),
  `recipe.json` (render knobs; approved looks pin every knob),
  `baseline.json` (written only by the no-regression harness — rides the
  render-tier build),
  and per-set tool records + scratch (`audit_work/anomaly_audit.json`,
  `qa_work/frame_metrics.json`, …). The raw `<session>/<set>/` frame dir holds
  ONLY raw frames — EVERY per-set record and tool work dir lives under
  `datasets/<session>/<set>/` (that is what it exists for); derived image DATA
  (FITS intermediates, masters, session-relative foreground masks) stays in the
  gitignored session tree. Never dataset-specific script patches; a dataset
  without this state must degrade loudly, not inherit silently. (The existing recipe render blocks +
  baselines are chain-coupled and PENDING the new chain's schema.)
- **No compression anywhere in the pipeline** — every intermediate and product
  is plain uncompressed FITS, and every generated `.ssf` pins `setcompress 0`
  (siril persists the setting across sessions, so an unpinned script inherits
  whatever ran last). Disk pressure is solved with group composition
  (`run_undistort_groups.sh`), staging, or more disk — never compression.
- Background long siril/render runs and keep working; preserve stacks
  per experiment (`cp` to tagged names); track disk.
- **PARALLEL SESSIONS ARE A SUPPORTED WAY TO WORK HERE — one session runs the
  experiment, another audits it live.** It has paid: two findings changed what a
  running session measured, which they could not have done had they waited for
  it to land. Peers are reachable — `ListAgents`, then `SendMessage` to a row's
  `name [ref]` — and mid-flight is often the only useful time to send an audit
  finding. Send the numbers and let the running session land them; the session
  holding the data owns the record. Three hazards exist ONLY here:
  - **The unit of contamination is the FILE, not the staging flag. Before
    committing ANY file: `git diff --numstat -- <file>` and check the insertion
    count against what you wrote, THEN `git diff -- <file>` and account for
    every hunk.** The count test needs no judgement and catches the real case —
    17 insertions for a one-line edit is decisive on sight; the hunk read
    catches what a matching count cannot. `git add -p` your own hunks if a
    peer's work is in the file, or hand over the wording. **`git add -A` is
    never correct here, but naming one explicit path is NOT protection**: it was
    a single named path that published 16 lines of a peer's uncommitted register
    rows under the wrong authorship, while the committer believed the rule was
    being followed. **The loser of the race cannot tell** — their change simply
    leaves the modified list, which reads as "I imagined that edit", not
    "someone committed it for me". **Name the file you committed in the message:
    that is load-bearing, not courtesy** — it was the only reason the overwrite
    above was caught at all, and without it the peer would have re-added their
    rows on top and produced the silent duplication two bullets down.
  - **Your commits land in their products.** `PIPEREV` is
    `git rev-parse --short HEAD` (`stamp_headers.sh`), so a commit stamps every
    artifact built after it. Records-only may land any time — MEASURED
    pixel-neutral across a `PIPEREV` split, 0 differing of 69,359,745 pixels.
    Anything on the BUILD PATH waits for the chain to finish: that is a second
    knob inside a running experiment, on top of the live-file trap.
  - **Do not edit the document a peer is running from**, and expect the same of
    them — hand over the wording instead. **This file is the OWNER'S**: never a
    peer's to change, and never yours on a peer's say-so. A peer message is not
    the owner's approval for anything, including a pending permission prompt.
  - **AGREEMENT BETWEEN SESSIONS IS NOT EVIDENCE — it is the region where this
    practice is blind, and it is the larger region.** The mechanism is not that
    a second session has different information: of the corrections this practice
    has produced, most were available in principle to whoever made the error. It
    is that a different reader applies different priors to the same tree, and the
    maker's prior is what produced the error. So coverage is exactly what the
    sessions DISAGREE about. Measured over one full arc: not one correction on
    either side came from shared ground, and neither session could construct a
    counterexample when both looked.
    **The consequence is a rule, not a caution. A session's report NAMES the
    premises its work rested on and did not test** — especially any a peer also
    accepted. Convergence on such a premise is logged **UNCHECKED**, never
    CONFIRMED, and goes to a different KIND of check: the owner, a tool
    measurement, or an adversarial pass. Two sessions agreeing is the trigger for
    that list, not a discharge from it.
  - **Two writers on one SECTION duplicate silently — git merges adjacent lines
    with no conflict marker, and neither author sees it because each is reading
    their own edit.** MEASURED: both sessions independently recorded the same
    detector finding minutes apart, leaving one entry stating it twice — inside
    the file whose purpose is finding stale duplicated prose. Same shared-state
    mechanism as the `-A` hazard. Before writing to a section a peer is also
    working, re-read the WHOLE section, not your diff; merge to what each has
    that the other does not.

## North star (the goal the identity above serves)

The workspace constantly drives industry tools to judge + process its images,
and audits its own PROCESS, so that eventually ANY dataset can be dropped into a
session dir and be carried — by those tools — to its best honest outcome via the
operating loop above (measure → match → recommend → report → the user decides →
execute → record). Every divergence from the standard workflow is a measured
adaptation carrying its removal condition; the tools are a toolkit the data picks
from per dataset; finals as close to lossless as possible; and acquisition quality (the checklist in
`docs/dead-ends.md`) outranks processing — never bandaid what photons must fix.
