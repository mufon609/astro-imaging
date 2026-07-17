#!/usr/bin/env bash
# Install the measured distortion model for the NIKKOR Z 24-70mm f/4 S @ 70 mm
# into the live lensfun user DB (the one darktable reads).
#
# Why a fitted entry replaces the community one: the community ptlens profile
# agrees with this fit at the field corner (0.06 px at r=2664) but diverges from
# it by 2.4-3.9 px through the paraxial/mid region (r=200-1000) — the error the
# A/B then confirmed empirically. On a
# far-drifting untracked set that error is crossed by the optical axis and
# smears an along-drift band through frame centre; with this entry the centre
# station sits at the in-exposure floor and the whole frame sharpens
# (docs/dead-ends.md, paraxial-band entry; datasets/.../experiments.jsonl
# paraxial_model_source). Values were fitted from this unit's own frames at
# infinity focus by Hugin (scripts/darktable/fit_lens_model.sh).
#
# This script also STRIPS the <vignetting> and <tca> calibrations from this
# lens's block. That is what makes the warp DISTORTION-ONLY: darktable ignores
# a style's lens op_params (only the enabled bit carries) and applies its
# default correction set, so the correction set can only be chosen in the data
# lensfun reads — with vignetting/tca absent, distortion is the only
# correction darktable CAN apply. Vignetting correction here would
# double-correct lights already flat-corrected upstream (docs/dead-ends.md).
#
# The target file is the machine-local lensfun updates DB
# (~/.local/share/lensfun/updates/version_1 — written by `lensfun-update-data`,
# which the route already requires per rig). `lensfun-update-data` OVERWRITES
# this patch: re-run this script after any DB update. Idempotent; STOPS loudly
# if the entry matches neither the community nor the fitted line (upstream
# drift — re-fit or reconcile before trusting a render).
#
# Verify after any darktable/lensfun version change: a uniform gray card
# warped through the `lensdist` style must keep corner medians == centre
# (Siril `stat`); a changed corner median means vignetting is back in the path.
#
# Removal conditions: an upstream lensfun entry measured for THIS unit at
# infinity focus, or a chain that consumes the model another way
# (Siril `register -disto=` with a trustworthy source). The vignetting/tca
# strip retires when darktable honors a style's lens op_params headless
# (re-check the uniform-card test per darktable version bump). Re-fit and
# re-install on any lens/body change, and per focal length used.
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

# Distortion-only enforcement (see header): strip vignetting/tca from this
# lens's block so darktable's ignore-the-style-params behavior cannot apply them.
python3 - "$DB" <<'PY'
import re, sys
p = sys.argv[1]
xml = open(p).read()
m = re.search(r'(<lens>(?:(?!</lens>).)*?24-70mm f/4 S(?:(?!</lens>).)*?</lens>)', xml, re.S)
assert m, "24-70mm f/4 S lens block not found — upstream drift, reconcile before rendering"
block = m.group(1)
stripped = re.sub(r'\s*<(?:vignetting|tca)\b[^>]*/>', '', block)
stripped = re.sub(r'\s*<!-- Taken with Nikon Z6 -->', '', stripped)
if stripped == block:
    print("install_lens_model: vignetting/tca already absent — distortion-only holds")
else:
    n = len(re.findall(r'<(?:vignetting|tca)\b', block))
    assert '<distortion' in stripped, "strip would leave no distortion model — refusing"
    open(p, "w").write(xml.replace(block, stripped))
    print(f"install_lens_model: stripped {n} vignetting/tca entries — this lens is now distortion-only in the DB")
PY
grep -n 'model="ptlens" focal="70"' "$DB" | head -3
