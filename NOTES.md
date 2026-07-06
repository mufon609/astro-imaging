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
   `denoise -vst` → `autostretch -linked -2.8 0.10` → `rmgreen` → `satu 0.3`
   → `preview_<set>_<timestamp>.jpg`. Iterate standalone:
   `scripts/run_post.sh <session> [set] [subsky-degree]` (denoise costs
   ~3 min — comment it out in the tmpl when iterating on gradients only).

Diagnostics: `diag_flat.ssf` (stretched master-flat check → JPEG); stack stats
print in every post run. Record stack median + bgnoise **before and after every
change** and compare noise/median — output normalization rescales levels when
the reference frame changes, so raw bgnoise numbers across runs are not
comparable.

Masters live in `<session>/work/masters/` and are **rebuilt automatically**
when any source DNG is newer than the master (drop in re-shot frames and just
re-run). Big FITS results are overwritten per set (`results/stack_<set>.fit`);
small timestamped JPEG previews accumulate for run-to-run comparison.

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
| `preview_set-03_20260706_<final>` | + gray V + post subsky 2 (chroma cleanup) | **keeper** — flat luminance ±9%, corner red tint neutralized by per-channel degree-2 curvature fit, 21/21 frames, MW intact |

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
