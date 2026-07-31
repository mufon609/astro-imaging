#!/usr/bin/env python3
"""THE one meaning of `recipe.json stack.exclude` — trailing FILENAME digits.

An exclude entry names a frame by the trailing digit run of its file name
(DSC_8647.NEF -> 8647; "M 20 Blue 16.fits" -> 16). Filename numbers are
stable across re-staging, re-batching and re-conversion; QA sequence indices
are not (they shift with the staged file list), and the two conventions
coexisting produced a measured silent no-op cull (a measured trap: an
index-style recipe consumed by the filename-matching builder excluded
nothing, exit 0). Every consumer and writer routes through this module:

  consumers  run_undistort_pipeline.sh / run_undistort_groups.sh (CLI keep
             mode), run_pipeline.sh (CLI positions mode — its Siril
             `unselect` needs 1-based sequence positions, which equal the
             staged order of the SAME sorted list it converts)
  writers    run_set_chain.sh auto-cull, cull_report.py suggestions

LOUD GUARD (the item-19 fix): an exclude number that matches ZERO staged
frames, or matches MORE THAN ONE, is a hard failure — a cull that cannot
apply exactly must stop the build, never silently keep everything. A frame
whose name carries no digits cannot be addressed by an exclude list and is
only an error when an exclude fails to resolve because of it.

CLI:
  cullspec.py keep      <recipe.json|-> <frame>...   kept frames, one/line
  cullspec.py positions <recipe.json|-> <frame>...   1-based positions of
                                                     excluded frames (staged
                                                     order), one/line
'-' means "no recipe" (keeps everything; prints nothing for positions).
Summary goes to stderr; unresolved/ambiguous excludes exit 1.
"""
import json
import os
import re
import sys


def frame_number(path):
    """Trailing digit run of the basename (extension stripped), or None."""
    m = re.search(r"(\d+)\D*$", os.path.splitext(os.path.basename(path))[0])
    return int(m.group(1)) if m else None


def load_excludes(recipe_path):
    """The recipe's stack.exclude as a sorted unique int list ([] if no
    recipe / no block). Raises ValueError on a malformed block."""
    if not recipe_path or recipe_path == "-" or not os.path.exists(recipe_path):
        return []
    stack = (json.load(open(recipe_path)).get("stack") or {})
    e = stack.get("exclude") or []
    if not (isinstance(e, list) and all(isinstance(n, int) and n > 0 for n in e)):
        raise ValueError(f"stack.exclude {e!r} must be a list of positive frame numbers")
    return sorted(set(e))


def resolve(recipe_path, frames):
    """(kept_frames, excluded_positions, problems). Positions are 1-based in
    the given frame order. problems is a list of human-readable strings —
    non-empty means the cull CANNOT apply exactly and the caller must stop."""
    excludes = load_excludes(recipe_path)
    if not excludes:
        return list(frames), [], []
    bynum = {}
    for i, f in enumerate(frames):
        n = frame_number(f)
        if n is not None:
            bynum.setdefault(n, []).append(i)
    kept, positions, problems = [], [], []
    hit = set()
    for n in excludes:
        where = bynum.get(n, [])
        if not where:
            problems.append(f"exclude {n}: matches NO staged frame")
        elif len(where) > 1:
            problems.append(
                f"exclude {n}: AMBIGUOUS — matches "
                + ", ".join(os.path.basename(frames[i]) for i in where))
        else:
            hit.add(where[0])
            positions.append(where[0] + 1)
    kept = [f for i, f in enumerate(frames) if i not in hit]
    return kept, sorted(positions), problems


def main():
    if len(sys.argv) < 3 or sys.argv[1] not in ("keep", "positions"):
        sys.exit(__doc__)
    mode, recipe, frames = sys.argv[1], sys.argv[2], sys.argv[3:]
    try:
        kept, positions, problems = resolve(recipe, frames)
    except ValueError as e:
        sys.exit(f"cullspec: invalid stack block in {recipe}: {e}")
    if problems:
        for p in problems:
            print(f"cullspec: {p}", file=sys.stderr)
        sys.exit(f"cullspec: ABORT — {len(problems)} exclude(s) cannot apply "
                 f"exactly (recipe {recipe}); a cull must never silently no-op "
                 "(a measured silent-no-op trap)")
    n_ex = len(frames) - len(kept)
    print(f"cull: recipe excludes {n_ex} frame(s); {len(kept)} eligible"
          if n_ex else f"cull: no recipe exclusions; {len(kept)} eligible",
          file=sys.stderr)
    for out in (kept if mode == "keep" else [str(p) for p in positions]):
        print(out)


if __name__ == "__main__":
    main()
