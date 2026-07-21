# Synthetic flats & bias — calibrating a flatless / biasless set (deep dive)

> **Read this as the researched ROUTE MAP for the flat/bias stage of the operating
> loop, not a fixed recipe.** Official tools do every pixel op; this records what
> each route corrects, what it cannot, and which route the DATA + priorities pick.
> Primary sources are cited inline; each claim is flagged VERIFIED (survived the
> adversarial pass) or DISPUTED. Durable findings graduate into
> [`../TOOLS.md`](../TOOLS.md), [`dead-ends.md`](dead-ends.md), and
> [`../BACKLOG.md`](../BACKLOG.md).

- **Question** — When real flats AND bias are MISSING, what are the well-known
  routes for synthetic flats + synthetic/master bias, and is there a route better
  than a background-model division? Which route does a **dust-first** DSO set pick?
- **Context** — OSC Bayer, uncooled mirrorless + camera lens (Nikon Z6III, 70 mm),
  wide-field, **fixed-tripod** so the sky drifts ~1500 px across the sensor over
  the session (373 lights); **matched darks exist** (214 × 6 s/ISO1600, QA-clean);
  headless Linux — Siril 1.4, GraXpert, ASTAP; PixInsight is reference-only
  (GUI/paid). **Priority #1: preserve faint cosmic dust / IFN** ([[preserve-cosmic-dust-is-the-priority]]).

## The two "dusts" (do not conflate — they are opposites)
- **Sensor dust motes** (dark donuts, dust on sensor/filter) = a DEFECT a flat removes.
- **Cosmic dust / IFN / faint nebulosity** = the SIGNAL to keep — the science target.
A **flat corrects the multiplicative sensor response and never subtracts sky
signal**, so a correct flat *preserves* cosmic dust. The threat to cosmic dust is
the additive **background-extraction** step, not the flat (see Area 4).

## Area 1 — Model-division synthetic flat (vignetting only)
- **VERIFIED — what it corrects:** dividing a frame by a smooth low-frequency
  background model compensates **vignetting + low-frequency gradients**. Siril's
  Background Extraction has a Division mode "mainly used to correct multiplicative
  phenomena, such as vignetting" (siril.readthedocs.io/en/stable/processing/background.html);
  GraXpert exposes `-correction Division` (github.com/Steffenhir/GraXpert README;
  siril.readthedocs.io/en/stable/processing/graxpert.html), mechanically per-channel
  `imarray / background × mean`.
- **VERIFIED — what it CANNOT correct:** dust motes/donuts and pixel-to-pixel
  response (PRNU). The model is a low-degree polynomial (≤4) or RBF (Siril) or a
  heavily-downsampled AI inference (GraXpert) — too coarse to carry mote edges or
  per-pixel gain. Siril's own gradient tutorial states background removal only
  **reduces** vignetting and a **real master flat is preferred** (siril.org/tutorials/gradient/).
- **SETTLED HERE (empirical, installed Siril 1.4.4):** Siril's *native headless*
  background command is **subtraction-only** — `subsky { -rbf | degree } [-dither]
  [-samples] [-tolerance] [-smooth] [-existing]`, no `-mode`/division. `subsky 1
  -mode=divide` returns *"Unknown parameter -mode=divide, aborting"* on the installed
  1.4.4. (The online "stable" Commands docs describe `-mode=subtract|divide`, so they
  either track a newer build or the GUI — a **doc-vs-binary conflict the empirical
  test resolved against the docs**; RETEST on the x86 Siril version: if `-mode=divide`
  is live there it is a NATIVE headless division-flat and GraXpert isn't needed for
  vignetting.) The Division correction otherwise lives in the GUI dialog. So **headless model-division needs GraXpert**
  `-correction Division` — official on x86; the arm build is the geeksville fork
  (audit-only, [[arm-rig-not-a-processing-target]]).
- **DUST-SAFE:** a smooth-model division scales illumination and never subtracts
  the IFN, so cosmic dust is preserved. (The dust threat is the *subtraction*
  background step — Area 4 — not this.)

## Area 2 — Sky flat / night-sky flat (from the lights)
- **VERIFIED — the technique:** median/σ-combine many **un-registered** frames; the
  moving sky rejects and the **sensor-fixed vignetting + dust motes + PRNU** remain
  — a real flat built from the lights (cloudynights.com/topic/755356; chaoticnebula.com;
  ianmorison.com/producing-a-flat-frame-from-a-light-frame; clarkvision.com/articles/nightscapes).
  Uniquely among synthetic routes it **captures dust motes + PRNU** a model cannot.
- **VERIFIED — the enabling condition:** a **20–100 px shift between frames is
  enough**; frames whose FOV did not move cannot be used (stars stay put). Dither
  OR unintentional/fixed-tripod **drift** satisfies it — july14's ~1500 px drift
  far exceeds the threshold.
- **VERIFIED — the decisive limit for a dust-first set:** the method works **only
  when faint structure is a SMALL portion of the frame**; **large-area faint signal
  (Milky Way filling the frame) contaminates the flat** and must then be removed by
  **manual clone-stamping** (trappedphotons.com/blog/?p=756; ianmorison; chaoticnebula).
  A contaminated flat, divided in, would **attenuate the very cosmic dust we must
  keep**. Secondary limits: poor SNR (few night-sky photons) and moonlight/gradient
  contamination (aavso.org/advantage-sky-flats-instead-lightbox-flat;
  cloudynights.com/topic/755356 "are sky flats truly flat").
- **VERIFIED — OSC caution:** flats apply BEFORE debayering, so a non-white
  sky-flat light source distorts colour through the debayer non-linearly and is not
  cleanly fixed by later RGB adjustment (cloudynights forum) — a caution against
  twilight/blue sky flats for OSC.
- **Headless?** The BUILD is pure Siril (convert un-registered → median/rej stack →
  `idiv` the lights by it) — identical tool, buildable here. The **clone-stamp fix
  is NOT headless** (GUI, subjective, non-reproducible) — a hard mark against it for
  a frame-filling field.

## Area 3 — Bias: skip it (CMOS), or synthesize a constant offset
- **VERIFIED — skip real bias on CMOS:** separate bias frames are unneeded and can
  **actively degrade** calibration; the bias signal is retained inside the matched
  darks (aavso.org/bias-frames-and-cmos-cameras-scaled-and-unscaled-darks;
  britastro.org/forums/topic/bias-frames-for-cmos). CMOS dark current is **not
  constant across exposure** (ASI2600 test: 0.161 e/px/s @10 s → 0.010 later), so
  **dark-SCALING (which needs a bias baseline) is invalid on CMOS** — use unscaled
  matched darks and no bias (aavso scaled/unscaled-darks).
- **VERIFIED — Siril synthetic bias:** subtract a single **constant ADU offset**
  from flats instead of a noisy master bias — `calibrate flat -bias="=256"` or
  `-bias="=64*$OFFSET"` (the `=`,`$`,quotes are mandatory). Siril recommends this
  (offset is very uniform on modern sensors; subtracting any real masterframe adds
  noise) — siril.org/tutorials/synthetic-biases; siril.org/2021/12/enough-with-dark-flats.
- **DISPUTED:** Siril's "enough with dark-flats" argues a synthetic offset suffices
  and dark-flats are usually unnecessary — which **contradicts the modern-CMOS
  consensus** of dark-flats over bias. Recorded as an open disagreement; moot for
  july14, which shoots no flats.
- **PixInsight SuperBias** models/smooths a master bias to behave as if built from
  thousands of frames (stack 100+ bias, then SuperBias) — noise-free master bias
  (pixinsight.com/forum SuperBias). GUI/paid → x86; irrelevant when skipping bias.

## Area 4 — The hierarchy, and the background-extraction dust threat
Ranked by what each route fixes (VERIFIED across siril calibration docs, lightvortex,
the sky-flat sources):
1. **Real flat** — corrects vignetting + **dust motes + PRNU** (all multiplicative
   effects). Cannot contain sky signal, so it **cannot erase cosmic dust**. Best.
2. **Sky flat** — same corrections **only if** the field is not frame-filling faint;
   otherwise contaminates (Area 2).
3. **Model-division** — vignetting/gradients only; dust-safe; no motes/PRNU.
- **The cosmic-dust threat is the additive BACKGROUND step, not the flat.**
  GraXpert AI BGE / DBE / Siril `subsky` at high degree **model and subtract** a
  background; a frame-filling faint complex is absorbed and erased (repo dead-end;
  suffolksky.com AI BGE). Guard: dust-safe background only — **first-degree `subsky
  1` plane, or off** for object-filling fields.
- **No flat at all?** For a wide-field fixed-tripod set where faint signal is NOT
  the goal, a dust-safe plane background can suffice; for a **dust-first** target it
  leaves vignetting as a residual and motes/PRNU uncorrected — an honest gap, not a
  full substitute.

## The july14 decision (the loop's RECOMMEND → RECORD)
Data: flatless + biasless; 214 clean matched darks; 373 lights; ~1500 px drift;
70 mm wide (likely frame-filling MW/IFN); **dust #1**. Constraints: **real flats are
off the table** (the lens was cleaned after the session, so no flat can match the
as-shot mote/optical state); tool-identity gates build-here to Siril.

- **Bias:** NONE — the matched darks carry it (CMOS). A synthetic constant offset
  only if a flat ever needs calibrating.
- **Flat — routes carried + gated:**
  - *Real flat:* impossible for this set (lens cleaned).
  - *Sky flat — TESTED CLEAN, the recommended route:* the 373-frame un-registered
    median (Siril, ~1500 px drift) came out smooth radial vignetting (~6% center-to-
    corner; Siril regional means center 1131 vs corners 1060–1086 ADU) + a mild
    left-right residual gradient, with **NO IFN structure baked in** — the drift +
    median rejected the sky. It corrects vignetting + motes + PRNU and is **dust-safe
    by validation** (the structured IFN is not in the flat). Adopted as the flat
    candidate, GATED on the user's eyes + a with/without comparison on full-frame
    lossless finals (dust the deciding metric). Record:
    `datasets/july14/set-01/qa_work/skyflat_qa.json`.
  - *Fallback if the sky flat is rejected on the finals:* vignetting-only GraXpert
    `-correction Division` (dust-safe, x86 official); on the arm rig now, no flat +
    a first-degree `subsky 1` plane (MW-safe background), vignetting a small residual.
- **Darks:** all 214 (QA-clean, flat pedestal — [[preserve-cosmic-dust-is-the-priority]] n/a; darks don't touch sky signal).
- **Trade-off (honest):** the validated sky flat corrects vignetting + motes + PRNU
  on the arm rig now — no gap — IF it passes the finals comparison. Residuals to
  tighten: a mild low-order L-R gradient (better left to the first-degree background
  step; smooth the flat to radial-only) and faint un-rejected star specks (a
  winsorized/sigma rejection removes them). If the finals reject the sky flat, the
  gap reopens (vignetting-only division → x86; motes/PRNU uncorrected) until a future
  session shoots real flats before cleaning.

## What graduates
- **[`../TOOLS.md`](../TOOLS.md):** the flat/bias route rows — synthetic flat =
  GraXpert Division (vignetting only, dust-safe, x86 official); Siril `subsky`
  subtraction-only (no headless division, empirically confirmed); sky flat
  (Siril-native, captures motes/PRNU, contaminates on frame-filling faint); bias =
  skip on CMOS, synthetic constant offset if needed.
- **[`dead-ends.md`](dead-ends.md):** the sky-flat contamination mechanism
  (frame-filling faint → baked into the flat → clone-stamp is the only fix, non-
  reproducible); CMOS skip-bias + invalid dark-scaling.
- **[`../BACKLOG.md`](../BACKLOG.md):** x86 GraXpert-Division vignetting correction
  as the dust-safe flat for flatless dust-first sets; realize the flat/bias route in
  the x86 chain's operating loop.

## Sources
Primary (tool docs):
- https://siril.readthedocs.io/en/stable/processing/background.html
- https://siril.readthedocs.io/en/stable/processing/graxpert.html
- https://siril.readthedocs.io/en/stable/preprocessing/calibration.html
- https://siril.org/tutorials/gradient/
- https://siril.org/tutorials/synthetic-biases/
- https://siril.org/2021/12/enough-with-dark-flats/
- https://free-astro.org/index.php/Siril:Commands
- https://github.com/Steffenhir/GraXpert/blob/main/README.md
- https://pixinsight.com/forum/index.php?threads/superbias-a-practical-example.7068/

Practitioner / forum / reference:
- https://www.aavso.org/bias-frames-and-cmos-cameras-scaled-and-unscaled-darks
- https://www.aavso.org/advantage-sky-flats-instead-lightbox-flat
- https://britastro.org/forums/topic/bias-frames-for-cmos
- https://www.cloudynights.com/topic/755356-are-sky-flats-truly-flat/
- https://www.cloudynights.com/forums/topic/777968-dust-spots-removal-with-synthetic-flat-halo-reduction-with-pixel-math-mmt/
- https://www.cloudynights.com/forums/topic/899344-questions-about-flat-frames/
- https://www.lightvortexastronomy.com/tutorial-pre-processing-calibrating-and-stacking-images-in-pixinsight.html
- https://www.ianmorison.com/producing-a-flat-frame-from-a-light-frame/
- https://chaoticnebula.com/learn-to-take-sky-flats-for-astrophotography/
- https://clarkvision.com/articles/nightscapes/
- https://astrobackyard.com/how-to-take-flat-frames/
- http://trappedphotons.com/blog/?p=756
- http://www.suffolksky.com/2024/04/25/background-extraction-and-noise-reduction-using-ai-for-free/

## Status
ADOPTED AND HARDENED INTO A RULE. The sky flat is the production flatless route,
built per set by `scripts/stack/build_sky_flat.sh` (dark-subtracted, CFA,
un-registered, winsorized — specks measured 101 → 0 vs the pure median this doc
proposed). **The rule this research did not yet know (measured, user-ratified): a
flat calibrates ONLY the exact frames it was built from** — the flat's low-order
term carries its SOURCE set's residual sky gradient, so cross-set application
imprints it (±6% L-R tilt measured; sensor content transfers, the sky term does
not) — mechanism + numbers in [`dead-ends.md`](dead-ends.md), the A/B in
`datasets/july14/set-03/experiments.jsonl` (flat_source_set03). The with/without
dust gate rides the standing judgment surfaces (dust measured REVEALED, not
erased, on every adopted render); Area 2's contamination limit still binds each
new set's flat, checked by the builder's validation gates.
