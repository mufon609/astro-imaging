# CLAUDE.md — operating manual for agents working in this repo

**Read order, every session:** (1) this file; (2) `README.md` — the
process contract (workflow mapping, review contract + standing audits,
per-set geometry, experiment discipline, north star); (3) `NOTES.md`
top to bottom — current truth ONLY: STATUS (approved recipe + byte-
reproduce command + expected numbers), design with each knob's measured
WHY, the DEAD-END registry (never re-attempt those), bandaid ledger,
acquisition checklist. Full history lives in `git log` (every commit
carries the NOTES of its time; approved recipes are git-tagged).
Volatile state (what is approved, open queue, disk-heavy artifacts) is
in NOTES STATUS — trust it over anything here.

## Environment (this rig)

- Siril 1.4.4 as a **user flatpak**, not on PATH:
  `flatpak run --command=siril-cli org.siril.Siril -d <workdir> -s <script>`
  The sandbox has home/host access but **its own private /tmp**: `.ssf`
  scripts MUST live under $HOME (repo `scripts/` or `<session>/work/`),
  never /tmp or a scratchpad.
- Kali linux arm64, 4 cores, 7.7 GB RAM, ~20-25 GB free disk. The disk
  is why intermediates are 16-bit with per-stage cleanup (quantization
  measured ≈18× below per-frame noise → ~+0.3% stack noise: negligible)
  and why big FITS get pruned once their numbers are recorded.
- Host python3: numpy + scipy + PIL, **no astropy** (equatorial→galactic
  is a fixed 3×3 in `scripts/astrometrics.py`), no rawpy.
- GraXpert 3.2 at `~/.local/bin/graxpert` (BGE + denoise only, no star
  removal). exiftool/exiv2 present. Outbound network works.
- StarNet2 ONNX weights at `~/.local/share/starnet/StarNet2_weights.onnx`
  (from the official Linux x64 CLI zip at download.starnetastro.com;
  license = personal astrophotography use, keep out of the repo) +
  its venv at `~/.local/share/starnet/venv` (onnxruntime aarch64).
  `scripts/starnet_sep.py` bootstraps the venv and errors loudly if
  the weights are missing.
- Plate solving: siril's internal solver cannot match this rig's
  ultra-wide trailed-star fields — use `scripts/solve_field.py` (blind
  astrometry.net from peak centroids; venv auto-bootstraps at
  `~/.local/share/astrometry-venv`; scale hint derives from the FITS
  header; the configured foreground is excluded from detection).
- Local Gaia catalogs at `~/.local/share/siril/siril_catalogues/`
  (astro + SPCC xpsamp chunks; siril settings already point there).
  SPCC needs the FULL cone of chunks — siril names the first missing
  one; a validated numpy cone-cover recipe is in NOTES. Re-download:
  zenodo 14692304 (astro) + 14738271 (chunks).

## Binding rules (the contract in README, distilled for agents)

- **One knob per experiment**, control bracketed, hypothesis
  pre-registered in NOTES BEFORE the run. A measurement that kills a
  hypothesis becomes a dead-end entry WITH ITS NUMBERS before anything
  else is tried.
- **The gate never loosens** (`bg_qa.py --sky-scope` thresholds; scope
  changes need explicit user ratification). Corridor/star-shell/clip0
  metrics are REPORTED or WARN context — never silently gated.
- **Aesthetic changes need the user's eyes** on judgment panels before
  any bake; objective fixes with pass/fail metrics may commit. Compare
  renders in LIKE encodings (a q92 4:2:0 jpg hides chroma a PNG shows).
- **After ANY script change, byte-verify the approved recipe** (all
  artifacts `cmp`-identical) or document exactly why it legitimately
  changed and get the new render approved.
- **No session/stream/ladder tags in script comments** — plain,
  standalone descriptions with their measured numbers; provenance
  narrative lives in NOTES/git only.
- **Maintain NOTES.md in its refactored shape**: update STATUS /
  design / knob-provenance / dead-ends / ledger IN PLACE; never append
  chronological session narrative.
- **New datasets get `config_<set>.json` / derived geometry** (WCS
  corridor, foreground mask) — never set-03-specific script patches; a
  configless set must degrade loudly, not inherit silently.
- Background long siril/render runs and keep working; preserve stacks
  per experiment (`cp` to tagged names); track disk.

## North star (the user's standing goal)

A pipeline that constantly audits its images and process steps so that
eventually ANY dataset can be dropped into a session dir and be
properly judged and processed to its best honest outcome. Every
divergence from the standard workflow is a measured adaptation carrying
its removal condition; finals as close to lossless as possible; and
acquisition quality (the checklist in NOTES) outranks processing —
never bandaid what photons must fix.
