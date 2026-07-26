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

**Sourced background (research sweep, 2026-07-26) — the community/optics
record matches the measured fingerprint:**
- Signature: "dim stars and galaxies harder to see, and bright stars develop
  fuzzy halos" (Sky & Telescope, dealing-with-dew); "the faint stuff in
  images can be affected well before you can actually see dew on the lens"
  (Lodriguss, astropix.com BGDA ch.2) — faint-star loss precedes the visible
  halo, exactly our nstars-crash-after-halo-growth ordering.
- Mechanism/time course: optics radiate to a clear sky and drop below the
  dew point even with air above it (skyatnightmagazine; blackwaterskies.co.uk
  — Dp ≈ T − (100−RH)/5); still air + humidity + clear sky are the worst
  case; NO source describes self-clearing — monotonic growth to session end
  unless heated. Wiping is futile (re-fogs in minutes; hair-dryer rescue
  repeats ~every 20 min).
- Scatter color: water droplets are Mie scatterers — wavelength-neutral
  (Britannica/NOAA cloud-color refs) — so the halo takes the color of star +
  ambient sky ("white" halos, Cloudy Nights 358932). Our halo's near-neutral
  RGB ratios are consistent.
- Salvage practice: cull the tail BY FRAME (blink + star-count/HFR/
  background trends; "best-X%" conventions); sigma rejection tolerates only
  a small fraction of soft frames and CANNOT remove a halo present in a
  contiguous block — within the block it is not an outlier (CN 517557,
  869299, 946505). No universal numeric threshold exists anywhere found —
  the trend curves + eyes are the standard, which is what this repo's
  timeline instrument now provides reproducibly.

**For future sessions (acquisition-side; checklist line graduated to
`docs/dead-ends.md`):** watch the bright-star halo live and check the front
element with a flashlight when in doubt (S&T); a low-power lens heater band
is the fix — 2–3.4 W is enough for a camera lens (philhart.com; Dew-Not/
Kendrick 2″), minimum power that prevents dew (excess heat = convection/soft
stars, CN 643667), on from session START, riding the extended barrel of the
retractable 24-70; the petal hood is sized for 24 mm and is weak protection
at 70 mm (1.5×-aperture guideline); moving air (small 12 V fan) is an
effective alternative (photographingspace.com); if dew is found mid-session,
warm and continue — do not stack through it. Post-hoc, any future session
re-runs the timeline instrument from `dewprobe/` as-is.

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

**RESOLVED 2026-07-26 (the warp-leg ICC fix — BACKLOG item 20): the shipped
corner chroma was CHAIN-INJECTED, level-dependently.** One knob (the float
TIFF leg: ICC tag stripped + LIN_REC709 export, measured identity 1.0000 at
all levels) and the rebuilt stacks read corners **R/G 1.008–1.018 —
july14-class neutral** (pre-fix 1.041–1.072), with the SPCC K family
collapsing to G 0.662–0.668 across all four products (per-set scatter 0.006
vs ~0.03 before). The level-dependence resolves the "identical chain,
different outputs" paradox that misled the earlier localization: the toe
error lives below linear ≈0.003, so july14's 6 s sky passed above it while
july23's 3 s sky sat inside it — same scripts, different injection. The
paragraph below records the earlier localization AS SUPERSEDED: its
raw-level session delta is real but self-cancels through the flat (as
division guarantees); its "chain-faithful" conclusion was wrong because the
chain's defect hid exactly where the two-session comparison could not
separate it from data. The surviving lesson: a level-dependent chain defect
DEFEATS same-chain/different-data controls — only the identity round-trip
instrument at the class's own sky level isolates it.

_Superseded localization (kept for the record):_ Two independent raw-level artifacts agree: (1) each session's
sky flat IS a dark-subtracted stack of its raw lights — per-CFA-plane
corner/centre gives july14 raw sky corners R/G **0.96–0.97** (blue-lean)
vs july23 **1.02–1.03** (red-lean): a ~5–6-point session delta at the RAW
stage, matching the finals' delta (≤1.009 vs 1.044–1.072); (2) the nine
pedestal-subtracted ministacks show july23's corner R/G **stable all night**
(~1.00–1.05, bottom corners strongest, no growth) — so the corner-red is
NOT dew-driven, NOT flat-created, NOT chain-created (the 16-bit-era chain
rendered july14 neutral and july23 red-cornered in the same two days with
identical scripts), and the user has ruled out the moon from field
knowledge. It is a stable spatial-chroma property of that night's raw sky
light, which the chain carries faithfully to the finals. WHY that night's
sky read corner-red is deliberately left unattributed — no discriminating
test exists in this data.

**What remains true and actionable (user field knowledge + doctrine):** The user has seen many stacks — july14-class included — originally
render with exactly this corner residual and get FIXED downstream. That
matches industry doctrine precisely: the standard post-stack order (Siril's
own: crop → BACKGROUND EXTRACTION → photometric colour → stretch; PI: DBE/
GradientCorrection before colour work) runs a background/gradient-removal
stage that our chain DOES NOT HAVE — the render tier (BACKLOG item 0) is
unbuilt, so every judgment surface ships straight from SPCC to a diagnostic
stretch with the background gradient still in it. SPCC then amplifies the
visibility: it neutralizes the CENTRE globally (K factors + global bg
offsets), pushing the whole spatial colour residual into the corners.
**The operative question is not "which sky term coloured the corners" but
"why is the judgment surface rendered without the standard stage that
removes it".** july14's near-neutral pre-BGE state (new moon, weak
gradient) was the lucky case, not the norm.

Secondary mechanism notes (kept for the record, demoted from "leading";
research-sweep citations merged):
- The additive scattered components (moon + the growing dew veil) plausibly
  explain why july23's PRE-BGE gradient is larger than july14's (flat
  self-cancellation breaks on additive, time-varying terms; corner chroma
  tracks the dew curve set-over-set: TR R/G 1.056→1.064→1.072→1.072).
  Ephemeris correction: the Jul 23/24 moon was a **waxing** gibbous
  (~70–82%, 9–10 days past new; new moon fell ON Jul 14 — moongiant/
  astronomy.com), low in the SOUTH and setting ~1 AM local (astronomy.com
  Jul-24 sky column, 40°N ref) — i.e. it SET during our session, consistent
  with the measured falling background 1068→1057 and set-01's brighter sky.
  Patat 2003 (A&A 400,1183): a ~10-day moon brightens B ~3 mag vs I ~1.2 —
  the moonlit sky is strongly BLUER while the dark sky is airglow-red;
  a lights-built flat inherits whichever sky built it (MaxIm DL sky-flat
  doc: the flat replicates "the illumination pattern AND spectrum" of the
  session). Optional cheap test if ever needed: first-100 vs last-100 flat.
- Color shading context (why corners amplify): CFA/microlens transmission is
  incidence-angle-dependent (CRA mismatch → radial pink/magenta casts —
  commonlands/edge-ai-vision; Z-mount permits ~44° corner rays vs F-mount
  12° — photographylife) and the 24-70/4 S measures ~2.4 EV corner falloff
  at 70 mm (OpticalLimits) — corner pixels are multiplied ~5× by ANY flat,
  so small per-channel flat errors become large corner chroma. No published
  per-channel curves or corner-cast reports exist for this lens (open).
  Tooling facts: lensfun models vignetting single-channel only and darktable
  has no GainMap/color-shading support (darktable FR #8728); Siril
  `-equalize_cfa` is a global per-channel scalar from a CENTRE region — no
  spatial per-channel equalization exists in the chain's tools. The standard
  industry answer to residual spatial colour is exactly the background
  stage (gradient removal before colour calibration — Siril docs order;
  PI ecosystem doctrine), which is divergence #1 above.
- Differential extinction / moon-dome: one-sided contributors only (the TR
  asymmetry; computed ≈0.07 mag B−V per 0.5 airmass across the field —
  percent-level), cannot make the radial term.
- Bit depth: refuted (32-bit carries the same chroma as 16-bit).
- SPCC (sourced): "The correction is globally uniform across the entire
  image, not spatially varying" (siril docs, spcc page) — it can neither
  create nor fix the spatial pattern; structure must pre-exist upstream.

**The conventional fix, MEASURED on this data (exp_subsky1, 2026-07-26) —
it decomposes the residual instead of erasing it:** `subsky 1` (the
registry's MW-safe first-degree plane) on the re-composed 3-set combine
removed the ONE-SIDED term — TR 1.070 → 1.057 with all corners converging
to a uniform ~5.5% — at zero structure cost (NAN contrast identical,
7.17/6.61/7.57 both arms: dust-safe NULL). What remains is a pure RADIAL
~5% R/G term a plane structurally cannot touch. So the corner residual =
(one-sided sky gradient — background-stage-correctable, dust-safe) +
(radial per-channel calibration residue — NOT correctable by any
background model this MW-filling class tolerates: the registry's measured
limits say degree ≥2 erases the MW band and full-model BGE absorbs
frame-filling nebulosity). The radial term's signature matches the
per-channel flat-error class amplified ~5× at the 2.4 EV corners; its
industry-standard fix is UPSTREAM — real per-channel flats at acquisition
(the checklist's primary path) — and july14's neutrality reads as a
self-consistent flat on a stable-colour new-moon sky rather than a
different chain. Ledger: `datasets/july23/experiments.jsonl`; like-encoded
pair in `web/results/july23/exp_subsky1_20260726/` for the user's eyes.

## Sources

- Repo records: `datasets/july23/dew_chroma/` (measurements.json — halo
  timeline, flat planes, stack chroma; session_timeline_exif.json;
  transparency_curve.json), `datasets/july23/set-0N/qa_work/frame_metrics.json`,
  `datasets/july23/snr_nan_regions_32bit.json`, july14 masters + SPCC stack.
- Astropy 8.0.1 ephemeris (geocentric moon; location-free approximation) +
  moongiant.com/astronomy.com phase pages (new moon Jul 14 2026; waxing
  gibbous ~70–82% Jul 23/24, moonset ~1 AM local at the 40°N reference).
- Dew: skyandtelescope.org dealing-with-dew · astropix.com BGDA ch.2 ·
  skyatnightmagazine.com how-stop-dew (+ DIY heater page) ·
  blackwaterskies.co.uk dew-formation-and-prevention (dew-point formula) ·
  ayton.id.au Ast_dew · photographingspace.com dew-proofing ·
  philhart.com dew-heaters (2–3.4 W lens bands) · astrobackyard.com
  dew-heaters · highpointscientific.com how-to-stop-dew · Cloudy Nights
  358932 (white halos), 643667 (over-heated band), 517557/869299 (soft-frame
  fraction under rejection), 946505 (star-count culling), 838843 (trend
  monitoring) · iceinspace.com.au 122853 (bloat causes) ·
  opticalmechanics.com seeing-vs-transparency (cirrus halos/photometry) ·
  nightskypix.com condensation (sensor-window vs lens) · Britannica/NOAA
  Mie/cloud-color (wavelength-neutral droplet scatter).
- Colour/gradient: Patat 2003 A&A 400,1183 (astro-ph/0301115 §7 — moonlit B
  +3 mag vs I +1.2) · Krisciunas & Schaefer 1991 PASP 103,1033 (moonlight
  model) · clarkvision.com natural night-sky colour (airglow red/green; LP
  orange; moonlit-blue MW) · MaxIm DL sky-flats doc (flat carries the sky's
  spectrum) · CN 755356/463798 (twilight-flat colour) · CN 801978 (flat
  over-correction at corners) · commonlands.com CRA + edge-ai-vision (CFA
  angle sensitivity) · patents US20070030379A1 (microlens CRA shift) ·
  photographylife.com Z-vs-F mount (44° vs 12° corner rays) · opticallimits
  24-70/4 S review (2.4 EV corner falloff @70) · rawpedia Flat-Field +
  Adobe LR flat-field (per-channel flat correction) · darktable issue #8728
  (no GainMap/colour-shading support; lensfun single-channel) ·
  siril.readthedocs spcc ("globally uniform… not spatially varying"),
  calibration (-equalize_cfa centre-region global scalars), background +
  siril.org gradient tutorial (BGE before colour; degree-1 per-sub for
  rotating gradients) · vikdhillon phy217 + UCSB deepspace ch.6 (extinction
  coefficients) · stirlingastrophoto multiscale-gradient-correction (PI
  doctrine: colour calibration after gradient correction).

## Verdict / recommendation

Part A: dew (or an equivalent progressive lens fog) — multi-axis-supported;
**USER DECIDED 2026-07-26: set-04 dropped from the combine, set-03's tail
(9752–9848) culled via recipe; per-set products preserved**
(`datasets/july23/combine_decision.json`). Part B, per user field knowledge:
the corner chroma is the normal pre-BGE state; the actionable divergence is
the chain's missing background-extraction stage (render tier, item 0) — the
`subsky 1` probe measures the conventional fix on this data; the moon/dew
terms remain only as notes on why this session's pre-BGE gradient ran large.

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
