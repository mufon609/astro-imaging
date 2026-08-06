# MEMORY.md — collaboration context (transferable)

**Why this file exists.** Claude's auto-memory is machine-local and does not
transfer when the repo moves rigs. This file carries only the durable
**collaboration context** — who the user is, how they judge and work. All
technical and process knowledge lives in the operating docs, never here:

- Binding rules + environment → `CLAUDE.md`
- Dead-end registry + acquisition checklist → `docs/dead-ends.md`
- Tool audit → `TOOLS.md`; x86 build order → `docs/x86-empirical-test-plan.md`
- Process/review/acceptance contract → `README.md`
- Per-dataset state model → `datasets/README.md`
- Full history → git (`git log`; the pre-reset chain at the commit whose
  message begins `checkpoint:`)

## Who the user is & how they work

- Runs this as a professional-bar project: lean docs, current-state-only
  records, outcomes with numbers — never narratives.
- **Decisive and autonomy-favoring** within the rules — has said "stop
  asking"; prefers action once intent is clear, and extends corrections
  class-generally ("audit the rest of the pipeline for the same mistake").
- **The user is the gate for what the DATA CANNOT SETTLE** — not for every
  decision. Routing measured facts through the right tool is the pipeline's job
  and the point of the project; aesthetics are judged only by their eyes. Asking
  a human to confirm what the instruments already measured is the failure mode,
  not the discipline (`CLAUDE.md`, "Where the gate actually is").
- Scraps throwaway platforms rather than bandaiding them; keeps the
  intellectual capital (mechanisms, dead-ends), not the scaffolding.
- **Storage on the working rig is transient by design**: raws stage in for
  processing and are freed once a set's chain is complete (originals live
  off-rig and re-stage in minutes); final processed images stay in `web/results/`;
  superseded intermediates are cleared without ceremony ("clear whatever...
  no longer needed. keep the final processed images in results").
- **Transient is NOT constrained — space must never shape a processing choice.**
  "i do not want to restrict the processing due to space… i expect 500-600 G to be
  the min present at anytime. if there is less space than that, clutter must exist
  and be found and remove - just lmk." So report the clutter and ask; never pick
  the cheaper route to save disk. This has already cost once: the single-pass vs
  groups route was decided by free disk alone, which on a big disk always picks the
  option that cannot be built on later.
- **Re-running is cheap; being wrong is not.** "i don't mind having to rerun any
  part of the process. slow and steady is the way to build for this project."
  Prefer the correct rebuild over the clever reuse, and do not present a rebuild
  as a cost the user needs protecting from.
- Expects killed hypotheses reported as plainly as wins — no
  "fixed/final/matched/close" language, ever; nothing is called fixed before
  it is tested on data.

## How the user judges (the formative corrections, verbatim)

- "you need to get this right before saving a flawed recipe" — nothing judged
  by eye commits before the user confirms the visual result.
- "stop throwing stuff at the wall" — one parameter per experiment, bracket
  the control, hypothesis BEFORE the run.
- "i need full uncompressed images … i can't use this cropped compressed
  images and charts" — the judgment surface is whole-frame lossless files,
  opened independently in the user's own viewers, LIKE encodings.
- "looks worse … what kind of a joke 'test' did it pass?" — a gate-PASS never
  stands in for the look; inspect the full-frame impression at 1:1 and state
  defects in the notes instead of hedging with numbers.
- "the midst of learn-nothing, try-everything" — the named failure mode:
  guess-and-check knob-thrashing with victory language. Never repeat it.
- "you have been guessing with conviction and need to slow down and research
  further instead of continue to guess and shoot from the hip confidently" —
  the second named failure mode: MECHANISM ATTRIBUTION WITHOUT A
  DISCRIMINATING TEST. A story consistent with the evidence is not a finding;
  name the competing mechanisms, state the test that separates them, run it,
  and only then attribute. Every reported claim carries its status: MEASURED
  (with numbers) or HYPOTHESIS (with the test that would settle it). The
  user's field knowledge (e.g. "that's dew") outranks an untested inference.

## Scope clarification (user-ratified 2026-07-26)

- "to judge and examine an issue i do not care if you use official tools;
  whatever is easiest is fine - the issue to avoid is in house code to solve
  problems that official tools already solve" — DIAGNOSTIC measurement may
  use any tool (numpy/PIL direct reads fine); the bright line applies to the
  PIPELINE: never in-house code where an official tool provides the
  processing/analysis capability.

## Reference-driven quality

When a dataset ships a reference finish, that is the bar: reproduce the
maker's actual process with THEIR tool on our data first, learn the mechanism
ours lacks, then mature our pipeline; separate reproducible process from the
maker's manual artistry; compare at like scale/orientation (verify parity
numerically). Study the reference and its published recipe BEFORE tuning.
