# Astrophotography processing pipeline — technical reference

This file describes the pipeline **technically**: what each stage does and
the technical reason it does it, plus the dead-end registry (what does not
work, and the mechanism why). It carries **no history and no dataset
names** — a choice is justified by the mechanism it exploits, not by the
frame it was tuned on. History lives in **git** (`git log`); per-dataset
state (approved knobs + measured baseline) lives in
`datasets/<session>/<set>/`. `README.md` is the process contract
(standard-workflow mapping, review contract, experiment discipline,
per-set geometry, north star). Keep this file technical: if a step has no
statable technical reason, that is a signal the step is wrong, not
something to document around.

## Environment

Rig/tooling facts live in **`CLAUDE.md`** (git-tracked, auto-loaded into
agent sessions): flatpak siril invocation + the /tmp rule, hardware/disk
constraints, python stack (no astropy), GraXpert, astrometry venv, local
Gaia catalog layout. SPCC needs the FULL local xpsamp cone for the solved
field; `scripts/calibrate/spcc_cone.py <solved_wcs.fit> [--fetch]` computes
the nside=2 nested HEALPix cover from the solved WCS (projecting the true
image centre, not CRVAL) and downloads any missing chunk (md5-verified). A
southern field needs southern chunks — the tool names and fetches them.

## Design (what each stage does and why)

**Stack builder (`run_pipeline.sh`)** — preflight (exiftool): hard-fail on
empty/mixed frame dirs; flats are used only when flats+biases exist AND
optics match the set, else the self-flat path. Registration floor on every
path: under HALF the set registered ABORTS the run (0.5 is a design pick —
half the set is not the set; the 0.9 advisory WARN stays inspection-side, a
60–90% set stacks loudly). Masters rebuild on manifest change
(names+sizes+mtimes — catches re-shot frames with stale timestamps).
Calibrate `-dark -cc=dark` (+flat +equalize_cfa when matched) →
`setfindstar -sigma=0.5` (a low detection sigma roughly doubles detected
stars; the blind triangle matcher needs the extra stars on sparse trailed
fields) → two-pass register → 32-bit rejection stack, `-norm=addscale
-output_norm`, **no `-rgb_equal`**: SPCC calibrates the raw Bayer balance
downstream from star photometry, and a pre-normalizer would hide exactly
the per-channel imbalance (two green photosites + per-channel QE) that SPCC
is designed to measure.

**Stack policy (optional `"stack"` recipe block)** — run_pipeline resolves
`{"weight": "wfwhm"|"nbstars"|null, "exclude": [frame numbers]}` from the
dataset recipe at stack time (recipe-only knob, no generic layer;
provenance printed) and applies it on every stack path (matched-flat, FITS
single, dual-band per line, self-flat). An absent/null/empty block is the
generic default: unweighted `rej 3 3` with byte-identical generated
scripts. Weight → `-weight=` on the stack line (regdata carries through
both seqapplyreg and direct register); exclude → `unselect <r_seq> n n`
lines + `-filter-incl` (MANDATORY: a plain stack ignores manual selection),
where n is the registration inspection's per-frame `n`. Identity caveat:
`unselect` indexes by 1-based POSITION, while a registration-reduced
sequence keeps original file numbers with gaps — position == n only on
contiguous sequences — so with any exclude the runner re-reads the stacked
.seq afterward (`verify_exclusion`) and hard-fails, removing the stack,
unless exactly the named file numbers were deselected. Trigger doctrine:
OFF generically. Siril's `-weight` is a min-max RAMP over the sequence's
regdata — the worst frame is driven toward zero weight at ANY spread, i.e.
soft-culling — so at low FWHM spread it adds sky noise (fewer effective
frames) for no crispness gain; rejection + addscale already absorb
transients and frame-level excursions. A weight or cull is therefore
per-dataset state, adopted only through a with-vs-without ladder when the
recorded registration-inspection numbers show a real trigger (FWHM CV far
above the low-spread regime, or cloud-class outlier flags). Any weight/cull
rebuilds the stack = a declared delta through gate + inspection.

**Dedicated-astrocam FITS branch (cooled mono/OSC)** — a set of `.fits`
lights forks to a FITS ingest: `fitsmeta.py` reads
exposure/gain/offset/filter/mono from the headers (the free-text `FILTER`
keyword — an SBIG convention, not validated core FITS — is normalized to a
canonical token; a mixed dir fails loud). Flats are matched to the lights
**by FILTER**, because vignetting and dust shadows are wavelength-dependent
so a flat is valid only for its own filter, and are calibrated with
**dark-flats** (darks matched to the flat exposure): a multi-second flat
carries dark current a bias cannot remove (`biases/` is the fallback).
Darks are filter-independent, matched by exposure/gain/offset. A mono light
is never debayered (no `BAYERPAT`); an OSC CFA FITS gets `-cfa -debayer`.
The render detects a 1-channel stack and takes the luminance-only path —
the final saturation acts on channel differences that are identically zero,
and SPCC has no colour to calibrate. A single-channel
FITS must be written `NAXIS=2`: siril's reader rejects a degenerate
`NAXIS3=1` cube. The `FILTER` keyword is optional in practice (some
capture software writes none): an absent filter normalizes to `-` on both
lights and flats so they still match, and filter identity then rests on the
directory staging. A master-only corpus stages PREBUILT masters in
`<session>/calib/{dark,flat}_<token>.fits`, matched by the normalized
FILENAME token — such masters carry no headers, so the filename is the
whole identity and the exposure match is unverifiable (both stated per
run); raw dirs win when both exist. Siril normalizes their ADU-scale floats
to [0,1] on import (same convention as ushort lights), so staging is a
plain copy, tracked by SOURCE identity (name+size+mtime marker) not file
mtime: a freshly staged master is always newer than every `calib/` source,
so an mtime test would keep the previous filter's dark.

**Dual-band OSC composition (`composition.json` + `compose.py`)** — a set
whose composition record is kind `dualband-osc` calibrates the CFA mosaic
(no debayer — the emission lines live on distinct photosites), splits each
frame into its lines (`seqextract_HaOIII -resample=oiii`: Ha native
half-size from the R photosites, XPIXSZ doubling so the header-derived solve
hint stays correct; OIII downsampled to the same size so NO channel carries
invented detail), and registers BOTH line sequences to the same
mid-sequence reference frame so the channels overlay without a second
interpolation pass. That overlay is MEASURED, not assumed: the star-centroid
residual between composed channels prints every compose and lands in the
inspection report (bound 1.0 px; the residual floor is the R-vs-G/B CFA
phase offset plus independent per-line transform fits). Then per-line stacks
compose R/G/B per the palette mapping into `stack_<set>_comp.fit`, which
enters the ordinary flow: solve → SPCC `-narrowband` with per-channel
emission wavelengths from the recipe (Ha 656.28, OIII 500.7 nm; the
narrowband mode changes the fit vs broadband-null, and G≡B falls out of the
identical synthesized OIII filters) → render unchanged. The full-size path
(native Ha + 2× drizzle instead of downsampling OIII) is the BACKLOG upgrade,
gated on measured dither coverage. No composition record → the set processes
as an ordinary single stack (a dual-band set then debayers like broadband:
legal, but its lines stay merged — the record encodes the data's goal).

**Mono filter-wheel composition (kind `mono-filters`)** — members are
SIBLING per-filter sets (each stacked by the ordinary mono path, per-filter
flats matched by FILTER keyword), keyed by a VIRTUAL target name. Different
frames per channel mean nothing overlays by construction, so `compose.py`
aligns the member STACKS first: a siril sequence registration to the
composition's `reference` member — ONE interpolation pass, and the reference
channel carries only the identity transform (choose the perceptually
dominant member). Stack-level star fields are registration-rich and no CFA
phase offset exists on this path, so the alignment lands well inside the
1.0 px bound. Alignment uses `-framing=min` (intersection): a pixel the
composed product ships must exist in EVERY channel, because compositing an
uncovered margin fabricates colour there (an uncovered block reads a strong
channel difference on otherwise neutral sky and fails the colour gate). A
composition naming a `luminance` member is REFUSED: LRGB joins L after both
parts are stretched, which compose-then-render cannot express — that design
lands with the LRGB corpus (BACKLOG).

**Self-flat branch (flatless sets)** — median of UNREGISTERED calibrated
frames (drifting stars self-reject) → per-frame planar glow subtraction
(`seqsubsky 1`, sensor coords, while linear) → `rechroma.py` shifts the R/B
medians to model-consistent targets (constants only — it cannot create
spatial structure; without it siril's per-channel level restoration prints a
magenta rim) → V2 gain fit from the median of the frames ACTUALLY being
divided (`selfflat.py`: block grid, sigma-clip, **binned radial medians +
isotonic non-increasing regression, GRAY** channel-mean) → divide →
**registration reference sweep** (mid-sequence outward, keep best,
early-stop) → stack. Why each odd piece is forced:

- A polynomial radial V(r) oscillates and prints concentric RINGS after
  division; only a monotone isotonic V is admissible.
- A per-channel V tints the corners, because the glow contaminates the
  per-channel falloff; V must be GRAY.
- Estimating V from glow-subtracted frames without rechroma breaks the
  pedestal/bowl ratio (siril's per-channel level restoration), so the
  divisor tints the corners.
- The true V lies between the multiplicative and the additive fit of the
  median, so neither a-priori model lands flat; only the empirical V2 of
  the actual frames being divided does.
- With trailed stars, registration matching is reference-dependent, so the
  reference is swept rather than auto-picked.
- Per-frame `seqsubsky 1` must stay on this branch: a stack-level-only BGE
  leaves a structured residual (rings) and loses more of the Milky Way.

**Plate solve (`solve_field.py`)** — blind astrometry.net on coarse
background-subtracted PEAK centroids: siril's PSF detection and starsep blob
centroids both fail to feed the matcher on trailed stars, and siril's
internal solver caps its cone and fails matching ultra-wide fields even with
local catalogs. The scale hint is derived from FOCALLEN/XPIXSZ in the header
(a hard-coded range cannot generalize across focals). Detection is
foreground-masked (treeline tips and glow edges poison the matcher). A
TAN-SIP WCS is injected for siril `spcc`.

**Per-set geometry (`datasets/<session>/<set>/geometry.json` +
`astrometrics.configure`)** — the only per-set composition fact is the
terrestrial FOREGROUND (a rect, or a pixel mask from `suggest_foreground.py`
— thresholded well below the sky level, border-anchored components, dilated
for the drift-smear halo — or none) plus its judgment crops. No geometry
file → foreground none. Border-anchor invariant, enforced at configure/load:
a foreground that touches no frame border is REFUSED, because the foreground
is excluded from the gate's sky scope and an interior "foreground" would
silently shrink the gate's jurisdiction (terrestrial obstructions enter from
an edge by construction). The background is never a per-set input: the gate
selects its sky STATISTICALLY (below) because bright celestial signal has no
fixed geometry a mask could scope.

**Render-engine routing (`render_engine`)** — `starcomb.py` is the default
render entry, but a dataset can declare its engine (`render_engine` in
recipe.json: auto|starcomb|nightlight). A mono-filters NARROWBAND (SHO)
composition auto-resolves to `nightlight` and starcomb DELEGATES to
`nightlight_sho.py` — the reference author's own tool, whose star-neutral
balance recovers the O3 sphere our SPCC equalizes away. Everything else is
the in-house chain below. The in-house chain is TOOL-ONLY (every
pixel-rewriting operator drives siril / GraXpert / StarNet2); the narrowband
colour+develop mechanism Siril has no equivalent for (per-line stretch + the
O3-sphere star-neutral balance) lives ONLY in Nightlight, not as an in-house
numpy path — a `--stack`/`--param` run of a narrowband set on starcomb gets
the broadband linked stretch (dominant line only) and says so.

**Product chain (`starcomb.py`)** on the SPCC stack — knob values resolve
CLI > `datasets/<session>/<set>/recipe.json` > `datasets/GENERIC.json`
(provenance printed; a recipe-less dataset renders generic and says so).
Every operator that rewrites the deliverable's pixels drives a tool;
python computes parameters (anchors, thresholds, clip fractions) and
MEASURES, siril/GraXpert/StarNet2 apply:

1. Linear background handling per `bgelin_mode`:
   - **gx** (generic) = GraXpert BGE + `subsky 1` on the STAR-FUL linear.
     Extraction must run before star separation: on a star-removed frame the
     frame-filling Milky Way reads as background and is absorbed, so the
     star-ful order preserves it. CLASS LIMIT: GraXpert's model cannot
     distinguish frame-filling FAINT nebulosity from a sky gradient at
     similar spatial scales, so it absorbs the faint nebulosity as
     background (its input clip keeps low-sigma diffuse signal inside the
     absorbable range, while bright compact objects saturate out and
     survive).
   - **plane** = `subsky 1` only. A first-degree plane removes the gate's
     gradient class and cannot absorb a localized cloud/object by
     construction — the retention mode for fields that ARE mostly object.
   - **off** = passthrough (measurement rungs).

   `subsky` runs WITHOUT `-dither`: dither injects unseeded noise (breaking
   byte-determinism) to mask quantization banding that cannot occur on a
   32-bit float chain, so it is pure liability here.

2. Star separation, engine per recipe (`auto` = net when the StarNet2
   weights are installed, else inpaint):
   - **net** (`starnet_sep.py`, StarNet2 ONNX on aarch64) runs linear under
     an exactly-invertible MTF pre-stretch — the vendor-sanctioned placement.
     It is the fail-safe: it keeps field-star flux and does not destroy
     resolved-object structure. Its failure mode is a cosmetic bright-star
     shell, and it is LOUD (residual large-scale structure fails the gate).
   - **inpaint** (`starsep.py`, mask+inpaint): local-bg detection, prominence
     threshold, area caps (geometry-overridable), skirt dilation, pyramid-seed
     + Jacobi inpaint, deterministic seed. It keys on compactness + prominence
     and has no notion of an extended object, so it cannot tell an HII knot
     from a star and destroys resolved structure (it WARNs when >10% of its
     detections sit inside an extended-object envelope), and it leaves the
     faint sub-threshold tail in the starless. Its failure is SILENT — real
     structure lost on an otherwise passing render.

   Both engines emit the same trio + an engine-invariant detection catalog,
   so culling/anchoring/shell audits measure them identically.

3. Starless stretch by **siril `autostretch`** (`stretch_linked`): **linked**
   (broadband/mono standard — one calibrated scene, one transfer for all
   channels; unlinked per-channel curves differentially amplify noise into
   chroma blotches, and after SPCC there is no cast left for them to
   compensate). `auto` → linked (the in-house chain serves the broadband/mono
   class; narrowband-palette colour+develop is Nightlight's job — a linked
   MTF on a narrowband composite renders only the dominant line, the reason
   Nightlight owns that class).

   Then post-stretch **siril `denoise -vst -mod=0.5`** (`starless_denoise`;
   `gx` swaps in GraXpert AI denoise, `vst` the linear placement, `off`
   none) → black_point by **siril `mtf b 0.5 1`** (a midtones balance of
   0.5 is the identity transfer, so a low shadow clip at b is exactly the
   linear rescale (x-b)/(1-b); the clip fraction is measured in python, the
   transform is siril's). The gate jpg (q92, pinned — this encoding IS the
   gate's identity) is written here, before the combine. There is NO
   in-house significance-coring stage: the tool denoisers (siril VST /
   GraXpert) are the denoise operators; the multi-scale Wiener corings were
   hand-rolled numpy and were removed (a tool-only chain leaves that hole
   rather than reintroduce numpy — ladder tool-denoise strength per class).

4. Stars: cull the faintest half by flux → floor the star layer at
   `stars_floor`×σ (python threshold clip, catalog/σ measured) → rendered by
   **siril `mtf 0 m 1`**, the single-parameter midtones transfer with a
   data-derived anchor m (`solve_mtf_m` over the top-tier star amplitude on
   the fixed G basis `peak_g`, or k·σ_G) computed in python and APPLIED by
   siril.

5. Recombine + finish by siril: **siril `pm`** screen blend
   1-(1-a)(1-b·opacity) (the star-layer opacity folded into the PixelMath
   expression) → **siril `satu`** chroma gain → jpg q100/4:4:4 (+ PNG8 +
   PNG16 with `--lossless`). Every final is sRGB-tagged (JPEG ICC + PNG
   chunks); the gate's q92 starless jpg carries no tag (gate identity).

**Knob reference (what each knob does and the technical reason; a value
marked *tuned default* has no cross-data universal — re-derive per data
class through a one-knob ladder):**

| knob = value | what it does / why |
|---|---|
| SPCC, not `rgb_equal` | SPCC fits the per-channel colour balance from star photometry on the raw-Bayer stack. The raw channels are imbalanced (two G photosites + per-channel QE); `rgb_equal` would pre-normalize that away and hide exactly what SPCC measures. |
| SPCC sensor spec = null (default) | With no `-oscsensor/-oscfilter`, SPCC uses a generic response to convert Gaia spectra to expected fluxes; the star fit dominates, so supplying a sensor's true curve is a refinement (opt in via the recipe's `"spcc"` block only for a sensor with a known-divergent response), not a requirement. |
| SPCC placement = pre-BGE | SPCC uses per-star local-annulus photometry, which cancels the smooth background, so the star-colour fit is the same before or after background extraction. Solve+SPCC therefore stay stack products, ahead of the render's BGE. |
| no crop stage (default) | Canonical chains crop registration borders because border pixels have fewer contributing frames. A rigidly-registered set has fully-covered borders carrying only a smooth low-amplitude level plane, so trimming changes nothing. A DRIFTING set is the exception — its under-covered border band is a real fake-falloff and is cropped by `crop_coverage.py` to the coverage-complete rectangle. |
| bge_first order | Extract background before star separation: on a star-removed frame the frame-filling Milky Way looks like background and is absorbed; the star-ful order preserves it. |
| stretch_linked auto | The channel coupling of siril `autostretch`: broadband/mono → linked (a calibrated scene needs one transfer; unlinked = the per-channel chroma-blotch engine, a measurement rung). `auto` → linked; narrowband-palette colour+develop is Nightlight's job, not an in-house stretch mode. |
| stars_opacity 1.0 | Reduced-opacity star screen (industry star-subduing); the star layer is screened at ×opacity, folded into the siril `pm` screen expression as a scalar. 1.0 = plain screen. Lower subdues bright star tops at the cost of dimming all stars. |
| starless_target 0.07 | The sky background's display level. Too high lifts the estimator's rim residual into visibility; the low target keeps the sky dark where the residual lives. *Tuned default.* |
| vstpost -mod=0.5 | Post-stretch VST denoise at half strength. It is post-stretch, not a linear placement, because on self-flat data the noise is radial after V(r) division, so any linear adaptive denoise imprints a radial signature; a post-stretch half-mod pass avoids that. |
| black_point 8 | A linear black-point shift by siril `mtf b 0.5 1` (midtones 0.5 = identity transfer, low shadow clip at b): it moves the floor while preserving contrast and all differences. Set to place the sky floor just above clip; the intended gap/lane blackness clips, the smooth sky barely does. *Tuned default.* |
| stars anchor 0.97 (`stars_peak`) | The `mtf 0 m 1` target for the star layer's median top-tier star; m is solved from it and applied by siril. Decoupled from the gate (stars and starless are separate layers). *Tuned default.* |
| anchor basis = G (`peak_g`) | The anchor is measured on the G channel, not max-over-channels. A max-over-channels anchor follows whichever channel is brightest, so a per-channel recalibration (SPCC K) shifts it between builds; a fixed-channel amplitude rescales with its own channel and cannot drift. The anchor's ABSOLUTE level is inherently per-field (top-tier is a tiny fraction of a rich star catalog but a large fraction of a sparse one), so no single value sets star brightness across fields. |
| stars_anchor catalog vs noise | `catalog` anchors on the top-tier star population; its absolute level is per-field. `noise` (k·σ_G) holds a physical star's brightness across rebuilds of ONE field, but k restates that field's star statistics and has no cross-field value, so noise mode requires `noise_anchor_k` from the recipe. |
| stars_floor 3.0 | Floors the star layer at 3σ to kill the ghost aura: the stars-layer skirt annulus amplifies star-subtraction noise through the MTF's very large low-end gain, and flooring cuts that wing (a smaller dilation just moves the cliff brighter; feathering alone does not touch the amplified wing). *Tuned default.* |
| cull 50 | Culls the faintest half of detections (noise-level clumping) before the star MTF. The faint-field character is set by the star MTF anchor + the starless floor, not the cull, so the exact value is not critical. |
| satu 0.2 | Final saturation gain by siril `satu <amount> 0 6` (background_factor 0 = all pixels, hue index 6 = all hues) on the combined render. Saturation scales all colour including star-edge fringe, so it is kept low to avoid amplifying the fringe. *Tuned default.* |
| jpg q100/4:4:4 | The final JPEG. q92 + 4:2:0 chroma subsampling halves chroma resolution and adds star-edge ringing (visible as a pixeled aura); q100/4:4:4 avoids it. PNG8 is the lossless artifact the determinism check compares; PNG16 is the float render at 65536 levels. Finals embed sRGB colorimetry (vendored lcms profile, timestamp/ID zeroed for byte-determinism) with pixels identical; the gate q92 jpg carries none (gate identity). |

**Standing per-render audits (printed + logged every starcomb run):** the
GATE (`bg_qa` on the starless render, composition-agnostic statistical sky
scope: colour ≤ 7, gradient ≤ 8, blotch ≤ 5, rings ≤ 8 on the statistical
dark sky, terrestrial foreground excluded — **thresholds never loosen**);
whole-frame QA as a reported reference; `star_shell_report` (aura_lum WARN >
4.0 — the ghost-aura discriminant; shell_chroma is a reported TREND with no
bound, because honest PSF fringe dominates it and a fixed bound would cry
wolf on clean renders); black_point clip0 sky; the stars anchor + MTF
low-end gain (a drift watch); star metrics; and the OBJECT-INTEGRITY audit
(`object_integrity.py`, WARN-only) grading the object region the gate cannot
see — against the render's OWN same-balance, co-registered input: chroma
neutralization (absolute object chroma vs the input) and coring mottle
(mid-scale texture excess) are reliable; structure is a grain-robust
worst-region correlation that catches GROSS flattening but not a small local
hollow (that class is an upstream channel-alignment concern — see the tool).

**Per-stage visibility (standing on every build)** — every starcomb render
writes a labeled full-frame image + measured numbers for each processing
stage (background → separation → stretch → denoise → black point → stars →
combine) + an `index.html` into `<final>_stages/`, so the
treatment at each step is visible and a final-render defect localizes to
its stage from one run (`--no-stage-vis` opts out). Stretched stages are
shown as-is (display-referred); linear stages go through the shared
inspection autostretch. This is a DIAGNOSTIC surface — it runs on a side
path and never touches the float artifact chain (determinism unaffected) —
and is NOT the aesthetic-judgment surface (the full-frame lossless finals
are). The denoise stage is captured via a vis-only pre-denoise save so the
post-stretch VST shows as its own step in true chain order.

**Per-frame quality assessment (the registration inspection)** — the
standard workflow's SubframeSelector step, measurement half only, WARN-only,
on every stack path. At each runner `INS reg` call — before per-stage
cleanup prunes the sequence — `inspect_stage.py` parses the .seq regdata
siril already computed during registration (per frame: fwhm, wfwhm,
roundness, quality, background, nstars + frame→reference homography) and
persists the full per-frame records + a .seq copy. Units are derived, never
configured: FWHM in px AND arcsec (206.265·XPIXSZ/FOCALLEN from the
sequence's reference frame; missing cards → px-only, stated); background
normalized to counts16 (raw regdata units are bitdepth-dependent). The
record carries the full shift list (homography translation terms) plus a
4×4-bin sub-pixel `dither_phase_frac` (the drizzle upgrade's gating record),
and `wfwhm_excess_pct` which reads matching LOSS distinctly from seeing
(wfwhm = fwhm·(1 + 2·lost matches/ref stars), per the 1.4.4 source).
Per-frame outlier flags: robust z vs the sequence's own median/MAD,
defect-side only (fwhm+, bg+, round−, nstars−), threshold 3.5. Flags WARN
and never cull, because a flagged frame (a seeing excursion, a sky-glow
frame, a trailing spike) still stacks cleanly through rejection +
normalization. Distribution bounds are sanity envelopes; a new data class
may WARN legitimately — revisit the bound there, don't ignore it. Per-dataset
override = optional `frame_qa` block in `recipe.json` ({metric: [lo, hi]}).
Consumers: deconvolution eligibility reads `fwhm_med_px` (sampling ratio vs
the Nyquist floor) + `fwhm_cv_pct`/`round_med` (PSF stability); the
acquisition checklist reads the per-frame flags; the stack-policy `exclude`
list names frames by this stage's recorded `n`. Weighting/culling POLICY is
deliberately not part of the measurement stage — its surface is the
per-dataset `"stack"` recipe block (stack-builder paragraph), byte-inert
until a recipe opts in with a measured reason.

## Per-stage expectations (inspection contract)

Mirrored in `inspect_stage.py EXPECTATIONS` (keep in sync). WARN-only —
inspection never aborts; the hard gate stays `bg_qa.py`. Bounds are sanity
envelopes; a new data class may WARN legitimately — revisit the bound
there, don't ignore it.

| stage | PASS bound (short) |
|---|---|
| master_dark | level16 / ceiling-clip / hot-frac all INFO (offset, sensor and gain facts; prebuilt ADU-scale masters normalized /65535) |
| master_flat | corner/center 0.35–1.02; coherent dust dip ≤ 5%; clip < 0.5%; level % INFO (histogram-peak exposure fact, goal ~50%) |
| calibrated | clip < 0.5%; stars ≥ 150; bg median16 INFO (a site/sensor fact) |
| selfflat_median | star ratio ≤ 5% of calibrated; corner/center 0.35–0.75 |
| subsky_frame | G median within ±10% of calibrated (tilt is INFO — a plane fit reads a nonzero bowl on any real sky) |
| gain | monotone non-increasing (THE ring guard); corner 0.38–0.58; gray (spread 0) |
| divided | p2v(r≤0.85) ≤ 0.20; rim(r>0.9) ≤ 0.25 |
| registration | registered/total ≥ 0.9; fwhm_cv_pct ≤ 45; round_med ≥ 0.30 (a trailed-tripod PSF ≈ 0.5 must pass); bg_span_pct ≤ 130; nstars_min_frac ≥ 0.35; per-frame outliers flagged at robust z 3.5 defect-side; INFO: fwhm med px+arcsec (sampling ratio), wfwhm excess (matching loss), dither phase coverage, shift range |
| stack | dark-sky p2v ≤ 0.20 on the statistical sky (a frame-filling object doesn't read as a defect); stars ≥ 300; noise/median, median16, sky_frac all INFO |
| compose | median star-centroid offset between composed channels ≤ 1.0 px (the lines must overlay without a second interpolation pass); p95 INFO |

## Dead ends (what does not work, and the mechanism why)

Gain/flat estimation:
- A single free-form gain fit bakes sky glow into the gain (the fit peaks
  off-axis toward the glow, distorting regional brightness). Sanity-check
  any gain by its center.
- A polynomial radial V(r) oscillates (mid hump + corner upturn) and prints
  concentric RINGS after division. Only a monotone isotonic V is admissible.
- A per-channel V tints the corners, because glow contaminates the
  per-channel falloff. V must be GRAY.
- Estimating V from glow-subtracted frames without rechroma corrupts the
  pedestal/bowl ratio (siril's per-channel level restoration) → corner tint
  on division.
- A multiplicative V×S fit and an additive-glow fit bracket the truth from
  opposite sides (rim over- vs under-corrected); no a-priori model of
  siril's plane subtraction lands between them, so only the empirical V2 of
  the actual frames being divided is a flat divisor.
- Refining the gain from the STACK's residual fails: the sky's own
  structure (Milky Way / glow / clouds) exceeds the residual being measured,
  so different statistics give opposite-sign "residuals." Never scale the
  stack in place.

Background handling:
- Per-frame `seqsubsky 2` (curvature) erases the Milky Way: at wide focal
  lengths the MW band IS frame-scale curvature, so only a geometric
  (band-mask) separation could discriminate it — and every hand-rolled
  masked surface wiggles the rim worse than the AI extractor.
- Stack-level-only BGE (divide-first, no per-frame subsky) is the cleanest
  LINEAR stage, but the AI extraction's residual is STRUCTURED → the
  starless sky fails the rings gate and more MW is lost. Per-frame `subsky 1`
  stays (self-flat branch only).

Stretch/denoise/color:
- Unlinked autostretch on a CALIBRATED stack differentially amplifies
  per-channel noise = the chroma-blotch ("rainbow") engine; after SPCC there
  is no cast left for it to compensate.
- Unlinked (sky-anchored per-channel) autostretch as the narrowband-palette
  line-lift is a NO-OP: BGE+SPCC already equalize the channel SKIES and
  autostretch anchors on sky, so unlinked ≡ linked. The line imbalance is
  OBJECT flux above a common sky, which sky-anchoring cannot address.
- GraXpert AI smoothing as faint-nebulosity protection is a NON-FIX by
  design: smoothing gaussian-blurs the model OUTPUT and does not change what
  the model infers, and max smoothing still absorbs the faint nebulosity.
  Mechanism: the model infers on a small thumbnail where a frame-filling
  faint complex looks like the trained-on light-pollution class, and its
  input clip keeps low-sigma diffuse signal inside the absorbable range
  (while bright compact objects saturate out and survive). `bgelin_mode`
  plane/off is the admissible handling for object-filling fields.
- In-house NUMPY narrowband finishing (a per-line stretch + LCh
  saturation/hue/SCNR/luminance-lift set) was REMOVED — it hand-rolled
  image processing that duplicates Nightlight. Mechanism lessons that stand:
  an OBJECT-anchored per-line stretch (lifting each line's faint end to a
  display target) overruns the noise budget and RGB-space stretching
  amplifies chroma noise wholesale; hard significance gates and hard
  hue-interval edges stipple/seam. Narrowband colour+develop is Nightlight's
  job (the star-neutral O3-sphere mechanism siril has no equivalent for) —
  a linked in-house autostretch on a narrowband composite renders only the
  dominant line, which is exactly why the class routes to Nightlight.
- `rmgreen` on a sky that is not green-dominant prints a global magenta cast.
- SPCC narrowband mode is the WRONG colour step for an SHO sphere: its
  photometric star fit equalises O3=Ha (both synthesised near-identically),
  scaling O3 DOWN from its natural lead (measured raw O3/Ha ~1.5 -> ~1.0
  after SPCC), which erases the blue O3 sphere (measured sphere B/R 0.77 vs
  3.21). The mechanism the sphere needs is a STAR-COLOUR-NEUTRAL balance:
  narrowband stars carry almost no O3, so neutralising the mean star colour
  BOOSTS O3 several-fold and reveals the sphere. That is a different
  question than SPCC answers (photometric star colour vs star-neutral tint)
  — driven by Nightlight for now (ledger), a native colour tool is BACKLOG.
- Linear denoise (VST or GraXpert) at ANY placement on self-flat data
  imprints a radial signature, because the noise is radial after V(r)
  division. Only a post-stretch `-vst -mod=0.5` on the starless render is
  clean.
- Chroma blur + saturation is scale-blind to mid-scale blotches and
  saturation re-amplifies them → worse rainbow — so neither is used to fight
  chroma noise. Multi-scale Wiener significance coring once did this in
  numpy, but that was hand-rolled processing and was removed; the tool-only
  chain leaves stretch-amplified chroma noise to the tool denoise (siril VST
  / GraXpert) or accepts it (ladder the tool-denoise strength per class).
- A fixed shell_chroma WARN bound cries wolf on clean renders (honest PSF
  fringe dominates it and scales with the chain's low-end gain). aura_lum is
  the defect discriminant.
- GraXpert BGE does NOT absorb a centred galaxy's halo: removing a broad
  background gradient makes the halo measure STRONGER against a lower
  far-field sky. Background extraction is not what damages a galaxy.

Separation on resolved objects:
- mask+inpaint cannot process a RESOLVED galaxy: it keys on compactness +
  prominence with no notion of a galaxy, so it inpaints HII knots out of the
  starless and screens them back through the stars MTF as hard blobs.
  StarNet2 (`net`) keeps the field-star flux while pulling far less galaxy
  structure into the stars layer. Running the net ON an inpaint starless
  cannot recover it — that base has already lost the knots.
- StarNet2's bright-star residual is a per-DATA property, not a fixed
  defect: on a tight PSF the net starless pedestal is below the inpaint
  fill's; on a big trailed PSF the same engine prints a visible bright-star
  shell. Measure it per dataset; never carry one set's number to another.
- A mono starless must leave the separator with ONE channel. The net's graph
  takes 3, so a mono stack is replicated to feed it; returning 3 channels
  drops the render off its luminance path onto the colour chain, whose
  patch-based `denoise -vst` prints rectangular blocks across the sky. The
  linear starless was clean throughout — the artifact was the wrong render
  path, never StarNet2.

Detection/solve/registration:
- CFA-lattice (undebayered) registration as a frame-QA instrument gives
  false positives on cloud texture: cloud structure reads as detections and
  adjacent cloud frames cross-match each other, so the reference chooser can
  pick a cloud frame. Frame QA and registration run on DEBAYERED calibrated
  data only; the CFA shortcut's disk saving is not worth a poisoned
  instrument.
- Siril's internal solver fails star-matching on ultra-wide trailed fields
  even with the local Gaia catalog and correct center. astrometry.net blind
  solve from coarse PEAK centroids works in seconds; blob/PSF centroids do
  not feed the matcher.
- Position hints from human field labels can be badly wrong. Blind-solve
  first, label after.
- 1-pass sequence-start registration strands drifting tail frames; 2-pass +
  low detection sigma recovers them, and on trailed self-flat frames a
  reference sweep beats the auto-reference.
- Dropping a minority sub-focal subset to homogenize the set buys no
  matching improvement and pays the full √N noise penalty. Keep all frames.
- Per-pixel rejection + addscale do NOT absorb every cloud passage. They
  hold for transients and short tails, but a band that DWELLS over one sky
  region makes the cloud-affected values the per-pixel MAJORITY there, and
  `rej 3 3` keeps them (coherent fibrous residue, rings at the bound). Cull
  clouds by PER-PIXEL MAJORITY RISK, not by visibility: a moving minority
  band stacks clean, a dwelling one does not.
- nstars is a BLIND cloud discriminant on rich fields, because detection
  saturates at siril's star cap on every frame (nstars z ≡ 0). The
  background channel carries the cloud signal instead. Raise the cap or the
  sigma before trusting nstars flags on wide fields.
- wFWHM weighting at low FWHM spread is WORSE than no weighting: siril's
  `-weight` is a min-max ramp (worst frame → ~0 weight at any spread), so at
  low spread it drops effective frames (added sky noise + a weight×sky-drift
  pedestal) for zero crispness gain. A per-dataset tool only, on a recorded
  trigger (FWHM CV far above this regime, or cloud-class flags) — never a
  default.
- Drizzle on heavily oversampled data (short focal / large pixels) is
  pointless.
- Deconvolution (makepsf + RL) where trailing is in-exposure fails: the
  fitted PSF is ≈ symmetric and unstable on ≈0 background; no de-trailing.

Separation/stars:
- Lowering the starsep prominence to catch the faint tail is NULL — the
  residual starless detections are noise-level clumping, not separable stars.
- No official StarNet binary exists for Linux aarch64 (x64 + macOS-ARM
  only). The weights file from the official Linux x64 package runs under an
  aarch64 onnxruntime wheel — that is the `net` engine.
- The stars-layer skirt annulus is the ghost-aura engine (the MTF's large
  low-end gain on subtraction noise): fixed by stars_floor, NOT by a smaller
  dilation (the cliff just moves brighter) or feathering alone (it does not
  touch the amplified wing).

QA/scope:
- Whole-frame QA as the gate on a separated chain reads real Milky
  Way/object signal as a background artifact, and a geometric sky mask
  cannot fix it (a bright object has no fixed band to configure). The gate
  runs a composition-agnostic STATISTICAL sky scope; whole-frame stays a
  reported reference.
- Judging background by hand-picked patches misses defects a whole-scope
  measurement catches — the lesson that motivated the statistical gate.
- A level-step seam gauge across mask edges reads ≈ 0: a mask-edge seam (e.g.
  a hard region mask multiplied into any correction) is a TEXTURE
  discontinuity, so a blotch-MAD ratio is the right gauge.
- Sensor `fixbanding` is wrong here: the visible bands are MW-oriented
  chroma survivors + star fringes, not a row/col pattern (the axis-aligned
  residual is far below the band-oriented one). Don't run it.
- Hiding a rim defect with a darker sky target or a crop masks it rather
  than fixing it; the rim is in the data (estimator extrapolation × stretch
  amplification) and must be fixed there.
- JPEG q92 + 4:2:0 for finals loses star-edge chroma to subsampling and adds
  star-edge errors, so judgment panels must compare LIKE encodings.
- An offline whole-frame P2V proxy does NOT predict the rendered gate
  gradient, because the gate measures the STRETCHED sky through the adaptive
  chain (autostretch, denoise, black point). Only a gate-scope proxy (dark-
  block selection + plane fit on the LINEAR residual) tracks the render.

## Bandaid/adaptation ledger (every divergence carries its removal condition)

1. **Self-flat chain** (median → V2 → rechroma → divide) — an ADAPTATION for
   sets with no matching flat. Dies when real flats exist at the set's focal
   length (the preflight auto-routes; the matched-flat path is proven
   end-to-end).
2. **Per-frame `seqsubsky 1`** — an ADAPTATION on the self-flat branch only
   (stack-level-only BGE fails, see dead ends). Dies with real flats.
3. **mask+inpaint separation as the weights-absent fallback** — the StarNet2
   weights are an external, personally-licensed file, so the pipeline must
   render without them. The fallback cannot tell an HII knot from a star (it
   WARNs when >10% of its detections sit inside an extended-object envelope)
   and leaves the faint sub-threshold tail in the starless. Dies if a
   redistributable separation model replaces the licensed weights. This entry
   also carries a per-recipe engine pin: on an ultra-wide MW-dominated
   self-flat field the net's residual large-scale structure fails the gate,
   so that recipe pins `inpaint`; that pin dies when a separation model
   without the bright-star-shell class lands (BACKLOG).
4. **Post-stretch denoise** (`-vst -mod=0.5` on the starless render) — an
   ADAPTATION for self-flat data, where the noise is radial after V(r)
   division so every linear denoise placement imprints a radial signature
   (see dead ends). The standard linear placement (`--starless-denoise gx`)
   stays available per data class.
5. **NEF→DNG conversion for High-Efficiency frames** — the bundled LibRaw
   cannot decode Nikon HE/HE★ (TicoRAW); Adobe DNG Converter licenses that
   decode. Every other camera raw ingests directly (siril debayers it). Dies
   when acquisition records 14-bit Lossless NEF (see checklist) or a bundled
   LibRaw that lists the body.
6. **Hand-rolled numpy processing operators — RESOLVED (the render chain is
   now TOOL-ONLY).** The chain formerly ran several pixel-rewriting operators
   in numpy; all are gone (`scripts/render/operators.json` is the catalog,
   now 6 processing operators, ALL status `tool`, 0 sanctioned):
   - MIGRATED to siril: black point → `mtf b 0.5 1`; stars layer → `mtf 0 m 1`
     (python computes the anchor m, siril applies); recombine → `pm` screen;
     final saturation → `satu`. (Stretch and denoise already drove siril
     `autostretch`/`denoise -vst` / GraXpert.)
   - DELETED with the hole left, NOT refilled with numpy: the multi-scale
     Wiener significance corings (`chroma_core`/`lum_core`). No tool provides
     multi-scale significance coring, and the tool denoisers (siril VST /
     GraXpert) ARE the denoise operators — so the corings were pure
     hand-rolled processing. Removing them raises stretch-amplified sky noise
     (a broadband set measured gate rings 8.2 vs the 8.0 bound — a declared
     delta); the tool-only replacement is to ladder the tool-denoise strength
     (`starless_denoise`) per class, never reintroduce the numpy coring.
   - DELETED as a Nightlight duplicate: the in-house per-line narrowband
     stretch + LCh finish (satgamma/huerot/scnr/ppgamma) and the in-house
     `star_neutral` colour balance. Narrowband SHO colour+develop is
     Nightlight's job (entry 7), so the in-house numpy that duplicated it is
     gone; a narrowband set on the starcomb path now gets the broadband
     linked stretch (dominant line only) and says so.
   `scripts/qa/hand_roll_audit.py` keeps the catalog honest and fails on a
   NEW unregistered hand-rolled processing function.
7. **Nightlight as the narrowband SHO colour+develop tool**
   (`scripts/render/nightlight_sho.py`) — a SANCTIONED TOOL for the
   narrowband-palette class: the reference author's own open tool (staged
   aarch64 binary), driven on our per-line member stacks. It provides the
   one mechanism our chain lacks: a STAR-COLOUR-NEUTRAL colour balance.
   Narrowband stars carry almost no O3, so neutralising the mean star
   colour boosts O3 several-fold, and THAT reveals the O3 sphere; siril
   SPCC's photometric fit instead equalises O3=Ha and erases it (see dead
   ends). Nightlight then develops with ONE global stretch and NO
   star-separation / corings / denoise — the un-conservative process a
   high-SNR emission target needs, which our conservative chain crushes.
   Reproduces the author's own output bit-closely on our data. Dies when
   the star-neutral balance is integrated natively as a general colour tool
   (BACKLOG); the published GOLD palette is the author's MANUAL finish (an
   aesthetic hue choice), not part of the reproducible tool output.

## Checklist for future acquisition sessions (the real quality lever)

- Record **14-bit Lossless-compressed NEF**, NOT High-Efficiency (HE/HE★):
  HE is TicoRAW-compressed (the bundled LibRaw can't decode it → forces the
  NEF→DNG fallback) and lossy-ish; Lossless preserves faint linear signal.
  Confirm 14-bit (high-speed continuous can drop to 12-bit).
- Use the sensor's higher conversion-gain stage (a dual-gain CMOS drops
  read noise above its switch ISO) and keep subs ≤ 500/focal-mm — star
  trailing, not read noise, caps sharpness on an untracked/lightly-tracked
  rig.
- MORE integration is the real lever: when band signal/grain ≈ 1, every
  processing knob is only polishing presentation until more photons arrive.
- Flats per focal length used that night, BEFORE touching the zoom; METER
  the flat to a ~50% histogram peak rather than trusting a shutter value,
  and diffuse the light source (a bare screen shows its pixel grid).
- VERIFY the flat source is uniform: shoot a flat, rotate the camera 180°
  against the source, shoot another — the two corner/center ratios must
  match. An overly-peaked source adds falloff the lens does not have and the
  flat is unusable; the lights' own sky is the cross-check (sky corner/center
  ≈ true lens falloff).
- Darks at the lights' exposure/ISO at night temperatures; biases at the
  flats' shutter (= exact flat-darks). Missing biases degrade to the
  documented synthetic-offset fallback (fine for the flat term) — but shoot
  them anyway, it is 30 seconds.
- Lock the zoom ring (tape); don't touch the camera mid-set (a focal-length
  step mid-run forces a mixed-optics stack).
- Dither between subs; avoid the moon (star fringes on trailed PSFs are
  dispersion — physical, and saturation only multiplies them).
- Stop a fast lens down ≥1 stop for bright-star fields: wide open it adds a
  red veiling-glare halo around bright stars. It is an honest optical
  signature, not removable in processing without a bandaid.
