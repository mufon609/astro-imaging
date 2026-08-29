#!/usr/bin/env bash
# CAMPAIGN DRIVER — BACKLOG output-norm-zero-point, the from-raws rebuild under
# ONE HEAD (stages 1-3 shipped: no -output_norm at any stacking tier, references
# pinned, anchors stamped; stage 4: the guard's level rows advisory).
# Runs the chain's OWN scripts, unattended, in the order the owner directed:
#   july31 -> aug06 -> aug09 -> aug14 (each: QA -> readiness -> from-raws members
#   -> per-set finals -> solve/SPCC/finish -> baseline_guard advisory -> the
#   night combine), then the four-night corpus.
# One log; every stage start/end timestamped; the first non-zero exit stops the
# campaign with the code in the log (set -e + an explicit trap).
# Launch (GO #8, not before):  nohup setsid bash scripts/.../campaign_zeropoint.sh &
# The move-aside that freed the chain's default names is recorded in
# datasets/corpus/campaign_zeropoint/moveaside_manifest.json.
set -euo pipefail
REPO=/home/samsung/Desktop/astro-imaging
LOG=$REPO/sessions/campaign_zeropoint.log
cd "$REPO"
exec >>"$LOG" 2>&1
stamp(){ date '+%Y-%m-%dT%H:%M:%S'; }
trap 'rc=$?; [ "$rc" -eq 0 ] || echo "$(stamp) CAMPAIGN STOPPED: stage \"${STAGE:-?}\" exited $rc"; exit $rc' EXIT
echo "$(stamp) CAMPAIGN START  HEAD=$(git -C "$REPO" rev-parse --short HEAD)  free=$(df -h "$REPO/sessions" | tail -1 | awk '{print $4}')"
[ -z "$(git -C "$REPO" status --short -- scripts docs)" ] || echo "$(stamp) NOTE: uncommitted changes under scripts/ or docs/ — PIPEREV will not describe the build"
for S in july31 aug06 aug09 aug14; do
  STAGE="session $S"
  echo "$(stamp) === $STAGE START"
  "$REPO/scripts/stack/run_session_chain.sh" "$REPO/sessions/$S" --yes
  echo "$(stamp) === $STAGE END  free=$(df -h "$REPO/sessions" | tail -1 | awk '{print $4}')"
done
STAGE="corpus combine (july31+aug06+aug09+aug14)"
echo "$(stamp) === $STAGE START"
"$REPO/scripts/stack/run_corpus_combine.sh" "$REPO/sessions/july31" "$REPO/sessions/aug06" "$REPO/sessions/aug09" "$REPO/sessions/aug14"
echo "$(stamp) === $STAGE END  free=$(df -h "$REPO/sessions" | tail -1 | awk '{print $4}')"
STAGE=done
echo "$(stamp) CAMPAIGN DONE"
