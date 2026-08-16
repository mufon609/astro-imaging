# Per-group flat-window experiment — the drivers, verbatim

The five scripts that produced `pergroup_flat_window_july31_set03`
(`datasets/july31/experiments.jsonl`). They are kept as the RECORD OF WHAT RAN,
not as reusable tooling: **the TARGET SET is hardcoded** (`july31`, `set-03`,
`groups_set-03`, `skyflat_set-03`), because they are one-off orchestration for one
measurement.

**The REPO PATH is NOT hardcoded, and this sentence used to say it was.** All five
derived `REPO` from an absolute `/home/samsung/…` literal that existed on exactly
one machine; they now derive it from their own location
(`$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)`, three levels because
this directory is three deep), which is what the other 30 scripts under `scripts/`
already do. **The change is behaviour-preserving on the rig that produced the
measurement** — the derived value is byte-identical to the literal it replaced —
so these are still the record of what ran, and a clone at any path can now read
and run them without editing five files first. The reusable parts are the shipped
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

## Which grid record is which — a naming trap, measured

`measure_flats.sh` writes TWO grid records per pair and the names invite the
wrong pairing (an auditor mis-paired them twice on the first read-through):

- `grid_<pair>.json`     — the **9x7 = 63-box** geometry, passed EXPLICITLY as
  `--nx=9 --ny=7`. Non-default. This is the registry's own geometry, used
  wherever a number is compared against a registry number.
- `gridfull_<pair>.json` — the **11x7 = 77-box** frame-filling geometry, which is
  `grid_ramp.py`'s DEFAULT (it fits as many boxes as the frame takes, spanning
  5700 of 6064 px against 63-box's 4600). Better lever, not comparable with the
  inherited figures.

So the plainly-named file is the non-default one. Every record is
self-describing — `measured.geometry_px` carries `nx`/`ny` — so read that rather
than the filename when it matters.
