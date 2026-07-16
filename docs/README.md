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
  `rc-astro-cli-linux.md`, `narrowband-star-neutral-options.md`,
  `siril-pyscript-headless.md`. Not one per web search — one per investigation
  that reaches a conclusion.
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

- [wide-field-untracked-registration](wide-field-untracked-registration.md) — why a
  global homography smears edge stars on a wide UNTRACKED set, EMPIRICALLY TESTED on
  july14 set-01: field rotation/gnomonic projection are NOT the cause (pure rotation
  is exactly a homography — Szeliski); radial LENS DISTORTION is, so the class needed
  is undistort→homography. Siril `register -disto=` is the native fix and its
  mechanism is proven on-rig, but the MODEL is the blocker (Siril's matcher fails 36°
  fields; astrometry.net's SIP is not reproducible at wide index scales → a measured
  LOSS) — which blocks WCS-reprojection equally. The model IS in the NEF (exiftool
  reads Nikon's radial coefficients); nothing headless applies it.

**Research pass — mid-2026 tool/technique landscape** (2026-07-14):
- [x86-setup-and-install](x86-setup-and-install.md) — reproducible per-tool install
  on x86-64 Kali (headless, no GPU): the four-layer method (apt/flatpak/venv/pinned
  `/opt`), checksums, gotchas + a drafted **untested** `scripts/setup/x86_bootstrap.sh`.
- [siril-stacking-workflow](siril-stacking-workflow.md) — 2026 headless calibrate/
  register/integrate: rejection-by-sub-count, the unified `-weight=` that breaks
  migrated scripts, drizzle-on-register, and the WBPP gaps (no Local Norm / PSF-Signal-Weight).
- [plate-solving-and-drizzle](plate-solving-and-drizzle.md) — the trailed/ultra-wide
  solve (astrometry.net peak-xylist is the *intended* override; ASTAP W08/G05 HFD; Siril
  findstar least-robust) + the drizzle sampling truth (short-focal is *under*sampled).
- [siril-natives-and-trailed-solve](siril-natives-and-trailed-solve.md) — Siril
  1.4.4/1.5.0-dev native surface; the chroma-noise / AI-deconv / star-neutral gaps
  all still non-native; sharpened trailed-field `-localasnet` verification.
- [siril-pyscript-headless](siril-pyscript-headless.md) — resolves the "numpy-inside
  pyscript = tool or hand-roll?" question (mechanism-location split: Class-2 drivers
  vs Class-1 numpy-inside) + headless viability on Linux.
- [rc-astro-cli-linux](rc-astro-cli-linux.md) — the deep-verify: `rc-astro` v0.9.9
  standalone Linux CLI (BXT/NXT/SXT), exact flags, CPU wall-clock, license, offline.
- [graxpert-3x-and-workflow-order](graxpert-3x-and-workflow-order.md) — GraXpert
  deconv is RC-only/stalled/buggy (correction); the linear-first workflow order is a
  strong default, not absolute (2026 AI-driven loosening).
- [free-ai-tool-wave-2026](free-ai-tool-wave-2026.md) — free AI tools filtered for
  headless-Linux-CPU (StarNet2.5.3, DeepSNR, GraXpert, AstroDenoisePy, Cosmic
  Clarity); AstroSharp dead-end; SyQon GUI-gated.
- [narrowband-star-neutral-options](narrowband-star-neutral-options.md) — VeraLux
  Alchemy + DBXtract are the free OIII-unmix mechanism, but GUI-only Class-1; the
  headless narrowband-colour gap stays open.
- [objective-qa-defect-metrics](objective-qa-defect-metrics.md) — the AUDIT side:
  numpy/scipy-computable frame-quality + processing-defect metrics (ringing,
  over-smoothing, over-flattening) to extend the measurement layer.
- [synthetic-flats-and-bias](synthetic-flats-and-bias.md) — flatless/biasless
  calibration routes: model-division (GraXpert, vignetting-only, dust-safe) vs a
  sky flat (captures motes/PRNU but contaminates on frame-filling IFN) vs skip-bias
  (CMOS) + synthetic offset; the dust-first route + july14's real-flats-impossible
  decision.
- [x86-empirical-test-plan](x86-empirical-test-plan.md) — the capstone: every
  "provisional until x86" flag from all deep-dives collapsed into one ordered,
  bracketed test protocol keyed to the x86 rebuild order (`docs/x86-empirical-test-plan.md`, Phase 0→5).
