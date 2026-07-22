#!/usr/bin/env bash
# Build the session's MASTER DARK from raw darks/ — drives the pinned Siril
# template (scripts/stack/siril/master_dark.ssf: convert -> `stack rej 3 3
# -nonorm`, 16-bit intermediates policy) headless, for the Tier-1 registry
# and standalone prep. The sky-flat builder and the undistort calibrate both
# consume the product at work/masters/dark_master.fit.
#
#   build_master_dark.sh <session-dir> [--force]
#
# Degrades loudly: no darks/ dir, too few frames, or an existing master
# without --force is a hard stop. LEAVES BEHIND: the master + the siril log
# (work/master_dark.log). CLEANS: the converted dark_*.fit sequence (a
# ~10 GB-class transient at 200+ frames) once the master is written.
set -euo pipefail
REPO=$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)
S=${1:?usage: build_master_dark.sh <session-dir> [--force]}
FORCE=
for a in "${@:2}"; do case "$a" in
  --force) FORCE=1;;
  *) echo "unknown arg $a" >&2; exit 1;;
esac; done
S=$(cd "$S" && pwd)
[ -d "$S/darks" ] || { echo "no darks/ under $S" >&2; exit 1; }
n=$(find "$S/darks" -maxdepth 1 -type f \( -iname '*.nef' -o -iname '*.dng' \
  -o -iname '*.cr2' -o -iname '*.cr3' -o -iname '*.arw' -o -iname '*.raf' \
  -o -iname '*.fit' -o -iname '*.fits' \) | wc -l)
[ "$n" -ge 8 ] || { echo "only $n raw/FITS frames in darks/ — need >=8 for a rejection master" >&2; exit 1; }
OUT=$S/work/masters/dark_master.fit
if [ -e "$OUT" ] && [ -z "$FORCE" ]; then
  echo "master exists: $OUT (use --force to rebuild)" >&2; exit 1
fi
mkdir -p "$S/work/masters"
echo "master dark: $n frames -> $OUT"
flatpak run --command=siril-cli org.siril.Siril -d "$S" \
  -s "$REPO/scripts/stack/siril/master_dark.ssf" \
  > "$S/work/master_dark.log" 2>&1 \
  || { echo "master dark build FAILED — $S/work/master_dark.log" >&2
       tail -5 "$S/work/master_dark.log" >&2; exit 1; }
[ -f "$OUT" ] || { echo "siril exited clean but wrote no master — $S/work/master_dark.log" >&2; exit 1; }
rm -f "$S"/work/dark_*.fit "$S"/work/dark_.seq
echo "=== DONE: $OUT ($n darks, rej 3 3, -nonorm) ==="
ls -la "$OUT"
