# Siril `pyscript` ecosystem: headless viability + tool-vs-hand-roll — deep dive

- **Question / scope** — Two linked questions that gate a whole class of tools:
  (1) Can the Siril community `pyscript` ecosystem (VeraLux, SyQon, Cosmic Clarity,
  StarNet, RC-Astro wrappers) run **headless on Linux** (no display / Xvfb)?
  (2) The REDESIGN **open philosophy question**: is numpy processing inside a
  `sirilpy` pyscript a genuine **TOOL** (adoptable like Nightlight) or **someone
  else's hand-rolled numpy in a wrapper** (rejected by the same rule that removed
  ours)? The answer decides whether the VeraLux/SyQon class is in-bounds at all.
- **Context** — 2026-07-14. Siril 1.4.x stable / 1.5.0-dev; Python scripting is
  officially **EXPERIMENTAL** (introduced 1.3.5-dev); **sirilpy API 1.1.13**.
  Target rig: x86-64 Kali, i7-14gen, 32 GB, **no GPU**, **headless** via
  `siril-cli`. Builds on [[siril-tool-ecosystem]] and [[siril-natives-and-trailed-solve]].

## Findings

### The repository & distribution
- Community scripts live at **`gitlab.com/free-astro/siril-scripts`** (project
  "FA / siril-scripts"), synced into Siril via **Preferences → Scripts → "Enable
  the siril-scripts online repository"** / **Scripts → Get Scripts** — Siril clones
  a local copy, lists scripts by category (Preprocessing / Processing / utility /
  core), you tick the ones you want. Contribution is fork → MR; scripts are
  versioned through MR titles carrying semver (e.g. *VeraLux Nox v1.0.0*, *SCUNet
  Denoise v2.0.0*). Both `.ssf` command scripts and `.py` pyscripts ship from the
  same repo. Root folders: `RC-Astro/`, `SyQon/`, `VeraLux/`, `core/`,
  `preprocessing/`, `processing/`, `utility/`.
- **Naming correction:** there is **no "Seti" folder.** Seti Astro (Franklin Marek)
  ships his *own standalone* suite (Cosmic Clarity / Seti Astro Suite Pro); in this
  repo his algorithm appears only as `processing/Statistical_Stretch.py`, a **port
  by Cyril Richard** (Siril's lead dev), and the `CosmicClarity_*.py` scripts are
  *driver* scripts for the external Cosmic Clarity binaries. So "Seti pyscripts" in
  our older notes conflates a standalone suite, one ported algorithm, and a set of
  external-binary drivers.

### The decisive split — TWO architectures by where the pixel mechanism lives
Reading the actual sources, the ecosystem is **not monolithic**. It splits cleanly:

**Class 2 — genuine external-tool orchestrators** (the pyscript is a thin,
headless-capable *driver*; the pixel mechanism is a real independent binary invoked
by `subprocess`):
- `processing/StarNet.py` → `subprocess` on the external **StarNet++ 2.5** binary.
- `RC-Astro/BlurXTerminator.py` / `NoiseXTerminator.py` / `StarXTerminator.py` →
  wrap the external RC-Astro `rc-astro` CLI.
- `processing/CosmicClarity_*.py` (Denoise/Sharpen/Darkstar/Superres/…) and
  `GraXpert-AI.py` → drive the external Cosmic Clarity / GraXpert binaries. (Siril's
  own docs cite `CosmicClarity_denoise.py` as the reference pyscript example.)
- **These are the SAME category as our `solve_field.py` driving astrometry.net** —
  thin orchestration over a real tool. Doctrine-consistent to adopt.

**Class 1 — self-contained numpy/scipy/torch image processors** (Siril is reduced
to pixel transport + a PyQt6 window; the mechanism is the script's own math libs).
All pull pixels with `get_image_pixeldata()` (often inside `image_lock()`), compute
the transform in-script, and push back with `set_image_pixeldata(...)` — they do
**not** call `siril.cmd()` for the pixel work:
- **VeraLux Silentium** (denoise) — `pywt.swt2/iswt2` stationary-wavelet denoise +
  `scipy.signal.convolve2d` + `scipy.ndimage`.
- **VeraLux HyperMetric** (stretch) — hand-implemented numpy `arcsinh` hyperbolic.
- **VeraLux Nox** (gradient removal, MR !180, 2026-01-17) — `scipy.sparse`
  Poisson-equation solver + IRLS + `opencv`.
- **SyQon Prism** (denoise/restore) — **PyTorch NAFNet** tiled inference + numpy
  IHS stretch, all in-memory.
- **Statistical_Stretch** (Seti Astro algorithm, Cyril Richard's port) — numpy.
- Same pattern for `SCUNet_Denoise.py`, `DeepSNR.py`, most of the 9-script VeraLux
  suite.
- **Running VeraLux Silentium IS running a numpy denoiser.** The mechanism is
  numpy/scipy/pywt/torch, not a compiled tool with standing independent of that code.

### Headless viability on Linux (no GPU, `siril-cli`)
- **Headless-first authoring is the documented baseline, not a hack.** The official
  "Hello, Siril!" example is fully headless (`import sirilpy`,
  `SirilInterface().connect()`, no PyQt6). sirilpy 1.1.13 is explicitly
  headless-aware: `is_cli()`, and `open_dialog()` **raises** headless,
  `get_siril_display_iccprofile()`/`undo_save_state()` return **None** headless.
- **Launch mechanism (matches our proven rig recipe):** `siril-cli` runs only
  `.ssf`; wrap the python entry in an `.ssf` that calls
  **`pyscript [-async] scriptname.py [script_argv]`** (a top-of-file
  `requires <version>` line is mandatory — a raw `.py` fed to `siril-cli` errors
  *"The 'requires' command is missing"*; the `.ssf` supplies it). `script_argv`
  passes `--no-gpu`, tile sizes, etc. Headless transports: `-s file.ssf`, `-s -`
  (stdin), `-p/-r/-w` named pipes, `-d` workdir.
- **BUT the community scripts split again on headless-usability:**
  - **GUI-mandatory, no headless guard** — unconditionally build a `QApplication` +
    `.show()` + `exec()` with **no `is_cli()` check and no arg vector** (confirmed:
    VeraLux Silentium, VeraLux HyperMetric; pattern across most of the VeraLux
    suite). On a headless box they need a display; under `QT_QPA_PLATFORM=offscreen`
    / Xvfb they *might* import, but being **slider-interactive with no parameter
    arguments they cannot be driven non-interactively** → **not usable for headless
    batch automation.** No Siril-specific Xvfb-success report was found.
  - **Dual-mode (GUI + real CLI path)** — `argparse` / `is_cli()` short-circuits
    before any window: `processing/StarNet.py`, `processing/Statistical_Stretch.py`,
    `SyQon/Prism.py` (`--tile-size … --no-gpu`; GUI only if no args). Siril ships an
    official "GUI + args" template for exactly this. **These run headless.**
- **Net:** Class-2 drivers and Class-1 *dual-mode* scripts run headless via the
  `.ssf`→`pyscript … [args]` wrapper; Class-1 *GUI-mandatory* scripts (most of
  VeraLux) do **not** headlessly automate as written, Xvfb or not.

### GUI toolkit note
New GUI scripts must use **PyQt6**; `tksiril`/tkinter is deprecated (Wayland), GTK
GUIs are rejected from the repo. (One outlier: SyQon `Prism.py` uses **PySide6**.)
Practical consequence for us: headless use never depends on the toolkit — it depends
on whether the script has an `is_cli()`/args path *before* it constructs a window.

## Resolution of the philosophy question (applying CLAUDE.md's existing bright line)
CLAUDE.md's rule is not about *provenance*, it is about *mechanism location*:
"the repo's own code only EXAMINES … every pixel-rewriting op drives a real tool …
UNLESS no available tool provides the mechanism, documented as a sanctioned
alternative with a removal condition." Applying that test to the two classes:

- **Class 2 (subprocess-drives-a-binary) = a TOOL.** In-bounds, adopt freely — it
  is orchestration of an industry binary, identical in kind to `solve_field.py`.
- **Class 1 (numpy/torch-inside) = the same thing our own removed corings were.**
  The mechanism is numpy. It is admissible **only** as a *sanctioned alternative
  with a removal condition* (the astrometry.net precedent) — i.e. when no compiled
  tool provides the mechanism — logged as such, and **never relabeled "a tool" for
  free** just because it is a versioned, MR-reviewed, named-author script in the
  official Free-Astro repo. Provenance (even Cyril Richard porting Statistical_
  Stretch) makes it a *published third-party numpy processor*, which is more than an
  ad-hoc in-repo hand-roll — but it is **not** equivalent to Siril/GraXpert/StarNet-
  the-binary, and the mechanism test is what decides in-bounds vs escape-hatch.

This **refines REDESIGN's working recommendation.** The old cut was "official repo &
reputationally-vouched = tool; a script we'd fork/edit = not." The sharper,
mechanism-based cut is: **subprocess-to-a-compiled-tool = tool; numpy-inside =
escape-hatch-with-removal-condition, regardless of repo or author.** The old cut
would wrongly bless VeraLux Silentium (official, vouched) as "a tool"; the mechanism
cut correctly treats it as a numpy denoiser you may sanction but must log with a
removal condition (e.g. "until NoiseXTerminator/Siril-native provides the chroma
mechanism").

## Sources
- Script files / repo mechanism — https://siril.readthedocs.io/en/stable/scripts/Script-files.html
- Python scripts (architecture) — https://siril.readthedocs.io/en/latest/scripts/Python-scripts.html
- sirilpy API 1.1.13 (`is_cli`, pixeldata, headless behaviors) — https://siril.readthedocs.io/en/latest/Python-API.html
- Authors' guide (PyQt6 mandate, tkinter deprecated, GTK rejected) — https://siril.readthedocs.io/en/latest/scripts/authors.html
- "Hello, Siril!" headless example — https://siril.readthedocs.io/en/latest/scripts/python_hello_siril.html
- GUI / GUI+args templates — https://siril.readthedocs.io/en/latest/scripts/python_gui_template.html
- Commands ref (`pyscript [-async] scriptname.py [argv]`) — https://siril.readthedocs.io/en/latest/Commands.html
- Headless mode (`-s`, `-s -`, pipes, `-d`) — https://siril.readthedocs.io/en/latest/Headless.html
- Repo (read via GitLab REST API + raw blobs): `VeraLux/VeraLux_Silentium.py`,
  `VeraLux/VeraLux_HyperMetric_Stretch.py`, `SyQon/Prism.py`, `processing/StarNet.py`,
  `processing/Statistical_Stretch.py` — https://gitlab.com/free-astro/siril-scripts
- MR !180 VeraLux Nox v1.0.0 — https://gitlab.com/free-astro/siril-scripts/-/merge_requests/180
- "Can sirilpy python scripts run via siril-cli?" (Graham_Smith, 2025-10-24) — https://discuss.pixls.us/t/can-sirilpy-python-scripts-run-via-siril-cli/53685
- Qt headless (`QT_QPA_PLATFORM=offscreen`, `xvfb-run`) — general Qt/pytest-qt docs

## Verdict / recommendation
- **Adopt Class-2 pyscript drivers freely** (RC-Astro, Cosmic Clarity, GraXpert,
  StarNet wrappers) — they are tool-orchestration and run headless.
- **Treat Class-1 numpy-inside scripts as escape-hatch-only.** If a Class-1 script
  fills a *genuine mechanism gap with no compiled tool* (e.g. VeraLux Silentium as a
  chroma-noise option while NoiseXTerminator is unlicensed), it may be **sanctioned
  with an explicit removal condition** — never adopted as a first-class "tool," and
  preferring a compiled tool (Siril-native / NXT / GraXpert) whenever one exists.
- **Headless planning:** do not count on the VeraLux GUI-mandatory scripts in a
  headless pipeline — they are slider-only. If a Class-1 mechanism is wanted
  headless, prefer the dual-mode ones (Statistical_Stretch, Prism `--no-gpu`) or
  reimplement the driver headless-first from the sirilpy examples.

## Status
**PROVISIONAL (source-verified architecture; doctrine call).** Script architectures
and headless mechanisms are primary-verified from Siril docs + repo source. The
philosophy *resolution* is an application of CLAUDE.md's existing mechanism test to
those facts — a doctrine refinement the user can override, not an empirical result.
Two items to verify empirically on x86: (a) whether any class-(A) GUI script can in
fact be driven under Xvfb/offscreen (expected: no useful parameter control); (b) the
headless-run teething errors reported for `Statistical_Stretch.py` via `.ssf`.

## Graduation
- **REDESIGN "Open philosophy question"** — RESOLVE it: replace the provenance-based
  working recommendation with the **mechanism-location** criterion (subprocess-to-a-
  binary = tool; numpy-inside = sanctioned-alternative-with-removal-condition).
- **TOOLS.md "three tool CLASSES"** — correct Class 3: split the pyscript ecosystem
  into Class-2 drivers (tools) vs Class-1 numpy-inside (escape-hatch); fix the
  blanket "🖥 needs Xvfb" implication — most VeraLux GUI-mandatory scripts are **not
  headless-drivable at all**, while dual-mode/driver scripts run under `siril-cli`.
- **TOOLS.md "FREE but DISPLAY-gated"** — correct: VeraLux GUI-mandatory ≠ "usable
  via Xvfb"; and mark VeraLux/SyQon-Prism/SCUNet/DeepSNR as numpy-inside (escape-
  hatch), Cosmic Clarity/RC-Astro/StarNet wrappers as Class-2 drivers.
- **MEMORY [[siril-tool-ecosystem]]** — add the Class-1/Class-2 split, the headless
  reality, and the "Seti = standalone, not a repo folder" correction.
- Done in the commit that follows the TOOLS/REDESIGN graduations.
