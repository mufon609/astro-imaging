# Astrophotography processing pipeline

Repo tracks the **processing pipeline** (Siril scripts + notes), not image data
(see `.gitignore`). Iterate on the pipeline, commit, re-run, compare previews;
revert with git if a change makes things worse.

## Environment

- Nikon Z6 III, raws converted to DNG (Adobe DNG Converter 18.4), 14-bit, RGGB
- Siril 1.4.4 as user flatpak: `flatpak run --command=siril-cli org.siril.Siril`
  - Flatpak sandbox has `home`/`host` access but **its own /tmp** — scripts must
    live under the home dir, not /tmp
- Host: Kali linux arm64, 4 cores, 7.7GB RAM, ~40GB free disk
  - Pipeline uses 16-bit intermediates + per-stage cleanup to stay within disk;
    final stack is 32-bit float

## Session 07-02-26 inventory (verified via exiftool + siril stat)

| dir    | n  | exposure | ISO | f/  | mm | taken               | pixel-level check |
|--------|----|----------|-----|-----|----|---------------------|-------------------|
| lights | 32 | 20s      | 200 | 4.0 | 24 | Jul 2 23:55–Jul 3 00:14 | mean 1065, bg ~57 ADU above offset, stars saturate |
| darks  | 74 | **1/10s**| 200 | 4.0 | 24 | Jul 5 11:41–11:55 (daytime) | mean 1007.9 ≈ bias, σ 4.09, hot px to 1918 |
| biases | 59 | 1/200s   | 200 | 4.0 | 24 | Jul 5 11:38         | mean 1008.0, σ 4.27 ✓ |
| flats  | 58 | 1/200s   | 200 | 4.0 | 24 | Jul 5 11:35–11:37   | median 1619, peak ~3200/16383 |

Sensor offset (black level) ≈ 1008 ADU.

### Issues found (acquisition, not organization — folders are filed correctly)

1. **Darks don't match lights**: 1/10s vs 20s (and taken at daytime temps).
   A 1/10s dark contains essentially zero dark signal (its stats are identical
   to bias). Standard dark subtraction is impossible; dark *optimization*
   would be scaling by ~200x — garbage. → Pipeline uses the master dark only as
   a bias-equivalent + **hot-pixel map for cosmetic correction** (`-cc=dark`).
   Hot pixels that only appear at 20s won't be mapped; dithering + rejection
   stacking has to absorb them.
2. **Flats are underexposed**: peak ~20% of full scale (ideal is ~50%).
   Usable — stacking 58 recovers SNR — but they add noise. Watch corners after
   flat division.
3. Flats/biases/darks shot 3 days after lights. Same lens/aperture per EXIF, so
   flats remain valid **if** the lens was untouched (dust/rotation) in between.
4. Session underexposed overall: ISO 200, sky bg only ~57 ADU over offset.
   Z6III's second gain stage starts at ISO 800 — ISO 200 has the high-read-noise
   path. Expect heavy stretch, watch for pattern noise.

## Pipeline design (v2)

`scripts/run_pipeline.sh <session-dir>` orchestrates five siril-cli stages,
deleting each stage's intermediates before the next (disk-limited):

0. preflight — exiftool check: hard-fails if a dir mixes exposure/ISO
   (protects against stale frames after a re-shoot), warns on darks/lights
   exposure mismatch and ISO mismatches
1. `10_master_bias.ssf` — stack biases, Winsorized rej 3/3, no norm
2. `20_master_flat.ssf` — calibrate flats with master bias, stack norm=mul
3. `30_master_dark.ssf` — stack darks
4. `40_lights.ssf` — calibrate (`-dark` + `-cc=dark` hot-pixel removal, flat,
   equalize_cfa, debayer) → register → 32-bit rej stack norm=addscale +
   rgb_equal. Same command is correct for matched *and* mismatched darks.
5. `50_postprocess.ssf` — planar background extraction + autostretch → JPEG
   preview. Run standalone via `scripts/run_post.sh <session>` to iterate on
   post without re-registering (~seconds instead of minutes).

Masters live in `<session>/work/masters/` and are **rebuilt automatically**
when any source DNG is newer than the master (drop in re-shot frames and just
re-run). Big FITS result is overwritten each run (`results/stack_latest.fit`);
small timestamped JPEG previews accumulate for run-to-run comparison.

## Iteration log (session 07-02-26)

| preview | variant | verdict |
|---|---|---|
| `preview_20260705_131357` | v1: no gradient removal | strong moonlit gradient, edges bright |
| `preview_20260705_131715` | subsky RBF s=20 tol=0.5 | **worse** — overfit, dark hole in sky center |
| `preview_20260705_131832` | subsky poly degree 1 | keeper — gentle, no artifacts |
| `preview_20260705_132244` | same, full-pipeline validation run | = |

Registration drops frames 27 & 32 (star matching fails despite ~390 stars —
field drift on fixed tripod reduces overlap with reference). 30/32 stacked.
Try `-2pass` registration if more frames start dropping.

The remaining bright-bottom gradient is real sky (waning gibbous moon + horizon
glow); stronger removal needs treeline-aware masking (GraXpert) — future work.

## Iteration ideas (not yet tried)

- Registration with distortion handling (24mm wide field, corner stars)
- `-filter-wfwhm` / quality filtering of lights before stack
- Drizzle (probably not: undersampled? no — 24mm @ 5.9µm is heavily oversampled
  spatially, skip)
- Background extraction (`subsky` / GraXpert — installed at ~/.local/bin/graxpert)
- Photometric color calibration (`pcc`) vs `rgb_equal`
- Denoising after stretch; starnet/star recomposition

## Re-shoot plan for THIS session (in progress)

User is re-taking calibration frames for 07-02-26:

- **Darks @ 20s ISO 200**: lens cap + viewfinder covered, long-exposure NR OFF,
  ambient temp as close to the night session as possible, ~40+ frames.
  Replace (delete) the old 1/10s files in `darks/` — preflight hard-fails on a
  mixed dir by design.
- **Flats via MacBook Air screen**: full-screen white, max brightness,
  True Tone / Night Shift / auto-brightness OFF; 1–2 sheets of plain white
  paper on the lens as diffuser (kills pixel grid + moiré); keep ISO 200 f/4
  focus untouched; adjust only shutter until histogram peaks near mid-scale
  (~50%, vs the ~20% we got at 1/200s) — expect somewhere around 1/60–1/15s;
  slower than ~1/60s also dodges screen-refresh banding.
- Then just `./scripts/run_pipeline.sh 07-02-26` — dark & flat masters rebuild
  automatically, bias master is reused.

## Checklist for future acquisition sessions

- Darks: same exposure/ISO as lights, shot at night-time temps
- Flats: histogram peak ~50%
- Consider ISO 800 (Z6III dual-gain step) if staying at 20s subs
- Dither between subs — it's what rescues us when darks are imperfect
