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
#                     [--chunk=24] [--rej=wins|median] [--select=<list-file>] [--desky]
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
# !! REVERTED 2026-08-04 — `--desky` IS OFF BY DEFAULT AND IS A KNOWN REGRESSION.
# It shipped ON 2026-07-29 (f170540) and cost 31x in background flatness: july31/
# set-01 measured corner spread 12.4% with it against 0.4% without, one knob, 500
# frames, everything else identical. CAUSE: `seqsubsky` is a BACKGROUND EXTRACTION
# operator, defined on a FLAT-FIELDED image, and this ran it on RAW frames still
# carrying vignetting — the frame is sky x V, not sky. The additive plane overshoots
# where V curves hardest (the frame edge) and INVERTS the asymmetry there: raw light
# +0.426, --desky flat -0.550, so dividing by it doubles the error. The analysis
# below is preserved because its PROBLEM STATEMENT is still correct — a sky flat does
# bake in the horizon-fixed gradient and does tilt the object (3.11% at 241 sigma).
# Its PROPOSED FIX is not. Full record: docs/dead-ends.md + datasets/july31/set-01/
# qa_work/desky_regression.json.
#
# --desky RUNS Siril `seqsubsky 1` ON THE SOURCE FRAMES FIRST, and exists because
# the drift argument below has a HOLE. The drift decorrelates anything fixed on
# the CELESTIAL sphere (stars, nebulosity). It does NOT decorrelate sky brightness
# structure fixed relative to the HORIZON — moonlight, and the airmass gradient —
# because on a FIXED mount the camera is horizon-fixed too, so that gradient sits
# still on the sensor for the whole set and integrates straight into the flat.
# A TRACKED MOUNT IS NOT IMMUNE — the driver is whether the SENSOR is fixed
# relative to the HORIZON, not whether the mount tracks. An untracked tripod and
# an alt-az mount without a derotator both hold the gradient still on the sensor
# (zero rejection). An equatorial mount only ROTATES it, by the parallactic angle,
# and averaging the gradient VECTOR over a swing dq retains sinc(dq/2) of its
# slope: 98.9% at dq=30 deg, 97.4% at 45, 90% at 90, 63.7% at a full 180. Pure
# translation retains 100% (mean_t[a + b.(x-s(t))] = a + b.x - b.<s>, slope
# unchanged, offset only shifted — and normalization absorbs the offset). So the
# mechanism applies to any sky flat; only its SIZE on tracked data is unmeasured.
# MEASURED contamination, two sessions, isolating each flat's ODD component about
# centre (which cancels the even/radial vignetting) and fitting a plane: 4.8-19.4%
# of centre level on a moonless night, 16.8-22.6% on a 98%-moonlit one, and on the
# moonlit night the odd plane's DIRECTION tracks the moon's bearing in SENSOR
# coordinates to 23 deg where random would scatter ~104 deg.
# WHY IT MATTERS: a sky gradient is ADDITIVE and a flat DIVIDES. Lights are
# (sky+object) x V, the contaminated flat is V x (1+g), so dividing leaves
# (sky+object)/(1+g) — the sky's gradient does come out, but the OBJECT is left
# carrying a 5-23% multiplicative tilt it never had. It also makes the usual
# corner-vs-centre flatness check SELF-FULFILLING: the final stack reads flat
# precisely BECAUSE the flat absorbed the gradient, so a good flatness number is
# not evidence the calibration is clean — judge the FLAT's odd component instead.
# WHY subsky ON THE FRAMES rather than on the assembled flat: the contamination
# enters ADDITIVELY through the frames, so removing it additively per-frame is the
# matching domain; dividing it out of the finished flat would be a multiplicative
# fudge. MEASURED on one calibrated CFA frame (`subsky 1`): odd plane 3.32% ->
# 0.35% (-89%) while the level is preserved to ratio 1.0000, the radial vignetting
# is untouched (corner/centre 0.3115 -> 0.3114) and the Bayer phases are identical
# — i.e. it removes the sky term and nothing the flat exists to capture. Siril
# reports "computed for CFA image", so it is mosaic-aware; degree 1 is the
# registry's preserving degree (degree >= 2 eats frame-filling faint structure).
# REMOVAL CONDITION: a real flat for the set, which retires this whole builder.
# NOT "a tracked mount" — see above, tracking does not remove the mechanism.
#
# ENABLING CONDITION (validate, never assume — dead-end registry): the drift
# between frames must exceed ~20-100 px AND faint structure must not fill the
# frame, or the sky bakes into the flat and dividing ATTENUATES the very
# signal a faint-signal-first set protects. This script therefore VALIDATES its
# product and records the numbers:
# - Siril `stat` on five fixed regions (centre + 4 corners): the flat must be
#   a smooth falloff (corners below centre), with no structured residual;
# - Siril `findstar` on the flat: residual star-speck count (a true flat has
#   no stars; specks are un-rejected sky remnants);
# - an autostretched preview PNG for the eye check (diagnostic surface only,
#   never a judgment surface).
# The record lands in datasets/<session>/<set>/qa_work/<flat-stem>_qa.json;
# the eye check for baked-in structure (the Milky Way star field) is the caller's
# gate before the flat enters any stack.
#
# Builds from ALL raw frames in <session-dir>/<set>/ — the stack-cull policy
# (recipe.json exclude) does NOT apply here: transients (satellites, aircraft)
# are per-pixel minorities the rejection removes, and more frames reject
# better.
#
# --select=<list-file> (one raw path per line) overrides that default and
# builds from exactly those frames. It exists for the case the all-frames
# default does NOT cover: a set whose frames do not share ONE pointing. The
# per-pixel rejection removes a moving sky, not a sky that CHANGED — so a set
# containing a mid-set re-aim averages two different skies into the flat's
# low-order term, and dividing either block by that blend prints the other
# block's gradient into it (the same mechanism as the ratified across-sets
# rule: a flat calibrates ONLY the exact frames it was built from). MEASURED
# on a set carrying a mid-set re-aim vs a same-night same-optics single-
# pointing set: left-right corner ratio 1.162 vs 1.032, while the top-bottom
# (optical) term was identical at 1.143 vs 1.142 — the divergence is sky, and
# it sits on the drift axis. Transient culling is still NOT a reason to
# select; only a pointing change is.
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
SESSION=${1:?usage: build_sky_flat.sh <session-dir> <set> --dark=<master.fit> --out=<flat.fit> [--chunk=24] [--rej=wins|median] [--select=<list-file>] [--desky]}
SET=${2:?missing <set>}
DARK= OUT= CHUNK=24 REJ=wins SELECT= DESKY=0
for a in "${@:3}"; do case "$a" in
  --dark=*) DARK=${a#*=};; --out=*) OUT=${a#*=};;
  --chunk=*) CHUNK=${a#*=};; --rej=*) REJ=${a#*=};;
  --select=*) SELECT=${a#*=};;
  --desky) DESKY=1;;
  *) echo "unknown arg $a" >&2; exit 1;;
esac; done
# --desky: run Siril `seqsubsky 1` on the dark-subtracted source frames before
# they are stacked into the flat, so the flat carries only SENSOR-fixed response.
# Siril does the pixel work; this only sequences it.
# `-nodither` IS REQUIRED, and its absence is not a small thing: `seqsubsky`
# dithers by DEFAULT (the opposite of `subsky`, where -dither is opt-IN), and the
# dither is UNSEEDED. MEASURED on two real frames, four independent runs, Siril's
# own isub+stat: the calibrated input is bit-identical run to run (isub all-nil),
# but two runs of plain `seqsubsky pp_c 1` differ by sigma 0.4 ADU (min -1.0, max
# +1.0) while two runs with -nodither are bit-identical; default-minus-nodither is
# a uniform [0,1] ADU term (mean +0.5). Siril logs it as "dithering: enabled".
# The dither exists to break quantization terracing when a smooth model is
# subtracted from coarsely quantized data — a case this data is nowhere near: the
# frames' own background noise is bgnoise 17.7 ADU on a 42.7 ADU sky, i.e. 35x the
# 0.5 ADU step, so there is no terracing for it to break. It buys nothing here and
# costs exact reproducibility of the flat and of every calibrated light, which is
# a contract requirement (no unseeded step) that already cost `subsky` its
# -dither once. Photometrically it is negligible either way (0.4/sqrt(401) =
# 0.02 ADU, 0.05% of sky) — this is a reproducibility fix, not a photometry one.
# %b in the chunk printf expands the \n, and collapses to nothing when off — so
# the generated .ssf is byte-identical to the pre-change one without --desky.
DESKYCMD= SRCPREFIX=pp_
if [ "$DESKY" = 1 ]; then
  DESKYCMD='seqsubsky pp_c 1 -nodither\n'; SRCPREFIX=bkg_pp_
fi
[ -z "$SELECT" ] || [ -f "$SELECT" ] || { echo "no such --select list: $SELECT" >&2; exit 1; }
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

if [ -n "$SELECT" ]; then
  mapfile -t SRC < <(grep -v '^[[:space:]]*$' "$SELECT" | sort)
  for f in "${SRC[@]}"; do
    [ -f "$f" ] || { echo "ABORT: --select lists a missing frame: $f" >&2; exit 1; }
  done
else
  mapfile -t SRC < <(find "$SESSION/$SET" -maxdepth 1 -type f \
    \( -iname '*.nef' -o -iname '*.dng' -o -iname '*.cr2' -o -iname '*.cr3' \
       -o -iname '*.arw' -o -iname '*.raf' \) | sort)
fi
N=${#SRC[@]}
[ "$N" -ge 20 ] || { echo "ABORT: only $N raw frames under $SESSION/$SET — a sky flat needs a deep un-registered stack" >&2; exit 1; }
# Same recovery as the undistort builder, and for the same reason: run_set_chain
# calls this WITHOUT a --chunk, so "adjust --chunk" was advice the one-click chain
# could not take — a set whose frame count was 1 mod 24 simply could not build its
# flat from the session button. Chunk size only bounds working-set residency, so
# shrinking is free. It LOOPS because one decrement can land on a remainder of 1
# again (N = q*CHUNK+1 gives N mod (CHUNK-1) = (q+1) mod (CHUNK-1)).
if [ $((N % CHUNK)) -eq 1 ]; then
  ORIGCHUNK=$CHUNK
  while [ "$CHUNK" -gt 2 ] && [ $((N % CHUNK)) -eq 1 ]; do CHUNK=$((CHUNK - 1)); done
  [ $((N % CHUNK)) -ne 1 ] || { echo "ABORT: $N frames leave a final chunk of 1 at every chunk size down to 2" >&2; exit 1; }
  echo "chunk shrunk $ORIGCHUNK -> $CHUNK ($N frames leave a final chunk of 1 at $ORIGCHUNK, which Siril cannot sequence; remainder is now $((N % CHUNK)))"
fi
# pp_ accumulation ~49 MB/frame (16-bit CFA) + one chunk of c_ transients + slack
NEED_GB=$(( N * 98 / 1024 + CHUNK * 98 / 1024 + 3 ))
FREE_GB=$(df -BG --output=avail "$SESSION" | tail -1 | tr -dc 0-9)
[ "$FREE_GB" -ge "$NEED_GB" ] || { echo "ABORT: ~${NEED_GB}G needed for $N frames, ${FREE_GB}G free" >&2; exit 1; }
echo "sky flat: $N un-registered lights${SELECT:+ (selected from $SELECT)}, dark-subtracted, CFA, rej=$REJ -> $OUT.fit"

rm -rf "$W"; mkdir -p "$W/pp"
n=0; ci=0; g=0
while [ $n -lt $N ]; do
  ci=$((ci+1))
  rm -rf "$W/nef" "$W/proc"; mkdir -p "$W/nef" "$W/proc"
  for ((k=0; k<CHUNK && n<N; k++, n++)); do
    ln -sf "${SRC[$n]}" "$W/nef/$(basename "${SRC[$n]}")"
  done
  printf 'requires 1.2.0\nset32bits\nsetcompress 0\ncd %s\nconvert c -out=%s\ncd %s\ncalibrate c -dark=%s -prefix=pp_\n%b' \
    "$W/nef" "$W/proc" "$W/proc" "$DARK" "$DESKYCMD" > "$W/c.ssf"
  sir "$W/c.ssf"
  rm -f "$W/proc"/c_*.fit
  ok=0
  for f in "$W/proc"/${SRCPREFIX}c_*.fit; do
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
printf 'requires 1.2.0\nset32bits\nsetcompress 0\ncd %s\n%s -out=%s\n' \
  "$W/pp" "$STACKCMD" "$OUT" > "$W/s.ssf"
sir "$W/s.ssf"
[ -f "$OUT.fit" ] || { echo "FLAT STACK FAILED — read $W/siril.log" >&2; exit 1; }
rm -rf "$W/pp"

# ---- validation: Siril stat on centre + 4 corners, findstar speck count,
# ---- autostretch preview. Region size 400 px, 200 px in from each edge.
read -r IW IH < <(python3 - "$OUT.fit" <<'PY'
import sys
from astropy.io import fits
hdr = fits.getheader(sys.argv[1])
print(int(hdr["NAXIS1"]), int(hdr["NAXIS2"]))
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
# Speck count comes from the STAR LIST the tool writes, not from a log message.
# The log-regex this replaced (`Found [0-9]+ star`) NEVER matched Siril 1.4.4,
# which prints "Found N Gaussian profile stars in image" — the profile word sits
# between the count and "stars". With `|| echo 0` behind it the gate therefore
# read 0 unconditionally: a validation gate that could not fail, and two flat
# records plus a ledger entry carried an unmeasured 0 (re-measured from the list:
# 1 speck on each of the four july23 flats, control and de-skied alike, so the
# conclusion held and only the evidence was missing). A log message is not an
# interface; `-out=` is.
# Two measured tool behaviours this has to respect (probed on-rig, Siril 1.4.4):
# findstar writes NO list when it finds zero stars — which is a flat's IDEAL
# result, so a missing list must read as 0, never as an error — and it still
# exits 0 in that case, so a real failure is caught by `set -e` on the run.
# What a silent no-op would look like is a missing "Candidates for stars:" line,
# and that IS asserted: it is findstar's own report of having run, printed
# whether or not any candidate survives the PSF gate.
printf 'requires 1.2.0\nsetcompress 0\nload %s\nfindstar -out=%s\n' \
  "$OUT.fit" "$W/specks.lst" > "$W/f.ssf"
rm -f "$W/specks.lst"
flatpak run --command=siril-cli org.siril.Siril -d "$W" -s "$W/f.ssf" > "$W/findstar.log" 2>&1
grep -q 'Candidates for stars:' "$W/findstar.log" || {
  echo "ABORT: findstar did not run on $OUT.fit (no 'Candidates for stars' report) — read $W/findstar.log" >&2; exit 1; }
FS_LOG=0
if [ -f "$W/specks.lst" ]; then FS_LOG=$(grep -vc '^#' "$W/specks.lst" || true); fi
printf 'requires 1.2.0\nsetcompress 0\nload %s\nautostretch\nsavepng %s\n' \
  "$OUT.fit" "${OUT}_view" > "$W/p.ssf"
sir "$W/p.ssf"

python3 - "$OUT.fit" "$W/stat.log" "$FS_LOG" "$N" "$REJ" "$DARK" "$QA_DIR/${STEM}_qa.json" "$B" "$M" "${SELECT:-}" "$DESKY" <<'PY'
import json, re, sys
flat, statlog, specks, n, rej, dark, rec_path, box, margin, select, desky = sys.argv[1:12]
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
                     "multiplicative norm",
           "desky": ("Siril seqsubsky 1 on the dark-subtracted source frames "
                     "before stacking — removes the additive sky plane that is "
                     "fixed in the sensor frame on a fixed mount (moonlight / "
                     "airmass) and does NOT reject out of the flat"
                     if desky == "1" else "off (flat carries any sensor-fixed "
                     "sky gradient present in the source frames)"),
           "frame_source": ("ALL raw frames in the set dir" if not select else
                            f"SELECTED subset ({select}) — the set does not "
                            "share one pointing, so the flat is built from "
                            "exactly the frames it calibrates")},
 "regional_stat_ADU": regions,
 "region_geometry_px": {"box": int(box), "corner_margin": int(margin)},
 "findstar_speck_count": int(specks),
 "gate": "smooth falloff (corners < centre), NO structured sky residual "
         "(the Milky Way star field) on the preview, speck count ~0; the eye "
         "check + the with/without finals comparison gate adoption "
         "(dead-end registry: a sky flat preserves frame-filling faint structure "
         "only when validated — that structure is UNRESOLVED STARLIGHT, not dust)",
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
