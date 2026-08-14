# TOOLS.md — the astrophotography toolkit, by pipeline tier

A tool **audit**, not a prescribed chain. For each pipeline tier: what the
tier does, the options, when/why to pick each, and the alternatives —
filtered for what runs on the **rig** (x86-64 Kali, Intel i7-14700K, 28 cores,
31 GB RAM, 1.8 TB NVMe, **no NVIDIA GPU**, headless-preferred — the full
environment is in `CLAUDE.md`, the installed inventory in
`scripts/setup/manifest.tsv`). The pipeline is a
TOOLKIT: pull the right tool per dataset + goal, each choice a measured
experiment. Current as of mid-2026.

## How to read this — the three tool CLASSES + the constraint columns

Every tool falls into one of three classes, which decides how cleanly it
fits our headless, orchestrate-not-hand-roll model:

1. **Native Siril command** — runs headless via `siril-cli -s` (or
   `pyscript`), free, deterministic, zero friction. The default substrate.
2. **Standalone CLI binary** — GraXpert, RC-Astro (BXT/NXT/SXT), StarNet2,
   ASTAP, Cosmic Clarity CLI. Headless-clean (own command line), some paid.
   Driven as a subprocess or a Siril script.
3. **Siril `pyscript` ecosystem** — splits by **where the pixel mechanism
   lives** (the resolved tool-vs-hand-roll test: mechanism LOCATION, not
   provenance or author reputation):
   **Class-2 drivers** (`RC-Astro/*`, `CosmicClarity_*`, `GraXpert-AI`,
   `StarNet`) `subprocess` a real compiled binary → genuine tools, headless-clean,
   same category as our `solve_field.py`. **Class-1 numpy-inside** (VeraLux suite,
   SyQon Prism, SCUNet, DBXtract) do the pixel math in the script's own
   numpy/scipy/pywt/torch → the mechanism IS numpy; admissible only as a sanctioned
   alternative with a removal condition, never relabeled "a tool," and most are
   **GUI-mandatory PyQt6 with no headless path** (slider-only → not batch-drivable
   even under Xvfb). Only dual-mode Class-1 scripts (Statistical_Stretch, SyQon
   Prism `--no-gpu`) run headless.

Constraint shorthand used below — **Cost** (FREE / PAID / FREEMIUM) ·
**Runs** (siril-native / CLI / pyscript-GUI / GUI-app) · **Linux** (✅ /
⚠ workaround / ❌) · **CPU** (✅ CPU-fine / 🐢 CPU-slow / needs-AVX2) ·
**Headless** (✅ via -s or CLI / 🖥 needs Xvfb).

**Orthogonal to all tiers: the TOOLS measure, and the repo records.** Quality numbers
come from the tools' own analysis, driven headless and captured to the dataset's record
— Siril `register` regdata / `stat` / `seqstat` / `findstar` / **`seqtilt`**, the solver
and SPCC logs. The in-house layer around them only orchestrates (`inspect_stage`,
`star_shape.py`, `spcc_run`), records, and — in the one sanctioned case where no tool
provides the mechanism — detects (`anomaly_audit`: culls nothing,
removal-conditioned; its RECORD is load-bearing — the groups builder derives its
dwell floor from it).
It never re-derives a measurement a tool already gives; when it did, the metric was
circular and lied (`docs/dead-ends.md`, trap 3). Which tool measures what is mapped
per tier below.

---

## Tier 0 — Acquisition

Not a software tier, but it outranks every tool: acquisition quality is the
real lever (the acquisition checklist, `docs/dead-ends.md`). No processing tool recovers
photons you didn't collect or fixes a focal-length step mid-set.

## Tier 1 — Calibration & Integration (stacking)

Bias/dark/flat calibrate → register → integrate → one linear master.

| Tool | Cost | Runs | Linux/CPU/Headless | When & why |
|---|---|---|---|---|
| **Siril** (calibrate/register/stack, `seqextract_HaOIII`, drizzle) | FREE | siril-native | ✅ / ✅ / ✅ | **Default.** One integrated FOSS workflow, scriptable headless, 32-bit, drizzle + Bayer-drizzle, dual-band line extraction. What our `run_pipeline.sh` orchestrates. |
| **PixInsight WBPP** | PAID | GUI-app | ✅ / ✅ / ❌ | Most control + best-automated weighting/rejection; the reference. Use for a cross-check or if you live in PI. Not headless-friendly. |
| **Astro Pixel Processor (APP)** | PAID | GUI-app | ✅ / ✅ / ❌ | Excellent mosaic/normalization + light-pollution modeling; strong batch. A stacking alternative when Siril's normalization struggles on big mosaics. |
| **ASTAP** | FREE | CLI | ✅ / ✅ / ✅ | Fast astrometric stacker + solver; good for a quick headless stack or as the solver (Tier 2). |
| **DeepSkyStacker** | FREE | GUI-app | ❌ (Win) | Legacy/simple; no reason over Siril here. |

**Pick:** Siril for the headless pipeline. **Flatless sets** → the researched
synthetic routes:
GraXpert `-correction Division` for vignetting-only correction (x86 official; Siril's
native `subsky` is subtraction-only — empirically confirmed on 1.4.4), or a Siril
sky flat ONLY when the field is not frame-filling faint (else it bakes in and
attenuates the unresolved starlight). **MEASURED LIMIT (2026-07-26): GraXpert's AI Division shares
the sky flat's enabling condition** — on a frame-filling-MW field it absorbed ~2/3
of the extended structure even at max smoothing (probe numbers in
`docs/dead-ends.md`; classical `-preferences_file` grid interpolation untested) —
so on that class the per-set sky flat remains the flatless route, and improving
it is the lever — a flat's shape reaches the delivered object ~1:1 (the flat
differential), so a better flat pays out one-for-one on the object. A real flat
is the divergence's removal condition, not an instruction to go shoot one. **The sky flat is strictly PER-SET (user-ratified rule): a
flat calibrates ONLY the exact frames it was built from** — its low-order term
carries the source set's own sky gradient, so cross-set application IMPRINTS that
gradient (measured ±6% L-R tilt on set-03 under set-01's flat vs ~1–2% under its
own; `docs/dead-ends.md`); a multi-set combine calibrates each member set with its
own flat before composing. Pinned builder with validation gates:
`scripts/stack/build_sky_flat.sh` (dark-subtracted, CFA, un-registered, winsorized
— the winsorized rejection measured star specks 101 → 0 vs a pure median).
**Bias** = skip on CMOS (matched darks carry it; dark-scaling
is invalid because CMOS dark current isn't constant across exposure), a synthetic
constant offset if a flat needs one. A real flat stays primary. PI/APP only as
reference or for a normalization edge case.

**Workflow specifics (headless, verified against the Siril 1.4.4 tag source):** masters
bias/dark `-nonorm`, flats `-norm=mul`; lights `-norm=addscale`. **Rejection by sub
count:** ≤6 percentile (`p`), ~7–50 winsorized (`rej w 3 3`), >50 GESD (`rej g 0.3 0.05`
— fraction+significance, NOT sigmas), large+gradients linear-fit (`rej l 3 3`).
Bare `rej n n` defaults to **Winsorized** and default light normalization is
addscale — settled by `help stack` on the rig's own 1.4.4 (was doc-UNCERTAIN).
Weighting `-weight={wfwhm|noise|nbstars|nbstack}` (unified — the old `-weight_from_*`
flags are REMOVED and will error migrated scripts). Registration: `-2pass`→`seqapplyreg`,
homography for wide fields, lanczos4+clamp. **`-framing=min` under-delivers on
mutually ROTATED members**: its axis-aligned rectangle kept 5.50 of the true
15.25 Mpx all-members common area (36%) on a 50-member two-window compose —
measured full-depth sky discarded; for framing decisions on rotated composes,
probe true per-pixel coverage with `scripts/qa/coverage_probe.sh` (constant
frames through the stored transforms, `stack sum`) and crop the `max` compose
to a verified coverage threshold instead. **Drizzle is a `register` option, not `stack`**
(CFA-drizzle 1×/pixfrac 1.0 for OSC; upscale only if sampling+dither justify —
`docs/dead-ends.md`, drizzle entry). **Two real gaps vs PixInsight WBPP:** no Local
Normalization and no PSF-Signal-Weight equivalent (our audit layer can supply a PSFSW
proxy — rank `(Σflux·Σmean_flux)/(σ_noise·M*)` within a dataset; it reproduces PSFSW
to R²≈95–99% from SNR², SNR and star count — PixInsight ImageWeighting doc). Comparison re-verified 2026-07-25 against
Siril 1.4.4 (confirmed still current stable) and PixInsight 1.9.4 / WBPP 2.9.0 — both
gaps still open (WBPP 2.9.0's new Frame Selection step is opt-in metric CULLING, not
weighting; Conejero: "we consider ESD the best rejection algorithm currently
available"). Vendor fork recorded: WBPP Auto starts GESD at ≥15 subs vs Siril doctrine
>50; and PI designates CFA drizzle the recommended OSC colour path while Siril's
canonical script demosaics at calibrate — full stage-by-stage audit in
[`docs/stacking-vs-official-pipelines.md`](docs/stacking-vs-official-pipelines.md).

## Tier 2 — Registration reference / plate solving / astrometry

Blind-solve → WCS for SPCC + annotation. Our dead-end: Siril's *internal*
star-match solver fails ultra-wide **trailed** fields.

| Tool | Cost | Runs | Linux/CPU/Headless | When & why |
|---|---|---|---|---|
| **Siril 1.4 native astrometry.net** (`platesolve -localasnet -blindpos -blindres`, SIP, auto-crop-wide) | FREE | siril-native | ✅ / ✅ / ✅ | **Now native in 1.4** (Dec 2025) — replaces our custom solve for ROUND-STAR (tracked) data. VERIFIED it does NOT drop-in replace `solve_field.py` for the TRAILED class: Siril feeds astrometry.net its own `findstar` (PSF-fit) star list, which is exactly the detection our dead-end says fails on trailed stars (ours feeds trail-robust PEAK centroids). Mitigation to TEST on x86: `setfindstar -relax=on` accepts non-star-shaped/trailed objects — may let native localasnet solve the trailed class too. See the verification note below. |
| **ASTAP** (`astap_cli -f file.fits`) | FREE | CLI | ✅ / ✅ / ✅ | **Fastest** local blind solve, but **NOT a trailed-field escape**: ASTAP's own docs say *"star streaks due to tracking errors … will be ignored and solving could fail"* and list *"stars are reasonably round"* as a solving precondition — it shares the roundness limitation. **Wide-field DBs (auto-select): W08 for FOV>20°** (~330–580 kB bright-star cut) **+ G05 for FOV>6°** (D-series usable ≥0.6°); G17/H17/H18 deprecated. `-z` downsample; FOV-blind auto-learn caps at 10° so **pass `-fov` explicitly for ultra-wide**. Use ASTAP for the NON-trailed / moderate-FOV class, not the trailed one. |
| **astrometry.net** (`solve-field`, our `solve_field.py`) | FREE | CLI | ✅ / ✅ / ✅ | Our current workaround — blind solve from PEAK centroids, which is what beat the trailed-star problem. Keep as the fallback until native/ASTAP are verified on trailed data. |

**Pick:** native localasnet for round-star data; **keep `solve_field.py` for
the trailed/ultra-wide class** (verified: native feeds Siril's PSF findstar on
the GREEN layer — the failing detection — which is a sufficient reason on its
own; the FOV>5° detection auto-crop is *"Ignored for astrometry.net solves,"* so
`-nocrop` is moot for `-localasnet` and only the PSF-fit findstar detection cuts
against trailed fields). On x86, run the empirical test — `setfindstar -relax=on -roundness=0.1
-maxR=<large>` + `platesolve -localasnet -blindpos -blindres` on a real trailed
stack vs `solve_field.py` vs ASTAP; if native/relaxed solves reliably, retire
the custom script; else it stays the trailed-field tool. (`-relax=on` only
loosens quality checks — more false-positives — it does NOT convert findstar's
round-PSF model into a peak-centroid detector.) **A tool-first alternative to
the hand-rolled peak detector — `image2xy` (astrometry.net's own extractor):**
source-verified it has NO shape/roundness gate at all (peak-in-connected-
component, closer to our peak-centroid than to a rejecting fitter) — so it does
return trailed sources. But it is NOT a clean win: the trail-relevant knobs
(`-a` saddle / `-p` significance / `-m` max-deblend-size) are NOT exposed by
`solve-field`'s CLI (need the standalone binary), a symmetric Gaussian match
kernel (`-w`) is SNR-mismatched to elongated PSFs, and `-a` saddle can FRAGMENT
one rippled trail into spurious detections. It's a **testable A/B, not a
retirement** (BACKLOG). **Trailed-class robustness ranking (mechanism + numbers:
`docs/dead-ends.md`, trailed-solve entries):** (1) astrometry.net fed our own
peak-centroid xylist — MOST robust, and confirmed the *intended* shape-blind
override (solve-field with an xylist runs no pixel extraction; the matcher is
geometry-only — but ADD `--no-remove-lines --uniformize 0` or two list-level
filters still thin the xylist), which VALIDATES `solve_field.py`; (2)
`image2xy` xylist — shape-blind, A/B-pending vs (1); (3) native `-localasnet`
and ASTAP — LEAST (both PSF-fit / roundness-gated; ASTAP's docs: "streaks …
will be ignored"). VERIFICATION detail below the table.

**Verification — does Siril 1.4 native solve replace `solve_field.py`?**
PARTIALLY. Both now use the astrometry.net ENGINE (Siril's *internal*
star-matcher was what failed on ultra-wide; localasnet bypasses it — that
half is native now). BUT the star DETECTION differs and that was the other
half of the failure: Siril localasnet "extracts the stars from your images
[with `findstar`] and submits this list to `solve-field`" (Siril docs) — i.e.
PSF-fit detection, which the `solve_field.py` docstring explicitly built
around ("Siril's PSF-fit detection ... fail to feed the matcher on this
[trailed] data"; ours uses trail-robust peak local-maxima). `solve_field.py`
also carries edges native lacks as first-class options: foreground-masked
detection (treeline/glow peaks poison the matcher), `--central` low-distortion
crop for warped wide lenses, and field-width-derived index-scale selection.
Net: native REPLACES for tracked/round-star data; for the trailed class it is
unverified and likely needs `-relax=on` tuning or the custom script. (This is
a MECHANISM verification from Siril docs + our source + the rig's command
help; no empirical solve was possible at the time — the image data was deleted.
The empirical test above is what settles it and has not been run.)

### Tier 2b — DISTORTION-aware registration (the wide-field UNTRACKED class)

A global star alignment smears edge stars on a wide field that drifts far. The
cause is **radial lens distortion**, not field rotation — for an ideal rectilinear
lens a pure camera rotation is EXACTLY a homography, so the projective part is
already right and the fix is **undistort → homography**, not a local/elastic warp
(mechanism + numbers: [`docs/wide-field-untracked-registration.md`](docs/wide-field-untracked-registration.md)).

| Tool | Cost | Runs | Linux/CPU/Headless | When & why |
|---|---|---|---|---|
| **Siril `register -disto=`** (`image` \| `file <path>` \| `master`) | FREE | siril-native | ✅ / ✅ / ✅ | **The ONLY native distortion route**, and the only one buildable on the identical tool. Consumes SIP terms from a prior `platesolve`/`seqplatesolve -order=2..5`; producer side can export a distortion master via `platesolve -disto=<file>`. **Syntax `-disto=file <path>` — two tokens** (`-disto=file=<path>` errors; `-disto=image` needs the loaded image solved). **`seqapplyreg` carries it** ("Distortion data was found in the sequence file") even though `-disto=` is absent from its own help — so `-2pass` + `seqapplyreg` works. Siril also READS an astrometry.net-injected TAN-SIP header. **MECHANISM PROVEN; the model source is the gap** (see the blocker below). |
| **Siril `register -transf=`** | FREE | siril-native | ✅ / ✅ / ✅ | shift \| similarity \| affine \| **homography** (default) — **global only, no local/elastic/TPS**. Siril recommends homography for wide fields. Nothing above homography exists to try; it is already exact for pure rotation. |
| **Siril multi-point registration** (`pss`/`register_mpp`/`stack_mpp`) | FREE | siril-native | ✅ / ✅ / ✅ | **NOT a route for this class.** 1.5-dev only (absent from 1.4.4), scoped to planetary/lunar **atmospheric seeing**, and the model is **piecewise TRANSLATION only** (affine/homographic components explicitly discarded). No `-disto=`/`-transf=`. |
| **PixInsight StarAlignment** (thin-plate-spline distortion correction) + DynamicAlignment | PAID | GUI-app | ✅ / ✅ / ❌ | The reference true-local distortion model. **x86/GUI — audit-only.** |
| **Astro Pixel Processor** (distortion-model registration) | PAID | GUI-app | ✅ / ✅ / ❌ | A practitioner A/B on the same data class (250×5 s, R5 + Sigma 40 mm f/1.6) reports Siril's global alignment smears corner stars where APP's distortion model does not. **x86/GUI — audit-only.** |
| **Sequator** (Lens / Complex distortion models) | FREE | GUI-app | ❌ (Win) | Its manual names our exact symptom (distortion → "false trails" worst at corners) and its models are gated on FIELD WIDTH, not tracking. First-party envelope: acceptable only to **~5 min of drift at 20 mm-equiv**. No Linux/headless — the METHOD transfers, not the tool. (It does NOT segment the sky and locally align — that common claim is refuted by its manual.) |
| **Hugin `cpfind`/`cpclean`/`autooptimiser`** (fit the lens FROM OUR OWN FRAMES — `scripts/darktable/fit_lens_model.sh`, installed by `install_lens_model.sh`) | FREE | CLI | ✅ / ✅ / ✅ | **The model source IN PRODUCTION for this rig's lens — adopted after a measured WIN at instrument and full depth** (centre station 5.30 → 3.67 px majFWHM at 168 frames, all stations within 3.4–3.8 px — the perpendicular-station level; seqtilt truncated-mean 3.27 → 3.06 px, a different statistic (see the floor entry's measure note); stars +10%; approved on the user's eyes). Fits the panotools radial model from star correspondences BETWEEN frames — the mechanism the SIP dead-end leaves viable (no catalog, no per-frame solve); its a,b,c paste DIRECTLY into a lensfun `model="ptlens"` entry — **MEASURED by probe: no rescaling happens or is needed, because lensfun uses hugin's own normalisation, HALF THE SHORT SIDE** (seeded star-field fixture at sensor geometry through the production warp; fitting the four installed models at once gives RMS 4.47 px for half-short-side vs 18.3 px half-long-side and 22.2 px half-diagonal, and a free normalisation lands at 2000 px against 2020 — supersedes the earlier source-reading claim of internal rescaling). **The consequence is load-bearing: the frame CORNER sits at ρ = 1.80 while `cpfind`'s control points reach only ρ ≈ 1.0, so the cubic extrapolates 80% past its support at the corners and two fits that are interchangeable inside the field can diverge by 6–8 px outside it — measured between the aug06 per-set fits, and the cause of the cross-set combine's corner star doubling (`docs/dead-ends.md`).** Installed into the live lensfun user DB so the darktable chain is untouched. The fit procedure is scripted as `fit_lens_model.sh` (proven step by step; the script's first as-written run is the next fit). Traps, all measured: SIFT CPs are weak on star fields (feed Siril-autostretched copies, `--fullscale`; 0 CPs on a 1500 px pair, ~10/pair near) and `align_image_stack`'s correlation search dies at ~130 px steps (3 CPs) — use `cpfind` on the full multi-image project (399 CPs/53 pairs) + **`cpclean`** (263 survive); **pin `v` at the astrometrically-solved hfov** — a free v collapses degenerate (v→0.93°, a=98); stage the optimize (ypr → +abc → +de); verify the override is not a silent no-op (darktable never fails loudly) via the lens_preflight difference proof. **The d,e stage is DEGENERATE and cannot be used — measured on every preserved fit** (aug06/set-02 d=6.3e6 e=−4.5e7 with a=282 b=1120 c=4733; july31/set-01 d=5.6e6 e=−1.4e7; aug06/set-01 d=−177 e=+378; aug06/set-03 d=−122 e=−524; only aug06/set-00 stays bounded at d=+1.8 e=+24.0 and disagrees with the absolute measurement by an order of magnitude). Mechanism: hugin fits d,e jointly with per-image y,p,r on BETWEEN-FRAME correspondences, where a centre shift is nearly degenerate with per-image yaw/pitch — an absolute-catalogue fit has ONE global affine instead and identifies the centre cleanly (`docs/untracked-widefield-standards.md`). It maps to lensfun's `<center>` element, which DOES exist and work in 0.3.4 — but the joint refit that would have used it puts the centre at (−6,+14) px, i.e. ZERO: a centred ptlens model describes this lens to a 0.27 px median once the per-frame nuisance is a HOMOGRAPHY rather than an affine (`scripts/qa/fit_ptlens_joint.py`; the affine-nuisance trap and its retraction are in `docs/dead-ends.md`). |
| **The camera's EMBEDDED distortion model** (Nikon `DistortionInfo`) — investigated, **NOT a usable source on this rig** | FREE | metadata | ❌ apply / ✅ read / ✅ headless read | **MEASURED over all 7,702 NEFs in the archive (4 nights, 23 set/dark dirs): the block is STATIC — exactly TWO distinct coefficient triples exist, and 7,355 frames (every light of every night) carry the SAME one**; the second appears in one dark dir only. It latches per power-up, not per focus state, so it cannot be a per-state source — and its entire dynamic range between the two triples is **0.808 px at the frame corner**, against a ≤0.35 px compose PASS gate. Structure: 3 radial coefficients, rational/2²⁰, in a private 84-byte block; the polynomial form is DOC for **DNG** WarpRectilinear and the Nikon→DNG mapping is unverified COMMUNITY. **Only `exiftool` decodes it** — exiv2, LibRaw and dcraw all fail (measured on-rig). **Nothing applies it headlessly on Linux for Nikon**: darktable and RawTherapee both implement embedded-metadata correction for Sony/Fuji/Olympus/Panasonic/DNG, no Nikon; the one live route is DNG opcodes via a proprietary non-native converter. The community decode effort for this block is open and unsolved. Read in the light of the reverted per-set doctrine (`docs/dead-ends.md`): "it is a shared model by construction" is no longer a disqualification, but "static, 0.808 px of range, unappliable headlessly" still is. |
| **darktable + lensfun** (`darktable-cli --style <s> --style-overwrite`) | FREE | CLI | ✅ / ✅ / ✅ | **THE ADOPTED FIX for this class — measured WIN at mid/edge, in production, shipped — with one measured CLASS LIMIT: the community profile's paraxial error writes an along-drift CENTRE BAND into a far-drifting set** (shipped render centre station 5.30 px / roundness 0.480 vs 3.60 / 0.706 perpendicular; the no-model control's centre is its BEST region — `docs/dead-ends.md` paraxial-band entry). **Fixed on this rig by a FITTED entry, PINNED per lens@focal** (`scripts/darktable/lens_models.json` — the authority; a per-set fit is a CANDIDATE promoted by an explicit act). The per-set variant was tried and REFUTED at its root (`docs/dead-ends.md`): its founding number was a compose artifact, the 0.47 px equivalence bound is exceeded 7-23x by REFITS OF ONE SET (0.36-6.30 px), and per-set models broke the combine — 2.99 px corner disagreement within a night, 5.34 px across nights, star doubling failed by eye, against 0.14-0.93 px under one model. The chain installs the pinned entry per run; the preflight and `lensfun-update-data` are the per-rig setup steps. An OFFICIAL *measured* lens profile, immune to the index-sparsity that kills a per-frame SIP fit. darktable must be built against Lensfun (Debian's is). **THE PARENTHETICAL THAT USED TO SIT HERE — *"Debian's RawTherapee is NOT — it doesn't link lensfun, so its auto-match is unavailable"* — LOOKS FALSE, AND IT WAS CLOSING A ROUTE.** MEASURED: `apt-cache show rawtherapee` → **5.12-2+b1**, `Depends: … liblensfun1 (>= 1:0.3.4) …`. **A Debian package does not carry a VERSIONED hard dependency on a shared library it does not link** — `dpkg-shlibdeps` generates that line by scanning the built binary's ELF `NEEDED` entries, and the versioned form is that mechanism's signature. **INSTRUMENT LIMIT, stated because this is the exact shape that produced the SCAMP and PSFEx errors in the other direction: this is PACKAGE METADATA, not a running `ldd`** — RawTherapee is not installed here. The completing check is `ldd $(which rawtherapee) | grep lensfun` after an install, or a contents lookup. **Rated high-confidence-FALSE rather than settled.** Whether RawTherapee is *worth* anything on this route is a separate question nobody has asked; what is recorded is that the stated ground for excluding it does not appear to hold. On july14, Siril `seqtilt` control → corrected → community 168-fr control: **off-axis aberration 0.57→0.31→0.25 px**, stars 5,095→10,707→11,805, 54/54 register; the SHIPPED fitted-model render measures **3.06 px truncated-mean / 12,976 stars / sensor tilt 0.31 (10%)** (the band leaving the statistic, not the floor moving). Sharpness vs the community model is NULL (truncated mean FWHM 3.20→3.28) and a radial model cannot fix the one-sided term (0.50→0.42→0.51 across the community arms; the fitted model's cut to 0.31 was paraxial model error, not tilt) — claim carefully. **The style is pinned in-repo** (`scripts/darktable/*.dtstyle` + `install_styles.sh`, verified to reproduce the warp to 0.000 px) — no GUI step. **`--style-overwrite` is REQUIRED**, else the style is silently ignored. **Correction set: a style's lens op_params are IGNORED — `modify_flags` included** (measured: flags 0–7, method/inverse flips, a blanked lens string → byte-identical output; `docs/dead-ends.md`) — and darktable's per-image default set includes **vignetting**, which FIGHTS a master/sky flat (the measured double-correction bowl, `datasets/july14/set-01/qa_work/gradient_qa.json`); **distortion-only is enforced in the lensfun user DB** (`install_lens_model.sh` strips this lens's vignetting/tca; verify with a uniform-card warp — corner medians == centre). **ICC is per-LEG, do not cross them: the 32-bit float production leg ships the TIFF untagged and exports `--icc-type LIN_REC709` (measured identity, ratio 1.0000 at every level and channel); `--icc-type SRGB` belongs ONLY on the 8/16-bit probe legs where it matches Siril's own tag** (`docs/dead-ends.md` ICC entry; CLAUDE.md environment). **The style carries ONLY the enabled bit; `focal`, `scale`, `camera` and `lens` are all baked but IGNORED — darktable re-detects them from EXIF and recomputes the autoscale (MEASURED: focal 70 vs 24 give opposite-sign warps; scale 1.046 vs 0 vs 1.5 are identical to 0.000 px; a swapped lens string gets that lens's own profile). So ONE style is camera-, lens- and focal-general.** **The same mechanism is a trap: darktable NEVER FAILS** — an unmatched lens gets NO correction, silently (0.000 px over 413 stars, exit 0, nothing in the log), and a wrong-but-present lens gets a wrong model just as quietly. It cannot be relied on to degrade loudly: the CHAIN must assert EXIF camera+lens+focal against the DB per set and STOP on a miss ("did the warp happen" is not enough — it passes the wrong-lens case). Debian's lensfun 0.3.4 lacks the Z6III → **`lensfun-update-data`**, which ships in **`liblensfun-bin`** (NOT `python3-lensfun` — that package exposes only DB-path helpers and no matcher); it writes the upstream DB to `~/.local/share/lensfun/updates/version_1`, a **machine-local, untracked** path the route depends on and which does not migrate with the repo — re-run it per rig. There is **no lensfun query CLI** in Debian (`lenstool` is unpackaged), which is why `scripts/stack/lens_preflight.py` proves the correction by asking darktable rather than by querying lensfun. Deterministic in pixels; between two measured runs its TIFF differed by one metadata byte — never gate this route on a file hash. Ordering is load-bearing: calibrate in SENSOR space → debayer → warp → register. **DECENTRING — what this stack can and cannot express, all verified against the installed 0.3.4:** the radial models (`poly3`/`poly5`/`ptlens`) are functions of radius alone and cannot represent a left-right asymmetry by construction; `acm` (Adobe Camera Model) is the only lensfun model carrying Brown's tangential pair (k4,k5) and **does not exist in 0.3.4** (zero occurrences of `ACM` in the v0.3.2 and v0.3.4 sources, none in the installed `liblensfun.so.0.3.4`; nine in v0.3.95, and there only in the correcting direction). The `<center>` element IS present and applied in 0.3.4, and darktable honours it — but the measured lens decentring is ~180–210 px in x and ~210–240 px in y, and installing that centre on coefficients fitted for centre=0 is a LOSS at every sign (2.589 → 4.235–7.610 px residual). Both routes are registered in `docs/dead-ends.md`; the only one that can work is a JOINT refit of a,b,c about a free centre. |

**Why `-disto=` is not the production route:** its mechanism is proven, but it needs
a trustworthy model, and every per-frame catalogue fit is a registered dead end
(Siril's matcher at ~36° fields; astrometry.net's SIP at wide index scales —
`docs/dead-ends.md`), which blocks WCS-reprojection equally. The model gap is closed
UPSTREAM instead: a measured profile applied before registration — the
darktable+lensfun row, with the entry FITTED from the set's own frames where a
community entry is inadequate (the Hugin row) — needing no `-disto=` at all. Nikon's
own coefficients ship in every NEF (exiftool decodes them) but sit in a private block
no headless Linux tool applies — a better model if darktable's "embedded metadata"
lens method ever reaches it, not a blocker today.
**SCAMP is NOT covered by this kill:** it fits TPV distortion by cross-matching a
DENSE reference catalogue (e.g. Gaia) against a prior WCS — a different model source
from astrometry.net's sparse-index SIP — so it earns its own named test (two fits of
the same fixed lens agreeing to ~1 px) before the reprojection route reopens.
**"Unpackaged on this distro" IS WRONG AS WRITTEN, and the error is the registered
`apt-cache policy` shape — it reads the BINARY index only.** MEASURED here:
`apt-cache policy scamp` → `Candidate: (none)`, but `apt-cache showsrc scamp` →
**Version 2.10.0-2, Debian Astro Team**, and this rig's `deb-src …bookworm` line is
configured and uncommented, so `apt-get source scamp` resolves and extracts. Same
precedent as the PSFEx row below, which the same check got wrong the same way.
**AND SETTLING AVAILABILITY DOES NOT SETTLE THE CAPABILITY — MEASURED FROM THE
SOURCE, AND THE ANSWER IS NO.** `object_tilt.py`'s removal condition names SCAMP as
the candidate for a *POSITION-DEPENDENT* photometric solution. SCAMP 2.10.0's own
`src/preflist.h` carries **five** astrometric order/degree parameters —
`DISTORTION`, `DISTORT_DEGREES`, `DISTORT_GROUPS`, `DISTORT_KEYS`,
`FOCDISTORT_DEGREE` — and on the photometric side only `PHOTOM`, `PHOTOMFLAG_KEY`,
`SOLVE_PHOTOM`, `MAGZERO_KEY/OUT/INTERR/REFERR`. **There is no photometric analogue
of `DISTORT_DEGREES`.** `src/photsolve.c` confirms the shape: `photsolve_fgroups`
*"Solve a different system for each instrument"*, keyed on `photomlabel==instru`,
with zero points as the unknowns. **So SCAMP's photometric solution is a SCALAR per
exposure per photometric instrument, not a function of position within a frame** —
it does the catalogue-free half of that condition and not the position-dependent
half, so the condition would NOT fire even with SCAMP built. Recorded because the
useful disposition is "the named candidate does not do the thing", which is a
different fact from "blocked on availability". Context worth carrying: the current
SCAMP manual contains five occurrences of "photometr" and no photometry chapter.
**GUARD, so the correction does not overshoot into a different wrong claim: this is
NOT "SCAMP cannot do photometry".** Solving a separate system per instrument with
zero points as the unknowns IS **relative photometric calibration across
overlapping exposures, catalogue-free** — a real capability, and a good one. The
precise form is: **it does the catalogue-free half and has no position-dependent
term at all.** Write it any looser and the next reader skips it for a problem it
would solve.
**AND THAT CAPABILITY LANDS ON A GAP STATED IN A DIFFERENT ITEM.**
BACKLOG:`intake-culling` records, for transparency drift, *"No per-FRAME form — the
instrument works on sub-stacks"*, and for cloud, *"per-frame background is NOT
recorded"*. A per-exposure relative zero point across overlapping exposures **is** a
per-frame transparency measure, taken on the stars' own flux rather than on
background level — which is the property that row already prefers. Our consecutive
frames overlap ~99% (drift ~1000 px across 6064), and the catalogue input SCAMP
needs is `source-extractor` 2.28.2, INSTALLED. **CANDIDATE, not a solution:** it is
not built (source-reachable, above), its behaviour on trailed stars is unprobed,
and no arm has been run. Recorded because the connection only became visible once
the capability was narrowed correctly.

**WCS-reprojection faint-signal notes (if the model gap ever closes):** SWarp's
**`SUBTRACT_BACK=Y` is the DEFAULT and must be turned OFF** — it subtracts a sky
model from every input and would eat a frame-filling star field. SWarp conserves flux only
with equal-area output projections (`FSCALASTRO_TYPE` = NONE|FIXED); its author
puts the TAN-safe limit at ~10° of field, so a ~30° field should not default to TAN.
In astropy `reproject`, `reproject_interp` is **not** flux-conserving (and offers no
Lanczos kernel); `reproject_adaptive` has `conserve_flux` and is documented as more
accurate under strong distortion / large sky areas; `reproject_exact` is an exact
drizzle valid at any FOV but slow. `reproject_and_coadd`'s `match_background` models
only a constant additive offset and forfeits the absolute zero point. astropy is
x86-gated.

**How this class is MEASURED — Siril `seqtilt` for the whole-frame radial/asymmetric
terms, plus fixed drift-axis stations for the band term.** `seqtilt` is the tool's
own spatial star-shape analysis and the only headless door to one:

| command | headless? | reports |
|---|---|---|
| **`seqtilt <seq>`** | ✅ *"Can be used in a script: YES"* | `Stars`, `Truncated mean[FWHM]`, **`Sensor tilt[FWHM]`** (best vs worst corner = the ASYMMETRIC term), **`Off-axis aberration[FWHM]`** (centre vs corners = the RADIAL term — *this* class's defect) |
| `tilt` | ❌ *"Can be used in a script: NO"* | same, single image |
| `inspector` | ❌ *"Can be used in a script: NO"* | a nine-panel corner/centre mosaic — visual only, no numbers |

Driven + recorded by `scripts/qa/star_shape.py`. `seqtilt` needs a SEQUENCE and Siril
cannot build one from a single frame, so a lone stack is presented as a two-frame
sequence of itself. Both terms are FWHM DIFFERENCES in px (bigger = worse) — not a
roundness ratio, and not `findstar`'s per-star "roundness" (FWHMy/FWHMx); do not mix
the three. **Never re-derive this by binning a `findstar` list by radius** — that is
circular and it fails silently (`docs/dead-ends.md`, trap 3).

**`seqtilt` is BLIND to a drift-aligned band** — centre-vs-corners improves as the
centre degrades toward the corners' mean (measured 0.57 → 0.25 px across renders whose
centre station degraded 4.03 → 5.30 px, and 0.13–0.16 px on instrument stacks with a
4.9-vs-3.5 centre-vs-perpendicular split). The band term is measured by
`scripts/qa/star_stations.py`: Siril `crop` + `findstar` (open gate) at fixed
equal-area stations about the geometric centre, along/perpendicular to the drift axis
taken from the astrometric solves — fixed EXTERNAL geometry, so the trap-3 circularity
cannot bite; the script records medians of the tool's own per-star fits
(`qa_work/star_stations_*.json`). Removal condition: an official tool reporting a
headless LOCAL star-shape map.

## Tier 3 — Photometric colour calibration

**TWO `findstar` PHOTOMETRY FACTS, both MEASURED, and getting either wrong is
worth more than the signal any photometric test here is chasing.**

- **`findstar`'s `mag` column is a TOTAL-FLUX magnitude, not a peak one** —
  verified as `−2.5·log10(A·2π·σx·σy)`, offset −0.0001 with MAD 0.0027 over 37
  matched stars. **Nothing in the column name says which it is, and reading it as
  a PEAK magnitude puts the zero point out by 1.76 mag** — about three times the
  size of the effect the photometric work was testing. Check it before building
  any zero point on that column.
- **Siril's `Sat` flag is a HARD-CLIP flag, not a LINEARITY flag, and soft
  non-linearity below the clip is invisible to it.** MEASURED: on one aug06 raw
  the brightest matched star (V_T 1.34) sits **1.77 mag BELOW** the flat zero
  point while its `Sat` flag reads **0**; above V_T 4.5 the ZP-vs-magnitude slope
  is −0.037 ± 0.036 (1.0σ from flat) and above V_T 5.0 it is −0.007 ± 0.066
  (0.1σ). **The direction is the hazard:** a zero point built on the brightest
  stars — the natural choice, since they have the best SNR — is biased FAINT, so
  the mistake manufactures apparent support for a throughput or exposure deficit.
  **Always test ZP flatness against instrumental magnitude; the tool flag will not
  do it for you.** (Frame context, so nobody re-derives full-well from the raw
  integers: these are ×4-scaled 14-bit frames — uint16 with BZERO 32768, green
  plane 969–22845 about a 1047 median — so the brightest pixel is ~35% of full
  well and nothing is hardware-saturated.)

**`split_cfa`'s CHANNEL ORDER CANNOT BE READ OFF `BAYERPAT` — IDENTIFY THE GREENS
FROM THE DATA, MEASURED.** `split_cfa` writes *"four distinct files (one for each
channel)"* with no averaging or interpolation, and `seqsplit_cfa` does the same for
a sequence (prefix `CFA_`). **The trap: `BAYERPAT=RGGB` plus raster order reads as
channels 1 and 2 being the greens, and on this rig THE DATA SAYS 0 AND 3.**
Measured on one aug06 raw by cross-matched star magnitudes — two greens are the
same filter on the same scene, so their pair must agree near zero with the
smallest scatter:

| pair | median Δmag | MAD | n |
|---|---|---|---|
| **ch0 − ch3** | **−0.005** | **0.115** | 706 |
| every other pair | 0.28–0.85 | ~2× the scatter | — |

Corroborated independently on a fresh `convert` + `split_cfa` of one raw: ch0/ch3
share background median **1047.0** and MAD **10.0** against ch1 1038/9 and ch2
1029/8 — pairwise median difference **0.00 ADU for ch0−ch3** against 9–18 for every
other pair — and ch0/ch3 keep 496/504 stars against 349/211.

**MECHANISM, MEASURED AND PREDICTIVE — it is the row order, and the value that
matters is `BOTTOM-UP`.** `ROWORDER` is **not a fixed siril property; it varies by
PRODUCT CLASS.** Measured on this rig: `convert` output, all four `split_cfa`
outputs and `convert -debayer` output are **`BOTTOM-UP`**, while STACKS are
`TOP-DOWN` (and `injected2.fit` carries no `ROWORDER` at all). So `BAYERPAT=RGGB`
describes the image as DISPLAYED while the array is stored bottom-up, i.e. array
row 0 is the displayed BOTTOM row, and a raster reader walking the stored 2×2 sees

    displayed   R G          stored BOTTOM-UP   G B      raster order over the
                G B                             R G      stored block:
                                                         ch0=G ch1=B ch2=R ch3=G

**Greens at ch0 and ch3 — which is what the photometry and the backgrounds
measure.** `TOP-DOWN` would predict greens at ch1/ch2, which is the wrong answer,
so the mechanism reproduces the observation rather than merely being consistent
with it. Same y-origin family as the `boxselect` counts-from-the-top trap and the
crop y-flip trap already registered here.

**STILL UNVERIFIED — the R/B half.** The row flip predicts ch1=B and ch2=R, but ch1
carries MORE stars (349 against 211 after the cut), which runs against expectation
for a reddened galactic-plane field. **The GREENS are settled by three independent
measures; the red/blue assignment is not.** Do not read one as the other.

**Cost if missed: a G1-vs-G2 null would compare RED against BLUE and return a
confident clean answer** — in the one design where that null is the test immune to
every other confound. It surfaced only because the star counts looked wrong, not
because anything checked. **Check `ROWORDER` on the ACTUAL product class you are
reading; a value taken from a stack does not describe a `convert` output.**

**ONE `findstar` SHAPE FACT, MEASURED — `setfindstar -moffat` is NOT a usable
second estimator on this corpus, and it is the only alternative profile the tool
offers.** `setfindstar [ [-gaussian] | [-moffat] ]` is scriptable and runs
headless; the `.lst` gains a fitted `beta` (col 4) and `Profile` (col 15), and
Siril's Moffat branch returns the TRUE Moffat FWHM as a function of β, not a
Gaussian-equivalent width (`src/algos/PSF.c`, 1.4.4). **Two failure modes make it
unusable for any second-moment quantity here, both measured on three aug06 raws
against the identical Gaussian call:**
- **β is UNIDENTIFIED for ~40% of stars.** Siril fits it through a bounded
  reparameterisation, `beta = MOFFAT_BETA_UBOUND * 0.5 * (cos(x₇) + 1.)` — the
  same construction as the axis ratio, and the derivative vanishes at BOTH
  bounds. MEASURED: **39.9 / 41.2 / 42.5%** of accepted stars pile at exactly
  β = 10.000. At this sampling (S ≈ 0.83) a fifth shape parameter has too few
  independent samples to constrain.
- **~10% carry a DIVERGENT second moment.** With `I(r) ∝ [1+(r/α)²]^(−β)`,
  `∫r³I dr` converges only for **β > 2** while FLUX needs only β > 1, and
  `minbeta` defaults to **1.5** — so the fit ACCEPTS stars with finite flux and
  infinite second moment. MEASURED: **10.3–11.2%** sit at β ≤ 2. For those rows a
  `major²−minor² = κ·L²` framing is not mis-calibrated, it is undefined.

Also measured: Moffat mode returns **13.6–15.4% fewer stars** than the identical
Gaussian call, so the two modes do not measure the same population without a
cross-match; and the Gaussian fit reads **6.3 / 7.4% broader** in median
FWHMx/FWHMy, matching the documented direction (a Gaussian fitted to a
wingier profile is pulled outward). **κ is profile-specific** — two profiles with
identical FWHM have very different second moments — so any Moffat A/B needs κ
re-derived under `-moffat` before it is quotable, which the β pathology makes not
worth doing. Numbers and the control that validates the probe environment:
`datasets/aug06/corner_work/moffat_probe.json`.

**THE SENSOR PEDESTAL, MEASURED — a rig constant, and it was ASSUMED at 1024 until
it was not.** **1007.2 ADU** on the 65535 scale, for **NIKON Z6_3, 14-bit**.
Instrument: Siril `stat` on the 328-frame master dark at the lights' own 2.5 s —
the right quantity, since it carries bias plus dark current, which is the additive
non-sky signal a light actually has. **Stable to 0.1 ADU across three nights**
(1007.2 / 1007.3 / 1007.3 over aug06, aug09, july31), so it is a sensor property
and not a per-night value. **Cross-checked by two further instruments sharing no
code: the camera's own EXIF `BlackLevel` reads 1008, and an independent astropy
read of the same master gives 1007.24.**
**WHY IT IS HERE RATHER THAN IN A DATASET RECORD:** it was measured inside one
set's cloud work, and the next person needing a pedestal will not look there — they
will look where the rig facts are, find nothing, and assume 1024, **which is exactly
what happened.** The assumed value understated the sky term by **62%** (26.9 vs the
measured 43.7 ADU on an aug06 background of 1050.9) and therefore overstated the
dilution of a raw background fraction as ~39× where it is **24×**.
**AND THE RULE IT CARRIES: any figure quoted "above pedestal", "above background",
"above bias" or "net of" MUST state its denominator, or it cannot be checked and
cannot be corrected when the reference moves.** This is the offset form of the
register's state-the-denominator rule for counts.

**A MEASURED ZERO POINT FOR THIS CAMERA+LENS, and the structural reason it cannot
settle an exposure question.** **ZP_V_T = 16.754 ± 0.015** (sem; MAD 0.060, n = 33
at V_T > 4.5, none tool-flagged saturated) for **NIKON Z6_3 + NIKKOR Z 24-70/4 S at
70 mm, f/4, ISO 1600, 2.5 s**, single debayered UNCALIBRATED raw, green layer, alt
73.8° (X = 1.0413). Instrument: astrometry.net solves and supplies the catalogue
magnitude via `solve-field --tag-all` (Tycho-2 `MAG_VT` into the `.corr` table),
Siril `findstar` supplies `mag` — read the total-flux fact above before using it.
**WHAT IT CANNOT DO, and the reason is structural rather than a precision limit:** a
zero point is *defined* as whatever reconciles instrumental with catalogue
magnitudes, so it absorbs gain, aperture, transmission, extinction and exposure in
ONE number. Measured flux constrains the PRODUCT (throughput × t_eff) and no
single-epoch photometry separates the factors. Testing a 0.570 mag effective-exposure
deficit needs an independent throughput prediction to better than 0.25 mag, and the
**QE × transmission integral alone is ~0.35 mag** (Bayer green vs V_T, response curve
unpublished) — so the verdict does not even depend on the gain, aperture or colour
terms. **The ZP is measured 33× better than the quantity it must be differenced
against; more photometry cannot help.** The lever that would break it is two nominal
exposures on one night through the same optics, which this corpus does not have —
exposure and night are perfectly aliased.

**FOUR OF SIRIL'S SIX CONFIGURED CATALOGUE PATHS POINT AT FILES THAT DO NOT EXIST,
AND THAT IS ACCEPTED (user-ratified 2026-08-14).** MEASURED — `config.1.4.ini`
lines 18–21 name `catalogue_namedstars`, `catalogue_unnamedstars`,
`catalogue_tycho2` and `catalogue_nomad` under `~/.local/share/kstars/`, and all
four are ABSENT. **The one measured consequence: there is no local NOMAD, so
anything defaulting to it reaches a REMOTE service** — `pcc`'s own help
distinguishes "the remote NOMAD (the complete version)" from a local install, and
`findcompstars -catalog=nomad` is the case already met (`-catalog=apass` is remote
regardless). **Nothing in the current chain reads any of the four**, so it does not
fire today; the owner has accepted the remote lookup and these are DELIBERATELY
UNUSED. They are kstars-hosted with different sources and licensing from the Zenodo
Gaia pair, which is why they were never bundled with it.
**THE HAZARD THAT REMAINS IS THE SHAPE, NOT THE LOOKUP, and it has cost time twice
here:** a config key pointing at a file nobody creates fails as a *blocked
measurement* rather than as a *missing file*. SPCC defaulted to a non-existent
`gaia_photometric.dat` and siril range-read online and **429'd**; the astrometric
Gaia catalogue was discovered the same way. **So if one of these four is ever read,
expect the failure to look like a data bug.** Blanking the four keys — so a future
failure reads "not configured" instead — is a one-line hardening that has NOT been
done.

**TWO CATALOGUE FACTS MEASURED ON THIS RIG, both of which blocked a real
measurement — read before designing anything that needs a star catalogue.**

- **`conesearch` IS GUI-ONLY HEADLESS, and its `help` gives no hint of it.** It
  runs far enough to print its own search geometry (*"centre coords:
  306.653107, 42.539787, radius: 865.668313 arcmin"*) and then aborts the whole
  script with **`execute_idle_and_wait_for_it called headless, this should not
  happen!`** — a string confirmed present in the installed 1.4.4 binary. `help
  conesearch` documents the command fully, `-out=` and `-cat=localgaia`
  included. **This is the THIRD instance of the registry's own pattern** after
  `tilt` and `inspector`: probe before believing a capability exists, even when
  help documents the exact flag you intend to use. (Distinct from the existing
  record of `conesearch` timing out on a 20.6° cone against TAPVizieR — that is
  an online-service limit; this is an unconditional headless abort.)
- **THE ASTROMETRIC GAIA CATALOGUE IS INSTALLED — this row previously said it was
  not, and the correction re-opens a route the row had closed.** MEASURED:
  `~/.local/share/siril/gaia_astrometric.dat`, **1,521,132,640 bytes**, fetched at
  `f0ebea7` with a hash chain and a functional probe (541 matched stars).
  `catalogue_gaia_photo` → `siril_catalogues/spcc` (xpsamp SPECTRAL chunks) is a
  SEPARATE catalogue and both are now present. **The damaging half was the
  downstream clause — *"`-cat=localgaia` has nothing to read even once the
  headless problem is solved"* — which closed a route on a premise that this
  team's own fetch had already falsified.** The headless limit on `conesearch` is
  unaffected and stands; only the has-nothing-to-read half was wrong.
  The Environment line reads "Local Gaia catalogs at
  `~/.local/share/siril/siril_catalogues/` (astro + SPCC xpsamp chunks)" — the
  astro half is absent. **Owner's file, flagged not edited.** Source if it is to
  be fetched: zenodo 14692304, per that same section.

| Tool | Cost | Runs | Linux/CPU/Headless | When & why |
|---|---|---|---|---|
| **Siril SPCC** (spectrophotometric, Gaia DR3 + QE/filter curves + atmosphere) | FREE | siril-native | ✅ / ✅ / ✅ | **Default; obsoletes PCC.** Broadband star-colour truth. Our `spcc_run.py`/`spcc_cone.py` orchestrate it + the local Gaia cone. |
| **PixInsight SPCC** | PAID | GUI-app | ✅ / ✅ / ❌ | The reference implementation; cross-check only. |

**Note:** SPCC is the WRONG step for the narrowband O3 sphere (it equalizes
O3=Ha — dead-end registry). Narrowband colour is Tier 10, not here.

**Tier 3b — POSITION-DEPENDENT photometry (star flats / photometric
self-calibration), audited on-rig.** The question is not "measure a star" — three
tools do that — it is "solve for throughput as a function of FOCAL-PLANE position
across overlapping exposures". Nothing installed here does the second.

| Tool | Cost | Runs | Linux/CPU/Headless | What it actually gives |
|---|---|---|---|---|
| **Siril `psf`** (+ `setphot`) | FREE | siril-native | ✅ / ✅ / ✅ | **The measurement this repo uses.** APERTURE photometry at a FORCED radius (`setphot -aperture=R -dyn_ratio=` outside [1.0,5.0]) against its own LOCAL annulus, one star per `boxselect`, on the 3-layer float cube directly. ~2.4 ms/star. Probed: over boxes 40–160 px the magnitude moves 5e-4 mag (identical to 1e-4 from 50 px up) while the FITTED background B moves 18%, so **the annulus is read from the IMAGE, not the selection**; a 30 px box fails; a failed measure returns `±9.9990`, the tool's own invalid sentinel. |
| **Siril `seqpsf -wcs=`** | FREE | siril-native | ✅ / ✅ / ✅ | **LOOKS like the cross-image answer and is NOT.** It converts the sky coordinate to pixels ONCE and measures that same pixel AREA in every image of the sequence. MEASURED on aug09/set-01's four blocks, one real star: **m = -2.104 in the reference block against +3.55 / +5.05 / +3.63** in the others. `-followstar` needs registration data and does not repair it (+3.55 / +3.87 / +2.86). Unusable on a drifting sequence. |
| **Siril `light_curve`** | FREE | siril-native | ✅ / ✅ / ✅ | Differential photometry of ONE target against averaged comparison stars, over time. Wrong axis — it is a time series, not a position solution. |
| **`source-extractor` 2.28.2** (`/usr/bin`, Debian's name for SExtractor) | FREE | CLI | ✅ / ✅ / ✅ | Installed and WORKS on these sub-stacks: **47,971 objects in 3.1 s**, `FLUX_APER`/`FLUXERR_APER` at several radii in one pass, `BACKPHOTO_TYPE LOCAL`, `ALPHA/DELTA_J2000` from the header WCS. A viable alternative per-image photometer; not adopted because `psf` gives the same measurement on the green layer the rest of the chain uses without a channel-extraction hop (SExtractor reads plane 1 of the cube), and because it does not close the actual gap either. Needs a `default.conv` in CWD or it aborts. **IT REPORTS SHAPE MOMENTS WITH NO UNCERTAINTY, AND THE `ERR*` FAMILY IS NOT IT — the names invite exactly the wrong reading.** MEASURED on the installed 2.28.2 via `source-extractor -dp`: the shape second moments are `X2_IMAGE` *"Variance along x"*, `Y2_IMAGE`, `XY_IMAGE` *"Covariance between x and y"* (and `X2MODEL_IMAGE` *"Variance along x from model-fitting"*), and **no parameter anywhere reports an uncertainty on any of them.** Every `ERR*` parameter is POSITIONAL, in four families that all say *position*: `ERRX2_IMAGE` *"Variance of **position** along x"*, `ERRX2WIN_IMAGE` *"…windowed **pos**…"*, `ERRX2PSF_IMAGE` *"…PSF **position**…"*, `ERRX2MODEL_IMAGE` *"…fitted **position**…"*. **`ERRX2_IMAGE` is NOT the error on `X2_IMAGE`** — it is the centroid uncertainty ellipse, and it sorts adjacent to the moment it does not describe. Consequence: **no installed tool reports a propagated error on a shape moment** (PSFEx gives χ² and per-grid FWHM/ellipticity min/mean/max with none attached; SCAMP gives per-context residual RMS), so the in-house frame-based error model's removal condition is **not** closer to firing. And a propagated PIXEL-NOISE error on one detection is a different quantity from a REALISATION SE across frames — conflating them is the defect the error-model work removed. |
| **SCAMP** 2.10.0 (astromatic) | FREE | CLI | ✅ / ✅ / ✅ | **INSTALLED** — `/home/samsung/.local/bin/scamp`, `SCAMP version 2.10.0 (2020-12-01)`, built from Debian source. The prior "NOT PACKAGED on this distro" was the `apt-cache policy` error: it reported the BINARY repo and was quoted as availability. It is the removal condition for `object_tilt.py` and **the condition still does not fire** — verified on the built binary, not inferred: `scamp -d` offers astrometric `DISTORT_DEGREES`/`DISTORT_GROUPS`/`DISTORT_KEYS`/`STABILITY_TYPE`, while the photometric side has only `SOLVE_PHOTOM`, `MAGZERO_OUT/INTERR/REFERR`, `PHOTINSTRU_KEY`, `MAGZERO_KEY`, `PHOTOMFLAG_KEY` — **no photometric analogue of `DISTORT_DEGREES` exists**, so its photometric solution is a SCALAR per instrument and never the position-dependent field the condition names. Availability and capability are separate facts and only the first changed. |

**And the gap does not matter on THIS data**, which is the load-bearing finding:
a catalogue-free star-flat solution needs the dither to break the low-order
degeneracy, and a translational drift cannot — only the 0.69–3.76°/set of field
rotation does, leaving a 29 px median lever on a 5769 px frame. Compounding it,
a FIXED camera makes the ATMOSPHERE sensor-fixed too, so no sensor-frame fit can
apportion the measured field between flat and sky. Both blockers, the controls
that prove the instrument itself is sound, and the 12-set corpus:
`docs/dead-ends.md` + `datasets/aug09/corpus_object_tilt.json`.

## Tier 4 — Gradient / background extraction (LINEAR, star-ful, early)

| Tool | Cost | Runs | Linux/CPU/Headless | When & why |
|---|---|---|---|---|
| **GraXpert** (AI BGE, or RBF/spline) | FREE | CLI + siril-native | ✅ / ✅ (**BGE is CPU-fast** — inference runs once on a ~240px thumbnail, O(1)) / ✅ | **Default AI gradient removal**, integrated in Siril 1.4 and standalone (`graxpert -cmd background-extraction`; `-cli` deprecated on the installed geeksville fork, while the official 3.0.x docs treat `-cli` as mandatory — flag semantics are BUILD-SPECIFIC, resolve on the pinned official build at x86 bring-up). **`-correction Division` = the headless synthetic-flat gap-filler** (multiplicative; smooth VIGNETTING only — BACKLOG). CLASS LIMIT (dead-end): the AI absorbs frame-filling FAINT nebulosity as gradient — use a plane/off for object-filling fields. |
| **Siril `subsky`** (`-rbf` or polynomial degree) | FREE | siril-native | ✅ / ✅ / ✅ | The retention mode — a first-degree plane removes the gradient class without absorbing localized nebulosity. Our `bgelin plane`. |
| **VeraLux Nox** (pyscript) | FREE | pyscript-GUI | ✅ / ✅ / ❌ | scipy sparse-Poisson gradient solve — a **Class-1 numpy-inside** script (mechanism = scipy, escape-hatch only) and **GUI-mandatory PyQt6** (not headless-drivable). (A prior "Seti AutoBGe" reference is unverified — no such script confirmed in the repo.) |
| **PixInsight DBE / GradientCorrection / MARS** | PAID | GUI-app | ✅ / ✅ / ❌ | DBE = manual sample gold standard; **MARS** (2026) = PI's new AI gradient model. Reference/cross-check. |

**Pick:** GraXpert AI for real gradients; Siril plane for object-filling
fields (the retention rule stands regardless of rig).

## Tier 5 — Deconvolution / sharpening (LINEAR, BEFORE denoise)

**2026 consensus: deconvolution goes early, in linear, BEFORE any noise
reduction** (NR destroys the fine low-contrast detail decon needs; BXT
explicitly dislikes denoised data). Classical RL is a measured dead end on this
data (unstable PSF on in-exposure trailing) — but a LEARNED deconvolver is a
live, installed, still-unmeasured option (BACKLOG:`learned-deconvolution`), and
`BlurXTerminator` "correct only" can even fix the elongated/trailed stars
that were the base rig's core data problem.

| Tool | Cost | Runs | Linux/CPU/Headless | When & why |
|---|---|---|---|---|
| **BlurXTerminator** (RC-Astro, `--correct-only` + sharpen) | PAID $99.95 | CLI (`rc-astro bxt`) + siril-script | ✅ (**Ubuntu 22.04+ "or equivalent"; Kali not vendor-certified — verify**) / **AVX2 (i7-14700 ok); no vendor CPU figures → `--benchmark-all`** / ✅ | **Best-in-class**; standalone **`rc-astro` v1.0.0 CLI** + Siril script, no PixInsight host. `--correct-only` corrects PSF aberration without sharpening → fixes star elongation/trailing. Perpetual license, **CLI free for holders, offline after activation**. Linux GPU = **NVIDIA-CUDA only** → no-GPU rig runs the supported CPU fallback. Call `rc-astro bxt` directly (Class-2); activation + model-cache + flag-capture steps print from `scripts/setup/x86_bootstrap.sh`. |
| **GraXpert deconvolution** (`deconv-obj` / `deconv-stellar` AI) | FREE | CLI + siril-native | ✅ / ✅ 🐢 (minutes CPU) / ✅ | **PRE-RELEASE only — NOT a shipped stable feature.** Official stable is **3.0.2 (BGE+denoise only)**; deconv exists only in the 3.1.0-RC line and the installed **`3.2.0a2` third-party fork** (`geeksville`, not upstream — pin the official build). Real but undocumented CLI (`-cmd {deconv-obj,deconv-stellar}`, flags in BACKLOG); object-mode artifact bug **#243 open and unaddressed**. BXT is the mature path. |
| **AstroSharp** (DeepSkyDetail) | FREE | Win .exe / R-Shiny | ❌ **dead end for us** / — / ❌ | **NOT viable**: TIFF-only with a **<600 KB file cap** (unusable full-frame), **no native Linux**, **no CLI**, C++ (no Python), multi-platform issue open+unresolved since 2023. Drop from consideration. |
| **Cosmic Clarity — Sharpen** (Seti) | FREE (donation) | CLI (folder-batch) | ✅ native Linux / 🐢 (CPU) / ✅ | Free stellar/non-stellar sharpen; leading free BXT alternative, a notch below; CPU-brutal without a GPU. A Class-2 binary driver. **INSTALLED on x86** `/opt/cosmicclarity-6.6` (bin `SetiAstroCosmicClarity`, reports **Sharpen V6.5 AI3.5s**), verified CPU-only `--disable_gpu` (~45s on a 1200px test frame — full-frame is far longer, unmeasured). **Folder-batch I/O, NO --input/--output flags: reads `input/` writes `output/` NEXT TO THE BINARY, ignores cwd** — hence the install is USER-OWNED, and orchestration stages each frame into `input/` (single-run; the shared dir has no concurrency). **CORRECTED 2026-08-03 — IT IS A Qt TOOL AND IT BLOCKS.** The earlier "no gnome-terminal needed" was wrong. It opens a Qt MODAL DIALOG on startup and waits for a click; unattended it hangs forever. MEASURED on an IDLE box (load 1.33) with an EMPTY input dir: blocked the full 115 s at 3% CPU / 3.2 s user time — waiting, not computing. With DISPLAY unset: `qt.qpa.xcb: could not connect to display`, exit 134. `QT_QPA_PLATFORM=offscreen` does NOT help (dialog still created, still unclickable); xvfb-run + xdotool blind-driving Return/space/click did not reach the widget. **Its CLI ARGUMENTS ARE ALSO IGNORED**: `--sharpening_mode "Stellar Only"` was passed and the dialog showed `Both`, and the run did both passes. The dialog's state is the authority. **The non-stellar pass CRASHES on real data** (`ValueError: zero-size array to reduction operation maximum` at chunk 5/36, AFTER the stellar pass completes — and nothing is saved, because the write happens after both). **Operator step that works:** launch with a display, set Sharpening Mode = `Stellar Only`, GPU off, click OK. So this tool is ATTENDED and NOT scriptable; it cannot satisfy the acceptance contract's reproducibility check unless the settings are recorded from the dialog per run. |
| **Siril `makepsf` + RL deconvolution** | FREE | siril-native | ✅ / ✅ / ✅ | Classical RL; our dead-end (unstable symmetric PSF on ≈0 background with in-exposure trailing). Only viable with a good stable PSF. |

**Pick:** BXT (`rc-astro bxt`) if any budget — best quality + `--correct-only`
fixes trailing, CPU-fast (~30–40 s); else GraXpert deconv (free, headless, but
**RC-stage** — measure, watch bug #243) or Siril RL. **Order rule (refined): decon
early-linear, before HEAVY denoise — a strong DEFAULT, not absolute** (Siril itself
recommends a *little* VST NR before RL; and 2026 AI tools tolerate nonlinear-stage
decon — see the process-rule note at the end).

**NO TOOL REPORTS A SUB-PSF TRAIL LENGTH — a closed negative, probed rather than
assumed.** The question is whether any packaged tool measures the in-exposure trail
length `L` directly, which would retire the in-house fixture calibration that
converts trail to anisotropy (BACKLOG:`removal-conditions`, `kappa_transfer.py`).
Answer: no.
- **TRIPPy** takes rate, angle and dt as INPUTS and builds a trailed aperture from
  them; it does not recover `L` from the image.
- **`astride` / `acstools`** target satellite and cosmic-ray trails MANY PSF WIDTHS
  long; a ~1.7 px smear inside a 2.4 px star is below what they detect at all.
- **`source-extractor`'s `A_IMAGE`/`B_IMAGE`** are second moments with NO trail
  model — they report a shape, not a length, and carry no error on that shape
  (its `ERR*` family is the POSITIONAL uncertainty ellipse, a different quantity
  sitting adjacent in the parameter list).
**So the well-formed capability to watch for is not "a tool reports L" — nobody
outside this project wants that — but "a tool reports a SECOND-MOMENT shape whose
bias is characterised", which would make the `(2.3548^2/12)*L^2` identity exact
rather than estimator-calibrated. `source-extractor`'s A/B_IMAGE are the installed
candidate and the open question is thresholding/windowing bias, not availability.**

## Tier 6 — Noise reduction (linear on starless; and/or nonlinear)

**Siril has no GENERAL chrominance-noise reduction — but it does not self-describe
that way, and the earlier wording here ("NO native chrominance-noise tool") is
refuted by the tool's own help text.** MEASURED, `help rmgreen` verbatim:
*"**Applies a chromatic noise reduction filter.** It removes green tint in the
current image. This filter is based on PixInsight's SCNR and it is also the same
filter used by HLVG plugin in Photoshop."* So a reader grepping Siril's command
list finds a tool that calls itself a chromatic noise reduction filter and
concludes this row is wrong. **The defensible form:** Siril's only native chroma
tool is `rmgreen`, which is green-tint removal (SCNR-equivalent) and SINGLE-HUE;
`denoise -indep` is *"denoising each channel separately"*, i.e. per-channel and
not chroma-targeted. **Neither is general chrominance-noise reduction, so the gap
this tier fills is real** — it is the WORDING that overreached, not the
conclusion. Denoise the STARLESS layer (linear preferred), AFTER deconvolution.

| Tool | Cost | Runs | Linux/CPU/Headless | When & why |
|---|---|---|---|---|
| **NoiseXTerminator** (RC-Astro) | PAID $59.95 | CLI (`rc-astro nxt`) + siril-script | ✅ / AVX2, **CPU-light (lighter than BXT; indic.)** / ✅🖥 | **Best + fastest** AI denoise; `rc-astro` v1.0.0 CLI. **Closes the chroma-noise gap:** AI3 has a *dedicated* chroma control (`denoise_color`, independent of the luminance `denoise` — not one global knob). Exact `rc-astro nxt` flag spelling is unpublished → capture with `rc-astro nxt` no-args on x86 (the bootstrap prints the step). Free CLI for holders, offline-after-activation. |
| **Siril `denoise`** (NL-Bayes; `-da3d`/`-sos`/`-indep`/`-mod`/`-mask`) | FREE | siril-native | ✅ / ✅ / ✅ | **Free, headless, deterministic.** Plain NL-Bayes on stacks; `-da3d` refine, `-sos` background artefacts, `-indep` blocky colour, `-mod` blend, **`-mask` (1.5.0-dev) to confine to a region**. **No native chroma mode** (docs still punt to GIMP — gap confirmed in 1.5.0-dev). Clean default when free+headless matters. |
| **DeepSNR 1.2.1 (Linux)** (StarNet author) | FREE | **native Linux CLI** | ✅ / ✅ (self-contained ONNX, **CPU fallback**) / ✅ | **Cleanest free headless denoiser fit** — trained on astro data, bundled ONNX Runtime (no CUDA/TF), built for automation/Siril. v1.2.1 is the **Linux x64-only** build; INSTALLED here at `/opt/deepsnr-1.2.1-0112`. CLI `-m/--model {1=RGB-only,2=default}`; docs say *"intended for monochrome cameras."* Architecture is not stated on the primary source (NAFNet is a third-party attribution). Luminance-vs-chroma behaviour is undocumented — not a citable chroma-gap fill. A Class-2 binary. |
| **GraXpert denoise** (AI, `-strength` + `-batch_size`) | FREE | CLI + siril-native | ✅ / ✅ 🐢 (**CPU-slow — ~14.5 min/48MP, >30 min large frames**) / ✅ | Free AI denoise, in Siril 1.4; `-batch_size 1–32` trades RAM for speed. CPU-slow is the real cost. Timing probe (onnxruntime `CPUExecutionProvider`): 1024² tile in **71 s** → ≈13–14 min extrapolated per 12 Mpx frame. INSTALLED here as 3.0.2 at `/opt/graxpert-3.0.2/GraXpert-linux/GraXpert` — that figure came from a fork build on the retired box, so re-time it before budgeting a run. Fork-CLI quirk (source-verified): the per-command flags (`-strength`/`-batch_size`/`-ai_version`; BGE `-correction`/`-smoothing`/`-bg`) are subparser-registered and HIDDEN from the top-level `--help` — they work when passed alongside `-cmd`. **LEAD (untested): `pip install graxpert[openvino]` claims ~5× CPU speedup on AVX2/VNNI Intel CPUs = the target rig's exact class** — x86 empirical candidate. No luminance/chroma split (single strength knob). |
| **SyQon Prism** (free "Siril Edition" / paid "Deep") | FREEMIUM | pyscript (**Class-1**) | ✅ via Siril / ✅ (Parallax **Nano** is CPU-only) / **✅ headless** (free tier, `is_cli()`) | 2026 neural (PyTorch NAFNet) denoise; numpy/torch-inside (escape-hatch). Free labels are Zenith/Prism-Siril-Edition/Parallax-**Nano** (not "Mini"). The free "Siril Edition" (`mini` model) branches on `siril.is_cli()` and runs headless — no dialog/license gate (an older community build was GUI-only; verify the free-tier headless run on-rig). |
| **Cosmic Clarity Denoise** (Seti, v6.5) | FREE (donation) | CLI (folder-batch) | ✅ native Linux / 🐢 (~7 min CPU) / ✅ | Free AI denoise; CPU-slow; Class-2 binary. **A FREE chroma-noise control exists here** (candidate free fill for the chroma gap alongside paid NXT): `--denoise_mode {luminance,full,separate}` + **`--color_denoise_strength`** (+ `--separate_channels`) — chroma vs luminance, headless. **CORRECTED 2026-08-03: Sharpen is NOT a plain CLI subprocess** — it is Qt and blocks on a modal dialog (see the Sharpen row). Denoise and Dark-Star ARE headless and verified so on this rig: Denoise completes unattended, Dark-Star prints `Non-Windows system using device: cpu` / `All images processed.` in ~110 s. **INSTALLED + VERIFIED on x86** (`/opt/cosmicclarity-6.6`, bin `SetiAstroCosmicClarity_denoise`, reports **Denoise V6.6 AI3.6**): CPU-only `--disable_gpu` works (~21s/1200px), and the free `--color_denoise_strength` chroma path RUNS, but **the knob SATURATES and is effectively binary**: MEASURED on real data, runs at 0.85 and 1.00 are BYTE-IDENTICAL (same md5) while 0.00 differs — so there is no headroom above the shipped 0.85, and WHERE between 0 and 0.85 it saturates is UNMEASURED. (`--denoise_strength` by contrast does work across its range: 0.0 output is byte-identical to the input, 1.0 differs by sigma 0.7-1.0 ADU.) The earlier "29% background noise cut" was one synthetic frame and did NOT establish that the knob is controllable — it only showed the tool does something. Consequence for BACKLOG:`render-ladder` L2: **the chroma knob SATURATES above 0.85, so a LADDER over it is not controllable.** The earlier wording — *"the CHROMA half of that ladder cannot be run through this CLI"* — is true in substance and **is a false-negative generator as written**: read without the preceding sentence in view it says *this CLI has no chroma path*, and it has one. `SetiAstroCosmicClarity_denoise --help` self-describes **`--denoise_mode {luminance,full,separate}`**, **`--color_denoise_strength`** and **`--separate_channels`**. **What cannot be run is a controllable ladder, not chroma** — and in a cell this long the qualifier and the conclusion will not always be read together, which is how a route-closing claim survives at byte 539 of a 4,640-character cell. **OPEN, and it is cheap: `--denoise_mode` takes three values and the record does not say which one the saturation was measured under. If it was `full`, the same knob under `--denoise_mode separate` is UNTESTED** — same frame, `--color_denoise_strength` at 0.00/0.50/0.85/1.00, md5 each output. **If 0.85 and 1.00 diverge under `separate`, the ladder is controllable and L2 reopens.** Not scheduled: L2 sits under the user-gated `render-ladder`. Dark-Star present (models v2.0/v2.1/v2.1c, v2.1c byte-identical to the official asset). **GAP — satellite + super-res do NOT run:** the official bundle's own frozen torch runtime raises `torch._C._sparse has no _spsolve` at startup (the binaries themselves are the official ones; satellite is byte-identical to the GH asset). The community AMD/ROCm rebuild runs them but is a third-party rebuild (geeksville-GraXpert precedent) — NOT adopted. So `anomaly_audit.py`'s streak-kernel removal condition stays **not-fired**: the official detector exists but will not run here. |
| **AstroDenoisePy 0.5.8** | FREE | CLI (`--device CPU`) | ✅ (py) / 🐢 / ✅ | CSBDeep/Noise2Noise; headless CLI; older, below NXT/DeepSNR. |
| **VeraLux Silentium** (SWT wavelet) | FREE | pyscript (**Class-1**) | ✅ via Siril / ✅ / **❌ GUI-mandatory** | `pywt` SWT denoise — **numpy-inside** (escape-hatch, not "a tool") and **GUI-mandatory PyQt6 with no arg vector → not headless-drivable** even under Xvfb. |

**Pick:** NXT (`rc-astro nxt`) if licensed — fastest, best, and AI3's dedicated
chroma path (`denoise_color`) **CONFIRMED** as the chroma-noise fill; else
**DeepSNR** (free, native Linux CLI, CPU) or Siril native `denoise` (headless,
deterministic) or GraXpert (CPU-slow). **For chroma noise specifically the gap is
now closable two ways** — paid NXT-AI3 (`denoise_color`/`denoise_lf_color`) and
**FREE Cosmic Clarity** (`--denoise_mode separate --color_denoise_strength`);
native Siril still has none for GENERAL chroma (`rmgreen` = green-cast SCNR only).
**Do it after (heavy) denoise-destroying steps — i.e. after deconvolution, on the
starless layer** — as a strong default (see the process-rule note).

## Tier 7 — Star removal / separation (LINEAR, pre-stretch)

Split starless + stars so nebula and stars are processed independently.

| Tool | Cost | Runs | Linux/CPU/Headless | When & why |
|---|---|---|---|---|
| **StarXTerminator** (RC-Astro) | PAID $49.95 | CLI (`rc-astro sxt`) + siril-script | ✅ / AVX2, **CPU tens-of-sec** / ✅🖥 | **Best** separation, fewest artefacts on resolved objects; `rc-astro` v1.0.0 CLI. **AI11.** Free CLI for holders, offline-after-activation. Call the binary directly for headless. |
| **StarNet2 v2.5.3** (native x86 CLI) | FREE | CLI + siril-native | ✅ / ✅ (self-contained ONNX, no TF/Torch/CUDA) / ✅ | **Free default on x86** — native binary. **Linux builds are x86-64 ONLY** (starnetastro.com CLI matrix: "Linux x64"; the sole ARM lane is macOS/CoreML; no source offered). INSTALLED here at `/opt/starnet2-2.5.3-0208`, and Siril's `starnet` command is gated on this binary — its `starnet_exe` config key points at it. **`-n/--unscreen <FILENAME>`** writes a star-layer file (not a bare toggle); highlight protection is on by default so the opt-out is **`-d/--disable-highlights-protection`**. Keeps field-star flux; safe on resolved objects. CPU-only on Linux (no documented GPU path). Siril integration is thin ("point Siril at the executable"). Class-2 binary. |
| **SyQon Zenith / Starless** (AI) | FREE | pyscript | ✅ via Siril / ✅ / **✅ headless** | Headless-capable: `SyQon_Starless.py` branches on `siril.is_cli()` and runs headless with the free `zenith` model (`pyscript SyQon_Starless.py --tile-size 512 --overlap 64`), no dialog/license gate; Prism (`mini`) and Parallax (`nano`) free tiers likewise. Verify the free-tier headless run on-rig. |
| **Siril `starnet`/`seqstarnet`** integration | FREE | siril-native | ✅ / ✅ / ✅ | Drives StarNet under an invertible MTF pre-stretch (vendor-sanctioned). |

**Dead-end (portable):** never use mask+inpaint on a RESOLVED object — it
destroys HII knots. Use a learned separator (StarXT/StarNet/Zenith). On x86
the inpaint fallback is retired (a learned separator always runs).

## Tier 8 — Stretch (the LINEAR → NONLINEAR boundary)

Starless hard, stars gently. Broadband → one linked transfer; narrowband →
per-line (Tier 10 / Nightlight).

| Tool | Cost | Runs | Linux/CPU/Headless | When & why |
|---|---|---|---|---|
| **Siril GHS surface: `ght`/`invght`, `autoghs`, `modasinh`, `asinh`, `mtf`, `linstretch` (+ seq variants)** | FREE | siril-native | ✅ / ✅ / ✅ | **Default.** The full GHS toolset is native + scriptable — there is NO command named `ghs` or `curves` in 1.4.4 (the GHS transform is **`ght`**; probed present + scriptable on this rig). Doctrine (ghsastro.co.uk + the authors' Siril tutorial): iterative multi-pass GHS beats a one-shot stretch; Siril's own docs call applying autostretch as-is "rarely advisable" for production. TRAP: `autostretch` AND `autoghs` default PER-CHANNEL — pass `-linked` after colour calibration (unlinked "will alter the white balance", Siril docs). `ght -HP`/`autoghs` implicit HP=0.7 is the star-bloat protection; `autoghs` SP = k·σ from the per-channel median, implicit B=13. |
| **VeraLux HyperMetric Stretch** | FREE | pyscript-GUI | ✅ / ✅ / 🖥 | Well-regarded 2026 photometric hyperbolic stretch (Roger-Clark "true colour" lineage); numpy-inside, needs Xvfb. |
| **Cosmic Clarity / Seti Statistical Stretch** | FREE | CLI / pyscript | ✅ / ✅ / ✅🖥 | Statistical-median-target stretch; a good automated option. |
| **Arcsinh + Histogram (classic)** | FREE | siril-native / PI | ✅ / ✅ / ✅ | Arcsinh preserves star colour; the traditional broadband move. |

**Pick:** Siril `ght`/`autoghs` (linked) for headless production; `autostretch
-linked` stays the DIAGNOSTIC surface. The pyscript stretches only if
you accept Xvfb + the numpy-inside call.

## Tier 9 — Star reduction / recomposition (NONLINEAR)

Recombine stars over starless; optionally shrink stars.

| Tool | Cost | Runs | Linux/CPU/Headless | When & why |
|---|---|---|---|---|
| **Siril `synthstar` + `unclipstars` + Star Re-composition** | FREE | siril-native | ✅ / ✅ / ✅ | **Native + headless.** `synthstar` rebuilds perfect PSF stars (fixes coma/trailing), `unclipstars` desaturates blown cores, Star Re-composition blends starmask ↔ starless. Replaces our numpy star-render hand-roll. |
| **VeraLux Star Recomposer** | FREE | pyscript-GUI | ✅ / ✅ / 🖥 | Sensor-profile star recomposition (core removal, reduction, optical healing); numpy-inside. |
| **Bill Blanshan star reduction** (PixelMath) | FREE | siril-native (`pm`) | ✅ / ✅ / ✅ | Classic star-shrink expressions runnable via `pm` — fully headless. |
| **StarXTerminator** (reduce mode) | PAID | CLI | ✅ / CPU-ok / ✅ | Star reduction as part of SXT if licensed. |

## Tier 10 — Colour & palette work (esp. narrowband SHO/HOO)

| Tool | Cost | Runs | Linux/CPU/Headless | When & why |
|---|---|---|---|---|
| **Siril `ccm` (diagonal) + our examine layer** ← the recommended star-neutral *approach* (tool half verified on 1.4.4; the measure→apply design untested) | FREE | siril-native + numpy | ✅ / ✅ / ✅ | **The doctrine-clean, headless star-neutral approach:** a DIAGONAL `ccm` (3×3 + gamma, verified on 1.4.4) IS a per-channel star-neutral balance, and the **ONLY headless neutral-balance path** (Manual Color Calibration has no CLI form). MEASURE the field's mean star colour from the tool's own star detections/photometry (no native command outputs the composite statistic — the DERIVED statistic is the in-house part, and per the bright line every per-star measure feeding it must be the tool's), then APPLY via `ccm` (`seqccm` batches). The design still needs one real-data run. |
| **Nightlight** (mlnoga; two-point RGB balance) | FREE (GPL-3) | **headless Go CLI** | ✅ x86/ARM / ✅ (no-GPU, AVX2) / ✅ | Headless Go star-balance reference. `OpRGBBalance` default params (`SkipBright=0, SkipDim=0.75`) balance the **brightest 25% of stars** to neutral RGB{1,1,1} — not a symmetric "mid-population"; its source/README say nothing of OIII/narrowband/SHO, so the **"lifts OIII" behaviour is our inference**, not a documented feature. **Unmaintained** (last release v0.2.6; Go-drift risk) — a mechanism reference, not a load-bearing dependency. |
| **VeraLux Alchemy / DBXtract** (NOT star-neutral) | FREE (GPL-3) | pyscript (**Class-1**) | ✅ via Siril / ✅ / **🖥 GUI-only** | Alchemy = nebula-anchored NB normalization + Ha/OIII crosstalk-unmix (**excludes stars** — opposite anchor from star-neutral); DBXtract = the GPL-3 Bayer-crosstalk-unmix reference (12-sensor QE tables + linear solve). For OSC dual-band unmix only; numpy-inside escape-hatch, GUI-gated. |
| **Siril `pm` / `rmgreen` / `satu` / `rgbcomp`** | FREE | siril-native | ✅ / ✅ / ✅ | `pm` NBRGB/palette mixing (per-channel via separate mono images), `rmgreen` SCNR (kill SPCC's warned green cast), `satu` hue-targeted saturation, `rgbcomp` SHO/HOO assembly. Headless toolbox. |
| **PixInsight (NarrowbandNormalization, SHO-AIP, Foraxx)** | PAID €300 | GUI-app | ✅ (**X11 mandatory, Wayland unsupported**; Xvfb unverified) / ✅ / ❌ | The reference for palette work; none does star-neutral balance. GUI-bound. |

**Note:** SPCC-narrowband is verified as the *cause* of the OIII flattening —
Siril's own docs say it gives "real intensities"/"a huge green cast" and
**recommend Manual Color Calibration for SHO**. The star-neutral balance that
recovers the sphere has a **clean headless resolution now**: measure the mean
star colour in the examine layer, apply a diagonal `ccm` (the *measurement* is
the only missing native piece, and it belongs in our audit layer anyway).
Nightlight (dormant) does a brightest-quartile
two-point RGB balance — a mechanism reference, but the OIII-lift is OUR inference,
not its documented purpose (see the Nightlight row).
Two mechanisms, don't conflate: **star-anchored** neutral balance (ccm+measure /
Nightlight) vs **nebula/QE-anchored** unmix (Alchemy/DBXtract, OSC dual-band).
Star-neutral is a valid mechanism but NOT a mainstream-named technique — the
mainstream decouples stars (remove → boost OIII starless → re-add stars).
Design + bracket: BACKLOG:`star-neutral-colour`.

## Tier 11 — Detail / local contrast (NONLINEAR)

| Tool | Cost | Runs | Linux/CPU/Headless | When & why |
|---|---|---|---|---|
| **Siril `wavelet`, `pm`, HDR compression** | FREE | siril-native | ✅ / ✅ / ✅ | À-trous wavelets for multiscale detail; headless. |
| **VeraLux Revela / HDR Multiscale** | FREE | pyscript-GUI | ✅ / ✅ / 🖥 | ATWT local contrast, HDR multiscale; numpy-inside. |
| **CLAHE / local contrast** (various) | FREE | pyscript / PI | ✅ / ✅ / varies | Contrast-limited adaptive histogram equalization for structure. |
| **BlurXTerminator** (as sharpen) | PAID | CLI | ✅ / CPU-ok / ✅ | Also a nonlinear detail enhancer if licensed. |

## Tier 12 — Final touches / export

- **SCNR / green removal** — Siril `rmgreen` (headless). Broadband strong,
  narrowband mild (protect OIII green).
- **Export** — Siril writes TIFF16 / PNG16 / PNG8 / q100 JPEG headless.
  `savepng filename` auto-writes 16-bit RGB PNG (color-type 2, depth 16) with an
  **iCCP** ICC chunk; `savetif filename [-astro] [-deflate]` writes 16-bit RGB
  TIFF + ICC (`savetif8`/`savetif32` variants). These **own the finals write —
  no in-house `write_png16` / hand-built sRGB chunks** (BACKLOG). Note: PIL
  misreads Siril's 16-bit RGB TIFF as uint8 → read it with `tifffile`. Our
  16-bit lossless PNG is the judgment surface — no 8-bit/reduced-depth copy.
- **Colorimetry** — Siril embeds ICC via `icc_assign {sRGB|…}` + a save-time
  Preference (iCCP full profile); with `savepng`/`savetif` owning the write, no
  vendored ICC profile is needed.

---

## Tier L — Lunar / planetary lucky imaging (a separate data CLASS, not a render tier)

Capture many short frames → the aligner's own quality ranking → best-N% stack
→ multiscale sharpen. No solve/SPCC (no stars), no BGE (no sky signal at lunar
exposures), denoise usually skipped (deep stacks; the AI denoisers are
deep-sky-trained — off-distribution). The regime is set by pixel scale: at a
small disc (e.g. 107 px @ 70 mm) seeing is sub-pixel → single-point disc
alignment is proper and multi-point buys nothing; from ~800 mm (Z6III pitch)
the class is seeing-limited → multi-point (AS!4/PSS-class) earns its keep.
Full audit + first-corpus route: [`docs/lunar-lucky-imaging.md`](docs/lunar-lucky-imaging.md).

| Tool | Cost | Runs | Linux/CPU/Headless | When & why |
|---|---|---|---|---|
| **Siril 1.4.4 lunar surface** (`convert [-ser]`, planetary registration, `sb`/`wiener`/`rl` + `makepsf`, `wavelet`/`wrecons`, `savepng`) | FREE | siril-native | ✅ / ✅ / **✅ except registration** | **The installed-tools route for ALIGN + STACK + SHARPEN — but NOT for quality-ranked selection.** Siril's own docs recommend Split Bregman/Wiener for stacked lunar images; wavelets are the scriptable RegiStax-class layer mechanism. **The planetary registrations (image-pattern DFT, KOMBAT) are GUI-ONLY in 1.4.4** (command reference full-text-verified + on-rig probe) — Image Pattern Alignment with a **track-covering selection** is the verified working configuration (KOMBAT measured dead on this class; both traps + numbers in `docs/dead-ends.md`). **MEASURED KILL: planetary registrations write NO per-frame quality even on success** — `stack -filter-quality=N%` consumes nothing in 1.4.4, so lucky-selection needs a ranking tool (PSS/AS!4). NEF ingest is libraw = **Lossless NEF only** (HE/HE★ TicoRAW have no open decoder). |
| **Siril 1.5-dev `register_mpp`/`stack_mpp`** | FREE | siril-native | ✅ / ✅ / ✅ | Siril's own multi-point planetary registration (piecewise translation — the correct lunar-seeing model). Dev-only today. **The pre-registered adoption test at 1.5 stable**: closes the headless gap AND the multi-point gap in the already-central tool. |
| **PlanetarySystemStacker 0.9.8.3** | FREE (GPLv3) | CLI (python) | ✅ / ✅ / ✅ | The ONLY headless Linux-native multi-point stacker (Surface/Planet modes, `--stack_percent`, drizzle 3×, own Laplace ranking, run protocol). **Dormant since 2023, pins `numpy<1.23`** → frozen-tool venv adaptation with a removal condition (1.5 MPP stable or PSS revival). Author-claimed AS!3-parity. |
| **AutoStakkert! 4** (4.0.11 stable / 4.0.13 beta) | FREE (private use) | Win GUI (Wine) | ⚠ Wine x86-64 (author-sanctioned) / ✅ / ❌ (semi-manual batch, no unattended mode) | The community QUALITY REFERENCE for the seeing-limited regime: MAP multi-point + the strongest quality estimator. The escalation bracket on x86 when a long-focal corpus arrives — pointless on a ~100 px disc. |
| **AstroSurface W5** (2026-05) | FREE | Win GUI | ⚠ Wine UNVERIFIED / ✅ / ❌ | Active all-in-one (stack + wavelets + Wiener/Van-Cittert). No CLI. A manual-judgment alternative, not a pipeline stage. |
| **waveSharp 3.0** (RegiStax successor) | FREE | **native Linux GUI** | ✅ / ✅ / ❌ | OKLab 3-layer wavelets, chroma denoise, threshold-based star-free COLOUR BALANCE, 16-bit PNG out. **Frozen/archived 2026-03** — use-as-is judgment tool; Siril wavelets are the scriptable fallback. RegiStax 6 itself: dead 2011; only RGB-Align (dispersion, Wine) retains a niche at long FL. |
| **ImPPG 2.1.0** | FREE (GPL-3) | native Linux GUI | ✅ / ✅ / 🖥 (Lua batch, GUI-launched) | Active Lucy-Richardson + adaptive unsharp with live preview — the solar/lunar community favourite for interactive deconv tuning. **PNG writer is 8-BIT — never the finals writer** (export TIFF16/FITS; Siril `savepng` mints the judgment PNG16). |
| **Hugin** (mosaic mode) | FREE | CLI + GUI | ✅ / ✅ / ✅ | The Linux lunar-mosaic route for long-FL panes (crater control points match where star fields fail; Siril mosaics are astrometric-only = impossible on lunar). Already in production here for lens fitting. |
| **RC-Astro BXT on lunar** | PAID | CLI | ✅ / AVX2 / ✅ | Officially accommodated (manual-PSF mode; AI4 fixed lunar clipping) but community-preferred lunar results remain classical wavelets/deconv — a bracketed x86 experiment at most, never the route. NXT/GraXpert denoise: deep-sky-trained, skip on lunar. |

**Pick (verified on the first corpus):** small-disc regime → the installed-Siril
route, now encoded as **`scripts/stack/run_lunar_pipeline.sh`** (prep → staged
disc crop → crop-matched dark calibration → GUI pattern registration with a
track-covering selection + MID-SEQUENCE reference [the DFT wrap guard] →
tool-audited verify → stack → sb deconvolution → per-set disc-neutral `ccm` →
clip-safe linear PNG16 pairs). KOMBAT: measured dead end on this class;
quality-ranked selection: not possible in 1.4.4 (no quality regdata) — the
ranking-tool ladder (PSS/AS!4) runs on x86 against the shipped full-stack
control. Seeing-limited corpus (≥~800 mm) → AS!4-under-Wine vs PSS vs
Siril-1.5-MPP, one bracketed head-to-head before any adoption. Capture doctrine
lives in the acquisition checklist (`docs/dead-ends.md`, lunar block — with the
measured exposure card).

## Cross-cutting: what's FREE-and-headless vs PAID vs GUI-gated

**The fully FREE + headless x86 stack** (no license, no display, runs under
`siril-cli` or a Class-2 binary): Siril 1.4 natives (solve / SPCC / drizzle /
ccm / curves / autostretch / GHS / denoise / synthstar / rgbcomp / wavelet /
pm / rmgreen / satu) + **GraXpert** (BGE **CPU-fast**, denoise **CPU-slow**,
deconv **RC/fork only**) + **StarNet2 v2.5.3** (star removal) + **SyQon** free
tiers (Zenith/Prism/Parallax — headless via `is_cli()`) + **DeepSNR 1.2.1**
(denoise, native Linux CLI) + **AstroDenoisePy** (unmaintained — archival only) +
**Cosmic Clarity** (sharpen/denoise incl. a FREE `--color_denoise_strength`
chroma control / dark-star, native Linux, CPU-slow) + **ASTAP** (fast solve,
non-trailed class). A complete, competitive pipeline — and the chroma-noise gap
has a FREE fill here (Cosmic Clarity). (`AstroSharp` is OUT — no Linux/CLI,
600 KB TIFF cap.) Watch-list, platform/free/headless UNVERIFIED — check before
any adoption: **AIDT/AIST** (mdci.ro, ONNX mono NR + Siril plugin) and
**AstroForge** (astroforge.de).

**PAID, real Linux CLI** (worth it if budget allows): **RC-Astro
BXT $99.95 / NXT $59.95 / SXT $49.95** (bundle $189.85) via the standalone
**`rc-astro` v1.0.0** binary (**Ubuntu 22.04+ "or equivalent," Kali not
vendor-certified — verify**) — best-in-class deconv (incl. `--correct-only`
trailing fix) / denoise (AI3 has a **dedicated chroma path `denoise_color` →
closes the chroma-noise gap**, exact CLI flag spelling pending an x86 `rc-astro
nxt` probe) / star removal. One cross-platform perpetual license, **CLI free for
holders**, AVX2 CPU (no vendor wall-clock table — **self-benchmark via
`--benchmark-all`**), **Linux GPU = NVIDIA-CUDA only** so a no-GPU box runs the
supported CPU fallback, **offline after activation + `rc-astro download-models`**.
Call the binary directly (Class-2). **PixInsight** €300 — reference (WBPP,
DBE/MARS), X11-only.

**FREE but GUI-gated / numpy-inside** (escape-hatch, per the resolved
philosophy question — the class-3 mechanism-location test above): the **VeraLux** suite
(Silentium / HyperMetric / Nox / Vectra / Alchemy / …), **SyQon** free tiers
(Zenith / Prism / Parallax-Nano), **SCUNet**, **DBXtract** — these do the pixel
math in their own numpy/scipy/pywt/torch (mechanism = numpy → sanctioned
*alternative with a removal condition*, never "a tool"). Most are **GUI-mandatory
PyQt6 with no arg vector → NOT headless-drivable even under Xvfb**; only
dual-mode ones (Statistical_Stretch, SyQon Prism `--no-gpu`) run headless. Prefer
a compiled tool (Siril-native / RC-Astro / GraXpert / StarNet / DeepSNR / Cosmic
Clarity — all Class-2 binaries) whenever one provides the mechanism.

## What is installed, and what is a deliberate gap

On this rig the only absences are CHOICES, and each is recoverable by installing the tool — not a platform wall.
Verified per-tool from primary sources (starnetastro.com CLI matrix, rc-astro.com
system requirements, pixinsight.com sysreq, setiastro/cosmicclarity releases,
Steffenhir/GraXpert releases + CI, hnsky.org) + on-rig probes:

- **INSTALLED and driven** (`/opt`, versions + checksums in
  `scripts/setup/manifest.tsv`): StarNet2 2.5.3 (siril's `starnet_exe` points at
  it), Cosmic Clarity 6.6 (denoise + non-stellar sharpen + darkstar),
  DeepSNR 1.2.1, GraXpert 3.0.2 (BGE + denoise), ASTAP, Nightlight 0.2.6, plus
  darktable 5.4.1 / lensfun 0.3.4, Hugin 2025.0.1, astrometry.net via the venv
  engine + `sep` 1.4.1, and astropy 8.0.1. The full Siril 1.4.4 native render
  surface is present and scriptable — but `help` LISTS commands that refuse in a
  script (`tilt`, `inspector`), so probe before believing a capability exists.
- **NOT INSTALLED, by choice** — RC-Astro (BlurXTerminator / NoiseXTerminator /
  StarXTerminator) and PixInsight, which also gates every PI-plugin route
  (RC-Astro-in-PI, DeepSNR-PI). Both are PAID and both run on this hardware
  (Linux x86-64 + AVX2); nothing blocks them but the decision to stay on free
  tools. That choice is deliberate and worth keeping: free public tools mean any
  contributor can reproduce and troubleshoot the same result.
- Consequence: denoise = Cosmic Clarity / GraXpert / Siril native; separation =
  StarNet2; learned deconvolution = Cosmic Clarity's non-stellar sharpen, which
  is UNMEASURED here (BACKLOG:`learned-deconvolution`).

## Research queue — candidates to investigate, and the question each would answer

**This is the ORACLE's standing intake.** It is not a shopping list and nothing
here is a recommendation: each row is a tool that plausibly bears on an open
problem, with the QUESTION that would settle whether it belongs. The Oracle feeds
this queue by review — it reads and reports, the owning session lands the row.
Availability below is probed on this rig, not assumed; re-probe on a distro bump.

| candidate | availability (probed) | the question it would answer |
|---|---|---|
| **SWarp** 2.41.5 | **INSTALLED** — and **the binary is `SWarp`, not `swarp`**. The lowercase name is not on PATH and the shell suggests `suckless-tools`, an unrelated package; `dpkg -L swarp` gives `/usr/bin/SWarp`. Probe: `SWarp -v` → *SWarp version 2.41.5 (2021-01-27)*. | The documented industry compose is per-image resampling onto a COMMON output WCS using each exposure's full solution — CD matrix *and* distortion (SDSS / CFHTLS / DES / Pan-STARRS lineage). It is the named route for BACKLOG:`compose-homography-smear`. **ANSWERED, AND IT IS THE FAILURE THAT LOOKS LIKE SUCCESS: SWarp CANNOT READ SIP, AND IT DROPS IT SILENTLY.** MEASURED from the 2.41.5 source (`apt-get source swarp`, no build): **`A_ORDER` / `B_ORDER` / `AP_ORDER` / `TAN-SIP` occur ZERO times in the entire tree** — there is no SIP reader. The projection is matched by a THREE-character compare, `src/wcs/wcs.c:488` `strncmp(&ctype[j][5], pcodes[k], 3)`, so `RA---TAN-SIP` resolves to pcode `TAN`; the axis check is an EIGHT-character compare, `:529` `strncmp(ctype[j], requir, 8)`, so `DEC--TAN` matches `DEC--TAN-SIP` and **raises no error**. The distortion path is then gated at `src/fitswcs.c:840-846` on pcode ∈ {TAN, TPV} **AND** non-zero `projp` (the PV terms) — and a SIP header carries no PV terms, so it falls to the bare `else return;` and **applies nothing**. The only nearby warning (`:959`) is about projection *inaccuracy*, not dropped distortion. **So SWarp accepts a TAN-SIP header without complaint, resamples on the CD matrix alone, and writes a normal-looking coadd that has silently discarded exactly the information it was adopted to preserve.** **THE WAY OUT IS ONE PACKAGE AND IT CHANGES THE DISPOSITION:** SWarp reads **TPV** natively (in the pcode list at `fitswcs.c:801` and inside the distortion gate at `:843`), and **`sip_tpv` 1.1 (PyPI, Shupe et al.) is the standard SIP↔TPV converter** — so the route is solve with SIP → convert headers SIP→TPV → SWarp consumes the distortion properly. Not "SWarp cannot do this" but "SWarp needs a documented header conversion first". **SETTLED — THE CONVERSION IS EXACT IN THE DIRECTION NEEDED, SO THE GATE IS OPEN** (MEASURED from the 1.1 sdist, `pip download --no-binary :all:`, read not built, 2026-08-14). **The two directions are structurally different and only the one we do NOT need is approximate.** `sip_to_pv.py` — ours — contains **no `lstsq`, no `polyfit`, no `curve_fit`, no fit of any kind**; it calls `sym_tpvexprs()` / `get_sip_keywords()` / `real_sipexprs()` / `add_pv_keywords()`, i.e. sympy expands the composition of the CD linear map with the SIP polynomial and matches coefficients term by term. Composing a linear map with a degree-n polynomial yields a degree-n polynomial, so **the identity is exact to floating point**. The REVERSE path `pv_to_sip.py` is the fitted one — it takes `aporder`/`bporder`, *"order for reverse polynomial… (default 4)"* — and the route never uses it. Order limit from the README: the method is *"extended to 7th order"* against our SIP order ≥2 (Shupe et al. 2012, SPIE 8451, 84511M). **And the inverse-mapping worry does not arise either:** resampling needs sky→pixel and TPV has no analytic inverse, but `src/fitswcs.c:836` (*"Check first that inversion is not straightforward"*) is SWarp's OWN numerical inversion, gated on TAN/TPV with non-zero `projp` — **so SIP's approximate `AP_`/`BP_` coefficients never enter the route at all.** **FALSIFIER RUN, AND BOTH HALVES HOLD — the source reading is now confirmed by execution** (july31 `groups_set-03/sub_01.fit`, 5831×3965, `RA---TAN-SIP`, A_ORDER=3, 17.027 ″/px; PM-reproduced independently). **Conversion exactness, 60×60 = 3600 points over the FULL frame:** SIP vs converted TPV median **0.000**, max **1.903e-10 arcsec = 1.118e-11 px**, and **FLAT in field radius** (max px by ρ bin: 9.63e-12 / 1.04e-11 / 1.12e-11 / 1.07e-11 / 1.08e-11) — **the corner-degradation failure mode is ABSENT**, which is the one that would have mattered. For scale, the WCS machinery's own SIP pix→sky→pix round-trip noise floor is **2.5e-07 px, ~22,000× LARGER** than the discrepancy. **POSITIVE CONTROL, because "they agree" can also mean "both did nothing":** SIP vs plain TAN (distortion stripped — what a dropped distortion looks like) reads median **21.85 arcsec**, max **235.4 arcsec = 13.82 px**, and GROWS to the corner (0.235 / 1.267 / 3.676 / 7.903 / 13.823 px). The control is **1.24e12×** the conversion residual and shows exactly the signature the real test did not, so the test can see a dropped distortion and saw none. **AND SWarp'S SIP-BLINDNESS IS NOW CONFIRMED BY SWarp ITSELF, not by source reading** — `-HEADER_ONLY Y`, no pixels resampled, three runs differing only in the input header's distortion, and the SIP result **reproduced here independently**:

| input header | output canvas | CRVAL1 | CRVAL2 |
|---|---|---|---|
| `TAN-SIP` (A_ORDER=3) | 6957 × 4619 | 312.423584825 | 42.105703820 |
| **plain TAN, SIP stripped** | **6957 × 4619** | **312.423584825** | **42.105703820** |
| TPV (converted, 17 PV) | 6935 × 4611 | 312.452563494 | 42.110220931 |

**The SIP output is IDENTICAL to the no-distortion output — same canvas, same CRVAL to nine decimals — while TPV moves the canvas 22 × 8 px and CRVAL by 104.3″ / 16.3″.** That is the silent drop end to end, and SWarp is demonstrably not blind in general. *(Output CTYPE is `RA---TAN` in all three because the output canvas is SWarp's own projection by construction — that field alone proves nothing; the discriminator is the canvas DIFFERING.)* **REPRODUCIBILITY GAP — NARROWED, NOT CLOSED, and the headline half of the previous wording is now FALSE.** It read *"`sip_tpv` IS NOT INSTALLED ON THIS RIG"*. MEASURED: `'/opt/astro-venv/bin/python' -c 'import sip_tpv'` **imports OK**, and it is installed by `install_python_tools.sh`, which `x86_bootstrap.sh` calls — so it IS clone-reachable. **What survives is the half that still gates adoption, and it is two separate facts:** (1) **zero rows in `scripts/setup/manifest.tsv`** — measured on the TOOL COLUMN, not a substring grep, which counts a mention inside the `scamp` row's notes; (2) **it is absent from host `python3` and from `astrometry-venv`, and every one of the ~175 python invocations under `scripts/` resolves to host `python3`** — so no consuming script can import it as written. **The convention exists (`$ASTRO_VENV`, used by both setup scripts) and so does the consumer pattern (`solve_field.py` re-execs into its own venv); neither has been applied on the read side.** So: the route's first link is verified AND the tool is now reproducible from a clone, but adopting it still needs a manifest row and a consumer that names the interpreter. **This claim was false for hours inside a ~4,000-character table cell, which is what a single un-compressed cell costs: a negative-claim sweep read the row and did not reach it.** Still NOT established and not tested: that a SWarp coadd built through TPV beats the adopted `seqplatesolve` + `seqapplyreg` route. Nothing was resampled. **Cheapest decisive on-rig check before anything else: `HEADER_ONLY Y` on one member** — it writes only the output header and reads no pixels, so it confirms what SWarp actually made of the WCS at zero cost. **AND THE NATIVE ALTERNATIVE DOES NOT CONSUME IT EITHER, BY A DIFFERENT MECHANISM.** Siril's own help: `seqapplyreg` *"Applies geometric transforms… using **registration data** previously computed"*, and registration data is `shift | similarity | affine | homography` — there is no per-image-WCS transform class. This repo already measured the consequence and never connected it: `register -disto=` is a SHARED-solution facility, each member undistorted by its OWN SIP then composed measures 3.99/6.42/6.19 px against the shipped route's 0.29/0.63/2.10/2.99, and **"Siril's own design assumes ONE optical state per sequence"**. **So `seqplatesolve` + `seqapplyreg` is NOT "the SWarp-class operation natively" — it is a solve reduced to a transform from the same family the defect is blamed on. Siril discards per-image distortion BY DESIGN; SWarp discards it BY SILENT OMISSION. The comparison as posed cannot be run, because one arm drops its own input.** **DEFAULTS THAT ARE WRONG FOR THIS DATA, all read from `src/preflist.h` and all silent:** `FSCALASTRO_TYPE FIXED` (VARIABLE is the one that tracks per-pixel solid angle — `src/resample.c:367` allocates the area buffer only under VARIABLE — and on a ~30° gnomonic field the pixel solid angle varies ~10% radially, the same term as the plate-scale work); `RESAMPLING_TYPE LANCZOS3` **with NO clamping parameter exposed at all**, i.e. unclamped ringing on undersampled stars where Siril's clamp is measured at 6.26% of PSF width — a different trade, not a better one; `COMBINE_TYPE MEDIAN` (not the plain mean the compose doctrine specifies, and poor on five members); `PROJECTION_ERR 0.001` (SWarp *approximates* the projection for speed, on a field where the projection is the thing under test); `PIXELSCALE_TYPE MEDIAN` on a field whose scale varies; `GAIN_DEFAULT 0.0`. **AND THE LINEAGE THE ROUTE IS ARGUED FROM IS HISTORICAL:** DES uses SWarp and that pipeline is a previous-decade design; Rubin/LSST moved to an in-house warp-then-assemble (`AssembleCoaddTask`, inverse-variance weighting), Roman uses IMCOM, and Zackay & Ofek's proper coaddition is the information-preserving alternative already in this registry. Every successor replaced the resample-then-combine step with something that carries a PSF model through it — notably LSST's warp kernel is *also* Lanczos3, so the interpolation choice is not what moved; the PSF handling is. **AND IT MAY ALREADY SATISFY A STANDING REMOVAL CONDITION NOBODY CONNECTED TO IT.** `coverage_frame.py`'s condition (BACKLOG:`removal-conditions`) offers two disjuncts, the second being *"a coverage map ON the union's own canvas that `verify_framing.py --map` can consume"*, and the recorded reason nothing satisfies it is that `coverage_probe.sh` builds its map through `register -2pass`, so **its canvas is not the product's**. SWarp resamples onto a SPECIFIED output WCS and writes its weight map on THAT canvas by construction — probed on this rig: `WEIGHTOUT_NAME coadd.weight.fits # Output weight-map filename`, alongside `PROJECTION_TYPE`/`CENTER_TYPE`/`IMAGE_SIZE`/`RESAMPLE`. **Two limits travel with it:** it answers the SECOND disjunct only — the maximal-rectangle search stays in-house — and whether `verify_framing.py --map` can consume a SWarp weight map is a FORMAT question that is unchecked. The tool was recorded as installed in one item and the condition it may satisfy sat 470 lines away in another. |
| **PSFEx** 3.21.1-1 | **SOURCE-PACKAGED AND REACHABLE HERE** — the earlier "NOT packaged" was true of Kali's BINARY repo (`apt-cache policy psfex`: no candidate) and false as stated. This rig already has `deb-src http://deb.debian.org/debian/ bookworm main` configured, and `apt-get source --print-uris psfex` resolves `psfex_3.21.1-1.dsc` + `psfex_3.21.1.orig.tar.gz` with SHA256s. Building stays inside the distro's own packaging — no upstream tarball. | Bertin's spatially-varying PSF modeller, same lineage as `source-extractor` (INSTALLED). It models the PSF as eigen-PSFs whose coefficients vary as a low-order POLYNOMIAL in (x,y) across the field — the survey-standard characterisation of exactly the quantity the corner defect is about, which our box-median stations only sample (Bertin 2011, ASP Conf. 442, 435; DES / HSC / CFIS). **Its input is available NOW:** it consumes a SExtractor catalogue carrying `VIGNET`, and the installed 2.28.2 offers `VIGNET`, `VIGNET_SHIFT`, `VIGNET_DGEOX/Y` (verified). **AND IT IMPLEMENTS THE CORRECTION, not just the measurement** — built-in PSF homogenisation (`HOMOBASIS_TYPE GAUSS-LAGUERRE`, `HOMOBASIS_NUMBER/SCALE`, `HOMOPSF_PARAMS`, `HOMOKERNEL_DIR/SUFFIX`, kernels as `.homo` FITS cubes), spatially varying because the model is. That is the DESDM operation. **`docs/untracked-widefield-standards.md` H.3(6) says PSF homogenisation is "absent from the repo entirely… No amateur tool in TOOLS.md implements it" — that is FALSE and needs correcting.** **Trade-off, stated because it is the owner's call:** homogenisation convolves to a common, slightly BROADER target PSF — it makes corner and centre match by softening the centre, and does NOT recover corner detail. Whether that is a root-cause fix or a bandaid under this repo's rule is doctrine, not a tool fact. **RUN — the two open questions are answered, and a THIRD tool fact came out that will misdirect the next person.** **IT DOES BUILD HERE — all three clauses of the previous wording are now false, and the binary-extraction route below is the SUPERSEDED workaround, not the shipped path.** It read *"It does NOT build here: `autoconf`/`automake`/`libtool` are absent and installing them needs root, so the deb-src route is blocked."* MEASURED: `autoconf` and `automake` are **present** (`/usr/bin/`), only `libtool` is absent, and **PSFEx 3.21.1 is built from the Debian source and installed at `~/.local/bin/psfex`** — so the conclusion is refuted by outcome regardless of the tool list. `install_astromatic.sh` does the root-once build-deps step and `x86_bootstrap.sh` reaches it, so the source build is **clone-reachable**. **This claim was corrected once already this session in `requirements-tools.txt` (`21560ae`) and survived here — a claim fixed at the site where it was REPORTED lives on at every other site that carries it, and the correction reads as complete because the reported instance is fixed.** Kept below for provenance: what previously worked with neither root nor a system change was the official bookworm BINARY, sha256-verified against the archive `Packages` index and extracted with its four transitive deps (`libatlas3-base`, `libplplot17`, `libshp2`, `libcsirocsa0`, `libcsironn0`, `libqsastime0`) into a scratchpad, run via `LD_LIBRARY_PATH`. It then works: 2053–2200 of 2275–2414 candidates accepted per frame, chi²/dof 1.36–1.49, and its field model **independently confirms the corner degradation** — FWHM 1.95 px at the frame centre to 3.2 px at the corners, a different algorithm sharing no code with Siril. `PSFVAR_DEGREES` 2 → 3 barely moves anything, so **the field does not demand a richer basis than the in-house spin-2 fit**. **THE TOOL FACT THAT MISDIRECTS: PSFEx exposes NO POSITION-RESOLVED SHAPE in any output.** The XML gives min/mean/max of FWHM/ellipticity/e1/e2 over the `PSFVAR_NSNAP` grid; the `.psf` gives model coefficients. So a position-resolved comparison **cannot** avoid re-deriving a shape from the model, and any instruction of the form "use PSFEx's own reported shape, don't re-derive moments" is self-contradictory — scoped that way twice already. Two traps inside the re-derivation: the polynomial basis order from `src/wcs/poly.c poly_powers()` is **`[1, X, X², Y, XY, Y²]`**, X-major within each power of Y, NOT the `[1, X, Y, X², XY, Y²]` any reader assumes — getting it wrong transposes the whole field model (settled against `source-extractor`'s own `ELONGATION`: corr +0.360 for the transcribed order against +0.006 for the guess). And PSFEx's own reported ellipticity comes from a **Moffat fit** (its XML carries `MoffatBeta`) while re-derived adaptive moments give ~0.84× a planted value — so a 0.038-vs-0.07 gap between them is a definition difference plus a calibrated estimator factor, **not a defect in either tool**, and not something to chase. Records: `datasets/aug06/corner_work/psfex_compare.json`. |
| **HOW MANY STARS A POSITION-DEPENDENT FIT NEEDS — the field's stated form, and it is an OCCUPANCY not a count** | Pan-STARRS, Magnier et al. 2016 (arXiv:1612.05244) Table 5 | *"Minimum number of stars required for a given order of the PSF 2D variations."* **16 / 54 / 128 / 300 / 576** stars for orders **1 / 2 / 3 / 4 / 5**, against **4 / 9 / 16 / 25 / 36** grid cells — i.e. `(order+1)²` cells, and dividing through gives **4 / 6 / 8 / 12 / 16 stars per cell**. **So the requirement is not "N stars" in the abstract; it is that every cell of an `(order+1)²` grid is populated several times over** — which is what to measure, since 128 stars all in one corner do not fill a 4×4 grid and a raw count cannot see that. Their fit is iterative with 3σ rejection over three passes, and the order is AUTOMATICALLY limited when the count is short. **Scope, and it matters: this is a FLOOR tuned to GPC1 chips with their own per-star precision, not a law — a minimum for a robust rejected fit depends on the scatter of the individual points.** Also stated for PSF parameters rather than a photometric scalar; the design matrix does not care which scalar it fits, but the paper does not say "photometry". **The paired tool fact: PSFEx states NO minimum at all** — no star count, no degrees-of-freedom condition, no conditioning warning, no discussion of degeneracy; its only quantitative guidance is that *"a third-degree polynomial on pixel coordinates (represented by 20 PSF vectors) should be able to map PSF variations with good accuracy on most exposures."* **So it will fit an under-determined spatial model without complaining.** Not a live hazard at our measured 2053–2200 accepted stars per frame, but the absence of a guard is invisible until someone runs it on a sparse field. SCAMP states no comparable photometric-mode threshold (searched negative). |
| **Piff** 1.6.0 | pip, pure python, CPU (`pip install piff`) | DES Y3's replacement for PSFEx (Jarvis et al. 2021, MNRAS 501, 1282). Headline difference: it models the PSF in **SKY** rather than pixel coordinates, and can do either. That is precisely our axis — our PSF is fixed in SENSOR coordinates while the sky drifts ~1000 px across it, so the frame the model lives in is the whole question for the union-vs-member comparison. **Open:** is it the better instrument than PSFEx for that specific split? Minimal-dependency fallback for homogenisation alone: **pypher** (Boucaud et al. 2016, ASCL 1609.022), pip, regularized-Wiener kernel between two PSFs. |
| **SCAMP** 2.10.0 | **INSTALLED** (`~/.local/bin/scamp`, built from Debian source) | Photometric + astrometric solution across overlapping exposures — the removal condition on `object_tilt.py`'s divergence, which does NOT fire (no photometric analogue of `DISTORT_DEGREES`; see the Tier-3 row). **This row previously read "NOT packaged (probed twice) … the row exists so nobody re-probes it a third time" while the binary was installed and this same file quoted `scamp -d` on it two sections up — a row whose stated purpose was to prevent the re-check that would have corrected it.** A "do not re-probe" note is only safe on a fact that cannot change; availability can. |
| python **`reproject`** 0.21.0 | **INSTALLED in `/opt/astro-venv` — and ABSENT from `~/.local/share/astrometry-venv`** | The astropy-native alternative to SWarp for WCS-based resampling. Same question as SWarp, different implementation; still blocked by per-frame SIP being unreproducible (`docs/dead-ends.md`), which is a DATA limit and not an availability one. **"Installed" is per-VENV on this rig and the two venvs differ — a consumer running under the solver venv still cannot import it, so name the interpreter with any availability claim.** |
| python **`astropy_healpix`** 2.0.1 | **INSTALLED in `/opt/astro-venv` — and ABSENT from `~/.local/share/astrometry-venv`** | `spcc_cone.py` hand-rolls the nside=2 nested cover. The open question was framed as *"does either candidate retire the hand-rolled cover?"* **as though neither were available — one is**, so that question is answerable now rather than gated on procurement. Siril 1.5's `healpix` command remains the other candidate and 1.5 is not installed. Same per-VENV caveat as `reproject`: `spcc_cone.py`'s own interpreter decides whether this is reachable. |
| **Siril 1.5.0-dev** | not installed; 1.4.4 is current stable | ADOPT: the native `mask_*` subsystem plus `-mask` on `denoise`/`rmgreen`/`epf`/`rl`/`sb`/`wiener` — the first native path to region-confined ops. **LOAD-BEARING RISK: `starnet`/`seqstarnet` are REMOVED in 1.5.0-dev**, consolidated behind `pyscript StarNet.py`, and `render_tier.sh` calls `starnet` — a bump breaks the shipped render tier. Migrate before bumping (BACKLOG:`siril-1.5`). |
| **GraXpert classical interpolators** (RBF / spline via `-preferences_file`, no AI model) | GraXpert 3.0.2 INSTALLED; this path UNTESTED | The AI path absorbs ~2/3 of extended structure on a starlight-filled field (measured). Do the classical grid interpolators avoid that, making GraXpert usable on this class? |
| ~~**RC-Astro BlurXTerminator**~~ | **ROW ANSWERED — retired to `docs/dead-ends.md`** | **ANSWERED, status DOCTRINE.** Its technical manual documents field-variable correction explicitly — 512×512 tiles *"processed independently to allow for non-stationary PSFs"*, *"the aberrations can vary across the image"* — and names our candidates in its correctable list *"in limited amounts"*: first/second-order coma and astigmatism, **trefoil (*"in image corners with some camera lenses"*)**, field curvature, and motion blur. So the registry's ceiling is a PROCUREMENT boundary, not a physics one. UNMEASURED on our data, PAID, and applying it while the cause is unidentified is the bandaid the owner refused. Full quotes and scope in `docs/dead-ends.md`. |
| **PSS** / **AutoStakkert!4** | not installed (x86 available) | Quality-ranked lucky-imaging frame selection — Siril 1.4.4 writes NO per-frame quality, so `-filter-quality` has nothing to consume. Gated on BACKLOG:`lunar-ladder`. |
| **waveSharp 3.0** / **ImPPG 2.1.0** | not installed (native Linux) | Judgment-quality lunar finishers, dormant until a long-focal corpus exists. |

**Rows retire by being answered, not by being installed.** A row whose question
is settled moves its finding into the relevant tier above or into
`docs/dead-ends.md`, and the row is deleted.

## The no-GPU reality

Every AI tool here runs CPU-only on the i7-14700 (AVX2), but slower — and the
spread is large. **Indicative CPU figures (from mixed / comparable hardware, NOT
measured on our rig — re-measure):** RC-Astro is reasonable on CPU (BXT ~30–40 s
from an i5-14600K; NXT/SXT lighter/faster — the NXT ~20–30 s figure is a
5-yr-old Mac, not 14th-gen); **GraXpert denoise (>30 min on large frames) and
Cosmic Clarity sharpen (15–30 min) are the slow ones** (also other CPUs);
GraXpert BGE is near-instant. Measure wall-clock and budget it — nothing here REQUIRES a GPU.
(An NVIDIA GPU accelerates all of them via CUDA/cuDNN on Linux — including
RC-Astro, whose Linux GPU path is NVIDIA-only — but every tool has a supported
CPU fallback; use `rc-astro <tool> --benchmark-all` to pin the fastest device.)

## The one process rule that changed everything

The 2026 consensus order, as a **strong DEFAULT (not an absolute rule)**:
**gradient removal → colour calibration (SPCC, on linear) → DECONVOLUTION
(linear, stars usually still present) → noise reduction (linear, on starless)
→ star removal → STRETCH → detail / colour / recomposition (nonlinear)**. The
two the old arm pipeline got wrong or couldn't do: **deconvolution comes early
and BEFORE (heavy) denoise** (now possible + can fix trailed stars), and
**noise reduction is a real tool step, not a hand-rolled coring**. Three
refinements from the multi-source validation (RC-Astro/Croman + Siril's own docs
+ ben.land/Cuiv/AstroBackyard — primary citations in git history):
(1) *light* NR before deconvolution is fine — Siril itself recommends a ~50–60%
VST to steady the RL — the rule is "no HEAVY NR first"; (2) **star-removal
placement is genuinely variable** (RC-Astro: linear/early; AstroBackyard:
post-first-stretch) — a per-dataset choice; (3) **2026 AI tools loosen the
linear-only rule** — because BXT/SXT/NXT/DeepSNR self-normalize, respected
practitioners (ben.land, Cuiv) run NR and even deconv in the *nonlinear* stage;
treat that as a measurable alternative, not a violation. What everyone still
agrees on: **colour-calibrate on linear, minimally-processed data**, and **no
heavy NR before deconvolution**.

Sources: the per-topic primary citations live in the research deep-dives — the
surviving ones in **`docs/`** (see `docs/README.md`), the retired
fully-graduated ones in git history. In brief: siril.org (1.4.0–1.4.4
releases; RC-Astro-in-Siril 2026-06; Zenith 2026-01; Parallax 2026-06),
siril.readthedocs `/latest` (1.5.0-dev commands / denoising / SPCC / platesolving /
Python-API / scripts), rc-astro.com (`rc-astro` v1.0.0 standalone CLI, FAQ,
product pages) + the GitLab RC-Astro script source, GraXpert GitHub **API**
(stable 3.0.2, deconv RC-only in 3.1.0rc2, bug #243), gitlab free-astro/siril-scripts
(VeraLux/SyQon/DBXtract source), starnetastro.com (StarNet2.5.3 / DeepSNR),
setiastro.com (Cosmic Clarity v6.5 / SASpro), mlnoga/nightlight (star-neutral),
hnsky.org (ASTAP), pixinsight.com ImageWeighting (QA metrics), ben.land 2025-12 +
AstroBackyard + PixInsight/Conejero (workflow-order).
