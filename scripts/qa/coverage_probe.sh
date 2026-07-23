#!/usr/bin/env bash
# Per-pixel COVERAGE MAP for a sub-stack compose — the framing instrument.
# Registers the REAL members (register -2pass stores the transforms), swaps
# each member for a constant-filled twin (Siril `fill`), applies the STORED
# transforms (seqapplyreg re-detects nothing), and sum-stacks: the output's
# value/1000 = how many members cover each pixel. Siril does every pixel op;
# the map is a PROBE instrument, never the deliverable.
#
#   coverage_probe.sh --out=<map.fit> <substack-dir>... [--framing=max]
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
# as the product crop and require `stat` Min >= threshold*1000 — this same
# check catches the numpy-vs-Siril crop y-origin flip, docs/dead-ends.md).
#
# MEASURED LIMITS (Siril 1.4.4; datasets/july14_fresh-start/set-01/qa_work/coverage_01345.json):
# - members*1000 saturates at 65535: Siril normalizes 16-bit input to [0,1],
#   so the sum CLIPS there regardless of a 32-bit stack output — above 65
#   members the map cannot distinguish coverage depths (thresholds <= 65*1000
#   stay valid; the script warns). Shrinking the fill constant would lift the
#   ceiling but silently break the value/1000 contract consumers verify with.
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
OUT= FRAMING=max; DIRS=()
for a in "$@"; do case "$a" in
  --out=*) OUT=${a#*=};; --framing=*) FRAMING=${a#*=};;
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
sir(){ flatpak run --command=siril-cli org.siril.Siril -d "$W" -s "$1" >> "$W/siril.log" 2>&1; }

n=0
for d in "${DIRS[@]}"; do
  [ -d "$d" ] || { echo "no such dir: $d" >&2; exit 1; }
  shopt -s nullglob; subs=("$d"/sub_*.fit); shopt -u nullglob
  [ ${#subs[@]} -ge 1 ] || { echo "no sub_*.fit in $d" >&2; exit 1; }
  for s in "${subs[@]}"; do n=$((n+1)); ln -sf "$(readlink -f "$s")" "$W/in/m_$(printf %05d "$n").fit"; done
done
[ "$n" -ge 2 ] || { echo "need >=2 members" >&2; exit 1; }
echo "coverage probe: $n members, framing=$FRAMING"

{ printf 'requires 1.2.0\nset16bits\nsetcompress 0\n'
  for ((i=1;i<=n;i++)); do
    printf 'load %s/in/m_%05d\nfill 1000\nsave %s/const/c_%05d\n' "$W" "$i" "$W" "$i"
  done; } > "$W/f.ssf"
sir "$W/f.ssf"
[ "$(ls "$W/const" | wc -l)" -eq "$n" ] || { echo "ABORT: const twins incomplete — read $W/siril.log" >&2; exit 1; }
printf 'requires 1.2.0\nset16bits\nsetcompress 0\ncd %s/in\nlink s -out=%s/seq\ncd %s/seq\nregister s -2pass\n' "$W" "$W" "$W" > "$W/r.ssf"
sir "$W/r.ssf"
[ -f "$W/seq/s_.seq" ] || { echo "ABORT: registration wrote no .seq — read $W/siril.log" >&2; exit 1; }
for ((i=1;i<=n;i++)); do
  rm -f "$W/seq/s_$(printf %05d "$i").fit"
  mv "$W/const/c_$(printf %05d "$i").fit" "$W/seq/s_$(printf %05d "$i").fit"
done
[ "$n" -le 65 ] || echo "WARNING: $n members exceed the 65535/1000 sum ceiling — map values clip at 65535 (65.5 members); coverage thresholds <= 65 remain valid (see docstring)"
printf 'requires 1.2.0\nset16bits\nsetcompress 0\ncd %s/seq\nseqapplyreg s -framing=%s -prefix=r_\nset32bits\nstack r_s sum -out=%s\n' \
  "$W" "$FRAMING" "$OUT" > "$W/a.ssf"
sir "$W/a.ssf"
[ -f "$OUT.fit" ] || { echo "ABORT: no coverage map — read $W/siril.log" >&2; exit 1; }
rm -rf "$W"
echo "=== DONE: $OUT.fit (value/1000 = member coverage; VERIFY canvas vs the compose product) ==="
ls -la "$OUT.fit"
