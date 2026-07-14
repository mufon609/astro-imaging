# x86-64 Kali setup & reproducible tool install — deep dive

- **Question / scope** — the "x86 tool inventory — DO THIS FIRST" (`TOOLS.md`): for every
  tool in TOOLS.md, what is the **best install method on x86-64 Kali** (Debian-based,
  headless, **no GPU**) for a **reproducible, version-pinned** setup — exact command,
  source, integrity (sha256/signature), install path, deps, and Kali-vs-Ubuntu
  gotchas — plus a drafted `scripts/setup/` **bootstrap** that installs → pins →
  verifies → emits a manifest. This is the environment-founding step of the rebuild.
- **Context** — 2026-07-14. Target: x86-64 Kali (rolling, glibc 2.42), i7-14gen,
  32 GB, 1 TB NVMe, **no GPU**, headless. Overlapping facts were verified first-hand
  on the arm box (Siril flatpak, GraXpert pipx, apt availability) where arch-agnostic;
  x86-only specifics are primary-sourced. Builds on all seven tool deep-dives.

## Findings — a four-layer install, each layer chosen for isolation

**Layer A — apt (system, signed):** `flatpak`, `pipx`, `astrometry.net` +
`astrometry-data-tycho2`, `libssl-dev`, a modern `golang`, optionally `xvfb`.
Integrity via Debian/Kali signatures. **PEP 668** is enforced (externally-managed) —
never `pip install` into system Python; venv/pipx/flatpak/`/opt` only.

**Layer B — flatpak (isolated runtime):** Siril, pinned by OSTree commit — immune to
glibc drift (bundled runtime).

**Layer C — project venv** (`.venv` or `/opt/astro-venv`): `numpy scipy pillow
astropy`, pinned in `requirements.txt` (ideally `--require-hashes`). pipx CLIs (e.g.
GraXpert alpha) live in their own pipx venvs.

**Layer D — pinned `/opt/<tool>-<version>/` self-contained binaries** (never touch
system Python).

### Per-tool install matrix (primary-verified sources; pin every version)
| Tool | Layer / method | Source (pinned) | Integrity | Install path | Headless verify |
|---|---|---|---|---|---|
| **Siril 1.4.4** | B · flatpak | flathub `org.siril.Siril` (id `org.free_astro.siril` is EOL) | Flathub GPG + OSTree commit | flatpak (sandbox) | `flatpak run --command=siril-cli org.siril.Siril -v` |
| **GraXpert** | D (stable zip) *or* C (pipx alpha) | GH `3.0.2/graxpert-linux-amd64.zip` (stable, BGE+denoise) · *or* `pipx install --pip-args=--pre "graxpert==3.2.0a2"` (alpha, adds deconv models) | GH asset digest / PyPI sha256 | `/opt/graxpert-3.0.2/` | `GraXpert-linux -h` |
| **StarNet2 2.5.3** | D · zip | `download.starnetastro.com/starnet2_linux_2.5.3-0208_ORT_x64_cli.zip` (142 MB) | **sha256 `101c724a…c29d99` (published)** | `/opt/starnet2-2.5.3/` | `starnet2 --version` |
| **DeepSNR 1.2.1** | D · zip | `download.deepsnrastro.com/deepsnr_linux_1.2.1-0112_ORT_x64_cli.zip` (232 MB) | **sha256 `05218b05…c17f9` (published)** | `/opt/deepsnr-1.2.1/` | `deepsnr -h` |
| **Cosmic Clarity** | D · frozen bins | GH `setiastro/cosmicclarity` "Linux" tag (2025-03-29) + model assets | per-asset sha256 (GH API) | `/opt/cosmicclarity-2025.03.29/` | `SetiAstroCosmicClarity --help` |
| **ASTAP** | D · CLI zip + DB | SF `astap_command-line_version_Linux_amd64.zip` (2026.06.29) + **wide-field DBs `W08` (276 kB) + `G05` (101 MB) for our ultra-wide class** (`d50` ~850 MB is the *narrow*-field DB; D-series caps at 6° — [[plate-solving-and-drizzle]]) | SF SHA-1/MD5 (compute own sha256) | `/opt/astap` | `astap_cli --version` (barebone = headless) |
| **astrometry.net** | A · apt + data | `apt install astrometry.net astrometry-data-tycho2` — **4100-series (Tycho-2) = the wide-field set** (scales 7–19, >1°) → `/usr/share/astrometry/` | apt signature | system | `solve-field --help` |
| **rc-astro** (BXT/NXT/SXT) | D · vendor installer, **license-gated** | authenticated account-page installer → binary `rc-astro` on PATH | none public (compute own) | (installer-chosen; **path TBD**) | `rc-astro bxt` (prints help + license) |
| **numpy/scipy/pillow/astropy** | C · venv | `requirements.txt` pinned (`astropy==8.0.1`, all manylinux wheels) | pip `--require-hashes` | `.venv` | `python -c "import astropy"` |
| **Nightlight 0.2.6** | D · `go build` | `git clone --branch v0.2.6 mlnoga/nightlight` → `go build ./cmd/nightlight` (**Go ≥1.20** despite go.mod=1.17) | `go.sum` / GOSUMDB | `/opt/nightlight-0.2.6/` | `nightlight version` |
| pipx / xvfb | A · apt | `apt install pipx xvfb` (xvfb only for GUI pyscripts — avoid) | apt | system | `pipx --version` |

### The specifics that bite (carry into the manifest notes)
- **Siril flatpak sandbox** has its own **private `/tmp`** → `.ssf`/`.py` must live under
  `$HOME` (repo `scripts/` or `<session>/work/`), never `/tmp`. The sandbox also can't
  reach `/opt` tools via Siril's *internal* "call StarNet/GraXpert" menu without
  `flatpak override --filesystem=host` — **not a blocker here** (we orchestrate each
  tool as its own headless step, not through Siril's menu).
- **GraXpert two channels diverge:** PyPI `3.2.0a2` (alpha, deconv) vs GitHub stable
  `3.0.2` zip (BGE+denoise). For a *stable reproducible* base use the 3.0.2 zip; pipx
  the alpha only if the deconv models are wanted (pre-release, bug #243). `-gpu false`
  for CPU; models auto-download (~tens of MB) to the GraXpert user-data dir — pin
  `-ai_version` + pre-cache online for offline runs.
- **StarNet/DeepSNR/Cosmic Clarity take TIFF/PNG, not FITS** — convert via Siril in the
  chain. StarNet & DeepSNR ship a **published sha256** (verify it); Cosmic Clarity is a
  rolling GH tag (pin by date + per-asset digest).
- **rc-astro — the "Ubuntu 22.04+" requirement is a glibc FLOOR, not a desktop/distro
  requirement.** RC-Astro states Linux reqs as glibc versions (its PixInsight build asks
  "Ubuntu 18.04 / glibc 2.27" — same pattern), so the standalone CLI's "Ubuntu 22.04"
  decodes to **glibc ≥ 2.35 + GLIBCXX ≥ 3.4.30 + AVX/AVX2/SSE**. It is a headless CLI
  with no GTK/GNOME libs → **the desktop environment is irrelevant** (do NOT switch DE to
  "mimic Ubuntu" — a bandaid; Kali-GNOME is still Kali, same glibc). **Kali has glibc 2.42
  + GLIBCXX 3.4.35 (verified) → clears the floor by forward-compatibility on any desktop.**
  Real check = **`ldd <rc-astro> && rc-astro --version`** on the rig (not the OS label);
  a missing *specific* lib → `apt install <it>`, never a DE change. No GPU → **`--device
  cpu`** (older `--engine` name is legacy). `--activate <email> <key>` once online +
  `download-models`, then offline. Installer is **license-gated** → the bootstrap can't
  auto-fetch it; it prints the manual steps.
- **astrometry.net index for OUR class:** the **4100-series (Tycho-2)** is the
  wide-field set (index quads should be 10–100% of image width); the widest Debian
  sub-packages are `astrometry-data-tycho2-10-19` (60′–2000′). `solve_field.py`
  bootstraps its own venv but uses these apt-installed indexes + `solve-field`.
- **PEP 668** (Kali externally-managed): venv/pipx only. **Go** is absent by default
  (`apt install golang` or pin a tarball). astropy is **absent on arm, present on x86**
  (venv `astropy==8.0.1`, or `apt python3-astropy`).

### The manifest + verification pass (the durable RECORD)
The bootstrap emits `scripts/setup/manifest.tsv` — one row per tool:
`tool | version | source_url | sha256 | install_path | verify_cmd | notes`. This is the
record the harness versions (and the seed for the new CLAUDE.md environment section).
It ends with a **verification pass** — each tool must answer `--version`/`--help` (and
model files present) or the setup **fails loud** (the repo's "degrade loudly, not
inherit silently" rule). Every download is **sha256-checked before install**; a
mismatch aborts.

## Companion artifact
`scripts/setup/x86_bootstrap.sh` (+ `requirements.txt`) — a drafted bootstrap that
encodes the matrix above: pinned versions/URLs/sha256 as top-of-file variables, the
four layers as idempotent steps, sha256-verified downloads, the license-gated rc-astro
step as printed manual instructions, then the manifest + verification pass. It **defaults
to a dry-run plan** and **refuses to run unless `uname -m` is `x86_64`** and `--go` is
passed — so it cannot execute on the arm box (or interfere with anything). It is
**UNTESTED** until run on the real x86 rig.

## Sources
- Siril — https://flathub.org/apps/org.siril.Siril · https://siril.readthedocs.io/en/stable/Headless.html · https://packages.debian.org/sid/siril
- GraXpert — https://pypi.org/pypi/graxpert/json · https://github.com/Steffenhir/GraXpert/releases
- StarNet — https://starnetastro.com/cli-tools/starnet/ · https://starnetastro.com/documentation/starnet/command-line-tool/
- DeepSNR — https://starnetastro.com/cli-tools/deepsnr/
- Cosmic Clarity — https://github.com/setiastro/cosmicclarity/releases · https://www.setiastro.com/cosmic-clarity
- ASTAP — https://www.hnsky.org/astap.htm · https://sourceforge.net/projects/astap-program/files/
- astrometry.net — https://astrometry.net/doc/readme.html · https://data.astrometry.net/ · https://packages.debian.org/sid/astrometry-data-tycho2
- rc-astro — https://www.rc-astro.com/stand-alone-rc-astro-tools/ (+ `docs/rc-astro-cli-linux.md` for the v0.9.9 `--device` flag)
- Python/astropy — https://docs.astropy.org/en/stable/install.html · Kali PEP 668 https://www.kali.org/docs/general-use/python3-external-packages/
- Nightlight — https://github.com/mlnoga/nightlight

## Verdict / recommendation
- **Install by isolation layer:** apt (signed) → flatpak Siril → project venv →
  pinned `/opt` self-contained binaries. Never system pip. Record every source +
  version + sha256 in the manifest; end with the verification pass.
- **The free stack is the cleanly-and-reproducibly-installable part** (Siril flatpak,
  StarNet/DeepSNR checksummed zips, ASTAP + astrometry.net apt, GraXpert) — once the TODO
  checksums are filled, and UNTESTED until run. **rc-astro is the only license-gated /
  manual step**, and the one glibc-compat unknown to smoke-test.
- **Prefer GraXpert 3.0.2 stable zip** for the reproducible base; add the 3.2.0a2 alpha
  (pipx) only if deconv is wanted, knowing it's pre-release.

## Status
**PROVISIONAL.** The install methods, URLs, and the two published checksums are
PRIMARY-VERIFIED; overlapping facts (Siril flatpak 1.4.4 vs apt 1.4.2, GraXpert pipx,
apt availability of ASTAP/astrometry.net) were verified first-hand on the arm box. The
**bootstrap script is UNTESTED** — it targets a rig that doesn't exist yet. Acceptance
test = run it on the x86 rig, confirm every verification-pass command exits 0, resolve
the flagged unknowns (rc-astro `/opt` path + Kali-glibc smoke test; GraXpert Linux
model-cache dir; StarNet/DeepSNR/rc-astro actually run CPU-only at usable wall-clock).

## Graduation
- **`TOOLS.md` — the x86 tool inventory** — point it at this deep-dive +
  `scripts/setup/x86_bootstrap.sh` as the concrete inventory/bootstrap; the manifest
  seeds the new CLAUDE.md environment section.
- **`scripts/setup/`** — the drafted bootstrap + requirements are the artifact (marked
  untested).
- No TOOLS.md tier change (this is install mechanics, not a tool choice).
