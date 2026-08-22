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

Phase 2 works file by file, and its point is DECLUTTERING (owner-directed):
remove duplicate info (in-file and cross-file — one home per claim), remove
clearly stale info, and remove the investigation notes around any problem that
is since FIXED and properly implemented — once a tool or mechanism ships, the
figuring-out archaeology is no longer load-bearing; the durable
rule/mechanism/tool-fact stays, compact, with its grounding numbers. Fact-check
along the way (re-measurements stamped to the commit they were taken at), but
the bias is removal. Pre-compression forms are never lost: git holds them, and
the live `docs/dead-ends.md` is untouched until the merge. A file that has had
its pass is RELEASED in `split.py`'s `PHASE2_RELEASED` set: maintained in
place from then on, never regenerated, excluded from the byte check.

| file | status |
|---|---|
| `registration-distortion.md` | DONE, audited + decluttered at `9957337`: 15 → 15 entries, 383 → ~290 file lines; the route-fight corrections kept as the BACKLOG-named mechanism home (the item's ordered-work section says "mechanisms + quotes in docs/dead-ends.md — not restated here") with the `-disto=master` UNDETERMINED status verified still accurate (the item's one open probe is `-localasnet`, not master); a surviving site of the corrected over-generalisation found in BACKLOG's closed bullet and logged above (out of scope to fix here); dtstyle/ICC entries compressed to measured mechanism + `CLAUDE.md` Environment as the operational home; trap-1/2/3 entry kept structurally intact (five external citation sites); per-set-models resolution stated with the `lens_models.json` authority (verified on disk, 4 keys); stale CFA-register-row bookkeeping and correction-journey narrative cut |
| `stacking-compose.md` | DONE, audited + decluttered at `9957337`: 13 → 13 entries, 443 → ~300 file lines; the mosaic entry reconciled against the shipped state (astrometric route SHIPPED + owner-PASSED with -2pass demoted to the regression arm, reference pinning RESOLVED via setref — both verified in BACKLOG:`compose-homography-smear`'s ordered-work section; the surviving band's member-borne attribution from `db2a230` stated with the compose exonerated; the "measured case for SWarp" wording superseded — the SWarp trial never ran, no SIP reader) and its 125 lines → ~85 across two entries' worth of content; fixed-and-implemented compressions (frame_order.py wrap fix, observer_frame_diversity epoch derivation, member_separation rebuild + user-ratified threshold removal → combine-contract §5); reference-route scope narrative flattened to per-route facts; inbound identities preserved (the ref-probe canvas/north/B-G numbers evidence-provenance cites, the optical-state-boundary material star-shape-optics points at) |
| `star-shape-optics.md` | DONE, audited + decluttered at `9957337`: 19 → 19 entries, 464 → ~290 file lines; the LIVE wrong number fixed (the χ²/dof "35.6 → ~1.1" pairing survived here after its register correction — replaced with the true within-binning pairs 35.60→1.81 / 40.95→1.57, a measured instance of the claim-survives-other-sites class); in-file duplicate cut (B113's trap note duplicated the dual-purpose entry); `db2a230` reconciliation applied as preface status (raw-frame term stands pipeline-exonerated, union carrier = member +x-edge — BACKLOG:`one-sided-band` is the status home); correction-journey narrative flattened to resolved readings (drift-direction, one-sided eliminations); string-search bookkeeping and attributions cut; fit-vs-moment sign test verified still unrun; register row cited by name not number |
| `calibration-flats.md` | DONE, audited + decluttered at `9957337`: 10 blocks → 11 entries (the alt-az bake-in block split at its transfer-function seam), 661 → ~360 file lines; the `sky × V` defect is OPEN so most dead ends here stay live — cuts are the 3.11%/241σ caveat de-duplicated to one home (the absolute-measurement dead end; six homes outside the registry verified consistent), the desky entry's stale "baseline.json never built" corrected (guard shipped, 13 baselines), correction-of-this-entry meta and lineage/string-search bookkeeping removed, instrument-provenance narrative dropped; status pointers to BACKLOG:`calibration-evidence` and BACKLOG:`per-group-flat-at-the-combine`; ramp-slope candidate verified still unswapped |
| `evidence-provenance.md` | DONE, audited + decluttered at `9957337`: 12 blocks → 15 entries (the 214-line second-session block split into four: priors/agreement, replication tests, capability-surface asymmetry, delivery-gap class), 633 → ~300 file lines; duplicates removed (the widening table — home: `00-registry-contract.md`'s SUBJECT axis; the md5-DATE companion — homes: this file's digest entry + `stacking-compose.md`'s probe; tilt/inspector probe rule — home: `CLAUDE.md`); superseded numbers dropped for the register-row census (solve counts, replay-key coverage); implemented guidance compressed to rule + pointer (DATASUM identity → `stamp_headers.sh`; composite stamp tuple → BACKLOG item carries status); incident forensics and sweep bookkeeping cut; cut safety pre-checked: 0 external references |
| `verification-traps.md` | DONE, audited + decluttered at `614ad33`: 15 → 14 entries (kernel-bugs fixture folded into check-cannot-fail as its analytic-value corollary; mechanism notes live in `kappa_transfer.py` itself), duplicates removed (the readability-limit punchline ×2, the decoration line ×2, the proximity-lesson paragraph duplicating `evidence-provenance.md`'s entry), fixed-and-implemented scaffolding cut (sip_tpv incident detail, regex-gate blow-by-blow, `^-[^-]` contract decision now closed, correction-of-this-entry meta, session attributions); cut safety pre-checked: 0 external references to any removed material |
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

- SURVIVING-SITE finding, out of this refactor's scope to fix (BACKLOG is not
  this workspace's file): BACKLOG:`native-solve-and-sip`'s CLOSED bullet
  asserts *"`register -disto=` is a SHARED-solution facility — Siril's design
  assumes ONE optical state per sequence"* — the registry corrected both
  halves (`-disto=` is three values with `master` UNDETERMINED, probe
  specified and unrun; the design claim is FALSE — `seqplatesolve` +
  `seqapplyreg` is the per-image operation and the shipped default). The
  registry's careful form is kept (`registration-distortion.md`, the
  standalone-SIP-warp entry); the BACKLOG bullet is a surviving site of the
  corrected over-generalisation.

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
