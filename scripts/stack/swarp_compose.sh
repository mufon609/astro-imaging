#!/usr/bin/env bash
# swarp_compose.sh — the WEIGHTED (tapered per-member weight) compose: SWarp with
# per-member weight maps, onto the canonical's grid, normalised like Siril's addscale.
#
#   swarp_compose.sh --out=<stack.fit> --members=<curated dir> --grid=<raw canonical compose .fit>
#                    --ref=<member path (the anchor, ANCLOC)> [--xc-json=<rule json>] [--tmin=0.02]
#                    [--kernel=LANCZOS4] [--fscalastro=NONE] [--work=<dir>] [--stage=all|split|head|weight|norm|coadd|rgb|stamp]
#
# WHY THIS EXISTS. run_undistort_compose.sh (Siril seqplatesolve + seqapplyreg) is the
# shipped astrometric compose and it takes NO per-member weight map, so a member's
# measured-bad entry-side zone (the GO #13 asymmetry rule, cropT_arm.json) can only be
# removed by cropping — and removing it starves the coverage of the canvas rim those
# columns alone feed (the bottom-left staircase measured on sel57 / crop20 / cropT).
# SWarp takes a weight map per input: the zone is TAPERED (1 -> t_min, never zero), so
# where good cover exists the tapered columns contribute ~2 % and where they are the
# only cover the weighted mean keeps them. This is an ARM beside the shipped route,
# not the route; every stage is a tool's operation and this file orchestrates:
#
#   split  : Siril `split` each member -> R/G/B 2-D FITS (SWarp is 2-D; D1)
#   head   : per member a TPV .head beside each channel file (sip_tpv, exact; the FITS
#            is never rewritten) carrying FLXSCALE = s_ref/s_i (D4)
#   weight : per member a 2-D weight map w = STACKCNT * t(x) (swarp_weight_maps.py; D5)
#   norm   : Siril `seqstat ... full` on the linked members -> per-member per-channel
#            IKSS location/scale; BACK_DEFAULT_i = loc_i - loc_ref*(s_i/s_ref) (D4)
#   coadd  : SWarp x3 (one per channel), COMBINE_TYPE WEIGHTED, MAP_WEIGHT,
#            RESCALE_WEIGHTS N, SUBTRACT_BACK Y + BACK_TYPE MANUAL (the per-image list),
#            FSCALASTRO_TYPE NONE (D3), the output grid from coadd.head (D2)
#   rgb    : Siril `rgbcomp` -> the 3-plane product
#   stamp  : Siril `update_key`: NMEMBER/STACKCNT/REGREF/REGMODEL/STACKNRM/ANCREF/ANCLOC
#            + WMAPFORM/WMAPXC/WMAPMIN/PIPEREV; then finish_render.sh as for every arm
#
# The rulings D1-D8 and the probes' expected values are the pre-registration
# (datasets/aug06/experiments.jsonl, swtaper_weighted_form_probes); the probe results
# are datasets/corpus/smear_attribution/swtaper_probes.json. GO #15 exercised split /
# head / weight / norm and single- and two-member coadds through the functions below;
# the arm-scale run (77 members, three channels, rgb, stamp) is GO #16.
#
# NOTHING here reads or writes a deliverable pixel in-house: Siril splits, stats and
# recomposes; SWarp resamples and combines; the weight maps and .head files are inputs.
#
# REMOVAL CONDITION: retire when Siril's compose accepts per-member weight maps (a
# scriptable per-image weight input to `stack`/`seqapplyreg`, or an equivalent in the
# shipped route). Registered in BACKLOG `removal-conditions`.
set -uo pipefail
REPO=$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)
VENVPY=/opt/astro-venv/bin/python                 # sip_tpv lives here (manifest: sip_tpv 1.1)
WRITER="$REPO/scripts/stack/swarp_weight_maps.py"
SWARP=${SWARP:-/usr/bin/SWarp}                    # the binary is SWarp, not swarp (TOOLS.md)
. "$REPO/scripts/lib/siril_run.sh" 2>/dev/null || true   # the serialized invoker (siril_run_logged)

OUT= MEMBERS= GRID= REF= XCJSON= TMIN=0.02 KERNEL=LANCZOS4 FSCAL=NONE WORK= STAGE=all
for a in "$@"; do case "$a" in
  --out=*) OUT=${a#*=};; --members=*) MEMBERS=${a#*=};; --grid=*) GRID=${a#*=};; --ref=*) REF=${a#*=};;
  --xc-json=*) XCJSON=${a#*=};; --tmin=*) TMIN=${a#*=};; --kernel=*) KERNEL=${a#*=};; --fscalastro=*) FSCAL=${a#*=};;
  --work=*) WORK=${a#*=};; --stage=*) STAGE=${a#*=};;
  *) echo "unknown arg $a" >&2; exit 1;;
esac; done
[ -n "$OUT" ] && [ -d "$MEMBERS" ] && [ -f "$GRID" ] && [ -f "$REF" ] || { sed -n '2,12p' "$0"; exit 1; }
WORK=${WORK:-$(dirname "$OUT")/swarp_work_$(basename "${OUT%.fit}")}
mkdir -p "$WORK"; WORK=$(readlink -f "$WORK")   # Siril runs with -d $WORK: every path it is given must be absolute
CH="$WORK/channels"; mkdir -p "$CH" "$WORK/resamp"; MEMBERS=$(readlink -f "$MEMBERS"); OUT=$(readlink -f "$(dirname "$OUT")")/$(basename "$OUT"); GRID=$(readlink -f "$GRID"); REF=$(readlink -f "$REF")
sir(){ siril_run_logged "$WORK" "$1" "$WORK/siril.log"; }

# ---- split: one Siril script, every member (a symlink or a file) -> <name>_{R,G,B}.fit
stage_split(){
  local ssf="$WORK/split.ssf"; { printf 'requires 1.4.4\nset32bits\nsetcompress 0\nsetext fit\n'
  for m in "$MEMBERS"/*.fit; do local b; b=$(basename "${m%.fit}")
    printf 'load %s\nsplit %s %s %s\n' "$(readlink -f "$m")" "$CH/${b}_R" "$CH/${b}_G" "$CH/${b}_B"; done; } > "$ssf"
  sir "$ssf"; ls "$CH"/*_G.fit >/dev/null 2>&1 || { echo "split: no channel files — read $WORK/siril.log" >&2; return 1; }
}
# ---- head: TPV .head beside each channel file (the same WCS for R/G/B), FLXSCALE from the norm table
stage_head(){
  for m in "$MEMBERS"/*.fit; do local b; b=$(basename "${m%.fit}"); local f; f=$(norm_fscale "$b" G)
    for c in R G B; do "$VENVPY" "$WRITER" head "$(readlink -f "$m")" "$CH/${b}_${c}.head" --flxscale="$(norm_fscale "$b" "$c")" >/dev/null || return 1; done
    grep -q 'RA---TPV' "$CH/${b}_G.head" && grep -q '^PV1_' "$CH/${b}_G.head" || { echo "head: $b lacks TPV/PV terms" >&2; return 1; }; done
}
# ---- weight: one map per member, the same for R/G/B (WEIGHT_IMAGE list points the three channels at it)
stage_weight(){
  for m in "$MEMBERS"/*.fit; do local b; b=$(basename "${m%.fit}"); local src; src=$(readlink -f "$m")
    local cnt; cnt=$(python3 -c "from astropy.io import fits; print(int(fits.getheader('$src')['STACKCNT']))")
    local xc; xc=$(member_xc "$b")
    if [ -n "$xc" ]; then "$VENVPY" "$WRITER" weight "$src" "$CH/${b}.weight.fits" --stackcnt="$cnt" --xc="$xc" --tmin="$TMIN" >/dev/null
    else "$VENVPY" "$WRITER" weight "$src" "$CH/${b}.weight.fits" --stackcnt="$cnt" >/dev/null; fi || return 1; done
}
# ---- norm: Siril seqstat on the linked members -> $WORK/norm.csv (member, channel, location, scale)
stage_norm(){
  local d="$WORK/normseq"; mkdir -p "$d"; rm -f "$d"/*.fit "$d"/*.seq
  local i=0; for m in "$MEMBERS"/*.fit; do i=$((i+1)); ln -sfn "$(readlink -f "$m")" "$d/$(printf 'n_%05d.fit' "$i")"; done
  printf 'requires 1.4.4\nsetcompress 0\nsetext fit\ncd %s\nlink n -out=%s\ncd %s\nseqstat n %s full\n' "$d" "$d/seq" "$d/seq" "$WORK/seqstat.csv" > "$WORK/norm.ssf"
  sir "$WORK/norm.ssf"; [ -s "$WORK/seqstat.csv" ] || { echo "norm: seqstat wrote nothing — read $WORK/siril.log" >&2; return 1; }
  "$VENVPY" "$WRITER" norm "$WORK/seqstat.csv" "$MEMBERS" "$(readlink -f "$REF")" "$WORK/norm.csv" || return 1   # member,channel,loc,scale,fscale,back_default
}
norm_fscale(){ local v; v=$(awk -F, -v m="$1" -v c="$2" '$1==m && $2==c {print $5}' "$WORK/norm.csv" 2>/dev/null); echo "${v:-1.0}"; }   # no table -> unscaled
norm_back(){   local v; v=$(awk -F, -v m="$1" -v c="$2" '$1==m && $2==c {print $6}' "$WORK/norm.csv" 2>/dev/null); echo "${v:-0.0}"; }
member_xc(){ [ -n "$XCJSON" ] && python3 - "$1" "$XCJSON" <<'EOF'
import json, sys
name, p = sys.argv[1], sys.argv[2]
# curated names are sub_NNN_<night>_<set>_<sub>; the rule json is keyed night/set/sub
parts = name.split("_", 2)[2]; night, rest = parts.split("_", 1); st, sub = rest.rsplit("_", 1) if rest.count("_") == 1 else (rest[:6], rest[7:])
m = f"{night}/{st}/{sub}"
v = json.load(open(p))["per_member"].get(m, {})
print(v["x_c"] if v.get("cropped") and v.get("x_c") is not None else "")
EOF
}
# ---- coadd: one SWarp run per channel onto coadd.head (D2); every D7 setting explicit
stage_coadd(){
  "$VENVPY" "$WRITER" coadd-head "$GRID" "$WORK/coadd.head" >/dev/null || return 1
  for c in R G B; do
    local list="$WORK/inputs_$c.txt" wlist= blist=; : > "$list"
    for m in "$MEMBERS"/*.fit; do local b; b=$(basename "${m%.fit}")
      echo "$CH/${b}_${c}.fit" >> "$list"; wlist="${wlist:+$wlist,}$CH/${b}.weight.fits"; blist="${blist:+$blist,}$(norm_back "$b" "$c")"; done
    cp "$WORK/coadd.head" "$WORK/coadd_$c.head"
    "$SWARP" @"$list" -c /dev/null -IMAGEOUT_NAME "$WORK/coadd_$c.fits" -WEIGHTOUT_NAME "$WORK/coadd_$c.weight.fits" \
      -HEADER_SUFFIX .head -WEIGHT_TYPE MAP_WEIGHT -WEIGHT_IMAGE "$wlist" -RESCALE_WEIGHTS N -COMBINE_TYPE WEIGHTED \
      -BLANK_BADPIXELS N -SUBTRACT_BACK Y -BACK_TYPE MANUAL -BACK_DEFAULT "$blist" -FSCALASTRO_TYPE "$FSCAL" -FSCALE_KEYWORD FLXSCALE \
      -PROJECTION_TYPE TAN -RESAMPLING_TYPE "$KERNEL" -RESAMPLE_DIR "$WORK/resamp" -DELETE_TMPFILES Y -WRITE_XML Y -XML_NAME "$WORK/swarp_$c.xml" \
      -VMEM_MAX 16384 -MEM_MAX 8192 -COMBINE_BUFSIZE 4096 -NTHREADS 0 -COPY_KEYWORDS OBJECT -VERBOSE_TYPE NORMAL > "$WORK/swarp_$c.log" 2>&1 \
      || { echo "SWarp failed on $c — read $WORK/swarp_$c.log" >&2; return 1; }
  done
}
# ---- rgb + stamp: Siril rgbcomp -> the 3-plane product; provenance via update_key
stage_rgb(){
  printf 'requires 1.4.4\nset32bits\nsetcompress 0\nsetext fit\nrgbcomp %s %s %s -out=%s\n' "$WORK/coadd_R.fits" "$WORK/coadd_G.fits" "$WORK/coadd_B.fits" "${OUT%.fit}" > "$WORK/rgb.ssf"
  sir "$WORK/rgb.ssf"; [ -f "$OUT" ] || { echo "rgbcomp wrote nothing — read $WORK/siril.log" >&2; return 1; }
}
stage_stamp(){
  local n; n=$(ls "$MEMBERS"/*.fit | wc -l); local rev; rev=$(git -C "$REPO" rev-parse --short HEAD)
  local cnt; cnt=$(for m in "$MEMBERS"/*.fit; do python3 -c "from astropy.io import fits; print(int(fits.getheader('$(readlink -f "$m")')['STACKCNT']))"; done | awk '{s+=$1} END{print s}')
  printf 'requires 1.4.4\nsetcompress 0\nsetext fit\nload %s\nupdate_key NMEMBER %s\nupdate_key STACKCNT %s\nupdate_key REGMODEL "swarp-tpv"\nupdate_key REGUNDIS T\nupdate_key STACKNRM "addscale-swarp"\nupdate_key REGREF "%s"\nupdate_key WMAPFORM "STACKCNT*t(x); t=1|raised-cosine|tmin"\nupdate_key WMAPMIN %s\nupdate_key WMAPXC "%s"\nupdate_key PIPEREV "%s"\nsave %s\n' \
    "$OUT" "$n" "$cnt" "$(basename "$REF")" "$TMIN" "${XCJSON:-none}" "$rev" "${OUT%.fit}" > "$WORK/stamp.ssf"
  sir "$WORK/stamp.ssf"
}
case "$STAGE" in
  all) stage_split && stage_norm && stage_head && stage_weight && stage_coadd && stage_rgb && stage_stamp;;
  split) stage_split;; norm) stage_norm;; head) stage_head;; weight) stage_weight;; coadd) stage_coadd;; rgb) stage_rgb;; stamp) stage_stamp;;
  *) echo "--stage must be all|split|norm|head|weight|coadd|rgb|stamp" >&2; exit 1;;
esac
