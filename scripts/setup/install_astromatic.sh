#!/usr/bin/env bash
# install_astromatic.sh — PSFEx and SCAMP, built from the Debian SOURCE packages
# into a user-owned prefix. Lane (b) of the two lanes this rig has.
#
#   ./install_astromatic.sh              dry run: print the plan, change nothing
#   ./install_astromatic.sh --root-cmds  print ONLY the commands needing sudo
#   ./install_astromatic.sh --go         fetch, build and install into $PREFIX
#   ./install_astromatic.sh --verify     run each binary, install nothing
#   ./install_astromatic.sh --manifest   emit manifest.tsv rows on stdout
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
# TWO DEBIAN BUILD-DEPS DO NOT EXIST ON KALI, AND NEITHER IS ACTUALLY REQUIRED.
# The Debian control files list `libatlas-base-dev` and `libplplot-dev`; on this
# rig `apt-get install` returns "has no installation candidate" for both, and
# `apt-cache search plplot` returns NOTHING — PLplot is absent from the archive
# entirely, not merely renamed. Both are optional to these builds:
#   libatlas-base-dev  -> ATLAS is one BLAS choice. `libatlas3-base` is now only a
#                         TRANSITIONAL package. Both configure.ac files offer
#                         `--enable-openblas` as a first-class alternative, so we
#                         build against `libopenblas-dev` (0.3.33+ds-3) instead.
#   liblapacke-dev     -> NOT in the Debian Build-Depends at all, and required
#                         anyway: configure looks for LAPACKE_dpotrf, which Kali's
#                         OpenBLAS does NOT bundle (nm on libopenblas.so: 0 hits;
#                         on liblapacke.so.3: 4). The RUNTIME is already present;
#                         only the dev headers and .so symlink are missing.
#   libplplot-dev      -> `--enable-plplot` is OPT-IN in both, and PLplot drives
#                         only the diagnostic CHECK-PLOTS. Omitting it costs the
#                         PNG/PS diagnostic output and nothing computational — the
#                         .psf model, the .head solutions and the XML are unaffected.
# Recorded because the Debian dep list reads as mandatory and is not, and a reader
# who trusts it concludes these cannot be built here. They can.
#
# CFLAGS="-fcommon" IS REQUIRED, not cosmetic. Both sources predate GCC 10, which
# made `-fno-common` the default: they rely on tentative definitions, so the link
# fails with "multiple definition of `gstr'" / "`bswapflag'" against the bundled
# libfits. Compilation succeeds and only the LINK fails, so the error appears late
# and looks like a source bug rather than a toolchain default.
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
BUILD_DEPS=(autoconf automake libtool libopenblas-dev liblapacke-dev libfftw3-dev libshp-dev libcurl4-openssl-dev pkg-config)

# Debian multiarch puts the BLAS/LAPACKE headers and libraries under
# /usr/include/<triplet> and /usr/lib/<triplet>, and neither configure searches
# there — MEASURED: with libopenblas-dev installed, configure still exits
# "OpenBLAS header files not found". Detected rather than hardcoded so this works
# on a rig with a different triplet.
MULTIARCH="$(dpkg-architecture -qDEB_HOST_MULTIARCH 2>/dev/null || echo x86_64-linux-gnu)"
BLAS_INC="$WORK/blas-inc"
BLAS_LIB="$WORK/blas-shim"

# THE SHIM, AND IT IS NOT A HACK — it is the standard ld linker-script mechanism.
# Both configures search ONLY -lopenblas / -lopenblasp for LAPACKE_dpotrf, because
# upstream OpenBLAS bundles LAPACKE. Debian SPLITS them: MEASURED, `nm -D` on
# libopenblas.so gives 0 hits for LAPACKE_dpotrf and on liblapacke.so.3 gives 4.
# Passing LIBS="-llapacke" does not survive into the check (AC_SEARCH_LIBS resets
# it), so the portable fix is a one-line GROUP script named libopenblas.so that
# resolves -lopenblas to BOTH real libraries. Verified: a bare LAPACKE_dpotrf link
# fails against the system libdir and succeeds through the shim.

MODE=plan
for a in "$@"; do
  case "$a" in
    --go)         MODE=go ;;
    --verify)     MODE=verify ;;
    --root-cmds)  MODE=rootcmds ;;
    --manifest)   MODE=manifest ;;
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
  mkdir -p "$WORK" "$PREFIX" "$BLAS_LIB"
  printf 'GROUP ( /usr/lib/%s/libopenblas.so /usr/lib/%s/liblapacke.so )\n' \
    "$MULTIARCH" "$MULTIARCH" > "$BLAS_LIB/libopenblas.so"
  # The headers are SPLIT too and configure takes ONE incdir: cblas.h and
  # openblas_config.h live under /usr/include/$MULTIARCH while lapacke*.h live at
  # /usr/include. configure bakes the incdir into config.h as LAPACKE_H, so a
  # single wrong directory fails at COMPILE time rather than configure time.
  mkdir -p "$BLAS_INC"
  for h in "/usr/include/$MULTIARCH"/cblas.h "/usr/include/$MULTIARCH"/openblas_config.h \
           /usr/include/lapacke.h /usr/include/lapacke_config.h /usr/include/lapacke_mangling.h \
           /usr/include/lapack.h; do
    [[ -e "$h" ]] && ln -sf "$h" "$BLAS_INC/$(basename "$h")"
  done
  for p in "${PKGS[@]}"; do
    log "=== $p ==="
    ( cd "$WORK" && rm -rf "$p"-* && apt-get source "$p" >/dev/null 2>&1 )
    d=$(find "$WORK" -maxdepth 1 -type d -name "$p-*" | head -1)
    [[ -n "$d" ]] || { echo "[astromatic] apt-get source $p produced nothing" >&2; exit 4; }
    ( cd "$d" && ./autogen.sh >/dev/null 2>&1 || autoreconf -i >/dev/null 2>&1 || true
      ./configure --prefix="$PREFIX" --enable-openblas \
        --with-openblas-incdir="$BLAS_INC" --with-openblas-libdir="$BLAS_LIB" \
        CFLAGS="-fcommon -O2" >/dev/null
      make -j"$(nproc)" >/dev/null
      make install >/dev/null )
    log "$p installed into $PREFIX/bin"
  done
  log "add to PATH if not already:  export PATH=\"$PREFIX/bin:\$PATH\""
  "$0" --verify
  ;;
manifest)
  # Emitted rather than written: manifest.tsv is GENERATED by x86_bootstrap.sh and
  # a hand-added row vanishes on the next --go.
  for p in "${PKGS[@]}"; do
    b="$PREFIX/bin/$p"; [[ -x "$b" ]] || b="$(command -v "$p" 2>/dev/null || true)"
    v=$([[ -n "$b" ]] && "$b" -v 2>&1 | head -1 | grep -oE '[0-9]+\.[0-9]+\.[0-9]+' | head -1 || echo NOT-INSTALLED)
    case "$p" in
      psfex) n="spatially-varying PSF model; its field model independently confirmed the corner degradation. Built --enable-openblas + CFLAGS=-fcommon, with a BLAS/LAPACKE linker-script shim (Debian splits LAPACKE out of OpenBLAS) and an include shim (cblas.h multiarch, lapacke.h not)" ;;
      scamp) n="writes PV%d_%d TPV headers — VERIFIED in the built binary — which is the format SWarp reads and that sip_tpv converts our SIP into. SExtractor -> SCAMP -> SWarp is the canonical Astromatic chain. Same build flags as psfex" ;;
    esac
    printf '%s\t%s\tdebian-source\tapt-source\t%s\t%s\t%s\n' "$p" "$v" "$b" "$p -v" "$n"
  done
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
