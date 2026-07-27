#!/bin/bash
# run_lunar_pipeline.sh <session-dir> <set> <stage> [options]
#
# The LUNAR (small-disc lucky-imaging) class builder: burst NEFs -> staged
# disc-window crop -> crop-matched dark calibration -> planetary registration
# (the one GUI step in Siril 1.4.4) -> tool-audited shift application ->
# stack -> disc-neutral colour -> like-encoded judgment surfaces. Every pixel
# operation and every measurement is Siril's; this script orchestrates,
# records, and guards. Verified end to end on a ~110 px disc at 17"/px;
# PROVISIONAL as-written (generalized from the run that produced those
# records - its first fresh end-to-end run is the next lunar corpus).
#
# The class facts this builder encodes (mechanisms + numbers:
# docs/dead-ends.md; route: docs/lunar-lucky-imaging.md):
#  - The staging crop is a DISK adaptation: full-frame 24.5 MP x 1000+ frame
#    sequences exceed the base rig; the window must contain the disc's whole
#    drift track (even x/y/w/h - CFA phase) and the master dark is cropped
#    with the IDENTICAL box. Removal condition: x86 disk.
#  - Planetary registrations are GUI-only in 1.4.4 and REQUIRE the selection
#    to contain the target's whole movement (use the whole staged frame).
#  - The reference frame goes to the SEQUENCE MIDDLE before registering:
#    circular DFT correlation wraps shifts beyond +/- min(w,h)/2 and stacks a
#    second coherent disc exactly one window away. setref first, always.
#  - A failed GUI registration leaves poisoned .seq state (deselection debris,
#    stale transforms): delete the .seq and re-register on a rebuilt sequence.
#  - 1.4.4 planetary regdata carries NO per-frame quality even on success:
#    quality-ranked stacking needs a ranking tool (the x86 ladder); this
#    builder ships the full-stack control.
#  - Registration is verified BEFORE stacking from the .seq itself (selection
#    repair, null-H refusal, aliasing-margin refusal, drift-span sanity) and
#    the stacked disc is inspected WHOLE-FRAME (a one-region zoom cannot see
#    a wrapped second disc).
#  - Colour: no stars -> no SPCC (recorded skip). The sunlit disc is the
#    neutral reference: Siril stat medians on an inside-disc box -> G-anchored
#    diagonal ccm. Judgment surfaces are linear PNG16 pairs at ONE clip-safe
#    integer gain (pm "$img$*k"), never per-image autostretch.
set -euo pipefail

REPO="$(cd "$(dirname "$0")/../.." && pwd)"
S="${1:?usage: run_lunar_pipeline.sh <session-dir> <set> <stage> [options]}"
SET="${2:?set name required}"
STAGE="${3:?stage required: prep|stage|calibrate|register|verify|stack|sharpen|wb|surfaces}"
shift 3
S="$(cd "$S" && pwd)"
SESSION="$(basename "$S")"
W="$S/work"
CROP="$W/crop_$SET"
DS="$REPO/datasets/$SESSION/$SET"
RESULTS="$REPO/web/results/$SESSION"
CHUNK=80

siril_run() {  # one instance at a time, always (flatpak instance-dir race)
  flatpak run --command=siril-cli org.siril.Siril -d "$1" -s "$2"
}

case "$STAGE" in

prep)
  # EXIF uniformity: the whole set + the darks must share ONE tuple
  # (exposure|ISO|model|lens|focal|size|compression); Lossless NEF only
  # (HE/HE* have no libraw decode). Loud stop on any second tuple.
  tuples=$(exiftool -q -p '$ExposureTime|$ISO|$Model|$LensModel|$FocalLength|$ImageSize|$NEFCompression' "$S/$SET"/*.NEF | sort -u)
  n=$(echo "$tuples" | wc -l)
  echo "$tuples"
  [[ $n -eq 1 ]] || { echo "PREP FAIL: $n distinct EXIF tuples in $SET (one required)" >&2; exit 1; }
  echo "$tuples" | grep -q 'Lossless' || { echo "PREP FAIL: not Lossless NEF" >&2; exit 1; }
  [[ -f "$W/masters/dark_master.fit" ]] || echo "WARN: no master dark at $W/masters/dark_master.fit"
  echo "PREP OK: $(ls "$S/$SET"/*.NEF | wc -l) frames, one tuple. Declare mount in $DS/acquisition.json (scripts/lib/acquisition.py resolve seeds it)."
  ;;

stage)
  # --box="x y w h" (even values). Chunked convert->seqcrop->accumulate; the
  # master dark is cropped with the IDENTICAL box.
  BOX=""; for a in "$@"; do [[ $a == --box=* ]] && BOX="${a#--box=}"; done
  [[ -n "$BOX" ]] || { echo "need --box=\"x y w h\" (from the operator's eyes on tool-made previews)" >&2; exit 1; }
  read -r bx by bw bh <<<"$BOX"
  for v in $bx $by $bw $bh; do (( v % 2 == 0 )) || { echo "STAGE FAIL: box values must be EVEN (CFA phase): $BOX" >&2; exit 1; }; done
  mkdir -p "$CROP" "$W/masters"
  files=("$S/$SET"/*.NEF); n=${#files[@]}; k=0; out=1
  while (( k < n )); do
    stagedir="$W/stage_cur"; rm -rf "$stagedir"; mkdir -p "$stagedir"
    for f in "${files[@]:k:CHUNK}"; do ln -s "$f" "$stagedir/"; done
    printf 'requires 1.4.0\nsetcompress 0\nset16bits\ncd %s\nconvert ch -out=.\nseqcrop ch %s -prefix=cropped_\nclose\n' \
      "work/stage_cur" "$BOX" > "$W/stage_cur.gen.ssf"
    siril_run "$S" "$W/stage_cur.gen.ssf" > "$W/stage_${SET}_${k}.log" 2>&1
    cnt=0
    for c in "$stagedir"/cropped_ch*.fit; do
      [[ -e "$c" ]] || { echo "STAGE FAIL: chunk @$k produced no crops" >&2; exit 1; }
      mv "$c" "$CROP/$(printf 'cl_%05d.fit' "$out")"; out=$((out+1)); cnt=$((cnt+1))
    done
    rm -rf "$stagedir"; echo "  chunk @$k: $cnt"
    k=$((k+CHUNK))
  done
  printf 'requires 1.4.0\nsetcompress 0\nset32bits\ncd work/masters\nload dark_master\ncrop %s\nsave dark_master_crop_%s\nclose\n' \
    "$BOX" "$SET" > "$W/master_crop_$SET.gen.ssf"
  siril_run "$S" "$W/master_crop_$SET.gen.ssf" > "$W/master_crop_$SET.log" 2>&1
  mkdir -p "$DS"
  [[ -f "$DS/staging_crop.json" ]] || printf '{\n "set": "%s", "box_xywh": [%s, %s, %s, %s],\n "why": "disk adaptation - the window carries the whole disc track; master dark cropped with the identical box",\n "removal_condition": "x86 disk - process full-frame"\n}\n' \
    "$SET" $bx $by $bw $bh > "$DS/staging_crop.json"
  echo "STAGE OK: $((out-1)) cropped frames in $CROP; master crop written; record $DS/staging_crop.json"
  ;;

calibrate)
  printf 'requires 1.4.0\nsetcompress 0\nset32bits\ncd work/crop_%s\nlink moon -out=.\ncalibrate moon -dark=../masters/dark_master_crop_%s -cfa -debayer -cc=dark\nclose\n' \
    "$SET" "$SET" > "$W/calibrate_$SET.gen.ssf"
  siril_run "$S" "$W/calibrate_$SET.gen.ssf" > "$W/calibrate_$SET.log" 2>&1
  echo "CALIBRATE OK: $(ls "$CROP"/pp_moon_*.fit | wc -l) frames"
  ;;

register)
  # Pre-register hygiene + the mid-sequence reference, then the GUI handoff.
  n=$(ls "$CROP"/pp_moon_*.fit | wc -l); mid=$(( (n + 1) / 2 ))
  if [[ -f "$CROP/pp_moon_.seq" ]] && grep -q '^R' "$CROP/pp_moon_.seq"; then
    echo "existing regdata found -> deleting .seq (never re-register over failed/old state; the GUI sequence search rebuilds it clean)"
    rm -f "$CROP/pp_moon_.seq"
    echo "NOTE: setref needs the rebuilt .seq - in the GUI, run Search Sequence FIRST, close Siril, then re-run this stage to set the reference."
    exit 0
  fi
  if [[ -f "$CROP/pp_moon_.seq" ]]; then
    printf 'requires 1.4.0\ncd work/crop_%s\nselect pp_moon 1 %s\nsetref pp_moon %s\nclose\n' "$SET" "$n" "$mid" > "$W/setref_$SET.gen.ssf"
    siril_run "$S" "$W/setref_$SET.gen.ssf" > "$W/setref_$SET.log" 2>&1
    echo "reference set to frame $mid of $n (mid-sequence: max |shift| stays under the +/- min(w,h)/2 aliasing bound)"
  else
    echo "no .seq yet - the GUI sequence search will build it; re-run this stage after to set the mid reference BEFORE registering."
    exit 0
  fi
  cat <<EOF
GUI STEP (the one manual step - planetary registration is GUI-only in 1.4.4):
  1. Siril GUI -> working directory $CROP
  2. Sequence tab -> Search sequence -> pp_moon
  3. Draw the selection over NEARLY THE WHOLE FRAME (the staged window already
     bounds the track; the method requires the selection to contain the disc's
     whole movement)
  4. Registration -> "Image Pattern Alignment (planetary - full disk)" ->
     register ALL images -> Go   (KOMBAT is a measured dead end on this class)
  5. Close Siril, then run the 'verify' stage.
EOF
  ;;

verify)
  seq="$CROP/pp_moon_.seq"
  [[ -f "$seq" ]] || { echo "VERIFY FAIL: no .seq" >&2; exit 1; }
  n=$(ls "$CROP"/pp_moon_*.fit | wc -l)
  # selection repair (failed runs leave deselection debris + a broken counter)
  printf 'requires 1.4.0\ncd work/crop_%s\nselect pp_moon 1 %s\nclose\n' "$SET" "$n" > "$W/verifysel_$SET.gen.ssf"
  siril_run "$S" "$W/verifysel_$SET.gen.ssf" > /dev/null 2>&1
  # null-H refusal + aliasing margin + span sanity, from the tool's own regdata
  read -r bw bh < <(python3 -c "import json;b=json.load(open('$DS/staging_crop.json'))['box_xywh'];print(b[2],b[3])")
  grep '^R' "$seq" | awk -v W="$bw" -v H="$bh" '
    { tx=$10; ty=$13; if ($9==0 && $10==0 && $11==0) nul++;
      if (tx<mnx) mnx=tx; if (tx>mxx) mxx=tx; if (ty<mny) mny=ty; if (ty>mxy) mxy=ty }
    END {
      lim=(W<H?W:H)/2 - 64;
      printf "frames=%d nullH=%d shift x[%d..%d] y[%d..%d] alias-bound=%d\n", NR, nul, mnx, mxx, mny, mxy, lim;
      if (nul>0)                       { print "VERIFY FAIL: null-H frames (registration failed - delete .seq, redo GUI step)"; exit 1 }
      if (mxx>lim||-mnx>lim||mxy>lim||-mny>lim) { print "VERIFY FAIL: shifts within 64 px of the circular-correlation wrap bound - re-register with a mid-track reference or a taller window"; exit 1 }
      print "VERIFY OK (whole-frame stack inspection still mandatory after stacking)"
    }' || exit 1
  ;;

stack)
  printf 'requires 1.4.0\nsetcompress 0\nset32bits\ncd work/crop_%s\nseqapplyreg pp_moon -interp=none\nstack r_pp_moon rej w 3 3 -nonorm -out=%s/stack_%s_q100\nclose\n' \
    "$SET" "../../../web/results/$SESSION" "$SET" > "$W/stack_$SET.gen.ssf"
  mkdir -p "$RESULTS"
  siril_run "$S" "$W/stack_$SET.gen.ssf" > "$W/stack_$SET.log" 2>&1
  grep -E 'images have been stacked' "$W/stack_$SET.log"
  rm -f "$CROP"/r_pp_moon_*   # regenerable; large
  echo "STACK OK -> $RESULTS/stack_${SET}_q100.fit"
  echo "MANDATORY next: whole-frame inspection of the stacked disc (one region cannot show a wrapped second disc); quality rungs ride the x86 ranking-tool ladder."
  ;;

sharpen)
  # sb (Split Bregman) is the ratified default; Siril's docs recommend
  # sb/wiener for stacked lunar images. Blind PSF from the stack itself.
  M="sb"; for a in "$@"; do [[ $a == --method=* ]] && M="${a#--method=}"; done
  printf 'requires 1.4.0\nsetcompress 0\nset32bits\ncd ../../web/results/%s\nload stack_%s_q100\nmakepsf blind\n%s\nsave stack_%s_q100%s\nclose\n' \
    "$SESSION" "$SET" "$M" "$SET" "$M" > "$W/sharpen_$SET.gen.ssf"
  siril_run "$S" "$W/sharpen_$SET.gen.ssf" > "$W/sharpen_$SET.log" 2>&1
  echo "SHARPEN OK -> stack_${SET}_q100${M}.fit (wiener leaves a frame-edge artifact band on this class - inspect before judging)"
  ;;

wb)
  # --disc="x y r" from the operator (in-house disc detection is out of
  # bounds). Measures the inscribed inside-disc box, G-anchored diagonal ccm.
  D=""; SRC="q100sb"
  for a in "$@"; do case $a in --disc=*) D="${a#--disc=}";; --src=*) SRC="${a#--src=}";; esac; done
  [[ -n "$D" ]] || { echo "need --disc=\"x y r\" (disc centre + radius in crop coords, operator-supplied)" >&2; exit 1; }
  read -r dx dy dr <<<"$D"
  half=$(python3 -c "print(int($dr/1.4142/2)*2)")
  bx=$((dx-half)); by=$((dy-half)); bw=$((half*2)); bh=$((half*2))
  printf 'requires 1.4.0\ncd ../../web/results/%s\nload stack_%s_%s\nboxselect %s %s %s %s\nstat main\nclose\n' \
    "$SESSION" "$SET" "$SRC" $bx $by $bw $bh > "$W/wbmeasure_$SET.gen.ssf"
  siril_run "$S" "$W/wbmeasure_$SET.gen.ssf" > "$W/wbmeasure_$SET.log" 2>&1
  eval "$(grep 'layer:' "$W/wbmeasure_$SET.log" | sed -E 's/.*(Red|Green|Blue) layer:.*Median: ([0-9.]+),.*/med_\1=\2/' | tr 'RGB' 'rgb' | sed 's/reen//;s/lue//;s/ed//')"
  kr=$(python3 -c "print(round($med_g/$med_r,4))"); kb=$(python3 -c "print(round($med_g/$med_b,4))")
  echo "disc medians R=$med_r G=$med_g B=$med_b -> kR=$kr kB=$kb (G-anchored)"
  printf 'requires 1.4.0\nsetcompress 0\nset32bits\ncd ../../web/results/%s\nload stack_%s_%s\nccm %s 0 0 0 1 0 0 0 %s 1\nsave stack_%s_%swb\nstat main\nclose\n' \
    "$SESSION" "$SET" "$SRC" "$kr" "$kb" "$SET" "$SRC" > "$W/wbapply_$SET.gen.ssf"
  siril_run "$S" "$W/wbapply_$SET.gen.ssf" > "$W/wbapply_$SET.log" 2>&1
  grep 'layer:' "$W/wbapply_$SET.log" | sed 's/^log: //'
  echo "WB OK -> stack_${SET}_${SRC}wb.fit (record gains + medians in the set's qa_work record)"
  ;;

surfaces)
  # like-encoded linear pairs: ONE integer gain k for every member, chosen
  # clip-safe from the tool-reported channel maxima of ALL named stacks.
  # usage: surfaces <tag> [<tag>...]  e.g. surfaces q100sb q100sbwb
  [[ $# -ge 1 ]] || { echo "usage: surfaces <recipe-tag> [...]" >&2; exit 1; }
  mkdir -p "$RESULTS/judge"
  maxall=0
  for t in "$@"; do
    printf 'requires 1.4.0\ncd ../../web/results/%s\nload stack_%s_%s\nstat main\nclose\n' "$SESSION" "$SET" "$t" > "$W/surfstat.gen.ssf"
    m=$(siril_run "$S" "$W/surfstat.gen.ssf" 2>&1 | grep 'layer:' | sed -E 's/.*Max: ([0-9.]+),.*/\1/' | sort -rn | head -1)
    maxall=$(python3 -c "print(max($maxall,$m))")
  done
  k=$(python3 -c "print(int(65500/$maxall))")
  echo "pair gain k=$k (max channel peak $maxall)"
  i=0
  for t in "$@"; do
    i=$((i+1)); cp "$RESULTS/stack_${SET}_${t}.fit" "$W/sf$i.fit"
    printf 'requires 1.4.0\nsetcompress 0\ncd work\npm "$sf%s$*%s"\nsavepng ../../../web/results/%s/judge/%s_%s_lin%s\nclose\n' \
      "$i" "$k" "$SESSION" "$SET" "$t" "$k" > "$W/surfmint.gen.ssf"
    siril_run "$S" "$W/surfmint.gen.ssf" > /dev/null 2>&1
    rm -f "$W/sf$i.fit"
    echo "  judge/${SET}_${t}_lin${k}.png"
  done
  echo "SURFACES OK - inspect whole-frame at 1:1 before handoff (mandatory)"
  ;;

*) echo "unknown stage: $STAGE" >&2; exit 1 ;;
esac
