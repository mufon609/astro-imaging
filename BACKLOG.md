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

The `hybrid` engine (StarNet2-ONNX run on the mask+inpaint starless) meets
every objective bar: gate PASS 1.375 (= the inpaint control), star aura_lum
+2.0 (= the approved render), the bright-star pedestal equals the inpaint
fill, the faint-tail residual drops to 589 detections (vs ~5.1k), and the
chroma rings improve 1.33/1.22 -> 1.11/1.00. Validated end-to-end; it awaits
only the user's aesthetic sign-off on like-encoding panels.

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
(k x sigma_G of the linear starless) holds to <=0.6. Acceptance is already
measured — a full noise-mode render on the canonical stack came out
byte-IDENTICAL to all four approved artifacts (k = 490.9663661574939). On
approval: flip the default, byte-verify the approved recipe once more, keep
`catalog` as a flag.

**Blocked by:** user's go-ahead (a render no-op on the current stack, but a
default change).

### A3 — Reorganize scripts/ into a professional, future-proof layout

scripts/ is a flat dump of ~two dozen files (orchestrators, siril templates,
the render chain, shared libs, QA, legacy). Group it by pipeline stage so
the workspace reads as a professional project. Multi-session; every step is
a pure move + path/import update with ZERO logic change, and the approved
recipe B7 must stay byte-identical (all four artifacts) after each phase —
that invariant gates the whole effort.

**Linchpin — the import strategy (Phase 1, DONE).** `scripts/lib/` now holds
the shared libs (astrometrics, bg_qa); every consumer got a uniform
depth-agnostic bootstrap that walks up from __file__ to the nearest dir
containing `lib/` and puts it on sys.path, so import STATEMENTS are unchanged
and Phases 3-5 file moves are pure `git mv` (no bootstrap edits). Constraint
for later phases: the non-lib sibling imports (starcomb->experiment,
starnet_sep->starsep, measure_stack->starcomb) resolve via Python's same-dir
auto-add, so keep each pair co-located when moved. Phase 2 adds the extracted
quicklook helpers into lib/. Audit refinements to the original plan, verified
in Phase 1: (a) the two lib files moved as PURE RENAMES — astrometrics's
own-dir insert now resolves to lib/ and bg_qa has no bootstrap (lazy `import
astrometrics`), so neither needed editing; the bootstrap is a consumer-only
concern. (b) solve_field (2 sites) + starnet_sep (1) had inside-function
inserts, hoisted to the module-top uniform bootstrap (their lazy
astrometrics/starsep imports kept). (c) the only Phase-1 by-path coupling was
run_post.sh's `bg_qa.py` invocation (repointed to `lib/bg_qa.py`);
run_pipeline.sh references neither lib.

**Target tree** (final; approached over phases):

    scripts/
      lib/         astrometrics.py, bg_qa.py (gate, still runnable),
                   <quicklook helpers extracted from experiment.py>
      stack/       run_pipeline.sh, selfflat.py, rechroma.py,
                   siril/  master_{bias,flat,dark}.ssf, lights.ssf.tmpl,
                           selfflat_{median,median2,divide,stack}.ssf.tmpl
      calibrate/   solve_field.py, spcc_run.py
      render/      starcomb.py, separation/ starsep.py starnet_sep.py
      qa/          inspect_stage.py, judgment_crops.py, measure_stack.py,
                   diag_flat.ssf
      geometry/    suggest_foreground.py
      legacy/      experiment.py (thinned), run_post.sh, postprocess.ssf.tmpl

**Coupling to update on each move:** run_pipeline.sh + run_post.sh sed/exec
paths (~13 template + py references); starcomb's subprocess construction of
the starsep/starnet paths; help strings, the README repo map, CLAUDE.md
paths, and the config_<set>.json _readme. The .ssf templates' INTERNAL
load/save paths are relative to the siril workdir, NOT scripts/, so moving
the files is safe — only the shell source path changes.

**Phases** (one per session-sized chunk; byte-verify + commit each):
  1. DONE — Import foundation: lib/ + the uniform bootstrap (the linchpin above).
  2. Extract experiment.py's eight shared helpers (run_graxpert, GRAXPERT,
     measure_jpg, sanitize, star_region, value_row, compose_rows, fmt) into
     lib/; repoint starcomb; thin/retire experiment.py into legacy/, pruning
     the four unlinked-stretch CHAINS (a dead end) to the one linked
     baseline.
  3. Render chain: starcomb -> render/, starsep + starnet -> render/
     separation/; update the subprocess paths.
  4. Stack pipeline: run_pipeline + selfflat + rechroma -> stack/, templates
     -> stack/siril/; update run_pipeline's sed/exec paths.
  5. calibrate/ qa/ geometry/ legacy/ groupings; update the remaining paths.
  6. Docs + polish: README repo map, CLAUDE.md, help strings, config note;
     optionally rename the numeric-prefixed templates to descriptive names.

**Every phase:** pure move (no logic change); py_compile + import-check every
touched module; byte-verify B7 (all four artifacts cmp-identical) — one
differing byte STOPS the phase; commit the phase alone; new/edited comments
follow the no-history-in-comments bar.

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

