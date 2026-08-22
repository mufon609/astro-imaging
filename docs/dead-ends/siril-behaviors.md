# Siril and tool silent behaviours

Phase-1 split of `docs/dead-ends.md` (organize-only; the original file stays
the live registry until the merge is decided). Content below the marker is
VERBATIM from the original, so in-text "above"/"below"/section references may
point at entries now homed in a sibling file — `README.md` in this directory
carries the index, the assignment rule, and the block manifest that resolves
them. Do not edit below the marker while the refactor is in phase 1; the split
is re-derivable from the manifest and verified byte-identical by `split.py`.

<!-- == verbatim content from docs/dead-ends.md below this marker == -->
- **SIRIL `offset` CLIPS AT ZERO IN 32-BIT FLOAT — its own help says it does not
  — and `stat` EXCLUDES zero pixels, so the two COMPOUND into a corruption that
  reads back as clean numbers.** `help offset` states *"In 32-bit mode, no
  clipping occurs"*. MEASURED by writing a uniform 300 ADU card, applying
  `offset -500`, and reading the SAVED FILE with an independent reader: it
  contains **all zeros**, not -200. Separately, a card that is half 0 and half
  400 ADU statts as **Mean 400.0, Median 400.0, Sigma 0.0, Min 0.0** where the
  truth is 200/200/200 — zeros are dropped from every estimator while `Min`
  still shows 0.0, and an all-zero region reports *"Statistics computation
  failed for channel N (all nil?)"*.
  **Why this bites here specifically:** a pedestal-free dark-subtracted sky sits
  ~1.5 sigma above zero, so every real light has a negative minority by
  construction (0.24% measured on aug09 lights, far more after flat division).
  An `offset` anywhere in a chain silently zeroes it and `stat` then reports the
  survivors as healthy. This corrupted a whole real-data run of the
  iterative-flat experiment — a -56443 ADU `offset` drove a flat's corners to
  zero, which read back as "all nil" — and it was caught only by reading saved
  pixels with a non-siril reader.
  **The clip-free equivalents, all probed:** `isub` of a constant card preserves
  negatives exactly (300 - 500 = -200.0), `imul` and `fmul` do not clip in either
  direction (`fmul` reached 90000, i.e. >65535 survives in 32-bit). To subtract a
  large constant from signed data, use `isub`, never `offset`; if an `offset` is
  unavoidable, order it so the operand is POSITIVE. Two further behaviours from
  the same probe: **`stack` writes no negative values** (frames 99.99% negative
  produced a 100%-zero stack), and **`subsky` leaves a constant pedestal rather
  than zeroing the level** (a 500->800 ADU ramp comes back uniform at 627.00).
  **Corollary for verification — TRUE OF THE `stat` COMMAND, FALSE OF THE TOOL,
  and the distinction is load-bearing because this corollary is what sends sessions
  to an independent reader.** The COMMAND emits exactly five fields — the canonical
  parser (`flat_odd_component.py`, the single definition every instrument imports)
  reads `Mean, Median, Sigma, Min, Max` and there is **no pixel count**, so nothing
  in that line reveals how many pixels were excluded. **But `sirilpy`'s `ImageStats`
  carries fourteen, including `total` (*"total number of pixels"*) and `ngoodpix`
  (*"number of non-zero pixels"*) — so `total − ngoodpix` IS the excluded-pixel
  count**, per channel, per region, headless, via `get_image_stats` /
  `get_selection_stats` / `get_seq_stats`. **The instruments CAN see the damage; the
  five-field stdout line is what prevented it.** An independent reader is still
  valid and is no longer the only route.
  **CODE AGAINST THE MEASURED OBJECT, NOT THE ANNOTATION — `get_selection_stats`
  has carried a defect in each half of its surface.** Upstream (present in the
  1.4.4 source and on master, unfiled as of 2026-08-22 — issues and MRs searched)
  its annotation reads `-> Optional[PSFStar]` with Args prose copied verbatim from
  `get_selection_star`, while its own Returns: line and its code agree on
  `ImageStats` — verified BY EXECUTION: sirilpy 1.0.25 on a real SPCC stack
  returns `sirilpy.models.ImageStats`, all fourteen stats fields, zero star-model
  fields (`datasets/aug09/set-05/sirilpy_work/probe_type.json`). The behavioral
  half is FIXED on this build: #1673 (channel argument ignored, green returned
  for every channel; closed 2025-06) — the same probe reads three DISTINCT
  per-channel medians on an SPCC stack.
  **AND THE SAME LAYER REMOVES A WHOLE DEFECT CLASS RATHER THAN ONE CLAIM: STDOUT
  SCRAPING.** The API returns typed values deserialised from a binary struct — no
  regex, no stdout, nothing to parse wrong. **`Sigma: -nan` is not a hazard when the
  field arrives as a float**, and that defect (a copied numeric-only regex silently
  dropping a zero-variance box) is recorded twice in this registry, in two
  instruments, from one copied pattern. Nine further per-region statistics the
  command never prints come with it — `avgDev`, `mad`, `sqrtbwmv`, `location`,
  `scale`, `normValue`, `bgnoise`.
  **WHAT DOES NOT CHANGE, AND WHY: every CLIPPING claim above STANDS.** `cmd()` is a
  pure pass-through and the API surface contains **zero** arithmetic or pixel
  operations — no `offset`, `idiv`, `fdiv`, `subsky`, `imul`, `isub` — so every one
  reaches the same C path and clips identically. **The only bypass is
  `get_image_pixeldata()` / `set_image_pixeldata()`, raw numpy over shared memory,
  and it is closed by DOCTRINE rather than by capability: doing the arithmetic in
  numpy on the deliverable's pixels is what the bright line forbids.** Stated
  explicitly because a session that finds those two methods will otherwise conclude
  the clipping problem is solved.

- **`seqsubsky` REFUSES A FRAME CARRYING NEGATIVE PIXELS** — *"Failed to generate
  background samples for image 0: removing the gradient on negative images is
  not supported"*. Pedestal-free dark-subtracted lights always carry them and
  flat division amplifies them (calibrated aug09/set-05 frames measure a minimum
  of **-2635 ADU**, from division by the flat's near-zero pixels), so any
  background operator run on flat-fielded pedestal-free data needs a constant
  pedestal added first. The pedestal **cancels exactly** out of the operator —
  the plane fitted to `C+P` is `(plane of C)+P`, so `subsky` returns
  `C - P_t + c_t` either way — and costs nothing numerically (a 30% gradient
  still resolves to ~2250 float32 levels at a 56k pedestal). Verify positivity
  with a guard that can fail, and remove the pedestal with `isub`, not `offset`
  (entry above).

- **Siril `stat` says "no data" by SAYING NOTHING, and a parser that does not
  expect the silence mis-pairs every later box.** `stat` excludes zero pixels
  from every estimator, so a selection that is ENTIRELY zero-coverage echoes
  its `Current selection` line and then emits no layer line at all. Anchoring
  the parse on the SELECTION echo (not on the layer lines) makes that box carry
  zero channels instead of silently stealing the next box's numbers — the same
  defence `starlight_preservation.py` uses. MEASURED: 234 of 4000 grid boxes on
  the aug06 union returned a selection with no stat behind it.

- **Siril SPCC SIGSEGVs (exit 139) in aperture photometry when the sensor DATABASE
  is missing — not a data/field bug.** MEASURED on a fresh x86 rig: the crash hit
  at "Applying aperture photometry to N stars" on ANY star count (5305, 106, 291),
  any field size (full 20° or a 7.5° crop), and single- or multi-thread — the SPCC
  sensor/filter/white-reference database dir was absent, so siril applied a
  `(null)` sensor response and dereferenced it. The catalog (Gaia chunks) being
  present is NOT enough; the sensor database is a SEPARATE git repo. The tell is
  `spcc_list oscsensor` returning EMPTY and a log line "Unable to open directory:
  .../siril-spcc-database". Fix = clone it (CLAUDE.md Environment, SPCC
  prerequisites). Do NOT chase the star count, field width, catalog format, or bit
  depth — all ruled out; the crash prints nothing useful and mimics a data bug.

**Tool state / plumbing** (a persisted preference and a dropped header are both
SILENT — pin the state, never inherit it):
- **Siril `stat` prints `Sigma: -nan` on a ZERO-VARIANCE selection, and a
  numeric-only regex then fails to match the WHOLE line — so a uniform region
  reads back as "no data" rather than as a measurement.** The failure is silent
  in both directions: an instrument that anchors its parse on the selection echo
  drops that box (it calls flat sky UNCOVERED); one that anchors on the layer
  lines shifts every later box's numbers up by one and mis-attributes the entire
  grid. Accept `nan` in the `Sigma` and `bgnoise` classes — `[-+0-9.eEanN]+`.
  The affected regions are exactly the ones a coverage or flatness test lands
  on: a saturated patch, a synthetic uniform card, a clipped rim. FOUND TWICE
  now, in two instruments, from one copied regex — the first time by the UNIFORM
  control of the per-group flat work (the one arm that produces uniform crops
  could not be measured at all), the second by `coverage_frame.py --selftest`,
  whose uniform planted ringing band reproduced it on the fixture's first run
  and whose non-zero falsification step therefore passed for the wrong reason.
  `starlight_preservation.py` carried the same latent copy and is fixed; the fix
  is provably neutral there (every paired block and every fit identical before
  and after, since no 235,000-px sky cell is zero-variance).
- **`seqapplyreg -interp=none` FAILS OUTRIGHT ON A HOMOGRAPHY-REGISTERED SEQUENCE —
  it does not degrade silently, and `-interp=nearest` is the no-blur control to use
  instead.** Siril's help says `none` forces the transform to a SHIFT, and a
  homography cannot be reduced to a shift, so the command errors rather than
  quietly dropping to something cheaper. Found by failing, during the resample-cost
  arms, where a zero-interpolation arm was wanted as the control that CAN read zero.
  **The tree already contained `-interp=none` in four places and none of them is
  this fact:** `run_lunar_pipeline.sh` pins it and `check_registration_pins.sh` +
  `README` record that pin as the guard's one interpolation EXEMPTION. That is a
  USE, not the failure — and the lunar route is SHIFT-registered, which is exactly
  why its exemption is safe and why reading it as general clearance would be wrong.
  (Migrated out of `BACKLOG:resample-cost-and-drizzle` before that item was shed;
  the arms it came from are `datasets/aug06/experiments.jsonl` →
  `resample_cost_arm_d_siril_pass`.)

- **SIRIL FALLS BACK TO AN UNWEIGHTED MEAN AT ANY PIXEL WHERE EVERY SURVIVING
  SAMPLE HAS ZERO WEIGHT — so a weighted stack silently contains unweighted
  pixels.** The vendor's own stated reasoning is that it is
  "better than a black pixel".
  (DOCTRINE — the ORACLE's source read; **not probed on this rig**, where siril is a
  flatpak binary. The phrase and the behaviour occur in no tracked file, so this is
  the first home.) It is filed here rather than in `TOOLS.md` Tier 1 deliberately:
  this is not a tool-CHOICE fact, it is a SILENT-BEHAVIOUR fact, and it belongs with
  `idiv` clipping at 1.0 and `stat` excluding zeros — the family whose defining
  property is that the output looks healthy.
  **Why it matters here specifically:** the compose weights by member noise
  (inverse-variance) or by `nbstack`, and coverage at a union canvas's edges is
  exactly where sample counts collapse — so the pixels most likely to hit the
  fallback are the union's rim and corners, which is also where this repo's largest
  measured defect lives. A rim pixel that quietly switches weighting scheme is
  indistinguishable in the product from one that did not.
  **What is NOT established, and must not be inferred:** the firing CONDITION here
  (whether any real product has hit it), the SIZE of any resulting discontinuity,
  and whether it applies to the plain-mean sub-stack compose at all — a plain mean
  has no weights to zero. **The probe that would settle it costs one run:** stack a
  fixture whose members are constructed so one region's samples all carry zero
  weight, and compare that region against the weighted arithmetic. Until then this
  is a vendor claim about a code path, not a finding about our products.

- **Siril `idiv` CLIPS AT 1.0, SILENTLY — so a ratio of two comparable images (the
  standard flat-vs-flat instrument) loses its whole upper tail with no warning.**
  The tell is a whole-frame `stat` printing **Max exactly 65535.0**. MEASURED on a
  ratio of two 250-frame sky flats: `idiv` reported Max 65535.0 and mean 63073.6,
  while the SAME division via `fdiv <B> 0.5` and `fdiv <B> 0.25` agreed exactly
  with each other after rescaling — true max **112156** (ratio 1.711 on the 65535
  scale) and mean 63115.4: idiv truncated everything above 1.0 and dragged the
  mean 0.066% with it. **Use `fdiv <B> <scalar>` with a scalar that keeps the
  result inside range** (0.5 suffices when the two images are comparable); the
  scalar is global and cancels out of any ratio-of-medians statistic.
  **What saves you depends entirely on WHERE the ratio sits.** When the bulk of
  the frame is below 1.0, regional MEDIANS survive a truncated tail (a within-set
  flat ratio at median 0.963 read corner spread 3.4817 clipped vs 3.4814
  unclipped, identical +0.0705 %/1000px slope). When the ratio straddles or
  exceeds 1.0 the medians go too, catastrophically — MEASURED on the five july31
  between-set flat ratios (corner spread at box 400 / margin 200, `idiv` against
  an unclipped `fdiv` leg): **−2.4, −0.7, −5.7, −3.3 and −9.1 percentage points**
  (flat01/flat04 reading 18.715 against a true 27.843 — **33% understated**), and
  flat03/flat04's `idiv` leg has a whole-frame MEDIAN of exactly 65535.0, i.e.
  over half the frame pinned at the clip. Never reason about whether the medians
  are safe — rebuild with `fdiv` and compare. Two scalars that agree after
  rescaling (0.25 vs 0.5) is the positive control that no truncation is moving
  them; a Max still at 65535.0 at BOTH scalars is a genuine divide-by-near-zero
  spike, not bulk clipping.
  **The corollary: RECORD THE SCALAR.**
  `datasets/july31/flat_gradient_measurement.json` states its instrument as
  "`idiv` of one flat by another"; its two surviving artifacts are reproduced
  exactly by `fdiv <B> 0.5` and are exactly 0.5000x a plain `idiv` of the same
  flats. An undocumented scalar is what kept that record's numbers off the clip,
  and anyone reproducing it AS WRITTEN would have understated every figure by up
  to 9.1 points. The measurement was right and the method line was wrong, which
  is the harder failure to catch.
- **Siril's FITS extension is a PERSISTED preference; every generated `.ssf`
  must pin `setext`.** `extension=` in `config.1.4.ini` decides what `convert`,
  `save` and `-out=` write, and a script that does not set it inherits whatever
  ran last — including another project's chain sharing the same rig. Measured
  against the repo's `.fit` globs with the setting on `.fits`:
  `build_master_dark.sh` reported *"siril exited clean but wrote no master"* on
  a master that had built **correctly**, and its `rm -f work/dark_*.fit` cleanup
  matched nothing, leaking **9.2 GB**; `build_sky_flat.sh` and
  `run_undistort_pipeline.sh` abort with *"calibrated nothing"*. Siril logs
  *"Script execution finished successfully"* throughout, so the cause reads as a
  data or Siril bug. Exactly the class `setcompress 0` is already pinned for.
  Bash `*.fit` does not match `*.fits` — an extension is not a glob prefix.
- **Calibration dirs are PLURAL — Siril's own convention** (`lights` / `flats` /
  `darks` / `biases`, never a singular). A singular staged dir (`dark/`) holds
  ≥8 raws, so the session chain and the web set-kind rule classified it as a
  **LIGHT set** and would carry the dark frames to frame QA, mount derivation
  and a full stack; both now list the singulars as calibration, and the
  builders still require the plural and stop loudly.

- **Never export a numpy/FITS-row-order pixel box to Siril `crop` unverified** —
  Siril's crop y-origin is the OPPOSITE end (y_siril = H − y_np − h), so an
  unverified export ships a vertically mirrored window. Measured: a
  coverage-validated box (map Min = 25 sub-stacks everywhere in numpy coords)
  statted **Min 0** after export — a zero-coverage wedge shipped in a render.
  The guard is tool-sourced and cheap: crop the instrument MAP with the exact
  same args and require Siril `stat` to reproduce the claimed bound before any
  product crop.
- **SIRIL `update_key` SILENTLY TRUNCATES A STRING VALUE AT THE FIRST `/` — it
  begins the FITS comment field.** Probed directly on a 16x16 test FITS through
  siril 1.4.4:
  | written | stored |
  |---|---|
  | `update_key K1 "aug06/set-01"` | `'aug06'` |
  | `update_key K3 "aug06/set-01,july31/set-01"` | `'aug06'` |
  | `update_key K2 "a,b"` | `'a,b'` (commas are fine) |
  | `update_key K4 "aug06_set-01+july31_set-01"` | intact |
  | `update_key K5 T` | `True` (a FITS boolean, not the string) |
  No error, no warning, exit 0. **CALSET is `<session>/<set>` by construction**,
  so every provenance stamp routed through siril loses the set and claims the
  whole session — and the stamp is the thing a compose gate reads to decide
  whether members are compatible. The existing corpus escaped only by accident:
  `backfill_substack_provenance.sh` wrote its keys with astropy `fits.setval`,
  which is why the backfilled `CALSET = july31/set-01` values kept their slash
  while a live build would not have. It would have corrupted the first rebuild.
  FIX, and it follows the repo's own precedent: provenance keys are applied with
  a FITS library (`header_apply_keys`, headers only, no pixel access) while the
  acquisition keys stay on siril's `update_key`, which is siril's own data and
  slash-free. Anything with a path, a date-with-slashes or a ratio in it must not
  go through `update_key`.

- **SIRIL REPORTS X, Y AND `angle` IN A TOP-DOWN FRAME — THE MIRROR OF THE FITS
  BOTTOM-UP CONVENTION — AND ALL THREE ARE MUTUALLY CONSISTENT.** Two independent
  measurements, which is why the label can be trusted:
  (1) synthetic stars planted at a known **+20.0°** come back from `findstar` at
  **−20.0° at every L ≥ 0.4 px** (−19.89 to −20.11 across an L sweep), and the
  reported Y flips with the angle — of 400 planted stars, **400 match under
  y → H − y and 0 match as planted** (`psf_calib.py`);
  (2) `source-extractor` 2.28.2, whose `Y_IMAGE` is standard FITS bottom-up, run
  on the same frame: **300 of Siril's 300 brightest match under y → H − y**, and
  only 2 of 300 match as reported (`psfex_work/`).
  Since a FITS file's first data row IS the bottom row, FITS y increases with the
  array row index while Siril's y decreases with it. **So Siril is the mirror of
  FITS, not an instance of it** — an earlier version of this entry labelled it
  "the FITS bottom-up frame", which is exactly backwards and would hand the wrong
  sign to anyone bringing in a WCS.
  **What is load-bearing is the mutual consistency, and that is unchanged:** any
  quantity built from Siril's own X, Y and `angle` TOGETHER — field azimuth,
  θ − φ, the radial/fixed decomposition, a drift bearing cross-matched from
  findstar lists — is unaffected by the frame entirely. What inverts is handedness
  and any comparison against something measured in FITS coordinates: a WCS/CD
  matrix, a `source-extractor` catalogue, a parallactic angle. Convert through the
  mirror or the sign of the answer is wrong. There is also a 1 px offset from FITS
  1-based indexing on top of the mirror.

