#!/usr/bin/env bash
# Compose already-built undistort SUB-STACKS into one deep stack — the cross-set
# final for the wide-field UNTRACKED class. run_undistort_groups.sh builds a
# set's sub-stacks (calibrate -> warp -> register -> reject, per group) and
# composes its OWN into stack_<set>_full; this composes sub-stacks from SEVERAL
# sets (or group dirs) into a single deeper stack, reusing the warping already
# done — no frame is re-processed.
#
#   run_undistort_compose.sh --out=<stack.fit> <subdir>... [--framing=min|max] [--weight=nbstack|noise]
#                            [--ref=<sub-stack path>|<1-based index>]
#
# e.g. run_undistort_compose.sh --out=web/results/july14/stack_set-01+02_full.fit \
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
# the compose work). -framing=max keeps the union (edges covered by fewer
# sub-stacks; depth/SNR fall off outward). Re-run with the same dirs to switch
# framing without recomputing sub-stacks.
#
# --ref PINS THE REFERENCE, and on a multi-night compose it must be pinned.
# `register -2pass`'s AUTO reference sets the output canvas ORIENTATION and,
# through `-norm=addscale`, the composite's raw channel BALANCE: a compose
# referenced to the wrong family measured K_B 0.846 (that member's own balance)
# with a rotated frame map, where the right reference gave 0.951 and an exact
# map. Within one night the members share a balance family and the auto pick is
# harmless. Across NIGHTS the families genuinely differ (measured on this rig:
# K_G 0.662-0.668 one night vs 0.697 another, both chain-clean — a transparency
# difference, not a defect), so whichever member the auto pick lands on silently
# decides the composite's starting balance and orientation. Pinning it makes
# that a recorded choice instead of a function of argument order. SPCC
# afterwards re-derives colour from the catalogue, so this governs the LINEAR
# composite the finish stage receives, not the final colour.
# Pick the member whose canvas the product should inherit — normally the
# deepest/most-central one. Accepts a sub-stack PATH (preferred; resolved to
# its linked index) or a bare 1-based index into the linked order.
#
# The compose is a PLAIN MEAN, never sigma rejection: sub-stacks are clean
# ~group-size means whose mutual scatter is ~sqrt(group) below per-frame noise,
# so a sigma gate across them clips real structure (star cores, MW lanes) along
# steep gradients instead of outliers (measured; docs/dead-ends.md). Rejection
# already happened WITHIN each group, at full per-frame strength.
#
# NOTHING is compressed; the generated .ssf pins setcompress 0. The flatpak
# sandbox has a private /tmp, so the scratch dir lives beside --out (under $HOME).
# WEIGHTING (--weight=nbstack | --weight=noise; default unweighted).
# A sub-stack of n frames each with per-frame variance s^2 has variance
# s^2/n, so the inverse-variance weight is n/s^2:
# - `nbstack` weights by stacked-image COUNT, i.e. by n. That IS the
#   inverse-variance weight — but ONLY while every member's per-frame noise s
#   is the same. True for members from one night/sky; the Siril doctrine that
#   nbstack is "for stacks-of-stacks" is about that regime.
# - `noise` weights by the MEMBER's measured noise, which already carries
#   s/sqrt(n) — so it yields n/s^2 in BOTH regimes and is strictly more
#   general. Prefer it for a MULTI-NIGHT compose, where sky brightness (and
#   therefore per-frame noise for a fixed object flux) differs between members
#   and count-weighting would over-weight the noisier night's frames.
#   Caveat: Siril's noise estimator conflates revealed texture with noise
#   (docs/dead-ends.md), which is tolerable here only because every member
#   shows the SAME field, so the texture term is common and largely cancels in
#   the relative weights. On members of different fields, do not trust it.
set -euo pipefail
OUT= FRAMING=min WEIGHT= REF=; SUBDIRS=()
for a in "$@"; do case "$a" in
  --out=*) OUT=${a#*=};; --framing=*) FRAMING=${a#*=};;
  --weight=nbstack|--weight=noise) WEIGHT="-weight=${a#*=}";;
  --ref=*) REF=${a#*=};;
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
n=0; MEMBERS=()
for d in "${SUBDIRS[@]}"; do
  [ -d "$d" ] || { echo "no such sub-stack dir: $d" >&2; exit 1; }
  shopt -s nullglob; subs=("$d"/sub_*.fit); shopt -u nullglob
  [ ${#subs[@]} -ge 1 ] || { echo "no sub_*.fit in $d" >&2; exit 1; }
  for s in "${subs[@]}"; do
    n=$((n + 1))
    MEMBERS[$n]=$(readlink -f "$s")
    ln -sf "${MEMBERS[$n]}" "$W/in/m_$(printf %05d "$n").fit"
  done
  echo "linked ${#subs[@]} sub-stacks from $(basename "$d")"
done
[ "$n" -ge 2 ] || { echo "ABORT: need >=2 sub-stacks total to register+stack, have $n" >&2; exit 1; }

# resolve --ref to a 1-based sequence index (m_ names are zero-padded in link
# order, so the linked index IS the sequence index)
SETREF=
if [ -n "$REF" ]; then
  RIDX=
  if [[ "$REF" =~ ^[0-9]+$ ]]; then
    RIDX=$REF
    [ "$RIDX" -ge 1 ] && [ "$RIDX" -le "$n" ] || {
      echo "ABORT: --ref=$REF out of range (1..$n)" >&2; exit 1; }
  else
    RP=$(readlink -f "$REF" 2>/dev/null || true)
    [ -n "$RP" ] || { echo "ABORT: --ref path does not resolve: $REF" >&2; exit 1; }
    for ((i=1; i<=n; i++)); do [ "${MEMBERS[$i]}" = "$RP" ] && RIDX=$i && break; done
    [ -n "$RIDX" ] || {
      echo "ABORT: --ref=$REF is not one of the $n linked sub-stacks" >&2
      for ((i=1; i<=n; i++)); do echo "   $i  ${MEMBERS[$i]}" >&2; done; exit 1; }
  fi
  SETREF="setref s $RIDX\n"
  echo "reference PINNED: member $RIDX -> ${MEMBERS[$RIDX]}"
else
  echo "reference: AUTO (register -2pass picks it) — pin it with --ref= for a"
  echo "  multi-night compose; the auto pick decides canvas orientation and the"
  echo "  composite's raw channel balance"
fi

# %b (not %s) for the setref line: it carries its own trailing newline as an
# escape, and collapses to nothing when the reference is left AUTO
printf 'requires 1.2.0\nset32bits\nsetcompress 0\ncd %s\nlink s -out=%s\ncd %s\nregister s -2pass\n%bseqapplyreg s -framing=%s -prefix=r_\nstack r_s mean none -norm=addscale %s -output_norm -out=%s\n' \
  "$W/in" "$W/seq" "$W/seq" "$SETREF" "$FRAMING" "$WEIGHT" "$OUT" > "$W/compose.ssf"
# State the weighting explicitly: "plain mean" printed unconditionally would be
# a WRONG RECORD whenever --weight=nbstack was passed, and this log is the
# build's provenance.
case "$WEIGHT" in
  -weight=nbstack) WDESC="weighted by stacked-image count (nbstack)";;
  -weight=noise)   WDESC="weighted by member noise, inverse-variance (noise)";;
  *)               WDESC="unweighted";;
esac
echo "composing $n sub-stacks (register -2pass -> ${SETREF:+setref $RIDX -> }-framing=$FRAMING -> mean, no rejection, $WDESC)"
sir "$W/compose.ssf"
[ -f "$OUT.fit" ] || { echo "COMPOSE FAILED — read $W/compose.log" >&2; exit 1; }
rm -rf "$W"
echo "=== DONE: $OUT.fit ($n sub-stacks, framing=$FRAMING) ==="
ls -la "$OUT.fit"
