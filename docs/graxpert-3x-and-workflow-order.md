# GraXpert 3.x status + the modern workflow-order consensus — deep dive

- **Question / scope** — Two linked things: (1) the real state of GraXpert 3.x
  (BGE / denoise / deconvolution) — version, CPU-only viability, headless CLI,
  Siril integration — because GraXpert is the cornerstone of the *free* x86 stack;
  and (2) validate the "one process rule" the toolkit states (deconvolution
  early-linear, before denoise; star-removal placement) across multiple credible
  2026 sources, and surface any consensus shift.
- **Context** — 2026-07-14. Target rig: x86-64 Kali, i7-14gen (AVX2, ~20 threads),
  32 GB, **no GPU**, headless. Siril 1.4.4 stable. Builds on
  [[siril-natives-and-trailed-solve]].

## Findings — Part 1: GraXpert 3.x (a material correction)

### Version & development status — stable frozen at 3.0.2; a 3.2.0 ALPHA lives on PyPI
- **Two distribution channels diverge** (verified first-hand on the arm rig +
  PyPI/GitHub APIs, 2026-07): **GitHub releases** peak at **`3.1.0rc2` (2025-01-01,
  pre-release)** over stable **`3.0.2` (2024-05-03)** with `main` frozen; but
  **PyPI** carries a newer **`3.2.0` ALPHA line** — `3.2.0a0.dev4…a2`, latest
  **`3.2.0a2` (2025-12-17)** — installable via `pip`/`pipx` (the arm rig runs
  exactly this). So CLAUDE.md's "GraXpert 3.2" is *correct* (3.2.0a2); there is no
  3.2.0 *stable*. **Net: latest stable = 3.0.2 (BGE+denoise only); everything with
  deconvolution is pre-release** (the 3.1.0-RC and 3.2.0-alpha lines).
- Development continues but **no STABLE release in ~2 years** (since 3.0.2,
  2024-05): the `develop` branch has commits through late-2025 (build/onnxruntime
  fixes; an experimental ONNX→PyTorch inference swap), and the **3.2.0-alpha line
  shipped to PyPI (a2, 2025-12-17)** — so it is not abandoned, just perpetually
  pre-release, with deconvolution never graduating to stable.
- **Feature-by-version:** BGE = all 3.x; **denoise added 3.0.0** (2024-04-17);
  **object deconv → 3.1.0rc1** (2024-11-10); **stellar deconv → 3.1.0rc2**
  (2025-01-01). **Deconvolution has therefore NEVER been in a stable release.**
- → This **corrects the current TOOLS.md/REDESIGN framing** ("GraXpert
  deconvolution, object + stellar AI, 2026" as a settled free option). Correct
  facts: deconv is a **pre-release feature** (3.1.0-RC / 3.2.0-alpha, late-2024
  → Dec-2025), never in a stable release; the x86 inventory must record the
  actual installed build (`pip show graxpert`) + model versions, and check via
  PyPI (`pip index versions graxpert`), not GitHub releases alone — the two
  channels diverge.

### (a) BGE — the free gradient standard, CPU-fast
De-facto free gradient-removal standard; BGE inference is **"almost instantaneous"
even on CPU** (lightweight model, not the heavy tile path). Fully headless +
Siril-integrated. No change to its standing.

### (b) Denoise — good quality, but CPU-SLOW is the real cost on a no-GPU rig
- Quality ≈ NoiseXTerminator, with a **slight edge to NXT** (ben.land); free.
- **CPU wall-clock is the catch** (documented, GitHub issues): 6000×4000 px on a
  Ryzen 7 5800 (8c/16t) Linux → **">30 minutes"**; 48 MP on M4 Pro CPU → 14.5 min;
  12000×8000 → ~1 hr. A **regression** is documented: same HW went from ~5 min
  (denoise model 1.0.0) to >30 min (3.0.x) — algorithmic, not hardware. GPU is
  ~6–7× faster than the CPU fallback.
- `-batch_size` (1–32, default 4) trades RAM for throughput; 32 GB permits raising
  it. **i7-14gen estimate (UNCERTAIN, no published number):** minutes for moderate
  frames, tens of minutes for large (>24 MP) frames.

### (c) Deconvolution — the weaker, less-mature path; BXT remains the reference
- RC/beta only. Two modes; both take `strength` 0–1 and `psfsize`/Image-FWHM 0–10.
- **Open artifact bug (issue #243, opened 2025-10-14, still open in 3.1.0rc2):**
  object-mode produces horizontal/vertical dark edge bands + a rectangular region
  of altered saturation/colour, visible after stretch — reported as **object-mode
  only** (not BGE/denoise/stellar). A real, unresolved maturity problem.
- **Siril's maintainer (2025-01) called GraXpert deconvolution "too difficult to
  maintain"** — that referred to the *old C wrapper* (later restored via the Python
  interface, see below), but it signals maturity concerns.
- The common "looks artificial" knock is **NOT substantiated** in primary sources —
  the concrete, verifiable issues are the object-mode artifact bug and weaker
  star-shape correction vs BXT. Treat "artificial" as UNCERTAIN.
- CPU deconv timing not separately documented; same ONNX tile path as denoise →
  expect the same order (minutes → tens of minutes).

### CLI invocation (authoritative — from `graxpert/main.py` argparse)
- **No separate `graxpert-cli` binary** — the same executable does GUI + CLI; on
  Linux it's the `GraXpert` binary from `graxpert-linux-amd64.zip`; **`-cli` is
  mandatory** to suppress the GUI.
- Global: `-cli`, `filename` (positional), `-cmd {background-extraction,denoising,
  deconv-obj,deconv-stellar}` (default background-extraction), `-gpu {true,false}`
  (default auto), `-ai_version N.N.N`, `-output NAME`, `-preferences_file`, `-v`.
- BGE: `-correction {Subtraction,Division}`, `-smoothing 0..1`, `-bg`.
  Denoise: `-strength 0..1` (0.5), `-batch_size 1..32` (4).
  Deconv (both): `-strength 0..1`, `-psfsize 0..10`, `-batch_size`.
- **CPU-only example:** `./GraXpert my_image.fits -cli -cmd denoising -strength 0.6
  -gpu false`. (Some third-party docs list only BGE/denoise — the source confirms
  deconv IS exposed via CLI.)
- Models live at `github.com/Dark-Matters-Astro/graxpert-ai-models`, auto-downloaded
  on first use, `-ai_version` pins. Newest: denoise 3.0.2 (2025-01-12),
  object-deconv 1.0.1, stellar-deconv 1.0.0 (both 2025-01-02).
- Linux CPU: links onnxruntime 1.20; GPU = CUDA 12 + cuDNN 9 (NVIDIA-only) → with
  no GPU falls back to `CPUExecutionProvider` (AVX2, multithreaded). Fully
  supported, just slower.

### Siril integration (reconciled)
- Siril drives GraXpert via the bundled **`GraXpert-AI.py`** pyscript, which reads
  GraXpert's ONNX models directly (replaced the earlier unreliable C wrapper).
  Present in stable **Siril 1.4.4**. **Stable Siril exposes all three** (BGE /
  Denoise / Deconv Stars+Objects); deconv options appear **only if deconv-capable
  models are installed** — docs explicitly recommend **GraXpert 3.1.0-RC2**.
- So on the x86 rig: **Siril 1.4.4 + GraXpert 3.1.0-RC2 → headless BGE + denoise +
  deconv** (a Class-2 driver per [[siril-pyscript-headless]]); flags via pyscript
  `-bge/-denoise/-deconv_obj/-deconv_stellar`, `-model=`, `-strength=`, `-psfsize=`,
  `-nogpu`.

## Findings — Part 2: workflow-order consensus (validated, with refinements)

### (a) Deconvolution early / linear / before NR — STRONG consensus, with a nuance
- Canonical mechanism (RC-Astro / Russell Croman, quoted across sources):
  *"Noise reduction (of any sort) should not be applied before deconvolution … NR
  tends to destroy the low-contrast information at fine scales that deconvolution
  needs … and gives the deconvolution algorithm a false sense of the SNR."* Plus:
  the PSF is modelled from the **linear, unstretched** image; stretching/denoising
  first invalidates it → ringing.
- **NUANCE (refines our absolute-sounding rule):** **Siril's own docs recommend a
  *little* NR *before* deconvolution** — an Anscombe VST at ~50–60% to "take the
  edge off" background noise so you can push more Richardson-Lucy iterations. So the
  real rule is **"no *heavy* NR before deconvolution,"** not "zero NR." Light
  pre-deconv NR is sanctioned.

### (b) Star-removal placement — genuinely variable
- RC-Astro (StarXTerminator): *"as early … as possible, ideally right after
  integration, with the data still linear (prior to stretching),"* using
  Subtraction (not Unscreen) on linear data.
- Deconv vs star-removal: **most run deconvolution with stars still present, then
  remove stars** (BXT is built to handle stars; removing first can over-process
  stellar halos). A minority remove stars first, then deconvolve starless.
- **Dissent:** many popular tutorials (AstroBackyard) remove stars **after the
  first stretch** (nonlinear). Placement is legitimately variable (linear-early vs
  post-stretch).

### (c) The full order — our stated order is broadly the mainstream, with caveats
Mainstream "linear-first" 2026 order:
> **gradient/background extraction → colour calibration (SPCC, on linear) →
> deconvolution (linear, stars in) → [star removal] → noise reduction (linear,
> often on starless) → STRETCH (GHS/arcsinh/MTF) → nonlinear detail / colour /
> saturation / star recomposition.**
Independent support: RC-Astro (Croman), Siril docs, PixInsight/Conejero M81-M82
example, 2025 AstroBin workflow threads. Caveats vs our current phrasing: deconv is
usually done **with stars present** (not after star removal), and "colour
calibration" specifically means **SPCC on barely-processed linear data**.

### Explicit dissent + the 2026 shift (important to record honestly)
- **AstroBackyard (Trevor Jones)** — NR *before* deconv, star-sep *after* first
  stretch. Popular but non-canonical (a commenter flags the RC-Astro contradiction).
- **ben.land, "Deep-sky images vol. 3" (2025-12-30)** — a deliberate **stretch-early
  school**: Stretch → SPCC → NR (DeepSNR) → Deconv (BXT "correct-only") → SXT →
  detail/colour. **Inverts two consensus rules** (NR-before-deconv, deconv-after-
  stretch); rationale: modern AI tools are order-tolerant, and NR-before-sharpen
  avoids amplifying artifacts. Credible current dissent.
- **Cuiv** — deconvolution/sharpening late (post-stretch).
- **2026 SHIFT:** because BXT/SXT/NXT/DeepSNR/GraXpert are noise-tolerant and
  self-normalizing (SXT internally stretches→reverses on linear input),
  respected practitioners increasingly run **NR and even deconv in the nonlinear
  stage**. "Linear-only deconvolution" is now a **strong default, not an absolute
  rule.** And RC-Astro's June-2026 CLI + Siril integration makes the **BXT-first
  linear-deconv workflow reachable headless on Linux/CPU** without PixInsight.
- **What everyone still agrees on:** colour calibration on **linear,
  minimally-processed** data; and **no *heavy* NR before deconvolution.**

## Sources
- GraXpert releases (API) — https://github.com/Steffenhir/GraXpert/releases ·
  `main.py` CLI — https://github.com/Steffenhir/GraXpert/blob/main/graxpert/main.py
- GraXpert AI models — https://github.com/Dark-Matters-Astro/graxpert-ai-models/releases
- Object-deconv artifact bug #243 — https://github.com/Steffenhir/GraXpert/issues/243
- CPU denoise timing #159 — https://github.com/Steffenhir/GraXpert/issues/159 (also #210, #224)
- Siril GraXpert interface — https://siril.readthedocs.io/en/stable/processing/graxpert.html
- Siril deconvolution docs (light-NR-before-deconv) — https://siril.readthedocs.io/en/stable/processing/deconvolution.html
- Siril maintainer on GraXpert deconv — https://discuss.pixls.us/t/graxpert-no-deconvolution-latest-git/47849
- RC-Astro workflow FAQ / SXT notes (via snippet; rc-astro.com 403s automated fetch) —
  https://www.rc-astro.com/faq/what-is-the-right-workflow/ · https://www.rc-astro.com/starxterminator-usage-notes/
- ben.land vol. 3 (2025-12-30) — https://ben.land/post/2025/12/30/deep-sky-images-vol-three/
- AstroBackyard workflow — https://astrobackyard.com/astrophotography-processing-workflow/
- PixInsight M81/M82 (Conejero) — https://www.pixinsight.com/examples/M81M82/index.html

## Verdict / recommendation
- **GraXpert: keep BGE as the free gradient default** (CPU-fast, headless). **Treat
  GraXpert denoise as a viable free fallback but budget CPU minutes-to-tens-of-
  minutes** (NXT is faster + slightly better if licensed). **Downgrade GraXpert
  deconvolution to "RC-stage, use with caution"** — it is not a shipped stable
  feature, object-mode has an open artifact bug, and BXT remains the reference. On a
  free-only x86 box, GraXpert deconv or Siril RL are the options; if any budget
  exists, BXT via the RC-Astro CLI is the deconvolution answer.
- **Workflow order: keep the linear-first order as the DEFAULT, not an absolute.**
  Encode the two refinements — *light* NR before deconv is fine (Siril VST), and
  star-removal placement is a per-dataset choice — and record the 2026 AI-driven
  nonlinear-stage option as a sanctioned alternative to measure, not a violation.

## Status
**PROVISIONAL.** GraXpert version/CLI/bug facts are PRIMARY-VERIFIED (GitHub API +
source + issues). CPU timings are real but from other CPUs — the i7-14gen numbers
are UNCERTAIN until measured on x86 (a named test: time `-cmd denoising`/`deconv-obj`
`-gpu false` on a representative frame). Workflow-order is a documented-consensus
synthesis, not an empirical result on our data.

## Graduation
- **TOOLS.md Tier 5 (deconv)** — correct the GraXpert row: RC-only (3.1.0rc2), never
  stable, object-mode artifact bug #243, needs GraXpert 3.1.0-RC2 for Siril deconv;
  fix "2026" dating; note BXT remains reference and CPU timing reality.
- **TOOLS.md Tier 4 (BGE)** — note BGE is CPU-fast (near-instant), unlike GraXpert
  denoise/deconv.
- **TOOLS.md Tier 6 (denoise)** — add GraXpert denoise CPU wall-clock reality +
  `-batch_size` + the >30-min regression; NXT slight quality edge.
- **TOOLS.md "one process rule"** — refine to a *strong default*: light NR before
  deconv is accepted (Siril VST); star-removal placement is variable; 2026 AI tools
  loosen the linear-only rule (ben.land/Cuiv), a measurable alternative not a
  violation.
- **REDESIGN** — x86 inventory: record GraXpert's actual installed version + model
  versions (GitHub stable = 3.0.2; deconv only in 3.1.0rc2; "3.2" unverified);
  dead-end/Tier-5 note: GraXpert deconv is RC-and-buggy, BXT is the mature path.
- Applied in the graduation commit.
