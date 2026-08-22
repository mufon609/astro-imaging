# Evidence, records, and provenance

Phase-2 file of the dead-ends registry split (`README.md` here holds the index
and dispositions; pre-compression forms live in git and in the live
`docs/dead-ends.md` until the merge). Entries are maintained IN PLACE.
Cross-references to sibling files are written as (`<file>.md`) pointers.

<!-- phase-2: maintained in place; not regenerated from the manifest -->
- **A BARE md5 OF FITS PIXEL DATA IS ONLY COMPARABLE WITHIN ONE BYTE-ORDER
  CONVENTION — quote a pixel-difference COUNT, never a digest, when the question
  is "did this product change?"** FITS stores pixels BIG-ENDIAN on disk, so
  `astropy` hands back a `>f4` array; hashing it AS READ and hashing it after a
  native-order cast (`<f4`, or an implicit `.astype`) give DIFFERENT digests for
  BIT-IDENTICAL pixels — measured by two sessions on one file, four digests,
  both right, products identical. **The failure mode is a false POSITIVE**,
  the expensive direction: it sends a session chasing a corruption that does
  not exist. A difference COUNT (`(a != b).sum()` with `max|diff|`) is
  convention-free and is what the verdict should quote; a digest, if recorded
  at all, carries its convention beside it. Same family: **a whole-file `cmp`
  (or md5) is the wrong test for "are these pixels the same"** — siril stamps
  its own creation `DATE` and the chain stamps `PIPEREV` (what that couples
  across parallel sessions is a BINDING RULE in `CLAUDE.md`), so two
  pixel-identical products always differ as FILES: the identity control here
  read "NOT byte-identical" while measuring 0 differing pixels of 69,359,745.
  A check that fires spuriously trains the operator to bypass it, which is how
  a real failure gets waved through later.

**EVERY RECORD-SCHEMA CHANGE CREATES A PRE-CHANGE GENERATION INDISTINGUISHABLE
FROM A POST-CHANGE ONE UNLESS SOMETHING MARKS IT.** A CLASS, not an incident,
and it applies to every schema this repo has ever changed. Measured twice in
one day in unrelated places: `solve_field.py`'s hint-contradiction gate added
its replay keys WITH the gate, so the pre-gate majority of records lacks them
and the one false solve the gate exists for has none — the mitigation
postdated the case it was built to make auditable (counts live in the
removal-conditions register row, their one home); and an error-model rename
left every pre-rename record carrying a neutrally-named SE no reader can
attribute to a model. **THE GENERAL MITIGATION: label BOTH sides and make the
consumer REFUSE a mixed set** — each row declares its `error_model` and the
resolver refuses rows that mix models or omit the label, so a pre-change
record fails LOUDLY instead of averaging silently into a post-change one.
**Corollary: the record layer is not a census of what was run — read any "we
measured N of these" row as a SAMPLE, never as COVERAGE, unless the census is
stated and checkable** (the solve corpus ran ~2× the register's claimed
denominator until a stated-method census was homed in the register row).

- **PREFER A CHECK WHOSE EVIDENCE IS READ FROM AN ARTIFACT OVER ONE A HUMAN
  TRANSCRIBES.** The registry already carries the negative — a check whose
  output is paraphrased is a check that did not run — and this is its
  constructive half: the paste-the-numstat rule was violated four times by its
  own author in a session actively watching for it, while the two checks that
  caught real defects the same day were both STRUCTURAL (numbers out of FITS
  headers; a diff of two generated `.ssf` files already on disk). A
  transcriptive check fails at whatever rate humans copy numbers. When a check
  must be transcriptive, that is a hook or a script waiting to be written, not
  a discipline problem.
  **THE CONVERSE IS THE HALF THAT BITES: THE ARTIFACT BEING RIGHT ONLY PROTECTS
  READERS WHO READ ARTIFACTS — AND A RECORD EXISTS PRECISELY FOR THE READERS
  WHO DO NOT.** In one evening four findings took the form "the record is
  wrong, the artifact is right" (a solve record asserting RA 6.03/Dec −65.10
  for a union whose header reads 310.62/+43.24 was the sharpest), each
  reported with the artifact as the reassurance. That is backwards for a
  record's audience: a right artifact beside a wrong record is a defect with
  its warning light disconnected. **Rank by who reads what — a wrong record
  with a right artifact is WORSE than one with a wrong artifact, because the
  second gets caught the first time anyone builds on it.**
  **ONE LEVEL UP, TO RESULTS: A RESULT THAT WAS PARAPHRASED IS A RESULT THAT
  WAS NOT RECORDED — and it survives longest when it flatters.** The
  error-model headline shipped as *"χ²/dof 35.6 on bootstrap errors becomes
  ~1.1 on frame-based ones"*; enumerating every `chi2_per_dof` in the record
  it cites returns nothing in [1.0, 1.2] — the 35.6's true frame-based
  counterpart is **1.8054**, quoted from a computation nobody persisted. It
  survived because the pairing named no QUANTITY (the binning — the
  name-the-quantity class, `star-shape-optics.md`) and because it failed in
  the FLATTERING direction: against an assumed null of 1, "1.1" reads as a
  perfect fit and nobody re-checks a number that says the model fits (the
  frame-based null is ν/(ν−2), so the honest sentence was "the errors are
  conservative"). **The rule: a headline number must be reproducible from a
  tracked record by enumeration, and a pairing must name the quantity both
  halves were computed over.**
  **AND FOR A NUMBER ARRIVING FROM ANOTHER PARTY: ASK WHERE IT LIVES BEFORE
  LANDING IT.** Three figures underpinning a retraction turned out to exist
  only inside a brief, verbatim, no tracked record anywhere — and were not
  even wrong, which is why nothing about them invited a check. **A number
  arithmetically consistent with a tracked one is still unhomed if no record
  contains it** — the case a reproducibility check passes and a provenance
  check fails. The discipline that works is the ASK, not the supplier's
  disclosure.
- **A NUMBER MEASURED FROM A LIVE TREE DESCRIBES A STATE THAT MAY NEVER HAVE
  BEEN COMMITTED — and it reads as a property of the work rather than of the
  moment.** The registry already says *never EDIT a running script*; this is
  the other half, *never MEASURE a changing one*, and it is the more common
  error because measuring feels passive. Five measured instances in one day
  across three sessions, kernels: falsification counts taken mid-edit and
  published for a state never committed; concurrency trials straddling three
  code states, the rate describing none of them; a delivery-gap finding gone
  false within the hour by a peer's commit; a proxy metric calibrated by the
  same session that was moving its calibration set — it reported the strongest
  row at zero and would have shipped INVERTED; and a calibration table
  measured from files the SAME COMMIT then edited — correct against the
  parent, wrong as published. **THE RULES: state the commit you measured at,
  and re-measure before citing; take the number from the COMMITTED artifact —
  at the state you are COMMITTING, after your own edit, not the state you
  started from.** A duplicated number is not corroborated by its duplicate —
  a second home is a second place to drift, and cross-checking the two homes
  confirms both while both disagree with the tree. **The general defence for
  any derived metric: calibrate against cases whose true answer is already
  known** — all three proxy predictors failed their calibration set, one
  inverting, and a metric that inverts on its own calibration set is worse
  than no metric.
- **REPLICATION BOUNDS ERROR ONLY WHEN THE TWO MEASUREMENTS DIFFER IN
  SOMETHING — ASK WHAT DIFFERED; IF THE ANSWER IS "THE OPERATOR", IT IS n=1
  WEARING n=2**, and the second instance reads as corroboration, which is
  worse than having only one. Measured in both directions: a worker and a
  manager each probed siril's DEFAULT `save`, both found `DATASUM` absent, and
  "BLOCKED, measured twice independently" went into a direction — nothing
  differed but the operator, and the error broke by varying the SOURCE
  (siril's help reads `save filename [-chksum]`, and the flag works). The
  converse also holds: **a doc establishes a claim; a probe settles it** —
  a listing alone promotes to a capability that refuses at runtime
  (`tilt`/`inspector`, the standing rig fact in `CLAUDE.md`).
  **"WHAT DIFFERED" IS NOT SUFFICIENT WHEN WHAT IS SHARED IS THE INFERENCE:
  vary what the CONCLUSION rests on, not what the apparatus measures — if the
  claim is causal, the differing thing must be the KNOB.** Two sessions
  measured composite-versus-member orientation with different conventions,
  agreed to the degree, and both concluded the registration reference does not
  matter on the shipped route; a one-knob probe (only `--ref` moved) falsified
  it — canvas, north and channel balance all moved (`stacking-compose.md`
  carries the numbers). An observational comparison cannot isolate a knob, and
  neither session moved one; the second measurement corroborated the first
  exactly where it was already blind.
  **AND A FAILURE MODE THE TEST DOES NOT REACH: ONE READER'S NUMBER TRAVELLING
  UNEXAMINED — CITATION IS NOT REPLICATION.** A rebuild verification (98
  products, 7,253,511,213 px, zero differing) was produced by one session,
  cited by a second, adopted by a third as a premise — nobody re-ran it; each
  citation raised the apparent support while the evidence base did not move.
  It happened to reproduce exactly on an independent re-run (minus precisely
  the one product deliberately deleted in between), and nothing in the
  practice would have caught it if it had not. **The tell: a figure whose
  apparent support is rising while its measurement count stays at one. The
  rule: when you cite a number you did not measure, re-run it or mark it as
  another session's single measurement in the same breath** — naming the
  source is not enough; all three sessions attributed it correctly and it
  still hardened into a premise.
- **A RANGE MEASURED IN ONE SESSION IS THAT SESSION'S SPREAD, NOT THE
  QUANTITY'S — AND EVERY SESSION THAT PUBLISHES ONE BELIEVES IT IS PUBLISHING
  THE QUANTITY.** The inverse of the n=1-wearing-n=2 rule above: one
  operator's repeats read as a population bound. Measured on the guard-suite
  wall time: four sessions published four ranges, no two agreeing, every one
  honestly measured from the author's own runs — and the session that
  correctly refused a peer's pooled range then published its own four-run
  band, whose next two runs landed OUTSIDE it. **n feels like the fix and is
  not**: every range carried its n, and n bounds sampling error while saying
  nothing about the unattributed between-moment term. **THE FIX IS NOT A
  BETTER RANGE, IT IS NO LITERAL** — the quantity was removed from all four of
  its homes because the runner PRINTS its own wall time on every run: a
  quantity that has produced four wrong published values wants a derivation,
  not a literal. **RULES:** state whether a range is a WITHIN-operator spread
  or a POOLED one and name who ran which; where the quantity is cheap to
  re-derive, publish the derivation. And **a record that retracts a literal by
  PASTING it becomes a hit for every sweep hunting live instances** — spell
  retracted figures out in words so a fixed-string sweep still returns zero.
- **A CLAIM CORRECTED AT ITS REPORTING SITE SURVIVES AT EVERY OTHER SITE THAT
  CARRIES IT — and the correction reads as complete because the reported
  instance is fixed.** The 14-vs-10 write-site lesson one level up: a build
  constraint was corrected in `requirements-tools.txt` and survived in
  `TOOLS.md`'s PSFEx row, refuted by OUTCOME (the tool was by then built and
  installed). **THE RULES, each one earned by a measured failure of the
  previous one:** when a claim is corrected, grep for the CLAIM across the
  tree, not just the row it was reported in; the grep is MATCH-CENTRED (the
  truncated-view entry, `verification-traps.md`); a records sweep is
  CASE-INSENSITIVE or it is not a sweep — the sweep that certified this class
  clean was falsified by its own casing, its query able to reach only its own
  report while the one live false instance (mixed-case) sat 1,635 lines above
  it; case-insensitivity alone then WIDENS the self-match, so the completion
  is *a count answers presence, not assertion — read the sentence*; and a
  record asserting a clean sweep states the exact query it ran.
  **YOU CANNOT DOCUMENT A STRING-SEARCH FINDING BY PASTING THE STRING** — the
  first write-up of this finding falsified itself on commit, its paste
  becoming a second occurrence and its pasted line number stale in the same
  commit. Split the literal so the record's own occurrences are
  distinguishable from live ones, and state COUNTS at a named commit, never
  line numbers. (`check_removal_conditions.sh` splits its own detector
  literal for exactly this reason.)
- **PROXIMITY TO A RULE IS NOT PROTECTION FROM IT — AND MAY BE THE OPPOSITE,
  BECAUSE WRITING THE RULE CREATES THE FEELING OF HAVING HANDLED IT.** Three
  worked instances, each by whoever had just written the relevant rule: a
  session handed a peer the flatpak-private-`/tmp` trap and one message later
  pointed a tool's `.ssf` at a `/tmp` scratchpad; a session shipped a guard
  against format drift in emitted commands, then passed an option in the one
  format the emitter drops — the rescue rung never fired and the soft-failure
  contract reported a clean skip; a commit whose SUBJECT named a
  stale-citation defect fixed the citation in the header and left it in the
  runtime message. **A freshly-written rule is a WORSE predictor of its
  author's compliance than an old one, so the check that matters runs against
  the ARTIFACT, not the intention** — none of the three was caught by the
  author remembering the rule just written.
- **A SECOND SESSION CATCHES ERRORS NOT BY HAVING DIFFERENT EVIDENCE BUT BY
  APPLYING DIFFERENT PRIORS TO THE SAME TREE — and the maker's prior is the
  one that produced the error.** The weaker mechanism is the useful one: the
  practice works on an IDENTICAL checkout. Three corrections from one
  build/audit pair, each against the more interesting answer for whoever made
  it, two of the three available in principle to their maker. **THE LIMIT
  MATTERS MORE THAN THE MECHANISM: it fails wherever both sessions share the
  prior — most of what two sessions agree about. Agreement is not evidence; it
  is the blind region, and it is the larger region** (the BINDING form is
  `CLAUDE.md`'s parallel-sessions rule). **THE OPERATING CONDITION that makes
  the limit usable: extract the shared proposition as ONE falsifiable
  sentence, then go look** — "we have converged, be careful" names nothing
  checkable. Measured on its first firing: two sessions argued the same
  records split from different evidence, both resting on "`manifest.tsv` is
  authoritative", which neither had checked; named in that form it fell to one
  command (21 rows, stale, omitting three installed tools and a 1.5 GB
  catalogue). A convergence with no named premise is not a tripwire, it is a
  mood.
- **A CAPABILITY SURFACE IS EVIDENCE OF PRESENCE, NEVER OF ABSENCE — before a
  doc reading retires a route, check whether the route is already RUNNING.** A
  listing's absence closes a live route, and nothing probes a route already
  written off. Measured, and it closed the named route for the largest defect
  in any shipped product: from `seqapplyreg`'s help listing
  `shift | similarity | affine | homography`, a session concluded Siril
  discards per-image distortion BY DESIGN and closed the native astrometric
  compose — while `seqplatesolve` + `seqapplyreg` (which COMPOSES each
  member's own SIP undistortion with the linear projection) was the SHIPPED
  DEFAULT, protected by a guard, stamped on the product headers, and stated in
  the vendor's manual. The help text describes what the command CONSUMES, not
  the stage that ran before it; **being written down in executable code did
  not prevent the closure**, which bounds "it is documented" as a defence.
  What made it survive: corroboration by a real measurement of a DIFFERENT
  command (`register -disto=`), correctly quoted, of the wrong subject — the
  measured-subject-widened-one-step pattern whose instances and bound are the
  SUBJECT axis in `00-registry-contract.md`.
- **A FIX WHOSE DELIVERY PATH EXCLUDES ITS OWN BENEFICIARY** — distinct from
  the check-cannot-fail family, because nothing here is a check. Two closed
  examples: `install_astromatic.sh`, written to close a
  not-reproducible-from-a-clone gap and called by nothing; then
  `install_hooks.sh` — worse, two GATES (`pre-push`, `prepare-commit-msg`)
  absent on exactly the machine never told to install them. Both were written
  into this registry and made false by the team's own work within about an
  hour — which is the durable point: **a delivery-gap finding is perishable by
  construction** (the live-tree entry above), and **the discharge test for any
  install recommendation is that a CLONE reaches it, never that the thing is
  present on this rig.**
- **A RATIFIED DECISION WHOSE JUSTIFICATION CITES A FRAME COUNT IS CONDITIONAL
  ON THE ROUTE THAT PRODUCES THAT COUNT — record the route with the
  ratification, or the decision silently means something else on another
  route.** A mechanism stated as a fraction ("1 frame in 500") carries a
  denominator that belongs to the pipeline, not the sky. Measured:
  `BACKLOG:aircraft-rejection-retest` ratified KEEPING an 8-frame aircraft
  crossing on "any pixel carries it in ~1 frame of 500" — true single-pass;
  the groups route stacks CONSECUTIVE blocks, so the same 8 frames land whole
  inside one group (53% of a group of 15, a per-pixel MAJORITY, which survives
  rejection — `intake-frame-qa.md`), and the compose is a plain mean. The
  identical ratified decision rejects the transient on one route and ships it
  on another. The class is wider than rejection: any "X is a small fraction of
  N" argument is invalidated by any change that alters N. When ratifying,
  write the ROUTE and the count the argument assumes; when changing a route,
  grep the ratified decisions for fractions — **and grep the REVERTS, not just
  the keeps**: the `--desky` revert's 12.4%-vs-0.4% headline
  (`calibration-flats.md`) is measured on the single-pass denominator, and
  nothing says what it measures on a 5×100 groups build.
- **A BASENAME IS NOT A FILE IDENTITY IN A MULTI-SESSION CORPUS — AND A CHECK
  THAT COMPARES ONE IS BLIND EXACTLY WHERE THE NAMES REPEAT.** Per-session
  directories make repeated names the NORMAL state (19 `skyflat*.fit` masters
  carry 12 distinct basenames; `dark_master.fit` exists in every session), so
  "do these two files share a filename" answers yes precisely when two
  different files are being confused — and two masters can agree on every
  other stamped field too (same `STACKCNT`, same `NAXIS1`), so
  name-plus-count collapses as well. **An identity test must compare
  something that cannot repeat: CONTENT.** IMPLEMENTED: the FITS `DATASUM` is
  computed in memory (siril strips `DATASUM`/`CHECKSUM` on any load+save,
  measured) and carried on the product beside the readable name — ESO's
  `CAL1 NAME` + `CAL1 DATAMD5` shape — by `scripts/stack/stamp_headers.sh`.
- **THE STAGED CORPUS IS NOT THE CORPUS. CHECK `datasets/` BEFORE DECLARING A
  CORPUS LIMIT — the reflex is to check `sessions/`, and the reflex has been
  wrong twice.** `sessions/` holds the nights whose raws are on the rig;
  `datasets/` holds the tracked records for every night ever ingested — twice
  as many. Both errors produced confident NEGATIVES: "all 12 staged sets are
  one target at 2.5 s, so there is no exposure lever" and a STOP calling a
  different exposure "an acquisition change" — while july27/set-01 and set-02
  are already recorded at 3.0 s (282 and 253 frames, same optics, same
  target), a 1.44× lever in L². **The cost of the reflex is a "cannot be done"
  written into a record about work that can.** Re-staging existing data is
  cheap by the owner's standing statement and is not an acquisition ask.
  **AVAILABLE IS NOT WORTH RUNNING — the lever WAS used and the question is
  CLOSED AGAINST it (`star-shape-optics.md`, the co-varying-systematic entry:
  contamination scaled with the lever; exposure and night perfectly aliased).
  Do NOT re-open the july27 exposure comparison.** The OFFSET shape is
  separately dead needing no frames: `t_eff = t_nom − δ` implies δ = 1021 ms
  against shutter latencies of O(1–10 ms), so multiplicative is the only
  surviving shape and no mechanism produces one.
- **A PROVENANCE STAMP BUILT AS AN ALLOW-LIST IS A DENY-LIST FOR EVERY KEY IT
  OMITS — siril `stack` propagates the REFERENCE member's ENTIRE header, so a
  route's leak surface = (reference header) − (keys siril recomputes) − (the
  allow-lists that route applies).** Measured on the four-night corpus: five
  reference-specific keys survived onto the composite and into `_spcc`
  (`PIPEREV`, the singular `CALSET`, `DATE-OBS`, `GRPSIZE`, `FILENAME`), the
  leaks REFERENCE-keyed, not first-member-keyed; what siril recomputes was
  verified, not assumed (`STACKCNT`/`LIVETIME` equal the member sums;
  `EXPSTART`/`EXPEND` carry the true span beside the false `DATE-OBS`). The
  sharpest instance: the commit that built the composite stamp tuple named
  CALSET inheritance as the defect it fixes, added the plural `CALSETS`, and
  never replaced the singular — its own worked example still shipped on the
  product. The acquisition block inherits the same way and is nothing-false
  until a corpus mixes values (july27's 3.0 s is the standing `EXPTIME`
  trigger). Census, values and route-class differences:
  `datasets/corpus/piperev_inheritance.json`; fix status:
  BACKLOG:`composite-header-identity` (the composite tuple has shipped; the
  rgbcomp/standard-route half and the next-compose read-back remain).
