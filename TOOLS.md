# TOOLS.md — the astrophotography toolkit, by pipeline tier

A tool **audit**, not a prescribed chain. For each pipeline tier: what the
tier does, the options, when/why to pick each, and the alternatives —
filtered for what runs on the **rig** (x86-64 Kali, Intel i7-14700K, 28 cores,
31 GB RAM, 1.8 TB NVMe, **no NVIDIA GPU**, headless-preferred — the full
environment is in `CLAUDE.md`, the installed inventory in
`scripts/setup/manifest.tsv`). The pipeline is a
TOOLKIT: pull the right tool per dataset + goal, each choice a measured
experiment ([[pipeline-as-toolkit]]). Current as of mid-2026.

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
provides the mechanism — detects (`anomaly_audit`, report-only, removal-conditioned).
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
so on that class the per-set sky flat remains the least-bad flatless route and
REAL flats at acquisition are the fix. **The sky flat is strictly PER-SET (user-ratified rule): a
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
[[stacking-vs-official-pipelines]].

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
| **Hugin `cpfind`/`cpclean`/`autooptimiser`** (fit the lens FROM OUR OWN FRAMES — `scripts/darktable/fit_lens_model.sh`, installed by `install_lens_model.sh`) | FREE | CLI | ✅ / ✅ / ✅ | **The model source IN PRODUCTION for this rig's lens — adopted after a measured WIN at instrument and full depth** (centre station 5.30 → 3.67 px majFWHM at 168 frames, all stations within 3.4–3.8 px — the perpendicular-station level; seqtilt truncated-mean 3.27 → 3.06 px, a different statistic (see the floor entry's measure note); stars +10%; approved on the user's eyes). Fits the panotools radial model from star correspondences BETWEEN frames — the mechanism the SIP dead-end leaves viable (no catalog, no per-frame solve); its a,b,c paste DIRECTLY into a lensfun `model="ptlens"` entry (lensfun rescales hugin-convention coefficients internally — read in the lensfun source and confirmed by the end-to-end behaviour), installed into the live lensfun user DB so the darktable chain is untouched. The fit procedure is scripted as `fit_lens_model.sh` (proven step by step; the script's first as-written run is the next fit). Traps, all measured: SIFT CPs are weak on star fields (feed Siril-autostretched copies, `--fullscale`; 0 CPs on a 1500 px pair, ~10/pair near) and `align_image_stack`'s correlation search dies at ~130 px steps (3 CPs) — use `cpfind` on the full multi-image project (399 CPs/53 pairs) + **`cpclean`** (263 survive); **pin `v` at the astrometrically-solved hfov** — a free v collapses degenerate (v→0.93°, a=98); stage the optimize (ypr → +abc → +de); verify the override is not a silent no-op (darktable never fails loudly) via the lens_preflight difference proof. The d,e centre shift maps to lensfun's `<center>` element — UNDOCUMENTED (absent from the shipped DTD/XSD, parsed by `database.cpp`), sign unverified: a separately-bracketed knob only if an abc-only fit leaves residue. |
| **darktable + lensfun** (`darktable-cli --style <s> --style-overwrite`) | FREE | CLI | ✅ / ✅ / ✅ | **THE ADOPTED FIX for this class — measured WIN at mid/edge, in production, shipped — with one measured CLASS LIMIT: the community profile's paraxial error writes an along-drift CENTRE BAND into a far-drifting set** (shipped render centre station 5.30 px / roundness 0.480 vs 3.60 / 0.706 perpendicular; the no-model control's centre is its BEST region — `docs/dead-ends.md` paraxial-band entry). **Fixed on this rig by the FITTED entry** (the Hugin row above); the preflight, `lensfun-update-data` and `install_lens_model.sh` are the per-rig setup steps. An OFFICIAL *measured* lens profile, immune to the index-sparsity that kills a per-frame SIP fit. darktable must be built against Lensfun (Debian's is; Debian's **RawTherapee is NOT** — it doesn't link lensfun, so its auto-match is unavailable). On july14, Siril `seqtilt` control → corrected → community 168-fr control: **off-axis aberration 0.57→0.31→0.25 px**, stars 5,095→10,707→11,805, 54/54 register; the SHIPPED fitted-model render measures **3.06 px truncated-mean / 12,976 stars / sensor tilt 0.31 (10%)** (the band leaving the statistic, not the floor moving). Sharpness vs the community model is NULL (truncated mean FWHM 3.20→3.28) and a radial model cannot fix the one-sided term (0.50→0.42→0.51 across the community arms; the fitted model's cut to 0.31 was paraxial model error, not tilt) — claim carefully. **The style is pinned in-repo** (`scripts/darktable/*.dtstyle` + `install_styles.sh`, verified to reproduce the warp to 0.000 px) — no GUI step. **`--style-overwrite` is REQUIRED**, else the style is silently ignored. **Correction set: a style's lens op_params are IGNORED — `modify_flags` included** (measured: flags 0–7, method/inverse flips, a blanked lens string → byte-identical output; `docs/dead-ends.md`) — and darktable's per-image default set includes **vignetting**, which FIGHTS a master/sky flat (the measured double-correction bowl, `datasets/july14/set-01/qa_work/gradient_qa.json`); **distortion-only is enforced in the lensfun user DB** (`install_lens_model.sh` strips this lens's vignetting/tca; verify with a uniform-card warp — corner medians == centre). **`--icc-type SRGB`, never `LIN_REC709`** (match Siril's tag — `docs/dead-ends.md`). **The style carries ONLY the enabled bit; `focal`, `scale`, `camera` and `lens` are all baked but IGNORED — darktable re-detects them from EXIF and recomputes the autoscale (MEASURED: focal 70 vs 24 give opposite-sign warps; scale 1.046 vs 0 vs 1.5 are identical to 0.000 px; a swapped lens string gets that lens's own profile). So ONE style is camera-, lens- and focal-general.** **The same mechanism is a trap: darktable NEVER FAILS** — an unmatched lens gets NO correction, silently (0.000 px over 413 stars, exit 0, nothing in the log), and a wrong-but-present lens gets a wrong model just as quietly. It cannot be relied on to degrade loudly: the CHAIN must assert EXIF camera+lens+focal against the DB per set and STOP on a miss ("did the warp happen" is not enough — it passes the wrong-lens case). Debian's lensfun 0.3.4 lacks the Z6III → **`lensfun-update-data`**, which ships in **`liblensfun-bin`** (NOT `python3-lensfun` — that package exposes only DB-path helpers and no matcher); it writes the upstream DB to `~/.local/share/lensfun/updates/version_1`, a **machine-local, untracked** path the route depends on and which does not migrate with the repo — re-run it per rig. There is **no lensfun query CLI** in Debian (`lenstool` is unpackaged), which is why `scripts/stack/lens_preflight.py` proves the correction by asking darktable rather than by querying lensfun. Deterministic in pixels; between two measured runs its TIFF differed by one metadata byte — never gate this route on a file hash. Ordering is load-bearing: calibrate in SENSOR space → debayer → warp → register. |

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
Unpackaged on this distro (`source-extractor`/`swarp` are packaged; `scamp` is not) —
x86-deferred.

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

| Tool | Cost | Runs | Linux/CPU/Headless | When & why |
|---|---|---|---|---|
| **Siril SPCC** (spectrophotometric, Gaia DR3 + QE/filter curves + atmosphere) | FREE | siril-native | ✅ / ✅ / ✅ | **Default; obsoletes PCC.** Broadband star-colour truth. Our `spcc_run.py`/`spcc_cone.py` orchestrate it + the local Gaia cone. |
| **PixInsight SPCC** | PAID | GUI-app | ✅ / ✅ / ❌ | The reference implementation; cross-check only. |

**Note:** SPCC is the WRONG step for the narrowband O3 sphere (it equalizes
O3=Ha — dead-end registry). Narrowband colour is Tier 10, not here.

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

## Tier 6 — Noise reduction (linear on starless; and/or nonlinear)

**Siril has NO native chrominance-noise tool** (its docs punt to GIMP) — the
chroma-noise gap our removed corings covered is real, and this tier fills
it. Denoise the STARLESS layer (linear preferred), AFTER deconvolution.

| Tool | Cost | Runs | Linux/CPU/Headless | When & why |
|---|---|---|---|---|
| **NoiseXTerminator** (RC-Astro) | PAID $59.95 | CLI (`rc-astro nxt`) + siril-script | ✅ / AVX2, **CPU-light (lighter than BXT; indic.)** / ✅🖥 | **Best + fastest** AI denoise; `rc-astro` v1.0.0 CLI. **Closes the chroma-noise gap:** AI3 has a *dedicated* chroma control (`denoise_color`, independent of the luminance `denoise` — not one global knob). Exact `rc-astro nxt` flag spelling is unpublished → capture with `rc-astro nxt` no-args on x86 (the bootstrap prints the step). Free CLI for holders, offline-after-activation. |
| **Siril `denoise`** (NL-Bayes; `-da3d`/`-sos`/`-indep`/`-mod`/`-mask`) | FREE | siril-native | ✅ / ✅ / ✅ | **Free, headless, deterministic.** Plain NL-Bayes on stacks; `-da3d` refine, `-sos` background artefacts, `-indep` blocky colour, `-mod` blend, **`-mask` (1.5.0-dev) to confine to a region**. **No native chroma mode** (docs still punt to GIMP — gap confirmed in 1.5.0-dev). Clean default when free+headless matters. |
| **DeepSNR 1.2.1 (Linux)** (StarNet author) | FREE | **native Linux CLI** | ✅ / ✅ (self-contained ONNX, **CPU fallback**) / ✅ | **Cleanest free headless denoiser fit** — trained on astro data, bundled ONNX Runtime (no CUDA/TF), built for automation/Siril. v1.2.1 is the **Linux x64-only** build; INSTALLED here at `/opt/deepsnr-1.2.1-0112`. CLI `-m/--model {1=RGB-only,2=default}`; docs say *"intended for monochrome cameras."* Architecture is not stated on the primary source (NAFNet is a third-party attribution). Luminance-vs-chroma behaviour is undocumented — not a citable chroma-gap fill. A Class-2 binary. |
| **GraXpert denoise** (AI, `-strength` + `-batch_size`) | FREE | CLI + siril-native | ✅ / ✅ 🐢 (**CPU-slow — ~14.5 min/48MP, >30 min large frames**) / ✅ | Free AI denoise, in Siril 1.4; `-batch_size 1–32` trades RAM for speed. CPU-slow is the real cost. Timing probe (onnxruntime `CPUExecutionProvider`): 1024² tile in **71 s** → ≈13–14 min extrapolated per 12 Mpx frame. INSTALLED here as 3.0.2 at `/opt/graxpert-3.0.2/GraXpert-linux/GraXpert` — that figure came from a fork build on the retired box, so re-time it before budgeting a run. Fork-CLI quirk (source-verified): the per-command flags (`-strength`/`-batch_size`/`-ai_version`; BGE `-correction`/`-smoothing`/`-bg`) are subparser-registered and HIDDEN from the top-level `--help` — they work when passed alongside `-cmd`. **LEAD (untested): `pip install graxpert[openvino]` claims ~5× CPU speedup on AVX2/VNNI Intel CPUs = the target rig's exact class** — x86 empirical candidate. No luminance/chroma split (single strength knob). |
| **SyQon Prism** (free "Siril Edition" / paid "Deep") | FREEMIUM | pyscript (**Class-1**) | ✅ via Siril / ✅ (Parallax **Nano** is CPU-only) / **✅ headless** (free tier, `is_cli()`) | 2026 neural (PyTorch NAFNet) denoise; numpy/torch-inside (escape-hatch). Free labels are Zenith/Prism-Siril-Edition/Parallax-**Nano** (not "Mini"). The free "Siril Edition" (`mini` model) branches on `siril.is_cli()` and runs headless — no dialog/license gate (an older community build was GUI-only; verify the free-tier headless run on-rig). |
| **Cosmic Clarity Denoise** (Seti, v6.5) | FREE (donation) | CLI (folder-batch) | ✅ native Linux / 🐢 (~7 min CPU) / ✅ | Free AI denoise; CPU-slow; Class-2 binary. **A FREE chroma-noise control exists here** (candidate free fill for the chroma gap alongside paid NXT): `--denoise_mode {luminance,full,separate}` + **`--color_denoise_strength`** (+ `--separate_channels`) — chroma vs luminance, headless. **CORRECTED 2026-08-03: Sharpen is NOT a plain CLI subprocess** — it is Qt and blocks on a modal dialog (see the Sharpen row). Denoise and Dark-Star ARE headless and verified so on this rig: Denoise completes unattended, Dark-Star prints `Non-Windows system using device: cpu` / `All images processed.` in ~110 s. **INSTALLED + VERIFIED on x86** (`/opt/cosmicclarity-6.6`, bin `SetiAstroCosmicClarity_denoise`, reports **Denoise V6.6 AI3.6**): CPU-only `--disable_gpu` works (~21s/1200px), and the free `--color_denoise_strength` chroma path RUNS, but **the knob SATURATES and is effectively binary**: MEASURED on real data, runs at 0.85 and 1.00 are BYTE-IDENTICAL (same md5) while 0.00 differs — so there is no headroom above the shipped 0.85, and WHERE between 0 and 0.85 it saturates is UNMEASURED. (`--denoise_strength` by contrast does work across its range: 0.0 output is byte-identical to the input, 1.0 differs by sigma 0.7-1.0 ADU.) The earlier "29% background noise cut" was one synthetic frame and did NOT establish that the knob is controllable — it only showed the tool does something. Consequence for BACKLOG:`render-ladder` L2: the CHROMA half of that ladder cannot be run through this CLI. Dark-Star present (models v2.0/v2.1/v2.1c, v2.1c byte-identical to the official asset). **GAP — satellite + super-res do NOT run:** the official bundle's own frozen torch runtime raises `torch._C._sparse has no _spsolve` at startup (the binaries themselves are the official ones; satellite is byte-identical to the GH asset). The community AMD/ROCm rebuild runs them but is a third-party rebuild (geeksville-GraXpert precedent) — NOT adopted. So `anomaly_audit.py`'s streak-kernel removal condition stays **not-fired**: the official detector exists but will not run here. |
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
| **Siril `ccm` (diagonal) + our examine layer** ← the recommended star-neutral *approach* (tool half verified on 1.4.4; the measure→apply design untested) | FREE | siril-native + numpy | ✅ / ✅ / ✅ | **The doctrine-clean, headless star-neutral approach:** a DIAGONAL `ccm` (3×3 + gamma, verified on 1.4.4) IS a per-channel star-neutral balance, and the **ONLY headless neutral-balance path** (Manual Color Calibration has no CLI form). MEASURE the field's mean star colour in our EXAMINE layer (numpy over detected stars — no native command outputs it), then APPLY via `ccm` (`seqccm` batches). Pixel op = a tool; measurement = ours. The design still needs one real-data run. |
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

Sources: the per-topic primary citations live in **`docs/`** (one cited `.md`
per deep-dive — see `docs/README.md`). In brief: siril.org (1.4.0–1.4.4
releases; RC-Astro-in-Siril 2026-06; Zenith 2026-01; Parallax 2026-06),
siril.readthedocs `/latest` (1.5.0-dev commands / denoising / SPCC / platesolving /
Python-API / scripts), rc-astro.com (`rc-astro` v1.0.0 standalone CLI, FAQ,
product pages) + the GitLab RC-Astro script source, GraXpert GitHub **API**
(stable 3.0.2, deconv RC-only in 3.1.0rc2, bug #243), gitlab free-astro/siril-scripts
(VeraLux/SyQon/DBXtract source), starnetastro.com (StarNet2.5.3 / DeepSNR),
setiastro.com (Cosmic Clarity v6.5 / SASpro), mlnoga/nightlight (star-neutral),
hnsky.org (ASTAP), pixinsight.com ImageWeighting (QA metrics), ben.land 2025-12 +
AstroBackyard + PixInsight/Conejero (workflow-order).
