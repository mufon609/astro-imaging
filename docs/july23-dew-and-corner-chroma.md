# july23 session anomalies: lens dew signature + radial corner chroma — deep dive

- **Question / scope** — Two user-caught anomalies in the july23 NAN session
  (4×~400×3 s, Z6III + 24-70/4 S @ 70 mm f/4, fixed tripod, flatless →
  per-set sky flats): (A) a large circular glow around Deneb in set-04 — user
  field call: **dew on the lens**; assess whether set-04 (or more) must be
  dropped, and leave notes future sessions can act on. (B) ALL july23
  products show corners chroma-shifted red vs centre while july14's final
  (same rig, same field, same chain) is corner-neutral — why. This doc holds
  the measured record, the discrimination logic, and the open tests. It
  exists because the first-pass attributions were made WITHOUT discriminating
  tests and two were wrong (registry entries; MEMORY correction).
- **Context** — 2026-07-26. Siril 1.4.4 flatpak, 32-bit float chain
  (post-rebuild), local astrometry.net. Session wall-clock 00:40–02:31 EDT
  2026-07-24; darks shot immediately after (02:33+). All pixel measurements
  Siril `stat` (means AND medians recorded); star positions via the per-set
  endpoint solves, linearly interpolated; every number's record is under
  `datasets/july23/` (copies of `sessions/july23/work/dewprobe/`).

## Part A — the Deneb glow: measured timeline

**Instrument.** Nine 16-frame UN-registered mean ministacks spanning the
session (raw frames, debayered, no calibration — pedestal and fixed
vignetting cancel in the differential). On each: 260 px box on Deneb and on
γ Cyg, each minus the mean of two flanking sky boxes ±700 px. MEANS, not
medians — a broad faint halo is invisible to a median (that error produced
the earlier false "constant halo" reading; dead-ends entry).

**Deneb halo, G channel (star-box minus flanks, ADU):**

| time (EDT) | point | halo G | note |
|---|---|---|---|
| 00:41 | set-01 early | 6.25 | session start, ~40 min after end of twilight |
| 01:05 | set-01 late | 7.55 | +21% within set-01 |
| 01:21 | set-02 mid | 7.65 | |
| 01:34 | set-02 late | 7.70 | plateau segment |
| 01:49 | set-03 mid | 8.45 | |
| 02:01 | set-03 late | 10.30 | +22% within set-03 |
| 02:05 | set-04 early | 7.05 | re-aim; flank geometry shifts the baseline |
| 02:18 | set-04 mid | 9.85 | |
| 02:30 | set-04 late | 11.95 | **+69% within set-04; +91% over the session** |

R and B channels scale together with G (R 4.05→6.65, B 5.45→10.6). γ Cyg's
box difference stays flat (~6.5–8.6, no trend) — but γ Cyg sits inside the
IC 1318 nebulosity, so its differential is dominated by static real emission;
it is NOT a clean second-star control (limitation; a cleaner control star
would sit on plain sky — none of comparable brightness is in-frame).

**Corroborating session curves** (Siril register regdata, 24 QA blocks,
`transparency_curve.json`):

- FWHM: **monotonic rise 2.627 → 2.72 px** (+3.4%) across the night, never
  recovering.
- nstars: stable ~1875 until set-04, then the terminal crash −13–16%
  (frames 0231–0250, the last ~20 min).
- Background: falls 1068 → 1057 (sky darkening — consistent with the 75%
  moon sinking; see Part B).
- CameraTemperature EXIF: not recorded by the Z6III on these frames
  (checked); no on-rig ambient/lens temperature exists. LIMITATION: the
  dew-point crossing cannot be confirmed from EXIF — only the optical
  signature speaks.

**Discrimination table (mechanism → prediction → what the data says):**

| mechanism | prediction | verdict on this data |
|---|---|---|
| dew film forming on the front element | halo around the brightest star GROWS monotonically, accelerating as the lens cools; FWHM creeps up; faint-star counts fall late; does not self-clear | **consistent on every axis** (halo +91% accelerating; FWHM monotonic; terminal nstars crash) — leading attribution (also the user's field call) |
| thin high cloud | patchy, non-monotonic; whole-sky; would show in mid-session blocks too | inconsistent — growth is smooth and monotonic; nstars stable until the very end |
| constant optical glare (lens signature) | halo constant all night | **refuted** — halo doubles |
| internal-reflection ghost | geometry keyed to star-vs-axis position; jumps at re-aims | inconsistent — survives four re-aims growing; the small T7 step is flank-baseline, not a ghost jump |
| focus drift | FWHM rise without a halo | explains neither the halo nor the crash |

**Status: dew = leading, strongly supported HYPOTHESIS** (growth pattern +
conditions + user field knowledge). Not proven to the exclusion of every
fogging variant (front element vs rear vs sensor window can't be separated
post-hoc from these frames); for the decision at hand they are equivalent.

**What it costs the data (measured on the 32-bit finals):** set-04 R-channel
NAN contrast 15.1% of sky vs set-02's 19.4% (the veil scatters signal into
sky); the Deneb disc residual after flat division +2.5/+5.8/+10 ADU
(set-04) vs 0/0/0 (sets 01–02); set-03's tail is already elevated (halo
10.3 at 02:01, contrast 17.4% vs 19.4%).

**Options for the user (nothing auto-proceeds):**
1. **Drop set-04 from the combine** → 1199-frame combine (−25% frames,
   ×0.87 SNR): removes the visible disc and the strongest veiling.
2. **Drop set-04 AND set-03's last ~2 blocks** (frames ≳9752) → ~1050
   frames: also removes the elevated set-03 tail.
3. **Keep set-04 with the declared caveat** (disc stays; veil cost stands).
Per-set stacks stay preserved regardless; only the combine re-composes
(~30 min).

**For future sessions (acquisition-side, graduates to the checklist when
ratified):** the signature to watch live is the bright-star halo; a dew
heater band / USB lens warmer (or at minimum a deep hood + periodic
flashlight check across the front element) is the fix; late-session sets on
humid nights are the risk window; if dew is found mid-session, warming and
continuing beats stacking through it — the affected tail is identifiable
post-hoc by exactly the timeline above (mean-based halo curve + FWHM +
nstars), which any future session can rerun from `dewprobe/`.

## Part B — the radial corner chroma: measured, mechanism OPEN

**The objective gradient (Siril stat medians on the LINEAR SPCC stacks;
corner (R/G) and (B/G) relative to centre):**

| stack | worst corner R/G shift | all-corner range | B/G range |
|---|---|---|---|
| july14 set-01 (369×6 s, NEW MOON) | **+0.9%** | 1.000–1.009 | 1.000–1.009 |
| july23 set-01 | +5.6% (TR) | 1.044–1.056 | 1.006–1.013 |
| july23 set-02 | +6.4% (TR) | 1.049–1.064 | 1.018–1.026 |
| july23 set-03 | +7.2% (TR) | 1.047–1.072 | 1.016–1.031 |
| july23 set-04 | +7.2% (TR) | 1.037–1.072 | 1.018–1.031 |
| july23 combine | +6.5% (TR) | 1.041–1.065 | 1.011–1.027 |

Every july23 product carries a 4–7% red shift in ALL FOUR corners (radial
term) plus a TR-weighted asymmetry (one-sided term); july14 is neutral to
0.9%. The user's eye was right, on every surface.

**The one measured global difference between the sessions: the moon.**
Astropy ephemeris (geocentric — observer location unknown, so phase and
field separation only): july14 session **1% illuminated** (new moon, 11°
elongation, below any practical horizon); july23 session **75% illuminated
waning gibbous**, 95–96° from the field, up during the whole run (the
falling sky background 1068→1057 is consistent with it sinking). A moonlit
sky is brighter, bluer in scatter, and carries a strong directional
gradient; a moonless sky is faint airglow + LP.

**The flats themselves carry session-specific structure (measured,
`split_cfa` per-Bayer-plane regional medians):** july23's flats are
LEFT/RIGHT asymmetric (TR corner deepest: TL≈0.52–0.61 vs TR≈0.46–0.51 of
centre) and the asymmetry GROWS set-to-set (set-01 TR 0.488 → set-04 TR
0.460) — a one-sided sky/scatter term baked into each flat, drifting
through the night, exactly where the stacks' TR-weighted chroma asymmetry
sits. july14's flat is asymmetric the OPPOSITE way (TL deepest 0.43 vs
TR/BR 0.58–0.64). This re-measures the registry's "a flat's low-order term
carries its source sky" mechanism per-channel, on real flats.

**Why the radial red term is NOT simple lens color shading:** same lens,
same f-stop, same chain on july14 renders neutral — pure static color
shading would show both nights. The residual is session-specific.

**Candidate mechanisms (hypotheses — each with its discriminating test;
NONE adopted):**

- **H1 — additive scattered components break the sky flat's multiplicative
  self-cancellation.** A lights-built flat cancels sky×vignetting exactly
  only while the frame content is multiplicative and stationary. july23 adds
  two ADDITIVE, TIME-VARYING glows: moonlight scatter (setting moon;
  gradient drifting) and the growing dew veil (Part A). Division by the
  median-of-lights then mis-corrects every frame by the difference between
  its instantaneous additive term and the median's, leaving a radial +
  one-sided colored residual. Predicts: corner chroma grows with the dew
  curve set-over-set (measured: TR R/G 1.056 → 1.064 → 1.072 → 1.072,
  matching until the plateau) and vanishes on a moonless dew-free night.
  TESTS: (a) next moonless session, identical chain → corners should read
  ≤1% like july14; (b) one set re-calibrated with a flat built from its
  FIRST 100 frames vs its LAST 100 — if the residual moves with the flat's
  time window, the time-varying additive term is implicated; both are
  one-knob cheap.
- **H2 — differential extinction / moon-dome gradient (one-sided
  contributors).** Cannot produce the all-corner radial term; can drive the
  TR asymmetry. TEST: the TR excess should track the field's orientation to
  the moon azimuth across the four re-aims; computable once observer
  location is declared (open input).
- **H3 — SPCC's spatial blindness (background offsets are global).**
  Not a cause but an amplifier: SPCC neutralizes the CENTRE (K factors from
  stars + global bg offsets), so any spatially varying colored residual is
  pushed entirely into the corners. No test needed — mechanism is
  documented tool behavior; the fix layer is the render tier's per-channel
  background extraction (item 0), which is where the corners get equalized
  in the standard workflow regardless of which upstream mechanism made them.
- **H4 — bit-depth or chain regression.** Refuted for the radial term: the
  32-bit rebuild carries the same corner chroma as the 16-bit run; july14's
  neutral render came through the same finish stage.

**Status: Part B mechanism OPEN.** The measured facts are the gradient
table, the flats' asymmetry, and the moon difference; H1 is the leading
candidate with two cheap pre-registered tests; no attribution is claimed
until one runs.

## Sources

- Repo records: `datasets/july23/dew_chroma/` (measurements.json — halo
  timeline, flat planes, stack chroma; session_timeline_exif.json;
  transparency_curve.json), `datasets/july23/set-0N/qa_work/frame_metrics.json`,
  `datasets/july23/snr_nan_regions_32bit.json`, july14 masters + SPCC stack.
- Astropy 8.0.1 ephemeris (geocentric moon; location-free approximation).
- _Sourced background (dew phenomenology, color shading, moonlight sky
  color, salvage practice) — research sweep in flight; merges here with
  citations when it lands._

## Verdict / recommendation

Part A: dew (or an equivalent progressive lens fog) is the leading,
multi-axis-supported attribution for the set-04 disc; the set-04 decision is
the user's — options quantified above. Part B: the corner chroma is real,
measured, session-specific, and moon/dew-correlated; adopt nothing until the
H1 tests run; the render tier's background extraction is the standard
downstream equalizer either way.

## Status

Part A: MEASURED timeline + discrimination; attribution = strong hypothesis
(field-confirmed class, not lab-proven). Part B: gradient MEASURED;
mechanism PROVISIONAL/OPEN with pre-registered tests.

## Graduation

- dead-ends: median-vs-mean halo photometry trap + two-point-control trap
  (landed); the earlier glare×flat entry rewritten in place.
- MEMORY.md: the "guessing with conviction" correction (landed).
- BACKLOG: set-04 combine decision (user-gated); H1 flat-window A/B; the
  moonlit-night sky-flat limitation as a class caveat on the flatless route.
- Acquisition checklist: dew control line — pending ratification after the
  research sweep merges.
