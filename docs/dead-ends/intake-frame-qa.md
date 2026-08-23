# Intake — frame QA, culling, drift/mount instruments

Phase-2 file of the dead-ends registry split (`README.md` here holds the index
and dispositions; pre-compression forms live in git and in the live
`docs/dead-ends.md` until the merge).

<!-- phase-2: maintained in place; not regenerated from the manifest -->
- Frame QA + registration run on DEBAYERED data only — CFA-lattice
  registration false-positives on cloud texture (adjacent cloud frames
  cross-match → a cloud reference).
- **A TWO-WINDOW DRIFT INSTRUMENT MUST CONFINE BOTH WINDOWS TO ONE CONTIGUOUS
  CAPTURE RUN — dir-endpoint windows measure re-aim + drift, a rate that is
  neither mount signature.** A re-aim can only occur ACROSS a capture-run
  boundary (within a run the interval timer leaves no time to recompose), so
  first/last-of-dir on a dir holding a stray pre-burst frame straddles the
  re-aim. MEASURED (140-frame dir: 1 aim frame, a 661 s pause carrying a
  0.373°-RA re-aim, then a contiguous 139-frame burst at 3.0 s cadence):
  first/last read RA rate 6.9751°/hr — 0.46× sidereal, neither fixed nor
  tracked, a spurious mount-underivable stop on a rigid tripod — while the
  run-confined window on the same dir read 14.8724°/hr = 0.99× sidereal, a
  clean fixed signature. Generalizes to ANY rate derived from dir-endpoint
  epochs (cadence, drift px/min). `mount_probe.sh` windows inside the
  longest run (the audit's own `segment_runs` boundary logic, not a
  re-derivation) and records the window facts in `mount_probe.json`; a dir
  with no readable epochs segments to ONE run = endpoint behavior.
  Corollary: a stray aim frame also EXTENDS the `-framing=min` trim (the
  canvas is sized by TIME SPAN — `stacking-compose.md`, the framing entry),
  so it is a cull candidate on canvas grounds independent of its optical
  quality (~58 px of width against 1/140 of depth here).
- Cloud culling is by per-pixel MAJORITY risk, not visibility: a moving
  minority band stacks clean through `rej 3 3`; a DWELLING band becomes the
  per-pixel majority and survives. `nstars` is a blind cloud discriminant on
  rich fields (detection saturates at the star cap — the background channel
  carries the cloud signal).
