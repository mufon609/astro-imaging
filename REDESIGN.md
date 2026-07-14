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

What x86 unlocks that arm64 blocked (the full tier-by-tier audit of every
option — free/paid, Linux/CPU/headless, when & why — is **[`TOOLS.md`]
(TOOLS.md)**; the highlights):

- **Star removal**: native StarNet2 (free CLI now runs — no ONNX workaround),
  StarXTerminator (best), or SyQon Zenith (new 2026 free AI).
- **Denoise**: NoiseXTerminator (best) / Siril native `denoise` (free,
  headless) / GraXpert / Cosmic Clarity / DeepSNR — real denoisers that
  **close the chroma-noise gap** the removed corings left (Siril has no
  native chrominance-noise tool — its docs punt to GIMP).
- **Deconvolution** REOPENS (it was a dead-end on arm — no tool + unstable
  PSF): BlurXTerminator (best; "correct only" even fixes elongated/trailed
  stars — the base rig's core data problem), or GraXpert deconv (free), or
  AstroSharp (free). 2026 rule: decon goes early-linear, BEFORE denoise.
- **RC-Astro (BXT/NXT/SXT) are now standalone Linux CLI + Siril-integrated**
  (2026) — NOT PixInsight-only anymore; one cross-platform license, AVX2 CPU
  (the i7-14700 qualifies), no GPU required.
- **GraXpert 3.x** now does BGE + denoise + AI deconvolution, all free + in
  Siril 1.4.
- **Siril 1.4 natives** may replace custom scripts: native astrometry.net
  blindsolve (VERIFIED — replaces `solve_field.py` for round-star data, but
  NOT the trailed/ultra-wide class: it feeds astrometry.net Siril's PSF
  `findstar`, the detection that fails on trails; keep `solve_field.py` for
  that class, test `-relax=on` on x86 — TOOLS.md Tier 2), native drizzle,
  `ccm`, curves, Star Re-composition.
- **PixInsight** (if licensed): the reference environment (WBPP, DBE/MARS).

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

**[`TOOLS.md`](TOOLS.md) is the tier-by-tier audit** of everything the rig
could use — the options at each pipeline stage, when/why to pick each, the
alternatives, and the cost / Linux / CPU / headless constraints. It is a
TOOLKIT, not a prescribed chain. The setup task on the x86 rig is to walk
TOOLS.md and record, per tool: does it install, does it license, and its
CPU wall-clock (no GPU → time the AI inference). Confirm at minimum: Siril
1.4.4+ (`pyscript`, `denoise -da3d/-sos/-indep`, `ccm`, `synthstar`,
`unclipstars`, native astrometry.net solve), GraXpert 3.x (BGE/denoise/
deconv), StarNet2 native CLI, astrometry.net + astropy; then decide whether
to license RC-Astro (BXT/NXT/SXT — best-in-class, now Linux CLI) and which
free AI tools (Cosmic Clarity, SyQon Zenith/Prism, AstroSharp, DeepSNR) to
stage.

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
4. **Rebuild the render as a TOOLKIT, not a fixed chain** — pick the tool
   per tier from [`TOOLS.md`](TOOLS.md) for the dataset + goal in front of
   you, each choice a measured declared delta against the ported gate/audits
   ([[pipeline-as-toolkit]]). The one process rule to honour (2026 consensus):
   gradient removal → colour calibration → **deconvolution (linear, before
   denoise)** → noise reduction (linear, on starless) → star removal (linear)
   → **stretch** → detail / colour / recomposition (nonlinear). What used to
   be a hole (deconv) is now a real early step; what used to be a hand-rolled
   coring (denoise) is now a tool.
5. **Re-port the guards**: hand_roll_audit + sweep around the new chain;
   re-seed operators.json; rebaseline every dataset on x86.
6. **Re-found BACKLOG** from what the x86 rebuild actually surfaces.

## Dead-end registry — do NOT re-attempt (rehomed from the deleted NOTES.md)

Data / physics / tool-doctrine mechanism lessons, arch-independent. **Read
this before proposing any experiment** (the contract's standing rule). Full
detail + the numbers live in git history (the `checkpoint` commit's NOTES).

**Gain/flat (the self-flat branch — kept code):**
- A free-form gain fit bakes sky glow into the gain (peaks off-axis toward
  the glow) — sanity-check any gain by its centre.
- A polynomial radial V(r) oscillates → concentric RINGS after division; only
  a monotone isotonic V is admissible. A per-channel V tints the corners
  (glow contaminates the per-channel falloff) → V must be GRAY.
- The true V lies between the multiplicative and additive fits of the median;
  only the empirical V2 of the frames ACTUALLY being divided is flat.
- Never refine the gain from the STACK's residual — the sky's own structure
  (MW/glow/clouds) exceeds the residual, giving opposite-sign results.

**Background:**
- The MW band IS frame-scale curvature at wide focal → `seqsubsky 2` erases
  it; only a first-degree plane or a full BGE is MW-safe.
- Stack-level-only BGE leaves a STRUCTURED residual (fails the rings gate,
  loses MW); per-frame `subsky 1` on the self-flat branch.
- GraXpert AI smoothing is NOT faint-nebulosity protection — smoothing blurs
  the model OUTPUT, not the inference; a frame-filling faint complex reads as
  the trained light-pollution class and is absorbed. Use a plane/off for
  object-filling fields. BGE does NOT absorb a centred galaxy's halo (it
  measures STRONGER against a lower far-field sky).

**Stretch / colour:**
- Unlinked autostretch on a calibrated stack is the chroma-blotch ("rainbow")
  engine — after SPCC there is no cast to compensate; use linked. Unlinked
  sky-anchored stretch as a narrowband line-lift is a NO-OP (BGE+SPCC already
  equalize the channel skies; the line imbalance is OBJECT flux, not sky).
- SPCC narrowband equalizes O3=Ha and erases the O3 sphere (raw O3/Ha ~1.5 →
  ~1.0; sphere B/R 0.77 vs 3.21). The sphere needs a **star-colour-neutral**
  balance (neutralise the mean star colour → O3 boosted, stars carry ~no O3)
  — a different question than SPCC's photometric fit. (Nightlight's mechanism;
  a native star-neutral tool is the open gap.)
- `rmgreen`/SCNR on a sky that is not green-dominant prints a global magenta
  cast.
- Siril has NO native chrominance-noise tool (its own docs punt to GIMP) — the
  chroma-noise gap is real; on x86 fill it with an AI denoiser (NoiseXT /
  Cosmic Clarity), NEVER a hand-rolled coring.

**Separation (informs the x86 tool choice):**
- A mask+inpaint separator DESTROYS resolved-object structure (inpaints HII
  knots out as stars, screens them back as blobs); a learned separator
  (StarNet2/StarXT) keeps field-star flux and far less object structure. Use
  the learned separator on resolved objects.
- A bright-star residual/shell is a per-DATA property (tight PSF vs big
  trailed PSF) — measure per dataset, never carry one set's number to another.

**Detection / solve / registration:**
- Frame QA + registration run on DEBAYERED data only — CFA-lattice
  registration false-positives on cloud texture (adjacent cloud frames
  cross-match → a cloud reference).
- Siril's internal solver fails ultra-wide trailed fields even with the local
  catalog; astrometry.net blind solve from coarse PEAK centroids works
  (blob/PSF centroids don't feed the matcher). Blind-solve first, label after.
- 1-pass sequence-start registration strands drifting tail frames; 2-pass +
  low detection sigma recovers them; on trailed frames a reference sweep beats
  the auto-reference. Keep all frames (dropping a minority sub-focal subset
  buys no matching gain and pays the full √N noise penalty).
- Cloud culling is by per-pixel MAJORITY risk, not visibility: a moving
  minority band stacks clean through `rej 3 3`; a DWELLING band becomes the
  per-pixel majority and survives. `nstars` is a blind cloud discriminant on
  rich fields (detection saturates at the star cap — the background channel
  carries the cloud signal).
- wFWHM weighting at low FWHM spread is WORSE than none (Siril `-weight` is a
  min-max ramp → worst frame ~0 weight at any spread).
- Drizzle on heavily oversampled data (short focal / large pixels) is
  pointless. CLASSICAL deconvolution (makepsf + RL) where trailing is
  in-exposure fails — unstable symmetric PSF on ≈0 background. This is NO
  LONGER a blanket dead-end on x86: BlurXTerminator's learned model corrects
  elongated/trailed stars where classical RL cannot (TOOLS.md Tier 5), and
  GraXpert/AstroSharp are free learned alternatives. Deconv is now a real
  early-linear step, done BEFORE denoise.

**QA / scope:**
- The GATE must be a composition-agnostic STATISTICAL sky scope — whole-frame
  reads real MW/object signal as a defect, and a geometric sky mask can't fix
  it (a bright object has no fixed band). Hand-picked patches miss defects a
  whole-scope measurement catches (the lesson that created the gate).
- Never hide a rim defect with a darker sky target or a crop — the rim is in
  the data (estimator extrapolation × stretch amplification), fix it there.
- Compare finals in LIKE encodings (q92+4:2:0 loses star-edge chroma to
  subsampling). Judgment is the user's eyes on FULL-FRAME LOSSLESS finals
  (PNG16+PNG8), opened independently; one bracketed knob per experiment;
  nothing aesthetic commits before the user's eyes.

## Acquisition checklist (the real quality lever — rehomed from NOTES.md)

Acquisition quality outranks processing; never bandaid what photons must fix.

- Record **14-bit Lossless-compressed** raw, NOT High-Efficiency (HE/HE★is
  TicoRAW-compressed, lossy-ish, and forces a DNG fallback); confirm 14-bit
  (high-speed continuous can drop to 12-bit).
- Use the sensor's higher conversion-gain stage (a dual-gain CMOS drops read
  noise above its switch ISO); keep subs ≤ 500/focal-mm — star trailing, not
  read noise, caps sharpness on an untracked/lightly-tracked rig.
- MORE integration is the real lever: when band signal/grain ≈ 1, every
  processing knob is only polishing until more photons arrive.
- Flats per focal length used that night, BEFORE touching the zoom; METER to a
  ~50% histogram peak (don't trust a shutter value); diffuse the source (a
  bare screen shows its pixel grid). VERIFY uniformity: shoot a flat, rotate
  the camera 180° against the source, shoot another — the two corner/centre
  ratios must match (an over-peaked source adds falloff the lens lacks and the
  flat is unusable; the lights' own sky corner/centre is the cross-check).
- Darks at the lights' exposure/ISO at night temperatures; biases at the
  flats' shutter (= exact flat-darks) — shoot them, it is 30 seconds.
- Lock the zoom ring (tape); don't touch the camera mid-set (a focal-length
  step forces a mixed-optics stack). Dither between subs; avoid the moon (star
  fringes on trailed PSFs are dispersion — physical, not removable in
  processing). Stop a fast lens down ≥1 stop for bright-star fields (wide open
  adds a red veiling-glare halo — an honest optical signature, not a bandaid
  to remove).
