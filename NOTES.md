# Astrophotography processing pipeline — lab notebook

This file is the **current truth**: what the pipeline is, why every
knob has its value (measured), and the dead-end registry (what was
tried, what number killed it — NEVER re-attempt these). All history
lives in **git** (`git log`; every commit carries the NOTES of its
time). Per-dataset records live in `datasets/<session>/<set>/`
(recipe + measured baseline). `README.md` is the process contract
(standard-workflow mapping, review contract, experiment discipline,
per-set geometry, north star). Update THIS file as states change;
never let it grow narrative.

## Environment

Rig/tooling facts live in **`CLAUDE.md`** (git-tracked, auto-loaded
into agent sessions): flatpak siril invocation + the /tmp rule,
hardware/disk constraints, python stack (no astropy), GraXpert,
astrometry venv, local Gaia catalog layout. Local SPCC xpsamp chunks:
{2,3,5,7,8,9,10,11,12,13,14,15,19,25,27,28,29,30,31,43} (Cygnus, Boötes,
Sagittarius cones) + {32,33,34,36,38,44,45} (LMC/SMC); SPCC needs the
FULL cone. `scripts/calibrate/spcc_cone.py <solved_wcs.fit> [--fetch]`
computes the nside=2 nested cover from the solved WCS (projects the true
image centre, not CRVAL) and fetches any missing chunk (validated:
reproduces the Cygnus 11-chunk cover for the 33.5° cone at 312.77,+48.16).
Camera: Nikon Z6 III, raws → DNG (Adobe DNG Converter
18.4), 14-bit RGGB.

## Current design (each piece carries its measured WHY)

**Stack builder (`run_pipeline.sh`)** — preflight (exiftool): hard-fail
on empty/mixed frame dirs; flats used only when flats+biases exist AND
optics match the set, else self-flat path. Registration floor on every
path: under HALF the set registered ABORTS the run (0.5 = a design
pick, half the set is not the set — revisit on the first real failure;
the 0.9 advisory WARN stays inspection-side, a 60–90% set stacks
LOUDLY). Masters rebuild on manifest
change (names+sizes+mtimes — catches re-shot frames with old
timestamps). Calibrate `-dark -cc=dark` (+flat +equalize_cfa when
matched) → `setfindstar -sigma=0.5` (~870 vs ~370 stars/frame: the
matcher needs the extra triangles) → two-pass register → 32-bit
rejection stack, `-norm=addscale -output_norm`, **no `-rgb_equal`** (a
live stacking option): SPCC calibrates the raw Bayer balance directly —
raw G runs ~×1.5 hot and SPCC measures it (K R 1.675 / G 0.749 / B 0.935
on 508 stars); a pre-normalizer would hide exactly what SPCC measures.
**Stack policy (optional `"stack"` recipe block)** — run_pipeline
resolves `{"weight": "wfwhm"|"nbstars"|null, "exclude": [frame
numbers]}` from the dataset recipe at stack time (recipe-only knob, no
generic layer; provenance printed every run) and applies it on every
stack path — matched-flat template, FITS single, dual-band per line,
self-flat. ABSENT block/null/empty = the generic default: today's
unweighted `rej 3 3` with generated scripts byte-identical (proven by
text diff per path + green sweep). Weight → `-weight=` on the stack
line (regdata carries through both seqapplyreg and direct register —
verified on the installed 1.4.4); exclude → `unselect <r_seq> n n`
lines + `-filter-incl` (MANDATORY: plain stack measured to ignore
manual selection), where n = the registration inspection's per-frame
`n` (a dual-band set's one list governs both line stacks). Identity
caveat, measured: unselect indexes by 1-based POSITION while a
registration-REDUCED sequence keeps original file numbers with gaps —
position == n only on contiguous sequences — so with any exclude the
runner re-reads the stacked .seq after the run (`verify_exclusion`)
and hard-fails, REMOVING the stack, unless exactly the named file
numbers were deselected. Trigger doctrine: OFF everywhere generically — siril's
`-weight` is a min-max RAMP over the sequence's regdata (soft-culling:
worst frame → ~0 weight at ANY spread; measured N_eff 11.9/16 and +21%
sky noise at 7.4% FWHM CV), so a weight or cull is per-dataset state
adopted only through a with-vs-without ladder when a dataset's RECORDED
registration-inspection numbers show a real trigger (fwhm_cv_pct far
above the measured low-spread-harm regime, or cloud-class outlier
flags); rejection +
addscale normalization already absorb transients and frame-level
excursions (the SHO dawn-glow class stacked into an approved base), and
any weight/cull change rebuilds the stack = declared delta through gate
+ inspection + the user's eyes downstream.

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
CFA FITS gets `-cfa -debayer` (measured on the ASI2600MC set: 15/15 debayered
to a 3-channel stack, inspection PASS). The render detects a 1-channel stack
and takes the luminance-only path — chroma coring and saturation act on
channel differences that are identically zero, and SPCC has no colour to
calibrate. A single-channel FITS must be written `NAXIS=2`: siril's reader
rejects a degenerate `NAXIS3=1` cube. Measured on M74 (47×120 s, TOA-130 mono
L): 47/47 registered, gate PASS (colour 0.0, gradient 0.5, blotch 0.1, rings
1.0); the flat master falls off only 1.3% to the corner. The `FILTER` keyword
is optional in practice (ASIAIR writes none): an absent filter normalizes to
`-` on both lights and flats, so they match; filter identity then rests on
the directory staging. A master-only corpus stages PREBUILT masters in
`<session>/calib/{dark,flat}_<token>.fits`, matched by the normalized
FILENAME token — such masters carry NO headers (measured), so the filename
is the whole identity and the exposure match is unverifiable, both stated
per run; raw dirs win when both exist. Siril normalizes their ADU-scale
floats to [0,1] on import (same convention as ushort lights), so staging
is a plain copy — tracked by SOURCE identity (name+size+mtime marker),
never file mtime: a freshly staged master is always newer than every
calib/ source, so an mtime test would keep the previous filter's dark.

**Dual-band OSC composition (`composition.json` + `compose.py`)** — a set
whose composition record is kind `dualband-osc` calibrates the CFA mosaic
(no debayer — the lines live on distinct photosites), splits each frame
into its emission lines (`seqextract_HaOIII -resample=oiii`: Ha native
half-size from the R photosites, XPIXSZ doubling keeps the header-derived
solve hint correct; OIII downsampled to the same size so NO channel
carries invented detail), registers BOTH line sequences to the same
mid-sequence reference frame — the channels must overlay without a second
interpolation pass, and that is MEASURED, not assumed: star-centroid
residual between composed channels prints every compose and lands in the
inspection report (bound 1.0 px; hoo_180s measured 0.589 median / 0.968
p95 — the ~0.5 px floor is the R-vs-G/B CFA phase offset plus independent
per-line transform fits) — then stacks per line and composes R/G/B per
the palette mapping into `stack_<set>_comp.fit`. The composed stack
enters the ordinary flow: solve (the half-size header solves clean) →
SPCC `-narrowband` with per-channel wavelengths from the recipe (hoo:
656.28/500.7/500.7 nm → K R0.127/G1.000/B1.000 on 2641 stars; the
narrowband mode measurably changes the fit vs broadband-null, R 0.127 vs
0.130, and G≡B falls out of the identical synthesized filters) → render
unchanged. The full-size path (native Ha + 2× drizzle) is the BACKLOG
upgrade, gated on measured dither coverage. No composition record → the
set processes as an ordinary single stack (a dual-band set then debayers
like broadband: legal, but its lines stay merged — the record encodes the
data's goal).

**Mono filter-wheel composition (kind `mono-filters`)** — members are
SIBLING per-filter sets (each stacked by the ordinary mono path,
per-filter flats matched by FILTER keyword), keyed by a VIRTUAL target
name. Different frames per channel → nothing overlays by construction,
so `compose.py` aligns the member STACKS first: a siril sequence
registration to the composition's `reference` member — ONE interpolation
pass, and the reference channel itself carries only the identity
transform (choose the perceptually dominant member; m20_rgb uses G).
Measured on the first target (M20, 15R/15G/16B × 80 s at 0.68″/px):
channel alignment 0.072 px median / 0.445 px p95 over 300 stars — an
order of magnitude inside the 1.0 px bound (stack-level star fields are
registration-rich, and no CFA phase offset exists on this path). The
alignment applies `-framing=min` (intersection): a pixel the composed
product ships must exist in EVERY channel — compositing an uncovered
margin fabricates colour there (measured: one uncovered corner block
read R−G +8 on an otherwise 0.0-median-neutral sky and failed the
colour gate; the intersection crop is 12×9 px on this target and
integer-aligned, so the reference channel is still never interpolated).
The composed stack then solves/SPCCs/renders exactly like any colour
stack (SPCC sensor-null broadband; K R0.880/G0.881/B1.000 on 913 stars
— a mild wheel balance). A composition naming a `luminance` member is
REFUSED: LRGB joins L after both parts are stretched, which
compose-then-render cannot express — that design lands with the LRGB
corpus (BACKLOG).

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
→ foreground none. Border-anchor invariant, enforced at configure/load: a
foreground that touches no frame border is REFUSED (the foreground is
excluded from the gate's sky scope, so an interior "foreground" would
silently shrink the gate's jurisdiction; terrestrial obstructions enter
from an edge by construction). The background is never a per-set input: the gate
selects its sky STATISTICALLY (below) because bright celestial signal has
no fixed geometry a mask could scope (see dead ends).

**Product chain (`starcomb.py`)** on the SPCC stack — knob values resolve
CLI > `datasets/<session>/<set>/recipe.json` > GENERIC (provenance printed
per run; a recipe-less dataset renders generic and says so):
1. Linear background handling per `bgelin_mode`: **gx** (generic) =
   GraXpert BGE + `subsky 1` on the STAR-FUL linear (the only MW-safe
   order: BGE on starless erases the MW, +38 → +0.4 linear). MEASURED
   CLASS LIMIT: GraXpert's model absorbs frame-filling FAINT
   nebulosity — 75–98% of the Bubble complex's +3…11 e-4 dust
   subtracted as background while set-03's +38 e-4 MW band survived;
   **plane** = `subsky 1` only (a first-degree plane removes the
   gate's gradient class and cannot absorb a localized cloud by
   construction — the retention mode for fields that ARE mostly
   object; 93–97% dust retention measured, gate colour 2.0);
   **rbf** = in-house constrained extraction + `subsky 1` (ONE gray
   thin-plate RBF through significance-masked clean-core samples +
   QUADRATIC per-channel chroma, deterministic; protection reference
   per `rbf_protect` — knob table; a per-dataset mode for fields
   carrying both a real gradient and faint signal a full extraction
   eats, never generic);
   **off** = passthrough (measurement rungs). `subsky` runs WITHOUT
   `-dither`: dither injects unseeded ±1 LSB16 noise (0.08σ — breaks
   byte-determinism) to mask quantization banding that cannot occur
   on a 32-bit float chain.
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
3. Starless stretch, class-resolved (`stretch_linked auto`, provenance
   printed): broadband/mono → **linked** autostretch −1.5 **0.07**;
   narrowband-palette composition (recipe `spcc.narrowband`) →
   **perline**: per-line NOISE-WIDTH-CAPPED stretch (per channel,
   gamma∘black-pin solved by fixed 24-step bisection so sky location
   = `starless_target` AND sky noise width = `perline_scale` — the
   stretch stops before amplifying noise into visibility; gamma
   ceiling 10, stated when it binds) THEN the gated LCh finishing
   set in the reference chain's order — satgamma (chroma gamma),
   huerot (Hubble hue rotation, ±8° feathered edges), scnr
   (avg-neutral green), ppgamma (post-peak partial gamma on Luv
   LUMINANCE applied as an RGB-ratio-preserving gain — chroma is
   never stretched), all blended in over a two-noise-width ramp
   above the sky significance gate (hard gates measured to stipple).
   The standard SHO chain stretches lines separately — one linked
   MTF renders only the dominant line (the drowned-O3-sphere
   defect); sky-anchored unlinking is a no-op after BGE+SPCC, and
   object-anchored per-line lifting overruns the noise budget and
   mottles through the corings (dead ends). Then post-stretch
   `denoise -vst -mod=0.5` → chroma_core 4 → lum_core 2 →
   black_point 8. The corings estimate their noise on the
   statistical dark sky and are Wiener-gated everywhere (no corridor
   to protect real structure — energy ≫ noise does). The gate jpg
   (q92, frozen — gate identity) is written HERE, before the
   combine.
4. Stars: cull 50 (< p50 flux) → stars_floor 3.0×σ → gray MTF anchored
   so the median top-500 G-basis component amplitude (`peak_g`) renders
   at 0.97.
5. Screen combine → satu 0.2 → jpg q100/4:4:4 (+ PNG8 + PNG16 with
   `--lossless`) — every final sRGB-tagged (JPEG ICC + PNG chunks;
   the gate's q92 starless jpg carries none: gate identity).

**Knob provenance (every value from a measured single-knob ladder):**

| knob = value | the number that set it |
|---|---|
| SPCC (not rgb_equal) | K R1.000/G0.656/B0.837 (R-normalized; raw G runs ×1.5 hot — the Bayer imbalance a pre-normalizer would hide) · 509/2850 stars kept · gate equivalent · rim chroma improves (−9.0→−7.2). Captured by `spcc_run.py` (work/spcc_<set>.{json,log}); rerun on the canonical stack is pixel-IDENTICAL (spcc deterministic) |
| SPCC sensor spec = null | grounding the response in the real train (`-oscsensor "Sony IMX571"` + `-oscfilter "Optolong L-Pro"`, the one chip with a database curve) measured IMMATERIAL on lpro_180s: K R0.370→0.371 / G0.912→0.898 / B1.000 (≤1.5%), B-offsets 5th decimal, output pixels p50 ≤5e-6 / p99 ≤2.6e-4 of full scale, sensor-only ≡ sensor+filter — the star-colour fit lands on the same balance, so the null default stands; a recipe opts in (`"spcc"` block) only with a measured reason |
| SPCC placement = pre-BGE | rerun on the BGE'd (gx + subsky 1) stack of the strongest-gradient field on hand (Sagittarius core, lpro_180s): K R0.370→0.371 / G,B unchanged / kept 1862→1887 of 5014 — per-star local-annulus photometry cancels the smooth background, so solve+SPCC stay a stack product ahead of the render's BGE; re-measure opportunistically when a DSLR-class pre-SPCC stack next exists |
| no crop stage | canonical chains crop registration borders first; measured unnecessary here. Stack probe (set-03): borders carry only a smooth ±2σ level plane, MAD BELOW the core — no band at any depth 2–160 px. 128px/side trim render: color 2.0→2.0, grad 3.2→4.8, blotch 2.7→2.4, rings 3.1→4.4 (both PASS) — trimming improves NOTHING; the borders never flattered the gate. The 1.3–1.6pt grad/ring movements are frame-extent sensitivity (BGE refit + block grid + radial bins), so gate numbers compare only at a fixed extent; the trim also moved aura +4.0→+4.5 purely through the top-500 anchor population (scale-awareness entry in BACKLOG). Re-open only on a measured edge-driven FAIL |
| bge_first order | MW +38 survives star-ful BGE; starless BGE kills it (+0.4) |
| stretch_linked auto | class-resolved: broadband → linked (unlinked = per-channel noise → chroma blotches, the "rainbow" engine; on a calibrated stack linked PASSES 2.8/1.2/1.8 and cuts blotches ~12% at source); narrowband palette (recipe spcc.narrowband) → perline (one linked MTF passes the 5× Ha/O3 line ratio through — rim +50 vs +15 counts8, sphere drowned at 0.3σ/px of 53-count chroma grain; perline renders sphere interior O3/Ha 1.05 vs linked 0.50 at chroma grain 8.9 vs 59 MAD; sky-anchored unlinked is a no-op after BGE+SPCC, dead ends). perline+finishing on the SHO target: gate FULL-PASS incl. colour 3.0 (linked control: colour 11.0 scope-FAIL), grad/blotch 0.0, sky clip0 0% — the first lifted narrowband render to pass the colour scope (hue rotation + SCNR move the flood out of its failure mode; the gated lift never touches the sky) |
| perline_scale 0.5 | the per-line stretch's sky noise-width budget (%): solved gammas S2 9.79 / Ha 4.27 / O3 3.94 land widths 0.485–0.496% at sky 7.0%, clip0 ~0 — each starved line stretched hardest, all to the SAME noise-relative depth; the reference corpus author's published value for this dataset (his 2021 revision used 2.0, unreachable here below the gamma-10 ceiling — all lines cap at 10.000, widths 0.49–0.78%, stated per run) |
| ppgamma 2.7 / ppsigma 1.0 | post-peak partial gamma on Luv L above sky+1σw, as an RGB-ratio-preserving gain (max gain ×3.72 measured); chroma never stretched — the anti-mottle property; author's published values |
| satgamma 1.1 | LCh chroma gamma above the same gate (Cref = p99.9 of gated chroma); author's 2020 value (1.4 in his 2021 revision) |
| huerot 120–147.5 by −35 | the Hubble-palette shift (the reference's golds ARE its rotated Ha greens; pure Ha-green measures hue 127.7). Edges feathered ±8° + the gate ramp: hard boundaries measured to stipple/seam (a knot at hue 100–119 sits below the interval and stays yellow-green — huerot_from calibration is an open judgment flag) |
| scnr 0.5 | avg-neutral green blend, the author's published tricolor value (0.1 suggested for bicolor HOO in his docs) |
| stars_opacity 1.0 | screen combine with stars×k (industry reduced-opacity star subduing). 1.0 = bit-exact plain screen (sweep-proven). SHO ladder: mid-star peaks 249→205 (0.8)→164 (0.6), saturated stars 6%→0% at ≤0.8, starless layer bit-identical across rungs |
| starless_target 0.07 | sky rim is real: 0.12 → sky rings 4.4 FAIL |
| vstpost -mod=0.5 | every linear denoise placement imprints a radial signature on self-flat data (5.1/4.6 FAIL); post-stretch half-mod: grain −40%, gate clean |
| chroma_core 4 | bands 0.73/1.25 (k=3: 1.08/1.88); star-color cost −1% on the linked chain. NOTE: tuned on underexposed set-03 (colour ≈ noise); on a bright real-colour target (the LMC) k=4 over-neutralizes real Hα — revisit per data class |
| lum_core 2 | gray patches (stretch-amplified lum noise ±2 counts) removed; noise estimated on the statistical dark sky, correction Wiener-gated everywhere; NO geometric factor (a hard rect printed a 4.5× texture seam; the Wiener gate protects real structure) |
| black_point 8 | bg 16→8; dark-sky clip0 ~0.5% = the intended gap/lane blackness; floor P50 + contrast survive (linear shift preserves differences) |
| stars anchor 0.97 | mid-peak 255 vs 225 at 0.85; layers decoupled (gate untouched) |
| anchor basis = G (`peak_g`) | a max-over-channels anchor follows whichever channel wins, so a per-channel recalibration (SPCC K) moves it (measured −8.5/−20 counts16 mid/faint G, low-end gain ×864→×996 between builds of one sky); the G-basis amplitude rescales WITH its channel and cannot drift. The anchor's ABSOLUTE level is a per-dataset fact: top-500 is the brightest 2.2% of a 22916-star catalog but 59% of an 852-star one — no single rule sets star brightness across fields |
| stars_anchor catalog (noise = per-dataset tool) | `--stars-anchor noise` (k·σ_G) holds a physical star's brightness constant across rebuilds of ONE sky; k has no cross-dataset value by construction (k = anchor/σ_G restates one field's star statistics — a 491σ field's k is an 11.5× brightness error on a 44σ field), so noise mode requires `noise_anchor_k` from the dataset recipe |
| stars_floor 3.0 | ghost-aura fix: bright-tier aura +7.0→+2.0 (raw stretch = +0.5), halo 1.73→1.36, cores/mid-peak untouched, gate bit-identical |
| cull 50 | metric-invisible across the 0–50 ladder on set-03 AND visually+metrically null on a rich wheel field (M20, 0/25/50) — the faint-field difference vs reference finishes lives in the stars MTF anchoring + the starless floor, not the cull |
| satu 0.2 | fringe span scales ~(1+s): 79/94/107 for 0/0.2/0.35; 0.2 keeps star color at −12% fringe |
| jpg q100/4:4:4 | q92+4:2:0 cost mean 2.29 / max 176 counts at star edges / 9.7 star chroma (part of the "pixeled aura"); q100/4:4:4 = mean 0.44 / max 5; PNG8 = the lossless artifact the determinism check compares; PNG16 = the float render at 65536 levels (writer roundtrip-verified); finals embed sRGB colorimetry (588-byte vendored lcms profile, timestamp/ID zeroed → byte-deterministic; PNG sRGB/gAMA/cHRM chunks) with pixels IDENTICAL — the gate q92 jpg carries none (gate identity) |
| rbf_protect significance (generic) | the C9 information gap as per-dataset state — single-image statistics cannot tell frame-filling faint nebulosity from instrumental envelope: `significance` protects everything above global statistical sky (the SMC class, envelope IS the target; acceptance numbers await the off-disk stack), `band` protects only the 32–202 px structure class and absorbs frame-scale elevation (calibration-debt envelopes; set-02 measured gate PASS 7.0/5.9/2.5/3.7 with dust structure-scale 95–96% — and the USER REJECTED the look 2026-07-12: flattening a dark envelope LIFTS it into a wash; gate-PASS-but-look-rejected). Inert unless bgelin_mode rbf; NO dataset pins either value |
| rbf internals: σ_s 32 / ceiling 202 / grid 30×20 / λ 1e-3 / quad chroma | each constant measured on set-02: σ_s 32 keeps the 50 px class above the smoothing (dust detects at 51–53σ_band); ceiling 202 = class constant ~1.35× the 150 px structure top, DECOUPLED from spacing (0.65×spacing at the denser grid would expose the 100–200 px class); grid 15×10→30×20 resolved the 200–600 px aliasing zone (with quad chroma: rings 11.4→3.7); λ noise-matched (sample-residual RMS 0.086 c16 ≈ window noise — λ shapes nothing, dead ends); chroma quad per channel = the 3-FAIL→PASS iteration (first-degree ceiling colour 9, quad rms 1.41→0.42 c16) |

**Standing per-render audits (printed + logged every starcomb run):**
the GATE (`bg_qa` on the starless render, composition-agnostic sky scope:
colour ≤ 7, gradient ≤ 8, blotch ≤ 5, rings ≤ 8 on the statistical dark
sky, terrestrial foreground excluded — **thresholds never loosen**);
whole-frame QA as reference; `star_shell_report` (aura_lum WARN > 4.0 —
calibrated fixed +2.0 vs defect +12.0 on the same star sample; shell_chroma
is a TREND, no bound — honest PSF fringe dominates it and a fixed bound
cries wolf on clean renders); black_point clip0 sky; stars anchor +
MTF low-end gain (drift watch); star metrics.

**Per-frame quality assessment (the registration inspection)** — the
standard workflow's SubframeSelector step, measurement half only,
WARN-only, on every stack path (matched-flat, self-flat, FITS,
dual-band per line). At each runner `INS reg` call — BEFORE per-stage
cleanup prunes the sequence — `inspect_stage.py` parses the .seq
regdata siril already computed during registration (structure verified
against siril 1.4.4 seqfile.c: per frame fwhm, wfwhm, roundness,
quality, background, nstars + frame→reference homography) and persists
the full per-frame records + a .seq copy into the run's inspection
dir. Units are derived, never configured: FWHM px AND arcsec
(206.265·XPIXSZ/FOCALLEN from the sequence's own reference frame — the
solve-hint derivation; missing cards → px-only, stated; the dual-band
path's doubled XPIXSZ flows through, measured 4.00″/px on 1.99″/px
data); background normalized to counts16 (raw regdata units are
bitdepth-dependent — measured ADU-16 on 16-bit sequences, not [0,1]).
The record carries the FULL SHIFT LIST (homography translation terms)
plus 4×4-bin sub-pixel `dither_phase_frac` — the drizzle upgrade's
gating record (hoo_180s: 0.69 per line). `wfwhm_excess_pct` reads
matching LOSS distinctly from seeing (wfwhm = fwhm·(1 + 2·lost
matches/ref stars), 1.4.4 source; honest corpus 1.6–85%). Per-frame
outlier flags: robust z vs the sequence's own median/MAD, defect side
only (fwhm+, bg+, round−, nstars−), threshold 3.5 — calibrated on the
11-sequence corpus where non-event frames stay under |z|≈3.4 and every
3.5+ flag maps to a physical event (SHO dawn-glow final frames bg z
+10.9…+119; hoo seeing excursions fwhm z +4.4/+5.5; smc trailing spike
round −3.9 with nstars −13.6), each of which still stacked into an
approved/passing base — WHY flags WARN and never cull. Distribution
bounds are envelopes of the measured honest corpus (per-class
subranges in the expectations row; the SELF-FLAT class contributed no
sequence — wide_50mm's 28-frame D810A re-registration exceeds current
free disk and set-03 is off-disk — so its first future run may WARN
legitimately: revisit bounds there, don't ignore); per-dataset
override = optional `frame_qa` block in recipe.json ({metric:
[lo, hi]}, provenance printed; a stateless dataset degrades loudly to
generic bounds).
Consumers: deconvolution eligibility reads `fwhm_med_px` (sampling —
hoo's extracted lines measure 1.58–1.61 px, undersampled, the drizzle
case) + `fwhm_cv_pct`/`round_med` (PSF stability); the acquisition
checklist reads the per-frame flags; the stack-policy `exclude` list
names frames by this stage's recorded `n`. Weighting/culling POLICY is
deliberately not part of the measurement stage — its surface SHIPPED
2026-07-12 as the per-dataset `"stack"` recipe block (stack-builder
paragraph above: resolution, mechanisms, trigger doctrine), byte-inert
until a recipe opts in with a measured reason; NO dataset pins one
(low-spread weighting measured actively harmful — the dead-end entry
carries the ramp numbers — and the honest corpus 2.0–34.0% CV all
stacked clean unweighted).

## Per-stage expectations (inspection contract)

Mirrored in `inspect_stage.py EXPECTATIONS` (keep in sync). WARN-only —
inspection never aborts; the hard gate stays `bg_qa.py`. Bounds are
sanity envelopes calibrated on set-03 (some self-flat-specific); a new
data class may WARN legitimately — revisit bounds there, don't ignore.

| stage | PASS bound (short) |
|---|---|
| master_dark | level16 / ceiling-clip / hot-frac all INFO (offset, sensor and gain facts — measured bias 155, darks 168–1316 c16, hot 0.001–1.5%; prebuilt ADU-scale masters normalized /65535) |
| master_flat | corner/center 0.35–1.02; coherent dust dip ≤ 5% (measured clean flats 0.3–0.9%); clip < 0.5%; level % INFO (histogram-peak exposure fact, goal ~50%) |
| calibrated | clip < 0.5%; stars ≥ 150; bg median16 INFO (a site/sensor fact — dark-site cooled mono ~35, light-polluted DSLR ~370–600) |
| selfflat_median | star ratio ≤ 5% of calibrated; corner/center 0.35–0.75 |
| subsky_frame | G median within ±10% of calibrated (tilt is INFO — bowl reads ~9–13% in any plane fit) |
| gain | monotone non-increasing (THE ring guard); corner 0.38–0.58; gray (spread 0) |
| divided | p2v(r≤0.85) ≤ 0.20; rim(r>0.9) ≤ 0.25 |
| registration | registered/total ≥ 0.9; fwhm_cv_pct ≤ 45 (honest corpus: guided classes 2.0–16.2, multi-hour 400–600 s archive 21.6–34.0); round_med ≥ 0.30 (corpus 0.71–0.90; the trailed-tripod class ≈ 0.5 must pass); bg_span_pct ≤ 130 (stable classes 2.5–9.6; dawn-flank archive members 51–103); nstars_min_frac ≥ 0.35 (stable 0.74–1.00; dawn-flank 0.47–0.62); per-frame outliers flagged at robust z 3.5 defect-side (fwhm+/bg+/round−/nstars−); INFO: fwhm med px+arcsec (sampling ratio, scale printed), wfwhm excess (matching loss), dither phase coverage (4×4 bins), shift range |
| stack | dark-sky p2v ≤ 0.20 on the statistical sky (a frame-filling object doesn't read as a defect); stars ≥ 300; noise/median, median16, sky_frac all INFO (ratios to an arbitrary pedestal / data-class facts) |
| compose | median star-centroid offset between composed channels ≤ 1.0 px (the lines must overlay without a second interpolation pass); p95 INFO |

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

Constrained extraction (v2 calibration, set-02):
- Symmetric compass sky references for retention grading → BLIND to a
  locally-linear absorption ramp by construction (gx's measured
  −1.1..−2.3 c16 differential read 93–108% through them; plane reads
  ~100% for the same reason). Retention local-sky references must be
  ONE-SIDED — darkest compass direction, geometry fixed on the stack.
- Masked-fraction cell eligibility (skip a sample cell at >50%
  masked) → starves texture-dense fields: 37/150 cells, whole frame
  bands unsampled, rendered grad 10.7. Eligibility = CLEAN-CORE (a
  fully unmasked value window surviving erosion), never area
  fraction — the mask itself knows where the clean sky is.
- RBF smoothing λ as a mid-scale-wiggle fix → four decades
  (1e-8→1e-2) moved the surface's 50–400 px MAD only 0.64→0.46 c16;
  the content was REAL 200–600 px sky structure ALIASED by the ~300
  px sample spacing — fixed by grid density (Nyquist), not
  regularization. λ stays at its noise-matched value (sample-residual
  RMS ≈ window noise); it shapes nothing.
- First-degree per-channel chroma correction on a curved coloured-LP
  field → colour 9 (plane's subsky reads 7.0 — the same first-degree
  ceiling). QUADRATIC per channel is the working low-order form
  (chroma residual rms 1.41/0.97→0.42/0.47 c16), block-scale rigidity
  preserved by construction; full per-channel spatial freedom stays
  the recorded colour-31 dead end.
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
  differentially amplify noise = the chroma-blotch ("rainbow") engine;
  there is no cast left for it to compensate after SPCC.
- Unlinked (sky-anchored per-channel) autostretch as the NARROWBAND-
  palette line-lift → NO-OP on this chain: BGE+SPCC already equalize
  the channel SKIES (49.5/48.2/48.1 e-4 on the SHO stack), and
  autostretch anchors on sky, so unlinked ≡ linked (sphere O3
  interior 1271 vs 1337 e-4; every sphere metric within noise). The
  line imbalance is OBJECT flux above a common sky.
- GraXpert AI smoothing as faint-nebulosity protection → NON-FIX by
  design AND by measurement: the team states smoothing "does not
  influence the result produced by the AI model" (it gaussian-blurs
  the model output), and max smoothing 1.0 still absorbed the Bubble
  dust (Ha probes +10.3/+5.8/+10.9/+9.9/+2.8 e-4 → +3.1/+0.5/+1.1/
  −1.3/−2.0 — retention 5–30% with over-subtraction). Mechanism: the
  AI infers on a 256 px thumbnail where a frame-filling faint complex
  is an ~85 px blob ≡ the trained-on light-pollution class, and its
  ±25·MAD input clip keeps 3–10σ dust fully inside the absorbable
  range while bright objects saturate out (why compact objects
  survive). The team's own FAQ: "sometimes it subtracts too much from
  my target" — their fix is retraining, not a knob. bgelin_mode
  plane/off (or preferences-file RBF with off-object samples) are the
  admissible handlings for object-filling fields.
- OBJECT-anchored per-line stretch (each line's p90-of-significant →
  a display target) → lifts the faint end past its noise budget; the
  corings then partial-Wiener-shrink the lifted grain into 40–120 px
  kept-vs-flattened MOTTLE ("blotchy", user-rejected across two
  packages — with the ghs lift and with relaxed corings alike). RGB-
  space stretching also amplifies CHROMA noise wholesale. The
  admissible per-line stretch is NOISE-WIDTH-CAPPED with luminance-
  only post-peak lifting (the reference chain's mechanism, in the
  design section); hard significance gates and hard hue-interval
  edges in the finishing ops stipple/seam — ramp and feather them.
- `rmgreen` on a sky that is not green-dominant → global magenta.
- Linear denoise (vst or GraXpert), ANY placement on self-flat data →
  noise is radial after V(r) division; adaptive smoothing imprints a
  radial signature → rings 4.1–5.1 FAIL. Only post-stretch
  `-vst -mod=0.5` on the starless render passes.
- Chroma blur (σ2/4) + satu → scale-blind to 48–128 px blotches; satu
  re-amplifies everything ×1.25 → rainbow WORSE. The fix is
  significance coring (Wiener, multi-scale), not blurring.
- A fixed shell_chroma WARN bound → cried wolf on a clean render
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
  structure into the stars layer (measured over the same components). Running
  the net ON an inpaint starless cannot fix it either — that base has already
  lost the knots, and no downstream inference can restore them.
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
- CFA-lattice (undebayered) registration as a frame-QA instrument →
  false positives on cloud texture. Measured (6-frame control, 3 clear
  + 3 cloud-band): the 2-pass reference chooser PICKED a band frame —
  cloud texture reads as detections (nstars 1899 vs clear 1848, fwhm
  2.83 ≈ stellar) — and the adjacent band frames cross-matched each
  other on cloud structure (near-identity H) while a clear frame
  FAILED. The same six frames debayered: reference lands clear, all
  three band frames fail matching, clear frames register. Frame QA and
  registration run on DEBAYERED calibrated data only; the CFA
  shortcut's disk savings are not worth a poisoned instrument.
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
- "Per-pixel rejection + addscale absorb any cloud passage" (the
  dawn-glow generalization) → PARTIALLY KILLED. Holds for transients
  and short tails; FAILS for a band that DWELLS over one sky region:
  ~30 frames (12% of the set) kept a slow cirrus band over the same
  upper-left zone, cloud-affected values became the per-pixel MAJORITY
  there, and `rej 3 3` kept them — the all-frames stack carried
  coherent fibrous residue (E1−E0 diff block structure 3.7 c16) and
  its render's rings metric sat AT the 8.0 bound. Excluding the 31
  z-flagged frames removed the residue (rings 6.6) at exactly the
  √(240/209) = +7.5% noise price. Cull clouds by PER-PIXEL MAJORITY
  RISK, not by visibility: a moving minority band stacks clean, a
  dwelling one does not.
- nstars as a cloud discriminant at `setfindstar -sigma=0.5` → BLIND
  on rich fields: detection saturates at siril's 2000-star cap on
  every frame (240/240 read exactly 2000), so nstars z ≡ 0. The bg
  channel carried the entire cloud signal instead. Raise the cap or
  the sigma before trusting nstars flags on wide MW fields.
- wFWHM weighting at low FWHM spread → WORSE than the recorded "no-op":
  siril's -weight is a min-max RAMP over the sequence (worst frame → ~0
  weight at ANY spread; measured at 7.4% CV: weights 1.93..−0.00, N_eff
  11.9/16, +21% statistical-sky noise, +24 c16 pedestal from the
  weight×sky-drift correlation). The set-03-era "~6% spread → would be
  a no-op" line was an unrun prediction; the measurement replaces it:
  at low spread weighting is all noise cost for zero crispness need.
  Per-dataset tool ONLY, on a recorded trigger (fwhm_cv_pct far above
  this regime, or cloud-class outlier flags) — never a default.
- Drizzle → heavily oversampled at 24 mm/5.9 µm; pointless.
- Deconvolution (makepsf + RL) → fitted PSF ≈ symmetric (trailing is
  in-exposure), unstable on ≈0 background; no de-trailing.

Separation/stars:
- Lowering starsep prominence (6→5→4σ) to catch the faint tail → NULL:
  residual starless detections 5137/5179/5159 — the stipple is
  noise-level clumping, not separable stars.
- StarNet official binaries on Linux aarch64 → none exists through
  v2.5.3 (x64 + macOS-ARM only). The weights file inside the official
  Linux x64 package runs under an aarch64 onnxruntime wheel — the `net`
  engine.
- The stars-layer skirt annulus is the ghost-aura engine (MTF ×~10³
  low-end gain on subtraction noise): fixed by stars_floor, NOT by
  smaller dilation (cliff moves brighter), NOT by feathering alone
  (doesn't touch the amplified wing).

QA/scope:
- Whole-frame QA as the gate on a separated chain → reads real MW/object
  signal as a background artifact ("ring 6.1" was pure MW signal); a
  geometric sky mask cannot fix it (a bright object has no fixed band to
  configure). The gate runs a composition-agnostic STATISTICAL sky scope;
  whole-frame stays a reported reference.
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
- "the offline whole-frame trend proxy predicts the rendered gradient" →
  mispredicted twice on the constrained-extraction ladder (proxy improved
  while rendered grad went 4.8→9.2): the gate measures the STRETCHED sky
  through the adaptive chain (autostretch parameters, corings, black
  point). Only a gate-scope proxy — dark-block selection + plane fit on
  the LINEAR residual — tracked the render; whole-frame P2V does not.

## Bandaid/adaptation ledger (every divergence carries its removal condition)

1. **Self-flat chain** (median → V2 → rechroma → divide) — ADAPTATION,
   measured. Dies when real flats exist at the set's focal length
   (preflight auto-routes; the matched-flat path is proven end-to-end).
2. **Per-frame `seqsubsky 1`** — ADAPTATION on the self-flat branch
   only (stack-level-only BGE measured FAIL, see dead ends). Dies with
   real flats.
3. **mask+inpaint separation as the weights-absent fallback** — the
   StarNet2 weights are an external, personally-licensed file, so the
   pipeline must still render without them; the fallback engine cannot
   tell an HII knot from a star (26% of a resolved object's detections
   were structure, inpainted away — see dead ends) and WARNs when >10%
   of its detections sit inside an extended-object envelope. Dies if a
   redistributable separation model replaces the licensed weights.
   Also carries the wide_50mm engine pin: on that 41° MW-dominated
   self-flat class the net's residual structure fails the gate
   (grad/rings 9.0/9.0 vs 6.4/4.2), so the recipe pins `inpaint`; dies
   when a separation model without the bright-star-shell class lands
   (BACKLOG). Costs owned where inpaint runs: <6σ faint tail left in
   the starless layer; skirt-aura class (mitigated by stars_floor).
4. **Post-stretch denoise** (`-vst -mod=0.5` on the starless render) —
   ADAPTATION for self-flat data, where noise is radial after V(r)
   division and every linear denoise placement imprints a radial
   signature (measured FAIL, see dead ends). Standard linear placement
   (`--starless-denoise gx`) stays available per data class.
5. **NEF→DNG conversion for Z6III High-Efficiency frames** — siril
   1.4.4 bundles LibRaw 0.22.0-Devel202502, which cannot decode Nikon
   HE/HE★ (TicoRAW); Adobe DNG Converter licenses that decode. Every
   other camera raw ingests directly (`raw_find` globs NEF/DNG/CR2/CR3/
   ARW/RAF/ORF/RW2/PEF/SRW and siril debayers them). Dies when
   acquisition records 14-bit Lossless NEF (see checklist) or the
   bundled LibRaw lists the Z6III body (released 0.22 does).

## Checklist for future acquisition sessions (the real quality lever)

- Record **14-bit Lossless-compressed NEF**, NOT High-Efficiency
  (HE/HE★): menu Photo Shooting → RAW Recording → Lossless. HE is
  TicoRAW-compressed (LibRaw can't decode → forces the NEF→DNG fallback
  in the ledger) and lossy-ish; Lossless preserves faint linear signal.
  Confirm 14-bit (high-speed continuous can drop to 12-bit).
- ISO 800 (Z6III second gain stage), subs ≤ 500/focal (13s @ 38 mm,
  20s @ 24 mm) — trailing, not noise, capped set-03's sharpness
- MORE integration: MW-band signal/grain ≈ 1 at 8.75 min ISO 200 —
  every processing knob is polishing presentation until photons improve
- Flats per focal length used that night, BEFORE touching the zoom;
  histogram peak ~50% — METER IT, don't trust a shutter value (Jul-5:
  1/160 s landed ~27%; session_02: 1/640 s landed ~6% = a visibly
  noisy master; ~1/50 s at the Jul-5 screen brightness was right);
  diffuse the screen (cloth over lens + distance — the pixel grid
  showed at ~0.3% RMS)
- VERIFY the flat source is uniform: shoot one flat, rotate the camera
  180° against the source, shoot another — the two corner/center
  ratios must match (session_02's flats carried ~3× extra source
  falloff over the lens's real vignette and were unusable; the lights'
  own sky is the cross-check: sky corner/center ≈ lens falloff)
- Darks same exposure/ISO at night temps; biases at the flats' shutter
  (= exact flat-darks). Missing biases degrade to the documented
  synthetic-offset fallback (fine for the flat term) — shoot them
  anyway; they are 30 seconds of work
- Lock the zoom ring (tape); don't touch the camera mid-set (set-03's
  37→38 mm step happened at a handled pause)
- Dither between subs; avoid the moon (star fringes on trailed PSFs
  are dispersion — physical, satu only multiplies them)
- A fast lens WIDE OPEN adds a red veiling-glare halo around bright stars
  (measured: Sigma 180 @ f/2.8 = a +4..+5 count R−G plateau to r≈38; the
  SAME body at 50 mm f/4 is clean) — stop any fast lens down ≥1 stop for
  bright-star fields. It is an honest optical signature, not removable in
  processing without a bandaid.
