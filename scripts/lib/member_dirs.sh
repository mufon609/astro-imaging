#!/usr/bin/env bash
# The ONE enumerator of canonical member dirs, shared by run_corpus_combine.sh (the
# compose door) and run_member_crop.sh (the portion-rule stage) — factored out so the
# two can never disagree about what a member is.
#
#   source scripts/lib/member_dirs.sh
#   canonical_member_dirs <session-dir>...      # prints one absolute groups_set-NN dir per line
#
# ALLOW-LIST, not a deny-list of the arm suffixes that happen to exist today. A
# canonical member dir is `<session>/work/groups_set-NN` and nothing else: set-00
# and set-0<letter> are the SPARE-FRAMES buckets (owner convention: real sets start
# at 01), and every arm dir (`_pinned`, `_l1arm`, `_crop5lr`, …) is a diagnostic
# variant that must never be composed into the deliverable. The deny-list this
# replaced named the two arms that existed when it was written, so every arm
# created after it would have been composed in silently (run_corpus_combine.sh's
# history). Dirs holding no sub_*.fit are skipped; a session with no member dir is
# reported by the caller, not here.
canonical_member_dirs() {  # <session-dir>...
  local S gd
  for S in "$@"; do
    [ -d "$S" ] || { echo "no such session dir: $S" >&2; return 1; }
    S=$(cd "$S" && pwd)
    for gd in "$S"/work/groups_set-*; do
      [ -d "$gd" ] || continue
      case "$(basename "$gd")" in
        groups_set-00|groups_set-0[a-z]) continue;;          # spare buckets: never members
        groups_set-[0-9][0-9]) ;;
        *) echo "[members]   skipping $(basename "$gd") — not a canonical groups_set-NN member dir (arm variants are not the corpus)" >&2; continue;;
      esac
      ls "$gd"/sub_*.fit >/dev/null 2>&1 || continue
      echo "$gd"
    done
  done
}
