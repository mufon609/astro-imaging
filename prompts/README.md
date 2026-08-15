# `prompts/` — what lives here, and where a lesson goes instead

**PROMPT-KIND: contract**

This directory holds the session role definitions and the working register. It is
the one writable surface in this repo that had **no destination rule and no
guard**, and it became the sink for everything sessions learned. This file is the
rule; `scripts/qa/check_prompt_scope.sh` is the part of it a machine can check.

---

## THE DEFECT THIS EXISTS TO PREVENT — measured, one day

A lesson learned mid-session has to be written somewhere. With no rule saying
where, it goes into the file the session already has open: its own role doc. The
role doc still contains the right instructions afterwards — **it is not corrupted,
it is DILUTED**, and the remit ends up below the depth a fresh session's attention
reaches.

```
PROJECT_MANAGER_PROMPT.md   419 → 459 → 503 → 532 → 565 → 598 → 624 → 637 → 647 → 654 → 668 → 213
ORACLE_TEMPLATE.md          233 → 362 → 388 → 397 → 407 → 445 → 463 → 482 → 555 → 565 → 222
```

Both grew across a single day and were then cut by two-thirds in one commit each.
**28 commits touching this directory netted the PM from 419 lines to 213 and the
Oracle from 233 to 238.** In the last two hours of that day, 21 commits touched
**zero** scripts and **zero** dataset records.

Two facts make this a structural problem rather than a bad day:

1. **The dilution is invisible from inside.** At 555 lines the Oracle's stated
   reason for existing sat at **line 455**, behind 454 lines of *how you fail*. No
   sentence in the file was wrong. A session reading it top-down calibrates on the
   failure catalogue and never reaches the remit.
2. **The correction is the second failure mode.** The panic cut that fixed the
   length **kept a prohibition and deleted every description of the failure it
   forbids** (`ced28ce`) — *"never report a negative from a structurally-impossible
   view"* survived while the definition of a structurally-impossible view went to
   zero tracked files. Length is gateable. A bad cut is not.

---

## THE DESTINATION RULE

**Every fact has exactly one home, and for almost everything a session learns, it
is not this directory.** A second home for a fact is a second place for it to
drift — the repo already carries that rule for code; this states it for prose.

| what you learned | where it goes |
|---|---|
| a mechanism, a number, a way an instrument fails here | `docs/dead-ends.md` |
| a tool's capability, limit, version, or flag behaviour | `TOOLS.md` |
| open work; a divergence and its removal condition | `BACKLOG.md` |
| how the owner works and judges | `MEMORY.md` |
| the contract itself | `CLAUDE.md` — **owner only, never a session's to edit** |
| what is queued, with whom, and what is pending the owner | `BACKLOG.md` (`pending-owner` for the last) |
| **the remit of one role, and its startup order** | **the role doc — and nothing else** |

### The discriminator — one question, and it settles almost every case

> **Would this sentence be true for a DIFFERENT role?**

**If yes, it is not role text.** It is a repo fact that belongs in the registry,
and putting it in a role doc gives it as many homes as there are roles.

- *"`grep` in an agent's shell is ugrep 7.5.0; `timeout grep` is GNU grep 3.12"* —
  true for every role. **Registry.** It was written into a role doc, which is how
  one shell shadow produced four write-ups of a single search failure, three wrong.
- *"You produce no measurement of our image data, ever"* — true of the Oracle and
  false of the worker. **Role doc.**
- *"A first report with nothing in it is a warning about the brief"* — true for
  every role, and it is correctly in `CLAUDE.md`'s orbit rather than restated
  three times here. Where a role doc must repeat it, that repetition is the cost
  being paid knowingly, not an accident.

### Before you CUT anything, check the destination

*"A second home is a second place to drift"* is only safe **once the first home
exists**. Migrate first, in the same commit, then cut. This is register rule (1)
— add the row in the same commit as the divergence — applied to prose. It has
been violated twice in measured cases, once by the session that wrote the rule.

---

## THE FOUR KINDS — every `.md` here declares exactly one

The declaration is one visible line near the top of the file:

```
**PROMPT-KIND: role**
```

It is visible rather than an HTML comment on purpose: this directory's failure
mode is text being cut without being read, and an invisible marker is the first
thing a cut loses.

| kind | what it is | ceiling | lifetime |
|---|---|---|---|
| `contract` | this file — the directory's own rule | **yes** | durable |
| `role` | a role definition, read by every session of that role at startup | **yes** | durable |
| `brief` | one engagement's task, with its acceptance criteria | no | **retired on completion**, unless the file declares itself standing |
| `register` | live state — the queue, the done-ledger, a handoff | no | shed as items land |

**A file with no marker, or with two, is RED.** The guard fails closed, because
the alternative is the hole this repo already documents as the worse case: a
detector that starts from declarations cannot see a thing that declares nothing.

**`brief` and `register` have no ceiling and that is deliberate, not an
oversight.** A brief may need to be long — it carries a full acceptance
specification and then dies. A register is *supposed* to accumulate and shed. The
ceiling exists for documents that are **read at startup by every session in that
role**, because that is the only place where length converts into diluted
judgement.

**The loophole this leaves is real: text evicted from a role doc can be parked in
an unceilinged `brief` that every session is then told to read.** Nothing detects
that. It is named here so that doing it is a choice rather than a drift.

---

## THE CEILING — 300 lines and 20,000 bytes, whichever binds first

Applies to `contract` and `role` only.

**Why two axes.** Line count alone is Goodhart-shaped — it is satisfiable by
writing longer lines, and this directory already contains an 827-character line.
The byte ceiling is the backstop. Both are proxies; see the limits below.

**Why 300.** It is calibrated against real data on both sides:

| | lines | bytes | verdict |
|---|---|---|---|
| `ADVERSARY_TEMPLATE.md` | 100 | 5,003 | passes |
| `WORKER_TEMPLATE.md` | 129 | 7,630 | passes |
| `PROJECT_MANAGER_PROMPT.md` | 215 | 13,170 | passes |
| `ORACLE_TEMPLATE.md` | 245 | 13,936 | passes |
| `ORACLE_TEMPLATE.md` @ `42e1f1e` | **565** | **34,962** | **RED on both axes** |
| `PROJECT_MANAGER_PROMPT.md` @ `deb4ef8` | **668** | **45,494** | **RED on both axes** |

22% headroom in lines over the largest live role doc, 43% in bytes. And it fires
where it should have: the Oracle's **first** accretion commit of that day took it
233 → 362, which 300 catches. The PM entered the day at 419 — already over, and it
was cut to 213 for exactly that reason.

**A ceiling is a budget, not a target.** Hitting it means something must LEAVE,
and the destination table says where. It does not mean the file is finished.

---

## STANDARDS-FIRST — what this reimplements, and why it deviates

`CLAUDE.md` requires naming the industry-standard way first.

**The standard is Diátaxis** (Daniele Procida, <https://diataxis.fr>), the
documentation architecture that partitions docs by *what the reader is doing* —
tutorial, how-to, reference, explanation — on the claim that mixing modes degrades
all of them, and that the characteristic failure is **accretion of explanation
into instruction**. That is precisely the defect measured above: role docs are
*instruction*, and what accreted into them was *explanation*. The four kinds here
are Diátaxis's move applied to a two-mode corpus.

**STATUS: DOCTRINE, source named, not measured here.**

**The measured constraint that forces the deviation: Diátaxis prescribes no
enforcement, and no off-the-shelf linter checks file-scope mode purity.**
`markdownlint`'s MD013 bounds *line* length, not file length or content class;
Vale and textlint check prose style and terminology, not whether a paragraph
belongs in the document it is in. There is nothing to bind a mode-purity test to.
So the deviation is a **size proxy**, hand-rolled, and the honest statement of it
is that it measures a correlate of the defect and not the defect.

If a linter that classifies documentation mode ever exists, this guard should be
replaced by it rather than extended.

---

## WHAT THE GUARD STRUCTURALLY CANNOT SEE

Read this before treating a GREEN run as coverage. There are three holes and the
guard covers none of them:

1. **Whether a sentence in a role doc has a first home elsewhere.** This is the
   actual defect. It is not greppable, and no metric should be invented to stand
   in for it — a repo-local attempt to proxy "does this cite a source" produced a
   count that **falsified itself on commit** and generated the opposite of the
   correct instruction.
2. **A destructive cut.** 668 → 213 passes this guard on every axis while deleting
   load-bearing text. The only defence is the destination rule above, and it is
   prose. `ced28ce` is the recorded instance.
3. **Dilution under the ceiling.** A 290-line role doc whose remit is at line 250
   is exactly the failure this exists to prevent, and it is GREEN.
4. **A CLAIM AND ITS REFUTATION, EACH ROUTED CORRECTLY, LANDING IN DIFFERENT FILES
   WITH NOTHING BRINGING THEM BACK TOGETHER.** This is not a guard gap — it is the
   destination rule's own mechanism, and it is not fixable by routing harder.
   MEASURED, and the instance is this repo's: *"no installed tool can correct a
   field-variable anisotropic PSF"* is a closed route and belongs in the registry;
   *"PSFEx implements the correction"* is a tool capability and belongs in
   `TOOLS.md`. Both routings were RIGHT. The two commits landed **35 minutes
   apart** in one research arc, neither referencing the other, and the
   contradiction stood for a day.
   **AND THE OBVIOUS MITIGATION IS ALREADY FALSIFIED HERE: more cross-references do
   not fix it.** `TOOLS.md` DID carry a pointer naming a third site as *"FALSE and
   needs correcting"* — it sat unactioned, and the session that later found the
   contradiction had READ that pointer during its own boot and still re-derived half
   of it hours later. **The tree can carry its own correction, unactioned, and still
   not reach a reader who has read it.**
   **DECIDED, not omitted: no machinery is built for this.** The mitigation that
   actually worked is a SEAT rather than a mechanism — a standing contradiction hunt
   across our docs and the tools' own, and a check on whether a later commit
   silently changed an earlier conclusion's standing. Both are staffed roles. If
   this class recurs with both seats running, that is the evidence that would
   reopen the question.

**So the yield of this guard is narrow and the bound is the useful half:** it
catches unbounded accretion, which is one of the three, and it is the only one of
the three a machine can catch. Everything else in this directory is held by the
destination rule and by whoever reads the diff.

---

## ADDING A FILE HERE

1. Declare its kind on a `**PROMPT-KIND: …**` line near the top.
2. If it is a `brief`, say in the file what retires it. Briefs are deleted on
   completion; history is git's.
3. Run `./scripts/qa/check_prompt_scope.sh` before you commit.
