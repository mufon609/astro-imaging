# Oracle handoff

**PROMPT-KIND: register**

**SUPERSEDES `prompts/ORACLE_HANDOFF_engagement2.md`, which must die in the same
commit that lands this.** What was still live in it is migrated below and marked
MIGRATED; what was stale is dropped and named as dropped, so nothing is lost
silently.

**The name carries no engagement number, deliberately.** Three handoffs would be
three places for the same fact to drift. **The next Oracle REPLACES this file; it
does not add a fourth.**

**Read `prompts/ORACLE_TEMPLATE.md` first — it is the role.** This file carries
only what a document cannot: searched negatives with what was actually looked at,
which of my claims are inference rather than measurement, the refs that make
external claims re-derivable, and the errors I made.

**THIS FILE IS A SNAPSHOT, NOT A LIVE RECORD — RE-VERIFY ANYTHING ITS AUTHOR
COULD HAVE CHANGED AFTER WRITING IT, AND THE UNCHECKED LIST IN §6 HARDEST.**
MEASURED, by the author, on this file: it states *"a correction delivered in
conversation does not correct the tree"* in §8, and then its own §6 item 6 was
answered in a peer message and left standing here for forty minutes — the rule
failing on the artifact that carries it. An UNCHECKED list is written by the one
party most likely to close an item and least likely to re-read the list.

---

## 1. SEARCHED AND EMPTY — DO NOT RE-RUN

Each cost real tokens and each closed something by being empty. **A searched
negative reported as a negative is a deliverable.**

**Mine, this engagement:**

- **SWarp has NO homogenisation-kernel reader in its SOURCE** — not merely
  undeclared in its config. 69 C files: `HOMO`, `homo_`, `.homo`, `PSFnormalize`,
  `homogen` = **0 files each**, against a `RESAMPLE` positive control at 4. The
  PSFEx manual routes `.homo` cubes to DES-internal **PSFnormalize** and says
  *"The SWarp software may also later include this possibility."* **It did not.**
- **The FITS registry has NO calibration-provenance convention.** 23 registered
  conventions enumerated; none covers calibration provenance or processing
  history.
- **MaxIm DL `CALSTAT` records WHICH STEPS ran (`B`/`D`/`F`), never which frame.**
  The vendor's header page carries no keyword naming a master.
- **astropy `ccdproc` deliberately erases master identity.** `log_meta.py`'s
  `_replace_array_with_placeholder()` rewrites a `CCDData` master as the literal
  string `"<CCDData>"`.
- **PixInsight XISF is UNREACHABLE from the vendor site** — three fetches
  (release, DRAFT 8, DRAFT 3) all **HTTP 403**. Do not retry there. It also could
  not change a FITS-keyword decision, since nothing here writes XISF.
- **Siril `-disto=master` is NOT DETERMINED by the documentation.** Both
  per-image and auto-selected-shared readings survive the sentence *"load
  automatically the matching distortion master corresponding to each image"*, and
  1.4.4's own `help register` carries the identical wording — **so it is not a
  docs-vs-build gap and reading harder will not settle it.** The discriminating
  probe is specified in the corner thread.
- **IRAF's header format strings are in NO documentation page** (five tried,
  including readthedocs and the `.hlp` sources). They are in the source:
  `setzero.x` / `setdark.x` / `setflat.x` / `setillum.x` / `setfringe.x`, plus
  `setheader.x` for `ccdproc`.

**MIGRATED from engagement 2 — still live, NOT re-verified by me:**

- No installed tool reports a propagated error on a shape moment.
- No tool fits a linear-trail model reporting length `L` directly.
- No shutter-metrology literature using trail length for effective exposure.
- No documented treatment of trail-profile non-uniformity in fixed-mount imaging.
- No upstream Siril/flatpak issue for concurrent `siril-cli` instance-dir
  collisions (the instance dir is a **flatpak** construct, so Siril's tracker
  will keep returning empty either way).
- No SCAMP photometric-mode minimum-detections threshold in its documentation.
- **No packaged headless CPU Linux tool for anisotropic spatially-varying
  deconvolution.** **QUALIFIED BY §3 BELOW** — PSFEx *computes* a
  spatially-varying homogenisation kernel; nothing installed *applies* it.
- `lenstool` unpackaged — **UNCHECKED by engagement 2's own admission**: it used
  `apt-cache policy`, the instrument that produced the SCAMP error. Completing
  check is `apt-cache showsrc lenstool`. The PM directed not to spend on it.

**DROPPED as stale:** engagement 2's §1 team roster (every seat has turned over)
and its §5 route-gating text (superseded by §3 and §5 here).

---

## 2. MY MECHANISM CLAIMS — UNMEASURED, LOAD-BEARING, DO NOT PROMOTE

All three are cited somewhere in the tree right now. **None is measured. If a
session quotes one as settled, that is the failure this seat exists to prevent.**

1. **Scale-based separation cannot split vignetting from a baked sky gradient
   here.** My generalisation of the registry's own parity argument for `subsky`
   degree 2 (*"they are the same functional form as vignetting"*). **This is what
   closes the IRAF illumination-correction route in the superflat unit** — if it
   is wrong, that route reopens.
2. **Classical interpolation trades class-blindness for placement sensitivity,
   and GraXpert's darkness-based auto-placement does not escape the absorption**
   (`background_grid_selection` imports `find_darkest_quadrant`; on a
   starlight-filled field the darkest cells are still starlight). **This is the
   LIMIT clause on the GraXpert row.**
3. **Siril 1.5's native masking reclassifies per-region RL from FORBIDDEN to
   UNPROVEN.** My reading of the registry's own classification against a
   documented capability. **If compressed to "1.5 unblocks per-region RL" it
   becomes a false all-clear on a physics question nobody has run** — the
   registry's *"the prior blocker is SNR, not seams"* is untouched.

---

## 3. FINDINGS THAT MOVED A ROUTE — measured half and unmeasured half

- **PSFEx implements spatially-varying PSF homogenisation.** `homo.c`: target is
  a circular Moffat from `HOMOPSF_PARAMS`, kernel expanded in a Gauss-Laguerre
  basis, solved by Cholesky (`LAPACKE_dposv`), **no guard against a target
  narrower than the measured PSF and no regularization** — only a non-fatal
  `warning("Not a positive definite matrix")`. `makeit.c:553,577` gates and calls
  it, so it is **declared AND consulted**. Installed since `754e5c5`.
  **`docs/dead-ends.md`'s "NO INSTALLED TOOL CAN CORRECT A FIELD-VARIABLE
  ANISOTROPIC PSF" is false as worded.** The route stays closed on three better
  grounds: no installed applier; the vendor calls homogenisation *"presently an
  experimental feature"*; and the owner's refusal, formally backed by Zackay &
  Ofek.
- **Siril `-weight` is two different estimators.** `wfwhm` and `nbstars` ARE
  min-max ramps — the worst frame gets **exactly 0, not ~0**, at any spread.
  `noise` is **inverse-variance, mean-normalised** (the standard optimal
  estimator) and drives nothing to zero. `nbstack` is the raw stack count.
  **VERSION JOINT UNRESOLVED: read at siril master, we run 1.4.4.** Probe:
  `median_and_mean.c` calls `siril_log_debug` printing per-frame weights, so one
  debug-enabled stack settles both the version question and our own data.
- **Siril DOES consume per-image distortion.** *"it is first corrected for
  distortion and then linearly projected… in a single operation."* The
  `seqapplyreg` transform-class list describes registration **data**, not the
  pixel mapping — `listed ≠ exhaustive`. **And "distortion found but not
  applied" is a documented state whose tell is a CONSOLE WARNING**, not a header
  key; `run_undistort_compose.sh:352,355` already gates on that channel.

---

## 4. PINNED REFS — my sources MOVE, git history does not

Every external claim above is re-derivable at:

    swarp   master  bf4f496f18c04a8d32022b45449ef8675ab9b3da
    psfex   master  25a586d16ba02d7ac06956e64d4e60ab85ed276c
    siril   master  5c7cfbc14fb9b4ecdc51e2cf52a800821c9873e3
    GraXpert  tag   3.0.2   (matches the installed build)

    Siril docs:  /en/stable = 1.4.4   /en/latest = 1.5.0-dev

**Pin the ref on any external claim you hand over.** This was a real gap in my own
work until the historian named it.

---

## 5. OPEN, AND WITH THE OWNER

**The superflat route on the `sky × V` object tilt** — the project's core open
defect, no corrective shipped.

- **The field's standard answer exists and the repo had never seen it.** SEARCHED,
  and the literals are written SPLIT below so this paragraph is not itself a hit:
  `super`+`flat`, `illumination `+`correction`, `illum`+`cor`, `mk`+`illum` each
  returned **0 tracked `.md` files** when measured — **at a commit BEFORE this file
  landed.** Re-measured at `51e36ab` each returns **exactly 1 file, and that file is
  this one**: the record asserting the absence became the only thing its own query
  could match. **The substance survives — nothing outside this file carries any of
  the four — the stated count does not.** Same shape the registry
  registers: *you cannot document a string-search finding by pasting the string;
  split the literal and state counts at a named commit.* The construction is a median of many un-registered
  dark-sky frames **across many pointings**, which is what makes an
  observer-frame term average down.
- **Our ratified ban (`README.md:85`) forbids exactly that construction**, and it
  was ratified against the imprint mechanism the superflat defeats by averaging.
  **Same measured fact, opposite conclusions; the repo has only ever seen one.**
- **Probe RAN (worker, `e99f3e6`):** max angular separation **37.17°** corpus-wide
  against a **27.09°** sensor field = **1.37 field widths**, dominated by
  cross-night pairs; **within-night 9.63–17.46° = 0.36–0.64 field widths.**
- **TWO CONSTRAINTS OPEN, NEITHER RESOLVED:** (1) a cross-night superflat spans
  different **optical states** — but the registry records that attribution as
  **UNATTRIBUTED** and says *"do not design a corrective… on the grounds that it
  is optics — that is not established"*, so the objection **selects the unit**
  (surveys build per-RUN; our stable block is the NIGHT) rather than killing the
  route; (2) moonless-vs-moonlit gradient magnitudes differ.
- **The ban is untouched. This is the owner's call, not the pipeline's.**

---

## 6. THE UNCHECKED LIST

**MIGRATED, still open:**

1. **Corner ⟂ compose independence.** Falsifier specified in engagement 2's file;
   goes live the moment anyone argues the SWarp/TPV route on priority grounds.
2. **A fresh clone completes the astromatic build.** Nobody has run a clone.
3. **`manifest.tsv` completeness.** Falsified once, four rows added — *"fixed the
   four we found"* is not *complete*.
4. **The 35.6's own reference distribution.** Untested by anyone.

**NEW, mine:**

5. **PARTLY DISCHARGED, and the residue is a stated BOUND rather than an open
   question.** The premise was that the registry's EVIDENCE-STATUS preamble is
   sufficient: it required *"n, instrument and scope"* and **never asked what the
   instrument was pointed AT**, while three over-generalisations were fully
   compliant with it and all wrong. SUBJECT landed as a fourth axis, and at
   `51e36ab` it is named as the **MEASURAND** with JCGM 200 (VIM) cited and the
   IVOA Provenance Data Model explicitly NOT adopted, deviation recorded.
   **Its own positive control then ran and caught 2 of 3** — it catches drift
   ACROSS a subject boundary and is **BLIND to drift WITHIN one** (`-weight` names
   `-weight`, so the axis matches and the widening sits inside the flag's own
   modes). **The missing half is a different discipline: enumerate a subject's own
   modes or values before asserting a behaviour of it** — which is what closed
   `-disto=` at three values and what nobody had done for `-weight`.
6. **CLOSED — MEASURED, and it carries a live hazard into `TOOLS.md`.**
   `background_grid_selection` imports from **NO interpreter on this rig**:
   `/opt/astro-venv/bin/python`, `/usr/bin/python3` and
   `~/.local/share/astrometry-venv/bin/python` all return
   `ModuleNotFoundError: No module named 'graxpert'`, while
   `/opt/graxpert-3.0.2/GraXpert-linux/` is present. Run by the Oracle, re-run
   independently by the PM. **CONSEQUENCE: `TOOLS.md`'s GraXpert row —
   *"Points can be produced by GraXpert's own `background_grid_selection(...)`, so
   the route needs no in-house analysis"* — is true of GraXpert and FALSE of this
   rig, and the hazard runs the dangerous way: a session follows it, finds no
   importable module, and writes the point placement in numpy, which is the exact
   bright-line crossing the sentence exists to prevent.** The route is
   bright-line-clean only AFTER `pip install graxpert` into `$ASTRO_VENV`,
   version-pinned to the bundled 3.0.2 since the generator's output feeds that
   CLI, with a `scripts/setup/manifest.tsv` row. **Routed to the worker as an
   INSTALL, not a doc edit; NOT LANDED as of `51e36ab`, so treat the row as
   hazardous until it is.**
7. **Whether siril `requires` has an upper bound.** MEASURED: it accepts a NEWER
   siril than its argument (`requires 1.2.0` under 1.4.4 → *"compatible"*), which
   rules out exact-match. **Upper bound untested** — and it decides whether a 1.5
   bump fails at the version check or later on an unknown `starnet`.

---

## 7. MY ERRORS — the shapes, because a successor inherits the seat, not the lessons

- **Wide-cell partial read.** Found the half of `README.md:83` that answered my
  question and treated it as the cell; the other half contradicted it. **The cell
  was 639 chars — NOT extreme — so this was a STOPPING RULE, not concealment by
  width.** (The genuine width case is the 4,506-char tail in `TOOLS.md`.)
- **Grouped three instances by surface; they measured to two plus one different
  mechanism.** The same error I had corrected in two other seats within the hour.
- **Claimed "written nothing" from a two-hour-old `git status`** while two of my
  own `.ssf` files sat in the repo ROOT — untracked and **not** gitignored.
- **NEAR MISS:** nearly reported *"Siril destroys DATASUM"* from a probe of the
  **DEFAULT**; `save -chksum` was documented throughout.
- **NEAR MISS:** nearly reported `TOOLS.md` as over-claiming on `rl`/`sb`/`wiener`
  mask-awareness, from a **summarised** vendor page that omitted them.
- **NEAR MISS:** nearly reported GUI `messagebox` behaviour as CLI behaviour;
  `cmdline_tools.py` settled it.

**The common shape, and it is the most transferable thing here: a surface that
reports CAPABILITY has no obligation to report BEHAVIOUR — and a SUMMARY of a
surface is a third thing again.** Three named variants met tonight:
`listed ≠ scriptable` (`tilt`/`inspector`), `declared ≠ consulted` (a config dump),
`listed ≠ exhaustive` (`seqapplyreg`'s transform classes). **Go to the source when
the answer decides a route.**

---

## 8. PROCESS FACTS IN NO OTHER DOCUMENT

- **`ListAgents` does not list the querent.** A roster that excludes the asker
  cannot answer *"does X exist"* when X might be the asker — I reported a peer's
  address as non-existent on exactly that. **Reply to the `from=` attribute, and
  never relay a peer's name to a third session as an address; names are
  per-vantage.**
- **A correction delivered in conversation does not correct the tree.** I narrowed
  my own Engagement-1 negative in messages and left the landed text standing.
  **When a later finding narrows an earlier one, grep the TREE for the earlier
  claim, not the conversation.**
- **My boot was independent; my state at retirement was NOT.** Anything I agreed
  with the PM or the worker on after roughly 20:00 is **not** corroboration.
  Give the same caveat when you hand a claim to a seat whose independence still
  has value.
- **A probe specified without controls is a probe half-specified.** My
  alt/az probe omitted the degenerate-coordinate hazard; the worker found a
  zenith degeneracy (a set 1.60° from zenith making raw azimuth spread
  meaningless) and an epoch-inheritance bug worth 45×, neither of which I named.
