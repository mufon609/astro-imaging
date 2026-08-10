# Consistency tiers — what is constant at which scope, and what that means for combining

The narrow question ("why do aug06's corners smear") has been answered. This is
the wide one: **every calibration input has a scope over which it is valid, and
the pipeline is correct only when each input is derived at its own scope and no
finer.** Getting a scope wrong in either direction breaks something:

- too COARSE → one night's state serves another (the problem the per-set model
  change was made to fix);
- too FINE → members that should be mutually consistent stop being so (the
  problem the per-set model change caused).

Both failures have now been measured here. The second is worse, because it
breaks the project's core purpose.

---

## 1. The tiers

| tier | what is constant | what is derived at this scope | what breaks if derived FINER | what breaks if derived COARSER |
|---|---|---|---|---|
| **INSTRUMENT** — camera + lens + focal | the optical design, sensor geometry, pixel scale, the lens's distortion *family* | the lens identity (`LensModel`, focal), the sensor geometry that sets ρ, the choice of route | — | a different lens/focal silently warps on the wrong profile (the preflight already stops this) |
| **OPTICAL STATE** — a focus setting | the distortion *coefficients* | the distortion model | **members stop agreeing** — MEASURED 2.99 px corner disagreement, visible star doubling, a product failed by eye | a state-mismatched model leaves residual — MEASURED set-01 off-axis 0.82 vs 0.48 px |
| **NIGHT / SESSION** — one outing | thermal regime, sky transparency family, the dark current | the **master dark** | more darks per set than the thermal regime justifies; no benefit | darks from another night mis-subtract the thermal signature |
| **SET** — one pointing, one continuous run | the sky gradient the set sees, the pointing, the drift geometry | the **synthetic sky flat**, the cull, the group derivation | — | a flat from another pointing carries the wrong sky; MEASURED as the reason flats are per-set |
| **PRODUCT** — what gets composed | nothing; this is where tiers must MEET | the combine's membership, framing, reference, weighting | — | — |

**The rule the arc violated:** the OPTICAL-STATE tier is not automatically the
SET tier. A state changes when focus changes. Focus is recalibrated per session
and *sometimes* mid-night — so a state may span a whole night, several nights, or
part of one. **Assigning the model to the SET was a guess about the state
boundary, not a measurement of it**, and the guess was finer than the truth.

## 2. What is measured about where the state boundary actually is

- **A fitted model is not reproducible to better than ~3 px** in the outer field.
  Four independent fits of ONE set span 0.36–6.30 px (median 3.22); the three
  *between-set* models span 4.01–10.99 px (median 7.04). The distributions
  OVERLAP. So the coefficient differences that were read as "each set is its own
  optical state" are **not separable from the fitting procedure's own noise**.
  The 0.47 px equivalence bound used to adopt per-set granularity is exceeded by
  7–23× by refits of a single set — it never discriminated anything.
- **One shared model beats per-set models cross-night**, one knob, same member
  pair: corner 3.38 vs 5.34, outer 2.07 vs 2.73, mid 1.09 vs 1.31, centre 0.41
  vs 0.92.
- **Every combine ever accepted in this repo used ONE model.** july14 under the
  july14 fit; july31 under it inherited (the one the owner passed); aug06 under
  three, failing.
- **Siril's own design assumes one optical state per sequence** —
  `register -disto=` applies one solution to a whole sequence, and the polynomial
  cancels only because every member shares it.

Taken together: **the evidence supports a COARSE state boundary — one model per
instrument-state, spanning nights — and does not support the per-set boundary.**
The owner's field experience (the generic model combined sets, cross-set and
cross-night) is consistent with all of it.

**What is NOT settled:** whether a genuine refocus mid-campaign needs a new
model, and how to detect one. That is the real question the per-set change was
reaching for, and it needs a state-CHANGE detector, not a per-set default.

## 3. Where the industry puts each tier

Stated first, per the standards-first rule.

| tier | industry practice | source |
|---|---|---|
| optical distortion | **derived per exposure from the sky**, carried in the exposure's own WCS (TPV/SIP); no shared instrument model at all | SWarp/SCAMP (Astromatic), the SDSS/CFHTLS/DES/Pan-STARRS lineage; PixInsight ImageSolver + StarAlignment with distortion; APP |
| coaddition | **resample every input onto one output WCS grid** using its own solution, then combine | SWarp |
| dark | per thermal regime (temperature + exposure + gain), reused across nights when the regime matches | universal |
| flat | per optical configuration, reused until the configuration changes | universal — **and this repo deviates deliberately: synthetic per-set sky flats, which is the project's point** |
| background matching | per input, before coaddition | SWarp `SUBTRACT_BACK`; PixInsight LocalNormalization/NSG; APP LNC |

The distortion row is the one that matters here: **the industry does not have
this problem because it does not have a shared instrument model to get the scope
of.** Distortion is a property of each exposure's astrometric solution.

## 4. The architecture this points to

Three layers, each at its own tier, none of them guessing a boundary:

1. **Within a set — keep the lens warp.** A far-drifting untracked set cannot be
   registered by one homography, and single ultra-wide trailed frames do not
   plate-solve. This is the measured reason the undistort route exists and it is
   unchanged.
2. **At the combine — resample astrometrically, not by a shared model.** Each
   member is plate-solved (MEASURED working natively: `seqplatesolve -order=3`,
   388/371 stars, ~0.9 px residual, agreeing with astrometry.net to 0.001°) and
   resampled onto one output WCS by its own solution. This makes cross-night
   identical to same-night by construction and removes the state-boundary
   question from the combine entirely. **The tool is SWarp** — packaged for this
   distro (2.41.5-3), not installed. Siril cannot do it: `register -disto=` is a
   shared-solution facility, MEASURED (a member warped by its own solution
   disagrees with its own unwarped self by 8.5–9.5 px).
3. **Detect state CHANGE instead of assuming it.** Replace "one model per set"
   with "one model per instrument-state, plus a measured trigger for refitting".
   The trigger is the same instrument the compose gate already uses: if members
   built under the incumbent model disagree beyond the gate's threshold, the
   state moved and a refit is due. That is a measurement, where the per-set
   default was a guess.

## 5. The instrument — FIXED, and what it found on the way

**Done.** `member_separation.py` now bins by each member's OWN field radius, and
fixing it exposed a larger fault than the zoning: it had been cross-matching the
REGISTERED copies, which do not share a coordinate frame. `seqapplyreg
-framing=max` on a variable-size sequence gives every output its own origin —
MEASURED 611.9 px apart in x on the 28-member union, constant to 0.4 px across
the field, i.e. a pure translation. Two consecutive members of ONE set shared
zero stars within 1 px and 67 of 2000 within 12. Every number the old instrument
produced was a chance nearest-neighbour distance between two offset frames; it
ranked its calibration cells correctly by luck of a monotone confound and
starved to UNMEASURED exactly where the offsets were largest.

The fix needed no extra solves: `register -2pass` already writes one homography
per member into the `.seq`, so each member's own `findstar` positions push
through `H_ref⁻¹·H_m` into the reference member's frame by construction. Full
numbers, the executed falsification and the re-measured threshold anchors:
`docs/dead-ends.md` and the ledger entry
`compose_gate_rezoned_by_member_field_radius`.

**What it measures now**, on the accepted 28-member union — 0/378 pairs
unmeasured against 378/378 before, in 12 s:

| zone (member-own field radius) | median | p90 | max |
|---|---|---|---|
| centre 0.00–0.25 | 0.22 px | 0.39 | 0.80 |
| mid 0.25–0.55 | 0.48 px | 0.89 | 1.56 |
| outer 0.55–0.80 | 1.30 px | 2.49 | 4.97 |
| corner 0.80–1.01 | 2.43 px | 4.94 | 7.53 |

**And it answers §2's open question directly: the disagreement is not a function
of night, or of set.** Same-night pairs median 2.44 px, cross-night 2.39,
same-SET 2.21. It is a function of member-own field radius and nothing else the
membership distinguishes. Cross-night combining is exonerated as a source; the
within-set compose is implicated — independently of the star-shape ladder that
found the same thing (`AUG06_MEMBER_EDGE_report.md`).

The 4.07 px "cross-night state difference" stays UNMEASURED: it was taken with
the canvas zoning *and* the broken frame.

## 6. Order of work this implies

1. ~~**Fix the instrument** (§5).~~ **DONE** — and it found the frame bug above.
2. **Re-anchor the thresholds — a USER decision.** The 0.35/1.00 px bands belong
   to the broken instrument. Re-measured on the fixed one the six anchors read
   0.14 / 0.21 / 0.38 / 1.23 / 3.04 / 3.28: the ordering holds and the floors
   barely move, but the user-PASSED product's pair crosses PASS→WARN and the
   never-accepted cell WARN→BLOCK. Nothing was re-anchored, because loosening an
   acceptance measure needs ratification.
3. **Re-measure the state boundary** with the fixed instrument: is aug06 one
   state or three? Answerable from members that already exist — and §5's
   night/set nulls already constrain it.
4. **Trial SWarp** as the standardization candidate (§4.2). The case for it is
   now measured rather than argued: the members' own astrometric solutions agree
   to 0.10 px median where the homography compose loses 1.06 px of FWHM.
5. **Only then** revisit corner-true fitting — under §4 it may not be needed at
   all, since astrometric resampling does not care how good the lens model was.
