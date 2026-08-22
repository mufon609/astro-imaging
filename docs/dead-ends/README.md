# dead-ends.md refactor workspace — phase 1, organize only

`docs/dead-ends.md` (4,653 lines, one flat registry section) remains the LIVE
registry and is UNTOUCHED. This directory is the proposed reorganization of its
content into topic files, built to be verifiable: every content line moved
VERBATIM into exactly one file, in original order, and `split.py` proves the
files reassemble byte-identical to the original. Nothing here is yet a
replacement — the merge (replace vs index vs discard) is a separate decision
with the owner, constrained by the "Merge constraints" section below.

Phase 1 = grouping ONLY. Not done here, by design: no wording changes, no
entry merges/deletions/updates, no fixing of "above"/"below" cross-references,
no re-ordering inside a group (original order kept). That is phase 2, entry by
entry, with this grouping as its work surface.

## Phase 2 status

Phase 2 works file by file: every entry audited against the artifact it
describes (the contract's four standing states), then removed only on the
owner-ratified conjunction (solved AND no longer worth knowing), merged,
updated, or revised — with every re-measurement stamped to the commit it was
taken at. A file that has had its pass is RELEASED in `split.py`'s
`PHASE2_RELEASED` set: maintained in place from then on, never regenerated,
excluded from the byte check.

| file | status |
|---|---|
| `verification-traps.md` | DONE, audited at `614ad33`: 0 removed, 0 merged, 1 entry split into 3, 12 revisions — full dispositions in this file's phase-2 commit |
| all other files | phase 1 (verbatim; regenerated + byte-checked by `split.py`) |

Why these groups: the original's seven implicit sections were already
stage-shaped EXCEPT `QA / scope`, which held 2,586 of 4,653 lines (56%) and
mixed four different subjects — star-shape/optics investigation method, WCS and
solve consumption, lens-model findings, and session process/evidence
discipline that is not astrophotography at all. The split aligns the pipeline
files with `TOOLS.md`'s tier taxonomy (Tier 0 acquisition → Tier 12 export,
Tier L lunar) and gives the cross-cutting discipline content its own files
instead of a catch-all.

## The files (pipeline order, then cross-cutting)

| file | scope | content lines | blocks |
|---|---|---|---|
| `00-registry-contract.md` | how entries are read/cited/written/deleted: evidence classes, SUBJECT axis, recording-rate + deletion rules, entry-standing states | 132 | 1 |
| `terminology-dust.md` | the "dust" ban and the four measured senses | 71 | 1 |
| `acquisition-checklist.md` | the acquisition checklist + LUNAR class block | 109 | 1 |
| `intake-frame-qa.md` | frame QA, culling, drift/mount instruments | 29 | 3 |
| `calibration-flats.md` | synthetic sky flats, darks, masters, flat-window policy | 650 | 10 |
| `background-extraction.md` | BGE: subsky degrees, GraXpert, coverage-crop order | 124 | 7 |
| `stretch-colour-judgment.md` | stretch, colour/chroma, SPCC-NB, judgment surfaces | 163 | 11 |
| `separation-deconv-psf.md` | star separation, deconvolution, PSF homogenisation/field-variable PSF | 168 | 5 |
| `plate-solving-wcs.md` | solver routes, xylists, union solves, `--max-stars`, SIP/CTYPE, matrix forms | 231 | 8 |
| `registration-distortion.md` | wide-field untracked registration + lens models, darktable/lensfun, ICC legs | 372 | 15 |
| `stacking-compose.md` | weights, rejection, walking noise, drizzle, groups route, sub-stack compose/union | 432 | 13 |
| `lunar-planetary.md` | planetary registrations: selection, quality, DFT aliasing | 62 | 4 |
| `star-shape-optics.md` | the star-shape/PSF/optics measurement family: spin-2, exponents, azimuthal traps, drift bearing | 453 | 19 |
| `siril-behaviors.md` | tool silent behaviours: clipping, persisted prefs, parsing/coordinate conventions, SPCC segfault | 265 | 13 |
| `measurement-discipline.md` | comparison crops, floors, reproducibility, controls, statistics choice | 192 | 10 |
| `verification-traps.md` | checks/search instruments that lie: cannot-fail checks, truncated views, shell/git/grep traps | 578 | 13 |
| `evidence-provenance.md` | records, claims, provenance, identity, multi-session epistemics | 622 | 12 |

Two content kinds, deliberately separated: the pipeline files (rows 3–13) hold
astrophotography dead-ends a session reads when working that stage; the
cross-cutting files (rows 14–17) hold discipline that applies to every
session, whatever the stage. `00-registry-contract.md` governs both.

## Assignment rule, and the review list it produces

Each top-level block went whole to ONE file, chosen by the PRIMARY SUBJECT its
own headline names. Blocks were never split, even where a tail changes
subject — splitting an entry is a phase-2 content decision. Entries whose body
carries a real second subject are flagged here as the phase-2 review list
(slugs are `manifest.tsv`'s):

- `four-corner-box-metric` → calibration-flats (also measurement-discipline)
- `sip-not-lens-model` → registration-distortion (also plate-solving-wcs)
- `aug06-edge-deficit-dead` → registration-distortion (also star-shape-optics — the three-level ladder cites it)
- `registration-comparison-traps` → registration-distortion (also measurement-discipline; holds the numbered trap 1/2/3 list `CLAUDE.md` cites as "trap 3")
- `twopass-reference-null` → measurement-discipline (also registration-distortion)
- `drift-window-contiguous-run` → intake-frame-qa (also measurement-discipline)
- `gitlog-no-time` → verification-traps (attribution/hedging tail → evidence-provenance)
- `log-regex-interface` → verification-traps (findstar tool facts → siril-behaviors)
- `compose-bit-reproducible` → measurement-discipline (route property → stacking-compose)
- `bgnoise-denoiser-judging` → stretch-colour-judgment (also measurement-discipline)
- `crop-y-origin-mirror` → siril-behaviors (also measurement-discipline)
- `dateobs-substack-epoch` → stacking-compose (also evidence-provenance)
- `frame-counter-wrap-order` → stacking-compose (basename-reuse tail → evidence-provenance)
- `findstar-dual-purpose` → star-shape-optics (makepsf half → separation-deconv-psf)
- `siril-top-down-frame` → siril-behaviors (consumers live in star-shape-optics)
- `standalone-sip-warp` → registration-distortion (also plate-solving-wcs, stacking-compose)
- `gui-selection-state` → lunar-planetary (generalises to ANY failed GUI registration → siril-behaviors)
- `spcc-sigsegv-database` → siril-behaviors (also `CLAUDE.md` Environment, SPCC prerequisites)

## Facts landed after the pin (phase-2 inputs)

- The one-sided band on the 52-member union is ATTRIBUTED member-borne — the
  compose is exonerated. Record `datasets/aug09/smear_work/rho_march.json`;
  register row + BACKLOG `compose-homography-smear` update in `db2a230`. The
  pinned registry text pre-dates that attribution, so the phase-2 pass over
  `registration-distortion.md` / `stacking-compose.md` and the
  one-sided-band mentions must reconcile against it.

## Where the original sections went

| original section (lines) | destinations (blocks) |
|---|---|
| preamble + meta (1–132) | 00-registry-contract 1 |
| Terminology (133–203) | terminology-dust 1 |
| Gain / flat (204–975) | calibration-flats 10, siril-behaviors 2, stacking-compose 1, evidence-provenance 1 |
| Background (976–1108) | background-extraction 7, siril-behaviors 1 |
| Stretch / colour (1109–1182) | stretch-colour-judgment 6 |
| Separation (1183–1194) | separation-deconv-psf 2 |
| Detection / solve / registration (1195–1826) | registration-distortion 8, stacking-compose 7, lunar-planetary 4, plate-solving-wcs 3, intake-frame-qa 3, separation-deconv-psf 2, siril-behaviors 1 |
| record-schema meta block (1827–1849) | evidence-provenance 1 |
| Tool state / plumbing (1850–1958) | siril-behaviors 6 |
| QA / scope (1959–4544) | star-shape-optics 19, verification-traps 13, evidence-provenance 10, measurement-discipline 10, registration-distortion 7, stacking-compose 5, plate-solving-wcs 5, stretch-colour-judgment 5, siril-behaviors 3 |
| Acquisition checklist (4545–4653) | acquisition-checklist 1 |

Original section-header LINES ride with the first following block:
`**Detection / solve / registration:**` sits atop `intake-frame-qa.md` and
`**QA / scope:**` atop `measurement-discipline.md` although those sections
dissolved — phase 2 replaces the headers. The doc title + `## Dead-end
registry` header are in `00-registry-contract.md`.

## Mechanics and verification

`manifest.tsv` is the authority: one row per top-level block (146 rows),
`start` line + destination + slug; a block ends where the next begins.
`split.py` validates every start is a real block start, regenerates all 17
files, then re-reads them from disk and reassembles the blocks in manifest
order. Measured output of the run that produced these files:

```
source: dead-ends.md  4653 lines  sha256 613d2fcb527707bc3ce9202e8d9445baa5db81fe6c405cd3bda7635cd29cd979
blocks: 146   files: 17
leftover content lines after reassembly: 0
reconstruction byte-identical to dead-ends.md: True
```

The sha256 pins the source state this split was derived from. Any edit to
`docs/dead-ends.md` invalidates the manifest's line numbers — re-run
`split.py` (it fails loudly on drift via the block-start validation and the
byte comparison; re-derive the manifest against the new state if it does).
Files released to phase 2 (`PHASE2_RELEASED` in `split.py`) are never
regenerated and are excluded from the byte check — the check then proves the
remaining files still carry their original spans verbatim.
`run_guards.sh` with this directory present: 24 passed, 0 failed.

## Merge constraints (inputs to the later decision, measured)

- 140 files outside the registry cite `dead-ends` — ~83 tracked dataset
  records, ~35 scripts, ~10 docs, plus `CLAUDE.md`/`README.md`/`TOOLS.md`/
  `BACKLOG.md`/`MEMORY.md` — nearly all by the PATH `docs/dead-ends.md` or by
  quoting an entry TITLE. The path must keep resolving: the merge either
  leaves an index at `docs/dead-ends.md` pointing here, or rewrites the path
  everywhere (records are frozen evidence — rewriting them is not an option),
  so the index form is the realistic one.
- Section-name references ("under 'QA / scope'" etc.) exist ONLY inside the
  registry itself: 12 internal, 0 elsewhere in tracked md/py/sh. The split
  strands those 12 (plus ~25 relative "entry above/below" references) across
  file boundaries — phase 2 rewrites them; until then this README + the
  manifest are the resolver.
- `CLAUDE.md` (owner's file) names `docs/dead-ends.md` in the read order and
  in the binding rule "maintain the dead-end registry IN PLACE" — the merge
  needs the owner's wording update there; nothing in this directory changes
  that file.
- While both the original and this split exist, every registry claim is
  DOUBLE-HOMED. The single-homing discipline means the merge must be a
  REPLACE (original becomes the index the moment the split goes live), never
  a long-lived duplicate. Guards are currently unaffected (24/24 green,
  scoped to code), but any future records sweep counting claim homes will
  read this directory as duplication — one more reason phase 2 should not
  linger.
