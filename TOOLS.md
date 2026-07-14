# TOOLS.md — the astrophotography toolkit, by pipeline tier

A tool **audit**, not a prescribed chain. For each pipeline tier: what the
tier does, the options, when/why to pick each, and the alternatives —
filtered for what actually runs on **this rig** (x86-64 Kali, i7 14th-gen,
32 GB, 1 TB NVMe, **no GPU**, headless-preferred). The pipeline is a
TOOLKIT: pull the right tool per dataset + goal, each choice a measured
experiment ([[pipeline-as-toolkit]]). Current as of mid-2026.

## How to read this — the three tool CLASSES + the constraint columns

Every tool falls into one of three classes, which decides how cleanly it
fits our headless, orchestrate-not-hand-roll model:

1. **Native Siril command** — runs headless via `siril-cli -s` (or
   `pyscript`), free, deterministic, zero friction. The default substrate.
2. **Standalone CLI binary** — GraXpert, RC-Astro (BXT/NXT/SXT), StarNet2,
   ASTAP, Cosmic Clarity CLI. Headless-clean (own command line), some paid.
   Driven as a subprocess or a Siril script.
3. **Siril `pyscript` ecosystem** — splits by **where the pixel mechanism
   lives** (the resolved tool-vs-hand-roll test — see `docs/siril-pyscript-headless.md`):
   **Class-2 drivers** (`RC-Astro/*`, `CosmicClarity_*`, `GraXpert-AI`,
   `StarNet`) `subprocess` a real compiled binary → genuine tools, headless-clean,
   same category as our `solve_field.py`. **Class-1 numpy-inside** (VeraLux suite,
   SyQon Prism, SCUNet, DBXtract) do the pixel math in the script's own
   numpy/scipy/pywt/torch → the mechanism IS numpy; admissible only as a sanctioned
   alternative with a removal condition, never relabeled "a tool," and most are
   **GUI-mandatory PyQt6 with no headless path** (slider-only → not batch-drivable
   even under Xvfb). Only dual-mode Class-1 scripts (Statistical_Stretch, SyQon
   Prism `--no-gpu`) run headless.

Constraint shorthand used below — **Cost** (FREE / PAID / FREEMIUM) ·
**Runs** (siril-native / CLI / pyscript-GUI / GUI-app) · **Linux** (✅ /
⚠ workaround / ❌) · **CPU** (✅ CPU-fine / 🐢 CPU-slow / needs-AVX2) ·
**Headless** (✅ via -s or CLI / 🖥 needs Xvfb).

**Orthogonal to all tiers: our own measurement/QA harness** (`bg_qa` gate,
`object_integrity`, `star_shell_report`, `inspect_stage`, `judgment_package`)
wraps whichever tools are chosen — it MEASURES and JUDGES, it does not
process. That is the durable core the reset kept; the tiers below are the
processing it audits.

---

## Tier 0 — Acquisition

Not a software tier, but it outranks every tool: acquisition quality is the
real lever (REDESIGN "Acquisition checklist"). No processing tool recovers
photons you didn't collect or fixes a focal-length step mid-set.

## Tier 1 — Calibration & Integration (stacking)

Bias/dark/flat calibrate → register → integrate → one linear master.

| Tool | Cost | Runs | Linux/CPU/Headless | When & why |
|---|---|---|---|---|
| **Siril** (calibrate/register/stack, `seqextract_HaOIII`, drizzle) | FREE | siril-native | ✅ / ✅ / ✅ | **Default.** One integrated FOSS workflow, scriptable headless, 32-bit, drizzle + Bayer-drizzle, dual-band line extraction. What our `run_pipeline.sh` orchestrates. |
| **PixInsight WBPP** | PAID | GUI-app | ✅ / ✅ / ❌ | Most control + best-automated weighting/rejection; the reference. Use for a cross-check or if you live in PI. Not headless-friendly. |
| **Astro Pixel Processor (APP)** | PAID | GUI-app | ✅ / ✅ / ❌ | Excellent mosaic/normalization + light-pollution modeling; strong batch. A stacking alternative when Siril's normalization struggles on big mosaics. |
| **ASTAP** | FREE | CLI | ✅ / ✅ / ✅ | Fast astrometric stacker + solver; good for a quick headless stack or as the solver (Tier 2). |
| **DeepSkyStacker** | FREE | GUI-app | ❌ (Win) | Legacy/simple; no reason over Siril here. |

**Pick:** Siril for the headless pipeline. Keep our self-flat branch for
flatless sets (data-class, not a tool gap). PI/APP only as reference or for
a normalization edge case.

**Workflow specifics (headless, 1.4.4 — `docs/siril-stacking-workflow.md`):** masters
bias/dark `-nonorm`, flats `-norm=mul`; lights `-norm=addscale`. **Rejection by sub
count:** ≤6 percentile (`p`), ~7–50 winsorized (`rej w 3 3`), >50 GESD (`rej g 0.3 0.05`
— fraction+significance, NOT sigmas), large+gradients linear-fit (`rej l 3 3`).
Weighting `-weight={wfwhm|noise|nbstars|nbstack}` (unified — the old `-weight_from_*`
flags are REMOVED and will error migrated scripts). Registration: `-2pass`→`seqapplyreg`,
homography for wide fields, lanczos4+clamp. **Drizzle is a `register` option, not `stack`**
(CFA-drizzle 1×/pixfrac 1.0 for OSC; upscale only if sampling+dither justify —
[[plate-solving-and-drizzle]]). **Two real gaps vs PixInsight WBPP:** no Local
Normalization and no PSF-Signal-Weight equivalent (our audit layer can supply a PSFSW
proxy — [[objective-qa-defect-metrics]]).

## Tier 2 — Registration reference / plate solving / astrometry

Blind-solve → WCS for SPCC + annotation. Our dead-end: Siril's *internal*
star-match solver fails ultra-wide **trailed** fields.

| Tool | Cost | Runs | Linux/CPU/Headless | When & why |
|---|---|---|---|---|
| **Siril 1.4 native astrometry.net** (`platesolve -localasnet -blindpos -blindres`, SIP, auto-crop-wide) | FREE | siril-native | ✅ / ✅ / ✅ | **Now native in 1.4** (Dec 2025) — replaces our custom solve for ROUND-STAR (tracked) data. VERIFIED it does NOT drop-in replace `solve_field.py` for the TRAILED class: Siril feeds astrometry.net its own `findstar` (PSF-fit) star list, which is exactly the detection our dead-end says fails on trailed stars (ours feeds trail-robust PEAK centroids). Mitigation to TEST on x86: `setfindstar -relax=on` accepts non-star-shaped/trailed objects — may let native localasnet solve the trailed class too. See the verification note below. |
| **ASTAP** (`astap_cli -f file.fits`) | FREE | CLI | ✅ / ✅ / ✅ | **Fastest** local blind solve; **HFD flux-weighted-centroid detection with NO roundness gate → *predicted* to keep MILD/MODERATE trailing where Siril findstar rejects it** (mechanism inference — measure; severe/rotational still fails: "oval stars ignored"). **Wide-field DBs = W08 (80°>FOV>20°, 276 kB) + G05 (20°>3°)** — the D-series caps at 6°; **G17/H17/H18 are deprecated**. Key lever `-z` downsample. A strong complementary trailed-field solver — measure it vs `solve_field.py`. |
| **astrometry.net** (`solve-field`, our `solve_field.py`) | FREE | CLI | ✅ / ✅ / ✅ | Our current workaround — blind solve from PEAK centroids, which is what beat the trailed-star problem. Keep as the fallback until native/ASTAP are verified on trailed data. |

**Pick:** native localasnet for round-star data; **keep `solve_field.py` for
the trailed/ultra-wide class** (verified: native feeds Siril's PSF findstar on
the GREEN layer — the failing detection — and, when computed FOV > 5°, further
**crops detection to the central area** unless `-nocrop`, a second failure mode
for ultra-wide trailed fields). On x86, run the empirical test — `setfindstar
-relax=on -roundness=0.1 -maxR=<large>` + `platesolve -localasnet -blindpos
-blindres -nocrop` on a real trailed stack vs `solve_field.py` vs ASTAP; if
native/relaxed solves reliably, retire the custom script; else it stays the
trailed-field tool. (`-relax=on` only loosens quality checks — more
false-positives — it does NOT convert findstar's round-PSF model into a
peak-centroid detector.) **Trailed-class robustness ranking (mechanism —
`docs/plate-solving-and-drizzle.md`):** (1) astrometry.net fed our own
peak-centroid xylist — MOST robust, and confirmed the *intended* shape-blind
override (solve-field with an xylist runs no extraction; the matcher is
geometry-only), which VALIDATES `solve_field.py`; (2) ASTAP + W08/G05 (HFD, no
roundness gate) for mild trailing; (3) native `-localasnet` — least (findstar
PSF-fit + >5° crop). VERIFICATION detail below the table.

**Verification — does Siril 1.4 native solve replace `solve_field.py`?**
PARTIALLY. Both now use the astrometry.net ENGINE (Siril's *internal*
star-matcher was what failed on ultra-wide; localasnet bypasses it — that
half is native now). BUT the star DETECTION differs and that was the other
half of the failure: Siril localasnet "extracts the stars from your images
[with `findstar`] and submits this list to `solve-field`" (Siril docs) — i.e.
PSF-fit detection, which the `solve_field.py` docstring explicitly built
around ("Siril's PSF-fit detection ... fail to feed the matcher on this
[trailed] data"; ours uses trail-robust peak local-maxima). `solve_field.py`
also carries edges native lacks as first-class options: foreground-masked
detection (treeline/glow peaks poison the matcher), `--central` low-distortion
crop for warped wide lenses, and field-width-derived index-scale selection.
Net: native REPLACES for tracked/round-star data; for the trailed class it is
unverified and likely needs `-relax=on` tuning or the custom script. (This is
a MECHANISM verification from Siril docs + our source + the rig's command
help; no empirical solve was possible — the image data is deleted and this is
the arm rig. The x86 test above is definitive.)

## Tier 3 — Photometric colour calibration

| Tool | Cost | Runs | Linux/CPU/Headless | When & why |
|---|---|---|---|---|
| **Siril SPCC** (spectrophotometric, Gaia DR3 + QE/filter curves + atmosphere) | FREE | siril-native | ✅ / ✅ / ✅ | **Default; obsoletes PCC.** Broadband star-colour truth. Our `spcc_run.py`/`spcc_cone.py` orchestrate it + the local Gaia cone. |
| **PixInsight SPCC** | PAID | GUI-app | ✅ / ✅ / ❌ | The reference implementation; cross-check only. |

**Note:** SPCC is the WRONG step for the narrowband O3 sphere (it equalizes
O3=Ha — dead-end registry). Narrowband colour is Tier 10, not here.

## Tier 4 — Gradient / background extraction (LINEAR, star-ful, early)

| Tool | Cost | Runs | Linux/CPU/Headless | When & why |
|---|---|---|---|---|
| **GraXpert** (AI BGE, or RBF/spline) | FREE | CLI + siril-native | ✅ / ✅ (**BGE is CPU-fast, near-instant**) / ✅ | **Default AI gradient removal**, integrated in Siril 1.4 and standalone. BGE inference is lightweight (CPU near-instant, unlike GraXpert denoise/deconv). CLASS LIMIT (dead-end): the AI absorbs frame-filling FAINT nebulosity as gradient — use a plane/off for object-filling fields. |
| **Siril `subsky`** (`-rbf` or polynomial degree) | FREE | siril-native | ✅ / ✅ / ✅ | The retention mode — a first-degree plane removes the gradient class without absorbing localized nebulosity. Our `bgelin plane`. |
| **VeraLux Nox** (pyscript) | FREE | pyscript-GUI | ✅ / ✅ / ❌ | scipy sparse-Poisson gradient solve — a **Class-1 numpy-inside** script (mechanism = scipy, escape-hatch only) and **GUI-mandatory PyQt6** (not headless-drivable). (A prior "Seti AutoBGe" reference is unverified — no such script confirmed in the repo.) |
| **PixInsight DBE / GradientCorrection / MARS** | PAID | GUI-app | ✅ / ✅ / ❌ | DBE = manual sample gold standard; **MARS** (2026) = PI's new AI gradient model. Reference/cross-check. |

**Pick:** GraXpert AI for real gradients; Siril plane for object-filling
fields (the retention rule stands regardless of rig).

## Tier 5 — Deconvolution / sharpening (LINEAR, BEFORE denoise)

**2026 consensus: deconvolution goes early, in linear, BEFORE any noise
reduction** (NR destroys the fine low-contrast detail decon needs; BXT
explicitly dislikes denoised data). This tier was a **dead-end on the arm
rig** (no tool + unstable PSF on trailed data) — **it REOPENS on x86**, and
`BlurXTerminator` "correct only" can even fix the elongated/trailed stars
that were the base rig's core data problem.

| Tool | Cost | Runs | Linux/CPU/Headless | When & why |
|---|---|---|---|---|
| **BlurXTerminator** (RC-Astro, `--correct-only` + sharpen) | PAID $99.95 | CLI (`rc-astro bxt`) + siril-script | ✅ (Ubuntu 22.04+; **verify on Kali**) / **AVX2 (i7-14700 ok), CPU ~30–40 s** / ✅ | **Best-in-class**, now the standalone **`rc-astro` v0.9.9 CLI** (Win/Mac/Linux) + a Siril script — no longer PI-only. `--correct-only` fixes optical aberration + star elongation/trailing. **AI4.** Cross-platform perpetual license, **CLI free for holders**, **offline after one-time activation**. For headless: **call `rc-astro bxt` directly** (Class-2 binary), don't wrap the GUI-first pyscript. See `docs/rc-astro-cli-linux.md`. |
| **GraXpert deconvolution** (object + stellar AI) | FREE | CLI + siril-native | ✅ / ✅ 🐢 (minutes CPU) / ✅ | **PRE-RELEASE only — NOT a shipped stable feature.** Deconv lives in the 3.1.0-RC / **3.2.0-alpha** builds (GitHub tops out at 3.1.0rc2; PyPI carries **3.2.0a2**, Dec-2025 — install via `pip`/`pipx`); **stable is 3.0.2 (BGE+denoise only)** — no stable deconv in ~2 yr. Object-mode has an **open artifact bug (#243)**. Siril needs GraXpert ≥3.1.0-RC2 for deconv. Usable free deconv, but BXT is the mature path; the "artificial" knock is unsubstantiated — the real issues are the bug + weaker star-shape correction. |
| **AstroSharp** (DeepSkyDetail) | FREE | Win .exe / R-Shiny | ❌ **dead end for us** / — / ❌ | **NOT viable**: TIFF-only with a **<600 KB file cap** (unusable full-frame), **no native Linux**, **no CLI**, C++ (no Python), multi-platform issue open+unresolved since 2023. Drop from consideration. |
| **Cosmic Clarity — Sharpen** (Seti) | FREE (donation) | CLI (folder-batch) | ✅ native Linux (needs gnome-terminal) / 🐢 (**15–30 min CPU**) / ✅ | Free stellar/non-stellar sharpen, **v6.5 (AI3.5s-c)**; leading free BXT alternative, a notch below; CPU-brutal without a GPU. A Class-2 binary driver. |
| **Siril `makepsf` + RL deconvolution** | FREE | siril-native | ✅ / ✅ / ✅ | Classical RL; our dead-end (unstable symmetric PSF on ≈0 background with in-exposure trailing). Only viable with a good stable PSF. |

**Pick:** BXT (`rc-astro bxt`) if any budget — best quality + `--correct-only`
fixes trailing, CPU-fast (~30–40 s); else GraXpert deconv (free, headless, but
**RC-stage** — measure, watch bug #243) or Siril RL. **Order rule (refined): decon
early-linear, before HEAVY denoise — a strong DEFAULT, not absolute** (Siril itself
recommends a *little* VST NR before RL; and 2026 AI tools tolerate nonlinear-stage
decon — see the process-rule note at the end).

## Tier 6 — Noise reduction (linear on starless; and/or nonlinear)

**Siril has NO native chrominance-noise tool** (its docs punt to GIMP) — the
chroma-noise gap our removed corings covered is real, and this tier fills
it. Denoise the STARLESS layer (linear preferred), AFTER deconvolution.

| Tool | Cost | Runs | Linux/CPU/Headless | When & why |
|---|---|---|---|---|
| **NoiseXTerminator** (RC-Astro) | PAID $59.95 | CLI (`rc-astro nxt`) + siril-script | ✅ / AVX2, **CPU-light (lighter than BXT; indic.)** / ✅🖥 | **Best + fastest** AI denoise; `rc-astro` v0.9.9 CLI. AI3's new architecture advertises "noise COLOUR & frequency separation" → the **likely** fill for Siril's chroma-noise gap (dead-end), though a chroma-specific CLI control is **unverified** — test. Free CLI for holders, offline-after-activation. Call the binary directly for headless. |
| **Siril `denoise`** (NL-Bayes; `-da3d`/`-sos`/`-indep`/`-mod`/`-mask`) | FREE | siril-native | ✅ / ✅ / ✅ | **Free, headless, deterministic.** Plain NL-Bayes on stacks; `-da3d` refine, `-sos` background artefacts, `-indep` blocky colour, `-mod` blend, **`-mask` (1.5.0-dev) to confine to a region**. **No native chroma mode** (docs still punt to GIMP — gap confirmed in 1.5.0-dev). Clean default when free+headless matters. |
| **DeepSNR 1.2.1** (NAFNet AI; StarNet author) | FREE | **native Linux CLI** | ✅ / ✅ (self-contained ONNX, **CPU fallback**) / ✅ | **Cleanest free headless denoiser fit** — NAFNet trained on astro data, bundled ONNX Runtime (no CUDA/TF), built for automation/Siril. A Class-2 binary. A strong free NXT alternative (quality vs NXT/GraXpert unmeasured here). |
| **GraXpert denoise** (AI, one strength knob) | FREE | CLI + siril-native | ✅ / ✅ 🐢 (**>30 min large frames; regressed from ~5 min**) / ✅ | Free AI denoise, in Siril 1.4; `-batch_size 1–32` trades RAM for speed. Slight quality edge to NXT. CPU-slow is the real cost. |
| **SyQon Prism** (free "Siril Edition" / paid "Deep") | FREEMIUM | pyscript (**Class-1**) | ✅ via Siril / ✅ (Parallax **Nano** is CPU-only) / **🖥 GUI-in-Siril, not headless-confirmed** | 2026 neural (PyTorch NAFNet) denoise; numpy/torch-inside (escape-hatch). Free labels are Zenith/Prism-Siril-Edition/Parallax-**Nano** (not "Mini"). Competitive quality; but presents a GUI dialog in Siril → not confirmed headless. |
| **Cosmic Clarity Denoise** (Seti) | FREE (donation) | CLI (folder-batch) | ✅ native Linux / 🐢 (~7 min CPU) / ✅ | Free AI denoise, v6.5; CPU-slow; Class-2 binary driver. |
| **AstroDenoisePy 0.5.8** | FREE | CLI (`--device CPU`) | ✅ (py) / 🐢 / ✅ | CSBDeep/Noise2Noise; headless CLI; older, below NXT/DeepSNR. |
| **VeraLux Silentium** (SWT wavelet) | FREE | pyscript (**Class-1**) | ✅ via Siril / ✅ / **❌ GUI-mandatory** | `pywt` SWT denoise — **numpy-inside** (escape-hatch, not "a tool") and **GUI-mandatory PyQt6 with no arg vector → not headless-drivable** even under Xvfb. |

**Pick:** NXT (`rc-astro nxt`) if licensed — fastest, best, and AI3's "colour
separation" **likely** fills the chroma-noise gap (verify); else **DeepSNR** (free,
native Linux CLI, CPU) or Siril native `denoise` (headless, deterministic) or
GraXpert (CPU-slow). For chroma noise specifically, NXT-AI3 is the likely fill;
native Siril still has none. **Do it
after (heavy) denoise-destroying steps — i.e. after deconvolution, on the starless
layer** — as a strong default (see the process-rule note).

## Tier 7 — Star removal / separation (LINEAR, pre-stretch)

Split starless + stars so nebula and stars are processed independently.

| Tool | Cost | Runs | Linux/CPU/Headless | When & why |
|---|---|---|---|---|
| **StarXTerminator** (RC-Astro) | PAID $49.95 | CLI (`rc-astro sxt`) + siril-script | ✅ / AVX2, **CPU tens-of-sec** / ✅🖥 | **Best** separation, fewest artefacts on resolved objects; `rc-astro` v0.9.9 CLI. **AI11.** Free CLI for holders, offline-after-activation. Call the binary directly for headless. |
| **StarNet2 v2.5.3** (native x86 CLI) | FREE | CLI + siril-native | ✅ / ✅ (self-contained ONNX) / ✅ | **Free default on x86** — native binary, `--unscreen` + highlight protection. Keeps field-star flux; safe on resolved objects. Siril-integrated. A Class-2 binary. |
| **SyQon Zenith** (2026, AI) | FREE | pyscript (**Class-1**) | ✅ via Siril / ✅ / **🖥 GUI-in-Siril, not headless-confirmed** | Jan-2026 free high-fidelity AI star removal, in Siril via Get Scripts. Competitive; but presents a GUI dialog → not confirmed headless. |
| **Siril `starnet`/`seqstarnet`** integration | FREE | siril-native | ✅ / ✅ / ✅ | Drives StarNet under an invertible MTF pre-stretch (vendor-sanctioned). |

**Dead-end (portable):** never use mask+inpaint on a RESOLVED object — it
destroys HII knots. Use a learned separator (StarXT/StarNet/Zenith). On x86
the inpaint fallback is retired (a learned separator always runs).

## Tier 8 — Stretch (the LINEAR → NONLINEAR boundary)

Starless hard, stars gently. Broadband → one linked transfer; narrowband →
per-line (Tier 10 / Nightlight).

| Tool | Cost | Runs | Linux/CPU/Headless | When & why |
|---|---|---|---|---|
| **Siril `autostretch` / `autoghs` / `linstretch` / `curves`** | FREE | siril-native | ✅ / ✅ / ✅ | **Default.** Linked autostretch (broadband), GHS (generalized hyperbolic, deep-data control), linstretch (black-point + sat), curves. All headless. |
| **VeraLux HyperMetric Stretch** | FREE | pyscript-GUI | ✅ / ✅ / 🖥 | Well-regarded 2026 photometric hyperbolic stretch (Roger-Clark "true colour" lineage); numpy-inside, needs Xvfb. |
| **Cosmic Clarity / Seti Statistical Stretch** | FREE | CLI / pyscript | ✅ / ✅ / ✅🖥 | Statistical-median-target stretch; a good automated option. |
| **Arcsinh + Histogram (classic)** | FREE | siril-native / PI | ✅ / ✅ / ✅ | Arcsinh preserves star colour; the traditional broadband move. |

**Pick:** Siril autostretch/GHS for headless; the pyscript stretches only if
you accept Xvfb + the numpy-inside call.

## Tier 9 — Star reduction / recomposition (NONLINEAR)

Recombine stars over starless; optionally shrink stars.

| Tool | Cost | Runs | Linux/CPU/Headless | When & why |
|---|---|---|---|---|
| **Siril `synthstar` + `unclipstars` + Star Re-composition** | FREE | siril-native | ✅ / ✅ / ✅ | **Native + headless.** `synthstar` rebuilds perfect PSF stars (fixes coma/trailing), `unclipstars` desaturates blown cores, Star Re-composition blends starmask ↔ starless. Replaces our numpy star-render hand-roll. |
| **VeraLux Star Recomposer** | FREE | pyscript-GUI | ✅ / ✅ / 🖥 | Sensor-profile star recomposition (core removal, reduction, optical healing); numpy-inside. |
| **Bill Blanshan star reduction** (PixelMath) | FREE | siril-native (`pm`) | ✅ / ✅ / ✅ | Classic star-shrink expressions runnable via `pm` — fully headless. |
| **StarXTerminator** (reduce mode) | PAID | CLI | ✅ / CPU-ok / ✅ | Star reduction as part of SXT if licensed. |

## Tier 10 — Colour & palette work (esp. narrowband SHO/HOO)

| Tool | Cost | Runs | Linux/CPU/Headless | When & why |
|---|---|---|---|---|
| **Siril `ccm` (diagonal) + our examine layer** ← the recommended star-neutral *approach* (untested) | FREE | siril-native + numpy | ✅ / ✅ / ✅ | **The doctrine-clean, headless star-neutral approach (a design to test, not yet run):** a **diagonal `ccm` IS a per-channel star-neutral balance** (arithmetic); MEASURE the field's mean star colour in our EXAMINE layer (numpy over detected stars — no native command outputs it), then APPLY via native `ccm`. Pixel op = a tool; measurement = ours. Recommended to adopt+test on the x86 chain. |
| **Nightlight** (mlnoga; star-neutral SHO) | FREE (GPL-3) | **headless Go CLI** | ✅ x86/ARM / ✅ (no-GPU, AVX2) / ✅ | The ready reference for star-neutral: `OpRGBBalance` balances the mid-population stars to neutral RGB{1,1,1} → lifts OIII vs Ha. **But DORMANT** (v0.2.6 2023, last commit 2024-01; Go-drift risk) — use to validate the mechanism, not as a load-bearing dependency. |
| **VeraLux Alchemy / DBXtract** (NOT star-neutral) | FREE (GPL-3) | pyscript (**Class-1**) | ✅ via Siril / ✅ / **🖥 GUI-only** | Alchemy = nebula-anchored NB normalization + Ha/OIII crosstalk-unmix (**excludes stars** — opposite anchor from star-neutral); DBXtract = the GPL-3 Bayer-crosstalk-unmix reference (12-sensor QE tables + linear solve). For OSC dual-band unmix only; numpy-inside escape-hatch, GUI-gated. |
| **Siril `pm` / `rmgreen` / `satu` / `rgbcomp`** | FREE | siril-native | ✅ / ✅ / ✅ | `pm` NBRGB/palette mixing (per-channel via separate mono images), `rmgreen` SCNR (kill SPCC's warned green cast), `satu` hue-targeted saturation, `rgbcomp` SHO/HOO assembly. Headless toolbox. |
| **PixInsight (NarrowbandNormalization, SHO-AIP, Foraxx)** | PAID €300 | GUI-app | ✅ (**X11 mandatory, Wayland unsupported**; Xvfb unverified) / ✅ / ❌ | The reference for palette work; none does star-neutral balance. GUI-bound. |

**Note:** SPCC-narrowband is verified as the *cause* of the OIII flattening —
Siril's own docs say it gives "real intensities"/"a huge green cast" and
**recommend Manual Color Calibration for SHO**. The star-neutral balance that
recovers the sphere has a **clean headless resolution now**: measure the mean
star colour in the examine layer, apply a diagonal `ccm` (the *measurement* is
the only missing native piece, and it belongs in our audit layer anyway —
[[objective-qa-defect-metrics]]). Nightlight is the dormant by-name reference.
Two mechanisms, don't conflate: **star-anchored** neutral balance (ccm+measure /
Nightlight) vs **nebula/QE-anchored** unmix (Alchemy/DBXtract, OSC dual-band).
Star-neutral is a valid mechanism but NOT a mainstream-named technique — the
mainstream decouples stars (remove → boost OIII starless → re-add stars). See
`docs/narrowband-star-neutral-options.md`.

## Tier 11 — Detail / local contrast (NONLINEAR)

| Tool | Cost | Runs | Linux/CPU/Headless | When & why |
|---|---|---|---|---|
| **Siril `wavelet`, `pm`, HDR compression** | FREE | siril-native | ✅ / ✅ / ✅ | À-trous wavelets for multiscale detail; headless. |
| **VeraLux Revela / HDR Multiscale** | FREE | pyscript-GUI | ✅ / ✅ / 🖥 | ATWT local contrast, HDR multiscale; numpy-inside. |
| **CLAHE / local contrast** (various) | FREE | pyscript / PI | ✅ / ✅ / varies | Contrast-limited adaptive histogram equalization for structure. |
| **BlurXTerminator** (as sharpen) | PAID | CLI | ✅ / CPU-ok / ✅ | Also a nonlinear detail enhancer if licensed. |

## Tier 12 — Final touches / export

- **SCNR / green removal** — Siril `rmgreen` (headless). Broadband strong,
  narrowband mild (protect OIII green).
- **Export** — Siril writes TIFF16 / PNG16 / PNG8 / q100 JPEG headless. Our
  `--lossless` PNG8+PNG16 remains the judgment surface; JPEG q100/4:4:4 the
  display final.
- **Colorimetry** — sRGB-tag finals (our `srgb.icc`).

---

## Cross-cutting: what's FREE-and-headless vs PAID vs GUI-gated

**The fully FREE + headless x86 stack** (no license, no display, runs under
`siril-cli` or a Class-2 binary): Siril 1.4 natives (solve / SPCC / drizzle /
ccm / curves / autostretch / GHS / denoise / synthstar / rgbcomp / wavelet /
pm / rmgreen / satu) + **GraXpert** (BGE **CPU-fast**, denoise **CPU-slow**,
deconv **RC-stage only**) + **StarNet2 v2.5.3** (star removal) + **DeepSNR**
(NAFNet denoise, native Linux CLI) + **AstroDenoisePy** + **Cosmic Clarity**
(sharpen/denoise/dark-star, native Linux, CPU-slow) + **ASTAP** (fast solve).
A complete, competitive pipeline. (`AstroSharp` is OUT — no Linux/CLI,
600 KB TIFF cap.)

**PAID, now a real Linux CLI** (worth it if budget allows): **RC-Astro
BXT $99.95 / NXT $59.95 / SXT $49.95** via the standalone **`rc-astro` v0.9.9**
binary (Ubuntu 22.04+, **verify on Kali**) — best-in-class deconv (incl.
`--correct-only` trailing fix) / denoise (AI3 "colour separation" **likely** fills the chroma-noise gap — verify) /
star removal. One cross-platform perpetual license, **CLI free for holders**,
AVX2 CPU (i7-14700 ok, ~20–40 s), no GPU, **offline after one-time activation**.
For headless, **call the binary directly** (Class-2), not the GUI pyscript.
**PixInsight** €300 — the reference (WBPP, DBE/MARS), **X11-only, not headless**.

**FREE but GUI-gated / numpy-inside** (escape-hatch, per the resolved
philosophy question — `docs/siril-pyscript-headless.md`): the **VeraLux** suite
(Silentium / HyperMetric / Nox / Vectra / Alchemy / …), **SyQon** free tiers
(Zenith / Prism / Parallax-Nano), **SCUNet**, **DBXtract** — these do the pixel
math in their own numpy/scipy/pywt/torch (mechanism = numpy → sanctioned
*alternative with a removal condition*, never "a tool"). Most are **GUI-mandatory
PyQt6 with no arg vector → NOT headless-drivable even under Xvfb**; only
dual-mode ones (Statistical_Stretch, SyQon Prism `--no-gpu`) run headless. Prefer
a compiled tool (Siril-native / RC-Astro / GraXpert / StarNet / DeepSNR / Cosmic
Clarity — all Class-2 binaries) whenever one provides the mechanism.

## The no-GPU reality

Every AI tool here runs CPU-only on the i7-14700 (AVX2), but slower — and the
spread is large. **Indicative CPU figures (from mixed / comparable hardware, NOT
measured on our rig — re-measure):** RC-Astro is reasonable on CPU (BXT ~30–40 s
from an i5-14600K; NXT/SXT lighter/faster — the NXT ~20–30 s figure is a
5-yr-old Mac, not 14th-gen); **GraXpert denoise (>30 min on large frames) and
Cosmic Clarity sharpen (15–30 min) are the slow ones** (also other CPUs);
GraXpert BGE is near-instant. Measure wall-clock and budget it — nothing here REQUIRES a GPU.
(An NVIDIA GPU accelerates all of them via CUDA/cuDNN on Linux — including
RC-Astro, whose Linux GPU path is NVIDIA-only — but every tool has a supported
CPU fallback; use `rc-astro <tool> --benchmark-all` to pin the fastest device.)

## The one process rule that changed everything

The 2026 consensus order, as a **strong DEFAULT (not an absolute rule)**:
**gradient removal → colour calibration (SPCC, on linear) → DECONVOLUTION
(linear, stars usually still present) → noise reduction (linear, on starless)
→ star removal → STRETCH → detail / colour / recomposition (nonlinear)**. The
two the old arm pipeline got wrong or couldn't do: **deconvolution comes early
and BEFORE (heavy) denoise** (now possible + can fix trailed stars), and
**noise reduction is a real tool step, not a hand-rolled coring**. Three
refinements from the multi-source validation (`docs/graxpert-3x-and-workflow-order.md`):
(1) *light* NR before deconvolution is fine — Siril itself recommends a ~50–60%
VST to steady the RL — the rule is "no HEAVY NR first"; (2) **star-removal
placement is genuinely variable** (RC-Astro: linear/early; AstroBackyard:
post-first-stretch) — a per-dataset choice; (3) **2026 AI tools loosen the
linear-only rule** — because BXT/SXT/NXT/DeepSNR self-normalize, respected
practitioners (ben.land, Cuiv) run NR and even deconv in the *nonlinear* stage;
treat that as a measurable alternative, not a violation. What everyone still
agrees on: **colour-calibrate on linear, minimally-processed data**, and **no
heavy NR before deconvolution**.

Sources: the per-topic primary citations live in **`docs/`** (one cited `.md`
per deep-dive — see `docs/README.md`). In brief: siril.org (1.4.0–1.4.4
releases; RC-Astro-in-Siril 2026-06; Zenith 2026-01; Parallax 2026-06),
siril.readthedocs `/latest` (1.5.0-dev commands / denoising / SPCC / platesolving /
Python-API / scripts), rc-astro.com (`rc-astro` v0.9.9 standalone CLI, FAQ,
product pages) + the GitLab RC-Astro script source, GraXpert GitHub **API**
(stable 3.0.2, deconv RC-only in 3.1.0rc2, bug #243), gitlab free-astro/siril-scripts
(VeraLux/SyQon/DBXtract source), starnetastro.com (StarNet2.5.3 / DeepSNR),
setiastro.com (Cosmic Clarity v6.5 / SASpro), mlnoga/nightlight (star-neutral),
hnsky.org (ASTAP), pixinsight.com ImageWeighting (QA metrics), ben.land 2025-12 +
AstroBackyard + PixInsight/Conejero (workflow-order).
