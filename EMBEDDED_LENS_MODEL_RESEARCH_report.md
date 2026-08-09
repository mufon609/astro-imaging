# RESEARCH — the manufacturer's embedded lens-distortion model as the optical-state source

Claim labels used throughout: **MEASURED** (on-rig probe, this report) · **DOC**
(primary source, cited) · **COMMUNITY** (forum/tracker, cited) · **HYPOTHESIS**
(stated with the test that would settle it).

No pipeline file, lensfun DB entry, style, or dataset record was written. Every
on-rig probe read NEF *headers* except the one pixel diagnostic in §2.5, which is
a diagnostic under CLAUDE.md's explicit carve-out and touched nothing.

---

## 0. Verdict

**The embedded model is NOT the per-state source. It is a STATIC table on this
rig, and it is blind to the exact difference it was hypothesised to encode.**

MEASURED over **all 7,702 NEFs in the archive** (4 nights, 23 set/dark
directories): the Nikon `DistortionInfo` block takes exactly **two** distinct
coefficient triples, and **7,355 frames — every light frame of every night —
carry the same one**. The second triple appears in one directory only
(`july31/darks`, 347 frames).

The kill is arithmetic. The two nights whose disagreement this route exists to
explain — a july31 member and an aug06 member, MEASURED at **4.07 px** corner
separation under a shared model (`cross_night_state_difference`) — carry
**byte-identical** distortion coefficients. Adopting the embedded model for both
nights *is* adopting a shared model, so it reproduces that failure by
construction.

And the model's whole dynamic range is too small to matter regardless: the
**entire** spread between the two observed triples is **0.808 px at the frame
corner**, against a 4.07 px defect and a ≤ 0.35 px compose PASS gate.

| question | answer |
|---|---|
| 1. per-STATE or static? | **STATIC** (MEASURED, 7,702 frames; latches per power-up, not per focus state) |
| 2. what is the model? | 3 radial coefficients, rational/2²⁰, in a private 84-byte block; polynomial form is DOC for **DNG's** WarpRectilinear, the Nikon→DNG mapping is **unverified COMMUNITY** |
| 3. what decodes it? | **exiftool only.** exiv2, LibRaw and dcraw all fail (MEASURED on-rig) |
| 4. what applies it headlessly on Linux? | **Nothing, natively.** darktable and RawTherapee both implement embedded-metadata correction for Sony/Fuji/Olympus/Panasonic/DNG — **no Nikon**. One live route remains (DNG opcodes via a proprietary non-native converter) |
| 5. prior art | The community effort to decode this exact block is **open and unsolved** |
| 6. validation | Designed in §6 — and its first step is a cheap gate that kills or unblocks both surviving routes |

**Consequence for the F2 road:** the fitting problem does **not** dissolve. The
hardest in-house component survives intact, and the corner-support/reproducibility
failure recorded at commit `75340bb` still gates multi-night combining.

**What is NOT dead:** the embedded model remains a candidate *static base model
that reaches the corner by construction* — which is precisely where the community
lensfun profile fails (its paraxial error writes a measured centre band). That is
a different and smaller prize than per-state, and §4 prices it honestly.

---

## 1. Q1 — Is the embedded model per-STATE or static? (the decisive question)

### 1.1 Instrument

`exiftool 13.55`, one invocation, headers only:

```
exiftool -q -r -ext NEF -csv -n \
  -DateTimeOriginal -ExifIFD:FocalLength -Nikon:SerialNumber -LensSerialNumber \
  -LensID -LensFirmwareVersion -FocusDistance -LensPositionAbsolute -FocusMode \
  -DistortionCorrectionVersion -DistortionCorrection -AutoDistortionControl \
  -RadialDistortionCoefficient1 -RadialDistortionCoefficient2 \
  -RadialDistortionCoefficient3 -VignetteCoefficient1..3 \
  -PowerUpTime -ShutterMode -ShutterCount -ImageWidth -ImageHeight -CropArea \
  sessions/
```

**n = 7,702 frames** — the complete archive: july14, july23, july31, aug06;
19 light sets + 4 dark sets.

### 1.2 What is constant across all 7,702 frames (MEASURED)

Body serial `3009577`; lens `NIKKOR Z 24-70mm f/4 S` serial `20471536`, firmware
`257`; `LensDataVersion 0802`; `FocalLength 70 mm`; `FocusDistance` at its
infinity encoding; `DistortionCorrectionVersion 0100`; `DistortionCorrection = 3`
("On (Required)"); `AutoDistortionControl = 1`; `ImageWidth/Height 6064×4040`;
`CropArea 8 4 6048 4032`.

### 1.3 The result — two triples in 7,702 frames (MEASURED)

| triple (c1, c2, c3) | frames | where |
|---|---|---|
| **A** = `0.01821231842, −0.01132106781, 0.05938911438` | **7,355** | all four nights; 22 of 23 directories — **every light set** |
| **B** = `0.01828289032, −0.01136207581, 0.05913734436` | 347 | `july31/darks` **only** |

Every one of the 19 light sets carries triple **A**. Three of the four dark sets
carry **A**. One dark set carries **B**.

### 1.4 It does not track optical state — it latches per power-up (MEASURED)

The state field that genuinely moves in this archive is
`Nikon:LensPositionAbsolute`. It **does not predict the coefficients**:

- it spans **−17 … 0** across the archive, and takes the value `0` in **both**
  coefficient groups;
- `july31/set-01` contains **3 distinct lens positions under a single triple**;
- `aug06/set-00` contains 2 distinct positions under a single triple.

Grouping instead by `Nikon:PowerUpTime` is clean and complete — **15 power-up
cycles across four nights, 14 of which emit triple A and exactly one of which
emits B**:

```
PowerUpTime            coef1          vignette1      night/set        n
2026:07:14 21:20:03    0.01821231842  -4.667527199   july14/darks    214
   … 13 further power-ups, all triple A, all four nights …
2026:08:01 00:33:31    0.01828289032  -4.62051487    july31/darks    347   <-- the lone outlier
2026:08:06 21:59:21    0.01821231842  -4.667527199   aug06/set-00    140
2026:08:06 22:43:55    0.01821231842  -4.667527199   aug06/set-01    500
```

The **vignetting** coefficients flip in the same single power-up
(`VignetteCoefficient1` −4.667527199 → −4.62051487). The whole correction block
is re-latched together, once, at one power-on — not tracked per shot.

**HYPOTHESIS (unsettled):** what re-latched it. The camera was power-cycled
(`PowerUpTime` differs) and `ShutterMode` differs (16 vs 81) between that dark
run and the neighbouring lights. This body exposes **no temperature tag**
(MEASURED: the only temperature-named tag in the NEF is `ColorTemperatureAuto`,
a white-balance value), so a thermal recalibration can be neither confirmed nor
refuted from headers. Settling it needs a deliberate probe — mount/unmount and
power-cycle the same lens at a fixed focus and read the block — which is an
acquisition-side experiment, not a processing one.

### 1.5 The magnitude — why even the observed variation is irrelevant (MEASURED)

At the frame corner every term of the polynomial is multiplied by 1, so the
difference between two triples at the corner is the sum of their coefficient
differences — **independent of the coefficient ordering**, which is the one
detail of the model form that is still unverified (§2.3). Corner radius for the
6048×4032 default crop is √(3024² + 2016²) = **3634.40 px**.

```
Δc1 = +7.057e-05   Δc2 = -4.101e-05   Δc3 = -2.518e-04   Σ = -2.222061e-04
ENTIRE observed spread of the embedded model at the corner  =  0.808 px
```

Against the numbers this route would have to beat:

| quantity | px at corner |
|---|---|
| **entire observed spread of the embedded model, 7,702 frames** | **0.81** |
| own-models corner member failure | 2.99 |
| **cross-night state difference (`cross_night_state_difference`)** | **4.07** |
| compose gate PASS | ≤ 0.35 |

The model's full range of motion across four nights is **one fifth** of the
defect it would have to explain — and that range is not even *between* the two
nights in question. Both carry triple A.

### 1.6 Scope limit — stated, because it is real

**Every frame in this archive is at 70 mm.** This probe therefore measures
"static across nights, sets, focus positions and power-ups **at one focal
length**". It says nothing about focal-length dependence: a zoom lens's embedded
table is near-certainly indexed by focal length, and this archive cannot see that
axis. That does not weaken the verdict — the project shoots this one focal
length, and the failure is *within* it — but a future dataset at a different
zoom setting would get a different (and equally static) triple, and the record
should say so rather than imply the block is a single constant.

---

## 2. Q2 — What exactly is the model?

### 2.1 Where it lives (MEASURED, `exiftool -v3`)

A private `DistortionInfo` sub-directory at **MakerNote tag 0x0005**, 84 bytes,
inside a nested 15-entry Nikon MakerNotes directory. Separate from — and a
sibling of — `VignetteInfo` at tag 0x0006 (116 bytes) and the older `DistortInfo`
at tag 0x002b (16 bytes, carries only `AutoDistortionControl`).

exiftool's decoder (`Image/ExifTool/Nikon.pm`, `%Image::ExifTool::Nikon::DistortionInfo`):

| block offset | field | format |
|---|---|---|
| `+0x00` | `DistortionCorrectionVersion` | `string[4]` → `"0100"` |
| `+0x04` | `DistortionCorrection` | `int8u` → `3` = *On (Required)* |
| `+0x14` | `RadialDistortionCoefficient1` | `rational64s` |
| `+0x1c` | `RadialDistortionCoefficient2` | `rational64s` |
| `+0x24` | `RadialDistortionCoefficient3` | `rational64s` |

**MEASURED from the raw block:** all three rationals carry the denominator
`0x00100000 = 2²⁰`, so the values are exact binary fractions — triple A is
`19097/2²⁰, −11871/2²⁰, 62274/2²⁰`. Nothing is quantised away by exiftool's
`%.5f` print conversion; use `-n` and the values are exact.

### 2.2 What exiftool does NOT decode (MEASURED, and it moves)

Hexdumping the 84-byte block across three frames shows a **fourth
2²⁰-denominator rational at `+0x40` that exiftool ignores, and it co-varies with
the three that are decoded**:

| frame | c1 num | c2 num | c3 num | `+0x40` num | `+0x40` value |
|---|---|---|---|---|---|
| july31/set-01 (A) | 19097 | −11871 | 62274 | 74572 | 0.07111740 |
| aug06/set-01 (A) | 19097 | −11871 | 62274 | 74572 | 0.07111740 |
| july31/darks (B) | 19171 | −11914 | 61994 | 74330 | 0.07088661 |

Constants across all three: `+0x08 = 88474`, `+0x0c = 4096`, `+0x10 = 4`, and two
zero rationals at `+0x2c` / `+0x34`. The final 4 bytes differ per block
(plausibly a checksum).

**HYPOTHESIS:** `+0x40` is the correction's **autoscale factor** — its value
(7.11%) sits just above the model's own corner correction (6.63%, §2.4), which is
exactly the scale needed to refill a pincushion-corrected frame plus margin. A
4th-order term is the competing reading; `+0x10 = 4` ("four coefficients"?) is
weak support for it. Not settled, and not load-bearing for anything in this
report.

### 2.3 The polynomial — DOC for DNG, UNVERIFIED for Nikon

**DOC** — Adobe's DNG SDK, `dng_lens_correction.h`, `WarpRectilinear`:

> radial warp `w(r) = (kr0 * r) + (kr1 * r^3) + (kr2 * r^5) + (kr3 * r^7)`
> … "A normalized radius of 1.0 corresponds to the distance from fCenter to the
> farthest corner of the image's active area."
> Domain constraint: "`w(r)` must be an increasing function" and "`f(x,y)` must
> be an invertible function."

**COMMUNITY, UNVERIFIED** — that Nikon's three coefficients *are* DNG's
`kr1..kr3` with `kr0 = 1`. The DPReview thread "Deep dive into Z lens
corrections" reports that the coefficients fed **in reverse order**
(`k1=Coeff3, k2=Coeff2, k3=Coeff1`) into the Adobe algorithm reproduce the
DNG result closely. I could not fetch that thread directly (HTTP 403 to this
rig), so this is second-hand and carries no weight beyond a lead. Note the
ordering question does **not** affect §1.5's corner number, which is
order-independent.

### 2.4 The normalization, and the corner — this is the part that matters

The repo normalises by **half the short side**, which places the frame corner at
ρ = 3634.40 / 2016 = **1.8028** — the ρ = 1.80 at which the in-house hugin fits
fail. DNG normalises by the **half-diagonal**, placing the same corner at ρ = 1.

Which convention Nikon uses is settled by a sanity check, not by a document
(MEASURED arithmetic):

| assumed ρ at the corner | model's corner stretch |
|---|---|
| **1.0000** (half-diagonal — DNG's convention) | **+6.6%** (240.9 px) |
| 1.8028 (half-short-side — the repo's convention) | +197.8% |

A 198% corner stretch is not a lens. **ρ = 1 is at the corner**, and therefore:

> **The manufacturer's model is defined out to its own sensor's corner by
> construction** — the DNG normalization *anchors* r = 1 there, and the
> invertibility constraint applies over that whole domain.

That is the one property the in-house route cannot obtain: the hugin fits fail at
ρ = 1.80 for want of corner control points, and this model has no corner to run
out of. It is the genuine merit of the route and it survives the Q1 verdict — it
is just a merit of a *static* model, not a per-state one.

### 2.5 Does the block carry vignetting / TCA? (MEASURED)

**Distortion and vignetting are already separate blocks** — `DistortionInfo`
(0x0005) and `VignetteInfo` (0x0006), each with its own version and coefficients.
exiftool exposes **no TCA block** for this body. So distortion-only is available
at the source, and the doctrine that vignetting must not ride along
(`install_lens_model.sh` strips it from the lensfun user DB, because it fights a
master/sky flat) is satisfiable.

Caveat if the DNG route is taken: a `WarpRectilinear` opcode carries distortion
**and TCA together** in one opcode (three planes), while vignetting is a separate
`FixVignetteRadial` opcode (DOC, DNG spec). Still separable, but the separation
happens at a different layer.

### 2.6 On-rig attempt to measure the model empirically — **clean NULL**

**Design.** Every NEF embeds a full-size (6048×4032) in-camera JPEG with the
correction applied (`AutoDistortionControl = On`, `DistortionCorrection = On
(Required)`), while the raw is uncorrected. The displacement field between that
JPEG and a `nodist` darktable render of the same NEF *is* the applied model,
measured directly — settling the ordering, the normalization and the corner
domain in one shot.

**Executed:** JPEG extracted with `exiftool -b -JpgFromRaw`; raw rendered with
`darktable-cli --style nodist --style-overwrite --icc-type LIN_REC709`,
`bpp=32`, un-rotated and cropped to `CropArea` so both sit in the same sensor
frame; sources extracted with **sep 1.4.1** (the repo's sanctioned extractor).
Three matchers tried: polar-angle matching, centre-out bootstrap with a
model-predicted search window, and patch phase-correlation on 8 rays.

**Result: NULL — no correspondence exists to fit.** The central-region
translation vote, which must peak sharply near (0,0) since the warp is ~0 at the
centre, produced **11 votes against a 99.9-percentile of 7** (no signal) at every
threshold from 4σ to 50σ.

**Mechanism, identified — a data limit, not a method limit.** Direct inspection
of matched 400×400 centre patches shows the in-camera JPEG is **dominated by 8×8
JPEG block artifacts**, not stars: a 2.5 s ISO 1600 sub-exposure at 70 mm is
sky-noise-dominated, and the camera's lossy 8-bit encode of that noise destroys
the faint star field. `sep` was detecting quantisation blocks in one image and
shot noise in the other.

**What would settle it** (not run — no such frame exists in this archive): one
frame from the same body + lens at the same focal length on a **bright,
structured subject** (daylight, or a moonlit landscape), where the in-camera JPEG
carries real detail. The measurement is then trivial and gives the model exactly.
This is worth two minutes at the next acquisition and would convert §2.3 from
COMMUNITY to MEASURED.

Note the parallel worth recording: this failed for the *same underlying reason*
the hugin corner fit failed — this project's frames do not carry recoverable
high-radius correspondences. That is a property of the data, and it constrains
every route that needs to *verify* a model from these frames.

---

## 3. Q3 — What can DECODE it?

All rows MEASURED on this rig against `sessions/july31/set-01/DSC_3782.NEF`.

| reader | version | decodes the coefficients? | evidence |
|---|---|---|---|
| **exiftool** | 13.55 | **YES — full numeric** | all three + version + `DistortionCorrection` + `AutoDistortionControl`; `-n` gives exact 2²⁰ rationals; swept 7,702 frames in one invocation |
| **exiv2** | installed | **NO** | `exiv2 -pa` returns only `Exif.Nikon3.VignetteControl`. No distortion tags at all |
| **LibRaw** | 0.22.1 | **NO** | zero occurrences of `distort` in `libraw.so.25` strings |
| **dcraw** | installed | **NO** | `dcraw -i -v` reports lens/focal but no correction data |
| **rawpy** | not installed | n/a | a LibRaw binding — would inherit LibRaw's gap |

**The exiv2 row is the important one.** darktable and RawTherapee both read maker
notes *through exiv2*. A decoder gap in exiv2 is therefore an application gap in
both consumers, and it is exactly the blocker the community names (§5).

**COMMUNITY (unverified):** exiftool gained this decode at 12.71. The rig runs
13.55, so it is moot here, but a bootstrap that pins exiftool should pin ≥ 12.71.

---

## 4. Q4 — What can APPLY it headlessly on Linux?

**The application gap is real and it is the blocker.** Free-tools constraint
stated per route.

### Route (a) — darktable's "embedded metadata" lens-correction method: **DEAD for Nikon**

**DOC** — darktable `src/common/image.h`:

```c
typedef enum dt_image_correction_type_t
{
  CORRECTION_TYPE_NONE, CORRECTION_TYPE_SONY, CORRECTION_TYPE_FUJI,
  CORRECTION_TYPE_DNG,  CORRECTION_TYPE_OLYMPUS, CORRECTION_TYPE_PANASONIC
} dt_image_correction_type_t;
```

**No `CORRECTION_TYPE_NIKON`.** The user manual's "only available if supported
metadata is found" resolves to this enum.

**MEASURED on the installed 5.4.1** — the feature is present but the maker is
not: `liblens.so` carries `DT_IOP_LENS_METHOD_EMBEDDED_METADATA`
(+ `..._VERSION_1/2`) and the help string *"embedded metadata provided by the
camera or software vendor"*; `libdarktable.so` carries `WarpRectilinear`.

**Independent corroboration, already in this repo:** TOOLS.md records the
MEASURED fact that darktable given an unmatched lens applies **no correction at
all** — *"0.000 px over 413 stars, exit 0, nothing in the log"*. Had a Nikon
embedded-metadata path existed, that case would have been corrected anyway.

**Free:** yes. **Reaches Nikon Z NEF:** no. **Verdict: dead, at 5.4.1 and at
current master.**

### Route (b) — the DNG opcode path: the only live route, and it is not free

`CORRECTION_TYPE_DNG` **is** supported, so a DNG carrying the correction as a
`WarpRectilinear` opcode *would* be applied headlessly by the installed darktable.
The question collapses to: **what writes that opcode on Linux?**

| converter | free | native Linux | headless | writes lens opcodes? |
|---|---|---|---|---|
| **Adobe DNG Converter** | no (proprietary, licensed) | **no** — Windows/macOS; runs under **Wine** (COMMUNITY: `thosoo/adobe-dng-converter-installer`) | yes — documented CLI (`-c/-u/-l`, `-d <outdir>`), batchable | **yes** (DOC/COMMUNITY — darktable PR #12880 names it as *the* mechanism) |
| **dnglab** | yes | yes | yes | **NO** — COMMUNITY: *"dnglab doesn't add Adobe DCP profiles or lens opcodes"* |
| exiftool | yes | yes | yes | it can *write* an opcode blob, but nothing derives one from Nikon's block (that derivation is §5's unsolved problem) |

**This is the crux of the whole route: the only converter that carries the model
is proprietary and non-native.** The one free, native, headless converter
explicitly drops it.

**Costs if taken:**

- **Toolchain:** Wine + a licensed Adobe binary added to `x86_bootstrap.sh` /
  `manifest.tsv`. Installable and pinnable-by-version, but **not redistributable**
  — a contributor cloning the repo must accept an Adobe licence to rebuild the
  environment. Comparable to the existing StarNet/GraXpert external installs, but
  those are freely fetchable.
- **Disk + wall-clock:** a NEF→DNG pass over every frame. At ~25 MB/frame that is
  ~12.5 GB per 500-frame set and ~185 GB archive-wide, in a chain whose disk
  pressure is already managed by group composition and which **forbids
  compression anywhere** (CLAUDE.md) — so the uncompressed DNG (`-u`) is the only
  compliant option, and it is the larger one.
- **Reproducibility:** it inserts a closed-source, un-auditable transform between
  the raw and the warp. The chain's "REPRODUCIBLE to a documented tolerance" test
  can still be met (pin the converter version), but the *why* of any coefficient
  becomes unreadable.
- **Consumers:** darktable 5.4.1 (installed) or RawTherapee ≥ 5.11. Note Debian's
  RawTherapee is not lensfun-linked (TOOLS.md) — irrelevant for opcodes, but it
  would be a **new tool** in the chain, whereas darktable is already the UNDISTORT
  stage.

**Unverified and decisive:** whether Adobe's converter writes a `WarpRectilinear`
opcode **for this body and lens**. `DistortionCorrection = 3` ("On (Required)")
is the flag ACR reads to decide the built-in profile is mandatory (DOC —
exiftool's own comment on the tag), which makes it likely, but likely is not
measured. §6's E0 settles it for the cost of one file.

### Route (c) — convert into the existing lensfun/ptlens slot: cheapest, and gated on §5

This route reuses the **entire** existing warp chain — darktable + the lensfun
user DB + `install_lens_model.sh` + `verify_lens_card.py` — and replaces only the
*fit*. No new tool, no new format, no Wine, no extra disk, no proprietary step.

**Precedent (COMMUNITY, and it is a strong one):** `uchrisu/lf_fitexif` fits
manufacturer embedded correction data to lensfun's PTLENS model; lensfun
discussion #1606 reports the distortion fit landing with *"minimal deviation"*,
and the maintainer calling the approach *"very useful and worth the effort"*.
**Sony E-mount only** — the README states *"Currently works only for Sony-E"*.
There is no Nikon support and, per §5, no decoded Nikon model to give it.

**The conversion arithmetic, once the model is pinned:** sample Nikon's
`w(ρ)` on a grid out to the corner and least-squares fit lensfun's ptlens form
`Rd = Ru(a·Ru³ + b·Ru² + c·Ru + 1−a−b−c)` in the half-short-side convention
(DOC — PanoTools: *"radius=1.0 is half the smaller side of the image"*). The two
bases differ — DNG's is **odd-only** (r, r³, r⁵, r⁷), PanoTools' carries **even
and odd** powers (r, r², r³, r⁴) — so the mapping is a close fit, **not an
identity**, and the residual at ρ = 1.80 is a number that must be computed and
reported, never assumed. It is cheap to compute and needs no data.

**Blocker:** route (c) needs the Nikon polynomial and its normalization to be
*known*, and §5 says the community has not derived them. Route (b)'s E0 gate is
the cheapest way to obtain them — a DNG opcode read gives Adobe's own
interpretation of Nikon's block, which is the mapping.

**Free:** yes, entirely. **Verdict: blocked on knowledge, not on tooling** — and
it is the route worth unblocking.

---

## 5. Q5 — Prior art

| source | what it establishes |
|---|---|
| [pixls.us — *Reverse engineering Nikon Z-series lens correction*](https://discuss.pixls.us/t/reverse-engineering-nikon-z-series-lens-correction/36733) | **The decisive prior-art finding.** paperdigits (Mica) with Colin Adams, Jade_NL, ggbutcher, kmilos. Status: data-gathering only — **no formula derived, no working decode of the structure, no code**. ggbutcher's standing hypothesis is that the values map to *"Adobe DNG opcode3 distortion correction"* — i.e. §2.3's mapping is the community's open question too, not a settled fact. kmilos: once decoded, *"someone will also need to enable accessing these blocks from exiv2"* — §3's gap, named by the people who would have to close it. Stated obstacle: Nikon holds the documentation under NDA |
| [lensfun discussion #1606 — *Using manufacturer lens correction data?*](https://github.com/lensfun/lensfun/discussions/1606) | The route-(c) precedent. uchrisu converts Sony embedded data → lensfun PTLENS with minimal deviation, plus vignetting and TCA. Maintainer `sarunasb`: *"manufacturers only cooperated with Adobe and alike … there is no known standard … proprietary 'standards' are not published"*, but supports it case-by-case. **Nikon not discussed** |
| [uchrisu/lf_fitexif](https://github.com/uchrisu/lf_fitexif) | The working implementation of that precedent. *"Currently works only for Sony-E"* |
| [darktable PR #12880 — embedded DNG lens corrections](https://github.com/darktable-org/darktable/pull/12880) (jenshannoschwalm) | Implements `WarpRectilinear` + `VignetteRadial` from `OpcodeList3`. Coverage listed as Leica Q2/Q/SL, Pixel 6, some phones; **Nikon NEF not among them**. Names Adobe DNG Converter as the way users obtain opcodes. Limitation: coefficients are valid for the **default crop**, and *"we can't autoscale as the coeffs are not valid any more"* |
| [darktable PR #12760 — Olympus embedded metadata](https://github.com/darktable-org/darktable/pull/12760) (paolodepetrillo) | The sibling maker-specific implementation; establishes the pattern each maker needs its own reverse-engineered decoder |
| [RawTherapee #2838](https://github.com/Beep6581/RawTherapee/issues/2838) → [PR #7100](https://github.com/Beep6581/RawTherapee/pull/7100) | Merged for **5.11**: Sony, Fujifilm, Olympus, Panasonic + DNG `WarpRectilinear`/`FixVignetteRadial`. **The identical maker set as darktable, and identically no Nikon** — two independent projects reaching the same boundary is strong evidence the boundary is the *decode*, not either implementation |
| [Adobe DNG SDK — `dng_lens_correction.h`](https://github.com/aizvorski/dng_sdk/blob/master/source/dng_lens_correction.h) | DOC for the WarpRectilinear polynomial, the corner-anchored normalization, and the invertibility domain (§2.3) |
| [PanoTools — Lens correction model](https://hugin.sourceforge.io/docs/manual/Lens_correction_model.html) | DOC for the ptlens/lensfun target basis and its half-short-side normalization (§4c) |
| [DPReview — *Deep dive into Z lens corrections*](https://www.dpreview.com/forums/threads/deep-dive-into-z-lens-corrections-including-impact-on-acuity.4358779/) | COMMUNITY lead on the reversed coefficient ordering. **Not directly verifiable** — returns HTTP 403 to this rig; cited second-hand and given no weight |
| [thosoo/adobe-dng-converter-installer](https://github.com/thosoo/adobe-dng-converter-installer) | COMMUNITY: Adobe DNG Converter under Wine on Linux, scripted |
| [NeoAnalogLab — dnglab vs Adobe DNG Converter](https://dng.neoanaloglab.com/en/compare/) | COMMUNITY: *"dnglab doesn't add Adobe DCP profiles or lens opcodes"* — the free-converter gap |

**Nobody has mapped these coefficients.** exiftool decodes the *storage*; no
public source decodes the *model*.

---

## 6. Q6 — Validation design (design only, nothing run)

Re-scoped by the Q1 verdict: this can no longer be validated as a per-state
source. It is validated as a **static base model that reaches the corner**, and
E2 below is written so that the route's failure is itself an informative
measurement rather than a wasted run.

### E0 — the gate (do this first; it is cheap and it decides everything)

**One knob:** none — this is an instrument check, no product is built.
**Cost:** one Wine install, one file converted.

Convert **one** NEF with Adobe DNG Converter under Wine; read the opcode with
`exiftool -v3 -OpcodeList3` (or `-b`) and compare the `WarpRectilinear`
`kr0..kr3` against the MakerNote triple.

- **PASS** — an opcode is present and its coefficients relate to the MakerNote
  triple by a stated transform. This simultaneously (i) proves route (b) works
  end-to-end and (ii) **hands route (c) the model form and normalization for
  free**, which is the knowledge §5 says nobody has published.
- **FAIL — no opcode written for this body:** route (b) is dead, and route (c)
  loses its only verification path. Both close; the report's verdict stands
  unchanged and nothing further is spent.

**Pre-registered:** E0 PASS is required before any pixel is warped by this model.

### E1 — one knob: the model source, within one night

**Control:** the shipped per-set fitted model. **Arm:** the embedded model via
whichever route E0 validated. Same set, same frames, same calibration, same
register/stack.

**Instruments (all existing):** `scripts/qa/member_separation.py` cross-pairs,
read against the compose gate (**PASS ≤ 0.35 px**, WARN to 1.00, BLOCK above);
plus `scripts/qa/star_stations.py` **read explicitly at the centre**, because the
community profile's known failure is a paraxial **centre band** (july14: centre
5.30 px vs perpendicular 3.60) and a corner-anchored manufacturer model is
precisely the thing that should not have one.

**Pre-registered:** the embedded model is worth adopting as a static base if it
holds the fitted model's within-night separation **and** shows no centre band.
Sharpness claims need the user's eyes on full-frame lossless finals — this
experiment does not settle aesthetics.

### E2 — the multi-night question, with its answer pre-registered

Compose one july31 member and one aug06 member, **both** under the embedded
model, and read `member_separation.py` at centre/mid/outer/corner.

**PRE-REGISTERED PREDICTION (from §1.3):** both nights carry byte-identical
coefficients, so this is arithmetically the *shared-model* configuration already
measured. Expect **≈ 4.07 px at the corner**, not ≤ 0.35.

- Landing near 4.07 px **confirms the Q1 verdict at product level** and closes
  the route for multi-night — a clean, cheap confirmation rather than an
  assumption.
- Landing at the 0.14–0.35 px floor would **refute** the reading that 4.07 px is
  a physical state difference, implying it was model error instead — which would
  rescue F1 (one model per combine family) and change the whole multi-night road.
  Low prior, high value; the run costs one compose.

### E3 — only if E1 and E2 favour the route

Compute the ptlens conversion residual: sample the embedded model out to
ρ = 1.80 and least-squares fit lensfun's ptlens basis; **report peak displacement
error over ρ ≤ 1.80**. Adopt route (c) only if that peak is below the compose
gate's 0.35 px; otherwise route (b) is the only faithful application and its
costs (§4b) apply in full.

### Kill criteria, stated in advance

Any one of these closes the investigation: E0 FAIL; E1 corner separation worse
than the fitted control beyond the WARN band; E2 at ≈ 4.07 px **and** no interest
in a static-only base model; E3 residual above 0.35 px with route (b) judged too
costly.

---

## 7. What inherits, now that the route does not replace the fit

The prompt asked for this explicitly, and the answer is unwelcome but clean:

- **The F2 fitting road is untouched.** Corner-true per-state fitting still has
  both failures recorded at `75340bb`: corner control points are unreachable
  without a degenerate fit, and the fit reproduces to only ~3 px — the size of the
  2.99 px defect it exists to remove. Nothing here relieves either.
- **The T-1 trade is unchanged.** Options (a) *wait for F2*, (b) *one shared
  aug06 model at 0.93 px, needs eyes*, and (c) *leave the failed union as
  evidence, per-set products stand* all stand exactly as costed in
  `COMPOSE_SMEAR_FIX_PLAN.md` §7. This research removes no option and adds none.
- **What it does add** is a negative that was worth buying: the manufacturer's
  data is now **priced**, TOOLS.md's long-standing unpriced entry can be closed,
  and no future session needs to re-open it hoping the coefficients are per-shot.
  They are not, on this rig, at this focal length, over 7,702 frames.
- **The one live lead** is §2.4's property — a model anchored at the corner by
  construction — against the community lensfun profile's measured paraxial centre
  band. That is a *static base model* question, and E0 prices it for the cost of
  one converted file.

---

## 8. Reproducing the probes

```bash
# Q1 — the archive sweep (headers only; ~7,700 frames, one invocation)
exiftool -q -r -ext NEF -csv -n -PowerUpTime -ExifIFD:FocalLength \
  -LensPositionAbsolute -RadialDistortionCoefficient1 \
  -RadialDistortionCoefficient2 -RadialDistortionCoefficient3 \
  -VignetteCoefficient1 sessions/

# Q2 — the raw 84-byte block, including the field exiftool does not decode
exiftool -v3 sessions/july31/set-01/DSC_3782.NEF | grep -A8 'DistortionInfo (SubDirectory)'

# Q3 — the decoder matrix
exiv2 -pa  <frame.NEF> | grep -i distort          # -> nothing
strings /usr/lib/x86_64-linux-gnu/libraw.so.25 | grep -ci distort   # -> 0
dcraw -i -v <frame.NEF>                            # -> no correction data

# Q4a — darktable's maker coverage, on the installed build
strings /usr/lib/x86_64-linux-gnu/darktable/plugins/liblens.so | grep -i embedded
strings /usr/lib/x86_64-linux-gnu/darktable/libdarktable.so | grep WarpRectilinear
```

Ledger: `datasets/aug06/experiments.jsonl` → `embedded_lens_model_research`.
