#!/usr/bin/env bash
# x86_bootstrap.sh — reproducible tool install for the x86-64 Kali production rig.
#
# STATUS: DRAFT, UNTESTED. It targets a rig that does not exist yet (the current
# base rig is arm64). Every step is primary-sourced (see docs/x86-setup-and-install.md)
# but NONE has been run. Treat as a plan-in-code, not a proven installer.
#
# WHAT IT DOES: installs the toolkit in four isolation layers (apt / flatpak / venv /
# pinned /opt binaries), sha256-verifies every download, prints the license-gated
# rc-astro steps for you to do by hand, emits a manifest, then runs a verification
# pass. Never uses system `pip` (Kali PEP 668).
#
# SAFETY: refuses to run unless `uname -m` == x86_64 AND `--go` is passed. Default is
# a dry-run that prints the plan. So it cannot execute on the arm box or touch anything.
#
# USAGE:
#   ./x86_bootstrap.sh            # dry-run: print the plan
#   ./x86_bootstrap.sh --go       # actually install (x86-64 only)
#   ./x86_bootstrap.sh --go --skip-data   # skip the big ASTAP D50 DB + index files
set -euo pipefail

# ---------------------------------------------------------------------------
# Pinned versions / sources / checksums — the manifest's source of truth.
# Update deliberately; a bump is a change to record, not a silent `latest`.
# ---------------------------------------------------------------------------
OPT=/opt
VENV="${ASTRO_VENV:-/opt/astro-venv}"

SIRIL_FLATPAK_ID="org.siril.Siril"                       # Flathub; 1.4.4 (apt only 1.4.2)

STARNET_VER="2.5.3-0208"
STARNET_URL="https://download.starnetastro.com/starnet2_linux_${STARNET_VER}_ORT_x64_cli.zip"
STARNET_SHA="101c724a50328cbeb1b3aedb74e18a81894100b3cf668de6b5006d0a46c29d99"   # published

DEEPSNR_VER="1.2.1-0112"
DEEPSNR_URL="https://download.deepsnrastro.com/deepsnr_linux_${DEEPSNR_VER}_ORT_x64_cli.zip"
DEEPSNR_SHA="05218b05460d3ff280d40bb97c9460f9464a8ebcbf08907d07085e61c97c17f9"   # published

# GraXpert: stable 3.0.2 zip (BGE+denoise) is the reproducible base. The 3.2.0a2 alpha
# (deconv models, pre-release, bug #243) is optional via pipx --pre.
GRAXPERT_VER="3.0.2"
GRAXPERT_URL="https://github.com/Steffenhir/GraXpert/releases/download/${GRAXPERT_VER}/graxpert-linux-amd64.zip"
GRAXPERT_SHA=""      # TODO: fill from the GitHub asset digest before running

# ASTAP CLI (no-GTK) + star DB(s). For the ULTRA-WIDE/trailed class use the WIDE DBs
# W08 (276 kB, 20-80 deg) + G05 (101 MB, 3-20 deg) — the D-series caps at 6 deg and
# G17/H17 are deprecated (docs/plate-solving-and-drizzle.md). For NARROW fields swap in
# d50_star_database.deb (~850 MB) instead.
ASTAP_URL="https://sourceforge.net/projects/astap-program/files/linux_installer/astap_command-line_version_Linux_amd64.zip/download"
ASTAP_DB_W08_URL="https://sourceforge.net/projects/astap-program/files/star_databases/w08_star_database.deb/download"
ASTAP_DB_G05_URL="https://sourceforge.net/projects/astap-program/files/star_databases/g05_star_database.deb/download"
# SourceForge publishes SHA-1/MD5 only — compute + record sha256 yourself:
ASTAP_SHA=""; ASTAP_DB_W08_SHA=""; ASTAP_DB_G05_SHA=""   # TODO: compute-your-own

# Cosmic Clarity: rolling GitHub "Linux" tag (2025-03-29), frozen self-contained bins.
COSMIC_TAG="Linux"   # pin by asset digest + the date below
COSMIC_DATE="2025-03-29"

# Nightlight: dormant Go tool (v0.2.6, 2023); go build from tag. Go >= 1.20 needed.
NIGHTLIGHT_VER="v0.2.6"

# ---------------------------------------------------------------------------
DRY=1; DO_DATA=1
for a in "$@"; do case "$a" in
  --go) DRY=0 ;;
  --skip-data) DO_DATA=0 ;;
  -h|--help) sed -n '2,20p' "$0"; exit 0 ;;
  *) echo "unknown arg: $a" >&2; exit 2 ;;
esac; done

MANIFEST="$(cd "$(dirname "$0")" && pwd)/manifest.tsv"
log(){ printf '\033[1;34m[bootstrap]\033[0m %s\n' "$*"; }
run(){ if [[ $DRY -eq 1 ]]; then printf '  (plan) %s\n' "$*"; else eval "$@"; fi; }
manifest(){ [[ $DRY -eq 1 ]] || printf '%s\t%s\t%s\t%s\t%s\t%s\t%s\n' "$@" >>"$MANIFEST"; }

# fetch <url> <dest> <sha256|""> : download then verify sha256 (fail loud on mismatch)
fetch(){ local url="$1" dest="$2" sha="${3:-}"
  run "curl -fL --retry 3 -o '$dest' '$url'"
  if [[ -n "$sha" && $DRY -eq 0 ]]; then
    echo "$sha  $dest" | sha256sum -c - || { echo "SHA256 MISMATCH: $dest" >&2; exit 1; }
  elif [[ -z "$sha" ]]; then
    log "WARN: no pinned sha256 for $dest — compute + record it (\`sha256sum '$dest'\`)"
  fi
}

# ---- guards ---------------------------------------------------------------
[[ "$(uname -m)" == "x86_64" ]] || { echo "REFUSING: not x86_64 (this is a draft for the x86 rig)."; exit 1; }
if [[ $DRY -eq 1 ]]; then log "DRY-RUN (plan only). Re-run with --go on the x86 rig to install."; fi
[[ $DRY -eq 0 ]] && : >"$MANIFEST" && printf 'tool\tversion\tsource\tsha256\tpath\tverify\tnotes\n' >>"$MANIFEST"

# ---- Layer A: apt (signed) ------------------------------------------------
log "Layer A — apt base"
run "sudo apt update"
run "sudo apt install -y flatpak pipx golang libssl-dev"
run "pipx ensurepath"
[[ $DO_DATA -eq 1 ]] && run "sudo apt install -y astrometry.net astrometry-data-tycho2"   # 4100-series = wide-field
# xvfb only if you must run a GUI pyscript (we avoid): sudo apt install -y xvfb
manifest astrometry.net apt apt-signed apt /usr/share/astrometry "solve-field --help" "4100 Tycho-2 wide-field indexes"

# ---- Layer B: flatpak Siril ----------------------------------------------
log "Layer B — Siril (flatpak $SIRIL_FLATPAK_ID, 1.4.4)"
run "sudo flatpak remote-add --if-not-exists flathub https://flathub.org/repo/flathub.flatpakrepo"
run "sudo flatpak install -y flathub $SIRIL_FLATPAK_ID"
# pin: flatpak remote-info --log flathub $SIRIL_FLATPAK_ID  -> record the OSTree commit
manifest Siril 1.4.4 flathub:$SIRIL_FLATPAK_ID ostree-signed flatpak \
  "flatpak run --command=siril-cli $SIRIL_FLATPAK_ID -v" "sandbox private /tmp: .ssf under \$HOME"

# ---- Layer C: project venv (PEP 668 safe) ---------------------------------
log "Layer C — Python venv ($VENV) + pinned requirements"
run "python3 -m venv '$VENV'"
run "'$VENV/bin/pip' install -U pip"
run "'$VENV/bin/pip' install -r '$(dirname "$0")/requirements.txt'"
manifest python-libs venv requirements.txt pip-hashes "$VENV" "'$VENV/bin/python' -c 'import astropy'" "astropy==8.0.1"

# ---- Layer D: pinned /opt self-contained binaries -------------------------
log "Layer D — pinned /opt binaries"
tmp="$(mktemp -d)"

# StarNet2 (TIFF/PNG in, not FITS)
fetch "$STARNET_URL" "$tmp/starnet.zip" "$STARNET_SHA"
run "sudo mkdir -p $OPT/starnet2-${STARNET_VER}"
run "sudo unzip -q -o '$tmp/starnet.zip' -d $OPT/starnet2-${STARNET_VER}"
manifest StarNet2 "$STARNET_VER" "$STARNET_URL" "$STARNET_SHA" "$OPT/starnet2-${STARNET_VER}" "starnet2 --version" "TIFF/PNG only"

# DeepSNR
fetch "$DEEPSNR_URL" "$tmp/deepsnr.zip" "$DEEPSNR_SHA"
run "sudo mkdir -p $OPT/deepsnr-${DEEPSNR_VER}"
run "sudo unzip -q -o '$tmp/deepsnr.zip' -d $OPT/deepsnr-${DEEPSNR_VER}"
manifest DeepSNR "$DEEPSNR_VER" "$DEEPSNR_URL" "$DEEPSNR_SHA" "$OPT/deepsnr-${DEEPSNR_VER}" "deepsnr -h" "NAFNet, self-contained ONNX"

# GraXpert stable zip (add pipx --pre 3.2.0a2 separately if deconv wanted)
fetch "$GRAXPERT_URL" "$tmp/graxpert.zip" "$GRAXPERT_SHA"
run "sudo mkdir -p $OPT/graxpert-${GRAXPERT_VER}"
run "sudo unzip -q -o '$tmp/graxpert.zip' -d $OPT/graxpert-${GRAXPERT_VER}"
manifest GraXpert "$GRAXPERT_VER" "$GRAXPERT_URL" "$GRAXPERT_SHA" "$OPT/graxpert-${GRAXPERT_VER}" "GraXpert-linux -h" "stable=BGE+denoise; -gpu false; alpha via pipx --pre for deconv"

# ASTAP CLI + wide-field star DBs (W08 + G05) for the ultra-wide/trailed class
if [[ $DO_DATA -eq 1 ]]; then
  fetch "$ASTAP_URL" "$tmp/astap.zip" "$ASTAP_SHA"
  fetch "$ASTAP_DB_W08_URL" "$tmp/astap_w08.deb" "$ASTAP_DB_W08_SHA"
  fetch "$ASTAP_DB_G05_URL" "$tmp/astap_g05.deb" "$ASTAP_DB_G05_SHA"
  run "sudo mkdir -p $OPT/astap"
  run "sudo unzip -q -o '$tmp/astap.zip' -d $OPT/astap"
  run "sudo dpkg -i '$tmp/astap_w08.deb' '$tmp/astap_g05.deb' || sudo apt -f install -y"   # DBs install under /opt/astap
  manifest ASTAP 2026.06.29 "$ASTAP_URL" "$ASTAP_SHA" "$OPT/astap" "astap_cli --version" "W08+G05 wide DBs (ultra-wide class); d50 for narrow; use astap_cli headless; libssl-dev if TLS errors"
fi

# Cosmic Clarity — frozen bins + model assets from the rolling GH tag (pin by date+digest)
log "Cosmic Clarity: fetch $COSMIC_TAG assets ($COSMIC_DATE) from github.com/setiastro/cosmicclarity/releases"
run "sudo mkdir -p $OPT/cosmicclarity-${COSMIC_DATE}"
# TODO: enumerate + sha256 each release asset (binaries + .onnx/.pth models) via the GH API, then unzip here.
manifest CosmicClarity "$COSMIC_DATE" "gh:setiastro/cosmicclarity#$COSMIC_TAG" per-asset-sha256 "$OPT/cosmicclarity-${COSMIC_DATE}" "SetiAstroCosmicClarity --help" "--disable_gpu; gnome-terminal only for GUI launcher"

# Nightlight — go build from the dormant tag (optional; a cross-check tool)
log "Nightlight: go build $NIGHTLIGHT_VER (Go >=1.20)"
run "git clone --branch $NIGHTLIGHT_VER --depth 1 https://github.com/mlnoga/nightlight '$tmp/nightlight'"
run "sudo mkdir -p $OPT/nightlight-0.2.6"
run "cd '$tmp/nightlight' && go build -o $OPT/nightlight-0.2.6/nightlight ./cmd/nightlight"
manifest Nightlight "$NIGHTLIGHT_VER" "gh:mlnoga/nightlight@$NIGHTLIGHT_VER" go.sum "$OPT/nightlight-0.2.6" "nightlight version" "dormant 2023; cross-check only"

run "rm -rf '$tmp'"

# ---- rc-astro: license-gated, manual --------------------------------------
cat <<'RCASTRO'

[bootstrap] rc-astro (BXT/NXT/SXT) is LICENSE-GATED — do this by hand:
  1) Download the Linux installer from your rc-astro account page (authenticated).
  2) Run it; the `rc-astro` binary lands on PATH (record its /opt path in the manifest).
  3) rc-astro <bxt|nxt|sxt> --activate <email> <license-key>     # once, online
  4) rc-astro download-models                                    # cache models, then offline
  5) Verify LIBRARIES (the req is a glibc-2.35/GLIBCXX-3.4.30 floor + AVX2, NOT a
     desktop — Kali glibc 2.42 clears it; a missing lib => apt install <it>, never a DE switch):
       ldd "$(command -v rc-astro)"   # confirm no 'not found'
       rc-astro bxt            # prints help + license state
       rc-astro --device       # list devices; use --device cpu (no GPU). (--engine is legacy)
  6) sha256 the installer yourself and add a manifest row.
RCASTRO

# ---- Verification pass (fail loud) ----------------------------------------
if [[ $DRY -eq 0 ]]; then
  log "Verification pass"
  fail=0
  check(){ log "verify: $*"; eval "$@" >/dev/null 2>&1 || { echo "  FAILED: $*" >&2; fail=1; }; }
  check "flatpak run --command=siril-cli $SIRIL_FLATPAK_ID -v"
  check "$OPT/starnet2-${STARNET_VER}/starnet2 --version"
  check "$OPT/deepsnr-${DEEPSNR_VER}/deepsnr -h"
  check "$OPT/graxpert-${GRAXPERT_VER}/GraXpert-linux -h"
  check "$OPT/nightlight-0.2.6/nightlight version"
  [[ $DO_DATA -eq 1 ]] && { check "astap_cli --version || astap --version"; check "solve-field --help"; }
  check "'$VENV/bin/python' -c 'import numpy,scipy,PIL,astropy;print(astropy.__version__)'"
  [[ $fail -eq 0 ]] && log "ALL VERIFY OK — manifest at $MANIFEST" || { echo "[bootstrap] VERIFY FAILURES — see above"; exit 1; }
else
  log "DRY-RUN complete. Fill the TODO sha256 fields, then re-run with --go on the x86 rig."
fi
