# BACKLOG

Open work: what it is, why it matters, and the test that closes it. Completed work
is not carried here — it lives in the operating docs and in `git log`.

**Items are keyed by SLUG, never by number.** Reference one by slug from code or docs — e.g. ``BACKLOG:`render-ladder` ``. Numbered items were the previous scheme and
they failed twice, silently: items 19 and 20 were closed and removed, their numbers
were reused for unrelated work, and seven code/doc sites went on pointing at the
wrong content with nothing to catch it. A slug cannot be recycled by accident, and a
reference to a deleted item is greppable.

An item earns its place by mattering to the REPO. Per-dataset findings live in
`datasets/<session>/<set>/`, mechanism lessons in
[`docs/dead-ends.md`](docs/dead-ends.md), tool facts in [`TOOLS.md`](TOOLS.md).
Anything unintelligible, superseded, or true of only one wiped dataset is deleted
rather than carried.

---

## `removal-conditions` — the register (contract-mandated)

Every divergence from the standard workflow carries a removal condition
(`CLAUDE.md`). **A condition nobody re-checks is a divergence that never ends** —
that has already cost real work: `star_shape_profile.py`'s condition had fired,
nothing re-checked it, and the stale metric invented a false anomaly a whole session
chased. Re-check on a tool version change, on a rig change, and before working any
item below.

**Rules for this table, because it failed as a register twice.** (1) Every
divergence declared in code belongs here — a `REMOVAL CONDITION:` in a docstring
that is not in this table is invisible, and an audit found FOUR of them plus one
adaptation with no condition written at all. When you add a
divergence, add the row in the same commit. **A later artifact-first sweep found
THREE MORE and they needed TWO DIFFERENT detectors**: `pa_convention.py` and
`psfex_compare.py` declared a condition with no row — findable by joining
`grep -rln 'REMOVAL CONDITION'` against this table — while `psf_calib.py` declared
**nothing at all** and is structurally invisible to that join, though three rows
cite its number. **Declared-but-no-row and no-condition-anywhere are different
holes; a detector for the first cannot see the second.** (2) Every row carries the date it was
last CHECKED against reality, not the date it was written — "not fired" with no
date is the exact state that let a fired condition sit unnoticed. (3) Status is
the current verdict and its evidence, not a history of the divergence; mechanism
narrative belongs in `docs/dead-ends.md` and the script's own docstring.
**AND A COMPRESSION PASS HAS ALREADY MEASURED HOW MUCH OF THIS TABLE VIOLATES IT: about 5%.**
A full read of the 37 rows then present (6,961 status words) found narrative in **TWO** — both
recounting how a finding was reached, both with the mechanism already homed. The
other 35 are verdicts, measurements and tool names, which is what it COSTS to
record those 37 divergences with their evidence. **A long row is not a violating row.**
The recognisable case is a row that RECOUNTS HOW A CONCLUSION WAS REACHED whose
mechanism lives in `docs/dead-ends.md` or `TOOLS.md` — i.e. prose that RESTATES
what a destination already carries. **Three cheap proxies for that were each built
and each calibrated against rows whose true answer was known, and each FAILED:**
word count (the longest row yielded 20%, a row 40% its size yielded 45%), number
density, and narrative-marker frequency — which INVERTED, scoring zero on the row
that compressed most. **Restatement is a semantic judgement and triage is a
reading pass.** So: read before cutting, cut only prose whose content is homed
elsewhere, keep every number in its cell, and **stop rather than push** — grinding
a further 18% out of a measurement row means deleting evidence to move a number.
(4) A condition that depends on the DATA (disk, sensor size) is re-checked per
dataset, and says so.
(5) **CHECK THE ROW AGAINST THE ARTIFACT, NEVER AGAINST WHAT YOU REMEMBER THE
ARTIFACT CONTAINS — a name you recall is a DESCRIPTION, and descriptions are what
a full artifact-first sweep of this table kept finding wrong.** MEASURED over that
sweep: the header keys the provenance stamp writes were guessed as
`LENSMOD`/`LENSFIT`/`OPTMODEL` and **all three were wrong** (`stamp_headers.sh:142`
writes `DISTMODL`/`DISTA`/`DISTB`/`DISTC`/`DISTNORM`/`DISTSRC`); a join of the
declaring files against this table false-positived on `siril_run.sh` because the
row writes the brace form `siril_run.{sh,py}`; and two sweeps of "the sub-stacks"
disagreed 78 vs 93 because one anchored its glob to `groups_*/` and the other did
not. **So: open the file, run the command, `df` the disk — and state the
DENOMINATOR with any count, or the next reader's sweep will not reproduce it.**
(6) **A COMPOUND CONDITION IS TWO CONDITIONS AND MUST BE REPORTED AS TWO.** A row
whose trigger reads "X, or Y" can have Y fire while the status reports X — measured
twice here in one sweep (the `header_provenance_lines` row's BACKFILL clause had
fired at 93/93 stamped; `constancy_fit.py`'s `rl -loadpsf=` clause had fired and the
route is declared DEAD BY MEASUREMENT two hundred lines away). **And a disjunct
naming an event that is DEFINED NOWHERE is not a condition at all** — "or the trail
question closes" appeared in exactly two places in the whole tree, both of them the
conditions themselves, so it could never be evaluated and therefore never fire.
(7) **THE DATE COLUMN IS A SEPARATE EDIT AND NOBODY MAKES IT.** MEASURED: two rows
carried re-verification evidence dated later than their own `last checked` column,
because the session that re-verified them wrote the finding into the STATUS and
left the column alone. Move the column in the same edit as the evidence. And when a
row is confirmed only by its `--selftest` passing rather than by re-probing its
condition, say so and LEAVE the date — selftest-green and condition-re-probed are
different statuses, and collapsing them is how a stale condition survives.
(8) **A HEADLINE NUMBER MUST EXIST IN A RECORD — a result that was paraphrased is
a result that was NOT RECORDED.** MEASURED: this table and a script docstring both
published *"χ²/dof 35.6 becomes ~1.1 on frame-based errors"*, and an enumeration of
every `chi2_per_dof` in the cited record returns six values with **nothing in
[1.0, 1.2]** — in either revision of it, so it was not regenerated away. The real
within-binning pairs are 35.60 → 1.81 and 40.95 → 1.57, and the published pairing
crossed two different binnings. It entered in the same commit that wrote the record
contradicting it. This is the registry's *"a check whose output is paraphrased is a
check that did not run"* one level up, and **it survived because it failed in the
FLATTERING direction** — against an assumed null of 1, "1.1" reads as a near-perfect
fit and nobody re-checks a number that says the model fits. **Before quoting a
figure in a row, open the record and find it.**
(9) **A CONDITION MUST BE EVALUABLE — "has this fired?" must have a determinate
answer — and that is a SEPARATE axis from whether it has fired or whether its
status text is true.** A full sweep of the condition column (the 37 rows then present, read
programmatically, so none skipped and none taken from the status text) found
**31 clean and four defect shapes**:
- **UNEVALUABLE / UNDEFINED TERM** — the trigger names an event nothing in the tree
  defines, so nobody can say whether it happened. Two instances, both now rewritten
  to name artifacts a reader can open: *"or the trail question closes"* and *"or
  cross-set composition leaving the project's goals"*.
- **MALFORMED** — the trigger names a capability nobody outside this project wants,
  so it can never occur. *"A tool reports trail length L directly"* was the measured
  case; the field measures sub-PSF elongation as an ellipticity and stops.
- **SOFT EDGE** — the trigger is a real event with no threshold, so a reader cannot
  tell whether it is already satisfied. *"whose bias is characterised"* — by whom,
  to what precision, published where?
- **SELF-GATED — evaluable, determinate, and INERT.** The trigger retires only on an
  experiment THIS PROJECT must run, so no external event will ever satisfy it and it
  sits "not fired" forever unless someone schedules the work. `DRIFT_FRAC_MIN`'s
  measured knee and `run_undistort_groups`'s quality cost are the two here. **Not a
  defect — but a register full of self-gated conditions looks maintained while
  nothing in it can ever retire, so mark them: the trigger is a DECISION TO WORK,
  not an event to wait for.**

**AND EVALUABILITY IS NOT PERMANENT — A MEASUREMENT CAN SPLIT A CONDITION'S TERM.**
*"darktable gains FITS I/O"* was a clean binary until darktable 5.4.1 was measured
to READ FITS and not write it; the condition became half-satisfied with its text
silent on which half. **It was in TWO rows, and both needed the same edit** — the
correction unit is the CLAUSE wherever it lives, not the row where the problem was
noticed. **Re-check evaluability whenever a measurement touches a term a condition
names.**

| divergence | retires when | last checked | status |
|---|---|---|---|
| `coverage_frame.py` largest-all-covered-rectangle search over Siril `stat` boxes (+ `web/verify_framing.py --channel=`, and the `--regdata-dir=`/`--tag=` A/B flags on `run_undistort_groups.sh`) | an official tool reports, headless, the largest fully covered axis-aligned rectangle of a registered union — or a coverage map ON the union's own canvas that `verify_framing.py --map` can consume | 2026-08-29 | **not fired — RE-CHECKED 2026-08-29: the SECOND disjunct is ONE HEADER CARD away, not a structural gap, and the canvas half of it is now MEASURED on this rig rather than read from `SWarp -d` — SWarp pins its output grid from a `.head` exactly (`datasets/corpus/smear_attribution/swtaper_probes.json`, `P2_output_head_pins_grid`; this table's `swarp_compose.sh` row); the count-vs-weight semantics stay UNCHECKED. NEW CONSUMER, load-bearing: the corpus baseline slot seeds its five regions INSIDE this instrument's rectangle and REUSES it on every compare — `datasets/corpus/baseline.json` `measures.placement`: coverage record `stack_july31+aug06+aug09+aug14_full_coverage.json` (sha 0fbc185c…), rect (Siril crop args) [852, 436, 6816, 4578], floor 27.15 Green, grid 40×26 — because a `framing=max` union's canvas corners are EMPTY (`docs/dead-ends/siril-behaviors.md`).** The disjunct asks for *"a coverage map ON the union's own canvas that `verify_framing.py --map` can consume"*, and the reason recorded below — that `coverage_probe.sh` builds its map through `register -2pass`, so its canvas is not the product's — is now true only of `coverage_probe.sh`. **SWarp removes that objection:** it resamples onto a SPECIFIED output WCS and writes its weight map on THAT canvas by construction (`WEIGHTOUT_NAME`, `CENTER_TYPE`, `IMAGE_SIZE`, `PROJECTION_TYPE`, verified by `SWarp -d`), and it postdates this row's previous check. **The format question `TOOLS.md` left open is ANSWERED and the answer is NO as things stand:** `verify_framing.py` reads the scale from the map's own **`COVSCALE`** card and REFUSES a map without one; a SWarp weight map carries none. **So: does not fire, blocked by a missing card rather than by the canvas.** Two limits travel with it — SWarp answers the SECOND disjunct only (the maximal-rectangle search stays in-house), and a weight map is a WEIGHT, so whether its values mean member COUNT under `--map-min` is UNCHECKED. Original probes, all standing: Siril `stat`/`bg` measure a selection or the whole frame and know nothing about coverage; `seqapplyreg -framing=` picks min/max/COG framings and reports no covered region. The repo held the VERIFY half and the CONSUME half (`finish_render --crop-record`) but nothing that PROPOSED a rectangle, so on a union nobody had hand-drawn a box for, the pinned crop-before-background order could not be followed at all. Every pixel and per-box number is Siril's (`boxselect`+`stat`, one load); in-house is the grid bookkeeping and the maximal-rectangle search. REPORTS ONLY — writes an UNVERIFIED record, crops nothing, exits 0 even when nothing clears the floor. **`--selftest` falsifies on a planted fixture:** the frame is recovered exactly (FITS **[160 100 480 250]**), Siril's own `crop` re-reads it at **Green Min 87.9 against an 80.0 bar** with the box deliberately ASYMMETRIC in y so a flipped origin goes RED, and both known failure modes DO fail — the clipping-channel floor covers **0 boxes**, and a mere-non-zero floor grows the rectangle **480x250 -> 640x350** by swallowing the ringing band. It caught a real defect on first run: Siril prints `Sigma: -nan` on a zero-variance box and the numeric-only regex silently dropped it (`docs/dead-ends.md`), a latent copy of which `starlight_preservation.py` also carried. **`--tag=` is a divergence only because arm builds need a work dir:** without it an arm lands on the CONTROL's members and the resume guard skips every group, so the arm looks built and IS the control. No arm is live today (every arm and scratch dir disposed at e4468e1, 73 items); the flag stays because the mechanism does — the next arm build needs it on its FIRST run, not after. |
| `member_separation.py` cross-match + zone medians | an official tool reports headless member-to-member POST-REGISTRATION positional residuals across a sequence (a scriptable Siril registration-residual map, or a PixInsight equivalent) | 2026-08-29 | **not fired — REBUILT, and the rebuild found the instrument had been measuring NOTHING.** It cross-matched the REGISTERED copies, and `seqapplyreg -framing=max` on a variable-size sequence gives each output its OWN origin (MEASURED **611.9 px** apart on the 28-member union; two members of one set shared **67 of 2000** stars within 12 px, **1721** once re-based). It now reads the members plus the homographies `register -2pass` wrote into the `.seq` and bins by MEMBER-OWN field radius: **0/378 pairs unmeasured against 378/378 before**, in 12 s, monotone **0.22/0.48/1.30/2.43 px** median. **SELFTEST RUN, PASSED AND RE-RUN against real members** (`sessions/aug06/work/l1_msep/in` — scratch, not preserved — 13 members under `register -2pass`): known displacement **3.086 px** measured back as **3.086 px**, and the incident reproduces — **89 cross-matches without the re-basing against 1905 with it** — so the defect that blinded this instrument still fires on demand. Both reproduce to the digit. A bare `--selftest` REFUSES loudly: it cannot run data-free, and exiting into the docstring read as a pass twice. **SCOPE THE ZONE NUMBERS — they are the ones a reader reaches for.** They are member-to-member DISAGREEMENT in the reference member's frame under `-2pass` homographies, NOT the delivered star shape of an astrometrically composed product and not a residual the shipped route leaves. T2 on the 13-member aug06 union: **0.924 / 2.618 / 5.399 / 5.729 px** (median over 78 pairs, centre/mid/outer/corner) while that product's delivered major axis at matched member-own radius runs **0.04-0.25 px above its members'** (`datasets/aug06/corner_work/`). Do not read one as the other. **THE THRESHOLD LAYER IS REMOVED (user-ratified): no PASS/WARN/BLOCK, no `--accept-separation`, no exit-6 abort, always exits 0 — it MEASURES, it does not gate.** Three measured grounds: the quantity is a sum of two terms and the compose makes one of them (two healthy sets read **1.12 / 0.95 px** composed among themselves and **3.02 / 3.38 px** inside a 41-degree 28-member sequence); the bands were anchored on the BROKEN instrument (re-measured on the fixed one: 0.14/0.21/0.38/1.23/3.04/3.28 against 0.144/0.194/0.352/0.934/2.991/2.112, which moves the user-PASSED pair out of PASS); and a band fires on every real compose, which trains the operator to bypass it. **The attribution this clause waited on has RUN (re-checked 2026-08-29): the union's surviving band is MEMBER-BORNE and the compose is exonerated** — canvas-tied residual −0.052 ± 0.040 px major / +0.011 ± 0.011 roundness (−1.28 / +0.99 SE, permutation p 0.208 / 0.328; `datasets/aug09/smear_work/rho_march.json`, `primary_top30.T4`), the carrier the members' own entry-side columns, since removed by member selection (`docs/corner-smear-member-selection.md` §2–3). **With the clause discharged the status is: a MEASUREMENT with no threshold, and none follows from the attribution** — the shipped selection keys on each member's own `findstar` station profile (`run_member_crop.sh`), not on member-to-member positional disagreement, so a band on this quantity would gate on a term the attribution found the compose does not own. Removal condition unchanged; the state-change detector (`compose-homography-smear`, ordered work 6) remains the one consumer that would want a RELATIVE trigger from this measurement, unbuilt. Siril `register` prints WITHIN-sequence residuals only; nothing reports where two members each place the same star. Built because both prior instruments are MEASURED BLIND: corner `findstar` FWHM ranked a FAILING union (**4.95 px**) above the visually clean control (**5.29 px**), and `seqtilt` read **0.34 px** off-axis for the FAILING union against **0.40** for the PASSING one. |
| optics/calibration FITS stamp (`header_provenance_lines`) | the warp stops being a TIFF round trip, so the model rides through natively (darktable gains a FITS **WRITER** — it has READ FITS since 5.4.1 (MEASURED: full-resolution export from a 6064x4040 `.fit`), and `.fits` output returns *"unknown extension"*, so the round trip is held open by the write side ALONE. The earlier wording *"gains FITS I/O"* became AMBIGUOUS the moment that was measured: half-satisfied, with the text not saying which half, or Siril `register -disto=` — BACKLOG:`native-solve-and-sip`) | 2026-08-22 | **not fired.** The warp is still Siril `savetif32` -> darktable -> Siril `convert`, which carries no FITS header; the blocker is the WRITE side alone — darktable 5.4.1 READS FITS and cannot WRITE it (measured, `stamp_headers.sh` row below). **The row's former second clause — the one-time `backfill_substack_provenance.sh` — FIRED and is EXECUTED: retired 2026-08-22.** Measured 2026-08-14: **93 of 93** `sub_*.fit` under `sessions/` stamped (`DISTMODL` present), 0 un-stamped; state the denominator — a glob anchored to `groups_*/` reads 78, every `sub_*.fit` under `sessions/` reads 93. The script is deleted; its three consumer sites (compose gate message, combine-contract §1/§4-consumer note) point at recovery from git history for an archive restore predating the stamp. Load-bearing why the stamp exists: the lensfun user DB is global, unscoped, single-valued machine state nothing reverts, so a sub-stack that cannot state its own optics cannot be composed safely later — 13 aug06 members under 3 different models once composed into a doubled union and nothing in the product could see it |
| `derive_compose_ref.py` (the multi-night registration reference, `run_undistort_compose.sh`) | siril chooses a sequence reference by a stated, deterministic, order-independent rule of its own — at which point AUTO already computes this | 2026-08-19 | **not fired — measured, siril takes INDEX 0.** Ten `compose_gate_*.json` records at 13/17/22/25/52/77 members all read `reference_member = s_00001`, and an auto arm measured **0 differing pixels of 98,194,977** against an explicit `--ref=1`. So the reference is whatever sorts FIRST: appending a night re-bases nothing, reordering the session arguments re-bases everything. **The divergence is DETERMINISM, not quality** — no choice of reference is materially better at the deliverable: SPCC absorbs the balance **64x** (B/G delta -0.2167 at the compose, -0.0034 after), and `-framing=max` includes every member either way so the sky union is identical, leaving a +0.19% bounding-box change that is empty corner. Fires only on a multi-night set; single-night keeps AUTO, so no single-night product moves. Order-independence is live-tested on the real 77-member corpus (forward and reversed session order pick the SAME member at the same 0.1622 deg) and `--selftest` falsifies all eight rules |
| `compose_preflight.py` + the compose's astrometric post-assert (`run_undistort_compose.sh`) | siril itself refuses to register a sequence whose members carry no usable solution, or the chain has no star-pair path left to fall back to | 2026-08-14 | **not fired — and the EVIDENCE this row used to carry is now FALSE, while the verdict stands.** It read *"it fires on today's corpus — the union's own members (`groups_set-0*_pinned/sub_*.fit`) carry NO WCS, so the guard refuses them at exit 3."* MEASURED 2026-08-14: **no `groups_*_pinned/` dir exists on this rig** (the 18 surviving group dirs are `groups_set-0N` plus `_l1arm`/`_l1ctrl`), and the members that DO survive carry WCS — `sessions/aug06/work/groups_set-01/sub_01.fit` reads `CTYPE1 = RA---TAN-SIP`, `CRVAL1 = 304.4330331279676`, so the guard would ACCEPT them. **The premise is inverted, not merely stale: a corpus statement outlived the corpus.** The condition itself is untouched — siril still does not refuse an unsolved sequence — so "not fired" is correct on the tool, not on the members. Grounds: `seqplatesolve` needs every member solved with SIP order >= 2 and siril reports NOTHING when they are not — it registers what it can and exports a finished-looking product. Measured cost of the silent fallback: roundness 0.458 against 0.974 on the 28-member union. Both halves are live-tested — refusal (exit 3) on unsolved members, acceptance plus "astrometric registration + per-member undistortion CONFIRMED" on solved ones, and `--selftest` falsifies the header checks |
| `solve_field.py` hint-contradiction gate (position > 2x the hint radius, scale outside +-20% of the header nominal; exit 9) | the solver itself refuses a solution that contradicts a supplied position/size hint — today the `astrometry` engine takes hints as search guidance only, and the blind fallback discards them entirely, so a hinted attempt that fails is followed by an unconstrained one whose answer nothing compares back | 2026-08-20 | **not fired, and it FIRES on the one measured false solve.** MEASURED: the corpus union's hinted attempt failed on a seam-contaminated framing=max canvas and the blind fallback shipped RA 6.03 Dec -65.10 at 12.96"/px, logodds 22.3 — against the product's own header pointing RA 309.77 Dec +41.70 (siril's WCS field centre, inherited from the already-solved members, so independent of this solve) and a 17"/px family. Nothing downstream could catch it: siril SPCC ran to COMPLETION on that WCS and produced plausible K factors (R 1.000 G 0.592 B 0.817, 1790/5153 stars kept). Thresholds are budgeted from mechanism, not fitted — integer-mm EXIF focal, XPIXSZ rounding, infinity-vs-marked focal and the TAN centre-to-corner ratio (1.066 at 28.6 deg) sum under 10%, doubled to 20%. The refusal's own numbers reproduce exactly (115.4 deg, 0.7405x). SCOPE LIMIT: 108 records (`solve_sub_*.json` under `sessions/`) are per-member sub-stacks whose headers carry FOCALLEN/XPIXSZ but no RA/DEC, so only the scale leg and the logodds warning are live there. **TWO CORRECTIONS FROM A 2026-08-14 RE-VERIFICATION, and the first is the sharper.** (1) **THE REPLAY IS NOT REPRODUCIBLE FROM THE RECORDS FOR THE CASE IT MATTERS ON.** `hint_available` and `header_scale_arcsec_px` — the fields whose own code comment says they exist so *"a later audit replays it from the record instead of re-deriving the nominal from the hint's 0.6x end"* — are ABSENT from the false-solve record: they shipped WITH the gate, so every pre-gate record lacks them (**134 of 268** carry them, 2026-08-20). **The mitigation postdates the case it was built to make auditable**, and the audit had to do exactly the re-derivation the field exists to prevent. (2) **THE SCRIPT'S CENSUS CLAIMS DEFER HERE** — the three-site count disagreement is resolved by de-duplication (comments + the floor WARNING cite this row; the `0ec22a8` shape). **CENSUS 2026-08-20** (`find` `solve_*.json` repo-wide; distinct = unique rounded ra/dec/scale/logodds so dual-writes collapse): **268 records + 1 keyword dump, 176 distinct solves, 82 scale-replayable, 34 hinted**. Position: hinted solves land 0.0002-0.274 deg from the hint against 30 deg allowed; the false solve sat ~110 deg out. Scale, each record against its OWN nominal: 69/82 inside 0.96-0.99; every outlier attributed — the 1.0344 CROP product (nominal 16.488), one 0.9593 sub-stack, and TEN aug14 mount_probe green-window solves at 1.0206-1.0665 (the probe-scale-artifact family — BACKLOG:`frame-qa-order-dependent-scale`); max |deviation| 6.65% = ~3x inside the +-20% band, denominator per-product. Logodds over the 176: 22.3-573.6, exactly THREE below 100 — the 22.3 false solve, and two REAL floor-class (59.5 `j31-3+a06-3_full_onemodel`, 63.0 `corpus4_full_wnbstack`), so "every real solve clears the floor" is REFUTED and the floor stays a WARNING by measurement, not just design |
| `route.py` `DRIFT_FRAC_MIN = 0.05` — the route key's floor | a MEASURED knee exists: an undistort-vs-homography A/B on this mechanism at two drift fractions below 0.25, closing where the removable term drops under the route's own irreducible residual (0.25 px off-axis aberration at full depth). The key itself (sky excursion / field) is mechanism-derived and does not retire with the floor | 2026-08-14 | **not fired — and the floor is EVIDENCE, not a knee.** No knee has ever been measured; the residual is monotonic in drift ("scales with TIME SPAN, not frame count"). 0.05 is the smallest excursion at which the term is measured present — the 9-min/~310 px window arm, `drift_frac` 0.051, whole-frame majFWHM 3.87 px against the full span's 4.74 px at 0.247. The corpus's 12 real sets measure 0.083–0.201, nearest 1.66x the floor, so nothing sits near it. The key UNDER-COUNTS twice (the `-framing=min` trim runs 1.16–1.29x the pure translation; a probe windowed inside the longest continuous run drops the re-aim excursion), which is why the floor sits at the bottom of the measured range rather than inside it. Fire-tested and RE-VERIFIED 2026-08-14 (nothing building, `__pycache__` cleared, `git diff` EMPTY afterwards and the file md5-identical to baseline): flipping the constant moves all five consumers together and back, selftest ratio 1.66x -> 1.38x and 0.05/1.66x restored. **THE PARENTHETICAL'S MECHANISM WAS WRONG AND IS CORRECTED — the instruction is safe, the reason given for it is not what happens.** It read "a same-length edit needs `__pycache__` cleared or importers read stale bytecode". MEASURED: a same-length edit ALONE does not trigger it — 0.05 -> 0.06 propagated immediately with a stale `.pyc` present and no clear. **Python invalidates on (mtime, size)**, so reproducing the trap needs BOTH held fixed (`touch -r` after a same-length edit), which does fire it: source read 0.07 while the importer returned 0.06. Clear the cache anyway — it is conservative and free — but do not expect a same-length edit by itself to hide the change |
| `cfa_control.py` in-house per-ρ-bin binning + least squares on the RAW CFA lattice | retires with `constancy_fit.py`, whose named alternative it tests — **and that row's condition was REPLACED 2026-08-14 after the original FIRED, so this one cascades onto the NEW condition (the sibling contract being provided elsewhere), not the dead `rl -loadpsf=` route** | 2026-08-14 | **CASCADE NOTE 2026-08-14: the condition this row inherits changed.** The `rl -loadpsf=` route it ultimately gated is dead by measurement on three grids, so the ORIGINAL inherited condition had fired unnoticed; the replacement is scoped to `contract_check()`, and this file is one of the two siblings that check enforces — `cfa_control.per_bin` must build rows the shared `constancy()` accepts, which is what caught a real regression that every other check was structurally unable to see. **not fired — and it REFUTES the demosaic alternative.** Siril does every pixel op (`convert` with NO `-debayer`, `seqsplit_cfa`, `findstar`); in-house is the binning, the spin-2 bookkeeping and the least squares. Reads no pixel. **Pre-registration committed at `90cf6ee` BEFORE the run, with no result attached.** **OUTCOME 1, the free null, PASSES:** the two green sub-lattices agree at χ² 3.00/3, max axis difference 2.73° — the CFA lattice injects no directional term. **OUTCOME 3: the rotation and the gate failure SURVIVE with no interpolation anywhere** — both greens reject a constant axis (χ² 15.8/2 and 37.9/2; constancy fit χ²/dof 28.2 and 46.7). The alternative held that a ρ-dependent demosaic term produces the non-constancy; remove the demosaic and it persists, so the demosaic is not necessary to produce it. **OUTCOME 2 differs and is NOT attributed:** CFA axes sit 2–10° above debayered (χ² 27.1/3 and 23.3/3), ambiguous between the demosaic and severe undersampling (S 0.83→0.415, across Kannawadi's 0.5) — pre-registered as unattributable and left so. **A TOOL TRAP WORTH THE ROW ON ITS OWN: `split_cfa`'s channel order cannot be read off BAYERPAT.** The parent carries RGGB and split_cfa emits in raster order, which reads as channels 1 and 2 being the greens; the DATA says 0 and 3 — cross-matched magnitudes give ch0–ch3 a −0.005 mag offset (MAD 0.115, 706 stars) against 0.28–0.85 for every other pair, and those two share a background median and MAD where the others do not. Reading the header would have compared R against B and called it the green null. DECLARED DEVIATION: 3 bins not the pre-registered 5, forced by the half-sized grid's ~1000 stars/frame against ~7000 — the debayered arm was re-binned to 3 as well so the comparison is like-for-like, and outcome 1 passes at either threshold |
| `frame_depth.py` in-house 40-frame re-run of the per-ρ-bin axis + constancy fit (extends `constancy_fit.py`) | retires with `constancy_fit.py` — **that row's condition was REPLACED 2026-08-14 after the original FIRED, so this cascades onto the NEW condition (the sibling contract being provided elsewhere), not the dead `rl -loadpsf=` route** | 2026-08-14 | **CASCADE NOTE 2026-08-14: the condition this row inherits changed**, for the reason given in the `cfa_control.py` row above; this file is the other sibling `contract_check()` enforces (`frame_depth.per_bin` must build rows the shared `constancy()` accepts). **not fired — and it REMOVES the one-frame condition the verdict used to carry.** Siril does every measurement (`convert -debayer` + `findstar`, the same call verbatim); in-house is the binning, the spin-2 bookkeeping and the least squares. Reads no pixel. **At N=40 the verdict no longer flips on DSC_6239: with it INCLUDED, axis constancy χ² 69.5/4 and fit χ²/dof 53.1 both REJECT** (excluded: 686.7 and 129.4). The 5-frame "nothing rejects" was a small-sample artefact — one anomalous frame is 20% of five and 2.5% of forty. **And "first frame of a run" is NOT a class:** only the first frame of the SET is anomalous (axis −36.91° at robust z = −25.7, next most deviant of 40 is −1.4), while the other four group-starts read +16.29 to +17.50 against a reference mean of +17.39 ± 1.52 — group-starts minus 6239 differ from the rest by −0.44 ± 0.43°, 1.0σ. So the exclusion used across this thread removes exactly one frame, not a systematic. Subset bracket EXACT: restricted to the original five it reproduces `constancy_fit.json` to the digit. Sample is designed, not convenient — four early-in-run and four spread frames from each of the five groups. `--selftest` asserts the class test detects a PLANTED offset and does NOT detect an absent one |
| `constancy_fit.py` in-house per-ρ-bin spin-2 binning + the 3-parameter constancy least squares (`C = f·T + K`) | **CONDITION REPLACED 2026-08-14 — the original FIRED and the file must NOT be deleted.** New condition: the sibling contract this file enforces is provided elsewhere — i.e. `contract_check()` is no longer the thing keeping `cfa_control.py` and `frame_depth.py` conformant with the shared fitter, **or** a tool reports a FIELD-CONSTANT PSF component over a star list | 2026-08-14 | **THE ORIGINAL CONDITION FIRED AND NOBODY FIRED IT** — this row read "not fired" while the route it gated was declared dead 200 lines away in this same file (`corner-fix-landscape`: "the FIX-classified route is DEAD … NO on three independent grids"). "Closed either way" was written for exactly that outcome. The `star_shape_profile.py` failure this table's header warns about, recurring. **DELETION IS THE WRONG DISPOSITION, on a CI fact:** `contract_check()` lives in this file and is the **`constancy_fit` check of the `run_guards.sh` roster** (cited by NAME — this table's own header records ordinal citation as having failed twice, and the ordinal written here was 18 against an actual 21), wired to the pre-push hook — deleting the file silently removes a gate, the one that catches a sibling drifting from the shared fitter. **The current purpose arrived with NO condition**, this table's stated worse case entering as the old one retires; hence the replacement condition. **NOT ESTABLISHED, and deliberately not written as "likely":** whether this code is load-bearing for `one-sided-band`'s unattributed radial term. That trace has not been run. **THE FINDING — it corrected the error model of every per-bin number in this thread.** A star-level bootstrap inside one pooled population understates the per-bin fixed term by a median **5.76x (range 4.1-9.2x)** against the five raws as INDEPENDENT realisations, inflating chi2/dof ~20x **WITHIN ONE BINNING**: `rho_equal` **35.60 -> 1.81**, `equal_count` **40.95 -> 1.57**, both at **dof 7**. **The previously published "~1.1" is WITHDRAWN — it was never in any record** (every `chi2_per_dof` in `constancy_fit.json` enumerated: those six values, nothing in [1.0, 1.2], absent from BOTH revisions, reproduced by two sessions) **and it was paired against 35.60, which belongs to the OTHER binning.** At **nu = 4** the null of a reduced statistic is nu/(nu-2) = **2.0**, so 1.81 sits BELOW its null: the frame-based errors are CONSERVATIVE, not "right". Why it survived, and the paraphrase lesson it produced: `docs/dead-ends.md`. **Retracts the fixed term's "10 to 20 sigma" rotation:** it SURVIVES at chi2 74.6/4 with frame-based errors but only with DSC_6239 excluded; all five frames reject nothing (chi2 3.0/4). Every star, PA and FWHM is Siril `findstar`'s; the trail WCS is astrometry.net's; the conversion is `psf_calib.json`'s fitted kappa. In-house: binning, spin-2 bookkeeping, least squares. Reads no pixel. `--selftest` recovers a planted (f, K) at two settings and asserts a ROTATING residual CANNOT be fitted by a constant (chi2/dof **20136**). |
| `psf_calib.py` in-house synthetic trailed-star FIXTURE renderer + straight-line fit — the SOURCE of the conversion constant κ = 0.49374712819727373 | **CONDITION NEWLY AUTHORED 2026-08-14 — PENDING OWNER RATIFICATION, because this divergence shipped with none:** retires when a tool reports a SECOND-MOMENT shape measurement whose thresholding/windowing bias is QUANTIFIED in a citable source, or measurable on a planted fixture, such that the (2.3548^2/12)*L^2 identity applies with a stated correction rather than an estimator calibration (the earlier *"whose bias is characterised"* set no threshold — characterised by whom, to what precision — so a reader could not say whether `source-extractor`'s `A_IMAGE` already qualifies), making the `major²−minor² = (2.3548²/12)·L²` identity exact rather than estimator-calibrated. `source-extractor`'s `A_IMAGE`/`B_IMAGE` (*"Profile RMS along major axis"*) are the INSTALLED candidate; the open question is thresholding/windowing bias, not availability | 2026-08-14 | **ROW ADDED 2026-08-14, AND THIS IS THE REGISTER'S OWN "WORSE CASE": an adaptation with NO written condition at all — not a docstring condition missing a row, but no condition anywhere.** It was invisible to the declared-but-no-row detector for exactly that reason, so two detectors are needed and only one existed. **Three rows depend on its number** — `constancy_fit.py`, `kappa_transfer.py` and `coherent_trail.py` all cite `psf_calib.json`'s fitted κ as the load-bearing conversion — and `kappa_transfer.py`'s row calls its fixtures *"the same standing as `psf_calib.py`'s"*, equating it to a row-carrying divergence inside a row while giving it none. **The register covered the test and missed the thing tested.** Not fired. Siril `findstar` measures every synthetic star with the same call the real measurement used; in-house renders the fixture and fits the line; no deliverable pixel is read. **Why the OBVIOUS condition was rejected as malformed:** "a tool reports trail length L directly" can never fire — the field has no customer for a sub-PSF trail length (asteroid/streak tools take the rate as an INPUT or target trails many PSF widths long, and weak lensing stops at ellipticity), so nobody is coming. A condition only this project wants is not waiting, it is malformed |
| `kappa_transfer.py` in-house fixture renderer + straight-line fit (tests whether the trail conversion κ survives a realistic base profile) | a tool reports the trail-to-anisotropy conversion for its OWN fitter — **or** no OPEN item in `one-sided-band` / `corner-fix-landscape` still depends on a κ-converted quantity (the testable replacement for the old "or the trail question closes") | 2026-08-29 | **NOT FIRED — RE-EVALUATED 2026-08-29 with the sibling rows (`coherent_trail.py`, `fit_ptlens_joint.py`) as ONE clause: recovery is settled (`corner-fix-landscape`: no route on this rig recovers corner detail — a closed verdict) and a selection route shipped, so `corner-fix-landscape`'s remaining open half (procurement or acceptance of the lens's SYMMETRIC radial softening) consumes NO κ-converted quantity; `one-sided-band`'s Open 1 — the unattributed radial term at 5.9 SE — still does, through the pinned prediction's trail ratio 0.3502 ± 0.0080 → ZP deficit 0.570 (κ-converted) and the trail-term separation inside the spin-2 fit. One open consumer = the disjunct has not fired.** And it ANSWERED the premise it was built for. κ = 0.49374712819727373 reproduced **EXACTLY** (ratio 1.000000, arm A — the harness did not move); the discrete renderer costs **0.14%** (arm B); arms C/D swap the profile and re-randomise placement at matched density, over a shared L ladder, 7×7 supersampling, phase randomisation, amplitude range, Poisson stream, 56 px grid and one `findstar` call. Base is **PSFEx** `psfex_work/deg3/g_00005.psf` (PSF_FWHM 2.401 px at PSF_SAMP 0.511) cut PERPENDICULAR to its major axis — the untrailed base, since a linear smear convolves along one axis only and no untrailed star exists on this rig; its minor-axis FWHM 1.89–2.11 px BRACKETS `psf_calib`'s 2.010 px Gaussian, so the substitution changes SHAPE and not width. Tool probed FIRST and rejected with a measurement, not an opinion: Siril `makepsf stars -savepsf=` ran headless over 322 bright non-saturated stars but returned **9 px × 3 px** at half maximum, a 3:1 elongation ~4× broader than the real stars (2.4 × 2.0 px). **CONDITION REWRITTEN because the old second disjunct could not be evaluated, so it could never fire:** *"or the trail question closes"* was defined nowhere — `grep -rn "trail question"` over BACKLOG/TOOLS/dead-ends returned only the two conditions themselves. Not *nobody wants the capability* (the Oracle's `psf_calib` case) but **nobody can tell when the event happened**; row 54 is the control that makes it a defect rather than pedantry — its question IS closed, it carries no closure disjunct, and "not fired" is correct there. First disjunct separately still open and now sourced: **no tool reports a sub-PSF trail length** — the probe and its better-formed replacement live in `TOOLS.md` Tier 5. `--selftest` asserts the segment adds exactly L²/12 anisotropy at three lengths and puts it in the cross term at 45°; it **FAILED FIRST**, catching two real bugs in this file's own kernel — both recorded in `docs/dead-ends.md`. Reads no deliverable pixel; the frames are FIXTURES, same standing as `psf_calib.py`'s |
| `coherent_trail.py` in-house spin-2 coherent-anisotropy estimator + per-ρ-bin joint fit | Siril (or any tool in `TOOLS.md`) reports a coherent spin-2 moment over a star list — **or** no OPEN item in `one-sided-band` / `corner-fix-landscape` still depends on a coherent-anisotropy quantity (the testable replacement for the old "or the trail question it serves closes") | 2026-08-29 | **RE-EVALUATED 2026-08-29 as one clause with `kappa_transfer.py` / `fit_ptlens_joint.py`: NOT FIRED — `corner-fix-landscape`'s open half (procurement / acceptance) consumes no coherent-anisotropy quantity now that recovery is settled and selection shipped; `one-sided-band`'s Open 1 (the radial term, 5.9 SE) still does — its trail component IS this estimator's coherent projection (0.5798 on the reference frames, Gate 1A below) — so one consumer stands.** **CONDITION REWRITTEN for the same defect as the row above: the old second disjunct named an event defined nowhere in the tree, so it could not be checked and could never fire.** The replacement names an artifact a reader can inspect. Verdict unchanged — **not fired** — probed: `findstar` reports per-star major/minor/PA and nothing aggregate; no siril command reports a coherent moment. Every star, every PA and the CONVERSION constant are Siril's (the constant is `psf_calib.json`'s FITTED 0.49375, measured by pushing planted trails through the same `findstar` call — **not** the analytic identity 0.46209, which understates the prediction by 6.41%); in-house is only the spin-2 bookkeeping, the cut ladder and the least-squares fit. Reads no pixel. REPORTS ONLY, exits 0. **Built because the composition was MISSING while its components survived** — the estimator behind this thread's central number existed only as inline code in a lost transcript. Gated on reproducing recorded numbers before producing new ones, and it does: Gate 1A nine numbers on `psf_work/f{1,2,3}.lst` (coherent magnitude 0.586908 = 0.5869, axis 9.1573 = 9.16, projection 0.579819 = 0.5798, frac-negative 0.29329 = 0.294 …); Gate 1B the full cut ladder AND all five per-raw values at once (0.4615/0.7573/0.8026/0.7951/0.8154, ladder 0.7264/0.7276/0.7251/0.7131); Gate 2 the planted control in `--selftest` (n 2735 = 2735, projection 1.3403 = 1.3403, axis 4.9034 = 4.9). **The fixture failed twice before it passed, both times in the FLATTERING direction:** the planted sites are in ARRAY order where `findstar` reports FITS order, so as-is matching recovered 85 of 2765 as chance coincidences and read the REAL population as planted (exact relation, measured: x+0.5, (H−0.5)−y, median residual 0.000 px both axes; the selftest now asserts the unflipped match must FAIL); and `injected2`/`sites2` is the representative frame while the lower-numbered pair is the discarded first-frame anomaly, pinned by a check that it still reads its −29.3° axis |
| `zero_point.py` in-house ZP arithmetic (`MAG_VT − m_inst` and its median/flatness fit) | an absolute throughput calibration for this camera+lens exists on the rig, **or** the corpus gains two nominal exposures on one night through the same optics | 2026-08-13 | **not fired, and the question it served is CLOSED as UNDERPOWERED for a STRUCTURAL reason — the measured ZP and that reason are now in `TOOLS.md`, since a zero point for this camera+lens outlives any one experiment.** astrometry.net does the solve, the field↔catalogue MATCH and supplies the catalogue magnitude itself — `solve-field --tag-all` propagates the Tycho-2 index's `MAG_VT` tag-along into the `.corr` table, so there is **no in-house catalogue reader and no cross-matcher**; in-house is only the subtraction, the median and the flatness fit. Reads no deliverable pixel (the one pixel read is a DIAGNOSTIC on the FITS data range, explicitly outside the bright line). **VERIFIED not assumed, and it is what makes the result valid:** Siril `findstar`'s `mag` is a TOTAL-flux magnitude, −2.5log10(A·2π·sx·sy), offset −0.0001 with MAD 0.0027 — a peak magnitude would have been wrong by 1.76 mag, three times the signal, and nothing in the column name says which it is. `--selftest` carries a fixture that CAN fail, including the check that a planted 0.57 mag deficit moves the ZP by 0.57 |
| `pa_convention.py` in-house spin-2 azimuthal decomposition of PSF ellipticity + the planted-orientation fixtures | an official tool reports, headless, the azimuthal decomposition of PSF ellipticity components over a field (a scriptable Siril whisker/e1-e2 map, or a PixInsight equivalent) — re-check on any Siril version bump | 2026-08-14 | **ROW ADDED 2026-08-14 — the condition was declared in the script (`pa_convention.py:92`) and had NO row, which register rule (1) forbids and which made it invisible.** Not fired: Siril reports per-star shape and no decomposition of it; PSFEx exposes no position-resolved shape in any output (`TOOLS.md`), so the in-house part remains the geometry and the fits over Siril's own measurements. **It is load-bearing beyond its own thread** — it generates the 443–531 px decentred ELLIPTICITY-field centre that `one-sided-band`'s commensurability paragraph turns on, and that is a different quantity from `fit_ptlens_joint.py`'s decentred POSITIONAL/distortion centre at (−6, +14) px. Imported by six sibling instruments, so a change here reaches all of them; `constancy_fit.py`'s `contract_check()` is the guard that a sibling still conforms |
| `psfex_compare.py` in-house re-derivation of shape from the PSFEx field model (basis-order transcription + spin-2 fit) | the in-house spin-2 field fit is retired or replaced as the field-model instrument — this file exists only to check one against the other and has no independent life | 2026-08-14 | **ROW ADDED 2026-08-14, AND ITS CONDITION REWRITTEN — declared at `psfex_compare.py:38` with no row (rule (1)), and the declared text was MALFORMED: it described the file's future relevance ("if PSFEx is adopted… this comparison inverts") rather than naming a testable trigger.** The form above can be checked by reading what the field-model instrument is. Not fired. Every PSF model is PSFEx's; in-house is only the re-derivation, which is UNAVOIDABLE and not a choice — **PSFEx exposes no position-resolved shape in any output** (XML gives min/mean/max over the `PSFVAR_NSNAP` grid; the `.psf` gives coefficients), so any position-resolved comparison must re-derive moments from the model. Two traps live in that re-derivation and both are recorded in `TOOLS.md`: the basis order is `[1, X, X², Y, XY, Y²]`, X-major within each power of Y, and PSFEx's own reported ellipticity is a MOFFAT fit while re-derived adaptive moments read ~0.84x a planted value — a definition difference plus a calibrated estimator factor, not a defect in either tool |
| `anomaly_audit.py` in-house streak kernel | a tool detects/classifies transient streaks | 2026-08-05 | **not fired** — probed siril 1.4.4's own command list: `cosme`/`find_cosme`/`find_hot`/`seqfind_cosme` are cold/hot PIXEL defect correction; no streak, trail, satellite or Hough command exists. Standing check: an extreme-elongation QA flag ADJACENT to an audited crossing is the same object until shown otherwise |
| `star_shape.py` two-frame duplication | Siril exposes a headless single-image tilt | 2026-08-05 | **not fired** — `tilt` IS listed by `help` but REFUSES in a script ("This command cannot be used in a script: tilt", probed on-rig). Siril cannot sequence one frame, so the duplication stands. A `help` listing is not evidence of scriptability |
| `star_stations.py` fixed-station `findstar` medians | a tool reports a headless LOCAL star-shape map | 2026-08-05 | **not fired** — `inspector` (the aberration-inspector grid, the closest native thing) also refuses in a script, probed the same way; `seqtilt` is centre-vs-corners and blind to the drift-aligned band this exists for |
| `shape_at_sky.py` sky-addressed `findstar` medians (the combined-product acceptance instrument) | an official tool reports headless star-shape statistics for a WCS-addressed subregion of a solved image | 2026-08-10 | **not fired** — same gap family as `star_stations.py`, at SKY positions instead of sensor stations: the compose-registration defect class lives at fixed sky on a combined canvas and no tool measures there headless. Every fit is Siril `findstar` (open gate), placement is header-only WCS, summarisation is medians of the tool's own numbers; box placement is VERIFIED per run by the tool's own per-star RA/Dec (the crop y-flip trap fired on first use and was caught by exactly that check). Calibrated against the recorded union A/B: reproduces 4.383/0.458 (defect) and 2.448/0.968 (control) to the third decimal on the kept reference |
| fitted lensfun entry, PINNED per lens/focal (`lens_models.json`) | an upstream lensfun entry measured for THIS unit at infinity focus, or a chain that consumes the model another way (Siril `register -disto=` with a trustworthy source — probed 2026-08-09, it is a SHARED-solution facility, not per-image reprojection, so it does not retire this) | 2026-08-09 | **not fired — and RE-INSTATED.** The 2026-08-08 retirement ("condition fired: the chain consumes the model another way — per-set optical-state records") is REVOKED: the per-set method was refuted at its root (`docs/dead-ends.md`) and reverted. Its founding number, aug06/set-01's 0.82 px off-axis, is a COMPOSE artifact — set-01's own groups read 0.40-0.45 px under that same pinned model. Per-set models broke the combine (2.99 px within a night, 5.34 px across nights) where one shared model composes clean and is what every accepted combine here ever used |
| lensfun user-DB strip of the fitted lens's `<vignetting>`/`<tca>` (`install_lens_model.sh`, enforced per set by `verify_lens_card.py`, which declares this same condition in its own docstring) | darktable honours a style's lens `op_params` | 2026-08-11 | **not fired — and no longer re-checked by hand.** `lens_preflight.py --require-profile` now runs `verify_lens_card.py` EVERY set (11.1 s of a 25.5 s preflight on 6064x4040 frames, so unconditional), because the strip is machine-local state `lensfun-update-data` reverts and the two cheaper checks are blind to it: reinstating the focal=70 aperture=4 `<vignetting>` pair by hand left the warp-happened proof and the pinned-coefficient assert both GREEN while the card read a 4219 ADU corner-vs-centre step on a 30000 ADU field (tol 1.0). Fire-tested both ways on aug06/set-01 (refuse -> re-strip -> 0.000 ADU). **NEVER RUN `install_lens_model.sh` WHILE A BUILD IS IN FLIGHT** — it rewrites the GLOBAL lensfun DB, which every live darktable warp is reading, so a QA or verification step that calls it mutates state a four-hour arm build depends on. Installing an IDENTICAL model still risks a torn read, and the DB is the one piece of unversioned machine state on the undistort route (nothing reverts it; `lensfun-update-data` wipes the strip outright). Caught live, no damage: a queued pin-verification was killed on firing and the DB verified after — all 56 XMLs parse, the fitted entry intact, no stale builder lock. Verify a pin from the build's OWN per-group output instead, which tests the model that actually ran rather than re-installing one. That test also found the restore path itself broken — the installer's idempotence test asked only about the distortion line, so it reported "already installed" and exited 0 on a block whose vignetting was back; it now re-strips and says so |
| per-set sky flat (`build_sky_flat.sh`, NOT de-skied) | a matching REAL flat for the set | 2026-08-12 | **not fired** — the flatless route, and it works: july31 sets measure 0.40/0.49/1.03/1.17% corner spread (a scratch rebuild from raws reproduced the experiments-ledger figures to the digit). The flat still converges to `sky x V`, so the object carries the sky's spatial profile — the MECHANISM is REAL and open, and NOT fixed by de-skying the source frames (`--desky` was a 31x regression; `docs/dead-ends.md`). **Its MAGNITUDE is UNMEASURED**: the long-quoted 3.11% / 241 sigma has no tracked record, and the catalogue-free re-measurement is now a registered DEAD END — the linear mode is degenerate under translational drift and the atmosphere is sensor-fixed for a fixed camera, so the pre-registered flat prediction failed 4 of 5 across 12 sets (`datasets/aug09/corpus_object_tilt.json`) |
| `flat_odd_component.py` in-house odd/even decomposition about frame centre + the plane fit, over Siril `fdiv` ratios and `stat` regional medians | a real flat exists for the set — the SAME first disjunct as the `build_sky_flat.sh` row above, so the two retire together — **or** the `sky × V` defect is measured absent on this rig, at which point the odd component is no longer a thing to watch | 2026-08-14 | **ROW ADDED 2026-08-14 by the first MECHANICAL run of rule (1) (`scripts/qa/check_removal_conditions.sh`); the condition was declared at `flat_odd_component.py:55` and had no row, which rule (1) forbids.** **WHY EVERY PRIOR SWEEP MISSED IT, and it is a reusable tell:** the basename DOES occur in this file — once, inside the `flat_differential.py` row's STATUS, naming it as the adopted primary instrument — so a join asking "does the name appear in the table" returns COVERED. **A mention is not a row**; the join must be on the DIVERGENCE column, and the under-reporting direction is the dangerous one because it reads as "everything is covered". Not fired: the flatless route is the mission and the `sky × V` defect is open and uncorrected. Siril does every pixel op and every measurement (`fdiv` at a recorded scalar, never `idiv` — which clips at 1.0 silently; `stat` regional medians); in-house is the odd/even decomposition, the plane fit and the bookkeeping. Reads no deliverable pixel, gates nothing, always exits 0. Load-bearing for `calibration-evidence`, which recorded this instrument as MISSING before it was built, and for the L/R-is-SKY finding (edge dipole sweeping +0.436 → 0 → −0.385 across the corpus, impossible for a sensor-fixed term) |
| `object_tilt.py` cross-match + weighted LS of magnitude against sensor position (+ `object_tilt_control.py`, `object_tilt_null.sh`, `object_tilt_corpus.py`) | an official tool reports a headless POSITION-DEPENDENT photometric solution across overlapping exposures with no external catalogue — SCAMP's photometric mode is the candidate, or a PixInsight equivalent | 2026-08-12 | **not fired — the divergence is UNFILLABLE on this data, so the code survives only as the record of that.** **SCAMP IS INSTALLED** (`~/.local/bin/scamp`, 2.10.0); the long-standing "no apt candidate on this distro" is FALSE and the verdict never rested on it. **The condition still cannot fire, and that is now sourced from the BINARY rather than a source reading:** `scamp -d` exposes no photometric analogue of `DISTORT_DEGREES`, so its photometric solution is one scalar per exposure per instrument (`TOOLS.md` Tier 3b — cross-referenced, not restated). Siril `seqpsf -wcs=` measures one fixed pixel area in every image, m = -2.104 against +3.55/+5.05/+3.63 (`docs/dead-ends.md`). Every pixel op and every flux is Siril's; in-house is the cross-match and the fit. MEASURES and gates nothing, always exits 0. `--selftest` falsifies in process: a planted +0.100 mag is NOT recovered on a pure-translation panel (-0.046 +- 0.0001, lever 0.00 px). `object_tilt_null.sh` runs it on REAL data — interleaved halves, predicted tilt zero, measured **+49.1 +- 5.0% at 11.8 sigma**. |
| `flat_differential.py` subtraction + straight-line fit (+ `flat_differential_arms.sh`, `flat_differential_report.py`) and the two A/B flags on `run_undistort_pipeline.sh` (`--regdata=`, `--nonorm`) | an official tool reports, headless, the position-dependent photometric RATIO FIELD between two ALIGNED exposures — i.e. the subtraction and the fit, not merely two flux lists. `source-extractor` dual-image mode gives the two lists and is installed; it does not close this | 2026-08-12 | **not fired.** Probed: no Siril command compares two images photometrically by position (`fdiv`+`stat` gives the pixel field and IS adopted as the primary instrument, via the shipped `flat_odd_component.py`; `seqpsf -at=` is applicable on an aligned pair, unlike the drifting case, but measures one star per invocation from a selection — the same per-star call as `psf`, with an unvalidated parser). Every pixel op and every flux is Siril's (`split`, `findstar`, `psf` at a forced radius against its own local annulus); in-house is the subtraction of two tool measurements and a weighted straight line. MEASURES and gates nothing. `--selftest` falsifies the mechanism in process on the SAME pure-translation panel that killed the absolute measurement: the absolute fit returns **-0.046 ± 0.0001 with the lever collapsed to 0.00 px** where the differential returns **+0.0999 ± 0.0001 with a 1548 px lever**, and blinding the position axis turns step 1's own acceptance check RED, restoring it turns it GREEN. **The builder flags are NOT cosmetic**: `register -2pass` re-chooses the reference frame from image quality and the CALIBRATION changes that choice (MEASURED, one knob: skyflat_set-05 → reference image 1, canvas 4896x3616; skyflat_set-01 → image 2, canvas 4887x3641), so without `--regdata` an A/B has two knobs and the arms are not pixel-comparable. Default path unchanged by both flags; `--nonorm` stamps STACKNRM/DIAGARM on the product |
| `grid_ramp.py` least-squares plane over Siril `stat` box medians | an official tool reports, headless, the FITTED low-order background ramp of an image as NUMBERS — a slope or plane coefficients, not a subtracted image, not a background-model image, not a star-shape tilt | 2026-08-12 | **not fired.** Probed on this rig rather than reasoned about: siril `bg` returns ONE scalar for the whole image; `subsky`/`seqsubsky` fit a polynomial or RBF and SUBTRACT it, reporting no coefficients; `tilt`/`seqtilt` compute "the FWHM difference between the best and worst corner truncated mean values" — a STAR-SHAPE measure, not a background level (and `seqtilt` IS scriptable, so the GUI-sibling search was run, not assumed); GraXpert 3.0.2 `-bg` writes the background MODEL as an IMAGE; ASTAP CLI-2026.07.16 `-analyse`/`-extract` report HFD, star counts and per-star rows only. Siril measures every box median; in-house is the plane. Fills the instrument gap `docs/dead-ends.md` names — the grid-fitted ramp slope is the registry's CANDIDATE replacement for four-corner spread, which is "not a gradient measure on a structured field" — and it REPORTS ONLY: no thresholds, no verdict, and swapping an acceptance measure stays a user ratification. `--selftest` falsifies the mechanism in process: blinding the position axis drives a planted +0.15 %/1000px to 0.000000 and turns step 1's own acceptance check RED, restoring it turns it GREEN; a uniform card through the whole Siril path reads slope 0/0 (−7e-15) so LEVEL cannot masquerade as GRADIENT; and an ORDERING CONTROL re-measures the two extreme boxes in their own Siril invocations, since the 63–77 medians are parsed from one run in emission order |
| `starlight_preservation.py` per-cell floor vs Gaia catalogue regression on an external lattice | an official tool reports, headless, the AGREEMENT between a star catalogue's predicted diffuse surface brightness and an image's own measured per-region background — the JOINT, not the two halves | 2026-08-12 | **not fired. BASIS NOTE (2026-08-14): the 2026-08-12 date stands deliberately — the 2026-08-14 sweep confirmed only that this instrument's `--selftest` PASSES inside `run_guards.sh`, and did NOT re-probe the tool landscape below.** "Selftest green" and "condition re-probed" are different statuses and collapsing them is how a stale condition survives; the date column tracks the second. Probed on this rig at the date shown, each with the command run rather than the help read: Siril `stat`/`bg`/`bgnoise` measure the image only (`bg` is one scalar for the frame) and `conesearch` returns the catalogue only — and at this field size it is not even usable, 20.6 deg radius at G<=17 against TAPVizieR, killed at 600 s with no output; `jsonmetadata -stats_from_loaded` ignores a selection and stats the whole frame; `source-extractor` 2.28.2 `-CHECKIMAGE_TYPE BACKGROUND` writes a local background MAP (1.7 s on 4907x3598) but compares it to nothing; GraXpert 3.0.2 `-bg` writes a background MODEL image; ASTAP CLI-2026.07.16 `-analyse`/`-extract` report HFD, star counts and per-star rows. Every pixel and every per-cell number is Siril's (`boxselect`+`stat`, PROBED identical to the `crop`+`stat` route to every printed digit in ONE load); the catalogue aggregate is the ESA Gaia archive's own server-side GROUP BY; in-house is the lattice, the WCS projection and the fits. MEASURES and gates nothing — no threshold, no verdict, always exits 0. `--selftest` falsifies the mechanism in process on a planted fixture: 299.14 recovered against 300.00 planted at R2 0.99993, an orthogonal predictor returns R2 0.00017, Siril `subsky 2` collapses the planted relation to 26.9% (RED) and the pristine copy re-reads 299.14 (GREEN); a catalogue control checks the archive's binned sum against its ungrouped total (agree to 1e-6) and the plane/pole flux contrast (6.3x). It caught a real defect on its first run — `boxselect` counts y from the TOP, and the mirrored lattice still recovered 54% of the planted relation at R2 0.30, which is exactly the kind of half-right number a fixture-free instrument would have shipped |
| GraXpert `-correction Division` synthetic flat | a matching real flat exists | 2026-08-05 | **not fired** — not adopted; no pipeline script calls it. Vignetting-only fallback |
| `baseline_guard.py` derived summaries (corner spread, edge dipole) over Siril `stat` | a tool reports a headless PRODUCT-level regression verdict against a stored reference | 2026-08-29 | **not fired** — nothing does. **Two owner-directed rule changes, both keeping it a no-regression RECORD:** the centre-median rows are ADVISORY while the product's `STACKNRM` differs from the baseline's (re-armed on re-seed; 18 of the 19 tracked baselines carry `addscale` — the 17 per-set seeds and the corpus slot `datasets/corpus/baseline.json` (seeded e4468e1; the slot itself ef3f08b); aug06/set-00's, a spare-frames bucket the chain never built, carries no `STACKNRM`; `git ls-files | grep baseline.json` = 19 on 2026-08-29); the absolute corner-spread ceiling WARNS on a CROSSING only — product over it, accepted baseline under it: a `CEILING … EXAMINE THE IMAGE MANUALLY` block, exit 0; a baseline seeded over it was examined at seed and carries the verdict in its note, so a product staying over it prints nothing (owner-approved 2026-08-29 after aug14/set-05's 4.381 seed made the block print on every run) — after it misfired on aug14/set-05's field (a Milky Way band puts a true 4.38% spread on the product; the same measure read 8.2% on the never-seeded `-output_norm` twin; the guard cannot separate sky structure from a flat error). The over-baseline (+1.0), dipole and level rules stay hard; `--selftest` (33 cases — 11 compare-rule + 22 explicit-slot, the four added at 4f9e462 for identity-before-measurement — in `run_guards`) keeps the `--desky` class (0.4→12.4%) going RED through the over-baseline rule. WIRED into `run_set_chain.sh` as the last step: it measures the finished product, and a regression exits **8** (a user decision, like the mount/route stops) without blocking or rewriting anything. Also a web stage for seeding/re-seeding. It is a no-regression RECORD, never a quality gate — a deliberate improvement fails it and the human re-seeds with a note. Blind spot to state when reading a PASS: both measures are STACK corners, which `docs/dead-ends.md` calls self-fulfilling for flat contamination, so it cannot see the open `sky x V` object tilt |
| `snr_regions.py` in-house SNR ratio over Siril `stat`/`bgnoise` | a tool exposes headless REGIONAL SNR | 2026-08-05 | **not fired** — `stat` and `bgnoise` are whole-image/selection; no regional-SNR command in 1.4.4. Every input number is the tool's; only the ratio is in-house. *(Was missing from this register until 2026-08-05.)* |
| `fingerprint.py` derived trail/drift geometry | an official tool reports headless trail/drift geometry with a declared-vs-measured mount cross-check | 2026-08-05 | **not fired. BASIS NOTE (2026-08-14): date held deliberately — the 2026-08-14 sweep confirmed only that `--selftest` PASSES in `run_guards.sh` and did NOT re-probe the tool landscape.** Same distinction as the `starlight_preservation.py` row: selftest-green is not condition-re-probed. No solver here exposes inter-epoch drift rate vs sidereal. The record schema and the STOP-on-CONTRADICT contract stay wherever it lands. *(Was missing from this register until 2026-08-05.)* |
| `inspect_stage.py` + `cull_report.py` robust-z per-frame flagging | a tool ships headless per-frame outlier flagging over its own registration metrics (SubframeSelector-class, scriptable) | 2026-08-05 | **not fired** — siril has `seqstat` (per-frame statistics to a file) and `select`/`unselect`, but no outlier GRADING over its own regdata. Persisting the tool's regdata is not a divergence and stays regardless. *(Was missing from this register until 2026-08-05.)* |
| prebuilt-master ingest (`run_pipeline.sh` `<session>/calib/`) | never — this is a supported INPUT class, not a divergence. **DECLARED NON-DIVERGENCE: it is trivially evaluable (it cannot fire) and is retained as an explicit marker, but it must not be counted as a live divergence — the table's row count overstates them by one** | 2026-08-05 | **CONDITION WRITTEN 2026-08-05, previously absent.** The code calls it "the adaptation for master-only data", which made it look like an unconditioned divergence. It is not one: a corpus that ships masters instead of raw calibration is a data class the repo accepts. What IS a stated limit: such masters carry no exposure/gain/filter headers, so the filename token is the whole identity and the exposure match is unverifiable — printed per run. Raw calibration dirs take precedence |
| 16-bit in four instruments (`coverage_probe.sh`, `run_frame_qa.sh`, `fit_lens_model.sh`, `run_lunar_pipeline.sh`) | the leg stops terminating in an integer/8-bit product | 2026-08-12 | **not fired** — each re-verified: `coverage_probe` switches to `set32bits` before its sum stack, `run_frame_qa` saves no product at all (analysis-only register), `fit_lens_model` terminates in `savetif8` for Hugin, `run_lunar_pipeline` pins it on its convert+seqcrop stage step only. Exemptions are enforced by name in `check_bitdepth.sh`, which reports FOUR |
| `run_undistort_groups.sh` group composition (one extra interpolation pass) | a measured quality cost of the extra pass at established magnitude (the along+1300 ledger resolving AGAINST groups), or the combine unit stops being CROSS-SET — i.e. `BACKLOG:final-best-percent-pass` and the cross-night combine contract are both closed or withdrawn (the previous wording, *"cross-set composition leaving the project's goals"*, named no observable state and was UNEVALUABLE; "the project's goals" occurs twice in the tree and never as something a reader could see having happened). **SELF-GATED on its first disjunct** — the measured cost retires only on a from-raws A/B at established magnitude, and the floor it is judged against is MEASURED ZERO at both tiers — the per-set REBUILD (`rebuild_repeat_floor_set01`, at `git show c7db472:datasets/july31/experiments.jsonl`: rf1/rf2/accepted bit-identical) and the corpus COMPOSE (`repeat_floor_corpus_compose`, `datasets/corpus/smear_attribution/repeat_floor.json`: compose, solve, SPCC and judge PNG bit-identical to the canonical, 58 stations Δ 0.000) — so a station delta between two arms is the knob's, never repeat noise, and the along+1300 groups gain (0.12–0.18 px) sits above a zero floor; whether that gain is worth the pass is an owner reading, not a measurement | 2026-08-29 | **RE-CHECKED 2026-08-29, second disjunct: NOT FIRED, and it is half-satisfied in the direction that KEEPS groups.** `final-best-percent-pass` is SHIPPED at the MEMBER tier (the portion rule is the corpus chain) and explicitly NOT closed — its per-FRAME cross-session surface is the open half; and the cross-night combine contract is more load-bearing than when this row was written: the canonical is a 77-member, four-night compose (NMEMBER 77, STACKCNT 8349, ledger 123–128). First disjunct unchanged (self-gated on the A/B; its floor is the measured zero above). **CONDITION REWRITTEN — the old trigger (free disk ≥ the single-pass peak) fired and was judged the WRONG condition: disk cannot retire groups.** Single-pass deletes the sub-stacks the cross-set combine composes and crops to `-framing=min` (composing per-set finals is a registered dead end), so a big disk buys nothing back; groups is the STANDING route (`force_route`), single-pass operator-only (`--route=single`, printed FORCED). Quality, two consistent accounts: the item-scoped one-knob A/B (60 frames even-stride) is **NULL — the route does not cause the one-sided band** (9/9 stations within 0.05 px majFWHM / 0.014 roundness; the band sits in BOTH arms at 1.27x/1.24x); the full-depth ledger records a small along+1300 improvement UNDER groups (0.12–0.18 px, direction replicates across two sets and two group sizes) whose proposed baseline mechanism was FALSIFIED (g250 landed outside the interval) and whose magnitude is NOT rebuild variance — the rebuild floor RAN and measured ZERO (`rebuild_repeat_floor_set01`, at `git show c7db472:datasets/july31/experiments.jsonl`; swept in the july31 ledger reset) — but stays UNESTABLISHED against the post-hoc station-selection objection that entry itself raised. Peak math stays data-dependent, `W × H × channels × 4 × 2`: 560 MiB/frame at 6064×4040 OSC, 8 MiB mono astrocam, 1378 MiB at 61 MP |
| `scripts/lib/siril_run.{sh,py}` flock-serialized siril-cli invoker | flatpak fixes the instance-dir lifecycle race, or Siril invocations stop being per-frame process spawns (e.g. pyscript batching) so there is no window to collide in | 2026-07-28 | **not fired** — the race is a flatpak lifecycle bug, unfixed at 1.4.4/current flatpak, and every builder still spawns one siril-cli per step. MEASURED serializing: 4 concurrent jobs 1.74 s vs 0.47 s single (3.7x, matching serialized 1.88 s not concurrent 0.47 s), 3 of 4 reporting the wait; shell and python share ONE lock (cross-language test 0.93 s = 2x single). The lock is per-USER so it serializes across sessions on this rig. Every participant is now adopted: the one hold-out (the JWST scripts — cut with JWST, `git show e40c007:scripts/jwst/`) went with the JWST cut, so `check_siril_invoke.sh` carries no exemption and any bypass FAILS rather than being reported |
| `scripts/lib/siril_run.sh` bounded LAUNCH retry (`SIRIL_LAUNCH_TRIES`, default 4) — the complement the invoker's own note reserved for "a non-participating third party" | `flatpak run` stops failing to launch an INSTALLED app: this rig completes a full-session build at `SIRIL_LAUNCH_TRIES=1` with no launch failure in any siril log | 2026-08-23 | **not fired** — NEW, and it exists because the failure was MEASURED here: two 1454-frame undistort builds died mid-chunk on `error: Extension org.freedesktop.Platform.GL.default has invalid merge-dirs` raised by `flatpak run` itself, Siril never started, and the builder died SILENTLY because the caller had redirected siril's output into a work-dir log. TRIGGER UNIDENTIFIED and the obvious hypothesis is REFUTED: 0 failures in 55 locked invocations under concurrent `flatpak list`/`info` AND concurrent `flatpak run`, 0 across the 100-minute build that then completed, no flatpak timers, repo untouched since 2026-07-18. The lock cannot prevent it — there is no second siril-cli to serialize against. Retry is SAFE because the launcher refused to start the app, so nothing ran. Discriminated on Siril's config-ini mtime, with the positive control the acceptance rule demands: siril-ran-script-OK exit 0 / ini CHANGED; siril-ran-script-FAILED exit 1 / ini CHANGED (must NEVER retry — it would repeat a whole stack); launch-failed exit 1 / ini UNCHANGED (must retry). BOTH failure branches exit 1, so the exit code alone cannot separate them; nanosecond `stat -c %y` prevents two runs inside one second aliasing the two. All four branches live-tested, disable knob included |
| `scripts/stack/stamp_headers.sh` — capture + `update_key` restore of the acquisition keys the undistort warp drops | the warp stage stops being a TIFF round trip: darktable gains a FITS **WRITER** — it has READ FITS since 5.4.1 (MEASURED: full-resolution export from a 6064x4040 `.fit`), and `.fits` output returns *"unknown extension"*, so the round trip is held open by the write side ALONE. The earlier wording *"gains FITS I/O"* became AMBIGUOUS the moment that was measured: half-satisfied, with the text not saying which half, or the distortion is consumed natively (Siril `register -disto=`, BACKLOG:`native-solve-and-sip`) so the keys are never dropped | 2026-08-14 | **not fired — but the long-stated reason is FALSE and the blocker is HALF the size this row asserted. darktable 5.4.1 READS FITS; it cannot WRITE it.** MEASURED both directions on two independent inputs: `darktable-cli <6064x4040 .fit> out.tif` exports, and the TIFF is **6064x4040** (exiftool) at 11.4 MB deflate RGB — the image was parsed, not fallen back on; `darktable-cli … out.fits` returns **`unknown extension '.fits'`** and writes nothing, and the format-plugin dir carries avif/copy/exr/j2k/jpeg/jpegxl/pdf/pfm/png/ppm/tiff/webp/xcf with no fits. So the round trip survives on the WRITE side alone. **This governs the shared condition wherever it appears** — the `header_provenance_lines` row above and BACKLOG:`native-solve-and-sip` both reason from the larger "no FITS I/O" premise; only a WRITER is missing. NOT tested: photometric fidelity of the read (dimensions and structure only). Values are Siril's own (read from the raw into the calibrated frame's header); in-house code only READS the header and hands them back to `update_key`. LIVETIME is the one derived value (n_frames × EXPTIME, both tool-sourced) because the per-frame EXPTIME Siril would sum was destroyed upstream. MEASURED restored on july27 set-01: 9 keys, LIVETIME 789.0 s = 263 × 3 s, and the solve regained its hint (`scale hint: 10.5-26.3 arcsec/px`, index scales 11-19, vs the prior blind WIDE-FIELD fallback) |
| `observer_frame_diversity.py` — per-group epoch DERIVATION + the corpus alt/az aggregation behind `datasets/corpus/observer_frame_diversity.json` | the sub-stack builder stamps each group's OWN epoch instead of the set's first `DATE-OBS`, at which point this reduces to an astropy coordinate transform anyone can run inline | 2026-08-14 | **not fired** — every group sub-stack of a set carries the SET's first `DATE-OBS` while its WCS centre has drifted up to 4.9 deg of RA (`docs/dead-ends.md`), so a group epoch must be recovered as `t0 + dRA/15.041 deg/hr`. astropy does the coordinate transform and the WCS read; in-house is the epoch derivation and the aggregation. Reads FITS headers and the tracked site record only, opens no pixel, gates nothing, always exits 0. **`--selftest` plants the defect on real data and asserts it REPRODUCES before asserting the fix catches it** — frozen clock 3.599 deg on a FIXED mount against 0.004 deg derived, 839x, and it fails if the improvement is under 5x so a silently-neutered derivation cannot pass. Regenerates the record it describes: `per_set` reproduces the hand-built original identically |
| `check_solve_records.py` record-vs-artifact pointing join | an official tool reports, headless, whether a plate-solve record's stated solution matches the WCS of the file it names | 2026-08-14 | **not fired** — probed: astrometry.net validates a solve against an IMAGE and knows nothing of our records; siril has no record concept; no tool joins a JSON provenance record to a FITS header. Reads headers and records only, opens no pixel, gates nothing, always exits 0. **It compares the record's field CENTRE against the target's own WCS EVALUATED AT THE CENTRE PIXEL, never `CRVAL`** — `CRVAL` is the tangent point (BACKLOG:`pointing-record-names-the-wrong-frame`) and MEASURED 1.662 deg from the centre on the one product that matters, against a clean-population spread of 0.012–0.364 deg over 22 pairs, so a CRVAL join carries ~5x the signal range as baseline error. `--selftest` falsifies on three arms, the third asserting CRVAL and centre-pixel are distinguishable so a comparand swap goes RED. Found one live case on 23 pairs: a record asserting RA 6.03 / Dec −65.10 for a product whose own WCS reads **115.4 deg** away, the false solve the registry already documents; no threshold was tuned, the gap is three orders of magnitude |
| `scripts/qa/fit_ptlens_joint.py` joint ptlens(a,b,c) + distortion-centre least squares with a projective nuisance | hugin/lensfun fit ptlens + distortion centre jointly against an absolute (catalogue) reference, or no OPEN item in `one-sided-band` / `corner-fix-landscape` still consumes a fitted distortion-centre quantity | 2026-08-29 | **ROW + CONDITION NEWLY AUTHORED — this divergence shipped with NONE** (no `REMOVAL CONDITION` literal anywhere, no row: the register's hole (b) NO-CONDITION-ANYWHERE, live in the tree until now; found by audit, the third instance beside `psf_calib.py`'s precedent). **RATIFIED (owner 2026-08-19).** Not fired: hugin's own d,e stage diverges (d = 6.3e6, the file's docstring). **RE-EVALUATED 2026-08-29 as one clause with the `kappa_transfer.py` / `coherent_trail.py` rows: of the two consuming items, `corner-fix-landscape`'s open half (procurement / acceptance) no longer consumes a distortion-centre quantity — recovery is settled and selection shipped — while `one-sided-band` still does (its commensurability paragraph turns on this fit's centred (−6, +14) px against `pa_convention.py`'s 443–531 px ellipticity centre); `compose-homography-smear`'s model questions consume this fit's candidate a,b,c as well, outside the clause's named items. One named consumer stands = not fired.** Not invoked by any chain; its model reaches production only through the explicit user-judged promote path (`fit_lens_model.sh`) |
| `scripts/darktable/cp_coverage.py` control-point radial-coverage analysis (rho percentiles + the pre-registered corner-true criterion) | hugin/lensfun report per-radius control-point support against the model's own normalisation, or the fitting route pins control points to a corner-inclusive station grid by construction | 2026-08-19 | **ROW + CONDITION NEWLY AUTHORED — shipped with none; hole (b); RATIFIED (owner 2026-08-19).** Not fired. Imported by `fit_lens_model.sh` only; the CLI's corner-support gate-exit has NO caller (README: imported, not invoked), so the exit-1 path is dead in practice and the analysis is promote-path evidence |
| `scripts/calibrate/spcc_cone.py` hand-rolled nside=2 nested ang2pix cover + `_tan_pix2sky` gnomonic step | (a) cover: siril 1.5 `healpix` adopted AND its pixel list verified to map to the zenodo chunk names (`siril-1.5`), or `astropy_healpix` adopted into this script's interpreter (installed in `/opt/astro-venv`, ABSENT from host python3 — `TOOLS.md`); (b) projection: the step moves to astropy WCS (already imported in this file; used for exactly this in `derive_compose_ref.py`) | 2026-08-19 | **ROW + CONDITIONS NEWLY AUTHORED — shipped with none; hole (b); RATIFIED (owner 2026-08-19). Two clauses, evaluated separately (rule 6). CLAUSE (b) FIRED the same day, owner-directed:** `_tan_pix2sky` deleted, the projection is astropy WCS built from the CD ALONE (the header's leftover PC+CDELT must be stripped — the dual-matrix trap this firing exposed — registry entry; the shed `wcs-dual-matrix-inject` item's close is `3eb669e`). MEASURED A/B, all 34 solved products: chunk lists identical 34/34; new centres agree with the headers' own OBJCTRA/OBJCTDEC at median 1.7 / worst 36.5 arcsec against the retired hand-roll's 17.8 / 151.6. **Clause (a) NOT FIRED** — the ang2pix cover stands until siril 1.5 `healpix` or astropy_healpix adoption. Consequence bound held: chunk SELECTION only, siril names any missing chunk loudly |
| `scripts/stack/lens_preflight.py` pinned-model XML scan — reads the lensfun user-DB XML as TEXT and compares literal a/b/c for the exact lens@focal (deliberately not the fuzzy matcher, which stays the tool's) | lensfun/darktable expose a headless query of the INSTALLED model's coefficients for a given lens@focal, or the chain consumes the model other than through the lensfun user DB | 2026-08-19 | **ROW + CONDITION NEWLY AUTHORED — the leg declared none; RATIFIED (owner 2026-08-19).** Not fired: Debian ships no lensfun query CLI (`lenstool` unpackaged, `python3-lensfun` exposes DB-path helpers only, `liblensfun-bin` update/adapter utilities only — the file's own probe list) |
| `scripts/calibrate/solve_field.py` coverage rescue rung — re-solves on the largest centred box inside Siril's measured covered rectangle when a blind solve starves | the astrometry.net engine accepts a detection-region/subarea constraint of its own | 2026-08-19 | **ROW + CONDITION NEWLY AUTHORED — the rung shipped (04678f2) with a LIMITS block and no retirement trigger; RATIFIED (owner 2026-08-19).** Not fired. Standing: a GENERAL SAFETY NET, not the fix for the corpus starvation (the reference derivation was — 03635b0); fires only on NO SOLUTION or floor-class, keeps the strictly better result, soft-by-contract |
| `datasets/aug09/smear_work/rho_march.py` member-attribution bookkeeping (WCS projection + least squares over the re-march's recorded `findstar` measurements) | an official tool reports, headless, coadd star-shape statistics attributed by contributing-member field position — or neither `compose-homography-smear` nor `one-sided-band` still consumes a member-attribution quantity | 2026-08-29 | **not fired — RE-EVALUATED 2026-08-29: the second disjunct is HALF-discharged.** `compose-homography-smear` no longer consumes a member-attribution quantity — its smear is attributed to the members and closed by member selection (`docs/corner-smear-member-selection.md`); `one-sided-band` still does: its open radial term cites this record's fitted member-radial slope (+0.435 px/unit ρ, reproducing corner_work's +0.53) as the member-own axis. One consumer standing = the disjunct has not fired. Same gap family as `shape_at_sky.py`/`member_separation.py`, at the attribution step: no siril/PSFEx/SCAMP surface decomposes a union's star shape by contributing member. Every star, FWHMx/FWHMy and amplitude is Siril `findstar`'s (the re-march's own lists); every geometry is the member's own solved WCS; in-house is the projection bookkeeping and the least squares. Reads headers and records only, no pixel, gates nothing, exits 0 (STOP conditions exit 3). Pre-registered BLIND, reading rules frozen before the run (`rho_march_prereg.json`); two controls fired blind on the author's geometry misconceptions — per-set ballhead roll, then meridian convergence dRA·sin(dec) — each verified header-only on all 12 sets before proceeding, both amendments committed before any band data was read. RESULT (`rho_march.json`, replicated at two depths): the union's surviving one-sided band is MEMBER-BORNE — composition-unexplained residual −0.05 ± 0.04 px major / +0.011 ± 0.011 roundness (−1.3/+1.0 SE, perm p 0.21/0.33); the left band samples members' own +x EDGES (pair Δsigned-x up to 1.89 of ±1) and member-own ρ is near zero and wrong-signed (−0.02), so the carrier is member +x-edge proximity (the exit-edge family), not raw radial optics and not the compose |
| `scripts/qa/member_solve_audit.py` per-set Theil-Sen scale trend + SIP-magnitude consistency check over each member's own solver-written WCS | the member solve itself refuses population-inconsistent solutions (e.g. `solve_field.py` growing a required neighbor-band check), making a post-hoc audit redundant | 2026-08-24 | **not fired — NEW, and its basis is measured, not doctrinal:** the astrometric compose registered members by unguarded blind solves, and both aug06+aug14 chains carried wrong-optimum fits — solved 16.791 arcsec/px in a 17.02–17.08 sibling population with SIP terms ~10x the siblings', edge-of-field sky positions bowed 31.5 px (median star-matched, n=1655) against the same member re-solved under a tight `--scale-band`, healthy member moved 0.000 px. A FIXED band is wrong (refraction drifts the effective scale ~0.5%/night — set-04 runs 17.03→16.94 across its own groups), hence the per-set trend. Every number read is the solver's own WCS or a header fact; in-house is the trend + flag rules; REPORTS ONLY, exits 0. `--selftest`: catches a planted wrong-optimum on both rules, does NOT flag a planted refraction drift, and proves a set-median rule would (trend rule load-bearing). Stated limit: blind to the ~0.1–0.2% TAN+SIP3 fit-variance floor (twins of identical data landed 16.973 vs 16.944, both stable, logodds 270+), which is the model's, not an outlier's |
| `run_undistort_compose.sh` + `run_undistort_groups.sh` (final compose) + `run_undistort_pipeline.sh` (sub-stacks, with the `setref lt 1` pin) stacks without `-output_norm` + the normalization-anchor stamp (`ANCLOC*`/`ANCSCL*`/`ANCREF`/`ANCSRC`, `STACKNRM=addscale`, `REGREF`/`REGREFSR=pinned` on the per-set final) | Siril offers a reference-anchored (or per-channel, non-min-max) output normalization — then `-output_norm` returns and the ANC* keys retire | 2026-08-28 | **not fired — NEW.** A deviation from Siril's OSC-script default TOWARD the linear-photometric standard (a defined, reproducible zero point tied to the normalization reference, display scaling separate); basis `docs/dead-ends/stacking-compose.md`, the `-output_norm` zero-point entry (E0-E3; the item `output-norm-zero-point` CLOSED, owner-accepted 2026-08-29 after the from-raws campaign — record `datasets/corpus/campaign_zeropoint/campaign_record.json`, 12 baselines re-seeded + aug14's 5 seeded on the accepted products). First product under it, aug06 set-01+02+03 `_nooutnorm` (ledger aug06 `output_norm_zero_point_compose_tier`; `datasets/corpus/pedestal_work/go2_compose_nooutnorm.json`): ANCLOC read back 0.00111621/0.00197157/0.00153994 = the M lines to the digit; level 72.808/128.792/100.545 ADU16 = the reference's −0.47/−0.32/−0.37%; H1 ΔK 0.000/0.000; H2 R/G 0.5653, B/G 0.7807; H3 4 clamped px of 30.1 M, both components member-backed, 0 in-frame zeros; against the hand-stacked E2 preview 87,798,306 px differ by ≤5.96e-7 (0.039 ADU16) — cached 6-digit M-line statistics vs a fresh stack (`docs/dead-ends/siril-behaviors.md`), not a knob. The post-assert greps Siril's own "Output normalization ...... disabled" and exits 4 otherwise; the wording is observed on 1.4.4 only, and a change aborts loudly rather than passing. `check_removal_conditions` already matches both basenames through older rows (`derive_compose_ref.py`, `compose_preflight.py`, the `--tag=` row), so this row is owed by the register's rule, not enforced by the guard. Per-set final under it, aug06/set-01 `_nooutnorm` from the existing five members (ledger aug06 `output_norm_zero_point_perset_final_set01`; `datasets/aug06/set-01/qa_work/refinal_nooutnorm.json`): ONE pixel-moving knob proven — clamp((new − 58.766 ADU16)/0.98255) reproduces the shipped `stack_set-01_full.fit` with 0 of 52,966,158 pixels differing above 1e-7 (`-transf=homography`/`-interp=lanczos4` are Siril's defaults, the 2pass re-picked image 1); level = the pinned member's own sky (ANCLOC ×0.997-0.998), R/G 0.5656 B/G 0.7806 vs the anchor's 0.5659/0.7806; 0 clamped, 0 in-frame zeros; K 1.000/0.640/0.860 unchanged; `baseline_guard` ADVISORY on the level rows (×2.35 post-SPCC — SPCC's b-offsets carry a constant ~28 ADU16 in R, so the neutralized level tracks R's pre-SPCC level, not G's), structure measures 0.297 / +0.0025 PASS and shrink with the pedestal exactly (0.699 × 43.0/101.1 = 0.297) |
| `scripts/calibrate/spcc_run.py` `spcc_list oscsensor` preload before `spcc` in the generated `.ssf` + the post-run log-order assertion (`SPCC JSON metadata loaded` before `SPCC will use`; the model listed verbatim by `spcc_list`; the model echoed by `spcc`) + the on-disk database preflight (the model exists as an `OSC_SENSOR`; an `is_dslr` model requires `-osclpf=`) | Siril loads the SPCC metadata before resolving names in `do_pcc` (1.4.4 resolves at `command.c:10152-10188` and loads at `:10205`; upstream master `ee7b942` still resolves first) — then the preload and the assertion retire; re-check at every version bump (BACKLOG `siril-1.5`) | 2026-08-29 | **not fired — NEW.** MEASURED (`datasets/july31/set-01/qa_work/spcc_h0_probe.json`, the H0 probe): a spec-less headless run resolves to index 0 of each list — "Generic mono sensor" × Antlia R/G/B, the model behind every shipped K record — and its log prints `SPCC will use mono senor "(null)"` at line 52 BEFORE `SPCC JSON metadata loaded` at 53; with `spcc_list oscsensor` first the load line precedes the use line (52 < 105, 56 < 109), "Nikon D750" and "Nikon D500" are listed verbatim and echoed, K 1.000/0.697/0.945 vs 1.000/0.700/0.955 (ΔK_G −0.003, ΔK_B −0.010) against the index-0 1.000/0.687/0.927 on the same input, the R/G fit sigma 0.140 → 0.095/0.093; the spec-less arm errors with Siril's own "Either the sensor or a filter was not specified ..." (exit 1, no K); the photometry prefs persist nothing. The spec-less refusal itself is Siril's own contract (no row); `readiness_report.py` reads RED on a set without a recipe `spcc` block until stage 2 pins a curve. |
| The **Nikon Z f proxy response** — `scripts/setup/spcc_curves/convert_curves.py` + `fetch_sources.sh` (`Nikon_Zf.json` / `Nikon_Zf_energy.json` tracked, `Nikon_Z6.json` cache-only by licence) installed as untracked `OSC_SENSOR` files in the siril-spcc-database clone and pinned by every canonical set's `recipe.json` `spcc` block (`{"oscsensor": "Nikon Z f", "oscfilter": "No filter", "whiteref": "Average Spiral Galaxy"}`) | a curve measured on THIS body (a grating on a CALSPEC standard — `docs/spcc-sensor-curve-z6iii.md` §1.5 B1, owner-gated) or an upstream "Nikon Z6 III" `OSC_SENSOR` entry lands — then the recipes name it and these files retire; re-check whenever the siril-spcc-database clone is updated | 2026-08-29 | **not fired — NEW.** A proxy by dye family, not by die: the Z f / Z6 share Nikon's CFA dyes and hot-mirror generation with the Z6 III (IMX820AQJ) by assumption, measured by no one. MEASURED on july31/set-01 (`spcc_set-01_arm_{zf,z6,d750,zfe}.json`): the four named curves within 0.002 (G) / 0.006 (B) on K; every real OSC curve moves the R/G fit toward the origin (σ 0.140 → 0.095–0.099, intercept share 0.71 → 0.42–0.48) and none the B/G (σ 0.107–0.108, share 0.39–0.44, "imprecise solution" fires); energy-vs-photon convention ΔK ≤ 0.002. Pinned on the owner's H4 approval of `set-01_arm_zf_spcc-linked.png`; all 22 canonical products re-calibrated from their existing `_wcs.fit` (7b9d1c6): ΔK_G +0.0093 ± 0.0011 (+1.44 ± 0.17%), ΔK_B +0.0191 ± 0.0017 (+2.22 ± 0.20%) over the 17 finals vs the accidental index-0 model, n_kept and b_R identical on all 22; records `datasets/corpus/spcc_pin_zf/pin_record.json`, `scripts/setup/spcc_curves/RECORD.json`. |
| `swarp_compose.sh` + `swarp_weight_maps.py` (SWarp per-member MAP_WEIGHT compose: split → seqstat-derived addscale re-creation via BACK_DEFAULT/FLXSCALE → CD-only TPV `.head` per member → weight maps → 3 coadds → rgbcomp → stamp) | Siril's compose accepts per-member weight maps (a per-pixel weight per sequence member in `stack`/`seqapplyreg`), at which point the SWarp engine and every re-creation of addscale in it retire | 2026-08-29 | **not fired — and the route is STOPPED, not adopted: scaffolding only.** Written for the tapered-weight arm of the corner-smear work and stopped by the owner before any arm was built (the tapered form's purpose — keeping the rim's coverage — is out of scope by the owner's word; ledger lines 115–116, `datasets/corpus/smear_attribution/swtaper_probes.json`). What stands are ENGINE FACTS measured on this rig's SWarp 2.41.5 (P1–P7): SWarp reads only the first plane of a cube; reads CD and ignores PC/CDELT when CD is present; applies TPV terms; pins the output grid from a `.head` exactly; SUBTRACTS the BACK_DEFAULT list; with RESCALE_WEIGHTS N a MAP_WEIGHT 3:1 planted mean reproduces to 0.004 % and with Y it fails (the positive control); DIVIDES a map's weight by FLXSCALE² (a quality-weighted arm must pre-multiply by f²); sip_tpv is exact on CD-only heads (≤ 4.8e-11 px) and a head carrying CD AND PC/CDELT makes astropy misread the TPV sky. The in-house parts are the weight-map writer (a formula over tool-sourced numbers: x_c from Siril findstar via the crop rule, STACKCNT and W from the header — no deliverable pixel read) and the addscale re-creation; every resampling and combine is SWarp's. NOT on any build path; no product built from it; `swarp_weight_maps.py --selftest` (6 cases) is the only thing that runs. Resume condition, separate from removal: a quality-WEIGHTED form (continuous per-pixel weight by measured quality, both sides of a member) is wanted after the exclusion rules settle — then the arm-scale paths (3 coadds, rgbcomp, stamp) and P3's Siril comparison are the unbuilt half. **RESUME TRIGGER FIRED 2026-08-29 — the exclusion rules have settled**: the portion rule is the chain (this table's `run_member_crop.sh` row; ledger 123–128) and the frame rule is a measured NULL on top of it (ledger 117–119). The scalar branch RAN — the `--weight=noise` corpus arm (`datasets/corpus/smear_attribution/weight_noise_arm.json`, ledger 134–136): a NULL, nothing degraded — Siril's own weights moved ~10 % between nights (july31 0.900 … aug14 1.094) and no station of 58 moved beyond +0.016 px — so nothing resumes; this per-pixel scaffolding stays STOPPED under the owner's ruling (the rim is out of scope) with its unbuilt half unchanged. Removal condition unchanged. |
| `run_member_crop.sh` + `member_profile.py` (the corpus combine's MEMBER-SELECTION stage: per-member station profile → the portion rule → curated dir of symlinks + Siril-cropped copies; `run_corpus_combine.sh --portion-rule`) | Siril's compose accepts per-member weight maps or a per-member region mask (a mask is the crop without the coverage cost) — the same condition the SWarp scaffolding row carries, and they retire together | 2026-08-29 | **not fired — IN THE CHAIN (`run_corpus_combine.sh --portion-rule`): the corpus canonical is built under it (0 differing pixels from the owner-approved candidate, ledger 128); the corpus baseline is seeded (`datasets/corpus/baseline.json`).** The rule (asymmetry FWHM(+dx) − FWHM(−dx) > bar, onset − half-width, intrinsic, rankless) is the owner-approved cropT arm's, verbatim; every constant lives in `datasets/corpus/recipe.json` (bar 0.20 px, stations ±600..±2400, r 400, top-30, half-width 300), never a script default. Every pixel op and measurement is a tool's (Siril findstar via `star_stations.py`; Siril `crop` of COPIES — originals never written); in-house is the rule arithmetic over the tool's numbers, the curated-dir bookkeeping, and the per-member profile CACHE (sha256 + geometry keyed, tracked). The frame-level score S_i rides along as an ADVISORY only (the GO #16 NULL). SCOPE: the corpus combine only; the per-set finals are not run through it until measured there — the ONE untested extension. Its test is a framing=max compose of ONE set's curated vs uncurated members (aug14/set-04: 6/6 cropped, x_c 900 ×1 / 1500 ×5, the stage record), shape measured on shared sky boxes, measurement only; the per-set final itself is `-framing=min` (`run_set_chain.sh:92`), and an intersection framing DROPS a cropped member's removed columns from the canvas (1416 of a 5832-wide member at x_c 1500) instead of replacing them with a better member's — so whether a per-set DELIVERABLE runs through the stage is the owner's ruling, not a measurement. `--selftest` (in `run_guards`) falsifies on synthetic members: a planted profile crossing the bar MUST crop at onset − half-width with the four MEMC* keys and kept-pixel identity; a flat profile MUST come out a symlink with none; a SYMMETRIC both-sides rise MUST NOT crop (the refuted intrinsic form); the pinned-reference refusal; the cache path (second run 0 profiled, verdicts identical, cache byte-identical). Composite provenance: `stamp_headers.sh` aggregates NCROPPED/MEMCRULE/MEMCXCS/MEMCPROV, never crashes on the legacy prose MEMCROP of the GO #12/#13 arm copies (LEGACY(n)), and a mixed-rule compose is REFUSED in the stamp (the hard stop is the caller's — stated, an UNCHECKED shared premise of both workers). The combine surfaces a derived reference that the rule cropped (a cropped anchor is UNTESTED — loud warning + reference_cropped in the stage record, never a refusal). ROW-RESOLVED x_c MEASURED NULL (`datasets/corpus/smear_attribution/rowmin_arm.json`, ledger 131–132): x_c = min over rows on the six row-profiled members moved the removed columns' own sky positions −0.004..−0.033 px (pre-registered ≥ 0.10), corners ≤ 0.02, at +1.2 % pixel-frames — the centre-row geometry stands; the outer station bounded (`row_profiles.json`: same-aperture Δ median +0.008 px, the r-200 reading scatters ±0.12). Decision map + the stage as built: `docs/corner-smear-member-selection.md`. |
| `datasets/corpus/smear_attribution/row_profiles.py` + `toprow_profiles.py` + `toprow_corner_coverage.py` (the row-resolved member profile — Siril `findstar` at `star_stations.py`'s geometry on the TOP and BOTTOM rows beside the cached centre row, the outer station at dx +2700 r 200 with its same-aperture control, the top row of all 77 — and the header-only WCS pin of which members' rows feed which canvas box) | a tool reports a headless row-resolved star-shape profile of a member (a per-region `findstar`/`seqtilt` surface by row), at which point this driver and its record are re-derived from that tool | 2026-08-29 | **not fired — a DIAGNOSTIC beside its record (the `rho_march.py` precedent), on no build path.** Every pixel op and measurement is Siril's (`findstar` through `star_stations.measure`); in-house is the row placement, the asymmetry arithmetic (`member_profile.apply_rule`, imported not copied) and the bookkeeping. What it measured (`datasets/corpus/smear_attribution/row_profiles.json`, ledger 129–130): the bottom row's degradation starts ~600 px EARLIER than the centre row's (onset 1200 on 5/5 cropped members vs 1800/2400) with the same far-station asymmetry; the top row is 0.4–0.5 px softer SYMMETRICALLY on the aug14 / aug09-set-05 members (the uniformly-soft case the asymmetry rule is blind to by design); the outer station is a bounded NULL (same-aperture Δ median +0.008 px) whose r-200 instrument scatters ±0.12 px — half the bar — so per-member calls in the last 86–116 px are unresolvable. Its consumer, the row-resolved crop arm, RAN and is a clean NULL (`rowmin_arm.json`, ledger 131–132) — the stage's centre-row geometry stands; what still consumes this record is the top-row symmetric-softness question (`docs/corner-smear-member-selection.md` §6), unscheduled. |
| `scripts/qa/check_site_privacy.py` — the observing-site guard: derives every form the machine-local `site.local.json` implies (decimal at 4+ places, sexagesimal, the geocentric OBSGEO components, a 5-decimal near-literal) and scans the tracked tree + the index for them, plus a STRUCTURAL check that no tracked JSON carries a numeric site key; positive controls for each form | an off-the-shelf secret/PII scanner (gitleaks / trufflehog class) with a rule for this site runs in the pre-push hook AND the resolver can write no coordinate by construction (the `site` block schema has no numeric key), at which point the in-house scan retires and only the structural check's job is left to the scanner's rule | 2026-08-30 | **not fired — in `run_guards` and the pre-push hook; `--selftest` 23 arms (every form, the perturbed class included, planted RED and named); a records guard, never a gate on a product.** Limits: with no local config the literal scan is SKIPPED aloud and only the structural check runs; it scans the tree and the index, never history (a form in a past commit is the rewrite's record, `datasets/corpus/history_rewrite/`); a form it does not derive (an undocumented offset, a place name, UTM/MGRS) is outside its scan — the template says what not to write. Mechanism + rulings: `docs/dead-ends/evidence-provenance.md`, "THE OBSERVING SITE IS A HOME ADDRESS" |

---


## `standard-route-output-norm` — the tracked-mount route still stacks with `-output_norm`

`run_pipeline.sh` (×3 light stacks via `$STACKPOL`) and `scripts/stack/siril/lights.ssf.tmpl:37`
carry `-norm=addscale -output_norm`, the global min-max rescale the undistort route retired
(mechanism + the shipped design: `docs/dead-ends/stacking-compose.md`, the `-output_norm`
zero-point entry). The route is untested by that closure: no current dataset is tracked-mount,
so it has no product to declare a delta on. Work, when a tracked set exists: the same shape as
the undistort tiers — drop the flag, assert Siril's own "Output normalization ...... disabled"
line, stamp `STACKNRM`/`ANC*`/`REGREF` (the standard route stamps nothing today —
`docs/combine-contract.md`:179, `stamp-key-inheritance`'s open (e)), guard advisory under the
STACKNRM change; one product, pre-registered as the undistort tiers were. Removal condition:
the same as the undistort rows' (Siril offering a reference-anchored output normalization).
**Closes when** the standard route ships without `-output_norm` on a measured product, or
records why it must keep it.

## `pending-owner` — decisions with the owner, and the input they ordered gathered

**Migrated from a retired session report** (owner: *"report.md was meant to be
temp. get rid of it. we don't need it. it's clutter."*). Its queue duplicated this
file slug-for-slug and its session transcripts are in git; what follows is what had
no other home. **Everything here is the owner's or is held for them.**

### UNCHECKED — logged, not discharged

- **"Self-picked targets outperformed assigned ones."** Handed over as established
  and **refused from the inside by the seat it flatters**: no counterfactual was
  measured, and it flatters both parties who agreed on it. Competing explanation is
  SEQUENCING, not autonomy — the first units were assigned, narrow, and taught the
  tree. **Operating rule adopted meanwhile: assign the first unit, then release.**

### Live with the owner

1. **WHETHER `BACKLOG.md` AND `docs/dead-ends.md` SHOULD REMAIN TWO FILES — HELD
   BY THE OWNER 2026-08-16, AND RECORDED HERE AS AN OPEN QUESTION RATHER THAN A
   DIRECTION.** The two have converged in role, and both are less useful for it.
   **Nothing changes until the current cleanup lands.** After it, the registry may
   be removed entirely — that is one of the options under consideration and it is
   **NOT DECIDED**. Do not read this row as a plan to merge or to delete; read it
   as notice that the question is live and the answer is the owner's.
   **THE CONSEQUENCE GOVERNS WHAT IS WORTH DOING IN THE MEANTIME, which is why it
   is recorded and not just held:** effort spent RESTRUCTURING `docs/dead-ends.md`
   internally is effort that may dissolve, so it should not be started. Deleting
   entries whose test is solved and no longer valuable — the rule ratified the same
   day, in that file's own preamble — **survives either outcome**, because the
   content leaves the tree regardless of which file survives. Reorganisation does
   not. Prefer the operation that is robust to the ruling.

2. **L2 may reopen.** Cosmic Clarity's chroma knob saturates above 0.85, but no
   record says which `--denoise_mode` that was measured under. `render-ladder` is
   user-gated and not the PM's to promote.

### Owner rulings that existed in NO other file

- **The per-member trim — RULED, RAN, REFUTED; no trim ships.** Owner 2026-08-22, verbatim: trim
  *"each side by about 5% ... so the worse part of each image never makes it into the stack"* — a
  DIRECTED TEST superseding the WAIT ruling once the band was attributed member-borne
  (`datasets/aug09/smear_work/rho_march.json`); executed 7775fdd, 2654d31, c6230cc. The owner's
  mechanism for the corners, verbatim: the far-corner stars are always at a member's frame edge —
  *"the stars being stacked are the worse images possible"* (measured on that axis: member-own field
  radius +0.53 px per unit ρ, 3.6 SE; coverage depth 0.2 SE). OUTCOME: RAN, REFUTED (H1/H2/H3 + rim)
  — diverse good contributors 7 members from 4 sets → 2–3 from one set, composite FWHM 3.257 →
  3.487, median ΔFWHM +0.133 px where ≥ 2 sets are lost vs +0.012 elsewhere; the corner-chase prune
  conditional on a WIN did not fire. Two chain defects it unmasked were fixed and KEPT: the
  unguarded wrong-scale member solves (`solve_field.py --scale-band` + `member_solve_audit.py`,
  c6230cc; cross-chain bow 31.5 → 1.4 px) and `-output_norm`'s single-pixel zero point (the closed
  `output-norm-zero-point` campaign). Registry: `docs/dead-ends/stacking-compose.md`,
  "PRE-REGISTRATION FRAME-WIDTH CROPPING (the retired `--crop-lr` knob)"; ledgers
  `datasets/aug06/experiments.jsonl` `frame_crop_5pct_per_side_before_registration` (+ its
  correction), `datasets/aug14/experiments.jsonl` `crop5lr_cross_night_combine_aug06_plus_aug14`,
  `crop5lr_cross_night_RIM_DEGRADATION_root_cause`, `member_solve_scale_band_fix`; records
  `datasets/corpus/crop_work/`; the arms were disposed in the rig cleanup (8d234c8), the records
  stand. The open half — whether properly centred frames would change the corners — is
  acquisition-side and not a route this repo takes (MEMORY: the data is a given).
- **Also ruled, and recorded elsewhere already:** the L1 judge triple
  (`datasets/aug06/l1_work/owner_ratification.json`), the two parallel-session rules
  (`b36ef3b`, `64f61d2`, both verified in `CLAUDE.md`), and starlight preservation as a
  logged UNCHECKED premise that blocks nothing
  (`datasets/aug06/l1_work/unchecked_premises.json`).

### Queue items that had no home in this file

- **`--weight=noise` corpus arm — MEASURED NULL, closed** (ledger 134–136;
  `datasets/corpus/smear_attribution/weight_noise_arm.json`; mechanism entry
  `docs/dead-ends/stacking-compose.md` "SIRIL'S NOISE WEIGHT IS (scale/bgnoise)² ON THE REGISTERED
  IMAGE'S NON-NULL PIXELS"; the map `docs/corner-smear-member-selection.md` §6). One knob, nbstack →
  noise on the chain's curated members, reference pinned 35: the reconstructed weights july31 0.900 /
  aug06 0.971 / aug09 0.988 / aug14 1.094 (the sharpest night the noisiest by Siril's estimator); all
  58 stations within −0.015..+0.016 px of the canonical (corners: six at 0.000, +0.007 / −0.015 at
  two — real, small responses: the compose repeat floor is ZERO, `repeat_floor.json`), seams identical, SPCC K within 0.004 — nothing gained, nothing degraded; nbstack
  stays the chain's default. The motivating 18–24 % cross-night gap is a THROUGHPUT gap on the stars,
  which a background-noise weight does not see. The weights are Siril's own — the `.seq` statistics
  through the source formula, MEASURED by a planted-noise two-member control (`noise_weight_control.json`).

(The real-flats HANDLED path re-homed into `route-recommendation`'s flat-source
bullet; pooled master darks re-homed into `dark-optimization-fork`.)

**Closes when** the owner rules on the two-file question.

---

## `compose-homography-smear` — the smear is CLOSED by member selection; the reprojection route and the model questions stay open

CLOSED, homed: the union's band and corners are member-borne, in the photons, night-ordered —
`docs/dead-ends/stacking-compose.md`, "THE UNION'S LEFT-BAND / BOTTOM-CORNER SMEAR IS NOT A
REGISTRATION OR COMPOSE DEFECT" and "THE SUB-STACK COMPOSE IS A MOSAIC, NOT A STACK" (the
astrometric compose is the shipped route, owner-PASSED); the decision map
`docs/corner-smear-member-selection.md` (cropT owner-approved 2026-08-29, §5); the attribution
records `datasets/aug09/smear_work/{smear_remarch,rho_march,rho_march_prereg}.json`; the blanket
trim (owner-directed 2026-08-22, RAN, REFUTED — BACKLOG:`pending-owner`;
`docs/dead-ends/stacking-compose.md`, "PRE-REGISTRATION FRAME-WIDTH CROPPING (the retired
`--crop-lr` knob)"). Geometry: `docs/dead-ends/registration-distortion.md`, "FITTING A LENS MODEL
AGAINST A PLATE SOLUTION WITH AN AFFINE NUISANCE" (a centred ptlens model fits to a 0.27 px median;
the `<center>` entry beside it). Optics: `docs/dead-ends/star-shape-optics.md`, "THE ONE-SIDED
STAR-SHAPE GRADIENT IS IN THE OPTICS-AND-PHOTONS OF A SINGLE EXPOSURE". The drift arithmetic:
`docs/untracked-widefield-standards.md` §H.4. The SCAMP/SWarp facts and defaults: `TOOLS.md`, the
SCAMP and SWarp rows. The canvas-x trap: `docs/dead-ends/measurement-discipline.md`.

OPEN — each settled at the COMBINE, one knob, or withdrawn with its reason:
1. The SCAMP/SWarp TPV reprojection as a COADD against the shipped `seqplatesolve` compose — U
   (no defect motivates it now).
2. Interleaved rather than consecutive groups — D (stations + the dwell-floor / rejection
   denominators); a trade, not a free win.
3. A corner-true shared model — N: no fit constrains past ρ 1.47–1.51 against a corner at 1.80
   (`docs/combine-contract.md`; `docs/dead-ends/registration-distortion.md`, "CORNER CONTROL POINTS
   CANNOT BE RECOVERED BY REORDERING OR RELAXING").
4. Which single model — the pinned july14 fit or a fresh fit — D; the corner-supported candidate
   a,b,c (ledger `ptlens_joint_refit_free_centre`) judged at the combine on star_stations + seqtilt,
   then the owner's eyes (U).
5. A state-CHANGE detector with a RELATIVE trigger — D once the member-separation quantity is
   attributed (`docs/combine-contract.md` §5).

**Closes when** 1–5 are each measured at the combine or withdrawn.

## `intake-culling` — one measured intake pass, one visible formula

USER-DIRECTED. More photons are always obtainable; a bad frame stacked is permanent.
Every recurring defect has a signature that is measurable per frame at intake, and
they should be measured ONCE, scored by a formula whose constants are visible and
adjustable, and reported per frame with its reason.

**THERE IS NO VENDOR DEFAULT TO ADOPT HERE, AND THAT CHANGES WHAT STANDARDS-FIRST
REQUIRES OF THIS ITEM.** (The ORACLE's, DOCTRINE — searched negative; `15/15/20` and
`combining expression` each occurred in ZERO tracked files before this.)
`CLAUDE.md` requires stating the industry-standard way FIRST and deviating only on
a measured constraint. Searched: **no vendor publishes a default combining
expression** for per-frame quality signatures. The **15/15/20 weighting that
circulates in the community is COMMUNITY, not vendor, and its constants are
UNDERIVABLE** — nobody publishes what they were fitted against, so adopting them
would be importing three magic numbers, which is the opposite of "constants visible
and adjustable". The one vendor direction found points at a **single proprietary
statistic** rather than a published combination.

**So the standards-first answer for this item is a SEARCHED NEGATIVE, and that is a
result rather than a gap:** there is no standard to adopt, so a visible in-house
formula is the standards-compliant choice here and not a deviation needing a
recorded excuse. What it still owes is what the item already demands — every
constant visible, every signature with a positive control.

**SECONDARY AND UNCONFIRMED, carried with its status because the source did not
resolve:** the PixInsight documentation returned **403** to the Oracle, so the last
two clauses above — the community provenance of 15/15/20 and the single-proprietary-
statistic direction — are UNVERIFIED against primary source. The first clause (no
published vendor combining expression) is the searched negative and is the load-
bearing one. Do not cite the secondary clauses as established.

| signature | what measures it | status |
|---|---|---|
| aircraft / satellite / bug | streak geometry | BUILT — `anomaly_audit.py` |
| shake / wind gust | per-frame FWHM + roundness spike; elongation angle off the trail axis | **THE ANGLE TEST NOW EXISTS AND IT FIRES** — `datasets/aug06/corner_work/drift_bearing.json`, commit `b512419`. The first block of aug06/set-01 reads θ₀ **19.75° away** from the rest of the set while its own drift bearing departs by only **0.150°** against a 0.062° SE — so the SKY was doing the normal thing to a fifth of a degree and only the star SHAPES were not. That localises it IN THE EXPOSURE (vibration or settling on the first frames after setup), not in the tracking or the sky. It reproduces across detection depth (−36.4° at σ 1.00 vs −29.8° at σ 0.50, same frame) and on the other night (july31/set-01 frame 1, −19.5°). **Fires on 2 of 21 frames, both the first exposure of a night** — which is a positive control this item required and did not have. Still needed for adoption: a per-FRAME form (this is per-block) and a decision on whether one frame is worth culling |
| cloud | background level and its rate of change — star COUNT is measured blind on rich fields (detection saturates at the cap) | per-frame background is NOT recorded |
| light pollution / moon | background gradient magnitude + bearing (the odd-plane term tracks the moon's bearing to 23 deg) | measured once ad hoc, no script |
| transparency drift within a set | the STARS' own throughput gradient, block to block — `object_tilt.py`'s per-block gradient term measures a within-set drift of **0.040–0.425 mag across the frame (median 0.149), MONOTONE in block order in 10 of 12 sets**, from Siril aperture photometry on matched stars | MEASURED as a by-product of the object-tilt dead end (`datasets/aug09/corpus_object_tilt.json`); it is a real per-block transparency signal this surface does not otherwise have, and unlike background level it is measured on the OBJECT's own flux. No per-FRAME form — the instrument works on sub-stacks |
| file inconsistency | per-frame mean/median step, EXIF constancy, truncation | not built |
| optical-state change mid-set | geometry residual step (BACKLOG:`compose-homography-smear`) | member-level only; no per-frame form |

Design constraints, each from a measured failure here:

- **Measure once.** One per-frame table, every column a tool's number, written at
  intake and never re-derived — so a different cull replays without re-measuring.
  **AND THE TABLE MUST NAME THE ARTIFACT IT MEASURED, NOT WHAT THE FRAME WAS
  CALLED. Today's does not, and that breaks this constraint on its own terms.**
  `records.jsonl`'s `file` field carries the RAW's basename while every metric is
  regdata from `register -2pass` over the DEBAYERED conversion (`run_frame_qa.sh`:
  `convert c -debayer` → `c_.seq` → `inspect_stage.py reg --seq`). So the table
  cannot be replayed from the file it names: Siril loads a NEF as the CFA MOSAIC,
  and MEASURED on 12 aug09/set-05 frames that returns **0.151× the recorded star
  count — one star in seven — against 0.855× on the debayered conversion of the
  same frames** (`datasets/aug09/set-05/sirilpy_work/analyse_probe.json`). A
  discrepancy that size reads as a BROKEN TOOL rather than as a wrong input, which
  is what makes it expensive. Recording the artifact costs one field.
- **One visible constants file**, per-dataset override in `recipe.json`. The
  aggressive-vs-conservative dial is the user's; the pipeline applies what is set
  and records it.
- **Every signature ships with a POSITIVE CONTROL** — data on which it MUST fire.
  Three checks have shipped green while broken (`docs/dead-ends.md`); a signature
  that cannot be made to fail on demand is decoration.
- **A cull is not the answer to every defect.** A mid-set optical-state change is
  not a bad-frame problem: the set wants SPLITTING at the boundary, not thinning.
  The report proposes the action, not just the exclusion.
- Reuse rather than rebuild: `run_frame_qa.sh` / `frame_metrics.json`,
  `anomaly_audit.py`, `cull_report.py`, `inspect_stage.py`, `cullspec.py` (which
  already aborts loudly on an exclude matching zero frames).

**Closes when** one intake pass writes every signature for a set, a tracked formula
turns them into a proposed action per frame with its reason, and each signature has
a control that demonstrates it firing.

## `render-ladder` — the render tier's remaining tiers, user-gated

The first tier is BUILT (`scripts/stack/render_tier.sh`: separate → denoise the
starless → stretch → screen-recombine, every pixel op and every measurement a
tool's, gated by a ratified `render` block) and one render is user-approved —
**but that approval (july23 `set-01+02_desky_linked`) sits on a stack built by
the REGRESSED `--desky` pipeline. Not revoked, but
not a trustworthy reference either; see the caveat in that set's `recipe.json`.**
What remains is the LADDER around it and the harness it feeds.

- **L1 background level — the FOCUS item (user-ratified), and no longer a
  choice between unknowns.** The desky revert removed two coupled halves; the
  lights-side half — per-frame `subsky 1 -nodither` on calibrated, debayered
  lights, the operator's correct domain and Siril's own per-frame degree-1
  doctrine — is restored UNCOUPLED as `--subsky-lights` (default OFF; the
  registry's desky entry carries the split). The combine-corner audit measured
  the cost of its absence: a ~+1% combine-introduced term at the framing=max
  compose's full-coverage corners, absent (<=0.2%) from the min-framed control
  on the same chain. The arm is pre-registered
  (`datasets/aug06/experiments.jsonl`, `subsky_lights_restoration`): one knob,
  members rebuilt, same flats/models/culls/compose args; judged on the
  same-sky linear corner probe AND the user's eyes on a like-encoded
  framing=max union pair — user-ratified requirement: the max union is the
  deliverable (manual crop later), no yield excuses.
  **THE COLLISION IS SETTLED BY MEASUREMENT: the per-member trim was an
  owner-DIRECTED TEST (2026-08-22) that RAN (7775fdd) and is REFUTED — no trim
  enters the combine** (the `pending-owner` ruling carries the outcome;
  `docs/dead-ends/stacking-compose.md`, the retired `--crop-lr` rule). The
  max-union statement governs the FINAL FRAMING unchanged; *"more worried about
  stacking bad sections than about not stacking enough"* governs what goes INTO
  the combine, and the trim, tested, traded area BEFORE the compose for no shape
  gain (canvas −8.7%, amplitude-matched stars −1.1% within one night; the rim
  starved across nights). Measured
  cost of the collision, so the choice is made against numbers: a +x member trim
  keeping 80% of each member leaves 4 of 20 measured union boxes with no
  contributing member at all; a radial cut to rho 0.80 costs 3.3% of the
  delivered crop's area and 9.4% of the member-contributions inside it
  (`datasets/aug06/corner_work/`). **Those 20%-class cuts stay not-recommended**
  (predicted gain corner roundness 0.911 -> 0.938 against memberless boxes); the
  mild ~5%/side bracket was the DIRECTED TEST that RAN (7775fdd) and failed — it
  removes the worst sky without improving what remains and concentrates the rim
  onto whichever set still reaches it; the band's carrier is located
  member-edge, exit-edge family (`rho_march.json`). The composite-level arm
  is DEMOTED for this defect (a composite plane structurally cannot fit a
  corner-local term — measured, july23 subsky-on-combine probe); on-stack
  background remains the render-stage question for the sky's own gradient.
  Adoption still gates on preservation of the frame-filling UNRESOLVED
  STARLIGHT (degree 1 only; `docs/dead-ends.md` terminology entry — it is
  stars, not dust).
- **L2 denoise strength** — the proven chroma killer. Objective instrument is the
  `noise_split.sh` structured term, never whole-frame `bgnoise`.
- **L3 stretch ladder** — GHS/`ght` arms against the current `mtf`, compared at a
  MATCHED background landing so curve shape is the knob, not brightness.
- **L4 thresholded `satu`.**
- **Riders:** seed `datasets/GENERIC.json` (still the `{"render": {}, "why": {}}`
  stub) with the six current knobs and a per-knob class-risk note; per-arm output
  tree (`web/results/<session>/exp_<param>_<stamp>/`) and the `<final>_stages/`
  labeled sequence, both binding requirements the tier does not yet emit;
  `judgment_package.py` re-wire (its `.metrics.json` producer — the old chain's
  renderer — no longer exists; the PNG16-only surface is already enforced).
- **Two known limits:** a set can carry only ONE ratified `render` block (keyed by
  name), so two kept looks are not expressible; and a mono set STOPS loudly — the
  luminance-only variant is unbuilt.

One knob per arm, hypothesis pre-registered, judged on full-frame lossless PNG16.
**Closes when** an approved, re-baselined render comes out of a laddered arm.

## `learned-deconvolution` — the question, not an arm

`render_tier.sh` skips deconvolution on grounds that hold (classical RL is a
measured dead end on in-exposure trailing; BXT uninstalled by choice; GraXpert's
immature), and the registry deliberately does NOT dead-end a LEARNED
deconvolver — so the question is live: does one buy OBJECT detail? (Distinct
from the corner question — a symmetric sharpener cannot de-trail an elongated
PSF.) The arm this item once specified is REFUTED: Cosmic Clarity's non-stellar
sharpen is measured ATTENDED-only with its CLI ignored and the pass crashing on
real data (`TOOLS.md`, the one home — this item was the third session to
believe its `--help`), and its model space is isotropic radius-only either way.
What it needs is a headless CPU-Linux learned deconvolver — the same
procurement gap `corner-fix-landscape` tracks (`torchmfbd` checks there).
**Closes when** such a tool is procured and one knob is run against it, or the
question is judged not worth the procurement.

## `calibration-evidence` — three live threads; the rest is closed and lives in the registry

**The problem this item exists for is REAL and UNCORRECTED: a sky flat converges to
`sky × V`, so the object carries the sky's spatial profile.** `--desky` is off by
default — a registered 31× regression, and the grounds it shipped on were all
measured with instruments blind to the failure. **Every route tried to date is
CLOSED and every mechanism is in [`docs/dead-ends.md`](docs/dead-ends.md)** — the
catalogue-free object-tilt dead end with both its independent blockers, the
odd-component edge-dipole sweep, the flat-differential WIN with its transfer
function, and the domain-corrected iterative sky flat. Those entries carry the
numbers at greater depth than this item did; do not re-derive them here.

**THE FLAT DIFFERENTIAL IS THE ONE ROUTE THAT WORKS, AND ITS SCOPE IS THE POINT.**
A ratio cancels what two flats share, so the sensor-fixed atmosphere cancels in the
subtraction and the lever is 1603 px against the absolute design's 29.1 px median.
It delivers the TRANSFER FUNCTION (flat shape reaches the object ~1:1, floor
exactly 0.0000) and **not the LEVEL** — the absolute tilt still needs the flats'
COMMON sky content, which is unmeasured.

### Live

1. **A with/without judgement pair on finals — BLOCKED ONLY ON THE RENDER GATE.**
   The arms' FITS were freed with the rig cleanup (`datasets/corpus/rig_cleanup_record.json`); the surviving records are `datasets/aug09/set-05/flatdiff_work/*.json`; rebuilding the arms is part of this item's cost
   (skyflat_set-05 vs skyflat_set-01, 125 frames each, registration pinned so the
   ONE knob is the flat) plus the production-normalization pair `arm_{An,Bn}.fit`,
   **which is the pair to judge** — the eyes pass must see the SHIPPED
   normalization. Each carries `DIAGARM` / `CALXSET` / `STACKNRM` / `REGPIN` on the
   FITS so a diagnostic arm cannot later be mistaken for a deliverable.
   `render_tier.sh` exits 7 without a ratified `render` block
   (BACKLOG:`render-ladder`). **The question is no longer "is there a difference"** —
   it is MEASURED at −22.5% of object flux across the frame — **but "which arm
   preserves unresolved starlight", which no instrument here decides.** Owner's eyes.
2. **`build_sky_flat.sh`'s gate is still corner-vs-centre, which the registry calls
   SELF-FULFILLING for this defect** — and the script's own line 289 says so. The
   builder now records both edge dipoles alongside it, so the honest statement is
   that the gate UNDER-CLAIMS rather than lies; it should stop claiming to check
   what it does not. **A shipped candidate replacement exists and no consumer knows
   it: `scripts/qa/grid_ramp.py`** fits the low-order background ramp as
   coefficients, which four-corner spread cannot do on a structured field. The
   register's `baseline_guard.py` row records the same blind spot. **Swapping an
   acceptance measure is a USER RATIFICATION**, so this is a proposal to the owner,
   not a change to make.
3. **SPCC order-robustness is UNTESTED, not verified.** Inserting the background
   step ahead of SPCC moved K_G −1.20%/−1.48% and K_B −0.47%/−0.80% on unchanged
   star counts — larger than the chain's own recorded K scatter (0.006). Confounded,
   because the de-skied arm also removes a real ~3% object tilt. **Clean test: SPCC
   the SAME stack with and without an on-stack background step only.**

**Closes when** all three are resolved: the judgement pair judged, the sky-flat gate
either replaced by ratification or honestly re-described, and SPCC order-robustness
measured on one knob.

## `walking-noise` — open gap, class-gated

Faint DRIFT-ALIGNED streaks visible at native 1:1 and below whole-frame statistics: a
sensor-fixed pattern (readout FPN + residual warm pixels) dragged into lines by
coherent un-dithered drift. Rejection and cosmetic correction both measured NULL —
it is sub-sigma STRUCTURED signal, not discrete outliers. First quantification
(`noise_split.sh`): drift-phase term ≈0.34/0.48/0.42 ADU (R/G/B) per ~199-frame half,
against ≈1.0/1.5/1.2 ADU total static structure.

One measured CONTRIBUTOR is gone at the source: 16-bit master darks stored a
sensor-fixed ±0.5 ADU pattern subtracted into every light (0.2889 ADU RMS against a
0.4213 floor, +21%), fixed chain-wide and enforced by `check_bitdepth.sh`. **Do NOT
count that as a measured reduction** — the stack-level A/B cannot resolve it (the
chain's run-to-run variation is ~10× the effect). Whether the streaks shrank needs
`noise_split.sh` on a group-built pair.

**Gated on the class recurring** (an un-dithered untracked set; dithering is the
acquisition-side fix and removes the driver). First-contact levers: matched
shutter-mode darks; then drift-axis-aligned pattern removal or an AI denoiser weighed
against preservation of the unresolved starlight — a bandaid, last resort.

## `dark-optimization-fork` — `-opt` vs matched darks on the uncooled body

Siril-FAQ doctrine fork: non-cooled cameras "should" use dark optimisation, while
base doctrine and both vendors say matched darks need none. A/B on one set, one
knob, judged on dark-residual / walking-noise metrics (feeds the
BACKLOG:`walking-noise` mechanism work). Low priority — our darks are same-night,
session-end temperature. Pooled masters across nights ride this fork (re-homed
from `pending-owner`): gated on the nights' masters measuring identical
(measured: Δ0.1 ADU, noise within 1%); judged on `noise_split.sh`'s structured
term; per-session stays the default.

## `native-solve-and-sip` — one probe left

- **`platesolve -localasnet` on the mildly-trailed class.** The solver dead-end was
  measured on roundness-0.615 frames; july23 measures 0.80 — **and july23 is no longer
  on the rig** (`sessions/` holds july27, july31, aug06, aug09, aug14). The class IS on
  the rig: every current set sits in the same mildly-trailed band by its own frame QA
  (`qa_work/frame_metrics.json` `distribution` roundness medians, set-01 of each:
  july27 0.786 at 3.0 s; aug14 0.797, aug06 0.822, july31 0.849, aug09 0.852 at 2.5 s)
  — july27/set-01 is the nearest substitute to july23's 0.80. If Siril's own blind
  solve handles this class, `solve_field.py` gains a native sibling (the external
  route stays for heavily-trailed data). One stack, one probe, record either verdict.
- ~~**Siril-native SIP undistort vs the darktable warp.**~~ **CLOSED — RUN and
  REFUTED AS INVOKED**: per-member SIP composed 3.99/6.42/6.19 px against the
  shipped route's 0.29–2.99 (`register -disto=` is a SHARED-solution facility —
  Siril's design assumes ONE optical state per sequence), while `seqplatesolve
  -order=3` DOES solve members natively — both corrected beliefs are in
  `docs/dead-ends.md`. The shared-context successor (SExtractor → SCAMP → SWarp
  via TPV, with the pooled-occupancy order argument) lives in
  BACKLOG:`compose-homography-smear`, its one home; the wrong-for-this-data
  SWarp defaults are in `TOOLS.md`'s SWarp row. Not restated here.

## `one-sided-band` — one unattributed radial term

CLOSED, homed: the term is in single raws and no chain stage causes it —
`docs/dead-ends/star-shape-optics.md`, "THE ONE-SIDED STAR-SHAPE GRADIENT IS IN THE
OPTICS-AND-PHOTONS OF A SINGLE EXPOSURE", "THE THREE-LEVEL SEPARATOR", "ON A RECTILINEAR LENS
THE PLATE SCALE IS NOT ONE NUMBER" (18 % to the gnomonic scale; the remainder at 5.9 SE), "AN
ELLIPTICITY EXPONENT IS NOT A BLUR EXPONENT", and "THE ONE-SIDED RADIAL TERM'S CANDIDATE
FAMILIES AND THEIR DISCRIMINATORS ARE DOCTRINE" (the table, the astigmatism × defocus falsifier,
the altitude bound, the centre commensurability); the union's band → BACKLOG:`compose-homography-smear`.
Records: `datasets/aug06/corner_work/` — `coherent_trail_bins.json` (trail ratio 0.3502, the
predicted ZP deficit 0.570), `phot_work/zero_point.json` (the structural degeneracy),
`cfa_control.json` (the CFA-axis arm, non-attributing by pre-declared design), `pa_convention.json`;
ledger `corner_radial_term_family_and_centre`.

OPEN:
1. The residual RADIAL term's family — N: coma-consistent, astigmatism not reached, the
   radial↔tangential sign flip absent; no installed instrument separates them here.
2. Unrun discriminators — D: per-Bayer-channel ellipticity (greens identified FROM THE DATA,
   `TOOLS.md`); whether the ±2400 FWHM asymmetry (night-ordered per-set medians −0.070 … +0.472 px,
   `datasets/corpus/member_selection/july31+aug06+aug09+aug14_full_portion.json`) is the odd
   ELLIPTICITY term — a per-set roundness asymmetry from `datasets/corpus/member_selection/profiles.json`
   `top30_round`, no new run. Cross-session altitude (atmospheric / gravity) — N, the lever
   unquantified at 63–88°.

**Closes when** the residual radial term is attributed, or a route ships that holds the corner at
the clean band's star shape on the owner's eyes (U).

## `pointing-record-names-the-wrong-frame` — two header fields that are not the pointing

Two independent traps, both MEASURED, both of which have already misled a session
each. Neither corrupts a shipped product — nothing on the build path consumes
either quantity as a pointing — but both are silent and both invite the same
mistake.

**1. `fingerprint.field_center` is the FIRST FRAME's solve, not the set's
pointing.** MEASURED: it equals `mount_probe.json`'s `solve_a` to machine
precision in all three sets checked, and the probe's window is the FIRST frame of
the longest contiguous capture run. A fixed mount sweeps RA through the set, so
the field's RA at the set MIDPOINT is higher — and the record is therefore
systematically LOW by about half a set span:

| set | first (`field_center`) | midpoint | authoritative (`OBJCTRA`) | first − auth | mid − auth |
|---|---|---|---|---|---|
| aug06/set-01 | 302.945 | 306.054 | 306.653 | **−3.708** | −0.599 |
| aug09/set-01 | 306.727 | 309.840 | 309.703 | **−2.977** | +0.136 |
| july31/set-01 | 308.558 | 312.399 | 312.856 | **−4.298** | −0.457 |

Always negative, never positive, and about half the 6.22 / 6.23 / 7.68° RA span
each set sweeps. The NAME is what causes the error — "field_center" reads as the
field's centre. **Consumers: none on the build path** (grep finds only
`fingerprint.py` itself and `verify_site.py`), so this is a naming/semantics
defect rather than a corrupted product. It has nonetheless misled two readers in
one session, including this manager.

**2. `CRVAL1/2` is the WCS TANGENT POINT and on these solves it is nowhere near
the pointing.** MEASURED across 13 products: **CRPIX sits 40–960 px from the
image centre**, and **CRVAL REPEATS across different sets and different nights** —
five discrete values serve all 13 products (306.62/42.00 covers july31/set-02,
aug06/set-03 and aug09/set-03; 310.62/43.24 covers aug06/set-02, aug09/set-01,
aug09/set-05 and july31/set-04). A quantity that repeats across unrelated
pointings is not a pointing. Reading it as one costs up to **3°**.

**What IS authoritative: the full solution evaluated at the central pixel**, which
is the pointing by construction — and `OBJCTRA`/`OBJCTDEC` reproduces it to
0.000–0.031° on 7 of 9 products (0.13–0.18° on the other two). Use `OBJCTRA`, or
evaluate the WCS at the centre; never `CRVAL`, never `field_center`.

**Closes when** `field_center` is either renamed to what it is
(`first_frame_center`) or computed as the set's actual pointing, and the two
`docs/`+`BACKLOG` sites that cite a "solved centre" name which one they mean.

## `corner-fix-landscape` — procurement or acceptance

Rule: every candidate is FIX / TRADE / BANDAID before it is listed; a trade or a concealment never
shares a list with a fix. CLOSED, homed: no route on this rig RECOVERS corner detail — a single
global PSF cannot (no field-constant trail scale on three grids:
`datasets/aug06/corner_work/{constancy_fit,frame_depth,cfa_control}.json`);
`docs/dead-ends/separation-deconv-psf.md`, "NO INSTALLED TOOL DELIVERS A FIELD-VARIABLE ANISOTROPIC
PSF CORRECTION" (per-region tiling is pixel surgery, FORBIDDEN) and "PSF HOMOGENISATION — REFUSED BY
THE OWNER" (zone down-weighting is the same act); the blanket trim (owner-directed 2026-08-22, RAN,
REFUTED — BACKLOG:`pending-owner`). The FIX-class route that shipped is member SELECTION (cropT,
owner-approved 2026-08-29; `docs/corner-smear-member-selection.md`); what it cannot remove is the
lens's SYMMETRIC radial softening, and this item is about THAT. The procurement facts:
`TOOLS.md`, Tier 5, the anisotropic row.

OPEN:
1. Procurement — N: `torchmfbd` (three documentation checks decide it), `pyimcom` (a survey
   OBSFILE schema and no bring-your-own-data path — weeks and a fork; `furry-parakeet`'s kernels
   the one cheap probe); `galsim.des.DES_PSFEx` is installed for PSF evaluation.
2. `-noclamp` — a TRADE, U after D: the cost is measured (BACKLOG:`resample-cost-and-drizzle`),
   the ringing it prevents is not — the planted fixture with a sharp-edge target closes it.

**Closes when** an anisotropic treatment is procured and measured, or the owner accepts the
corner as-is (U).

## `resample-cost-and-drizzle` — the clamp costs 14× the kernel, and it is a pinned doctrine

**MEASURED, and it is a cost of OUR OWN PIN rather than of Lanczos4: the shipped
resample pass costs 6.26% of PSF width and the CLAMP is essentially all of it —
13.8× the kernel.** Lanczos4 unclamped 0.45%, clamped **6.26%**, cubic 5.39%, and a
nearest control reading **exactly 0.00%**, which is what makes the figure
interpolation blur rather than a fixture artefact. **The darktable warp adds 5.88%
and the CHAIN TOTAL is ≈12%**, with quadrature verified in series to −0.35% against
a nodist control that also reads exactly 0.00%.
**Quote ~6% and ~12%, never three significant figures** — fixture-to-fixture
variation is ~0.2 pp (5.88 against 5.67 on two independently generated fixtures).

**Full arms, controls and derivations are in `datasets/aug06/experiments.jsonl`** —
`resample_cost_arm_d_siril_pass`, `resample_cost_series_run`,
`resample_cost_arm_d_COMPLETE` (**read the LAST entry of each id**; two carry
supersession chains). That ledger holds the fixture design, the rank-matched
depth-matching that was mandatory, the ICC toe check that does not bite here, and
the ellipticity-vs-size-ratio coupling — whose downstream consequence is stated
where it is used, in `one-sided-band`, against its own ledger citation rather than
a copy of it.

**AND 6.26% IS A SINGLE-CONFIGURATION NUMBER FOR A QUANTITY THAT THEORY SAYS IS
NOT CONSTANT — so it is an ESTIMATE WITH AN UNSTATED SPREAD, not a property of the
clamp.** (DOCTRINE — the ORACLE's, from polyphase / fractional-delay filter theory;
`polyphase`, `fractional-delay` and `single-configuration` each occurred in ZERO
tracked files before this, so this is the first home.) A resampling kernel is a
fractional-delay filter and its response depends on the FRACTIONAL SAMPLE PHASE,
so the blur it costs is a function of where each star's centre falls between
pixels — and the clamp acts on exactly the ringing that phase controls. The arm
above planted ONE FWHM (2.10 px) and ONE set of sub-pixel shifts, so it sampled
that distribution once. The honest reading of the table is "6.26% at this PSF width
and this phase distribution", and neither the spread across phases nor the
dependence on FWHM has been measured.

**READ THE NEXT SENTENCE BEFORE USING THIS: IT IS NOT AN ARGUMENT ON `-noclamp` IN
EITHER DIRECTION.** It does not make the clamp cheaper, it does not make it dearer,
and it does not favour removing the pin. All it does is put an error bar of unknown
width on a figure that has been quoted as exact — including in
`corner-fix-landscape`, where the owner is being offered "a 6.26% gain against an
unquantified loss". **Both sides of that offer are now less determinate than they
read:** the loss was already unquantified, and the gain is a one-configuration
sample.

**What would close it, and it needs no new fixture:** re-run the existing planted
arm across a spread of sub-pixel phases and at two or more planted FWHM, and report
the range rather than a point. The same two-amplitude discipline this repo already
requires elsewhere — a quantity that is constant in the right parameterisation and
varying in the wrong one announces which it is.

**This is a doctrine number.** `check_registration_pins.sh` pins lanczos4 WITH
clamping — pinning it means asserting `-noclamp` is absent — and the guard's own
comment states the reason: *"clamping is the DEFAULT this repo keeps (lanczos4
rings on stars)"*. So ~6% of PSF width per resampling pass is what that pin
costs. **It is a TRADE, not a defect**, and the ringing it suppresses is real and
recorded elsewhere in this registry; **no call has been made and none should be
made without the owner's eyes**, since ringing is judged and blur is measured.

**Why drizzle is still live** (Oracle shortlist item 2, never opened): FWHM
2.0–2.4 px debayered is ~1.4–1.7 px on the green CFA lattice — undersampled — and
the untracked drift supplies ideal sub-pixel dither across 500 frames, the
textbook case. `docs/dead-ends.md` rules drizzle out on TRAILING grounds, but the
trail here is 1.4–1.9 px, comparable to the PSF rather than a long streak.
**Re-open with the number, not the category.**

**Closes when** the drizzle question is decided against the measured number rather
than against the category — i.e. whether ~1.4–1.9 px of trail on a 2.0–2.4 px PSF
disqualifies a technique whose preconditions (undersampling, sub-pixel dither
across 500 frames) this corpus otherwise meets textbook-perfectly. **The
architectural blocker is measured and is not the trail:** `seqapplyreg -drizzle`
refuses a debayered RGB sequence outright, so it is not one knob on this route.
`split_cfa` now supplies an un-interpolated mono green plane with the greens
identified, which is the only path the refusal does not name — unprobed, and not
asserted to be useful (the refusal and its "MONO is accepted" detail are in
`datasets/aug06/experiments.jsonl` → `two_probes_drizzle_input_and_otf_zeros`;
`split_cfa`'s own capability is in `TOOLS.md`).

## `star-neutral-colour` — the narrowband gap

SPCC-narrowband equalises O3=Ha and erases the O3 sphere; Siril has no single command
for a star-colour-neutral balance. Headless path identified and the tool half
confirmed on 1.4.4: measure mean star colour in the examine layer → apply a diagonal
`ccm`. UNTESTED design — do not cite as a method. Run it against a bracket (SPCC,
Nightlight) when a narrowband corpus arrives.

## `siril-1.5` — one load-bearing migration risk

1.4.4 is current stable; 1.5.0 is dev master. The trigger is a version bump, not the
rig (already x86).

- **RISK, now load-bearing: `starnet`/`seqstarnet` are REMOVED in 1.5.0-dev**,
  consolidated behind `pyscript StarNet.py`. `render_tier.sh` calls `starnet`, so a
  1.5 bump breaks the shipped render tier. Migrate before bumping.
- **Adopt on 1.5:** the native `mask_*` subsystem plus `-mask` on
  `denoise`/`rmgreen`/`epf`/`rl`/`sb`/`wiener` — the first native path to
  region-confined ops without a hand-rolled blend.
- **Retirement candidates:** `healpix` (lists the NESTED pixels overlapping a solved
  image — what `spcc_cone.py` hand-rolls; needs a check that its list maps to the
  zenodo chunk names) and `eqcrop ra1 dec1 ra2 dec2` (the natural consumer of a
  framing record's RA/Dec form).

## `final-best-percent-pass` — one target, many sessions: the FINAL pass selects by measured quality — thresholds, not a percentile

The standing multi-session practice's endgame (user-ratified): after many
~500-frame sets accumulate on one target, a FINAL pass re-selects from ALL
sessions' data. The owner's ruling (2026-08-29) fixes its FORM: a best-N% ladder is
a RANK rule and on an equal-quality corpus would drop N% for nothing ("consider
what happens if ALL the images were to be the same quality … should we have cut off
thresholds opposed to blanket cut rules?"), so the pass selects by QUALITY
THRESHOLDS that exclude nothing on an equal corpus. MEASURED at the MEMBER tier on
the 77-member four-night corpus (the corpus gate has fired): a PORTION threshold
(crop a member's entry-side columns beyond the onset where FWHM(+dx) − FWHM(−dx)
> 0.20 px — `cropT`, owner-approved) carries the gain, band 2.97 → 2.79 px at full
depth; a FRAME threshold (exclude a member whose interior+exit-side FWHM exceeds
the corpus's 25th percentile by > 0.20 px) is a NULL on top of it at −16.2 % of the
frames — reported, not gated (`docs/corner-smear-member-selection.md`). **SHIPPED
at the MEMBER tier:** the portion threshold is the chain for the corpus combine
(`run_corpus_combine.sh --portion-rule` → `run_member_crop.sh`; the canonical
corpus is built under it, 0 differing pixels from the owner-approved candidate;
guarded by `datasets/corpus/baseline.json`; the selection recorded per member in
`datasets/corpus/member_selection/<tag>_portion.json`). Unbuilt: the per-FRAME
cross-session quality surface (per-set `frame_metrics.json` exists; nothing ranks
or thresholds across sessions; `cullspec` excludes are per-set). Selection is
adopted only through a measured arm with a pre-registered prediction, never as a
default.
**Closes when** the per-FRAME surface ships the same way — a final-pass product
from measured THRESHOLD selection at the frame tier across at least two sessions'
data, with its per-set selection recorded.

## `session-level-mount` — one tripod pays for up to four probes

`mount` is modelled PER SET while it is a session-level fact: one tripod on one
night still pays for a drift probe per set. **Closes when** a decisive
session-level measurement seeds every sibling set's record (provenance kept per
set — a re-aimed set still cross-checks).

## `per-group-flat-at-the-combine` — the trade is only decidable at the combine unit

**PAUSED BY THE OWNER pending real flats** — the flat-residual research line is
on hold until real flats exist to compare actual frames against the current
synthetic masters. This is an owner decision about sequencing, NOT a
recommendation from this repo to acquire them: the synthetic-flat route stays
the mission and "a real flat" remains the divergence's removal CONDITION.
Do not pick this item up before that comparison exists.

The per-group flat measurement is CLOSED at the per-set deliverable: composed
object tilt **+0.055% ± 0.083%, 0.7σ over 1217 stars** — indistinguishable from
zero, because the set flat already IS the mean of the group flats, so a
plain-mean compose cannot tell them apart (cancellation measured 75–94%, refined
from the flat-side sensor-frame arithmetic by the drift and the `-framing=min`
crop). What per-group flats change is the MEMBER: transfer 1:1, object tilt
moving 0.36–2.13% in x at 4.3–21.3σ, backgrounds 28–40× more consistent
member-to-member (recorded as the mechanism's SIZE, never as evidence of better
calibration — that is the self-fulfilling direction), and a COST of 3.271% (x) /
4.335% (y) member-to-member object-imprint disagreement where the shipped route
has exactly zero.

**Why this is not optional to resolve.** The member is the cross-night COMBINE
unit, and MEMORY's binding rule is that every calibration/model/route change is
evaluated against the COMBINE unit, not just per-set products — measured twice
already, per-set models smearing cross-set unions. A per-set verdict on a
member-level trade is therefore an incomplete verdict, and the sign of the trade
can invert at the combine: member imprints that cancel within one set need not
cancel across nights whose skies differ.

**Closes when** a combine-level A/B, one knob (the flat window), members from
both arms, is judged at the combine — the level where the disagreement either
averages away or compounds. No instrument here can say which member calibration
is closer to truth, so anything the data cannot settle goes to the owner under
the evidence gate. Numbers and the full trade:
`datasets/july31/set-03/pergroup_work/pergroup_flat_report.json`,
`docs/dead-ends.md`.

## `calibration-master-identity-is-a-basename` — the name cannot distinguish the file

`CALFLAT`/`CALDARK` record a BASENAME, and basenames collide across sessions by
construction here: **19** `skyflat*.fit` masters under `sessions/` carry **12**
distinct basenames, `skyflat_set-01/02/03.fit` each in three sessions, and
`dark_master.fit` is the basename in **all three**. Two colliding masters can also
agree on every other stamped field — july31 and aug06 `skyflat_set-03.fit` both
read `STACKCNT=500`, `NAXIS1=6064` — so one product's calibration provenance can be
byte-identical to another's while naming a different file.

**SEPARATE from the record-vs-reality defect** (fixed at `ea41e5a`; the mechanism
is homed in `docs/dead-ends.md`, *"a basename is not a file identity in a
multi-session corpus"*) and not
fixed by it: stamping from the value that RAN makes the string TRUE and leaves it
AMBIGUOUS. The dark case shows the separation cleanly — no flag exists there to
deprecate and the collision is total, so a record-vs-reality fix has nothing to
bite on.

**ORDERED, and the order is load-bearing.**
(a) **Stamp from what RAN** — root cause; IRAF `setflat.x` stamps the frame it used
by control flow (`:39` resolve, `:54` open, `:130` scale off the opened image,
`:143` stamp).
(b) **Pair the name with a CONTENT HASH of the master, carried as a provenance
VALUE** — ESO `CAL1 NAME` + `CAL1 DATAMD5`, mirrored, inventing nothing. It fits
the 68-char field, needs no flag and no new step, and survives the toolchain
measured (siril preserves foreign keys; only the checksum CARDS drop). Separability
demonstrated on the real colliding pair with the FITS datasum arithmetic as the
probe, **3443652352 vs 884799382**; ESO's MD5 is the shape to mirror, because the
FITS checksum convention disclaims identity in its own text — *"the CHECKSUM
keyword can always be updated after making modifications to the file, leaving no
trace."*
**A session-qualified name derived from the path was proposed and WITHDRAWN** —
that is a naming scheme this project would be inventing, and the standard already
solves it. **(b) is unsafe before (a):** at today's emitter the hash is computed
from the flat the RECORD names, so it is correct on all 78 clean products and wrong
in both failure modes.
(c) **Backfill only behind a bit-reproducible rebuild check** — a backfilled hash
describes today's master, and this corpus has a documented rebuild.

**NOT this item: SELF-integrity** (`DATASUM`/`CHECKSUM` on a file's own header).
Different question, different mechanism, its own item — see the sibling item's
disposition (3).

**(a) AND (b) HAVE LANDED. (c) remains** (a "(d)" once cited here was never
defined anywhere — the sentence entered at `ea41e5a` already dangling; one
occurrence ever). `CALFLAT`/`CALDARK` are built from
the masters that RAN, and `CALFSUM`/`CALDSUM` carry the content hash as a
provenance VALUE in ESO's placement. Both are in `stamp_headers.sh`'s composite
`KEYS` tuple, so a union's `uniq` sees them: measured, two members with the same
`CALSET`, same basename and different files read `CALFSUM MIXED(2)` / `PROVMIX T`
with the hash and **`PROVMIX F` without it** — the old behaviour called that
"provenance consistent". `CALPROV` labels `ran` vs `record` so the fallback is not
silent.
**STANDARDS-FIRST DEVIATION, RECORDED WITH ITS REASON: ESO's field is
`CAL1 DATAMD5` and this uses the FITS `DATASUM` arithmetic instead.** It is a
deviation from the mirrored standard, so it is recorded rather than assumed.
**The reason is functional, not cost.** `DATASUM` covers the DATA records ONLY,
so it is insensitive to header churn: two masters with identical pixels and
different headers ARE the same calibration and hash the same, while **an MD5 over
the file would report a false mismatch on any header touch** — a defect, not
conservatism. Two supporting facts: it is the FITS-REGISTERED arithmetic and siril
implements it identically to `astropy` (measured, same value to the digit on the
same bytes, so a master hashed by either verifies under the other), and it does
separate the real colliding trio (**3443652352 / 884799382 / 369242041**).
The convention's own disclaimer does not reach this use — it warns that a checksum
**in a file's OWN header** can be silently rewritten by an editor, whereas this one
is carried on the PRODUCT and verified by RECOMPUTING from the master.
**THE BOUND, so a growing corpus revisits rather than inherits it silently:
`DATASUM` is 32-bit, so the birthday collision risk scales as n²/2³³.** At 19
masters that is ~2e-8 — enormous margin. A corpus larger by orders of magnitude
should re-derive this rather than assume it carries.

**Closes when** calibration-master identity in a product's header distinguishes two
same-named masters, and a check exists that can be made to fail on demand by
pointing a product at the wrong one.

## `lunar-ladder` — lunar lucky imaging: x86 ladder + next capture remain

**STATE: the first corpus is processed end to end and the chain is codified as
`scripts/stack/run_lunar_pipeline.sh`** (PROVISIONAL as-written — its first
fresh run is the next lunar corpus). Both sets' finals are user-ratified:
sb deconvolution + per-set disc-neutral WB (satu closed-fail; wiener arm
PAUSED on user order — equal on-disc, frame-edge artifact noted). Session
raws/intermediates freed (re-stageable); stacks + judge surfaces in
`web/results/july26/` (freed with the july26 raws — rebuildable); every mechanism in `docs/dead-ends.md`.

**Remains open:**
- **The x86 quality ladder** (best 10/15/20/25% vs the shipped q100 controls,
  PSS `--stack_percent` or AS!4 — pre-registered in both sets' ledgers).
  Needs: PSS venv on the x86 rig + re-staged data (NEFs from archive, replay
  `run_lunar_pipeline.sh` stages, or transfer nothing and re-shoot better).
- **Next lunar capture at the corrected card** (acquisition checklist lunar
  block: disc histogram 50–70% — f/4 · 1/320 s · ISO 800 at 70 mm class) —
  more photons beat every processing knob measured this corpus.
- **Siril 1.5 MPP adoption test** (unchanged — retires the GUI step when
  stable lands and it measures quality).
- Long-focal escalation ladder (unchanged, dormant until such a corpus):
  AS!4-under-Wine vs PSS vs 1.5-MPP head-to-head; waveSharp 3.0 (native
  Linux GUI, frozen) / ImPPG 2.1.0 as judgment-quality finishers; Hugin for
  mosaics; RGB-align only where dispersion is measured (≥ ~800 mm).

Class facts, records and the full mechanism set live in
[`docs/lunar-lucky-imaging.md`](docs/lunar-lucky-imaging.md), `docs/dead-ends.md`
(registration/aliasing/seq-hygiene/quality entries + the acquisition
checklist's lunar block), `datasets/july26/` (ledgers with every verdict),
and the builder's own docstring.

## `web-culled-frames` — one surface for every excluded frame

USER-ORDERED: the Sky Objects section becomes **Culled Frames**, the single
examination surface for every frame the pipeline excluded, grouped by CAUSE — sky
objects (anomaly audit) as one subset, frame-QA defect-side auto-culls as another,
hand-ratified `recipe.json` excludes as a third. Each entry shows frame + sequence n,
set, cause with its metrics, and the record it traces to. The existing culled rollup
MERGES into it. Selection surfaces only — any per-frame preview is Siril-made.
**Closes when** after a chain run with auto-culls the page lists every excluded frame
under its cause and the separate Sky Objects entry is gone from the grouped rail.

## `framing-radec` — reproduce a drawn frame after a stack rebuild

The capture side, the verification and the diagnostic consume side are built and
exercised: a drawn rectangle becomes
`datasets/<session>/framing_<product>.json` carrying BOTH coordinate conventions (the
measured y-flip trap) plus WCS RA/Dec corners, `verify_framing.py` stamps it with
Siril `crop`+`stat`, and `finish_render --crop-record` applies a VERIFIED record to
the LINEAR stack before solve/SPCC/stretch, refusing unverified records and canvas
mismatches.

UNBUILT: deriving the rect on a REBUILT canvas from the record's RA/Dec corners —
today a canvas mismatch is refused, not re-derived. Siril 1.5's `eqcrop` is the
natural consumer. **Closes when** a drawn box renders to a final matching it AND the
record reproduces that framing after a stack rebuild.

## `route-recommendation` — the last wiring on the distortion route

The route is validated, scripted, and the chain routes on the measured key
(`scripts/lib/route.py`: tracked → standard; fixed with `drift_frac` ≥ 0.05 →
undistort groups; below the floor → standard). Remaining:

- **Per-lens facts re-derive at the next new lens/body/focal:** confirm lensfun
  coverage, interpolation behaviour and crop factor before first use. Any focal not
  fitted rides the community entry until fitted (`fit_lens_model.sh` per focal). A
  community profile can be right at the corner and wrong paraxially — the drift-axis
  station measure is the backstop `seqtilt` cannot provide.
- **The undistort route's FLAT source is the per-set sky flat only.** A session
  with real flats staged is refused (`run_set_chain.sh` exit 6; readiness goes
  RED first on the one-click path) with the two commands that resolve it by
  hand (owner precedence: real flats WIN when present — the wiring makes staged
  flats USED, never a recommendation to acquire them). Closes when the chain
  builds a master flat from a staged `flats*`/`calib` dir and passes it as
  `--flat=` — the builder already takes any master, so this is chain wiring,
  not a builder change.
- **The undistort builders take camera raws only** (the route's first stage is
  darktable's lens correction, and darktable reads raws). A FITS
  dedicated-astrocam set now routes here on its measured drift and is refused by
  name (`exit 9`), pointing at the standard route. Closes when a FITS path
  around the darktable stage exists — a BUILDER change, and a real capability
  gap rather than a routing defect.

## `cross-set-record-home` — the corpus has a record home; the FINISH stage still cannot write to it

`datasets/corpus/` now IS the corpus-level home and holds the corpus records —
`baseline.json`, `recipe.json`, `member_selection/` (the stage records + the profile
cache), `smear_attribution/`, the first build's finish records
(`solve_stack_july31+aug06+aug09+aug14_outnorm_presolvefix.json` — NOT the canonical's;
its `_identity` block carries the numbers) and the rest
(`datasets/corpus/README.md`). What is still wrong is the FINISH stage:
`finish_render.sh:66` hard-requires `--session=` and `--set=` ("SPCC spec routing +
record naming"), so a combine's finish records file under the REFERENCE set. The live
wart: the promote of the member-selection canonical (e4468e1) wrote
`solve_stack_july31+aug06+aug09+aug14_full.json` and
`spcc_set-02_july31+aug06+aug09+aug14_full.json` under
`datasets/aug09/set-02/qa_work/` (their `_nosel` predecessors moved aside beside them)
— a session-level product filed as a per-set one, the same defect as the earlier
1760-frame four-set combine's SPCC record landing under set-03. `datasets/README.md`
reserves session-level records for exactly this case (`../render_<tag>.json` beside
`experiments.jsonl`) and the finish stage cannot write one. **Closes when** a cross-set
product's finish records write under `datasets/corpus/` (or the session-level home)
without borrowing a member set's directory.

## `frame-qa-order-dependent-scale` — the same data measures differently by run order

`qa_work/frame_metrics.json` prefers the solved plate scale only if the fingerprint
already carries one, so running frame QA BEFORE the mount probe makes the pooled
record's px→arcsec scale keep the nominal instead of a solved one — 17.5031
nominal vs 18.003 probe, 2.9% apart. It is self-documented via `pixel_scale_source`
and never re-derived once written. **AMENDED (measured during the optics-state
audit): the 18.003 "solved" figure is itself an artifact** — all nine stack
solves across three sessions read 16.98–17.08 ″/px, so the probe pipeline's
green-plane scale arithmetic inflates by ~5.6%; the 13 pooled records it seeded
(july31/aug06/aug09) carry its figure, aug14's five kept the nominal (the order
defect recurred) and per-frame arcsec columns embed the nominal throughout
(px figures unaffected; `datasets/aug06/experiments.jsonl`,
`solved_scale_artifact_18_vs_17`). **Closes when** the scale is re-derived from
a direct full-frame solve (or the record refreshed against the stack solve)
and the probe-pipeline arithmetic's error is root-caused.

## `l1-set02-nonreplication` — two powered surfaces, same night, opposite answers

**OPEN QUESTION, not a scheduled item, and it touches a PAUSED line — see the fence.**

The L1 per-frame-vs-on-stack supplement SPLIT between two surfaces that the
pre-committed power criterion both rates as POWERED, with comparable errors:
set-01 separates at **2.59/2.09/1.47 SE**, set-02 does not at **0.85/0.03/0.48**.
Resolved in the verdict by rule (a split is reported, never majority-voted)
because no mechanism was in hand.

**One candidate is already refuted, at the cost of one lookup.** "The effect grows
with sky span" cannot explain it: the two sets' inter-frame excursions are
`sky_sep_arcsec` 16497.76 and 16549.39 — **4.5827° vs 4.5971°, 0.31% apart**.

**The successor hypothesis, stated so it can be tested rather than re-derived.**
The union's paired deltas say the on-stack arm REVEALS the starlight relation
(+6.34/+12.93/+6.37, 2.22–2.96 SE) while the per-frame arm leaves it unmoved
(−1.39/−0.83/−0.72, 0.31–0.66 SE). If what an on-stack plane reveals is the
anti-correlated `sky × V` residual, then the size of the arm difference should
track **the magnitude of that confound on each surface**, which is a property of
the flat rather than of the geometry. Prediction: the split follows set-02's
FLAT, not set-02's sky. It also explains union-vs-per-set without sky span — the
union is where the most confound accumulates, not where the most sky is.

**FENCED.** Testing it reaches into the flat-residual line, which the owner has
PAUSED pending real flats (`per-group-flat-at-the-combine` carries the pause).
Recorded so the question survives, not to schedule work. **Closes when** the
flat-residual line unpauses — this item rides that pause.

## `composite-header-identity` — the tuple shipped; the rgbcomp/standard-route half and the next-compose read-back remain

**LANDED (`ebbce14`):** the composite stamp now writes `PIPEREV` =
HEAD-at-compose, rides `CALSET` (plus `CALFSUM`/`CALDSUM`) in the MIXED-tuple,
sets `DATE-OBS` to the earliest member start (FITS convention, equals the ISO
of siril's own `EXPSTART`), and deletes `GRPSIZE`/`FILENAME` on composites —
the former candidates (a)–(d), with `CLAUDE.md`'s stamp-scope amended by the
owner. Census + intent trace: `datasets/corpus/piperev_inheritance.json`;
mechanism entry in the registry. Acquisition-block inheritance stays uniform
today; july27's 3.0 s makes `EXPTIME` fire on any future mixed corpus.

**OPEN:** (e) whether `compose.py` rgbcomp composites and `run_pipeline.sh`
stacks get the tuple at all — today they apply NO stamp (absent, not false);
the read-back at the next real compose — TWO real composes have run since (the
candidate at 140c742, the promote at e4468e1) and the read-back is DONE:
`datasets/corpus/member_selection/candidate_msel.json` records `PIPEREV`, `DATE-OBS`
and `NCROPPED` read back from the product, and the rest is READ BACK on the
canonical (PIPEREV 36d9bab, stack_id 1ff0ecea…; `datasets/corpus/piperev_inheritance.json`
`readback_canonical`): `CALSET` 'MIXED(17)', `CALFSUM` 'MIXED(17)',
`CALDSUM` 'MIXED(4)', `GRPSIZE` and `FILENAME` absent, `DATE-OBS` 2026-08-01T02:51:17,
`NCROPPED` 27 — the stamp emitted equals the header read back for every key of the
tuple, so the header-only A/B (pixels untouched) is done; still owed: register/guard
coverage naming the tuple's key set. The compose stamps no WEIGHT key either: the weighting is
recoverable only from Siril's own HISTORY card ("image weighting from image count"
vs "from noise" — the wnoise arm, `datasets/corpus/smear_attribution/weight_noise_arm.json`);
if a weight ever becomes a chain choice it gets a stamped key (STACKWGT). Retrofit
of existing products would ride the retired
`backfill_substack_provenance.sh` precedent (recover from git).

**Closes when** the rgbcomp/standard-route stamping decision is made and recorded
and a guard names the tuple's key set (the read-back half is done, above).

## `set-identity-by-sort-order` — the routing fix landed; three glob-order picks remain

**FIXED (measured colour-neutral):** the two set-identity-from-sort-position
sites (`run_corpus_combine.sh`, `run_session_chain.sh`) now derive session/set
from the composed product's OWN `REGREF` (loud exit if absent or unstaged), and
`finish_render.sh` refuses a composite whose `--set` is neither in the CALSETS
window nor the reference set — fire-tested both ways (the set-0b case stops at
exit 1 with the named error before any tool runs); the two mis-filed records
are relocated to `datasets/corpus/` (the spcc one keeps the `set-0b` token in
its name as the defect's own evidence). Why it mattered — the name is POLICY,
the path is DATA: a wrong `--set` reaches `spcc_run.py` (recipe spec → SPCC
params → `_spcc` pixels), `solve_field.py` (that set's `geometry.json`
foreground → the solve itself), `render_tier.sh` (a RATIFIED block under a
wrong set applies silently; exit-7 protects only unratified names), and
`baseline_guard.py` (wrong baseline → wrong exit-8 verdict); both corpus
firings were by-absence only. Header-only signature for any future consumer:
check `--set` ∈ `CALSETS`, or refuse a singular set claim on `NMEMBER` > 1.

**What remains OPEN here:** the glob-order acquisition-header donor
(`run_undistort_pipeline.sh:286`, `header_capture "$(ls "$P/proc"/pp_c_*.fit | head -1)"` — the fix is `frame_order.py`'s capture-order
emit, but it re-times the ACQHDR donor on wrapped sets and deserves its own
look), the starmask glob pick (`render_tier.sh:269`), and the real corpus-level
record HOME (`cross-set-record-home` — records still file under the reference
set's `qa_work/`, contributing but per-set-shaped).

## `capability-gaps` — real capabilities the pipeline lacks

Each lands as a measured declared delta when its gate opens.

- **Full-size dual-band** — native Ha + 2× drizzle of OIII instead of downsampling
  OIII to Ha's half size. Gated on measured dither coverage (the per-frame
  `dither_phase_frac` record exists).
- **LRGB join** — `compose` REFUSES a `luminance` member, because L joins after both
  parts are stretched and this compose-then-render flow cannot express a nonlinear
  step. `rgbcomp -lum=` is the headless mechanism when an L corpus arrives; the CLI
  `-lum` blend colour space is undocumented — resolve before first use.

## `spcc-sensor-curve` — the accidental response model is retired and the Nikon Z f proxy is pinned; the B/G residual and the body-measured curve remain

Research: `docs/spcc-sensor-curve-z6iii.md` (evidence-classed; §4 the
pre-registered test, §5 the untested premises); the headless resolution trap is
a `docs/dead-ends/siril-behaviors.md` entry. Stages 0–2 SHIPPED: runner 91fc93a,
curves 9521128, recipes 2295ba5, the 22 re-calibrations 7b9d1c6.

**Measured basis.** Headless Siril 1.4.4 resolves sensor/filter/white-reference
names BEFORE loading its database, so every spec-less run used index 0 of every
list — "Generic mono sensor" × Antlia R/G/B × "Average Spiral Galaxy": that model
named explicitly (A‴, `spcc_arm_A3.json`) reproduces the shipped july31/set-01 run
to the digit (K 1.000/0.687/0.927, R/G 0.488722+0.239501x σ 0.140369). A bare
`-oscsensor=` WITHOUT the `spcc_list` preload is echoed and NOT honoured (A′ =
Canon EOS 1D Mark III × Antila RGB_ultra_ii, K 0.681/0.911); with the preload the
names resolve and a spec-less run errors (H0). On set-01 the four named proxies —
Z f 0.697/0.947, Z6 0.696/0.943, D750 0.697/0.945, Z f (energy) 0.698/0.949 — sit
within 0.002 (G) / 0.006 (B); any real OSC curve moves the R/G fit toward the
origin (σ 0.140 → 0.095–0.099, intercept share 0.71 → 0.42–0.48) and none moves
the B/G fit (σ 0.107–0.108, share 0.39–0.44, "imprecise solution" fires);
energy vs photon convention ΔK ≤ 0.002. H1 by the letter: neither WIN nor NULL —
the residual intercept is not curve-driven. H3 unresolved by resolution: the
field's band is 1.2% above the sky and Siril `stat` prints 0.1 ADU16, 5–10×
coarser than the predicted departure (`spcc_h3_band_excess.json`). H4: the owner
approved `set-01_arm_zf_spcc-linked.png` beside the index-0 surface; pin "Nikon Z f".

**Delta declared (7b9d1c6; `datasets/corpus/spcc_pin_zf/pin_record.json`).** All
22 canonical products re-calibrated from their existing `_wcs.fit` (one knob):
over the 17 finals ΔK_G +0.0093 ± 0.0011 (+1.44 ± 0.17%), ΔK_B +0.0191 ± 0.0017
(+2.22 ± 0.20%); nights +1.7/+2.4%, corpus +1.8/+2.4%; n_kept and b_R identical
on all 22; R/G σ 0.131–0.161 → 0.069–0.131 on every product; B/G σ moves ≤ 0.006
and the warning fires 22/22. Guard 17/17 PASS — blind by construction: SPCC's
offsets pin the neutralised sky to the R level, so the centre rows read identical
to 0.1 ADU16 whatever K. The index-0 products and PNGs are kept as `_idx0_` twins
(`moveaside_manifest.json`, 44 files, 8.56 GB).

**Remaining.**
- DONE, owner-accepted 2026-08-29: the 17 baselines re-seeded on the pinned
  products (seed lines equal to the compare measures; stack_id = the pinned
  product's sha; aug14/set-05's ceiling verdict carried forward) and the 44
  `_idx0_` twins disposed under the manifest's identities (0 mismatches,
  8,559,911,176 B; `moveaside_manifest.json` "disposed").
- The upstream MR for the Z f conversion (Apache-2.0 → GPLv3; the database's
  issue #3 asks for it) — the owner's call; the Butcher Z6 stays local (CC BY-NC-SA).
- OPEN, closed by no proxy: the B/G fit's intercept (share 0.39–0.44 and σ > 0.10
  under every curve). Suspects, none measured: the photometry in a dense 17″/px
  field (7.9/17.9 px apertures on blended stars — §4's NULL branch); Gaia XP's
  BP/RP junction at 640–680 nm and its systematics below 400 nm (§1.6); the blue
  edge of the response (UV cut / hot mirror) that no proxy measures on this body.
  Discriminator: a body-measured curve (§1.5 B1 — owner-gated, NOT implied by this
  item) or the same pin on a sparse field (MECHANISM: a crowding-driven intercept
  would fall there, a curve-driven one would not).
- Removal conditions (register): the `spcc_list` preload + log assertion
  (`spcc_run.py` row); the Z f proxy in the recipes + `scripts/setup/spcc_curves/`.

**Closes when** the owner accepts the delta (re-seed + twin disposal done) and the
B/G residual has an owner — B1 scheduled, or the residual registered as a
property of dense fields with its discriminator run.
