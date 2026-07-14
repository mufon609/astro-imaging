# Narrowband star-neutral / OIII-sphere / Ha-OIII unmix options — deep dive

- **Question / scope** — What tools/mechanisms now recover narrowband OIII that SPCC
  crushes — the "OIII sphere" problem — and do any run **headless on Linux, no GPU**?
  The dead-end registry records that SPCC equalizes OIII=Ha and erases the sphere,
  and the fix is a star-colour-neutral balance (a genuine native-Siril gap). This
  updates TOOLS.md Tier 10 and that dead-end.
- **Context** — 2026-07-14. Rig: x86-64 Kali, no GPU, headless. Native Siril has no
  star-population-measured neutral balance ([[siril-natives-and-trailed-solve]]:
  SPCC `-narrowband` is physical bandpass calibration, not a star-neutral white ref).
  Tool architecture per [[siril-pyscript-headless]].

## Findings

### Two DISTINCT mechanisms (they apply to different data classes — don't conflate)
1. **Star-colour-neutral balance** (the dead-end registry's mechanism, for **mono**
   Ha/OIII/SII): stars carry ~no OIII, so neutralizing the mean star colour boosts
   OIII → reveals the sphere. Nightlight's mechanism; still no native Siril tool.
2. **Ha/OIII Bayer crosstalk unmix** (for **OSC dual-band** data): solve the
   per-sensor QE crosstalk to separate Ha and OIII from the Bayer RGB triplet, then
   normalize/boost OIII. This is what **DBXtract / VeraLux Alchemy** do.

### VeraLux Alchemy — the direct match, but GUI-only (Class-1)
- A Siril 1.4+ pyscript (author Riccardo Paterniti, **v1.0.3**, free, donation).
  Purpose: *"Linear-Phase Narrowband Normalization & Mixing"* — normalize+mix dual-band
  OSC *before stretch*, aligning weak OIII to the strong Ha reference.
- **Mechanism (verified in source):** `_quantum_unmix_ha_oiii()` — dual-band Ha/OIII
  separation using **sensor-specific crosstalk compensation coefficients derived from
  DBXtract** ("a physical signal model, not a correction"): per-channel median-bg
  subtract → solve Ha/OIII amplitudes from the RGB triplet → **background alignment**
  (shift weak channels to Ha black point) → **MAD-based gain matching** → a **manual
  OIII boost (0.5×–5.0×)** → linear per-RGB blend. **All linear, output stretch-ready.**
  This is exactly the "reveal the OIII the SPCC fit erased" move — it does NOT equalize
  OIII=Ha.
- Free, **CPU-only** (numpy/astropy), runs on Linux inside Siril — **but GUI-only
  PyQt6** (QMainWindow, sliders, live MTF preview): **no headless/CLI mode.** A Class-1
  numpy-inside script → per the philosophy resolution, an escape-hatch tool, and not
  even headless as written.

### DBXtract — the GPL-3.0 reference primitive
- `processing/DBXtract.py` in the Siril repo (author Raúl Hussein / Astrocitas;
  PyQt6 port by Adrian Knagg-Baugh of the Siril team; **GPL-3.0**, **v1.0.1**).
- **The open reference implementation of the Ha/OIII (and SII/OIII) Bayer-crosstalk
  unmix**: a **QE lookup table for 12 IMX sensor models (9 coefficients each)**,
  per-channel median-bg subtract, OIII estimated from green+blue weighted by QE
  ratios, **linear equations solved to isolate each narrowband from RGB crosstalk**,
  adaptive dual-OIII combine.
- Linux (via Siril), CPU, free — **GUI-only PyQt6, no headless.** But its **published
  per-sensor coefficient tables + documented linear solve are the mechanism to
  orchestrate/reference** if a headless path is built.

### The rest of the landscape
- **SASpro** (Seti Astro Suite Pro) — has NB→RGB combine **with normalization** +
  **star-based white balance** + "NB to RGB Stars," but **not** a physical
  crosstalk-unmix matrix. GUI-only (Qt), Linux via venv, free GPL-3.0, very active
  (**v1.19.6, 2026-07-13**).
- **Other Siril NB pyscripts** (free-astro repo, Siril 1.4): `ContinuumSubtraction.py`,
  `Hubble_Palette_from_Dual-Band_OSC.py`, `NB_2_RGB.py`, `Narrowband_Palette_Picker.py`,
  `PalettePicker.py` — palette/combine helpers; the consistent repo pattern is PyQt6
  GUI (per-script headless status not individually verified).
- **SyQon / Cosmic Clarity / GraXpert** — **none does narrowband colour** (deconv /
  denoise / star-removal / BGE only).
- **Native Siril** — `ccm` (3×3) / `pm` can apply a *diagonal* or fixed matrix, but
  **not** a star-population-measured neutral balance nor a per-sensor QE unmix. The
  gap stands.
- **Astro Pixel Processor** — commercial duo-band Ha/OIII Bayer-leakage unmix; Linux
  build exists; not headless/CLI for this step.
- **Nightlight** — F did not surface current status; it remains the arm-staged
  star-neutral SHO reference from the dead-end registry, **x86/Linux status STILL
  UNVERIFIED** (a follow-up: confirm whether a current x86 Nightlight build/CLI exists).

## Sources
- VeraLux Alchemy source (`_quantum_unmix_ha_oiii`, mechanism) — https://gitlab.com/free-astro/siril-scripts/-/raw/main/VeraLux/VeraLux_Alchemy.py
- DBXtract source (QE tables, linear solve) — https://gitlab.com/free-astro/siril-scripts/-/raw/main/processing/DBXtract.py
- Siril python-scripts index — https://siril.readthedocs.io/en/stable/scripts/python-scripts-list.html
- SASpro — https://github.com/setiastro/setiastrosuitepro/ · https://www.setiastro.com/seti-astros-editng-suite
- SyQon (not NB) — https://syqon.eu/ · Parallax https://siril.org/2026/06/parallax/
- APP duo-band unmix — https://www.astropixelprocessor.com/community/main-forum/app-ha-oiii-extraction-from-osc-with-duoband-filter-unmixing-bayer-colour-leakage-from-duo-band-filters/
- VeraLux workflow (secondary) — https://www.cloudynights.com/forums/topic/991558-veralux-workflow-in-siril/ · https://www.youtube.com/watch?v=2N6K2KnQy1o

## Verdict / recommendation
- **The exact OIII-recovery mechanisms exist free/CPU/Linux — but all GUI-gated
  Class-1 pyscripts; none ships a headless CLI as of mid-2026.** The headless
  narrowband-colour gap is real and open.
- **For OSC dual-band OIII recovery:** DBXtract is the GPL-3.0 reference (published
  per-sensor QE tables + linear solve); Alchemy adds normalization + OIII-boost +
  star-neutral mixing on top. On a headless box, the doctrine-clean paths are (a)
  orchestrate DBXtract's *documented mechanism* as a sanctioned reference (the
  astrometry.net precedent — mechanism = the GPL-3.0 published tables/solve, removal
  condition = a headless tool ships it), or (b) drive the GUI script under `Xvfb`
  (untested hypothesis, and it is slider-interactive → likely not parameter-drivable).
- **For mono Ha/OIII star-neutral:** re-verify Nightlight on x86; else a `ccm`-driven
  star-population-measured neutral balance remains the native gap to close.
- Do **not** treat Alchemy/DBXtract as first-class "tools" for the harness — they are
  numpy-inside (Class-1); adopt only as sanctioned escape-hatch mechanisms with a
  removal condition.

## Status
**PROVISIONAL.** Mechanisms + versions are PRIMARY-VERIFIED from script source. The
headless-viability claims (GUI-only, no CLI) are source-verified; the Xvfb workaround
is an untested hypothesis. Nightlight x86 status is UNVERIFIED. Applicability
(OSC-dual-band vs mono) is mechanism-derived, not tested on our data.

## Graduation
- **TOOLS.md Tier 10** — add **DBXtract** (GPL-3.0 Ha/OIII crosstalk-unmix reference,
  per-sensor QE tables); sharpen the **VeraLux Alchemy** entry with the actual
  mechanism + GUI-only/Class-1 status; state the two-mechanism / two-data-class split;
  flag Nightlight x86 as unverified; confirm the native star-neutral gap stands.
- **REDESIGN dead-end (SPCC/OIII sphere)** — the star-neutral/unmix mechanism now has
  named free tools (Alchemy/DBXtract) but they are **GUI-gated Class-1**; DBXtract's
  published GPL-3.0 QE tables + linear solve are the headless reference to orchestrate;
  the headless-CLI narrowband-colour gap remains open.
- Applied in the graduation commit.
