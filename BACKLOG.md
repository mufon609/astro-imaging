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

### A1 — Retire mask+inpaint as the default star separator

mask+inpaint is the aarch64 bandaid (written when no StarNet build existed) and
it is now measured to be WRONG on resolved objects: on M74 it classifies 229 of
852 detections (26.9%) — the galaxy's HII knots — as stars, inpaints them out
of the starless, and screens them back through the stars MTF as hard white
blobs; the 6212 px² galaxy core is admitted by `AREA_MAX_BRIGHT`. StarNet2
(`--sep-engine net`) renders the same field correctly. Star separation on any
resolved target must not use it.

This INVALIDATES the previously-planned `hybrid` adoption for such fields:
hybrid runs the net ON the inpaint starless, so it inherits a base whose knots
are already destroyed. Hybrid remains interesting only where the frame holds no
resolved extended object.

Measured on both classes (single-knob `sep_engine` ladders, gate + star shells):

| engine  | set-03 gate | set-03 aura | M74 gate | M74 aura | M74 galaxy |
|---|---|---|---|---|---|
| inpaint | PASS | +0.0 | PASS | +4.9 WARN | steals 32% more structure |
| net     | PASS | +4.0 | PASS | +4.0 | preserves |
| hybrid  | PASS | +0.0 | — | — | invalid (inpaint base) |

net keeps 100.0% of genuine field-star flux while pulling 32% less galaxy
structure into the stars layer. Its cost is a visible striped residual around
BRIGHT stars on set-03 (aura +0.0 → +4.0, still inside the bound). hybrid is
clean there but cannot be used where a resolved object exists.

The choice is therefore data-class dependent, and the failure modes are not
symmetric: net's worst case is cosmetic (a bright-star shell), inpaint's worst
case DESTROYS real signal. Prefer the fail-safe engine as the default.

Best candidate to measure next: exclude extended objects from the inpaint star
mask (`build_star_mask` already has `extended_object_mask` available). Then the
inpaint base flattens bright FIELD stars only — never galaxy knots — and the net
run over it removes the stars inside the object. That would make one engine
correct on both classes: clean bright stars (hybrid's win) AND preserved galaxy
structure (net's win).

Then: demote mask+inpaint to the fallback used when the StarNet2 weights are
absent, update the README step-6 row, declare the delta and bring the
like-encoding panels. The set-03 bright-star change is aesthetic → user's eyes.

**Relates to:** A2 (the anchor is a per-dataset knob, not the cause here).

### A2 — Make the stars anchor stable within a dataset (do NOT globalize it)

Do not flip the default to `noise`. Measured: `k = 490.9663661574939` is DEFINED
as set-03's catalog anchor divided by set-03's sigma_G, so the noise anchor
simply re-states set-03's star statistics as if they were universal. On M74 the
catalog anchor sits at 44 sigma; the noise anchor asserts 491 sigma — an 11x
mismatch that would render that field's stars far too dim (m 0.000100 ->
0.001155).

The real defect is that the anchor samples a different depth of each field's
luminosity function. "median of the top 500" is the brightest 2% of set-03's
22916 catalog stars but the brightest 59% of M74's 852. A fixed FRACTION is no
better and swings the other way (top-10%: 143 sigma on set-03, 1824 sigma on
M74). No single rule sets a star brightness across fields — the anchor's
absolute level is a per-dataset recipe knob (C1).

What IS worth fixing narrowly, and is objective: `cat["peak"]` is the component
peak of the MAX-OVER-CHANNELS residual, so SPCC's per-channel gains move which
channel wins and the anchor drifts (measured: G-channel star rendering -8.5/-20
counts at mid/faint tiers between builds of the same sky). Compute the anchor on
a FIXED basis (the luminance / G channel) so a per-channel rescale cannot move
it, and declare the delta. Keep `noise` as a flag, documented as a same-dataset
stability tool, never a cross-dataset default.

**Blocked by:** user's go-ahead (a render no-op on the current stack, but a
default change).

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

### C1 — Multi-dataset architecture (per-dataset state as first-class)

The scripts are dataset-generic (`run_pipeline.sh <session> <set>`; `raw_find`
ingests any camera raw), but the repo's per-dataset STATE is still
single-session: NOTES STATUS, the approved recipe, and the recorded baseline
metrics are all set-03-specific, and a `config_<set>.json` must live inside the
gitignored session dir — so a copyright-ignored dataset (e.g. Wang's raws) can
hold NO tracked config or record at all. To manage many stacking workflows the
repo needs, roughly:

- **Split NOTES** into dataset-independent design + dead-ends (stays) vs a
  per-dataset record (approved recipe, reproduce target, pending items, config
  rationale). `SESSIONS.md` is the index; each dataset gets its own record.
- **A tracked home for per-dataset config/recipe outside the gitignored data
  dir** (e.g. `configs/<dataset>/`), so a copyright-ignored dataset is
  version-controlled without committing its raws.
- **Generalize the approved recipe from one global default to per-dataset**:
  starcomb's defaults are set-03-tuned (its SNR/target); a different camera/
  target/integration needs its own tuned recipe (the LMC's `chroma_core`
  desaturation and M74's blown core are the live examples).
- **Per-dataset recorded baseline** — each approved render carries its own
  rebuild command + baseline metrics, which the no-regression sweep reads.

Non-blocking: configless datasets already degrade loudly and process to an
honest (if generic) result. This is the structural work that stops set-03 from
being the unicorn.

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
`spcc_run.py` (sourced from `config_<set>.json` so it rides the per-dataset
config work), run the null-vs-OSC K-factor ladder, and get the colour result
judged. The spec must DEFAULT to the current null behaviour so set-03's
existing calibration (K R1.000/G0.656/B0.837) and reproduce are untouched —
only sets that opt in get the sensor-grounded calibration.

**Relates to:** C1 (the sensor spec is a per-dataset config field).

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
is now a routine standard step for well-sampled data (a TOA-130 galaxy field at
long integration is the textbook case), and the rig already has two free
aarch64-capable options — GraXpert 3.2.0a2 exposes `deconv-obj`/`deconv-stellar`
(AI, CPU), and Siril 1.4.4 ships classical `makepsf` + `rl`/`sb`/`wiener`. Add
an optional, off-by-default deconvolution stage (linear, after gradient removal
+ color calibration, BEFORE noise reduction — the firm ordering rule). Keep the
measured set-03 SKIP as its removal/skip condition, and note the low-SNR
hallucination risk of AI deconvolution (learned priors can synthesize
unmeasured detail on faint signal — conservative/PSF-correct-only defaults).
No free deconvolution runs natively on this rig beyond these two: BlurXTerminator
is paid + x86-64, Cosmic Clarity has no aarch64 binary.

### C5 — Add ASTAP as a fast offline solver complement

`solve_field.py` (blind astrometry.net from peak centroids) is the RIGHT and
necessary solver for this rig's ultra-wide trailed fields — ASTAP is documented
to fail where astrometry.net solves them (33°+ distorted frames), and it builds
quads from centroids that trailing degrades. But ASTAP 2026.06.29 (free,
MPL-2.0) ships a **native aarch64 headless CLI** (`astap_cli`) with built-in
Gaia photometric calibration, and for NARROWER, round-star fields (a TOA-130
galaxy at ~0.6″/px) it is faster, simpler, fully offline, and needs no
astrometry.net index download. Add ASTAP as an optional solver backend chosen
per field (or auto by field width from the header), with `solve_field.py`
retained as the fallback for wide/trailed frames. Its Johnson/Bessel photometry
is also an SPCC-adjacent color check worth capturing. The dedicated-astrocam
sets (TOA-130 at ~0.6″/px) are exactly the narrow, round-star case ASTAP suits.

### C6 — Combine multi-filter mono channels (LRGB + narrowband palettes)

The FITS ingest reads and normalizes the `FILTER` header and matches flats to
lights by filter, so a single-filter mono set (luminance) processes end to end.
What is missing is the CONVERGENCE step: a target shot through several filters
is N independent per-filter stacks that must be combined.

- **Register every filter's stack to ONE common reference** (siril global
  registration takes `-extref=<file>`), so channels overlay pixel-for-pixel and
  composition needs no second interpolation pass.
- **Broadband LRGB:** combine R/G/B, run SPCC on the RGB **only**, stretch
  LINKED (an unlinked stretch alters the calibrated white balance), then apply
  L as luminance (`rgbcomp -lum=`). L is added after the histograms are
  stretched, not before.
- **Narrowband:** SPCC must be **gated OFF** — a palette is a false-colour
  mapping of emission-line intensity, not a photometric calibration. Assign
  channels by palette with `pm` (PixelMath): SHO = SII→R, Ha→G, OIII→B; HOO =
  Ha→R, OIII→G+B. Normalize/stretch each channel independently (there is no
  true white to protect), then `rmgreen` (SCNR) — Ha→G makes green dominate.
- Narrowband palette colour is aesthetic and therefore goes through the user's
  eyes, never an objective colour gate.

Needs a multi-filter dataset to verify: `imx585c` is single-filter (L), so an
LRGB/SHO combiner built against it would be unverifiable. Acquire or download a
mono LRGB or SHO set first. **Relates to:** C1 (each palette/target is its own
per-dataset recipe), C2 (SPCC sensor profile is a broadband-only concern).

### C7 — Verify the OSC-CFA FITS branch

The FITS ingest routes debayer on the header — a mono frame (no `BAYERPAT`,
`NAXIS=2`) is never debayered, an OSC CFA FITS (`BAYERPAT` present) gets
`-cfa -debayer`. Only the MONO branch is verified (imx585c). The CFA branch is
written but has never seen data: a dedicated OSC camera (e.g. the IMX585**C**
the practice set was meant to be) writes a single-channel CFA FITS that siril
must debayer, and the render then takes the normal colour chain (SPCC, chroma
coring, satu). Verify on a real OSC-FITS set: confirm the Bayer pattern is read
from the header, the debayered stack is 3-channel, SPCC runs, and the colour
render passes the gate. Until then, treat the CFA branch as untested code.

### C8 — Re-baseline the reference renders under the new acceptance contract

The acceptance contract is now determinism + no-regression across data classes
+ declared delta (README "How a change is accepted"), not byte-identity with
set-03. Two follow-ups:

- The recorded set-03 baseline artifacts (`starcomb_set-03_APPROVED_20260708_*`)
  now differ from a fresh render by ±1 count on ~1% of pixels (all gate and
  star-shell metrics identical). Decide whether to re-baseline + tag them so the
  determinism check compares against current code, or keep them as the approved
  look and record the tolerance.
- The no-regression sweep needs to be runnable in one command over every
  registered dataset (currently it is a manual per-dataset render + gate read),
  and LMC/SMC need their render caches regenerated to be included.

