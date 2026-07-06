# Prompt for the standard-workflow integration session (copy-paste below the line)

---

Read `~/Desktop/astrophotography/NOTES.md` fully before touching anything —
it is the source of truth: pipeline design, every measured lesson, every
dead end with its numbers (do not re-attempt them). Environment facts are
in auto-memory: Siril 1.4.4 user flatpak (`flatpak run --command=siril-cli
org.siril.Siril -d <dir> -s <script>`, .ssf scripts under $HOME not /tmp),
4-core arm64 / 7.7GB RAM / ~30GB free disk, python3 with numpy + scipy +
PIL + matplotlib (NO astropy), exiftool, GraXpert 3.2 at
`~/.local/bin/graxpert` (BGE + denoise only — NO star removal), NO StarNet
(no aarch64 build exists — star separation is `scripts/starsep.py`,
mask+inpaint). Timings: full pipeline ~15 min, post-only ~1 min, GraXpert
~4 min cold then cached, starsep ~85 s cached by input identity.

MISSION: restructure our pipeline to follow the INDUSTRY-STANDARD deep-sky
workflow end to end. Where we diverge from the standard, that divergence
is a bandaid unless it is a measured, documented adaptation forced by this
data. Perfect the process on the current crappy data first (set-03:
21×25s ISO 200 @ 37/38mm, no matching flats, moonlit sky) — if the
standard process looks good at ISO 200 it will look great at ISO 800 with
shorter subs. FULL FRAME remains mandatory (no crops hiding defects), the
foreground branch (bottom-left) must never drive decisions (it is masked
in QA), and the goal image is unchanged: black sky, visible MW dust/glow,
sharp shining stars.

THE REFERENCE STANDARD (audit against this, in this order):
1. Calibrate (bias/dark/flat) → register → integrate/stack
2. LINEAR: gradient/background extraction (DBE/GraXpert-class), star-ful
3. LINEAR: photometric color calibration (SPCC/PCC via plate solve)
4. LINEAR: deconvolution (optional, data permitting)
5. LINEAR: noise reduction
6. Star separation (starless + stars layers)
7. Stretch starless hard (nebulosity), stars gently (cores/color) —
   optionally cull/reduce the faint star tail
8. Recombine (screen/PixelMath), final touches (saturation, curves),
   export

STEP 1 — AUDIT (do this before changing anything):
a. Verify the recorded state reproduces: re-run `bg_qa.py` on
   `results/candidate_v5_fullframe.jpg` (expect PASS: blocks 1.35,
   colors ≤6, rings 3.7/3.4/3.4) and on
   `preview_set-03_20260706_104902.jpg` (expect FAIL 4.9/6.8). Confirm
   `stack_set-03.fit` MW contrast ≈ +39 linear counts via
   `starcomb.box_median_g` (MW_BOX − SKY_BOX). Spot-check two or three
   NOTES claims against their exp dirs (`results/exp_*/hypothesis.md` +
   metrics).
b. Produce a gap-analysis table into NOTES.md: standard step | our
   implementation | verdict (COMPLIANT / ADAPTATION-justified / BANDAID)
   | fix plan. Known entries to classify honestly:
   - Self-flat chain (median → V2 → rechroma → divide): ADAPTATION forced
     by missing 37/38mm flats — with real flats the entire chain
     disappears behind the preflight branch (flat division + stack-level
     BGE). Keep it isolated, do not let it leak into the flat path.
   - Per-frame `seqsubsky 1` before stacking: NOT standard (standard
     removes gradients once, on the stack). It exists because the
     self-flat division amplifies per-frame glow. Re-examine whether the
     bge_first order on the stack can replace it WITHOUT reviving the
     +55% periphery lift dead end — measure, don't assume.
   - `rgb_equal` color calibration: BANDAID. The standard is SPCC/PCC:
     investigate siril 1.4 `platesolve` + `spcc` with offline/local
     catalogs on this box (no unrestricted internet assumed — check
     what catalog downloads siril needs and whether they are feasible).
     If SPCC lands, the unlinked-stretch cast handling may simplify.
   - Deconvolution: documented dead end on this data (trailed stars, PSF
     unstable on ≈0 background) — COMPLIANT to skip, note it.
   - Denoise: currently OUT (gate: pre-stretch rings 5.1, post-stretch
     4.2 vs 4.0). Standard does noise reduction LINEAR (step 5) — test
     linear denoise (siril -vst AND GraXpert denoising) on the STARLESS
     layer inside the standard order; also the untested post-stretch
     `-mod≈0.5` blend.
   - QA gate: bg_qa treats the whole frame as background, so it reads a
     boosted MW as artifact (measured: mw_boost 0.6 → ring 6.1). The
     standard-aligned reframing is LAYER-APPROPRIATE QA: strict
     blocks/rings gate on the STARLESS background render, star metrics
     on the stars layer, aesthetics judged by the user on the recombine.
     This is a scope change, NOT a threshold change — thresholds never
     loosen. It requires the user's explicit ratification in-session
     before touching bg_qa's role. Present it as the first decision.
c. Confirm the open user decision from NOTES "DECISION MATRIX"
   (2026-07-06): bright MW + full frame + whole-frame gate is measurably
   incompatible on this data. The layer-appropriate QA reframing above is
   the standard-workflow resolution of it.

STEP 2 — INTEGRATE (single-variable discipline still applies):
Target chain for set-03, standard order, each transition gated:
  stack (L2 self-flat pipeline, preserved `stack_set-03_L2.fit`)
  → GraXpert BGE + subsky 1 on the STAR-FUL linear (measured MW-safe
    order; on starless it erased the MW +38→+0.4 — never BGE starless)
  → SPCC if feasible (else rgb_equal + document as remaining bandaid)
  → linear denoise ladder on the starless layer (S3, pending)
  → starsep.py separation (validated: clean layers, MW intact)
  → starless stretch ladder + mw_boost under the ratified QA scope;
    stars: fix the anchor (0.85 renders mid-peak 225 vs 250 star-ful —
    ladder 0.85/0.92/0.97), faint-cull ladder (S4, pending)
  → screen recombine → final QA + user judgment.
Tools you already have: `scripts/starcomb.py` (bge_first order is
default; ladder mode with --param/--values/--hypothesis),
`scripts/experiment.py` (post-chain ladders), `scripts/inspect_stage.py`
(per-stage reports wired into `run_pipeline.sh`/`run_post.sh`),
`scripts/bg_qa.py` (the gate). Preserved inputs:
`results/stack_set-03_L2.fit` (canonical), `_prechroma.fit` (historical).

RULES (unchanged): hypotheses pre-registered in NOTES before each run;
one knob per experiment, bracketing the control; measurement kills a
hypothesis → write the dead end into NOTES with numbers BEFORE trying
anything else; recipe/aesthetic changes need the user's visual approval
(objective fixes with pass/fail metrics may commit); never loosen a QA
threshold; keep NOTES.md current as you go. When a full-pipeline run is
needed, background it and keep working; preserve the stack per
experiment (`cp` to a tagged name) — L3 taught us why.

SUCCESS CRITERIA for this session: (1) gap-analysis table in NOTES with
every divergence classified and either fixed or justified; (2) the
standard-ordered chain runs end to end on set-03 producing a full-frame
image the user approves visually, with layer-appropriate QA passing
under whatever gate scope the user ratifies; (3) every bandaid that
remains is listed with its removal condition (e.g. "dies when real
flats exist" / "dies when SPCC catalogs are installed").
