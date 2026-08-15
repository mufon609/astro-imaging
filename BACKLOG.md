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
A full read of all 37 rows (6,961 status words) found narrative in **TWO** — both
recounting how a finding was reached, both with the mechanism already homed. The
other 35 are verdicts, measurements and tool names, which is what it COSTS to
record 37 divergences with their evidence. **A long row is not a violating row.**
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
status text is true.** A full sweep of the condition column (all 37 read
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
| optics/calibration FITS stamp (`header_provenance_lines`) + `backfill_substack_provenance.sh` | the warp stops being a TIFF round trip, so the model rides through natively (darktable gains a FITS **WRITER** — it has READ FITS since 5.4.1 (MEASURED: full-resolution export from a 6064x4040 `.fit`), and `.fits` output returns *"unknown extension"*, so the round trip is held open by the write side ALONE. The earlier wording *"gains FITS I/O"* became AMBIGUOUS the moment that was measured: half-satisfied, with the text not saying which half, or Siril `register -disto=` — BACKLOG:`native-solve-and-sip`); the BACKFILL retires once no un-stamped sub-stack remains on any rig | 2026-08-14 | **THIS ROW CARRIES TWO CLAUSES AND THEY HAVE DIFFERENT ANSWERS — read them separately, because reporting only the first is what hid the second.** **(a) THE STAMP — not fired.** The warp is still Siril `savetif32` -> darktable -> Siril `convert`, which carries no FITS header; the reason is now narrower than this row long stated — darktable 5.4.1 READS FITS and cannot WRITE it (measured, `stamp_headers.sh` row below), so it is the WRITE side that keeps the round trip. **(b) THE BACKFILL — FIRED.** Its trigger is *"no un-stamped sub-stack remains on any rig"*, and MEASURED 2026-08-14 across every `sub_*.fit` under `sessions/`: **93 of 93 stamped (`DISTMODL` present), 0 un-stamped** — 78 in the 18 `groups_*` dirs plus 15 `pergroup/arm{A,B,I}` diagnostic-arm sub-stacks. **State the denominator with the number, because two sweeps of "the same thing" disagreed at 78 vs 93** — anchoring the glob to `groups_*/` excludes the pergroup arms; the defensible figure is every `sub_*.fit` under `sessions/`, which is 93. Scope: measurable only on THIS rig, and "any rig" is unbounded — but `CLAUDE.md`'s environment is one rig, so it is met on the only rig that exists. `backfill_substack_provenance.sh` is therefore discharged and should retire on the owner's word. Load-bearing: the lensfun user DB is global, unscoped, single-valued machine state that nothing reverts, so a sub-stack that cannot state its own optics cannot be composed safely later — 13 aug06 members under 3 different models composed into a doubled union and nothing in the product could see it |
| `compose_preflight.py` + the compose's astrometric post-assert (`run_undistort_compose.sh`) | siril itself refuses to register a sequence whose members carry no usable solution, or the chain has no star-pair path left to fall back to | 2026-08-14 | **not fired — and the EVIDENCE this row used to carry is now FALSE, while the verdict stands.** It read *"it fires on today's corpus — the union's own members (`groups_set-0*_pinned/sub_*.fit`) carry NO WCS, so the guard refuses them at exit 3."* MEASURED 2026-08-14: **no `groups_*_pinned/` dir exists on this rig** (the 18 surviving group dirs are `groups_set-0N` plus `_l1arm`/`_l1ctrl`), and the members that DO survive carry WCS — `sessions/aug06/work/groups_set-01/sub_01.fit` reads `CTYPE1 = RA---TAN-SIP`, `CRVAL1 = 304.4330331279676`, so the guard would ACCEPT them. **The premise is inverted, not merely stale: a corpus statement outlived the corpus.** The condition itself is untouched — siril still does not refuse an unsolved sequence — so "not fired" is correct on the tool, not on the members. Grounds: `seqplatesolve` needs every member solved with SIP order >= 2 and siril reports NOTHING when they are not — it registers what it can and exports a finished-looking product. Measured cost of the silent fallback: roundness 0.458 against 0.974 on the 28-member union. Both halves are live-tested — refusal (exit 3) on unsolved members, acceptance plus "astrometric registration + per-member undistortion CONFIRMED" on solved ones, and `--selftest` falsifies the header checks |
| `solve_field.py` hint-contradiction gate (position > 2x the hint radius, scale outside +-20% of the header nominal; exit 9) | the solver itself refuses a solution that contradicts a supplied position/size hint — today the `astrometry` engine takes hints as search guidance only, and the blind fallback discards them entirely, so a hinted attempt that fails is followed by an unconstrained one whose answer nothing compares back | 2026-08-14 | **not fired, and it FIRES on the one measured false solve.** MEASURED: the corpus union's hinted attempt failed on a seam-contaminated framing=max canvas and the blind fallback shipped RA 6.03 Dec -65.10 at 12.96"/px, logodds 22.3 — against the product's own header pointing RA 309.77 Dec +41.70 (siril's WCS field centre, inherited from the already-solved members, so independent of this solve) and a 17"/px family. Nothing downstream could catch it: siril SPCC ran to COMPLETION on that WCS and produced plausible K factors (R 1.000 G 0.592 B 0.817, 1790/5153 stars kept). Thresholds are budgeted from mechanism, not fitted — integer-mm EXIF focal, XPIXSZ rounding, infinity-vs-marked focal and the TAN centre-to-corner ratio (1.066 at 28.6 deg) sum under 10%, doubled to 20%. The refusal's own numbers reproduce exactly (115.4 deg, 0.7405x). SCOPE LIMIT: 53 are per-member sub-stacks whose headers carry FOCALLEN/XPIXSZ but no RA/DEC, so only the scale leg and the logodds warning are live there. **TWO CORRECTIONS FROM A 2026-08-14 RE-VERIFICATION, and the first is the sharper.** (1) **THE REPLAY IS NOT REPRODUCIBLE FROM THE RECORDS FOR THE CASE IT MATTERS ON.** `hint_available` and `header_scale_arcsec_px` — the fields whose own code comment says they exist so *"a later audit replays it from the record instead of re-deriving the nominal from the hint's 0.6x end"* — are ABSENT from the false-solve record. Only **43 of 195** record files carry them, because they shipped WITH the gate, so every pre-gate record lacks them. **The mitigation postdates the case it was built to make auditable**, and the audit had to do exactly the re-derivation the field exists to prevent. (2) **THE COUNT DISAGREES ACROSS THREE SITES AND NONE MATCHES THE CORPUS:** this row said "69 recorded / 68 clean"; `solve_field.py:312` says "68 records replayed"; `:323` and `:330` say "67 real solves". **MEASURED on disk: 195 record files, 145 distinct solves, 35 replayable.** A SHIPPED script disagreeing with the register is the same shape as the SCAMP claim corrected at `1eacee3`; none of the three written figures is reconcilable with the corpus and all three are superseded by the measurement. The scale band holds for 34 of 35 replayable solves (0.9726-0.9759); **the single 1.0344 outlier is not a drifted solve but a CROP product** whose header nominal is 16.488 against everything else's 17.503, so the headroom there is ~5.8x rather than 8x — the denominator is per-product |
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
| lensfun user-DB strip of the fitted lens's `<vignetting>`/`<tca>` (`install_lens_model.sh`) | darktable honours a style's lens `op_params` | 2026-08-11 | **not fired — and no longer re-checked by hand.** `lens_preflight.py --require-profile` now runs `verify_lens_card.py` EVERY set (11.1 s of a 25.5 s preflight on 6064x4040 frames, so unconditional), because the strip is machine-local state `lensfun-update-data` reverts and the two cheaper checks are blind to it: reinstating the focal=70 aperture=4 `<vignetting>` pair by hand left the warp-happened proof and the pinned-coefficient assert both GREEN while the card read a 4219 ADU corner-vs-centre step on a 30000 ADU field (tol 1.0). Fire-tested both ways on aug06/set-01 (refuse -> re-strip -> 0.000 ADU). **NEVER RUN `install_lens_model.sh` WHILE A BUILD IS IN FLIGHT** — it rewrites the GLOBAL lensfun DB, which every live darktable warp is reading, so a QA or verification step that calls it mutates state a four-hour arm build depends on. Installing an IDENTICAL model still risks a torn read, and the DB is the one piece of unversioned machine state on the undistort route (nothing reverts it; `lensfun-update-data` wipes the strip outright). Caught live, no damage: a queued pin-verification was killed on firing and the DB verified after — all 56 XMLs parse, the fitted entry intact, no stale builder lock. Verify a pin from the build's OWN per-group output instead, which tests the model that actually ran rather than re-installing one. That test also found the restore path itself broken — the installer's idempotence test asked only about the distortion line, so it reported "already installed" and exited 0 on a block whose vignetting was back; it now re-strips and says so |
| per-set sky flat (`build_sky_flat.sh`, NOT de-skied) | a matching REAL flat for the set | 2026-08-12 | **not fired** — the flatless route, and it works: july31 sets measure 0.40/0.49/1.03/1.17% corner spread (a scratch rebuild from raws reproduced the experiments-ledger figures to the digit). The flat still converges to `sky x V`, so the object carries the sky's spatial profile — the MECHANISM is REAL and open, and NOT fixed by de-skying the source frames (`--desky` was a 31x regression; `docs/dead-ends.md`). **Its MAGNITUDE is UNMEASURED**: the long-quoted 3.11% / 241 sigma has no tracked record, and the catalogue-free re-measurement is now a registered DEAD END — the linear mode is degenerate under translational drift and the atmosphere is sensor-fixed for a fixed camera, so the pre-registered flat prediction failed 4 of 5 across 12 sets (`datasets/aug09/corpus_object_tilt.json`) |
| `flat_odd_component.py` in-house odd/even decomposition about frame centre + the plane fit, over Siril `fdiv` ratios and `stat` regional medians | a real flat exists for the set — the SAME first disjunct as the `build_sky_flat.sh` row above, so the two retire together — **or** the `sky × V` defect is measured absent on this rig, at which point the odd component is no longer a thing to watch | 2026-08-14 | **ROW ADDED 2026-08-14 by the first MECHANICAL run of rule (1) (`scripts/qa/check_removal_conditions.sh`); the condition was declared at `flat_odd_component.py:55` and had no row, which rule (1) forbids.** **WHY EVERY PRIOR SWEEP MISSED IT, and it is a reusable tell:** the basename DOES occur in this file — once, inside the `flat_differential.py` row's STATUS, naming it as the adopted primary instrument — so a join asking "does the name appear in the table" returns COVERED. **A mention is not a row**; the join must be on the DIVERGENCE column, and the under-reporting direction is the dangerous one because it reads as "everything is covered". Not fired: the flatless route is the mission and the `sky × V` defect is open and uncorrected. Siril does every pixel op and every measurement (`fdiv` at a recorded scalar, never `idiv` — which clips at 1.0 silently; `stat` regional medians); in-house is the odd/even decomposition, the plane fit and the bookkeeping. Reads no deliverable pixel, gates nothing, always exits 0. Load-bearing for `calibration-evidence`, which recorded this instrument as MISSING before it was built, and for the L/R-is-SKY finding (edge dipole sweeping +0.436 → 0 → −0.385 across the corpus, impossible for a sensor-fixed term) |
| `object_tilt.py` cross-match + weighted LS of magnitude against sensor position (+ `object_tilt_control.py`, `object_tilt_null.sh`, `object_tilt_corpus.py`) | an official tool reports a headless POSITION-DEPENDENT photometric solution across overlapping exposures with no external catalogue — SCAMP's photometric mode is the candidate, or a PixInsight equivalent | 2026-08-12 | **not fired — the divergence is UNFILLABLE on this data, so the code survives only as the record of that.** **SCAMP IS INSTALLED** (`~/.local/bin/scamp`, 2.10.0); the long-standing "no apt candidate on this distro" is FALSE and the verdict never rested on it. **The condition still cannot fire, and that is now sourced from the BINARY rather than a source reading:** `scamp -d` exposes no photometric analogue of `DISTORT_DEGREES`, so its photometric solution is one scalar per exposure per instrument (`TOOLS.md` Tier 3b — cross-referenced, not restated). Siril `seqpsf -wcs=` measures one fixed pixel area in every image, m = -2.104 against +3.55/+5.05/+3.63 (`docs/dead-ends.md`). Every pixel op and every flux is Siril's; in-house is the cross-match and the fit. MEASURES and gates nothing, always exits 0. `--selftest` falsifies in process: a planted +0.100 mag is NOT recovered on a pure-translation panel (-0.046 +- 0.0001, lever 0.00 px). `object_tilt_null.sh` runs it on REAL data — interleaved halves, predicted tilt zero, measured **+49.1 +- 5.0% at 11.8 sigma**. |
| `flat_differential.py` subtraction + straight-line fit (+ `flat_differential_arms.sh`, `flat_differential_report.py`) and the two A/B flags on `run_undistort_pipeline.sh` (`--regdata=`, `--nonorm`) | an official tool reports, headless, the position-dependent photometric RATIO FIELD between two ALIGNED exposures — i.e. the subtraction and the fit, not merely two flux lists. `source-extractor` dual-image mode gives the two lists and is installed; it does not close this | 2026-08-12 | **not fired.** Probed: no Siril command compares two images photometrically by position (`fdiv`+`stat` gives the pixel field and IS adopted as the primary instrument, via the shipped `flat_odd_component.py`; `seqpsf -at=` is applicable on an aligned pair, unlike the drifting case, but measures one star per invocation from a selection — the same per-star call as `psf`, with an unvalidated parser). Every pixel op and every flux is Siril's (`split`, `findstar`, `psf` at a forced radius against its own local annulus); in-house is the subtraction of two tool measurements and a weighted straight line. MEASURES and gates nothing. `--selftest` falsifies the mechanism in process on the SAME pure-translation panel that killed the absolute measurement: the absolute fit returns **-0.046 ± 0.0001 with the lever collapsed to 0.00 px** where the differential returns **+0.0999 ± 0.0001 with a 1548 px lever**, and blinding the position axis turns step 1's own acceptance check RED, restoring it turns it GREEN. **The builder flags are NOT cosmetic**: `register -2pass` re-chooses the reference frame from image quality and the CALIBRATION changes that choice (MEASURED, one knob: skyflat_set-05 → reference image 1, canvas 4896x3616; skyflat_set-01 → image 2, canvas 4887x3641), so without `--regdata` an A/B has two knobs and the arms are not pixel-comparable. Default path unchanged by both flags; `--nonorm` stamps STACKNRM/DIAGARM on the product |
| `grid_ramp.py` least-squares plane over Siril `stat` box medians | an official tool reports, headless, the FITTED low-order background ramp of an image as NUMBERS — a slope or plane coefficients, not a subtracted image, not a background-model image, not a star-shape tilt | 2026-08-12 | **not fired.** Probed on this rig rather than reasoned about: siril `bg` returns ONE scalar for the whole image; `subsky`/`seqsubsky` fit a polynomial or RBF and SUBTRACT it, reporting no coefficients; `tilt`/`seqtilt` compute "the FWHM difference between the best and worst corner truncated mean values" — a STAR-SHAPE measure, not a background level (and `seqtilt` IS scriptable, so the GUI-sibling search was run, not assumed); GraXpert 3.0.2 `-bg` writes the background MODEL as an IMAGE; ASTAP CLI-2026.07.16 `-analyse`/`-extract` report HFD, star counts and per-star rows only. Siril measures every box median; in-house is the plane. Fills the instrument gap `docs/dead-ends.md` names — the grid-fitted ramp slope is the registry's CANDIDATE replacement for four-corner spread, which is "not a gradient measure on a structured field" — and it REPORTS ONLY: no thresholds, no verdict, and swapping an acceptance measure stays a user ratification. `--selftest` falsifies the mechanism in process: blinding the position axis drives a planted +0.15 %/1000px to 0.000000 and turns step 1's own acceptance check RED, restoring it turns it GREEN; a uniform card through the whole Siril path reads slope 0/0 (−7e-15) so LEVEL cannot masquerade as GRADIENT; and an ORDERING CONTROL re-measures the two extreme boxes in their own Siril invocations, since the 63–77 medians are parsed from one run in emission order |
| `starlight_preservation.py` per-cell floor vs Gaia catalogue regression on an external lattice | an official tool reports, headless, the AGREEMENT between a star catalogue's predicted diffuse surface brightness and an image's own measured per-region background — the JOINT, not the two halves | 2026-08-12 | **not fired. BASIS NOTE (2026-08-14): the 2026-08-12 date stands deliberately — the 2026-08-14 sweep confirmed only that this instrument's `--selftest` PASSES inside `run_guards.sh`, and did NOT re-probe the tool landscape below.** "Selftest green" and "condition re-probed" are different statuses and collapsing them is how a stale condition survives; the date column tracks the second. Probed on this rig at the date shown, each with the command run rather than the help read: Siril `stat`/`bg`/`bgnoise` measure the image only (`bg` is one scalar for the frame) and `conesearch` returns the catalogue only — and at this field size it is not even usable, 20.6 deg radius at G<=17 against TAPVizieR, killed at 600 s with no output; `jsonmetadata -stats_from_loaded` ignores a selection and stats the whole frame; `source-extractor` 2.28.2 `-CHECKIMAGE_TYPE BACKGROUND` writes a local background MAP (1.7 s on 4907x3598) but compares it to nothing; GraXpert 3.0.2 `-bg` writes a background MODEL image; ASTAP CLI-2026.07.16 `-analyse`/`-extract` report HFD, star counts and per-star rows. Every pixel and every per-cell number is Siril's (`boxselect`+`stat`, PROBED identical to the `crop`+`stat` route to every printed digit in ONE load); the catalogue aggregate is the ESA Gaia archive's own server-side GROUP BY; in-house is the lattice, the WCS projection and the fits. MEASURES and gates nothing — no threshold, no verdict, always exits 0. `--selftest` falsifies the mechanism in process on a planted fixture: 299.14 recovered against 300.00 planted at R2 0.99993, an orthogonal predictor returns R2 0.00017, Siril `subsky 2` collapses the planted relation to 26.9% (RED) and the pristine copy re-reads 299.14 (GREEN); a catalogue control checks the archive's binned sum against its ungrouped total (agree to 1e-6) and the plane/pole flux contrast (6.3x). It caught a real defect on its first run — `boxselect` counts y from the TOP, and the mirrored lattice still recovered 54% of the planted relation at R2 0.30, which is exactly the kind of half-right number a fixture-free instrument would have shipped |
| GraXpert `-correction Division` synthetic flat | a matching real flat exists | 2026-08-05 | **not fired** — not adopted; no pipeline script calls it. Vignetting-only fallback |
| `baseline_guard.py` derived summaries (corner spread, edge dipole) over Siril `stat` | a tool reports a headless PRODUCT-level regression verdict against a stored reference | 2026-08-05 | **not fired** — nothing does. WIRED into `run_set_chain.sh` as the last step: it measures the finished product, and a regression exits **8** (a user decision, like the mount/route stops) without blocking or rewriting anything. Also a web stage for seeding/re-seeding. It is a no-regression RECORD, never a quality gate — a deliberate improvement fails it and the human re-seeds with a note. Blind spot to state when reading a PASS: both measures are STACK corners, which `docs/dead-ends.md` calls self-fulfilling for flat contamination, so it cannot see the open `sky x V` object tilt |
| `snr_regions.py` in-house SNR ratio over Siril `stat`/`bgnoise` | a tool exposes headless REGIONAL SNR | 2026-08-05 | **not fired** — `stat` and `bgnoise` are whole-image/selection; no regional-SNR command in 1.4.4. Every input number is the tool's; only the ratio is in-house. *(Was missing from this register until 2026-08-05.)* |
| `fingerprint.py` derived trail/drift geometry | an official tool reports headless trail/drift geometry with a declared-vs-measured mount cross-check | 2026-08-05 | **not fired. BASIS NOTE (2026-08-14): date held deliberately — the 2026-08-14 sweep confirmed only that `--selftest` PASSES in `run_guards.sh` and did NOT re-probe the tool landscape.** Same distinction as the `starlight_preservation.py` row: selftest-green is not condition-re-probed. No solver here exposes inter-epoch drift rate vs sidereal. The record schema and the STOP-on-CONTRADICT contract stay wherever it lands. *(Was missing from this register until 2026-08-05.)* |
| `inspect_stage.py` + `cull_report.py` robust-z per-frame flagging | a tool ships headless per-frame outlier flagging over its own registration metrics (SubframeSelector-class, scriptable) | 2026-08-05 | **not fired** — siril has `seqstat` (per-frame statistics to a file) and `select`/`unselect`, but no outlier GRADING over its own regdata. Persisting the tool's regdata is not a divergence and stays regardless. *(Was missing from this register until 2026-08-05.)* |
| prebuilt-master ingest (`run_pipeline.sh` `<session>/calib/`) | never — this is a supported INPUT class, not a divergence. **DECLARED NON-DIVERGENCE: it is trivially evaluable (it cannot fire) and is retained as an explicit marker, but it must not be counted as a live divergence — the table's row count overstates them by one** | 2026-08-05 | **CONDITION WRITTEN 2026-08-05, previously absent.** The code calls it "the adaptation for master-only data", which made it look like an unconditioned divergence. It is not one: a corpus that ships masters instead of raw calibration is a data class the repo accepts. What IS a stated limit: such masters carry no exposure/gain/filter headers, so the filename token is the whole identity and the exposure match is unverifiable — printed per run. Raw calibration dirs take precedence |
| 16-bit in four instruments (`coverage_probe.sh`, `run_frame_qa.sh`, `fit_lens_model.sh`, `run_lunar_pipeline.sh`) | the leg stops terminating in an integer/8-bit product | 2026-08-12 | **not fired** — each re-verified: `coverage_probe` switches to `set32bits` before its sum stack, `run_frame_qa` saves no product at all (analysis-only register), `fit_lens_model` terminates in `savetif8` for Hugin, `run_lunar_pipeline` pins it on its convert+seqcrop stage step only. Exemptions are enforced by name in `check_bitdepth.sh`, which reports FOUR |
| `run_undistort_groups.sh` group composition (one extra interpolation pass) | a measured quality cost of the extra pass at established magnitude (the along+1300 ledger resolving AGAINST groups), or the combine unit stops being CROSS-SET — i.e. `BACKLOG:final-best-percent-pass` and the cross-night combine contract are both closed or withdrawn (the previous wording, *"cross-set composition leaving the project's goals"*, named no observable state and was UNEVALUABLE; "the project's goals" occurs twice in the tree and never as something a reader could see having happened). **SELF-GATED on its first disjunct** — the measured cost retires only on `rebuild_repeat_floor_set01`, an experiment THIS project must run | 2026-08-06 | **CONDITION REWRITTEN — the old trigger (free disk ≥ the single-pass peak) fired and was judged the WRONG condition: disk cannot retire groups.** Single-pass deletes the sub-stacks the cross-set combine composes and crops to `-framing=min` (composing per-set finals is a registered dead end), so a big disk buys nothing back; groups is the STANDING route (`force_route`), single-pass operator-only (`--route=single`, printed FORCED). Quality, two consistent accounts: the item-scoped one-knob A/B (60 frames even-stride) is **NULL — the route does not cause the one-sided band** (9/9 stations within 0.05 px majFWHM / 0.014 roundness; the band sits in BOTH arms at 1.27x/1.24x); the full-depth ledger records a small along+1300 improvement UNDER groups (0.12–0.18 px, direction replicates across two sets and two group sizes) whose proposed baseline mechanism was FALSIFIED (g250 landed outside the interval) and whose magnitude is UNESTABLISHED until the pre-registered `rebuild_repeat_floor_set01` runs (`datasets/july31/experiments.jsonl`). Peak math stays data-dependent, `W × H × channels × 4 × 2`: 560 MiB/frame at 6064×4040 OSC, 8 MiB mono astrocam, 1378 MiB at 61 MP |
| `scripts/lib/siril_run.{sh,py}` flock-serialized siril-cli invoker | flatpak fixes the instance-dir lifecycle race, or Siril invocations stop being per-frame process spawns (e.g. pyscript batching) so there is no window to collide in | 2026-07-28 | **not fired** — the race is a flatpak lifecycle bug, unfixed at 1.4.4/current flatpak, and every builder still spawns one siril-cli per step. MEASURED serializing: 4 concurrent jobs 1.74 s vs 0.47 s single (3.7x, matching serialized 1.88 s not concurrent 0.47 s), 3 of 4 reporting the wait; shell and python share ONE lock (cross-language test 0.93 s = 2x single). The lock is per-USER so it serializes across sessions on this rig. Every participant is now adopted: the one hold-out (`scripts/jwst/*`) went with the JWST cut, so `check_siril_invoke.sh` carries no exemption and any bypass FAILS rather than being reported |
| `scripts/stack/stamp_headers.sh` — capture + `update_key` restore of the acquisition keys the undistort warp drops | the warp stage stops being a TIFF round trip: darktable gains a FITS **WRITER** — it has READ FITS since 5.4.1 (MEASURED: full-resolution export from a 6064x4040 `.fit`), and `.fits` output returns *"unknown extension"*, so the round trip is held open by the write side ALONE. The earlier wording *"gains FITS I/O"* became AMBIGUOUS the moment that was measured: half-satisfied, with the text not saying which half, or the distortion is consumed natively (Siril `register -disto=`, BACKLOG:`native-solve-and-sip`) so the keys are never dropped | 2026-08-14 | **not fired — but the long-stated reason is FALSE and the blocker is HALF the size this row asserted. darktable 5.4.1 READS FITS; it cannot WRITE it.** MEASURED both directions on two independent inputs: `darktable-cli <6064x4040 .fit> out.tif` exports, and the TIFF is **6064x4040** (exiftool) at 11.4 MB deflate RGB — the image was parsed, not fallen back on; `darktable-cli … out.fits` returns **`unknown extension '.fits'`** and writes nothing, and the format-plugin dir carries avif/copy/exr/j2k/jpeg/jpegxl/pdf/pfm/png/ppm/tiff/webp/xcf with no fits. So the round trip survives on the WRITE side alone. **This governs the shared condition wherever it appears** — the `header_provenance_lines` row above and BACKLOG:`native-solve-and-sip` both reason from the larger "no FITS I/O" premise; only a WRITER is missing. NOT tested: photometric fidelity of the read (dimensions and structure only). Values are Siril's own (read from the raw into the calibrated frame's header); in-house code only READS the header and hands them back to `update_key`. LIVETIME is the one derived value (n_frames × EXPTIME, both tool-sourced) because the per-frame EXPTIME Siril would sum was destroyed upstream. MEASURED restored on july27 set-01: 9 keys, LIVETIME 789.0 s = 263 × 3 s, and the solve regained its hint (`scale hint: 10.5-26.3 arcsec/px`, index scales 11-19, vs the prior blind WIDE-FIELD fallback) |
| 5-set combine via TWO interleaved-half composes + a 2-member `-weight=nbstack` join (the 107-sub single-registration max compose needed ~37G transient vs ~24G reclaimable on the previous rig) | x86 disk → re-compose all 107 sub-stacks in ONE registration (every `groups_*` dir is kept for exactly this) | 2026-08-14 | **condition MET on this rig — the re-compose has NOT been run**, so the divergence stands in every shipped product until it is. Free disk is a SNAPSHOT and moved: MEASURED **814 G** available (`df /`, 2026-08-14) where this row long read 950 G, a 136 G drift. Quote the HEADROOM, not the level — the single-registration compose needs ~37 G transient, so the condition clears by >20x and is insensitive to the drift. Declared cost while it stands: the non-reference half carries one extra interpolation; halves span all five sets (interleaved), STACKCNT propagates exact frame weights (794+781=1575); the join landed natively in the cov25 orientation family. The 5-member per-set-stack shortcut is a measured dead-end (pre-cropped members — registry) |
| `observer_frame_diversity.py` — per-group epoch DERIVATION + the corpus alt/az aggregation behind `datasets/corpus/observer_frame_diversity.json` | the sub-stack builder stamps each group's OWN epoch instead of the set's first `DATE-OBS`, at which point this reduces to an astropy coordinate transform anyone can run inline | 2026-08-14 | **not fired** — every group sub-stack of a set carries the SET's first `DATE-OBS` while its WCS centre has drifted up to 4.9 deg of RA (`docs/dead-ends.md`), so a group epoch must be recovered as `t0 + dRA/15.041 deg/hr`. astropy does the coordinate transform and the WCS read; in-house is the epoch derivation and the aggregation. Reads FITS headers and the tracked site record only, opens no pixel, gates nothing, always exits 0. **`--selftest` plants the defect on real data and asserts it REPRODUCES before asserting the fix catches it** — frozen clock 3.599 deg on a FIXED mount against 0.004 deg derived, 839x, and it fails if the improvement is under 5x so a silently-neutered derivation cannot pass. Regenerates the record it describes: `per_set` reproduces the hand-built original identically |
| `check_solve_records.py` record-vs-artifact pointing join | an official tool reports, headless, whether a plate-solve record's stated solution matches the WCS of the file it names | 2026-08-14 | **not fired** — probed: astrometry.net validates a solve against an IMAGE and knows nothing of our records; siril has no record concept; no tool joins a JSON provenance record to a FITS header. Reads headers and records only, opens no pixel, gates nothing, always exits 0. **It compares the record's field CENTRE against the target's own WCS EVALUATED AT THE CENTRE PIXEL, never `CRVAL`** — `CRVAL` is the tangent point (BACKLOG:`pointing-record-names-the-wrong-frame`) and MEASURED 1.662 deg from the centre on the one product that matters, against a clean-population spread of 0.012–0.364 deg over 22 pairs, so a CRVAL join carries ~5x the signal range as baseline error. `--selftest` falsifies on three arms, the third asserting CRVAL and centre-pixel are distinguishable so a comparand swap goes RED. Found one live case on 23 pairs: a record asserting RA 6.03 / Dec −65.10 for a product whose own WCS reads **115.4 deg** away, the false solve the registry already documents; no threshold was tuned, the gap is three orders of magnitude |

---

## `pending-owner` — decisions with the owner, and the input they ordered gathered

**Migrated from the retired `prompts/REPORT.md`** (owner: *"report.md was meant to be
temp. get rid of it. we don't need it. it's clutter."*). Its queue duplicated this
file slug-for-slug and its session transcripts are in git; what follows is what had
no other home. **Everything here is the owner's or is held for them.**

### The HISTORIAN role doc — HELD BY THE OWNER

A fifth seat runs with no role doc. `CLAUDE.md:487` enumerates a "four-session team",
so a fifth standing role is a contract question and `CLAUDE.md` is the owner's file
alone. Measured: `ls prompts/` has no HISTORIAN file, and GNU grep via `env -i`
returns **2** incidental hits tree-wide (`prompts/ORACLE_HANDOFF.md:141`,
`docs/dead-ends.md:3019`) — references to the seat's work, neither a remit.
**OWNER'S RULING: HOLD** — *"I want you to write the doc for the historian later on
after you have an understanding of how it has been helpful in the past (ask the
oracle) — worry about this later. this is a gap but you don't have experience to
write this up yet. hold off."* The seat correctly refused to write its own.
**The input the owner ordered gathered, first-hand from the Oracle:** the seat dated
a claim and refused to collapse its ambiguity (*"NO INSTALLED TOOL CAN CORRECT…"*
entered `6541ce2`; first `PSFEx` anywhere is `4e17e2d`, so TRUE when written by two
days twenty hours — then three defensible staleness dates and no ruling between
them); it reversed the causal order both other seats assumed; it traced a claim's
SEED (**an over-generalised negative becomes CORROBORATION for the next one**, so the
scope error is invisible at the second site because the first is a real measurement
correctly quoted); and it produced a maintenance census with a structural cause.
**CENSUS CORRECTED IN MIGRATION:** it read *"2 commits in its entire existence"* for
`docs/untracked-widefield-standards.md`; `7c746f8` made it **3**, and the shape
stands while the count does not.
**What it changed about the Oracle's method:** *a config dump proves a parameter is
DECLARED, never that it is CONSULTED*; *its sources MOVE and git history does not*
(the pinned-upstream-SHA rule); and the refutation of a clause the Oracle had read at
boot and not questioned.
**Its characteristic error, for the eventual doc's failure catalogue: it attributes
from PLAUSIBILITY rather than from the record** — stray `.ssf` files attributed from
who was busy; `1e7c15e` attributed to a session it predated by ten hours; a class
reported from commit SUBJECTS it had not diffed. It flagged its own scope every time,
which is why none did damage. **The rule: your authority is the diff and the
artifact — not the commit message, which is the author's own account.**

### UNCHECKED — logged, not discharged

- **"A size ceiling on role docs reduces the dilution it was built to prevent."**
  Three seats have reasoned INSIDE this premise since `prompts/README.md` landed;
  that file self-flags its mechanism as DOCTRINE and concedes the ceiling measures a
  CORRELATE, and its own hole (c) is a counterexample in principle. Not reachable by
  the PM's audit-by-re-execution, which cannot reach a premise the brief rests on.
  Routes: the owner, a tool measurement, or the adversary.
- **"Self-picked targets outperformed assigned ones."** Handed over as established
  and **refused from the inside by the seat it flatters**: no counterfactual was
  measured, and it flatters both parties who agreed on it. Competing explanation is
  SEQUENCING, not autonomy — the first units were assigned, narrow, and taught the
  tree. **Operating rule adopted meanwhile: assign the first unit, then release.**

### Live with the owner

1. **The removal-conditions register — the premise previously put to the owner was
   FALSE.** It read *"not one row EVER removed by its condition firing"*; `243b0a6`
   removed a row marked **FIRED** (`solve_field.detect_stars` peak centroids, retired
   because SExtractor's `sep` took the job). The census also inverts: the register
   ran **10 → 4 across late July** and only grows monotonically from ~08-05, so the
   quoted figure describes ten days. **Third framing: a burst of newly-DISCOVERED
   divergences during intensive auditing, not a failure to retire.** What stays open
   is the SCHEMA question — a key, and a destination for code that outlives its
   divergence — not whether the register can shed rows.
2. **A `sirilpy` upstream doc defect**, technically settled, unfiled.
   `get_selection_stats` is annotated `-> Optional[PSFStar]` with prose copied from
   `get_selection_star` while it returns `ImageStats.deserialize(response)`.
   **Outward-facing action under the owner's identity needs their word**, and whether
   it is already filed on Siril's tracker was never checked.
3. **L2 may reopen.** Cosmic Clarity's chroma knob saturates above 0.85, but no
   record says which `--denoise_mode` that was measured under. `render-ladder` is
   user-gated and not the PM's to promote.

### Owner rulings that existed in NO other file

**The per-member trim — RULED: WAIT, and the corner defect is REAL.** Migrated
because a tree-wide search put these verbatim quotes in the retired file and nowhere
else. The degradation is VISIBLE to the owner on the full-frame render — *"they are
already bad in the full frame render. i can see it and no render will make it look
better - just more obvious."* So it is not a below-threshold residue and the render
tier cannot improve it. **Because the cause is unknown, any step forward is a
BANDAID** — the owner applying `CLAUDE.md`'s own rule. The trim stays refused, with
the stated reason: crop and we may never find the real cause, while losing frame
size, SNR-over-time and possibly final quality, *"because there are issues with an
unknown cause, so how deep or subtle the issue is is not known."* **Keep digging is
the ratified direction.**
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

- **Real-flats HANDLED path** — wire master-flat builds into the undistort route so
  staged real flats are USED, not merely refused accurately (owner precedence: real
  flats WIN when present). Not a recommendation to acquire them.
- **`--weight=noise` corpus arm** — motivated by a MEASURED 18–24% cross-night noise
  gap (aug09 haze, +0.16 mag extinction, 16,913 matched stars); pre-registered
  one-knob A/B against the shipped `nbstack` corpus, judged on `snr_regions` +
  `shape_at_sky` + the owner's eyes.
- **Pooled master darks** — belongs under `dark-optimization-fork`, which does not
  mention pooling. Gated on the nights' masters measuring identical (they did: Δ0.1
  ADU, noise within 1%); judged on `noise_split.sh`'s structured term. Per-session
  stays the default.

**Closes when** the owner rules on the historian doc and on the register schema, and
the three queue items above are either scheduled or refused.

---

## `compose-homography-smear` — the largest measured defect in any shipped product

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
put it: x = 5–25% at 0.878–0.885 against its MIRROR x = 75–95% at 0.950–0.968, with
FWHM SYMMETRIC over the same span** (2.460 at x45, 2.897 at x05, 2.717 at x95) — so
it is not the radial field term. **NOT ATTRIBUTED, and canvas-x cannot attribute it:**
it does not separate compose smear from the optics term below. The rho axis is the
discriminator and is deferred. **This item's own rule — only no-band AND no-rho-signal
supersedes — fails on the first clause, so the item STANDS AMENDED, not removed.**

**METHOD FACT — CANVAS-X FRACTIONS ARE NOT PORTABLE ACROSS PRODUCTS, and a band must
be addressed in SKY coordinates.** On the 52-member canvas this item's own defect
point RA 294.86 sits at **x = 76.2%** and its control RA 314.72 at **x = 41.2%** — so
"x = 15–30%" *there* addresses RA 328–320, not the sky the 0.458 was measured on.
Marching only the stated band measures different sky and reads clean.

Ordered work — nothing here is executed on an accepted product:

1. **Reference pinning is RESOLVED** — the compose registers all members in one
   sweep with the reference setref-pinned (a deterministic level anchor).
   **THE SWarp TRIAL IS NOT RESOLVED AND WAS NEVER RUN; THIS ITEM SAID IT WAS.**
   `native-solve-and-sip` recorded SWarp as installed with the comparison OPEN
   while this line struck it through as settled — two items contradicting each
   other about the route for the defect the owner can see.
   **SWarp's HALF STANDS; SIRIL'S IS FALSE AND CLOSED THE ROUTE THIS CHAIN ALREADY
   SHIPS.** MEASURED (`TOOLS.md`): SWarp has NO SIP reader at all
   (`A_ORDER`/`B_ORDER`/`AP_ORDER` occur zero times in its 2.41.5 source; a 3-char
   compare truncates `RA---TAN-SIP` to `TAN`; the distortion gate needs PV terms
   SIP does not carry, so it applies nothing and warns about nothing) — **confirmed
   by SWarp itself, which produces an IDENTICAL output canvas and CRVAL to nine
   decimals from a TAN-SIP header and from one with SIP deleted.**
   **"Siril discards per-image distortion BY DESIGN" is REFUTED.** It reasoned from
   `seqapplyreg`'s help listing registration data as
   `shift | similarity | affine | homography`. That list is TRUE and does not carry
   the conclusion — the registration data IS linear, and the SIP undistortion is
   COMPOSED with it. Siril's own registration manual: *"it is first corrected for
   distortion and then linearly projected … this actually occurs in a single
   operation (the pixel mapping is computed as the composition of this non-linear
   correction and then the linear projection)"*, and *"undistortion will be applied
   as defined when platesolving the sequence … if the images were plate-solved
   using a SIP order larger than 1, then undistortion will automatically be
   included"* (siril.readthedocs.io, Registration, 1.4.4 stable). The corroboration
   cited was `register -disto=`, a DIFFERENT command this registry records as
   designed for *"a sequence sharing one plate solution"* — which is why it fails
   and why it says nothing about `seqplatesolve`.
   **THE ARTIFACT SETTLES IT — THE ASTROMETRIC ROUTE IS THE SHIPPED DEFAULT.**
   `run_undistort_compose.sh:330` is `seqplatesolve s`; `register -2pass` survives
   only behind `--starpair`, which prints *"NOT the shipped route … must never
   build a product anyone judges or ships"*. The compose greps siril's OWN log for
   *"Astrometric registration computed"* and *"undistortion will be applied"* and
   exits 4 if either is missing (`:351-358`), so the product cannot be BUILT
   without the tool reporting it; the stamp (`:389-390`) separately defaults
   `REGU=F` and flips to T only on that line. `web/results/aug06/stack_set-01+02+03_full.fit`
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
   What is left is the RHO AXIS, which is the discriminator and is deferred: a column
   averages over whichever members cover it, so a wider product DILUTES a band rather
   than sharpening it, and no-band-with-rho-signal reads as fixed when it is only
   diluted. Only no-band AND no-rho-signal supersedes — and a band survived.
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
   cause. Last resort, and it must be called what it is.
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
(R² 0.90 against sensor x, **0.05 against elapsed time**), and it sits on the side
stars drift OUT of, and it is the exit edge that smears. **The −3.87 px/frame figure
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

**Two hypotheses, not yet separated** (ledger
`exit_edge_registration_vs_fixed_lens_residual`) — both predict the measured
sensor-position collapse, and they differ only in DRIFT-SPAN dependence:
1. an uncorrected asymmetric (decentring) distortion term fixed in sensor
   coordinates — lensfun's `ptlens` is purely radial and has no tangential terms, so
   it cannot remove a left-right asymmetry by construction;
2. a registration failure at the exit edge — stars there are transient, so the
   global homography is least constrained on that side.

**The discriminator:** stack the same sensor region from sub-blocks of decreasing
drift span (50 / 25 / 12 consecutive frames) and measure blur at MATCHED sensor x.
Flat ⇒ fixed residual. Falling with span ⇒ registration. Stacking only the low-drift
half of a set would be a BANDAID as a fix, but is the cheap end of this arm as a test.

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
  **BOTH OWNER STATEMENTS STAND SIDE BY SIDE UNTIL THE OWNER RESOLVES THEM, and
  neither is assumed away.** That one governs the FINAL FRAMING. The owner has
  since said they are *"more worried about stacking bad sections than about not
  stacking enough"*, which governs what goes INTO the combine — a different act,
  and the two collide only if a per-member trim is adopted, since that trades
  area BEFORE the compose rather than cropping the picture after it. Measured
  cost of the collision, so the choice is made against numbers: a +x member trim
  keeping 80% of each member leaves 4 of 20 measured union boxes with no
  contributing member at all; a radial cut to rho 0.80 costs 3.3% of the
  delivered crop's area and 9.4% of the member-contributions inside it
  (`datasets/aug06/corner_work/`). **Not recommended on today's evidence** — the
  predicted gain is corner roundness 0.911 -> 0.938 and the cause is measured
  in-exposure but unidentified. The composite-level arm
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
  stub) with the six current knobs and a per-knob class-risk note; first
  `baseline.json` via the no-regression harness; per-arm output tree
  (`web/results/<session>/exp_<param>_<stamp>/`) and the `<final>_stages/` labeled
  sequence, both binding requirements the tier does not yet emit;
  `judgment_package.py` re-wire (its PNG8 pairing predates the 16-bit-only policy).
- **Two known limits:** a set can carry only ONE ratified `render` block (keyed by
  name), so two kept looks are not expressible; and a mono set STOPS loudly — the
  luminance-only variant is unbuilt.

One knob per arm, hypothesis pre-registered, judged on full-frame lossless PNG16.
**Closes when** an approved, re-baselined render comes out of a laddered arm.

## `learned-deconvolution` — the tool it named CANNOT run the test

`render_tier.sh` skips deconvolution on three grounds that all hold: classical RL is
a measured dead end on in-exposure trailing, BlurXTerminator is not installed, and
GraXpert's is the immature path. The registry explicitly does NOT dead-end a
LEARNED deconvolver, so the question is live.

**THE ARM THIS ITEM PROPOSED IS REFUTED BY A MEASUREMENT 500 LINES AWAY, AND THE
ITEM READ AS READY WORK.** It named `/opt/cosmicclarity-6.6`'s
`deep_nonstellar_sharp_cnn_radius_{1,2,4,8}` and specified a non-stellar sharpen as
the test. `TOOLS.md` records, MEASURED on this rig: Cosmic Clarity **is a Qt tool
that BLOCKS on a modal dialog**, **its CLI arguments are IGNORED**
(`--sharpening_mode "Stellar Only"` was passed and the dialog showed `Both`), and
**the non-stellar pass CRASHES on real data** — the exact pass this item specified.
Verdict there: *"ATTENDED and NOT scriptable"*. `render_tier.sh` is headless, so the
test cannot run as written. **Two sessions independently read that binary's `--help`
and reported a headless capability it does not honour; this item is the third
instance of the same error, still standing.** Mechanism note that survives: the
model space is `radius_{1,2,4,8}`, a scalar RADIUS — spatially varying but
**ISOTROPIC**, size only and never ellipticity — so it could not address an
anisotropic corner term even if it were drivable.

**What survives is the QUESTION, not the arm:** does a learned deconvolver buy
OBJECT detail? That is distinct from the corner question — a symmetric sharpener
cannot de-trail an elongated PSF — and it needs a headless CPU-Linux learned
deconvolver, which is the same procurement gap `corner-fix-landscape` tracks.
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
   coefficients, which four-corner spread cannot do on a structured field. Register
   row 67 records the same blind spot for `baseline_guard.py`. **Swapping an
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
session-end temperature.

## `native-solve-and-sip` — two probes, in order

- **`platesolve -localasnet` on the mildly-trailed class.** The solver dead-end was
  measured on roundness-0.615 frames; july23 measures 0.80. If Siril's own blind
  solve handles this class, `solve_field.py` gains a native sibling (the external
  route stays for heavily-trailed data). One stack, one probe, record either verdict.
- ~~**Siril-native SIP undistort vs the darktable warp.**~~ **CLOSED — RUN and
  REFUTED AS INVOKED.** Two beliefs were corrected on the way and both are in
  `docs/dead-ends.md`: `seqplatesolve -order=3` DOES solve members natively
  (388/371 matched stars, centres agreeing with astrometry.net to 0.001°), so the
  "Siril cannot solve this class" belief had widened past its evidence — it was
  measured on single ULTRA-WIDE TRAILED frames and stacked members have round
  stars. But `register -disto=` is a SHARED-solution facility: each member
  undistorted by its OWN SIP then composed measures 3.99/6.42/6.19 px against the
  shipped route's 0.29/0.63/2.10/2.99. **Siril's own design assumes ONE optical
  state per sequence.**
  **AND THE ARCHITECTURE THAT KILLED IT IS THE ONE THE STANDARDS AVOID — RECORDED
  IN OUR OWN TREE AND NEVER CONNECTED TO IT.** `docs/untracked-widefield-standards.md`
  §H.3(3) already says the field uses **a high-order term shared across a stability
  context plus a low-order per-exposure term**, and that *"the shared variant does
  not appear to have been tried"* (`:966–974`). **SCAMP's default IS that
  architecture** — `STABILITY_TYPE INSTRUMENT`, verified by `scamp -d` — so the
  per-frame SIP failure recorded here is precisely the failure mode it exists to
  avoid, and the untried variant has been named in this repo the whole time.
  **THE QUANTITATIVE HALF, and it is why this is not merely a different shape.**
  MECHANISM, not measured: per-frame we have ~**37** Tycho-2 matches, which by the
  Pan-STARRS occupancy yardstick (`TOOLS.md`) supports **order 1 and not order 2**.
  But `STABILITY_TYPE INSTRUMENT` fits ONE distortion polynomial per astrometric
  instrument using detections from **ALL** exposures in it — so the count
  constraining the shared term is **POOLED, not per-frame**: across ~13 members
  that is roughly **480** against the same table's **300 for order 4**, and SCAMP's
  default `DISTORT_DEGREES` is **3**, which needs 128. **The shared-context
  architecture does not merely dodge the sparsity failure; it moves the reachable
  order from 1 to 3–4 on the field's own yardstick.**
  **THE CONDITION ON THAT, and it is checkable rather than assumable:** pooling
  helps only if the pooled OCCUPANCY fills the (order+1)² grid, not merely the
  total count. Members 4.28° apart with ~1000 px of drift make the pooled coverage
  far better than any single frame's, which is favourable — **but it is an
  occupancy check, and the machinery for it exists.**
  **THE SUCCESSOR IS NOW RUNNABLE AND BELONGS TO
  BACKLOG:`compose-homography-smear`** — per-image resampling onto a COMMON output
  WCS using each exposure's full solution, which SWarp does once fed a distortion
  it can read. SWarp 2.41.5, `sip_tpv` 1.1 and SCAMP 2.10.0 are all installed; the
  two entry paths and the wrong-for-this-data defaults of both tools are recorded
  there, not restated here.

## `one-sided-band` — the fix-path gate is ANSWERED; what is left is one unattributed term

Stars in the far corners of combined products are less round and slightly larger.
The defect is REAL, visible to the owner on the full-frame render, and confirmed on
single unregistered RAWs by two independent tools. **Nothing the pipeline does
causes it** — coverage depth, the compose, within-member registration and any
lensfun distortion residual are each eliminated by measurement, and Siril
`findstar` on THREE SINGLE RAWS (debayered, uncalibrated, unwarped, unregistered,
unstacked, 8074 stars) carries the term at full size. An uncorrected frame cannot
carry the RESIDUAL of a correction that has not been applied.

**PRODUCTS UNDERSTATE IT.** An isotropic blur added everywhere compresses a ratio
toward 1, so the raws' corner defect is **+28.7% against the delivered +23.6%**
(`resample-cost-and-drizzle`). Single-RAW measurements are unaffected — which is
most of this item's evidence — but any product-vs-member or product-vs-raw
comparison inherits it.

### The gate is answered and it FAILS

**`corner-fix-landscape` gates its only FIX-classified route (`rl -loadpsf=`) on a
genuinely FIELD-CONSTANT component. Asked directly — is there a single trail scale
`f` making `C(ρ) − f·T(ρ)` a constant 2-vector — the answer is NO, unconditionally**
(`constancy_fit.json`, `frame_depth.json`; PM-audited by re-execution).

| sample | DSC_6239 | axis χ²/4 | constancy χ²/dof |
|---|---|---|---|
| N = 40 | **in** | **69.5 — REJECTS** | **53.1** |
| N = 40 | out | 686.7 — REJECTS | 129.4 |
| N = 5 | in | 3.0 — no rejection | 1.81 |

An earlier five-frame run appeared to hinge on excluding one frame; **that was a
small-sample artefact** — one anomalous frame is 20% of five and 2.5% of forty.
Subset bracket EXACT: the original five sit inside the forty and reproduce
`constancy_fit.json` to the digit (15.4 / 3.0 / 1.81 / 4.31 ± 1.80).

**Three things it is NOT, each excluded by measurement rather than argument:**
- **Not a binning artefact.** The fixed term's axis runs **+0.04 / +13.86 / +21.94 /
  +15.74 / +10.49°** across equal-COUNT bins and **+6.40 / +17.31 / +22.91 / +13.80
  / +17.47°** across ρ-EQUAL bins — span 16.5° against 17.4°.
- **Not the incomplete-azimuth artefact**, this thread's most repeated failure. The
  inscribed circle holds to ρ = 0.5544, so bins 1 and 2 lie WHOLLY inside complete
  azimuth, and the rotation is already there between those two alone: **+12.42 ±
  2.10 (5.9σ)** with every frame in, **+12.96 ± 0.82 (15.9σ)** without DSC_6239.
  The axes are also non-monotone across ρ (5.99 → 18.41 → 21.30 → 13.29 → 14.08),
  which no single radial term produces.
- **Not a class.** "First frame of a run" is one frame: group starts read −36.91 /
  +16.84 / +17.20 / +17.50 / +16.29° against index ≥ 25 at +17.39 ± 1.52 (n = 20),
  starts-minus-6239 against the rest is **−0.44 ± 0.43°, 1.0σ**, and DSC_6239 sits
  at robust **z = −25.7** where the next most deviant of 40 is −1.4. **So the
  exclusion used across this thread does not become a systematic anywhere it has
  been applied**, including the injection rebuild.

**TWO LIMITS TRAVEL WITH THE VERDICT AND NEITHER IS OPTIONAL.** χ²/dof of 53–129
means the model is badly MISSPECIFIED rather than that it measured something. And
**this design can KILL the route but can NEVER quote a trail scale** — T varies only
5.1% in magnitude and 1.5° in axis across the bins, so `f` is nearly collinear with
the constant and is separately degenerate with any overall scale error in the WCS
behind T.
**THE "design condition 126–132" THIS SENTENCE CARRIED IS WITHDRAWN — IT IS IN NO
RECORD.** Enumerated: `constancy_fit.json` holds **16** `design_condition` values,
and they are bimodal — the five per-bin values per binning run **1.08–2.00**
(`rho_equal` 1.0809/1.0950/1.0878/1.6802/2.0010; `equal_count`
1.1027/1.0911/1.0949/1.1105/1.8247), and the six WHOLE-FIT values are
**100.43, 130.81, 136.08, 140.05, 141.45, 141.84**. **Exactly one (130.81) lies in
the quoted range and no subset spans 126–132**; both revisions of the file are
identical on this. The COLLINEARITY the sentence exists to state is UNAFFECTED and
is in fact understated — the whole-fit condition runs to 141.8. What is withdrawn
is the range, which is the same class as this thread's withdrawn `~1.1` χ²/dof: a
headline pair quoted from a computation nobody persisted, and it survived because
nothing about it looked wrong.

**COMPOSITION NOTE for a gated target:** `psf_work/f{1,2,3}.lst` — Gate 1A's
8074-star sample — is DSC_6239 / 6339 / 6439, so **one third carries the anomaly**.
The gate reproduces exactly because it tests the estimator rather than the sample,
but 0.5869 / 0.5798 are not corpus-representative.

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
- **~~Cosmic Clarity~~ WITHDRAWN — not a headless candidate, and the tree said so.**
  `TOOLS.md` records it MEASURED: a Qt tool that BLOCKS on a modal dialog, **its
  CLI arguments IGNORED**, and the non-stellar pass CRASHES on real data. **Three
  sessions read its `--help` and reported a capability it does not honour.** What
  survives is a mechanism note: its model space is `radius_{1,2,4,8}`, a scalar —
  spatially varying but **ISOTROPIC**, size only, never ellipticity.
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
  **Under this repo's own evidence gate the two halves belong in different places:**
  whether to accept a visible artefact for sharpness is aesthetic and the owner's,
  but the artefact's MAGNITUDE is a thing an instrument settles — so the owner is
  currently being offered a 6.26% gain against an unquantified loss. **The fixture
  that would close it already exists and needs no new design:** the same planted
  synthetic frames pushed through the shipped `register -2pass` →
  `seqapplyreg -interp=` operation verbatim, with a sharp-edge target added and the
  overshoot measured clamped vs unclamped. Cheap, and it converts an owner decision
  from one number to two.
- **BANDAID / accepted failure mode, NOT candidates:** PSF homogenisation, zone
  down-weighting, cropping. Owner-REFUSED as a category, with Zackay & Ofek 2017
  making it a measured information loss (`docs/dead-ends.md`).

### The ceiling is a noise budget, not a wall — MEASURED

**THIS ITEM'S THREE MEASURED THREADS ALL REPLAY FROM `datasets/aug06/experiments.jsonl`
— checked 2026-08-14.** The OTF scan (`two_probes_drizzle_input_and_otf_zeros`):
0 of 12 at centre with max recovery **0.0034**, 0 of 12 at corner TL max **0.0076**,
1 of 12 at corner BR at **0.0223**; MTF ladder centre 0.837/0.575/0.265/0.072
against corner TL 0.685/0.317/0.079/0.028. The drizzle refusal: the tool's verbatim
string, on a sequence-TYPE check. The clamp trade: 0.45% / 6.26% with a 0.00%
nearest-neighbour control. **And the procurement negatives still HOLD** —
`torchmfbd`, `pyimcom`, `sf_deconvolve` and `properimage` are absent from both
`astro-venv` and host `python3`; only `galsim` 2.8.5 imports, which is what this
item already records.

**A CONTROL FIRED ON ITS OWN AUTHOR HERE, AND IT IS WORTH KEEPING.** `4cabf36`'s
first pass asked only whether the minimum in-band MTF fell below a threshold, read
0.004–0.009 and printed *"IN-BAND NULL PRESENT"* — conflating a monotone ROLL-OFF,
which every PSF has and which bounds SNR, with a true NULL, an interior minimum the
MTF recovers from. Caught inside the session and recorded in the commit. **That
distinction is the whole probe:** had it shipped, a noise budget would have been
written down as an information wall, and the restoration question would have been
closed permanently on an artefact of the test rather than on the data.

Scanned on the PSFEx model's own corner PSF, 12 radial cuts per position, asking
whether the MTF ever RECOVERS after its running minimum: **0 of 12 cuts at centre,
0 of 12 at corner TL, 1 of 12 at corner BR (0.0223, model noise). No in-band OTF
zero anywhere — the corner is ATTENUATED, not nulled.** Median MTF over azimuth
runs centre 0.837 / 0.575 / **0.265** / 0.072 against corner TL 0.685 / 0.317 /
**0.079** / 0.028 at |f| = 0.1 / 0.2 / **0.3** / 0.4 cyc/px, so the corner is ~3×
down through the mid band and any restoration that flattens it applies ~3× gain
there. **SCOPE, and it must travel with the number: this is the OTF of the PSFEx
MODEL, not the true PSF.** The eigen-PSFs are full 25×25 images and CAN represent
a null, so the polynomial field fit is not the obstacle — but PSFEx fits noisy
undersampled stars and a sharp null could be smoothed away. It shows no MODELLED
null; it cannot prove no true null.

### Drizzle

**REFUSED on debayered input, MEASURED not inferred:** `seqapplyreg -drizzle` on a
real 6064×4040×3 debayered RGB sequence returns verbatim *"This sequence is not
mono / CFA, cannot drizzle"*. So the refusal is a SEQUENCE-TYPE check rather than
anything Bayer-specific. **One detail recorded without a claim attached: the
refusal names mono as acceptable, so a green-plane-only mono route is not refused
by this check** — and `split_cfa` now provides exactly such a plane with the greens
identified (`TOOLS.md`). Unprobed, and not asserted to be useful.

**Closes when** an anisotropic treatment is procured and measured, or the owner
accepts the corner as-is. **The in-chain question is settled: no route on this rig
recovers corner detail, and the defect is in the photons of single unprocessed
RAWs.** What remains is a procurement decision and an acceptance decision, both the
owner's — see `compose-homography-smear` for the DIFFERENT defect that IS caused by
a chain stage and does have a live candidate route.

## `resample-cost-and-drizzle` — the clamp costs 14× the kernel, and it is a pinned doctrine

**MEASURED, and it is a cost of OUR OWN PIN rather than of Lanczos4.** Six
synthetic frames, 700 stars each, planted FWHM 2.10 px matching the corpus,
sub-pixel shifts so interpolation has real work, through the shipped operation
verbatim (`register -2pass -transf=homography` then `seqapplyreg -interp=`):

| arm | w | cost |
|---|---|---|
| input | 2.2050 | — |
| nearest (control) | 2.2050 | **0.00%** |
| cubic | 2.3238 | 5.39% |
| lanczos4 **`-noclamp`** | 2.2150 | **0.45%** |
| lanczos4 **CLAMPED — the shipped path** | 2.3431 | **6.26%** |

**The clamping costs 13.8× what the Lanczos4 kernel does.** The kernel is nearly
free on this PSF; the clamp is essentially the entire cost. The nearest control
reading exactly 0.00% is what makes 6.26% credible as interpolation blur rather
than a fixture artefact.

**This is a doctrine number.** `check_registration_pins.sh` pins lanczos4 WITH
clamping — pinning it means asserting `-noclamp` is absent — and the guard's own
comment states the reason: *"clamping is the DEFAULT this repo keeps (lanczos4
rings on stars)"*. So ~6% of PSF width per resampling pass is what that pin
costs. **It is a TRADE, not a defect**, and the ringing it suppresses is real and
recorded elsewhere in this registry; **no call has been made and none should be
made without the owner's eyes**, since ringing is judged and blur is measured.

**THE COUPLING, and it changes how every product-level shape number is read.
STATE THE QUANTITY WITH THE FIGURE — these are TWO different dilutions and they
were once reported as if commensurable:**
- **ELLIPTICITY falls 20.02%** at fixed aberration over the whole chain
  (`1/1.1182² = 0.7998`), since `e ≈ κℓ²/2w²`.
- **A centre-to-corner SIZE RATIO compresses 1.2874 → 1.2359**, i.e. the chain
  understates the corner size excess by **5.2 points, not 20** — de-blurring the
  delivered crop (centre 2.480, worst corner 3.065 px) by the measured 1.1031 px
  chain kernel in quadrature gives raws of 2.221 and 2.860.

**The consequence is the one that matters for this repo: an isotropic blur added
everywhere compresses a ratio toward 1, so THE RAWS' CORNER DEFECT IS WORSE THAN
ANY PRODUCT SHOWS — +28.7% against the delivered +23.6% — and every product-side
corner number here is CONSERVATIVE by a now-knowable amount.** Single-RAW
measurements are unaffected, which is most of the corner thread's evidence; any
product-vs-member or product-vs-raw comparison inherits it.

**THE DARKTABLE HALF IS MEASURED AND THE CHAIN TOTAL IS CLOSED.** Full-sensor
6064×4040 so the lens model lands at the right field radii, sky pedestal at the
corpus's own 1053 ADU, and star amplitudes drawn from the REAL distribution of
aug06/set-01 frame 1 (p10/p50/p90 = 211/469/1900 ADU) rather than convenient
levels:

| arm | w | cost |
|---|---|---|
| **nodist CONTROL** | 2.2050 | **0.00%** |
| lensdist = the shipped warp | 2.3346 | 5.88% |
| **chain total (darktable + Siril)** | **2.4655** | **≈ +12%** |

The control at exactly 0.00% is what makes 5.88% attributable to the WARP rather
than to the TIFF round trip, the ICC leg or the float conversion — a control that
*can* read zero and does.
**Quadrature is VERIFIED, not assumed:** run in actual series, predicted 2.4610
against a measured mean of 2.4525 — **−0.35%**, so combining the two passes'
kernels in quadrature holds to better than 1%.
**PRECISION BOUND, and it governs every figure here:** darktable measured 5.88%
and 5.67% on two independently generated fixtures, so **fixture-to-fixture
variation is ~0.2 pp**. Quote these as ~6% and ~12%, never to three significant
figures.
**ICC checked and it does not bite, for a reason that generalises:** star
AMPLITUDES straddle the toe (median 455 ADU = 0.00695 linear) but every actual
PIXEL sits on the 1053 ADU pedestal = 0.01607 linear, 5× above it, so the band is
never reached.
**DEPTH MATCHING WAS MANDATORY AND A COMMON AMPLITUDE FLOOR WAS IMPOSSIBLE** —
the lensdist arm detects 587 stars against the input's 393 (49% deeper), and
darktable's float output is not in ADU (inputs 1259–2.765e4, outputs 0.010–0.42),
so the scales are incommensurable and rank-matching on the N brightest is the
only valid form. Unmatched 6.09% against rank-matched 5.88% is the size of the
artefact that avoids.

**A MEASUREMENT TRAP THAT NEARLY PRODUCED A FALSE NULL, and it generalises to any
before/after on a registered sequence: `register -2pass` gives the REFERENCE
frame no transform, so it receives no interpolation at all.** The first series
read had "darktable only" and "darktable THEN Siril" identical at w 2.3299 — the
Siril pass appearing to cost exactly nothing, which reads as a spectacular
quadrature failure. The cause was that 2pass had chosen image 1 as reference and
`S_w_00001` is an untouched frame; the earlier separate arm happened to pick
image 5, which is why it never surfaced. **MEASURE A NON-REFERENCE FRAME,
ALWAYS.** It was caught only because the null was too clean.

**Two tool facts found by failing, both now sourced from Siril itself:**
- **`seqapplyreg -interp=none` FAILS on a homography-registered sequence.** The
  help says `none` forces the transform to a shift, and a homography cannot be
  reduced to one, so it errors rather than degrading silently. Use
  `-interp=nearest` for a no-blur control.
- **Bayer drizzle and the lensfun undistort stage are MUTUALLY EXCLUSIVE as
  currently built**, verbatim from Siril's help: *"when using -drizzle on images
  taken with a color camera, the input images must not be debayered. In that
  case, star detection will always occur on the green pixels."* The undistort
  route runs darktable on debayered data. So "just try drizzle" is not a one-knob
  experiment on this route.

**Why drizzle is still live** (Oracle shortlist item 2, never opened): FWHM
2.0–2.4 px debayered is ~1.4–1.7 px on the green CFA lattice — undersampled — and
the untracked drift supplies ideal sub-pixel dither across 500 frames, the
textbook case. `docs/dead-ends.md` rules drizzle out on TRAILING grounds, but the
trail here is 1.4–1.9 px, comparable to the PSF rather than a long streak.
**Re-open with the number, not the category.**

**TWO OF THIS ITEM'S THREE CLOSING CLAUSES HAVE ALREADY FIRED, INSIDE ITS OWN
BODY, AND NOBODY FIRED THEM** — the same shape as the `guards-and-ci` row that
outlived its fix by three days. The old condition read *"closes when the darktable
half is measured and the shipped total is known, and the drizzle question is
decided"*. **The darktable half IS measured above (5.88%, against a control
reading exactly 0.00%) and the shipped total IS known (~12%, with quadrature
verified to −0.35%).** Only the drizzle decision was ever outstanding.

**Closes when** the drizzle question is decided against the measured number rather
than against the category — i.e. whether ~1.4–1.9 px of trail on a 2.0–2.4 px PSF
disqualifies a technique whose preconditions (undersampling, sub-pixel dither
across 500 frames) this corpus otherwise meets textbook-perfectly. **The
architectural blocker is measured and is not the trail:** `seqapplyreg -drizzle`
refuses a debayered RGB sequence outright, so it is not one knob on this route.
`split_cfa` now supplies an un-interpolated mono green plane with the greens
identified, which is the only path the refusal does not name — unprobed, and not
asserted to be useful (`corner-fix-landscape`).

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

## `final-best-percent-pass` — one target, many sessions, stack the best N%

The standing multi-session practice's endgame (user-ratified; walkthrough §6):
after many ~500-frame sets accumulate on one target, a FINAL pass analyzes
ALL sessions' raws and stacks only the best percentile. Unbuilt mechanics: a
cross-session frame-quality surface (per-set `frame_metrics.json` exists;
nothing ranks across sessions), a global best-N% selection the builders can
consume (`cullspec` excludes are per-set), and the ladder itself — N% arms,
one knob per arm, judged on full-frame lossless finals; README's
reference-standard row 1 soft-culling caution applies (selection adopted
through a measured ladder, never a default). Gated on the corpus existing.
**Closes when** a final-pass product ships from a measured best-N% ladder
across at least two sessions' raws with its per-set selection recorded.

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

**(a) AND (b) HAVE LANDED. (c) and (d) remain.** `CALFLAT`/`CALDARK` are built from
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

## `guards-and-ci` — the runner EXISTS; what remains is a per-block bit-depth gap

**`scripts/qa/run_guards.sh` is BUILT and GREEN** — it runs all eight guards plus
every data-free selftest, **24 checks in 27-33 s**, per-check PASS/FAIL, non-zero
exit if any fails, `--list` for the roster. Documented at `README:444` with its
limits in the row. **Fire-tested BOTH ways**: breaking the executable bit takes it
RED at exit 126 while `bash scripts/…` passes blind — reproducing the registered
trap exactly — and a planted unpinned `set16bits` takes it RED through the
content path, so it is not only launch failure that propagates.

**Invocation is `./scripts/…`, never `bash scripts/…`, and that is load-bearing
rather than style:** `bash` sidesteps the executable bit, which is why an audit once
reported five passes while a guard was non-executable and the row describing it
outlived its fix by three days.

**STATED LIMITS, carried in the runner's own GREEN output so it cannot imply
coverage it lacks:** these guards verify WIRING, never OUTPUT. `check_bitdepth` is
per-FILE and static, so a builder already emitting `set32bits` in one generated
`.ssf` passes even if a newly added emission omits the pin. One check reaches the
network (the ESA Gaia control) and is labelled `[network]` and run unconditionally —
**no `--skip` flag on purpose**, since a conditional path nobody exercises is the
defect class the runner exists to catch. THREE checks are excluded with reasons
rather than dropped silently: `member_separation --selftest` (needs a live seq-dir),
`object_tilt_null.sh` (real corpus data), and `x86_bootstrap.sh --selftest-gaia`
(downloads the catalogue). **The per-dataset `corner_work/*.py` instruments are NOT
excluded as a class** — `pa_convention` and `constancy_fit` are IN the roster,
marked `[lib]`, by the deliberate exception `e939f26` landed for: the exclusion
keys on what a file IS, not where it lives. **An earlier revision of this row
listed them as excluded, which UNDERSTATED coverage** — the same wording `README`
already records as a corrected error, alive here at a third site.

**AND THE ROSTER'S OWN CONSTRUCTION IS A KNOWN LIMIT, recorded in its docstring:**
it was built from `grep -rln selftest`, so a selftest exposed under a
non-matching flag is **silently absent rather than reported missing** —
`--selftest-gaia` is the proof the naming is not uniform. The only mitigation that
works is procedural: add the CHECKS row in the same commit as the selftest, since
nothing detects a check that was never added.

**REMAINS OPEN, deliberately deferred:** the bit-depth check's per-FILE granularity.
Per-block would need the printf/heredoc blocks split on the `> "$X.ssf"` boundary
every builder uses, and a fragile parser is worse than a stated limit. **Closes
when** that granularity is worth the parser, or the limit is accepted permanently.

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
  hand. Closes when the chain builds a master flat from a staged `flats*`/`calib`
  dir and passes it as `--flat=` — the builder already takes any master, so this
  is chain wiring, not a builder change.
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
already carries one, so running frame QA BEFORE the mount probe makes every
`fwhm_arcsec` inherit the nominal scale instead of the solved one — a 2.8% error
(17.5031 nominal vs 18.003 solved). It is self-documented via `pixel_scale_source`
and never re-derived once written. **AMENDED (measured during the optics-state
audit): the 18.003 "solved" figure is itself an artifact** — all nine stack
solves across three sessions read 16.98–17.08 ″/px, so the probe pipeline's
green-plane scale arithmetic inflates by ~5.6% and every `fwhm_arcsec` in the
corpus rides it (px figures unaffected; `datasets/aug06/experiments.jsonl`,
`solved_scale_artifact_18_vs_17`). **Closes when** the scale is re-derived from
a direct full-frame solve (or the record refreshed against the stack solve)
and the probe-pipeline arithmetic's error is root-caused.

## `single-pass-reference-lottery` — the groups route pins it, the single-pass route does not

`run_undistort_groups.sh` pins `setref s 1` after its `register -2pass` because
"2pass's auto-pick made that a lottery across rebuilds" — with `-norm=addscale
-output_norm` the reference IS the product's level anchor, and two builds of one
set measured 67 vs 43 ADU. `run_undistort_pipeline.sh` runs the same unpinned
`register lt -2pass` and has no such pin.

**MEASURED that it moves the product, not just the level** (12 frames of
aug09/set-05, one knob — the flat): `skyflat_set-05` → reference image 1 and a
**4896x3616** canvas; `skyflat_set-01` → reference image 2 and **4887x3641**. So
the reference choice is sensitive to the calibration, and it changes the delivered
CANVAS, not only its anchor. Two rebuilds of the identical arm are otherwise
bit-identical in pixels (0 differing pixels of 3x3616x4896), so this is the one
non-deterministic-looking input on the route — and it is not noise, it is a real
dependence on the data.

**REPLICATED on a second night, a second knob and a second class of calibration
change** (12 consecutive aug06/set-01 frames, one knob — `--subsky-lights`):
reference index **8 → 11**, canvas **6038x4033 → 6037x4030**. So it is not a
property of the flat: ANY step that changes the calibrated frames' statistics
re-ranks the quality the 2pass picks its reference from. **And the pick is
DETERMINISTIC** — a repeat of the unflagged arm, identical in every argument,
reproduced the `.seq` BYTE-for-byte (same reference, same homographies) and the
stack pixel-for-pixel (0 differing of 73,053,762). That matters beyond this
item: because the registration is a deterministic function of its input, a
re-run of an arm's own configuration reproduces its registration exactly, so an
A/B can pin to a donor that IS the control's registration rather than a stand-in
for it — verified end-to-end here, a from-raws member rebuilt under today's tree
reproducing its control member at **0 differing pixels of 69,225,420** across a
PIPEREV change (a1dc91b → 1f261e7).

**Closes when** the single-pass route either pins its reference the way the groups
route does, or records why it must not. Do not pin it as a side effect of a
diagnostic: the A/B path already has `--regdata=` (removal-conditions register),
which pins registration WITHOUT touching what a default build emits. Changing the
default changes every single-pass product's canvas, so it is a declared-delta
change needing its own before/after.

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

**FENCED.** Testing that reaches into the flat-residual line, which the owner has
PAUSED pending real flats. Nothing here reopens it, and this item is recorded so
the question survives the session rather than to schedule work. **Closes when**
the owner either rules it out of scope or unpauses the line it depends on.

## `capability-gaps` — real capabilities the pipeline lacks

Each lands as a measured declared delta when its gate opens.

- **Full-size dual-band** — native Ha + 2× drizzle of OIII instead of downsampling
  OIII to Ha's half size. Gated on measured dither coverage (the per-frame
  `dither_phase_frac` record exists).
- **LRGB join** — `compose` REFUSES a `luminance` member, because L joins after both
  parts are stretched and this compose-then-render flow cannot express a nonlinear
  step. `rgbcomp -lum=` is the headless mechanism when an L corpus arrives; the CLI
  `-lum` blend colour space is undocumented — resolve before first use.
