# Star separation, deconvolution, PSF treatment

Part of the dead-end registry — `docs/dead-ends.md` is the index, and
`00-registry-contract.md` governs how entries are read, cited, written and
deleted. Entries are maintained IN PLACE (pre-compression forms are in git;
the pre-split single-file registry is `docs/dead-ends.md`'s own history).
Cross-references to sibling files are written as (`<file>.md`) pointers.

<!-- registry content below; docs/dead-ends.md is the index -->
- **MECHANISM, NOT MEASURED:** a mask+inpaint separator is reported to
  destroy resolved-object structure (inpainting HII knots out as stars and
  screening them back as blobs), where a learned separator
  (StarNet2/StarXT) keeps field-star flux and far less object structure —
  hence use the learned one on resolved objects. No side-by-side numbers
  are recorded; consistent with how the two methods work and with the
  shipped chain's StarNet2 separation measuring cleanly, but not a
  controlled result.
- A bright-star residual/shell is a per-DATA property (tight PSF vs big
  trailed PSF) — measure per dataset, never carry one set's number to
  another.
- CLASSICAL deconvolution (makepsf + RL) where trailing is in-exposure
  fails — unstable symmetric PSF on ≈0 background. (A LEARNED deconvolver
  is NOT classical RL and is a live x86 option, not a dead-end — tool
  choice + CPU costs in `TOOLS.md`.)
- **PSF HOMOGENISATION — REFUSED BY THE OWNER, and the ruling binds wider
  than the technique.** Convolving each frame to a common, broader target
  PSF so corner and centre match is *"absolutely not a fix"*; *"the centre
  is most important and it would be stupid to take that for granted"*; it
  is *"not a suggested improvement but an accepted failure mode"*. **"Fix
  the root or it isn't a fix at all."** **The general form refused on
  sight: matching the corner to the centre by DEGRADING THE CENTRE, and any
  variant buying uniformity by spending quality at the good end of the
  field. Cropping and zone down-weighting are the same act by other means.
  Only a treatment that RECOVERS corner detail counts as a fix.**
  **The literature agrees formally — a measured information loss, not an
  aesthetic preference.** Zackay & Ofek 2017, *"How to coadd images?"* I
  and II (arXiv:1512.06872, 1512.06879): the optimal coadd applies a
  matched filter to each image USING ITS OWN PSF and only then sums —
  verbatim, *"methods that either match filter after coaddition, or perform
  PSF homogenization prior to coaddition, will result in loss of
  sensitivity."* Homogenisation is the OLDER standard (the DES/Pan-STARRS
  lineage it was proposed from) and the modern result supersedes it.
  **The argument that produced the proposal, kept because the flaw
  recurs:** *"every available response is identical under either aberration
  label"* — an equivalence that holds only by counting non-fixes
  (homogenise, down-weight, accept) as responses. **And the measured half
  that refutes it directly:** at the frame CENTRE there is no aberration
  gradient at all, so the chain is essentially the entire degradation
  there — ~12% of PSF width, of which the Lanczos4 kernel is 0.45% and the
  CLAMP pin 6.26% (one configuration, not a constant). A treatment that
  adds blur at the centre was proposed for a chain already softening the
  centre by ~12%. Implementation lead if the COADD question is ever
  reopened (orthogonal to deconvolution; availability UNVERIFIED here):
  `properimage` (quatrope/ProperImage), pip-installable.
- **NO INSTALLED TOOL DELIVERS A FIELD-VARIABLE ANISOTROPIC PSF
  CORRECTION — the MEASUREMENT is installed and the APPLIER is not, the
  treatment is owner-REFUSED either way, and a GLOBAL PSF cannot close a
  field gradient at all.** Three arms on one raw frame, identical Siril
  `findstar` settings (baseline FWHM major 2.340 px, roundness 0.807, 7083
  detections; roundness gradient across x −0.099):
  **Cosmic Clarity** (Stellar Only, auto-PSF, amount 0.50): 2.310 / 0.802 /
  6913, gradient **−0.093** — NULL, and ARCHITECTURAL rather than tuning:
  its models are named `radius_1/2/4/8` and radius is a scalar; an oriented
  elongation has no representation in its interface.
  **Siril `rl` global** (`-mul -iters=10`): a genuine 10% FWHM gain
  rank-matched on the brightest 1500 — but gradient **−0.091**, roundness
  slightly WORSE, 77% of detections destroyed. Not tuning: one PSF over the
  whole frame sharpens everywhere by the same factor and leaves a field
  variation where it was.
  **`makepsf stars` is the POSITIVE result**: per-band kernel ratios track
  findstar band for band (gradient −0.105 against −0.099) — Siril CAN
  measure the anisotropy; it applies one PSF per image. What remains with
  installed tools is per-REGION tiling and reassembly — pixel surgery on
  the deliverable — and the prior blocker is SNR, not seams: if regularised
  RL still eats the faint population, per-region RL will too.
  **The capability landscape, on grounds that cannot rot with an install**
  (an earlier form of this title — "no installed tool CAN correct" — was
  made false by this team's own PSFEx install within the same arc):
  (1) **NOTHING INSTALLED CAN APPLY THE KERNEL.** PSFEx computes
  homogenisation kernels (`homobasis` parameters CONSULTED, not merely
  declared — verified in its source) and writes `.homo.fits` cubes and
  stops; Bertin's manual names `PSFnormalize` (DES-internal, unpackaged) as
  the applier and SWarp never gained one — **measured from source AND from
  the installed binary: 0 of SWarp's 69 C files and 0 strings in
  `$(which SWarp)` match `homo|psfnormalize`, against `RESAMPLE` in 4 files
  / 43 strings as the positive control** (the control licenses reading the
  zero: config names DO survive as literals). `pypher` (the pip-installable
  applier) is absent from both interpreters here.
  (2) **The vendor calls homogenisation EXPERIMENTAL** — its own word
  (DOCTRINE).
  (3) **The doctrinal closure is the real one and is already held by the
  refusal entry above** — a closure resting on no tool fact cannot be
  falsified by an install.
  Bound worth attacking (MECHANISM, untested): a target PSF *narrower* than
  the field's best would be deconvolution rather than degradation, and
  PSFEx does not forbid it — not proposed: experimental, unregularised, no
  applier, and the regional-deconvolution blocker here is SNR.
  **The documented landscape is not this rig (DOCTRINE, unmeasured
  here):** RC-Astro's BlurXTerminator manual documents exactly this
  capability — 512×512 tiles processed independently *"to allow for
  non-stationary PSFs"*, correcting *"in limited amounts"* first/second
  order coma and astigmatism, trefoil, defocus, chromatic aberration,
  motion blur — on LINEAR input right after integration, needing stars
  throughout. **So the ceiling here is a PROCUREMENT boundary, not a
  physics one** (RC-Astro is PAID and the gap is deliberate — `TOOLS.md`).
  What this does NOT do: measure anything on our data, establish the
  correction works at our magnitudes, or make applying it a fix — a
  correction of unknown provenance applied to a finished product while the
  defect's cause is unidentified is the bandaid the owner has already
  refused; and our defect is measured IN-EXPOSURE in sensor coordinates
  while BXT runs on the stacked product where each output position holds a
  blend of sensor-position PSFs.
