# BACKLOG

Open work: what it is, why it matters, and the test that closes it. Completed work
is not carried here — it lives in the operating docs and in `git log`.

**Items are keyed by SLUG, never by number.** Reference one by slug from code or docs — e.g. ``BACKLOG:`render-ladder` ``. Numbered items were the previous scheme and
they failed twice, silently: items 19 and 20 were closed and removed, their numbers
were reused for unrelated work, and seven code/doc sites went on pointing at the
wrong content with nothing to catch it. A slug cannot be recycled by accident, and a
reference to a deleted item is greppable.

An item earns its place by mattering to the REPO. Per-dataset findings live in
`datasets/<session>/<set>/`, mechanism lessons in
[`docs/dead-ends.md`](docs/dead-ends.md), tool facts in [`TOOLS.md`](TOOLS.md).
Anything unintelligible, superseded, or true of only one wiped dataset is deleted
rather than carried.

---

## `removal-conditions` — the register (contract-mandated)

Every divergence from the standard workflow carries a removal condition
(`CLAUDE.md`). **A condition nobody re-checks is a divergence that never ends** —
that has already cost real work: `star_shape_profile.py`'s condition had fired,
nothing re-checked it, and the stale metric invented a false anomaly a whole session
chased. Re-check on a tool version change, on a rig change, and before working any
item below.

| divergence | retires when | status |
|---|---|---|
| `anomaly_audit.py` in-house streak kernel | a tool detects/classifies streaks | **not fired** — no Siril or ASTAP mechanism (`cosme`/`find_hot` are defect correction). Standing check: an extreme-elongation QA flag ADJACENT to an audited crossing is the same object until shown otherwise (a missed entry frame was user-caught this way) |
| `star_shape.py` two-frame duplication | Siril exposes a headless single-image tilt | **not fired** — `tilt`/`inspector` are script-NO, and Siril cannot sequence one frame |
| `star_stations.py` fixed-station `findstar` medians | a tool reports a headless LOCAL star-shape map | **not fired** — `seqtilt` is centre-vs-corners and blind to the drift-aligned band this exists for |
| fitted lensfun entry for the 24-70/4 S @ 70 | an upstream entry measured for THIS unit, or a chain consuming the model another way | **not fired** — re-fit per rig/lens/focal and after every `lensfun-update-data`. x86 re-fit CONFIRMS the incumbent (≤0.47 px difference, within fit noise); numbers in `qa_work/lens_fit.json` |
| lensfun user-DB strip of this lens's `<vignetting>`/`<tca>` | darktable honours a style's lens `op_params` | **not fired** — measured ignored on 5.4.1; re-verify per darktable bump with `verify_lens_card.py` (grid control + uniform card; the card ALONE is vacuous) |
| per-set sky flat, de-skied (`build_sky_flat.sh --desky`) | a matching REAL flat for the set | **not fired** — the validated flatless route. `--desky` removes the alt-az-fixed sky term the drift cannot reject; it is not optional alongside the per-frame background step |
| GraXpert `-correction Division` synthetic flat | a matching real flat exists | **not fired** — not adopted; vignetting-only fallback |
| 16-bit in three instruments (`coverage_probe.sh`, `run_frame_qa.sh`, `fit_lens_model.sh`) | the leg stops terminating in an integer/8-bit product | **not fired** — each exemption is stated in `check_bitdepth.sh` with the reason its precision is capped downstream anyway |
| ~~unpinned neural stages in the render tier~~ | — | **RETIRED, not fired: there was no divergence.** MEASURED bit-identical per stage (StarNet2 also across thread counts, Cosmic Clarity denoise, Siril's stretch/asinh/pm), so byte-identity is the available bar and nothing needed pinning. Neither binary exposes a thread/seed flag anyway. Numbers in `docs/dead-ends.md` |
| ~~`frame_metrics.json` CFA-sampled FWHM (Bayer-inflated, relative-only)~~ | — | **RETIRED, condition fired and honoured.** `run_frame_qa.sh` debayers at convert, so `register` measures the green layer at full resolution and absolute FWHM is real. The inflation the caveat warned about, measured one-knob on 20 frames of a 2.5s ISO1600 set: CFA 2.564 px / roundness 0.825 vs debayered 2.350 px / 0.850 — **+9.1% FWHM**, and the mosaic depresses roundness too. Records written the old way keep the caveat in their own `method` string; july23's absolutes stay inflated and relative-only |
| `run_undistort_groups.sh` group composition (one extra interpolation pass) | free disk ≥ the single-pass peak (~231 MB/frame) | **FIRED** — 933 G against ~90 G for 400 frames, so `run_undistort_pipeline.sh` is always reachable and the route is dormant. Keep the script (a bigger corpus can re-arm it) but stop treating it as a live route |

---

## `render-ladder` — the render tier's remaining tiers, user-gated

The first tier is BUILT (`scripts/stack/render_tier.sh`: separate → denoise the
starless → stretch → screen-recombine, every pixel op and every measurement a
tool's, gated by a ratified `render` block) and one render is user-approved. What
remains is the LADDER around it and the harness it feeds.

- **L1 background level** — per-frame `subsky 1` is the SHIPPED default (`--desky`),
  adopted on registry grounds (stack-level-only leaves a structured residual). The
  open question is now a CHALLENGE to a default, not a choice between unknowns:
  on-stack vs per-frame, one knob, preservation of the frame-filling UNRESOLVED
  STARLIGHT deciding (`docs/dead-ends.md` terminology entry — it is stars, not dust).
- **L2 denoise strength** — the proven chroma killer. Objective instrument is the
  `noise_split.sh` structured term, never whole-frame `bgnoise`.
- **L3 stretch ladder** — GHS/`ght` arms against the current `mtf`, compared at a
  MATCHED background landing so curve shape is the knob, not brightness.
- **L4 thresholded `satu`.**
- **Riders:** seed `datasets/GENERIC.json` (still the `{"render": {}, "why": {}}`
  stub) with the six current knobs and a per-knob class-risk note; first
  `baseline.json` via the no-regression harness; per-arm output tree
  (`web/results/<session>/exp_<param>_<stamp>/`) and the `<final>_stages/` labeled
  sequence, both binding requirements the tier does not yet emit;
  `judgment_package.py` re-wire (its PNG8 pairing predates the 16-bit-only policy).
- **Two known limits:** a set can carry only ONE ratified `render` block (keyed by
  name), so two kept looks are not expressible; and a mono set STOPS loudly — the
  luminance-only variant is unbuilt.

One knob per arm, hypothesis pre-registered, judged on full-frame lossless PNG16.
**Closes when** an approved, re-baselined render comes out of a laddered arm.

## `render-reproducibility` — CLOSED: the tier is bit-reproducible

**Measured, so this is done.** Two identical runs of each stage, compared with Siril
`isub` (all-nil = bit-identical): StarNet2 via `starnet -stretch` — identical, and
identical again across thread counts (default 28 vs `setcpu 1`, cross-compared);
Cosmic Clarity denoise (`--disable_gpu`, separate mode) — identical; Siril's stretch
+ `asinh -human` + `pm` recombine — identical. Nothing needed pinning, and neither
binary exposes a thread/seed/device flag to pin with.

**A number this corrected.** The 1.34% "run-to-run floor" that motivated this item was
a misattribution: it came from two render records read as a same-arm repeat, where the
old record logged neither its linear source nor its knob provenance. It is gone from
`web/serve.py`, and the render colour check now reports an EXACT shift with no
NULL-below-floor verdict — because with a deterministic chain there is no floor to
hide an effect under, and between two ladder arms off one stack any difference is the
knob. Mechanism + the "a floor is a measurement, not a subtraction" lesson:
`docs/dead-ends.md`.

Thread-count invariance holds for BOTH neural stages: StarNet2 at siril's default 28
threads vs `setcpu 1`, and Cosmic Clarity at 28 vs `OMP_NUM_THREADS=1` — bit-identical
each way and cross-compared. So the determinism is not an artifact of one machine
state, and a rig with a different core count reproduces the same bytes.

## `learned-deconvolution` — unmeasured, and the tool is installed

`render_tier.sh` skips deconvolution on three grounds that all hold — classical RL is
a measured dead end on in-exposure trailing, BlurXTerminator is not installed,
GraXpert's is the immature path. The fourth was never checked:
`/opt/cosmicclarity-6.6` ships `SetiAstroCosmicClarity` with
`deep_nonstellar_sharp_cnn_radius_{1,2,4,8}`, beside the denoiser the tier already
drives, and the registry explicitly does NOT dead-end a learned deconvolver.

The mainstream runs deconvolution with stars PRESENT, so it goes before the
separation. **Test:** one knob, non-stellar sharpen on the linear SPCC stack vs none,
bracketed by a same-arm repeat, judged on `star_stations.py` majFWHM per station +
`seqtilt` + the user's eyes at 1:1. The hypothesis under test is OBJECT detail — a
symmetric sharpener cannot de-trail an elongated PSF. Until it runs, the skip is a
hypothesis and the docstring says so.

## `calibration-evidence` — the de-sky work's unfinished evidence

`--desky` shipped as the chain default on measured grounds (flat odd plane
4.84%→1.98% set-01, 7.82%→2.42% set-02; vignetting held ≤0.12%; PRNU correlation
0.999951). Three pieces of evidence are still missing, in priority order:

- **The odd-component instrument has no script.** The measurement that justified the
  default exists only as numbers in an `experiments.jsonl` sentence, so it cannot be
  re-run — and `build_sky_flat.sh`'s built-in gate is still corner-vs-centre, which
  the registry entry written alongside it calls SELF-FULFILLING for exactly this
  defect ("judge it on the FLAT's odd component, not the stack's corners"). Either
  the odd term becomes a script whose every pixel op is a tool's (Siril `stat` on
  quadrant crops gives it without in-house pixel maths), or the gate stops claiming
  to check what it does not. The probe's own invocation is preserved: DSC_8647/8/9 →
  `convert` → `calibrate -dark` → `load pp_c_00001` → `save before` → `subsky 1` →
  `save after`.
- **Which arm is CORRECT still rests on estimator arithmetic.** The 3.11%
  differential star-flux plane proves the two calibrations DIFFER; only the
  derivation says de-skied is right, and the Gaia check was structurally impossible
  (trailed stars at 17″/px). **The test that needs no catalogue:** within one set the
  drift carries every star ~1500 px across the sensor, so stack the FIRST third and
  the LAST third separately, match the same stars between them, and fit measured flux
  against sensor position. The correct calibration makes a star's flux independent of
  where it landed.
- **A with/without judgement pair on finals** — both flats exist for set-01/02, so
  this is stageable now. Unresolved-starlight preservation is the metric, the user's eyes decide.

Related and open: **SPCC order-robustness is UNTESTED, not verified.** Inserting the
background step ahead of SPCC moved K_G −1.20%/−1.48% and K_B −0.47%/−0.80% on
unchanged star counts — larger than the chain's own recorded K scatter (0.006).
Confounded, because the de-skied arm also removes a real ~3% object tilt. Clean test:
SPCC the SAME stack with and without an on-stack background step only.

## `walking-noise` — open gap, class-gated

Faint DRIFT-ALIGNED streaks visible at native 1:1 and below whole-frame statistics: a
sensor-fixed pattern (readout FPN + residual warm pixels) dragged into lines by
coherent un-dithered drift. Rejection and cosmetic correction both measured NULL —
it is sub-sigma STRUCTURED signal, not discrete outliers. First quantification
(`noise_split.sh`): drift-phase term ≈0.34/0.48/0.42 ADU (R/G/B) per ~199-frame half,
against ≈1.0/1.5/1.2 ADU total static structure.

One measured CONTRIBUTOR is gone at the source: 16-bit master darks stored a
sensor-fixed ±0.5 ADU pattern subtracted into every light (0.2889 ADU RMS against a
0.4213 floor, +21%), fixed chain-wide and enforced by `check_bitdepth.sh`. **Do NOT
count that as a measured reduction** — the stack-level A/B cannot resolve it (the
chain's run-to-run variation is ~10× the effect). Whether the streaks shrank needs
`noise_split.sh` on a group-built pair.

**Gated on the class recurring** (an un-dithered untracked set; dithering is the
acquisition-side fix and removes the driver). First-contact levers: matched
shutter-mode darks; then drift-axis-aligned pattern removal or an AI denoiser weighed
against preservation of the unresolved starlight — a bandaid, last resort.

## `native-solve-and-sip` — two probes, in order

- **`platesolve -localasnet` on the mildly-trailed class.** The solver dead-end was
  measured on roundness-0.615 frames; july23 measures 0.80. If Siril's own blind
  solve handles this class, `solve_field.py` gains a native sibling (the external
  route stays for heavily-trailed data). One stack, one probe, record either verdict.
- **Then Siril-native SIP undistort vs the darktable warp.** Siril 1.4 fits SIP and
  `register -disto=` consumes it — a DIFFERENT SIP source than the index-constrained
  fit the registry killed. This is the fitted-lens-model removal-condition test with
  a concrete native route. One knob, judged on `seqtilt` off-axis + drift-axis
  stations + full-frame finals. Precondition: the probe above must solve this class.

## `star-neutral-colour` — the narrowband gap

SPCC-narrowband equalises O3=Ha and erases the O3 sphere; Siril has no single command
for a star-colour-neutral balance. Headless path identified and the tool half
confirmed on 1.4.4: measure mean star colour in the examine layer → apply a diagonal
`ccm`. UNTESTED design — do not cite as a method. Run it against a bracket (SPCC,
Nightlight) when a narrowband corpus arrives.

## `siril-1.5` — one load-bearing migration risk

1.4.4 is current stable; 1.5.0 is dev master. The trigger is a version bump, not the
rig (already x86).

- **RISK, now load-bearing: `starnet`/`seqstarnet` are REMOVED in 1.5.0-dev**,
  consolidated behind `pyscript StarNet.py`. `render_tier.sh` calls `starnet`, so a
  1.5 bump breaks the shipped render tier. Migrate before bumping.
- **Adopt on 1.5:** the native `mask_*` subsystem plus `-mask` on
  `denoise`/`rmgreen`/`epf`/`rl`/`sb`/`wiener` — the first native path to
  region-confined ops without a hand-rolled blend.
- **Retirement candidates:** `healpix` (lists the NESTED pixels overlapping a solved
  image — what `spcc_cone.py` hand-rolls; needs a check that its list maps to the
  zenodo chunk names) and `eqcrop ra1 dec1 ra2 dec2` (the natural consumer of a
  framing record's RA/Dec form).

## `guards-and-ci` — nothing runs the guards

`check_bitdepth.sh` says "run it in CI / before a release" and no runner exists; the
web session smoke test added to it inherits that. Also open: the bit-depth check is
per-FILE, so a builder that already emits `set32bits` in one generated `.ssf` passes
even if a newly added emission omits it — per-block granularity needs the
printf/heredoc blocks split on the `> "$X.ssf"` boundary every builder here uses.
Deferred deliberately: a fragile parser is worse than a stated limit, and the limit is
printed in the guard's own OK line.

## `flatpak-race` — serialize or harden the Siril invokers

MEASURED on x86: two rapid-fire `siril-cli` loops running concurrently died after
~10 min with `bwrap: Can't get type of source /run/user/1000/.flatpak/…/tmp` —
flatpak tears down the per-app instance dir when one short-lived instance exits as
another starts its sandbox. One occurrence in ~150 paired invocations; probabilistic,
kills the caller mid-chain under `set -e`, and the failing script prints nothing.
Not a data or Siril bug.

Practice adopted: ONE siril-loop job at a time, globally. Hardening (pick one, as its
own change): a shared `sir()` with a bounded retry on the bwrap signature, or an
flock-serialized invoker every script sources — shared code either way
(`calibrate_light.sh` is the precedent). Retires when flatpak fixes the instance-dir
lifecycle, or Siril invocations stop being per-frame process spawns.

## `web-jobs-filter` — DIAGNOSED, one-line fix

USER-OBSERVED: starting a job made other sessions' jobs repopulate the Run page. The
mechanism is in the code: `web/index.html` filters on `M.session`, which LAGS a fetch
(`loadSession` sets `SESSION` synchronously, then awaits `M`) and falsy-defaults to
SHOW ALL; the running-strip a few lines below already uses `SESSION`. Use `SESSION` in
both and never default to show-all. **Closes when** starting a job on a session page
with another session's records present leaves the table showing only this session's
rows, at start, during, and at completion.

## `web-culled-frames` — one surface for every excluded frame

USER-ORDERED: the Sky Objects section becomes **Culled Frames**, the single
examination surface for every frame the pipeline excluded, grouped by CAUSE — sky
objects (anomaly audit) as one subset, frame-QA defect-side auto-culls as another,
hand-ratified `recipe.json` excludes as a third. Each entry shows frame + sequence n,
set, cause with its metrics, and the record it traces to. The existing culled rollup
MERGES into it. Selection surfaces only — any per-frame preview is Siril-made.
**Closes when** after a chain run with auto-culls the page lists every excluded frame
under its cause and the separate Sky Objects entry is gone from the grouped rail.

## `framing-radec` — reproduce a drawn frame after a stack rebuild

The capture side, the verification and the diagnostic consume side are built and
exercised: a drawn rectangle becomes
`datasets/<session>/framing_<product>.json` carrying BOTH coordinate conventions (the
measured y-flip trap) plus WCS RA/Dec corners, `verify_framing.py` stamps it with
Siril `crop`+`stat`, and `finish_render --crop-record` applies a VERIFIED record to
the LINEAR stack before solve/SPCC/stretch, refusing unverified records and canvas
mismatches.

UNBUILT: deriving the rect on a REBUILT canvas from the record's RA/Dec corners —
today a canvas mismatch is refused, not re-derived. Siril 1.5's `eqcrop` is the
natural consumer. **Closes when** a drawn box renders to a final matching it AND the
record reproduces that framing after a stack rebuild.

## `route-recommendation` — the last wiring on the distortion route

The route is validated, scripted, and the chain already routes by fingerprint
(`run_set_chain.sh`: tracked → standard, fixed+wide → undistort). Remaining:

- **Wire the vignetting-off assertion into `lens_preflight.py --require-profile`.**
  `verify_lens_card.py` exists and passes on x86 (grid control fires, uniform card
  corner-vs-centre 0.000 ADU) but nothing calls it from the preflight — today it is a
  manual step, so a darktable/lensfun bump can silently reintroduce double-corrected
  vignetting.
- **Per-lens facts re-derive at the next new lens/body/focal:** confirm lensfun
  coverage, interpolation behaviour and crop factor before first use. Any focal not
  fitted rides the community entry until fitted (`fit_lens_model.sh` per focal). A
  community profile can be right at the corner and wrong paraxially — the drift-axis
  station measure is the backstop `seqtilt` cannot provide.
- **Run the two-window drift solve live on a boundary-regime camera-raw corpus** —
  the fingerprint's precise instrument has been self-tested but not exercised where
  the cheap trail-vs-roundness check cannot decide.

## `aircraft-rejection-retest` — prove the aircraft actually rejected

The "satellites stay" policy was ratified on satellites and july23 recorded **no
aircraft**. july31/set-03 has one — both audit objects open on `DSC_5151` at
33.3/37.2 deg PA, the two-parallel-trails signature of a single airframe — crossing
`DSC_5151..5158`, 8 of 500 frames. The user ratified KEEPING it on the stated
mechanism: the trail MOVES, so any pixel carries it in ~1 frame of 500, which is the
minority per-pixel sigma rejection removes. That mechanism is sound but is an
argument, not a measurement — `check_stack_rejection.sh` guards the rejection CLAUSE,
not the rejection OUTCOME.

**Closes when** set-03 is stacked twice — the ratified stack, and a control with
`DSC_5151..5158` excluded — and the two are differenced (Siril `isub` + `stat`) along
the aircraft's track. Nil residual on the track = rejection did its job and the frames
are free depth. A visible trail or a level step = the keep was wrong, and it becomes a
cull with its numbers. Cheap: one extra 492-frame stack, no new tooling. More data is
always obtainable, so a cull that buys certainty is not a loss.

## `capability-gaps` — real capabilities the pipeline lacks

Each lands as a measured declared delta when its gate opens.

- **Full-size dual-band** — native Ha + 2× drizzle of OIII instead of downsampling
  OIII to Ha's half size. Gated on measured dither coverage (the per-frame
  `dither_phase_frac` record exists).
- **LRGB join** — `compose` REFUSES a `luminance` member, because L joins after both
  parts are stretched and this compose-then-render flow cannot express a nonlinear
  step. `rgbcomp -lum=` is the headless mechanism when an L corpus arrives; the CLI
  `-lum` blend colour space is undocumented — resolve before first use.
