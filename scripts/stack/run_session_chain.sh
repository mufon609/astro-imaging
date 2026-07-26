#!/usr/bin/env bash
# ONE-CLICK durable-core chain for EVERY light set in a session — the session
# button of the user-ratified chain amendment (web/README.md). Enumerates the
# staged light sets (any set dir that is not calibration/staging plumbing),
# then runs scripts/stack/run_set_chain.sh on each in name order, STOPPING at
# the first set that exits nonzero — a gate firing for one set (mount
# CONTRADICT, flags awaiting cull ratification, unroutable fingerprint) halts
# the chain there with that set's exit code, so nothing downstream builds past
# an unresolved decision. Sets whose products already exist skip work inside
# the per-set chain, so a re-click after resolving a gate resumes where it
# stopped.
#
#   run_session_chain.sh <session-dir> [--plan]
#
# --plan prints every set's derived plan (route + reason + exact commands)
# and executes nothing — the same full-disclosure contract as the per-set
# chain, session-wide.
set -euo pipefail
REPO=$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)
SESSION=${1:?usage: run_session_chain.sh <session-dir> [--plan]}
PLAN=
for a in "${@:2}"; do case "$a" in
  --plan) PLAN=--plan;;
  *) echo "unknown arg $a" >&2; exit 1;;
esac; done
SESSION=$(cd "$SESSION" && pwd)

# light sets = staged dirs that are not calibration groups or plumbing and
# actually hold frames (mirrors the web session model's set-kind rule)
SETS=()
for d in "$SESSION"/*/; do
  name=$(basename "$d")
  case "$name" in
    darks|biases|flats|flats_*|darkflats|calib|work|reference|.*) continue;;
  esac
  n=$(find "$d" -maxdepth 1 -type f \
    \( -iname '*.nef' -o -iname '*.dng' -o -iname '*.cr2' -o -iname '*.cr3' \
       -o -iname '*.arw' -o -iname '*.raf' -o -iname '*.fit' -o -iname '*.fits' \) \
    2>/dev/null | wc -l)
  [ "$n" -ge 8 ] && SETS+=("$name")
done
[ ${#SETS[@]} -gt 0 ] || { echo "no light sets with >=8 frames under $SESSION" >&2; exit 1; }

echo "[session chain] $(basename "$SESSION"): ${#SETS[@]} light set(s): ${SETS[*]}"
for s in "${SETS[@]}"; do
  echo "[session chain] ===== $s ====="
  "$REPO/scripts/stack/run_set_chain.sh" "$SESSION" "$s" $PLAN || {
    rc=$?
    echo "[session chain] STOPPED at $s (exit $rc) — resolve the gate above, then re-click to resume from here" >&2
    exit "$rc"
  }
done
# the decisions the run made, in one place (standing auto-cull policy:
# flagged frames excluded; a hand-ratified recipe block always won)
echo "[session chain] ===== decisions ====="
for s in "${SETS[@]}"; do
  python3 - "$REPO/datasets/$(basename "$SESSION")/$s/recipe.json" "$s" <<'PY'
import json, sys
try:
    st = (json.load(open(sys.argv[1])) or {}).get("stack") or {}
except (OSError, ValueError):
    st = {}
e = st.get("exclude") or []
why = (st.get("why") or "")[:140]
print(f"[session chain] {sys.argv[2]}: culled {len(e)} frame(s)"
      + (f" n={e} — {why}" if e else ""))
PY
done
echo "[session chain] DONE — all ${#SETS[@]} set(s) carried to their judge surfaces (or already there)"
