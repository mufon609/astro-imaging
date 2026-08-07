# UI investigation report — per-set pipeline position + zero-state

Deliverable of the read-only investigation ordered by
[`ui-position-and-zero-state-brief.md`](ui-position-and-zero-state-brief.md).
Everything below was re-verified against the code and, where marked
**measured**, by execution: `web/serve.py` was run and its APIs curled for
july31 (built), july23/july14 (staged raws only), and colonnello-m20
(records only); `readiness_report.py --no-write` was run on built and fresh
sets (record mtime confirmed unchanged); `run_set_chain.sh --plan` and
`run_session_chain.sh --plan` were run on built and fresh sets. Nothing was
built and nothing outside this file was edited. Statements without a
"measured" tag are code readings — hypotheses confirmed only to the strength
of a reading.

---

## 1. Current-state map, re-verified

What actually renders where, from which endpoint and record:

| surface | component (grep anchor) | source | state |
|---|---|---|---|
| per-stage chips + next action | `stage_status` (serve.py) → `nextActionBlock` (index.html) | products/records on disk via `session_model`, overlaid by this server's job table | SESSION-scoped: sets blur into "missing for: …" lists |
| readiness rail | `readinessRow` (index.html) | `GET /api/readiness/<s>/<set>` → subprocess `readiness_report.py --json-only --no-write` | per-set FITNESS, not position; full rail on Overview + set page, **overall chip only** on Sets rows (`rrov_` fill) |
| proto-stepper 1 | `lifecycle` (index.html) | session model per set | 4 phases, rendered only at the top of the set page's Frames tab |
| proto-stepper 2 — **omitted from the brief** | `CHAIN_STEPS` / `chainStepState` / `renderStrips` (index.html) | session model + `/api/paths` masters + `/api/jobs` | 7 steps (mount QA cull flats stack SPCC judge) per set, ●/○ table on the Run page, 20 s poll while a job runs |
| job list / log | `refreshJobs`, `watchJob`, `EXIT_MEANING` (index.html) | `/api/jobs*`, logs under `sessions/.webjobs/` | one job at a time rig-wide; chain prints `[chain <set>] <stage>` lines; groups builder prints `=== group g/K ===` lines |
| chain | `run_set_chain.sh`, `run_session_chain.sh` | — | measure phase (acquisition/fingerprint → frame QA → audit → auto-cull → optics) → readiness report (evaluator exit 3 → chain exit 7) → ONE approval → masters → stack → finish → `baseline_guard` (exit 8) |

**Corrections to the brief, called out:**

1. **`nextActionBlock()` does NOT return null on a fresh session, and the
   zero-state Overview is not empty.** Measured on july23 and july14 (raws
   only): `/api/status` returns todos with specific whys, and the Overview
   renders "next · `frame_qa` — missing for: set-01, …" with a run link.
   The null branch fires only when the status fetch itself fails. The real
   zero-state gaps are different in character: (a) "next" names the MANUAL
   stage (`frame_qa` ranks first in `STAGE_ORDER`) instead of the one-click
   chain that would run it; (b) nothing explains staging or what the one
   click does; (c) the session header renders `— · — @ — mm · — s · ISO —`
   (no acquisition record yet); (d) the readiness rail is a wall of RED
   (finding 2).
2. **`lifecycle()` is not the only proto-stepper.** The Run page's
   `CHAIN_STEPS` strip is a second, with DIFFERENT evidence rules — the
   "second convention" risk the brief warns about is already live, twice
   over. Where they disagree, the strip is the more correct one: its cull
   step reads `recipe present OR zero flags`, which is the semantics
   `lifecycle()`'s "decided" phase lacks.
3. **`lifecycle()`'s rules break on the validation corpus.** Measured on
   july31: sets 02–04 are built, judged, and baseline-seeded, yet read
   "decided: no recipe — generic defaults" and "confirmed: —" forever —
   a zero-flag set never gets a recipe written (the chain's auto-cull writes
   one only when flags exist), and `kept` is then null so `confirm` is
   `unknown`. Code-read, no corpus case yet: `fullSurface` accepts only
   `recipe_tag ∈ {full, ownflat}`, so a standard-route product
   `stack_<set>.fit` (tag none) would leave "stacked/confirmed" pending
   forever on the tracked route.
4. **The Sets page renders only the overall readiness chip**, not a
   per-criterion rail (the brief says the sets page renders "a per-set
   readiness rail" — the full rail is Overview + set page).
5. **The readiness rail is unscoped where `stage_status` is scoped.**
   Measured: `datasets/july31/qa_work_compose/` (a session-level records
   dir) is classified `lights` by `set_kind`'s fallback, so the flagship
   built session's Overview rail carries a RED row for it; july23's
   3-frame `set-00` gets a RED chip on the Sets page while `_scope`
   correctly excludes it from status; a records-only session
   (colonnello-m20) 500s the evaluator (`shutil.disk_usage` on the absent
   session dir) and renders "evaluator unavailable".
6. **A stale job record can outvote the disk.** Measured: july14's
   `previews` chip reads "done — a recorded run of this session completed
   it" from `sessions/.webjobs/j20260723-*-previews.json` (cmd
   `web/make_previews.sh july14`, rc 0) while no previews manifest exists —
   the session was reset to raws since. `stage_status`'s overlay
   (`state == todo and job done → done`) trusts a recorded job over the
   absence of its product. This is direct evidence for the mechanism choice
   in finding 1: products survive resets; job records are only trustworthy
   for `running`.
7. **A readiness-RED chain stop renders as a crash.** `run_set_chain.sh`
   exits 7 on RED (measured mapping: evaluator exit 3 → chain exit 7), but
   `EXIT_MEANING` in index.html has no rc-7 row for it, so the jobs table
   shows "failed (rc 7)" with the read-the-log hint instead of "stopped —
   readiness RED".

**Verified as the brief states:** click-gated execution and the fixed
registry (`_stage_registry`, `POST /api/run`, chain stages pass `--yes` on a
real click and `--plan` on preview); ONE evaluator behind CLI, chain, and
`/api/readiness` (`--no-write` measured leaving the record untouched);
record text renders through `textContent` (`h()`); the staged-only Sets row
and set-page header carry the derive-then-ask language, and CHIP_HELP's
"not yet measured" entry matches; `sessions_inventory` unions results +
datasets + staging so fresh sessions are navigable (measured: july23 lists
`darks` as calibration and four staged light sets with raw counts, plus the
3-frame `set-00`).

**Adjacent staleness noticed while verifying (not this report's scope, one
line each):** BACKLOG `web-jobs-filter` appears already shipped
(`refreshJobs` filters on `SESSION` and never defaults to show-all);
`web/README.md` still describes `RENDER_RATIO_FLOOR_PCT`, which BACKLOG
`render-reproducibility` records as removed from serve.py;
`datasets/README.md` still opens with "Tracked today: none";
`RUN_JULY31_FROM_RAWS_PROMPT.md` shows as deleted in the working tree
(pre-existing — it was absent before this investigation's first command).

---

## 2. Finding 1 — per-set pipeline position

### Design options

**A. Extend `lifecycle()`** — fix its evidence rules, render it beyond the
Frames tab.
- For: smallest diff; the component exists.
- Against: it computes in the browser, so a third copy of evidence rules
  lives in JS beside `chainStepState`'s and the server's; its granularity
  (4 phases) cannot answer "where is the run NOW"; it still leaves the
  CHAIN_STEPS strip as a divergent sibling; every page computes its own
  answer from the model rather than reading one.

**B. Chain writes a machine-readable progress marker** (the brief's option
c), UI reads it for both ✓ and ▶.
- For: exact live stage, even for CLI-launched runs; no inference.
- Against: it is a SECOND state surface that can contradict the products —
  the july14 previews chip is the measured shape of exactly that failure
  (recorded state outliving disk truth). A marker's home would be gitignored
  scratch (`sessions/<session>/work/`), so it vanishes with the session tree
  while `datasets/` records survive — the opposite durability of the thing
  it describes. And it is not needed for the ✓s at all: the chain's own
  skip-if-exists tests already make products the position record.

**C. Server-computed position from products + records, mirroring the
chain's own skip checks; live ▶ derived from the jobs table.**
- For: one truth source ("the record is the truth"); the evidence tests are
  copied from `run_set_chain.sh`'s skip logic, so the stepper can never
  disagree with what a re-click would actually do; survives server restarts
  and session resets; no log parsing (`docs/dead-ends.md`: a log-message
  regex is not a measurement interface).
- Against: the ▶ is inferred, not reported — for a chain job it is the
  first incomplete step (correct by construction: skip-if-exists means the
  chain runs exactly that next), but a CLI-launched run shows advancing ✓s
  with no ▶ (stated in the edge table as the honest degrade).

### Recommendation: C, one component, server-side

**Mechanism, named:**

- **Data source:** a `position` block computed in `serve.py` per light set,
  inside `session_model` (new helper, e.g. `set_position(session, set,
  surfaces, jobs)`), so it ships in `GET /api/session/<name>` — the model
  every page already fetches; no new endpoint, no extra round-trips. Each
  step's test is the chain's own skip test (table in §3). The live overlay:
  `start_job` additionally persists the validated `args` into the job
  record (it already persists `cmd`, `stage`, `session`); a running
  `chain_set` job whose `args.set` matches — or a running `chain_session`
  job in this session — marks this set's first incomplete step `running`
  (for `chain_session`, only on the first set in name order with an
  incomplete chain, which is the set the chain is actually on); a running
  MANUAL stage job marks the step that stage maps to. Job records are never
  used for `done` — products only (the measured july14 lesson).
- **Component:** one `positionRow(p)` renderer in index.html beside
  `readinessRow` — same pattern, chips/dots with `title` evidence per step
  (`textContent` discipline). It REPLACES both proto-steppers: `lifecycle()`
  in the Frames tab and the `CHAIN_STEPS` strip on the Run page (retirement
  is user decision D4).
- **Render locations** (D2): Sets table — a compact position column beside
  the readiness chip; set page header — the full stepper with evidence
  tooltips, above the tabs (not buried in one); Overview — one row per set
  under the readiness rail, so fitness and position read side by side.
- **Groups sub-progress** without inventing a third copy of the group-size
  derivation (`readiness_report._derived_group` is already a keep-in-sync
  second copy of `run_undistort_groups.sh`'s): the stack step's evidence
  while building reads `work/groups_<set>/sub_*.fit` count plus the
  `GRPSIZE` header the builder stamps — "3 sub-stacks on disk (group size
  100)" — count and stamp only, no re-derived K.
- **Scoping:** position (and the readiness rail, same fix) iterates the
  sets `stage_status` counts — `_unprocessable` filtered, kinds `lights`
  only — which removes the measured `qa_work_compose` RED row and the
  `set-00` chip in the same change.

---

## 3. Step-to-evidence table

Steps mirror `run_set_chain.sh`'s own sequence and skip tests (the brief's
instruction: the chain is the authoritative product-to-stage mapping).
Records under `datasets/<session>/<set>/`, products under
`web/results/<session>/`, masters under `sessions/<session>/work/masters/`.

| step | walkthrough § | proves it done (the chain's own test) | chain anchor (grep) |
|---|---|---|---|
| measured | §2.1–2.2 | `acquisition.json` present AND `qa_work/frame_metrics.json` present; display value `registered/total` | `run_frame_qa.sh` call under `say "frame QA"` |
| audited | §2.3 | `audit_work/anomaly_audit.json` present; display objects + longest dwell (the dwell-floor producer) | `obstruction audit exists — skipping` |
| routed | §3 | `acquisition.json` `mount` (+`mount_source`) and `exif.fov_deg` derive a route (`tracked→standard`; `fixed+fov≥10→undistort-groups`); display `fingerprint.label` + `mount (source)` | `route (re-derived)` |
| decided (cull) | §2.2 policy | `recipe.json` `stack` block present, OR frame QA ran with zero flags (measurement decided it — nothing to cull) | `auto-cull (standing policy)` |
| masters | §4 | undistort routes: `dark_master.fit` AND `skyflat_<set>.fit` or `skyflat_<set>_desky.fit` (both spellings — `_has_flat` in serve.py already does this; the CHAIN_STEPS strip misses `_desky`); standard route: n/a (builder-internal); real-flats-on-undistort: the exit-6 stop, shown as blocked not pending | `per-set sky flat` / `STOP: real flats staged` |
| stacked | §5–6 | THE ROUTE'S product name exactly: `stack_<set>.fit` (standard, forced single) or `stack_<set>_full.fit` (groups) — never a tag whitelist (`fullSurface`'s `{full, ownflat}` is the drift to avoid); while building, `work/groups_<set>/sub_*.fit` count + `GRPSIZE` | `stack exists -> skip build` |
| solved / SPCC | §7 | `stack_<name>_wcs.fit`; `stack_<name>_spcc.fit` (+`work/spcc_<set>*.json`); mono set: SPCC n/a | `finish (solve -> SPCC -> judge surface)` |
| judged | §8 | `judge/<name>_spcc-linked.png` OR `judge/<name>_lum-autostretch.png` — the EXACT names; a recipe-tagged variant does not count (the chain deliberately re-finishes in that case) | `judge_surface()` |
| baselined | §9 | `baseline.json` present (written only by `baseline_guard.py --seed` after a human accepted a product); `readiness.json` = the last evaluated report | `no-regression:` |

Display language per the contract: steps say what the record shows
("`frame_metrics.json` on disk, 500/507 registered"), never "final/fixed";
the readiness rail remains the separate fitness surface beside this — a set
can be GREEN-ready and one step in, or fully positioned with a YELLOW rail.

---

## 4. Edge-case table

| case | designed behavior | basis |
|---|---|---|
| standard route (tracked) | optics/masters/sky-flat steps n/a (route-aware, like the readiness `optics` row); stack evidence is `stack_<set>.fit` — fixes the `fullSurface` whitelist miss | chain builds no masters on that route; `run_pipeline.sh` resolves internally |
| forced `--route=single` | stack evidence `stack_<set>.fit`; route step shows OPERATOR-FORCED (readiness already words it) | `force_route()` |
| composed / virtual set (`m20_rgb`) | not the per-set stepper; either its own short position (member stacks ✓ → `stack_<target>_comp.fit` → wcs/spcc → judge) or excluded with the `compose_channels` chip — user decision D3 | `kind == composed`, `compose_channels` logic in `stage_status` |
| calibration dirs (incl. singular spellings) and `reference/` | never get a stepper or a rail chip | `set_kind`, CALIBRATION_DIRS; dead-ends "calibration dirs are plural" |
| records-only dir under `datasets/` (`qa_work_compose`) | excluded by the `_unprocessable` scope (today it renders a RED rail row on the built flagship session — measured) | `_unprocessable`, `_scope` |
| set under 8 frames (`set-00`) | excluded, listed with its reason exactly as `_scope.skipped` does (today it gets a RED readiness chip — measured) | scripts' own refusals quoted in serve.py |
| resumed run | steps read done from products — identical to the chain's skip decisions, so the stepper predicts the re-click exactly (measured: built-set `--plan` prints skip lines for stack + judge) | skip-if-exists |
| session chain live set | while a `chain_session` job runs, the live set is the first (name order) with an incomplete chain; its first incomplete step is ▶ — the chain's own iteration order, and `run_session_chain` skips <8-frame sets exactly as the scope does (measured: july23 plan enumerated 4 of 5) | `run_session_chain.sh` set enumeration |
| re-measured set, stale downstream products | the kept-count case is already modeled: `confirm: differs` → MISMATCH on full-depth tags; broader staleness (new measurement, old stack) is NOT modeled today — option: flag downstream steps `stale` when `frame_metrics.json`/`recipe.json` are newer than the product (mtime is weak evidence; D5) | `confirmChip`, `FULL_DEPTH_TAGS` |
| a terminal (not the web) is building | no web job → no ▶; ✓s advance as products land on refresh; the component's help states it ("live state comes from web jobs; CLI runs show as advancing evidence") — honest degrade, no pid-scanning | jobs table is the only live source |
| adopted / stale job records | never colour a position step `done` from a job record — products only; `running` only pid-checked (`_pid_alive`) | measured: july14 `previews done` vs no manifest on disk |
| fresh set (raws only) | all steps pending — this state IS the zero-state card's trigger (finding 2); the stepper renders ○○○… with "the one click runs these" | measured july23 |
| records-only session (raws freed) | position ✓s from records/products remain true; runnable-ness needs staging — card variant "records on file; raws not staged (`sessions/<s>/<set>` absent) — re-stage to run"; today nothing says this and status shows plain todos (measured, colonnello-m20); also stop the evaluator 500 (guard `disk_usage` on a missing session dir) | `sessions_inventory` union vs staging tree |
| mono set | SPCC step n/a; judged evidence is `_lum-autostretch.png` | `judge_surface()`, README (mono skips SPCC) |

---

## 5. Finding 2 — zero-state pending-vs-RED, and the start-here card

### The structural fact the options turn on (measured)

On a fresh set the rail reads overall RED with five RED rows — mount,
route, frame_qa, obstruction_audit, optics — every one carrying a detail
that already says "the chain's measure phase runs/derives this". Those five
RED branches are **unreachable in the chain's own invocation**: the chain
runs the measure steps (or exits 2/4/5) BEFORE it calls the evaluator, so
post-measure those records exist by construction. They appear only on
pre-run surfaces (web rail, ad-hoc CLI) — where RED's ratified meaning,
"the only thing that stops a run", is false: the run click is legitimate,
and the run itself produces exactly these records. The current pre-run rail
therefore contradicts the colour contract on staged-only sets; this is a
correctness question, not a cosmetic one.

### Options for where pending-vs-RED lives

**A. Fourth evaluator status, `PENDING`, computed from the records** —
`evaluate()` marks a measure-phase criterion PENDING when its producing
record is absent and nothing measured stands against it: mount PENDING when
no declaration AND no fingerprint measurement exists (a fingerprint that
measured and could not decide stays RED — that genuinely stops, exit 4);
route PENDING while mount is; frame_qa/obstruction_audit PENDING when their
record is absent; optics PENDING while the route is unknown or the
preflight record absent. `overall` = PENDING when any row is pending and no
row is RED; CLI exit stays 0 (only RED exits 3). The chain's post-measure
invocation cannot see PENDING structurally; `--post-measure` on the chain's
call (absence → RED) is available as belt-and-braces if wanted.
- For: one evaluator, one vocabulary, all three surfaces agree (the ad-hoc
  CLI on a fresh set stops printing misleading RED too); the state is
  derived from the records, not asserted by the caller.
- Against: amends the user-stated three-colour contract — needs
  ratification (D1) — and every consumer of the status vocabulary must
  learn the fourth value (`rrClass`'s else-branch currently paints unknown
  statuses as RED, so the UI change must land with the evaluator change).

**B. An `--pre-run` flag the web passes** — same rendering, but the state
depends on the caller's assertion rather than the records; the unflagged
CLI still prints RED for a fresh set, so one of the three surfaces keeps
the misleading reading; two callers can disagree with reality.

**C. Web-only remap** (UI renders not-run REDs as neutral when the set is
`staged_only`) — forks semantics away from the one-evaluator principle, the
CLI and the tracked `readiness.json` never carry the state the page shows,
and the remap key (`staged_only`) is a different fact than "measure phase
has not run" (a set with QA but no audit is neither).

**D. Overload YELLOW** — rejected: YELLOW's ratified meaning is "met, but
look"; not-yet-measured is not met, so this muddies the contract exactly as
RED does today.

### Recommendation: A

**Mechanism, named:** `readiness_report.evaluate()` grows `PENDING` per the
rules above (status vocabulary `GREEN/YELLOW/RED/PENDING`, `_RANK` ordering
pending below green for `overall` selection with the any-pending/no-RED
rule); `rrClass` maps PENDING to the neutral chip; the rail chip text reads
"pending — the run measures this" (the evaluator's own detail strings
already say it). The chain call site adds `--post-measure` so absence after
the measure phase stays RED even if a future refactor breaks the structural
guarantee. Ratification of the fourth state is D1 — until given, nothing
changes.

### The zero-state card

**Content and placement:** an Overview card, rendered when any counted
light set has no `frame_metrics.json` (the same records the position block
reads — not `staged_only`, which misses a half-measured set). It shows:
what is staged, from the session model (`N light sets, M frames; darks
staged: yes/no` — measured available for july23: 4 sets, 401/400/401/399
frames, 213 darks); what the one click does, in the chain's own vocabulary
(measure → one readiness report → your approval is the click → build →
judge surface — the `_STAGE_DOCS.chain_session.detail` text already says
this and can render here); a **preview plan** action (`chain_session` with
`plan: true` — the existing `runChainDirect` pattern, executes nothing,
measured to print per-set plans); and a **Start** button that is the
existing gated `chain_session` stage, exactly as the Run page fires it
(dry-run disclosure then `--yes`). No new execution path, nothing on page
load.

**Partially fresh session:** the card stays but scopes itself — "set-05 is
staged and unmeasured; the session button measures it and skips the built
sets" (verified chain behavior: skip-if-exists per set, `run_session_chain`
resumes at the first incomplete set). The "where you left off" block
remains the primary surface once anything is measured; on a fully-fresh
session the card leads (D6).

**Sets-page staged row and set-page staged header:** verified already in
derive-then-ask language ("the set chain's measure phase derives the mount
from the data … declaring is the OVERRIDE"; CHIP_HELP "not yet measured"
matches). They need no wording change; they inherit the pending treatment
automatically through the shared rail once the evaluator carries PENDING.
The `not yet measured` warn chip on the row can stay — it is descriptive,
not a readiness colour.

**Rides along (same change, measured causes):** scope the rail exactly as
`stage_status` scopes (`_unprocessable` + kind), which removes the
`qa_work_compose` RED row and the `set-00` chip; guard the evaluator
against an absent session dir so a records-only session reads "not staged"
instead of "evaluator unavailable".

---

## 6. Scope fence — what this deliberately does NOT do

- **No new execution paths.** Start/preview buttons are the existing
  `chain_session`/`chain_set` registry stages; execution stays click-gated
  per run; no watcher, nothing on page load.
- **No second readiness opinion.** PENDING comes from the one evaluator or
  not at all; the UI never remaps colours on its own.
- **No log parsing for state, and no progress-marker file.** Position ✓s
  are products/records; ▶ is jobs-table-derived. Revisit the marker only if
  a builder stage grows long opaque internal phases whose products land
  only at the end AND intra-stage position is actually needed.
- **No registry changes.** No new stage; `_stage_registry` untouched except
  none — the job-record `args` addition is serve-internal.
- **Stops at the chain's own end.** The stepper ends at judged → baselined
  (§8–§9); it does not model the render tier or any aesthetic state beyond
  the existing `render_tier` chip — aesthetics stay the user's eyes on the
  full-frame lossless finals.
- **Moves and renames nothing.** Records render read-only through
  `textContent`; no artifact is touched; language stays "what the record
  shows" (no "final/fixed").
- **Flagged, not folded in** (each a one-line fix belonging to its own
  change): the `EXIT_MEANING` rc-7 row for `run_set_chain.sh`; the
  evaluator's `disk_usage` crash on an absent session dir; the stale
  `web/README.md` floor paragraph; BACKLOG `web-jobs-filter` closure check.

---

## 7. Decisions only you can make (options, with the recommendation first)

**D1 — pending semantics (amends the ratified colour contract).**
(a) *Recommended:* fourth evaluator status PENDING, records-derived, chain
passes `--post-measure`; (b) `--pre-run` flag, web-only; (c) web-only
remap, evaluator untouched; (d) keep RED as-is and accept the contract
mismatch on pre-run rails.

**D2 — where the stepper renders.**
(a) *Recommended:* all three — compact column on Sets rows, full stepper on
the set page header, per-set rows on Overview beside the readiness rail;
(b) set page + Sets only; (c) set page only (position stays one click deep).

**D3 — composed/virtual targets.**
(a) *Recommended:* a short compose-specific position (members ✓ → composed
stack → wcs/spcc → judge); (b) excluded from steppers, `compose_channels`
chip only.

**D4 — the two existing proto-steppers.**
(a) *Recommended:* retire both (`lifecycle()` in the Frames tab, the
`CHAIN_STEPS` strip on the Run page) in favor of the one component — two
divergent evidence rules is the measured current defect; (b) keep the
Frames-tab strip as a set-local summary and retire only the Run-page strip.

**D5 — staleness signal for re-measured sets.**
(a) *Recommended:* content-based only (the existing `confirm`
kept-vs-header check; MISMATCH on full-depth tags), no mtime heuristics;
(b) add an mtime hint (records newer than product ⇒ "stale" mark), stated
as weak evidence; (c) none.

**D6 — zero-state card precedence.**
(a) *Recommended:* on a fully-fresh session the card leads and the
"where you left off" block is omitted (its "next · frame_qa" points at the
manual stage a first-timer should not start with); (b) card sits above the
next-action block, both render.
