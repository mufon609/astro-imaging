# The free / freemium AI astro-tool wave (mid-2026) — deep dive

- **Question / scope** — Survey the current FREE / freemium AI processing tools
  (star removal, denoise, deconvolution, sharpening) and filter them hard for what
  actually runs **headless-CLI on Linux, CPU-only, no GPU** — the rig's real
  constraint. Extends TOOLS.md Tiers 5–7 and the free-stack cross-cutting section.
  Corrects several existing entries.
- **Context** — 2026-07-14. Target rig: x86-64 Kali, i7-14gen (AVX2), 32 GB, **no
  GPU**, headless. The paid quality bar is RC-Astro ([[rc-astro-cli-linux]]); these
  free tools matter precisely where budget = 0. Architecture (numpy-inside vs
  binary-driver) per [[siril-pyscript-headless]].

## Findings

### Fitness table (headless-Linux-CPU is the filter)
| Tool | Capability | Linux | Headless-CLI | Free? | CPU viable |
|---|---|---|---|---|---|
| **StarNet v2.5.3** (CLI) | Star removal | native x64 | **yes** | free | yes (minutes) |
| **DeepSNR 1.2.1** (CLI) | Denoise (NAFNet) | native x64 | **yes** | free | yes (ONNX CPU) |
| **GraXpert** | BGE + denoise (+ deconv RC) | native | **yes** | free/OSS | yes (denoise slow) |
| **AstroDenoisePy 0.5.8** | Denoise (CSBDeep/N2N) | likely (py, not documented) | **yes** (`--device CPU`) | free | yes (slow) |
| **Cosmic Clarity v6.5** | sharpen/denoise/star/upscale/sat/aberration | native x64 | partial (arg-drivable, under-doc) | free (donation) | yes but SLOW (sharpen 15–30 min) |
| **SyQon** Zenith/Prism/Parallax-Nano | star / denoise / deconv | via Siril | **no** (GUI dialog in Siril) | free tiers | yes (Nano CPU-only) |
| **SCUNet** Siril script | denoise (stretched) | via Siril | unclear | free/OSS | likely |
| **SASpro** | GUI suite (aggregator) | workaround (venv) | **no** (Qt GUI) | free (donation) | yes |
| **AstroSharp** | deconv/sharpen | **no** | **no** | free | n/a |

### The genuinely free + headless + Linux + CPU set (the free stack's AI layer)
- **StarNet v2.5.3 (CLI)** — Nikita Misiura. Native Linux x64, self-contained
  ONNX/ORT, CPU-capable, `--unscreen` + highlight protection. The **de-facto free
  headless SXT alternative on Linux.** A Class-2 binary (in-bounds).
- **DeepSNR 1.2.1 (Linux CLI, May 2026)** — same author; **NAFNet** denoiser trained
  on astro data. **Self-contained (ONNX Runtime bundled, no CUDA/TF), CPU fallback on
  all platforms, explicitly built for automation/scripts/Siril**, TIFF/PNG 8/16-bit.
  On the headless-CPU criteria this is the **cleanest free denoiser fit** (self-contained,
  CPU, automation-built) — a real NXT alternative from a trusted author, and a Class-2
  binary. **Upgrade its standing** (TOOLS Tier 6 had it as a footnote). (Quality vs
  NXT/GraXpert not measured here — a comparison to run on x86.)
- **GraXpert** — BGE (CPU-fast) + denoise (CPU-slow) + deconv (RC-only); full CLI,
  CPU fallback. Details in [[graxpert-3x-and-workflow-order]].
- **AstroDenoisePy 0.5.8** (BSD-3, Sep-2024) — CSBDeep / Noise2Noise (TF/Keras),
  headless `python -m astrodenoise.main img.tif --device CPU`. Pure-Python →
  Linux-likely; older, below NXT/DeepSNR. A Class-1 (its own TF model) but shipped as
  a standalone CLI package, so it's a driver-usable tool, not an in-repo hand-roll.

### Cosmic Clarity (Seti Astro) — capable, native-Linux, but CPU-brutal
- Modules: Sharpen (Stellar/Non-Stellar/Both), Denoise (Full/Luminance), **Dark
  Star** (star removal), **Super Resolution** (upscale), **Satellite Trail Removal**,
  AI Aberration Correction. Sharpen/Denoise **v6.5 (AI3.5s-c, Dec 2025)**.
- **Native Linux 64-bit build** (needs `gnome-terminal`); free donationware.
- **CPU is dramatically slower:** measured (via the Siril venv path) **sharpen
  ≈15–30 min CPU vs ≤10 s GPU; denoise ≈7 min CPU vs ~10 s GPU** (image size
  unstated — re-measure on the i7). Arg-drivable (the Siril wrapper invokes it
  non-interactively) but the exact flag list isn't in primary docs.
- Reputation: the **leading free BXT/NXT alternative**, a notch below RC-Astro. A
  Class-2 binary driver.

### SyQon — competitive quality, but the free tiers are GUI-in-Siril (naming corrected)
- Naming split: standalone products **Parallax** (deconv), **DeepPrism** (denoise),
  **Starless** (star removal), **Continuum** (app, Win/Mac only, paid). The **free
  Siril editions** are **Zenith** (star removal, Jan-2026), **Prism** (denoise, a
  free "Siril Edition"; a paid "Prism Deep" exists), **Parallax Nano** (deconv,
  **CPU-only, free with account**). → **Correct TOOLS.md's "Prism Mini"** — the
  confirmed free labels are Zenith / Prism-Siril-Edition / Parallax-**Nano**.
- **Headless: NOT confirmed.** They run inside Siril (itself Linux/headless-capable),
  but present a **parameter GUI dialog**, and Siril's API raises `SirilError` if a
  dialog is opened headless → in practice **GUI-driven within the Siril desktop.**
  SyQon Prism is a Class-1 numpy/PyTorch-inside script (NAFNet). Paid pricing is
  account-gated (undisclosed). Quality rated competitive with SXT/NXT/BXT.

### Downgrades / dead ends / watch-list
- **AstroSharp (DeepSkyDetail) — DEAD END for us.** Windows `.exe` + R/Shiny, C++
  (no Python), **TIFF-only and files must be < 600 KB** (unusable full-frame), **no
  native Linux**, no CLI, multi-platform issue open+unresolved since May-2023.
  **Correct TOOLS.md Tier 5** (currently "a real FOSS option ⚠ workaround").
- **SASpro (Seti Astro Suite Pro)** — GUI aggregator (bundles CosmicClarity + SyQon
  models + MFDeconv + aberration + morphological star reduction). **Linux = venv
  workaround; GUI-only, no headless.** Useful as a reference desktop, not a headless
  driver.
- **SCUNet Siril script** — SCUNet denoiser for *stretched* colour + "uberSmooth"
  astro variants; runs via Siril on Linux; headless unclear; below NXT/DeepSNR. A
  Class-1 numpy/ONNX-inside script.
- **AstroNoiseNet** (Steffenhir) — PRIDNet **research** repo, no releases; not a product.
- **Watch (unconfirmed Linux/headless):** **AIDT / AIST** (mdci.ro, freeware
  May-2026, AI mono NR, "AIST Siril Plugin v4.0" Jun-2026, ONNX-Runtime) and
  **AstroForge** (astroforge.de, "20 algorithms + 18 ML models," RL deconv/CLAHE).
  Both need platform/free/headless verification before adoption.

## Sources
- SyQon — https://syqon.eu/ (/parallax, /prism, /continuum, /free-parallax-nano) ·
  Zenith https://siril.org/2026/01/a-brand-new-star-removal-script-comes-to-siril-zenith/ ·
  Parallax https://siril.org/2026/06/parallax/
- Cosmic Clarity — https://www.setiastro.com/cosmic-clarity ·
  SASpro https://github.com/setiastro/setiastrosuitepro · https://pypi.org/project/setiastrosuitepro/ ·
  CPU-timing thread https://discuss.pixls.us/t/workaround-for-problem-with-no-gpu-support-on-setiastro-cosmic-clarity-scripts/52539
- AstroSharp — https://github.com/deepskydetail/AstroSharp · issue #1 (Linux) https://github.com/deepskydetail/AstroSharp/issues/1
- AstroDenoisePy — https://github.com/p7ayfu77/astro-csbdeep
- StarNet / DeepSNR — https://starnetastro.com/cli-tools/ · https://starnetastro.com/cli-tools/deepsnr/
- SCUNet Siril script — https://gitlab.com/free-astro/siril-scripts/-/merge_requests/29 · AstroNoiseNet https://github.com/Steffenhir/AstroNoiseNet
- GraXpert — https://github.com/Steffenhir/GraXpert · https://pypi.org/project/graxpert/
- Watch — https://mdci.ro/aipt.php · https://astroforge.de/

## Verdict / recommendation
- **The free AI layer of the x86 stack, headless:** StarNet v2.5.3 (star removal) +
  **DeepSNR** and/or GraXpert-denoise + AstroDenoisePy (denoise) + GraXpert BGE
  (gradient). All Class-2/driver-usable binaries, all CPU-capable. This is a complete
  free star-removal + denoise + gradient path with **no GPU and no GUI**.
- **Cosmic Clarity** is the free sharpen/deconv option (and star removal via Dark
  Star) — adopt if you accept 15–30 min CPU sharpen; else prefer BXT if any budget.
- **SyQon free tiers**: only if you accept **Siril-desktop GUI** operation — do not
  count them as headless without an x86 test. Quality is competitive, so worth a
  measured look on a desktop, but not a headless-pipeline primitive today.
- **Drop AstroSharp**; keep AIDT/AIST + AstroForge on a watch-list pending verification.

## Status
**PROVISIONAL.** Versions, capabilities, licensing, and architecture are
PRIMARY-VERIFIED (vendor sites + repos). The two empirical unknowns per tool are
Linux-headless actually-runs and CPU wall-clock on the i7 — the x86 setup test:
install each, run `--device CPU` / `-gpu false` headless on a representative frame,
time it, and (for SyQon/SCUNet) confirm whether `siril-cli -s` can drive the script
without a display.

## Graduation
- **TOOLS.md Tier 6 (denoise)** — upgrade **DeepSNR** to a first-class free headless
  option (NAFNet, native Linux CLI, self-contained ONNX, CPU fallback); keep
  AstroDenoisePy; note GraXpert-denoise CPU-slow.
- **TOOLS.md Tier 7 (star removal)** — StarNet **v2.5.3** `--unscreen`; note SyQon
  Zenith is GUI-in-Siril not headless-confirmed.
- **TOOLS.md Tier 5 (deconv/sharpen)** — **correct AstroSharp to a dead end**
  (TIFF<600 KB, no Linux, no CLI); Cosmic Clarity native-Linux + CPU-brutal timings.
- **TOOLS.md cross-cutting** — fix SyQon "Prism Mini" naming; mark SyQon/SASpro
  GUI-gated; add the AIDT/AIST + AstroForge watch-list.
- Applied in the graduation commit.
