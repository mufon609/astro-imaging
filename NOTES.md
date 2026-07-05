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

## Pipeline v1 design

`scripts/run_pipeline.sh <session-dir>` orchestrates four siril-cli stages,
deleting each stage's intermediates before the next (disk-limited):

1. `10_master_bias.ssf` — stack biases, Winsorized rej 3/3, no norm
2. `20_master_flat.ssf` — calibrate flats with master bias, stack norm=mul
3. `30_master_dark.ssf` — stack darks (used for cosmetic correction only)
4. `40_lights.ssf` — calibrate (dark as bias-equivalent + cc, flat, equalize_cfa,
   debayer) → register → 32-bit rej stack norm=addscale + rgb_equal
   → autostretched JPEG preview

Masters are kept in `<session>/work/masters/` and **reused if present** — delete
that dir (or a single master) to force a rebuild. Big FITS result is
overwritten each run (`results/stack_latest.fit`); small timestamped JPEG
previews accumulate for run-to-run comparison.

## Iteration ideas (not yet tried)

- Registration with distortion handling (24mm wide field, corner stars)
- `-filter-wfwhm` / quality filtering of lights before stack
- Drizzle (probably not: undersampled? no — 24mm @ 5.9µm is heavily oversampled
  spatially, skip)
- Background extraction (`subsky` / GraXpert — installed at ~/.local/bin/graxpert)
- Photometric color calibration (`pcc`) vs `rgb_equal`
- Denoising after stretch; starnet/star recomposition

## Checklist for the next acquisition session

- Darks: same exposure/ISO as lights (20s), shot at night-time temps
- Flats: histogram peak ~50% (raise exposure ~1/60s or add light)
- Consider ISO 800 (Z6III dual-gain step) if staying at 20s subs
- Dither between subs — it's what rescues us when darks are imperfect
