#!/usr/bin/env bash
# Install the measured distortion model for the NIKKOR Z 24-70mm f/4 S @ 70 mm
# into the live lensfun user DB (the one darktable reads).
#
# Why a fitted entry replaces the community one: the community ptlens profile is
# right at the field corner (agrees with this fit to 0.06 px at r=2664) but
# overcorrects the paraxial/mid region by 2.4-3.9 px (r=200-1000). On a
# far-drifting untracked set that error is crossed by the optical axis and
# smears an along-drift band through frame centre; with this entry the centre
# station sits at the in-exposure floor and the whole frame sharpens
# (docs/dead-ends.md, paraxial-band entry; datasets/.../experiments.jsonl
# paraxial_model_source). Values were fitted from this unit's own frames at
# infinity focus by Hugin (scripts/darktable/fit_lens_model.sh).
#
# The target file is the machine-local lensfun updates DB
# (~/.local/share/lensfun/updates/version_1 — written by `lensfun-update-data`,
# which the route already requires per rig). `lensfun-update-data` OVERWRITES
# this patch: re-run this script after any DB update. Idempotent; STOPS loudly
# if the entry matches neither the community nor the fitted line (upstream
# drift — re-fit or reconcile before trusting a render).
#
# Removal conditions: an upstream lensfun entry measured for THIS unit at
# infinity focus, or a chain that consumes the model another way
# (Siril `register -disto=` with a trustworthy source). Re-fit and re-install
# on any lens/body change, and per focal length used.
set -euo pipefail
DB="$HOME/.local/share/lensfun/updates/version_1/mil-nikon.xml"
COMMUNITY='<distortion model="ptlens" focal="70" a="0.012" b="-0.017" c="0.039"/>'
FITTED='<distortion model="ptlens" focal="70" a="0.00350093" b="0.01453356" c="0.00043983"/>'
A=${1:-}; B=${2:-}; C=${3:-}
if [ -n "$A" ]; then
  [ -n "$B" ] && [ -n "$C" ] || { echo "usage: install_lens_model.sh [a b c]  (no args = pinned values)" >&2; exit 1; }
  FITTED="<distortion model=\"ptlens\" focal=\"70\" a=\"$A\" b=\"$B\" c=\"$C\"/>"
fi
[ -f "$DB" ] || { echo "install_lens_model: $DB missing — run lensfun-update-data first (the DB that carries the Z6III)" >&2; exit 1; }

if grep -qF "$FITTED" "$DB"; then
  echo "install_lens_model: fitted entry already installed"
elif grep -qF "$COMMUNITY" "$DB"; then
  python3 - "$DB" "$COMMUNITY" "$FITTED" <<'PY'
import sys
p, old, new = sys.argv[1], sys.argv[2], sys.argv[3]
s = open(p).read()
assert s.count(old) == 1, "expected exactly one community focal=70 ptlens line for this lens"
open(p, "w").write(s.replace(old, new))
PY
  echo "install_lens_model: fitted entry installed (community focal=70 line replaced)"
else
  echo "install_lens_model: the DB carries NEITHER the known community entry NOR the fitted one." >&2
  echo "Upstream drift — re-fit (fit_lens_model.sh) or reconcile before rendering this class." >&2
  exit 1
fi
grep -n 'model="ptlens" focal="70"' "$DB" | head -3
