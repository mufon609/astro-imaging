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

## The defect, quantified (Siril `findstar`, binned by field radius)

`scripts/qa/star_shape_profile.py` bins Siril's PSF fits by distance from the
field centre — the measurement that separates "the registration model is wrong"
(shape degrades with radius) from "the frames are soft" (shape flat vs radius).
Roundness here is orientation-blind minor/major; 1.0 = round.

Existing baseline (124 frames, CFA-registered, full 43-min window), 23,830 stars,
whole-frame roundness 0.542 / major-axis FWHM 5.25 px:

| r (px) | roundness | major FWHM |
|---|---|---|
| 0–444 | 0.531 | 4.78 |
| 889–1333 | 0.553 | 4.88 |
| 1778–2222 | 0.520 | 6.05 |
| 2222–2666 | **0.478** | **7.61** |

Monotonic growth with radius — the radial signature. The worst region (right
edge) reaches majFWHM 9.66 px and roundness 0.35 in the top-right corner.

- **MEASURED — the asymmetry is NOT explained by an off-centre crop.** A scan for
  the centre that best makes majFWHM a function of radius lands at (2000,1750) —
  only 87 px from the crop centre — and improves the rank correlation only
  0.320 → 0.331. So the pattern is predominantly radial **plus a genuine
  one-sided component** (at comparable radius, right majFWHM 9.66 vs left 5.66).
  Differential refraction (asymmetric with hour angle) and lens decentering are
  the candidates; **UNRESOLVED** here.

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
  the darktable lens module's *enabled bit* (matched `lensfix`/`nolens` styles, both
  `--style-overwrite`, identical module sets).

| | frames | stars/Mpx | roundness | majFWHM | roundness vs radius |
|---|---|---|---|---|---|
| **OFF** (control) | 52/54 | 981 | 0.550 | 4.63 px | 0.507→0.570→**0.556** (sags; majFWHM spikes 5.19) |
| **ON** (lensfun) | **54/54** | **1418 (+45%)** | **0.656** | **4.25 px** | **0.674 / 0.683 / 0.655 / 0.631 / 0.659 — FLAT** |

- **WIN.** The edge degradation is gone: roundness holds ~0.63–0.68 from r=448 to
  r=2685. Crops: `qa_work/reg/star_shapes_lensfun.png` — the control's edge is washed
  into diagonal streaks; the corrected edge is a dense field of point stars.
- **MECHANISM CONFIRMED, not just the outcome:** the **CENTRE** bin also improved
  (0.507 → 0.594) where distortion is ≈0. That is exactly the prediction — undistort
  the frames and ONE global homography fits *every* star, instead of being a
  compromise that degrades everywhere. It also explains why two frames that could not
  match now register (52/54 → 54/54).
- **Traps checked:** this is stars **per Mpx** (ON's frame is 3% *smaller*, so +45% is
  not the area artifact), and roundness is a shape measure, so it cannot be inflated
  by extra detections.
- **CONFOUND DECLARED:** the preset carries `modify_flags=7` = distortion|TCA|vignetting,
  so vignetting + TCA correction were applied too. Vignetting cannot change star SHAPE
  but it brightens corners and so inflates part of the star-COUNT gain; the
  roundness/FWHM gains and the centre-bin gain (vignetting ≈1.0 there) are
  uncontaminated. A distortion-only re-run (`modify_flags=1`) is BACKLOG.
- **NOT a shippable render.** darktable works from raw, so this arm carries **no
  darks/flats** — dark/flat calibration must happen in sensor space BEFORE any
  geometric warp. It is a GEOMETRY test, which is valid precisely because the defect
  is flat-independent. Absolute numbers are **not** comparable with the A/B/C
  experiments (different pipeline); only OFF-vs-ON is.

## The july14 decision (the loop's RECOMMEND → REPORT → the user decides)

- **Recommended:** the **lensfun distortion model**, productionised — it removes the
  edge degradation **at full 43-min depth**, which neither route A nor C could do.
  The remaining work is ORDERING, not discovery: Siril calibrate (CFA, dark + the
  validated sky flat) → debayer → apply the warp → register → stack. The open
  engineering question is applying the lensfun warp to a *calibrated linear image*
  rather than to raw.
- **Superseded:** route A (full depth, measured edge defect) and route C (short
  window, floor-limited, 1/4 depth, +56% field). The depth-vs-edge trade-off is no
  longer forced. Keep C as the fallback if productionisation fails.
- **Not proposed:** cropping to the good field — that hides a defect that is in the data.
- **The honest floor, restated:** ~3.4–3.6 px of in-exposure trailing is in every frame
  and **no method removes it**. Success is the edge matching the centre — which the
  lensfun route now achieves.
- **Trade-off recorded:** the fix depends on a COMMUNITY-measured lens profile (not
  Nikon's own coefficients, which ship in every NEF but sit in a private block no
  headless tool applies) and on a lensfun DB update the distro does not provide.
  Both are cheap and reproducible; neither is under our control.

## What graduates

- **[`../TOOLS.md`](../TOOLS.md):** Tier 2 — Siril 1.4.4 `register -disto=`
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

**EMPIRICALLY TESTED on the real july14 set-01 frames.** Two routes to a
distortion model were implemented and measured against the SAME one-knob harness:
Siril `register -disto=` fed an astrometry.net SIP — **killed (a LOSS), with its
numbers**; and an OFFICIAL MEASURED profile (darktable + lensfun) — **WIN**:
roundness-vs-radius flattens (0.550 → 0.656 whole-frame, flat 0.63–0.68 across the
field) at FULL depth, and 54/54 frames register. Root cause established from theory
(Szeliski), from the tools' own measurements, and from experiment C, then CONFIRMED
by the fix behaving exactly as predicted (the centre improves too).
**Remaining work is ordering, not discovery:** calibrate in sensor space → warp →
register, so darks/flats and the validated sky flat survive. The dust-preservation
gate (the user's eyes on full-frame lossless finals) has NOT yet run on a
productionised render.
