#!/usr/bin/env bash
# ONE-CLICK durable-core chain for a light set (user-ratified amendment,
# web/README.md): preflight -> frame QA -> route-by-fingerprint stack ->
# solve -> SPCC -> diagnostic judge surface. Every pixel op stays an official
# tool inside the existing pinned scripts; this only sequences them with hard
# gates between, and it STOPS the moment a decision belongs to the user:
#
#   exit 2  mount declared-vs-measured CONTRADICT (fingerprint) — reconcile
#   exit 3  RETIRED — frame-QA flags no longer stop: the STANDING USER
#           POLICY auto-culls flagged defect-side frames (they exclude like
#           any obstruction), writes the recipe stack block with the flags
#           as the why, and reports the decision inline + in the session
#           summary; a hand-ratified stack block is never overwritten
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
PLAN=0 DESKYOPT=--desky
for a in "${@:3}"; do case "$a" in
  --plan) PLAN=1;;
  --no-desky) DESKYOPT=;;
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
elif [ -z "$FOV" ]; then
  # a mount-only pre-declaration (the web declare click on a fresh set):
  # preflight seeds the header facts, then the route re-derives mid-run
  ROUTE=derive-after-preflight
  REASON="mount declared '$MOUNT' but header facts not yet seeded — preflight fills them and the route re-derives (frame QA runs first either way)"
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
# The flat's NAME must record whether it was de-skied, for the same reason a stack
# carries a recipe-tag: it is a different chain shape, and the two are not
# interchangeable. Without it one path held two different products — and because
# the build is skipped when the file exists, a session that already had a
# CONTAMINATED skyflat_<set>.fit on disk would silently reuse it and the --desky
# default would never take effect at all. The de-skied flat also has to pair with
# the per-frame background step (see the --desky note below), and the light
# builders derive that pairing from this name.
SKYFLAT=$SESSION/work/masters/skyflat_$SET${DESKYOPT:+_desky}.fit
HAVE_REAL_FLATS=0
if compgen -G "$SESSION/flats*" >/dev/null; then HAVE_REAL_FLATS=1; fi
if [ -d "$SESSION/calib" ]; then HAVE_REAL_FLATS=1; fi
NAME=
if [ -n "$STACK" ]; then NAME=$(basename "$STACK" .fit); NAME=${NAME#stack_}; fi
# The judge-surface existence test must match the EXACT names finish_render.sh
# writes (<name>_spcc-linked.png, or <name>_lum-autostretch.png on a mono
# stack) — never ${NAME}_*.png. That looser glob ALSO matches a preserved
# RECIPE-TAG VARIANT of the same set (e.g. set-01_263all_spcc-linked.png),
# which is exactly what the naming convention prescribes when bracketing an
# A/B. The chain then reports the OLD variant's surface as already-done and
# silently skips finishing the REBUILT stack, leaving it with no WCS and no
# SPCC — a rebuilt product that looks complete and is not.
judge_surface() {   # echoes the existing surface for $1, or returns nonzero
  local n=$1 p
  for p in "$RESULTS/judge/${n}_spcc-linked.png" \
           "$RESULTS/judge/${n}_lum-autostretch.png"; do
    [ -f "$p" ] && { echo "$p"; return 0; }
  done
  return 1
}

# ---- the PLAN (printed on every run; --plan stops here) -----------------
say "PLAN — $NFRAMES frames | mount declared '${MOUNT:-UNDECLARED}' | fingerprint: $FPLABEL${VERDICT:+ ($VERDICT)}"
say "PLAN — frame QA: $([ -n "$NFLAGS" ] && echo "done, $NFLAGS defect-side flag(s)" || echo "not yet run — will run") | cull: $([ -n "$RATIFIED" ] && echo "ratified recipe block" || echo "standing auto-cull (flagged frames exclude; reported at the end)")"
say "PLAN — route: $ROUTE${REASON:+ — $REASON}"
if [ -z "$MOUNT" ] && [ "$ROUTE" != stop-undeclared ]; then
  # measured but not yet declared: the route above came from the MEASURED
  # signature — state it, and state that the declaration gate still stops
  say "PLAN — WILL STOP before building: mount measured '$MEASURED' but NOT DECLARED — accept the pre-filled verdict on the set page, then re-click"
fi
case "$ROUTE" in
  stop-undeclared) say "PLAN — WILL MEASURE then STOP: mount undeclared — the fingerprint measures it first (roundness if QA exists, else the two-window drift probe: scripts/qa/mount_probe.sh), the verdict pre-fills the set page's mount control, your accept-click writes the declaration, a re-click resumes";;
  stop-unroutable) say "PLAN — WILL STOP: $REASON";;
  derive-after-preflight)
    if [ -z "$NFLAGS" ]; then say "PLAN — steps: 1. scripts/qa/run_frame_qa.sh $SESSION $SET"; fi
    say "PLAN — then: route + remaining steps derive after preflight seeds the header facts (masters -> stack -> finish, skipping what exists)";;
  *)
    if [ -n "$NFLAGS" ] && [ "$NFLAGS" != 0 ] && [ -z "$RATIFIED" ]; then
      say "PLAN — auto-cull will exclude the $NFLAGS flagged frame(s) and report (standing policy; a hand-ratified recipe block overrides)"
    fi
    say "PLAN — steps (existing products skip):"
    if [ -z "$NFLAGS" ]; then say "  1. scripts/qa/run_frame_qa.sh $SESSION $SET"; fi
    if [ "$ROUTE" != standard ]; then
      if [ ! -f "$DARK" ]; then say "  2. scripts/stack/build_master_dark.sh $SESSION"; fi
      if [ "$HAVE_REAL_FLATS" = 1 ]; then
        say "  3. WILL STOP: real flats staged — master-flat wiring for the undistort route is manual (gap)"
      elif [ ! -f "$SKYFLAT" ]; then
        say "  3. scripts/stack/build_sky_flat.sh $SESSION $SET --dark=$DARK --out=$SKYFLAT $DESKYOPT"
      fi
    fi
    if [ -f "$STACK" ]; then
      say "  4. stack exists -> skip build ($STACK)"
    else case "$ROUTE" in
      standard)         say "  4. scripts/stack/run_pipeline.sh $SESSION $SET";;
      undistort)        say "  4. scripts/stack/run_undistort_pipeline.sh $SESSION $SET --dark=$DARK --flat=$SKYFLAT $DESKYOPT";;
      undistort-groups) say "  4. scripts/stack/run_undistort_groups.sh $SESSION $SET --dark=$DARK --flat=$SKYFLAT $DESKYOPT";;
    esac; fi
    if JS=$(judge_surface "$NAME"); then
      say "  5. judge surface exists -> skip finish ($(basename "$JS"))"
    elif compgen -G "$RESULTS/judge/${NAME}_*.png" >/dev/null; then
      # A RECIPE-TAGGED variant exists but not the canonical name. Say so, and
      # do NOT treat it as done: a tagged surface may have been produced from a
      # different stack (an A/B arm, or a hand-named finish), so silently
      # skipping here is what once left a rebuilt stack with no WCS and no SPCC
      # while reporting success. The finish re-runs and writes the canonical name.
      say "  5. scripts/stack/finish_render.sh $STACK $NAME --session=$SESSION --set=$SET"
      say "     (note: no canonical ${NAME}_spcc-linked.png, but recipe-tagged surface(s) exist:"
      say "      $(cd "$RESULTS/judge" && echo ${NAME}_*.png) — those are not assumed to come from this stack)"
    else
      say "  5. scripts/stack/finish_render.sh $STACK $NAME --session=$SESSION --set=$SET"
    fi;;
esac
say "PLAN — disk free now: $(df -h "$SESSION" | tail -1 | awk '{print $4}')"
if [ "$PLAN" = 1 ]; then say "plan only — nothing executed"; exit 0; fi

# ---- gates fire in order ------------------------------------------------
# the declaration gate is independent of routability: a MEASURED mount can
# derive the route for the plan, but nothing builds on an undeclared one —
# the measure branch below stops with the accept-the-verdict message
# (immediately when a measurement already exists)
if [ -z "$MOUNT" ]; then ROUTE=stop-undeclared; fi
if [ "$ROUTE" = stop-undeclared ]; then
  # measure-then-stop (user-ratified: measure + confirm click). The mount
  # stays a DECLARED fact — the chain measures the signature, records it,
  # and stops; the set page pre-fills the verdict and the user's accept
  # click writes the declaration. Nothing routes until then.
  say "mount undeclared — measuring the signature before stopping"
  python3 - "$REPO" "$SESSION" "$SET" <<'PY' || true
import glob, os, sys
sys.path.insert(0, os.path.join(sys.argv[1], "scripts", "lib"))
import acquisition
frames = sorted(f for pat in ("*.nef", "*.NEF", "*.dng", "*.DNG", "*.cr2",
                              "*.CR2", "*.arw", "*.ARW", "*.fit", "*.fits")
                for f in glob.glob(os.path.join(sys.argv[2], sys.argv[3], pat)))
try:
    acquisition.resolve(sys.argv[2], sys.argv[3], frames)
except acquisition.AcquisitionUndeclared:
    pass          # expected: the record is seeded with the derived facts
PY
  python3 "$REPO/scripts/lib/fingerprint.py" "$SESSION" "$SET" >/dev/null || true
  MEASURED=$(python3 -c "import json;print((json.load(open('$DSET/fingerprint.json')).get('mount_check') or {}).get('measured') or '')" 2>/dev/null || true)
  if [ -z "$MEASURED" ]; then
    say "roundness not decisive (or no QA yet) — running the two-window drift probe"
    "$REPO/scripts/qa/mount_probe.sh" "$SESSION" "$SET" >/dev/null || true
    MEASURED=$(python3 -c "import json;print((json.load(open('$DSET/fingerprint.json')).get('mount_check') or {}).get('measured') or '')" 2>/dev/null || true)
  fi
  if [ -n "$MEASURED" ]; then
    say "STOP: the data reads as '$MEASURED' — accept it on the set page (pre-filled), then re-click"
  else
    say "STOP: mount undeclared and the instruments could not decide — declare it on the set page, then re-click"
  fi
  exit 4
fi

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
  # STANDING USER POLICY: flagged defect-side frames exclude like any
  # obstruction — the chain writes the cull, states it, and proceeds; the
  # decisions are reported again in the end summary. A hand-ratified
  # recipe stack block is never overwritten and always wins.
  say "auto-cull (standing policy): $NFLAGS flagged frame(s) exclude; a hand-ratified recipe block overrides"
  python3 - "$DSET" "$REPO" <<'PY'
import json, os, sys
d, repo = sys.argv[1], sys.argv[2]
sys.path.insert(0, os.path.join(repo, "scripts", "lib"))
from cullspec import frame_number   # THE exclude convention: filename digits
qa = json.load(open(os.path.join(d, "qa_work", "frame_metrics.json")))
flagged = qa.get("flagged_defect_side_z") or []
nums, nameless = set(), []
for f in flagged:
    n = frame_number(f["file"])
    (nums.add(n) if n is not None else nameless.append(f["file"]))
if nameless:
    sys.exit("auto-cull ABORT: flagged frame(s) without a filename number "
             "cannot be addressed by stack.exclude: " + ", ".join(nameless))
nums = sorted(nums)
rp = os.path.join(d, "recipe.json")
rec = {}
if os.path.exists(rp):
    try:
        rec = json.load(open(rp))
    except ValueError:
        rec = {}
if isinstance(rec.get("stack"), dict):
    print("recipe stack block already present — leaving it untouched")
    sys.exit(0)
why = ("auto-cull, standing policy: defect-side robust z >= 3.5 flags "
       "exclude (" + "; ".join(f"{f['file']}: {','.join(f['flags'])}"
                               for f in flagged)
       + "). Exclude numbers are trailing filename digits (cullspec). "
       "A hand-ratified stack block overrides this write.")
rec["stack"] = {"weight": None, "exclude": nums, "why": why}
json.dump(rec, open(rp, "w"), indent=1)
print(f"culled frames {nums}: " + ", ".join(sorted(f['file'] for f in flagged)))
PY
  RATIFIED=yes
fi

# the route re-derives once the preflight/QA above have seeded the facts —
# the mount-only pre-declaration case, and a stop-unroutable that a fresh
# derivation may have settled
if [ "$ROUTE" = stop-unroutable ] || [ "$ROUTE" = derive-after-preflight ]; then
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
    fixed-wide)
      FREE_KB=$(df -k --output=avail "$SESSION" | tail -1 | tr -d ' ')
      if [ "$FREE_KB" -gt "$SINGLEPASS_KB" ]; then
        ROUTE=undistort; STACK=$RESULTS/stack_$SET.fit
      else
        ROUTE=undistort-groups; STACK=$RESULTS/stack_${SET}_full.fit
      fi;;
    *) say "STOP: route still underivable after preflight (mount/fov missing from the seeded facts) — the user picks the route"; exit 5;;
  esac
  NAME=$(basename "$STACK" .fit); NAME=${NAME#stack_}
  say "route (re-derived): $ROUTE"
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
# DESKY is ON by default, and it is passed to BOTH halves of the correction —
# the flat builder here and the light builder below. They are not independent
# options: a de-skied flat stops calibration dividing the object by the sky's own
# profile and leaves the gradient in ADDITIVELY, which is the domain the
# per-frame background step removes it in. Half-applying it is worse than either
# consistent choice (the judge stretch amplifies a background gradient 9-17x).
# WHY IT IS ON HERE: reaching this code means the set is FLATLESS (real flats
# stop above and retire the builder) on the undistort route, and both measured
# sets are that class. Measured contamination it removes: flat odd-plane
# 4.84%%->1.98%% (set-01) and 7.82%%->2.42%% (set-02), while radial vignetting
# holds to <=0.12%%, PRNU correlation >0.9995 and dust-mote depth changes -2 to
# -3%%. Proven on the object by differential star photometry: a 3.11%%
# position-dependent flux plane at 241 sigma. Pass --no-desky to opt out.
# NOT scoped by mount, and the earlier claim that it was is WRONG: a tracked
# mount is not immune. The driver is whether the SENSOR is fixed relative to the
# HORIZON. An untracked tripod and an alt-az mount without a derotator both hold
# an alt-az-fixed gradient still on the sensor (zero rejection). An equatorial
# mount only ROTATES it by the parallactic angle, and averaging the gradient
# vector over a swing dq retains sinc(dq/2) of its slope — 98.9%% at dq=30 deg,
# 90%% at 90 deg, 63.7%% at a full 180 deg. Translation alone retains 100%%
# (mean_t[a + b.(x-s(t))] keeps slope b). So a tracked flatless set needs this
# too; its SIZE there is simply unmeasured, since both measured sets are fixed
# mount. `mount` in acquisition.json cannot even distinguish equatorial from
# alt-az, so it is not a safe key for this decision.
    "$REPO/scripts/stack/build_sky_flat.sh" "$SESSION" "$SET" --dark="$DARK" --out="$SKYFLAT" $DESKYOPT
  fi
fi

# stack via the routed builder
if [ -f "$STACK" ]; then
  say "stack exists — skipping build ($STACK)"
else
  say "stack ($ROUTE)"
  case "$ROUTE" in
    standard)         "$REPO/scripts/stack/run_pipeline.sh" "$SESSION" "$SET";;
    undistort)        "$REPO/scripts/stack/run_undistort_pipeline.sh" "$SESSION" "$SET" --dark="$DARK" --flat="$SKYFLAT" $DESKYOPT;;
    undistort-groups) "$REPO/scripts/stack/run_undistort_groups.sh" "$SESSION" "$SET" --dark="$DARK" --flat="$SKYFLAT" $DESKYOPT;;
  esac
  [ -f "$STACK" ] || { say "builder finished but $STACK is missing"; exit 1; }
fi

# finish: solve -> cone -> SPCC -> linked autostretch judge PNG16
if judge_surface "$NAME" >/dev/null; then
  say "judge surface exists — skipping finish ($(basename "$(judge_surface "$NAME")"))"
else
  say "finish (solve -> SPCC -> judge surface)"
  "$REPO/scripts/stack/finish_render.sh" "$STACK" "$NAME" --session="$SESSION" --set="$SET"
fi

CULLS=$(python3 -c "
import json
try:
    s = json.load(open('$DSET/recipe.json')).get('stack') or {}
    e = s.get('exclude') or []
    print(f'{len(e)} frame(s) n={e}' if e else 'none')
except (OSError, ValueError):
    print('none')" 2>/dev/null || echo "none")
say "DONE — stack: $STACK | judge: $(judge_surface "$NAME" || echo '?') | culled: $CULLS | free: $(df -h "$SESSION" | tail -1 | awk '{print $4}')"
