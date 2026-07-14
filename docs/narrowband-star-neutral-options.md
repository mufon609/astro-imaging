# Narrowband star-neutral / OIII-sphere / Ha-OIII unmix options — deep dive

- **Question / scope** — What tools/mechanisms now recover narrowband OIII that SPCC
  crushes — the "OIII sphere" problem — and do any run **headless on Linux, no GPU**?
  The dead-end registry records that SPCC equalizes OIII=Ha and erases the sphere,
  and the fix is a **star-colour-neutral balance** (a genuine native-Siril gap). This
  updates TOOLS.md Tier 10 and that dead-end.
- **Context** — 2026-07-14. Rig: x86-64 Kali, no GPU, headless. Native Siril has no
  star-population-measured neutral balance ([[siril-natives-and-trailed-solve]]:
  SPCC `-narrowband` is physical bandpass calibration; Siril docs themselves say it
  yields *"real intensities" / "a huge green cast"* and **recommend Manual Color
  Calibration for SHO** — i.e. SPCC is verified as the *cause* of the OIII flattening,
  not the fix). Tool architecture per [[siril-pyscript-headless]].

## Findings

### TWO distinct mechanisms — do not conflate (the earlier confusion, corrected)
- **(1) Star-colour-neutral balance (star-ANCHORED):** neutralize the mean STAR
  colour → since stars carry ~no OIII, this lifts OIII/SII relative to Ha and reveals
  the sphere. This is the dead-end registry's mechanism (mono NB or any RGB NB
  composite). Implemented by **Nightlight**, or doctrine-cleanly by **`ccm` fed by a
  measured mean-star-colour**.
- **(2) Nebula-channel normalization / Ha-OIII Bayer crosstalk unmix (nebula-ANCHORED
  or sensor-QE-anchored):** align the weak OIII channel to the strong Ha *nebula*
  signal, or solve the OSC Bayer crosstalk. This is **VeraLux Alchemy / DBXtract** —
  and it explicitly **excludes stars as outliers** (the *opposite* anchor from
  star-neutral). Useful, but NOT the star-neutral mechanism.

### Nightlight — the one tool that does star-neutral by name; headless, but dormant
- Markus Noga, **github.com/mlnoga/nightlight**. Pure-**Go**, in-memory, **headless
  CLI** stack/compose pipeline (`stats/stack/rgb/argb/lrgb`; optional REST+Blockly
  GUI; JSON `-job` spec for scripted orchestration). **Linux x86-64 (+ARM), no GPU**
  (Go + AVX2 SIMD, multi-core), **GPL-3.0**. Reliable install = `go build` from source
  (release ships only a generic zip).
- **The star-neutral mechanism (source-verified):** `OpRGBBalance`
  (`internal/ops/rgb/rgb.go`) is a two-point white balance — black point = darkest
  NxN block; **white point = the DETECTED STARS, skipping the brightest+dimmest
  fractions, balancing the middle star population to neutral `RGB{1,1,1}`.** Forcing
  Ha-dominated (red/magenta) stars to grey redistributes channel weight and **lifts
  OIII/SII relative to Ha** — the described behaviour. Errors if zero stars detected.
  Supporting NB flags: `scnr`, LCH hue-rotation (`rotFrom/To/By`), LCH chroma
  (`chromaFrom/To/By`), `neutSigmaLow/High`.
- **Status: DORMANT.** Latest release **v0.2.6 (2023-02-27)**; last commit
  **2024-01-20**; nothing in 2025-2026; not archived (dormant, not retired). 51 stars,
  no by-name community footprint. Go-toolchain drift is a real risk for a go-forward
  dependency (v0.2.6 was itself a broken-dependency fix).
- (Mechanism is a source reading — a hypothesis about runtime behaviour until built
  and run on x86.)

### The doctrine-clean headless path — measure in the examine layer, apply via native `ccm`
- **`ccm` (3×3 colour matrix, NEW in Siril 1.4.0, headless):** a **diagonal `ccm`
  with gamma=1 is exactly a per-channel multiply** `r'=kr·r, g'=kg·g, b'=kb·b` — i.e.
  a star-neutral balance *if* you supply `(kr,kg,kb)` that equalize the mean star
  colour. `pm` can do the same but `ccm`-diagonal is cleaner for a straight RGB
  per-channel scale.
- **The gap, located precisely:** **no native Siril command outputs a field's mean
  star colour.** SPCC/PCC measure the star population internally but *consume* it to
  fit a catalog white reference; `psf`/`seqpsf` measure *individual* stars, not a
  population colour. So the **measurement** must live in our **examine layer** (numpy
  over `get_image_stars` / detected-star photometry) — which is EXAMINING, squarely
  in-bounds — and the **application** is native + headless (`ccm` diagonal).
- **This is the cleanest approach we've identified (a design, untested here):** it is
  fully headless, uses a real tool for the pixel op (Siril `ccm`), keeps only
  measurement in our code, and needs neither the dormant Nightlight nor a GUI-gated
  script. It also unifies with the
  audit side ([[objective-qa-defect-metrics]]): "mean star colour" is just another
  measured quantity. Manual Color Calibration in Siril does the same balance but is
  **GUI-only**.

### VeraLux Alchemy + DBXtract — the nebula/crosstalk path (CORRECTED: not star-neutral)
- **VeraLux Alchemy** (Riccardo Paterniti, **v1.0.3**, GPL-3.0, free) — *"Linear-Phase
  Narrowband Normalization & Mixing."* Source shows two mechanisms: (1) channel
  normalization by a robust median+MAD **linear fit that aligns weak OIII/SII to the
  Ha reference while deliberately EXCLUDING stars as outliers** (signal = 99.5th pct);
  (2) optional **"quantum unmixing"** = Ha/OIII duo-band crosstalk separation via a
  per-sensor matrix from DBXtract. **Anchor is the NEBULA (or sensor QE), not the
  stars — the opposite of star-neutral.** GUI-only PyQt6 (Class-1), CPU, Linux-via-Siril.
- **DBXtract** (Raúl Hussein / Astrocitas; PyQt6 port by Siril's A. Knagg-Baugh;
  **GPL-3.0**, v1.0.1) — the open reference Ha/OIII (and SII/OIII) **Bayer-crosstalk
  unmix**: a per-sensor **QE lookup table (12 IMX models, 9 coeffs each)** + a linear
  solve to isolate each NB line from the RGB triplet. GUI-only, CPU, Linux-via-Siril.
  Its published tables + documented solve are the mechanism to orchestrate if a
  headless OSC-dual-band unmix is wanted.

### The rest of the landscape (all GUI-bound for the colour step)
- **PixInsight** on Linux: build 1.9.4 "Lockhart" (May-2026), x86-64, but **X11/XCB
  mandatory (Wayland unsupported); true headless via Xvfb unverified**; €300 perpetual.
  Its NB tools — **NarrowbandNormalization** (Blanshan+Cranfield, ~Aug-2024, on
  *starless* data), **SHO-AIP**, **Foraxx/dynamic** (PixelMath, not a packaged tool) —
  are all GUI-bound and none does star-neutral balance.
- **SASpro** — has *"star-based white balance"* + NB→RGB normalization by name, but the
  mechanism is undocumented (unverified whether it neutralizes mean star colour), and
  it is **GUI-only** (Qt). Free GPL-3.0, very active (v1.19.6, 2026-07-13).
- **SyQon / Cosmic Clarity / GraXpert** — no narrowband-colour module.
- **APP** — commercial duo-band Bayer-leakage unmix; Linux build; not headless-CLI.

### Is star-neutral a named 2026 technique? No — mainstream decouples stars
Star-colour-neutral balance is a **valid, sound mechanism but NOT a branded, mainstream
technique**. The mainstream 2026 SHO/HOO flow instead **decouples stars**: remove stars
→ process the nebula *starless* (boost OIII freely) → re-add stars from separate
broadband RGB or synthetic sources → calibrate the nebula with SPCC-narrowband. Named
approaches: **JP Metsavainio "Tonemap"** (blend ~20% Ha into weak SII/OIII; mask-desaturate
magenta star cores), **Foraxx / dynamic** (Blanshan / "The Coldest Nights"), **Adam Block
"Narrowband Unlocked"** (paid). Star-neutral sits downstream of and less common than these.

## Sources
- Nightlight — https://github.com/mlnoga/nightlight · `OpRGBBalance` https://raw.githubusercontent.com/mlnoga/nightlight/master/internal/ops/rgb/rgb.go · CLI https://raw.githubusercontent.com/mlnoga/nightlight/master/cmd/nightlight/main.go · https://api.github.com/repos/mlnoga/nightlight
- Siril `ccm` / `pm` / SPCC narrowband — https://siril.readthedocs.io/en/latest/color-management/ccm.html · https://siril.readthedocs.io/en/stable/processing/color-calibration/spcc.html · https://siril.readthedocs.io/en/latest/processing/color-calibration/manual.html
- VeraLux Alchemy source — https://gitlab.com/free-astro/siril-scripts/-/raw/main/VeraLux/VeraLux_Alchemy.py · DBXtract source — https://gitlab.com/free-astro/siril-scripts/-/raw/main/processing/DBXtract.py
- PixInsight Linux/X11 + license — https://pixinsight.com/sysreq/ · https://pixinsight.com/licenses/ · NarrowbandNormalization https://cosmicphotons.com/scripts/ · Foraxx/dynamic https://thecoldestnights.com/2020/06/pixinsight-dynamic-narrowband-combinations-with-pixelmath/
- SASpro — https://github.com/setiastro/setiastrosuitepro/blob/main/README.md
- SHO best practice — https://buckeyestargazer.net/Pages/narrowbandstars2.php (Metsavainio) · https://adamblockstudios.com/learning-path/narrowband-unlocked/ · SPCC-in-the-wild https://forums.ruuth.xyz/t/spcc-narrowband/157
- OIII-shell objects / [OIII] traces the shell — https://en.wikipedia.org/wiki/NGC_2359 · https://arxiv.org/pdf/2403.12754

## Verdict / recommendation
- **The cleanest headless, doctrine-clean path we've identified for star-neutral
  balance** (a design to test, not yet run): measure the mean star colour in the
  **examine layer** (numpy over detected-star photometry) → apply a **diagonal `ccm`**
  natively in Siril (headless). This would close the gap without a GUI tool, without
  hand-rolling the pixel op, and folds "mean star colour" into the audit layer.
  **Recommended to adopt and test** on the x86 chain — a measured experiment against a
  controlled bracket.
- **Nightlight** is the ready-made reference (it does exactly this by name, headless,
  Linux, no-GPU) — but **dormant since 2024**; use it to validate the mechanism/coeffs
  and as a cross-check, not as a load-bearing go-forward dependency (Go-drift risk).
- **Alchemy/DBXtract** solve a *different* problem (OSC nebula normalization / Bayer
  crosstalk), are GUI-only Class-1, and are **not** the star-neutral answer — keep them
  for OSC-dual-band unmix only, as sanctioned escape-hatch mechanisms with a removal
  condition (DBXtract's GPL-3.0 tables are the reference to reimplement headless).
- **The native star-neutral gap is real but now has a clean fix** (ccm+measurement); no
  GUI-gated or dormant tool is required on the critical path.

## Status
**PROVISIONAL.** Nightlight's mechanism/dormancy, the `ccm`-diagonal arithmetic, the
"no native mean-star-colour command" gap, Alchemy's star-excluding anchor, and the
SPCC "use Manual for SHO" warning are all PRIMARY-VERIFIED from source/docs. The
recommended ccm+measurement path is a *design hypothesis* — the concrete x86 test:
measure mean star colour, feed a diagonal `ccm`, and confirm on a real OIII-shell stack
that the sphere lifts and stars go neutral, bracketed against SPCC and against Nightlight.

## Graduation
- **TOOLS.md Tier 10** — rewrite around the two-mechanism split: (1) the
  **ccm-diagonal-fed-by-measured-mean-star-colour** headless path (the recommended
  native fix; measurement in the examine layer); (2) **Nightlight** verified but
  dormant; (3) **Alchemy/DBXtract** = OSC nebula-normalization / Bayer-crosstalk unmix
  (GUI-only Class-1), NOT star-neutral. Note SPCC-is-the-cause + PixInsight X11-only.
- **The dead-end registry (`docs/dead-ends.md`)** — update: the star-neutral gap has a
  doctrine-clean headless resolution (measure mean star colour in examine layer → apply
  native `ccm` diagonal); Nightlight is the dormant reference; the *measurement* is an
  audit-layer item, linking to [[objective-qa-defect-metrics]].
- Applied in the graduation commit.
