# Astrophotography processing pipeline — lab notebook

This file is the **current truth**: what the pipeline is, why every
knob has its value (measured), and the dead-end registry (what was
tried, what number killed it — NEVER re-attempt these). The full
chronological history — every experiment arc, superseded recipe and
session narrative — lives in **git** (`git log`, and every commit
carries the NOTES of its time; recipe tags: `B5-approved`,
`B6-approved`, `B7-approved`). `README.md` is the process contract
(standard-workflow mapping, review contract, experiment discipline,
per-set geometry, north star). Update THIS file as states change;
never let it grow narrative again.

## STATUS (2026-07-07)

- **Approved recipe: B7** (git tag `B7-approved`; defaults
  byte-reproduce it). B6/B5 are HISTORY — explicitly not approved and
  superseded by B7; their renders and stacks are pruned, the record lives
  in git (tags `B5-approved` / `B6-approved`).
- Reproduce before touching anything:

      python3 scripts/render/starcomb.py 07-02-26 set-03 \
          --stack 07-02-26/results/stack_set-03_norgbeq_spcc.fit --lossless

  Expected: gate (starless-sky) PASS blocks 1.375 (P5/P50/P95 = 5/8/11)
  colors 2/2 rings 3.0/1.3/1.2 · corridor floor +4.0/−3.0, bands
  0.6/1.2 · black_point clip0 corridor ~16.2% / sky ~1.2% · star shells
  aura_lum +2.0 (WARN >4.0), shell_chroma ~28.9 (trend) · stars anchor
  0.0284 → m 0.00090 (low-end gain ×996) · all four artifacts
  byte-identical to
  `results/starcomb_set-03_APPROVED_B7_20260707_103839.{jpg,png,_16bit.png,_starless.jpg}`.
- Last audited 2026-07-07: byte-reproduce 4/4 cmp-identical; star-shell
  audit fires by measurement (B6 defect record aura +12.0 WARN / B7
  +2.0 clean, shell_chroma 16.7/28.9, newest starsep catalog); gate
  scope = config_set-03.json geometry; artifact spot-checks — jpg
  q100/4:4:4 vs PNG mean 0.41/max 5 (table: 0.44/5), PNG16→PNG8
  requantize max diff 0.
- **The `lights` set is NOT approved** (user verdict: "massive issues -
  just different quality issues") — it is the generalization testbed
  only. Its stacks/renders were pruned; regen:
  `scripts/stack/run_pipeline.sh 07-02-26 && solve_field + spcc` (catalogs
  installed).
- **Open queue (payoff order):** TWO USER JUDGMENTS PENDING —
  (1) `sep_engine hybrid` adoption (ledger #4: all objective bars
  met, panels in `results/exp_starsep_sep_engine_20260707_125122/
  judgment/`); (2) `stars_anchor noise` default flip (ledger #7:
  drift mechanism killed in synthesis, canonical render reproduced;
  acceptance = byte-compare at flip). Then: lights-set data-general
  process fixes (treeline-aware background, corner chroma) if that
  set ever matters; **next acquisition (see checklist) — worth more
  than all remaining processing work combined.** SPCC K-factor
  auto-capture: DONE (`spcc_run.py`, 2026-07-07; canonical K
  R1.000/G0.656/B0.837, spcc rerun pixel-deterministic).
- Optional, unapplied: WCS-derived corridor for set-03 (validated
  IoU 0.776 vs the hand strip, gate-equivalent; switching re-renders →
  needs user approval; new sets already default to it).

## Environment

Rig/tooling facts live in **`CLAUDE.md`** (git-tracked, auto-loaded
into agent sessions): flatpak siril invocation + the /tmp rule,
hardware/disk constraints, python stack (no astropy), GraXpert,
astrometry venv, local Gaia catalog layout. Catalog chunk state as of
2026-07-07: astro + SPCC xpsamp {2,3,5,7,8,9,10,11,12,13,14,15,19,25,
27,29,30,31,43} = the Cygnus + Boötes cones (7.4 GB); SPCC needs the
FULL cone; the nside=2 nested cone-cover is computable in numpy
(validated: reproduces the Cygnus 11-chunk list for the 33.5° cone at
312.77,+48.16). Camera: Nikon Z6 III, raws → DNG (Adobe DNG Converter
18.4), 14-bit RGGB.

## Data (session 07-02-26)

| set | frames | optics | field (blind-solved) | calibration | path |
|---|---|---|---|---|---|
| `set-03` | 21×25s ISO200 | 37/38 mm f/4 (mid-set 1 mm EXIF step) | **Cygnus** — RA 312.77° Dec +48.16°, 32.78″/px, Deneb near center | darks matched, **no flat at this focal** | self-flat branch |
| `lights` | 32×20s ISO200 | 24 mm f/4 | **Boötes** — RA 227.21° Dec +45.19°, 48.9″/px (the session's old "Big Dipper" label belonged HERE, not set-03) | darks+biases+flats matched | matched-flat path |

Calibration frames (re-shot 2026-07-05): darks 40×20s (mean ≈ bias:
hot-pixel map is the win), biases 98×1/160s (= exact flat-darks),
flats 100×1/160s (~27% of full scale — under the ~50% goal; the
MacBook-screen grid shows at ~0.3% RMS: harmless at these SNRs,
avoidable — see checklist). Sensor offset ≈ 1008 ADU. set-03 sky bg
~57 ADU above offset: heavily underexposed (ISO 200 is below the
Z6III's second gain stage) — corridor signal/grain ≈ 1 at 8.75 min;
**quality is exposure-limited, not process-limited.** Stars are
uniformly elongated by in-exposure trailing (25s ≈ 2× rule-of-500 at
38 mm): the crispness ceiling, not misregistration.

## Current design (each piece carries its measured WHY)

**Stack builder (`run_pipeline.sh`)** — preflight (exiftool): hard-fail
on empty/mixed frame dirs; flats used only when flats+biases exist AND
optics match the set, else self-flat path. Masters rebuild on manifest
change (names+sizes+mtimes — catches re-shot frames with old
timestamps). Calibrate `-dark -cc=dark` (+flat +equalize_cfa when
matched) → `setfindstar -sigma=0.5` (~870 vs ~370 stars/frame: the
matcher needs the extra triangles) → two-pass register → 32-bit
rejection stack, `-norm=addscale -output_norm`, **no rgb_equal** (SPCC
calibrates the raw balance directly; it measured K R 1.675 / G 0.749 /
B 0.935 on 508 stars — rgb_equal was the primary raw-Bayer normalizer
and only obscured what SPCC measures).

**Self-flat branch (flatless sets)** — median of UNREGISTERED
calibrated frames (drifting stars self-reject) → per-frame planar glow
subtraction (`seqsubsky 1`, sensor coords, while linear) → `rechroma.py`
shifts R/B medians to model-consistent targets C_c·median(V) (constants
only — cannot create spatial structure; without it siril's per-channel
level restoration prints a magenta rim, R−G +148 at the stack rim) →
V2 gain fit from the median of the frames ACTUALLY being divided
(`selfflat.py`: 101px block grid, 2.5σ clip, **binned radial medians +
isotonic non-increasing regression, GRAY** (channel-mean)) → divide →
**registration reference sweep** (mid-sequence outward, keep best,
early-stop: with trailed stars matching is reference-dependent —
measured 11→19/21, 12→21/21, 2-pass auto-pick→18/21) → stack. WHY the
odd pieces: polynomial V oscillates and prints RINGS (radial profile
54→31→54→6); per-channel V tints corners (glow contaminates per-channel
falloff); V estimated from glow-subtracted frames breaks the
pedestal/bowl ratio (0.61/0.37/0.47 vs true 0.52–0.56); the "right" V
lies between the multiplicative (0.537 corner → −16% rim) and additive
(0.472 → +7% rim) fits, so only the empirical V2 of the actual frames
lands flat (rim_dev 0.175→0.067). Per-frame `seqsubsky 1` must stay on
this branch: stack-level-only BGE measured gate FAIL 4.8 vs 2.7 + MW
loss (+0.7 vs +2.6 at bgelin).

**Plate solve (`solve_field.py`)** — blind astrometry.net on 200
coarse background-subtracted PEAK centroids (starsep blob centroids and
siril's PSF detection both fail to feed the matcher on trailed stars;
siril's internal solver caps its online cone at ~2.5° and fails
matching these ultra-wide fields even with local catalogs). Scale hint
derived from FOCALLEN/XPIXSZ in the header (a hard-coded range can
never generalize across focals). Foreground-masked detection (treeline
tips/glow edges poison the matcher — a treed field solved only after
exclusion). TAN-SIP WCS injected for siril `spcc`.

**Per-set geometry (`config_<set>.json` + `astrometrics.configure`)** —
corridor (manual | wcs: galactic |b| ≤ 9.0°, calibrated IoU 0.776
against set-03's hand-measured strip with the gate verdict unchanged |
none+loud warning), foreground (rect | pixel mask from
`suggest_foreground.py` — threshold 0.4×sky-median ≈ −42σ,
border-band-anchored components, dilated for the drift-smear halo |
none), report boxes and judgment crops (config or derived from the
corridor). A configless+WCSless set gets corridor NONE (gate degrades
to whole-frame on the starless render = stricter) and mw_boost skips —
**no set ever inherits set-03's masks silently.**

**Product chain (`starcomb.py`, defaults = B7)** on the SPCC stack:
1. GraXpert BGE + `subsky 1` on the STAR-FUL linear (the only
   MW-safe order: BGE on starless erases the MW, +38 → +0.4 linear).
2. `starsep.py` mask+inpaint separation (no aarch64 StarNet): local-bg
   detection 4σ, component prominence 6σ, area caps (config-overridable
   px² values), dilate 3 (+5 bright), pyramid-seed + Jacobi inpaint,
   matched fill noise 0.7σ, deterministic seed; catalog saved for
   culling. Cost owned: the <6σ faint tail stays in the starless layer
   (physical floor — prominence 4/5/6 all measured ~5.1k residual
   detections, the "stipple" is noise-level clumping).
3. Starless: **linked** autostretch −1.5 **0.07** → post-stretch
   `denoise -vst -mod=0.5` → chroma_core 4 (pre-boost) → lum_core 2 →
   mw_boost 1.2 on the luminosity-weighted corridor mask →
   black_point 8. The gate jpg (q92, frozen — gate identity) is
   written HERE, before the combine.
4. Stars: cull 50 (< p50 flux) → stars_floor 3.0×σ → gray MTF anchored
   so the median top-500 amplitude renders at 0.97.
5. Screen combine → satu 0.2 → jpg q100/4:4:4 (+ PNG8 + PNG16 with
   `--lossless`).

**Knob provenance (every value from a measured single-knob ladder):**

| knob = value | the number that set it |
|---|---|
| SPCC (not rgb_equal) | K R1.000/G0.656/B0.837 (R-normalized; raw G runs ×1.5 hot — the Bayer imbalance rgb_equal used to hide) · 509/2850 stars kept · gate equivalent · rim chroma improves (−9.0→−7.2). Captured by `spcc_run.py` (work/spcc_<set>.{json,log}); rerun on the canonical stack is pixel-IDENTICAL (spcc deterministic). An older grep-lost triple (1.675/0.749/0.935) does not reproduce — trust the json |
| bge_first order | MW +38 survives star-ful BGE; starless BGE kills it (+0.4) |
| linked stretch | unlinked = per-channel noise → chroma blotches (the "rainbow" engine); on a calibrated stack linked PASSES (2.8/1.2/1.8) and cuts blotches ~12% at source |
| starless_target 0.07 | sky rim is real: 0.12 → sky rings 4.4 FAIL (corridor-masked scope) |
| vstpost -mod=0.5 | every linear denoise placement imprints a radial signature on self-flat data (5.1/4.6 FAIL); post-stretch half-mod: grain −40%, gate clean |
| chroma_core 4, pre-boost | bands 0.73/1.25 (k=3: 1.08/1.88); pre-boost halves the boosted-noise coloration; star-color cost −1% on the linked chain |
| lum_core 2 | gray patches (stretch-amplified lum noise ±2 counts) removed; blocks 1.20→1.12; NO geometric foreground factor (a hard rect printed a 4.5× texture seam; the Wiener gate already protects real structure) |
| mw_boost 1.2, lum mask | boost is corridor-contained (gate bit-identical at any k); the flat geo mask lifted noise floor AND darkened the darkest blocks (P5 −3.0 vs lum −1.0); k is aesthetic |
| black_point 8 | user "blackest": bg 16→8; corridor clip0 16.2% = the requested gap blackness; sky clip0 1.2%; MW box contrast + floor P50 survive (linear shift preserves differences) |
| stars anchor 0.97 | mid-peak 255 vs 225 at 0.85; layers decoupled (gate untouched). CAVEAT: the catalog anchor is data-dependent → low-end gain drifted ×864→×996 between builds of the same sky; measured mechanism = per-channel gain (catalog mode −8.5/−20 counts mid/faint G drift under the SPCC K set vs noise mode ≤0.6 — see ledger #7; `--stars-anchor noise` ready, default-off) |
| stars_floor 3.0 | ghost-aura fix: bright-tier aura +7.0→+2.0 (raw stretch = +0.5), halo 1.73→1.36, cores/mid-peak untouched, gate bit-identical |
| cull 50 | metric-invisible; user's max-removal pole (the alternate cull-0 faint-field look remains a flag away) |
| satu 0.2 | fringe span scales ~(1+s): 79/94/107 for 0/0.2/0.35; 0.2 keeps star color at −12% fringe |
| jpg q100/4:4:4 | q92+4:2:0 cost mean 2.29 / max 176 counts at star edges / 9.7 star chroma (part of the "pixeled aura"); q100/4:4:4 = mean 0.44 / max 5; PNG8 = byte-verify artifact; PNG16 = the float render at 65536 levels (writer roundtrip-verified) |

**Standing per-render audits (printed + logged every starcomb run):**
the GATE (`bg_qa --sky-scope` on the starless render: blocks P95/P50 ≤
1.6, colors ≤ 7, rings ≤ 4 — **thresholds never loosen**; corridor +
foreground masked as known signal/non-sky); whole-frame QA as reference;
`corridor_report` (floor Δ, along-band chroma P2V, seam texture);
`star_shell_report` (aura_lum WARN > 4.0 — calibrated fixed +2.0 vs
defect +12.0 on the same star sample; shell_chroma is a TREND, no bound
— honest PSF fringe dominates it and a fixed bound cried wolf on the
approved render); black_point clip0 corridor/sky; stars anchor + MTF
low-end gain (drift watch); star metrics; MW box contrast.

## Per-stage expectations (inspection contract)

Mirrored in `inspect_stage.py EXPECTATIONS` (keep in sync). WARN-only —
inspection never aborts; the hard gate stays `bg_qa.py`. Bounds are
sanity envelopes calibrated on set-03 (some self-flat-specific); a new
data class may WARN legitimately — revisit bounds there, don't ignore.

| stage | PASS bound (short) |
|---|---|
| calibrated | bg median16 100–1500; clip < 0.5%; stars ≥ 150 |
| selfflat_median | star ratio ≤ 5% of calibrated; corner/center 0.35–0.75 |
| subsky_frame | G median within ±10% of calibrated (tilt is INFO — bowl reads ~9–13% in any plane fit) |
| gain | monotone non-increasing (THE ring guard); corner 0.38–0.58; gray (spread 0) |
| divided | p2v(r≤0.85) ≤ 0.20; rim(r>0.9) ≤ 0.25 |
| registration | registered/total ≥ 0.9 |
| stack | noise/median(G) 1.2–2.2%; p2v ≤ 0.20; stars ≥ 300; median16 150–1500 |

## DEAD ENDS — never re-attempt (each killed by measurement)

Gain/flat estimation:
- Single free-form gain fit → bakes the moonglow into the gain (peak
  off-axis, regional brightness distorted). Sanity-check any gain by
  its center.
- Polynomial radial V(r) (r²/r⁴/r⁶) → +4% mid hump + corner upturn →
  concentric RINGS after division (profile 54→31→54→6). Only monotone
  isotonic V is admissible.
- Per-channel V → corner tint (glow contaminates per-channel falloff,
  ~5% spread); V must be GRAY.
- Estimating V from glow-subtracted frames without rechroma → siril's
  per-channel level restoration corrupts the pedestal/bowl ratio →
  V 0.61/0.37/0.47 vs true 0.52–0.56 → corner tint on division.
- Multiplicative V×S fit on the untouched median → additive glow
  flattens it: corner 0.537, divided rim −16%. Additive-model fit →
  0.472, rim +7%. Both bracket truth; no a-priori model of siril's
  plane subtraction nails it → V2 from the actual frames (empirical)
  is the only flat divisor (rim_dev 0.067).
- Refining the gain from the STACK's residual → the sky's own
  structure (MW/glow/clouds, 2–8%) exceeds the ~2% residual being
  measured; opposite-sign "residuals" from different statistics.
  3× confirmed. Never scale the stack in place either.
- Per-frame `seqsubsky 2` (curvature) → erases the MW (+38 → +0.0
  linear): at 37 mm the MW band IS frame-scale curvature. Only
  geometric (band-mask) separation can discriminate — and hand-rolled
  masked surfaces (border-anchored / lower-envelope / corridor-excluded
  RBF) all wiggle the rim: rings 8–10 vs GraXpert's 5–6.
- Stack-level-only BGE (divide-first, no per-frame subsky) → cleanest
  LINEAR stage of any chain (rim −0.4%) but gx's big-extraction
  residual is STRUCTURED → starless-sky rings 4.8 FAIL vs 2.7, and MW
  +0.7 vs +2.6. Per-frame subsky 1 stays (self-flat branch only).

Stretch/denoise/color:
- Unlinked autostretch on a CALIBRATED stack → per-channel curves
  differentially amplify noise = the chroma-blotch ("rainbow") engine.
  (Pre-SPCC it was compensating a cast — that justification died with
  SPCC.)
- `rmgreen` on a sky that is not green-dominant → global magenta.
- Linear denoise (vst or GraXpert), ANY placement on self-flat data →
  noise is radial after V(r) division; adaptive smoothing imprints a
  radial signature → rings 4.1–5.1 FAIL. Only post-stretch
  `-vst -mod=0.5` on the starless render passes.
- Denoise AFTER the boost → noise field is non-stationary (corridor
  ×2.2) → NL-Bayes under-averages the corridor, over-smooths the sky:
  corridor grain 6→7, MW −1.
- Chroma blur (σ2/4) + satu → scale-blind to 48–128 px blotches; satu
  re-amplifies everything ×1.25 → rainbow WORSE. The fix is
  significance coring (Wiener, multi-scale), not blurring.
- A fixed shell_chroma WARN bound → cried wolf on the approved render
  (honest PSF fringe dominates and scales with the chain's low-end
  gain). aura_lum is the defect discriminant.

Detection/solve/registration:
- Siril internal solver on these ultra-wide trailed fields → fails
  star matching at 52° AND 26° even with the local Gaia catalog and
  correct center. astrometry.net blind solve from coarse PEAK
  centroids works in seconds (logodds 115–373); blob/PSF centroids
  don't feed the matcher.
- Position hints from session labels → set-03's "Big Dipper" label was
  ~70° wrong (it belonged to the lights composition). Blind-solve
  first, label after.
- 1-pass sequence-start registration → drift strands tail frames
  (26/32); 2-pass + sigma 0.5 → 31/32; on trailed self-flat frames the
  auto-reference under-performs a SWEEP (18/21 vs 21/21 @ ref 12).
- 38mm-only subset (dropping the 8×37mm frames) → same per-frame
  matching luck, full √(18/11) noise penalty. Keep all frames.
- wFWHM weighting/filtering → no-op at ~6% FWHM spread.
- Drizzle → heavily oversampled at 24 mm/5.9 µm; pointless.
- Deconvolution (makepsf + RL) → fitted PSF ≈ symmetric (trailing is
  in-exposure), unstable on ≈0 background; no de-trailing.

Separation/stars:
- Lowering starsep prominence (6→5→4σ) to catch the faint tail → NULL:
  residual starless detections 5137/5179/5159 — the stipple is
  noise-level clumping, not separable stars.
- StarNet: no Linux aarch64 build through v2.5.3. Route that remains:
  official ONNX packages (Linux x64) + verified-installable aarch64
  onnxruntime wheels — go/no-go is whether the .onnx is loose in the
  package (ledger #4).
- The stars-layer skirt annulus is the ghost-aura engine (MTF ×~10³
  low-end gain on subtraction noise): fixed by stars_floor, NOT by
  smaller dilation (cliff moves brighter), NOT by feathering alone
  (doesn't touch the amplified wing).

QA/scope:
- Whole-frame QA as the gate on a separated chain → reads intentional
  MW lift as background artifact (k=0.6 → "ring 6.1" was pure corridor
  signal). Gate scope = starless-sky (corridor+foreground masked),
  ratified 2026-07-06; whole-frame stays a reported reference.
- Judging by hand-picked patches → the whole-frame-QA lesson that
  started the gate (2.69/38 on a render that "looked fine" in patches).
- A level-step seam gauge across mask edges → strip-median ≈ 0; the
  coring seam is a TEXTURE discontinuity (blotch-MAD ratio works).
- Sensor `fixbanding` → the visible bands are corridor-oriented chroma
  survivors + star fringes, NOT row/col pattern (axis-aligned residual
  0.2–0.5 rms vs 1.2–2.5 corridor-oriented). Don't run it.
- Hiding defects with darkness/crops → the 0.07-target "fix" and the
  150–250px crops were masking the rim, not fixing it; the rim was in
  the data (estimator extrapolation × stretch amplification).
- JPEG q92 + 4:2:0 for finals → max 176-count star-edge errors and
  ~40% of the shell chroma HIDDEN by subsampling (13.3 measured through
  the jpg vs 21.9 on the PNG) → panels must compare like encodings.

Prediction inversions worth remembering (recorded, instructive):
- "K_G will move 0.904→~1 without rgb_equal" → actual K_G 0.749:
  rgb_equal was the PRIMARY raw-Bayer normalizer, not a tweak.
- "corridor clip0 must stay ~0 under black_point" → inverted: the
  corridor's dark gaps/lanes clip (9–16%) and that IS the requested
  effect; the smooth cored sky barely clips (0.01–1%).

## Bandaid/adaptation ledger (every divergence carries its removal condition)

1. **Self-flat chain** (median → V2 → rechroma → divide) — ADAPTATION,
   measured. Dies when real flats exist at the set's focal length
   (preflight auto-routes; the matched-flat path is proven end-to-end).
2. **Per-frame `seqsubsky 1`** — ADAPTATION on the self-flat branch
   only (stack-level-only BGE measured FAIL, see dead ends). Dies with
   real flats.
3. ~~rgb_equal~~ — CLOSED 2026-07-07 (user-approved): SPCC calibrates
   the raw stack directly.
4. **Star separation by mask+inpaint** — ADAPTATION (no aarch64
   StarNet). Removal IN PROGRESS 2026-07-07: official v2.5.3 Linux x64
   CLI package DOES ship a loose StarNet2_weights.onnx (131 MB, NHWC
   1×512×512×3 float [0,1], clip tail in-graph; license = personal
   astrophotography use only) → `scripts/render/separation/starnet_sep.py`
   runs it on aarch64 ORT (0.3 s/tile, bit-deterministic; invertible zero-clip MTF
   pre-stretch to bg 0.25, window 512 stride 256 central-crop
   assembly; weights+venv under ~/.local/share/starnet/). Smoke crop
   (1024², MW corridor): starless residual detections 83 vs the
   engine-invariant catalog's 1440 components, faint-tail stipple
   visually gone, bg med/σ unchanged vs inpaint (Δp50 1e-6).
   Full-frame validation, measured (exp_starsep_sep_engine_20260707_
   120825, `--sep-engine net`, default-off in starcomb — B7
   byte-verified after the plumbing): sky side all PASS and better
   than inpaint — gate blocks 1.25 vs 1.38, MW contrast 5.0 vs 4.0,
   corridor floor +5.0/−2.6 vs +4.0/−3.0, starless residual
   detections 1180 vs ~5.1k (stipple visually gone), no structure
   holes (sky delta p0.1 −1.2 counts16 < 1σ; foreground restore w/
   8px feather required — the net eats treeline texture, −221
   counts16, policy = branch not sky, same as the mask engine).
   KILLED at stock settings: star_shell aura_lum +12.0 WARN (bound
   4.0, inpaint +2.0). Mechanism measured on the bright-tier sample:
   the net STARLESS keeps a residual halo pedestal under bright stars
   (+8.0/+6.7/+2.2 counts16 at r0-4/4-8/8-12 vs r32-40 baseline;
   inpaint fill is flat +0.3/+0.4/+0.5) and the starless autostretch
   amplifies it; the stars layer is NOT the engine (its skirts are
   dimmer than inpaint's: 10.9 vs 17.8 counts16 at r4-8; flux books
   balance). 2× upsampled inference (official bright-star mode,
   `--upsample`, 4× runtime): pedestal r4-8 +6.7→+4.2 but r0-4
   +8.0→+7.7 — bar (≤ +1) NOT met, killed as the fix. HYBRID (engine
   `hybrid` = net inference ON the inpaint starless, stars = stack −
   final starless): ALL BARS MET 2026-07-07 — pedestal +0.3/+0.4
   (= the inpaint fill exactly), starless residual detections 589
   (vs inpaint ~5.1k, stock net 1180), MW contrast +7.0 (= control),
   no holes (sky delta p0.1 −1.1 counts16 < 1σ; the negative patches
   ARE the removed stipple), σ16 3.79 unchanged; B7-config render:
   gate PASS blocks 1.375 (= control), aura_lum +2.0 (= the approved
   render), corridor +4.0/−3.0, chroma rings IMPROVE 1.33/1.22 →
   1.11/1.00 (the stipple was corridor-oriented chroma). Render-domain
   stipple gain is subtler than linear (much of the tail sits near
   the render floor on this underexposed data — photons still rule).
   PENDING USER JUDGMENT:
   `results/exp_starsep_sep_engine_20260707_125122/` (renders,
   metrics, judgment/ crops incl. starless-stipple + bright-shell
   panels; the killed stock-net A/B is exp_..._120825). Default stays
   `inpaint` until approved; the net pass adds ~5 min on this box.
   Cost of the inpaint engine documented: <6σ faint tail in the
   starless layer; skirt-aura class (mitigated by stars_floor).
5. **Denoise** — linear placements structurally dead on self-flat data;
   post-stretch `-vst -mod=0.5` is in the approved chain.
6. **mw_boost** (luminosity-weighted) — the lift itself dies when the
   next acquisition has enough integration that a global stretch
   renders the MW without local help.
7. **Stars anchor (median top-500)** — data-dependent low-end gain
   (×864→×996 drift measured). Removal: noise-relative/fixed-gain
   anchor, pre-registered, B7-reproducibility preserved.
   MEASURED 2026-07-07 (hypothesis confirmed, sharpened): the drift
   class is PER-CHANNEL gain (the rgb_equal→SPCC transition), not
   global gain. Synthetic test on the canonical layers (per-component
   per-channel amplitudes, floor+MTF replicated, G-channel u8 vs
   control): pure global gain ×0.8/×1.25 → BOTH modes track (max
   drift 0.45 counts, identical — catalog also follows global gain);
   per-channel SPCC K (1.0/0.656/0.837) → catalog mode drifts −1.0/
   −8.5/−20.0 median counts (bright/mid/faint tier, max 20.2) because
   the max-over-channel top-500 median moves differently than any one
   channel, while noise mode holds +0.05/+0.17/+0.60 (its m tracks
   K_G exactly: 0.656×0.000904 = 0.000587). `--stars-anchor noise`
   default-off in starcomb (catalog = B7 identity, byte-verified);
   k_anchor 490.9663661574939 = canonical anchor 0.0284109 / σ_G
   5.78673e-5. ACCEPTANCE MEASURED: a full noise-mode render on the
   canonical stack is byte-IDENTICAL to all four B7 artifacts — the
   default flip is a render no-op there and awaits only the user's
   go-ahead.
8. **Whole-frame QA on the recombine** — retired as gate (scope
   ratified 2026-07-06); lives on as a reported reference.
9. **Raw ingest** — RESOLVED for any siril-readable raw. `run_pipeline.sh`
   (`raw_find`) globs every common camera raw — NEF/DNG/CR2/CR3/ARW/RAF/
   ORF/RW2/PEF/SRW — and siril's `convert` debayers them directly (verified:
   Wang's D810A NEF ingests RGGB 14-bit and stacks a clean master; set-03's
   DNG still matches the same glob). DNG conversion is retained ONLY as a
   FALLBACK for a raw THIS rig's siril cannot decode: siril 1.4.4 bundles
   LibRaw 0.22.0-Devel202502, which does not list the Z6III body and cannot
   decode Nikon HE/HE★ (TicoRAW) — so a Z6III **HE** frame still needs Adobe
   DNG Converter (which licenses that decode). That last fallback dies once
   Z6III acquisition records 14-bit **Lossless** NEF (see checklist) or the
   rig's siril bundles a LibRaw that lists the body (released 0.22 does; the
   Feb-2025 devel predates it).

## Checklist for future acquisition sessions (the real quality lever)

- Record **14-bit Lossless-compressed NEF**, NOT High-Efficiency
  (HE/HE★): menu Photo Shooting → RAW Recording → Lossless. HE is
  TicoRAW-compressed (LibRaw can't decode → forces the NEF→DNG bandaid,
  ledger #9) and lossy-ish; Lossless matches Wang's D810A and preserves
  faint linear signal. Confirm 14-bit (high-speed continuous can drop
  to 12-bit).
- ISO 800 (Z6III second gain stage), subs ≤ 500/focal (13s @ 38 mm,
  20s @ 24 mm) — trailing, not noise, capped set-03's sharpness
- MORE integration: corridor signal/grain ≈ 1 at 8.75 min ISO 200 —
  every processing knob is polishing presentation until photons improve
- Flats per focal length used that night, BEFORE touching the zoom;
  histogram peak ~50% (1/50s at the Jul-5 screen brightness); diffuse
  the screen (cloth over lens + distance — the pixel grid showed at
  ~0.3% RMS)
- Darks same exposure/ISO at night temps; biases at the flats' shutter
  (= exact flat-darks)
- Lock the zoom ring (tape); don't touch the camera mid-set (set-03's
  37→38 mm step happened at a handled pause)
- Dither between subs; avoid the moon (star fringes on trailed PSFs
  are dispersion — physical, satu only multiplies them)
