#!/usr/bin/env bash
# ONE-CLICK durable-core chain for a light set (user-ratified amendment,
# web/README.md): preflight -> frame QA -> obstruction audit -> cull ->
# route-by-fingerprint stack -> solve -> SPCC -> diagnostic judge surface.
# Every pixel op stays an official
# tool inside the existing pinned scripts; this only sequences them with hard
# gates between, and it STOPS the moment a decision belongs to the user:
#
#   exit 2  mount declared-vs-measured CONTRADICT (fingerprint) — reconcile
#   exit 3  RETIRED — frame-QA flags no longer stop: the STANDING USER
#           POLICY auto-culls flagged defect-side frames (they exclude like
#           any obstruction), writes the recipe stack block with the flags
#           as the why, and reports the decision inline + in the session
#           summary; a hand-ratified stack block is never overwritten
#   exit 4  mount undeclared AND underivable — the instruments disagreed or
#           nothing measured. A decisive signature self-derives and does NOT
#           stop (acquisition.resolve, mount_source=derived)
#   exit 5  unroutable fingerprint (neither tracked nor fixed+wide) — the
#           two-window drift solve / the user decides the route
#   exit 6  real flats staged but no master-flat wiring for the undistort
#           route — resolve the flat manually (documented gap)
#   exit 7  readiness RED — the one-surface report (readiness_report.py)
#           names the blocker up front; nothing was built
#   exit 8  the finished PRODUCT regressed against this set's accepted
#           baseline (scripts/qa/baseline_guard.py). Nothing is blocked or
#           rewritten — the stack and judge surface are built — but the
#           product no longer measures like the one a human accepted, which
#           is a decision only the user can close: find the cause, or
#           re-seed the baseline with a note if the change is deliberate
#
#   run_set_chain.sh <session-dir> <set> [--plan] [--yes] [--route=auto|single|groups] [--group=N]
#
# --yes is the ONE approval, given up front: after the measure phase prints
# the readiness report (every criterion GREEN/YELLOW/RED on one surface), the
# build runs unattended. The web run button passes it — the click IS the
# approval. Without it an interactive terminal asks once after the report; a
# non-interactive run stops there (exit 0, report recorded) so nothing builds
# on an approval nobody gave.
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
# fingerprint (tracked -> standard; fixed+wide -> undistort GROUPS, the
# STANDING route: retained sub-stacks keep the cross-set combine buildable
# at a measured-NULL quality cost; --route=single is the operator override,
# printed as FORCED — see force_route() for the ratified why + numbers);
# the printed reason keeps every derived route fully disclosed.
set -euo pipefail
REPO=$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)
source "$REPO/scripts/stack/disk_budget.sh"   # the SAME per-set disk derivation
                                              # run_undistort_pipeline.sh enforces. Routing
                                              # on a private copy is what let this chain send
                                              # a set to a builder that then refused it.
SESSION=${1:?usage: run_set_chain.sh <session-dir> <set> [--plan]}
SET=${2:?missing <set>}
PLAN=0 DESKYOPT= FORCE_ROUTE= GROUPOPT= YES=0
for a in "${@:3}"; do case "$a" in
  --plan) PLAN=1;;
  --yes) YES=1;;
  --desky) DESKYOPT=--desky;;
  --no-desky) DESKYOPT=;;
  --route=*) FORCE_ROUTE=${a#*=};;
  --group=*) GROUPOPT=--group=${a#*=};;
  *) echo "unknown arg $a" >&2; exit 1;;
esac; done
case "${FORCE_ROUTE:-auto}" in
  auto|single|groups) ;;
  *) echo "--route must be auto|single|groups (got '$FORCE_ROUTE')" >&2; exit 1;;
esac

# --route= OVERRIDES the standing route WITHIN the undistort class. It does not
# change the class — that stays derived from the fingerprint.
#
# GROUPS IS THE STANDING ROUTE (user-ratified: this fork is never a question).
# Single-pass DELETES every warped and registered frame and keeps only a
# -framing=min final, while run_undistort_compose.sh composes SUB-STACKS;
# composing per-set finals instead is a registered dead end (each final has
# already discarded its outer drift zones, so the combine has holes exactly
# where only those zones covered) — so single-pass permanently forecloses the
# cross-set combine. What it buys back is one fewer interpolation pass, and
# that delta MEASURED NULL (one-knob A/B, 60 frames even-stride: 9/9
# drift-axis stations within 0.05 px majFWHM / 0.014 roundness; the full-depth
# ledger's small unresolved 0.12-0.18 px delta runs in groups' favor), plus
# the retained sub-stacks (one full-frame float FITS per group, ~285 MiB at
# 6064x4040 OSC). Nothing measured favors single-pass, so the data settles the
# fork and the router never asks. --route=single stays for the operator — an
# A/B arm, a deliberate no-combine build — and the plan prints it as
# OPERATOR-FORCED rather than derived.
force_route() {   # <derived-route> -> the route to use, reason on stderr
  case "$FORCE_ROUTE" in
    groups) [ "$1" = undistort ] && { echo "undistort-groups"; return; };;
    single) [ "$1" = undistort-groups ] && { echo "undistort"; return; };;
  esac
  echo "$1"
}
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
aud = rd("audit_work/anomaly_audit.json")
mc = fp.get("mount_check") or {}
exif = acq.get("exif") or {}
print(acq.get("mount") or "")
print(acq.get("mount_source") or "")
print(mc.get("verdict") or "")
print(mc.get("measured") or "")
print(exif.get("fov_deg") if exif.get("fov_deg") is not None else "")
print("" if qa is None else len(qa.get("flagged_defect_side_z") or []))
print("yes" if isinstance(recipe.get("stack"), dict) else "")
# obstruction audit: objects|longest dwell|UNKNOWN count, or empty if never run.
# The dwell is what run_undistort_groups.sh turns into its group-size floor.
if aud is None:
    print("")
else:
    objs = aud.get("unique_objects") or []
    print("%d|%d|%d" % (len(objs), max((o.get("n") or 0) for o in objs) if objs else 0,
                        sum(1 for o in objs if o.get("cls") not in ("aircraft", "satellite"))))
print(fp.get("label") or "not yet derived")   # last line stays non-empty:
PY
)                                             # $() strips trailing newlines
{ read -r MOUNT; read -r MSRC; read -r VERDICT; read -r MEASURED; read -r FOV; read -r NFLAGS; \
  read -r RATIFIED; read -r AUDITSUM; read -r FPLABEL; } <<< "$FACTS" || true

MOUNT_EFF=${MEASURED:-$MOUNT}
# The single-pass peak is NOT a routing input (groups is the standing route) —
# it is derived for the PLAN's disk line and for a forced --route=single, via
# the same undistort_peak_gib that builder's preflight enforces, so a forced
# route and its builder cannot disagree. DERIVED from this set's own frame
# geometry, so a bigger sensor or a mono corpus is budgeted for what it is;
# legitimately underivable on a fresh set (the plan prints before preflight
# seeds the record) — an empty value is not an error, and the builders
# enforce their own budgets either way.
FREE_GB=$(df -BG --output=avail "$SESSION" | tail -1 | tr -dc 0-9)
SINGLEPASS_GB=$(undistort_peak_gib "$SESSION" "$SET" "$NFRAMES" 2>/dev/null || echo "")
ROUTE= REASON=
if [ "$MOUNT_EFF" = "tracked" ]; then
  ROUTE=standard
  REASON="tracked mount: no inter-frame drift to fight -> calibrate/register/stack (run_pipeline)"
elif [ "$MOUNT_EFF" = "fixed" ] && [ -n "$FOV" ] && \
     python3 -c "import sys; sys.exit(0 if float('$FOV') >= 10 else 1)"; then
  # GROUPS is the standing route for the whole class — no disk fork, no
  # question; force_route() carries the ratified why + numbers
  ROUTE=undistort-groups
  REASON="fixed mount + ${FOV} deg field -> undistort class; groups is the STANDING route (sub-stacks keep the cross-set combine buildable; quality delta vs single-pass measured NULL)${SINGLEPASS_GB:+ — disk ${FREE_GB}G free, single-pass peak would be ${SINGLEPASS_GB}G (--route=single overrides)}"
  FORCED=$(force_route "$ROUTE")
  if [ "$FORCED" != "$ROUTE" ]; then
    REASON="OPERATOR-FORCED --route=$FORCE_ROUTE (derived was '$ROUTE'): $REASON"
    ROUTE=$FORCED
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
say "PLAN — $NFRAMES frames | mount '${MOUNT:-UNDECLARED}'${MSRC:+ ($MSRC)} | fingerprint: $FPLABEL${VERDICT:+ ($VERDICT)}"
say "PLAN — frame QA: $([ -n "$NFLAGS" ] && echo "done, $NFLAGS defect-side flag(s)" || echo "not yet run — will run") | cull: $([ -n "$RATIFIED" ] && echo "ratified recipe block" || echo "standing auto-cull (flagged frames exclude; reported at the end)")"
# ~1 s/frame measured on this rig (july31: 500 frames in 8 min, 260 in 4)
say "PLAN — obstruction audit: $([ -n "$AUDITSUM" ] \
  && echo "done, ${AUDITSUM%%|*} object(s), longest dwell $(x=${AUDITSUM#*|}; echo "${x%%|*}") frame(s)" \
  || echo "not yet run — will run (~$((NFRAMES / 60 + 1)) min); it is what gives the groups builder its dwell floor")"
say "PLAN — route: $ROUTE${REASON:+ — $REASON}"
if [ -z "$MOUNT" ] && [ "$ROUTE" != stop-undeclared ]; then
  # measured but not yet declared: the route above came from the MEASURED
  # signature, which the run ADOPTS (mount_source=derived) and continues on
  say "PLAN — mount measured '$MEASURED', not declared: the run adopts it (mount_source=derived) and continues — declaring on the set page is the override, not a required step"
fi
case "$ROUTE" in
  stop-undeclared) say "PLAN — WILL MEASURE then derive: mount undeclared — the fingerprint measures it (roundness if QA exists, else the two-window drift probe: scripts/qa/mount_probe.sh); a decisive verdict is ADOPTED (mount_source=derived) and the run continues; it STOPS (exit 4) only if the instruments disagree or nothing measures";;
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
      undistort-groups) say "  4. scripts/stack/run_undistort_groups.sh $SESSION $SET --dark=$DARK --flat=$SKYFLAT $DESKYOPT $GROUPOPT";;
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
# MOUNT, by the evidence gate (CLAUDE.md "WHERE THE GATE ACTUALLY IS"): the
# instruments measure the signature and a DECISIVE one is adopted on the
# record (acquisition.resolve, mount_source=derived), announced, and the run
# CONTINUES — the data settled it. It stops (exit 4) only when the
# instruments disagree or nothing measures, the one mount call a human is
# actually needed for. A set-page declaration remains the override, and
# every later re-derive still cross-checks it (CONTRADICT stops, exit 2).
derive_mount() {  # resolve: seed/refresh the record; print a just-adopted mount, or ""
  python3 - "$REPO" "$SESSION" "$SET" <<'PY' 2>/dev/null || true
import glob, os, sys
sys.path.insert(0, os.path.join(sys.argv[1], "scripts", "lib"))
import acquisition
frames = sorted(f for pat in ("*.nef", "*.NEF", "*.dng", "*.DNG", "*.cr2",
                              "*.CR2", "*.arw", "*.ARW", "*.fit", "*.fits")
                for f in glob.glob(os.path.join(sys.argv[2], sys.argv[3], pat)))
try:
    print(acquisition.resolve(sys.argv[2], sys.argv[3], frames).get("derived_now") or "")
except acquisition.AcquisitionUndeclared:
    pass          # underivable so far — the record is still seeded with the facts
PY
}
if [ -z "$MOUNT" ]; then ROUTE=stop-undeclared; fi
if [ "$ROUTE" = stop-undeclared ]; then
  say "mount undeclared — measuring the signature"
  # ONE resolve call both seeds the EXIF facts and adopts a signature already
  # decisive on record. Capture the value HERE: resolve() reports derived_now
  # only on the adopting call, so a throwaway seed call swallows the adoption
  # and "nothing derived" mis-reads as instrument disagreement — exit 4 with
  # the answer already on the record.
  DERIVED=$(derive_mount)
  if [ -z "$DERIVED" ]; then
    python3 "$REPO/scripts/lib/fingerprint.py" "$SESSION" "$SET" >/dev/null || true
    MEASURED=$(python3 -c "import json;print((json.load(open('$DSET/fingerprint.json')).get('mount_check') or {}).get('measured') or '')" 2>/dev/null || true)
    if [ -z "$MEASURED" ]; then
      say "roundness not decisive (or no QA yet) — running the two-window drift probe"
      "$REPO/scripts/qa/mount_probe.sh" "$SESSION" "$SET" >/dev/null || true
    fi
    DERIVED=$(derive_mount)   # adopt what the probe/fingerprint just settled
  fi
  if [ -n "$DERIVED" ]; then
    say "mount DERIVED from the data: '$DERIVED' (recorded as mount_source=derived, not a human declaration)"
    say "  the two-instrument cross-check still runs every re-derive; a later measurement that"
    say "  disagrees with this one STOPS as CONTRADICT. Override by setting \"mount\" on the set page."
    MOUNT=$DERIVED; MOUNT_EFF=$DERIVED
    # The plan-phase ROUTE is stale (forced to stop-undeclared; on a fresh
    # set the facts landed only in the resolve above). Hand it to the
    # existing post-preflight re-derivation, which also rebuilds STACK/NAME
    # and the disk budget — left unrouted, the builder case matches no arm
    # and the run dies at "builder finished but stack missing" after the
    # masters.
    ROUTE=derive-after-preflight
  else
    R4=$(python3 -c "import json;print(((json.load(open('$DSET/fingerprint.json')) or {}).get('mount_check') or {}).get('reason') or 'no measurement produced')" 2>/dev/null || echo "no measurement produced")
    say "STOP: mount underivable — $R4"
    say "  the instruments could not settle it, which is the one mount call that is yours:"
    say "  declare \"mount\" on the set page (fixed | tracked), then re-click"
    exit 4
  fi
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
# OBSTRUCTION AUDIT — the step README lists as per-set prep and this chain did
# not call, which is why every july31 product was built with the groups builder
# printing "dwell floor: NOT CHECKED — UNVERIFIED".
#
# WHY IT BELONGS IN THE CHAIN AND NOT BESIDE IT. run_undistort_groups.sh derives
# its group size to keep every group inside the GESD rejection band, and the other
# half of that rationale — "any transient is a clear minority" — is satisfied only
# if a group exceeds max_dwell / the GESD outlier fraction. The builder already
# computes that floor, raises the derived group to it, and ABORTS an explicit
# --group below it. It reads the floor from THIS record, so with no record the
# constraint is not enforced, merely asserted. Measured on july31: all four sets
# cleared, but set-03 cleared at 90% of the cap (a 27-frame satellite, floor 90
# against a running group of 100) — by arithmetic accident, since nothing in the
# derivation had ever read a dwell length.
#
# It runs on EVERY route, not just the groups one. The dwell floor is the
# groups-specific consumer, but the inventory and the UNKNOWN surface are per-set
# QA that any route wants, and a route-conditional QA step is one that silently
# does not run. Report-only: it never moves, deletes or rewrites a frame, and it
# gates nothing here — the builder's own floor check is the gate.
if [ -z "$AUDITSUM" ]; then
  say "obstruction audit (~$((NFRAMES / 60 + 1)) min at ~1 s/frame)"
  python3 "$REPO/scripts/qa/anomaly_audit.py" "$SESSION/$SET"
  AUDITSUM=$(python3 - "$DSET/audit_work/anomaly_audit.json" <<'PY'
import json, sys
objs = json.load(open(sys.argv[1])).get("unique_objects") or []
print("%d|%d|%d" % (len(objs), max((o.get("n") or 0) for o in objs) if objs else 0,
                    sum(1 for o in objs if o.get("cls") not in ("aircraft", "satellite"))))
PY
)
else
  say "obstruction audit exists — skipping ($DSET/audit_work/anomaly_audit.json)"
fi
AUD_OBJ=${AUDITSUM%%|*}; AUD_REST=${AUDITSUM#*|}
AUD_DWELL=${AUD_REST%%|*}; AUD_UNKNOWN=${AUD_REST##*|}
# The floor the groups builder will apply, restated here so the number is visible
# at the step that produced it rather than only inside the builder.
AUD_FLOOR=$(python3 -c "import math;print(math.ceil($AUD_DWELL / 0.30))")
say "  $AUD_OBJ unique object(s); longest dwell $AUD_DWELL frame(s) -> groups dwell floor >= $AUD_FLOOR"
if [ "$AUD_UNKNOWN" != 0 ]; then
  # UNKNOWN is the audit's honest anomaly surface: an obstruction matching no
  # known signature. Reported loudly, never gated — classifying it is the user's.
  say "  ANOMALY: $AUD_UNKNOWN object(s) classified UNKNOWN — matched no callout signature."
  say "    These deserve human eyes: $DSET/audit_work/anomaly_audit.json"
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

# EXIF uniformity of the frames that will ACTUALLY be stacked (post-cull).
# The standard route hard-fails on a mixed set (run_pipeline.sh `uniform()`),
# but the undistort builders have no equivalent, so a frame shot at a different
# exposure/ISO enters the stack with a master dark that does not match it —
# over- or under-subtracted, silently. Frame QA does not catch this: its defect
# sides are fwhm +1, bg +1, round -1, nstars -1, and a SHORTER exposure moves bg
# and trailing the safe way, so only the nstars term can fire, by luck.
# WARN, never stop: the exposure is a fact the user may have chosen, and the
# cull decision is theirs (a hand-ratified recipe block is how they act on it).
mapfile -t KEPT < <(python3 "$REPO/scripts/lib/cullspec.py" keep "$DSET/recipe.json" "${FRAMES[@]}" 2>/dev/null || printf '%s\n' "${FRAMES[@]}")
if [ ${#KEPT[@]} -gt 0 ] && command -v exiftool >/dev/null 2>&1; then
  # NOT a pipe into python: a `<<'PY'` heredoc IS stdin, so it would replace the
  # pipe and the exiftool rows would never arrive (silent empty check).
  EXIFTSV=$(exiftool -q -T -FileName -ExposureTime -ISO "${KEPT[@]}" 2>/dev/null || true)
  python3 - "$SET" "$EXIFTSV" <<'PY' || true
import collections, sys
rows = [l.split("\t") for l in sys.argv[2].splitlines() if l.strip()]
rows = [r for r in rows if len(r) >= 3]
if rows:
    tally = collections.Counter((r[1], r[2]) for r in rows)
    (exp, iso), n = tally.most_common(1)[0]
    odd = [r for r in rows if (r[1], r[2]) != (exp, iso)]
    if odd:
        s = sys.argv[1]
        print(f"[chain {s}] WARNING: {len(odd)} of {len(rows)} frames to be stacked "
              f"do not match the dominant {exp}s ISO{iso} — the master dark matches "
              f"only the dominant setting, so these are mis-calibrated:")
        for r in odd:
            print(f"[chain {s}]     {r[0]}  {r[1]}s ISO{r[2]}")
        print(f"[chain {s}] WARNING: exclude them via recipe.json stack.exclude "
              f"if the mismatch is not intended")
PY
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
      # groups is the STANDING route (force_route has the why); the builders
      # derive and enforce their own disk budgets
      ROUTE=undistort-groups
      FORCED=$(force_route "$ROUTE")
      [ "$FORCED" = "$ROUTE" ] || say "route FORCED by --route=$FORCE_ROUTE (derived was '$ROUTE')"
      ROUTE=$FORCED
      case "$ROUTE" in
        undistort)        STACK=$RESULTS/stack_$SET.fit;;
        undistort-groups) STACK=$RESULTS/stack_${SET}_full.fit;;
      esac;;
    *) say "STOP: route still underivable after preflight (mount/fov missing from the seeded facts) — the user picks the route"; exit 5;;
  esac
  NAME=$(basename "$STACK" .fit); NAME=${NAME#stack_}
  say "route (re-derived): $ROUTE"
fi

# OPTICS GATE FIRST — before any master is built. run_undistort_pipeline.sh runs
# this itself, but it runs it AFTER this chain has already spent a master dark and
# a whole-set sky flat. Both are throwaway work if the optics are wrong, and the
# gate's failure modes are exactly the silent-wrong ones (a lens lensfun cannot
# match warps NOTHING and says nothing; an installed model that is not the PINNED
# one warps with different optics than every product it will be compared against).
# Cost here is one darktable render pair, ~10 s; cost of discovering it after the
# flat is the flat. The builder keeps its own call — defence in depth, not a
# substitute.
if [ "$ROUTE" != standard ]; then
  say "optics preflight (before the masters — a wrong-optics stop must not cost a flat build)"
  mkdir -p "$DSET/qa_work"
  python3 "$REPO/scripts/stack/lens_preflight.py" "$SESSION" "$SET" --require-profile \
    --json="$DSET/qa_work/lens_preflight.json" || exit 1
fi

# ---- READINESS: every criterion on ONE surface, then ONE approval ---------
# The measure phase above (acquisition, fingerprint, frame QA, audit, cull,
# optics) has produced every record the evaluator quotes; from here the build
# runs unattended. RED stops HERE (exit 7) — never hours into a build. The
# report is a tracked record, so what was approved is auditable afterwards.
say "readiness report"
RRC=0
python3 "$REPO/scripts/qa/readiness_report.py" "$SESSION" "$SET" \
  --route="$ROUTE" --post-measure ${FORCE_ROUTE:+--forced-route=$FORCE_ROUTE} || RRC=$?
if [ "$RRC" = 3 ]; then
  say "STOP: readiness RED — the report above names the blocker; nothing was built"
  exit 7
elif [ "$RRC" != 0 ]; then
  say "readiness evaluator failed (rc=$RRC)"; exit "$RRC"
fi
if [ "$YES" != 1 ]; then
  if [ -t 0 ]; then
    read -r -p "[chain $SET] proceed with the build? [y/N] " ANS
    case "$ANS" in
      y|Y|yes|YES) ;;
      *) say "not approved — nothing built (report recorded: $DSET/readiness.json)"; exit 0;;
    esac
  else
    say "report only — no --yes and no terminal to ask. Re-run with --yes to build (the web run button passes it)."
    exit 0
  fi
fi

# masters (undistort routes bring their own; the standard route's builder
# resolves masters internally and hard-stops flatless itself)
if [ "$ROUTE" != standard ]; then
  # DARKS vs LIGHTS. The standard route checks this (run_pipeline.sh preflight)
  # and WARNs on a mismatch; the undistort route checked NOTHING — neither this
  # chain, nor build_master_dark.sh, nor run_undistort_pipeline.sh, which simply
  # consumes whatever --dark= it is handed. july31's 347 darks do match the lights
  # at 2.5 s / ISO1600, but nothing in the pipeline established that. Same
  # semantics as the standard route: a mismatch is DEGRADED, not fatal (the dark
  # still carries the bias level and the hot-pixel map that -cc=dark needs), so it
  # WARNs loudly rather than stopping — changing that to a stop is a gate change
  # and belongs in its own bracket.
  if [ -d "$SESSION/darks" ]; then
    python3 - "$SESSION" "$SET" <<'PY' || true
import glob, os, re, subprocess, sys
sess, sset = sys.argv[1], sys.argv[2]
RAW = ("*.nef", "*.dng", "*.cr2", "*.cr3", "*.arw", "*.raf")
def facts(d):
    fs = [f for p in RAW for f in glob.glob(os.path.join(d, p))
          + glob.glob(os.path.join(d, p.upper()))]
    if not fs:
        return None, 0
    r = subprocess.run(["exiftool", "-q", "-T", "-ExposureTime", "-ISO", *fs],
                       capture_output=True, text=True)
    vals = sorted({l.strip() for l in r.stdout.splitlines() if l.strip()})
    return vals, len(fs)
dv, dn = facts(os.path.join(sess, "darks"))
lv, ln = facts(os.path.join(sess, sset))
if not dv or not lv:
    sys.exit(0)                      # not a camera-raw corpus; nothing to compare
if len(dv) > 1:
    print(f"[chain {sset}] WARNING: darks/ is MIXED ({dn} frames): {dv}")
if len(lv) > 1:
    print(f"[chain {sset}] WARNING: {sset} is MIXED ({ln} frames): {lv}")
if dv[:1] != lv[:1]:
    print(f"[chain {sset}] WARNING: darks {dv} != {sset} {lv} — the master dark "
          "then works as a bias + hot-pixel map only, NOT as a dark-current "
          "subtraction. Degraded, not fatal; shoot matched darks.")
else:
    print(f"[chain {sset}] darks match the lights ({dn} darks, {ln} lights, "
          f"exposure/ISO {lv[0].replace(chr(9), ' / ')})")
PY
  fi
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
# DESKY IS OFF BY DEFAULT — it was ON from 2026-07-29 to 2026-08-04 and that was
# a 31x REGRESSION in background flatness. Measured on july31/set-01, 500 frames,
# one knob, everything else identical (Siril stat, medians, box 400/margin 200):
#
#   --desky ON  (shipped 07-29..08-04)   corner spread 12.4%   edge dipole +0.148
#   --desky OFF (the prior pipeline)     corner spread  0.4%   edge dipole +0.004
#
# 0.4% reproduces the 0.3-0.7% the route delivered before --desky landed. The
# mechanism: `seqsubsky` is a BACKGROUND EXTRACTION operator, defined on a
# flat-fielded image. The flat builder was running it on RAW frames that still
# carry vignetting — the frame is sky x V, not sky. Fitting an additive plane to
# that product and subtracting it overshoots hardest where V curves hardest, at
# the frame edge, and drives the local asymmetry through zero: the raw light
# measures +0.426 there, the --desky flat -0.550, sign INVERTED, in every session
# tested. Dividing by that flat roughly doubles the error instead of removing it.
# Numbers + the three-arm comparison: datasets/july31/experiments.jsonl.
#
# The concern that motivated --desky is REAL and remains open: a sky flat is a
# median of the set's own lights, so it converges to sky x V and calibration
# leaves the object carrying the sky's spatial profile (measured at 3.11% / 241
# sigma by differential star photometry). That is a genuine defect. --desky is
# simply not a valid fix for it, and its cure measured 31x worse than the
# disease. Pass --desky to reproduce the regressed configuration for testing.
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
    undistort-groups) "$REPO/scripts/stack/run_undistort_groups.sh" "$SESSION" "$SET" --dark="$DARK" --flat="$SKYFLAT" $DESKYOPT $GROUPOPT;;
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

# ---- no-regression check against the set's own accepted baseline ---------
# LAST, because it compares the finished PRODUCT. This is the check the repo did
# not have when a 31x background regression shipped and stayed in for six days:
# every other guard here verifies WIRING (that the code is plumbed the way
# doctrine says), and `--desky` left every wire intact while corrupting the data.
#
# It is a no-regression RECORD, not a quality gate, so it never blocks or rewrites
# anything — the product is already built and every aesthetic step past this point
# is user-gated anyway. But a regression IS a decision that belongs to the user,
# so it exits 8 the way the mount and route gates exit 2/4/5/6: loud, named, and
# still flagging on the next re-click until the human either finds the cause or
# re-seeds the baseline with a note. A DELIBERATE improvement fails it too, and
# that is correct.
BASEPROD=$RESULTS/stack_${NAME}_spcc.fit
[ -f "$BASEPROD" ] || BASEPROD=$STACK          # mono sets skip SPCC entirely
GUARD_RC=0
if [ ! -f "$DSET/baseline.json" ]; then
  say "no-regression: no baseline for this set yet — nothing to compare against."
  say "  Seed one ONCE YOU HAVE ACCEPTED this product (it becomes the reference"
  say "  every later run is measured against):"
  say "    python3 scripts/qa/baseline_guard.py $SESSION $SET $BASEPROD --seed --note='why'"
else
  say "no-regression: comparing the product against this set's accepted baseline"
  python3 "$REPO/scripts/qa/baseline_guard.py" "$SESSION" "$SET" "$BASEPROD" || GUARD_RC=$?
fi

CULLS=$(python3 -c "
import json
try:
    s = json.load(open('$DSET/recipe.json')).get('stack') or {}
    e = s.get('exclude') or []
    print(f'{len(e)} frame(s) n={e}' if e else 'none')
except (OSError, ValueError):
    print('none')" 2>/dev/null || echo "none")
say "DONE — stack: $STACK | judge: $(judge_surface "$NAME" || echo '?') | culled: $CULLS | obstructions: ${AUD_OBJ:-?} (longest dwell ${AUD_DWELL:-?}) | free: $(df -h "$SESSION" | tail -1 | awk '{print $4}')"
if [ "${AUD_UNKNOWN:-0}" != 0 ]; then
  say "  ANOMALY UNRESOLVED: $AUD_UNKNOWN obstruction(s) classified UNKNOWN — see $DSET/audit_work/anomaly_audit.json"
fi

if [ "$GUARD_RC" != 0 ]; then
  say "STOP: the product REGRESSED against this set's accepted baseline (above)."
  say "  Nothing was blocked or rewritten — the stack and judge surface are built."
  say "  Find the cause, or if the change is deliberate and you have judged it"
  say "  better, re-seed with --reseed and a note. Re-running keeps flagging until"
  say "  one of those happens."
  exit 8
fi
