# TOOLS.md — the astrophotography toolkit, by pipeline tier

A tool **audit**, not a prescribed chain. For each pipeline tier: what the
tier does, the options, when/why to pick each, and the alternatives —
filtered for what actually runs on **this rig** (x86-64 Kali, i7 14th-gen,
32 GB, 1 TB NVMe, **no GPU**, headless-preferred). The pipeline is a
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
   lives** (the resolved tool-vs-hand-roll test — see `docs/siril-pyscript-headless.md`):
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
synthetic routes ([`docs/synthetic-flats-and-bias.md`](docs/synthetic-flats-and-bias.md)):
GraXpert `-correction Division` for dust-safe vignetting (x86 official; Siril's
native `subsky` is subtraction-only — empirically confirmed on 1.4.4), or a Siril
sky flat ONLY when the field is not frame-filling faint (else it bakes in and
attenuates the IFN); **bias** = skip on CMOS (matched darks carry it; dark-scaling
is invalid because CMOS dark current isn't constant across exposure), a synthetic
constant offset if a flat needs one. A real flat stays primary. PI/APP only as
reference or for a normalization edge case.

**Workflow specifics (headless, 1.4.4 — `docs/siril-stacking-workflow.md`):** masters
bias/dark `-nonorm`, flats `-norm=mul`; lights `-norm=addscale`. **Rejection by sub
count:** ≤6 percentile (`p`), ~7–50 winsorized (`rej w 3 3`), >50 GESD (`rej g 0.3 0.05`
— fraction+significance, NOT sigmas), large+gradients linear-fit (`rej l 3 3`).
Weighting `-weight={wfwhm|noise|nbstars|nbstack}` (unified — the old `-weight_from_*`
flags are REMOVED and will error migrated scripts). Registration: `-2pass`→`seqapplyreg`,
homography for wide fields, lanczos4+clamp. **Drizzle is a `register` option, not `stack`**
(CFA-drizzle 1×/pixfrac 1.0 for OSC; upscale only if sampling+dither justify —
[[plate-solving-and-drizzle]]). **Two real gaps vs PixInsight WBPP:** no Local
Normalization and no PSF-Signal-Weight equivalent (our audit layer can supply a PSFSW
proxy — [[objective-qa-defect-metrics]]).

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
retirement** (BACKLOG). **Trailed-class robustness ranking (mechanism —
`docs/plate-solving-and-drizzle.md`):** (1) astrometry.net fed our own
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
help; no empirical solve was possible — the image data is deleted and this is
the arm rig. The x86 test above is definitive.)

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
| **darktable + lensfun** (`darktable-cli --style <s> --style-overwrite`) | FREE | CLI | ✅ / ✅ / ✅ | **THE ADOPTED FIX for this class — measured WIN, in production, shipped.** An OFFICIAL *measured* lens profile, immune to the index-sparsity that kills a per-frame SIP fit. darktable must be built against Lensfun (Debian's is; Debian's **RawTherapee is NOT** — it doesn't link lensfun, so its auto-match is unavailable). On july14, Siril `seqtilt` control → corrected → shipped 168 fr: **off-axis aberration 0.57→0.31→0.25 px**, stars 5,095→10,707→11,805, 54/54 register. Sharpness is NULL (truncated mean FWHM 3.20→3.28) and the one-sided term is uncorrected (sensor tilt 0.50→0.42→0.51) — claim neither. **The style is pinned in-repo** (`scripts/darktable/*.dtstyle` + `install_styles.sh`, verified to reproduce the warp to 0.000 px) — no GUI step. **`--style-overwrite` is REQUIRED**, else the style is silently ignored. `modify_flags=1` (distortion only): the GUI default 7 adds **vignetting**, which FIGHTS a master/sky flat. **`--icc-type SRGB`, never `LIN_REC709`** (match Siril's tag — `docs/dead-ends.md`). **The style carries ONLY `modify_flags`; `focal`, `scale`, `camera` and `lens` are all baked but IGNORED — darktable re-detects them from EXIF and recomputes the autoscale (MEASURED: focal 70 vs 24 give opposite-sign warps; scale 1.046 vs 0 vs 1.5 are identical to 0.000 px; a swapped lens string gets that lens's own profile). So ONE style is camera-, lens- and focal-general.** **The same mechanism is a trap: darktable NEVER FAILS** — an unmatched lens gets NO correction, silently (0.000 px over 413 stars, exit 0, nothing in the log), and a wrong-but-present lens gets a wrong model just as quietly. It cannot be relied on to degrade loudly: the CHAIN must assert EXIF camera+lens+focal against the DB per set and STOP on a miss ("did the warp happen" is not enough — it passes the wrong-lens case). Debian's lensfun 0.3.4 lacks the Z6III → **`lensfun-update-data`**, which ships in **`liblensfun-bin`** (NOT `python3-lensfun` — that package exposes only DB-path helpers and no matcher); it writes the upstream DB to `~/.local/share/lensfun/updates/version_1`, a **machine-local, untracked** path the route depends on and which does not migrate with the repo — re-run it per rig. There is **no lensfun query CLI** in Debian (`lenstool` is unpackaged), which is why `scripts/stack/lens_preflight.py` proves the correction by asking darktable rather than by querying lensfun. Deterministic in pixels; its TIFF differs by one metadata byte per run, so never gate on a file hash. Ordering is load-bearing: calibrate in SENSOR space → debayer → warp → register. |

**Why the Siril-native `-disto=` route is not the one in production (measured, not
theoretical):** `register -disto=` needs a trustworthy distortion model and this rig
cannot *fit* one. Siril's own matcher fails ~36° fields (roundness + catalogue depth
both eliminated — `docs/dead-ends.md`), and astrometry.net's SIP is **not reproducible**
at wide index scales (two solves of the same fixed lens disagree 65 px median; more
field stars fix only the linear solve). Feeding it in is a measured LOSS. **This blocks
WCS-reprojection equally** (SWarp / astropy `reproject` need the same per-frame
solution). The mechanism is sound and the model gap is **CLOSED** — by a measured
profile applied upstream (the darktable+lensfun row), which needs no `-disto=` at all.
Nikon's own coefficients also ship in every NEF (exiftool decodes
`RadialDistortionCoefficient1/2/3` + `DistortionCorrection: On (Required)`), but they
sit in a Nikon-private block **no headless Linux tool applies** — a better model if
darktable's "embedded metadata" lens method ever reaches it, not a blocker today.

**WCS-reprojection dust-safety notes (if the model gap ever closes):** SWarp's
**`SUBTRACT_BACK=Y` is the DEFAULT and must be turned OFF** — it subtracts a sky
model from every input and would eat frame-filling IFN. SWarp conserves flux only
with equal-area output projections (`FSCALASTRO_TYPE` = NONE|FIXED); its author
puts the TAN-safe limit at ~10° of field, so a ~30° field should not default to TAN.
In astropy `reproject`, `reproject_interp` is **not** flux-conserving (and offers no
Lanczos kernel); `reproject_adaptive` has `conserve_flux` and is documented as more
accurate under strong distortion / large sky areas; `reproject_exact` is an exact
drizzle valid at any FOV but slow. `reproject_and_coadd`'s `match_background` models
only a constant additive offset and forfeits the absolute zero point. astropy is
x86-gated.

**How this class is MEASURED — Siril `seqtilt`, and only `seqtilt`.** It is the tool's
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
| **GraXpert** (AI BGE, or RBF/spline) | FREE | CLI + siril-native | ✅ / ✅ (**BGE is CPU-fast** — inference runs once on a ~240px thumbnail, O(1)) / ✅ | **Default AI gradient removal**, integrated in Siril 1.4 and standalone (`graxpert -cmd background-extraction`; `-cli` deprecated). **`-correction Division` = the headless synthetic-flat gap-filler** (multiplicative; smooth VIGNETTING only — BACKLOG). CLASS LIMIT (dead-end): the AI absorbs frame-filling FAINT nebulosity as gradient — use a plane/off for object-filling fields. |
| **Siril `subsky`** (`-rbf` or polynomial degree) | FREE | siril-native | ✅ / ✅ / ✅ | The retention mode — a first-degree plane removes the gradient class without absorbing localized nebulosity. Our `bgelin plane`. |
| **VeraLux Nox** (pyscript) | FREE | pyscript-GUI | ✅ / ✅ / ❌ | scipy sparse-Poisson gradient solve — a **Class-1 numpy-inside** script (mechanism = scipy, escape-hatch only) and **GUI-mandatory PyQt6** (not headless-drivable). (A prior "Seti AutoBGe" reference is unverified — no such script confirmed in the repo.) |
| **PixInsight DBE / GradientCorrection / MARS** | PAID | GUI-app | ✅ / ✅ / ❌ | DBE = manual sample gold standard; **MARS** (2026) = PI's new AI gradient model. Reference/cross-check. |

**Pick:** GraXpert AI for real gradients; Siril plane for object-filling
fields (the retention rule stands regardless of rig).

## Tier 5 — Deconvolution / sharpening (LINEAR, BEFORE denoise)

**2026 consensus: deconvolution goes early, in linear, BEFORE any noise
reduction** (NR destroys the fine low-contrast detail decon needs; BXT
explicitly dislikes denoised data). This tier was a **dead-end on the arm
rig** (no tool + unstable PSF on trailed data) — **it REOPENS on x86**, and
`BlurXTerminator` "correct only" can even fix the elongated/trailed stars
that were the base rig's core data problem.

| Tool | Cost | Runs | Linux/CPU/Headless | When & why |
|---|---|---|---|---|
| **BlurXTerminator** (RC-Astro, `--correct-only` + sharpen) | PAID $99.95 | CLI (`rc-astro bxt`) + siril-script | ✅ (**Ubuntu 22.04+ "or equivalent"; Kali not vendor-certified — verify**) / **AVX2 (i7-14700 ok); no vendor CPU figures → `--benchmark-all`** / ✅ | **Best-in-class**; standalone **`rc-astro` v1.0.0 CLI** + Siril script, no PixInsight host. `--correct-only` corrects PSF aberration without sharpening → fixes star elongation/trailing. Perpetual license, **CLI free for holders, offline after activation**. Linux GPU = **NVIDIA-CUDA only** → no-GPU rig runs the supported CPU fallback. Call `rc-astro bxt` directly (Class-2). See `docs/rc-astro-cli-linux.md`. |
| **GraXpert deconvolution** (`deconv-obj` / `deconv-stellar` AI) | FREE | CLI + siril-native | ✅ / ✅ 🐢 (minutes CPU) / ✅ | **PRE-RELEASE only — NOT a shipped stable feature.** Official stable is **3.0.2 (BGE+denoise only)**; deconv exists only in the 3.1.0-RC line and the installed **`3.2.0a2` third-party fork** (`geeksville`, not upstream — pin the official build). Real but undocumented CLI (`-cmd {deconv-obj,deconv-stellar}`, flags in BACKLOG); object-mode artifact bug **#243 open and unaddressed**. BXT is the mature path. |
| **AstroSharp** (DeepSkyDetail) | FREE | Win .exe / R-Shiny | ❌ **dead end for us** / — / ❌ | **NOT viable**: TIFF-only with a **<600 KB file cap** (unusable full-frame), **no native Linux**, **no CLI**, C++ (no Python), multi-platform issue open+unresolved since 2023. Drop from consideration. |
| **Cosmic Clarity — Sharpen** (Seti) | FREE (donation) | CLI (folder-batch) | ✅ native Linux (needs gnome-terminal) / 🐢 (**15–30 min CPU**) / ✅ | Free stellar/non-stellar sharpen, **v6.5 (AI3.5s-c)**; leading free BXT alternative, a notch below; CPU-brutal without a GPU. A Class-2 binary driver. |
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
| **NoiseXTerminator** (RC-Astro) | PAID $59.95 | CLI (`rc-astro nxt`) + siril-script | ✅ / AVX2, **CPU-light (lighter than BXT; indic.)** / ✅🖥 | **Best + fastest** AI denoise; `rc-astro` v1.0.0 CLI. **Closes the chroma-noise gap:** AI3 has a *dedicated* chroma control (`denoise_color`, independent of the luminance `denoise` — not one global knob). Exact `rc-astro nxt` flag spelling is unpublished → capture with `rc-astro nxt` no-args on x86 (`docs/rc-astro-cli-linux.md`). Free CLI for holders, offline-after-activation. |
| **Siril `denoise`** (NL-Bayes; `-da3d`/`-sos`/`-indep`/`-mod`/`-mask`) | FREE | siril-native | ✅ / ✅ / ✅ | **Free, headless, deterministic.** Plain NL-Bayes on stacks; `-da3d` refine, `-sos` background artefacts, `-indep` blocky colour, `-mod` blend, **`-mask` (1.5.0-dev) to confine to a region**. **No native chroma mode** (docs still punt to GIMP — gap confirmed in 1.5.0-dev). Clean default when free+headless matters. |
| **DeepSNR 1.2.1 (Linux)** (StarNet author) | FREE | **native Linux CLI** | ✅ / ✅ (self-contained ONNX, **CPU fallback**) / ✅ | **Cleanest free headless denoiser fit** — trained on astro data, bundled ONNX Runtime (no CUDA/TF), built for automation/Siril. v1.2.1 is the **Linux** build (Win 1.2.2 / mac 1.2.0). CLI `-m/--model {1=RGB-only,2=default}`; docs say *"intended for monochrome cameras."* Architecture is not stated on the primary source (NAFNet is a third-party attribution). Luminance-vs-chroma behaviour is undocumented — not a citable chroma-gap fill. A Class-2 binary. |
| **GraXpert denoise** (AI, `-strength` + `-batch_size`) | FREE | CLI + siril-native | ✅ / ✅ 🐢 (**CPU-slow — ~14.5 min/48MP, >30 min large frames**) / ✅ | Free AI denoise, in Siril 1.4; `-batch_size 1–32` trades RAM for speed. CPU-slow is the real cost. **LEAD (untested): `pip install graxpert[openvino]` claims ~5× CPU speedup on AVX2/VNNI Intel CPUs = the target rig's exact class** — x86 empirical candidate. No luminance/chroma split (single strength knob). |
| **SyQon Prism** (free "Siril Edition" / paid "Deep") | FREEMIUM | pyscript (**Class-1**) | ✅ via Siril / ✅ (Parallax **Nano** is CPU-only) / **✅ headless** (free tier, `is_cli()`) | 2026 neural (PyTorch NAFNet) denoise; numpy/torch-inside (escape-hatch). Free labels are Zenith/Prism-Siril-Edition/Parallax-**Nano** (not "Mini"). The free "Siril Edition" (`mini` model) branches on `siril.is_cli()` and runs headless — no dialog/license gate (an older community build was GUI-only; verify the free-tier headless run on-rig). |
| **Cosmic Clarity Denoise** (Seti, v6.5) | FREE (donation) | CLI (folder-batch) | ✅ native Linux / 🐢 (~7 min CPU) / ✅ | Free AI denoise; CPU-slow; Class-2 binary. **A FREE chroma-noise control exists here** (candidate free fill for the chroma gap alongside paid NXT): `--denoise_mode {luminance,full,separate}` + **`--color_denoise_strength`** (+ `--separate_channels`) — chroma vs luminance, headless. gnome-terminal is needed only for Super-Res + Satellite-Removal (Qt, `QT_QPA_PLATFORM=offscreen`/Xvfb); Sharpen/Denoise/Dark-Star are plain CLI subprocesses (Dark Star has a `headless` gate). Source-verified, quality unmeasured — x86 test. |
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
| **StarNet2 v2.5.3** (native x86 CLI) | FREE | CLI + siril-native | ✅ / ✅ (self-contained ONNX, no TF/Torch/CUDA) / ✅ | **Free default on x86** — native binary. **`-n/--unscreen <FILENAME>`** writes a star-layer file (not a bare toggle); highlight protection is on by default so the opt-out is **`-d/--disable-highlights-protection`**. Keeps field-star flux; safe on resolved objects. CPU-only on Linux (no documented GPU path). Siril integration is thin ("point Siril at the executable"). Class-2 binary. |
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
| **Siril `autostretch` / `autoghs` / `linstretch` / `curves`** | FREE | siril-native | ✅ / ✅ / ✅ | **Default.** Linked autostretch (broadband), GHS (generalized hyperbolic, deep-data control), linstretch (black-point + sat), curves. All headless. |
| **VeraLux HyperMetric Stretch** | FREE | pyscript-GUI | ✅ / ✅ / 🖥 | Well-regarded 2026 photometric hyperbolic stretch (Roger-Clark "true colour" lineage); numpy-inside, needs Xvfb. |
| **Cosmic Clarity / Seti Statistical Stretch** | FREE | CLI / pyscript | ✅ / ✅ / ✅🖥 | Statistical-median-target stretch; a good automated option. |
| **Arcsinh + Histogram (classic)** | FREE | siril-native / PI | ✅ / ✅ / ✅ | Arcsinh preserves star colour; the traditional broadband move. |

**Pick:** Siril autostretch/GHS for headless; the pyscript stretches only if
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
the only missing native piece, and it belongs in our audit layer anyway —
[[objective-qa-defect-metrics]]). Nightlight (dormant) does a brightest-quartile
two-point RGB balance — a mechanism reference, but the OIII-lift is OUR inference,
not its documented purpose (see the Nightlight row).
Two mechanisms, don't conflate: **star-anchored** neutral balance (ccm+measure /
Nightlight) vs **nebula/QE-anchored** unmix (Alchemy/DBXtract, OSC dual-band).
Star-neutral is a valid mechanism but NOT a mainstream-named technique — the
mainstream decouples stars (remove → boost OIII starless → re-add stars). See
`docs/narrowband-star-neutral-options.md`.

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
  `--lossless` PNG8+PNG16 remains the judgment surface.
- **Colorimetry** — Siril embeds ICC via `icc_assign {sRGB|…}` + a save-time
  Preference (iCCP full profile), so the vendored `srgb.icc` is no longer needed
  once `savepng`/`savetif` own the write.

---

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
600 KB TIFF cap.)

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
philosophy question — `docs/siril-pyscript-headless.md`): the **VeraLux** suite
(Silentium / HyperMetric / Nox / Vectra / Alchemy / …), **SyQon** free tiers
(Zenith / Prism / Parallax-Nano), **SCUNet**, **DBXtract** — these do the pixel
math in their own numpy/scipy/pywt/torch (mechanism = numpy → sanctioned
*alternative with a removal condition*, never "a tool"). Most are **GUI-mandatory
PyQt6 with no arg vector → NOT headless-drivable even under Xvfb**; only
dual-mode ones (Statistical_Stretch, SyQon Prism `--no-gpu`) run headless. Prefer
a compiled tool (Siril-native / RC-Astro / GraXpert / StarNet / DeepSNR / Cosmic
Clarity — all Class-2 binaries) whenever one provides the mechanism.

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
refinements from the multi-source validation (`docs/graxpert-3x-and-workflow-order.md`):
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
