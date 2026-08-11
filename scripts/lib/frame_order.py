#!/usr/bin/env python3
"""Emit a set's frames in CAPTURE ORDER, not filename order.

Usage: frame_order.py <frame>...        -> one path per line, chronological

WHY THIS EXISTS — a MEASURED corruption that filename sort walks straight into.

The camera's frame counter wraps at 9999 -> 0001. A set that spans the wrap
sorts by NAME into an order that is not the order it was shot in, and the groups
builder slices GROUPS AS CONSECUTIVE TIME BLOCKS ("a group is a consecutive time
block of a 1497 s burst and the sky sweeps 6.25 deg of RA through it").

Measured on aug09/set-02 — 456 frames, one continuous 22.8-minute run at a
uniform 3.00 s cadence, wrapping DSC_9999 -> DSC_0001:

    by NAME  DSC_0001 … DSC_0264 , DSC_9808 … DSC_9999
    by TIME  DSC_9808 … DSC_9999 , DSC_0001 … DSC_0264
    frames in the same position under both orderings:  0 / 456

Under filename order the first group would be the LAST 100 frames shot, and one
group would straddle the wrap — joining frames ~20 minutes and ~6 deg of sky
apart into a single sub-stack whose pointing is the average of two ends of the
drift. Nothing downstream could see it: the member would simply register and
stack worse, and the cause would be invisible in the product.

It is not a re-aim. The epochs are continuous and the cadence never varies; only
the NAME goes backwards. (`segment_runs` reports such a set as two capture runs
for the same reason — a frame-number discontinuity — which is why the mount
probe confined its windows to 264 of 456 frames there. It still read a decisive
fixed signature, so that is a narrowed baseline rather than a wrong answer.)

BLAST RADIUS, measured across the whole corpus: 12 of 13 sets have name order ==
time order exactly; only aug09/set-02 differs, and it differs completely.

Falls back to the given order with a LOUD warning when epochs are unreadable
(a dedicated-astrocam set with no EXIF, say) — silence there would reintroduce
the bug it exists to prevent.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def capture_order(frames):
    """(ordered_frames, note) — chronological when every frame has an epoch."""
    import acquisition
    rows = acquisition.timeline(list(frames))
    by_name = {os.path.basename(f): f for f in frames}
    if not rows or not all(r.get("epoch") for r in rows) or len(rows) != len(frames):
        return list(frames), "EPOCHS UNREADABLE — falling back to the given order"
    rows.sort(key=lambda r: r["epoch"])
    ordered = [by_name.get(r["file"], r["file"]) for r in rows]
    same = sum(1 for a, b in zip(frames, ordered) if a == b)
    if same == len(frames):
        return ordered, ""
    return ordered, (f"CAPTURE ORDER DIFFERS FROM FILENAME ORDER — only "
                     f"{same}/{len(frames)} frames align (a frame-counter wrap "
                     f"or out-of-order names); using capture order")


def main():
    # stdin, not argv: a 500-frame list passed through xargs can be SPLIT into
    # several invocations at ARG_MAX, and each chunk would be ordered
    # independently — silently reintroducing the bug this exists to prevent.
    frames = sys.argv[1:]
    if not frames and not sys.stdin.isatty():
        frames = [ln.strip() for ln in sys.stdin if ln.strip()]
    if not frames:
        sys.exit(__doc__)
    ordered, note = capture_order(frames)
    if note:
        print(f"[frame_order] {note}", file=sys.stderr)
    print("\n".join(ordered))


if __name__ == "__main__":
    main()
