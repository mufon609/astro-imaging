# Intake — frame QA, culling, drift/mount instruments

Phase-1 split of `docs/dead-ends.md` (organize-only; the original file stays
the live registry until the merge is decided). Content below the marker is
VERBATIM from the original, so in-text "above"/"below"/section references may
point at entries now homed in a sibling file — `README.md` in this directory
carries the index, the assignment rule, and the block manifest that resolves
them. Do not edit below the marker while the refactor is in phase 1; the split
is re-derivable from the manifest and verified byte-identical by `split.py`.

<!-- == verbatim content from docs/dead-ends.md below this marker == -->
**Detection / solve / registration:**
- Frame QA + registration run on DEBAYERED data only — CFA-lattice registration
  false-positives on cloud texture (adjacent cloud frames cross-match → a cloud
  reference).
- **A TWO-WINDOW DRIFT INSTRUMENT MUST CONFINE BOTH WINDOWS TO ONE CONTIGUOUS
  CAPTURE RUN — dir-endpoint windows measure re-aim + drift, a rate that is
  neither mount signature.** A re-aim can only occur ACROSS a capture-run
  boundary (the audit's segment_runs law: within a run the interval timer
  leaves no time to recompose), so first/last-of-dir on a dir holding a stray
  pre-burst frame straddles the re-aim. MEASURED (140-frame dir: 1 aim frame,
  a 661 s pause carrying a 0.373 deg-RA re-aim (981 arcsec sky-projected), then a contiguous 139-frame burst
  at 3.0 s cadence): first/last read RA rate 6.9751 deg/hr — 0.46x sidereal,
  neither fixed nor tracked, a spurious mount-underivable stop on a rigid
  tripod — while the run-confined window on the same dir read 14.8724 deg/hr
  = 0.99x sidereal, a clean fixed signature (dec drift −19.4 arcsec over
  414 s). Generalizes to ANY rate derived from dir-endpoint epochs (cadence,
  drift px/min). `mount_probe.sh` windows inside the longest run
  (acquisition.timeline + segment_runs — the audit's own boundary logic, not
  a re-derivation) and records the window facts in `mount_probe.json`; a dir
  with no readable epochs/frame numbers segments to ONE run = endpoint
  behavior. Corollary: a stray aim frame also EXTENDS the `-framing=min` trim
  (the canvas is sized by TIME SPAN — framing entry above), so it is a cull
  candidate on canvas grounds independent of its optical quality (~58 px of
  width against 1/140 of depth here).
- Cloud culling is by per-pixel MAJORITY risk, not visibility: a moving minority
  band stacks clean through `rej 3 3`; a DWELLING band becomes the per-pixel
  majority and survives. `nstars` is a blind cloud discriminant on rich fields
  (detection saturates at the star cap — the background channel carries the cloud
  signal).
