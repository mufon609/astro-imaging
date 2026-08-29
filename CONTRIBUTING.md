# Contributing — how to work in this repo

`README.md` says what this is and where to start; this file says how to work
here. Every rule below is a POINTER to the section that binds it — nothing is
restated, so nothing here can drift from its home. (README = what and where to
start, CONTRIBUTING = how to contribute is the GitHub convention:
docs.github.com, "Setting guidelines for repository contributors".)

## Set up the rig (in this order; each step names its verify command)

1. Git hooks, from tracked source: `scripts/setup/install_hooks.sh`; verify
   `scripts/setup/install_hooks.sh --check`. The pre-push hook runs the guards.
2. Tools: `scripts/setup/x86_bootstrap.sh` (a dry run — prints the plan and any
   missing sha256 pin), then `--go` (x86-64 only; fail-closed on an unpinned
   download). It installs the Siril flatpak, the `/opt` neural tools, ASTAP and
   its wide star databases, astrometry.net + its indexes, the `/opt/astro-venv`
   python libs, the local Gaia astrometric catalogue, the SPCC sensor database
   and the Siril config patches. The
   inventory of record is `scripts/setup/manifest.tsv`; verify
   `scripts/qa/check_manifest_verify.sh` (runs every row's verify command).
3. darktable styles + the fitted lens model:
   `scripts/darktable/install_styles.sh <darktable-configdir>` and
   `scripts/darktable/install_lens_model.sh <session-dir> <set>`; re-run both
   after every `lensfun-update-data` (it wipes the user DB); verify
   `scripts/darktable/verify_lens_card.py --session <dir> --set <name>`.
   The why of each: `CLAUDE.md` "Environment".
4. SPCC, per field: `scripts/calibrate/spcc_cone.py <solved_wcs.fit> --fetch`
   downloads the Gaia photometric chunks a field needs. SPCC has THREE
   machine-local prerequisites, and a missing sensor DATABASE makes Siril
   SIGSEGV silently (exit 139) — the long form is `CLAUDE.md` "Environment".
5. Prove the tree: `scripts/qa/run_guards.sh` (every guard + every data-free
   selftest; `--list` prints the roster). GREEN verifies WIRING, not output.

## The rules (one line each; the named section is the authority)

- The bright line — in-house code never reads, transforms or gates the
  deliverable's pixels and never reimplements a tool's measurement; deciding
  FROM the tools' numbers is the pipeline's job: `CLAUDE.md` "What this repo IS"
  and "WHERE THE GATE ACTUALLY IS".
- One knob per experiment, control bracketed, hypothesis pre-registered before
  the run: `CLAUDE.md` "Binding rules"; `README.md` "The experiment discipline".
- Read the dead-end registry before proposing ANY experiment: `docs/dead-ends.md`
  (the index) → `docs/dead-ends/00-registry-contract.md` → the stage files your
  work touches.
- Every acceptance measure ships with a positive control, and measures never
  loosen: `CLAUDE.md` "Binding rules".
- The judgment surface is the full-frame 16-bit PNG only; no compression
  anywhere; every generated `.ssf` pins `setcompress 0` and `set32bits`:
  `README.md` "Data integrity"; `scripts/stack/check_bitdepth.sh` enforces it.
- A result is a WIN, a clean NULL, or needs-eyes — never "fixed / final /
  matched / close": `README.md` "The experiment discipline".
- Every divergence from the standard workflow carries a removal condition AND a
  row in `BACKLOG.md` `removal-conditions`; `scripts/qa/check_removal_conditions.sh`.
- Style: no session tags, no chronological narrative, no bare dates except
  register data (a ratification stamp, a last-checked stamp): `CLAUDE.md`
  "Binding rules".
- `CLAUDE.md` is the OWNER's file: read it every session; never edit it —
  propose a diff.

## Committing (the protocol is `CLAUDE.md` "PARALLEL SESSIONS")

- Before committing ANY file: `git diff --numstat -- <file>`, then read every
  hunk; PASTE the measured numstat into the commit message, and name the file.
- Never `git add -A`; `git add -p` your own hunks when a peer's work shares
  the file.
- Anything on the BUILD PATH waits for a running chain to finish (`PIPEREV` is
  stamped from HEAD at build time); records-only commits may land any time.
- The pre-push hook runs `scripts/qa/run_guards.sh`; a RED guard is a broken
  pin, never a reason for `--no-verify`.

## Where a result is written (one home each)

| what | home |
|---|---|
| open work, a decision the owner holds, a divergence's removal condition | `BACKLOG.md`, by slug (``BACKLOG:`<slug>` ``), never by number |
| a mechanism that kills a route, with its numbers | the stage file under `docs/dead-ends/`; cite it as FILE + ENTRY HEADLINE, never as the index |
| a tuning experiment and its verdict | `datasets/<session>/<set>/experiments.jsonl` (`datasets/README.md`) |
| a per-set measurement | `datasets/<session>/<set>/<tool>_work/*.json` — the instrument, the exact command, the tool's own numbers |
| a stage's technical WHY | the kept script's own docstring, updated in place |
| a cited research deep-dive | `docs/<topic>.md` + its row in `docs/README.md` |
| a tool fact or option | `TOOLS.md`, by tier |

Citation rule going forward: a registry citation is `docs/dead-ends/<file>.md`
plus the entry headline. Older citations that name an entry against the index
resolve via the note at the top of `docs/dead-ends.md`; `scripts/qa/check_doc_pointers.py`
fails the guards on any backticked path, BACKLOG slug or relative link that
does not resolve.
