# Fresh-session brief — measure the object tilt, catalogue-free

**SELF-RETIRING.** Delete this file in the commit that lands the result.

You are settling the flatless route's remaining photometric defect with a
number. A sky flat converges to `(mean sky) × V`; horizon-fixed sky structure
cannot drift out of a median of un-registered lights, so it bakes into the flat,
and dividing by it leaves the OBJECT carrying a multiplicative tilt it never
had. Backgrounds then look flat BY CONSTRUCTION — the corner-vs-centre check is
self-fulfilling for exactly this defect — and star shapes are untouched. The
harm is photometric and nothing in the chain currently sees it.

The figure the repo quotes for it, **3.11% at 241σ, has no tracked record.**
Verified live: it is cited in `BACKLOG.md` (three sites) and in the
`readiness.json` prose of at least five sets, and no `datasets/` record holds
the measurement, its instrument or its n.
It entered as prose. Your result replaces it or marks it unverified at every
citation.

## What is already verified — do not re-derive it

Re-executed on this rig before this brief was written (load average 1.2–1.5,
926 G free):

- **All five guards PASS** (`check_bitdepth`, `check_calibrate`,
  `check_siril_invoke`, `check_stack_rejection`, `check_registration_pins`) and
  all three selftests PASS (`compose_preflight`, `lens_preflight`, `route.py`).
- **The corpus is fully staged**: 12 real light sets over 3 nights — **5,723
  staged** raws (`.nef` count per set dir, `set-00` excluded as the spare-frames
  bucket) and **5,665 stacked** (sum of `STACKCNT` over all 52 sub-stacks), so
  **58 culled**. The cull is not uniform: aug06/set-03 alone accounts for 44 of
  it, which is the cloud block `BACKLOG:intake-culling` names as a positive
  control — a set whose members you should expect to behave differently.
  `run_session_chain.sh sessions/aug09 --plan` walks all five sets clean end to
  end.
- **The inputs you need already exist and are solved.** Every set has its
  groups-route sub-stacks under `sessions/<night>/work/groups_set-NN/` — 4–5
  consecutive-time blocks per set, 52 across the corpus, each independently
  plate-solved (`solve_sub_NN.json`, scale 17.008–17.028″/px, SIP WCS in the
  header). **No rebuild is required for the measurement.**
- **The drift, in the units that matter.** Sky excursion per set runs
  2.37–5.75° (`fingerprint.json`), which at the stacks' 16.98″/px is
  **503–1220 px across the sensor** — aug09/set-01 976 px, july31/set-01 1220 px.
  (BACKLOG:`calibration-evidence` said "~1500 px"; corrected in the commit that
  landed this brief.) Measured per-block on aug09/set-01: consecutive
  sub-stack solved centres step 307.36 → 308.95 → 310.63 → 312.28° RA, and their
  `CRPIX1` steps ~258 px — the same star lands ~258 px apart between adjacent
  blocks and ~774 px across the set.

## Standards first — research before you design anything

This is not novel territory in the field, only in this repo. The survey lineage
is **photometric self-calibration**, also called **star flats**: SDSS übercal
(Padmanabhan et al. 2008), Pan-STARRS1 forward global calibration (Schlafly et
al. 2012), SNLS/DES star flats (Regnault et al. 2009). The principle is exactly
what this data hands you for free: repeated measurements of the same stars at
different focal-plane positions constrain the position-dependent throughput
without any external catalogue. **Untracked drift is free dithering.** Say so in
the record, with the source.

**Before writing one line of measurement code, search the tools for it**, and
record what you searched and what each one returned:

- Siril's own photometry surface — `psf`, `seqpsf`, `light_curve`, and whatever
  else `help` lists. A GUI-only name may have a scriptable sibling; that trap
  has already cost this repo a whole instrument (`tilt`/`inspector` refuse,
  `seqtilt` was the answer). **Probe, never assume — `help` listing a command is
  not evidence it runs headless.**
- SExtractor's core `sep` 1.4.1, already installed in
  `~/.local/share/astrometry-venv` and already this repo's sole extractor. It
  exposes `extract` (flux), `sum_circle`, `sum_ellipse`, `sum_circann`,
  `sum_ellipann`, `flux_radius` — i.e. real aperture photometry.
- **SCAMP** (astromatic) is the standards answer for a photometric solution
  across overlapping exposures and is NOT installed. Check whether it is
  packaged for this rig and whether it runs headless on this data. If it does
  the job, that outranks anything built here — report it and stop.
- ASTAP's photometry, GraXpert, anything else in `TOOLS.md` that could plausibly
  report position-dependent throughput.

"Every number came from a tool" does not make an in-house analysis in-bounds.
If a tool does this, use the tool.

## The measurement

**The principle is the separability principle used diagnostically**: a term
fixed in SENSOR coordinates and a term fixed on the SKY are degenerate until
something decouples them, and the drift is the decoupler. The flat's residual
tilt is sensor-fixed; the sky is sky-fixed; the drift carries every star
503–1220 px across the sensor within one set.

**Shape.** Within one set, every block was calibrated by the SAME per-set sky
flat, so the multiplicative residual `g(sensor)` is common to all of them. For a
star matched across blocks, the ratio of its measured flux between block *j* and
block *k* is `g(P_j)/g(P_k)` — the star's own brightness, the extinction, the
zero point and the aperture all cancel to the extent they are common. Correct
calibration makes a star's measured flux independent of where on the sensor it
landed.

**Per sub-stack**: the tool measures every star's flux and its position in that
sub-stack's OWN pixel grid — which IS the sensor position for that block — and
its RA/Dec from the sub-stack's own solved WCS. Cross-match by sky position
across the blocks of one set. Fit measured flux against sensor position. The
in-house part is the cross-match and the fit and nothing else; it is the same
class as `member_separation.py`, and if it ships it carries a removal-conditions
row in the same commit.

**Report the fit as a fractional tilt across the sensor, per set, plus its
uncertainty and its n.** Do not report a single corpus number as if the defect
were one thing.

**Resolution limit, state it with the result**: each block averages a star over
that block's own drift (~244 px for a 4-block set), so the instrument sees `g`
convolved with a boxcar that wide along the drift axis. More, shorter blocks
sharpen it and cost depth — if you rebuild blocks, declare the count as a knob
and state the smear.

**What it constrains and what it does not.** The drift is predominantly in RA
and lands on one sensor axis, so this measures the along-drift gradient and says
nothing about the perpendicular one. That is the right axis: the flat
decomposition puts the L/R term at 3.6× the T/B term and identifies it as SKY.
Say the limitation out loud rather than letting the number read as whole-field.

## The confounders, each with the control that separates it

These are not hypotheticals; every one is a registered mechanism in this repo.

1. **A Gaussian-fit magnitude moves with the PSF, and the PSF varies across the
   field.** The registry records a radial field aberration in the optics —
   roundness gradient −0.099 across x, major-axis angle tracking field azimuth
   in 7 of 8 zones. A fitted magnitude at constant true flux therefore reads
   differently at different sensor positions, which is precisely the signal
   under test. **Control: aperture photometry with a fixed aperture large enough
   to contain the worst PSF in the field, and repeat the whole fit at a second
   aperture radius.** A real throughput tilt does not move with aperture; a
   PSF-fit artefact does. Report both radii. This is also the answer to the
   trailed-photometry caveat — the 20–30% systematic on record is *Gaussian-fit
   photometry on trailed stars*, and it is a scale error that cancels in a ratio
   only if it does not vary with position.
2. **Detection depth.** `findstar` goes as faint as the image allows and
   marginal fits are inflated; comparing populations across images of different
   depth measures depth, not quality — measured at a factor of 9 across one
   pair. **Control: one common fitted-amplitude threshold across every block and
   every arm, or rank-match on the N brightest. Report n and the faintest
   admitted amplitude with every number.**
3. **`findstar`'s default roundness floor is 0.50**, which truncates exactly the
   elongated tail this data is made of. Drop it to 0.05. `seqfindstar` writes no
   star lists headless on 1.4.4 — use per-image `findstar -out=`. And
   `setfindstar -reset` returns exit 1 on success, so an `.ssf` ending in it
   fails a `set -e` caller for no reason.
4. **Sub-stacks do not share a pixel origin.** `seqapplyreg -framing=max` on a
   variable-size sequence gives every output its own origin — measured 611.9 px
   apart, and it made `member_separation.py` measure nothing at all for a long
   time (67 of 2000 stars matched within 12 px; 1721 once re-based). **Match by
   sky position through each product's own WCS, never by pixel coordinates.**
   The blocks' geometries here differ (5769×3950, 5769×3959, 5772×3962,
   5771×3935 on one set) — that is the same fact.
5. **A sub-stack's `DATE-OBS` is inherited from its first frame** — all four
   aug09/set-01 blocks read `2026-08-10T03:49:33`. Per-block timing comes from
   the group's `g*.list` member lists, not the stack header.
6. **The zero point differs between blocks** (extinction and transparency drift
   through a set; the corpus carries a measured 18–24% cross-night noise gap and
   +0.16 mag of extinction on the hazy night). The multiplicative part of that is
   a constant factor — the fit's INTERCEPT, not its slope. Normalise it out
   explicitly and say you did; do not let it leak into the tilt.
7. **The members are not offset-free, and an offset does not cancel the way a
   scale does.** Every light stack pins **`-norm=addscale -output_norm`**
   (`run_undistort_groups.sh`, `run_undistort_pipeline.sh`,
   `run_undistort_compose.sh`, `lights.ssf.tmpl`), which matches each member's
   background TO THE REFERENCE and then re-zeroes at the darkest pixel. So each
   block carries its own ADDITIVE pedestal as well as its own scale. A scale
   divides out of a flux ratio; **a pedestal does not** — and because the
   pedestal is per block, and blocks are what define the position axis, it leaks
   straight into the quantity under test and can manufacture a tilt outright.
   **Control: the flux measure must be locally background-subtracted, and say
   which one you used.** Both tool-sourced options exist — `sep`'s local-annulus
   forms (`sum_circle(..., bkgann=…)`, `sum_circann`), or `findstar`'s fitted
   amplitude `A`, which the star list already reports above its own fitted local
   background `B`. A raw aperture sum over an un-subtracted background is not an
   admissible measure here.
8. **A number read off a loaded box is not a measurement.** A fixture reading
   moved 3× (14666 vs 45398) between loaded and idle on identical inputs. Check
   `uptime` before quoting anything and put the load in the record.
9. **Siril's own `stat` cannot verify Siril's own damage** — it excludes zero
   pixels, and `offset` clips at 0 in 32-bit against its own help. If any step
   subtracts, use `isub`, and read saved pixels with an independent reader.
   `idiv` clips at 1.0 silently; ratios use `fdiv`.

## The controls that make this a measurement — required, not optional

The repo's most persistent defect is a check that cannot fail, and the thing
meant to prove it could fail is usually defective too. **Falsifications are
executed, never argued.** Three controls, all of which must be run and reported:

1. **The NULL control fixes your noise floor, and it is measured, not
   subtracted.** Split one set INTERLEAVED — even frames against odd — and run
   the identical instrument on the two halves. Interleaved halves span the same
   drift, so their mean sensor positions differ by one frame interval
   (~2 px against the ~774 px real baseline, 0.3%): **the predicted tilt is
   zero.** Whatever the instrument reports there is its floor. This is the exact
   control shape the flat-window work already validated on this data —
   interleaved halves 0.035%/0.046% corner spread against 3.481%/4.177%
   contiguous. A floor is a measurement, not a subtraction of two numbers you
   happen to have; that mistake produced a threshold permissive enough to call a
   real 1% colour shift noise.
2. **The POSITIVE control must move the instrument.** Take one real block pair,
   apply a KNOWN multiplicative ramp with the tool (`fdiv`/`imul` against a
   synthetic ramp card — the flat-side work's discrimination pattern), and
   require the instrument to recover that ramp's slope. Report the
   discrimination ratio the way the iterative-flat NULL did (48–62× is the
   standard this repo has already met). An instrument that cannot recover a
   planted tilt cannot be trusted to report a real one.
3. **The CORPUS prediction, and it is falsifiable.** If the tilt is caused by
   the flat's baked-in sky gradient, the measured tilt must track the flats'
   own measured L/R dose across the 12 sets — **including changing sign.**
   Verified in `datasets/aug09/corpus_flat_odd_component.json` (edge geometry):

   | set | L/R | edge dipole x |
   |---|---|---|
   | july31/set-01 | 0.6420 | **+0.4360** |
   | july31/set-02 | 0.6810 | +0.3795 |
   | july31/set-03 | 0.7197 | +0.3260 |
   | july31/set-04 | 0.8012 | +0.2208 |
   | aug06/set-01 | 0.8969 | +0.1087 |
   | aug06/set-02 | 0.9331 | +0.0692 |
   | aug06/set-03 | 1.0259 | **−0.0255** |
   | aug09/set-01 | 1.1081 | −0.1026 |
   | aug09/set-02 | 1.1800 | −0.1651 |
   | aug09/set-03 | 1.3210 | −0.2766 |
   | aug09/set-04 | 1.4407 | −0.3611 |
   | aug09/set-05 | 1.4772 | **−0.3853** |

   Three nights are three sky regimes (moonlit july31, clear aug06, hazy aug09)
   and the sweep is monotone through zero. **aug06/set-03 is a built-in null
   control** — a flat carrying essentially no L/R sky dose should show
   essentially no tilt — and july31/set-01 and aug09/set-05 are the two extremes
   with OPPOSITE sign. A tilt that does not track this ordering falsifies the
   attribution even if the tilt itself is real, and that is a finding worth as
   much as a confirmation. Pre-register the prediction before you run it.

## Fenced — do not resurrect any of these

Read `docs/dead-ends.md` in full first. These are closed with mechanisms:

- **Raw-domain de-sky (`--desky`)** — `seqsubsky` on the flat's raw source
  frames. A domain error, 31× regression, 12.4% vs 0.4% corner spread, and its
  cited proof of success was the defect's own signature.
- **Degree ≥2 backgrounds** — refuted on parity grounds: vignetting is an even
  radial function and degree 2 is the first degree with even terms, so `subsky`
  cannot separate them.
- **The entire self-referential flat-correction class**, including the
  domain-corrected iterative sky flat: the iteration returns whichever flat it
  is handed. Controls moved the same code 81.7%/93.4% where the scheme moved it
  1.7%/1.2%.
- **Additive matching for the corner term** — measured NULL; the driver is
  multiplicative and unreachable by any background subtraction.
- **GraXpert `-correction Division`** on fields filled with unresolved
  starlight — eats ~2/3 of the extended structure.
- **A Gaia catalogue check** — structurally impossible here (trailed stars at
  17″/px). That is *why* this design is catalogue-free; the stars are their own
  reference.
- **Corner-vs-centre or four-corner-box flatness as evidence about this
  defect** — self-fulfilling by construction, and on a Milky Way field a
  four-corner metric measures which bit of sky landed in four boxes.
- **Any acquisition or equipment answer** — real flats, a tracker, stopping the
  lens down. The data is a given; the fix lives in the chain.

## The decision rule — owner-ratified, apply it as written

- **Tilt SMALL** → record it, carry it as the route's declared floor, and file
  the self-calibration research as a documented opening. Done.
- **Tilt SIGNIFICANT** → the constructive half of this measurement becomes the
  fix's foundation: the sensor-fixed field fitted from matched-star flux ratios
  is externally referenced (the stars themselves), which is what dodges the
  self-cancellation that killed the whole iterative class. Do NOT build the
  corrective in this session — report the measurement and the design opening,
  and the fix gets its own brief.
- **Measurement too NOISY** → report the noise floor with its numbers. The
  separability research then has to find another form, and knowing the floor is
  the deliverable.

## Acceptance — executable, each with what you ran

1. Every guard and selftest still PASSES after your changes, and any new
   instrument has a `--selftest` that FALSIFIES its own mechanism in process:
   break it, watch it go RED, restore, watch it catch again. Argued
   verification does not count — it has failed three times here for three
   different reasons, each time looking green.
2. The NULL (interleaved-halves) control is run and its floor reported with n.
3. The POSITIVE (planted-ramp) control is run and its discrimination ratio
   reported.
4. The corpus prediction is pre-registered, then run across all 12 sets, with
   aug06/set-03 called out as the near-zero control and the two extremes as the
   sign test.
5. Per-night numbers across all three regimes; no single corpus figure standing
   alone.
6. Every number carries its instrument, its n, its faintest admitted amplitude,
   its aperture radius, its background-subtraction form, and the box's `uptime`.
7. **A tracked record exists** under `datasets/`, and the untracked 3.11%/241σ
   figure is either replaced by it or marked unverified at all of its citation
   sites — `BACKLOG.md` (three) and the `readiness.json` prose of at least
   five sets. Re-grep before you start; the citation set moves.
8. The tool search is recorded — what you searched, what each returned, and why
   anything in-house was necessary. Anything in-house that ships gets its
   removal-conditions row in the same commit.
9. `prompts/REPORT.md` updated in the same commit; this file deleted in it.
10. Before editing any chain script, `pgrep -f` it — a running bash script is a
    live file, and editing one mid-flight executes garbage.

## Honest failure

**The NULL is the most valuable result this program produces.** If the tilt is
below the floor, if the instrument cannot resolve it, if the corpus prediction
fails, or if the whole design turns out to be confounded by something above —
say so plainly, with the numbers, and register it. The iterative-flat session
was this arc's most valuable session and it returned nothing but a NULL with
controls. Do not manufacture a result, do not soften one, and never use
"fixed / final / matched / close" language. A killed hypothesis becomes a
dead-end entry with its numbers before anything else is tried.

Verify everything in this brief against the repo before relying on it.
