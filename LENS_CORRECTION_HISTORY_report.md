# The lens-correction history, and what the defect actually is

Two questions answered here: **what this camera's data has actually been corrected
with, across the whole history in `git`**, and **what we now know about the defect**
that history was chasing. The open question — how the rest of the field handles this
on non-dedicated cameras — is deliberately NOT answered here; it is out with a
fresh-eyes session (`RESEARCH_UNTRACKED_STACKING_PROMPT.md`) so the answer is not
shaped by anything in this repo.

---

## Part 1 — What we now know about the defect

### 1.1 The instrument carries a fixed left-right star-shape gradient

MEASURED on RAW frames — `convert -debayer` only, **no dark, no flat, no lens warp,
no registration, no stack** — three frames per set (first / middle / last), pooled,
800 px boxes, roundness = median min/max over the 120 brightest Siril `findstar` fits:

| set | x=8% | 30% | 50% | 70% | x=92% | left−right |
|---|---|---|---|---|---|---|
| aug06/set-01 | 0.849 | 0.842 | 0.803 | 0.773 | **0.727** | 0.122 |
| aug06/set-02 | 0.851 | 0.844 | 0.785 | 0.791 | **0.698** | 0.153 |
| aug06/set-03 | 0.839 | 0.845 | 0.783 | 0.801 | **0.676** | 0.164 |
| july31/set-01 | 0.871 | 0.862 | 0.845 | 0.812 | 0.818 | 0.053 |
| july31/set-02 | 0.878 | 0.830 | 0.818 | 0.839 | **0.745** | 0.134 |
| july31/set-03 | 0.859 | 0.837 | 0.828 | 0.798 | **0.694** | 0.165 |

**Six of six, both nights, always the same sensor side**, and **monotone across the
field** rather than symmetric about the centre. Monotone is the signature of
DECENTRING or TILT; a radial aberration is symmetric.

**Sidereal trailing geometry is eliminated as the cause.** Untracked trail length
scales as cos(dec), so a field spanning declination trails more on its low-dec side.
But this sensor's x-axis runs mostly along RA: the measured declination span across
the frame is **+42.60° to +40.38°**, which predicts a roundness gradient of **0.011**.
We measure **0.122–0.165** — an order of magnitude larger.

### 1.2 A radial model cannot correct it, and measurably does not

lensfun's `ptlens` is `a·r⁴ + b·r³ + c·r²` — a function of radius alone. A monotone
left-right term is not representable in it. Measured on aug06/set-01: roundness runs
**0.849 → 0.727 before the warp** and **0.931 → 0.851 after it**. The warp roughly
halves the gradient and cannot remove it.

This is the same fact the registry already carried under a different name — a
one-sided component measured with Siril `seqtilt` as "sensor tilt", 0.50/16% →
0.42/13% → 0.51/16% across control → community profile → fitted profile, with the
note *"a radial model cannot fix a one-sided term"* — and `BACKLOG:one-sided-band`.
It was known as tilt at one station and was never connected to the smear.

### 1.3 What the rest of the chain does with it

The gradient is fixed in SENSOR coordinates. The sky drifts across the sensor at
**3.87 px/frame** (from Siril's own registration homographies). Everything downstream
follows from those two facts:

| stage | effect | size |
|---|---|---|
| optics + in-exposure trail, single frame | the gradient above | roundness 0.85 → 0.70 |
| stacking, uniform cost | registration + resampling | +0.16–0.18 px FWHM |
| **stacking at the EXIT edge** | stars leave the frame there, so the homography is least constrained | **+0.25 px**, roundness −0.010 (against +0.019 elsewhere) |
| **per-group registration reference** | each member inherits the gradient at whatever sensor sampling its own auto-picked reference sat at | **up to 3.12 px** of member-to-member disagreement |
| compose of disagreeing members | doubling | union roundness **0.45–0.60** |

The reference term dominates by more than 10×. MEASURED, one knob, identical frames:
five per-block registrations give a worst member pair of **3.12 px**; one global
reference gives **0.48 px**. Siril's auto-picks landed at frames **6, 26, 15, 3, 26
of 50**, and the member that breaks away is always the one whose reference sits
furthest from the rest.

### 1.4 What is ruled out

- **Cross-night combining** — same-night pairs 2.44 px median, cross-night 2.39.
- **The distortion model CHOICE** — all 28 members of the accepted union carry
  identical coefficients, and the smear appears within a single set.
- **Acquisition** — 500 frames, identical exposure/ISO/aperture/focal, 3.00 s
  interval (min 2.99, max 3.01), no gap anywhere.
- **Differential refraction** — target at 72–77° altitude; differential refraction
  across the field moves 1.98 → 1.89 px over the whole run. 0.09 px, wrong direction.
- **A time-progressive optical change** — R² 0.05 against elapsed time.
- **The aug06 "member edge deficit"** that opened this arc — +0.174 / +0.130 /
  +0.175 px across single → warped single → member. Flat, frame-level, far too small.

---

## Part 2 — Every lens correction this camera's data has been through

Recovered from `git`. **At least SEVEN distinct coefficient sets have existed**, and
products were built under several of them.

| # | ptlens a / b / c | origin | status |
|---|---|---|---|
| 1 | 0.012 / −0.017 / 0.039 | **lensfun COMMUNITY profile**, focal=70 | superseded |
| 2 | **0.00350093 / 0.01453356 / 0.00043983** | fitted from july14/set-01's own frames, `0c967a9` | **SHIPPED — the pinned model** |
| 3 | 0.0033627 / 0.0149465 / 0.0005744 | x86 re-fit of the same frames, `887eb00` | candidate, measured NULL vs #2 |
| 4 | 0.00808615 / 0.00191793 / 0.012386 | aug06/set-01 own fit, `ca723da` | reverted |
| 5 | 0.00428142 / 0.0199376 / — | aug06/set-02 own fit, `f9ad45f` | reverted |
| 6 | 0.00191581 / 0.0119443 / 0.00157443 | aug06/set-03 own fit, `f9ad45f` | reverted |
| 7 | 0.00493263 / 0.0125447 / — | a further re-fit, `295aa26` | reverted |

Note the spread. #4's `a` is **2.3×** the shipped value and its `b` is **13% of it**;
#6's `a` is **55%** of the shipped value. These are not small perturbations.

### 2.1 The three eras

**Era 1 — community profile (until `0c967a9`, 2026-07-17).** darktable + lensfun with
the stock `Nikkor Z 24-70mm f/4 S` entry. MEASURED to fix the edges but to WRITE A NEW
DEFECT into the centre: a community radial profile carries a small paraxial error, and
as a star crosses the optical axis during the drift the radial unit vector flips sign,
turning ±ε into a ~2ε smear ALONG the drift — a band through frame centre. Full-depth
centre majFWHM **5.30 px / roundness 0.480** against 3.60–4.12 perpendicular; the
no-model control INVERTS it (centre 4.03, its best). Also killed in that era: keying
lensfun on the SOLVED effective focal (67.8) instead of the calibrated 70 — the
interpolated 50–70 model is worse at the centre (5.42 vs 4.88 px).

**Era 2 — one fitted model, pinned (`0c967a9` → `9095564`, and again from `82ef3c4`).**
Fitted from july14/set-01's own frames by between-frame star correspondence
(Siril → Hugin cpfind/cpclean/autooptimiser, hfov pinned at the solved value).
Accepted on a full-depth A/B against the community profile: centre station **5.30 →
3.67 px**, all-station spread **1.70 → 0.52 px**, `seqtilt` truncated-mean FWHM
3.27 → 3.06. This is the current authority.

**Era 3 — per-set optical states (`9095564` → `82ef3c4`), REVERTED.** The doctrine
"focus recalibrates every session, so the model keys on the OPTICAL STATE, per set"
was adopted and gave sets #4–#7 above. It was **refuted at its root**: its founding
evidence (aug06/set-01 measuring 0.82 px off-axis) was a COMPOSE artifact — that set's
five groups each read 0.40–0.45 px under the pinned model; its discriminator never
discriminated (four independent fits of ONE set span 0.36–6.30 px against a
between-set spread of 4.01–10.99); and it was adopted on 1 WIN / 3 NULL. The cost was
`33c43d8`: **13 aug06 members composed under 3 different models**, producing 2.99 px
of corner disagreement within a night and 5.34 px across nights — visible star
doubling, failed by eye.

### 2.2 What the live database holds now

Verified on-rig. The focal=70 entry is **#2, the pinned model**, and the file carries
its own audit trail:

```
<!-- astro-imaging fitted: focal=70 replaced a=0.00808615… b=0.00191793… c=0.012386…;
     from aug06/set-01; vignetting+tca stripped (0) -->
<distortion model="ptlens" focal="70" a="0.00350093" b="0.01453356" c="0.00043983"/>
```

That comment records that the machine was still carrying **#4** — the reverted
aug06/set-01 per-set fit — until it was replaced at the start of this investigation.
The lensfun user DB is global, unscoped, single-valued machine state that nothing
reverts, which is exactly why the sub-stack header stamp (`DISTA/B/C`, `DISTSRC`,
`DISTPROV`) exists.

---

## Part 3 — What is done now, and why

1. **Calibrate** — dark + per-set synthetic sky flat, `-cc=dark`, CFA-equalised,
   debayered. Ordering is load-bearing: darks and flats are sensor-grid properties, so
   calibration finishes in SENSOR space before any geometric step.
2. **Install and VERIFY the pinned model** — `install_lens_model.sh` writes #2 into the
   lensfun user DB from `lens_models.json`; `lens_preflight.py --require-profile`
   asserts the live DB matches and makes darktable prove it corrects this lens.
3. **Warp** — Siril `savetif32` → darktable `--style lensdist` → Siril `convert`.
   32-bit float throughout, TIFF untagged, `--icc-type LIN_REC709` (a measured perfect
   identity; the older SRGB tag-matching carried a TRC toe error that inflates a
   3 s-class sky).
4. **Register + stack per group** — `register -2pass` → `seqapplyreg -framing=min` →
   rejection by sub count. **This is where the dominant defect is introduced**, via
   the auto-picked per-group reference.
5. **Compose** — members registered together, plain mean, no rejection across
   sub-stacks. Member disagreement is now MEASURED and recorded but no longer gated.

**Why the warp exists at all:** for an ideal rectilinear lens a pure camera rotation
maps exactly to an 8-DOF homography, so the only residual that survives an optimal
global fit on a star field is unmodelled radial lens distortion. Remove the drift *or*
remove the distortion and the homography becomes exact — measured two ways, and it is
why the route is undistort→register rather than a better transform class.

---

## Part 4 — Steps that were done and are no longer done

| step | why it was done | why it stopped | measured cost/benefit |
|---|---|---|---|
| **darktable vignetting + TCA correction** | never chosen — it is darktable's DEFAULT correction set, and a style cannot select which corrections run | `02901f0` strips `<vignetting>`/`<tca>` from the lens's DB block so distortion is the only correction lensfun CAN apply | it was DOUBLE-correcting already flat-corrected lights: corner/centre **1.27–1.37× linear**, 2.2–2.6× stretched |
| **community lensfun profile** | the first working distortion fix | replaced by the fitted model | centre 5.30 → 3.67 px, all-station spread 1.70 → 0.52 |
| **per-set optical models** | a real per-set difference was believed measured | refuted at its root; `82ef3c4` | broke the combine: 2.99 px within a night, 5.34 across |
| **`--desky`** (seqsubsky on the flat's RAW source frames) | to stop the sky baking into the synthetic flat | a DOMAIN error — background extraction is defined on flat-fielded data | **31× regression**: corner spread 12.4% vs 0.4% |
| **16-bit intermediates** | an old rig's RAM/disk limit | condition fired on x86 | the 16-bit chain read only ~55–70% of the 32-bit arm's extended contrast |
| **in-house peak-centroid extractor** | astrometry.net needed a shape-blind xylist | `sep` (SExtractor's core) passed every solve at equal-or-higher odds | logodds 299 vs 289, identical SPCC K |
| **`star_shape_profile.py`** (in-house radial metric) | no tool gave a local star-shape map | its origin was derived from the very detections the defect suppressed | it INVENTED an anomaly a whole session chased |
| **the i450 recrop** | to hide a corner defect | a bandaid — the registered dead-end class | revoked |
| **the compose PASS/WARN/BLOCK gate** | to stop a doubled product shipping | it gated a number that mixes a real defect with one the compose itself creates, and its thresholds were anchored on an instrument that was measuring chance | removed this session, user-ratified; the number is still measured and stamped |

**One step that is available and switched OFF:** `--subsky-lights` (per-frame degree-1
background subtraction on calibrated lights). It is the uncoupled GOOD half of the
reverted `--desky` and defaults to off pending the render-ladder L1 arm.

---

## Part 5 — What is open

**The toolkit gap is now concrete, not hypothetical.** Every frame this rig has shot
carries a 0.12–0.16 roundness decentring term, and the correction tool in the pipeline
models distortion as a function of radius alone. That is not a tuning problem; it is a
model-form problem.

Three things follow, in order:

1. **Pin the registration reference.** Measured 6.5× on the dominant term, one knob,
   and at the per-set product level it costs no field of view — the per-set compose
   already crops to the members' intersection (shipped product 4907×3599 against a
   single-reference member's 4897×3729). Untested variant worth trying:
   one global registration with `-framing=max`, which should keep the swept area too.
2. **Size the exit-edge term.** Same sensor region, sub-blocks of 50/25/12 frames,
   blur at matched sensor x. Flat means a fixed residual; falling with span means
   registration. Uses frames already on disk.
3. **Answer the model-form question from outside this repo** —
   `RESEARCH_UNTRACKED_STACKING_PROMPT.md`. Specifically whether a radial-only profile
   is considered adequate for this work, what PixInsight and the survey pipelines
   model that it does not, and which free headless tool can fit or apply a distortion
   model WITH decentring terms. Designing a fix before that answer is guessing.
