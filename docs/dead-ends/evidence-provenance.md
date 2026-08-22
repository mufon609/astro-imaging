# Evidence, records, and provenance

Phase-1 split of `docs/dead-ends.md` (organize-only; the original file stays
the live registry until the merge is decided). Content below the marker is
VERBATIM from the original, so in-text "above"/"below"/section references may
point at entries now homed in a sibling file — `README.md` in this directory
carries the index, the assignment rule, and the block manifest that resolves
them. Do not edit below the marker while the refactor is in phase 1; the split
is re-derivable from the manifest and verified byte-identical by `split.py`.

<!-- == verbatim content from docs/dead-ends.md below this marker == -->
- **A BARE md5 OF FITS PIXEL DATA IS ONLY COMPARABLE WITHIN ONE BYTE-ORDER
  CONVENTION — quote a pixel-difference COUNT, never a digest, when the question
  is "did this product change?"** FITS stores pixels BIG-ENDIAN on disk, so
  `astropy` hands back a `>f4` array; hashing it AS READ and hashing it after any
  native-order cast (`<f4`, or an implicit `.astype`) give DIFFERENT digests for
  BIT-IDENTICAL pixels. MEASURED on one file, both ways, by two sessions
  independently: `armA` reads `7ea062fb217e6254` as-read and `91237e3e98fe7477`
  native; `armB` reads `15c99af99b5e0c6b` and `3a23c8725ec6d972`. Both sessions
  were right and the products were identical. **The failure mode is a
  false POSITIVE**: two readers comparing digests across that boundary conclude a
  product changed when nothing did — the expensive direction, because it sends a
  session chasing a corruption that does not exist. A difference COUNT
  (`(a != b).sum()` with `max|diff|`) is convention-free and is what the verdict
  should quote; if a digest is recorded at all, the convention is recorded beside
  it. Related trap, same family: **a whole-file `cmp` is the wrong test for "are
  these pixels the same"** — siril stamps its own creation `DATE` and the chain
  stamps `PIPEREV` (`git rev-parse --short HEAD`; what that couples across
  parallel sessions is a BINDING RULE in `CLAUDE.md`, not restated here), so two
  pixel-identical products always differ as FILES. The identity control here read "NOT byte-identical"
  while measuring 0 differing pixels of 69,359,745, max\|diff\| exactly 0. A check
  that fires spuriously trains the operator to bypass it, which is how a real
  failure gets waved through later.

**EVERY RECORD-SCHEMA CHANGE CREATES A PRE-CHANGE GENERATION INDISTINGUISHABLE
FROM A POST-CHANGE ONE UNLESS SOMETHING MARKS IT.** A CLASS, not an incident, and
it applies to every schema this repo has ever changed. **MEASURED twice in one day
in unrelated places:** `solve_field.py`'s hint-contradiction gate added
`hint_available` and `header_scale_arcsec_px` expressly so *"a later audit replays
it from the record instead of re-deriving the nominal"* — and they shipped WITH the
gate, so only **43 of 195** records carry them and **the one false solve the gate
exists for has none**. The mitigation postdated the case it was built to make
auditable. Separately, an error-model rename left every pre-rename record carrying
a neutrally-named SE no reader can attribute to a model.
**THE GENERAL MITIGATION, arrived at for a specific case:** label BOTH sides and
make the consumer REFUSE a mixed set. The error-model fix does exactly that — each
row declares its `error_model` and the resolver refuses rows that mix models or
omit the label, so a pre-change record fails LOUDLY rather than being silently
averaged with a post-change one. **A schema change without that leaves a silent
generation boundary; with it, the boundary is a hard stop.**
**COROLLARY THAT MOVES OTHER ITEMS' DISPOSITIONS: the record layer is not a
complete census of what was run.** MEASURED: **145 distinct solves on disk** against
a register claiming ~68 and a shipped script claiming 68 then 67, none
reconcilable. So any claim of the form "we measured N of these" carries an unstated
and demonstrably wrong denominator. **Read every such row as a SAMPLE, never as
COVERAGE, unless the census is stated and checkable.**

- **PREFER A CHECK WHOSE EVIDENCE IS READ FROM AN ARTIFACT OVER ONE A HUMAN
  TRANSCRIBES.** The registry already carries the negative — a check whose
  output is paraphrased is a check that did not run — and this is its
  constructive half. MEASURED in one session that was actively watching for it:
  a rule requiring a measured `git diff --numstat` to be pasted into a commit
  message was violated **four times by its own author**, three caught before
  push and one after, while the two checks that caught real defects the same
  day were both STRUCTURAL — a canvas comparison whose numbers came out of the
  FITS headers, and a diff of two generated `.ssf` files that already existed on
  disk. A transcriptive check fails at whatever rate humans copy numbers, and
  that rate is not zero even under attention. When a check must be
  transcriptive, that is a hook or a script waiting to be written, not a
  discipline problem.
  **AND THE CONVERSE, WHICH IS THE HALF THAT BITES: "PREFER THE ARTIFACT" IS A
  RULE FOR THE AUDITOR AND NOT A CONSOLATION FOR THE READER. THE ARTIFACT BEING
  RIGHT ONLY PROTECTS READERS WHO READ ARTIFACTS — AND A RECORD EXISTS PRECISELY
  FOR THE READERS WHO DO NOT.** MEASURED, and it is why this needs saying: in one
  evening FOUR findings took the form *"the record is wrong, the artifact is
  right"* — a solve record asserting RA 6.03/Dec −65.10 for a union whose header
  reads 310.62/+43.24; a registry closing a route the shipped chain runs by
  default; a `-weight` generalisation contradicted by the chain's own
  `WDESC="inverse-variance"`; and a homogenisation claim contradicted by a
  shipped guard. **Each was reported with the artifact as the reassurance, and
  each quietly assumed a reader who would open the artifact. That is backwards
  for a record's audience.** The correct artifact makes the defect INVISIBLE to
  its own author and leaves it fully operative on everyone who trusts the record —
  so a right artifact beside a wrong record is not a mitigated defect, it is a
  defect with its warning light disconnected. **Rank by who reads what: a wrong
  record with a right artifact is WORSE than a wrong record with a wrong artifact,
  because the second gets caught the first time anyone builds on it.**
  **AND THE SAME FAILURE APPLIES ONE LEVEL UP, TO RESULTS: a RESULT that was
  paraphrased is a result that was NOT RECORDED — and it survives longest when it
  flatters.** MEASURED: the headline of this repo's error-model finding was
  published, in a register row and in a shipped docstring, as *"χ²/dof 35.6 on
  bootstrap errors becomes ~1.1 on frame-based ones"*. Enumerating **every**
  `chi2_per_dof` in the record it cites returns
  `[1.5669, 1.8054, 19.2935, 30.3153, 35.5969, 40.9469]` — **nothing in [1.0, 1.2]**,
  across **both** revisions of that file, byte-identical in each. The 35.6 is one
  binning's bootstrap and its own frame-based counterpart is **1.8054**; the other
  binning pairs 40.9469 → 1.5669. `git log -S` puts the entry at the commit that
  wrote the contradicting record, so it was quoted from a computation nobody
  persisted — not lost to a later regeneration and not from a retired arm.
  **The finding itself was unaffected (~20× either way), which is exactly why the
  number went unchecked for so long.** Two mechanisms kept it alive: it paired two
  numbers without their QUANTITY stated (the binning), which is this thread's
  registered commensurability class; and it failed in the FLATTERING direction —
  against an assumed null of 1, "1.1" reads as a near-perfect fit, and nobody
  re-checks a number that says the model fits. At the frame-based ν the null is
  **ν/(ν−2)**, so the true 1.81 sits BELOW it and the honest sentence is *"the
  errors are conservative"*, not *"the errors are right"*. **The rule: a headline
  number must be reproducible from a tracked record by enumeration, and a pairing
  must name the quantity both halves were computed over.**
  **AND FOR A NUMBER ARRIVING FROM ANOTHER PARTY THE RULE HAS A SECOND HALF: ASK
  WHERE IT LIVES BEFORE LANDING IT, AND DO NOT RELY ON THE SUPPLIER VOLUNTEERING
  THAT IT LIVES NOWHERE.** MEASURED: three figures underpinning a retraction were
  offered for landing, the receiving side asked what record held them, and the
  answer was that they had reached their user **inside a brief, verbatim, with no
  tracked record anywhere**. The supplier then said plainly that the question is
  what surfaced it — absent the question the figures would have landed and nobody
  would have looked. **So the discipline that works is the ASK, not the
  disclosure**, and a record of this class should say which of the two operated.
  The figures were not even wrong: their difference reproduced the tree's own
  measured term exactly, which is precisely why nothing about them invited a
  check. **A number that is arithmetically consistent with a tracked one is still
  unhomed if no record contains it**, and that is the case a reproducibility check
  passes and a provenance check fails.
- **A NUMBER MEASURED FROM A LIVE TREE DESCRIBES A STATE THAT MAY NEVER HAVE BEEN
  COMMITTED — and it reads as a property of the work rather than of the moment.**
  The registry already says *never EDIT a running script*; this is the other half,
  *never MEASURE a changing one*, and it is the more common error because measuring
  feels passive. **FOUR MEASURED INSTANCES in one day, across three sessions:**
  (1) falsification counts for a bootstrap edit taken mid-edit and published as
  `psfex 0 -> 4` where the committed state is 7 — *"the numbers described a state
  that was never committed"*; (2) concurrency trials read as *"intermittent, 2 of
  3 RED"* while the fix was landing in stages, so the trials straddled **three**
  code states and the rate described none of them; (3) a delivery-gap finding
  (`install_astromatic.sh` reachable from nothing) that went false **within the
  hour** by a peer's commit, after being written into this file; (4) **the sharpest
  — a proxy metric calibrated against four rows scored AFTER the calibrating
  session had itself compressed them, correlated against their PRE-compression cut
  rates.** Mover and measurer the same session, in the same command, in the very
  metric under calibration; it reported the strongest row at **zero** narrative
  markers and would have shipped inverted.
  **THE RULE: state the commit you measured at, and re-measure before citing.** A
  number without a commit is a claim about an instant nobody can return to.
  **AND THE MITIGATION THAT ACTUALLY WORKS IS STRUCTURAL, not vigilance:** take the
  number from the COMMITTED artifact, never the working copy — which is what the
  `prepare-commit-msg` numstat stamp already enforces for one class of number, and
  the reason that hook exists at all. Every instance above was a number a hook did
  not cover. **Corollary: a finding ABOUT the tree is perishable by construction —
  delivery gaps, reachability, "nothing calls X" — so it carries its commit or it
  is not a finding.**
  **THE "COMMITTED ARTIFACT" MITIGATION IS NOT SUFFICIENT AND INSTANCE (5) IS WHY:
  IT CAN BE SATISFIED BY THE PARENT.** A calibration table justifying a size ceiling
  was measured from four files and published in `c7c5c4d` — the same commit that
  edited all four, inserting a two-line marker into each. Every row was the
  PRE-EDIT state, wrong by a constant **+2 lines / +23 bytes**, and the numbers
  were correct against `c7c5c4d^`. So the measurement WAS taken from a committed
  artifact; it was the wrong one. The stated headroom of 26% was 25%.
  **THE STRONGER FORM: measure at the state you are COMMITTING — after your own
  edit — not at the state you started from.** The failure needs no concurrency and
  no peer: the mover and the measurer are the same session in the same commit, and
  the table is internally consistent, so nothing in it looks wrong.
  **AND THE SECOND HOME IS WHAT MAKES IT SURVIVE A CHECK:** the same four rows were
  duplicated verbatim into `check_prompt_scope.sh`'s header (since removed), so cross-checking
  either against the other CONFIRMS both while both disagree with the tree — the
  file's own destination rule (*a second home is a second place to drift*) failing
  inside the commit that states it. **A duplicated number is not corroborated by
  its duplicate.** Found independently by two sessions on the same boot, each
  re-running `wc` rather than reading the table.
  **AND THE CASE THAT SAVED (4) IS THE GENERAL DEFENCE: a proxy calibrated against
  cases whose true answer is already known.** Three predictors were built for that
  triage — narrative markers per 100 words, word count, fraction of numbers homed
  elsewhere — and **all three failed on the calibration set**, the first one
  *inverting*. Without the calibration the inverted metric ships and is quoted with
  confidence. **A metric that inverts on its own calibration set is worse than no
  metric**, and this is the positive-control rule applied to a PROXY rather than to
  a gate.
- **A RANGE MEASURED IN ONE SESSION IS THAT SESSION'S SPREAD, NOT THE QUANTITY'S —
  AND EVERY SESSION THAT PUBLISHES ONE BELIEVES IT IS PUBLISHING THE QUANTITY.**
  The INVERSE of the `n=1 wearing n=2` rule above: there, two measurements differ in
  nothing but the operator and read as replication; here, one operator's repeated
  measurements read as a population bound. Both produce a number nobody can
  reproduce, by opposite mechanisms, so a citation must say which it is.
  **MEASURED on this repo's own guard-suite wall time, which four sessions
  published four times and no two agreed** (written out in words below on purpose —
  see the rule at the end of this entry):
  a 27-to-33 band, an about-30 point estimate, a 44-to-48 band, a 41-to-43 band.
  The first sits BELOW every later observation; the other three each exclude most
  of what the other sessions saw. **Every one was honestly measured. Every one was
  the author's own runs.**
  **THE SHARPEST INSTANCE IS SELF-INFLICTED AND ARRIVED WITHIN THE HOUR.** The
  session that refused to publish a peer's pooled range — on the correct ground
  that it had executed only 4 of the 10 runs in it — published its OWN four as
  41-to-43. Its next three runs, same rig, same commit family, same hand, read
  **44** and **40**: BOTH outside the range it had just published, giving a true
  own-session spread of **40 to 44 over seven runs**. The refusal was right and the
  replacement would have been the fifth wrong literal. **A spread does not converge
  by being yours.**
  **WHY IT SURVIVES: n feels like the fix and is not.** Every one of the four was
  quoted with its n (4, 2, 4, 4) and every one was still wrong, because n bounds
  the SAMPLING error and says nothing about a between-operator or between-moment
  term nobody has attributed. Here that term is still UNATTRIBUTED — load was ruled
  out (one session's fastest run carried its highest load), the `[network]` check
  measured dead flat at 18 s over four consecutive runs, and the per-check spread
  within a session is ~3 s against a ~10 s spread across them.
  **THE FIX IS NOT A BETTER RANGE, IT IS NO LITERAL.** The quantity was removed from
  all four of its homes and replaced by the claim it was making, because the runner
  PRINTS its own wall time on every run — the treatment `pre-push` already gives the
  check COUNT, for the reason stated there: *a count with six homes and no guard
  goes stale by default*. **A quantity that has produced four wrong published values
  does not want to be a literal; it wants a derivation.**
  **AND THE ENTRY'S OWN CONCLUSION APPLIES TO THE ENTRY.** The pooled observations
  across sessions span roughly 39 to 50 over about a dozen runs — and that figure is
  not published as the answer either, because **nobody ran all of them**; it is an
  aggregate of numbers most of its quoters did not execute, which is the thing this
  entry exists to name. Only the own-session figures above were executed by the
  author who states them.
  **RULE, and it is two halves:** state whether a range is a WITHIN-operator spread
  or a POOLED one, and name who ran which; and where the quantity is cheap to
  re-derive, publish the derivation rather than any range. **Second rule, learned by
  breaking it twice in one session:** a record that retracts a literal by PASTING it
  becomes a hit for every sweep hunting live instances — the acceptance grep for
  this very cleanup went RED on its own retraction — so the four figures above are
  spelled out in words, and a fixed-string sweep for any of them still returns zero.
- **A CLAIM CORRECTED AT ITS REPORTING SITE SURVIVES AT EVERY OTHER SITE THAT
  CARRIES IT — and the correction reads as complete because the reported instance
  is fixed.** This repo's own 14-vs-10 write-site lesson, one level up: there the
  fix was applied to the read sites a grep could see while every caller kept
  writing the old key; here the fix is applied to the row a finding was reported
  in while every other file keeps asserting it. MEASURED: a two-lane build
  constraint was corrected in `requirements-tools.txt` and **survived in
  `TOOLS.md`'s PSFEx row**, still reading *"It does NOT build here:
  `autoconf`/`automake`/`libtool` are absent… the deb-src route is blocked"* —
  while `autoconf` and `automake` are present and PSFEx 3.21.1 is built from
  source and installed. **The conclusion was refuted by OUTCOME, not merely by the
  tool list.** **The rule: when a claim is corrected, grep for the CLAIM across the
  tree, not just the row it was reported in — and the grep must be match-centred,
  or it repeats the entry above.**
  **AND THE COUNTER-MEASUREMENT, because it bounds the class rather than inflating
  it:** a match-centred sweep for survivors of every negative corrected in one
  working session (`NOT PACKAGED`, `not installed`, `no FITS reader`) found **no
  live false instances** — the remaining hits were true or generic template
  guidance. **So the mechanism is real and the rate on any given set of edits may
  be zero. Both halves belong in any citation of this entry.**
  **THAT COUNTER-MEASUREMENT WAS FALSIFIED BY ITS OWN CASING, AND THE SELF-MATCH IS
  THE FINDING.** A live false instance existed the whole time — the SCAMP row near
  the top of this file — and the search string this record NAMES could not reach
  it. **MEASURED AT `4d1185d^`, and the literals are written SPLIT below so this
  paragraph is not itself a hit:** searching the all-caps spelling
  (`NOT` + `PACK`+`AGED`) returned exactly ONE line, and it was the sentence
  reporting the sweep as clean; searching the mixed-case spelling
  (`NOT` + `pack`+`aged`) returned exactly ONE line, 1,635 lines above it, and it
  was the live false claim. So the sweep's own record was the only thing its own
  query could match.
  **AND THE FIRST WRITE-UP OF THIS FINDING FALSIFIED ITSELF ON COMMIT, WHICH IS THE
  REUSABLE HALF.** It documented the search by PASTING the literal string and a
  line number. On commit the paste became a second occurrence — so the sentence
  *"exactly one uppercase occurrence"* was true when measured and FALSE once
  written — and the pasted line number was already stale by 32 lines, because text
  had been added above it in the same commit. **The `doi.org` shape again: the
  sentence asserting an absence became the thing present.**
  **THE RULE: YOU CANNOT DOCUMENT A STRING-SEARCH FINDING BY PASTING THE STRING.**
  Split the literal so the record's own occurrences are distinguishable from live
  ones, and state COUNTS at a named commit rather than line numbers, which move.
  This tree already had the pattern in two places — `check_removal_conditions.sh`
  splits its own detector literal, and `check_prompt_scope.sh` (since removed)
  scoped its marker to a head window precisely because the contract file showed
  the marker in an example.
  **AND CASE-INSENSITIVITY ALONE IS NOT THE FIX: it closes the MISS and WIDENS the
  self-match, by matching both casings of the record's own text.** The completion
  is already in this file — *a count answers presence, not assertion; read the
  sentence.* Same self-match family as `pgrep` matching its own argv,
  `check_removal_conditions` matching its own detector string, and
  `check_prompt_scope`'s head-window rule — here appearing INSIDE the record that
  certifies a sweep clean, which is the worst position for it.
- **PROXIMITY TO A RULE IS NOT PROTECTION FROM IT — AND MAY BE THE OPPOSITE, BECAUSE
  WRITING THE RULE CREATES THE FEELING OF HAVING HANDLED IT.** Distinct from the
  self-match family above, which is about a detector matching its own text; this is
  about the AUTHOR of a rule breaking it, and the interval is measured in minutes.
  THREE WORKED INSTANCES, all inside one unit, each by whoever had just written the
  relevant rule:
  (1) a session handed a peer a numbered trap list including *"every `.ssf` must live
  under `$HOME` — the Siril flatpak has a private `/tmp`"*, then ONE MESSAGE LATER
  pointed `coverage_frame.py`'s output at a `/tmp` scratchpad, where the tool writes
  its `.ssf` beside the record — both runs died silently and the numbers had to be
  re-taken;
  (2) a session shipped a guard whose entire purpose is catching format drift in
  emitted commands, then invoked `coverage_frame.py --grid 40x26` as two arguments
  against an emitter that parses only `--opt=value`, so the option was dropped, the
  rescue rung never fired, and a soft-failure contract reported a clean skip;
  (3) a commit whose SUBJECT names a stale-citation defect fixed that citation in the
  file's header and left it in the runtime message, so the guard kept PRINTING the
  wrong-route number while the message asserted it was fixed.
  **The generalisation is not "be careful" — it is that a freshly-written rule is a
  WORSE predictor of the author's compliance than an old one, so the check that
  matters is the one run against the artifact, not against the intention.** Instance
  (1) was caught by a silent failure, (2) only by a positive control that had to
  fire, (3) only by re-reading the tool's OUTPUT rather than its diff. None was
  caught by the author remembering the rule they had just written.

  **THE RULE: a records sweep is case-INSENSITIVE (`grep -i`) or it is not a sweep,
  and a record asserting a clean sweep states the exact query it ran** so a later
  reader can re-run it rather than trust it. HONEST BOUND, carried because two
  sessions agreed on it and neither could test it: nobody can now show what casing
  the original sweep actually used. What is checkable, and all that is claimed, is
  that the string this record names cannot reach the instance it missed. The other
  two strings it names (`not installed`, `no FITS reader`) have NOT been re-swept.
- **A SECOND SESSION CATCHES ERRORS NOT BY HAVING DIFFERENT EVIDENCE BUT BY
  APPLYING DIFFERENT PRIORS TO THE SAME TREE — and the maker's prior is the one
  that produced the error.** The weaker mechanism is the useful one: it means
  the practice works on an IDENTICAL checkout, with no separate data on either
  side. THREE WORKED INSTANCES, all from one L1 build/audit pair, and each
  correction ran AGAINST the more interesting answer for whoever made it:
  (1) a per-frame background step was argued to be the combine-corner fix from
  its optical-state reading — refutable from `build_sky_flat.sh`'s own
  justification, which the maker had already read; (2) the union's coarse
  resolving power was attributed to framing=max mosaic heterogeneity — killed
  by a single homogeneous per-set stack (aug06/set-03) measuring COARSER than
  the union, 0.334 against 0.287 in Red; (3) a flat "no pooling" doctrine was
  invented in place of the meta-analysis default — refutable from the
  standards-first rule in `CLAUDE.md`, which the maker reads at session start.
  Two of the three were available in principle to their maker; only (2) needed
  evidence that did not yet exist.
  **AND THE LIMIT, which matters more than the mechanism:** it fails on anything
  where both sessions share the prior, which is most of what any two sessions
  agree about. Across that whole exchange, NOT ONE correction on either side
  came from shared ground. Two sessions agreeing is therefore not evidence —
  it is the region where the practice is blind, and it is the larger region.
  **THE OPERATING CONDITION, without which the limit above is unusable — MEASURED
  on the first instance of it actually firing.** Knowing agreement is the blind
  region does not by itself find anything: *"we have converged, be careful"* names
  nothing checkable and produces nothing. **What works is to extract the shared
  proposition as ONE falsifiable sentence, then go look.** MEASURED: two sessions
  independently argued for the same records split — installed-state belongs in the
  generated inventory, capability in `TOOLS.md` — from different evidence
  (a 24-hour staleness pattern; an availability-vs-capability row). Both rested on
  *"`manifest.tsv` is authoritative"*, which neither had checked. Named in that
  form it fell to one command: **21 rows, last written before the day's work,
  omitting PSFEx, SCAMP, `source-extractor` and a 1.5 GB catalogue.** Had it stood,
  every reader would have been redirected to an authoritative-looking inventory
  silently missing the tool behind the field model that register row 52 cites —
  the arm validating the κ that three rows rest on. **The rule is not "distrust
  agreement"; it is "name the premise both sides stand on, in a form someone can
  falsify without further interpretation, and check it."** A convergence with no
  named premise is not a tripwire, it is a mood.
  **AND THE OPERATIONAL TEST FOR WHETHER A SECOND MEASUREMENT COUNTS AT ALL:
  REPLICATION BOUNDS ERROR ONLY WHEN THE TWO MEASUREMENTS DIFFER IN SOMETHING.
  Ask what differed. If the answer is "the operator", it is n=1 wearing n=2**, and
  the second instance reads as corroboration, which is worse than having only one.
  MEASURED, n=2, in both directions:
  **IT FAILED** — a worker and a manager each probed siril's DEFAULT `save`, each
  found `DATASUM` absent, and the manager wrote *"BLOCKED, measured twice
  independently"* into a direction. Nothing differed but the operator. The error
  was broken by varying the SOURCE, not by repeating the probe: siril's own help
  reads `save filename [-chksum]` and the flag works at runtime, so the default
  had been promoted to a limit.
  **IT WORKED** — asked to re-check a stale-negative sweep, the worker deliberately
  did NOT re-run the phrase sweep, on the grounds that a phrase sweep is what let
  the original claim survive, and asked the RIG instead. Same question, different
  instrument, real null across 9 availability and 12 interpreter-scoped claims.
  **THE CONVERSE IS ALSO REGISTERED HERE, so the rule is not "prefer docs": the
  docs WITHOUT a probe promote a LISTING to a capability** — `tilt` and `inspector`
  are listed by `help` and refuse at runtime. **A doc establishes the claim; a
  probe settles it.** `save -chksum` was put through both, and siril's checksum
  arithmetic then matched astropy's on identical bytes.
  **AND THE TEST ABOVE IS NOT SUFFICIENT — MEASURED, ON A CASE THAT PASSES IT AND
  STILL FAILED. "ASK WHAT DIFFERED" IS ANSWERED CORRECTLY AND THE CONVERGENCE IS
  STILL WRONG, WHEN WHAT DIFFERED IS THE APPARATUS AND WHAT IS SHARED IS THE
  INFERENCE.** Two sessions asked whether siril's registration reference still
  matters on the SHIPPED astrometric route. Both measured composite-versus-member
  orientation, with DIFFERENT conventions and independently: −0.44°/+0.32° and
  −0.45°/−0.73° for the composites against members at −164.77°/+164.35°/−176.57°
  and −164.85°/+165.07°. Both concluded *"the composite inherits no member's
  orientation, therefore the reference does not matter"*, and one wrote it into a
  tracked record. **The measurements were right, agreed to the degree, and were
  taken by different means — the replication test above is satisfied.** The
  conclusion was false: a one-knob probe (same 4 members, 2 nights, same framing
  and weight, only `--ref` moved) gives canvas 7071×4629 → 7095×4622, north
  +9.6244° → +7.7633°, centre-median G 157.4 → 90.5, B/G 0.7427 → 0.5260.
  **THE MECHANISM: an OBSERVATIONAL comparison cannot isolate a knob, and neither
  session moved one.** Composite-versus-member is a comparison between two
  populations; *"does the reference change the product"* is causal. Measuring the
  observation more carefully, twice, by two conventions, leaves the causal step
  entirely untouched — so the second measurement corroborated the first exactly
  where it was already blind. **THE SHARPER RULE: vary what the CONCLUSION rests
  on, not what the apparatus measures. If the claim is causal, the differing thing
  must be the knob.** The existing entry's *"different KIND of check"* is right and
  under-specified: every worked example above is a different READER of the same
  tree, and here two different readers with two different instruments both missed
  it. What caught it was an EXPERIMENT.
  **COMPANION, FOUND INSIDE THAT SAME PROBE — AN INSTRUMENT WHOSE FAILURE SIGNAL
  IS ITS OWN ARTEFACT.** The probe's pre-registration declared bit-identity by
  `md5sum`, and all three arms differed, which by its own stated rule voided it.
  The difference was the FITS `DATE` card alone — siril stamps a write time, so
  two pixel-identical products NEVER md5-match. **md5 of a FITS is not a pixel
  comparison.** Read at face value it would have reported the positive control
  failing and buried a live finding. Same shape as `stat` printing *"stats
  failed"* on an all-zero difference (which is that test's SUCCESS signal), one
  level up: there the artefact is in the tool's output, here it is in the choice
  of instrument. The comparison that settled it was per-pixel with a planted
  +0.01 control: **0 differing of 98,194,977 between the auto arm and an explicit
  `--ref=1`, control 1 differing.**
  **AND A DISTINCT FAILURE MODE THE REPLICATION TEST ABOVE DOES NOT REACH: ONE
  READER'S NUMBER TRAVELLING UNEXAMINED. CITATION IS NOT REPLICATION.** That test
  asks what DIFFERED between two measurements and calls it n=1 if the answer is
  "the operator". This is worse: there is only ONE measurement, and it acquires
  the appearance of several by being quoted. MEASURED instance, three sessions: a
  rebuild verification — 98 products, **7,253,511,213 px, zero differing** — was
  produced by one session, cited by a second to the owner and to a third, and
  adopted by the third as a stated premise. **Nobody re-ran it.** Each citation
  raised the apparent support while the evidence base did not move, and the
  originating session was the one that had to point at it.
  **THE HAZARD IS NOT THAT IT WAS WRONG — IT REPRODUCED EXACTLY**, and that is the
  point rather than a mitigation. Re-run independently: 97 products,
  7,107,861,513 px, zero differing, one file GONE. The delta is
  **145,649,700 px = 8540x5685x3**, precisely the one product deliberately deleted
  in between and announced in that commit. The figure survived contact — and
  **nothing in the practice would have caught it if it had not.** A number that is
  never re-run is indistinguishable from one that cannot be.
  **THE TELL, and it is checkable:** a figure whose apparent support is rising
  while its measurement count stays at one. **THE RULE: when you cite a number you
  did not measure, either re-run it or mark it as another session's single
  measurement in the same breath.** Naming the source is not enough — all three
  sessions here attributed it correctly and it still hardened into a premise.
  **AND THE MIRROR OF THAT IS THE EXPENSIVE DIRECTION: A LISTING'S *ABSENCE*
  RETIRING A CAPABILITY THAT EXISTS. `listed` IS NOT `exhaustive`.** A listing's
  PRESENCE manufacturing a capability opens a dead route and the next probe kills
  it; a listing's ABSENCE *closes* a live one, and nothing probes a route already
  written off. MEASURED, and it closed the named route for the largest defect in
  any shipped product: `seqapplyreg`'s help says it applies *"registration data
  previously computed"* and registration data is
  `shift | similarity | affine | homography`. From that list a session concluded
  *"there is no per-image-WCS transform class … Siril discards per-image
  distortion BY DESIGN"* and closed the native astrometric compose. **The premise
  is TRUE; the conclusion does not follow.** The registration data IS linear —
  Siril COMPOSES the SIP undistortion with it: *"it is first corrected for
  distortion and then linearly projected … in a single operation"*
  (siril.readthedocs.io, Registration). The help text describes what the command
  CONSUMES and has no obligation to describe the stage that ran before it.
  **What made it survive: the corroboration was a DIFFERENT COMMAND.**
  `register -disto=`'s 3.99/6.42/6.19 px is a shared-solution facility, which is
  why it fails and why it says nothing about `seqplatesolve` — a real measurement,
  correctly quoted, of the wrong subject, which reads as confirmation.
  **The refutation was in four places at the time it was written** — a shipped
  script (`run_undistort_compose.sh:330`, `seqplatesolve` is the DEFAULT), a
  shipped guard built expressly to protect the capability
  (`compose_preflight.py`), a product header (`REGMODEL = astrometric`,
  `REGUNDIS = True`), and the vendor's own manual. **Being written down in
  executable code did not prevent it**, which bounds "it is documented" as a
  defence: none of those four is a document anyone re-reads at the moment of use.
  **THE RULE: a capability surface is evidence of PRESENCE, never of ABSENCE —
  the same asymmetry as never reporting a negative from a truncated view, one
  level up. Before a doc reading retires a route, check whether the route is
  already running.**
  **AND THE CAUSE UNDER IT IS OURS, NOT THE VENDOR'S — n=3, THREE FILES, TWO
  SESSIONS, ONE EVENING. A CORRECT MEASUREMENT OF A NARROW SUBJECT, WIDENED ONE
  STEP, THEN QUOTABLE AS CORROBORATION.** The doc reading above did not invent its
  conclusion: it found a pre-existing over-generalisation in THIS registry and
  quoted it as support. The widening is always from something MEASURED to
  something ADJACENT, and the adjacency differs every time:

      operation -> command   a standalone SIP warp    -> "register -disto= is not per-image"
      command   -> design    register -disto=         -> "Siril's design assumes ONE optical
                                                         state per sequence"
      flag      -> tool      -weight=wfwhm|nbstars    -> "Siril's -weight is a min-max ramp"
                             is a min-max ramp           (FALSE of -weight=noise, which is
                                                          inverse-variance, as the shipped
                                                          run_undistort_compose.sh says)

  **In every instance the measurement is correct and the number is right.** The
  defect is the NOUN the number gets attached to in the write-up, which is why
  re-checking the measurement never catches it. **The check is one question asked
  of the EVIDENCE rather than of the claim: what exactly was RUN?**
  **THE REGISTRY'S OWN PREAMBLE DOES NOT CATCH THIS, AND THAT IS THE FINDING —
  all three entries are FULLY COMPLIANT WITH IT AND STILL WRONG.** It required n,
  instrument and scope; each of the three carries all three correctly. SUBJECT has
  been added there as a fourth axis for exactly this reason.
  **DO NOT COMPUTE A RATE FROM THESE THREE.** All three surfaced because someone
  was working the adjacent thing — a shipped route contradicted one, a queued
  experiment depended on another, the third was found while editing that entry's
  tail. **None was found by looking for this class**, so three is a sample of
  where attention happened to fall, not of how often it happens. The
  consequence-VISIBLE case (a claim a shipped artifact contradicts) is the rare
  one; the quiet case — wrong about a subject nobody has re-run — has no tell at
  all.
  **AND THE SAME CHECK CAUGHT A FIX WHOSE DELIVERY PATH EXCLUDED ITS OWN
  BENEFICIARY** — a class distinct from the check-cannot-fail family, because
  nothing here is a check. `install_astromatic.sh` was written expressly to close
  the *"VERIFIED and NOT REPRODUCIBLE FROM A CLONE"* gap, states that purpose in its
  own header, and was called by nothing: `x86_bootstrap.sh` — the script `CLAUDE.md`
  defines the environment as — mentioned it, `psfex`, `scamp` and `source-extractor`
  ZERO times each. The omission was not a design choice; that script already runs
  `sudo apt install` 23 times, so root is not the reason.
  **BOTH INSTANCES OF THIS CLASS ARE NOW CLOSED, AND THE SPEED OF THAT IS THE
  DURABLE PART — read what follows as a CLASS with two historical examples, never
  as a live defect list.** `install_astromatic.sh` is invoked three times
  (`x86_bootstrap.sh` `--root-cmds`, `--go`, `--manifest`), so the paragraph above
  is history. The second example was **`install_hooks.sh`**, and it was worse: the
  first omitted a TOOL, that one omitted two GATES. MEASURED while it stood — the
  bootstrap matched `install_hooks|hooks/|pre-push|core.hooksPath` ZERO times, the
  only pointer outside the hook machinery was a session ROLE file (a document
  rewritten at every handoff), and since `.git/hooks/` is never tracked a fresh
  clone got neither `pre-push` (the guard runner gated nothing) nor
  `prepare-commit-msg` (no staged-numstat stamp) — the two mechanisms built to
  close *"nothing runs the guards"* and to stop paraphrased counts, absent on
  exactly the machine never told to install them. **CLOSED: the bootstrap now runs
  `install_hooks.sh` as Layer 0, ahead of every other layer, and `--check` reports
  both hooks ok at exit 0.**
  **WHAT SURVIVES BOTH CLOSURES, and it is the reason the entry is kept rather than
  deleted: each example was written into this registry and made FALSE BY THIS
  TEAM'S OWN WORK within about an hour — twice, in one file, once by the session
  auditing for that very class.** A `last checked` date cannot catch that, and
  neither can re-reading; only re-executing the claim against committed HEAD can.
  **So a delivery-gap finding is perishable by construction: state the commit it
  was measured at, and re-measure before citing it.** The general test is unchanged
  and does not perish — a recommendation is discharged only when a CLONE reaches
  it, never by the thing being present on this rig.
  **Discharge test for any
  install recommendation, and it is `CLAUDE.md`'s existing standard rather than a
  new rule: a recommendation is discharged only when a CLONE reaches it, never by
  the thing being present on this rig.**
- **A RATIFIED DECISION WHOSE JUSTIFICATION CITES A FRAME COUNT IS CONDITIONAL ON
  THE ROUTE THAT PRODUCES THAT COUNT — record the route with the ratification, or
  the decision silently means something else on another route.** A user decision
  is ratified against a MECHANISM, and a mechanism stated as a fraction ("a
  minority per-pixel sigma rejection removes", "1 frame in 500") carries a
  denominator that belongs to the pipeline, not to the sky. MEASURED instance:
  `BACKLOG:aircraft-rejection-retest` ratified KEEPING an 8-frame aircraft
  crossing on "any pixel carries it in ~1 frame of 500" — true single-pass. The
  groups route stacks CONSECUTIVE BLOCKS, so the same 8 frames land whole inside
  one group — 53% of a group of 15, a per-pixel MAJORITY, which this registry
  says survives — and the compose is a plain mean with no rejection. The
  identical ratified decision rejects the transient on one route and ships it on
  another. The class is wider than rejection: any acceptance argument of the
  form "X is a small fraction of N" is invalidated by any change that alters N —
  group size, a cull, a sub-stack compose, a frame-count-derived algorithm
  switch. When ratifying, write the ROUTE and the count the argument assumes;
  when changing a route, grep the ratified decisions for fractions before
  assuming they carry.
  **And grep the REVERTS, not just the keeps.** A revert is a ratified decision
  too, and this registry's most expensive one states itself as a fraction: the
  `--desky` entry's headline — corner spread 12.4% vs 0.4% — is qualified "500
  frames, one knob", i.e. measured on the single-pass denominator; nothing says
  what it measures on a 5x100 groups build. The rule is symmetric: a decision to
  STOP doing something inherits its route just as a decision to keep does.
- **A BASENAME IS NOT A FILE IDENTITY IN A MULTI-SESSION CORPUS — AND A CHECK THAT
  COMPARES ONE IS BLIND EXACTLY WHERE THE NAMES REPEAT.** MEASURED: **19
  `skyflat*.fit` masters under `sessions/` carry 12 DISTINCT basenames**;
  `skyflat_set-01/02/03.fit` each exist in **three** sessions and
  `dark_master.fit` exists in **all three**. Per-session directories make repeated
  names the NORMAL state, not an edge case, so any predicate of the form *"do
  these two files share a filename"* answers *yes* precisely when two different
  files are being confused — the failure is silent and it is worst on the case the
  check exists to catch. **Two masters can also agree on every other stamped
  field:** july31 and aug06 `skyflat_set-03.fit` both read `STACKCNT=500`,
  `NAXIS1=6064`, so a name-plus-frame-count identity collapses too, and the
  provenance a product ships is then byte-identical to a correct one. **The fix is
  CONTENT, not a better name.** A FITS `DATASUM` separates the real trio at
  **3443652352 / 884799382 / 369242041** and costs 0.05 s per 6064x4040 float
  master via `astropy`, computed in memory so the master is never rewritten —
  which matters because siril STRIPS `DATASUM`/`CHECKSUM` on any load+save while
  preserving foreign keys (both measured). Carry the hash on the PRODUCT as a
  provenance value beside the readable name, which is ESO's `CAL1 NAME` +
  `CAL1 DATAMD5` shape. **A session-qualified name was proposed and withdrawn: it
  is a naming scheme this project would be inventing, and deriving it by counting
  path components from the end is itself a trap — the last two components are
  `masters/<file>` for every session and distinguish nothing.**
  **THE GENERAL FORM, which outlives the instance: an identity test must compare
  something that cannot repeat.** A path can repeat under a re-clone, a basename
  repeats by directory convention, a name-plus-count repeats whenever two runs use
  the same depth. Content does not.

- **THE STAGED CORPUS IS NOT THE CORPUS. CHECK `datasets/` BEFORE DECLARING A
  CORPUS LIMIT — the reflex is to check `sessions/`, and the reflex has now been
  wrong twice.** `sessions/` holds the nights whose raws are on the rig — three of
  them. `datasets/` holds the tracked per-set records for every night ever
  ingested — **six**. A capability that exists only in the recorded corpus is
  invisible to anyone who checks the staged one, and both times the error
  produced a confident *negative*:
  - a BACKLOG kill-note read "all 12 staged sets are one target at 2.5 s and
    70 mm, so there is no exposure lever either" — true of the staged corpus,
    false of the recorded one;
  - and then a STOP: "a set at a materially different exposure … is an
    acquisition change", when **july27/set-01 and set-02 are already recorded at
    3.0 s** (282 and 253 frames, same 70 mm, same ISO 1600, same target).
  That 3.0 s against 2.5 s is a **1.44× lever in L²**, and it is the discriminator
  that breaks the trail-amplitude degeneracy the drift work could not break at one
  exposure — because a trail-amplitude error scales with L² while an optical term
  does not scale with exposure at all. **The cost of the reflex is not a wasted
  search; it is a "cannot be done" written into a record about work that can.**
  Re-staging existing data is cheap by the owner's own standing statement and is
  not an acquisition ask.
  **AVAILABLE IS NOT WORTH RUNNING, and this entry is the one a top-down reader
  finishes on: the lever WAS used and the question is CLOSED AGAINST it — see the
  co-varying-systematic entry above (contamination scaled with the lever; exposure
  and NIGHT perfectly aliased). Do NOT re-open the july27 exposure comparison.**
  The OFFSET shape is separately dead needing no frames: `t_eff = t_nom − δ` implies
  δ = 1.0206 s = **1021 ms** against shutter latencies of O(1–10 ms), so
  multiplicative is the only surviving shape and no mechanism produces one.

- **A PROVENANCE STAMP BUILT AS AN ALLOW-LIST IS A DENY-LIST FOR EVERY KEY IT
  OMITS — siril `stack` propagates the REFERENCE member's ENTIRE header, so a
  route's leak surface = (reference header) − (keys siril recomputes) − (the
  allow-lists that route applies).** MEASURED on the four-night corpus (77
  members, reference = member 36): five reference-specific keys survive on the
  composite — `PIPEREV` (7 distinct values across members), the SINGULAR
  `CALSET` (17), `DATE-OBS` (17), `GRPSIZE` (10), `FILENAME` (50) — and all five
  propagate into `_spcc`. The leaks are REFERENCE-keyed, not first-member-keyed
  (the old/new corpus pair discriminates: each leaks its own reference's
  values). The acquisition block (`EXPTIME`…`INSTRUME`) is inherited the same
  way and reads 1 distinct across all 77 today — nothing false until a corpus
  mixes values (july27's 3.0 s vs 2.5 s is the standing `EXPTIME` trigger).
  What siril RECOMPUTES is verified, not assumed: `STACKCNT`/`LIVETIME` equal
  the member sums exactly; `EXPSTART`/`EXPEND` carry the true span beside the
  false `DATE-OBS`. **The route classes differ because the allow-lists applied
  differ:** groups per-set finals get BOTH stamps post-stack (measured: set-01's
  final reads the build-era `PIPEREV` while its own reference sub carries an
  older one; residual leak `GRPSIZE`/`FILENAME`); `run_undistort_compose`
  products get the composite tuple ONLY (the five-key leak class);
  `run_pipeline.sh` and `compose.py` apply NEITHER — absent, not false. The
  singular `CALSET` is the sharpest instance: the commit that built the
  composite tuple names CALSET inheritance as the defect it fixes, added the
  plural `CALSETS`, and never replaced the singular — its own worked example
  still ships on the product. **The wrong-mechanism trap that rode with it:**
  two sessions confirmed to each other that a per-set final's `DATE-OBS` is
  right only because `setref s 1` picks the earliest group. Both missed that a
  SECOND stamp call carries it (`header_stamp_lines` ends with `DATE-OBS` and is
  applied to the final), and the fallback is empty anyway — every sub of a set
  carries the SAME `DATE-OBS` (measured 4/4 and 5/5; all stamped from one
  set-level capture). Reading the artifact (which function emits which keys,
  applied where) settled in minutes what two agreeing readers had settled
  wrongly. Full census, values, intent trace and the tracked-record carriers:
  `datasets/corpus/piperev_inheritance.json`; the fix decision is
  BACKLOG:`composite-header-identity`.

