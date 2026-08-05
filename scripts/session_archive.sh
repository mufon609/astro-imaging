#!/usr/bin/env bash
# Archive a session's DERIVED state, and optionally reset the session to raw
# frames only.
#
#   session_archive.sh <session> [--reset] [--to=<dir>] [--plan]
#
# WHAT IT MOVES (everything a run produced, nothing a camera produced):
#   datasets/<session>/          tracked records + their gitignored work scratch
#   web/results/<session>/       stacks, WCS/SPCC products, judge surfaces, previews
#   sessions/<session>/work/     masters and pipeline intermediates
#
# WHAT IT NEVER TOUCHES: the raw frame dirs (`sessions/<session>/<set>/`,
# `darks/`, `flats/`, `biases/`, `darkflats/`, `calib/`). It asserts the raw
# count is identical before and after, and aborts if it is not.
#
# WHY THIS EXISTS. Resetting a session for a clean end-to-end test was a
# hand-rolled sequence of cp/rm/git-rm, which is exactly the kind of thing that
# deletes a deliverable on the one run somebody mistypes. It also kept leaving
# gitignored scratch behind (`qa_work/frameqa/*.seq`, `audit_work/_stars.lst`)
# because `git rm` only removes what git tracks — so a "clean" session still had
# state a fresh run could inherit.
#
# THE ARCHIVE IS A HOLDING AREA, NOT A BACKUP OF RECORD. Storage on this rig is
# transient by design: raws live off-rig and re-stage in minutes, the tracked
# records live in git, and this archive exists so a fresh run can be COMPARED
# against what preceded it. Delete an archive once its comparison is done. If you
# want a real backup, it belongs off this machine.
#
# Root: $ASTRO_ARCHIVE_ROOT, default ~/astro-archive. Each run writes
# <root>/<session>_<stamp>/ and REFUSES to overwrite an existing one.
set -euo pipefail
REPO=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
cd "$REPO"

SESSION=${1:?usage: session_archive.sh <session> [--reset] [--to=<dir>] [--plan]}
RESET=0 PLAN=0 ROOT=${ASTRO_ARCHIVE_ROOT:-$HOME/astro-archive}
for a in "${@:2}"; do case "$a" in
  --reset) RESET=1;;
  --plan)  PLAN=1;;
  --to=*)  ROOT=${a#*=};;
  *) echo "unknown arg $a" >&2; exit 1;;
esac; done

[ -d "sessions/$SESSION" ] || [ -d "datasets/$SESSION" ] || [ -d "web/results/$SESSION" ] || {
  echo "session_archive: nothing named '$SESSION' under sessions/, datasets/ or web/results/" >&2; exit 1; }

RAW_GLOBS=( -iname '*.nef' -o -iname '*.dng' -o -iname '*.cr2' -o -iname '*.cr3'
            -o -iname '*.arw' -o -iname '*.raf' -o -iname '*.fit' -o -iname '*.fits' )
count_raws() {   # raw frames OUTSIDE work/ — i.e. what the camera produced
  find "sessions/$SESSION" -type f \( "${RAW_GLOBS[@]}" \) -not -path "sessions/$SESSION/work/*" 2>/dev/null | wc -l
}
RAW_BEFORE=$(count_raws)

DEST=$ROOT/${SESSION}_$(date +%Y-%m-%dT%H%M%S)
SRCS=()
for p in "datasets/$SESSION" "web/results/$SESSION" "sessions/$SESSION/work"; do
  [ -e "$p" ] && SRCS+=("$p")
done

echo "session_archive: $SESSION"
echo "  raw frames (kept, untouched): $RAW_BEFORE"
if [ ${#SRCS[@]} -eq 0 ]; then
  echo "  nothing derived to archive — the session is already raw-only"
  exit 0
fi
for p in "${SRCS[@]}"; do
  printf '  archive: %-34s %s\n' "$p" "$(du -sh "$p" 2>/dev/null | cut -f1)"
done
echo "  -> $DEST"
[ "$RESET" = 1 ] && echo "  --reset: the above are REMOVED from the tree afterwards (raws stay)"
[ "$PLAN" = 1 ] && { echo "  plan only — nothing done"; exit 0; }

[ -e "$DEST" ] && { echo "session_archive: $DEST already exists — refusing to overwrite" >&2; exit 1; }
mkdir -p "$DEST"
for p in "${SRCS[@]}"; do
  cp -a "$p" "$DEST/$(echo "$p" | tr '/' '_')"
done
echo "  archived $(find "$DEST" -type f | wc -l) files ($(du -sh "$DEST" | cut -f1))"

if [ "$RESET" = 1 ]; then
  # git rm removes only TRACKED files; the gitignored scratch beside them
  # (qa_work/frameqa/*.seq, audit_work/_stars.lst, siril logs) has to go too or
  # the "clean" session still carries state a fresh run can inherit.
  git rm -r -q --ignore-unmatch "datasets/$SESSION" 2>/dev/null || true
  rm -rf "datasets/$SESSION" "web/results/$SESSION" "sessions/$SESSION/work"
  RAW_AFTER=$(count_raws)
  if [ "$RAW_AFTER" != "$RAW_BEFORE" ]; then
    echo "session_archive: ABORT-AFTER-THE-FACT — raw count changed $RAW_BEFORE -> $RAW_AFTER." >&2
    echo "  Restore from $DEST immediately and do not trust this session." >&2
    exit 1
  fi
  echo "  reset: session is now raw-only ($RAW_AFTER frames, unchanged)"
fi
echo "  restore: cp -a $DEST/<entry> back to its path (entries are the path with / as _)"
