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

### A1 — Adopt the StarNet2 hybrid star-separation engine

The `hybrid` engine (StarNet2-ONNX run on the mask+inpaint starless) met
every objective bar when last measured: gate PASS (= the inpaint control),
star aura_lum +2.0, the bright-star pedestal equals the inpaint fill, the
faint-tail residual drops to 589 detections (vs ~5.1k), chroma rings improve.
It awaits the user's aesthetic sign-off on like-encoding panels. NOTE: those
bars were measured under the REMOVED corridor-gate — re-measure against the
composition-agnostic gate + corridor-free baseline before adopting.

Judge `07-02-26/results/exp_starsep_sep_engine_20260707_125122/judgment/`
(`judge_starless_stipple.jpg` is the headline; `judge_bright_shells.jpg`
shows the bright shells unchanged) plus the full renders `v0_hybrid.jpg` /
`v1_inpaint.jpg`. Do NOT revisit the stock-net A/B in
`exp_starsep_sep_engine_20260707_120825` (aura +12, killed).

On approval the change is coupled: flip the starcomb default `--sep-engine`
to `hybrid`, re-render `--lossless`, verify the numbers, tag the render, and
bake the artifacts + NOTES STATUS. The starless jpg is the gate input, so
its identity changes — this establishes a NEW byte-reproduce contract that
supersedes the current one. Then demote mask+inpaint to the documented
fallback and update the README step-6 row. Needs the net cache trio
`work/starsep/*_neth.*` (regens in ~7 min if pruned).

**Blocked by:** user's visual judgment.

### A2 — Flip the stars anchor default to noise-relative

The catalog anchor (median top-500 max-over-channel amplitude) is
data-dependent: under the SPCC per-channel gains it drifts the G-channel
star rendering -8.5/-20 counts (mid/faint), while the noise-relative anchor
(k x sigma_G of the linear starless) holds to <=0.6 (k = 490.9663661574939).
On approval: flip the default, byte-verify the reproduce once more, keep
`catalog` as a flag. NOTE: the earlier byte-identity acceptance was against
the retired B7 artifacts — re-verify the noise-mode render is a byte no-op
against the new corridor-free set-03 baseline before flipping.

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
single-session: NOTES STATUS, the approved recipe, and the byte-reproduce
contract are all set-03-specific, and a `config_<set>.json` must live inside the
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
  target/integration needs its own tuned recipe + its own byte-reproduce (the
  LMC's `chroma_core` desaturation is the live example).
- **Re-cast the byte-reproduce gate as per-dataset** — each approved render
  carries its own reproduce command + numbers.

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

### C8 — Stack-inspection metrics for low-background / centered-object fields

`sky_flatness()` grades the stack on the statistical dark sky, which fixed the
off-centre object case (LMC/SMC). Two limits remain, both measured on the
imx585c M74 stack (mono, dark sky, 47×120 s):

- **A CENTERED object contaminates a RADIAL sky profile by construction.** M74
  sits at frame centre; its faint outer envelope lies between `bg` and `bg+3σ`,
  so the dark-sky selector keeps it (sky_frac 0.97) and the sky radial profile
  reads 50.7 counts at r≈0 falling to 37.7 at r≈0.5 — a `p2v_inner_rel` of
  0.35 that is the GALAXY, not a flat-field defect (the flat master measures
  only 1.3% radial falloff and 1.9% large-scale structure). A plane fit over
  sky blocks, or the detrended ring amplitude the gate already uses, is robust
  to a smooth centred envelope where a raw radial P2V is not.
- **`noise_over_median_pct` and `bg_median16` are ratios to an arbitrary
  pedestal.** The stack background is 38 counts here (dark sky, plus siril's
  `-output_norm` compressing by the saturated-star max) vs ~370–600 on the DSLR
  sets, so noise/median reads 11% and bg_median16 falls under its 150 floor —
  both WARN on a stack that is demonstrably good. Either measure noise against
  the signal scale rather than the pedestal, or make the level bound a
  data-class fact instead of one absolute range.

Do not simply widen the bounds: re-derive what each metric is meant to catch
(vignetting residual; grossly wrong exposure/SNR) and measure that directly.

