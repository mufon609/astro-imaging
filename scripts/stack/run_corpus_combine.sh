#!/usr/bin/env bash
# THE FINAL COMBINE — every member from every night into one stack, then one
# render of the full wide canvas.
#
#   run_corpus_combine.sh <session-dir>... [--out=<stack.fit>] [--framing=min|max]
#                         [--weight=nbstack|noise] [--plan]
#
# e.g. run_corpus_combine.sh sessions/july31 sessions/aug06 sessions/aug09
#
# WHY THIS IS A SCRIPT AND NOT A NOTE. The cross-night union was the project's
# actual deliverable and it was the ONE level nothing automated: the session
# chain looped its sets and stopped, so the union only ever existed because
# someone assembled it by hand. That is how it came to be built from a mix of
# optical eras nobody could tell apart afterwards, and how the star-pair
# registration that cost 0.458 roundness went unnoticed for as long as it did.
#
# IT COMPOSES MEMBERS, NEVER PER-SET OR PER-NIGHT FINALS. A final has already
# been cropped to its own coverage, so a combine of finals has holes exactly
# where only the discarded outer drift zones covered — a registered dead end
# (docs/dead-ends.md). Every level composes the same sub-stacks; only the SET of
# members differs.
#
# REGISTRATION is astrometric by construction: run_undistort_compose.sh derives
# it from each member's own plate solution and applies that member's own SIP
# undistortion, and compose_preflight.py REFUSES the build if any member cannot
# carry it. Members are solved at build time by run_undistort_groups.sh, so a
# corpus built by the chain is ready; one assembled from older members may not
# be, and will be told so rather than silently falling back.
set -euo pipefail
REPO=$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)
OUT= FRAMING=max WEIGHT=nbstack PLAN=; SESSIONS=()
for a in "$@"; do case "$a" in
  --out=*) OUT=${a#*=};;
  --framing=*) FRAMING=${a#*=};;
  --weight=*) WEIGHT=${a#*=};;
  --plan) PLAN=1;;
  --*) echo "unknown arg $a" >&2; exit 1;;
  *) SESSIONS+=("$a");;
esac; done
[ ${#SESSIONS[@]} -ge 1 ] || { echo "usage: run_corpus_combine.sh <session-dir>... [--out=]" >&2; exit 1; }

GROUPDIRS=(); NAMES=()
for S in "${SESSIONS[@]}"; do
  [ -d "$S" ] || { echo "no such session dir: $S" >&2; exit 1; }
  S=$(cd "$S" && pwd); ses=$(basename "$S")
  n=0
  for gd in "$S"/work/groups_set-*; do
    [ -d "$gd" ] || continue
    # arm variants are not the corpus; set-00 is the SPARE-FRAMES bucket, never
    # a light set (owner convention: real sets start at 01)
    case "$gd" in *_pinned|*_subsky1|*/groups_set-00) continue;; esac
    ls "$gd"/sub_*.fit >/dev/null 2>&1 || continue
    GROUPDIRS+=("$gd"); n=$((n + $(ls "$gd"/sub_*.fit | wc -l)))
  done
  [ "$n" -gt 0 ] && NAMES+=("$ses")
  echo "[corpus] $ses: $n member(s)"
done
[ ${#GROUPDIRS[@]} -ge 2 ] || { echo "[corpus] need members from at least 2 group dirs, have ${#GROUPDIRS[@]}" >&2; exit 1; }

NAME=$(IFS=+; echo "${NAMES[*]}")
OUT=${OUT:-$REPO/web/results/${NAMES[-1]}/stack_${NAME}_full.fit}
TOTAL=$(for g in "${GROUPDIRS[@]}"; do ls "$g"/sub_*.fit; done | wc -l)
echo "[corpus] $TOTAL members from ${#GROUPDIRS[@]} group dir(s) across ${#NAMES[@]} night(s) -> $(basename "$OUT")"
if [ -n "$PLAN" ]; then
  echo "[corpus] PLAN — compose (astrometric, preflight-guarded) then one full-canvas render; nothing executed"
  exit 0
fi

"$REPO/scripts/stack/run_undistort_compose.sh" --out="$OUT" --framing="$FRAMING" \
  --weight="$WEIGHT" "${GROUPDIRS[@]}"

# The render is part of the deliverable, not a follow-up: a combine nobody can
# look at is not finished. finish_render.sh solves -> SPCC -> linked stretch ->
# full-frame 16-bit PNG, which is the only surface a verdict may be taken on.
"$REPO/scripts/stack/finish_render.sh" "$OUT" "${NAME}_full" \
  --session="$(cd "${SESSIONS[-1]}" && pwd)" --set="$(basename "$(ls -d "$(cd "${SESSIONS[-1]}" && pwd)"/set-* | tail -1)")"
echo "[corpus] DONE -> $OUT"
echo "[corpus] render -> web/results/${NAMES[-1]}/judge/${NAME}_full_spcc-linked.png"
