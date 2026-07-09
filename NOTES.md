# Astrophotography processing pipeline — lab notebook

This file is the **current truth**: what the pipeline is, why every
knob has its value (measured), and the dead-end registry (what was
tried, what number killed it — NEVER re-attempt these). The full
chronological history — every experiment arc, superseded recipe and
session narrative — lives in **git** (`git log`, and every commit
carries the NOTES of its time; each approved baseline is git-tagged, e.g.
`set-03-baseline-20260709`). `README.md` is the process contract
(standard-workflow mapping, review contract, experiment discipline,
per-set geometry, north star). Update THIS file as states change;
never let it grow narrative again.

## STATUS (2026-07-09)

- **Per-dataset state is first-class**: `datasets/<session>/<set>/` (tracked)
  holds each dataset's `geometry.json` + `recipe.json` (knobs resolve CLI >
  recipe > GENERIC, provenance printed) + `baseline.json` (written only by
  `scripts/qa/sweep.py --rebaseline`). **The no-regression sweep is one
  command** — `python3 scripts/qa/sweep.py` — gate + shell bounds + metric
  drift + artifact-byte comparison over every baselined dataset;
  `--determinism` double-renders cold.
- **The render chain is deterministic from the stack, cold caches
  included** (measured: two fully-cold M74 builds byte-identical across all
  four artifacts; the full sweep byte-reproduces every baseline). The
  bgelin subsky runs WITHOUT dither: unseeded ±1 LSB16 noise, pointless on
  a 32-bit float chain, was the one nondeterministic step (two cold builds
  differed on 100% of pixels, RMS 0.41 counts16, detection 852→858). The
  deterministic re-render was verified metric-identical on every dataset
  and USER-CONFIRMED visually equivalent 2026-07-09 (set-03 churn 17.3% of
  pixels at RMS 2.2 counts16 = the seeded fill re-drawing over a slightly
  different mask + ~50 faint cull flips; LMC 52% at RMS 1.3 counts8).
- **Star separation architecture settled** (measured on three data
  classes; numbers in ledger #4 and the per-dataset recipes): StarNet2
  ONNX (`net`) is the generic default via `sep_engine auto` — its failure
  mode is LOUD (the gate catches it) while inpaint's is silent (real
  structure destroyed on a PASSing render; the >10% in-envelope WARN is
  its only tell). Engine facts by class: resolved object (M74) → net
  preserves what inpaint destroys, aura also better (+4.0 vs +4.9);
  ultra-wide MW-dominated self-flat DSLR (wide_50mm 41°) → net FAILS the
  gate outright (grad 9.0 / rings 9.0 / aura +5.0 vs inpaint PASS
  6.4 / 4.2 — residual large-scale structure + bright-star shells);
  set-03 (37 mm) carries the same class cosmetically (aura +4.0, inside
  the bound — USER-ACCEPTED 2026-07-09); matched-flat off-centre object
  (SMC) → both pass, net aura +3.2. The `hybrid` engine is DELETED
  (ledger #4). The ONLY engine pin is wide_50mm = `inpaint` (measured
  gate fail; lifts when a better separation model lands — BACKLOG); every
  other dataset tracks generic.
- **Datasets** (registry: SESSIONS.md; records: `datasets/`; every recipe
  tracks the GENERIC pipeline — per the user's direction the repo optimizes
  the generalized chain, not any one dataset's frozen render — with
  wide_50mm's engine pin as the single measured exception):
  - `07-02-26/set-03` — processed; underexposed: quality is
    exposure-limited (corridor-era B5/B6/B7 tags are history).
  - `nikon-test/lmc_180mm` — processed. The bright-star red halo is the
    Sigma-180-wide-open veiling-glare signature (R−G plateau +4..+5 counts
    r≈6–38; absent on the same body at 50 mm f/4 and on set-03) — USER
    VERDICT final: honest gear data, no render-side de-fringe; fix is
    acquisition (stop down). chroma_core k=4 was the user's ladder pick.
  - `nikon-test/smc_180mm`, `nikon-test/wide_50mm` — processed, gate PASS.
  - `imx585c/m74_toa130` — processed (first FITS + first mono set), gate
    PASS; reference master in `imx585c/reference/`.
  - `07-02-26/lights` — NOT approved (user: "massive issues");
    generalization testbed only.
  - `siril-m8m20` — the C7 OSC-CFA verification set + C6 dual-band case.
    The rest of the C6 corpus (colonnello-m20 mono-RGB, mlnoga-ngc7635
    SHO) is off-disk; re-stage via
    `~/.cache/astro_recovery/fetch_corpus.sh`.
- **The gate is composition-agnostic** (`bg_qa`): sky selected STATISTICALLY
  (blocks ≤ P50+2.5·MAD, foreground excluded), grading colour / plane-fit
  gradient / blotch / rings — no per-set corridor (the geometric corridor
  broke on the object-dominated LMC; a plane fit to the statistical sky
  generalizes). Calibrated: references pass with margin; injected 8-count
  gradient / ring / colour cast FAILS.
- **No user-judgment items open.** Judgment packages
  (`scripts/qa/judgment_crops.py`) must state their question
  (`--question=`) and ship a full-frame pair + lossless 1:1 crops — a
  package that makes the judge guess the question is a defect. SPCC still
  runs sensor-null — BACKLOG C2.
- **Next acquisition (see checklist) — worth more than all remaining
  processing.**

## Environment

Rig/tooling facts live in **`CLAUDE.md`** (git-tracked, auto-loaded
into agent sessions): flatpak siril invocation + the /tmp rule,
hardware/disk constraints, python stack (no astropy), GraXpert,
astrometry venv, local Gaia catalog layout. Catalog chunk state as of
2026-07-07: astro + SPCC xpsamp {2,3,5,7,8,9,10,11,12,13,14,15,19,25,
27,29,30,31,43} = the Cygnus + Boötes cones (northern), plus the southern
LMC/SMC chunks {32,33,34,36,38,44,45} added 2026-07-08; SPCC needs the
FULL cone. `scripts/calibrate/spcc_cone.py <solved_wcs.fit> [--fetch]`
computes the nside=2 nested cover from the solved WCS (projects the true
image centre, not CRVAL) and fetches any missing chunk (validated:
reproduces the Cygnus 11-chunk cover for the 33.5° cone at 312.77,+48.16).
Camera: Nikon Z6 III, raws → DNG (Adobe DNG Converter
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

**Dedicated-astrocam FITS branch (cooled mono/OSC)** — a set of `.fits` lights
forks to a FITS ingest: `fitsmeta.py` reads exposure/gain/offset/filter/mono
from the headers (the free-text `FILTER` keyword — an SBIG convention, not
validated core FITS — is normalized to a canonical token; a mixed dir fails
loud). Flats are matched to the lights **by FILTER** (vignetting and dust
shadows are wavelength-dependent, so a flat is valid only for its own filter)
and calibrated with **dark-flats**, darks matched to the flat exposure: the
CMOS standard, since a multi-second flat carries dark current a bias cannot
remove (`biases/` is the fallback). Darks are filter-independent, matched by
exposure/gain/offset. A mono light is never debayered (no `BAYERPAT`); an OSC
CFA FITS gets `-cfa -debayer` (that branch is written but unverified). The
render detects a 1-channel stack and takes the luminance-only path — chroma
coring and saturation act on channel differences that are identically zero, and
SPCC has no colour to calibrate. A single-channel FITS must be written
`NAXIS=2`: siril's reader rejects a degenerate `NAXIS3=1` cube. Measured on M74
(47×120 s, TOA-130 mono L): 47/47 registered, gate PASS (colour 0.0, gradient
0.5, blotch 0.1, rings 1.0); the flat master falls off only 1.3% to the corner.

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

**Per-set geometry (`datasets/<session>/<set>/geometry.json` +
`astrometrics.configure`)** — the only per-set composition fact is the
terrestrial FOREGROUND (rect | pixel mask from `suggest_foreground.py` —
threshold 0.4×sky-median ≈ −42σ, border-band-anchored components, dilated
for the drift-smear halo | none) plus its judgment crops. No geometry file
→ foreground none. There is NO MW corridor: the background gate selects
its sky STATISTICALLY (below), so a galactic band is never a per-set
input — that geometric mask was a set-03-specific bandaid that broke on an
object-dominated field (the LMC).

**Product chain (`starcomb.py`)** on the SPCC stack — knob values resolve
CLI > `datasets/<session>/<set>/recipe.json` > GENERIC (provenance printed
per run; a recipe-less dataset renders generic and says so):
1. GraXpert BGE + `subsky 1` on the STAR-FUL linear (the only
   MW-safe order: BGE on starless erases the MW, +38 → +0.4 linear).
   NO `-dither`: dither is unseeded ±1 LSB16 noise for banding that
   cannot occur on a 32-bit float chain, and it was the render's one
   nondeterministic step (two cold builds differed on 100% of pixels,
   RMS 0.41 counts16 = 0.08σ, moving downstream star detection 852→858).
2. Star separation, engine per recipe (`auto` = net when the StarNet2
   weights are installed, else inpaint):
   - `net` (`starnet_sep.py`, StarNet2 ONNX on aarch64, linear under an
     exactly-invertible MTF pre-stretch — the vendor-sanctioned
     placement): the fail-safe — keeps 100.0% of field-star flux on a
     resolved object and pulls 33% less galaxy-zone flux than inpaint;
     its worst case is a cosmetic bright-star shell (set-03 aura +4.0,
     at the WARN bound).
   - `inpaint` (`starsep.py`, mask+inpaint): local-bg detection 4σ,
     prominence 6σ, area caps (geometry-overridable px²), dilate 3 (+5
     bright), pyramid-seed + Jacobi inpaint, fill noise 0.7σ,
     deterministic seed. It cannot tell an HII knot from a star
     (structure destruction on resolved objects — it WARNs when >10% of
     its detections sit inside an extended-object envelope) and leaves
     the <6σ faint tail in the starless (prominence 4/5/6 all measured
     ~5.1k residual detections — noise-level clumping).
   Both engines emit the same trio + the engine-invariant detection
   catalog, so culling/anchoring/shell audits measure them identically.
3. Starless: **linked** autostretch −1.5 **0.07** → post-stretch
   `denoise -vst -mod=0.5` → chroma_core 4 → lum_core 2 → black_point 8.
   The corings estimate their noise on the statistical dark sky and are
   Wiener-gated everywhere (no corridor to protect real structure — energy
   ≫ noise does). The gate jpg (q92, frozen — gate identity) is written
   HERE, before the combine.
4. Stars: cull 50 (< p50 flux) → stars_floor 3.0×σ → gray MTF anchored
   so the median top-500 amplitude ON THE FIXED G BASIS (`peak_g`)
   renders at 0.97 (`basis max`, the max-over-channels reading, exists
   only as a recipe escape hatch — nothing uses it).
5. Screen combine → satu 0.2 → jpg q100/4:4:4 (+ PNG8 + PNG16 with
   `--lossless`).

**Knob provenance (every value from a measured single-knob ladder):**

| knob = value | the number that set it |
|---|---|
| SPCC (not rgb_equal) | K R1.000/G0.656/B0.837 (R-normalized; raw G runs ×1.5 hot — the Bayer imbalance rgb_equal used to hide) · 509/2850 stars kept · gate equivalent · rim chroma improves (−9.0→−7.2). Captured by `spcc_run.py` (work/spcc_<set>.{json,log}); rerun on the canonical stack is pixel-IDENTICAL (spcc deterministic). An older grep-lost triple (1.675/0.749/0.935) does not reproduce — trust the json |
| bge_first order | MW +38 survives star-ful BGE; starless BGE kills it (+0.4) |
| linked stretch | unlinked = per-channel noise → chroma blotches (the "rainbow" engine); on a calibrated stack linked PASSES (2.8/1.2/1.8) and cuts blotches ~12% at source |
| starless_target 0.07 | sky rim is real: 0.12 → sky rings 4.4 FAIL |
| vstpost -mod=0.5 | every linear denoise placement imprints a radial signature on self-flat data (5.1/4.6 FAIL); post-stretch half-mod: grain −40%, gate clean |
| chroma_core 4 | bands 0.73/1.25 (k=3: 1.08/1.88); star-color cost −1% on the linked chain. NOTE: tuned on underexposed set-03 (colour ≈ noise); on a bright real-colour target (the LMC) k=4 over-neutralizes real Hα — revisit per data class |
| lum_core 2 | gray patches (stretch-amplified lum noise ±2 counts) removed; noise estimated on the statistical dark sky, correction Wiener-gated everywhere; NO geometric factor (a hard rect printed a 4.5× texture seam; the Wiener gate protects real structure) |
| black_point 8 | user "blackest": bg 16→8; dark-sky clip0 ~0.5% (the gap/lane blackness requested); floor P50 + contrast survive (linear shift preserves differences) |
| stars anchor 0.97 | mid-peak 255 vs 225 at 0.85; layers decoupled (gate untouched) |
| stars_anchor_basis g | the anchor is the median top-500 component peak; on the MAX-over-channels basis a per-channel recalibration (SPCC K) moves which channel wins and the anchor drifts (measured −8.5/−20 counts16 mid/faint G, low-end gain ×864→×996 between builds of one sky); the G basis rescales WITH its channel and cannot drift. `max` survives only as the pin on approved looks that predate the fix. The anchor's ABSOLUTE level stays a per-dataset recipe fact: top-500 is the brightest 2.2% of set-03's 22916-star catalog but 59% of M74's 852 — no single rule sets star brightness across fields |
| stars_floor 3.0 | ghost-aura fix: bright-tier aura +7.0→+2.0 (raw stretch = +0.5), halo 1.73→1.36, cores/mid-peak untouched, gate bit-identical |
| cull 50 | metric-invisible; user's max-removal pole (the alternate cull-0 faint-field look remains a flag away) |
| satu 0.2 | fringe span scales ~(1+s): 79/94/107 for 0/0.2/0.35; 0.2 keeps star color at −12% fringe |
| jpg q100/4:4:4 | q92+4:2:0 cost mean 2.29 / max 176 counts at star edges / 9.7 star chroma (part of the "pixeled aura"); q100/4:4:4 = mean 0.44 / max 5; PNG8 = the lossless artifact the determinism check compares; PNG16 = the float render at 65536 levels (writer roundtrip-verified) |

**Standing per-render audits (printed + logged every starcomb run):**
the GATE (`bg_qa` on the starless render, composition-agnostic sky scope:
colour ≤ 7, gradient ≤ 8, blotch ≤ 5, rings ≤ 8 on the statistical dark
sky, terrestrial foreground excluded — **thresholds never loosen**);
whole-frame QA as reference; `star_shell_report` (aura_lum WARN > 4.0 —
calibrated fixed +2.0 vs defect +12.0 on the same star sample; shell_chroma
is a TREND, no bound — honest PSF fringe dominates it and a fixed bound
cried wolf on the approved render); black_point clip0 sky; stars anchor +
MTF low-end gain (drift watch); star metrics.

## Per-stage expectations (inspection contract)

Mirrored in `inspect_stage.py EXPECTATIONS` (keep in sync). WARN-only —
inspection never aborts; the hard gate stays `bg_qa.py`. Bounds are
sanity envelopes calibrated on set-03 (some self-flat-specific); a new
data class may WARN legitimately — revisit bounds there, don't ignore.

| stage | PASS bound (short) |
|---|---|
| calibrated | clip < 0.5%; stars ≥ 150; bg median16 INFO (a site/sensor fact — dark-site cooled mono ~35, light-polluted DSLR ~370–600) |
| selfflat_median | star ratio ≤ 5% of calibrated; corner/center 0.35–0.75 |
| subsky_frame | G median within ±10% of calibrated (tilt is INFO — bowl reads ~9–13% in any plane fit) |
| gain | monotone non-increasing (THE ring guard); corner 0.38–0.58; gray (spread 0) |
| divided | p2v(r≤0.85) ≤ 0.20; rim(r>0.9) ≤ 0.25 |
| registration | registered/total ≥ 0.9 |
| stack | dark-sky p2v ≤ 0.20 on the statistical sky (a frame-filling object doesn't read as a defect); stars ≥ 300; noise/median, median16, sky_frac all INFO (ratios to an arbitrary pedestal / data-class facts) |

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
- Chroma blur (σ2/4) + satu → scale-blind to 48–128 px blotches; satu
  re-amplifies everything ×1.25 → rainbow WORSE. The fix is
  significance coring (Wiener, multi-scale), not blurring.
- A fixed shell_chroma WARN bound → cried wolf on the approved render
  (honest PSF fringe dominates and scales with the chain's low-end
  gain). aura_lum is the defect discriminant.
- "lum_core erases a centred galaxy's faint outer disk" → KILLED. Measured on
  M74 (lum_core 0 vs 2, same stretch, starless layers): the galaxy's median
  profile is preserved at 100% of its counts-above-background at EVERY radius
  out to r=525 px, while sky noise falls 5.93 → 1.48 counts (−75%). The Wiener
  gate does protect real structure; the coring is not what damages a galaxy.
- "GraXpert BGE absorbs a centred galaxy's halo" → KILLED. Halo survival
  pre-BGE → post-BGE is 101–144% at every radius (BGE removed a broad
  background gradient, so the halo measures STRONGER against a lower far-field
  sky). Background extraction is not what damages a galaxy.

Separation on resolved objects:
- mask+inpaint star separation cannot process a RESOLVED galaxy. It keys on
  compactness + prominence and has no notion of "galaxy": on M74 (992 mm) 229
  of 852 kept detections (26.9%) lie inside the galaxy (r < 350 px, median area
  14 px² — HII knots), and the largest admitted component is 6212 px² (the
  core, allowed by AREA_MAX_BRIGHT=12000). Those knots are inpainted OUT of the
  starless and screened back through the stars MTF, rendering as hard white
  blobs. StarNet2 (`--sep-engine net`) renders the same field correctly: it
  keeps 100.0% of the genuine field-star flux while pulling 32% LESS galaxy
  structure into the stars layer (measured over the same components). The
  `hybrid` engine cannot fix it — hybrid's base IS the inpaint starless, which
  has already lost the knots.
- StarNet2's bright-star residual is a per-DATA property, not a fixed defect.
  On M74 the net starless pedestal is 1.28 counts16 at r0-4 (0.26σ), SMALLER
  than the inpaint fill's 1.85 (0.38σ); on set-03 the same engine prints a
  visible striped bright-star shell (aura_lum +0.0 → +4.0). Measure it per
  dataset; do not carry one set's number to another.
- A mono starless must leave the separator with ONE channel. The net's graph
  takes 3, so a mono stack is replicated to feed it; returning 3 channels drops
  the render off its luminance path onto the colour chain, whose patch-based
  `denoise -vst` printed rectangular blocks across the sky (gate rings 10.2 vs
  1.0). The linear starless was clean throughout — the artifact was the wrong
  render path, never StarNet2.

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
- Whole-frame QA as the gate on a separated chain → reads real MW/object
  signal as a background artifact ("ring 6.1" was pure MW signal). The gate
  runs a composition-agnostic STATISTICAL sky scope instead (dark blocks,
  foreground excluded); whole-frame stays a reported reference. (The interim
  corridor-masked scope was itself a bandaid — removed 2026-07-08.)
- Judging by hand-picked patches → the whole-frame-QA lesson that
  started the gate (2.69/38 on a render that "looked fine" in patches).
- A level-step seam gauge across mask edges → strip-median ≈ 0; the
  coring seam is a TEXTURE discontinuity (blotch-MAD ratio works).
- Sensor `fixbanding` → the visible bands are MW-oriented chroma
  survivors + star fringes, NOT row/col pattern (axis-aligned residual
  0.2–0.5 rms vs 1.2–2.5 band-oriented). Don't run it.
- Hiding defects with darkness/crops → the 0.07-target "fix" and the
  150–250px crops were masking the rim, not fixing it; the rim was in
  the data (estimator extrapolation × stretch amplification).
- JPEG q92 + 4:2:0 for finals → max 176-count star-edge errors and
  ~40% of the shell chroma HIDDEN by subsampling (13.3 measured through
  the jpg vs 21.9 on the PNG) → panels must compare like encodings.

Prediction inversions worth remembering (recorded, instructive):
- "K_G will move 0.904→~1 without rgb_equal" → actual K_G 0.749:
  rgb_equal was the PRIMARY raw-Bayer normalizer, not a tweak.
- "the dark gaps must stay ~0-clip under black_point" → inverted: the MW's
  dark gaps/lanes clip (9–16%) and that IS the requested gap blackness; the
  smooth cored sky barely clips (0.01–1%).

## Bandaid/adaptation ledger (every divergence carries its removal condition)

1. **Self-flat chain** (median → V2 → rechroma → divide) — ADAPTATION,
   measured. Dies when real flats exist at the set's focal length
   (preflight auto-routes; the matched-flat path is proven end-to-end).
2. **Per-frame `seqsubsky 1`** — ADAPTATION on the self-flat branch
   only (stack-level-only BGE measured FAIL, see dead ends). Dies with
   real flats.
3. ~~rgb_equal~~ — CLOSED 2026-07-07 (user-approved): SPCC calibrates
   the raw stack directly.
4. **Star separation by mask+inpaint** — DEMOTED to the weights-absent
   fallback (and set-03's pinned approved look). The StarNet2 ONNX
   engine (`starnet_sep.py`: official v2.5.3 weights, personal-use
   license, aarch64 ORT, invertible zero-clip MTF pre-stretch to bg
   0.25 — the vendor-sanctioned linear placement) is the generic
   default via `sep_engine auto`. Measured basis (2026-07-09 ladders
   under the composition-agnostic gate, both PASS everywhere):
   inpaint mis-classifies a resolved object's structure as stars (M74:
   26% of its 852 detections are in-galaxy HII knots, inpainted out
   and screened back as hard white blobs; the 6212 px² core passes
   AREA_MAX_BRIGHT) while net keeps 100.0% of field-star flux and
   pulls 33% less galaxy-zone flux; on the star-field set-03 net's
   only cost is a striped bright-star shell (aura +0.0 → +4.0, at the
   WARN bound); on the MORE extreme ultra-wide class (wide_50mm, 41°
   MW-dominated self-flat) the same residual-structure class FAILS the
   gate outright (grad/rings 9.0/9.0, aura +5.0 vs inpaint PASS
   6.4/4.2) — so net's failure mode is LOUD where inpaint's (structure
   destruction on a PASSing render) is silent; the asymmetry still
   favours net as the generic default. starsep.py now WARNs when >10%
   of its detections sit inside an extended-object envelope. The
   `hybrid` engine (net run ON the inpaint starless — a repo invention
   with no standard-practice counterpart, structurally unable to
   restore knots its base already destroyed) is DELETED. The set-03
   bright-star shell under net was USER-ACCEPTED 2026-07-09; the single
   engine pin is wide_50mm = `inpaint` on its measured gate FAIL. Costs
   owned where inpaint runs: <6σ faint tail in the starless layer;
   skirt-aura class (mitigated by stars_floor).
5. **Denoise** — linear placements structurally dead on self-flat data;
   post-stretch `-vst -mod=0.5` is in the approved chain.
6. **Stars anchor** — the same-sky drift class is FIXED structurally:
   the drift was PER-CHANNEL gain (measured: pure global gain ×0.8/×1.25
   → both anchor modes track ≤0.45 counts; the SPCC K set 1.0/0.656/0.837
   → the max-over-channels catalog anchor drifts −1.0/−8.5/−20.0 counts
   bright/mid/faint), so the catalog anchor now reads the component peak
   on the FIXED G basis (`peak_g`, generic default `stars_anchor_basis
   g`), which rescales with its channel and cannot drift; `basis max` is
   a recipe escape hatch nothing uses. `--stars-anchor noise` remains a same-sky
   stability tool ONLY: its k is per-dataset by construction (k =
   anchor/σ_G literally restates one dataset's star statistics — set-03's
   491σ asserts an 11.5× star-brightness error on M74's 44σ field), so
   the hardcoded default was DELETED and noise mode requires
   `noise_anchor_k` from the dataset recipe. The anchor's ABSOLUTE level
   (top-500 samples 2.2% of set-03's luminosity function but 59% of
   M74's) stays a per-dataset recipe fact.
7. **Whole-frame QA as the gate** — SUPERSEDED, not adapted: the gate now
   selects its sky STATISTICALLY (composition-agnostic — colour / gradient /
   blotch / rings on the dark blocks, foreground excluded), so it neither
   reads real MW/object as a defect NOR needs a per-set corridor. The
   2026-07-06 sky-scope-via-corridor decision is gone with the corridor
   itself (removed 2026-07-08). Whole-frame QA lives on as a reported
   reference.
8. **Raw ingest** — RESOLVED for any siril-readable raw. `run_pipeline.sh`
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
- A fast lens WIDE OPEN adds a red veiling-glare halo around bright stars
  (measured: Sigma 180 @ f/2.8 = a +4..+5 count R−G plateau to r≈38; the
  SAME body at 50 mm f/4 is clean) — stop any fast lens down ≥1 stop for
  bright-star fields. It is an honest optical signature, not removable in
  processing without a bandaid.
