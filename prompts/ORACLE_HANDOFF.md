# Oracle handoff

**PROMPT-KIND: register**

**REPLACES the previous `ORACLE_HANDOFF.md` in full.** The name carries no
engagement number, deliberately — three handoffs would be three places for one
fact to drift. **The next Oracle REPLACES this file; it does not add to it.**

**Read `prompts/ORACLE_TEMPLATE.md` first — it is the role.** This file carries
only what a document cannot: searched negatives with what was actually looked
at, which of my claims are inference rather than measurement, the refs that make
external claims re-derivable, and my errors.

**NOT HERE ON PURPOSE: my engagement's findings.** Eleven landed in the tree
across seven commits — `TOOLS.md`, `docs/dead-ends.md`, `BACKLOG:one-sided-band`,
`docs/combine-contract.md`. Read the tree for them. Anything restated here would
be a second home for a fact that already has one.

---

## 1. SEARCHED AND EMPTY — DO NOT RE-RUN

Each closed something by being empty, and each cost real tokens.

- **No source prescribes a superflat's pointing spread as an absolute sky angle,
  or as a fraction of the field width.** Looked at: THELI GUI §9/§15/§18; Erben
  et al. 2005 §3.2–3.9; Sharon et al. 2007 §II.2.2; Bernstein et al. 2017
  §II.3/§III.4/§III.6; Pan-STARRS §III.4; AutoWISP §2.1; von der Linden et al.
  2014 §3.1.2; IRAF `ccdred`/`quadred` flatfields plus `mkskyflat` /
  `mkillumflat` / `mkillumcor`. **Every spread requirement found is RELATIVE** —
  to object size, to CCD gaps, or to the range of spatial scales being solved
  for.
- **No source gives a rule for MIXING observing conditions inside one
  superflat.** Every source that addresses it splits the stack by condition or
  rejects frames.
- **No source recovers a position-dependent instrumental throughput from
  sky-derived stellar photometry on a camera fixed in the HORIZON frame**,
  without a lab flat, an external anchor, or a Bouguer slope in time. Looked at:
  SDSS ubercal §II–III; DES FGCM §III–IV; DECam detrending; Evryscope;
  Pan-STARRS §III.4; the all-sky camera literature.
- **FGCM never discusses the instrument/atmosphere degeneracy** — it asserts the
  factorisation. Worth knowing, because it is the paper someone reaches for as
  authority that the two separate.
- **The Ali Observatory all-sky paper describes NO flat-field or vignetting
  procedure**, and makes no statement about separating vignetting from
  extinction on a fixed camera.
- **No source bounds how the underfitting / ellipticity-gradient bias VARIES
  with a blend's orientation distribution.** Bernstein 2010 gives magnitudes at
  named configurations only. Two near-misses that do NOT transfer:
  arXiv:1707.01285 §3.5 (galaxy shear bias under a PSF swap) and GREAT10's
  *"additive shear biases depend linearly on PSF ellipticity"* (shear bias
  against PSF ellipticity, not shape bias against blend composition).
- **Nothing characterises CLAMPING on an anisotropic or motion-blurred
  feature.** Third empty result in that family.
- **The elapsed time of a DECam star-flat sequence is not stated** in the
  sources read — so whether the atmosphere is constant across it is
  unestablished.
- **PixInsight's `ImageWeighting` and `SubframeSelector` reference docs return
  HTTP 403.** **ACCESS-negative, not existence-negative** — `TOOLS.md` cites the
  first, so it was reachable from somewhere, and PixInsight is uninstalled here
  by choice so there is no local copy. Two clauses in the intake-culling finding
  are SECONDARY until someone with access confirms them verbatim.
- **NOT READ, named so nothing here is taken as a complete survey:** Chromey &
  Hasselbacher 1996 (paywalled, abstract only — the 2–5%/degree twilight figure
  is SECOND-HAND via Freudling 2007 and Wei 2014); Regnault et al. 2009;
  Schlafly et al. 2012; Tamuz et al. 2005 in full; Penev et al. 2013; Heymans
  et al. 2012; Jarvis et al. 2016; Filippenko 1982.

## 2. MY MECHANISM CLAIMS — UNMEASURED, LOAD-BEARING, DO NOT PROMOTE

**None is measured. If a session quotes one as settled, that is the failure this
seat exists to prevent.**

1. **A pure change of registration reference is a COMMON transform** —
   `H_B⁻¹·H_m = (H_B⁻¹·H_A)·(H_A⁻¹·H_m)` — **so the relative orientation
   mixture at a sky position is invariant and only the FIT RESIDUAL changes.**
   Elementary, but it is what bounds the reference-swap experiment's confound
   analysis.
2. **A clamp is a phase-dependent NONLINEARITY acting preferentially on the
   steepest gradients, which are star cores.** Follows from two sourced halves;
   **no source states it for clamping.**
3. **Clamping broadens the MINOR axis of a trailed star preferentially, so it
   would make trailed stars ROUNDER — the sign is plausibly opposite to
   "induces ellipticity."** Mine. **It points at a "our gradient is a floor"
   reading which is NOT established and must not be adopted** — that reading
   arrived twice by different mechanisms and was refused both times.
4. **Second moments of a weighted-mean coadd are the weighted mean of the input
   moments, so the trace is preserved EXACTLY under equal-trace orientation
   mixing.** Exact arithmetic — **but the observable here is a Gaussian FIT, not
   a moment trace**, and the registry already records that a fitter misreads a
   blend.
5. **WITHDRAWN, recorded so it is not re-adopted:** *"a bias common to both arms
   largely cancels in the reference swap."* Too strong. What survives is only
   that the BINARY reading is robust — a null stays a null.

## 3. PINNED REFS — my sources move, git history does not

    Montage  distort.c / wcs.c / wcsinit.c   82a5e1162c6c   2016-12-22
             MontageLib/Project              6a34acf914b3   2023-04-10
             MontageLib/ProjectPP            5d2f1a1583ad   2023-09-07
    Siril    read at TAG 1.4.4 (median_and_mean.c, stacking.h, command.c);
             master fetched only for the diff
    GraXpert releases API: stable 3.0.2 (2024-05-03); newest tag 3.1.0rc2
             (2025-01-01, prerelease=true)
    Siril    GitLab tags: 1.4.4 = 2026-06-17; NO 1.5.0 tag exists
    CosmicClarity  setiastro/cosmicclarity, newest release 2025-03-29
    AstroSharp     deepskydetail/AstroSharp, ZERO releases, pushed 2025-12-19

**Papers:** arXiv 0810.0027 (Jarvis/Schechter/Jain 2008) · 1001.2333 (Bernstein
2010) · astro-ph/0703454 (Padmanabhan ubercal) · 1706.01542 (Burke FGCM) ·
1706.09928 (Bernstein DECam) · 2302.10929 + 1904.11991 (Evryscope) ·
astro-ph/0501144 (Erben GaBoDS) · 0711.0808 (Sharon WOOTS) · 1407.8283 (Wei
AST3) · astro-ph/0610705 (Freudling FORS) · 1401.2636 (Bernstein & Gruen) ·
2501.08358 (Ali all-sky).

**PIN THE REF ON ANY EXTERNAL CLAIM YOU HAND OVER. I read Montage at `master`
and was rescued only by the files not having moved since 2016** — that is luck,
not practice.

## 4. MY ERRORS — the shapes, because a successor inherits the seat and not the lessons

- **TWO OVER-READS IN ONE SESSION, BOTH IN THE SAME DIRECTION — the one that
  made the finding look more valuable.** (a) A sentence in a register row's
  STATUS cell widened to *"the removal condition is mis-keyed and has already
  fired"*; the condition was in a different column and correctly keyed. (b) The
  **absence** of an `INSTALLED` marker read as a declaration of absence.
  **Treat a same-direction pair as a live bias, not two incidents.**
- **MATCH-CENTRED EXTRACTION RETURNS A CELL; I ATTRIBUTED ITS PROPERTY TO THE
  ROW.** The truncated-view failure, committed while using the instrument the
  registry prescribes as its fix. **Fix: column-split before forming any verdict
  on a table-borne claim.**
- **AND THAT FIX IS NECESSARY, NOT SUFFICIENT.** A research-queue row's content
  can continue past the table's end, in a paragraph — where a column-split on
  the row returns **zero**. **Check whether the row is the whole cell FIRST.**
- **I CITED A THRESHOLD AS A *RECORDED* LESSON WHEN NO TRACKED FILE CARRIES IT.**
  The word **`recorded`** is what gave it the tree's authority. **Where the
  figure originated I cannot establish, and neither should you.**
- **I BUILT AN AMENDMENT ON THREE FIGURES THAT REACHED ME IN A UNIT BRIEF WITH
  NO TRACKED RECORD**, and used them to retract an elimination. The arithmetic
  was sound; the inputs were a message. **Found because a worker ASKED where the
  numbers came from — not by my volunteering it.**
- **I SOURCE-READ MONTAGE FOUR FILES DEEP AND NEVER ASKED WHETHER IT WAS
  PACKAGED.** It is — Debian `montage` plus `python3-montagepy`. I had refused
  the availability class as *rig state*; **"is this in the distro archive" is a
  fact about the ARCHIVE, not the rig, and that is this seat's lane.**
  **`0 files in the tree` is a fact about the tree and never about the rig.**
- **NEAR MISS — I nearly reported that Montage cannot read SIP.** `wcsinit.c`
  returns **0** for `SIP`, `TAN-SIP`, `A_ORDER`. WCSTools calls it
  **`DISTORT_SIRTF`**. **A grep keyed on the modern name returns a confident
  false negative on a route-closing question.**
- **NEAR MISS — a search summary handed me *"cubic (3rd-order Lanczos) x-domain
  interpolation … 0.04e"*.** The paper says *"cubic **u-space**"* — Fourier
  domain, not Lanczos. **Had it landed we would carry a fabricated agreement
  between our own measurement and the literature, which is worse than having no
  literature.**
- **I let three units die in deleted untracked files and did not object.** The
  files were never cleared to land; **the findings did not need to go with them
  and I did not say so until someone else measured it a day later.**

**THE COMMON SHAPE, and it is the most transferable thing here: a surface that
reports CAPABILITY has no obligation to report BEHAVIOUR — and a SUMMARY of a
surface is a third thing again.** `listed ≠ scriptable`. `declared ≠ consulted`.
`listed ≠ exhaustive`. **Go to the source when the answer decides a route, and
pin it.**

## 5. THE UNCHECKED LIST — open, not discharged

**Migrated, still open:** corner ⟂ compose independence · a fresh clone completes
the astromatic build · `manifest.tsv` completeness (falsified once; *"fixed the
four we found"* is not *complete*) · the 35.6's own reference distribution.

**Mine:** **which of Montage's THREE bundled WCS trees the build links** — I read
`wcssubs3.9.0_montage`; `wcstools-3.8.1` and `-3.8.7` are also vendored, and no
SHA answers this. A `config.make` read settles it.

**Possibly closed, unverified by me:** whether siril `requires` has an upper
bound. **I did not re-run it.**

**MEASURED AND NOT CLOSED — `graxpert` is not importable anywhere on this rig.**
`ModuleNotFoundError: No module named 'graxpert'` on **`/opt/astro-venv`,
`/usr/bin/python3` and `~/.local/share/astrometry-venv`**; `manifest.tsv`
carries the `/opt` **binary** only, no module row. So the predecessor's question
— does `background_grid_selection` import from a pip install — is ANSWERED NO
for this rig, and what it leaves behind is the live half: **`TOOLS.md`'s
`GraXpert classical interpolators` row, in the research queue, still
reads *"Points can be produced by GraXpert's own `background_grid_selection(...)`,
so the route needs no in-house analysis"*, unhedged, in a cell whose neighbouring
clauses are correctly hedged. That sentence sends a session to numpy on the
deliverable's pixels.**

## 6. OPEN WITH THE OWNER

**The superflat route on the `sky × V` object tilt — the project's core open
defect, no corrective shipped.** The flat-residual line is **PAUSED by the owner
pending real flats** (`8ccba18`). **The tree carried two contradictory readings
of that pause's scope**; the disposition reached was that the pause holds,
because it is a tracked owner act while the exemption's only witness was the
document that benefited from it. **The owner rules; nothing is scheduled on that
line.**

## 7. PROCESS FACTS IN NO OTHER DOCUMENT

- **`ListAgents` does not list the querent.** A roster is every live session
  EXCEPT the asker. **The corollary that names are per-vantage is FALSE** — all
  other names agree across vantages and are safe to relay; a worker falsified it
  with set arithmetic over three rosters. Reply to the `from=` attribute, for
  that narrower reason.
- **Messages cross.** A peer can endorse as decisive something you retracted
  between their composing and your reading. **Name it rather than quietly
  re-sending** — the failure is silent in the other direction.
- **A count without its stated filter is not a measurement.** Two seats measured
  *"the same thing"* and disagreed five times in one day, every time from an
  unstated filter.

## 8. THREE OF MY CLAIMS THAT WERE CORRECTED — do not re-derive them

1. **`-weight` and `--nonorm` DO co-occur in one file** (`run_pipeline.sh`). The
   separation is by **INVOCATION** — `-nonorm` is on the calibration-master
   stack, which never receives the weight variable. **The conclusion survives;
   the file-level reason is false.** A false reason on a true conclusion
   discredits the conclusion when it fails.
2. **`TRANSFER FUNCTION` is a taken term** — it carries the flat-differential
   result at two sites. The coadd-orientation demotion landed descriptively,
   with no new term.
3. **`Evryscope` is 0 files tree-wide**, so any claim about what a past session
   published about it is team history and unsupportable as a tree fact. The
   Evryscope fact itself is sourced and fine.
