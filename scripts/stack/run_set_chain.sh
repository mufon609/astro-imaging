#!/usr/bin/env bash
# ONE-CLICK durable-core chain for a light set (user-ratified amendment,
# web/README.md): preflight -> frame QA -> route-by-fingerprint stack ->
# solve -> SPCC -> diagnostic judge surface. Every pixel op stays an official
# tool inside the existing pinned scripts; this only sequences them with hard
# gates between, and it STOPS the moment a decision belongs to the user:
#
#   exit 2  mount declared-vs-measured CONTRADICT (fingerprint) — reconcile
#   exit 3  frame QA raised defect-side flags and no ratified cull policy
#           exists (recipe.json "stack" block) — the cull decision is the
#           user's (BACKLOG item 3); ratify, then re-click
#   exit 4  mount undeclared — declare it on the set page first
#   exit 5  unroutable fingerprint (neither tracked nor fixed+wide) — the
#           two-window drift solve / the user decides the route
#   exit 6  real flats staged but no master-flat wiring for the undistort
#           route — resolve the flat manually (documented gap)
#
#   run_set_chain.sh <session-dir> <set> [--plan]
#
# --plan prints the derived plan (route + reason, gates, disk math, the exact
# commands, what will be skipped as already-built) and executes NOTHING; the
# same plan is printed first on every real run, so the click's authorization
# is always fully disclosed. Steps skip work whose product already exists
# (stack, judge surface), so a chain interrupted by a gate resumes with a
# re-click after the user's decision.
#
# The chain ends at the DIAGNOSTIC judge surface (linked autostretch PNG16 —
# finish_render.sh): everything aesthetic beyond it (the render-tier ladder)
# stays per-rung and user-judged. Route choice comes from the DERIVED
# fingerprint (tracked -> standard; fixed+wide -> undistort, single-pass vs
# groups by measured disk headroom vs the ~231 MB/frame single-pass peak);
# the printed reason makes the click a ratification of that recommendation,
# never a silent auto-route.
set -euo pipefail
REPO=$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)
SESSION=${1:?usage: run_set_chain.sh <session-dir> <set> [--plan]}
SET=${2:?missing <set>}
PLAN=0
for a in "${@:3}"; do case "$a" in
  --plan) PLAN=1;;
  *) echo "unknown arg $a" >&2; exit 1;;
esac; done
SESSION=$(cd "$SESSION" && pwd)
SNAME=$(basename "$SESSION")
DSET=$REPO/datasets/$SNAME/$SET
RESULTS=$REPO/web/results/$SNAME
say(){ echo "[chain $SET] $*"; }

# ---- gather the facts the plan states (reads only) ----------------------
NFRAMES=$(find "$SESSION/$SET" -maxdepth 1 -type f \
  \( -iname '*.nef' -o -iname '*.dng' -o -iname '*.cr2' -o -iname '*.cr3' \
     -o -iname '*.arw' -o -iname '*.raf' -o -iname '*.fit' -o -iname '*.fits' \) \
  2>/dev/null | wc -l)
[ "$NFRAMES" -ge 8 ] || { say "only $NFRAMES frames staged under $SESSION/$SET"; exit 1; }

FACTS=$(python3 - "$DSET" <<'PY'
import json, os, sys
d = sys.argv[1]
def rd(p):
    try: return json.load(open(os.path.join(d, p)))
    except (OSError, ValueError): return None
acq = rd("acquisition.json") or {}
fp = rd("fingerprint.json") or {}
qa = rd("qa_work/frame_metrics.json")
recipe = rd("recipe.json") or {}
mc = fp.get("mount_check") or {}
exif = acq.get("exif") or {}
print(acq.get("mount") or "")
print(mc.get("verdict") or "")
print(mc.get("measured") or "")
print(exif.get("fov_deg") if exif.get("fov_deg") is not None else "")
print("" if qa is None else len(qa.get("flagged_defect_side_z") or []))
print("yes" if isinstance(recipe.get("stack"), dict) else "")
print(fp.get("label") or "not yet derived")   # last line stays non-empty:
PY
)                                             # $() strips trailing newlines
{ read -r MOUNT; read -r VERDICT; read -r MEASURED; read -r FOV; read -r NFLAGS; \
  read -r RATIFIED; read -r FPLABEL; } <<< "$FACTS" || true

MOUNT_EFF=${MEASURED:-$MOUNT}
FREE_KB=$(df -k --output=avail "$SESSION" | tail -1 | tr -d ' ')
SINGLEPASS_KB=$((NFRAMES * 231 * 1024))
ROUTE= REASON=
if [ "$MOUNT_EFF" = "tracked" ]; then
  ROUTE=standard
  REASON="tracked mount: no inter-frame drift to fight -> calibrate/register/stack (run_pipeline)"
elif [ "$MOUNT_EFF" = "fixed" ] && [ -n "$FOV" ] && \
     python3 -c "import sys; sys.exit(0 if float('$FOV') >= 10 else 1)"; then
  if [ "$FREE_KB" -gt "$SINGLEPASS_KB" ]; then
    ROUTE=undistort
    REASON="fixed mount + ${FOV} deg field -> undistort class; disk $(($FREE_KB/1024/1024))G covers the single-pass peak $(($SINGLEPASS_KB/1024/1024))G"
  else
    ROUTE=undistort-groups
    REASON="fixed mount + ${FOV} deg field -> undistort class; disk $(($FREE_KB/1024/1024))G < single-pass peak $(($SINGLEPASS_KB/1024/1024))G (~231 MB/frame x $NFRAMES) -> balanced groups"
  fi
elif [ -z "$MOUNT" ]; then
  ROUTE=stop-undeclared
else
  ROUTE=stop-unroutable
  REASON="fingerprint is neither tracked nor fixed+wide (mount '$MOUNT_EFF', fov '${FOV:-?}') — the drift-solve instrument or the user picks the route"
fi

# products that already exist decide the skips
STACK=
case "$ROUTE" in
  standard)          STACK=$RESULTS/stack_$SET.fit;;
  undistort)         STACK=$RESULTS/stack_$SET.fit;;
  undistort-groups)  STACK=$RESULTS/stack_${SET}_full.fit;;
esac
DARK=$SESSION/work/masters/dark_master.fit
SKYFLAT=$SESSION/work/masters/skyflat_$SET.fit
HAVE_REAL_FLATS=0
if compgen -G "$SESSION/flats*" >/dev/null; then HAVE_REAL_FLATS=1; fi
if [ -d "$SESSION/calib" ]; then HAVE_REAL_FLATS=1; fi
NAME=
if [ -n "$STACK" ]; then NAME=$(basename "$STACK" .fit); NAME=${NAME#stack_}; fi
JUDGE_GLOB=$RESULTS/judge/${NAME}_*.png

# ---- the PLAN (printed on every run; --plan stops here) -----------------
say "PLAN — $NFRAMES frames | mount declared '${MOUNT:-UNDECLARED}' | fingerprint: $FPLABEL${VERDICT:+ ($VERDICT)}"
say "PLAN — frame QA: $([ -n "$NFLAGS" ] && echo "done, $NFLAGS defect-side flag(s)" || echo "not yet run — will run") | cull policy ratified: ${RATIFIED:-no}"
say "PLAN — route: $ROUTE${REASON:+ — $REASON}"
case "$ROUTE" in
  stop-undeclared) say "PLAN — WILL STOP: mount undeclared (declare on the set page)";;
  stop-unroutable) say "PLAN — WILL STOP: $REASON";;
  *)
    if [ -n "$NFLAGS" ] && [ "$NFLAGS" != 0 ] && [ -z "$RATIFIED" ]; then
      say "PLAN — WILL STOP after QA gate: $NFLAGS flag(s) await your cull ratification"
    fi
    say "PLAN — steps (existing products skip):"
    if [ -z "$NFLAGS" ]; then say "  1. scripts/qa/run_frame_qa.sh $SESSION $SET"; fi
    if [ "$ROUTE" != standard ]; then
      if [ ! -f "$DARK" ]; then say "  2. scripts/stack/build_master_dark.sh $SESSION"; fi
      if [ "$HAVE_REAL_FLATS" = 1 ]; then
        say "  3. WILL STOP: real flats staged — master-flat wiring for the undistort route is manual (gap)"
      elif [ ! -f "$SKYFLAT" ]; then
        say "  3. scripts/stack/build_sky_flat.sh $SESSION $SET --dark=$DARK --out=$SKYFLAT"
      fi
    fi
    if [ -f "$STACK" ]; then
      say "  4. stack exists -> skip build ($STACK)"
    else case "$ROUTE" in
      standard)         say "  4. scripts/stack/run_pipeline.sh $SESSION $SET";;
      undistort)        say "  4. scripts/stack/run_undistort_pipeline.sh $SESSION $SET --dark=$DARK --flat=$SKYFLAT";;
      undistort-groups) say "  4. scripts/stack/run_undistort_groups.sh $SESSION $SET --dark=$DARK --flat=$SKYFLAT";;
    esac; fi
    if compgen -G "$JUDGE_GLOB" >/dev/null; then
      say "  5. judge surface exists -> skip finish ($(basename $(compgen -G "$JUDGE_GLOB" | head -1)))"
    else
      say "  5. scripts/stack/finish_render.sh $STACK $NAME --session=$SESSION --set=$SET"
    fi;;
esac
say "PLAN — disk free now: $(df -h "$SESSION" | tail -1 | awk '{print $4}')"
if [ "$PLAN" = 1 ]; then say "plan only — nothing executed"; exit 0; fi

# ---- gates fire in order ------------------------------------------------
if [ "$ROUTE" = stop-undeclared ]; then say "STOP: mount undeclared — declare it on the set page, then re-click"; exit 4; fi

# preflight: seed/refresh acquisition (raises on undeclared mount AND on a
# CONTRADICT fingerprint), then re-derive the fingerprint record
say "preflight: acquisition + fingerprint"
mapfile -t FRAMES < <(find "$SESSION/$SET" -maxdepth 1 -type f \
  \( -iname '*.nef' -o -iname '*.dng' -o -iname '*.cr2' -o -iname '*.cr3' \
     -o -iname '*.arw' -o -iname '*.raf' -o -iname '*.fit' -o -iname '*.fits' \) | sort)
PYRC=0
python3 - "$REPO" "$SESSION" "$SET" "${FRAMES[@]}" <<'PY' || PYRC=$?
import os, sys
sys.path.insert(0, os.path.join(sys.argv[1], "scripts", "lib"))
import acquisition
try:
    acquisition.resolve(sys.argv[2], sys.argv[3], sys.argv[4:])
except acquisition.MountContradicted as e:
    print(e); sys.exit(2)
except acquisition.AcquisitionUndeclared as e:
    print(e); sys.exit(4)
PY
[ "$PYRC" = 0 ] || exit "$PYRC"
python3 "$REPO/scripts/lib/fingerprint.py" "$SESSION" "$SET" >/dev/null || {
  rc=$?; if [ "$rc" = 2 ]; then say "STOP: mount CONTRADICT — see $DSET/fingerprint.json"; fi; exit "$rc"; }

# frame QA (writes frame_metrics.json + refreshes the fingerprint itself)
if [ -z "$NFLAGS" ]; then
  say "frame QA"
  "$REPO/scripts/qa/run_frame_qa.sh" "$SESSION" "$SET"
  NFLAGS=$(python3 -c "import json;print(len(json.load(open('$DSET/qa_work/frame_metrics.json')).get('flagged_defect_side_z') or []))")
fi
if [ "$NFLAGS" != 0 ] && [ -z "$RATIFIED" ]; then
  say "STOP: frame QA flagged $NFLAGS frame(s) and no ratified cull policy exists —"
  say "      the cull decision is yours: review the Frames view, record recipe.json"
  say "      {\"stack\": {\"exclude\": [...], ...}} (or an explicit keep-all block), re-click"
  exit 3
fi

# route may have been stop-unroutable only when a fingerprint existed; a
# fresh derivation above may have settled it — re-read once
if [ "$ROUTE" = stop-unroutable ]; then
  NEWROUTE=$(python3 - "$DSET" <<'PY'
import json, os, sys
fp = json.load(open(os.path.join(sys.argv[1], "fingerprint.json")))
acq = json.load(open(os.path.join(sys.argv[1], "acquisition.json")))
mc = fp.get("mount_check") or {}
m = mc.get("measured") or acq.get("mount")
fov = (acq.get("exif") or {}).get("fov_deg") or 0
print("tracked" if m == "tracked" else "fixed-wide" if (m == "fixed" and fov >= 10) else "no")
PY
)
  case "$NEWROUTE" in
    tracked)    ROUTE=standard; STACK=$RESULTS/stack_$SET.fit;;
    fixed-wide) ROUTE=undistort-groups; STACK=$RESULTS/stack_${SET}_full.fit;;
    *) say "STOP: $REASON"; exit 5;;
  esac
  NAME=$(basename "$STACK" .fit); NAME=${NAME#stack_}
fi

# masters (undistort routes bring their own; the standard route's builder
# resolves masters internally and hard-stops flatless itself)
if [ "$ROUTE" != standard ]; then
  if [ ! -f "$DARK" ]; then
    say "master dark"
    "$REPO/scripts/stack/build_master_dark.sh" "$SESSION"
  fi
  if [ "$HAVE_REAL_FLATS" = 1 ]; then
    say "STOP: real flats staged — build/point the master flat manually (undistort-route wiring gap)"
    exit 6
  fi
  if [ ! -f "$SKYFLAT" ]; then
    say "per-set sky flat (the ratified per-set-flat rule)"
    "$REPO/scripts/stack/build_sky_flat.sh" "$SESSION" "$SET" --dark="$DARK" --out="$SKYFLAT"
  fi
fi

# stack via the routed builder
if [ -f "$STACK" ]; then
  say "stack exists — skipping build ($STACK)"
else
  say "stack ($ROUTE)"
  case "$ROUTE" in
    standard)         "$REPO/scripts/stack/run_pipeline.sh" "$SESSION" "$SET";;
    undistort)        "$REPO/scripts/stack/run_undistort_pipeline.sh" "$SESSION" "$SET" --dark="$DARK" --flat="$SKYFLAT";;
    undistort-groups) "$REPO/scripts/stack/run_undistort_groups.sh" "$SESSION" "$SET" --dark="$DARK" --flat="$SKYFLAT";;
  esac
  [ -f "$STACK" ] || { say "builder finished but $STACK is missing"; exit 1; }
fi

# finish: solve -> cone -> SPCC -> linked autostretch judge PNG16
if compgen -G "$JUDGE_GLOB" >/dev/null; then
  say "judge surface exists — skipping finish"
else
  say "finish (solve -> SPCC -> judge surface)"
  "$REPO/scripts/stack/finish_render.sh" "$STACK" "$NAME" --session="$SESSION" --set="$SET"
fi

say "DONE — stack: $STACK | judge: $(compgen -G "$JUDGE_GLOB" | head -1 || echo '?') | free: $(df -h "$SESSION" | tail -1 | awk '{print $4}')"
