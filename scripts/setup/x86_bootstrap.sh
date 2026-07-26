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
# INTEGRITY: FAIL-CLOSED. A download with no pinned sha256 ABORTS a --go install
# (a dry-run lists which pins are missing) — pin it, or pass --allow-unpinned to
# install unverified on purpose. A checksum mismatch always aborts. No silent
# unverified install.
#
# SAFETY: refuses to run unless `uname -m` == x86_64 AND `--go` is passed. Default is
# a dry-run that prints the plan. So it cannot execute on the arm box or touch anything.
#
# USAGE:
#   ./x86_bootstrap.sh                    # dry-run: print the plan + missing pins
#   ./x86_bootstrap.sh --go               # install (x86-64 only; refuses unpinned downloads)
#   ./x86_bootstrap.sh --go --allow-unpinned   # install even where a sha256 pin is missing
#   ./x86_bootstrap.sh --go --skip-data   # skip the ASTAP wide DBs + astrometry.net indexes
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

# GraXpert: official stable 3.0.2 zip (BGE+denoise) is the reproducible base. Deconv
# exists only in the 3.1.0-RC line and a third-party fork's `3.2.0a2` (geeksville, a
# PyPI test build — NOT official, bug #243) — pipx --pre it ONLY if deconv is wanted,
# knowing it is neither official nor a reproducible pin.
GRAXPERT_VER="3.0.2"
GRAXPERT_URL="https://github.com/Steffenhir/GraXpert/releases/download/${GRAXPERT_VER}/graxpert-linux-amd64.zip"
# The GitHub API returns no `digest` for this release's assets (it predates asset
# digests), so the pin below is a self-computed sha256 of the downloaded zip,
# cross-checked against the API's published asset SIZE (392722792 B, exact match).
# That pins REPRODUCIBILITY; authenticity rests on the HTTPS fetch from GitHub.
GRAXPERT_SHA="0a7364c3304ba19f12231d533c80b294054d6558d54ecd81668e4dec49092588"

# ASTAP CLI (no-GTK) + star DB(s). For the ULTRA-WIDE/trailed class use the WIDE DBs
# W08 (276 kB, 20-80 deg) + G05 (101 MB, 3-20 deg) — the D-series caps at 6 deg and
# G17/H17 are deprecated (docs/plate-solving-and-drizzle.md). For NARROW fields swap in
# d50_star_database.deb (~850 MB) instead.
ASTAP_URL="https://sourceforge.net/projects/astap-program/files/linux_installer/astap_command-line_version_Linux_amd64.zip/download"
# NOTE: upstream RENAMED this file (w08_star_database.deb -> w08_star_database_mag08_astap.deb);
# the old name now 404s. Coverage is unchanged and still correct for the ultra-wide
# class — the upstream readme states W08 for 80>FOV>20 deg, G05 for 20>FOV>3 deg, and
# the D-series (incl. the newer D80) caps at 6 deg.
ASTAP_DB_W08_URL="https://sourceforge.net/projects/astap-program/files/star_databases/w08_star_database_mag08_astap.deb/download"
ASTAP_DB_G05_URL="https://sourceforge.net/projects/astap-program/files/star_databases/g05_star_database.deb/download"
# SourceForge publishes MD5 only (in its per-path RSS `<media:hash algo="md5">`), so
# each artifact was fetched, verified against that published MD5, and its sha256
# computed and pinned here. Published MD5s matched exactly:
#   astap.zip      60728d212706efc0aad5a71a8f384311  (size 314864)
#   w08 .deb       7d9e4a9625601777d556a6718fe9ab62  (size 276144)
#   g05 .deb       63a92e1056dbd8fc84676ff5cdc14ced  (size 101323692)
ASTAP_SHA="dbbc6e6949ccde637154dada10b7fba596d2efc8acb1539c3b9d89191b67c6d6"
ASTAP_DB_W08_SHA="523131fbf448c547d42051df5d23aea7e92b0ca75484043abb35cd128da7beed"
ASTAP_DB_G05_SHA="f4a93403a0c23ac3ca0e05d0fe91080b0f0a21739aa9fabd20bc0dd5e4f77099"

# Cosmic Clarity: rolling GitHub "Linux" tag (2025-03-29), frozen self-contained bins.
COSMIC_TAG="Linux"   # pin by asset digest + the date below
COSMIC_DATE="2025-03-29"

# Nightlight: dormant Go tool (v0.2.6, 2023); go build from tag. Go >= 1.20 needed.
NIGHTLIGHT_VER="v0.2.6"

# ---------------------------------------------------------------------------
DRY=1; DO_DATA=1; ALLOW_UNPINNED=0
for a in "$@"; do case "$a" in
  --go) DRY=0 ;;
  --skip-data) DO_DATA=0 ;;
  --allow-unpinned) ALLOW_UNPINNED=1 ;;
  -h|--help) sed -n '2,25p' "$0"; exit 0 ;;
  *) echo "unknown arg: $a" >&2; exit 2 ;;
esac; done

MANIFEST="$(cd "$(dirname "$0")" && pwd)/manifest.tsv"
log(){ printf '\033[1;34m[bootstrap]\033[0m %s\n' "$*"; }
run(){ if [[ $DRY -eq 1 ]]; then printf '  (plan) %s\n' "$*"; else eval "$@"; fi; }
manifest(){ [[ $DRY -eq 1 ]] || printf '%s\t%s\t%s\t%s\t%s\t%s\t%s\n' "$@" >>"$MANIFEST"; }

# fetch <url> <dest> <sha256|""> : require a pin (FAIL-CLOSED), download, verify sha256.
fetch(){ local url="$1" dest="$2" sha="${3:-}"
  if [[ -z "$sha" ]]; then
    if [[ $DRY -eq 1 ]]; then
      log "NOTE: $(basename "$dest") has NO pinned sha256 — pin it before --go (or use --allow-unpinned)."
    elif [[ $ALLOW_UNPINNED -eq 1 ]]; then
      log "WARN: installing $(basename "$dest") UNVERIFIED (--allow-unpinned) — record: sha256sum '$dest' → paste into its *_SHA pin."
    else
      echo "[bootstrap] REFUSING: no pinned sha256 for $url" >&2
      echo "  Compute it (sha256sum the file) and set the *_SHA variable, or re-run with --allow-unpinned." >&2
      exit 1
    fi
  fi
  run "curl -fL --retry 3 -o '$dest' '$url'"
  if [[ -n "$sha" && $DRY -eq 0 ]]; then
    echo "$sha  $dest" | sha256sum -c - || { echo "[bootstrap] SHA256 MISMATCH: $dest ($url)" >&2; exit 1; }
  fi
}

# ---- guards + preflight ---------------------------------------------------
[[ "$(uname -m)" == "x86_64" ]] || { echo "REFUSING: not x86_64 (this is a draft for the x86 rig)."; exit 1; }
if [[ $DRY -eq 0 ]]; then
  for t in curl sha256sum sudo; do
    command -v "$t" >/dev/null || { echo "[bootstrap] MISSING prerequisite: $t — apt install it first."; exit 1; }
  done
  tmp="$(mktemp -d)"; trap 'rm -rf "$tmp"' EXIT       # always clean up, even on an early exit
else
  tmp="<tmpdir>"
  log "DRY-RUN (plan only). Re-run with --go on the x86 rig to install."
fi
[[ $DRY -eq 0 ]] && : >"$MANIFEST" && printf 'tool\tversion\tsource\tsha256\tpath\tverify\tnotes\n' >>"$MANIFEST"

# ---- Layer A: apt (signed) ------------------------------------------------
log "Layer A — apt base"
run "sudo apt update"
run "sudo apt install -y flatpak pipx golang git unzip libssl-dev"
run "pipx ensurepath"
[[ $DO_DATA -eq 1 ]] && run "sudo apt install -y astrometry.net astrometry-data-tycho2"   # 4100-series = wide-field
# xvfb only if you must run a GUI pyscript (we avoid): sudo apt install -y xvfb
manifest astrometry.net apt apt-signed apt /usr/share/astrometry "solve-field --help" "4100 Tycho-2 wide-field indexes"

# darktable + lensfun = the UNDISTORT stage (the wide-field UNTRACKED class).
# darktable must be BUILT AGAINST lensfun — Debian's is; its RawTherapee is NOT
# (no lensfun link, so no auto-match). liblensfun-bin carries lensfun-update-data:
# it is NOT in python3-lensfun (that package has only DB-path helpers and no
# matcher), and without it the DB update below cannot run.
run "sudo apt install -y darktable liblensfun-bin python3-lensfun hugin-tools"
manifest darktable apt apt-signed apt /usr/bin/darktable-cli "darktable-cli --version" "UNDISTORT stage; must be built against lensfun"
manifest lensfun apt apt-signed apt /usr/share/lensfun "lensfun-update-data --help" "liblensfun-bin ships lensfun-update-data (NOT python3-lensfun)"
manifest hugin-tools apt apt-signed apt /usr/bin/cpfind "cpfind --version" "lens-model FIT route: cpfind/cpclean/autooptimiser fit ptlens a,b,c from a set's own frames (scripts/darktable/fit_lens_model.sh)"

# The undistort route needs THREE things apt cannot give it, ALL
# machine-local — none migrates with the repo, so they are re-created per rig:
#
#  1. The UPSTREAM lensfun DB. The distro's 0.3.4 DB predates recent bodies (it
#     lacks the Nikon Z6III, measured), and without a CAMERA match lensfun cannot
#     build a modifier at all — the body supplies the crop factor, the lens the
#     distortion. lensfun-update-data writes the upstream DB to
#     ~/.local/share/lensfun/updates/version_1 (a USER path — run it as the user
#     who will process, not root). INTEGRITY EXCEPTION: it fetches over plain
#     HTTP, unsigned and unpinned — the one Layer-A input outside this script's
#     fail-closed sha256 model, and it supplies the geometry model. The update
#     IS deterministic (a from-scratch rebuild is byte-identical), so version_1/
#     can be sha256-pinned per rig if that trade is worth its upkeep.
#  2. The lens STYLES, from the repo. Their op_params blob is the pinned artifact;
#     darktable has no CLI style import, so install_styles.sh writes them into
#     darktable's data.db directly. Never re-create them by hand in the GUI.
#  3. The FITTED lens model. Where a community DB entry's paraxial error writes
#     the centre band into a far-drifting set (docs/dead-ends.md), the entry
#     measured from the unit's own frames replaces it: install_lens_model.sh
#     patches the user updates DB (idempotent, loud on upstream drift) and MUST
#     be re-run after every lensfun-update-data, which overwrites the patch.
#
# Skipping any of these is SILENT: darktable applies no correction to a lens it
# cannot match, exits 0, and logs nothing (measured). scripts/stack/lens_preflight.py
# --require-profile is what catches that, and the verification pass below runs it.
log "Layer A2 — lensfun DB update + the repo's darktable lens styles + the fitted lens model"
# lensfun-update-data's exit codes (read from /usr/bin/lensfun-update-data, MEASURED here):
#   0 = a newer DB was downloaded
#   1 = "No newer database was found for last installed Lensfun" — ALREADY CURRENT,
#       which is SUCCESS for us, not a failure
#   3 = "No location was responsive.  Network down?" — a REAL failure
# Under `set -e` a bare call aborts the whole bootstrap on code 1, so the script could
# only ever run once: every re-run dies here the moment the DB is current. Tolerate 1
# ONLY — 3 (and anything else) must still fail loud, because a stale or missing DB
# disables lens correction SILENTLY (darktable exits 0 and logs nothing on no match).
if [[ $DRY -eq 1 ]]; then
  printf '  (plan) %s\n' "lensfun-update-data"
else
  set +e; lensfun-update-data; lu_rc=$?; set -e
  case $lu_rc in
    0) log "lensfun DB updated" ;;
    1) log "lensfun DB already current (exit 1) — continuing" ;;
    *) echo "[bootstrap] lensfun-update-data FAILED (exit $lu_rc) — DB not usable; aborting" >&2; exit 1 ;;
  esac
fi
run "bash '$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)/darktable/install_styles.sh' \"\${XDG_CONFIG_HOME:-\$HOME/.config}/darktable\""
run "bash '$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)/darktable/install_lens_model.sh'"
manifest lensfun-db upstream lensfun-update-data n/a "$HOME/.local/share/lensfun/updates/version_1" "test -d $HOME/.local/share/lensfun/updates/version_1" "MACHINE-LOCAL: not tracked, re-run per rig; distro DB lacks recent bodies"
manifest dt-lens-styles repo scripts/darktable n/a "\${XDG_CONFIG_HOME:-\$HOME/.config}/darktable/data.db" "true" "lensdist/nodist; op_params is the pinned artifact; no GUI step"
manifest dt-lens-model repo scripts/darktable n/a "$HOME/.local/share/lensfun/updates/version_1/mil-nikon.xml" "true" "RETIRED-BODY PIN (24-70/4 S @ 70) — re-fit for the new rig's lens FIRST (fit_lens_model.sh); re-install after every lensfun-update-data; skip when the wide-untracked class is not in play"

# ---- Layer B: flatpak Siril ----------------------------------------------
log "Layer B — Siril (flatpak $SIRIL_FLATPAK_ID, 1.4.4)"
run "sudo flatpak remote-add --if-not-exists flathub https://flathub.org/repo/flathub.flatpakrepo"
run "sudo flatpak install -y flathub $SIRIL_FLATPAK_ID"
# Flathub `stable` observed serving 1.4.4 at this OSTree commit (subject: "Merge pull
# request #28 from flathub/1_4_4", 2026-06-19). Recorded so a later drift is visible:
# re-check with `flatpak remote-info flathub $SIRIL_FLATPAK_ID` before trusting a
# re-install. Siril 1.5.0-dev REMOVES starnet/seqstarnet and would break any .ssf that
# calls them — never install that line here.
SIRIL_OSTREE_COMMIT="9fad0dc12d090f6d0d0b4cb925904e4978e0943fb24a8acf703c33ee86f80e90"
manifest Siril 1.4.4 "flathub:$SIRIL_FLATPAK_ID@$SIRIL_OSTREE_COMMIT" ostree-signed flatpak \
  "flatpak run --command=siril-cli $SIRIL_FLATPAK_ID -v" "sandbox private /tmp: .ssf under \$HOME"

# ---- Layer B2: SPCC runtime prerequisites (machine-local, siril flatpak) --
# SPCC (scripts/calibrate/spcc_run.py) has THREE machine-local prerequisites; miss the
# sensor DATABASE and siril SIGSEGVs in aperture photometry (exit 139) with NO useful
# message — it mimics a data/field bug and cost a long hunt (docs/dead-ends.md; CLAUDE.md
# Environment). None migrate with the repo, so they are re-created per rig. MEASURED x86.
log "Layer B2 — SPCC prerequisites (sensor database + Gaia catalog path + config)"
SPCC_DB_URL="https://gitlab.com/free-astro/siril-spcc-database.git"
SPCC_DB_DIR="$HOME/.var/app/org.siril.Siril/data/siril-spcc-database"
SPCC_CAT_DIR="$HOME/.local/share/siril/siril_catalogues/spcc"
SIRIL_CFG="$HOME/.var/app/org.siril.Siril/config/siril/config.1.4.ini"

# (1) The sensor/filter/white-reference DATABASE — a SEPARATE small git repo from the
#     Gaia catalog. Without it `spcc_list` is empty, SPCC applies a (null) sensor
#     response and crashes. siril's own auto-download can fail silently; clone it.
run "mkdir -p '$(dirname "$SPCC_DB_DIR")'"
run "[ -d '$SPCC_DB_DIR/.git' ] || git clone --depth 1 '$SPCC_DB_URL' '$SPCC_DB_DIR'"

# (2) Siril's config is created on its first run — trigger it, then point
#     catalogue_gaia_photo at the local Gaia chunk dir (a fresh flatpak defaults it to a
#     non-existent gaia_photometric.dat, so siril range-reads ONLINE and 429s), and set
#     auto_update_spcc=false (catalog + database are both local). Set-or-append, idempotent.
run "mkdir -p '$SPCC_CAT_DIR'"
run "flatpak run --command=siril-cli $SIRIL_FLATPAK_ID -v >/dev/null 2>&1 || true"
if [[ $DRY -eq 1 ]]; then
  printf '  (plan) patch %s: catalogue_gaia_photo=%s ; auto_update_spcc=false\n' "$SIRIL_CFG" "$SPCC_CAT_DIR"
else
  [ -f "$SIRIL_CFG" ] || { echo "[bootstrap] siril config not created at $SIRIL_CFG — run siril once, then re-run" >&2; exit 1; }
  for kv in "catalogue_gaia_photo=$SPCC_CAT_DIR" "auto_update_spcc=false"; do
    k=${kv%%=*}
    if grep -q "^$k=" "$SIRIL_CFG"; then sed -i "s#^$k=.*#$kv#" "$SIRIL_CFG"
    else printf '%s\n' "$kv" >> "$SIRIL_CFG"; fi
  done
  log "siril SPCC config set (catalogue_gaia_photo -> local chunks; auto_update_spcc=false)"
fi

# (3) The Gaia xp_sampled cone chunks are FIELD-dependent — NOT pre-installable here;
#     scripts/calibrate/spcc_cone.py <solved_wcs.fit> --fetch downloads exactly the
#     field's nside=2 cover per render (md5-verified).
manifest spcc-database git-HEAD gitlab:free-astro/siril-spcc-database n/a "$SPCC_DB_DIR" \
  "test -d '$SPCC_DB_DIR/osc_sensors'" "MACHINE-LOCAL sensor/filter/whiteref defs; MISSING => siril SPCC SIGSEGV (exit 139)"
manifest spcc-config siril-flatpak-config n/a n/a "$SIRIL_CFG" \
  "grep -q 'catalogue_gaia_photo=$SPCC_CAT_DIR' '$SIRIL_CFG'" "catalogue_gaia_photo -> local chunks; auto_update_spcc=false"
manifest spcc-gaia-cone per-render scripts/calibrate/spcc_cone.py n/a "$SPCC_CAT_DIR" \
  "true" "FIELD-dependent: spcc_cone.py <wcs> --fetch per render (zenodo 14738271, md5-verified)"

# ---- Layer C: project venv (PEP 668 safe) ---------------------------------
# $VENV defaults under /opt (root-owned parent) — create with sudo, then chown to the
# invoking user so pip and later dep changes need no root and the venv is not a
# root-owned artifact the orchestration must sudo to modify.
log "Layer C — Python venv ($VENV) + pinned requirements"
run "sudo python3 -m venv '$VENV'"
run "sudo chown -R '$(id -un):$(id -gn)' '$VENV'"
run "'$VENV/bin/pip' install -U pip"
run "'$VENV/bin/pip' install -r '$(dirname "$0")/requirements.txt'"
manifest python-libs venv requirements.txt pip-hashes "$VENV" "'$VENV/bin/python' -c 'import astropy'" "astropy==8.0.1"

# ---- Layer D: pinned /opt self-contained binaries -------------------------
log "Layer D — pinned /opt binaries"

# Each vendor zip contains a TOP-LEVEL DIRECTORY, so the binary does NOT land at
# $OPT/<tool>-<ver>/<tool> as the manifest first assumed. These are the real paths,
# MEASURED on this rig after extraction. Weights (.onnx) sit beside their binary, so
# the archive layout is kept as shipped rather than flattened. Note GraXpert ships
# `GraXpert-linux` as a DIRECTORY whose binary is `GraXpert` — running the directory
# name is what produced the "permission denied" on the first run here.
STARNET_BIN="$OPT/starnet2-${STARNET_VER}/starnet2_linux_${STARNET_VER}_ORT_x64_cli/starnet2"
DEEPSNR_BIN="$OPT/deepsnr-${DEEPSNR_VER}/deepsnr_linux_${DEEPSNR_VER}_ORT_x64_cli/deepsnr"
GRAXPERT_BIN="$OPT/graxpert-${GRAXPERT_VER}/GraXpert-linux/GraXpert"
ASTAP_BIN="$OPT/astap/astap_cli"     # not on PATH — always invoke by absolute path

# StarNet2 (TIFF/PNG in, not FITS)
fetch "$STARNET_URL" "$tmp/starnet.zip" "$STARNET_SHA"
run "sudo mkdir -p $OPT/starnet2-${STARNET_VER}"
run "sudo unzip -q -o '$tmp/starnet.zip' -d $OPT/starnet2-${STARNET_VER}"
manifest StarNet2 "$STARNET_VER" "$STARNET_URL" "$STARNET_SHA" "$STARNET_BIN" "'$STARNET_BIN' --version" "TIFF/PNG only; zip nests a top-level dir"

# DeepSNR
fetch "$DEEPSNR_URL" "$tmp/deepsnr.zip" "$DEEPSNR_SHA"
run "sudo mkdir -p $OPT/deepsnr-${DEEPSNR_VER}"
run "sudo unzip -q -o '$tmp/deepsnr.zip' -d $OPT/deepsnr-${DEEPSNR_VER}"
manifest DeepSNR "$DEEPSNR_VER" "$DEEPSNR_URL" "$DEEPSNR_SHA" "$DEEPSNR_BIN" "'$DEEPSNR_BIN' -h" "NAFNet, self-contained ONNX; zip nests a top-level dir"

# GraXpert stable zip (add pipx --pre 3.2.0a2 separately if deconv wanted)
fetch "$GRAXPERT_URL" "$tmp/graxpert.zip" "$GRAXPERT_SHA"
run "sudo mkdir -p $OPT/graxpert-${GRAXPERT_VER}"
run "sudo unzip -q -o '$tmp/graxpert.zip' -d $OPT/graxpert-${GRAXPERT_VER}"
manifest GraXpert "$GRAXPERT_VER" "$GRAXPERT_URL" "$GRAXPERT_SHA" "$GRAXPERT_BIN" "'$GRAXPERT_BIN' -h" "stable=BGE+denoise; -gpu false; GraXpert-linux is a DIR, binary is GraXpert inside it"

# ASTAP CLI + wide-field star DBs (W08 + G05) for the ultra-wide/trailed class
if [[ $DO_DATA -eq 1 ]]; then
  fetch "$ASTAP_URL" "$tmp/astap.zip" "$ASTAP_SHA"
  fetch "$ASTAP_DB_W08_URL" "$tmp/astap_w08.deb" "$ASTAP_DB_W08_SHA"
  fetch "$ASTAP_DB_G05_URL" "$tmp/astap_g05.deb" "$ASTAP_DB_G05_SHA"
  run "sudo mkdir -p $OPT/astap"
  run "sudo unzip -q -o '$tmp/astap.zip' -d $OPT/astap"
  run "sudo dpkg -i '$tmp/astap_w08.deb' '$tmp/astap_g05.deb' || sudo apt -f install -y"   # DBs install under /opt/astap
  # OBSERVED build is CLI-2026.07.16 (the SF zip moved on from the 2026.06.29 the docs
  # recorded); the sha256 above pins the exact artifact regardless of the label.
  manifest ASTAP CLI-2026.07.16 "$ASTAP_URL" "$ASTAP_SHA" "$ASTAP_BIN" "'$ASTAP_BIN'" "W08+G05 wide DBs (ultra-wide class); d50 for narrow; use astap_cli headless; libssl-dev if TLS errors"
fi

# Cosmic Clarity — NOT installed here: the suite is a multi-GB MANUAL download with no
# stable pinnable URL (the GH "Linux" tag is an a-la-carte updater, and the full-suite
# bundle comes from the setiastro site). Staged by hand, then placed + verified by the
# dedicated installer, which records the folder-batch I/O + the satellite/superres gap.
log "Cosmic Clarity: install manually — download the CosmicClaritySuite_Linux bundle, extract, then run scripts/setup/install_cosmicclarity.sh (USER-OWNED /opt install; folder-batch I/O). satellite+superres are a known GAP (bundle torch runtime broken)."

# Nightlight — go build from the dormant tag (optional; a cross-check tool)
log "Nightlight: go build $NIGHTLIGHT_VER (Go >=1.20)"
# --recurse-submodules is REQUIRED, not a nicety: web/blockly is a git submodule
# (google/blockly) and web/static.go has a `//go:embed blockly` directive, so a plain
# --depth 1 clone leaves the dir empty and the build dies with
#   "pattern blockly: cannot embed directory blockly: contains no embeddable files".
# --shallow-submodules keeps the blockly fetch cheap (the REST/Blockly GUI is embedded
# unconditionally even though we only ever use the headless CLI). MEASURED on this rig.
run "git clone --branch $NIGHTLIGHT_VER --depth 1 --recurse-submodules --shallow-submodules https://github.com/mlnoga/nightlight '$tmp/nightlight'"
run "(cd '$tmp/nightlight' && go build -o '$tmp/nightlight/nightlight' ./cmd/nightlight)"   # build as user (Go cache in \$HOME); subshell isolates the cd
run "sudo mkdir -p $OPT/nightlight-0.2.6"
run "sudo cp '$tmp/nightlight/nightlight' $OPT/nightlight-0.2.6/nightlight"                  # then install root-owned into /opt
manifest Nightlight "$NIGHTLIGHT_VER" "gh:mlnoga/nightlight@$NIGHTLIGHT_VER" go.sum "$OPT/nightlight-0.2.6" "nightlight version" "dormant 2023; cross-check only; built from tag v0.2.6 but the binary self-reports 'Version 0.2.5' (upstream never bumped the string) - the TAG is the pin, not the printed version"
# ($tmp is cleaned by the EXIT trap set in the guards block)

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
       rc-astro nxt --benchmark-all   # measure + pin the fastest device (CPU here; no vendor figures exist)
  6) Capture the REAL per-tool flags with a no-arg run — esp. `rc-astro nxt` (the exact
     chroma flag spelling, e.g. denoise_color, that closes the chroma-noise gap) — and
     reconcile TOOLS.md / docs/rc-astro-cli-linux.md to what is actually there.
  7) sha256 the installer yourself and add a manifest row.
RCASTRO

# ---- Verification pass (fail loud; surfaces the OBSERVED version) ----------
if [[ $DRY -eq 0 ]]; then
  log "Verification pass"
  fail=0
  # run the verify cmd; print its first output line (the observed version/reality); fail loud.
  check(){ local out; log "verify: $*"
    # Report the first NON-EMPTY line: StarNet2 and DeepSNR both emit a leading blank
    # line before their version string, so a plain `head -n1` rendered a genuine PASS
    # as empty output and made a working tool look unverified. (MEASURED here.)
    if out="$(eval "$@" 2>&1)"; then printf '  OK   %s\n' "$(printf '%s' "$out" | awk 'NF{print;exit}')"
    else echo "  FAILED: $*" >&2; fail=1; fi; }
  check "flatpak run --command=siril-cli $SIRIL_FLATPAK_ID -v"
  # SPCC prereqs: the sensor DATABASE (its absence is the SIGSEGV) + the config path.
  # A version string proves nothing here — SPCC crashes silently without the database.
  check "test -d '$HOME/.var/app/org.siril.Siril/data/siril-spcc-database/osc_sensors' && echo 'SPCC sensor database present'"
  check "grep -q 'catalogue_gaia_photo=$HOME/.local/share/siril/siril_catalogues/spcc' '$HOME/.var/app/org.siril.Siril/config/siril/config.1.4.ini' && echo 'SPCC catalog path set'"
  check "darktable-cli --version"
  # The UNDISTORT route's install is only real if the DB update landed AND the
  # styles are in darktable's data.db. Prove both, not just that the binary
  # exists: a missing DB or a missing style both fail SILENTLY at render time.
  check "test -d '$HOME/.local/share/lensfun/updates/version_1' && echo 'upstream lensfun DB present'"
  check "python3 -c \"import sqlite3,os,sys; d=os.path.expanduser('~/.config/darktable/data.db'); c=sqlite3.connect('file:%s?mode=ro'%d,uri=True); n=[r[0] for r in c.execute('SELECT name FROM styles')]; sys.exit(0 if {'lensdist','nodist'} <= set(n) else 1)\" && echo 'lensdist+nodist styles installed'"
  log "NOTE: the styles + DB only PROVE out against real frames — run
     scripts/stack/lens_preflight.py <session> <set> --require-profile
  on a camera-lens set. It renders one frame through lensdist vs nodist and asks
  Siril for the difference; an all-nil difference means no profile matched and the
  set would stack UNCORRECTED with no warning from darktable."
  check "'$STARNET_BIN' --version"
  check "'$DEEPSNR_BIN' -h"
  check "'$GRAXPERT_BIN' -h"
  check "$OPT/nightlight-0.2.6/nightlight version"
  # NO ||-fallback here: a shell command-not-found handler can exit 0 and turn a
  # missing binary into a false PASS (observed on this rig with the old astap_cli ||
  # astap chain). Check the absolute path, and assert the wide star DBs really landed.
  if [[ $DO_DATA -eq 1 ]]; then
    # astap_cli --version exits 0 printing NOTHING; only the no-arg run reports the
    # build ("ASTAP astrometric solver version CLI-YYYY.MM.DD"). Verify by that.
    check "'$ASTAP_BIN'"
    check "ls $OPT/astap/w08_* >/dev/null && ls $OPT/astap/g05_* >/dev/null && echo 'W08+G05 star DBs present'"
    check "solve-field --help"
  fi
  check "'$VENV/bin/python' -c 'import numpy,scipy,PIL,astropy;print(astropy.__version__)'"
  # rc-astro is manual / license-gated — verify only if the operator has installed it
  if command -v rc-astro >/dev/null; then check "rc-astro --device"
  else log "rc-astro: not on PATH — install it manually (steps above), then re-verify."; fi
  [[ $fail -eq 0 ]] && log "ALL VERIFY OK — manifest at $MANIFEST" || { echo "[bootstrap] VERIFY FAILURES — see above"; exit 1; }
else
  log "DRY-RUN complete. Pin the missing sha256 fields (noted above), then re-run with --go on the x86 rig."
fi
