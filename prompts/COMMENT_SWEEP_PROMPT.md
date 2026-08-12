# Comment sweep — find and fix stale comment/record prose

**STANDING UTILITY — NON-RETIRING.** Unlike the one-shot briefs in this
directory, this file is not consumed by its run. Run it whenever wanted; leave
it in place afterwards.

## The policy (complete — you need no other context)

Comments and record entries are **high-value, load-bearing, technical**: the
constraint or mechanism with its measured numbers, present tense, detailed but
not long-winded, free of anything that ages. When and in what order lives in
git. A date is allowed only where the date IS the information — a doctrine
ratification stamp, or a last-checked stamp on a claim that goes stale (rig
inventory, tool version, measured-on-this-rig). Both are register data, not
narrative. (`CLAUDE.md`, binding rules — the one home; this file restates it
only so a sweep session can run standalone.)

## What a GOOD comment looks like (the repo's revealed preference)

The shape the history keeps and strengthens: **the constraint, why it exists,
the number that proves it, and the scope it holds at** — present tense, no
story. From `4d70455`, `scripts/calibrate/solve_field.py`:

    # The hint radius is the declared position uncertainty. Twice it is already
    # generous — every hinted solve in this corpus lands within 0.27 deg of a 15
    # deg hint (68 records replayed) — while the measured false solve sat ~110
    # deg out, 7x the radius. So this separates by two orders of magnitude and
    # is not a tuned number.

Note what earns its place: a number, its sample size, and an explicit claim
about what the number does NOT prove. **Length is not the target — staleness
is.** A long comment dense with measured constraint is correct; a short one
that will be false after the next tool bump is not.

## Categories, each with its detector

Counts are removed lines over 638 commits (in-place edits only, whole-file
retirements excluded), from the history mining that produced this file.

**Every grep below is line-based and this repo wraps its comments, so a phrase
split across two `#` lines is INVISIBLE to it.** Run each pattern a second time
over joined comment blocks — concatenate each run of consecutive comment lines,
strip the `#`, then match. That second pass is not optional: it found 7 hits the
line-based greps missed in one run, including `run_undistort_groups.sh`'s *"It
used / to be a bare `GROUP=15`"* and four dangling `BACKLOG item N` citations.

### 1. Drift — the prose asserts what the code contradicts (HIGHEST COST)

Not mechanically greppable; the only category that has recurred as *the same
error six times* (`e40c007` flagged three, `1f5fc6c` the fifth, `018ae54` the
sixth — all the ICC leg rule). It is also the only category that can actively
mislead a future session into rebuilding something discredited.

*Detector — semantic, run per claim:* for every comment or doc line that states
a tool flag, a default, a file path, or a pipeline contract, grep the shipped
script for that flag/path and confirm it still says so.

**Run the repo's own guards first — they are the authoritative drift detectors
for anything they cover**, and they print the true counts to compare prose
against:

    bash scripts/stack/check_bitdepth.sh
    bash scripts/stack/check_registration_pins.sh [--selftest]

That is how the exemption-count drift was caught: `check_bitdepth.sh` exempts
and reports **four** instruments while `README.md` and `BACKLOG.md`'s register
row both said *three*, the row omitting `run_lunar_pipeline.sh` entirely — a
number a reader would have trusted over the guard.

Examples:
- `1f5fc6c` — `docs/wide-field-untracked-registration.md` asserted
  `--icc-type SRGB, never LIN_REC709` while the shipped
  `run_undistort_pipeline.sh` strips the ICC tag and exports `LIN_REC709` on
  the float leg. The 16-bit-era rule was stated as the production contract.
- `e40c007` — `objective-qa-defect-metrics.md` ranked as priority #1
  *"Radial-profile undershoot ringing detector — reuses the existing radial
  profiles ... Cheapest high-value win."* There were no existing radial
  profiles: `star_shape_profile.py` was deleted in `e3864e8`, and it is
  **trap 3** in `docs/dead-ends.md` — a metric whose origin moved with the
  defect. A session following the doc would have rebuilt a discredited
  instrument as "the cheapest available win."

**Rule: REVISE, never delete.** Restate to what the code does now, and keep the
measured number. Deleting a drifted claim loses the constraint; correcting it
is the whole value of the sweep.

### 2. Date-stamped chronology — 10 code / 245 md

    grep -rnE '20[0-9]{2}-[0-9]{2}-[0-9]{2}' --include='*.py' --include='*.sh' --include='*.md' .

Verbatim removals:
- `7489069` — `# It shipped ON 2026-07-29 (f170540) and cost 31x in background flatness: july31/`
- `3ac041a` — `# Defaults = APPROVED RECIPE B6 (2026-07-06 session 5, user-approved:`

**Rule:** strip the date, keep the number. `cost 31x in background flatness`
is the information; `shipped ON 2026-07-29` is git's. **Do not strip** a
ratification stamp, a `MEASURED <date>` / `last checked <date>` stamp on a
claim that can go stale, or the dated **Context** line that `docs/README.md`
requires of every deep-dive under its `## Template` heading — those are the
sanctioned register uses, and a sweep that deletes them destroys mandated
data. The clearest case is `BACKLOG.md`'s removal-condition register, whose
re-verify column is entirely dates (`| 2026-08-11 | not fired`): the date is
the staleness of the check, which is the column's whole point.

### 3. Session / stream / arc narrative — 4 code / 48 md

    grep -rniE 'this session|last session|previous session|session [0-9]|for (two|three|four) sessions|the arc\b' --include='*.py' --include='*.sh' --include='*.md' .

**Beware — "session" is also this repo's domain noun** for an imaging night
(`<session>/<set>/`). In `web/serve.py`, *"another session's runs must not
color THIS session's chips"*, and in `run_set_chain.sh`, *"real flats are
staged for this session"*, are correct domain usage. Only work-session
narrative is in scope.

Verbatim removals:
- `3ac041a` — `# M0 (session 5): NO branch factor in the applied weight. The hard`
- `25bc0a5` — `For three sessions the registry used "cosmic dust", "MW", "IFN" and "dust-safe" interchangeably for FOUR physically unrelated things.`

**Rule:** REMOVE the session framing; keep any residual fact in present tense.
The second example's fact — the four senses are physically unrelated — stayed;
only *"for three sessions"* went.

### 4. How-it-was-found story / incident narrative — 4 code / 13 md

    grep -rniE 'originally|previously|used to (be|quote|only|have)|formerly|turned out|was found (by|when)|where the [a-z]+ came from|an audit (on|found)' --include='*.py' --include='*.sh' --include='*.md' .

The cleanest instance is `7854550`, which trimmed a `CLAUDE.md` rule to its
constraint:

    -  own scope (measured cost: "the repo versions process, not image data" — a
    -  rule about GIT — was transplanted into the archival contract and inverted
    -  the FITS self-description standard; combining would have required repo
    -  access years later. The industry answer, self-describing files, was basic,
    -  known, and unasked-for). The bright line's anti-drift test already forces
    +  own scope. The bright line's anti-drift test forces

**Rule — the discriminator is NUMBERS, not tense.** An incident story with no
measurement is clutter: REMOVE. A measured cost is the evidence the rule rests
on: KEEP (`CLAUDE.md` keeps *"the fingerprint measured it four independent
times within 0.6% of sidereal"* for exactly this reason). A `used to` that
carries a measurement — e.g. `3072fd0`'s idempotence comment, *"MEASURED by
reinstating the fitted lens's vignetting pair by hand — verify_lens_card read
a 4219 ADU corner-vs-centre step on a 30000 ADU uniform card (tol 1.0)"* — is
REVISED to present tense, never dropped.

### 5. Retired-mechanism reference that outlived its revert — 13 code / 143 md

    grep -rniE 'REVERTED|RETIRED|SUPERSEDED|DEPRECATED|\blegacy\b|no longer (exists|used|shipped)|the old chain' --include='*.py' --include='*.sh' --include='*.md' .

Verbatim removals:
- `7489069` — ``# !! REVERTED 2026-08-04 — `--desky` IS OFF BY DEFAULT AND IS A KNOWN REGRESSION.``
- `4ca79cc` — `# geometry (the ~231 MB/frame this line used to quote was the retired 16-bit`

**Rule:** if the mechanism is gone from the code AND its record lives in
`docs/dead-ends.md`, REMOVE and let the registry carry it. If it names a live
guard (a flag that must stay off, a default that must not come back), REVISE
to a present-tense constraint pointing at the registry entry — the reason it
must not return is load-bearing.

### 6. Numbered cross-references that rot — 16 code / 119 md

    grep -rnE 'BACKLOG[: ]+item [0-9]|\bitem [0-9]+\b|NOTES S[0-9]|recipe B[0-9]' --include='*.py' --include='*.sh' --include='*.md' .

`c76af73` re-keyed BACKLOG to slugs because *"numeric cross-references had gone
stale twice"* and called numeric keys "the clutter mechanism". Verbatim:
- `# declaration (BACKLOG item 1: consumers STOP on CONTRADICT).`
- `# BACKLOG item 19: index-style excludes measured silently no-opping in the`

**Rule:** REVISE to the slug (`BACKLOG:one-sided-band`). Remove only if the
item is closed and the referenced fact is dead.

### 7. Line-number citations — 9 in tree, both audited ones had drifted

    grep -rnoE '[a-zA-Z_/.-]+\.(py|sh|ssf|md):[0-9]+' --include='*.md' --include='*.py' --include='*.sh' .

`5e66292` corrected `run_set_chain.sh:112,353` → `145,425`, `README.md:576` →
`586`, `siril/master_dark.ssf:14` → `15`, and added the standing instruction to
*"grep the predicate rather than trust the numbers, since they have now drifted
once."*

**Rule:** REVISE to a greppable anchor — a function name, a section heading, or
the predicate itself. A bare `file.py:NNN` is a citation with a decay clock.

**Measured rot rate: 3 of 3.** The only line-number citations left in the tree
(`web/serve.py`, quoting the frame-count refusals) had ALL drifted by the next
sweep — `run_set_chain.sh:57` pointed at a routing comment, `run_frame_qa.sh:69`
at a `find`, `build_sky_flat.sh:170` at a variable assignment. Treat any
surviving `file:NNN` as wrong until checked.

### NOT a sweep category: victory / status language

Zero instances have ever been removed in 638 commits. The
`WIN | NULL | needs-eyes` rule and the *never "fixed/final/matched/close"*
ban stop it at write time. **Do not grep for `fixed`** — in this repo it is
overwhelmingly the geometry adjective (*fixed mount*, *horizon-fixed*,
*fixed+wide*), and every match in the mining was a false positive. Left here
so a future run does not re-derive the same empty result.

## The safety rule (non-negotiable)

A comment is REMOVED only when its information is:
1. **false**, or
2. **preserved elsewhere** — git, `docs/dead-ends.md`, or the docstring it
   duplicates (verify the duplicate EXISTS; do not assume graduation), or
3. **pure chronology** — when it happened, in what order, by whom.

Anything else is **REVISED to the shortest correct form, never dropped.**
When in doubt, keep and tighten. Deleting a load-bearing constraint is the one
failure mode this sweep cannot detect in its own diff.

## Scope

**In:** `scripts/**` comments and docstrings, `docs/**`, `README.md`,
`TOOLS.md`, `BACKLOG.md`, `MEMORY.md`, `web/**`, and the `why` / free-text
strings in tracked `datasets/**/*.json` records.

**Out:**
- **`CLAUDE.md` ratification stamps** and any dated register entry per
  category 2 — sanctioned, not clutter.
- **`docs/dead-ends.md` mechanism entries** — records, pruned only by the
  registry's own rules (`CLAUDE.md`: maintain IN PLACE). Category 1 drift
  corrections still apply; wholesale entry removal does not.
- **`docs/README.md` Context lines** — the deep-dive template mandates the date.
- **This file and `COMMENT_HYGIENE.md`** — both quote the bad shapes verbatim
  in order to teach them, so every detector hits its own examples here. Expected,
  not clutter.
- **The root session reports** (`ITERATIVE_FLAT_VERDICT.md`,
  `ROUTE_KEY_GENERALITY.md`, `TIER_B_HARDENING.md`, `REBUILD_VERIFICATION.md`
  and their successors) — transcripts of one completed session, stating what was
  true at the measurement. Their detector hits are real (six `file:NNN` cites in
  `ROUTE_KEY_GENERALITY.md` alone, pointing at sites that session then removed)
  and revising them would rewrite a record rather than a contract. Category 1
  still applies where a report is CITED by live prose as current guidance.
- Anything under `.git/`, and gitignored derived data.

## Acceptance shape for a run

1. Every hunk in the diff cites its category number.
2. Re-run every detector above. It returns clean, or each survivor is listed
   with the sanctioned-use or domain-noun reason it stayed.
3. Category 1 is reported separately with the file, the claim, and the code
   that refutes it — a drift correction is a factual finding, not a tidy-up,
   and it is the reason this sweep is worth running.
4. Report counts per category: removed / revised / kept-with-reason.
