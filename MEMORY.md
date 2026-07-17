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
- **The user is the gate**: nothing output-shaping proceeds without their
  decision; aesthetics are judged only by their eyes.
- Scraps throwaway platforms rather than bandaiding them; keeps the
  intellectual capital (mechanisms, dead-ends), not the scaffolding.
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

## Reference-driven quality

When a dataset ships a reference finish, that is the bar: reproduce the
maker's actual process with THEIR tool on our data first, learn the mechanism
ours lacks, then mature our pipeline; separate reproducible process from the
maker's manual artistry; compare at like scale/orientation (verify parity
numerically). Study the reference and its published recipe BEFORE tuning.
