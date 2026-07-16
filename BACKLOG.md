---
id: meta/BACKLOG
type: meta
---

# BACKLOG

**Superseded by the x86 redesign — see `docs/x86-empirical-test-plan.md`.**

The prior BACKLOG was a long queue of refinements and adaptations for the
aarch64 base rig and its hand-rolled render chain. The rig migration to
x86-64 (and the Siril-1.4 tool-rich discovery) makes almost all of it moot:
the render chain is being rebuilt tool-first on x86, and the arm64
workarounds' removal conditions have fired. That queue lives in git history;
it is not carried forward. The x86 rebuild will re-found this file from what
the rebuild actually surfaces.

## Architecture — build the chain AS the data-driven operating loop

The x86 render chain must be built as the per-dataset operating loop, not a fixed
sequence: **MEASURE** the dataset with the tools → **MATCH** its facts + the
declared priorities to the toolkit's routes → **RECOMMEND** the optimum with its
reason → **REPORT** it to the user → the user **accepts / adjusts / reroutes /
clarifies** (the gate before execution) → **EXECUTE** → **RECORD** the choice AND
its trade-off. Architecting this in from day one is far cheaper than retrofitting
a recommender onto a hard-coded chain. Stated as doctrine in `CLAUDE.md` ("What
this repo IS") and `README.md` ("The operating loop"); this item tracks realizing
it in the chain ([`docs/x86-empirical-test-plan.md`](docs/x86-empirical-test-plan.md)).
Each route it can recommend is one that RESEARCH has vetted and `TOOLS.md`
carries; each choice + trade-off it records is what tells us what to improve next.

## #1 PRIORITY (deep dive DONE, fix FOUND + PROVEN): productionise the lensfun warp

**The fix works and is measured** — an OFFICIAL MEASURED lens profile (darktable
5.4.1 built against Lensfun + the upstream lensfun DB) flattens roundness-vs-radius
at FULL 43-min depth: whole-frame roundness 0.550 → **0.656**, majFWHM 4.63 → **4.25 px**,
star density +45%/Mpx, roundness FLAT 0.63–0.68 from r=448 to r=2685, and 54/54
frames register (vs 52/54). The centre improved too (0.507 → 0.594) where distortion
is ≈0 — confirming the mechanism, not just the outcome. Crops:
`qa_work/reg/star_shapes_lensfun.png`. Detail: the deep dive + `registration_qa.json`.

**Remaining work is ORDERING, not discovery.** The proof ran darktable from RAW, so it
carries no darks/flats — dark/flat calibration must happen in SENSOR space BEFORE any
geometric warp, or the sky flat (validated, dust-safe) and the master dark stop
matching. Ordered:

1. **DONE — productionised, and the ordering + linearity are SOLVED.** Chain:
   Siril `calibrate` (CFA, master dark + sky flat) → debayer → `savetif` → `exiftool
   -TagsFromFile` (Make/Model/LensModel/FocalLength — darktable needs them to match
   the profile) → `darktable-cli --style lensdist --style-overwrite --icc-type SRGB`
   → Siril `register -2pass` → `seqapplyreg -framing=min` → `stack`. Proven on real
   calibrated frames: darktable warps the Siril TIFF with the identical piece hash as
   the raw run, and its module list collapses to `colorin lens finalscale colorout
   gamma`. **Do not** reorder to warp-then-calibrate: darks/flats are sensor-grid
   properties and a CFA mosaic cannot be interpolated.
   **LINEARITY — the trap, and the fix (do not get this backwards):** Siril's
   `savetif` embeds `sRGB-elle-V2-srgbtrc.icc` — a TONE CURVE — on linear pixels, and
   neither `icc_assign sRGBlinear` nor `set gui.icc_pedantic_linear=true` changes it.
   **`--icc-type SRGB` MATCHES that tag**, so darktable's decode and re-encode cancel:
   VERIFIED identity round trip, A_out/A_in **0.9996–1.0000, IQR 0.0003**.
   **`--icc-type LIN_REC709` is the BROKEN option** — it leaves the sRGB decode
   uncancelled (measured A_out/A_in climbing 0.1008 → 0.2121, gamma ≈1.34) and
   silently destroys photometry while looking correct on a preview. Match the tag;
   never "force linear". Verify with star AMPLITUDES vs brightness (constant ratio),
   never a mean or a preview.
2. **DONE — confound cleaned.** Distortion-only (`modify_flags` 7 → 1: no vignetting,
   which would fight the sky flat; no TCA) re-run on calibrated frames:
   **1010 → 1610 stars/Mpx (+59%), roundness 0.551 → 0.643, majFWHM 4.42 → 4.06 px**,
   the control's radial degradation (3.99 → 6.20 px) largely removed. The vignetting
   confound did NOT drive the gain — removing it made the gain LARGER.
3. **DONE — dust gate PASSED (the user's eyes, full-frame lossless).** Dust preserved,
   deep red intact, centre and right side fixed. Priority #1 cleared.
4. **Setup dependency — RECORDED** in `x86-setup-and-install` (lensfun DB update,
   the one-time GUI preset step, `--style-overwrite`, distortion-only, colour).
5. **Better model (optional):** Nikon's OWN coefficients ship in every NEF
   (`RadialDistortionCoefficient1/2/3`, `DistortionCorrection: On (Required)`) and would
   beat a community measurement — but they live in a Nikon-private SubIFD block that no
   headless Linux tool applies. Watch darktable's "embedded metadata" lens method.
6. **Cross-check (x86/GUI, now optional):** APP / PixInsight fit distortion from
   star correspondences with no catalog. Only worth it if the route disappoints.

**OPEN (not yet explained):** the corrected stack's innermost bin (r<445, n=386) reads
worse than its neighbours and than the control's centre; the outermost bin stays
elevated (5.14 vs 3.91 px mid-field), so the correction is large but not total.
Residual suspects: the community profile's accuracy, and the unresolved one-sided
component (differential refraction vs lens decentering).

## FRESH SESSION — DERIVE THE CONFIG FINGERPRINT FROM THE DATA (process organisation)

A session on process ORGANISATION, not on any one route: **the pipeline should READ the
gathered data and work out what it is**, then organise the processing around that. Today's
route is chosen by a config fingerprint — untracked drift at wide focal — and that
fingerprint is DERIVABLE, not something the user should have to declare.

**july14 proves it is derivable — every number below was measured this session:**
- **In-exposure trail, PREDICTED from EXIF alone:** 15"/s x cos(dec) x exposure / pixel
  scale. At 6 s, dec +47, 18.02"/px -> **3.40 px**. Siril's per-frame `findstar` measured
  roundness 0.615 (uniform across all 373) implying **~3.6 px**. Agreement within 6%.
  Mild trailing at 6 s is exactly the untracked signature at this focal — long enough to
  drift, short enough not to streak.
- **Inter-frame drift:** measured **34 px/min**; two astrometric solves 43 min apart give
  RA advancing **14.99°/hr vs the sidereal 15.041°/hr (0.3%)** with **Dec constant to 7
  arcsec**. A direction fixed in the rotating Earth frame traces a rotation about the
  polar axis: Dec preserved, RA at exactly the sidereal rate. That is a FIXED MOUNT,
  proven from the data — not declared.
- So the fingerprint = {exposure, focal, sensor/pixel scale, measured drift rate vs
  sidereal, per-frame roundness} -> "untracked, wide, drifting N px/min".

**Why this matters beyond convenience:** `mount` is currently a DECLARED fact
([[stop-and-ask-not-assume]]) because EXIF cannot record it. That rule stays — a
consumer must never ASSUME — but a derived measurement can now **CONFIRM or CONTRADICT**
the declaration, which is strictly better than either alone. A set declared `tracked`
whose stars drift at the sidereal rate is a labelling error the pipeline should catch and
STOP on, loudly.

Scope for that session: what can be derived vs what must stay declared; how the derived
fingerprint drives the operating loop's MEASURE -> MATCH step; where it is recorded; and
how a contradiction between declared and measured is surfaced. It should NOT re-litigate
today's route — that route is settled and is just one fingerprint's answer.

## ADOPT — make the distortion route a REPO PROCESS, focal-general, with culling decided

The wide-field untracked route is validated but currently exists as one dataset's
experiment at ONE focal length with an UNEXAMINED frame-selection default. Both must
change before it can be the process this repo recommends to any set with the same
config footprint. **AUDIT first, then implement** — the audit questions below are
cheap and each one gates a design choice.

### A. Generalise beyond 70 mm — AUDIT
- **THE decisive question: does darktable's lens module re-detect focal/aperture from
  each image's EXIF when applied via a style, or use the `op_params` baked into the
  style?** The `lensfix`/`lensdist` blobs hard-code `focal=70.0 aperture=4.0`. If
  darktable re-detects, ONE style serves every focal and the route generalises for
  free. If it uses the baked value, a 24 mm frame silently gets a 70 mm correction —
  the same class of silent-wrong as the LIN_REC709 gamma. **Test:** apply the 70 mm
  style to a 24 mm frame and measure the warp (`modified roi IN ... lens` + star
  displacement vs radius) against a style built at 24 mm. Everything else in this
  section depends on the answer.
- lensfun carries CALIBRATED entries at 24/28/35/50/70 for this lens and interpolates
  between them; confirm the interpolated behaviour at an intermediate focal, and that
  `crop=1.0` holds for the body.
- **Degrade loudly, never silently** (the repo's per-dataset rule): a set whose
  camera+lens is absent from the lensfun DB, or whose focal EXIF is missing/mixed,
  must STOP and say so — never fall back to an unrelated profile. `acquisition.json`
  already derives `focal_length_mm`, so the check is cheap.
- **Mixed-focal sets are a hard stop**, not an interpolation: the acquisition
  checklist's "lock the zoom ring" exists for this. Verify per-set, not per-session.

### B. The CONFIG FINGERPRINT is what selects this route — see the separate item below
This route is chosen by a config fingerprint the data itself carries (untracked drift at
wide focal). DERIVING that fingerprint from the gathered data is its own problem and gets
its own session — "DERIVE THE CONFIG FINGERPRINT" below. This item only needs the
fingerprint as an INPUT: given "untracked + wide + profile exists", recommend the route.

### C. Culling — ASSESSED but NEVER DECIDED (FRESH SESSION; do not fold into a render run)
- `frame_metrics.json` flagged 4 of 373 at z>3.5 (6897, 6900, 7263, 7264) and
  `cull_report` proposed excluding them. **No render in the registration deep-dive
  applied that.** It was an unexamined default, not a decision — the gap this item
  closes.
- **The stride subsets were quality-BLIND.** Every-7th (54 frames) and even-stride
  (169 frames) selected by TIME to fit the disk, not by quality: the 169-frame render
  INCLUDES DSC_6900, the frame flagged "worst on all three axes", while the 54-frame
  render excluded all four by luck. Disk pressure silently became frame selection.
  A full-depth render must use ALL frames plus an EXPLICIT culling decision.
- **The likely right answer is still "keep all", but it must be decided and recorded.**
  The spread is tiny — worst FWHM 3.857 vs median 3.634 (6.1%), background flat to
  0.35%, 98% of frames within +-2% of median FWHM — and the dead-end registry already
  says dropping a minority subset buys no matching gain and pays the full sqrt(N) noise
  penalty, and that wFWHM weighting at low spread is WORSE than none.
- **Re-assess culling AFTER the warp, not before.** The distortion correction made 2
  previously-unmatchable frames register (52/54 -> 54/54), so frames that would have
  been culled as match failures are now usable. Any cull computed on un-warped frames
  is measuring the wrong pipeline.
- Decide + record per set (accept/reject each candidate with its reason) in the
  per-dataset record, so "keep all" is a ratified choice rather than a default.

### D. Implement
Fold A-C into the chain as the operating loop's MATCH -> RECOMMEND step for this
footprint: measure drift + read focal/camera/lens -> check the lensfun DB -> recommend
the route WITH its reason (or plain homography, with its reason) -> report -> user
decides -> execute -> record the choice AND its trade-off. Route detail:
[`docs/wide-field-untracked-registration.md`](docs/wide-field-untracked-registration.md);
setup traps: [`docs/x86-setup-and-install.md`](docs/x86-setup-and-install.md).

## NEXT THREAD — combine all 5 july14 sets into one deep render (~1865 frames)

july14 is **5 sets of the same object**, same workflow, the camera **moved and
re-centred on the target every ~45 min**. set-01 (373 frames, 43 min) is one such
window; only set-01 + set-00 (4 frames) are local — the rest must be brought over.

**The re-aims cost nothing — the validated route already covers them.** A manual
re-centre is a rotation about the optical centre, and pure rotation with all scene
points at infinity is EXACTLY a homography (Szeliski — the same result that pins the
root cause). Stars are at infinity, so even a translated tripod head adds no parallax.
Once undistorted, a re-aim is indistinguishable from drift: same `register -2pass`, no
new mechanism. Lens distortion is fixed in SENSOR coordinates, so moving the camera
does not invalidate the lensfun warp either. Expect ~5x integration = **~2.24x SNR**
over set-01 alone.

This also retires the fixed-tripod drift wall for THIS data: the field slides off the
sensor after ~3.0 h at 70 mm (measured 34 px/min), so a single 2000-frame untracked
window would have ZERO common area — but each 45-min set sits at 76% field retained.
The re-centring solved it in acquisition.

Ordered:
1. **Verify every set is 70 mm** (both local sets are). The darktable style's
   `op_params` bake in `focal=70.0`, and lensfun carries SEPARATE calibrated entries
   at 24/28/35/50/70 — a zoom bump between sets silently applies the wrong distortion
   model. This is the acquisition checklist's "lock the zoom ring" surfacing as a
   processing consequence. Also confirm ISO/exposure match the darks.
2. **Measure the re-aim scatter before committing to one combined stack.**
   `-framing=min` keeps only what is common to ALL frames: within a set the drift is
   ~1500 px, across sets it is drift + hand-re-centring error. If scatter is large the
   common area drops below set-01's 76% — fallback is stack-per-set then combine the 5
   stacks (worse: 5 discrete residuals rather than one fit).
3. **Rebuild the sky flat from all ~1865 un-registered frames** — more frames = better
   Milky-Way rejection, which directly addresses the "faint un-rejected star specks"
   flagged in `skyflat_qa.json`. Same dust-contamination validation gate.
4. **Storage: ~433 GB peak** (1865 x 232 MB uncompressed). Comfortable on the x86 1 TB;
   impossible on the arm rig. No GPU needed — Siril has no GPU path, and the AI tier
   runs once per stack, not per frame.

## SUPERSEDED — the earlier framing (kept for the mechanism)

The deep dive is complete and the route was implemented + tested on the real frames —
[`docs/wide-field-untracked-registration.md`](docs/wide-field-untracked-registration.md),
record `datasets/july14/set-01/qa_work/registration_qa.json`. Settled:

- **Root cause is radial LENS DISTORTION**, not field rotation/projection (a homography
  is EXACT for pure rotation). Required transform class: **undistort → homography** —
  nothing local/elastic is needed, and `-transf=` already tops out at the right model.
- **Siril `register -disto=` is the native fix and its MECHANISM is proven on-rig**
  (syntax `-disto=file <path>`; `seqapplyreg` carries the undistortion; Siril reads an
  astrometry.net-injected TAN-SIP).
- **The blocker is the MODEL, not the mechanism.** Siril's matcher fails ~36° fields
  (roundness + catalogue depth eliminated); astrometry.net's SIP is not reproducible at
  wide index scales (65 px median disagreement for a lens that never moved) and feeding
  it in is a measured LOSS. Same blocker kills WCS-reprojection.
- **The model IS in the data**: exiftool decodes `DistortionCorrection: On (Required)` +
  `RadialDistortionCoefficient1/2/3` from every NEF. Nothing headless applies it.

Ranked routes to a trustworthy distortion model (each ends in the same proven
`register -disto=`; deciding metrics unchanged — removes edge trailing across the FULL
frame, preserves the dust, headless-first, free):

1. **Apply the NEF's own embedded Nikon profile (x86 test).** The exact model ships in
   every frame. Test whether darktable / RawTherapee (recent versions claim embedded
   lens-correction support for maker metadata) can apply it and emit linear 16-bit
   output, then re-register. Order constraint: calibration (dark/flat) is CFA and must
   precede any geometric warp, so the warp lands after debayer. Watch: the model form /
   normalisation is Nikon-private and undocumented; verify against the measured ~3.4%
   pincushion before trusting it.
2. **Astro Pixel Processor distortion-model registration (x86/GUI).** The one route with
   a published A/B fixing exactly this defect on this data class. Paid + GUI → audit,
   then a one-off run to see whether the edge reaches the in-exposure floor.
3. **PixInsight StarAlignment thin-plate-spline distortion correction (x86/GUI).** The
   reference local distortion model; cross-check.
4. **A denser index / better SIP for astrometry.net.** The failure is index sparsity at
   scales 12–19, not field-star count. Worth re-testing only if a denser wide-scale index
   series exists; otherwise closed.
5. **Re-shoot with tracking** — future acquisition only, useless for these frames, and
   would not remove the in-exposure trailing floor either (it would remove its CAUSE).

**Do not re-attempt** (killed with numbers, `docs/dead-ends.md`): `-disto=` fed by a
200-or-1500-star astrometry.net SIP; `setfindstar -relax=`/`-limitmag=` to rescue Siril's
solver on a ~36° field; "a better global transform"; short-window sub-stacks recombined
into one deep stack (the combine reintroduces the identical model error).

**Open for july14 set-01:** the depth-vs-edge choice (route A full 43-min depth with a
measured edge defect vs route C short-window at the floor for ~4× less integration) is an
aesthetic judgement awaiting the user's eyes on full-frame lossless finals. Also
unresolved: the defect's one-sided component (differential refraction vs lens decentering).

## Carried forward — durable data-capability items (not arch-specific)

These are real imaging capabilities the pipeline does not yet have; they
survive the rig change and should be reconsidered during the x86 rebuild
(x86 rebuild step 4+), each as a measured declared delta:

- **LRGB join** — compose L after both L and RGB are stretched (the standard
  luminance-detail join). The compose stage currently REFUSES a `luminance`
  member because compose-then-render cannot express a post-stretch L-join;
  the x86 chain should. Siril `rgbcomp -lum=` is the native primitive.
- **Full-size dual-band** — native Ha + 2× drizzle of OIII instead of
  downsampling OIII to Ha's half-size, gated on measured dither coverage
  (the per-frame `dither_phase_frac` record already exists in the
  registration QA).
- **run_pipeline auto-routing to a partitioned/large-sequence path** — on
  32 GB this is largely unnecessary, but a very large sequence may still want
  common-reference partitioning; decide against the real x86 memory headroom.
- **Deconvolution** — a measured dead-end on the arm64 data (unstable
  symmetric PSF on in-exposure trailing); revisit with BlurXTerminator on
  x86, where a real deconvolution tool exists.
- **A star-colour-neutral colour step** — the O3-sphere mechanism Siril has no
  single-command equivalent for. The headless path is now identified and its tool
  half EMPIRICALLY confirmed: measure mean star colour in the examine layer →
  apply a diagonal `ccm` (the ONLY headless neutral-balance path; verified on
  1.4.4). Nightlight is a dormant mechanism reference only — NOT "its job" (its
  OpRGBBalance balances the brightest-quartile stars; the OIII-lift is our
  inference, `docs/dead-ends.md`). The x86 chain runs the measure→ccm design
  against a bracket (SPCC, Nightlight).

## Tool-first audit — in-house reinventions to retire

The kept `scripts/` still hand-roll several things a tool or standard library
owns — the same class of reinvention as a hand-rolled FITS parser (a tool writes
a format, a library reads it; never hand-parse). Priority-ordered; each names the
mechanism, the replacement, the action, and the source. "x86-gated" = needs
`astropy`, absent on the arm base rig; "now" = the tool runs on arm today.

- **16-bit PNG writer + sRGB chunks → Siril `savepng` (NOW — EMPIRICALLY
  CONFIRMED).** `astrometrics.write_png16` is a from-scratch 16-bit RGB PNG encoder
  (zlib/struct, because Pillow cannot write 48-bit RGB PNG) plus hand-built
  sRGB/gAMA/cHRM chunks (`png_srgb_info`/`srgb_icc`/`PNG_SRGB_CHUNKS`). **Probe on
  the installed 1.4.4 flatpak**: `savepng` of a float32 FITS produced a PNG with
  IHDR color-type 2, bit-depth 16, and an **iCCP** chunk — so it writes 16-bit RGB
  PNG AND embeds the ICC automatically,
  retiring the writer AND the colorimetry. `savepng filename` takes NO flags (16-bit
  auto-selected when the source is 16/32-bit); the profile comes from a prior
  `icc_assign {sRGB|…}` + a save-time Preference. Nuance: iCCP (full profile), not
  the lightweight sRGB+gAMA+cHRM triplet — both standards-compliant. Source:
  on-rig probe + Siril Commands / color-management docs.

- **FITS I/O — 5 hand-rolled parsers → `astropy` (x86-gated).**
  `astrometrics.py` (`read_fits`/`read_fits_planes`/`write_fits_planes`/
  `fits_dims`/`fits_pixel_scale`), `compose.py` (its own `read_fits_raw` +
  writer), `solve_field.py` (header reads + manual TAN-SIP WCS card injection),
  `spcc_cone.py`, `fitsmeta.py` each re-parse 2880-byte cards by hand.
  `astropy.io.fits` + `astropy.wcs` retire all five — **CONFIRMED clean**
  (astropy **8.0.1**, Python ≥3.11, NumPy ≥2.0). Gotchas all
  primary-verified verbatim: write float32 directly so BZERO/BSCALE auto-scaling
  stays off (BSCALE/BZERO exist to smuggle unsigned INT through signed BITPIX;
  float32=-32 maps natively); numpy `[y,x]` ↔ FITS `NAXIS1` (x) reversed
  (`.shape == (NAXIS2, NAXIS1)`); SIP needs `to_header(relax=True)` (adds the
  `-SIP` CTYPE suffix; default `relax=False` OMITS it). Interim on arm: read
  Siril outputs via `savetif` + **`tifffile`** where only a read is needed
  (PIL misreads Siril's 16-bit RGB TIFF as uint8); the writes/WCS-inject wait
  for astropy on x86. Source: astropy io.fits / wcs docs.

- **Hand-rolled PNG decoder (export-verify) → library reader or 16-bit TIFF.**
  `judgment_package.read_png16_sampled` hand-implements a full PNG decoder — all
  five scanline filters — to read PNG16 for the PNG8/PNG16 integrity check. Once
  Siril writes the file, the reader is only an integrity check: switch the
  lossless judgment surface to 16-bit TIFF read with `tifffile` (clean 16-bit RGB
  + ICC; x86), or read the PNG with a ~15-line stdlib chunk parser (examines
  IHDR/depth/colortype — not a decode, so no hand-roll violation). Pairs with the
  `savepng`/`savetif` adoption above. Source: tifffile / imageio docs.

- **Synthetic-flat GAP → GraXpert `-correction Division` (adopt — mechanism
  CONFIRMED in source).** The in-house self-flat was removed; a set with no
  matching flat now hard-stops. Additive background subtraction ≠ a multiplicative
  flat. `graxpert -cmd background-extraction -correction Division -smoothing <0-1>
  -gpu false <file>` is the headless-CPU multiplicative option — source
  (`background_extraction.py`): per channel `imarray/background*mean`, i.e. divide
  by the low-frequency model = the synthetic-flat approximation. Flag corrections:
  **`-cli` is deprecated** (no longer required), and **`-bg_pts` is NOT a real
  flag** (the AI path needs zero sample points; `-preferences_file` matters only
  for the classical RBF/Spline modes). Siril's `subsky` CLI is additive-only (its
  Division mode is GUI-only); ASTAP has no headless synth-flat; PixInsight is
  GUI/paid. Caveat 1: corrects smooth VIGNETTING only, not dust/PRNU (model built
  from a ~240px downsample) — a real master-flat is the correct fix, so adopt with
  "a matching real flat exists" as the removal condition. Caveat 2: the installed
  GraXpert is a **third-party fork** (`geeksville`, PyPI test build), not official
  — official stable 3.0.2 is BGE+denoise-only but DOES include `-correction
  Division`. Source: GraXpert source (`main.py`/`background_extraction.py`). Full
  route map + the Siril-native SKY-FLAT alternative (captures motes/PRNU but
  contaminates on frame-filling IFN → dust-first sets must validate or reject it),
  the CMOS skip-bias / synthetic-offset doctrine, and july14's real-flats-impossible
  decision: [`docs/synthetic-flats-and-bias.md`](docs/synthetic-flats-and-bias.md).

- **Sky-flat tightening (july14 set-01 sky flat validated CLEAN — `docs/synthetic-flats-and-bias.md`).**
  The Siril-native sky flat is the recommended flat for this flatless set; before it
  enters a stack, tighten: (a) winsorized/sigma rejection instead of pure median to
  drop the faint un-rejected star specks; (b) smooth the flat to radial-only so
  division corrects vignetting without flattening the low-order sky/IFN gradient
  (leave that to the first-degree `subsky 1` background step); (c) dark-subtract the
  lights before building the flat (production); (d) the deciding test is a
  with/without comparison on full-frame lossless finals, dust-preservation the metric
  (the user's eyes). x86 GraXpert `-correction Division` stays the vignetting-only fallback.

- **`solve_field` peak detection → `image2xy` (A/B test, NOT a clean win —
  refined).** `solve_field.detect_stars` hand-rolls `maximum_filter` peak-centroid
  detection to feed astrometry.net, because Siril's PSF-fit `findstar` rejects
  trailed stars — a SANCTIONED gap-filler, not a blind reinvention. `image2xy`
  (simplexy), astrometry.net's own extractor that `solve-field` runs by default,
  is **source-verified to have NO shape/roundness gate at all** (estimate noise →
  median-subtract → threshold → connected-components → pick representative peak;
  grep for round/eccentric/psf-fit = zero) — so it DOES return trailed sources,
  mechanically closer to our peak-centroid than to a rejecting fitter. BUT it is
  NOT strictly-more-tool-first: (1) the trail-relevant knobs — `-a` saddle (σ,
  def 5; can FRAGMENT one rippled trail into spurious detections), `-p`
  significance (σ, def 8), `-m` **max deblend object size** (def 2000; NOT a
  "reject" flag) — are NOT exposed by `solve-field`'s CLI, so tuning needs the
  standalone `image2xy` binary; (2) `-s` = median-filter box (NOT sigma; sigma is
  `-g`); (3) a symmetric Gaussian match kernel (`-w`, def 1px) is SNR-mismatched
  to an elongated PSF. Action: A/B on a real trailed ultra-wide frame — tuned
  `image2xy` → `.xy.fits` → `solve-field --x-column X --y-column Y --width W
  --height H --no-remove-lines --uniformize 0` (those two flags off, else the
  supplied xylist is still list-filtered) vs the current peak-centroid xylist; a
  hypothesis until measured, record a dead-end with numbers either way. ASTAP is
  NOT the answer (its own docs: streaks ignored, "stars reasonably round" → solve
  fails on trailed fields; W08 FOV>20° / G05 FOV>6°). Source: image2xy man /
  simplexy.c / augment-xylist.c; ASTAP hnsky.org docs.

- **Under-used natives to adopt opportunistically.** `pm` (PixelMath) is
  scriptable headless — variables need **`$name$` tokens** (`"$img1$*0.5+$img2$*0.5"`;
  the naked-name form errors, confirmed on-rig) — any per-image arithmetic on a
  deliverable moves to the tool (bound: ≤10 input images per expression; full
  operator set incl `iif`/`mtf`/`noise`). `seqstat seq out.csv {basic|main|full}`
  and `seqheader seq KEY… -out=file.csv` emit clean headless CSVs (bgnoise/median/
  MAD/BWMV/location/scale; any header keyword) beyond the `register` regdata
  `inspect_stage` already pulls. **CAVEAT `seqpsf`/`psf`**: the PSF-fit photometry
  is real (FWHM, Amplitude, Magnitude, Background, SNR, X/Y) but headless CSV is
  NOT a documented flag — docs say it console-prints in headless mode; the GUI
  Plot "Export to CSV" is GUI-only — so capturing it means log-parsing (test
  before relying on it). Note Siril's **"roundness" = FWHMy/FWHMx, NOT
  eccentricity** `e=√(1−(b/a)²)` — related but distinct; use the right term.
  (No single Siril command reproduces PixInsight SubframeSelector's exact
  SNRWeight/PSFSignalWeight set; roundness↔eccentricity and noise↔SNR are analogs.)

- **`spcc_cone.py` cover math → Siril `healpix` (1.5.0-dev, NEW target).**
  `scripts/calibrate/spcc_cone.py` hand-rolls the nside=2 nested-HEALPix cover of
  a solved WCS to pick which local Gaia SPCC chunks to fetch. Siril 1.5.0-dev adds
  **`healpix`** — *"lists the NESTED HEALPix pixels at level 1 (Nside=2) and level
  8 (Nside=256) that overlap the currently loaded plate-solved image"* — the exact
  computation. Candidate to retire/verify the in-house cover math once the rig runs
  1.5.0; needs an empirical check that `healpix`'s pixel list maps to the
  zenodo-catalogue chunk filenames the fetcher expects. 1.5.0-dev only (not 1.4.4).
  Source: 1.5.0 ChangeLog / Commands (latest).

- **Confirmed CLEAN (audited, no change).** `inspect_stage.py` and
  `cull_report.py` compute only over Siril's regdata, not pixels; `judgment_
  crops.py` is PIL inspection rendering; the `astrometrics` foreground masks are
  per-set config geometry. All ALLOWED (orchestration / decision-logic over tool
  numbers).

## Script-level audit — does each whole script still make sense?

Beyond the I/O reinventions above: which WHOLE scripts a tool can replace or
remove under the checklist-workspace model. No kept script flagrantly breaks the
"no in-house pixel ANALYSIS / gate" rule — the measurement layer that did was
already deleted. What remains are two scripts doing an in-house pixel OPERATION a
tool owns, and two dormant on the wiped render chain. (run_pipeline, the
calibrate/SPCC set, inspect_stage, cull_report, and anomaly_audit are solid
orchestration / record / checklist / detector — not listed.)

- **`compose.py` → REPLACE its core with Siril `rgbcomp` (EMPIRICALLY confirmed).**
  The member ALIGN is already Siril (`register` + `seqapplyreg -framing=min`); the
  channel COMBINE is in-house (`np.stack` three mono planes → hand-rolled 3-plane
  FITS write). **Probe on 1.4.4**: `rgbcomp chR chG chB -out=out` → a 3-plane
  float32 RGB FITS ("Successful RGB composition"), and `rgbcomp -lum=chG chR chG
  chB -out=out` → the LRGB join ran headless — so the in-house assembly + FITS I/O
  retire, AND `rgbcomp -lum={img}` is the native LRGB primitive that closes the
  "LRGB join" carried-forward gap `compose` currently REFUSES. `compose` shrinks to:
  resolve `composition.json` → drive the Siril align (mono-filters) → `rgbcomp`.
  OPEN: the CLI `-lum` luminance-blend colour space (GUI offers HSL/HSV/Lab; the
  CLI default is undocumented) — check on a real dual-band + mono-filter set.

- **`crop_coverage.py` → REPLACE with `seqapplyreg -framing=min`, likely REMOVE.**
  It applies a precomputed coverage rectangle (array slice → FITS write) to trim a
  drift set's uncovered border band. Siril does this natively at registration:
  `-framing=min` *"crops each image to the area it has in common with all images
  of the sequence"* BEFORE stacking (compose already uses it) — so no falloff band
  ever forms, which is earlier + cleaner than the current post-stack crop. Adding
  `-framing=min` to the ordinary stack template makes the separate crop script AND
  its bounds-JSON producer redundant. `crop x y w h` is the native primitive if a
  post-hoc crop is ever needed. PENDING a real long-drift set: confirm
  `-framing=min`'s "common area" accounts for **drift AND rotation** (what
  crop_coverage's "union variant" bounds encode), not just translation.

- **`judgment_package.py` / `judgment_crops.py` → DORMANT (render-coupled).** They
  assemble judgment sets from render FINALS; the render chain is wiped/pending on
  x86, so they cannot run until it produces finals. The CONTRACT they encode
  (PNG8+PNG16 export-verify, WIN/NULL/needs-eyes, QUESTION.md, native-1:1
  pre-handoff inspection) is durable doctrine — keep the pattern — but reactivate
  them with the render rebuild, replacing the hand-rolled PNG codec then
  (`savepng` writer + `tifffile`/TIFF reader, per the reinventions section).

## 1.5.0-dev — pre-register before the x86 Siril upgrade

Siril 1.4.4 is current stable; 1.5.0 is unreleased (dev master). Nothing to adopt
today, but three items to plan for when the x86 rig moves to 1.5.0:

- **Native image-mask subsystem** — 12 `mask_*` commands (`mask_from_stars`/
  `_lum`/`_color`/`_channel`, `mask_blur`/`_feather`/`_threshold`/`_invert`…) plus
  a `-mask` flag on `denoise`/`rmgreen`/`epf`/`rl`/`sb`/`wiener` and a Python mask
  API. This is the first NATIVE path to region-confined ops (e.g. denoise the
  starless/background only) WITHOUT a hand-rolled numpy mask-blend — squarely
  in-bounds; adopt for the render when on 1.5.0. (`-mask` is dev-only; absent from
  1.4.4 syntax, confirmed.)
- **`healpix` / `eqcrop`** — `healpix` is the `spcc_cone.py` retirement candidate
  (above); `eqcrop ra1 dec1 ra2 dec2` is an RA/Dec-box crop (coordinate-defined
  framing, reproducible).
- **MIGRATION RISK: `starnet`/`seqstarnet` native commands are REMOVED in
  1.5.0-dev** (Siril consolidated StarNet behind `pyscript StarNet.py`, same as
  RC-Astro/SyQon). Capability kept, command surface gone — any `.ssf`/template that
  calls `starnet`/`seqstarnet` must migrate to `pyscript StarNet.py` before a 1.5.0
  bump. Also: `sb` deconv is **Split Bregman** (correct any doc/comment naming it
  otherwise). Source: 1.5.0 ChangeLog / Commands (readthedocs latest).
