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

_(add each writeup here, newest first)_

- [pipeline-wide-field-untracked](pipeline-wide-field-untracked.md) — THE
  step-by-step process document for the validated class (camera raws, fixed
  mount, wide field): every stage from staging to seeded baseline with the
  tool that touches the pixels, the record it writes, and the measured reason
  it is done that way (mount bands, dwell floor, desky regression, plain-mean
  compose, ICC legs, SPCC traps, stretch regimes, the complete stop list).
  EMPIRICALLY TESTED — validated end to end by the july31 blackbox rebuild.

  per-filter stretch → colorize → screen/channel-isolation with pseudogreen,
  saturation-null + chip-gap fills as the documented artifact pass, the
  Neptune separate-transfers doctrine (= the wide-field caption's short+long
  equivalent at L3), Schmidt's toolchain + "three congruent images", Hueso's
  WinJUPOS methods + CC-BY derotated products; Siril 1.4.4 SOURCE-verified to
  express the placed-points transfer via `pm` (probe-confirmed on-rig).
  Drives j2_widefield_v2.
  `query`), the consensus i2d→reproject→asinh→chromatic-palette workflow with
  tool fit (reproject sanctioned; `exact` wrong below 0.05″/px; Siril probes
  pre-registered; FITS Liberator v5 as the GUI reference), and the Jupiter
  recreation plan (PID 1373 provenance verbatim; wide-field first — its two
  filters are simultaneous, no derotation; the close-up's 9–22° rotation gap
  is the class decision). PROVISIONAL except the verified acquisition route.
- [lunar-lucky-imaging](lunar-lucky-imaging.md) — the LUNAR data class:
  lucky-imaging model mapped onto the repo's stage design (no solve/SPCC/BGE
  — documented skips), the 2025-26 stacker/finisher audit (Siril 1.4.4
  headless-except-registration; 1.5-dev `register_mpp` as the adoption test;
  PSS/AS!4/waveSharp/ImPPG evidence-tagged), Z6III capture doctrine
  (Lossless-NEF-only, 20 fps e-shutter), sampling regimes (70 mm disc =
  107 px → single-point alignment is proper; ≥800 mm → multi-point class),
  and the first-corpus route + pre-registered best-N% ladder. PROVISIONAL —
  no lunar pixel processed yet.
- [july23-dew-and-corner-chroma](july23-dew-and-corner-chroma.md) — the
  july23 session's two data-quality findings, current-state: LENS DEW (the
  known environment issue — measured halo-growth signature, the reusable
  detection instrument, the sets-01+02-only final combine, prevention
  checklist) and the RESOLVED warp-leg ICC toe defect (untagged-linear
  float contract, identity 1.0000 verified; corners restored to
  reference-class ≤1.018 R/G).
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

**Research pass — mid-2026 tool/technique landscape**:
- [x86-setup-and-install](x86-setup-and-install.md) — reproducible per-tool install
  on x86-64 Kali (headless, no GPU): the four-layer method (apt/flatpak/venv/pinned
  `/opt`), checksums, gotchas + a drafted **untested** `scripts/setup/x86_bootstrap.sh`.
- [siril-stacking-workflow](siril-stacking-workflow.md) — 2026 headless calibrate/
  register/integrate: rejection-by-sub-count, the unified `-weight=` that breaks
  migrated scripts, drizzle-on-register, and the WBPP gaps (no Local Norm / PSF-Signal-Weight).
- [siril-natives-and-trailed-solve](siril-natives-and-trailed-solve.md) — Siril
  1.4.4/1.5.0-dev native surface; the chroma-noise / AI-deconv / star-neutral gaps
  all still non-native; sharpened trailed-field `-localasnet` verification.
- [siril-pyscript-headless](siril-pyscript-headless.md) — resolves the "numpy-inside
  pyscript = tool or hand-roll?" question (mechanism-location split: Class-2 drivers
  vs Class-1 numpy-inside) + headless viability on Linux.
- [graxpert-3x-and-workflow-order](graxpert-3x-and-workflow-order.md) — GraXpert
  deconv is RC-only/stalled/buggy (correction); the linear-first workflow order is a
  strong default, not absolute (2026 AI-driven loosening).
- [free-ai-tool-wave-2026](free-ai-tool-wave.md) — free AI tools filtered for
  headless-Linux-CPU (StarNet2.5.3, DeepSNR, GraXpert, AstroDenoisePy, Cosmic
  Clarity); AstroSharp dead-end; SyQon GUI-gated.
- [narrowband-star-neutral-options](narrowband-star-neutral-options.md) — VeraLux
  Alchemy + DBXtract are the free OIII-unmix mechanism, but GUI-only Class-1; the
  headless narrowband-colour gap stays open.
- [synthetic-flats-and-bias](synthetic-flats-and-bias.md) — flatless/biasless
  calibration routes: model-division (GraXpert, vignetting-only, starlight-safe) vs
  a sky flat (captures motes/PRNU but contaminates on a frame-filling star field) vs
  skip-bias (CMOS) + synthetic offset; the starlight-first route + july14's real-flats-impossible
  decision. Since adopted + hardened: the sky flat is strictly PER-SET (the
  ratified exact-frames rule; imprint mechanism in dead-ends), pinned as
  `scripts/stack/build_sky_flat.sh`.
- [x86-empirical-test-plan](x86-empirical-test-plan.md) — the capstone: every
  "provisional until x86" flag from all deep-dives collapsed into one ordered,
  bracketed test protocol keyed to the x86 rebuild order (`docs/x86-empirical-test-plan.md`, Phase 0→5).
