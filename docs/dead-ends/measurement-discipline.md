# Measurement discipline — comparisons, floors, controls

Phase-1 split of `docs/dead-ends.md` (organize-only; the original file stays
the live registry until the merge is decided). Content below the marker is
VERBATIM from the original, so in-text "above"/"below"/section references may
point at entries now homed in a sibling file — `README.md` in this directory
carries the index, the assignment rule, and the block manifest that resolves
them. Do not edit below the marker while the refactor is in phase 1; the split
is re-derivable from the manifest and verified byte-identical by `split.py`.

<!-- == verbatim content from docs/dead-ends.md below this marker == -->
**QA / scope:**
- **DERIVE A COMPARISON CROP FROM THE SHARED PIXEL GRID, NEVER FROM EACH
  SURFACE'S OWN PLATE SOLVE.** Cropping two surfaces to "the same sky" by
  mapping a sky box through each one's own WCS looks obviously right and is
  wrong: two independent solves of the same field disagree by more than the
  tolerance a per-cell comparison needs. MEASURED on the aug06 3-set union
  (31.5° wide, 17.07″/px): solves of the same pixels landed 60–114 px apart, so
  the derived boxes differed and a paired instrument read a surface against a
  shifted copy of itself. **The tell was a NULL CONTROL that had to read
  exactly 1.000 and read 1.069** — the reproduction arm was pixel-identical to
  its control (0 differing of 101,278,350) and could not honestly return
  anything else. **The cheap general check is the tool's own detections:** Siril
  `findstar` on both surfaces, cross-matched — **33,465 of 33,465 stars at
  median dx +0.000 / dy +0.000, zero spread**, which proves the grid is shared
  and therefore that the crop must be the SAME PIXEL BOX. Re-cropped that way
  the null control reads 1.0000 ± 0.0000. Applies to any paired measurement on
  separately-solved products, and the star-match test costs one Siril call.
- **`register -2pass` GIVES THE REFERENCE FRAME NO TRANSFORM, SO IT RECEIVES NO
  INTERPOLATION AT ALL — MEASURE A NON-REFERENCE FRAME, ALWAYS. A before/after taken
  on the reference reads a PERFECT NULL for a stage that did nothing to it.**
  MEASURED, and it nearly shipped as a spectacular result: a series comparing
  "darktable only" against "darktable THEN Siril" read **identical at w 2.3299**,
  i.e. the Siril resampling pass appearing to cost exactly nothing — which reads as
  a quadrature failure worth investigating. The cause was that 2pass had chosen
  image 1 as its reference and `S_w_00001` is an untouched frame. An earlier
  separate arm happened to pick image 5, which is why the trap had never surfaced.
  **It was caught only because the null was TOO CLEAN**, which is the weakest
  possible defence and not one to rely on.
  **Generalises past that experiment: this applies to ANY before/after on a
  registered sequence**, and the reference is picked by the tool unless pinned, so
  which frame is safe to measure changes between runs (`setref`, and
  `BACKLOG:single-pass-reference-lottery`). **The adjacent durable text is NOT this
  fact:** `scripts/stack/compose.py` records that *"the reference channel itself
  gets only the identity transform"* — a true property of one stage, in a script
  docstring, saying nothing about how to measure. (Migrated out of
  `BACKLOG:resample-cost-and-drizzle` before that item was shed; arms in
  `datasets/aug06/experiments.jsonl` → `resample_cost_series_run`.)

- **A POSITIVE CONTROL DRAWN FROM A RECORDS FIELD IS ONLY A CONTROL FOR SIGNATURES
  THAT DO NOT USE THAT FIELD — check the cull's provenance before using a cull as
  a control.** MEASURED, and the design was pre-registered before it ran, which is
  what made the failure legible rather than invisible. A test of whether a cloud
  signature separates from normal variation used a set's 44-frame `stack.exclude`
  list as its positive control, and reported the selection criterion as
  UNDOCUMENTED. **The criterion was documented in the ADJACENT KEY of the same
  object** — `stack.why`: *"auto-cull, standing policy: defect-side robust
  z >= 3.5 flags exclude"*, with per-frame flags showing **44 of 44 selected on
  `nstars` and 29 of 44 also on `bg`**. So the control was the OUTPUT of a
  threshold on the two fields under test: **on that control the signature could
  not have failed**, which is the item's own *"a signature that cannot be made to
  fail on demand is decoration"* arriving from the control side instead of the
  detector side.
  **THE RESCUE IS THE USEFUL PART, AND IT GENERALISES: a partially-circular control
  usually contains a non-circular sub-population — find the frames selected WITHOUT
  reference to the field you are testing.** Here 15 frames were flagged on `nstars`
  only, so `bg` was not their criterion, and `bg` separated them at **Z +4.05
  against +1.12 in a matched clean set** where the identical detector ran and
  flagged nothing. **Better still, that sub-population is conditioned AGAINST the
  effect** — nstars-only means their `bg` z was below the cull threshold — so the
  surviving estimate is CONSERVATIVE, not merely uncontaminated. The circular
  headline (Z +6.07 on all 44) was **1.5× larger** than the honest one, and the
  strongest-looking result of the whole test, `Z_nstars` −8.70, was **entirely
  selection** and had to be withdrawn.
  **So: state which fields built the control, and quote the record that says so.**
- The GATE must be a composition-agnostic STATISTICAL sky scope — whole-frame
  reads real MW/object signal as a defect, and a geometric sky mask can't fix it
  (a bright object has no fixed band). Hand-picked patches miss defects a
  whole-scope measurement catches (the lesson that created the gate).
- **A NUMBER READ OFF A LOADED BOX IS NOT A MEASUREMENT — record the load with
  the reading, for EVERY tool, not just the slow neural ones.** MEASURED:
  `verify_lens_card.py`'s grid positive control read Siril sigma **14666**
  while 500 concurrent darktable warps were running, and **45398.0** on three
  independent idle runs — a 3x error on identical inputs, identical optics and
  an identical pinned model. This is an instrument fact, not a tool fact (first
  hit reading a Cosmic Clarity probe while an unrelated job held the box at
  load average 300 — ~30 min of CPU and a registry entry that had to be
  retracted). Check `uptime` before quoting any number, and put the load in the
  record.
  **SCOPE, because the obvious inference is wrong:** this does NOT mean the
  pipeline's own output moves with load. The production undistort warp was
  bracketed deliberately — the exact `run_undistort_pipeline.sh` invocation on
  one real calibrated frame, three arms at 1-min loadavg 25.06 / 28.22 / 26.12,
  compared with Siril `isub`+`stat` — and every pair is **all nil,
  bit-identical**
  (`datasets/july31/set-01/qa_work/warp_load_determinism.json`). The
  deliverable is deterministic; it is the FIXTURE reading that moved.
  Distinguish the two before concluding a route is unreproducible, and note
  that the anomaly's own leg (a synthetic 16-bit card at `--icc-type SRGB`) is
  still unexplained.
- **A stack-level A/B on this chain cannot resolve anything below its run-to-run
  floor — and the chain is NOT pixel-reproducible.** MEASURED (identical frames,
  identical recipe, two runs of the undistort chain, identical output geometry):
  the two products differ by **2.06% of sky at star edges and 0.073% in flat
  sky**, the difference tracking local gradient (star-edge/flat-sky ratio
  **28.4×**) exactly as resampling error does — it is interpolation variance in
  registration, not the knob under test. Cost of not knowing this: a
  calibration A/B whose whole-frame difference read "√2 × the per-arm noise",
  which looks like a large real effect and is entirely the floor. **Bracket a
  stack-level experiment with a SAME-ARM REPEAT RUN, not just an A/B**, and
  treat any claimed effect under ~0.07% flat-sky / ~2% star-edge as unmeasured.
  Corollary: measure a calibration change where it is unambiguous (on the
  MASTER) rather than where it is swamped (on the finished stack).
  **SCOPE — "THE CHAIN IS NOT PIXEL-REPRODUCIBLE" IS TRUE OF THIS COMPARISON AND
  FALSE AS A PROPERTY OF THE CHAIN.** The floor above is between two separately
  REGISTERED runs, and registration interpolation is what varies. Measured
  elsewhere in this registry and not to be discovered by a reader who stops here:
  the groups route's COMPOSE stage recomposes BIT-IDENTICALLY, the whole groups
  route rebuilds all-nil across six pairwise directions, and every stage of the
  render tier is bit-identical run to run including across thread counts. **So the
  quantity that is not reproducible is a REGISTRATION SWEEP, not the chain** — cite
  this floor for A/Bs that re-register, never as a general statement.
- **THE STACK ROUTE'S COMPOSE STAGE IS BIT-REPRODUCIBLE — the "register sweep is
  non-deterministic" exemption does not cover it.** MEASURED, two sets: july31
  set-01 and set-02 each recomposed from their own UNCHANGED sub-stacks
  (`register s -2pass` → `seqapplyreg -framing=min` → `stack mean none`) and
  differenced against the original with Siril `isub` — **all three channels nil,
  both times**. SCOPE: n=2, same-arm, one rig, siril 1.4.4, and the COMPOSE
  sweep only (5 members). A compose-level A/B may therefore be judged on BYTES,
  and a same-arm compose repeat is a real zero rather than a tolerance.
  **EXTENDED — the WHOLE GROUPS ROUTE is bit-reproducible, not just the compose,
  so a full rebuild has a repeat floor of ZERO.** july31/set-01 rebuilt TWICE
  from the same 500 culled raws through the entire chain (calibrate → darktable
  warp → per-group `register -2pass` → GESD stack → compose) at `--group=100`,
  and both differenced against the ARCHIVED product: **all six pairwise
  directions all-nil, all three channels**. So the rebuild-repeat floor the
  route claims were gated on is 0.00 px, and the three commits that landed
  between the archived build and the rebuilds are MEASURED pixel-neutral rather
  than assumed so.
  **Two controls that make this a result instead of a check that cannot fail**,
  both required because Siril reports an all-zero difference as a FAILURE string
  (*"Statistics computation failed for channel N (all nil?)"*): (1) the guard
  was BROKEN on purpose — `(x1.01) − x` prints Red/Green/Blue mean 0.3/2.1/1.5,
  so the nil is a measured zero; (2) every pair was differenced in BOTH
  directions, since a one-way nil would only prove A ≤ B if `isub` clipped — and
  a `(x0.99) − x` probe showed it does NOT clip (means −0.3/−2.1/−1.5, minima
  −589.3/−655.3/−567.2).
  **SCOPE, and it is narrower than "the chain is deterministic":** the groups
  route never runs a 500-frame sweep. It runs five INDEPENDENT 100-frame
  `register -2pass` sweeps plus the 5-member compose. So per-frame registration
  is measured deterministic at **n=100** (×5 groups, ×2 arms) and the compose at
  n=5; the SINGLE-PASS 500-frame sweep is still a different problem size and
  still unmeasured, so the README exemption survives exactly where it was
  written and nowhere wider. Numbers: `datasets/july31/experiments.jsonl`,
  `rebuild_repeat_floor_set01`. **A dry-run surface that stops short of the
  guards that can refuse the run is the wrong half of a dry run** — `--plan` now
  exercises the resume guard and the dwell floor and exits.
- **Do NOT assume "neural / ONNX / multi-threaded" means non-reproducible — MEASURE
  it. On this rig the whole render tier is BIT-IDENTICAL run to run.** Two
  identical runs of each stage, compared with Siril `isub` (all-nil =
  bit-identical): StarNet2 via siril `starnet -stretch` — identical, and
  identical AGAIN across thread counts (default 28 vs `setcpu 1`, and
  cross-compared); Cosmic Clarity denoise (`--disable_gpu`, separate mode) —
  identical, and identical across thread counts too (28 vs `OMP_NUM_THREADS=1`),
  so the determinism is not an artifact of one machine state; Siril's stretch +
  `asinh -human` + `pm` recombine — identical. So byte-identity IS the available
  bar here and a re-render reproduces exactly. Neither binary even exposes a
  thread/seed/device flag to pin (StarNet2's CLI is I/O + weights + stride +
  upsample only), so the reproducibility came free rather than from pinning.
- **The trap that replaced: a "run-to-run floor" derived from two runs whose
  inputs were never recorded.** A 1.34% colour floor was taken from two render
  records read as a same-arm repeat and hardcoded into a verdict that then
  called anything below 1.34% "unmeasurable" — but the old record logged NEITHER
  its linear source NOR its knob provenance, so nothing in it established that
  the two runs shared inputs and knobs; once every stage measured deterministic,
  two identical runs could not have produced different ratios, so something
  unrecorded differed. **A floor is a MEASUREMENT, not a subtraction of two
  numbers you happen to have** — bracket it deliberately with both arms'
  provenance recorded, or you build a threshold that hides real effects. The
  cost here was a verdict permissive enough to call a real 1% colour shift
  noise. (The stack-level floor in this registry — 2.06% at star edges, 0.073%
  in flat sky — is real, but it measures INTERPOLATION variance between
  separately REGISTERED stacks; it does not apply to two renders of one stack.)
- **NEVER measure a faint BROAD halo with region MEDIANS — the median is robust
  against exactly the wide low tail under test.** MEASURED cost (july23 Deneb
  disc): a median-based two-point control read the halo "identical before vs
  inside the haze window" and a mechanism was mis-attributed on it; the
  MEAN-based 9-timepoint timeline over the same data shows the halo GROWING
  all night — G-channel star-box-minus-flanks 6.25 → 7.6 → 7.7 → 8.5 → 10.3 ADU
  (sets 01–03) and 7.1 → 9.9 → 12.0 WITHIN set-04 (+91% session-wide,
  accelerating late), alongside a monotonic FWHM rise 2.627 → 2.72 px and the
  terminal nstars crash (−13–16%, last ~20 min). Two lessons: (1) means (or
  outer-annulus statistics) for broad-glow photometry, medians only for
  compact-source-robust background; (2) a two-point control CANNOT test a
  monotonic-growth hypothesis — sample the full span. The growth pattern +
  conditions make DEW ON THE LENS the leading attribution (user field call;
  the full investigation record is in git history — the july23 session is
  archived); the per-set
  flat-cancellation variance on the FINAL stacks (Deneb-box excess 0/0/0 →
  +2.5/+5.8/+10 ADU across sets 01→04) remains measured and stands — a
  lights-built flat both bakes in and partially cancels a time-varying glow,
  inconsistently per set.

