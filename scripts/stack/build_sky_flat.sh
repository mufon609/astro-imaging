#!/usr/bin/env bash
# Sky-flat builder for a flatless set: median/winsorized stack of the set's own
# UN-registered lights. The sky drifts across the sensor between frames (fixed
# tripod or dither), so the moving sky rejects out of the per-pixel statistic
# and what remains is the SENSOR-FIXED response — vignetting + dust motes +
# PRNU — i.e. a real flat built from the lights themselves. Every pixel op is
# Siril's (convert / calibrate / stack / stat / findstar); this only
# orchestrates and records.
#
#   build_sky_flat.sh <session-dir> <set> --dark=<master.fit> --out=<flat.fit> \
#                     [--chunk=24] [--rej=wins|median]
#
# Recipe (the validated build, plus the ratified rejection tightening):
# - lights stay CFA (NO debayer): an OSC flat divides the CFA mosaic before
#   any interpolation, so the flat must live on the same grid;
# - calibrate with the matched master dark ONLY (pedestal-free lights — a flat
#   built with the ~1k ADU pedestal in would under-correct when divided);
# - UN-registered stack with MULTIPLICATIVE input normalization (-norm=mul,
#   the flat-frame doctrine: frames used for division normalize by scale);
# - rejection: wins = `rej w 3 3` (default — kills the faint star specks a
#   pure median leaves; each sky pixel is a moving minority the winsorized
#   sigma gate rejects) | median = pure median, no rejection (the earlier
#   validated build; kept as the attribution arm for flat-vs-flat A/Bs).
#
# ENABLING CONDITION (validate, never assume — dead-end registry): the drift
# between frames must exceed ~20-100 px AND faint structure must not fill the
# frame, or the sky bakes into the flat and dividing ATTENUATES the very
# signal a dust-first set protects. This script therefore VALIDATES its
# product and records the numbers:
# - Siril `stat` on five fixed regions (centre + 4 corners): the flat must be
#   a smooth falloff (corners below centre), with no structured residual;
# - Siril `findstar` on the flat: residual star-speck count (a true flat has
#   no stars; specks are un-rejected sky remnants);
# - an autostretched preview PNG for the eye check (diagnostic surface only,
#   never a judgment surface).
# The record lands in datasets/<session>/<set>/qa_work/<flat-stem>_qa.json;
# the eye check for baked-in structure (MW band / IFN clumps) is the caller's
# gate before the flat enters any stack.
#
# Builds from ALL raw frames in <session-dir>/<set>/ — the stack-cull policy
# (recipe.json exclude) does NOT apply here: transients (satellites, aircraft)
# are per-pixel minorities the rejection removes, and more frames reject
# better.
#
# GUARDS: chunked convert+calibrate (raw + converted copies never resident
# together beyond one chunk; a full-set c_ + pp_ tree would not fit tight
# disks); chunk remainder of 1 aborts up front (Siril cannot build a sequence
# from one frame); disk preflight for the accumulated pp_ set + one chunk.
#
# REMOVAL CONDITION: a matching real flat exists for the set (shot at the
# session's optical state) — then this builder and its product retire for
# that set.
#
# Nothing is compressed; every generated .ssf pins `setcompress 0`.
set -euo pipefail
REPO=$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)
SESSION=${1:?usage: build_sky_flat.sh <session-dir> <set> --dark=<master.fit> --out=<flat.fit> [--chunk=24] [--rej=wins|median]}
SET=${2:?missing <set>}
DARK= OUT= CHUNK=24 REJ=wins
for a in "${@:3}"; do case "$a" in
  --dark=*) DARK=${a#*=};; --out=*) OUT=${a#*=};;
  --chunk=*) CHUNK=${a#*=};; --rej=*) REJ=${a#*=};;
  *) echo "unknown arg $a" >&2; exit 1;;
esac; done
[ -n "$DARK" ] && [ -f "$DARK" ] || { echo "need --dark=<existing master dark>" >&2; exit 1; }
[ -n "$OUT" ] || { echo "need --out=<flat.fit>" >&2; exit 1; }
case "$REJ" in wins|median) ;; *) echo "--rej must be wins or median" >&2; exit 1;; esac
SESSION=$(cd "$SESSION" && pwd)
DARK=$(cd "$(dirname "$DARK")" && pwd)/$(basename "$DARK")
OUT=${OUT%.fit}
mkdir -p "$(dirname "$OUT")"
OUT="$(cd "$(dirname "$OUT")" && pwd)/$(basename "$OUT")"
STEM=$(basename "$OUT")
W=$SESSION/work/flatbuild_$SET
QA_DIR=$REPO/datasets/$(basename "$SESSION")/$SET/qa_work
mkdir -p "$QA_DIR"
sir(){ flatpak run --command=siril-cli org.siril.Siril -d "$W" -s "$1" >> "$W/siril.log" 2>&1; }

mapfile -t SRC < <(find "$SESSION/$SET" -maxdepth 1 -type f \
  \( -iname '*.nef' -o -iname '*.dng' -o -iname '*.cr2' -o -iname '*.cr3' \
     -o -iname '*.arw' -o -iname '*.raf' \) | sort)
N=${#SRC[@]}
[ "$N" -ge 20 ] || { echo "ABORT: only $N raw frames under $SESSION/$SET — a sky flat needs a deep un-registered stack" >&2; exit 1; }
[ $((N % CHUNK)) -ne 1 ] || { echo "ABORT: $N frames leave a final chunk of 1 (Siril cannot sequence one frame) — adjust --chunk" >&2; exit 1; }
# pp_ accumulation ~49 MB/frame (16-bit CFA) + one chunk of c_ transients + slack
NEED_GB=$(( N * 49 / 1024 + CHUNK * 49 / 1024 + 3 ))
FREE_GB=$(df -BG --output=avail "$SESSION" | tail -1 | tr -dc 0-9)
[ "$FREE_GB" -ge "$NEED_GB" ] || { echo "ABORT: ~${NEED_GB}G needed for $N frames, ${FREE_GB}G free" >&2; exit 1; }
echo "sky flat: $N un-registered lights, dark-subtracted, CFA, rej=$REJ -> $OUT.fit"

rm -rf "$W"; mkdir -p "$W/pp"
n=0; ci=0; g=0
while [ $n -lt $N ]; do
  ci=$((ci+1))
  rm -rf "$W/nef" "$W/proc"; mkdir -p "$W/nef" "$W/proc"
  for ((k=0; k<CHUNK && n<N; k++, n++)); do
    ln -sf "${SRC[$n]}" "$W/nef/$(basename "${SRC[$n]}")"
  done
  printf 'requires 1.2.0\nset16bits\nsetcompress 0\ncd %s\nconvert c -out=%s\ncd %s\ncalibrate c -dark=%s -prefix=pp_\n' \
    "$W/nef" "$W/proc" "$W/proc" "$DARK" > "$W/c.ssf"
  sir "$W/c.ssf"
  rm -f "$W/proc"/c_*.fit
  ok=0
  for f in "$W/proc"/pp_c_*.fit; do
    [ -f "$f" ] || break
    g=$((g+1)); ok=1
    mv "$f" "$W/pp/f_$(printf %05d "$g").fit"
  done
  [ "$ok" -eq 1 ] || { echo "ABORT: chunk $ci calibrated nothing — read $W/siril.log" >&2; exit 1; }
  rm -rf "$W/nef" "$W/proc"
  echo "chunk $ci: $n/$N  $(df -h "$SESSION" | tail -1 | awk '{print $4" free"}')"
done
[ "$g" -eq "$N" ] || { echo "ABORT: calibrated $g of $N frames" >&2; exit 1; }

# f_00001..f_NNNNN in one dir = one sequence; Siril scans the CWD and builds
# the .seq itself (the light pipeline's proven pattern — no link step needed)
STACKCMD="stack f rej w 3 3 -norm=mul"
[ "$REJ" = median ] && STACKCMD="stack f med -norm=mul"
rm -f "$W/pp"/*.seq
printf 'requires 1.2.0\nset16bits\nsetcompress 0\ncd %s\n%s -out=%s\n' \
  "$W/pp" "$STACKCMD" "$OUT" > "$W/s.ssf"
sir "$W/s.ssf"
[ -f "$OUT.fit" ] || { echo "FLAT STACK FAILED — read $W/siril.log" >&2; exit 1; }
rm -rf "$W/pp"

# ---- validation: Siril stat on centre + 4 corners, findstar speck count,
# ---- autostretch preview. Region size 400 px, 200 px in from each edge.
read -r IW IH < <(python3 - "$OUT.fit" <<'PY'
import sys
from astropy.io import fits
with fits.open(sys.argv[1]) as h:
    d = h[0].data
print(d.shape[-1], d.shape[-2])
PY
)
B=400; M=200
declare -A RX RY
RX[center]=$(( (IW - B) / 2 )); RY[center]=$(( (IH - B) / 2 ))
RX[TL]=$M;                RY[TL]=$M
RX[TR]=$((IW - M - B));   RY[TR]=$M
RX[BL]=$M;                RY[BL]=$((IH - M - B))
RX[BR]=$((IW - M - B));   RY[BR]=$((IH - M - B))
: > "$W/stat.log"
for r in center TL TR BL BR; do
  printf 'requires 1.2.0\nsetcompress 0\nload %s\ncrop %s %s %s %s\nstat\n' \
    "$OUT.fit" "${RX[$r]}" "${RY[$r]}" "$B" "$B" > "$W/v.ssf"
  flatpak run --command=siril-cli org.siril.Siril -d "$W" -s "$W/v.ssf" 2>&1 \
    | sed -n "s/^log: \(.*Mean:.*\)/$r \1/p" >> "$W/stat.log"
done
printf 'requires 1.2.0\nsetcompress 0\nload %s\nfindstar -out=%s\n' \
  "$OUT.fit" "$W/specks.lst" > "$W/f.ssf"
FS_LOG=$(flatpak run --command=siril-cli org.siril.Siril -d "$W" -s "$W/f.ssf" 2>&1 \
  | grep -oE 'Found [0-9]+ star' | grep -oE '[0-9]+' || echo 0)
printf 'requires 1.2.0\nsetcompress 0\nload %s\nautostretch\nsavepng %s\n' \
  "$OUT.fit" "${OUT}_view" > "$W/p.ssf"
sir "$W/p.ssf"

python3 - "$OUT.fit" "$W/stat.log" "$FS_LOG" "$N" "$REJ" "$DARK" "$QA_DIR/${STEM}_qa.json" "$B" "$M" <<'PY'
import json, re, sys
flat, statlog, specks, n, rej, dark, rec_path, box, margin = sys.argv[1:10]
regions = {}
for line in open(statlog):
    m = re.match(r"(\w+)\b.*?Mean: ([0-9.]+), Median: ([0-9.]+), Sigma: ([0-9.]+)",
                 line)
    if m and m.group(1) not in regions:
        regions[m.group(1)] = {"mean": float(m.group(2)),
                               "median": float(m.group(3)),
                               "sigma": float(m.group(4))}
rec = {
 "tool": "Siril 1.4.4 — un-registered lights: CFA convert -> calibrate -dark "
         "-> stack (-norm=mul); Siril stat regional crops + findstar + "
         "autostretch preview",
 "flat": flat,
 "build": {"frames": int(n), "rejection": rej, "dark": dark,
           "method": "UN-registered, dark-subtracted (pedestal-free), CFA, "
                     "multiplicative norm"},
 "regional_stat_ADU": regions,
 "region_geometry_px": {"box": int(box), "corner_margin": int(margin)},
 "findstar_speck_count": int(specks),
 "gate": "smooth falloff (corners < centre), NO structured sky residual "
         "(MW band / IFN clumps) on the preview, speck count ~0; the eye "
         "check + the with/without finals comparison gate adoption "
         "(dead-end registry: a sky flat is dust-safe only when validated)",
 "preview": flat.replace(".fit", "_view.png"),
}
json.dump(rec, open(rec_path, "w"), indent=1)
print(f"regional ADU: " + " ".join(
    f"{k} {v['median']:.0f}" for k, v in regions.items()))
print(f"speck count: {specks}")
print(f"record: {rec_path}")
PY
echo "=== DONE: $OUT.fit (validate before use: preview ${OUT}_view.png + the qa record) ==="
ls -la "$OUT.fit"
