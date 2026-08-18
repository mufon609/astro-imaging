# Historian handoff

**PROMPT-KIND: register**

**THIS IS NOT A ROLE DOC AND MUST NOT BECOME ONE.** The historian role doc is
OWNER-HELD (`BACKLOG:pending-owner`) with a stated prerequisite: an understanding
of how the seat has been helpful, gathered from the Oracle. The seat correctly
refused to write its own and so do I. What follows is **what I was told and what
I did** — a snapshot that dies when you replace it, not a specification. **Replace
this file; do not add a second.**

**Read `prompts/ORACLE_HANDOFF.md` for the shape.** This carries only what a
document cannot: my errors, my searched negatives, and which of my claims are
inference.

---

## 1. THE REMIT, AS DICTATED TO ME

The other seats answer **what is true now**. You answer **why the tree is the way
it is**: why a file, rule, number or entry was implemented, what was tested, what
was considered and rejected, what the author believed, and whether it still holds.
**Sources: `git log`, the commit MESSAGES, the diffs, and the artifact at each
commit.** Session reports are deleted by design here — the messages are the only
surviving transcript. That is why this seat exists.

**READ ORDER:** `CLAUDE.md` → `docs/dead-ends.md` COMPLETELY → `BACKLOG.md` →
`TOOLS.md` → `MEMORY.md` → `README.md` → `prompts/`. Then run
`./scripts/qa/run_guards.sh` yourself. Then `git log` — it is the transcript.

**YOUR FIRST REPORT IS WHAT THE BRIEF GOT WRONG.** Not an acknowledgement, not a
plan. Every brief here has carried at least one error, mine included. **A first
report with nothing in it is a warning about the brief.**

## 2. THE METHOD — four rules

1. **A claim you EXECUTED is yours; one you READ is a hypothesis** — including
   commit messages. A message is its author's account, not the artifact. **Where
   they differ the artifact wins, and that gap is usually the best finding.**
2. **QUOTE THE ARTIFACT VERBATIM. NEVER QUOTE A PERSON ON A PEER'S SAY-SO.** Git
   is checkable; a relayed sentence is not. Write *"X relayed the owner as
   saying…"*, never *"the owner said…"*, without their own text.
3. **Never MEASURE a live tree.** Pin with `git show <sha>:<path>` and **state the
   commit every number was taken at**. A finding about the tree is perishable by
   construction — mine went stale inside two hours, twice, once by a peer's commit
   landing between my measurement and their cut.
4. **Report the failed searches and the empty results. A searched negative is a
   full deliverable.**

## 3. SCOPE LIMIT

**You see the tree's HISTORY, not the team's.** A proposal never committed leaves
no trace. **Refuse rather than reconstruct.** I did this once and it held: a peer
reported a tool as "published backwards twice"; the tool's name is 0 files
tree-wide, so it cannot be a tree fact, and it went back rather than into a record.

## 4. THE SEAT'S FAILURE MODE — assume you are doing this

**ATTRIBUTION FROM PLAUSIBILITY RATHER THAN FROM THE RECORD.** Three variants,
all measured on this seat:

- **Object-level** — authorship blamed on whoever was busy; a commit attributed to
  a session it predated by ten hours; a class reported from commit SUBJECTS nobody
  had diffed.
- **One level up** — attributing to the OWNER something held only from a peer.
- **State-level** — a destination CHECK reported as a LANDING, because siblings had
  landed and the check was done.

**Mine, this session, in its cheapest form twice:** I called a coordinate site
"reduced precision" because it failed an exact-literal search — it is full
precision differing in the last digit. **I inferred from a search RESULT instead
of reading the LINE.** And I read `run_session_chain.sh` in my own output as the
`run_set_chain.sh` a peer had named, and nearly confirmed a false claim; it
surfaced only because a later grep returned empty and I chased the empty.

**And the sharpest form: a FRESHER measurement of mine displacing an OLDER correct
account. Recency is not authority in this seat. The artifact is.**

## 5. INSTRUMENT HAZARDS — a family of nine, then one that is different

Every one is a search that returned a confident wrong answer. **Read the matches,
never count them** — `-c` answers presence, not assertion, and a corrected record
deliberately contains the string it corrects.

1. **Wrapped prose defeats a line-oriented grep.** Three instances in one day, one
   pointing at a person — the most expensive direction. **Joining lines is not
   enough: continuations are indented, so `tr '\n' ' ' | tr -s ' '`.**
2. **Case, BOTH directions, same day.** `git grep -ilF 'DISTORT_'` → 43 files;
   case-sensitive → 5, because the tree writes `undistort_` everywhere. Five
   minutes later a peer's case-SENSITIVE search for `transfer function` returned 0
   on a phrase that is capitalised. **There is no safe default casing.**
3. **Unescaped `.` is a regex wildcard.** 13 apparent hits on a branch with 0. Had
   I reported it I would have said a private coordinate was already published.
4. **Float and star-list collisions.** `6.26` sits inside `206.265`; `40.078…`
   inside Siril findstar values.
5. **Brace notation defeats a basename screen** — `master_{bias,flat,dark}.ssf`,
   `siril_run.{sh,py}`. **Twice, both mine, on two separate censuses.**
6. **Rounding produces FALSE UNHOMED** — `2.2050` against a ledger's `2.205`.
   First member of the family whose failure is CONSERVATIVE; it blocks a correct
   cut rather than permitting a wrong one. **Say that out loud wherever it lands,
   because "it only over-reports" is how an over-reporting check gets relaxed.**
7. **zsh: unquoted `$REV:scripts/…` breaks on the `:s` modifier — and DOUBLE
   QUOTING DOES NOT DEFEND IT. Braces do: `"${R}:scripts/…"`.** Whether it fails
   loud or silent depends on the positions of `c` in the remainder. Measured over
   all 113 tracked `scripts/` paths: **45% loud, 32% bare rev (pathspec silently
   vanishes and you get a tree-wide answer that looks legitimate), 22% mangled.**
   Under `2>/dev/null` inside `$(…)` it returns empty and reads as a searched
   negative.
8. **`git grep`/`git log -S` need `-e` for a pattern starting with `-`.**
9. **A single `-S` on a string that wraps returns EMPTY, and empty reads as never
   existed.** Search single-line substrings.

**AND THE ONE THAT IS NOT A MATCHING FAILURE — the Oracle's, and it outranks the
nine.** A grep of Montage's source for `pix2foc`/`distortinit` returns **zero and
the capability is still used**, because the call runs through a library the caller
never names. **The string answer is RIGHT and the capability answer is WRONG.** It
cannot be fixed by better matching, only by reading the call chain.

## 6. TWO RULES IN FORCE

- **THE MIGRATION TEST.** A fact earns a migration only if its absence would make
  someone **REDO CLOSED WORK or REACH A WRONG CONCLUSION**. Otherwise cut — git
  holds it. *"It exists nowhere else"* is why it is unhomed, not why it is needed.
  **BOUNDARY: this governs CLOSED facts. Open work is unhomed by definition and
  stays.**
- **INBOUND-POINTER SWEEP BEFORE EVERY CUT. No size threshold, wide scope. Sweep
  the SET, not each block** — a block queued later can be the target of a pointer
  you cleared earlier. **Carry both numbers: this rule went 6 for 6; the hypothesis
  it replaced (*"self-declaring sections are the dangerous ones"*) went 0 for 3.
  The failed one is what makes the surviving one credible.**

## 7. UNCHECKED AND UNDISCHARGED — carry these, they are not closed

- **The `README.md` repo map is UNREAD against its code — 62 of 80 rows when I
  measured, and it is 82 rows now, so the unread count has grown. Unchecked, NOT
  clean.** Existence is a census (39/39 named present, 0 missing); truth is a
  sample of 18. **State the row count you measured at; it moves daily.**
- **`prompts/PROJECT_MANAGER_PROMPT.md:28` and `BACKLOG.md:178-179` carry a relayed
  owner quote presented as his direct words.** `relay` returns **0** in the PM file;
  `BACKLOG` has one hit at `:1062` on unrelated prose, so **both quotes are still
  unflagged**. **Mine to flag, unresolved pending the owner's own text. Do not let
  it retire unrecorded.**
- **DISCHARGED WHILE THIS FILE WAS BEING WRITTEN — and that is the lesson, not the
  item.** `docs/wide-field-untracked-registration.md:209` closed the
  WCS-reprojection route on a premise since scoped to single trailed frames. It was
  written BY an audit pass (`1f5fc6c`), refuted seven days later (`1e7c15e`), and
  untouched for nine days. **I listed it here as open; the worker fixed it at
  `77cec6c` in the minutes between my writing the line and re-verifying it.** The
  file now carries the narrowing. **A finding about the tree is perishable by
  construction and this document is not exempt: THREE of my claims went stale
  between drafting and hashing. Re-verify every number in section 7 before acting
  on it — do not inherit them.**
- **Two `scripts/ingest/` scripts are evidenced by NOTHING** — no doc, no caller,
  no output record. **UNCLEAR is the verdict, not a gap I failed to close.**
- **Five of ~11 register removals were traced only after a peer flagged that a
  ruling on 7 of 12 is a ruling on a sample.** They are traced now; the lesson is
  that the flag was right.

## 8. WHAT I GOT WRONG, because you inherit the seat and not the lessons

- **I gave a peer a defence that does not work** — *"quote the ref-path"*, when
  only braces defend. **Inference from a result rather than from the mechanism, one
  message after issuing the warning.** It corrupted four of my own measurements
  within the hour, three of them as clean zeros.
- **I reported a zero-inbound-pointer result that was correct and went stale**,
  and a peer's own commit created the pointers between my measurement and their
  cut. **Re-run a pointer check immediately before anything moves, never from a
  message.**
- **My basename screens over-report on brace notation, twice**, and my
  reword-vs-removal classification missed a divergence renamed across categories
  (a DATASET name to a SCRIPT name).
- **Eight numeric quantities moved in one day** because two sessions measured
  differently and neither stated the filter. **State your filter with every count.
  It is the single cheapest discipline in this repo and the most often skipped.**
