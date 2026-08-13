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
divergence, add the row in the same commit. (2) Every row carries the date it was
last CHECKED against reality, not the date it was written — "not fired" with no
date is the exact state that let a fired condition sit unnoticed. (3) Status is
the current verdict and its evidence, not a history of the divergence; mechanism
narrative belongs in `docs/dead-ends.md` and the script's own docstring.
(4) A condition that depends on the DATA (disk, sensor size) is re-checked per
dataset, and says so.

| divergence | retires when | last checked | status |
|---|---|---|---|
| `coverage_frame.py` largest-all-covered-rectangle search over Siril `stat` boxes (+ `web/verify_framing.py --channel=`, and the `--regdata-dir=`/`--tag=` A/B flags on `run_undistort_groups.sh`) | an official tool reports, headless, the largest fully covered axis-aligned rectangle of a registered union — or a coverage map ON the union's own canvas that `verify_framing.py --map` can consume | 2026-08-12 | **not fired.** Probed with the command run, not the help read: Siril `stat`/`bg` measure a selection or the whole frame and know nothing about coverage; `seqapplyreg -framing=` picks min/max/COG framings and reports no covered region; the repo's own `coverage_probe.sh` DOES build a true per-pixel member-count map, but through `register -2pass`, so on an ASTROMETRICALLY registered union its canvas is not the product's — its own docstring already refuses that use. The repo held the VERIFY half (`verify_framing.py`) and the CONSUME half (`finish_render --crop-record`) but nothing that PROPOSED the rectangle, so on a union nobody had hand-drawn a box for, the registry's pinned crop-before-background order could not be followed at all. Every pixel and every per-box number is Siril's (`boxselect`+`stat`, one load); in-house is the grid bookkeeping and the maximal-rectangle search. REPORTS ONLY — it writes an UNVERIFIED framing record and `verify_framing.py` decides; it crops nothing and exits 0 even when nothing clears the floor. `--selftest` falsifies the mechanism on a planted fixture: the planted frame is recovered exactly (FITS [160 100 480 250]), Siril's own `crop` re-reads it at Green Min 87.9 against an 80.0 bar with the box deliberately ASYMMETRIC in y so a flipped origin goes RED, and both known failure modes DO fail — the floor on the clipping channel covers 0 boxes, and a mere-non-zero floor grows the rectangle from 480x250 to 640x350 by swallowing the ringing band. It caught a real defect on its first run: Siril prints `Sigma: -nan` on a zero-variance box and the copied numeric-only regex silently dropped it (`docs/dead-ends.md`), a latent copy of which `starlight_preservation.py` also carried — fixed, and provably neutral there. The `--tag=` flag is a divergence only in the sense that arm builds need a work dir: without it an arm lands on the CONTROL's members and the resume guard then skips every group, so the arm looks built and IS the control |
| `member_separation.py` cross-match + zone medians | an official tool reports headless member-to-member POST-REGISTRATION positional residuals across a sequence (a scriptable Siril registration-residual map, or a PixInsight equivalent) | 2026-08-13 | **SELFTEST RUN AND PASSED, AND RE-RUN.** The L1 arm A build produced the sequence it needed: 13 members linked and `register -2pass` run over them (`sessions/aug06/work/l1_msep/in`), then `<seq-dir> --selftest` executed against those real members. Known displacement 3.086 px measured back as **3.086 px**; and the INCIDENT reproduces — **89 cross-matches without the re-basing against 1905 with it**, so the defect that made this instrument measure nothing still fires on demand. Re-executed 2026-08-13 on that same live sequence before the corner-quality work used anything of this instrument's: **both numbers reproduce to the digit**. **SCOPE THE ZONE NUMBERS CARRY, because they are the ones a reader reaches for:** they are member-to-member DISAGREEMENT in the reference member's frame under `register -2pass` homographies, which is NOT the delivered star shape of an astrometrically composed product and not a residual the shipped route leaves. On the 13-member aug06 union its T2 record reads 0.924 / 2.618 / 5.399 / 5.729 px (median over 78 pairs, centre/mid/outer/corner) while that product's own delivered major axis at matched member-own radius runs **0.04-0.25 px above its members'** and the radius trend is the members' own (`datasets/aug06/corner_work/`). Do not read one as the other. **not fired — REBUILT, and the rebuild found the instrument had been measuring nothing.** It cross-matched the REGISTERED copies, and `seqapplyreg -framing=max` on a variable-size sequence gives each output its OWN origin (MEASURED 611.9 px apart on the 28-member union; two members of ONE set shared 67 of 2000 stars within 12 px, 1721 once re-based). It now reads the members plus the homographies `register -2pass` wrote into the `.seq`, and bins by MEMBER-OWN field radius: 0/378 pairs unmeasured on that union against 378/378 before, in 12 s, with a monotone profile (0.22/0.48/1.30/2.43 px median). `<seq-dir> --selftest` executes the falsification against real members (a bare `--selftest` refuses loudly — it cannot run data-free, and exiting into the docstring read as a pass twice). **THE THRESHOLD LAYER IS REMOVED (user-ratified): no PASS/WARN/BLOCK, no `--accept-separation`, no exit-6 abort, always exits 0 — it MEASURES, it does not gate.** Three measured grounds: the quantity is a sum of two terms and the compose makes one of them (two healthy sets read 1.12 / 0.95 px composed among themselves and 3.02 / 3.38 px inside a 41° 28-member sequence); the bands were anchored on the broken instrument (anchors re-measured on the fixed one: 0.14 / 0.21 / 0.38 / 1.23 / 3.04 / 3.28 against 0.144 / 0.194 / 0.352 / 0.934 / 2.991 / 2.112, which moves the user-PASSED pair out of PASS); and a band fires on every real compose, which trains the operator to bypass it. **No threshold is to be written until the disagreement is attributed between the compose's global registration and the members' optical state (BACKLOG:`compose-homography-smear`) — this is a settled decision, not an open question to re-raise.** Original grounds unchanged: Siril `register` prints WITHIN-sequence residuals only; nothing reports where two members each place the same star. Built because the two prior instruments are MEASURED BLIND: corner `findstar` FWHM ranked a FAILING union (4.95 px) above the visually clean control (5.29 px), `seqtilt` read 0.34 px off-axis for the FAILING union against 0.40 for the PASSING one |
| optics/calibration FITS stamp (`header_provenance_lines`) + `backfill_substack_provenance.sh` | the warp stops being a TIFF round trip, so the model rides through natively (darktable gains FITS I/O, or Siril `register -disto=` — BACKLOG:`native-solve-and-sip`); the BACKFILL retires once no un-stamped sub-stack remains on any rig | 2026-08-09 | **not fired** — the warp is still Siril `savetif32` -> darktable -> Siril `convert`, which carries no FITS header. Load-bearing: the lensfun user DB is global, unscoped, single-valued machine state that nothing reverts, so a sub-stack that cannot state its own optics cannot be composed safely later — 13 aug06 members under 3 different models composed into a doubled union and nothing in the product could see it |
| `compose_preflight.py` + the compose's astrometric post-assert (`run_undistort_compose.sh`) | siril itself refuses to register a sequence whose members carry no usable solution, or the chain has no star-pair path left to fall back to | 2026-08-10 | **not fired — and it fires on today's corpus.** The union's own members (`groups_set-0*_pinned/sub_*.fit`) carry NO WCS, so the guard refuses them at exit 3. Grounds: `seqplatesolve` needs every member solved with SIP order >= 2 and siril reports NOTHING when they are not — it registers what it can and exports a finished-looking product. Measured cost of the silent fallback: roundness 0.458 against 0.974 on the 28-member union. Both halves are live-tested — refusal (exit 3) on unsolved members, acceptance plus "astrometric registration + per-member undistortion CONFIRMED" on solved ones, and `--selftest` falsifies the header checks |
| `solve_field.py` hint-contradiction gate (position > 2x the hint radius, scale outside +-20% of the header nominal; exit 9) | the solver itself refuses a solution that contradicts a supplied position/size hint — today the `astrometry` engine takes hints as search guidance only, and the blind fallback discards them entirely, so a hinted attempt that fails is followed by an unconstrained one whose answer nothing compares back | 2026-08-11 | **not fired, and it FIRES on the one measured false solve.** MEASURED: the corpus union's hinted attempt failed on a seam-contaminated framing=max canvas and the blind fallback shipped RA 6.03 Dec -65.10 at 12.96"/px, logodds 22.3 — against the product's own header pointing RA 309.77 Dec +41.70 (siril's WCS field centre, inherited from the already-solved members, so independent of this solve) and a 17"/px family. Nothing downstream could catch it: siril SPCC ran to COMPLETION on that WCS and produced plausible K factors (R 1.000 G 0.592 B 0.817, 1790/5153 stars kept). Thresholds are budgeted from mechanism, not fitted — integer-mm EXIF focal, XPIXSZ rounding, infinity-vs-marked focal and the TAN centre-to-corner ratio (1.066 at 28.6 deg) sum under 10%, doubled to 20%. Replayed over all 69 recorded solves: 1 refusal (the known-false one, on BOTH legs — 115.4 deg out and 0.740x) and 68 clean, real solves spanning 0.969-0.976 of nominal at logodds 103-574. SCOPE LIMIT: 53 of the 68 are per-member sub-stacks whose headers carry FOCALLEN/XPIXSZ but no RA/DEC, so only the scale leg and the logodds warning are live there |
| `route.py` `DRIFT_FRAC_MIN = 0.05` — the route key's floor | a MEASURED knee exists: an undistort-vs-homography A/B on this mechanism at two drift fractions below 0.25, closing where the removable term drops under the route's own irreducible residual (0.25 px off-axis aberration at full depth). The key itself (sky excursion / field) is mechanism-derived and does not retire with the floor | 2026-08-12 | **not fired — and the floor is EVIDENCE, not a knee.** No knee has ever been measured; the residual is monotonic in drift ("scales with TIME SPAN, not frame count"). 0.05 is the smallest excursion at which the term is measured present — the 9-min/~310 px window arm, `drift_frac` 0.051, whole-frame majFWHM 3.87 px against the full span's 4.74 px at 0.247. The corpus's 12 real sets measure 0.083–0.201, nearest 1.66x the floor, so nothing sits near it. The key UNDER-COUNTS twice (the `-framing=min` trim runs 1.16–1.29x the pure translation; a probe windowed inside the longest continuous run drops the re-aim excursion), which is why the floor sits at the bottom of the measured range rather than inside it. Fire-tested: flipping the constant moves all five consumers together and back (a same-length edit needs `__pycache__` cleared or importers read stale bytecode and the test reports a false "did not move") |
| `anomaly_audit.py` in-house streak kernel | a tool detects/classifies transient streaks | 2026-08-05 | **not fired** — probed siril 1.4.4's own command list: `cosme`/`find_cosme`/`find_hot`/`seqfind_cosme` are cold/hot PIXEL defect correction; no streak, trail, satellite or Hough command exists. Standing check: an extreme-elongation QA flag ADJACENT to an audited crossing is the same object until shown otherwise |
| `star_shape.py` two-frame duplication | Siril exposes a headless single-image tilt | 2026-08-05 | **not fired** — `tilt` IS listed by `help` but REFUSES in a script ("This command cannot be used in a script: tilt", probed on-rig). Siril cannot sequence one frame, so the duplication stands. A `help` listing is not evidence of scriptability |
| `star_stations.py` fixed-station `findstar` medians | a tool reports a headless LOCAL star-shape map | 2026-08-05 | **not fired** — `inspector` (the aberration-inspector grid, the closest native thing) also refuses in a script, probed the same way; `seqtilt` is centre-vs-corners and blind to the drift-aligned band this exists for |
| `shape_at_sky.py` sky-addressed `findstar` medians (the combined-product acceptance instrument) | an official tool reports headless star-shape statistics for a WCS-addressed subregion of a solved image | 2026-08-10 | **not fired** — same gap family as `star_stations.py`, at SKY positions instead of sensor stations: the compose-registration defect class lives at fixed sky on a combined canvas and no tool measures there headless. Every fit is Siril `findstar` (open gate), placement is header-only WCS, summarisation is medians of the tool's own numbers; box placement is VERIFIED per run by the tool's own per-star RA/Dec (the crop y-flip trap fired on first use and was caught by exactly that check). Calibrated against the recorded union A/B: reproduces 4.383/0.458 (defect) and 2.448/0.968 (control) to the third decimal on the kept reference |
| fitted lensfun entry, PINNED per lens/focal (`lens_models.json`) | an upstream lensfun entry measured for THIS unit at infinity focus, or a chain that consumes the model another way (Siril `register -disto=` with a trustworthy source — probed 2026-08-09, it is a SHARED-solution facility, not per-image reprojection, so it does not retire this) | 2026-08-09 | **not fired — and RE-INSTATED.** The 2026-08-08 retirement ("condition fired: the chain consumes the model another way — per-set optical-state records") is REVOKED: the per-set method was refuted at its root (`docs/dead-ends.md`) and reverted. Its founding number, aug06/set-01's 0.82 px off-axis, is a COMPOSE artifact — set-01's own groups read 0.40-0.45 px under that same pinned model. Per-set models broke the combine (2.99 px within a night, 5.34 px across nights) where one shared model composes clean and is what every accepted combine here ever used |
| lensfun user-DB strip of the fitted lens's `<vignetting>`/`<tca>` (`install_lens_model.sh`) | darktable honours a style's lens `op_params` | 2026-08-11 | **not fired — and no longer re-checked by hand.** `lens_preflight.py --require-profile` now runs `verify_lens_card.py` EVERY set (11.1 s of a 25.5 s preflight on 6064x4040 frames, so unconditional), because the strip is machine-local state `lensfun-update-data` reverts and the two cheaper checks are blind to it: reinstating the focal=70 aperture=4 `<vignetting>` pair by hand left the warp-happened proof and the pinned-coefficient assert both GREEN while the card read a 4219 ADU corner-vs-centre step on a 30000 ADU field (tol 1.0). Fire-tested both ways on aug06/set-01 (refuse -> re-strip -> 0.000 ADU). **NEVER RUN `install_lens_model.sh` WHILE A BUILD IS IN FLIGHT** — it rewrites the GLOBAL lensfun DB, which every live darktable warp is reading, so a QA or verification step that calls it mutates state a four-hour arm build depends on. Installing an IDENTICAL model still risks a torn read, and the DB is the one piece of unversioned machine state on the undistort route (nothing reverts it; `lensfun-update-data` wipes the strip outright). Caught live, no damage: a queued pin-verification was killed on firing and the DB verified after — all 56 XMLs parse, the fitted entry intact, no stale builder lock. Verify a pin from the build's OWN per-group output instead, which tests the model that actually ran rather than re-installing one. That test also found the restore path itself broken — the installer's idempotence test asked only about the distortion line, so it reported "already installed" and exited 0 on a block whose vignetting was back; it now re-strips and says so |
| per-set sky flat (`build_sky_flat.sh`, NOT de-skied) | a matching REAL flat for the set | 2026-08-12 | **not fired** — the flatless route, and it works: july31 sets measure 0.40/0.49/1.03/1.17% corner spread (a scratch rebuild from raws reproduced the experiments-ledger figures to the digit). The flat still converges to `sky x V`, so the object carries the sky's spatial profile — the MECHANISM is REAL and open, and NOT fixed by de-skying the source frames (`--desky` was a 31x regression; `docs/dead-ends.md`). **Its MAGNITUDE is UNMEASURED**: the long-quoted 3.11% / 241 sigma has no tracked record, and the catalogue-free re-measurement is now a registered DEAD END — the linear mode is degenerate under translational drift and the atmosphere is sensor-fixed for a fixed camera, so the pre-registered flat prediction failed 4 of 5 across 12 sets (`datasets/aug09/corpus_object_tilt.json`) |
| `object_tilt.py` cross-match + weighted LS of magnitude against sensor position (+ `object_tilt_control.py`, `object_tilt_null.sh`, `object_tilt_corpus.py`) | an official tool reports a headless POSITION-DEPENDENT photometric solution across overlapping exposures with no external catalogue — SCAMP's photometric mode is the candidate, or a PixInsight equivalent | 2026-08-12 | **not fired — and the divergence it fills is now known to be UNFILLABLE ON THIS DATA, which is why the code stays only as the record of that.** Probed: `scamp` has no apt candidate on this distro (`source-extractor` 2.28.2 and `swarp` do, and source-extractor runs on these sub-stacks — 47,971 objects in 3.1 s with `FLUX_APER` at two radii and `BACKPHOTO_TYPE LOCAL`); Siril's `seqpsf -wcs=` converts the sky coordinate to pixels ONCE and measures that same pixel area in every image (MEASURED: m = -2.104 in the reference block against +3.55/+5.05/+3.63 in the other three, and `-followstar` does not repair it without registration data), so no tool cross-matches a star across a drifting sequence headless. Every pixel op and every flux is Siril's (`findstar` + `psf` aperture photometry, forced radius, local annulus); the in-house part is the cross-match and the fit. It MEASURES and gates nothing — no thresholds, no verdict, always exits 0. `--selftest` falsifies its own mechanism in process (a pure-translation panel must NOT recover a planted +0.100 mag: it returns -0.046 +- 0.0001 and the lever collapses to 0.00 px; restore the rotation and the same code catches it again), and `object_tilt_null.sh` executes it on REAL data — interleaved halves, predicted tilt exactly zero, measured +49.1 +- 5.0% at 11.8 sigma |
| `flat_differential.py` subtraction + straight-line fit (+ `flat_differential_arms.sh`, `flat_differential_report.py`) and the two A/B flags on `run_undistort_pipeline.sh` (`--regdata=`, `--nonorm`) | an official tool reports, headless, the position-dependent photometric RATIO FIELD between two ALIGNED exposures — i.e. the subtraction and the fit, not merely two flux lists. `source-extractor` dual-image mode gives the two lists and is installed; it does not close this | 2026-08-12 | **not fired.** Probed: no Siril command compares two images photometrically by position (`fdiv`+`stat` gives the pixel field and IS adopted as the primary instrument, via the shipped `flat_odd_component.py`; `seqpsf -at=` is applicable on an aligned pair, unlike the drifting case, but measures one star per invocation from a selection — the same per-star call as `psf`, with an unvalidated parser). Every pixel op and every flux is Siril's (`split`, `findstar`, `psf` at a forced radius against its own local annulus); in-house is the subtraction of two tool measurements and a weighted straight line. MEASURES and gates nothing. `--selftest` falsifies the mechanism in process on the SAME pure-translation panel that killed the absolute measurement: the absolute fit returns **-0.046 ± 0.0001 with the lever collapsed to 0.00 px** where the differential returns **+0.0999 ± 0.0001 with a 1548 px lever**, and blinding the position axis turns step 1's own acceptance check RED, restoring it turns it GREEN. **The builder flags are NOT cosmetic**: `register -2pass` re-chooses the reference frame from image quality and the CALIBRATION changes that choice (MEASURED, one knob: skyflat_set-05 → reference image 1, canvas 4896x3616; skyflat_set-01 → image 2, canvas 4887x3641), so without `--regdata` an A/B has two knobs and the arms are not pixel-comparable. Default path unchanged by both flags; `--nonorm` stamps STACKNRM/DIAGARM on the product |
| `grid_ramp.py` least-squares plane over Siril `stat` box medians | an official tool reports, headless, the FITTED low-order background ramp of an image as NUMBERS — a slope or plane coefficients, not a subtracted image, not a background-model image, not a star-shape tilt | 2026-08-12 | **not fired.** Probed on this rig rather than reasoned about: siril `bg` returns ONE scalar for the whole image; `subsky`/`seqsubsky` fit a polynomial or RBF and SUBTRACT it, reporting no coefficients; `tilt`/`seqtilt` compute "the FWHM difference between the best and worst corner truncated mean values" — a STAR-SHAPE measure, not a background level (and `seqtilt` IS scriptable, so the GUI-sibling search was run, not assumed); GraXpert 3.0.2 `-bg` writes the background MODEL as an IMAGE; ASTAP CLI-2026.07.16 `-analyse`/`-extract` report HFD, star counts and per-star rows only. Siril measures every box median; in-house is the plane. Fills the instrument gap `docs/dead-ends.md` names — the grid-fitted ramp slope is the registry's CANDIDATE replacement for four-corner spread, which is "not a gradient measure on a structured field" — and it REPORTS ONLY: no thresholds, no verdict, and swapping an acceptance measure stays a user ratification. `--selftest` falsifies the mechanism in process: blinding the position axis drives a planted +0.15 %/1000px to 0.000000 and turns step 1's own acceptance check RED, restoring it turns it GREEN; a uniform card through the whole Siril path reads slope 0/0 (−7e-15) so LEVEL cannot masquerade as GRADIENT; and an ORDERING CONTROL re-measures the two extreme boxes in their own Siril invocations, since the 63–77 medians are parsed from one run in emission order |
| `starlight_preservation.py` per-cell floor vs Gaia catalogue regression on an external lattice | an official tool reports, headless, the AGREEMENT between a star catalogue's predicted diffuse surface brightness and an image's own measured per-region background — the JOINT, not the two halves | 2026-08-12 | **not fired.** Probed on this rig, each with the command run rather than the help read: Siril `stat`/`bg`/`bgnoise` measure the image only (`bg` is one scalar for the frame) and `conesearch` returns the catalogue only — and at this field size it is not even usable, 20.6 deg radius at G<=17 against TAPVizieR, killed at 600 s with no output; `jsonmetadata -stats_from_loaded` ignores a selection and stats the whole frame; `source-extractor` 2.28.2 `-CHECKIMAGE_TYPE BACKGROUND` writes a local background MAP (1.7 s on 4907x3598) but compares it to nothing; GraXpert 3.0.2 `-bg` writes a background MODEL image; ASTAP CLI-2026.07.16 `-analyse`/`-extract` report HFD, star counts and per-star rows. Every pixel and every per-cell number is Siril's (`boxselect`+`stat`, PROBED identical to the `crop`+`stat` route to every printed digit in ONE load); the catalogue aggregate is the ESA Gaia archive's own server-side GROUP BY; in-house is the lattice, the WCS projection and the fits. MEASURES and gates nothing — no threshold, no verdict, always exits 0. `--selftest` falsifies the mechanism in process on a planted fixture: 299.14 recovered against 300.00 planted at R2 0.99993, an orthogonal predictor returns R2 0.00017, Siril `subsky 2` collapses the planted relation to 26.9% (RED) and the pristine copy re-reads 299.14 (GREEN); a catalogue control checks the archive's binned sum against its ungrouped total (agree to 1e-6) and the plane/pole flux contrast (6.3x). It caught a real defect on its first run — `boxselect` counts y from the TOP, and the mirrored lattice still recovered 54% of the planted relation at R2 0.30, which is exactly the kind of half-right number a fixture-free instrument would have shipped |
| GraXpert `-correction Division` synthetic flat | a matching real flat exists | 2026-08-05 | **not fired** — not adopted; no pipeline script calls it. Vignetting-only fallback |
| `baseline_guard.py` derived summaries (corner spread, edge dipole) over Siril `stat` | a tool reports a headless PRODUCT-level regression verdict against a stored reference | 2026-08-05 | **not fired** — nothing does. WIRED into `run_set_chain.sh` as the last step: it measures the finished product, and a regression exits **8** (a user decision, like the mount/route stops) without blocking or rewriting anything. Also a web stage for seeding/re-seeding. It is a no-regression RECORD, never a quality gate — a deliberate improvement fails it and the human re-seeds with a note. Blind spot to state when reading a PASS: both measures are STACK corners, which `docs/dead-ends.md` calls self-fulfilling for flat contamination, so it cannot see the open `sky x V` object tilt |
| `snr_regions.py` in-house SNR ratio over Siril `stat`/`bgnoise` | a tool exposes headless REGIONAL SNR | 2026-08-05 | **not fired** — `stat` and `bgnoise` are whole-image/selection; no regional-SNR command in 1.4.4. Every input number is the tool's; only the ratio is in-house. *(Was missing from this register until 2026-08-05.)* |
| `fingerprint.py` derived trail/drift geometry | an official tool reports headless trail/drift geometry with a declared-vs-measured mount cross-check | 2026-08-05 | **not fired** — no solver here exposes inter-epoch drift rate vs sidereal. The record schema and the STOP-on-CONTRADICT contract stay wherever it lands. *(Was missing from this register until 2026-08-05.)* |
| `inspect_stage.py` + `cull_report.py` robust-z per-frame flagging | a tool ships headless per-frame outlier flagging over its own registration metrics (SubframeSelector-class, scriptable) | 2026-08-05 | **not fired** — siril has `seqstat` (per-frame statistics to a file) and `select`/`unselect`, but no outlier GRADING over its own regdata. Persisting the tool's regdata is not a divergence and stays regardless. *(Was missing from this register until 2026-08-05.)* |
| prebuilt-master ingest (`run_pipeline.sh` `<session>/calib/`) | never — this is a supported INPUT class, not a divergence | 2026-08-05 | **CONDITION WRITTEN 2026-08-05, previously absent.** The code calls it "the adaptation for master-only data", which made it look like an unconditioned divergence. It is not one: a corpus that ships masters instead of raw calibration is a data class the repo accepts. What IS a stated limit: such masters carry no exposure/gain/filter headers, so the filename token is the whole identity and the exposure match is unverifiable — printed per run. Raw calibration dirs take precedence |
| 16-bit in four instruments (`coverage_probe.sh`, `run_frame_qa.sh`, `fit_lens_model.sh`, `run_lunar_pipeline.sh`) | the leg stops terminating in an integer/8-bit product | 2026-08-12 | **not fired** — each re-verified: `coverage_probe` switches to `set32bits` before its sum stack, `run_frame_qa` saves no product at all (analysis-only register), `fit_lens_model` terminates in `savetif8` for Hugin, `run_lunar_pipeline` pins it on its convert+seqcrop stage step only. Exemptions are enforced by name in `check_bitdepth.sh`, which reports FOUR |
| `run_undistort_groups.sh` group composition (one extra interpolation pass) | a measured quality cost of the extra pass at established magnitude (the along+1300 ledger resolving AGAINST groups), or cross-set composition leaving the project's goals | 2026-08-06 | **CONDITION REWRITTEN — the old trigger (free disk ≥ the single-pass peak) fired and was judged the WRONG condition: disk cannot retire groups.** Single-pass deletes the sub-stacks the cross-set combine composes and crops to `-framing=min` (composing per-set finals is a registered dead end), so a big disk buys nothing back; groups is the STANDING route (`force_route`), single-pass operator-only (`--route=single`, printed FORCED). Quality, two consistent accounts: the item-scoped one-knob A/B (60 frames even-stride) is **NULL — the route does not cause the one-sided band** (9/9 stations within 0.05 px majFWHM / 0.014 roundness; the band sits in BOTH arms at 1.27x/1.24x); the full-depth ledger records a small along+1300 improvement UNDER groups (0.12–0.18 px, direction replicates across two sets and two group sizes) whose proposed baseline mechanism was FALSIFIED (g250 landed outside the interval) and whose magnitude is UNESTABLISHED until the pre-registered `rebuild_repeat_floor_set01` runs (`datasets/july31/experiments.jsonl`). Peak math stays data-dependent, `W × H × channels × 4 × 2`: 560 MiB/frame at 6064×4040 OSC, 8 MiB mono astrocam, 1378 MiB at 61 MP |
| `scripts/lib/siril_run.{sh,py}` flock-serialized siril-cli invoker | flatpak fixes the instance-dir lifecycle race, or Siril invocations stop being per-frame process spawns (e.g. pyscript batching) so there is no window to collide in | 2026-07-28 | **not fired** — the race is a flatpak lifecycle bug, unfixed at 1.4.4/current flatpak, and every builder still spawns one siril-cli per step. MEASURED serializing: 4 concurrent jobs 1.74 s vs 0.47 s single (3.7x, matching serialized 1.88 s not concurrent 0.47 s), 3 of 4 reporting the wait; shell and python share ONE lock (cross-language test 0.93 s = 2x single). The lock is per-USER so it serializes across sessions on this rig. Every participant is now adopted: the one hold-out (`scripts/jwst/*`) went with the JWST cut, so `check_siril_invoke.sh` carries no exemption and any bypass FAILS rather than being reported |
| `scripts/stack/stamp_headers.sh` — capture + `update_key` restore of the acquisition keys the undistort warp drops | the warp stage stops being a TIFF round trip: darktable gains FITS I/O, or the distortion is consumed natively (Siril `register -disto=`, BACKLOG:`native-solve-and-sip`) so the keys are never dropped | 2026-07-28 | **not fired** — darktable 5.4.1 has no FITS reader, so the warp leg is TIFF and the loss is structural. Values are Siril's own (read from the raw into the calibrated frame's header); in-house code only READS the header and hands them back to `update_key`. LIVETIME is the one derived value (n_frames × EXPTIME, both tool-sourced) because the per-frame EXPTIME Siril would sum was destroyed upstream. MEASURED restored on july27 set-01: 9 keys, LIVETIME 789.0 s = 263 × 3 s, and the solve regained its hint (`scale hint: 10.5-26.3 arcsec/px`, index scales 11-19, vs the prior blind WIDE-FIELD fallback) |
| 5-set combine via TWO interleaved-half composes + a 2-member `-weight=nbstack` join (the 107-sub single-registration max compose needed ~37G transient vs ~24G reclaimable on the previous rig) | x86 disk → re-compose all 107 sub-stacks in ONE registration (every `groups_*` dir is kept for exactly this) | 2026-08-06 | **condition MET on this rig (950 G free, per the groups-row measurement) — the re-compose has NOT been run**, so the divergence stands in every shipped product until it is. Declared cost while it stands: the non-reference half carries one extra interpolation; halves span all five sets (interleaved), STACKCNT propagates exact frame weights (794+781=1575); the join landed natively in the cov25 orientation family. The 5-member per-set-stack shortcut is a measured dead-end (pre-cropped members — registry) |

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

Ordered work — nothing here is executed on an accepted product:

1. ~~Reference pinning~~ and ~~the SWarp trial~~ are RESOLVED: the compose
   registers all members in one sweep with the reference setref-pinned
   (deterministic level anchor), and per-image astrometric resampling is the
   ADOPTED route (`seqplatesolve` + `seqapplyreg`, each member's own solution
   and SIP — the SWarp-class operation natively; corpus defect position
   measures 0.980 roundness, clean-band level). The remaining work below is
   the OPTICS term, which no registration reaches.
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
stars drift OUT of — Siril's own homographies give −3.87 px/frame across the sensor,
and it is the exit edge that smears. At matched distance from the sensor centre that
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
| shake / wind gust | per-frame FWHM + roundness spike; elongation angle off the trail axis | metrics exist, the ANGLE is unused, no test |
| cloud | background level and its rate of change — star COUNT is measured blind on rich fields (detection saturates at the cap) | per-frame background is NOT recorded |
| light pollution / moon | background gradient magnitude + bearing (the odd-plane term tracks the moon's bearing to 23 deg) | measured once ad hoc, no script |
| transparency drift within a set | the STARS' own throughput gradient, block to block — `object_tilt.py`'s per-block gradient term measures a within-set drift of **0.040–0.425 mag across the frame (median 0.149), MONOTONE in block order in 10 of 12 sets**, from Siril aperture photometry on matched stars | MEASURED as a by-product of the object-tilt dead end (`datasets/aug09/corpus_object_tilt.json`); it is a real per-block transparency signal this surface does not otherwise have, and unlike background level it is measured on the OBJECT's own flux. No per-FRAME form — the instrument works on sub-stacks |
| file inconsistency | per-frame mean/median step, EXIF constancy, truncation | not built |
| optical-state change mid-set | geometry residual step (BACKLOG:`compose-homography-smear`) | member-level only; no per-frame form |

Design constraints, each from a measured failure here:

- **Measure once.** One per-frame table, every column a tool's number, written at
  intake and never re-derived — so a different cull replays without re-measuring.
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
  cost of the collision, so the choice is made against numbers: a one-sided +x
  member trim keeping 80% of each member leaves 4 of 20 measured union boxes
  with no contributing member at all; a radial cut to rho 0.80 costs 3.3% of the
  delivered crop's area and 9.4% of the member-contributions inside it
  (`datasets/aug06/corner_work/`). The composite-level arm
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

## `learned-deconvolution` — unmeasured, and the tool is installed

`render_tier.sh` skips deconvolution on three grounds that all hold — classical RL is
a measured dead end on in-exposure trailing, BlurXTerminator is not installed,
GraXpert's is the immature path. The fourth was never checked:
`/opt/cosmicclarity-6.6` ships `SetiAstroCosmicClarity` with
`deep_nonstellar_sharp_cnn_radius_{1,2,4,8}`, beside the denoiser the tier already
drives, and the registry explicitly does NOT dead-end a learned deconvolver.

The mainstream runs deconvolution with stars PRESENT, so it goes before the
separation. **Test:** one knob, non-stellar sharpen on the linear SPCC stack vs none,
bracketed by a same-arm repeat, judged on `star_stations.py` majFWHM per station +
`seqtilt` + the user's eyes at 1:1. The hypothesis under test is OBJECT detail — a
symmetric sharpener cannot de-trail an elongated PSF. Until it runs, the skip is a
hypothesis and the docstring says so.

## `calibration-evidence` — the de-sky work's unfinished evidence

**`--desky` is off by default; it was a 31x regression
(`docs/dead-ends.md`). The grounds it shipped on (flat odd plane 4.84%→1.98%
set-01, 7.82%→2.42% set-02; vignetting held ≤0.12%; PRNU correlation 0.999951)
were all measured with instruments blind to the failure: the odd plane is a
whole-frame fit that CANCELS under a partial sign inversion, and "vignetting held"
was a centre-vs-corner radial ratio that averages the two sides together.**
The underlying problem the work was aimed at is still real and still uncorrected —
a sky flat converges to `sky x V` and tilts the object. These
evidence gaps therefore remain open for whatever the eventual fix is:

- ~~**The 3.11% / 241-sigma figure itself has NO TRACKED RECORD.**~~ **CLOSED, as
  UNVERIFIED — and the re-measurement is a DEAD END.** The figure is now marked
  unverified at all 13 code and doc sites plus the 13 `readiness.json` records
  (the generator, `readiness_report.py`, was the real site — the JSONs regenerate
  from it). The catalogue-free re-measurement the brief specified was BUILT
  (`scripts/qa/object_tilt.py`, Siril `findstar` + Siril `psf` aperture photometry
  at a forced radius against its own local annulus) and does not reproduce it, for
  two independent reasons either of which is fatal:
  **(1) GEOMETRIC.** A linear sensor-fixed mode is EXACTLY absorbed by the
  per-star and per-block nuisances under a pure translation, so the 503-1220 px of
  drift is not the lever — the FIELD ROTATION is, and it is only 0.69-3.76 deg per
  set, leaving a median effective lever of **29.1 px on a 5769 px frame (0.5%, a
  ~200x extrapolation)**. `--selftest` executes the falsification: a planted
  +0.100 mag returns as **-0.046 +- 0.0001** on a pure-translation panel, so a
  degenerate fit reads confidently WRONG rather than unidentified. Read the lever,
  never the sigma.
  **(2) PHYSICAL, and it survives any fix to (1).** For a FIXED camera every
  sensor position maps to a fixed altitude, so atmospheric extinction and skyglow
  across this 27-degree field are sensor-fixed TOO, and both are airmass-shaped —
  nearly the same spatial shape as the flat's baked-in sky term. The fit measures
  their SUM. The time-varying half is MEASURED: a within-set gradient drift of
  **0.040-0.425 mag (median 0.149), monotone in block order in 10 of 12 sets**,
  whose leak into a shared-gradient fit (0.74-13.45 mag) exceeds the measured
  shared gradient in every set.
  **The instrument is sound and the controls say so**: a Siril `imul` ramp of edge
  ratio 1.2222 recovers at 1.24x (0.95x on the best-levered pair) and a uniform
  card moves every number by exactly 0.00. What fails is the DATA'S GEOMETRY, and
  the discrimination number says so: the planted ramp moves the answer 9.85 points
  against a floor of 49.08 — **0.20x**, where the iterative-flat NULL met 48-62x.
  **The floor is 49 PERCENTAGE POINTS**: aug09/set-01 rebuilt as interleaved
  halves (249 even frames against 249 odd) has a predicted tilt of EXACTLY ZERO —
  both products average a star over the same sensor positions — and measures
  **+49.08 +- 4.97% at r=10 and +50.82 +- 5.65% at r=16, 3086 stars, 11.8 sigma**.
  A floor the size of the measurement, read at high formal significance, is the
  same lesson `--selftest` 4a teaches: read the lever, not the sigma.
  **The pre-registered corpus prediction failed 4 of 5** — every set exceeds its
  flat's own dose by 1.4-86x, and aug06/set-03, the pre-registered built-in null,
  measures +223 +- 28% against a predicted +2.6%. Numbers:
  `datasets/aug09/corpus_object_tilt.json`,
  `datasets/aug09/tilt_corpus_prediction.json`, `docs/dead-ends.md`.
- ~~**The odd-component instrument has no script.**~~ **CLOSED** —
  `scripts/qa/flat_odd_component.py`. Siril does every pixel op (load/crop/fdiv)
  and every measurement (stat); it reports LR / TB / corner ratio / both edge
  dipoles at the two geometries already in use, and `--ratio B [--control]` does
  the flat-vs-flat division that cancels vignetting and the instrumental base
  exactly (`fdiv` only — `idiv` clips at 1.0 silently; the two-scalar control is
  built in). It REPORTS and gates nothing, per the note below.
  **What it found, which changes what a fix may assume:** the LEFT-RIGHT odd
  component is SKY (monotonic within all three nights, edge dipole sweeping
  +0.436 → 0 → −0.385 across the corpus, impossible for a sensor-fixed term) —
  but the TOP-BOTTOM term is **not** demonstrably instrumental either, since it
  sits above 1 on july31 (drifting +6.7% through that night) and below 1 on
  aug06/aug09. Neither axis isolates the instrument, and the
  constant-within-a-night part stays unattributed between optics and static sky.
  Numbers: `datasets/aug09/corpus_flat_odd_component.json`,
  `datasets/aug09/experiments.jsonl`.
  Still open from this bullet: `build_sky_flat.sh`'s built-in gate remains
  corner-vs-centre, which the registry calls SELF-FULFILLING for this defect.
  The builder does now record both edge dipoles alongside it, so the honest
  statement is that the gate under-claims rather than lies — but it should stop
  claiming to check what it does not.
- **Which arm is CORRECT rests on estimator arithmetic, and the catalogue-free
  test that was supposed to settle it is now a DEAD END.** The Gaia check is
  structurally impossible (trailed stars at 17″/px), and "measure the same stars in
  consecutive time blocks and fit flux against sensor position" was BUILT and RUN
  over all 12 sets: the linear mode is degenerate under the drift's translation, the
  1–3.8° of field rotation leaves only a 29 px median lever, and the atmosphere is
  sensor-fixed for a fixed camera so nothing in the sensor frame can apportion the
  measured field between flat and sky. Do not re-propose it (`docs/dead-ends.md`;
  `datasets/aug09/corpus_object_tilt.json`).
  ~~**What is still available to settle it:** (a) the FLAT DIFFERENTIAL…~~
  **(a) IS DONE — WIN with controls, and it changes what a corrective may assume.**
  Two flats of the same optical state and different sky dose (aug09 set-01 vs
  set-05, Δedge dipole 0.2827) on the SAME 125 set-05 lights, one knob.
  **Delivered: −22.477 ± 0.077% object-flux tilt (r = 10 px, 914 stars, Siril
  `psf`) and edge dipole_x −0.2356 on the pixel-ratio field (Siril `fdiv` +
  `stat`).** The apples-to-apples form needs no model — the flats' OWN ratio
  cropped to the delivered canvas measures −0.2383 (edge) / −0.2010 (corner)
  against the delivered −0.2356 / −0.2021, i.e. **98.9% and 100.6%**, and 101.2%
  after correcting by the planted card's own 97.7% recovery through the same
  comparison. **The transfer from flat SHAPE to delivered object is ~1:1 with no
  measurable attenuation.** Floor EXACTLY 0.0000 on both instruments (the
  non-vacuous uniform-card version changes 74.10% of the pixels and still moves
  no dipole), so discrimination is unbounded where the object-tilt instrument
  managed 0.20x. Both blockers die structurally: `M_i` cancels identically, so the
  lever is 1603 px against the absolute measurement's 29.1 px median, and the
  sensor-fixed atmosphere cancels in the subtraction — demonstrated on the SAME
  pure-translation panel that killed the absolute design.
  **The shipped normalization absorbs 0.3% of it**, so nothing is hiding the
  defect; the same pair moves the BACKGROUND dipole +48.6% as a pedestal artefact,
  which is why the pixel field is read on `-nonorm` arms only.
  **SCOPE — it does NOT close "which arm is correct".** A ratio cancels what the
  two flats share, so the absolute tilt still needs the flats' COMMON sky content,
  which is unmeasured; this gives the transfer function, not the level.
  Numbers: `datasets/aug09/flatdiff_prediction.json` (committed before the arms),
  `datasets/aug09/set-05/flatdiff_work/flat_differential.json`, `docs/dead-ends.md`.
  (b) `flat_odd_component.py --ratio` is what the primary instrument invokes.
- **A with/without judgement pair on finals** — the metric is unresolved-starlight
  preservation and the user's eyes decide. **NOT stageable as originally written:
  the de-skied flats it named for set-01/02 no longer exist on disk** (verified),
  and the de-skied arm is a registered 31x regression regardless. The pairing that
  IS stageable is two shipped-builder flats of different sky dose — within-night,
  so the optical state is fixed; aug09 set-01 vs set-05 is the corpus maximum at
  Δdipole 0.2827. Blocked on the render gate: `render_tier.sh` exits 7 without a
  ratified `render` block (BACKLOG:`render-ladder`) — re-verified.
  **THE ARMS NOW EXIST AND ARE PRESERVED, so only the gate is left.** The flat
  differential built both, 125 frames each, registration pinned so the ONE knob is
  the flat: `sessions/aug09/work/flatdiff/arm_A.fit` (skyflat_set-05) and
  `arm_B.fit` (skyflat_set-01), linear, plus the production-normalization pair
  `arm_An.fit` / `arm_Bn.fit` — which is the pair to judge, since the eyes pass
  must see the SHIPPED normalization. Each carries its own tag on the FITS
  (`DIAGARM`, `CALXSET`, `STACKNRM`, `REGPIN`), so a diagnostic arm cannot be
  mistaken for a deliverable months from now. What the eyes are for: the delivered
  difference is MEASURED at −22.5% of object flux across the frame, so this pass
  is no longer "is there a difference" but "which arm preserves unresolved
  starlight", which no instrument here decides.

**ROUTES NOW CLOSED — do not re-derive them.** The DOMAIN-CORRECTED ITERATIVE
SKY FLAT (calibrate the flat's source frames with `F0`, `seqsubsky` in that
flat-fielded domain, restore the level, multiply back by `F0`, restack) is DEAD:
it reconstructs whichever flat it is handed, because dividing by `F0` is what
removes the gradient from the sky and multiplying back restores it. Measured
NULL against positive controls that move the same code 81.7% (fixture) and 93.4%
(real data) where the scheme moves it 1.7% / 1.2% (`docs/dead-ends.md`). It repaired `--desky`'s domain error and still
could not work, so "run the operator in the right domain" is exhausted as an
angle. No builder flag was added and no removal-conditions row created — there
is no divergence to retire.

Related and open: **SPCC order-robustness is UNTESTED, not verified.** Inserting the
background step ahead of SPCC moved K_G −1.20%/−1.48% and K_B −0.47%/−0.80% on
unchanged star counts — larger than the chain's own recorded K scatter (0.006).
Confounded, because the de-skied arm also removes a real ~3% object tilt. Clean test:
SPCC the SAME stack with and without an on-stack background step only.

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
- ~~**Then Siril-native SIP undistort vs the darktable warp.**~~ **RUN —
  REFUTED AS INVOKED, and two beliefs corrected on the way.**
  (a) The precondition is MET for MEMBERS: `seqplatesolve -order=3` solved both
  aug06 members natively, 388/371 matched stars, residual sigx/sigy ~0.9 px,
  centres agreeing with astrometry.net to 0.001 deg. The "Siril cannot solve this
  class" belief was measured on single ULTRA-WIDE TRAILED frames and had widened
  past its evidence — stacked members have round stars.
  (b) But `register -disto=` is a SHARED-solution facility, not per-image
  reprojection: each member undistorted by its OWN SIP then composed measured
  3.99/6.42/6.19 px against the shipped route's 0.29/0.63/2.10/2.99, and ONE
  member warped by its own solution disagrees with its own unwarped self by
  8.50/9.45/6.76 px. The polynomial cancels only when every member shares it —
  so Siril's own design assumes ONE optical state per sequence.
  (c) The stated acceptance measures here (`seqtilt` off-axis + drift-axis
  stations) are both MEASURED BLIND to the star-doubling defect
  (`docs/dead-ends.md`); the re-run used `member_separation.py`.
  SUCCESSOR, unmeasured candidate: the industry operation is resampling each
  exposure onto a COMMON output WCS using its own full solution (CD matrix AND
  distortion) — SWarp's model, the SDSS/CFHTLS/DES/Pan-STARRS lineage. Nothing
  installed does it; SWarp is packaged for this distro at 2.41.5-3, python
  `reproject` is absent. The route is BACKLOG:`compose-homography-smear`.

## `one-sided-band` — two mechanisms left on the residual drift-axis term

MEASURED on july27 (3 s subs, so the in-exposure trail is half july14's and no
longer masks it): a one-sided along-drift band at the +1300 station only — set-02
majFWHM 3.65 / roundness 0.684 against centre 2.56 / 0.901, elongation position
angle (+4.3°) aligned to the drift axis; the −side and both perpendicular stations
sit at the centre's floor. ELIMINATED:
- **the optics and the sky** — a single RAW frame (no calibration, warp or stack)
  is uniform across the field (0.712–0.810, +1300 marginally BETTER than centre),
  so nothing in-exposure produces it;
- **the lens correction misfiring** — `verify_lens_card.py` PASSES on this rig
  (grid control fires, Siril sigma 45644.8; uniform card corner-vs-centre
  0.000 ADU), and the community entry carries vignetting the fitted one does not,
  so a zero photometric delta proves the FITTED distortion-only entry is the one
  matching despite the EXIF string matching the community entry's capitalisation;
- **the stack architecture** — the july27 route A/B returned NULL: the band sits
  in BOTH arms at the same magnitude (register, groups row). The july31
  full-depth ledger adds a small groups-side improvement at the same station
  (0.12–0.18 px), mechanism unattributed and magnitude gated on the unmeasured
  rebuild floor (`datasets/july31/experiments.jsonl`) — a modifier of the band,
  not its driver.

REMAINING: distortion-model residual vs differential refraction. The named
discriminator is unchanged (hour-angle dependence: refraction varies with it, a
model residual does not) and has two same-night sets 30 min apart at different
pointings — set-01 reads a 13% along+1300 FWHM excess, set-02 43% — suggestive of
refraction but confounded by the pointing change. Cheapest next cut: a `lensdist`
vs `nodist` arm on the same 60-frame A/B input, which separates the model from
everything else in one knob.

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

## `calxset-names-the-wrong-axis` — a provenance flag that overclaims

`run_undistort_pipeline.sh` stamps `CALXSET=T` whenever `--flat` is not the flat
the set's record names. The trigger is right; the NAME is not. It reads
"cross-SET calibration", and the per-group flat arms are cross-WINDOW **within
one set** — a later reader would take those members for another set's
calibration. Nothing is lost today: `CALFLAT` records which flat actually ran and
is authoritative for which case it is.

**Do NOT rename the key** — products already carry it and a rename strands every
one of them. **Closes when** the definition site states the real trigger
("`CALFLAT` is not this set's recorded flat", covering cross-set and
cross-window alike) and names `CALFLAT` as the datum that says which. Found by
header inspection during the per-group flat arms; the fix is held off the build
path while an experiment is in flight.

## `guards-and-ci` — nothing runs the guards

`check_bitdepth.sh` says "run it in CI / before a release" and no runner exists; the
web session smoke test added to it inherits that, and so does
`check_registration_pins.sh` (the newest of the family — `-transf=`/`-interp=` pins,
per COMMAND, with a `--selftest` that falsifies its own rules). **And one guard cannot be run at
all: `scripts/stack/check_stack_rejection.sh` is mode 664**, so `./scripts/…` is
permission-denied and only `bash scripts/…` works — a guard that fails to execute
is indistinguishable from a guard that passed, which is this repo's most persistent
defect shape. Also open: the bit-depth check is
per-FILE, so a builder that already emits `set32bits` in one generated `.ssf` passes
even if a newly added emission omits it — per-block granularity needs the
printf/heredoc blocks split on the `> "$X.ssf"` boundary every builder here uses.
Deferred deliberately: a fragile parser is worse than a stated limit, and the limit is
printed in the guard's own OK line.

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

## `parallel-session-staging-unit` — "stage explicit paths" does not protect a shared FILE

**OWNER DECISION — a proposed `CLAUDE.md` amendment, not made here.** `CLAUDE.md` is
the owner's file and a peer message is not the owner's approval; this item states the
measured gap and the proposed wording for the owner to accept or reject.

**The contract's rule was followed and the hazard fired anyway.** The parallel-sessions
clause says *"Stage explicit paths — NEVER `git add -A`"*, and its stated mechanism is
that `-A` sweeps a peer's unrelated files. MEASURED here: a peer staged **one explicit
path** (`BACKLOG.md`, named in its own commit message) while this session had two
uncommitted edits in that same file — a `removal-conditions` row and a
`single-pass-reference-lottery` replication. Both were published inside commit
`0a016e2` under that peer's message and authorship, undescribed by it. 17 insertions
landed where the commit message accounts for one row.

**The unit of contamination is the FILE, not the pathspec form.** `-A` is one way to
sweep a peer's work; naming a file both sessions have edited is another, and the rule
as written does not cover it. Nothing was lost — no duplication, both rows verbatim,
guards pass — so the cost here was attribution, not content.

**And the detection asymmetry is the same one the clause already records for `-A`:**
the loser's `git status` simply goes clean, which reads as *"I imagined that edit"*
rather than *"someone committed it for me"*. It is only visible via
`git log -S'<phrase>' -- <file>`, which nobody runs unprompted. **The only reason it was
caught here is that the committing session NAMED the file in its message to the other**
— which makes "say what you committed" a load-bearing practice rather than courtesy: it
is the sole signal the losing side gets. Without it the rows would have been re-added on
top and produced exactly the silent duplication the fourth hazard describes.

**Three candidate wordings, owner's choice** (the second and third are the committing
session's, and it argues them from having hit the trap while believing itself compliant):

1. Before committing a file, `git diff --stat -- <file>` and check the diff is only
   yours; if a peer has uncommitted work in it, `git add -p` your own hunks or hand
   over the wording.
2. Stronger, because in a long session the failure mode is not *seeing* a foreign hunk
   but *mistaking one for your own*: `git diff -- <file>` and account for EVERY hunk
   before staging.
3. Structural, removing the per-case judgement: if `ListAgents` shows a live peer in
   this repo, treat every shared record file as contested by default.

**Closes when** the owner accepts, rejects or rewrites one of them.

**A SECOND, SEPARATE `CLAUDE.md` PROPOSAL — the parallel-sessions clause states what
the practice caught and never states where it is blind.** It currently says parallel
sessions are supported, cites two findings that changed what a running session
measured, and lists four hazards. All true. But a rule that advertises its successes
without its failure mode gets over-trusted, and the failure mode is now measured: a
second session catches errors by applying different PRIORS to the same tree, not by
holding different evidence — so it is blind wherever both sessions share the prior,
which is most of what any two sessions agree about. Across the L1 build/audit pair,
not one correction on either side came from shared ground. **Proposed sentence**, to
sit with the four hazards: *two sessions agreeing is not evidence — it is the region
where this practice is blind, and it is the larger region.* The mechanism and its
three worked instances are registered in `docs/dead-ends.md` (QA / scope) either way;
this proposal is only about whether the LIMIT is stated where the practice is
authorised. **Closes when** the owner accepts, rejects or rewrites it.

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
