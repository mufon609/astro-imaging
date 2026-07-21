#!/usr/bin/env bash
# Compose already-built undistort SUB-STACKS into one deep stack — the cross-set
# final for the wide-field UNTRACKED class. run_undistort_groups.sh builds a
# set's sub-stacks (calibrate -> warp -> register -> reject, per group) and
# composes its OWN into stack_<set>_full; this composes sub-stacks from SEVERAL
# sets (or group dirs) into a single deeper stack, reusing the warping already
# done — no frame is re-processed.
#
#   run_undistort_compose.sh --out=<stack.fit> <subdir>... [--framing=min|max]
#
# e.g. run_undistort_compose.sh --out=results/july14/stack_set-01+02_full.fit \
#        july14/work/groups_set-01 july14/work/groups_set-02
#
# WHY IT COMPOSES CLEANLY ACROSS SETS: after the lens-distortion warp every
# frame-to-frame map is a pure homography, and homographies COMPOSE — so a
# sub-stack from ANY set registers to the common reference with no model error,
# and a manual re-aim between sets is indistinguishable from within-set drift
# (same register -2pass). This is the SAME validity that lets the group builder
# compose within a set; it does NOT hold on un-warped frames (the residual
# distortion re-enters at the sub-stack join — a measured dead end,
# docs/dead-ends.md).
#
# -framing=min keeps the area common to ALL sub-stacks — across sets that is the
# re-aim OVERLAP, so measure the re-aim scatter first (a large re-aim shrinks it;
# BACKLOG item 8). -framing=max keeps the union (edges covered by fewer
# sub-stacks; depth/SNR fall off outward). Re-run with the same dirs to switch
# framing without recomputing sub-stacks.
#
# The compose is a PLAIN MEAN, never sigma rejection: sub-stacks are clean
# ~group-size means whose mutual scatter is ~sqrt(group) below per-frame noise,
# so a sigma gate across them clips real structure (star cores, MW lanes) along
# steep gradients instead of outliers (measured; docs/dead-ends.md). Rejection
# already happened WITHIN each group, at full per-frame strength.
#
# NOTHING is compressed; the generated .ssf pins setcompress 0. The flatpak
# sandbox has a private /tmp, so the scratch dir lives beside --out (under $HOME).
# --weight=nbstack is the STACKS-OF-STACKS weighting (Siril doctrine: nbstack
# is only for stacks-of-stacks): members of unequal depth are weighted by
# their stacked-image count, so a mean of per-set FULL stacks approximates the
# per-frame-equal weighting the all-sub-stacks compose gives natively (counts
# are proportional to frames within a few % at ~15-frame groups). Default
# remains the plain unweighted mean for equal-depth sub-stack members.
set -euo pipefail
OUT= FRAMING=min WEIGHT=; SUBDIRS=()
for a in "$@"; do case "$a" in
  --out=*) OUT=${a#*=};; --framing=*) FRAMING=${a#*=};;
  --weight=nbstack) WEIGHT="-weight=nbstack";;
  --*) echo "unknown arg $a" >&2; exit 1;;
  *) SUBDIRS+=("$a");;
esac; done
[ -n "$OUT" ] || { echo "need --out=<stack.fit>" >&2; exit 1; }
case "$FRAMING" in min|max) ;; *) echo "--framing must be min or max" >&2; exit 1;; esac
[ ${#SUBDIRS[@]} -ge 1 ] || { echo "give at least one sub-stack dir (holding sub_*.fit)" >&2; exit 1; }
OUT=${OUT%.fit}
mkdir -p "$(dirname "$OUT")"
# Absolutize: the flatpak Siril sandbox resolves -s/-d and every `cd` in the
# .ssf from its OWN cwd, so a relative --out makes it miss the generated script.
OUT="$(cd "$(dirname "$OUT")" && pwd)/$(basename "$OUT")"
W="$(dirname "$OUT")/.compose_$(basename "$OUT")"
rm -rf "$W"; mkdir -p "$W/in" "$W/seq"
sir(){ flatpak run --command=siril-cli org.siril.Siril -d "$W" -s "$1" >> "$W/compose.log" 2>&1; }

# Gather every sub-stack into one dir as uniquely-named symlinks (siril `link`
# takes ALL images in the CWD, so the dir must hold ONLY the members; the
# per-set names collide, hence the global index). Order is immaterial to a mean.
n=0
for d in "${SUBDIRS[@]}"; do
  [ -d "$d" ] || { echo "no such sub-stack dir: $d" >&2; exit 1; }
  shopt -s nullglob; subs=("$d"/sub_*.fit); shopt -u nullglob
  [ ${#subs[@]} -ge 1 ] || { echo "no sub_*.fit in $d" >&2; exit 1; }
  for s in "${subs[@]}"; do
    n=$((n + 1))
    ln -sf "$(readlink -f "$s")" "$W/in/m_$(printf %05d "$n").fit"
  done
  echo "linked ${#subs[@]} sub-stacks from $(basename "$d")"
done
[ "$n" -ge 2 ] || { echo "ABORT: need >=2 sub-stacks total to register+stack, have $n" >&2; exit 1; }

printf 'requires 1.2.0\nset16bits\nsetcompress 0\ncd %s\nlink s -out=%s\ncd %s\nregister s -2pass\nseqapplyreg s -framing=%s -prefix=r_\nstack r_s mean none -norm=addscale %s -output_norm -out=%s\n' \
  "$W/in" "$W/seq" "$W/seq" "$FRAMING" "$WEIGHT" "$OUT" > "$W/compose.ssf"
echo "composing $n sub-stacks (register -2pass -> -framing=$FRAMING -> plain mean)"
sir "$W/compose.ssf"
[ -f "$OUT.fit" ] || { echo "COMPOSE FAILED — read $W/compose.log" >&2; exit 1; }
rm -rf "$W"
echo "=== DONE: $OUT.fit ($n sub-stacks, framing=$FRAMING) ==="
ls -la "$OUT.fit"
