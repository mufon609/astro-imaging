# RC-Astro BXT / NXT / SXT standalone CLI on Linux — deep verify

- **Question / scope** — The mission's flagged "deep verify": does RC-Astro
  (BlurXTerminator / NoiseXTerminator / StarXTerminator) ship a *real* standalone
  Linux CLI, and what are the exact invocation, CPU-only wall-clock (no GPU),
  license mechanics, and headless story? This is the single strongest paid
  recommendation in the toolkit; the money + doctrine decision rides on it.
- **Context** — 2026-07-14. Standalone CLI announced 2026-06-24, **`rc-astro`
  v0.9.9 beta 2026-07-02 → v1.0.0 production 2026-07 (out of beta)**; integrated into Siril (needs 1.4.4, announced
  2026-06). Target rig: x86-64 Kali, **i7-14700 (AVX2 ✓)**, 32 GB, **no GPU**,
  headless. Builds on [[siril-pyscript-headless]] (RC-Astro scripts are Class-2
  drivers).

## Findings

### 1. A real standalone CLI exists — and it's the clean headless primitive
- **Binary `rc-astro`**, one multi-tool with per-product subcommands **`bxt` / `nxt`
  / `sxt`**. Linux install `/opt/rc-astro`, symlinked into `/usr/local/bin`.
  v1.0.0 production 2026-07 (out of beta; 0.9.9 was the 2026-07-02 beta); standalone announced 2026-06-24.
- **Linux requirement: "Ubuntu 22.04+" is a glibc FLOOR, not a desktop or distro
  requirement.** RC-Astro states Linux reqs as glibc versions (its PixInsight build asks
  "Ubuntu 18.04 / glibc 2.27") → the standalone decodes to **glibc ≥ 2.35 + GLIBCXX ≥
  3.4.30 + AVX/AVX2/SSE**. It is a headless CLI (no GTK/GNOME libs), so **the desktop
  environment does not matter** — switching DE to "mimic Ubuntu" is a bandaid on a
  non-problem (Kali-GNOME is still Kali, same glibc). Debian-based **Kali has glibc 2.42
  + GLIBCXX 3.4.35 (verified) → clears the floor by forward-compatibility.** The
  definitive check is `ldd` on the binary, not the OS label.
- **Pure CLI, no display.** Reads/writes files directly; **formats TIF, FITS, XISF,
  PNG**; `--depth {8U,16U,32F,64F}` (default = input; RC recommends 32/64-bit float
  for linear BXT). Output defaults to `<input>-<product>.<ext>`; `-o/--output` (file
  or dir), `--overwrite` required to replace. Batch via wildcards.
- **Invocation (verbatim):**
  `rc-astro bxt image.tif --sharpen-stars 0.5 --sharpen-nonstellar 0.5`
  `rc-astro bxt input/*.tif --output out_dir`
- **BXT flags:** `--ss/--sharpen-stars`[0–0.7], `--ash/--adjust-star-halos`[-0.5–0.5],
  `--nsr/--nonstellar-radius`[0–8], `--ansr/--auto-nonstellar-radius`(def true),
  `--sn/--sharpen-nonstellar`[0–1], **`--correct-only`** (the trailed/aberration
  fixer, no sharpening), `--overlap`[0–0.5, def 0.2], `--ml-version N`(0=latest),
  `--device`, `--depth`, `--license`, `--activate`.
- **Introspection:** `rc-astro <product>` (no args) prints help; `rc-astro <product>
  --json` emits a machine-readable parameter schema (how Siril/SASpro build their
  UIs — a clean integration surface for our own orchestration).
- **Offline-capable:** internet is needed ONLY for (a) license activation, (b) ML
  model download, (c) update checks. **Processing runs fully offline once activated
  + models cached.** Pre-fetch with `rc-astro download-models`. → activate once
  online, then a headless/air-gapped box processes offline.
- **Device control (the no-GPU lever):** `--engine` was replaced by **`--device`**
  in 0.9.9. `rc-astro --device` lists devices; **`rc-astro <product> --benchmark-all`**
  benchmarks every device incl. CPU and saves the fastest as default;
  `--device cpu` forces CPU; `rc-astro --device-default <dev>` sets it.

### 2. Siril integration — Class-2 drivers, but call the binary directly for headless
- Three sirilpy scripts (BXT/SXT/NXT), announced by Cyril Richard (2026-06), require
  Siril 1.4.4 (+ SASpro ≥1.18.13). **They `subprocess` the `rc-astro` CLI** (import
  PyQt6 for the GUI + astropy for FITS I/O) — confirmed by reading
  `RC-Astro/BlurXTerminator.py` v1.0.5 source.
- Exact wrapper call: `rc-astro bxt -o <output.fits> --overwrite --device <dev>
  [params] <input.fits>`; the script writes a temp FITS, runs the CLI, parses the
  **NDJSON event stream on stdout** (status/device/progress/warning/error), reads the
  result back. Management probes: `rc-astro --json` (products+ML versions),
  `rc-astro --device --json`, `rc-astro bxt --ml-version N --json`.
- The scripts expose a headless CLI path (`pyscript BlurXTerminator.py --sn 0.5
  --ansr`, `--sequence`, `--correct-only`), runnable via an `.ssf` `pyscript`
  wrapper — but they are **GUI-first** (PyQt6). *Importing* PyQt6 needs no display;
  only `QApplication` does, and the CLI branch should skip it — but that is
  UNCERTAIN until tested on x86.
- **Doctrine call (matches [[use-industry-tools-not-hand-rolled]]):** for a headless
  pipeline, **call `rc-astro bxt/nxt/sxt` directly on FITS** and skip the Siril
  wrapper entirely. The CLI is a clean compiled-binary primitive — the same category
  as `solve_field.py` driving astrometry.net — so orchestrating it directly is
  strictly simpler and avoids the GUI-first uncertainty.

### 3. License mechanics
- **Per-tool, perpetual, no subscription** (free fully-functional trial). Prices
  (rc-astro.com, 2026-07): **BXT $99.95 · NXT $59.95 · SXT $49.95 · bundle ≈$189.85**
  ($10 off each additional tool once you own one). **`SIRIL10` = 10% off new.**
- **One license is cross-host AND cross-platform** — the same key works across
  PixInsight, Photoshop, Windows, macOS, Linux, the CLI, Siril, and SASpro. The
  **CLI is free for existing license holders** (no repurchase).
- Activation: `rc-astro <product> --activate <email> <key>`. Perpetual = up to **3
  computers**; activating multiple hosts on one computer consumes only one
  activation; resettable from the dashboard.
- **Headless-relevant:** activation requires outbound HTTPS **once**; "tools can be
  used offline after initial activation." Connectivity self-test at
  `validate.rc-astro.com`.

### 4. Hardware — AVX2, GPU-optional, CPU timings
- **AVX2 required** (AVX + AVX2 + SSE). **The i7-14700 qualifies.** Pre-AVX / some
  low-power CPUs are unsupported.
- **GPU optional.** On Linux, GPU accel needs an **NVIDIA** GPU (cuDNN 9, compute
  ≥7.5); **no GPU → automatic CPU fallback, fully supported**, just slower.
- **CPU-only wall-clock (indicative — other CPUs, re-measure with `--benchmark-all`):**
  BXT on an **i5-14600K CPU-only ≈ 40 s** (same Raptor-Lake family → the i7-14700
  should be **~30–40 s** for a typical frame; ~5.5 min was seen on an older Ryzen 9
  3900X for a big luminance frame). **NXT ≈ 20–30 s** on 45 MP (much lighter than
  BXT). **SXT** tens of seconds, faster than BXT. Planning figure, i7-14700 CPU-only,
  24–60 MP: **BXT tens-of-sec–~2 min; NXT/SXT faster.** SXT AI11's ~6 GB memory note
  is *GPU* memory; on CPU it uses system RAM (32 GB ample); "lite" AI11 variants use ~4× less.

### 5. Current AI model versions (mid-2026)
- **BXT: AI4** (2023-12; expanded aberration correction, direct linear processing).
  AI2 selectable. **No AI5.** PixInsight module 2.1.5 (2026-04).
- **NXT: AI3** (2025-02; vendor description: *"completely new architecture —
  iterative noise reduction, noise colour & frequency separation"*). AI2 selectable.
  → AI3 has a **dedicated chroma control**, not one global knob: `enable_color_separation`
  + `denoise_color` (chroma-HF, independent of the luminance `denoise`) + `denoise_lf_color`
  (chroma-LF) + `iterations` (RC-Astro AI3 release + PixInsight AI3 manual). This is the
  fill for Siril's chroma-noise gap. The only unobserved piece is the exact `rc-astro nxt`
  CLI flag spelling — no verbatim `nxt --help` is published; BXT shows 1:1 CLI↔PixInsight-param
  parity, so capture the real flags with `rc-astro nxt` no-args on x86. PixInsight module 2.3.4.
- **SXT: AI11** (2022-09, trained incl. JWST/Hubble). **No AI12.** "Lite" variants
  for low memory. PixInsight module 2.4.12.
- CLI model select: `--ml-version N` (0 = latest).

## Sources
- Stand-Alone RC-Astro Tools — https://www.rc-astro.com/stand-alone-rc-astro-tools/
- Stand-Alone CLI Release 1.0.0 (production, out of beta) — https://www.rc-astro.com/stand-alone-cli-release-1-0-0/ ; 0.9.9 beta (`--device`, `--benchmark-all`, breaking change) — https://www.rc-astro.com/stand-alone-cli-release-0-9-9/
- License FAQ (cross-platform, free for holders, 3 activations) — https://www.rc-astro.com/faq/do-i-need-to-purchase-new-licenses-to-use-the-cli/
- RC-Astro FAQ (AVX req, offline-after-activation, Linux cuDNN/compute-cap, SXT memory) — https://www.rc-astro.com/frequently-asked-questions/
- Product pages (prices, AI versions) — https://www.rc-astro.com/software/bxt/ · /nxt/ · /sxt/
- Siril announcement (3 scripts, Siril 1.4.4, SIRIL10) — https://siril.org/2026/06/rc-astro-tools-available-in-siril/
- **Siril RC-Astro script source** (exact `rc-astro` invocation, subprocess, NDJSON, pyscript headless usage) — https://gitlab.com/free-astro/siril-scripts/-/raw/main/RC-Astro/BlurXTerminator.py
- discuss.pixls.us "Can sirilpy python scripts run via siril-cli?" — https://discuss.pixls.us/t/can-sirilpy-python-scripts-run-via-siril-cli/53685
- Cloudy Nights BXT/NXT timing threads — https://www.cloudynights.com/topic/909926-blurxterminator-processing-time/ · https://www.cloudynights.com/articles/astro-gear-today/reviews/software/noise-be-gone33-testing-rc-astro-noisexterminator-r4568/
- Note: rc-astro.com + cloudynights.com return HTTP 403 to automated fetch; RC-Astro
  content verified via browser-UA retrieval; GitLab (the key deep-verify source) is
  fully fetchable.

## Verdict / recommendation
- **RC-Astro is genuinely usable on this rig, headless, no GPU, at reasonable CPU
  wall-clock.** The old "PixInsight-only on Linux" blocker is gone. If any budget
  exists, **BXT ($99.95) is the strongest single spend** (best deconvolution +
  fixes trailed/elongated stars via `--correct-only` — the base rig's core data
  problem), **NXT ($59.95)** the fastest best denoise (and its AI3 "colour separation"
  is the **likely** chroma-noise-gap fill — verify), **SXT ($49.95)** the best star separation.
- **Orchestrate the `rc-astro` binary directly** (Class-2, file-in→file-out), not the
  GUI-first Siril pyscript. Activate once online + `download-models`, then run
  offline. Use `--benchmark-all` on real frames to get true wall-clock and to pin
  `--device cpu`.
- This does **not** displace the free stack — it augments it. The free path (Siril +
  GraXpert + StarNet2) remains complete; RC-Astro buys quality + speed + the
  chroma-noise/trailed-star fixes.

## Status
**PROVISIONAL (primary-verified specs; not yet run on our rig).** All CLI/flags/
license/model facts are PRIMARY-VERIFIED from rc-astro.com + the Siril script source.
The two empirical unknowns for x86: (a) the *full* shared-lib set the binary pulls — the
stated glibc-2.35 / GLIBCXX-3.4.30 floor is already cleared by Kali's 2.42 / 3.4.35
(verified), so confirm the rest with `ldd <rc-astro>` on the rig; any gap is a specific
`apt install`, never a distro/desktop change; (b) true i7-14700 CPU wall-clock per tool
at our frame sizes
(`--benchmark-all` + timed run). Also verify the Siril script's CLI branch avoids
`QApplication` if wrapping it headless (or just call `rc-astro` directly and moot it).

## Graduation
- **TOOLS.md Tier 5 (BXT)** — concrete standalone-CLI facts: `rc-astro bxt`,
  `--correct-only`, AI4, CPU ~30–40 s (14th-gen), $99.95, offline-after-activation,
  call-directly doctrine.
- **TOOLS.md Tier 6 (NXT)** — AI3 colour+frequency separation ⇒ the concrete
  chroma-noise fill; CPU ~20–30 s; $59.95.
- **TOOLS.md Tier 7 (SXT)** — AI11, CPU tens-of-sec, $49.95, `rc-astro sxt`.
- **TOOLS.md cross-cutting "PAID but Linux-CLI"** — replace the general claim with
  the concrete `rc-astro` v1.0.0 CLI, prices, AVX2, offline, Ubuntu-22.04 caveat.
- **TOOLS.md** — the RC-Astro-Linux-CLI bullet → concrete; add "call the binary
  directly, don't wrap the GUI pyscript" + "activate-once-online then offline" to
  x86 setup; chroma-noise dead-end → NXT AI3 colour separation is the **likely** fill
  (verify it exposes a chroma control).
- Applied in the graduation commit.
