#!/usr/bin/env bash
# Fetch the two PINNED spectral-response sources the spcc-sensor-curve proxies
# are converted from (BACKLOG:spcc-sensor-curve stage 1; docs/spcc-sensor-curve-z6iii.md
# section 1.4 / 1.5) into a machine-local cache and verify every byte by sha256.
#
#   fetch_sources.sh [<cache-dir>]      default $HOME/.cache/astro-imaging/spcc_curves
#
# Pinned to a commit, never a branch: a curve that changes upstream must change
# its sha here, or the conversion record (RECORD.json) no longer describes what
# was installed. Exits non-zero on any mismatch; a mismatch is NOT retried.
#
# 1. Nikon Z f — Weta Digital physlight camera SSF, republished in ASWF
#    rawtoaces-data (Apache-2.0; the LICENSE is fetched beside it and kept with
#    the converted files). 380-780 nm at 5 nm, units "relative".
# 2. Nikon Z 6 — Glenn Butcher's ssf-data, DIY transmissive-grating spectroscope
#    + ssftool, measured through the NIKKOR Z 24-70mm f/4 S (this project's lens
#    model). CC BY-NC-SA 4.0: fetched and converted locally, NEVER tracked or
#    redistributed by this repo.
set -euo pipefail
CACHE=${1:-$HOME/.cache/astro-imaging/spcc_curves}
mkdir -p "$CACHE"

ZF_COMMIT=cf6452c3ce44112f6cf3f1c2d7bf6381a4c90638
ZF_BASE=https://raw.githubusercontent.com/AcademySoftwareFoundation/rawtoaces-data/$ZF_COMMIT
Z6_COMMIT=dce9021f98bc28942a8f84ca3cdb5e791f3a1931
Z6_BASE=https://raw.githubusercontent.com/butcherg/ssf-data/$Z6_COMMIT/Nikon/Z6/spectroscope

# url  local-name  sha256 (measured at first fetch, 2026-08-29)
SOURCES="
$ZF_BASE/data/camera/Nikon_Z_f_380_780_5.json Nikon_Z_f_380_780_5.json ba357c75362fdcdba789a445b77ef6ffdd2ee6a713200ca00dcc94e9ca38f4ec
$ZF_BASE/LICENSE rawtoaces-data-LICENSE c71d239df91726fc519c6eb72d318ec65820627232b2f796219e87dcf35d0ab4
$Z6_BASE/Nikon_Z6_ssf.csv Nikon_Z6_ssf.csv 6cb4dc7b550acd6c3793f13b0a188145ccc3fcb2e50d559c4c37c06e181bb642
$Z6_BASE/README.md Nikon_Z6_README.md 17ba60d99cf514343249bf744f3080f16d482d2827f7dc36df29082325284234
"
rc=0
while read -r url name sum; do
  [ -n "$url" ] || continue
  dst=$CACHE/$name
  if [ ! -f "$dst" ]; then
    curl -sSL --fail -o "$dst.part" "$url" && mv "$dst.part" "$dst"
  fi
  got=$(sha256sum "$dst" | cut -d' ' -f1)
  if [ "$got" = "$sum" ]; then
    echo "ok      $name  $got"
  else
    echo "MISMATCH $name  expected $sum  got $got  ($url)" >&2
    rc=1
  fi
done <<< "$SOURCES"
date -u +%Y-%m-%dT%H:%M:%SZ > "$CACHE/fetched_at.txt"
exit $rc
