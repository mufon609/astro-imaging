#!/usr/bin/env bash
# install_astromatic.sh — PSFEx and SCAMP, built from the Debian SOURCE packages
# into a user-owned prefix. Lane (b) of the two lanes this rig has.
#
#   ./install_astromatic.sh              dry run: print the plan, change nothing
#   ./install_astromatic.sh --root-cmds  print ONLY the commands needing sudo
#   ./install_astromatic.sh --go         fetch, build and install into $PREFIX
#   ./install_astromatic.sh --verify     run each binary, install nothing
#
# ROOT IS NEEDED EXACTLY ONCE, FOR BUILD DEPENDENCIES, AND NOTHING ELSE.
# `--root-cmds` prints that one apt line. After it has been run, everything below
# is unprivileged: `apt-get source` needs no root, ./configure --prefix into a
# user-owned directory needs no root, and `make install` there needs no root.
#
# WHY SOURCE RATHER THAN A BINARY .deb. PSFEx already runs on this rig — as a
# scratchpad extraction of a bookworm binary driven through LD_LIBRARY_PATH — and
# its output is ALREADY CITED in our records: the field model that independently
# confirmed the corner degradation (FWHM 1.95 px centre to 3.2 px corner, a
# different algorithm sharing no code with Siril) and the "degree 2 to 3 barely
# moves it" result. That is the same gap `sip_tpv` had before today: VERIFIED and
# NOT REPRODUCIBLE FROM A CLONE. A pinned source build inside the distro's own
# packaging fixes that; an extraction into a scratchpad does not.
#
# WHY SCAMP IS HERE, since the register argues against it. It argues against the
# PHOTOMETRIC half, correctly — `src/preflist.h` carries five astrometric
# order/degree parameters and NO photometric analogue of DISTORT_DEGREES, so its
# photometric solution is a scalar per exposure per instrument and cannot satisfy
# the position-dependent condition in `object_tilt.py`'s row. That judged the wrong
# half. MEASURED in `src/fitswcs.c`: SCAMP writes `PV%d_%d` keywords and carries
# "TPV" in its pcode list — so it is the NATIVE PRODUCER of exactly the format
# SWarp reads (`fitswcs.c:801`, `:843`) and that `sip_tpv` converts our SIP into.
# SExtractor -> SCAMP -> SWarp, all speaking TPV, is the canonical Astromatic
# chain and it is the documented industry answer to BACKLOG:`compose-homography-smear`.
#
# THE CONSTRAINT THAT PUT THESE IN THEIR OWN SCRIPT — MEASURED, not assumed:
# `autoconf`, `automake` and `libtool` are ABSENT on this rig (`make` and `gcc` are
# present), and both packages are autotools-based. Without them `apt-get source` +
# build fails at the bootstrap step, which is why PSFEx went in as an extracted
# binary in the first place. This script refuses rather than half-building.
set -euo pipefail

PREFIX="${ASTROMATIC_PREFIX:-$HOME/.local}"
WORK="${ASTROMATIC_WORK:-$HOME/.cache/astromatic-build}"
PKGS=(psfex scamp)
BUILD_DEPS=(autoconf automake libtool libatlas-base-dev libfftw3-dev libplplot-dev libshp-dev libcurl4-openssl-dev pkg-config)

MODE=plan
for a in "$@"; do
  case "$a" in
    --go)         MODE=go ;;
    --verify)     MODE=verify ;;
    --root-cmds)  MODE=rootcmds ;;
    -h|--help)    sed -n '2,20p' "$0"; exit 0 ;;
    *) echo "unknown argument: $a" >&2; exit 2 ;;
  esac
done
log(){ printf '[astromatic] %s\n' "$*"; }

missing_deps(){
  local m=()
  for p in "${BUILD_DEPS[@]}"; do
    dpkg -s "$p" >/dev/null 2>&1 || m+=("$p")
  done
  printf '%s\n' "${m[@]}"
}

case "$MODE" in
rootcmds)
  # The ONLY privileged step. Printed alone so it can be reviewed and run by hand.
  echo "sudo apt-get update"
  echo "sudo apt-get install -y ${BUILD_DEPS[*]}"
  ;;
plan)
  log "DRY RUN — nothing will be fetched or built. Re-run with --go."
  log "prefix: $PREFIX     build dir: $WORK"
  mapfile -t miss < <(missing_deps)
  if [[ ${#miss[@]} -gt 0 && -n "${miss[0]}" ]]; then
    log "BUILD DEPS MISSING (${#miss[@]}): ${miss[*]}"
    log "these need ROOT — run:  $0 --root-cmds"
  else
    log "build deps: all present — --go will work unprivileged"
  fi
  for p in "${PKGS[@]}"; do
    v=$(apt-cache showsrc "$p" 2>/dev/null | awk '/^Version:/{print $2; exit}')
    printf '  %-8s source %-12s installed: %s\n' "$p" "${v:-NOT-FOUND}" \
      "$(command -v "$p" || command -v "${p^^}" || echo no)"
  done
  ;;
go)
  mapfile -t miss < <(missing_deps)
  if [[ ${#miss[@]} -gt 0 && -n "${miss[0]}" ]]; then
    echo "[astromatic] REFUSING: build deps missing: ${miss[*]}" >&2
    echo "[astromatic] run '$0 --root-cmds' and execute those, then re-run --go." >&2
    echo "[astromatic] half-building autotools sources is how PSFEx ended up as a" >&2
    echo "[astromatic] scratchpad binary extraction in the first place." >&2
    exit 3
  fi
  mkdir -p "$WORK" "$PREFIX"
  for p in "${PKGS[@]}"; do
    log "=== $p ==="
    ( cd "$WORK" && rm -rf "$p"-* && apt-get source "$p" >/dev/null 2>&1 )
    d=$(find "$WORK" -maxdepth 1 -type d -name "$p-*" | head -1)
    [[ -n "$d" ]] || { echo "[astromatic] apt-get source $p produced nothing" >&2; exit 4; }
    ( cd "$d" && ./autogen.sh >/dev/null 2>&1 || autoreconf -i >/dev/null 2>&1 || true
      ./configure --prefix="$PREFIX" >/dev/null
      make -j"$(nproc)" >/dev/null
      make install >/dev/null )
    log "$p installed into $PREFIX/bin"
  done
  log "add to PATH if not already:  export PATH=\"$PREFIX/bin:\$PATH\""
  "$0" --verify
  ;;
verify)
  fail=0
  for p in "${PKGS[@]}"; do
    b=""
    for cand in "$PREFIX/bin/${p^^}" "$PREFIX/bin/$p" "$(command -v "${p^^}" 2>/dev/null)" "$(command -v "$p" 2>/dev/null)"; do
      [[ -n "$cand" && -x "$cand" ]] && { b="$cand"; break; }
    done
    if [[ -n "$b" ]]; then
      printf '  OK    %-8s %s\n' "$p" "$("$b" -v 2>&1 | head -1)"
    else
      printf '  FAIL  %-8s not found in %s/bin or on PATH\n' "$p" "$PREFIX"; fail=1
    fi
  done
  exit $fail
  ;;
esac
