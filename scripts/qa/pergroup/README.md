# Per-group flat-window experiment — the drivers, verbatim

The five scripts that produced `pergroup_flat_window_july31_set03`
(`datasets/july31/experiments.jsonl`). They are kept as the RECORD OF WHAT RAN,
not as reusable tooling: paths and the target set are hardcoded, because they are
one-off orchestration for one measurement. The reusable parts are the shipped
instruments they call — `build_sky_flat.sh --select=`,
`run_undistort_pipeline.sh --regdata= --nonorm`, `flat_odd_component.py`,
`grid_ramp.py`, `flat_differential.py`, `pergroup_flat_report.py`.

Run order:

1. `build_flats.sh`   — five per-group flats from the standing route's own
   `gN.list`, plus the two interleaved 50+50 half-flats that measure the build
   FLOOR at the group's own depth (control 1).
2. `measure_flats.sh` — every group flat against the per-set flat, the
   extreme-group contrast, and the floor pair, with both instruments.
3. `build_arms.sh`    — the 19 arms. Per group: A (per-set flat, writes the
   registration data), B (that group's own flat, handed A's), I (per-set flat
   again through B's slot — control 2). Then on group 1: the planted ramp card
   (control 3), the uniform card (control 4), and the production-normalization
   pair.
4. `compose_arms.sh`  — one compose per arm with the COMPOSE registration pinned
   across arms too, which the shipped groups driver has no flag for and which
   this measurement cannot do without. Keeps the registered members.
5. `measure_arms.sh`  — the delivered difference at member and composed level,
   the controls, each flat ratio cropped to its member's own delivered canvas,
   and the per-member background ramp in both arms.

Two things in here are load-bearing and easy to lose in a re-run:

- **Registration is pinned at BOTH levels.** `register -2pass` re-chooses its
  reference from image quality and the calibration changes that choice, so
  without pinning the reference is a second knob — at the member level AND again
  at the compose, whose five inputs differ between arms by construction.
- **The comparison window is `set / group`, not `group / set`.** A member is
  `light / flat`, so the delivered ratio armB/armA is `flat_A / flat_B`. Building
  the window the other way pairs the right magnitude with the wrong sign and
  reads as a total failure of transfer.
