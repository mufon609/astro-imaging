# UI investigation brief — per-set pipeline position + zero-state

**What this is.** A brief for a read-only investigation of the two dashboard
gaps named below. The deliverable is a REPORT, not an implementation:
`docs/ui-position-and-zero-state-report.md`, structure specified at the end.
The user will review it and decide the implementation. Verify every claim in
this brief against the code and records yourself — it was written by a session
that read the code, but the contract says a reading is a hypothesis until
checked.

**Context.** The dashboard (`web/serve.py` + `web/index.html`, 127.0.0.1-only)
drives the pipeline the repo documents in
`docs/pipeline-wide-field-untracked.md`. As of this brief: the chain takes ONE
approval at a readiness report (`scripts/qa/readiness_report.py` — one
evaluator feeding CLI, chain, and `GET /api/readiness/<session>/<set>`), the
web run buttons pass `--yes` (the click is the approval), and the session /
sets / set pages render a per-set readiness rail from that endpoint. A
new-user audit found the two remaining gaps below.

---

## Finding 1 — no per-set pipeline POSITION

The user's requirement: *"track/show the user exactly where the data is in
the pipeline."* What exists shows fitness and session-level state, not
per-set position:

- `stage_status()` in `serve.py` (`GET /api/status/<session>`) — per-STAGE
  done/running/todo/na chips, but SESSION-scoped: four sets blur into one
  row per stage ("missing for: set-02, set-03").
- The readiness rail (`/api/readiness`) — per-set, but it answers "is this
  set FIT to run", not "WHERE is this set in the run".
- `lifecycle(s)` in `index.html` — a four-phase strip (measured → decided →
  stacked → confirmed) rendered only inside the set page's Frames tab. This
  is a proto-stepper: audit it first; extending it may beat inventing a
  parallel component, or it may be the thing a real stepper replaces.
- `nextActionBlock()` in `index.html` — computes the session's next stage
  from `stage_status` in declared pipeline order (`STAGE_ORDER`).
- Jobs: one at a time rig-wide (`/api/jobs`, log tail in the Run page); the
  chain prints per-stage `[chain <set>] <stage>` lines into the job log.

What is missing: a per-set stepper — e.g. measure ✓ → route ✓ → masters ✓ →
stack ▶ → solve/SPCC · → judge · → baseline · — with the RUNNING stage live,
visible on Overview and Sets, not buried in a tab.

Every input exists per set. Records: `acquisition.json`, `fingerprint.json`,
`qa_work/frame_metrics.json`, `audit_work/anomaly_audit.json`, `recipe.json`,
`qa_work/lens_preflight.json`, `readiness.json`, `baseline.json`. Products:
masters under `sessions/<s>/work/masters/`, `stack_<set>_full.fit`,
`_wcs`/`_spcc` variants, `judge/<name>_spcc-linked.png` (the chain's own
skip-if-exists checks in `run_set_chain.sh` are the authoritative
product-to-stage mapping — mirror them, do not invent a second convention).

**Questions the report must answer:**
1. Extend `lifecycle()`, replace it, or add a distinct component — and where
   does it render (Overview? Sets rows? set page header?).
2. Where does POSITION truth come from? Options to weigh: (a) products +
   records on disk (matches "the record is the truth"; cannot show a live
   running stage on its own); (b) parsing the chain's job-log lines (live,
   but log-scraping is fragile); (c) the chain WRITING a machine-readable
   progress marker as it goes. For (c), weigh where such a marker lives
   against workspace discipline (`datasets/` = tracked records;
   `sessions/.webjobs/` = run scratch) — a transient run-state file is
   probably scratch, not a tracked record. Recommend one mechanism.
3. Step granularity: map proposed steps to the walkthrough doc's stages
   (§2–§9) and state, for each step, the exact record/product that proves
   it done.
4. Edge cases the design must state: the standard route (no optics/flat
   steps), composed/virtual sets, calibration dirs, a resumed run (products
   exist → steps read done), the session chain (which set is live), a
   re-measured set whose downstream products are now stale, and a set another
   terminal (not the web) is building.

## Finding 2 — zero-state reads as broken, not pending

A fresh session (raws only) IS navigable — `sessions_inventory()` unions the
results, records, and staging trees. But:

- Overview: `nextActionBlock()` returns null when no stages report, so the
  page reads empty; nothing says "start here."
- The readiness rail pre-run shows RED "not run" for frame QA / audit /
  mount — honest for the CHAIN (whose report runs after the measure phase,
  where not-run is genuinely wrong) but misleading on the web BEFORE any run:
  a first-timer reads "broken," and the truthful state is "pending — the run
  measures this."

What is missing: (a) a zero-state "start here" card — staging paths, what
the one click will do, and a Start button that is the existing gated
`chain_session` stage (full plan disclosure, `--yes` = the click); (b) a
neutral pending state for pre-measure rails.

**Questions the report must answer:**
1. Where does pending-vs-RED semantics live? Options: a fourth evaluator
   status (e.g. PENDING when the measure phase has not run at all — but the
   chain's post-measure usage must never see it), an evaluator flag
   (`--pre-run`?), or a web-only remap (UI renders not-run REDs as neutral
   when the set is staged_only — but that forks semantics away from the
   one-evaluator principle). Recommend one, with the colour contract in
   mind: RED is defined as "the only thing that stops a run."
2. The exact zero-state card content and placement, and what it shows for a
   session that is PARTIALLY fresh (some sets measured, one newly added).
3. Whether the Sets-page staged-only row and set-page staged-only header
   (both just rewritten to derive-then-ask language — verify) need the same
   pending treatment.

---

## Constraints that bind ANY design (verify each in the named source)

- **Execution is click-gated, always** (`web/README.md`, user-ratified): the
  site may execute only from an explicit per-run user action — never
  automatically, never on page load. A Start button is fine; a watcher that
  auto-runs is a contract amendment only the user can make.
- **Fixed stage registry** (`_stage_registry()` in `serve.py`): anything
  runnable is one of the pinned stages; no new execution paths.
- **One evaluator** (BACKLOG `readiness-report`, CLOSED): readiness colours
  come from `readiness_report.py` everywhere; do not compute a second
  opinion in the UI.
- **The record is the truth**: the UI renders records and products; it never
  invents state. Record text renders through `textContent` (see `h()` in
  `index.html`) — keep that discipline.
- **Language discipline** (CLAUDE.md): nothing is "final/fixed"; steps say
  what the record shows.
- **No chronological narrative in comments or record entries**; cite symbols
  and grep anchors, never line numbers.

## How to work

Read-only. Do not run builds; do not edit anything except writing your
report. You may: start `web/serve.py` and curl the APIs; run
`readiness_report.py <session> <set> --no-write`; run the chains with
`--plan` (executes nothing). `sessions/july31` is a fully-built validation
corpus; a scratch fresh-session fixture for zero-state observation is fine
under your scratchpad (not under the repo).

## The report (`docs/ui-position-and-zero-state-report.md`)

1. Current-state map, re-verified (what actually renders where, from which
   endpoint/record — corrections to THIS brief called out explicitly).
2. Per finding: 2–3 design options with trade-offs, then ONE recommendation
   with its mechanism named concretely (data source, component, endpoint).
3. The stepper's step-to-evidence table (step → record/product that proves it).
4. The edge-case table with the designed behavior for each.
5. Scope fence: what the recommendation deliberately does NOT do.
6. Open questions only the user can answer (priorities/aesthetics), stated
   as decisions with options — not as blockers buried in prose.
