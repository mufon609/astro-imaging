# The domain-corrected iterative sky flat — NULL, and the mechanism why

**Verdict: clean NULL, and the reason is structural rather than a tuning miss.**
The iteration reconstructs whichever flat it is handed: `F1 ≈ F_roundtrip`,
always. The brief's scheme hands it `F0`, so `F1 ≈ F0` and the baked-in sky
gradient is untouched. Two independent measurements say so — a synthetic fixture
with known truth and a positive control, and real frames on the live path — and
the algebra says why.

Nothing here was adopted, nothing shipped, no product overwritten. The builder
is unchanged — a flag was NOT added, because a flag that selects an inert
mechanism is dead code with a maintenance cost (see *Why nothing was
implemented*).

**What DID come out of it, and it is the useful half:** a model-free instrument
for the flat's odd component (`scripts/qa/flat_odd_component.py` — an
instrument `BACKLOG:calibration-evidence` records as missing), the aug09 dose
curve decomposed with it, the left-right term confirmed as SKY by a sign sweep
across the corpus that no sensor-fixed term can produce — and a correction to
the brief's premise, since the top-bottom term turns out **not** to be
demonstrably instrumental either. Four Siril behaviours were also pinned by
probe, two of which silently corrupt data.

Records (all tracked):
`datasets/aug09/flat_ratio_decomposition.json`,
`datasets/aug09/iterative_flat_fixture.json`,
`datasets/aug09/corpus_flat_odd_component.json`,
`datasets/aug09/set-05/qa_work/iterative_flat_realdata.json`,
`datasets/aug09/set-05/qa_work/iterative_flat_downstream.json`,
`datasets/aug09/experiments.jsonl`.

---

## 1. The decomposition — done first, before anything was designed

The brief asked for this measurement before any build, and it turned out to be
the most valuable thing in the session. Instrument: Siril `fdiv <B> <scalar>` on
pairs of flats built by the SAME builder from the SAME night, lens, focal and
aperture — which cancels vignetting and the instrumental base **exactly**, with
no model and no fit — then Siril `stat` medians on regional crops (box 400 /
margin 200). `idiv` is never used; it clips at 1.0 silently.

**No-clip control PASSED, and the operator choice is not academic here.** The
05/01 pair was built at scalar 0.5 and 0.25; every regional median rescales by
exactly **2.0000**, so no truncation is moving them. Whole-frame `Max` reads
65535.0 at *both* scalars, which per the registry is a genuine
divide-by-near-zero spike (a few dead pixels), not bulk clipping.

Running the same pair through the forbidden `idiv` shows what the contract is
protecting: this ratio's median is ~1.07, i.e. it **straddles 1.0** — the case
the registry calls catastrophic rather than survivable — and `idiv` returns a
whole-frame **median of exactly 65535.0** with the TL corner reading 65534.9
where the true ratio is **1.2085**. Over half the frame pinned at the clip, and
the corner structure that this entire decomposition rests on simply gone.

### The five aug09 flats, one instrument

| | set-01 | set-02 | set-03 | set-04 | set-05 |
|---|---|---|---|---|---|
| corner ratio | 1.127 | 1.211 | 1.317 | 1.403 | 1.468 |
| **L/R — grows** | 1.0729 | 1.1450 | 1.2543 | 1.3391 | **1.3806** |
| **T/B — stable** | 0.9542 | 0.9485 | 0.9573 | 0.9599 | **0.9455** |
| edge dipole x | −0.1026 | −0.1651 | −0.2766 | −0.3611 | −0.3853 |
| edge dipole y | −0.0659 | −0.0771 | −0.0638 | −0.0625 | −0.0838 |

The dose curve the brief cites is confirmed (1.127 → 1.468, brightest BL,
darkest TR in every set). The decomposition is sharper than "a growing term on a
stable base": **the two terms live on different axes.** L/R runs 1.0729 → 1.3806
while T/B holds 0.953 ± 0.006, and the edge dipole x grows 3.75× while dipole y
is flat.

### The ratios — where the base cancels exactly

| pair | corner ratio | L/R | **T/B** | edge dipole x |
|---|---|---|---|---|
| 05/01 | 1.312 | 1.2955 | **0.9867** | −0.2851 |
| 04/01 | 1.258 | 1.2538 | **1.0031** | −0.2621 |
| 03/01 | 1.179 | 1.1721 | **1.0005** | −0.1813 |
| 02/01 | 1.075 | 1.0670 | **0.9928** | −0.0682 |
| 03/02 | 1.108 | 1.0983 | **1.0077** | −0.1133 |
| 04/03 | 1.077 | 1.0696 | **1.0029** | −0.0802 |
| 05/04 | 1.049 | 1.0329 | **0.9844** | −0.0237 |

**In every ratio T/B cancels to 1.000** (0.9844–1.0077, mean 0.998). The
top-bottom term is identical in all five flats and is therefore fixed in sensor
coordinates. The left-right term is what differs, and it composes
multiplicatively as a dose should: the four consecutive increments multiply to
1.0670 × 1.0983 × 1.0696 × 1.0329 = **1.2944** against the directly measured
05/01 value of **1.2955** — agreement to **0.08%**.

**SCOPE, and it matters.** A ratio cancels whatever is COMMON to both flats, so
it measures the CHANGE in sky, not the total. Any sky term that was already
present in set-01 and did not vary cancels into the "stable base" alongside the
instrumental term. The ratio therefore gives a *lower bound* on the sky
contamination, and the stable base is "instrument + any static sky", not
"instrument".

### The cross-night discriminator — and it corrects the reading above

Same instrument over every sky flat in the corpus, three nights, same body, lens
and focal (`scripts/qa/flat_odd_component.py`, load average 5.86):

| flat | L/R | T/B | corner ratio | c/centre | dipole x | dipole y | bright/dark |
|---|---|---|---|---|---|---|---|
| july31/set-01 | 0.6343 | 1.1393 | 1.776 | 0.5120 | **+0.4360** | +0.1211 | TR/BL |
| july31/set-02 | 0.6684 | 1.1602 | 1.717 | 0.5133 | +0.3795 | +0.1402 | TR/BL |
| july31/set-03 | 0.7093 | 1.2087 | 1.686 | 0.5105 | +0.3260 | +0.1851 | TR/BL |
| july31/set-04 | 0.7892 | 1.2160 | 1.525 | 0.5113 | +0.2208 | +0.1779 | TR/BL |
| aug06/set-01 | 0.8953 | 0.9680 | 1.152 | 0.5305 | +0.1087 | −0.0684 | BR/TL |
| aug06/set-02 | 0.9383 | 0.9676 | 1.105 | 0.5346 | +0.0692 | −0.0611 | BR/BL |
| aug06/set-03 | 1.0046 | 0.9685 | 1.076 | 0.5369 | **−0.0255** | −0.0596 | BR/TR |
| aug09/set-01 | 1.0729 | 0.9542 | 1.127 | 0.4794 | −0.1026 | −0.0659 | BL/TR |
| aug09/set-02 | 1.1450 | 0.9485 | 1.211 | 0.4807 | −0.1651 | −0.0771 | BL/TR |
| aug09/set-03 | 1.2543 | 0.9573 | 1.317 | 0.4848 | −0.2766 | −0.0638 | BL/TR |
| aug09/set-04 | 1.3391 | 0.9599 | 1.403 | 0.4856 | −0.3611 | −0.0625 | BL/TR |
| aug09/set-05 | 1.3806 | 0.9455 | 1.468 | 0.4942 | **−0.3853** | −0.0838 | BL/TR |

**L/R rises monotonically WITHIN every night, on all three nights** — july31
0.634 → 0.789, aug06 0.895 → 1.005, aug09 1.073 → 1.381 — and the edge dipole x
sweeps continuously from **+0.436 through zero (aug06/set-03, −0.0255) to
−0.385**. Focus is not touched inside a night, so a within-night monotonic
change on fixed optics can only be sky; and a term fixed in SENSOR coordinates
cannot change sign across nights on the same body, lens and focal. The
left-right odd component is SKY, decisively.

**This corrects the "stable instrumental base" reading, including my own earlier
framing of it.** T/B cancels to 1.000 in every aug09 ratio, which invites reading
T/B as "the instrument". Across the corpus it is not: july31's T/B runs
**1.139 → 1.216**, above 1 and drifting **+6.7% monotonically through that
night**, while aug06 and aug09 sit *below* 1 (0.968 and 0.946–0.960). T/B
therefore flips sides between nights and drifts within at least one of them, so
it carries sky too.

The honest decomposition is narrower than "L/R is sky, T/B is instrument":

- **Within aug09**, the sky's change happens to lie almost entirely on the L-R
  axis, which is *why* T/B cancels in those ratios. That is a property of that
  night's pointing and horizon geometry, not a general axis split.
- **Across the corpus, neither axis isolates the instrument** — both dipoles
  change sign between nights.
- The part that is constant within a night remains **unattributed** between
  optics and a static sky term. It cannot be assigned to the lens by these data,
  and per-session focus recalibration (standing practice here) is a live
  alternative explanation for a per-session-constant term.

So the brief's premise that the stable base "contains a real instrumental odd
component that is a CORRECT correction" is **not established by this corpus**,
and a fix designed to preserve the T-B term specifically would be preserving
something not shown to be instrumental. That does not license zeroing it either
— the `--desky` regression's signature was driving this term through zero. It
means the attribution is an open question, and the discriminator that would
settle it is stated in §7.

---

## 2. The algebra — why `F0` cancels

Operator semantics, probed on-rig (Siril 1.4.4) rather than assumed:

| command | measured behaviour |
|---|---|
| `calibrate -flat=F` | `C = R/F × k`, `k ≈ mean(F)` (probe: light 1000 ADU, flat mean 0.5 → 661–1984 ADU against a predicted 667–2000) |
| `subsky 1` | subtracts the fitted plane and leaves a **constant pedestal, not zero** (probe: a 500→800 ADU ramp came back uniform at 627.00) |
| `offset v` | adds `v` **in ADU** (`offset 0.5` rounds to a no-op) — and **clips at 0**, contradicting its own help; see §3a |
| `imul F` | exact multiply (probe: matched prediction to every printed digit) |

With `P_t` the fitted plane, `c_t` Siril's pedestal and `m_t` the frame's
pre-subsky median, the five steps compose to:

```
C_t     = k·R_t / F0                      1. calibrate with F0
subsky  → C_t − P_t + c_t                 2. seqsubsky 1 -nodither
restore → C_t − P_t + m_t                 3. restore the frame's own level
imul    → k·R_t − (P_t − m_t)·F0          4. back to the sensor domain
stack   → F1 = k·F0 − ⟨P_t − m_t⟩·F0      5. rebuild
```

(Step 3 is written `restore` rather than `offset` deliberately: `offset` cannot
be used for it, for the reason in §3a.)

Dividing by `F0` is *what removes the gradient from the sky* — that is what a
flat does. So in the flat-fielded domain the sky is already flat, `P_t` is a
constant plane, and `P_t − m_t = 0`. And where a frame's own gradient differs
from the set average, `⟨P_t − m_t⟩ = 0` **because `F0` is that average**. Either
way:

> **F1 = k·F0.** `F0` appears on both sides of the round trip and cancels.

Stated the other way, which is the form the measurements confirm: after `subsky`
the flat-fielded frame is structureless, so `imul` returns `const × F_roundtrip`
and a stack of those returns `F_roundtrip`. **The iteration reconstructs the
flat it was handed.**

This is a hypothesis until executed. It was executed twice.

---

## 3. Four tool facts found on the way, all independently useful

### 3a. `offset` CLIPS AT ZERO in 32-bit float — its own help says it does not

`help offset` states: *"In 16-bit mode, values of pixels that fall outside of
[0, 65535] are clipped. In 32-bit mode, no clipping occurs."* Measured, on a
uniform 300 ADU card with `offset -500`, reading the SAVED file back with
astropy rather than trusting the tool's own report: the file contains **all
zeros**, not −200.

This is not academic for this repo. A pedestal-free dark-subtracted sky sits
~1.5σ above zero, so a real frame has a large negative minority by construction,
and any `offset` in a chain silently zeroes it. `isub` of a constant card is the
clip-free equivalent (probed: 300 − 500 = −200.0 exactly), and values above
65535 survive fine in 32-bit (`fmul` produced 90000). **Only `offset` clips.**

### 3b. Siril `stat` EXCLUDES zero pixels from its statistics

A card that is half 0 and half 400 ADU reports `Mean: 400.0, Median: 400.0,
Sigma: 0.0, Min: 0.0` where the true values are 200 / 200 / 200. Zeros are
dropped from the estimators while `Min` still reports 0.0, and an all-zero
region reports *"Statistics computation failed for channel 0 (all nil?)"*.

**Together, 3a and 3b are a trap that hides its own damage**: `offset` zeroes a
frame's negative minority, and `stat` then reports the survivors as clean
numbers. The first real-data run of this experiment was corrupted exactly this
way — a −56443 ADU `offset` drove the corners to zero and the flat's corners
read "all nil" — and it was caught only by reading the saved pixels back
independently. That run was discarded and every arm re-run clip-free.

### 3c. `stack` writes no negative values

Measured on the discarded run, whose input frames were 99.99% negative: the
stacked output was **100% zeros**. Nothing but clipping produces that. A
pedestal-free sky's lower tail therefore does not survive a stack, which is a
property the shipped builder already lives with (its `pp_` inputs are 0.24%
negative) but which any scheme reasoning about signed intermediates must know.

### 3d. A hard block: `seqsubsky` refuses negative images

`seqsubsky` **refuses to run on the flat-fielded frames**:

```
Failed to generate background samples for image 0:
removing the gradient on negative images is not supported
```

Pedestal-free dark-subtracted lights carry negative pixels by construction (the
builder deliberately subtracts the ~1k ADU pedestal), and flat division only
amplifies them — the calibrated aug09/set-05 frames measure a minimum of
**−56343 ADU**, from division by the flat's near-zero dead pixels. Step 2 of the
brief's scheme cannot execute as written on real data.

This is a crash, not a mechanism test, so the scheme was given its fairest
possible run: a constant pedestal (56443 ADU here) added before `subsky` and
verified positive by a guard that can fail. The pedestal **cancels exactly** out
of the operator — the plane fitted to `C+P` is `(plane of C) + P`, so `subsky`
returns `C − P_t + c_t` either way, and step 3 sets the absolute level
regardless. It costs nothing numerically: the gradient still resolves to ~2250
float32 levels at that pedestal.

---

## 4. The synthetic fixture — with the positive control that makes it a test

Truth is known by construction: frames are `(sky × (1+g) + moving stars) × V`,
with `V` an EVEN RADIAL vignetting (L/R = 1.000 exactly) and `g` an odd
left-right gradient. 512², 40 frames, seeded, stars drifting so the stack rejects
them. Siril performs every pixel operation and every measurement; numpy builds
the cards only.

**One knob: the flat used for the round trip (steps 1 and 4).**

| arm | round-trip flat | F1 L/R | **gradient removed** |
|---|---|---|---|
| *truth* `V` | — | 1.0000 | — |
| *`F0` — pass 1, today's builder* | — | 1.2378 | — (this is the defect) |
| **A — the scheme as specified** | `F0` | 1.2338 | **1.7%** |
| **B — positive control** | true `V` | 1.0436 | **81.7%** |
| C — break: skip the level restore | `F0` | 1.2338 | 1.7% |
| D — break: degree 2 | `F0` | 1.2331 | 2.0% |

The fixture first reproduces the defect: `F0` bakes the sky in at L/R 1.2378
where the truth is 1.0000, while T/B stays at 1.0078 — the contamination lands
on ONE axis and leaves the other alone, which is the behaviour §1 measures on
the real flats. (The fixture's T/B sits near 1.000 rather than the real corpus's
0.953 because no instrumental odd term was built into `V`; what the fixture
reproduces is the sky term's axis-selectivity, not the corpus's optics.)

**Arm B is what makes arm A's null a measurement.** Handed a clean flat, the
identical code removes 81.7% of the same gradient. So the harness demonstrably
CAN detect recovery, at ~48× the signal arm A produces. Arm A returning "no
change" is a result, not a check that cannot fail.

**The mechanism is visible in the intermediates, not just the endpoints.** The
per-frame median before and after `seqsubsky`:

| arm | pre-subsky median | post-subsky median | restore applied |
|---|---|---|---|
| A (round-trip `F0`) | 46.3 / 46.4 / 46.7 | 46.3 / 46.4 / 46.7 | **0.0 / 0.0 / 0.0** |
| B (round-trip `V`) | 46.1 / 46.3 / 46.6 | 45.2 / 45.4 / 45.5 | 0.9 / 0.9 / 1.1 |

In arm A `subsky` moves the median by **exactly zero** — the flat-fielded sky is
already flat, so the fitted plane is a constant and there is nothing to remove.
That is the `P_t − m_t = 0` of the algebra, measured directly. In arm B, handed
a flat that does not already contain the gradient, the same operator finds one.

Arms C and D are the brief's two deliberate breaks, and their reading is
secondary but consistent: breaking an already-inert mechanism changes nothing.
(Note that degree 2 did NOT destroy the vignetting profile here — c/ctr 0.7093
against the truth's 0.7068 — because in the flat-fielded domain the even
vignetting term has already been divided out, so there is nothing for the even
quadratic to eat. That is not a licence to use degree 2 anywhere the registry
forbids it: the registry's kill is on UN-flat-fielded frames, where the even term
is present and is eaten.)

Both arms confirm the mechanism in the same direction: **F1 tracks its round-trip
flat** (A: 1.2338 vs `F0`'s 1.2378; B: 1.0436 vs `V`'s 1.0000).

### What this fixture could NOT catch — worth more than the arms

The fixture's master dark is **zeros**, because synthesising a realistic dark was
not the point. That made it blind to a whole class of defect: the first real-data
run double-subtracted the dark (the `pp_` frames are already dark-subtracted and
`-dark=` was passed again), which drove the calibrated frame to a median of
**−1247 ADU at 99.99% negative** and left every later stage fitting noise. A
double subtraction of a *zero* dark is a no-op, so the fixture passed green
through the exact bug that invalidated the real run.

The registry's fixture-discipline entry requires that a fixture exercise the live
path; this is a sharper corollary — **a fixture whose calibration frames are
trivial cannot exercise calibration**, and "it passes on the fixture" earns
nothing about the stages the fixture stubbed out. What caught it was reading the
saved pixels back with an independent reader at every stage, not any assertion
inside the harness.

---

## 5. Real data, live path — aug09/set-05

100 frames, Siril doing every step: `convert` → `calibrate -dark` →
`calibrate -flat=` → `seqsubsky 1 -nodither` → level restore → `imul` → `fmul`
→ `stack rej w 3 3 -norm=mul`. The arm's own control, `F0_100`, is built from
the **same 100 frames**, so nothing is confounded by frame selection. It reads
L/R 1.3939 against the shipped 500-frame flat's 1.3806 — the subset is
representative to 1%.

**One knob: the round-trip flat.** Arm B is handed a flat from a DIFFERENT set
of the same night, carrying a different sky dose (set-01, L/R 1.0729), so the
gradient difference is still in the sky when `subsky` sees it.

| | round-trip flat | F1 L/R | F1 T/B | F1 dipole x | F1 / its round-trip flat |
|---|---|---|---|---|---|
| control `F0_100` | — | 1.3939 | 0.9575 | −0.3920 | — |
| **A — as specified** | `F0_100` (1.3939) | **1.3891** | 0.9582 | −0.3880 | L/R **0.9967**, T/B 1.0004, c/ctr 0.9998 |
| **B — positive control** | set-01 flat (1.0729) | **1.0940** | 0.9498 | −0.1154 | L/R **1.0146**, T/B 0.9932, c/ctr 1.0108 |

**Arm A removes 1.2% of the gradient** (1.3939 → 1.3891 against a target of
1.000), and `F1/F0` is flat to 0.33% in L/R and 0.04% in T/B — i.e. `F1` is `F0`
rescaled, which is `F1 = k·F0` measured directly.

**Arm B is the result that names the mechanism.** It was fed *set-05's* frames,
whose own sky dose is 1.3939, and handed *set-01's* flat. It returned
**1.0940** — set-01's value, not set-05's — closing **93.4%** of the distance
between the two. Its dipole x came back at −0.1154 against set-01's −0.1026,
not set-05's −0.3920. The output is a function of the flat it was handed and
essentially not of the frames' own sky dose.

Arm B moved L/R by 0.2999; arm A moved it by 0.0048. **A 62× discrimination on
real data**, one knob apart.

Both arms preserve the even radial term (c/centre 0.4974 and 0.4982 against the
control's 0.4973), so nothing was destroyed. In arm A nothing was *changed*
either — its T/B comes back at 0.9582 against the control's 0.9575. Arm B's T/B
reads 0.9498, tracking set-01's 0.9542 rather than set-05's 0.9575, which is the
same "returns the flat it was handed" behaviour showing up on the second axis.

Implementation notes for reproduction: the calibrated frames measured a minimum
of −2635 ADU (A) and −2223 ADU (B), so pedestals of 2735 / 2322 ADU were added
before `seqsubsky`, verified by a guard that can fail (pedestalled minima 1145.9
and 639.9 ADU, required ≥ 0). The pedestal cancels exactly out of the operator.

---

## 6. Downstream — the declared delta

Siril `calibrate -flat=` divides by the flat and rescales by the flat's own
mean, so a flat differing only by a constant produces an identical calibrated
frame. The same 4 dark-subtracted lights were calibrated with `F0`, with `F1`,
and — as a **deliberately broken guard** — with set-01's flat, then differenced
with `isub` **in both directions** (a one-way nil would only prove `A ≤ B` if
`isub` clipped).

| pair | mean difference |
|---|---|
| F1 vs F0 | **−0.0 ADU** (and 0.0 reversed) |
| BROKEN vs F0 | **0.2 ADU** (and −0.2 reversed) |

On a ~49 ADU sky the F1-vs-F0 difference is below the printed 0.1 ADU
resolution, while the broken arm registers — so the comparison can see a
difference and there is none to see.

The tilt left in the calibrated light, same regional instrument:

| flat used | calibrated light corner L/R |
|---|---|
| `F0` | 0.99390 |
| `F1` | 0.99796 |
| BROKEN (set-01's flat) | **1.29919** |

**The broken arm validates the whole instrument arithmetically**: 1.29919 is
exactly 1.3939 / 1.0729, the ratio of the two flats' own doses. Calibrating with
the wrong night's dose prints that mismatch as a 30% tilt.

**Reading it honestly, because the obvious reading is the trap the registry
names.** The sky flattens to ≈0.994 under `F0` *because* `F0` absorbed the sky's
gradient — the registry calls this flatness check self-fulfilling, and it is not
evidence the calibration is clean. So the 0.994 → 0.998 move is **not** a measure
of the object-tilt fix. The object tilt is set by the flat's OWN non-radial
content, which went 1.3939 → 1.3891: **1.2% of the defect, consistent with §5
and with the fixture.** No judgment surfaces were produced, because a 1.2% change
in a flat that calibrates to a sub-0.1-ADU frame difference has nothing for
anyone's eyes to adjudicate.

---

## 7. What this does and does not settle

**Killed:** the domain-corrected iteration as specified. Not by tuning — by
structure. No parameter choice reaches it, and a second pass cannot help: the
fixed point of `F1 = F_roundtrip` is reached on the first iteration.

**NOT killed, and explicitly still open:**

- **The defect itself.** A sky flat still converges to `sky × V` and still leaves
  the object carrying a multiplicative tilt. Nothing here corrects it, and the
  `--desky` entry's "STILL OPEN" clause stands unchanged.
- **The 3.11% / 241σ figure still has no tracked record.**
  `BACKLOG:calibration-evidence` keeps that gap. This work did not close it —
  see *Deferred*, below.
- **Background extraction in the correct domain, on the LIGHTS.** That is
  `--subsky-lights`, a different and already-restored step; this NULL says
  nothing about it and must not be cited against it.
- **The time-differential route the decomposition opens.** The dose term
  composes multiplicatively across a night to 0.08%, sweeps monotonically within
  all three nights, and passes through zero mid-corpus. Whether that supports
  recovering an instrument-only flat by extrapolation is an untested hypothesis
  and a separate experiment with its own pre-registration. Recorded as a
  candidate, not a plan.
- **Which part of the flat is actually the instrument.** §1 shows neither axis
  isolates it. The discriminator that would: the odd component measured on flats
  from two nights whose POINTING differs while the optical state does not, or —
  cleaner — the same night's flats compared against an independent horizon
  reference (altitude/azimuth per set, which this corpus's EXIF cannot supply,
  no GPS). Until then the constant-within-a-night term stays unattributed
  between optics and static sky, and no fix should be designed on the assumption
  that it is optics.

**Vacuous under a null, and stated so rather than claimed as a pass:** the
brief's acceptance items 3 (july31's correct correction survives) and 4
(starlight survives) are satisfied *by construction* when the operation changes
nothing. They are not evidence for anything and are not reported as passes.

**Deferred, explicitly:**

- **Acceptance 2 — rebuilding all five aug09 flats.** The scheme returns each
  set's own `F0`, so five rebuilds would re-measure five no-ops at roughly 40
  minutes each. The mechanism is established algebraically, on a fixture with a
  positive control, and on the strongest real set (set-05, the largest dose at
  L/R 1.3806). Rebuilding the other four buys no new information about a
  cancellation that does not depend on dose size.
- **Acceptance 6 — the catalogue-free object-tilt test.** This measures the
  ORIGINAL WOUND, not this scheme, and a null fix cannot shrink a tilt. It
  remains the right test and it remains designed in
  `BACKLOG:calibration-evidence`; it is a separate experiment with its own
  hypothesis, and folding it into a killed arm would confound the record.

**Not touched, per the brief:** the 1.20 corner-asymmetry WARN threshold is
unchanged. Loosening an acceptance measure is a user ratification and was never
part of this work.

---

## 8. Why nothing was implemented

The brief specified a flag on `build_sky_flat.sh`, default OFF. It was not
added. Shipping a flag whose mechanism is measured inert would put dead code
behind a switch nobody should ever throw, and would carry a removal condition
for a divergence that does not exist — the builder never diverged, because the
scheme never worked. `build_sky_flat.sh` is untouched; `git diff` on it is
empty.

The corresponding removal-conditions row was therefore also not added: there is
no new divergence to retire. The BACKLOG entry that governs the underlying
defect (`calibration-evidence`) is updated instead, with this route marked dead
so the next session does not re-derive it.
