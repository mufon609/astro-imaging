# Wide-field untracked registration — why one homography smears the edges (deep dive)

> **Read this as the researched ROUTE MAP for the registration stage of the
> operating loop, not a fixed recipe.** Official tools do every pixel op and
> every measurement; this records the mechanism, the measured routes (kept and
> killed), and the traps. Claims are flagged VERIFIED (survived the adversarial
> pass), MEASURED (on this repo's real frames, identical tool), or DISPUTED.
> The distilled operating truth lives in `TOOLS.md` Tier 2b and
> [`dead-ends.md`](dead-ends.md); this file is the deep record behind them.

- **Question** — Stacking a WIDE, UNTRACKED sequence with Siril's global 2-pass
  star alignment leaves the centre sharp and smears edge stars into short arcs.
  Why does one global transform fail, what transform class is required, and
  which route removes the edge trailing across the FULL frame while PRESERVING
  the frame-filling unresolved starlight?
- **Context** — Nikon Z6III + NIKKOR Z 24–70 mm f/4 S at 70 mm, OSC Bayer,
  6064×4040, **fixed tripod**, 373 × 6 s ISO1600 over 43 min, ~1500 px of sky
  drift. Frames not re-shootable with tracking, so the fix must be processing.
  **Priority #1: preserve the frame-filling UNRESOLVED STARLIGHT**
  (`dead-ends.md` terminology entry, sense 2 — it is stars, not dust).

## The theory — a homography is EXACT for this geometry

The assumed cause ("field rotation + gnomonic projection cannot be corrected by
one global transform") is **FALSE as a mechanism**, and this matters because it
points at the wrong fix.

- **VERIFIED — pure camera rotation is exactly a homography.** Szeliski, *Image
  Alignment and Stitching* §2.3: the pure-rotation case is equivalent to all
  scene points at infinity, and the inter-frame mapping is a plane projective
  transform (8 DOF). A fixed tripod under the rotating sky IS that case: stars
  at infinity, sky rotation an SO(3) map — linear in homogeneous coordinates,
  i.e. precisely a homography of the gnomonic plane. Verbatim-confirmed from
  the primary PDF. So for an IDEAL rectilinear lens, field rotation and
  gnomonic projection produce ZERO residual under a homography.
- **VERIFIED — what actually remains.** Szeliski's residual list for an optimal
  global fit: (1) unmodelled radial distortion, (2) parallax, (3) scene motion,
  (4) exposure differences. For a star field (2)–(4) are nil. **Radial lens
  distortion is the mechanism** — it displaces stars ∝ radius, exactly the
  centre-sharp / edge-smeared signature.
- **The composition, stated precisely:** with a real lens the inter-frame map
  is `distort ∘ H ∘ distort⁻¹` — NOT a homography (Kukelova et al., CVPR 2015,
  "Radial Distortion Homography"). As a star drifts 1500 px it samples a
  different local distortion; no 8-DOF global fit absorbs the difference.
- **VERIFIED — the lens is far from ideal.** The 24–70/4 S measures ~3.4%
  pincushion at 70 mm uncorrected (opticallimits.com); at the frame corner
  (r ≈ 3643 px) that is ~120 px of displacement — two orders of magnitude above
  the ~1 px registration accuracy a stack needs.

**Required transform class: undistort → homography.** Not a local/elastic
warp — the global projective part is already exactly right; only the lens model
is missing.

## The residual budget (MEASURED on these frames)

Every number from a tool: astrometry.net (solves), Siril `findstar` (PSF fits),
exiftool (NEF metadata).

| term | magnitude | fixable by registration? |
|---|---|---|
| **Radial lens distortion** | ~3.4% → ~120 px at the corner; ~8.6 px of smear at the crop edge after the best-fit homography | **YES — with a distortion model** |
| **In-exposure trailing** | **3.40 px predicted / ~3.6 px measured** | **NO — baked into each 6 s frame** |
| **Differential refraction** | ~1–4 px across 28.6°, asymmetric with hour angle | partly (per-frame model only) |

- **The field:** blind solve RA 306.047°, Dec +47.043° (Cygnus), 18.02″/px →
  effective focal ~67.8 mm (nominal 70).
- **The tripod never moved and the sky behaved exactly as theory says:** two
  solves 43 min apart give Dec +47.043° → +47.045° (constant to 7 arcsec) while
  RA advances 10.816° in 2597 s = 14.99°/hr vs sidereal 15.041°/hr (**0.3%**).
- **The in-exposure FLOOR:** 15″/s × cos(47.04°) × 6 s ÷ 18.02″/px = 3.40 px;
  independently, per-frame `findstar` roundness is **0.615 median, uniform
  across all 373 frames** (0.589–0.675) at FWHM 3.634 px ⇒ ≈3.6 px of trail.
  Physics, the solve and the PSF fits agree within 6%. No registration removes
  it; stars are ~1.6:1 at BEST. **Success is the EDGE matching the CENTRE,
  never round stars.** The uniform per-frame roundness is also the proof the
  radius-dependent smear is introduced by register+stack, not by the frames.

## The defect, quantified (Siril `seqtilt`)

`seqtilt` is the tool's own spatial star-shape measure and the only headless
door to one (`tilt`/`inspector` refuse in scripts): **Off-axis
aberration[FWHM]** = centre vs corners (the RADIAL term — this defect);
**Sensor tilt[FWHM]** = best vs worst corner (the ASYMMETRIC term);
**Truncated mean[FWHM]**; **Stars**. Driven + recorded by
`scripts/qa/star_shape.py` (`qa_work/star_shape_*.json`).

| production A/B + full depth | stars | truncated mean FWHM | **off-axis aberration** | sensor tilt |
|---|---|---|---|---|
| **OFF** — no distortion model, 54 fr | 5,095 | 3.20 px | **0.57 px** | 0.50 (16%) |
| **ON** — lensfun community, 54 fr | 10,707 | 3.28 px | **0.31 px** | 0.42 (13%) |
| community, 168 fr (superseded control) | 11,805 | 3.27 px | **0.25 px** | 0.51 (16%) |
| **SHIPPED** — FITTED model, 168 fr | 12,976 | 3.06 px | **0.25 px** | 0.31 (10%) |

- **The radial term is the defect, and it is removed** — 0.57 → 0.31, and 0.25
  at full depth (the deepest render is the most uniform, not the least).
- **The one-sided component is MEASURED, not unresolved** — a radial model
  cannot correct a one-sided term; the FITTED model's cut to 0.31 (10%) shows
  that fraction was paraxial model error, not tilt. The remainder's candidates
  and current state: BACKLOG:`one-sided-band`.
- **Sharpness vs the community model is NULL** (3.20 → 3.28 → 3.27): the
  correction buys star COUNT and radial UNIFORMITY; the in-exposure floor is
  untouched, exactly as predicted. The FITTED model's 3.06 is the centre band
  leaving the statistic, not the floor moving.

> **Do not re-derive this by binning a `findstar` list by radius** — the origin
> moves with the defect (537 px from a detection-sigma change alone) and the
> profile flattens as the defect worsens. `dead-ends.md`, "Three traps that
> make a registration comparison lie", trap 3. `seqtilt` has no origin to get
> wrong.

## The centre band the correction introduces (and the measure that sees it)

`seqtilt`'s centre-vs-corners is BLIND to a defect confined to a band along the
drift axis — it IMPROVES as the centre degrades toward the corners' mean.
Measured with fixed 350 px equal-area stations about the geometric centre
(`scripts/qa/star_stations.py`; drift axis 174.4° from the frame-1/373 solves;
records `qa_work/star_stations_*.json`) — cells are [n, majFWHM px, roundness]:

| stack | centre | along +1300 | perp −1300 |
|---|---|---|---|
| 168 fr community model (the band; superseded) | 927, **5.30**, 0.480 | 954, 4.32, 0.574 | 798, **3.60**, 0.706 |
| production 54 fr ON | 837, **5.73**, 0.437 | 914, 4.22, 0.585 | 628, 3.62, 0.679 |
| production 54 fr OFF (control) | 864, **4.03**, 0.556 | 748, **4.83**, 0.485 | 234, 3.95, 0.594 |
| **SHIPPED 168 fr FITTED model** (band removed) | 1086, **3.67**, 0.629 | 1005, 3.73, 0.638 | 851, **3.41**, 0.673 |

- **The inversion is the finding.** The control's centre is its BEST region
  (true distortion → 0 at the axis) and its defect grows OUTWARD; the
  community-corrected arms fix mid/edge and INTRODUCE a centre band — worst at
  the very centre, absent perpendicular (3.5–3.6 px = the floor). Confirmed by
  the user's eyes on the full-frame final (Deneb sits ~320 px above the band
  core).
- **Mechanism:** the community profile carries a small paraxial error ε(r); a
  star whose sky position CROSSES the optical axis during the ~1500 px drift
  has its radial unit vector flip sign, so ±ε becomes a ~2ε along-drift smear
  confined to the corridor the axis swept. Mid-field never crosses; its
  near-constant residual is absorbed by the per-frame homography. A tracked rig
  can never see this term.
- **Brightness split:** at detection sigma 3.0 the corrected centre reads
  3.89 px — bright cores survive; the band is a FAINT-star/texture defect that
  bright-star medians hide.
- **KILLED — the focal key:** EXIF 67.8 (solved effective focal) as the lensfun
  interpolation key is WORSE at the centre (5.42/0.468 vs control 4.88/0.516;
  `experiments.jsonl` paraxial_focal_key); the calibrated focal=70 entry is the
  best community key.
- **The fix — ADOPTED** (`experiments.jsonl` paraxial_model_source): a model
  fitted from THIS unit's own frames by between-frame star-correspondence
  fitting (`scripts/darktable/fit_lens_model.sh` — Hugin `cpfind`+`cpclean`+
  staged `autooptimiser`, hfov pinned at the solved value), installed into the
  live lensfun DB (`install_lens_model.sh`). The fitted curve agrees with the
  community entry at the crop corner (Δ 0.06 px) and diverges 2.4–3.9 px
  through the paraxial/mid field — the ε(r) the fit implies. Full-depth A/B vs
  community: centre station **5.30 → 3.67 px** (roundness 0.480 → 0.629),
  all-station spread 1.70 → **0.52 px**, truncated-mean **3.27 → 3.06 px**,
  stars +10%, sensor tilt 0.51 → 0.31. Approved on the user's eyes, full-frame
  lossless. The model is the PINNED registry entry for this lens@focal,
  fitted from the class's own frames, pinned in
  `scripts/darktable/lens_models.json` (THE authority — restored when the
  per-set-authority method was refuted at its root and reverted) and installed
  per run by the chain.

## The experiment — one knob, on the real frames

54 lights = every 7th of 373, spanning the FULL 43-min window (the residual
scales with TIME SPAN, not frame count). Calibrated with the validated master
dark + sky flat, debayered before registration, `-framing=min`, identical stack
parameters; the only knob is `-disto=`.

| | stars | roundness | majFWHM | radial (centre → edge) |
|---|---|---|---|---|
| **A** homography (control) | 17,770 | 0.528 | **4.74 px** | 4.33 → 6.46 |
| **B** + SIP undistort (`-disto=`) | **7,561** | 0.569 | **6.02 px** | 7.92 → 4.61 (**inverted**) |
| **C** homography, 9-min window | **26,354** | **0.600** | **3.87 px** | 3.52 → 6.41 |

- **B is a LOSS (killed hypothesis)** — `-disto=` relocated and worsened the
  defect, smearing the whole frame and halving detections. B's "better edge"
  (4.61 vs 6.46) is **survivorship bias** — per unit area B has 541 stars/Mpx
  vs A's 1259 (−57%). Read any star-shape metric with its n, and any n per
  unit area (`-framing=min` gives each variant a different frame size) —
  `dead-ends.md`, traps 1–2.
- **C CONFIRMS THE MECHANISM.** A 9-min (~310 px drift) window is better at
  every radius; its inner field (r < 1700) sits at the single-frame floor
  (roundness 0.619–0.634 vs 0.615; majFWHM 3.52 vs 3.63) — remove the drift
  and the homography becomes exact. C also keeps +56% field (5654×3899,
  22.0 Mpx vs A's 4169×3385, 14.1 Mpx) — less drift intersects away less. Cost
  is depth (12 vs 54 frames); per Mpx C detects slightly FEWER stars (1195 vs
  1259), exactly as 4.5× less integration predicts. Short-window stacking is
  the fallback, not the route: combining the sub-stacks reintroduces the
  identical model error (block k → block 1 spans the same drift) as discrete
  ghosts.

## Why B failed — the model, not the mechanism

- **MEASURED — the mechanism is sound.** `register -2pass -disto=file <path>` →
  "Distortion data is valid and will be used"; `seqapplyreg` carries it
  ("Distortion data was found in the sequence file") even though `-disto=` is
  absent from its own help. Syntax is `-disto=file <path>` — two tokens;
  `-disto=image` requires the loaded image solved. Siril also reads an
  astrometry.net-injected TAN-SIP header it did not write.
- **MEASURED — the SIP is not a lens model.** Fixed tripod ⇒ the distortion is
  physically identical every frame, yet two solves 43 min apart disagree by
  **65.3 px median (worst 127.9)** at the same sensor positions; a
  `--max-stars=1500` cap cuts it only to **43.8 (worst 132.1)** while the
  LINEAR solve improves sharply (scale 18.02/18.20 → 18.05/18.06; RA-drift
  error 6% → 0.3%; logodds 127 → 782). **More stars fix the position, not the
  distortion.** Mechanism: the SIP tweak is constrained by *matched index*
  stars, and the index at the wide scales this field needs (12–19) is
  Tycho-2-based and sparse — some positions agree (bottom 3.8 px) while others
  are wild (TR 132.1 px). **On SINGLE TRAILED FRAMES this also blocks any route that needs a
  per-frame astrometric solution.** (The tool names that stood here are removed
  and the scope is now stated — see the correction below.)
  **CORRECTION — AND THE FIRST VERSION OF THIS CORRECTION OVERREACHED.** It called
  the original sentence *"wrong three ways"*. It was not: **its premise is NARROWED,
  not false, and about a third of it survives.** The sentence read *"This blocks the
  WCS-reprojection route equally (SWarp / astropy `reproject` need the same
  per-frame solution)"*. **Rescoping the premise and dropping the two tool names is
  the correct disposition — "wrong three ways" invites DELETION of a clause that is
  true**, and this repo's own registry rescopes a narrowed blocker rather than
  deleting it.
  **(a) THE PREMISE IS NARROWED, NOT FALSE, AND THIS FILE NEVER STATES THE SCOPE.**
  The unusable-SIP finding is about SINGLE TRAILED FRAMES and it HOLDS there. On STACKED MEMBERS, whose stars are
  round, Siril's own `seqplatesolve -order=3` solves this class at ~0.9 px
  residual (`docs/dead-ends.md`), and members are what the shipped compose
  registers. MEASURED: `stacked`, `stacked member` and `seqplatesolve` each occur
  **0 times in all 411 lines of this file**, so a reader who lands here closes the
  route and never meets the narrowing.
  **(b) IT IS WRONG ABOUT SWarp, IN THE OPPOSITE DIRECTION FROM WHAT IT SAYS.**
  SWarp's blocker is not that it needs a per-frame solution — **it cannot read SIP
  at all and drops it SILENTLY**, accepting a `TAN-SIP` header and resampling on
  the CD matrix alone (measured from source and confirmed by SWarp itself under
  `-HEADER_ONLY Y`; `TOOLS.md`). A tool that ignores the model is a different
  problem from one that demands it, and the fix is different too.
  **(c) THE THIRD TOOL IS NOT NAMED HERE AT ALL, AND IT SPLITS BY ENTRY POINT — do
  not collapse the two.** `mProject` is verified end to end through Mink's `libwcs`
  (`wcsinit`→`distortinit`, `pix2wcs`→`pix2foc`, `wcs2pix`→`wcsc2pix`→`foc2pix`).
  `mProjectPP`, the plane-to-plane fast path, uses **Montage's OWN distortion code
  rather than Mink's** — `two_plane.h` / `Initialize_TwoPlane_BothDistort`, with
  `initdata_byheader` per plane — so it has an EXPLICIT distortion path and does not
  silently drop it, but **whether that path parses SIP specifically is NOT
  ESTABLISHED**, and one fetch closes it. **NOTHING IS PROMOTED BY ANY OF THIS** —
  `TOOLS.md`'s disposition stands unchanged: NOT ADOPTED and NOT RECOMMENDED,
  pending a probe that its SIP handling is real on OUR headers plus a manifest row.
  The point is only that this sentence's blanket "the WCS-reprojection route" is not
  one route with one blocker.
  **WHY IT SURVIVED, AND IT IS THE REUSABLE PART: THE SENTENCE WAS WRITTEN BY AN
  AUDIT.** It entered at `1f5fc6c` (08-07), *"wide-field registration deep-dive
  audited and condensed 622 → 385"* — rewritten by a compression pass rather than
  carried forward. The SWarp SIP-drop was MEASURED seven days later (`e59d4d2`,
  08-14). Of **20 commits that have touched this file, exactly ONE ever touched this
  sentence — the one that wrote it.** **Being audited is what makes a reader assume a
  file is current**, so a condense pass is where a claim most easily acquires
  authority it was never given.
- **Siril's own solver cannot supply the model either** — "Initial solve
  failed" at the computed 36.45° FOV with the correct centre, local Gaia and
  `-nocrop`; relaxed detection (candidates 3316 → 8694) and `-limitmag=+4`
  (2177 → 138,498 stars, mag 7.81 → 11.81) both ELIMINATED — the blocker is the
  star MATCHER at ultra-wide FOV (`dead-ends.md`, trailed-solve entry).
- **The model EXISTS in the data — the gap is a tool that applies it.** The NEF
  carries Nikon's own model (`DistortionCorrection: On (Required)`, radial
  coefficients 0.01821 / −0.01132 / 0.05939 — exiftool decodes them, refuting
  the "not decoded by open source" claim), but no headless Linux tool APPLIES
  the private block. A better model if darktable's embedded-metadata lens
  method ever reaches it; not a blocker today.

## Routes audited (verdicts; full rows + constraints live in `TOOLS.md` Tier 2b)

- **Siril `register -disto=`** — the only native distortion route; mechanism
  proven above, blocked solely by the model source. `-transf=` tops out at
  homography (no local/TPS — and nothing above homography is needed).
- **Siril multi-point (`register_mpp`)** — NOT a route: 1.5-dev, planetary
  seeing scope, piecewise TRANSLATION only.
- **PixInsight StarAlignment TPS / APP distortion-model registration** — the
  paid/GUI references; a practitioner A/B on this exact class reports Siril's
  global alignment smearing corners where APP's model does not. Audit-only.
- **Sequator** — its manual names our exact symptom (distortion → "false
  trails" worst at corners) and its author's envelope is ~5 min of drift at
  20 mm-equivalent; our window is 43 min — 8×. Windows/GUI; the METHOD
  transfers, not the tool. (Its "segments the sky and locally aligns" claim is
  REFUTED by its manual.)
- **WCS reprojection (SWarp / astropy `reproject`)** — inherits the SIP
  blocker; faint-signal traps if ever reopened (SUBTRACT_BACK default,
  flux-conservation, TAN beyond ~10°) are recorded in TOOLS Tier 2b.
- **Drizzle** — does NOT fix alignment-model error (`dead-ends.md`, drizzle
  entry).
- **OSC order** — debayer BEFORE registration (a CFA mosaic cannot be
  interpolated); CFA-drizzle is the documented exception (needs CFA input).

## The fix — an OFFICIAL MEASURED distortion model (WIN, on the real frames)

The SIP route *fitted* distortion per-frame from sparse trailed stars; the
answer is a model **measured for the lens**, immune to index sparsity:
**lensfun**, applied by **darktable** (darktable does every pixel op; lensfun
owns the model and its undocumented normalisation — hand-implementing it would
risk a silent factor-of-two error).

- **VERIFIED:** the community profile is focal-matched (`ptlens` focal="70"
  a=0.012 b=−0.017 c=0.039 for the 24-70/4 S — a calibrated entry, not
  interpolated). **MEASURED DB gap:** Debian's lensfun 0.3.4 has no `Nikon
  Z6_3`; without a camera match lensfun cannot build a modifier at all (the
  body supplies the crop factor). `lensfun-update-data` installs the upstream
  DB (which has it) to `~/.local/share/lensfun/updates/version_1`; darktable
  then auto-matches (autoscale 1.046).
- **WIN, on the tool's own measure:** off-axis aberration **0.57 → 0.31 px**,
  stars **5,095 → 10,707**, **54/54** frames register vs 52/54. The correction
  improves the field CENTRE too, where distortion ≈ 0 — exactly the
  prediction: undistort and ONE homography fits every star instead of being a
  global compromise. What it does NOT buy: sharpness (NULL) and the one-sided
  term. The community entry's paraxial error then wrote the centre band, and
  the FITTED entry replaced it (sections above).

## The july14 decision (the loop's RECOMMEND → REPORT → the user decides)

Chosen, executed and SHIPPED: the lensfun route with the model FITTED from the
set's own frames. Superseded: route A (full depth, measured edge defect) and
route C (short window, floor-limited, 1/4 depth, +56% field — kept as the
fallback if the route ever fails on a set). Not proposed: cropping to the good
field (hides a defect that is in the data). The honest floor stands: ~3.4–3.6 px
in-exposure trailing in every frame. Trade-off recorded: the fix depends on a
lensfun DB update the distro does not provide, and on per-set fitted-state
records installed per run; the session's records are archived (git history).

## The production chain (what runs, and the traps in it)

Every pixel operation is a tool's. The order is forced: **darks/flats are
sensor-grid properties, so calibration finishes in SENSOR space before any
geometric warp**, and a CFA mosaic cannot be interpolated — debayer sits
between. Scripted as `scripts/stack/run_undistort_pipeline.sh` (guards, disk
math and per-set mechanics in its own docstring).

```
Siril calibrate (CFA, master dark + validated sky flat, -equalize_cfa -debayer)
  → Siril savetif32                       (32-bit float TIFF, linear)
  → exiftool -TagsFromFile … -icc_profile:all=
       (copies Make/Model/LensModel/FocalLength — savetif carries none and
        darktable needs them to match the profile — and STRIPS the ICC tag)
  → darktable-cli --style lensdist --style-overwrite --icc-type LIN_REC709
  → Siril register -2pass → setref 1 (the pinned reference frame) → seqapplyreg -framing=min
  → stack (rejection doctrine-selected by sub count) -norm=addscale — no -output_norm;
    the sub-stack's level is its reference frame's own sky, stamped ANCLOC*/ANCSCL*
```

- **ICC, the float-leg contract:** untagged TIFF in + `LIN_REC709` out — a
  MEASURED PERFECT identity, ratio 1.0000 at every level and channel, warp
  confirmed firing. `--icc-type SRGB` (the earlier 16-bit-era rule) is correct
  ONLY on the 8/16-bit probe legs, and carries a TRC toe error that inflates a
  3 s-class sky on the float leg; never strip with siril `icc_remove` before
  `savetif32` (global ~1/12.92 scale). Mechanism + numbers: `dead-ends.md`,
  ICC entry; the two-leg rule: `CLAUDE.md` Environment.
- **The style is a pinned artifact, not a GUI step** — and it carries ONLY the
  enabled bit: darktable ignores the whole op_params blob and re-detects
  camera/lens/focal from each image's EXIF, so one style is
  camera/lens/focal-general and the correction SET cannot be chosen in a style.
  Distortion-only is enforced in the lensfun user DB instead
  (`install_lens_model.sh` strips vignetting/tca — unstripped vignetting
  DOUBLE-corrects flat-corrected lights). Field-by-field proof:
  `dead-ends.md`, darktable-style entry; verify per rig with
  `verify_lens_card.py` (the uniform card ALONE is vacuous — grid control
  required).
- **THE TRAP: darktable never fails.** An unmatched lens gets NO correction,
  silently (measured 0.000 px over 413 stars, exit 0, nothing in the log); a
  wrong-but-present lens gets a wrong model just as quietly. The chain must
  assert EXIF camera+lens+focal against the DB per set and STOP on a miss —
  `lens_preflight.py --require-profile` is that guard; "did the warp happen"
  is not sufficient (it passes the wrong-lens case). Mixed-focal or
  mixed-lens sets are a hard stop, not an interpolation.
- **darktable is deterministic; its container is not** — same input + style
  differs by one metadata byte while the warp reproduces exactly (and the
  production warp measured bit-identical under load, `dead-ends.md`). Never
  gate this route on a file hash.

## What graduates

- **`TOOLS.md` Tier 2b** — the full route rows (darktable+lensfun, the Hugin
  fit, `-disto=`, the WCS-reprojection notes) with this file's numbers.
- **[`dead-ends.md`](dead-ends.md)** — the Szeliski mechanism entry; the SIP
  kill; the three comparison traps; the in-exposure floor; the paraxial-band
  entry; the darktable-style inertness entry; the ICC contract.
- **`BACKLOG.md`** — `one-sided-band` (the open residual term),
  `native-solve-and-sip` (the Siril-native SIP comparator, the fitted model's
  removal-condition test), `route-recommendation`, and the RE-INSTATED
  fitted-lensfun register row (per-set-model authority is a registered dead
  end; the row records why, and the pruned `optical-state-models` item's close
  lives in git).

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
  (Szeliski, *Image Alignment and Stitching*, DOI 10.1561/0600000009)
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

**SOLVED AND SHIPPED — edges by the measured lens profile, the centre band by
fitting the model from the set's own frames.** Three model sources measured
against the same one-knob harness: astrometry.net SIP → `register -disto=` —
**killed (a LOSS)**; the community lensfun entry — **WIN at mid/edge** but its
paraxial error writes the centre band; the entry **fitted from this unit's
frames** — adopted (centre at the in-exposure floor, whole frame sharper,
approved on the user's eyes). The fitted model is since PINNED as data and
installed from the record (BACKLOG `removal-conditions`, fitted-lens row); the
chain is productionised; the style's warp verified reproducible to 0.000 px.

**THE GEOMETRY IS NOT THE OPEN TERM — a centred radial model already fits it.**
Measured against an absolute catalogue (`git show d2c4591:scripts/qa/fit_ptlens_joint.py`: sep
centroids, astrometry.net solve + catalogue, 970 matched pairs over 6 frames, 2
nights, 6 pointings), a **centred** ptlens model with a per-frame homography
nuisance reaches a **0.27 px median** residual. A free distortion centre lands
at (−6, +14) px and buys 0.05 px of median; Brown's tangential pair contributes
a 2.89 px peak and the same nothing. The lens is not measurably decentred.
This RETRACTS an earlier reading of the same data (8.35/6.71/8.54 px
"irreducible" residual, a ~180–240 px centre offset reproducing across nights),
which used an AFFINE nuisance where the geometry requires a HOMOGRAPHY — the
Szeliski result at the top of this file applies to the FIT as much as to the
registration, and the unabsorbed projective term is quadratic and even in x,
which is what decentring looks like. Same data, one knob: affine 14.24 px RMS /
7.63 median against homography 3.19 / 0.27. The trap is registered in
[`dead-ends.md`](dead-ends.md); the standards reading behind the chase is
[`untracked-widefield-standards.md`](untracked-widefield-standards.md).
CONSEQUENCE for the one-sided term: it is not an uncorrected distortion, so no
distortion model of any expressiveness removes it — the remaining candidates are
aberration and sensor tilt, which are optics, not geometry.

**Open:** the residual one-sided along-drift term — the measurements and the
eliminations are in `datasets/aug06/corner_work/` (`frame_depth.json` for the
N=40 table and the not-a-class test, `shape_azimuth_m01s{1,2}.json` for the
complete-azimuth check); the hour-angle discriminator remains OPEN work and
lives in BACKLOG:`one-sided-band`
(this file's earlier open items — the one-sided mechanism question and the
july14 render's disk-bound frame selection — are superseded by that slug and by
the chain's cull machinery + the session archive respectively).
