# x86 empirical-test plan — turning the provisional research into experiments — deep dive

- **Question / scope** — Every finding in this research pass is marked PROVISIONAL
  until run on the x86 rig (the contract: "nothing is final until empirically tested").
  This consolidates all those flags into ONE ordered, bracketed protocol, keyed to
  the x86 rebuild order — an executable checklist so the rebuild settles each
  hypothesis with a control and a pass/fail metric, not by assertion.
- **Context** — Written from the ten deep-dives in `docs/`. Rig: x86-64
  Kali, i7-14gen, 32 GB, **no GPU**, headless. Each test names what it SETTLES, the
  BRACKET/control, the METRIC, and the source deep-dive. Run them in phase order; a
  phase's result can change later phases.

## The protocol

### Phase 0 — Found the environment (`docs/x86-setup-and-install.md`)
| Test | Settles | Bracket / metric | Pass |
|---|---|---|---|
| Run `scripts/setup/x86_bootstrap.sh --go` (fill TODO sha256 first) | the whole install plan | the verification pass (every tool `--version`/`--help`) | all exit 0 |
| `ldd <rc-astro>` + `rc-astro --version` (a LIBRARY check, not a desktop one) | the real dep = glibc ≥2.35 / GLIBCXX ≥3.4.30 / AVX2 floor (Kali has 2.42 / 3.4.35 — verified) | no "not found" libs; runs | runs; a missing lib → `apt install <it>`, not a DE/distro change |
| `rc-astro <t> --benchmark-all` + timed run (BXT/NXT/SXT) on a real frame, `--device cpu` | true CPU wall-clock (all quoted numbers are other CPUs) | seconds/frame at 24–60 MP | record; sanity ≈ tens-of-sec BXT |
| GraXpert `-cmd denoising`/`deconv-obj` `-gpu false` timed (flag spelling is build-specific — resolve on the pinned build) | GraXpert CPU cost + which version installed | wall-clock; version print | record; OFFICIAL 3.0.2 (or 3.1.0-RC for deconv) only — PyPI 3.2.0a2 is the geeksville fork, do not install |
| StarNet2 / DeepSNR / Cosmic Clarity headless run + timed | do the free binaries run CPU-only + wall-clock | seconds/min per frame | run headless, no display |

### Phase 1 — Port the orchestration + record layer
| Test | Settles | Bracket / metric | Pass |
|---|---|---|---|
| Re-run the tool-sourced measures on a known stack — Siril `stat`/`seqstat`, `register` regdata via `inspect_stage.py`, `seqtilt` via `star_shape.py` | the orchestration ports (the TOOLS do the measuring; there is no in-house measurement core) | same tool numbers as arm on the same inputs | agree within tolerance |
| astropy equatorial→galactic vs our fixed 3×3 in `astrometrics.py` (ARM-doable now — astropy 8.0.1 installed) | the arm-era hand-rolled matrix | max angular error vs `astropy.coordinates` | agree to arcsec |
| Fire the removal conditions the x86 rig unblocks — 32-bit intermediates, debayered `frame_metrics` re-measure (the astropy FITS-parser + 3×3 retirement is ARM-doable now, item 9) | the register in `BACKLOG.md`; each is gated on this rig, not on research | each retirement lands as a declared delta | condition fired + register updated |
| sirilpy headless via `.ssf`→`pyscript` under the x86 flatpak | the "proven on arm" claim on x86 | a trivial pyscript runs headless | runs, no display |

### Phase 2 — Rebuild the stack builder (`docs/siril-stacking-workflow.md`)
| Test | Settles | Bracket / metric | Pass |
|---|---|---|---|
| Reconcile `run_pipeline.sh`/`.ssf` to 1.4.4 syntax, then run calibrate→register→stack | migrated-script breakage (unified `-weight=`, `-2pass`, no `-noout`/`-cc=bothpasses`) | clean run on a known set; compare masters/stack | no syntax errors; stack sane |
| `help stack` on the flatpak | bare-`rej` default algorithm (UNCERTAIN) | is it Winsorized? | confirm or switch to `rej w 3 3` |
| 32-bit end-to-end on a full sequence (drop `set16bits`) | the 7.7 GB→32 GB RAM relaxation, and the 16-bit stack-time intermediates' removal condition | holds full sequence in RAM; stack noise vs the 16-bit path | completes without the workaround |
| Run the UNDISTORT stage end to end (`install_styles.sh` + `install_lens_model.sh` → `run_undistort_pipeline.sh`, its first as-written run) | the arm-era WIN re-measured on x86 (every arm finding is a hypothesis here) | Siril `seqtilt` + `scripts/qa/star_stations.py`, control vs corrected | reproduces the fitted-model render's direction and magnitudes: off-axis ~0.25 px; centre station at the perpendicular-station level (~3.4–3.8 px majFWHM, no along-drift band); seqtilt truncated-mean ~3.0–3.1 px |

### Phase 3 — Plate solving, the trailed class (`docs/plate-solving-and-drizzle.md`)
| Test | Settles | Bracket / metric | Pass |
|---|---|---|---|
| One real trailed ultra-wide stack solved 3 ways: (a) `solve_field.py` peak-xylist, (b) `astap_cli` + W08/G05 (`-z auto -speed slow`), (c) Siril `platesolve -localasnet -blindpos -blindres -nocrop` + `setfindstar -relax=on -roundness=0.1 -maxR=large` | can native/ASTAP retire `solve_field.py`? | solve success · residual RMS · wall-clock | (a) is the baseline; retire only if (c) matches |
| Inspect the trails | uniform vs rotational trailing (affects ASTAP) | centroid consistency across the field | informs the ranking |

### Phase 4 — The render toolkit, per tier (`TOOLS.md` + the tool deep-dives)
| Test | Settles | Bracket / metric | Pass |
|---|---|---|---|
| **Workflow order** on a real dataset: linear-first default vs the 2026 nonlinear-stage alternative (ben.land) | strong-default vs a measurable alternative | gate/audit deltas, full-frame lossless finals | declared delta; user's eyes on aesthetics |
| **Deconv**: BXT `--correct-only` vs GraXpert deconv (RC) vs Siril RL, on trailed stars | which fixes trailing; is GraXpert deconv usable/buggy (#243) | star roundness + ringing (the radial-undershoot metric) | BXT expected best; measure |
| **Denoise / chroma**: does NXT AI3 expose a chroma-specific control + close the chroma-noise gap? vs DeepSNR / Siril `denoise` / GraXpert | the NXT-AI3 "likely fill" (UNVERIFIED) | chroma-channel MAD on masked background (audit metric) | chroma noise down without texture loss |
| **Star-neutral (narrowband)**: measure mean star colour in the examine layer → apply a diagonal `ccm`; bracket vs SPCC and vs Nightlight (`go build`) | the doctrine-clean ccm+measurement design (untested) | OIII-shell B/R + mean star chroma → neutral | sphere lifts, stars ~neutral |
| **pyscript headless**: try a Class-1 GUI script (VeraLux) under `xvfb-run`/`QT_QPA_PLATFORM=offscreen`; run a dual-mode one (`Statistical_Stretch`, SyQon Prism `--no-gpu`) via `.ssf` | are Class-1 GUI scripts batch-drivable? (expected: no) | does it run + accept params non-interactively | confirm the escape-hatch boundary |

### Phase 5 — Extend the audit layer (`docs/objective-qa-defect-metrics.md`)
| Test | Settles | Bracket / metric | Pass |
|---|---|---|---|
| Implement each candidate metric, then run on DELIBERATELY degraded renders (over-sharpened / over-smoothed / over-flattened) + known-good | do the derived detectors actually fire? (they are constructions, not validated) | detector value on bad vs good | fires on bad, quiet on good, before it may gate |
| PSFSW proxy vs a PixInsight SubframeSelector export (if available) | the `(Σflux·Σmeanflux)/(noise·M*)` proxy | rank correlation | high correlation = usable weight |

## Cross-cutting acceptance (the contract)
Every render-altering result is judged by the three-check acceptance in `README.md`
("How a change is accepted"): **reproducible** — NOT a byte-identical double-render,
which is the wrong bar on this chain (the neural tools' multi-threaded inference is not
bit-reproducible, and even darktable's TIFF differs by a metadata byte per run while its
warp reproduces exactly) — verified cheaply to a documented tolerance; **no-regression**
across data classes, judged on the TOOLS' recorded measures against each dataset's
baseline, criteria never loosening; and **declared delta** (metric deltas + like-encoding
panels; objective-better-or-equal may commit, anything aesthetic needs the user's eyes on
full-frame lossless finals). One bracketed knob per experiment; a killed hypothesis
becomes a `docs/dead-ends.md` entry **with its numbers**.

## Sources
Internal synthesis of the ten `docs/` deep-dives (each carries its own primary
citations + Status/Graduation). No new external sources.

## Verdict / recommendation
Run the phases in order on the x86 rig. Phase 0–2 are prerequisites (environment +
ported core + stack builder); Phase 3 settles the solve doctrine; Phase 4 is the
per-tier toolkit selection (each a measured declared delta); Phase 5 grows the product
(the audit layer). This document is the executable x86 rebuild order — it
is where "provisional" becomes "verified."

## Status
**PROVISIONAL by construction** — it is the list of what is NOT yet tested. It settles
nothing itself; it makes the settling reproducible. Every row is a hypothesis with a
named control + metric.

## Graduation
- **This plan IS the x86 rebuild order** — each rebuild step runs from this plan, so the
  order is executed as bracketed experiments, not asserted.
- No TOOLS.md change (this is a test protocol, not a tool).
- Applied in this deep-dive's commit.
