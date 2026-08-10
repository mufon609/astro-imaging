# The aug06 member EDGE chase — where the defect enters, and what actually smears the union

Commissioned by `CHASE_AUG06_MEMBER_EDGE_PROMPT.md` §4: *measure single frames with
the same instrument as the member march, and decide whether the aug06 edge deficit is
introduced inside the within-group registration/stack or upstream of it.*

**It is upstream — and it is not the defect the owner sees.** Both halves of that
sentence are measured, and the second one is the result that matters.

- The aug06-vs-july31 member edge difference is **flat across the whole chain** once
  the star population is flux-matched (+0.174 → +0.130 → +0.175 px). Neither the warp
  nor the registration/stack introduces or amplifies it. The 2.6× growth the original
  reading showed is a **detection-depth artefact**.
- The smear on the accepted cross-night union is **introduced by the within-set
  5-member compose**: five members measuring roundness **0.924–0.942** at one sky
  compose to **0.582** there, and to **0.949** at another sky where they measure
  0.903–0.958. A single homography cannot align members whose optical axes are
  **4.28° apart** — which is what a set's five members are, because a group is a
  consecutive time block of a sweeping sky.
- The members' **own astrometric solutions** place the same stars within
  **0.10 px median / 0.26 px p90** at exactly the sky where the homography compose
  loses 1.06 px of FWHM. The alignment information exists; the compose discards it.

Records: `datasets/aug06/experiments.jsonl` —
`member_edge_deficit_level_of_entry` (pre-registered before the run) and
`within_set_compose_is_the_visible_smear`. Mechanisms graduated into
`docs/dead-ends.md`; the work queue is BACKLOG:`compose-homography-smear`.
Nothing was executed on an accepted product.

---

## 1. The instrument, and why it is the same one

Every number below is Siril's. `setfindstar reset -roundness=0.10 -relax=on
-maxR=1.0`; 800×800 `crop` boxes; `findstar -layer=1 -maxstars=2000`;
**FWHM = median of (FWHMx+FWHMy)/2**, **roundness = median of min/max**. The
in-house part is the median of the tool's own fits and nothing else.

That reduction was **verified to reproduce the member march that produced the
finding, exactly**, from its preserved `.lst` files: aug06/set-01 recomputes
3.11 / 2.765 / 2.518 / 2.49 / 2.97 and 0.9027 / 0.883 / 0.9091 / 0.9494 / 0.8487
against the ledger's 3.11 / 2.77 / 2.52 / 2.49 / 2.96 and 0.903 / 0.883 / 0.909 /
0.949 / 0.849. Without that check the whole comparison would have been across two
instruments again — the error this chase exists to correct.

Where boxes were placed by sky rather than by frame fraction, they were placed
through each product's own solved WCS and then **verified by Siril's own per-star
RA/Dec output** — every box landed within 0.23° of its target. That check caught a
first pass that had silently mirrored every crop: Siril's `crop` y-origin is the
opposite end from FITS row order (`docs/dead-ends.md`), and the registry's own guard
is what found it.

Load at every reading: 1-minute average 0.2–1.4. No measurement was taken on a busy
box.

## 2. §4's question: which level does the edge deficit enter at?

Three levels, one instrument, four members. **L1** the calibrated + debayered single;
**L2** the same single after the darktable `lensdist` warp under the PINNED model
(installed and preflight-verified: *"pinned model OK … darktable PROVES it corrects
this set"*); **L3** the 100-frame member those very frames built. Frames are 5 evenly
spread through each group's own `g1.list`, with that set's own master dark and sky
flat.

**Edge-minus-centre FWHM (px), pooled over x = 8% and 92% and over two sets per
session:**

| level | aug06 | july31 | session difference |
|---|---|---|---|
| L1 calibrated single | +0.364 | +0.190 | **+0.174** |
| L2 warped single | +0.190 | +0.060 | **+0.130** |
| L3 member (100 frames) | +0.285 | +0.110 | **+0.175** |

*(one common fitted-amplitude cut per level, chosen so every box of every arm keeps
≥60 stars: L1 A≥0.03073, L2 A≥0.02654, L3 A≥0.01819)*

**Flat.** The chain neither creates nor amplifies the session difference.
`H_upstream` confirmed; `H_stack` and `H_warp` killed.

### 2.1 What the original reading was measuring

On the **full detected population** the same three levels read +0.176 → +0.162 →
**+0.456**, which is what made the stack look guilty. That growth is entirely the
faint tail, and the faint tail is not comparable: on the moonless night the member
reaches fitted amplitude **A ≥ 0.00031**, on the moonlit one only **A ≥ 0.00060**.
At one box the aug06-minus-july31 difference reads +0.055 px on the 30 brightest,
+0.081 at 60, +0.119 at 120, +0.180 at 250, +0.308 at 400, and **+0.518 on
everything** — a factor of nine across the same two files.

This is the mirror of the registry's survivorship trap and is now registered beside
it: a raw `findstar` median is **not comparable across levels of a chain**, and a
darker sky beats a brighter one on depth before it says anything about quality.

### 2.2 The within-group candidates, closed

**Drift span** (§5.1) — one knob, 10 frames per arm, consecutive (21 px span) against
full-span (235 px), everything else identical:

| arm | span | edge excess |
|---|---|---|
| aug06 consecutive | 21 px | +0.240 |
| aug06 full-span | 235 px | +0.293 |
| july31 consecutive | 21 px | −0.020 |
| july31 full-span | 232 px | +0.022 |

An 11× larger span costs **+0.053 px** (aug06) and **+0.042 px** (july31) — the same
in both, so span is a small common modifier, never the differentiator. Independently,
the `framing=min` trim at matched group size is already equal: aug06/set-01 234×80 px
against july31/set-01 232×88 px.

§5.2 (registration residual), §5.3 (transform class) and §5.4 (the warp's residual)
are moot as *explanations of the session difference*: L1 already carries it in full,
before any of them run.

### 2.3 What the residual +0.175 px actually is

At the field edges the two sessions are **nearly equal** in FWHM (aug06 2.08–2.18 px,
july31 2.10–2.16); aug06's **centre** is the sharper (1.758/1.765 against
2.058/1.830). So "aug06's edge is worse" is a centre advantage plus a right-edge
roundness deficit (x = 92% roundness aug06 0.756/0.725 against july31 0.829/0.809),
present in the raw calibrated frame. EXIF records no difference at all — f/4, 70 mm,
2.5 s, ISO 1600, manual focus, `FocusDistance` 10.0 m (coarse-quantised), electronic
shutter, VR off, same body and lens. The remaining candidate is focus/field state,
which no processing knob reaches and which **is not worth a fix**: 0.175 px is below
what the compose defect below throws away.

### 2.4 One record correction

§3.2's *"aug06's RAW SINGLES are the more field-uniform of the two (1.174 vs 1.220)"*
does not survive. That figure came from 700 px **corner** boxes at `sigma=0.5`; the
finding came from an 800 px **mid-height march** at `sigma=1.0`. Under one
instrument aug06's singles are the **worse** at the horizontal field edges (+0.364
against +0.190 px of edge excess). The inference "therefore the degradation is
introduced between single frame and member" was an artefact of comparing two
instruments — the same failure mode the arc was already carrying.

## 3. The defect the owner actually sees

The union canvas marched at 5% steps, 800 px boxes, mid row, 30 brightest per box —
with each session's per-set coverage at the same columns, from each per-set stack's
own solved WCS projected into the union's:

| x% | RA | FWHM | roundness | aug06 sets | july31 sets | |
|---|---|---|---|---|---|---|
| 5 | 286.2 | 2.74 | 0.989 | 0.00 | 0.00 | |
| 10 | 287.0 | 2.83 | 0.966 | 0.66 | 0.00 | |
| **15** | 291.0 | 4.20 | **0.489** | 2.02 | 0.00 | SMEARED |
| **20** | 294.1 | 4.47 | **0.448** | 2.83 | 0.32 | SMEARED |
| **25** | 296.2 | 4.19 | **0.493** | 3.00 | 1.76 | SMEARED |
| **30** | 299.9 | 3.44 | **0.613** | 3.00 | 2.90 | SMEARED |
| 35 | 303.7 | 2.88 | 0.781 | 3.00 | 3.00 | soft |
| 40 | 305.2 | 2.67 | 0.841 | 2.91 | 2.98 | soft |
| 45–70 | 308–320 | 2.44–2.70 | **0.916–0.968** | ~3 | ~3 | the clean band |
| 75 | 323.1 | 2.87 | 0.895 | 1.70 | 3.00 | soft |
| 80 | 325.2 | 3.05 | 0.857 | 0.39 | 2.72 | soft |
| **85** | 327.2 | 3.51 | **0.731** | 0.00 | 1.56 | SMEARED |
| **90** | 329.7 | 4.79 | **0.543** | 0.00 | 0.34 | SMEARED |
| 95 | 331.8 | 2.84 | 0.837 | 0.00 | 0.00 | soft |

*(a 0.00 means outside every per-set compose, not absent data — the members extend
further than the per-set stacks used as the coverage proxy)*

Two things fall out immediately. The **extreme left is clean** (x = 10%, roundness
0.966) — so this is not "the aug06 field edge". And roundness collapses the moment
**more than one aug06 set overlaps**: 0.66 sets → 0.966, 2.02 sets → 0.489, at
adjacent columns.

### 3.1 The same sky at four levels

800 px boxes at **RA 294.86 / Dec +44.99**, placed by each product's own WCS, 30
brightest fits (so a 100-frame member and a 28-member union are rank-matched):

| level | FWHM / roundness |
|---|---|
| set-01 member `sub_01` (ρ 0.41) | 2.42 / **0.924** |
| set-01 member `sub_02` (ρ 0.46) | 2.46 / **0.924** |
| set-01 member `sub_03` (ρ 0.51) | 2.52 / **0.937** |
| set-01 member `sub_04` (ρ 0.57) | 2.54 / **0.941** |
| set-01 member `sub_05` (ρ 0.62) | 2.54 / **0.942** |
| set-01's own 5-member compose | 3.48 / **0.582** |
| set-03's own 5-member compose | 2.70 / 0.910 |
| aug06 13-member 3-set union | 3.83 / 0.530 |
| 28-member cross-night union | 4.38 / 0.458 |

Control, same instrument, same members, **RA 314.72 / Dec +42.15**: members
2.23–2.38 / 0.903–0.958, set-01 compose **2.43 / 0.949**, union 2.45 / 0.968. The
compose costs nothing there.

So: **every member is clean, at mid-field radius, and their own 5-member compose
throws away 1.06 px of FWHM and 0.34 of roundness.** The 3-set and cross-night joins
add less than the within-set step did (0.582 → 0.530 → 0.458). The cross-night
combine is not the problem, and neither is the model — all 28 members carry identical
`DISTA/B/C`.

Confirmed by eye at 1:1, like-for-like crops of the same sky
(`sessions/aug06/work/edgechase/looks/`): the member shows round points; the compose
of those same members shows every star drawn into a short dash.

### 3.2 The mechanism

A group is a **consecutive time block**, so within one 1497 s burst the sky sweeps
6.25° of RA and set-01's five members solve to centres **RA 303.87 / 304.78 / 306.03 /
307.41 / 308.16 — 4.28° apart**. Composing them is stitching different pointings, and
the registry's own Szeliski result then applies one level up: the true
member-to-member map is `distort ∘ H ∘ distort⁻¹`, while `register -2pass` fits `H`
alone. Any lens-model residual that survives the shared warp is exactly what a
homography cannot absorb.

The discriminator that names the fix: **the members' own astrometric solutions place
the same stars within 0.10 px median / 0.26 px p90** (10 pairs, n = 1151) at the very
sky where the homography compose loses 1.06 px. The information needed to align them
exists in each member's own WCS. That is a measured case for per-image astrometric
resampling, not an argument for it.

### 3.3 Why set-01 and not set-03 — answered, and it is two things

The re-zoned gate was run and its pre-registered prediction held (set-01's members
**4.91 px** at the corner against set-03's **0.95**). It resolves the disagreement
into two measured terms, neither yet sized against the other:

**(a) The compose makes part of it.** The same members disagree more when registered
inside a big sequence than when composed among themselves — july31/set-01
**1.12 → 3.02 px**, aug06/set-03 **0.95 → 3.38 px**, going from their own 4–5-member
compose to the 41°, 28-member union. One homography per member against a distant
reference is a region-weighted compromise, and members compromised over different
regions disagree with each other.

**(b) aug06/set-01 carries an optical-state change mid-burst.** Its groups 1,2,3 agree
to **0.21–0.34 px**; groups 4,5 sit **2.95–4.91 px** away. Three checks rule out the
alternatives:

| check | result |
|---|---|
| pointing spread? | members 1–3 are **2.16° apart at 0.34 px**; members 3–4 are **1.38° apart at 3.14 px** — smaller separation, 9× the disagreement |
| registration reference? | 1\|4 reads **2.95 / 2.98 / 3.02 px** with the reference at member 1, 3, 5; every pair moves <2% |
| what kind of residual? | **radial** about each member's own axis (median radial/tangential 0.39/0.24 for 3\|4, 0.32/0.17 for 4\|5) against **tangential** for the healthy pairs (0.03/0.06 for 1\|2) |

A homography absorbs translation, rotation and scale exactly, so a radial residual
growing with own field radius is a change in the **radial distortion** — the optical
state — not a mis-fit. All five groups are exactly 100 consecutive frames of one
1497 s burst, so the boundary is a time boundary.

This does **not** revive per-set models: a per-set model would be wrong for part of
its own set. It establishes that the optical-state tier can be finer than the set
tier, and that a state boundary is something to detect rather than assume.

**Still open:** what physically changed at that boundary (focus/temperature drift and
a mechanical shift both predict a radial term), and how the union's 2.43 px corner
median splits between (a) and (b).

### 3.4 The gate could not see any of this

The accepted union's own compose gate returned **`VERDICT: UNMEASURED`** — 378 of 378
pairs produced no zone with ≥100 matched stars — and was overridden with
`--accept-separation=99`. The product shipped with no working geometry gate. Its
zones are canvas-radial; the smeared sky sits at canvas ρ ≈ 0.46, pooled into a MID
annulus that is clean everywhere else.

## 4. What it costs the deliverable

**Four of nineteen marched columns read roundness 0.448–0.613** — x = 15–30% of the
canvas width, RA 291–300 — against **0.916–0.968** in the clean band x = 45–70%. Two
more columns read 0.543–0.731 at x = 85–90%, the thin july31-only right edge, which is
a *different* cause (a single session's own field edge at ≤0.34 sets of coverage) and
reads as soft-and-noisy rather than directional, matching the owner's own distinction.

That is roughly **a fifth of the frame smeared, and it is the fifth the owner named**.
The judged surface was the full 8659×6009 canvas, so none of it was hidden by framing.

**Would a fix change the verdict?** Bringing x = 15–30% to the clean band's roundness
would convert about a fifth of the frame from visibly doubled stars to points, at
unchanged depth and unchanged coverage. On this repo's own history — the products the
owner failed were failed for star doubling at 2.11 and 2.99 px — yes, materially.
The accepted union is currently "accepted with a known defect"; the defect has a
measured mechanism and is not inherent to cross-night combining.

## 5. Ranked fix proposals — for the owner to decide

Nothing below has been executed. All of it stays inside the flatless route; none of it
touches acquisition or asks for real flats.

1. **Fix the instrument first — re-zone `member_separation.py` by each member's own
   field radius.** Contained to one script, no new tooling, and it is the prerequisite
   for judging every option below. It also closes a live hole: the accepted union
   shipped ungated. *(BACKLOG:`compose-homography-smear` item 1.)*
2. **Trial SWarp** (packaged for this distro at 2.41.5-3, not installed) — resample
   each member onto one output WCS by its **own** solution instead of by a shared
   homography. This is the industry operation for exactly this problem, per-member
   solving is measured working here (8/8, logodds 113–201), and the 0.10 px agreement
   between members' own solutions is direct evidence it would remove the defect. It
   also makes the model-scope question moot. Cost: install, an interpolation and
   photometry check, and a declared delta on a rebuilt union.
3. **Interleaved rather than consecutive groups** — one knob, cheap, collapses the
   within-set pointing spread to ~0 and with it the homography's job. **Real trade,
   not a free win:** co-pointed members compose to one member's sky area, so the
   swept-field mosaic that makes the wide canvas is lost, and the dwell-floor and
   transient-rejection arguments both carry a denominator that changes with the route
   (registry). Worth running as a one-knob measurement on set-01 before believing
   either way.
4. **A corner-true shared lens model** — reduces the residual the homography must
   absorb. No fit on record constrains past ρ 1.47–1.51 against a corner at 1.80.
   Expensive, and it does not remove the mechanism, only shrinks it. A candidate is
   judged at the COMBINE, never on a per-set product — the registered trap.
5. **Compose-input edge shrink / `-framing=min`** — ships less sky rather than fixing
   the cause. Last resort, and it should be called what it is.

**Explicitly NOT recommended:** chasing the +0.175 px frame-level session difference
from §2. It is real, it is acquisition-side, and it is an order below what item 2
would recover.

## 6. Nulls, stated as plainly as the wins

- The within-group registration/stack does **not** introduce the aug06 edge deficit.
- Drift span within a group is a **+0.05 px** effect, equal in both sessions.
- The distortion **model** is not implicated anywhere in this report: all 28 members
  of the accepted union carry identical coefficients, and the smear appears within a
  single set under a single model.
- The **cross-night join** is not the problem: it adds 0.530 → 0.458 on top of a
  within-set 0.924 → 0.582.

## 7. Reproducing this

Probe and records: `sessions/aug06/work/edgechase/` — `probe.py` (stages 1–3),
`levels.json`, `span.json`, `union_profile.json`, `boxes.json` (every crop with its
target sky and the product's own WCS), `looks/` (the 1:1 surfaces and every `.ssf`).
The session tree is gitignored by design; the numbers, instruments and box geometry
are in the two ledger entries, and the members are rebuildable bit-identically from
raws plus tracked records (`docs/combine-contract.md` §0.1).
