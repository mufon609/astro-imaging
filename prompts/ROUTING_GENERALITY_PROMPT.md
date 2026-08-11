# Fresh-session prompt — single-source the route key on a measured quantity

**Do not take this document's word for anything.** Every claim below is
checkable in the repo; check it. Read `CLAUDE.md` first (it is the briefing and
the read order), then `docs/dead-ends.md`, then `BACKLOG.md`
`routing-generality` and `route-recommendation`, then `git log` for the
fingerprint/routing arc.

---

## The defect, stated so you can attack it

The pipeline is supposed to pinpoint measured facts in the data and make the
right routing call for ANY rig — the same code correct for OSC raws on an
untracked tripod AND for a mono, tracked, long-exposure set with real flats.
Instead the route key `fov >= 10` is hard-coded at SIX sites, single-sourced
nowhere (verified live before this prompt was written):

    scripts/lib/fingerprint.py:245        (_label width band)
    scripts/lib/fingerprint.py:291        (the route branch)
    scripts/stack/run_set_chain.sh:165    (initial route decision)
    scripts/stack/run_set_chain.sh:504    (post-preflight re-derivation)
    scripts/qa/readiness_report.py:183    (readiness evaluator)
    web/serve.py:1712                     (the web rail's set position)

Re-grep before you touch anything: `grep -rniE "fov[^0-9]*>= *10" scripts/ web/`.
This is the exact defect class `disk_budget.sh` was created to kill (two
builders carried private copies of one constant and diverged 2x; routing on a
private copy once sent a set to a builder that refused it) — and it is
spreading: two of the six sites grew AFTER the item was registered.

**The key is also physically wrong, not just multiplied.** The undistort route
exists because the real frame-to-frame map of a drifting field is
`distort ∘ H ∘ distort⁻¹` — unmodelled lens distortion smears registration in
proportion to how far the sky DRIFTS across the sensor, not to how wide the
field is. A fixed tripod at 200 mm has a small field and LARGE drift: today it
exits 5 as unroutable despite being the same class with MORE drift. The
physically correct key is measured `drift_px`, which `fingerprint.py` ALREADY
computes (`drift_px`, `drift_px_per_min`, plus the sidereal expectation
`sidereal_drift_px_per_min`) — the route never consumes it.

## Step 1 — derive the key from the mechanism, and record why

Do not swap one magic constant for another. State the quantity and threshold
FROM the registry's own measurements, in the file that becomes the single
source. Anchors on record (`docs/dead-ends.md`):

- the class was established on a 43-min / ~1500 px-drift set, and a 9-min
  / ~310 px window STILL measured better whole-frame than the full span — so
  even ~300 px of drift is enough for the distortion term to bite;
- `drift_px` UNDER-COUNTS: total `-framing=min` trim runs 1.16–1.29x the pure
  translation in every measured set (field rotation + warp border) — a
  threshold derived from `drift_px` must state this;
- the corpus this repo has measured: 2.5–6 s subs drifting ~900–1500 px per
  set, all correctly on the undistort route.

Decide what the DATA cannot settle and leave it to the user (exit 5 remains
the honest stop for a genuinely undecidable fingerprint — the evidence gate,
`CLAUDE.md` "WHERE THE GATE ACTUALLY IS"). Everything an instrument answers
decisively, the router decides and records.

## Step 2 — single-source it

One definition, six consumers. `disk_budget.sh` is the repo's precedent for
the shape (a sourced/imported derivation shared by bash and python callers —
note `fingerprint.py` and `serve.py` import python, `run_set_chain.sh` shells
out; pick a mechanism that serves both without a private copy anywhere).
The fingerprint record should carry the derived route + the key's value and
provenance, so every downstream consumer can READ the decision rather than
re-deriving it — re-derivation at six sites is how this defect grew.

## Step 3 — the two refusals name their class

1. **Real flats staged on the undistort route → exit 6.** Doing acquisition
   RIGHT stops the one-click chain while the flatless path runs. Either wire
   the master-flat path for the undistort route, or make the stop name its
   class and the exact manual step that resolves it. Do not silently prefer
   the sky flat when real flats exist.
2. **A fixed + wide + FITS (dedicated-astrocam) set** routes to undistort,
   whose builders glob camera raws only, and dies with "no raw frames" — the
   right stop with the WRONG diagnosis. Make the refusal say what it actually
   found (FITS lights on a route whose builders take camera raws) and what the
   next step is.

"Handled" beats "named", but a named refusal that is accurate and actionable
is acceptable — record which you shipped and why.

## Acceptance — each of these is checked, not asserted

1. `grep -rniE "fov[^0-9]*>= *10" scripts/ web/` returns ONLY the single
   source (or nothing, if the key is drift-based with no fov clause left).
2. **The existing corpus routes identically.** All 12 real sets
   (july31 01–04, aug06 01–03, aug09 01–05) must derive `undistort-groups`
   before and after — verify with `run_session_chain.sh <session> --plan` per
   session (plan mode builds nothing) and diff the printed routes. Any change
   to an existing set's route is a FAILURE of this work, not a finding.
3. **The 200 mm case routes.** Construct a fingerprint-record fixture (fixed
   mount, fov ~2 deg, drift_px large) and show the router sends it to the
   undistort class instead of exit 5. Fixture discipline per
   `docs/dead-ends.md` ("a fixture's decoy must match the scanner's own
   pattern"): prove the fixture exercises the live branch, not a lookalike.
4. **The mono/tracked class still routes standard.** `datasets/colonnello-m20/`
   holds that class's RECORDS (frames are off-rig) — use them, or a fixture in
   their shape, to show `tracked` still derives the standard route.
5. **Fire test on the single source:** temporarily flip the threshold, show
   ALL consumers move together (`--plan` on one session + the readiness
   evaluator + the web model if cheap), restore, show they move back. A copy
   that did not move is the defect this work exists to kill.
6. **Both refusals demonstrated:** stage (or fixture) each class, show the
   refusal names it accurately with its next step.
7. `set-00` is never enumerated as a light set (owner convention: spare
   frames; the session chain already skips it — do not regress this).

## Rules

- Official tools do every pixel operation and measurement; this work is
  ROUTING ONLY — no builder behavior changes, no new thresholds on anything
  but the route key, and the key's provenance is recorded where it is defined.
- `pgrep -f run_set_chain; pgrep -f run_session_chain; pgrep -f
  run_undistort` BEFORE editing any chain script — editing a bash script with
  an invocation in flight executes garbage (registered trap, measured cost:
  one corrupted pilot build).
- One knob per experiment; a killed hypothesis goes to `docs/dead-ends.md`
  with its numbers.
- Comments are load-bearing constraint + numbers only — no chronology, no
  session narrative (owner rule; the registry's no-narrative entry).
- When the work is DONE: remove `routing-generality` from `BACKLOG.md`
  entirely (history lives in git), update `route-recommendation` if its
  remaining bullets moved, add any new divergence to the removal-conditions
  register IN THE SAME COMMIT, and retire THIS prompt file (`git rm
  prompts/ROUTING_GENERALITY_PROMPT.md`) — recovery is by commit.
- Do not `git push` unless asked. Do not delete raw frames.

## Deliverable

A cited `.md` at the repo root: the mechanism-derived key with its rationale
and numbers, the single-source design, the 12-set before/after route table,
the fixture results for the 200 mm and mono/tracked classes, both refusal
demonstrations, the fire-test transcript, and every file changed with its
commit. If the drift-keyed route CANNOT be made safe for the existing corpus,
that is the most valuable result available — report it plainly with the
numbers and leave the fov key in place, single-sourced.
