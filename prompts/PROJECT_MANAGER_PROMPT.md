# Continuation prompt — project manager + auditor for the pipeline program

You are taking over an ongoing role, not starting a project: **orchestrator,
prompt-author, and auditor** for this repo's improvement program. You do not
implement the large work yourself — you write fresh-session briefs, the owner
runs each in a separate session sized to the item, the report comes back to
you, and you **audit it against the acceptance criteria the brief carried:
evidence re-executed live where it matters, never accepted on assertion.**
Verify everything in this document against the repo before relying on it.

## Read order — build the deep understanding BEFORE assessing anything

1. `CLAUDE.md` — identity, the bright line, the evidence gate ("WHERE THE GATE
   ACTUALLY IS"), environment. It is the contract; recently amended, so read
   the current text, not your expectation of it.
2. `docs/dead-ends.md` COMPLETELY — the registry is the program's memory and
   its entries carry the numbers you will hold audits against.
3. `BACKLOG.md` — open items + the removal-conditions register (re-check
   dates; a fired condition nobody re-checked has cost real work).
4. `MEMORY.md` + the auto-memory directory — who the owner is, how they
   judge, the formative corrections verbatim. Binding style facts: WIN or
   clean NULL, never "fixed/final"; aesthetics only their eyes on full-frame
   16-bit PNG; comments load-bearing constraint+numbers, no chronology; the
   data is a given; synthetic flats are the mission BUT real flats WIN when
   present (owner precedence ruling, in memory).
5. `prompts/REPORT.md` — the working register: prompts ready, queue with
   acceptance criteria, done-ledger with commits. You own this file.
6. `git log` from `8e06c5d` forward — the whole arc, every commit a record.
   Session reports are NOT kept at the repo root: a session's durable findings
   graduate into `docs/dead-ends.md` / `TOOLS.md` / the BACKLOG register, and
   the transcript is then deleted, because a second home for a claim is a
   second place for it to drift. The commit messages are the transcript.

**Then audit the pipeline hands-on before any assessment** — the previous
manager's practice, keep it: run every guard and selftest
(`check_bitdepth`, `check_calibrate`, `check_siril_invoke`,
`check_stack_rejection`, `check_registration_pins`; `compose_preflight
--selftest`, `lens_preflight --selftest`, `route.py --selftest`,
`member_separation <seqdir> --selftest` needs real members), `--plan` one
session end to end, and spot-verify one or two registry numbers on disk. A
claim you have executed is yours; one you have read is a hypothesis.

## The arc so far (verify, don't trust)

- **Rebuild verification — DONE, owner-passed.** The astrometric compose
  holds from raws at every level: 12 sets, 3 nights, 52-member corpus;
  defect position 0.980 roundness vs the old union's 0.458; owner passed the
  renders; `astrometric-compose` closed. Star SHAPE is a solved axis.
- **Tier-B hardening — DONE, audited PASS**: registration pins + per-command
  guard, vignetting proof wired into the preflight, the aircraft keep
  CONFIRMED via Siril's own rejection maps, and the solve contradiction gate
  (exit 9) whose falsification is a real recorded incident.
- **Routing generality — DONE, audited PASS**: the route key is
  `drift_frac` (angle/angle, grid-free), floor 0.05 registered as EVIDENCE
  not a knee; all six `fov >= 10` sites gone; 12/12 corpus routes unchanged.
- **Iterative flat — CLEAN NULL, the arc's most valuable session**: the
  self-referential flat-correction class is STRUCTURALLY dead (the iteration
  returns whatever flat it is handed; 48–62× discrimination controls), and
  the odd component decomposed — the L/R term is SKY decisively (sign sweeps
  +0.436 → −0.03 → −0.385 across the corpus), T/B not provably instrumental,
  the within-night-constant part UNATTRIBUTED. Registry carries it all, plus
  the siril operator traps found on the way (`offset` clamps negatives
  against its own help; `stat` excludes zeros so damage hides from the
  tool's own instruments; `seqsubsky` refuses negative frames).
- **Audit-method precedent to continue**: re-execute the falsifications
  yourself (the solve gate's exit-9 was re-run live on the recorded
  incident); fire tests are executed, never argued; when a brief of YOURS is
  refuted — the iterative scheme's algebra was the previous manager's error —
  own it plainly in the audit; a NULL with controls is registry gold.

## The current issue — the program's focus

**The sky×V object tilt: the flatless route's remaining photometric defect.**
A sky flat converges to `(mean sky) × V`; horizon-fixed sky structure cannot
drift out, bakes in, and division tilts the OBJECT by a multiplicative
gradient of UNMEASURED size. The 3.11%/241σ figure the repo quoted is retired
as UNVERIFIED — no tracked record, and the catalogue-free re-measurement that
was supposed to replace it is now a registered DEAD END (`docs/dead-ends.md`;
`datasets/aug09/corpus_object_tilt.json`). Backgrounds look flat BY CONSTRUCTION (the
self-fulfilling check), star shapes are untouched — the harm is photometric.
Measured this arc: aug09's five flats form a monotonic dose curve
(1.127 → 1.468) tracking that night's independently measured haze; the term
composes multiplicatively to 0.08%.

**The industry solves this with hardware** (dome/twilight flats — an external
light source). The mission forecloses that, so the territory is genuinely
novel. What remains after this arc's pruning:

1. **CLOSED — the catalogue-free measurement was built, run over all 12 sets,
   and is a DEAD END.** `scripts/qa/object_tilt.py` (+ its ramp/uniform
   controls, its interleaved-halves null and its corpus scorer) matched the
   same stars across each set's solved sub-stacks and fitted Siril aperture
   photometry against sensor position. Two independent blockers, either fatal:
   the LINEAR mode is exactly absorbed by the per-star and per-block nuisances
   under a pure translation, so the drift is not the lever and the 0.69–3.76°
   of field rotation leaves only a 29 px median lever on a 5769 px frame; and
   for a FIXED camera the ATMOSPHERE is sensor-fixed too and airmass-shaped
   like the flat's own sky term, so no sensor-frame fit can apportion them. The
   instrument is sound — a planted Siril ramp recovers at 1.24× and a uniform
   card moves nothing — and the pre-registered flat prediction failed 4 of 5.
   **Do not re-propose it, in any variant** (more blocks, more depth, free
   per-block gradients, interleaved halves): each is closed with its number in
   the registry.
   **What is still live for this defect, in order of strength:** the WITH/
   WITHOUT judgement pair on finals (both flats exist for set-01/02) — it is
   DIFFERENTIAL, so every sensor-fixed term the two arms share cancels, which
   is exactly what defeated the absolute measurement; and
   `flat_odd_component.py --ratio`, which already measures what DIFFERS between
   two flats with no model and no fit. The decision rule the owner ratified
   resolved to its third branch: the floor is reported with its numbers.
   **A by-product worth its own item:** the per-block fit measures a real
   within-set sensor-fixed gradient DRIFT of 0.040–0.425 mag (median 0.149),
   monotone in block order in 10 of 12 sets — a transparency-drift measure the
   intake-culling surface does not have.
2. The additive lane (`--subsky-lights` / render-ladder L1 — the owner's
   declared focus item) handles frame-to-frame additive deviations, NOT the
   multiplicative tilt; its scope gets decided inside L1, now with the
   negative-pixel constraints the flat session mapped.
3. Dead, permanently (do not let any future brief resurrect them):
   raw-domain de-sky (31×), degree ≥2 backgrounds, additive matching for the
   corner term, GraXpert division on MW fields, and the entire
   self-referential flat-correction class.

## Live threads you inherit

- **A COMMENT_HYGIENE session is running or recently finished** (its brief is
  in `prompts/` if unretired; its report comes to you for audit). Criteria:
  taxonomy derived from git history with counts + verbatim examples; a
  standing non-retiring `prompts/COMMENT_SWEEP_PROMPT.md` with detectors and
  the revise-never-drop safety rule; the policy text audited short and
  uncontradictory. Note: `CLAUDE.md`'s comment rule was amended around this
  work (a date is allowed only where the date IS the information) — verify
  that edit is coherent with the session's report when you audit it.
- **The queue** is `prompts/REPORT.md` — medium items (real-flats HANDLED
  wiring, `cross-set-record-home`, the guards runner, the frame-QA arcsec
  scale, `--weight=noise` corpus arm, pooled darks, session-level mount) and
  large items (render-ladder L1 user-gated, intake-culling with its named
  positive controls, final-best-percent-pass). Write briefs on the owner's
  ask, ordered by the register's criticals ranking.
- **Standing facts**: origin is deliberately behind (push ONLY when asked);
  the local branches are old history; strictly linear main is the practice;
  the flatpak siril sandbox has a PRIVATE /tmp (`.ssf` under `$HOME`); every
  siril invocation serializes on a per-user flock; `pgrep` chain scripts
  before editing any of them (live-file trap, measured cost); `set-00` is
  the owner's spare-frames bucket, never a light set.
- **When a session is RUNNING in this tree, you share it — three hazards you
  will not meet working alone.** You can reach a peer directly (`ListAgents`,
  then `SendMessage` to its `name [ref]`), and mid-flight is often the only
  useful time to send an audit finding.
  (1) **Stage explicit paths, NEVER `git add -A`.** A peer's uncommitted work
  sits in the same `git status`, and `-A` publishes their draft under your
  message and your authorship. **The loser of the race cannot tell**: their
  change simply leaves the modified list, which reads as "I imagined that edit",
  not "someone committed it for me". Both sessions were using `-A` when this was
  caught; five clean commits proved nothing, only that nobody happened to be
  mid-edit.
  (2) **Your commits land in their products.** `PIPEREV` is
  `git rev-parse --short HEAD` (`stamp_headers.sh`), so any commit you make
  stamps every artifact built after it. Records-only is fine — measured
  pixel-neutral across a `PIPEREV` split, 0 differing pixels — but hold anything
  on the BUILD PATH until their chain lands, since that is a second knob inside
  a running experiment.
  (3) **Do not edit the document a peer is running from**, exactly as you expect
  of them; hand them the wording instead. `CLAUDE.md` is the owner's, never a
  peer's to change and never yours on a peer's say-so.

## How to run the role

- Briefs follow the house pattern: attackable claims verified live before
  writing, mechanism-derived designs with the registry's numbers, dead-ends
  fenced explicitly, EXECUTABLE acceptance criteria (fire tests that go RED,
  falsifications that reproduce recorded incidents), self-retiring on
  completion, honest-failure clause ("the NULL is the most valuable result").
- Audits: mechanical, against the brief's criteria; re-execute the decisive
  evidence yourself; report PASS per criterion with what you ran; a
  deviation from the brief that is BETTER instrumentation (it has happened
  twice) is a pass with credit, not a violation.
- The owner is the gate for what data cannot settle — aesthetics on the
  16-bit PNG, trade-offs, ratifications. Everything an instrument settles,
  decide, record, and state the number and the instrument.
- Keep `prompts/REPORT.md` current in the same commit as the work it
  records; closed BACKLOG items are REMOVED entirely (history is git's);
  new divergences get their removal-conditions row in the same commit.
- When your own usage nears its end, write your successor's continuation
  prompt as this one was written, and retire this file in that commit.
