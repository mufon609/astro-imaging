# Stacking chain vs official pipelines (Siril doctrine + WBPP reference) — deep dive

- **Question / scope** — How far does the repo's stacking chain (calibrate →
  [undistort] → register → stack) diverge from what the tool vendors themselves
  prescribe: Siril's own official doctrine (docs + shipped scripts + team
  statements) and PixInsight WBPP as the industry reference — audited
  stage-by-stage, with the july23 4-set run (North America Nebula field) as the
  live test case. This is the standing re-verification README's
  reference-standard table requires, run as its own investigation.
- **Context** — 2026-07-25. Siril **1.4.4 stable is current** (released
  2026-06-17; 1.5.0 is dev-only — verified from siril.org). Rig: x86-64 Kali,
  28 threads, 31 GB, no GPU, flatpak Siril, headless throughout. Test data:
  july23 — Nikon Z6III + 24-70/4 S @ 70 mm, 4 sets × ~400 × 3 s ISO 1600,
  fixed tripod (declared + solve-confirmed: RA advances at the sidereal rate,
  Dec constant to 0.03°/set), flatless by acquisition, 211 matched darks.
  Every doctrine claim below carries its source; repo-side numbers cite the
  tracked records.

## Findings

### A. The official Siril 1.4.4 chain (primary sources)

Current stable: 1.4.4 (2026-06-17). The canonical `OSC_Preprocessing.ssf`
(ships in `gitlab.com/free-astro/siril` at tag 1.4.4; header "Preprocessing
v1.4") runs exactly:

```
stack bias rej 3 3 -nonorm -out=../masters/bias_stacked
calibrate flat -bias=../masters/bias_stacked
stack pp_flat rej 3 3 -norm=mul -out=../masters/pp_flat_stacked
stack dark rej 3 3 -nonorm -out=../masters/dark_stacked
calibrate light -dark=../masters/dark_stacked -flat=../masters/pp_flat_stacked
          -cc=dark -cfa -equalize_cfa -debayer
register pp_light                       # one pass, homography, lanczos4+clamp
stack r_pp_light rej 3 3 -norm=addscale -output_norm -rgb_equal -32b -out=result
```

No plate solve, no SPCC, no quality culls in the official script — the chain
ends at the linear 32-bit stack. Doctrine highlights (docs =
siril.readthedocs.io/en/stable; scripts = free-astro/siril + siril-scripts):

- **Calibration formula is (L − D)/(F − O)**: bias calibrates the FLAT only;
  lights get matched dark + flat (the dark carries the bias). Darks: same
  exposure/ISO, "approximately the same temperature ... this is the reason we
  make dark frames at the end, or in the middle of the imaging session"
  (calibration.html). FAQ adds: for non-cooled cameras over long sessions "the
  correct way ... is to use dark optimisation" (`-opt`, bias-calibrated darks).
- **No flats shot → official answer is to SKIP flat division entirely**
  (`OSC_Preprocessing_WithoutFlat.ssf`; FAQ "I don't have flats"). No official
  source endorses or rejects building a flat from the lights themselves
  (absence of doctrine, searched docs/FAQ/blog/forums).
- **Cosmetic correction**: script uses bare `-cc=dark` = hot-only σ3;
  `-cc=dark 3 3` (docs) adds cold-pixel correction.
- **Registration**: homography is default and "strongly recommended for
  wide-field images"; `-2pass` is the docs' own better-reference improvement
  (compute transforms first, then `seqapplyreg`); lanczos4 + clamping default.
  **Lens distortion is now handled natively**: platesolve fits SIP (default
  Cubic, to order 5 — "Unless you have a perfectly optically flat field, it is
  usualy a good idea to platesolve using SIP") and `register -disto=image|
  file|master` applies it, correcting star positions before the fit and
  composing undistort+projection into ONE resampling at export
  (registration.html; the DSA script in the official repo is the worked
  example). 1.4 also drives local astrometry.net blind solves natively
  (`platesolve -localasnet -blindpos -blindres`).
- **Stacking**: rejection by sub count — percentile "ideal for small sets (up
  to 6 images)"; GESD "excellent performances with large dataset of more 50
  images" (parameters are outlier FRACTION + SIGNIFICANCE — Siril's own GUI
  defaults 0.3/0.05, from `src/gui/stacking.c`); winsorized 3/3 is the factory
  default between; linear-fit for "large stacks and images containing sky
  gradients with differing spatial distributions". Lights normalize
  additive+scaling (default), `-output_norm` rescales the result; flats
  `-norm=mul`; masters `-nonorm`. `-rgb_equal` is conditioned by the command
  reference on SPCC/PCC NOT being used later. Weighting: factory `NO_WEIGHT`,
  no official script uses `-weight=`, docs prescribe nothing.
- **Bit depth**: 32-bit default; "a 16-bit stacking can lose a lot of
  information" (preferences_gui.html); official scripts pin `-32b`.
- **Quality filtering**: official scripts cull nothing; FAQ offers
  `-filter-fwhm=75%` only as an optional user tweak.
- **Color**: SPCC mandatory on the linear, plate-solved stack; official
  post-stack order: crop → background extraction → photometric colour →
  deconv → stretch → SCNR → saturation → export. For OSC colour the SPCC page
  recommends the Bayer-drizzle variant ("Drizzle provides a significant
  improvement over debayering").

### B. Stage-by-stage: our chain vs Siril doctrine

Our chain = `run_undistort_pipeline.sh` (wide-field untracked class) with
per-set sky flats (`build_sky_flat.sh`), as run on july23.

| stage | official Siril doctrine | our chain | verdict |
|---|---|---|---|
| master dark | `stack dark rej 3 3 -nonorm`, matched exp/ISO, same-session temperature | identical, 211 matched darks shot immediately after the last light (02:33), 2 exposure-strays excluded by EXIF match | **MATCH** |
| bias | on flats only; lights never (dark carries it) | no bias anywhere; sky-flat inputs are dark-subtracted (offset leaves via the dark), flat denominator therefore pedestal-free | **MATCH in intent** — mechanism differs, recorded |
| dark optimization | skip for matched darks; FAQ recommends `-opt` for uncooled cameras | not used — darks are same-night, shot at session-end temperature | **MATCH (base doctrine)**; FAQ fork noted → named test below |
| flat | real flats; if none shot, official answer = no flat at all | per-set sky flat from the set's own lights (mul-norm, winsorized), validation-gated (regional falloff, 0 specks, preview eye check) | **DIVERGENCE (documented adaptation)** — official alternative leaves ~2× corner falloff uncorrected with no native multiplicative fixer (`subsky` is subtraction-only); no official position exists on light-built flats; removal condition = a real matching flat |
| light calibrate | `-dark -cc=dark -cfa -equalize_cfa -debayer` | `-dark -cc=dark 3 3 -flat=<skyflat> -equalize_cfa -cfa -debayer` | **MATCH+** (adds documented cold-pixel side; `-cc=dark` is mandatory repo-wide — walking-noise lesson) |
| debayer timing | calibrate CFA, debayer after | identical | **MATCH** (Bayer-drizzle colour variant noted below) |
| undistort | native: SIP platesolve + `register -disto=` | darktable + lensfun model FITTED from the set's own frames, warped before registration | **DIVERGENCE (measured adaptation)** — astrometry.net per-frame SIP at this field scale is a measured LOSS (majFWHM 4.74→6.02 px, dead-ends registry); Siril-native SIP from its own solver is UNTESTED on this class and is the fitted model's written removal condition → named test below |
| register | homography; `-2pass` documented improvement; official script 1-pass | `register -2pass` + `seqapplyreg -framing=min` | **MATCH (docs-side)**; `-framing=min` is documented, neutral; 2-pass beats script default per docs' own rationale |
| rejection | ≤6 percentile; >50 GESD 0.3/0.05 (tool defaults); winsorized 3/3 factory default between | `stack_rejection.sh`: percentile ≤6, winsorized 7–50, GESD >50 at 0.3/0.05 | **MATCH** (the 7–50 winsorized band is our inference; docs state no band) |
| normalization | lights addscale + `-output_norm` | identical | **MATCH** |
| `-rgb_equal` | script passes it; command doc conditions it on NOT using SPCC | omitted (we run SPCC) | **MATCH (doc-side)** — the official script and its own command doc disagree; we follow the doc condition |
| weighting | factory NO_WEIGHT; nothing prescribed | off, per-set recipe records why (measured min-max-ramp soft-cull at low spread) | **MATCH** |
| culling | official scripts none; `-filter-*` optional | recorded per-frame QA policy → recipe exclude with reasons (session-edge settle, frame-wide degradation, aircraft; satellites kept) | **EXTENSION** — no conflict; official filters cull on registration metrics only, blind to transient classes |
| bit depth | 32-bit; docs warn 16-bit stacking loses information | 16-bit stack-time intermediates (`set16bits`) — RETIRED adaptation, measured ≈18× below per-frame noise (~+0.3% stack noise) | **DIVERGENCE whose removal condition has now FIRED** (x86 RAM/disk present) → drop `set16bits`, re-measure, declared delta (BACKLOG) |
| solve | native `platesolve` incl. `-localasnet` blind | external astrometry.net xylist route (sep extractor) — Siril's findstar-based matcher measured failing ultra-wide TRAILED fields | **DIVERGENCE (measured adaptation)** — the july23 class is only mildly trailed (roundness 0.80 vs july14's 0.615), so the native solver deserves a re-probe on this class → named test below |
| SPCC | linear + solved, before stretch; after crop/BGE in the official order | SPCC directly on the raw solved stack (BGE is a render-tier gap; K-delta order-robustness check pre-registered in README) | **MATCH with recorded gap** |

### C. PixInsight WBPP / industry reference

Version anchor (verified 2026-07): PixInsight **1.9.4 Lockhart** (2026-06-21),
**WBPP 2.9.0** (2026-01-14); DSS 6.2.2 (2026-07-18, now cross-platform); APP
2.0.0-beta46. WBPP stage order: calibrate (auto pedestal) → auto
CosmeticCorrection from the master dark (default-on since 2.7.5) → debayer →
measurement (PSF metadata) → opt-in Frame Selection (new in 2.9.0) →
StarAlignment → LocalNormalization → ImageIntegration → Autocrop →
astrometric solution on masters.

Where WBPP doctrine and Siril doctrine (and ours) stand against each other:

| axis | PixInsight/WBPP doctrine | Siril doctrine / our chain |
|---|---|---|
| master dark | average, no normalization, winsorized, no bias, no optimization for matched darks ("bias not required ... already present in dark frames"; optimization fails on amp glow) | **identical** — full agreement across all three |
| cosmetic correction | auto-CC from the master dark, default-on | `-cc=dark` from the dark's bad-pixel map — **same mechanism**, ours mandatory repo-wide |
| flats when none shot | no sanctioned lights-built flat; gradient tools are ADDITIVE-only by their own docs (GradientCorrection "purely additive"; MARS leaves multiplicative to Gaia normalization). APP alone sanctions an analytic vignetting model (Kang-Weiss artificial flats) | our per-set sky flat has no vendor precedent anywhere; closest official relative is Peris's twilight sky-flat procedure (percentile clip <0.02 to kill stars) — winsorized on ~400 drifting lights is our own validated mechanism |
| weighting | PSF Signal Weight default-on; bad frames get weight≈0, not exclusion ("no more a real need of throwing away frames" — Sartori); min-weight 0.005 is a compute-saver, not a cull | Siril factory NO_WEIGHT, no script weights; ours off with the measured min-max-ramp pathology. **Genuine philosophical split** — PI's normalized photometric weights have no ramp pathology; Siril has no PSFSW equivalent (standing TOOLS.md gap, still true at 2.9.0) |
| local normalization | between registration and integration, "crucial" with time-varying gradients, default-enabled | **no Siril equivalent** (global addscale only) — the second standing TOOLS.md gap, confirmed still open |
| registration | homography default + thin-plate-spline distortion correction for wide fields/mosaics; **external distortion models** "pre-correct the images for optical aberrations ... so the registration process can work with undistorted alignment references" | Siril: homography only (+SIP `-disto=` since 1.4). Our darktable pre-warp is mechanically the PI *external distortion model* idea, executed out-of-band — the need is recognized by every vendor (APP: enable distortion correction when RMS >0.5 px; DSS: polynomial warp) |
| rejection by N | WBPP Auto: <6 percentile, 6–15 winsorized, **≥15 GESD**; "we consider ESD the best rejection algorithm currently available" (Conejero); sigma defaults asymmetric 4/2 | Siril: ≤6 percentile, >50 GESD, winsorized between (3/3 convention). Ours follows Siril; both vendors converge on percentile-small / winsorized-mid / GESD-deep — they differ only on where GESD starts (15 vs 50) |
| lights normalization | additive-with-scaling + scaled output — Table 1 | **identical** |
| framing | register to reference geometry, **Autocrop the master after** integration | ours crops BEFORE (`-framing=min`) — same intent, opposite order |
| OSC colour | CFA (Bayer) drizzle is THE recommended final path; demosaiced integration = "temporary working images" | Siril's standard script (and ours) demosaics at calibrate; Siril's own SPCC page now also recommends Bayer drizzle — **the sharpest doctrinal split**, and for our class it is chained on moving undistortion inside Siril (drizzle needs CFA in; the darktable warp needs demosaiced in) |
| culling | keep-and-weight; 2.9.0 adds opt-in metric-threshold Frame Selection (preview aimed at "satellites, aircraft trails") | our recorded-QA-policy cull (~0–2 frames/set) is the manual equivalent of that opt-in step |
| bit depth | float32 end-to-end, no 16-bit blessing anywhere | Siril: 32-bit default, 16-bit allowed with a warning; our `set16bits` divergence stands out against BOTH vendors — removal condition fired |

DSS cross-check: kappa-sigma/median-kappa-sigma defaults, median masters,
score-based reference, polynomial (not TPS) warp, hot pixels from the master
dark at median+16σ — an older, simpler doctrine that contradicts nothing
above. APP: quality weights (star count + SNR, offset by FWHM), LNC local
normalization, MBB blending, distortion correction on demand, "no outlier
rejection unless needed — the Bad Pixel Map takes care of hot/bad pixels".

### D. Measured on the july23 run (the live test)

- Frame QA (Siril `register -2pass` regdata, 1601 frames): 100% registration,
  zero match failures, per-set medians FWHM 2.633/2.648/2.675/2.718 px
  (CFA-sampled), roundness 0.798–0.803, background stable to 0.1%
  (`datasets/july23/set-0<N>/qa_work/frame_metrics.json`, archived — `git show 3554aa3:datasets/july23/`). The 3 s subs halve
  july14's in-exposure trail exactly as the acquisition checklist predicts
  (roundness 0.80 vs 0.615 at 6 s).
- Anomaly audit: satellites only in sets 01–02 (5 + 1 objects), no aircraft so
  far; culls are session-edge settle frames only (2/401, 0/400, 1/401 …).
- Fixed-mount fingerprint: set-01 sweeps RA 306.56°→313.44° in 27.2 min
  (15.18°/hr RA ≈ sidereal), Dec constant 43.69→43.66; the camera was re-aimed
  ~6.2° back between sets (set-02 starts at RA 307.25°) — four nearly
  coincident footprints (`datasets/july23/set-0<N>/fingerprint.json`, archived — `git show 3554aa3:datasets/july23/`; all four
  verdicts CONFIRM fixed).
- Stacks (single-pass undistort chain, ~2 h/set wall-clock serial): 399/400/
  400/398 of eligible frames registered AND stacked — zero registration loss
  across 1597 frames. GESD (0.3/0.05) per-channel rejection 0.001–0.5% —
  outlier tails only, exactly the doctrine intent at this depth. Stack
  background noise (Siril bgnoise, ADU): set-01 1.45/1.78/1.34 → set-04
  1.20/1.36/1.15 (R/G/B) — monotonic improvement matching the sky darkening
  QA saw (bg16 1065→1057).
- Blind solves on all four stacks + combine: 17.05–17.07″/px, centers RA
  309.6–310.8, Dec +41.9…+43.8 (the ~1.8° southward re-aim walk across the
  night); logodds 157–414.
- SPCC (spec-less run = the accidental index-0 model, "Generic mono sensor" ×
  Antlia R/G/B — `docs/spcc-sensor-curve-z6iii.md` §1.2; local Gaia XP): K factors R 1.000 across
  the board, G 0.686–0.728, B 0.883–0.967, ~2900–3120 of ~5100–5510
  photometry stars kept per product — one tight family, and the same ballpark
  as july14 set-01's tracked record (G 0.708, B 0.945): same sensor, sane.
- Combine (4-member min-framing compose of the per-set stacks, plain mean +
  nbstack weights, STACKCNT 1597): 4109×2612 full-depth canvas — the 4-way
  intersection after per-set drift crops (~1050 px each) and the re-aim
  scatter; NAN + Pelican + the Cygnus dark lanes comfortably inside.
  Union/groups framing stays available if the wider drift corridor is wanted.
- Judge surfaces (diagnostic linked autostretch, 16-bit PNG): clean at
  inspection scale — no seams, holes, rim artifacts, chroma blotches, or
  visible walking-noise streaks; uniform airglow tint expected (background
  extraction is the user-gated render tier, not this chain).
- One infrastructure lesson, measured: two concurrent rapid-fire flatpak
  siril-cli loops die probabilistically in bwrap sandbox setup (instance-dir
  cleanup race) — closed by the flock-serialized invoker
  (`scripts/lib/siril_run.sh`, removal-register row); the chain reran
  serialized and clean.
- **32-bit doctrine, vindicated on data:** 16-bit integer intermediates
  (1) quantized one channel's histogram to MAD=0, degenerating Siril's
  linked-autostretch statistics, and (2) suppressed extended-structure
  contrast ~30–45% (probe twin: NAN contrast 4.8/2.4/3.9 vs 8.5/2.9/5.6
  %-of-sky). The 32-bit chain reads contrast 15–37% of sky (SNR 6–13) vs
  ~10% (2.3–3.3) at full depth. Both vendors' float doctrine is measured
  signal protection on low-e-flux wide-field data, not conservatism.
- **The warp leg's ICC contract is level-critical:** the sRGB-tag-matched
  round trip carries a TRC toe mismatch below linear ≈0.003 (+4.7% at
  0.0015) that injected a radial corner chroma on 3 s-class data while
  leaving 6 s-class untouched; the fixed contract (untagged float TIFF +
  LIN_REC709 export) measures identity 1.0000 at every level. Registry ICC
  entry (mechanism + numbers).

### E. Doctrine deltas → named tests (pre-registered, not run here)

1. **Siril-native SIP undistort vs the darktable route** — one knob (the
   distortion mechanism), same set, judged on `seqtilt` off-axis + drift-axis
   stations + full-frame finals. The fitted lensfun entry's removal condition
   names exactly this ("a chain consuming the model another way — `register
   -disto=` with a trustworthy source"). Blocker history: astrometry.net SIP
   was measured-bad at this scale; the UNTESTED arm is Siril's own solver's
   SIP on the mildly-trailed july23 class.
2. **Native `platesolve -localasnet` on the july23 stack class** — the
   dead-end covers Siril's matcher on heavily-trailed july14 frames;
   roundness 0.80 data may match fine. If it does, the external solve route
   gains a native sibling (solve_field.py stays for the trailed class).
3. **`-opt` dark optimization vs matched darks (uncooled body)** — FAQ
   doctrine fork; A/B on one set, judged on dark-residual metrics (ties into
   the BACKLOG:`walking-noise` mechanism work). Low priority: our darks are
   same-night, shot at session-end temperature, which is the condition base
   doctrine says needs no optimisation.
   **POOLED MASTERS ACROSS NIGHTS RIDE THIS SAME FORK, and the decision rule
   is:** pooling is gated on the nights' masters measuring identical, judged
   on `noise_split.sh`'s structured term, and **per-session stays the
   default** until it is. The gate is currently SATISFIED on level and not
   yet decided: the three nights' pedestals agree to 0.1 ADU (`TOOLS.md`, the
   sensor-pedestal entry — cited, not restated) and their noise agrees within
   1%. Level agreement is not the whole test; the structured term is.
4. **Bayer-drizzle colour route for OSC** (SPCC page recommendation) —
   structurally incompatible with the darktable warp (drizzle needs CFA input;
   the warp needs demosaiced frames), so it becomes live only if test 1 moves
   undistortion into Siril. Chain dependency recorded.
5. **`set16bits` retirement** — not a test of doctrine (docs are unambiguous);
   an x86 re-measure landing as a declared delta.

## Sources

- siril.org/download/ + /download/2026-06-17-siril-1-4-4/ (stable version)
- gitlab.com/free-astro/siril @1.4.4: `<siril-repo>/scripts/OSC_Preprocessing*.ssf`,
  `src/core/settings.c`, `src/gui/stacking.c`, `src/gui/uifiles/siril.ui`
- gitlab.com/free-astro/siril-scripts: `preprocessing/OSC_Preprocessing_
  Without{Flat,Dark,DBF}.ssf`, `DSA-OSC_Preprocessing_with_BGE_and_Undistort.ssf`
- siril.readthedocs.io/en/stable: preprocessing/{calibration,registration,
  stacking,conversion,drizzle}.html, astrometry/platesolving.html,
  processing/color-calibration/spcc.html, preferences/preferences_gui.html,
  Commands.html
- siril.org/faq/ · siril.org/2021/12/enough-with-dark-flats/
- discuss.pixls.us t/20991, t/35487, t/23972 (team statements, historical)
- pixinsight.net/dev (PI 1.9.4 build 1695, WBPP 2.9.0 announcements) ·
  pixinsight.com/forum threads 18148 (1.8.9/ESD-best), 18182 (WBPP 2.4.0 —
  the Auto rejection table + LN placement), 23775 (auto-CC default), 19079
  (min-weight intent), 25260 (1.9.3/Autocrop)
- pixinsight.com/doc/docs/{ImageWeighting,MARS,XISF-1.0-spec} · archived
  pixinsight.com/doc/tools/{ImageIntegration,ImageCalibration,StarAlignment}
  · gitlab.com/pixinsight/Reference-Documentation (LocalNormalization,
  CosmeticCorrection, Debayer, GradientCorrection pidocs) ·
  pixinsight.com/tutorials/{master-frames,sa-distortion}
- deepskystacker.free.fr technical/FAQ (2026 archive) + github.com/
  deepskystacker/DSS · astropixelprocessor.com (features, Mabula mosaic
  tutorial part 2, downloads)
- Repo records: `git show 3554aa3:datasets/july23/` (QA/audit/solves; session since archived —
  the records live in the archive + git history), `docs/dead-ends.md`
  (SIP/solver/weighting mechanisms); the 1.4.4 syntax audit this doc builds on
  is graduated into `TOOLS.md` Tier 1 (deep-dive retired — git history)

## Verdict / recommendation

The chain is doctrine-compliant at every stage Siril documents, usually at the
tool's own defaults (rejection selection, normalization, weighting-off,
cc=dark, debayer timing, 2-pass registration), and the master/calibration
doctrine agrees across ALL vendors checked (matched darks -nonorm, no bias, no
optimization, CC from the dark, CFA flat division, addscale lights). The real
divergences are three, all documented adaptations with mechanisms and removal
conditions: the per-set sky flat (no vendor sanctions a lights-built flat;
Siril's official answer is "no flat at all" — strictly worse for a ~2× falloff
lens with no native multiplicative corrector; APP's Kang-Weiss analytic model
is the nearest vendor-shaped alternative and GraXpert Division remains our
researched fallback), the external undistort (mechanically PixInsight's own
"external distortion model" idea executed out-of-band; Siril-native SIP is the
untested comparator → named test), and 16-bit stack intermediates (against
both vendors' doctrine; removal condition fired on this rig — retire next).
Two industry-reference capabilities remain genuine Siril-side gaps, confirmed
still open at WBPP 2.9.0: Local Normalization and PSF-Signal-Weight-class
weighting. Where the two vendors themselves disagree (GESD threshold 15 vs 50,
CFA-drizzle-as-final vs demosaic, weight-by-default vs no-weight, crop-before
vs autocrop-after), our chain sits on the Siril side by construction, and each
fork is now recorded here rather than implicit.

## Status

PROVISIONAL (doctrine mapping source-verified 2026-07-25; named tests not yet
run; WBPP section pending). Repo-side numbers are EMPIRICALLY TESTED and cite
tracked records.

## Graduation

- BACKLOG: named tests E1–E3 + the fired `set16bits` removal condition.
- TOOLS.md: Siril 1.4.4 confirmed current stable; native `-localasnet`
  blind-solve sibling + SIP `-disto=` noted against the solver/undistort rows.
- README reference-standard table: verified current at 1.4.4 (this doc is the
  audit trail).
- dead-ends.md: no changes (no entry contradicted; the SIP entry's scope is
  astrometry.net-index SIP, unchanged).
