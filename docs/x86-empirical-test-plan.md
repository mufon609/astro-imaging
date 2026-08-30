# x86 empirical-test plan — the provisional flags, as ordered experiments — deep dive

- **Question / scope** — Every research finding was PROVISIONAL until run on the
  x86 rig (the contract: "nothing is final until empirically tested"). This file
  collapsed all those flags into ONE ordered, bracketed protocol keyed to the
  rebuild order. It is now two things: the record of what the rebuild EXECUTED,
  with where each result lives; and the live protocol for the phases still open,
  keyed to their BACKLOG slugs. Inherited numbers re-measure in this order.
- **Context** — Rig: x86-64 Kali, i7-14700K, 28 threads, 31 GB, **no GPU**,
  headless. Each open row names what it SETTLES, the BRACKET/control, and the
  METRIC; a phase's result can change later phases.

## Executed — where each result lives

| phase | outcome | record |
|---|---|---|
| 0 — environment | bootstrap ran; the installed inventory with versions/sources/checksums is `scripts/setup/manifest.tsv`; free neural tools installed + driven CPU-only (Cosmic Clarity sharpen is the exception: Qt-modal, ATTENDED-only) | `CLAUDE.md` Environment; `TOOLS.md` per-tier rows + "What is installed" |
| 0 — rc-astro rows | MOOT — RC-Astro (and PixInsight) are NOT INSTALLED **by choice**, a deliberate gap, not a platform block; the `ldd`/`--benchmark-all` steps print from the bootstrap if ever bought | `TOOLS.md` "What is installed, and what is a deliberate gap" |
| 1 — orchestration port | tool-sourced measures re-run on this rig; every divergence/gap-filler sits in the removal-condition register with per-row status; `frame_metrics` CFA condition FIRED and honoured (debayer at convert; +9.1% FWHM inflation measured on the CFA arm); sirilpy headless via `.ssf`→`pyscript` probe-confirmed | `BACKLOG.md` `removal-conditions`; `CLAUDE.md` Environment |
| 2 — stack builder | chain reconciled to 1.4.4 and run; bare-`rej` default SETTLED (Winsorized, `help stack` on-rig); 16-bit intermediates condition FIRED with its cost measured (+21% master fixed-pattern; ~30–45% extended-structure contrast loss); undistort stage ran as written; the whole class chain validated end to end by the july31 blackbox rebuild | `TOOLS.md` Tier 1; `docs/dead-ends.md` (16-bit entries); `docs/pipeline-wide-field-untracked.md` |
| 3 — extractor half | RUN and settled: SExtractor's core `sep` is the SOLE extractor (returns trailed sources, median elongation ~1.3; blind-solves at logodds 299 vs the in-house peak centroids' 289, identical SPCC K); the in-house fallback is RETIRED | `docs/dead-ends.md`, trailed-solve entry; `solve_field.py` docstring |

## Open — the live protocol

### Phase 3 remainder — native solve + SIP (BACKLOG:`native-solve-and-sip`)
| Test | Settles | Bracket / metric | Pass |
|---|---|---|---|
| One real trailed ultra-wide stack solved 3 ways: (a) `solve_field.py` sep-xylist, (b) `astap_cli` + W08/G05 (`-z auto -speed slow`), (c) Siril `platesolve -localasnet -blindpos -blindres` + `setfindstar -relax=on -roundness=0.1 -maxR=large` | can native/ASTAP retire `solve_field.py`? (class-gated: the mildly-trailed class first — the dead-end was measured at roundness 0.615, july23-class data reads 0.80) | solve success · residual RMS · wall-clock | (a) is the baseline; retire only if (c) matches |

### Phase 4 — render toolkit, per tier (BACKLOG:`render-ladder`)
The ladder skeleton (L1 background → L2 denoise → L3 stretch → L4 satu), riders,
and limits live in BACKLOG:`render-ladder`; the learned-deconvolution question is
BACKLOG:`corner-fix-landscape` (OPEN item 1 — a procurement; nothing installed runs
headless); the chroma budget instrument is `noise_split.sh`
(BACKLOG:`walking-noise`); the narrowband star-neutral bracket is
BACKLOG:`star-neutral-colour`. One doctrine row stays here because it brackets the
ladder itself: **workflow order** — linear-first default vs the nonlinear-stage
alternative (`TOOLS.md`, "The one process rule": the 2026 AI tools loosen
linear-only) — one knob, gate/audit deltas, full-frame lossless finals, the
user's eyes on aesthetics.

### Phase 5 — extend the audit layer (open; candidates, not validated metrics)
| Test | Settles | Bracket / metric | Pass |
|---|---|---|---|
| Implement each candidate defect detector, run on DELIBERATELY degraded renders (over-sharpened / over-smoothed / over-flattened) + known-good | do the derived detectors actually fire? (they are constructions, not validated published astro metrics) | detector value on bad vs good | fires on bad, quiet on good, BEFORE it may gate |
| PSFSW proxy vs a PixInsight SubframeSelector export (if available) | the `(Σflux·Σmean_flux)/(σ_noise·M*)` proxy | rank correlation | high correlation = usable weight |

Surviving candidates (the deep-dive that derived them is retired; full
derivations + sources in git history): **residual-autocorrelation whiteness** +
**fine-scale-energy vs the noise floor** (denoise over-smoothing, the "plastic"
test); **removed-background-model spectral / negative-bowl** (BGE
over-flattening); **clip fractions, star-colour loss, chroma-channel MAD**
(clipping / colour); **gradient-decay sharpness** (arXiv 2410.10488). VOID:
the radial-profile undershoot detector's "reuses the existing radial profiles"
premise — that instrument was retired as circular (`docs/dead-ends.md`, trap 3);
a ringing detector needs a NEW mechanism, not a revival. Every estimator these
validate against comes from the tools (Siril `stat`/`register`/`seqtilt`,
SubframeSelector); a detector is a candidate *standalone ALLOWED detector* on
the `anomaly_audit.py` pattern ONLY where no tool measures the defect — never a
numpy gate.

## Cross-cutting acceptance (the contract)
Every render-altering result is judged by the three-check acceptance in
`README.md` ("How a change is accepted"): **reproducible** — verified cheaply to
a documented tolerance; byte-identity is not REQUIRED, though the current render
tier and the groups route both measured bit-reproducible on this rig
(`docs/dead-ends.md`) — the tolerance form stays because it survives a stage or
rig where determinism is unverified; **no-regression** across data classes on
the TOOLS' recorded measures, criteria never loosening; **declared delta**
(metric deltas + like-encoding panels; objective-better-or-equal may commit,
anything aesthetic needs the user's eyes on full-frame lossless finals). One
bracketed knob per experiment; a killed hypothesis becomes a `docs/dead-ends.md`
entry WITH its numbers.

## Sources
Internal synthesis of the research deep-dives (surviving ones in `docs/`,
retired ones in git history — each carried its own primary citations).

## Status
The executed table is MEASURED (each row's record named in place). The open
phases are hypotheses with named controls + metrics — they settle nothing until
run.

## Graduation
- Executed results live in the operating docs named per row; open work is keyed
  to BACKLOG slugs so this file and the queue cannot drift apart.
