# Fresh-session brief — the flat differential: does the flat's dose reach the object?

**SELF-RETIRING.** Delete this file in the commit that lands the result.

The absolute object tilt is a registered DEAD END: a linear sensor-fixed mode is
exactly degenerate with the per-star and per-block nuisances under translational
drift, and for a fixed camera the atmosphere is sensor-fixed too, with the same
airmass shape as the flat's residual. Read that entry in `docs/dead-ends.md`
before anything else. This brief is the measurement that survives both blockers,
and the reason it survives them is its entire justification.

**The question, stated so it cannot drift:** two flats of the same optical state
but different sky dose, applied to the SAME lights through the SAME chain — how
much of the flats' difference survives to the delivered object?

## Why this kills both blockers — the design's whole case

**Blocker 1 dies because there are no free nuisances left.** The absolute
measurement modelled `m_ij = M_i + z_j + a·u_ij` and had to fit `M_i` (per-star
brightness) and `z_j` (per-block zero point). Under a pure translation
`u_ij = u_i + c_j`, the signal splits into `a·u_i` + `a·c_j` and those two fits
absorb it exactly. **Here both arms are the SAME star in the SAME frames**, so
`M_i` cancels identically and `z_j` cancels identically. What is left is
`Δ(x) = g_B(x) − g_A(x)` with nothing free to absorb a linear mode. The
degeneracy is not mitigated — it is structurally absent.

**Blocker 2 dies for the same reason.** Identical frames carry identical
extinction and identical skyglow at every sensor position. Both cancel in the
difference. What survives is only the two flats' imprint difference.

**REQUIRED, and it is the sharpest thing in this brief:** the selftest must
demonstrate that immunity **on the same pure-translation panel that broke the
absolute design** — the fixture in `object_tilt.py --selftest` step 4a, where a
planted +0.100 mag returns −0.046 ± 0.0001 and the lever collapses to 0.00 px.
The differential instrument, on that same panel, must recover a planted flat
difference correctly. Same fixture, opposite verdict, one screen.

## The arms — one knob, and the knob is the flat

Verified on disk: all 12 sky flats are present at
`sessions/<night>/work/masters/skyflat_set-NN.fit`.

- **Lights:** `aug09/set-05`.
- **Arm A (production):** set-05's lights ÷ `skyflat_set-05` — the real shipped
  calibration.
- **Arm B (counterfactual):** the same lights ÷ `skyflat_set-01`.
- Everything else identical: same darks, same undistort chain, same registration,
  same stack, same geometry.

**Why this pair, from the record** (`datasets/aug09/corpus_flat_odd_component.json`,
edge geometry):

| flat | L/R | edge dipole x |
|---|---|---|
| aug09/set-01 | 1.1081 | −0.1026 |
| aug09/set-05 | 1.4772 | −0.3853 |

**Δdipole 0.2827 — the largest within-night contrast in the corpus** (july31
0.2152, aug06 0.1342). **Within-night is required, not convenient:** focus
recalibrates per session, so a cross-night flat pair differs in OPTICAL state as
well as sky dose and the difference stops isolating the sky term. That is the
same argument the L/R decomposition used to prove the L/R term is sky — focus is
untouched inside a night, so a within-night change on fixed optics can only be
sky. Do not pair across nights.

**Depth:** even-stride sample to preserve the FULL drift span — the span is what
smears the imprint, and it is the quantity under test. Every 4th frame of set-05
gives 125 frames over the same 1497 s. Do not use a contiguous block.

## The ratified rule, and the exemption this brief claims

`README.md` step 1b, user-ratified: **"A flat calibrates ONLY the exact frames it
was built from — cross-set reuse and any shared/union flat on a multi-set combine
are banned."** Arm B is exactly that banned manoeuvre, and the ban is correct as
a product rule.

**The exemption, stated narrowly:** this is a DIAGNOSTIC arm. Its outputs are
tagged as such, never delivered, never composed into anything, and never the
verdict on a render. The precedent is already in the registry — the
iterative-flat session handed set-05's frames set-01's flat as a positive
control and it returned set-01's value, closing 93.4% of the distance. Same
manoeuvre, same direction, already accepted as a control. If arm B's product
escapes into `web/results/` untagged, that is a defect in this session, not a
naming preference.

## Two instruments, and the first needs no in-house code at all

**PRIMARY — the pixel ratio.** Both arms run identical frames through identical
registration, so the two stacks are pixel-aligned. Siril `fdiv` of arm B by arm A
therefore yields the delivered imprint-ratio field **directly**, and Siril `stat`
regional medians measure its gradient. No cross-match, no fit, no photometry — the
tool does every pixel operation and every measurement. Use `fdiv`, never `idiv`
(it clips at 1.0 silently), and read the LINEAR stacks, never a stretched surface.

**CONFIRMING — matched-star flux ratio.** The same star sits at the same pixel in
both arms, so no cross-match is needed here either. Reuse `object_tilt.py`'s Siril
`psf` aperture photometry, which is already built, already aperture-invariance
tested, and already background-subtracted against its own local annulus. This
measures the effect on the OBJECT's own flux — the defect's stated harm — and it
is independent of the pixel-ratio instrument. Two instruments, one question.

**Report both. If they disagree, that disagreement is the finding**, and neither
number ships until it is attributed.

## The normalization trap — the one real confounder, and it is live

Every light stack pins **`-norm=addscale -output_norm`**, whose per-frame
coefficients are computed from the frames' own statistics. Those statistics
DIFFER between arms because the flats differ, so **the normalization partially
absorbs the very difference under test.**

Required handling: run the diagnostic arms at **`-nonorm`** (a stated deviation,
diagnostic-only, both arms identical), **and** run one pair at the production
`-norm=addscale -output_norm` to MEASURE how much it absorbs. That absorption
figure is itself worth recording — it tells any future corrective how much of a
calibration difference the shipped chain silently swallows.

## Pre-register before you run, and commit it first

Write the prediction to a tracked record and COMMIT it before the arms are built
— the last session did this and it is why its corpus result is trustworthy.

- **The direction and the shape** of the expected ratio field, taken from the two
  flats' own measured L/R and dipole.
- **The upper bound:** the delivered ratio is the flats' ratio SMEARED by the
  drift, so `|delivered| ≤ |flat ratio|`. State the predicted smear factor from
  the drift span before measuring it.
- **What would falsify** a "the dose reaches the object" conclusion.

## Controls — all four run and reported

1. **IDENTITY / floor.** Run both arms with the SAME flat. The predicted ratio
   field is exactly 1.000 everywhere. The groups route is measured
   bit-reproducible on this rig (all-nil in both directions, both arms), so this
   floor should be a **true zero** — and if it is not, something
   non-deterministic is in the arm and must be found before any number is read.
   A floor is a measurement, not a subtraction of two numbers you happen to have.
2. **PLANTED difference.** Divide one arm's flat by a ramp card of known edge
   ratio (Siril `fdiv`), predict the delivered ratio, measure the recovery.
   **Report the discrimination ratio against the floor** — the iterative-flat
   NULL met 48–62×, the object-tilt instrument managed 0.20× and that is why it
   was unusable.
3. **DEGENERACY IMMUNITY.** The pure-translation panel above.
4. **APERTURE INVARIANCE** at two radii on the photometric arm.

## Scope — state it plainly so the result cannot be over-read in either direction

This measures the **difference of two imprints**. A null means *the flats' dose
difference does not reach the object* — which **bounds** the absolute tilt (it
says the object's sensitivity to a Δdipole of 0.283 sits below the measured
floor) — it does **not** equal the absolute tilt, and it cannot resurrect the
3.11%/241σ figure, which stays UNVERIFIED. A positive result gives the delivered
sensitivity to a known dose difference, which IS the number a corrective needs.
Neither outcome licenses a statement about the flat's share of the total defect;
that remains UNTESTED, per the registry.

## The second half of the original item — explicitly DEFERRED, with what unblocks it

`BACKLOG:calibration-evidence` also asks for a with/without judgement pair on
FINALS, owner's eyes, unresolved-starlight preservation as the metric. **Deferred
this session, for a stated reason:** `render_tier.sh` is user-gated and stops at
exit 7 without a ratified `render` block, which this dataset does not have
(`BACKLOG:render-ladder`). Preserve both arms' linear stacks, tagged, so the eyes
pass runs the moment that block is ratified — and say in the report that it is
waiting on the gate, not forgotten.

**Correct the item while you are there:** it claims "both flats exist for
set-01/02", meaning the de-skied pair. Verified live — **no de-skied flat exists
anywhere on disk**, so that half is not stageable as written. The de-skied arm is
a registered 31× regression anyway; two shipped-builder flats of different sky
dose are the better pair and are what this brief uses.

## Fenced — do not resurrect

Raw-domain de-sky (`--desky`, 31× regression); degree ≥2 backgrounds (parity);
the entire self-referential flat-correction class; additive matching for the
corner term; GraXpert Division on MW fields; a Gaia catalogue check (trailed
stars at 17″/px); corner-vs-centre or four-corner-box flatness as evidence about
this defect (self-fulfilling by construction); the absolute catalogue-free tilt
(dead, both blockers). And no acquisition answer — the data is a given.

## Acceptance — executable, each with what you ran

1. The prediction is committed BEFORE the arms are built.
2. All four controls run and reported, with the discrimination ratio in the form
   the standard asks for.
3. The selftest falsifies the instrument's own mechanism in process — break it,
   watch it go RED, restore, watch it catch again — including the
   pure-translation panel demonstration.
4. Both instruments reported; any disagreement attributed, not averaged.
5. The normalization absorption is measured, not assumed.
6. Every number carries its instrument, n, aperture radius, background form, and
   the box's `uptime`.
7. Arm B's outputs are tagged diagnostic and never enter `web/results/` as a
   deliverable.
8. Five guards and every selftest PASS; `--plan` still walks a session clean.
9. Anything in-house that ships carries its removal-conditions row in the same
   commit; `prompts/REPORT.md` updated; this file deleted in it.
10. `pgrep -f` any chain script before editing it.

## Honest failure

**The NULL is the most valuable result this program produces**, and this program
has now banked two of them. If the dose does not reach the object, if the floor
swallows the signal, or if the two instruments disagree irreconcilably — say so
plainly with the numbers, register it, and state what it bounds. Never
"fixed/final/matched/close". A killed hypothesis becomes a dead-end entry with
its numbers before anything else is tried.

Verify everything in this brief against the repo before relying on it.
