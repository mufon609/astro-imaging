# Wide-field untracked registration — why one homography smears the edges (deep dive)

> **Read this as the researched ROUTE MAP for the registration stage of the
> operating loop, not a fixed recipe.** Official tools do every pixel op and
> every measurement; this records what each route corrects, what it cannot, and
> which route the DATA + priorities pick. Primary sources are cited inline; each
> claim is flagged VERIFIED (survived the adversarial pass), MEASURED (on this
> repo's real frames, this rig, identical tool), or DISPUTED. Durable findings
> graduate into [`../TOOLS.md`](../TOOLS.md), [`dead-ends.md`](dead-ends.md) and
> [`../BACKLOG.md`](../BACKLOG.md).

- **Question** — Stacking a WIDE, UNTRACKED sequence with Siril's global 2-pass
  star alignment leaves the centre sharp and smears edge stars into short arcs.
  Why does one global transform fail, what transform class is actually required,
  and which route removes the edge trailing across the FULL frame while
  PRESERVING the faint cosmic dust?
- **Context** — Nikon Z6III + NIKKOR Z 24–70 mm f/4 S at 70 mm, OSC Bayer,
  6064×4040, **fixed tripod**, 373 × 6 s ISO1600 over 43 min, ~1500 px of sky
  drift, target = Milky Way + dark-nebula dust. These frames CANNOT be re-shot
  with tracking, so the fix must be a processing method.
  **Priority #1: preserve the faint cosmic dust / IFN**
  ([[preserve-cosmic-dust-is-the-priority]]).

## The theory — a homography is EXACT for this geometry

The assumed cause ("field rotation + gnomonic projection cannot be corrected by
one global transform") is **FALSE as a mechanism**, and this matters because it
points at the wrong fix.

- **VERIFIED — pure camera rotation is exactly a homography.** Szeliski,
  *Image Alignment and Stitching* §2.3 ("Rotational Panoramas"): the pure-rotation
  case "is equivalent to" all scene points lying at infinity, and the resulting
  inter-frame mapping is a plane projective transform (8 DOF). A fixed tripod
  under a rotating sky IS that case exactly: stars are at infinity, and the sky's
  rigid rotation about the celestial pole is an SO(3) map, which in homogeneous
  coordinates is linear — i.e. precisely a homography of the gnomonic plane
  (pdf: pages.cs.wisc.edu/~dyer/cs534/papers/szeliski-alignment-tutorial.pdf;
  DOI 10.1561/0600000009). **Verbatim-confirmed from the primary PDF.**
- **Consequence:** for an IDEAL rectilinear lens, field rotation and gnomonic
  projection produce ZERO residual under a homography. Neither is the defect.
- **VERIFIED — what actually remains.** Szeliski enumerates the residual sources
  that survive an *optimal* global rotational/homography registration:
  **(1) unmodelled radial distortion**, (2) small translations/parallax,
  (3) scene motion, (4) exposure differences. For a star field, (2)–(4) are nil.
  **Radial lens distortion is the mechanism**, and it displaces stars by an amount
  proportional to their radial distance from the optical axis — which is exactly
  the centre-sharp / edge-smeared signature observed.
- **The composition, stated precisely:** with a real lens the inter-frame map is
  `distort ∘ H ∘ distort⁻¹`, which is NOT a homography. As a star drifts 1500 px
  it samples a different local distortion, and no 8-DOF global fit can absorb the
  difference. (Kukelova et al., CVPR 2015, "Radial Distortion Homography" treats
  this exact composite as its problem statement.)
- **VERIFIED — the lens is far from ideal.** The NIKKOR Z 24–70 mm f/4 S measures
  ~3.4% pincushion at 70 mm uncorrected (opticallimits.com review). At the frame
  corner (r ≈ 3643 px) that is ~120 px of displacement from the ideal gnomonic
  position — two orders of magnitude above the ~1 px registration accuracy a
  stack needs.

**So the required transform class is: undistort → homography.** Not a local or
elastic warp — the global projective part is already exactly right. Only the
lens model is missing.

## The residual budget (MEASURED on these frames)

Every number below comes from a tool: astrometry.net (solve), Siril `findstar`
(PSF fits), exiftool (NEF metadata).

| term | magnitude | fixable by registration? |
|---|---|---|
| **Radial lens distortion** | ~3.4% → ~120 px at the corner; leaves ~8.6 px of smear at the crop edge after the best-fit homography | **YES — with a distortion model** |
| **In-exposure trailing** | **3.40 px predicted / ~3.6 px measured** | **NO — baked into each 6 s frame** |
| **Differential refraction** | ~1–4 px across 28.6°, asymmetric with hour angle | partly (per-frame model only) |

- **MEASURED — the field.** astrometry.net blind solve: **RA 306.047°, Dec
  +47.043°** (Cygnus), 18.02 arcsec/px → effective focal ~67.8 mm (nominal 70).
- **MEASURED — the tripod never moved, and the sky behaved exactly as theory
  says.** Two independent solves 43 min apart give Dec **+47.043° → +47.045°**
  (constant to 7 arcsec) while RA advances **10.816°** in 2597 s = 14.99°/hr vs
  the sidereal 15.041°/hr (**0.3%**). A direction fixed in the rotating Earth
  frame traces a rotation about the polar axis, which preserves declination and
  advances RA at exactly the sidereal rate. Confirmed to 0.3%.
- **MEASURED — the in-exposure trailing FLOOR.** 15″/s × cos(47.04°) × 6 s ÷
  18.02″/px = **3.40 px**. Independently, Siril's per-frame `findstar` fits over
  all 373 frames give roundness (FWHMy/FWHMx) **0.615 median, uniform across the
  set** (min 0.589, max 0.675) at FWHM 3.634 px — implying ≈3.6 px of trail.
  Physics, the astrometric solve and the tool's PSF fits agree within 6%.
  **No registration method can remove this**: it is within-exposure. Stars in this
  data are elongated ~1.6:1 at BEST. The goal is to make the EDGE as good as the
  CENTRE — not to make stars round.
- **MEASURED — the defect is registration-induced, not a frame property.**
  Per-frame roundness is *uniform across the set*; the radius-dependent smear
  appears only after register+stack.

## The defect, quantified (Siril `seqtilt`)

The measurement that separates "the registration model is wrong" (shape degrades
with radius) from "the frames are soft" (shape flat vs radius) is **Siril's own**,
headless: `seqtilt` fits the PSF across the frame and reports

- **Off-axis aberration[FWHM]** — centre vs corners = the **radial** term, i.e.
  exactly the defect this deep dive is about;
- **Sensor tilt[FWHM]** — best vs worst corner = the **asymmetric** term;
- **Truncated mean[FWHM]** — whole-frame FWHM, outlier-truncated;
- **Stars** — how many it fitted.

Both terms are FWHM differences in px (bigger = worse). Driven + recorded by
`scripts/qa/star_shape.py`; record: `qa_work/registration_qa.json`
→ `spatial_star_shape`. `tilt` and `inspector` are GUI-only (*"Can be used in a
script: NO"*); `seqtilt` is the only headless door.

| 54-frame production A/B | stars | truncated mean FWHM | **off-axis aberration** | sensor tilt |
|---|---|---|---|---|
| **OFF** — no distortion model | 5,095 | 3.20 px | **0.57 px** | 0.50 (16%) |
| **ON** — lensfun | 10,707 | 3.28 px | **0.31 px** | 0.42 (13%) |
| **shipped** — lensfun, 168 fr | 11,805 | 3.27 px | **0.25 px** | 0.51 (16%) |

- **The radial term is the defect, and it is removed** — off-axis aberration
  0.57 → 0.31, and **0.25 at full 168-frame depth** (the deepest render is the
  most uniform, not the least).
- **The one-sided component is MEASURED, not unresolved** — sensor tilt
  0.50 (16%) → 0.42 (13%) → 0.51 (16%). A radial lens model cannot correct a
  one-sided term, and does not: it survives the correction essentially untouched.
  Candidates remain differential refraction (asymmetric with hour angle) and lens
  decentering; distinguishing them is open, but the term itself is now a number
  the tool prints rather than an inference.
- **Sharpness is NULL** — truncated mean FWHM 3.20 → 3.28 → 3.27. The correction
  buys star COUNT and radial UNIFORMITY, never sharpness; the in-exposure trailing
  floor is untouched, exactly as predicted.

> **Do not re-derive this by binning a `findstar` list by radius.** That was tried
> and it is circular — the binning origin gets inferred from the detections, the
> defect suppresses edge detections, so the origin moves *with* the defect and the
> profile flattens as the defect worsens. Measured: the origin shifted 537 px on one
> stack purely by tightening the detection sigma, and the profile then showed no
> defect on a frame whose right third has no detectable stars. It also invented a
> phantom "the correction degrades the centre" anomaly that reverses at a sane
> threshold. `seqtilt` has no origin to get wrong. Mechanism: `dead-ends.md`,
> "Three traps that make a registration comparison lie" (trap 3).

## The centre band the correction introduces (and the measure that sees it)

`seqtilt`'s off-axis aberration is centre-vs-corners: a defect CONFINED TO A BAND
along the drift axis makes that number BETTER as the centre degrades toward the
corners' mean. Measured with fixed 350 px equal-area stations about the geometric
centre (`scripts/qa/star_stations.py`; drift axis 174.4° in image coordinates from
the frame-1/373 solves; records `qa_work/star_stations_*.json`) — cells are
[n, majFWHM px, roundness]:

| stack | centre | along +1300 | perp −1300 |
|---|---|---|---|
| shipped 168 fr lensfun | 927, **5.30**, 0.480 | 954, 4.32, 0.574 | 798, **3.60**, 0.706 |
| production 54 fr ON | 837, **5.73**, 0.437 | 914, 4.22, 0.585 | 628, 3.62, 0.679 |
| production 54 fr OFF (control) | 864, **4.03**, 0.556 | 748, **4.83**, 0.485 | 234, 3.95, 0.594 |

- **The inversion is the finding.** The control's centre is its BEST region (true
  distortion → 0 at the axis) and its defect grows OUTWARD along the drift; the
  corrected arms fix mid/edge and INTRODUCE a centre band — worst at the very
  centre, absent perpendicular to the drift (3.5–3.6 px = the in-exposure floor).
  Confirmed by the user's eyes on the shipped full-frame final ("under Deneb" —
  Deneb sits ~320 px above the band core).
- **Mechanism.** The community profile carries a small paraxial error ε(r). A star
  whose sky position CROSSES the optical axis during the ~1500 px drift has its
  radial unit vector flip sign, so ±ε becomes a ~2ε along-drift smear confined to
  the corridor the axis swept. Mid-field never crosses the axis; its near-constant
  residual is absorbed by the per-frame homography. A tracked rig can never see
  this term, which is why no mainstream reference reports a "field-centre" residual.
- **Brightness split.** At detection sigma=3.0 the corrected centre reads 3.89 px —
  bright cores survive; the faint population smears toward/below detection. The
  band is a faint-star/texture defect: the dust-gate pass and the band coexist on
  the same final, and bright-star medians (including the earlier sigma-3.0
  "reversal", which also compared against a shifted-origin control profile —
  `dead-ends.md` trap 3, refined) hide it.
- **KILLED — the focal key.** EXIF 67.8 (the solved effective focal) as the lensfun
  interpolation key is WORSE at the centre (5.42/0.468 vs control 4.88/0.516 on the
  12-frame instrument; `experiments.jsonl` paraxial_focal_key): the calibrated
  focal=70 entry is the best available community key.
- **The fix — ADOPTED (`experiments.jsonl` paraxial_model_source):** a model
  fitted from THIS unit's own frames by between-frame star-correspondence fitting
  (`scripts/darktable/fit_lens_model.sh` — Hugin `cpfind`+`cpclean`+staged
  `autooptimiser`, hfov pinned at the solved value), installed into the live
  lensfun DB (`scripts/darktable/install_lens_model.sh`) so the chain itself is
  unchanged. The fitted curve agrees with the community entry at the crop corner
  (Δ 0.06 px) and diverges from it by 2.4–3.9 px through the paraxial/mid field —
  the ε(r) the fit implies (model-vs-model; backed by the A/B confirming the
  fit's predictions). Full-depth A/B vs the community entry: centre station
  **5.30 → 3.67 px** (roundness 0.480 → 0.629), all-station spread 1.70 →
  **0.52 px**, seqtilt truncated-mean FWHM **3.27 → 3.06 px**, stars +10%,
  sensor tilt 0.51 → 0.31 px. Approved on the user's eyes, full-frame lossless.

## The experiment — one knob, on the real frames

54 lights = every 7th of 373, spanning the FULL 43-min window (the residual
scales with the TIME SPAN, not frame count, so subsampling cadence reproduces the
geometry at a fraction of the disk). Calibrated with the validated master dark +
sky flat, **debayered before registration**, `-framing=min`, identical stack
parameters. The only knob is `-disto=`.
Record: `datasets/july14/set-01/qa_work/registration_qa.json`.

| | stars | roundness | majFWHM | radial (centre → edge) |
|---|---|---|---|---|
| **A** homography (control) | 17,770 | 0.528 | **4.74 px** | 4.33 → 6.46 |
| **B** + SIP undistort (`-disto=`) | **7,561** | 0.569 | **6.02 px** | 7.92 → 4.61 (**inverted**) |
| **C** homography, 9-min window | **26,354** | **0.600** | **3.87 px** | 3.52 → 6.41 |

- **B is a LOSS (killed hypothesis).** `-disto=` did not remove the defect; it
  relocated and worsened it, smearing the whole frame (see
  `qa_work/reg/star_shapes_AB.png`) and halving detected stars.
- **MEASUREMENT TRAP, recorded so it is not repeated:** B's radial profile claims
  the *edge* improved (4.61 vs A's 6.46). That is **survivorship bias** — B's
  smearing pushed most stars below the detection threshold, so the median is over
  the lucky survivors. The honest signal is the star count **per unit area** (A and
  B are near-identical in size: 1259 vs 541 stars/Mpx, −57%), and the full-frame
  crops settle it. Any star-shape metric must be read with its n — and any n must be
  read per unit area, since `-framing=min` gives each variant a different frame size.
- **C CONFIRMS THE MECHANISM.** A 9-min window (~310 px drift) is better at
  **every** radius, and its inner field (r < 1700) sits **exactly at the
  single-frame floor** (roundness 0.619–0.634 vs the 0.615 floor; majFWHM 3.52 vs
  the 3.63 per-frame FWHM) — registration adds *nothing* there.
  **Remove the drift and the homography becomes exact** — the theory, proved on
  this data. The crops (`qa_work/reg/star_shapes_AC.png`, matched field radii) show
  C with clean point stars at LEFT, CENTRE **and RIGHT**, where A's right edge is
  destroyed. The cost is depth: 12 frames vs 54.
  (**Do NOT read C's higher raw star count as evidence** — C's frame is 56% larger,
  so per unit area it is 1195 stars/Mpx vs A's 1259, i.e. slightly FEWER, exactly as
  4.5× less integration predicts. Compare star counts per area or not at all.)
- **C also keeps MORE FIELD** — 5654×3899 (22.0 Mpx) vs A's 4169×3385 (14.1 Mpx),
  **+56% area**: less drift means `-framing=min` intersects away less of the frame.
  So the short window trades integration time for BOTH edge sharpness and field
  coverage, which makes the depth-vs-edge call less one-sided than it first looks.

## Why B failed — the distortion model, not the mechanism

The mechanism works; the model is the broken link. Both halves were probed
on-rig, on Siril 1.4.4 (the identical tool the x86 target runs).

- **MEASURED — the mechanism is sound.** `register seq -2pass -disto=file <path>`
  → *"Distortion data is valid and will be used"*; `seqapplyreg` then reports
  *"Distortion data was found in the sequence file, undistortion will be
  applied"* — so `-2pass` + `seqapplyreg` DOES carry the undistortion through to
  export even though `-disto=` is absent from `seqapplyreg`'s own help. Syntax is
  **`-disto=file <path>` (two tokens)**; `-disto=file=<path>` errors;
  `-disto=image` requires the loaded image to be solved. Siril also **reads an
  astrometry.net-injected TAN-SIP header it did not write** (*"Image is already
  plate solved"*).
- **MEASURED — the SIP is not a lens model.** The camera is on a fixed tripod, so
  the lens distortion is physically IDENTICAL in every frame. Two independent
  astrometry.net solves 43 min apart disagree by a **median of 65.3 px (worst
  127.9 px)** at the same sensor positions. A real lens model must agree to ~1 px.
  With `--max-stars=1500` the disagreement only falls to **43.8 px (worst 132.1)**
  — while the LINEAR solve improves sharply (scale 18.02/18.20 → 18.05/18.06;
  RA-drift error 6% → 0.3%; logodds 127 → 782). **More stars fix the position, not
  the distortion.**
- **Mechanism of that failure:** astrometry.net's SIP tweak is constrained by
  *matched index* stars, and the 4200-series index at the wide scales this field
  needs (12–19) is Tycho-2-based and sparse — supplying more *field* stars cannot
  help when few index stars exist to match. Hence some positions agree (bottom
  3.8 px, BL 15.0 px) while others are wild (TR 132.1 px).
- **This blocks the WCS-reprojection route too**, which needs the same
  trustworthy per-frame distortion solution.

## Siril's own solver cannot supply the model either

- **MEASURED — reproduces and REFINES the dead-end.** With the correct centre from
  the blind solve, the local Gaia catalogue and `-nocrop`, Siril's internal solver
  reports *"Initial solve failed"* → near-solve failed, at a computed FOV of
  36.45° (diagonal). Two candidate causes were tested and **eliminated**:
  - relaxed detection (`setfindstar -relax=on -roundness=0.05 -sigma=0.5`) raised
    candidates 3316 → 8694 — still failed;
  - catalogue depth (`-limitmag=+4`) raised the fetch from **2177 → 138,498** Gaia
    stars (limit mag 7.81 → 11.81) — still failed.
  So the blocker is Siril's **star MATCHER at ultra-wide FOV**, not the roundness
  gate and not the auto limit magnitude. (The auto limit magnitude of 7.81 for a
  36° field is nonetheless a real mismatch worth knowing: detection goes far
  deeper than the catalogue it is matched against.)

## The model EXISTS in the data — the gap is a tool that applies it

- **MEASURED (on-rig probe, exiftool) — the NEF carries the lens model.**
  `DistortionCorrection: On (Required)`, `DistortionCorrectionVersion: 0100`,
  `RadialDistortionCoefficient1/2/3 = 0.01821 / -0.01132 / 0.05939`, plus a
  VignetteInfo block. "On (Required)" means the raw is UNCORRECTED and the profile
  is meant to be applied downstream.
- **DISPUTED / SUPERSEDED:** the research found sources stating the Nikon Z
  correction block was *not decoded* by open source and that exiv2 cannot reach it
  (discuss.pixls.us "Reverse engineering Nikon Z series lens correction", 2023).
  **The on-rig probe contradicts this for the radial terms**: exiftool decodes them
  today (see exiftool's `Nikon.pm`). What remains undocumented is the exact model
  form / normalisation, and — decisively — **no headless Linux tool APPLIES the
  profile**. This is the same doc-vs-binary pattern the flats work hit: the
  empirical probe wins.
- **The precise gap:** a trustworthy distortion model is present in every frame;
  what is missing is an official tool that applies it (or emits it as a Siril
  distortion master). That single missing link is what stands between this data
  and the proven `-disto=` mechanism.

## Routes audited

**Distortion-aware / local registration**
- **Siril 1.4.4 `register -disto=`** — FREE / siril-native / headless. The only
  native distortion route. `-transf=` offers ONLY shift | similarity | affine |
  homography — **no local, elastic, piecewise or thin-plate-spline option**
  (VERIFIED, siril.readthedocs.io Commands + on-rig help). Producer side:
  `platesolve`/`seqplatesolve -order=1..5` (SIP) and `-disto=<file>` to save a
  distortion master. Mechanism proven here; blocked only by the model source.
- **Siril multi-point registration** — **NOT a route.** 1.5-dev only (absent from
  1.4.4), scoped to planetary/lunar atmospheric seeing, and the model is
  **piecewise TRANSLATION only** (any affine/homographic component is explicitly
  discarded) — not a distortion-aware warp
  (siril.readthedocs.io/en/latest/preprocessing/multipoint.html).
- **PixInsight StarAlignment thin-plate-spline distortion correction +
  DynamicAlignment** — PAID / GUI. The reference implementation of a true local
  distortion model (pixinsight.com/tutorials/sa-distortion/). **x86/GUI-deferred,
  audit-only.**
- **Astro Pixel Processor distortion-model registration** — PAID / GUI. A
  practitioner A/B on the same data class (250 × 5 s, Canon R5 + Sigma 40 mm at
  f/1.6) reports Siril's global star registration smears corner stars into short
  trails while APP's distortion-model registration does not
  (discuss.pixls.us/t/siril-needs-distortion-correction-in-stacking/20991).
  **x86/GUI-deferred, audit-only.**
- **Siril developers' own position** — distortion correction in registration was a
  known, unscheduled limitation (Hourdin 2020-10-26; Richard 2023-02-05), with the
  stated reason that "lenses can be characterised easily but telescopes cannot".
  That dates those sources to the pre-1.4 era: 1.4 shipped `-disto=`. Their reason
  implies the sanctioned fix is to derive distortion **from the data per frame**
  (SIP at plate-solve) — exactly the route tested here.

**WCS reprojection (survey-grade, headless)**
- Aligning by TRUE sky coordinates *would* remove rotation AND distortion — but
  only to the accuracy of the per-frame WCS, so it **inherits the same SIP blocker
  measured above**. Not a way around the model gap.
- **astropy `reproject`** — `reproject_interp` is **NOT flux-conserving** and all
  routines assume surface-brightness units; `reproject_adaptive` has an explicit
  `conserve_flux` flag and is documented as more accurate exactly under **strong
  distortion / large sky areas**; `reproject_exact` is an exact drizzle valid at
  any FOV but slow. `reproject_interp` offers no Lanczos kernel (nearest /
  bilinear / biquadratic / bicubic only) — the LANCZOS3 choice is a SWarp option,
  not a reproject one. `find_optimal_celestial_wcs` defaults to TAN but the
  projection is user-settable. `reproject_and_coadd`'s `match_background` models
  only a single CONSTANT ADDITIVE offset per image and forfeits the absolute
  photometric zero point (reproject.readthedocs.io celestial/mosaicking).
  **astropy is x86-gated** (absent on the arm base rig).
- **SWarp** — **`SUBTRACT_BACK = Y` by DEFAULT**: it subtracts a sky background
  model from every input. For a frame-filling faint IFN target this is the single
  most dangerous default in the route and **must be turned off**
  ([[preserve-cosmic-dust-is-the-priority]]). `PROJECTION_TYPE` accepts any WCS
  code (TAN is merely the shipped value); `RESAMPLING_TYPE` ∈ {NEAREST, BILINEAR,
  LANCZOS2/3/4}; `FSCALASTRO_TYPE` has only NONE|FIXED, so SWarp conserves flux
  only with equal-area output projections. **VERIFIED — the projection question is
  real at this FOV:** SWarp's author sets an explicit threshold — fields under
  ~10° may safely use TAN; beyond that TAN's radial stretch is a problem. This
  field is ~30°, so a TAN output grid is NOT automatically right; equal-area
  projections (ZEA/AIT/…) conserve surface brightness and are preferred for large
  areas.

**Untracked-nightscape specialists**
- **VERIFIED — Sequator's manual names our exact symptom**: distortion produces
  "false trails" that are worst at image corners, and the remedy is a distortion
  model. Its author's own residual budget is projection effects, in-camera/embedded
  lens optical correction, and atmospheric refraction — the same list derived above.
  Its "Lens" vs "Complex" models are gated on FIELD WIDTH, not tracking mode
  (sites.google.com/view/sequator/manual).
- **VERIFIED — first-party envelope:** Sequator's author reports acceptable
  distortion correction only up to roughly a **5-minute total drift window at
  20 mm-equivalent**. Our window is 43 minutes — 8× that. Independent confirmation
  that the non-homographic residual grows with drift, matching experiment C.
- **DISPUTED → REFUTED:** the premise that Sequator "segments the sky into regions
  and locally aligns them" is **not supported** by its manual, which documents no
  segmented/piecewise/local alignment; its "Sky region" option is a foreground/sky
  selector. Do not carry that claim.
- Sequator (Windows) and Starry Landscape Stacker (macOS) are GUI-only — **no
  headless Linux path**, so the METHOD, not the tool, is what transfers.

**Mitigations**
- **Short-time-window stacking — MEASURED, works, with a real cost.** Experiment C
  above. The catch: **combining the sub-stacks reintroduces the identical model
  error** (mapping block k to block 1 spans the same drift), and turns a smooth
  smear into a few discrete ghosts. So short windows buy edge sharpness by paying
  integration time; they are not a way to keep both.
- **Drizzle does NOT fix alignment-model error** — it is a sampling method, needs
  real sub-pixel dither, and cannot de-trail ([[plate-solving-and-drizzle]]).
- **VERIFIED — the OSC order, and its one exception.** Debayer BEFORE registration:
  interpolating an undebayered CFA mosaic through a geometric transform mixes
  neighbouring R/G/B photosites. Siril forces the choice explicitly — **drizzle
  requires NON-debayered (CFA) input, while debayered RGB sequences can only use
  interpolation** — so **CFA-drizzle is the documented exception** to the rule
  (siril.readthedocs.io registration; on-rig `register` help). The existing 124-frame
  baseline registered CFA data with lanczos4, which is why its previews carry no
  real colour; variant A here debayers first and measures better (majFWHM 5.25 →
  4.74 px, though frame count and CFA sampling confound a strict comparison —
  **suggestive, not proven**).

## The fix — an OFFICIAL MEASURED distortion model (WIN, on the real frames)

The SIP route failed because it *fitted* distortion per-frame from sparse trailed
stars. The answer is a model that was **measured for the lens** and so cannot suffer
index sparsity at all: **lensfun**, applied by **darktable** (built against Lensfun
0.3.4). darktable does every pixel op; lensfun owns the model AND its normalisation
(which is undocumented — the header, the Debian doc package and both upstream manual
pages all omit it, so hand-implementing it would risk a silent factor-of-two error).

- **VERIFIED — the profile exists and is focal-matched**: `<distortion model="ptlens"
  focal="70" a="0.012" b="-0.017" c="0.039"/>` for the *Nikkor Z 24-70mm f/4 S* —
  70 mm is a calibrated entry, not interpolated.
- **MEASURED — the DB gap that must be closed first**: Debian's lensfun 0.3.4 database
  does **not** contain the Z6III. It has `Nikon Z 6` / `Nikon Z 6_2`; the EXIF says
  `NIKON Z6_3` (a 2024 body). Without a camera match lensfun cannot build a modifier —
  the body supplies the CROP FACTOR, the lens supplies the distortion.
  **`lensfun-update-data`** installs the upstream DB to
  `~/.local/share/lensfun/updates/version_1`, which HAS `Nikon Z6_3`. darktable then
  auto-matched: camera `Nikon Z6_3`, lens `Nikkor Z 24-70mm f/4 S`, focal 70.0,
  aperture 4.0, crop 1.0, autoscale 1.046.
- **The experiment — one knob.** 54 lights, FULL 43-min window; the only difference is
  the darktable lens module's *enabled bit* (matched styles, both `--style-overwrite`,
  identical module sets). The numbers that settle it are the **production** A/B in
  "The defect, quantified" above: it runs on properly calibrated frames
  (`modify_flags=1`, distortion only) and is measured with Siril's own `seqtilt`.
- **WIN, on the tool's own measure:** off-axis aberration **0.57 → 0.31 px**, star
  count **5,095 → 10,707**, and **54/54** frames register vs 52/54. Crops:
  `qa_work/reg/star_shapes_lensfun.png` — the control's edge is washed into diagonal
  streaks; the corrected edge is a dense field of point stars.
- **MECHANISM CONFIRMED, not just the outcome:** the correction improves the field
  **centre** too, where distortion is ≈0. That is exactly the prediction — undistort
  the frames and ONE global homography fits *every* star, instead of being a
  compromise that degrades everywhere. It also explains why two frames that could not
  match now register.
- **What it does NOT buy:** sharpness (truncated mean FWHM 3.20 → 3.28 — NULL) and the
  one-sided term (sensor tilt 0.50 → 0.42, and 0.51 at full depth — uncorrected). Claim
  neither.
- **Confound retired:** the first arm ran `modify_flags=7` (distortion|TCA|vignetting).
  The production A/B re-ran distortion-only (`modify_flags=1`) — vignetting correction
  would fight the sky flat — and the gain got LARGER, so the confound did not drive it.
- **The raw arm was a GEOMETRY test, not a render:** darktable working from raw carries
  no darks/flats, so that arm's absolute numbers are not comparable with anything else
  (darktable also applies the EXIF orientation to raw but not to Siril's TIFF, so its
  stacks are portrait where the production stacks are landscape). Superseded by the
  production A/B, which calibrates in sensor space first.

## The july14 decision (the loop's RECOMMEND → REPORT → the user decides)

- **Chosen, executed and SHIPPED:** the **lensfun distortion route with the model
  FITTED FROM THE SET'S OWN FRAMES** — the community DB entry removes the radial
  edge degradation but writes the paraxial centre band (section above), so the
  fitted entry replaces it at this focal. The chain is "The production chain"
  below, scripted as `scripts/stack/run_undistort_pipeline.sh`. Approved on the
  user's eyes at full depth: dust preserved, centre at the floor, edges held.
- **Superseded:** route A (full depth, measured edge defect) and route C (short
  window, floor-limited, 1/4 depth, +56% field). The depth-vs-edge trade-off is no
  longer forced. Keep C as the fallback if the route ever fails on a set.
- **Not proposed:** cropping to the good field — that hides a defect that is in the data.
- **The honest floor, restated:** ~3.4–3.6 px of in-exposure trailing is in every frame
  and **no method removes it**. Success is the edge matching the centre — which the
  lensfun route now achieves.
- **Trade-off recorded:** the fix depends on a COMMUNITY-measured lens profile (not
  Nikon's own coefficients, which ship in every NEF but sit in a private block no
  headless tool applies) and on a lensfun DB update the distro does not provide.
  Both are cheap and reproducible; neither is under our control.

## The production chain (what actually ran, and the traps in it)

Every pixel operation is a tool's. The order is forced by one constraint: **darks and
flats are sensor-grid properties, so calibration must finish in SENSOR space before any
geometric warp**, and a CFA mosaic cannot be interpolated — hence debayer sits between.

```
Siril calibrate (CFA, master dark + validated sky flat, -equalize_cfa -debayer)
  → Siril savetif                       (16-bit TIFF, linear)
  → exiftool -TagsFromFile              (Make/Model/LensModel/FocalLength — savetif
                                         carries none, and darktable needs them to
                                         match the lensfun profile)
  → darktable-cli --style lensdist --style-overwrite --icc-type SRGB
  → Siril register -2pass → seqapplyreg -framing=min → stack rej 3 3 -norm=addscale
```

Scripted as **`scripts/stack/run_undistort_pipeline.sh`** — it runs
`lens_preflight.py --require-profile` first (darktable silently applies NO
correction to a lens lensfun cannot match), refuses a frame count whose final
chunk would be a single frame (Siril cannot sequence one frame), and checks the
~231 MB/frame uncompressed disk peak before any work. The model the warp applies
is the lensfun DB entry for the EXIF-matched lens; for this rig's 24-70/4 S at
70 mm that is the entry **fitted from the set's own frames**
(`scripts/darktable/fit_lens_model.sh`, installed by `install_lens_model.sh`) —
the community entry's paraxial error is the centre-band mechanism above.

- **The style is a pinned artifact, not a GUI step.** `scripts/darktable/lensdist.dtstyle`
  (+ `nodist.dtstyle`, the disabled-bit control) with `scripts/darktable/install_styles.sh`
  to install them headlessly into a darktable config. Verified: installed into a fresh
  config, the warp reproduces to **0.000 px at every radius**. It carries
  `modify_flags=1` (distortion only — vignetting correction would fight the sky flat;
  TCA is unwanted).
- **The style carries ONLY `modify_flags` — everything else in the blob is inert.**
  MEASURED, one knob each, ~400 matched stars per arm:

  | baked field | honoured? | proof |
  |---|---|---|
  | `focal=70.0` | **no** — re-detected from EXIF | EXIF 70 vs 24 → opposite-sign warps (+26→+69 px vs −6→−19 px): pincushion at the long end, barrel at the wide |
  | `scale=1.046028` | **no** — recomputed | scale 1.046 vs 0 vs **1.5** → identical to **0.000 px** |
  | `camera`, `lens` | **no** — re-detected from EXIF | EXIF lens → a 50 mm prime at the same focal gets that prime's own, much weaker profile |
  | `modify_flags=1` | **YES** | this is the only field that carries |

  So **one style is camera-, lens- and focal-general** — no per-focal style is needed, and
  the feared "a 24 mm frame silently gets a 70 mm correction" cannot happen.
- **THE TRAP, and it is the same mechanism: darktable never fails.** Because nothing is
  baked, a lens the DB cannot match gets **NO correction, silently** — an unrecognised
  `LensModel` measured max |dr| = **0.000 px over 413 stars**, exit 0, **no warning in the
  log**. A wrong-but-present lens is worse: a wrong, weaker model, equally silent. The
  route therefore **cannot rely on the tool to degrade loudly** — the chain must assert
  EXIF camera+lens+focal against the DB and against the set's `acquisition.json` BEFORE
  the run, per set, and STOP on a miss. "Did the warp happen?" is not sufficient: it
  passes the wrong-lens case. This is also why a mixed-focal or mixed-lens set is a hard
  stop, not an interpolation — each frame silently gets its own EXIF's model. The DB gap
  is real and ordinary: Debian's lensfun 0.3.4 lacks the Z6III; `lensfun-update-data`
  supplies it.
- **`--icc-type SRGB`, never `LIN_REC709`** — the round-trip linearity trap; mechanism
  and numbers in [`dead-ends.md`](dead-ends.md).
- **darktable is deterministic; its container is not.** Same input + style twice differs
  by exactly **one byte** (a metadata timestamp), while the measured warp reproduces
  exactly. Never gate this route on a file hash — compare pixels or the warp.

## What graduates

- **[`../TOOLS.md`](../TOOLS.md):** Tier 2b — **darktable-cli + lensfun** as the working
  distortion route for this class, its pinned style + the focal re-detection that makes
  it focal-general, `--icc-type SRGB` (match the tag), and `modify_flags=1`. Tier 2 —
  Siril `seqtilt` as the headless spatial star-shape measure (off-axis aberration /
  sensor tilt), and `tilt`/`inspector` as GUI-only. Siril 1.4.4 `register -disto=`
  (`image|file <path>|master`) as the ONLY native distortion route, its proven
  syntax, and that `seqapplyreg` carries it; `-transf=` is global-only (no
  local/TPS); Siril's matcher fails ~36° fields with magnitude/roundness
  eliminated; Siril reads an astrometry.net-injected TAN-SIP.
- **[`dead-ends.md`](dead-ends.md):** field rotation + gnomonic projection are NOT
  the cause (a homography is exact for pure rotation — Szeliski); radial lens
  distortion is; astrometry.net SIP at wide index scales is not a reproducible
  lens model (65 px / 44 px disagreement) and more field stars do not fix it;
  the survivorship-bias trap in star-shape medians; in-exposure trailing is the
  unremovable floor.
- **[`../BACKLOG.md`](../BACKLOG.md):** the ranked routes to a trustworthy
  distortion model (x86/GUI-deferred).

## Sources

Primary (tool / vendor docs):
- https://siril.readthedocs.io/en/stable/preprocessing/registration.html
- https://siril.readthedocs.io/en/stable/astrometry/platesolving.html
- https://siril.readthedocs.io/en/stable/Commands.html
- https://siril.readthedocs.io/en/latest/preprocessing/multipoint.html
- https://siril.org/download/2025-12-05-siril-1-4-0/
- https://www.pixinsight.com/tutorials/sa-distortion/index.html
- https://reproject.readthedocs.io/en/stable/celestial.html
- https://reproject.readthedocs.io/en/stable/mosaicking.html
- https://star.herts.ac.uk/~pwl/Lucas/rho_oph/swarp.pdf
- https://sites.google.com/view/sequator/manual
- https://sites.google.com/site/starrylandscapestacker/new-in-version-1-7
- https://github.com/exiftool/exiftool/blob/master/lib/Image/ExifTool/Nikon.pm

Theory / literature:
- https://pages.cs.wisc.edu/~dyer/cs534/papers/szeliski-alignment-tutorial.pdf
  (Szeliski, *Image Alignment and Stitching*, DOI 10.1561/0600000009 — pure
  rotation ⇒ homography; the post-registration residual list)
- https://openaccess.thecvf.com/content_cvpr_2015/papers/Kukelova_Radial_Distortion_Homography_2015_CVPR_paper.pdf
- https://arxiv.org/pdf/1005.4454 (Lang et al., astrometry.net)
- https://www.aanda.org/articles/aa/full_html/2014/06/aa23459-14/aa23459-14.html
  (differential atmospheric refraction scaling)
- https://ui.adsabs.harvard.edu/abs/1998PASP..110..738G/abstract

Practitioner / forum / reference:
- https://discuss.pixls.us/t/siril-needs-distortion-correction-in-stacking/20991
- https://discuss.pixls.us/t/reverse-engineering-nikon-z-series-lens-correction/36733
- https://opticallimits.com/nikon/nikon-z/nikkor-z-24-70mm-f-4-s-review/
- https://www.celestron.com/blogs/knowledgebase/what-is-field-rotation-how-does-it-affect-my-scope-s-viewing-and-imaging

## Status

**SOLVED AND SHIPPED on the real july14 set-01 frames — edges by the measured
lens profile, the centre band by fitting the model from the set's own frames.**
Three model sources were measured against the same one-knob harness: an
astrometry.net SIP fed to `register -disto=` — **killed (a LOSS)**; the community
lensfun entry — **WIN at mid/edge**, but its paraxial error writes the centre
band; the entry **fitted from this unit's frames** — the adopted route (centre at
the in-exposure floor, whole frame sharper, approved on the user's eyes). Root
cause established from theory (Szeliski) and from the tools' own measurements.

On Siril `seqtilt`, control → corrected → shipped 168-frame render: **off-axis
aberration 0.57 → 0.31 → 0.25 px**, stars 5,095 → 10,707 → 11,805, 54/54 registered.
Sharpness is **NULL** (truncated mean FWHM 3.20 → 3.28 → 3.27) and the **one-sided
term is uncorrected** (sensor tilt 0.50 → 0.42 → 0.51) — a radial model cannot fix it.
The chain is productionised ("The production chain"), the style is pinned and its
warp verified reproducible to 0.000 px, the route is measured focal-general, and the
dust-preservation gate PASSED on the user's eyes on a full-frame lossless final.

**Open, and specific:**
- **Which mechanism drives the residual one-sided term** — the fitted model
  reduced sensor tilt 0.51 → 0.31 px (part of it was model error); the remainder's
  candidates stay differential refraction (asymmetric with hour angle) vs lens
  decentering, discriminated by hour-angle dependence across sets.
- **The shipped render's frame selection was disk-bound, not chosen** (168 of 373 by
  stride). An explicit culling decision is owed.
