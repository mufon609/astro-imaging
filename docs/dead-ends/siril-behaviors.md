# Siril and tool silent behaviours

Part of the dead-end registry — `docs/dead-ends.md` is the index, and
`00-registry-contract.md` governs how entries are read, cited, written and
deleted. Entries are maintained IN PLACE (pre-compression forms are in git;
the pre-split single-file registry is `docs/dead-ends.md`'s own history).
Cross-references to sibling files are written as (`<file>.md`) pointers.
The defining property of this family: the output looks healthy.

<!-- registry content below; docs/dead-ends.md is the index -->
- **SIRIL `offset` CLIPS AT ZERO IN 32-BIT FLOAT — its own help says it does
  not — and `stat` EXCLUDES zero pixels, so the two COMPOUND into a
  corruption that reads back as clean numbers.** `help offset` states *"In
  32-bit mode, no clipping occurs"*; MEASURED by writing a uniform 300 ADU
  card, applying `offset -500`, and reading the SAVED FILE with an
  independent reader: **all zeros**, not −200. Separately, a half-0/half-400
  card statts as Mean 400.0 / Median 400.0 / Sigma 0.0 where the truth is
  200/200/200 — zeros drop from every estimator — and an all-zero region
  reports *"Statistics computation failed for channel N (all nil?)"*.
  **Why it bites here:** a pedestal-free dark-subtracted sky sits ~1.5σ above
  zero, so every real light has a negative minority by construction (0.24%
  measured, far more after flat division) — an `offset` anywhere in a chain
  silently zeroes it and `stat` reports the survivors as healthy (it
  corrupted a whole real-data experiment run, caught only by a non-siril
  reader). **The clip-free equivalents, all probed:** `isub` of a constant
  card preserves negatives exactly (300 − 500 = −200.0); `imul`/`fmul` do
  not clip in either direction (`fmul` reached 90000, so >65535 survives in
  32-bit). To subtract a large constant from signed data use `isub`, never
  `offset`; if an `offset` is unavoidable, order it so the operand is
  POSITIVE. Same probe: **`stack` writes no negative values** (99.99%-
  negative frames produced a 100%-zero stack) and **`subsky` leaves a
  constant pedestal rather than zeroing the level** (a 500→800 ramp comes
  back uniform at 627.00).
  **Corollary — TRUE OF THE `stat` COMMAND, FALSE OF THE TOOL:** the COMMAND
  emits five fields with no pixel count, so nothing in that line reveals how
  many pixels were excluded — but **`sirilpy`'s `ImageStats` carries
  fourteen, including `total` and `ngoodpix`, so `total − ngoodpix` IS the
  excluded-pixel count**, per channel, per region, headless. The API returns
  typed values from a binary struct — no regex, no stdout, nothing to parse
  wrong — which removes the whole stdout-scraping defect class (the
  `Sigma: -nan` regex below is not a hazard when the field arrives as a
  float). Verified BY EXECUTION on a real SPCC stack: `ImageStats` with all
  fourteen fields, three DISTINCT per-channel medians (the
  channel-argument bug #1673 is fixed on this build); its upstream
  annotation still claims `PSFStar` — code against the measured object, not
  the annotation (`datasets/aug09/set-05/sirilpy_work/probe_type.json`).
  **Every CLIPPING claim above STANDS under the API:** `cmd()` is a pure
  pass-through with zero arithmetic surface, so every operation reaches the
  same C path and clips identically. The only bypass is
  `get_image_pixeldata()`/`set_image_pixeldata()` — raw numpy over shared
  memory — closed by DOCTRINE, not capability: arithmetic in numpy on the
  deliverable's pixels is what the bright line forbids. Stated explicitly
  because a session that finds those two methods will otherwise conclude
  the clipping problem is solved.
- **`seqsubsky` REFUSES A FRAME CARRYING NEGATIVE PIXELS** — *"removing the
  gradient on negative images is not supported"*. Pedestal-free
  dark-subtracted lights always carry them and flat division amplifies them
  (calibrated frames measure minima to **−2635 ADU**, from division by the
  flat's near-zero pixels), so any background operator on flat-fielded
  pedestal-free data needs a constant pedestal added first. The pedestal
  **cancels exactly** out of the operator — the plane fitted to `C+P` is
  `(plane of C)+P` — and costs nothing numerically (a 30% gradient still
  resolves to ~2250 float32 levels at a 56k pedestal). Verify positivity
  with a guard that can fail, and remove the pedestal with `isub`, not
  `offset` (entry above).
- **Siril `stat` says "no data" by SAYING NOTHING, and a parser that does
  not expect the silence mis-pairs every later box.** A selection that is
  ENTIRELY zero-coverage echoes its `Current selection` line and then emits
  no layer line at all. Anchoring the parse on the SELECTION echo (not the
  layer lines) makes that box carry zero channels instead of silently
  stealing the next box's numbers. MEASURED: 234 of 4000 grid boxes on a
  union returned a selection with no stat behind it.
- **Siril SPCC SIGSEGVs (exit 139) in aperture photometry when the sensor
  DATABASE is missing — not a data/field bug.** Ruled out by measurement:
  ANY star count (5305/106/291), any field size, single- or multi-thread —
  the sensor/filter/white-reference database dir was absent, so siril
  applied a `(null)` sensor response and dereferenced it. The tell:
  `spcc_list oscsensor` returns EMPTY plus an "Unable to open directory"
  log line. Do NOT chase the star count, field width, catalog format, or
  bit depth. Mechanism + the three machine-local prerequisites + fix:
  `CLAUDE.md` Environment (SPCC prerequisites).
- **Siril `stat` prints `Sigma: -nan` on a ZERO-VARIANCE selection, and a
  numeric-only regex then fails to match the WHOLE line** — so a uniform
  region reads back as "no data" rather than as a measurement, silently in
  both directions (a selection-echo-anchored parser drops the box; a
  layer-line-anchored one shifts every later box's numbers). Accept `nan`
  in the `Sigma` and `bgnoise` classes — `[-+0-9.eEanN]+`. The affected
  regions are exactly what coverage/flatness tests land on: saturated
  patches, synthetic uniform cards, clipped rims. Found twice, in two
  instruments, from ONE COPIED REGEX — the copied-pattern propagation is
  the durable half; the fix is provably neutral where no cell is
  zero-variance.
- **`seqapplyreg -interp=none` FAILS OUTRIGHT ON A HOMOGRAPHY-REGISTERED
  SEQUENCE — it does not degrade silently, and `-interp=nearest` is the
  no-blur control to use instead.** Siril's help says `none` forces the
  transform to a SHIFT, and a homography cannot reduce to a shift, so the
  command errors rather than quietly dropping to something cheaper. The
  tree's four existing `-interp=none` sites are the LUNAR route's pin — a
  USE, not this fact: that route is SHIFT-registered, which is exactly why
  its exemption is safe and why reading it as general clearance would be
  wrong. (Arms: `datasets/aug06/experiments.jsonl`,
  `resample_cost_arm_d_siril_pass`.)
- **SIRIL FALLS BACK TO AN UNWEIGHTED MEAN AT ANY PIXEL WHERE EVERY
  SURVIVING SAMPLE HAS ZERO WEIGHT — so a weighted stack silently contains
  unweighted pixels.** (DOCTRINE — the vendor's stated reasoning is "better
  than a black pixel"; a source read, NOT probed on this rig, and the
  phrase occurs in no tracked file, so this is the first home.) Why it
  matters here: the compose weights by member noise or `nbstack`, and
  sample counts collapse exactly at a union canvas's rim and corners —
  where the largest measured defect lives — and a rim pixel that quietly
  switches weighting scheme is indistinguishable in the product. **Not
  established, and must not be inferred:** whether any real product has hit
  it, the size of any discontinuity, and whether it applies to the
  plain-mean compose at all (a plain mean has no weights to zero). The
  probe that would settle it costs one run: a fixture whose members give
  one region all-zero weights, compared against the weighted arithmetic.
  Until then, a vendor claim about a code path, not a finding about our
  products.
- **Siril `idiv` CLIPS AT 1.0, SILENTLY — so a ratio of two comparable
  images (the standard flat-vs-flat instrument) loses its whole upper tail
  with no warning.** The tell: a whole-frame `stat` printing **Max exactly
  65535.0**. MEASURED on a ratio of two 250-frame flats: `idiv` Max 65535.0
  / mean 63073.6, while the SAME division via `fdiv <B> 0.5` and
  `fdiv <B> 0.25` agreed exactly after rescaling — true max 112156, mean
  63115.4. **Use `fdiv <B> <scalar>` with a scalar keeping the result in
  range; two scalars agreeing after rescale is the positive control that no
  truncation is moving them** (a Max still at 65535.0 at BOTH scalars is a
  genuine divide-by-near-zero spike, not bulk clipping). What saves you
  depends on WHERE the ratio sits: below 1.0, regional medians survive a
  truncated tail (measured identical); straddling or above 1.0 the medians
  go too — the five between-set flat ratios understated corner spread by
  −0.7 to **−9.1 percentage points** (33% understated on the worst, with a
  whole-frame MEDIAN pinned at 65535.0). Never reason about whether the
  medians are safe — rebuild with `fdiv` and compare. **Corollary: RECORD
  THE SCALAR.** A record stating its instrument as "`idiv` of one flat by
  another" was actually built with an undocumented 0.5× scalar — the only
  thing keeping its numbers off the clip; anyone reproducing it AS WRITTEN
  would have understated every figure. The measurement was right and the
  method line was wrong, which is the harder failure to catch.
- **Siril's FITS extension is a PERSISTED preference; every generated
  `.ssf` must pin `setext`.** `extension=` in `config.1.4.ini` decides what
  `convert`, `save` and `-out=` write, and a script that does not set it
  inherits whatever ran last — including another project's chain on the
  same rig. Measured against the repo's `.fit` globs with the setting on
  `.fits`: a master built **correctly** while its builder reported "wrote
  no master" and its cleanup matched nothing, leaking **9.2 GB**; two other
  builders abort with "calibrated nothing" — and Siril logs "Script
  execution finished successfully" throughout, so the cause reads as a
  data or Siril bug. Exactly the class `setcompress 0` is already pinned
  for. Bash `*.fit` does not match `*.fits` — an extension is not a glob
  prefix.
- **Calibration dirs are PLURAL — Siril's own convention** (`lights` /
  `flats` / `darks` / `biases`, never a singular). A singular staged dir
  (`dark/`) holds ≥8 raws, so the session chain and the web set-kind rule
  classified it as a LIGHT set and would have carried dark frames to frame
  QA, mount derivation and a full stack; both now list the singulars as
  calibration, and the builders still require the plural and stop loudly.
- **Never export a numpy/FITS-row-order pixel box to Siril `crop`
  unverified** — Siril's crop y-origin is the OPPOSITE end
  (`y_siril = H − y_np − h`), so an unverified export ships a vertically
  mirrored window. Measured: a coverage-validated box (map Min = 25
  everywhere in numpy coords) statted **Min 0** after export — a
  zero-coverage wedge shipped in a render. The guard is tool-sourced and
  cheap: crop the instrument MAP with the exact same args and require Siril
  `stat` to reproduce the claimed bound before any product crop.
- **SIRIL `update_key` SILENTLY TRUNCATES A STRING VALUE AT THE FIRST
  `/` — it begins the FITS comment field.** Probed directly through siril
  1.4.4:

  | written | stored |
  |---|---|
  | `update_key K1 "aug06/set-01"` | `'aug06'` |
  | `update_key K2 "a,b"` | `'a,b'` (commas are fine) |
  | `update_key K4 "aug06_set-01+july31_set-01"` | intact |
  | `update_key K5 T` | `True` (a FITS boolean, not the string) |

  No error, no warning, exit 0. `CALSET` is `<session>/<set>` by
  construction, so every provenance stamp routed through siril loses the
  set and claims the whole session — and the stamp is what a compose gate
  reads to decide member compatibility. FIX SHIPPED, following the repo's
  own precedent: provenance keys are applied with a FITS library
  (`header_apply_keys` in `stamp_headers.sh` — headers only, no pixel
  access) while acquisition keys stay on siril's `update_key`, which is
  siril's own data and slash-free. Anything with a path, a
  date-with-slashes or a ratio must not go through `update_key`.
- **SIRIL REPORTS X, Y AND `angle` IN A TOP-DOWN FRAME — THE MIRROR OF THE
  FITS BOTTOM-UP CONVENTION — AND ALL THREE ARE MUTUALLY CONSISTENT.** Two
  independent measurements: (1) synthetic stars planted at +20.0° come back
  from `findstar` at **−20.0°** at every L ≥ 0.4 px, and of 400 planted
  stars **400 match under y → H − y and 0 as planted** (`psf_calib.py`);
  (2) `source-extractor`, whose `Y_IMAGE` is standard FITS bottom-up, run
  on the same frame: **300 of Siril's 300 brightest match under
  y → H − y**. Since a FITS file's first data row IS the bottom row,
  **Siril is the mirror of FITS, not an instance of it** — an earlier form
  of this entry said "the FITS bottom-up frame", exactly backwards, which
  would hand the wrong sign to anyone bringing in a WCS. **Load-bearing:
  any quantity built from Siril's own X, Y and `angle` TOGETHER (field
  azimuth, θ − φ, a drift bearing cross-matched from findstar lists) is
  unaffected by the frame entirely; what inverts is handedness and any
  comparison against something measured in FITS coordinates** — a WCS/CD
  matrix, a `source-extractor` catalogue, a parallactic angle: convert
  through the mirror or the sign of the answer is wrong. There is also a
  1 px offset from FITS 1-based indexing on top of the mirror.
- **`stat` / `seqstat` MIN and MAX INCLUDE zero pixels — computed before the
  non-null reassignment — so "every estimator excludes zeros" is true of the
  level/dispersion estimators only.** MEASURED on 20+ products and members
  (`datasets/corpus/pedestal_work/`): min reads 0.0 wherever zero padding
  exists and the true minimum where none does. A union's darkest NON-zero
  pixel — the quantity `-output_norm` subtracts — is not reportable by
  `stat`; it needs a diagnostic read.
- **`stack -norm=addscale` on a sequence whose `.seq` already carries M lines
  normalizes on those CACHED statistics (written with 6 significant digits);
  a fresh registration normalizes on full-precision ones — so a hand re-stack
  from a kept scratch and a fresh chain build of the same members are NOT
  pixel-identical.** MEASURED (n = 1 build, 13-member aug06 union,
  `datasets/corpus/pedestal_work/go2_compose_nooutnorm.json`): 87,798,306 of
  101,278,350 pixels differ by ≤5.96e-7 (0.039 ADU16, ≤5 float32 ULP at 1.0),
  invisible at `seqstat`'s sixth digit; a re-stack on the fresh scratch with
  its just-cached M lines is bit-identical to the earlier hand re-stack and
  differs from the fresh build identically. The cache mechanism is INFERRED
  from that two-way identity, not read from the source. Reading rule: a
  fresh-vs-re-stack pixel comparison at this level is float rounding, never
  a knob; a fresh-vs-fresh comparison of the same configuration is
  bit-identical (E0: 0 differing).
