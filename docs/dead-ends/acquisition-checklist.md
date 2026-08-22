# Acquisition checklist — the real quality lever

Phase-1 split of `docs/dead-ends.md` (organize-only; the original file stays
the live registry until the merge is decided). Content below the marker is
VERBATIM from the original, so in-text "above"/"below"/section references may
point at entries now homed in a sibling file — `README.md` in this directory
carries the index, the assignment rule, and the block manifest that resolves
them. Do not edit below the marker while the refactor is in phase 1; the split
is re-derivable from the manifest and verified byte-identical by `split.py`.

<!-- == verbatim content from docs/dead-ends.md below this marker == -->
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
- **DEW CONTROL (measured cost, july23: two of four sets excluded from the
  final combine).**
  A clear still humid night radiation-cools the lens below the dew point even
  in summer; the film NEVER self-clears and faint-star loss precedes the
  visible film. Run a low-power lens heater band from session START (2–3.4 W
  suffices for a camera lens; minimum power that prevents dew — excess heat
  makes convection/soft stars), riding the extended barrel; the 24-70's petal
  hood is sized for 24 mm and is weak protection at 70 mm; a small fan works
  where a band is absent. Watch the brightest star's halo live and flashlight
  the front element when in doubt; if dew is found, warm and continue — never
  stack through it (a contiguous dewed block is NOT rejectable per-pixel; the
  cull is by frame, post-hoc identifiable by the halo/FWHM/nstars timeline —
  mean-based star-box-minus-flanks ministacks + the frame-QA trends, numbers in
  the halo-photometry entry above).
- **VERIFY FOCUS ON THE FIRST FEW FRAMES, then leave it alone — and if you must
  refocus, do it AT A SET BOUNDARY, never mid-set.** MEASURED on one session: the
  first 149 frames ran 9% soft (registration FWHM 2.944 px vs 2.680 achievable)
  and the deficit was present in frame ONE at 2.910 — the lens was never focused,
  not drifting out of focus. A mid-set correction then cost 205 s of pause, three
  handling-ruined frames, and a 1.2 deg re-aim that split the set into two
  pointing swaths — forcing a 152-frame block exclusion, a separate flat, and a
  smaller min-framing intersection for every product that set entered. The same
  correction 15 min later at the set boundary (where a re-aim pause already
  happens) would have cost nothing. Post-correction focus then held for 90+ min:
  the apparent later "drift" (2.672 -> 2.797 -> 2.730 px) REVERSED with nothing
  touched, so it was seeing, not focus — periodic refocusing was not supported by
  the data, and the per-set QA FWHM is the self-check that would show a real
  drift. Cheap check up front: shoot a handful, read the frame-QA FWHM/star
  counts, fix it then.
- **DO NOT SHOOT A FAINT BROADBAND TARGET UNDER HEAVY MOONLIGHT — measured, the
  integration does not buy it back.** A 98%-lit moon 24 deg up, 72 deg off the
  field, raised the sky **4.2x** against a moonless night at the SAME hour on the
  same rig (single raw frames, matched to 3 s of clock time: R/G/B 116/219/166 ADU
  above pedestal vs 27/52/40 — **PEDESTAL UNSTATED, and that makes the 4.2× ratio
  uncheckable rather than wrong: it is 219/52, so it is SENSITIVE to the reference.
  The sensor pedestal is now MEASURED at 1007.2 ADU (`TOOLS.md`); if these figures
  used the 1024 that was assumed elsewhere, both are understated by 16.8 and the
  true ratio is (219+16.8)/(52+16.8) = 3.43, a 23% overstatement. If they used the
  correct reference, 4.2× stands. Nobody can tell, which is the defect.** Weak
  hint in the figures' favour and offered as a hint only, since inferring the input
  from the tidiness of the output is backwards: a 16.8 error would generally break
  the R/G 0.53-vs-0.52 agreement below, and it does not.
  **THE RULE THIS COSTS: any figure quoted "above pedestal", "above background",
  "above bias" or "net of" MUST state its denominator** — the offset form of the
  register's state-the-denominator rule for counts, and the same discipline the
  cloud record carries. A literal grep for the assumed value cannot find this class:
  the assumption does not survive as a literal, it survives as a number COMPUTED
  from it; the excess is colour-NEUTRAL — R/G 0.53 vs 0.52,
  B/G 0.75 vs 0.77 — which is what identifies moonlight rather than a light
  dome). Consequences, all measured: per-frame noise ~2.4x worse against fixed
  star flux; ~2.7x fewer stars detected per frame (700 vs 1877); and **1030
  moonlit frames FAILED to improve on 799 moonless frames** — a 7-member
  cross-session combine came out **29% WORSE** in background-limited SNR than the
  moonless session alone, and on a smaller frame. Moonlight also worsens the two
  display/calibration defects above: it doubles the autostretch's gradient
  amplification (17x vs 8.7x) and roughly doubles the sky gradient the flat bakes
  in. There is no processing remedy; more integration is not one. Check moon
  phase and altitude when PLANNING, not after.
- Focus recalibration each session is STANDING PRACTICE, and the lens's
  distortion/field-curvature profile moves with it — so the processing-side
  model is per optical state (BACKLOG:`optical-state-models`), and the
  BLUR half is acquisition's alone: if SINGLE frames measure corner-vs-centre
  FWHM elevation, that is field curvature no warp can fix — the refocus
  procedure is the lever, not processing.
- Lock the zoom ring (tape); don't touch the camera mid-set (a focal-length step
  forces a mixed-optics stack). Dither between subs; avoid the moon (star fringes
  on trailed PSFs are dispersion — physical, not removable in processing). Stop a
  fast lens down ≥1 stop for bright-star fields (wide open adds a red veiling-glare
  halo — an honest optical signature, not a bandaid to remove).

**LUNAR (small-disc lucky imaging) — the class block (first corpus measured):**
- **Lossless-compressed NEF only** (HE/HE★ are TicoRAW — no libraw/open decode; a
  set shot HE is unprocessable on this stack). Electronic shutter is safe (9.3 ms
  readout smears 0.14″ at lunar drift) and shock-free — use it.
- **EXPOSE THE DISC: histogram peak 50–70%, never clip the highlands.** The
  measured miss: f/4 · 1/2500 s · ISO 800 at 70 mm put the disc median at ~4% of
  the 14-bit range (peak ~9%) — 2.5–3 stops under; the corrected card for that
  optic is **f/4 · 1/320 s · ISO 800**. At undersampled focal lengths EXPOSURE
  TIME is the free lever (drift 15″/s × 1/320 s ≈ 0.003 px at 17″/px; seeing is
  sub-pixel — nothing to freeze): raise time, not ISO (gain adds no photons and
  burns headroom; ISO 800 already sits at the dual-gain stage). From ~800 mm at
  this pixel pitch seeing becomes resolved, the 1/500–1/1000 s freeze-floor
  returns, and ISO reluctantly becomes the second lever.
- Shoot darks at the LIGHTS' exact tuple in the same thermal window (the between-
  sets slot works); matched short darks ≈ bias + FPN and calibrate cleanly.
- Frame count buys selection depth: 1000+ frames/target at ~1 fps or bursts; keep
  fractions are a stack-time knob, never a capture-time one. Focus on the
  terminator in magnified live view; VR/IBIS off on a rigid tripod; moon > ~40°
  altitude; terminator phases carry the relief.
