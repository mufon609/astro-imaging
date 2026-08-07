# Fresh-session prompt — process aug06 from raws, then the two-session combine

Read `CLAUDE.md` first. It states what this repo is, the binding rules, and the
order to read everything else in — including
`docs/pipeline-wide-field-untracked.md`, the validated chain this data class
runs. That is the whole briefing; the repo carries the rest.

`sessions/aug06/` holds raw frames only: four light sets + a darks group
(expected from the source inventory: set-00 141, set-01 502, set-02 500,
set-03 500 lights + 328 darks — VERIFY the staged counts yourself). Same
target, camera and settings as the validated july31 corpus (Z6III,
24-70 @ 70 mm, 2.5 s, ISO 1600) per the acquisition plan — the solves verify
the field; report if it does not overlap july31's instead of assuming.

## Goals, in order

1. **Every aug06 set through the chain to judged products** — the walkthrough's
   route exactly: measure → ONE readiness report → the single approval → build
   → judge surfaces. The chain derives everything derivable (mount, route,
   cull, groups); baselines seed only after the user accepts the products.

2. **The combine is the point.** After the per-set products, compose across
   BOTH sessions: july31's retained sub-stacks
   (`sessions/july31/work/groups_*/`) plus aug06's. Verify what
   `run_undistort_compose.sh` actually supports for a cross-session member
   list before assuming it composes one — and the cross-set record home is a
   known gap (BACKLOG:`cross-set-record-home`): a session-spanning product's
   records must not be filed under a member set; degrade loudly and report
   rather than inventing a location silently.

3. **The framing question is PRE-REGISTERED, not assumed.** Hypothesis: a
   combine restricted to full-depth (~500-frame) sets may keep a larger
   fully-covered canvas — "the full scope of the frame" — than one including
   the short sets (aug06/set-00 at ~141, july31/set-04 at 260), because a
   member's drift span sets what it can cover. TEST it with the framing
   instrument: `scripts/qa/coverage_probe.sh` per-pixel coverage on at least
   two candidate member lists — [all sub-stacks] vs [500-frame sets only] —
   and report the measured canvas-vs-depth trade-off (fully-covered area,
   member count, effective frames) side by side. The CHOICE between area and
   depth is the user's; your job is the measured options in front of them,
   per the evidence gate.

Work the way the contract says: the tools measure, the chain routes what the
data settles, you stop only where a decision is genuinely the user's, and
every result is reported as measured — WIN, clean NULL, or needs-eyes, with
its instrument and numbers. Nothing is "fixed" or "final" until measured;
aesthetics are the user's eyes on full-frame lossless finals. Report what you
measured, what you chose, what you rejected, and anything you could not
explain.
