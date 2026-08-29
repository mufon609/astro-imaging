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
| `coverage_frame.py` largest-all-covered-rectangle search over Siril `stat` boxes (+ `web/verify_framing.py --channel=`, and the `--regdata-dir=`/`--tag=` A/B flags on `run_undistort_groups.sh`) | an official tool reports, headless, the largest fully covered axis-aligned rectangle of a registered union — or a coverage map ON the union's own canvas that `verify_framing.py --map` can consume | 2026-08-14 | **not fired — and the SECOND disjunct is now ONE HEADER CARD away, not a structural gap.** The disjunct asks for *"a coverage map ON the union's own canvas that `verify_framing.py --map` can consume"*, and the reason recorded below — that `coverage_probe.sh` builds its map through `register -2pass`, so its canvas is not the product's — is now true only of `coverage_probe.sh`. **SWarp removes that objection:** it resamples onto a SPECIFIED output WCS and writes its weight map on THAT canvas by construction (`WEIGHTOUT_NAME`, `CENTER_TYPE`, `IMAGE_SIZE`, `PROJECTION_TYPE`, verified by `SWarp -d`), and it postdates this row's previous check. **The format question `TOOLS.md` left open is ANSWERED and the answer is NO as things stand:** `verify_framing.py` reads the scale from the map's own **`COVSCALE`** card and REFUSES a map without one; a SWarp weight map carries none. **So: does not fire, blocked by a missing card rather than by the canvas.** Two limits travel with it — SWarp answers the SECOND disjunct only (the maximal-rectangle search stays in-house), and a weight map is a WEIGHT, so whether its values mean member COUNT under `--map-min` is UNCHECKED. Original probes, all standing: Siril `stat`/`bg` measure a selection or the whole frame and know nothing about coverage; `seqapplyreg -framing=` picks min/max/COG framings and reports no covered region. The repo held the VERIFY half and the CONSUME half (`finish_render --crop-record`) but nothing that PROPOSED a rectangle, so on a union nobody had hand-drawn a box for, the pinned crop-before-background order could not be followed at all. Every pixel and per-box number is Siril's (`boxselect`+`stat`, one load); in-house is the grid bookkeeping and the maximal-rectangle search. REPORTS ONLY — writes an UNVERIFIED record, crops nothing, exits 0 even when nothing clears the floor. **`--selftest` falsifies on a planted fixture:** the frame is recovered exactly (FITS **[160 100 480 250]**), Siril's own `crop` re-reads it at **Green Min 87.9 against an 80.0 bar** with the box deliberately ASYMMETRIC in y so a flipped origin goes RED, and both known failure modes DO fail — the clipping-channel floor covers **0 boxes**, and a mere-non-zero floor grows the rectangle **480x250 -> 640x350** by swallowing the ringing band. It caught a real defect on first run: Siril prints `Sigma: -nan` on a zero-variance box and the numeric-only regex silently dropped it (`docs/dead-ends.md`), a latent copy of which `starlight_preservation.py` also carried. **`--tag=` is a divergence only because arm builds need a work dir:** without it an arm lands on the CONTROL's members and the resume guard skips every group, so the arm looks built and IS the control. |
| `member_separation.py` cross-match + zone medians | an official tool reports headless member-to-member POST-REGISTRATION positional residuals across a sequence (a scriptable Siril registration-residual map, or a PixInsight equivalent) | 2026-08-13 | **not fired — REBUILT, and the rebuild found the instrument had been measuring NOTHING.** It cross-matched the REGISTERED copies, and `seqapplyreg -framing=max` on a variable-size sequence gives each output its OWN origin (MEASURED **611.9 px** apart on the 28-member union; two members of one set shared **67 of 2000** stars within 12 px, **1721** once re-based). It now reads the members plus the homographies `register -2pass` wrote into the `.seq` and bins by MEMBER-OWN field radius: **0/378 pairs unmeasured against 378/378 before**, in 12 s, monotone **0.22/0.48/1.30/2.43 px** median. **SELFTEST RUN, PASSED AND RE-RUN against real members** (`sessions/aug06/work/l1_msep/in`, 13 members under `register -2pass`): known displacement **3.086 px** measured back as **3.086 px**, and the incident reproduces — **89 cross-matches without the re-basing against 1905 with it** — so the defect that blinded this instrument still fires on demand. Both reproduce to the digit. A bare `--selftest` REFUSES loudly: it cannot run data-free, and exiting into the docstring read as a pass twice. **SCOPE THE ZONE NUMBERS — they are the ones a reader reaches for.** They are member-to-member DISAGREEMENT in the reference member's frame under `-2pass` homographies, NOT the delivered star shape of an astrometrically composed product and not a residual the shipped route leaves. T2 on the 13-member aug06 union: **0.924 / 2.618 / 5.399 / 5.729 px** (median over 78 pairs, centre/mid/outer/corner) while that product's delivered major axis at matched member-own radius runs **0.04-0.25 px above its members'** (`datasets/aug06/corner_work/`). Do not read one as the other. **THE THRESHOLD LAYER IS REMOVED (user-ratified): no PASS/WARN/BLOCK, no `--accept-separation`, no exit-6 abort, always exits 0 — it MEASURES, it does not gate.** Three measured grounds: the quantity is a sum of two terms and the compose makes one of them (two healthy sets read **1.12 / 0.95 px** composed among themselves and **3.02 / 3.38 px** inside a 41-degree 28-member sequence); the bands were anchored on the BROKEN instrument (re-measured on the fixed one: 0.14/0.21/0.38/1.23/3.04/3.28 against 0.144/0.194/0.352/0.934/2.991/2.112, which moves the user-PASSED pair out of PASS); and a band fires on every real compose, which trains the operator to bypass it. **No threshold until the disagreement is attributed between the compose's global registration and the members' optical state (BACKLOG:`compose-homography-smear`) — settled, not an open question.** Siril `register` prints WITHIN-sequence residuals only; nothing reports where two members each place the same star. Built because both prior instruments are MEASURED BLIND: corner `findstar` FWHM ranked a FAILING union (**4.95 px**) above the visually clean control (**5.29 px**), and `seqtilt` read **0.34 px** off-axis for the FAILING union against **0.40** for the PASSING one. |
| optics/calibration FITS stamp (`header_provenance_lines`) | the warp stops being a TIFF round trip, so the model rides through natively (darktable gains a FITS **WRITER** — it has READ FITS since 5.4.1 (MEASURED: full-resolution export from a 6064x4040 `.fit`), and `.fits` output returns *"unknown extension"*, so the round trip is held open by the write side ALONE. The earlier wording *"gains FITS I/O"* became AMBIGUOUS the moment that was measured: half-satisfied, with the text not saying which half, or Siril `register -disto=` — BACKLOG:`native-solve-and-sip`) | 2026-08-22 | **not fired.** The warp is still Siril `savetif32` -> darktable -> Siril `convert`, which carries no FITS header; the blocker is the WRITE side alone — darktable 5.4.1 READS FITS and cannot WRITE it (measured, `stamp_headers.sh` row below). **The row's former second clause — the one-time `backfill_substack_provenance.sh` — FIRED and is EXECUTED: retired 2026-08-22.** Measured 2026-08-14: **93 of 93** `sub_*.fit` under `sessions/` stamped (`DISTMODL` present), 0 un-stamped; state the denominator — a glob anchored to `groups_*/` reads 78, every `sub_*.fit` under `sessions/` reads 93. The script is deleted; its three consumer sites (compose gate message, combine-contract §1/§4-consumer note) point at recovery from git history for an archive restore predating the stamp. Load-bearing why the stamp exists: the lensfun user DB is global, unscoped, single-valued machine state nothing reverts, so a sub-stack that cannot state its own optics cannot be composed safely later — 13 aug06 members under 3 different models once composed into a doubled union and nothing in the product could see it |
| `derive_compose_ref.py` (the multi-night registration reference, `run_undistort_compose.sh`) | siril chooses a sequence reference by a stated, deterministic, order-independent rule of its own — at which point AUTO already computes this | 2026-08-19 | **not fired — measured, siril takes INDEX 0.** Ten `compose_gate_*.json` records at 13/17/22/25/52/77 members all read `reference_member = s_00001`, and an auto arm measured **0 differing pixels of 98,194,977** against an explicit `--ref=1`. So the reference is whatever sorts FIRST: appending a night re-bases nothing, reordering the session arguments re-bases everything. **The divergence is DETERMINISM, not quality** — no choice of reference is materially better at the deliverable: SPCC absorbs the balance **64x** (B/G delta -0.2167 at the compose, -0.0034 after), and `-framing=max` includes every member either way so the sky union is identical, leaving a +0.19% bounding-box change that is empty corner. Fires only on a multi-night set; single-night keeps AUTO, so no single-night product moves. Order-independence is live-tested on the real 77-member corpus (forward and reversed session order pick the SAME member at the same 0.1622 deg) and `--selftest` falsifies all eight rules |
| `compose_preflight.py` + the compose's astrometric post-assert (`run_undistort_compose.sh`) | siril itself refuses to register a sequence whose members carry no usable solution, or the chain has no star-pair path left to fall back to | 2026-08-14 | **not fired — and the EVIDENCE this row used to carry is now FALSE, while the verdict stands.** It read *"it fires on today's corpus — the union's own members (`groups_set-0*_pinned/sub_*.fit`) carry NO WCS, so the guard refuses them at exit 3."* MEASURED 2026-08-14: **no `groups_*_pinned/` dir exists on this rig** (the 18 surviving group dirs are `groups_set-0N` plus `_l1arm`/`_l1ctrl`), and the members that DO survive carry WCS — `sessions/aug06/work/groups_set-01/sub_01.fit` reads `CTYPE1 = RA---TAN-SIP`, `CRVAL1 = 304.4330331279676`, so the guard would ACCEPT them. **The premise is inverted, not merely stale: a corpus statement outlived the corpus.** The condition itself is untouched — siril still does not refuse an unsolved sequence — so "not fired" is correct on the tool, not on the members. Grounds: `seqplatesolve` needs every member solved with SIP order >= 2 and siril reports NOTHING when they are not — it registers what it can and exports a finished-looking product. Measured cost of the silent fallback: roundness 0.458 against 0.974 on the 28-member union. Both halves are live-tested — refusal (exit 3) on unsolved members, acceptance plus "astrometric registration + per-member undistortion CONFIRMED" on solved ones, and `--selftest` falsifies the header checks |
| `solve_field.py` hint-contradiction gate (position > 2x the hint radius, scale outside +-20% of the header nominal; exit 9) | the solver itself refuses a solution that contradicts a supplied position/size hint — today the `astrometry` engine takes hints as search guidance only, and the blind fallback discards them entirely, so a hinted attempt that fails is followed by an unconstrained one whose answer nothing compares back | 2026-08-20 | **not fired, and it FIRES on the one measured false solve.** MEASURED: the corpus union's hinted attempt failed on a seam-contaminated framing=max canvas and the blind fallback shipped RA 6.03 Dec -65.10 at 12.96"/px, logodds 22.3 — against the product's own header pointing RA 309.77 Dec +41.70 (siril's WCS field centre, inherited from the already-solved members, so independent of this solve) and a 17"/px family. Nothing downstream could catch it: siril SPCC ran to COMPLETION on that WCS and produced plausible K factors (R 1.000 G 0.592 B 0.817, 1790/5153 stars kept). Thresholds are budgeted from mechanism, not fitted — integer-mm EXIF focal, XPIXSZ rounding, infinity-vs-marked focal and the TAN centre-to-corner ratio (1.066 at 28.6 deg) sum under 10%, doubled to 20%. The refusal's own numbers reproduce exactly (115.4 deg, 0.7405x). SCOPE LIMIT: 108 records (`solve_sub_*.json` under `sessions/`) are per-member sub-stacks whose headers carry FOCALLEN/XPIXSZ but no RA/DEC, so only the scale leg and the logodds warning are live there. **TWO CORRECTIONS FROM A 2026-08-14 RE-VERIFICATION, and the first is the sharper.** (1) **THE REPLAY IS NOT REPRODUCIBLE FROM THE RECORDS FOR THE CASE IT MATTERS ON.** `hint_available` and `header_scale_arcsec_px` — the fields whose own code comment says they exist so *"a later audit replays it from the record instead of re-deriving the nominal from the hint's 0.6x end"* — are ABSENT from the false-solve record: they shipped WITH the gate, so every pre-gate record lacks them (**134 of 268** carry them, 2026-08-20). **The mitigation postdates the case it was built to make auditable**, and the audit had to do exactly the re-derivation the field exists to prevent. (2) **THE SCRIPT'S CENSUS CLAIMS DEFER HERE** — the three-site count disagreement is resolved by de-duplication (comments + the floor WARNING cite this row; the `1eacee3` shape). **CENSUS 2026-08-20** (`find` `solve_*.json` repo-wide; distinct = unique rounded ra/dec/scale/logodds so dual-writes collapse): **268 records + 1 keyword dump, 176 distinct solves, 82 scale-replayable, 34 hinted**. Position: hinted solves land 0.0002-0.274 deg from the hint against 30 deg allowed; the false solve sat ~110 deg out. Scale, each record against its OWN nominal: 69/82 inside 0.96-0.99; every outlier attributed — the 1.0344 CROP product (nominal 16.488), one 0.9593 sub-stack, and TEN aug14 mount_probe green-window solves at 1.0206-1.0665 (the probe-scale-artifact family — BACKLOG:`frame-qa-order-dependent-scale`); max |deviation| 6.65% = ~3x inside the +-20% band, denominator per-product. Logodds over the 176: 22.3-573.6, exactly THREE below 100 — the 22.3 false solve, and two REAL floor-class (59.5 `j31-3+a06-3_full_onemodel`, 63.0 `corpus4_full_wnbstack`), so "every real solve clears the floor" is REFUTED and the floor stays a WARNING by measurement, not just design |
| `route.py` `DRIFT_FRAC_MIN = 0.05` — the route key's floor | a MEASURED knee exists: an undistort-vs-homography A/B on this mechanism at two drift fractions below 0.25, closing where the removable term drops under the route's own irreducible residual (0.25 px off-axis aberration at full depth). The key itself (sky excursion / field) is mechanism-derived and does not retire with the floor | 2026-08-14 | **not fired — and the floor is EVIDENCE, not a knee.** No knee has ever been measured; the residual is monotonic in drift ("scales with TIME SPAN, not frame count"). 0.05 is the smallest excursion at which the term is measured present — the 9-min/~310 px window arm, `drift_frac` 0.051, whole-frame majFWHM 3.87 px against the full span's 4.74 px at 0.247. The corpus's 12 real sets measure 0.083–0.201, nearest 1.66x the floor, so nothing sits near it. The key UNDER-COUNTS twice (the `-framing=min` trim runs 1.16–1.29x the pure translation; a probe windowed inside the longest continuous run drops the re-aim excursion), which is why the floor sits at the bottom of the measured range rather than inside it. Fire-tested and RE-VERIFIED 2026-08-14 (nothing building, `__pycache__` cleared, `git diff` EMPTY afterwards and the file md5-identical to baseline): flipping the constant moves all five consumers together and back, selftest ratio 1.66x -> 1.38x and 0.05/1.66x restored. **THE PARENTHETICAL'S MECHANISM WAS WRONG AND IS CORRECTED — the instruction is safe, the reason given for it is not what happens.** It read "a same-length edit needs `__pycache__` cleared or importers read stale bytecode". MEASURED: a same-length edit ALONE does not trigger it — 0.05 -> 0.06 propagated immediately with a stale `.pyc` present and no clear. **Python invalidates on (mtime, size)**, so reproducing the trap needs BOTH held fixed (`touch -r` after a same-length edit), which does fire it: source read 0.07 while the importer returned 0.06. Clear the cache anyway — it is conservative and free — but do not expect a same-length edit by itself to hide the change |
| `cfa_control.py` in-house per-ρ-bin binning + least squares on the RAW CFA lattice | retires with `constancy_fit.py`, whose named alternative it tests — **and that row's condition was REPLACED 2026-08-14 after the original FIRED, so this one cascades onto the NEW condition (the sibling contract being provided elsewhere), not the dead `rl -loadpsf=` route** | 2026-08-14 | **CASCADE NOTE 2026-08-14: the condition this row inherits changed.** The `rl -loadpsf=` route it ultimately gated is dead by measurement on three grids, so the ORIGINAL inherited condition had fired unnoticed; the replacement is scoped to `contract_check()`, and this file is one of the two siblings that check enforces — `cfa_control.per_bin` must build rows the shared `constancy()` accepts, which is what caught a real regression that every other check was structurally unable to see. **not fired — and it REFUTES the demosaic alternative.** Siril does every pixel op (`convert` with NO `-debayer`, `seqsplit_cfa`, `findstar`); in-house is the binning, the spin-2 bookkeeping and the least squares. Reads no pixel. **Pre-registration committed at `21653a1` BEFORE the run, with no result attached.** **OUTCOME 1, the free null, PASSES:** the two green sub-lattices agree at χ² 3.00/3, max axis difference 2.73° — the CFA lattice injects no directional term. **OUTCOME 3: the rotation and the gate failure SURVIVE with no interpolation anywhere** — both greens reject a constant axis (χ² 15.8/2 and 37.9/2; constancy fit χ²/dof 28.2 and 46.7). The alternative held that a ρ-dependent demosaic term produces the non-constancy; remove the demosaic and it persists, so the demosaic is not necessary to produce it. **OUTCOME 2 differs and is NOT attributed:** CFA axes sit 2–10° above debayered (χ² 27.1/3 and 23.3/3), ambiguous between the demosaic and severe undersampling (S 0.83→0.415, across Kannawadi's 0.5) — pre-registered as unattributable and left so. **A TOOL TRAP WORTH THE ROW ON ITS OWN: `split_cfa`'s channel order cannot be read off BAYERPAT.** The parent carries RGGB and split_cfa emits in raster order, which reads as channels 1 and 2 being the greens; the DATA says 0 and 3 — cross-matched magnitudes give ch0–ch3 a −0.005 mag offset (MAD 0.115, 706 stars) against 0.28–0.85 for every other pair, and those two share a background median and MAD where the others do not. Reading the header would have compared R against B and called it the green null. DECLARED DEVIATION: 3 bins not the pre-registered 5, forced by the half-sized grid's ~1000 stars/frame against ~7000 — the debayered arm was re-binned to 3 as well so the comparison is like-for-like, and outcome 1 passes at either threshold |
| `frame_depth.py` in-house 40-frame re-run of the per-ρ-bin axis + constancy fit (extends `constancy_fit.py`) | retires with `constancy_fit.py` — **that row's condition was REPLACED 2026-08-14 after the original FIRED, so this cascades onto the NEW condition (the sibling contract being provided elsewhere), not the dead `rl -loadpsf=` route** | 2026-08-14 | **CASCADE NOTE 2026-08-14: the condition this row inherits changed**, for the reason given in the `cfa_control.py` row above; this file is the other sibling `contract_check()` enforces (`frame_depth.per_bin` must build rows the shared `constancy()` accepts). **not fired — and it REMOVES the one-frame condition the verdict used to carry.** Siril does every measurement (`convert -debayer` + `findstar`, the same call verbatim); in-house is the binning, the spin-2 bookkeeping and the least squares. Reads no pixel. **At N=40 the verdict no longer flips on DSC_6239: with it INCLUDED, axis constancy χ² 69.5/4 and fit χ²/dof 53.1 both REJECT** (excluded: 686.7 and 129.4). The 5-frame "nothing rejects" was a small-sample artefact — one anomalous frame is 20% of five and 2.5% of forty. **And "first frame of a run" is NOT a class:** only the first frame of the SET is anomalous (axis −36.91° at robust z = −25.7, next most deviant of 40 is −1.4), while the other four group-starts read +16.29 to +17.50 against a reference mean of +17.39 ± 1.52 — group-starts minus 6239 differ from the rest by −0.44 ± 0.43°, 1.0σ. So the exclusion used across this thread removes exactly one frame, not a systematic. Subset bracket EXACT: restricted to the original five it reproduces `constancy_fit.json` to the digit. Sample is designed, not convenient — four early-in-run and four spread frames from each of the five groups. `--selftest` asserts the class test detects a PLANTED offset and does NOT detect an absent one |
| `constancy_fit.py` in-house per-ρ-bin spin-2 binning + the 3-parameter constancy least squares (`C = f·T + K`) | **CONDITION REPLACED 2026-08-14 — the original FIRED and the file must NOT be deleted.** New condition: the sibling contract this file enforces is provided elsewhere — i.e. `contract_check()` is no longer the thing keeping `cfa_control.py` and `frame_depth.py` conformant with the shared fitter, **or** a tool reports a FIELD-CONSTANT PSF component over a star list | 2026-08-14 | **THE ORIGINAL CONDITION FIRED AND NOBODY FIRED IT** — this row read "not fired" while the route it gated was declared dead 200 lines away in this same file (`corner-fix-landscape`: "the FIX-classified route is DEAD … NO on three independent grids"). "Closed either way" was written for exactly that outcome. The `star_shape_profile.py` failure this table's header warns about, recurring. **DELETION IS THE WRONG DISPOSITION, on a CI fact:** `contract_check()` lives in this file and is the **`constancy_fit` check of the `run_guards.sh` roster** (cited by NAME — this table's own header records ordinal citation as having failed twice, and the ordinal written here was 18 against an actual 21), wired to the pre-push hook — deleting the file silently removes a gate, the one that catches a sibling drifting from the shared fitter. **The current purpose arrived with NO condition**, this table's stated worse case entering as the old one retires; hence the replacement condition. **NOT ESTABLISHED, and deliberately not written as "likely":** whether this code is load-bearing for `one-sided-band`'s unattributed radial term. That trace has not been run. **THE FINDING — it corrected the error model of every per-bin number in this thread.** A star-level bootstrap inside one pooled population understates the per-bin fixed term by a median **5.76x (range 4.1-9.2x)** against the five raws as INDEPENDENT realisations, inflating chi2/dof ~20x **WITHIN ONE BINNING**: `rho_equal` **35.60 -> 1.81**, `equal_count` **40.95 -> 1.57**, both at **dof 7**. **The previously published "~1.1" is WITHDRAWN — it was never in any record** (every `chi2_per_dof` in `constancy_fit.json` enumerated: those six values, nothing in [1.0, 1.2], absent from BOTH revisions, reproduced by two sessions) **and it was paired against 35.60, which belongs to the OTHER binning.** At **nu = 4** the null of a reduced statistic is nu/(nu-2) = **2.0**, so 1.81 sits BELOW its null: the frame-based errors are CONSERVATIVE, not "right". Why it survived, and the paraphrase lesson it produced: `docs/dead-ends.md`. **Retracts the fixed term's "10 to 20 sigma" rotation:** it SURVIVES at chi2 74.6/4 with frame-based errors but only with DSC_6239 excluded; all five frames reject nothing (chi2 3.0/4). Every star, PA and FWHM is Siril `findstar`'s; the trail WCS is astrometry.net's; the conversion is `psf_calib.json`'s fitted kappa. In-house: binning, spin-2 bookkeeping, least squares. Reads no pixel. `--selftest` recovers a planted (f, K) at two settings and asserts a ROTATING residual CANNOT be fitted by a constant (chi2/dof **20136**). |
| `psf_calib.py` in-house synthetic trailed-star FIXTURE renderer + straight-line fit — the SOURCE of the conversion constant κ = 0.49374712819727373 | **CONDITION NEWLY AUTHORED 2026-08-14 — PENDING OWNER RATIFICATION, because this divergence shipped with none:** retires when a tool reports a SECOND-MOMENT shape measurement whose thresholding/windowing bias is QUANTIFIED in a citable source, or measurable on a planted fixture, such that the (2.3548^2/12)*L^2 identity applies with a stated correction rather than an estimator calibration (the earlier *"whose bias is characterised"* set no threshold — characterised by whom, to what precision — so a reader could not say whether `source-extractor`'s `A_IMAGE` already qualifies), making the `major²−minor² = (2.3548²/12)·L²` identity exact rather than estimator-calibrated. `source-extractor`'s `A_IMAGE`/`B_IMAGE` (*"Profile RMS along major axis"*) are the INSTALLED candidate; the open question is thresholding/windowing bias, not availability | 2026-08-14 | **ROW ADDED 2026-08-14, AND THIS IS THE REGISTER'S OWN "WORSE CASE": an adaptation with NO written condition at all — not a docstring condition missing a row, but no condition anywhere.** It was invisible to the declared-but-no-row detector for exactly that reason, so two detectors are needed and only one existed. **Three rows depend on its number** — `constancy_fit.py`, `kappa_transfer.py` and `coherent_trail.py` all cite `psf_calib.json`'s fitted κ as the load-bearing conversion — and `kappa_transfer.py`'s row calls its fixtures *"the same standing as `psf_calib.py`'s"*, equating it to a row-carrying divergence inside a row while giving it none. **The register covered the test and missed the thing tested.** Not fired. Siril `findstar` measures every synthetic star with the same call the real measurement used; in-house renders the fixture and fits the line; no deliverable pixel is read. **Why the OBVIOUS condition was rejected as malformed:** "a tool reports trail length L directly" can never fire — the field has no customer for a sub-PSF trail length (asteroid/streak tools take the rate as an INPUT or target trails many PSF widths long, and weak lensing stops at ellipticity), so nobody is coming. A condition only this project wants is not waiting, it is malformed |
| `kappa_transfer.py` in-house fixture renderer + straight-line fit (tests whether the trail conversion κ survives a realistic base profile) | a tool reports the trail-to-anisotropy conversion for its OWN fitter — **or** no OPEN item in `one-sided-band` / `corner-fix-landscape` still depends on a κ-converted quantity (the testable replacement for the old "or the trail question closes") | 2026-08-14 | **NOT FIRED — and it ANSWERED the premise it was built for.** κ = 0.49374712819727373 reproduced **EXACTLY** (ratio 1.000000, arm A — the harness did not move); the discrete renderer costs **0.14%** (arm B); arms C/D swap the profile and re-randomise placement at matched density, over a shared L ladder, 7×7 supersampling, phase randomisation, amplitude range, Poisson stream, 56 px grid and one `findstar` call. Base is **PSFEx** `psfex_work/deg3/g_00005.psf` (PSF_FWHM 2.401 px at PSF_SAMP 0.511) cut PERPENDICULAR to its major axis — the untrailed base, since a linear smear convolves along one axis only and no untrailed star exists on this rig; its minor-axis FWHM 1.89–2.11 px BRACKETS `psf_calib`'s 2.010 px Gaussian, so the substitution changes SHAPE and not width. Tool probed FIRST and rejected with a measurement, not an opinion: Siril `makepsf stars -savepsf=` ran headless over 322 bright non-saturated stars but returned **9 px × 3 px** at half maximum, a 3:1 elongation ~4× broader than the real stars (2.4 × 2.0 px). **CONDITION REWRITTEN because the old second disjunct could not be evaluated, so it could never fire:** *"or the trail question closes"* was defined nowhere — `grep -rn "trail question"` over BACKLOG/TOOLS/dead-ends returned only the two conditions themselves. Not *nobody wants the capability* (the Oracle's `psf_calib` case) but **nobody can tell when the event happened**; row 54 is the control that makes it a defect rather than pedantry — its question IS closed, it carries no closure disjunct, and "not fired" is correct there. First disjunct separately still open and now sourced: **no tool reports a sub-PSF trail length** — the probe and its better-formed replacement live in `TOOLS.md` Tier 5. `--selftest` asserts the segment adds exactly L²/12 anisotropy at three lengths and puts it in the cross term at 45°; it **FAILED FIRST**, catching two real bugs in this file's own kernel — both recorded in `docs/dead-ends.md`. Reads no deliverable pixel; the frames are FIXTURES, same standing as `psf_calib.py`'s |
| `coherent_trail.py` in-house spin-2 coherent-anisotropy estimator + per-ρ-bin joint fit | Siril (or any tool in `TOOLS.md`) reports a coherent spin-2 moment over a star list — **or** no OPEN item in `one-sided-band` / `corner-fix-landscape` still depends on a coherent-anisotropy quantity (the testable replacement for the old "or the trail question it serves closes") | 2026-08-14 | **CONDITION REWRITTEN for the same defect as the row above: the old second disjunct named an event defined nowhere in the tree, so it could not be checked and could never fire.** The replacement names an artifact a reader can inspect. Verdict unchanged — **not fired** — probed: `findstar` reports per-star major/minor/PA and nothing aggregate; no siril command reports a coherent moment. Every star, every PA and the CONVERSION constant are Siril's (the constant is `psf_calib.json`'s FITTED 0.49375, measured by pushing planted trails through the same `findstar` call — **not** the analytic identity 0.46209, which understates the prediction by 6.41%); in-house is only the spin-2 bookkeeping, the cut ladder and the least-squares fit. Reads no pixel. REPORTS ONLY, exits 0. **Built because the composition was MISSING while its components survived** — the estimator behind this thread's central number existed only as inline code in a lost transcript. Gated on reproducing recorded numbers before producing new ones, and it does: Gate 1A nine numbers on `psf_work/f{1,2,3}.lst` (coherent magnitude 0.586908 = 0.5869, axis 9.1573 = 9.16, projection 0.579819 = 0.5798, frac-negative 0.29329 = 0.294 …); Gate 1B the full cut ladder AND all five per-raw values at once (0.4615/0.7573/0.8026/0.7951/0.8154, ladder 0.7264/0.7276/0.7251/0.7131); Gate 2 the planted control in `--selftest` (n 2735 = 2735, projection 1.3403 = 1.3403, axis 4.9034 = 4.9). **The fixture failed twice before it passed, both times in the FLATTERING direction:** the planted sites are in ARRAY order where `findstar` reports FITS order, so as-is matching recovered 85 of 2765 as chance coincidences and read the REAL population as planted (exact relation, measured: x+0.5, (H−0.5)−y, median residual 0.000 px both axes; the selftest now asserts the unflipped match must FAIL); and `injected2`/`sites2` is the representative frame while the lower-numbered pair is the discarded first-frame anomaly, pinned by a check that it still reads its −29.3° axis |
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
| `baseline_guard.py` derived summaries (corner spread, edge dipole) over Siril `stat` | a tool reports a headless PRODUCT-level regression verdict against a stored reference | 2026-08-29 | **not fired** — nothing does. **Two owner-directed rule changes, both keeping it a no-regression RECORD:** the centre-median rows are ADVISORY while the product's `STACKNRM` differs from the baseline's (re-armed on re-seed; all 17 seeds now carry `addscale`); the absolute corner-spread ceiling WARNS on a CROSSING only — product over it, accepted baseline under it: a `CEILING … EXAMINE THE IMAGE MANUALLY` block, exit 0; a baseline seeded over it was examined at seed and carries the verdict in its note, so a product staying over it prints nothing (owner-approved 2026-08-29 after aug14/set-05's 4.381 seed made the block print on every run) — after it misfired on aug14/set-05's field (a Milky Way band puts a true 4.38% spread on the product; the same measure read 8.2% on the never-seeded `-output_norm` twin; the guard cannot separate sky structure from a flat error). The over-baseline (+1.0), dipole and level rules stay hard; `--selftest` (11 cases, in `run_guards`) keeps the `--desky` class (0.4→12.4%) going RED through the over-baseline rule. WIRED into `run_set_chain.sh` as the last step: it measures the finished product, and a regression exits **8** (a user decision, like the mount/route stops) without blocking or rewriting anything. Also a web stage for seeding/re-seeding. It is a no-regression RECORD, never a quality gate — a deliberate improvement fails it and the human re-seeds with a note. Blind spot to state when reading a PASS: both measures are STACK corners, which `docs/dead-ends.md` calls self-fulfilling for flat contamination, so it cannot see the open `sky x V` object tilt |
| `snr_regions.py` in-house SNR ratio over Siril `stat`/`bgnoise` | a tool exposes headless REGIONAL SNR | 2026-08-05 | **not fired** — `stat` and `bgnoise` are whole-image/selection; no regional-SNR command in 1.4.4. Every input number is the tool's; only the ratio is in-house. *(Was missing from this register until 2026-08-05.)* |
| `fingerprint.py` derived trail/drift geometry | an official tool reports headless trail/drift geometry with a declared-vs-measured mount cross-check | 2026-08-05 | **not fired. BASIS NOTE (2026-08-14): date held deliberately — the 2026-08-14 sweep confirmed only that `--selftest` PASSES in `run_guards.sh` and did NOT re-probe the tool landscape.** Same distinction as the `starlight_preservation.py` row: selftest-green is not condition-re-probed. No solver here exposes inter-epoch drift rate vs sidereal. The record schema and the STOP-on-CONTRADICT contract stay wherever it lands. *(Was missing from this register until 2026-08-05.)* |
| `inspect_stage.py` + `cull_report.py` robust-z per-frame flagging | a tool ships headless per-frame outlier flagging over its own registration metrics (SubframeSelector-class, scriptable) | 2026-08-05 | **not fired** — siril has `seqstat` (per-frame statistics to a file) and `select`/`unselect`, but no outlier GRADING over its own regdata. Persisting the tool's regdata is not a divergence and stays regardless. *(Was missing from this register until 2026-08-05.)* |
| prebuilt-master ingest (`run_pipeline.sh` `<session>/calib/`) | never — this is a supported INPUT class, not a divergence. **DECLARED NON-DIVERGENCE: it is trivially evaluable (it cannot fire) and is retained as an explicit marker, but it must not be counted as a live divergence — the table's row count overstates them by one** | 2026-08-05 | **CONDITION WRITTEN 2026-08-05, previously absent.** The code calls it "the adaptation for master-only data", which made it look like an unconditioned divergence. It is not one: a corpus that ships masters instead of raw calibration is a data class the repo accepts. What IS a stated limit: such masters carry no exposure/gain/filter headers, so the filename token is the whole identity and the exposure match is unverifiable — printed per run. Raw calibration dirs take precedence |
| 16-bit in four instruments (`coverage_probe.sh`, `run_frame_qa.sh`, `fit_lens_model.sh`, `run_lunar_pipeline.sh`) | the leg stops terminating in an integer/8-bit product | 2026-08-12 | **not fired** — each re-verified: `coverage_probe` switches to `set32bits` before its sum stack, `run_frame_qa` saves no product at all (analysis-only register), `fit_lens_model` terminates in `savetif8` for Hugin, `run_lunar_pipeline` pins it on its convert+seqcrop stage step only. Exemptions are enforced by name in `check_bitdepth.sh`, which reports FOUR |
| `run_undistort_groups.sh` group composition (one extra interpolation pass) | a measured quality cost of the extra pass at established magnitude (the along+1300 ledger resolving AGAINST groups), or the combine unit stops being CROSS-SET — i.e. `BACKLOG:final-best-percent-pass` and the cross-night combine contract are both closed or withdrawn (the previous wording, *"cross-set composition leaving the project's goals"*, named no observable state and was UNEVALUABLE; "the project's goals" occurs twice in the tree and never as something a reader could see having happened). **SELF-GATED on its first disjunct** — the measured cost retires only on `rebuild_repeat_floor_set01`, an experiment THIS project must run | 2026-08-06 | **CONDITION REWRITTEN — the old trigger (free disk ≥ the single-pass peak) fired and was judged the WRONG condition: disk cannot retire groups.** Single-pass deletes the sub-stacks the cross-set combine composes and crops to `-framing=min` (composing per-set finals is a registered dead end), so a big disk buys nothing back; groups is the STANDING route (`force_route`), single-pass operator-only (`--route=single`, printed FORCED). Quality, two consistent accounts: the item-scoped one-knob A/B (60 frames even-stride) is **NULL — the route does not cause the one-sided band** (9/9 stations within 0.05 px majFWHM / 0.014 roundness; the band sits in BOTH arms at 1.27x/1.24x); the full-depth ledger records a small along+1300 improvement UNDER groups (0.12–0.18 px, direction replicates across two sets and two group sizes) whose proposed baseline mechanism was FALSIFIED (g250 landed outside the interval) and whose magnitude is UNESTABLISHED until the pre-registered `rebuild_repeat_floor_set01` runs (`datasets/july31/experiments.jsonl`). Peak math stays data-dependent, `W × H × channels × 4 × 2`: 560 MiB/frame at 6064×4040 OSC, 8 MiB mono astrocam, 1378 MiB at 61 MP |
| `scripts/lib/siril_run.{sh,py}` flock-serialized siril-cli invoker | flatpak fixes the instance-dir lifecycle race, or Siril invocations stop being per-frame process spawns (e.g. pyscript batching) so there is no window to collide in | 2026-07-28 | **not fired** — the race is a flatpak lifecycle bug, unfixed at 1.4.4/current flatpak, and every builder still spawns one siril-cli per step. MEASURED serializing: 4 concurrent jobs 1.74 s vs 0.47 s single (3.7x, matching serialized 1.88 s not concurrent 0.47 s), 3 of 4 reporting the wait; shell and python share ONE lock (cross-language test 0.93 s = 2x single). The lock is per-USER so it serializes across sessions on this rig. Every participant is now adopted: the one hold-out (`scripts/jwst/*`) went with the JWST cut, so `check_siril_invoke.sh` carries no exemption and any bypass FAILS rather than being reported |
| `scripts/lib/siril_run.sh` bounded LAUNCH retry (`SIRIL_LAUNCH_TRIES`, default 4) — the complement the invoker's own note reserved for "a non-participating third party" | `flatpak run` stops failing to launch an INSTALLED app: this rig completes a full-session build at `SIRIL_LAUNCH_TRIES=1` with no launch failure in any siril log | 2026-08-23 | **not fired** — NEW, and it exists because the failure was MEASURED here: two 1454-frame undistort builds died mid-chunk on `error: Extension org.freedesktop.Platform.GL.default has invalid merge-dirs` raised by `flatpak run` itself, Siril never started, and the builder died SILENTLY because the caller had redirected siril's output into a work-dir log. TRIGGER UNIDENTIFIED and the obvious hypothesis is REFUTED: 0 failures in 55 locked invocations under concurrent `flatpak list`/`info` AND concurrent `flatpak run`, 0 across the 100-minute build that then completed, no flatpak timers, repo untouched since 2026-07-18. The lock cannot prevent it — there is no second siril-cli to serialize against. Retry is SAFE because the launcher refused to start the app, so nothing ran. Discriminated on Siril's config-ini mtime, with the positive control the acceptance rule demands: siril-ran-script-OK exit 0 / ini CHANGED; siril-ran-script-FAILED exit 1 / ini CHANGED (must NEVER retry — it would repeat a whole stack); launch-failed exit 1 / ini UNCHANGED (must retry). BOTH failure branches exit 1, so the exit code alone cannot separate them; nanosecond `stat -c %y` prevents two runs inside one second aliasing the two. All four branches live-tested, disable knob included |
| `scripts/stack/stamp_headers.sh` — capture + `update_key` restore of the acquisition keys the undistort warp drops | the warp stage stops being a TIFF round trip: darktable gains a FITS **WRITER** — it has READ FITS since 5.4.1 (MEASURED: full-resolution export from a 6064x4040 `.fit`), and `.fits` output returns *"unknown extension"*, so the round trip is held open by the write side ALONE. The earlier wording *"gains FITS I/O"* became AMBIGUOUS the moment that was measured: half-satisfied, with the text not saying which half, or the distortion is consumed natively (Siril `register -disto=`, BACKLOG:`native-solve-and-sip`) so the keys are never dropped | 2026-08-14 | **not fired — but the long-stated reason is FALSE and the blocker is HALF the size this row asserted. darktable 5.4.1 READS FITS; it cannot WRITE it.** MEASURED both directions on two independent inputs: `darktable-cli <6064x4040 .fit> out.tif` exports, and the TIFF is **6064x4040** (exiftool) at 11.4 MB deflate RGB — the image was parsed, not fallen back on; `darktable-cli … out.fits` returns **`unknown extension '.fits'`** and writes nothing, and the format-plugin dir carries avif/copy/exr/j2k/jpeg/jpegxl/pdf/pfm/png/ppm/tiff/webp/xcf with no fits. So the round trip survives on the WRITE side alone. **This governs the shared condition wherever it appears** — the `header_provenance_lines` row above and BACKLOG:`native-solve-and-sip` both reason from the larger "no FITS I/O" premise; only a WRITER is missing. NOT tested: photometric fidelity of the read (dimensions and structure only). Values are Siril's own (read from the raw into the calibrated frame's header); in-house code only READS the header and hands them back to `update_key`. LIVETIME is the one derived value (n_frames × EXPTIME, both tool-sourced) because the per-frame EXPTIME Siril would sum was destroyed upstream. MEASURED restored on july27 set-01: 9 keys, LIVETIME 789.0 s = 263 × 3 s, and the solve regained its hint (`scale hint: 10.5-26.3 arcsec/px`, index scales 11-19, vs the prior blind WIDE-FIELD fallback) |
| `observer_frame_diversity.py` — per-group epoch DERIVATION + the corpus alt/az aggregation behind `datasets/corpus/observer_frame_diversity.json` | the sub-stack builder stamps each group's OWN epoch instead of the set's first `DATE-OBS`, at which point this reduces to an astropy coordinate transform anyone can run inline | 2026-08-14 | **not fired** — every group sub-stack of a set carries the SET's first `DATE-OBS` while its WCS centre has drifted up to 4.9 deg of RA (`docs/dead-ends.md`), so a group epoch must be recovered as `t0 + dRA/15.041 deg/hr`. astropy does the coordinate transform and the WCS read; in-house is the epoch derivation and the aggregation. Reads FITS headers and the tracked site record only, opens no pixel, gates nothing, always exits 0. **`--selftest` plants the defect on real data and asserts it REPRODUCES before asserting the fix catches it** — frozen clock 3.599 deg on a FIXED mount against 0.004 deg derived, 839x, and it fails if the improvement is under 5x so a silently-neutered derivation cannot pass. Regenerates the record it describes: `per_set` reproduces the hand-built original identically |
| `check_solve_records.py` record-vs-artifact pointing join | an official tool reports, headless, whether a plate-solve record's stated solution matches the WCS of the file it names | 2026-08-14 | **not fired** — probed: astrometry.net validates a solve against an IMAGE and knows nothing of our records; siril has no record concept; no tool joins a JSON provenance record to a FITS header. Reads headers and records only, opens no pixel, gates nothing, always exits 0. **It compares the record's field CENTRE against the target's own WCS EVALUATED AT THE CENTRE PIXEL, never `CRVAL`** — `CRVAL` is the tangent point (BACKLOG:`pointing-record-names-the-wrong-frame`) and MEASURED 1.662 deg from the centre on the one product that matters, against a clean-population spread of 0.012–0.364 deg over 22 pairs, so a CRVAL join carries ~5x the signal range as baseline error. `--selftest` falsifies on three arms, the third asserting CRVAL and centre-pixel are distinguishable so a comparand swap goes RED. Found one live case on 23 pairs: a record asserting RA 6.03 / Dec −65.10 for a product whose own WCS reads **115.4 deg** away, the false solve the registry already documents; no threshold was tuned, the gap is three orders of magnitude |
| `scripts/qa/fit_ptlens_joint.py` joint ptlens(a,b,c) + distortion-centre least squares with a projective nuisance | hugin/lensfun fit ptlens + distortion centre jointly against an absolute (catalogue) reference, or no OPEN item in `one-sided-band` / `corner-fix-landscape` still consumes a fitted distortion-centre quantity | 2026-08-19 | **ROW + CONDITION NEWLY AUTHORED — this divergence shipped with NONE** (no `REMOVAL CONDITION` literal anywhere, no row: the register's hole (b) NO-CONDITION-ANYWHERE, live in the tree until now; found by audit, the third instance beside `psf_calib.py`'s precedent). **RATIFIED (owner 2026-08-19).** Not fired: hugin's own d,e stage diverges (d = 6.3e6, the file's docstring) and both consuming items are OPEN. Not invoked by any chain; its model reaches production only through the explicit user-judged promote path (`fit_lens_model.sh`) |
| `scripts/darktable/cp_coverage.py` control-point radial-coverage analysis (rho percentiles + the pre-registered corner-true criterion) | hugin/lensfun report per-radius control-point support against the model's own normalisation, or the fitting route pins control points to a corner-inclusive station grid by construction | 2026-08-19 | **ROW + CONDITION NEWLY AUTHORED — shipped with none; hole (b); RATIFIED (owner 2026-08-19).** Not fired. Imported by `fit_lens_model.sh` only; the CLI's corner-support gate-exit has NO caller (README: imported, not invoked), so the exit-1 path is dead in practice and the analysis is promote-path evidence |
| `scripts/calibrate/spcc_cone.py` hand-rolled nside=2 nested ang2pix cover + `_tan_pix2sky` gnomonic step | (a) cover: siril 1.5 `healpix` adopted AND its pixel list verified to map to the zenodo chunk names (`siril-1.5`), or `astropy_healpix` adopted into this script's interpreter (installed in `/opt/astro-venv`, ABSENT from host python3 — `TOOLS.md`); (b) projection: the step moves to astropy WCS (already imported in this file; used for exactly this in `derive_compose_ref.py`) | 2026-08-19 | **ROW + CONDITIONS NEWLY AUTHORED — shipped with none; hole (b); RATIFIED (owner 2026-08-19). Two clauses, evaluated separately (rule 6). CLAUSE (b) FIRED the same day, owner-directed:** `_tan_pix2sky` deleted, the projection is astropy WCS built from the CD ALONE (the header's leftover PC+CDELT must be stripped — the dual-matrix trap this firing exposed — registry entry; the shed `wcs-dual-matrix-inject` item's close is `7078d0e`). MEASURED A/B, all 34 solved products: chunk lists identical 34/34; new centres agree with the headers' own OBJCTRA/OBJCTDEC at median 1.7 / worst 36.5 arcsec against the retired hand-roll's 17.8 / 151.6. **Clause (a) NOT FIRED** — the ang2pix cover stands until siril 1.5 `healpix` or astropy_healpix adoption. Consequence bound held: chunk SELECTION only, siril names any missing chunk loudly |
| `scripts/stack/lens_preflight.py` pinned-model XML scan — reads the lensfun user-DB XML as TEXT and compares literal a/b/c for the exact lens@focal (deliberately not the fuzzy matcher, which stays the tool's) | lensfun/darktable expose a headless query of the INSTALLED model's coefficients for a given lens@focal, or the chain consumes the model other than through the lensfun user DB | 2026-08-19 | **ROW + CONDITION NEWLY AUTHORED — the leg declared none; RATIFIED (owner 2026-08-19).** Not fired: Debian ships no lensfun query CLI (`lenstool` unpackaged, `python3-lensfun` exposes DB-path helpers only, `liblensfun-bin` update/adapter utilities only — the file's own probe list) |
| `scripts/calibrate/solve_field.py` coverage rescue rung — re-solves on the largest centred box inside Siril's measured covered rectangle when a blind solve starves | the astrometry.net engine accepts a detection-region/subarea constraint of its own | 2026-08-19 | **ROW + CONDITION NEWLY AUTHORED — the rung shipped (a515053) with a LIMITS block and no retirement trigger; RATIFIED (owner 2026-08-19).** Not fired. Standing: a GENERAL SAFETY NET, not the fix for the corpus starvation (the reference derivation was — bf3491e); fires only on NO SOLUTION or floor-class, keeps the strictly better result, soft-by-contract |
| `datasets/aug09/smear_work/rho_march.py` member-attribution bookkeeping (WCS projection + least squares over the re-march's recorded `findstar` measurements) | an official tool reports, headless, coadd star-shape statistics attributed by contributing-member field position — or neither `compose-homography-smear` nor `one-sided-band` still consumes a member-attribution quantity | 2026-08-22 | **not fired** — same gap family as `shape_at_sky.py`/`member_separation.py`, at the attribution step: no siril/PSFEx/SCAMP surface decomposes a union's star shape by contributing member. Every star, FWHMx/FWHMy and amplitude is Siril `findstar`'s (the re-march's own lists); every geometry is the member's own solved WCS; in-house is the projection bookkeeping and the least squares. Reads headers and records only, no pixel, gates nothing, exits 0 (STOP conditions exit 3). Pre-registered BLIND, reading rules frozen before the run (`rho_march_prereg.json`); two controls fired blind on the author's geometry misconceptions — per-set ballhead roll, then meridian convergence dRA·sin(dec) — each verified header-only on all 12 sets before proceeding, both amendments committed before any band data was read. RESULT (`rho_march.json`, replicated at two depths): the union's surviving one-sided band is MEMBER-BORNE — composition-unexplained residual −0.05 ± 0.04 px major / +0.011 ± 0.011 roundness (−1.3/+1.0 SE, perm p 0.21/0.33); the left band samples members' own +x EDGES (pair Δsigned-x up to 1.89 of ±1) and member-own ρ is near zero and wrong-signed (−0.02), so the carrier is member +x-edge proximity (the exit-edge family), not raw radial optics and not the compose |
| `scripts/qa/member_solve_audit.py` per-set Theil-Sen scale trend + SIP-magnitude consistency check over each member's own solver-written WCS | the member solve itself refuses population-inconsistent solutions (e.g. `solve_field.py` growing a required neighbor-band check), making a post-hoc audit redundant | 2026-08-24 | **not fired — NEW, and its basis is measured, not doctrinal:** the astrometric compose registered members by unguarded blind solves, and both aug06+aug14 chains carried wrong-optimum fits — solved 16.791 arcsec/px in a 17.02–17.08 sibling population with SIP terms ~10x the siblings', edge-of-field sky positions bowed 31.5 px (median star-matched, n=1655) against the same member re-solved under a tight `--scale-band`, healthy member moved 0.000 px. A FIXED band is wrong (refraction drifts the effective scale ~0.5%/night — set-04 runs 17.03→16.94 across its own groups), hence the per-set trend. Every number read is the solver's own WCS or a header fact; in-house is the trend + flag rules; REPORTS ONLY, exits 0. `--selftest`: catches a planted wrong-optimum on both rules, does NOT flag a planted refraction drift, and proves a set-median rule would (trend rule load-bearing). Stated limit: blind to the ~0.1–0.2% TAN+SIP3 fit-variance floor (twins of identical data landed 16.973 vs 16.944, both stable, logodds 270+), which is the model's, not an outlier's |
| `run_undistort_compose.sh` + `run_undistort_groups.sh` (final compose) + `run_undistort_pipeline.sh` (sub-stacks, with the `setref lt 1` pin) stacks without `-output_norm` + the normalization-anchor stamp (`ANCLOC*`/`ANCSCL*`/`ANCREF`/`ANCSRC`, `STACKNRM=addscale`, `REGREF`/`REGREFSR=pinned` on the per-set final) | Siril offers a reference-anchored (or per-channel, non-min-max) output normalization — then `-output_norm` returns and the ANC* keys retire | 2026-08-28 | **not fired — NEW.** A deviation from Siril's OSC-script default TOWARD the linear-photometric standard (a defined, reproducible zero point tied to the normalization reference, display scaling separate); basis `docs/dead-ends/stacking-compose.md`, the `-output_norm` zero-point entry (E0-E3; the item `output-norm-zero-point` CLOSED, owner-accepted 2026-08-29 after the from-raws campaign — record `datasets/corpus/campaign_zeropoint/campaign_record.json`, 12 baselines re-seeded + aug14's 5 seeded on the accepted products). First product under it, aug06 set-01+02+03 `_nooutnorm` (ledger aug06 `output_norm_zero_point_compose_tier`; `datasets/corpus/pedestal_work/go2_compose_nooutnorm.json`): ANCLOC read back 0.00111621/0.00197157/0.00153994 = the M lines to the digit; level 72.808/128.792/100.545 ADU16 = the reference's −0.47/−0.32/−0.37%; H1 ΔK 0.000/0.000; H2 R/G 0.5653, B/G 0.7807; H3 4 clamped px of 30.1 M, both components member-backed, 0 in-frame zeros; against the hand-stacked E2 preview 87,798,306 px differ by ≤5.96e-7 (0.039 ADU16) — cached 6-digit M-line statistics vs a fresh stack (`siril-behaviors.md`), not a knob. The post-assert greps Siril's own "Output normalization ...... disabled" and exits 4 otherwise; the wording is observed on 1.4.4 only, and a change aborts loudly rather than passing. `check_removal_conditions` already matches both basenames through older rows (`derive_compose_ref.py`, `compose_preflight.py`, the `--tag=` row), so this row is owed by the register's rule, not enforced by the guard. Per-set final under it, aug06/set-01 `_nooutnorm` from the existing five members (ledger aug06 `output_norm_zero_point_perset_final_set01`; `datasets/aug06/set-01/qa_work/refinal_nooutnorm.json`): ONE pixel-moving knob proven — clamp((new − 58.766 ADU16)/0.98255) reproduces the shipped `stack_set-01_full.fit` with 0 of 52,966,158 pixels differing above 1e-7 (`-transf=homography`/`-interp=lanczos4` are Siril's defaults, the 2pass re-picked image 1); level = the pinned member's own sky (ANCLOC ×0.997-0.998), R/G 0.5656 B/G 0.7806 vs the anchor's 0.5659/0.7806; 0 clamped, 0 in-frame zeros; K 1.000/0.640/0.860 unchanged; `baseline_guard` ADVISORY on the level rows (×2.35 post-SPCC — SPCC's b-offsets carry a constant ~28 ADU16 in R, so the neutralized level tracks R's pre-SPCC level, not G's), structure measures 0.297 / +0.0025 PASS and shrink with the pedestal exactly (0.699 × 43.0/101.1 = 0.297) |
| `scripts/calibrate/spcc_run.py` `spcc_list oscsensor` preload before `spcc` in the generated `.ssf` + the post-run log-order assertion (`SPCC JSON metadata loaded` before `SPCC will use`; the model listed verbatim by `spcc_list`; the model echoed by `spcc`) + the on-disk database preflight (the model exists as an `OSC_SENSOR`; an `is_dslr` model requires `-osclpf=`) | Siril loads the SPCC metadata before resolving names in `do_pcc` (1.4.4 resolves at `command.c:10152-10188` and loads at `:10205`; upstream master `ee7b942` still resolves first) — then the preload and the assertion retire; re-check at every version bump (BACKLOG `siril-1.5`) | 2026-08-29 | **not fired — NEW.** MEASURED (`datasets/july31/set-01/qa_work/spcc_h0_probe.json`, the H0 probe): a spec-less headless run resolves to index 0 of each list — "Generic mono sensor" × Antlia R/G/B, the model behind every shipped K record — and its log prints `SPCC will use mono senor "(null)"` at line 52 BEFORE `SPCC JSON metadata loaded` at 53; with `spcc_list oscsensor` first the load line precedes the use line (52 < 105, 56 < 109), "Nikon D750" and "Nikon D500" are listed verbatim and echoed, K 1.000/0.697/0.945 vs 1.000/0.700/0.955 (ΔK_G −0.003, ΔK_B −0.010) against the index-0 1.000/0.687/0.927 on the same input, the R/G fit sigma 0.140 → 0.095/0.093; the spec-less arm errors with Siril's own "Either the sensor or a filter was not specified ..." (exit 1, no K); the photometry prefs persist nothing. The spec-less refusal itself is Siril's own contract (no row); `readiness_report.py` reads RED on a set without a recipe `spcc` block until stage 2 pins a curve. |
| The **Nikon Z f proxy response** — `scripts/setup/spcc_curves/convert_curves.py` + `fetch_sources.sh` (`Nikon_Zf.json` / `Nikon_Zf_energy.json` tracked, `Nikon_Z6.json` cache-only by licence) installed as untracked `OSC_SENSOR` files in the siril-spcc-database clone and pinned by every canonical set's `recipe.json` `spcc` block (`{"oscsensor": "Nikon Z f", "oscfilter": "No filter", "whiteref": "Average Spiral Galaxy"}`) | a curve measured on THIS body (a grating on a CALSPEC standard — `docs/spcc-sensor-curve-z6iii.md` §1.5 B1, owner-gated) or an upstream "Nikon Z6 III" `OSC_SENSOR` entry lands — then the recipes name it and these files retire; re-check whenever the siril-spcc-database clone is updated | 2026-08-29 | **not fired — NEW.** A proxy by dye family, not by die: the Z f / Z6 share Nikon's CFA dyes and hot-mirror generation with the Z6 III (IMX820AQJ) by assumption, measured by no one. MEASURED on july31/set-01 (`spcc_set-01_arm_{zf,z6,d750,zfe}.json`): the four named curves within 0.002 (G) / 0.006 (B) on K; every real OSC curve moves the R/G fit toward the origin (σ 0.140 → 0.095–0.099, intercept share 0.71 → 0.42–0.48) and none the B/G (σ 0.107–0.108, share 0.39–0.44, "imprecise solution" fires); energy-vs-photon convention ΔK ≤ 0.002. Pinned on the owner's H4 approval of `set-01_arm_zf_spcc-linked.png`; all 22 canonical products re-calibrated from their existing `_wcs.fit` (41eecff): ΔK_G +0.0093 ± 0.0011 (+1.44 ± 0.17%), ΔK_B +0.0191 ± 0.0017 (+2.22 ± 0.20%) over the 17 finals vs the accidental index-0 model, n_kept and b_R identical on all 22; records `datasets/corpus/spcc_pin_zf/pin_record.json`, `scripts/setup/spcc_curves/RECORD.json`. |
| `swarp_compose.sh` + `swarp_weight_maps.py` (SWarp per-member MAP_WEIGHT compose: split → seqstat-derived addscale re-creation via BACK_DEFAULT/FLXSCALE → CD-only TPV `.head` per member → weight maps → 3 coadds → rgbcomp → stamp) | Siril's compose accepts per-member weight maps (a per-pixel weight per sequence member in `stack`/`seqapplyreg`), at which point the SWarp engine and every re-creation of addscale in it retire | 2026-08-29 | **not fired — and the route is STOPPED, not adopted: scaffolding only.** Written for the tapered-weight arm of the corner-smear work and stopped by the owner before any arm was built (the tapered form's purpose — keeping the rim's coverage — is out of scope by the owner's word; ledger lines 115–116, `datasets/corpus/smear_attribution/swtaper_probes.json`). What stands are ENGINE FACTS measured on this rig's SWarp 2.41.5 (P1–P7): SWarp reads only the first plane of a cube; reads CD and ignores PC/CDELT when CD is present; applies TPV terms; pins the output grid from a `.head` exactly; SUBTRACTS the BACK_DEFAULT list; with RESCALE_WEIGHTS N a MAP_WEIGHT 3:1 planted mean reproduces to 0.004 % and with Y it fails (the positive control); DIVIDES a map's weight by FLXSCALE² (a quality-weighted arm must pre-multiply by f²); sip_tpv is exact on CD-only heads (≤ 4.8e-11 px) and a head carrying CD AND PC/CDELT makes astropy misread the TPV sky. The in-house parts are the weight-map writer (a formula over tool-sourced numbers: x_c from Siril findstar via the crop rule, STACKCNT and W from the header — no deliverable pixel read) and the addscale re-creation; every resampling and combine is SWarp's. NOT on any build path; no product built from it; `swarp_weight_maps.py --selftest` (6 cases) is the only thing that runs. Resume condition, separate from removal: a quality-WEIGHTED form (continuous per-pixel weight by measured quality, both sides of a member) is wanted after the exclusion rules settle — then the arm-scale paths (3 coadds, rgbcomp, stamp) and P3's Siril comparison are the unbuilt half. |
| `run_member_crop.sh` + `member_profile.py` (the corpus combine's MEMBER-SELECTION stage: per-member station profile → the portion rule → curated dir of symlinks + Siril-cropped copies; `run_corpus_combine.sh --portion-rule`) | Siril's compose accepts per-member weight maps or a per-member region mask (a mask is the crop without the coverage cost) — the same condition the SWarp scaffolding row carries, and they retire together | 2026-08-29 | **not fired — the ENCODED portion rule (owner: "go ahead and encode it"), measured before encoding.** The rule (asymmetry FWHM(+dx) − FWHM(−dx) > bar, onset − half-width, intrinsic, rankless) is the owner-approved cropT arm's, verbatim; every constant lives in `datasets/corpus/recipe.json` (bar 0.20 px, stations ±600..±2400, r 400, top-30, half-width 300), never a script default. Every pixel op and measurement is a tool's (Siril findstar via `star_stations.py`; Siril `crop` of COPIES — originals never written); in-house is the rule arithmetic over the tool's numbers, the curated-dir bookkeeping, and the per-member profile CACHE (sha256 + geometry keyed, tracked). The frame-level score S_i rides along as an ADVISORY only (the GO #16 NULL). SCOPE: the corpus combine only; the per-set finals are not run through it until measured there. `--selftest` (in `run_guards`) falsifies on synthetic members: a planted profile crossing the bar MUST crop at onset − half-width with the four MEMC* keys and kept-pixel identity; a flat profile MUST come out a symlink with none; a SYMMETRIC both-sides rise MUST NOT crop (the refuted intrinsic form); the pinned-reference refusal; the cache path (second run 0 profiled, verdicts identical, cache byte-identical). Composite provenance: `stamp_headers.sh` aggregates NCROPPED/MEMCRULE/MEMCXCS/MEMCPROV, never crashes on the legacy prose MEMCROP of the GO #12/#13 arm copies (LEGACY(n)), and a mixed-rule compose is REFUSED in the stamp (the hard stop is the caller's — stated, an UNCHECKED shared premise of both workers). The combine surfaces a derived reference that the rule cropped (a cropped anchor is UNTESTED — loud warning + reference_cropped in the stage record, never a refusal). Decision map + encoding design: `docs/corner-smear-member-selection.md`. |

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
   is recorded and not just held:** effort spent RESTRUCTURING `dead-ends.md`
   internally is effort that may dissolve, so it should not be started. Deleting
   entries whose test is solved and no longer valuable — the rule ratified the same
   day, in that file's own preamble — **survives either outcome**, because the
   content leaves the tree regardless of which file survives. Reorganisation does
   not. Prefer the operation that is robust to the ruling.

2. **L2 may reopen.** Cosmic Clarity's chroma knob saturates above 0.85, but no
   record says which `--denoise_mode` that was measured under. `render-ladder` is
   user-gated and not the PM's to promote.

### Owner rulings that existed in NO other file

**The per-member trim — RE-RULED (owner 2026-08-22): DIRECTED TEST, superseding
the WAIT ruling — EXECUTED (6d9e568, 2654d31, d9e6081; outcome below).** The WAIT stood on the cause being unknown; that premise
weakened when the surviving union band was ATTRIBUTED member-borne with the
compose exonerated (`datasets/aug09/smear_work/rho_march.json` — the rim is
built exclusively from the members' own frame edges), so trimming *"each side by
about 5% ... so the worse part of each image never makes it into the stack"*
(owner's words) is a mechanism-matched mitigation, not a blind step. The
degradation itself remains VISIBLE to the owner on the full-frame render and is
not a below-threshold residue. Directed as a measured TEST, sequenced AFTER the
dead-ends cleanup: one knob (per-side trim fraction), control untrimmed, judged
at the COMBINE on the shape march + a rho_march re-run + the coverage/area cost,
plus the owner's eyes on full-frame lossless; still a TRADE by doctrine (ships
less sky — the rim thins or moves inward). The 80%-keep datapoint (4 of 20
union boxes left with NO contributing member) is why ~5%/side is the first arm,
bracketed mild. **If the trim WINS, the corner-chase dead-ends material prunes
(owner-directed)**, keeping only entries load-bearing elsewhere (lensfun
ρ-normalization/corner support, the per-set-model refutation, the error-model
rules).
**OUTCOME — RAN, REFUTED, NO TRIM SHIPS** (ledgers: `datasets/aug06/experiments.jsonl`
`frame_crop_5pct_per_side_before_registration` + its correction; `datasets/aug14/
experiments.jsonl` `crop5lr_cross_night_combine_aug06_plus_aug14`,
`crop5lr_cross_night_RIM_DEGRADATION_root_cause`, `member_solve_scale_band_fix`;
records `datasets/corpus/crop_work/`). Ran 2026-08-23 (6d9e568) as `--crop-lr=0.05`
— Siril `seqcrop`, 303 px/side of 6064, after undistort, before `register` — one
knob against the accepted aug06 union: shared-sky shape NULL (18 sky-addressed
boxes: median ΔFWHM +0.0025 px, Δroundness −0.002; star stations within 0.03 px /
0.011) at a measured coverage cost (canvas −8.7%, amplitude-matched stars −1.09%,
−5.5 to −11.6% in three outer boxes); the discarded sky is only modestly worse than
the outer band kept (FWHM 2.784 vs 2.748 px, roundness 0.885 vs 0.924) — the crop
removes bad sky, it does not improve the sky that remains; the aesthetic verdict
was the owner's. The cross-night arm (aug06+aug14, 38 members, 4138 frames, same
reference pinned; 2654d31) FAILED all three owner hypotheses — alignment (cross-night
centre pair separation 0.718 → 0.895 px, +25%), stars (amplitude-matched −3.43%),
roundness (0.932 → 0.929, NULL) — and the owner saw a smeared left rim the
shared-interior grid could not: ROOT CAUSE, the crop damages no member (same member,
same sky, cropped vs not: FWHM within 0.005 px) but changes WHO reaches the rim — rim
sky is covered only through members' frame-edge bands, so the 5%/side crop drops the
diverse good contributors (7 members from 4 sets → 2–3 from one set; composite FWHM
3.257 → 3.487; median ΔFWHM +0.133 px where ≥2 sets are lost vs +0.012 elsewhere). The
smear also unmasked a real chain defect in BOTH chains — unguarded wrong-scale member
solves (16.79–16.99″/px against a 17.00–17.08 population; cross-chain bow 31.5 → 1.4 px
once fixed) — closed by `solve_field.py --scale-band` + `member_solve_audit.py`
(d9e6081), which healed the arm's centre regression (0.895 → 0.78 px) and part of the
rim; the structural cost stayed. The +8.3% "pedestal" between the arms was a PROPERTY
of `-output_norm`'s single-pixel min/max zero point (0f924f5) and became the
`output-norm-zero-point` campaign (closed, owner-accepted). The knob is REFUTED (H1/H2/H3
+ rim) and registered — `docs/dead-ends/stacking-compose.md`, the retired `--crop-lr`
rule; the arms were deleted in the rig cleanup (06e5622), the records stand; the
corner-chase prune conditional on a WIN did not fire.
**The owner's own mechanism for the corners**, field knowledge that matches what was
measured: the far-corner stars are ALWAYS at the edge of a member's frame, so the
union corner is built exclusively from worst-case samples — *"the stars being stacked
are the worse images possible."* The corner work measured that axis independently
(member-own field radius **+0.53 px per unit ρ, 3.6 SE**; coverage depth **0.2 SE**).
The open half — whether properly centred frames would change it — is acquisition-side
and therefore not a route this repo takes (MEMORY: the data is a given).
**Also ruled, and recorded elsewhere already:** the L1 judge triple
(`datasets/aug06/l1_work/owner_ratification.json`), the two parallel-session rules
(`b36ef3b`, `64f61d2`, both verified in `CLAUDE.md`), and starlight preservation as a
logged UNCHECKED premise that blocks nothing
(`datasets/aug06/l1_work/unchecked_premises.json`).

### Queue items that had no home in this file

- **`--weight=noise` corpus arm** — motivated by a MEASURED 18–24% cross-night noise
  gap (aug09 haze, +0.16 mag extinction, 16,913 matched stars); pre-registered
  one-knob A/B against the shipped `nbstack` corpus, judged on `snr_regions` +
  `shape_at_sky` + the owner's eyes. Repositioned by the member-selection work:
  weighting is the standards-first ALTERNATIVE to exclusion and is queued BEHIND the
  exclusion rules, because a scalar per-frame weight cannot address portions of a
  member (`docs/corner-smear-member-selection.md` §6); the per-pixel (SWarp) branch is
  closed by the owner's stop, this scalar branch stays open. Read any bgnoise-based
  judgment of it against the field's regime: member/canonical bgnoise ratio 1.8–2.5×
  where a photon-limited mean would read 8.8× — bgnoise is structure-limited here.

(The real-flats HANDLED path re-homed into `route-recommendation`'s flat-source
bullet; pooled master darks re-homed into `dark-optimization-fork`.)

**Closes when** the owner rules on the two-file question and the
`--weight=noise` arm is scheduled or refused.

---

## `compose-homography-smear` — the union's smear is ATTRIBUTED TO THE MEMBERS, not the compose; the reprojection route and the model questions are what stay open

**STATE (measured; the map is `docs/corner-smear-member-selection.md`).** The
surviving left-band / bottom-corner smear of the multi-night union is NOT a
registration or compose defect: the drift-span discriminator this item named RAN
(three nested arms, 26.1 / 104.3 / 235.7 px of span — the exit-side blur flat within
ΔFWHM −0.025..+0.055 px across 9×), the band is built exclusively from the members'
own ENTRY-side columns and reads on them what the union reads, it is present in
single raws and night-ordered (aug14 softest), and the corners are the lens's
asymmetric term. Member SELECTION removes it: the per-member entry-side THRESHOLD
crop `cropT` (27 of 77 members' columns beyond the asymmetry onset; band 2.97 → 2.79
px at full depth, no seam) is owner-approved (2026-08-29); a frame-level threshold
on top of it is a measured NULL. What this item still holds open, below: the
SCAMP/SWarp reprojection route (untested as a coadd; its motivation as a smear fix
is gone, the route itself is untouched), interleaved groups, the corner-true shared
model, which single model, the state-change detector, the candidate model with corner
support. The historical body follows; where it names the compose or the exit edge as
the carrier, the measured state above overrides it.

**The sub-stack compose is a MOSAIC and is being aligned with a single homography.**
A group is a consecutive time block, so within one 1497 s burst the sky sweeps 6.25°
and a set's five members solve to centres **4.28° apart**. MEASURED at RA 294.86 /
Dec +44.99 (Siril `findstar`, 800 px boxes placed by each product's own solved WCS,
30 brightest fits so depth is rank-matched): all five aug06/set-01 members read
**2.42–2.54 px / roundness 0.924–0.942** at own-field radius 0.41–0.62, and their own
5-member compose reads **3.48 / 0.582**; the 13-member union 0.530, the 28-member
cross-night union 0.458. Control at RA 314.72: compose **2.43 / 0.949** against members
at 0.903–0.958. Mechanism and the full numbers: [`docs/dead-ends.md`](docs/dead-ends.md).

Cost on the accepted cross-night union, 19 columns marched at 5% steps: **roundness
0.448–0.613 over x = 15–30% of the canvas width** against 0.916–0.968 in the clean
band x = 45–70%. That is the smear the owner named.

**RE-MARCHED UNDER THE ASTROMETRIC ROUTE. The headline does NOT reproduce; a weaker
one-sided band survives and is UNATTRIBUTED** (`datasets/aug09/smear_work/smear_remarch.json`
— Siril `findstar` via `shape_at_sky.py`, this item's own method and grid, on the
surviving 52-member three-night union). **The clean band is the control that makes
the rest comparable: 0.918–0.976 against 0.916–0.968.** x = 15–30% reads
**0.878–0.917** against 0.448–0.613, and the four-position ladder reproduces the
ASTROMETRIC arm — RA 294.86 **0.980** against `02cf170`'s astrometric 0.974 /
star-pair 0.458. **What survives is one-sided and shifted left of where this item
put it: x = 5–25% at 0.878–0.885 against its MIRROR x = 75–95% at 0.950–0.968.**
**CORRECTION — an earlier revision of this paragraph called the FWHM profile
SYMMETRIC and that is FALSE.** It is U-shaped AND tilted: across the 9 mirrored
pairs the odd (left−right) term runs +0.180 px at x05/x95 down through zero near
x30/x70 and to −0.100 at x35/x65, and **8 of 9 pairs carry the SAME handedness in
both quantities** — the side with the larger FWHM is the side with the worse
roundness. So the asymmetry is not the radial field term, and it is not absent
either.
**MAJOR vs MINOR SPLITS IT, from the tool's own per-star `FWHMx`/`FWHMy`
(no new data — Siril's surviving `findstar` lists, same 30 brightest):** over the
outer pairs x05–x25 the MAJOR axis differs by **+0.206 px** mean while the MINOR
differs by **−0.038** and does not hold a sign (+0.045, 0.000, −0.070, −0.080,
−0.085). **Major grows, minor approximately does not — the signature of a one-sided
anisotropic ADDITION rather than a scale change**, which keeps the convolved-blur
family live. Note `fwhm_px` in the record is the MEAN `(FWHMx+FWHMy)/2`, not the
major; do not read it as one.
**ATTRIBUTED — MEMBER-BORNE; the compose is EXONERATED for the surviving band**
(`datasets/aug09/smear_work/rho_march.json` — pre-registered blind, reading rules
frozen before the run, replicated at two selection depths): after
member-composition controls the canvas-tied residual is **−0.05 ± 0.04 px major /
+0.011 ± 0.011 roundness** (−1.3/+1.0 SE, permutation p 0.21/0.33). The left band
samples the members' own **+x EDGES** — pair Δ(mean member-own signed-x) up to
**1.89 of a ±1 range**, because canvas-edge sky is reachable only by member frame
edges — and the channel split says member-own ρ composition is near zero and
WRONG-SIGNED (−0.02), so the carrier is member +x-EDGE proximity — their ENTRY
side, measured later as night-dominated and in the photons (`docs/corner-smear-member-selection.md` §2) — NOT the compose. The
fitted member-radial slope, +0.435 px/unit ρ, independently reproduces
corner_work's union measurement (+0.53 px/unit ρ). No compose change removes what
rides in with member edges; the surviving-band question re-scopes to the member
edge term.

**METHOD FACT — CANVAS-X FRACTIONS ARE NOT PORTABLE ACROSS PRODUCTS, and a band must
be addressed in SKY coordinates.** On the 52-member canvas this item's own defect
point RA 294.86 sits at **x = 76.2%** and its control RA 314.72 at **x = 41.2%** — so
"x = 15–30%" *there* addresses RA 328–320, not the sky the 0.458 was measured on.
Marching only the stated band measures different sky and reads clean.

Ordered work — nothing here is executed on an accepted product:

1. **Reference pinning is RESOLVED** — the compose registers all members in one
   sweep with the reference setref-pinned (a deterministic level anchor).
   **THE ASTROMETRIC ROUTE IS THE SHIPPED DEFAULT, settled by the artifact.**
   Two closed wrong beliefs from the route fight are homed and not restated
   here: *"Siril discards per-image distortion by design"* is REFUTED (the SIP
   undistortion is COMPOSED with the linear projection at `seqplatesolve`;
   `register -disto=` is the different, shared-solution command) and the SWarp
   trial was never run — SWarp has NO SIP reader at all; mechanisms + quotes in
   `docs/dead-ends.md` and `TOOLS.md`. The compose is `seqplatesolve s`;
   `register -2pass` survives only behind `--starpair`, which prints *"NOT the
   shipped route … must never build a product anyone judges or ships"*; the
   compose greps siril's OWN log for *"Astrometric registration computed"* and
   *"undistortion will be applied"* and exits 4 if either is missing, and the
   stamp defaults `REGU=F`, flipping to T only on that line. `web/results/aug06/stack_set-01+02+03_full.fit`
   carries `REGMODEL = astrometric`, `REGUNDIS = True`.
   **SO THE 0.458 IN THIS ITEM'S HEADLINE IS THE REGRESSION ARM'S NUMBER.** One
   knob on the 28-member union, same members/order/reference/framing/stack, star
   counts within 1-2% at every position (`02cf170`): star-pair 4.383 px / 0.458
   roundness at the defect against astrometric **2.678 / 0.974**; RA301.58
   0.725 -> 0.917; RA308.20 0.931 -> 0.946; RA314.72 control 0.968 -> 0.961 —
   monotone in the defect's own size, control unchanged. Canvas answered separately
   (`82fa507`): MORE sky, 800.1 vs 773.5 sq.deg. Rebuilt from raws by a fresh-eyes
   session at 0.980 (`bac4616`) and OWNER-PASSED (`e04077f`), which recorded *"the
   parent item's reference-pin and SWarp-trial bullets are resolved by the same
   adoption"*. The register row for `compose_preflight.py` above already carries
   this; the item did not.
   **ANSWERED — re-marched; the numbers and their caveats are in the header above.**
   The RHO AXIS has now RUN and ATTRIBUTED the surviving band — member-borne, the
   compose exonerated for it; verdict + numbers in the header above
   (`rho_march.json`, design + frozen reading rules in `rho_march_prereg.json`).
   The ORIGINAL 19 columns stay unreproducible: their subject
   `stack_j31-3+a06-3_full_onemodel` is deleted, so the re-march is a FIRST
   measurement and nothing diffs column-by-column (`docs/dead-ends.md` carries this
   as the worked example of UNREPRODUCIBLE BY CONSTRUCTION).
   **NONE OF THIS TOUCHES THE OPTICS TERM** in "What the defect IS" below — a
   single-frame aberration no registration reaches.
   **THERE IS NOW A CANDIDATE ROUTE WITH ITS FIRST LINK MEASURED, AND TWO ENTRY
   PATHS — both installed. IT IS NOT YET "THE ROUTE", AND CALLING IT ONE WOULD
   REPEAT THE FORM OF THE ERROR ABOVE:** the line this replaces declared an
   UNMEASURED architecture ADOPTED, and a TPV chain that nobody has run is also an
   unmeasured architecture. What is measured is the first link (`sip_tpv`'s
   conversion) and the components' availability; the coadd itself is untested and
   nothing has been resampled.
   SWarp reads **TPV** natively (`fitswcs.c:801`, `:843`), so:
   (a) **convert our own SIP** — `sip_tpv` 1.1, whose forward direction is a
   symbolic sympy substitution and NOT a fit, measured exact at **1.118e-11 px max
   over 3600 points and FLAT in field radius**, against a distortion-stripped
   positive control at 13.82 px growing to the corner;
   (b) **produce TPV natively** — **SCAMP 2.10.0**, whose own preference table
   offers **`PROJECTION_TYPE  SAME # SAME, TPV or TAN`** as a documented OUTPUT
   setting (verified by `scamp -d` on the built binary, not inferred from a format
   string), making **SExtractor → SCAMP → SWarp the canonical Astromatic chain**
   and the documented industry answer to this item. **State the PAIR, not SCAMP
   alone: SCAMP solves and writes `.head`; it resamples nothing.**
   **WHY THE SHARED CONTEXT CHANGES THE REACHABLE ORDER** (moved from
   `native-solve-and-sip`, its one home now): per-frame ~37 Tycho-2 matches
   support order 1 by the Pan-STARRS occupancy yardstick (`TOOLS.md`), but
   `STABILITY_TYPE INSTRUMENT` fits ONE distortion polynomial per astrometric
   instrument from ALL exposures — pooled across ~13 members that is ~480
   against the table's 300-for-order-4, and SCAMP's default `DISTORT_DEGREES`
   is 3 (needs 128). The condition is OCCUPANCY, not count: pooling helps only
   if the pooled coverage fills the (order+1)² grid — members 4.28° apart with
   ~1000 px of drift make it favourable, and it is checkable before any arm.
   The standards doc already named the architecture (§H.3(3): a high-order term
   shared across a stability context plus low-order per-exposure, *"the shared
   variant does not appear to have been tried"*) — SCAMP's default IS it.
   **THREE SCAMP DEFAULTS TO SET BEFORE ANY ARM, from the same table:**
   `ASTREF_CATALOG` defaults to **`2MASS`, which is REMOTE** — set `FILE` against a
   local catalogue or the first attempt reaches a network service, the same class
   of surprise as `conesearch`; `MOSAIC_TYPE UNCHANGED` has `SAME_CRVAL` and
   `SHARE_PROJAXIS` available and bears directly on members 4.28° apart; and
   `ASTRINSTRU_KEY` defaults to `FILTER,QRUNID`, which is what defines the
   stability context below.
   **AND SCAMP IS NOT ACTUALLY USABLE HEADLESS UNTIL ONE DEFAULT IS CHANGED, so it
   should not be counted as installed-and-ready:** `ASTREF_CATALOG` defaults to
   **`2MASS`, which is REMOTE**. Until `FILE` is set against a local catalogue the
   first run reaches a network service — the same class as `conesearch` being
   GUI-only headless, and avoidable by naming it now rather than discovering it
   mid-run.
   **BEFORE ANY ARM: SWarp's defaults are wrong for this data and silent about it.**
   `SUBTRACT_BACK=Y` would eat a frame-filling star field; `FSCALASTRO_TYPE FIXED`
   does not track per-pixel solid angle where our ~30° gnomonic field varies ~10%
   radially (`VARIABLE` does); `RESAMPLING_TYPE LANCZOS3` exposes **no clamping
   parameter at all**, a different trade from Siril's measured 6.26% clamp rather
   than a better one; `COMBINE_TYPE MEDIAN` is not the plain mean the compose
   doctrine specifies. And the lineage argued from is historical — DES uses SWarp
   on a previous-decade design, while Rubin/LSST moved to an in-house
   warp-then-assemble and Roman uses IMCOM, every successor carrying a PSF model
   through the step.
2. **Interleaved rather than consecutive groups** — one knob, cheap, collapses the
   within-set pointing spread to ~0. Trades the swept-field mosaic for consistency
   (co-pointed members compose to one member's area) and changes the dwell-floor and
   transient-rejection denominators, so it is a real trade, not a free win.
3. **A corner-true shared model** — reduces the residual the homography must absorb.
   No fit here constrains past ρ 1.47–1.51 against a corner at 1.80. The per-set trap
   is registered; a candidate is judged at the COMBINE, never per-set.
4. **Compose-input edge shrink / min framing** — ships less sky rather than fixing the
   cause. Last resort, and it must be called what it is. The MEMBER-side variant
   (per-member edge trim) was an owner-DIRECTED TEST (2026-08-22) that RAN (6d9e568)
   and is REFUTED: NULL on shared sky, canvas −8.7%, and at a framing=max union's rim
   it starves contributor diversity (`docs/dead-ends/stacking-compose.md`, the retired
   `--crop-lr` rule; the `pending-owner` ruling carries the outcome). No BLANKET trim
   ships. What DID ship is not a trim of that kind: a per-member THRESHOLD crop of
   the columns a member's own profile measures as asymmetrically degraded (`cropT`,
   owner-approved 2026-08-29) — selection by measured quality, full depth kept
   elsewhere, no seam at 27 boundaries (`docs/corner-smear-member-selection.md` §3).
5. **Which single model** — the pinned july14 fit is the default on history and
   provenance; a fresh per-set fit is a legitimate CANDIDATE. Settled at the
   COMBINE, one knob, never on a per-set product (a compose artifact
   masquerades as optics there — the registry's per-set-model entries).
6. **A state-CHANGE detector** — a genuine mid-campaign refocus needs a new
   model; the trigger reads from the member-separation MEASUREMENT and must be
   RELATIVE (members cluster and one or two break away at 2.5–3× the cluster's
   own scatter in five sets, ~15× in the sixth) — a shape that survives an
   instrument change where a constant does not. No threshold is invented until
   the quantity is attributed (`docs/combine-contract.md` §5).

**What the defect IS, measured.** The softness tracks SENSOR POSITION, not time
(R² 0.90 against sensor x, **0.05 against elapsed time**) — and, corrected by the
later member attribution, it is the members' ENTRY side that carries the union's
band (`docs/corner-smear-member-selection.md` §2). **The −3.87 px/frame figure
once quoted here is REFUTED by this repo's own later measurement — the drift is
1.9064 px/frame against 1.9581 predicted (2.6%), so 3.87 was out by 2.03× and
exceeded the physical ceiling** (`docs/dead-ends.md`). **THE STANDARDS DOC'S H.4
"ARITHMETIC DISAGREEMENT" IS CLOSED BY THIS AGAINST THE REPO, NOT IN ITS FAVOUR —
the previous wording said the latter and mis-credited the exchange.** H.4 stated
that −3.87 px/frame *"exceeds physics"* and predicted **1.98 px/frame** at this
target; the repo's own later measurement returned **1.9064 measured / 1.9581
predicted**. **The external review was right, this repo's number was wrong by
2.03×, and the doc's prediction matched the eventual measurement to ~4%.** Recorded
in this direction deliberately: a record that reads as though the repo won an
exchange it lost systematically under-weights outside review, in a project that
staffs a seat to provide it. At matched distance from the sensor centre that
side reads **2.86 px / roundness 0.821** against the other's **2.59 / 0.853**.
Acquisition is clean (identical exposure/ISO/aperture/focal across 500 frames, 3.00 s
interval, no gap) and refraction is ruled out (72–77° altitude, differential
refraction across the field changes 0.09 px over the run, in the wrong direction).

**Two hypotheses — SEPARATED (ledger `drift_span_discriminator_exit_edge`, lines
98–99):** (1) an uncorrected asymmetric term fixed in sensor coordinates — lensfun's
`ptlens` is purely radial and has no tangential terms, so it cannot remove a
left-right asymmetry by construction; (2) a registration failure at the exit edge.
The discriminator this item named RAN: three nested arms of aug06/set-01 with
26.1 / 104.3 / 235.7 px of stacked drift span, blur at matched sensor x — FLAT on
the exit side across 9× (ΔFWHM(L−S) −0.025..+0.055 px, roundness within 0.018), so
(2) is REFUTED and (1) stands, further attributed to the photons of single raws with
a night ordering (aug14 raws 2.94–3.03 px / 0.53 at along+2400 against july31's
2.18 / 0.80). No compose change removes it; member selection does
(`docs/corner-smear-member-selection.md`).

**UNBLOCKED — the standards research is done** (`docs/untracked-widefield-standards.md`,
fresh-eyes session, 45 cited sources). What it settles:
- **No astronomical standard fits a radial model.** SIP, TPV and TNX are all general
  bivariate polynomials; PixInsight uses thin-plate splines; HST needs a residual
  LOOKUP TABLE on top of its polynomial. A radial-only profile is nobody's answer.
- **The tool question is answered, and both lensfun routes are now measured, not
  guessed** (`docs/dead-ends.md`): `acm` (the only lensfun model with Brown's
  tangential k4,k5) is ABSENT from 0.3.4 and appears only in v0.3.95; `<center>`
  DOES exist and work in 0.3.4, and installing it without refitting a,b,c about it
  is a LOSS at every sign (2.589 → 4.235–7.610 px).
- **THE DECENTRING READING IS RETRACTED — it was the wrong nuisance transform.**
  The joint refit has been RUN (`scripts/qa/fit_ptlens_joint.py`, 970
  catalogue-matched pairs, 6 frames, 2 nights, 6 pointings) and the answer is
  that the centre belongs at zero: (−6, +14) px, with Brown's tangential pair
  contributing a 2.89 px peak and buying 0.05 px of median. A **centred** ptlens
  model describes this lens to a **0.27 px median**. The earlier 8.35/6.71/8.54 px
  "irreducible" residual and the ~180–240 px centre were the unabsorbed
  projective term of an AFFINE nuisance where the geometry requires a HOMOGRAPHY
  (two TAN projections of the same sky differ by a homography exactly). Same
  data, one knob: affine 14.24 px RMS / 7.63 median against homography 3.19 /
  **0.27**. `docs/dead-ends.md` carries the trap.

**What this leaves the item — now MEASURED, not inferred.** The GEOMETRY is not the
open term (a centred radial model fits it to a 0.27 px median), and the star-shape
gradient has since been characterised directly on single raw frames (Siril
`findstar`, 3 frames x 6 sets x 2 nights, 136k stars, roundness floor dropped to
0.05 because the default 0.50 truncates the tail under study):
- **It is REAL, not a detection artefact** — it survives inside amplitude quartiles
  in 6/6 sets, though median star brightness varies 2–10x across x.
- **It is ANISOTROPIC, not defocus** — the MINOR axis is symmetric left-vs-right
  (2.08 vs 2.00 px) while the MAJOR axis is not (2.46 vs 2.63). Sensor tilt as a
  tilted focal plane would inflate both.
- **It is RADIAL, not residual motion** — the major-axis angle tracks the field
  azimuth in 7 of 8 zones in every set (resultant 0.45–0.85 at the edges), where
  in-exposure trailing would hold one fixed sensor direction.
So it is a field aberration of the coma family with an asymmetric amplitude — in
the optics. No distortion model and no re-registration removes it. The candidate a,b,c from this fit
(a=0.005185 b=0.010655 c=0.004969) differ from the shipped model and are the
first ones with CORNER support (catalogue pairs reach ρ ≈ 1.8; cpfind stops at
ρ ≈ 1.0–1.5) — a CANDIDATE, judged at the COMBINE on star_stations + seqtilt and
the owner's eyes, never on its own residual.

**Closes when** a route ships that holds the exit-edge sensor region at the clean
side's star shape on the owner's eyes.

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
| shake / wind gust | per-frame FWHM + roundness spike; elongation angle off the trail axis | **THE ANGLE TEST NOW EXISTS AND IT FIRES** — `datasets/aug06/corner_work/drift_bearing.json`, commit `ae107a8`. The first block of aug06/set-01 reads θ₀ **19.75° away** from the rest of the set while its own drift bearing departs by only **0.150°** against a 0.062° SE — so the SKY was doing the normal thing to a fifth of a degree and only the star SHAPES were not. That localises it IN THE EXPOSURE (vibration or settling on the first frames after setup), not in the tracking or the sky. It reproduces across detection depth (−36.4° at σ 1.00 vs −29.8° at σ 0.50, same frame) and on the other night (july31/set-01 frame 1, −19.5°). **Fires on 2 of 21 frames, both the first exposure of a night** — which is a positive control this item required and did not have. Still needed for adoption: a per-FRAME form (this is per-block) and a decision on whether one frame is worth culling |
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
  owner-DIRECTED TEST (2026-08-22) that RAN (6d9e568) and is REFUTED — no trim
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
  mild ~5%/side bracket was the DIRECTED TEST that RAN (6d9e568) and failed — it
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
   The arms exist and are preserved: `sessions/aug09/work/flatdiff/arm_{A,B}.fit`
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
  measured on roundness-0.615 frames; july23 measures 0.80. If Siril's own blind
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

## `one-sided-band` — the fix-path gate is ANSWERED; what is left is one unattributed term

Stars in the far corners of combined products are less round and slightly larger.
The defect is REAL, visible to the owner on the full-frame render, and confirmed on
single unregistered RAWs by two independent tools. **Nothing the pipeline does
causes it** — coverage depth, the compose, within-member registration and any
lensfun distortion residual are each eliminated by measurement, and Siril
`findstar` on THREE SINGLE RAWS (debayered, uncalibrated, unwarped, unregistered,
unstacked, 8074 stars) carries the term at full size. An uncorrected frame cannot
carry the RESIDUAL of a correction that has not been applied. CONFIRMED again on 18
single raws across 6 sets with an explicit NIGHT ordering (aug14 softest), and the
UNION band's carrier — the members' own entry-side columns — is attributed and
answered by member selection (`docs/corner-smear-member-selection.md`); the raw-frame
RADIAL term below stays the open question of this item.

**PRODUCTS UNDERSTATE IT.** An isotropic blur added everywhere compresses a ratio
toward 1, so the raws' corner defect is **+28.7% against the delivered +23.6%**
(`datasets/aug06/experiments.jsonl` → `resample_cost_arm_d_COMPLETE`, the LAST
entry of that id; `datasets/README.md` carries why that qualifier is load-bearing
and how to read this ledger for a homing check). Single-RAW measurements are
unaffected — which is most of this item's evidence — but any product-vs-member
or product-vs-raw comparison inherits it.

### The pinned prediction

Inner three bins only (complete azimuth, condition 1.09–1.10): trail ratio
**0.3502 ± 0.0080**, `t_eff/t_nom` = 0.5918, predicted ZP deficit **0.570 ± 0.012
(stat) ± 0.013 (axis choice)**. The ZP that would test it is measured 33× better
than the quantity it must be differenced against and still cannot settle it —
the degeneracy is structural, not a precision limit (`TOOLS.md`).

### The decentring reading, and READ THE QUANTITY BESIDE IT

**The field is DECENTRED** — free centre beats centred at F 169–999, offsets
443–531 px — but **no optical centre is quoted**, deliberately: three populations
disagree by ~300 px in x while quoting 10–31 px formal errors, mutually
inconsistent by 10–20 of their own sigmas. That inconsistency IS the result; one
decentred radial field plus a constant does not describe this field. The
phantom-decentring entry in `docs/dead-ends.md` is why the restraint is mandatory.

**THIS DOES NOT CONTRADICT `compose-homography-smear`, AND THE APPARENT CONFLICT IS
A COMMENSURABILITY CASE.** That item records the decentring reading as RETRACTED
with the centre at zero, (−6, +14) px. **The two fit different quantities:**
`fit_ptlens_joint.py` fits a decentred POSITIONAL / DISTORTION field against
catalogue pairs; `pa_convention.py` fits a decentred radial ELLIPTICITY field. **A
distortion centre at zero does not refute an ellipticity-field centre at 443–531
px.** Neither record said which it meant.

### The candidate list, with discriminators — DOCTRINE, and NONE of it is measured on this corpus

**Source throughout: Jarvis, Schechter & Jain 2008 (arXiv:0810.0027). Every row is
DOCTRINE or MECHANISM from external literature. Nothing here is a claim about this
data**, and no row may be promoted to one by being quoted.

| candidate | signature | discriminator |
|---|---|---|
| **Decentred / misaligned optic** (§III.2) | astigmatism *"grows linearly with distance from the center of the field"* with the centre DISPLACED; ellipticity ∝ astigmatism × defocus, so odd in shape while size stays even | spin-2 fit per ρ-bin with a **FREE CENTRE** — a displaced centre is the signature |
| **Off-axis coma** (§III.1) | *"a vector field, directed outward from the axis"* — radial, centred, linear growth | the same fit: a one-sided term is NOT coma unless the axis is displaced, which is the row above |
| **Defocus / focal-plane tilt** (§II.1, §III.3) | *"defocus which varies linearly"* → a one-sided SIZE gradient | **ON THE LIST — an earlier elimination is RETRACTED.** It rested on the size profile being symmetric; this item records the odd left−right term at **+0.180 px**, so the convolved-blur family is live |
| **Atmospheric dispersion** | elongation along the ELEVATION vector (horizon frame), CHROMATIC, ∝ tan(z) | **per-Bayer-channel ellipticity — the cheapest test available here**, and the only discriminator in this table that keys on colour. Cross-session direction test inherits the altitude bound below |
| **Tracking / mount error** | fixed direction, FIELD-CONSTANT | the spin-2 fit already separates field-constant from radial; a gradient is not this |
| **Gravity / flexure** (§V.2) | correlates with *"the direction of gravity, namely the declination and zenith distance"* | cross-session at differing altitude — inherits the altitude bound, and does NOT separate from atmospheric without the chromatic test |
| **Registration / resampling residual** | smears along the residual direction, grows with distance from where the transform was CONSTRAINED, and moves size AND shape together | **REFUTED as the union band's carrier** — the 9× drift-span discriminator read the exit-side blur flat (ledger 98–99); the signature stands as a signature. Its separators as written: **reference swap, read BINARY** (BACKLOG:`single-pass-reference-lottery`): must move if registration, cannot move if sensor-fixed. Second separator: the **three-level ladder**, immune because level 1 uses no reference |

**TWO THINGS ARE NOT CANDIDATES AND MUST NOT BE LISTED AS SUCH.** The coadd
PSF-orientation mixing is DEMOTED — see the section below. And the **clamp acting
across a trail is a COMPONENT TO SEPARATE OUT, not a candidate**: it is
field-constant where it aligns with the trail axis, and a field-constant term
cannot produce a one-sided radial gradient. Naming it explicitly is what lets the
spin-2 fit absorb it instead of leaving it to contaminate a radial term.

**WITHDRAWN with the list:** the narrowed question *"what adds an odd ellipticity
term without an odd size term"*. The sizes are not equal, so the question presumed
a symmetry the data does not have.

**THE BAYER DISCRIMINATOR IS STATED IN THE TREE'S STRONGER FORM, NOT THE SOURCE'S.**
The weaker warning is that the greens are channels 0 and 3, so a channel-order
error compares RED against BLUE. `TOOLS.md` establishes something harder: **the
order cannot be read off `BAYERPAT` at all** — *"IDENTIFY THE GREENS"* — because
raster order and `ROWORDER` both enter and `ROWORDER` varies by product class
(`convert` and `split_cfa` outputs against stacks, with one fixture carrying none).
Identify the greens FROM THE DATA; "remember ch0/ch3" is not a usable instruction.

**THE ALTITUDE BOUND, AND IT BINDS TWO ROWS.** `docs/dead-ends.md` records the whole
corpus at **altitude 63.4–87.7°, |HA| ≤ 2.35 h — the flat end of the refraction
curve**. So both hour-angle senses being present does NOT make the lever large, and
how much sense-reversal signal survives at these zenith distances is UNQUANTIFIED.
That bound applies to the **atmospheric** row and to the **gravity/flexure** row,
since both are cross-session at differing altitude.

**THE ASTIGMATISM × DEFOCUS ROW IS A GOOD FALSIFIER AND A WEAK CONFIRMER — read
the direction before scheduling it.** The source is unambiguous that *"a combination
of astigmatism and defocus is needed to produce elliptical images"* and that the
second-moment difference is proportional to their PRODUCT, so astigmatism alone
gives a circular PSF. Three qualifications travel with it, and a summary of this row
lost all three in one hop:
1. **"At best focus" is not zero defocus ACROSS A FIELD.** Field curvature makes the
   focal surface curved, so the edges carry defocus at nominal best focus. The
   product is generally non-zero off-axis; the vanishing is on-axis only.
2. **The lever's SIZE is unmeasured.** Per-session refocus moves the defocus term by
   an unknown amount. If refocus repeats to a small fraction of the depth of focus,
   the between-session variation may be invisible.
3. **The between-session comparison is CONFOUNDED** — temperature, optical state and
   sky all change too, and this repo's own flat work already records per-session
   focus recalibration as *"a live alternative explanation for a per-session-constant
   term"*, pointing the other way.
**THE FALSIFIER, and it is asymmetric:** if the asymmetry amplitude is CONSTANT
across sessions — one lens, one focal length, focus recalibrated between them — then
the astigmatism × defocus product is NOT driving it, because the defocus term should
have moved and the effect did not. **That is a clean kill.** If it VARIES, that is
consistent with the mechanism and does NOT confirm it, by qualification 3. Schedule
it for the kill, not for the confirmation. **It needs no new acquisition** — between-
session variation on one lens at one focal length is already-collected data, and
per-session focus recalibration is already standing practice.

### A candidate that is DEMOTED, and it must not be listed beside the term it is a corollary of

**The coadd-orientation candidate — the idea that how members are oriented in the
coadd could be a SOURCE of the one-sided term — is demoted. It has no source term.**
It is a COROLLARY of the single-frame optical term reaching the coadd, not an
independent mechanism, so listing it alongside the real candidates in the "Open"
list below would double-count one physical cause and invite an experiment that
cannot come back negative. The single-RAW evidence at the head of this item is what
settles it: the term is present at full size on frames that have no coadd, no
registration and no orientation choice.

**NAMED DESCRIPTIVELY ON PURPOSE, AND NO NEW TERM IS COINED FOR IT.** The thing
being demoted is *the mechanism by which the single-frame optical term reaches the
coadd*; the entire content of the demotion is that it is NOT a candidate, and a
named thing reads as a thing to go and study. **`TRANSFER FUNCTION` is also
TAKEN** and must not be reused here: it occurs in two files (`BACKLOG.md`,
`docs/dead-ends.md`) and both are the flat-differential result, where it means
the flat-shape-to-object-tilt conversion measured at essentially 1:1.

### Open

1. **The unattributed RADIAL term.** 18% is attributed to the gnomonic plate scale
   (measured, parameter-free, a subtraction rather than a knob); the remainder
   survives at 5.9 SE. Family unresolved — coma consistent, astigmatism not reached,
   and the radial↔tangential sign flip that would establish astigmatism is ABSENT.
2. **A few-degree axis offset between the CFA and debayered grids**, pre-registered
   as AMBIGUOUS between the demosaic and severe undersampling (S 0.83 → 0.415) and
   deliberately unattributed. It bounds rather than explains: whatever it is moves
   the axis a few degrees and neither creates nor destroys the rotation. Separating
   them needs a mosaic-planting arm requiring a synthetic colour distribution
   against a real reddened field — judged not worth it; disagree only with a design.
   **THIS IS AN ABANDONMENT THAT ITS OWN DESIGN PRE-AUTHORISED, AND THE DISTINCTION
   IS WORTH MORE THAN THE ITEM.** `21653a1` declared, BEFORE the run and before
   anyone knew which way it would go: *"DIFFERENT_means: AMBIGUOUS between the
   demosaic and severe undersampling. **This arm cannot separate them and will not
   attribute.**"* It came out DIFFERENT (χ² 27.060 and 23.272 at 3 dof, offsets
   2.2–9.7°) and was reported as non-attributing, exactly as pre-declared. **So the
   refusal to attribute is a RESULT, not a stall — nothing dangles, and re-opening
   it needs a new design rather than more of the same data.**
   **CONTRAST IT WITH THE COMPOSE CASE IN `compose-homography-smear`**, where a
   conclusion was reversed with no record of the reversal and a shipped route was
   retired by a doc reading. **Pre-declared non-attribution and undocumented
   reversal both leave a question open; only one of them leaves a reader able to
   tell which.** That is the difference between "settled", "abandoned" and
   "unreproducible by construction", and this cluster now carries a worked example
   of each.

**THE MECHANISMS THIS THREAD PRODUCED NOW LIVE IN `docs/dead-ends.md`**, because
they generalise past it: the stack-side non-stellar tails that govern any
stack-side statistic; the incomplete-azimuth leak and its ⟨cos 2φ⟩ geometry; the
per-bin error-model rule (*a per-bin property estimated from N frames has N
independent realisations*); the plate-scale trap; the refraction-as-shape closure;
and the magnitude-vs-projection commensurability case. Numbers and provenance for
everything above are in the tracked records under
`datasets/aug06/corner_work/`, which carry them directly.

**Closes when** the residual radial term is attributed, or a route ships that holds
the corner at the clean band's star shape on the owner's eyes.

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

## `corner-fix-landscape` — the FIX-classified route is DEAD; what is left is procurement or acceptance

**The classification rule, adopted after a list of four "responses" turned out to
contain three non-fixes: every candidate is FIX / TRADE / BANDAID before it is
listed, and a trade or a concealment never appears in the same list as a fix.** If
the honest answer is "no fix is available on this rig", that is the finding — and
on today's evidence it very nearly is.

**THE ONE FIX-CLASSIFIED ROUTE ON THIS RIG IS DEAD BY MEASUREMENT.** Single-PSF
deconvolution of a field-constant component (`rl -loadpsf=`, scriptable and
verified installed) required a genuinely FIELD-CONSTANT term. Asked directly — is
there a single trail scale `f` making `C(ρ) − f·T(ρ)` a constant 2-vector — the
answer is NO on **three independent grids**: debayered N=5, debayered N=40, and a
raw CFA grid with no interpolation anywhere. **A single global PSF cannot remove
this component.** Numbers, the N=40 table and the not-a-class test are in
`datasets/aug06/corner_work/frame_depth.json`; the complete-azimuth check is in
that directory's `shape_azimuth_m01s{1,2}.json`. Not restated here.

### The remaining candidates, each with its verdict

- **NOT PROCURED — anisotropic spatially-varying deconvolution.** The only class of
  treatment that would RECOVER corner detail. Farrens et al. 2017 (A&A 601 A66) is
  built for a known spatially varying PSF, i.e. what PSFEx produces, but its
  backend is a source integration; StarTools SVDecon is GPU+GUI; BXT is
  PixInsight-hosted and uninstalled by choice. **"There is no packaged headless CPU
  Linux tool for the anisotropic half" is now FALSE AS WRITTEN** (last checked
  2026-08-14): **`torchmfbd` 0.9.2** (pip, A&A 2025 703 A269) states it handles
  spatially variant PSFs. **The SENTENCE is refuted; the SUBSTANCE may hold, and
  three checks decide it — any one voids it:** does it do NON-BLIND deconvolution
  with a supplied PSF field (unstated in its README); **MOMFBD's premise is
  frame-to-frame aberration DIVERSITY while ours is STATIC and identical in every
  frame**, so blind mode would have nothing to exploit; and PyTorch CPU-only at
  6064×4040 on a no-GPU rig, with `torch` + `triton` costing 37 packages.
  **Procurement-and-integration boundary, not a physics ceiling.**
- **IMCOM / `pyimcom` 1.2.1 — WEEKS AND A FORK, not days and an adapter** (its own
  `docs/config_README.rst`, 2026-08-14). It is the principled generalisation of
  both drizzle and homogenisation — a user-specified output PSF from undersampled
  dithered exposures with varying input PSFs, and **nothing requires the target PSF
  to be broader**. But mandatory `OBSFILE` is a survey OBSERVATION-TABLE schema,
  supported inputs are a small named set, and there is **no plugin system and no
  bring-your-own-data path** — formats are added by maintainers in-tree. **The one
  probe that could still make it cheap, unsettled:** `furry-parakeet` holds the
  linear-algebra kernels separately from the Roman driver.
- **~~Cosmic Clarity~~ WITHDRAWN — not a headless candidate** (`TOOLS.md`, the
  one home, measured: attended-only, CLI ignored, non-stellar pass crashes;
  three sessions believed its `--help`). Surviving mechanism note: model space
  `radius_{1,2,4,8}` — spatially varying but ISOTROPIC, size only, never
  ellipticity.
- **NOT THE ROUTE — `sf_deconvolve`**: it deconvolves a stack of postage stamps,
  one PSF per object, not a field. It restores objects, not images.
- **CLOSED ON DOCTRINE, not capability — tiled deconvolution.** Siril has every
  pixel operation for the classical overlap-add answer, but the tiler and blender
  would be in-house code READING AND REWRITING the deliverable's pixels. FORBIDDEN
  by the bright line. Do not propose it.
- **TOOL FACT, and it is now INSTALLED:** `galsim.des.DES_PSFEx` reads a PSFEx
  `.psf` directly and evaluates the PSF at an arbitrary position, so the
  `[1, X, X², Y, XY, Y²]` basis-order trap `TOOLS.md` documents cannot arise.
- **TRADE — `-noclamp`.** The clamp costs 6.26% of PSF width per pass against a
  0.45% kernel, **at the frame centre where there is no aberration gradient at
  all**. By this repo's own contract the clamp is itself a bandaid — ringing is a
  symptom of UNDERSAMPLING — but removing it trades an artefact for sharpness
  rather than fixing anything, and nobody has measured the ringing it prevents on
  THIS data. Owner's call, not a free win.
  **AND THAT IS A TRADE WITH ONE NUMBER ON IT — CONFIRMED, not just restated.** The
  COST replays exactly from `datasets/aug06/experiments.jsonl`
  (`resample_cost_arm_d_siril_pass`): lanczos4 **unclamped 0.45%**, **clamped
  6.26%**, with the nearest-neighbour control at **0.00%** validating the
  instrument. The BENEFIT has no number anywhere — a tree-wide search for a ringing
  measurement over `datasets/` returns none, and the record itself says only
  *"reintroduces whatever artefact the clamp was added for."*
  The both-sides-indeterminate framing of the owner's choice (a
  single-configuration gain against an unquantified loss) is homed in
  BACKLOG:`resample-cost-and-drizzle` and not restated here. **The fixture
  that would close it already exists and needs no new design:** the same planted
  synthetic frames pushed through the shipped `register -2pass` →
  `seqapplyreg -interp=` operation verbatim, with a sharp-edge target added and the
  overshoot measured clamped vs unclamped. Cheap, and it converts an owner decision
  from one number to two.
- **BANDAID / accepted failure mode, NOT candidates:** PSF homogenisation, zone
  down-weighting — owner-REFUSED, with Zackay & Ofek 2017 making homogenisation a
  measured information loss (`docs/dead-ends.md`). **Cropping LEFT this category
  (owner 2026-08-22) as a DIRECTED TEST; the test RAN (6d9e568) and REFUTED it** —
  NULL on shared sky, −8.7% canvas, a starved rim at the cross-night union (root
  cause: contributor diversity, not member damage) — so it is not a candidate either:
  a measured dead end, registered (`docs/dead-ends/stacking-compose.md`, the retired
  `--crop-lr` rule; the `pending-owner` ruling carries the outcome). No BLANKET trim
  ships. The per-member THRESHOLD crop that later shipped (`cropT`, owner-approved
  2026-08-29) is a different thing from that symmetric trim: it removes only the
  columns a member's own profile measures as asymmetrically degraded, keeps full
  depth elsewhere, and is a FIX-class SELECTION by measured quality, not a bandaid
  (`docs/corner-smear-member-selection.md` §3).

**Closes when** an anisotropic treatment is procured and measured, or the owner
accepts the corner as-is. **The in-chain question is settled only for RECOVERY: no
route on this rig recovers corner detail from a frame, and the defect is in the
photons of single unprocessed RAWs.** Member SELECTION is the third route this item
did not name: it removes the degrading portions before the mean and moved the union's
band 2.97 → 2.79 px (`cropT`); what it cannot remove is the lens's SYMMETRIC radial
softening, which every frame carries — the procurement / acceptance decision above
applies to THAT. `compose-homography-smear` no longer names a chain-caused defect
(its smear is attributed to the members).

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
frames — reported, not gated (`docs/corner-smear-member-selection.md`). Unbuilt:
the per-FRAME cross-session quality surface (per-set `frame_metrics.json` exists;
nothing ranks or thresholds across sessions; `cullspec` excludes are per-set), and
the encoding of the member-tier rules as a chain stage. Selection is adopted only
through a measured arm with a pre-registered prediction, never as a default.
**Closes when** a final-pass product ships from measured THRESHOLD selection across
at least two sessions' data with its per-set selection recorded.

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

**SEPARATE from the record-vs-reality defect** (fixed at `e4f4a6a`; the mechanism
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
defined anywhere — the sentence entered at `e4f4a6a` already dangling; one
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
`web/results/july26/`; every mechanism in `docs/dead-ends.md`.

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

## `cross-set-record-home` — a multi-set product has nowhere to write

`finish_render.sh` hard-requires `--set` (it exits with "--session= and --set= are
required"), so the 1760-frame four-set combine's SPCC record landed under set-03 —
a session-level product filed as a per-set one. `datasets/README.md` already
reserves session-level records for exactly this case (`../render_<tag>.json`
beside `experiments.jsonl`) and the finish stage cannot write one. **Closes when**
a cross-set product writes a session-level record without borrowing a member set's
directory.

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

## `site-privacy-vs-public-repo` — the observing site is a home address, and this repo is meant to be published

**THE REPO IS INTENDED TO BE PUBLIC, so this blocks publication rather than being a
reason not to publish.** `github.com/mufon609/astro-imaging`; measured PUBLIC by one
instrument (unauthenticated GitHub API GET, HTTP 200 — single-source, not
independently confirmed). **The observing site is a home address at 11 cm precision
and it sits in 20 tracked files.**

**The exposure is LOCAL ONLY and this is the cheapest it will ever be.** `git grep -lF`
on the latitude returns **19 at HEAD and 0 on `origin/main`**; the coordinates entered
at `f49b7cc` and `ebf8209` against a last-pushed `048e69d`, i.e. after it. A history
rewrite today touches local objects only; after a push, forks and API caches make it
permanent.

**WHY IT IS NOT A ONE-FILE PROBLEM — five constraints, each closing a naive fix:**

1. **Tracking it is REQUIRED by the contract.** `CLAUDE.md` Environment: a
   machine-local value nobody can rebuild has already cost this repo a shipped optical
   model. `scripts/setup/site.json` exists *because* of that rule, so the file is not
   the defect.
2. **It is load-bearing science, not metadata.** The site resolves into hour angle,
   altitude, azimuth and parallactic angle; the refraction-vs-mechanical-sag
   discriminator (`docs/dead-ends.md`, optical-state boundary) is unrunnable without
   it, and that entry records this record as what removed the blocker.
3. **IT REGENERATES.** `acquisition.resolve()` writes the `site` block into every
   `acquisition.json` on every chain run, so a one-time scrub is undone by the next
   run. 16 of the 20 files are those records.
4. **THE GEOCENTRIC FORM INVERTS.** The block carries `OBSGEO_XYZ_m`
   `[REDACTED_OBSGEO_X, REDACTED_OBSGEO_Y, REDACTED_OBSGEO_Z]` beside the degrees, and Cartesian
   geocentric returns lat/long to the metre — so removing `SITELAT`/`SITELONG` alone
   leaves the position fully recoverable.
5. **THE SITE CANNOT BE LOCATED BY STRING SEARCH IN THIS TREE, and a grep-driven
   scrub is therefore unsafe in BOTH directions.** The exact six-decimal literal
   returns 19 files and **MISSES a real site**: `scripts/setup/verify_site.py:22`
   carries `REDACTED_SITELAT` in a prose comment — full precision, differing in the last
   digit only, **0.11 m from the true value**. Widening to a 3-decimal prefix returns
   **31 files, of which 11 are collisions** (`40.078924`, `1240.078926`, `240.078202`
   in Siril star lists). True surface: **20 files**. Any sweep must be structural —
   JSON keys plus a read of the code — and must ship a positive control proving it
   finds `verify_site.py`.

**THREE APPROACHES ARE DENIED (owner ruling 2026-08-16). Do not re-propose them:**
- **Make the repo private** — denied on the project's own terms: a workspace that can
  never be published defeats the point of building it in the open.
- **Round the coordinate** — 3 decimals is ~111 m and the science is unaffected
  (0.001° moves a derived altitude by 0.001°, against effects measured in whole
  degrees). Denied anyway.
- **Untrack the site** — it is the contract's own named failure mode, constraint 1.

**A fact the solver will want, stated because the record already carries it and not
as an argument for any approach:** `site.json` records `"status": "TRANSCRIBED,
UNVERIFIED"`, `verify_site.py` bounds the value only at the DEGREE level by its own
admission, and the same file names an unrun derivation that would recover latitude
from field rotation across solved frames. The tree therefore publishes 11 cm of
precision that nothing has verified past ~1°.

**Closes when** the repo can be published with the site out of it, without breaking
the rebuildable-from-tracked-files rule and without disabling the hour-angle
derivations. Until then the push is HELD — not because of the commit volume, which
is fine, but because of this.

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
the read-back at the next real compose (header-only A/B: stamp emitted vs
header read back, pixels untouched); and register/guard coverage naming the
tuple's key set. Retrofit of existing products would ride the retired
`backfill_substack_provenance.sh` precedent (recover from git).

**Closes when** the next compose reads back the chosen keys from its product
and the rgbcomp/standard-route stamping decision is made and recorded.

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
(`run_undistort_pipeline.sh:277` — the fix is `frame_order.py`'s capture-order
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
a `docs/dead-ends/siril-behaviors.md` entry. Stages 0–2 SHIPPED: runner 25cfed6,
curves 5cd01e0, recipes 199360c, the 22 re-calibrations 41eecff.

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

**Delta declared (41eecff; `datasets/corpus/spcc_pin_zf/pin_record.json`).** All
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
