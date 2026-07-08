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

Renderer-touching items that batch into a single polish pass.

### B1 — Harden the star-separation stdout trio contract

`starcomb._run_sep` picks the starless/stars/catalog paths as "the last
three printed lines ending .fit/.npz". It survives every current print in
both separators but is one future diagnostic line away from mis-parsing.
Have `starsep.py` and `starnet_sep.py` emit a sentinel-prefixed trio line
and parse THAT explicitly, with an index guard for fewer than three paths.
Byte-verify the approved recipe afterward, since the separation output feeds
the render.

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

