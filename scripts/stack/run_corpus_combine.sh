#!/usr/bin/env bash
# THE FINAL COMBINE — every member from every night into one stack, then one
# render of the full wide canvas.
#
#   run_corpus_combine.sh <session-dir>... [--out=<stack.fit>] [--framing=min|max]
#                         [--weight=nbstack|noise] [--plan] [--portion-rule[=<bar px>]]
#
# --portion-rule runs THE PORTION-RULE STAGE first (run_member_crop.sh: profile every
# member, crop the measured-bad entry-side zone off a copy, curated dir + tracked
# record — the bar from datasets/corpus/recipe.json member_selection.portion_rule
# unless given explicitly, and echoed) and hands the compose THAT dir instead of the
# group dirs; the compose invocation itself is unchanged. Without the flag the chain
# is byte-for-byte the previous one. Owner-approved on the cropT arm
# (datasets/corpus/smear_attribution/cropT_arm.json; ledger 111-118).
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
OUT= FRAMING=max WEIGHT=nbstack PLAN= PORTION= PBAR=; SESSIONS=()
for a in "$@"; do case "$a" in
  --out=*) OUT=${a#*=};;
  --framing=*) FRAMING=${a#*=};;
  --weight=*) WEIGHT=${a#*=};;
  --plan) PLAN=1;;
  --portion-rule) PORTION=1;;
  --portion-rule=*) PORTION=1; PBAR=${a#*=};;
  --*) echo "unknown arg $a" >&2; exit 1;;
  *) SESSIONS+=("$a");;
esac; done
[ ${#SESSIONS[@]} -ge 1 ] || { echo "usage: run_corpus_combine.sh <session-dir>... [--out=]" >&2; exit 1; }

# The member-dir enumerator is SHARED with run_member_crop.sh (the portion-rule
# stage): scripts/lib/member_dirs.sh holds the allow-list — `groups_set-NN` and
# nothing else, spare buckets and arm variants never — and its history (the
# deny-list that let every later arm into the corpus silently). One function, so
# the stage and the compose can never disagree about what a member is.
. "$REPO/scripts/lib/member_dirs.sh"
GROUPDIRS=(); NAMES=()
for S in "${SESSIONS[@]}"; do
  [ -d "$S" ] || { echo "no such session dir: $S" >&2; exit 1; }
  S=$(cd "$S" && pwd); ses=$(basename "$S")
  n=0
  while IFS= read -r gd; do
    [ -n "$gd" ] || continue
    GROUPDIRS+=("$gd"); n=$((n + $(ls "$gd"/sub_*.fit | wc -l)))
  done < <(canonical_member_dirs "$S")
  [ "$n" -gt 0 ] && NAMES+=("$ses")
  echo "[corpus] $ses: $n member(s)"
done
[ ${#GROUPDIRS[@]} -ge 2 ] || { echo "[corpus] need members from at least 2 group dirs, have ${#GROUPDIRS[@]}" >&2; exit 1; }

NAME=$(IFS=+; echo "${NAMES[*]}")
OUT=${OUT:-$REPO/web/results/${NAMES[-1]}/stack_${NAME}_full.fit}
# THE PRODUCT TAG derives from the OUTPUT's basename (stack_<tag>.fit -> <tag>), and
# every name downstream — the finish's _wcs/_spcc/judge PNG, the curated dir, the
# stage record — is built from it, so a --out can never write its finish products
# onto ANOTHER product's names (the tag was "${NAME}_full" whatever --out said, so a
# candidate's finish would have overwritten the canonical's _wcs/_spcc/PNG). With no
# --out the default above is stack_${NAME}_full.fit, hence TAG == "${NAME}_full" and
# the default path is byte-for-byte the previous behaviour. An --out that is not of
# the form stack_<tag>.fit is refused: the finish could not name its products.
TAG=$(basename "$OUT"); TAG=${TAG#stack_}; TAG=${TAG%.fit}
[ -n "$TAG" ] && [ "$(basename "$OUT")" = "stack_${TAG}.fit" ] \
  || { echo "[corpus] --out must be named stack_<tag>.fit (got '$(basename "$OUT")'): the finish products derive their names from <tag>" >&2; exit 1; }
TOTAL=$(for g in "${GROUPDIRS[@]}"; do ls "$g"/sub_*.fit; done | wc -l)
echo "[corpus] $TOTAL members from ${#GROUPDIRS[@]} group dir(s) across ${#NAMES[@]} night(s) -> $(basename "$OUT")"
if [ -n "$PLAN" ]; then
  echo "[corpus] PLAN — compose (astrometric, preflight-guarded) then one full-canvas render; nothing executed"
  exit 0
fi

if [ -n "$PORTION" ]; then
  # THE PORTION-RULE STAGE — the curated dir replaces the group dirs as the compose's
  # input; the stage's record is the tracked account of what was cropped and why.
  # No --ref is pinned here (the compose derives its reference afterwards), so the
  # stage's reference refusal does not apply; the DERIVED reference is checked back
  # against the stage record after the compose below (reference_cropped) instead.
  # Named from TAG: the curated dir curated_<tag>; the stage record keeps the _portion
  # suffix (<tag>_portion.json) because it is the STAGE's record of what it cropped
  # for that product, and the bare <tag>.json name is left to the product's own
  # candidate/acceptance records in the same dir.
  PRECORD="$REPO/datasets/corpus/member_selection/${TAG}_portion.json"
  CURATED="${SESSIONS[-1]%/}/work/curated_${TAG}"
  "$REPO/scripts/stack/run_member_crop.sh" "${SESSIONS[@]}" --out="$CURATED" ${PBAR:+--bar="$PBAR"} \
    --recipe="$REPO/datasets/corpus/recipe.json" --record="$PRECORD" \
    --tag="${TAG}_portion" || { echo "[corpus] the portion-rule stage FAILED (exit $?) — nothing composed" >&2; exit 1; }
  GROUPDIRS=("$(cd "$CURATED" && pwd)")
  echo "[corpus] portion rule applied: composing from $CURATED"
fi
"$REPO/scripts/stack/run_undistort_compose.sh" --out="$OUT" --framing="$FRAMING" \
  --weight="$WEIGHT" "${GROUPDIRS[@]}"

# The render is part of the deliverable, not a follow-up: a combine nobody can
# look at is not finished. finish_render.sh solves -> SPCC -> linked stretch ->
# full-frame 16-bit PNG, which is the only surface a verdict may be taken on.
# --session/--set route the SPCC spec + record filing and derive from the
# product's OWN registration reference (REGREF, the stamped anchor) — a
# CONTRIBUTING set by construction. The retired `ls -d set-* | tail -1` was
# sort-position identity: ASCII orders digits before letters, so set-0a/0b's
# creation made the LAST name a spare bucket and two corpus records filed
# under a set with zero members in the product
# (BACKLOG:set-identity-by-sort-order).
if [ -n "$PORTION" ]; then
  # THE DERIVED-REFERENCE CHECK. The curated dir renames members and the compose
  # resolves symlinks, so REGREF carries a groups path for an UNCROPPED reference
  # but a curated path for a CROPPED copy — and the curated path overflows the
  # 68-char FITS string and truncates. The leading "<idx>:" survives either way
  # and the stage record maps index -> member, so the RECORD is the resolver for
  # both the finish routing and the check. A cropped derived reference is a
  # SURFACED FACT, never a refusal (the anchor's IKSS location/scale change with
  # its columns and that state is untested): say it loudly, mark the stage
  # record (reference_cropped=true), continue.
  read -r REFSES REFSET < <(python3 - "$OUT" "$PRECORD" <<'PY'
import json, re, sys
from astropy.io import fits          # HEADER only — no pixel access
h = fits.getheader(sys.argv[1])
r = str(h.get("REGREF", "")); rsrc = str(h.get("REGREFSR", "") or "auto")
rec = json.load(open(sys.argv[2]))
m = re.match(r"(\d+):", r)
row = next((v for v in rec["table"].values() if m and v.get("index") == int(m.group(1))), None)
if row is None:
    sys.exit(f"cannot resolve REGREF {r!r} against the stage record {sys.argv[2]} — cannot route the finish")
mm = re.search(r"/([^/]+)/work/groups_(set-[0-9a-z]+)/", row["member"])
if not mm:
    sys.exit(f"stage record row {row['name']}: no parseable member path {row['member']!r}")
if row.get("cropped"):
    print(f"WARNING: the compose derived its reference as {row['name']} (REGREF {r!r}, source {rsrc}) — a member the portion rule CROPPED (x_c {row['x_c']}). A cropped anchor is UNTESTED (its IKSS location/scale change with its columns); recording reference_cropped=true in the stage record", file=sys.stderr)
    rec["reference_cropped"] = True; rec["reference_regref"] = r
    json.dump(rec, open(sys.argv[2], "w"), indent=1)
else:
    print(f"[corpus] derived reference {row['name']}: uncropped in the stage record", file=sys.stderr)
print(mm.group(1), mm.group(2))
PY
) || exit 1
else
  read -r REFSES REFSET < <(python3 - "$OUT" <<'PY'
import re, sys
from astropy.io import fits          # HEADER only — no pixel access
r = str(fits.getheader(sys.argv[1]).get("REGREF", ""))
m = re.match(r"\d+:([^/]+)/groups_(set-[0-9a-z]+)/", r)
if not m:
    sys.exit(f"no parseable REGREF on {sys.argv[1]} (got {r!r}) — cannot route the finish")
print(m.group(1), m.group(2))
PY
) || exit 1
fi
REFDIR=
for s in "${SESSIONS[@]}"; do
  [ "$(basename "$(cd "$s" && pwd)")" = "$REFSES" ] && REFDIR=$(cd "$s" && pwd)
done
[ -n "$REFDIR" ] || { echo "[corpus] REGREF names session '$REFSES', which is not among the staged sessions" >&2; exit 1; }
"$REPO/scripts/stack/finish_render.sh" "$OUT" "$TAG" \
  --session="$REFDIR" --set="$REFSET"
echo "[corpus] DONE -> $OUT"
echo "[corpus] render -> web/results/${REFSES}/judge/${TAG}_spcc-linked.png"
