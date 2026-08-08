# Fresh-session prompt — optics-state audit: attribute the aug06 field terms, adopt per the verdict

Read `CLAUDE.md` first — it is the briefing and the read order. The
pre-registered plan you are executing is BACKLOG:`optical-state-models`; read
it in full, and the register row for the fitted lensfun entry it amends. Do
not re-derive the plan — run it.

## The question

aug06 products measure a field-dependent degradation under the july-fitted
pinned lens model: centre FWHM BETTER than the july31 family (set-01: 2.99 px)
with both spatial terms ~2x elevated (off-axis 0.82 vs 0.16–0.47 px; tilt
0.53 vs 0.21–0.25 px). The user states focus is recalibrated every session
(sometimes mid-night), so the model describes ONE optical state. Attribute
the elevation: DISPLACEMENT (july's model mis-mapping august's glass —
a refit fixes it) vs BLUR (august's focus state carries more field
curvature — acquisition's lever; no warp fixes blur). Then adopt per the
pre-registered rules. HOLD the cross-session combine until this closes.

## The investigation (the BACKLOG item's discriminators, in order)

1. **Displacement vs blur.** Corner-vs-centre star sharpness on SINGLE
   mid-burst frames — calibrated and debayered, never a stack — from
   july31/set-01, aug06/set-00, aug06/set-01. Instruments: the tool's own
   measures only, fixed external geometry (the `star_stations.py` pattern /
   Siril `findstar` on fixed crops — trap 3 forbids any geometry derived
   from the detections). Several singles per corpus, not one — state n.
   - Soft corners ON SINGLES in the aug06 corpora but not july31 → BLUR:
     record it as the acquisition signature, no processing change follows.
   - Uniform singles + degraded stacks → DISPLACEMENT: proceed to step 2.
   - Mixed → report both magnitudes separately; only a genuinely
     unmeasurable weighting goes to the user.
2. **Granularity (displacement branch).** Fit models from each corpus's own
   frames with `fit_lens_model.sh` (scripted; feed it per its own traps) —
   july31, aug06/set-00, aug06/set-01 — and compare pairwise on the
   register's displacement-equivalence test (≤0.47 px max mid-field
   displacement = same model). Verdict: per-session state vs per-set state.
3. **Adoption (pre-registered, execute without re-asking):**
   - BLUR: record the verdict + numbers in the BACKLOG item and the session
     records; build sets 02/03 under the pinned model as-is; the checklist's
     acquisition note is the standing fix.
   - DISPLACEMENT, states equivalent across aug06: fit ONE aug06 model, pin
     it as data beside the july entry (the `lens_models.json` pattern —
     keyed by session/state, installed from the record), rebuild set-00 and
     set-01 only if their model differs from july's beyond equivalence
     (re-running is cheap and correct), build 02/03 under the aug06 model.
   - DISPLACEMENT, per-set states: fit per set, same pinning pattern, same
     rebuild rule, and say so loudly — that granularity changes the standing
     preflight design (note it in the BACKLOG item for the wiring step).
   - Either displacement branch: verify each adopted model the pinned way
     (`lens_preflight` difference proof; `verify_lens_card.py` if the DB is
     touched), and re-measure the rebuilt products' spatial terms — the
     before/after IS the experiment record, one knob, control bracketed.
4. **Then the combine gate lifts**: with every member correctly rectified
   under its own state's model, goal 2 of `RUN_AUG06_PROMPT.md` proceeds
   (six ~500-frame members; membership already ratified).

## Constraints

- One knob per experiment; hypothesis before run; MEASURED vs HYPOTHESIS
  labels on every claim; numbers with instruments; no narrative in records.
- Every fitted model is PINNED AS DATA in the tracked record before any
  product depends on it — a model that exists only in a machine-local DB is
  the exact failure the register row documents.
- The judge surfaces already awaiting the user's eyes stay untouched;
  rebuilds produce new candidates beside them, never overwrites.
- Commit as you go, evidence-bearing messages, tree clean at the end.

## Deliverable

`OPTICS_STATE_AUDIT_PROMPT_report.md` at the repo root, committed: the
verdict with its discriminating numbers (per corpus, per instrument, n
stated), the granularity matrix if reached, every adopted/pinned model with
its verification, what was rebuilt and its before/after spatial terms, the
explicit go/no-go state of sets 02/03 and the combine, and anything only the
user can decide, stated as options. The report will be audited against your
commits.
