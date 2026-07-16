# Dead-end registry + acquisition checklist

Durable, arch-independent field lessons: the processing dead-ends never to
re-attempt (each with its mechanism), and the acquisition choices that outrank
any processing knob. **Read the dead-end registry before proposing ANY
experiment** — if a thing does not work, the mechanism why is here. Full detail
+ the original numbers live in git history (the `checkpoint` commit's NOTES).

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
  SHO — i.e. SPCC is the *cause*, not the fix. The sphere needs a
  **star-colour-neutral** balance (neutralise the mean star colour → O3 boosted,
  stars carry ~no O3). **Headless path — tool half verified on 1.4.4, the design
  untested** (`docs/narrowband-star-neutral-options.md`): a **diagonal `ccm` IS
  that balance** — `ccm m00..m22 [gamma]`, the ONLY headless neutral-balance path
  (Manual Color Calibration has no CLI). Measure the field's mean star colour in
  the EXAMINE layer (numpy; no native command outputs it — an audit-layer item),
  then apply native `ccm`. Nightlight (`mlnoga`, headless Go CLI, GPL-3,
  **unmaintained**) does NOT do star-neutral-SHO "by name" — its `OpRGBBalance`
  default balances the **brightest 25% of stars** (not a "mid-population"), and its
  source says nothing of OIII/narrowband; the "lifts OIII" behaviour is our
  inference. A mechanism reference, not a dependency.
- `rmgreen`/SCNR on a sky that is not green-dominant prints a global magenta cast.
- Siril has NO native GENERAL chrominance-noise tool (its own docs punt to GIMP,
  byte-identical disclaimer in 1.4.4 AND 1.5.0-dev). `rmgreen` IS a native
  SCNR-style "chromatic noise reduction filter" but SINGLE-HUE (green cast only) —
  it does not close the general chroma gap. On x86 fill the general gap with an AI
  denoiser, NEVER a hand-rolled coring. **The gap is closable two ways:** (1) paid
  **NoiseXTerminator AI3** has a *dedicated* chroma path — `enable_color_separation`
  + `denoise_color` (chroma-HF, independent of luminance `denoise`) +
  `denoise_lf_color` (chroma-LF) — confirmed machinery (the only open piece is the
  exact `rc-astro nxt` CLI flag spelling — probe on x86); (2) FREE **Cosmic Clarity**
  Denoise `--denoise_mode separate --color_denoise_strength` is an explicit free
  chroma-vs-luminance control (quality unmeasured — x86 test). Free fallbacks
  without a chroma split: DeepSNR / GraXpert.

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
  the supplied xylist. This confirms `solve_field.py` is sanctioned, not a hack.
  **`image2xy`** (astrometry.net's own extractor) is source-verified to have NO
  shape/roundness gate (peak-in-connected-component) so it DOES return trailed
  sources — but it is NOT a clean retirement of the hand-roll: its trail knobs
  (`-a` saddle / `-p` / `-m`) aren't exposed by `solve-field`, a symmetric match
  kernel is SNR-mismatched to trails, and `-a` can fragment one trail into
  spurious detections → a **testable A/B**, not a swap (BACKLOG). Robustness
  ranking: (1) astrometry.net + own peak xylist; (2) `image2xy` xylist
  (shape-blind, A/B-pending); (3) native `-localasnet` AND **ASTAP** — LEAST (both
  PSF-fit / roundness-gated; ASTAP's own docs: *"star streaks … will be ignored,"*
  precondition *"stars reasonably round"* — it shares the roundness limitation, not
  an escape; wide DBs W08 FOV>20° / **G05 FOV>6°**; G17/H17/H18 deprecated). Keep
  `solve_field.py`; the x86
  test is `-relax=on -roundness=0.1 -maxR=large` vs the custom script vs ASTAP+W08
  vs an image2xy xylist (TOOLS.md Tier 2).
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
  MEASURED on the 43-min/1500-px-drift Cygnus set: a 9-min (310 px) window is
  better at EVERY radius and its inner field sits exactly at the single-frame
  floor — remove the drift and the homography becomes exact
  ([`wide-field-untracked-registration.md`](wide-field-untracked-registration.md)).
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
  suffer index sparsity, and it is a measured WIN on this set (roundness 0.550→0.656,
  flat across the field, 54/54 registered). **The lesson: for a wide UNTRACKED field,
  fit-the-distortion-from-sparse-trailed-stars is the dead end; measured-profile is the
  route.** (Fitting from star correspondences BETWEEN frames — PixInsight/APP — is a
  different, viable mechanism; it is the per-frame *catalog* solve that fails.)
- **In-exposure trailing is the unremovable FLOOR** — no registration method touches
  it. On a fixed tripod at 6 s / dec +47 / 18″px it is ~3.4 px predicted and ~3.6 px
  measured (per-frame roundness 0.615, uniform across the set). Stars are elongated
  ~1.6:1 at BEST; success is the EDGE matching the CENTRE, never round stars. That
  the per-frame roundness is *uniform* is also the proof the radial smear is
  introduced by register+stack, not by the frames.
- **Two traps that make a registration comparison lie — both hit in one experiment.**
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
- Cloud culling is by per-pixel MAJORITY risk, not visibility: a moving minority
  band stacks clean through `rej 3 3`; a DWELLING band becomes the per-pixel
  majority and survives. `nstars` is a blind cloud discriminant on rich fields
  (detection saturates at the star cap — the background channel carries the cloud
  signal).
- wFWHM weighting at low FWHM spread is WORSE than none (Siril `-weight` is a
  min-max ramp → worst frame ~0 weight at any spread).
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
  unstable symmetric PSF on ≈0 background. This is NO LONGER a blanket dead-end on
  x86: BlurXTerminator's learned model corrects elongated/trailed stars where
  classical RL cannot (`--correct-only`, `rc-astro bxt`, CPU ~30–40 s) — **BXT is
  the mature deconv path**. Free learned alternatives are weaker: **GraXpert deconv
  is pre-release only** (never shipped stable, open object-mode artifact bug #243)
  and Cosmic Clarity (CPU 15–30 min); **AstroSharp is OUT** (no Linux/CLI, 600 KB
  TIFF cap). Deconv is a real early-linear step (before *heavy* denoise) — a strong
  default, not absolute.

**QA / scope:**
- The GATE must be a composition-agnostic STATISTICAL sky scope — whole-frame
  reads real MW/object signal as a defect, and a geometric sky mask can't fix it
  (a bright object has no fixed band). Hand-picked patches miss defects a
  whole-scope measurement catches (the lesson that created the gate).
- Never hide a rim defect with a darker sky target or a crop — the rim is in the
  data (estimator extrapolation × stretch amplification), fix it there.
- Compare finals in LIKE encodings (q92+4:2:0 loses star-edge chroma to
  subsampling). Judgment is the user's eyes on FULL-FRAME LOSSLESS finals
  (PNG16+PNG8), opened independently; one bracketed knob per experiment; nothing
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
