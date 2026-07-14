# MEMORY.md — collaboration context + residual lessons (transferable)

**Why this file exists.** Claude's auto-memory lives machine-local
(`~/.claude/…/memory/`) and does NOT transfer when the repo moves to the x86
desktop. This file carries the durable **collaboration context** (who the
user is, how they judge and work) and the **residual lessons** that don't
have a natural home in the technical/process docs — so they travel with the
repo. It supersedes the machine-local auto-memory for the transfer.

Where knowledge is already saved (don't duplicate it here — go read it):
- Binding rules + environment → `CLAUDE.md`
- Reset plan, target architecture, **dead-end registry**, acquisition
  checklist → `REDESIGN.md`
- The tier-by-tier **tool audit** (2026 landscape) → `TOOLS.md`
- Process/review/acceptance contract → `README.md`
- Per-dataset state model → `datasets/README.md`
- Full history (pre-reset chain, old NOTES.md) → git, the `checkpoint` commit

Only what is NOT in those lives below.

## The ethos: nothing is final until empirically tested

Codified as a binding rule in `CLAUDE.md`. A mechanism analysis / doc reading
/ source comparison is a **hypothesis**, not a verified fact — say so and
name the test that would settle it. Across the rig migration this is sharp:
**every arm-era finding is a hypothesis on the desktop until re-measured
there.** Live example — the solve verification below.

### Solve verification (provisional finding, 2026-07)
Siril 1.4 native `platesolve -localasnet` was **mechanism-verified** (Siril
docs + our source + rig command help) to: replace `solve_field.py` for
ROUND-STAR data, but NOT the trailed/ultra-wide class — native feeds
astrometry.net Siril's own PSF `findstar`, the detection our dead-end says
fails on trails (ours feeds trail-robust peak centroids). Mitigation to test:
`setfindstar -relax=on`. **Not empirically confirmed** — image data was
deleted and this is the arm rig. Full detail + the x86 test = `TOOLS.md`
Tier 2. Keep `solve_field.py` as the trailed-field tool until the x86 test says otherwise.

## Who the user is & how they work

- Runs the astro pipeline as a serious, professional-bar project; expects a
  high polish bar (lean docs; resolved-defect narrative compresses to
  outcome + numbers + a git pointer).
- **Decisive and autonomy-favoring** — has explicitly said "stop asking."
  Prefers action over deliberation once intent is clear. Often **extends
  scope class-generally** ("this is class-general — audit the rest of the
  pipeline for the same mistake").
- **Scraps throwaway platforms rather than bandaid them** — plans rig
  migrations deliberately (arm64 base → x86 production), and will hard-reset
  a repo to its durable core rather than polish disposable scaffolding, while
  keeping the intellectual capital (the measurement harness + the dead-end
  lessons).
- Works in **long sessions** with a handoff pattern: a fresh session first
  audits the repo + the previous work independently, then the backlog /
  redesign needs, before implementing. Quick approvals, with reasons.
- **Expects killed hypotheses reported as plainly as wins** — no
  "fixed/final/matched/close" language, ever.

## How the user judges (the review contract's human side)

The mechanism is in `README.md` (review contract) + `CLAUDE.md` (binding
rules). What's NOT there — the personal context + the formative corrections
that must never be re-learned the hard way:

- **The user personally judges all aesthetics**, from FULL-FRAME LOSSLESS
  finals (PNG16 + PNG8) opened independently in their own viewers — never
  crops, composited panels, or any lossy surface. Compare LIKE encodings.
- They have been **burned by premature commits and multi-knob churn**, hence
  the discipline. The corrections, verbatim, in order:
  - "you need to get this right before saving a flawed recipe" — nothing
    judged by eye commits before the user confirms the visual result.
  - "stop throwing stuff at the wall" — one parameter per experiment,
    bracket the control, hypothesis BEFORE the run.
  - "i need full uncompressed images ... i can't use this cropped compressed
    images and charts" — the judgment surface is whole-frame lossless files,
    nothing else.
  - "looks worse ... what kind of a joke 'test' did it pass?" — a
    gate-PASS never stands in for the look; inspect the SUMMED full-frame
    impression, and when candidate defects stack up, say it looks worse in
    the notes instead of hedging with numbers.
  - "the midst of learn-nothing, try-everything" — the named failure mode:
    guess-and-check knob-thrashing on throwaway scripts with victory
    language. Never repeat it.

## Reference-driven quality (the methodology)

When a dataset ships a reference finish (the data author's own output), that
is the quality bar. The method that works (and the one that failed):
- **Reproduce the PRO's ACTUAL process with THEIR OWN open tool on our
  data** — not our chain reapplied. Learn the specific mechanism our pipeline
  lacks, then mature the pipeline from it. (Concrete win: the SHO O3 sphere =
  a star-colour-neutral balance that boosts O3, which SPCC erases — learned
  by driving the author's Nightlight, now in the dead-end registry.)
- **Separate reproducible process from manual artistry** — a published
  "gold" is often the author's manual GIMP/curves finish (an aesthetic hue
  choice), not part of the reproducible tool output; don't chase the manual
  part as if it were the process.
- Compare at LIKE scale + orientation, and verify orientation parity
  NUMERICALLY (an eyeball same-orientation call was wrong once; corpus
  authors publish sky-true, our renders are camera-native/mirrored).
- **Failure to avoid:** two judgment rounds were burned tuning toward an
  unstudied reference whose maker's recipe was published in the dataset's own
  repo. Study the reference + recover the documented recipe BEFORE tuning.

## Portable tooling gotchas (carry to the desktop)

Traps measured the hard way; the portable ones (re-verify arm-specifics on
x86 — shell, /tmp, flatpak may differ):
- **PIL silently truncates 16-bit RGB PNGs to 8-bit** (mode 'RGB', uint8, no
  warning). Use the repo's PNG16 writer/decoder (`astrometrics.write_png16` /
  the reader in `judgment_package.py`), never a bare `Image.save`.
- **FITS header cards are exactly 80 bytes** — one longer COMMENT shifts the
  card grid and every reader rejects the file. `compose.py` fails loud on it.
- **Siril normalizes float FITS with values > 1 to [0,1] on import**
  ("Normalizing input data") — ADU-scale float masters feed as-is.
- **siril `autoghs`**: SP = shadowsclip·sigma from the MEDIAN, D = amount,
  default B=13 (very SP-focused), HP=0.7, clipmode=rgbblend. A single autoghs
  from linear CANNOT replace the MTF autostretch (gain concentrates at SP≈sky)
  — use it as a FINISHING pass after autostretch.
- **Backgrounded `python … | tee log` shows nothing until exit** (python
  buffers stdout when piped) — track long runs by artifact files or `ps`, not
  the log tail.
- **Watcher loops must not `pgrep -f <pattern>`** where the pattern appears
  in the watcher's own command line (it matches itself, never exits) — watch a
  PID / output-file condition / `pgrep -x`.
- **sirilpy pyscript runs HEADLESS** via an `.ssf` wrapper (`requires 1.4.0`
  + `pyscript foo.py`) — proven; siril-cli runs `.ssf` only.
- Arm-base only (verify/retire on x86): the harness shell was zsh (unquoted
  `$var` does NOT word-split — use `for a b c in …` or `${=var}`); `/tmp` was
  a small tmpfs; Siril ran as a flatpak with its own private `/tmp`.
