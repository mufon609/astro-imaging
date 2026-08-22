# Lunar / planetary registration

Phase-1 split of `docs/dead-ends.md` (organize-only; the original file stays
the live registry until the merge is decided). Content below the marker is
VERBATIM from the original, so in-text "above"/"below"/section references may
point at entries now homed in a sibling file — `README.md` in this directory
carries the index, the assignment rule, and the block manifest that resolves
them. Do not edit below the marker while the refactor is in phase 1; the split
is re-derivable from the manifest and verified byte-identical by `split.py`.

<!-- == verbatim content from docs/dead-ends.md below this marker == -->
- **Siril planetary registrations (Image Pattern Alignment AND KOMBAT) fail — quietly
  producing garbage shifts — when the drawn selection does not CONTAIN THE TARGET'S
  WHOLE MOVEMENT across the sequence** (the official docs state the precondition; a
  drifting target that exits the box leaves the correlation/template matcher with
  noise, and nothing fails loudly). MEASURED (july26 lunar, ~110 px disc, 230/665 px
  untracked drift, selection ~250 px = smaller than the track): tail-frame shifts
  (41,10)/(50,20) where the physical drift demands ≈(10,185); 809 frames "registered"
  in 984 ms (~1 ms/frame — no real per-frame work) vs 220 frames in 23.5 s; every
  regdata quality field −1 → `stack -filter-quality=25%` computed threshold 0.000000
  and filtered in ZERO frames; the applied-registration control stack rejected the
  misaligned disc to a faint smudge (winsorized 3/3 — the per-pixel disc minority
  rejected as outlier). THE RULE: size the selection to the full drift track (a
  staging crop that already bounds the track makes "nearly the whole frame" the
  correct selection) — and after registering, verify per-frame quality was actually
  WRITTEN (regdata ≠ −1) before any quality-filtered stack; the registration docs do
  not promise quality storage, only the stacking docs imply it.
  **KOMBAT specifically is DEAD on this rig's 1.4.4 for this corpus** — four
  configurations measured (tight template + default 25% area; whole-frame selection +
  100% area; tight template + 100% area — the mechanically correct template-matching
  pairing — twice): every run left 219/220 frames with a NULL H (no match) and
  quality −1, failing silently in the GUI. Do not re-attempt KOMBAT on 32-bit float
  3-channel crops of this class; the surviving in-Siril candidate is Image Pattern
  Alignment with a track-covering selection, and the cross-tool route is PSS.
- **Siril 1.4.4 planetary registrations write NO per-frame quality — even on a
  VERIFIED-successful run — so a `-filter-quality` stack has nothing to consume.**
  MEASURED end-to-end (july26 set-01): Image Pattern Alignment with a track-covering
  selection produced physically-correct translations (tail (10,187–190) vs predicted
  ≈(10,185); limb coherent on the applied-registration control stack) yet every
  regdata quality field stayed −1 and `stack -filter-quality=25%` still computed
  threshold 0.000000 / filtered-in 0. The stacking docs' "quality (planetary DFT or
  Kombat registrations)" filter criterion is a dead letter in 1.4.4. Quality-ranked
  ("lucky") frame selection therefore needs a RANKING tool (PSS `--stack_percent`,
  AS!4 — both x86-only), or Siril 1.5's MPP if it measures quality — verify before
  designing on it.
- **Failed Siril GUI registration attempts leave the sequence's SELECTION state
  corrupted — silently.** Symptom: after repeated failed planetary registrations the
  .seq held frames 2–220 deselected with nb_selected = −218 (a counter driven
  negative), making a later `seqapplyreg` abort with "registration data is a set of
  null matrices" even though layer R1 held valid transforms — the failure surfaces
  one step downstream, mislabeled. Repair is scriptable: `select <seq> 1 <N>` before
  applying; after ANY failed GUI registration, inspect the .seq header (S-line
  nb_selected + I-line flags) before trusting the next step's error — or take the
  safe reset: DELETE the .seq and let the next sequence search rebuild it clean
  (cheap, and it removes the selection debris).
- **Planetary DFT registration ALIASES shifts beyond ±half its correlation window —
  and stacks a SECOND coherent disc exactly one window away.** Circular (FFT)
  correlation resolves translation only within ±window/2; a target whose drift from
  the REFERENCE frame exceeds that wraps modulo the window, silently. MEASURED
  (july26 set-02, 1024×1536 crop, 809 frames, reference = frame 1 at one end of a
  ~670 px monotonic track): frames with true shift ≤ +379 registered exactly; the
  tail's true +670 was recorded as −355 = 670 − 1024 (the frame's SHORT dimension —
  the effective window), off by exactly one window; the stack rendered TWO clean
  discs ~1024 px apart (each wrap-class coherent at its own position), REPRODUCED
  identically on a clean rebuilt sequence — the method's arithmetic, not stale
  state. Set-01 (max shift 190 px) never hit it. THE RULE: put the REFERENCE near
  the TRACK MIDDLE (`setref` before registering) so max |shift| < window/2 —
  halving the reach requirement; verify tail shifts against the physical drift after
  EVERY planetary registration (predicted-vs-regdata is a 10-second check). Stack
  verification is WHOLE-FRAME first, zoom second — a limb/zoom coherence check on
  ONE region cannot see a second disc (the registry's trap-1 in new clothing). Keep
  all frames (dropping a minority sub-focal subset buys no matching gain and pays
  the full √N noise penalty).
