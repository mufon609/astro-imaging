# Implementation report — what gets built next, and how it is judged

The rebuild-verification session's findings, distilled to the work they
demand. Companion to the prompt briefs in this directory; the audit session
checks each item against the acceptance stated here. Ordering within each
block is the priority.

## Prompts ready to run (in this directory)

- **[`COMBINE_FLAT_WINDOW_PROMPT.md`](COMBINE_FLAT_WINDOW_PROMPT.md)** — STAGED,
  not cleared: it is a multi-set member rebuild and needs the owner's word that
  the machine is free. Arm A exists in full (the whole 12-set corpus is per-set
  flats); arm B barely exists, so the bill is per-group flats plus a member
  rebuild for every set entering the test combine.

`COMMENT_SWEEP_PROMPT.md` is a **standing utility, not a queue item**: it does
not retire, and it is run on demand rather than scheduled here.
`ORACLE_TEMPLATE.md` and `ADVERSARY_TEMPLATE.md` are templates the PM customises
per engagement, not items — the four-session team is OPTIONAL and specified in
`PROJECT_MANAGER_PROMPT.md`.

## Waiting on the owner — NOTHING IS. All four are ruled; this section is the record of what they decided

Every item this section carried has been decided. It survived as "waiting"
through two handoffs because the decisions landed ELSEWHERE and nobody closed the
row — a record can go stale by being RESOLVED, not only by being contradicted,
and nothing in a stale row is false about the past. **Close the row in the commit
that lands the decision.**

1. **The L1 judge triple — RULED, and the reason is unusual and load-bearing.**
   The owner opened the three surfaces, reported NO visible difference, and
   approved the on-stack level on the instruments. That is what the honest-checks
   system exists for. `datasets/aug06/l1_work/owner_ratification.json`.
2. **The two parallel-session rules — RULED, and in the contract.** The staging
   unit was delegated to the manager and landed at **`b36ef3b`** (the hunk check
   with a mechanical count in front of it; the structural option rejected with its
   reason recorded). The blind-spot sentence was ratified as part of "(a) and (b)"
   and landed at **`64f61d2`** with its tripwire. Both verified present in
   `CLAUDE.md` today.
3. **Starlight preservation as the adoption gate — NOT a pending decision.** It is
   a logged UNCHECKED premise (`datasets/aug06/l1_work/unchecked_premises.json`)
   and it blocks nothing. It becomes live only if someone proposes that instrument
   as the acceptance gate for a NEW step.
4. **The per-member trim — RULED: WAIT, and the corner defect is REAL.** The
   owner settled the question three sessions ran without: **the degradation is
   VISIBLE to their eye on the full-frame render** — *"they are already bad in the
   full frame render. i can see it and no render will make it look better - just
   more obvious."* So it is not a below-threshold residue, and the render tier
   cannot improve it. **Because the cause is unknown, any step forward from here
   is a BANDAID** — the owner applying `CLAUDE.md`'s own rule directly. The trim
   stays refused, and the stated reason is the one to carry: crop and we may never
   find the real cause, while losing frame size, SNR-over-time, and possibly final
   quality, *"because there are issues with an unknown cause, so how deep or
   subtle the issue is is not known."* **Keep digging is the ratified direction.**

**The owner's own mechanism for the corners, recorded because it is field
knowledge and it matches what was measured.** The far-corner stars are ALWAYS at
the edge of a member's frame, so the union corner is built exclusively from
worst-case samples — *"the stars being stacked are the worse images possible."*
The corner work measured exactly that axis independently: the degradation is on
MEMBER-OWN FIELD RADIUS (+0.53 px per unit rho, 3.6 SE) and coverage depth
contributes nothing (0.2 SE). The open half of the owner's statement is whether
properly centred frames would change it, which is an acquisition-side question
and therefore NOT a route this repo takes (MEMORY: the data is a given).

## Landed — the artifact-first audit: a third of the register was wrong, and the method that found it

**THE METHOD IS THE DELIVERABLE. Derive a check's target list from the ARTIFACT —
the config's actual keys, the file's actual mode, the actual `open()` calls, the
actual call sites — never from anyone's description of it, including your own.**
The cheap tell: the check and the thing checked get named by the same person in
the same act, so a check written against a REMEMBERED name inherits its author's
vocabulary. Every partial target list below was produced by a session actively
watching for this failure.

**THE REGISTER: 34 rows checked, 11 defective, plus 3 divergences with no row and
2 stale date columns.** Sampling was mechanical and stated before its output was
read (the 28 files declaring `REMOVAL CONDITION`, tree-path order, stride 5 from
index 3), so no session's sense of which rows looked risky could steer it; the six
went out as FILES, not row numbers, so each row was located from its artifact. The
six returned **4 defects**, which is what justified sweeping the other 28.
**TWO CONDITIONS HAD FIRED WHILE THEIR ROWS READ "not fired"** — row 51's
`rl -loadpsf=` disjunct (`corner-fix-landscape`'s own header reads *"the
FIX-classified route is DEAD"*), cascading to rows 49/50; and row 45's BACKFILL
clause (93 sub-stacks on this rig, **93 stamped, 0 un-stamped**). Rows 51/49/50
were REWRITTEN rather than deleted: `contract_check()` lives in `constancy_fit.py`
and is roster check 18 behind the pre-push hook, so deleting the file would
silently remove a check from the gate.

**A HEADLINE NUMBER THAT EXISTS IN NO RECORD.** The error-model finding shipped as
*"χ²/dof 35.6 on bootstrap errors becomes ~1.1 on frame-based"*. Enumerating every
`chi2_per_dof` in the cited record returns
`[1.5669, 1.8054, 19.2935, 30.3153, 35.5969, 40.9469]` — **nothing in [1.0, 1.2]**,
in BOTH revisions, byte-identical. 35.6 is one binning's bootstrap and its own
counterpart is **1.8054**; the other pairs 40.9469 → 1.5669. **The finding survives
at ~20× either way, which is why it went unchecked.** It failed in the flattering
direction: against an assumed null of 1, "1.1" reads as a near-perfect fit.

**ν IS PER-CALL, NOT A CONSTANT, AND THE NULL IS NOT 1.** `decompose`'s frame-based
SE divides by that call's own `nf` with **no pooling across bins**, so a
significance built on it is Student-t with ν = nf − 1 and its square is F(1, ν).
Measured across the records ν runs **3 to 39**; the null expectation of a reduced
statistic so formed is **ν/(ν−2)** — 3.00 at ν=3, 2.00 at ν=4, 1.05 at ν=39. The
σ-unit keys are renamed `*_t_frame_based` and carry `dof_frame_based` plus the
FORMULA rather than a value, because a number true for one caller in a shared
docstring is the neutral-key defect one layer up. **The corpus record
REGENERATION is deliberately NOT run**: the capability is integrated, the artifacts
still carry the old generation.

**THE GUARD RUNNER WAS UNSAFE TO RUN CONCURRENTLY, AND IT IS THE PRE-PUSH HOOK.**
Five selftests wrote fixtures to FIXED shared paths under `~/.cache/astro-imaging/`,
so two runs destroyed each other. **Three string greps each returned a different
partial list** — `grid_ramp` builds its path with `os.path.join` split across two
lines, so the literal never appears in source and no path grep can see the one
whose log carried the actual failure; an AST walk found the set. Falsified both
ways: pre-change concurrent **4 of 4 runners RED**, post-change **6 of 6 GREEN**,
with a sequential pre-change control GREEN (which is what makes it a race and not a
broken check). It produces false REDs, never false GREENs. The runner had also been
deleting its own logs on exit, so the first occurrence was unattributable.

**A FIX WHOSE DELIVERY PATH EXCLUDES ITS OWN BENEFICIARY — a new class.**
`install_astromatic.sh` states in its own header that it exists to close the
*"VERIFIED and NOT REPRODUCIBLE FROM A CLONE"* gap; `x86_bootstrap.sh` mentions it,
`psfex`, `scamp` and `source-extractor` **zero times each**. Not a design choice —
that script already runs `sudo apt install` 23 times. **PSFEx's field model is
cited in register row 52, the arm validating the κ that rows 51/52/53 rest on.**

**FOUR OF FIVE NEGATIVE TOOL CLAIMS IN `TOOLS.md` WERE WRONG OR OVERSTATED.** A
negative closes routes and never self-corrects — a stale positive is caught the
moment someone tries the thing. The Gaia astrometric catalogue IS installed
(1,521,132,640 bytes) against a row whose downstream clause closed a route;
`reproject` 0.21.0 and `astropy_healpix` 2.0.1 are installed; `help rmgreen` reads
*"Applies a chromatic noise reduction filter"* against a row saying no such tool
exists. **All three FALSE were invalidated by this team's own installs inside 24
hours — a generator problem, which no last-checked date catches.**
**AND "INSTALLED" IS PER-INTERPRETER:** the six tool-layer packages import in
`/opt/astro-venv` and NOT in `~/.local/share/astrometry-venv`, while all 175 python
invocations across `scripts/` resolve to `/usr/bin/python3`, which has none of
them. **`sip_tpv` gates the SWarp route for `compose-homography-smear` and no
script can import it as written.** The convention exists (`$ASTRO_VENV`) and so
does the consumer pattern (`solve_field.py` re-execs into its venv); it was never
applied on the read side. **Gating prerequisite on that route, not a live defect.**

**THE CONVERGENCE TRIPWIRE FIRED FOR THE FIRST TIME RATHER THAN BEING CITED.** Two
sessions argued the same records split from different evidence, both resting on
*"`manifest.tsv` is authoritative"*, which neither had checked. **21 rows, omitting
PSFEx, SCAMP, `source-extractor` and a 1.5 GB catalogue.** What made it fire was
naming the SPECIFIC shared premise as one falsifiable sentence — *"we have
converged, be careful"* names nothing checkable. The `TOOLS.md` restructure is HELD
until the manifest is real: an omission in a file declared authoritative looks like
nothing, which is worse than a wrong claim.

**Numbers:** `docs/dead-ends.md` (QA/scope — the paraphrased-RESULT entry, the
convergence operating condition, the pgrep interval entry), `BACKLOG.md`'s register
and its rules (5) and (8), `TOOLS.md` Tier 3 / Tier 6 / research queue.

### The next batch's input — the cloud signature is ALIVE, on weaker evidence than its headline

**Pre-registered before the run** (`datasets/aug06/cloud_work/cloud_prereg.json`,
committed with no result attached). **Then corrected twice, and the correction is
the finding.**

**THE POSITIVE CONTROL WAS BUILT FROM THE QUANTITY UNDER TEST.** The headline read
`Z_bg +6.07` and `Z_nstars −8.70` on aug06/set-03's 44 excluded frames against a
matched negative control (set-01, worst 44-frame window, `Z_bg −1.80`). But
`recipe.json`'s `stack.why` — **one key over from the `exclude` list** — records the
criterion: *"defect-side robust z >= 3.5 flags exclude"*, census **44 of 44 flagged
on `nstars`, 29 of 44 also on `bg`.** The exclude list IS that flagger's output, so
on this control the signature could not have failed — which is what the item's own
rule forbids.

**WHAT SURVIVES IS NON-CIRCULAR AND IS A FLOOR.** 15 frames were flagged `nstars`
ONLY, so their `bg` robust-z was **below 3.5** — conditioned AGAINST high bg. On
those: **`bg` Z +4.05, n=15**, against +6.41 on the 29 circular ones. Conditioned in
the unfavourable direction, so +4.05 bounds the effect from below rather than
estimating it. `fwhm` was never a cull field, so **Z_fwhm 1.75 is non-circular** and
the frames did not get softer — transparency, not seeing or focus.

**WITHDRAWN:** `Z_nstars` entirely (all 44 were nstars-selected); the claim that
star count carries the signal more strongly than background; and with it the
proposed correction to `intake-culling`'s *"star count is measured blind on rich
fields"* note, **which stands uncorrected.**

**THE LIMIT THAT BOUNDS EVERY FUTURE CLAIM ON THIS SIGNATURE:** nothing establishes
by OBSERVATION that these frames contain cloud. `REPORT.md` calls it a cloud block;
`recipe.json` records an auto-cull on z-flags. **So what is validated is agreement
with the existing auto-cull, NOT detection of cloud** — and the acceptance bar for
this signature can only be *"agrees with, or improves on, the z-flagger"* unless a
block is identified by a record outside the frame-QA fields.

**Scope:** one set, one night, n=15 non-circular of 44 against 456. No threshold
proposed, no cull built, no detector wired.

**GENERAL LESSON, and it outlives the result: a cull is not a positive control for
any signature that uses the fields the cull was made on — check the cull's
provenance before using it as a control.** A partially-circular control usually
contains a non-circular sub-population; find the frames selected without reference
to the field under test. Here the circular headline was **1.5× larger** than the
honest one, and the strongest-looking half was entirely selection.

**Item state, checked rather than assumed** (`intake-culling`, 7 signature rows):
**2 built** (aircraft/satellite; shake/wind, which now fires on 2 of 21 frames),
**1 blocker stale** (cloud — `bg` IS recorded, across 13 sets), **4 open** — of
which light-pollution/moon needs *"background gradient magnitude + bearing"*, a
per-frame quantity **nothing records**, making it a larger unit than the cloud step
rather than a fallback from it.

## Landed during the corner-quality session — the axis is settled, and the crop line the brief asked for is REFUSED by the numbers

**The corners degrade on MEMBER-OWN FIELD RADIUS. Coverage depth contributes
nothing measurable to star shape.** Two axes on the same post-fix product (the
13-member astrometric union, `stack_set-01+02+03_full_wcs.fit`, 1454 frames),
20 boxes of 800 px placed by its own solved WCS, weighted by bootstrap SE:

| | rho coefficient | depth coefficient |
|---|---|---|
| major axis | **+0.53 px per unit rho, 3.6 SE** → +0.38 px over rho 0.13–0.85 | −0.0016 px per member, **0.2 SE** → −0.02 px over depth 2.3–13.0 |
| minor axis | +0.43, 9.4 SE → +0.31 px | +0.0076, 2.0 SE → +0.08 px |
| roundness | −0.057, 1.7 SE → −0.041 | +0.0026, 1.1 SE → +0.028 |

The axes are correlated (r = −0.78) but **not collinear**, which is what makes
this separable: 48.8% of the union canvas carries all 13 members while
member-own radius there still sweeps 0.08–0.80, and a rho band of 0.70–0.86
carries depths from 2 to 13. Both transects were measured.

**The verdict survives the depth-matching rule rather than depending on it** —
six rules over the same Siril fits (top 10/30/100 and three common amplitude
floors): the rho coefficient on major axis stays **+0.51 to +0.59 at 3.6–5.2
SE**, the depth coefficient stays **0.0–1.0 SE**. The trap is live and was
caught firing: on a 200 px series where top-30 reaches each box's own faintest
detection, corr(depth, major) reads **−0.425** and corr(depth, roundness)
**+0.367** — under one common amplitude floor the same boxes read **−0.003** and
**−0.060**. An unmatched median manufactures exactly the corner defect under
investigation.

**Attribution, by a discriminating test: it is the MEMBER's own field, not the
compose.** Four members from three sets, measured at their own field radius,
read major **2.305 → 2.781 px** and roundness **0.951 → 0.863** across rho
0.10 → 0.80 — a +0.476 px rise against the union's own +0.505 px over the same
span. The compose adds a roughly radius-independent **+0.04 to +0.28 px** of
major axis (median +0.13) and no radial trend. So the term is **MEMBER-LEVEL**,
and the compose's contribution is a small offset whose decomposition —
per-member solve error, lanczos4 resampling, residual registration — is
**UNATTRIBUTED**; the test is pairwise cross-matching of the members' own
findstar RA/Dec binned by member-own radius, the astrometric analogue of what
`member_separation.py` measures through `register -2pass` homographies.

**THE DEFECT HAS TWO COMPONENTS AND EARLIER WORDING HERE CLAIMED ONE.** Over 148
member stations, **star SIZE is purely radial**: adding a one-sided term to a
radial model gives **F = 0.7**, x-only R² 0.006 against rho-only 0.486. **Star
ROUNDNESS needs BOTH**: F = **44.6** adding x to a radial model and **19.7**
adding rho to a one-sided one, R² 0.223 x-only, 0.106 rho-only, **0.316
together**. The first pass published "7.1 SE on x against 1.6 SE on rho" from a
fit carrying x + |x_frac| + rho, and `corr(|x_frac|, rho) = +0.93` — the
symmetric term sat in the |x_frac| coefficient and rho was left a collinear
remainder of the wrong sign. Six specifications now, not one: x runs 4.2–7.1
SE and rho 1.6–5.5 SE, and the spread across weightings is decided by the data
— between-station scatter is **tau = 0.0300 against a median measurement SE of
0.0066 (4.5×)**, so weighting by 1/se² over-weights a few low-SE stations while
the random-effects weight 1/(se²+tau²) is correct and lands on the unweighted
answer (x 6.52 SE, rho 4.20 SE).

**The ASYMMETRY itself is model-free and stands.** At matched |x_frac| the two
sides differ: roundness **−x 0.944 / +x 0.882** at |x| 0.6–0.8 and **0.975 /
0.868** at 0.8–1.0, with the sign inverting near the centre. It is sensor-fixed,
not sky: two members looking at sky **1.76–3.01° apart** give azimuth profiles
correlated at **r = +0.889** (roundness) and **+0.916** (major). That is
BACKLOG:`compose-homography-smear`'s exit-edge finding, now measured at MEMBER
level with a matched-radius control.

**AND IT IS ALREADY IN A SINGLE EXPOSURE.** Siril `findstar` on three raws —
debayered, uncalibrated, unwarped, unregistered, unstacked, 8074 stars — reads
the same one-sided term at the same size: roundness **−x 0.861 / +x 0.791** at
|x| 0.6–0.8 and **0.846 / 0.782** at 0.8–1.0, x at **13.8 SE** and **F = 191.8**
on a radial model, holding in a brightest-quartile control (−0.076, −0.035).
Star size is purely radial there too (rho 30.4 SE, x 0.1 SE, F = 0.0). This
rules OUT three mechanisms — within-member registration, the compose, and a
residual of the lensfun distortion model (an uncorrected frame carries no
residual of a correction). **One inherited claim is in tension and is flagged
rather than resolved**: the registry records the major-axis angle tracking field
azimuth in 7 of 8 zones; on these three frames the median PA is near-constant
across 8 azimuth sectors (**spread 15.8°**), the trailing signature.

**ONE OF THE THREE IN-EXPOSURE CANDIDATES IS NOW ATTRIBUTED, by a prediction
with no free parameter.** A fixed mount trails each star by 15.041·cos(dec)·t_exp
arcsec, so across a field spanning **20.9° of declination** the trail length
runs **1.407 → 1.867 px** — a third longer at the low-dec edge, from the EXIF
and the members' own WCS alone. A uniformly trailed star has variance L²/12, so
`major² − minor² = (2.3548²/12)·L² = 0.462·L²`, which predicts a slope of
**2.266 px²** against cos²(dec). Measured on the 148 stations: **2.901 ± 0.542
alone (1.17σ)** and **2.548 ± 0.416 with rho and x held (0.68σ)**. It is
independent of the radial term (`corr(cos²dec, rho) = +0.011`). Variance
partition on the anisotropy: cos²dec 0.164, rho 0.199, x 0.212, **all three
0.519**, each at 6.1–7.4 SE.

**The conversion decides the verdict, so it is stated in the record.** The
`sqrt(w² + L²)` quadrature that reads naturally overstates the prediction by
**2.16×** (4.905 px²), and against that number this same measurement sits **3.70σ
LOW** — confirmation or refutation turns entirely on which was used. **Limit:**
the regressor is 99% collinear with sensor y here, so what is tested is the
MAGNITUDE of a y-aligned gradient, not its direction; what makes it specific is
that its size matches a parameter-free calculation.

**It does NOT close the question.** The one-sided x term and the radial term
both survive at **6.9 and 7.4 SE** with cos²dec held — the corner defect is
three terms and this attributes one. An optical asymmetry and differential
refraction remain unseparated for the other two, neither removable by a better
distortion model. **And the obvious follow-up is dead on arrival: there is no
lever for it.** "Does the effect scale with each field's own dec range" needs
fields with different dec ranges; the 13 members vary by **4.9%** in cos²(dec)
span. Re-measured independently over all 15 recorded sets at a fixed 18.02° field
extent, the cos²δ SPAN runs **0.3060–0.3090 — 1.0% of its mean**; same verdict,
sharper. The within-frame lever is the large one (cos²dec 0.378 → 0.732) and it
has already been used.
**SCOPE CORRECTION on the exposure half of that kill: "no exposure lever either"
is true of the STAGED corpus and FALSE of the RECORDED one.** july27 holds two
sets at **3.0 s** (282 and 253 frames) on the same target (dec 42.39 / 43.68) at
the same plate scale (36.18 / 35.81 ″/px against aug06's 35.58 — the same focal).
Since `L ∝ t_exp`, 3.0 s predicts **1.44× the anisotropy** of 2.5 s, against a
1.0% declination lever and a term the fit resolves at ~6 SE. Raws are off-rig.
**A CANDIDATE with a named confound, not a decisive test:** a different night is
a different optical state and two of the three terms ARE optical, so ρ and x must
be held as the shipped instrument already holds them — and a change in the optics
themselves is held by nothing. The named discriminator
(BACKLOG:`one-sided-band`, hour-angle dependence) still has not run, and the
headers carry DATE-OBS but no site coordinates.

**So: no crop line is handed over, and the corrected prediction is why.** Under
the two-term model the best joint trim measured — keep x_frac ≤ 0.70, no radial
cut — is predicted to move delivered roundness at the four crop corners
**0.911 → 0.938** and the worst box **0.882 → 0.903**, for **15% of every
member's area** and **4 of 20 measured union boxes losing every contributing
member**. A radial cut alone moves star size **2.887 → 2.877 px** at rho 0.80
for 36% of each member, because the members' own major-axis profile plateaus
above rho ≈ 0.5. **These are PREDICTIONS**, from the members' own profiles plus
which members reach each position; only the one-knob A/B settles them. On these
numbers the case for trimming is weak, and the root cause is unidentified —
which is the order CLAUDE.md puts them in.

**The depth axis could not be measured in the background, and saying so is the
result.** A 100-frame member and the 1454-frame union measure the **same**
relative background sigma at the same nine sky positions (median ratios 1.079
and 0.957 for two different members; sqrt-n predicts 3.81), and the
position-to-position pattern is shared (r = +0.89 union-vs-member, +0.98
member-vs-member). Siril `bgnoise` on this field is reading the sky's own
structure, not a random term that averages down, so no depth cost is claimed
from it. What would settle it is a difference image between two equal-depth
halves at the same sky, which isolates the random part.

**Two findings nobody was looking for.** (1) **Every per-set stack in
`web/results/aug06` — and its judge PNG — is `REGMODEL=starpair REGUNDIS=False`,
the pre-fix route**; only the `set-01+02+03` unions are astrometric. This
session nearly used them as a constant-depth control. set-01's carries the
registered defect plainly: roundness **0.746/0.672/0.629/0.569** at RA
300.0/298.1/296.6/294.2 against 0.960 at RA 315.0 — a sky-fixed band at the
sky position the registry already names (RA 294.86), not a radial profile.
(2) The header-derived depth map is verified by the tool, not asserted: of 3636
boxes the geometry calls covered, Siril calls **0** entirely uncovered.

**The delivered numbers, for the eye that started this.** The crop the owner
judges spans major **2.480 px / roundness 0.951 at centre** to **2.705–3.065 px
/ 0.843–0.981 at its four corners**. That is a residue, not the defect the owner
remembers: the compose fix took the large one (0.92 → 0.58 roundness), and what
is left is +21% on star size and −0.11 on roundness at worst.

**Premises this rests on and did NOT test:** that member-own radius measured
from each member's own canvas centre is the right optical origin (the group's
own drift smears a sky point over ~250 px of a 5769 px frame, ~4%); that a
member's own star shape is the optics rather than optics-plus-within-group
registration (the four members agree tightly and the registry's 136k-star raw
measurement agrees, but no single-RAW arm was run here); and that the +x
asymmetry is one mechanism rather than two superposed.

**Numbers:** `datasets/aug06/corner_work/corner_quality.json` (every box with
its instrument, n, and faintest admitted amplitude),
`shrink_prediction.json`, the 15 `shape_*.json` / `regional_noise_*.json`
records, and the two reproducers `two_axes.py` / `shrink_prediction.py` beside
them. `member_separation --selftest` re-run on the live sequence first, both
numbers reproducing to the digit; its register row updated.

## Landed during the L1 build session — the arms separate on the primary surface, and the supplement splits

**Both arms built, neither falsifier fired, and the pre-registered DIRECTION holds
on the surface the pre-registration named.** Union (13 members, 1454 frames, one
knob), paired retained on the inherited lattice:

| channel | arm A per-frame | arm B on-stack | separation |
|---|---|---|---|
| Red | 0.8609 ± 0.2118 | 1.6364 ± 0.2871 | 2.17 SE |
| Green | 0.9399 ± 0.1955 | 1.9367 ± 0.3162 | 2.68 SE |
| Blue | 0.9473 ± 0.0838 | 1.4688 ± 0.1745 | 2.69 SE |

`falsifier_arm_A` NOT REFUTED — the lowest reading anywhere is union Red 0.8609,
**0.18 SE** below the 0.90 line against a 2 SE requirement. `falsifier_arm_B` NOT
REFUTED — 2.56/3.28/3.26 SE *above* the line. CONFIRMED-AS-EQUIVALENT does not
fire: the arms separate in all three channels. **retained_A < retained_B in 11 of
12 channel-surface cells**, which is the mechanism's own prediction.

**The supplement SPLITS and that is reported, not resolved.** set-01 separates at
2.59/2.09/1.47 SE; set-02 does not, at 0.85/0.03/0.48 SE. The heterogeneity gate
passes (1.38/1.61/1.44 SE) so inverse-variance combining is permitted:
**−0.1079 ± 0.0457 (2.36 SE), −0.0644 ± 0.0483 (1.33 SE), −0.0247 ± 0.0441
(0.56 SE)** — direction in all three, significance only in Red.

**AUDITED, and the audit changed what the result LICENSES.** The four-surface
audit passed on all four pre-agreed questions, and independently re-derived the
separations from raw `delta_slope`, bypassing `retained` entirely —
2.1739/2.6812/2.6941, identical to nine decimals. Two corrections landed:

- **The union answers the STATISTICAL question; the supplement licenses the word
  STARLIGHT.** The power criterion had two clauses and the SE argument answers
  only one. The shift-null asks whether the predictor registers with the image at
  all, and on the union CONTROL it does not (p 0.266/0.252/0.230). It IS detected
  on the union's arm B surface (0.022/0.000/0.036) and on both powered per-set
  controls (0.000–0.043). So both halves are load-bearing, for different halves
  of the claim.
- **The separation is driven by arm B moving, not arm A** — and the SIGNS
  decide what it recommends. Union paired deltas: arm A −1.3851/−0.8292/−0.7158
  at **0.66/0.31/0.63 SE — consistent with zero**; arm B +6.3361/+12.9340/+6.3711
  at 2.22/2.96/2.69 SE. `retained_A < retained_B` holds, but the honest sentence
  is **the on-stack plane REVEALS the starlight relation while the per-frame step
  leaves it where it was** — not that per-frame costs starlight. Those two
  readings are close in words and **opposite in what they recommend**: the first
  leaves the preservation criterion neutral on per-frame, the second would count
  against it. Nothing here counts against per-frame on preservation grounds.

**One loose end closed rather than left open:** "the effect grows with sky span"
is REFUTED as the explanation of the supplement split — the two powered sets'
excursions are 4.5827° and 4.5971°, **0.31% apart**, against separations of 2.59
and 0.85 SE. It may still apply to union-versus-per-set, which is untested.

**The least comfortable sentence: by this session's own pre-committed criterion
the PRE-REGISTERED PRIMARY SURFACE IS UNDER-POWERED** (control shift-null p
0.266/0.252/0.230). It separated anyway, because a difference's significance is
independent of the shared baseline that sets the ratio's scale. The powered
surfaces show a much smaller effect (0.00–0.18) than the union (0.52–1.00). Both
are true; the verdict picks between them only by rule, not by preference.

**A NULL CONTROL CAUGHT A WRONG METHOD BEFORE IT SHIPPED.** The control rebuilt
from raws composes to a union **pixel-identical to the shipped one (0 of
101,278,350)**, so its paired reading had to be exactly 1.000 — it read 1.069,
because crops derived from each surface's own plate solve differ by 60–114 px on
a 31.5° field. Siril's own detections settled it: **33,465 of 33,465 stars at
dx +0.000 / dy +0.000**. Re-cropped on the shared pixel grid the control reads
**1.0000 ± 0.0000**.

**Reproducibility, measured rather than assumed:** all 13 members rebuild
**bit-identical (0 of 893,212,122 px)** across a PIPEREV change, which is what
makes the pinned donor *the control's own registration* rather than a stand-in.
`--regdata-dir` verified at production geometry — canvas frozen (5830×3958 both)
while **100.00% of pixels move**, because a pin that worked by disabling the
treatment would also freeze the canvas.

**Four defects found by executing the route:** `run_undistort_groups.sh`
hardcoded `BKGLIGHT=none` (an arm's product denying its members' treatment);
`run_corpus_combine.sh` used a deny-list, so this experiment's arm dirs would
have been composed into the deliverable corpus; the starlight instrument had no
retry across ~140 sequential archive queries and discarded a whole lattice on one
blip; and its stat regex could not parse `Sigma: -nan`, silently dropping any
zero-variance region.

**`member_separation --selftest` now runs** on the sequence arm A produced: known
displacement 3.086 px measured back as 3.086 px, and the incident reproduces at
**89 matches without re-basing against 1905 with it**.

**Judge triple** (like-encoded, one shared crop, per-product linked autostretch):
`web/results/aug06/judge/set-01+02+03_{l1crop,l1bkgframe,l1bkgstack}_spcc-linked.png`.
**The owner's eyes decide anything aesthetic; the instrument gated nothing.**

**Premises this rests on and did NOT test** are named in
`datasets/aug06/l1_work/unchecked_premises.json` — the load-bearing one being
that starlight preservation is the right gate for this decision at all.

**Numbers:** `datasets/aug06/experiments.jsonl`
(`l1_background_level_perframe_vs_onstack`), `datasets/aug06/l1_work/*.json`,
each set's `starlight_work/starlight_l1{base,onstack,arm}.json`.

## Queued — needs prompts (medium; one session can take several)

- **`per-group-flat-at-the-combine`** — FIRST, because MEMORY makes it binding:
  a calibration change is evaluated against the COMBINE unit, and the member IS
  the cross-night combine unit. The per-set question is closed (composed tilt
  +0.055% ± 0.083%, 0.7σ — zero by construction, the set flat already being the
  mean of the group flats). What is open is the trade the change makes at the
  member: backgrounds 28–40× more consistent against 3.271%/4.335%
  member-to-member object-imprint disagreement where the shipped route has zero.
  The sign can invert at the combine — imprints that cancel within one set have
  no reason to cancel across nights whose skies differ. One knob, members from
  both arms; the half no instrument can settle goes to the owner.
- **Real-flats HANDLED path** — wire master-flat builds into the undistort
  route so staged real flats are USED, not just accurately refused (routing
  session shipped "named"; owner precedence: real flats WIN when present).
- **`cross-set-record-home`** — night/corpus SPCC records and baselines file
  under a borrowed member set (bitten twice this rebuild). Multi-set products
  write session-level records; combine products get a baseline home.
- **Guards runner** (`guards-and-ci`) — **SHIPPED and hardened; what remains is the
  per-block bit-depth gap the item names.** 18 checks, invoked by the pre-push
  hook, RED on a deliberately broken mechanism, logs retained on failure, and
  concurrency-safe (per-run `mkdtemp` under `$HOME` — `/tmp` is unusable because
  the Siril flatpak has a private one). **Read its LIMITS block before quoting it
  as coverage: it verifies WIRING, not output.**
- **`frame-qa-order-dependent-scale`** — every `fwhm_arcsec` rides a ~5.6%
  scale artifact; re-derive against the stack-solve family (16.98–17.08″/px)
  and root-cause the probe arithmetic.
- **`--weight=noise` corpus arm** — motivated by a MEASURED 18–24% cross-night
  noise gap (aug09 haze: +0.16 mag extinction, 16,913 matched stars);
  pre-registered one-knob A/B vs the shipped nbstack corpus, judged on
  `snr_regions` + `shape_at_sky` + the owner's eyes.
- **Pooled master darks** (under `dark-optimization-fork`) — gated on the
  nights' masters measuring identical (these did: Δ0.1 ADU, noise within 1%);
  judged on the `noise_split.sh` structured term. Per-session stays default.
- **`session-level-mount`** — one decisive probe seeds sibling sets (five
  redundant probes measured on aug09).

## Large — one session each, own prompt when scheduled

- **`render-ladder` L1** (user-gated; the owner's declared focus) — the
  on-stack background-level ladder.
- **`intake-culling` transparency surface** — per-frame sky + rate-of-change +
  nstars (+ matched-flux anchor), visible constants; positive controls that
  MUST fire: aug06/set-03's 44-frame cloud block and july31's moonrise ramp.
  Fix the item's stale "per-frame background is NOT recorded" row
  (`records.jsonl` carries it for every frame).
- **`final-best-percent-pass`** — UNBLOCKED by this rebuild (a 12-set,
  three-night corpus on one target now exists).
- **`routing-generality`** — prompt already written (above); listed here
  because it is large.

## Watch-only (work exists only if they fire)

- Union-canvas solves: the corpus hinted solve failed on seam-contaminated
  detection and the blind fallback shipped a false solution — `--central` is
  the remedy and the Tier-B solve gate is the fix; night-level solves also
  run hintless of `--central` (aug06's logodds 156 was depressed).
- `findstar` detection-count jitter ~0.3% between identical runs (top-30
  medians stable to the third decimal) — an instrument fact to carry, not fix.
- aug09 ingest is local-hash verified only; no source-side hashes exist for
  that night. A fact about the record, not fixable after the fact.

## Landed during the per-group flat session — NULL at the product, a measured TRADE at the member

**Narrowing the flat window from 500 frames to 100 does not improve the per-set
product, and the rule the brief leaned on is not grounds for it.** july31/set-03,
one knob, 19 arms of 100 frames, registration pinned at BOTH levels, all four
controls run.

**The doctrinal argument does not transfer, and this is the finding.** A ratio of
two flats from one night, lens, focal and aperture cancels vignetting EXACTLY, so
what differs between a group flat and the set flat **is the sky term** — the
optical state does not change inside a 25-minute burst. **The discriminator is
what the flat DESCRIBES**, not whether the rule is "about optics" (an earlier
framing said that and it was wrong — the rule's own justification is a *sky*
divergence: a mid-set re-aim measured L-R 1.162 vs 1.032 while the top-bottom
optical term was identical at 1.143 vs 1.142). The rule fires when a flat
averages frames that saw **different** skies, so it describes a blend **no frame
saw**. Under one continuous pointing there is no blend — the set flat **is** the
mean of the sky its own frames saw, which is what the rule asks for. So the rule
is already satisfied at the set level, **both arms imprint a sky, neither is less
contaminated**, and only the **uniformity** of that imprint across members
changes. That is why the composed difference is zero **by construction** rather
than by luck.

**The product does not move, and that was recorded before it was measured.** The
per-set flat IS the groups' average — the mean of the five departures is **0.82%
(x) and 0.76% (y) of a typical departure** — so a plain-mean compose cancels
them. Delivered: the composed object L/R tilt moves **+0.055% ± 0.083%, 0.7σ**
(Siril `psf`, 1217 stars), the composed pixel field 7–25% of the mean member
magnitude. Cancellation is 75–94%, not the >99% the sensor-frame arithmetic
gives, because the compose is a SKY-frame mean of patterns that drifted ~453 px.

**At member level the correction is real and 1:1** — planted-corrected transfer
**1.007 (x) / 1.077 (y)** — moving each member's object tilt **0.36–2.13% in x
(4.3–21.3σ)** and up to **3.42% in y**. It **buys** member backgrounds **28–40×**
more consistent (the registry's SELF-FULFILLING direction — the mechanism's size,
not evidence of better calibration) and **costs 3.271% (x) / 4.335% (y) of
member-to-member object-imprint disagreement where the shipped route has exactly
zero**. No instrument here can say which side is closer to truth, so by the
evidence gate it is a trade the DATA CANNOT SETTLE — **the owner decides**.

**Controls.** FLOOR at the group's own depth, built not inherited: **0.0546%**
corner spread, every effect **20–62×** it. IDENTITY: **0 differing pixels** on all
five groups and the compose, with the same comparison firing at **99.9995–
99.9998%** on the one-knob pair, so the zero is discriminating rather than
vacuous. PLANTED: **0.9926** recovery against the card over the delivered canvas.
UNIFORM: every dipole **+0.0000** and star differential **+0.000%** — level cannot
reach the product, only shape.

**Predictions: 5 held, 2 split, 2 falsified.** The inherited anchor **reproduces
to 0.02%** on post-reset flats (|g1 vs g5| predicted 1.3085 %/1000px, measured
+1.3088). Falsified: the "smallest departure at the middle group" clause (the
zero-crossing sits between g2 and g3, 4.7 floors apart), and the enabling-condition
worry — every group flat measures **ZERO** findstar specks against the set flat's
**ONE**, despite averaging 90.9 px of celestial motion against 453.3 px.

**Open, and it is the right next question:** the member is the cross-night COMBINE
unit, so a combine-level A/B is where the member-level trade could pay or cost.
Not run here.

**Deferred, gate-blocked not forgotten:** the owner's eyes on full-frame finals.
`render_tier.sh` exits 7 without a ratified `render` block and july31/set-03 has
none (`BACKLOG:render-ladder`). Both arms' linear stacks and all three composes
are preserved and tagged on the FITS (`DIAGARM`/`CALXSET`/`STACKNRM`/`REGPIN`) in
`sessions/july31/work/pergroup/`, deliberately NOT in `web/results/`.

**Two shipped fixes fell out of it.** `grid_ramp.py` — the registry's named
candidate gradient measure, which had no script, so the measurement behind a
registered finding could not be re-run; tool search PROBED, reports without
gating, selftest falsifies its own mechanism. And Siril prints `Sigma: -nan` on a
zero-variance crop while the shipped STAT regex carried an `n` but no `a`, so the
UNIFORM control — the one arm that produces uniform crops — could not be measured
at all; fixed, provably neutral (sigma is parsed and discarded), second copy
removed.

**Numbers:** `datasets/july31/pergroup_flat_prediction.json` (committed before the
first flat), `datasets/july31/experiments.jsonl`
(`pergroup_flat_window_july31_set03`), the 50 records in
`datasets/july31/set-03/pergroup_work/`, `docs/dead-ends.md`.

## Landed during the flat-differential session — WIN with controls

**The flat's dose difference reaches the delivered object essentially 1:1.** Two
flats of the same optical state and different sky dose (aug09 set-01 vs set-05,
Δedge dipole 0.2827 — the corpus maximum within a night) applied to the SAME 125
set-05 lights, one knob. **Delivered: −22.477 ± 0.077% object-flux tilt (r = 10 px,
914 stars, Siril `psf` against its own local annulus; −22.450 ± 0.082% at r = 16)
and edge dipole_x −0.2356 on the pixel-ratio field (Siril `fdiv` + `stat`).**

**The apples-to-apples comparison needs no model.** The flats' OWN ratio field,
cropped to the delivered canvas and measured with the same shipped instrument,
reads −0.2383 (edge) and −0.2010 (corner) against the delivered −0.2356 and
−0.2021 — **98.9% and 100.6%**, tracking point-by-point along nine midline boxes
to ≤0.008. A planted ramp of known dipole +0.1583 over that same window recovers
at **97.7%**, so the real number corrected by the control's own systematic is
**101.2%: no measurable attenuation.**

**Both blockers that killed the absolute tilt die structurally, and the selftest
proves it on the SAME fixture.** `M_i` cancels identically (the same star in the
same photons), so nothing per-star is fitted and the lever becomes the spread of
star positions: **1603 px against the absolute measurement's 29.1 px median**;
identical frames carry identical extinction and skyglow, so the sensor-fixed
atmosphere cancels in the subtraction. On `object_tilt --selftest` 4a's
pure-translation panel, one screen: **absolute −0.0464 ± 0.0001 with the lever at
0.00 px, differential +0.0999 ± 0.0001 with a 1548 px lever.**

**The floor is EXACTLY ZERO** — both instruments, all three channels, both
apertures. The identity rebuild is bit-identical; the non-vacuous version (a
uniform 1.05 card) changes **74.10% of the pixels** and still moves every dipole
by 0.0000. That control also measured the mechanism: **Siril `calibrate`
normalizes the flat by its own level, so a flat's LEVEL cannot reach the product
— only its SHAPE can.** Discrimination is unbounded (planted movement 0.1547
against 0.0000), where the object-tilt instrument managed 0.20×.

**The shipped normalization absorbs 0.3%** of the object's difference (−22.477%
at `-nonorm` vs −22.550% at `-norm=addscale -output_norm`), so nothing is hiding
the defect. The same pair moves the BACKGROUND dipole **+48.6%** and splits the
channels — a pedestal artefact, not imprint (psf's local annulus removes an
additive term, regional medians cannot; measured: `An/A` is a uniform 2.02× while
`Bn/B` runs 1.859 left to 1.667 right). **Read the pixel field on `-nonorm` arms
only.**

**The two instruments differ by 1.34% and it is attributed, not averaged**: the
delivered field's x-slope varies with y (max departure from the end-to-end line
0.0204 along the midline), so a corner-anchored dipole, a plane fit over stars and
a midline profile are three summaries of one field — on the exactly-linear planted
card the same two instruments agree to 0.32%.

**The brief's own load-bearing premise was false and had to be fixed first.** It
asserted the arms are pixel-aligned because they share a chain; `register -2pass`
re-chooses its reference from image quality and the CALIBRATION changes that
choice — measured, one knob: reference image 1 / canvas 4896×3616 against image 2
/ 4887×3641. `run_undistort_pipeline.sh` gained `--regdata=` (every arm is handed
the first arm's registration data) and `--nonorm`, both default-off; `CALFLAT`
also stamped the set's RECORDED flat rather than the one that RAN, now corrected
with `CALXSET` marking a cross-set calibration on the product itself.

**SCOPE, stated before the result and unchanged by it:** this is the DIFFERENCE
of two imprints. It gives the delivered sensitivity to a KNOWN dose difference —
the number a corrective needs — and NOT the absolute tilt, which needs the flats'
COMMON sky content and is still unmeasured. It does not resurrect the 3.11%/241σ
figure (UNVERIFIED), and the T/B attribution caveat stands.

**Deferred, gate-blocked not forgotten:** the with/without pair on FINALS.
`render_tier.sh` exits 7 without a ratified `render` block and aug09/set-05 has
none (`BACKLOG:render-ladder`) — re-verified. Both arms' linear stacks are
preserved and tagged (`DIAGARM`/`CALXSET`/`STACKNRM`/`REGPIN` on the FITS),
including the production-normalization pair, which is the one to judge.

**Numbers:** `datasets/aug09/flatdiff_prediction.json` (committed before the
arms), `datasets/aug09/set-05/flatdiff_work/flat_differential.json` + the five
pair records, `docs/dead-ends.md`, `datasets/aug09/experiments.jsonl`.

## Landed during the object-tilt session — NULL with controls

The catalogue-free `sky × V` object-tilt measurement was BUILT, run over all 12
sets, and is now a registered **DEAD END**; the untracked 3.11%/241σ figure is
retired as **UNVERIFIED** at all 13 code and doc sites and in the 13
`readiness.json` records (via their generator, which was the real site).

**Two independent blockers, either fatal.** (1) A linear sensor-fixed mode is
EXACTLY absorbed by the per-star and per-block nuisances under a pure
translation, so the 503–1220 px of drift carries none of it; the lever is the
FIELD ROTATION, 0.69–3.76°/set, leaving a **29.1 px median lever on a 5769 px
frame — a ~200× extrapolation**. (2) For a FIXED camera every sensor position
maps to a fixed altitude, so atmospheric extinction and skyglow across this
27° field are sensor-fixed too and airmass-shaped like the flat's own sky term;
the fit sees their SUM, and both external anchors are closed (a catalogue is
structurally impossible at 17″/px on trailed stars, a real flat IS the fix).

**The instrument is sound and the controls prove it**: a Siril `imul` ramp of
edge ratio 1.2222 recovers at **1.24×** (0.95× on the best-levered block pair)
and a uniform card moves every number by **exactly 0.00** — but its
**discrimination against the floor is 0.20×** (planted 9.85 points against a
49.08-point floor), where the iterative-flat NULL met 48–62×. **The floor is 49
percentage points** — aug09/set-01 rebuilt as interleaved halves has a predicted
tilt of exactly zero and measures **+49.08 ± 4.97% (r = 10 px) / +50.82 ± 5.65%
(r = 16 px), 3086 stars, 11.8σ**. `--selftest`
falsifies the mechanism in process — a pure-translation panel returns a planted
+0.100 mag as **−0.046 ± 0.0001** with the lever at 0.00 px, so a degenerate fit
reads confidently WRONG; read the lever, never the sigma.

**The pre-registered corpus prediction failed 4 of 5**: every set exceeds its
own flat's dose by **1.4–86× (median 8.1×)**, and aug06/set-03 — pre-registered
as the built-in null — measures **+223 ± 28%** against a predicted +2.6%.
ρ = +0.68 (p 0.015) is a real ordering but cannot confirm at those magnitudes,
since the flat's L/R sweeps with the night's sky state and so does the
confounder. Median within-set block-pair spread **529 points**, where one
sensor-fixed field must give one answer.

**By-product worth its own item:** the per-block fit measures a real within-set
sensor-fixed gradient DRIFT of **0.040–0.425 mag (median 0.149), monotone in
block order in 10 of 12 sets** — a transparency-drift measure
`BACKLOG:intake-culling` does not have.

**Numbers:** `datasets/aug09/corpus_object_tilt.json`,
`datasets/aug09/tilt_corpus_prediction.json` (committed before the corpus ran),
the 12 per-set `tilt_work/object_tilt.json`, `docs/dead-ends.md`, and the three
nights' `experiments.jsonl`.

## Landed during the verification session (audit's done-ledger)

`dd7a13d` guard made executable + `shape_at_sky.py` acceptance instrument
(calibrated to the recorded union A/B to the third decimal) · `a1dc91b`
member-provenance CALSET truncation fix + header repairs · `3f1980d` corpus
glob can never ingest set-00 · `1791bb4` master-dark rejection recorded as the
vendor's own command (item closed) · `82f67f8` BACKLOG prune (closed items
removed entirely) · `f43e482` `snr_regions` triple fix (negative-value regex,
cross-session basename collision, flatpak-private-/tmp workdir) · `739c626`
Tier A: set-00 skipped by the session chain, per-set compose reference pinned
(**verified on aug06/set-01 ONLY — this ledger previously said "verified
bit-identical" unqualified, which widened the commit's own scope. The L1 session
measured the pin MOVING the canvas on aug06 set-02 and set-03; set-01 was
bit-identical because its unpinned auto-pick already landed on member 1, which is
what the pin selects. The pin is right; the recorded scope was not**),
astrometric caveat on separation records, bare
`--selftest` refuses instead of masquerading as help · `fa40ef1`/`28b91cf`
the prompt briefs.

## Landed during the Tier-B hardening session

`8d370dd` `-transf=`/`-interp=` pinned at all 20 emissions + `check_registration_pins.sh` (per COMMAND, `--selftest`), proven no-behaviour-change by an all-nil recompose · `3072fd0` `verify_lens_card.py` wired into `lens_preflight --require-profile` unconditionally (11.1 s), fire-tested — and `install_lens_model.sh`'s idempotence test fixed, since it reported "already installed" on a DB whose vignetting was back · `4d70455` the solve refuses a solution contradicting its own hints (exit 9), `--central` corrected to fraction-of-frame at three sites; falsification fires, 0/69 false · `e7cb2be` the aircraft rejection CONFIRMED via Siril `-rejmaps` (the product-level A/B the item specified is under-powered by the group+compose dilution — recorded in `docs/dead-ends.md`) · `7d4946e` the Tier-B report + its prompt retired.

**Numbers: BACKLOG's removal-conditions rows for the solve gate and the lens-card wiring; the aircraft entry in `docs/dead-ends.md`.**

## Landed during the iterative-flat session

The domain-corrected iterative sky flat is **NULL, structurally**: the iteration
reconstructs whichever flat it is handed (`F1 = F_roundtrip`), because dividing
by `F0` is what removes the gradient from the sky and multiplying back restores
it. It repaired `--desky`'s domain error and still could not work, so "run the
operator in the correct domain" is exhausted as an angle. Positive controls move
the same code 81.7% (fixture, round-trip flat = the known true `V`) and 93.4%
(real data, handed another set's flat — it returned THAT set's flat from set-05's
frames) where the scheme moves it 1.7% / 1.2%; a 48–62× discrimination, so the
null is a measurement and not a check that cannot fail. No builder flag was
added and no removal-conditions row created — a flag selecting an inert
mechanism is dead code and there is no divergence to retire; `build_sky_flat.sh`
is byte-unchanged.

What the session leaves behind is worth more than the arm: `flat_odd_component.py`
— the odd-component instrument `BACKLOG:calibration-evidence` recorded as MISSING
— and the decomposition it produced. The left-right term is SKY (monotonic within
all three nights; edge dipole sweeping +0.436 → 0 → −0.385 across the corpus,
impossible for a sensor-fixed term), but the brief's premise that the stable base
is "a real instrumental odd component" is **refuted**: T/B sits above 1 on july31
and drifts +6.7% through that night while sitting below 1 on aug06/aug09, so
neither axis isolates the instrument and the constant-within-a-night part stays
unattributed. Four Siril behaviours pinned by probe, two of which silently
corrupt data — `offset` clips at 0 in 32-bit against its own documentation, and
`stat` excludes zeros, which compound into damage that reads back as clean
numbers.

**Numbers: `docs/dead-ends.md` (the iterative-flat entry) + `datasets/aug09/experiments.jsonl`.**

## Landed during the routing-generality session

The route key is one derivation (`scripts/lib/route.py`) on the sky excursion as
a fraction of the field, replacing six private copies of a `fov`-width test that
also inverted the physics — a fixed mount sweeps 0.2507 × cos(dec) °/min at any
focal length, so a narrow field crosses more of itself per minute than a wide
one, and the width floor excluded exactly the sets with the most drift. Keyed on
an ANGLE, not `drift_px`: camera raws solve on the half-res green plane, so the
recorded px figures read 2.078–2.137× the sensor's scale and would mean two
different things on two rigs. Floor 0.05 is EVIDENCE (the smallest excursion the
term is measured present at), not a knee — none has ever been measured. All 12
real sets route identically; the fire test moves five consumers together; the
200 mm and mono/tracked fixtures route through the live chain; both refusals name
their class with the resolving step. `routing-generality` removed from BACKLOG.

**Numbers: `scripts/lib/route.py` (+ its `--selftest`) and BACKLOG's removal-conditions row for the floor.**

## Landed during the comment-hygiene session

The removal taxonomy is derived from all 638 commits, not assumed: seven
categories over 1,403 removed comment lines and 15,397 removed record lines
(in-place edits only — 52 wholesale `.md` retirements excluded as a different
mechanism). The costly category is **drift**, prose asserting what the code
contradicts, and it is the only one that recurred — six instances of the ICC
leg rule alone, one of which pointed a future session at `docs/dead-ends.md`
trap 3 as "the cheapest available win". One anticipated category is **refuted**:
victory language has never once been removed, and its obvious detector matches
only domain vocabulary (*fixed mount*, *matched-flat*).

The policy audit found the date rule **false as written**. "Doctrine
ratification stamps are the one exception" would have a literal sweep delete
`BACKLOG.md`'s entire re-verify column, `CLAUDE.md`'s own rig stamp, and the
dated Context line `docs/README.md` requires of every deep-dive. The rule now
states the principle that covers all three: a date is allowed where the date IS
the information — what supersedes what, or how stale a claim is.

Shipped: [`COMMENT_SWEEP_PROMPT.md`](COMMENT_SWEEP_PROMPT.md) (non-retiring),
the `CLAUDE.md` rule revision, `COMMENT_HYGIENE_PROMPT.md` retired. No sweep was
run — that is the standing prompt's job, on the owner's schedule.

**The taxonomy, detectors and policy live in [`COMMENT_SWEEP_PROMPT.md`](COMMENT_SWEEP_PROMPT.md).**

## The standing sweep's first run — AUDITED PASS

`bd1c675`, audited by re-execution rather than on the report's assertion.

- **Category 1 (drift) CONFIRMED live.** `check_bitdepth.sh` names four
  exemptions and prints "the 4 documented instrument exemptions"; `README.md`
  said three and `BACKLOG.md`'s register row said three while omitting
  `run_lunar_pipeline.sh` entirely — prose contradicting the guard that enforces
  it. Both corrected, and the guard still exits 0. This is the finding that
  justifies the run.
- **Category 6 CONFIRMED.** `grep -cE '^## \`?[0-9]' BACKLOG.md` returns **0**,
  so all 30 numbered refs did point at nothing. Three survive tree-wide, all of
  them the taxonomy's own teaching examples in the sweep prompt — sanctioned,
  not misses.
- **Category 7**: the surviving `file:NNN` cites are six in
  the route-key session's transcript rather than a live contract (retired since).
- **Regression check**: all five guards and all three selftests PASS after the
  edits, and `run_session_chain.sh sessions/aug09 --plan` walks five sets clean.

**One gap found in the standing prompt, fixed here.** Its `Scope` named the root
session reports neither IN nor OUT while its own detectors return live hits
there. They are now explicitly OUT as transcripts, with category 1 still
applying where a report is cited as current guidance — the sweep is non-retiring,
so an ambiguity in it recurs every run.

## Landed during the L1 research session — the gate now exists, and two beliefs resolved against themselves

The brief's premise held: L1's adoption gate was unresolved-starlight
preservation and nothing in the tree measured it. It does now, and building it
changed what the build session should expect.

**The instrument** — `scripts/qa/starlight_preservation.py`, an ALLOWED
gap-filler: Siril `boxselect`+`stat` measures every per-cell floor, the ESA Gaia
archive's TAP service aggregates the catalogue server-side, and in-house code
holds only the lattice, the WCS projection and the fits. It gates nothing and
always exits 0. The tool search behind the removal condition was run rather than
reasoned — Siril `stat`/`bg`/`bgnoise` measure the image only and `conesearch`
is not even usable at this field size (20.6° radius at G≤17 against TAPVizieR,
killed at 600 s with no output); `source-extractor -CHECKIMAGE_TYPE BACKGROUND`
writes a background map in 1.7 s but compares it to nothing; GraXpert `-bg`
writes a model image; ASTAP reports HFD and star rows. Two probes replaced
assumptions: `boxselect`+`stat` is identical to `crop`+`stat` to every printed
digit in ONE load, and `jsonmetadata -stats_from_loaded` silently ignores a
selection.

**The selftest earned its place on its first run.** `boxselect` counts y from the
TOP; the mirrored lattice still recovered 54% of a planted relation at R² 0.30 —
a half-right number a fixture-free instrument would have shipped. Fixed, the
positive control reads 299.14 against 300.00 planted at R² 0.99993, an orthogonal
predictor returns R² 0.00017, Siril `subsky 2` collapses the planted relation to
26.9% and the pristine copy re-reads 299.14 to 1e-6.

**Degree 1 vs 2 is MEASURED, and the answer needed no image.** `subsky d` removes
a degree-d surface, so the most it can take is the fraction of the Gaia
predictor's own spatial variance a degree-d surface can represent: over
aug06/set-01, **plane 10.0%, quadratic 36.2%, cubic 43.5%** (140-cell external
lattice, predictor spanning 174% of its mean). Degree 2 costs a third at worst,
not erasure — the registry's "seqsubsky 2 erases it" was mechanism, and the
bound is smaller than it implied. No confound can move this number.

**The image-side version of that test cannot settle it on today's products, and
why is a second result.** One knob, on-stack `subsky 1` vs `2`, paired on the
same cells: the Gaia slope RISES — retained 1.232/1.274/1.237 at degree 1 and
1.517/1.846/1.604 at degree 2 (SE 0.056–0.155). The open `sky × V` residual is
anti-correlated with the starlight and biases the raw slope low, so
confound-removed and starlight-removed land in one statistic with opposite signs.
Sizes fall out: predicted starlight spans 0.71–0.86 ADU across the frame against
a measured floor span of 2.50–4.00 ADU, so **roughly a fifth to a third of the
frame-scale floor variation is starlight and the rest is not.** A clean
structural check comes free — residualise both arms by a quadratic and the
degree-2 arm retains 1.000/1.010/1.018, i.e. `subsky` moves only its own
polynomial subspace.

**"Visible rings" is not an eye observation.** It entered as *"fails the rings
gate"* and commit `870bf7d` rewrote it to *"visible rings"* in the same diff that
deleted the gate — `bg_qa.ring_amp`, the detrended peak-to-valley of a 40-bin
RADIAL profile of the render. That is the reference FORBIDDEN class and the same
radial-binning family as trap 3. Stack-level BGE is UNJUDGED; if the on-stack arm
loses, that is discovered, not predicted.

**Standards-first: our default already matches the vendors.** Siril's own docs
recommend per-frame degree 1 (*"in a single image, the background gradient is
much simpler and generally follows a simple linear (degree 1) function"*), and
both Siril and PixInsight put background extraction before colour calibration —
the order this chain runs. What is NOT vendor doctrine anywhere is the
starlight-preservation argument for degree 1; Siril's stated reason is gradient
complexity.

**Numbers: `docs/dead-ends.md` (Background), the register row in `BACKLOG.md`,
and `datasets/aug06/set-01/starlight_work/*.json`.**

### What the build session inherits — the unknowns, stated

1. **The two arms may not be separable on this criterion.** An on-stack plane is
   bounded at 10.0% by the catalogue, and the paired instrument resolves 5–16%.
   The arms can only differ materially if the per-frame step reaches structure a
   single sky-plane cannot — which is exactly the pre-registered directional
   prediction (a sum of planes fitted in SENSOR coordinates to frames drifting
   across the sky is not one sky-plane). If that mechanism is weak, expect a
   NULL, and the level choice will have to be made on other grounds.
2. **Degree 2 is NOT a third arm.** Two arms, degree held at 1, dither held off.
   The degree question is answered by the bound above and does not need a build.
3. **`--gsplit` is inherited, not measured here.** G = 11.0 at 50% completeness
   comes from the archived july23 record. Every magnitude bin is kept, so a
   re-measured limit re-splits the record offline without re-querying.
4. **Expect `retained > 1` and do not read it as starlight being added** — see
   the confound above. The catalogue bound is the number no confound touches.
5. **`member_separation.py --selftest` cannot run on today's tree** — no complete
   registered `s_*.fit` sequence survived the from-raws rebuild. One
   `register -2pass` on any groups dir restores it. Pre-existing, unrelated to
   this session's changes, and now stated in its register row.

The pre-registration covering both arms is
`datasets/aug06/experiments.jsonl`, `l1_background_level_perframe_vs_onstack`,
with a falsifier for each arm and every path re-verified against disk.
