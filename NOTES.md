# Astrophotography processing pipeline

Repo tracks the **processing pipeline** (Siril scripts + notes), not image data
(see `.gitignore`). Iterate on the pipeline, commit, re-run, compare previews;
revert with git if a change makes things worse.

## Environment

- Nikon Z6 III, raws converted to DNG (Adobe DNG Converter 18.4), 14-bit, RGGB
- Siril 1.4.4 as user flatpak: `flatpak run --command=siril-cli org.siril.Siril`
  - Flatpak sandbox has `home`/`host` access but **its own /tmp** — scripts must
    live under the home dir, not /tmp
- Host: Kali linux arm64, 4 cores, 7.7GB RAM, ~40GB free disk
  - Pipeline uses 16-bit intermediates + per-stage cleanup to stay within disk;
    final stack is 32-bit float

## Session 07-02-26 inventory (verified via exiftool + siril stat)

Calibration frames **re-shot 2026-07-05** (replacing the mismatched 1/10s darks
and dim 1/200s flats — see "Re-shoot outcome" below):

| dir    | n   | exposure | ISO | f/  | mm | taken               | pixel-level check |
|--------|-----|----------|-----|-----|----|---------------------|-------------------|
| lights | 32  | 20s      | 200 | 4.0 | 24 | Jul 2 23:55–Jul 3 00:14 | mean 1065, bg ~57 ADU above offset, stars saturate |
| darks  | 40  | 20s ✓    | 200 | 4.0 | 24 | Jul 5 14:20–14:35   | mean 1007.5 ≈ bias (no measurable mean dark current at 20s), σ 4.6, hot px to 4246 |
| biases | 98  | 1/160s   | 200 | 4.0 | 24 | Jul 5 13:55–13:57   | mean 1007.8, σ 4.08 ✓ |
| flats  | 100 | 1/160s   | 200 | 4.0 | 24 | Jul 5 13:53–13:54   | median 1964 (≈956 ADU signal), peak ~4400/16383 ≈ 27% |

Sensor offset (black level) ≈ 1008 ADU. Biases share the flats' 1/160s shutter,
so they double as exact flat-darks.

### Remaining acquisition caveats

1. **Flats still under target**: ~27% of full scale at peak (goal ~50%); brighter
   than the first attempt (~20%) but shy — next time ~3× more shutter (≈1/50s at
   the same screen brightness). 100 frames keep master-flat noise ≪ sky noise.
2. Darks shot at afternoon temps vs midnight lights: mean level is unaffected
   (≈ bias), and the hot-pixel population at warmer temp is a superset — fine
   for subtraction + `-cc=dark` mapping.
3. Flats/biases/darks shot 3 days after lights. Same lens/aperture per EXIF, so
   flats remain valid **if** the lens was untouched (dust/rotation) in between.
4. Session underexposed overall: ISO 200, sky bg only ~57 ADU over offset.
   Z6III's second gain stage starts at ISO 800 — ISO 200 has the high-read-noise
   path. Expect heavy stretch, watch for pattern noise.

## Pipeline design (v4 — per-set)

A session dir holds **shared calibration** (darks/biases/flats) plus one or
more **light-frame sets** (`lights/`, `set-03/`, …).
`scripts/run_pipeline.sh <session-dir> [lights-set]` (set defaults to `lights`)
orchestrates five siril-cli stages, deleting each stage's intermediates before
the next (disk-limited):

0. preflight — exiftool check: hard-fails on an empty frame dir or a dir
   mixing exposure/ISO (protects against stale frames after a re-shoot);
   warns on darks/set exposure mismatch and ISO mismatches; compares
   **focal length + f-number** of flats vs the set. A flat is used only when
   flats AND biases dirs exist and the optics match — otherwise the set
   takes the self-flat path. Only darks + the set dir are required at all;
   flat/bias master stages are skipped entirely when unused.
   Masters rebuild on **manifest change** (file names+sizes+mtimes recorded
   at build time) — catches re-shot frames even when copied with older
   timestamps, which a plain `-newer` check silently misses.
1. `10_master_bias.ssf` — stack biases, Winsorized rej 3/3, no norm
2. `20_master_flat.ssf` — calibrate flats with master bias, stack norm=mul
3. `30_master_dark.ssf` — stack darks
4. `40_lights.ssf.tmpl` — per-set script generated into `work/` (`@SET@`,
   `@FLATOPT@`): calibrate (`-dark` + `-cc=dark` hot-pixel removal, flat +
   equalize_cfa when optics match, debayer) → `setfindstar -sigma=0.5` +
   **two-pass** register + `seqapplyreg` → 32-bit rej stack norm=addscale +
   rgb_equal → `results/stack_<set>.fit`. The calibrate command is correct
   for matched *and* mismatched darks.
   **Flatless sets take the SELF-FLAT path instead** (4a/4b/4c/4d):
   `40a_selfflat_median.ssf.tmpl` calibrates without flat, median-stacks
   the UNREGISTERED frames (drifting stars self-reject; the static
   vignette × sky survives), then `seqsubsky pp_light 1` subtracts each
   frame's PLANAR glow (level-preserving, sensor coords, while linear) —
   the frames that continue are glow-free so the later division amplifies
   only the glow's curvature residual, not the full tilt.
   **V must be estimated from the UNTOUCHED median** (the multiplicative
   factorization V×S only holds there): estimating from glow-subtracted
   frames breaks — subsky's per-channel level restoration shifts the
   pedestal/bowl ratio and the extracted V diverges per channel (measured
   0.61/0.37/0.47 corners vs the true 0.52–0.56 → corner tint on division).
   `scripts/selfflat.py` separates the median into **V(r) × S(planar)** on
   a 101px block-median grid with 2.5σ clipping (alternating fits; planar S
   has no radial term so all falloff lands in V; foreground/star residue
   reject as outliers; aborts if >25% of the grid rejects). V(r) is
   **binned radial medians + isotonic non-increasing regression**, NOT a
   polynomial — an r²/r⁴/r⁶ fit oscillated (+4% mid-radius hump, corner
   upturn) and printed concentric light/dark RINGS into the sky after
   division; concentric structure is invisible to x-y subsky, so it must
   never enter the gain. The division uses a **GRAY V** (mean of the three
   channel profiles): the colored glow's radial component contaminates
   per-channel falloff (~5% spread, R deepest with warm moonglow) and
   per-channel division tints the corners red; a gray gain cannot change
   color by construction. Writes V (V(center)=1, float FITS) →
   `40b_selfflat_divide.ssf.tmpl` DIVIDES every glow-subtracted frame by V
   (second `calibrate -flat=` pass) — corner stars and sky re-brighten
   together, which `subsky` can never do.
   Gain kept at `work/masters/selfflat_<set>.fit` for inspection.
   Registration then runs as a **reference sweep** (bash loop, 1-pass
   `setref` + `register` per candidate, mid-sequence outward, early-stop on
   all-registered, best kept): with trailed stars, star matching succeeds or
   fails per reference and no heuristic predicts it — measured on set-03:
   ref 11 → 19/21, ref 12 → 21/21, 2-pass auto-pick (14) → 18/21.
   `40d_selfflat_stack.ssf.tmpl` stacks the winner.
   *v1 lesson (2026-07-06): fitting ONE free-form surface and dividing bakes
   the moonglow into the gain — its peak lands off the optical axis and
   regional brightness distorts (visible as blotchy over/under-corrected
   sky). Always sanity-check a fitted gain by its center: a vignette is
   radially symmetric about the image center.*
5. `50_postprocess.ssf.tmpl` — stat + bgnoise of the linear stack (the
   before/after record), then background extraction (`@SUBSKY@`) →
   `denoise -vst` → **unlinked** `autostretch -2.8 0.15` (per-channel bg
   equalization kills global casts; `-linked` preserves them) → `satu 0.3`
   → `preview_<set>_<timestamp>.jpg`. **No rmgreen**: SCNR on a sky that
   is not green-dominant dyes the whole image magenta/red. Iterate
   standalone: `scripts/run_post.sh <session> [set] [subsky-degree]`
   (denoise costs ~3 min — comment it out when iterating on gradients).

Diagnostics: `diag_flat.ssf` (stretched master-flat check → JPEG); stack stats
print in every post run. Record stack median + bgnoise **before and after every
change** and compare noise/median — output normalization rescales levels when
the reference frame changes, so raw bgnoise numbers across runs are not
comparable.

Masters live in `<session>/work/masters/` and are **rebuilt automatically**
when any source DNG is newer than the master (drop in re-shot frames and just
re-run). Big FITS results are overwritten per set (`results/stack_<set>.fit`);
small timestamped JPEG previews accumulate for run-to-run comparison.

## Per-stage expectations (inspection contract)

Every pipeline run auto-produces `results/inspect_<set>_<timestamp>/`
(index.html + one JPEG, radial-profile PNG and metric block per stage) via
`scripts/inspect_stage.py`. All stage JPEGs use the **same** rendering — MTF
autostretch, linked, shadow clip median−2.8·σ, background target 0.25,
data-driven anchors — so stages are visually comparable. The numeric bounds
below are mirrored in `EXPECTATIONS` inside `inspect_stage.py`; violations
mark the stage **WARN** in the report (inspection never aborts a run — the
hard gate stays `bg_qa.py` on the final preview). Values calibrated on
set-03 (21×25s ISO200 37/38mm, self-flat path), 2026-07-06.

| stage | output SHOULD look like | verifying metric → PASS bound |
|---|---|---|
| calibrated frame (`pp_light_*`) | sky with vignette bowl + moonglow tilt, stars to the corners, offset gone, hot px mapped out | bg median (16-bit units) 100–1500 (measured 115); clipped px < 0.5%; stars ≥ 150 (measured ~5000); no channel median at 0 |
| self-flat median (`selfflat_med`) | smooth V×S surface: bowl + tilt only — drifting stars self-rejected, MW smeared away | stars ≤ 5% of calibrated-frame count (star detector uses a 0.4%-of-local-bg prominence floor — pure σ thresholds promote glow mottles to "stars" on smooth surfaces); radial corner/center 0.35–0.75; `selfflat.py` grid rejection < 25% (aborts above) |
| glow-subtracted frame (`bkg_pp_light_*`, after rechroma) | tilt gone, bowl intact, per-channel medians at the model-consistent targets C_c·median(V) | plane tilt is INFO-only (the bowl's truncation reads as ~9–13% "tilt" in any plane fit — divided-stage flatness is the real check); G median within ±10% of calibrated |
| self-flat gain (`selfflat_gain`) | smooth gray radial falloff, 1.0 center → ~0.54 corner, **no rings** | monotone non-increasing (exact — THE ring guard); corner 0.45–0.65; channel spread 0 (gray by construction); detrended radial P2V is INFO-only (detrend lag on the knee reads ~2.6% on a ring-free monotone curve) |
| divided frame (`pp_bkg_pp_light_*`) | flat sky edge-to-edge, corner stars re-brightened with the sky; noise rises ~1/V toward corners | radial P2V (r ≤ 0.85) ≤ 20% of median full-range (the recorded "±9%" = 18% full-range); rim zone r > 0.9 deviation ≤ 25% (open defect: extrapolation zone) |
| registration (sweep) | best reference registers (nearly) all frames | registered/total ≥ 0.9 (measured 21/21 @ ref 12; 2-pass auto-pick was 18/21) |
| linear stack (`stack_<set>`) | flat bg, MW visible under stretch, no rejection artifacts, rim slightly thinner coverage | bgnoise/median (G) 1.2–1.7% (measured 1.46%); radial P2V (r ≤ 0.85) ≤ 20% full-range (glow+MW still present — absolute flatness is judged after subsky); stars ≥ 300; median 150–1500 |
| post: subsky | glow/gradient removed, background centered near zero offset from median, MW untouched | block-map spread (P95−P5 of block medians) ≤ 4× bgnoise; radial P2V not worse than input |
| post: denoise | grain −35…−45%, faint stars survive | bgnoise ratio 0.5–0.75 of input; star count Δ ≥ −10%; radial-profile shift < 1.0 8-bit count (KNOWN FAIL — out of chain until placement passes) |
| post: autostretch | neutral dark sky at the target bg, casts equalized, stars bright not gray | bg median (8-bit) within ±6 of target×255; bg |R−G|,|B−G| ≤ 3; top-100 star peak median ≥ 200/255 (below = "washed out") |
| post: satu (if used) | color saturation up in stars/MW, background chroma unchanged | bg color dev change ≤ 1 count; star peak median must not drop |
| final preview JPEG | black sky, structured MW, sharp bright stars, no rings, full frame | `bg_qa.py` gate PASS (blocks P95/P50 ≤ 1.6, color ≤ 7; rings lum ≤ 4, chroma ≤ 4) + star metrics reported (count, FWHM-eq, top-100 peak, halo ratio) |

Star metrics (count/FWHM/peak/halo) come from a numpy detector in
`inspect_stage.py` (local maxima > bg+8σ, equivalent-area FWHM, halo =
flux(3–8px)/flux(<3px)) — consistent across linear FITS and 8-bit JPEG, so
"washed out stars" is now a measured quantity, not an impression.

## Iteration log (session 07-02-26)

| preview | variant | verdict |
|---|---|---|
| `preview_20260705_131357` | v1: no gradient removal | strong moonlit gradient, edges bright |
| `preview_20260705_131715` | subsky RBF s=20 tol=0.5 | **worse** — overfit, dark hole in sky center |
| `preview_20260705_131832` | subsky poly degree 1 | keeper — gentle, no artifacts |
| `preview_20260705_132244` | same, full-pipeline validation run | = (old-cal baseline: 30/32, G noise/median 1.49%) |
| `preview_20260706_003151` | **re-shot cals**, 1-pass reg | calibration clean (corners/color/center ✓) but 26/32 — 4 more drifted tail frames dropped; G 1.58% |
| `preview_20260706_003913` | + 2-pass registration | 30/32 (auto-ref → frame 32); G 1.42% — beats old-cal |
| `preview_20260706_004620` | + `setfindstar -sigma=0.5` | **keeper** — 31/32 (ref → 18), G 1.40%, stars tight, no artifacts |
| `preview_set-03_20260706_011304` | set-03 first run (no flat, subsky 1) | 20/21; planar subsky can't fit vignette bowl, corners near clip |
| `preview_set-03_20260706_011346` | set-03 subsky 2 | **keeper** — flattest practical sky (σ 77.6 vs 87.6), Milky Way visible; mottling is real sky (clouds/moonglow), not artifacts |
| `preview_set-03_deconv` | + makepsf stars + RL 20 iters | no de-trailing benefit — rejected |
| `preview_set-03_20260706_014933` | self-flat v1 (single free-form gain) + subsky 1 | background flat to ±5% and 21/21 registered, **but looked wrong** — glow baked into the gain (peak off-center), regional brightness distorted. Deleted with the old-data purge |
| `preview_set-03_20260706_020421` | **self-flat v2: radial V(r) only** + subsky 1 | **keeper** — natural look, vignette gone, glow left for subsky, MW intact |
| `preview_set-03_20260706_020759` | same, subsky 2 | marginally flatter mid-field, MW intact — either is fine |
| `preview_set-03-38mm_*` | 13×38mm-only experiment | rejected (see set-03 table) — artifacts removed |
| `preview_set-03_denoised` | + `denoise -vst` | bgnoise −41%, grain visibly reduced, faint stars kept — good final-polish option |
| stretch ladder (removed) | 21-frame stack, `autostretch -linked -2.8` at bg 0.10 / 0.15 ± denoise/rmgreen/satu | **the "smokey" look was the stretch**: default autostretch targets bg 0.25 unlinked → gray veil; 0.10 overshoots dark and crushes the faint MW. Keeper: **0.15 linked + denoise + rmgreen + satu 0.3**, baked into `50_postprocess.ssf.tmpl` |
| ringed preview (removed) | radial-POLY self-flat + full pipeline | **concentric rings** (user spotted): preview radial profile oscillated 54→31→54→6 because the r²/r⁴/r⁶ V(r) had a +4% hump and corner upturn — division printed inverse rings |
| isotonic preview (removed) | **isotonic self-flat** + ref sweep (21/21) + subsky 2 + stretch | rings gone (profile 33→41→51→45) but periphery lifted +55% — the additive glow amplified by the corner division (glow/V) |
| seqsubsky orderings (removed) | per-frame `seqsubsky 1` BEFORE division | flattest field yet (profile 43→38→36, ±9%). Two sub-lessons: V must be estimated from the UNTOUCHED median (glow-subtracted frames break the pedestal/bowl ratio → per-channel V diverged 0.61/0.37/0.47 → tint); per-channel division tints corners anyway (glow contaminates per-channel profiles) → **gray V** |
| gray-V + subsky-2 render (removed) | + gray V + post subsky 2 (chroma cleanup) | flat luminance ±9%, corner red largely neutralized — **but globally "dyed red"** (user): `rmgreen` clamps G on a sky that is not green-dominant → magenta shift everywhere, `-linked` stretch preserves it, `satu` amplifies it |
| unlinked + satu render (removed) | unlinked autostretch, satu 0.3, no rmgreen | still rejected by user ("dyed red/brown, not black"). Root cause of the whole arc: judging by hand-picked patches — whole-frame QA scored it 2.69 luminance spread / 38 color dev = objectively awful |
| RBF ladder (removed) | subsky -rbf, tolerance/samples/smooth swept under whole-frame QA | tolerance=1 rejected the horizon glow from its own background model (that is WHY the bottom band survived everything); tol=3 + samples=30 + smooth=0.15 + 150px edge crop + no satu → QA 1.13 / 7 |
| `preview_set-03_20260706_104902` | **APPROVED BASELINE** — full recipe in `50_postprocess.ssf.tmpl` | user-approved neutral dark sky, MW intact; QA gate now runs in every `run_post`. Known residual (next audit target): faint concentric chroma/lum rings, measured radial P2V lum 4.9 / R-G 6.8 counts, worst at the rim (r≈0.86–0.96) |
| refine-gain / radial-polish (dead end, 3× confirmed) | measure gain residual from the stack, fold back, re-divide | **impossible on this data**: the sky's own per-channel structure (MW band, glow, clouds; 2–8%) exceeds the ~2% gain residual being measured. Median AND 30th-percentile azimuthal statistics both returned opposite-sign per-channel "residuals" (the sky, not the lens). Never scale the stack in place either |
| `candidate_v4` (unapproved) | GraXpert BGE → subsky 2 → autostretch -1.5 0.07 unlinked → satu 0.2 → crop 250 | QA PASS (blocks 1.31, rings 3.9/2.3/2.8), bg truly black (6.7%, R=G=B=17); user verdict: rings/vignette/black much better BUT **stars washed out + smokey, crop must go**. Also: denoise shifts the radial profile ~1 count (fails the gate margin) wherever placed — currently out of the chain |

**Process reset (user directive 2026-07-06):** no more multi-knob iterations.
Single-variable ladders only (test X at 0.3/0.5/0.7-style brackets), hypothesis
stated before each run, per-stage inspection artifacts auto-generated so every
pipeline stage can be judged — not just the final preview. Handoff prompt for
the implementation session: `NEXT_SESSION_PROMPT.md`.

**Inspection + experiment tooling (2026-07-06, this session):**
- `scripts/astrometrics.py` — shared measurement lib (minimal FITS reader
  with display-orientation flip, gradient-immune diff-MAD bgnoise, radial
  lum+chroma profiles, numpy star detector: count / FWHM-eq / elongation /
  halo ratio / top-100 & mid-tier(100–500) peak / saturated-star fraction).
  Star "washed out" is now measurable: candidate_v4 saturates only 57% of
  its measured stars (mid-tier peak 249/255) vs 100% (254/255) for the
  approved-baseline render — matches the user's verdict exactly.
- `scripts/inspect_stage.py` — per-stage inspection (consistent linked MTF
  autostretch on every stage JPEG: shadow σ=-2.8, bg target 0.25), metrics +
  PASS/WARN vs the expectations table, browsable per-run report
  (`results/inspect_<set>_<ts>/index.html`); wired into `run_pipeline.sh` +
  `run_post.sh` (post ops save intermediates via `save` in the template,
  measured then deleted). Inspection warns, never aborts; `bg_qa.py`
  (refactored importable, thresholds byte-identical) stays the hard gate.
- `scripts/experiment.py` — single-variable ladder harness: one `--param`,
  bracketed `--values` (control auto-included, bracketing enforced),
  mandatory `--hypothesis`; reruns only the affected ops from the pinned
  stack (shared prefix computed once, GraXpert cached), emits per-value
  JPEGs + QA/star metric table + side-by-side full/star-field/corner strips
  into `results/exp_*/`, then stops for user judgment. Chains: `baseline`
  (approved recipe) and `candidate` (candidate_v4 recipe).
- Measured while validating: JPEG quality 85→98 only jitters ring P2V by
  ~±0.4 count and star sat% by a few points — that is the metric noise
  floor, not a star-quality lever.
- **Current-stack drift finding:** re-running the approved recipe on the
  stack rebuilt at 11:21 (post refine-gain dead end) gives QA FAIL rings
  lum 7.2 / R-G 4.9 — worse than the 104902 approved render (4.9/6.8, gate
  added later). The stack behind the approved preview no longer exists;
  the instrumented full run regenerates the canonical stack + per-stage
  report, and all experiments pin against that. Fresh canonical run
  (`inspect_set-03_20260706_123508`): 21/21 @ ref 13 (sweep: 10→15, 11→18,
  12→20, 13→21 — reference-dependence confirmed yet again), stack noise/med
  1.57%, recipe rerun QA FAIL rings lum 4.7 / R-G 6.7 ≈ the approved-era
  values. Canonical current state to beat.

**RIM/RING ROOT CAUSE — measured, 2026-07-06 (from the per-stage radial
chroma profiles in `inspect_set-03_20260706_123508`).** R−G in 16-bit
counts at r=0.3 → r=0.98, per stage: calibrated −63→−32 (natural
G-dominant sky, multiplicative bowl, ratios consistent) | seqsubsky output
−11→**+20** (SIGN FLIP BORN HERE: per-channel planar fit + per-channel
level restoration re-centers each channel on its own median; G's bowl is
~65 counts deep vs R's ~34, so after re-centering the rim goes R−G
positive) | divided −11→**+37** (gray-V division amplifies the rim ×1.9 —
it preserves ratios but scales the absolute imbalance) | stack −27→**+148**
(addscale normalization + rgb_equal scale R up globally ≈4×) | post-subsky
~0→+4.5 (RBF cleans everything below r≈0.93; the extrapolation zone keeps
the residual) | post-stretch ~0→**+13** at r=0.98 (the QA R−G ring).
Luminance has a second, independent component: the divided frame keeps a
real **−16% G falloff at r>0.93** (V(r) under-corrects the outer 2–4% of
radius and/or glow curvature is concentrated there); after RBF + stretch it
renders as the bright-ring-at-0.93 / dark-edge-at-0.98 signature (G 30.8 →
35.0 → 15.8). The 150–250px crop has been hiding exactly these two rims.
Fix experiments must attack (C) the seqsubsky chroma re-centering and (L)
the V(r)/glow rim under-correction separately.

**Experiment campaign (a) star quality — RESOLVED 2026-07-06 (ladders in
`results/exp_set-03_*`; all on the candidate chain, one knob each, fresh
canonical stack; star metrics re-anchored with the current prominence-floor
detector: candidate_v4 = sat 7%/mid 249, approved baseline = 12%/254):**

| exp | knob | result |
|---|---|---|
| A1 `stretch_target` | 0.05 / 0.07 / 0.12 | **THE washout driver**: sat 3→6→13%, mid-peak 239→247→255. 0.12 restores baseline-level stars exactly (13%/255 vs baseline 12/254). BUT rings/blocks fail at 0.12 (4.3 / \|R−G\| 13): the dark 0.07 render was *hiding* the rim, not fixing it |
| A2 `stretch_linked` | linked / unlinked | linked does NOT recover stars (4%/242) and FAILS QA blocks (\|R−G\| 8 — preserves the global cast). Unlinked stays |
| A3 `satu` | off / 0.2 / 0.3 | no star-core effect (sat 5–6%, mid 245–247), no QA effect. Not a washout driver |
| A4 `graxpert` | off / on | off: QA FAIL (blocks 1.88, \|R−G\| 15, ring RG 4.2) AND worse stars (mid 207, sat 1%) — GraXpert is the load-bearing flattener of the candidate chain and *helps* stars via better stretch anchoring. Stays |
| smoke `jpgq` | 85 / 92 / 98 | ring P2V jitter ±0.4 count, sat ±few % — measurement noise floor, not a lever |

**Verdict (a): stars washed out = stretch target 0.07.** Fix = target
~0.12 (chain `candidate_bright` in experiment.py) — blocked solely by the
rim. → resolves into (b).

**Experiment campaign (b) rim, crop ladders (B1 dark / B2 bright chain):**
candidate@0.07: crop 250 PASS / 150 FAIL (\|R−G\| 9) / 0 FAIL (\|R−G\| 12,
rings 5.3/6.6). candidate_bright@0.12: FAILS at every margin (250: \|R−G\|
13; 0: \|R−G\| 19, rings 8.0/9.6). Chroma blocks+rings dominate at full
frame in both — the rim chroma born at seqsubsky must be fixed in the
pipeline, not in post.

**B3 — CHROMA RE-CENTERING FIX (scripts/rechroma.py), 2026-07-06, run
`inspect_set-03_20260706_130456`:** after seqsubsky, each frame's R/B
medians are shifted by a constant back to their calibrated offsets
relative to G (R ≈ −53, B ≈ −17 counts/frame; G untouched; constants
cannot create spatial structure). Measured rim chroma R−G @ r=0.98:
subsky frame +20 → **−33**, divided +37 → **−60 with the radial spread
collapsed 48 → 5 counts**, stack +148 → **−15 (10×)**. B−G similar.
The magenta rim is gone at the stack level. Residual final-image failure
(baseline RBF render: rings lum 5.7 / R−G 6.6 / B−G 4.4) is now dominated
by (L): the real **G luminance falloff −13…−16% at r>0.93** present in
every divided frame (V(r) tail resolution + glow curvature residual —
NOT fixed by rechroma, expected) plus the background model's own edge
extrapolation error (±3–4 counts chroma at the edge after stretch).
Pre-fix stack preserved as `results/stack_set-03_prechroma.fit`.
G-based inspection metrics are bit-identical pre/post fix (the fix moves
only R/B) — a good null check that nothing else changed.
(L) fix candidates, one at a time: V(r) rim resolution (NBINS 24→48 +
slope-extrapolated tail beyond the last bin center — the flat tail +
0.958–1.0 pooling under-corrects corners by est. ~10 of the 16%), then
estimator edge behavior (denser RBF samples / GraXpert), then a minimal
crop only if a hard floor remains.

**(L) ROOT CAUSE FOUND ANALYTICALLY before trying the above (2026-07-06,
from the 130456 report's stored profiles):** S(r) = median/V_fit is flat
±1% to r=0.93 → the fitted V tracks the *median* fine; the −16% appears
only when dividing the glow-SUBTRACTED frames. The additive glow level
L ≈ 25 counts inside the median flattens the multiplicative fit:
V_fit = (V·S̄+L)/(S̄+L) = 0.537 measured, so true V = (V_fit·(S̄+L)−L)/S̄
≈ 0.43 (S̄≈105). Dividing frames whose additive part subsky already
removed by the too-shallow V_fit under-corrects the bowl by
(1−V)·L/(V·S̄+L) ≈ 16% at the rim — the measured value, to the count.
Also explains why the remaining chroma ring tracks G(r): rgb_equal turns
any luminance rim into a chroma rim (R−G ≈ (k−1)·G(r)).
**Experiment L1 (hypothesis, pre-registered):** change selfflat.py to the
additive-glow factorization `median = V(r)·C + A(planar)` (V isotonic
non-increasing as before, A planar so it cannot absorb falloff, C scalar
sky level; per-channel C_c exported) and make rechroma.py's target
model-consistent: shift each bkg channel to median = C_c·median(V_gray)
so the frames' additive residual is ~zero and division returns flat S̄_c
per channel. Expected: divided-frame rim_dev −16% → ~0, gain corner
~0.43, stack G rim flat, final ring lum ≤ 4 at small/no crop; chroma
follows luminance via rgb_equal. If divided rim_dev does NOT collapse,
the additive model is wrong — revert both and write the dead end.

**L1 result (run `inspect_set-03_20260706_132051`): half right —
direction correct, magnitude overshoots.** Gain corner 0.472 (predicted
0.43); divided-frame flatness HALVED (p2v 0.136→0.060, rim_dev
0.175→0.090) and chroma flat (R−G −68…−75 across r, spread 8 counts);
the −16% dark rim is gone — but replaced by **+7% bright rim** (stack
+10%), which the stretch blows into ring lum 18.3 = QA FAIL worse.
Cause: siril's per-frame plane subtraction removes the planar COMPONENT
of the vignetted bowl too, so the frames' actual radial falloff is
shallower than the true lens V — the "right" V for division lies between
the multiplicative fit (0.537: −16%) and the additive fit (0.472: +7%),
and no a-priori model of siril's internals will nail it.
*Sub-lesson: first L1 attempt exported float-unit rechroma targets that
would have zeroed every background — killed mid-run; rechroma now has a
75%-of-level sanity guard and explicit 16-bit units.*

**Experiment L2 (hypothesis, pre-registered): close the loop empirically —
divide by the measured shape of the actual frames.** After rechroma,
median-stack the glow-subtracted frames themselves (`selfflat_med2`,
nonorm — levels already aligned) and fit V2 from THAT (same isotonic gray
fit; its A term should come out ≈0 since the planes are subtracted).
Division by V2 flattens the divided median BY CONSTRUCTION. The old
"never estimate V from glow-subtracted frames" dead end does not apply:
that failure was siril's per-channel level restoration corrupting
per-channel V ratios (0.61/0.37/0.47), which rechroma now normalizes
before the estimate — and V stays gray regardless. Expected: V2 corner
between 0.47 and 0.54, per-channel corner spread ≤ 0.05 (else the dead
end IS back → abort), divided rim_dev ≤ 3%, stack rim flat, final ring
lum ≤ 4 before crop enters the discussion.

**FULL-FRAME QA PASS — candidate_v5 (2026-07-06,
`results/candidate_v5_fullframe.jpg`, UNAPPROVED pending user judgment).**
On the L2 stack (rechroma + V2), chain `fullframe_v5` = GraXpert BGE →
`subsky 1` → `autostretch (unlinked) -1.5 0.07` → `satu 0.2` → **no crop**
→ jpg 92: QA blocks 1.35 / colors ≤ 6 / rings 3.7 / 3.4 / 3.4 at the full
6064×4040. Stars: mid-tier peak 250, sat 7% (≥ candidate_v4's 249/7 —
same dark-render tier). Found via the subsky-degree ladder
(`exp_set-03_subsky_20260706_133842`): after GraXpert, post-subsky degree
**1** passes while 2/3 overfit per channel and re-create the color
failure (|B−G| 6 / 8 / 9 for degree 1/2/3) — higher degree HURTS.
**The remaining trade is render brightness vs the rim residual**
(`exp_set-03_stretch_target_20260706_133958`): target 0.07 PASS / sat 7%;
0.09 FAIL rings 4.3 (sat 11%); 0.12 FAIL rings 5.4 (sat 17% = baseline
stars). The +2% linear rim (post-estimator extrapolation zone) caps how
bright the full frame can be rendered; brighter needs either the crop
back or a better rim model. USER JUDGMENT NEEDED: approve candidate_v5
(full frame, dark) vs bright-with-crop vs keep hunting the last 2%.

**Experiments (c) denoise — CLOSED (`exp_set-03_denoise_20260706_134059`,
fullframe_v5 chain):** `-vst` before stretch FAIL (rings 5.1 — the known
~1-count radial shift, amplified by the stretch); after stretch NEAR MISS
(ring R−G 4.2 vs gate 4.0, blocks fine); off PASS. Denoise stays OUT of
the chain. Only untested option left: post-stretch `-vst` with a
modulation blend (`-mod≈0.5`) — expected ~halved ring effect; run as its
own single-knob ladder if grain bothers the user in candidate_v5.

**L2 result (run `inspect_set-03_20260706_132833`): upstream now clean;
the last standing defect is the POST estimator's rim extrapolation ×
stretch amplification.** V2 corner 0.489 (between 0.472/0.537 exactly as
predicted), per-channel spread 0.036 ✓ no dead-end recurrence. Divided
p2v 0.052 / rim_dev 0.067 (from 0.136/0.175 at session start); chroma
flat (R−G spread ≤ 7 counts pre-rgb_equal). The residue: a NON-MONOTONE
+5% bump at r=0.93 in the divided frames = the per-frame glow curvature
that `seqsubsky 1` (planar) cannot remove and a monotone V must not
absorb (a monotone gain cannot remove a bump — that IS the anti-ring
guard working). Post-RBF flattens it to **+2.3% linear at the rim** —
and the MTF stretch amplifies deviations at the background point by
~2.5 8-bit counts per 1% linear → ring lum 17. THE BAR, made explicit:
**rim-vs-mid flatness after the post background model must be ≤ ~1.5%
linear for ring ≤ 4.** Both failed models bracket truth; further V
tinkering is pointless — the remaining battle is the background
estimator's behavior in the outer zone (RBF extrapolates; GraXpert may
model it), or a minimal crop of the r>0.93 zone (≈ the existing 250px —
which is exactly why that crop "worked").

Registration history: with a sequence-start reference (1-pass default), the
fixed-tripod field drift strands the tail frames — 2/32 dropped with old cals,
6/32 after recalibration (borderline frames flipped when calibration changed
the detected-star sets). Two-pass registration picks a better reference and
recovers them; denser detection (`setfindstar -sigma=0.5`: ~870 vs ~370
stars/frame) moved it to 31/32. Frame 2 still fails star matching — not worth
chasing (+1 frame ≈ 1.6% noise). Per-frame FWHM spread is only ~6%
(uniform conditions), so wFWHM weighting/filtering would be a no-op here.

The remaining bright-bottom gradient is real sky (waning gibbous moon + horizon
glow); stronger removal needs treeline-aware masking (GraXpert) — future work.
The halos in the sky around the treeline are inherent to star-aligned stacking
of a landscape: treeline pixels flip between tree and sky across drifting
frames and rejection only partially cleans the transition. Sky-only quality is
unaffected away from the trees; a dedicated foreground blend is the real fix.

## set-03 (same night, second composition — nearly pure sky, Big Dipper area)

| what | value |
|---|---|
| frames | 21 × 25s ISO 200 f/4, Jul 3 00:47–00:57 |
| focal | **mixed: 8 × 37mm + 13 × 38mm** — single step at a ~57s mid-set pause (frame 8→9, camera touched); EXIF is integer-mm so true change is ≥1 reporting step, ≤ 2.7% scale |
| calibration | darks 20s (warn: bias+hot-pixel-map mode), **no flat** (24mm flats ≠ 37/38mm — preflight auto-routes to SELF-FLAT path) |
| self-flat (final) | V(r) monotone isotonic, **gray** (channel-mean): 1.00 → 0.91 @ r=0.5 → 0.537 @ corner; glow tilt 27–31%/half-frame measured on the untouched median, subtracted per frame by `seqsubsky 1` before division. Grid outliers 3–4% |
| registration | **21/21 via reference sweep** (ref 12; the 2-pass auto-reference stranded 3 frames — trailed stars make matching reference-dependent). Mixed focal absorbed by homography — corner crops show no scale smear |
| stack | `stack_set-03.fit` 21 frames, G bgnoise 3.33 vs 3.57 @ 18 frames — the full √(21/18) recovered |
| gradient | vignette divided out → subsky handles only the glow; degree 1 auto (degree 2 marginally flatter, both keep the MW) |
| 38mm-only experiment | **rejected**: 11/13 registered (same ~85% fraction as the full set — failures are per-frame matching luck, not focal mix), G noise/median 1.324% = the full √(18/11) penalty for dropping 7 frames. Keep all 21 |
| denoise | `denoise -vst` (NL-Bayes) on the post-subsky linear: bgnoise **−41%** (ch0 5.16→3.05), faint stars preserved, no artifacts. Post-polish option, not in the default pipeline — it can't add signal and aggressive use eats faint MW |
| stars | uniformly elongated: **in-exposure trailing** (25s at 37–38mm ≈ 2× rule-of-500 ≈ 13s) — the crispness ceiling; NOT misregistration (no doubling) |
| deconv | tried `makepsf stars` + `rl -iters=20` on the linear: no visible de-trailing (fitted PSF ≈ symmetric), PSF fit unstable on ≈0 background — rejected (`preview_set-03_deconv.jpg`) |

Verdict: sky quality is registration/stack-limited no more — it's exposure-
limited (trailing + ISO 200). For crisp stars at ~38mm: ≤13s subs, ISO 800,
and more of them.

## Master flat screen-pixel check (user spotted grid in raw flats)

Confirmed by per-CFA-plane FFT (Bayer mosaic excluded by construction):
coherent horizontal banding, periods 4–12 sensor px, peaks 88–166× above the
spectrum floor, **~0.3% RMS** (vs ~0.1–0.15% pure shot-noise floor for a
100-frame master). Impact on stacked lights: negligible — 0.3% of a ~57 ADU
sky background ≈ 0.2 ADU/frame, buried under ~4 ADU frame noise and further
decorrelated by drift-dither. The 24mm results stand. Fix at acquisition:
cloth/t-shirt diffuser over the lens + more screen distance.

## Star separation arc (2026-07-06, session 3 — user direction)

User verdict on candidate_v5: **MW dust/glow missing (too dark) and the
dark render may just be hiding the chroma/ring issue** — correct on both:
the measured target ladder (0.07 PASS / 0.09 FAIL 4.3 / 0.12 FAIL 5.4)
shows the rim residual is hidden, not gone, and the same 0.07 target is
what crushes the MW.

**Standard DSO workflow vs ours:** calibrate → register → stack →
linear gradient removal (DBE/GraXpert) → photometric color calibration
(SPCC/PCC) → deconvolution (BlurX) → linear noise reduction (NoiseX) →
**star separation (StarNet++/StarXTerminator)** → stretch starless HARD
(GHS/arcsinh: nebulosity without star bloat) + stars gently (cores/color
protected, faint tail often culled or reduced) → screen/PixelMath
recombine. Ours matches through gradient removal; it diverges at: color
cal = `rgb_equal` only (PCC needs plate solve — future); decon = dead end
here (trailing, PSF unstable on ≈0 bg); denoise = out (gate); and above
all NO star separation — one global stretch had to serve stars AND
nebulosity, which is exactly the trade-off that failed (bright = rim +
star bloat, dark = no MW). Star separation removes that coupling AND
gives the background model star-free data (better rim behavior).
StarNet++ has no aarch64 build; GraXpert 3.2 has no star removal →
`scripts/starsep.py` does classic mask+inpaint (component filter: peak
prominence ≥6σ + compact area, bright-core exception; branch excluded;
multi-scale seed + Jacobi diffusion inpaint + matched noise; catalog
saved for flux-percentile culling). Measured on the V2 stack: 23k stars
masked (13.7% of frame), starless keeps MW band + dark lanes intact (no
holes/halos), stars layer leaks no background. Faint 4–6σ stars remain
in the starless layer as stipple (below the prominence cut) — the
denoise-on-starless experiment is the intended cleaner.
`scripts/starcomb.py` = split processing (starless: GraXpert BGE →
subsky 1 → optional denoise → unlinked stretch; stars: gray MTF anchored
to top-500 amplitude median → screen combine) + single-knob ladder mode
with the same discipline (hypothesis, control value, metric table,
strips, STOP). It also QA-grades the STARLESS render alone — the honest
rim check no dark render can hide behind.

**Pre-registered hypotheses:**
- S2 `starless_target` 0.07/0.12/0.15: with stars out and gx modeling a
  star-free background, the rim should stay ≤4 rings at brighter targets
  (the star-ful chain failed at 0.09); MW contrast should rise with
  target. If starless-only rings still blow up at 0.12, the rim is in
  the data, not the estimator's star handling.
- S3 `starless_denoise` off/vst: denoise's gate failure was measured on
  star-ful frames; on smooth starless data VST NL-Bayes should not
  create radial structure → rings stay, stipple + grain drop.
- S4 `cull_pct` 0/50/75: culling the faint half of the catalog cleans
  the field without touching bright-star impact; count drops, mid-peak
  unchanged; user judges the look.

**S2 result: hypothesis REFUTED — the rim is in the DATA.** Starless-only
rings scale with render brightness exactly like the star-ful chain
(0.07→3.9 PASS, 0.12→5.0, 0.15→6.3+). Star handling was never the
estimator's rim problem. ALSO exposed: **GraXpert BGE erases the MW on
starless input** — measured linear MW contrast +38.1 counts before gx →
+0.4 after (on star-ful input it left ~+4 through to candidate_v5). With
stars gone, the AI reads diffuse nebulosity as background. bge on
starless = MW killer; and the stars branch at anchor 0.85 renders dimmer
(mid 225) than the star-ful chain (250) — anchor needs its own ladder.
**S5 border-anchored membrane: REFUTED** — a border-only thin-plate
cannot represent the glow's interior curvature (over-subtracts mid-frame:
MW contrast −19) and border-sample scatter wiggles the rim (ring L 8.6).
**S6 lower-envelope grid RBF: REFUTED for rings** — keeps some MW (+4 vs
gx's +1) but ring L 9.4 (rejection creates local extrapolation pockets;
the surface still tracks the broad band partially).

**Conclusion + L3 (pre-registered): fix the +2% at the SOURCE.** The
divided frames carry a non-monotone +5% bump at r≈0.93 = per-frame glow
CURVATURE that planar `seqsubsky 1` leaves and monotone V must not
absorb. Change `40a` per-frame `seqsubsky 1 → 2` (curvature removed in
sensor coords while additive-clean). Self-consistent with the L2
architecture: whatever bowl share the quadratic absorbs just makes V2
shallower and rechroma targets adapt (C·med(V)). A smooth quadratic
cannot print rings (no oscillation). Expect: divided-frame bump at 0.93
≈ gone, stack rim ≤ ~1%, fullframe chain rings ≤ 4 at target 0.12 (the
star-bright render). Risks pre-registered: per-frame quadratic may bend
the MW band per frame — gate: stack MW contrast must stay ≈ +38 linear;
V2 corner will change (quadratic absorbs bowl share) — that is expected,
not a failure.

**L3 result: REFUTED — the worst-case risk materialized.** The rim goal
was achieved perfectly (divided frames flat to 0.975 rim/mid, the 0.93
bump GONE, stack chroma flat +3) **and the Milky Way was erased: stack
MW contrast +38 → +0.0 linear.** At 37mm the MW band is frame-scale
curvature — indistinguishable from glow curvature to ANY unmasked smooth
fit. DEAD END for unmasked per-frame curvature removal; reverted to
`seqsubsky 1`, stack regenerated (MW +39.7 ✓, preserved as
`stack_set-03_L2.fit`). *Meta-lesson: rim curvature and MW are the same
spatial frequency; only geometric (band-mask) separation can
discriminate.*

**S7 'banded' (geometric corridor exclusion, pre-registered above):
REFUTED** — corridor-edge samples sit in band skirts, the bridging
surface runs high (MW −9 after subtract) and the thin-plate still
wiggles the rim (ring L 9.9). All three hand-rolled RBF surfaces
(border/envelope/banded) land at ring 8–10 vs gx's 5–6: block-sample
scatter (±3–5 counts) through one global smoothing parameter cannot be
simultaneously flexible (glow blob), stiff (rim) and null (band).

**S8 'bge_first + mw_boost' (order fixed to the standard one: GraXpert
BGE + subsky 1 on the STAR-FUL stack — measured MW-safe there — then
separation, then band-corridor midtone lift on the starless layer):**
k=0 regression ✓ QA rings 3.0–4.4 (the sep+recombine roundtrip itself
costs ~+0.7 ring vs plain v5), MW +4; k=0.6 → rings 6.1, MW +5; k=1.2 →
rings 6.9, blocks 1.72, MW +6. **The gate reads an intentionally lifted
MW as background nonuniformity** — the corridor crosses radial bins
asymmetrically (ring metric) and brightens blocks (block metric).

**DECISION MATRIX (2026-07-06, needs the user — every route measured):**
1. **Full frame + gate intact + dark:** candidate_v5 stands (QA PASS,
   MW subtle +4). The stars can be brightened independently via the
   separation (stars anchor 0.85→~0.97) without touching the gate.
2. **Bright MW/stars:** mathematically incompatible with the CURRENT
   gate on THIS data at ANY crop — the rim residual and the lifted MW
   both read as rings/blocks (measured at crop 0/150/250: all fail at
   target ≥0.09). Not an engineering gap anymore; a gate-vs-goal
   conflict.
3. **Gate evolution (user's call only):** treat the MEASURED MW corridor
   as signal — mask it from the block map and compute ring metrics on
   the corridor-complement (exactly how the branch is already masked as
   known-non-sky). Thresholds stay untouched elsewhere. Then mw_boost ≈
   0.6–1.2 + target 0.07 gives a full-frame render with visible MW dust
   whose SKY portion still passes the strict gate. This is a scope
   change of the gate, not a loosening of its thresholds — but it is
   the user's decision by the project's own rules.
4. Next acquisition remains the physical fix (≤13s subs, ISO 800, real
   flats): more MW signal per count of glow → less boost needed.

## Iteration ideas (not yet tried)

- Registration with distortion handling (24mm wide field, corner stars)
- `-filter-wfwhm` / `-weight_from_wfwhm`: no-op for THIS session (FWHM spread
  ~6%) — revisit when a session has variable seeing/clouds/wind
- Drizzle (probably not: undersampled? no — 24mm @ 5.9µm is heavily oversampled
  spatially, skip)
- GraXpert background extraction (installed at ~/.local/bin/graxpert) for
  treeline-aware gradient removal — `subsky 1` is the in-Siril ceiling
- Photometric color calibration (`pcc`) vs `rgb_equal` (needs plate solve +
  catalog access)
- Denoising after stretch; starnet/star recomposition

## Re-shoot outcome (2026-07-05, all three calibration sets replaced)

- Darks now match lights (20s ISO 200, 40 frames): preflight warning gone,
  full dark subtraction valid, hot pixels (to 4246 ADU) properly mapped.
  Z6III mean dark current at 20s ≈ 0, so the win is the hot-pixel map.
- Flats brighter (27% peak vs 20%) but still below the ~50% goal at 1/160s —
  the MacBook-screen brightness needed ~1/50s. 100 frames compensate.
- Biases re-shot too (98 @ 1/160s — same shutter as flats = exact flat-darks).
- All three masters rebuilt automatically by the freshness check; no script
  changes were needed for the data swap itself.
- **Calibration validated by before/after compare**: no new artifacts (corners,
  color, banding, hot-pixel residue all clean); per-signal background noise
  unchanged at equal frame count. But the recalibrated frames initially
  registered *worse* (26/32 vs 30/32) — borderline drifted tail frames flipped
  to failing with a sequence-start reference → fixed with 2-pass registration
  (see iteration log).

## Checklist for future acquisition sessions

- Darks: same exposure/ISO as lights, shot at night-time temps
- Flats: histogram peak ~50% — the Jul 5 MacBook-screen setup at 1/160s gave
  only ~27%; use ≈1/50s at that screen brightness
- Flats: **diffuse the screen** — cloth/t-shirt over the lens + distance from
  the screen (Jul 5 flats show the screen pixel grid at ~0.3% RMS: harmless
  this time, avoidable always)
- Flats: shoot a flat set **per focal length used** that night, before touching
  the zoom — a 24mm flat cannot calibrate 37mm lights (set-03 ran flatless)
- Lock the zoom ring (tape) and avoid touching the camera mid-set — set-03
  stepped 37→38mm exactly at a mid-set pause where the camera was handled
- Sub length ≤ 500/focal (13s at 38mm, 20s at 24mm) or stars trail — trailing,
  not noise, capped set-03's sharpness
- Consider ISO 800 (Z6III dual-gain step), especially with shorter subs
- Dither between subs — it's what rescues us when darks are imperfect
