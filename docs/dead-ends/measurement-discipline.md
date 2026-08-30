# Measurement discipline — comparisons, floors, controls

Part of the dead-end registry — `docs/dead-ends.md` is the index, and
`00-registry-contract.md` governs how entries are read, cited, written and
deleted. Entries are maintained IN PLACE (pre-compression forms are in git;
the pre-split single-file registry is `docs/dead-ends.md`'s own history).
Cross-references to sibling files are written as (`<file>.md`) pointers.

<!-- registry content below; docs/dead-ends.md is the index -->
- **DERIVE A COMPARISON CROP FROM THE SHARED PIXEL GRID, NEVER FROM EACH
  SURFACE'S OWN PLATE SOLVE.** Cropping two surfaces to "the same sky" by
  mapping a sky box through each one's own WCS looks obviously right and is
  wrong: two independent solves of the same field disagree by more than the
  tolerance a per-cell comparison needs (measured: solves of the same
  pixels landed 60–114 px apart, so a paired instrument read a surface
  against a shifted copy of itself — **the tell was a NULL CONTROL that had
  to read exactly 1.000 and read 1.069** on arms that were pixel-identical).
  **The cheap general check is the tool's own detections:** Siril `findstar`
  on both surfaces, cross-matched — 33,465 of 33,465 stars at median
  dx/dy +0.000, zero spread — proves the grid is shared and the crop must
  be the SAME PIXEL BOX (re-cropped that way the null reads
  1.0000 ± 0.0000). Applies to any paired measurement on separately-solved
  products; the star-match test costs one Siril call.
- **`register -2pass` GIVES THE REFERENCE FRAME NO TRANSFORM, SO IT RECEIVES
  NO INTERPOLATION AT ALL — MEASURE A NON-REFERENCE FRAME, ALWAYS.** A
  before/after taken on the reference reads a PERFECT NULL for a stage that
  did nothing to it — measured, and it nearly shipped as a spectacular
  result (a resampling pass "costing exactly nothing" at w identical to
  four decimals; the reference happened to be the measured frame, and an
  earlier arm had happened to pick a different one, which is why the trap
  had never surfaced). It was caught only because the null was TOO CLEAN —
  the weakest possible defence. **Generalises to ANY before/after on a
  registered sequence**: the reference is picked by the tool unless pinned,
  so which frame is safe to measure changes between runs (`setref`;
  closed — the reference pin shipped: `run_undistort_compose.sh --ref`,
  `REGREFSR` pinned).
- **A POSITIVE CONTROL DRAWN FROM A RECORDS FIELD IS ONLY A CONTROL FOR
  SIGNATURES THAT DO NOT USE THAT FIELD — check the cull's provenance
  before using a cull as a control.** MEASURED (pre-registered, which is
  what made the failure legible): a cloud-signature test used a set's
  44-frame `stack.exclude` list as its positive control — and the cull's
  own criterion was a threshold on the two fields under test (44 of 44
  selected on `nstars`, 29 on `bg`), so **on that control the signature
  could not have failed**: "a signature that cannot be made to fail on
  demand is decoration", arriving from the control side. **The rescue
  generalises: a partially-circular control usually contains a non-circular
  sub-population** — the 15 frames flagged on `nstars` only had `bg` as a
  free variable, and `bg` separated them at Z +4.05 against +1.12 in a
  matched clean set; better, that sub-population is conditioned AGAINST the
  effect, so the surviving estimate is CONSERVATIVE. The circular headline
  was 1.5× the honest one, and the strongest-looking result (Z −8.70) was
  entirely selection and was withdrawn. **State which fields built the
  control, and quote the record that says so.**
- The GATE must be a composition-agnostic STATISTICAL sky scope —
  whole-frame reads real MW/object signal as a defect, and a geometric sky
  mask can't fix it (a bright object has no fixed band). Hand-picked
  patches miss defects a whole-scope measurement catches (the lesson that
  created the gate).
- **A NUMBER READ OFF A LOADED BOX IS NOT A MEASUREMENT — record the load
  with the reading, for EVERY tool, not just the slow neural ones.**
  MEASURED: a grid positive control read Siril sigma **14666** under 500
  concurrent darktable warps and **45398.0** on three independent idle
  runs — a 3× error on identical inputs and an identical pinned model (an
  earlier hit at load average 300 cost ~30 min of CPU and a retracted
  registry entry). Check `uptime` before quoting any number and put the
  load in the record. **SCOPE, because the obvious inference is wrong: the
  pipeline's own output does NOT move with load** — the production
  undistort warp was bracketed deliberately at 1-min loadavg 25–28 and
  every pair is all-nil bit-identical
  (`git show c7db472:datasets/july31/set-01/qa_work/warp_load_determinism.json`
  — the record was swept in the july31 raws-only reset and is carried as
  INHERITED). The deliverable is deterministic; it is the FIXTURE reading
  that moved. Distinguish the two before concluding a route is
  unreproducible.
- **A stack-level A/B on this chain cannot resolve anything below its
  run-to-run floor.** MEASURED (identical frames, identical recipe, two
  runs of the undistort chain): the products differ by **2.06% of sky at
  star edges and 0.073% in flat sky**, the difference tracking local
  gradient (ratio 28.4×) exactly as resampling error does — interpolation
  variance in registration, not the knob under test. Cost of not knowing:
  a calibration A/B whose whole-frame difference read "√2 × the per-arm
  noise" and was entirely the floor. **Bracket a stack-level experiment
  with a SAME-ARM REPEAT RUN, not just an A/B**, and treat effects under
  ~0.07% flat-sky / ~2% star-edge as unmeasured; measure a calibration
  change where it is unambiguous (on the MASTER), not where it is swamped.
  **SCOPE — "the chain is not pixel-reproducible" is true of THIS
  COMPARISON and false as a property of the chain:** the floor is between
  two separately REGISTERED runs. The compose stage, the whole groups
  route, and the render tier are each measured bit-reproducible (entries
  below) — **the non-reproducible quantity is a REGISTRATION SWEEP; cite
  this floor for A/Bs that re-register, never as a general statement.**
- **THE STACK ROUTE'S COMPOSE STAGE IS BIT-REPRODUCIBLE — the "register
  sweep is non-deterministic" exemption does not cover it.** Measured, two
  sets recomposed from their own unchanged sub-stacks and differenced with
  Siril `isub`: all three channels nil, both times — a compose-level A/B
  may be judged on BYTES, and a same-arm compose repeat is a real zero.
  **EXTENDED — the WHOLE GROUPS ROUTE is bit-reproducible:** one set
  rebuilt TWICE from the same 500 culled raws through the entire chain
  (calibrate → warp → per-group register → GESD stack → compose), both
  differenced against the ARCHIVED product — **all six pairwise directions
  all-nil, all three channels**, so the rebuild-repeat floor is 0.00 px and
  the commits that landed in between are MEASURED pixel-neutral. **Two
  controls make this a result instead of a check that cannot fail** (Siril
  reports an all-zero difference as a FAILURE string): the guard was BROKEN
  on purpose (`(x1.01) − x` prints nonzero means, so the nil is a measured
  zero), and every pair was differenced in BOTH directions after a probe
  showed `isub` does not clip negatives. **SCOPE, narrower than "the chain
  is deterministic":** the groups route never runs a 500-frame sweep —
  per-frame registration is measured deterministic at n=100 (×5 groups ×2
  arms) and the compose at n=5; the single-pass 500-frame sweep is a
  different problem size and unmeasured, so the README exemption survives
  exactly where it was written. Numbers: `rebuild_repeat_floor_set01` at
  `git show c7db472:datasets/july31/experiments.jsonl` (swept in the
  july31 reset; carried as INHERITED). A dry-run surface that stops short
  of the guards that can refuse the run is the wrong half of a dry run —
  `--plan` exercises the resume guard and the dwell floor and exits.
- **Do NOT assume "neural / ONNX / multi-threaded" means non-reproducible —
  MEASURE it. On this rig the whole render tier is BIT-IDENTICAL run to
  run.** Two identical runs of each stage compared with Siril `isub`:
  StarNet2 — identical, and identical AGAIN across thread counts (28 vs
  1); Cosmic Clarity denoise (`--disable_gpu`) — identical, also across
  thread counts; Siril stretch + `asinh` + `pm` recombine — identical. So
  byte-identity IS the available bar and a re-render reproduces exactly;
  neither binary even exposes a thread/seed/device flag to pin — the
  reproducibility came free rather than from pinning.
- **A "run-to-run floor" derived from two runs whose inputs were never
  recorded is not a floor.** A 1.34% colour figure from two render records
  read as a same-arm repeat was hardcoded into a verdict that called
  anything below it "unmeasurable" — but the old records logged neither
  their linear source nor their knob provenance, and once every stage
  measured deterministic, two identical runs could not have produced
  different ratios: something unrecorded differed. **A floor is a
  MEASUREMENT, not a subtraction of two numbers you happen to have** —
  bracket it deliberately with both arms' provenance recorded, or you
  build a threshold that hides real effects (the cost here: a verdict
  permissive enough to call a real 1% colour shift noise). The stack-level
  floor above is real but measures interpolation variance between
  separately registered stacks — it does not apply to two renders of one
  stack.
- **NEVER measure a faint BROAD halo with region MEDIANS — the median is
  robust against exactly the wide low tail under test.** Measured cost: a
  median-based two-point control read a halo "identical before vs inside
  the haze window" and a mechanism was mis-attributed on it; the MEAN-based
  9-timepoint timeline over the same data shows the halo GROWING all night
  (star-box-minus-flanks 6.25 → 10.3 ADU across sets, +91% session-wide,
  accelerating late, alongside a monotonic FWHM rise and a terminal nstars
  crash). Two lessons: (1) means or outer-annulus statistics for broad-glow
  photometry; medians only for compact-source-robust background; (2) a
  two-point control CANNOT test a monotonic-growth hypothesis — sample the
  full span. The growth pattern + conditions make DEW ON THE LENS the
  leading attribution (user field call; the full investigation is in git
  history — the july23 session is archived). The per-set flat-cancellation
  variance on the final stacks (Deneb-box excess 0/0/0 → +2.5/+5.8/+10 ADU
  across sets) remains measured and stands — a lights-built flat both bakes
  in and partially cancels a time-varying glow, inconsistently per set.
- **CANVAS-X FRACTIONS ARE NOT PORTABLE ACROSS PRODUCTS — A BAND IS ADDRESSED IN
  SKY COORDINATES.** MEASURED: the union defect point RA 294.86 sat at x = 76.2 % of one
  canvas and its control RA 314.72 at 41.2 %, so "x = 15–30 %" on a different product
  addressed RA 328–320 — different sky, which read clean. `shape_at_sky.py` places its
  boxes by each product's own WCS for this reason; a station is a sky position, and a
  canvas fraction is only the address it had on one product.
