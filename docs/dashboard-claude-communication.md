# Dashboard ↔ Claude communication — RESOLUTION (BACKLOG item 14)

- **Question / scope** — what connects Claude to the dashboard-driven pipeline
  for troubleshooting and building, with routine runs staying zero-AI-token.
- **Resolution (user decision, 2026-07-22)** — **No integration. No new
  surface.** No workspace MCP server, no Agent SDK bridge, no new endpoints,
  no contract amendments. Claude Code's existing tools (read/grep/shell) on
  the repo tree ARE the communication architecture.

## The surface, as it already exists (measured 2026-07-22)

- `sessions/.webjobs/*.log` — per-job logs, summarized at source by the stage
  wrappers (measured 118 B – 18 KB, median ≈0.7 KB; first line is the exact
  command, outcome lines are greppable).
- `datasets/<session>/…/*.json` + `web/results/<session>/solve_*.json` +
  `previews/manifest.json` — typed compact records (0.5–6 KB each), the
  durable interface. `anomaly_audit.json` (~89 KB) is the one large record —
  pull fields, don't read it whole.
- Deep tool logs — `qa_work/frameqa/siril.log` (712 KB ≈ 178k tokens),
  `work/spcc_*.log` (~116 KB each), `work/groups_*_run.log` — **grep/tail
  only, never whole**: one raw read costs most of a session's context.
- `/api/*` (serve.py) — exists for the site; Claude may query it when the
  server happens to be up, but needs nothing from it.

## The one standing rule

New stages keep the pattern the existing wrappers already follow:
**summarize at source** — the wrapper filters tool output into the job log,
and each result lands as one compact JSON record. That is the whole
architecture. (A related site papercut — failed-job records carrying a
bounded log tail — is tracked as website finding F6, a UI convenience, not AI
integration.)

## Evaluated and REJECTED (recorded so it is not re-proposed)

A workspace MCP server (typed read-only status/record tools) and an Agent SDK
bridge (propose-in-browser with a UI approve gate) were evaluated against
current Claude Code docs and the measured numbers above. Both are mechanically
feasible; both were REJECTED by the user: each adds an API surface to build,
maintain, and ratify for marginal benefit over reading the files directly —
and the SDK bridge could additionally require API-key billing outside the Max
subscription. Do not re-propose either absent an explicit new ask.

## Status

RESOLVED — nothing to build; BACKLOG item 14 closes on this note.
