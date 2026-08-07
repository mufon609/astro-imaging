# DOCS_CLEANUP_PROMPT report — the docs/ deep-dives pass, executed

Third pass of the repo-slimming campaign, per `DOCS_CLEANUP_PROMPT.md`. The
ratified principle applied throughout: a note earns deletion when its durable
content is enforced in code or documented in an operating doc with its
mechanism and numbers — git keeps the full text of everything removed.

Commits of this pass (audit against these):
`d3ce14a` (test plan condensed) → `e730d3b` (3 banner-flagged retired) →
`7a23dd9` (6 tool-research retired) → `2dd133a` (4 served retired) →
`0e4cdcb` (index rewrite). Every retirement commit repoints its citations in
the same commit — the tree has no dangling reference at any of the five states.

## 1. Disposition table

18 in-scope deep-dives. "Where the facts live" pointers were VERIFIED by
opening the target and finding the fact before deletion, not read off the
files' own Graduation sections.

| file | lines | disposition | reason; where each unique load-bearing fact now lives |
|---|---|---|---|
| objective-qa-defect-metrics.md | 224 | **RETIRED** (`e730d3b`) | Verdict #1 VOID per its own banner (proposed reviving the instrument that is dead-ends trap 3). Tools-measure principle → `TOOLS.md` "Orthogonal to all tiers" + `CLAUDE.md` bright line; PSFSW proxy structure → graduated inline to `TOOLS.md` Tier 1; surviving detector candidates + the VOID note → `docs/x86-empirical-test-plan.md` Phase 5; estimator definitions re-derivable from the PixInsight ImageWeighting doc TOOLS cites |
| plate-solving-and-drizzle.md | 186 | **RETIRED** (`e730d3b`) | Top entry's identity superseded (peak-centroid → `sep`, the A/B it called for ran: logodds 299 vs 289). Robustness ranking + W08/G05 + xylist-is-intended → `docs/dead-ends.md` trailed-solve entries + `TOOLS.md` Tier 2; drizzle sampling truth (minor-axis FWHM, backwards-oversampling correction, CFA-drizzle 1×) → `docs/dead-ends.md` drizzle entry; ASTAP DB choice also enforced in `scripts/setup/x86_bootstrap.sh` |
| rc-astro-cli-linux.md | 176 | **RETIRED** (`e730d3b`) | Driving manual for a tool NOT INSTALLED by choice. Decision-relevant facts (v1.0.0 CLI, prices, `--correct-only`, NXT-AI3 `denoise_color`, AVX2/CPU fallback, offline-after-activation, call-the-binary-directly) → `TOOLS.md` Tiers 5/6/7 + cross-cutting "PAID, real Linux CLI"; activation/model-cache/flag-capture steps → printed by `scripts/setup/x86_bootstrap.sh`; glibc-floor decode → the bootstrap's rc-astro block |
| free-ai-tool-wave.md | 135 | **RETIRED** (`7a23dd9`) | Every verdict lives in `TOOLS.md` Tiers 5/6/7 + cross-cutting at NEWER, measured state (Cosmic Clarity 6.6 installed, Qt-modal sharpen trap, saturating chroma knob — all post-dating the file); AstroSharp dead-end → Tier 5 row; SyQon naming/headless → Tiers 6/7 + cross-cutting; AIDT/AIST + AstroForge watch-list → graduated to `TOOLS.md` cross-cutting |
| ui-position-and-zero-state-brief.md | 146 | **RETIRED** (`2dd133a`) | Consumed work order: its deliverable is the KEPT report, the ratified design shipped (`d2c6a5c`). Constraints it restated live in `web/README.md` / `CLAUDE.md` / the report itself |
| narrowband-star-neutral-options.md | 152 | **RETIRED** (`7a23dd9`) | Two-mechanism split (star-anchored vs nebula/QE-anchored), ccm-diagonal design, Nightlight dormancy + brightest-quartile correction, Alchemy/DBXtract scoping, SPCC-is-the-cause → `TOOLS.md` Tier 10 (richer than the file); UNTESTED design + bracket → `BACKLOG.md` `star-neutral-colour`; OIII-sphere mechanism → `docs/dead-ends.md` |
| siril-stacking-workflow.md | 158 | **RETIRED** (`7a23dd9`) | Its purpose (reconcile migrated scripts to 1.4.4) is served — the chain runs. Rejection-by-sub-count, norms, unified `-weight=` breakage, `-2pass`→`seqapplyreg`, drizzle-on-register, WBPP gaps, bare-`rej` on-rig settlement → `TOOLS.md` Tier 1; `-cc` modes → `docs/stacking-vs-official-pipelines.md` §A/§B; canonical script lines → the official `.ssf` quoted there |
| siril-pyscript-headless.md | 185 | **RETIRED** (`7a23dd9`) | The Class-1/Class-2 mechanism-location split IS `TOOLS.md`'s class-3 definition + cross-cutting section; per-script classifications → the same TOOLS rows; `.ssf`→`pyscript` headless mechanics + the `requires` trap → `CLAUDE.md` Environment |
| siril-natives-and-trailed-solve.md | 209 | **RETIRED** (`7a23dd9`) | The three native gaps (chroma / AI-deconv / star-neutral) with fresh-citation status → `TOOLS.md` Tiers 5/6/10 + `docs/dead-ends.md` chroma entry; localasnet-feeds-findstar + >5°-crop-moot mechanism → `TOOLS.md` Tier 2 verification note + dead-ends trailed-solve entry; `savepng`/`savetif` facts → `TOOLS.md` Tier 12; 1.5-dev `-mask` → Tier 6 row + BACKLOG `siril-1.5` |
| graxpert-3x-and-workflow-order.md | 209 | **RETIRED** (`7a23dd9`) | Version/channel split (3.0.2 stable; deconv RC-only; geeksville fork warning), bug #243, CPU costs, CLI quirks → `TOOLS.md` Tiers 4/5/6 + `scripts/setup/x86_bootstrap.sh` GraXpert block; workflow-order consensus + the three refinements → `TOOLS.md` "The one process rule"; Division-flat class limit → `docs/dead-ends.md` GraXpert-Division entry |
| synthetic-flats-and-bias.md | 212 | **RETIRED** (`2dd133a`) | Status was "ADOPTED AND HARDENED INTO A RULE". Route map (division vs sky flat vs skip, class limits) → `TOOLS.md` Tier 1 Pick; build recipe + validation gates → `scripts/stack/build_sky_flat.sh` docstring; contamination / alt-az bake-in / per-set imprint / CMOS skip-bias mechanisms → `docs/dead-ends.md` Gain/flat entries + `TOOLS.md` Tier 1; `subsky` subtraction-only settlement → `TOOLS.md` Tier 1; july14 decision → that archived session's records (git) |
| x86-setup-and-install.md | 218 | **RETIRED** (`2dd133a`) | Superseded by its own artifact: `scripts/setup/x86_bootstrap.sh` (pins, URLs, sha256s, the lensfun plain-HTTP integrity exception in Layer-A2 comments) + `scripts/setup/manifest.tsv` + `CLAUDE.md` Environment; darktable/lensfun setup → `CLAUDE.md` + `TOOLS.md` Tier 2b + dead-ends. Also carried a DRIFTED ICC claim (`--icc-type SRGB`, "never LIN_REC709") that the shipped float-leg contract inverted — a fourth drift instance beyond the three bannered in `e40c007` |
| july23-dew-and-corner-chroma.md | 112 | **RETIRED** (`2dd133a`) | Halo photometry (mean-not-median + full timeline numbers 6.25→10.3 ADU, +91%) → `docs/dead-ends.md` halo entry; dew prevention → the acquisition checklist's dew-control line; ICC toe contract + `icc_remove` trap + verify-at-sky-level → dead-ends ICC entry; session state → archived (datasets/july23 reset to raws, `50dfd20`), so its record pointers were already history-only |
| x86-empirical-test-plan.md | 100 | **CONDENSED → 86** (`d3ce14a`) | Phases 0–2 + the extractor half of 3 are executed — now one-line outcomes each with the record that holds it; open phases key to BACKLOG slugs (`native-solve-and-sip`, `render-ladder`, `learned-deconvolution`, `star-neutral-colour`); Phase 5 keeps the surviving audit-layer candidates + the VOID note. Kept because `CLAUDE.md`, `MEMORY.md`, `README.md` ×2 and `datasets/README.md` all cite it as the re-measure order — a retirement would have forced content edits in protected files |
| ui-position-and-zero-state-report.md | 393 | **KEPT** | Live design record of the SHIPPED position/PENDING work; cited from `web/serve.py` (×2, as the position/scope contract) and `docs/pipeline-wide-field-untracked.md`. One repoint: its line-4 link to the retired brief |
| lunar-lucky-imaging.md | 260 | **KEPT** | The live class record for an open thread (BACKLOG `lunar-ladder`); cited from `run_lunar_pipeline.sh`, `TOOLS.md` Tier L, `BACKLOG.md` |
| stacking-vs-official-pipelines.md | 289 | **KEPT** | The standing doctrine audit README's review contract requires; cited from `TOOLS.md` Tier 1; current (Siril 1.4.4 / WBPP 2.9.0); its named tests E1–E4 live as BACKLOG slugs. Two repoints (retired sources line, retired july23 pointer) |
| wide-field-untracked-registration.md | 622 | **KEPT** at the pass; then **AUDITED + CONDENSED → 385** on user order (`1f5fc6c`, §5.2) | The "route + traps" reference the code cites (`run_undistort_pipeline.sh`, `lens_preflight.py`, plus `CLAUDE.md`/`README.md`/`TOOLS.md` Tier 2b/dead-ends). The audit found a fifth drift instance (16-bit-era ICC rule stated as the production contract — corrected against the shipped code); measured tables kept, duplicated route/trap prose deduplicated to TOOLS Tier 2b / dead-ends / the script docstring; stale open items superseded in place (one-sided term → BACKLOG:`one-sided-band`) |
| docs/README.md | 151 → 106 | **INDEX REWRITTEN** (incrementally + `0e4cdcb`) | Matches the surviving set exactly (verified, §6); orphan fragment removed; report entry added; lunar entry's stale PROVISIONAL corrected to the file's own EMPIRICALLY TESTED; retirement rule added to "The rules"; example filenames now name survivors |

Not touched (out of scope, no pointer breakage): `docs/dead-ends.md` and
`docs/pipeline-wide-field-untracked.md` beyond the pointer fixes listed in §3.

## 2. Graduations performed (fact → where it landed)

1. **PSFSW proxy** — `(Σflux·Σmean_flux)/(σ_noise·M*)`, ranked within a
   dataset; reproduces PSFSW to R²≈95–99% from SNR², SNR and star count →
   `TOOLS.md` Tier 1, inline at the former citation site (`e730d3b`).
2. **Free-tool watch-list** — AIDT/AIST (mdci.ro) + AstroForge (astroforge.de),
   platform/free/headless UNVERIFIED → `TOOLS.md` cross-cutting FREE-stack
   paragraph (`7a23dd9`).
3. **Surviving audit-layer detector candidates** (whiteness,
   fine-scale-vs-noise-floor, removed-model spectral/negative-bowl, clip
   fractions, star-colour loss, chroma-channel MAD, gradient-decay sharpness)
   + **detector #1 VOID** (needs a new mechanism, not a revival — dead-ends
   trap 3) → `docs/x86-empirical-test-plan.md` Phase 5 (`d3ce14a`).
4. **The retirement principle itself** → `docs/README.md` "The rules"
   (`0e4cdcb`), so the practice this campaign ratified is documented where the
   next research session lands.
5. Two drift corrections in surviving files, aligned to the operating docs'
   measured state: the test plan's "neural tools are not bit-reproducible"
   clause → the dead-ends-measured bit-identity + CLAUDE.md tolerance form
   (`d3ce14a`); the index's lunar "PROVISIONAL — no lunar pixel processed yet"
   → EMPIRICALLY TESTED on the first corpus (`0e4cdcb`).

## 3. Citations repointed (from → to)

`e730d3b`:
- `TOOLS.md` Tier 1 drizzle note: `[[plate-solving-and-drizzle]]` → `docs/dead-ends.md`, drizzle entry
- `TOOLS.md` Tier 1 WBPP gaps: `[[objective-qa-defect-metrics]]` → the inline PSFSW proxy (§2.1)
- `TOOLS.md` Tier 2 ranking: `docs/plate-solving-and-drizzle.md` → `docs/dead-ends.md`, trailed-solve entries
- `TOOLS.md` Tier 5 BXT row: "See `docs/rc-astro-cli-linux.md`" → bootstrap prints the activation/flag-capture steps
- `TOOLS.md` Tier 6 NXT row: `(docs/rc-astro-cli-linux.md)` → "(the bootstrap prints the step)"
- `TOOLS.md` Tier 10 note: `[[objective-qa-defect-metrics]]` → dropped (sentence self-contained)
- `docs/dead-ends.md` drizzle entry: trailing `docs/plate-solving-and-drizzle.md` → dropped (entry self-contained)
- `scripts/setup/x86_bootstrap.sh` ASTAP comment → `docs/dead-ends.md` trailed-solve entry; rc-astro step 6 → "reconcile TOOLS.md"
- `docs/wide-field-untracked-registration.md` drizzle line → `dead-ends.md`, drizzle entry
- `docs/README.md`: 3 index entries removed; rules' example filenames → surviving files

`7a23dd9`:
- `TOOLS.md` class-3 definition: "see `docs/siril-pyscript-headless.md`" → the criterion stated inline (mechanism location, not provenance)
- `TOOLS.md` Tier 1 header: `docs/siril-stacking-workflow.md` → "verified against the Siril 1.4.4 tag source"
- `TOOLS.md` Tier 10: "See `docs/narrowband-star-neutral-options.md`" → BACKLOG:`star-neutral-colour`
- `TOOLS.md` cross-cutting: `docs/siril-pyscript-headless.md` → "the class-3 mechanism-location test above"
- `TOOLS.md` process rule: `docs/graxpert-3x-and-workflow-order.md` → its primary sources named + git history
- `docs/dead-ends.md` OIII entry: `docs/narrowband-star-neutral-options.md` → BACKLOG:`star-neutral-colour` + `TOOLS.md` Tier 10
- `scripts/stack/render_tier.sh` ORDER comment: `docs/graxpert-3x-and-workflow-order.md` part 2c → `TOOLS.md`, "The one process rule that changed everything"
- `docs/stacking-vs-official-pipelines.md` Sources: `docs/siril-stacking-workflow.md` → graduated into `TOOLS.md` Tier 1 (retired — git history)
- `docs/README.md`: 6 index entries removed

`2dd133a`:
- `TOOLS.md` Tier 1 Pick: `docs/synthetic-flats-and-bias.md` link → dropped (routes stated in place)
- `docs/dead-ends.md` sky-flat entry: `synthetic-flats-and-bias.md` → `scripts/stack/build_sky_flat.sh` gates + `TOOLS.md` Tier 1
- `docs/dead-ends.md` halo entry: `docs/july23-dew-and-corner-chroma.md` → git history (session archived)
- `docs/dead-ends.md` dew checklist line: `docs/july23-dew-and-corner-chroma.md` → detection method inline + the halo entry
- `README.md` setup-table row: `docs/x86-setup-and-install.md` → `scripts/setup/manifest.tsv` (see §5.1 — row rewritten beyond the bare link)
- `scripts/setup/x86_bootstrap.sh` header: `docs/x86-setup-and-install.md` → "per-tool sources in the manifest rows + git history"
- `docs/stacking-vs-official-pipelines.md` §D ICC line: `docs/july23-dew-and-corner-chroma.md` → the registry ICC entry
- `docs/ui-position-and-zero-state-report.md` line 4: brief link → "consumed work order, retired — git history"
- `docs/README.md`: 3 index entries removed

`d3ce14a` (inside the condensed test plan): Phase 0/2/3/5 pointers to
`x86-setup-and-install.md` / `siril-stacking-workflow.md` /
`plate-solving-and-drizzle.md` / `objective-qa-defect-metrics.md` → the
executed-outcomes table's records and BACKLOG slugs.

`0e4cdcb`: `TOOLS.md` sources tail: "per-topic primary citations live in
docs/" → survivors in docs/, retired ones in git history.

## 4. Before / after totals

- **docs/ directory**: 5,593 lines / 21 files → **3,214 lines / 9 files**
  (−2,379, −43%). Line counts: `wc -l docs/*.md`.
- **In-scope deep-dives**: 3,986 lines / 18 files → **1,650 lines / 5 files**
  (−59%): 13 retired (2,322 lines), 1 condensed (100 → 86), 4 kept (1,564).
- Out-of-scope survivors in docs/: `dead-ends.md` 1,172 → 1,174 (repoint
  edits), `README.md` 151 → 106, `pipeline-wide-field-untracked.md` 284
  (untouched).
- Operating-doc deltas from graduations/repoints: `TOOLS.md` 563 → 570;
  `README.md` (root) one row rewritten; `scripts` touched: `x86_bootstrap.sh`
  (3 comment lines), `render_tier.sh` (1 comment line).
- **After the §5 resolutions** (`20b3850`, `1f5fc6c`): docs/ **2,978 lines**
  (wide-field 622 → 385; stacking-vs +1 annotation line) — 5,593 → 2,978
  overall, −47%; in-scope deep-dives 3,986 → 1,414, −65%.

## 5. Open decisions — all three RESOLVED by the user (follow-up commits)

1. **Bootstrap header — RESOLVED (`20b3850`).** User: arm64 is retired, only
   the x86 rig exists — clean it up entirely. The header's "DRAFT, UNTESTED,
   targets a rig that does not exist yet" was replaced with the measured
   state: steps verified PIECEWISE during this rig's bring-up (every tool
   installed + driven; `manifest.tsv` the tracked inventory those installs
   recorded), with the one-shot from-scratch pass on a fresh machine named as
   the standing acceptance test (a step failing there is a bug in the script,
   per CLAUDE.md's rebuildable-from-tracked-files rule). The "draft" refusal
   message at the `uname -m` guard was fixed in the same commit. During the
   pass itself, the root `README.md` setup-table row had already dropped the
   same stale claim when its retirement-forced pointer rewrite landed
   (`2dd133a`) — flagged then, consistent now.
2. **wide-field-untracked-registration.md — AUDITED, condense WARRANTED,
   DONE (`1f5fc6c`): 622 → 385.** User: condense if the audit says so, don't
   invent problems, don't stop short. The audit found a real problem — a
   FIFTH drift instance this campaign surfaced: the file asserted
   "`--icc-type SRGB`, never `LIN_REC709`" and a 16-bit `savetif` chain
   diagram, while the shipped `run_undistort_pipeline.sh` strips the ICC tag
   and exports `LIN_REC709` on a `savetif32` float leg (verified in the
   script before editing). Corrected to the two-leg contract. Condense kept
   every measured table (seqtilt A/B + full depth, drift-axis stations, the
   A/B/C experiment, the SIP 65/128 px kill) and the theory; route-audit and
   production-trap prose deduplicated to one-line verdicts pointing at
   `TOOLS.md` Tier 2b / dead-ends / the script docstring, which carry them
   verbatim. Stale Status items superseded in place: the one-sided term →
   BACKLOG:`one-sided-band` (holds the newer july27/july31 state); the july14
   disk-bound frame-selection debt died with the session archive + the
   chain's cull machinery. All citing anchors (`CLAUDE.md`, `README.md` ×2,
   `TOOLS.md` Tier 2b, `lens_preflight.py`, `run_undistort_pipeline.sh`,
   dead-ends) still resolve; the index entry still describes the file.
3. **Archived-record paths in KEEP files — user delegated; DECIDED: paths
   stay** (`1f5fc6c`). They name the instrument records; records re-stage
   with a session and live in the archive + git history meanwhile — per-path
   "(archived)" annotations would rot the other way on re-stage. One
   clarifying annotation added at the single place a reader could mistake
   them for on-disk state: `stacking-vs-official-pipelines.md` §Sources
   (`datasets/july23/*` — session since archived). The condensed wide-field
   file annotates its own july14 record pointer inline.

## 6. Verification evidence (re-runnable)

**No dangling references to any retired file** — for each of the 13 retired
basenames, this sweep returns nothing outside this report and git internals:

```
for f in objective-qa-defect-metrics plate-solving-and-drizzle rc-astro-cli-linux \
         free-ai-tool-wave ui-position-and-zero-state-brief narrowband-star-neutral-options \
         siril-stacking-workflow siril-pyscript-headless siril-natives-and-trailed-solve \
         graxpert-3x-and-workflow-order synthetic-flats-and-bias x86-setup-and-install \
         july23-dew-and-corner-chroma; do
  grep -rn "$f" --include='*.md' --include='*.py' --include='*.sh' --include='*.html' \
       --include='*.ssf' --include='*.json' --include='*.tsv' . | grep -v DOCS_CLEANUP
done
# → no output (verified clean at HEAD 0e4cdcb)
```

**Index matches the surviving set** — indexed filenames == deep-dive files on
disk (README.md and dead-ends.md are operating files, not indexed deep-dives):

```
grep -oE '^\- \[[a-z0-9-]+\]\(([a-z0-9-]+\.md)\)' docs/README.md | sed -E 's/.*\((.*)\)/\1/' | sort
ls docs/*.md | xargs -n1 basename | grep -vE '^(README|dead-ends)\.md$' | sort
# → identical lists (diff empty): lunar-lucky-imaging, pipeline-wide-field-untracked,
#   stacking-vs-official-pipelines, ui-position-and-zero-state-report,
#   wide-field-untracked-registration, x86-empirical-test-plan
```

**Link check over surviving docs** — every `*.md` reference in `docs/*.md`
resolves, with four benign non-links: a bare "`.md`" (prose, not a link);
`INSPECTION.md` (a generated per-package artifact — `scripts/qa/judgment_package.py`);
`RUN_JULY31_FROM_RAWS_PROMPT.md` (the ui-report *describing* an already-deleted
prompt, not pointing at one); `scripting.md` (a file inside the external ImPPG
repo, named in a source citation).

**Tree clean**: `git status --short` empty after every commit of this pass.
