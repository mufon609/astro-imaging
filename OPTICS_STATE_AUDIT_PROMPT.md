# Fresh-session prompt — optics-state ADOPTION: rebuild under per-set models, then the combine

Read `CLAUDE.md` first — it is the briefing and the read order. The
investigation phase is COMPLETE and its verdicts are on record — do not redo
it: BACKLOG:`optical-state-models` (discriminators 1–2 carry their measured
verdicts), `datasets/aug06/experiments.jsonl` (the ledger entries
`optical_state_d1_displacement_vs_blur`, `fit_instrument_cp_starvation`,
`optical_state_d2_granularity_matrix`), and the fitted models at
`datasets/aug06/set-00/qa_work/lens_fit.json` (317 CPs) and
`datasets/aug06/set-01/qa_work/lens_fit.json` (114 CPs, strict-pruned).
Verdicts: the aug06 field-term elevation is DISPLACEMENT (the raws are
clean); the optical state is PER-SET. This prompt is the execution of
adoption step 3. **Trigger: start when the in-flight set-03 build completes**
— that product is a control arm, not waste.

## The work, in order

1. **Fit set-02 and set-03 from their own frames** with the PATCHED
   `fit_lens_model.sh` (it now fattens detection copies with gauss 3 and
   preserves its ptos/logs). Use the working geometry: a 12-frame mid-burst
   subset staged as its own dir (the ledger records why spread-12 over 500
   starves). If default cpclean leaves multi-px residuals, apply the strict
   prune the set-01 record documents (cpclean -n 1 x2, staged re-optimize)
   and record CP counts + rms in the set's `lens_fit.json`.
2. **Rebuild every aug06 set warp-onward under its OWN model** —
   `install_lens_model.sh` per set from the set's record, then the chain
   (masters, QA, audit, culls, flats all survive; only warp -> register ->
   stack -> solve -> SPCC -> judge re-run). PRESERVE the current
   pinned-model products first under tagged names (`cp` — the binding
   preserve-per-experiment rule): they are the A/B control arms.
3. **Accept per set by the A/B, never the fit's residual**: `seqtilt` +
   `star_stations.py` (drift axis from the solves) rebuilt-vs-control, then
   the user's eyes on both judge surfaces side by side. Expected direction:
   set-01 off-axis 0.82 -> toward the 0.16–0.47 family; a rebuild that does
   not measurably improve does NOT adopt — report it and stop for the user.
4. **Diagnose the july31 fit failure** (66 CPs / 152 px residuals on its
   12-frame subset — ledger; cause OPEN). Its preserved procedure is the
   same as aug06's; find what differs (frame content? moon gradient? the
   subset window?). If a trustworthy july31 fit lands: fit + rebuild july31
   set-01/02/03 the same way (the pinned incumbent was fitted from JULY14
   frames, a different night). If it cannot be made trustworthy: july31
   stays under the pinned model — its products are the family floor — and
   you state the heterogeneity in the combine's record.
5. **Baselines**: accepted rebuilds fail their seeded baselines BY DESIGN —
   re-seed with a note only after the user accepts each product.
6. **TWIN combines, both built (user-ordered A/B)** — from the rebuilt
   own-model members' sub-stacks, compose BOTH: (a) aug06-only (its three
   ~500-frame sets) and (b) the six-member both-sessions combine
   (membership ratified: full sets only). Like-encoded judge surfaces side
   by side + a coverage record for EACH arm. Carry the measured context in
   the record: july31 sky is only ~6% brighter per frame (bg 1115–1117 vs
   1050–1055 — light-pollution-dominated site, so no SNR penalty and the
   six-member arm gains ~1.4x depth), the two nights' gradient orientations
   are FLIPPED (partial cancellation, magnitude measurable only in the
   build), and the pointing spans cost canvas: aug06-only 1.89 x 0.19 deg
   vs six-member 5.21 x 1.58 deg (~an extra ~700 x 300 px off the
   fully-covered area). WHICH arm carries forward is the user's eyes on the
   paired surfaces — never decided here. The cross-set record-home gap
   (BACKLOG:`cross-set-record-home`) still applies — degrade loudly on
   record placement.
7. **Close the loop**: update BACKLOG:`optical-state-models` step 3 with the
   A/B numbers; the standing-preflight wiring ("does the pinned model fit
   THIS session's frames") remains the item's closing condition — note what
   its design should be from what this run teaches.

## Not in this run (scope fence)

The render-ladder L1 background step (the lever for july31's moonlit
gradient — user-gated, its own bracket), the final best-N% pass (needs more
sessions), and any change to combine MEMBERSHIP (ratified: full sets only;
set-00 and set-04 stay standalone).

## Constraints

One knob per experiment; MEASURED vs HYPOTHESIS labels; numbers with
instruments; nothing overwritten — controls preserved, rebuilds beside them;
judge surfaces for the user's eyes at full frame; commit as you go,
evidence-bearing messages, tree clean at the end. Report to
`OPTICS_STATE_AUDIT_PROMPT_report.md` at the root, committed: per-set fits
(CPs, rms), A/B tables, adoption verdicts, the july31 diagnosis outcome,
combine state, and anything only the user can decide, stated as options.
