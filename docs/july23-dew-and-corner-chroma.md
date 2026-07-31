# july23 session — lens dew (known environment issue) + the resolved warp-leg ICC defect

- **Question / scope** — The july23 NAN session's two data-quality findings,
  recorded current-state: (A) progressive DEW on the lens — the one
  REMAINING, environment-side issue, which sized the final combine; (B) a
  warp-leg ICC defect — found, fixed, verified (closed).
- **Context** — Session 00:40–02:31 EDT 2026-07-24: Z6III + 24-70/4 S @
  70 mm f/4, fixed tripod, 4×~400×3 s ISO 1600, flatless (per-set sky
  flats), 211 matched darks. Chain: 32-bit float durable core
  (calibrate → undistort → register → stack → solve → SPCC), Siril 1.4.4.

## A. Lens dew — the known environment issue

**Signature on this session (all Siril-measured; records in
`datasets/july23/dew_chroma/`):**

- The brightest star's scattering halo GROWS through the night: Deneb
  star-box-minus-flanks (G, ADU) 6.25 → 7.6 → 7.7 → 8.5 → 10.3 across sets
  01–03, then 7.1 → 9.9 → 12.0 WITHIN set-04 — +91% over the session,
  accelerating as the lens cools. MEANS, never medians (a median is blind
  to a broad faint halo — dead-ends registry).
- FWHM rises monotonically 2.627 → 2.72 px and never recovers; faint-star
  counts crash (−13–16%) only in the final ~20 min — faint-signal loss
  precedes the visible film.
- The user-visible symptoms: a scattering disc around Deneb (set-04) and
  lightened contrast around stars (set-03's later frames).

**Disposition (user-decided):** the FINAL combine is **sets 01+02 only**
(799 frames) — the dew-clean sets. Set-03 (full-depth 303-frame stack,
dew-tail 9752–9848 already recipe-culled) and set-04 (398-frame stack)
remain preserved per-set products, excluded from the deliverable
(`datasets/july23/combine_decision.json`). Dew cannot be stacked through:
the veil is consistent within contiguous frame blocks, so per-pixel
rejection never sees it — culling is by frame/set.

**For future sessions:** prevention is acquisition-side — the dew-control
line in the checklist (`docs/dead-ends.md`): low-power lens heater band
from session start, minimum power; the 24-70's petal hood is weak at
70 mm; watch the brightest star's halo live; if dew is found, warm and
continue — never stack through it. Post-hoc detection is reproducible:
re-run the halo timeline from `sessions/<session>/work/dewprobe/`
(mean-based star-minus-flanks ministacks + the frame-QA FWHM/nstars
trends).

## B. Warp-leg ICC defect — RESOLVED

**Defect:** the wide-field chain's float TIFF round trip (Siril `savetif32`
→ darktable warp → reconvert) was not an identity at low levels: a TRC
toe-segment mismatch between Siril's embedded sRGB variant and darktable's
SRGB export inflated values +4.7% at linear 0.0015, fading to identity by
0.003. A 3 s sky (~0.0016) sits inside the band; a 6 s sky sits above it —
so the defect was level-gated to short-exposure classes and invisible to
star-amplitude verification. On this session it rendered as a radial red
corner cast (R/G corners 1.04–1.07 vs centre) on every product.

**Fix (in `run_undistort_pipeline.sh`):** the TIFF ships UNTAGGED (exiftool
strips the ICC profile in the same pass that copies the lens EXIF) and
darktable exports `--icc-type LIN_REC709`.

**Verification (rebuild of all member sets through the fixed leg):**
round-trip ratio 1.0000 at every level and channel with the warp confirmed
firing (corner displacement 0.22 vs centre 0.003); corner chroma collapsed
to **R/G 1.008–1.018** on every product (july14 reference ≤1.009); the
SPCC K family tightened to G 0.662–0.668 (per-set scatter 0.006 vs ~0.03
pre-fix). Ledger: `datasets/july23/experiments.jsonl`
(`icc_leg_fix_rebuild`, WIN).

**Durable contract + traps** (dead-ends registry, ICC entry): float leg =
untagged linear TIFF + linear export profile; never Siril `icc_remove`
before `savetif32` (global ~1/12.92 scale); verify any ICC change with a
ratio-vs-level curve down to the exposure class's own SKY level — star
amplitudes alone cannot see a toe error.

## Final render state

`web/results/july23/stack_set-01+02_min.fit` (+`_wcs`/`_spcc`): 799 frames,
min-framing, nbstack weights. Judgment surfaces (pinned per-product rule,
16-bit PNG): `judge/set-01_399sp32…`, `judge/set-02_400sp32…`,
`judge/set-01+02_min32_spcc-linked.png`. Per-set stacks for all four sets
(and `stack_set-03_400full`) preserved beside them. The remaining
output-shaping work (background extraction, stretch policy — the render
tier, BACKLOG:`render-ladder`) is user-gated as ever; these surfaces are the durable
core's diagnostic finish.

## Sources

- Records: `datasets/july23/` (dew_chroma/ instruments, experiments.jsonl,
  per-set qa_work, combine_decision.json).
- Dew phenomenology + prevention (research sweep, cited in full in git
  history of this doc): skyandtelescope.org dealing-with-dew · astropix.com
  BGDA ch.2 · skyatnightmagazine.com dew guides · blackwaterskies.co.uk
  (dew-point formula) · philhart.com (2–3.4 W lens bands) · Cloudy Nights
  358932/643667/517557/869299/946505 · photographingspace.com dew-proofing.
- ICC: measured on-rig (`bisect/iccprobe` method); dead-ends ICC entry.

## Verdict / recommendation

Dew is an acquisition-side issue with a working detection instrument and a
checklist fix — no processing remedy exists or should be attempted. The ICC
defect is closed with a measured identity contract. The final combine is
the cleanest honest product of this session's data.

## Status

A: EMPIRICALLY MEASURED (timeline + disposition executed). B: RESOLVED,
verification measured on the shipped products.

## Graduation

dead-ends: mean-not-median halo photometry; dew-control checklist line;
the ICC float-leg contract + icc_remove trap; verify-at-sky-level rule.
BACKLOG: the cull-spec and ICC-toe items are closed and removed; dew disposition executed.
