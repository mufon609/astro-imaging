#!/usr/bin/env bash
# Finish a stacked FITS into a JUDGEABLE render: plate-solve -> SPCC colour
# calibration -> linked auto-stretch -> full-frame 16-bit PNG. This is the
# render-chain finish stage; every pixel op is an official tool (astrometry.net
# solve, Siril SPCC, Siril autostretch/savepng) and this only orchestrates them.
#
#   finish_render.sh <stack.fit> <png-name> [--session=D --set=S] [--ra=R --dec=D --radius-deg=N]
#                    [--central=F] [--crop-record=J]
#
# Output: web/results/<session>/judge/<png-name>_spcc-linked.png (16-bit, full-frame,
# colour-calibrated, linked stretch — the surface the user judges). Intermediates
# <stack>_wcs.fit and <stack>_spcc.fit are kept beside the stack.
#
# --session/--set route the SPCC run: the set's recipe.json "spcc" block (if
# any) resolves the sensor spec, and the K-factor record lands under the RIGHT
# set's name in <session>/work/spcc_<set>_<tag>.{json,log} (one predictable
# place per result). --session resolves like before: relative to the CWD.
#
# SPCC uses the sensor-null generic default (the sp168 precedent) unless a set
# recipe carries a sensor spec; K factors are captured to work/spcc_<name>.json.
# The linked stretch is MANDATORY after SPCC (unlinked autostretch on a
# calibrated stack is the chroma-blotch engine — docs/dead-ends.md).
set -euo pipefail
REPO=$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)
STACK=${1:?usage: finish_render.sh <stack.fit> <png-name> [--ra= --dec= --radius-deg=]}
NAME=${2:?missing <png-name>}
shift 2
RA=310 DEC=47 RAD=40 SESSION=sessions/july14 SET=set-01 CENTRAL= CROPREC= FIELDW=
for a in "$@"; do case "$a" in
  --ra=*) RA=${a#*=};; --dec=*) DEC=${a#*=};; --radius-deg=*) RAD=${a#*=};;
  --session=*) SESSION=${a#*=};; --set=*) SET=${a#*=};;
  --central=*) CENTRAL=${a#*=};;
  --crop-record=*) CROPREC=${a#*=};;
  *) echo "unknown arg $a" >&2; exit 1;;
esac; done
[ -f "$STACK" ] || { echo "no such stack: $STACK" >&2; exit 1; }
STACK=$(cd "$(dirname "$STACK")" && pwd)/$(basename "$STACK")

# The item-12 CONSUME side: apply a user-drawn, VERIFIED framing to the
# LINEAR stack before anything else (crop-before-stretch doctrine; the
# record's siril args target the source product's canvas — checked). An
# unverified record is refused loudly.
if [ -n "${CROPREC:-}" ]; then
  [ -f "$CROPREC" ] || { echo "no such framing record: $CROPREC" >&2; exit 1; }
  ARGS=$(python3 - "$CROPREC" "$STACK" <<'PY'
import json, sys
rec, stack = sys.argv[1], sys.argv[2]
r = json.load(open(rec))
if r.get("status") != "verified":
    sys.exit(f"finish_render: framing record status is '{r.get('status')}' — "
             "a render must refuse an unverified framing "
             "(run web/verify_framing.py first)")
from astropy.io import fits
h = fits.getheader(stack)
canvas = [int(h["NAXIS1"]), int(h["NAXIS2"])]
if list(r.get("canvas_wh") or []) != canvas:
    sys.exit(f"finish_render: record canvas {r.get('canvas_wh')} does not "
             f"match stack {canvas} — wrong product for this framing")
print(*r["rect_siril_crop_args"])
# A Siril-cropped stack carries no FOCALLEN/XPIXSZ, and the solver's
# wide-field fallback scales grind on a sub-union field — so the crop's
# true field width comes from the record's own RA/Dec corners (the first
# horizontal edge pair; astropy does the spherical math).
c = r.get("radec_corners_deg")
if c and len(c) == 4:
    from astropy.coordinates import SkyCoord
    a = SkyCoord(c[0][0], c[0][1], unit="deg")
    b = SkyCoord(c[1][0], c[1][1], unit="deg")
    print(f"{a.separation(b).arcmin:.1f}")
else:
    print("")
PY
) || exit 1
  { read -r CX CY CW CH; read -r FIELDW; } <<< "$ARGS"
  CROPPED=$(dirname "$STACK")/stack_${NAME}.fit
  # The cropped stack is a NEW product: writing it onto the input (a <png-name>
  # equal to the source stem) or onto any existing stack would destroy a built
  # product in place — refuse loudly instead.
  if [ "$CROPPED" = "$STACK" ]; then
    echo "finish_render: crop output $CROPPED IS the input stack — pass a distinct <png-name> (the framed product must not replace its source)" >&2
    exit 1
  fi
  if [ -e "$CROPPED" ]; then
    echo "finish_render: $CROPPED already exists — refusing to overwrite a built stack (delete it first or pick another <png-name>)" >&2
    exit 1
  fi
  WC=$(dirname "$STACK")/.crop_$NAME; rm -rf "$WC"; mkdir -p "$WC"
  printf 'requires 1.4.0\nsetcompress 0\nload %s\ncrop %s %s %s %s\nsave %s\n' \
    "$STACK" "$CX" "$CY" "$CW" "$CH" "${CROPPED%.fit}" > "$WC/c.ssf"
  flatpak run --command=siril-cli org.siril.Siril -d "$WC" -s "$WC/c.ssf" \
    > "$WC/log" 2>&1 || { echo "crop failed — $WC/log" >&2; exit 1; }
  rm -rf "$WC"
  [ -f "$CROPPED" ] || { echo "crop wrote no stack" >&2; exit 1; }
  echo "[finish $NAME] 0/4 verified crop applied to the LINEAR stack ($CX $CY $CW $CH) -> $CROPPED"
  STACK=$CROPPED
fi
BASE=${STACK%.fit}
WCS=${BASE}_wcs.fit; SPCC=${BASE}_spcc.fit
JUDGE=$REPO/web/results/$(basename "$SESSION")/judge/${NAME}_spcc-linked
mkdir -p "$(dirname "$JUDGE")"

echo "[finish $NAME] 1/4 solve"
# --central=<frac> restricts detection to the frame's central fraction — the
# union-canvas (framing=max) case, whose coverage seams false-detect otherwise.
python3 "$REPO/scripts/calibrate/solve_field.py" "$STACK" --detect=sep --max-stars=400 \
  --ra="$RA" --dec="$DEC" --radius-deg="$RAD" ${CENTRAL:+--central=$CENTRAL} \
  ${FIELDW:+--field-width-arcmin=$FIELDW} \
  --inject="$WCS" 2>&1 | grep -iE 'SOLVED|fail|warn' || true
[ -f "$WCS" ] || { echo "[finish $NAME] SOLVE FAILED (no WCS injected)" >&2; exit 1; }

echo "[finish $NAME] 2/4 catalog cone"
python3 "$REPO/scripts/calibrate/spcc_cone.py" "$WCS" --fetch 2>&1 | tail -1

echo "[finish $NAME] 3/4 SPCC"
python3 "$REPO/scripts/calibrate/spcc_run.py" "$SESSION" "$SET" \
  --in="$WCS" --out="$SPCC" --tag="$NAME" 2>&1 | grep -iE 'K factors|fail' || true
[ -f "$SPCC" ] || { echo "[finish $NAME] SPCC FAILED" >&2; exit 1; }

echo "[finish $NAME] 4/4 linked stretch -> PNG"
W=$(dirname "$STACK")/.finish_$NAME; rm -rf "$W"; mkdir -p "$W"
printf 'requires 1.4.0\nsetcompress 0\nload %s\nautostretch -linked\nsavepng %s\n' "$SPCC" "$JUDGE" > "$W/s.ssf"
flatpak run --command=siril-cli org.siril.Siril -d "$W" -s "$W/s.ssf" >> "$W/log" 2>&1
rm -rf "$W"
[ -f "$JUDGE.png" ] || { echo "[finish $NAME] STRETCH FAILED" >&2; exit 1; }
echo "[finish $NAME] DONE -> $JUDGE.png"
