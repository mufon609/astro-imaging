# Comment hygiene — the removal taxonomy, mined from the history

What this repo actually deletes from comments and records, derived from all 638
commits rather than assumed; the standing sweep tool built from it
([`prompts/COMMENT_SWEEP_PROMPT.md`](prompts/COMMENT_SWEEP_PROMPT.md)); and the
policy audit that found the date rule wrong as written.

## Method

Two corpora, kept separate because they answer different questions:

- **Code comments** — `git log -p --diff-filter=M -- '*.sh' '*.py'`, removed
  lines beginning `#`: **1,403 removed comment lines**.
- **Record prose** — `git log -p --diff-filter=M -- '*.md'`, removed lines:
  **15,397**. `--diff-filter=M` matters: **52 `.md` files were deleted
  wholesale**, and counting those lines would have drowned the in-place signal
  in doc retirements, which are a different mechanism (graduation, not hygiene).

Counts below are removed lines, not distinct comments; a multi-line comment
contributes several. They rank categories, they do not measure comments.

## The category table

| # | category | code | md | detector |
|---|---|---|---|---|
| 1 | **drift — asserts what the code contradicts** | — | — | semantic; grep the shipped script for every flag/path a comment names |
| 2 | date-stamped chronology | 10 | 245 | `20[0-9]{2}-[0-9]{2}-[0-9]{2}` |
| 3 | session / stream / arc narrative | 4 | 48 | `this session\|session [0-9]\|for (two\|three) sessions` |
| 4 | how-it-was-found story | 4 | 13 | `originally\|previously\|used to (be\|quote)\|turned out\|an audit (on\|found)` |
| 5 | retired-mechanism reference | 13 | 143 | `REVERTED\|RETIRED\|SUPERSEDED\|\blegacy\b\|the old chain` |
| 6 | numbered cross-reference that rots | 16 | 119 | `BACKLOG[: ]+item [0-9]\|\bitem [0-9]+\b\|NOTES S[0-9]` |
| 7 | line-number citation | — | 5 | `[a-zA-Z_/.-]+\.(py\|sh\|ssf\|md):[0-9]+` |

Every detector runs against the current tree and returns live hits (69 / 19 /
14 / 72 / 38 / 12 respectively) — most of them sanctioned uses, which is why
the sweep prompt pairs each with its exclusion rule rather than a delete order.

### 1. Drift — the costly one, and the only recurring one

Category 1 has no line count because it is semantic, and it is nonetheless the
finding that matters: **the same error recurred six times.** `e40c007` flagged
three drifted deep-dives, `1f5fc6c` corrected the fifth instance, `018ae54` the
sixth — all of them the ICC leg rule. From `1f5fc6c`'s message:

> the file asserted `--icc-type SRGB, never LIN_REC709` and a 16-bit savetif
> chain diagram, while the shipped `run_undistort_pipeline.sh` strips the ICC
> tag and exports LIN_REC709 on a `savetif32` float leg — the 16-bit-era rule
> stated as the production contract.

The severe case is `e40c007`, where a doc did not merely go stale but pointed a
future session at a discredited instrument. Its priority #1 read *"Radial-profile
undershoot ringing detector — reuses the existing radial profiles ... Cheapest
high-value win."* There were no existing radial profiles: `star_shape_profile.py`
was deleted in `e3864e8`, and it is **trap 3** in `docs/dead-ends.md` — the
metric whose origin moved with the defect. As the commit puts it:

> The file carried no caveat at all, so a session following TOOLS to it would be
> told that rebuilding the discredited metric was the cheapest available win.

This is why the sweep prompt's rule for category 1 is **revise, never delete**:
the drifted line still marks a real contract; only its content is wrong.

### 2. Date-stamped chronology

- `7489069` — `# It shipped ON 2026-07-29 (f170540) and cost 31x in background flatness: july31/`
- `3ac041a` — `# Defaults = APPROVED RECIPE B6 (2026-07-06 session 5, user-approved:`
- `9388b8f` — `# 2026-07-23 — the same procedure on the same frames under a different Hugin`

The `31x` survived; the date and the commit hash did not. That is the whole
rule: strip the date, keep the number.

### 3. Session / stream / arc narrative

- `3ac041a` — `# M0 (session 5): NO branch factor in the applied weight. The hard`
- `25bc0a5` — `For three sessions the registry used "cosmic dust", "MW", "IFN" and "dust-safe" interchangeably for FOUR physically unrelated things.`

The second is instructive: the *fact* (four unrelated senses) is still in
`docs/dead-ends.md`. Only "for three sessions" was clutter.

### 4. How-it-was-found story

The cleanest instance is `7854550`, which trimmed a `CLAUDE.md` rule to its
constraint — a whole incident paragraph out, one clause in:

```diff
-  own scope (measured cost: "the repo versions process, not image data" — a
-  rule about GIT — was transplanted into the archival contract and inverted
-  the FITS self-description standard; combining would have required repo
-  access years later. The industry answer, self-describing files, was basic,
-  known, and unasked-for). The bright line's anti-drift test already forces
-  this question for pixel operations; this rule forces it for design.
+  own scope. The bright line's anti-drift test forces this question for pixel
+  operations; this rule forces it for design.
```

**The discriminator is numbers, not tense.** That paragraph had none — it was a
story. `CLAUDE.md` keeps a "measured cost" one line away (*"the fingerprint
measured it four independent times within 0.6% of sidereal"*) because that one
carries the evidence the rule rests on.

### 5. Retired-mechanism reference

- `7489069` — ``# !! REVERTED 2026-08-04 — `--desky` IS OFF BY DEFAULT AND IS A KNOWN REGRESSION.``
- `4ca79cc` — `# geometry (the ~231 MB/frame this line used to quote was the retired 16-bit`

### 6. Numbered cross-references

`c76af73` re-keyed BACKLOG to slugs, 615 lines → 285, and named the mechanism
outright: *"NUMERIC KEYS WERE THE CLUTTER MECHANISM"*, after *"numeric
cross-references had gone stale twice"*. It removed eleven such comments from
scripts alone, e.g. `# BACKLOG item 19: index-style excludes measured silently
no-opping in the`.

### 7. Line-number citations

`5e66292` corrected `run_set_chain.sh:112,353` → `145,425`, `README.md:576` →
`586`, and `siril/master_dark.ssf:14` → `15` — then added the standing
instruction to *"grep the predicate rather than trust the numbers, since they
have now drifted once."* Twelve such citations remain in the tree.

### The category the history does NOT support

The brief anticipated **victory / status language** ("fixed", "final",
"matched", "close"). **Zero instances have ever been removed** — a targeted
search across all 638 commits and both corpora returned nothing. It is stopped
at write time by the `WIN | NULL | needs-eyes` rule, not by sweeps. Worse, the
obvious detector is actively harmful: grepping the removal corpus for all four
banned words returns only domain vocabulary — *fixed mount*, *fixed-px annuli*,
*matched-flat*, *matched darks*, *final chunk* — and, at rank 30, the policy
line quoting its own ban. **No genuine instance, and no true positive to
offset the noise.** The sweep prompt records this as a non-category so a future
run does not re-derive the same empty result.

## The counter-pattern — what gets kept and strengthened

By revealed preference, the shape that survives is **constraint + why + the
number + the scope it holds at**, present tense. From `4d70455`,
`scripts/calibrate/solve_field.py`:

    # The hint radius is the declared position uncertainty. Twice it is already
    # generous — every hinted solve in this corpus lands within 0.27 deg of a 15
    # deg hint (68 records replayed) — while the measured false solve sat ~110
    # deg out, 7x the radius. So this separates by two orders of magnitude and
    # is not a tuned number.

What earns the space: a number, its sample size (68 records), and an explicit
claim about what the number does not prove (not a tuned threshold). **Length is
not the target — staleness is.** `8d370dd`'s guard header runs some twenty
lines and is entirely load-bearing, including a paragraph on why literals at
every site beat one shared constant.

The revise-not-remove case is `3072fd0`, which contains a `used to` that
category 4's detector flags and that must **not** be dropped:

    # ... It used to ask only about the line, so a block whose <vignetting> had
    # come back while the coefficients stayed right reported "already installed"
    # and exited 0, leaving the DB double-correcting: MEASURED by reinstating the
    # fitted lens's focal=70 aperture=4 vignetting pair by hand — verify_lens_card
    # read a 4219 ADU corner-vs-centre step on a 30000 ADU uniform card (tol 1.0)
    # while this script said there was nothing to do.

It carries a measured defect with its tolerance. It is REVISED to present tense
("the idempotence test covers both halves; asking only about the line reports
'already installed' on a block whose vignetting came back — 4219 ADU on a 30000
ADU card, tol 1.0"), never deleted.

## Policy audit

**Where it is stated:** exactly one place — `CLAUDE.md`, binding rules. `README.md`
carries no restatement (checked); `MEMORY.md` gestures at it once (*"outcomes
with numbers — never narratives"*) as a characterization of the user, not a
competing statement of the rule. **One home, no duplication — passes.**

**Contradiction with the mission: NONE found.** The no-narrative rule does not
read as "no detail" — the same bullet requires "its measured numbers", and the
adjacent rules mandate measured deltas throughout.

**One fault found, and it was load-bearing.** The rule read:

> (Doctrine ratification stamps are the one exception — they order which rule
> supersedes which.)

**That is false about this repo, and a sweep obeying it literally would have
destroyed mandated data.** Three classes of date are in active, sanctioned use
and only the first was covered:

1. ratification stamps — `CLAUDE.md`'s `(user-ratified, 2026-08-06)`;
2. **last-checked / measured-on stamps** — `CLAUDE.md`'s own
   `**The rig** (measured, 2026-08-05)`, `install_lens_model.sh`'s
   `MEASURED 2026-08-05`, and above all **`BACKLOG.md`'s removal-condition
   register, whose re-verify column is entirely dates** (`| 2026-08-10 | not
   fired`). `018ae54` ratified this class explicitly: *"Re-verification dates on
   tool claims stay — they are register-style last-checked data, not
   narrative."*
3. **`docs/README.md`'s deep-dive template**, which *requires* a dated
   **Context** line of every deep-dive — a second tracked document mandating
   what the binding rule forbade.

The unifying principle, which the rule now states: **a date is allowed where the
date IS the information** — what supersedes what, or how stale a claim is. Both
are register data. Before/after:

```diff
-- **No session/stream/ladder tags, dates, or chronological narrative in
+- **No session/stream/ladder tags, chronological narrative, or bare dates in
   comments or record entries** (scripts, BACKLOG, docs alike) — state the
   constraint and its measured numbers, get to the point; when and in what
-  order lives in git only. (Doctrine ratification stamps are the one
-  exception — they order which rule supersedes which.)
+  order lives in git only. A date is allowed only where the date IS the
+  information: a doctrine ratification stamp (which rule supersedes which), or
+  a last-checked stamp on a claim that goes stale (rig inventory, tool version,
+  measured-on-this-rig). Both are register data, not narrative.
```

Two lines longer, and the only version a sweep can be run against safely.

## The deliverable

[`prompts/COMMENT_SWEEP_PROMPT.md`](prompts/COMMENT_SWEEP_PROMPT.md) — marked
**NON-RETIRING**, unlike the one-shot briefs beside it. It carries the policy in
full (so a sweep session needs no other context), the counter-pattern above, the
seven categories with detector + verbatim example + revise-vs-remove rule, the
two traps a naive sweep falls into (`session` is this repo's domain noun for an
imaging night; `fixed` is a geometry adjective), the safety rule (remove only
what is false, preserved elsewhere, or pure chronology — everything else is
revised to the shortest correct form), the scope exclusions, and a four-point
acceptance shape.

**Scope of this record:** the taxonomy is derived from this repo's own history
and holds for it. The counts rank categories; they are removed lines, not
distinct comments. No sweep was run — that is the deliverable's job, on the
owner's schedule.
