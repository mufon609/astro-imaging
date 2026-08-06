# JWST official rendering process (STScI team + the 2022 Jupiter pair) — deep dive

- **Question / scope** — What the JWST imaging team (Joseph DePasquale, Alyssa
  Pagan — STScI) and Judy Schmidt / Ricardo Hueso (the 2022-08-22 Jupiter pair)
  actually DOCUMENTED about turning calibrated per-filter data into the released
  color images: stretch tool + parameter semantics, black/white point doctrine,
  colorize + blend mechanics, artifact policy, and the Jupiter-specific
  mechanisms (derotation, short+long exposures, gap fills). Drives the
  j2_widefield_v2 design (`datasets/jwst-jupiter/experiments.jsonl`).
- **Context** — 2026-07-27. Siril 1.4.4 flatpak (arm rig), astropy 8, prepared
  common-grid frames + measured levels in
  `datasets/jwst-jupiter/qa_work/j2_v2_levels.json`. Evidence classes used
  below: **PRIMARY** (the maker's own words), **SECONDARY** (official org
  page/caption, not the maker personally), **SOURCE** (the tool's own code at
  the installed version), **COMMUNITY**, **INFERRED** (marked).

## Findings

### 1. The team's documented pipeline shape (PRIMARY throughout)

Per-filter stretch → per-filter artifact pass → colorize each filter →
combine → reference-based white balance → tonal finish. Every step below is
quoted from DePasquale's Sky at Night tutorial, the STScI "Art & Science of
Webb Imagery" lecture (2023-01-17, official re-upload), or Pagan's
Princeton/NEAF talks (URLs in Sources).

- **Stretch**: FITS Liberator, asinh. DePasquale's only published number:
  "setting the Scaling to Asinh, then setting the 'Scaled peak level' to 100,
  ensuring that the black and white point sliders encompass the bulk of the
  data." Pagan: scaled peak level is "the most powerful parameter"; stretch
  conservatively because finishing happens later ("I'm pretty judicial in my
  stretch"). Linear is rejected for deep fields because clipping = "information
  that we can't get back" — but **"for solar system objects linear tends to
  work just fine because they're pretty bright"** (Pagan, Princeton).
- **Dynamic-range doctrine for bright planets — the Neptune precedent**
  (Pagan, both talks): "we need to stretch each individual part of this image
  separately… if we stretch it all the same the disc would be blown out, the
  rings would be faint" — disc / rings / background field get SEPARATE
  transfers, "composited together". This is the team's documented equivalent
  of the Jupiter wide-field caption's "combination of short and long
  exposures" at display time.
- **Artifact pass, per filter, BEFORE rescale/combine** (Pagan): saturated
  cores arrive as nulls ("you can't perform any sort of photometry" flags) and
  are FILLED — "replaced by the nearest neighbor… we tend to do nearest
  neighbor", DePasquale's Photoshop alternative: Color-Range select the black
  cores, "set them to white"; ordering constraint: "that step should come
  first before rescaling." **SW chip gaps: "the chip Gap only exists for the
  short wavelength so we can actually fill that in with the closest wavelength
  filter to it in the longer wavelengths."** 1/f banding: removed with
  banding-removal actions or an "artificial flat". Cosmic rays: neighborhood
  average, "careful not to add or remove anything that wasn't already there."
- **Colorize + blend**: chromatic ordering (shortest→blue … longest→red;
  official explainer SECONDARY + DePasquale PRIMARY), with sanctioned
  deviations when a line is covered by another filter (Carina F470N→yellow).
  Mechanism: per-filter grayscale layers, each colorized, then **"I prescribe
  my colors accordingly where I can screen up these images together"** (Pagan,
  Princeton — Photoshop screen blend); the lecture describes the same step as
  "combine them additively together". The institutional written recipe
  (Chandra openFITS lineage, SECONDARY): Colorize hue 0/120/240, S=100,
  L=−50, layer mode **screen**. DePasquale's constraint that fixes hue sets:
  colors "when they're all added together, they come out to white."
  N>3 filters: adjacent pairs averaged into channels ("just a linear
  combination… added together and divided by two").
- **White balance is reference-based, not photometric**: neutralize the
  background to "very very dark gray or almost black" with equal RGB; white
  reference = bright astrophysical structure (star cores; face-on spirals for
  deep fields). DePasquale's tonal endpoints: "blank sky background slightly
  above absolute black… brightest parts pure white without being overly
  saturated." (Confirms this class's SPCC skip.)
- **Integrity rule** (DePasquale): "we're not trying to introduce things that
  weren't there and we're not trying to take things away that are there — with
  the exception of the instrumental artifacts."

### 2. The 2022-08-22 Jupiter pair specifically

Processed by **Judy Schmidt** (close-up; wide-field with **Ricardo Hueso**) —
NOT by DePasquale/Pagan (SECONDARY captions; the STScI 2023/147 "Jupiter
NIRCam" asset is a LATER DePasquale reprocessing of the same data, a different
deliverable).

- **The wide-field caption with the HDR statement lives in the Berkeley/AURA
  long form** (SECONDARY, verbatim): "A combination of **short and long
  exposures** in F212N (mapped to an orange color) and F335M (mapped to cyan)
  show Jupiter's rings and some of its small satellites together with
  background galaxies… The diffraction pattern created by the bright auroras,
  as well as the moon Io (just off to the left, not visible in the image),
  form a complex background of scattered light around Jupiter." The NASA blog
  caption is shorter (two filters, no exposure wording). ESA page chips:
  F335M=cyan band, F212N=orange band. **Chromatic order is deliberately
  INVERTED on this image** (longer λ = cyan) — sanctioned-deviation class.
- **What "short and long exposures" physically was** (Hueso et al. 2023
  Nature Astronomy Methods, PRIMARY): NIRCam ramps were read non-destructively
  3× per image; the team used "a combination of one, two and three groups… to
  remove saturated areas, produce sharp images without rotational smearing,
  and obtain high signal-to-noise ratio." I.e. ramp-GROUP selection at level
  2 — not exposed by L3 `_i2d` products. **Faithful L3 equivalent = separate
  display transfers composited (the Neptune doctrine), declared as such.**
- Schmidt's own statements (PRIMARY): the wide-field "was fairly simple to put
  together. I think that would've existed without me" (Planetary Radio) — the
  close-up is where "a lot of work went into creating **three congruent
  images** to allow for the use of 3 color channels. Jupiter's rapid rotation
  and not fitting within a single detector field makes things challenging"
  (Flickr, the ONLY primary derotation statement). Her philosophy: "I try to
  get it to look natural."
- **Schmidt's documented JWST toolchain** (Space.com walkthrough, PRIMARY):
  MAST advanced search → calib level 3 → **I2D** → FITS Liberator **ArcSinh**
  ("move the hill to the middle of the screen") → **16-bit TIFF, flipped** →
  Photoshop adjustment layers (non-destructive) → per-filter group + curves →
  **Advanced Blending channel isolation** (each filter occupies one RGB
  channel) → **Channel Mixer "pseudogreen": half red + half blue into green;
  "Make sure that your RGB channels add up to 100 percent."** Green gets "the
  nicest data" (Planetary Radio). Her July-2022 commissioning Jupiter (Flickr,
  PRIMARY) additionally documents **screen-mode channel layering** and
  **cross-filter gap fill**: "There were gaps in the data that had to be
  filled in using either filter to complete the other."
- **Hueso's wide-field assembly** (Nature Methods, PRIMARY): navigation of
  every frame in **WinJUPOS** against a synthetic lat-lon grid (WCS
  cross-checked with python); frames minutes apart combined with WinJUPOS
  derotation; the acquisition itself was designed so the four-detector "gaps…
  can be recovered with an appropriate dither pattern using four exposures."
  The team's derotated per-filter products are published **CC-BY** at
  github.com/JWSTGiantPlanets/Jupiter-Atmosphere-NIRCAM (PNGs: per-epoch
  3-image derotated combines, plain + high-pass; sqrt scaling on F212N,
  linear elsewhere) — the J3 derotation reference.
- **Close-up filter discrepancy** (recorded, J3 concern): blog + Schmidt's
  Flickr say the cyan channel is **F150W2**; the later STScI asset and the
  Hueso repo README say **F164N**. Schmidt's own statement (F150W2) is
  authoritative for HER composite; the F164N versions are different products.

### 3. The stretch tools — capability verdicts

- **FITS Liberator v5** (NOIRLab, Nov 2025; User's Guide techdoc113):
  Python/PySide6, **binary-only distribution, Linux amd64 only (deb/rpm/
  AppImage; macOS-ARM exists, Linux-ARM does not, no pip/source)** →
  **environment-blocked on the arm rig**; first-class candidate on x86. Real
  batch CLI: `fl5 -i <fits> -o <dir> -f asinh|linear -b <background>
  -p <peak> [--bit-depth 8|16|32]` + `.stretch` sidecar templates (GUI-saved;
  band-aware dispatch recognizes JWST filter tokens). v5 stretch set is
  exactly **linear + asinh**. Parameter semantics (guide, DOCUMENTED):
  background level "subtracted before the stretch"; peak level = "brightest
  sources of interest"; **Scaled Peak Level** = target brightness after
  scaling = the stretch-strength knob (default 10; doctrine: try 100, 1000…);
  black/white levels then window the STRETCHED values. Output TIFF only.
  Headless display requirement UNTESTED (x86 probe: bare TTY +
  `QT_QPA_PLATFORM=offscreen`; also dump a GUI-saved `.stretch` to learn its
  undocumented schema).
- **Siril 1.4.4 expresses the placed-points asinh transfer natively**
  (SOURCE-verified + rig-probed, `qa_work/j2_v2_stretch_probe.json`):
  - `asinh S O` = `clamp01( asinh(S·(x−O)/(1−O)) / asinh(S) )` — black point
    placeable, **white pinned at 1.0**, mono path clean, clips at 0.
  - `pm` in 32f **does not clip** (negatives and >1 survive save/load,
    SOURCE: raw `te_eval` store; probe: −0.25/+4.75 round-trip), tokens are
    `$name$` per file in cwd (≤10 images), `asinh()`/`max()`/`min()`/`iif()`
    available in expressions.
  - Therefore **out = asinh(S·(x−B)/(W−B))/asinh(S)** is one `pm` line per
    filter — the FITS Liberator placed-points model verbatim (B ↔ background
    level, W ↔ peak level, S ↔ scaled-peak role). `mtf B 0.5 W` is a pure
    linear [B,W]→[0,1] rescale (SOURCE: m=0.5 degenerates to identity) if a
    two-step form is preferred. GHS commands (`ght`/`modasinh`/`autoghs`) pin
    both endpoints — placement must be the separate linear step (same
    architecture as FITS Liberator itself).
  - `rgbcomp r g b` copies channels VERBATIM (SOURCE: no normalization);
    `savepng` is the single clamping 16-bit hop; FITS `save` preserves
    out-of-range.
  - **The v2 pre-registered FITS-Liberator adoption condition ("if Siril
    asinh cannot express the placed-points transfer") did NOT fire** — and FL
    is additionally arm-blocked; `fl5` becomes the pre-registered x86
    cross-check instead.

### 4. What remains undocumented (honest gaps)

- No numeric stretch parameters for any released image (only "scaled peak
  100" as a tutorial start and FL's default 10).
- No maker-published hue values for named colors (the Chandra lineage hue
  0/120/240 is the only written numeric recipe) — covered for us by the
  staged reference originals + measured hue anchors
  (`qa_work/j2_reference_study.json`: the release is a RESTRAINED duotone —
  belts only ~10% warm, aurora ~28% blue-excess, ring/sky/spikes neutral,
  sky lifted ~0.04).
- Screen vs strict-additive is ambiguous in the spoken record (Pagan "screen
  up" vs lecture "additively"); for the 2-filter wide-field the two converge
  everywhere except the green channel (screen darkens G slightly where both
  filters are bright). Schmidt's Space.com channel-isolation + pseudogreen is
  the most JWST-specific written mechanism.
- Schmidt's exact close-up derotation tool/order (J3's problem) — "three
  congruent images" is the entire primary record; the team's WinJUPOS route +
  CC-BY products are the documented alternative.

## Sources

STScI team: skyatnightmagazine.com/astrophotography/process-astro-images-like-james-webb-space-telescope
(DePasquale tutorial); youtube.com/watch?v=Evlmlj5TbPY (STScI lecture, official);
youtube.com/watch?v=8uUz_reqTko (Pagan Princeton); youtube.com/watch?v=cB5LuTxA2bY
(Pagan NEAF); science.nasa.gov/mission/webb/science-overview/science-explainers/how-are-webbs-full-color-images-made/;
petapixel.com 2023-07-26 + 2023-08-11 interviews; nasa.gov/mediacast/gravity-assist-how-we-make-webb-and-hubble-images;
chandra.harvard.edu/photo/openFITS/casa.html. Jupiter pair:
science.nasa.gov/blogs/webb/2022/08/22/webbs-jupiter-images-showcase-auroras-hazes/;
vcresearch.berkeley.edu/news/surprising-details-leap-out-sharp-new-james-webb-space-telescope-images-jupiter
+ aura-astronomy.org mirror (the short+long caption); esawebb.org/images/jupiter-auroras{1,2}/;
esawebb.org/about/general/image-processing/; apod.nasa.gov/apod/ap220830.html;
flickr.com/photos/geckzilla/52304433754 (three congruent images) +
52219195378 (screen + gap fill); planetary.org/planetary-radio/2022-chabot-dart-impact-report-and-judy-schmidt;
space.com/james-webb-space-telescope-image-editing (Schmidt walkthrough);
nature.com/articles/s41550-023-02099-2 (Hueso Methods);
github.com/JWSTGiantPlanets/Jupiter-Atmosphere-NIRCAM (CC-BY derotated).
FITS Liberator v5: noirlab.edu/public/media/archives/techdocs/pdf/techdoc113.pdf
(User's Guide); noirlab.edu/public/products/applications/app012/ (packages —
deb is `Architecture: amd64`). Siril: siril.readthedocs.io/en/stable (1.4.4)
+ gitlab.com/free-astro/siril 1.4.4 tag sources (asinh.c, mtf.c, ghs code,
pixel_math_runner.c, rgbcomp, savepng float_to_ushort_range).

## Verdict / recommendation

The documented process, expressed in the sanctioned toolset for the
wide-field v2: per-filter placed-points transfers (Siril `pm` asinh form; B =
measured pedestal, W = measured structure level, S bracketed) with the
F212N disc/field split per the Neptune doctrine; artifact fills (chip gap ←
F335M; saturation nulls → white-fill) exactly as the team documents them —
each a USER-gated policy toggle; palette = channel isolation + Schmidt's
pseudogreen (R=F212N, B=F335M, G=half each), balance judged against the
staged reference originals. FITS Liberator v5: skip on arm (blocked),
pre-register `fl5` as the x86 cross-check of the Siril transfer.

## Status

**PROVISIONAL** as a render recipe until the v2 composite is built and judged
(the ledger's j2_widefield_v2). The tool-capability claims are EMPIRICALLY
TESTED on-rig (stretch probe, levels) or SOURCE-verified at 1.4.4; the
process claims are documented-source extractions with evidence classes
marked.

## Graduation

- `TOOLS.md` Tier A — FITS Liberator row corrected (v5 facts, arm-blocked,
  `fl5` CLI); Siril row gains the pm placed-points note.
- `docs/jwst-archival-class.md` — provenance corrections (short+long caption
  source; F150W2-vs-F164N discrepancy; reference originals staged).
- `datasets/jwst-jupiter/experiments.jsonl` — the v2 design amendment
  (pre-registered before any run).
