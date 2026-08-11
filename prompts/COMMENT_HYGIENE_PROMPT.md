# Fresh-session prompt — comment hygiene: mine the history, build the sweep, audit the policy

**Do not take this document's word for anything** — verify every claim in the
repo. Read `CLAUDE.md` first (the binding rules carry the comment policy),
then the auto-memory's comments entry if present, then work the steps in
order. You do NOT perform a repo-wide comment sweep in this session — the
GENERIC PROMPT you produce is the tool that does, run by the owner whenever
wanted.

## The owner's comment standard (the bar for everything below)

Comments are **high-value, load-bearing, technical**: the constraint or
mechanism with its measured numbers, present tense, detailed but not
long-winded, free of anything that will age or go stale. Dates, session
narrative, and how-it-was-found stories live in git, never in comments — the
one exception is a doctrine ratification stamp, which orders which rule
supersedes which. The policies governing comments must read like the comments
they demand: well-defined and short.

---

## Step 1 — mine the git history for what actually gets deleted

Do not guess the categories; derive them. The repo's history is full of
deliberate comment and note removals (cleanup commits, doc retirements, the
numbered→slug BACKLOG migration, superseded-era purges). Extract them:

    git log -p --diff-filter=M -- '*.sh' '*.py' | grep -E '^-\s*#' ...
    git log -p -- '*.md'            (removed prose lines in docs/records)
    git log --oneline | grep -iE 'cleanup|retire|prune|narrative|stale'

Read enough real instances to CATEGORIZE what is constantly being removed —
with counts and 2–3 verbatim examples per category. Expect (but verify, and
keep only what the history supports) shapes like: date-stamped chronology;
session/stream/arc narrative; references to retired mechanisms that outlived
their revert; numbered-item references that rotted when the numbering
changed; mechanism prose that had already graduated into `docs/dead-ends.md`
and survived as a stale duplicate; victory/status language ("fixed",
"final") on unmeasured claims. Whatever the history actually shows is the
taxonomy — including categories this list does not anticipate.

Also record the OPPOSITE class: comments the history shows being kept or
strengthened (constraint + measured numbers on the line they govern), so the
sweep prompt can say what a GOOD comment is by the repo's own revealed
preference, not by taste.

## Step 2 — generate the generic sweep prompt (the deliverable)

Write `prompts/COMMENT_SWEEP_PROMPT.md`: a REUSABLE brief the owner can run
in any future session to find and remove/revise exactly the categories Step 1
established. It is a standing utility — mark it explicitly as NON-retiring,
unlike one-shot briefs. It must contain:

- the policy, stated in full in a few lines (so the sweep session needs no
  other context);
- per category: a detector (a grep/pattern where the category is mechanically
  findable; honest guidance where it needs judgment), 1–2 examples from Step
  1, and the revise-vs-remove rule;
- the safety rule, non-negotiable: a comment is removed only when its
  information is (a) false, (b) preserved in git/`docs/dead-ends.md`/the
  docstring it duplicates, or (c) pure chronology. A load-bearing constraint
  is REVISED to the shortest correct form, never dropped — when in doubt,
  keep and tighten;
- scope: scripts, docs, BACKLOG, record `why` strings — but never the
  ratification-stamp exception, never `docs/dead-ends.md` mechanism entries
  (those are records, pruned by their own registry rules only);
- an acceptance shape for each run: the diff cites its category per hunk, and
  a re-run of the detectors comes back clean or explains every survivor.

## Step 3 — audit the policy text itself

Find every place the comment policy is stated (at minimum the `CLAUDE.md`
binding rule; check README/docs for restatements). Verify: (1) the statements
agree with each other and with the standard at the top of this prompt;
(2) nothing contradicts the mission (records DO carry measured numbers and
scope — the no-narrative rule must not read as "no detail"; ratification
stamps ARE dated by design); (3) the policy is itself short and well-defined.
If a statement is long-winded, duplicated, or contradictory, revise it in
place — smallest correct wording, one home, pointers elsewhere — and show the
before/after in your report.

## Rules

- This session edits: the new prompt file, the policy text (if Step 3 finds
  fault), and nothing else — the sweep itself belongs to the generic prompt's
  future runs.
- History mining is read-only; when citing removed comments, quote them
  verbatim with their commit hash.
- Comments and prompt text you write are held to the same standard they
  describe.
- Do not `git push` unless asked. Retire THIS prompt (`git rm
  prompts/COMMENT_HYGIENE_PROMPT.md`) when the sweep prompt is committed and
  the policy audit is recorded; `COMMENT_SWEEP_PROMPT.md` stays.

## Deliverable

A cited `.md` at the repo root: the category table (name, count, verbatim
examples, detector), the kept-comment counter-pattern, the policy audit
verdict with any before/after diffs, and the committed
`prompts/COMMENT_SWEEP_PROMPT.md`.
