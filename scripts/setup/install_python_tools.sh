#!/usr/bin/env bash
# install_python_tools.sh — the pinned Python tool layer, installable onto a rig
# that is ALREADY bootstrapped, and re-runnable without touching anything else.
#
# WHY THIS EXISTS SEPARATELY FROM x86_bootstrap.sh. The bootstrap installs the
# venv and its requirements as Layer C, but `x86_bootstrap.sh --go` TRUNCATES
# manifest.tsv and re-enters every layer — so "add one package" cannot be done by
# re-running it on a live rig without re-doing apt, flatpak, /opt binaries and the
# 1.5 GB Gaia catalogue. This script does the Layer-C-shaped part alone.
#
#   ./install_python_tools.sh              dry run: print the plan, change nothing
#   ./install_python_tools.sh --go         install into $VENV
#   ./install_python_tools.sh --verify     import-check every package, install nothing
#   ./install_python_tools.sh --lock       regenerate requirements.lock from the venv
#   ./install_python_tools.sh --manifest   emit manifest.tsv rows on stdout
#
# SAFETY: default is a dry run, matching x86_bootstrap.sh's own convention, so a
# stray invocation cannot touch the toolchain. NEVER uses system pip (Kali
# enforces PEP 668); everything lands in $VENV.
#
# THE MANIFEST PROBLEM, AND WHY THIS SCRIPT DOES NOT HAND-EDIT manifest.tsv.
# manifest.tsv is GENERATED — x86_bootstrap.sh truncates it with `: >"$MANIFEST"`
# on every --go. A row added here by hand would survive in git until the next
# bootstrap and then vanish silently, which is a registered defect in this repo
# (BACKLOG history: a hand-added row recreating the bug it recorded). So this
# script EMITS rows (--manifest) for the bootstrap to consume, and the pinned
# package list lives in requirements-tools.txt, which is tracked.
#
# TWO REPRODUCIBILITY DEFECTS THIS CLOSES, both measured before it was written:
#   (1) manifest.tsv's python-libs row carries `pip-hashes` in its sha256 column
#       while requirements.txt says in its own header "these are version pins, NOT
#       hash pins (UNTESTED on x86)". The manifest OVERCLAIMED. `--lock` produces
#       the artifact that makes the claim true, and until it is run the honest
#       value is `version-pins`.
#   (2) requirements.txt says "The AUTHORITATIVE lock is generated on the first
#       x86 install: pip freeze > requirements.lock". requirements.lock DOES NOT
#       EXIST. The plan was written and never executed.
set -euo pipefail

VENV="${ASTRO_VENV:-/opt/astro-venv}"
HERE="$(cd "$(dirname "$0")" && pwd)"
TOOLS_REQ="$HERE/requirements-tools.txt"
LOCK="$HERE/requirements.lock"
PIP="$VENV/bin/pip"
PY="$VENV/bin/python"

MODE=plan
for a in "$@"; do
  case "$a" in
    --go)       MODE=go ;;
    --verify)   MODE=verify ;;
    --lock)     MODE=lock ;;
    --manifest) MODE=manifest ;;
    -h|--help)  sed -n '2,30p' "$0"; exit 0 ;;
    *) echo "unknown argument: $a" >&2; exit 2 ;;
  esac
done

log(){ printf '[tools] %s\n' "$*"; }

# ---------------------------------------------------------------------------
# The roster. Each row: package  import-name  the QUESTION it unblocks.
# A tool earns a row by having a live question attached, not by being interesting
# — an installed tool nobody drives is its own kind of debt.
# ---------------------------------------------------------------------------
roster(){ cat <<'ROSTER'
sip_tpv|sip_tpv|Gates the SWarp route for BACKLOG:compose-homography-smear. SWarp cannot read SIP and drops it silently; sip_tpv's forward direction is a symbolic sympy substitution, exact to 1.118e-11 px over 3600 points and flat in field radius.
galsim|galsim|Reads a PSFEx .psf DIRECTLY and evaluates the PSF anywhere, retiring the [1,X,X2,Y,XY,Y2] basis-order trap TOOLS.md documents. Pairs with PSFEx.
astroquery|astroquery|Siril's conesearch is GUI-ONLY headless and timed out on a 20.6 deg cone; this is the standard headless Vizier/SIMBAD/Gaia client that makes that wall a non-event.
astropy_healpix|astropy_healpix|Retires the nside=2 nested cover spcc_cone.py hand-rolls — closes a declared divergence.
reproject|reproject|The astropy-native reprojector, and unlike SWarp it consumes SIP directly through astropy's WCS. Independent second arm for compose-homography-smear.
piff|piff|Models the PSF in SKY rather than pixel coordinates, which is this corpus's axis — PSF fixed in sensor coords while the sky drifts ~1000 px across it.
astropy_iers_data|astropy_iers_data|DATE-VERSIONED and arrives transitively, so it is exactly what gets left unpinned — and unpinned means the environment drifts on every rebuild.
ROSTER
}

[[ -x "$PY" ]] || { echo "[tools] $VENV is not a venv — run x86_bootstrap.sh first" >&2; exit 3; }

case "$MODE" in
plan)
  log "DRY RUN — nothing will be installed. Re-run with --go."
  log "venv: $VENV  ($("$PY" -c 'import sys;print(sys.version.split()[0])'))"
  printf '\n  %-14s %-9s %s\n' PACKAGE STATE WHY
  while IFS='|' read -r pkg imp why; do
    if "$PY" -W ignore -c "import $imp" >/dev/null 2>&1; then st=PRESENT; else st=MISSING; fi
    printf '  %-14s %-9s %s\n' "$pkg" "$st" "${why:0:96}…"
  done < <(roster)
  printf '\n'
  log "pins: $TOOLS_REQ"
  log "after --go, run --lock to regenerate $LOCK (it does not exist yet — see header)"
  ;;
go)
  log "installing into $VENV from $TOOLS_REQ"
  "$PIP" install -r "$TOOLS_REQ"
  log "verifying imports"
  fail=0
  while IFS='|' read -r pkg imp _; do
    if v=$("$PY" -W ignore -c "import $imp,sys;print(getattr($imp,'__version__','?'))" 2>&1); then
      printf '  OK    %-14s %s\n' "$pkg" "$v"
    else
      printf '  FAIL  %-14s %s\n' "$pkg" "$(printf '%s' "$v" | tail -1)"; fail=1
    fi
  done < <(roster)
  [[ $fail -eq 0 ]] || { echo "[tools] one or more imports FAILED — the install is not usable" >&2; exit 1; }
  log "all imports OK — now run --lock"
  ;;
verify)
  fail=0
  while IFS='|' read -r pkg imp _; do
    if v=$("$PY" -W ignore -c "import $imp,sys;print(getattr($imp,'__version__','?'))" 2>&1); then
      printf '  OK    %-14s %s\n' "$pkg" "$v"
    else
      printf '  FAIL  %-14s not importable\n' "$pkg"; fail=1
    fi
  done < <(roster)
  exit $fail
  ;;
lock)
  # The artifact requirements.txt promises and nobody generated. `pip freeze`
  # gives exact versions for the WHOLE resolved tree including transitive deps —
  # which is what makes a later --require-hashes install reproducible.
  log "freezing $VENV -> $LOCK"
  { printf '# GENERATED by install_python_tools.sh --lock. Do not hand-edit.\n'
    printf '# Exact resolved tree of %s, python %s.\n' "$VENV" "$("$PY" -c 'import sys;print(sys.version.split()[0])')"
    printf '# Re-install elsewhere with: pip install -r requirements.lock\n'
    "$PIP" freeze; } > "$LOCK"
  log "wrote $(wc -l < "$LOCK") lines"
  ;;
manifest)
  # TSV rows for x86_bootstrap.sh to append. Emitting rather than writing is
  # deliberate: manifest.tsv is generated and a hand-added row vanishes silently.
  while IFS='|' read -r pkg imp why; do
    v=$("$PY" -W ignore -c "import $imp;print(getattr($imp,'__version__','unknown'))" 2>/dev/null || echo NOT-INSTALLED)
    printf '%s\t%s\tpypi\tversion-pins\t%s\t%s\t%s\n' \
      "$pkg" "$v" "$VENV" "'$PY' -c 'import $imp'" "$why"
  done < <(roster)
  ;;
esac
