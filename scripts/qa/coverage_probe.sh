#!/usr/bin/env bash
# Per-pixel COVERAGE MAP for a sub-stack compose — the framing instrument.
# Registers the REAL members (register -2pass stores the transforms), swaps
# each member for a constant-filled twin (Siril `fill`), applies the STORED
# transforms (seqapplyreg re-detects nothing), and sum-stacks. The output is
# PROPORTIONAL to how many members cover each pixel. Siril does every pixel op;
# the map is a PROBE instrument, never the deliverable.
#
# THE `value/1000 = members` CONTRACT THIS FILE USED TO CLAIM IS FALSE —
# MEASURED, and it made the map UNCONSUMABLE by a fixed threshold.
# `stack ... sum` RENORMALISES its output to full scale, so the `fill 1000`
# constant CANCELS and does not survive into the product. Measured on this rig,
# reading the written map directly:
#   3 members -> raw floats 0, 0.3333, 0.6667, 1.0   (Siril `stat` Max 65535)
#   4 members -> raw floats 0, 0.25, 0.50, 0.75, 1.0
# i.e. the value is `members / max_coverage`, NOT `members * 1000`. A consumer
# forming a threshold as `map-min * 1000` is therefore wrong for THIS map too,
# not merely for a foreign one — at 3 members, one member reads 21845 where the
# contract predicted 1000.
#
# CONSEQUENCE, and it is why this script stamps no scale: the map's
# ADU-per-member is `65535 / max_coverage`, and max_coverage is NOT knowable
# here. That is now MEASURED, not merely unestablished.
#
# `stack ... sum` NORMALISES BY THE OBSERVED MAXIMUM, not by N. Settled on a
# PLANTED fixture that pins the geometry outright, because three attempts on
# real members could not build the discriminating case — registration drops the
# non-overlapping member and STACKCNT comes back reduced, so max_coverage == N
# every time. Three frames, disjoint-then-chained halves, coverage 1,2,2,1
# across x, so max_coverage = 2 while N = 3:
#
#   MEASURED levels  0.5, 1.0        (= k / max_coverage)  <- observed maximum
#   would have been  0.333, 0.667    (= k / N)             <- N
#
# So `65535/STACKCNT` is WRONG, and provably: on that fixture it reads a
# 2-member maximum as if it were 3. Stamping it would have been a second
# guessed constant on top of the one that caused the false PASS.
#
# NO OTHER SIRIL STACK MODE RECOVERS AN ABSOLUTE COUNT — probed on the same
# fixture, commands run rather than help read:
#   sum          renormalises to the observed max (above)
#   mean / rej   DISCARDS coverage entirely: every level collapses to the fill
#                value (single level 1000 ADU across coverage 1 AND 2), tested
#                with `mean none -nonorm`, `mean n 0 0 -nonorm`, `rej n 0 0
#                -nonorm` — all three identical
#   max / min    a binary footprint, never a count
#   med          a median, which does not count either
# `-output_norm` is documented for "median and mean stacking only", so sum's
# rescale cannot be switched off.
#
# THE ROUTE THAT REMAINS is not another constant: either recover max_coverage
# from the map's own level ladder (the step is 1/max_coverage, but lanczos4
# ringing pollutes it and it is an inference from pixels), or change what
# `--map-min` MEANS — a fraction of the maximum coverage is well defined from
# the map alone, where a member COUNT is not. The second is a contract change
# and is not this script's call to make.
# `verify_framing.py --map` REFUSES a map that declares no scale, so this
# script's output is refused by design until one of those lands.
#
#   coverage_probe.sh --out=<map.fit> <substack-dir>... [--framing=max]
#                     [--ref=<1-based index in link order>]
#
# --ref pins the registration REFERENCE (setref after the -2pass, the same
# re-basing the compose script uses) so the map's canvas matches a compose
# pinned to the SAME member — without it both auto-pick and the doc's
# dimensions-check is the only guard. Link order = argument order, so the
# index is computable from the member counts.
#
# Same member interface + order as run_undistort_compose.sh (dirs of
# sub_*.fit, linked in argument order), so the map reproduces the compose's
# canvas when registration picks the same reference — VERIFY the map's
# dimensions equal the compose product's before using it (geometry check;
# a mismatch means re-compose from this probe's own registration).
#
# MEASURED uses (both in the ledgers): the true all-members common area vs
# `-framing=min` (min's axis-aligned rectangle kept 5.50 of 15.25 Mpx on 50
# rotated members — min discards ~2/3 of full-depth sky under rotation), and
# coverage-thresholded crop selection (crop the MAP with the exact same args
# as the product crop and require `stat` Min >= the threshold in the map's OWN
# scale — this same check catches the numpy-vs-Siril crop y-origin flip,
# docs/dead-ends.md; see the renormalisation note above for why that scale is
# not `*1000` and is currently undeclarable).
#
# MEASURED LIMITS (Siril 1.4.4; datasets/july14/set-01/qa_work/coverage_01345.json):
# - a 65-member depth ceiling was recorded here from `members*1000` saturating
#   at 65535. That arithmetic assumed the false contract above: the sum is
#   renormalised, so the fill constant cancels and there is no *1000 to clip.
#   The ceiling is therefore UNVERIFIED as stated and the warning below quotes
#   it — re-measure it against the renormalised scale before relying on it.
#   What IS measured is that a 32-bit output resolves the 1/max_coverage steps
#   cleanly at the depths tested (3 and 4 members).
# - the apply+sum must run over the FULL sequence in ONE pass: the applied
#   sequence's residual pure-translation regdata is CHUNK-relative (the same
#   frame lands at different origins under different selections), so chunked
#   partial sums cannot be composed; without -filter-incl the selection is
#   ignored entirely. Deselecting the reference frame NULLS the .seq
#   reference field (restore with `setref`).
#
# Nothing is compressed; the .ssf pins setcompress 0. The scratch lives
# beside --out (under $HOME — the Siril flatpak has a private /tmp).
set -euo pipefail
REPO=$(cd "$(dirname "${BASH_SOURCE[0]}")"/../.. && pwd)
source "$REPO/scripts/lib/siril_run.sh"   # serialized siril-cli invoker (BACKLOG:removal-conditions)
OUT= FRAMING=max REF=; DIRS=()
for a in "$@"; do case "$a" in
  --out=*) OUT=${a#*=};; --framing=*) FRAMING=${a#*=};;
  --ref=*) REF=${a#*=};;
  --*) echo "unknown arg $a" >&2; exit 1;;
  *) DIRS+=("$a");;
esac; done
[ -n "$OUT" ] || { echo "need --out=<map.fit>" >&2; exit 1; }
[ ${#DIRS[@]} -ge 1 ] || { echo "give at least one sub-stack dir (sub_*.fit)" >&2; exit 1; }
OUT=${OUT%.fit}
mkdir -p "$(dirname "$OUT")"
OUT="$(cd "$(dirname "$OUT")" && pwd)/$(basename "$OUT")"
W="$(dirname "$OUT")/.covprobe_$(basename "$OUT")"
rm -rf "$W"; mkdir -p "$W/in" "$W/seq" "$W/const"
sir(){ siril_cli -d "$W" -s "$1" >> "$W/siril.log" 2>&1; }

n=0
for d in "${DIRS[@]}"; do
  [ -d "$d" ] || { echo "no such dir: $d" >&2; exit 1; }
  shopt -s nullglob; subs=("$d"/sub_*.fit); shopt -u nullglob
  [ ${#subs[@]} -ge 1 ] || { echo "no sub_*.fit in $d" >&2; exit 1; }
  for s in "${subs[@]}"; do n=$((n+1)); ln -sf "$(readlink -f "$s")" "$W/in/m_$(printf %05d "$n").fit"; done
done
[ "$n" -ge 2 ] || { echo "need >=2 members" >&2; exit 1; }
echo "coverage probe: $n members, framing=$FRAMING"

{ printf 'requires 1.2.0\nset16bits\nsetcompress 0\nsetext fit\n'
  for ((i=1;i<=n;i++)); do
    printf 'load %s/in/m_%05d\nfill 1000\nsave %s/const/c_%05d\n' "$W" "$i" "$W" "$i"
  done; } > "$W/f.ssf"
sir "$W/f.ssf"
[ "$(ls "$W/const" | wc -l)" -eq "$n" ] || { echo "ABORT: const twins incomplete — read $W/siril.log" >&2; exit 1; }
printf 'requires 1.2.0\nset16bits\nsetcompress 0\nsetext fit\ncd %s/in\nlink s -out=%s/seq\ncd %s/seq\nregister s -2pass -transf=homography\n' "$W" "$W" "$W" > "$W/r.ssf"
sir "$W/r.ssf"
[ -f "$W/seq/s_.seq" ] || { echo "ABORT: registration wrote no .seq — read $W/siril.log" >&2; exit 1; }
for ((i=1;i<=n;i++)); do
  rm -f "$W/seq/s_$(printf %05d "$i").fit"
  mv "$W/const/c_$(printf %05d "$i").fit" "$W/seq/s_$(printf %05d "$i").fit"
done
[ "$n" -le 65 ] || echo "WARNING: $n members exceed the 65535/1000 sum ceiling — map values clip at 65535 (65.5 members); coverage thresholds <= 65 remain valid (see docstring)"
if [ -n "$REF" ]; then
  { [ "$REF" -ge 1 ] && [ "$REF" -le "$n" ]; } 2>/dev/null \
    || { echo "ABORT: --ref=$REF is not a 1..$n link index" >&2; exit 1; }
  echo "reference pinned: member $REF of $n (setref after -2pass, the compose's own re-basing)"
fi
# The map must be read at the SAME interpolation the composed product carries:
# lanczos4 rings at a member's edge, so a coverage threshold calibrated under a
# different kernel does not transfer (the Min > 0 crop guard already passes on
# that ringing — docs/dead-ends.md).
printf 'requires 1.2.0\nset16bits\nsetcompress 0\nsetext fit\ncd %s/seq\n%sseqapplyreg s -framing=%s -prefix=r_ -interp=lanczos4\nset32bits\nstack r_s sum -out=%s\n' \
  "$W" "${REF:+setref s $REF$'\n'}" "$FRAMING" "$OUT" > "$W/a.ssf"
sir "$W/a.ssf"
[ -f "$OUT.fit" ] || { echo "ABORT: no coverage map — read $W/siril.log" >&2; exit 1; }
rm -rf "$W"
echo "=== DONE: $OUT.fit (value is PROPORTIONAL to member coverage — the sum is"
echo "    renormalised, so value/1000 is NOT the member count; see the header note."
echo "    verify_framing.py --map REFUSES this map until its scale is declarable."
echo "    VERIFY canvas vs the compose product) ==="
ls -la "$OUT.fit"
