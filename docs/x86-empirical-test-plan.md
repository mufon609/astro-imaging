# x86 empirical-test plan — turning the provisional research into experiments — deep dive

- **Question / scope** — Every finding in this research pass is marked PROVISIONAL
  until run on the x86 rig (the contract: "nothing is final until empirically tested").
  This consolidates all those flags into ONE ordered, bracketed protocol, keyed to
  REDESIGN's rebuild order — an executable checklist so the rebuild settles each
  hypothesis with a control and a pass/fail metric, not by assertion.
- **Context** — 2026-07-14. Written from the ten deep-dives in `docs/`. Rig: x86-64
  Kali, i7-14gen, 32 GB, **no GPU**, headless. Each test names what it SETTLES, the
  BRACKET/control, the METRIC, and the source deep-dive. Run them in phase order; a
  phase's result can change later phases.

## The protocol

### Phase 0 — Found the environment (`docs/x86-setup-and-install.md`)
| Test | Settles | Bracket / metric | Pass |
|---|---|---|---|
| Run `scripts/setup/x86_bootstrap.sh --go` (fill TODO sha256 first) | the whole install plan | the verification pass (every tool `--version`/`--help`) | all exit 0 |
| `rc-astro bxt` + `rc-astro --version` on Kali | Ubuntu-22.04 binary vs Kali glibc (~2.38) forward-compat | runs vs "GLIBC not found" | runs; else document the gap |
| `rc-astro <t> --benchmark-all` + timed run (BXT/NXT/SXT) on a real frame, `--device cpu` | true CPU wall-clock (all quoted numbers are other CPUs) | seconds/frame at 24–60 MP | record; sanity ≈ tens-of-sec BXT |
| GraXpert `-cli -cmd denoising/deconv-obj -gpu false` timed | GraXpert CPU cost + which version installed | wall-clock; `pip show graxpert` | record; confirm 3.0.2 vs 3.2.0a2 |
| StarNet2 / DeepSNR / Cosmic Clarity headless run + timed | do the free binaries run CPU-only + wall-clock | seconds/min per frame | run headless, no display |

### Phase 1 — Port the measurement core (REDESIGN KEEP set)
| Test | Settles | Bracket / metric | Pass |
|---|---|---|---|
| Run `bg_qa` gate + `object_integrity` + `star_shell_report` on a known stack | the core ports verbatim (numpy/FITS/Siril-CLI) | same outputs as arm on the same inputs | identical within tolerance |
| astropy equatorial→galactic vs our fixed 3×3 in `astrometrics.py` | the arm-era hand-rolled matrix (astropy was absent) | max angular error vs `astropy.coordinates` | agree to arcsec |
| sirilpy headless via `.ssf`→`pyscript` under the x86 flatpak | the "proven on arm" claim on x86 | a trivial pyscript runs headless | runs, no display |

### Phase 2 — Rebuild the stack builder (`docs/siril-stacking-workflow.md`)
| Test | Settles | Bracket / metric | Pass |
|---|---|---|---|
| Reconcile `run_pipeline.sh`/`.ssf` to 1.4.4 syntax, then run calibrate→register→stack | migrated-script breakage (unified `-weight=`, `-2pass`, no `-noout`/`-cc=bothpasses`) | clean run on a known set; compare masters/stack | no syntax errors; stack sane |
| `help stack` on the flatpak | bare-`rej` default algorithm (UNCERTAIN) | is it Winsorized? | confirm or switch to `rej w 3 3` |
| Drop `partitioned_stack`; 32-bit end-to-end on a full sequence | the 7.7 GB→32 GB RAM relaxation | holds full sequence in RAM | completes without the workaround |

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
Every render-altering result is judged by the three-check acceptance: **deterministic**
(run twice → identical artifacts), **no-regression** (all registered datasets still pass
the gate + star-shell + inspection; the gate never loosens), and **declared delta**
(metric deltas + like-encoding panels; objective-better-or-equal may commit, anything
aesthetic needs the user's eyes on full-frame lossless finals). One bracketed knob per
experiment; a killed hypothesis becomes a REDESIGN dead-end entry **with its numbers**.

## Sources
Internal synthesis of the ten `docs/` deep-dives (each carries its own primary
citations + Status/Graduation). No new external sources.

## Verdict / recommendation
Run the phases in order on the x86 rig. Phase 0–2 are prerequisites (environment +
ported core + stack builder); Phase 3 settles the solve doctrine; Phase 4 is the
per-tier toolkit selection (each a measured declared delta); Phase 5 grows the product
(the audit layer). This document is the executable form of REDESIGN's rebuild order — it
is where "provisional" becomes "verified."

## Status
**PROVISIONAL by construction** — it is the list of what is NOT yet tested. It settles
nothing itself; it makes the settling reproducible. Every row is a hypothesis with a
named control + metric.

## Graduation
- **REDESIGN "Rebuild order"** — cross-reference this plan from each rebuild step, so the
  order is executed as bracketed experiments, not asserted.
- No TOOLS.md change (this is a test protocol, not a tool).
- Applied in this deep-dive's commit.
