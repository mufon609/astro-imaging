# How the field actually stacks UNTRACKED camera-lens wide-field — a cited reading

Answer to `RESEARCH_UNTRACKED_STACKING_PROMPT.md`. Research only: no processing, no
experiments, no pixel work was done for this document.

## Method, and one disclosure

Sources were read first and the repo second, as the prompt asked. Everything in
sections **A–G** was formed from primary sources (tool documentation, source code,
survey/instrument papers) plus forum searching; section **H** was written after
reading the repo and is the only place the repo is referenced.

**Disclosure:** `CLAUDE.md` is injected into every session in this workspace
automatically, so it was in context before the prompt was read. It could not be
un-read. It is a doctrine document, not a findings document — it contains no claim
about this dataset's symptom, no registration measurement, and no distortion
analysis — so the unanchored reading the prompt asked for is intact for A–G, with
two exceptions I will name explicitly where they occur (the installed lensfun and
darktable versions, and the existence of a fitted lens model, are facts I knew from
it and verified independently on the rig).

**Provenance tags used throughout:**
- **DOCUMENTED** — a tool's own docs, source code, or a primary paper.
- **COMMUNITY** — forum/user consensus, with the count of independent reports.
- **INFERRED** — my reasoning, with the arithmetic or the test that would settle it.

Two sources refused automated fetching (`pixinsight.com` returned 403 to the
fetcher, `cloudynights.com` returned 403 to both fetcher and curl). PixInsight was
retrieved successfully by direct request and is quoted from the full text.
Cloudy Nights could not be opened at all; the two CN threads cited below are marked
**COMMUNITY (search-index summary only — page not opened)** and should be treated as
the weakest evidence here.

---

## 0. The short answer

1. **The transform class is not the problem.** For an ideal rectilinear lens, drift
   *and* field rotation of a fixed camera are exactly a homography — 8 DOF, Siril's
   default. Nothing about untracked sky motion, at any magnitude, needs more than
   that. What breaks the homography is the lens's departure from a pinhole, and only
   that. (§A, §F.1)
2. **Untracked drift is the one case where lens distortion cannot cancel.** In a
   tracked sequence the field sits at the same sensor position every frame, so
   distortion is common-mode and registration never sees it. ASTAP states this
   assumption in its own docs. Drift breaks it: each star samples a *different* part
   of the distortion field in every frame. This is the mechanism the field
   consistently names for this data class. (§A, §E)
3. **A radial-only lens profile is provably insufficient for astrometric-grade
   work, and every astronomical standard abandoned radial models decades ago.** SIP,
   TPV and TNX are all general bivariate polynomials, not radial functions; HST needs
   a residual *lookup table* on top of the polynomial. Nobody in astronomy fits a
   radial model. (§C, §D)
4. **On this rig, lensfun cannot represent decentring at all.** The Adobe Camera
   Model (`acm`), the only lensfun model with tangential terms, does not exist in
   lensfun 0.3.4 — verified in the installed binary and in the v0.3.4 source. It
   appears only in v0.3.95+. (§D — this is the hardest single finding in this
   document.)
5. **But I do not think an uncorrected decentring term is the leading explanation of
   the reported symptom, and neither is registration failure.** Three sensor-fixed
   effects that are forced by physics and by the stack geometry — in-exposure trail
   length varying by 1.6× across this field, gnomonic plate-scale inflation toward
   the edges, and each output sky position averaging a *different, biased* track
   across the lens — all produce exactly the signature reported (fixed in sensor
   coordinates, R² high against position, R² ~0 against time) and none of them is
   fixed by any distortion model. They must be subtracted before anything is
   attributed. (§F)
6. **One stated number does not survive arithmetic.** 3.87 px/frame at 17.06 ″/px
   and a 3.00 s cadence is 22 ″/s of sky motion. The sidereal ceiling is 15.041 ″/s
   at δ=0 and 11.18 ″/s at δ=+42. The figure is 1.97× the physical prediction for
   this target. Conclusions that rest on it — above all *which* strip of the frame has
   partial coverage, and how wide it is — are resting on a number that is out by
   almost exactly 2×. (§F.4)

---

## A. What Siril itself recommends for this class

### A.1 There is no Siril workflow for untracked fixed-tripod stacking

**DOCUMENTED (negative).** I read the Siril 1.4.4 and 1.5.0 registration, plate
solving, stacking and sequence documentation, the 1.4.0 beta/RC release notes, the
tutorial index, and the command reference. **Siril documents no workflow, tutorial,
recommended parameter set, or even a paragraph for untracked / fixed-tripod
wide-field stacking.** There is no statement anywhere about how much sky movement
one registration can absorb, and no criterion for splitting a long drifting run.
The word "untracked" does not appear. This is a clean negative and I am not going to
pad it: the class is undocumented by the tool.

Sources: [Registration 1.4.4](https://siril.readthedocs.io/en/stable/preprocessing/registration.html),
[Registration 1.5.0](https://siril.readthedocs.io/en/latest/preprocessing/registration.html),
[Platesolving 1.4.4](https://siril.readthedocs.io/en/stable/astrometry/platesolving.html),
[Stacking 1.4.4](https://siril.readthedocs.io/en/stable/preprocessing/stacking.html),
[Commands 1.4.4](https://siril.readthedocs.io/en/stable/Commands.html),
[Sequences 1.4.4](https://siril.readthedocs.io/en/stable/Sequences.html),
[1.4.0 Beta 1 notes](https://siril.org/download/2025-04-26-siril-1-4-0-beta1/),
[tutorials index](https://siril.org/tutorials/).

### A.2 Transform classes, and what the docs say about sufficiency

**DOCUMENTED.** Siril offers five classes, quoted from the registration page:

| Class | DOF | Siril's own words |
|---|---|---|
| Shift | 2 | "well-suited for images with no distortion, no scaling and no field rotation" |
| Euclidean | 3 | "for images with no distortion, no scaling" |
| Similarity | 4 | "more rigid mapping than homography, well-suited for images with no distortion" |
| Affine | 6 | "well-suited for images with **little** distortion" |
| Homography | 8 | "the default … **strongly recommended for wide-field images**" |

The only statement about a global transform becoming insufficient is the implicit
one in that ladder: distortion is the axis along which the classes are ordered, and
homography is the top of it. There is no documented "beyond this, a global transform
fails" criterion. `-transf=` selects the class; `homography` is the default
([Commands](https://siril.readthedocs.io/en/stable/Commands.html)).

**INFERRED, and important:** the ladder is misleading for this case. A homography
is not merely "good enough" for untracked drift — for a pinhole camera it is
*exact*, at any drift magnitude and any field rotation, because pure rotation about
the camera centre induces the planar homography `H = K R K⁻¹` independent of scene
depth ([OpenCV homography tutorial](https://docs.opencv.org/4.13.0/d9/dab/tutorial_homography.html),
[Szeliski, *Image Alignment and Stitching*, §2.2](https://pages.cs.wisc.edu/~dyer/cs534/papers/szeliski-alignment-tutorial.pdf);
standard result, Hartley & Zisserman). A fixed camera watching the sky *is* a camera
undergoing pure rotation relative to the scene. So the residual after a global
homography is, by construction, **only** the lens's departure from rectilinearity
(plus refraction, plus sampling). Choosing a richer transform class is therefore not
the fix; the transform class is already exactly right.

### A.3 `-disto=` — what it is for, what it consumes

**DOCUMENTED**, quoted verbatim from the 1.4.4 command reference:

> `-disto=` uses distortion terms from a previous platesolve solution (with a SIP
> order > 1). It takes as parameter either `image` to use the solution contained in
> the currently loaded image, `file` followed by the path to the image containing the
> solution or `master` to load automatically the matching distortion master
> corresponding to each image. When using this option, the polynomials are used both
> to correct star positions before computing the transformation and to undistort the
> images when output images are exported.

And on the two-stage application, from the registration page:

> Distortion coefficients handled by Siril follow SIP convention. This convention
> assumes that the pixel coordinates need to be corrected BEFORE trying to map them
> through a linear transformation.

> When exporting the registered image, it is first corrected for distortion and then
> linearly projected to be aligned to the reference image. Note that this actually
> occurs in a single operation … so as to avoid interpolating pixel values twice.

Where the solution comes from: `platesolve` and `seqplatesolve` both accept
`-order=` (1–5, "up to fifth-order polynomial distortions, following the SIP
convention"; the GUI default is cubic) and `-disto=<file>` to *save* the solution as
a `.wcs` distortion file. `seqplatesolve` additionally: "Using this command will
update registration data unless the option `-noreg` is passed."

So the documented pipeline shape is: **solve with SIP → save/point at a distortion
solution → register consuming it.** That is a *shared, static, sensor-fixed* model,
applied identically to every frame — architecturally the same choice SCAMP makes for
the instrument-stable part of its distortion (§C.2).

Caveat, **COMMUNITY (1 report, unanswered)**: a user on discuss.pixls.us hit
`Unknown distortion type ps_distortion.wcs, aborting` when passing the file
produced by `seqplatesolve -disto=` straight into `register -disto=`, with no
developer reply on the thread —
[discuss.pixls.us #55120](https://discuss.pixls.us/t/using-distortion-files-to-correct-image-in-siril-1-4-0/55120).
The argument grammar is `-disto=file <path>` / `-disto=master` / `-disto=image`, not
`-disto=<path>`, which is the likely cause, but it is worth knowing the trap exists.

### A.4 Astrometric registration

**DOCUMENTED.** "Introduced in version 1.3, this is the preferred mode for
assembling mosaics or images with little overlap … can also be useful to register
stacks issued from different set-ups", and critically:

> Undistortion will be applied as defined when platesolving the sequence, meaning if
> the images were plate-solved using a SIP order larger than 1, then undistortion
> will automatically be included.

This is a genuinely different registration route: alignment is computed **through
the plate solution of each frame**, not by fitting a 2-D transform to star pairs. It
therefore carries each frame's *own* geometry, including whatever asymmetric terms
that frame's SIP fit absorbed.

**INFERRED (needs a 5-minute headless probe):** the docs never name a
`register -astrometric` flag, and the string "astrometric" does not occur in the
1.4.4 command reference at all. The headless route appears to be
`seqplatesolve <seq> -order=N` (which "will update registration data") followed by
`seqapplyreg <seq> -framing=…`. I could not confirm this from documentation and I am
not going to assert it as fact.

### A.5 Framing and the reference frame

**DOCUMENTED.** `seqapplyreg -framing={current|min|max|cog}`:
`max` = bounding box of all frames; `min` = "crops each image to the area it has in
common with all images of the sequence"; **`cog` = "determines the best framing
position as the center of gravity (cog) of all the images."**

Reference frame default: "if the sequence has already been registered, it is the
best image, in term of lowest FWHM or highest quality …; otherwise, it is the first
image of the sequence that is not excluded." `-2pass` changes this to "choosing the
best reference frame using a function based on FWHM and the number of stars".
`setref` sets it manually.

**This is the most under-appreciated fact in the Siril documentation for this data
class.** Both defaults — first frame, or best-FWHM frame — are chosen without any
reference to *position in the drift*. For a drifting sequence the reference frame
selects which window of sky the output canvas covers, and therefore *which sky
strips are covered by only a few frames*. A first-frame or best-FWHM reference can
put the output window at one end of the drift, where one edge of the canvas holds
sky that left the sensor early and is consequently built from a small, and
systematically edge-of-lens, subset of frames. `-framing=min` and `-framing=cog`
exist precisely to attack this and are not mentioned in any registration guidance.

**COMMUNITY (1 report, search-index summary only — page not opened):** a Cloudy
Nights thread on Siril reference-frame choice contains, per the search index, "When
using only a tripod and camera, there is a lot of drift, and some pictures may be
too far drifted to be aligned, which is why choosing a reference frame that
represents the 'average' position of all frames would stack better" —
[CN 883376](https://www.cloudynights.com/topic/883376-siril-question-why-choose-another-reference-frame-in-the-plot-screen/).
Same conclusion, arrived at by a user rather than by the tool's documentation.

### A.6 Splitting a long run

**DOCUMENTED (negative).** Siril nowhere recommends splitting a long untracked run
into shorter registration units, and states no criterion for doing so. The
capability to combine the pieces afterwards exists (astrometric registration is
documented as useful "to register stacks issued from different set-ups"), but the
recommendation does not.

---

## B. How PixInsight handles it

PixInsight is the reference implementation here and its documentation is
unusually explicit about mechanism. Quotes from
[Arbitrary Distortion Correction with StarAlignment](https://www.pixinsight.com/tutorials/sa-distortion/index.html)
(Juan Conejero, PTeam) and
[New Plate Solving Distortion Correction Algorithm](https://pixinsight.com/tutorials/solver-distortion/)
(2019).

**DOCUMENTED — the model.** StarAlignment's distortion correction is not a
polynomial at all:

> StarAlignment's distortion correction algorithm uses two-dimensional surface
> splines, also known as *thin plates*, as a non-rigid mathematical model to describe
> the geometrical transformation necessary to register two images.

> Thin plates are also necessary to correct for **differential distortion**, which is
> the kind of deformations that must be corrected to build accurate wide-field
> mosaics.

Since November 2013 these are **approximating** rather than interpolating splines,
with a `Spline smoothness` parameter (default 0.25), explicitly because interpolating
splines over-fit noisy star positions: "What you are looking at … is the result of
excessive local adaptation, or excessive flexibility in the registration model."
This is a warning worth carrying: a maximally flexible distortion model fitted to
imperfect star centroids makes registration *worse*, and PixInsight learned it the
hard way on a wide-field mosaic.

**DOCUMENTED — star matching.** Triangle similarity was replaced by polygonal
descriptors (default: pentagons) precisely because "Triangle similarity is invariant
to some affine transformations … Clearly, this excludes any form of local
distortion, and also excludes more general linear transformations such as projective
transformations (homographies)."

**DOCUMENTED — distortion models.** Externally-defined distortion models are
supported: plain CSV, header `2DSurfaceSpline|ThinPlate, <order 2..5>`, then ≥3 nodes
of `x, y, dx, dy` — "where `<x>,<y>` are the image coordinates of the point of
application of a distortion vector, and `<dx>,<dy>` define the vector's magnitude and
direction." A model "can be used to pre-correct the images for optical aberrations
such as field curvature, lateral chromatic aberration and other arbitrary
geometrical transformations", after which `Undistorted Reference` is enabled because
the reference is now undistorted. Order 2 is recommended; "Higher order models can
easily become unstable and are thus discouraged for normal use."

**What it models that a radial profile does not:** everything. The model is a vector
field sampled at arbitrary points — it has no symmetry assumption whatsoever, radial
or otherwise. Notably, the tutorial's own reference [5] is
**Brown, D. C. (1966), *Decentering Distortion of Lenses*, Photogrammetric
Engineering 32(3), 444–462** — PixInsight cites the founding decentring paper while
demonstrating that its own model does not need Brown's parameterisation at all.

**DOCUMENTED — plate solving.** The astrometric solution also uses approximating
thin plate splines, with "shape-preserving surface simplifiers" raising the usable
star count from 5,000 to 25,000: "we can work with a small subset of stars where
distortion is low (typically, the central areas of the image), while much more stars
are used where distortion is high (typically, the corners of the image)." Measured
result on a 500 mm f/2.8 wide-field CCD frame at 3.658 ″/px: a linear WCS is wrong
by **4.83″ and 3.43″** at one corner star, thin-plate-spline solution wrong by
**0.05″ and 0.06″** — "better than 0.1 arcseconds consistently throughout the entire
image … less than 0.03 pixels."

**DOCUMENTED — when PixInsight says NOT to use it.**

> Unless it is really necessary, don't use the distortion correction feature. In
> general, distortion correction is only necessary in two cases: Registration of
> images acquired with different telescopes or lenses. Wide-field mosaics.
> If the images being registered are not subject to differential distortions,
> applying distortion correction won't provide more accuracy.

**INFERRED:** an untracked drifting run at 70 mm is squarely inside PixInsight's own
"differential distortions" category — different parts of the same lens are being
mixed at each output position, which is exactly the mosaic condition — even though
it is a single set of frames from a single lens. That reframing (a drifting stack is
a mosaic-like problem, not a dithered-stack problem) is the most useful single idea
I took from PixInsight's documentation.

**Verification method worth stealing, DOCUMENTED:** subtract registered from
reference with PixelMath and inspect residuals; PixInsight distinguishes registration
error (residual with the brightness peak still present) from lateral chromatic
aberration (two coloured lobes with the peak removed) by residual morphology.

---

## C. What the astronomical standards do

### C.1 The representations: SIP, TPV, TNX — none of them radial

**DOCUMENTED.** SIP (Shupe et al. 2005, ADASS XIV, P3.2.18,
[PDF](https://irsa.ipac.caltech.edu/data/SPITZER/docs/files/spitzer/shupeADASS.pdf))
defines distortion as *general bivariate polynomials in pixel coordinates*:

> We define `A_p_q` and `B_p_q` as the polynomial coefficients for polynomial terms
> `u^p v^q`. Then `f(u,v) = Σ A_p_q u^p v^q, p+q ≤ A_ORDER`, `g(u,v) = Σ B_p_q u^p v^q,
> p+q ≤ B_ORDER`.

with `[x y]ᵀ = CD · [u+f(u,v), v+g(u,v)]ᵀ`. Every cross term `u^p v^q` is free and
independent. **A radial model is a one-parameter-family special case of this;
SIP does not assume symmetry of any kind and represents decentring, shear, and
arbitrary asymmetry natively.** The motivating case was itself non-static: "the
distortion changes with scan mirror position, and hence from one image to the next."

TPV (SCAMP/WCSLIB) is the same idea applied in *intermediate world* coordinates
rather than pixel coordinates — Shupe et al. 2012,
[More Flexibility in Representing Geometric Distortion in Astronomical Images](https://web.ipac.caltech.edu/staff/shupe/reprints/SIP_to_PV_SPIE2012.pdf):
SCAMP/SExtractor compute distortion "in celestial coordinates with polynomial
coefficients stored in the FITS header with the `PV i_j` keywords" while
Astrometry.net "solves for distortion in pixel coordinates using the SIP convention".
The paper's contribution is a lossless converter between them, so the two families
are inter-translatable. TNX is the IRAF-lineage equivalent using Chebyshev/Legendre
basis polynomials; same general-polynomial character.

None of the three is radial. **There is no radial distortion convention in FITS.**

### C.2 Derived per exposure, or shared? Both — deliberately split

**DOCUMENTED.** This is the design question, and the surveys answer it the same way
twice, independently.

SCAMP (Bertin 2006, ADASS XV, ASP Conf. Ser. 351, 112,
[PDF](https://adsabs.harvard.edu/pdf/2006ASPC..351..112B)):

> with the MEGACAM instrument one can make the assumption that the high order part of
> the astrometric distortion pattern is stable within a given observing run, while the
> linear part varies globally over the field of view from exposure to exposure. This
> allows much more robust solutions to be computed, especially when crowded or empty
> images are involved.

Implemented via `STABILITY_TYPE` (`INSTRUMENT` / `EXPOSURE` / `PRE-DISTORTED`),
`DISTORT_DEGREE` for the chip-constant polynomial and `FOCDISTORT_DEGREE` for the
mosaic-wide exposure-dependent one; SCAMP "first reads all image headers and then
splits the exposures into a series of astrometric *contexts*", each isolating epochs
where the focal plane is stable. Astrometric engine is WCSLIB "to which we added
support for the TPV description of polynomial distortions"
([SCAMP docs](https://scamp.readthedocs.io/en/latest/), 2.6.2).

Pan-STARRS reaches the identical architecture (Magnier et al. 2020,
[Pan-STARRS Photometric and Astrometric Calibration](https://iopscience.iop.org/article/10.3847/1538-4365/abb82a),
[ar5iv](https://ar5iv.labs.arxiv.org/html/1612.05242)): third-order polynomials chip →
focal plane (static, per-camera), plus **a single pair of polynomials per exposure**
mapping focal plane → tangent plane, and — note this — those per-exposure polynomials
"account for optical distortion in the camera **and distortions from changing
atmospheric refraction across the field of the camera**, with a single pair of
polynomials used for each exposure since these effects are smooth across the field."

**The standard is therefore: a high-order static term shared across the run, plus a
low-order per-exposure term.** Neither alone. Refraction is not modelled physically;
it is absorbed into the per-exposure low-order term.

### C.3 The polynomial is not the end of the road

**DOCUMENTED.** HST is the clearest statement that even a *general* high-order
polynomial is insufficient at sub-pixel level. AstroDrizzle carries three distinct
distortion objects: `IDCTAB` (high-order polynomial coefficients), `NPOLFILE`
(a 2-D lookup table of *residuals from* the polynomial, per filter), and `D2IMFILE`
(detector-level column irregularities) —
[HST: How Distortions are Represented in AstroDrizzle](https://hst-docs.stsci.edu/drizzpac/chapter-4-astrometric-information-in-the-header/4-2-how-distortions-are-represented-in-astrodrizzle),
[STScI/ACS distortion](https://www.stsci.edu/hst/instrumentation/acs/data-analysis/distortion).
The CD matrix + SIP are quoted as good to ~0.1 px, with the lookup tables carrying
what remains. If a *space telescope's* polynomial needs a residual lookup table, no
consumer lens is going to be adequately described by three radial coefficients.

### C.4 Coaddition: distortion is only half the problem

**DOCUMENTED, and this is the part of the standards literature that the prompt's two
hypotheses do not reach.** Surveys do not just align frames; they *homogenise the
PSF* before coadding, because objects land on different focal-plane positions in
different exposures.

Dark Energy Survey ([DES Data Management](https://arxiv.org/pdf/1109.6741),
[DES Image Processing Pipeline](https://arxiv.org/pdf/1801.03177)): with each object
observed at ~10 different focal-plane locations, "if images are simply coadded,
discontinuities in the PSF variation as a function of position within the coadd image
result", and non-homogenised coaddition "can introduce sharp PSF discontinuities on
the ~0°.1 scale that are difficult to model with conventional polynomial approximation
techniques". The fix is to convolve every input to a common circular Moffat target
PSF using position-dependent PSFEx kernels.

Pan-STARRS (Price & Magnier 2019,
[Pan-STARRS PSF-Matching for Subtraction and Stacking](https://arxiv.org/abs/1901.09999)):
PSF-matching "is also used to homogenize the PSF of inputs to stacks, resulting in
improved photometric precision compared to regular coaddition."

SWarp/TERAPIX handles the complementary half: per-pixel weight maps, with edge-flagged
pixels weighted to zero, so that partially-covered and marginal-quality regions do not
silently contaminate the coadd
([SWarp](https://www.astromatic.net/software/swarp/), [TERAPIX pipeline](https://adsabs.harvard.edu/pdf/2002ASPC..281..228B)).

**The standard practice, stated plainly:** align with a general polynomial that is
partly shared and partly per-exposure; carry per-pixel weights; and *homogenise the
PSF across the focal plane before coadding*. Amateur tools implement the first, some
of the second, and none of the third.

---

## D. The specific technical question: radial-only vs decentring

### D.1 Is a radial-only model adequate for astrometric-grade work?

**DOCUMENTED — no, and the field settled this before FITS existed.** Brown's
*Decentering Distortion of Lenses* (1966) is the reference PixInsight itself cites;
the Brown–Conrady model exists precisely because radial terms leave a systematic
residual when lens elements are not perfectly co-axial. OpenCV states the physical
cause in one line: tangential distortion "occurs because the image-taking lense is
not aligned perfectly parallel to the imaging plane"
([OpenCV camera calibration](https://docs.opencv.org/4.x/dc/dbb/tutorial_py_calibration.html)),
with

```
x_d = x + [2·p1·x·y + p2·(r² + 2x²)]
y_d = y + [p1·(r² + 2y²) + 2·p2·x·y]
```

Where the literature says radial-only breaks down: the vision literature is explicit
that radial-plus-tangential itself has limits — Brown–Conrady "cannot represent the
complex distortion in cameras with off-axis optical elements", for which bi-cubic or
rational models with more DOF are preferred
([Calcam calibration theory](https://euratom-software.github.io/calcam/html/intro_theory.html),
[Tangram Vision on Brown–Conrady](https://www.tangramvision.com/blog/the-innovative-brown-conrady-model)).
The astronomical answer is the same one arrived at from the other direction: skip the
physical parameterisation entirely and fit a general polynomial (§C.1) or a spline
(§B), which contains radial *and* decentring *and* everything else as special cases.

**INFERRED:** for this problem, "does the model include p1, p2" is the wrong
question. The right question is "is the model general in 2-D or symmetric about a
point", and every astronomy tool has answered *general* since 2005. Fitting
Brown–Conrady would be adopting photogrammetry's 1966 answer when the astronomical
standard is strictly more expressive and is already implemented in the tools on this
rig.

### D.2 Which Linux/free/headless tools can fit or apply a non-radial model

| Tool | Model | Fits? | Applies? | Non-radial? |
|---|---|---|---|---|
| **astrometry.net** `solve-field` | SIP, general bivariate polynomial | yes, per image, `--tweak-order` | writes WCS; other tools apply | **yes, fully** |
| **Siril** `platesolve`/`seqplatesolve` | SIP order 1–5 | yes, per image or per sequence | yes, `register -disto=` | **yes, fully** |
| **SCAMP** | TPV/PV, shared + per-exposure | yes | via SWarp | **yes, fully** |
| **PixInsight** StarAlignment | thin plate spline vector field | yes | yes | **yes, arbitrary** (not installed) |
| **OpenCV** `calibrateCamera` | Brown–Conrady k1..k6, **p1,p2**, thin-prism s1..s4, tilted-sensor τx,τy | yes | yes (`undistort`) | **yes** |
| **Hugin** `align_image_stack` | panotools a,b,c radial + **d,e centre shift** + g,t shear | yes (`-d`, `-i`) | yes (`-a` writes aligned TIFFs) | **partly** — centre shift ≈ first-order decentring, plus shear |
| **lensfun ≤ 0.3.4** | poly3 / poly5 / ptlens | (external) | yes | **NO — radially symmetric only** |
| **lensfun ≥ 0.3.95** | + `acm` (Adobe) with k4,k5 | (external) | yes, correction direction only | **yes, tangential** |
| **ASTAP** | SIP, 3rd order | yes (solver option) | for astrometry, **not** for stacking | yes, but see below |
| **GraXpert** | n/a — background extraction / denoise / deconvolution only | no | no | n/a |

**DOCUMENTED, and the sharpest finding in this document — lensfun on this rig cannot
express decentring.** lensfun's models are "none", "poly3", "poly5", "ptlens", "acm";
the first four are radial functions of `r_u` alone. Only `acm` (Adobe Camera Model)
carries tangential terms — from the lensfun manual, in units of focal length:

```
x_d = x_u(1 + k1·r_u² + k2·r_u⁴ + k3·r_u⁶) + 2x_u(k4·y_u + k5·x_u) + k5·r_u²
y_d = y_u(1 + k1·r_u² + k2·r_u⁴ + k3·r_u⁶) + 2y_u(k4·y_u + k5·x_u) + k4·r_u²
```

(`k4`, `k5` are Brown's decentring pair in Adobe's normalisation —
[lensfun manual, lfDistortionModel](https://lensfun.github.io/manual/latest/group__Lens.html)).

I verified against the installed library rather than trusting the docs:

- `strings /usr/lib/x86_64-linux-gnu/liblensfun.so.0.3.4` contains `poly3`, `poly5`,
  `ptlens` — and **no** `acm`.
- lensfun **v0.3.4** `libs/lensfun/mod-coord.cpp` contains **zero** occurrences of
  `ACM`; **v0.3.2** likewise zero; **v0.3.95** has nine.
- Installed package: `liblensfun1 1:0.3.4-2+b1`.

In current lensfun master, `lfModifier::EnableDistortionCorrection` dispatches
`LF_DIST_MODEL_ACM → ModifyCoord_Dist_ACM` in the forward direction but, when
`Reverse` is set, emits `"[lensfun] \"acm\" distortion model is not yet implemented
for reverse correction"` and does nothing
([mod-coord.cpp](https://raw.githubusercontent.com/lensfun/lensfun/master/libs/lensfun/mod-coord.cpp)).
The forward direction is the one image correction uses, so `acm` *is* usable for
undistorting — **on lensfun ≥ 0.3.95 only**.

**Consequence:** on lensfun 0.3.4 there is no way — none, at any effort — to apply a
decentring correction through darktable. Hypothesis 1 in the prompt cannot even be
*tested* on this rig through the lens-profile route without upgrading lensfun to
0.3.95+ and hand-authoring an `acm` database entry with `k1..k5`. And note the
normalisation trap: ACM coordinates are "measured in units of the focal length of the
lens", unlike the other models.

**Hugin is the free non-radial option that is actually installed-able today.**
`align_image_stack` optimises `-d` "radial distortion for all images, except for
first" and `-i` "image center shift for all images, except for first"
([Debian man page](https://manpages.debian.org/testing/hugin-tools/align_image_stack.1.en.html)).
A displaced distortion centre is the first-order equivalent of decentring — it makes
the correction field asymmetric — and `g,t` shear exists in the panotools lens model
([Lens correction model](https://wiki.panotools.org/Lens_correction_model)). Pat David
recommended exactly this route to a Siril user hitting corner trails
([discuss.pixls.us #20991](https://discuss.pixls.us/t/siril-needs-distortion-correction-in-stacking/20991)).
Its weakness for this data: it optimises lens parameters *per image except the first*,
which for a fixed lens is the wrong constraint — it lets a static lens property vary
frame to frame and absorb sky motion.

**ASTAP states the tracked-case assumption explicitly, and it is the assumption this
data violates** ([ASTAP](https://www.hnsky.org/astap.htm)):

> Using this option the solver will add 3th order SIP polynomial coefficients to the
> header to cope with image distortion. **This option is not relevant for stacking
> since the distortion for each frame will be the same. It is only important for
> positional astrometry.**

That sentence is correct for a tracked sequence and false for a drifting one. It is
the cleanest available articulation of *why* untracked wide-field is a special case:
distortion is common-mode only if the field does not move across the sensor.

### D.3 Feeding such a model into Siril

**DOCUMENTED — yes, and this is Siril's intended mechanism.** SIP is a general
polynomial (§C.1), so a decentring/asymmetric term needs no special support: it is
representable in the same `A_p_q`/`B_p_q` coefficients Siril already consumes. Three
supply routes, all documented:

1. `platesolve … -order=3..5 -disto=<out.wcs>` on one representative frame, then
   `register <seq> -2pass -disto=file <that frame>` — one shared static model,
   the SCAMP `STABILITY_TYPE=INSTRUMENT` shape.
2. `seqplatesolve <seq> -order=3..5` then `register <seq> -disto=master` — a
   per-frame model, matched per image via the master-distortion path-parsing pattern
   documented in [Path parsing](https://siril.readthedocs.io/en/stable/Pathparsing.html).
3. Astrometric registration, where "undistortion will be applied as defined when
   platesolving the sequence" (§A.4).

An externally-fitted model (OpenCV, Hugin) would have to be *converted into SIP
coefficients written to a FITS/WCS header* to enter Siril; there is no documented
import path for a lens-profile format. The SIP↔PV converters exist
([Shupe et al. 2012](https://web.ipac.caltech.edu/staff/shupe/reprints/SIP_to_PV_SPIE2012.pdf))
but nothing converts lensfun/Adobe/PTLens profiles to SIP.

---

## E. Is this a known problem?

### E.1 What IS widely reported

**COMMUNITY — corner/edge star trails in wide-field stacks, attributed to lens
distortion. At least 5 independent reports across 3 sites, plus 2 Siril developers
confirming the mechanism.**

- Nathan Myhrvold, 250 frames, 40 mm f/1.6: stars in the corners become "short star
  trails" in Siril while APP is clean; he attributes it to Siril not modelling lens
  distortion during registration. Siril developer **Vincent Hourdin (vinvin)**:
  *"we know, that's a limitation, and it's not going to happen soon, it's not even in
  the list of things to be implemented."* Developer **lock042**: *"distorsion is not
  an easy issue. If lens can be easily characterized it is not the same for
  telescopes. So we know about it, but it is not a priority."*
  ([discuss.pixls.us #20991](https://discuss.pixls.us/t/siril-needs-distortion-correction-in-stacking/20991))
  — note this thread predates 1.4; Siril has since shipped SIP distortion in
  registration.
- Untracked tripod, Nikon D7200, 42 mm, 90 × 8 s: "severe distortion of the stars at
  the corners", worst in the lower right corner, and less crisp than Sequator.
  lock042: *"Currently Siril has no such a reduce distorsion feature. So it is better
  to use software that can do it if your images are too distored."*
  ([discuss.pixls.us #35487](https://discuss.pixls.us/t/stacking-non-tracked-images-got-severe-distortion/35487))
- Siril issue **#182**, "Global registration used is often to poor with wide field":
  the algorithm "only uses linear fit. This is not good when images are distorded
  (generally for wide fields)" → resolved by adopting homography in 0.9.7
  ([gitlab #182](https://gitlab.com/free-astro/siril/-/issues/182)).
- Live feature requests confirming distortion modelling is now the active frontier:
  **#1606** "Allow the creation and usage of one distortion model per color channel"
  and **#1908** "CFA-independent distortion model estimation", both open.
- Cloudy Nights, "Wide-field edge distortion when stacking Milky Way subs"
  ([CN 724742](https://www.cloudynights.com/forums/topic/724742-wide-field-edge-distortion-when-stacking-milky-way-subs/))
  and "Wide-field Milky Way is distorted" ([CN 940003](https://www.cloudynights.com/forums/topic/940003-wide-field-milky-way-is-distorted/))
  — **search-index summary only, pages not opened**: the reported mechanism is that
  "geometric distortion in the lens can cause problems as the stars move — the
  position of some stars will change more than others due to the distortion", and that
  images "get worse the more you stack". Remedy offered: correct distortion on each
  sub before stacking.

So: **the general phenomenon — wide-field camera-lens stacks degrading at the
edges/corners because lens distortion is not modelled during registration — is
common, named, and has a known remedy.**

### E.2 What is NOT reported — a clean negative

I searched Cloudy Nights, discuss.pixls.us, Stargazers Lounge, DPReview, the Siril
GitLab issue tracker (via API, for `untracked`, `tripod`, `drift`, `wide field`,
`distortion`) and the lensfun issue tracker. **I found no report anywhere of the
specific signature described in the prompt: softness and elongation concentrated on
ONE side of the sensor, with the opposite side clean, in an untracked stack.** Every
report I found describes *radially symmetric* degradation — corners and edges, all of
them, worst at the corners. Not one describes a left/right asymmetry.

Siril's issue tracker returns **zero** issues matching "untracked" and one
tangentially related match for "tripod" (an Astrotracer file-format issue).

There is also no documented amateur discussion of the mechanism I consider most
likely (§F.3) — that in a drifting stack each output sky position averages a
*different, biased* track across the lens's PSF field. The professional analogue is
documented (DES/Pan-STARRS PSF discontinuities from focal-plane position variation,
§C.4); the amateur translation of it appears nowhere I could find.

**This asymmetry is unusual, and the absence of reports is itself informative:** it
argues against explanations that would apply to everyone with a zoom lens (which
would be widely reported), and towards explanations specific to *this* geometry —
this declination, this altitude, this drift direction, this reference frame — or to a
sample-specific lens fault.

---

## F. What I think the sources point at

Formed before weighing the prompt's two hypotheses, then reconciled with them.

### F.1 What can be ruled out on documented grounds

- **The transform class.** A homography is exact for pure camera rotation (§A.2).
  Drift magnitude and field rotation, alone, cannot break it. Ruled out.
- **Refraction.** `R ≈ 58.3″·tan z`. At 75° altitude the field spans z ≈ 0.7°–29.3°,
  so refraction displaces stars by 0.7″–32.7″ across the field — but almost all of
  that is a linear compression that any affine or projective transform absorbs. The
  *nonlinear* residual (deviation of `tan z` from a straight line across the field) is
  ≈ 1.1″ ≈ **0.065 px**. Consistent with the 0.09 px stated in the prompt, and
  negligible. Ruled out. (**INFERRED**, arithmetic above; the standards fold refraction
  into a per-exposure low-order term for exactly this reason, §C.2.)

### F.2 Two sensor-fixed effects that are forced by physics, and are not distortion

Both are **INFERRED** but rest only on documented rates and standard projection
geometry. Both produce R² high against sensor position and R² ≈ 0 against time —
the same signature the prompt reports as evidence for hypothesis 1.

**(a) In-exposure trail length varies by 1.6× across this field.** A star at
declination δ moves at `15.041·cos δ` ″/s — the same `cos δ` that appears in the NPF
rule's declination term ([PhotoPills](https://www.photopills.com/calculators/spotstars),
[National Parks at Night on NPF](https://www.nationalparksatnight.com/blog/2019/4/13/new-rule-for-shooting-the-sharpest-stars-in-the-sky)).
At 2.5 s and 17.06 ″/px:

| position | δ | trail |
|---|---|---|
| field centre | +42.0° | 1.64 px |
| edge toward the equator | +27.7° | **1.95 px** |
| edge toward the pole | +56.3° | **1.22 px** |

A **0.73 px, 1.6× monotone gradient in the in-exposure smear, fixed in sensor
coordinates, present in every single frame, and unremovable by any registration or
distortion model.** The measured side-to-side difference is 0.27 px FWHM and 0.032 in
roundness; this effect is of the right order to produce it (a naive quadrature
estimate over-predicts, which is expected — the smear is a top-hat convolved with the
optical PSF, and Siril fits an elliptical Gaussian to the result).

**Its gradient runs along the declination direction, which is perpendicular to the
drift direction.** That is a decisive, free discriminator: if the FWHM gradient is
along the drift axis, this is not the cause; if it is along the pole direction, it
is. Both directions are already known from the plate solutions and the homographies.

**(b) Gnomonic plate-scale inflation.** For a rectilinear lens, `r = f·tan θ`, so the
plate scale in ″/px falls toward the edges and a fixed *angular* blur covers more
*pixels*: ×sec²θ radially, ×sec θ tangentially. At the long-edge midpoint
(θ = 14.3°): **+6.5% radial, +3.2% tangential**; at the corner (θ = 17.3°): +9.7% /
+4.7%. This alone inflates a 2.30 px centre FWHM to ~2.45 px at the mid-edge and
drops roundness by ~3% — with no lens defect of any kind. It is radially symmetric,
so it cannot produce the asymmetry, but it is a floor that must be subtracted before
any edge is called "soft".

### F.3 The mechanism I would put first, which is neither of the prompt's two

**INFERRED.** In a drifting stack, each output sky position is built from a
*different and systematically biased* set of sensor positions.

A star that sits at the exit edge of the reference frame was near that edge for its
whole life on the sensor and then left: **it was only ever imaged through the outer
zone of the lens.** A star at the entry edge of the reference frame traverses inward
over the run and is imaged through the outer zone, the mid-field, and the centre. The
stacked PSF at each output position is the average of the lens's PSF along that
position's track. So even with *perfect* geometric registration, output PSF quality
varies systematically with position in the reference frame, one-sidedly, fixed in
sensor coordinates, and independent of elapsed time.

This is the amateur translation of the documented survey problem: DES observes each
object at ~10 focal-plane positions and gets "discontinuities in the PSF variation as
a function of position within the coadd image" unless the PSF is homogenised (§C.4).
The untracked case is worse than the survey case in one specific way: survey dithers
are *random*, so focal-plane position averages out; here the motion is *monotonic*,
so it does not average — it produces a ramp.

**Why this matters more than the distinction between the prompt's two hypotheses:**
no distortion model fixes it. SIP, thin plate splines, `acm` with k4/k5 — all of them
correct *geometry* (where the star lands). None corrects *blur* (what shape the star
has when it lands). If the dominant term is PSF-track-averaging, fitting a decentring
model is effort spent on the wrong quantity, and the measurement will come back a
clean NULL.

**The test, and it is cheap:** the model predicts output FWHM at position `p` is the
mean of the single-frame PSF over `p`'s track. Measure single-frame FWHM/roundness vs
sensor position on **one** frame (`findstar` on a raw calibrated frame, no
registration). Then predict the stacked pattern by averaging that field along each
track — the tracks are already known from the homographies. If the prediction
reproduces the 25 measurements, the story is PSF averaging, not distortion.

### F.4 The number that does not survive arithmetic

**INFERRED, and please check this before anything else.**

The prompt states a drift of **3.87 px/frame** with plate scale 17.06 ″/px and a
3.00 s cadence. That is 66.0 ″ per frame = **22.0 ″/s of sky motion**.

The sidereal rate is 15.041 ″/s at δ = 0 and `15.041·cos δ` elsewhere. At δ = +42°
it is **11.18 ″/s = 1.96 px/frame**. The fastest-moving point anywhere in this field
(δ ≈ +27.7°) reaches 13.31 ″/s = 2.34 px/frame. **No point on this sensor can move
faster than ~2.3 px/frame.** 22 ″/s is 1.46× the hard physical ceiling at the
celestial equator, and 1.97× the prediction for this target's declination.

That factor is suspiciously close to exactly 2. Candidate explanations: the drift was
differenced across a two-frame baseline; or it is a peak-to-peak figure across the
sensor rather than a per-frame displacement; or the plate scale or cadence used in
the conversion is not the one stated.

**Why it matters, concretely:** the total sky translation over the run is
`15.041·cos δ·1500 s`, i.e. **734–1170 px depending on declination — 12–19% of the
6064 px sensor width**, not the 1935 px (32%) implied by 3.87 px/frame. The width of
the partial-coverage strip, and therefore the whole "exit edge" account and
hypothesis 2's premise that exit-edge stars are "present in fewer frames", is set by
that number. It should be re-derived from the plate solutions before the hypothesis
is weighed.

Related, and worth stating because it is not obvious: at 72–77° altitude, field
rotation rate is `ω·cos φ·cos A / cos(alt)` and `sec(alt)` is **3.2–4.4** — you are
near the zenith, where alt-az field rotation is at its most violent
([field rotation derivation](https://vixra.org/pdf/2205.0085v1.pdf),
[stargazing.net](http://www.stargazing.net/david/doublestars/fieldrotation.html)).
The consequence is that track length and direction vary strongly across the sensor
(734 px at the pole-ward edge to 1170 px at the equator-ward edge), so "the exit
edge" is not a single column of x — it is a corner-dependent flow field. Any fit of
25 measurements against "sensor x" is fitting a 1-D proxy to a 2-D vector field, and
an R² of 0.90 against x does not distinguish a gradient along x from a gradient at
30° to x.

### F.5 Weighing the prompt's two hypotheses

**Hypothesis 1 — uncorrected decentring, fixed in sensor coordinates.** Plausible
and mechanically sound; it is exactly what a radial-only profile cannot remove, and
§C/§D show the whole field agrees radial-only is inadequate. Three cautions. (i) It
is not independently testable on this rig through lensfun, which has no non-radial
model at 0.3.4 (§D.2). (ii) The magnitude question is unanswered: decentring in a
modern S-line zoom is typically small compared to the ~1 px effects in play, and no
one has measured it here. (iii) Most importantly, it is a *geometry* explanation for
what may be a *blur* observation — and it makes a sharp prediction that has not been
checked: if geometry is wrong, registration residuals of individual stars must show
the same one-sided pattern. **That is the test, and it costs nothing:** Siril already
computes per-star residuals during registration. A geometric cause shows there. If
residuals are flat while stacked FWHM is one-sided, hypothesis 1 is dead.

**Hypothesis 2 — registration under-constrained at the exit edge.** Weakest of the
candidates, for a documented reason: Siril's global registration is a RANSAC fit of a
homography to hundreds of star pairs spread over the whole frame. An 8-DOF model
fitted to that many points is not meaningfully "less constrained" on one side; a
global model has no local degrees of freedom to lose. The variant that *is* live —
that exit-edge sky is present in fewer frames — is a **coverage** argument, not a
constraint argument, and coverage is governed by the reference frame choice (§A.5)
and by the drift magnitude that §F.4 puts in doubt.

**My ranking**, all INFERRED, to be settled by measurement not argument:
1. PSF-track-averaging + trail-length gradient + projection inflation (§F.2, §F.3) —
   all sensor-fixed, all forced, none requiring a lens fault.
2. Coverage taper set by reference-frame position (§A.5) — real, cheap to fix.
3. Uncorrected non-radial distortion (§F.5) — real in principle, unmeasured here,
   and currently untestable through lensfun on this rig.
4. Registration under-constraint (§F.5) — mechanically weak.

---

## G. The single change I would make first

> **Read §H.2 before acting on this section.** This is the unanchored answer, left
> as written. The repo has already measured this route on its own frames and it was
> a **LOSS**. §H.3 states the part of the argument that survives that measurement and
> what it changes.

**Plate-solve every frame with SIP order 3+ and register through the distortion
solution — and, in the same run, pin the registration reference to the temporal
middle of each set with `-framing=cog`.**

```
seqplatesolve <seq> -order=3 -nocrop [-localasnet]
setref <seq> 250
register <seq> -2pass -disto=master
seqapplyreg <seq> -framing=cog -interp=lanczos4
```

**Why this first.**

1. It is the only change that attacks a cause the field agrees is real for this data
   class (§E: five independent reports, two Siril developers, one PixInsight
   tutorial, ASTAP's own tracked-case caveat inverted), using the tool's documented
   mechanism rather than a workaround.
2. SIP is a general bivariate polynomial (§C.1). It subsumes radial *and* decentring
   *and* shear. It therefore tests hypothesis 1 **without** needing lensfun to gain a
   model it does not have, without fitting Brown–Conrady, and without leaving Siril.
   If an asymmetric distortion term exists, an order-3+ SIP fit will absorb it; if
   the symptom persists unchanged, hypothesis 1 is falsified in one run.
3. It is the standards-conformant architecture: a shared static high-order term
   (`-disto=master` / a single `-disto=file`) is SCAMP's `STABILITY_TYPE=INSTRUMENT`,
   and it is what Pan-STARRS does with its per-chip polynomial (§C.2).
4. The reference-frame pin is nearly free and attacks the coverage taper (§A.5,
   §F.4) — the one part of hypothesis 2 that survives scrutiny — in the same run.
   `-framing=cog` and a mid-run reference put the output window in the middle of the
   drift, making coverage symmetric instead of one-sided.
5. It replaces an out-of-pipeline undistort stage with an in-pipeline one that
   interpolates **once**: "this actually occurs in a single operation … so as to avoid
   interpolating pixel values twice" (§A.3). Any darktable/lensfun undistort followed
   by a Siril registration warp is two interpolations of the same pixels.

**What it costs.**

- ~500 plate solves per set. At 28.6° with trailed stars this is the expensive step —
  budget minutes per frame on a CPU-only rig if the local astrometry.net path is used,
  i.e. **hours per 500-frame set**, versus seconds for star-pair registration. This is
  the real price and it is not small.
- Solve failures become frame losses. `-nocrop` is required above 5° of field
  ("If the computed field of view is larger than 5 degrees, star detection will be
  bounded to a cropped area around the center of the image unless `-nocrop` option is
  passed"), which makes each solve slower still.
- Risk of over-fitting: PixInsight's documented experience is that an over-flexible
  registration model fitted to uncertain star positions makes things *worse* (§B).
  Order 3 first; order 5 only if 3 measurably wins. Trailed stars have larger centroid
  uncertainty than round ones, so this risk is elevated here.
- It will not fix §F.2/§F.3 at all. If the dominant term is trail-length gradient,
  projection inflation, or PSF-track averaging, this change returns a clean NULL —
  which is itself the most valuable result available, because it eliminates the entire
  distortion family in one measurement.

**And one thing to do before all of it, because it costs minutes and can invalidate
the framing of the question:** re-derive the drift rate (§F.4), and measure the
single-frame FWHM/roundness field on one unregistered frame (§F.3). The first checks a
number that is out by ~2×; the second measures the sensor-fixed PSF field that three
of the four candidate mechanisms depend on. Neither requires a stack.

---
