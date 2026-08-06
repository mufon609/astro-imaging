# Lunar lucky imaging — route, toolkit, and first-corpus plan — deep dive

- **Question / scope** — How this workspace carries a LUNAR dataset to its best
  honest outcome: the lucky-imaging processing model (capture many short
  frames → tool-ranked quality selection → aligned best-N% stack → multiscale
  sharpening), which official tools provide each stage on this rig and the x86
  target, and the concrete route + pre-registered experiments for the first
  lunar corpus. The deep-sky chain's solve/SPCC/BGE stages do not apply (no
  stars, no sky background to model) — this class needs its own route through
  the toolkit, under the same contract (tools do all pixel work + measurement;
  one knob per experiment; the user gates every output-shaping run).
- **Context** — 2026-07. Rigs: the previous base rig (Siril 1.4.4 flatpak, GraXpert,
  darktable, Hugin, astrometry.net venv) + the x86-64 target (same toolset +
  the neural x86 binaries). Camera: Nikon Z6III — 5.94 µm pitch (35.9 mm /
  6048 px), 14-bit NEF in ALL drive modes, e-shutter readout 9.3 ms in
  continuous RAW (community-measured) — and the first lunar corpus is shot at
  **70 mm** (24-70/4 S): 17.5″/px, lunar disc ≈ 107 px. User priorities:
  installed tools first where the workflow is documented-proper; picky
  quality selection (best 10/15/20/25 % ladder, pre-registered below).

## Findings

### 1. The lucky-imaging model, mapped onto this repo's stage design

| deep-sky stage | lunar equivalent | tool status |
|---|---|---|
| calibrate (dark/flat) | same mechanics; matched darks apply (short-exposure darks ≈ bias + FPN). Flats optional — single bright target near frame centre; flatless is first-class | Siril, installed, headless |
| frame QA (findstar FWHM/roundness) | **does not transfer** — no stars. Frame quality = the aligner's own per-frame quality metric (Siril planetary registration `quality` 0–1 regdata; PSS Laplace rank; AS!4 gradient estimator). The tools measure; selection is a recipe knob | tool-sourced, per aligner |
| register (star / homography) | **disc/surface alignment**: Siril "image pattern alignment" (DFT, translation) or KOMBAT (template match) — both **GUI-only in 1.4.4** (verified: zero planetary registration commands in the 1.4.4 command reference, and on-rig `help register` restricts the scriptable command to deep-sky star fields). Multi-point (seeing-patch) alignment exists only in AS!4/PSS — and in Siril 1.5-dev as `register_mpp`/`stack_mpp` (piecewise translation, scoped to planetary/lunar seeing) | GUI in 1.4.4; headless arrives with 1.5 |
| stack (rejection mean, all frames) | **quality-SELECTED stack**: `stack … -filter-quality=N%` consumes the planetary registration's quality regdata headless; sum/mean over the best fraction. Rejection still guards transients | Siril, headless once registered |
| solve → SPCC | **skipped — no stars to solve or calibrate on.** Colour truth = the sunlit-disc neutral assumption (daylight/as-shot WB); record the skip + reason per set | n/a (documented skip) |
| BGE / gradient | **skipped** — no sky signal to model at lunar exposures (sky is ~black at 1/2500 s); a background pedestal subtraction only if measured | n/a |
| deconvolution / sharpen | **the load-bearing render stage.** Siril's own docs: "Stacked lunar images can be sharpened very nicely using the Split Bregman or Wiener methods" — `sb` / `wiener` (+ `makepsf blind|manual`) and à-trous `wavelet`/`wrecons` (RegiStax-class layer weighting) are ALL scriptable in 1.4.4 (on-rig probe) | Siril, installed, headless |
| denoise | usually unnecessary (a 100–300-frame stack is deep); the AI denoisers (NXT, GraXpert) are **deep-sky-trained — off-distribution on lunar** (vendor/official docs) | skip by default |
| stretch | minimal — the disc is bright; histogram/curves only. No GHS ladder needed for a first corpus | Siril, headless |
| export | same policy: uncompressed FITS intermediates; judgment surface = full-frame 16-bit PNG via Siril `savepng` (ImPPG's PNG writer is 8-bit — never the finals writer) | Siril, headless |

### 2. Sampling regimes — what focal length decides (Z6III, 5.94 µm)

Scale = 206.265 × 5.94 / FL. Moon ≈ 0.52° ≈ 1870″. Seeing-limited once the
seeing FWHM spans ≥ ~2 px:

| FL (mm) | ″/px | disc px | regime |
|---|---|---|---|
| 70 | 17.5 | ~107 | deeply undersampled — seeing (2–4″) is 0.1–0.2 px, INVISIBLE |
| 400 | 3.06 | ~610 | sampling-limited |
| 800 | 1.53 | ~1220 | transition (critical at ~3″ seeing) |
| 1200 | 1.02 | ~1835 | seeing-limited in average seeing |
| 2000 | 0.61 | ~3055 | fully seeing-limited — lucky imaging essential |

Consequences, mechanism-first:
- **At 70 mm, multi-point alignment buys nothing** — seeing distortion across
  a 107 px disc is sub-pixel; a single translation aligns the whole disc to
  the same accuracy multi-point would. AS!4's MAP advantage is a long-FL
  property. Siril's single-point planetary alignment is NOT a compromise at
  this scale; the free-astro "not capable of high-resolution planetary"
  caveat applies to the seeing-limited regimes.
- **What quality selection rejects at 70 mm** is transparency dips, gust
  vibration and focus drift — not seeing. The stack's measured gain is SNR
  (√N ≈ 10–17× for 100–300 kept frames), which buys the aggressive
  deconvolution/wavelet pass a single frame cannot survive.
- Atmospheric-dispersion RGB misalignment (~1–2″ at moderate altitude) is
  ≤ 0.1 px at 70 mm — the RGB-align stage is unnecessary for this corpus
  (it becomes real at ≥ 800 mm; RegiStax-under-Wine or channel-split
  re-registration are the known fixes there).
- From ~800 mm the regime flips: frame selection pays directly in
  resolution, keep-percentages drop, multi-point alignment starts earning
  its keep, and the AS!4/PSS class becomes the documented-proper toolset.

### 3. Toolkit audit — lunar stackers + finishers (2025–26, primary-sourced)

**Stack/align:**
- **Siril 1.4.4** (installed, both rigs) — headless: NEF→SER/FITS-sequence
  conversion (`convert [-debayer] [-ser]`, libraw), quality-filtered stacking
  (`-filter-quality=N%`), sb/wiener/rl deconvolution, wavelets, PNG16 export.
  GUI-only: the planetary registrations (pattern/KOMBAT) that produce the
  quality regdata. Lossless-NEF only (HE/HE★ are TicoRAW — no libraw decode).
- **Siril 1.5-dev `register_mpp`/`stack_mpp`** — Siril's own multi-point
  planetary registration (piecewise translation). Not in 1.4.4. **The
  pre-registered adoption test when 1.5 reaches stable**: it would close both
  the headless gap and the multi-point gap in the already-central tool.
- **PlanetarySystemStacker 0.9.8.3** (GPLv3, pip) — the ONLY headless
  Linux-native multi-point stacker: real CLI (Surface/Planet modes,
  `--stack_percent`, drizzle to 3×, in-tool dark/flat, run protocol), its own
  Laplace/Sobel/gradient frame ranking. **Dormant since 2023, pins
  `numpy<1.23`** → dedicated older-Python venv; author-claimed AS!3-parity
  quality. If adopted: a frozen-tool adaptation with a removal condition
  (Siril 1.5 MPP stable, or PSS revival).
- **AutoStakkert! 4** (freeware, Windows) — the community quality reference:
  MAP multi-point, strongest quality estimation, drizzle. Author-sanctioned
  under Wine on x86-64. Latest build beta-flagged (4.0.13, 2025-02); batch is
  semi-manual (no documented unattended mode). The escalation tool for the
  seeing-limited regime, not for a 107 px disc.
- **AstroSurface W5** (2026-05, freeware, Windows GUI) — active all-in-one
  (stack + wavelets + Wiener/Van-Cittert deconv); no CLI; Wine unverified.
- **RegiStax 6** — dead since 2011; only its RGB-Align retains a niche (Wine,
  official instructions). **waveSharp 3.0** is its wavelet successor — now
  with a **native Linux build** (2025-12) but frozen/archived 2026-03;
  GUI-only; OKLab wavelets + threshold-based star-free COLOUR BALANCE.
- **ImPPG 2.1.0** (GPL-3, native Linux, active 2025-11) — Lucy-Richardson +
  adaptive unsharp with live preview; Lua batch scripting but GUI-launched
  (semi-headless); PNG output 8-bit-only (export TIFF16/FITS).
- **Lynkeos** macOS-only; **Stackistry** dormant 2018; **eise.app** (2026)
  browser-based stacker — watch, not a pipeline stage. **PIPP** abandoned;
  Siril `convert -ser` replaces it on Linux. **ffmpeg cannot read/write SER.**
- **Mosaics** (long-FL future): Siril mosaics are astrometric-only (need
  plate solves — impossible on lunar panes); the Linux route is **Hugin**
  (installed; crater control points work where star fields fail), mosaic/
  rectilinear mode, TIFF16 end-to-end.

**AI tools on lunar (verdict: not the route):** BXT officially accommodates
lunar via manual-PSF mode (and the standalone RC-Astro CLI 0.9.9 now runs on
Linux, integrated in Siril since 2026-06), but the community-preferred lunar
results remain classical wavelets/deconvolution — treat BXT-on-lunar as a
bracketed x86 experiment at most. NXT and GraXpert denoise are deep-sky-
trained (vendor docs) — off-distribution on lunar; skip.

### 4. Z6III capture doctrine (for the acquisition checklist, next session)

- **Format: Lossless-compressed 14-bit NEF only** — HE/HE★ (TicoRAW) have no
  libraw/open decode; N-RAW video has NO Linux decode path (Resolve-Linux
  excluded — dead end); ProRes RAW HQ decode landed in ffmpeg 8.0 (2025-08,
  probe-before-trust); H.265 10-bit is the video fallback (DX 4K ≈ 1:1
  photosites; FX 4K downsamples 1.57× — avoid).
- **Mode: Continuous H-extended, ELECTRONIC shutter, 20 fps full-res NEF** —
  e-shutter rolling readout (9.3 ms) smears 0.14″ at lunar drift — harmless;
  no shutter shock. Buffer ≈ 1000 frames on a VPG400-class CFexpress B
  (~600 MB/s sustained); ≈ 30 MB/frame. HSFC+ C60/C120 (JPEG-only, fw ≥2.00
  for FINE) is the volume fallback for the seeing-limited regime.
- **Exposure:** looney-11 transposed to the lens's sharp aperture (f/5.6–f/8
  + ISO 100–800; stopping a telephoto to f/11 shrinks the aperture and raises
  the diffraction floor); shutter 1/500–1/1000 s (freezes atmosphere; drift
  is negligible); histogram peak ~50–70 %, never clip highlands.
- **Technique:** MF in magnified live view on the TERMINATOR (refocus between
  bursts as optics cool); moon > ~40° altitude; terminator phases carry the
  relief (full moon is flat light); VR/IBIS Off on a rigid tripod (test once
  both ways); 3–6 bursts of 250–500 frames, re-centre between bursts;
  1000–2000 frames/target total; sensor dust is soft at f/5.6–f/8 (Z6III has
  no sensor shield — mind cap-off swaps).

### 5. The route for the FIRST corpus (july26, 70 mm) — proposed, user-gated

Corpus facts (measured): darks 310 × uniform 1/2500 s | ISO 800 | 70 mm |
Lossless NEF (22:45–22:50); lights ≈ 29 GB inbound (≈ 1000–1200 NEFs at that
size), same-night. At this scale the installed-Siril route is documented-
proper end to end except one step:

1. **Master dark** — Siril: convert CFA → `stack rej 3 3 -nonorm -32b`
   (winsorized, uncompressed, 32-bit master per the ratified end-to-end-32-bit
   chain). Record + raw deletion per user order (re-stageable).
2. **Lights preflight** — exiftool uniformity (must match the darks'
   1/2500 | 800 | 70 mm | Lossless), `acquisition.json` seeded + `mount`
   declared; loud stop on mismatch.
3. **Calibrate** — subtract master dark in sensor space (CFA), then debayer
   (same order doctrine as the deep-sky chain).
4. **Register** — the one open mechanism choice (user decides):
   - **(a) Siril GUI image-pattern-alignment** (selection box on the disc;
     one GUI interaction per set) → quality regdata in the .seq → everything
     downstream headless. Installed today, documented-proper.
   - **(b) PSS headless Planet mode** (`--stack_percent`, its own ranking) —
     fully scriptable, but adopts a dormant tool (venv-pinned, removal-
     conditioned).
   Recommendation: (a) for the first corpus — installed tool, zero new
   dependencies, and the GUI step is one user click in a user-gated stage
   anyway; pre-register (b) as the automation alternative.
5. **The picky ladder (pre-registered, user-declared):** one knob =
   keep-fraction; values **best 10 / 15 / 20 / 25 %** by the registration's
   own quality metric (`stack … -filter-quality=N% -32b`, sum or rej-mean —
   bracket includes a control at 100 % to measure what selection buys).
   Each stack preserved (`cp` to tagged names), judged like-encoded.
   Hypothesis: at 107 px disc scale, selection rejects transparency/vibration
   outliers; expected a real but modest sharpness delta and a monotonic SNR
   cost with pickiness — the user's eyes pick the operating point.
6. **Sharpen ladder (after a stack is chosen):** `makepsf blind` (bracket:
   `manual -gaussian` sizes) → **`sb` vs `wiener`** (the officially-lunar-
   recommended pair) one knob at a time; then a `wavelet 5 2` / `wrecons`
   coefficient bracket as the alternative arm. Judged on full-frame PNG16
   (the user zooms in their own viewer — no crop surfaces).
7. **Colour:** as-shot/daylight WB (sunlit-disc neutral assumption — no
   SPCC possible, recorded as the documented skip); optional mineral-moon
   `satu` increments as a user-gated aesthetic ladder. No rmgreen, no BGE.
8. **Export:** Siril `savepng` 16-bit full frame → `web/results/july26/judge/`.

### 6. Documented gaps (candidate dead-end / register entries)

- **Headless planetary registration does not exist in Siril 1.4.4** — the
  quality regdata source is a GUI step. Retired by: Siril 1.5 stable
  (`register_mpp`/`stack_mpp`), or PSS adoption.
- **Headless star-free white balance** — no Siril command implements a
  disc-threshold WB (waveSharp's COLOUR BALANCE is the GUI tool for it).
  Neutral-assumption + user eyes covers the 70 mm corpus.
- **N-RAW on Linux** and **HE/HE★ NEF anywhere in the pipeline** — no open
  decoders (2025-26). Shoot Lossless; skip N-RAW.

## Sources

Primary: siril.readthedocs.io (registration / stacking / deconvolution /
atrouwavelets / Commands — 1.4.4 command reference full-text-verified for the
planetary-commands absence; deconvolution page carries the lunar sb/wiener
recommendation), free-astro.org/index.php/Siril (multi-point statement),
gitlab free-astro `command_list.h` (1.5-dev mpp + wavelet-denoise surface),
autostakkert.com (download/beta/guides + Wine statement),
github.com/Rolf-Hempel/PlanetarySystemStacker + PyPI (CLI source-verified),
astrosurface.com, astronomie.be/registax (+ linux.html),
codeberg.org Corbee/waveSharp3.0 (installation + reference guides),
github.com/GreatAttractor/imppg (+ scripting.md), siril.org 2026-06 RC-Astro
news + rc-astro.com technical manual, github.com/Steffenhir/GraXpert,
hugin.sourceforge.io mosaic tutorials, Nikon Z6III online manual (release
modes / HSFC+ / RAW recording / VR / d5) + fw 2.00 notes, horshack
RollingShutter DB, libraw.org supported cameras, FFmpeg 8.0 ProRes RAW
commit, photographylife moon guide, skyatnightmagazine DSLR-moon-stacking,
Cloudy Nights threads (AS!4 lunar tutorial; BXT-for-planets; single-vs-stack;
video-vs-stills; wavelets RS6-vs-waveSharp). On-rig: Siril 1.4.4 flatpak
`help` probe (register/stack/wavelet/wrecons/rl/convert/boxselect/setref);
exiftool EXIF sweep of the july26 dark set.

## Verdict / recommendation

For the 70 mm july26 corpus: the **installed-Siril route** (§5) — it is
documented-proper at this image scale, headless everywhere except one
GUI registration click, and identical on both rigs. PSS is the headless
alternative if that click must go; AS!4-under-Wine and the waveSharp/ImPPG
finishers enter only when a long-focal (seeing-limited) corpus arrives, each
as a bracketed experiment. Pre-register the Siril 1.5 MPP adoption test — it
is the convergence point where the whole chain goes native-headless.

## Status

**EMPIRICALLY TESTED on the first corpus (two sets, 220 + 809 frames), with
refinements the run itself measured** — now encoded in the class builder
`scripts/stack/run_lunar_pipeline.sh` (PROVISIONAL as-written; generalized
from the runs that produced the records):

- Registration = Image Pattern Alignment with a **track-covering selection**
  and the **reference pre-set to the sequence middle** (circular DFT
  correlation wraps beyond ± min(w,h)/2 — the two-disc failure); KOMBAT is a
  measured dead end on this class; failed GUI runs poison the .seq (delete +
  rebuild). All mechanisms + numbers: `docs/dead-ends.md`.
- 1.4.4 planetary regdata carries **no per-frame quality even on success** —
  the picky ladder needs a ranking tool (PSS/AS!4, x86); the full-stack
  control ships from this rig and is the ladder's bracket.
- Finish (user-ratified on this corpus): sb blind-PSF deconvolution (wiener
  equal on-disc but leaves a frame-edge artifact band) → disc-neutral
  diagonal `ccm` from inside-disc `stat` medians, gains measured PER SET
  (same-night sets agreed to 0.2% — the rule verified itself) → NO
  saturation (mineral satu 0.2/0.4 both failed the user's eyes at this disc
  scale) → linear PNG16 pairs at one clip-safe integer gain.
- The quality-selection hypothesis stays open for the x86 ladder; the §4
  capture card was measured 2.5–3 stops under and corrected (now in the
  acquisition checklist).

## Graduation

- `TOOLS.md` — Tier L added, then updated to the verified route + builder.
- `BACKLOG.md` — item 21 (route resolved; x86 ladder + next-capture remain).
- `docs/dead-ends.md` — registration/aliasing/seq-hygiene/quality entries
  with their numbers, and the §4 lunar block GRADUATED into the acquisition
  checklist with the measured exposure card.
- `scripts/stack/run_lunar_pipeline.sh` — the class builder (prep → stage →
  calibrate → register → verify → stack → sharpen → wb → surfaces).
