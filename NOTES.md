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

Calibration frames **re-shot 2026-07-05** (replacing the mismatched 1/10s darks
and dim 1/200s flats — see "Re-shoot outcome" below):

| dir    | n   | exposure | ISO | f/  | mm | taken               | pixel-level check |
|--------|-----|----------|-----|-----|----|---------------------|-------------------|
| lights | 32  | 20s      | 200 | 4.0 | 24 | Jul 2 23:55–Jul 3 00:14 | mean 1065, bg ~57 ADU above offset, stars saturate |
| darks  | 40  | 20s ✓    | 200 | 4.0 | 24 | Jul 5 14:20–14:35   | mean 1007.5 ≈ bias (no measurable mean dark current at 20s), σ 4.6, hot px to 4246 |
| biases | 98  | 1/160s   | 200 | 4.0 | 24 | Jul 5 13:55–13:57   | mean 1007.8, σ 4.08 ✓ |
| flats  | 100 | 1/160s   | 200 | 4.0 | 24 | Jul 5 13:53–13:54   | median 1964 (≈956 ADU signal), peak ~4400/16383 ≈ 27% |

Sensor offset (black level) ≈ 1008 ADU. Biases share the flats' 1/160s shutter,
so they double as exact flat-darks.

### Remaining acquisition caveats

1. **Flats still under target**: ~27% of full scale at peak (goal ~50%); brighter
   than the first attempt (~20%) but shy — next time ~3× more shutter (≈1/50s at
   the same screen brightness). 100 frames keep master-flat noise ≪ sky noise.
2. Darks shot at afternoon temps vs midnight lights: mean level is unaffected
   (≈ bias), and the hot-pixel population at warmer temp is a superset — fine
   for subtraction + `-cc=dark` mapping.
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
   equalize_cfa, debayer) → `setfindstar -sigma=0.5` + **two-pass** register +
   `seqapplyreg` → 32-bit rej stack norm=addscale + rgb_equal. The calibrate
   command is correct for matched *and* mismatched darks.
5. `50_postprocess.ssf` — planar background extraction + autostretch → JPEG
   preview. Run standalone via `scripts/run_post.sh <session>` to iterate on
   post without re-registering (~seconds instead of minutes).

Diagnostics: `diag_flat.ssf` (stretched master-flat check → JPEG) and
`diag_stack.ssf` (stat + bgnoise of the current stack). Record stack
median + bgnoise **before and after every change** and compare noise/median —
output normalization rescales levels when the reference frame changes, so raw
bgnoise numbers across runs are not comparable.

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
| `preview_20260705_132244` | same, full-pipeline validation run | = (old-cal baseline: 30/32, G noise/median 1.49%) |
| `preview_20260706_003151` | **re-shot cals**, 1-pass reg | calibration clean (corners/color/center ✓) but 26/32 — 4 more drifted tail frames dropped; G 1.58% |
| `preview_20260706_003913` | + 2-pass registration | 30/32 (auto-ref → frame 32); G 1.42% — beats old-cal |
| `preview_20260706_004620` | + `setfindstar -sigma=0.5` | **keeper** — 31/32 (ref → 18), G 1.40%, stars tight, no artifacts |

Registration history: with a sequence-start reference (1-pass default), the
fixed-tripod field drift strands the tail frames — 2/32 dropped with old cals,
6/32 after recalibration (borderline frames flipped when calibration changed
the detected-star sets). Two-pass registration picks a better reference and
recovers them; denser detection (`setfindstar -sigma=0.5`: ~870 vs ~370
stars/frame) moved it to 31/32. Frame 2 still fails star matching — not worth
chasing (+1 frame ≈ 1.6% noise). Per-frame FWHM spread is only ~6%
(uniform conditions), so wFWHM weighting/filtering would be a no-op here.

The remaining bright-bottom gradient is real sky (waning gibbous moon + horizon
glow); stronger removal needs treeline-aware masking (GraXpert) — future work.

## Iteration ideas (not yet tried)

- Registration with distortion handling (24mm wide field, corner stars)
- `-filter-wfwhm` / `-weight_from_wfwhm`: no-op for THIS session (FWHM spread
  ~6%) — revisit when a session has variable seeing/clouds/wind
- Drizzle (probably not: undersampled? no — 24mm @ 5.9µm is heavily oversampled
  spatially, skip)
- GraXpert background extraction (installed at ~/.local/bin/graxpert) for
  treeline-aware gradient removal — `subsky 1` is the in-Siril ceiling
- Photometric color calibration (`pcc`) vs `rgb_equal` (needs plate solve +
  catalog access)
- Denoising after stretch; starnet/star recomposition

## Re-shoot outcome (2026-07-05, all three calibration sets replaced)

- Darks now match lights (20s ISO 200, 40 frames): preflight warning gone,
  full dark subtraction valid, hot pixels (to 4246 ADU) properly mapped.
  Z6III mean dark current at 20s ≈ 0, so the win is the hot-pixel map.
- Flats brighter (27% peak vs 20%) but still below the ~50% goal at 1/160s —
  the MacBook-screen brightness needed ~1/50s. 100 frames compensate.
- Biases re-shot too (98 @ 1/160s — same shutter as flats = exact flat-darks).
- All three masters rebuilt automatically by the freshness check; no script
  changes were needed for the data swap itself.
- **Calibration validated by before/after compare**: no new artifacts (corners,
  color, banding, hot-pixel residue all clean); per-signal background noise
  unchanged at equal frame count. But the recalibrated frames initially
  registered *worse* (26/32 vs 30/32) — borderline drifted tail frames flipped
  to failing with a sequence-start reference → fixed with 2-pass registration
  (see iteration log).

## Checklist for future acquisition sessions

- Darks: same exposure/ISO as lights, shot at night-time temps
- Flats: histogram peak ~50% — the Jul 5 MacBook-screen setup at 1/160s gave
  only ~27%; use ≈1/50s at that screen brightness
- Consider ISO 800 (Z6III dual-gain step) if staying at 20s subs
- Dither between subs — it's what rescues us when darks are imperfect
