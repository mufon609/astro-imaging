# Dead-end registry + acquisition checklist

Durable, arch-independent field lessons: the processing dead-ends never to
re-attempt (each with its mechanism), and the acquisition choices that outrank
any processing knob. **Read the dead-end registry before proposing ANY
experiment** — if a thing does not work, the mechanism why is here. Full detail
+ the original numbers live in git history (the NOTES at the commit whose message
begins `checkpoint:` — `git log --oneline --grep='^checkpoint:'`).

## Dead-end registry — do NOT re-attempt

Data / physics / tool-doctrine mechanism lessons.

**Gain / flat** (self-calibration — real flats are the primary path; when they
have issues, synthetic-flat / vignetting correction is a GAP to fill with an
OFFICIAL tool, never an in-house fit. The entries below are methods that FAIL —
the constraints any such tool must satisfy):
- A free-form gain fit bakes sky glow into the gain (peaks off-axis toward the
  glow) — sanity-check any gain by its centre.
- A polynomial radial V(r) oscillates → concentric RINGS after division; only a
  monotone isotonic V is admissible. A per-channel V tints the corners (glow
  contaminates the per-channel falloff) → V must be GRAY.
- The true V lies between the multiplicative and additive fits of the median;
  only the empirical V2 of the frames ACTUALLY being divided is flat.
- Never refine the gain from the STACK's residual — the sky's own structure
  (MW/glow/clouds) exceeds the residual, giving opposite-sign results.
- A SKY FLAT (median of un-registered lights) captures vignetting + dust motes +
  PRNU, but a frame-filling faint complex (MW/IFN) does NOT reject — it bakes into
  the flat and division ATTENUATES the cosmic dust. The only fix is manual
  clone-stamping (GUI, non-reproducible). So the sky flat is dust-safe ONLY when
  faint structure is a small part of the frame; validate before use
  ([`synthetic-flats-and-bias.md`](synthetic-flats-and-bias.md)).

**Background:**
- The MW band IS frame-scale curvature at wide focal → `seqsubsky 2` erases it;
  only a first-degree plane or a full BGE is MW-safe.
- Stack-level-only BGE leaves a STRUCTURED residual (visible rings, loses MW);
  per-frame `subsky 1` is the MW-safe background step.
- GraXpert AI smoothing is NOT faint-nebulosity protection — smoothing blurs the
  model OUTPUT, not the inference; a frame-filling faint complex reads as the
  trained light-pollution class and is absorbed. Use a plane/off for
  object-filling fields. BGE does NOT absorb a centred galaxy's halo (it measures
  STRONGER against a lower far-field sky).

**Stretch / colour:**
- Unlinked autostretch on a calibrated stack is the chroma-blotch ("rainbow")
  engine — after SPCC there is no cast to compensate; use linked. Unlinked
  sky-anchored stretch as a narrowband line-lift is a NO-OP (BGE+SPCC already
  equalize the channel skies; the line imbalance is OBJECT flux, not sky).
- SPCC narrowband equalizes O3=Ha and erases the O3 sphere (raw O3/Ha ~1.5 →
  ~1.0; sphere B/R 0.77 vs 3.21). Siril's own docs confirm SPCC-NB gives "real
  intensities"/"a huge green cast" and recommend Manual Color Calibration for
  SHO — i.e. for a narrowband SHO target, SPCC is the *cause* of the lost sphere,
  not the fix. (The star-colour-neutral fix is a candidate DESIGN, UNTESTED —
  `docs/narrowband-star-neutral-options.md`; not settled, do not cite as a method.)
- `rmgreen`/SCNR on a sky that is not green-dominant prints a global magenta cast.
- Siril has NO native GENERAL chrominance-noise tool (its own docs punt to GIMP,
  byte-identical disclaimer in 1.4.4 AND 1.5.0-dev). `rmgreen` IS a native
  SCNR-style filter but SINGLE-HUE (green cast only) — it does not close the general
  chroma gap. NEVER hand-roll a chroma coring; close the gap with an AI denoiser on
  x86 (tool options + their chroma-vs-luminance flags: `TOOLS.md`).

**Separation** (informs the x86 tool choice):
- A mask+inpaint separator DESTROYS resolved-object structure (inpaints HII knots
  out as stars, screens them back as blobs); a learned separator (StarNet2/StarXT)
  keeps field-star flux and far less object structure. Use the learned separator
  on resolved objects.
- A bright-star residual/shell is a per-DATA property (tight PSF vs big trailed
  PSF) — measure per dataset, never carry one set's number to another.

**Detection / solve / registration:**
- Frame QA + registration run on DEBAYERED data only — CFA-lattice registration
  false-positives on cloud texture (adjacent cloud frames cross-match → a cloud
  reference).
- Siril's internal solver fails ultra-wide trailed fields even with the local
  catalog; astrometry.net blind solve from coarse PEAK centroids works (blob/PSF
  centroids don't feed the matcher). Blind-solve first, label after.
  **REFINED (measured, 36.45° field, correct centre from a blind solve, local Gaia,
  `-nocrop`): the blocker is Siril's star MATCHER, not detection quality and not
  catalogue depth — both were tested and ELIMINATED.** Relaxed detection
  (`setfindstar -relax=on -roundness=0.05 -sigma=0.5`) raised candidates 3316→8694
  and still failed; `-limitmag=+4` raised the catalogue fetch 2177→138,498 Gaia
  stars (limit mag 7.81→11.81) and still failed ("Initial solve failed" → near-solve
  failed). Do not re-attempt those two knobs. Side finding worth knowing: Siril's
  AUTO limit magnitude for a 36° field is only **7.81**, while its detection goes far
  deeper — a real population mismatch, just not the blocker. Native
  `platesolve -localasnet` does NOT rescue this class: it still feeds
  astrometry.net Siril's `findstar` PSF-fit detection (on the green layer) — that
  detection alone is the failure mode; the FOV>5° detection auto-crop is
  *"Ignored for astrometry.net solves"* (Siril concept page) — a Siril-internal-
  solver behaviour only, so it is not a `-localasnet` failure mode and `-nocrop`
  is moot there.
  `setfindstar -relax=on` only loosens quality checks (more false-positives) — it
  does not become a peak-centroid detector. **Feeding astrometry.net a
  peak-centroid xylist is the INTENDED shape-blind override** (solve-field given
  an xylist runs NO pixel extraction; the matcher is geometry-only, Lang 2010) —
  but ADD `--no-remove-lines --uniformize 0` or two LIST-level filters still thin
  the supplied xylist. This confirms the xylist-feed design is sanctioned, not a hack.
  **An official extractor does the job, better:** SExtractor's core (`sep`) is
  shape-blind (returns trailed sources, median elongation ~1.3 measured),
  blind-solves at HIGHER odds than in-house peak centroids (logodds 299 vs 289,
  scale Δ 1.2e-5), and its WCS yields identical SPCC K factors — `solve_field.py`
  defaults to it (per-dataset A/B record: `extractor_ab.json`). Two valid fits'
  centres can differ by hundreds of arcsec — the SIP wobble documented below,
  which never reaches SPCC (it re-matches stars from the seed).
  **`image2xy`** (astrometry.net's own extractor) is source-verified shape-blind
  too and stays an optional binary cross-check — its trail knobs (`-a` saddle /
  `-p` / `-m`) aren't exposed by `solve-field`, a symmetric match kernel is
  SNR-mismatched to trails, and `-a` can fragment one trail into spurious
  detections. Robustness
  ranking: (1) astrometry.net + a **sep** xylist (measured); (2) the
  in-house peak xylist (fallback, retirement pending — removal register); (3)
  `image2xy` xylist (shape-blind, untested); (4) native `-localasnet` AND **ASTAP** — LEAST (both
  PSF-fit / roundness-gated; ASTAP's own docs: *"star streaks … will be ignored,"*
  precondition *"stars reasonably round"* — it shares the roundness limitation, not
  an escape; wide DBs W08 FOV>20° / **G05 FOV>6°**; G17/H17/H18 deprecated).
- 1-pass sequence-start registration strands drifting tail frames; 2-pass + low
  detection sigma recovers them; on trailed frames a reference sweep beats the
  auto-reference. Keep all frames (dropping a minority sub-focal subset buys no
  matching gain and pays the full √N noise penalty).
- **Wide UNTRACKED edge smear: "field rotation / gnomonic projection" is NOT the
  cause.** For an IDEAL rectilinear lens a pure camera rotation maps EXACTLY to an
  8-DOF homography (stars are at infinity; sky rotation is SO(3), linear in
  homogeneous coordinates) — zero residual. Szeliski, *Image Alignment and
  Stitching* §2.3, names the residuals that survive an optimal global fit, and for
  a star field only one applies: **unmodelled RADIAL LENS DISTORTION**. The real
  map is `distort ∘ H ∘ distort⁻¹`. Distortion displaces stars ∝ radius → centre
  sharp, edges smeared; as a star drifts it samples a different local distortion
  and no global fit absorbs the difference. So the fix is **undistort → homography**,
  NOT a local/elastic transform. Do not chase "better global transforms"
  (`-transf=` tops out at homography, which is already exactly right).
  MEASURED on a 43-min/1500-px-drift set, two independent ways: a 9-min
  (310 px) window is better whole-frame (majFWHM 3.87 vs 4.74 px) and undistorting
  the frames collapses Siril `seqtilt`'s off-axis aberration 0.57 → 0.25 px at FULL
  depth — remove the drift *or* remove the distortion and the homography becomes
  exact, which is the same statement twice
  ([`wide-field-untracked-registration.md`](wide-field-untracked-registration.md)).
  (The short-window arm's per-radius numbers came from a retired in-house radial
  metric — trap 3 below — and its stacks are gone, so they are not quoted; the
  whole-frame and `seqtilt` evidence above is what the conclusion rests on.)
- **astrometry.net's SIP is NOT a reproducible lens model at wide index scales —
  so `register -disto=` has no model to eat.** The camera was on a fixed tripod
  (lens distortion physically identical every frame), yet two independent solves
  43 min apart disagree at the same sensor positions by **65 px median / 128 px
  worst**; a real lens model must agree to ~1 px. Raising the star cap to 1500 cut
  it only to 44 px (worst 132) while sharply improving the LINEAR solve (scale
  agreement, RA-drift error 6%→0.3%, logodds 127→782) — **more stars fix the
  position, not the distortion**. Mechanism: the SIP tweak is constrained by
  *matched index* stars, and the 4200-series index at the wide scales an ultra-wide
  field needs (12–19) is Tycho-2-based and sparse. Feeding this SIP to
  `register -disto=` is a measured **LOSS** (whole-frame majFWHM 4.74→6.02 px,
  detected stars 17,770→7,561, smear spread frame-wide). **This blocks the
  WCS-reprojection route too** (SWarp / astropy `reproject` need the same per-frame
  solution). The `-disto=` MECHANISM is sound — **the model source was the gap, and it
  is now closed**: use an OFFICIAL *measured* lens profile (darktable + lensfun,
  `TOOLS.md` Tier 2b) instead of fitting one from the data. A measured profile cannot
  suffer index sparsity, and it is a measured WIN — Siril `seqtilt`,
  control → corrected → full-depth render: **off-axis aberration (the radial
  term) 0.57 → 0.31 → 0.25 px**, stars 5095 → 10707 → 11805, 54/54 registered.
  **The lesson: for a wide UNTRACKED field, fit-the-distortion-from-sparse-trailed-stars
  is the dead end; measured-profile is the route.** (Fitting from star correspondences
  BETWEEN frames — PixInsight/APP — is a different, viable mechanism; it is the
  per-frame *catalog* solve that fails.)
  **What the model does NOT buy, measured on the same runs:** sharpness is NULL
  (truncated mean FWHM 3.20 → 3.28 → 3.27 px — the in-exposure floor below is
  untouched, exactly as predicted), and the **one-sided component is NOT corrected**
  (sensor tilt 0.50/16% → 0.42/13% → 0.51/16%). A radial model cannot fix a
  one-sided term and does not. The correction buys star COUNT and radial UNIFORMITY.
  Do not claim an FWHM win for it.
- **In-exposure trailing is the unremovable FLOOR** — no registration method touches
  it. On a fixed tripod at 6 s / dec +47 / 18″px it is ~3.4 px predicted and ~3.6 px
  measured (per-frame roundness 0.615, uniform across the set). Stars are elongated
  ~1.6:1 at BEST; success is the EDGE matching the CENTRE, never round stars. That
  the per-frame roundness is *uniform* is also the proof the radial smear is
  introduced by register+stack, not by the frames.
  **Measure note — the floor's px numbers are not one statistic.** ~3.4 is a predicted
  trail LENGTH; the ~3.6 per-frame FWHM was CFA-sampled (Bayer-inflated, relative-only
  — removal-condition register); station values are debayered majFWHM medians
  (3.4–3.8 px at the perpendicular stations); `seqtilt`'s truncated mean mixes axes
  and reads 3.0–3.1 px on the same stacks. Compare within one statistic; the operative
  claim is edge ≈ centre, never an absolute px value across statistics.
- **A community lens profile can fix the edges and still WRITE A NEW DEFECT into the
  centre — the paraxial-error × drift band.** True distortion → 0 at the optical axis,
  so an UNCORRECTED wide untracked stack has a pristine centre (the control's centre is
  its best region). A community radial profile carries a small paraxial error ε(r);
  as a star's sky position CROSSES the axis during the drift the radial unit vector
  flips sign, so ±ε becomes a ~2ε smear ALONG THE DRIFT, confined to the corridor the
  axis swept — a band through frame centre, worst at the very centre, invisible
  perpendicular to the drift. MEASURED (Siril findstar at fixed 350 px stations about
  the geometric centre, along/perpendicular to the solved drift axis): full-depth
  centre station majFWHM **5.30** / roundness **0.480** vs perpendicular
  **3.60–4.12** / up to **0.706**; the no-model control INVERTS it (centre
  4.03/0.556 — its best; degradation outward along the drift instead). The band is
  a FAINT-star/texture defect (bright cores read fine at tight detection sigma) —
  a stretch shows it and bright-star medians hide it. **`seqtilt` off-axis
  aberration (centre vs corners) is BLIND to it and even improves as the centre
  degrades toward the corners' mean** — never accept a wide-untracked render on
  `seqtilt` alone; measure fixed drift-axis stations
  (`scripts/qa/star_stations.py`). A tracked rig can never see this term (no
  drift), consistent with no mainstream reference reporting a "field-centre"
  residual. ε-source candidates (open — the fix is the same regardless):
  community a/b/c fitted with the centre pinned at image centre (absorbing the
  calibrator copy's decentering into radial terms that don't transfer between
  units); focus-distance dependence; unit variation. **The fix:** a model fitted
  FROM THIS UNIT'S OWN FRAMES by between-frame star-correspondence fitting — the
  mechanism the SIP dead-end explicitly leaves viable
  (`scripts/darktable/fit_lens_model.sh` → `install_lens_model.sh`; traps in the
  script + TOOLS.md Tier 2b) — removes the band (centre station 5.30 → 3.67 px at
  full depth, every station at the perpendicular-station level) and sharpens the
  whole frame (seqtilt truncated-mean 3.27 → 3.06 px — a different statistic;
  measure note in the floor entry above). Also KILLED: the solved effective focal
  (67.8) as the lensfun interpolation key — the interpolated 50–70 model is WORSE
  at the centre (5.42 vs 4.88 px); the calibrated focal=70 entry is the best
  community key.
- **A darktable lens STYLE carries NOTHING but the enabled bit — and an unmatched lens
  is a SILENT NO-OP.** The `op_params` blob bakes method, modify_flags, camera, lens,
  focal, aperture and scale; darktable IGNORES all of it, re-detects the lens from
  each image's EXIF, and applies its DEFAULT correction set (distortion + TCA +
  **vignetting**). Measured: EXIF focal 70 vs 24 → opposite-sign displacement fields
  (+26→+69 px vs −6→−19 px); `scale` 1.046 vs 0 vs 1.5 → identical to 0.000 px; a
  swapped lens string → that lens's own profile; modify_flags 0–7, method/inverse
  flips, and a BLANKED blob lens string → byte-identical output (uniform/grid card,
  Siril `stat`). ONE style is therefore camera-, lens- and focal-general — and the
  correction SET cannot be chosen in a style at all. The unwanted vignetting
  correction DOUBLE-corrects flat-corrected lights: corner/centre **1.27–1.37×
  linear** measured on a full-depth stack, 2.2–2.6× after the stretch. **Enforce the
  correction set in the DATA lensfun reads:** strip `<vignetting>`/`<tca>` from the
  lens's block in the user DB (`install_lens_model.sh`) so distortion is the only
  correction darktable CAN apply; verify after any darktable/lensfun bump by warping
  a uniform card through the style — corner medians must equal the centre (Siril
  `stat`).
  **The trap is the other side of the same mechanism.** Because nothing is baked, a lens
  the DB cannot match gets **NO correction, silently**: an unrecognised `LensModel`
  produced max |dr| = **0.000 px over 413 stars**, exit 0, and **not one word in the log**.
  A wrong-but-present lens is worse — it applies a wrong, weaker model, also silently. So:
  - **darktable CANNOT be relied on to degrade loudly. It never fails.** A set whose lens
    is missing from the DB stacks UNCORRECTED and the only symptom is a worse `seqtilt`
    off-axis aberration in the final — i.e. exactly the defect the route exists to remove,
    reintroduced with no warning.
  - **"Did the warp happen?" is NOT a sufficient guard** — it passes on the wrong-lens
    case. The guard must assert the EXIF camera+lens+focal against the DB and against the
    set's recorded `acquisition.json`, per set, BEFORE the run; a non-zero warp is only a
    secondary confirmation.
  - Corollary: this is what makes a MIXED-focal or mixed-lens set a hard stop rather than
    an interpolation — every frame silently gets its own EXIF's model.
- **Round-tripping linear astro data through a raw converter: MATCH the ICC tag, never
  "force linear".** Siril's `savetif` embeds **`sRGB-elle-V2-srgbtrc.icc`** — an sRGB
  TONE CURVE — on LINEAR pixels, and **`icc_assign sRGBlinear` does NOT change what
  `savetif` embeds** (the export profile comes from a save-time preference; `set
  gui.icc_pedantic_linear=true` does not change it either). So a converter reading that
  TIFF applies an sRGB→linear DECODE to already-linear data. Exporting with a LINEAR
  profile (`darktable --icc-type LIN_REC709`) then leaves that decode UNCANCELLED:
  measured A_out/A_in climbing **0.1008 → 0.2121** across the brightness range
  (effective gamma ≈1.34) — silently destroying photometry, SPCC and the stretch while
  looking fine on a preview. **The fix is to MATCH the output profile to the input tag**
  (`--icc-type SRGB`): the decode and the re-encode cancel exactly — VERIFIED as an
  identity round trip, A_out/A_in = **0.9996–1.0000**, IQR 0.0003. The tag is
  "wrong" either way; what matters is that it is wrong *consistently*. Always verify
  linearity with star AMPLITUDES vs brightness (a constant ratio), never with a mean or
  a preview: a gamma preserves the median's rank order and hides in a stretch.
- **Three traps that make a registration comparison lie — all three hit on one set.**
  (1) **Survivorship bias:** a bad registration spreads flux below the detection
  threshold, so the SURVIVING stars' median roundness/FWHM can *improve* while the
  image gets worse — the `-disto=` LOSS above reported a BETTER edge median (4.61 vs
  6.46 px) on a visibly-destroyed frame. Always read a star-shape metric with its
  **n**, and confirm on full-frame crops. (2) **Area confound:** `-framing=min` gives
  each variant a DIFFERENT frame size (less drift ⇒ larger intersection), so raw star
  counts are not comparable — a short-window stack's higher count was entirely its
  56% larger frame; per unit area it was slightly LOWER. Compare **stars per Mpx**, or
  not at all. Also open the detection gate (`setfindstar -roundness=0.05 -relax=on`)
  when measuring elongation, or the metric silently rejects exactly the stars under
  test.
  (3) **A CIRCULAR METRIC — an origin inferred from the data it measures.** A radial
  star-shape profile binned Siril's `findstar` list about the STAR BOUNDING-BOX centre.
  That origin is a function of the defect: the smear suppresses edge detections, the
  box shrinks toward the good region, the origin moves — **measured 537 px of origin
  shift** from a detection-sigma change alone, after which the profile reported
  roundness *improving* outward on a stack whose right third yields no detections at
  all. A worse defect makes the metric look better, and the same circularity
  manufactures doubt about real defects just as easily — it settles nothing in either
  direction. The generalisation: **never key a metric to a geometry
  derived from the measurement itself** — measure about a FIXED, externally-known
  origin, or use the tool's own measure. Siril has one headless:
  **`seqtilt`** (off-axis aberration = centre vs corners; sensor tilt = best vs worst
  corner) — no origin to get wrong, though it is a WHOLE-FRAME measure and blind to a
  drift-aligned band (paraxial-band entry; `tilt`/`inspector` are "Can be used in a
  script: NO"). Star COUNT per radial bin is not a quality measure
  either: it is sky density × detection efficiency, and detection efficiency peaks
  exactly where the sky is poorest.
- Cloud culling is by per-pixel MAJORITY risk, not visibility: a moving minority
  band stacks clean through `rej 3 3`; a DWELLING band becomes the per-pixel
  majority and survives. `nstars` is a blind cloud discriminant on rich fields
  (detection saturates at the star cap — the background channel carries the cloud
  signal).
- wFWHM weighting at low FWHM spread is WORSE than none (Siril `-weight` is a
  min-max ramp → worst frame ~0 weight at any spread).
- **Never sigma-reject across SUB-STACK composes.** Sub-stacks are clean
  ~group-size means, so their mutual scatter is ~√group below per-frame noise —
  a 3σ gate at that tiny σ fires on the systematic differences sub-pixel
  registration leaves along steep gradients (star edges, MW lanes), not on
  outliers. Measured (`rej 3 3` across 25 fifteen-frame sub-stacks vs a plain
  mean of the same registered set): pixels rewritten by up to **±3800 ADU on a
  ~140 ADU sky**, star cores carved out, dark rip-like streaks through
  structured regions — while whole-frame `seqtilt` medians stayed FLAT (stars
  13,903 vs 13,784; FWHM 3.07 vs 3.10), so the damage is invisible to
  frame-wide statistics and shows on the stretched final. Reject within groups
  (full per-frame strength, where satellites die); compose sub-stacks with a
  PLAIN MEAN.
- Drizzle: "short focal / large pixels ⇒ oversampled" is BACKWARDS (that geometry
  gives large arcsec/px → *few* px per star → UNDER-sampled, drizzle's home turf).
  Judge sampling by measured **minor-axis FWHM**, not the "wide" label: ≥~2–3 px =
  oversampled (skip), <2 px = undersampled (2× drizzle *can* help IF real
  sub-pixel dither + many registered frames). Trailed data is oversampled only
  where *trailing/bloat* spreads the star; drizzle is pointless there because
  trailing breaks the dither/registration preconditions AND drizzle can't de-trail
  (it renders a sharper *smeared* star). CFA-drizzle 1×/pixfrac 1.0 is a separate
  OSC-only win (cleaner colour noise). `docs/plate-solving-and-drizzle.md`.
- CLASSICAL deconvolution (makepsf + RL) where trailing is in-exposure fails —
  unstable symmetric PSF on ≈0 background. (A LEARNED deconvolver is NOT classical RL
  and is a live x86 option, not a dead-end — tool choice + CPU costs in `TOOLS.md`.)

**QA / scope:**
- The GATE must be a composition-agnostic STATISTICAL sky scope — whole-frame
  reads real MW/object signal as a defect, and a geometric sky mask can't fix it
  (a bright object has no fixed band). Hand-picked patches miss defects a
  whole-scope measurement catches (the lesson that created the gate).
- **Never read a LINEAR residual off a STRETCHED surface.** An autostretch places the
  sky low on a steep curve, so it can compress or amplify a background ratio by
  several× depending on where the background lands — the same class of gradient read
  "corner/centre 1.06" on an autostretched preview and **1.27–1.37 linear** on the
  shipped stack (2.2–2.6 in its stretched judge PNGs). A display-domain ratio answers
  "what does the eye see", never "how big is the residual": measure gradients with
  Siril `stat` regional medians on the LINEAR image, and state the domain with the
  number. (Same trap in reverse: a pedestal-included ADU ratio understates a light-
  domain falloff — a ~1 EV vignetting read "6.3%" with the ~1007 ADU pedestal in.)
- Never hide a rim defect with a darker sky target or a crop — the rim is in the
  data (estimator extrapolation × stretch amplification), fix it there.
- Compare finals in LIKE encodings (q92+4:2:0 loses star-edge chroma to
  subsampling). Judgment is the user's eyes on FULL-FRAME LOSSLESS finals
  (16-bit PNG only — never an 8-bit/reduced-depth/lossy copy), opened
  independently; one bracketed knob per experiment; nothing
  aesthetic commits before the user's eyes.

## Acquisition checklist — the real quality lever

Acquisition quality outranks processing; never bandaid what photons must fix.

- Record **14-bit Lossless-compressed** raw, NOT High-Efficiency (HE/HE★ is
  TicoRAW-compressed, lossy-ish, and forces a DNG fallback); confirm 14-bit
  (high-speed continuous can drop to 12-bit).
- Use the sensor's higher conversion-gain stage (a dual-gain CMOS drops read
  noise above its switch ISO); keep subs ≤ 500/focal-mm — star trailing, not read
  noise, caps sharpness on an untracked/lightly-tracked rig.
- MORE integration is the real lever: when band signal/grain ≈ 1, every processing
  knob is only polishing until more photons arrive.
- Flats per focal length used that night, BEFORE touching the zoom; METER to a
  ~50% histogram peak (don't trust a shutter value); diffuse the source (a bare
  screen shows its pixel grid). VERIFY uniformity: shoot a flat, rotate the camera
  180° against the source, shoot another — the two corner/centre ratios must match
  (an over-peaked source adds falloff the lens lacks and the flat is unusable; the
  lights' own sky corner/centre is the cross-check).
- Darks at the lights' exposure/ISO at night temperatures; biases at the flats'
  shutter (= exact flat-darks) — shoot them, it is 30 seconds.
- Lock the zoom ring (tape); don't touch the camera mid-set (a focal-length step
  forces a mixed-optics stack). Dither between subs; avoid the moon (star fringes
  on trailed PSFs are dispersion — physical, not removable in processing). Stop a
  fast lens down ≥1 stop for bright-star fields (wide open adds a red veiling-glare
  halo — an honest optical signature, not a bandaid to remove).
