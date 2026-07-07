# Astrophotography processing pipeline — lab notebook

Repo tracks the **processing pipeline** (Siril scripts + notes), not image data
(see `.gitignore`). Iterate on the pipeline, commit, re-run, compare previews;
revert with git if a change makes things worse.

## STATUS — read this first (2026-07-07, end of session 6)

- **Process contract & how to run: `README.md`.** This file is the
  chronological lab notebook — the sections below are HISTORY (kept with
  their numbers so dead ends are never re-attempted); a few carry
  `[SUPERSEDED]`/`[RESOLVED]` markers where a skimmer might mistake them
  for open items.
- **Current approved recipe: B6** (user-approved, starcomb defaults,
  byte-verified again at session-6 start AND after the context refactor;
  git tag `B6-approved`). One command: `python3 scripts/starcomb.py
  07-02-26 set-03 --stack 07-02-26/results/stack_set-03_spcc.fit
  --lossless`. Reproduction contract: the 8-bit PNG (and starless jpg)
  are byte-identical; the final jpg default is now q100/4:4:4 (measured
  mean 0.44 counts vs PNG — the approved q92 artifact reproduces with
  `--jpg-quality 92 --jpg-subsampling -1`); `--lossless` also writes a
  16-bit PNG. True B6 gate numbers: blocks 1.12 colors 2/3 rings
  2.2/1.0/1.7 (the old "2/4, 1.9/1.4/1.9" line was B5's, corrected).
- **Per-set geometry is config now** (`config_<set>.json`: corridor
  manual/wcs/none, foreground rect/mask/none, boxes, crops — README
  "Per-set geometry"). No set silently inherits set-03's masks; a
  configless+WCSless set degrades loudly. Data-generalization proven on
  the `lights` set (Boötes, matched-flat path) end-to-end to a gated
  render — see "A3 RESULT".
- **The gate:** `bg_qa.py --sky-scope` on the STARLESS render (thresholds
  never loosen). Whole-frame QA + `corridor_report` numbers are REPORTED
  context in every run. Star metrics on the stars layer. The user judges
  aesthetics on the recombine before anything is baked.
- **Discipline:** single-knob ladders, hypotheses pre-registered here
  BEFORE running, dead ends written with numbers, stale-knob rule (a
  fixed root cause makes every knob tuned during the hunt stale).
- **AWAITING USER JUDGMENT (session-6 packages, nothing baked):**
  (1) B: rgb_equal removed — render pair `judgment_B_norgbeq/`; on
  approval the canonical stack switches to `stack_set-03_norgbeq_spcc.fit`.
  (2) D: star ghost-aura fix — `stars_floor` 0/1.5/3.0 in
  `exp_starsep_stars_floor_*/` (`judge_star_tiles.png`); root cause +
  numbers in "D ROOT CAUSE". (3) E: output black point 0/4/6/8 in
  `exp_starsep_black_point_*/`. (4) A2: WCS-derived corridor for set-03
  (validated, `wcs_corridor_overlay_set-03.png`) — switching re-renders.
- **Open queue:** StarNet-ONNX aarch64 check (bandaid #5 removal — see
  ledger), optional starless_target re-ladder (user request only), and
  the real quality lever — the next acquisition (ISO 800, ≤13s subs,
  matched flats per focal; see "Checklist for future acquisition
  sessions").
- **Current bandaid/adaptation ledger:** "Bandaid ledger — session 6
  refresh" (older ledgers superseded).

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
the implementation session: `NEXT_SESSION_PROMPT.md` [executed in sessions
4–5, file deleted; `README.md` is the standing process contract].

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
`results/candidate_v5_fullframe.jpg`) [HISTORY: user verdict below — MW too dark; superseded by the separation chain; file kept as audit anchor].**
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

## set-03 (same night, second composition — nearly pure sky, **CYGNUS**)

**Field identity corrected 2026-07-06 by blind astrometric solve** (local
astrometry.net engine, Tycho-2 wide-field indexes 4213–4219, 200
peak-detected stars): center **RA 312.774° = 20h51m, Dec +48.156°**,
scale 32.78″/px (= the 37.5mm/5.92µm prediction), logodds 373.5 —
certain. The brightest frame star (px 3258,1775) is **Deneb**. The old
"Big Dipper area" label was wrong (~70° off) and is why every
position-hinted platesolve failed; the strong MW band through the frame
is the Cygnus Milky Way, which retroactively strengthens the
corridor-as-signal QA scope.

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

**DECISION MATRIX (2026-07-06) [RESOLVED same day: option 3 ratified (layer-appropriate QA scope); session 5 then replaced the geometric boost with the luminosity-weighted lift]:**
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

## Standard-workflow audit (2026-07-06, session 4)

Mission: restructure to the industry-standard deep-sky order (calibrate →
stack → linear BGE → SPCC → [decon] → linear NR → star separation → split
stretch → recombine); every divergence is a bandaid unless measured and
forced by this data.

**Audit (a) — the recorded state REPRODUCES exactly (2026-07-06):**
- `bg_qa candidate_v5_fullframe.jpg`: PASS — blocks 1.35, colors 4.0/6.0,
  rings 3.7/3.4/3.4 (= recorded to the decimal)
- `bg_qa preview_set-03_20260706_104902.jpg`: FAIL — rings lum 4.9,
  R−G 6.8 (= recorded)
- MW contrast via `starcomb.box_median_g`: `stack_set-03.fit` = `_L2.fit`
  = **+39.7** linear counts (= recorded)
- Exp-dir spot-checks all match NOTES: stretch_target 133958
  (0.07 PASS / 0.09 rings 4.3 / 0.12 rings 5.4), subsky 133842 (worst
  color 6/8/9 for degree 1/2/3), mw_boost 143904 (k=0 ring 4.4 blocks
  1.33 / k=0.6 ring 6.1 / k=1.2 ring 6.9 blocks 1.72)

**Gap analysis — standard step | our implementation | verdict | plan:**

| # | standard | ours | verdict | fix plan / removal condition |
|---|---|---|---|---|
| 1 | calibrate bias/dark/flat | darks+biases matched ✓; **no 37/38mm flats** → self-flat chain (median → V2 → rechroma → divide) | **ADAPTATION** (measured: L1/L2 arc, rings/rim root-caused) | dies when real flats exist at the set's focal — preflight already auto-routes to the flat path; chain stays isolated to the flatless branch (40a/40a2/40b/40d) |
| 1b | gradients removed ONCE, on the stack | per-frame `seqsubsky 1` before division | **ADAPTATION** (justification predates GraXpert — re-examining) | measure: divide-first (multiplicative V from untouched median), NO per-frame subsky, stack-level GraXpert BGE only. Must not revive the +55% periphery lift. Keep whichever measures flatter at the rim |
| 2 | linear BGE on the stack, star-ful | GraXpert BGE + `subsky 1`, star-ful linear | **COMPLIANT** | order measured MW-safe (+38 in → +4 at render); BGE on starless ERASES the MW (+38 → +0.4) — never reorder |
| 3 | SPCC/PCC via plate solve | `rgb_equal` | **BANDAID** | SPCC feasibility test in progress: online cone is capped ≈2.5° (measured: NOMAD 1727 stars, solve FAIL on the 52° field) → local Gaia astro catalog (1.14 GB, zenodo 14692304) + `platesolve -nocrop`; SPCC needs per-field healpix-1 xpsamp chunks (zenodo 14738271, 0.03–0.63 GB each). If the solver can't do 52° trailed-star fields → rgb_equal stays, removal = narrower field / solver improvement |
| 4 | deconvolution (optional, data permitting) | skipped | **COMPLIANT** | measured dead end on this data (in-exposure trailing, PSF unstable on ≈0 bg) — data-limited, not process-limited |
| 5 | linear noise reduction | none (denoise OUT by gate) | **GAP — standard placement untested** | S3 ladder: off / `-vst` / GraXpert denoise on the STARLESS linear inside the standard order; fallback rung post-stretch `-vst -mod=0.5` |
| 6 | star separation (StarNet/SXT) | `starsep.py` mask+inpaint | **ADAPTATION** (no aarch64 StarNet; layers validated clean, MW intact) | dies when a real star-removal net runs on this box (or an off-box step) |
| 7 | stretch starless hard, stars gently, cull faint tail | starcomb split stretch; stars anchor 0.85 renders dim (mid-peak 225 vs 250 star-ful); cull untested | **PARTIAL — ladders pending** | stars_peak ladder 0.85/0.92/0.97; S4 cull_pct 0/50/75; starless target + mw_boost under the ratified QA scope |
| 8 | screen recombine + final touches | starcomb screen combine + satu | **COMPLIANT** | sep+recombine roundtrip costs ~+0.7 ring (measured) — watch it, don't hide it |
| QA | layer-appropriate checks | whole-frame `bg_qa` on the recombined jpg | **MIS-SCOPED for a separated workflow** (measured: mw_boost 0.6 → ring 6.1 — an intentional MW lift reads as background artifact) | layer-appropriate QA: strict blocks/rings gate on the STARLESS render's SKY (MW corridor + branch masked as known signal/non-sky), star metrics on the stars layer, user judges the recombine. Scope change, thresholds byte-identical — **RATIFIED by user in-session 2026-07-06**: gate = starless-sky (corridor+branch masked), star metrics on stars layer, user judges recombine; whole-frame QA stays as a reported reference, never the gate on the recombine |

**Experiment G1 (pre-registered 2026-07-06): divide-first + stack-level BGE
vs per-frame seqsubsky.** The per-frame `seqsubsky 1` is non-standard
(standard removes gradients once, on the stack); its justification predates
GraXpert in the chain. Variant (`scripts/exp_bgeonly.sh`, single
architectural knob = the glow path): calibrate → median (norm=mul) →
**multiplicative** V×S fit (`selfflat.py --model=mult`, clip floored at 3%
of model so the steep tail survives — synthetic: corner 0.657→0.576 vs
true 0.540; the additive/L2 path byte-untouched) → divide the UNTOUCHED
frames → sweep → stack → `stack_set-03_bgeonly.fit`; glow removed ONCE by
GraXpert BGE + subsky 1 on the stack (starcomb bge_first). No rechroma
(nothing re-centered channels), no V2 (mult-V matches glow-retaining
frames by construction). Hypothesis: gx (blob-capable, measured MW-safe
star-ful) models the amplified corner glow (glow/V) that subsky-2 could
not in the isotonic arc (+55% periphery, the recorded dead end). IF TRUE:
MW ≈ +39 preserved, starless-sky QA ≈ canonical at 0.07, comparable rim.
IF FALSE: stack radial profile shows the periphery lift and starless-sky
rings ≫ 4 — write the dead end, keep per-frame subsky as a measured
ADAPTATION. Decision on corridor-masked starless-sky QA + stack rim + MW.

**G1 result (run 16:11, `stack_set-03_bgeonly.fit` kept): REFUTED at the
gate — per-frame seqsubsky stays, with its justification refreshed
against the CURRENT (GraXpert-era) chain.** The linear stage was the
cleanest of any chain yet: stack rim_dev **−4.6% smooth monotone** (vs
canonical +9.0% with the 0.93 bump), stack rim chroma R−G **−0.3** (vs
−12.5 — no seqsubsky ⇒ the re-centering wound never exists ⇒ no rechroma
needed), 21/21 @ ref 12 same as canonical; post-gx linear dead flat
(rim_dev −0.4%, rim chroma +0.5/+0.3). **The +55% periphery dead end did
NOT return — GraXpert models the amplified corner glow that subsky-2
could not.** But it loses where it counts: (i) gx pays for the larger
extraction in MW — bgelin MW **+0.7 linear vs +2.6** canonical (render
MW 2.0 vs 4.0); (ii) the gx residual after the big extraction is
STRUCTURED (mid-scale radial wiggle ±1.5 counts + a −3 count rim dip)
where canonical's is a smooth trend, and the stretch amplifies that into
starless-sky rings **4.8 = GATE FAIL vs canonical 2.7 PASS** at the
identical render config (bge_first, target 0.07, k=0). Kept for reuse:
runner `scripts/exp_bgeonly.sh`, `selfflat.py --model=mult` (tail-robust
clip: floor at 3% of model — synthetic corner 0.657→0.576, true 0.540),
and the variant stack. Real-flat sets have the variant's division
geometry — revisit the mult fit then.
Side-finding: BOTH chains crush the broad MW at BGE (canonical keeps
only +2.6 of the stack's +39.7) — the corridor boost re-lifts it later.
Follow-up single-knob candidate (pre-register first): GraXpert
`-smoothing` ladder — stiffer background ↔ MW retention trade, measured
at the gate.

**SPCC feasibility arc (2026-07-06, standard-workflow step 3).** Measured
path to a working plate solve on this rig's ultra-wide trailed fields:
- Siril internal solver: online catalog cone hard-capped ≈2.5° (NOMAD
  1727 stars fetched for a 52° field → fail). Local Gaia astro catalog
  (zenodo 14692304, 1.14 GB bz2 → 1.5 GB, installed at
  `~/.local/share/siril/siril_catalogues/`, setting
  `core.catalogue_gaia_astro`) lifts the cone cap (33°, 5507 stars) but
  star MATCHING still fails at 52° AND at a 26° center crop, even with
  the correct center, `-nocrop`, `-order=3..5`, `-downscale`,
  `-limitmag=+1.5` — every combination "Initial solve failed".
- astrometry.net engine (pip `astrometry`, Tycho-2 indexes 4213–4219 =
  quads 2.8–33°) blind-solves the SAME field from **200 peak-detected
  stars** in seconds: logodds 361–373. Two lessons: (i) the star SOURCE
  matters — starsep blob centroids failed to match, coarse
  bg-subtracted peak centroids solved (`scripts/solve_field.py`,
  self-bootstrapping venv); (ii) the recorded field identity was WRONG —
  the frame is **CYGNUS (center 20h51m +48.2°, Deneb near center)**, not
  Big Dipper, so every position hint before the blind solve was ~70° off.
- Siril ACCEPTS an injected TAN-SIP WCS (header surgery on a copy:
  `solve_field.py --inject=`); `spcc` proceeds to catalog fetch on it.
  SPCC xpsamp chunks for this footprint (nested nside=2 healpix
  {2,9,12,13,14,15,31} ≈ the installer's "Summer Triangle" preset):
  zenodo 14738271, ~2.2 GB, installed to
  `.../siril_catalogues/spcc/`, setting `core.catalogue_gaia_photo`.

**SPCC experiment (pre-registered): replace the rgb_equal BANDAID with
photometric calibration.** Run `spcc -catalog=localgaia` on the
WCS-injected canonical stack → `stack_set-03_spcc.fit`. Accept if: spcc
converges on ≥50 matched stars, MW contrast (G) survives ≈ +39, and the
standard render chain on the SPCC'd stack passes the starless-sky gate
with bg color dev ≤ current (colors ≤ 6). User judges star/MW color on
the recombine. If accepted: rgb_equal stays in 40d for now (linear
scalings compose; removing it is its own later change), unlinked-vs-
linked stretch gets re-laddered on the SPCC chain since the cast SPCC
fixes is what unlinked stretch was compensating.

**SPCC RESULT (2026-07-06, 32 s with local catalogs):
"Spectrophotometric Color Calibration succeeded."** White-balance
factors K = 0.987 / **0.904** / 1.000 (R/G/B) — the photometric truth
wants G ~10% below the rgb_equal stack, i.e. rgb_equal leaves a
measured green-strong cast (exactly what the unlinked stretch has been
compensating). Linear checks: MW contrast +35.9 = 39.7 × 0.904 to the
decimal (pure multiplicative rescale — structure untouched); rim
chroma IMPROVES (R−G −9.0 vs −12.5, B−G +0.4 vs −4.8). Saved as
`results/stack_set-03_spcc.fit`. Note: SPCC needs the full 33°-radius
CONE of xpsamp chunks — the footprint set alone fails on the first
missing chunk (siril names it). Render acceptance test (gate + colors)
[RESOLVED: met in the composite runs, S8']; matched-star count not captured in the
truncated log (rerun with full capture if it ever matters).

**S8′ — the ratified gate applied to the existing S8 renders (2026-07-06,
no re-render, same JPEGs):** starless-sky scope (corridor incl. boost
feather + branch masked, thresholds identical): k=0 / 0.6 / 1.2 ALL PASS
with IDENTICAL sky numbers — blocks 1.27, colors 4/5, rings 2.7/2.3/2.9.
The boost is provably corridor-contained (the sky statistics do not move
with k); the old whole-frame "ring 6.1" at k=0.6 was pure corridor
signal. Whole-frame numbers remain as recorded in S8 (reference).
Regression guard: whole-frame scope on candidate_v5 still PASS
1.35/3.7/3.4/3.4 byte-identical after the bg_qa change.

**Ladder pre-registrations (2026-07-06, all: starcomb bge_first on the
canonical stack, single knob, NEW starless-sky gate + whole-frame
reference reported):**
- **A `starless_target` 0.07 (control) / 0.12 / 0.15** — S2's failure
  (0.12 → rings 5.0) was WHOLE-FRAME (corridor included). With the
  corridor masked, the only offender should be the +2.3% linear rim ×
  stretch slope; prediction: sky rings at 0.12 < 5.0, and the admissible
  target is whatever holds ≤4 — that value becomes the render target.
  **A RESULT (`exp_starsep_starless_target_20260706_165048`): the sky
  rim is real — base target stays 0.07.** Sky-scope rings: 0.07 → 2.7
  PASS | 0.12 → **4.4 FAIL** | 0.15 → 5.3 FAIL. The corridor masking
  explains only 5.0→4.4 of S2's failure at 0.12; the remaining 4.4 is
  rim in the corridor-complement sky. Render MW 4.0/7.0/9.0 with target
  — but the layered route gets MW visibility from the boost instead
  (S8′: k=1.2 on the 0.07 base = MW 6.0, sky PASS 2.7 unchanged), so
  brightness is assembled from gated parts: base 0.07 + boost k (user
  taste, extend ladder past 1.2 if wanted) + stars anchor (Ladder B).
- **B `stars_peak` 0.85 (control) / 0.92 / 0.97** — the stars-layer MTF
  anchor renders mid-peak 225 vs the star-ful chain's 250. Prediction:
  mid-peak rises monotonically with the anchor toward ≥250 (sat% toward
  the baseline 12–17%); sky gate untouched (different layer). User
  judges the look.
  **B RESULT (`exp_starsep_stars_peak_20260706_165244`): CONFIRMED —
  the anchor is the star-brightness lever and the layers are decoupled.**
  mid-peak 223 / 242 / **255** and sat 2 / 4 / **16%** for anchor
  0.85 / 0.92 / 0.97 (0.97 = the A1 baseline star tier); the sky gate is
  bit-identical 2.7/2.3/2.9 PASS at every rung. Halo ratio rises with
  brightness (1.14 / 1.39 / 1.96) — user judges 0.92 vs 0.97 on the
  strips.
- **C `cull_pct` 0 (control) / 50 / 75** — culling the faint half/¾ of
  the star catalog cleans field stipple; count drops, top-100 and
  mid-peak unchanged (bright tail untouched), gate unchanged. User
  judges.
  **C RESULT (`exp_starsep_cull_pct_20260706_165419`): metric-invisible,
  purely aesthetic.** Gate identical PASS (2.7/2.3/2.9), mid-peak 242 /
  halo 1.38 at every rung; detector count wiggles +30 (blend
  separation, cosmetic). The faint-field look is the user's call from
  the strips; no metric constrains it.
- **D `starless_denoise` off (control) / vst / gx** — linear NR on the
  STARLESS layer (standard step 5 placement). The old gate failures
  (pre-stretch 5.1 / post-stretch 4.2) were measured on STAR-FUL data;
  starless has no cores to ring around. Prediction: vst (and GraXpert
  denoise) on the linear starless keeps sky rings ≤ control and cuts
  grain 30–45%; if rings move, denoise stays OUT and the dead end gets
  its number.
  **D RESULT (`exp_starsep_starless_denoise_20260706_165555`): REFUTED —
  denoise is out at the STANDARD placement too, with numbers.** Sky
  rings: off 2.7 PASS | vst 4.1 FAIL | gx 4.6 FAIL (blocks unchanged
  1.27 — the damage is purely radial). Mechanism now clear: after the
  V(r) division the noise level is RADIAL by construction (corner noise
  amplified 1/V), any noise-adaptive denoiser smooths more where noise
  is higher, and that radial smoothing differential shifts the radial
  profile — the stretch amplifies it past the gate. Linear denoise is
  structurally incompatible with the ring gate on self-flat data; not a
  placement problem. Last untested rung: post-stretch `-vst -mod=0.5`
  (measured next).
  **vstpost RESULT (`exp_starsep_starless_denoise_20260706_172142`):
  PASSES — denoise is back, post-stretch only.** Sky gate 2.6/3.0/1.9
  blocks 1.20 (≈ control 2.7/2.3/2.9 @ 1.27); central grain −40%
  (diff-MAD 5.0→3.0 8-bit), bg σ −29% (7.3→5.2). Placement lesson
  complete: pre-stretch/linear = radial imprint = FAIL; post-stretch
  half-modulated on the STARLESS render = grain cut with the sky
  metrics unmoved. Optional composite rung (user judges smoothness;
  starcomb `--starless-denoise vstpost`).

**Ladder E `mw_boost` 0 / 1.2 / 2.0 (pre-registered above as extension of
S8′; `exp_starsep_mw_boost_20260706_172414`): CONFIRMED — corridor
containment holds at full strength.** Sky gate bit-identical
2.7/2.3/2.9 PASS at every k; MW render contrast 5 → 7 → 9; whole-frame
reference rises 3.8 → 8.8 → 10.4 (that IS the MW lifting — reference
only). Strips: k=1.2 shows the band + dark-lane structure with no
visible corridor edge (feather works); k=2.0 is dramatic but amplifies
corridor grain (vstpost is the matching fix) and makes the
canonical-stack greenish cast obvious — the SPCC stack should render
cleaner color. Admissible k is now purely the user's aesthetic call.

**Composite candidates (rendered on `stack_set-03_spcc.fit`, target
0.07 base, both must pass the starless-sky gate to be offered):**
- comp_a_conservative: mw_boost 0.6, stars_peak 0.92, cull 0, denoise off
- comp_b_bold: mw_boost 1.2, stars_peak 0.97, cull 50, denoise vstpost
Known cosmetic caveat measured on the E strips: the corridor's bottom
end reaches the branch, so the boost also lifts the branch halo a bit
(gate unaffected — the zone is masked); if it bothers the eye, the fix
is one line (zero the boost mask over the branch block).
**Both composites GATE PASS on the SPCC stack (2026-07-06 17:28):**
comp_a blocks 1.20 rings 2.7/2.9/2.1 MW 6.0 | comp_b blocks 1.20 rings
2.6/3.0/1.9 MW 8.0 — colors ≤6 = the SPCC render acceptance criterion
met. Full-frame, no crop. Files:
`starcomb_set-03_comp_a_conservative_20260706_172551.jpg`,
`starcomb_set-03_comp_b_bold_20260706_172741.jpg` (+ `_starless`
each). [RESOLVED: superseded by the B-series; renders pruned.]

**REMAINING BANDAIDS + removal conditions [SUPERSEDED by "Bandaid
ledger — session 5 refresh" further down; kept as the session-4
snapshot]:**
1. **Self-flat chain** (median → V1 → rechroma → V2 → divide) —
   ADAPTATION, measured. Dies when real flats exist at the set's focal
   length; preflight already auto-routes to the flat path.
2. **Per-frame `seqsubsky 1`** — ADAPTATION, re-justified 2026-07-06
   against the current chain by G1 (stack-level-only BGE: gate FAIL 4.8
   vs 2.7 + MW loss). Exists only on the self-flat branch → dies with
   real flats.
3. **`rgb_equal` at stack time** — BANDAID; SPCC measured it ~10%
   G-strong. Removal: user accepts the SPCC render → solve+spcc becomes
   a post-stack stage (tooling + catalogs installed), rgb_equal dropped
   from 40d in its own gated change.
4. **Whole-frame QA as the recombine gate** — RETIRED by ratified scope
   change (2026-07-06); lives on as a reported reference metric.
5. **Star separation by mask+inpaint** (`starsep.py`) — ADAPTATION
   (no aarch64 StarNet). Dies when a real star-removal net runs on this
   box or off-box.
6. **Denoise** — linear placements are a measured structural dead end on
   self-flat data (radial-adaptive smoothing = radial imprint); the
   post-stretch `-mod=0.5` starless rung PASSES and is an optional
   aesthetic knob, not a default.
7. **Crop** — eliminated; the layered chain passes the gate at full
   frame (crop's only remaining use would be aesthetic framing).

**"Cleanliness" ladder set F–I (pre-registered 2026-07-06, user-directed
after the grain audit: corridor signal/grain ≈ 1 at 8.75 min ISO 200 —
the knobs polish presentation, photons are the real fix). All on the
SPCC stack, base = comp_b config, each experiment varies ONE knob and
adopts the previous winner:**
- **F `sep_prom` 6 (control) / 5 / 4** — the 4–6σ faint tail currently
  stays in the STARLESS layer as stipple (below starsep's prominence
  cut) where the boost amplifies it and cull can't reach it. Lowering
  the cut moves it to the stars layer. Predict: starless stipple count
  drops, stars-layer count rises (cull 50 eats it), MW contrast
  unchanged (MW knots are extended — the compactness test keeps them),
  gate PASS. ABORT if MW linear contrast drops >10% (separation eating
  MW).
  **F RESULT (`exp_starsep_sep_prom_20260706_180933`): NULL — the
  prominence cut is not the stipple lever.** Starless residual star
  count 5137 / 5179 / 5159 and corridor grain 6.00 / 6.00 / 6.00 for
  prom 6 / 5 / 4; gate PASS and MW 8.0 everywhere. The "stipple" is not
  made of separable 4–6σ components — it is noise-level clumping (the
  post-stretch detector counts noise maxima), exactly what
  signal/grain ≈ 1 predicts. sep_prom stays 6; the denoise/chroma
  knobs are the real levers.
- **G `starless_denoise` vstpost (control) / vst_after_boost** — vstpost
  runs before the boost so the boost re-amplifies residual grain
  ×(1+k). After-boost denoising sees the amplified grain. Predict:
  corridor grain 7 → ≤5 at identical MW contrast; gate PASS.
  **G RESULT (`exp_starsep_starless_denoise_20260706_181710`): REFUTED —
  vstpost (before boost) stays.** vst_after_boost: corridor grain 6→**7**
  (worse), sky 4→2 (over-smoothed, don't care), MW 8→7 (lift eaten).
  Mechanism: after the boost the noise field is NON-STATIONARY (corridor
  ×2.2 vs sky); NL-Bayes with a global σ under-averages the noisy
  corridor patches and over-smooths the quiet sky — the opposite of the
  goal. Denoise-before-boost sees stationary noise and treats the
  corridor properly; the boost then amplifies a residual that is
  already minimized.
- **H `chroma_nr` 0 (control) / 2 / 4 px** — the speckle is
  color-dominant; blur R−G/B−G only, G untouched. Predict: chroma grain
  collapses, luminance grain unchanged, sky color-dev ≤ control, gate
  PASS; large-scale star/MW color intact (strips).
  **H RESULT (`exp_starsep_chroma_nr_20260706_181938`): CONFIRMED —
  chroma_nr 4 is free money.** 4px-lag chroma clump amplitude in the
  corridor 7.0 / 4.0 / **2.0** for σ 0 / 2 / 4 (the crops' visible
  speckle scale); luminance grain flat (7→8 = jpg-quantization floor
  jitter); gate PASS everywhere and best at σ4 (2.3/2.3/1.8); MW 8.0
  and star metrics identical. Winner σ=4 — adopted.
- **I `satu` 0 (control) / 0.2 / 0.35** — the new chain shipped with NO
  saturation step; chroma gain on the combined render, AFTER chroma_nr
  so it amplifies color, not speckle. Gate + color-dev decide the
  ceiling; user judges the look.
Then **B″** = comp_b + all four winners, full audit, user judgment.
  **I RESULT (`exp_starsep_satu_20260706_182244`): CONFIRMED — satu is a
  free color knob post-chroma-NR.** Star-pixel mean |chroma| 18.1 /
  21.9 / 24.7 for s 0 / 0.2 / 0.35; sky gate BIT-IDENTICAL (satu runs
  on the combined render, the gated starless layer never sees it);
  speckle stays down (4px clump 2→3); sat% 13→15/16 (mild clip growth).
  Ceiling not reached at 0.35; 0.2 = safe default, taste decides.

**B″ final config: SPCC stack · target 0.07 · mw_boost 1.2 ·
stars_peak 0.97 · cull 50 · vstpost (before boost) · chroma_nr 4 ·
satu 0.2 · sep_prom 6.**

**Disk cleanup (2026-07-06, user-directed; 15→32 GB free).** Deleted, with
regeneration paths: `stack_set-03_L2.fit` (verified byte-identical to
`stack_set-03.fit` — dedup, canonical name kept); `_prechroma` (historic,
numbers in NOTES); `_bgeonly` (G1, regen via `exp_bgeonly.sh`); `_wcs`
(regen in seconds: `solve_field.py <stack> --inject=...`; the solved WCS
itself kept at `work/wcs_set-03.json`, and `stack_set-03_spcc.fit`
carries it in-header). Siril local catalogs REMOVED (7.5 GB):
re-download = zenodo 14692304 (astro, 1.14 GB bz2) + 14738271 chunks
{2,3,9,11,12,13,14,15,19,29,31} for this field (settings
`core.catalogue_gaia_astro/photo`). Superseded exp dirs: images
stripped, hypothesis.md + metrics.jsonl kept (full-strip list = morning
arc + S2/S5–S8 + F/G refuted). work/ caches: only the SPCC chain's
bgelin/gx/starsep kept hot. Old previews deleted except the two audit
anchors (`preview_set-03_20260706_104902.jpg`, `candidate_v5_fullframe.jpg`).

**CHROMA SIGNIFICANCE CORING (pre-registered 2026-07-06, the correct-step
fix for the user's "rainbow" — measured birth + scale trace above the
composite list).** Diagnosis recap (all measured, sky-only, corridor
excluded): linear chroma structure ≤0.1 counts at 16–128 px after BGE →
the UNLINKED STRETCH amplifies per-channel noise into 1–3 counts of
colored blotch at ALL scales → NL-Bayes (few-px) and chroma-blur σ4
(≤16 px) are scale-blind to the 48–128 px blotches → satu re-amplified
everything ~×1.25 (B″ measurably worst at 48–128 px; B″ withdrawn).
FIX: multi-scale Wiener shrinkage of R−G/B−G toward NEUTRAL — gaussian
pyramid (σ 2/8/32/128), per-level noise measured from the corridor-
excluded sky, per-level energy gate e/(e+(kσ)²); chroma that is not
significantly above its own noise goes to gray instead of being smeared.
Real color (bright-star hues, genuinely tinted signal) passes by
construction. `starcomb --chroma-core k` (0=off), applied AFTER
boost+denoise; satu only after coring, if at all. Ladder J: k = 2/3/4
(control 0). ACCEPTANCE: the scale-trace table re-run lands the rendered
sky ≤ ~0.5 counts at 16/48/128 px; star-pixel mean |chroma| within ~10%
of control; gate PASS; MW contrast unchanged; user judges B‴.

**J RESULT (`exp_starsep_chroma_core_20260706_195853`): CONFIRMED,
decisively.** Sky chroma structure RG/BG at 16 / 48 / 128 px:
k=0 → 2.52/3.01 · 1.47/2.03 · 1.10/1.67 | k=2 → 0.83/1.12 · 0.51/0.80 ·
0.37/0.57 | **k=3 → 0.12/0.54 · 0.34/0.50 · 0.28/0.38 (acceptance met)**
| k=4 → 0.02/0.05 · 0.26/0.36 · 0.24/0.32 (≈ linear floor). Star-pixel
|chroma| 19.5 → 18.9/18.5/18.2 (−3/−5/−7%, within acceptance). Gate PASS
at every k and the sky ring-color metrics IMPROVE (ringRG 3.0→1.3,
ringBG 1.9→1.0): the coring also removes the large-scale color wobble
the ring meter was seeing. MW 8.0, stars mid 255 / sat 13, halo —
unchanged. **Winner k=3** (k=4 = maximal neutrality at −7% star color,
kept in the strips). B‴ = comp_b config + chroma_core 3, NO satu, NO
chroma-blur (both superseded by coring).

**USER VERDICT on B‴ (2026-07-06): "much better, correct direction" —
two residuals + a directive.** (i) Leftover coloration toward the
middle; (ii) the former color bands now read as GRAY patches — the
background contrast is uneven (the coring removed the blotches' chroma,
not their luminance; the rainbow was masking the gray). Directive:
bandaids whose root cause is now fixed must be REVERTED, and nothing is
baked/committed until this is addressed.

**Bandaid ledger for the color cast (user question answered):**
`rgb_equal` = stack-time bandaid, INERT under SPCC (linear scalings
compose; SPCC's fit absorbs it) — removal is hygiene, queued (needs
re-stack + catalog re-download). **Unlinked autostretch = ACTIVE
bandaid** ("per-channel bg equalization kills global casts" — stretch-
time cast compensation) **and the rainbow's engine**: per-channel curves
differentially amplify per-channel noise into color blotches. A2's
linked-stretch QA failure was measured on the PRE-SPCC cast — invalid
against the calibrated stack.

**J2 (pre-registered): stretch linkage on the SPCC chain, unlinked
(control) / linked, B‴ config otherwise.** Predict: linked on the
CALIBRATED stack keeps a neutral bg (no cast to preserve), REDUCES
chroma blotch amplitude at the source (one curve for all channels), gate
PASS, stars unaffected (separate layer). If bg casts return → SPCC
didn't fully fix the root cause, unlinked stays and is re-documented as
a measured adaptation (not a stale bandaid).

**J2 RESULT (`exp_starsep_stretch_linked_20260706_203750`): CONFIRMED —
the unlinked-stretch bandaid is REVERTED; linked is the chain's stretch.**
On the SPCC-calibrated stack, linked PASSES the gate (2.8/1.2/1.8,
blocks 1.20; A2's old linked failure was the pre-SPCC cast, now
measured stale), cuts luminance blotches ~12% at the source (L16/L48
2.33/1.40 vs 2.65/1.58), improves the whole-frame reference (7.0 vs
7.9). Cost: MW render contrast 6 vs 8 at the same boost (different
curve shape; recoverable via k if wanted). Linked adopted.

**J3 (pre-registered): coring order, post-boost (control) / pre-boost.**
The middle's leftover color = boosted corridor noise-chroma (×2.2)
beating significance thresholds calibrated on the un-boosted sky.
Pre-boost coring neutralizes first; the boost then amplifies neutral
signal and cannot re-create color. Predict: corridor chroma residual
drops to sky levels; MW luminance contrast unchanged.

**J3 RESULT (`exp_starsep_core_order_20260706_204538`): CONFIRMED —
coring moves BEFORE the boost.** Corridor chroma residual (the user's
"middle coloration"): post → 1.89/2.36 (16px RG/BG), 1.38/1.81 (48px)
| pre → **0.81/1.18, 0.54/0.87**. Gate identical PASS, MW luminance
contrast unchanged (coring is chroma-only). Residual sits above sky
level because the boost ×2.2 amplifies the significant survivors —
honest color, user judges.

**K measurement (gray patches quantified):** sky G blotch, detrended,
16/48/128 px: linear after BGE 0.10/0.08/0.06 → stretched
2.65/1.59/1.16 (unlinked; linked 2.33/1.40) → B‴ identical (chroma
coring correctly does not touch luminance). The unevenness is
stretch-amplified luminance noise, ~±2 counts on a 15-count sky.

**K (measure first, decide after J2/J3): mid-scale LUMINANCE blotches**
— same trace as the chroma one but on G (detrended), sky-only, linear vs
rendered stages. If the gray patches are stretch-born noise (expected),
options: sky-only luminance significance coring toward the smooth
background (corridor protected), or acceptance as honest grain — user
judges with the numbers in hand.

**K RESULT (`exp_starsep_lum_core_20260706_205037`): CONFIRMED — the
gray patches were the sky's own stretch-amplified luminance noise and
the sky-only coring removes them.** k=0 → blocks 1.20 rings 2.8 | k=2 →
**blocks 1.12 rings 1.9** | k=3 ≡ k=2. Winner k=2 (lighter touch).
Bonus: MW render contrast 6→8 at the same boost (flatter sky makes the
corridor stand out). Combined-frame lum blotch 3.31/2.90/1.55 →
1.51/2.37/1.25 at 16/48/128 px. Note for the user's star judgment:
star-pixel |chroma| eased 18.5→15.2 with the linked stretch — a
satu-after-coring rung can restore star color selectively if wanted.

**B⁗ (`starcomb_set-03_final_B4_20260706.jpg`, promoted from the K
ladder's k=2 rung): the full winner chain** = SPCC stack · linked
stretch (bandaid reverted, J2) · target 0.07 · vstpost · chroma_core 3
PRE-boost (J3) · lum_core 2 (K) · mw_boost 1.2 · stars anchor 0.97 ·
cull 50 · no satu · no chroma-blur · full frame. **GATE: PASS blocks
1.12, colors 2/4, rings 1.9/1.4/1.9 — the flattest, most neutral sky
of the project.** [RESOLVED: user approved as B4 below.]

**USER: B⁴ APPROVED** ("much better") + directive: restore/maximize
color now that the root causes are fixed. SPCC + linked stretch
accepted as the color chain. Bake+commit after the final tuning rung.

**I′ (pre-registered): satu-after-coring on the B⁴ base, 0 (control) /
0.2 / 0.35.** Both corings run on the starless layer BEFORE the
combine; satu runs on the combined render — so it amplifies only
surviving (significant) color: star hues and honest corridor tint, not
noise. Predict: star-pixel |chroma| recovers from 15.2 toward ≥19; sky
chroma traces stay at the floor (neutral × gain = neutral); gate PASS.
Winner becomes B⁵ = the APPROVED RECIPE.

**I′ RESULT (`exp_starsep_satu_20260706_210947`): CONFIRMED.**
star |chroma| 15.2 / 18.5 / **20.9** for satu 0 / 0.2 / 0.35; sky
chroma16 stays 0.29/0.56 → 0.79/0.97 at 0.35 (≈⅓ of the old rainbow's
2.5–3.3, at the jpg quantization scale); gate bit-identical PASS.
Winner **0.35**.

## APPROVED RECIPE — B⁵ (2026-07-06, USER-APPROVED) [SUPERSEDED by B6, session 5]

`results/starcomb_set-03_APPROVED_B5_20260706.jpg` — full frame
6064×4040, GATE PASS blocks **1.12**, colors 2/4, rings
**1.9/1.4/1.9** (the flattest sky of the project).

    python3 scripts/starcomb.py 07-02-26 set-03 \
        --stack results/stack_set-03_spcc.fit
    # all knobs are now the starcomb DEFAULTS (baked 2026-07-06):
    #   starless: linked autostretch -1.5 0.07 · vstpost denoise
    #             · chroma_core 3 (pre-boost) · lum_core 2 · mw_boost 1.2
    #   stars:    anchor 0.97 · cull 50
    #   combine:  screen · satu 0.35 · full frame · no crop
    # input = the SPCC-calibrated stack (solve_field.py --inject + spcc)

Chain provenance, each knob a measured ladder: target 0.07 (A: rim caps
brighter), vstpost (D: linear NR structurally dead, post-stretch −40%
grain), anchor 0.97 (B: mid-peak 255, layers decoupled), cull 50 (C:
metric-invisible), boost 1.2 (E/S8′: corridor-contained at any k),
chroma_core 3 (J: rainbow → neutral, sky at linear floor), pre-boost
order (J3: middle coloration halved+), linked stretch (J2: unlinked
bandaid retired post-SPCC), lum_core 2 (K: gray patches removed, blocks
1.20→1.12, MW +2 free), satu 0.35 (I′: star color 20.9, sky ≤1 count).
Rejected on measurement: sep_prom (F: null), vst_after_boost (G:
non-stationary noise), chroma-blur+satu (H+I: made the rainbow worse —
withdrawn).

**PIPELINE VERIFICATION (2026-07-06): the baked defaults reproduce the
approved image PIXEL-EXACTLY.** One command, no flags beyond the stack:
`starcomb.py 07-02-26 set-03 --stack results/stack_set-03_spcc.fit
--lossless` → jpg byte-equivalent to the promoted B⁵ (max diff 0, mean
0.000 — the whole chain incl. NL-Bayes denoise is deterministic), gate
PASS identical (1.12, 1.9/1.4/1.9). Side-finding: **JPEG q92 costs
mean 2.6 counts (max 242 at star edges, 32% of pixels >2) on this
grain-heavy content** — the earlier "diff" was entirely jpg
quantization. Finals ship as lossless PNG (`--lossless`):
`results/starcomb_set-03_approved_verify_20260706_212422.png` (43.6 MB,
6064×4040) = the pixel-true approved product.

## Session 5 (2026-07-06/07): four-defect audit — provenance, QA blind spots, re-derivation

**USER VERDICT on B⁵ (start of session): four defects, all confirmed and
measured on the approved render** (`_approved_verify_...png`, pixel-true;
gate re-run first: starless-sky PASS 1.12 / 1.9/1.4/1.9 = recorded values
— the state reproduces, the defects live where the gate does not look):

1. **"Leftover chroma, banding streaks/strips of red and blue."** Two
   measured components: (i) diffuse chroma bands in/along the corridor —
   large-scale (σ24-smoothed) profile P2V along the band axis **B−G 4.0 /
   R−G 2.2 counts** (across-band ~1.0, rows ~0.5 — the structure is
   corridor-oriented, not sensor row/col banding; linear sensor banding
   was ruled out at 0.2–0.5 count rms hi-pass); (ii) per-star red/blue
   fringing on the trailed PSFs: star-pixel R−B spans **P5 −76 / P95 +72
   counts** (÷1.35 without satu). Both are *survivors × amplifiers*:
   chroma that passes the core gets ×2.2 (boost, corridor) then ×1.35
   (satu).
2. **"Gray left where red chroma bands were removed (left-top)."**
   Left-top starless sky blocks span 12–20 vs global P50 15 (+5-count
   patches). Mechanism: coring R−G→0 removes the *chroma*, not the
   correlated G-luminance of the blotch; lum_core k=2 shrinks it only
   partially (K: residual 1.5/2.4/1.3 counts at 16/48/128 px), and satu
   re-amplifies survivors ×1.35.
3. **"Dark areas inside the MW glow gray instead of deep black."**
   Corridor starless floor **P50 22 / P5 12** vs deep-sky **P50 15**
   (block G medians, branch excluded). The geometric boost multiplies
   *everything* above bg ×(1+k)=2.2 inside the corridor: real glow AND
   noise AND the gaps the user wants black. **The ratified gate masks the
   corridor, so this cost is structurally invisible to QA** — it was
   accepted on S8′ "corridor containment" (true for the SKY statistics)
   without any corridor-scoped metric existing.
4. **"Faint star removal half-done."** Sub-prominence (<6σ) stars stay in
   the starless layer (F: ~5.1k detector counts, unmovable by prom
   4/5/6) and are boosted ×2.2 into smudges; meanwhile cull 50 deletes
   the separated faint half (~11.5k stars) from the stars layer entirely,
   leaving their inpaint fills — adjacent "shows-through" and
   "removed-hole" states = the user's "caught between" look. C recorded
   the cull as metric-invisible and left it at 50 by default; the
   aesthetic was never actually judged.

**+ objective defect found during the audit: the branch-rectangle SEAM.**
`lum_core` multiplies its correction by the *hard* branch rectangle
(rows ≥0.75h, cols <0.22w) — the correction stops dead at the edge and
prints a straight line into the sky: measured starless G step **+1.0
count** across y=0.75h and **−1.5** across x=0.22w (visible in crops).
The mask was borrowed from the QA block scope, where a hard rectangle is
fine; in a *rendering* operator it must be feathered (or tight to the
actual treeline). Related known cosmetic: the boost mask does not exclude
the branch at all (S8-era note) — same class of fix.

**Knob-provenance audit (the user's rule: when a root cause is fixed,
every variable tuned while hunting it must be re-derived).** The root
causes fixed late in session 4 were SPCC (replacing rgb_equal's cast) and
the linked stretch (retiring the unlinked bandaid = the blotch engine).
Provenance of every B⁵ knob, from the exp-dir fixed-configs:

| knob = value | derived in | chain it was tuned on | verdict |
|---|---|---|---|
| starless_target 0.07 | A-starsep 16:50 | canonical (non-SPCC) stack, unlinked, NO corings, boost 0 | **STALE — re-derive** (the 0.12-fails-gate cap predates every noise treatment now in the chain) |
| starless_denoise vstpost | D 16:55→17:21 | canonical stack, unlinked, no corings | **STALE — re-verify** (placement lesson likely still holds; the *need* may not) |
| mw_boost 1.2 | E 17:24 | canonical stack, unlinked, no corings, stars 0.92 | **STALE — re-derive**, and the geometric-corridor *architecture* itself is the issue-3 engine |
| chroma_core 3 | J 19:58 | SPCC stack but **unlinked**, core_order post | **STALE — re-ladder** (J2 measured linked cuts blotch amplitude ~12% at source; k was never re-chosen) |
| core_order pre | J3 20:45 | linked chain | current ✓ |
| lum_core 2 | K 20:50 | linked chain | current ✓ (but its branch mask prints the seam — fix objectively) |
| stars_peak 0.97 / cull 50 | B/C 16:52/16:54 | stars layer (stretch-independent) | anchor ✓; **cull 50 re-judge** (issue 4; "metric-invisible" ≠ approved) |
| satu 0.35 | I′ 21:09 | linked B⁴ chain | current ✓ mechanically; **re-judge at the end** (it amplifies every surviving defect: bands, fringes, gray patches) |

**QA blind-spot fixes (scope stays ratified: gate thresholds untouched,
corridor stays masked from the GATE).** New REPORTED corridor metrics in
every starcomb run, so corridor-contained costs are measured instead of
invisible: `corridor_floor` (P50 and P5 of corridor starless block
medians minus sky P50 — issue 3's number), `corridor_chroma` (along-band
R−G/B−G profile P2V — issue 1's number), `seam_step` (starless G step
across the branch-mask edges — the objective defect gauge). Reported
next to the gate line in every run and logged in metrics.jsonl.

**Pre-registered experiments (single knob each, control bracketed,
verdicts by measurement; aesthetic winners need the user):**
- **M0 (objective fix, commit on pass/fail): feather the rendering
  masks.** lum_core's branch factor and the boost mask's branch exclusion
  become smooth (feathered rectangle, σ≈0.02·h at the edges; geometry
  unchanged otherwise). Hypothesis: seam_step → <0.3 counts both edges;
  gate + all other metrics unchanged within noise. (The QA/block masks
  are statistics scopes and stay hard — this touches only rendering
  operators.)
- **M1 `boost_mask` geo (control) / lum:** replace the flat geometric
  corridor gain with a LUMINOSITY-WEIGHTED lift (standard astrophoto
  practice: luminosity masks / masked stretch): M_lum =
  corridor_geo × norm(smooth(starless − bg, σ≈64px))₊, so the lift
  follows the actual glow and the gaps/floor stay put. Hypothesis:
  corridor_floor P5-delta → ~0 (gaps reach sky black), MW contrast
  within ~1 of control, gate PASS, stipple amplification in gaps drops.
  If MW visibly weakens the mask normalization is wrong, not the idea —
  measure before judging.
- **M2 `mw_boost` re-ladder on the winning mask: 1.2 (control) / 0.8 /
  0.5.** With the floor fixed, k trades MW pop vs corridor noise
  amplification honestly. corridor_floor + corridor grain + MW contrast
  reported; user judges the strips.
  **M1 RESULT (`exp_starsep_boost_mask_20260706_220955`): CONFIRMED —
  lum adopted.** geo → lum: floor P50 +6.2 → **+5.0**, floor P5 **−3.0 →
  −1.0** (the flat gain was amplifying NEGATIVE deviations too — geo
  pushed the darkest corridor blocks 3 counts BELOW sky level; the
  glow-weighted lift leaves the gaps at sky black), band chroma RG/BG
  1.27/2.50 → **1.08/1.88**, gate byte-identical PASS, stars unchanged.
  Cost as predicted: MW 8.0 → 6.0 (mid-glow weight < 1) → M2 re-ladders
  k UPWARD on the lum mask (revised from the pre-registration above:
  values 1.6/2.0, control 1.2): at the glow the weight ≈ 0.5–1 so k=2.0
  restores mid-glow gain ≈ geo@1.2 while the gaps (weight ≈ 0.1) stay
  ≈ dark. Hypothesis: MW → ≈8 with floor P50 ≤ +6, P5 ≥ −1.5, bands ≤
  geo control, gate PASS.
  **M2 RESULT (`exp_starsep_mw_boost_20260706_221706`): k recovers MW
  linearly but trades the M1 gains back proportionally.** k=1.2/1.6/2.0
  → MW 6/7/8, floor P50 +5.0/+6.0/+6.0, P5 −1.0/−1.8/−2.0, bands RG/BG
  1.08/1.88 · 1.2/2.1 · 1.3/2.4; gate identical PASS throughout. At
  matched MW 8, lum@2.0 still beats geo@1.2 on gaps (P5 −2.0 vs −3.0,
  P50 6.0 vs 6.2) — never worse. **The k value is an honest aesthetic
  trade (gap blackness ↔ MW brightness): user judges. Ladder base for
  M3–M5 = lum @ k=1.2** (max issue-3 fix, matching the complaint);
  k=2.0 rendered for the judgment package as the MW-parity option.
- **M3 `chroma_core` re-ladder on the linked chain: 3 (control) / 2 / 4.**
  Acceptance per J: sky chroma ≤ ~0.5 counts at 16/48/128 px, star
  |chroma| within ~10% of control, gate PASS — plus the new
  corridor_chroma metric for the band residual (issue 1i).
  **M3 RESULT (`exp_starsep_chroma_core_20260706_222709`): k=4 WINS by
  the pre-registered criterion.** Corridor bands RG/BG: k=2 → 1.66/3.08,
  k=3 → 1.08/1.88, **k=4 → 0.73/1.25** (vs B5's 1.16/2.31 ≈ −40%);
  sky colors 2/3; star|chroma| 18.7/18.5/18.3 — the J-era −7% star-color
  cost of k=4 was an UNLINKED-chain artifact, on the linked chain it is
  −1%. Gate PASS everywhere, floor/MW untouched (chroma-only op ✓).
  chroma_core 4 adopted for the candidate.
- **M4 `cull_pct` re-judge with corridor crops: 50 (control) / 25 / 0.**
  Hypothesis: cull 0 restores the separated faint stars over their own
  inpaint sites, converting "smudge + hole" into "faint star" (issue 4);
  metrics unchanged (C); the look is the user's call — this time with
  corridor close-ups in the strips, not full-frame thumbnails.
  **M4 RESULT (`exp_starsep_cull_pct_20260706_223650`): metrics invariant
  (re-confirms C) — the corridor close-ups are decisive and split the
  issue into two coherent looks.** cull 0 restores the separated faint
  half over their own inpaint sites: the half-state ("smudge + hole")
  visibly disappears — the corridor reads as a dense honest star field
  on black. cull 50 (+lum boost, which amplifies near-bg fills less than
  geo did) is cleaner than B5 but keeps residual smudges = the
  UNSEPARABLE sub-6σ stipple (F: noise-level clumping) + 11.4k inpaint
  fills. The user's stated expectation ("properly removed → black") is
  the cull-high pole and is PHYSICALLY CAPPED on this data — full
  removal of the faint tail is impossible below the separation floor, so
  the honest choices are: no half-state via cull 0 (candidate default,
  recommended) or maximal removal via cull 50+ accepting the stipple
  floor. USER DECIDES; both rendered in the judgment package.
- **M5 `satu` 0.35 (control) / 0.2 / 0:** after M1–M4 remove/reduce the
  defect signal satu was amplifying, re-judge how much chroma gain the
  render wants. Star fringe span (R−B P5..P95 over star pixels) reported.
- **M6 `starless_target` 0.07 (control) / 0.10 / 0.12 — only if the user
  wants a brighter overall render** after M1–M5: the 0.07 cap predates
  the corings; the gate ceiling may have moved. bg level rises with
  target (0.07→18, 0.12→31 of 255) — this knob trades global sky
  blackness for MW brightness, which is the user's aesthetic call, so it
  runs LAST and only on request.

  **M5 RESULT (`exp_starsep_satu_20260706_224743`): fringe span scales
  ~(1+s) exactly; the chain changes already cut it.** satu 0/0.2/0.35 →
  star|chroma| 13.4/16.4/18.7, star R−B span 79/94/107 counts (B5
  measured 148 at satu 0.35 — cull-0's faint-star population + the M1–M3
  chain lowered the per-pixel extremes). Gate/bands/floor bit-identical
  (satu never touches the gated layer ✓ re-confirmed). The residual
  fringe driver is physical (trailed PSF + atmospheric dispersion —
  acquisition checklist item), satu only multiplies it. **Candidate
  default satu 0.2** (clear star color at −12% fringe vs 0.35); 0 and
  0.35 rungs kept as the color poles for the user.

**Sensor-banding check (session 5, measured before touching anything):**
axis-aligned banding in the LINEAR SPCC stack, sky-only hi-pass column/row
median profiles: cols P2V 5.3–7.9 / rows 3.1 (16-bit counts) ≈ 0.008–0.012%
of signal — real but sub-visible after the stretch (rendered axis-aligned
residual 0.2–0.5 count rms vs the 1.2–2.5 count corridor-oriented bands).
**Verdict: NO fixbanding-class step needed; the user's "bands" are
corridor-oriented chroma survivors + per-star trailing fringes, not sensor
pattern.** Dead end for a fixbanding experiment — don't run one.

**M0 results (objective seam fix, two iterations):**
- Metric lesson first: a level-step seam gauge FAILED (strip-median ≈ 0 —
  the coring seam is a TEXTURE discontinuity; level steps are dominated by
  real sky gradients + 8-bit quantization). corridor_report's seam gauge
  is now the blotch-texture MAD ratio across each rectangle edge (σ16
  hi-pass → σ48 smooth, un-cored/cored side; 1.0 = no seam). B5 measures
  **4.46 (y) / 1.35 (x)** — the objective number behind the visible line.
- M0a (feathered branch factor, feather 0.05): y-ratio 4.46 → 3.13, x
  1.35 → 0.86 — the LINE goes away but the rectangle remains a zone of
  un-cored, texture-mismatched sky (ramp just hides the edge).
- M0b (branch factor REMOVED from lum_core's applied correction; branch
  stays excluded from the noise ESTIMATE): the Wiener significance gate
  already protects real structure (tree/halo energy ≫ noise ⇒ correction
  ≈ 0 there) — the geometric protection was redundant for the foreground
  and harmful for the sky sharing its rectangle. The mw_boost mask keeps
  a FEATHERED branch exclusion (a gain has no significance gate; unfixed
  it lifted the tree halo — the S8-era known cosmetic, now closed).
  **M0b ADOPTED (objective): gate byte-identical PASS (1.12, 2/4,
  1.9/1.4/1.9), floor/band metrics unchanged, no line at either rectangle
  edge (none can exist — the correction has no boundary), the old
  rectangle's sky visibly smoother in the A/B crops, tree halo no longer
  lifted.** Residual seam_y texture ratio 2.94 (from 4.46) = the corner's
  honest glow structure passing the significance gate, not a mask
  artifact; it may improve further at M2 (less boost) but is not a seam.

**SESSION 5 CANDIDATES (all gate PASS, full frame, awaiting user judgment
— per the rules NOTHING is baked as defaults until approval; run via
flags on the M0-fixed scripts):**
- **C1 (recommended)** `--boost-mask lum --chroma-core 4 --cull-pct 0
  --satu 0.2`: every measured defect number at its session-best — floor
  +5.0/−1.0 (B5: +7/−3 at the old metric run, geo +6.2/−3.0 same-day),
  bands 0.73/1.25 (B5 1.16/2.31), no seam, no half-removed stars
  (restored faint field), fringe span 94 (B5 148). Cost vs B5: MW box
  contrast 6 vs 8, busier faint-star field.
- **C2 (MW parity)** = C1 + `--mw-boost 2.0`: MW 8 = B5's level; floor
  +6.0/−2.0, bands 1.3/2.4 (≈B5's, still no geo gap-darkening).
- **C3 (max removal)** = C1 + `--cull-pct 50`: the user's stated issue-4
  pole (faint stars removed) — cleaner than B5 (lum boost amplifies
  near-bg inpaint fills less) but the sub-6σ stipple floor is physical;
  gaps can never be fully starless-black on this data.
- satu poles on the C1 base: 0 (fringe-minimal, muted) and 0.35
  (B5-level color) live in `exp_starsep_satu_20260706_224743/`.

**Bandaid ledger — session 5 refresh (THE CURRENT LEDGER; the session-4
list above is superseded). Every divergence from the standard workflow,
with its class and removal condition:**
1. **Self-flat chain** (median → V1 → rechroma → V2 → divide) —
   ADAPTATION, measured. Dies when real flats exist at the set's focal
   length; preflight already auto-routes to the flat path.
2. **Per-frame `seqsubsky 1`** — ADAPTATION, re-justified by G1 against
   the GraXpert-era chain (stack-level-only BGE: gate FAIL 4.8 vs 2.7 +
   MW loss). Exists only on the self-flat branch → dies with real flats.
3. **`rgb_equal` at stack time** — BANDAID made INERT by SPCC (linear
   scalings compose). Removal queued: catalog re-download + re-stack +
   re-SPCC + gate verify, its own gated change (templates annotated).
4. **Whole-frame QA as the recombine gate** — RETIRED by the ratified
   scope change; lives on as a reported reference. Its corridor blind
   spot is covered by REPORTED corridor metrics
   (`astrometrics.corridor_report`) in every starcomb run.
5. **Star separation by mask+inpaint** (`starsep.py`) — ADAPTATION (no
   aarch64 StarNet). Dies when a real star-removal net runs on this box
   or off-box. Cost documented: the <6σ faint tail stays in the starless
   layer (physical floor, M4/F).
6. **Denoise** — linear placements are a measured structural dead end on
   self-flat data (radial-adaptive smoothing = radial imprint); the
   post-stretch `-vst -mod=0.5` starless rung is in the approved chain.
7. **Crop** — eliminated; the layered chain passes the gate at full
   frame.
8. **NEW/CLOSED: hard branch rectangle in rendering operators** — was
   printing a seam (M0); rendering ops now use significance protection
   (lum_core) or feathered masks (mw_boost). Statistics scopes keep the
   hard rectangle by design.
9. **RECLASSIFIED: flat geometric mw_boost** — was an unmeasured
   corridor-wide gain (the issue-3 engine, invisible to the gate);
   replaced by the luminosity-weighted lift (M1) = the standard
   luminosity-mask idiom. The knob k remains aesthetic (M2), its cost is
   now measured (floor/band metrics). Removal condition for the boost
   entirely: enough integration at the next acquisition that the global
   stretch renders the MW without a local lift (ISO 800, ≤13s subs, real
   flats).
10. **STALE-KNOB RULE INSTITUTIONALIZED:** chroma_core 3 → 4 (M3, linked
   chain), satu 0.35 → 0.2 recommended (M5), cull 50 → user decision
   (M4), target 0.07 re-validated only in so far as the corings moved the
   rim numbers — M6 remains available on request.

## APPROVED RECIPE — B6 (2026-07-06 session 5, USER-APPROVED)

**User verdict on the session-5 candidates: "C1 with … the judge box on
the far right side wins and is approved" — the far-right judgment-panel
tile is C3_maxremoval = the C1 chain with cull 50 (the user's stated
issue-4 pole: faint stars removed).** Approved config, now the starcomb
DEFAULTS (this commit):

    python3 scripts/starcomb.py 07-02-26 set-03 \
        --stack 07-02-26/results/stack_set-03_spcc.fit [--lossless]
    # defaults (B6): SPCC stack · linked autostretch -1.5 0.07 · vstpost
    #   · chroma_core 4 pre-boost (M3) · lum_core 2 (no branch factor, M0)
    #   · mw_boost 1.2 on the LUMINOSITY-WEIGHTED corridor mask (M1/M2)
    #   · stars anchor 0.97 · cull 50 (M4, user choice) · screen
    #   · satu 0.2 (M5) · full frame · no crop

Delta to B5, each from a measured ladder: boost_mask geo→lum (M1: gaps
at sky black, floor P5 −3.0→−1.0, bands −20%), chroma_core 3→4 (M3:
bands −40%, star color −1% on the linked chain), satu 0.35→0.2 (M5:
fringe span −12%), lum_core branch seam fixed (M0). Kept: cull 50 (M4 —
the far-right panel; C1's cull-0 faint-field kept as the recorded
alternate `starcomb_set-03_C1_recommended_*.png`, regen `--cull-pct 0`).
Gate PASS blocks 1.12 colors 2/3 rings 2.2/1.0/1.7 (starless-sky scope;
correction 2026-07-07: this line originally carried B5's gate numbers
"2/4, 1.9/1.4/1.9" by transcription — the byte-verified B6 artifact
itself measures 2/3, 2.2/1.0/1.7 PASS, re-confirmed against the
approved file at session-6 start); corridor REPORTED floor
**+5.0/−1.0** (B5-era geo: +6.2/−3.0), bands **0.73/1.25**
(B5: 1.16/2.31), no mask seam. **VERIFIED: the
defaults-only render is BYTE-IDENTICAL to the approved C3 files (max
diff 0, mean 0.0000)** — product:
`starcomb_set-03_APPROVED_B6_*.{jpg,png}` (+`_starless`). Superseded
loose renders pruned (C2, C3-tagged duplicates, M0a/M0b intermediates —
all regenerable by flags recorded above); C1 kept as the alternate.

## Session 6 (2026-07-07): data-generalization + bandaid removal

**Session mission (user):** make the pipeline DATA-GENERAL (a new session
of files must not break scripts tailored to set-03), remove remaining
bandaids (rgb_equal), root-cause the star ghost-aura, upgrade export
quality objectively, and build a blacks/bands candidate set for judgment.
Session start state verified: B6 defaults render byte-identical to the
approved artifacts (jpg + starless jpg + png all `cmp`-identical);
NOTES B6 gate line corrected (was carrying B5's numbers).

### A1 — hard-coded constant inventory (2026-07-07, every script read)

Classification: U = universal (algorithm/sanity, data-independent) ·
D = per-image DERIVABLE (from WCS/EXIF/data) · C = needs per-session
CONFIG (composition fact) · L = legacy-only (not in the product chain).

| # | location | constant | class | plan |
|---|---|---|---|---|
| 1 | astrometrics `BAND_P0/P1/HALFW` (single source; re-exported to starcomb, used by bg_qa `sky_signal_mask`, `corridor_report`, starcomb boost mask + `lum_core`/`chroma_core` sky scopes) | corridor (0.30,1.00)→(0.80,0.00) halfw 0.19 — HAND-MEASURED on set-03's framing | **D** (WCS → galactic-latitude band) + C override | A2: WCS-derived mask, config `corridor` |
| 2 | astrometrics `branch_mask`/`branch_mask_frac` (used by starsep never-star zone, star_metrics, corridor_report, chroma/lum_core noise scopes) | foreground rect y≥0.75h, x<0.22w | **C** (composition fact; data-derived candidate reported) | A2: config `foreground.rect`; absent → none |
| 3 | bg_qa `block_metrics` inline `mask[gy*0.75:, :gx*0.22]` | same rect, duplicated | **C** | A2: read from shared context (one source) |
| 4 | inspect_stage `post_subsky` inline `ys≥0.75, xs<0.22` | same rect, third copy | **C** | A2: shared context |
| 5 | astrometrics `plane_tilt` `(cy≥0.5)&(cx<−0.56)` | same rect in ±1 block coords | **C** | A2: shared context |
| 6 | astrometrics `corridor_report` seam strips at y=0.75h/x=0.22w (+0.05–0.20w, 0.78–0.97h sample bands) | seam gauges anchored to the branch rect | **C** (follows #2; gauges skipped when no foreground) | A2 |
| 7 | starcomb `MW_BOX`/`SKY_BOX` (0.40,0.30,0.70,0.55)/(0.05,0.25,0.25,0.50) + starsep MW readout box (same) | MW-contrast report boxes, set-03 framing | **D** (derive: densest in-corridor box vs farthest sky box) + C override | A2: derive from corridor mask |
| 8 | starsep `AREA_MAX` 1500 / `AREA_MAX_BRIGHT` 12000 px | component caps tuned on 8px-trailed 37mm stars | **U-ish with C escape** (px² does not scale with focal; safe shorter, risky longer focals) | config `starsep.area_max*` override; keep defaults |
| 9 | starsep `K_DETECT` 4σ, `K_PROM` 6σ, `K_BRIGHT` 40σ, `DILATE_ALL` 3 / `DILATE_BRIGHT` 5, `JACOBI_ITERS` 40, fill noise 0.7σ, rng seed | σ-relative detection/inpaint params | **U** (scale-free) — DILATE/0.7σ under D-stream (aura) scrutiny | leave; D-stream may re-derive |
| 10 | solve_field `SizeHint(26.0, 40.0)` arcsec/px + `scales={13..19}` | plate-solve scale hint — set-03's 32.78″/px only; **24mm set = 50.9″/px is OUTSIDE → solve would fail** | **D** (compute from EXIF focal + sensor pitch, widen envelope) | A2/A3: derive hint per stack; keep blind fallback |
| 11 | inspect_stage `EXPECTATIONS` bounds | per-stage WARN bounds calibrated on set-03 (some self-flat-specific: corner_gain 0.38–0.58, stack noise 1.2–2.2%) | **U as sanity envelopes** (WARN-only by design, never abort) | annotate set-03 calibration in table header; revisit per new data class |
| 12 | judgment_crops `CROPS` 4 fixed px boxes | session-5 defect zones on set-03 | **C** (defect zones are per-image) | config `judgment_crops`; absent → derived defaults (corridor center/edge, lefttop, foreground corner) |
| 13 | starcomb starless-jpg q92 (gate input!) + final jpg q92 | export encoding | starless q92 = **U frozen** (gate identity — never touch); final = C-stream ladder | C-stream |
| 14 | selfflat `BLOCK` 101 / `NBINS` 24 / `CLIP_SIGMA` 2.5 / `GUARD`, rechroma 75% guard | fit algorithm params | **U** | none |
| 15 | experiment.py chains (crop 150/250, RBF spec), run_post `M=150`, `SUBSKY_DEG` | legacy quick-look recipes | **L** | none (documented legacy) |
| 16 | 40_lights/40d `-rgb_equal` | stack-time WB | bandaid #3 | B-stream removal |

### A2 — pre-registered (2026-07-07): per-set context + WCS corridor

**Change:** introduce a per-set context loaded from
`<session>/config_<set>.json` (tracked in git — composition facts are
process, not image data): corridor (manual params | `wcs` mode with
`b_halfwidth_deg` | none), foreground rect (or none), report boxes,
judgment crops, optional starsep overrides. All geometry consumers (#1–#7,
#12) read the context. set-03's measured values MOVE into
`config_set-03.json`; the module-level constants become the no-config
legacy fallback ONLY for direct library calls on set-03-era artifacts
(product entry points all configure the context explicitly, and a set
with no config + no WCS gets corridor=None (gate falls back to
whole-frame scope on the starless render = stricter, warned), foreground
=None, boost skipped with a warning — NO silent set-03 inheritance).

**WCS corridor derivation:** pixel grid → RA/Dec via the injected TAN-SIP
WCS (numpy: CRPIX/CD + forward SIP; SIP terms ~arcmin at edges, kept
anyway) → galactic latitude b via the fixed J2000 ICRS→galactic rotation
matrix (no astropy) → corridor = |b| ≤ b_halfwidth. Hand-measured halfw
0.19·diag at 32.78″/px ≈ **12.6° galactic halfwidth** (first guess;
calibrated by overlap sweep).

**Hypotheses (validation on set-03, B6 render):**
1. With `config_set-03.json` carrying exactly the current constants, the
   B6 defaults render stays **byte-identical** (config == constants ⇒
   same masks ⇒ same pixels). HARD REQUIREMENT.
2. The WCS-derived corridor at the IoU-best halfwidth reproduces the
   hand-measured corridor: IoU ≥ ~0.75 expected (the hand corridor is a
   straight strip in frame coords; the galactic band is gently curved).
3. Swapping the derived mask into the GATE SCOPE on the byte-verified B6
   starless render leaves the verdict PASS (thresholds untouched; scope
   geometry shifts slightly). Gate-scope swap is validation-only this
   session — set-03's shipping config stays manual until the user
   approves any re-render.
If IoU lands far below or the gate flips, the derivation (or the 12.6°
guess) is wrong — investigate before any adoption, numbers into NOTES.

**A2 RESULTS (2026-07-07): all three hypotheses CONFIRMED.**
1. Context refactor byte-clean: every mask (band hard/feathered, branch
   hard/frac, sky scope) `np.array_equal` between builtin constants and
   `config_set-03.json`-sourced context; full B6 defaults re-render under
   the new code = **byte-identical** (jpg + starless jpg + png `cmp`).
2. WCS corridor: galactic b spans −26.9°..+30.4° over the frame (the
   plane crosses it, as it must in Cygnus). IoU vs the hand corridor
   peaks at **b_halfwidth 9.0° → IoU 0.776** (sweep 6°..17°, single
   smooth peak; 12.6° first-guess was too wide — the hand strip's 0.19
   diag halfwidth is anisotropic frame-fraction units, not sky degrees).
   Config + SetContext default set to the calibrated 9.0°.
3. Gate-scope swap on the approved B6 starless render: manual PASS
   1.12 / 2/3 / 2.2/1.0/1.7 → wcs-derived PASS 1.20 / 2/1 / 2.3/2.0/1.0
   — verdict unchanged, numbers move within thresholds as the scope
   geometry shifts. corridor_report in wcs mode: floor +5.0/−2.0, bands
   0.68/2.44 (l-binned axis instead of the strip projection — different
   binning, same story).
   **Overlay** (`results/wcs_corridor_overlay_set-03.png`): the derived
   band VISIBLY tracks the real MW course (incl. its gnomonic curvature)
   better than the straight hand strip. Adoption for set-03 = a render
   change → user approval; new sets default to wcs mode automatically.
   solve_field scale hint now derived from FITS FOCALLEN/XPIXSZ
   (hard-coded 26–40″/px would have made every 24mm solve fail).

### C — pre-registered (2026-07-07): final-export quality ladder

The B6 jpg ships at q92 with PIL's default chroma subsampling and is
MEASURED to cost mean 2.6 counts (max 242 at star edges, 32% of px >2)
vs the lossless PNG on this grain-heavy content. Ladder (objective,
pass/fail decided by numbers — the pixel DATA is unchanged, only the
encoding): q92 control (must byte-reproduce the approved jpg from the
PNG pixels — sanity), then subsampling=0 at q92/q95/q98/q100. Metrics
per rung: file size, mean |diff| vs PNG, max |diff|, %px>2, star-pixel
chroma diff (subsampling's main victim). **Decision rule (pre-registered):
adopt the cheapest rung with mean ≤ 0.5 counts AND %px>2 ≤ 2%;** PNG
stays the canonical final regardless; the approved q92 artifact stays
reproducible via an explicit --jpg-quality/--jpg-subsampling override.
Hypothesis: subsampling=0 alone kills most of the star-edge max error;
q98+ brings the mean under 0.5; q100 ~ lossless-adjacent at ~2-3x q92
size.

**C RESULT (2026-07-07): q100 + subsampling=0 adopted (only rung meeting
the pre-registered bar).** Vs the canonical PNG pixels (control q92 +
default 4:2:0 byte-reproduces the approved jpg ✓ measurement chain
sound):

| rung | MB | mean err | max | %px>2 | star-px chroma err |
|---|---|---|---|---|---|
| q92 sub=4:2:0 (B6 control) | 6.9 | 2.291 | 176 | 27.3 | 9.68 |
| q92 sub=0 | 8.7 | 1.963 | 47 | 25.7 | 6.83 |
| q95 sub=0 | 11.9 | 1.489 | 34 | 17.7 | 4.54 |
| q98 sub=0 | 18.1 | 0.823 | 13 | 4.2 | 1.95 |
| **q100 sub=0** | **29.7** | **0.437** | **5** | **0.72** | **0.69** |

Chroma subsampling alone was the star-edge killer (max 176 → 47).
Baked as the starcomb final-jpg default (`--jpg-quality 100
--jpg-subsampling 0`); the approved B6 q92 artifact reproduces with
`--jpg-quality 92 --jpg-subsampling -1`. The STARLESS jpg (gate input)
is untouched at q92 — its encoding is part of the gate identity. PNG
(`--lossless`) stays the canonical final.

**C USER VERDICT (2026-07-07): "those uncompressed versions are really
good. they look pretty sharp"** — the q100/4:4:4 + 16-bit-PNG export
upgrade is confirmed by eye, not just by the diff numbers.

**C addendum — full lossiness inventory (2026-07-07, user asked for
finals as close to lossless as possible).** Product pixel path audited
end-to-end: float from the 32-bit stack through every op (the q92
starless jpg is gate INPUT only, never product). The three real cuts:
(1) JPEG encoding — ceiling reached at q100/4:4:4 (mean 0.44, max 5;
JPEG is 8-bit + DCT by construction, cannot go further); (2) 8-bit
export depth — the render is float, 8-bit keeps 256 levels: `--lossless`
now ALSO writes a **16-bit PNG** (`*_16bit.png`, 65536 levels quantized
straight from the float render; dependency-free writer in astrometrics
`write_png16`, roundtrip verified bit-exact — Pillow cannot write
48-bit RGB PNGs) next to the byte-verification 8-bit PNG; (3) 16-bit
integer calibrated intermediates (disk constraint): quantization step
≈ 18× below per-frame noise σ → ~+0.3% stack noise in quadrature —
negligible, documented. NOTE for D-stream: 4:2:0's
9.7-count star-pixel chroma error + DCT blocking at q92 is itself a
"pixeled aura around stars" candidate — the D measurement must run on
the PNG to separate encoding artifact from pipeline artifact.

### D — pre-registered (2026-07-07): star ghost-aura root cause

User issue 3 (session 5): zoomed in, stars show a pixeled ghost
ring/aura (streaks fine). MEASURE FIRST on the pixel-true PNG, then the
q92 jpg (encoding candidate), against the no-separation raw stretch of
the same stack. Method: median luminance annulus profile r=0..40 px
around a mid-bright star sample (starsep catalog ranks ~100-500, cores
unsaturated), on (a) B6 PNG, (b) B6 q92 jpg, (c) consistent autostretch
of the SPCC stack (no separation — the control that never saw
mask/inpaint), plus the layer decomposition (starless_st, stars_st
contributions). Suspects in order (from the separation architecture):
(1) starsep hard dilated mask boundary (DILATE_ALL 3 / +5 bright): an
annulus of inpaint fill + 0.7σ matched noise whose texture diverges
from the vstpost-denoised surroundings; (2) the stars-layer MTF
(anchor 0.97 ⇒ huge low-end gain) amplifying the fill-residual inside
the dilation annulus into a plateau that ends at the mask cliff;
(3) q92 4:2:0 DCT blocking (encoding, killed by C). Discriminators:
a plateau-then-cliff at the mask radius in the stars-layer profile ⇒
(2); a texture/level step at mask radius in the starless profile ⇒
(1); aura present in jpg but absent in PNG ⇒ (3).

**D ROOT CAUSE (2026-07-07, measured on the pixel-true PNG — annulus
profiles, 300 mid-bright stars ranks 100-400 + 70 bright ranks 10-80):**
The ghost aura is the STARS-LAYER SKIRT ANNULUS (core → dilated mask
edge), three stacked amplifiers + one encoder:
1. stars-layer MTF (anchor 0.97 ⇒ huge low-end gain) lifts subtracted
   PSF-wing luminance to **+7 (bright tier, r=12) / +11 (mid tier, r=8)
   counts over background vs +0.5 / +3 for the raw no-separation
   stretch** of the same stack;
2. the same gain × satu lifts the skirt's subtraction-noise chroma to
   **MAD 20-30 counts at r=4-10 vs 6 for raw** — the visible COLORED
   SPECKLE SHELL;
3. both terminate at the mask cliff against a starless layer whose
   texture is far smoother than raw (chroma MAD 1.5 vs 5.9) —
   maximum perceptual contrast ⇒ reads as a ring;
4. q92 4:2:0 JPEG adds DCT blocking + 9.7-count star-pixel chroma error
   on top = the "pixeled" quality (KILLED by C: q100 subsampling=0).
The starless layer itself is CLEAN (level ring ≤ +0.7 count): the
inpaint+matched-noise annulus (suspect 1) and cull-50 patches are NOT
the level/chroma driver. Dark ring: −1 count = negligible.

**StarNet-on-aarch64 feasibility (2026-07-07 re-check, bandaid #5
removal condition):** still NO Linux aarch64 build (v2.5.3, 2026-06-27)
— BUT StarNet's current packages moved from TensorFlow to **self-
contained ONNX Runtime** on Linux/Windows/macOS-x64. onnxruntime wheels
for linux-aarch64 py3.13 EXIST (1.20–1.27, verified installable here).
Concrete route next session: download the official Linux x64 CLI
package, check it ships a loose readable .onnx (vs embedded in the
binary — the go/no-go), then a small tiled-inference driver (256px
tiles, the nekitmm/starnet protocol) on the aarch64 wheel. If the model
is embedded/encrypted: dead end, mask+inpaint stays. Landing this
retires starsep's ADAPTATION entirely. Sources:
https://starnetastro.com/cli-tools/starnet/ ·
https://starnetastro.com/release-notes/ ·
https://github.com/nekitmm/starnet

**D fix ladder (pre-registered): `stars_floor` 0 (control) / 1.5 / 3.0.**
Subtract k·σ_c (per-channel linear sky noise measured on the linear
starless layer) from the stars LINEAR layer before its MTF — skirt
residuals below the noise floor stop being amplified; genuine star
signal (amplitude ≫ kσ) passes. Prediction: bright-tier aura lum
+7 → ≤ +2 at r=12; skirt chroma MAD 20-30 → < 10; top-100/mid star
peaks UNCHANGED (anchor comes from the catalog, floor ≪ star
amplitudes); gate bit-identical (starless untouched). Risk owned by the
user: the faintest stars (amplitude ~ kσ) lose their skirts and may
read "cut out" — judgment panels decide. Fallback rung if the cliff
still shows after flooring: feathered combine at the mask boundary.

**D LADDER RESULT (`exp_starsep_stars_floor_20260707_005345`):
CONFIRMED — the floor kills the aura, cores untouched, gate
bit-identical.** Bright-tier (ranks 10-80) annulus metrics per rung:

| stars_floor | aura lum (r12-25 − base) | skirt chroma MAD (r6-10) | core | halo ratio | gate |
|---|---|---|---|---|---|
| 0 (B6) | **+7.0** | 24.5 | 248.5 | 1.73 | PASS 1.12/2.2/1.0/1.7 |
| 1.5 | **+1.5** (prediction ≤2 ✓) | 21.5 | 248.5 | 1.54 | bit-identical PASS |
| 3.0 | +2.0 | **13.3** | 248.5 | 1.41 | bit-identical PASS |

Star mid-peak 248 / sat 6% at every rung (cores untouched ✓ anchor is
catalog-derived). The chroma-MAD floor (~13 at r6-10, k=3) is the
HONEST trailed-PSF/atmospheric-dispersion fringe — flooring removes the
noise speckle, not real star color (the "<10" prediction was half
wrong: it assumed all skirt chroma was noise). MW box 6→6→5 (k=3 shaves
faint-star skirt flux inside the MW box; reporting artifact, the
starless MW is untouched). Panels: `judge_star_tiles.png` (5 star
ranks × 3 rungs, 3× zoom — the speckle shell visibly gone at 1.5,
clean at 3.0) + full strips. **USER JUDGES k (0/1.5/3.0); nothing
baked.** The mask-cliff fallback (feathered combine) was NOT needed at
the level metric; park it.

### A3 RESULT (2026-07-07): the lights set ran END-TO-END — generalization proven

`scripts/run_pipeline.sh 07-02-26` → solve → SPCC → starcomb, zero
script edits during the runs; every failure fixed as a PROCESS fix:
1. **Pipeline (matched-flat path)**: preflight routed correctly, self-flat
   chain stayed dormant, masters rebuilt (manifests were missing), 31/32
   registered (frame 2 = the known unmatchable), stack built. Stage WARNs
   were all honest data statements: stack radial p2v 0.82 (the moon-glow
   ring, not a flat failure), post_subsky block spread 40x (the treeline
   was unmasked until config_lights.json existed).
2. **Process fixes exposed (all data-general, none set-03-specific):**
   solve_field star-window clipping at frame edges (mgrid/data shape
   mismatch crash); venv bootstrap re-exec check (realpath of the venv
   python symlink == system python → "already inside" while outside;
   fixed via sys.prefix); hard-coded solve scale hint (26–40″/px could
   never solve a 24mm field — now derived from FOCALLEN/XPIXSZ);
   foreground detection: binary_closing erosion eats border pixels →
   border-BAND test; and the composition itself demanded a pixel-MASK
   foreground (treeline arc — a rect can't model it): new
   `suggest_foreground.py` + mask support in the context (EDT feather).
3. **Solve**: RA 227.209° Dec +45.187°, 48.89″/px, logodds 115 —
   **Boötes** (the session-1 "Big Dipper area" label belonged to THIS
   composition; solved only after foreground-masked star detection —
   treeline/glow peaks poisoned the matcher before).
4. **SPCC**: 518 matched stars (needed 8 more xpsamp chunks — nside=2
   cone-cover computed in numpy, validated by reproducing set-03's
   11-chunk list exactly; ~1.2 GB added).
5. **starcomb**: full chain ran; corridor honestly EMPTY (no |b|≤9°
   pixel in a Boötes frame) → mw_boost auto-skipped, MW contrast NaN,
   floor/seam metrics null; **gate reported an honest FAIL** (blocks
   6.64 — p95 106 vs p50 16: the moonlit horizon-glow band above the
   treeline survives BGE+subsky; rings 10.1; colors 28/22). That is the
   DATA (glow-dominated composition), not a pipeline break — exactly
   what the gate exists to say. Render `starcomb_lights_a3proof_*.jpg`:
   dark star-rich sky, 3321 stars (elong 1.48 — 20s at 24mm sits at the
   rule-of-500 limit), treeline glow band + reddish high-noise corners
   as the visible residuals. Follow-ups if this set ever becomes a
   product: treeline-aware background model, corner chroma.

### B — pre-registered (2026-07-07): rgb_equal removal (bandaid #3)

Catalogs reinstalled (7.4 GB: astro + 11 Cygnus chunks + 8 Boötes
chunks). Change: drop `-rgb_equal` from both stack templates (40_lights,
40d) — ONE architectural knob. Verification on set-03: re-stack
(preserve the current canonical as `stack_set-03_rgbeq.fit`), re-solve +
re-SPCC the new stack, render with B6 defaults, compare: SPCC K factors
(expect K_G to move from 0.904 toward ~1 — SPCC absorbing the raw
balance instead of the pre-scaled one), MW contrast (expect ≈ +35.9
linear ± the K change), gate + corridor report vs B6, judgment panels
for the user (a render-affecting change — canonical stack does NOT
switch without the user's eyes). If anything degrades measurably: dead
end with numbers, annotation restored. Note the stack rebuild also
re-runs registration (sweep is deterministic given the same frames) —
byte-identity of the new stack vs old is NOT expected (independent
build); the comparison is metric + visual.

**B RESULT (2026-07-07): rgb_equal is OUT — SPCC absorbs the full raw
balance; nothing degrades at the gate; user judges the render pair
before the canonical stack switches.**
- Re-stack clean: sweep ref 11→20/21, ref 12→**21/21** (same as
  history); stack inspect PASS noise/med 1.30%, p2v 0.048; rgb_equal-era
  stack preserved as `stack_set-03_rgbeq.fit`.
- Solve identical (RA 312.945 Dec +48.148, 32.78″/px, logodds 361).
- **SPCC on the RAW stack: 508 stars, K ≈ R 1.675 / G 0.749 / B 0.935**
  (recovered as post/pre medians). The pre-registration guessed "K_G
  0.904 → ~1" — WRONG in magnitude: rgb_equal was not a small tweak, it
  was the primary raw-Bayer-balance normalizer (G ~2× sensitive); SPCC
  is designed to do exactly that job itself, which is why the removal is
  architecture-correct.
- Linear: MW box +31.5 (rgbeq-era: +35.9 — different global norm, see
  render), rim_dev +6.4% (was +8.2%), rim R−G −7.2 (was −9.0) — rim
  IMPROVES.
- **Render (B6 defaults): GATE PASS blocks 1.12 colors 2/2 rings
  3.2/1.2/1.1** (B6: 1.12, 2/3, 2.2/1.0/1.7 — all far under limits;
  ring_l +1.0 = independent stack build + fresh separation, watch it,
  don't hide it). Corridor floor +5.0/−2.0, bands 0.60/1.33 (B6:
  +5.0/−1.0, 0.73/1.25). MW render contrast 5.0 vs 6.0. Stars: mid 248
  vs 255, sat 6.0% vs 14.6% — the fresh separation on the differently-
  normalized stack shifts the anchor's amplitude distribution → bright
  tail renders slightly dimmer; visible in panels, user judges (a
  stars_peak re-ladder on the new stack is the knob if wanted).
- Panels: `results/judgment_B_norgbeq/` (B6_approved vs no_rgbeq, 4
  zones). Files: `starcomb_set-03_norgbeq_20260707_*.{jpg,png,_16bit.png}`,
  stack `stack_set-03_norgbeq_spcc.fit`.
- **Templates edited** (40_lights + 40d): `-rgb_equal` dropped with a
  plain standing comment; the lights A3 stack predates this change
  (built WITH rgb_equal — inert under its SPCC; rebuild optional).
- CANONICAL SWITCH PENDING USER: on approval, `stack_set-03_norgbeq_spcc.fit`
  becomes the render input (and the B6 byte-verify target re-anchors to
  the newly approved render); until then B6 remains the approved product
  on `stack_set-03_spcc.fit`.

### E — pre-registered (2026-07-07): blacker blacks (output black point)

User issue 2: background should be BLACK (sits at ~16/255 by
construction, autostretch target 0.07) without losing star/MW glow;
residual gray patches 1.5/2.4/1.3 counts at 16/48/128 px and bands
0.73/1.25 remain. There is NO output-levels op in the chain today; the
industry move is an output black point (levels) — LINEAR, linked (no
cast change), applied to the STARLESS layer AFTER the boost and BEFORE
the gate jpg (so the gate + corridor metrics SEE it — no hiding):
out = (x − b)/(1 − b). Linear shift preserves differences (MW box
contrast should survive ~unchanged, scaled ×255/(255−b) ≈ +3%);
everything below b clips to true black — that is the point for the sky,
and the RISK for the corridor (the boost lifts glow ABOVE bg, so
corridor pixels should sit above b — measure, don't assume).
**Ladder `black_point` b = 0 (control) / 4 / 6 / 8 (8-bit counts);
bg 16 → ~16/12/10/8.** New reported numbers per rung: corridor
clip0 fraction (glow pixels driven to 0 — must stay ≈ 0) vs sky clip0
fraction (growing = blacker blacks working), floor/bands, MW contrast,
gate. AESTHETIC: judgment panels per rung, USER DECIDES; nothing bakes.
lum_core/chroma_core re-ladder only if patches/bands still show at the
approved black point (deferred).

**E RESULT (`exp_starsep_black_point_20260707_013304`): every rung
gate-PASS with the MW/glow untouched by measurement; one prediction
inverted, instructively.**

| b | bg | gate blocks | rings | corridor clip0 | sky clip0 | MW | floor P50 |
|---|---|---|---|---|---|---|---|
| 0 | 16 | PASS 1.12 | 2.2/1.0/1.7 | — | — | 6.0 | +5.0 |
| 4 | 12 | PASS 1.17 | 2.3/1.3/1.3 | 9.3% | 0.01% | 6.0 | +5.0 |
| 6 | 10 | PASS 1.20 | 2.4/1.3/1.0 | 12.1% | 0.23% | 6.0 | +5.0 |
| 8 | 8 | PASS 1.25 | 2.4/1.3/1.0 | 15.6% | 1.05% | 6.0 | +5.0 |

The clip0 prediction was BACKWARDS: the corridor scope is 42% of the
frame and includes the dark gaps/lanes + boost-amplified grain's low
tail — ITS pixels clip (9–16%), and that clipping is the user's
requested effect (gaps at true black); the lum-cored SKY is so smooth
that almost nothing in it reaches b (0.01–1%) — the sky gets uniformly
DARKER (16→8) rather than crushed. The signal metrics prove glow
survival: MW contrast 6.0, floor P50 +5.0, bands 0.7/1.2–1.3 at every
rung; blocks ratio drifts 1.12→1.25 purely because P50 drops (P95/P50
arithmetic), rings stay ≤2.4. Stars bit-stable (mid 248, sat 6%).
Panels: `exp_starsep_black_point_*/judgment/` (4 zones × 4 rungs).
**USER PICKS b (0/4/6/8); nothing baked.** If the user wants sky at
TRUE 0, b must exceed the sky floor (~13) — that would clip real sky
texture; the honest route there is more integration, not a deeper clip.

### Bandaid ledger — session 6 refresh (THE CURRENT LEDGER; session-5 list superseded)

1. **Self-flat chain** — ADAPTATION, unchanged. Dies when real flats
   exist at the set's focal (preflight auto-routes; the matched-flat
   path was exercised end-to-end by the lights set this session ✓).
2. **Per-frame `seqsubsky 1`** — ADAPTATION, unchanged (self-flat
   branch only; dies with real flats).
3. **`rgb_equal`** — **REMOVED from both templates** (B). SPCC absorbs
   the full raw balance (K R 1.675 / G 0.749 / B 0.935, 508 stars);
   gate PASS with equivalent numbers. Fully closed once the user
   approves the norgbeq render pair and the canonical stack switches.
4. **Whole-frame QA on the recombine** — reported reference only
   (unchanged since the ratified scope change).
5. **Star separation by mask+inpaint** — ADAPTATION. Removal condition
   now CONCRETE: StarNet ships self-contained ONNX packages (no aarch64
   build, but onnxruntime aarch64 wheels verified installable) — next
   session: check the Linux x64 package for a loose .onnx; if readable,
   a tiled-inference driver retires this. Its measured aura cost has a
   working fix meanwhile (stars_floor ladder, D — awaiting user's k).
6. **Denoise** — post-stretch `-vst -mod=0.5` on the starless render is
   in the approved chain; linear placements remain a measured dead end
   on self-flat data (unchanged).
7. **Crop** — eliminated (unchanged).
8. **Hard-coded set-03 geometry in scripts** — **CLOSED (A1/A2)**:
   corridor/foreground/boxes/crops live in `config_<set>.json` or derive
   (WCS galactic corridor; suggest_foreground mask); no silent set-03
   inheritance (corridor=none + warning when nothing is available).
   set-03's manual corridor stays config'd for byte-identity; the
   validated WCS corridor (IoU 0.776, gate-equivalent) awaits user
   approval since switching re-renders.
9. **Flat geometric mw_boost** — luminosity-weighted mask (unchanged);
   removal condition still "enough integration next acquisition".
10. **Legacy quick-look named `preview_*`** — renamed `quicklook_*`
    (was repeatedly mistaken for the product render).

## Iteration ideas (not yet tried)

(Pruned 2026-07-06: GraXpert BGE, photometric color calibration, post-stretch
denoise and star separation/recombination all graduated into the chain.)

- Registration with distortion handling (24mm wide field, corner stars)
- `-filter-wfwhm` / `-weight_from_wfwhm`: no-op for THIS session (FWHM spread
  ~6%) — revisit when a session has variable seeing/clouds/wind
- Drizzle (probably not: undersampled? no — 24mm @ 5.9µm is heavily oversampled
  spatially, skip)

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
