#!/usr/bin/env bash
# Finish a stacked FITS into a JUDGEABLE render: plate-solve -> SPCC colour
# calibration -> linked auto-stretch -> full-frame 16-bit PNG. This is the
# render-chain finish stage; every pixel op is an official tool (astrometry.net
# solve, Siril SPCC, Siril autostretch/savepng) and this only orchestrates them.
#
#   finish_render.sh <stack.fit> <png-name> [--session=D --set=S] [--ra=R --dec=D --radius-deg=N]
#
# Output: results/<session>/judge/<png-name>_spcc-linked.png (16-bit, full-frame,
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
RA=310 DEC=47 RAD=40 SESSION=july14 SET=set-01 CENTRAL=
for a in "$@"; do case "$a" in
  --ra=*) RA=${a#*=};; --dec=*) DEC=${a#*=};; --radius-deg=*) RAD=${a#*=};;
  --session=*) SESSION=${a#*=};; --set=*) SET=${a#*=};;
  --central=*) CENTRAL=${a#*=};;
  *) echo "unknown arg $a" >&2; exit 1;;
esac; done
[ -f "$STACK" ] || { echo "no such stack: $STACK" >&2; exit 1; }
STACK=$(cd "$(dirname "$STACK")" && pwd)/$(basename "$STACK")
BASE=${STACK%.fit}
WCS=${BASE}_wcs.fit; SPCC=${BASE}_spcc.fit
JUDGE=$REPO/results/$(basename "$SESSION")/judge/${NAME}_spcc-linked
mkdir -p "$(dirname "$JUDGE")"

echo "[finish $NAME] 1/4 solve"
# --central=<frac> restricts detection to the frame's central fraction — the
# union-canvas (framing=max) case, whose coverage seams false-detect otherwise.
python3 "$REPO/scripts/calibrate/solve_field.py" "$STACK" --detect=sep --max-stars=400 \
  --ra="$RA" --dec="$DEC" --radius-deg="$RAD" ${CENTRAL:+--central=$CENTRAL} \
  --inject="$WCS" 2>&1 | grep -iE 'SOLVED|fail' || true
[ -f "$WCS" ] || { echo "[finish $NAME] SOLVE FAILED (no WCS injected)" >&2; exit 1; }

echo "[finish $NAME] 2/4 catalog cone"
python3 "$REPO/scripts/calibrate/spcc_cone.py" "$WCS" --fetch 2>&1 | tail -1

echo "[finish $NAME] 3/4 SPCC"
python3 "$REPO/scripts/calibrate/spcc_run.py" "$SESSION" "$SET" \
  --in="$WCS" --out="$SPCC" --tag="$NAME" 2>&1 | grep -iE 'K factors|fail' || true
[ -f "$SPCC" ] || { echo "[finish $NAME] SPCC FAILED" >&2; exit 1; }

echo "[finish $NAME] 4/4 linked stretch -> PNG"
W=$(dirname "$STACK")/.finish_$NAME; rm -rf "$W"; mkdir -p "$W"
printf 'requires 1.2.0\nload %s\nautostretch -linked\nsavepng %s\n' "$SPCC" "$JUDGE" > "$W/s.ssf"
flatpak run --command=siril-cli org.siril.Siril -d "$W" -s "$W/s.ssf" >> "$W/log" 2>&1
rm -rf "$W"
[ -f "$JUDGE.png" ] || { echo "[finish $NAME] STRETCH FAILED" >&2; exit 1; }
echo "[finish $NAME] DONE -> $JUDGE.png"
