# Registry contract — evidence classes, subject axis, write/delete rules

Phase-1 split of `docs/dead-ends.md` (organize-only; the original file stays
the live registry until the merge is decided). Content below the marker is
VERBATIM from the original, so in-text "above"/"below"/section references may
point at entries now homed in a sibling file — `README.md` in this directory
carries the index, the assignment rule, and the block manifest that resolves
them. Do not edit below the marker while the refactor is in phase 1; the split
is re-derivable from the manifest and verified byte-identical by `split.py`.

<!-- == verbatim content from docs/dead-ends.md below this marker == -->
# Dead-end registry + acquisition checklist

Durable, arch-independent field lessons: the processing dead-ends never to
re-attempt (each with its mechanism), and the acquisition choices that outrank
any processing knob. **Read the dead-end registry before proposing ANY
experiment** — if a thing does not work, the mechanism why is here. Full detail
+ the original numbers live in git history (the NOTES at the commit whose message
begins `checkpoint:` — `git log --oneline --grep='^checkpoint:'`).

## Dead-end registry — do NOT re-attempt

Data / physics / tool-doctrine mechanism lessons.

**EVIDENCE STATUS — read this before citing any entry as settled.** Entries here
are not all the same kind of thing. Three classes:
- **MEASURED** — an actual controlled comparison with numbers and a named
  instrument. Cite freely, within its stated scope.
- **MECHANISM** — a physical or tool-behaviour argument, sometimes with a
  worked example, but no controlled A/B on this data. Reasonable to act on;
  NOT evidence, and it should not be quoted as a result.
- **DOCTRINE** — a practice adopted from vendor documentation or the field's
  consensus. Legitimate, but its authority is the source, not our data.
An entry with no numbers and no hedge is MECHANISM or DOCTRINE, whatever its
tone; the load-bearing ones are flagged in place. **Anything asserting a
result should carry its n, its instrument and its scope — and if a claim covers
one dataset, it says so.**
**AND ITS SUBJECT, WHICH IS A FOURTH AXIS AND WAS MISSING: name the thing the
instrument was pointed AT, and confirm the headline names that same thing.**
MEASURED that the other three do not reach it — three entries drifted from the
subject they measured to an adjacent one while carrying n, instrument and scope
correctly, so **enforcing this rule as it previously stood passes every one of
them** (the pattern entry under "QA / scope"). **SCOPE is the near-miss that hides
the gap:** scope answers *how widely does this apply* — one dataset, one night,
one rig — and subject answers *what was measured*. They read as the same question
and are not, which is why compliance on one masked drift on the other.

**STANDARDS-FIRST — SUBJECT IS THE MEASURAND, and the term is not ours.** JCGM 200
(VIM, = ISO/IEC Guide 99) defines the **measurand** as *"the quantity intended to
be measured"* — wording changed in the 3rd edition from *"quantity subject to
measurement"* precisely to put INTENTION above apparatus. VIM's core distinction is
the one the three instances re-derived from scratch: **the quantity actually
measured may differ from the measurand as defined, and where it does, a correction
is required.** Adopt the TERM. **DEVIATION, recorded with its reason as
`CLAUDE.md` requires:** the axes deliberately re-derive W3C PROV's
Entity/Activity triple in PROSE, because this registry is read by people and not
parsers — and the IVOA Provenance Data Model is NOT adopted, a machine-readable
serialisation being the wrong instrument for a document whose failure mode is text
nobody re-reads. **`n` is in neither standard and is a local statistical addition.**
**PRECISION NOTE, tagged MECHANISM because it is the attackable part:** the VIM
CONCEPT transfers exactly, its illustrated mechanism does NOT — VIM's examples are
the measurement perturbing the system (a voltmeter loading the battery it reads),
whereas ours is the CLAIM drifting to an adjacent subject while the measurement
stays put. Two instances of one distinction, not one failure. (Citation and split:
the Oracle's.)

**THE POSITIVE CONTROL ON THIS AXIS — RUN BACKWARDS OVER THE THREE INSTANCES, AND
IT CATCHES 2 OF 3. The miss is the useful half and it bounds the axis.** Every
acceptance measure ships with data on which it MUST fire (`CLAUDE.md`); an axis is
no exception, so the three entries that defeated n+instrument+scope were re-read
against SUBJECT:
- **operation → command** (*"`register -disto=` IS NOT PER-IMAGE REPROJECTION"*,
  measured on a standalone SIP warp performed OUTSIDE siril's registration) —
  **CAUGHT.** The measurement never invoked the command, so the mismatch survives
  at any granularity of naming.
- **command → design** (*"Siril's own design assumes ONE optical state per
  sequence"*, from a `-disto=` measurement) — **CAUGHT.** One command against a
  whole tool's design is a mismatch of KIND.
- **flag → tool** (*"Siril `-weight` is a min-max ramp"*, true of `wfwhm`/`nbstars`
  and FALSE of `noise`) — **MISSED.** An author names the subject `-weight`; the
  headline says `-weight`; the axis compares them and finds a match. **The widening
  is INSIDE the named subject, not across it.**
**SO THE BOUND: this axis catches drift ACROSS a subject boundary and is BLIND to
drift WITHIN one**, because it never says at what GRANULARITY the subject must be
named, and a reader has no prompt to choose one finer than the claim. **The missing
half is a separate discipline — enumerate the subject's own modes or values before
asserting a behaviour OF it**, which is exactly what closed `-disto=` (three values,
`master` UNDETERMINED) and what nobody has yet done for `-weight`.

**RECORDING RATE — OWNER-RATIFIED, AND SCOPED TO THIS REGISTRY ONLY. A finding
earns an entry here only if it would change a future decision; everything else
lives in the commit message.** MEASURED, since 00:00 on 2026-08-14: this file ran
**+1,139 / −59, net +1,080** (2,740 → 3,820 lines) while `BACKLOG.md` ran
**+1,216 / −1,530, net −314** across **six** net-negative commits (largest
`2657a3c` −413, then `0ecf111` −286). **The queue sheds and the registry does
not.** **CARRY THE RISK RATHER THAN PRETENDING IT AWAY: this registry's value has
repeatedly been an entry nobody expected to fire** — so the test is *would it
change a decision*, never *is it interesting*, and a rate rule is a budget on
WRITING, never a licence to delete what is already here.

**AND THE OTHER HALF OF THAT RULE IS NOW WRITTEN DOWN — OWNER-RATIFIED 2026-08-16.
THIS REGISTRY IS NOT APPEND-ONLY. AN ENTRY IS DELETED WHEN THE TEST IT DOCUMENTS IS
SOLVED AND THE TEST NO LONGER HAS VALUE.** The queue has always had this half
written down and the registry never did, which is the whole reason this file has
only ever grown. The two rules are siblings: the recording rate governs what may be
WRITTEN, and this governs what may be REMOVED.
**Read the condition as the conjunction it is.** Solved is not sufficient on its
own — a solved problem whose entry still stops someone re-attempting the route
retains its value and stays; that is what most of this file is. What goes is an
entry whose test is both settled AND no longer worth anyone's time to know about.
**It is not a licence to compress, reorganise or shorten** — the sentence above
about a rate rule never licensing deletion stands untouched, and this is a
different operation on a different trigger.

**FOUR WAYS AN ENTRY'S STANDING DIFFERS FROM WHAT THE ENTRY APPEARS TO SAY.**
"Settled" is not among them — it is the null hypothesis every entry is read under,
and naming it changes no decision, so it is deliberately not a fifth state. Each of
these four does change one, and each earned its place by having already happened
here:
- **ABANDONED CLEANLY** — the non-attribution was PRE-DECLARED, before the run and
  before the outcome was known, then honoured. *Changes:* re-running the same data
  is worthless; only a new DESIGN reopens it. Without the label, an open
  unattributed question invites a retry. (`21653a1`'s CFA arm — *"this arm cannot
  separate them and will not attribute"* — delivered exactly as declared.)
- **UNREPRODUCIBLE BY CONSTRUCTION** — the numbers live only in prose, or the
  subject no longer exists. *Changes:* a "re-measurement" is a FIRST measurement and
  nothing can be diffed against the old figures. (`compose-homography-smear`'s 19
  marched columns: in no tracked file, and their product deleted.)
- **SILENTLY REVERSED** — a conclusion overturned with no record that anything was
  being overturned. *Changes:* everything downstream of the reversal is suspect and
  the reversal itself is the thing to audit. **The expensive one** — it retired a
  measured, adopted, OWNER-PASSED compose route on a help-text reading, four days
  after that route shipped.
- **MOOTED** — the claim is still TRUE and its subject turned out not to exist.
  *Changes:* it is invisible to every check keyed on truth, so no re-verification
  pass will surface it and only a reader tracing the SUBJECT will. **The quietest**,
  because nothing about the sentence ever becomes false. (*"lensfun cannot represent
  decentring on this rig"* — true, and the joint refit then put the centre at
  (−6, +14) px.)
**All four are properties of the RECORD and not of the instrument, so no guard
reaches any of them** — they are found only by reading an entry against the artifact
it describes.

