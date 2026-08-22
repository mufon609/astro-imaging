# Verification traps — checks and search instruments that lie

Phase-2 file of the dead-ends registry split (`README.md` in this directory
holds the index and the per-file dispositions). Entries below are maintained
IN PLACE — no longer byte-verbatim with `docs/dead-ends.md`; revisions are in
git and `split.py` no longer regenerates this file. Cross-references to
entries in sibling files are written as (`<file>.md`, entry) pointers;
unmarked "above"/"below" references resolve within this file.

<!-- phase-2: maintained in place; not regenerated from the manifest -->
- **A CHECK THAT ONLY VERIFIES THE FROZEN HALF CANNOT FAIL IN THE DIRECTION THAT
  MATTERS.** Pinning registration across an A/B is verified by the arm's canvas
  matching the donor's — and a pin that worked by accidentally DISABLING the
  treatment produces an identical canvas too. So the geometry check alone passes
  on the one outcome that would void the experiment. The whole verification is
  **frozen AND the knob still acted**: MEASURED on the aug06 L1 arm, donor vs
  pinned arm member, canvas 5830×3958 both ways while **69,225,418 of
  69,225,420 px (100.00%) differ**. Generalises past registration to every
  "held fixed by construction" claim — assert what must NOT move and, in the
  same breath, what MUST. The second assertion is the one that feels redundant
  while writing it, which is exactly how the class survives.
- **A WATCHER LOOP WHOSE OWN COMMAND LINE CONTAINS ITS `pgrep` PATTERN WAITS
  FOR ITSELF, FOREVER.** `until ! pgrep -f 'scratchpad/foo.sh'; do sleep; done`
  has that string in its own argv, so `pgrep` matches the watching shell and
  the condition never clears — and any *other* loop waiting on that pattern
  deadlocks behind it. MEASURED: **seven hours of idle wall-clock** across two
  separate stages of one chain, with the real work finished and nothing running.
  It is silent — `pgrep` reports the stage "alive", so a status check confirms
  health while nothing computes. Tells: a stage "running" with a zero-byte
  output file, and `ps` showing no tool process. Fix at the source — a pidfile,
  `pgrep -f pat | grep -v $$`, or splitting the literal (`'foo''.sh'`) so argv
  never holds the pattern.
  **AND IT WAS NOT IN THE BRIEF.** Checked rather than assumed: the L1 brief's
  acceptance item 9 says only *"`pgrep -f` any chain script before editing
  it"* — about not editing a live script, a different hazard — and the words
  watcher, self-match and immortal shell appear nowhere in it. So this is NOT
  an instance of a named warning failing; it is a trap that the person writing
  the acceptance criteria did not see coming while writing a criterion about
  `pgrep`. That is the more useful lesson and the weaker claim: proximity to a
  hazard in prose is not coverage of it. (The brief itself is since retired
  with the role docs — zero tracked matches; the lesson is not.)
  **AND THE OPPOSITE DIRECTION IS ALSO LIVE: `pgrep` SAMPLES AN INSTANT, SO IT
  CANNOT REFUTE AN INTERVAL CLAIM.** The entry above is the false POSITIVE
  (`pgrep` reports alive while nothing computes); this is the false NEGATIVE, and
  it is the one that closes an investigation early. MEASURED while diagnosing a
  concurrency race in `run_guards.sh`: a session `pgrep`ed for a competing run,
  saw none, and declared the race refuted — while the runner's own kept log
  carried `[siril_run] another Siril job holds the lock — waiting` on the exact
  path that then died. **The log recorded the INTERVAL; the process check sampled
  one moment inside it.** For any claim of the form "nothing else was running",
  the admissible evidence is a record covering the whole window — a lock line, a
  timestamped log, a pidfile with its lifetime — never a point observation. Same
  rule as reading the artifact rather than the description, applied to time.
- **THE DETECTOR CAN BE RIGHT AND THE DISPLAY THROW THE ANSWER AWAY — a distinct
  failure from a check pointed at the wrong object, and it reads as a clean
  negative.** Every other entry in this family is a target list built from a
  remembered name. This one is not: the search was correct, it MATCHED, and the
  rendering discarded the evidence. **MEASURED, twice on one claim, at opposite
  ends of the same length problem.** A route-closing sentence — *"`sip_tpv` IS NOT
  INSTALLED ON THIS RIG … adopting it needs a manifest row"*, false, gating the
  SWarp route on the largest measured defect in any shipped product — sat at **byte
  offset 539 of a 4,640-character table cell**. One sweep of that file's negative
  claims read the row and never reached it. A second session then grepped for it,
  **matched it correctly**, piped through `cut -c1-190` for readability, saw only
  the first 190 characters (about an unrelated canvas result) and reported the
  sentence did not exist anywhere in the tree — **a confident negative produced by
  a correct detector**. The claim was 349 characters past the cut.
  **MECHANISM CORRECTED — truncation does not merely WITHHOLD the evidence, it
  SUBSTITUTES a familiar one, and that is why the reader stops with justification
  rather than stopping short.** The head-end instance is the proof: that session
  read the first ~260 characters, recognised its OWN already-settled SWarp finding
  there, and correctly concluded the row was accounted for. Nothing looked
  truncated; it looked answered. **A window does not present as partial — it
  presents as the object**, so the stopping rule fires on content that is real,
  relevant and irrelevant to the question. **The instrument fix follows from that:
  window on the MATCH, not on the line — and use the TRAILING-RANGE form,
  `grep -oE "PATTERN.{0,200}"`, never `grep -n PATTERN | cut`.** (This entry
  first recommended the exact-count two-sided window `.{60}PATTERN.{110}`,
  RETRACTED: that form was later measured STRUCTURALLY IMPOSSIBLE on wrapped
  prose — MODE 1 of the three-modes entry below; this registry's own longest
  line is 108 — and the two-range `{0,n}` repair hits ugrep's complexity limit,
  MODE 2.) And state coverage as what was actually read: the
  head-end sweep's honest coverage was *"the first 260 characters of each matching
  row"*, never *"the rows"*.
  **The two failures are the same defect at both ends: a fact buried past where
  anyone reads.** 4,640 characters hid it from the sweep; 190 characters hid it
  from the grep. **So a length limit added for readability is part of the
  instrument and inherits its verdict** — `grep -c` on the file or `grep -o` on the
  pattern would both have been right, `grep -n | cut` was not.
  **THE RULE: never report a NEGATIVE from a truncated view.** A positive survives
  truncation — you saw the thing. A negative asserts absence over the whole object,
  and a window cannot support that. Count, or extract the match itself; the
  cheapest correct forms are `grep -c` and `grep -o`. **Corollary for the records:
  a claim that cannot be found inside the cell that contains it is already lost —
  compress so that each claim survives as a separately greppable statement, since
  the failure here was not length alone but one sentence being unfindable inside
  another.**
  **SIBLING, AND IT QUALIFIES THE FIX ABOVE: `grep -c` IS NOT A SAFE FALLBACK WHEN
  THE QUESTION IS WHAT A SENTENCE ASSERTS.** Same family — a reduction applied
  after a correct match, discarding what the match was for. MEASURED on the same
  claim: checking whether the false `sip_tpv` sentence was still live,
  `grep -c "IS NOT INSTALLED ON THIS RIG"` returned **1 before the fix, 1 after,
  and 1 at HEAD** — read as a count, "still broken". It was not: the fix RETRACTS
  the claim while QUOTING it, so the phrase survives by design, exactly as a
  withdrawn `~1.1` does elsewhere in this registry (the paraphrased-result
  entry, `evidence-provenance.md`). **A count answers presence, not
  assertion, and a corrected record deliberately contains the string it corrects —
  so on a well-maintained tree the count is guaranteed to mislead.** Read the
  sentence. The correct instrument here is `grep -o` with context, and then human
  reading of what came back.
- **AN INSTRUMENT THAT RETURNS A PLAUSIBLE ANSWER WHILE MEASURING NOTHING IS THE
  DOMINANT FAILURE MODE HERE, AND READING ITS OUTPUT NEVER CATCHES IT — RE-RUNNING
  DOES. FOUR IN ONE SESSION, EACH IN A DIFFERENT INSTRUMENT, NONE OF THEM AN
  ERROR.** Every one produced a well-formed result that a careful reader would
  accept:
  - **A DELETION FILTER BLIND TO THE CONTENT IT PROTECTS.** `CLAUDE.md` then
    required reading the `-` lines of any deletion, `git diff | grep '^-'`. Refining that to
    `grep -E '^-[^-]'` to drop the `--- a/file` header **silently excludes every
    deleted markdown BULLET**, because a removed `- **item**` renders as
    `-- **item**`. MEASURED on a 97-line cut: the refined form showed **83** lines
    and the correct form **97**, and all 14 hidden lines were bullet TITLES — the
    exact class the rule exists to protect, and the class of this file's own
    registered instance where an accurate numstat passed while a title was
    destroyed. **A limit added for readability becomes part of the instrument and
    inherits its verdict.** Correct forms: plain `grep '^-'`, or
    `awk '/^--- /{next} /^-/'`.
  - **A SHELL PROBE THAT CANNOT DO WHAT IT CLAIMS.** Testing a path derivation by
    setting `BASH_SOURCE` inside `bash -c` — it cannot be overridden that way, and
    every arm returned `/home`: a real path, measuring nothing. Settled by
    EXECUTING a probe carrying the line verbatim at a foreign path.
  - **A SWEEP STRUCTURALLY UNABLE TO SEE WHAT IT WAS ASKED.** An omission sweep was
    used to ask whether a reason for an omission had been STATED. It shows what is
    absent and can never show what is explained — a check whose mechanism excludes
    the thing it tests for, run by an auditor while auditing.
  - **A COUNT RIGHT BY TWO CANCELLING ERRORS**, and the count itself gives no sign.
  **THE COMMON SHAPE: none returned an error, and none returned an implausible
  number.** Reading harder does not reach any of them, because the output is exactly
  what a correct run would look like. **What reached all four was running the
  measurement a second way — a different instrument, an execution instead of a
  simulation, or the same query at a state known to be clean.**
  **AND THE CONTROL THAT MAKES IT CHEAP: before believing an instrument reports a
  defect, run it on a case whose answer is already known.** A block-parity scan read
  ODD on an edited entry — the signature of real damage — and the same scan on the
  PRE-EDIT file read ODD too, because the extraction began mid-span. One command,
  and it separated an artifact from a finding.
  (n=4, one session; surfaced from ordinary work rather than from looking for the
  class, so do not compute a rate. The decision the `^-[^-]` instance flagged is
  CLOSED: `CLAUDE.md` no longer prescribes any grep form — its check is
  whole-hunk accounting, `git diff -- <file>` with every hunk accounted for
  (zero `^-` literals in the contract at `614ad33`) — and the measurement stays
  as the reason a header-dropping refinement must never come back.)

- **THE FIRST MEMBER OF THE COLLISION FAMILY THAT IS NOT A MATCHING FAILURE: THE
  SEARCH RETURNS THE RIGHT ANSWER ABOUT THE STRING AND THE WRONG ANSWER ABOUT THE
  CAPABILITY, BECAUSE THE CALL CHAIN RUNS THROUGH A LIBRARY THE CALLER NEVER
  NAMES.** Every other member of this family is a match that went wrong — an
  unescaped `.`, a star-list numeric collision, `DISTORT_` being a suffix of
  `undistort_`, casing in both directions, zsh's `:s` eating a ref, prose wrapped
  across a line, a rounded figure, brace notation. **This one matches correctly and
  the correct match is still a false negative about the question being asked.**
  MEASURED on a route-bearing question: Montage's `montageProject.c` names NO
  distortion function anywhere, so grepping Montage's own source for `pix2foc`
  returns **ZERO** — while the capability is in use, because the chain runs
  `wcsinit`→`distortinit` and `pix2wcs`→`pix2foc` inside Mink's `libwcs`. A session
  checking the obvious way gets a confident negative and closes a route.
  **IT CANNOT BE FIXED BY BETTER MATCHING — no casing rule, no window, no
  brace-expansion reaches it. The only instrument that answers it is READING THE
  CALL CHAIN**, and the tell that you need to is a negative about a CAPABILITY drawn
  from a search for a SYMBOL.
  **AND THE ORDINARY CASING TRAP FIRED INSIDE THE SAME UNIT, WHILE THAT ONE WAS
  BEING REPORTED:** a case-sensitive grep for `DISTORT` in `montageProjectPP.c`
  returns nothing while `Initialize_TwoPlane_BothDistort` is in the file. Both
  directions of the family, one file, one session.
  (Attribution: the framing is the historian's, the source reads the oracle's. n=1 —
  do not compute a rate from it, and note the finding surfaced because someone was
  working the adjacent question, not because anyone was looking for this class.)

- **A WRAPPER SILENTLY CHANGES THE SUBJECT WHEN THE COMMAND IS A SHELL FUNCTION,
  AND THE VARIANT THAT RETURNS PLAUSIBLE NUMBERS IS WORSE THAN THE ONE THAT RETURNS
  NOTHING.** MEASURED. `grep` in an agent's interactive shell is not the rig's grep:
  the Claude Code shell snapshot shadows it — its own comment reads *"Shadow
  find/grep with embedded bfs/ugrep"* — with
  `ARGV0=ugrep "$CLAUDE_CODE_EXECPATH" -G --ignore-files --hidden -I --exclude-dir=.git …`.
  **`timeout`, `time`, `env`, `xargs`, `nice` and `strace` exec a BINARY and bypass
  the function**, so a wrapped probe and a bare one run different programs on the
  same command string:
  `grep` → **ugrep 7.5.0**; `/usr/bin/grep`, `timeout … grep` and
  `env -i /bin/sh -c grep` → **GNU grep 3.12**.
  **That one fact produced FOUR write-ups of a single search failure, three of them
  wrong**, across three sessions: a "silent zero" that would not reproduce (it does,
  on ugrep — `rc=2 exceeds complexity limits`, 5 stderr lines, on a two-range
  window); an "intermittent, load-correlated" error (**deterministic at 15-min
  loadavg 0.91 and 0.68**, and simply absent on GNU grep); and a `-c` that appeared
  to change meaning (ugrep `-oEc` **12** matches, ugrep `-Ec` **3** lines,
  `/usr/bin/grep -oEc` **3** lines even under `-o`).
  **THE SAME MECHANISM FIRED TWICE IN ONE DAY WITH OPPOSITE SYMPTOMS**, which is
  what makes the plausible-number case the dangerous one: `/usr/bin/time siril_cli …`
  could not run a shell function at all and returned **empty output, nearly read as
  a measurement**; `timeout grep …` ran a different program and returned **clean
  numbers, read as the same measurement**.
  **REPEATS DO NOT SAVE YOU — repeats of the wrong program are a precise wrong
  answer**, and a 3-repeat ladder taken through `timeout` was published as the
  evidence for withdrawing a correct finding.
  **THE RULE: `type <cmd>` before wrapping anything, and in a cross-session
  comparison name the PROGRAM and the QUANTITY beside the number.** Two sessions
  both said "grep" and meant different programs, so each correctly deferred to the
  other's contradicting measurement and BOTH landed wrong — deferring to a peer's
  measurement over your own inference is normally right, and fails only when the
  instruments differ invisibly. Same class as `bgnoise` not being `bg`, one level up.
  **SCOPE THAT OUTLIVES THE INCIDENT: this repo's shipped scripts and guards get GNU
  grep 3.12, never ugrep** (`env -i /bin/sh -c grep`), so nothing concluded from an
  interactive `grep` describes how a shipped script behaves.
  **And the agent's grep is `git grep`-shaped, which is mostly CORRECT here:** `-G`
  (BRE, so `{n,m}` needs `-E`/`-P`) plus `--ignore-files`. Over `*.md` — agent
  **25**, `/usr/bin/grep` **27**, `git ls-files '*.md'` **25**, the agent's set
  *identical* to the tracked set, the whole gap being two untracked judge notes
  under the gitignored output root. For RECORD sweeps that scope is safer than GNU
  grep, which can lift a stale claim out of an untracked scratch file and present it
  as the tree's position. **The residual has a DIRECTION worth carrying: a
  declaration inside a gitignored path is HIDDEN from interactive ugrep and VISIBLE
  to a guard's GNU grep, so it surfaces as a guard failure nobody can reproduce by
  hand.** `check_removal_conditions.sh` was built interactively and runs under bash;
  re-measured on both programs it reads **28 files each, `comm` empty in both
  directions** — unaffected, by luck rather than design.
- **A SEARCH THAT DID NOT RUN HAS THREE MODES, AND THE EXIT CODE IS THE
  DISCRIMINATOR — re-homed as its own entry after a role doc kept the PROHIBITION
  and deleted the DETECTOR:** *"never report a negative from a structurally-impossible
  view"* survived a cut while every description of what makes a view structurally
  impossible went to zero tracked files.
  **MODE 1 — AN EXACT-COUNT WINDOW WIDER THAN THE FILE'S LONGEST LINE CANNOT MATCH,
  AND IT EXITS CLEAN.** No error, empty stdout, `rc=1` — indistinguishable from a
  searched null, and it reads identically on ugrep and GNU grep:
```
  awk longest line          docs/dead-ends.md 108   TOOLS.md 6611   BACKLOG.md 3165
  .{60}darktable.{110}      docs/dead-ends.md ->  0  rc=1   STRUCTURALLY IMPOSSIBLE
  .{20}darktable.{40}       docs/dead-ends.md ->  3  rc=0   the claims ARE there
```
  **Measure the width with one `awk '{if(length>m)m=length}END{print m}'` before
  choosing a window — never from the file's reputation.** The registry is wrapped
  prose; the toolkit and the register are where the long cells are.
  **MODE 2 — two range quantifiers exceed ugrep's complexity limit, deterministically
  (`rc=2`, five stderr lines), while GNU grep runs the same pattern fine.** `grep -P`
  dodges it by using PCRE2 instead of ugrep's own engine. A separate width effect on
  GNU grep is a **HANG, not an error** — superlinear in window width, `.{0,1000}`
  9.9 s → `.{0,1600}` 39.3 s → `.{0,2000}` killed at 40 s with no output and no
  message, so a timeout inside a pipeline reads as a null.
  **MODE 3 — the one that returns a NUMBER, so nothing prompts a re-check.**
  `2>&1 | wc -l` reported **"5 matches"** where there were none — those being MODE 2's
  five stderr lines counted as data.
  **THE DISCRIMINATOR IS THE EXIT CODE, which is why no width threshold is needed:**
  `rc=0` empty is a real no-match; `rc=1` empty may be MODE 1's structural zero;
  **`rc=2` is a search that did not run.**
  **THE SAFE FORM: ONE range quantifier on the TRAILING side —
  `grep -oE "PATTERN.{0,200}"` — positive-controlled, with the PROGRAM and the
  QUANTITY named, and stderr never merged into a count.**
- **THE PASTE RULE IS NOT ABOUT NUMSTAT — that is the instrument it was first
  written about, not its scope.** `CLAUDE.md` states it as *"PASTE the measured
  numstat into the commit — never a description of it"* and *"a check whose output
  is paraphrased is a check that did not run"*, so it reads as a rule about one
  command. **MEASURED, in the commit that re-homed the three-modes entry above: the numstat was
  pasted correctly and the destination check three lines below it was PARAPHRASED** —
  *"verified homed: all six strings now 1 file"*, when the before-check and the
  after-check had been run on **different strings** (`NEVER MERGE STDERR` was
  silently swapped for `MODE 3`) and one of the six was in **zero** files. The
  content was genuinely re-homed; only the sentence claiming to prove it was wrong.
  **A verification sentence that reads as evidence and is not — the same shape as a
  null instrument quoted as corroboration, one commit apart, by the same author.**
  **THE RULE: paste the literal command and its literal output for EVERY check a
  later reader would otherwise have to re-derive, per block rather than as one
  summary line over all of them.** A per-block paste catches a swapped search string
  on sight; a summary line cannot, because it is written from memory of what was
  fixed rather than from a re-run.
  **AND A CORRECTLY PASTED NUMSTAT DOES NOT COVER A DESTRUCTIVE CUT, BECAUSE AN
  AGGREGATE SAYS NOTHING ABOUT WHICH LINES WENT.** MEASURED, and the instance sat
  in the tree for a day: `c1a20d3` pasted `37 5 docs/dead-ends.md` accurately and
  one of those five deletions was the BULLET AND TITLE of an unrelated entry —
  *"A LINEAR REGRESSOR AVERAGES A SIGN-FLIPPING PATTERN TO ZERO, AND THAT NULL IS"*
  — leaving its continuation orphaned mid-paragraph inside the preceding entry
  about Siril's top-down frame, so two unrelated subjects read as one. **The
  numstat check FIRED and PASSED; the count was right and the content was
  destroyed.** Same class as the cut that kept a prohibition and deleted its
  detector, nine minutes apart, neither caught by the rule written for it.
  **THE RULE THIS ADDS: for a DELETION, read the `-` lines, not the count.**
  `git diff -- <file> | grep '^-'` is the check; the count test cannot reach it.
  **THE CHEAP DETECTOR — AND IT HAS THREE FAILURE MODES, NOT THE ONE FIRST
  RECORDED HERE. Read all three before running it.** A block-parity scan for an odd
  bold-marker count over the ~294 top-level bullets in the seven record files did
  find this cut. Measured at a PINNED commit, three variants of the same scan:

      naive        (count markers per block)                294 bullets, 1 odd
      line-scoped  (strip fenced + inline code per LINE)    294 bullets, 1 odd
      CORRECT      (strip fenced + inline code, MULTILINE)  294 bullets, 0 odd

  **Both flags are FALSE POSITIVES and the true answer is zero.**
  **MODE 1 — THE DETECTOR MATCHES ITS OWN DOCUMENTATION.** The sentence above
  quotes a bold marker as inline code; a naive counter counts it, so the block
  goes odd. The instrument went RED on the sentence describing the instrument,
  minutes after it was written. Fourth instance of the self-match family here,
  after `pgrep` in its own argv, `check_removal_conditions`, and
  `check_prompt_scope`'s head-window rule (that guard is since REMOVED with the
  role docs it policed; the mechanism it illustrates is not). **The original sweep was clean only
  because no record file yet contained a quoted marker — documenting the detector
  is what broke it.**
  **MODE 2 — A LINE-SCOPED CODE STRIPPER MIS-PAIRS BACKTICKS ACROSS A WRAP**, eats
  a real bold closer, and manufactures an imbalance in clean prose (the live
  example was a `TOOLS.md` code span wrapping a line; its line ref is dropped
  as stale — line numbers do not survive edits). **Note the direction: mode 2
  is produced BY the fix for mode 1.**
  **THE CORRECT FORM: strip fenced blocks, then strip inline code spans ALLOWING
  NEWLINES INSIDE THE SPAN, then count per block.**
  **AND THE FALSE-NEGATIVE BOUND STILL STANDS:** it catches a cut that UNBALANCES
  a marker and is blind to one removing a balanced span, so it is not a detector
  for the class — it caught this instance by how this instance happened to fail.
  **The first version of this paragraph stated that bound and NEITHER false
  positive, which is the error this entry exists to teach: a positive reported
  from an instrument its author had not falsified.** Corrected by the author.
- **IN zsh, A `<rev>:<path>` PATHSPEC BUILT FROM A SHELL PARAMETER IS SILENTLY
  MANGLED, AND DOUBLE-QUOTING DOES NOT DEFEND — ONLY `${REV}` DOES. THE FAILURE
  MODE THAT MATTERS IS NOT THE ERROR, IT IS THE ONE THAT RETURNS PLAUSIBLE
  NUMBERS FOR THE WRONG FILES.** This rig's agent shells are zsh 5.9
  (`$0=/usr/bin/zsh`, `BASH_VERSION` unset), so this fires in ordinary use and
  NOT in the repo's shipped `#!/usr/bin/env bash` scripts. zsh applies history-style
  modifiers to `$name:…`, and the path's first character selects one. MEASURED,
  one knob, synthetic `R=abc`:

      $R:scripts/x   bad substitution   LOUD — but see the correction below
      $R:web/x       b/x                SILENT — the ref is GONE
      $R:lib/x       abcib/x            SILENT — `:l` fired
      $R:qa/x        abca/x             SILENT — `:q` fired
      $R:upper/x     ABCpper/x          SILENT — `:u` fired, and it UPCASED the value
      $R:hd/x        .d/x               SILENT — `:h` fired
      $R:docs/x      abc:docs/x         safe (`d` is not a modifier letter)
      $R:README.md   abc:README.md      safe

  **CORRECTION TO THE LINE ABOVE, AND IT IS THE HALF THAT MAKES THIS PREDICTABLE:
  `scripts/` IS NOT RELIABLY THE LOUD ONE. It announces itself on FEWER THAN HALF
  of this repo's own paths.** `:s` is the SUBSTITUTION modifier and it takes the
  NEXT CHARACTER as its delimiter — for `scripts/…` that delimiter is `c`. What
  happens then depends on **where the remaining `c`s are in the rest of the path**:
  with no second `c` the substitution is unterminated and zsh shouts; WITH one it
  parses as a no-op, the value survives intact, and the path is simply GONE.
  Pre-registered as a prediction and tested 4/4, two each way — and the two halves
  differ by ONE LETTER IN A DIRECTORY NAME:

      scripts/lib/route.py            no later c   -> bad substitution   LOUD
      scripts/qa/anomaly_audit.py     no later c   -> bad substitution   LOUD
      scripts/stack/build_sky_flat.sh c in "sta[c]k" -> the bare rev      SILENT
      scripts/calibrate/solve_field.py c in "cali…"  -> the bare rev      SILENT

  **THREE OUTCOMES, NOT TWO — counted by EVALUATING the expansion for all 113
  tracked `scripts/` paths, reproduced independently by two sessions to the file:**

      A  bad substitution                     51  45%   LOUD, you stop
      B  bare rev, pathspec VANISHES          37  32%   the dangerous one
      C  mangled rev (`<sha>overage.py`)      25  22%   loud, but the message
                                                        names a path you never typed

  **So B is a third of this repo's script paths, and B is where the number comes
  back real, correct, and about the wrong scope.** That is the registered MODE 3 —
  *the one that returns a NUMBER, so nothing prompts a re-check* — reached with no
  range quantifier, no stderr merge and no `wc -l`, just a colon.
  **THE FIRST VERSION OF THIS ENTRY CLAIMED `scripts/` WAS SELF-ANNOUNCING, AND A
  READER WHO TESTED IT ON `route.py` WOULD HAVE CONFIRMED THAT AND STOPPED** — a
  positive from the 45% that happens to be loud, generalised over the 32% that is
  not. Corrected by the contributor of the original finding, whose own binary split
  ("has a second `c`") was also too coarse: it predicts NOT-LOUD, and C is not
  silent.

  **THE DEFENCE IS BRACES, NOT QUOTES**, and the obvious fix is the wrong one —
  parameter expansion happens INSIDE double quotes, so the modifier still fires:

      git cat-file -p $R:scripts/lib/route.py       -> bad substitution
      git cat-file -p "$R:scripts/lib/route.py"     -> bad substitution
      git cat-file -p "${R}:scripts/lib/route.py"   -> #!/usr/bin/env python3 …

  **THE EXPENSIVE DIRECTION, MEASURED HERE:** a mangled pathspec does not
  necessarily fail — git can drop it and search the WHOLE TREE at that rev instead.
  `git grep -c 'desky' $R:scripts/stack/build_sky_flat.sh` returned
  **`BACKLOG.md:6` and `experiments.jsonl:2`** — real counts, for files nobody
  asked about — while the true count in the named file is **15 lines matching `desky`** — and
  state the string, because the same file is elsewhere recorded at **9**, which is
  `--desky`, a strict subset. Two sessions reported 9 and 15 for "the same" count
  and both were right; that is the seventh quantity to move here in a day on an
  unstated filter. That is MODE 3 of
  the registered search-failure set (*the one that returns a NUMBER, so nothing
  prompts a re-check*) reached by a new mechanism, and a second session hit the
  zero-valued version of it in the same hour, reading `--desky: 0` for a file
  carrying 9 and nearly reporting live code as deleted.
  **THE RULE: write `"${REV}:path"`, and treat any `<rev>:<path>` result as
  suspect until the ref is visibly present in the output.** Same family as the
  shell-function shadow above — the instrument changed and the numbers stayed
  plausible — and it was found only because the advice *"quote the ref-path"* was
  itself tested rather than adopted, by its own author, one message after issuing it.
  **RE-MEASURED at `614ad33` over the current tracked `scripts/` paths — an
  independent third reproduction of the classifier: 115 paths, A=51 B=37 C=27.**
  A and B are IDENTICAL to the 113-path census (the two paths added since both
  classify C), so B remains a third of this repo's script paths (32%).
- **`git log --oneline` CARRIES NO TIME, SO IT CANNOT ORDER A COMMIT AGAINST
  ANYTHING THAT IS NOT A COMMIT — and the failure is not the ordering, which was
  correct.** MEASURED: a session ran `git log --oneline -5`, saw a commit at the
  top, and concluded that the work had been done AFTER a boot message and a gate —
  then told the owner a peer *"did the work and jumped the gate anyway"*, and
  escalated it to *"wrong in the direction that made the peer look better"*. The
  peer had stated the true sequence four times, unprompted, against its own
  interest. Re-checked with `%ad`, every *"already landed"* claim was true when made.
  **THE STATED MECHANISM WAS ALSO WRONG, AND IT MATTERS BECAUSE IT MISDIRECTS THE
  FIX.** The confession named *"`--oneline` orders by topology, not chronology"*.
  Git's own documentation says the default IS reverse chronological, and over the
  last 60 commits here **zero are out of timestamp order** — this history is linear
  and the displayed ORDER was right. **So `--topo-order` is not the remedy and
  reaching for it would leave the defect live.** The real defect: **position in a
  commit list establishes order among COMMITS and says nothing about a commit's
  position relative to an event that is not in the log** — a message, a boot, an
  approval. The list omits time entirely; the reader supplies it and does not
  notice supplying it. Same family as the truncated view above: **the display
  presents as the object, so what it does not carry is not experienced as missing.**
  **THE RULE: to place a commit against a non-commit event, print the time —
  `git log --format='%h %ad' --date=format:'%H:%M:%S'` — and get the event's time
  from its own source.** A `--oneline` list is evidence of sequence among commits
  and of nothing else.
  **AND THE SECOND LAYER COST MORE THAN THE FIRST: the inference was reported to a
  third party AS THE PEER'S OWN FRAMING** — *"I took it from the PM's account
  instead of the timestamps"* — when the peer's account had said the opposite.
  **An inference attributed to the person it indicts is unfalsifiable by them
  without the transcript**, and it was made in the message where its author was
  claiming the verifier role. **State whose inference it is, especially when it is
  adverse: "I concluded X from Y" and "they said X" are different claims and only
  one of them is checkable.**
  **AND THE HEDGE MUST NOT WEAKEN AS THE CLAIM BECOMES ADVERSE — n=1, and it is the
  INVERSION that makes it worth a line.** MEASURED: one session reported the same
  evidence to two peers within minutes, labelling the authorship inference *"an
  inference and I will label it as one"* to the UNINVOLVED party and stating it flat
  — *"these are your probes"* — to the party it ACCUSED. The hedge went to the
  reader who could not act on it; the assertion went to the one being blamed; and
  the attribution was wrong. **An adverse claim needs MORE hedging than a neutral
  observation, not less.** The negative was provable (the files demonstrably were
  not the reporter's) and only the positive was inference — reporting the provable
  half and holding the other is the whole of the fix.
  **AND THE GENERAL FORM, which outlives the incident: A SELF-AUDIT RUN ON THE
  INSTRUMENT THAT FAILED INHERITS ITS FAILURE.** The confession above was prompt,
  unforced and correctly owned — and it diagnosed itself with the same reasoning
  that produced the error, which is how it arrived at a mechanism that was **tidy
  and false**. One command with `%ad` would have settled it and was not reached for,
  **because the author was explaining rather than measuring.** Tidier is the tell:
  three separate corrections in one day were each replaced by a neater story than
  the truth, and in every case the neatness is what stopped the next person
  checking. **When auditing your own error, change instruments — the one you used
  is the one under suspicion.**
- **REACHABILITY IS NOT GREPPABLE IN THIS TREE — SCREEN WIDE, THEN READ EVERY CALL
  SITE. And note the DIRECTION of the error: an under-reporting reachability check
  reads as "everything is reachable", which is the answer that ends the search.**
  MEASURED over a sweep of **108 tracked `.sh`/`.py`** (untracked scratch excluded —
  the question is what a CLONE reaches):
  - **screen 1, basename appearing anywhere in tracked text → 4 candidates.
    UNDER-reported**, because a mention in a comment or a record counts as a hit.
  - **screen 2, an invocation-context regex (`./`, `bash`, `python3`, `$REPO/`,
    `$(dirname "$0")/`) → 33 candidates. OVER-reported by 32.**
  - **reading every call site → 1 delivery gap + 3 unclear.** Neither screen was
    right; the resolution was reading, and the two screens disagreed by 29.

  **Four ways a real invocation escapes a regex, each measured here — the list is
  the useful part, because any one of them turns an orphan sweep into a false
  all-clear:**
  1. **Assembled with `os.path.join`** — `lens_preflight.py` builds
     `os.path.join(STYLE_DIR, "verify_lens_card.py")`. Same mechanism as the
     `grid_ramp` path split across two source lines: **the literal path never
     appears in the file, so every path-anchored grep is blind to it.**
  2. **Assembled with `$(dirname "$0")/`** — `x86_bootstrap.sh` invokes
     `install_astromatic.sh` this way three times, and a literal-path grep reports
     it orphaned. **This one flipped a live finding to false in both directions:**
     the sweep that declared it an orphan was wrong, and so was the re-check that
     would have "confirmed" it with the same instrument.
  3. **Inside a string literal** — `install_cosmicclarity.sh` is named in a
     `log "…"` operator instruction, which is a real and correct delivery path.
  4. **Inside a data structure** — `run_session_chain.sh` appears in a lambda's
     list at `web/serve.py`.

  **And one category that is not an orphan at all: a LIBRARY.** `siril_run.py`,
  `cp_coverage.py` and `flat_differential_report.py` are `import`ed and never
  invoked. A reachability sweep that does not separate modules from entry points
  reports its own dependencies as dead code.

  **THE FIFTH ESCAPE IS THE ONE THAT WOULD DELETE A LIVE TOOL, AND NEITHER A CODE
  SEARCH NOR A DOC SEARCH REACHES IT: a script can be evidenced ONLY BY ITS
  OUTPUT.** `scripts/ingest/{fetch_session,link_heartbeat,remote_publish}.sh` were
  INVOKED by no code and appeared in no `.md` WHEN THIS ENTRY WAS WRITTEN — and the
  tracked records settle it: **9 `ingest_work/ingest.json` across two nights, all 9
  naming `remote_publish.sh` as the hash producer, covering 3,591 frames with
  `verified_bad = 0`.** That evidence is unchanged and re-measured: still 9 of 9.
  **THE SUPPORTING NEGATIVE HAS SINCE ROTTED AND THE FINDING HAS NOT.** `README.md`
  carries a repo-map row for each of the three (landed 49.7 h after this entry), so
  the `.md` half is now FALSE and the closing *"undocumented — a DOCUMENTATION gap"*
  is false with it: the gap this entry named has been CLOSED, and the entry stood 13
  days without knowing. **Scope the surviving half precisely — it is INVOCATION, not
  reference:** re-measured, 0 invocation-shaped references to any of the three exist
  outside `scripts/ingest/` itself, while `fetch_session.sh` names
  `remote_publish.sh` at three sites as operator prose and a record string — which
  escape #3 above counts as a real delivery path. (Both halves re-verified at
  `614ad33`: 9 of 9 records name `remote_publish.sh`, and 0 invocation-shaped
  references exist outside `scripts/ingest/` — the re-verifying sweep itself
  first reported 8, all of them its own path-prefix filter failing to match, a
  live instance of the plausible-number class this file records.) **The durable lesson is the
  method, not the negative:** search the records before classifying anything as
  dead. A rot at HOUR scale is caught by the session that caused it; this one ran
  for DAYS and was caught by nobody, which is the case a `last checked` date cannot
  reach.
  **So the sweep's question "what invokes this" is the wrong one on its own; the
  completeness question is "what does this leave behind".** Search the records
  before classifying anything as dead.
  **Corollary met in the same records — READ THE FIELD, NOT THE PROSE BESIDE IT.**
  Those records carry a `_note` that opens *"source-verified: hashes computed at
  the source by remote_publish.sh…"*, which read as contradicting a since-retired session
  report's *"local-hash verified only"*. It does not: the `_note` is a two-term GLOSSARY
  whose first sentence defines the term that does NOT apply, and the actual
  `integrity` field reads **`transfer-verified` in all 9**. A glossary that leads
  with the inapplicable term invites the misread, and the field is the datum.
  **Classify before reporting — DELIVERY GAP (meant to run, nothing reaches it),
  OPERATOR TOOL (run by hand by design, and say where that is documented), DEAD,
  or UNCLEAR. "Unclear" is a finding**, and it is the honest verdict when the
  answer is an owner's decision rather than a measurement — **but exhaust the
  OUTPUT search before settling on it: the ingest trio above was filed UNCLEAR on
  a code-and-doc search and resolved to LIVE by one look at the records.**
- **THE REPO'S MOST PERSISTENT DEFECT: A CHECK THAT CANNOT FAIL — AND THE THING
  MEANT TO PROVE IT COULD FAIL IS USUALLY DEFECTIVE TOO. VERIFY BY EXECUTING:
  break the mechanism, watch the assertion go RED, restore.** Reasoning about a
  fixture's construction is not verification; it has failed three times in a
  row, each time for a different reason, each time looking green:
  1. `grep -oE 'Found [0-9]+ star' … || echo 0` — the regex never matched Siril
     1.4.4's actual wording, so the fallback supplied 0 unconditionally.
  2. The uniform lens card — warping a uniform field yields a uniform field, so
     corner==centre passes whether vignetting was stripped OR the module never
     fired; needed a GRID positive control that MUST differ (full entry:
     `registration-distortion.md`, the darktable lens STYLE entry).
  3. `lens_preflight.check_pinned_model`'s mutation test, TWICE — a counted-less
     `str.replace` moved the live element AND the decoy together (a mutation
     that changes every copy cannot distinguish "reads the right copy" from
     "reads any copy"), and its replacement's decoy was written `focal=70` where
     the scanner requires `focal="70"`, so the fixture contained no decoy at all
     and passed with masking disabled.
  The common shape is not "bad metric": **the falsification step was argued
  rather than run.** The executable form, shipped in
  `lens_preflight.py --selftest`: neutralise the mechanism in-process (which is
  why `live()` is module-level and not a closure), assert the incident
  REPRODUCES, restore, assert it is caught again. A test that cannot be made to
  fail on demand is decoration. Corollary for a fixture with a decoy: assert the
  decoy MATCHES the scanner's own pattern before trusting any result built on it
  (measured: 2 pattern matches in the raw block, 1 after masking).
- **TWO KERNEL BUGS IN THE SAME SYNTHETIC-TRAIL FIXTURE, BOTH FOUND BY A SELFTEST
  THAT FAILED FIRST** (fixture: `datasets/aug06/corner_work/kappa_transfer.py`).
  The fixture deposits a trail of known length `L` and the
  calibration recovers it from a second-moment shape, so a bias in the DEPOSIT is
  indistinguishable from a bias in the estimator — which is why the selftest
  asserts the ANALYTIC value rather than self-consistency.
  - **Endpoint-sampled `linspace` inflates the segment variance by `(N+1)/(N-1)`.**
    Sampling a segment at `N` points INCLUDING both endpoints is not a uniform
    draw from it — the ends are over-weighted. A uniform segment's variance is
    `L^2/12`; the endpoint-sampled deposit is `L^2/12 * (N+1)/(N-1)`, so at N=11
    it is 20% wide and at N=101 still 2%. The fix is MIDPOINT sampling, not more
    samples: the bias falls as `1/N` but never reaches zero, so "use enough
    points" would have hidden it under the noise floor rather than removed it.
  - **Bilinear deposit adds `h^2/6` to ONE axis, where it does NOT cancel.**
    Splitting each sample across its four neighbouring pixels convolves the
    deposit with the bilinear kernel, whose variance is `h^2/6` per axis
    (`h` = pixel pitch). On an ISOTROPIC quantity that term is common-mode and
    drops out — which is why it survived review. The calibration's observable is
    `major^2 - minor^2`, a DIFFERENCE of axes, and the trail lies along one of
    them, so the term lands on the major axis alone and survives the subtraction
    as a pure additive bias in the very quantity being fitted.
  **Neither bug is visible in the fixture's own output** — a slightly-too-long
  trail still looks like a trail — and both would have propagated into the
  transfer coefficient as an unattributable few-percent error. General form:
  **a test that could not fail is decoration; a test that failed FIRST earned its
  place.** The corollary specific to synthetic fixtures: the generator and the
  estimator must each be checked against an ANALYTIC value, never against each
  other, because a shared discretisation error is invisible to round-tripping.
- **A RUNNING BASH SCRIPT IS A LIVE FILE, NOT A SNAPSHOT — never edit one that
  has an invocation in flight.** bash reads a script lazily and remembers a BYTE
  OFFSET, so inserting lines ABOVE the current execution point makes it resume
  mid-token and execute garbage. The recovery shape: kill the shells whose
  offsets are invalidated, LEAVE any child builder running (a separate process
  with its own unmodified file), and re-enter the chain from a clean read once
  it lands — built products skip, so the cost is zero. Check
  `pgrep -f <script>` before editing anything the chain drives.
- **A LOG-MESSAGE REGEX IS NOT A MEASUREMENT INTERFACE — parse the tool's
  structured output, and prove the tool RAN.** A validation gate read
  `grep -oE 'Found [0-9]+ star' … || echo 0` off Siril's `findstar` log; Siril
  1.4.4 actually prints **"Found N Gaussian profile stars in image"** — the
  profile word sits between the count and "stars" — so the regex never matched
  and the fallback supplied a 0 **unconditionally**. A gate that cannot fail,
  and two flat records plus a ledger entry carried a speck count that was never
  measured. (Re-measured from the tool's own `-out=` list: 0–1 specks on every
  july23 flat, de-skied and control alike — the conclusion had been right by
  luck.) The wording is also version- AND parameter-dependent (the profile word
  changes with `setfindstar -profile=`), so it was never a stable interface.
  **Three `findstar` behaviours a replacement must respect** (probed on-rig,
  1.4.4): (1) with zero stars it writes **NO list file at all** — which is a
  flat's IDEAL result, so a missing list must read as 0, never as an error;
  (2) it still exits **0** in that case, so `set -e` on the run is a valid
  failure check but tells you nothing about the count; (3) its
  `Candidates for stars: N` line IS printed whether or not any candidate
  survives the PSF gate, so that line — not the count — is the positive control
  proving the measurement happened. Unrelated landmine found in the same probe:
  **`setfindstar -reset` returns exit 1** on success in 1.4.4, so an `.ssf`
  ending in it fails a `set -e` caller for no reason.
  **AND `findstar`'s DETECTION COUNT JITTERS ~0.3% BETWEEN IDENTICAL RUNS while the
  top-30 medians hold to the third decimal** — an instrument fact to carry, not a
  defect to chase. It bounds what a COUNT comparison can resolve and leaves a
  rank-matched shape comparison unaffected, which is the form this registry already
  requires for cross-level work (`star-shape-optics.md`, the detection-depth
  entry). (This entry is the jitter figure's sole home — its original record
  was retired.)
