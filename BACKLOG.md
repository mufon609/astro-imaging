---
id: meta/BACKLOG
type: meta
---

# BACKLOG

Deferred work — real, concrete, and would be lost otherwise; not on the
active roadmap. An item leaves when promoted to a roadmap phase, addressed,
or superseded.

## How this file works

**This file is self-governing** — it is the root authority for how the
BACKLOG is written, identified, and closed. Nothing outside it governs it.

**Sections.** Open items are partitioned by dependency shape:
**A — Priority sequence** (ordering / coupling constraints),
**B — Parallel batch** (renderer-pass items that ship together),
**C — Anytime** (no upstream blockers). **Default focus is C:** no
dependencies, finishable in one pass. Reserve A and B for sessions scoped
to them — starting a constrained item out of order half-bakes it and
clutters the file. Cross-reference entries with `**Blocks:**` /
`**Blocked by:**` lines so the dependency graph stays inline.

**Identifiers** (A1, B1, C1…) are positional working labels, not stable
IDs. A new entry takes the lowest unused number in its section, so numbers
**recycle**; once a section — and ultimately the whole BACKLOG — is cleared,
numbering restarts from 1. Because an ID is transient, **never reference it
outside this file** — not in code, docs, prompts, commit messages, or
`git log` searches. Describe the work; the commit diff + message are the
record.

**Opening an entry.** Write it forward-looking and prescriptive: the work
and why it matters. No "Surfaced from", audit/session label, or commit hash
pinning when the need arose — that history lives in `git log`.

**Closing an entry.** The goal is to REMOVE items, not annotate them.
Delete the block in full — no retirement marker, no placeholder; the
shipping commit's diff + message is the canonical record. Then sweep any
code comments that cited the closed ID (delete them, or rewrite to describe
current behavior) — that sweep is part of closing, not follow-up.

**Externally-blocked items** waiting on an event the repo can't drive (FOIA
resolution, registry access, third-party publication) live, when
topic-specific, in `meta/topic/research-queue.md` "Externally blocked". If a
genuinely toolkit-neutral one ever surfaces (rare), reinstate an "Externally
blocked" heading at the foot of this file.

---

## A. Priority sequence

Items with ordering or coupling constraints.

### A3 — Redesign the foreground-mask derivation

The terrestrial `foreground` still uses a rect or a `suggest_foreground.py`
-derived pixel mask, and the DERIVATION is weak: the treeline mask was never
good (its own config note admits the smear tips are only partially covered)
and a rect cannot model a real treeline arc. (The old structural complaint —
foreground excluded from the gate's blocks but not its rings — is FIXED: the
composition-agnostic gate now excludes the foreground from BOTH scopes.)
Redesign the derivation to robustly capture a real treeline silhouette + its
drift-smear halo, validated with numbers on the `lights` set. Keep terrestrial
masking distinct from the statistical sky selection that already handles bright
celestial signal (a galaxy / the MW / a nebula) with no mask at all.

---

## B. Parallel batch (renderer pass)

Renderer-touching items that batch into a single polish pass. None currently
open.

---

## C. Anytime (no dependencies)

No upstream blockers; safe to pick up in any session. Default-focus tier.

### C2 — Give SPCC the real OSC sensor + filter profile

`spcc_run.py` runs bare `spcc -catalog=localgaia`; siril logs `mono sensor
"(null)"` with `filters "(null)"` and derives the K factors by fitting Gaia
star colours against a default response — for every set (set-03's Z6III and
the D810A alike). That is a relative channel balance (it does neutralise the
sky: LMC corner G/R 1.44 -> 0.98, B/R 0.71 -> 0.99) but not the
sensor-grounded spectrophotometric calibration the `SPCC`/`_spcc` naming
implies. Siril's `spcc` accepts `-oscsensor=` (+ optional filter / white
reference); passing the camera's actual OSC response grounds the per-channel
scaling in real QE curves instead of a generic default.

Do it as a measured, per-set choice: add an optional sensor spec to
`spcc_run.py` (sourced from `datasets/<session>/<set>/recipe.json`), run the
null-vs-OSC K-factor ladder, and get the colour result judged. The spec must
DEFAULT to the current null behaviour so set-03's existing calibration
(K R1.000/G0.656/B0.837) and reproduce are untouched — only sets that opt in
get the sensor-grounded calibration.

Verified against the SPCC database (July 2026): sensors are filed by CHIP —
`Sony_IMX571.json` covers the siril-m8m20 ASI2600MC set (the ready test case),
but no Z6III or D810A curve exists; those need a digitized response curve
contributed by GitLab MR to siril-spcc-database before this can ground them.
`spcc_list oscsensor` enumerates the exact names.

### C3 — Per-stage cleanup for the self-flat sequence chain

The self-flat branch accumulates four full frame sequences in `work/`
(converted `light_*` → calibrated `pp_light_*` → glow-subtracted
`bkg_pp_light_*` → divided `pp_bkg_pp_light_*`) and never removes a consumed
one, so peak disk is ~4× a single sequence. On this rig's ~417 MB D810A
frames that is ~22 GB for a 28-frame set — over the free disk, so a large set
cannot process without babysitting `work/` by hand. Each stage needs only the
current + previous sequence: `light_*` is dead after calibrate, `pp_light_*`
after subsky, `bkg_pp_light_*` after divide. Delete each consumed sequence at
its stage boundary (after its inspection stage has read it), which drops the
peak to ~2 sequences (~14 GB for 28 frames). This is the "per-stage cleanup"
CLAUDE.md already names as the design intent; it is simply missing for the
self-flat chain (the matched-flat path is smaller and less affected). Verify a
self-flat set still stacks by the gate + inspection bounds (a stack is not
byte-reproducible), and that each removed sequence is genuinely unreferenced
downstream before deleting it.

### C4 — Optional deconvolution stage for well-sampled data

The pipeline has NO deconvolution and the standard-workflow row marks step 4
COMPLIANT-SKIP — correct on set-03 (in-exposure star trailing is not a static
PSF; the fitted PSF is symmetric and unstable on ≈0 background, measured). But
that is a per-data measurement, not a pipeline capability: linear deconvolution
is a routine standard step for well-sampled data (a TOA-130 galaxy field at
long integration is the textbook case), and the rig has exactly two free
aarch64-capable options (verified July 2026):

- **Siril 1.4.4 `makepsf` + `rl`** — the classical route; official guidance:
  `makepsf stars` on LINEAR data, RL with the gradient-descent formulation to
  prevent ringing, `-alpha` regularization, few iterations first. Placement:
  after colour calibration, before stretch. Note the vendor disagreement on
  noise-reduction order: siril docs say denoise BEFORE its RL (classical decon
  amplifies noise); RC-Astro says never denoise before ITS deconvolution —
  the rule is per-tool, and for siril rl the denoise-first order applies.
- **GraXpert `deconv-obj` / `deconv-stellar`** — AI (ONNX models 1.0.x,
  Jan 2025), CPU-capable, but ALPHA: no stable GraXpert release ships it
  (3.2.0a2 is the newest of the 3.2 alphas; last stable is 3.0.2). Low-SNR
  hallucination risk: learned priors can synthesize unmeasured detail —
  conservative settings, and judge against the classical result.

Add the stage optional and off by default, driven by the dataset recipe; keep
the measured set-03 SKIP as its removal condition. m74_toa130 (0.72"/px,
94 min) is the test case, and its `imx585c/reference/` master is the honest
comparison target. Still no third option: BlurXTerminator is paid + x86-64 +
AVX; Cosmic Clarity ships no aarch64 binary (its MIT source + ONNX models
could be wrapped like StarNet2 if ever needed).

### C5 — Add ASTAP as a fast offline solver complement

`solve_field.py` (blind astrometry.net from peak centroids) is the RIGHT and
necessary solver for this rig's ultra-wide trailed fields — ASTAP's own docs
disqualify it there (verified July 2026, hnsky.org "Conditions required for
solving": "Stars streaks due to tracking errors or severe optical distortion
will be ignored and solving could fail"; its wide-field W08 database is
mag-8-limited). But ASTAP v2026.06.29 (free) ships a **native aarch64
headless CLI** (`astap_cli`, 298 kB zip) with the D50/D05 databases, and for
NARROWER, round-star fields (a TOA-130 galaxy at ~0.7″/px) it is faster,
simpler, fully offline, and needs no astrometry.net index download. Add ASTAP
as an optional solver backend chosen per field (or auto by field width from
the header), with `solve_field.py` retained as the fallback for wide/trailed
frames. Its Johnson/Bessel photometry is also an SPCC-adjacent color check
worth capturing.

For the OTHER end — the 41° wide_50mm class where even blind astrometry.net
needed a position hint against wide-lens distortion — the candidate worth a
trial is **tetra3/cedar-solve** (ESA lost-in-space solver, default database
10–30° FOV, solves from centroids in milliseconds on Pi-class ARM).

### C6 — Combine multi-filter channels (LRGB, narrowband palettes, dual-band OSC)

The FITS ingest reads and normalizes the `FILTER` header and matches flats to
lights by filter, so a single-filter mono set (luminance) processes end to end.
What is missing is the CONVERGENCE step: a target shot through several filters
is N independent per-filter stacks that must be combined.

- **Register every filter's stack to ONE common reference** (siril global
  registration takes `-extref=<file>`), so channels overlay pixel-for-pixel and
  composition needs no second interpolation pass.
- **Broadband LRGB:** combine R/G/B, run SPCC on the RGB **only**, stretch
  LINKED, then apply L AFTER both are stretched (`rgbcomp -lum=`) — LRGB
  combination is a nonlinear-space operation (CIE L*a*b*), the
  linear-combine shortcut is wrong per PixInsight doctrine and the Siril book.
- **Narrowband palettes:** assign channels with `pm`: SHO = SII→R, Ha→G,
  OIII→B; HOO = Ha→R, OIII→G+B; `rmgreen` after Ha→G mappings. CORRECTED
  against Siril 1.4.4 docs (July 2026): "SPCC never on narrowband" is
  outdated — SPCC has a dedicated **narrowband mode** (`-narrowband
  -rwl/-gwl/-bwl + bandwidths`, filters synthesized in siril; for HOO set the
  two OIII channels to the same wavelength). Palette AESTHETICS still go to
  the user's eyes; the narrowband-mode calibration itself is objective.
- **Dual-band OSC (the siril-m8m20 case):** extraction happens in
  PREPROCESSING, per frame, from the CFA data (`seqextract_HaOIII`; Ha from
  the R photosites at half size — the docs' quality path stacks Ha with 2×
  drizzle rather than interpolating), then the per-line stacks combine as
  above. This is an ingest-path fork, not a render-side one.

Test data: `siril-m8m20/` (ASI2600MC OSC HOO+L-Pro, author's finished
masters as the answer key) is on disk; the mono corpus (`colonnello-m20/`
RGB wheel, `mlnoga-ngc7635/` SHO) is off-disk — re-stage with
`~/.cache/astro_recovery/fetch_corpus.sh`. Sources + license terms are
recorded in `.gitignore`, layout caveats in SESSIONS.md. **Relates to:** C2
(the m8m20 chip has a real SPCC profile: Sony IMX571), C7 (its L-Pro set
exercises the OSC-CFA branch).

### C8 — Evaluate newer star-separation models (declared-delta ladders)

The engine abstraction is in place (net/inpaint per recipe); the MODEL behind
`net` is the StarNet2 weights snapshot this repo bootstrapped. Verified July
2026, three candidates worth a measured ladder each, all CPU/aarch64-plausible:

- **StarNet2 2.5.3 weights** (released 2026-06-27; the Linux x64 CLI zip still
  ships a loose `StarNet2_weights.onnx`, now under a 2026 license text).
  2.5.2/2.5.3 added *highlight protection* around saturated regions — exactly
  the bright-star-shell class that keeps set-03 pinned to inpaint. Verify the
  graph I/O shape first (may differ from the current weights), then run the
  sep_engine ladder on set-03 (aura bound) + M74 (knot preservation).
- **SyQon Zenith** (free star-removal model, siril.org-announced 2026-01;
  PyTorch, runs near native resolution, CPU-capable via aarch64 torch wheels;
  ~2x slower, RAM-hungry — watch the 7.7 GB ceiling).
- **Cosmic Clarity Dark Star v2.1c** (MIT, ships a 14.5 MB ONNX — would slot
  into the existing onnxruntime wrapper directly).

Bars: aura_lum within bound on set-03, 100% field-star flux + knot
preservation on M74, byte-determinism, and like-encoding panels for anything
that changes an approved look.

### C9 — Measure the two canonical-order deviations

The linear chain deviates from the 2026 canonical order (crop → BGE → solve →
SPCC → …) in two measurable places; neither has been quantified here:

- **SPCC runs on the un-BGE'd stack** (solve+SPCC happen before starcomb's
  BGE). PixInsight's SPCC doc names strong gradients as a white-balance
  dispersion source; siril's book also orders BGE before colour calibration.
  Measure: SPCC K factors + kept-star count on the raw vs BGE'd stack (one
  dataset per class). If the K set moves materially, reorder (BGE becomes a
  pre-SPCC stack product, not a render-side step).
- **No crop stage.** Registration edge bands are currently handled only by
  the statistical sky selection; the canonical chains crop first because edge
  artifacts skew global statistics (GraXpert BGE sees them too). Measure the
  edge influence on one stack (gate metrics with/without a trim) before
  adding any stage.

### C10 — Try a GHS finishing stretch (aesthetic ladder)

Siril's docs now position GHS as the most capable stretch ("rarely advisable"
to use plain autostretch as-is) and provide the scriptable `autoghs` (+
`-clipmode=rgbblend` unclipped highlights). The current chain uses linked MTF
`autostretch` + significance corings. Run a like-encoding ladder (autostretch
control vs `autoghs` variants) on one approved + one provisional dataset —
pure aesthetics, user's eyes decide; no bake without approval.

### C11 — Gate sky scope on emission-flooded frames (scope change; needs ratification)

On a frame whose every block carries real emission (siril-m8m20 `lpro_180s`:
M8/M20 with the Sagittarius MW core filling the 2.5° field), the gate's
block-luminance sky selector has no true dark sky to find — the faintest 85%
of blocks still hold diffuse Hα, and its real chroma reads as a colour
defect: the render fails ONLY colour (22.0 vs limit 7; gradient 2.0, blotch
2.2, rings 3.2 all pass, shells +2.2). The author's own finished RGB of the
same data reads colour 65.4 / gradient 27.7 through the same gate — the
field is coloured at every luminance level; a ≤7 sky-colour bar is
structurally unreachable there without destroying real signal.

The gate stays as-is until a SCOPE decision is ratified (thresholds never
loosen; this is not a threshold question). Candidate scope refinement:
exclude `extended_object_mask` regions from the COLOUR grading blocks (the
corings' `sky_pixel_mask` already excludes them), so colour grades true sky
where any exists and reports INFO where none does — grading gradient/blotch/
rings unchanged. Prerequisite measurements: the mask's coverage on this
frame, and the colour number it then yields on all six datasets (must not
move any existing PASS).

Independent of scope: SPCC ran sensor-null here (K R0.370/G0.912/B1.000 on
1862 stars); the C2 `-oscsensor "Sony IMX571"` ladder is the designed test
of whether a real chip profile moves the sky balance materially on this
class.
