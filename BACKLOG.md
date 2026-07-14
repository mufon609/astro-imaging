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
asks "what next", take: **C18 → C6 → B1 → C4 → C11 →
C14 → C12/C7/C3/C15** (C18 leads: direct user directive; the former
lead closed — the ratified stack weighting/culling policy surface
shipped as per-dataset recipe state with its mechanism verification;
earlier closures: the class-triage checklist shipped into README, and
C17's report-card half shipped with its preset half moving to the
awaiting-inputs tier below, its redesigned scope needing user
ratification).
C8 and C10 run when their external/user inputs arrive, C17's preset
half on its ratification; C16 (new, user-specified) awaits its
ratified position; C13 after its
industry-norm research; C5 only on a measured solve failure; A3 in a
session scoped to it. The order
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
  2-3 px PSF those annuli measure sky, not shell; on a big trailed
  one (~8 px) they sit near the core — the same number means
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
128 px border trim alone shifts the aura reading purely through
the top-500 anchor population, with no change to any star's rendering
context.

---

## C. Anytime (no dependencies)

No upstream blockers; safe to pick up in any session. Default-focus tier.

### C1 — Flat USABILITY gate in the raw-path preflight (awaits pick-up ranking)

The preflight accepts any flats whose optics match the set, but a flat can
be present, matched, and WRONG: a flat shot against a non-uniform light
source can carry several times the lens's real corner falloff, and
dividing by it would over-brighten the corners badly. The `master_flat`
inspection already WARNs on exactly this (corner_over_center < 0.35) but
inspection never routes. Add a measured usability check to the raw-path
preflight: build the master flat, compare its corner/center against the
lights' own sky falloff (a dark-subtracted median probe of a few lights —
the sky IS a uniform source through the same optics), and route to
self-flat LOUDLY with both numbers when they disagree beyond a calibrated
bound. The flat stays on disk as evidence; the route decision prints its
numbers. Keep the check cheap (a few frames, coarse grid).

### C2 — Integrate the partitioned runner: auto-route + inspection stages (awaits pick-up ranking)

`partitioned_stack.py` (common-reference partitioned integration for
sets whose intermediates exceed free disk) runs standalone and proved
the mechanism set on a 240-frame 24.5 MP set with ~5 GB free. Two
integration steps remain: (1) run_pipeline.sh computes the projected
single-pass footprint (frames × per-frame stage cost vs `df`) and
routes to the partitioned runner loudly when the monolithic path cannot
fit — mirroring the self-flat auto-route pattern; (2) the runner emits
the standard per-stage inspection (INS master/calibrated/reg/stack) —
an unusable flat once sailed past the runner precisely because the
INS stages were skipped there (the standing audit caught it the moment
it was invoked); wire them in so the partitioned path carries the same
review contract as the monolithic one. Byte-inert for every set the
monolithic path still serves.

### C3 — Per-stage cleanup for the self-flat sequence chain

The self-flat branch accumulates four full frame sequences in `work/`
(converted `light_*` → calibrated `pp_light_*` → glow-subtracted
`bkg_pp_light_*` → divided `pp_bkg_pp_light_*`) and never removes a consumed
one, so peak disk is ~4× a single sequence. On large (~417 MB) raw
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
COMPLIANT-SKIP where star trailing is in-exposure (not a static PSF; the
fitted PSF is symmetric and unstable on ≈0 background). But
that is a per-data measurement, not a pipeline capability: linear deconvolution
is a routine standard step for well-sampled data (a well-sampled galaxy
field at long integration is the textbook case), and the rig has exactly two free
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
not assumed: the registration inspection records supply the sampling
ratio (fwhm_med_px vs the 2.0 px Nyquist floor, with its arcsec twin)
and PSF stability (fwhm_cv_pct + round_med) per sequence, and the stage
runs only when the data supports it, with the dataset recipe as the
explicit override in both directions. Keep the in-exposure-trailing SKIP
as its removal condition. A well-sampled long-integration mono galaxy set,
with a reference master to compare against, is the test case. Still no
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

The composition machinery is LIVE for both shipped kinds and both
mono-filters classes (NOTES design section carries the measured
numbers): `dualband-osc` (per-line stacks from one set's CFA frames)
and `mono-filters` broadband (an RGB filter-wheel target) + narrowband
SHO (a prebuilt-master SHO target, recipe-driven narrowband SPCC). The SHO PALETTE AESTHETICS (green
dominance vs the finished gold/teal looks; `rmgreen` is legal on this
green-dominant class) are render-side and sit with the user's judgment
package, not here. What remains:

- **Broadband LRGB**: compose R/G/B, SPCC the RGB only, stretch LINKED,
  apply L AFTER both are stretched (`rgbcomp -lum=`) — LRGB combination
  is a nonlinear-space operation (CIE L*a*b*); the linear-combine
  shortcut is wrong per PixInsight doctrine and the Siril book. This is
  the one piece compose-then-render cannot express (L joins
  post-stretch, inside the render) — design it against the render
  chain, not around it. compose.py REFUSES a `luminance` member until
  then. NO TEST CORPUS IS STAGED for this: the one LRGB candidate is excluded
  by user request (.gitignore note; the stager's `.done` marker enforces
  the skip) — pick an L-bearing corpus
  with the user before starting.
- **Dual-band FULL-SIZE upgrade:** native half-size Ha stacked with 2×
  drizzle instead of downsampling OIII (the docs' quality path) — gated
  on MEASURED dither coverage of the set, meaning sub-pixel PHASE
  diversity of the per-frame shifts. The registration inspection now
  records the full per-frame shift list + 4×4-bin phase coverage on
  every run, and it confirmed sub-pixel phase diversity on the dual-band
  set (dither coverage spread across the shift bins), so the upgrade is
  unblocked. The motivation is on record too: the extracted half-size
  lines measure under the 2 px Nyquist floor — they are undersampled,
  and drizzle is the recovery path.

Test data: the SHO corpus stages via
`~/.cache/astro_recovery/fetch_corpus.sh` (idempotent, disk-floor
guarded); the LRGB slot has no staged corpus (see the LRGB bullet).
Sources + license terms in `.gitignore`; per-corpus layout caveats in
each gitignored `<session>/README.md`.

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
  the bright-star-shell class that pins a wide trailed field to inpaint. Verify the
  graph I/O shape first (may differ from the current weights), then run the
  sep_engine ladder on a wide trailed field (aura bound) + a resolved galaxy (knot preservation).
- **SyQon Zenith** (free star-removal model, siril.org-announced 2026-01;
  PyTorch, runs near native resolution, CPU-capable via aarch64 torch wheels;
  ~2x slower, RAM-hungry — watch the 7.7 GB ceiling).
- **Cosmic Clarity Dark Star v2.1c** (MIT, ships a 14.5 MB ONNX — would slot
  into the existing onnxruntime wrapper directly).

Bars: aura_lum within bound on the wide trailed field, field-star flux +
knot preservation on the resolved galaxy, byte-determinism, and
like-encoding panels for anything
that changes an approved look.

### C9 — Survey-referenced background separation (the long-term professional direction)

From a single image alone, no estimator can distinguish frame-filling
faint nebulosity from sky gradient at similar spatial scales — every
failure in the retention ledger (a frame-filling nebula complex, a faint
galaxy envelope, dark-lane dust, all partly absorbed) is this one
information gap wearing different data. The industry's emerging answer is EXTERNAL knowledge:
PixInsight's MultiscaleGradientCorrection subtracts a calibrated
all-sky survey reference (the MARS database) so the background model
comes from survey truth instead of the image's own statistics; manual
DBE sample placement encodes the same knowledge by hand. This
pipeline already plate-solves every stack, so the same move is open
to us: fetch a low-resolution reference of the solved field (dust-map
/ survey class TBD — IRAS/Planck dust maps are the classic prior;
licensing, resolution and photometric-scale questions are the
research half) and use it to VETO background samples on known
nebulosity, so the model rests on survey truth, not the image's own
statistics. Research first (sources, licenses, resolution
limits at 35″/px wide fields vs 1″/px scopes), then design as an
OPTIONAL sample-veto layer over the background extractor — never a
hard dependency (offline operation must survive). This is the
principled fix for the information gap the retention ledger keeps
hitting: an image-only estimator cannot know which faint structure is
real, but a solved field plus a survey prior can.

### C10 — Try a GHS finishing stretch (aesthetic ladder)

Siril's docs now position GHS as the most capable stretch ("rarely advisable"
to use plain autostretch as-is) and provide the scriptable `autoghs` (+
`-clipmode=rgbblend` unclipped highlights). The current chain uses linked MTF
`autostretch` + significance corings. MOTIVATION (deep-data classes,
user-flagged across targets, user calls the fix foundational): the
single-midtone MTF mis-serves BOTH ends of high-DR data at once — the
faint shell renders far dimmer than a good allocation gives it, and the
bright-core structure/grain ratio collapses through the stretch (the
object's mid-tones land on the flattened shoulder), so the core sits
just above sky where a reference finish allocates a wide band to the
same structure. The floor/top
single-knob ladders were judged (generic wins — black_point cannot move
above-sky contrast, linear-shift invariance; stars_peak fixes tops only
at a faint-field cost). GHS's toe+shoulder is the structural answer to
all of it. Run a like-encoding ladder (autostretch control vs `autoghs`
variants) on two datasets of different classes — pure aesthetics,
user's eyes decide; no bake without approval. Narrowband-palette
interaction: the per-line stretch superseded the earlier narrowband ghs
case study, and a ghs finishing pass now composes ON TOP of the perline
base (linked, the
lines already equalized) — that combination is unprobed; ladder it on
the perline class only after the perline look itself is judged.

### C11 — Redesign the colour gate as chain-added colour (ratified direction)

On a frame whose every block carries real emission (a broadband field the
Milky Way core fills edge to edge), the gate's block-luminance sky selector
has no true dark sky to find — the faintest blocks still hold diffuse Hα,
and that real chroma reads as a colour defect: the render fails ONLY colour
while every achromatic metric passes. Even the data author's own finished
RGB of such a field fails the same colour bar — the field is coloured at
every luminance level, so a ≤7 sky-colour bar is structurally unreachable
there without destroying real signal. Leaving the
class permanently un-baselineable is also unacceptable: the no-regression
suite would be blind to an entire data class.

**Interim (landed):** the class is no longer regression-blind — a
scope-ACKED baseline (`sweep.py --rebaseline <ds> --ack-color-scope`,
refused unless colour is the SOLE failing gate metric) keeps an
emission-flooded dataset inside the byte/achromatic/shell regression net
with colour graded one-sided vs its record. That is drift TRACKING only;
this redesign remains the sole path to full colour admission (an acked
colour is never judged against the ≤7 bar).

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
`extended_object_mask` regions from the colour blocks (the mask covers only
a small fraction of an emission-flooded frame and leaves the colour metric
unchanged), and accepting permanent colour-FAIL for the class
(blinds the regression suite).

The switch LANDS only with calibration evidence presented to the user:
the injected 8-count cast still FAILS, all currently-passing datasets
still PASS, and the emission-flooded field's honest colour passes — then
it is baselined.
Thresholds never loosen; this changes what colour MEASURES, with proof it
still catches every defect it caught before.

Context: the colour excess is REAL SKY, not a calibration artifact —
grounding SPCC in the true sensor response, and running SPCC before vs
after background extraction, both move the fit negligibly, so neither the
calibration nor the chain order explains it.

Scope update: the per-line stretch (`stretch_linked perline`) re-pins
every channel's sky at the same target, so a narrowband-palette render
passes the CURRENT colour gate outright (linked scope-FAILs on colour,
perline PASSes with achromatics clean) — that class no longer motivates
this redesign and can baseline as-is. The broadband emission-flooded
fields — a broadband OSC set, and an approved dual-band look pinned to the
linked stretch (per-line for it would be a new declared delta through the
user's eyes, not a gate change) — are
scope-ACK tracked in the interim (see above); full colour admission
still needs this redesign. The redesigned comparison must
also stay honest under per-line stretching: each channel's transform
differs by design, so "chain-added colour" is divergence from the
calibrated stack pushed through THAT channel's own transform.

### C12 — Measure the OSC calibration divergence between the raw and FITS paths

The camera-raw path calibrates OSC lights with `-flat=... -equalize_cfa`;
the FITS OSC path applies the flat WITHOUT `-equalize_cfa` (only mono FITS
and one OSC set have run through it). The flag normalizes the FLAT's CFA
channel means so division does not re-tint the light — a flat-artifact
correction, distinct from the sky balance SPCC measures downstream. Run the
one-knob stack experiment on the OSC-CFA set (with/without, compare SPCC K
factors + gate metrics + rim chroma), then either align the two paths or
document the measured reason they differ.

### C13 — Decide the canonical final orientation (research the norm first)

The composed products are parity-MIRRORED against the solved sky
(det(CD) > 0; root cause: top-down camera FITS carrying no ROWORDER
keyword, ingested under siril's bottom-up default — self-consistent
everywhere downstream, so only the solve can see it), while every
data-author reference on hand publishes sky-true (verified numerically by
flip-correlation, not by eye — an eyeball same-orientation call was wrong
once, so parity is always checked numerically). `solve_field` now prints and
records parity on every solve, so the fact is never hidden. RESEARCH
FIRST: what the publication norm actually is (sky-true parity vs
camera-native; AAVSO/professional conventions vs amateur practice),
then decide the canonical export orientation. Implementing sky-true
means flipping finals at export when the solve knows parity — a
declared delta across every baselined dataset (full rebaseline) and a
visual change to any approved look, so the decision and the numbers go
to the user before any code moves.

### C14 — Audit and tighten the global-vs-local recipe layering

The layering is live (CLI > `recipe.json` > `datasets/GENERIC.json`,
schema in code, per-knob why notes in the file) but grew organically —
audit it as ONE design: naming and terminology consistency
("generic" vs "base" vs "foundational"), what belongs in the generic
file vs a recipe vs a composition record vs geometry (the four-file
contract should state a crisp decision rule), how the `spcc` and
`stack` blocks and future stage knobs (decon) slot into the same
resolution order, whether approved-recipe pinning should snapshot the generic
"why" notes it froze against, and whether the docs (README + both
dataset contracts + NOTES design section) tell one coherent story a new
contributor can follow. Edit and tighten — documentation and structure,
no behavior change without its own declared delta.

### C15 — Baselines record per-stage intermediate hashes (drift forensics)

A baseline pins the stack sha and the final artifact hashes — nothing in
between. When a render drifts against its baseline, the stage that moved
is unrecoverable if the per-stage caches are gone (a real drift once
could not be localized because the deterministic caches had been pruned;
the answer would have been one `cmp` against the cached bgelin/trio). Record the intermediate identities in `baseline.json` at
rebaseline time — bgelin sha256 + separation-trio sha256s (+ compose
inputs for composed targets) — so any future drift localizes to its
stage from the records alone, prune or no prune. Hashing ~0.5 GB per
dataset at rebaseline is seconds; do NOT hash on ordinary sweeps.

### C16 — Reference-finish reverse-engineering: report, then the user picks mirror / diverge / learn

User-specified. When a corpus ships a reference finish (the answer
key), its study becomes a standing PROCESS with a deliverable report —
never an ad-hoc investigation. The process:

1. ANALYZE the reference image, measured: structure/allocation map
   (percentile levels of object vs sky), palette/hue distribution,
   noise and texture character at native scale, star treatment,
   orientation/parity vs our chain (numerically, never by eye).
2. REVERSE-ENGINEER the toolchain: image metadata, the author's
   published tooling and recipes (repos, Makefiles, articles, forum
   threads), tool-signature heuristics; when the tool is open and
   runnable, REPRODUCE the reference on this rig and keep the
   intermediates as calibration targets. (This has been done once: a
   narrowband corpus's finish traced to the author's open-source tool and
   published recipe, reproduced locally, which yielded the noise-capped
   stretch, the LCh finishing set, and the background-retention fix.)
3. REPORT honestly, mechanism by mechanism: what our chain can mirror
   (and with which knobs), what used tools/steps we DO NOT have (with
   license and platform reality, per the separation-weights
   precedent), what is data vs processing, and what is manual
   finishing no tool encodes.
4. STOP and ASK the user, report in hand: (a) COPY the style —
   calibrate our chain toward the reference via ladders and their
   eyes; (b) DIVERGE deliberately — record the chosen difference and
   its reason; (c) LEARN — follow the reference process itself,
   integrate the key insights of the industry process actually used
   into our chain as measured mechanisms, and examine our outcome
   against the reproduced original.

Deliverable: the documented procedure + a report template, with a
`scripts/qa/` tool for the automatable measurements (parity, palette
distribution, allocation, texture — library pieces exist). README's
"Adding a dataset" step 0 already mandates the study; this entry
builds the skill so ANY reference-bearing corpus gets the same
treatment. Placement in the pick-up order needs user ratification
(natural fit: before the next reference-bearing corpus lands;
complements the object-integrity audit's retention traces).

### C17 — Palette-balance presets (REDESIGN against the per-line stretch)

User-specified; the capture REPORT CARD half is shipped
(`scripts/qa/capture_report.py`, wired into compose for mono-filters —
dualband raw rates await the extraction step; spec-sheet QE curves via
siril's SPCC response data remain an optional refinement; L slots in as
one more member row when the LRGB join lands). What remains is the
PRESET knob — and it needs a redesign decision before implementation:
the original spec (LINEAR pre-stretch channel weights: `natural` ∝
measured line flux, `per-source` SNR-capped, `custom`) predates the
per-line stretch architecture. Measured since: linear equalization is
destructive through the corings (a large linear channel weight collapses
the object; the user judged the SPCC continuum as-is the winner over
linear-weighted variants), and the narrowband class's real balance
mechanism is the NONLINEAR per-line object-anchored stretch
(`stretch_linked perline`), which equalizes object prominence with the
sky pinned. Candidate redesign: presets become perline ANCHOR POLICIES
(how each line's anchor/target resolves — e.g. `natural` = anchors from
the card's measured line rates; `per-source` = noise-capped per-line
gain, a starved band renders fainter never noisier; `custom` = explicit
per-line targets in the recipe), with linear weights remaining only as
the broadband mono-filters option (mild wheel imbalance, linked stretch
kept). Any preset implementation must still couple channel gain with
the corings' noise scope. USER RATIFICATION required for the redesigned
scope before code.

### C18 — Object-integrity audit: sharpen the structure measure + calibrate on the escapes

The standing object-region audit LANDED (`scripts/qa/object_integrity.py`,
wired WARN-only into every starcomb render): it grades the object the gate
is blind to against the render's OWN same-balance, co-registered input.
RELIABLE today: chroma neutralization (absolute object chroma vs the input
— catches the balance-probe/vst chroma-crush class) and coring MOTTLE
(mid-scale texture excess). Structure is a grain-robust, registration-
tolerant, worst-region correlation that catches GROSS object flattening but
does NOT resolve a SMALL LOCAL hollow (a Bubble-sized shell reads ~0.87,
washed out by the surrounding object; pushing the block smaller false-flags
on mottle). That specific hollow-shell class turned out to be an upstream
channel MISALIGNMENT, caught by `nightlight_sho.py`'s alignment check — a
complementary guard, not this render audit.

Remaining:
- **Small-local structure sensitivity** — a measure that isolates a
  shell-sized structure loss without false-flagging mottle (a matched-scale
  template / local-vs-neighborhood coherence, not a whole-object or
  fixed-block correlation). Real, separate effort.
- **Calibrate the thresholds on the FOUR measured escapes** (balance-probe
  neutralization, vst chroma-crush, linked-stretch drowned O3 sphere,
  coring mottle) — each must WARN, every approved render must not; the
  escapes regenerate from the pinned stacks with the recorded knobs.
- WARN-only until a class history exists; the gate never loosens. Companion
  to the ratified colour-gate redesign (C11, chain-ADDED colour) — together
  they bound the chain from both sides.

### C19 — Migrate the remaining hand-rolled processing operators to their tools — DONE

The render chain (`starcomb.py`) is now TOOL-ONLY: `operators.json` carries
6 processing operators, ALL status `tool`, 0 sanctioned / 0
migration-candidate, and `hand_roll_audit.py` PASSes with zero custom
processing. What happened, per operator:
- MIGRATED to siril: black point → `mtf b 0.5 1`; stars layer → `mtf 0 m 1`
  (python computes anchor m, siril applies); recombine → `pm` screen; final
  saturation → `satu`. (SCNR had already moved to siril `rmgreen`.)
- DELETED, hole left (NOT refilled with numpy): the multi-scale Wiener
  significance corings (`chroma_core`/`lum_core`). No tool provides
  multi-scale significance coring, and the tool denoisers (siril VST /
  GraXpert) ARE the denoise operators, so the corings were pure hand-rolled
  processing. Removing them raises stretch-amplified sky noise (a broadband
  set measured gate rings 8.2 vs the 8.0 bound — a declared delta needing
  rebaseline/re-judgment); the replacement lever is `starless_denoise`
  strength, laddered per class.
- DELETED as a Nightlight duplicate: the in-house per-line narrowband stretch
  + LCh finish (`satgamma`/`huerot`/`scnr`/`ppgamma`) and the in-house
  `color_engine=star_neutral` balance. Narrowband SHO colour+develop is
  Nightlight's job (C20), so the numpy that duplicated it is gone.

Determinism holds (byte-identical re-render measured). FOLLOW-ON (own
declared deltas, the user's eyes on finals): re-judge + rebaseline the
datasets whose look changed when the corings were removed (the 4
formerly-approved recipes were downgraded to `provisional` with a
`tool_migration` note); and if a non-self-flat faint-signal class wants more
sky-noise suppression than the tool VST gives, ladder `starless_denoise` gx
vs vstpost vs off — never reintroduce a numpy coring.

### C20 — Narrowband path: generalize Nightlight beyond SHO, calibrate

LANDED: **render-engine routing** (`render_engine` recipe field; a
mono-filters NARROWBAND SHO composition delegates to `nightlight_sho.py` by
default — the author's tool, sanctioned). The in-house numpy narrowband path
(`color_engine=star_neutral` + per-line stretch + LCh finish) was REMOVED in
C19 as hand-rolled processing that duplicated Nightlight — Nightlight is now
the SOLE honest narrowband colour+develop path (the star-neutral O3-sphere
mechanism siril has no equivalent for). A narrowband set on the starcomb
path gets the broadband linked stretch (dominant line only) and says so.

Remaining:
- **Generalize the nightlight engine beyond SHO** (dual-band HOO, other
  narrowband compositions) — `nightlight_sho.py` is 3-channel SHO-specific;
  a HOO or other-palette composition needs its own channel mapping / develop.
- **A native star-neutral colour tool** (so the O3-sphere balance is not
  Nightlight-only) stays a genuine gap — but it must be a TOOL mechanism, not
  the removed in-house numpy. Until one exists, Nightlight is the path.
- **Gold hue finish** on the green SHO base is a finishing CHOICE (the
  reference gold is the author's manual GIMP hue); drive it in Nightlight
  (`hue_offset`) on the user's eyes, never a rehydrated numpy huerot.
