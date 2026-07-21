#!/usr/bin/env bash
# Half-split difference noise test — separates RANDOM noise from the static
# structure that floors whole-image bgnoise (unresolved-star confusion +
# sensor-pattern residual). One registration of the given sub-stacks, two
# subset MEANS per split, A−B difference: everything identical in both halves
# cancels, so `bgnoise` on the difference reads √2 × the per-half RANDOM σ.
# Two splits, two meanings:
#   interleaved (odd/even by member order) — halves share the drift-smeared
#     sensor pattern almost exactly → the diff is the cleanest random-σ read;
#   timehalf (first half vs second)        — the pattern sits at different
#     drift phases → any excess of timehalf σ over interleaved σ is the
#     STRUCTURED (walking-noise-class) component, fingerprinted.
# Every pixel op is Siril's (link / register -2pass / seqapplyreg -framing=min
# / stack mean / isub / bgnoise / stat); this orchestrates and records. 32-bit
# processing mode throughout — a 16-bit difference would clip negatives and
# quantize the sub-ADU σ under test.
#
#   noise_split.sh --out=<record.json> --work=<scratch-dir> <substack-dir>...
#
# Sub-stacks are linked in argument order (the compose-driver convention).
# -framing=min keeps the all-members intersection: uniform full depth, no
# coverage-varying zones in the statistics.
set -euo pipefail
OUT= WORK=; DIRS=()
for a in "$@"; do case "$a" in
  --out=*) OUT=${a#*=};; --work=*) WORK=${a#*=};;
  --*) echo "unknown arg $a" >&2; exit 1;;
  *) DIRS+=("$a");;
esac; done
[ -n "$OUT" ] && [ -n "$WORK" ] || { echo "need --out=<record.json> --work=<scratch>" >&2; exit 1; }
[ ${#DIRS[@]} -ge 1 ] || { echo "give sub-stack dir(s)" >&2; exit 1; }
mkdir -p "$(dirname "$OUT")"
rm -rf "$WORK"; mkdir -p "$WORK/in" "$WORK/seq"
W="$(cd "$WORK" && pwd)"
OUT="$(cd "$(dirname "$OUT")" && pwd)/$(basename "$OUT")"
sir(){ flatpak run --command=siril-cli org.siril.Siril -d "$W" -s "$1" >> "$W/siril.log" 2>&1; }

n=0
for d in "${DIRS[@]}"; do
  shopt -s nullglob; subs=("$d"/sub_*.fit); shopt -u nullglob
  [ ${#subs[@]} -ge 1 ] || { echo "no sub_*.fit in $d" >&2; exit 1; }
  for s in "${subs[@]}"; do n=$((n+1)); ln -sf "$(readlink -f "$s")" "$W/in/m_$(printf %05d $n).fit"; done
done
[ "$n" -ge 4 ] || { echo "need >=4 members to split" >&2; exit 1; }
echo "noise split: $n members"

printf 'requires 1.2.0\nset32bits\nsetcompress 0\ncd %s/in\nlink s -out=%s/seq\ncd %s/seq\nregister s -2pass\nseqapplyreg s -framing=min -prefix=r_\n' \
  "$W" "$W" "$W" > "$W/r.ssf"
sir "$W/r.ssf"
[ -f "$W/seq/r_s_00001.fit" ] || { echo "ABORT: no registered frames — read $W/siril.log" >&2; exit 1; }

# subset symlink dirs: interleaved odd/even + first/second time halves
mkdir -p "$W/odd" "$W/even" "$W/h1" "$W/h2"
half=$(( (n + 1) / 2 ))
for ((i=1;i<=n;i++)); do
  f="$W/seq/r_s_$(printf %05d $i).fit"
  [ -f "$f" ] || { echo "ABORT: registered frame $i missing (registration dropped a member — the split needs all)" >&2; exit 1; }
  if (( i % 2 )); then ln -sf "$f" "$W/odd/r_$(printf %05d $i).fit"; else ln -sf "$f" "$W/even/r_$(printf %05d $i).fit"; fi
  if (( i <= half )); then ln -sf "$f" "$W/h1/r_$(printf %05d $i).fit"; else ln -sf "$f" "$W/h2/r_$(printf %05d $i).fit"; fi
done
for q in odd even h1 h2; do
  mkdir -p "$W/${q}_seq"
  printf 'requires 1.2.0\nset32bits\nsetcompress 0\ncd %s/%s\nlink q -out=%s/%s_seq\ncd %s/%s_seq\nstack q mean none -norm=addscale -out=%s/mean_%s\n' \
    "$W" "$q" "$W" "$q" "$W" "$q" "$W" "$q" > "$W/s_$q.ssf"
  sir "$W/s_$q.ssf"
  [ -f "$W/mean_$q.fit" ] || { echo "ABORT: subset $q stack missing" >&2; exit 1; }
done

diffstats(){ # $1=A $2=B $3=tag -> lines "tag bgnoise: ..." + "tag stat: ..."
  printf 'requires 1.2.0\nset32bits\nsetcompress 0\nload %s\nisub %s\nbgnoise\nstat\n' "$1" "$2" > "$W/d.ssf"
  flatpak run --command=siril-cli org.siril.Siril -d "$W" -s "$W/d.ssf" 2>&1 \
    | grep -E 'Background noise value|Mean:' | sed "s/^log: /$3 /"
}
{ diffstats "$W/mean_odd.fit"  "$W/mean_even.fit" "interleaved"
  diffstats "$W/mean_h1.fit"   "$W/mean_h2.fit"   "timehalf"
  printf 'requires 1.2.0\nset32bits\nsetcompress 0\nload %s\nbgnoise\n' "$W/mean_odd.fit" > "$W/d.ssf"
  flatpak run --command=siril-cli org.siril.Siril -d "$W" -s "$W/d.ssf" 2>&1 \
    | grep -E 'Background noise value' | sed 's/^log: /halfstack /'
} > "$W/results.txt"
cat "$W/results.txt"

python3 - "$W/results.txt" "$OUT" "$n" <<'PY'
import json, re, sys
txt, out, n = open(sys.argv[1]).read(), sys.argv[2], int(sys.argv[3])
def noise(tag):
    return [float(v) for v in re.findall(
        rf"{tag} Background noise value \(channel: #\d\): ([0-9.eE+-]+)", txt)]
inter, half, hstack = noise("interleaved"), noise("timehalf"), noise("halfstack")
rec = {"members": n,
       "diff_bgnoise_interleaved": inter,
       "diff_bgnoise_timehalf": half,
       "random_sigma_per_half_interleaved": [round(v / 2**0.5, 4) for v in inter],
       "halfstack_total_bgnoise": hstack,
       "note": "random σ per half = interleaved diff / sqrt(2); timehalf excess "
               "over interleaved = the structured (drift-phase) component; "
               "halfstack_total_bgnoise is the same half's whole-image bgnoise "
               "(structure INCLUDED) for the floor comparison. 32-bit chain; "
               "inputs are 16-bit sub-stacks (quantization σ 0.29/sqrt(members/2) "
               "per half, declared).", }
json.dump(rec, open(out, "w"), indent=1)
print("record:", out)
PY
rm -rf "$W/odd" "$W/even" "$W/h1" "$W/h2" "$W"/*_seq "$W/seq" "$W/in"
echo "=== DONE ==="
