# Lunar / planetary registration

Part of the dead-end registry — `docs/dead-ends.md` is the index, and
`00-registry-contract.md` governs how entries are read, cited, written and
deleted. Entries are maintained IN PLACE (pre-compression forms are in git;
the pre-split single-file registry is `docs/dead-ends.md`'s own history).
Cross-references to sibling files are written as (`<file>.md`) pointers.

<!-- registry content below; docs/dead-ends.md is the index -->
- **Siril planetary registrations (Image Pattern Alignment AND KOMBAT)
  fail — quietly producing garbage shifts — when the drawn selection does
  not CONTAIN THE TARGET'S WHOLE MOVEMENT across the sequence** (the
  official docs state the precondition; a drifting target that exits the box
  leaves the matcher with noise, and nothing fails loudly). MEASURED (~110
  px disc, 230/665 px untracked drift, selection ~250 px = smaller than the
  track): tail-frame shifts (41,10)/(50,20) where the physical drift demands
  ≈(10,185); 809 frames "registered" in 984 ms (~1 ms/frame — no real
  per-frame work) vs 220 frames in 23.5 s; every regdata quality field −1 →
  `stack -filter-quality=25%` computed threshold 0.000000 and filtered in
  ZERO frames; the applied-registration control stack rejected the
  misaligned disc to a faint smudge. THE RULE: size the selection to the
  full drift track (a staging crop that already bounds the track makes
  "nearly the whole frame" the correct selection) — and after registering,
  verify per-frame quality was actually WRITTEN (regdata ≠ −1) before any
  quality-filtered stack. **KOMBAT specifically is DEAD on this rig's 1.4.4
  for this corpus** — four configurations measured, including the
  mechanically correct template-matching pairing: every run left 219/220
  frames with a NULL H and quality −1, failing silently in the GUI. The
  surviving in-Siril candidate is Image Pattern Alignment with a
  track-covering selection; the cross-tool route is PSS.
- **Siril 1.4.4 planetary registrations write NO per-frame quality — even on
  a VERIFIED-successful run — so a `-filter-quality` stack has nothing to
  consume.** Measured end-to-end: Image Pattern Alignment with a
  track-covering selection produced physically-correct translations (tail
  (10,187–190) vs predicted ≈(10,185); limb coherent on the control stack)
  yet every regdata quality field stayed −1 and `-filter-quality=25%` still
  filtered in 0. The stacking docs' "quality (planetary DFT or Kombat)"
  filter criterion is a dead letter in 1.4.4. Quality-ranked ("lucky") frame
  selection therefore needs a RANKING tool (PSS `--stack_percent`, AS!4), or
  Siril 1.5's MPP if it measures quality — verify before designing on it.
- **Failed Siril GUI registration attempts leave the sequence's SELECTION
  state corrupted — silently.** After repeated failed planetary
  registrations the `.seq` held frames 2–220 deselected with
  nb_selected = −218 (a counter driven negative), making a later
  `seqapplyreg` abort with "registration data is a set of null matrices"
  even though the layer held valid transforms — the failure surfaces one
  step downstream, mislabeled. Repair is scriptable (`select <seq> 1 <N>`
  before applying), or take the safe reset: DELETE the `.seq` and let the
  next sequence search rebuild it clean. After ANY failed GUI registration,
  inspect the `.seq` header before trusting the next step's error.
- **Planetary DFT registration ALIASES shifts beyond ±half its correlation
  window — and stacks a SECOND coherent disc exactly one window away.**
  Circular (FFT) correlation resolves translation only within ±window/2; a
  target whose drift from the REFERENCE exceeds that wraps modulo the
  window, silently. MEASURED (1024×1536 crop, 809 frames, reference at one
  end of a ~670 px monotonic track): frames with true shift ≤ +379
  registered exactly; the tail's true +670 was recorded as −355 = 670 −
  1024 (the frame's SHORT dimension — the effective window), and the stack
  rendered TWO clean discs ~1024 px apart, REPRODUCED identically on a
  clean rebuilt sequence — the method's arithmetic, not stale state. THE
  RULE: put the REFERENCE near the TRACK MIDDLE (`setref` before
  registering) so max |shift| < window/2, and verify tail shifts against
  the physical drift after EVERY planetary registration
  (predicted-vs-regdata is a 10-second check). Stack verification is
  WHOLE-FRAME first, zoom second — a limb/zoom coherence check on ONE
  region cannot see a second disc (trap 1 of the comparison-traps entry,
  `registration-distortion.md`, in new clothing). Keep all frames (dropping
  a minority sub-focal subset buys no matching gain and pays the full √N
  noise penalty).
