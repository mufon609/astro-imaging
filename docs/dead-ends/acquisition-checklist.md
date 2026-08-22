# Acquisition checklist — the real quality lever

Phase-2 file of the dead-ends registry split (`README.md` here holds the index
and dispositions; pre-compression forms live in git and in the live
`docs/dead-ends.md` until the merge).

<!-- phase-2: maintained in place; not regenerated from the manifest -->
Acquisition quality outranks processing; never bandaid what photons must fix.

- Record **14-bit Lossless-compressed** raw, NOT High-Efficiency (HE/HE★ is
  TicoRAW-compressed, lossy-ish, and forces a DNG fallback); confirm 14-bit
  (high-speed continuous can drop to 12-bit).
- Use the sensor's higher conversion-gain stage (a dual-gain CMOS drops read
  noise above its switch ISO); keep subs ≤ 500/focal-mm — star trailing, not
  read noise, caps sharpness on an untracked/lightly-tracked rig.
- MORE integration is the real lever: when band signal/grain ≈ 1, every
  processing knob is only polishing until more photons arrive.
- Flats per focal length used that night, BEFORE touching the zoom; METER to
  a ~50% histogram peak (don't trust a shutter value); diffuse the source (a
  bare screen shows its pixel grid). VERIFY uniformity: shoot a flat, rotate
  the camera 180° against the source, shoot another — the two corner/centre
  ratios must match (an over-peaked source adds falloff the lens lacks; the
  lights' own sky corner/centre is the cross-check).
- Darks at the lights' exposure/ISO at night temperatures; biases at the
  flats' shutter (= exact flat-darks) — shoot them, it is 30 seconds.
- **DEW CONTROL (measured cost, july23: two of four sets excluded from the
  final combine).** A clear still humid night radiation-cools the lens below
  the dew point even in summer; the film NEVER self-clears and faint-star
  loss precedes the visible film. Run a low-power lens heater band from
  session START (2–3.4 W suffices; minimum power that prevents dew — excess
  heat makes convection/soft stars), riding the extended barrel; the 24-70's
  petal hood is sized for 24 mm and is weak protection at 70 mm; a small fan
  works where a band is absent. Watch the brightest star's halo live and
  flashlight the front element when in doubt; if dew is found, warm and
  continue — never stack through it (a contiguous dewed block is NOT
  rejectable per-pixel; the cull is by frame, post-hoc identifiable by the
  halo/FWHM/nstars timeline — mean-based ministacks + the frame-QA trends;
  numbers in the halo-photometry entry, `measurement-discipline.md`).
- **VERIFY FOCUS ON THE FIRST FEW FRAMES, then leave it alone — and if you
  must refocus, do it AT A SET BOUNDARY, never mid-set.** MEASURED on one
  session: the first 149 frames ran 9% soft (registration FWHM 2.944 px vs
  2.680 achievable) and the deficit was present in frame ONE at 2.910 — the
  lens was never focused, not drifting. A mid-set correction then cost 205 s
  of pause, three handling-ruined frames, and a 1.2° re-aim that split the
  set into two pointing swaths — forcing a 152-frame block exclusion, a
  separate flat, and a smaller min-framing intersection for every product
  that set entered; the same correction 15 min later at the set boundary
  would have cost nothing. Post-correction focus held 90+ min: the apparent
  later "drift" REVERSED with nothing touched — seeing, not focus — so
  periodic refocusing is not supported by the data; the per-set QA FWHM is
  the self-check that would show a real drift. Cheap check up front: shoot a
  handful, read the frame-QA FWHM/star counts, fix it then.
- **DO NOT SHOOT A FAINT BROADBAND TARGET UNDER HEAVY MOONLIGHT — measured,
  the integration does not buy it back.** A 98%-lit moon 24° up, 72° off the
  field raised the sky ~4× against a moonless night at the same hour
  (R/G/B 116/219/166 ADU above pedestal vs 27/52/40 — a ratio SENSITIVE to
  the pedestal reference, which those figures did not state; the excess is
  colour-neutral, which is what identifies moonlight rather than a light
  dome). **The rule that costs: any figure quoted "above pedestal", "above
  background" or "net of" MUST state its denominator** — the offset form of
  the state-the-denominator rule, and a literal grep cannot find the class
  (the assumption survives as a number COMPUTED from it, not as a literal).
  Consequences, all measured: per-frame noise ~2.4× worse against fixed star
  flux; ~2.7× fewer stars detected (700 vs 1877); and **1030 moonlit frames
  FAILED to improve on 799 moonless frames** — a 7-member cross-session
  combine came out 29% WORSE in background-limited SNR than the moonless
  session alone, on a smaller frame. Moonlight also roughly doubles the
  autostretch's gradient amplification and the sky gradient the flat bakes
  in. There is no processing remedy; more integration is not one. Check moon
  phase and altitude when PLANNING, not after.
- Focus recalibration each session is STANDING PRACTICE, and the lens's
  distortion/field-curvature profile moves with it — the processing-side
  model authority is `scripts/darktable/lens_models.json` keyed
  `<lens>@<focal>`, with optical-state boundaries DETECTED, not assumed
  (`stacking-compose.md`); the BLUR half is acquisition's alone: if SINGLE
  frames measure corner-vs-centre FWHM elevation, that is field curvature no
  warp can fix — the refocus procedure is the lever, not processing.
- Lock the zoom ring (tape); don't touch the camera mid-set (a focal-length
  step forces a mixed-optics stack). Dither between subs; avoid the moon
  (star fringes on trailed PSFs are dispersion — physical, not removable in
  processing). Stop a fast lens down ≥1 stop for bright-star fields (wide
  open adds a red veiling-glare halo — an honest optical signature, not a
  bandaid to remove).

**LUNAR (small-disc lucky imaging) — the class block (first corpus
measured):**
- **Lossless-compressed NEF only** (HE/HE★ are TicoRAW — no libraw/open
  decode; a set shot HE is unprocessable on this stack). Electronic shutter
  is safe (9.3 ms readout smears 0.14″ at lunar drift) and shock-free — use
  it.
- **EXPOSE THE DISC: histogram peak 50–70%, never clip the highlands.** The
  measured miss: f/4 · 1/2500 s · ISO 800 at 70 mm put the disc median at
  ~4% of the 14-bit range — 2.5–3 stops under; the corrected card for that
  optic is **f/4 · 1/320 s · ISO 800**. At undersampled focal lengths
  EXPOSURE TIME is the free lever (drift 15″/s × 1/320 s ≈ 0.003 px at
  17″/px; seeing is sub-pixel — nothing to freeze): raise time, not ISO
  (gain adds no photons and burns headroom; ISO 800 already sits at the
  dual-gain stage). From ~800 mm at this pixel pitch seeing becomes
  resolved, the 1/500–1/1000 s freeze-floor returns, and ISO reluctantly
  becomes the second lever.
- Shoot darks at the LIGHTS' exact tuple in the same thermal window (the
  between-sets slot works); matched short darks ≈ bias + FPN and calibrate
  cleanly.
- Frame count buys selection depth: 1000+ frames/target at ~1 fps or bursts;
  keep fractions are a stack-time knob, never a capture-time one. Focus on
  the terminator in magnified live view; VR/IBIS off on a rigid tripod;
  moon > ~40° altitude; terminator phases carry the relief.
