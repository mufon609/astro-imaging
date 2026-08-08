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
adoption step 3.

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
6. **The combine** (RUN_AUG06_PROMPT.md goal 2, membership ratified: six
   ~500-frame members, full sets only): compose the rebuilt own-model
   members' sub-stacks; coverage record per the prompt; the cross-set
   record-home gap (BACKLOG:`cross-set-record-home`) still applies — degrade
   loudly on record placement.
7. **Close the loop**: update BACKLOG:`optical-state-models` step 3 with the
   A/B numbers; the standing-preflight wiring ("does the pinned model fit
   THIS session's frames") remains the item's closing condition — note what
   its design should be from what this run teaches.

## Constraints

One knob per experiment; MEASURED vs HYPOTHESIS labels; numbers with
instruments; nothing overwritten — controls preserved, rebuilds beside them;
judge surfaces for the user's eyes at full frame; commit as you go,
evidence-bearing messages, tree clean at the end. Report to
`OPTICS_STATE_AUDIT_PROMPT_report.md` at the root, committed: per-set fits
(CPs, rms), A/B tables, adoption verdicts, the july31 diagnosis outcome,
combine state, and anything only the user can decide, stated as options.
