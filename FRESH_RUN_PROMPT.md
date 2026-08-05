# Prompt for a fresh session — paste everything below this line

---

Run this repo's pipeline end to end on the **july31** session, starting from nothing
but the raw frames, and report back on how well the repo actually held up.

**READ FIRST, in this order** (the repo's own read-order, and it is binding):
`CLAUDE.md` → `docs/dead-ends.md` → `TOOLS.md` → `MEMORY.md` → `README.md` →
`BACKLOG.md` → `datasets/README.md` → `web/README.md`.

## The state you are starting from

`sessions/july31/` holds **raw frames only** — 347 darks and four light sets
(set-01 507, set-02 500, set-03 500, set-04 260 NEFs). There are no masters, no
records, no stacks, no judge surfaces, and no `datasets/july31/` at all. Every
prior artifact for this session was deliberately removed so the pipeline has to
derive everything itself.

**Every other session has been reset the same way.** `july14` and `july23` are also
raw-frames-only — no records, no masters, no stacks, no judge surfaces. There is
nothing in this repo to inherit a per-dataset answer from, by design. The only
per-dataset records left are `colonnello-m20`'s, which are a MONO / TRACKED /
per-filter set with no frames staged — useful to read as a contrast class, useless
as a source of answers for this one.

Archives of all three sessions exist outside the repo. You are not to look for
them or use them. If you catch yourself reaching for a remembered number instead
of measuring one, stop and measure.

## What to do

Follow the repo's operating loop: **measure → match → recommend → report → the
user decides → execute → record.** You are the gate-respecting operator, not an
autopilot: anything output-shaping stops for a human decision, and the docs tell
you which stops exist.

**The mount for july31 is `fixed` — an untracked tripod.** That is the operator's
declaration; take it as given and do not stop to ask. The chain will still want it
written into `acquisition.json`, so declare it and carry on.

Do NOT take it on faith, though: the fingerprint measures the mount independently
from trail-vs-roundness and a two-window drift solve. If the measurement
CONTRADICTS `fixed`, that is a real finding — stop and report it rather than
overriding the instrument with this instruction.

That gate is a known wart, and it is on the list to automate: the pipeline should
only ask a human when the answer is genuinely absent from the data, and here it
is not — the drift rate against sidereal settles it. Note in your report what it
would take to derive `mount` automatically and where that logic belongs.

One stop IS expected and is the contract working correctly, not a failure:

- **exit 7 — render tier proposal.** With no ratified `render` block the tier
  measures, writes `render_proposed`, prints it and stops. Read the proposed knobs
  and say whether you would accept them, with reasons.

Prioritise getting **one set completely through** — frame QA → masters → route →
stack → solve → SPCC → judge surface → render tier — so the whole path is proven,
then extend to the rest of the session. Background the long runs and keep working;
do not sit and wait on a stack.

## What to report back

1. **The exact process used to STACK.** Every stage in order, the actual command
   or tool call, and for each parameter: was it derived from THIS data, read from
   a record, or hardcoded? Name the file and line where each choice was made.
2. **The exact process used to STRETCH.** Same standard. The stretch is where a
   pipeline most easily hides an unjustified constant — say exactly where each
   number came from.
3. **Ambiguities.** Anywhere the docs or the code left you unsure which way to go,
   or where two readings were both defensible.
4. **Contradictions.** Anywhere a doc claims one thing and the code does another,
   or two docs disagree. Verify against the code before reporting — do not trust a
   doc because it is confident.
5. **Recommendations.** What you would change, ordered by what would prevent the
   worst failure.

## The standard this repo is trying to meet — judge it against this

The pipeline must **pinpoint exact facts in the data to make its choices, while
staying general enough to make those same choices for a completely different rig.**
Concretely: the same code has to do the right thing for these Nikon OSC raws from
an untracked tripod AND for a monochrome, tracked, long-exposure setup with real
flats and no lens distortion to correct.

So while you work, flag every place the pipeline:

- **assumed instead of measured** — a constant where a derivation belonged;
- **hardcoded something specific to one camera, sensor size, focal length, mount
  type, filter, or exposure class** — anything that would be wrong on the mono
  tracked rig;
- **could not proceed without a human** where the data actually contained the
  answer, or conversely **proceeded silently** where it should have stopped;
- **would behave differently, or break, if the data were mono / tracked / real-flat
  / a different sensor size** — say what would happen and why.

Be blunt. A finding that the repo made a bad choice is worth more than a clean run
report. Report killed hypotheses as plainly as wins, no "fixed/final/matched"
language, and state whether each claim is MEASURED (with numbers and the
instrument) or a HYPOTHESIS (with the test that would settle it).
