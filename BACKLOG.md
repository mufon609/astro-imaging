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

**Pick-up order** (user-ratified; re-rank when items close). When a session
asks "what next", take: **C6 → B1 → C9 → C1+C2 → C4 → C11 →
C12/C7/C3**. C8 and C10 run when their external/user inputs arrive; C5
only on a measured solve failure; A3 in a session scoped to it. The order
optimizes for the north star: capability breadth first (any data class),
then trustworthy cross-class measurement, then stage-check completeness.

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

Renderer-touching items that batch into a single polish pass.

### B1 — Scale-aware pixel constants in the metrics and render operators

The measurement/operator stack hardcodes absolute-pixel scales that encode
one PSF/resolution class and are not comparable across rigs:

- `star_shell_report` samples the aura at fixed annuli (peak 8-16 px minus
  baseline 32-40 px, ranks 10..80) with no per-set override. On a tight
  2-3 px PSF (m74) those annuli measure sky, not shell; on a big trailed
  one (set-03, ~8 px) they sit near the core — the same number means
  different things per class. (The sweep no longer hard-fails on the
  absolute WARN bound — aura regression is graded against each dataset's
  own baseline — so the brittleness is gone, but the METRIC still is not
  a cross-class physical quantity.)
- `chroma_core`/`lum_core` pyramid sigmas (2/8/32/128 px) + 4 px energy
  window; `extended_object_mask` smoothing scale (48 px); `starsep` skirt
  dilations (3/+5 px) and local-background footprint (33 px, stride 4) —
  the area caps are geometry-overridable, these are not; `star_metrics`
  windows (9 px dedup, core <=3 px, halo 3-8 px).

Design commitment: **derive, don't configure.** The pipeline already
measures FWHM, pixel scale and frame geometry — each scale above must be
derived from those measured data properties (per-set override remaining
as a measured exception only), and the EFFECTIVE values must print in the
metric line so a recorded number is interpretable. Gate thresholds never
loosen; every change lands as a declared delta re-derived per dataset
(one knob at a time). Until then the recorded aura/coring numbers are
only comparable within one dataset AT ONE FRAME EXTENT — measured: a
128 px border trim alone moved set-03's aura +4.0→+4.5 purely through
the top-500 anchor population, with no change to any star's rendering
context.

---

## C. Anytime (no dependencies)

No upstream blockers; safe to pick up in any session. Default-focus tier.

### C1 — Master calibration frames get an inspection stage

The masters (bias/dark/flat) most directly cause background gradients and
dust rings, yet they are the only pipeline products with no inspection
metric — a bad flat surfaces only downstream as a stack gradient.
`diag_flat.ssf` exists but is manual. Add an INS stage after each master
build reporting the numbers that matter per master: flat corner falloff %
and dust-shadow depth, dark/bias median + clipped-pixel fraction, into the
same run report (WARN-only, per the inspection contract). Calibrate bounds
on the masters already measured (the m74 flat falls 1.3% to the corner).

### C2 — Registration floor: abort a near-empty stack

All three stack paths now report registered/total (INS reg), but a run
that registers a fraction of its frames still proceeds to stack and
render. The self-flat path aborts only at zero. Implement a hard floor in
the runner at CATASTROPHE level — reg_fraction < 0.5 (less than half the
set is not the set; the abort message must name the reg log and the
reference-sweep option) — while 0.9 stays the advisory WARN: a 60-90%
set is degraded-but-honest data that should stack LOUDLY, not an error.
The 0.5 value is a design pick (half the set); revisit it with the first
real failure case. Keep INS WARN-only; the floor belongs to the runner.

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

Add the stage optional and off by default — but ELIGIBILITY IS MEASURED,
not assumed: the per-frame assessment (C9) supplies the sampling ratio
(measured FWHM vs pixel scale) and PSF stability, and the stage runs only
when the data supports it, with the dataset recipe as the explicit
override in both directions. Keep the measured set-03 SKIP as its removal
condition. m74_toa130 (0.72"/px, 94 min) is the test case, and its
`imx585c/reference/` master is the honest comparison target. Still no
third option: BlurXTerminator is paid + x86-64 + AVX; Cosmic Clarity
ships no aarch64 binary (its MIT source + ONNX models could be wrapped
like StarNet2 if ever needed).

### C5 — Add ASTAP as a fast offline solver complement

**CONDITIONAL — do not implement on convenience.** The solve stage runs
once per dataset and caches its WCS; a second solver backend adds
divergence surface (two code paths, two failure modes) for no capability
gain while `solve_field.py` keeps solving every class on disk (wide
trailed blind; narrow fields with a position hint). The trigger that
makes this real is a MEASURED solve failure — a dataset class the
current path cannot solve at all (not "grinds without a hint") — and the
entry then earns implementation with that dataset as its test case.

Research retained for that day: ASTAP is disqualified for this rig's
wide trailed fields by its own docs (verified July 2026, hnsky.org:
"Stars streaks due to tracking errors or severe optical distortion will
be ignored and solving could fail"; the W08 wide database is
mag-8-limited), but ASTAP v2026.06.29 ships a native aarch64 headless
CLI (`astap_cli`, 298 kB) with D50/D05 databases — faster, simpler, and
fully offline for narrow round-star fields; its Johnson/Bessel
photometry is an SPCC-adjacent colour check worth capturing. For the
opposite end (the 41° class where blind solving needed a position hint
against wide-lens distortion), the trial candidate is tetra3/cedar-solve
(ESA lost-in-space solver, 10–30° FOV database, centroid-based,
milliseconds on Pi-class ARM).

### C6 — Multi-filter combine: the remaining kinds

The composition machinery is LIVE for both shipped kinds (NOTES design
section carries the measured numbers): `dualband-osc` (per-line stacks
from one set's CFA frames) and `mono-filters` (sibling per-filter sets
aligned to a reference member — the M20 wheel target measured 0.077 px
median channel alignment). What remains:

- **SHO palettes** (the mlnoga NGC7635 corpus): a `mono-filters`
  composition with narrowband members — channel assignment objective,
  SPCC narrowband wavelengths already plumbed through the recipe
  (SII→R 671.6 nm / Ha→G 656.28 / OIII→B 500.7); `rmgreen` after the
  Ha→G mapping is a render-side aesthetic the user judges (the dead-end
  registry's magenta warning applies only to non-green-dominant skies —
  SHO is green-dominant by construction). NOTE: this corpus ships MASTER
  calibration files, which the pipeline cannot ingest (it builds masters
  from raw dirs) — assess master-calib ingest when staging it.
- **Broadband LRGB** (the app-ngc292 corpus): compose R/G/B, SPCC the
  RGB only, stretch LINKED, apply L AFTER both are stretched
  (`rgbcomp -lum=`) — LRGB combination is a nonlinear-space operation
  (CIE L*a*b*); the linear-combine shortcut is wrong per PixInsight
  doctrine and the Siril book. This is the one piece compose-then-render
  cannot express (L joins post-stretch, inside the render) — design it
  against the render chain, not around it. compose.py REFUSES a
  `luminance` member until then.
- **Dual-band FULL-SIZE upgrade:** native half-size Ha stacked with 2×
  drizzle instead of downsampling OIII (the docs' quality path) — gated
  on MEASURED dither coverage of the set.
- **Cross-geometry judgment packaging** (pipeline render vs an answer
  key at a different scale) recurs with every author-master corpus —
  promote the session scratch script into `judgment_crops.py`.

Test data: both remaining corpora are off-disk (the fetch stopped at its
disk floor after M20) — free disk, re-run
`~/.cache/astro_recovery/fetch_corpus.sh` (idempotent). Sources +
license terms in `.gitignore`, layout caveats in SESSIONS.md.

### C7 — Deduplicate the FITS I/O and MTF-solve helpers

Four minimal FITS header parsers (astrometrics/selfflat/rechroma/fitsmeta)
and two writers (selfflat 3-D, starsep mono NAXIS=2) copy the same
BITPIX/BZERO/END-card logic with divergent orientation/normalization
conventions; `solve_mtf_m` exists three times and only starcomb's copy
clamps degenerate inputs. Hoist into `astrometrics` with explicit
orientation/normalization flags, preserving each caller's EXACT current
behaviour. Acceptance: the sweep byte-reproduces every baseline and
`--determinism` passes — this refactor must be invisible in the artifacts.

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

### C9 — Per-frame quality assessment stage (measure what the data is)

The pipeline reads acquisition METADATA at preflight but never measures
the per-frame QUALITY distribution — the SubframeSelector/weighting step
of the standard workflow, and the literal "assess the data before
processing it" stage. Siril already writes per-frame FWHM/roundness into
the registration `.seq` (inspect_stage parses that file for shifts);
extend the parse and add an INS stage after registration reporting the
distribution — FWHM median + spread, roundness, background level drift
across the sequence — with per-frame outliers flagged. Policy stays
measured: culling/weighting remain OFF by default (the wFWHM no-op is a
set-03 fact at 6% spread, not a law); a dataset whose measured spread
justifies it gets a one-knob ladder via its recipe. Feeds: deconvolution
eligibility (C4: sampling ratio + PSF stability), the acquisition
checklist feedback loop (drift and passing clouds become visible per
frame), and honest per-class decisions everywhere a "the data supports
X" question arises. **Blocks:** C4 (eligibility inputs).

### C10 — Try a GHS finishing stretch (aesthetic ladder)

Siril's docs now position GHS as the most capable stretch ("rarely advisable"
to use plain autostretch as-is) and provide the scriptable `autoghs` (+
`-clipmode=rgbblend` unclipped highlights). The current chain uses linked MTF
`autostretch` + significance corings. Run a like-encoding ladder (autostretch
control vs `autoghs` variants) on two datasets of different classes —
pure aesthetics, user's eyes decide; no bake without approval.

### C11 — Redesign the colour gate as chain-added colour (ratified direction)

On a frame whose every block carries real emission (siril-m8m20 `lpro_180s`:
M8/M20 with the Sagittarius MW core filling the 2.5° field), the gate's
block-luminance sky selector has no true dark sky to find — the faintest 85%
of blocks still hold diffuse Hα, and its real chroma reads as a colour
defect: the render fails ONLY colour (22.0 vs limit 7; gradient 2.0, blotch
2.2, rings 3.2 all pass, shells +2.2). The author's own finished RGB of the
same data reads colour 65.4 / gradient 27.7 through the same gate — the
field is coloured at every luminance level; a ≤7 sky-colour bar is
structurally unreachable there without destroying real signal. Leaving the
class permanently un-baselineable is also unacceptable: the no-regression
suite would be blind to an entire data class.

**Ratified direction:** the colour gate's question becomes "did the CHAIN
ADD colour the calibrated data does not have?" — a process gate, not a
neutrality demand. SPCC provides a star-grounded colour reference in the
linear stack; grade the render's sky colour as DIVERGENCE from the
calibrated stack's own colour at matched locations, one-sided (added
chroma fails; noise-chroma the corings removed toward neutral does not).
Honest Hα then passes on any field while a chain-introduced cast fails
everywhere. Implementation care: the stretch is nonlinear, so compare
chroma at matched luminance levels (or push the reference through the
same stretch) — design the comparison so it cannot be gamed by the
stretch itself.

Two dead candidates, measured — do not re-propose: excluding
`extended_object_mask` regions from the colour blocks (mask covers 14% of
the motivating frame, drops 3/529 sky blocks, colour 22.0 unchanged;
references move ≤1.0), and accepting permanent colour-FAIL for the class
(blinds the regression suite).

The switch LANDS only with calibration evidence presented to the user:
the injected 8-count cast still FAILS, all currently-passing datasets
still PASS, lpro_180s's honest colour passes — then lpro is baselined.
Thresholds never loosen; this changes what colour MEASURES, with proof it
still catches every defect it caught before.

Context (measured): the 22.0 colour excess is REAL SKY, not a calibration
artifact — grounding SPCC in the true train response moves K ≤1.5% and
the output ≤2.6e-4 p99, and SPCC on the BGE'd stack moves K_R +0.3% —
neither the calibration nor the chain order explains it.

### C12 — Measure the OSC calibration divergence between the raw and FITS paths

The camera-raw path calibrates OSC lights with `-flat=... -equalize_cfa`;
the FITS OSC path applies the flat WITHOUT `-equalize_cfa` (only mono FITS
and one OSC set have run through it). The flag normalizes the FLAT's CFA
channel means so division does not re-tint the light — a flat-artifact
correction, distinct from the sky balance SPCC measures downstream. Run the
one-knob stack experiment on the OSC-CFA set (with/without, compare SPCC K
factors + gate metrics + rim chroma), then either align the two paths or
document the measured reason they differ.
