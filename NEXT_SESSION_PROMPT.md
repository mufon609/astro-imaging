# Next-session prompt (copy-paste; delete this file once executed)

Read ~/Desktop/astrophotography/README.md first (the process contract:
standard-workflow mapping, review contract incl. the standing audits,
per-set geometry, experiment discipline, the NORTH STAR), then NOTES.md
TOP TO BOTTOM (it is short by design: STATUS, current design with each
knob's measured WHY, the DEAD ENDS registry — NEVER re-attempt those,
bandaid ledger, acquisition checklist). NOTES is the source of truth;
full chronological history lives in git log only. Environment facts live in auto-memory: Siril 1.4.4 user
flatpak (`flatpak run --command=siril-cli org.siril.Siril -d <dir> -s
<script>`, scripts under $HOME not /tmp), 4-core arm64 / 7.7GB RAM /
~24GB free disk, python3 numpy+scipy+PIL (NO astropy), GraXpert 3.2 at
~/.local/bin/graxpert (BGE + denoise only), local Gaia/SPCC catalogs
INSTALLED (7.4GB: astro + Cygnus + Boötes xpsamp chunks), astrometry
venv at ~/.local/share/astrometry-venv.

CURRENT STATE: approved recipe B7 (git tag B7-approved; B6/B5 are
HISTORY, not approved — B6's stack was pruned, only its jpg+png record
remains). Reproduce before touching anything:
    python3 scripts/starcomb.py 07-02-26 set-03 \
        --stack 07-02-26/results/stack_set-03_norgbeq_spcc.fit --lossless
expect: gate (starless-sky) PASS blocks 1.375 (P5/P50/P95 = 5/8/11)
colors 2/2 rings 3.0/1.3/1.2; corridor floor +4.0/-3.0, bands 0.6/1.2,
black_point clip0 corridor ~16.2% / sky ~1.2%; star shells aura_lum
+2.0 (WARN >4.0) shell_chroma ~28.9 (trend); stars anchor 0.0284 -> m
0.00090 (low-end gain x996); all four artifacts byte-identical to
results/starcomb_set-03_APPROVED_B7_20260707_103839.{jpg,png,_16bit.png,
_starless.jpg}. Per-set geometry: config_set-03.json (corridor manual,
foreground rect) + config_lights.json (corridor wcs, foreground mask) —
new sets derive from WCS/config, NEVER inherit set-03 silently.

MISSION — audit first, then the queued work, one knob at a time,
hypotheses pre-registered in NOTES before each run:

0. AUDIT (blocking): reproduce B7 byte-exact (above). Then verify the
   standing audits fire by measurement, not by trust: star_shell_report
   on results/starcomb_set-03_APPROVED_B6_20260706_232205.png (the
   defect-era record; use the newest starsep catalog in work/starsep/)
   must WARN (aura ~+12), on the B7 png must be clean (~+2); the gate
   scope must match config_set-03.json geometry. Spot-check 2-3 numbers
   from the NOTES knob-provenance table against the artifacts. Any
   mismatch: STOP, root-cause, write it into NOTES before proceeding.

A. StarNet-ONNX on aarch64 (bandaid #5 removal — the deepest remaining
   processing-quality lever). Recorded facts: StarNet v2.5.3 ships
   self-contained ONNX Runtime packages for Linux x64 (no aarch64
   build); onnxruntime aarch64 wheels 1.20-1.27 verified installable
   here. Next actions, in order: download the official Linux x64 CLI
   package; check it contains a LOOSE readable .onnx (the go/no-go —
   if embedded/encrypted in the binary: DEAD END, write it with what
   was found, mask+inpaint stays); if loose: build a tiled-inference
   driver (256px tiles + overlap blending, the nekitmm/starnet
   protocol) in the astrometry venv or its own; VALIDATE on set-03's
   bgelin: starless MW contrast must survive (>= the mask+inpaint
   chain's +2.6 at bgelin, ideally ~+39 stack-level), no structure
   holes, star recovery >= current catalog, gate + star_shell on a
   B7-config render with the net-separated layers; user judges panels
   vs B7 before ANY bake. If adopted: starsep.py becomes the fallback,
   bandaid #5 closes, and the <6σ faint-tail cost + skirt-aura class
   disappears at the source.

B. Noise-relative stars anchor (kills the measured x864->x996 low-end
   gain drift between stacks of the SAME sky). Pre-register: replace
   the data-dependent anchor (median top-500 catalog amplitude) with a
   noise-relative or fixed-gain anchor such that the SAME sky renders
   the same star brightness across stack builds; MUST keep B7
   byte-identical via default plumbing (e.g. the new mode defaults off
   until approved, or reproduces m=0.00090 exactly on the canonical
   stack); ladder + panels; star_shell + star metrics decide
   objectively, user approves the look.

C. North-star robustness (continue as capacity allows): the pipeline
   should judge ANY dropped-in dataset honestly. The lights set is the
   standing testbed (NOT approved, massive known issues: treeline glow
   band above the mask, reddish high-noise corners, glow-dominated gate
   FAIL — regen: run_pipeline 07-02-26 && solve_field && spcc, chunks
   installed). Candidate process fixes must be data-general (e.g.
   foreground-aware background modeling, corner chroma handling) — no
   set-specific patches. Also queued small: capture SPCC K factors
   into a log/json automatically at spcc time (they were grep-lost
   once).

RULES (README has the full contract): one knob per experiment, control
bracketed; measurement kills a hypothesis -> dead end into NOTES with
numbers BEFORE trying anything else; gate thresholds NEVER loosen
(scope changes need explicit user ratification); corridor + star-shell
metrics are REPORTED/WARN context, never silently gated; aesthetic
changes need the user's eyes on judgment panels before any bake;
objective fixes with pass/fail metrics may commit; after ANY script
change re-verify B7 byte-identical (all four artifacts) or document
exactly why it legitimately changed and get the new render approved;
NO session/stream/ladder tags in script comments (plain standalone
descriptions; history lives in git); background long runs and keep
working; preserve stacks per experiment (cp to tagged names); keep
NOTES.md current as you go — IN ITS REFACTORED SHAPE: update STATUS /
design / knob-provenance / dead-ends / ledger IN PLACE, add new dead
ends to the registry with their numbers, and NEVER append
chronological session narrative (that is what git history is for).

SUCCESS CRITERIA: (1) audit passed with numbers recorded (or the
mismatch root-caused); (2) StarNet-ONNX either WORKING with validated
layers + panels awaiting judgment, or a dead end with exact findings;
(3) the anchor is data-stable with B7 reproducibility intact (or its
dead end written); (4) any lights-set process fixes are data-general
and measured; (5) NOTES STATUS + README + bandaid ledger + memory
updated — every surviving divergence still carries its removal
condition; (6) repo clean, committed, and this file deleted with a
fresh NEXT_SESSION_PROMPT.md if work remains.

Remember the user's standing directive: the acquisition checklist (ISO
800, <=13s subs, matched flats per focal, no moon, dithering) is worth
more than all remaining processing work combined — surface it whenever
image quality is discussed, and never bandaid what photons must fix.
