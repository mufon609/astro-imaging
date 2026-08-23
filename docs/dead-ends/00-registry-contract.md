# Registry contract — evidence classes, subject axis, write/delete rules

Part of the dead-end registry — `docs/dead-ends.md` is the index. This file
governs how every entry in this directory is read, cited, written and
deleted. Entries are maintained IN PLACE (pre-compression forms are in git;
the pre-split single-file registry is `docs/dead-ends.md`'s own history).

<!-- registry content below; docs/dead-ends.md is the index -->
Durable, arch-independent field lessons: the processing dead-ends never to
re-attempt (each with its mechanism), and the acquisition choices that outrank
any processing knob. **Read the registry before proposing ANY experiment** —
if a thing does not work, the mechanism why is here. Full detail + the
original numbers live in git history (the NOTES at the commit whose message
begins `checkpoint:` — `git log --oneline --grep='^checkpoint:'`).

**EVIDENCE STATUS — read this before citing any entry as settled.** Entries
are not all the same kind of thing. Three classes:
- **MEASURED** — an actual controlled comparison with numbers and a named
  instrument. Cite freely, within its stated scope.
- **MECHANISM** — a physical or tool-behaviour argument, sometimes with a
  worked example, but no controlled A/B on this data. Reasonable to act on;
  NOT evidence, and it should not be quoted as a result.
- **DOCTRINE** — a practice adopted from vendor documentation or the field's
  consensus. Legitimate, but its authority is the source, not our data.
An entry with no numbers and no hedge is MECHANISM or DOCTRINE, whatever its
tone. **Anything asserting a result carries its n, its instrument and its
scope — and if a claim covers one dataset, it says so.**

**AND ITS SUBJECT, A FOURTH AXIS: name the thing the instrument was pointed
AT, and confirm the headline names that same thing.** MEASURED that the other
three axes do not reach it — three entries drifted from the subject they
measured to an adjacent one while carrying n, instrument and scope correctly,
so enforcing the rule as it previously stood passes every one of them.
**SCOPE is the near-miss that hides the gap:** scope answers *how widely does
this apply*; subject answers *what was measured*. They read as the same
question and are not.
**STANDARDS-FIRST — SUBJECT IS THE MEASURAND, and the term is not ours.**
JCGM 200 (VIM, = ISO/IEC Guide 99) defines the **measurand** as *"the
quantity intended to be measured"* — wording changed in the 3rd edition
precisely to put INTENTION above apparatus, and VIM's core distinction is the
one re-derived here: the quantity actually measured may differ from the
measurand as defined, and where it does, a correction is required. Adopt the
TERM. **Deviation, recorded with its reason:** the axes re-derive W3C PROV's
Entity/Activity triple in PROSE, because this registry is read by people, not
parsers; the IVOA Provenance Data Model is NOT adopted — a machine-readable
serialisation is the wrong instrument for a document whose failure mode is
text nobody re-reads. `n` is in neither standard and is a local statistical
addition. PRECISION NOTE, tagged MECHANISM: the VIM concept transfers
exactly, its illustrated mechanism does not — VIM's examples are the
measurement perturbing the system; ours is the CLAIM drifting to an adjacent
subject while the measurement stays put.
**THE POSITIVE CONTROL ON THIS AXIS — run backwards over the three instances,
it catches 2 of 3, and the miss bounds the axis:**
- **operation → command** (*"`register -disto=` IS NOT PER-IMAGE
  REPROJECTION"*, measured on a standalone SIP warp performed OUTSIDE siril's
  registration) — **CAUGHT**: the measurement never invoked the command.
- **command → design** (*"Siril's own design assumes ONE optical state per
  sequence"*, from a `-disto=` measurement) — **CAUGHT**: one command against
  a whole tool's design is a mismatch of KIND.
- **flag → tool** (*"Siril `-weight` is a min-max ramp"*, true of
  `wfwhm`/`nbstars` and FALSE of `noise`) — **MISSED**: the headline names
  the subject `-weight` and the axis finds a match. **The widening is INSIDE
  the named subject, not across it.**
**SO THE BOUND: this axis catches drift ACROSS a subject boundary and is
BLIND to drift WITHIN one**, because it never says at what GRANULARITY the
subject must be named. The missing half is a separate discipline — enumerate
the subject's own modes or values before asserting a behaviour OF it — which
is what closed `-disto=` (three values, `master` UNDETERMINED) and what the
`-weight` scoping (`stacking-compose.md`) applied after the fact.

**RECORDING RATE — OWNER-RATIFIED, AND SCOPED TO THIS REGISTRY ONLY. A
finding earns an entry here only if it would change a future decision;
everything else lives in the commit message.** MEASURED: across one two-day
span this registry grew net +1,080 lines while `BACKLOG.md` shed net −314 —
the queue sheds and the registry did not. **Carry the risk rather than
pretending it away: this registry's value has repeatedly been an entry nobody
expected to fire** — so the test is *would it change a decision*, never *is
it interesting*, and a rate rule is a budget on WRITING, never a licence to
delete what is already here.

**AND THE OTHER HALF — OWNER-RATIFIED 2026-08-16. THIS REGISTRY IS NOT
APPEND-ONLY. AN ENTRY IS DELETED WHEN THE TEST IT DOCUMENTS IS SOLVED AND THE
TEST NO LONGER HAS VALUE.** The two rules are siblings: the recording rate
governs what may be WRITTEN, this governs what may be REMOVED.
**Read the condition as the conjunction it is.** Solved is not sufficient on
its own — a solved problem whose entry still stops someone re-attempting the
route retains its value and stays; that is what most of this registry is.
What goes is an entry whose test is both settled AND no longer worth
anyone's time to know about. **It is not a licence to compress, reorganise
or shorten** — that is a different operation on a different trigger.

**FOUR WAYS AN ENTRY'S STANDING DIFFERS FROM WHAT THE ENTRY APPEARS TO SAY.**
"Settled" is not among them — it is the null hypothesis every entry is read
under. Each of these four changes a decision, and each has already happened
here:
- **ABANDONED CLEANLY** — the non-attribution was PRE-DECLARED, before the
  run, then honoured. *Changes:* re-running the same data is worthless; only
  a new DESIGN reopens it. Without the label, an open unattributed question
  invites a retry.
- **UNREPRODUCIBLE BY CONSTRUCTION** — the numbers live only in prose, or the
  subject no longer exists. *Changes:* a "re-measurement" is a FIRST
  measurement; nothing can be diffed against the old figures.
- **SILENTLY REVERSED** — a conclusion overturned with no record that
  anything was being overturned. *Changes:* everything downstream of the
  reversal is suspect and the reversal itself is the thing to audit. **The
  expensive one** — it retired a measured, adopted, owner-passed compose
  route on a help-text reading, four days after that route shipped.
- **MOOTED** — the claim is still TRUE and its subject turned out not to
  exist. *Changes:* it is invisible to every check keyed on truth; only a
  reader tracing the SUBJECT finds it. **The quietest**, because nothing
  about the sentence ever becomes false.
**All four are properties of the RECORD and not of the instrument, so no
guard reaches any of them** — they are found only by reading an entry against
the artifact it describes.
