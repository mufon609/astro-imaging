#!/usr/bin/env bash
# install_cosmicclarity.sh — install the Cosmic Clarity Suite to /opt, USER-OWNED.
#
# Resolves the x86_bootstrap.sh "Cosmic Clarity: NOT installed" TODO. Kept separate
# because the suite is a multi-GB manual download (no stable URL to pin), so it is
# staged by hand and this script only PLACES + VERIFIES what was downloaded.
#
# WHY USER-OWNED, not root like the other /opt tools. MEASURED on this rig: the
# Cosmic Clarity CLIs have NO --input/--output flags. They read `input/` and write
# `output/` RELATIVE TO THE BINARY'S OWN DIRECTORY (folder-batch), ignoring the cwd
# entirely — a run from a separate work dir processed the binary's own input/ and
# wrote to the binary's own output/. A root-owned tree would therefore not be
# writable by the processing user, and orchestration would need sudo per frame. So
# the tree is chowned to the invoking user (the same sudo-create-then-chown pattern
# the venv uses). Orchestration stages each frame INTO input/, runs, and collects
# from output/ — a wrapper's job, not this installer's.
#
# WHAT IS INSTALLED (this "AlternateBuild" = the official CUDA full-suite bundle;
# its satellite binary is byte-identical to the official GitHub asset — verified):
#   WORKS CPU-only (--disable_gpu), inference verified on this rig:
#     SetiAstroCosmicClarity          Sharpen  V6.5 AI3.5s   (45s/1200px frame)
#     SetiAstroCosmicClarity_denoise  Denoise  V6.6 AI3.6    (21s/1200px frame;
#                                     carries the FREE chroma path
#                                     --color_denoise_strength, TOOLS.md's free
#                                     chroma-gap fill — 29% bg noise cut, structure kept)
#     setiastrocosmicclarity_darkstar Dark Star (v2.0/v2.1/v2.1c models all present,
#                                     v2.1c byte-identical to official)
#   BROKEN in this bundle — a DOCUMENTED GAP, not installed as working:
#     setiastrocosmicclarity_satellite  } official binaries, but the bundle's own
#     setiastrocosmicclarity_superres   } frozen torch runtime raises
#       AttributeError: module 'torch._C._sparse' has no attribute '_spsolve'
#     (the community AMD/ROCm rebuild runs them, but it is a third-party rebuild —
#     the geeksville-GraXpert precedent — so it is NOT adopted. See TOOLS.md.)
#
# USAGE (run WITH sudo; it chowns back to you):
#   sudo scripts/setup/install_cosmicclarity.sh [SRC_DIR] [DEST]
#   SRC_DIR default: ./cosmic/extracted/CosmicClaritySuite_Linux (repo-root-relative)
#   DEST    default: /opt/cosmicclarity-6.6
set -euo pipefail

SRC="${1:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)/cosmic/extracted/CosmicClaritySuite_Linux}"
DEST="${2:-/opt/cosmicclarity-6.6}"
OWNER="${SUDO_USER:-$(id -un)}"          # who to hand ownership to (folder-batch write)

[[ "$(uname -m)" == "x86_64" ]] || { echo "REFUSING: not x86_64."; exit 1; }
[[ $EUID -eq 0 ]] || { echo "Run with sudo (it chowns the tree back to \$SUDO_USER)."; exit 1; }
[[ -d "$SRC" ]] || { echo "SRC not found: $SRC (extract the suite tarball first)."; exit 1; }
[[ -x "$SRC/SetiAstroCosmicClarity_denoise" ]] || { echo "SRC has no denoise binary — wrong dir?"; exit 1; }

echo "[cc] installing $SRC -> $DEST (owner: $OWNER)"
# input/output are staging dirs, never ship test frames into /opt:
rm -f "$SRC"/input/* "$SRC"/output/* 2>/dev/null || true
mkdir -p "$DEST"
cp -a "$SRC"/. "$DEST"/
mkdir -p "$DEST/input" "$DEST/output"
chown -R "$OWNER":"$(id -gn "$OWNER")" "$DEST"     # folder-batch write access, no sudo at run time

echo "[cc] verify (CPU, headless) — the working tools must answer, as $OWNER:"
fail=0
for probe in \
  "SetiAstroCosmicClarity --help" \
  "SetiAstroCosmicClarity_denoise --help" \
  "setiastrocosmicclarity_darkstar --help"; do
  bin="${probe%% *}"
  if sudo -u "$OWNER" bash -c "cd '$DEST' && ./$probe" 2>&1 | grep -q 'usage:'; then
    echo "  OK   $bin"
  else
    echo "  FAILED $bin"; fail=1
  fi
done
echo "[cc] NOTE: satellite + superres are a documented GAP (bundle torch runtime "
echo "     broken) — not verified here on purpose. See TOOLS.md."
[[ $fail -eq 0 ]] && echo "[cc] DONE — $DEST" || { echo "[cc] VERIFY FAILURES above"; exit 1; }
