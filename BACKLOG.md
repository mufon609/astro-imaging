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
- **A native star-colour-neutral colour tool** — the O3-sphere mechanism
  Siril has no equivalent for (currently Nightlight's job). Still a genuine
  gap; the x86 chain decides Nightlight-x86 vs a native `ccm`+recombine path.

## Tool-first audit — in-house reinventions to retire

The kept `scripts/` still hand-roll several things a tool or standard library
owns — the same class of reinvention as a hand-rolled FITS parser (a tool writes
a format, a library reads it; never hand-parse). Priority-ordered; each names the
mechanism, the replacement, the action, and the source. "x86-gated" = needs
`astropy`, absent on the arm base rig; "now" = the tool runs on arm today.

- **16-bit PNG writer + sRGB chunks → Siril `savepng` (NOW).**
  `astrometrics.write_png16` is a from-scratch 16-bit RGB PNG encoder
  (zlib/struct, because Pillow cannot write 48-bit RGB PNG) plus hand-built
  sRGB/gAMA/cHRM chunks. Siril `savepng` writes 16-bit RGB PNG and embeds sRGB as
  a full ICC (`iCCP`) chunk automatically (`icc_assign` to set explicitly) —
  verified on the 1.4.4 flatpak; replaces the writer AND the colorimetry. Nuance:
  Siril tags via `iCCP` (full profile), not the lightweight sRGB+gAMA+cHRM
  triplet — both standards-compliant; only matters if a reader parses for those
  ancillary chunks. Source: Siril Commands + color-management docs.

- **FITS I/O — 5 hand-rolled parsers → `astropy` (x86-gated).**
  `astrometrics.py` (`read_fits`/`read_fits_planes`/`write_fits_planes`/
  `fits_dims`/`fits_pixel_scale`), `compose.py` (its own `read_fits_raw` +
  writer), `solve_field.py` (header reads + manual TAN-SIP WCS card injection),
  `spcc_cone.py`, `fitsmeta.py` each re-parse 2880-byte cards by hand.
  `astropy.io.fits` + `astropy.wcs` retire all five. Gotchas: write float32
  directly so BZERO/BSCALE auto-scaling stays off; numpy `[y,x]` ↔ FITS `NAXIS1`
  (x) is reversed; SIP needs `to_header(relax=True)` (adds the `-SIP` CTYPE
  suffix). Interim on arm: read Siril outputs via `savetif` + PIL where only a
  read is needed; the writes/WCS-inject wait for astropy. Source: astropy
  io.fits / wcs docs.

- **Hand-rolled PNG decoder (export-verify) → library reader or 16-bit TIFF.**
  `judgment_package.read_png16_sampled` hand-implements a full PNG decoder — all
  five scanline filters — to read PNG16 for the PNG8/PNG16 integrity check. Once
  Siril writes the file, the reader is only an integrity check: switch the
  lossless judgment surface to 16-bit TIFF read with `tifffile` (clean 16-bit RGB
  + ICC; x86), or read the PNG with a ~15-line stdlib chunk parser (examines
  IHDR/depth/colortype — not a decode, so no hand-roll violation). Pairs with the
  `savepng`/`savetif` adoption above. Source: tifffile / imageio docs.

- **Synthetic-flat GAP → GraXpert `-correction Division` (adopt).**
  The in-house self-flat was removed; a set with no matching flat now hard-stops.
  Additive background subtraction ≠ a multiplicative flat. GraXpert
  `-cli -cmd background-extraction -correction Division` is the ONLY headless-CPU
  multiplicative option (models the low-frequency background, divides — the
  synthetic-flat approximation); the repo already has GraXpert 3.2. Siril's
  `subsky` CLI is additive-only (its Division mode is GUI-only); ASTAP has no
  headless synth-flat; PixInsight is GUI/paid. Caveat: this corrects smooth
  VIGNETTING only, not dust motes / high-frequency PRNU — a real master-flat is
  the correct fix, so adopt as a documented gap-filler with "a matching real flat
  exists" as its removal condition. Source: GraXpert README; Siril background docs.

- **`solve_field` peak detection → `image2xy` (A/B test, not an automatic win).**
  `solve_field.detect_stars` hand-rolls `maximum_filter` peak-centroid detection
  to feed astrometry.net, because Siril's PSF-fit `findstar` rejects trailed
  stars — a SANCTIONED gap-filler, not a blind reinvention. `image2xy` (simplexy),
  astrometry.net's own extractor that `solve-field` runs by default, does NO
  PSF-fit / roundness rejection, so it DOES return elongated sources — strictly
  more tool-first, removes the hand-roll. BUT it is peak-based (peak not centroid;
  `-a` saddle can split a long trail; `-m` can reject one), so on heavy trails it
  shares the hand-roll's limitation. Action: A/B on a real trailed ultra-wide
  frame (image2xy xylist vs the current peak-centroid xylist → solve-field) — a
  hypothesis until measured. ASTAP is NOT the answer (docs: oval stars ignored →
  solve fails on trailed fields, though it handles the wide FOV via W08/V17
  databases). Source: image2xy man / simplexy.c; ASTAP docs.

- **Under-used natives to adopt opportunistically.** `pm` (PixelMath) is
  scriptable headless (verified) — any per-image arithmetic on a deliverable
  moves to the tool (bound: ≤10 input images per expression). `seqstat` /
  `seqpsf` / `seqheader` emit richer per-frame CSVs (bgnoise, full PSF params,
  any header keyword) beyond the `register` regdata `inspect_stage` already
  pulls — available if the checklist wants more measures. (No single Siril
  command reproduces PixInsight SubframeSelector's exact SNRWeight/PSFSignalWeight/
  Eccentricity set; roundness ↔ eccentricity and noise ↔ SNR are the analogs.)

- **Confirmed CLEAN (audited, no change).** `inspect_stage.py` and
  `cull_report.py` compute only over Siril's regdata, not pixels; `judgment_
  crops.py` is PIL inspection rendering; `compose.py`'s core is channel assembly;
  the `astrometrics` foreground masks are per-set config geometry. All ALLOWED
  (orchestration / decision-logic over tool numbers).
