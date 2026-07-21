# Render-tier build plan for the ARM base rig — pre-registered (deep dive)

> **This is the MEASURE → MATCH → RECOMMEND → REPORT package for the render
> tier, ending at the user's go/no-go gate. Nothing below executes without the
> user's explicit GO** (the operating loop: the user is the gate before any
> output-shaping run). Every claim carries its evidence class: **[probe]** =
> measured on this rig this audit; **[primary]** = vendor/official docs,
> independently re-verified; **[record]** = tracked repo measurement.

- **Question / scope** — Build the final-render tier for the approved
  full-session deliverable on THIS arm rig, from tools verified to run here,
  in standard-workflow order — while the genuinely environment-blocked tiers
  (separation + neural denoise/deconv binaries) wait for x86. Supersedes the
  blanket "render pending x86" framing: that conflated the user-gated BUILD
  with the environment; only the neural x86-64 binaries are rig-blocked.
- **Context** — Kali arm64, 4 cores, 7.7 GB RAM; Siril 1.4.4 flatpak (aarch64)
  [probe]; GraXpert 3.2.0a2 (geeksville fork, pipx; BGE model 1.0.1 + denoise
  model 3.0.2 cached) [probe]; darktable-cli 5.4.1. Input surface: the
  approved deliverable's linear chain — `stack_set-01+02+03+04+05_max_wcs.fit`
  (solved, pre-SPCC) and its ratified cov25 crop frame
  (`cov25frame_all5_map.json`: crop 3705 1437 3472 3456) [record].

## MEASURE — what the data is (all tool-sourced)

- Linear SPCC'd cov25 stack: 3472×3456 (12.0 Mpx), BITPIX 16, sky median
  ~92–93 ADU, mean R/G/B 95.6/96.0/95.8 (SPCC-neutral), bgnoise 1.8/2.2/1.8
  ADU [probe, Siril `stat`/`bgnoise`] — matching the recorded instrument
  numbers [record].
- Background noise composition [record, `noise_split.sh`]: the RANDOM
  component scales √N exactly; the visible floor is depth-independent static
  structure ≈1.0/1.5/1.2 ADU, of which the **drift-phase structured (walking-
  noise-class) term is ≈0.34/0.48/0.42 ADU (R/G/B) per ~199-frame half**
  (set-04) — the denoise tier's objective target. The remainder is
  unresolved-star confusion texture = REAL SKY, which no step may erase.
- Stars: trailed ~1.6:1 (in-exposure floor — unremovable), seqtilt on the
  deliverable 9138 stars / truncated-mean FWHM 3.17 px / off-axis 0.35 px
  [record]. **No clipped cores in linear**: channel Max 0.30 of full scale
  [probe] → `unclipstars` has nothing to fix in linear on THIS data; star
  protection is a stretch-time concern here.
- Field class: frame-filling MW + dark-nebula dust (dust preservation is
  priority #1). Registry constraint [record, dead-ends]: full AI background
  extraction ABSORBS frame-filling faint nebulosity, `seqsubsky 2` erases the
  MW band → the only dust-safe background moves on this field are a
  **first-degree plane or none**.
- No terrestrial foreground configured (whole frame is sky) [record].
- Residual gradient on the deliverable: regional medians 91–94 ADU
  (~1–3% class) [record, `gradient_stat_all5cov25frame.json`].

## MATCH — doctrine × registry × the verified tool surface

- **Background level** — Siril's own docs recommend **per-frame degree-1 on
  the subs when the gradient rotates with the session** ("in a single image,
  the background gradient is much simpler and generally follows a simple
  linear function"; FAQ: per-frame linear removal is "in general much better")
  [primary]; the general default is once-on-the-stack. PixInsight has no
  per-frame-DBE doctrine (it normalizes at integration) [primary]. The
  registry holds the same fork as a measured lesson from the pre-reset chain
  (stack-level-only left a structured residual). BACKLOG item 7 names the A/B;
  this dataset (fixed tripod, session-long field rotation) is exactly the
  geometry the per-frame doctrine addresses.
- **Order** — both vendors: gradient removal BEFORE photometric colour
  calibration, all linear [primary]. The repo's mechanism claim (SPCC's
  per-star annulus cancels a smooth background → K order-robust) becomes a
  CHECK, not an assumption: the A/B re-runs SPCC after the background step and
  records the K delta.
- **Denoise** — Siril: NL denoise "should perform best on unstretched images"
  [primary]; GraXpert's denoise model is built for linear data [primary].
  On arm the runnable arms are Siril native `denoise` [probe] and the
  installed GraXpert [probe]; every neural alternative is x86-blocked (§ENV).
  Whole-frame `bgnoise` is NOT the ladder metric: on a structure-floored sky a
  real denoise can RAISE the estimator (measured on the probe tile: Siril
  denoise 2.05→2.55 while GraXpert 2.05→1.14 — the estimator conflates
  revealed texture with noise) [probe]. The objective instrument is the
  noise-split decomposition (structured term ↓, confusion texture unharmed) +
  the user's eyes on dust.
- **Stretch** — GHS doctrine: iterative multi-pass with SP near the dimmest
  data of interest, HP protecting stars; one-shot autostretch is "rarely
  advisable as is" for production [primary]. Linked mandatory after SPCC
  (unlinked "will alter the white balance") [primary + registry]. The full GHS
  surface is scriptable HERE: `ght`/`invght`, `autoghs`, `modasinh`, `mtf`,
  `linstretch` [probe].
- **Star finishing without separation** — `synthstar` outputs a star MASK
  requiring a starless layer to recombine [probe + primary] → separation-
  dependent, x86-blocked. `unclipstars` is linear-only and this data has no
  linear clipping [probe] → N/A here; prevention (GHS `-HP`, clipmode
  rgbblend) is the star-finishing mechanism on this rig. `satu` has the
  background threshold (median+σ factor) [probe/primary]; doctrine places
  saturation after stretch, iteratively [primary].

## RECOMMEND — the pre-registered ladder sequence (one knob per experiment)

**Chain skeleton for every candidate** (each stage a full-frame FITS + the
tool's numbers into `<final>_stages/` — the per-stage visibility requirement):

```
max_wcs.fit ── crop cov25 (stat-verified vs coverage map — the y-flip guard)
  → [L1 background arm]  → SPCC (one unit; K + n recorded, delta vs control)
  → [L2 denoise arm]     → [L3 stretch arm] → [L4 satu] → savepng (16-bit)
```

Crop precedes the background step because `subsky`'s sample grid would ingest
the max-canvas's zero-coverage rims (its `-tolerance` excludes only BRIGHT
outliers [primary]) — and precedes SPCC so the background step can stay
doctrine-ordered before colour calibration. The control arm re-derives the
approved look through the same skeleton (crop → SPCC → stretch) so every
ladder's knob is the ONLY difference. All arms 32-bit from the crop on
(`set32bits`), `setcompress 0`, judged on full-frame lossless PNG16 in
`results/july14/judge/`, one arm per experiment, ledger entries in
`datasets/july14/set-01/experiments.jsonl` opened at run time with these
hypotheses, closed WIN | NULL | needs-eyes; a killed hypothesis goes to
`docs/dead-ends.md` with its numbers.

### L1 — background-step LEVEL (BACKLOG item 7's named A/B; runs FIRST)

- **Knob:** the background step: `none` (control) | `stack` (`subsky 1
  -dither` on the cov25 crop) | `frame` (per-frame `seqsubsky 1` before
  registration).
- **Hypothesis (pre-registered):** a first-degree plane per FRAME removes the
  session-rotated gradient component that no single stack-level plane can
  express, measurably flattening regional medians WITHOUT touching the MW/dust
  (a degree-1 plane cannot absorb structure); the stack-level plane improves
  the mean tilt only. Expected magnitude is small — the deliverable is already
  flat to ~1–3% [record] — so a NULL is a legitimate close (the step then
  stays OFF, its reason recorded).
- **Arms + cost:**
  - `stack` arm: minutes. `load` cov25 crop → `subsky 1 -dither` → SPCC.
  - `frame` arm, scoped: set-01 ONLY (its raws are staged; set-02's are not).
    Bracket first at ONE 15-frame group (insert `seqsubsky 1` on the warped,
    debayered frames before `register`; ~minutes): compare that group's stack
    vs its no-subsky twin (regional medians + stretched inspection). Only if
    the mechanism shows does the full 369-frame set-01 rebuild run (hours,
    groups route). Full-session per-frame adoption would need set-02 re-staged
    — a gate decision AFTER the set-01 verdict, never assumed.
- **Metrics:** `regional_stat.py` linear medians (the gradient instrument);
  SPCC K delta vs control (the order-robustness check); dust = the user's eyes
  on the PNG16 pair (the deciding metric); `seqtilt` sanity (stars/FWHM must
  not move — a plane cannot legally sharpen).
- **Registry guards:** degree 1 ONLY (degree 2 erases the MW band — dead-end);
  no GraXpert AI BGE on this frame-filling field (absorption dead-end);
  `-dither` ON for the stack arm (anti-banding; restores the knob byte-identity
  once cost).

### L2 — linear denoise ladder (after L1's verdict is adopted)

- **Knob (experiment D1):** denoiser identity on the L1-winning linear
  surface: `none` (control) | Siril `denoise` (defaults; auto cosmetic
  correction stays ON — the chain's `-cc=dark` already ran, but denoise's own
  CC is its documented default and is kept for the first rung) | GraXpert
  `-cmd denoising -strength 0.5 -gpu false`.
- **Hypothesis (pre-registered):** an NL/AI denoiser at moderate strength
  reduces the drift-phase STRUCTURED term (target: the measured 0.34/0.48/0.42
  ADU/half, set-04 [record]) and the residual random term, while the confusion
  texture (real sky) and the dust lanes stay — measured as: timehalf-vs-
  interleaved excess SHRINKS on denoised halves, and the user sees no dust
  loss at 1:1. Failure mode pre-named: plastic sky / eaten dust → that arm
  dies with its numbers.
- **Objective instrument (scoped where the baseline exists):** re-run the
  set-04 split on DENOISED halves — apply the arm's denoiser identically to
  the four existing set-04 half-stacks (timehalf + interleaved pairs,
  `july14/work/noisesplit_set04/`), recompute both diffs
  (`noise_split.sh` mechanics): structured excess after vs before. Siril arm
  ~minutes; GraXpert arm ~4 × ~30 min (24 Mpx halves, extrapolated from the
  71 s/1024² probe).
- **Follow-on rungs (each its own one-knob experiment):** strength within the
  winning tool (GraXpert 0.3/0.7 bracketing 0.5; Siril `-mod=` 0.5/0.75) —
  only after D1 picks a direction; `-indep`/`-da3d` only on their documented
  artifact triggers.
- **Chroma:** the general chroma-noise gap has NO arm fill (Siril has no
  general chroma tool [primary + registry]; NXT-AI3/Cosmic Clarity chroma
  controls are x86-blocked §ENV). `rmgreen` only on a MEASURED green
  dominance — the SPCC'd stack is neutral [probe], so expected unused.
- **Wall-clock:** full-frame 12 Mpx: GraXpert ≈13–14 min/arm [probe,
  extrapolated ×11.4 from tile]; Siril denoise seconds-to-a-minute class
  [probe]. Re-measured and recorded at run time.

### L3 — stretch ladder (replaces the diagnostic autostretch)

- **Knob (experiment S1):** stretch engine on the L1+L2-adopted linear
  surface, at a MATCHED background landing (so arms differ in curve shape,
  not brightness): `autostretch -linked` (control — the approved diagnostic
  look) | `autoghs -linked k D` (SP tracks the sky at k·σ from the median;
  bracket k∈{-2,-1,0} at the D that lands the control's background) |
  two-pass `ght` (doctrine form: pass 1 D moderate, SP at the measured sky
  point — sky median/65535 ≈ 0.0014 from `stat` [probe] — HP 0.7; pass 2
  gentle refine; exact params computed from the measured histogram at run
  time and recorded).
- **Hypothesis (pre-registered):** a GHS-class stretch at matched background
  reveals more faint dust structure at equal star bloat (HP-protected) than
  the single-shot autostretch — the doctrine position [primary], falsifiable
  by the eyes on the PNG16 set.
- **Objective checks (gate, not judgment):** zero highlight clipping
  (`stat` Max < 1.0), black point not crushed (Min > 0, low-tail fraction
  recorded), background landing within the matched band, star-count/FWHM on
  the stretched surface recorded for bloat comparison. Aesthetics = the
  user's eyes ONLY (needs-eyes verdict class).
- **Registry guards:** `-linked` mandatory post-SPCC (unlinked = the
  chroma-blotch engine [registry + primary]); no histogram compression to
  hide blown tops (no-bandaid rule); clipmode stays rgbblend (default).

### L4 — finishing (post-stretch, iterative, smallest knobs)

- **satu ladder:** amount ∈ {0.15, 0.30, 0.45}, `background_factor 1` (the
  threshold that spares sky noise [primary]), hue range 6 (all). One amount
  per experiment against the S1 winner; the user picks on the PNG16 set.
- **unclipstars:** N/A on this data in linear [probe — no clipped cores];
  re-checked on the stretched winner (if the stretch clips any core, the
  stretch arm is re-tuned instead — cause over symptom).
- **NOT run without a separate proposal:** `unpurple` (fringe cosmetic —
  tension with the registry's "dispersion fringes are physical" acquisition
  entry; needs its own case), `epf`/`wavelet`/`clahe` local contrast (later
  candidates once the base look is approved), `fixbanding` (axis-aligned
  only — the walking streaks sit ~5.6° off vertical, geometric mismatch, and
  item 11's mechanism work owns that defect).

**Sequencing rule:** L1 closes (user verdict) before L2 runs on its winner;
L2 before L3; a failed arm reverts to the standing control before the next
knob (revert-on-failure). Each experiment: full-frame PNG16 judgment set
via the standing surfaces in `results/july14/judge/`, records + verdicts in
the ledger; every run re-records its wall-clock.

## ENV — the verified environment-blocked list (arm)

Per-tool primary evidence (re-verified this audit; details in `TOOLS.md`):

| tool | blocked because | evidence class |
|---|---|---|
| StarNet2 v2.5.3 CLI | Linux builds are x64-only; sole ARM lane is macOS/CoreML; no source | [primary] starnetastro.com CLI matrix |
| RC-Astro `rc-astro` (BXT/NXT/SXT) | "Modern Intel/AMD x64 CPU … AVX, AVX2, and SSE … required" on Linux | [primary] rc-astro.com system requirements |
| DeepSNR 1.2.1 | Linux CLI is x64-only (ORT build); ARM64 = macOS CoreML only | [primary] starnetastro.com |
| Cosmic Clarity | release lanes Windows/Linux/AppleIntel/AppleSilicon — no ARM-Linux; MIT torch source public → source-run POSSIBLE but undocumented/unofficial (not a pinned route) | [primary] setiastro/cosmicclarity releases |
| PixInsight (gates all PI plugins) | Linux = x86_64 + AVX2/FMA3 required | [primary] pixinsight.com/sysreq |
| Siril `starnet`/`seqstarnet` | command present [probe] but requires the external StarNet binary above | [primary] Siril docs |

NOT blocked on arm (probed): the full Siril 1.4.4 native render surface;
GraXpert BGE (4.5 s/tile) + denoise (71 s/tile) on the installed fork; ASTAP
even has official aarch64 builds (uninstalled; roundness-gated for trailed
fields anyway) [primary].

## The GATE — decisions the user owns before anything runs

1. **GO / NO-GO / REROUTE** on the ladder sequence L1→L4 as pre-registered.
2. **GraXpert pin for the arm experiments:** the installed fork 3.2.0a2
   (+denoise model 3.0.2), recorded verbatim as this rig's pinned instance —
   or an official-source 3.0.2 install first (`pip` from the official repo
   tag; the x86 policy pin stays official either way).
3. **Per-frame arm scope:** accept the set-01-only scoping for L1's `frame`
   arm (full-session adoption would need set-02 re-staged — decided only
   after the set-01 verdict).
4. **SPCC `-atmos`:** available in 1.4.4 [probe]; needs the site
   elevation/pressure DECLARED (not in acquisition records). Default stays
   OFF unless the user wants it declared and laddered.

## Status

**PRE-REGISTERED, NOT RUN.** Every hypothesis above is written before any
execution; no output-shaping command runs until the user's GO. Tool-presence
and wall-clock probe numbers are from this audit's on-rig probes; doctrine
citations were independently re-verified from primary sources this audit.

## Graduation

- BACKLOG: this plan is the open render-tier item; item 7's A/B is L1.
- On completion each adopted knob re-seeds `datasets/GENERIC.json` + the
  per-set recipes (approved looks pin every knob), the no-regression harness
  gains its first render baseline, and the x86 plan (Phase 4) inherits the
  adopted arms as measured priors.
