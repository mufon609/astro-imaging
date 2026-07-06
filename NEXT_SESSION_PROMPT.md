# Prompt for the pipeline-inspection session (copy-paste below the line)

---

Read `~/Desktop/astrophotography/NOTES.md` fully before touching anything —
it is the source of truth: pipeline design, every measured lesson, and the
dead ends already ruled out (do not re-attempt them). Environment facts are
in auto-memory (Siril 1.4.4 as user flatpak — `flatpak run
--command=siril-cli org.siril.Siril -d <dir> -s <script>`, .ssf scripts must
live under $HOME not /tmp, 4-core arm64 / 7.7GB RAM, exiftool + numpy +
GraXpert available, no astropy).

GOAL of the photo: a crisp, natural Milky Way from session `07-02-26`, set
`set-03` (21×25s ISO200 @ 37/38mm, no usable flats → self-flat path): black
background, visible MW gas structure, sharp shining stars. Remove: moonlight
glow, lens vignette, noise. FULL FRAME — the current 250px crop must be
eliminated by solving the rim/edge behavior, not by hiding it. The small
foreground branch (bottom-left corner) must stop driving decisions: mask it
in measurements, never let it force crops or recipe contortions.

Current state: `./scripts/run_pipeline.sh 07-02-26 set-03` runs end-to-end
(self-flat path: unregistered median → isotonic gray V(r) gain → per-frame
seqsubsky → divide → registration reference sweep → stack → post from
`50_postprocess.ssf.tmpl`). `scripts/bg_qa.py` grades final previews
(whole-frame block map + radial ring metrics) and runs inside `run_post`.
Last candidate (`results/candidate_v4.jpg`, unapproved): rings/vignette/
black background good (QA PASS, bg R=G=B=17), but stars washed out and
smokey, and it relies on the crop.

TWO DELIVERABLES, in order:

1. PER-STAGE INSPECTION, built into the pipeline. First write an
   expectations table into NOTES.md: for every stage (calibrated frame,
   seqsubsky output, self-flat gain, divided frame, registration, linear
   stack, then each post operation individually), state what its output
   SHOULD look like and which metric verifies it. Then make the pipeline
   auto-produce per stage: (a) a small inspection JPEG with one CONSISTENT
   autostretch so stages are visually comparable, (b) stage-appropriate
   metrics (levels, bgnoise, radial luminance+chroma profile, star count/
   FWHM where relevant), (c) PASS/WARN against the expectations table.
   Collect it all into one browsable per-run report
   (`results/inspect_<set>_<timestamp>/index.md` or .html) so the user can
   judge every step, not just the final image.

2. A CONTROLLED EXPERIMENT HARNESS, then use it. A script that takes ONE
   parameter and a value list (always bracket the current value, e.g. 0.3 /
   0.5 / 0.7), reruns ONLY the affected stages from a pinned input, and
   emits side-by-side outputs plus a metric table, then stops for user
   judgment. Every experiment starts with a written hypothesis: "changing X
   should affect Y because Z" — no multi-knob changes, no unbracketted
   values pulled from thin air. Use the harness on the open defects in this
   order: (a) star quality — why are stars washed out/smokey in
   candidate_v4? isolate: autostretch clip/target, satu, GraXpert's star
   handling, JPEG quality — one at a time; (b) full-frame rim behavior so
   the crop can be removed (every background estimator extrapolates in the
   outer zone — solve with measurement, not cropping); (c) noise last
   (denoise currently shifts the radial profile ~1 count and is out of the
   chain — find placement/parameters that pass the gate or leave it out).

RULES: never commit a recipe/aesthetic change before the user approves its
output visually; objective technical fixes with pass/fail metrics may
commit. Single-variable discipline is mandatory. When a measurement kills a
hypothesis, write the dead end into NOTES.md before trying anything else.
Extend `bg_qa.py` as needed but never loosen a threshold to make a result
pass. Keep every processing decision and verdict in NOTES.md as you go.
