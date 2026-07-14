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
  stars carry ~no O3). **Headless path — a design to test, not yet run**
  (`docs/narrowband-star-neutral-options.md`): a **diagonal `ccm` IS that
  balance** (arithmetic) — measure the field's mean star colour in the EXAMINE
  layer (numpy; no native command outputs it — an audit-layer item), then apply
  native `ccm`. Nightlight (`mlnoga`, headless Go CLI, GPL-3) does this by name
  but is **dormant** (2024) — a reference, not a dependency.
- `rmgreen`/SCNR on a sky that is not green-dominant prints a global magenta cast.
- Siril has NO native chrominance-noise tool (its own docs punt to GIMP) — the
  chroma-noise gap is real and **confirmed still non-native as of 1.5.0-dev**
  (same GIMP disclaimer). On x86 fill it with an AI denoiser, NEVER a hand-rolled
  coring — **NoiseXTerminator AI3 is the likely fill** (its architecture
  advertises "noise COLOUR & frequency separation"; `rc-astro nxt`, CPU ~20–30 s)
  — though a chroma-specific CLI control is unverified, so confirm before calling
  the gap closed; free fallbacks are DeepSNR / GraXpert / Cosmic Clarity.

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
  centroids don't feed the matcher). Blind-solve first, label after. Native
  `platesolve -localasnet` does NOT rescue this class: it still feeds
  astrometry.net Siril's `findstar` PSF-fit detection (on the green layer), and
  when FOV > 5° it further **crops detection to the central area** unless
  `-nocrop`. `setfindstar -relax=on` only loosens quality checks (more
  false-positives) — it does not become a peak-centroid detector. **Feeding
  astrometry.net a peak-centroid xylist is the INTENDED shape-blind override**
  (solve-field with an xylist runs NO extraction; the matcher is geometry-only,
  Lang 2010) — this confirms `solve_field.py` is doing the sanctioned thing, not
  a hack. Robustness ranking: (1) astrometry.net + own peak xylist, (2) ASTAP +
  the wide DBs **W08/G05** (HFD centroids, no roundness gate — *predicted* to keep
  mild trailing, measure; the D-series caps at 6°, G17/H17 deprecated), (3) native
  `-localasnet` (least). Keep `solve_field.py`; the x86 test is `-relax=on
  -roundness=0.1 -maxR=large` + `-nocrop` vs the custom script vs ASTAP+W08
  (TOOLS.md Tier 2).
- 1-pass sequence-start registration strands drifting tail frames; 2-pass + low
  detection sigma recovers them; on trailed frames a reference sweep beats the
  auto-reference. Keep all frames (dropping a minority sub-focal subset buys no
  matching gain and pays the full √N noise penalty).
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
