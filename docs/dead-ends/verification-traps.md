# Verification traps — checks and search instruments that lie

Phase-2 file of the dead-ends registry split (`README.md` here holds the index
and dispositions; pre-compression forms live in git and in the live
`docs/dead-ends.md` until the merge). Entries are maintained IN PLACE.
Cross-references to sibling files are written as (`<file>.md`) pointers.

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
  **THE OPPOSITE DIRECTION IS ALSO LIVE: `pgrep` SAMPLES AN INSTANT, SO IT
  CANNOT REFUTE AN INTERVAL CLAIM.** The false NEGATIVE, and the one that
  closes an investigation early: a session `pgrep`ed for a competing run, saw
  none, and declared a concurrency race refuted — while the runner's own kept
  log carried `[siril_run] another Siril job holds the lock — waiting` on the
  exact path that then died. For any claim of the form "nothing else was
  running", the admissible evidence is a record covering the whole window — a
  lock line, a timestamped log, a pidfile with its lifetime — never a point
  observation.
- **NEVER REPORT A NEGATIVE FROM A TRUNCATED VIEW — THE DETECTOR CAN BE RIGHT
  AND THE DISPLAY THROW THE ANSWER AWAY.** A positive survives truncation (you
  saw the thing); a negative asserts absence over the whole object, and a
  window cannot support that. MEASURED twice on one route-closing claim, at
  opposite ends of the same length problem: a false sentence sat at byte
  offset 539 of a 4,640-character table cell — past where one sweep stopped
  reading, and past a second session's `| cut -c1-190`, which produced a
  confident negative from a CORRECT match. **Truncation does not merely
  WITHHOLD the evidence, it SUBSTITUTES a familiar one**: a window does not
  present as partial, it presents as the object, so the stopping rule fires on
  content that is real, relevant, and irrelevant to the question. **A length
  limit added for readability is part of the instrument and inherits its
  verdict.** The cheap correct forms: `grep -c` for presence; `grep -o` with a
  TRAILING range window, `grep -oE "PATTERN.{0,200}"` (the three-modes entry
  below is why the window must be that shape); and state coverage as what was
  actually read.
  **`grep -c` IS NOT A SAFE FALLBACK WHEN THE QUESTION IS WHAT A SENTENCE
  ASSERTS**: a corrected record deliberately QUOTES the claim it retracts, so
  on a well-maintained tree a count of the string is guaranteed to mislead — a
  count answers presence, not assertion. Read the sentence.
  **Corollary for the records: a claim that cannot be found inside the cell
  that contains it is already lost — compress so that each claim survives as a
  separately greppable statement.**
- **AN INSTRUMENT THAT RETURNS A PLAUSIBLE ANSWER WHILE MEASURING NOTHING IS THE
  DOMINANT FAILURE MODE HERE, AND READING ITS OUTPUT NEVER CATCHES IT —
  RE-RUNNING A DIFFERENT WAY DOES.** Four in one session, each in a different
  instrument, none an error: a deletion filter refined for readability
  (`grep -E '^-[^-]'` to drop diff headers) that silently excluded every
  deleted markdown bullet — the exact class the check existed to protect; a
  shell probe that could not do what it claimed (`BASH_SOURCE` cannot be
  overridden inside `bash -c`, so every arm returned a real path, measuring
  nothing); a sweep structurally unable to see what it was asked (an omission
  sweep asked whether a reason had been STATED — it shows absence, never
  explanation); and a count right by two cancelling errors. **The common
  shape: no error and no implausible number — the output is exactly what a
  correct run would look like.** What reached all four was running the
  measurement a second way: a different instrument, an execution instead of a
  simulation, or the same query at a state known to be clean. **The control
  that makes it cheap: before believing an instrument reports a defect, run it
  on a case whose answer is already known.** (n=4, one session, surfaced from
  ordinary work — do not compute a rate.)
- **A SEARCH FOR A SYMBOL RETURNS THE RIGHT ANSWER ABOUT THE STRING AND THE
  WRONG ANSWER ABOUT THE CAPABILITY WHEN THE CALL CHAIN RUNS THROUGH A LIBRARY
  THE CALLER NEVER NAMES.** MEASURED on a route-bearing question: Montage's
  `montageProject.c` names no distortion function, so grepping Montage's own
  source for `pix2foc` returns ZERO — while the capability is in use, because
  the chain runs `wcsinit`→`distortinit` and `pix2wcs`→`pix2foc` inside Mink's
  `libwcs`. No casing rule, window, or brace-expansion reaches it; **the only
  instrument that answers a capability question is READING THE CALL CHAIN**,
  and the tell that you need to is a negative about a CAPABILITY drawn from a
  search for a SYMBOL. (The ordinary casing trap fired in the same codebase:
  case-sensitive `DISTORT` misses `Initialize_TwoPlane_BothDistort`. n=1 — do
  not compute a rate.)
- **A WRAPPER SILENTLY CHANGES THE SUBJECT WHEN THE COMMAND IS A SHELL FUNCTION,
  AND THE VARIANT THAT RETURNS PLAUSIBLE NUMBERS IS WORSE THAN THE ONE THAT
  RETURNS NOTHING.** `grep` in an agent's interactive shell is not the rig's
  grep: the Claude Code shell snapshot shadows it with ugrep
  (`ARGV0=ugrep … -G --ignore-files --hidden -I --exclude-dir=.git`), and
  **`timeout`, `time`, `env`, `xargs`, `nice` and `strace` exec a BINARY,
  bypassing the function** — so a wrapped probe and a bare one run different
  programs on the same command string: `grep` → ugrep 7.5.0; `/usr/bin/grep`,
  `timeout … grep`, `env -i /bin/sh -c grep` → GNU grep 3.12. Both symptom
  directions are live: `/usr/bin/time siril_cli …` cannot run a shell function
  at all and returns empty output that nearly reads as a measurement;
  `timeout grep …` runs a different program and returns clean numbers that
  read as the same measurement. **Repeats do not save you — repeats of the
  wrong program are a precise wrong answer.** THE RULE: `type <cmd>` before
  wrapping anything, and in a cross-session comparison name the PROGRAM and
  the QUANTITY beside the number — two sessions both said "grep", meant
  different programs, and both landed wrong by correctly deferring to each
  other.
  **SCOPE THAT OUTLIVES THE INCIDENT:** this repo's shipped scripts and guards
  get GNU grep 3.12, never ugrep (`env -i /bin/sh -c grep`), so nothing
  concluded from an interactive `grep` describes how a shipped script behaves.
  The agent's grep is `git grep`-shaped (`-G`, so `{n,m}` needs `-E`/`-P`;
  `--ignore-files`) — for RECORD sweeps that scope is safer than GNU grep,
  which can lift a stale claim out of an untracked scratch file; the residual
  DIRECTION worth carrying is that a declaration inside a gitignored path is
  HIDDEN from interactive ugrep and VISIBLE to a guard's GNU grep, so it
  surfaces as a guard failure nobody can reproduce by hand.
- **A SEARCH THAT DID NOT RUN HAS THREE MODES, AND THE EXIT CODE IS THE
  DISCRIMINATOR** — the detector behind the prohibition *"never report a
  negative from a structurally-impossible view"*.
  **MODE 1 — an exact-count window wider than the file's longest line cannot
  match, and it exits clean.** No error, empty stdout, `rc=1` —
  indistinguishable from a searched null, identical on ugrep and GNU grep:
```
  awk longest line          docs/dead-ends.md 108   TOOLS.md 6611   BACKLOG.md 3165
  .{60}darktable.{110}      docs/dead-ends.md ->  0  rc=1   STRUCTURALLY IMPOSSIBLE
  .{20}darktable.{40}       docs/dead-ends.md ->  3  rc=0   the claims ARE there
```
  **Measure the width first — `awk '{if(length>m)m=length}END{print m}'` —
  never from the file's reputation.** The registry is wrapped prose; the
  toolkit and the register are where the long cells are.
  **MODE 2 — two range quantifiers exceed ugrep's complexity limit,
  deterministically** (`rc=2`, five stderr lines) while GNU grep runs the same
  pattern fine (`grep -P` dodges it via PCRE2). A separate width effect on GNU
  grep is a **HANG, not an error** — superlinear in window width,
  `.{0,2000}` killed at 40 s with no output — so a timeout inside a pipeline
  reads as a null.
  **MODE 3 — the one that returns a NUMBER, so nothing prompts a re-check:**
  `2>&1 | wc -l` reported **"5 matches"** where there were none — MODE 2's five
  stderr lines counted as data.
  **THE DISCRIMINATOR IS THE EXIT CODE**, which is why no width threshold is
  needed: `rc=0` empty is a real no-match; `rc=1` empty may be MODE 1's
  structural zero; **`rc=2` is a search that did not run.**
  **THE SAFE FORM: ONE range quantifier on the TRAILING side —
  `grep -oE "PATTERN.{0,200}"` — positive-controlled, with the PROGRAM and the
  QUANTITY named, and stderr never merged into a count.**
- **THE PASTE RULE IS NOT ABOUT NUMSTAT — that is the instrument it was first
  written about, not its scope.** Paste the literal command and its literal
  output for EVERY check a later reader would otherwise have to re-derive, per
  block rather than as one summary line over all of them. A per-block paste
  catches a swapped search string on sight; a summary line is written from
  memory of what was fixed, not from a re-run — MEASURED: a commit's
  *"verified homed: all six strings now 1 file"* had silently swapped one
  search string, and one of the six was in ZERO files; the content was right
  and the sentence claiming to prove it was not.
  **A CORRECTLY PASTED NUMSTAT DOES NOT COVER A DESTRUCTIVE CUT — an aggregate
  says nothing about which lines went.** MEASURED: `c1a20d3` pasted
  `37 5 docs/dead-ends.md` accurately while one of the five deletions was the
  bullet and TITLE of an unrelated entry, leaving its continuation orphaned
  inside the preceding entry — the count was right and the content was
  destroyed. **For a DELETION, read the `-` lines, not the count:**
  `git diff -- <file> | grep '^-'`.
  **The cheap block-parity detector (odd bold-marker count per block) has
  three failure modes — read them before running it:** (1) it matches its own
  documentation — a bold marker quoted as inline code flips a block odd (the
  self-match family: `pgrep` in its own argv, a guard matching its own
  detector string); (2) a line-scoped code stripper mis-pairs backticks across
  a wrapped code span and manufactures an imbalance in clean prose — the fix
  for mode 1 produces mode 2; (3) the false-negative bound — it catches a cut
  that UNBALANCES a marker and is blind to one removing a balanced span, so it
  is not a detector for the class. Correct form: strip fenced blocks, then
  strip inline code spans ALLOWING NEWLINES INSIDE THE SPAN, then count per
  block.
- **IN zsh, A `<rev>:<path>` PATHSPEC BUILT FROM A SHELL PARAMETER IS SILENTLY
  MANGLED, AND DOUBLE-QUOTING DOES NOT DEFEND — ONLY `${REV}` DOES. THE FAILURE
  MODE THAT MATTERS IS NOT THE ERROR, IT IS THE ONE THAT RETURNS PLAUSIBLE
  NUMBERS FOR THE WRONG FILES.** This rig's agent shells are zsh 5.9
  (`$0=/usr/bin/zsh`, `BASH_VERSION` unset), so this fires in ordinary use and
  NOT in the repo's shipped `#!/usr/bin/env bash` scripts. zsh applies
  history-style modifiers to `$name:…`, and the path's first character selects
  one. MEASURED, one knob, synthetic `R=abc`:

      $R:web/x       b/x                SILENT — the ref is GONE
      $R:lib/x       abcib/x            SILENT — `:l` fired
      $R:qa/x        abca/x             SILENT — `:q` fired
      $R:upper/x     ABCpper/x          SILENT — `:u` fired, and it UPCASED the value
      $R:hd/x        .d/x               SILENT — `:h` fired
      $R:docs/x      abc:docs/x         safe (`d` is not a modifier letter)
      $R:README.md   abc:README.md      safe

  **`scripts/` is NOT reliably the loud one.** `:s` is the SUBSTITUTION
  modifier and takes the NEXT character as its delimiter — for `scripts/…`
  that is `c` — and the outcome depends on where the remaining `c`s in the
  path are: with no second `c` the substitution is unterminated and zsh
  shouts; with one it parses as a no-op and the path is simply GONE. Three
  outcomes over the tracked `scripts/` paths — measured at 113 paths by two
  sessions, re-measured at `614ad33` by a third (115 paths, A=51 B=37 C=27:
  A and B identical, both added paths class C):

      A  bad substitution                     51  45%   LOUD, you stop
      B  bare rev, pathspec VANISHES          37  32%   the dangerous one
      C  mangled rev (`<sha>overage.py`)      25  22%   loud, but the message
                                                        names a path you never typed

  **So B is a third of this repo's script paths — the number comes back real,
  correct, and about the wrong scope** (MODE 3 of the three-modes entry,
  reached with just a colon). **THE DEFENCE IS BRACES, NOT QUOTES** — parameter
  expansion happens INSIDE double quotes, so the modifier still fires:

      git cat-file -p $R:scripts/lib/route.py       -> bad substitution
      git cat-file -p "$R:scripts/lib/route.py"     -> bad substitution
      git cat-file -p "${R}:scripts/lib/route.py"   -> #!/usr/bin/env python3 …

  **THE EXPENSIVE DIRECTION:** a mangled pathspec does not necessarily fail —
  git can drop it and search the WHOLE TREE at that rev instead, returning
  real counts for files nobody asked about. **THE RULE: write `"${REV}:path"`,
  and treat any `<rev>:<path>` result as suspect until the ref is visibly
  present in the output.**
- **`git log --oneline` CARRIES NO TIME, SO IT CANNOT ORDER A COMMIT AGAINST
  ANYTHING THAT IS NOT A COMMIT — and the failure is not the ordering, which
  is correct.** The default IS reverse chronological (this history measured
  linear: zero of 60 consecutive commits out of timestamp order), so
  `--topo-order` is not the remedy. **Position in a commit list establishes
  order among COMMITS and says nothing about a commit's position relative to
  an event that is not in the log** — a message, a boot, an approval. The list
  omits time entirely; the reader supplies it and does not notice supplying it
  (the truncated-view mechanism: the display presents as the object, so what
  it does not carry is not experienced as missing). MEASURED cost: an adverse
  wrong conclusion about a peer session, escalated to the owner, from a
  `git log --oneline -5` reading. **THE RULE: to place a commit against a
  non-commit event, print the time — `git log --format='%h %ad'
  --date=format:'%H:%M:%S'` — and get the event's time from its own source.**
  **Three reporting rules from the same incident:** state WHOSE inference an
  adverse claim is — "I concluded X from Y" and "they said X" are different
  claims and only one is checkable; an adverse claim needs MORE hedging than a
  neutral observation, not less (measured inversion: the hedge went to the
  uninvolved party, the flat assertion to the accused, and the attribution was
  wrong); and **a self-audit run on the instrument that failed inherits its
  failure** — when auditing your own error, change instruments, because a tidy
  mechanism reached by explaining rather than measuring is the tell.
- **REACHABILITY IS NOT GREPPABLE IN THIS TREE — SCREEN WIDE, THEN READ EVERY
  CALL SITE; an under-reporting reachability check reads as "everything is
  reachable", which is the answer that ends the search.** MEASURED over 108
  tracked `.sh`/`.py`: a basename screen returned 4 candidates
  (UNDER-reported — a mention in a comment or record counts as a hit), an
  invocation-context regex returned 33 (OVER-reported by 32), and reading
  every call site returned 1 delivery gap + 3 unclear — the screens disagreed
  by 29 and neither was right.
  **Five ways a real invocation escapes a regex, each measured here — any one
  turns an orphan sweep into a false all-clear:**
  1. assembled with `os.path.join` — the literal path never appears in the
     file, so every path-anchored grep is blind to it;
  2. assembled with `$(dirname "$0")/` — this one flipped a live finding to
     false in both directions: the sweep that declared the script orphaned was
     wrong, and so was any re-check with the same instrument;
  3. inside a string literal — an operator instruction in a `log "…"` is a
     real and correct delivery path;
  4. inside a data structure — a script named in a lambda's list
     (`web/serve.py`);
  5. **evidenced only by its OUTPUT** — the ingest trio
     (`scripts/ingest/{fetch_session,link_heartbeat,remote_publish}.sh`) was
     invoked by no code, and its tracked records settle it as LIVE: 9 of 9
     `ingest_work/ingest.json` name `remote_publish.sh` as the hash producer
     (re-verified at `614ad33`, with 0 invocation-shaped references outside
     `scripts/ingest/`). **Search the records before classifying anything as
     dead — the completeness question is "what does this leave behind", not
     only "what invokes this".**
  And one category that is not an orphan at all: a LIBRARY — an `import`ed
  module reported dead by an invocation sweep is the sweep reporting its own
  dependencies as dead code.
  **Classify before reporting — DELIVERY GAP (meant to run, nothing reaches
  it), OPERATOR TOOL (run by hand by design, and say where that is
  documented), DEAD, or UNCLEAR ("unclear" is a finding)** — and read the
  FIELD, not the prose beside it, when a record carries both. A finding about
  the tree is perishable by construction: it carries the commit it was
  measured at and is re-measured before citing.
- **THE REPO'S MOST PERSISTENT DEFECT: A CHECK THAT CANNOT FAIL — AND THE THING
  MEANT TO PROVE IT COULD FAIL IS USUALLY DEFECTIVE TOO. VERIFY BY EXECUTING:
  break the mechanism, watch the assertion go RED, restore.** Reasoning about
  a fixture's construction is not verification; it failed three consecutive
  times, each differently, each looking green: a log regex that never matched
  the tool's wording, so the fallback supplied the value unconditionally; a
  VACUOUS fixture (warping a uniform card yields a uniform card, so the check
  passes whether the treatment fired or not — it needed a grid positive
  control that MUST differ; full entry: `registration-distortion.md`, the
  darktable lens STYLE entry); and a mutation test that moved the live element
  and its decoy together — a mutation that changes every copy cannot
  distinguish "reads the right copy" from "reads any copy", and the
  replacement decoy did not even match the scanner's pattern. The executable
  form, shipped in `lens_preflight.py --selftest`: neutralise the mechanism
  in-process, assert the incident REPRODUCES, restore, assert it is caught
  again. **A test that cannot be made to fail on demand is decoration; a test
  that failed FIRST earned its place.** Two corollaries: assert a fixture's
  decoy MATCHES the scanner's own pattern before trusting results built on it;
  and a synthetic fixture's generator and estimator must each be checked
  against an ANALYTIC value, never against each other — a shared
  discretisation error is invisible to round-tripping (the measured instance's
  mechanism notes live at the implementation,
  `datasets/aug06/corner_work/kappa_transfer.py`).
- **A RUNNING BASH SCRIPT IS A LIVE FILE, NOT A SNAPSHOT — never edit one that
  has an invocation in flight.** bash reads a script lazily and remembers a BYTE
  OFFSET, so inserting lines ABOVE the current execution point makes it resume
  mid-token and execute garbage. The recovery shape: kill the shells whose
  offsets are invalidated, LEAVE any child builder running (a separate process
  with its own unmodified file), and re-enter the chain from a clean read once
  it lands — built products skip, so the cost is zero. Check
  `pgrep -f <script>` before editing anything the chain drives.
- **A LOG-MESSAGE REGEX IS NOT A MEASUREMENT INTERFACE — parse the tool's
  structured output, and prove the tool RAN.** A validation gate grepped
  Siril's `findstar` log for wording 1.4.4 does not print, so its `|| echo 0`
  fallback supplied the count unconditionally — a check that cannot fail; and
  the wording is version- AND parameter-dependent (the profile word changes
  with `setfindstar -profile=`), so it was never a stable interface. Read the
  tool's own `-out=` list instead.
  **Three `findstar` behaviours a consumer must respect** (probed on-rig,
  1.4.4): (1) with zero stars it writes **NO list file at all** — a flat's
  IDEAL result, so a missing list must read as 0, never as an error; (2) it
  still exits **0** in that case, so `set -e` on the run tells you nothing
  about the count; (3) its `Candidates for stars: N` line IS printed whether
  or not any candidate survives the PSF gate — that line, not the count, is
  the positive control proving the measurement happened. Landmine from the
  same probe: **`setfindstar -reset` returns exit 1 on success in 1.4.4**, so
  an `.ssf` ending in it fails a `set -e` caller for no reason.
  **`findstar`'s detection count jitters ~0.3% between identical runs while
  the top-30 medians hold to the third decimal** — an instrument fact, not a
  defect to chase: it bounds what a COUNT comparison can resolve and leaves a
  rank-matched shape comparison unaffected (`star-shape-optics.md`, the
  detection-depth entry). (This entry is the jitter figure's sole home.)
