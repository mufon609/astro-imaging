# docs/dead-ends/ — the dead-end registry

The registry's content files — one per pipeline stage plus the cross-cutting
disciplines. The index (file map, citation rule) is
[`../dead-ends.md`](../dead-ends.md); [`00-registry-contract.md`]
(00-registry-contract.md) governs how entries are read, cited, written and
deleted. Entries are maintained IN PLACE, in the stage file they belong to.

## Provenance

This directory replaced the single-file registry (4,653 lines) in two
recorded operations, both in this path's git history:
- **The split** (commit `f8cffb8`): every top-level block moved verbatim to
  one topic file; `manifest.tsv` is the map (its line numbers refer to the
  pre-split file, pinned at sha256 `613d2fcb…` — recover it with
  `git log -- docs/dead-ends.md`), and the split was verified by byte-exact
  reconstruction (`split.py`, retired with the refactor — in git history).
- **The declutter** (ten per-file commits, `ae4fdf9`…`1bc5c22`): every entry
  audited against the tree, duplicates / stale claims / fixed-and-implemented
  scaffolding removed, every re-measurement stamped to the commit it was
  taken at; per-file dispositions are in those commit messages
  (`git log --oneline -- docs/dead-ends/`). Registry content 4,653 → 2,749
  lines.

Pre-compression forms of every entry are in git; nothing was lost.

## Pending, out of this directory's scope

- BACKLOG:`native-solve-and-sip`'s CLOSED bullet asserts *"`register -disto=`
  is a SHARED-solution facility — Siril's design assumes ONE optical state
  per sequence"* — both halves corrected in this registry
  (`registration-distortion.md`, the standalone-SIP-warp entry: `master` is
  UNDETERMINED with its probe specified and unrun; the design claim is
  FALSE). A surviving site of the corrected over-generalisation, awaiting a
  BACKLOG-scoped edit.
