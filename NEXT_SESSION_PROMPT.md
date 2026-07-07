CLAUDE.md (auto-loaded) is the agent operating manual. Then read
~/Desktop/astrophotography/README.md (process contract), then NOTES.md
TOP TO BOTTOM (STATUS, design + knob provenance, DEAD ENDS — never
re-attempt those, bandaid ledger, acquisition checklist). NOTES is the
source of truth for state; history lives in git log only.

CURRENT STATE: approved recipe B7 unchanged (tag B7-approved; defaults
byte-reproduce it — verified 3× on 2026-07-07 including after every
script change). Reproduce before touching anything:
    python3 scripts/starcomb.py 07-02-26 set-03 \
        --stack 07-02-26/results/stack_set-03_norgbeq_spcc.fit --lossless
expect: gate (starless-sky) PASS blocks 1.375 (5/8/11), colors 2/2,
rings 3.0/1.3/1.2; corridor +4.0/-3.0, bands 0.6/1.2; clip0 ~16.2%/1.2%;
aura_lum +2.0, shell_chroma ~28.9; anchor 0.0284 [catalog] -> m 0.00090
(x996); all four artifacts byte-identical to
results/starcomb_set-03_APPROVED_B7_20260707_103839.*. Then delete the
duplicate renders (watch the shell cwd and the .png glob: it also
matches _16bit.png — compare exact stamped names).

TWO USER JUDGMENTS ARE PENDING (do not bake either without the user):

1. sep_engine `hybrid` (NOTES ledger #4 — StarNet2-ONNX on aarch64,
   validated end-to-end this session). Every objective bar met: gate
   PASS 1.375 (= control), aura_lum +2.0 (= approved), pedestal = the
   inpaint fill, faint-tail residual 589 vs ~5.1k, chroma rings improve
   1.33/1.22 -> 1.11/1.00. The user judges:
   results/exp_starsep_sep_engine_20260707_125122/judgment/
   (judge_starless_stipple.jpg is the headline; judge_bright_shells.jpg
   shows shells unchanged; 4 standard zone panels) + the full renders
   v0_hybrid.jpg / v1_inpaint.jpg. The killed stock-net A/B record is
   exp_starsep_sep_engine_20260707_120825/ (aura +12 — do not revisit;
   numbers in ledger #4). If APPROVED: flip starcomb default
   --sep-engine to hybrid, re-render --lossless, verify expected
   numbers, tag B8-approved, bake artifacts + STATUS (the starless jpg
   = gate input changes identity: new byte-reproduce contract), move
   ledger #4 to CLOSED (starsep.py becomes the fallback), update the
   README step-6 row. The hybrid needs the net cache trio
   work/starsep/*_neth.* (kept; regens in ~7 min if pruned).

2. stars_anchor `noise` default flip (NOTES ledger #7). Mechanism
   measured and killed in synthesis: per-channel gain (the real drift
   class) moves catalog-mode G rendering -8.5/-20 counts (mid/faint)
   while noise mode holds <= 0.6. ACCEPTANCE ALREADY MEASURED: a full
   noise-mode render on the canonical stack came out byte-IDENTICAL to
   all four B7 artifacts. If the user approves: flip the default,
   byte-verify once more, keep `catalog` as a flag.

ENVIRONMENT ADDITIONS (in CLAUDE.md now): StarNet2 weights + venv at
~/.local/share/starnet/ (license: personal astrophotography use only —
keep weights out of the repo). scripts/starnet_sep.py bootstraps its
venv; scripts/spcc_run.py runs siril SPCC and captures K factors to
work/spcc_<set>.{json,log} — USE IT for every future spcc (canonical K:
R 1.000 / G 0.656 / B 0.837, 509/2850 kept; spcc rerun measured
pixel-deterministic; the old 1.675/0.749/0.935 triple was a grep-loss
casualty and does not reproduce).

REMAINING QUEUE AFTER THE JUDGMENTS: lights-set data-general fixes
(treeline-aware background modeling, corner chroma) only if that set
matters; NEXT ACQUISITION outranks everything (checklist in NOTES: ISO
800, subs <= 500/focal, matched flats per focal BEFORE zoom changes,
dither, no moon). The hybrid's render-domain gain was measurably
subtler than its linear-domain gain BECAUSE the data is
exposure-limited — more photons buy more than any remaining knob.

RULES (README has the full contract): one knob per experiment,
hypothesis pre-registered in NOTES before the run; killed hypotheses
get their numbers written before anything else is tried; the gate
never loosens; corridor/star-shell/clip0 are REPORTED context; nothing
aesthetic bakes without the user's eyes on like-encoding panels; after
ANY script change byte-verify B7 (all four artifacts, exact names);
no session tags in script comments; NOTES stays in its refactored
shape (update in place, never append narrative); background long runs;
preserve stacks per experiment; track disk (~22 GB free).
