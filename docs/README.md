# docs/ — research deep-dives

Well-structured writeups of the knowledge-base research this repo does
between processing work. The harness's RECORD + AUDIT function extends to the
tool/technique landscape: this is where a session lands a **major deep-dive**
(a tool, a technique, a comparison, an open question) as a durable, cited
`.md` — before its conclusions graduate into the operating docs.

**Research only. No image processing happens here or anywhere in a research
session** (the repo drives industry tools; it never processes pixels itself —
`CLAUDE.md` "What this repo IS").

## The rules

- **One `.md` per MAJOR deep-dive.** Descriptive kebab-case name, e.g.
  `lunar-lucky-imaging.md`, `wide-field-untracked-registration.md`,
  `stacking-vs-official-pipelines.md`. Not one per web search — one per
  investigation that reaches a conclusion.
- **Findings are PROVISIONAL until empirically tested** (CLAUDE binding rule).
  Mark mechanism/research findings as such and name the test that would settle
  each.
- **Cite sources** (links). Prefer primary + recent (2025–2026).
- **Graduate durable findings.** docs/ is the deep record; the *operating*
  docs are the distilled truth. When a finding is solid, fold it into the
  right operating doc — a `TOOLS.md` tier entry, a `docs/dead-ends.md` dead-end, a
  `MEMORY.md` note — and record that graduation in the writeup. Don't let
  docs/ and the operating docs drift.
- **Retire fully-graduated deep-dives.** A writeup earns deletion when every
  durable finding is enforced in code or documented in an operating doc with
  its mechanism and numbers — git history keeps the full text (and the
  retirements name where each fact landed). What stays here must be
  load-bearing: the live deep record for an open thread, or the route + traps
  reference the code cites.

## Template (each deep-dive `.md`)

```
# <Topic> — deep dive

- **Question / scope** — what it investigates + why it matters to the harness.
- **Context** — date; tool/Siril versions; the rig constraints that bear on it
  (x86-64, no GPU, headless-preferred).
- **Findings** — the substance, organized.
- **Sources** — cited links.
- **Verdict / recommendation** — adopt / skip / alternatives, and why.
- **Status** — PROVISIONAL (mechanism/research) vs EMPIRICALLY TESTED.
- **Graduation** — what this changed in TOOLS.md / `docs/dead-ends.md` / MEMORY (or "none yet").
```

## Index

_(add each writeup here, newest first; retired writeups live in git history)_

- [pipeline-wide-field-untracked](pipeline-wide-field-untracked.md) — THE
  step-by-step process document for the validated class (camera raws, fixed
  mount, wide field): every stage from staging to seeded baseline with the
  tool that touches the pixels, the record it writes, and the measured reason
  it is done that way (mount bands, dwell floor, desky regression, plain-mean
  compose, ICC legs, SPCC traps, stretch regimes, the complete stop list).
  EMPIRICALLY TESTED — validated end to end by the july31 blackbox rebuild.
- [lunar-lucky-imaging](lunar-lucky-imaging.md) — the LUNAR data class:
  lucky-imaging model mapped onto the repo's stage design (no solve/SPCC/BGE
  — documented skips), the 2025-26 stacker/finisher audit (Siril 1.4.4
  headless-except-registration; 1.5-dev `register_mpp` as the adoption test;
  PSS/AS!4/waveSharp/ImPPG evidence-tagged), Z6III capture doctrine
  (Lossless-NEF-only, 20 fps e-shutter), sampling regimes (70 mm disc =
  107 px → single-point alignment is proper; ≥800 mm → multi-point class).
  EMPIRICALLY TESTED on the first corpus (two sets), refinements measured in
  place; the class builder is `scripts/stack/run_lunar_pipeline.sh` and the
  open ladder is BACKLOG:`lunar-ladder`.
- [stacking-vs-official-pipelines](stacking-vs-official-pipelines.md) — the
  stacking chain audited stage-by-stage against CURRENT official doctrine
  (Siril 1.4.4 docs/scripts/team statements; PixInsight 1.9.4 + WBPP 2.9.0 as
  the industry reference; DSS/APP cross-checks), with the july23 4-set NAN run
  as the live test. Verdict: doctrine-compliant at every documented Siril
  stage; three documented adaptations (per-set sky flat — no vendor sanctions
  a lights-built flat; external darktable undistort — mechanically PI's own
  "external distortion model" idea; 16-bit intermediates — removal condition
  FIRED on x86); the two standing Siril-side gaps vs WBPP (Local
  Normalization, PSF-Signal-Weight) confirmed still open at 2.9.0; named
  tests pre-registered (Siril-native SIP `-disto=` vs the warp, native blind
  solve on the mildly-trailed class, `-opt` dark optimization, Bayer-drizzle
  colour route).
- [wide-field-untracked-registration](wide-field-untracked-registration.md) — why a
  global homography smears a wide UNTRACKED set, EMPIRICALLY TESTED and SOLVED:
  field rotation/gnomonic projection are NOT the cause (pure rotation is exactly a
  homography — Szeliski); radial LENS DISTORTION is, so the class is
  undistort→homography. The model source decides everything: a per-frame SIP fit and
  a community DB profile's paraxial region are both measured failure modes
  (`dead-ends.md`); the adopted route corrects with a model **fitted from the set's
  own frames** (Hugin between-frame fit → lensfun entry → darktable warp), measured
  by the drift-axis station tool `seqtilt` cannot replace. Production:
  `scripts/stack/run_undistort_pipeline.sh` + `scripts/darktable/fit_lens_model.sh`.
- [x86-empirical-test-plan](x86-empirical-test-plan.md) — the capstone: every
  "provisional until x86" flag collapsed into one ordered, bracketed protocol.
  Now half record, half protocol: the executed phases state their outcome and
  the operating doc holding it; the open phases key to BACKLOG slugs
  (`native-solve-and-sip`, `render-ladder`) plus the audit-layer candidate
  detectors (Phase 5, none validated).

## Retired root reports — recover by commit, not by path

The combine-corner / compose-smear arc produced five root-level reports. Their
durable findings have all graduated into the operating docs — `docs/dead-ends.md`
(the mechanisms and the blind instruments), `docs/combine-contract.md` (the
contract, the gate thresholds, the scope tiers, the standards comparison, the
history), `TOOLS.md` (the hugin, darktable and
embedded-model rows) and BACKLOG `optical-state-models` — so the reports were
retired rather than left to contradict them.

Recover any of them at the commit before their removal:

    git show f64603d:COMPOSE_SMEAR_INVESTIGATION_report.md
    git show f64603d:COMPOSE_SMEAR_FIX_PLAN.md
    git show f64603d:COMBINE_CORNERS_AUDIT_report.md
    git show f64603d:COMBINE_HISTORY_AND_STANDARDS.md
    git show f64603d:EMBEDDED_LENS_MODEL_RESEARCH_report.md

`datasets/aug06/experiments.jsonl` cites them by name in entries written while
they existed; those citations resolve the same way. Citing a COMMIT rather than a
working-tree path is the standing convention here — a bare path in a long-lived
record goes dangling the first time a session is reset.


## `untracked-widefield-standards.md` — how the field actually stacks untracked
## camera-lens wide-field (fresh-eyes standards reading)

An unanchored reading of Siril's own docs, PixInsight's, the FITS distortion
conventions (SIP / TPV / TNX), the survey lineage (SCAMP+SWarp, Pan-STARRS, DES,
HST) and the forums, written before the repo was opened and with the repo
comparison quarantined in its own final section. 45 cited sources. Its durable
findings have graduated into `docs/dead-ends.md` (the lensfun `acm` version
boundary and the `<center>` kill), `TOOLS.md` (the hugin and darktable+lensfun
rows) and BACKLOG `one-sided-band`; the deep-dive keeps the citations and the
reasoning behind them.

The aug06 member-edge chase and this arc's prompts were retired the same way the
compose-smear arc's were — findings graduated, recovery by commit:

    git show 53edcc2:AUG06_MEMBER_EDGE_report.md
    git show 53edcc2:CHASE_AUG06_MEMBER_EDGE_PROMPT.md
    git show 53edcc2:RESEARCH_UNTRACKED_STACKING_PROMPT.md
