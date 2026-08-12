# Fresh-session brief — per-group flats: does narrowing the flat window pay?

**SELF-RETIRING.** Delete this file in the commit that lands the result.

A per-set sky flat is applied to every frame in the set, and the registry
measures that it does not describe them: split one set into contiguous halves and
the two flats differ by **3.481% corner spread (july31/set-03) and 4.177%
(set-04)** against a build floor of **0.035% / 0.046%** — **100.0× and 90.6× the
floor**. Dividing the first frames of a burst by a flat built from all of them
leaves a corner-to-corner error of order half that, ~1.7%, with opposite sign at
the other end. The shipped route eats that error today.

The flat differential now says what such an error costs: **a flat's shape reaches
the delivered object at ~1:1** over the same window (delivered/flat 0.9887, 1.0117
corrected by the planted control, floor exactly 0.0000). So a flat improvement
is not a hope — it pays out one-for-one on the object, and the payoff is
predictable before the run.

**Per-group flats are also the more doctrinally correct object**, and this is the
strongest argument for them: the ratified rule is that **a flat calibrates ONLY
the exact frames it was built from**. A per-set flat applied across a 25-minute
burst already violates the spirit of that rule against its own measured
within-set change. Narrowing the window moves toward the rule, not away from it.

## Lead with the complication — it is not a footnote

**The within-set flat term and the object tilt are on DIFFERENT AXES.** The
within-set change is predominantly TOP-BOTTOM — y-slope **+0.8178** against
x-slope **+0.0705 %/1000 px** on set-03, an **11.6× excess** — whereas the
sensor-fixed residual the stack carries, and the sky dose the differential
measured reaching the object, are LEFT-RIGHT (**+0.171 %/1000 px**). Two axes are
two terms.

So: **per-group flats are not automatically the fix for the L/R object tilt, and
this brief must not be written up as though they were.** What generalizes from
the differential is the TRANSFER — any change in the flat's shape reaches the
object ~1:1 — not the axis. Whether narrowing the window also moves the L/R term
is an open question this measurement answers rather than assumes. A result that
improves T/B and leaves L/R untouched is a real, reportable WIN on a real defect;
claiming it fixed the object tilt would not be.

## Feasibility is already measured — verify it, do not re-derive it

The obvious objection is that a 100-frame flat is too noisy to be worth building.
It is not, and the number is on record: the builder's floor from **interleaved
halves at 130+130 frames is 0.046% corner spread** (grid range 0.128%), against a
within-set effect of 3.5–4.2%. A 100-frame group flat therefore sits roughly
**75–90× above its own build noise**. Confirm it at the group's actual depth as
control 1 below; do not inherit the 250+250 figure.

## The arms — one knob, and it is the flat window

**Set: july31/set-03.** Every input is on disk and every relevant number is
already measured there: the 3.481% half-to-half term, the 0.035% interleaved
floor, the grid-ramp axis decomposition, and exactly **5 groups × 100 frames**
with `g1.list … g5.list` under `sessions/july31/work/groups_set-03/`.

- **Arm A (production):** the existing single per-set flat, all 500 frames.
- **Arm B:** five per-group flats. **No new builder code is needed** —
  `build_sky_flat.sh` already takes `--select=<list-file>`, and each `gN.list` is
  exactly the absolute-path frame list it expects. Group *k*'s frames are
  calibrated by group *k*'s own flat.

**REGISTRATION MUST BE PINNED ACROSS ARMS — non-negotiable.** `register -2pass`
re-chooses its reference from image quality and **the calibration changes that
choice** (measured: one flat picked image 1 and a 4896×3616 canvas, the other
image 2 and 4887×3641). Without pinning, the reference is a second knob hiding
inside a one-knob design. Use `run_undistort_pipeline.sh --regdata=<lt_.seq>`,
which the differential session built for exactly this.

**Normalization:** run the arms `--nonorm` for the pixel instrument, plus one
production-normalized pair. The shipped `-norm=addscale -output_norm` absorbs
only 0.3–0.4% of a calibration difference on the OBJECT but moves the background
pixel field **48.6%** (a pedestal artefact — `psf`'s local annulus is immune,
regional medians are not), so the pixel field is valid on `-nonorm` arms only.

## Pre-register before you build, and commit it first

Two sessions running have made this the practice and it is why their results are
trustworthy. Write the prediction to a tracked record and commit it **before** the
arms exist.

- **Shape and sign.** Each group's flat should depart from the set flat by roughly
  half the half-to-half term at the ENDS (~1.7%), **with opposite sign at the two
  ends and near zero in the middle group.** That sign structure is strongly
  falsifiable — predict it explicitly.
- **Monotonicity.** The flat-to-flat ratios should be monotone in group order if a
  smooth within-burst evolution is the driver. `flat_odd_component.py --ratio`
  measures what differs between two flats with no model and no fit — use it.
- **Axis.** The change should be T/B dominant, per the 11.6× excess. **If it comes
  out L/R dominant, the attribution is wrong and that is the finding.**
- **Delivered.** ~1:1 of the flat change, from the differential's transfer.
- **What would falsify** the conclusion that narrowing the window helps.

## The risk this design carries, and it must be measured not argued

Each group's sub-stack would be calibrated by a DIFFERENT flat, and the registry
names the within-burst flat term as *"the measured member-to-member differencer
within a set"*. So per-group flats could reduce every member's own residual while
making members differ MORE from each other — and the compose is a plain mean, so
that difference lands in the product.

**Measure both levels:** the per-member (sub-stack) residual and the composed
product. `member_separation.py` is NOT the instrument — it measures positional
residuals, not photometric ones. Use the differential instrument at member level.

## Controls — all four run and reported

1. **FLOOR at the group's own depth.** Build two flats from INTERLEAVED halves of
   ONE group (50 + 50). Interleaved halves span the same sub-burst, so any
   time-evolving term cancels and only the build floor remains. That floor — not
   the inherited 250+250 figure — is what a per-group difference is read against.
   A floor is a measurement, not a subtraction of two numbers you happen to have.
2. **IDENTITY.** Run arm B's machinery with all five "per-group" flats set to the
   SAME per-set flat. It must reproduce arm A exactly; the groups route is
   measured bit-reproducible on this rig, so expect a **true zero**, and if it is
   not zero, find out why before reading any number.
3. **PLANTED.** The differential harness's known ramp, to fix the recovery
   systematic that every delivered figure is then corrected against.
4. **SELFTEST.** Anything that ships falsifies its own mechanism in process —
   break it, watch it go RED, restore, watch it catch again. Argued verification
   does not count; it has failed here three times for three different reasons.

## Fenced — and the first one is the trap this item invites

- **DO NOT SIZE A FLAT WINDOW FROM ELAPSED TIME. The time-dose hypothesis is
  DEAD on its own pre-registered falsifier:** set-04 ran 777 s against set-03's
  1497 s, so a time-driven term predicted 0.52×; it measured **1.200×** — the
  SHORTER burst produced MORE half-to-half change. Group count is a route
  property here, not a duration policy, and burst duration must not be
  re-proposed as the explanatory variable.
- **DO NOT JUDGE THIS ON STACK CORNER SPREAD.** A four-corner box metric is not a
  gradient measure on a structured field — it measures which bit of sky landed in
  four boxes — and corner-vs-centre is self-fulfilling for flat contamination by
  construction. The registry's named candidate is the **grid-fitted ramp slope**
  (reproducible to 7% between independent builds). Report it as the candidate it
  is: changing an acceptance measure needs the owner's ratification.
- Raw-domain de-sky (`--desky`, 31× regression); degree ≥2 backgrounds (parity);
  the entire self-referential flat-correction class; additive matching for the
  corner term; GraXpert Division on MW fields; a Gaia catalogue check; the
  absolute catalogue-free object tilt (dead, both blockers).
- **No acquisition answer.** The data is a given, and a real flat is the
  divergence's removal CONDITION, not the route. The fix lives inside the
  flatless route — that is the mission.

## Scope — state it before the result exists

This measures whether narrowing the flat window improves the calibration of ONE
set. **It does not establish a policy.** A policy needs the corpus and the
owner's ratification, and the acceptance measures do not loosen to accommodate
it. Nor does any outcome speak to the flat's share of the absolute object tilt,
which stays UNTESTED, or resurrect the 3.11%/241σ figure, which stays UNVERIFIED.

## Acceptance — executable, each with what you ran

1. The prediction is committed BEFORE the arms are built.
2. All four controls run and reported, with the discrimination against the
   measured floor in the form the standard asks for.
3. Both levels measured — per-member and composed — and the member-to-member
   risk answered with numbers rather than dismissed.
4. The axis decomposition (T/B vs L/R) reported, and the headline written to the
   axis the result actually moved.
5. Every number carries its instrument, n, and the box's `uptime`.
6. Five guards and every selftest PASS; `--plan` still walks a session clean.
7. Anything in-house that ships carries its removal-conditions row in the same
   commit; `prompts/REPORT.md` updated; this file deleted in it.
8. `pgrep -f` any chain script before editing it — and do not leave watcher
   loops whose own `pgrep` pattern matches each other, which is how four
   immortal shells were left behind last session.

## The owner's gate

Anything aesthetic is decided by their eyes on the full-frame 16-bit PNG, never
by a metric. Note that `render_tier.sh` exits 7 without a ratified `render` block
and july31/set-03 has none, so an eyes-on-finals pass is gate-blocked
(`BACKLOG:render-ladder`) — preserve both arms' linear stacks, tagged, and say in
the report that it is waiting on the gate rather than forgotten.

## Honest failure

**The NULL is the most valuable result this program produces**, and it has banked
two. If the per-group flats differ from the set flat by less than the build floor,
if the improvement does not reach the product, if members diverge more than each
gains, or if the axis comes out wrong — say so plainly with the numbers and
register it. Never "fixed/final/matched/close". A killed hypothesis becomes a
dead-end entry with its numbers before anything else is tried.

Verify everything in this brief against the repo before relying on it.
