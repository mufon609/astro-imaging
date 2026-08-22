# Star separation, deconvolution, PSF treatment

Phase-1 split of `docs/dead-ends.md` (organize-only; the original file stays
the live registry until the merge is decided). Content below the marker is
VERBATIM from the original, so in-text "above"/"below"/section references may
point at entries now homed in a sibling file — `README.md` in this directory
carries the index, the assignment rule, and the block manifest that resolves
them. Do not edit below the marker while the refactor is in phase 1; the split
is re-derivable from the manifest and verified byte-identical by `split.py`.

<!-- == verbatim content from docs/dead-ends.md below this marker == -->
**Separation** (informs the x86 tool choice):
- **MECHANISM, NOT MEASURED:** a mask+inpaint separator is reported to destroy
  resolved-object structure (inpainting HII knots out as stars and screening
  them back as blobs), where a learned separator (StarNet2/StarXT) keeps
  field-star flux and far less object structure — hence use the learned one on
  resolved objects. No side-by-side numbers are recorded. The conclusion is
  consistent with how the two methods work and with the fact that the shipped
  chain's StarNet2 separation measures cleanly, but it is not a controlled
  result.
- A bright-star residual/shell is a per-DATA property (tight PSF vs big trailed
  PSF) — measure per dataset, never carry one set's number to another.

- CLASSICAL deconvolution (makepsf + RL) where trailing is in-exposure fails —
  unstable symmetric PSF on ≈0 background. (A LEARNED deconvolver is NOT classical RL
  and is a live x86 option, not a dead-end — tool choice + CPU costs in `TOOLS.md`.)
- **PSF HOMOGENISATION — REFUSED BY THE OWNER, and the ruling binds wider than the
  technique.** Convolving each frame to a common, broader target PSF so corner and
  centre match is *"absolutely not a fix"*; *"the centre is most important and it
  would be stupid to take that for granted"*; it is *"not a suggested improvement
  but an accepted failure mode"*. **"Fix the root or it isn't a fix at all."**
  **The general form refused on sight: matching the corner to the centre by
  DEGRADING THE CENTRE, and any variant buying uniformity by spending quality at
  the good end of the field. Cropping and zone down-weighting are the same act by
  other means. Only a treatment that RECOVERS corner detail counts as a fix.**
  **The literature agrees formally — this is a measured information loss, not an
  aesthetic preference.** Zackay & Ofek 2017, *"How to coadd images?"* I and II
  (arXiv:1512.06872, 1512.06879): the optimal coadd applies a matched filter to
  each image USING ITS OWN PSF and only then sums, and verbatim — **"methods that
  either match filter after coaddition, or perform PSF homogenization prior to
  coaddition, will result in loss of sensitivity."** The proper coadd *"preserves
  all the information from the original individual images on all spatial
  frequencies"*. So homogenisation is the OLDER standard (the DES/Pan-STARRS
  lineage it was proposed from) and the modern result supersedes it.
  **The argument that produced the proposal, kept because the flaw recurs:** it was
  argued that since the cause is outside the chain, *"every available response is
  identical under either aberration label"* — listing homogenisation, zone
  down-weighting, accept-it, and spatially-varying deconvolution. **Three of the
  four are ways of not fixing it**; the equivalence holds only by counting
  non-fixes as responses. **And the measured half that refutes it directly:** at
  the frame CENTRE there is no aberration gradient at all, so the chain is
  essentially the entire degradation there — ~12% of PSF width, of which the
  Lanczos4 kernel is 0.45% and our own CLAMP pin is 6.26% (one configuration,
  not a constant — BACKLOG:`resample-cost-and-drizzle`). A treatment that adds
  blur at the centre was proposed for a chain already softening the centre by ~12%.
  Implementation lead if the COADD question is ever reopened (orthogonal to
  deconvolution, availability UNVERIFIED here): `properimage` (quatrope/ProperImage),
  pip-installable.

- **NO INSTALLED TOOL DELIVERS A FIELD-VARIABLE ANISOTROPIC PSF CORRECTION — the
  MEASUREMENT is installed and the APPLIER is not, the treatment is owner-REFUSED
  either way, and a GLOBAL
  PSF cannot close a field gradient at all.** Three arms on one raw frame, every
  arm measured with identical Siril `findstar` settings (baseline whole-frame
  FWHM major 2.340 px, roundness 0.807, 7083 detections; roundness gradient
  across x −0.099).
  **Cosmic Clarity** (Stellar Only, Auto Detect PSF ON, amount 0.50, 704 chunks):
  2.310 / 0.802 / 6913, gradient **−0.093**. NULL, and ARCHITECTURAL rather than
  tuning — its own help says `--auto_detect_psf` measures the PSF per chunk and
  chooses "the two nearest **radius** models", and its models are named
  `radius_1/2/4/8`. Radius is a scalar; there is no ratio or angle in its
  interface, so an oriented elongation has no representation. The field-variable
  path was exercised and still could not express the defect.
  **Siril `rl` global** (`-mul -iters=10`): a genuine 10% FWHM gain rank-matched
  on the brightest 1500 (2.260 → 2.035) — but gradient **−0.091**, roundness
  slightly WORSE, and 77% of detections destroyed. Not tuning: one PSF over the
  whole frame sharpens everywhere by the same factor and leaves a field
  variation where it was.
  **`makepsf stars` is the POSITIVE result**: per 1500 px band its kernel ratio
  reads 0.863 / 0.851 / 0.816 / 0.804 / 0.758 against findstar's 0.832 / 0.836 /
  0.805 / 0.790 / 0.733 — gradient −0.105 against −0.099, FWHM tracking band for
  band. Siril CAN measure the anisotropy; it just applies one PSF per image.
  What remains with installed tools is Siril's PSF per REGION — tiling and
  reassembly, i.e. pixel surgery on the deliverable. The prior blocker is SNR,
  not seams: `-tv`/`-fh` regularisation with `-alpha=` is unbracketed, and if
  regularised RL still eats the faint population, per-region RL will too.
  **THE TITLE'S EARLIER FORM — *"no installed tool CAN correct"* — WAS MADE FALSE
  BY THIS TEAM'S OWN WORK, AND NOT BY AN EXTERNAL EVENT. THE ROUTE STAYS CLOSED ON
  BETTER GROUNDS.** The caveat defending the entry and the fact that voids it
  landed **35 minutes apart, in the same research arc, with neither commit
  referencing the other** — and the session was demonstrably working across BOTH
  files the whole time: `30da598` (08-13 15:08) wrote the load-bearing-`INSTALLED`
  caveat into this file **and edited `TOOLS.md` in the same commit** (`+32/0` here,
  `+2/-2` there, `+1` to `manifest.tsv`); `4e17e2d` (08-13 15:43) then wrote *"IT
  IMPLEMENTS THE CORRECTION"* into that same `TOOLS.md` and never came back.
  **A session wrote the defence, then landed the fact that eats it, into a file it
  had edited 35 minutes earlier.** That the two sites were both in reach makes the
  un-amended title sharper, not more forgivable. **MEASURED:** `psfex -dd` emits a
  `PSF homogeneisation kernel` section carrying `HOMOBASIS_TYPE`
  (`NONE`/`GAUSS-LAGUERRE`), `HOMOBASIS_NUMBER`, `HOMOBASIS_SCALE`,
  `HOMOPSF_PARAMS`, `HOMOKERNEL_DIR`, `HOMOKERNEL_SUFFIX` — and the parameter is
  CONSULTED, not merely declared: `makeit.c:553` gates on
  `homobasis_type != HOMOBASIS_NONE` and `:577` calls `psf_homo(…)`.
  **NO SINGLE DATE IS DEFENSIBLE HERE and the ambiguity is in the entry's own
  load-bearing word:** PSFEx was RUN on this rig at `543f099` (08-13 16:53) from a
  sha256-verified binary, scoped *"measurement, not adoption"*, and BUILT+INSTALLED
  at `754e5c5` (08-14 10:42). Which one makes `INSTALLED` true is the question the
  entry rested on without asking. **Three grounds replace the capability claim,
  none of which can go stale the same way:**
  (1) **NOTHING INSTALLED CAN APPLY THE KERNEL.** PSFEx writes `.homo.fits` cubes
  and stops. Bertin's manual names `PSFnormalize` (DES-internal, unpackaged) as the
  applier and says *"The SWarp software may also later include this possibility"* —
  it never did. **MEASURED FROM SOURCE, not from a config dump, because a dump
  proves a parameter is DECLARED and never that it is CONSULTED: 0 of SWarp's 69 C
  files contain `HOMO` / `homo_` / `.homo` / `PSFnormalize` / `homogen`, against
  `RESAMPLE` in 4 as the positive control.** That was SWarp *master*; **the gap to
  our installed 2.41.5 is CLOSED on the binary this rig actually runs** —
  `strings $(which SWarp)` matches `homo|psfnormalize` **0** times against
  `RESAMPLE` **43** times. The control is what licenses reading the zero: it proves
  config names DO survive as literals in the compiled output, so the zero is an
  absence rather than an artifact of stripping. **The gap is a PACKAGING one rather
  than a field one, which sharpens this ground:** `pypher` (Boucaud et al. 2016,
  ASCL 1609.022) is a pip-installable minimal-dependency applier and is absent from
  both interpreters here (MEASURED: host `python3` and `/opt/astro-venv`).
  (2) **The vendor calls homogenisation EXPERIMENTAL** — its own word, DOCTRINE,
  from the manual, which nobody on this team has read directly.
  (3) **THE DOCTRINAL CLOSURE IS THE REAL ONE AND IS ALREADY HELD, CORRECTLY, BY
  ITS OWN ENTRY — see *"PSF HOMOGENISATION — REFUSED BY THE OWNER, and the ruling
  binds wider than the technique"* above.** It carries the owner's words, the
  general form, and Zackay & Ofek 2017 making it a measured information loss rather
  than a preference. **It is not restated here on purpose: this entry's capability
  claim was a WEAKER, STALEABLE restatement of that closure, and the newer home is
  the one that rotted.** A closure resting on no tool fact cannot be falsified by an
  install. (Referenced by TITLE, not by line: three coordinates decayed under
  commits in one day.)
  **THE BOUND THE ORACLE ASKED TO HAVE ON THE RECORD, tagged MECHANISM — its
  inference from the solver structure, untested, and it says this is the part most
  worth attacking:** a target PSF *narrower* than the field's best would be
  deconvolution rather than degradation, and PSFEx does not forbid it — the one
  variant the owner's refusal does not obviously reach. NOT proposed: experimental,
  unregularised, no applier, and this registry already records the blocker for
  regional deconvolution here as **SNR, not seams**.
  Attribution: the finding, the `homo.c`/`makeit.c` source reads, the Bertin quotes
  and the three grounds are the Oracle's; the 35-minute self-inflicted account is
  the historian's, and it replaced an install-date frame that looked for an external
  cause.
  **THE WORD "INSTALLED" IN THIS ENTRY'S TITLE IS LOAD-BEARING, AND THE
  DOCUMENTED LANDSCAPE IS NOT THE SAME AS THIS RIG. STATUS: DOCTRINE — vendor
  documentation, UNMEASURED here.** RC-Astro's BlurXTerminator technical manual
  documents this exact capability, and the entry must not be read as "nothing
  corrects a field-variable anisotropic PSF." Verbatim: *"Images are processed in
  512×512 pixel 'tiles,' with overlap between tiles to avoid artifacts.
  Individual tiles are processed independently to allow for non-stationary
  PSFs."*; *"The PSF need not be stationary — the aberrations can vary across the
  image. BlurXTerminator will attempt to correct for the local PSF in each part of
  the image."*; and it *"will attempt to make the point spread function (PSF)
  found in the image azimuthally symmetric (round)."* Its stated correctable list,
  *"in limited amounts"*, names our candidates by name: **first- and second-order
  coma and astigmatism; trefoil (*"common with pinched optics and in image corners
  with some camera lenses"*); defocus (poor focus and/or field curvature);
  longitudinal and lateral chromatic aberration; motion blur (guiding errors)**.
  It requires LINEAR input *"ideally right after integration, channel combination,
  and perhaps color calibration and gradient removal"* — which is where our stacks
  sit. Stated limitation: it needs stars throughout, and *"if a particular tile
  does not have enough stars in it, BlurXTerminator will revert to trying to
  deduce the PSF from non-stellar features"*.
  **So the ceiling here is a PROCUREMENT boundary, not a physics one** (RC-Astro
  is PAID and the gap is deliberate — `TOOLS.md`). **What this does NOT do:**
  it does not measure anything on our data, it does not establish the correction
  would work at our magnitudes (*"limited amounts"* is the vendor's own hedge),
  and **it does not make applying it a fix** — a correction of unknown provenance
  applied to a finished product, while the defect's cause is unidentified, is the
  bandaid the owner has already refused. Our defect is also measured IN-EXPOSURE
  in sensor coordinates, and BXT runs on the stacked product where each output
  position holds a blend of sensor-position PSFs (MEMORY's corollary); the union
  corner is built from similar-rho samples so it is less blended there, but that
  is an argument, not a measurement. Source: rc-astro.com BlurXTerminator
  technical manual, fetched 2026-08-13.

