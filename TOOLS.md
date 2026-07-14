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
3. **Siril `pyscript` ecosystem** — VeraLux, SyQon, Seti. Mostly **PyQt6
   GUIs** that connect to a running Siril over IPC → they need a **display
   (Xvfb)** to run headless, and many do the processing in numpy inside the
   script. Powerful, but the messiest fit; see [[siril-tool-ecosystem]] and
   the "tool vs hand-rolled numpy" question in REDESIGN.

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

## Tier 2 — Registration reference / plate solving / astrometry

Blind-solve → WCS for SPCC + annotation. Our dead-end: Siril's *internal*
star-match solver fails ultra-wide **trailed** fields.

| Tool | Cost | Runs | Linux/CPU/Headless | When & why |
|---|---|---|---|---|
| **Siril 1.4 native astrometry.net** (`platesolve -localasnet -blindpos -blindres`, SIP, auto-crop-wide) | FREE | siril-native | ✅ / ✅ / ✅ | **Now native in 1.4** (Dec 2025) — replaces our custom solve for ROUND-STAR (tracked) data. VERIFIED it does NOT drop-in replace `solve_field.py` for the TRAILED class: Siril feeds astrometry.net its own `findstar` (PSF-fit) star list, which is exactly the detection our dead-end says fails on trailed stars (ours feeds trail-robust PEAK centroids). Mitigation to TEST on x86: `setfindstar -relax=on` accepts non-star-shaped/trailed objects — may let native localasnet solve the trailed class too. See the verification note below. |
| **ASTAP** (`astap -f file.fits`) | FREE | CLI | ✅ / ✅ / ✅ | **Fastest** (~2 s local blind solve vs astrometry.net's 5–30 s); its own star-pattern solver + local star DB. Best when a rough center is known; excellent headless. A third solver option distinct from astrometry.net. |
| **astrometry.net** (`solve-field`, our `solve_field.py`) | FREE | CLI | ✅ / ✅ / ✅ | Our current workaround — blind solve from PEAK centroids, which is what beat the trailed-star problem. Keep as the fallback until native/ASTAP are verified on trailed data. |

**Pick:** native localasnet for round-star data; **keep `solve_field.py` for
the trailed/ultra-wide class** (verified: native feeds Siril's PSF findstar,
the failing detection). On x86, run the empirical test — `setfindstar
-relax=on` + `platesolve -localasnet -blindpos -blindres` on a real trailed
stack vs `solve_field.py` vs ASTAP; if native/relaxed solves reliably, retire
the custom script; else it stays the trailed-field tool. VERIFICATION detail
below the table.

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
| **GraXpert** (AI BGE, or RBF/spline) | FREE | CLI + siril-native | ✅ / ✅ (GPU optional via CUDA) / ✅ | **Default AI gradient removal**, integrated in Siril 1.4 and standalone. CLASS LIMIT (dead-end): the AI absorbs frame-filling FAINT nebulosity as gradient — use a plane/off for object-filling fields. |
| **Siril `subsky`** (`-rbf` or polynomial degree) | FREE | siril-native | ✅ / ✅ / ✅ | The retention mode — a first-degree plane removes the gradient class without absorbing localized nebulosity. Our `bgelin plane`. |
| **Seti AutoBGe** (pyscript) | FREE | pyscript-GUI | ✅ / ✅ / 🖥 | Sample-point RBF background; a scripted middle ground. Needs Xvfb headless. |
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
| **BlurXTerminator** (RC-Astro, "correct only" + sharpen) | PAID | CLI + siril-script | ✅ / needs-AVX2, CPU-ok 🐢 / ✅ (CLI) 🖥 (script) | **Best-in-class**, now a standalone Linux CLI (2026) + a Siril script — no longer PI-only. Corrects optical aberration + star elongation/trailing. Cross-platform license; free CLI for holders. The single strongest reason to spend money. |
| **GraXpert deconvolution** (object + stellar AI, 2026) | FREE | CLI + siril-native | ✅ / ✅ 🐢 / ✅ | **Free deconv**, now in GraXpert 3.x + Siril 1.4. The FOSS answer to the deconv gap; can look "artificial" — measure. |
| **AstroSharp** (DeepSkyDetail) | FREE | CLI (C++) | ⚠ workaround / ✅ / ⚠ | Free BXT alternative; BXT is better but this is a real FOSS option. Linux is a workaround (Windows-first). |
| **Cosmic Clarity — Sharpen** (Seti) | FREE | CLI | ✅ / 🐢 (15–30 min CPU) / ✅ | Free stellar/non-stellar sharpen; CPU-slow without a GPU. |
| **Siril `makepsf` + RL deconvolution** | FREE | siril-native | ✅ / ✅ / ✅ | Classical RL; our dead-end (unstable symmetric PSF on ≈0 background with in-exposure trailing). Only viable with a good stable PSF. |

**Pick:** BXT if licensed (also fixes trailing); else GraXpert deconv (free,
headless). **Order rule is the real lesson: decon FIRST-linear, before denoise.**

## Tier 6 — Noise reduction (linear on starless; and/or nonlinear)

**Siril has NO native chrominance-noise tool** (its docs punt to GIMP) — the
chroma-noise gap our removed corings covered is real, and this tier fills
it. Denoise the STARLESS layer (linear preferred), AFTER deconvolution.

| Tool | Cost | Runs | Linux/CPU/Headless | When & why |
|---|---|---|---|---|
| **NoiseXTerminator** (RC-Astro) | PAID | CLI + siril-script | ✅ / needs-AVX2, CPU-ok / ✅🖥 | **Best + fastest** AI denoise; standalone Linux CLI (2026) + Siril script. The premium default if licensed. |
| **Siril `denoise`** (NL-Bayes; `-da3d`/`-sos`/`-indep`/`-mod`) | FREE | siril-native | ✅ / ✅ / ✅ | **Free, headless, deterministic.** Plain NL-Bayes on stacks; `-da3d` refine, `-sos` for background artefacts, `-indep` for blocky colour, `-mod` to blend. No chroma-specific mode. The clean default when free+headless matters. |
| **GraXpert denoise** (AI, one strength knob) | FREE | CLI + siril-native | ✅ / ✅ 🐢 / ✅ | Free AI denoise, in Siril 1.4; slower than NXT. Solid FOSS option. |
| **SyQon Prism** (Mini FREE / Deep PAID) / **Parallax Nano** (FREE) | FREEMIUM | pyscript | ✅ / ✅ / 🖥 | 2026 neural denoise, free tiers for Siril. Prism = denoise; Parallax = broader. Via Siril scripts. |
| **Cosmic Clarity Denoise** (Seti) | FREE | CLI | ✅ / 🐢 / ✅ | Free AI denoise; CPU-slow. |
| **DeepSNR**, **AstroDenoisePy** | FREE | CLI / pyscript | ✅ / ✅ / varies | Free open-source AI denoisers worth a measured look. |
| **VeraLux Silentium** (SWT wavelet, non-AI) | FREE | pyscript-GUI | ✅ / ✅ / 🖥 | Well-reviewed non-AI linear-stage denoise; numpy-inside, needs Xvfb headless (the "tool vs hand-roll" call). |

**Pick:** NXT if licensed; else Siril native `denoise` (headless, free,
deterministic) or GraXpert. **Do it AFTER deconvolution, not before.**

## Tier 7 — Star removal / separation (LINEAR, pre-stretch)

Split starless + stars so nebula and stars are processed independently.

| Tool | Cost | Runs | Linux/CPU/Headless | When & why |
|---|---|---|---|---|
| **StarXTerminator** (RC-Astro) | PAID | CLI + siril-script | ✅ / needs-AVX2, CPU-ok / ✅🖥 | **Best** separation, fewest artefacts on resolved objects; standalone Linux CLI (2026). Premium default. |
| **StarNet2** (native x86 CLI) | FREE | CLI + siril-native | ✅ / ✅ / ✅ | **Free default on x86** — the native binary runs now (no more ONNX-under-onnxruntime arm workaround). Keeps field-star flux; safe on resolved objects. Siril-integrated. |
| **SyQon Zenith** (2026, AI) | FREE | pyscript | ✅ / ✅ / 🖥 | Brand-new (Jan 2026) free high-fidelity AI star removal, in Siril via Get Scripts. A StarNet alternative worth measuring. |
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
| **Nightlight** (reference author's tool — star-neutral SHO) | FREE | CLI | ⚠ (arm-staged; x86 rebuild) / ✅ / ✅ | The one mechanism Siril lacks: **star-colour-neutral balance** that recovers the O3 sphere SPCC erases (dead-end registry). Our sanctioned narrowband precedent; re-stage on x86. |
| **Siril `ccm` / `pm` / `rmgreen` / `satu`** | FREE | siril-native | ✅ / ✅ / ✅ | `ccm` = 3×3 colour matrix (channel scales / a diagonal ≈ star-neutral balance); `pm` = NBRGB palette mixing; `rmgreen` = SCNR; `satu` = saturation. The headless narrowband toolbox. |
| **VeraLux Alchemy / Vectra** | FREE | pyscript-GUI | ✅ / ✅ / 🖥 | Alchemy = narrowband normalization + Ha/OIII crosstalk unmix; Vectra = LCH colour grading with star protection. numpy-inside. |
| **PixInsight (SHO scripts, PixelMath)** | PAID | GUI-app | ✅ / ✅ / ❌ | The reference for narrowband palette work. |

**Note:** the star-neutral O3-sphere balance is a genuine gap in native Siril
(`ccm` can do a diagonal scale, but not the star-population-measured
balance). Nightlight or a `ccm`-driven star-neutral computation fills it —
a real design question for the x86 chain.

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
`siril-cli`): Siril 1.4 natives (solve / SPCC / drizzle / ccm / curves /
autostretch / GHS / denoise / synthstar / rgbcomp / wavelet / pm / rmgreen /
satu) + **GraXpert** (BGE / denoise / deconv) + **StarNet2** (star removal) +
**ASTAP** (fast solve) + **AstroSharp / DeepSNR / AstroDenoisePy** (extra
free AI). This alone is a complete, competitive pipeline.

**PAID, but now Linux-CLI + headless-capable** (worth it if budget allows):
**RC-Astro BXT / NXT / SXT** — best-in-class deconv (incl. trailing
correction) / denoise / star removal, one cross-platform license, AVX2 CPU
(the i7-14700 qualifies), no GPU required (slower). **PixInsight** — the
reference environment (WBPP, DBE/MARS), not headless.

**FREE but DISPLAY-gated** (need Xvfb, and are numpy-inside — the "tool vs
hand-rolled" judgment call): the **VeraLux** suite (Silentium / HyperMetric /
Revela / Vectra / Alchemy / Star Recomposer) and much of **SyQon** (Zenith /
Prism / Parallax) and **Seti** pyscripts. Reachable headless only via an
Xvfb virtual display; decide the philosophy question (REDESIGN) before
leaning on them.

## The no-GPU reality

Every AI tool here runs CPU-only on the i7-14700 (AVX2), but slower: RC-Astro
tools are reasonable on CPU; GraXpert/Cosmic Clarity denoise are notably
slow; a full run is minutes per image, not seconds. Measure wall-clock and
budget it — but nothing here REQUIRES a GPU. (If throughput ever bites, an
NVIDIA GPU accelerates GraXpert/Cosmic Clarity/SyQon via CUDA; RC-Astro tools
are CPU-only anyway.)

## The one process rule that changed everything

The 2026 consensus order is worth stating once, because it differs from the
old chain: **gradient removal → colour calibration → DECONVOLUTION (linear)
→ noise reduction (linear, on starless) → star removal (linear) → STRETCH →
detail / colour / recomposition (nonlinear)**. The two that the old arm
pipeline got wrong or couldn't do: **deconvolution comes early and BEFORE
denoise** (and is now possible + can fix trailed stars), and **noise
reduction is a real tool step, not a hand-rolled coring**.

Sources: siril.org (Siril 1.4.0 release; RC-Astro-in-Siril 2026-06; SyQon
Zenith 2026-01; Parallax 2026-06), siril.readthedocs (platesolving /
denoising / SPCC / Python), rc-astro.com (standalone tools), GraXpert GitHub
(3.x deconv+denoise), setiastro.com (Cosmic Clarity / SASpro),
deepskydetail/AstroSharp, hnsky.org (ASTAP), Cloudy Nights / AstroBin
(AstroDenoisePy, VeraLux, workflow-order threads), undersouthwestskies (2025
Siril-1.4 workflow), ben.land 2025-12 (refined technique).
