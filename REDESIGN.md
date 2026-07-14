# REDESIGN.md — x86 re-founding of the pipeline

The authoritative go-forward plan. This repo was built on an **aarch64
(Kali arm64) BASE rig** — a prototype whose job was to establish the
discipline, build the self-auditing measurement harness, and learn the data
lessons. It did that. The **production rig is x86-64 Kali** (Intel i7
14th-gen, 32 GB RAM, 1 TB NVMe, **no GPU**). This document records what the
reset keeps, what it removes, and how the chain is rebuilt on x86.

## Why the reset

Two things converged:

1. **The rig migration** makes most of the repo's complexity throwaway. A
   large fraction of it is scaffolding for aarch64 constraints that do not
   exist on the target: no native StarNet binary, no StarXTerminator /
   NoiseXTerminator / Cosmic Clarity (x86-only), no astropy, a tight 118 GB
   shared disk, 7.7 GB RAM, 4 cores. Polishing the arm64 chain is a bandaid
   on a disposable platform.
2. **The Siril-1.4 discovery** (this session): Siril 1.4.4 ships a native
   Python API (`pyscript` + bundled `sirilpy`, proven headless on this rig),
   an auto-synced community script ecosystem, and a rich native command set
   (`denoise -da3d/-sos/-indep`, `ccm`, `synthstar`, `unclipstars`,
   `linstretch`, `rgbcomp`, `wavelet`, `subsky -rbf`). Most of what the
   pipeline hand-rolled is a native tool.

The tool-only render migration earlier this session proved the point: the
measurement/audit layer **separates cleanly** from the processing chain. So
the reset keeps the durable core and rebuilds the chain on x86 where the
real tools run.

**This is a redesign, not a scrap.** ~⅔ of the repo (the contract, the
measurement harness, the data lessons, the calibration/stack/compose
drivers) is platform-independent and ports to x86 ~verbatim. ~⅓ (the render
chain + aarch64 bandaids + resource adaptations + most of BACKLOG) is
removed here and rebuilt on x86. Everything removed is preserved in git
history at the `checkpoint` commit that precedes the reset.

## Target environment (x86-64 production rig)

- **Intel i7 14th-gen** (P+E cores, ~20 threads): fast stacking/registration,
  viable CPU inference.
- **32 GB RAM** (vs 7.7): hold full-frame float stacks in memory —
  `partitioned_stack` (the RAM workaround) is unnecessary.
- **1 TB NVMe** (vs 118 GB shared): keep **32-bit intermediates end to end**,
  keep per-experiment stacks, drop the aggressive per-stage cleanup and the
  16-bit-intermediate quantization compromise; fast I/O.
- **No GPU**: the newly-available AI tools (StarXTerminator, NoiseXTerminator,
  Cosmic Clarity, native StarNet, SCUNet) run **CPU-only** — feasible on the
  i7 but a real selection factor. Favor CPU-efficient tools; measure
  wall-clock.
- **x86-64 Kali**: unlocks native binaries and `astropy` (the equatorial→
  galactic 3×3 and other astropy gaps close).

What x86 unlocks that arm64 blocked:

- **Star removal**: native StarNet2, or StarXTerminator (best-in-class) —
  replaces BOTH the ONNX-under-onnxruntime workaround and the mask+inpaint
  fallback.
- **Denoise**: NoiseXTerminator / Cosmic Clarity Denoise / SCUNet — real AI
  denoisers that **close the chroma/luminance-noise gap** the removed corings
  left (Siril has no native chrominance-noise tool — its own docs punt to
  GIMP).
- **Deconvolution**: BlurXTerminator — the deconv step that was a measured
  dead-end on arm64 (unstable PSF, no tool).
- **PixInsight** (if licensed): the full reference toolset for cross-checking.

## Architecture thesis: invert the ratio

Today the pipeline is a **thick adaptation-chain** with a thin audit layer
bolted on. The redesign inverts it:

> **A THIN orchestration layer + a THICK measurement harness, over
> best-in-class tools.**

The audit layer *is* the product. Processing is "drive the good tools and
measure honestly." Every pixel-rewriting step drives a real tool (Siril /
StarXTerminator / NoiseXTerminator / GraXpert / BlurXTerminator /
astrometry.net, or a reference author's own open tool); python only computes
parameters, sequences, and MEASURES. The orchestrate-not-hand-roll guard
stays — now trivially satisfiable because the tools exist.

## KEEP — the durable core (ports to x86 ~verbatim)

Platform-independent numpy/FITS measurement + tool-orchestration + the
discipline. This is the hard-won value.

**Measurement & audit (the crown jewel):**
- `lib/astrometrics.py` — FITS I/O, bg/star metrics, radial profiles, masks
  (foreground + statistical sky + extended-object), `star_shell_report`,
  colour/MTF primitives.
- `lib/bg_qa.py` — THE GATE (statistical sky-scope; thresholds never loosen).
- `lib/render_helpers.py` — GraXpert runner, `measure_jpg`, ladder strips
  (prune unused after the rebuild).
- `lib/srgb.icc` — vendored sRGB profile (output colorimetry).
- `qa/inspect_stage.py` — per-stage inspection + the per-frame registration
  QA (the SubframeSelector measurement step).
- `qa/object_integrity.py` — object-region audit (chroma-neutralization +
  mid-scale mottle + gross-flattening).
- `qa/judgment_package.py` — judgment-set assembler (PNG8+PNG16 pixel-verify,
  WIN/NULL/needs-eyes verdicts).
- `qa/capture_report.py`, `qa/measure_stack.py`, `qa/cull_report.py`,
  `qa/stack_ab.py`, `qa/judgment_crops.py`, `qa/diag_flat.ssf` — capture
  card, stack stats, frame-cull analysis, stack comparators, crop panels,
  flat diagnostic.

**Calibration / stack / compose drivers (data-class, not arch):**
- `calibrate/solve_field.py` — blind astrometry.net solve (Siril's internal
  solver genuinely fails ultra-wide trailed fields — a data issue, not
  aarch64).
- `calibrate/spcc_cone.py`, `spcc_run.py` — local-Gaia SPCC coverage + runner.
- `stack/run_pipeline.sh` + `stack/siril/*.ssf(.tmpl)` — the Siril
  calibrate/register/stack orchestration.
- `stack/compose.py`, `fitsmeta.py`, `crop_coverage.py` — composition
  convergence, FITS metadata probe, drift-crop.
- `stack/selfflat.py`, `rechroma.py`, `siril/selfflat/*` — the self-flat
  branch (data-class adaptation for flatless sets; **not** arch-specific — it
  stays).
- `geometry/suggest_foreground.py` — per-set foreground derivation.

**The discipline & records:**
- The contract & acceptance model (CLAUDE.md rules, README process contract,
  experiment discipline, three-check acceptance, north star) — principles
  verbatim, environment re-founded on x86.
- `datasets/<session>/<set>/` — the per-dataset state MODEL
  (geometry/composition/recipe/experiments). NOTE: `recipe.json` render
  blocks, `GENERIC.json`'s render layer, and every `baseline.json` are
  **chain-coupled** — reference/pending until the new chain defines its knob
  schema and rebaselines on x86.
- Git history — the dead-end lessons and provenance the contract leans on.

## WIPE — product chain + aarch64/prototype bandaids (rebuilt on x86)

Removed from the working tree; preserved in history at the `checkpoint`
commit.

| Removed | Why it goes | x86 replacement |
|---|---|---|
| `render/starcomb.py` | The product chain — deeply arm/prototype-shaped (FITS round-trips, the old knob schema) | Rebuild tool-first: StarXT/StarNet + NoiseXT/Cosmic Clarity + BlurXT + Siril (autostretch/mtf/pm/satu/synthstar) + the sirilpy API |
| `render/operators.json` | Catalogs the wiped chain's operators | Re-seed with the new chain |
| `render/separation/starnet_sep.py` | ONNX-under-onnxruntime StarNet aarch64 workaround | Native StarNet2 / StarXTerminator |
| `render/separation/starsep.py` | mask+inpaint fallback (destroys resolved structure) — existed only because the weights were arch-blocked | Real star removal always available on x86 → no fallback needed |
| `render/nightlight_sho.py` | Nightlight arm64-staged binary driver | Revisit on x86 (Nightlight x86, or a native star-neutral path) |
| `stack/partitioned_stack.py` | 651-line workaround for 7.7 GB RAM | 32 GB → hold full sequences; unnecessary |
| `qa/hand_roll_audit.py` | The orchestrate-guard — scans the wiped chain | Re-port around the new chain (the guard PATTERN is durable) |
| `qa/sweep.py` | No-regression harness — renders via the wiped chain | Re-port around the new chain (the no-regression + declared-delta PATTERN is durable) |

## x86 tool inventory — DO THIS FIRST on the new rig

The chain design depends on what actually runs. On the x86 rig, verify /
install and record versions + CPU wall-clock (no GPU → time the inference):

- [ ] **Siril 1.4.4+** — native or flatpak? confirm `pyscript`/`sirilpy`,
  `denoise -da3d/-sos/-indep`, `ccm`, `synthstar`, `unclipstars`, `rgbcomp`,
  `linstretch`, `subsky -rbf`.
- [ ] **StarNet2** native x86 CLI (star-removal baseline).
- [ ] **StarXTerminator** (RC-Astro) — standalone or PixInsight-only? license?
  CPU wall-clock.
- [ ] **NoiseXTerminator** (RC-Astro) — the chroma/luminance-noise gap filler.
  CPU wall-clock.
- [ ] **BlurXTerminator** (RC-Astro) — deconvolution (a dead-end on arm).
- [ ] **Cosmic Clarity** (Seti Astro) — Linux x86 CPU build (denoise / sharpen
  / darkstar) — the free alternative to RC-Astro.
- [ ] **GraXpert** x86 (BGE + denoise) — already used; confirm.
- [ ] **PixInsight** — licensed? (reference cross-check; SPCC/BXT/NXT host).
- [ ] **astrometry.net** local indexes; **astropy** (installable on x86 —
  retire the fixed 3×3 equatorial→galactic fallback if wanted).
- [ ] Siril community scripts (VeraLux, SyQon, Naztronomy…): headless-viable?
  PyQt6 GUIs need a display (Xvfb, or a headless/argv fork). See the
  philosophy question below.

## Open philosophy question (decide before adopting the Siril script ecosystem)

A `sirilpy` `pyscript` doing numpy processing (e.g. VeraLux Silentium's
wavelet denoise) — is that **"orchestrating a Siril-ecosystem tool"**
(adoptable, like Nightlight) or **"someone else's hand-rolled numpy in a
wrapper"** (rejected by the same rule that removed ours)? The answer sets
whether the VeraLux/SyQon class is in-bounds at all, and whether they run
headless (Xvfb). Working recommendation: a distributed, versioned,
reputationally-vouched tool from the official Siril repo counts as a tool
(the Nightlight precedent); a script we would fork or edit does not.

## Rebuild order (on x86 — each step a measured experiment)

1. **Found the environment**: run the inventory above → new CLAUDE.md
   environment section + tool paths.
2. **Port the core verbatim**: the KEEP set runs unchanged (numpy / FITS /
   Siril-CLI). Smoke-test the gate + audits on a known stack.
3. **Rebuild the stack builder** minimally: drop `partitioned_stack`, go
   32-bit intermediates, confirm calibrate/register/stack + self-flat +
   compose on x86 Siril.
4. **Rebuild the render chain tool-first**, one operator at a time, each a
   measured declared delta against the ported gate/audits: star removal →
   StarXT/StarNet; denoise → NoiseXT/Cosmic Clarity (closes the coring gap);
   stretch → Siril autostretch/GHS or Statistical_Stretch; stars →
   synthstar/unclipstars; deconv → BlurXT; narrowband → the star-neutral
   question (Nightlight x86 or native `ccm` + recombine).
5. **Re-port the guards**: hand_roll_audit + sweep around the new chain;
   re-seed operators.json; rebaseline every dataset on x86.
6. **Re-found BACKLOG** from what the x86 rebuild actually surfaces.

## Portable lessons that survive (do NOT relearn)

From the dead-end registry — data / physics / tool-doctrine, arch-independent:

- The Milky Way band IS frame-scale curvature at wide focal length →
  `subsky 2` (curvature) erases it; only a first-degree plane or a full BGE
  is MW-safe.
- Unlinked autostretch on a calibrated stack is the chroma-blotch ("rainbow")
  engine — after SPCC there is no cast left to compensate, so use linked.
- SPCC narrowband mode equalizes O3=Ha and erases the O3 sphere → the sphere
  needs a **star-colour-neutral** balance (neutralise the mean star colour;
  narrowband stars carry ~no O3, so O3 is boosted), a different question than
  SPCC's photometric fit answers.
- Cloud culling is by per-pixel MAJORITY risk (a dwelling band survives
  `rej 3 3`), not by visibility; `nstars` is a blind cloud discriminant on
  rich fields (detection saturates at the star cap — the background channel
  carries the cloud signal).
- wFWHM weighting at low FWHM spread is WORSE than none (Siril `-weight` is a
  min-max ramp, driving the worst frame to ~0 weight at any spread).
- Drizzle on heavily oversampled data (short focal / large pixels) is
  pointless; deconvolution where trailing is in-exposure fails (unstable
  symmetric PSF on ≈0 background — revisit with BlurXTerminator on x86).
- Blind-solve from coarse PEAK centroids beats Siril's internal solver on
  ultra-wide trailed fields; PSF/blob centroids do not feed the matcher.
- The GATE must be a STATISTICAL sky scope — not hand-picked patches, not
  whole-frame (real MW/object signal reads as a background defect otherwise).
- Judgment is the user's eyes on FULL-FRAME LOSSLESS finals (PNG16+PNG8),
  opened independently; compare like encodings; one bracketed knob per
  experiment; nothing aesthetic commits before the user's eyes.
