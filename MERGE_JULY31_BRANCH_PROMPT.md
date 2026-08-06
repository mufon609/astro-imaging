# Prompt for a fresh session — land the july31 branch on main

Third prompt from the july31 run, and the one that must go FIRST: the other two
(`AUDIT_FLAT_GRADIENT_PROMPT.md`, `AUDIT_PIPELINE_INTEGRITY_PROMPT.md`) live on a
branch that is not on main and does not merge cleanly.

Paste everything below the line.

---

# The situation

`fix/lens-guard-and-flat-odd-component` is pushed, complete and self-consistent.
It is **71 commits ahead** of its merge-base and has never been on main. `main`
has moved **57 commits** since that base, on largely unrelated work (JWST Jupiter,
lunar july26, july27) plus several infrastructure fixes that **collide with the
branch**.

**How the divergence went unnoticed, because it is the transferable part:** the
session that produced the branch checked `git merge-base --is-ancestor main HEAD`
against a **stale local `main` ref** — one that had not been fetched for weeks —
got "yes", and reported a clean fast-forward. It then fast-forwarded local `main`
and attempted a push, which the remote correctly rejected. Local `main` was reset
to `origin/main` and nothing was lost. **Ancestry checked against an unfetched ref
answers a question about the past.** `git fetch` before any merge-base reasoning.

## Measured, so you do not have to re-derive it

| | |
|---|---|
| merge-base | `243b0a6` |
| branch ahead | **71** commits (37 pre-existing from `fix/calibration-bitdepth-and-flat-gradient`, 34 from the july31 session) |
| `origin/main` ahead | **57** commits |
| already upstream (`git cherry`) | **zero** — every branch commit is `+`; there are no patch-level duplicates to drop |
| merge conflicts | **19 files, 39 hunks** |

Worst files: `build_sky_flat.sh` (6 hunks), `run_undistort_groups.sh` (4),
`run_pipeline.sh` (4), `BACKLOG.md` (4), `run_set_chain.sh` (3).

# MERGE — do not rebase

The user's words were "rebase onto origin/main", but the mechanics argue against
it and you should say so before proceeding:

- **The branch is already pushed.** A rebase rewrites it and needs a force-push.
- **37 of the 71 commits are another author's**, also already pushed. Rebasing
  rewrites their history too.
- **Rebase resolves conflicts up to 71 times; a merge resolves them once.** With
  39 hunks that is the whole difference between an afternoon and a week.

`git merge origin/main` into the branch, resolve once, then fast-forward main.
If the user specifically wants linear history, say what it costs and let them choose.

# The collisions — classified, because most are NOT duplicates

This is the part worth reading before touching anything. Four of the five look
like duplicate work and only one is.

### 1. Sky-flat non-radial detection — COMPLEMENTARY, keep both

- **main `5f04dfb`** adds **corner asymmetry**: the opposite-corner RATIO.
  Vignetting is radial, so all four corners sit at the same radius and a
  vignetting-only flat reads 1.00; excess is non-radial (decentering, sensor tilt).
- **branch `4b235d4`** adds **`edge_dipole_x` / `edge_dipole_y`** at box 80 /
  margin 2 — `baseline_guard.py`'s own convention — and compares left-right
  against top-bottom. Vignetting contributes equally to both axes, so an excess
  of |x| over |y| is non-radial by construction.

Different geometry, different null, different defect. main's catches a diagonal
decentering term; the branch's catches the horizon-fixed sky gradient a sky flat
absorbs, and it is the instrument `BACKLOG:calibration-evidence` records as
missing. **Keep both.** They are two readings of one question and the flat's QA
record has room for both.

### 2. Siril concurrency — COMPLEMENTARY, but see §3, this one has teeth

- **main `487274c`** adds a **flock-serialized shared invoker**
  (`scripts/stack/siril_invoke.sh`) closing the measured flatpak race, across
  30 files, plus a guard `check_siril_invoke.sh` that enforces it.
- **branch `63108c7`** adds a **pid lock on the undistort work dir**, which
  prevents a *different* failure: two builders share `work/undistort_<set>` and
  the second `rm -rf`s the first's tree mid-flight.

Serializing siril calls does not stop a second builder deleting a work dir.
**Keep both.**

### 3. THE ACTUAL INTEGRATION WORK — the branch predates the shared invoker

**This is the one that will bite, and a naive conflict resolution will miss it.**

main re-plumbed every siril call through `siril_invoke.sh` and added
`check_siril_invoke.sh` to enforce it. The branch edits
`build_sky_flat.sh`, `run_undistort_pipeline.sh`, `run_undistort_groups.sh`,
`run_set_chain.sh`, `finish_render.sh`, `lens_preflight.py` and `render_tier.sh`
— and **every one of its additions still calls `flatpak run --command=siril-cli`
directly.**

A textually-correct merge therefore produces code that **fails main's own guard**.
Resolving the conflict is not enough; the branch's *new* siril calls must be
re-pointed at the shared invoker. Specifically at least:

- `build_sky_flat.sh` — the new edge-geometry `stat` loop (box 80 / margin 2)
- `run_undistort_pipeline.sh` — nothing new, but confirm the `dt_last.log` change
  did not detach an existing call
- `lens_preflight.py` — the `--selftest` path does not invoke siril; the
  `prove_correction` path does

**Run `bash scripts/stack/check_siril_invoke.sh` as the acceptance test.** It is
main's guard and it will tell you when you are done.

### 4. Disk model — LIKELY SUPERSEDED, verify before keeping

main has `052c21d` ("routing message quoted the stale 231 MB/frame") and
`f4957d0` ("disk model back to 32-bit"). The branch has `ffe93ba`, deriving the
sky-flat budget from the set's own geometry via a `sky_flat_frame_mib` wrapper
(93 MiB/frame measured, against a hardcoded 98). Read both. The branch's is a
derivation and main's are corrections to constants — the derivation probably
subsumes them, but **check main did not also derive it** before assuming.

### 5. Groups route — main may already answer a branch question

main `9b0974c`: *"the architecture A/B returns NULL — the groups route does not
cause the one-sided band (item 7)"*, measured on july27. The branch's route work
concluded a narrow, replicated, **magnitude-unestablished** improvement at one
drift-axis station, explicitly gated on a rebuild-repeat floor that was never
measured. These may be consistent (different defect, different session) or main's
NULL may bound the branch's claim. **Read `datasets/july31/experiments.jsonl`
before merging BACKLOG.md**, and reconcile the two accounts rather than letting
whichever text wins the conflict stand.

# What must not be lost

The branch's substantive content, in case a conflict silently drops it:

- **`lens_preflight.py --selftest`** — the optics assertion could not fail (it
  read a `<distortion/>` element out of its own marker comment). Fixed at source,
  and the selftest **falsifies itself**: it neutralises the masking in-process,
  asserts the incident reproduces, restores. Verify it still passes post-merge.
- **`install_lens_model.sh`** no longer writes a verbatim element into the marker
  (the decoy), only coefficients.
- **Derived group size** with the GESD **dwell floor**
  (`G >= ceil(max_dwell/0.30)`), and `--plan` exercising the guards that can
  refuse a run.
- **`--route=` / `--group=`** operator overrides through the chain and the session
  driver.
- **`star_black`** as a resolved render knob; **SPCC sensor-match status**.
- **Four registry entries** in `docs/dead-ends.md`: checks-that-cannot-fail, the
  running-bash-script trap, load-dependent readings, and route-conditional
  ratified decisions.
- **The two audit prompts** at the repo root — they are the next session's work
  and they are not on main.

# Acceptance

Post-merge, all of these must pass. They are cheap and several were run by hand
throughout the branch's development:

```
bash scripts/stack/check_siril_invoke.sh      # main's guard — the integration test
./scripts/stack/check_bitdepth.sh
bash scripts/stack/check_stack_rejection.sh
./scripts/stack/check_calibrate.sh
python3 scripts/stack/lens_preflight.py --selftest
python3 scripts/lib/fingerprint.py --selftest
bash -n on every modified .sh
```

`BACKLOG:guards-and-ci` is open precisely because nothing runs these
automatically. Landing this merge without running them would be the exact failure
that item describes.

# Rules

- **`git fetch` first, and check ancestry against `origin/main`, never a local
  ref.** That error is what produced this prompt.
- Resolve on the **merits**, not on which side committed later. Four of the five
  collisions are complementary; defaulting to "take theirs" or "take mine" loses
  a real instrument either way.
- The branch is pushed and is the only copy of 34 commits. **Do not force-push it**
  until the merge is verified.
- A conflict resolution that compiles is not a resolution. Run the guards.
