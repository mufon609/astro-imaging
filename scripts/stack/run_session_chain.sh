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
#   run_session_chain.sh <session-dir> [--plan] [--route=…] [--group=N]
#
# --plan prints every set's derived plan (route + reason + exact commands)
# and executes nothing — the same full-disclosure contract as the per-set
# chain, session-wide.
set -euo pipefail
REPO=$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)
SESSION=${1:?usage: run_session_chain.sh <session-dir> [--plan]}
PLAN=
EXTRA=()
for a in "${@:2}"; do case "$a" in
  --plan) PLAN=--plan;;
  # Route and group size are per-RUN operator decisions (see run_set_chain.sh
  # force_route() and run_undistort_groups.sh's derived group size). They pass
  # straight through so a session-wide choice is made once, and every set's
  # printed plan still states it as OPERATOR-FORCED rather than derived.
  # --yes is the chain amendment's ONE approval, session-wide: each set still
  # prints its readiness report, and the build proceeds unattended past
  # YELLOWs (RED still stops with exit 7).
  --route=*|--group=*|--desky|--no-desky|--yes) EXTRA+=("$a");;
  *) echo "unknown arg $a" >&2; exit 1;;
esac; done
SESSION=$(cd "$SESSION" && pwd)

# light sets = staged dirs that are not calibration groups or plumbing and
# actually hold frames (mirrors the web session model's set-kind rule)
SETS=()
for d in "$SESSION"/*/; do
  name=$(basename "$d")
  # The SINGULAR forms are calibration too. The pipeline's own convention is
  # Siril's — plural (its bundled scripts use `cd darks`/`flats`/`biases`/
  # `lights` and never a singular) — but a singular staged dir must not fall
  # through to the LIGHT branch: it holds >=8 raws, so it would be enumerated
  # as a light set and carried to frame QA, mount derivation and a full stack.
  # build_master_dark.sh still requires the plural (it stops loudly on the
  # singular); this list only refuses to mistake one for lights.
  case "$name" in
    darks|dark|biases|bias|flats|flat|flats_*|darkflats|darkflat|calib|work|reference|.*) continue;;
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
  "$REPO/scripts/stack/run_set_chain.sh" "$SESSION" "$s" $PLAN ${EXTRA[@]+"${EXTRA[@]}"} || {
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
