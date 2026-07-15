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
  Division`. Source: GraXpert source (`main.py`/`background_extraction.py`).

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
