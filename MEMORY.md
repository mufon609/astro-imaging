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
- "the entire point of astrophotography is to take pictures on different
  nights, under different conditions and to be able to stack them
  altogether... we cannot overlook basic functionality like stacking from
  night to night" — multi-night accumulation is the CORE purpose; the
  lens-not-telescope divergences never lower that bar. Evaluate every
  calibration/model/route change against the COMBINE unit, not just per-set
  products (measured twice: per-set models smeared the cross-set unions;
  a shared family model fails across nights at 4.07 px corner state
  difference).
- "THE POINT OF THE PROJECT IS TO BE ABLE TO DO SYNTHETIC FLATS. SO STOP
  ASKING FOR REAL FLATS." — the repo has never had real flats and that is the
  mission, not a gap. A defect traced to flat-residual mechanics gets its fix
  INSIDE the flatless route (better sky-flat construction, geometry/route
  policy, a correcting tool) — recommending real flats abandons the project's
  core problem and can never explain a NEW defect, since the flats route is
  the constant across every product, passing and failing alike.
- "the goal needs to be focused on trying to mimic industry standards. the
  foundation of the project is to avoid inhouse code. why would we ignore
  such a basic option if it's the solution to our issue and an industry
  standard" — standards-first applies to ARCHITECTURE, not just pixel
  operations: every contract/schema/provenance design states the
  industry-standard way first (with source) and deviates only on a measured
  constraint, recorded. Binding rule in CLAUDE.md; measured cost was the
  combine contract inverting FITS self-description (git in the combine path).
- "my eyes can miss things so if i approved something that is clearly wrong
  thats fine just let me know why you think that... some things may be hidden
  until a later phase so i could have missed it then and caught it now" — an
  approval records what was visible AT APPROVAL TIME, never a constraint
  against fixing what is measured later. When evidence shows an approved
  artifact carries an issue, or a fix requires changing one: state it plainly
  with the evidence and proceed on the fix's merits — never rank a fix down
  or design around an accepted product to avoid touching it. The owner is
  told why, decides, and re-approves the new artifact.
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

## The target is DENSITY, not line count (user-ratified 2026-08-16)

What the repo is measured on is whether its lines are load-bearing, not how many
there are. Integrating a lesson properly is worth the lines it costs, and a long
document that earns its length is not a defect.

The failure state being guarded against is a cluttered, ad-hoc repo that is hard
to understand — not a large one. So growth is a PROMPT to ask what the lines
bought, never a budget to stay under, and a line-count delta is not by itself
evidence of anything.

This supersedes any framing that treats net growth as a metric to minimise. The
standing practice that survives it: a landing that adds substantially states what
it bought. That is a statement of value, not an apology for size.

## Reference-driven quality

When a dataset ships a reference finish, that is the bar: reproduce the
maker's actual process with THEIR tool on our data first, learn the mechanism
ours lacks, then mature our pipeline; separate reproducible process from the
maker's manual artistry; compare at like scale/orientation (verify parity
numerically). Study the reference and its published recipe BEFORE tuning.

## The data is a given — fixes live in the CHAIN (user-ratified 2026-08-10)

NEVER recommend an acquisition or equipment change as the route to a defect —
stopping the lens down, a faster/better lens, a tracker, real flats. This
project exists to carry whatever the data IS to its best honest outcome **in
code**, driven by the official tools. The owner's words: *"do not ask for
external changes — figure it out in code, that's why I'm building this project
in the first place"*, and *"people shoot with much faster lenses all the time
without issue"*.

This is the same rule as "synthetic flats are the point, never recommend real
flats" — one shape, one reason. Generalise from it.

An acquisition ask is also usually UNMEASURED: the f/5.6 recommendation that
triggered this ratification compared no apertures on this data and was asserted
from general optics.

The north star's *"acquisition quality outranks processing"* governs what must
not be BANDAIDED — never process away photons that were never collected. It is
not a licence to hand the defect back to the operator.

**Corollary, and it is where the discipline bites:** a stage that addresses a
defect goes where the defect is WELL-DEFINED, not where it is convenient to
bolt on. A pass over a finished product is a bandaid by construction. The
worked example: the star-shape defect is fixed in SENSOR coordinates and the
sky drifts ~1000 px across the sensor, so after registration each output
position holds a blend of many sensor-position PSFs and there is no PSF left to
correct — any PSF stage therefore belongs per frame, in sensor space, after
debayer and before the undistort warp and register.
