# Fresh-session prompt — RESEARCH: the manufacturer's embedded lens-distortion model as the optical-state source

Read `CLAUDE.md` first (read order, binding rules — including standards-first
for architecture). This is a RESEARCH session: primary sources plus on-rig
probes of real frames. No pipeline changes, no fixes; the deliverable is a
report.

## Why this research exists

The undistort route needs a distortion model per OPTICAL STATE (focus
recalibrates every session; states differ between nights — measured 4.07 px
corner disagreement under a shared model, `cross_night_state_difference`).
The in-house route to that model — hugin fits from star correspondences —
just failed its corner-support pilot two ways (commit 75340bb): corner
control points are unreachable without a degenerate fit (a SIFT matching
limit on aberrated corner stars), and the fit procedure reproduces to only
~3 px, the size of the 2.99 px defect it exists to remove.

`TOOLS.md` has long recorded, unpriced: **Nikon's own distortion
coefficients ship in every NEF** (exiftool decodes them; no headless Linux
tool applies them). If those coefficients are per-shot and applicable, the
manufacturer's calibration replaces the entire fitting problem — per-shot
means per-state automatically, and the hardest in-house component of the
route dissolves. This must be known regardless of outcome.

## The questions, in order of decisiveness

1. **Is the embedded model per-STATE or static?** The decisive question.
   Probe REAL frames on this rig (raws staged under `sessions/*/`):
   exiftool dumps of the distortion-related MakerNote tags for the Z6III +
   NIKKOR Z 24-70mm f/4 S — across frames within one set, across sets of
   one night, and across nights (july31 vs aug06 span a known state
   difference). If the coefficients vary with recorded focus
   distance/state, per-shot-ness is proven on this project's own data; if
   identical everywhere, the source is a static per-lens/per-focal table (a
   community-profile equivalent — still worth pricing, no longer the
   per-state answer).
2. **What exactly is the model?** Tag names, the polynomial's form, its
   normalization/reference radius, and its valid domain — specifically
   whether it is defined out to the frame corner (the in-house fits fail at
   ρ = 1.80, normalized by half the short side; a manufacturer model that
   covers its own sensor's corners is the entire point). Does the block
   also carry vignetting/TCA (which must be separable — distortion-only is
   enforced doctrine)?
3. **What can DECODE it fully?** exiftool's support level (numeric
   coefficients vs opaque binary), libraw, and any other reader. Verify on
   the rig's actual NEFs, not from docs alone.
4. **What can APPLY it headlessly on Linux?** The application gap is the
   recorded blocker. Price every route:
   - darktable's "embedded metadata" lens-correction method — its format
     support matrix at 5.4.1 and current master (does it reach Nikon Z
     NEFs, or only DNG/other makers?);
   - the DNG path: Adobe's converter embeds Nikon's correction as DNG
     opcodes (WarpRectilinear — a PUBLIC, documented model in the DNG
     spec); which headless Linux tools apply DNG opcodes; what the NEF→DNG
     conversion costs (tooling, Wine, batch, fidelity);
   - conversion into the existing lensfun/ptlens slot: can Nikon's (or the
     DNG opcode's) polynomial be mapped into the ptlens form the current
     warp already applies — exactly or to a stated accuracy at ρ = 1.80?
     This route reuses the entire existing warp chain and only replaces the
     fit.
5. **Prior art**: lensfun/exiftool/RawTherapee/ART/darktable issue trackers
   and forums for Nikon Z embedded-correction extraction or conversion;
   anyone who has mapped these coefficients before. Cite everything.
6. **Validation plan if viable** (design only, do not run): the instruments
   already exist — apply the embedded model to real frames via the chosen
   route, then `member_separation.py` cross-pairs against the fitted-model
   arms and the cross-night pair; the compose gate's thresholds
   (PASS ≤ 0.35 px) are the acceptance bar. State the one-knob experiment
   sequence that would adopt or kill this route.

## Discipline

- Primary sources with URLs; every claim labeled DOC / MEASURED (on-rig
  probe) / COMMUNITY / HYPOTHESIS. Real-frame probes are diagnostics and
  encouraged; nothing writes into the pipeline, the lensfun DB, or any
  record other than the report and ledger.
- The in-house fit apparatus is context, not the subject: do not extend it,
  do not re-litigate its pilot. If the embedded route is viable it REPLACES
  the fit; if partially viable, state exactly which part survives; if dead,
  state the mechanism and the fitting/(c)-class alternatives inherit.

## Deliverable

`EMBEDDED_LENS_MODEL_RESEARCH_report.md` at the repo root, committed:
answers to the six questions in order, the per-state verdict with the
on-rig evidence, the application-route table with costs and the free-tools
constraint stated per route, prior art cited, and the designed validation
sequence. A ledger entry (`embedded_lens_model_research`) with the verdict.
Stop at the report.
