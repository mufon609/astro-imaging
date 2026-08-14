#!/usr/bin/env bash
# x86_bootstrap.sh — reproducible tool install for the x86-64 Kali production rig.
#
# STATUS: the production install script for the repo's ONE rig class (x86-64
# Kali; CLAUDE.md "Environment"). Its steps are verified
# PIECEWISE on this rig: every tool below is installed and driven here, and
# scripts/setup/manifest.tsv is the tracked inventory (versions, sources,
# checksums) those installs recorded. NOT yet run as ONE from-scratch pass on a
# fresh machine — that single-run rebuild is the acceptance test for any new or
# reimaged rig, and a step failing there is a bug in this script, not the rig
# (CLAUDE.md: the environment must be rebuildable from tracked files).
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
# a dry-run that prints the plan, so a stray invocation cannot touch anything.
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
# G17/H17 are deprecated (docs/dead-ends.md, trailed-solve entry). For NARROW fields swap in
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
DRY=1; DO_DATA=1; ALLOW_UNPINNED=0; SELFTEST_GAIA=0
for a in "$@"; do case "$a" in
  --go) DRY=0 ;;
  --skip-data) DO_DATA=0 ;;
  --allow-unpinned) ALLOW_UNPINNED=1 ;;
  --selftest-gaia) SELFTEST_GAIA=1 ;;   # fire-test Layer B3 in a scratch dir; installs nothing
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

# ---- Layer B3's implementation, defined HERE ------------------------------
# It lives above the guards so `--selftest-gaia` can fire-test it WITHOUT entering
# any install layer and WITHOUT reaching the line that truncates $MANIFEST. The
# layer itself executes in position, further down. `fetch()` above is not reused:
# this needs resume, a decompress step, a second hash and a rename, none of which
# it does.
#
# WHY THIS LAYER EXISTS. siril's config ships `catalogue_gaia_astro` pointing at
# ~/.local/share/siril/gaia_astrometric.dat and nothing here ever created it, so a
# fresh rig got a config naming a file the bootstrap never wrote. It surfaced as a
# BLOCKED MEASUREMENT (`-cat=localgaia` with nothing to read), not as a missing
# file. The published basename differs from the one siril expects, so the file is
# RENAMED on install and THE CONFIG IS NEVER TOUCHED — the config was always right.
#
# TWO HASHES, BOTH SOURCE-PUBLISHED, AND THE SECOND IS NOT DECORATIVE. Zenodo
# publishes an API md5 per file AND in-record .sha256sum sidecars, including one for
# the DECOMPRESSED artifact. Checking that one independently is what makes bunzip2 a
# VERIFIED step rather than a trusted one — a destination-only hash is
# self-verification and cannot catch a corrupted decompress. Provenance for both
# pins: scripts/setup/catalogue_ingest.json.
GAIA_ASTRO_URL="${GAIA_ASTRO_URL:-https://zenodo.org/records/14692304/files/siril_cat_healpix8_astro.dat.bz2?download=1}"
GAIA_ASTRO_DEST="${GAIA_ASTRO_DEST:-$HOME/.local/share/siril/gaia_astrometric.dat}"
GAIA_ASTRO_BZ2_SHA="${GAIA_ASTRO_BZ2_SHA:-846ad4b12c50865df0cb8c5b23453f22eec78bbe9969e17d669ae19eb49d421f}"
GAIA_ASTRO_DAT_SHA="${GAIA_ASTRO_DAT_SHA:-2fa40c93fe115235d35c5050757f2ef60a326a6f3030f87be1598c016fcb2388}"

install_gaia_astro(){
  local dest="$GAIA_ASTRO_DEST" stage bz2 dat
  stage="$(dirname "$dest")/_fetch"; bz2="$stage/siril_cat_healpix8_astro.dat.bz2"
  dat="$stage/siril_cat_healpix8_astro.dat"
  # IDEMPOTENT, and it is what stops a re-run pulling 1.1 GB again.
  if [[ -f "$dest" ]] && echo "$GAIA_ASTRO_DAT_SHA  $dest" | sha256sum -c --status -; then
    log "gaia_astrometric.dat present and sha256-VERIFIED — no fetch"; return 0; fi
  [[ -f "$dest" ]] && log "gaia_astrometric.dat present but FAILS its sha256 — refetching"
  mkdir -p "$stage" "$(dirname "$dest")" || return 1
  # RESUME IS ONLY SAFE ONTO A PARTIAL OF THE **SAME** FILE, and nothing here can
  # tell a partial from a stale wrong one. Found by this layer's own fire test: a
  # run that failed its decompressed-hash check left the bad archive staged, and
  # the next `-C -` resumed ON TOP OF IT. So: reuse a staged archive only when it
  # already matches its pin, and if a resume is refused, start from zero rather
  # than build on whatever is there. Every failure path below deletes the archive
  # for the same reason.
  if [[ -f "$bz2" ]] && echo "$GAIA_ASTRO_BZ2_SHA  $bz2" | sha256sum -c --status -; then
    log "staged archive already matches its pin — skipping the download"
  else
    if ! curl -fL --retry 3 -C - -o "$bz2" "$GAIA_ASTRO_URL"; then
      log "resume refused or interrupted — restarting the download from zero"
      rm -f "$bz2"
      curl -fL --retry 3 -o "$bz2" "$GAIA_ASTRO_URL" \
        || { echo "[bootstrap] gaia-astrometric: DOWNLOAD FAILED ($GAIA_ASTRO_URL)" >&2
             rm -f "$bz2"; return 1; }
    fi
  fi
  echo "$GAIA_ASTRO_BZ2_SHA  $bz2" | sha256sum -c --status - \
    || { echo "[bootstrap] gaia-astrometric: SHA256 MISMATCH on the COMPRESSED file — refusing" >&2
         rm -f "$bz2"; return 1; }
  rm -f "$dat"
  bunzip2 -k "$bz2" \
    || { echo "[bootstrap] gaia-astrometric: DECOMPRESS FAILED" >&2; rm -f "$bz2" "$dat"; return 1; }
  echo "$GAIA_ASTRO_DAT_SHA  $dat" | sha256sum -c --status - \
    || { echo "[bootstrap] gaia-astrometric: SHA256 MISMATCH on the DECOMPRESSED file — refusing" >&2
         rm -f "$dat" "$bz2"; return 1; }
  mv -f "$dat" "$dest" || return 1
  # RE-VERIFY AT THE INSTALLED PATH: a bad move must not pass as a good download.
  echo "$GAIA_ASTRO_DAT_SHA  $dest" | sha256sum -c --status - \
    || { echo "[bootstrap] gaia-astrometric: VERIFY FAILED AT THE INSTALLED PATH — refusing" >&2; return 1; }
  rm -f "$bz2"
  log "gaia_astrometric.dat installed and VERIFIED at $dest"
}

# ONE definition of the row, called by the layer AND by the selftest, so the test
# exercises the real generator instead of a copy that can drift from it.
manifest_gaia(){
  manifest gaia-astrometric zenodo-14692304 "$GAIA_ASTRO_URL" "$GAIA_ASTRO_DAT_SHA" "$GAIA_ASTRO_DEST" \
    "echo '$GAIA_ASTRO_DAT_SHA  $GAIA_ASTRO_DEST' | sha256sum -c --status - && echo 'gaia astrometric catalogue verified'" \
    "ASTROMETRIC half of the local Gaia pair; siril's catalogue_gaia_astro points here and the config is NOT modified. RENAMED from the published siril_cat_healpix8_astro.dat. Compressed AND decompressed sha256 are both source-published (zenodo in-record sidecars + API md5) — scripts/setup/catalogue_ingest.json"
}

selftest_gaia(){
  local sc bad=0 n=0 rc
  sc="$(mktemp -d)"; DRY=0; MANIFEST="$sc/manifest.tsv"; : >"$MANIFEST"
  mkdir -p "$sc/src" "$sc/other"
  head -c 200000 /dev/urandom > "$sc/src/siril_cat_healpix8_astro.dat"
  head -c 200000 /dev/urandom > "$sc/other/siril_cat_healpix8_astro.dat"
  ( cd "$sc/src"   && bzip2 -kf siril_cat_healpix8_astro.dat )
  ( cd "$sc/other" && bzip2 -kf siril_cat_healpix8_astro.dat )
  local good_bz2 good_dat other_bz2
  good_bz2="$(sha256sum "$sc/src/siril_cat_healpix8_astro.dat.bz2" | cut -d' ' -f1)"
  good_dat="$(sha256sum "$sc/src/siril_cat_healpix8_astro.dat"     | cut -d' ' -f1)"
  other_bz2="$(sha256sum "$sc/other/siril_cat_healpix8_astro.dat.bz2" | cut -d' ' -f1)"
  GAIA_ASTRO_DEST="$sc/dest/gaia_astrometric.dat"

  t(){ n=$((n+1)); local want="$1" name="$2"
       if install_gaia_astro >"$sc/o.$n" 2>&1; then rc=0; else rc=1; fi
       if { [[ "$want" == GREEN && $rc -eq 0 ]] || [[ "$want" == RED && $rc -ne 0 ]]; }; then
         printf '  %-56s %s\n' "$name" "OK ($want)"
       else printf '  %-56s *** FAIL *** wanted %s, rc=%s\n' "$name" "$want" "$rc"
            sed 's/^/        /' "$sc/o.$n"; bad=1; fi; }

  echo "LAYER B3 SELFTEST — scratch $sc (installs nothing, downloads nothing)"
  GAIA_ASTRO_BZ2_SHA="$good_bz2"; GAIA_ASTRO_DAT_SHA="$good_dat"

  GAIA_ASTRO_URL="file://$sc/src/NO_SUCH_FILE.bz2"
  t RED "(a) source MISSING must fail, not pass silently"
  [[ -e "$sc/dest/gaia_astrometric.dat" ]] && { echo "  *** FAIL *** dest created on a failed fetch"; bad=1; }

  GAIA_ASTRO_URL="file://$sc/other/siril_cat_healpix8_astro.dat.bz2"
  t RED "(b) COMPRESSED hash mismatch must abort"
  [[ -e "$sc/dest/gaia_astrometric.dat" ]] && { echo "  *** FAIL *** dest created on a hash mismatch"; bad=1; }

  # the pin matches the served bytes but the CONTENT is the other payload, so only
  # the DECOMPRESSED hash can catch it. Proves that leg is load-bearing.
  GAIA_ASTRO_BZ2_SHA="$other_bz2"
  t RED "(b2) DECOMPRESSED hash mismatch must abort (2nd leg is real)"
  [[ -e "$sc/dest/gaia_astrometric.dat" ]] && { echo "  *** FAIL *** dest created on a decompressed mismatch"; bad=1; }

  GAIA_ASTRO_BZ2_SHA="$good_bz2"; GAIA_ASTRO_URL="file://$sc/src/siril_cat_healpix8_astro.dat.bz2"
  t GREEN "(c) correct source + pins must INSTALL"
  echo "$good_dat  $GAIA_ASTRO_DEST" | sha256sum -c --status - \
    && printf '  %-56s %s\n' "(c2) installed file verifies at its path" "OK" \
    || { echo "  *** FAIL *** installed file does not verify"; bad=1; }

  t GREEN "(d) re-run is IDEMPOTENT (must skip the fetch)"
  grep -q 'no fetch' "$sc/o.$n" \
    && printf '  %-56s %s\n' "(d2) second run skipped the download" "OK" \
    || { echo "  *** FAIL *** second run did not skip"; bad=1; }

  manifest_gaia
  grep -q '^gaia-astrometric	' "$MANIFEST" \
    && printf '  %-56s %s\n' "(e) manifest row GENERATED into \$MANIFEST" "OK" \
    || { echo "  *** FAIL *** no manifest row"; bad=1; }
  echo "  row: $(cut -c1-96 "$MANIFEST" | tail -1)"

  rm -rf "$sc"
  [[ $bad -eq 0 ]] && { echo "SELFTEST PASSED"; return 0; } || { echo "SELFTEST FAILED"; return 1; }
}
if [[ $SELFTEST_GAIA -eq 1 ]]; then selftest_gaia; exit $?; fi

# ---- guards + preflight ---------------------------------------------------
[[ "$(uname -m)" == "x86_64" ]] || { echo "REFUSING: not x86_64 (this installer targets the x86 rig only)."; exit 1; }
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

# ---- Layer 0: the repo's git hooks -----------------------------------------
# FIRST because it needs neither root nor any other layer, and because what it
# installs is what GATES everything else. `.git/hooks/` is untracked BY GIT'S
# DESIGN, so the hooks live under scripts/setup/hooks/ and are installed from
# there — the tracked-source-plus-installer pattern the darktable styles and the
# fitted lens model already use.
#
# MEASURED GAP THIS CLOSES: `install_hooks.sh` was referenced by NOTHING a clone
# runs — its own usage line and one session role file, and zero mentions in this
# script. So a fresh clone had NO pre-push guard gate and NO staged-numstat stamp:
# the two mechanisms built to stop "nothing runs the guards" and to stop a
# hand-typed numstat, both present only on rigs where someone ran the installer by
# hand. The installer's own header names the clause it was violating: "a fact that
# is not reproducible from tracked files is the bug (CLAUDE.md, Environment)."
log "Layer 0 — git hooks (pre-push guard gate, staged-numstat stamp)"
run "'$(dirname "$0")/install_hooks.sh'"

# ---- Layer A: apt (signed) ------------------------------------------------
log "Layer A — apt base"
run "sudo apt update"
run "sudo apt install -y flatpak pipx golang git unzip libssl-dev"
run "pipx ensurepath"
# `astrometry-data-tycho2` is a METAPACKAGE THAT SHIPS NO INDEX FILES — MEASURED,
# `dpkg -L` returns only docs/copyright/lintian. It pulls the per-scale sub-packages,
# and on this arch the ones carrying data are the `-littleendian` variants (the
# `amd64` siblings install and ship 0 files here). The series is `index-tycho2-NN`,
# NOT the 4100 series an earlier comment and manifest note both named: MEASURED,
# `ls /usr/share/astrometry` matches `4100` ZERO times. A wrong series name in an
# inventory is a false negative waiting for whoever greps for it.
[[ $DO_DATA -eq 1 ]] && run "sudo apt install -y astrometry.net astrometry-data-tycho2 source-extractor"
# xvfb only if you must run a GUI pyscript (we avoid): sudo apt install -y xvfb
manifest astrometry.net apt apt-signed apt /usr/bin/solve-field "solve-field --help" "the SOLVER BINARY only — the index DATA is the separate row below, because this verify passes with the index dir empty"
# THE INDEX DATA IS ITS OWN ROW BECAUSE THE SOLVER'S VERIFY CANNOT SEE IT.
# `solve-field --help` exits 0 on a machine with no index files at all, so the row
# above asserted nothing about the catalogue. This verify READS an actual index:
# `query-starkd` opens the star kdtree, searches it, and `-T` pulls the tag-along
# columns — so requiring `MAG_VT` proves the file parses, the tree holds stars at
# that position, AND the catalogue magnitude column is present. That column is the
# one behind the measured zero point (ZP_V_T = 16.754, `TOOLS.md` Tier 3), which is
# why it is the right thing to assert rather than mere file existence.
# FIRE-TESTED FOUR WAYS, ~5 ms: real index exit 0; missing index, a garbage file of
# the same name, and a valid index queried where it holds no stars all exit 1.
manifest astrometry-index-tycho2 2-5 apt-signed apt /usr/share/astrometry "query-starkd -r 306 -d 42 -R 10 -T /usr/share/astrometry/index-tycho2-19.littleendian.fits | grep -q MAG_VT" "13 Tycho-2 star-kdtree indexes, index-tycho2-07..19, from the -littleendian sub-packages; the astrometry-data-tycho2 metapackage itself ships ZERO index files"
# source-extractor is the INPUT STAGE both PSFEx and SCAMP consume (Layer C3), and
# it is NOT installed explicitly anywhere: it arrives as a RECOMMENDS of
# astrometry.net above. MEASURED — `apt-cache show astrometry.net` lists it under
# Recommends (not Depends), this rig has `APT::Install-Recommends "1"` with no
# override in /etc/apt/apt.conf.d/, and dpkg marks the installed copy `auto`. It is
# recorded here because the manifest's job is to say what a clone ENDS UP WITH, and
# a transitively-acquired binary that two pinned tools depend on is exactly the
# machine-local value CLAUDE.md's Environment section warns about. THE FRAGILITY IS
# THE POINT OF THE ROW: an apt run with --no-install-recommends omits it, and the
# failure surfaces as PSFEx/SCAMP building cleanly and finding no input stage.
manifest source-extractor 2.28.2+ds-1 apt-recommends-of-astrometry.net apt /usr/bin/source-extractor "source-extractor --version" "input stage for PSFEx and SCAMP (Layer C3). NOT explicitly installed — arrives as a Recommends of astrometry.net; --no-install-recommends omits it"

# darktable + lensfun = the UNDISTORT stage (the wide-field UNTRACKED class).
# darktable must be BUILT AGAINST lensfun — Debian's is; its RawTherapee is NOT
# (no lensfun link, so no auto-match). liblensfun-bin carries lensfun-update-data:
# it is NOT in python3-lensfun (that package has only DB-path helpers and no
# matcher), and without it the DB update below cannot run.
run "sudo apt install -y darktable liblensfun-bin python3-lensfun hugin-tools"
manifest darktable apt apt-signed apt /usr/bin/darktable-cli "darktable-cli --version" "UNDISTORT stage; must be built against lensfun"
# verify is `command -v`, NOT `lensfun-update-data --help`: that binary exits 1
# unprivileged with "root privileges needed for updating the system database"
# EVEN FOR --help, so the old column could never pass as a non-root check.
# What this row asserts is that liblensfun-bin SHIPS the binary, and presence
# is exactly what `command -v` tests.
manifest lensfun apt apt-signed apt /usr/share/lensfun "command -v lensfun-update-data" "liblensfun-bin ships lensfun-update-data (NOT python3-lensfun); verify is presence-only because the binary needs root even for --help"
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
# The distortion model is per LENS and per FOCAL, fitted from a set's own
# frames, so there is nothing to install until a set exists: bootstrapping a
# rig cannot know which glass it will meet. Run it when the first
# wide-untracked set lands:
#   scripts/darktable/fit_lens_model.sh <session> <set> ...   (fit)
#   scripts/darktable/install_lens_model.sh <session> <set>   (install + strip)
log "lens model: skipped at bootstrap — per lens/focal, install it per set (see manifest note)"
manifest lensfun-db upstream lensfun-update-data n/a "$HOME/.local/share/lensfun/updates/version_1" "test -d $HOME/.local/share/lensfun/updates/version_1" "MACHINE-LOCAL: not tracked, re-run per rig; distro DB lacks recent bodies"
manifest dt-lens-styles repo scripts/darktable n/a "\${XDG_CONFIG_HOME:-\$HOME/.config}/darktable/data.db" "true" "lensdist/nodist; op_params is the pinned artifact; no GUI step"
manifest dt-lens-model repo scripts/darktable n/a "$HOME/.local/share/lensfun/updates/version_1" "true" "PER LENS+FOCAL, fitted from a set's own frames (fit_lens_model.sh) and installed with install_lens_model.sh <session> <set> — which finds the vendor DB file by searching for the lens. Nothing to install at bootstrap; re-install after every lensfun-update-data; skip when the wide-untracked class is not in play"

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

# ---- Layer B3: the ASTROMETRIC Gaia catalogue -----------------------------
# The OTHER half of the local Gaia pair. B2 above installs the PHOTOMETRIC (SPCC
# xpsamp) side; this is the one plate solving reads via `-cat=localgaia`. Its
# implementation, its pins and its `--selftest-gaia` fire test are defined above
# the guards — see the block after fetch().
log "Layer B3 — the ASTROMETRIC Gaia catalogue (plate solving, -cat=localgaia)"
if [[ $DRY -eq 1 ]]; then
  printf '  (plan) fetch   %s\n' "$GAIA_ASTRO_URL"
  printf '  (plan) verify  sha256 %.12s... on the COMPRESSED file, then %.12s... on the DECOMPRESSED one\n' \
    "$GAIA_ASTRO_BZ2_SHA" "$GAIA_ASTRO_DAT_SHA"
  printf '  (plan) install %s  (RENAMED from siril_cat_healpix8_astro.dat; the siril config is NOT touched)\n' \
    "$GAIA_ASTRO_DEST"
  printf '  (plan) re-verify at the installed path, then skip entirely on any later run\n'
  printf '  (plan) fire-test this layer without installing: %s --selftest-gaia\n' "$(basename "$0")"
else
  install_gaia_astro || { echo "[bootstrap] Layer B3 FAILED — the astrometric catalogue is NOT installed" >&2; exit 1; }
fi
manifest_gaia

# ---- Layer C: project venv (PEP 668 safe) ---------------------------------
# $VENV defaults under /opt (root-owned parent) — create with sudo, then chown to the
# invoking user so pip and later dep changes need no root and the venv is not a
# root-owned artifact the orchestration must sudo to modify.
log "Layer C — Python venv ($VENV) + pinned requirements"
run "sudo python3 -m venv '$VENV'"
run "sudo chown -R '$(id -un):$(id -gn)' '$VENV'"
run "'$VENV/bin/pip' install -U pip"
run "'$VENV/bin/pip' install -r '$(dirname "$0")/requirements.txt'"
manifest python-libs venv requirements.txt version-pins "$VENV" "'$VENV/bin/python' -c 'import astropy'" "astropy==8.0.1; requirements.txt carries VERSION pins, not hash pins, and said so in its own header while this column claimed pip-hashes — corrected. requirements.lock is the hash-capable artifact, generated by install_python_tools.sh --lock"

# ---- Layer C2: the pinned TOOL layer --------------------------------------
# Separate from Layer C because it is a different KIND of dependency: Layer C is
# the MEASUREMENT layer the repo's own scripts import (astropy/numpy/scipy/PIL) and
# breaking it breaks the chain; C2 is candidate instruments answering named open
# questions that nothing on the build path imports yet. Splitting them means a tool
# experiment cannot take the chain down with it.
log "Layer C2 — pinned Python tool layer"
run "'$(dirname "$0")/install_python_tools.sh' --go"
# Rows are EMITTED by the script and appended here rather than written by it —
# manifest.tsv is generated and a hand-added row vanishes on the next --go.
if [[ $DRY -eq 0 ]]; then "$(dirname "$0")/install_python_tools.sh" --manifest >>"$MANIFEST"; fi

# ---- Layer C2b: the PLATE-SOLVE venv ---------------------------------------
# A THIRD venv, and it is the one nothing recorded. `solve_field.py` re-execs
# itself inside ~/.local/share/astrometry-venv, which holds `sep` — CLAUDE.md's
# "the sole extractor" for the trailed-field solve, the in-house peak-centroid
# fallback having been RETIRED. It had NO manifest row, and `solve_field.py`
# created it with a bare `pip install astrometry sep astropy numpy scipy`: NO
# VERSIONS. So the extraction stage of the solve path was whatever pip resolved
# on the day a clone first solved a field.
#
# Now pinned by scripts/setup/requirements-solve.txt at the versions MEASURED on
# this rig, and created HERE so a clone gets it deterministically instead of
# lazily on first use. `solve_field.py` keeps its own bootstrap as the fallback
# and installs from the SAME pin file, refusing outright if that file is missing
# rather than silently reverting to an unpinned resolve.
log "Layer C2b — plate-solve venv (sep, the solve path's extractor)"
run "python3 -m venv '$HOME/.local/share/astrometry-venv'"
run "'$HOME/.local/share/astrometry-venv/bin/pip' install -q -r '$(dirname "$0")/requirements-solve.txt'"
manifest solve-venv venv requirements-solve.txt version-pins "$HOME/.local/share/astrometry-venv" \
  "'$HOME/.local/share/astrometry-venv/bin/python' -c 'import sep, astrometry'" \
  "the venv solve_field.py re-execs into. sep 1.4.1 is CLAUDE.md's 'sole extractor' for the trailed-field solve; was created UNPINNED until requirements-solve.txt existed"


# ---- Layer C3: the ASTROMATIC lane, built from Debian source ----------------
# WHY THIS WIRING IS THE FIX, and it is the sharpest instance of the class this
# repo keeps measuring: `install_astromatic.sh` was written expressly to close
# "VERIFIED and NOT REPRODUCIBLE FROM A CLONE" — its own header says so — and
# NOTHING CALLED IT. So the remedy for not-reproducible-from-a-clone was itself
# unreachable from a clone. PSFEx's field model is already cited in the corner
# records and in BACKLOG row 52 (the arm that validated the kappa rows 51/52/53
# all rest on), so a standing measurement was resting on a machine-local build.
#
# ROOT IS NOT WHY IT WAS OMITTED: this script already runs `sudo apt install` 23
# times, including astrometry.net, darktable, liblensfun-bin and hugin-tools. The
# astromatic lane simply needs its OWN apt line for build deps, which the script
# emits via --root-cmds rather than duplicating here.
#
# `source-extractor` IS NAMED EXPLICITLY in Layer A's apt line, and the reason is
# that it arrives transitively ONLY BY A RECOMMENDS. MEASURED: `astrometry.net`
# lists it under Recommends (NOT Depends), this rig has `APT::Install-Recommends
# "1"` with no override in /etc/apt/apt.conf.d/, and dpkg marks the installed copy
# `auto`. So on a default apt it does arrive — and ONE common hardening flag,
# `--no-install-recommends`, silently removes it. CLAUDE.md says a contributor GETS
# the environment by cloning and running this script; a dependency a single flag
# can delete does not satisfy "gets", and the failure it produces is the expensive
# shape: PSFEx and SCAMP build cleanly and find no input stage at RUN time.
# Standards-first: declare what you require rather than inheriting another
# package's judgement about what is optional.
log "Layer C3 — Astromatic lane (PSFEx, SCAMP) from Debian source"
while IFS= read -r c; do [[ -n "$c" ]] && run "$c"; done \
  < <("$(dirname "$0")/install_astromatic.sh" --root-cmds)
run "'$(dirname "$0")/install_astromatic.sh' --go"
# Rows are EMITTED by the script, same as C2 — a hand-added row vanishes on the
# next --go, which is how manifest.tsv came to omit this lane in the first place.
if [[ $DRY -eq 0 ]]; then "$(dirname "$0")/install_astromatic.sh" --manifest >>"$MANIFEST"; fi

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
# Installing the binary is NOT enough: siril's `starnet`/`seqstarnet` are gated on
# TWO config keys that a fresh flatpak leaves EMPTY, so the command fails on a rig
# where the binary is present and verified. Same class of trap as the SPCC sensor
# database. Siril's integration is the path worth having — it applies an INVERTIBLE
# MTF pre-stretch (`starnet -stretch`) so a linear stack can be separated and the
# inverse applied to both the starless and the star mask.
STARNET_W="$OPT/starnet2-${STARNET_VER}/starnet2_linux_${STARNET_VER}_ORT_x64_cli/StarNet2_weights.onnx"
if [[ $DRY -eq 1 ]]; then
  printf '  (plan) patch %s: starnet_exe / starnet_weights\n' "$SIRIL_CFG"
else
  for kv in "starnet_exe=$STARNET_BIN" "starnet_weights=$STARNET_W"; do
    k=${kv%%=*}
    if grep -q "^$k=" "$SIRIL_CFG"; then sed -i "s#^$k=.*#$kv#" "$SIRIL_CFG"
    else printf '%s\n' "$kv" >> "$SIRIL_CFG"; fi
  done
  log "siril StarNet config set (starnet_exe + starnet_weights -> /opt)"
fi
manifest starnet-config siril-flatpak-config n/a n/a "$SIRIL_CFG" \
  "grep -q 'starnet_exe=$STARNET_BIN' '$SIRIL_CFG'" \
  "MACHINE-LOCAL: siril starnet_exe + starnet_weights. EMPTY on a fresh flatpak => the siril 'starnet' command FAILS even with the binary installed"

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
# verify uses the ABSOLUTE path: the binary is installed under $OPT and is NOT
# on PATH, so a bare `nightlight version` exits 127 and the row asserted an
# install its own check could not confirm.
manifest Nightlight "$NIGHTLIGHT_VER" "gh:mlnoga/nightlight@$NIGHTLIGHT_VER" go.sum "$OPT/nightlight-0.2.6" "'$OPT/nightlight-0.2.6/nightlight' version" "dormant 2023; cross-check only; built from tag v0.2.6 but the binary self-reports 'Version 0.2.5' (upstream never bumped the string) - the TAG is the pin, not the printed version"
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
     reconcile TOOLS.md to what is actually there.
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
  # The ASTROMETRIC half. Assert the CONTENT, not the presence: a truncated or
  # half-written file exists and would pass `test -f`, and its absence was
  # originally discovered as a blocked measurement rather than as a missing file.
  check "echo '$GAIA_ASTRO_DAT_SHA  $GAIA_ASTRO_DEST' | sha256sum -c --status - && echo 'gaia astrometric catalogue present + sha256 verified'"
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
